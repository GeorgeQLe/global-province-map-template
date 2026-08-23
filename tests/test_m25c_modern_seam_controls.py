from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
from shapely.geometry import LineString, shape

from gpm.qa.start_date import (
    _canonical_json_hash,
    _check_positive_border_applicability,
    _execute_assertions,
)
from gpm.schemas import (
    SchemaValidationError,
    validate_historical_boundary_registry,
    validate_spatial_golden_borders,
)


ROOT = Path(__file__).resolve().parents[1]
PACKETS = ROOT / "research/start-dates/1444-global-v1/regional-packets"
ASIA_EUROPE_COUNTS = {
    "030": {"assertions": 21, "sources": 10, "derived_files": 1},
    "034": {"assertions": 53, "sources": 10, "derived_files": 1},
    "035": {"assertions": 57, "sources": 8, "derived_files": 1},
    "039": {"assertions": 29, "sources": 19, "derived_files": 1},
    "143": {"assertions": 17, "sources": 8, "derived_files": 1},
    "145": {"assertions": 29, "sources": 12, "derived_files": 1},
}
ITALY_SLOVENIA_CORRIDOR_COMPONENTS = {
    "prv_4135770ab968f38bca67", "prv_1b8a54b0c098d8c2cf09",
    "prv_24db15d5ae130c8a28f3", "prv_124f2c3c7427e9b49fc8",
    "prv_7ee3d24c2bcf29c026f3", "prv_09be1f2b49e888579cb7",
    "prv_134894c766f1b126146b", "prv_23535148c54f1b807d57",
    "prv_f45f86dd0797a2cb63f4",
}


