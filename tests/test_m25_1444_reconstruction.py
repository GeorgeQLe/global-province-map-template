import hashlib
import json
import shutil
from pathlib import Path

from gpm.qa.start_date import run_start_date_qa
from shapely.geometry import shape


ROOT = Path(__file__).resolve().parents[1]
PASS_DIR = ROOT / "research" / "start-dates" / "1444-v1"


def _load(name: str):
    return json.loads((PASS_DIR / name).read_text(encoding="utf-8"))


def test_m25_candidate_is_rejected_by_the_hardened_start_date_contract(tmp_path):
    result = run_start_date_qa(
        pass_dir=PASS_DIR,
        report_output=tmp_path / "start_date_qa.json",
    )
    report = json.loads((tmp_path / "start_date_qa.json").read_text())

    assert not result.passed
    assert result.artifact_count == 9
    assert result.error_count == 14 and result.warning_count == 0
    assert len(report["assertion_results"]) == 15
    assert {row["status"] for row in report["assertion_results"]} == {"pass"}
    codes = {row["code"] for row in report["findings"]}
    assert {"MISSING_FABRIC_SIDECAR", "BOUNDARY_DATE_OUT_OF_RANGE", "POSITIVE_ASSERTION_USES_SOFT_EVIDENCE"} <= codes


def test_m25_manifest_pins_all_release_artifacts():
    manifest = _load("pass_manifest.json")

    assert manifest["pass_id"] == "official-1444-reconstruction-v1"
    assert manifest["start_date"] == "1444-11-11"
    assert manifest["geometry_revision"] == "1444-r1"
    assert manifest["scope"]["priority_regions"] == [
        "low-countries", "burgundy", "france", "hre", "central-europe",
    ]
    assert len(manifest["artifacts"]) == 9
    for record in manifest["artifacts"].values():
        path = PASS_DIR / record["path"]
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"]


def test_m25_brussels_and_nord_negative_anachronism_regressions(tmp_path):
    run_start_date_qa(
        pass_dir=PASS_DIR,
        report_output=tmp_path / "start_date_qa.json",
    )
    report = json.loads((tmp_path / "start_date_qa.json").read_text())
    results = {row["assertion_id"]: row for row in report["assertion_results"]}
    golden = _load("golden.json")
    definitions = {row["assertion_id"]: row for row in golden["assertions"]}

    for assertion_id, forbidden_id in (
        ("negative-modern-brussels-capital-region", "forbidden-modern-brussels-capital-region"),
        ("negative-modern-nord-department", "forbidden-modern-nord-department"),
    ):
        definition = definitions[assertion_id]
        result = results[assertion_id]
        assert definition["expectation"] == "negative_anachronism"
        assert definition["boundary_feature_ids"] == [forbidden_id]
        assert result["status"] == "pass"
        assert result["measurement"] <= result["tolerance"]

    boundaries = {
        row["properties"]["feature_id"]: row
        for row in _load("boundaries.geojson")["features"]
    }
    assert boundaries["forbidden-modern-brussels-capital-region"]["properties"]["valid_from"] == "2022"
    assert boundaries["forbidden-modern-nord-department"]["properties"]["valid_from"] == "2022"


def test_m25_reconstructed_province_interiors_do_not_overlap():
    provinces = [
        shape(row["geometry"])
        for row in _load("build.geojson")["features"]
        if row["properties"]["feature_type"] == "province"
    ]

    for index, left in enumerate(provinces):
        for right in provinces[index + 1:]:
            assert left.intersection(right).area == 0


