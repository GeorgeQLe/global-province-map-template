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
    ("005", "005-south-america-2026-08-16.json", 2200, 0),
    ("011", "011-western-africa-2026-08-16.json", 641, 2),
    ("013", "013-central-america-2026-08-16.json", 605, 0),
    ("014", "014-eastern-africa-2026-08-16.json", 715, 0),
    ("015", "015-northern-africa-2026-08-16.json", 643, 0),
    ("017", "017-middle-africa-2026-08-16.json", 527, 0),
    ("018", "018-southern-africa-2026-08-16.json", 225, 0),
    ("021", "021-northern-america-2026-08-16.json", 3986, 0),
    ("029", "029-caribbean-2026-08-16.json", 372, 0),
    ("030", "030-eastern-asia-2026-08-16.json", 1941, 0),
    ("034", "034-southern-asia-2026-08-16.json", 910, 0),
    ("035", "035-south-eastern-asia-2026-08-16.json", 1759, 3),
    ("039", "039-southern-europe-2026-08-15.json", 464, 0),
    ("053", "053-australia-new-zealand-2026-08-16.json", 1199, 7),
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
    if region == "005":
        assert packet["expected_counts"] == {
            "assertions": 32, "assignments": 2200, "build_features": 8,
            "derived_files": 0, "m49_corrections": 0, "polities": 15,
            "sources": 9,
        }
        assert packet["visual_review_artifact"]["sha256"] == (
            "7275a21a0e8eea8acf508d0e8518e8432f1c2c4164958d6cfa1592b180bf64c2"
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
            "assertions": 32, "assignments": 715, "build_features": 8,
            "derived_files": 0, "m49_corrections": 0, "polities": 13,
            "sources": 9,
        }
        assert packet["visual_review_artifact"]["sha256"] == (
            "73860a47d532f9015e9c0e6006cfcc4dfe8581c72a66218f5d9605a024e51345"
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
                "scenario-uninhabited-western-indian-ocean"}.issubset(actors)
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
            "assertions": 32, "assignments": 372, "build_features": 8,
            "derived_files": 0, "m49_corrections": 0, "polities": 11,
            "sources": 8,
        }
        assert packet["visual_review_artifact"]["sha256"] == (
            "ce83e796b976bfd6ca81678425766c99eab5eeda532dfe4a4b66c9f9a413ecba"
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
