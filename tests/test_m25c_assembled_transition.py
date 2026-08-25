from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace

import pytest

from gpm.qa.m25c_assembled import (
    ASSEMBLED_VERSION,
    REGION_014_GRADE_C_CHANGE_IDS,
    REGION_014_GRADE_C_GAPS,
    qualify_assembled_pass,
)
from gpm.qa import m25c_assembled
from gpm.qa import start_date as start_date_qa
from gpm.schemas import WORLDWIDE_M49_SUBREGIONS

ROOT = Path(__file__).resolve().parents[1]


def _script_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, str):
        path.write_text(value, encoding="utf-8")
    else:
        path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _assembled_fixture(root: Path) -> list[dict]:
    regions = sorted(WORLDWIDE_M49_SUBREGIONS)
    province_ids = [f"p{i:05d}" for i in range(22_000)]
    locations = [f"l{i:05d}" for i in range(23_582)]
    members = {province_id: [] for province_id in province_ids}
    for index, location_id in enumerate(locations):
        members[province_ids[index % len(province_ids)]].append(location_id)
    assignments = [
        {"province_id": province_id, "region_id": regions[index % 22],
         "location_ids": members[province_id]}
        for index, province_id in enumerate(province_ids)
    ]
    sidecars = {
        "fabric_manifest": "sidecars/location_fabric_manifest.json",
        "locations": "sidecars/locations.geojson",
        "lineage": "sidecars/location_lineage.json",
        "province_membership": "sidecars/province_membership.csv",
        "aggregation_manifest": "sidecars/aggregation_manifest.json",
        "adjacency": "sidecars/adjacency.csv",
    }
    for role, relative in sidecars.items():
        value = (
            {"generator_version": ASSEMBLED_VERSION, "qa_mode": "certification_review", "provisional": False}
            if role == "aggregation_manifest" else {"role": role}
        )
        _write(root / relative, value)
    assignment_document = {
        "artifact_version": ASSEMBLED_VERSION,
        "assignments": assignments,
        "fabric_sidecars": {
            role: {"path": sidecars[role], "sha256": _hash(root / sidecars[role])}
            for role in ("fabric_manifest", "locations", "lineage", "province_membership")
        },
        "release_sidecars": {
            role: {"path": sidecars[role], "sha256": _hash(root / sidecars[role])}
            for role in ("aggregation_manifest", "adjacency")
        },
    }
    coverage = [
        {"region_id": region, "layer": layer, "grade": "A", "known_gaps": [], "exclusions": []}
        for region in regions
        for layer in ("geometry", "politics", "hierarchy", "gazetteer_relationships")
    ]
    grade_c_row = next(
        row for row in coverage
        if (row["region_id"], row["layer"]) == ("014", "geometry")
    )
    grade_c_row["grade"] = "C"
    grade_c_row["known_gaps"] = list(REGION_014_GRADE_C_GAPS)
    documents = {
        "source_manifest.json": {"sources": []},
        "boundaries.geojson": {"features": []},
        "gazetteer.json": {"polities": []},
        "assignments.json": assignment_document,
        "golden.json": {"assertions": []},
        "build.geojson": {"features": []},
        "coverage.json": {"coverage": coverage, "known_gaps": [], "exclusions": []},
        "changelog.json": {"changes": [
            {"change_id": change_id} for change_id in REGION_014_GRADE_C_CHANGE_IDS
        ]},
        "historical-territory-status.json": {
            "qa_mode": "certification_review", "provisional": False,
            "components": [{"provisional": False} for _ in province_ids],
            "provinces": [{"provisional": False} for _ in province_ids],
        },
        "positive-border-applicability.json": {"records": []},
        "world_coverage_mask.geojson": {
            "features": [{"properties": {"location_id": value}} for value in locations],
        },
        "anomaly_inventory.json": {"anomalies": []},
        "anomaly_census_review_ledger.json": {"entries": []},
    }
    for name, document in documents.items():
        document["artifact_version"] = ASSEMBLED_VERSION
        _write(root / name, document)
    _write(root / "dossier.md", "# Assembled evidence\n")
    _write(root / "candidate_status.json", {
        "status": "assembled_pending_research_qa",
        "review_acceptance_allowed": False, "certification_allowed": False,
        "runtime_publication_allowed": False, "public_release_allowed": False,
    })
    packets = []
    for region in regions:
        packets.append({
            "region_id": region,
            "assignment_overrides": [
                {"province_id": row["province_id"]}
                for row in assignments if row["region_id"] == region
            ],
        })
    return packets


def test_assembled_qualifier_accepts_exact_world_closure(tmp_path):
    packets = _assembled_fixture(tmp_path)
    qualify_assembled_pass(tmp_path, packets=packets)


