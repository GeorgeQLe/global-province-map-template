import csv
import json
from pathlib import Path

import pytest

from gpm.cli import main
from gpm.exporters import ExportError, export_atlas_pack
from gpm.exporters.atlas import tag_fill_color
from gpm.schemas import SchemaValidationError, validate_atlas_manifest


def test_tag_fill_color_is_deterministic_and_hex():
    first = tag_fill_color("FRA")
    second = tag_fill_color("FRA")
    assert first == second
    assert first.startswith("#")
    assert len(first) == 7
    assert tag_fill_color("ENG") != tag_fill_color("FRA")
    assert tag_fill_color("UNK") == "#8a8a8a"
    assert tag_fill_color("") == "#8a8a8a"


def test_export_atlas_pack_writes_choropleth_legend_and_tables(tmp_path):
    province_input = tmp_path / "provinces.geojson"
    output_dir = tmp_path / "atlas-out"
    _write_provinces(
        province_input,
        [
            _land("land_a", _polygon(0, 0, 1, 1), name="Alpha", region="REG-1", country="FRA"),
            _land("land_b", _polygon(1, 0, 2, 1), name="Beta", region="REG-1", country="FRA"),
            _land("land_c", _polygon(0, 1, 1, 2), name="Gamma", region="REG-2", country="GBR"),
            _land("land_d", _polygon(1, 1, 2, 2), name="Delta", region="REG-2", country="DEU"),
        ],
    )

    result = export_atlas_pack(
        "modern-small",
        province_input=province_input,
        output_dir=output_dir,
        scenarios=("modern-baseline", "demo-1444"),
    )

    assert result.province_count == 4
    assert result.scenario_ids == ("modern-baseline", "demo-1444")
    assert result.scenario_ownership_row_count == 8
    assert result.tag_count >= 2
    assert result.pack_type == "atlas"
    assert Path(result.atlas_manifest).is_file()

    manifest = json.loads(Path(result.atlas_manifest).read_text(encoding="utf-8"))
    assert manifest["milestone"] == "M10"
    assert manifest["pack_type"] == "atlas"
    assert manifest["scenarios"] == ["modern-baseline", "demo-1444"]
    assert manifest["counts"]["provinces"] == 4
    validate_atlas_manifest(manifest)

    assert (output_dir / "tables" / "provinces.csv").is_file()
    assert (output_dir / "geojson" / "provinces.geojson").is_file()
    assert (output_dir / "attribution.json").is_file()
    assert (output_dir / "README.md").is_file()

    choropleth = json.loads(
        (output_dir / "scenarios" / "demo-1444" / "ownership_choropleth.geojson").read_text()
    )
    assert choropleth["gpm"]["milestone"] == "M10"
    assert choropleth["gpm"]["layer"] == "ownership_choropleth"
    assert len(choropleth["features"]) == 4
    props_by_id = {
        feature["properties"]["province_id"]: feature["properties"]
        for feature in choropleth["features"]
    }
    # Country rule remaps modern FRA → FRA with French culture in demo-1444.
    assert props_by_id["land_a"]["owner"] == "FRA"
    assert props_by_id["land_a"]["culture"] == "french"
    assert props_by_id["land_a"]["owner_color"].startswith("#")
    assert props_by_id["land_c"]["owner"] == "ENG"
    assert props_by_id["land_c"]["culture"] == "english"

    legend = json.loads((output_dir / "scenarios" / "demo-1444" / "legend.json").read_text())
    assert legend["paint_field"] == "owner"
    assert legend["count"] >= 2
    tags = {item["tag"]: item for item in legend["tags"]}
    assert "FRA" in tags
    assert tags["FRA"]["display_name"] == "France"
    assert tags["FRA"]["owner_province_count"] == 2
    assert tags["FRA"]["fill_color"] == props_by_id["land_a"]["owner_color"]
    assert legend["styles"]["maplibre_fill_color"][0] == "match"
    assert legend["styles"]["maplibre_fill_color"][1] == ["get", "owner"]

    owners = json.loads((output_dir / "scenarios" / "demo-1444" / "owners.geojson").read_text())
    owner_tags = {feature["properties"]["owner"] for feature in owners["features"]}
    assert "FRA" in owner_tags
    assert "ENG" in owner_tags
    fra_owner = next(
        feature for feature in owners["features"] if feature["properties"]["owner"] == "FRA"
    )
    assert fra_owner["properties"]["province_count"] == 2
    assert set(fra_owner["properties"]["province_ids"]) == {"land_a", "land_b"}
    assert fra_owner["geometry"] is not None

    with (output_dir / "scenarios" / "demo-1444" / "tags.csv").open(
        newline="", encoding="utf-8"
    ) as file:
        tag_rows = list(csv.DictReader(file))
    assert any(row["tag"] == "FRA" for row in tag_rows)

    with (output_dir / "scenarios" / "demo-1444" / "ownership.csv").open(
        newline="", encoding="utf-8"
    ) as file:
        ownership_rows = list(csv.DictReader(file))
    assert len(ownership_rows) == 4
    assert "owner_color" in ownership_rows[0]

    countries = json.loads(
        (output_dir / "scenarios" / "demo-1444" / "countries.json").read_text()
    )
    assert countries["milestone"] == "M10"
    assert any(item["tag"] == "FRA" and "color" in item for item in countries["countries"])


