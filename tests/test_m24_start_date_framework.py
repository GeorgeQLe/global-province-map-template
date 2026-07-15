import copy
import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from gpm.cli import main
from gpm.qa.start_date import run_start_date_qa
from gpm.schemas import (
    SchemaValidationError, load_schema, validate_historical_boundary_registry,
    validate_location_assignments, validate_polity_gazetteer, validate_spatial_golden_borders,
    validate_start_date_changelog, validate_start_date_coverage, validate_start_date_pass_manifest,
    validate_start_date_qa_report, validate_start_date_source_manifest,
)


def _write(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _polygon(x0, y0, x1, y1):
    return {"type": "Polygon", "coordinates": [[[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]]]}


def _make_pass(root: Path) -> Path:
    pass_id, start_date, version = "fixture-1444-v1", "1444-11-11", "1.0.0"
    header = {"schema_version": "0.1.0", "artifact_version": version, "pass_id": pass_id, "start_date": start_date}
    def province_id(location_id: str) -> str:
        payload = json.dumps({"members": [[location_id, "whole"]], "profile_id": "fixture", "start_date": start_date, "aggregation_revision": "1", "geometry_revision": "1444-r1"}, sort_keys=True, separators=(",", ":"))
        return f"prv_{hashlib.sha256(payload.encode()).hexdigest()[:20]}"
    province_a, province_b = province_id("loc-a"), province_id("loc-b")
    (root / "dossier.md").write_text(
        "# Fixture dossier\n\n## Scope\nFixture region.\n\n## Research Questions\nWhich border applies?\n\n"
        "## Citations\nFixture map.\n\n## Transformations and Conflicts\nGeoreferenced; no unresolved conflict.\n\n"
        "## Exclusions\nNone.\n\n## Uncertainty\nGeneralized line.\n", encoding="utf-8")
    boundaries = []
    for fid, geometry, semantics in (
        ("frontier", {"type": "LineString", "coordinates": [[1, 0], [1, 1]]}, "sovereignty frontier"),
        ("forbidden-modern", _polygon(10, 10, 11, 11), "forbidden modern outline"),
    ):
        boundaries.append({"type": "Feature", "geometry": geometry, "properties": {
            "feature_id": fid, "geometry_revision": "1", "valid_from": "1444-01-01", "valid_to": "1444-12-31",
            "date_precision": "year", "semantics": semantics, "side_polity_ids": {"left": "fra", "right": "bur"},
            "source_ids": ["src-map"], "license_lineage": ["Public domain"], "confidence": "high",
            "uncertainty_notes": "Generalized fixture.", "classification": "hard_constraint",
            "geographic_scope": "fixture-region", "start_date_programs": [start_date],
        }})
    assertions = [
        {"assertion_id": "border", "region_id": "fixture-region", "layer": "geometry", "assertion_type": "border", "expectation": "positive", "subject_ids": ["province-a", "province-b"], "boundary_feature_ids": ["frontier"], "spatial_relation": "border_matches_boundary_hausdorff_lte", "unit": "coordinate_units", "tolerance": 0.01, "notes": "Adjacent provinces share the dated frontier."},
        {"assertion_id": "capital-politics", "region_id": "fixture-region", "layer": "politics", "assertion_type": "capital", "expectation": "positive", "subject_ids": ["loc-a", "province-a"], "boundary_feature_ids": [], "spatial_relation": "capital_within_subject", "unit": "boolean", "tolerance": 1, "notes": "Capital belongs to its polity province."},
        {"assertion_id": "capital-hierarchy", "region_id": "fixture-region", "layer": "hierarchy", "assertion_type": "capital", "expectation": "positive", "subject_ids": ["loc-a", "province-a"], "boundary_feature_ids": [], "spatial_relation": "capital_within_subject", "unit": "boolean", "tolerance": 1, "notes": "Capital belongs to the hierarchy."},
        {"assertion_id": "capital-gazetteer", "region_id": "fixture-region", "layer": "gazetteer_relationships", "assertion_type": "capital", "expectation": "positive", "subject_ids": ["loc-a", "province-a"], "boundary_feature_ids": [], "spatial_relation": "capital_within_subject", "unit": "boolean", "tolerance": 1, "notes": "Gazetteer capital is spatially valid."},
        {"assertion_id": "negative-modern", "region_id": "fixture-region", "layer": "geometry", "assertion_type": "outline", "expectation": "negative_anachronism", "subject_ids": ["province-a"], "boundary_feature_ids": ["forbidden-modern"], "spatial_relation": "forbidden_outline_overlap_ratio_lte", "unit": "ratio", "tolerance": 0.1, "notes": "Forbidden modern outline is absent."},
    ]
    by_layer = {layer: [a["assertion_id"] for a in assertions if a["layer"] == layer] for layer in ("geometry", "politics", "hierarchy", "gazetteer_relationships")}
    documents = {
        "source_manifest.json": {**header, "document_type": "start_date_source_manifest", "sources": [{"source_id": "src-map", "citation": "Fixture historical map", "url": "https://example.invalid/map", "access_date": "2026-07-13", "version": "1", "license": "Public domain", "checksum": "a" * 64, "transformations": ["georeferenced"], "review_status": "reviewed"}], "conflict_resolution_notes": ["Primary map controls the fixture boundary."]},
        "boundaries.geojson": {**header, "document_type": "historical_boundary_registry", "type": "FeatureCollection", "features": boundaries},
        "gazetteer.json": {**header, "document_type": "polity_gazetteer", "polities": [
            {"polity_id": "fra", "name": "France", "aliases": [], "valid_from": "0987", "valid_to": None, "capital_location_ids": ["loc-a"], "source_ids": ["src-map"], "relationships": [{"relationship_id": "fra-claims-bur", "type": "claim", "target_polity_id": "bur", "valid_from": "1444", "valid_to": None, "source_ids": ["src-map"], "confidence": "medium", "notes": "Fixture relationship."}]},
            {"polity_id": "bur", "name": "Burgundy", "aliases": [], "valid_from": "1363", "valid_to": "1477", "capital_location_ids": ["loc-b"], "source_ids": ["src-map"], "relationships": []}]},
        "assignments.json": {**header, "document_type": "start_date_location_assignments", "fabric_revision": "global-h3-v1-r1", "aggregation_revision": "1", "aggregation_profile": "fixture", "geometry_revision": "1444-r1", "expected_province_count": 2, "fabric_sidecars": {}, "targeted_split_requests": [], "assignments": [
            {"assignment_id": "assignment-a", "location_ids": ["loc-a"], "province_id": "province-a", "polity_ids": ["fra"], "uncertainty": 0.1, "source_ids": ["src-map"], "notes": "Fixture."},
            {"assignment_id": "assignment-b", "location_ids": ["loc-b"], "province_id": "province-b", "polity_ids": ["bur"], "uncertainty": 0.1, "source_ids": ["src-map"], "notes": "Fixture."}]},
        "golden.json": {**header, "document_type": "spatial_golden_borders", "assertions": assertions},
        "build.geojson": {**header, "document_type": "start_date_full_build_geometry", "geometry_revision": "1444-r1", "type": "FeatureCollection", "features": [
            {"type": "Feature", "properties": {"feature_id": "province-a", "feature_type": "province"}, "geometry": _polygon(0, 0, 1, 1)},
            {"type": "Feature", "properties": {"feature_id": "province-b", "feature_type": "province"}, "geometry": _polygon(1, 0, 2, 1)},
            {"type": "Feature", "properties": {"feature_id": "loc-a", "feature_type": "capital"}, "geometry": {"type": "Point", "coordinates": [0.5, 0.5]}},
            {"type": "Feature", "properties": {"feature_id": "loc-b", "feature_type": "capital"}, "geometry": {"type": "Point", "coordinates": [1.5, 0.5]}}]},
        "coverage.json": {**header, "document_type": "start_date_coverage", "exclusions": [], "known_gaps": [], "coverage": [{"region_id": "fixture-region", "layer": layer, "grade": "A", "source_ids": ["src-map"], "assertion_ids": by_layer[layer], "evidence_summary": "Reviewed fixture evidence and executed QA.", "exclusions": [], "known_gaps": []} for layer in by_layer]},
        "changelog.json": {**header, "document_type": "start_date_changelog", "version": version, "released_at": "2026-07-13", "changes": [{"change_id": "initial", "category": "research", "summary": "Initial fixture pass.", "affected_ids": []}], "migrations": []},
    }
    documents = json.loads(json.dumps(documents).replace('"province-a"', json.dumps(province_a)).replace('"province-b"', json.dumps(province_b)))
    sidecar_documents = {
        "fabric_manifest.json": {"schema_version": "0.1.0", "manifest_type": "location_fabric", "fabric_id": "global-h3-v1", "fabric_revision": "1"},
        "locations.geojson": {"type": "FeatureCollection", "features": [
            {"type": "Feature", "properties": {"location_id": "loc-a"}, "geometry": _polygon(0, 0, 1, 1)},
            {"type": "Feature", "properties": {"location_id": "loc-b"}, "geometry": _polygon(1, 0, 2, 1)},
        ]},
        "location_lineage.json": {"schema_version": "0.1.0", "fabric_id": "global-h3-v1", "fabric_revision": "1", "events": []},
    }
    for name, document in sidecar_documents.items():
        _write(root / name, document)
    (root / "province_membership.csv").write_text(
        f"province_id,location_id,piece_id\n{province_a},loc-a,whole\n{province_b},loc-b,whole\n",
        encoding="utf-8",
    )
    documents["assignments.json"]["fabric_sidecars"] = {
        role: {"path": name, "sha256": _hash(root / name)} for role, name in {
            "fabric_manifest": "fabric_manifest.json", "locations": "locations.geojson",
            "lineage": "location_lineage.json", "province_membership": "province_membership.csv",
        }.items()
    }
    for name, document in documents.items(): _write(root / name, document)
    artifact_names = {"dossier": "dossier.md", "source_manifest": "source_manifest.json", "boundary_registry": "boundaries.geojson", "polity_gazetteer": "gazetteer.json", "location_assignments": "assignments.json", "golden_borders": "golden.json", "full_build_geometry": "build.geojson", "coverage_matrix": "coverage.json", "changelog": "changelog.json"}
    manifest = {**header, "document_type": "start_date_research_pass", "version": version, "era": "late-medieval", "fabric_revision": "global-h3-v1-r1", "geometry_revision": "1444-r1", "generated_at": "2026-07-13T12:00:00Z", "scope": {"regions": ["fixture-region"], "priority_regions": ["fixture-region"], "layers": ["geometry", "politics", "hierarchy", "gazetteer_relationships"]}, "artifacts": {kind: {"path": name, "version": version, "sha256": _hash(root / name)} for kind, name in artifact_names.items()}}
    _write(root / "pass_manifest.json", manifest)
    return root / "pass_manifest.json"


def _rehash(root: Path, kind: str) -> None:
    manifest = json.loads((root / "pass_manifest.json").read_text())
    path = root / manifest["artifacts"][kind]["path"]
    manifest["artifacts"][kind]["sha256"] = _hash(path)
    _write(root / "pass_manifest.json", manifest)


def _rehash_sidecar(root: Path, role: str) -> None:
    assignments = json.loads((root / "assignments.json").read_text())
    sidecar = root / assignments["fabric_sidecars"][role]["path"]
    assignments["fabric_sidecars"][role]["sha256"] = _hash(sidecar)
    _write(root / "assignments.json", assignments)
    _rehash(root, "location_assignments")


def test_m24_complete_pass_executes_spatial_contract_and_cli(tmp_path, capsys):
    _make_pass(tmp_path)
    first = run_start_date_qa(pass_dir=tmp_path)
    first_report = (tmp_path / "start_date_qa.json").read_bytes()
    second = run_start_date_qa(pass_dir=tmp_path)
    assert first.passed and second.passed and first.artifact_count == 9
    assert first_report == (tmp_path / "start_date_qa.json").read_bytes()
    report = json.loads(first_report)
    assert {item["status"] for item in report["assertion_results"]} == {"pass"}
    assert main(["qa", "start-date", "--pass-dir", str(tmp_path), "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "pass"


@pytest.mark.parametrize(("kind", "path", "value", "code"), [
    ("boundary_registry", ("features", 0, "properties", "valid_to"), "1400", "BOUNDARY_DATE_OUT_OF_RANGE"),
    ("polity_gazetteer", ("polities", 0, "capital_location_ids"), ["missing"], "UNKNOWN_CAPITAL_LOCATION"),
    ("polity_gazetteer", ("polities", 0, "relationships", 0, "source_ids"), ["missing"], "UNKNOWN_RELATIONSHIP_SOURCE"),
    ("location_assignments", ("targeted_split_requests",), [{"request_id": "split", "location_ids": ["missing"], "reason": "needed", "status": "requested", "source_ids": ["missing"]}], "UNKNOWN_SPLIT_LOCATION"),
    ("full_build_geometry", ("features", 1, "geometry", "coordinates"), [[[3, 0], [4, 0], [4, 1], [3, 1], [3, 0]]], "SPATIAL_ASSERTION_FAILED"),
])
def test_cross_artifact_and_spatial_failures(tmp_path, kind, path, value, code):
    _make_pass(tmp_path)
    manifest = json.loads((tmp_path / "pass_manifest.json").read_text())
    artifact = tmp_path / manifest["artifacts"][kind]["path"]
    document = json.loads(artifact.read_text())
    target = document
    for part in path[:-1]: target = target[part]
    target[path[-1]] = value
    _write(artifact, document); _rehash(tmp_path, kind)
    result = run_start_date_qa(pass_dir=tmp_path)
    codes = {item["code"] for item in json.loads((tmp_path / "start_date_qa.json").read_text())["findings"]}
    assert not result.passed and code in codes


def test_checksum_failure_returns_one_without_certification(tmp_path, capsys):
    _make_pass(tmp_path)
    coverage = json.loads((tmp_path / "coverage.json").read_text()); coverage["coverage"][0]["source_ids"] = ["missing"]
    _write(tmp_path / "coverage.json", coverage)
    assert main(["qa", "start-date", "--pass-dir", str(tmp_path), "--format", "json"]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "fail"
    report = json.loads((tmp_path / "start_date_qa.json").read_text())
    assert {item["code"] for item in report["findings"]} >= {"CHECKSUM_MISMATCH", "UNCERTIFIED_A_GRADE"}


def test_dossier_completeness_and_symlink_are_fail_closed(tmp_path):
    _make_pass(tmp_path)
    (tmp_path / "dossier.md").write_text("# Empty shell\n", encoding="utf-8")
    result = run_start_date_qa(pass_dir=tmp_path)
    assert not result.passed
    assert "INCOMPLETE_DOSSIER" in {item["code"] for item in json.loads((tmp_path / "start_date_qa.json").read_text())["findings"]}


def test_all_nine_schemas_are_draft_2020_12_and_reject_unknown_fields(tmp_path):
    manifest_path = _make_pass(tmp_path)
    validators = {
        "start-date-pass-manifest": (manifest_path, validate_start_date_pass_manifest),
        "start-date-source-manifest": (tmp_path / "source_manifest.json", validate_start_date_source_manifest),
        "historical-boundary-registry": (tmp_path / "boundaries.geojson", validate_historical_boundary_registry),
        "polity-gazetteer": (tmp_path / "gazetteer.json", validate_polity_gazetteer),
        "start-date-location-assignments": (tmp_path / "assignments.json", validate_location_assignments),
        "spatial-golden-borders": (tmp_path / "golden.json", validate_spatial_golden_borders),
        "start-date-coverage": (tmp_path / "coverage.json", validate_start_date_coverage),
        "start-date-changelog": (tmp_path / "changelog.json", validate_start_date_changelog),
    }
    for name, (path, validator) in validators.items():
        schema = load_schema(name); Draft202012Validator.check_schema(schema)
        document = json.loads(path.read_text()); validator(document)
        document["misspelled_field"] = True
        with pytest.raises(SchemaValidationError): validator(document)
    run_start_date_qa(pass_dir=tmp_path)
    qa_schema = load_schema("start-date-qa-report"); Draft202012Validator.check_schema(qa_schema)
    report = json.loads((tmp_path / "start_date_qa.json").read_text()); validate_start_date_qa_report(report)
    report["misspelled_field"] = True
    with pytest.raises(SchemaValidationError): validate_start_date_qa_report(report)


def test_manifest_rejects_unexpected_artifact_and_path_traversal(tmp_path):
    manifest_path = _make_pass(tmp_path); manifest = json.loads(manifest_path.read_text())
    manifest["artifacts"]["surprise"] = copy.deepcopy(manifest["artifacts"]["dossier"])
    with pytest.raises(SchemaValidationError): validate_start_date_pass_manifest(manifest)
    manifest = json.loads(manifest_path.read_text()); manifest["artifacts"]["dossier"]["path"] = "../dossier.md"
    _write(manifest_path, manifest)
    result = run_start_date_qa(pass_dir=tmp_path)
    assert not result.passed
    assert "ARTIFACT_OUTSIDE_PASS" in {item["code"] for item in json.loads((tmp_path / "start_date_qa.json").read_text())["findings"]}


@pytest.mark.parametrize(("grade", "source_ids", "assertion_ids", "summary", "gaps", "expected"), [
    ("A", ["src-map"], ["negative-modern"], "Evidence", [], None),
    ("B", ["src-map"], [], "Reconstructed", [], "UNDOCUMENTED_GRADE_GAP"),
    ("B", ["src-map"], [], "Reconstructed", ["Generalized"], "UNCERTIFIED_B_GRADE"),
    ("C", ["src-map"], [], "Scaffolded", [], "UNDOCUMENTED_GRADE_GAP"),
    ("U", ["src-map"], [], "Claim", [], "U_GRADE_CERTIFICATION_CLAIM"),
    ("U", [], [], "", [], None),
])
def test_coverage_grade_evidence_rules(tmp_path, grade, source_ids, assertion_ids, summary, gaps, expected):
    _make_pass(tmp_path)
    coverage = json.loads((tmp_path / "coverage.json").read_text())
    row = coverage["coverage"][0]
    row.update(grade=grade, source_ids=source_ids, assertion_ids=assertion_ids, evidence_summary=summary, known_gaps=gaps)
    _write(tmp_path / "coverage.json", coverage); _rehash(tmp_path, "coverage_matrix")
    result = run_start_date_qa(pass_dir=tmp_path)
    codes = {item["code"] for item in json.loads((tmp_path / "start_date_qa.json").read_text())["findings"]}
    if expected:
        assert not result.passed and expected in codes
    else:
        assert result.passed


def test_malformed_artifact_and_internal_symlink_fail_closed(tmp_path):
    _make_pass(tmp_path)
    (tmp_path / "source_manifest.json").write_text("{broken", encoding="utf-8")
    _rehash(tmp_path, "source_manifest")
    result = run_start_date_qa(pass_dir=tmp_path)
    assert not result.passed
    assert "INVALID_ARTIFACT" in {item["code"] for item in json.loads((tmp_path / "start_date_qa.json").read_text())["findings"]}

    other = tmp_path / "real-dossier.md"; other.write_text("content", encoding="utf-8")
    (tmp_path / "dossier.md").unlink(); (tmp_path / "dossier.md").symlink_to(other)
    _rehash(tmp_path, "dossier")
    result = run_start_date_qa(pass_dir=tmp_path)
    assert not result.passed
    assert "SYMLINK_ARTIFACT" in {item["code"] for item in json.loads((tmp_path / "start_date_qa.json").read_text())["findings"]}


def test_version_identity_and_revision_mismatches_are_rejected(tmp_path):
    _make_pass(tmp_path)
    build = json.loads((tmp_path / "build.geojson").read_text()); build["geometry_revision"] = "wrong"
    _write(tmp_path / "build.geojson", build); _rehash(tmp_path, "full_build_geometry")
    changelog = json.loads((tmp_path / "changelog.json").read_text()); changelog["artifact_version"] = "2"
    _write(tmp_path / "changelog.json", changelog); _rehash(tmp_path, "changelog")
    result = run_start_date_qa(pass_dir=tmp_path)
    codes = {item["code"] for item in json.loads((tmp_path / "start_date_qa.json").read_text())["findings"]}
    assert not result.passed
    assert {"GEOMETRY_REVISION_MISMATCH", "ARTIFACT_VERSION_MISMATCH"} <= codes


def test_fabric_sidecars_fail_closed_for_missing_substituted_and_unknown_locations(tmp_path):
    _make_pass(tmp_path)
    (tmp_path / "location_lineage.json").unlink()
    result = run_start_date_qa(pass_dir=tmp_path)
    codes = {item["code"] for item in json.loads((tmp_path / "start_date_qa.json").read_text())["findings"]}
    assert not result.passed and "MISSING_FABRIC_SIDECAR" in codes

    _make_pass(tmp_path)
    locations = json.loads((tmp_path / "locations.geojson").read_text())
    locations["features"][0]["properties"]["location_id"] = "substituted"
    _write(tmp_path / "locations.geojson", locations)
    result = run_start_date_qa(pass_dir=tmp_path)
    codes = {item["code"] for item in json.loads((tmp_path / "start_date_qa.json").read_text())["findings"]}
    assert not result.passed and "FABRIC_SIDECAR_CHECKSUM_MISMATCH" in codes
    _rehash_sidecar(tmp_path, "locations")
    result = run_start_date_qa(pass_dir=tmp_path)
    codes = {item["code"] for item in json.loads((tmp_path / "start_date_qa.json").read_text())["findings"]}
    assert not result.passed and {"UNKNOWN_FABRIC_LOCATION", "UNKNOWN_MEMBERSHIP_LOCATION"} <= codes


def test_fabric_lineage_membership_ids_geometry_and_full_count_are_enforced(tmp_path):
    _make_pass(tmp_path)
    assignments = json.loads((tmp_path / "assignments.json").read_text())
    assignments["targeted_split_requests"] = [{"request_id": "accepted", "location_ids": ["loc-a"], "reason": "fixture", "status": "accepted", "source_ids": ["src-map"]}]
    _write(tmp_path / "assignments.json", assignments); _rehash(tmp_path, "location_assignments")
    result = run_start_date_qa(pass_dir=tmp_path)
    codes = {item["code"] for item in json.loads((tmp_path / "start_date_qa.json").read_text())["findings"]}
    assert not result.passed and "ACCEPTED_SPLIT_WITHOUT_LINEAGE" in codes

    _make_pass(tmp_path)
    membership = (tmp_path / "province_membership.csv").read_text().replace("prv_", "bad_", 1)
    (tmp_path / "province_membership.csv").write_text(membership, encoding="utf-8")
    _rehash_sidecar(tmp_path, "province_membership")
    result = run_start_date_qa(pass_dir=tmp_path)
    codes = {item["code"] for item in json.loads((tmp_path / "start_date_qa.json").read_text())["findings"]}
    assert not result.passed and "NON_DERIVED_PROVINCE_ID" in codes

    _make_pass(tmp_path)
    build = json.loads((tmp_path / "build.geojson").read_text())
    build["features"][0]["geometry"] = _polygon(0, 0, 0.9, 1)
    _write(tmp_path / "build.geojson", build); _rehash(tmp_path, "full_build_geometry")
    result = run_start_date_qa(pass_dir=tmp_path)
    codes = {item["code"] for item in json.loads((tmp_path / "start_date_qa.json").read_text())["findings"]}
    assert not result.passed and "PROVINCE_MEMBERSHIP_GEOMETRY_MISMATCH" in codes

    _make_pass(tmp_path)
    assignments = json.loads((tmp_path / "assignments.json").read_text())
    assignments["expected_province_count"] = 22000
    _write(tmp_path / "assignments.json", assignments); _rehash(tmp_path, "location_assignments")
    result = run_start_date_qa(pass_dir=tmp_path)
    codes = {item["code"] for item in json.loads((tmp_path / "start_date_qa.json").read_text())["findings"]}
    assert not result.passed and "INCOMPLETE_FULL_BUILD" in codes


def test_positive_boundary_cannot_be_certified_from_soft_evidence(tmp_path):
    _make_pass(tmp_path)
    boundaries = json.loads((tmp_path / "boundaries.geojson").read_text())
    boundaries["features"][0]["properties"]["classification"] = "soft_evidence"
    _write(tmp_path / "boundaries.geojson", boundaries); _rehash(tmp_path, "boundary_registry")
    result = run_start_date_qa(pass_dir=tmp_path)
    codes = {item["code"] for item in json.loads((tmp_path / "start_date_qa.json").read_text())["findings"]}
    assert not result.passed and "POSITIVE_ASSERTION_USES_SOFT_EVIDENCE" in codes


def test_overlapping_province_interiors_are_rejected(tmp_path):
    _make_pass(tmp_path)
    build = json.loads((tmp_path / "build.geojson").read_text())
    build["features"][1]["geometry"] = _polygon(0.5, 0, 1.5, 1)
    _write(tmp_path / "build.geojson", build); _rehash(tmp_path, "full_build_geometry")
    result = run_start_date_qa(pass_dir=tmp_path)
    report = json.loads((tmp_path / "start_date_qa.json").read_text())
    assert not result.passed
    assert any(item["code"] == "INVALID_ARTIFACT" and "overlap" in item["message"] for item in report["findings"])


def test_schema_rejects_duplicate_ids_boundary_sides_and_unsupported_relation(tmp_path):
    _make_pass(tmp_path)
    assignments = json.loads((tmp_path / "assignments.json").read_text())
    assignments["assignments"][1]["assignment_id"] = "assignment-a"
    with pytest.raises(SchemaValidationError): validate_location_assignments(assignments)
    boundaries = json.loads((tmp_path / "boundaries.geojson").read_text())
    boundaries["features"][0]["properties"]["side_polity_ids"]["right"] = "fra"
    with pytest.raises(SchemaValidationError): validate_historical_boundary_registry(boundaries)
    golden = json.loads((tmp_path / "golden.json").read_text())
    golden["assertions"][0]["spatial_relation"] = "trust_me"
    with pytest.raises(SchemaValidationError): validate_spatial_golden_borders(golden)