def test_m25_downgrades_unsupported_grades_and_exposes_unaccepted_split_claims():
    coverage = _load("coverage.json")
    assignments = _load("assignments.json")
    sources = _load("source_manifest.json")

    assert len(coverage["coverage"]) == 5 * 4
    assert {row["grade"] for row in coverage["coverage"]} == {"C", "U"}
    assert all(row["known_gaps"] for row in coverage["coverage"])
    assert {row["request_id"] for row in assignments["targeted_split_requests"]} == {
        "split-brussels-modern-outline", "split-nord-modern-outline",
    }
    assert {row["status"] for row in assignments["targeted_split_requests"]} == {"accepted"}
    assert assignments["expected_province_count"] == 22000
    assert set(assignments["fabric_sidecars"]) == {"fabric_manifest", "locations", "lineage", "province_membership"}
    assert all(row["review_status"] == "reviewed" for row in sources["sources"])


def test_m25_historical_downloads_are_checksum_pinned_and_frontiers_are_soft():
    sources = {row["source_id"]: row for row in _load("source_manifest.json")["sources"]}
    expected = {
        "shepherd-france-1453": "123742af7f7e8390d16ca01817e14b5cfc1e066233ea8be31ce2ccf72146008e",
        "droysen-hre-1400": "44bc2f48fc19a8ee00bb3b534387feeafdaca9597648948923b1ff4cf96d6cd4",
        "nelson-europe-1430": "e75c37a522cfad805b66728f8e45b8a828d9ff6e0d137072d809456df6794d61",
        "jacquerye-burgundian-netherlands-1477": "55be2e03be689ad12d964486e118466fb58d675866a4672f03c2fee7386d88d9",
        "geoboundaries-bel-adm1-2022": "7af87f5035779f0aefe5bf930288572979e490ab0441fd9b92942a519bea0974",
        "geoboundaries-fra-adm2-2022": "a14ed131c86c802e5d546c7cbeccbd4daebc94a66fea413f563935a53504f251",
        "geoboundaries-fra-adm1-2022": "26b876de5b03c99399ccec16a367deb8681c4953eecede32ac6f5d4fb581bf09",
        "geoboundaries-deu-adm1-2022": "65af06f80e837028997c396d2c67d74fb1e1752d884e9a0638d5c736ee8c345a",
        "geoboundaries-cze-adm0-2022": "26452c32c6013dabb946428b8b97e43c52982b7eb7112075237fc415262a3e28",
    }
    assert {key: sources[key]["checksum"] for key in expected} == expected
    frontiers = [
        feature for feature in _load("boundaries.geojson")["features"]
        if feature["properties"]["feature_id"].startswith("frontier-")
    ]
    assert {feature["properties"]["classification"] for feature in frontiers} == {"soft_evidence"}


def test_m25_gazetteer_preserves_composite_relationships():
    gazetteer = _load("gazetteer.json")
    relationships = {
        relationship["relationship_id"]: relationship
        for polity in gazetteer["polities"]
        for relationship in polity["relationships"]
    }

    assert relationships["bra-union-bur"]["type"] == "personal_union"
    assert relationships["bur-claim-fra"]["type"] == "claim"
    assert relationships["col-estate-hre"]["type"] == "dependency"
    assert relationships["boh-estate-hre"]["type"] == "dependency"


def test_m25_brussels_and_nord_material_mutations_fail(tmp_path):
    candidate = tmp_path / "candidate"
    shutil.copytree(PASS_DIR, candidate)
    golden = json.loads((candidate / "golden.json").read_text())
    for assertion in golden["assertions"]:
        if assertion["assertion_id"] in {"negative-modern-brussels-capital-region", "negative-modern-nord-department"}:
            assertion["tolerance"] = 0
    (candidate / "golden.json").write_text(json.dumps(golden, indent=2, sort_keys=True) + "\n")
    manifest = json.loads((candidate / "pass_manifest.json").read_text())
    manifest["artifacts"]["golden_borders"]["sha256"] = hashlib.sha256((candidate / "golden.json").read_bytes()).hexdigest()
    (candidate / "pass_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    run_start_date_qa(pass_dir=candidate)
    report = json.loads((candidate / "start_date_qa.json").read_text())
    failed = {row["assertion_id"] for row in report["assertion_results"] if row["status"] == "fail"}
    assert {"negative-modern-brussels-capital-region", "negative-modern-nord-department"} <= failed
