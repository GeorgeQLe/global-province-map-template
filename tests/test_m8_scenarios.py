import csv
import json
from pathlib import Path

import pytest

from gpm.cli import main
from gpm.exporters import export_game_pack
from gpm.scenarios import (
    ScenarioError,
    build_scenario_ownership,
    list_scenarios,
    load_scenario,
    resolve_ownership_records,
    validate_scenario_document,
)
from gpm.schemas import SchemaValidationError, validate_scenario_definition


def test_bundled_scenarios_list_and_validate():
    summaries = list_scenarios()
    ids = {item.scenario_id for item in summaries}
    assert "modern-baseline" in ids
    assert "demo-1444" in ids
    assert "official-1836" in ids

    modern = load_scenario("modern-baseline")
    assert modern["era"] == "modern"
    assert modern["country_rules"] == []

    demo = load_scenario("demo-1444")
    assert demo["era"] == "1444"
    assert any(rule["match_parent_country_id"] == "FRA" for rule in demo["country_rules"])
    validate_scenario_document(demo)
    validate_scenario_definition(demo)

    official = load_scenario("official-1836")
    assert official["era"] == "1836"
    assert official["quality_tier"] == "curated-politics"
    assert official["official_era"] is True
    validate_scenario_document(official)
    validate_scenario_definition(official)


def test_resolve_ownership_baseline_country_region_and_province_layers():
    scenario = {
        "schema_version": "0.1.0",
        "scenario_id": "test-layering",
        "label": "Layering test",
        "era": "test",
        "start_date": "1444-11-11",
        "end_date": None,
        "defaults": {"culture": None, "religion": "catholic", "disputed": False},
        "countries": {
            "FRA": {"display_name": "France"},
            "ENG": {"display_name": "England"},
            "BUR": {"display_name": "Burgundy"},
        },
        "country_rules": [
            {
                "match_parent_country_id": "FRA",
                "owner": "FRA",
                "controller": "FRA",
                "cores": ["FRA"],
                "culture": "french",
            }
        ],
        "region_rules": [
            {
                "match_parent_region_id": "FR-HDF",
                "owner": "BUR",
                "controller": "BUR",
                "cores": ["BUR", "FRA"],
                "culture": "burgundian",
            }
        ],
        "province_overrides": [
            {
                "province_id": "land_c",
                "owner": "ENG",
                "controller": "ENG",
                "cores": ["ENG", "FRA"],
                "claims": ["FRA"],
                "disputed": True,
                "notes": "Occupied",
            }
        ],
    }
    features = [
        _land("land_a", country="FRA", region="FR-IDF"),
        _land("land_b", country="FRA", region="FR-HDF"),
        _land("land_c", country="FRA", region="FR-NOR"),
        _land("land_d", country="DEU", region="DE-BE"),
        _sea("sea_a"),
    ]
    # resolve only considers land features passed in; caller filters seas.
    land_only = [feature for feature in features if feature["properties"]["kind"] == "land"]
    records, stats = resolve_ownership_records(scenario, land_only)

    by_id = {row["province_id"]: row for row in records}
    assert set(by_id) == {"land_a", "land_b", "land_c", "land_d"}

    assert by_id["land_a"]["owner"] == "FRA"
    assert by_id["land_a"]["assignment_source"] == "country_rule"
    assert by_id["land_a"]["culture"] == "french"
    assert by_id["land_a"]["religion"] == "catholic"

    assert by_id["land_b"]["owner"] == "BUR"
    assert by_id["land_b"]["assignment_source"] == "region_rule"
    assert by_id["land_b"]["cores"] == ["BUR", "FRA"]
    assert by_id["land_b"]["culture"] == "burgundian"

    assert by_id["land_c"]["owner"] == "ENG"
    assert by_id["land_c"]["controller"] == "ENG"
    assert by_id["land_c"]["assignment_source"] == "province_override"
    assert by_id["land_c"]["disputed"] is True
    assert by_id["land_c"]["claims"] == ["FRA"]

    assert by_id["land_d"]["owner"] == "DEU"
    assert by_id["land_d"]["assignment_source"] == "baseline"
    assert by_id["land_d"]["cores"] == ["DEU"]

    assert stats["country_rule_hits"] == 3  # a, b, c all FRA before region/province win
    assert stats["region_rule_hits"] == 1
    assert stats["province_override_hits"] == 1
    assert stats["baseline_only_count"] == 1


