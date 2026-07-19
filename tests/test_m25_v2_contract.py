import hashlib
import json
from pathlib import Path

import pytest

from gpm.builders.aggregation import ProvinceAggregationError, aggregate_location_provinces
from gpm.cli import main
from gpm.qa.render import render_start_date_pass
from gpm.qa.start_date import run_start_date_qa
from gpm.schemas import (
    SchemaValidationError,
    validate_historical_boundary_registry,
    validate_location_assignments,
    validate_spatial_golden_borders,
    validate_start_date_source_manifest,
)
from test_m24_start_date_framework import _make_pass


def _polygon(x0, y0, x1, y1):
    return {"type": "Polygon", "coordinates": [[[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]]]}


def _write(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _make_v2_pass(root: Path) -> None:
    _make_pass(root)
    pass_id, version = "fixture-1444-v2", "2.0.0"
    derived_geometry = {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"source_feature_reference": "fixture plate 1"}, "geometry": {"type": "LineString", "coordinates": [[1, 0], [1, 1]]}}]}
    coverage_mask = {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"polity_id": "fra"}, "geometry": _polygon(0, 0, 1, 1)}]}
    _write(root / "derived-frontier.geojson", derived_geometry)
    _write(root / "coverage-mask.geojson", coverage_mask)

    source_manifest = json.loads((root / "source_manifest.json").read_text())
    base_source = source_manifest["sources"][0]
    source_manifest["sources"] = [
        {**base_source, "source_id": "src-primary", "citation": "Fixture academic reconstruction", "source_type": "academic", "valid_from": "1444-01-01", "valid_to": "1444-12-31", "independence_group": "academic-fixture", "derived_artifacts": [
            {"artifact_id": "derived-frontier", "role": "boundary_geometry", "path": "derived-frontier.geojson", "sha256": _hash(root / "derived-frontier.geojson"), "media_type": "application/geo+json"},
            {"artifact_id": "coverage-fra", "role": "coverage_mask", "path": "coverage-mask.geojson", "sha256": _hash(root / "coverage-mask.geojson"), "media_type": "application/geo+json"},
        ]},
        {**base_source, "source_id": "src-corroboration", "citation": "Independent fixture corroboration", "source_type": "corroborating", "valid_from": "1444", "valid_to": "1444", "independence_group": "corroboration-fixture", "derived_artifacts": []},
    ]

    boundaries = json.loads((root / "boundaries.geojson").read_text())
    frontier, forbidden = boundaries["features"]
    frontier["properties"].update(
        source_ids=["src-primary", "src-corroboration"], derived_geometry_artifact_id="derived-frontier", error_budget_km=2.0,
        georeferencing={"transform_method": "affine", "crs": "EPSG:4326", "control_points": [{"id": "a"}, {"id": "b"}, {"id": "c"}], "residual_error_km": 1.5, "digitizer": "fixture-generator", "reviewer": "fixture-boundary-reviewer", "source_feature_reference": "fixture plate 1"},
    )
    forbidden["properties"].update(classification="soft_evidence", source_ids=["src-corroboration"])

    gazetteer = json.loads((root / "gazetteer.json").read_text())
    for polity in gazetteer["polities"]:
        polity["source_ids"] = ["src-primary", "src-corroboration"]
        for relationship in polity["relationships"]:
            relationship["source_ids"] = ["src-primary", "src-corroboration"]

    assignments = json.loads((root / "assignments.json").read_text())
    assignments["constraint_sha256"] = _hash(root / "boundaries.geojson") if (root / "boundaries.geojson").exists() else "0" * 64
    for row in assignments["assignments"]:
        polity = row["polity_ids"][0]
        row.update(region_id="fixture-region", sovereign_polity_id=polity, owner_polity_id=polity, controller_polity_id=polity,
                   core_polity_ids=[polity], claim_polity_ids=[], dispute_polity_ids=[], source_ids=["src-primary", "src-corroboration"],
                   hierarchy={"area_id": f"area-{polity}", "region_id": "fixture-region", "superregion_id": "fixture-superregion", "method": "deterministic-fixture"})

    golden = json.loads((root / "golden.json").read_text())
    for assertion in golden["assertions"]:
        if assertion["spatial_relation"] == "border_matches_boundary_hausdorff_lte":
            assertion.update(spatial_relation="border_matches_boundary_hausdorff_km_lte", unit="kilometres", tolerance=2.0)

    coverage = json.loads((root / "coverage.json").read_text())
    grade_by_layer = {"geometry": "B", "politics": "B", "hierarchy": "C", "gazetteer_relationships": "B"}
    for row in coverage["coverage"]:
        row.update(grade=grade_by_layer[row["layer"]], source_ids=["src-primary", "src-corroboration"], known_gaps=["Miniature fixture generalization."])

    documents = {
        "source_manifest.json": source_manifest, "boundaries.geojson": boundaries, "gazetteer.json": gazetteer,
        "assignments.json": assignments, "golden.json": golden, "coverage.json": coverage,
        "changelog.json": json.loads((root / "changelog.json").read_text()),
        "build.geojson": json.loads((root / "build.geojson").read_text()),
    }
    for document in documents.values():
        document.update(schema_version="0.2.0", artifact_version=version, pass_id=pass_id)
    documents["changelog.json"]["version"] = version

    constraint_sha = hashlib.sha256((json.dumps(boundaries, indent=2, sort_keys=True) + "\n").encode()).hexdigest()
    documents["assignments.json"]["constraint_sha256"] = constraint_sha
    aggregation = {"actual_province_count": 2, "historical_constraint_policy": {"sha256": constraint_sha}}
    _write(root / "aggregation_manifest.json", aggregation)
    province_ids = [row["province_id"] for row in assignments["assignments"]]
    (root / "adjacency.csv").write_text(f"from_province_id,to_province_id\n{province_ids[0]},{province_ids[1]}\n", encoding="utf-8")
    documents["assignments.json"]["release_sidecars"] = {
        "aggregation_manifest": {"path": "aggregation_manifest.json", "sha256": _hash(root / "aggregation_manifest.json")},
        "adjacency": {"path": "adjacency.csv", "sha256": _hash(root / "adjacency.csv")},
    }
    for name, document in documents.items():
        _write(root / name, document)

    review_dir = root / "review"
    review_dir.mkdir(exist_ok=True)
    (review_dir / "fixture-region.svg").write_text("<svg xmlns=\"http://www.w3.org/2000/svg\"><title>fixture-region</title></svg>\n", encoding="utf-8")
    review = {"schema_version": "0.2.0", "document_type": "start_date_review_manifest", "pass_id": pass_id, "generator": "fixture-generator", "reviewer": "fixture-human-reviewer", "status": "accepted", "renders": [{"region_id": "fixture-region", "path": "fixture-region.svg", "sha256": _hash(review_dir / "fixture-region.svg")} ]}
    _write(review_dir / "review_manifest.json", review)

    manifest = json.loads((root / "pass_manifest.json").read_text())
    manifest.update(schema_version="0.2.0", artifact_version=version, pass_id=pass_id, version=version,
                    review={"manifest_path": "review/review_manifest.json", "sha256": _hash(review_dir / "review_manifest.json"), "generator": "fixture-generator", "reviewer": "fixture-human-reviewer", "status": "accepted"})
    for record in manifest["artifacts"].values():
        record["version"] = version
        record["sha256"] = _hash(root / record["path"])
    _write(root / "pass_manifest.json", manifest)


