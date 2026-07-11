"""M13: second curated official scenario (1444 / curated-politics)."""

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


def test_official_1444_bundled_metadata_and_schema():
    scenario = load_scenario("official-1444")
    assert scenario["scenario_id"] == "official-1444"
    assert scenario["era"] == "1444"
    assert scenario["start_date"] == "1444-11-11"
    assert scenario["quality_tier"] == "curated-politics"
    assert scenario["official_era"] is True
    assert scenario["recommended_profile"] == "eu-like"
    assert "europe" in scenario["priority_theaters"]
    assert len(scenario["countries"]) >= 40
    assert len(scenario["country_rules"]) >= 50
    assert len(scenario["region_rules"]) >= 50
    # Elevated theaters: Italian states, Burgundy, Granada, Novgorod, Byzantium.
    region_ids = {rule["match_parent_region_id"] for rule in scenario["region_rules"]}
    assert "IT-RM" in region_ids
    assert "IT-MI" in region_ids
    assert "IT-VE" in region_ids
    assert "ES-GR" in region_ids
    assert "FR-21" in region_ids  # Burgundy core
    assert "DE-BY" in region_ids
    assert "GB-EDH" in region_ids  # Scotland
    owners = {rule["owner"] for rule in scenario["country_rules"]}
    assert {"ENG", "FRA", "CAS", "ARA", "POR", "HAB", "MOS", "TUR", "MNG", "MAM"} <= owners
    validate_scenario_document(scenario)
    validate_scenario_definition(scenario)

    summaries = list_scenarios()
    by_id = {item.scenario_id: item for item in summaries}
    assert "official-1444" in by_id
    summary = by_id["official-1444"]
    assert summary.quality_tier == "curated-politics"
    assert summary.official_era is True
    assert summary.recommended_profile == "eu-like"


def test_official_1444_golden_file_exists():
    path = SCENARIO_GOLDEN_DIR / "official-1444.json"
    assert path.is_file()
    golden = json.loads(path.read_text(encoding="utf-8"))
    assert golden["scenario_id"] == "official-1444"
    mins = golden["min_owner_counts"]
    assert mins["ENG"] >= 10
    assert mins["BUR"] >= 5
    assert mins["BYZ"] >= 1
    assert mins["MNG"] >= 10


def test_null_padded_region_ids_match_rules():
    """Shapefile-style NUL padding must not break region rule matching."""
    scenario = load_scenario("official-1444")
    features = [
        _land("land_bav", country="DEU", region="DE-BY\x00\x00"),
        _land("land_mil", country="ITA", region="IT-MI\x00"),
        _land("land_sco", country="GBR", region="GB-EDH\x00\x00\x00"),
    ]
    records, stats = resolve_ownership_records(scenario, features)
    by_id = {row["province_id"]: row for row in records}
    assert by_id["land_bav"]["owner"] == "BAV"
    assert by_id["land_bav"]["assignment_source"] == "region_rule"
    assert by_id["land_mil"]["owner"] == "MLO"
    assert by_id["land_sco"]["owner"] == "SCO"
    assert stats["region_rule_hits"] == 3