@pytest.mark.parametrize("mutation,match", [
    ("missing_packet", "exactly one packet"),
    ("duplicate_override", "exactly one override"),
    ("coverage_gap", "reviewed region 014 Grade C"),
    ("mixed_mode", "mixed QA modes"),
    ("provisional_flag", "explicitly reject provisional"),
    ("sentinel", "provisional source lineage"),
])
def test_assembled_qualifier_fails_closed(tmp_path, mutation, match):
    packets = _assembled_fixture(tmp_path)
    if mutation == "missing_packet":
        packets.pop()
    elif mutation == "duplicate_override":
        packets[0]["assignment_overrides"].append(packets[1]["assignment_overrides"][0])
    elif mutation == "coverage_gap":
        document = json.loads((tmp_path / "coverage.json").read_text())
        document["coverage"][0]["known_gaps"] = ["gap"]
        _write(tmp_path / "coverage.json", document)
    elif mutation == "mixed_mode":
        aggregation = json.loads((tmp_path / "sidecars/aggregation_manifest.json").read_text())
        aggregation["qa_mode"] = "provisional_internal_review"
        _write(tmp_path / "sidecars/aggregation_manifest.json", aggregation)
        assignments = json.loads((tmp_path / "assignments.json").read_text())
        assignments["release_sidecars"]["aggregation_manifest"]["sha256"] = _hash(tmp_path / "sidecars/aggregation_manifest.json")
        _write(tmp_path / "assignments.json", assignments)
    elif mutation == "provisional_flag":
        canonical = json.loads((tmp_path / "historical-territory-status.json").read_text())
        canonical["components"][0]["provisional"] = True
        _write(tmp_path / "historical-territory-status.json", canonical)
    else:
        source = json.loads((tmp_path / "source_manifest.json").read_text())
        source["note"] = "official-1444-modern-scaffold-provisional"
        _write(tmp_path / "source_manifest.json", source)
    with pytest.raises(ValueError, match=match):
        qualify_assembled_pass(tmp_path, packets=packets)


def test_assembled_qualifier_rejects_sidecar_path_escape_and_symlink(tmp_path):
    packets = _assembled_fixture(tmp_path)
    assignments_path = tmp_path / "assignments.json"
    assignments = json.loads(assignments_path.read_text())
    assignments["fabric_sidecars"]["locations"]["path"] = "../outside.json"
    _write(assignments_path, assignments)
    with pytest.raises(ValueError, match="escapes"):
        qualify_assembled_pass(tmp_path, packets=packets)

    assignments["fabric_sidecars"]["locations"]["path"] = "sidecars/locations-link.json"
    target = tmp_path / "sidecars/locations.geojson"
    link = tmp_path / "sidecars/locations-link.json"
    link.symlink_to(target)
    assignments["fabric_sidecars"]["locations"]["sha256"] = _hash(target)
    _write(assignments_path, assignments)
    with pytest.raises(ValueError, match="may not contain symlinks"):
        qualify_assembled_pass(tmp_path, packets=packets)


def test_transactional_promotion_restores_previous_output_on_swap_failure(tmp_path, monkeypatch):
    generator = _script_module("m25c_generator_transaction", "generate-m25c-provisional-pass.py")
    target, staging = tmp_path / "candidate", tmp_path / "staging"
    target.mkdir()
    staging.mkdir()
    (target / "marker").write_text("old")
    (staging / "marker").write_text("new")
    real_replace = generator.os.replace
    calls = 0

    def failing_replace(source, destination):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected swap failure")
        return real_replace(source, destination)

    monkeypatch.setattr(generator.os, "replace", failing_replace)
    with pytest.raises(OSError, match="injected"):
        generator._promote_directory(staging, target)
    assert (target / "marker").read_text() == "old"


def test_generator_defaults_safe_and_requires_explicit_assembled_inputs(monkeypatch):
    generator = _script_module("m25c_generator_cli", "generate-m25c-provisional-pass.py")
    captured = []
    monkeypatch.setattr(generator, "generate", lambda args: captured.append(args))
    monkeypatch.setattr(sys, "argv", ["generate-m25c-provisional-pass.py"])
    assert generator.main() == 0
    assert captured[0].assembly_mode == "provisional"
    assert captured[0].output_dir == generator.DEFAULT_OUTPUT

    monkeypatch.setattr(sys, "argv", [
        "generate-m25c-provisional-pass.py", "--assembly-mode", "assembled-pass",
    ])
    with pytest.raises(SystemExit):
        generator.main()


def test_accepted_fabric_binding_rejects_tampering(tmp_path, monkeypatch):
    values = {
        "location_fabric_manifest.json": json.dumps({"actual_location_count": 30_216}),
        "location_lineage.json": "{}",
        "province_membership.csv": "province_id,location_id,piece_id\np,l,whole\n",
        "location_adjacency.csv": "from_location_id,to_location_id\nl1,l2\n",
        "locations.geojson": "{}",
    }
    for name, value in values.items():
        (tmp_path / name).write_text(value)
    monkeypatch.setattr(m25c_assembled, "ACCEPTED_FABRIC_SHA256", {
        name: _hash(tmp_path / name) for name in values
    })
    m25c_assembled.qualify_fabric_sidecars(tmp_path)
    (tmp_path / "location_lineage.json").write_text('{"tampered":true}')
    with pytest.raises(ValueError, match="checksum changed"):
        m25c_assembled.qualify_fabric_sidecars(tmp_path)


