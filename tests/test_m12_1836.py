"""M12: first curated official scenario (1836 / curated-politics)."""

from __future__ import annotations

import json
from pathlib import Path

from gpm.cli import main
from gpm.paths import SCENARIO_DIR, SCENARIO_GOLDEN_DIR
from gpm.qa.scenario import run_scenario_politics_qa
from gpm.release.quality import (
    QUALITY_TIER_CURATED_POLITICS,
    accuracy_label,
)
from gpm.scenarios import (
    list_scenarios,
    load_scenario,
    resolve_ownership_records,
    validate_scenario_document,
)
from gpm.schemas import validate_scenario_definition


def _land(province_id, *, country="FRA", region="FR-01", name=None):
    return {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
        },
        "properties": {
            "province_id": province_id,
            "display_name": name or province_id,
            "kind": "land",
            "parent_region_id": region,
            "parent_country_id": country,
            "area_sq_km": 100.0,
            "estimated_population": 1000.0,
            "terrain_class": None,
            "coastal": False,
            "island": False,
            "source_lineage": ["test"],
            "license_lineage": ["public domain"],
        },
    }


def test_official_1836_bundled_metadata_and_schema():
    scenario = load_scenario("official-1836")
    assert scenario["scenario_id"] == "official-1836"
    assert scenario["era"] == "1836"
    assert scenario["start_date"] == "1836-01-01"
    assert scenario["quality_tier"] == "curated-politics"
    assert scenario["official_era"] is True
    assert scenario["recommended_profile"] == "victoria-like"
    assert "europe" in scenario["priority_theaters"]
    assert "north-america" in scenario["priority_theaters"]
    assert len(scenario["countries"]) >= 40
    assert len(scenario["country_rules"]) >= 50
    assert len(scenario["region_rules"]) >= 50
    # Elevated theaters: German states, Italian states, Texas, partitions.
    region_ids = {rule["match_parent_region_id"] for rule in scenario["region_rules"]}
    assert "DE-BY" in region_ids
    assert "IT-RM" in region_ids
    assert "US-TX" in region_ids
    assert "PL-MA" in region_ids
    owners = {rule["owner"] for rule in scenario["country_rules"]}
    assert {"GBR", "FRA", "PRU", "AUS", "RUS", "USA", "QNG", "TUR"} <= owners
    validate_scenario_document(scenario)
    validate_scenario_definition(scenario)

    summaries = list_scenarios()
    by_id = {item.scenario_id: item for item in summaries}
    assert "official-1836" in by_id
    summary = by_id["official-1836"]
    assert summary.quality_tier == "curated-politics"
    assert summary.official_era is True
    assert summary.recommended_profile == "victoria-like"


def test_official_1836_golden_file_exists():
    path = SCENARIO_GOLDEN_DIR / "official-1836.json"
    assert path.is_file()
    golden = json.loads(path.read_text(encoding="utf-8"))
    assert golden["scenario_id"] == "official-1836"
    mins = golden["min_owner_counts"]
    assert mins["GBR"] >= 10
    assert mins["TEX"] >= 1
    assert mins["BAV"] >= 1


def test_null_padded_region_ids_match_rules():
    """Shapefile-style NUL padding must not break region rule matching."""
    scenario = load_scenario("official-1836")
    features = [
        _land("land_bav", country="DEU", region="DE-BY\x00\x00"),
        _land("land_tex", country="USA", region="US-TX\x00"),
        _land("land_pru", country="DEU", region="DE-BE\x00\x00\x00"),
    ]
    records, stats = resolve_ownership_records(scenario, features)
    by_id = {row["province_id"]: row for row in records}
    assert by_id["land_bav"]["owner"] == "BAV"
    assert by_id["land_bav"]["assignment_source"] == "region_rule"
    assert by_id["land_tex"]["owner"] == "TEX"
    assert by_id["land_pru"]["owner"] == "PRU"
    assert stats["region_rule_hits"] == 3


def test_elevated_theaters_resolve_over_country_defaults():
    scenario = load_scenario("official-1836")
    features = [
        _land("it_rome", country="ITA", region="IT-RM"),
        _land("it_turin", country="ITA", region="IT-TO"),
        _land("it_naples", country="ITA", region="IT-NA"),
        _land("pl_galicia", country="POL", region="PL-MA"),
        _land("us_cal", country="USA", region="US-CA"),
        _land("us_ore", country="USA", region="US-OR"),
        _land("irl", country="IRL", region="IE-D"),
        _land("nor", country="NOR", region="NO-03"),
    ]
    records, _stats = resolve_ownership_records(scenario, features)
    by_id = {row["province_id"]: row for row in records}
    assert by_id["it_rome"]["owner"] == "PAP"
    assert by_id["it_turin"]["owner"] == "SAR"
    assert by_id["it_naples"]["owner"] == "SIC"
    assert by_id["pl_galicia"]["owner"] == "AUS"
    assert by_id["us_cal"]["owner"] == "MEX"
    assert by_id["us_ore"]["owner"] == "GBR"
    assert by_id["us_ore"]["disputed"] is True
    assert by_id["irl"]["owner"] == "GBR"
    assert by_id["nor"]["owner"] == "SWE"