def test_constraint_aware_aggregation_blocks_hard_crossing_and_pins_hash(tmp_path):
    locations = {"type": "FeatureCollection", "gpm": {"fabric_id": "fixture", "fabric_revision": "2", "geometry_revision": "1444-r2"}, "features": [
        {"type": "Feature", "properties": {"location_id": "a"}, "geometry": _polygon(0, 0, 1, 1)},
        {"type": "Feature", "properties": {"location_id": "b"}, "geometry": _polygon(1, 0, 2, 1)},
    ]}
    constraints = {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"classification": "hard_constraint"}, "geometry": {"type": "LineString", "coordinates": [[1, 0], [1, 1]]}}]}
    _write(tmp_path / "locations.geojson", locations); _write(tmp_path / "constraints.geojson", constraints)
    with pytest.raises(ProvinceAggregationError, match="stopped aggregation"):
        aggregate_location_provinces("eu-like", location_input=tmp_path / "locations.geojson", output_dir=tmp_path / "blocked", target_province_count=1, historical_constraints_input=tmp_path / "constraints.geojson", generated_at="2026-07-15T00:00:00+00:00")
    result = aggregate_location_provinces("eu-like", location_input=tmp_path / "locations.geojson", output_dir=tmp_path / "kept", target_province_count=2, historical_constraints_input=tmp_path / "constraints.geojson", generated_at="2026-07-15T00:00:00+00:00")
    manifest = json.loads(Path(result.manifest_output).read_text())
    assert manifest["historical_constraint_policy"] == {
        "hard_constraints": "remove_crossing_merge_edges",
        "soft_evidence": "merge_score_penalty_only",
        "sha256": hashlib.sha256((tmp_path / "constraints.geojson").read_bytes()).hexdigest(),
    }