def test_preflight_updates_only_the_informational_review_permission(tmp_path, monkeypatch):
    builder = _script_module("m25c_builder_preflight", "build-m25c-global-pass.py")
    failed = SimpleNamespace(passed=False, error_count=4, to_dict=lambda: {"status": "fail"})
    monkeypatch.setattr(builder, "run_start_date_qa", lambda **kwargs: failed)
    with pytest.raises(SystemExit, match="4 non-review"):
        builder.stage_preflight(Namespace(output_dir=tmp_path))
    status = json.loads((tmp_path / "candidate_status.json").read_text())
    assert status["status"] == "assembled_pending_research_qa"
    assert not any(status[key] for key in (
        "review_acceptance_allowed", "certification_allowed",
        "runtime_publication_allowed", "public_release_allowed",
    ))

    clean = SimpleNamespace(passed=True, error_count=0, to_dict=lambda: {"status": "pass"})
    monkeypatch.setattr(builder, "run_start_date_qa", lambda **kwargs: clean)
    builder.stage_preflight(Namespace(output_dir=tmp_path))
    status = json.loads((tmp_path / "candidate_status.json").read_text())
    assert status["status"] == "pending_independent_review"
    assert status["review_acceptance_allowed"] is True
    assert status["certification_allowed"] is False


def test_accept_review_recomputes_qa_before_mutating_review_bytes(tmp_path, monkeypatch):
    builder = _script_module("m25c_builder_acceptance", "build-m25c-global-pass.py")
    manifest = {
        "qa_mode": "certification_review",
        "review": {"generator": "gpm qa render", "status": "pending_independent_review"},
    }
    review = {
        "generator": "gpm qa render", "reviewer": "pending-independent-review",
        "status": "pending_independent_review", "renders": [],
    }
    _write(tmp_path / "pass_manifest.json", manifest)
    _write(tmp_path / "review/review_manifest.json", review)
    before_manifest = (tmp_path / "pass_manifest.json").read_bytes()
    before_review = (tmp_path / "review/review_manifest.json").read_bytes()
    monkeypatch.setattr(builder, "_verify_review_bundle", lambda *args: None)
    failed = SimpleNamespace(passed=False, error_count=54)
    monkeypatch.setattr(builder, "run_start_date_qa", lambda **kwargs: failed)
    with pytest.raises(SystemExit, match="54 non-review"):
        builder.stage_accept_review(Namespace(
            output_dir=tmp_path, reviewer="Independent Human", review_date="2026-08-22",
        ))
    assert (tmp_path / "pass_manifest.json").read_bytes() == before_manifest
    assert (tmp_path / "review/review_manifest.json").read_bytes() == before_review


def test_generic_assembly_cannot_relabel_provisional_artifacts(tmp_path, monkeypatch):
    packets = _assembled_fixture(tmp_path)
    assert packets
    canonical_path = tmp_path / "historical-territory-status.json"
    canonical = json.loads(canonical_path.read_text())
    canonical["qa_mode"] = "provisional_internal_review"
    canonical["provisional"] = True
    _write(canonical_path, canonical)
    original_manifest = b'{"qa_mode":"provisional_internal_review"}\n'
    (tmp_path / "pass_manifest.json").write_bytes(original_manifest)
    builder = _script_module("m25c_builder_assembly", "build-m25c-global-pass.py")
    monkeypatch.setattr(builder, "_require_resolved_inventory", lambda output: None)
    with pytest.raises(SystemExit, match="assembly qualification rejected"):
        builder.stage_assembly(Namespace(output_dir=tmp_path))
    assert (tmp_path / "pass_manifest.json").read_bytes() == original_manifest


def test_ordinary_qa_independently_rejects_mixed_provisional_lineage(tmp_path):
    aggregation = tmp_path / "aggregation.json"
    _write(aggregation, {
        "qa_mode": "provisional_internal_review", "provisional": True,
        "generator_version": "1.0.0-provisional.1",
    })
    documents = {
        "canonical_historical_status": {
            "qa_mode": "provisional_internal_review", "provisional": True,
            "artifact_version": "1.0.0-provisional.1",
            "components": [{"provisional": True}], "provinces": [{"provisional": True}],
        },
        "location_assignments": {
            "release_sidecars": {"aggregation_manifest": {"path": "aggregation.json"}},
        },
        "source_manifest": {"note": "official-1444-modern-scaffold-provisional"},
    }
    findings = []
    start_date_qa._check_m25c_certification_lineage(
        tmp_path, {"artifact_version": ASSEMBLED_VERSION, "artifacts": {}}, documents, findings,
    )
    assert {row["code"] for row in findings} == {
        "MIXED_QA_MODE", "PROVISIONAL_LINEAGE", "MIXED_ARTIFACT_VERSION",
        "PROVISIONAL_SOURCE_LINEAGE",
    }