def test_export_atlas_uncertainty_layer_flags_disputed_and_occupation(tmp_path):
    province_input = tmp_path / "provinces.geojson"
    scenario_path = tmp_path / "custom.json"
    output_dir = tmp_path / "atlas-uncertain"

    _write_provinces(
        province_input,
        [
            _land("land_a", _polygon(0, 0, 1, 1), country="FRA", region="R1"),
            _land("land_b", _polygon(1, 0, 2, 1), country="FRA", region="R1"),
            _land("land_c", _polygon(0, 1, 1, 2), country="GBR", region="R2"),
        ],
    )
    scenario_path.write_text(
        json.dumps(
            {
                "schema_version": "0.1.0",
                "scenario_id": "uncertain-demo",
                "label": "Uncertainty demo",
                "era": "test",
                "start_date": "1444-11-11",
                "end_date": None,
                "countries": {
                    "FRA": {"display_name": "France"},
                    "ENG": {"display_name": "England"},
                },
                "defaults": {"disputed": False},
                "country_rules": [
                    {
                        "match_parent_country_id": "FRA",
                        "owner": "FRA",
                        "controller": "FRA",
                        "cores": ["FRA"],
                    },
                    {
                        "match_parent_country_id": "GBR",
                        "owner": "ENG",
                        "controller": "ENG",
                        "cores": ["ENG"],
                    },
                ],
                "region_rules": [],
                "province_overrides": [
                    {
                        "province_id": "land_b",
                        "owner": "FRA",
                        "controller": "ENG",
                        "disputed": True,
                        "notes": "Occupied",
                    }
                ],
                "license_lineage": ["test scenario"],
            }
        ),
        encoding="utf-8",
    )

    # Place scenario where load_scenario can find it via path... export_atlas uses ids.
    # Copy into configs is not ideal; instead write under a temp scenario and monkeypatch is heavy.
    # Use configs by temporarily writing is risky. Prefer loading via custom scenario_id
    # by placing the file in SCENARIO_DIR is not good for tests.
    #
    # For this unit test, call export after registering the scenario next to configs using
    # monkeypatch of SCENARIO_DIR is cleaner. Simpler approach: use resolve path by writing
    # into a temporary configs dir and monkeypatch gpm.scenarios.resolve.SCENARIO_DIR.
    import gpm.exporters.atlas as atlas_mod
    import gpm.scenarios.resolve as resolve_mod

    scenario_dir = tmp_path / "scenarios"
    scenario_dir.mkdir()
    (scenario_dir / "uncertain-demo.json").write_text(
        scenario_path.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    original_load = resolve_mod.load_scenario

    def _load(scenario_id, **kwargs):
        if scenario_id == "uncertain-demo":
            return original_load(scenario_id, scenario_dir=scenario_dir)
        return original_load(scenario_id, **kwargs)

    resolve_mod.load_scenario = _load  # type: ignore[assignment]
    atlas_mod.load_scenario = _load  # type: ignore[assignment]
    try:
        result = export_atlas_pack(
            "modern-small",
            province_input=province_input,
            output_dir=output_dir,
            scenarios=("uncertain-demo",),
        )
    finally:
        resolve_mod.load_scenario = original_load  # type: ignore[assignment]
        atlas_mod.load_scenario = original_load  # type: ignore[assignment]

    uncertainty = json.loads(
        (output_dir / "scenarios" / "uncertain-demo" / "uncertainty.geojson").read_text()
    )
    assert len(uncertainty["features"]) == 1
    assert uncertainty["features"][0]["properties"]["province_id"] == "land_b"
    assert uncertainty["features"][0]["properties"]["disputed"] is True
    assert uncertainty["features"][0]["properties"]["controller"] == "ENG"
    assert result.scenario_ownership_row_count == 3


def test_export_atlas_flags_skip_optional_layers(tmp_path):
    province_input = tmp_path / "provinces.geojson"
    output_dir = tmp_path / "atlas-minimal"
    _write_provinces(
        province_input,
        [_land("land_a", _polygon(0, 0, 1, 1), country="FRA", region="R1")],
    )
    result = export_atlas_pack(
        "modern-small",
        province_input=province_input,
        output_dir=output_dir,
        scenarios=("modern-baseline",),
        include_base_geometry=False,
        include_owner_dissolve=False,
    )
    assert result.include_base_geometry is False
    assert result.include_owner_dissolve is False
    assert not (output_dir / "geojson").exists()
    assert not (output_dir / "scenarios" / "modern-baseline" / "owners.geojson").exists()
    assert (output_dir / "scenarios" / "modern-baseline" / "ownership_choropleth.geojson").is_file()


def test_export_atlas_requires_scenario_when_empty(tmp_path):
    province_input = tmp_path / "provinces.geojson"
    _write_provinces(
        province_input,
        [_land("land_a", _polygon(0, 0, 1, 1), country="FRA")],
    )
    with pytest.raises(ExportError, match="at least one scenario"):
        export_atlas_pack(
            "modern-small",
            province_input=province_input,
            output_dir=tmp_path / "out",
            scenarios=(),
        )


def test_export_atlas_cli_json(tmp_path, capsys):
    province_input = tmp_path / "provinces.geojson"
    output_dir = tmp_path / "cli-atlas"
    _write_provinces(
        province_input,
        [
            _land("land_a", _polygon(0, 0, 1, 1), country="FRA", region="R1"),
            _land("land_b", _polygon(1, 0, 2, 1), country="GBR", region="R2"),
        ],
    )
    assert (
        main(
            [
                "export",
                "atlas",
                "--profile",
                "modern-small",
                "--province-input",
                str(province_input),
                "--output-dir",
                str(output_dir),
                "--scenario",
                "modern-baseline",
                "--scenario",
                "demo-1444",
                "--format",
                "json",
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["pack_type"] == "atlas"
    assert payload["scenario_ids"] == ["modern-baseline", "demo-1444"]
    assert payload["province_count"] == 2
    assert (output_dir / "atlas_manifest.json").is_file()


def test_validate_atlas_manifest_rejects_bad_pack_type():
    with pytest.raises(SchemaValidationError):
        validate_atlas_manifest(
            {
                "schema_version": "0.1.0",
                "milestone": "M10",
                "pack_type": "game-template",
                "profile_id": "modern-small",
                "generated_at": "2026-07-10T00:00:00+00:00",
                "generator_version": "0.1.0",
                "scenarios": ["modern-baseline"],
                "counts": {
                    "provinces": 1,
                    "scenarios": 1,
                    "scenario_ownership_rows": 1,
                    "unique_tags": 1,
                    "legend_entries": 1,
                    "attribution_records": 1,
                },
                "files": ["atlas_manifest.json"],
            }
        )


def _polygon(x0, y0, x1, y1):
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [x0, y0],
                [x1, y0],
                [x1, y1],
                [x0, y1],
                [x0, y0],
            ]
        ],
    }


def _land(province_id, geometry, *, name=None, region="R1", country="AAA"):
    return {
        "type": "Feature",
        "geometry": geometry,
        "properties": {
            "province_id": province_id,
            "display_name": name or province_id,
            "kind": "land",
            "parent_region_id": region,
            "parent_country_id": country,
            "area_sq_km": 100.0,
            "estimated_population": 1000,
            "terrain_class": "plains",
            "coastal": False,
            "island": False,
            "source_lineage": ["natural_earth:test"],
            "license_lineage": ["Natural Earth public domain"],
        },
    }


def _write_provinces(path: Path, features: list[dict]) -> None:
    path.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": features,
            }
        ),
        encoding="utf-8",
    )
