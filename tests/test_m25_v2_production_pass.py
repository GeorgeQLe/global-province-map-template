"""Acceptance checks for the committed `official-1444-reconstruction-v2` pass.

The large generated sidecars (`build.geojson`, `sidecars/locations.geojson`)
are pinned by SHA-256 but not committed; tests that need them skip when they
are absent so the suite stays runnable from a plain checkout. Reproduce them
with `python scripts/build-m25-v2-pass.py all`.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PASS_DIR = ROOT / "research" / "start-dates" / "1444-v2"
BIG_SIDECARS = (PASS_DIR / "build.geojson", PASS_DIR / "sidecars" / "locations.geojson")

pytestmark = pytest.mark.skipif(
    not (PASS_DIR / "pass_manifest.json").is_file(),
    reason="1444-v2 pass not assembled",
)


def _manifest() -> dict:
    return json.loads((PASS_DIR / "pass_manifest.json").read_text())


def test_v2_pass_identity_and_scope():
    manifest = _manifest()
    assert manifest["pass_id"] == "official-1444-reconstruction-v2"
    assert manifest["schema_version"] == "0.2.0"
    assert manifest["fabric_revision"] == "global-h3-v1-r2"
    assert manifest["geometry_revision"] == "1444-r2"
    assert manifest["scope"]["priority_regions"] == [
        "low-countries", "burgundy", "france", "hre", "central-europe",
    ]


def test_v2_pass_is_fail_closed_until_independently_reviewed():
    """Pre-review, the schema itself must reject the pass manifest."""
    from gpm.qa.start_date import StartDateQAError, run_start_date_qa
    from gpm.schemas import SchemaValidationError, validate_start_date_pass_manifest

    manifest = _manifest()
    if manifest["review"]["status"] == "accepted":
        pytest.skip("pass has been independently reviewed")
    with pytest.raises(SchemaValidationError):
        validate_start_date_pass_manifest(manifest)
    with pytest.raises(StartDateQAError):
        run_start_date_qa(pass_dir=PASS_DIR, report_output=Path("/tmp") / "ignored-m25v2-qa.json")


def test_v2_hard_boundaries_carry_georeferencing_and_date_valid_sources():
    boundaries = json.loads((PASS_DIR / "boundaries.geojson").read_text())
    sources = {
        item["source_id"]: item
        for item in json.loads((PASS_DIR / "source_manifest.json").read_text())["sources"]
    }
    hard = [f for f in boundaries["features"] if f["properties"]["classification"] == "hard_constraint"]
    assert len(hard) == 5
    for feature in hard:
        props = feature["properties"]
        georeferencing = props["georeferencing"]
        assert len(georeferencing["control_points"]) >= 3
        assert props["error_budget_km"] >= georeferencing["residual_error_km"]
        cited = [sources[s] for s in props["source_ids"]]
        assert any(s["source_type"] in {"academic", "primary"} for s in cited)
        groups = {
            s["independence_group"] for s in cited
            if s["source_type"] not in {"soft_corroboration", "negative_control"}
        }
        assert len(groups) >= 2


def test_v2_negative_controls_reuse_the_audit_pins():
    sources = {
        item["source_id"]: item
        for item in json.loads((PASS_DIR / "source_manifest.json").read_text())["sources"]
    }
    assert sources["geoboundaries-bel-adm1-2022"]["checksum"] == (
        "7af87f5035779f0aefe5bf930288572979e490ab0441fd9b92942a519bea0974"
    )
    assert sources["geoboundaries-fra-adm2-2022"]["checksum"] == (
        "a14ed131c86c802e5d546c7cbeccbd4daebc94a66fea413f563935a53504f251"
    )


def test_v2_split_requests_are_backed_by_r2_lineage():
    assignments = json.loads((PASS_DIR / "assignments.json").read_text())
    lineage = json.loads((PASS_DIR / "sidecars" / "location_lineage.json").read_text())
    events = {
        event["request_id"]: event
        for event in lineage["events"]
        if isinstance(event, dict) and isinstance(event.get("request_id"), str)
    }
    accepted = [r for r in assignments["targeted_split_requests"] if r["status"] == "accepted"]
    assert accepted, "the pass must carry accepted split requests with real lineage"
    for request in accepted:
        event = events[request["request_id"]]
        assert event["parent_location_ids"]
        assert set(request["location_ids"]) <= set(event["child_location_ids"])
    request_ids = {r["request_id"] for r in accepted}
    assert any("split-frontier-scheldt" in rid for rid in request_ids)
    assert any("brussels" in rid for rid in request_ids)


@pytest.mark.skipif(
    not all(path.is_file() for path in BIG_SIDECARS),
    reason="large generated sidecars not present; run scripts/build-m25-v2-pass.py",
)
def test_v2_pass_passes_every_gate_except_review(tmp_path):
    """With a test-only signature, everything but the human review must pass."""
    from gpm.qa.start_date import run_start_date_qa

    copy = tmp_path / "1444-v2"
    shutil.copytree(PASS_DIR, copy)
    review_path = copy / "review" / "review_manifest.json"
    review = json.loads(review_path.read_text())
    review["reviewer"] = "test-only-not-a-real-review"
    review["status"] = "accepted"
    review_path.write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = json.loads((copy / "pass_manifest.json").read_text())
    manifest["review"].update({
        "reviewer": "test-only-not-a-real-review",
        "status": "accepted",
    })
    import hashlib

    manifest["review"]["sha256"] = hashlib.sha256(review_path.read_bytes()).hexdigest()
    boundaries_path = copy / "boundaries.geojson"
    boundaries = json.loads(boundaries_path.read_text())
    for feature in boundaries["features"]:
        georeferencing = feature["properties"].get("georeferencing")
        if georeferencing and georeferencing["reviewer"] == "pending-independent-review":
            georeferencing["reviewer"] = "test-only-not-a-real-review"
    boundaries_path.write_text(json.dumps(boundaries, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest["artifacts"]["boundary_registry"]["sha256"] = hashlib.sha256(boundaries_path.read_bytes()).hexdigest()
    (copy / "pass_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = run_start_date_qa(pass_dir=copy)
    report = json.loads((copy / "start_date_qa.json").read_text())
    failed = [f for f in report["findings"] if f["severity"] == "error"]
    assert result.passed, f"non-review findings: {failed}"
    executed = {row["assertion_id"]: row for row in report["assertion_results"]}
    assert all(row["status"] == "pass" for row in executed.values())
    assert "negative-modern-brussels-capital-region" in executed
    assert "negative-modern-nord-department" in executed
