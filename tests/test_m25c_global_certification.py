"""M25C additive worldwide certification contracts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from gpm.qa.certification import EraCertificationError, validate_certification_bundle
from gpm.release.demo import DemoBuildError, build_demo
from gpm.schemas import (
    SchemaValidationError, WORLDWIDE_M49_SUBREGIONS,
    validate_spatial_golden_borders, validate_start_date_pass_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
GLOBAL = ROOT / "research" / "start-dates" / "1444-global-v1"
PILOT = ROOT / "research" / "start-dates" / "1444-v2"


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