def test_accuracy_label_notes_official_1836():
    label = accuracy_label(
        scenarios=("official-1836", "modern-baseline"),
        politics_tier=QUALITY_TIER_CURATED_POLITICS,
        profile_id="victoria-like",
    )
    assert label["politics_quality_tier"] == "curated-politics"
    assert any("official-1836" in note for note in label["scenario_notes"])
    assert any("curated-politics" in note for note in label["scenario_notes"])
    assert any("official-1836" in s and "curated-politics" in s for s in label["honest_statements"])


def test_cli_scenario_list_and_validate_include_1836(capsys):
    assert main(["scenario", "list"]) == 0
    listed = capsys.readouterr().out
    assert "official-1836" in listed
    assert "curated-politics" in listed

    assert main(["scenario", "validate", "--scenario", "official-1836"]) == 0
    validated = capsys.readouterr().out
    assert "official era: yes" in validated
    assert "victoria-like" in validated


def test_qa_auto_discovers_bundled_golden(tmp_path):
    province_input = tmp_path / "provinces.geojson"
    features = [
        _land(f"p{i}", country="GBR", region=f"GB-{i:02d}")
        for i in range(60)
    ]
    features.extend(_land(f"f{i}", country="FRA", region=f"FR-{i:02d}") for i in range(50))
    features.append(_land("bav", country="DEU", region="DE-BY"))
    features.append(_land("tex", country="USA", region="US-TX"))
    features.append(_land("haw", country="USA", region="US-HI"))
    # Enough major-power bulk for golden floors that the fixture can meet.
    features.extend(_land(f"rus{i}", country="RUS", region=f"RU-{i:02d}") for i in range(30))
    features.extend(_land(f"aus{i}", country="AUT", region=f"AT-{i}") for i in range(20))
    features.extend(_land(f"usa{i}", country="USA", region=f"US-E{i}") for i in range(20))
    features.extend(_land(f"mex{i}", country="MEX", region=f"MX-{i:02d}") for i in range(25))
    features.extend(_land(f"spa{i}", country="ESP", region=f"ES-{i:02d}") for i in range(25))
    features.extend(_land(f"net{i}", country="NLD", region=f"NL-{i:02d}") for i in range(15))
    features.extend(_land(f"qng{i}", country="CHN", region=f"CN-{i:02d}") for i in range(25))
    features.extend(_land(f"tur{i}", country="TUR", region=f"TR-{i:02d}") for i in range(35))
    features.extend(_land(f"sar{i}", country="ITA", region="IT-TO") for i in range(6))
    features.extend(_land(f"sic{i}", country="ITA", region="IT-NA") for i in range(6))
    features.extend(_land(f"pap{i}", country="ITA", region="IT-RM") for i in range(4))
    features.extend(_land(f"bel{i}", country="BEL", region=f"BE-{i:02d}") for i in range(6))
    features.extend(_land(f"brz{i}", country="BRA", region=f"BR-{i:02d}") for i in range(12))
    features.extend(_land(f"pru{i}", country="DEU", region="DE-BE") for i in range(6))

    province_input.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "name": "provinces",
                "gpm": {"schema_version": "0.1.0", "profile_id": "modern-small"},
                "features": features,
            }
        ),
        encoding="utf-8",
    )
    report_output = tmp_path / "politics_qa.json"
    # Point golden discovery at the real bundled file via default path;
    # use explicit path here so the test does not require full global geometry.
    result = run_scenario_politics_qa(
        "modern-small",
        "official-1836",
        province_input=province_input,
        adjacency_input=None,
        golden_input=SCENARIO_GOLDEN_DIR / "official-1836.json",
        report_output=report_output,
    )
    assert result.golden_analysis == "complete"
    assert result.passed, report_output.read_text(encoding="utf-8")


def test_scenario_definition_path_is_under_configs():
    path = SCENARIO_DIR / "official-1836.json"
    assert path.is_file()
    document = json.loads(path.read_text(encoding="utf-8"))
    assert document["official_era"] is True
