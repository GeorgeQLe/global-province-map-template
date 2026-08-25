import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "research/start-dates/1444-global-v1/replacement-evidence/synthetic-actor-model-revision-v1"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_hash(value):
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def record_hash(record):
    return canonical_hash({key: value for key, value in record.items() if key != "record_sha256"})


def test_named_actor_revision_is_hash_bound_and_scoped_to_three_pairs():
    manifest = load(PACKET / "manifest.json")
    revision = load(PACKET / "chorotega-model-revision.json")
    actor = revision["actor_revision"]
    pairs = revision["incident_pair_revisions"]

    assert manifest["totals"] == {
        "named_actor_revisions": 1,
        "incident_components": 1,
        "incident_pairs": 3,
        "exact_date_actor_polygons_obtained": 0,
        "independent_shared_lines_obtained": 0,
        "implementation_changes": 0,
        "immediate_qa_change": 0,
    }
    assert actor["actor_id"] == "scenario-chorotega-polities"
    assert actor["component_ids"] == ["cmp-prv_4839d93e9052a93c9eff"]
    assert {row["pair_id"] for row in pairs} == {
        "pair-033c8c56f58879850c13",
        "pair-6ccc8630a36792a6b485",
        "pair-bb3626368adadb263232",
    }
    assert actor["record_sha256"] == record_hash(actor)
    assert all(row["record_sha256"] == record_hash(row) for row in pairs)
    assert any(
        row["path"] == "scripts/generate-m25c-region-013-packet.py"
        for row in manifest["frozen_inputs"]
    )
    for artifact in manifest["artifacts"]:
        path = PACKET / artifact["path"]
        assert path.stat().st_size == artifact["bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == artifact["sha256"]


def test_revision_removes_false_polity_semantics_without_promoting_geometry():
    revision = load(PACKET / "chorotega-model-revision.json")
    actor = revision["actor_revision"]
    proposed = actor["proposed_model"]

    assert actor["current_model"]["actor_kind"] == "polity"
    assert actor["current_model"]["generator_dispatch"].startswith("Natural Earth NIC")
    assert {row["name"] for row in actor["named_later_source_features"]} == {
        "Matagalpa", "Silam", "Ulva", "Yosco", "Maribichicoa",
    }
    assert proposed == {
        "replacement_actor_id": "scenario-northern-nicaragua-community-fabric-unresolved",
        "name": "Northern Nicaraguan community fabric (1444 identity unresolved)",
        "actor_kind": "community",
        "relationship": "territorial_presence",
        "certainty": "uncertain",
        "authority_facet": "unknown",
        "sovereign_polity_id": None,
        "owner_polity_id": None,
        "controller_polity_id": None,
        "hard_border_eligible": False,
    }
    assert all(not row["independent_shared_line_obtained"] for row in revision["incident_pair_revisions"])
    assert all(row["implementation_status"] == "not_implemented_pending_reviewer_decision" for row in revision["incident_pair_revisions"])
    assert actor["implementation_status"] == "not_implemented_pending_reviewer_decision"


def test_generator_reproduces_the_committed_packet():
    before = {path.name: path.read_bytes() for path in PACKET.glob("*.json")}
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/generate-m25c-synthetic-actor-model-revision.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    after = {path.name: path.read_bytes() for path in PACKET.glob("*.json")}

    assert result.returncode == 0, result.stderr
    assert before == after
