from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "research/start-dates/1444-global-v1/replacement-evidence/actor-component-specific-v1"
PRIOR = ROOT / "research/start-dates/1444-global-v1/replacement-evidence/best-reasonable-v1"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record_sha256(record: dict) -> str:
    payload = {key: value for key, value in record.items() if key != "record_sha256"}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


def test_manifest_pins_inputs_and_outputs():
    manifest = load(PACKET / "manifest.json")
    assert manifest["status"] == "research complete; pending independent review; not implemented"
    assert manifest["totals"]["rejected_finding_routes"] == 32
    assert manifest["totals"]["rejected_pair_records"] == 180
    assert manifest["totals"]["affected_actor_records"] == 107
    assert manifest["totals"]["actors_with_any_source_coverage"] == 8
    assert manifest["totals"]["actor_evidence_classes"] == {
        "minor_source_overlap": 6,
        "outside_source_polity_coverage": 99,
        "partial_or_multiple_source_zones": 2,
    }
    assert manifest["totals"]["rejected_component_records"] == 206
    for row in manifest["frozen_inputs"]:
        assert sha256(ROOT / row["path"]) == row["sha256"]
    for row in manifest["artifacts"]:
        path = PACKET / row["path"]
        assert path.stat().st_size == row["bytes"]
        assert sha256(path) == row["sha256"]


def test_component_records_are_exact_rejected_surface_and_full_geometry():
    decisions = load(PRIOR / "review-decisions.json")
    expected = {row["component_id"] for row in decisions["component_decisions"] if row["decision"] == "reject"}
    records = load(PACKET / "component-specific-evidence.json")["records"]
    assert {row["component_id"] for row in records} == expected
    assert all(row["measurement_method"] == "full component polygon intersection with spherical geodesic area" for row in records)
    assert all(0 <= row["coverage_ratio"] <= 1 for row in records)
    assert all(row["review_status"] == "pending_independent_review" for row in records)
    assert all(row["record_sha256"] == record_sha256(row) for row in records)


def test_actor_and_pair_records_bind_exact_current_ids():
    pair_decisions = load(PRIOR / "review-decisions.json")["pair_decisions"]
    expected_pairs = {row["pair_id"] for row in pair_decisions if row["decision"] == "reject"}
    pairs = load(PACKET / "pair-specific-evidence.json")["records"]
    actors = load(PACKET / "actor-specific-evidence.json")["records"]
    actor_ids = {row["actor_id"] for row in actors}
    assert {row["pair_id"] for row in pairs} == expected_pairs
    assert all(row["left_actor_id"] in actor_ids and row["right_actor_id"] in actor_ids for row in pairs)
    assert all(row["record_sha256"] == record_sha256(row) for row in pairs + actors)
    assert all(row["identity_assessment"] == "not_established_by_geometry" for row in actors)


def test_routes_preserve_fail_closed_review_boundary():
    records = load(PACKET / "finding-routes.json")["records"]
    assert len(records) == 32
    assert Counter(row["finding_code"] for row in records) == {
        "MISSING_POSITIVE_BORDER_ASSERTION": 9,
        "BORDER_APPLICABILITY_NOT_QUALIFIED": 3,
        "NON_EXECUTABLE_SEAM_ASSERTION": 4,
        "SPATIAL_ASSERTION_FAILED": 8,
        "UNCERTIFIED_A_GRADE": 8,
    }
    assert all(row["implementation_status"] == "not_implemented" for row in records)
    assert all(row["review_status"] == "pending_independent_review" for row in records)
    assert all(row["record_sha256"] == record_sha256(row) for row in records)
