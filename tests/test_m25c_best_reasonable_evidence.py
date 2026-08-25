from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/start-dates/1444-global-v1/replacement-evidence"
FROZEN = BASE / "cliopatria-v0.2.0"
PACKET = BASE / "best-reasonable-v1"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record_sha256(record: dict) -> str:
    payload = {key: value for key, value in record.items() if key != "record_sha256"}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


def test_best_reasonable_manifest_and_artifact_hashes():
    manifest = load(PACKET / "manifest.json")
    assert manifest["status"] == "research complete; pending independent review; not implemented"
    assert manifest["totals"]["deferred_finding_routes"] == 43
    assert manifest["totals"]["pair_records"] == 180
    assert manifest["totals"]["component_records"] == 512
    assert manifest["totals"]["medium_confidence_pairs"] == 127
    assert manifest["totals"]["low_confidence_pairs"] == 53
    assert manifest["totals"]["medium_confidence_components"] == 312
    assert manifest["totals"]["low_confidence_components"] == 200
    assert manifest["source_records"]["openhistoricalmap"]["returned_relation_count"] == 116
    assert manifest["source_records"]["openhistoricalmap"]["usable_polygon_count"] == 113
    assert manifest["source_records"]["openhistoricalmap"]["sourced_polygon_count"] == 21
    for artifact in manifest["artifacts"]:
        path = PACKET / artifact["path"]
        assert path.stat().st_size == artifact["bytes"]
        assert sha256(path) == artifact["sha256"]
    for input_group in ("regional_packets", "regional_dossiers"):
        assert manifest["frozen_inputs"][input_group]
        for frozen_input in manifest["frozen_inputs"][input_group]:
            assert sha256(ROOT / frozen_input["path"]) == frozen_input["sha256"]


def test_pair_records_bind_every_frozen_nonzero_pair():
    frozen = load(FROZEN / "applicability-review-candidates.json")
    evidence = load(PACKET / "pair-evidence.json")["records"]
    expected = {
        (
            record["region_id"],
            pair["left_actor_id"],
            pair["right_actor_id"],
            tuple(pair["component_ids"]),
            pair["disposition"],
        )
        for record in frozen["records"]
        for pair in record["eligible_land_adjacent_actor_pairs"]
    }
    actual = {
        (
            row["region_id"],
            row["left_actor_id"],
            row["right_actor_id"],
            tuple(row["incident_component_ids"]),
            row["recommended_disposition"],
        )
        for row in evidence
    }
    assert actual == expected
    assert len({row["pair_id"] for row in evidence}) == 180
    assert all(row["review_status"] == "pending_independent_review" for row in evidence)
    assert all(row["reviewed_regional_source_ids"] for row in evidence)
    assert all(row["record_sha256"] == record_sha256(row) for row in evidence)
    assert all(
        {"feature_ids", "sourced_feature_ids"} <= set(surface)
        for row in evidence
        for surface in row["spatial_corroboration"].values()
    )
    for row in evidence:
        medium_qualified = (
            row["sourced_openhistoricalmap_component_count"] > 0
            or (
                row["spatial_corroboration"]["historical_basemap_1400"]["named_component_count"] > 0
                and row["spatial_corroboration"]["historical_basemap_1492"]["named_component_count"] > 0
            )
        )
        assert (row["confidence"] == "medium") is medium_qualified


def test_component_records_bind_every_deferred_corridor_row():
    expected = set()
    for path in sorted((FROZEN / "regions").glob("*.json")):
        dossier = load(path)
        expected.update(
            (dossier["region_id"], row["component_id"])
            for row in dossier["corridor_component_mapping"]
            if row["source_classification"] != "single_polity"
        )
    evidence = load(PACKET / "component-evidence.json")["records"]
    actual = {(row["region_id"], row["component_id"]) for row in evidence}
    assert actual == expected
    assert len(actual) == 512
    assert Counter(row["frozen_source_classification"] for row in evidence) == {
        "outside_cliopatria_polity_coverage": 509,
        "overlapping_polities": 3,
    }
    assert all(row["record_sha256"] == record_sha256(row) for row in evidence)
    assert all(row["limitations"] for row in evidence)


def test_finding_routes_cover_exact_deferred_decision_surface():
    routes = load(PACKET / "finding-routes.json")["records"]
    assert len(routes) == 43
    assert Counter(row["finding_code"] for row in routes) == {
        "MISSING_POSITIVE_BORDER_ASSERTION": 9,
        "BORDER_APPLICABILITY_NOT_QUALIFIED": 3,
        "NON_EXECUTABLE_SEAM_ASSERTION": 7,
        "SPATIAL_ASSERTION_FAILED": 12,
        "UNCERTIFIED_A_GRADE": 12,
    }
    for row in routes:
        pair_route = row["finding_code"] in {
            "MISSING_POSITIVE_BORDER_ASSERTION",
            "BORDER_APPLICABILITY_NOT_QUALIFIED",
        }
        assert bool(row["pair_evidence_ids"]) is pair_route
        assert bool(row["component_evidence_ids"]) is not pair_route
        assert row["review_status"] == "pending_independent_review"
        assert row["record_sha256"] == record_sha256(row)
