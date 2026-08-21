from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from gpm.historical import TerritorialStatusOverlayError, resolve_territorial_status
from gpm.exporters import dissolve_territorial_owners, territorial_status_atlas_features
from gpm.runtime import RuntimePack, compile_runtime_pack
from gpm.schemas import SchemaValidationError, derive_province_facets, validate_historical_territory_status


def _canonical() -> dict:
    geometry = lambda x: {"type": "Polygon", "coordinates": [[[x, 0], [x + 1, 0], [x + 1, 1], [x, 1], [x, 0]]]}
    facets = {"habitability": "habitable", "population_presence": "resident", "settlement_pattern": "dispersed", "tenure": "customary_community", "authority": "local_decentralized", "x-game:movement": "open"}
    return {
        "schema_version": "0.2.0", "compatibility_revision": "2", "start_date": "1444-11-11", "scenario_id": "base",
        "components": [
            {"territory_component_id": "c1", "political_unit_id": None, "province_id": "p1", "geometry": geometry(0), "facets": facets, "historically_required": True, "minimum_area_merge_exempt": True, "evidence_ids": ["s"]},
            {"territory_component_id": "c2", "political_unit_id": None, "province_id": "p1", "geometry": geometry(1), "facets": {**facets, "settlement_pattern": "mobile"}, "historically_required": True, "minimum_area_merge_exempt": True, "evidence_ids": ["s"]},
        ],
        "political_units": [{"political_unit_id": "community-a", "actor_kind": "community", "territory_component_ids": [], "documented_status": "documented community presence"}],
        "provinces": [{"province_id": "p1", "territory_component_ids": ["c1", "c2"]}],
        "statuses": [{"subject_id": "c1", "relationship": "territorial_presence", "actor_political_unit_id": "community-a", "valid_from": "1400-01-01", "valid_to": "1500-01-01", "evidence_ids": ["s"], "certainty": "documented"}],
    }


def _overlay(*operations: dict, revision: str = "2", scenario: str = "custom") -> dict:
    return {"schema_version": "0.1.0", "document_type": "territorial_status_overlay", "overlay_id": scenario, "scenario_id": scenario, "base_compatibility_revision": revision, "provenance": {"source_ids": ["s"]}, "operations": list(operations)}


def test_v2_facets_nullable_actors_extensions_and_province_derivation():
    document = _canonical()
    validate_historical_territory_status(document)
    facets = derive_province_facets(document)["p1"]
    assert facets["settlement_pattern"] == "mixed"
    assert facets["x-game:movement"] == "open"
    broken = copy.deepcopy(document)
    del broken["components"][0]["facets"]["authority"]
    with pytest.raises(SchemaValidationError):
        validate_historical_territory_status(broken)


def test_uninhabited_components_reject_synthetic_actors():
    document = _canonical()
    component = document["components"][0]
    component["facets"] = {"habitability": "uninhabitable", "population_presence": "none", "settlement_pattern": "none", "tenure": "none", "authority": "none"}
    with pytest.raises(SchemaValidationError, match="synthetic territorial actor"):
        validate_historical_territory_status(document)


def test_overlay_order_province_expansion_component_specificity_and_fail_closed():
    document = _canonical()
    resolved = resolve_territorial_status(document, [_overlay(
        {"op": "set_facet", "target_kind": "component", "target_id": "c2", "dimension": "settlement_pattern", "value": "mobile"},
        {"op": "set_facet", "target_kind": "province", "target_id": "p1", "dimension": "settlement_pattern", "value": "nucleated"},
    )])
    values = {row["territory_component_id"]: row["facets"]["settlement_pattern"] for row in resolved["components"]}
    assert values == {"c1": "nucleated", "c2": "mobile"}
    later = resolve_territorial_status(resolved, [_overlay({"op": "set_facet", "target_kind": "province", "target_id": "p1", "dimension": "settlement_pattern", "value": "semi_mobile"}, scenario="later")])
    assert {row["facets"]["settlement_pattern"] for row in later["components"]} == {"semi_mobile"}
    with pytest.raises(TerritorialStatusOverlayError, match="revision"):
        resolve_territorial_status(document, [_overlay({"op": "set_facet", "target_kind": "component", "target_id": "c1", "dimension": "authority", "value": "unknown"}, revision="stale")])
    with pytest.raises(TerritorialStatusOverlayError, match="unknown component"):
        resolve_territorial_status(document, [_overlay({"op": "set_facet", "target_kind": "component", "target_id": "missing", "dimension": "authority", "value": "unknown"})])