def test_elevated_theaters_resolve_over_country_defaults():
    scenario = load_scenario("official-1444")
    features = [
        _land("it_rome", country="ITA", region="IT-RM"),
        _land("it_milan", country="ITA", region="IT-MI"),
        _land("it_venice", country="ITA", region="IT-VE"),
        _land("it_naples", country="ITA", region="IT-NA"),
        _land("es_granada", country="ESP", region="ES-GR"),
        _land("es_catalonia", country="ESP", region="ES-B"),
        _land("fr_burgundy", country="FRA", region="FR-21"),
        _land("fr_brittany", country="FRA", region="FR-29"),
        _land("fr_calais", country="FRA", region="FR-62"),
        _land("gb_scotland", country="GBR", region="GB-EDH"),
        _land("gb_england", country="GBR", region="GB-LND"),
        _land("nl_burg", country="NLD", region="NL-NH"),
        _land("pl_teu", country="POL", region="PL-PM"),
        _land("tr_byz", country="TUR", region="TR-34"),
    ]
    records, _stats = resolve_ownership_records(scenario, features)
    by_id = {row["province_id"]: row for row in records}
    assert by_id["it_rome"]["owner"] == "PAP"
    assert by_id["it_milan"]["owner"] == "MLO"
    assert by_id["it_venice"]["owner"] == "VEN"
    assert by_id["it_naples"]["owner"] == "NAP"
    assert by_id["es_granada"]["owner"] == "GRA"
    assert by_id["es_catalonia"]["owner"] == "ARA"
    assert by_id["fr_burgundy"]["owner"] == "BUR"
    assert by_id["fr_brittany"]["owner"] == "BRI"
    assert by_id["fr_calais"]["owner"] == "ENG"
    assert by_id["fr_calais"]["disputed"] is True
    assert by_id["gb_scotland"]["owner"] == "SCO"
    assert by_id["gb_england"]["owner"] == "ENG"
    assert by_id["nl_burg"]["owner"] == "BUR"
    assert by_id["pl_teu"]["owner"] == "TEU"
    assert by_id["tr_byz"]["owner"] == "BYZ"


def test_accuracy_label_notes_official_1444():
    label = accuracy_label(
        scenarios=("official-1444", "modern-baseline"),
        politics_tier=QUALITY_TIER_CURATED_POLITICS,
        profile_id="eu-like",
    )
    assert label["politics_quality_tier"] == "curated-politics"
    assert any("official-1444" in note for note in label["scenario_notes"])
    assert any("curated-politics" in note for note in label["scenario_notes"])
    assert any("official-1444" in s for s in label["honest_statements"])
    # 1836 and 1936 still missing from this release label
    assert any("1836" in item for item in label["do_not_claim"])


def test_accuracy_label_both_official_eras():
    label = accuracy_label(
        scenarios=("official-1444", "official-1836"),
        politics_tier=QUALITY_TIER_CURATED_POLITICS,
    )
    notes = " ".join(label["scenario_notes"])
    assert "official-1444" in notes
    assert "official-1836" in notes
    honest = " ".join(label["honest_statements"])
    assert "official-1444" in honest
    assert "official-1836" in honest
    # Only 1936 remains missing among official program eras
    dnc = " ".join(label["do_not_claim"])
    assert "1936" in dnc
    assert "curated official 1444" not in dnc or "1936" in dnc


def test_cli_scenario_list_and_validate_include_1444(capsys):
    assert main(["scenario", "list"]) == 0
    listed = capsys.readouterr().out
    assert "official-1444" in listed
    assert "curated-politics" in listed

    assert main(["scenario", "validate", "--scenario", "official-1444"]) == 0
    validated = capsys.readouterr().out
    assert "official era: yes" in validated
    assert "eu-like" in validated