def test_unknown_province_override_errors_unless_allowed():
    scenario = {
        "schema_version": "0.1.0",
        "scenario_id": "unknown-override",
        "label": "Unknown override",
        "era": "test",
        "start_date": "1444-11-11",
        "province_overrides": [{"province_id": "missing", "owner": "ENG"}],
    }
    features = [_land("land_a", country="FRA", region="FR-IDF")]
    with pytest.raises(ScenarioError, match="unknown land province_id"):
        resolve_ownership_records(scenario, features)

    records, stats = resolve_ownership_records(
        scenario,
        features,
        allow_unknown_overrides=True,
    )
    assert len(records) == 1
    assert stats["unknown_override_count"] == 1
    assert records[0]["owner"] == "FRA"


def test_build_scenario_ownership_writes_outputs(tmp_path):
    province_input = tmp_path / "provinces.geojson"
    output_dir = tmp_path / "scenarios" / "modern-baseline"
    _write_provinces(
        province_input,
        [
            _land("land_a", country="FRA", region="FR-IDF", name="Paris"),
            _land("land_b", country="DEU", region="DE-BE", name="Berlin"),
            _sea("sea_a"),
        ],
    )

    result = build_scenario_ownership(
        "modern-baseline",
        profile_id="modern-small",
        province_input=province_input,
        output_dir=output_dir,
    )
    assert result.land_province_count == 2
    assert result.ownership_row_count == 2
    assert result.baseline_only_count == 2
    assert Path(result.ownership_csv).is_file()
    assert Path(result.ownership_json).is_file()
    assert Path(result.countries_json).is_file()
    assert Path(result.scenario_manifest).is_file()

    with Path(result.ownership_csv).open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    assert {row["province_id"] for row in rows} == {"land_a", "land_b"}
    assert {row["owner"] for row in rows} == {"FRA", "DEU"}
    assert all(row["assignment_source"] == "baseline" for row in rows)

    ownership = json.loads(Path(result.ownership_json).read_text(encoding="utf-8"))
    assert ownership["milestone"] == "M8"
    assert ownership["count"] == 2

    manifest = json.loads(Path(result.scenario_manifest).read_text(encoding="utf-8"))
    assert manifest["scenario_id"] == "modern-baseline"
    assert manifest["counts"]["ownership_rows"] == 2


def test_build_demo_1444_applies_country_and_region_rules(tmp_path):
    province_input = tmp_path / "provinces.geojson"
    output_dir = tmp_path / "demo"
    _write_provinces(
        province_input,
        [
            _land("land_paris", country="FRA", region="FR-IDF"),
            _land("land_lille", country="FRA", region="FR-HDF"),
            _land("land_madrid", country="ESP", region="ES-MD"),
            _land("land_barcelona", country="ESP", region="ES-CT"),
            _land("land_berlin", country="DEU", region="DE-BE"),
        ],
    )
    result = build_scenario_ownership(
        "demo-1444",
        profile_id="eu-like",
        province_input=province_input,
        output_dir=output_dir,
    )
    ownership = json.loads(Path(result.ownership_json).read_text(encoding="utf-8"))
    by_id = {row["province_id"]: row for row in ownership["records"]}
    assert by_id["land_paris"]["owner"] == "FRA"
    assert by_id["land_paris"]["assignment_source"] == "country_rule"
    assert by_id["land_lille"]["owner"] == "BUR"
    assert by_id["land_lille"]["assignment_source"] == "region_rule"
    assert by_id["land_madrid"]["owner"] == "CAS"
    assert by_id["land_barcelona"]["owner"] == "ARA"
    assert by_id["land_berlin"]["owner"] == "DEU"
    assert by_id["land_berlin"]["assignment_source"] == "baseline"


def test_scenario_cli_list_validate_build(tmp_path, capsys):
    assert main(["scenario", "list", "--format", "json"]) == 0
    listed = json.loads(capsys.readouterr().out)
    assert {item["scenario_id"] for item in listed} >= {"modern-baseline", "demo-1444"}

    assert main(["scenario", "validate", "--scenario", "demo-1444", "--format", "json"]) == 0
    validated = json.loads(capsys.readouterr().out)
    assert validated["valid"] is True
    assert validated["scenario_id"] == "demo-1444"

    province_input = tmp_path / "provinces.geojson"
    output_dir = tmp_path / "out"
    _write_provinces(
        province_input,
        [_land("land_a", country="FRA", region="FR-IDF")],
    )
    assert (
        main(
            [
                "scenario",
                "build",
                "--scenario",
                "modern-baseline",
                "--province-input",
                str(province_input),
                "--output-dir",
                str(output_dir),
                "--format",
                "json",
            ]
        )
        == 0
    )
    summary = json.loads(capsys.readouterr().out)
    assert summary["ownership_row_count"] == 1
    assert (output_dir / "ownership.csv").is_file()