def test_overlay_relationship_exact_remove_and_runtime_v2_round_trip(tmp_path: Path):
    document = _canonical()
    relation = {key: value for key, value in document["statuses"][0].items() if key != "subject_id"}
    removed = resolve_territorial_status(document, [_overlay({"op": "remove_relationship", "target_kind": "component", "target_id": "c1", "relationship": relation})])
    assert removed["statuses"] == []
    with pytest.raises(TerritorialStatusOverlayError, match="exactly one"):
        resolve_territorial_status(removed, [_overlay({"op": "remove_relationship", "target_kind": "component", "target_id": "c1", "relationship": relation})])
    source = tmp_path / "canonical.json"
    source.write_text(json.dumps(document), encoding="utf-8")
    compile_runtime_pack(source, tmp_path / "runtime", compatibility_revision="2", max_zoom=0)
    runtime = RuntimePack(tmp_path / "runtime")
    assert runtime.manifest["schema_version"] == "2.0.0"
    assert runtime.scenario_facets()[0]["facets"]["x-game:movement"] == "open"
    state = runtime.resolved_territory_state()
    assert state["components"][0]["owner"] is None
    assert state["provinces"][0]["facets"]["settlement_pattern"] == "mixed"


def test_worldwide_packets_have_exact_compositional_coverage():
    root = Path(__file__).resolve().parents[1] / "research" / "start-dates" / "1444-global-v1" / "regional-packets"
    packets = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(root.glob("*.json"))]
    assignments = [row for packet in packets for row in packet["assignment_overrides"]]
    assert len(packets) == 22
    assert len(assignments) == 22_000
    locations = json.loads((root.parent / "world_coverage_mask.geojson").read_text(encoding="utf-8"))["features"]
    assert len(locations) == 23_582
    assert len({row["province_id"] for row in assignments}) == 22_000
    assert all(set(row["facets"]) >= {"habitability", "population_presence", "settlement_pattern", "tenure", "authority"} for row in assignments)
    uninhabited = [row for row in assignments if row["facets"]["habitability"] == "uninhabitable"]
    assert len(uninhabited) == 219
    assert all(not any(row.get(key) for key in ("polity_ids", "sovereign_polity_id", "owner_polity_id", "controller_polity_id", "status_relationships")) for row in uninhabited)
    assert not any("uninhabited" in polity["polity_id"] for packet in packets for polity in packet["polities"])


def test_atlas_uses_neutral_unowned_style_facets_and_overlay_ownership():
    document = _canonical()
    features = territorial_status_atlas_features(document)
    assert all(feature["properties"]["owner"] is None for feature in features)
    assert all(feature["properties"]["owner_color"] == "#8a8a8a" for feature in features)
    assert features[0]["properties"]["habitability"] == "habitable"
    assert dissolve_territorial_owners(features) == []
    relationship = {"relationship": "owner", "actor_political_unit_id": "community-a", "valid_from": "1400-01-01", "valid_to": "1500-01-01", "evidence_ids": ["s"], "certainty": "documented"}
    overlaid = territorial_status_atlas_features(document, overlays=(_overlay({"op": "upsert_relationship", "target_kind": "component", "target_id": "c1", "relationship": relationship}),))
    assert [feature["properties"]["owner"] for feature in overlaid] == ["community-a", None]
    assert len(dissolve_territorial_owners(overlaid)) == 1
