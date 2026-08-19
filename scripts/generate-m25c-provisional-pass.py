#!/usr/bin/env python3
"""Generate the deterministic, non-promotable M25C worldwide provisional pass."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from shapely.geometry import mapping, shape
from shapely.ops import unary_union
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gpm.qa.start_date import run_start_date_qa  # noqa: E402
from gpm.schemas import WORLDWIDE_M49_SUBREGIONS  # noqa: E402

PASS_ID = "official-1444-global-v1"
START_DATE = "1444-11-11"
VERSION = "1.0.0-provisional.1"
PROVISIONAL_SOURCE_ID = "official-1444-modern-scaffold-provisional"

APPROVED_REVIEWED_SCAFFOLD_POLITIES = frozenset({
    "scenario-ara", "scenario-ava", "scenario-ayu", "scenario-bah", "scenario-bav",
    "scenario-ben", "scenario-boh", "scenario-bos", "scenario-bra", "scenario-bre",
    "scenario-bri", "scenario-bur", "scenario-byz", "scenario-cas", "scenario-col",
    "scenario-cri", "scenario-cyp", "scenario-dai", "scenario-dan", "scenario-del",
    "scenario-eng", "scenario-fer", "scenario-flo", "scenario-fra", "scenario-gen",
    "scenario-geo", "scenario-gra", "scenario-guj", "scenario-hab", "scenario-han",
    "scenario-hes", "scenario-hun", "scenario-jap", "scenario-kor", "scenario-lit",
    "scenario-luc", "scenario-mam", "scenario-mlo", "scenario-mng", "scenario-mol",
    "scenario-mor", "scenario-mos", "scenario-nap", "scenario-nav", "scenario-nep",
    "scenario-nov", "scenario-oir", "scenario-pal", "scenario-pap", "scenario-pol",
    "scenario-pom", "scenario-por", "scenario-pro", "scenario-qqa", "scenario-sah",
    "scenario-sav", "scenario-sax", "scenario-ser", "scenario-sie", "scenario-swi",
    "scenario-teu", "scenario-tib", "scenario-tim", "scenario-tlc", "scenario-tun",
    "scenario-tur", "scenario-uzb", "scenario-ven", "scenario-vij", "scenario-wal",
    "scenario-wur",
})

APPROVED_PRUNED_SCAFFOLD_POLITIES = frozenset({
    "scenario-abw", "scenario-aia", "scenario-ald", "scenario-asm", "scenario-ata",
    "scenario-atc", "scenario-atf", "scenario-atg", "scenario-bdi", "scenario-bjn",
    "scenario-blm", "scenario-bmu", "scenario-brb", "scenario-brt", "scenario-bwa",
    "scenario-caf", "scenario-chag", "scenario-civ", "scenario-clp", "scenario-cnm",
    "scenario-cok", "scenario-com", "scenario-cpv", "scenario-csi", "scenario-cuw",
    "scenario-cym", "scenario-cyn", "scenario-dji", "scenario-dma", "scenario-esb",
    "scenario-eth", "scenario-flk", "scenario-fro", "scenario-fsm", "scenario-gab",
    "scenario-ggy", "scenario-gmb", "scenario-gnb", "scenario-gnq", "scenario-grd",
    "scenario-grl", "scenario-gum", "scenario-ham", "scenario-hkg", "scenario-hmd",
    "scenario-imn", "scenario-ioa", "scenario-iot", "scenario-ire", "scenario-jey",
    "scenario-kab", "scenario-kan", "scenario-kas", "scenario-ken", "scenario-khm",
    "scenario-kir", "scenario-kna", "scenario-kon", "scenario-kos", "scenario-lbr",
    "scenario-lca", "scenario-liv", "scenario-lso", "scenario-mac", "scenario-maf",
    "scenario-mal", "scenario-man", "scenario-mdv", "scenario-mhl", "scenario-mnp",
    "scenario-moz", "scenario-mrt", "scenario-msr", "scenario-mus", "scenario-mwi",
    "scenario-nah", "scenario-nam", "scenario-ncl", "scenario-nfk", "scenario-niu",
    "scenario-nor", "scenario-nru", "scenario-oyo", "scenario-pcn", "scenario-pga",
    "scenario-plw", "scenario-psx", "scenario-pyf", "scenario-rwa", "scenario-sco",
    "scenario-scr", "scenario-sds", "scenario-sgs", "scenario-shn", "scenario-slb",
    "scenario-sle", "scenario-sol", "scenario-som", "scenario-son", "scenario-spi",
    "scenario-spm", "scenario-stp", "scenario-swe", "scenario-swz", "scenario-sxm",
    "scenario-syc", "scenario-tca", "scenario-tgo", "scenario-tls", "scenario-ton",
    "scenario-tto", "scenario-tuv", "scenario-tza", "scenario-uga", "scenario-umi",
    "scenario-unk", "scenario-usg", "scenario-vct", "scenario-vgb", "scenario-vir",
    "scenario-vut", "scenario-wlf", "scenario-wsb", "scenario-wsm", "scenario-zaf",
    "scenario-zmb", "scenario-zwe",
})

APPROVED_LEGACY_CORE_COUNTS = {
    "scenario-ald": 61,
    "scenario-fro": 12,
    "scenario-ggy": 6,
    "scenario-imn": 2,
    "scenario-ire": 39,
    "scenario-jey": 1,
    "scenario-liv": 27,
    "scenario-nor": 73,
    "scenario-sco": 99,
    "scenario-swe": 514,
}

APPROVED_REDUNDANT_PILOT_ASSERTIONS = frozenset({
    "capital-burgundy-politics-1444",
    "capital-burgundy-relationships-1444",
    "capital-central-europe-politics-1444",
    "capital-central-europe-relationships-1444",
    "capital-france-politics-1444",
    "capital-france-relationships-1444",
    "capital-hre-politics-1444",
    "capital-hre-relationships-1444",
    "capital-low-countries-politics-1444",
    "capital-low-countries-relationships-1444",
})
GENERATED_AT = "2026-08-14T00:00:00Z"
PROFILE = "eu-like"
AGGREGATION_REVISION = "1444-r2"
GEOMETRY_REVISION = "1444-r2"
TARGET_PROVINCES = 22_000
LAYERS = ("geometry", "politics", "hierarchy", "gazetteer_relationships")

DEFAULT_OUTPUT = ROOT / "data" / "processed" / "m25c-provisional"
GLOBAL = ROOT / "research" / "start-dates" / "1444-global-v1"
PILOT = ROOT / "research" / "start-dates" / "1444-v2"
ANOMALY = ROOT / "data" / "processed" / "m25c-global-staging" / "evidence"
SCENARIO = ROOT / "data" / "processed" / "demo_build" / "atlas" / "scenarios" / "official-1444"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--global-input", type=Path, default=GLOBAL)
    parser.add_argument("--pilot-input", type=Path, default=PILOT)
    parser.add_argument("--anomaly-input", type=Path, default=ANOMALY)
    parser.add_argument("--scenario-input", type=Path, default=SCENARIO)
    parser.add_argument("--regional-packets-dir", type=Path)
    parser.add_argument("--qa", action="store_true")
    args = parser.parse_args()
    generate(args)
    if args.qa:
        result = run_start_date_qa(
            pass_dir=args.output_dir,
            report_output=args.output_dir / "start_date_provisional_qa.json",
            provisional_internal_review=True,
        )
        print(json.dumps(result.to_dict(), sort_keys=True))
        if not result.passed:
            return 1
    return 0


def generate(args: argparse.Namespace) -> None:
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    sidecars = output / "sidecars"
    sidecars.mkdir(exist_ok=True)

    packets = _load_packets(args.regional_packets_dir)
    mask = _load(args.global_input / "world_coverage_mask.geojson")
    location_region_overrides = {
        row["location_id"]: row["region_id"]
        for packet in packets for row in packet.get("location_region_overrides") or []
    }
    for feature in mask["features"]:
        location_id = feature["properties"]["location_id"]
        if location_id in location_region_overrides:
            feature["properties"]["region_id"] = location_region_overrides[location_id]
    mask_features = sorted(mask["features"], key=lambda f: f["properties"]["location_id"])
    locations = {f["properties"]["location_id"]: f for f in mask_features}
    if len(locations) != 23_582:
        raise SystemExit(f"provisional mask must contain 23582 locations, found {len(locations)}")
    regions = {f["properties"]["region_id"] for f in mask_features}
    if regions != WORLDWIDE_M49_SUBREGIONS:
        raise SystemExit("provisional mask does not span the exact 22 M49 subregions")

    original_groups: dict[str, list[str]] = defaultdict(list)
    with (args.global_input / "sidecars" / "province_membership.csv").open(newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            if row["location_id"] in locations:
                original_groups[row["province_id"]].append(row["location_id"])
    if {item for group in original_groups.values() for item in group} != set(locations):
        raise SystemExit("accepted r2 membership does not close over the playable mask")

    pilot_assignments = _load(args.pilot_input / "assignments.json")["assignments"]
    locked = [
        sorted(row["location_ids"])
        for row in pilot_assignments
        if set(row["location_ids"]).issubset(locations)
    ]
    groups = _target_groups(original_groups, locked, TARGET_PROVINCES)
    memberships = []
    province_geometries: dict[str, Any] = {}
    for group in groups:
        members = [(location_id, "whole") for location_id in group]
        province_id = _derived_province_id(members)
        memberships.extend((province_id, location_id, "whole") for location_id in group)
        province_geometries[province_id] = unary_union([shape(locations[item]["geometry"]) for item in group])

    _write_csv(sidecars / "province_membership.csv", ("province_id", "location_id", "piece_id"), memberships)
    locations_document = _load(args.global_input / "sidecars" / "locations.geojson")
    locations_document["features"] = mask_features
    locations_document.setdefault("gpm", {})["provisional_playable_location_count"] = len(mask_features)
    _write(sidecars / "locations.geojson", locations_document)
    fabric = _load(args.global_input / "sidecars" / "location_fabric_manifest.json")
    fabric["actual_location_count"] = len(mask_features)
    fabric.setdefault("counts", {})["locations"] = len(mask_features)
    fabric["provisional_filter"] = "accepted-m49-playable-mask-non-antarctic"
    _write(sidecars / "location_fabric_manifest.json", fabric)
    shutil.copyfile(args.global_input / "sidecars" / "location_lineage.json", sidecars / "location_lineage.json")

    location_to_province = {location_id: province_id for province_id, location_id, _ in memberships}
    adjacency = _province_adjacency(args.global_input / "sidecars" / "location_adjacency.csv", location_to_province)
    _write_csv(sidecars / "adjacency.csv", ("from_province_id", "to_province_id"), adjacency)

    sources = _merge_records(
        "source_id",
        _load(args.anomaly_input / "source_manifest.json")["sources"],
        _load(args.pilot_input / "source_manifest.json")["sources"],
    )
    sources.append(_provisional_source(args.scenario_input / "ownership_choropleth.geojson"))
    sources = sorted(_merge_records("source_id", sources), key=lambda row: row["source_id"])
    source_manifest = _header("start_date_source_manifest") | {
        "sources": sources,
        "conflict_resolution_notes": [
            "Accepted anomaly-census and pilot sources retain their reviewed state.",
            "The official-1444 modern-scaffold transfer is planned provisional evidence only.",
        ],
    }
    _copy_derived_artifacts(args.anomaly_input, output, _load(args.anomaly_input / "source_manifest.json")["sources"])
    _copy_derived_artifacts(args.pilot_input, output, _load(args.pilot_input / "source_manifest.json")["sources"])

    scenario_features = _load(args.scenario_input / "ownership_choropleth.geojson")["features"]
    transfer = _transfer_scenario(province_geometries, scenario_features)
    pilot_by_group = {tuple(sorted(row["location_ids"])): row for row in pilot_assignments}
    country_names = {row["tag"]: row.get("display_name") or row["tag"] for row in _load(args.scenario_input / "countries.json")["countries"]}
    polities = _merge_polities(
        _load(args.pilot_input / "gazetteer.json")["polities"],
        _load(args.anomaly_input / "gazetteer.json")["polities"],
    )
    known_polities = {row["polity_id"] for row in polities}
    for tag in sorted({str(feature["properties"].get("owner") or "UNK") for feature in scenario_features}):
        polity_id = _tag_polity(tag)
        if polity_id not in known_polities:
            polities.append({
                "polity_id": polity_id, "name": country_names.get(tag, tag), "aliases": [tag],
                "valid_from": None, "valid_to": None, "capital_location_ids": [], "relationships": [],
                "source_ids": ["official-1444-modern-scaffold-provisional"],
            })
    polities.sort(key=lambda row: row["polity_id"])
    gazetteer = _header("polity_gazetteer") | {"polities": polities}

    assignments_rows = []
    province_regions: dict[str, str] = {}
    for group in groups:
        province_id = _derived_province_id([(item, "whole") for item in group])
        pilot = pilot_by_group.get(tuple(group))
        region = _majority(locations[item]["properties"]["region_id"] for item in group)
        if pilot:
            sovereign, owner, controller = (pilot[key] for key in ("sovereign_polity_id", "owner_polity_id", "controller_polity_id"))
            source_ids = sorted(pilot["source_ids"])
            polity_ids = sorted(set(pilot["polity_ids"]) | {sovereign, owner, controller})
            cores = sorted(pilot.get("core_polity_ids") or [owner])
            claims = sorted(pilot.get("claim_polity_ids") or [])
            disputes = sorted(pilot.get("dispute_polity_ids") or [])
            note = "Accepted 1444-v2 pilot treatment retained exactly."
        else:
            tag = transfer[province_id]["owner"]
            owner = controller = sovereign = _tag_polity(tag)
            source_ids = ["official-1444-modern-scaffold-provisional"]
            polity_ids, cores, claims, disputes = [owner], [owner], [], []
            note = "Provisional politics transferred by maximum-area overlap; not historical evidence."
        province_regions[province_id] = region
        assignments_rows.append({
            "assignment_id": f"asg-{province_id}", "location_ids": group, "province_id": province_id,
            "polity_ids": polity_ids, "uncertainty": 0.25 if pilot else 1.0, "source_ids": source_ids,
            "notes": note, "region_id": region, "sovereign_polity_id": sovereign,
            "owner_polity_id": owner, "controller_polity_id": controller,
            "core_polity_ids": cores, "claim_polity_ids": claims, "dispute_polity_ids": disputes,
            "hierarchy": {"area_id": f"area-{region}-{owner}", "region_id": region,
                          "superregion_id": f"m49-superregion-{region}",
                          "method": "provisional-owner-region-grouping-v1"},
        })
    assignments_rows.sort(key=lambda row: row["province_id"])

    boundaries = _provisional_boundaries(args.pilot_input, scenario_features)
    _write(output / "boundaries.geojson", boundaries)
    constraint_hash = _sha256(output / "boundaries.geojson")
    aggregation = {
        "schema_version": "0.1.0", "manifest_type": "province_aggregation",
        "fabric_id": "global-h3-v1", "fabric_revision": "2", "start_date": START_DATE,
        "profile_id": PROFILE, "aggregation_revision": AGGREGATION_REVISION,
        "geometry_revision": GEOMETRY_REVISION, "actual_province_count": TARGET_PROVINCES,
        "input_location_count": len(locations), "input_piece_count": len(locations),
        "merge_count": len(locations) - TARGET_PROVINCES, "modern_boundary_influence": "none",
        "algorithm": "accepted-membership-filter-with-deterministic-resplit",
        "historical_constraint_policy": {"hard_constraints": "remove_crossing_merge_edges",
                                           "soft_evidence": "merge_score_penalty_only", "sha256": constraint_hash},
        "generated_at": GENERATED_AT, "generator_version": VERSION,
        "files": ["locations.geojson", "province_membership.csv"],
        "inputs": {"locations": "locations.geojson", "historical_constraints": "../boundaries.geojson", "modern_pieces": None},
        "provisional": True,
    }
    _write(sidecars / "aggregation_manifest.json", aggregation)
    assignments = _header("start_date_location_assignments") | {
        "fabric_revision": "global-h3-v1-r2", "aggregation_revision": AGGREGATION_REVISION,
        "aggregation_profile": PROFILE, "geometry_revision": GEOMETRY_REVISION,
        "expected_province_count": TARGET_PROVINCES, "constraint_sha256": constraint_hash,
        "fabric_sidecars": _sidecar_records(output, {
            "fabric_manifest": "sidecars/location_fabric_manifest.json", "locations": "sidecars/locations.geojson",
            "lineage": "sidecars/location_lineage.json", "province_membership": "sidecars/province_membership.csv",
        }),
        "release_sidecars": _sidecar_records(output, {
            "aggregation_manifest": "sidecars/aggregation_manifest.json", "adjacency": "sidecars/adjacency.csv",
        }),
        "assignments": assignments_rows, "targeted_split_requests": [],
    }
    _write(output / "assignments.json", assignments)

    capital_features = [
        feature for feature in _load(args.pilot_input / "build.geojson")["features"]
        if feature["properties"]["feature_type"] == "capital"
    ]
    capital_index = {feature["properties"]["feature_id"]: feature for feature in capital_features}
    for packet in packets:
        for feature in packet.get("build_features") or []:
            capital_index[feature["properties"]["feature_id"]] = {
                "type": "Feature",
                "properties": {
                    "feature_id": feature["properties"]["feature_id"],
                    "feature_type": "capital",
                },
                "geometry": json.loads(json.dumps(feature["geometry"])),
            }
    capital_features = list(capital_index.values())
    capital_ids = [feature["properties"]["feature_id"] for feature in capital_features]
    if len(capital_ids) != len(set(capital_ids)):
        raise SystemExit("regional packet build feature IDs must be globally unique")
    build = _header("start_date_full_build_geometry") | {
        "geometry_revision": GEOMETRY_REVISION, "type": "FeatureCollection",
        "features": [{"type": "Feature", "properties": {"feature_id": province_id, "feature_type": "province"},
                      "geometry": mapping(province_geometries[province_id])}
                     for province_id in sorted(province_geometries)] + capital_features,
    }
    _write(output / "build.geojson", build)

    golden = _load(args.pilot_input / "golden.json")
    golden.update(_header("spatial_golden_borders"))
    boundary_index = {f["properties"]["feature_id"]: f for f in boundaries["features"]}
    for assertion in golden["assertions"]:
        if assertion["assertion_type"] == "capital":
            assertion["subject_ids"][1] = location_to_province[assertion["subject_ids"][0]]
        source_ids = sorted({sid for bid in assertion["boundary_feature_ids"] for sid in boundary_index[bid]["properties"]["source_ids"]})
        if not source_ids:
            source_ids = ["official-1444-modern-scaffold-provisional"]
        assertion["tolerance_policy"] = {"fixed_before_measurement": True,
                                         "source_derived_tolerance": assertion["tolerance"], "source_ids": source_ids}
    _write(output / "golden.json", golden)

    coverage_rows = []
    for region in sorted(WORLDWIDE_M49_SUBREGIONS):
        for layer in LAYERS:
            grade = "B" if layer == "politics" else "C"
            coverage_rows.append({
                "region_id": region, "layer": layer, "grade": grade,
                "source_ids": ["official-1444-modern-scaffold-provisional"], "assertion_ids": [],
                "evidence_summary": "Structural provisional coverage only; exact-date regional promotion remains pending.",
                "exclusions": [], "known_gaps": [
                    "No certification-grade exact-date regional packet has replaced this provisional layer."
                ],
            })
    coverage = _header("start_date_coverage") | {
        "coverage": coverage_rows, "exclusions": [],
        "known_gaps": ["All 22 regions require four-layer Grade-A promotion before certification."],
    }
    _apply_packets(packets, source_manifest, gazetteer, boundaries, golden, assignments, coverage)
    _apply_approved_polity_source_cleanup(
        source_manifest, gazetteer, boundaries, golden, assignments, coverage,
    )
    boundaries["features"].sort(key=lambda feature: feature["properties"]["feature_id"])
    golden["assertions"].sort(key=lambda row: row["assertion_id"])
    assignments["assignments"].sort(key=lambda row: row["province_id"])
    coverage["coverage"].sort(key=lambda row: (row["region_id"], row["layer"]))
    _write(output / "boundaries.geojson", boundaries)
    constraint_hash = _sha256(output / "boundaries.geojson")
    aggregation["historical_constraint_policy"]["sha256"] = constraint_hash
    _write(sidecars / "aggregation_manifest.json", aggregation)
    assignments["constraint_sha256"] = constraint_hash
    assignments["release_sidecars"]["aggregation_manifest"]["sha256"] = _sha256(sidecars / "aggregation_manifest.json")
    for name, document in (("source_manifest.json", source_manifest), ("gazetteer.json", gazetteer),
                           ("golden.json", golden), ("assignments.json", assignments),
                           ("coverage.json", coverage)):
        _write(output / name, document)

    canonical = _canonical_status(province_geometries, assignments["assignments"])
    inventory = _load(args.global_input / "anomaly_inventory.json")
    canonical["accepted_anomaly_ids"] = sorted(row["anomaly_id"] for row in inventory["anomalies"])
    canonical["qa_mode"] = "provisional_internal_review"
    canonical["artifact_version"] = VERSION
    _write(output / "historical-territory-status.json", canonical)
    shutil.copyfile(args.global_input / "anomaly_inventory.json", output / "anomaly_inventory.json")
    ledger = _load(args.anomaly_input / "anomaly_census_review_ledger.json")
    ledger["artifact_version"] = VERSION
    _write(output / "anomaly_census_review_ledger.json", ledger)
    _write(output / "world_coverage_mask.geojson", mask)
    _copy_packet_derived_files(packets, output)

    changelog = _header("start_date_changelog") | {
        "version": VERSION, "released_at": "2026-08-14",
        "changes": [{"change_id": "provisional-worldwide-seed", "category": "research",
                     "summary": "Transferred official-1444 scaffold politics by maximum-area overlap; output is non-promotable.",
                     "affected_ids": sorted(WORLDWIDE_M49_SUBREGIONS)}],
        "migrations": ["No runtime or public migration is permitted from provisional_internal_review output."],
    }
    _write(output / "changelog.json", changelog)
    (output / "dossier.md").write_text(_dossier(packets), encoding="utf-8")
    review = {"schema_version": "1.0.0", "pass_id": PASS_ID, "generator": "gpm qa render",
              "reviewer": "pending-independent-review", "status": "pending_independent_review", "renders": []}
    _write(output / "review" / "review_manifest.json", review)

    artifact_files = {
        "dossier": "dossier.md", "source_manifest": "source_manifest.json", "boundary_registry": "boundaries.geojson",
        "polity_gazetteer": "gazetteer.json", "location_assignments": "assignments.json", "golden_borders": "golden.json",
        "full_build_geometry": "build.geojson", "coverage_matrix": "coverage.json", "changelog": "changelog.json",
        "canonical_historical_status": "historical-territory-status.json", "world_coverage_mask": "world_coverage_mask.geojson",
        "anomaly_inventory": "anomaly_inventory.json", "anomaly_review_ledger": "anomaly_census_review_ledger.json",
    }
    artifacts = {role: {"path": name, "version": _artifact_version(output / name), "sha256": _sha256(output / name)}
                 for role, name in artifact_files.items()}
    manifest = {
        "schema_version": "0.3.0", "document_type": "start_date_research_pass", "artifact_version": VERSION,
        "pass_id": PASS_ID, "start_date": START_DATE, "version": VERSION, "era": "late-medieval",
        "fabric_revision": "global-h3-v1-r2", "geometry_revision": GEOMETRY_REVISION,
        "generated_at": GENERATED_AT, "qa_mode": "provisional_internal_review",
        "scope": {"kind": "worldwide", "regions": sorted(WORLDWIDE_M49_SUBREGIONS),
                  "priority_regions": sorted(WORLDWIDE_M49_SUBREGIONS), "layers": list(LAYERS),
                  "world_coverage_mask_sha256": artifacts["world_coverage_mask"]["sha256"],
                  "partition": {"standard": "UN M49", "revision": "2026-08-14",
                                "antarctica": "excluded-not-in-playable-fabric",
                                "subregions": sorted(WORLDWIDE_M49_SUBREGIONS)}},
        "artifacts": artifacts,
        "review": {"manifest_path": "review/review_manifest.json", "sha256": _sha256(output / "review" / "review_manifest.json"),
                   "generator": "gpm qa render", "reviewer": "pending-independent-review",
                   "status": "pending_independent_review"},
    }
    _write(output / "pass_manifest.json", manifest)
    _write(output / "candidate_status.json", {"pass_id": PASS_ID, "start_date": START_DATE,
           "status": "provisional_internal_review", "public_release_allowed": False,
           "review_acceptance_allowed": False, "certification_allowed": False, "runtime_publication_allowed": False})


def _target_groups(original: dict[str, list[str]], locked: list[list[str]], target: int) -> list[list[str]]:
    used: set[str] = set()
    groups: list[list[str]] = []
    for group in sorted(locked):
        if used.intersection(group):
            raise SystemExit("pilot assignment groups overlap")
        used.update(group); groups.append(group)
    for province_id in sorted(original):
        remainder = sorted(set(original[province_id]) - used)
        if remainder:
            groups.append(remainder)
    while len(groups) < target:
        candidates = [(len(group), group, index) for index, group in enumerate(groups) if len(group) > 1]
        if not candidates:
            raise SystemExit("cannot split membership to requested province target")
        _size, group, index = max(candidates, key=lambda row: (row[0], row[1]))
        groups[index] = group[:-1]
        groups.append([group[-1]])
    if len(groups) != target:
        raise SystemExit(f"playable membership already exceeds target: {len(groups)} > {target}")
    result = sorted((sorted(group) for group in groups), key=lambda group: group)
    flat = [item for group in result for item in group]
    if len(flat) != len(set(flat)):
        raise SystemExit("generated membership is not exact-once")
    return result


def _derived_province_id(members: list[tuple[str, str]]) -> str:
    payload = json.dumps({"members": sorted(members), "profile_id": PROFILE, "start_date": START_DATE,
                          "aggregation_revision": AGGREGATION_REVISION, "geometry_revision": GEOMETRY_REVISION},
                         sort_keys=True, separators=(",", ":"))
    return f"prv_{hashlib.sha256(payload.encode()).hexdigest()[:20]}"


def _transfer_scenario(provinces: dict[str, Any], features: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    geometries = [shape(feature["geometry"]) for feature in features]
    tree = STRtree(geometries)
    result = {}
    for province_id in sorted(provinces):
        geometry = provinces[province_id]
        ranked = []
        for index in tree.query(geometry):
            area = geometry.intersection(geometries[int(index)]).area
            if area > 0:
                ranked.append((area, str(features[int(index)]["properties"].get("owner") or "UNK"), int(index)))
        if not ranked:
            point = geometry.representative_point()
            nearest = int(tree.nearest(point))
            ranked.append((0.0, str(features[nearest]["properties"].get("owner") or "UNK"), nearest))
        _, owner, index = sorted(ranked, key=lambda row: (-row[0], row[1], row[2]))[0]
        result[province_id] = {"owner": owner, "source_province_id": features[index]["properties"]["province_id"]}
    return result


def _provisional_boundaries(pilot: Path, scenario_features: list[dict[str, Any]]) -> dict[str, Any]:
    document = _load(pilot / "boundaries.geojson")
    document.update(_header("historical_boundary_registry"))
    owner_geometries: dict[str, list[Any]] = defaultdict(list)
    for feature in scenario_features:
        owner_geometries[str(feature["properties"].get("owner") or "UNK")].append(shape(feature["geometry"]))
    owners = sorted(owner_geometries)
    dissolved = [unary_union(owner_geometries[owner]) for owner in owners]
    tree = STRtree(dissolved)
    for left_index, left in enumerate(dissolved):
        for right_raw in tree.query(left):
            right_index = int(right_raw)
            if right_index <= left_index:
                continue
            shared = left.boundary.intersection(dissolved[right_index].boundary)
            if shared.is_empty or shared.geom_type not in {"LineString", "MultiLineString"}:
                continue
            left_owner, right_owner = owners[left_index], owners[right_index]
            document["features"].append({"type": "Feature", "geometry": mapping(shared), "properties": {
                "feature_id": f"provisional-owner-boundary-{_slug(left_owner)}-{_slug(right_owner)}",
                "geometry_revision": GEOMETRY_REVISION, "valid_from": None, "valid_to": None,
                "date_precision": "unknown", "semantics": "soft provisional scenario ownership boundary",
                "side_polity_ids": {"left": _tag_polity(left_owner), "right": _tag_polity(right_owner)},
                "source_ids": ["official-1444-modern-scaffold-provisional"],
                "license_lineage": ["Natural Earth public domain", "internal curated-politics scenario"],
                "confidence": "provisional", "uncertainty_notes": "Never a hard historical constraint.",
                "classification": "soft_evidence", "geographic_scope": "worldwide",
                "start_date_programs": [START_DATE],
            }})
    document["features"].sort(key=lambda feature: feature["properties"]["feature_id"])
    return document


def _canonical_status(geometries: dict[str, Any], assignments: list[dict[str, Any]]) -> dict[str, Any]:
    components, provinces, statuses = [], [], []
    unit_components: dict[str, list[str]] = defaultdict(list)
    assignment_index = {row["province_id"]: row for row in assignments}
    for province_id in sorted(geometries):
        component_id = f"cmp-{province_id}"
        assignment = assignment_index[province_id]
        sovereign, owner, controller = (
            assignment["sovereign_polity_id"], assignment["owner_polity_id"], assignment["controller_polity_id"]
        )
        evidence = assignment["source_ids"]
        components.append({"territory_component_id": component_id, "political_unit_id": owner,
                           "province_id": province_id, "geometry": mapping(geometries[province_id]),
                           "historically_required": True, "minimum_area_merge_exempt": True,
                           "evidence_ids": evidence, "provisional": True})
        unit_components[owner].append(component_id)
        provinces.append({"province_id": province_id, "territory_component_ids": [component_id],
                          "hierarchy": assignment_index[province_id]["hierarchy"], "provisional": True})
        for relationship, actor in (("sovereign", sovereign), ("owner", owner), ("controller", controller)):
            statuses.append({"subject_id": component_id, "relationship": relationship,
                             "actor_political_unit_id": actor, "valid_from": START_DATE, "valid_to": START_DATE,
                             "evidence_ids": evidence, "certainty": "uncertain" if evidence == ["official-1444-modern-scaffold-provisional"] else "documented"})
    actor_ids = {
        actor for row in assignments
        for actor in (row["sovereign_polity_id"], row["owner_polity_id"], row["controller_polity_id"])
    }
    political_units = [{"political_unit_id": unit, "territory_component_ids": sorted(components_for_unit),
                        "documented_status": "provisional owner grouping"}
                       for unit, components_for_unit in sorted(unit_components.items())]
    external = sorted(actor_ids - set(unit_components))
    return {"schema_version": "0.1.0", "pass_id": PASS_ID, "start_date": START_DATE, "scenario_id": PASS_ID,
            "components": components, "political_units": political_units, "provinces": provinces,
            "statuses": statuses, "external_actor_ids": external, "adjacency": []}


def _load_packets(directory: Path | None) -> list[dict[str, Any]]:
    if directory is None:
        return []
    packets = []
    for path in sorted(directory.glob("*.json")):
        packet = _load(path)
        packet["_packet_path"] = str(path.resolve())
        packets.append(packet)
    for packet in packets:
        if packet.get("packet_type") != "m25c_regional_evidence" or packet.get("start_date") != START_DATE:
            raise SystemExit("regional packet has invalid type/date")
        if packet.get("region_id") not in WORLDWIDE_M49_SUBREGIONS:
            raise SystemExit("regional packet has invalid M49 region")
        if not packet.get("as_of_date") or not packet.get("source_pins"):
            raise SystemExit("regional packet must be dated and source-pinned")
        for pin in packet["source_pins"]:
            if (
                not isinstance(pin, dict) or not pin.get("source_id") or not pin.get("locator")
                or not re.fullmatch(r"[0-9a-f]{64}", str(pin.get("sha256") or ""))
            ):
                raise SystemExit("regional packet source pins require source_id, exact locator, and sha256")
        _qualify_grade_a_packet(packet, Path(packet["_packet_path"]))
    return sorted(packets, key=lambda row: (row["region_id"], row["as_of_date"], row.get("packet_id", "")))


def _qualify_grade_a_packet(packet: dict[str, Any], packet_path: Path | None = None) -> None:
    rows = packet.get("coverage") or []
    if not any(row.get("grade") == "A" for row in rows):
        return
    region = packet["region_id"]
    indexed = {(row.get("region_id"), row.get("layer")): row for row in rows}
    if set(indexed) != {(region, layer) for layer in LAYERS}:
        raise SystemExit(f"Grade-A packet {region} must replace all four regional layers")
    if any(row.get("grade") != "A" or row.get("known_gaps") or row.get("exclusions") for row in rows):
        raise SystemExit(f"Grade-A packet {region} must be gap-free across all four layers")
    if packet.get("visual_review") != "accepted" or not all(
        packet.get(flag) is True for flag in (
            "complete_assignment_coverage", "complete_status_coverage", "complete_hierarchy_coverage",
        )
    ):
        raise SystemExit(f"Grade-A packet {region} lacks accepted visual review or completeness attestations")
    source_index = {row["source_id"]: row for row in packet.get("sources") or []}
    pin_index = {row["source_id"]: row for row in packet["source_pins"]}
    pin_ids = set(pin_index)
    for source_id, pin in pin_index.items():
        source = source_index.get(source_id)
        if source is None or pin["sha256"] != _source_pin_sha256(source, pin["locator"]):
            raise SystemExit(f"Grade-A packet {region} has an invalid canonical source pin for {source_id}")
    for row in rows:
        cited = row.get("source_ids") or []
        if not cited or not set(cited).issubset(pin_ids):
            raise SystemExit(f"Grade-A packet {region}/{row['layer']} cites unpinned evidence")
        evidence = [source_index.get(source_id) for source_id in cited]
        if any(source is None or source.get("review_status") != "reviewed" for source in evidence):
            raise SystemExit(f"Grade-A packet {region}/{row['layer']} lacks reviewed source records")
        if not any(source.get("source_type") in {"academic", "primary"} for source in evidence if source):
            raise SystemExit(f"Grade-A packet {region}/{row['layer']} lacks an academic or primary anchor")
        if any(not _source_applies(source, START_DATE) for source in evidence if source):
            raise SystemExit(f"Grade-A packet {region}/{row['layer']} contains evidence not applicable on {START_DATE}")
    for feature in packet.get("boundary_features") or []:
        props = feature.get("properties") or {}
        if props.get("classification") != "hard_constraint":
            continue
        evidence = [source_index.get(source_id) for source_id in props.get("source_ids") or []]
        groups = {source.get("independence_group") for source in evidence if source}
        if len(groups) < 2:
            raise SystemExit(f"Grade-A hard boundary {props.get('feature_id')} lacks independent corroboration")
    build_ids: set[str] = set()
    for feature in packet.get("build_features") or []:
        props = feature.get("properties") or {}
        feature_id = props.get("feature_id")
        if (
            not feature_id or feature_id in build_ids or props.get("feature_type") != "capital"
            or (feature.get("geometry") or {}).get("type") != "Point"
            or not set(props.get("source_ids") or []).issubset(pin_ids)
        ):
            raise SystemExit(f"Grade-A packet {region} has an invalid or duplicate build feature")
        build_ids.add(feature_id)
    asset_ids: set[str] = set()
    target_paths: set[str] = set()
    for derived in packet.get("derived_files") or []:
        asset_id = derived.get("asset_id")
        relative = Path(str(derived.get("path") or ""))
        target = Path(str(derived.get("target_path") or ""))
        if (
            not asset_id or asset_id in asset_ids or not relative.parts or relative.is_absolute()
            or ".." in relative.parts or not target.parts or target.is_absolute() or ".." in target.parts
            or target.as_posix() in target_paths
            or not re.fullmatch(r"[0-9a-f]{64}", str(derived.get("sha256") or ""))
            or not set(derived.get("source_ids") or []).issubset(pin_ids)
            or len({source_index[sid]["independence_group"] for sid in derived.get("source_ids") or []}) < 2
            or not _source_applies(derived, START_DATE)
        ):
            raise SystemExit(f"Grade-A packet {region} has an invalid derived file declaration")
        asset_ids.add(asset_id)
        target_paths.add(target.as_posix())
        if packet_path is not None:
            asset_path = packet_path.parent / relative
            try:
                asset_path.resolve().relative_to(packet_path.parent.resolve())
            except ValueError as exc:
                raise SystemExit(f"Grade-A packet {region} derived file escapes packet assets") from exc
            if asset_path.is_symlink() or not asset_path.is_file() or _sha256(asset_path) != derived["sha256"]:
                raise SystemExit(f"Grade-A packet {region} derived file is missing or checksum-invalid: {asset_id}")


def _source_applies(source: dict[str, Any], start_date: str) -> bool:
    def bound(value: Any, high: bool) -> str:
        text = str(value or "")
        if re.fullmatch(r"\d{4}", text):
            return f"{text}-12-31" if high else f"{text}-01-01"
        return text or ("9999-12-31" if high else "0001-01-01")
    return bound(source.get("valid_from"), False) <= start_date <= bound(source.get("valid_to"), True)


def _source_pin_sha256(source: dict[str, Any], locator: str) -> str:
    """Bind a packet pin to the complete source record and its exact locator."""
    payload = json.dumps(
        {"locator": locator, "source": source},
        sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _apply_packets(packets: list[dict[str, Any]], sources: dict[str, Any], gazetteer: dict[str, Any],
                   boundaries: dict[str, Any], golden: dict[str, Any], assignments: dict[str, Any],
                   coverage: dict[str, Any]) -> None:
    if not packets:
        return
    source_index = {row["source_id"]: row for row in sources["sources"]}
    for packet in packets:
        for row in packet.get("sources") or []:
            incoming = json.loads(json.dumps(row))
            existing = source_index.get(row["source_id"])
            if existing:
                artifacts = {
                    artifact["artifact_id"]: artifact
                    for artifact in (existing.get("derived_artifacts") or []) + (incoming.get("derived_artifacts") or [])
                }
                incoming["derived_artifacts"] = [artifacts[key] for key in sorted(artifacts)]
            source_index[row["source_id"]] = incoming
    source_rows = list(source_index.values())
    polity_index = {row["polity_id"]: row for row in gazetteer["polities"]}
    for packet in packets:
        for row in packet.get("polities") or []:
            incoming = json.loads(json.dumps(row))
            existing = polity_index.get(row["polity_id"])
            if existing:
                for field in ("aliases", "capital_location_ids", "source_ids"):
                    incoming[field] = sorted(
                        set(existing.get(field) or []) | set(incoming.get(field) or [])
                    )
                relationships = {
                    relation["relationship_id"]: relation
                    for relation in (existing.get("relationships") or [])
                    + (incoming.get("relationships") or [])
                }
                incoming["relationships"] = [relationships[key] for key in sorted(relationships)]
            polity_index[row["polity_id"]] = incoming
    polity_rows = list(polity_index.values())
    sources["sources"] = sorted(source_rows, key=lambda row: row["source_id"])
    gazetteer["polities"] = sorted(polity_rows, key=lambda row: row["polity_id"])
    boundaries["features"].extend(f for p in packets for f in p.get("boundary_features") or [])
    golden["assertions"].extend(a for p in packets for a in p.get("assertions") or [])
    overrides = {row["province_id"]: row for p in packets for row in p.get("assignment_overrides") or []}
    assignments["assignments"] = [{**row, **overrides.get(row["province_id"], {})} for row in assignments["assignments"]]
    replacement = {(row["region_id"], row["layer"]): row for p in packets for row in p.get("coverage") or []}
    coverage["coverage"] = [replacement.get((row["region_id"], row["layer"]), row) for row in coverage["coverage"]]
    promoted = {
        region for region in WORLDWIDE_M49_SUBREGIONS
        if all(
            replacement.get((region, layer), {}).get("grade") == "A"
            and not replacement[(region, layer)].get("known_gaps")
            and not replacement[(region, layer)].get("exclusions")
            for layer in LAYERS
        )
    }
    remaining = sorted(WORLDWIDE_M49_SUBREGIONS - promoted)
    coverage["known_gaps"] = ([] if not remaining else [
        f"{len(remaining)} of 22 regions require four-layer Grade-A promotion before certification: "
        + ", ".join(remaining)
    ])


def _apply_approved_polity_source_cleanup(
    sources: dict[str, Any], gazetteer: dict[str, Any], boundaries: dict[str, Any],
    golden: dict[str, Any], assignments: dict[str, Any], coverage: dict[str, Any],
) -> None:
    """Apply the reviewer-approved 2026-08-18 scaffold-reference cleanup."""
    provisional_boundaries = [
        feature for feature in boundaries["features"]
        if feature["properties"].get("source_ids") == [PROVISIONAL_SOURCE_ID]
    ]
    if len(provisional_boundaries) != 262 or any(
        feature["properties"].get("classification") != "soft_evidence"
        or feature["properties"].get("confidence") != "provisional"
        or feature["properties"].get("valid_from") is not None
        or feature["properties"].get("valid_to") is not None
        for feature in provisional_boundaries
    ):
        raise SystemExit("approved cleanup expected exactly 262 undated provisional soft boundaries")
    provisional_boundary_ids = {
        feature["properties"]["feature_id"] for feature in provisional_boundaries
    }
    asserted_provisional_boundaries = {
        boundary_id
        for assertion in golden["assertions"]
        for boundary_id in assertion.get("boundary_feature_ids") or []
        if boundary_id in provisional_boundary_ids
    }
    if asserted_provisional_boundaries:
        raise SystemExit("approved cleanup refuses to prune an asserted provisional boundary")
    boundaries["features"] = [
        feature for feature in boundaries["features"]
        if feature["properties"]["feature_id"] not in provisional_boundary_ids
    ]

    redundant_assertions = {
        assertion["assertion_id"]
        for assertion in golden["assertions"]
        if PROVISIONAL_SOURCE_ID in assertion.get("tolerance_policy", {}).get("source_ids", [])
    }
    if redundant_assertions != APPROVED_REDUNDANT_PILOT_ASSERTIONS:
        raise SystemExit("approved cleanup found unexpected provisional pilot assertions")
    golden["assertions"] = [
        assertion for assertion in golden["assertions"]
        if assertion["assertion_id"] not in APPROVED_REDUNDANT_PILOT_ASSERTIONS
    ]

    observed_core_counts = {
        polity_id: sum(
            polity_id in (assignment.get("core_polity_ids") or [])
            for assignment in assignments["assignments"]
        )
        for polity_id in APPROVED_LEGACY_CORE_COUNTS
    }
    if observed_core_counts != APPROVED_LEGACY_CORE_COUNTS:
        raise SystemExit("approved cleanup found unexpected legacy core-reference counts")
    legacy_core_ids = set(APPROVED_LEGACY_CORE_COUNTS)
    for assignment in assignments["assignments"]:
        cores = assignment.get("core_polity_ids") or []
        if legacy_core_ids.intersection(cores):
            assignment["core_polity_ids"] = sorted({
                assignment["owner_polity_id"] if polity_id in legacy_core_ids else polity_id
                for polity_id in cores
            })

    source_index = {row["source_id"]: row for row in sources["sources"]}
    provisional_polities = {
        row["polity_id"]: row for row in gazetteer["polities"]
        if PROVISIONAL_SOURCE_ID in row.get("source_ids", [])
    }
    reviewed_polities = {
        polity_id for polity_id, row in provisional_polities.items()
        if set(row["source_ids"]) - {PROVISIONAL_SOURCE_ID}
    }
    pruned_polities = set(provisional_polities) - reviewed_polities
    if (len(provisional_polities) != 198
            or reviewed_polities != APPROVED_REVIEWED_SCAFFOLD_POLITIES
            or pruned_polities != APPROVED_PRUNED_SCAFFOLD_POLITIES):
        raise SystemExit("approved cleanup found unexpected provisional polity records")
    for polity_id in reviewed_polities:
        replacement_ids = set(provisional_polities[polity_id]["source_ids"]) - {PROVISIONAL_SOURCE_ID}
        if any(source_index.get(source_id, {}).get("review_status") != "reviewed"
               for source_id in replacement_ids):
            raise SystemExit(f"approved cleanup found an unreviewed replacement source for {polity_id}")
        provisional_polities[polity_id]["source_ids"] = sorted(replacement_ids)

    retained_polity_ids = {
        row["polity_id"] for row in gazetteer["polities"]
        if row["polity_id"] not in provisional_polities or row["polity_id"] in reviewed_polities
    }
    referenced_polity_ids = set()
    for assignment in assignments["assignments"]:
        for key in ("polity_ids", "core_polity_ids", "claim_polity_ids", "dispute_polity_ids"):
            referenced_polity_ids.update(assignment.get(key) or [])
        for key in ("sovereign_polity_id", "owner_polity_id", "controller_polity_id"):
            referenced_polity_ids.add(assignment[key])
    for feature in boundaries["features"]:
        referenced_polity_ids.update(feature["properties"].get("side_polity_ids", {}).values())
    for polity in gazetteer["polities"]:
        referenced_polity_ids.update(
            relation["target_polity_id"] for relation in polity.get("relationships") or []
        )
    pruned_but_referenced = pruned_polities & referenced_polity_ids
    if pruned_but_referenced:
        raise SystemExit("approved cleanup would prune referenced polities: "
                         + ", ".join(sorted(pruned_but_referenced)))
    gazetteer["polities"] = [
        row for row in gazetteer["polities"] if row["polity_id"] in retained_polity_ids
    ]
    sources["sources"] = [
        row for row in sources["sources"] if row["source_id"] != PROVISIONAL_SOURCE_ID
    ]

    for artifact_name, document in (
        ("source manifest", sources), ("gazetteer", gazetteer),
        ("boundary registry", boundaries), ("golden assertions", golden),
        ("assignments", assignments), ("coverage", coverage),
    ):
        if PROVISIONAL_SOURCE_ID in json.dumps(document, sort_keys=True):
            raise SystemExit(f"approved cleanup left a provisional source reference in {artifact_name}")


def _provisional_source(path: Path) -> dict[str, Any]:
    return {"source_id": "official-1444-modern-scaffold-provisional",
            "citation": "Internal official-1444 curated-politics overlay on the modern Natural Earth scaffold.",
            "url": None, "access_date": "2026-08-14", "version": VERSION,
            "checksum": _sha256(path), "license": "internal scaffold; non-public provisional use only",
            "transformations": ["maximum-area spatial overlap onto accepted M23 r2 locations"],
            "review_status": "planned", "source_type": "institutional", "valid_from": None, "valid_to": None,
            "independence_group": "internal-official-1444-scenario", "derived_artifacts": []}


def _province_adjacency(path: Path, mapping_by_location: dict[str, str]) -> list[tuple[str, str]]:
    edges = set()
    with path.open(newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            left = mapping_by_location.get(row["from_location_id"])
            right = mapping_by_location.get(row["to_location_id"])
            if left and right and left != right:
                edges.add(tuple(sorted((left, right))))
    return sorted(edges)


def _merge_records(key: str, *groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for group in groups:
        for row in group:
            merged.setdefault(row[key], json.loads(json.dumps(row)))
    return list(merged.values())


def _merge_polities(*groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for group in groups:
        for source in group:
            polity_id = source["polity_id"]
            if polity_id not in merged:
                merged[polity_id] = json.loads(json.dumps(source))
                continue
            target = merged[polity_id]
            for field in ("aliases", "capital_location_ids", "source_ids"):
                target[field] = sorted(set(target.get(field) or []) | set(source.get(field) or []))
            relations = {row["relationship_id"]: row for row in target.get("relationships") or []}
            for relation in source.get("relationships") or []:
                relations.setdefault(relation["relationship_id"], json.loads(json.dumps(relation)))
            target["relationships"] = [relations[key] for key in sorted(relations)]
    return list(merged.values())


def _copy_derived_artifacts(source_root: Path, output: Path, sources: list[dict[str, Any]]) -> None:
    for source in sources:
        for artifact in source.get("derived_artifacts") or []:
            relative = Path(artifact["path"])
            if relative.is_absolute() or ".." in relative.parts:
                raise SystemExit(f"derived artifact escapes evidence root: {relative}")
            source_path = source_root / relative
            target = output / relative
            if not source_path.is_file():
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_path, target)


def _copy_packet_derived_files(packets: list[dict[str, Any]], output: Path) -> None:
    """Copy only qualified, checksum-pinned packet assets into the assembled pass."""
    output_root = output.resolve()
    for packet in packets:
        packet_path = Path(packet["_packet_path"])
        for derived in packet.get("derived_files") or []:
            source = (packet_path.parent / derived["path"]).resolve()
            target = (output / derived["target_path"]).resolve()
            try:
                target.relative_to(output_root)
            except ValueError as exc:
                raise SystemExit(f"packet derived target escapes assembled pass: {derived['target_path']}") from exc
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)


def _header(document_type: str) -> dict[str, Any]:
    return {"schema_version": "0.3.0", "document_type": document_type, "artifact_version": VERSION,
            "pass_id": PASS_ID, "start_date": START_DATE}


def _sidecar_records(root: Path, records: dict[str, str]) -> dict[str, dict[str, str]]:
    return {role: {"path": path, "sha256": _sha256(root / path)} for role, path in records.items()}


def _majority(values: Any) -> str:
    counts: dict[str, int] = defaultdict(int)
    for value in values:
        counts[value] += 1
    return sorted(counts, key=lambda value: (-counts[value], value))[0]


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-") or "unknown"


def _tag_polity(tag: str) -> str:
    return f"scenario-{_slug(tag)}"


def _artifact_version(path: Path) -> str:
    return VERSION if path.suffix == ".md" else str(_load(path).get("artifact_version") or VERSION)


def _dossier(packets: list[dict[str, Any]]) -> str:
    return f"""# M25C provisional worldwide evidence pass

## Scope
All 22 non-Antarctic M49 subregions, 23,582 playable locations, and exactly 22,000 provisional provinces.

## Research questions
Which provisional records must be replaced by exact-date evidence before certification?

## Citations
Accepted anomaly-census and 1444-v2 pilot citations are retained in source_manifest.json. The worldwide politics seed is explicitly planned internal scaffold evidence.

## Transformations and conflicts
Modern scenario ownership is transferred by deterministic maximum-area overlap. {len(packets)} dated regional packet(s) were merged in stable order.

## Exclusions
Antarctica is excluded. This pass cannot be review-accepted, certified, published, or promoted to the demo.

## Uncertainty
Every unpromoted region declares layer gaps. Soft provisional ownership lines are never historical hard constraints.
"""


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_csv(path: Path, header: tuple[str, ...], rows: Any) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(header); writer.writerows(rows)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