def test_schema_02_requires_georeferencing_derived_evidence_and_typed_assignments():
    header = {"schema_version": "0.2.0", "artifact_version": "2", "pass_id": "v2", "start_date": "1444-11-11"}
    source = {**header, "document_type": "start_date_source_manifest", "conflict_resolution_notes": [], "sources": [{
        "source_id": "s", "citation": "Source", "url": None, "access_date": None, "version": None,
        "license": "Public domain", "checksum": None, "transformations": [], "review_status": "reviewed",
    }]}
    with pytest.raises(SchemaValidationError, match="source_type"):
        validate_start_date_source_manifest(source)

    boundary = {**header, "document_type": "historical_boundary_registry", "type": "FeatureCollection", "features": [{
        "type": "Feature", "geometry": {"type": "LineString", "coordinates": [[0, 0], [1, 1]]}, "properties": {
            "feature_id": "b", "geometry_revision": "1444-r2", "valid_from": "1444", "valid_to": "1444", "date_precision": "year", "semantics": "frontier",
            "side_polity_ids": {"left": "a", "right": "b"}, "source_ids": ["s"], "license_lineage": ["PD"], "confidence": "high", "uncertainty_notes": "n",
            "classification": "hard_constraint", "geographic_scope": "r", "start_date_programs": ["1444-11-11"],
        }}]}
    with pytest.raises(SchemaValidationError, match="derived_geometry_artifact_id"):
        validate_historical_boundary_registry(boundary)

    assignments = {**header, "document_type": "start_date_location_assignments", "fabric_revision": "global-h3-v1-r2", "aggregation_revision": "1444-r2", "aggregation_profile": "eu-like", "geometry_revision": "1444-r2", "expected_province_count": 1,
        "fabric_sidecars": {role: {"path": role, "sha256": "a" * 64} for role in ("fabric_manifest", "locations", "lineage", "province_membership")},
        "constraint_sha256": "b" * 64, "release_sidecars": {role: {"path": role, "sha256": "c" * 64} for role in ("aggregation_manifest", "adjacency")},
        "assignments": [{"assignment_id": "a", "location_ids": ["l"], "province_id": "p", "polity_ids": ["x"], "uncertainty": 0, "source_ids": ["s"], "notes": ""}], "targeted_split_requests": []}
    with pytest.raises(SchemaValidationError, match="region_id"):
        validate_location_assignments(assignments)


def test_schema_02_uses_kilometre_golden_relation():
    document = {"schema_version": "0.2.0", "document_type": "spatial_golden_borders", "artifact_version": "2", "pass_id": "v2", "start_date": "1444-11-11", "assertions": [{
        "assertion_id": "b", "region_id": "r", "layer": "geometry", "assertion_type": "border", "expectation": "positive", "subject_ids": ["a", "b"], "boundary_feature_ids": ["f"],
        "spatial_relation": "border_matches_boundary_hausdorff_km_lte", "unit": "kilometres", "tolerance": 10, "notes": "Measured in kilometres.",
    }]}
    validate_spatial_golden_borders(document)


def _rehash_artifact(root: Path, role: str) -> None:
    manifest = json.loads((root / "pass_manifest.json").read_text())
    record = manifest["artifacts"][role]
    record["sha256"] = _hash(root / record["path"])
    _write(root / "pass_manifest.json", manifest)


def _finding_codes(root: Path) -> set[str]:
    run_start_date_qa(pass_dir=root)
    return {finding["code"] for finding in json.loads((root / "start_date_qa.json").read_text())["findings"]}


def test_complete_miniature_v2_pass_is_accepted(tmp_path):
    _make_v2_pass(tmp_path)
    first = run_start_date_qa(pass_dir=tmp_path)
    first_report = (tmp_path / "start_date_qa.json").read_bytes()
    second = run_start_date_qa(pass_dir=tmp_path)
    assert first.passed and second.passed
    assert first_report == (tmp_path / "start_date_qa.json").read_bytes()
    assert json.loads(first_report)["milestone"] == "M25"


