#!/usr/bin/env python3
"""Build the independently reviewed M25C worldwide 1444 research pass.

The builder is deterministic and input-driven.  It enriches the accepted M23
fabric, assembles reviewed curator inputs, renders the review bundle, and stops
at the independent-review boundary.  It never invents evidence or signs its
own output, and it intentionally contains no runtime/certification stage.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

from shapely import make_valid
from shapely.geometry import mapping, shape
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gpm.geo.shapefile import read_zipped_shapefile  # noqa: E402
from gpm.qa.render import StartDateRenderError, render_start_date_pass  # noqa: E402
from gpm.qa.start_date import (  # noqa: E402
    HISTORICAL_ANOMALY_TYPES,
    StartDateQAError,
    validate_anomaly_inventory,
    run_start_date_qa,
)
from gpm.schemas import (  # noqa: E402
    SchemaValidationError,
    WORLDWIDE_M49_SUBREGIONS,
    validate_historical_boundary_registry,
    validate_historical_territory_status,
    validate_location_assignments,
    validate_location_fabric_manifest,
    validate_location_lineage,
    validate_polity_gazetteer,
    validate_spatial_golden_borders,
    validate_start_date_changelog,
    validate_start_date_coverage,
    validate_start_date_source_manifest,
)

PASS_ID = "official-1444-global-v1"
START_DATE = "1444-11-11"
ARTIFACT_VERSION = "1.0.0"
GENERATED_AT = "2026-07-19T00:00:00Z"
DEFAULT_OUTPUT = ROOT / "research" / "start-dates" / "1444-global-v1"
PILOT = ROOT / "research" / "start-dates" / "1444-v2"
DEFAULT_NATURAL_EARTH = ROOT / "data" / "raw" / "natural_earth" / "ne_10m_admin_0_countries.zip"
ANOMALY_TYPES = HISTORICAL_ANOMALY_TYPES
M49_BY_NATURAL_EARTH_SUBREGION = {
    "Antarctica": "Antarctica",
    "Western Africa": "011", "Eastern Africa": "014", "Northern Africa": "015",
    "Middle Africa": "017", "Southern Africa": "018", "South America": "005",
    "Central America": "013", "Northern America": "021", "Caribbean": "029",
    "Eastern Asia": "030", "Southern Asia": "034", "South-Eastern Asia": "035",
    "Central Asia": "143", "Western Asia": "145", "Southern Europe": "039",
    "Eastern Europe": "151", "Northern Europe": "154", "Western Europe": "155",
    "Australia and New Zealand": "053", "Melanesia": "054", "Micronesia": "057",
    "Polynesia": "061",
}
ARTIFACT_FILES = {
    "dossier": "dossier.md",
    "source_manifest": "source_manifest.json",
    "boundary_registry": "boundaries.geojson",
    "polity_gazetteer": "gazetteer.json",
    "location_assignments": "assignments.json",
    "golden_borders": "golden.json",
    "full_build_geometry": "build.geojson",
    "coverage_matrix": "coverage.json",
    "changelog": "changelog.json",
    "canonical_historical_status": "historical-territory-status.json",
    "world_coverage_mask": "world_coverage_mask.geojson",
    "anomaly_inventory": "anomaly_inventory.json",
}
CURATED_FILES = tuple(name for role, name in ARTIFACT_FILES.items() if role not in {"world_coverage_mask"})
REJECTION_REPORT = "m25c_rejection_report.json"
REQUIRED_FABRIC_SIDECARS = {
    "fabric_manifest": "location_fabric_manifest.json",
    "lineage": "location_lineage.json",
    "province_membership": "province_membership.csv",
    "adjacency": "location_adjacency.csv",
}
EVIDENCE_VALIDATORS = {
    "source_manifest.json": validate_start_date_source_manifest,
    "boundaries.geojson": validate_historical_boundary_registry,
    "gazetteer.json": validate_polity_gazetteer,
    "assignments.json": validate_location_assignments,
    "golden.json": validate_spatial_golden_borders,
    "coverage.json": validate_start_date_coverage,
    "changelog.json": validate_start_date_changelog,
    "historical-territory-status.json": validate_historical_territory_status,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=(
        "inventory", "fabric", "evidence", "splits", "aggregation", "assembly",
        "render", "preflight", "accept-review", "research-pipeline",
    ))
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--inventory-input", type=Path)
    parser.add_argument("--fabric-input", type=Path)
    parser.add_argument("--fabric-sidecars-dir", type=Path)
    parser.add_argument("--natural-earth-input", type=Path, default=DEFAULT_NATURAL_EARTH)
    parser.add_argument("--evidence-dir", type=Path)
    parser.add_argument("--split-fabric-dir", type=Path)
    parser.add_argument("--paintability-input", type=Path)
    parser.add_argument("--split-requests-input", type=Path)
    parser.add_argument("--reviewer")
    parser.add_argument("--review-date")
    args = parser.parse_args()
    if args.stage == "research-pipeline":
        findings = _validate_curator_handoff(args)
        _write_rejection_report(args.output_dir, findings)
        if findings:
            raise SystemExit(
                f"curator handoff rejected with {len(findings)} finding(s); "
                f"see {args.output_dir.resolve() / REJECTION_REPORT}"
            )
    stages = (
        "inventory", "fabric", "evidence", "splits", "aggregation", "assembly",
        "render", "preflight",
    ) if args.stage == "research-pipeline" else (args.stage,)
    for stage in stages:
        globals()[f"stage_{stage.replace('-', '_')}"](args)
    return 0


def stage_inventory(args: argparse.Namespace) -> None:
    """Pin pilot provenance and install a curator-supplied resolved inventory."""
    output = args.output_dir.resolve()
    (output / "provenance").mkdir(parents=True, exist_ok=True)
    pilot_files = {
        path.relative_to(PILOT).as_posix(): _sha256(path)
        for path in sorted(PILOT.rglob("*")) if path.is_file()
    }
    _write(output / "provenance" / "1444-v2-seed.json", {
        "schema_version": "1.0.0", "source_lineage": "1444-v2",
        "reuse_policy": "read-only-hash-pinned-evidence-only",
        "promotion_prohibited": True, "files": pilot_files,
    })
    if args.inventory_input is None:
        raise SystemExit("inventory stage requires --inventory-input with reviewed, resolved worldwide anomalies")
    inventory = _load(args.inventory_input)
    _validate_inventory(inventory)
    _write(output / "anomaly_inventory.json", _canonicalize_inventory(inventory))
    _write_candidate_status(output, "research_inputs_assembled_pending_independent_review")


def stage_fabric(args: argparse.Namespace) -> None:
    """Enrich accepted M23 locations with exact non-Antarctic M49 codes."""
    if args.fabric_input is None:
        raise SystemExit("fabric stage requires --fabric-input from the accepted M23 playable land fabric")
    if args.fabric_sidecars_dir is None:
        raise SystemExit("fabric stage requires --fabric-sidecars-dir with the accepted M23 manifest, lineage, membership, and adjacency")
    _validate_fabric_sidecars(args.fabric_sidecars_dir)
    locations = _load(args.fabric_input)
    features = locations.get("features") or []
    if not features:
        raise SystemExit("fabric input contains no playable locations")
    enriched = enrich_m49(locations, args.natural_earth_input)
    revision = _fabric_revision(enriched)
    mask_features = [
        {"type": "Feature", "geometry": feature["geometry"], "properties": {
            "location_id": feature["properties"]["location_id"],
            "region_id": feature["properties"]["m49_subregion"],
        }}
        for feature in sorted(enriched["features"], key=lambda item: item["properties"]["location_id"])
        if feature["properties"].get("m49_subregion") != "Antarctica"
    ]
    mask = {
        "schema_version": "0.3.0", "document_type": "world_coverage_mask",
        "artifact_version": ARTIFACT_VERSION, "pass_id": PASS_ID, "start_date": START_DATE,
        "fabric_revision": revision, "type": "FeatureCollection", "features": mask_features,
    }
    regions = {feature["properties"]["region_id"] for feature in mask_features}
    if regions != WORLDWIDE_M49_SUBREGIONS:
        raise SystemExit(f"enriched fabric does not span the exact 22-part M49 partition: {sorted(regions)}")
    output = args.output_dir.resolve()
    sidecars = output / "sidecars"
    sidecars.mkdir(parents=True, exist_ok=True)
    _copy_sidecars(args.fabric_sidecars_dir, sidecars)
    _write(sidecars / "locations.geojson", enriched)
    _write(output / "world_coverage_mask.geojson", mask)


def enrich_m49(document: dict[str, Any], natural_earth_input: Path) -> dict[str, Any]:
    """Return a byte-stable fabric copy enriched by maximum country overlap."""
    countries: list[Any] = []
    codes: list[str] = []
    for feature in read_zipped_shapefile(Path(natural_earth_input)):
        raw = feature.properties.get("SUBREGION") or feature.properties.get("subregion") or ""
        name = str(raw).replace("\x00", "").strip()
        code = M49_BY_NATURAL_EARTH_SUBREGION.get(name)
        if not code:
            continue
        geometry = make_valid(shape(feature.geometry))
        if not geometry.is_empty:
            countries.append(geometry)
            codes.append(code)
    if not countries:
        raise SystemExit(f"Natural Earth input has no mapped admin-0 geometry: {natural_earth_input}")
    tree = STRtree(countries)
    enriched = json.loads(json.dumps(document))
    missing: list[str] = []
    for feature in enriched.get("features") or []:
        props = feature.get("properties") or {}
        location_id = str(props.get("location_id") or "")
        geometry = make_valid(shape(feature.get("geometry")))
        ranked: list[tuple[float, str]] = []
        for index in tree.query(geometry):
            area = geometry.intersection(countries[int(index)]).area
            if area > 0:
                ranked.append((area, codes[int(index)]))
        if not ranked:
            point = geometry.representative_point()
            _, code, _ = min(
                (point.distance(country), codes[index], index)
                for index, country in enumerate(countries)
            )
            ranked.append((0.0, code))
        if not ranked:
            missing.append(location_id)
            continue
        props["m49_subregion"] = sorted(ranked, key=lambda row: (-row[0], row[1]))[0][1]
        feature["properties"] = props
    if missing:
        raise SystemExit("M49 enrichment could not classify playable locations: " + ", ".join(missing[:20]))
    enriched["features"] = sorted(enriched["features"], key=lambda item: item["properties"]["location_id"])
    return enriched


def stage_evidence(args: argparse.Namespace) -> None:
    if args.evidence_dir is None:
        raise SystemExit("evidence stage requires --evidence-dir containing reviewed schema-0.3 artifacts")
    source = args.evidence_dir.resolve()
    output = args.output_dir.resolve()
    findings = _validate_evidence_bundle(source)
    if findings:
        _write_rejection_report(output, findings)
        raise SystemExit(
            f"reviewed evidence bundle rejected with {len(findings)} finding(s); "
            f"see {output / REJECTION_REPORT}"
        )
    for name in CURATED_FILES:
        if name == "anomaly_inventory.json":
            continue
        path = source / name
        if not path.is_file():
            raise SystemExit(f"reviewed evidence bundle is incomplete: missing {path}")
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    generated = {
        "pass_manifest.json", "candidate_status.json", "world_coverage_mask.geojson",
        "start_date_qa.json", "start_date_preflight.json",
    }
    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source)
        if path.is_symlink() or not path.is_file() or relative.parts[0] in {"review", "provenance"} or relative.as_posix() in generated:
            continue
        target = output / relative
        if target.name == "locations.geojson" and target.parent.name == "sidecars":
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    inventory_source = source / "anomaly_inventory.json"
    if inventory_source.is_file():
        inventory = _load(inventory_source)
        _validate_inventory(inventory)
        _write(output / "anomaly_inventory.json", _canonicalize_inventory(inventory))
    _require_resolved_inventory(output)


def stage_splits(args: argparse.Namespace) -> None:
    """Install only an explicitly reviewed r3 fabric; otherwise preserve r2."""
    if args.split_fabric_dir is None:
        locations = _load(args.output_dir / "sidecars" / "locations.geojson")
        if _fabric_revision(locations).endswith("-r3"):
            raise SystemExit("revision 3 requires --split-fabric-dir with reviewed parent/child lineage")
        return
    if args.paintability_input is None or args.split_requests_input is None:
        raise SystemExit("revision 3 requires --paintability-input and --split-requests-input")
    paintability = _load(args.paintability_input)
    requests = _load(args.split_requests_input).get("requests") or []
    if paintability.get("crossing_count", 0) < 1 or paintability.get("status") != "fail" or not requests:
        raise SystemExit("revision 3 requires documented paintability failures and reviewed split requests")
    request_ids = {str(row.get("request_id")) for row in requests}
    source = args.split_fabric_dir.resolve()
    lineage = _load(source / "location_lineage.json")
    events = lineage.get("events") or []
    accepted = [row for row in events if row.get("operation") in {"split_by_boundary", "refine_h3"}]
    if not accepted or any(not row.get("parent_location_ids") or not row.get("child_location_ids") for row in accepted):
        raise SystemExit("revision-3 split fabric lacks parent/child lineage")
    if any(str(row.get("request_id")) not in request_ids for row in accepted):
        raise SystemExit("revision-3 lineage contains a split without a reviewed request")
    locations = _load(source / "locations.geojson")
    if _fabric_revision(locations) != "global-h3-v1-r3":
        raise SystemExit("reviewed split fabric must identify global-h3-v1-r3")
    _copy_sidecars(source, args.output_dir / "sidecars")
    stage_fabric(argparse.Namespace(**{**vars(args), "fabric_input": source / "locations.geojson", "fabric_sidecars_dir": source}))


def stage_aggregation(args: argparse.Namespace) -> None:
    _require_resolved_inventory(args.output_dir)
    assignments = _load(args.output_dir / "assignments.json")
    if assignments.get("expected_province_count") != 22_000:
        raise SystemExit("worldwide aggregation must target exactly 22,000 provinces")
    rows = assignments.get("assignments") or []
    province_ids = {row.get("province_id") for row in rows}
    if len(province_ids) != 22_000:
        raise SystemExit(f"worldwide aggregation produced {len(province_ids)} provinces, expected 22000")
    assigned = [location for row in rows for location in row.get("location_ids") or []]
    if len(assigned) != len(set(assigned)):
        raise SystemExit("worldwide assignments are not exact-once")
    mask = _load(args.output_dir / "world_coverage_mask.geojson")
    mask_ids = {feature["properties"]["location_id"] for feature in mask["features"]}
    if set(assigned) != mask_ids:
        raise SystemExit("worldwide assignments do not cover every and only world-mask location")
    aggregation_record = assignments.get("release_sidecars", {}).get("aggregation_manifest", {})
    aggregation = _load(args.output_dir / aggregation_record.get("path", "sidecars/aggregation_manifest.json"))
    if aggregation.get("modern_boundary_influence") != "none":
        raise SystemExit("worldwide aggregation must disable modern-boundary influence")
    policy = aggregation.get("historical_constraint_policy") or {}
    hard_policy = policy.get("hard") or policy.get("hard_constraints")
    if hard_policy not in {"block_crossing_edges", "forbid_cross_boundary_merges", "remove_crossing_merge_edges"}:
        raise SystemExit("historical hard constraints must block cross-boundary merges")


def stage_assembly(args: argparse.Namespace) -> None:
    output = args.output_dir.resolve()
    _require_resolved_inventory(output)
    missing = [name for name in ARTIFACT_FILES.values() if not (output / name).is_file()]
    if missing:
        raise SystemExit("assembly is missing reviewed artifacts: " + ", ".join(missing))
    assignments = _load(output / "assignments.json")
    geometry = _load(output / "build.geojson")
    mask_hash = _sha256(output / "world_coverage_mask.geojson")
    artifacts = {
        role: {"path": name, "version": _artifact_version(output / name), "sha256": _sha256(output / name)}
        for role, name in ARTIFACT_FILES.items()
    }
    manifest = {
        "schema_version": "0.3.0", "document_type": "start_date_research_pass",
        "artifact_version": ARTIFACT_VERSION, "pass_id": PASS_ID, "start_date": START_DATE,
        "version": ARTIFACT_VERSION, "era": "late-medieval",
        "fabric_revision": assignments["fabric_revision"],
        "geometry_revision": geometry["geometry_revision"], "generated_at": GENERATED_AT,
        "scope": {
            "kind": "worldwide", "regions": sorted(WORLDWIDE_M49_SUBREGIONS),
            "priority_regions": sorted(WORLDWIDE_M49_SUBREGIONS),
            "layers": ["geometry", "politics", "hierarchy", "gazetteer_relationships"],
            "world_coverage_mask_sha256": mask_hash,
            "partition": {"standard": "UN M49", "revision": "2026-07-19",
                          "antarctica": "excluded-not-in-playable-fabric",
                          "subregions": sorted(WORLDWIDE_M49_SUBREGIONS)},
        },
        "artifacts": artifacts,
        "review": {"manifest_path": "review/review_manifest.json", "sha256": "0" * 64,
                   "generator": "gpm qa render", "reviewer": "pending-independent-review",
                   "status": "pending_independent_review"},
    }
    _write(output / "pass_manifest.json", manifest)
    _write_candidate_status(output, "pending_independent_review")


def stage_render(args: argparse.Namespace) -> None:
    output = args.output_dir.resolve()
    try:
        result = render_start_date_pass(pass_dir=output, output_dir=output / "review")
    except StartDateRenderError as exc:
        raise SystemExit(f"render rejected: {exc}") from exc
    manifest = _load(output / "pass_manifest.json")
    manifest["review"]["sha256"] = _sha256(Path(result.manifest_output))
    manifest["review"]["reviewer"] = "pending-independent-review"
    manifest["review"]["status"] = "pending_independent_review"
    _write(output / "pass_manifest.json", manifest)
    print(json.dumps(result.to_dict(), sort_keys=True))


def stage_preflight(args: argparse.Namespace) -> None:
    try:
        result = run_start_date_qa(
            pass_dir=args.output_dir, report_output=args.output_dir / "start_date_preflight.json",
            pending_review=True,
        )
    except StartDateQAError as exc:
        raise SystemExit(f"preflight rejected: {exc}") from exc
    print(json.dumps(result.to_dict(), sort_keys=True))
    if not result.passed:
        raise SystemExit(f"preflight failed with {result.error_count} non-review error(s)")


def stage_accept_review(args: argparse.Namespace) -> None:
    if not args.reviewer or not args.review_date:
        raise SystemExit("accept-review requires --reviewer and --review-date")
    try:
        date.fromisoformat(args.review_date)
    except ValueError as exc:
        raise SystemExit("--review-date must use YYYY-MM-DD") from exc
    output = args.output_dir.resolve()
    manifest_path = output / "pass_manifest.json"
    review_path = output / "review" / "review_manifest.json"
    manifest, review = _load(manifest_path), _load(review_path)
    reviewer = args.reviewer.strip()
    if not reviewer or reviewer.casefold() in {
        str(review.get("generator", "")).casefold(), "gpm qa render", "generator",
        "pending-independent-review",
    }:
        raise SystemExit("reviewer identity must name an independent human reviewer")
    _verify_review_bundle(output, manifest, review)
    original_manifest, original_review = manifest_path.read_bytes(), review_path.read_bytes()
    review.update({"reviewer": reviewer, "reviewed_at": args.review_date, "status": "accepted"})
    _write(review_path, review)
    manifest["review"].update({"reviewer": reviewer, "status": "accepted", "sha256": _sha256(review_path)})
    _write(manifest_path, manifest)
    result = run_start_date_qa(pass_dir=output)
    if not result.passed:
        manifest_path.write_bytes(original_manifest)
        review_path.write_bytes(original_review)
        raise SystemExit(f"acceptance rolled back: ordinary research QA has {result.error_count} error(s)")
    _write_candidate_status(output, "accepted_research_pass", reviewer=reviewer, review_date=args.review_date)


def _verify_review_bundle(output: Path, manifest: dict[str, Any], review: dict[str, Any]) -> None:
    if review.get("generator") != manifest["review"]["generator"] or review.get("status") != "pending_independent_review":
        raise SystemExit("review manifest is not the pending output of the pinned generator")
    expected_regions = set(manifest["scope"]["regions"])
    inventory = _load(output / manifest["artifacts"]["anomaly_inventory"]["path"])
    expected_anomalies = {f"anomaly:{row['type']}" for row in inventory["anomalies"]}
    actual_regions, actual_anomalies = set(), set()
    for render in review.get("renders") or []:
        identity = str(render.get("region_id") or "")
        if render.get("sheet_type", "region") == "anomaly":
            actual_anomalies.add(identity)
        else:
            actual_regions.add(identity)
        path = output / "review" / str(render.get("path") or "")
        if not path.is_file() or _sha256(path) != render.get("sha256"):
            raise SystemExit(f"review render is missing or changed: {identity}")
    if actual_regions != expected_regions or actual_anomalies != expected_anomalies:
        raise SystemExit("review bundle does not exactly cover all 22 regions and anomaly classes")


def _validate_inventory(inventory: dict[str, Any]) -> None:
    if inventory.get("schema_version") != "0.3.0" or inventory.get("pass_id") != PASS_ID or inventory.get("start_date") != START_DATE:
        raise SystemExit("anomaly inventory has the wrong schema/pass/date identity")
    try:
        validate_anomaly_inventory(inventory)
    except SchemaValidationError as exc:
        raise SystemExit(str(exc)) from exc


def _require_resolved_inventory(output: Path) -> None:
    path = Path(output) / "anomaly_inventory.json"
    if not path.is_file():
        raise SystemExit("resolved worldwide anomaly inventory is missing")
    _validate_inventory(_load(path))


def _canonicalize_inventory(inventory: dict[str, Any]) -> dict[str, Any]:
    """Return the canonical byte-stable ordering for a validated inventory."""
    result = json.loads(json.dumps(inventory))
    for row in result["anomalies"]:
        for field in ("region_ids", "subject_ids", "source_ids"):
            row[field] = sorted(row[field])
    result["anomalies"].sort(key=lambda row: row["anomaly_id"])
    census = result["census"]
    census["region_ids"] = sorted(census["region_ids"])
    census["types"] = sorted(census["types"])
    for cell in census["cells"]:
        cell["anomaly_ids"] = sorted(cell["anomaly_ids"])
        cell["source_ids"] = sorted(cell["source_ids"])
    census["cells"].sort(key=lambda cell: (cell["region_id"], cell["type"]))
    return result


def _copy_sidecars(source: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for path in sorted(Path(source).iterdir()):
        if path.is_file() and not path.is_symlink():
            shutil.copyfile(path, target / path.name)


def _validate_curator_handoff(args: argparse.Namespace) -> list[dict[str, Any]]:
    """Report every independently detectable handoff defect before assembly."""
    findings: list[dict[str, Any]] = []
    inventory: dict[str, Any] | None = None
    if args.inventory_input is None:
        _reject(findings, "anomaly_inventory", "MISSING_INPUT", [], "historical-curator", "--inventory-input is required")
    else:
        try:
            inventory = _load(args.inventory_input)
            _validate_inventory(inventory)
        except SystemExit as exc:
            affected = _inventory_affected_ids(inventory or {})
            _reject(findings, "anomaly_inventory", _inventory_rejection_rule(str(exc)), affected, "historical-curator", str(exc))
    if args.fabric_input is None:
        _reject(findings, "fabric", "MISSING_INPUT", [], "fabric-curator", "--fabric-input is required")
    elif not args.fabric_input.is_file():
        _reject(findings, "fabric", "MISSING_INPUT", [str(args.fabric_input)], "fabric-curator", "fabric input does not exist")
    if args.fabric_sidecars_dir is None:
        _reject(findings, "fabric_sidecars", "MISSING_INPUT", [], "fabric-curator", "--fabric-sidecars-dir is required")
    else:
        findings.extend(_fabric_sidecar_findings(args.fabric_sidecars_dir))
    if not args.natural_earth_input.is_file():
        _reject(findings, "natural_earth", "MISSING_INPUT", [str(args.natural_earth_input)], "pipeline-operator", "Natural Earth admin-0 input does not exist")
    if args.evidence_dir is None:
        _reject(findings, "evidence_bundle", "MISSING_INPUT", [], "historical-curator", "--evidence-dir is required")
    else:
        findings.extend(_validate_evidence_bundle(args.evidence_dir.resolve(), inventory=inventory))
    return sorted(findings, key=lambda row: (row["artifact"], row["rule"], row["affected_ids"]))


def _validate_evidence_bundle(source: Path, *, inventory: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    documents: dict[str, dict[str, Any]] = {}
    if not source.is_dir():
        _reject(findings, "evidence_bundle", "MISSING_INPUT", [str(source)], "historical-curator", "evidence directory does not exist")
        return findings
    for name in CURATED_FILES:
        if name == "anomaly_inventory.json":
            continue
        path = source / name
        if path.is_symlink():
            _reject(findings, name, "SYMLINK_INPUT", [name], "historical-curator", "curated artifacts may not be symlinks")
            continue
        if not path.is_file():
            _reject(findings, name, "MISSING_ARTIFACT", [name], "historical-curator", "required reviewed artifact is missing")
            continue
        if name == "dossier.md":
            continue
        try:
            document = _load(path)
        except SystemExit as exc:
            _reject(findings, name, "MALFORMED_JSON", [name], "historical-curator", str(exc))
            continue
        documents[name] = document
        validator = EVIDENCE_VALIDATORS.get(name)
        if validator:
            try:
                validator(document)
            except SchemaValidationError as exc:
                _reject(findings, name, "SCHEMA_REJECTION", [name], "historical-curator", str(exc))
        if (document.get("pass_id"), document.get("start_date")) != (PASS_ID, START_DATE):
            _reject(findings, name, "PASS_IDENTITY_MISMATCH", [name], "historical-curator", f"expected {PASS_ID}/{START_DATE}")
        if document.get("schema_version") != "0.3.0":
            _reject(findings, name, "SCHEMA_VERSION_MISMATCH", [name], "historical-curator", "expected schema 0.3.0")
    _validate_evidence_contract(documents, findings)
    inventory_path = source / "anomaly_inventory.json"
    bundle_inventory: dict[str, Any] | None = None
    if inventory_path.is_file() and not inventory_path.is_symlink():
        try:
            bundle_inventory = _load(inventory_path)
            _validate_inventory(bundle_inventory)
        except SystemExit as exc:
            _reject(findings, "anomaly_inventory.json", "INVALID_INVENTORY", [], "historical-curator", str(exc))
            bundle_inventory = None
    effective_inventory = inventory if inventory is not None else bundle_inventory
    if effective_inventory is not None:
        _validate_anomaly_handoff(effective_inventory, documents, findings)
    if inventory is not None and bundle_inventory is not None:
        if _canonicalize_inventory(inventory) != _canonicalize_inventory(bundle_inventory):
            _reject(
                findings, "anomaly_inventory.json", "INVALID_CENSUS_LINK", [],
                "historical-curator",
                "--inventory-input and evidence/anomaly_inventory.json must be the same canonical census",
            )
    assignments_path = source / "assignments.json"
    if assignments_path.is_file() and not assignments_path.is_symlink():
        try:
            assignments = _load(assignments_path)
        except SystemExit:
            assignments = {}
        for group in ("fabric_sidecars", "release_sidecars"):
            records = assignments.get(group)
            if not isinstance(records, dict):
                continue
            for role, record in records.items():
                if not isinstance(record, dict):
                    continue
                relative = Path(str(record.get("path") or ""))
                artifact = f"{group}:{role}"
                if relative.is_absolute() or ".." in relative.parts:
                    _reject(findings, artifact, "PATH_ESCAPE", [str(relative)], "historical-curator", "sidecar path escapes the evidence bundle")
                    continue
                path = source / relative
                if path.is_symlink() or not path.is_file():
                    _reject(findings, artifact, "MISSING_OR_SYMLINK_SIDECAR", [str(relative)], "historical-curator", "hash-pinned sidecar is missing or symlinked")
                elif _sha256(path) != str(record.get("sha256") or "").lower():
                    _reject(findings, artifact, "CHECKSUM_MISMATCH", [str(relative)], "historical-curator", "sidecar does not match its assignment hash")
    for path in source.rglob("*"):
        if path.is_symlink():
            _reject(findings, path.relative_to(source).as_posix(), "SYMLINK_INPUT", [], "historical-curator", "bundle entries may not be symlinks")
    return findings


def _validate_evidence_contract(documents: dict[str, dict[str, Any]], findings: list[dict[str, Any]]) -> None:
    """Check worldwide invariants that do not depend on staged/generated files."""
    sources = documents.get("source_manifest.json", {}).get("sources") or []
    reviewed = {row.get("source_id") for row in sources if row.get("review_status") == "reviewed"}
    all_sources = {row.get("source_id") for row in sources}
    assignments = documents.get("assignments.json", {})
    rows = assignments.get("assignments") or []
    provinces = {row.get("province_id") for row in rows}
    locations = [location for row in rows for location in row.get("location_ids") or []]
    regions = {row.get("region_id") for row in rows}
    if assignments and (assignments.get("expected_province_count") != 22_000 or len(provinces) != 22_000):
        _reject(findings, "assignments.json", "INVALID_GLOBAL_PROVINCE_COUNT", [], "aggregation-curator", f"found {len(provinces)} unique provinces; expected 22000")
    if len(locations) != len(set(locations)):
        duplicates = sorted(value for value, count in Counter(locations).items() if count > 1)
        _reject(findings, "assignments.json", "DUPLICATE_LOCATION_ASSIGNMENT", duplicates[:100], "aggregation-curator", "locations must be assigned exactly once")
    if rows and regions != WORLDWIDE_M49_SUBREGIONS:
        _reject(findings, "assignments.json", "INVALID_WORLD_PARTITION", sorted(str(value) for value in regions ^ WORLDWIDE_M49_SUBREGIONS), "aggregation-curator", "assignments must span the exact 22-part M49 partition")
    for row in rows:
        unknown = sorted(set(row.get("source_ids") or []) - all_sources)
        unreviewed = sorted(set(row.get("source_ids") or []) - reviewed)
        if unknown:
            _reject(findings, "assignments.json", "UNKNOWN_SOURCE_REFERENCE", [str(row.get("assignment_id")), *unknown], "historical-curator", "assignment references unknown sources")
        elif unreviewed:
            _reject(findings, "assignments.json", "UNREVIEWED_SOURCE_REFERENCE", [str(row.get("assignment_id")), *unreviewed], "historical-curator", "worldwide assignments require reviewed sources")
    coverage = documents.get("coverage.json", {})
    coverage_rows = coverage.get("coverage") or []
    indexed = {(row.get("region_id"), row.get("layer")): row for row in coverage_rows}
    if coverage:
        for region in sorted(WORLDWIDE_M49_SUBREGIONS):
            for layer in ("geometry", "politics", "hierarchy", "gazetteer_relationships"):
                row = indexed.get((region, layer))
                if row is None or row.get("grade") != "A" or row.get("known_gaps") or row.get("exclusions"):
                    _reject(findings, "coverage.json", "GLOBAL_COVERAGE_NOT_A", [region, layer], "historical-curator", "worldwide coverage must be gap-free grade A")
    if coverage and (coverage.get("known_gaps") or coverage.get("exclusions")):
        _reject(findings, "coverage.json", "GLOBAL_COVERAGE_GAPS", [], "historical-curator", "worldwide coverage may not declare gaps or exclusions")


def _validate_anomaly_handoff(
    inventory: dict[str, Any], documents: dict[str, dict[str, Any]], findings: list[dict[str, Any]],
) -> None:
    """Cross-check every anomaly and census survey link against reviewed evidence."""
    sources = documents.get("source_manifest.json", {}).get("sources") or []
    source_ids = {row.get("source_id") for row in sources if isinstance(row, dict)}
    reviewed_ids = {
        row.get("source_id") for row in sources
        if isinstance(row, dict) and row.get("review_status") == "reviewed"
    }
    source_index = {
        row.get("source_id"): row for row in sources
        if isinstance(row, dict) and isinstance(row.get("source_id"), str)
    }
    polities = documents.get("gazetteer.json", {}).get("polities") or []
    polity_ids = {row.get("polity_id") for row in polities if isinstance(row, dict)}
    polity_index = {
        row.get("polity_id"): row for row in polities
        if isinstance(row, dict) and isinstance(row.get("polity_id"), str)
    }
    referenced_polities: set[str] = set()

    for row in inventory.get("anomalies") or []:
        if not isinstance(row, dict):
            continue
        anomaly_id = str(row.get("anomaly_id") or "<missing-anomaly-id>")
        _reject_unknown_anomaly_refs(
            findings, anomaly_id, row.get("source_ids"), source_ids, reviewed_ids,
        )
        evidence = [source_index[source_id] for source_id in row.get("source_ids") or [] if source_id in source_index]
        has_anchor = any(source.get("source_type") in {"academic", "primary"} for source in evidence)
        independence_groups = {
            source.get("independence_group") for source in evidence
            if isinstance(source.get("independence_group"), str) and source.get("independence_group")
        }
        if not has_anchor or len(independence_groups) < 2:
            _reject(
                findings, "anomaly_inventory", "UNREVIEWED_ANOMALY_SOURCE", [anomaly_id],
                "historical-curator",
                "resolved anomaly requires an academic/primary anchor and two independent provenance groups",
            )
        unknown_subjects = sorted(set(row.get("subject_ids") or []) - polity_ids)
        referenced_polities.update(set(row.get("subject_ids") or []) & polity_ids)
        if unknown_subjects:
            _reject(
                findings, "anomaly_inventory", "UNKNOWN_ANOMALY_SUBJECT",
                [anomaly_id, *unknown_subjects], "historical-curator",
                "anomaly references polity IDs absent from gazetteer.json",
            )

    for polity_id in sorted(referenced_polities):
        polity = polity_index[polity_id]
        polity_sources = polity.get("source_ids")
        if not polity_sources:
            _reject(
                findings, "gazetteer.json", "UNREVIEWED_ANOMALY_SOURCE", [polity_id],
                "historical-curator", "an anomaly subject polity must cite reviewed sources",
            )
        else:
            _reject_unknown_anomaly_refs(
                findings, polity_id, polity_sources, source_ids, reviewed_ids,
            )

    census = inventory.get("census")
    if not isinstance(census, dict):
        return
    for cell in census.get("cells") or []:
        if not isinstance(cell, dict):
            continue
        identity = f"{cell.get('region_id')}/{cell.get('type')}"
        _reject_unknown_anomaly_refs(
            findings, identity, cell.get("source_ids"), source_ids, reviewed_ids,
        )


def _reject_unknown_anomaly_refs(
    findings: list[dict[str, Any]], identity: str, values: Any,
    source_ids: set[Any], reviewed_ids: set[Any],
) -> None:
    refs = set(values) if isinstance(values, list) else set()
    unknown = sorted(refs - source_ids)
    if unknown:
        _reject(
            findings, "anomaly_inventory", "UNKNOWN_ANOMALY_SOURCE",
            [identity, *unknown], "historical-curator",
            "anomaly or census cell references source IDs absent from source_manifest.json",
        )
    unreviewed = sorted((refs & source_ids) - reviewed_ids)
    if unreviewed:
        _reject(
            findings, "anomaly_inventory", "UNREVIEWED_ANOMALY_SOURCE",
            [identity, *unreviewed], "historical-curator",
            "anomaly and census survey sources must have review_status reviewed",
        )


def _inventory_rejection_rule(message: str) -> str:
    normalized = message.casefold()
    if "review requires" in normalized or "review_date" in normalized:
        return "INVALID_CENSUS_REVIEW"
    if "orphan anomaly" in normalized:
        return "ORPHAN_ANOMALY"
    if "link" in normalized:
        return "INVALID_CENSUS_LINK"
    if "census" in normalized:
        return "INCOMPLETE_ANOMALY_CENSUS"
    return "INVALID_INVENTORY"


def _inventory_affected_ids(inventory: dict[str, Any]) -> list[str]:
    affected: set[str] = set()
    for row in inventory.get("anomalies") or []:
        if not isinstance(row, dict):
            continue
        anomaly_id = str(row.get("anomaly_id") or "<missing-anomaly-id>")
        if (
            row.get("resolution") != "resolved" or not row.get("region_ids")
            or not row.get("source_ids") or not row.get("subject_ids")
            or _is_placeholder_id(anomaly_id)
            or any(
                _is_placeholder_id(value)
                for field in ("source_ids", "subject_ids")
                for value in row.get(field) or []
            )
        ):
            affected.add(anomaly_id)
    return sorted(affected)


def _validate_fabric_sidecars(source: Path) -> None:
    findings = _fabric_sidecar_findings(source)
    if findings:
        details = "; ".join(f"{row['rule']}:{row['artifact']}" for row in findings)
        raise SystemExit(f"accepted M23 fabric sidecars are invalid: {details}")


def _fabric_sidecar_findings(source: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    source = Path(source)
    if not source.is_dir():
        _reject(findings, "fabric_sidecars", "MISSING_INPUT", [str(source)], "fabric-curator", "sidecar directory does not exist")
        return findings
    for role, name in REQUIRED_FABRIC_SIDECARS.items():
        path = source / name
        if path.is_symlink():
            _reject(findings, role, "SYMLINK_INPUT", [name], "fabric-curator", "sidecars may not be symlinks")
        elif not path.is_file():
            _reject(findings, role, "MISSING_SIDECAR", [name], "fabric-curator", "required M23 sidecar is missing")
    for role, name, validator in (
        ("fabric_manifest", "location_fabric_manifest.json", validate_location_fabric_manifest),
        ("lineage", "location_lineage.json", validate_location_lineage),
    ):
        path = source / name
        if path.is_file() and not path.is_symlink():
            try:
                validator(_load(path))
            except (SchemaValidationError, SystemExit) as exc:
                _reject(findings, role, "SCHEMA_REJECTION", [name], "fabric-curator", str(exc))
    for role, name, required in (
        ("province_membership", "province_membership.csv", {"province_id", "location_id", "piece_id"}),
        ("adjacency", "location_adjacency.csv", {"from_location_id", "to_location_id"}),
    ):
        path = source / name
        if path.is_file() and not path.is_symlink():
            try:
                with path.open(encoding="utf-8", newline="") as handle:
                    header = set(next(csv.reader(handle), []))
                if not required.issubset(header):
                    raise ValueError(f"expected columns {sorted(required)}")
            except (OSError, UnicodeError, csv.Error, ValueError) as exc:
                _reject(findings, role, "INVALID_CSV", [name], "fabric-curator", str(exc))
    return findings


def _write_rejection_report(output: Path, findings: list[dict[str, Any]]) -> None:
    _write(Path(output).resolve() / REJECTION_REPORT, {
        "schema_version": "1.0.0", "report_type": "m25c_curator_handoff_rejection",
        "pass_id": PASS_ID, "start_date": START_DATE,
        "status": "reject" if findings else "pass", "finding_count": len(findings),
        "findings": findings,
    })


def _reject(findings: list[dict[str, Any]], artifact: str, rule: str, affected_ids: list[str], owner: str, message: str) -> None:
    findings.append({
        "artifact": artifact, "rule": rule, "affected_ids": sorted(str(value) for value in affected_ids),
        "remediation_owner": owner, "message": message,
    })


def _is_placeholder_id(value: Any) -> bool:
    normalized = str(value).strip().casefold()
    return normalized in {"pending", "placeholder", "todo", "tbd", "unknown"} or normalized.startswith("pending-")


def _fabric_revision(document: dict[str, Any]) -> str:
    meta = document.get("gpm") or {}
    fabric_id = str(meta.get("fabric_id") or "global-h3-v1")
    revision = str(meta.get("fabric_revision") or "")
    if not revision and document.get("features"):
        revision = str(document["features"][0].get("properties", {}).get("fabric_revision") or "")
    if not revision:
        raise SystemExit("fabric input lacks a revision")
    return f"{fabric_id}-r{revision.removeprefix('r')}"


def _artifact_version(path: Path) -> str:
    if path.suffix == ".md":
        return ARTIFACT_VERSION
    return str(_load(path).get("artifact_version") or ARTIFACT_VERSION)


def _write_candidate_status(output: Path, status: str, **extra: str) -> None:
    _write(output / "candidate_status.json", {
        "pass_id": PASS_ID, "start_date": START_DATE, "status": status,
        "public_release_allowed": False, **extra,
    })


def _load(path: Path) -> dict[str, Any]:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"cannot read JSON {path}: {exc}") from exc


def _write(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
