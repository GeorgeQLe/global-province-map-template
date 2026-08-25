#!/usr/bin/env python3
"""Generate full-geometry evidence for the remaining M25C QA blockers.

This is intentionally a research-only generator.  It replaces representative-
point inference with equal-area intersections between the exact assembled
territory components and the pinned Cliopatria 1444 polity polygons.  Results
are then aggregated by current actor and bound back to every rejected pair and
finding route.  Geometry agreement is not treated as proof of actor identity,
an exact historical border, or permission to edit the assembled candidate.
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
from shapely.ops import unary_union
from shapely.strtree import STRtree

from gpm.geo.metrics import geometry_area_sq_km


ROOT = Path(__file__).resolve().parents[1]
START_DATE = "1444-11-11"
BASE = ROOT / "research/start-dates/1444-global-v1/replacement-evidence"
CLIO = BASE / "cliopatria-v0.2.0"
PRIOR = BASE / "best-reasonable-v1"
ASSEMBLED = ROOT / "data/processed/m25c-assembled-pass/historical-territory-status.json"
PACKETS = ROOT / "research/start-dates/1444-global-v1/regional-packets"
OUTPUT = BASE / "actor-component-specific-v1"


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


def valid_geometry(value: Any):
    geometry = make_valid(shape(value))
    if geometry.is_empty:
        raise SystemExit("evidence input contains an empty geometry")
    return geometry


def evidence_class(coverage: float, dominant: float, source_count: int) -> str:
    if coverage >= 0.95 and dominant >= 0.90 and source_count == 1:
        return "near_complete_single_source_zone"
    if coverage >= 0.50:
        return "partial_or_multiple_source_zones"
    if coverage > 0:
        return "minor_source_overlap"
    return "outside_source_polity_coverage"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    args = parser.parse_args()

    canonical = load(ASSEMBLED)
    cliopatria_path = CLIO / "cliopatria-1444.geojson"
    cliopatria = load(cliopatria_path)
    decisions_path = PRIOR / "review-decisions.json"
    decisions = load(decisions_path)
    prior_components_path = PRIOR / "component-evidence.json"
    prior_pairs_path = PRIOR / "pair-evidence.json"
    prior_routes_path = PRIOR / "finding-routes.json"
    prior_components = {row["component_id"]: row for row in load(prior_components_path)["records"]}
    prior_pairs = {row["pair_id"]: row for row in load(prior_pairs_path)["records"]}
    prior_routes = {
        (row["region_id"], row["finding_code"]): row
        for row in load(prior_routes_path)["records"]
    }

    rejected_component_ids = {
        row["component_id"] for row in decisions["component_decisions"] if row["decision"] == "reject"
    }
    rejected_pair_ids = {
        row["pair_id"] for row in decisions["pair_decisions"] if row["decision"] == "reject"
    }
    rejected_findings = [row for row in decisions["finding_decisions"] if row["decision"] == "reject"]

    components = {row["territory_component_id"]: row for row in canonical["components"]}
    packet_paths = sorted(PACKETS.glob("*.json"))
    actor_names = {}
    for packet_path in packet_paths:
        for row in load(packet_path).get("polities") or []:
            actor_names[row["polity_id"]] = row["name"]
    for row in canonical["political_units"]:
        actor_names.setdefault(row["political_unit_id"], row.get("documented_status"))
    missing = rejected_component_ids - components.keys()
    if missing:
        raise SystemExit(f"rejected components are missing from assembled input: {sorted(missing)}")

    source_records: list[dict[str, Any]] = []
    source_geometries = []
    for index, feature in enumerate(cliopatria["features"]):
        properties = feature.get("properties") or {}
        if properties.get("Type") != "POLITY" or not feature.get("geometry"):
            continue
        geometry = valid_geometry(feature["geometry"])
        source_records.append({
            "source_feature_id": f"cliopatria-1444:{index}",
            "name": properties.get("Name"),
            "seshat_id": properties.get("SeshatID"),
            "wikidata_id": properties.get("Wikidata"),
            "wikipedia": properties.get("Wikipedia"),
            "valid_from": properties.get("FromYear"),
            "valid_to": properties.get("ToYear"),
            "feature_sha256": canonical_hash(feature),
        })
        source_geometries.append(geometry)
    tree = STRtree(source_geometries)

    intersection_cache: dict[str, dict[str, Any]] = {}

    def intersections(component_id: str) -> dict[str, Any]:
        if component_id in intersection_cache:
            return intersection_cache[component_id]
        geometry = valid_geometry(components[component_id]["geometry"])
        total_area = geometry_area_sq_km(geometry)
        rows = []
        covered_pieces = []
        for index in tree.query(geometry):
            source_geometry = source_geometries[int(index)]
            overlap = geometry.intersection(source_geometry)
            if overlap.is_empty:
                continue
            overlap_area = geometry_area_sq_km(overlap)
            if overlap_area <= max(total_area * 1e-8, 1e-6):
                continue
            source = source_records[int(index)]
            rows.append({
                **source,
                "intersection_area_sq_km": round(overlap_area, 6),
                "component_area_ratio": round(min(1.0, overlap_area / total_area), 9),
            })
            covered_pieces.append(overlap)
        rows.sort(key=lambda row: (-row["intersection_area_sq_km"], row["source_feature_id"]))
        covered_area = (
            geometry_area_sq_km(unary_union(covered_pieces)) if covered_pieces else 0.0
        )
        result = {
            "component_area_sq_km": round(total_area, 6),
            "covered_area_sq_km": round(min(total_area, covered_area), 6),
            "coverage_ratio": round(min(1.0, covered_area / total_area), 9),
            "intersections": rows,
        }
        intersection_cache[component_id] = result
        return result

    component_records = []
    for component_id in sorted(rejected_component_ids):
        prior = prior_components[component_id]
        measured = intersections(component_id)
        dominant = measured["intersections"][0]["component_area_ratio"] if measured["intersections"] else 0.0
        classification = evidence_class(measured["coverage_ratio"], dominant, len(measured["intersections"]))
        record = {
            "component_id": component_id,
            "province_id": components[component_id]["province_id"],
            "region_id": prior["region_id"],
            "current_actor_id": components[component_id].get("political_unit_id"),
            "current_actor_name": actor_names.get(components[component_id].get("political_unit_id")),
            "prior_evidence_record_sha256": prior["record_sha256"],
            "prior_rejection_reason": next(
                row["reason"] for row in decisions["component_decisions"] if row["component_id"] == component_id
            ),
            "measurement_method": "full component polygon intersection with spherical geodesic area",
            **measured,
            "evidence_class": classification,
            "recommended_treatment": (
                "review_as_component_specific_grade_c_candidate"
                if classification == "near_complete_single_source_zone"
                else "retain_fail_closed_and_obtain_component_specific_source"
            ),
            "limitations": [
                "Spatial agreement does not prove that the current synthetic actor and source polity are identical.",
                "Cliopatria linework is smoothed to roughly 0.07 degrees and retains unquantified border uncertainty.",
                "This record does not establish surveyed precision, a gap-free Grade-A component, or permission to edit.",
            ],
            "review_status": "pending_independent_review",
        }
        record["record_sha256"] = record_hash(record)
        component_records.append(record)

    pair_actor_ids = sorted({
        actor_id
        for pair_id in rejected_pair_ids
        for actor_id in (prior_pairs[pair_id]["left_actor_id"], prior_pairs[pair_id]["right_actor_id"])
    })
    actor_components: dict[str, list[str]] = defaultdict(list)
    for component_id, component in components.items():
        if component.get("political_unit_id") in pair_actor_ids:
            actor_components[component["political_unit_id"]].append(component_id)

    actor_records = []
    actor_record_by_id = {}
    for actor_id in pair_actor_ids:
        inventory = sorted(actor_components[actor_id])
        total_area = 0.0
        covered_area = 0.0
        source_area: Counter[str] = Counter()
        source_by_id = {row["source_feature_id"]: row for row in source_records}
        for component_id in inventory:
            measured = intersections(component_id)
            total_area += measured["component_area_sq_km"]
            covered_area += measured["covered_area_sq_km"]
            for row in measured["intersections"]:
                source_area[row["source_feature_id"]] += row["intersection_area_sq_km"]
        coverage = min(1.0, covered_area / total_area) if total_area else 0.0
        ranked = []
        for source_id, area in sorted(source_area.items(), key=lambda item: (-item[1], item[0])):
            source = source_by_id[source_id]
            ranked.append({
                **source,
                "intersection_area_sq_km": round(area, 6),
                "actor_area_ratio": round(min(1.0, area / total_area), 9),
            })
        dominant = ranked[0]["actor_area_ratio"] if ranked else 0.0
        record = {
            "actor_id": actor_id,
            "actor_name": actor_names.get(actor_id),
            "component_inventory": inventory,
            "component_count": len(inventory),
            "actor_area_sq_km": round(total_area, 6),
            "source_covered_area_sq_km": round(min(total_area, covered_area), 6),
            "source_coverage_ratio": round(coverage, 9),
            "source_zone_attribution": ranked,
            "evidence_class": evidence_class(coverage, dominant, len(ranked)),
            "identity_assessment": "not_established_by_geometry",
            "limitations": [
                "The current actor label is compared spatially but is not asserted to be the same entity as any source polygon.",
                "Coverage is aggregated over the actor's complete assembled component inventory; overlapping source polygons may make per-source ratios non-additive.",
            ],
            "review_status": "pending_independent_review",
        }
        record["record_sha256"] = record_hash(record)
        actor_records.append(record)
        actor_record_by_id[actor_id] = record

    component_record_by_id = {row["component_id"]: row for row in component_records}
    pair_records = []
    for pair_id in sorted(rejected_pair_ids):
        prior = prior_pairs[pair_id]
        left = actor_record_by_id[prior["left_actor_id"]]
        right = actor_record_by_id[prior["right_actor_id"]]
        left_source = left["source_zone_attribution"][0]["source_feature_id"] if left["source_zone_attribution"] else None
        right_source = right["source_zone_attribution"][0]["source_feature_id"] if right["source_zone_attribution"] else None
        distinct = bool(left_source and right_source and left_source != right_source)
        zonal_support = distinct and min(left["source_coverage_ratio"], right["source_coverage_ratio"]) >= 0.50
        record = {
            "pair_id": pair_id,
            "region_id": prior["region_id"],
            "left_actor_id": prior["left_actor_id"],
            "right_actor_id": prior["right_actor_id"],
            "left_actor_record_sha256": left["record_sha256"],
            "right_actor_record_sha256": right["record_sha256"],
            "incident_component_ids": prior["incident_component_ids"],
            "rejected_incident_component_record_sha256s": [
                component_record_by_id[item]["record_sha256"]
                for item in prior["incident_component_ids"] if item in component_record_by_id
            ],
            "prior_evidence_record_sha256": prior["record_sha256"],
            "dominant_source_zones_are_distinct": distinct,
            "evidence_class": "distinct_partial_or_better_source_zones" if zonal_support else "insufficient_pair_specific_support",
            "recommended_treatment": (
                "review_zonal_applicability_only_no_exact_border"
                if zonal_support else "retain_fail_closed_and_obtain_pair_to_citation_claims"
            ),
            "limitations": [
                "Distinct source-zone overlap does not establish that either source polity is identical to the current actor.",
                "This analysis does not derive or validate the exact shared line between the current actors.",
                "Positive-border assertions still require independently sourced linework or an approved non-line applicability treatment.",
            ],
            "review_status": "pending_independent_review",
        }
        record["record_sha256"] = record_hash(record)
        pair_records.append(record)

    pair_record_by_id = {row["pair_id"]: row for row in pair_records}
    route_records = []
    for decision in sorted(rejected_findings, key=lambda row: (row["region_id"], row["finding_code"])):
        prior = prior_routes[(decision["region_id"], decision["finding_code"])]
        component_hashes = [
            component_record_by_id[item]["record_sha256"]
            for item in prior["component_evidence_ids"] if item in component_record_by_id
        ]
        accepted_component_hashes = [
            prior_components[item]["record_sha256"]
            for item in prior["component_evidence_ids"] if item not in component_record_by_id
        ]
        pair_hashes = [pair_record_by_id[item]["record_sha256"] for item in prior["pair_evidence_ids"]]
        record = {
            "region_id": decision["region_id"],
            "finding_code": decision["finding_code"],
            "finding_message": prior["finding_message"],
            "prior_finding_decision_sha256": decision["decision_sha256"],
            "component_record_sha256s": component_hashes,
            "previously_accepted_component_evidence_sha256s": accepted_component_hashes,
            "pair_record_sha256s": pair_hashes,
            "review_status": "pending_independent_review",
            "implementation_status": "not_implemented",
        }
        record["record_sha256"] = record_hash(record)
        route_records.append(record)

    component_doc = {"document_type": "m25c-component-specific-geometry-evidence", "schema_version": "1.0.0", "start_date": START_DATE, "records": component_records}
    actor_doc = {"document_type": "m25c-actor-specific-geometry-evidence", "schema_version": "1.0.0", "start_date": START_DATE, "records": actor_records}
    pair_doc = {"document_type": "m25c-pair-specific-geometry-evidence", "schema_version": "1.0.0", "start_date": START_DATE, "records": pair_records}
    route_doc = {"document_type": "m25c-remaining-finding-evidence-routes", "schema_version": "1.0.0", "start_date": START_DATE, "records": route_records}
    artifacts = [
        write_json(args.output_dir, "component-specific-evidence.json", component_doc),
        write_json(args.output_dir, "actor-specific-evidence.json", actor_doc),
        write_json(args.output_dir, "pair-specific-evidence.json", pair_doc),
        write_json(args.output_dir, "finding-routes.json", route_doc),
    ]
    component_classes = Counter(row["evidence_class"] for row in component_records)
    actor_classes = Counter(row["evidence_class"] for row in actor_records)
    pair_classes = Counter(row["evidence_class"] for row in pair_records)
    manifest = {
        "document_type": "m25c-actor-component-specific-evidence-manifest",
        "schema_version": "1.0.0",
        "start_date": START_DATE,
        "status": "research complete; pending independent review; not implemented",
        "method": "full component polygon intersections and complete actor aggregation with spherical geodesic area",
        "source": {
            "name": "Cliopatria v0.2.0 pinned 1444 slice",
            "path": str(cliopatria_path.relative_to(ROOT)),
            "sha256": file_hash(cliopatria_path),
            "polity_feature_count": len(source_records),
        },
        "frozen_inputs": [
            {"path": str(path.relative_to(ROOT)), "sha256": file_hash(path)}
            for path in (ASSEMBLED, decisions_path, prior_components_path, prior_pairs_path, prior_routes_path, *packet_paths)
        ],
        "totals": {
            "rejected_finding_routes": len(route_records),
            "rejected_pair_records": len(pair_records),
            "affected_actor_records": len(actor_records),
            "actors_with_any_source_coverage": sum(row["source_coverage_ratio"] > 0 for row in actor_records),
            "actor_evidence_classes": dict(sorted(actor_classes.items())),
            "rejected_component_records": len(component_records),
            "component_evidence_classes": dict(sorted(component_classes.items())),
            "pair_evidence_classes": dict(sorted(pair_classes.items())),
        },
        "decision_boundary": [
            "No geometry match establishes identity between a synthetic current actor and a source polity.",
            "No record establishes an exact historical border or Grade-A precision.",
            "Independent review must decide every route before any serial implementation.",
            "No packet, assembled artifact, tolerance, permission, or Task 17 state changes here.",
        ],
        "artifacts": artifacts,
    }
    write_json(args.output_dir, "manifest.json", manifest)
    print(json.dumps(manifest["totals"], sort_keys=True))


if __name__ == "__main__":
    main()
