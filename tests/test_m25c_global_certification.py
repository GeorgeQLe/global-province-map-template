"""M25C additive worldwide certification contracts."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from argparse import Namespace
from pathlib import Path

import pytest
from shapely.geometry import box, mapping

from gpm.geo.shapefile import ShapeFeature
from gpm.qa.certification import EraCertificationError, certify_era, validate_certification_bundle
from gpm.release.demo import DemoBuildError, build_demo
from gpm.schemas import (
    SchemaValidationError, WORLDWIDE_M49_SUBREGIONS,
    validate_spatial_golden_borders, validate_start_date_pass_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
GLOBAL = ROOT / "research" / "start-dates" / "1444-global-v1"
PILOT = ROOT / "research" / "start-dates" / "1444-v2"

CORRECTED_DESTINATION_PAIRS = {
    "005": {
        "loc_835f12fffffffff_c5be541d90": ("prv_19e89e4eaa5dfc2e2b3a", "guiana"),
        "loc_835f12fffffffff_7d7d0ad1d6": ("prv_24997d8e705642bb38f5", "guiana"),
        "loc_83d09efffffffff_9e81297988": ("prv_310ae0921fe95823a658", "bouvet"),
        "loc_835f16fffffffff_30c99531b6": ("prv_5081bb9cdeeb7086dcfd", "guiana"),
        "loc_835f1efffffffff_a99e688aa1": ("prv_58b55f11fd5efce327a6", "guiana"),
        "loc_835f14fffffffff_2ef32b2a07": ("prv_7be0440ed5267d0d1db3", "guiana"),
        "loc_835f13fffffffff_daefe30f3d": ("prv_8eea9d15a3846e2137d9", "guiana"),
        "loc_835f33fffffffff_2a560c7111": ("prv_9aff2ceaa4e216c0cc1e", "guiana"),
        "loc_835f10fffffffff_4b6436f831": ("prv_a1149707e1319b5535a6", "guiana"),
        "loc_835f15fffffffff_ed166b3ae1": ("prv_a5171223bb3523db5c71", "guiana"),
        "loc_835f11fffffffff_341d198e42": ("prv_bed2f369053802b9bafe", "guiana"),
    },
    "014": {
        "loc_83a254fffffffff_bf97337886": ("prv_25dc8e80988576f13b94", "reunion"),
        "loc_83a304fffffffff_05539f788e": ("prv_4f169aa651ddb7613e94", "mayotte"),
        "loc_83a250fffffffff_a1a76e1ee2": ("prv_621047cd51de209ae7a6", "reunion"),
        "loc_83a304fffffffff_714c8bce3a": ("prv_8f086db76587de59188f", "mayotte"),
        "loc_83a255fffffffff_a359a377a6": ("prv_a080717eaf32dacfea49", "reunion"),
    },
    "029": {
        "loc_835e43fffffffff_7a1063e862": ("prv_17a2082ff620fff2365c", "guadeloupe"),
        "loc_835e5cfffffffff_2ab68c1e58": ("prv_2672ba4a59434e1097be", "guadeloupe"),
        "loc_835e43fffffffff_c83e1ce1da": ("prv_4a456cb955650662c02c", "guadeloupe"),
        "loc_835e4bfffffffff_7b21fd4fff": ("prv_5486a37d9e86c8d02c36", "saba"),
        "loc_835e43fffffffff_8e2598daef": ("prv_55d2a5f86e33f9a1e0f6", "guadeloupe"),
        "loc_835e46fffffffff_f74726b473": ("prv_57b4e5f40a10e9eb381e", "martinique"),
        "loc_835e5cfffffffff_15e968bfc2": ("prv_601f0e1dce2c047ff9b1", "guadeloupe"),
        "loc_835e5cfffffffff_3798bc792c": ("prv_67d747708875f2223712", "guadeloupe"),
        "loc_835e43fffffffff_483b66cd61": ("prv_6851031205ea4eed2d95", "guadeloupe"),
        "loc_835e43fffffffff_38c143e382": ("prv_7e505f8595a1e7d80118", "guadeloupe"),
        "loc_835e42fffffffff_62ba9e62fb": ("prv_7f27dae3ee89a0f66538", "martinique"),
        "loc_835e5dfffffffff_a646fd5470": ("prv_82a3457e29f98a53c095", "guadeloupe"),
        "loc_835e43fffffffff_73093ec31b": ("prv_8fea3e2c28a3f224b005", "guadeloupe"),
        "loc_835e5dfffffffff_e2b27ba088": ("prv_94e92fbb78d7fe1b97b2", "guadeloupe"),
        "loc_836744fffffffff_c1890d6cc2": ("prv_ab4cbfb4ba8ef151dae9", "bonaire"),
        "loc_835e4bfffffffff_12eb076dd3": ("prv_b31341d5fc6a20f66d8d", "st-eustatius"),
        "loc_836740fffffffff_50847f2e9c": ("prv_bb1f1984122ac5695b3b", "bonaire"),
        "loc_835e5dfffffffff_1060162a95": ("prv_bbe4b181a47cc45070b6", "guadeloupe"),
        "loc_835e5dfffffffff_2656f3ce70": ("prv_be9567c2033d1b7fee4f", "guadeloupe"),
        "loc_835e40fffffffff_dba80c9470": ("prv_c5fff292c95e2ba4f0ee", "martinique"),
        "loc_835e43fffffffff_269993ccb5": ("prv_d1eefa0b15368af256bb", "guadeloupe"),
        "loc_835e5cfffffffff_133685825d": ("prv_d4a91f94d8f3312856f3", "guadeloupe"),
        "loc_835e43fffffffff_9c67cb4923": ("prv_eef6464d5bfff220c3b2", "guadeloupe"),
        "loc_836746fffffffff_f55accb5a3": ("prv_f7a214361558b659829e", "bonaire"),
    },
}

CORRECTED_POLICIES = {
    "guiana": ("scenario-orinoco-guianas", 0.45, {
        "cnrs-guiana-precolumbian-forest", "inrap-guyane-kourou-luna1",
        "inrap-guyane-precolumbian",
    }, "French Guiana residual:"),
    "bouvet": ("scenario-uninhabited-south-atlantic-islands", 0.05,
               {"npolar-bouvet-history"}, "Bouvet residual:"),
    "mayotte": ("scenario-pre-sultanate-mayotte-communities", 0.45, {
        "culture-mayotte-archaeological-timeline", "culture-mayotte-forty-years",
        "openedition-tsingoni-mosque", "persee-mayotte-bagamoyo",
    }, "Mayotte residual:"),
    "reunion": ("scenario-uninhabited-western-indian-ocean", 0.05,
                {"culture-indian-ocean-reunion-history"}, "Reunion residual:"),
    "guadeloupe": ("scenario-kalinago-lesser-antilles", 0.45, {
        "adlfi-anse-a-la-gourde", "inrap-antilles-archaeology",
        "inrap-guadeloupe-history", "pmc-east-guadeloupe-networks",
    }, "Guadeloupe residual:"),
    "martinique": ("scenario-kalinago-lesser-antilles", 0.45, {
        "inrap-martinique-anse-bellay", "leiden-martinique-ansea-trabaud",
        "yale-martinique-later-prehistory",
    }, "Martinique residual:"),
    "saba": ("scenario-eastern-taino-communities", 0.35, {
        "leiden-precolumbian-saba-thesis", "leiden-saba-first-inhabitants",
        "springer-late-precolonial-saba-networks",
    }, "Saba residual:"),
    "st-eustatius": ("scenario-small-island-communities", 0.55, {
        "jas-st-eustatius-golden-rock", "leiden-st-eustatius-archaeology",
    }, "Sint Eustatius residual:"),
    "bonaire": ("scenario-caquetio-southern-caribbean", 0.25, {
        "royalsociety-caquetio-calibration", "tandf-bonaire-isotopes",
    }, "Bonaire residual:"),
}


def _builder_module():
    path = ROOT / "scripts" / "build-m25c-global-pass.py"
    spec = importlib.util.spec_from_file_location("m25c_builder", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _provisional_module():
    path = ROOT / "scripts" / "generate-m25c-provisional-pass.py"
    spec = importlib.util.spec_from_file_location("m25c_provisional", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _artifact(path: str = "artifact.json") -> dict[str, str]:
    return {"path": path, "version": "1.0.0", "sha256": "0" * 64}


def _global_manifest() -> dict:
    roles = (
        "dossier", "source_manifest", "boundary_registry", "polity_gazetteer",
        "location_assignments", "golden_borders", "full_build_geometry",
        "coverage_matrix", "changelog", "canonical_historical_status",
        "world_coverage_mask", "anomaly_inventory", "anomaly_review_ledger",
    )
    return {
        "schema_version": "0.3.0", "document_type": "start_date_research_pass",
        "artifact_version": "1.0.0", "pass_id": "official-1444-global-v1",
        "start_date": "1444-11-11", "version": "1.0.0", "era": "late-medieval",
        "fabric_revision": "1444-global-r1", "geometry_revision": "1444-global-r1",
        "generated_at": "2026-07-19T00:00:00Z",
        "scope": {
            "kind": "worldwide", "regions": sorted(WORLDWIDE_M49_SUBREGIONS),
            "priority_regions": sorted(WORLDWIDE_M49_SUBREGIONS),
            "layers": ["geometry", "politics", "hierarchy", "gazetteer_relationships"],
            "world_coverage_mask_sha256": "0" * 64,
            "partition": {"standard": "UN M49", "revision": "2026-07-19",
                          "antarctica": "excluded-not-in-playable-fabric",
                          "subregions": sorted(WORLDWIDE_M49_SUBREGIONS)},
        },
        "artifacts": {role: _artifact(f"{role}.json") for role in roles},
        "review": {"manifest_path": "review/review_manifest.json", "sha256": "0" * 64,
                   "generator": "gpm qa render", "reviewer": "independent-reviewer", "status": "accepted"},
    }


def test_global_schema_is_additive_and_pins_the_exact_world_partition():
    validate_start_date_pass_manifest(_global_manifest())
    invalid = _global_manifest()
    invalid["scope"]["regions"].pop()
    invalid["scope"]["partition"]["subregions"] = invalid["scope"]["regions"]
    invalid["scope"]["priority_regions"] = invalid["scope"]["regions"]
    with pytest.raises(SchemaValidationError, match="pinned 22-part"):
        validate_start_date_pass_manifest(invalid)


def test_global_manifest_may_encode_pending_review_for_preflight_only():
    manifest = _global_manifest()
    manifest["review"].update({
        "reviewer": "pending-independent-review",
        "status": "pending_independent_review",
    })
    validate_start_date_pass_manifest(manifest)
    manifest["schema_version"] = "0.2.0"
    with pytest.raises(SchemaValidationError, match="must be accepted"):
        validate_start_date_pass_manifest(manifest)


def test_provisional_manifest_mode_is_schema_valid_but_non_promotable(tmp_path):
    manifest = _global_manifest()
    manifest["qa_mode"] = "provisional_internal_review"
    manifest["review"].update({
        "reviewer": "pending-independent-review",
        "status": "pending_independent_review",
    })
    validate_start_date_pass_manifest(manifest)

    output = tmp_path / "pass"
    review = output / "review"
    review.mkdir(parents=True)
    (output / "pass_manifest.json").write_text(json.dumps(manifest) + "\n")
    (review / "review_manifest.json").write_text(json.dumps({
        "generator": "gpm qa render", "reviewer": "pending-independent-review",
        "status": "pending_independent_review", "renders": [],
    }) + "\n")
    builder = _builder_module()
    with pytest.raises(SystemExit, match="cannot be review-accepted"):
        builder.stage_accept_review(Namespace(
            output_dir=output, reviewer="Human Reviewer", review_date="2026-08-14",
        ))
    with pytest.raises(EraCertificationError, match="never certification-eligible"):
        certify_era(pass_dir=output, runtime_dir=tmp_path / "runtime", output=tmp_path / "cert.json")


def test_provisional_membership_resplit_is_exact_and_deterministic():
    provisional = _provisional_module()
    original = {"a": ["l1", "l2", "l3"], "b": ["l4", "l5"], "c": ["l6"]}
    left = provisional._target_groups(original, [["l1", "l2"]], 5)
    right = provisional._target_groups(original, [["l1", "l2"]], 5)
    assert left == right
    assert len(left) == 5
    assert sorted(item for group in left for item in group) == [f"l{i}" for i in range(1, 7)]
    assert ["l1", "l2"] in left


def test_approved_polity_source_cleanup_is_exact_and_fail_closed():
    provisional = _provisional_module()
    source_id = provisional.PROVISIONAL_SOURCE_ID
    reviewed_ids = provisional.APPROVED_REVIEWED_SCAFFOLD_POLITIES
    pruned_ids = provisional.APPROVED_PRUNED_SCAFFOLD_POLITIES
    assert len(reviewed_ids) == 71
    assert len(pruned_ids) == 127
    assert reviewed_ids.isdisjoint(pruned_ids)

    sources = {"sources": [
        {"source_id": source_id, "review_status": "planned"},
        {"source_id": "reviewed", "review_status": "reviewed"},
    ]}
    gazetteer = {"polities": [
        *[
            {"polity_id": polity_id, "source_ids": [source_id, "reviewed"],
             "relationships": []}
            for polity_id in sorted(reviewed_ids)
        ],
        *[
            {"polity_id": polity_id, "source_ids": [source_id], "relationships": []}
            for polity_id in sorted(pruned_ids)
        ],
        *[
            {"polity_id": f"reviewed-owner-{polity_id}", "source_ids": ["reviewed"],
             "relationships": []}
            for polity_id in provisional.APPROVED_LEGACY_CORE_COUNTS
        ],
    ]}
    boundaries = {"features": [
        {"properties": {
            "feature_id": f"provisional-boundary-{index}",
            "source_ids": [source_id], "classification": "soft_evidence",
            "confidence": "provisional", "valid_from": None, "valid_to": None,
            "side_polity_ids": {"left": "scenario-ara", "right": "scenario-ava"},
        }}
        for index in range(262)
    ]}
    golden = {"assertions": [
        {"assertion_id": assertion_id, "boundary_feature_ids": [],
         "tolerance_policy": {"source_ids": [source_id]}}
        for assertion_id in sorted(provisional.APPROVED_REDUNDANT_PILOT_ASSERTIONS)
    ]}
    assignments = {"assignments": [
        {
            "assignment_id": f"assignment-{polity_id}-{index}",
            "polity_ids": [f"reviewed-owner-{polity_id}"],
            "core_polity_ids": [polity_id], "claim_polity_ids": [],
            "dispute_polity_ids": [],
            "sovereign_polity_id": f"reviewed-owner-{polity_id}",
            "owner_polity_id": f"reviewed-owner-{polity_id}",
            "controller_polity_id": f"reviewed-owner-{polity_id}",
        }
        for polity_id, count in provisional.APPROVED_LEGACY_CORE_COUNTS.items()
        for index in range(count)
    ]}
    coverage = {"coverage": [], "known_gaps": []}

    provisional._apply_approved_polity_source_cleanup(
        sources, gazetteer, boundaries, golden, assignments, coverage, stage="references",
    )

    assert not boundaries["features"]
    assert not golden["assertions"]
    assert all(
        row["core_polity_ids"] == [row["owner_polity_id"]]
        for row in assignments["assignments"]
    )

    provisional._apply_approved_polity_source_cleanup(
        sources, gazetteer, boundaries, golden, assignments, coverage, stage="polities",
    )

    assert {row["source_id"] for row in sources["sources"]} == {"reviewed"}
    assert not boundaries["features"]
    assert not golden["assertions"]
    assert len(gazetteer["polities"]) == 81
    assert not pruned_ids.intersection(row["polity_id"] for row in gazetteer["polities"])
    assert all(row["source_ids"] == ["reviewed"] for row in gazetteer["polities"])
    assert all(
        row["core_polity_ids"] == [row["owner_polity_id"]]
        for row in assignments["assignments"]
    )


def test_worldwide_negative_control_inventory_is_exact_and_fail_closed():
    packets = [json.loads(path.read_text()) for path in sorted((GLOBAL / "regional-packets").glob("*.json"))]
    assertions = [row for packet in packets for row in packet.get("assertions") or []]
    seams = [
        row for row in assertions
        if row["spatial_relation"] == "regional_status_boundary_matches_forbidden_modern_seam_ratio_lte"
    ]
    regions = {
        "005", "011", "013", "014", "015", "017", "018", "021", "029",
        "030", "034", "035", "039", "053", "054", "057", "061", "143", "145",
    }
    assert len(seams) == 19
    assert {row["region_id"] for row in seams} == regions
    assert all(row["tolerance"] == 0.2 and row["measurement_parameters"] == {"corridor_km": 75} for row in seams)
    assert not any(row["assertion_id"] == "region-015-border-marinid-zayyanid" for row in assertions)
    positive_border_regions = {
        row["region_id"] for row in assertions
        if row["expectation"] == "positive" and row["assertion_type"] == "border"
    }
    assert regions.isdisjoint(positive_border_regions)

    retired = {
        "030": "region-030-border-ming-oirat",
        "034": "region-034-border-bahmani-vijayanagara",
        "035": "region-035-border-ayutthaya-cambodia",
        "039": "region-039-border-portugal-castile",
        "143": "region-143-border-timurid-moghulistan",
        "145": "region-145-border-ottoman-qara-qoyunlu",
    }
    assert not {row["assertion_id"] for row in assertions}.intersection(retired.values())
    retired_artifacts = {
        "derived-region-015-marinid-zayyanid-frontier",
        "derived-region-015-polity-masks",
        "derived-region-030-ming-oirat-frontier",
        "derived-region-034-bahmani-vijayanagara-frontier",
        "derived-region-035-ayutthaya-cambodia-frontier",
        "derived-region-039-portugal-castile-frontier",
        "derived-region-039-portugal-castile-mask",
        "derived-region-143-timurid-moghulistan-frontier",
        "derived-region-145-ottoman-qara-qoyunlu-frontier",
        "derived-region-145-ottoman-qara-qoyunlu-mask",
    }
    assert retired_artifacts.isdisjoint(
        artifact["artifact_id"]
        for packet in packets for source in packet["sources"]
        for artifact in source.get("derived_artifacts") or []
    )
    for region in retired:
        packet = next(packet for packet in packets if packet["region_id"] == region)
        regional_seams = [row for row in packet["assertions"] if row["expectation"] == "negative_anachronism"]
        assert len(regional_seams) == 1
        assert not (GLOBAL / "regional-packets" / "assets" / region / "boundaries.geojson").exists()
    for region in regions:
        packet = next(packet for packet in packets if packet["region_id"] == region)
        regional_seams = [row for row in packet["assertions"] if row["expectation"] == "negative_anachronism"]
        assert len(regional_seams) == 1
    for region in {"039", "145"}:
        assert not (GLOBAL / "regional-packets" / "assets" / region / "polity-masks.geojson").exists()


def test_region_057_applicability_review_is_assembled_only_and_hash_bound(monkeypatch):
    provisional = _provisional_module()
    canonical = {"components": [{
        "territory_component_id": "component-057", "province_id": "province-057",
    }]}
    assignments = {"assignments": [{
        "province_id": "province-057", "region_id": "057", "source_ids": ["source-057"],
    }]}
    source_manifest = {"sources": [{"source_id": "source-057"}]}
    golden = {"assertions": [{
        "assertion_id": "anchor-057", "region_id": "057", "layer": "geometry",
        "expectation": "positive", "assertion_type": "capital",
    }]}
    arguments = (canonical, assignments, source_manifest, golden)
    revisions = {"fabric_revision": "fabric-r1", "geometry_revision": "geometry-r1"}

    pending = provisional._positive_border_applicability(*arguments, **revisions)
    pending_record = next(row for row in pending["records"] if row["region_id"] == "057")
    assert pending_record["independent_review"]["status"] == "pending_independent_review"

    approved_unsigned = {
        key: value for key, value in pending_record.items() if key != "independent_review"
    }
    approved_unsigned["determination"] = provisional.REGION_057_APPLICABILITY_DETERMINATION
    monkeypatch.setattr(
        provisional, "REGION_057_APPLICABILITY_RECORD_SHA256",
        provisional._hash_json(approved_unsigned),
    )
    approved = provisional._positive_border_applicability(
        *arguments, **revisions, apply_approved_reviews=True,
    )
    approved_record = next(row for row in approved["records"] if row["region_id"] == "057")
    assert approved_record["independent_review"] == {
        "status": "accepted", "reviewer": "independent-reviewers",
        "reviewed_at": "2026-08-23",
        "record_sha256": provisional._hash_json(approved_unsigned),
    }

    source_manifest["sources"][0]["changed_after_review"] = True
    with pytest.raises(SystemExit, match="new independent review required"):
        provisional._positive_border_applicability(
            *arguments, **revisions, apply_approved_reviews=True,
        )


def test_regional_packet_cannot_promote_a_weak_grade_a_claim():
    provisional = _provisional_module()
    packet = {
        "region_id": "155", "source_pins": [{"source_id": "s", "locator": "p. 1", "sha256": "0" * 64}],
        "sources": [{"source_id": "s", "review_status": "reviewed", "source_type": "academic",
                     "valid_from": "1400", "valid_to": "1500", "independence_group": "one"}],
        "coverage": [{"region_id": "155", "layer": "politics", "grade": "A",
                      "source_ids": ["s"], "known_gaps": [], "exclusions": []}],
    }
    with pytest.raises(SystemExit, match="all four regional layers"):
        provisional._qualify_grade_a_packet(packet)


@pytest.mark.parametrize(("region", "filename", "assignment_count", "correction_count"), [
    ("005", "005-south-america-2026-08-16.json", 2211, 0),
    ("011", "011-western-africa-2026-08-16.json", 641, 2),
    ("013", "013-central-america-2026-08-16.json", 605, 0),
    ("014", "014-eastern-africa-2026-08-16.json", 720, 0),
    ("015", "015-northern-africa-2026-08-16.json", 643, 0),
    ("017", "017-middle-africa-2026-08-16.json", 527, 0),
    ("018", "018-southern-africa-2026-08-16.json", 225, 0),
    ("021", "021-northern-america-2026-08-16.json", 3986, 0),
    ("029", "029-caribbean-2026-08-16.json", 396, 0),
    ("030", "030-eastern-asia-2026-08-16.json", 1941, 0),
    ("034", "034-southern-asia-2026-08-16.json", 910, 0),
    ("035", "035-south-eastern-asia-2026-08-16.json", 1759, 3),
    ("039", "039-southern-europe-2026-08-15.json", 464, 0),
    ("053", "053-australia-new-zealand-2026-08-16.json", 1199, 7),
    ("054", "054-melanesia-2026-08-16.json", 414, 0),
    ("057", "057-micronesia-2026-08-16.json", 175, 0),
    ("061", "061-polynesia-2026-08-16.json", 176, 0),
    ("143", "143-central-asia-2026-08-16.json", 310, 3),
    ("145", "145-western-asia-2026-08-15.json", 768, 0),
    ("151", "151-eastern-europe-2026-08-15.json", 2178, 0),
    ("154", "154-northern-europe-2026-08-15.json", 1367, 1),
    ("155", "155-western-europe-2026-08-15.json", 385, 39),
])
def test_completed_region_grade_a_packets(region, filename, assignment_count, correction_count):
    provisional = _provisional_module()
    packet_path = GLOBAL / "regional-packets" / filename
    packet = json.loads(packet_path.read_text())

    provisional._qualify_grade_a_packet(packet, packet_path)

    assert packet["region_id"] == region
    assert packet["start_date"] == "1444-11-11"
    assert packet["visual_review"] == "accepted"
    assert len(packet["visual_review_artifact"]["sha256"]) == 64
    assert {row["layer"] for row in packet["coverage"]} == set(provisional.LAYERS)
    assert all(row["grade"] == "A" and not row["known_gaps"] and not row["exclusions"]
               for row in packet["coverage"])
    assert len(packet["assignment_overrides"]) == assignment_count
    assert len({row["province_id"] for row in packet["assignment_overrides"]}) == assignment_count
    assert all("official-1444-modern-scaffold-provisional" not in row["source_ids"]
               for row in packet["assignment_overrides"])
    assert len(packet["location_region_overrides"]) == correction_count
    if packet.get("packet_version") == "2.0.0":
        profiles = {row["polity_id"]: row for row in packet["polities"]}
        assert all(row.get("actor_kind") for row in profiles.values())
        assert not any("uninhabited" in polity_id for polity_id in profiles)
        for row in packet["assignment_overrides"]:
            assert set(row["facets"]) == {"habitability", "population_presence", "settlement_pattern", "tenure", "authority"}
            relationship_actors = {item["actor_political_unit_id"] for item in row["status_relationships"]}
            assert relationship_actors <= set(profiles)
            if row["facets"]["habitability"] == "uninhabitable":
                assert not row["polity_ids"] and not relationship_actors
                assert row["owner_polity_id"] is row["controller_polity_id"] is row["sovereign_polity_id"] is None
        return
    if region == "005":
        assert packet["expected_counts"] == {
            "assertions": 32, "assignments": 2211, "build_features": 8,
            "derived_files": 0, "m49_corrections": 0, "polities": 15,
            "sources": 13,
        }
        assert packet["visual_review_artifact"]["sha256"] == (
            "2d08b4d7d5c4dd84377f1c87d42151ab734f7758ea97eb2604c4c8ceb9702ede"
        )
        actors = {row["owner_polity_id"] for row in packet["assignment_overrides"]}
        assert not actors.intersection({"scenario-flk", "scenario-nah"})
        assert {"scenario-inca-cusco", "scenario-chimor", "scenario-aymara-kingdoms",
                "scenario-muisca-chiefdoms", "scenario-tairona-chiefdoms",
                "scenario-amazonian-riverine", "scenario-mapuche-communities",
                "scenario-uninhabited-south-atlantic-islands"}.issubset(actors)
    elif region == "011":
        assert packet["expected_counts"] == {
            "assertions": 32, "assignments": 641, "build_features": 8,
            "derived_files": 0, "m49_corrections": 2, "polities": 15,
            "sources": 8,
        }
        assert packet["visual_review_artifact"]["sha256"] == (
            "b799182c56dbec98d6d45f31bd8ce7380697f3c66745502fc94c8247677c4150"
        )
        actors = {row["owner_polity_id"] for row in packet["assignment_overrides"]}
        assert not actors.intersection({
            "scenario-mal", "scenario-son", "scenario-mrt", "scenario-oyo",
            "scenario-civ", "scenario-gnb", "scenario-cpv", "scenario-sle",
            "scenario-lbr", "scenario-ben", "scenario-tgo", "scenario-shn",
            "scenario-gmb", "scenario-sah",
        })
        assert {"scenario-mali-empire-decline", "scenario-tuareg-niger-bend",
                "scenario-songhai-kingdom", "scenario-jolof-senegambia",
                "scenario-mossi-kingdoms", "scenario-akan-states",
                "scenario-hausa-city-states", "scenario-yoruba-polities",
                "scenario-benin-kingdom", "scenario-uninhabited-atlantic-islands"}.issubset(actors)
        assert {target: sum(row["region_id"] == target for row in packet["location_region_overrides"])
                for target in {"015", "017"}} == {"015": 1, "017": 1}
    elif region == "013":
        assert packet["expected_counts"] == {
            "assertions": 48, "assignments": 605, "build_features": 12,
            "derived_files": 0, "m49_corrections": 0, "polities": 25,
            "sources": 11,
        }
        assert packet["visual_review_artifact"]["sha256"] == (
            "621f1de5a6712a1491b27087985fef2bce966d209e3c7a02a285f2311fe87871"
        )
        actors = {row["owner_polity_id"] for row in packet["assignment_overrides"]}
        assert not actors.intersection({"scenario-nah", "scenario-clp"})
        assert {"scenario-mexica-triple-alliance", "scenario-tlaxcalan-confederation",
                "scenario-purepecha-state", "scenario-yucatan-successor-polities",
                "scenario-peten-belize-maya", "scenario-kiche-state",
                "scenario-pipil-cuzcatlan", "scenario-lenca-polities",
                "scenario-nicarao-polities", "scenario-diquis-chiefdoms",
                "scenario-cocle-parita-chiefdoms",
                "scenario-uninhabited-east-pacific-islands"}.issubset(actors)
    elif region == "014":
        assert packet["expected_counts"] == {
            "assertions": 32, "assignments": 720, "build_features": 8,
            "derived_files": 0, "m49_corrections": 0, "polities": 14,
            "sources": 14,
        }
        assert packet["visual_review_artifact"]["sha256"] == (
            "98a51a9d5a934c4b969d886cd99797aeb970ad7fe958ed50b5eb42c46fc720c2"
        )
        actors = {row["owner_polity_id"] for row in packet["assignment_overrides"]}
        assert not actors.intersection({
            "scenario-eth", "scenario-tza", "scenario-moz", "scenario-unk",
            "scenario-som", "scenario-sds", "scenario-zmb", "scenario-ken",
        })
        assert {"scenario-solomonic-ethiopia", "scenario-adal-sultanate",
                "scenario-ajuran-somali", "scenario-great-lakes-kingdoms",
                "scenario-kilwa-swahili-network", "scenario-great-zimbabwe-transition",
                "scenario-malagasy-communities",
                "scenario-uninhabited-western-indian-ocean",
                "scenario-pre-sultanate-mayotte-communities"}.issubset(actors)
        mayotte = {row["polity_id"]: row for row in packet["polities"]}[
            "scenario-pre-sultanate-mayotte-communities"
        ]
        assert mayotte == {
            "aliases": [], "capital_location_ids": [],
            "name": "Pre-sultanate Mayotte communities",
            "polity_id": "scenario-pre-sultanate-mayotte-communities",
            "relationships": [],
            "source_ids": [
                "culture-mayotte-archaeological-timeline",
                "culture-mayotte-forty-years", "openedition-tsingoni-mosque",
                "persee-mayotte-bagamoyo",
            ],
            "valid_from": "1400", "valid_to": "1500",
        }
    elif region == "015":
        assert packet["expected_counts"] == {
            "assertions": 25, "assignments": 643, "build_features": 6,
            "derived_files": 2, "m49_corrections": 0, "polities": 9,
            "sources": 10,
        }
        assert packet["visual_review_artifact"]["sha256"] == (
            "19ba39121d02d71d9c2e9dd58b269bc91339eb23c53ab69a879361ba87b7ec05"
        )
        names = {row["polity_id"]: row["name"] for row in packet["polities"]}
        assert names["scenario-mor"].startswith("Marinid Sultanate")
        assert {"scenario-dongola", "scenario-alodia"}.issubset(names)
    elif region == "017":
        assert packet["expected_counts"] == {
            "assertions": 32, "assignments": 527, "build_features": 8,
            "derived_files": 0, "m49_corrections": 0, "polities": 13,
            "sources": 8,
        }
        assert packet["visual_review_artifact"]["sha256"] == (
            "71817c27b493b111209610d2c2bd709e4873be8b2d110053ab1fe876282175ae"
        )
        actors = {row["owner_polity_id"] for row in packet["assignment_overrides"]}
        assert not actors.intersection({
            "scenario-caf", "scenario-gab", "scenario-gnq", "scenario-kan",
            "scenario-kon", "scenario-stp",
        })
        assert {"scenario-kongo-kingdom", "scenario-kanem-bornu",
                "scenario-sao-lake-chad", "scenario-tio-anziku-polities",
                "scenario-mbundu-polities", "scenario-cameroon-grassfields",
                "scenario-equatorial-forest-communities",
                "scenario-ubangian-communities", "scenario-upemba-polities",
                "scenario-uninhabited-gulf-guinea-islands"}.issubset(actors)
    elif region == "021":
        assert packet["expected_counts"] == {
            "assertions": 32, "assignments": 3986, "build_features": 8,
            "derived_files": 0, "m49_corrections": 0, "polities": 13,
            "sources": 11,
        }
        assert packet["visual_review_artifact"]["sha256"] == (
            "b3d9e29b88602856f4fb07a5671c071ca59984057d813889c6a3bb9a4fc32b3e"
        )
        actors = {row["owner_polity_id"] for row in packet["assignment_overrides"]}
        assert "scenario-nah" not in actors
        assert {"scenario-norse-greenland", "scenario-thule-inuit",
                "scenario-hohokam-communities", "scenario-mississippian-chiefdoms",
                "scenario-iroquoian-villages", "scenario-uninhabited-remote-islands"}.issubset(actors)
    elif region == "018":
        assert packet["expected_counts"] == {
            "assertions": 32, "assignments": 225, "build_features": 8,
            "derived_files": 0, "m49_corrections": 0, "polities": 8,
            "sources": 8,
        }
        assert packet["visual_review_artifact"]["sha256"] == (
            "5b6086afc19995c54413496414280806c15837a77955ae975a95e858fd933adf"
        )
        actors = {row["owner_polity_id"] for row in packet["assignment_overrides"]}
        assert not actors.intersection({
            "scenario-atf", "scenario-bwa", "scenario-kon", "scenario-lso",
            "scenario-nam", "scenario-swz", "scenario-zaf",
        })
        assert {"scenario-limpopo-shashe-successors",
                "scenario-sotho-tswana-communities",
                "scenario-nguni-speaking-communities",
                "scenario-kalahari-san-communities",
                "scenario-khoe-pastoral-communities",
                "scenario-ovambo-kavango-communities",
                "scenario-cape-khoekhoe-san",
                "scenario-uninhabited-southern-ocean-islands"}.issubset(actors)
    elif region == "029":
        assert packet["expected_counts"] == {
            "assertions": 32, "assignments": 396, "build_features": 8,
            "derived_files": 0, "m49_corrections": 0, "polities": 11,
            "sources": 22,
        }
        assert packet["visual_review_artifact"]["sha256"] == (
            "a9968a21b77e7a979c70dba2bd291b01529e9f3bc93b0ce3fa3c5a9820288ccf"
        )
        actors = {row["owner_polity_id"] for row in packet["assignment_overrides"]}
        assert not actors.intersection({
            "scenario-nah", "scenario-tca", "scenario-vct", "scenario-tto",
            "scenario-grd", "scenario-vir", "scenario-vgb", "scenario-aia",
            "scenario-bjn", "scenario-cym", "scenario-atg", "scenario-brb",
            "scenario-maf", "scenario-kna", "scenario-msr", "scenario-dma",
            "scenario-lca", "scenario-umi", "scenario-blm", "scenario-abw",
            "scenario-ser", "scenario-sxm", "scenario-usg", "scenario-cuw",
        })
        assert {"scenario-lucayan-chiefdoms", "scenario-cuba-taino-chiefdoms",
                "scenario-guanahatabey-communities",
                "scenario-hispaniola-taino-chiefdoms",
                "scenario-boriken-taino-chiefdoms",
                "scenario-jamaica-taino-communities",
                "scenario-eastern-taino-communities",
                "scenario-kalinago-lesser-antilles",
                "scenario-trinidad-communities",
                "scenario-caquetio-southern-caribbean",
                "scenario-small-island-communities"}.issubset(actors)
    elif region == "030":
        assert packet["expected_counts"] == {
            "assertions": 21, "assignments": 1941, "build_features": 5,
            "derived_files": 1, "m49_corrections": 0, "polities": 8,
            "sources": 9,
        }
        assert packet["visual_review_artifact"]["sha256"] == (
            "995c0fe202ab3c93d9266fc1706da7fe513076aada09db811969a2ed88807abc"
        )
        actors = {row["owner_polity_id"] for row in packet["assignment_overrides"]}
        assert not actors.intersection({"scenario-hkg", "scenario-mac", "scenario-mos"})
        assert {"scenario-jurchen", "scenario-moghulistan", "scenario-northern-yuan"}.issubset(actors)
    elif region == "034":
        assert packet["expected_counts"] == {
            "assertions": 53, "assignments": 910, "build_features": 13,
            "derived_files": 1, "m49_corrections": 0, "polities": 20,
            "sources": 9,
        }
        assert packet["visual_review_artifact"]["sha256"] == (
            "6f7d463396142edcd69616c2732687b740c55c41dc7d5c700d1f22b60106f000"
        )
        actors = {row["owner_polity_id"] for row in packet["assignment_overrides"]}
        assert not actors.intersection({"scenario-iot", "scenario-mdv"})
        assert {"scenario-kotte", "scenario-jaffna", "scenario-maldives",
                "scenario-uninhabited-iot"}.issubset(actors)
    elif region == "035":
        assert packet["expected_counts"] == {
            "assertions": 57, "assignments": 1759, "build_features": 14,
            "derived_files": 1, "m49_corrections": 3, "polities": 29,
            "sources": 7,
        }
        assert packet["visual_review_artifact"]["sha256"] == (
            "8931349ecff68ab92179bd23c964bf85292a0b12a4b640bc56b2e6c22b6af6d2"
        )
        actors = {row["owner_polity_id"] for row in packet["assignment_overrides"]}
        assert not actors.intersection({"scenario-unk", "scenario-mal", "scenario-pga", "scenario-scr"})
        assert {"scenario-hanthawaddy", "scenario-lanxang", "scenario-malacca",
                "scenario-majapahit", "scenario-sulu"}.issubset(actors)
        assert {row["region_id"] for row in packet["location_region_overrides"]} == {"053"}
    elif region == "039":
        assert packet["expected_counts"] == {
            "assertions": 29, "assignments": 464, "build_features": 7,
            "derived_files": 2, "m49_corrections": 0, "polities": 23,
            "sources": 18,
        }
        assert packet["visual_review_artifact"]["sha256"] == (
            "ee88cd687939060294c5a3e75ca392435245a605d2dc2ab6e3fbf0aff96f0f66"
        )
        names = {row["polity_id"]: row["name"] for row in packet["polities"]}
        assert names["scenario-tur"].endswith("after the Battle of Varna")
        assert names["scenario-nap"] == "Kingdom of Naples under Alfonso V"
    elif region == "053":
        assert packet["expected_counts"] == {
            "assertions": 32, "assignments": 1199, "build_features": 8,
            "derived_files": 0, "m49_corrections": 7, "polities": 14,
            "sources": 12,
        }
        assert packet["visual_review_artifact"]["sha256"] == (
            "2b3d18fcd8920ce1359d768a03aee2ba8cfe846aed0404f8868ee37e2e53e7e6"
        )
        actors = {row["owner_polity_id"] for row in packet["assignment_overrides"]}
        assert not actors.intersection({"scenario-nah", "scenario-csi", "scenario-atc", "scenario-nfk"})
        assert {
            "scenario-kimberley-communities", "scenario-arnhem-top-end-communities",
            "scenario-cape-york-torres-communities", "scenario-western-desert-communities",
            "scenario-central-desert-communities", "scenario-southwest-australia-communities",
            "scenario-murray-southeast-communities", "scenario-east-coast-australia-communities",
            "scenario-tasmanian-communities", "scenario-maori-north-island-hapu",
            "scenario-maori-south-island-hapu", "scenario-norfolk-polynesian-community",
            "scenario-tokelau-communities", "scenario-uninhabited-australasian-islands",
        } == actors
        assert {row["region_id"] for row in packet["location_region_overrides"]} == {"061"}
    elif region == "054":
        assert packet["expected_counts"] == {
            "assertions": 32, "assignments": 414, "build_features": 8,
            "derived_files": 0, "m49_corrections": 0, "polities": 12,
            "sources": 10,
        }
        assert packet["visual_review_artifact"]["sha256"] == (
            "b47bc579f3d0753d57cb20cdf2b6fe33ad494075dc65c870f79f16ff614e52c9"
        )
        actors = {row["owner_polity_id"] for row in packet["assignment_overrides"]}
        assert not actors.intersection({"scenario-png", "scenario-slb", "scenario-vut",
                                        "scenario-fji", "scenario-ncl"})
        assert {
            "scenario-new-guinea-highlands-communities",
            "scenario-new-guinea-north-coast-communities",
            "scenario-new-guinea-south-coast-communities",
            "scenario-bismarck-bougainville-communities",
            "scenario-western-solomons-communities",
            "scenario-central-solomons-communities",
            "scenario-santa-cruz-communities",
            "scenario-northern-vanuatu-communities",
            "scenario-central-southern-vanuatu-chiefdoms",
            "scenario-western-fiji-chiefdoms", "scenario-eastern-fiji-chiefdoms",
            "scenario-kanak-chiefdoms",
        } == actors
    elif region == "057":
        assert packet["expected_counts"] == {
            "assertions": 32, "assignments": 175, "build_features": 8,
            "derived_files": 0, "m49_corrections": 0, "polities": 13,
            "sources": 10,
        }
        assert packet["visual_review_artifact"]["sha256"] == (
            "d81edf89684cfdf97f65faa1c5a891df1a47a552aef38a5b5e858e4ddea8c7dc"
        )
        actors = {row["owner_polity_id"] for row in packet["assignment_overrides"]}
        assert not actors.intersection({
            "scenario-fsm", "scenario-gum", "scenario-kir", "scenario-mhl",
            "scenario-mnp", "scenario-nru", "scenario-plw", "scenario-umi",
        })
        assert {
            "scenario-palau-island-communities",
            "scenario-southwest-palau-communities",
            "scenario-yap-western-caroline-communities",
            "scenario-central-caroline-atoll-communities",
            "scenario-saudeleur-pohnpei", "scenario-leluh-kosrae",
            "scenario-chamorro-latte-communities",
            "scenario-marshall-ralik-communities",
            "scenario-marshall-ratak-communities",
            "scenario-gilbert-island-communities",
            "scenario-line-phoenix-voyaging-communities",
            "scenario-nauru-island-community",
            "scenario-uninhabited-remote-micronesian-islands",
        } == actors
    elif region == "061":
        assert packet["expected_counts"] == {
            "assertions": 32, "assignments": 176, "build_features": 8,
            "derived_files": 0, "m49_corrections": 0, "polities": 15,
            "sources": 10,
        }
        assert packet["visual_review_artifact"]["sha256"] == (
            "a3fb0c1f3d719bdd9aa893c5e3b2da38758c5b046cb98c7cb1adeb6fece59c9e"
        )
        actors = {row["owner_polity_id"] for row in packet["assignment_overrides"]}
        assert not actors.intersection({
            "scenario-asm", "scenario-cok", "scenario-niu", "scenario-pcn",
            "scenario-pyf", "scenario-ton", "scenario-tuv", "scenario-wlf",
            "scenario-wsm",
        })
        assert {
            "scenario-tuvalu-atoll-communities", "scenario-marquesas-valley-polities",
            "scenario-society-islands-communities", "scenario-tuamotu-communities",
            "scenario-gambier-communities", "scenario-austral-islands-communities",
            "scenario-northern-cook-communities", "scenario-southern-cook-chiefdoms",
            "scenario-tui-tonga-chiefdom", "scenario-samoan-chiefly-communities",
            "scenario-niue-community", "scenario-uvea-chiefdom",
            "scenario-futuna-chiefdoms", "scenario-pitcairn-henderson-communities",
            "scenario-uninhabited-pitcairn-islands",
        } == actors
    elif region == "143":
        assert packet["expected_counts"] == {
            "assertions": 17, "assignments": 310, "build_features": 4,
            "derived_files": 1, "m49_corrections": 3, "polities": 8,
            "sources": 7,
        }
        assert packet["visual_review_artifact"]["sha256"] == (
            "cf8220bb99658d6b45f1d6ffc6cd42b6535f01282e26656432f2799e14d6ebd0"
        )
        actors = {row["owner_polity_id"] for row in packet["assignment_overrides"]}
        assert not actors.intersection({"scenario-chag", "scenario-kaz", "scenario-mos", "scenario-uzb"})
        assert {"scenario-abul-khayr-uzbek", "scenario-moghulistan",
                "scenario-timurid-transoxiana", "scenario-nogai"}.issubset(actors)
        assert {target: sum(row["region_id"] == target for row in packet["location_region_overrides"])
                for target in {"145", "151"}} == {"145": 1, "151": 2}
    elif region == "145":
        assert packet["expected_counts"] == {
            "assertions": 29, "assignments": 768, "build_features": 7,
            "derived_files": 2, "m49_corrections": 0, "polities": 8,
            "sources": 11,
        }
        assert packet["visual_review_artifact"]["sha256"] == (
            "5db0275d6156cd6188bb85abcadc28811f7a1b2452efcd2e5b5dc3add93afcac"
        )
        assert "scenario-unk" not in {
            row["owner_polity_id"] for row in packet["assignment_overrides"]
        }
        assert {row["polity_id"] for row in packet["polities"]} >= {
            "scenario-rasulid", "scenario-local-arabia",
        }
    elif region == "151":
        assert packet["expected_counts"] == {
            "assertions": 5, "assignments": 2178, "m49_corrections": 0,
            "polities": 15, "sources": 10,
        }
        assert packet["visual_review_artifact"]["sha256"] == (
            "2ecf89be71b36d59ac8ea05c90e8dde5bff80c1e839003a67ec5311cf7cf5d2b"
        )
        assert {row["polity_id"]: row["name"] for row in packet["polities"]}[
            "scenario-pol"
        ].endswith("post-Varna interregnum")
    elif region == "154":
        assert packet["location_region_overrides"] == [{
            "location_id": "loc_83d09efffffffff_9e81297988", "region_id": "005",
            "reason": "Bouvet Island is geographically in UN M49 South America, not Northern Europe.",
        }]
        assert packet["expected_counts"] == {
            "assertions": 23, "assignments": 1367, "derived_files": 3,
            "m49_corrections": 1, "polities": 18, "sources": 14,
        }
    elif region == "155":
        assert {target: sum(row["region_id"] == target for row in packet["location_region_overrides"])
                for target in {"005", "014", "029"}} == {"005": 10, "014": 5, "029": 24}


def test_corrected_assignments_are_exactly_once_in_destination_packets():
    packet_files = {
        "005": "005-south-america-2026-08-16.json",
        "014": "014-eastern-africa-2026-08-16.json",
        "029": "029-caribbean-2026-08-16.json",
    }
    destinations = {
        region: json.loads((GLOBAL / "regional-packets" / filename).read_text())
        for region, filename in packet_files.items()
    }
    correction_packets = [
        json.loads((GLOBAL / "regional-packets" / filename).read_text())
        for filename in (
            "154-northern-europe-2026-08-15.json",
            "155-western-europe-2026-08-15.json",
        )
    ]
    correction_map = {
        row["location_id"]: row["region_id"]
        for packet in correction_packets for row in packet["location_region_overrides"]
        if row["region_id"] in destinations
    }
    expected_targets = {
        location_id: region
        for region, pairs in CORRECTED_DESTINATION_PAIRS.items()
        for location_id in pairs
    }
    assert correction_map == expected_targets
    assert all(not packet["location_region_overrides"] for packet in destinations.values())

    destination_indexes = {
        region: {row["province_id"]: row for row in packet["assignment_overrides"]}
        for region, packet in destinations.items()
    }
    correction_provinces = {
        row["province_id"]
        for packet in correction_packets for row in packet["assignment_overrides"]
    }
    occurrence_count = 0
    for region, pairs in CORRECTED_DESTINATION_PAIRS.items():
        for location_id, (province_id, policy_id) in pairs.items():
            occurrences = [
                (candidate_region, index[province_id])
                for candidate_region, index in destination_indexes.items()
                if province_id in index
            ]
            assert len(occurrences) == 1
            assert occurrences[0][0] == region
            assert province_id not in correction_provinces
            row = occurrences[0][1]
            actor, uncertainty, source_ids, note_prefix = CORRECTED_POLICIES[policy_id]
            uninhabited = row["facets"]["habitability"] == "uninhabitable"
            assert row["polity_ids"] == ([] if uninhabited else [actor])
            profiles = {item["polity_id"]: item for item in destinations[region]["polities"]}
            state_actor = not uninhabited and profiles[actor]["actor_kind"] == "state"
            expected_primary = actor if state_actor else None
            assert row["sovereign_polity_id"] == expected_primary
            assert row["owner_polity_id"] == expected_primary
            assert row["controller_polity_id"] == expected_primary
            assert row["core_polity_ids"] == ([actor] if state_actor else [])
            assert {item["actor_political_unit_id"] for item in row["status_relationships"]} == (set() if uninhabited else {actor})
            assert row["claim_polity_ids"] == []
            assert row["dispute_polity_ids"] == []
            assert row["uncertainty"] == uncertainty
            assert set(row["source_ids"]) == source_ids
            assert row["notes"].startswith(note_prefix)
            assert row["hierarchy"] == {
                "area_id": f"area-{region}-{actor}",
                "method": "evidence-backed-polity-region-grouping-v1",
                "region_id": region,
                "superregion_id": f"m49-superregion-{region}",
            }
            occurrence_count += 1
    assert occurrence_count == 40


def test_region_grade_a_source_pins_bind_the_canonical_source_records():
    provisional = _provisional_module()
    packet_path = GLOBAL / "regional-packets" / "155-western-europe-2026-08-15.json"
    packet = json.loads(packet_path.read_text())
    packet["source_pins"][0]["sha256"] = "0" * 64

    with pytest.raises(SystemExit, match="invalid canonical source pin"):
        provisional._qualify_grade_a_packet(packet)


def test_regional_packet_merge_preserves_cross_region_polity_capitals():
    provisional = _provisional_module()
    packet = {
        "region_id": "145", "sources": [], "coverage": [],
        "polities": [{
            "polity_id": "shared", "name": "Shared polity", "aliases": [],
            "capital_location_ids": ["eastern-capital"], "relationships": [],
            "source_ids": ["east-source"],
        }],
        "boundary_features": [], "assertions": [], "assignment_overrides": [],
    }
    sources = {"sources": []}
    gazetteer = {"polities": [{
        "polity_id": "shared", "name": "Shared polity", "aliases": [],
        "capital_location_ids": ["western-capital"], "relationships": [],
        "source_ids": ["west-source"],
    }]}
    boundaries = {"features": []}
    golden = {"assertions": []}
    assignments = {"assignments": []}
    coverage = {"coverage": []}

    provisional._apply_packets(
        [packet], sources, gazetteer, boundaries, golden, assignments, coverage,
    )

    assert gazetteer["polities"][0]["capital_location_ids"] == [
        "eastern-capital", "western-capital",
    ]
    assert gazetteer["polities"][0]["source_ids"] == ["east-source", "west-source"]


def test_region_grade_a_derived_files_are_contained_regular_and_checksum_pinned(tmp_path):
    provisional = _provisional_module()
    source_path = GLOBAL / "regional-packets" / "155-western-europe-2026-08-15.json"
    packet_path = tmp_path / "packet.json"
    packet = json.loads(source_path.read_text())
    asset = tmp_path / "assets" / "boundary.geojson"
    asset.parent.mkdir()
    asset.write_text('{"type":"FeatureCollection","features":[]}\n')
    source_ids = ["dauphant-2020-sources", "shepherd-historical-atlas"]
    packet["derived_files"] = [{
        "asset_id": "checked-boundary", "path": "assets/boundary.geojson",
        "target_path": "regional-assets/155/boundary.geojson",
        "sha256": hashlib.sha256(asset.read_bytes()).hexdigest(),
        "source_ids": source_ids, "valid_from": "1400", "valid_to": "1500",
    }]
    packet_path.write_text(json.dumps(packet))

    provisional._qualify_grade_a_packet(packet, packet_path)
    packet["derived_files"][0]["sha256"] = "0" * 64
    with pytest.raises(SystemExit, match="missing or checksum-invalid"):
        provisional._qualify_grade_a_packet(packet, packet_path)


def test_region_grade_a_build_features_require_checked_unique_capital_points():
    provisional = _provisional_module()
    packet_path = GLOBAL / "regional-packets" / "155-western-europe-2026-08-15.json"
    packet = json.loads(packet_path.read_text())
    packet["build_features"] = [{
        "type": "Feature", "properties": {
            "feature_id": "capital-test", "feature_type": "capital",
            "source_ids": ["regional-survey-155"],
        },
        "geometry": {"type": "Point", "coordinates": [0, 0]},
    }]
    provisional._qualify_grade_a_packet(packet)
    packet["build_features"].append(json.loads(json.dumps(packet["build_features"][0])))
    with pytest.raises(SystemExit, match="invalid or duplicate build feature"):
        provisional._qualify_grade_a_packet(packet)


def test_m49_enrichment_is_deterministic_and_marks_antarctica(monkeypatch):
    builder = _builder_module()
    countries = [
        ShapeFeature(mapping(box(0, 0, 2, 2)), {"SUBREGION": "Western Europe"}),
        ShapeFeature(mapping(box(2, 0, 4, 2)), {"SUBREGION": "Eastern Europe"}),
        ShapeFeature(mapping(box(0, -80, 4, -60)), {"SUBREGION": "Antarctica"}),
    ]
    monkeypatch.setattr(builder, "read_zipped_shapefile", lambda _path: countries)
    fabric = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"location_id": "west"}, "geometry": mapping(box(0, 0, 1, 1))},
        {"type": "Feature", "properties": {"location_id": "east"}, "geometry": mapping(box(3, 0, 4, 1))},
        {"type": "Feature", "properties": {"location_id": "south"}, "geometry": mapping(box(1, -70, 2, -69))},
    ]}
    result = builder.enrich_m49(fabric, Path("unused.zip"))
    assert [row["properties"]["m49_subregion"] for row in result["features"]] == ["151", "Antarctica", "155"]
    assert all("m49_subregion" not in row["properties"] for row in fabric["features"])


def test_resolved_inventory_rejects_placeholder_subjects_and_sources():
    builder = _builder_module()
    inventory = json.loads((ROOT / "tests/fixtures/m25c/placeholder-anomaly-inventory.json").read_text())
    with pytest.raises(SystemExit, match="top-level fields"):
        builder._validate_inventory(inventory)


def test_evidence_rejection_is_aggregated_and_copies_no_invalid_inputs(tmp_path):
    builder = _builder_module()
    evidence = tmp_path / "evidence"
    output = tmp_path / "output"
    evidence.mkdir()
    (evidence / "source_manifest.json").write_text(json.dumps({
        "schema_version": "0.2.0", "pass_id": "wrong-pass", "start_date": "1444-11-12",
    }) + "\n")
    args = Namespace(evidence_dir=evidence, output_dir=output)
    with pytest.raises(SystemExit, match="reviewed evidence bundle rejected"):
        builder.stage_evidence(args)
    report = json.loads((output / builder.REJECTION_REPORT).read_text())
    assert report["status"] == "reject"
    assert report["finding_count"] > 3
    assert {"artifact", "rule", "affected_ids", "remediation_owner"}.issubset(report["findings"][0])
    assert not (output / "source_manifest.json").exists()


def test_evidence_bundle_accepts_the_versioned_census_ledger_contract(tmp_path):
    builder = _builder_module()
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    for name in builder.CURATED_FILES:
        if name in {"anomaly_inventory.json", "dossier.md"}:
            continue
        schema_version = (
            "1.0.0" if name == "anomaly_census_review_ledger.json" else "0.3.0"
        )
        (evidence / name).write_text(json.dumps({
            "schema_version": schema_version,
            "pass_id": builder.PASS_ID,
            "start_date": builder.START_DATE,
        }) + "\n")

    findings = builder._validate_evidence_bundle(evidence)

    ledger_findings = [
        row for row in findings
        if row["artifact"] == "anomaly_census_review_ledger.json"
    ]
    assert not any(row["rule"] == "SCHEMA_VERSION_MISMATCH" for row in ledger_findings)


def test_handoff_reports_all_missing_input_owners(tmp_path):
    builder = _builder_module()
    args = Namespace(
        inventory_input=None, fabric_input=None, fabric_sidecars_dir=None,
        natural_earth_input=tmp_path / "missing-ne.zip", evidence_dir=None,
    )
    findings = builder._validate_curator_handoff(args)
    assert {(row["artifact"], row["remediation_owner"]) for row in findings} == {
        ("anomaly_inventory", "historical-curator"),
        ("evidence_bundle", "historical-curator"),
        ("fabric", "fabric-curator"),
        ("fabric_sidecars", "fabric-curator"),
        ("natural_earth", "pipeline-operator"),
    }


def test_evidence_sidecar_paths_and_hashes_fail_closed(tmp_path):
    builder = _builder_module()
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    assignments = {
        "fabric_sidecars": {
            "lineage": {"path": "../lineage.json", "sha256": "0" * 64},
            "locations": {"path": "sidecars/locations.geojson", "sha256": "0" * 64},
        },
        "release_sidecars": {},
    }
    (evidence / "assignments.json").write_text(json.dumps(assignments) + "\n")
    sidecars = evidence / "sidecars"
    sidecars.mkdir()
    (sidecars / "locations.geojson").write_text("{}\n")
    findings = builder._validate_evidence_bundle(evidence)
    by_rule = {(row["artifact"], row["rule"]) for row in findings}
    assert ("fabric_sidecars:lineage", "PATH_ESCAPE") in by_rule
    assert ("fabric_sidecars:locations", "CHECKSUM_MISMATCH") in by_rule


def test_render_and_preflight_report_missing_manifest_without_traceback(tmp_path):
    builder = _builder_module()
    args = Namespace(output_dir=tmp_path)
    with pytest.raises(SystemExit, match="render rejected: Cannot read"):
        builder.stage_render(args)
    with pytest.raises(SystemExit, match="preflight rejected: Pass manifest does not exist"):
        builder.stage_preflight(args)


def test_handoff_contract_reports_count_partition_review_and_coverage_defects():
    builder = _builder_module()
    documents = {
        "source_manifest.json": {"sources": [{"source_id": "draft", "review_status": "pending"}]},
        "assignments.json": {
            "expected_province_count": 22_000,
            "assignments": [{
                "assignment_id": "a1", "province_id": "p1", "region_id": "155",
                "location_ids": ["loc1", "loc1"], "source_ids": ["draft"],
            }],
        },
        "coverage.json": {"coverage": [], "known_gaps": ["gap"], "exclusions": []},
    }
    findings = []
    builder._validate_evidence_contract(documents, findings)
    rules = {row["rule"] for row in findings}
    assert {
        "INVALID_GLOBAL_PROVINCE_COUNT", "DUPLICATE_LOCATION_ASSIGNMENT",
        "INVALID_WORLD_PARTITION", "UNREVIEWED_SOURCE_REFERENCE",
        "GLOBAL_COVERAGE_NOT_A", "GLOBAL_COVERAGE_GAPS",
    }.issubset(rules)


def test_pending_lineage_hash_pins_the_unchanged_pilot():
    provenance = json.loads((GLOBAL / "provenance" / "1444-v2-seed.json").read_text())
    actual = {
        path.relative_to(PILOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(PILOT.rglob("*")) if path.is_file()
    }
    assert provenance["promotion_prohibited"] is True
    assert provenance["files"] == actual
    assert json.loads((GLOBAL / "candidate_status.json").read_text())["public_release_allowed"] is False


def test_global_assertions_reject_tolerances_widened_after_source_lock():
    golden = json.loads((PILOT / "golden.json").read_text())
    golden["schema_version"] = "0.3.0"
    for assertion in golden["assertions"]:
        assertion["tolerance_policy"] = {
            "fixed_before_measurement": True,
            "source_derived_tolerance": assertion["tolerance"],
            "source_ids": ["reviewed-source"],
        }
    validate_spatial_golden_borders(golden)
    golden["assertions"][0]["tolerance"] += 1
    with pytest.raises(SchemaValidationError, match="not fixed"):
        validate_spatial_golden_borders(golden)


def test_certification_bundle_rejects_tampering(tmp_path):
    roles = ("research_pass", "research_qa", "canonical_historical_status", "independent_review", "runtime_manifest")
    records = {}
    for role in roles:
        path = tmp_path / f"{role}.json"
        path.write_text("{}\n")
        records[role] = {"path": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    benchmark = tmp_path / "runtime_benchmark.json"
    benchmark.write_text(json.dumps({"status": "pass", "gates": {"all": "pass"}}) + "\n")
    records["runtime_benchmark"] = {"path": benchmark.name, "sha256": hashlib.sha256(benchmark.read_bytes()).hexdigest()}
    certification = {
        "schema_version": "1.0.0", "certification_type": "gpm-global-era-certification",
        "status": "accepted", "certification_id": "official-1444-global-v1",
        "pass_id": "official-1444-global-v1", "start_date": "1444-11-11",
        "scope": "worldwide", "public_scenario_id": "official-1444",
        "compatibility_revision": "1", "artifacts": records,
        "gates": {name: "pass" for name in ("research", "world_partition", "coverage", "canonical_runtime_parity", "runtime_determinism", "runtime_performance", "independent_review")},
    }
    path = tmp_path / "certification.json"
    path.write_text(json.dumps(certification) + "\n")
    assert validate_certification_bundle(path)["status"] == "accepted"
    benchmark.write_text('{"status":"fail","gates":{}}\n')
    with pytest.raises(EraCertificationError, match="missing or altered"):
        validate_certification_bundle(path)


def test_certification_bundle_rejects_forged_provisional_lineage(tmp_path):
    roles = ("research_pass", "research_qa", "canonical_historical_status", "independent_review", "runtime_manifest")
    records = {}
    for role in roles:
        artifact = tmp_path / f"{role}.json"
        content = {"qa_mode": "provisional_internal_review"} if role == "research_pass" else {}
        artifact.write_text(json.dumps(content) + "\n")
        records[role] = {"path": artifact.name, "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest()}
    benchmark = tmp_path / "runtime_benchmark.json"
    benchmark.write_text(json.dumps({"status": "pass", "gates": {"all": "pass"}}) + "\n")
    records["runtime_benchmark"] = {"path": benchmark.name, "sha256": hashlib.sha256(benchmark.read_bytes()).hexdigest()}
    certification = {
        "schema_version": "1.0.0", "certification_type": "gpm-global-era-certification",
        "status": "accepted", "certification_id": "official-1444-global-v1",
        "pass_id": "official-1444-global-v1", "start_date": "1444-11-11", "scope": "worldwide",
        "public_scenario_id": "official-1444", "compatibility_revision": "1", "artifacts": records,
        "gates": {name: "pass" for name in (
            "research", "world_partition", "coverage", "canonical_runtime_parity",
            "runtime_determinism", "runtime_performance", "independent_review",
        )},
    }
    path = tmp_path / "certification.json"
    path.write_text(json.dumps(certification) + "\n")
    with pytest.raises(EraCertificationError, match="cannot be published or demo-promoted"):
        validate_certification_bundle(path)


def test_certification_bundle_rejects_artifacts_outside_bundle(tmp_path):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_text("{}\n")
    records = {
        role: {"path": "../outside.json", "sha256": hashlib.sha256(outside.read_bytes()).hexdigest()}
        for role in (
            "research_pass", "research_qa", "canonical_historical_status",
            "independent_review", "runtime_manifest", "runtime_benchmark",
        )
    }
    certification = {
        "schema_version": "1.0.0", "certification_type": "gpm-global-era-certification",
        "status": "accepted", "certification_id": "official-1444-global-v1",
        "pass_id": "official-1444-global-v1", "start_date": "1444-11-11",
        "scope": "worldwide", "public_scenario_id": "official-1444",
        "compatibility_revision": "1", "artifacts": records,
        "gates": {name: "pass" for name in (
            "research", "world_partition", "coverage", "canonical_runtime_parity",
            "runtime_determinism", "runtime_performance", "independent_review",
        )},
    }
    path = bundle / "certification.json"
    path.write_text(json.dumps(certification) + "\n")
    with pytest.raises(EraCertificationError, match="escapes bundle directory"):
        validate_certification_bundle(path)


def test_demo_refuses_uncertified_official_1444():
    with pytest.raises(DemoBuildError, match="requires --certification-input"):
        build_demo(scenarios=("official-1444",), validate=False)
