#!/usr/bin/env python3
"""Build read-only, hash-bound replacement evidence for the M25C QA blockers.

The generator never edits regional packets or an assembled candidate.  It
combines a pinned Cliopatria snapshot with the frozen assembled status,
adjacency, controls, and preflight report to produce separately reviewable
regional dossiers, direct-border candidates, and applicability audits.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

from shapely.geometry import mapping, shape
from shapely.ops import transform as shapely_transform
from shapely.strtree import STRtree


ROOT = Path(__file__).resolve().parents[1]
START_DATE = "1444-11-11"
SOURCE_COMMIT = "ad28a691b7c07c1fca89d0e0636d324667d2a258"
SOURCE_VERSION = "v0.2.0"
SOURCE_ARCHIVE_SHA256 = "d01ae3a20d358cc5d54f69d9d725d390767d9c8759ac89ad6f90c58d106f3370"
SOURCE_GEOJSON_SHA256 = "5df3b5868cfab8f76030853fa2346ed3cd71171ad807b6f72d783ee2dce6839e"
SOURCE_URL = (
    "https://github.com/Seshat-Global-History-Databank/cliopatria/"
    f"blob/{SOURCE_COMMIT}/cliopatria.geojson.zip"
)
SOURCE_DOI = "https://doi.org/10.1038/s41597-025-04516-9"
REGIONS = (
    "005", "011", "013", "014", "015", "017", "018", "021", "029",
    "030", "034", "035", "039", "053", "054", "061", "143", "145",
)

# These pairs are explicit, same-snapshot Cliopatria adjacencies.  They replace
# only missing positive-border evidence and are not used to validate modern
# negative controls or choose candidate values.
DIRECT_BORDER_PAIRS = {
    "014": ("Ethiopian Empire", "Adal Sultanate"),
    "015": ("Marinid Sultanate", "Zayyanid dynasty"),
    "030": ("Ming Dynasty", "Four Oirats"),
    "034": ("Vijayanagara Empire", "Bahmani Sultanate"),
    "035": ("Khmer Empire", "Ayutthaya Kingdom"),
    "039": ("Kingdom of Portugal", "Crown of Castile"),
    "143": ("Chagatai Khanate", "Timurid Empire"),
    "145": ("Rasulid Dynasty", "Mamluk Sultanate"),
}

APPLICABILITY_CANDIDATES = {
    "005": "evidence_supports_zone_not_line",
    "011": "evidence_supports_zone_not_line",
    "013": "non_territorial_fabric",
    "017": "evidence_supports_zone_not_line",
    "018": "non_territorial_fabric",
    "021": "non_territorial_fabric",
    "029": "non_territorial_fabric",
    "053": "non_territorial_fabric",
    "054": "evidence_supports_zone_not_line",
    "061": "no_land_adjacency",
}


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def _canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: Any) -> dict[str, Any]:
    data = _json_bytes(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return {"path": path.name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _region_from_message(message: str) -> str | None:
    normalized = message.casefold()
    for region_id in REGIONS:
        if f"region {region_id}" in normalized or f"region-{region_id}-" in normalized or f" {region_id}/" in normalized:
            return region_id
    return None


def _project_for(reference):
    center_lat = reference.centroid.y
    x_scale = 111.320 * math.cos(math.radians(center_lat))
    y_scale = 110.574
    return lambda x, y, z=None: (x * x_scale, y * y_scale)


def _active_actors(canonical: dict[str, Any]) -> dict[str, tuple[str, ...]]:
    result: dict[str, set[str]] = defaultdict(set)
    for status in canonical["statuses"]:
        if status.get("valid_from") <= START_DATE <= status.get("valid_to"):
            result[status["subject_id"]].add(status["actor_political_unit_id"])
    return {key: tuple(sorted(value)) for key, value in result.items()}


def _actor_pairs(
    region_id: str,
    canonical: dict[str, Any],
    assignments: dict[str, Any],
    adjacency_path: Path,
    disposition: str,
) -> list[dict[str, Any]]:
    region_by_province = {row["province_id"]: row["region_id"] for row in assignments["assignments"]}
    components = {
        row["province_id"]: row
        for row in canonical["components"]
        if region_by_province.get(row["province_id"]) == region_id
    }
    actors = _active_actors(canonical)
    pair_components: dict[tuple[str, str], set[str]] = defaultdict(set)
    with adjacency_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            left_id, right_id = row["from_province_id"], row["to_province_id"]
            if left_id not in components or right_id not in components:
                continue
            left, right = components[left_id], components[right_id]
            left_actors = actors.get(left["territory_component_id"], ()) or actors.get(left_id, ())
            right_actors = actors.get(right["territory_component_id"], ()) or actors.get(right_id, ())
            for left_actor in left_actors:
                for right_actor in right_actors:
                    if left_actor == right_actor:
                        continue
                    pair = tuple(sorted((left_actor, right_actor)))
                    pair_components[pair].update((left["territory_component_id"], right["territory_component_id"]))
    return [
        {
            "left_actor_id": pair[0],
            "right_actor_id": pair[1],
            "component_ids": sorted(component_ids),
            "disposition": disposition,
        }
        for pair, component_ids in sorted(pair_components.items())
    ]


def _corridor_mapping(
    region_id: str,
    canonical: dict[str, Any],
    assignments: dict[str, Any],
    source_features: list[dict[str, Any]],
    source_geometries: list[Any],
    source_tree: STRtree,
    seam,
) -> list[dict[str, Any]]:
    region_by_province = {row["province_id"]: row["region_id"] for row in assignments["assignments"]}
    actors = _active_actors(canonical)
    project = _project_for(seam)
    projected_seam = shapely_transform(project, seam)
    rows = []
    for component in canonical["components"]:
        if region_by_province.get(component["province_id"]) != region_id:
            continue
        geometry = shape(component["geometry"])
        projected = shapely_transform(project, geometry)
        distance_km = projected.distance(projected_seam)
        if distance_km > 75.0:
            continue
        point = geometry.representative_point()
        match_names = sorted(
            source_features[int(index)]["properties"]["Name"]
            for index in source_tree.query(point, predicate="intersects")
        )
        component_id = component["territory_component_id"]
        rows.append({
            "component_id": component_id,
            "province_id": component["province_id"],
            "distance_to_modern_seam_km": round(distance_km, 6),
            "current_political_unit_id": component.get("political_unit_id"),
            "current_facets": component.get("facets"),
            "current_relationship_actors": list(actors.get(component_id, ())),
            "current_evidence_ids": component.get("evidence_ids", []),
            "cliopatria_representative_point_matches": match_names,
            "source_classification": (
                "single_polity" if len(match_names) == 1 else
                "overlapping_polities" if match_names else
                "outside_cliopatria_polity_coverage"
            ),
        })
    return sorted(rows, key=lambda row: row["component_id"])


def build(cliopatria_input: Path, assembled: Path, output: Path) -> None:
    if _sha256(cliopatria_input) != SOURCE_GEOJSON_SHA256:
        raise SystemExit("Cliopatria GeoJSON checksum does not match pinned v0.2.0 bytes")

    source_doc = _load(cliopatria_input)
    source_features = sorted(
        [
            feature for feature in source_doc["features"]
            if feature["properties"]["FromYear"] <= 1444 <= feature["properties"]["ToYear"]
        ],
        key=lambda feature: (
            feature["properties"]["Name"], feature["properties"]["FromYear"],
            feature["properties"]["ToYear"], feature["properties"]["Type"],
        ),
    )
    polity_features = [feature for feature in source_features if feature["properties"]["Type"] == "POLITY"]
    source_geometries = [shape(feature["geometry"]) for feature in polity_features]
    source_tree = STRtree(source_geometries)
    source_by_name = {feature["properties"]["Name"]: feature for feature in polity_features}
    geometry_by_name = {feature["properties"]["Name"]: shape(feature["geometry"]) for feature in polity_features}

    canonical = _load(assembled / "historical-territory-status.json")
    assignments = _load(assembled / "assignments.json")
    preflight = _load(assembled / "start_date_preflight.json")
    applicability = _load(assembled / "positive-border-applicability.json")
    pass_manifest = _load(assembled / "pass_manifest.json")
    source_manifest = _load(assembled / "source_manifest.json")
    golden = _load(assembled / "golden.json")
    findings = [row for row in preflight["findings"] if row["severity"] == "error"]
    if len(findings) != 56:
        raise SystemExit(f"expected frozen 56-error baseline, found {len(findings)}")

    output.mkdir(parents=True, exist_ok=True)
    artifacts: dict[str, dict[str, Any]] = {}
    source_slice = {
        "type": "FeatureCollection",
        "source_id": "cliopatria-v0.2.0-1444",
        "attribution": "Bennett et al., Cliopatria (2025), Seshat Global History Databank",
        "source_commit": SOURCE_COMMIT,
        "license": "CC BY 4.0",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "derivation": "All source records whose inclusive FromYear/ToYear range contains 1444; features are unchanged and deterministically sorted.",
        "features": source_features,
    }
    artifacts["cliopatria_1444"] = _write_json(output / "cliopatria-1444.geojson", source_slice)

    direct_features = []
    for region_id, (left_name, right_name) in sorted(DIRECT_BORDER_PAIRS.items()):
        left, right = geometry_by_name[left_name], geometry_by_name[right_name]
        shared = left.boundary.intersection(right.boundary)
        if shared.is_empty or shared.length <= 0 or shared.geom_type not in {"LineString", "MultiLineString"}:
            raise SystemExit(f"Cliopatria pair {region_id}/{left_name}/{right_name} has no shared line")
        direct_features.append({
            "type": "Feature",
            "properties": {
                "feature_id": f"replacement-cliopatria-{region_id}-{left_name}-{right_name}".lower().replace(" ", "-"),
                "region_id": region_id,
                "start_date": START_DATE,
                "left_source_polity": left_name,
                "right_source_polity": right_name,
                "source_id": "cliopatria-v0.2.0-1444",
                "source_native_crs": "EPSG:4326",
                "source_intervals": [
                    [source_by_name[left_name]["properties"]["FromYear"], source_by_name[left_name]["properties"]["ToYear"]],
                    [source_by_name[right_name]["properties"]["FromYear"], source_by_name[right_name]["properties"]["ToYear"]],
                ],
                "derivation": "exact shared polygon-boundary intersection; no candidate or modern-control geometry used",
                "native_resolution_degrees": 0.07,
                "proposed_error_budget_km": 20.0,
                "review_status": "pending_independent_review",
            },
            "geometry": mapping(shared),
        })
    direct_doc = {"type": "FeatureCollection", "features": direct_features}
    artifacts["direct_border_candidates"] = _write_json(output / "direct-border-candidates.geojson", direct_doc)

    current_applicability = {row["region_id"]: row for row in applicability["records"]}
    applicability_reviews = []
    region_artifacts = {}
    for region_id in REGIONS:
        control_path = assembled / "regional-assets" / region_id / "negative-controls.geojson"
        seam = shape(_load(control_path)["features"][0]["geometry"])
        mapping_rows = _corridor_mapping(
            region_id, canonical, assignments, polity_features, source_geometries, source_tree, seam,
        )
        region_findings = [row for row in findings if _region_from_message(row["message"]) == region_id]
        single = sum(row["source_classification"] == "single_polity" for row in mapping_rows)
        dossier = {
            "schema_version": "1.0.0",
            "document_type": "m25c_replacement_evidence_dossier",
            "region_id": region_id,
            "start_date": START_DATE,
            "status": "pending_independent_review",
            "frozen_findings": [{"code": row["code"], "message": row["message"]} for row in region_findings],
            "review_route": (
                "direct_source_boundary" if region_id in DIRECT_BORDER_PAIRS else
                "applicability_candidate" if region_id in APPLICABILITY_CANDIDATES else
                "source_spatial_corroboration_and_component_remap"
            ),
            "cliopatria_source": {
                "version": SOURCE_VERSION,
                "commit": SOURCE_COMMIT,
                "source_geojson_sha256": SOURCE_GEOJSON_SHA256,
                "snapshot_feature_count": len(source_features),
                "polity_mapping_feature_count": len(polity_features),
                "date_rule": "FromYear <= 1444 <= ToYear",
                "license": "CC BY 4.0",
                "peer_reviewed_method_doi": SOURCE_DOI,
            },
            "corridor_component_count": len(mapping_rows),
            "single_polity_component_count": single,
            "source_coverage_ratio": round(single / len(mapping_rows), 12) if mapping_rows else 0.0,
            "direct_border_pair": list(DIRECT_BORDER_PAIRS[region_id]) if region_id in DIRECT_BORDER_PAIRS else None,
            "corridor_component_mapping": mapping_rows,
            "independence_statement": (
                "Cliopatria bytes and source geometry predate this candidate; the derivation reads neither "
                "candidate boundaries nor modern-control geometry when selecting source polity values."
            ),
            "limitations": [
                "Cliopatria encodes unquantified historical-border uncertainty.",
                "Its raster-to-vector workflow was smoothed to 0.07 degrees; the proposed 20 km budget is conservative but requires reviewer acceptance.",
                "A component outside Cliopatria polity coverage is not evidence of an empty or ungoverned landscape.",
                "This dossier authorizes no packet mutation; uncovered or overlapping components require an explicit reviewer disposition.",
            ],
        }
        record = _write_json(output / "regions" / f"{region_id}.json", dossier)
        region_artifacts[region_id] = {**record, "path": f"regions/{region_id}.json"}

        if region_id in APPLICABILITY_CANDIDATES:
            if region_id in current_applicability:
                candidate = dict(current_applicability[region_id])
            else:
                region_by_province = {
                    row["province_id"]: row["region_id"] for row in assignments["assignments"]
                }
                region_components = [
                    row for row in canonical["components"]
                    if region_by_province.get(row["province_id"]) == region_id
                ]
                source_by_id = {row["source_id"]: row for row in source_manifest["sources"]}
                source_ids = sorted({
                    source_id
                    for row in region_components
                    for source_id in row.get("evidence_ids", [])
                    if source_id in source_by_id
                    and source_by_id[source_id].get("review_status") == "reviewed"
                    and source_by_id[source_id].get("source_type") != "negative_control"
                })
                anchors = sorted(
                    row["assertion_id"] for row in golden["assertions"]
                    if row.get("region_id") == region_id
                    and row.get("layer") == "geometry"
                    and row.get("expectation") == "positive"
                    and row.get("assertion_type") == "capital"
                )
                inventory = sorted(row["territory_component_id"] for row in region_components)
                candidate = {
                    "region_id": region_id,
                    "start_date": START_DATE,
                    "status": "not_applicable",
                    "reason": APPLICABILITY_CANDIDATES[region_id],
                    "fabric_revision": pass_manifest["fabric_revision"],
                    "geometry_revision": pass_manifest["geometry_revision"],
                    "component_inventory": inventory,
                    "component_inventory_sha256": _canonical_hash(inventory),
                    "source_ids": source_ids,
                    "source_sha256": {source_id: _canonical_hash(source_by_id[source_id]) for source_id in source_ids},
                    "hard_anchor_assertion_ids": anchors,
                    "eligible_land_adjacent_actor_pairs": [],
                    "determination": "pending generated audit",
                    "independent_review": {},
                }
            candidate["reason"] = APPLICABILITY_CANDIDATES[region_id]
            candidate["eligible_land_adjacent_actor_pairs"] = _actor_pairs(
                region_id, canonical, assignments, assembled / "sidecars" / "adjacency.csv",
                candidate["reason"],
            )
            candidate["determination"] = (
                f"Independent replacement-evidence audit enumerates {len(candidate['component_inventory'])} components "
                f"and {len(candidate['eligible_land_adjacent_actor_pairs'])} distinct current land-adjacent actor pairs. "
                "Each pair remains separately decision-gated; no hard line is inferred from a modern control."
            )
            unsigned = {key: value for key, value in candidate.items() if key != "independent_review"}
            candidate["independent_review"] = {
                "status": "pending_independent_review",
                "reviewer": "pending-independent-review",
                "reviewed_at": None,
                "record_sha256": _canonical_hash(unsigned),
            }
            applicability_reviews.append(candidate)

    applicability_doc = {
        "schema_version": "0.3.0",
        "document_type": "positive_border_applicability",
        "artifact_version": applicability["artifact_version"],
        "pass_id": applicability["pass_id"],
        "start_date": START_DATE,
        "records": applicability_reviews,
    }
    artifacts["applicability_review_candidates"] = _write_json(
        output / "applicability-review-candidates.json", applicability_doc,
    )

    frozen_inputs = {}
    for relative in (
        "historical-territory-status.json", "assignments.json", "golden.json",
        "positive-border-applicability.json", "start_date_preflight.json",
        "sidecars/adjacency.csv",
    ):
        path = assembled / relative
        frozen_inputs[relative] = {"bytes": path.stat().st_size, "sha256": _sha256(path)}

    manifest = {
        "schema_version": "1.0.0",
        "document_type": "m25c_replacement_evidence_manifest",
        "generated_for": "56 non-review errors before Task 17",
        "start_date": START_DATE,
        "candidate_mutated": False,
        "source": {
            "source_id": "cliopatria-v0.2.0-1444",
            "title": "Cliopatria — worldwide political entities, 3400 BCE–2024 CE",
            "citation": "Bennett, J. S. et al. Cliopatria — A geospatial database of world-wide political entities from 3400 BCE to 2024 CE. Scientific Data 12, 247 (2025).",
            "version": SOURCE_VERSION,
            "commit": SOURCE_COMMIT,
            "url": SOURCE_URL,
            "doi": SOURCE_DOI,
            "license": "CC BY 4.0",
            "license_url": "https://creativecommons.org/licenses/by/4.0/",
            "archive_sha256": SOURCE_ARCHIVE_SHA256,
            "geojson_sha256": SOURCE_GEOJSON_SHA256,
            "review_status": "pending_independent_project_review",
        },
        "method": {
            "source_snapshot_rule": "FromYear <= 1444 <= ToYear",
            "component_sample": "Shapely representative_point tested against untouched source polygons",
            "corridor_scope": "all region components at projected distance <= 75 km from the frozen modern negative-control seam",
            "direct_border_derivation": "exact boundary intersection of two untouched same-snapshot source polygons",
            "candidate_geometry_used_to_choose_source_values": False,
            "modern_control_used_to_choose_source_values": False,
        },
        "frozen_inputs": frozen_inputs,
        "artifacts": artifacts,
        "region_artifacts": region_artifacts,
        "accounting": {
            "frozen_error_count": 56,
            "regions_with_errors": len(REGIONS),
            "direct_border_candidates": len(DIRECT_BORDER_PAIRS),
            "applicability_audits": len(APPLICABILITY_CANDIDATES),
            "regional_dossiers": len(region_artifacts),
            "task_17_advanced": False,
        },
    }
    _write_json(output / "manifest.json", manifest)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cliopatria-input", type=Path, required=True)
    parser.add_argument("--assembled-dir", type=Path, default=ROOT / "data/processed/m25c-assembled-pass")
    parser.add_argument(
        "--output-dir", type=Path,
        default=ROOT / "research/start-dates/1444-global-v1/replacement-evidence/cliopatria-v0.2.0",
    )
    args = parser.parse_args()
    build(args.cliopatria_input, args.assembled_dir, args.output_dir)


if __name__ == "__main__":
    main()
