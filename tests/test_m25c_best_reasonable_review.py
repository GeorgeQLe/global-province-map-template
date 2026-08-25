from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "research/start-dates/1444-global-v1/replacement-evidence/best-reasonable-v1"


def load(name: str):
    return json.loads((PACKET / name).read_text(encoding="utf-8"))


def canonical_hash(record: dict) -> str:
    payload = {key: value for key, value in record.items() if key != "decision_sha256"}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


def test_review_binds_every_evidence_record_and_honest_grade():
    review = load("review-decisions.json")
    pairs = load("pair-evidence.json")["records"]
    components = load("component-evidence.json")["records"]
    findings = load("finding-routes.json")["records"]
    pairs_by_id = {row["pair_id"]: row for row in pairs}
    components_by_id = {row["component_id"]: row for row in components}
    findings_by_id = {(row["region_id"], row["finding_code"]): row for row in findings}

    assert review["status"] == "reviewed; narrow Grade C acceptance; not implemented"
    for artifact in review["reviewed_artifacts"]:
        assert hashlib.sha256((PACKET / artifact["path"]).read_bytes()).hexdigest() == artifact["sha256"]
    assert {row["pair_id"] for row in review["pair_decisions"]} == {row["pair_id"] for row in pairs}
    assert {row["component_id"] for row in review["component_decisions"]} == {
        row["component_id"] for row in components
    }
    assert {
        (row["region_id"], row["finding_code"]) for row in review["finding_decisions"]
    } == {(row["region_id"], row["finding_code"]) for row in findings}
    assert all(row["decision_sha256"] == canonical_hash(row) for group in (
        review["pair_decisions"], review["component_decisions"], review["finding_decisions"]
    ) for row in group)
    assert all(
        row["evidence_record_sha256"] == pairs_by_id[row["pair_id"]]["record_sha256"]
        for row in review["pair_decisions"]
    )
    assert all(
        row["evidence_record_sha256"] == components_by_id[row["component_id"]]["record_sha256"]
        for row in review["component_decisions"]
    )
    assert all(
        row["evidence_record_sha256"]
        == findings_by_id[(row["region_id"], row["finding_code"])]["record_sha256"]
        for row in review["finding_decisions"]
    )

    assert Counter((row["decision"], row["geometry_grade"]) for row in review["pair_decisions"]) == {
        ("reject", "not_applicable"): 180,
    }
    assert Counter((row["decision"], row["geometry_grade"]) for row in review["component_decisions"]) == {
        ("accept", "C"): 306,
        ("reject", "U"): 206,
    }
    assert Counter((row["decision"], row["geometry_grade"]) for row in review["finding_decisions"]) == {
        ("accept", "C"): 11,
        ("reject", "U"): 20,
        ("reject", "not_applicable"): 12,
    }
    assert not any(row.get("geometry_grade") in {"A", "B"} for group in (
        review["pair_decisions"], review["component_decisions"], review["finding_decisions"]
    ) for row in group)


def test_component_acceptance_requires_both_named_brackets_and_no_more():
    review = load("review-decisions.json")
    evidence = {row["component_id"]: row for row in load("component-evidence.json")["records"]}
    for decision in review["component_decisions"]:
        row = evidence[decision["component_id"]]
        surfaces = row["spatial_corroboration"]
        expected = (
            surfaces["historical_basemap_1400"]["named_match_count"] > 0
            and surfaces["historical_basemap_1492"]["named_match_count"] > 0
        )
        assert (decision["decision"] == "accept") is expected
        if expected:
            assert decision["accepted_scope"] == "documented_approximate_geometry_scaffold_only"
            assert len(decision["known_gaps"]) == 4


def test_finding_acceptance_is_complete_and_component_only():
    review = load("review-decisions.json")
    accepted_components = {
        row["component_id"] for row in review["component_decisions"] if row["decision"] == "accept"
    }
    routes = {
        (row["region_id"], row["finding_code"]): row
        for row in load("finding-routes.json")["records"]
    }
    for decision in review["finding_decisions"]:
        route = routes[(decision["region_id"], decision["finding_code"])]
        expected = bool(route["component_evidence_ids"]) and all(
            component_id in accepted_components for component_id in route["component_evidence_ids"]
        )
        assert (decision["decision"] == "accept") is expected
