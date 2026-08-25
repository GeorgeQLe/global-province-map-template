#!/usr/bin/env python3
"""Generate best-reasonable supplemental evidence for deferred M25C findings.

This is a research generator, not an implementation generator. It binds the
frozen actor pairs and corridor components to two approximate historical
basemap snapshots, an exact-date OpenHistoricalMap query, and the already
reviewed regional source pins. Approximate or missing evidence remains visible
and is never promoted to surveyed linework or Grade-A certification.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from shapely.geometry import GeometryCollection, LineString, MultiPolygon, Polygon, shape
from shapely.ops import polygonize, unary_union
from shapely.strtree import STRtree


ROOT = Path(__file__).resolve().parents[1]
START_DATE = "1444-11-11"
BASE = ROOT / "research/start-dates/1444-global-v1/replacement-evidence/cliopatria-v0.2.0"
ASSEMBLED = ROOT / "data/processed/m25c-assembled-pass"
PACKETS = ROOT / "research/start-dates/1444-global-v1/regional-packets"
OUTPUT = ROOT / "research/start-dates/1444-global-v1/replacement-evidence/best-reasonable-v1"

HISTORICAL_BASEMAP_COMMIT = "62d8f1a03a71f2d3ff17f2d166f7553f256bce68"
HISTORICAL_BASEMAP_HASHES = {
    1400: "9349daa1afe05e4b73c56e31735bf8c13625bd35b7a23f17aa2f3a4bc672a20f",
    1492: "b952a7804cc4ed6c14aaebcb78e2e087c34ee5b1ffa1b659325cdfb45a806af3",
}
OHM_QUERY = (
    '[out:json][timeout:240][maxsize:1073741824];'
    'relation(-90,-180,90,180)["admin_level"="2"]'
    '(if:t["start_date"] <= "1444-11-11" && '
    '(!is_tag("end_date") || t["end_date"] > "1444-11-11"));out body geom;'
)
OHM_SNAPSHOT_HASH = "90d7b175b48ca1382e35c3e313761481e9139e8a646eb8ba086e49e7d7b12b89"

ACCEPTED_FINDINGS = {
    ("014", "MISSING_POSITIVE_BORDER_ASSERTION"),
    ("015", "MISSING_POSITIVE_BORDER_ASSERTION"),
    ("030", "MISSING_POSITIVE_BORDER_ASSERTION"),
    ("030", "NON_EXECUTABLE_SEAM_ASSERTION"),
    ("030", "SPATIAL_ASSERTION_FAILED"),
    ("030", "UNCERTIFIED_A_GRADE"),
    ("034", "MISSING_POSITIVE_BORDER_ASSERTION"),
    ("035", "MISSING_POSITIVE_BORDER_ASSERTION"),
    ("039", "MISSING_POSITIVE_BORDER_ASSERTION"),
    ("061", "BORDER_APPLICABILITY_NOT_QUALIFIED"),
    ("061", "MISSING_POSITIVE_BORDER_ASSERTION"),
    ("143", "MISSING_POSITIVE_BORDER_ASSERTION"),
    ("145", "MISSING_POSITIVE_BORDER_ASSERTION"),
}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> dict[str, Any]:
    data = json_bytes(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return {"path": str(path.relative_to(OUTPUT)), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def historical_index(path: Path, expected_hash: str, label: str) -> dict[str, Any]:
    if file_hash(path) != expected_hash:
        raise SystemExit(f"{label} checksum does not match the pinned source bytes")
    doc = load(path)
    records = []
    geometries = []
    for offset, feature in enumerate(doc["features"]):
        if not feature.get("geometry"):
            continue
        geometry = shape(feature["geometry"])
        if geometry.is_empty:
            continue
        properties = feature.get("properties") or {}
        records.append({
            "feature_id": f"{label}:{offset}",
            "name": properties.get("NAME"),
            "subject": properties.get("SUBJECTO"),
            "part_of": properties.get("PARTOF"),
            "border_precision": properties.get("BORDERPRECISION"),
            "feature_sha256": canonical_hash(feature),
        })
        geometries.append(geometry)
    return {"records": records, "geometries": geometries, "tree": STRtree(geometries)}


def relation_geometry(element: dict[str, Any]):
    outer_lines = []
    inner_lines = []
    for member in element.get("members") or []:
        points = member.get("geometry") or []
        if len(points) < 2:
            continue
        line = LineString([(point["lon"], point["lat"]) for point in points])
        (inner_lines if member.get("role") == "inner" else outer_lines).append(line)
    if not outer_lines:
        return GeometryCollection()
    polygons = list(polygonize(unary_union(outer_lines)))
    if not polygons:
        return GeometryCollection()
    outer = unary_union(polygons)
    if inner_lines:
        holes = list(polygonize(unary_union(inner_lines)))
        if holes:
            outer = outer.difference(unary_union(holes))
    if isinstance(outer, (Polygon, MultiPolygon)):
        return outer
    return GeometryCollection()


def ohm_index(path: Path) -> dict[str, Any]:
    if file_hash(path) != OHM_SNAPSHOT_HASH:
        raise SystemExit("OpenHistoricalMap snapshot checksum does not match the reviewed query result")
    doc = load(path)
    records = []
    geometries = []
    for element in doc.get("elements") or []:
        geometry = relation_geometry(element)
        if geometry.is_empty:
            continue
        tags = element.get("tags") or {}
        records.append({
            "feature_id": f"ohm:relation:{element['id']}",
            "name": tags.get("name"),
            "start_date": tags.get("start_date"),
            "end_date": tags.get("end_date"),
            "source": tags.get("source"),
            "source_name": tags.get("source:name"),
            "license": tags.get("license") or tags.get("licence"),
            "attribution": tags.get("attribution"),
            "relation_sha256": canonical_hash(element),
        })
        geometries.append(geometry)
    return {"records": records, "geometries": geometries, "tree": STRtree(geometries)}


def matches(index: dict[str, Any], geometry) -> list[dict[str, Any]]:
    point = geometry.representative_point()
    return [index["records"][int(value)] for value in index["tree"].query(point, predicate="intersects")]


def packet_sources() -> dict[str, list[dict[str, Any]]]:
    result = {}
    for path in sorted(PACKETS.glob("[0-9][0-9][0-9]-*.json")):
        packet = load(path)
        result[packet["region_id"]] = [
            {
                "source_id": row["source_id"],
                "citation": row["citation"],
                "url": row["url"],
                "valid_from": row.get("valid_from"),
                "valid_to": row.get("valid_to"),
                "source_type": row.get("source_type"),
                "review_status": row.get("review_status"),
            }
            for row in packet.get("sources") or []
            if row.get("source_type") != "negative_control"
        ]
    return result


def source_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    named = [row for row in rows if row.get("name")]
    return {
        "match_count": len(rows),
        "named_match_count": len(named),
        "names": sorted({row["name"] for row in named}),
        "feature_ids": sorted(row["feature_id"] for row in rows),
        "sourced_feature_ids": sorted(row["feature_id"] for row in rows if row.get("source")),
        "feature_license_overrides": {
            row["feature_id"]: row["license"] for row in rows if row.get("license")
        },
    }


def confidence(evidence: dict[str, Any]) -> str:
    if evidence["openhistoricalmap"]["sourced_feature_ids"]:
        return "medium"
    if evidence["historical_basemap_1400"]["named_match_count"] and evidence["historical_basemap_1492"]["named_match_count"]:
        return "medium"
    return "low"


def build(historical_1400: Path, historical_1492: Path, ohm_snapshot: Path, output: Path) -> None:
    global OUTPUT
    OUTPUT = output
    hb1400 = historical_index(historical_1400, HISTORICAL_BASEMAP_HASHES[1400], "historical-basemap-1400")
    hb1492 = historical_index(historical_1492, HISTORICAL_BASEMAP_HASHES[1492], "historical-basemap-1492")
    ohm = ohm_index(ohm_snapshot)

    canonical = load(ASSEMBLED / "historical-territory-status.json")
    geometry_by_component = {
        row["territory_component_id"]: shape(row["geometry"])
        for row in canonical["components"]
    }
    regional_sources = packet_sources()
    applicability = load(BASE / "applicability-review-candidates.json")
    dossiers = {path.stem: load(path) for path in sorted((BASE / "regions").glob("*.json"))}

    component_records = []
    for region_id, dossier in dossiers.items():
        source_ids = [row["source_id"] for row in regional_sources[region_id]]
        for row in dossier["corridor_component_mapping"]:
            if row["source_classification"] == "single_polity":
                continue
            component_id = row["component_id"]
            geometry = geometry_by_component[component_id]
            point = geometry.representative_point()
            evidence = {
                "historical_basemap_1400": source_summary(matches(hb1400, geometry)),
                "historical_basemap_1492": source_summary(matches(hb1492, geometry)),
                "openhistoricalmap": source_summary(matches(ohm, geometry)),
            }
            record = {
                "component_id": component_id,
                "region_id": region_id,
                "province_id": row["province_id"],
                "representative_point": [round(point.x, 7), round(point.y, 7)],
                "frozen_source_classification": row["source_classification"],
                "current_political_unit_id": row["current_political_unit_id"],
                "current_facets": row["current_facets"],
                "current_relationship_actors": row["current_relationship_actors"],
                "spatial_corroboration": evidence,
                "reviewed_regional_source_ids": source_ids,
                "recommended_treatment": (
                    "approximate_spatial_corroboration"
                    if any(value["named_match_count"] for value in evidence.values())
                    else "regional_context_only"
                ),
                "confidence": confidence(evidence),
                "review_status": "pending_independent_review",
                "limitations": [
                    "The 1400 and 1492 layers bracket rather than equal 1444-11-11.",
                    "Historical Basemaps BORDERPRECISION=1 denotes approximate geometry.",
                    "An OHM match is decisive only when its own source and date lineage pass review.",
                    "This record does not by itself authorize a component mutation or Grade-A claim.",
                ],
            }
            record["record_sha256"] = canonical_hash(record)
            component_records.append(record)

    pair_records = []
    pair_ids_by_region: dict[str, list[str]] = {}
    for applicability_record in applicability["records"]:
        region_id = applicability_record["region_id"]
        if not applicability_record["eligible_land_adjacent_actor_pairs"]:
            continue
        pair_ids_by_region[region_id] = []
        regional_source_ids = [row["source_id"] for row in regional_sources[region_id]]
        for pair in applicability_record["eligible_land_adjacent_actor_pairs"]:
            evidence_counts = {
                key: Counter()
                for key in ("historical_basemap_1400", "historical_basemap_1492", "openhistoricalmap")
            }
            evidence_feature_ids = {key: set() for key in evidence_counts}
            sourced_feature_ids = {key: set() for key in evidence_counts}
            named_components = Counter()
            sourced_ohm_components = 0
            for component_id in pair["component_ids"]:
                geometry = geometry_by_component[component_id]
                evidence = {
                    "historical_basemap_1400": source_summary(matches(hb1400, geometry)),
                    "historical_basemap_1492": source_summary(matches(hb1492, geometry)),
                    "openhistoricalmap": source_summary(matches(ohm, geometry)),
                }
                for key, value in evidence.items():
                    evidence_counts[key].update(value["names"])
                    evidence_feature_ids[key].update(value["feature_ids"])
                    sourced_feature_ids[key].update(value["sourced_feature_ids"])
                    if value["named_match_count"]:
                        named_components[key] += 1
                if evidence["openhistoricalmap"]["sourced_feature_ids"]:
                    sourced_ohm_components += 1
            pair_id = "pair-" + canonical_hash({
                "region_id": region_id,
                "left_actor_id": pair["left_actor_id"],
                "right_actor_id": pair["right_actor_id"],
                "component_ids": pair["component_ids"],
            })[:20]
            record = {
                "pair_id": pair_id,
                "region_id": region_id,
                "left_actor_id": pair["left_actor_id"],
                "right_actor_id": pair["right_actor_id"],
                "incident_component_ids": pair["component_ids"],
                "recommended_disposition": pair["disposition"],
                "reviewed_regional_source_ids": regional_source_ids,
                "spatial_corroboration": {
                    key: {
                        "named_component_count": named_components[key],
                        "total_component_count": len(pair["component_ids"]),
                        "match_names": sorted(values),
                        "feature_ids": sorted(evidence_feature_ids[key]),
                        "sourced_feature_ids": sorted(sourced_feature_ids[key]),
                    }
                    for key, values in evidence_counts.items()
                },
                "sourced_openhistoricalmap_component_count": sourced_ohm_components,
                "rationale": (
                    "Treat the exact frozen adjacency as a reconstructed frontier zone, not a source-derived line."
                    if pair["disposition"] == "evidence_supports_zone_not_line"
                    else "Treat the exact frozen adjacency as contact between non-territorial reconstruction fabrics, not a positive sovereign border."
                ),
                "confidence": (
                    "medium"
                    if sourced_ohm_components
                    or (
                        named_components["historical_basemap_1400"]
                        and named_components["historical_basemap_1492"]
                    )
                    else "low"
                ),
                "review_status": "pending_independent_review",
                "limitations": [
                    "Regional citations establish historical context but are not automatically pair-specific linework.",
                    "Bracketing approximate maps corroborate zones only and cannot establish surveyed boundaries.",
                    "Independent review must accept this pair separately before applicability implementation.",
                ],
            }
            record["record_sha256"] = canonical_hash(record)
            pair_records.append(record)
            pair_ids_by_region[region_id].append(pair_id)

    component_ids_by_region: dict[str, list[str]] = {}
    for record in component_records:
        component_ids_by_region.setdefault(record["region_id"], []).append(record["component_id"])

    finding_records = []
    for region_id, dossier in dossiers.items():
        for finding in dossier["frozen_findings"]:
            code = finding["code"]
            if (region_id, code) in ACCEPTED_FINDINGS:
                continue
            pair_route = code in {"MISSING_POSITIVE_BORDER_ASSERTION", "BORDER_APPLICABILITY_NOT_QUALIFIED"}
            record = {
                "region_id": region_id,
                "finding_code": code,
                "finding_message": finding["message"],
                "pair_evidence_ids": pair_ids_by_region.get(region_id, []) if pair_route else [],
                "component_evidence_ids": component_ids_by_region.get(region_id, []) if not pair_route else [],
                "recommended_completion": (
                    "review_pair_specific_best_reasonable_applicability"
                    if pair_route else
                    "review_component_specific_approximate_corridor_reconstruction"
                ),
                "grade_policy": (
                    "not_applicable" if pair_route else
                    "retain Grade A only if all cited gates pass; otherwise publish as Grade B/C with documented gaps"
                ),
                "review_status": "pending_independent_review",
            }
            record["record_sha256"] = canonical_hash(record)
            finding_records.append(record)

    output.mkdir(parents=True, exist_ok=True)
    artifacts = []
    artifacts.append(write_json(output / "pair-evidence.json", {
        "document_type": "m25c_best_reasonable_pair_evidence",
        "schema_version": "1.0.0",
        "start_date": START_DATE,
        "records": sorted(pair_records, key=lambda row: (row["region_id"], row["pair_id"])),
    }))
    artifacts.append(write_json(output / "component-evidence.json", {
        "document_type": "m25c_best_reasonable_component_evidence",
        "schema_version": "1.0.0",
        "start_date": START_DATE,
        "records": sorted(component_records, key=lambda row: (row["region_id"], row["component_id"])),
    }))
    artifacts.append(write_json(output / "finding-routes.json", {
        "document_type": "m25c_best_reasonable_finding_routes",
        "schema_version": "1.0.0",
        "start_date": START_DATE,
        "records": sorted(finding_records, key=lambda row: (row["region_id"], row["finding_code"])),
    }))

    source_records = {
        "historical_basemaps": {
            "repository": "https://github.com/aourednik/historical-basemaps",
            "commit": HISTORICAL_BASEMAP_COMMIT,
            "license": "GPL-3.0",
            "snapshots": [
                {"year": year, "sha256": digest, "url": f"https://raw.githubusercontent.com/aourednik/historical-basemaps/{HISTORICAL_BASEMAP_COMMIT}/geojson/world_{year}.geojson"}
                for year, digest in HISTORICAL_BASEMAP_HASHES.items()
            ],
            "qualification": "approximate bracketing corroboration only",
        },
        "openhistoricalmap": {
            "endpoint": "https://overpass-api.openhistoricalmap.org/api/interpreter",
            "query": OHM_QUERY,
            "snapshot_sha256": OHM_SNAPSHOT_HASH,
            "returned_relation_count": len(load(ohm_snapshot).get("elements") or []),
            "usable_polygon_count": len(ohm["records"]),
            "sourced_polygon_count": sum(bool(row.get("source")) for row in ohm["records"]),
            "license": "CC0 by default; feature-specific license tags override",
            "qualification": "exact-date corroboration; feature-specific source review required",
        },
    }
    manifest = {
        "document_type": "m25c_best_reasonable_evidence_manifest",
        "schema_version": "1.0.0",
        "start_date": START_DATE,
        "status": "research complete; pending independent review; not implemented",
        "source_records": source_records,
        "frozen_inputs": {
            "applicability_review_candidates_sha256": file_hash(BASE / "applicability-review-candidates.json"),
            "assembled_status_sha256": file_hash(ASSEMBLED / "historical-territory-status.json"),
            "regional_packets": [
                {
                    "path": str(path.relative_to(ROOT)),
                    "sha256": file_hash(path),
                }
                for path in sorted(PACKETS.glob("[0-9][0-9][0-9]-*.json"))
            ],
            "regional_dossiers": [
                {
                    "path": str(path.relative_to(ROOT)),
                    "sha256": file_hash(path),
                }
                for path in sorted((BASE / "regions").glob("*.json"))
            ],
        },
        "totals": {
            "deferred_finding_routes": len(finding_records),
            "pair_records": len(pair_records),
            "component_records": len(component_records),
            "medium_confidence_pairs": sum(row["confidence"] == "medium" for row in pair_records),
            "low_confidence_pairs": sum(row["confidence"] == "low" for row in pair_records),
            "medium_confidence_components": sum(row["confidence"] == "medium" for row in component_records),
            "low_confidence_components": sum(row["confidence"] == "low" for row in component_records),
        },
        "artifacts": artifacts,
        "decision_boundary": [
            "Every record remains unsigned and pending independent review.",
            "Approximate evidence may support a zone or Grade-B/C reconstruction but never surveyed precision.",
            "No packet, assembled artifact, tolerance, permission, or Task 17 state changes here.",
        ],
    }
    write_json(output / "manifest.json", manifest)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--historical-1400", type=Path, required=True)
    parser.add_argument("--historical-1492", type=Path, required=True)
    parser.add_argument("--ohm-snapshot", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    args = parser.parse_args()
    build(args.historical_1400, args.historical_1492, args.ohm_snapshot, args.output_dir)


if __name__ == "__main__":
    main()