def _control_module():
    path = ROOT / "scripts/m25c_negative_controls.py"
    spec = importlib.util.spec_from_file_location("m25c_negative_controls_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _polygon(x0: float, x1: float) -> dict:
    return {"type": "Polygon", "coordinates": [[[x0, 0], [x1, 0], [x1, 1], [x0, 1], [x0, 0]]]}


def _golden() -> dict:
    return {"assertions": [{
        "assertion_id": "region-r-negative-modern-test-seam",
        "region_id": "r", "layer": "geometry", "assertion_type": "seam",
        "expectation": "negative_anachronism", "subject_ids": ["r"],
        "boundary_feature_ids": ["modern-seam"],
        "spatial_relation": "regional_status_boundary_matches_forbidden_modern_seam_ratio_lte",
        "unit": "ratio", "tolerance": 0.2,
        "measurement_parameters": {"corridor_km": 75}, "notes": "Synthetic seam.",
    }]}


def _canonical(*, facet_transition: bool, actor_transition: bool, nullable: bool = True) -> dict:
    facets = {"habitability": "habitable", "population_presence": "resident", "settlement_pattern": "dispersed", "tenure": "customary_community", "authority": "local_decentralized"}
    right_facets = {**facets, "settlement_pattern": "mobile"} if facet_transition else facets
    owner = None if nullable else "compatibility-owner"
    statuses = []
    if actor_transition:
        statuses = [
            {"subject_id": "c1", "relationship": "territorial_presence", "actor_political_unit_id": "actor-a", "valid_from": "1400-01-01", "valid_to": "1500-01-01", "evidence_ids": ["e"]},
            {"subject_id": "c2", "relationship": "territorial_presence", "actor_political_unit_id": "actor-b", "valid_from": "1400-01-01", "valid_to": "1500-01-01", "evidence_ids": ["e"]},
        ]
    return {
        "components": [
            {"territory_component_id": "c1", "province_id": "p1", "political_unit_id": owner, "facets": facets, "evidence_ids": ["e"], "geometry": _polygon(0, 1)},
            {"territory_component_id": "c2", "province_id": "p2", "political_unit_id": owner, "facets": right_facets, "evidence_ids": ["e"], "geometry": _polygon(1, 2)},
        ],
        "statuses": statuses,
    }


def _execute(reference: LineString, canonical: dict) -> dict:
    findings = []
    results = _execute_assertions(
        _golden(), {}, {"modern-seam": {"geometry": reference.__geo_interface__}}, findings,
        canonical=canonical,
        assignments={"assignments": [{"province_id": "p1", "region_id": "r"}, {"province_id": "p2", "region_id": "r"}]},
        start_date="1444-11-11",
    )
    assert len(results) == 1
    return results[0]


@pytest.mark.parametrize(("facet_transition", "actor_transition"), [(True, False), (False, True)])
def test_seam_detects_facet_only_and_actor_only_transitions_with_nullable_owners(facet_transition, actor_transition):
    result = _execute(LineString([(1, 0), (1, 1)]), _canonical(facet_transition=facet_transition, actor_transition=actor_transition))
    assert result["status"] == "fail"
    assert result["measurement"] == pytest.approx(1.0)
    assert result["transition_count"] == 1
    assert result["affected_component_ids"] == ["c1", "c2"]


def test_seam_pass_zero_length_fail_closed_and_diagnostics_are_deterministic():
    canonical = _canonical(facet_transition=True, actor_transition=False)
    first = _execute(LineString([(1, 0), (1, 1)]), canonical)
    second = _execute(LineString([(1, 0), (1, 1)]), copy.deepcopy(canonical))
    assert first == second
    assert first["status"] == "fail" and first["measurement"] == pytest.approx(1.0)
    assert first["executable"] is True and first["coverage_ratio"] == pytest.approx(1.0)
    zero = _execute(LineString([(1, 0), (1, 0)]), canonical)
    assert zero["status"] == "fail" and zero["measurement"] is None
    assert zero["reference_length_km"] == 0


def test_seam_with_covered_zero_transitions_is_executable_and_passes():
    findings = []
    args = (
        _golden(), {}, {"modern-seam": {"geometry": LineString([(1, 0), (1, 1)]).__geo_interface__}},
    )
    kwargs = {
        "canonical": _canonical(facet_transition=False, actor_transition=False),
        "assignments": {"assignments": [
            {"province_id": "p1", "region_id": "r"},
            {"province_id": "p2", "region_id": "r"},
        ]}, "start_date": "1444-11-11",
    }
    results = _execute_assertions(*args, findings, **kwargs)
    repeated_findings = []
    repeated = _execute_assertions(*copy.deepcopy(args), repeated_findings, **copy.deepcopy(kwargs))
    assert (results, findings) == (repeated, repeated_findings)
    assert results[0]["status"] == "pass"
    assert results[0]["measurement"] == 0
    assert results[0]["executable"] is True
    assert results[0]["transition_count"] == 0
    assert results[0]["affected_component_ids"] == []
    assert findings == []


def test_seam_with_uncovered_or_unknown_coverage_fails_closed():
    uncovered = _execute(
        LineString([(4, 0), (4, 1)]),
        _canonical(facet_transition=False, actor_transition=False),
    )
    assert uncovered["status"] == "fail" and uncovered["measurement"] is None
    assert uncovered["coverage_ratio"] == 0
    unknown = _canonical(facet_transition=False, actor_transition=False)
    unknown["components"][0]["facets"] = {
        **unknown["components"][0]["facets"], "authority": "unknown",
    }
    result = _execute(LineString([(1, 0), (1, 1)]), unknown)
    assert result["status"] == "fail" and result["measurement"] is None
    assert result["eligibility_rejection_reasons"] == {"unknown_required_facet": ["c1"]}


def test_seam_rejects_non_line_reference_geometry():
    findings = []
    result = _execute_assertions(
        _golden(), {}, {"modern-seam": {"geometry": _polygon(1, 2)}}, findings,
        canonical=_canonical(facet_transition=True, actor_transition=False),
        assignments={"assignments": [{"province_id": "p1", "region_id": "r"}, {"province_id": "p2", "region_id": "r"}]},
        start_date="1444-11-11",
    )[0]
    assert result["status"] == "fail" and result["measurement"] == 1
    assert {row["code"] for row in findings} >= {"INVALID_SEAM_REFERENCE_GEOMETRY", "SPATIAL_ASSERTION_FAILED"}


def test_border_applicability_requires_exact_hashes_capital_anchor_and_review():
    source = {"source_id": "e", "review_status": "reviewed"}
    unsigned = {
        "region_id": "r", "start_date": "1444-11-11", "status": "not_applicable",
        "reason": "no_land_adjacency", "fabric_revision": "fabric-r1",
        "geometry_revision": "geometry-r1", "component_inventory": ["c1"],
        "component_inventory_sha256": _canonical_json_hash(["c1"]),
        "source_ids": ["e"], "source_sha256": {"e": _canonical_json_hash(source)},
        "hard_anchor_assertion_ids": ["anchor"], "eligible_land_adjacent_actor_pairs": [],
        "determination": "No land adjacency.",
    }
    record = unsigned | {"independent_review": {
        "status": "accepted", "reviewer": "independent-reviewer",
        "reviewed_at": "2026-08-23", "record_sha256": _canonical_json_hash(unsigned),
    }}
    document = {"records": [record]}
    manifest = {
        "start_date": "1444-11-11", "fabric_revision": "fabric-r1",
        "geometry_revision": "geometry-r1",
    }
    documents = {
        "canonical_historical_status": {"components": [{
            "territory_component_id": "c1", "province_id": "p1",
        }]},
        "location_assignments": {"assignments": [{"province_id": "p1", "region_id": "r"}]},
        "golden_borders": {"assertions": [{
            "assertion_id": "anchor", "region_id": "r", "layer": "geometry",
            "expectation": "positive", "assertion_type": "capital",
        }]},
    }
    findings, results = [], []
    qualified = _check_positive_border_applicability(
        document, manifest, documents, {"e": source},
        {"anchor": {"status": "pass"}}, findings, results,
    )
    assert qualified == {"r"} and findings == [] and results[0]["status"] == "pass"

    tampered = copy.deepcopy(document)
    tampered["records"][0]["hard_anchor_assertion_ids"] = ["changed-after-review"]
    findings, results = [], []
    assert _check_positive_border_applicability(
        tampered, manifest, documents, {"e": source},
        {"anchor": {"status": "pass"}}, findings, results,
    ) == set()
    assert results[0]["status"] == "fail"
    assert findings[0]["code"] == "BORDER_APPLICABILITY_NOT_QUALIFIED"
    assert "record_hash_mismatch" in findings[0]["message"]


def test_schema_030_seam_contract_is_exact():
    assertion = _golden()["assertions"][0] | {
        "tolerance_policy": {"fixed_before_measurement": True, "source_derived_tolerance": 0.2, "source_ids": ["ne"]},
    }
    document = {"schema_version": "0.3.0", "document_type": "spatial_golden_borders", "artifact_version": "3", "pass_id": "p", "start_date": "1444-11-11", "assertions": [assertion]}
    validate_spatial_golden_borders(document)
    for mutation, match in (
        (("measurement_parameters", {"corridor_km": 76}), "corridor_km"),
        (("subject_ids", ["not-r"]), "region_id"),
        (("assertion_type", "outline"), "contract"),
    ):
        broken = copy.deepcopy(document)
        broken["assertions"][0][mutation[0]] = mutation[1]
        with pytest.raises(SchemaValidationError, match=match):
            validate_spatial_golden_borders(broken)
    older = copy.deepcopy(document)
    older["schema_version"] = "0.2.0"
    older["assertions"][0].pop("tolerance_policy")
    with pytest.raises(SchemaValidationError):
        validate_spatial_golden_borders(older)


def test_nullable_historical_sides_are_limited_to_soft_modern_controls():
    props = {
        "feature_id": "modern", "geometry_revision": "natural-earth-5.1.1",
        "valid_from": "2022", "valid_to": None, "date_precision": "year",
        "semantics": "modern seam", "side_polity_ids": None,
        "reference_unit_ids": ["AAA", "BBB"], "source_ids": ["ne"],
        "license_lineage": ["Public domain"], "confidence": "high",
        "uncertainty_notes": "control", "classification": "soft_evidence",
        "geographic_scope": "r", "start_date_programs": ["1444-11-11"],
    }
    document = {"schema_version": "0.3.0", "document_type": "historical_boundary_registry", "artifact_version": "3", "pass_id": "p", "start_date": "1444-11-11", "type": "FeatureCollection", "features": [{"type": "Feature", "geometry": {"type": "LineString", "coordinates": [[0, 0], [1, 1]]}, "properties": props}]}
    validate_historical_boundary_registry(document)
    hard = copy.deepcopy(document)
    hard["features"][0]["properties"]["classification"] = "hard_constraint"
    with pytest.raises(SchemaValidationError, match="null only"):
        validate_historical_boundary_registry(hard)


def test_all_nineteen_natural_earth_controls_are_nonempty_and_packet_assets_are_pinned():
    controls = _control_module()
    assert len(controls.CONTROLS) == 19
    for region, (_left, _right, suffix) in sorted(controls.CONTROLS.items()):
        first = controls.extract_control(region)
        second = controls.extract_control(region)
        assert not first.is_empty and first.length > 0 and first.equals_exact(second, 0)
        packet_path = next(PACKETS.glob(f"{region}-*.json"))
        packet = json.loads(packet_path.read_text())
        derived = next(row for row in packet["derived_files"] if row["role"] == "negative_control_geometry")
        asset_path = packet_path.parent / derived["path"]
        assert hashlib.sha256(asset_path.read_bytes()).hexdigest() == derived["sha256"]
        boundary = next(row for row in packet["boundary_features"] if row["properties"]["feature_id"] == f"forbidden-modern-{suffix}")
        assert shape(boundary["geometry"]).equals_exact(first, 0)


def test_oceania_controls_use_the_exact_admin1_archive_and_units():
    controls = _control_module()
    assert controls.ADMIN1_CONTROLS == {"053", "054", "057", "061"}
    assert controls.NATURAL_EARTH_ADMIN1_SHA256 == hashlib.sha256(
        controls.STATES_PROVINCES.read_bytes()
    ).hexdigest()
    assert {region: controls.CONTROLS[region][:2] for region in controls.ADMIN1_CONTROLS} == {
        "053": ("AU-WA", "AU-SA"),
        "054": ("PG-CPM", "PG-NCD"),
        "057": ("NR-14", "NR-11"),
        "061": ("AS-X05~", "AS-X01~"),
    }
    for region in controls.ADMIN1_CONTROLS:
        packet_path = next(PACKETS.glob(f"{region}-*.json"))
        packet = json.loads(packet_path.read_text())
        source = next(row for row in packet["sources"] if row["source_type"] == "negative_control")
        assert source["source_id"] == f"natural-earth-admin1-5.1.1-region-{region}"
        assert source["checksum"] == controls.NATURAL_EARTH_ADMIN1_SHA256


def test_asia_europe_packet_counts_and_retired_lineage_are_exact():
    controls = _control_module()
    for region, expected in ASIA_EUROPE_COUNTS.items():
        packet_path = next(PACKETS.glob(f"{region}-*.json"))
        packet = json.loads(packet_path.read_text())
        assert {key: packet["expected_counts"][key] for key in expected} == expected
        if region == "039":
            assert not any(row["assertion_type"] == "border" for row in packet["assertions"])
            assert not any(
                row["properties"]["feature_id"] == "region-039-portugal-castile-frontier"
                for row in packet["boundary_features"]
            )
            reconstructed = {
                row["province_id"]: row for row in packet["assignment_overrides"]
                if row.get("facets", {}).get("authority") != "unknown"
            }
            assert set(reconstructed) == ITALY_SLOVENIA_CORRIDOR_COMPONENTS
            for row in reconstructed.values():
                assert row["facets"] == {
                    "authority": "shared", "habitability": "habitable",
                    "population_presence": "resident", "settlement_pattern": "mixed",
                    "tenure": "contested",
                }
                assert {
                    relationship["actor_political_unit_id"]
                    for relationship in row["status_relationships"]
                } == {"scenario-hab", "scenario-hun", "scenario-ven"}
            continue
        retirement = controls.RETIREMENTS[region]
        assert retirement["assertion_id"] not in {row["assertion_id"] for row in packet["assertions"]}
        assert retirement["boundary_id"] not in {
            row["properties"]["feature_id"] for row in packet["boundary_features"]
        }
        assert retirement["asset_ids"].isdisjoint(row["asset_id"] for row in packet["derived_files"])
        source_artifacts = {
            artifact["artifact_id"]
            for source in packet["sources"] for artifact in source.get("derived_artifacts") or []
        }
        assert retirement["artifact_ids"].isdisjoint(source_artifacts)