def test_scenario_cli_reports_missing_provinces(tmp_path, capsys):
    assert (
        main(
            [
                "scenario",
                "build",
                "--scenario",
                "modern-baseline",
                "--province-input",
                str(tmp_path / "missing.geojson"),
            ]
        )
        == 1
    )
    captured = capsys.readouterr()
    assert "does not exist" in captured.err
    assert "Traceback" not in captured.err


def test_export_pack_embeds_scenarios(tmp_path):
    province_input = tmp_path / "provinces.geojson"
    output_dir = tmp_path / "pack"
    _write_provinces(
        province_input,
        [
            _land("land_a", country="FRA", region="FR-IDF"),
            _land("land_b", country="GBR", region="GB-ENG"),
        ],
    )
    result = export_game_pack(
        "eu-like",
        province_input=province_input,
        output_dir=output_dir,
        scenarios=("modern-baseline", "demo-1444"),
    )
    assert result.scenario_ids == ("modern-baseline", "demo-1444")
    assert result.scenario_ownership_row_count == 4
    assert (output_dir / "scenarios" / "modern-baseline" / "ownership.csv").is_file()
    assert (output_dir / "scenarios" / "demo-1444" / "ownership.json").is_file()
    manifest = json.loads(Path(result.pack_manifest).read_text(encoding="utf-8"))
    assert manifest["milestone"] == "M8"
    assert manifest["scenarios"] == ["modern-baseline", "demo-1444"]
    assert "scenarios/demo-1444/ownership.csv" in manifest["files"]


def test_export_pack_cli_with_scenario(tmp_path, capsys):
    province_input = tmp_path / "provinces.geojson"
    output_dir = tmp_path / "pack-out"
    _write_provinces(
        province_input,
        [_land("land_a", country="FRA", region="FR-IDF")],
    )
    assert (
        main(
            [
                "export",
                "pack",
                "--profile",
                "eu-like",
                "--province-input",
                str(province_input),
                "--output-dir",
                str(output_dir),
                "--scenario",
                "modern-baseline",
                "--format",
                "json",
            ]
        )
        == 0
    )
    summary = json.loads(capsys.readouterr().out)
    assert summary["scenario_ids"] == ["modern-baseline"]
    assert summary["scenario_ownership_row_count"] == 1
    assert (output_dir / "scenarios" / "modern-baseline" / "ownership.csv").is_file()


def test_invalid_scenario_document_raises():
    with pytest.raises(ScenarioError):
        validate_scenario_document({"schema_version": "0.1.0"})
    with pytest.raises(SchemaValidationError):
        validate_scenario_definition({"schema_version": "0.1.0", "scenario_id": "x"})


def _write_provinces(path: Path, features: list[dict]) -> None:
    path.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "name": "provinces",
                "gpm": {"profile_id": "modern-small", "id_scheme": "test"},
                "features": features,
            }
        ),
        encoding="utf-8",
    )


def _land(
    province_id: str,
    *,
    country: str = "AAA",
    region: str = "REG-1",
    name: str | None = None,
) -> dict:
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
            "parent_country_id": country,
            "parent_region_id": region,
            "area_sq_km": 1000.0,
            "estimated_population": 5000.0,
            "terrain_class": "plains",
            "coastal": False,
            "island": False,
            "source_lineage": [f"source:{province_id}"],
            "license_lineage": ["Natural Earth public domain"],
        },
    }


def _sea(province_id: str) -> dict:
    return {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[-1, -1], [0, -1], [0, 0], [-1, 0], [-1, -1]]],
        },
        "properties": {
            "province_id": province_id,
            "display_name": province_id,
            "kind": "sea",
            "parent_country_id": None,
            "parent_region_id": None,
            "area_sq_km": 250.0,
            "estimated_population": None,
            "terrain_class": "ocean",
            "coastal": False,
            "island": False,
            "sea_class": "ocean",
            "source_lineage": [f"source:{province_id}"],
            "license_lineage": ["Natural Earth public domain"],
        },
    }
