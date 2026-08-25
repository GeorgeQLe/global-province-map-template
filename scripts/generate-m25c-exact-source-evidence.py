#!/usr/bin/env python3
"""Bind newly audited sources to every remaining rejected M25C record.

The optional Driver shapefile measurement deliberately preserves the source's
temporal and licensing failures.  A spatial match is useful record-level
evidence, but it is never promoted to exact-date evidence by this generator.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from shapely import make_valid
from shapely.geometry import shape
from shapely.ops import transform
from shapely.strtree import STRtree


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/start-dates/1444-global-v1/replacement-evidence"
PRIOR = BASE / "actor-component-specific-v1"
BEST = BASE / "best-reasonable-v1"
OUTPUT = BASE / "exact-source-v1"
CANONICAL = ROOT / "data/processed/m25c-assembled-pass/historical-territory-status.json"
ASSIGNMENTS = ROOT / "data/processed/m25c-assembled-pass/assignments.json"
DRIVER_REGIONS = {"013", "021", "029"}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record_hash(record: dict[str, Any]) -> str:
    return canonical_hash({key: value for key, value in record.items() if key != "record_sha256"})


def write_json(output: Path, name: str, value: Any) -> dict[str, Any]:
    data = (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()
    path = output / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return {"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def load_driver(base: Path | None):
    if base is None:
        return [], [], None, None, []
    try:
        import shapefile  # type: ignore[import-not-found]
        from pyproj import Transformer  # type: ignore[import-not-found]
    except ImportError as exc:
        raise SystemExit("Driver import requires the pyshp and pyproj packages") from exc

    required = [base.with_suffix(ext) for ext in (".shp", ".shx", ".dbf", ".prj", ".cpg")]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise SystemExit(f"Driver source files are missing: {missing}")
    source_crs = base.with_suffix(".prj").read_text(encoding="utf-8")
    component_transformer = Transformer.from_crs("EPSG:4326", source_crs, always_xy=True)
    reader = shapefile.Reader(str(base.with_suffix(".shp")))
    records = []
    geometries = []
    for index, item in enumerate(reader.iterShapeRecords()):
        geometry = make_valid(shape(item.shape.__geo_interface__))
        properties = item.record.as_dict()
        record = {
            "source_feature_id": f"driver-1953:{index}",
            "name": properties.get("Name"),
            "other_names": properties.get("Other"),
            "language_family": properties.get("Language f"),
            "feature_sha256": canonical_hash({
                "properties": properties,
                "geometry": geometry.__geo_interface__,
            }),
        }
        records.append(record)
        geometries.append(geometry)
    return records, geometries, STRtree(geometries), component_transformer, [
        {"path": path.name, "bytes": path.stat().st_size, "sha256": file_hash(path)}
        for path in required
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--driver-base",
        type=Path,
        required=True,
        help="Path without extension to the five Driver shapefile files",
    )
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    args = parser.parse_args()

    registry_path = OUTPUT / "source-registry.json"
    registry = load(registry_path)
    sources = {row["source_id"]: row for row in registry["sources"]}
    source_hashes = {source_id: canonical_hash(row) for source_id, row in sources.items()}
    sources_by_region: dict[str, list[str]] = defaultdict(list)
    for source in registry["sources"]:
        for region_id in source["applicable_region_ids"]:
            sources_by_region[region_id].append(source["source_id"])

    components_doc = load(PRIOR / "component-specific-evidence.json")
    actors_doc = load(PRIOR / "actor-specific-evidence.json")
    pairs_doc = load(PRIOR / "pair-specific-evidence.json")
    routes_doc = load(BEST / "finding-routes.json")
    remaining_route_keys = {
        (row["region_id"], row["finding_code"])
        for row in load(PRIOR / "finding-routes.json")["records"]
    }
    canonical = load(CANONICAL)
    assignments = load(ASSIGNMENTS)
    component_geometry = {
        row["territory_component_id"]: make_valid(shape(row["geometry"]))
        for row in canonical["components"]
    }
    component_region = {
        f"cmp-{row['province_id']}": row["region_id"] for row in assignments["assignments"]
    }
    component_actors = {
        f"cmp-{row['province_id']}": sorted(row.get("polity_ids") or [])
        for row in assignments["assignments"]
    }

    driver_records, driver_geometries, driver_tree, component_transformer, driver_files = load_driver(args.driver_base)
    measurement_cache: dict[str, dict[str, Any]] = {}

    def driver_measurement(component_id: str) -> dict[str, Any] | None:
        if driver_tree is None or component_region.get(component_id) not in DRIVER_REGIONS:
            return None
        if component_id in measurement_cache:
            return measurement_cache[component_id]
        geometry = make_valid(transform(component_transformer.transform, component_geometry[component_id]))
        component_area = geometry.area
        intersections = []
        covered = []
        for raw_index in driver_tree.query(geometry):
            index = int(raw_index)
            overlap = geometry.intersection(driver_geometries[index])
            if overlap.is_empty or overlap.area <= max(component_area * 1e-10, 1e-14):
                continue
            source = driver_records[index]
            intersections.append({
                **source,
                "component_area_ratio": round(min(1.0, overlap.area / component_area), 9),
            })
            covered.append(overlap)
        intersections.sort(key=lambda row: (-row["component_area_ratio"], row["source_feature_id"]))
        from shapely.ops import unary_union
        coverage = min(1.0, unary_union(covered).area / component_area) if covered else 0.0
        result = {
            "coverage_ratio": round(coverage, 9),
            "intersections": intersections,
            "measurement_method": "full component intersection in the source North America Albers equal-area CRS",
        }
        measurement_cache[component_id] = result
        return result

    component_records = []
    for prior in components_doc["records"]:
        region_id = prior["region_id"]
        measurement = driver_measurement(prior["component_id"])
        record = {
            "component_id": prior["component_id"],
            "region_id": region_id,
            "prior_record_sha256": prior["record_sha256"],
            "candidate_source_ids": sorted(sources_by_region[region_id]),
            "candidate_source_record_sha256s": [
                source_hashes[source_id] for source_id in sorted(sources_by_region[region_id])
            ],
            "driver_measurement": measurement,
            "exact_date_component_source_obtained": False,
            "independently_derived_line_obtained": False,
            "qualification": "retain_rejected",
            "qualification_reasons": [
                "No audited source supplies a licensed exact-date component polygon.",
                "No audited source supplies a licensed independently derived exact shared line for this component.",
            ],
        }
        if measurement is not None:
            record["qualification_reasons"].append(
                "Driver feature mappings are exact and measurable, but their source chronology begins in the sixteenth century and mixes later observations."
            )
        record["record_sha256"] = record_hash(record)
        component_records.append(record)
    component_by_id = {row["component_id"]: row for row in component_records}

    pair_incident_by_actor: dict[str, set[str]] = defaultdict(set)
    for pair in pairs_doc["records"]:
        for component_id in pair["incident_component_ids"]:
            for actor_id in component_actors.get(component_id, []):
                if actor_id in {pair["left_actor_id"], pair["right_actor_id"]}:
                    pair_incident_by_actor[actor_id].add(component_id)

    actor_names = {row["actor_id"]: row.get("actor_name") for row in actors_doc["records"]}
    actor_records = []
    for prior in actors_doc["records"]:
        actor_id = prior["actor_id"]
        inventory = sorted(pair_incident_by_actor[actor_id])
        bindings = []
        for component_id in inventory:
            measurement = driver_measurement(component_id)
            if measurement and measurement["intersections"]:
                bindings.append({
                    "component_id": component_id,
                    "source_feature_bindings": measurement["intersections"],
                })
        regions = sorted({component_region[item] for item in inventory})
        if not regions:
            regions = sorted({
                pair["region_id"] for pair in pairs_doc["records"]
                if actor_id in {pair["left_actor_id"], pair["right_actor_id"]}
            })
        candidate_source_ids = sorted({source_id for region in regions for source_id in sources_by_region[region]})
        record = {
            "actor_id": actor_id,
            "actor_name": actor_names[actor_id],
            "region_ids": regions,
            "prior_record_sha256": prior["record_sha256"],
            "incident_component_inventory": inventory,
            "candidate_source_ids": candidate_source_ids,
            "candidate_source_record_sha256s": [source_hashes[source_id] for source_id in candidate_source_ids],
            "component_to_citation_bindings": bindings,
            "all_incident_components_have_named_driver_features": bool(inventory) and len(bindings) == len(inventory),
            "exact_actor_identity_claim_obtained": False,
            "exact_target_date_claim_obtained": False,
            "qualification": "retain_rejected",
            "qualification_reason": "Named feature bindings do not establish that the synthetic aggregate actor is identical to every mapped source group at 1444-11-11.",
        }
        record["record_sha256"] = record_hash(record)
        actor_records.append(record)
    actor_by_id = {row["actor_id"]: row for row in actor_records}

    pair_records = []
    for prior in pairs_doc["records"]:
        left = actor_by_id[prior["left_actor_id"]]
        right = actor_by_id[prior["right_actor_id"]]
        record = {
            "pair_id": prior["pair_id"],
            "region_id": prior["region_id"],
            "left_actor_id": prior["left_actor_id"],
            "right_actor_id": prior["right_actor_id"],
            "left_actor_record_sha256": left["record_sha256"],
            "right_actor_record_sha256": right["record_sha256"],
            "incident_component_ids": prior["incident_component_ids"],
            "prior_record_sha256": prior["record_sha256"],
            "actor_to_citation_surface_complete": (
                left["all_incident_components_have_named_driver_features"]
                and right["all_incident_components_have_named_driver_features"]
            ),
            "exact_target_date_pair_claim_obtained": False,
            "independent_shared_line_obtained": False,
            "qualification": "retain_rejected",
            "qualification_reason": "No source establishes both exact synthetic actors and their disposition or shared line on 1444-11-11.",
        }
        record["record_sha256"] = record_hash(record)
        pair_records.append(record)
    pair_by_id = {row["pair_id"]: row for row in pair_records}

    route_records = []
    for prior in routes_doc["records"]:
        if (prior["region_id"], prior["finding_code"]) not in remaining_route_keys:
            continue
        component_hashes = [
            component_by_id[item]["record_sha256"]
            for item in prior["component_evidence_ids"]
            if item in component_by_id
        ]
        previously_accepted_component_ids = [
            item for item in prior["component_evidence_ids"] if item not in component_by_id
        ]
        pair_hashes = [pair_by_id[item]["record_sha256"] for item in prior["pair_evidence_ids"]]
        record = {
            "region_id": prior["region_id"],
            "finding_code": prior["finding_code"],
            "prior_record_sha256": prior["record_sha256"],
            "component_record_sha256s": component_hashes,
            "previously_accepted_component_ids": previously_accepted_component_ids,
            "pair_record_sha256s": pair_hashes,
            "qualifying_record_count": 0,
            "submission_status": "not_submitted_no_qualifying_exact_source",
            "implementation_status": "not_implemented",
        }
        record["record_sha256"] = record_hash(record)
        route_records.append(record)

    source_doc = {
        "document_type": "m25c-new-source-qualification-audit",
        "schema_version": "1.0.0",
        "start_date": "1444-11-11",
        "records": [
            {**source, "record_sha256": source_hashes[source["source_id"]]}
            for source in registry["sources"]
        ],
    }
    actor_doc = {"document_type": "m25c-exact-actor-citation-attempt", "schema_version": "1.0.0", "start_date": "1444-11-11", "records": actor_records}
    component_doc = {"document_type": "m25c-exact-component-line-attempt", "schema_version": "1.0.0", "start_date": "1444-11-11", "records": component_records}
    pair_doc = {"document_type": "m25c-exact-pair-citation-attempt", "schema_version": "1.0.0", "start_date": "1444-11-11", "records": pair_records}
    route_doc = {"document_type": "m25c-exact-source-finding-submissions", "schema_version": "1.0.0", "start_date": "1444-11-11", "records": route_records}
    artifacts = [
        write_json(args.output_dir, "source-audit.json", source_doc),
        write_json(args.output_dir, "actor-citation-evidence.json", actor_doc),
        write_json(args.output_dir, "component-line-evidence.json", component_doc),
        write_json(args.output_dir, "pair-evidence.json", pair_doc),
        write_json(args.output_dir, "finding-submissions.json", route_doc),
    ]
    manifest = {
        "document_type": "m25c-exact-source-evidence-manifest",
        "schema_version": "1.0.0",
        "start_date": "1444-11-11",
        "status": "source audit complete; no qualifying exact-date record; not implemented",
        "source_registry": {"path": str(registry_path.relative_to(ROOT)), "sha256": file_hash(registry_path)},
        "driver_source_files": driver_files,
        "frozen_inputs": [
            {"path": str(path.relative_to(ROOT)), "sha256": file_hash(path)}
            for path in (
                CANONICAL,
                ASSIGNMENTS,
                PRIOR / "component-specific-evidence.json",
                PRIOR / "actor-specific-evidence.json",
                PRIOR / "pair-specific-evidence.json",
                PRIOR / "finding-routes.json",
                BEST / "finding-routes.json",
            )
        ],
        "totals": {
            "audited_sources": len(registry["sources"]),
            "driver_features": len(driver_records),
            "actors": len(actor_records),
            "actors_with_complete_named_driver_binding": sum(row["all_incident_components_have_named_driver_features"] for row in actor_records),
            "components": len(component_records),
            "components_with_driver_intersection": sum(bool(row["driver_measurement"] and row["driver_measurement"]["intersections"]) for row in component_records),
            "pairs": len(pair_records),
            "pairs_with_complete_named_driver_binding": sum(row["actor_to_citation_surface_complete"] for row in pair_records),
            "finding_routes": len(route_records),
            "qualifying_exact_date_records": 0,
        },
        "decision_boundary": [
            "Exact record binding is not exact historical truth.",
            "A source with the wrong date cannot qualify a 1444 record even when polygon coverage is complete.",
            "Citation-only copyrighted raster plates are not redistributed, traced, or treated as licensed linework.",
            "No record is submitted for independent acceptance and no implementation or permission changes.",
        ],
        "artifacts": artifacts,
    }
    write_json(args.output_dir, "manifest.json", manifest)
    print(json.dumps(manifest["totals"], sort_keys=True))


if __name__ == "__main__":
    main()
