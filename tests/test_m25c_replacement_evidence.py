import hashlib
import json
from pathlib import Path

from shapely.geometry import shape

from gpm.schemas import validate_positive_border_applicability


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "research/start-dates/1444-global-v1/replacement-evidence/cliopatria-v0.2.0"
ASSEMBLED = ROOT / "data/processed/m25c-assembled-pass"
REGIONS = {
    "005", "011", "013", "014", "015", "017", "018", "021", "029",
    "030", "034", "035", "039", "053", "054", "061", "143", "145",
}


def _load(relative: str):
    return json.loads((EVIDENCE / relative).read_text())


def test_replacement_evidence_accounts_for_frozen_blockers_without_advancing_task_17():
    manifest = _load("manifest.json")
    assert manifest["candidate_mutated"] is False
    assert manifest["accounting"] == {
        "frozen_error_count": 56,
        "regions_with_errors": 18,
        "direct_border_candidates": 8,
        "applicability_audits": 10,
        "regional_dossiers": 18,
        "task_17_advanced": False,
    }
    dossiers = [_load(f"regions/{region_id}.json") for region_id in sorted(REGIONS)]
    assert sum(len(row["frozen_findings"]) for row in dossiers) == 56
    assert {row["region_id"] for row in dossiers} == REGIONS
    assert all(row["status"] == "pending_independent_review" for row in dossiers)


def test_cliopatria_snapshot_and_direct_borders_are_date_valid_and_geometry_independent():
    source = _load("cliopatria-1444.geojson")
    assert len(source["features"]) == 144
    assert all(
        feature["properties"]["FromYear"] <= 1444 <= feature["properties"]["ToYear"]
        for feature in source["features"]
    )
    source_polities = {
        feature["properties"]["Name"]: feature
        for feature in source["features"]
        if feature["properties"]["Type"] == "POLITY"
    }
    borders = _load("direct-border-candidates.geojson")["features"]
    assert len(borders) == 8
    assert {row["properties"]["region_id"] for row in borders} == {
        "014", "015", "030", "034", "035", "039", "143", "145",
    }
    for feature in borders:
        geometry = shape(feature["geometry"])
        props = feature["properties"]
        assert geometry.is_valid and not geometry.is_empty and geometry.length > 0
        assert geometry.geom_type in {"LineString", "MultiLineString"}
        assert props["start_date"] == "1444-11-11"
        assert props["derivation"].startswith("exact shared polygon-boundary intersection")
        assert props["review_status"] == "pending_independent_review"
        left = shape(source_polities[props["left_source_polity"]]["geometry"])
        right = shape(source_polities[props["right_source_polity"]]["geometry"])
        assert geometry.equals(left.boundary.intersection(right.boundary))


def test_applicability_candidates_are_schema_valid_hash_bound_and_unsigned():
    document = _load("applicability-review-candidates.json")
    validate_positive_border_applicability(document)
    records = {row["region_id"]: row for row in document["records"]}
    assert set(records) == {"005", "011", "013", "017", "018", "021", "029", "053", "054", "061"}
    assert records["061"]["reason"] == "no_land_adjacency"
    assert records["061"]["eligible_land_adjacent_actor_pairs"] == []
    assert all(records[region_id]["eligible_land_adjacent_actor_pairs"] for region_id in set(records) - {"061"})
    for record in records.values():
        review = record["independent_review"]
        unsigned = {key: value for key, value in record.items() if key != "independent_review"}
        encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        assert review == {
            "status": "pending_independent_review",
            "reviewer": "pending-independent-review",
            "reviewed_at": None,
            "record_sha256": hashlib.sha256(encoded).hexdigest(),
        }


def test_manifest_pins_every_generated_artifact_and_frozen_input():
    manifest = _load("manifest.json")
    for relative, record in manifest["frozen_inputs"].items():
        path = ASSEMBLED / relative
        assert path.stat().st_size == record["bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"]
    for record in manifest["artifacts"].values():
        path = EVIDENCE / record["path"]
        assert path.stat().st_size == record["bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"]
    for region_id, record in manifest["region_artifacts"].items():
        assert region_id in REGIONS
        path = EVIDENCE / record["path"]
        assert path.stat().st_size == record["bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"]