def test_v2_rejects_missing_coverage_mask_and_copied_modern_geometry(tmp_path):
    _make_v2_pass(tmp_path)
    sources = json.loads((tmp_path / "source_manifest.json").read_text())
    sources["sources"][0]["derived_artifacts"] = [
        item for item in sources["sources"][0]["derived_artifacts"] if item["role"] != "coverage_mask"
    ]
    _write(tmp_path / "source_manifest.json", sources)
    _rehash_artifact(tmp_path, "source_manifest")
    assert "MISSING_POLITY_COVERAGE_MASK" in _finding_codes(tmp_path)

    _make_v2_pass(tmp_path)
    boundaries = json.loads((tmp_path / "boundaries.geojson").read_text())
    boundaries["features"][0]["geometry"] = boundaries["features"][1]["geometry"]
    _write(tmp_path / "boundaries.geojson", boundaries)
    _rehash_artifact(tmp_path, "boundary_registry")
    assert "COPIED_NEGATIVE_CONTROL_GEOMETRY" in _finding_codes(tmp_path)


def test_v2_rejects_invalid_lineage_adjacency_and_tampered_review(tmp_path):
    _make_v2_pass(tmp_path)
    assignments = json.loads((tmp_path / "assignments.json").read_text())
    assignments["targeted_split_requests"] = [{"request_id": "missing-lineage", "location_ids": ["loc-a"], "reason": "fixture split", "status": "accepted", "source_ids": ["src-primary"]}]
    _write(tmp_path / "assignments.json", assignments)
    _rehash_artifact(tmp_path, "location_assignments")
    assert "ACCEPTED_SPLIT_WITHOUT_LINEAGE" in _finding_codes(tmp_path)

    _make_v2_pass(tmp_path)
    (tmp_path / "adjacency.csv").write_text("from_province_id,to_province_id\nmissing,missing\n", encoding="utf-8")
    assignments = json.loads((tmp_path / "assignments.json").read_text())
    assignments["release_sidecars"]["adjacency"]["sha256"] = _hash(tmp_path / "adjacency.csv")
    _write(tmp_path / "assignments.json", assignments)
    _rehash_artifact(tmp_path, "location_assignments")
    assert "INVALID_FULL_BUILD_ADJACENCY" in _finding_codes(tmp_path)

    _make_v2_pass(tmp_path)
    (tmp_path / "review/fixture-region.svg").write_text("<svg>tampered</svg>\n", encoding="utf-8")
    assert "TAMPERED_REVIEW_RENDER" in _finding_codes(tmp_path)


def test_v2_schema_rejects_incomplete_politics_hierarchy_and_nonindependent_digitizing():
    header = {"schema_version": "0.2.0", "artifact_version": "2", "pass_id": "v2", "start_date": "1444-11-11"}
    assignments = {**header, "document_type": "start_date_location_assignments", "fabric_revision": "r2", "aggregation_revision": "1444-r2", "aggregation_profile": "eu-like", "geometry_revision": "1444-r2", "expected_province_count": 1,
        "fabric_sidecars": {role: {"path": role, "sha256": "a" * 64} for role in ("fabric_manifest", "locations", "lineage", "province_membership")},
        "constraint_sha256": "b" * 64, "release_sidecars": {role: {"path": role, "sha256": "c" * 64} for role in ("aggregation_manifest", "adjacency")},
        "assignments": [{"assignment_id": "a", "location_ids": ["l"], "province_id": "p", "polity_ids": ["x"], "uncertainty": 0, "source_ids": ["s"], "notes": "", "region_id": "r", "sovereign_polity_id": "x", "owner_polity_id": "x", "controller_polity_id": "x", "core_polity_ids": [], "claim_polity_ids": [], "dispute_polity_ids": []}], "targeted_split_requests": []}
    with pytest.raises(SchemaValidationError, match="hierarchy"):
        validate_location_assignments(assignments)

    boundary = {**header, "document_type": "historical_boundary_registry", "type": "FeatureCollection", "features": [{"type": "Feature", "geometry": {"type": "LineString", "coordinates": [[0, 0], [1, 1]]}, "properties": {
        "feature_id": "b", "geometry_revision": "1444-r2", "valid_from": "1444", "valid_to": "1444", "date_precision": "year", "semantics": "frontier", "side_polity_ids": {"left": "a", "right": "b"}, "source_ids": ["s"], "license_lineage": ["PD"], "confidence": "high", "uncertainty_notes": "n", "classification": "hard_constraint", "geographic_scope": "r", "start_date_programs": ["1444-11-11"], "derived_geometry_artifact_id": "d", "error_budget_km": 1, "georeferencing": {"transform_method": "affine", "crs": "EPSG:4326", "control_points": [{}, {}, {}], "residual_error_km": 1, "digitizer": "same", "reviewer": "same", "source_feature_reference": "plate"}
    }}]}
    with pytest.raises(SchemaValidationError, match="reviewer must differ"):
        validate_historical_boundary_registry(boundary)


