import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "research/start-dates/1444-global-v1/replacement-evidence/exact-source-v1"
PRIOR = ROOT / "research/start-dates/1444-global-v1/replacement-evidence/actor-component-specific-v1"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_hash(value):
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def record_hash(record):
    return canonical_hash({key: value for key, value in record.items() if key != "record_sha256"})


def test_exact_source_packet_is_hash_bound_and_covers_the_frozen_rejected_surface():
    manifest = load(PACKET / "manifest.json")
    actors = load(PACKET / "actor-citation-evidence.json")["records"]
    components = load(PACKET / "component-line-evidence.json")["records"]
    pairs = load(PACKET / "pair-evidence.json")["records"]
    routes = load(PACKET / "finding-submissions.json")["records"]

    assert manifest["totals"] == {
        "actors": 107,
        "actors_with_complete_named_driver_binding": 32,
        "audited_sources": 8,
        "components": 206,
        "components_with_driver_intersection": 74,
        "driver_features": 584,
        "finding_routes": 32,
        "pairs": 180,
        "pairs_with_complete_named_driver_binding": 53,
        "qualifying_exact_date_records": 0,
    }
    assert {row["actor_id"] for row in actors} == {
        row["actor_id"] for row in load(PRIOR / "actor-specific-evidence.json")["records"]
    }
    assert {row["component_id"] for row in components} == {
        row["component_id"] for row in load(PRIOR / "component-specific-evidence.json")["records"]
    }
    assert {row["pair_id"] for row in pairs} == {
        row["pair_id"] for row in load(PRIOR / "pair-specific-evidence.json")["records"]
    }
    assert {(row["region_id"], row["finding_code"]) for row in routes} == {
        (row["region_id"], row["finding_code"])
        for row in load(PRIOR / "finding-routes.json")["records"]
    }

    for records in (actors, components, pairs, routes):
        assert all(row["record_sha256"] == record_hash(row) for row in records)
    for artifact in manifest["artifacts"]:
        data = (PACKET / artifact["path"]).read_bytes()
        assert len(data) == artifact["bytes"]
        assert hashlib.sha256(data).hexdigest() == artifact["sha256"]


def test_new_sources_remain_fail_closed_at_the_exact_date_and_line_gates():
    registry = load(PACKET / "source-registry.json")
    audit = load(PACKET / "source-audit.json")
    actors = load(PACKET / "actor-citation-evidence.json")["records"]
    components = load(PACKET / "component-line-evidence.json")["records"]
    pairs = load(PACKET / "pair-evidence.json")["records"]
    routes = load(PACKET / "finding-submissions.json")["records"]

    assert registry["sources"] == [
        {key: value for key, value in row.items() if key != "record_sha256"}
        for row in audit["records"]
    ]
    assert all(row["record_sha256"] == record_hash(row) for row in audit["records"])
    assert all(source["exact_locator"] for source in registry["sources"])
    assert all(not source["target_date_qualified"] for source in registry["sources"])
    assert all(not row["exact_actor_identity_claim_obtained"] for row in actors)
    assert all(not row["exact_target_date_claim_obtained"] for row in actors)
    assert all(not row["exact_date_component_source_obtained"] for row in components)
    assert all(not row["independently_derived_line_obtained"] for row in components)
    assert all(not row["exact_target_date_pair_claim_obtained"] for row in pairs)
    assert all(not row["independent_shared_line_obtained"] for row in pairs)
    assert all(row["qualifying_record_count"] == 0 for row in routes)
    assert all(row["submission_status"] == "not_submitted_no_qualifying_exact_source" for row in routes)


def test_driver_measurements_pin_named_features_without_erasing_source_limits():
    manifest = load(PACKET / "manifest.json")
    components = load(PACKET / "component-line-evidence.json")["records"]
    measured = [row for row in components if row["driver_measurement"]]
    intersecting = [row for row in measured if row["driver_measurement"]["intersections"]]

    assert {row["path"]: row["sha256"] for row in manifest["driver_source_files"]} == {
        "driver.cpg": "3ad3031f5503a4404af825262ee8232cc04d4ea6683d42c5dd0a2f2a27ac9824",
        "driver.dbf": "9da7f53ef3be120ad360e8859430f7cfedf6c347942d0035f8ee6a94aab073f5",
        "driver.prj": "196efbc101bdf96bb8f05e963169714226001a34667d8ad3ac3473d1761e3d1e",
        "driver.shp": "1339480bd5cdb2b92bd5729578e5704e929b95d634a144f701b7571effe49356",
        "driver.shx": "6eca93e3f92d9dfe7bfc271d6bfc3b0c792bc4f627c5144f3be98846dc69c431",
    }
    assert measured
    assert len(intersecting) == 74
    assert all(0 < row["driver_measurement"]["coverage_ratio"] <= 1 for row in intersecting)
    assert all(
        feature["name"] and feature["feature_sha256"]
        for row in intersecting
        for feature in row["driver_measurement"]["intersections"]
    )
    assert all(row["qualification"] == "retain_rejected" for row in intersecting)


def test_generator_refuses_to_overwrite_without_the_pinned_driver_source():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/generate-m25c-exact-source-evidence.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "--driver-base" in result.stderr
    assert "required" in result.stderr
