"""M25C additive worldwide certification contracts."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from argparse import Namespace
from pathlib import Path

import pytest
from shapely.geometry import box, mapping

from gpm.geo.shapefile import ShapeFeature
from gpm.qa.certification import EraCertificationError, validate_certification_bundle
from gpm.release.demo import DemoBuildError, build_demo
from gpm.schemas import (
    SchemaValidationError, WORLDWIDE_M49_SUBREGIONS,
    validate_spatial_golden_borders, validate_start_date_pass_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
GLOBAL = ROOT / "research" / "start-dates" / "1444-global-v1"
PILOT = ROOT / "research" / "start-dates" / "1444-v2"


def _builder_module():
    path = ROOT / "scripts" / "build-m25c-global-pass.py"
    spec = importlib.util.spec_from_file_location("m25c_builder", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _artifact(path: str = "artifact.json") -> dict[str, str]:
    return {"path": path, "version": "1.0.0", "sha256": "0" * 64}


def _global_manifest() -> dict:
    roles = (
        "dossier", "source_manifest", "boundary_registry", "polity_gazetteer",
        "location_assignments", "golden_borders", "full_build_geometry",
        "coverage_matrix", "changelog", "canonical_historical_status",
        "world_coverage_mask", "anomaly_inventory",
    )
    return {
        "schema_version": "0.3.0", "document_type": "start_date_research_pass",
        "artifact_version": "1.0.0", "pass_id": "official-1444-global-v1",
        "start_date": "1444-11-11", "version": "1.0.0", "era": "late-medieval",
        "fabric_revision": "1444-global-r1", "geometry_revision": "1444-global-r1",
        "generated_at": "2026-07-19T00:00:00Z",
        "scope": {
            "kind": "worldwide", "regions": sorted(WORLDWIDE_M49_SUBREGIONS),
            "priority_regions": sorted(WORLDWIDE_M49_SUBREGIONS),
            "layers": ["geometry", "politics", "hierarchy", "gazetteer_relationships"],
            "world_coverage_mask_sha256": "0" * 64,
            "partition": {"standard": "UN M49", "revision": "2026-07-19",
                          "antarctica": "excluded-not-in-playable-fabric",
                          "subregions": sorted(WORLDWIDE_M49_SUBREGIONS)},
        },
        "artifacts": {role: _artifact(f"{role}.json") for role in roles},
        "review": {"manifest_path": "review/review_manifest.json", "sha256": "0" * 64,
                   "generator": "gpm qa render", "reviewer": "independent-reviewer", "status": "accepted"},
    }


def test_global_schema_is_additive_and_pins_the_exact_world_partition():
    validate_start_date_pass_manifest(_global_manifest())
    invalid = _global_manifest()
    invalid["scope"]["regions"].pop()
    invalid["scope"]["partition"]["subregions"] = invalid["scope"]["regions"]
    invalid["scope"]["priority_regions"] = invalid["scope"]["regions"]
    with pytest.raises(SchemaValidationError, match="pinned 22-part"):
        validate_start_date_pass_manifest(invalid)


def test_global_manifest_may_encode_pending_review_for_preflight_only():
    manifest = _global_manifest()
    manifest["review"].update({
        "reviewer": "pending-independent-review",
        "status": "pending_independent_review",
    })
    validate_start_date_pass_manifest(manifest)
    manifest["schema_version"] = "0.2.0"
    with pytest.raises(SchemaValidationError, match="must be accepted"):
        validate_start_date_pass_manifest(manifest)


def test_m49_enrichment_is_deterministic_and_marks_antarctica(monkeypatch):
    builder = _builder_module()
    countries = [
        ShapeFeature(mapping(box(0, 0, 2, 2)), {"SUBREGION": "Western Europe"}),
        ShapeFeature(mapping(box(2, 0, 4, 2)), {"SUBREGION": "Eastern Europe"}),
        ShapeFeature(mapping(box(0, -80, 4, -60)), {"SUBREGION": "Antarctica"}),
    ]
    monkeypatch.setattr(builder, "read_zipped_shapefile", lambda _path: countries)
    fabric = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"location_id": "west"}, "geometry": mapping(box(0, 0, 1, 1))},
        {"type": "Feature", "properties": {"location_id": "east"}, "geometry": mapping(box(3, 0, 4, 1))},
        {"type": "Feature", "properties": {"location_id": "south"}, "geometry": mapping(box(1, -70, 2, -69))},
    ]}
    result = builder.enrich_m49(fabric, Path("unused.zip"))
    assert [row["properties"]["m49_subregion"] for row in result["features"]] == ["151", "Antarctica", "155"]
    assert all("m49_subregion" not in row["properties"] for row in fabric["features"])


def test_resolved_inventory_rejects_placeholder_subjects_and_sources():
    builder = _builder_module()
    inventory = json.loads((GLOBAL / "anomaly_inventory.json").read_text())
    for row in inventory["anomalies"]:
        row["resolution"] = "resolved"
    with pytest.raises(SystemExit, match="placeholders="):
        builder._validate_inventory(inventory)
    for index, row in enumerate(inventory["anomalies"]):
        row["subject_ids"] = [f"polity-{index}"]
        row["source_ids"] = [f"source-{index}"]
    builder._validate_inventory(inventory)


def test_evidence_rejection_is_aggregated_and_copies_no_invalid_inputs(tmp_path):
    builder = _builder_module()
    evidence = tmp_path / "evidence"
    output = tmp_path / "output"
    evidence.mkdir()
    (evidence / "source_manifest.json").write_text(json.dumps({
        "schema_version": "0.2.0", "pass_id": "wrong-pass", "start_date": "1444-11-12",
    }) + "\n")
    args = Namespace(evidence_dir=evidence, output_dir=output)
    with pytest.raises(SystemExit, match="reviewed evidence bundle rejected"):
        builder.stage_evidence(args)
    report = json.loads((output / builder.REJECTION_REPORT).read_text())
    assert report["status"] == "reject"
    assert report["finding_count"] > 3
    assert {"artifact", "rule", "affected_ids", "remediation_owner"}.issubset(report["findings"][0])
    assert not (output / "source_manifest.json").exists()


def test_handoff_reports_all_missing_input_owners(tmp_path):
    builder = _builder_module()
    args = Namespace(
        inventory_input=None, fabric_input=None, fabric_sidecars_dir=None,
        natural_earth_input=tmp_path / "missing-ne.zip", evidence_dir=None,
    )
    findings = builder._validate_curator_handoff(args)
    assert {(row["artifact"], row["remediation_owner"]) for row in findings} == {
        ("anomaly_inventory", "historical-curator"),
        ("evidence_bundle", "historical-curator"),
        ("fabric", "fabric-curator"),
        ("fabric_sidecars", "fabric-curator"),
        ("natural_earth", "pipeline-operator"),
    }


def test_evidence_sidecar_paths_and_hashes_fail_closed(tmp_path):
    builder = _builder_module()
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    assignments = {
        "fabric_sidecars": {
            "lineage": {"path": "../lineage.json", "sha256": "0" * 64},
            "locations": {"path": "sidecars/locations.geojson", "sha256": "0" * 64},
        },
        "release_sidecars": {},
    }
    (evidence / "assignments.json").write_text(json.dumps(assignments) + "\n")
    sidecars = evidence / "sidecars"
    sidecars.mkdir()
    (sidecars / "locations.geojson").write_text("{}\n")
    findings = builder._validate_evidence_bundle(evidence)
    by_rule = {(row["artifact"], row["rule"]) for row in findings}
    assert ("fabric_sidecars:lineage", "PATH_ESCAPE") in by_rule
    assert ("fabric_sidecars:locations", "CHECKSUM_MISMATCH") in by_rule


def test_render_and_preflight_report_missing_manifest_without_traceback(tmp_path):
    builder = _builder_module()
    args = Namespace(output_dir=tmp_path)
    with pytest.raises(SystemExit, match="render rejected: Cannot read"):
        builder.stage_render(args)
    with pytest.raises(SystemExit, match="preflight rejected: Pass manifest does not exist"):
        builder.stage_preflight(args)


def test_handoff_contract_reports_count_partition_review_and_coverage_defects():
    builder = _builder_module()
    documents = {
        "source_manifest.json": {"sources": [{"source_id": "draft", "review_status": "pending"}]},
        "assignments.json": {
            "expected_province_count": 22_000,
            "assignments": [{
                "assignment_id": "a1", "province_id": "p1", "region_id": "155",
                "location_ids": ["loc1", "loc1"], "source_ids": ["draft"],
            }],
        },
        "coverage.json": {"coverage": [], "known_gaps": ["gap"], "exclusions": []},
    }
    findings = []
    builder._validate_evidence_contract(documents, findings)
    rules = {row["rule"] for row in findings}
    assert {
        "INVALID_GLOBAL_PROVINCE_COUNT", "DUPLICATE_LOCATION_ASSIGNMENT",
        "INVALID_WORLD_PARTITION", "UNREVIEWED_SOURCE_REFERENCE",
        "GLOBAL_COVERAGE_NOT_A", "GLOBAL_COVERAGE_GAPS",
    }.issubset(rules)


def test_pending_lineage_hash_pins_the_unchanged_pilot():
    provenance = json.loads((GLOBAL / "provenance" / "1444-v2-seed.json").read_text())
    actual = {
        path.relative_to(PILOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(PILOT.rglob("*")) if path.is_file()
    }
    assert provenance["promotion_prohibited"] is True
    assert provenance["files"] == actual
    assert json.loads((GLOBAL / "candidate_status.json").read_text())["public_release_allowed"] is False


def test_global_assertions_reject_tolerances_widened_after_source_lock():
    golden = json.loads((PILOT / "golden.json").read_text())
    golden["schema_version"] = "0.3.0"
    for assertion in golden["assertions"]:
        assertion["tolerance_policy"] = {
            "fixed_before_measurement": True,
            "source_derived_tolerance": assertion["tolerance"],
            "source_ids": ["reviewed-source"],
        }
    validate_spatial_golden_borders(golden)
    golden["assertions"][0]["tolerance"] += 1
    with pytest.raises(SchemaValidationError, match="not fixed"):
        validate_spatial_golden_borders(golden)


def test_certification_bundle_rejects_tampering(tmp_path):
    roles = ("research_pass", "research_qa", "canonical_historical_status", "independent_review", "runtime_manifest")
    records = {}
    for role in roles:
        path = tmp_path / f"{role}.json"
        path.write_text("{}\n")
        records[role] = {"path": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    benchmark = tmp_path / "runtime_benchmark.json"
    benchmark.write_text(json.dumps({"status": "pass", "gates": {"all": "pass"}}) + "\n")
    records["runtime_benchmark"] = {"path": benchmark.name, "sha256": hashlib.sha256(benchmark.read_bytes()).hexdigest()}
    certification = {
        "schema_version": "1.0.0", "certification_type": "gpm-global-era-certification",
        "status": "accepted", "certification_id": "official-1444-global-v1",
        "pass_id": "official-1444-global-v1", "start_date": "1444-11-11",
        "scope": "worldwide", "public_scenario_id": "official-1444",
        "compatibility_revision": "1", "artifacts": records,
        "gates": {name: "pass" for name in ("research", "world_partition", "coverage", "canonical_runtime_parity", "runtime_determinism", "runtime_performance", "independent_review")},
    }
    path = tmp_path / "certification.json"
    path.write_text(json.dumps(certification) + "\n")
    assert validate_certification_bundle(path)["status"] == "accepted"
    benchmark.write_text('{"status":"fail","gates":{}}\n')
    with pytest.raises(EraCertificationError, match="missing or altered"):
        validate_certification_bundle(path)


def test_certification_bundle_rejects_artifacts_outside_bundle(tmp_path):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_text("{}\n")
    records = {
        role: {"path": "../outside.json", "sha256": hashlib.sha256(outside.read_bytes()).hexdigest()}
        for role in (
            "research_pass", "research_qa", "canonical_historical_status",
            "independent_review", "runtime_manifest", "runtime_benchmark",
        )
    }
    certification = {
        "schema_version": "1.0.0", "certification_type": "gpm-global-era-certification",
        "status": "accepted", "certification_id": "official-1444-global-v1",
        "pass_id": "official-1444-global-v1", "start_date": "1444-11-11",
        "scope": "worldwide", "public_scenario_id": "official-1444",
        "compatibility_revision": "1", "artifacts": records,
        "gates": {name: "pass" for name in (
            "research", "world_partition", "coverage", "canonical_runtime_parity",
            "runtime_determinism", "runtime_performance", "independent_review",
        )},
    }
    path = bundle / "certification.json"
    path.write_text(json.dumps(certification) + "\n")
    with pytest.raises(EraCertificationError, match="escapes bundle directory"):
        validate_certification_bundle(path)


def test_demo_refuses_uncertified_official_1444():
    with pytest.raises(DemoBuildError, match="requires --certification-input"):
        build_demo(scenarios=("official-1444",), validate=False)