def test_qa_auto_discovers_bundled_golden(tmp_path):
    province_input = tmp_path / "provinces.geojson"
    features = []
    # England bulk (GBR → ENG)
    features.extend(_land(f"eng{i}", country="GBR", region=f"GB-E{i:02d}") for i in range(25))
    # France residual (use department codes not claimed by Burgundy/Brittany/etc.)
    # Avoid FR-02/21/22/25/29/35/56/58/59/60/62/70/71/80/89/90 and Provence FR-04..06/13/83/84.
    fra_residual = [
        f"FR-{n:02d}"
        for n in (
            1, 3, 7, 8, 9, 10, 11, 12, 14, 15, 16, 17, 18, 19, 23, 24, 26, 27, 28,
            30, 31, 32, 33, 34, 36, 37, 38, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49,
            50, 51, 52, 53, 54, 55, 57, 61, 63, 64, 65, 66, 67, 68, 69, 72, 73, 74,
            75, 76, 77, 78, 79, 81, 82, 85, 86, 87, 88, 91, 92, 93, 94, 95,
        )
    ]
    features.extend(
        _land(f"fra{i}", country="FRA", region=rid) for i, rid in enumerate(fra_residual)
    )
    features.extend(_land(f"bur{i}", country="FRA", region="FR-21") for i in range(8))
    features.extend(_land(f"bri{i}", country="FRA", region="FR-29") for i in range(4))
    # Iberia
    features.extend(_land(f"cas{i}", country="ESP", region=f"ES-M{i}") for i in range(25))
    features.extend(_land(f"ara{i}", country="ESP", region="ES-B") for i in range(12))
    features.append(_land("gra", country="ESP", region="ES-GR"))
    features.extend(_land(f"por{i}", country="PRT", region=f"PT-{i:02d}") for i in range(12))
    # HRE / Austria / Bohemia / Hungary
    features.extend(_land(f"hab{i}", country="AUT", region=f"AT-{i}") for i in range(12))
    features.extend(_land(f"boh{i}", country="CZE", region=f"CZ-{i}") for i in range(8))
    features.extend(_land(f"hun{i}", country="HUN", region=f"HU-{i}") for i in range(15))
    features.append(_land("bav", country="DEU", region="DE-BY"))
    # Poland-Lithuania / Teutonic
    features.extend(_land(f"pol{i}", country="POL", region=f"PL-MZ{i}") for i in range(15))
    features.append(_land("teu", country="POL", region="PL-PM"))
    features.extend(_land(f"lit{i}", country="LTU", region=f"LT-{i}") for i in range(12))
    features.extend(_land(f"blr{i}", country="BLR", region=f"BY-{i}") for i in range(5))
    # Muscovy / Novgorod
    features.extend(_land(f"mos{i}", country="RUS", region=f"RU-MOS{i}") for i in range(20))
    features.append(_land("nov", country="RUS", region="RU-NGR"))
    # Ottomans / Byzantium / Mamluks / Ming
    features.extend(_land(f"tur{i}", country="TUR", region=f"TR-{i:02d}") for i in range(40))
    features.append(_land("byz", country="TUR", region="TR-34"))
    features.extend(_land(f"mam{i}", country="EGY", region=f"EG-{i:02d}") for i in range(15))
    features.extend(_land(f"mng{i}", country="CHN", region=f"CN-{i:02d}") for i in range(25))
    # Italy majors
    features.extend(_land(f"nap{i}", country="ITA", region="IT-NA") for i in range(12))
    features.extend(_land(f"pap{i}", country="ITA", region="IT-RM") for i in range(6))
    features.extend(_land(f"mlo{i}", country="ITA", region="IT-MI") for i in range(5))
    features.extend(_land(f"ven{i}", country="ITA", region="IT-VE") for i in range(6))
    # Scotland + Low Countries Burgundy
    features.extend(_land(f"sco{i}", country="GBR", region="GB-EDH") for i in range(8))
    features.extend(_land(f"nl{i}", country="NLD", region=f"NL-{i}") for i in range(8))

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
    result = run_scenario_politics_qa(
        "modern-small",
        "official-1444",
        province_input=province_input,
        adjacency_input=None,
        golden_input=SCENARIO_GOLDEN_DIR / "official-1444.json",
        report_output=report_output,
    )
    assert result.golden_analysis == "complete"
    assert result.passed, report_output.read_text(encoding="utf-8")


def test_scenario_definition_path_is_under_configs():
    path = SCENARIO_DIR / "official-1444.json"
    assert path.is_file()
    document = json.loads(path.read_text(encoding="utf-8"))
    assert document["official_era"] is True
    assert document["recommended_profile"] == "eu-like"


def test_demo_1444_remains_scaffold_baseline():
    """Pedagogical demo must not be re-labeled as official."""
    demo = load_scenario("demo-1444")
    assert demo["scenario_id"] == "demo-1444"
    assert demo.get("official_era") is not True
    assert demo.get("quality_tier") in (None, "scaffold-baseline")