def test_v2_schema_accepts_reproducible_structured_feature_reference():
    header = {"schema_version": "0.2.0", "artifact_version": "2", "pass_id": "v2", "start_date": "1444-11-11"}
    properties = {
        "feature_id": "b", "geometry_revision": "1444-r2", "valid_from": "1444", "valid_to": "1444", "date_precision": "year",
        "semantics": "frontier", "side_polity_ids": {"left": "a", "right": "b"}, "source_ids": ["s"], "license_lineage": ["PD"],
        "confidence": "high", "uncertainty_notes": "n", "classification": "hard_constraint", "geographic_scope": "r",
        "start_date_programs": ["1444-11-11"], "derived_geometry_artifact_id": "d", "error_budget_km": 1,
        "georeferencing": {
            "transform_method": "substring", "crs": "EPSG:4326", "control_points": [{}, {}, {}], "residual_error_km": 1,
            "digitizer": "fixture-digitizer", "reviewer": "fixture-reviewer", "source_feature_reference": {
                "kind": "ne-rivers", "record_indexes": [42], "substring": {
                    "measure_units": "substrate-line-planar-degrees", "start_measure": 0.25, "end_measure": 0.75,
                    "substrate_merge_rule": "shapely-linemerge-longest-component",
                },
            },
        },
    }
    boundary = {**header, "document_type": "historical_boundary_registry", "type": "FeatureCollection", "features": [{
        "type": "Feature", "geometry": {"type": "LineString", "coordinates": [[0, 0], [1, 1]]}, "properties": properties,
    }]}
    validate_historical_boundary_registry(boundary)
    properties["georeferencing"]["source_feature_reference"]["substring"]["end_measure"] = 0.1
    with pytest.raises(SchemaValidationError, match="start_measure < end_measure"):
        validate_historical_boundary_registry(boundary)


def test_render_is_deterministic_and_cli_writes_region_sheets(tmp_path):
    pass_dir = tmp_path / "pass"; pass_dir.mkdir()
    build = {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"feature_id": "p", "feature_type": "province"}, "geometry": _polygon(0, 0, 1, 1)}]}
    boundaries = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"feature_id": "frontier", "geographic_scope": "france", "classification": "hard_constraint", "error_budget_km": 2,
         "georeferencing": {"transform_method": "substring", "crs": "EPSG:4326", "residual_error_km": 1.5,
                             "control_points": [{"name": "anchor", "lon": 1, "lat": 0.5, "residual_km": 1.5}]}},
         "geometry": {"type": "LineString", "coordinates": [[1, 0], [1, 1]]}},
        {"type": "Feature", "properties": {"feature_id": "forbidden-modern-france", "geographic_scope": "france", "classification": "soft_evidence"},
         "geometry": {"type": "LineString", "coordinates": [[0.75, 0], [0.75, 1]]}},
    ]}
    assignments = {"assignments": [{"province_id": "p", "region_id": "france", "owner_polity_id": "fra", "uncertainty": 0.2, "hierarchy": {"area_id": "a"}}]}
    for name, value in (("build.json", build), ("boundaries.json", boundaries), ("assignments.json", assignments)): _write(pass_dir / name, value)
    manifest = {"pass_id": "v2", "geometry_revision": "1444-r2", "generated_at": "2026-07-15T00:00:00Z", "scope": {"priority_regions": ["france"]}, "artifacts": {
        "full_build_geometry": {"path": "build.json"}, "boundary_registry": {"path": "boundaries.json"}, "location_assignments": {"path": "assignments.json"}}}
    _write(pass_dir / "pass_manifest.json", manifest)
    first = render_start_date_pass(pass_dir=pass_dir, output_dir=tmp_path / "one")
    second = render_start_date_pass(pass_dir=pass_dir, output_dir=tmp_path / "two")
    assert (tmp_path / "one/france.svg").read_bytes() == (tmp_path / "two/france.svg").read_bytes()
    assert (tmp_path / "one/review_manifest.json").read_bytes() == (tmp_path / "two/review_manifest.json").read_bytes()
    svg = (tmp_path / "one/france.svg").read_text()
    assert "Inset A — frontier (hard constraint)" in svg
    assert "max residual 1.5 km ≤ budget 2 km" in svg
    assert "anchor (1.5 km)" in svg
    assert "Inset B — forbidden-modern-france" in svg
    assert "negative control: modern outline vs 1444 provinces" in svg
    assert first.region_count == second.region_count == 1
    assert main(["qa", "render", "--pass-dir", str(pass_dir), "--output-dir", str(tmp_path / "cli"), "--format", "json"]) == 0
