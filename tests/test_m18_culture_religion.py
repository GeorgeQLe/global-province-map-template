"""M18 culture / religion atlas paint layers."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from gpm.cli import main
from gpm.exporters import ExportError, export_atlas_pack
from gpm.exporters.atlas import (
    OWNERSHIP_TABLE_FIELDS,
    OWNERSHIP_TABLE_FIELDS_BASE,
    identity_fill_color,
    tag_fill_color,
)
from gpm.schemas import validate_atlas_manifest


def test_identity_fill_color_null_and_deterministic():
    assert identity_fill_color(None) == "#8a8a8a"
    assert identity_fill_color("") == "#8a8a8a"
    assert identity_fill_color("   ") == "#8a8a8a"
    assert identity_fill_color("french") == tag_fill_color("french")
    assert identity_fill_color("french") == identity_fill_color("french")
    assert identity_fill_color("french") != identity_fill_color("english")


def test_export_atlas_identity_paint_default(tmp_path):
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
        scenarios=("demo-1444", "modern-baseline"),
    )

    assert result.include_identity_paint is True
    assert result.include_identity_dissolve is True
    assert result.unique_culture_count >= 1
    assert result.unique_religion_count >= 1

    manifest = json.loads(Path(result.atlas_manifest).read_text(encoding="utf-8"))
    assert manifest["milestone"] == "M18"
    assert manifest["include_identity_paint"] is True
    assert manifest["include_identity_dissolve"] is True
    assert manifest["counts"]["unique_cultures"] >= 1
    validate_atlas_manifest(manifest)

    scenario_dir = output_dir / "scenarios" / "demo-1444"
    for name in (
        "culture_legend.json",
        "religion_legend.json",
        "cultures.csv",
        "religions.csv",
        "cultures.geojson",
        "religions.geojson",
    ):
        assert (scenario_dir / name).is_file(), name

    choropleth = json.loads(
        (scenario_dir / "ownership_choropleth.geojson").read_text(encoding="utf-8")
    )
    assert choropleth["gpm"]["milestone"] == "M18"
    assert set(choropleth["gpm"]["paint_fields"]) == {
        "owner",
        "controller",
        "culture",
        "religion",
    }
    props_by_id = {
        feature["properties"]["province_id"]: feature["properties"]
        for feature in choropleth["features"]
    }
    assert props_by_id["land_a"]["culture"] == "french"
    assert props_by_id["land_a"]["culture_color"] == identity_fill_color("french")
    assert props_by_id["land_a"]["religion_color"] == identity_fill_color(
        props_by_id["land_a"]["religion"]
    )
    # modern-baseline has null culture → unassigned gray
    baseline = json.loads(
        (
            output_dir / "scenarios" / "modern-baseline" / "ownership_choropleth.geojson"
        ).read_text(encoding="utf-8")
    )
    for feature in baseline["features"]:
        assert feature["properties"]["culture_color"] == "#8a8a8a"
        assert feature["properties"]["religion_color"] == "#8a8a8a"

    culture_legend = json.loads(
        (scenario_dir / "culture_legend.json").read_text(encoding="utf-8")
    )
    assert culture_legend["paint_field"] == "culture"
    assert culture_legend["color_field"] == "culture_color"
    assert culture_legend["unassigned_color"] == "#8a8a8a"
    assert culture_legend["count"] >= 1
    assert culture_legend["styles"]["maplibre_fill_color_property"] == [
        "get",
        "culture_color",
    ]
    ids = {entry["id"] for entry in culture_legend["entries"]}
    assert "french" in ids
    french = next(e for e in culture_legend["entries"] if e["id"] == "french")
    assert french["fill_color"] == identity_fill_color("french")
    assert french["province_count"] >= 1

    owner_legend = json.loads((scenario_dir / "legend.json").read_text(encoding="utf-8"))
    assert owner_legend["paint_field"] == "owner"
    assert "tags" in owner_legend
    assert "entries" not in owner_legend

    cultures_geo = json.loads(
        (scenario_dir / "cultures.geojson").read_text(encoding="utf-8")
    )
    assert cultures_geo["gpm"]["dissolve"] == "culture"
    culture_ids = {
        feature["properties"].get("culture") for feature in cultures_geo["features"]
    }
    assert "french" in culture_ids

    with (scenario_dir / "ownership.csv").open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    assert "culture_color" in rows[0]
    assert "religion_color" in rows[0]
    assert list(rows[0].keys())[-2:] == ["culture_color", "religion_color"]

    scenario_manifest = json.loads(
        (scenario_dir / "scenario_manifest.json").read_text(encoding="utf-8")
    )
    assert scenario_manifest["milestone"] == "M18"
    modes = {mode["field"]: mode for mode in scenario_manifest["paint"]["modes"]}
    assert set(modes) == {"owner", "controller", "culture", "religion"}
    assert modes["culture"]["legend"] == "culture_legend.json"
    assert modes["culture"]["dissolve"] == "cultures.geojson"
    assert modes["controller"]["legend"] is None
    assert "unique_cultures" in scenario_manifest["counts"]
    assert "culture_legend.json" in scenario_manifest["files"]
    assert "cultures.geojson" in scenario_manifest["files"]
    # files inventory matches written files
    on_disk = sorted(p.name for p in scenario_dir.iterdir() if p.is_file())
    assert scenario_manifest["files"] == on_disk


def test_export_atlas_no_identity_paint_restores_m10_surface(tmp_path):
    province_input = tmp_path / "provinces.geojson"
    output_dir = tmp_path / "atlas-m10"
    _write_provinces(
        province_input,
        [
            _land("land_a", _polygon(0, 0, 1, 1), country="FRA", region="R1"),
            _land("land_b", _polygon(1, 0, 2, 1), country="GBR", region="R2"),
        ],
    )
    result = export_atlas_pack(
        "modern-small",
        province_input=province_input,
        output_dir=output_dir,
        scenarios=("demo-1444",),
        include_identity_paint=False,
    )
    assert result.include_identity_paint is False
    assert result.include_identity_dissolve is False
    assert result.unique_culture_count == 0

    scenario_dir = output_dir / "scenarios" / "demo-1444"
    for name in (
        "culture_legend.json",
        "religion_legend.json",
        "cultures.csv",
        "religions.csv",
        "cultures.geojson",
        "religions.geojson",
    ):
        assert not (scenario_dir / name).exists()

    choropleth = json.loads(
        (scenario_dir / "ownership_choropleth.geojson").read_text(encoding="utf-8")
    )
    props = choropleth["features"][0]["properties"]
    assert "culture_color" not in props
    assert "religion_color" not in props
    assert "culture" in props  # data still present
    assert choropleth["gpm"]["paint_fields"] == ["owner", "controller"]

    with (scenario_dir / "ownership.csv").open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    assert "culture_color" not in rows[0]
    assert "owner_color" in rows[0]
    assert list(rows[0].keys()) == list(OWNERSHIP_TABLE_FIELDS_BASE)

    scenario_manifest = json.loads(
        (scenario_dir / "scenario_manifest.json").read_text(encoding="utf-8")
    )
    mode_fields = [m["field"] for m in scenario_manifest["paint"]["modes"]]
    assert mode_fields == ["owner", "controller"]
    assert "unique_cultures" not in scenario_manifest["counts"]


def test_export_atlas_no_identity_dissolve_keeps_legends(tmp_path):
    province_input = tmp_path / "provinces.geojson"
    output_dir = tmp_path / "atlas-no-dissolve"
    _write_provinces(
        province_input,
        [_land("land_a", _polygon(0, 0, 1, 1), country="FRA", region="R1")],
    )
    result = export_atlas_pack(
        "modern-small",
        province_input=province_input,
        output_dir=output_dir,
        scenarios=("demo-1444",),
        include_identity_dissolve=False,
    )
    assert result.include_identity_paint is True
    assert result.include_identity_dissolve is False
    scenario_dir = output_dir / "scenarios" / "demo-1444"
    assert (scenario_dir / "culture_legend.json").is_file()
    assert not (scenario_dir / "cultures.geojson").exists()
    assert not (scenario_dir / "religions.geojson").exists()
    scenario_manifest = json.loads(
        (scenario_dir / "scenario_manifest.json").read_text(encoding="utf-8")
    )
    culture_mode = next(
        m for m in scenario_manifest["paint"]["modes"] if m["field"] == "culture"
    )
    assert culture_mode["dissolve"] is None


def test_identity_dissolve_includes_unassigned(tmp_path):
    province_input = tmp_path / "provinces.geojson"
    output_dir = tmp_path / "atlas-unassigned"
    _write_provinces(
        province_input,
        [
            _land("land_a", _polygon(0, 0, 1, 1), country="FRA", region="R1"),
            _land("land_b", _polygon(1, 0, 2, 1), country="DEU", region="R2"),
        ],
    )
    # demo-1444 assigns culture for FRA/GBR-like rules; DEU may fall to defaults
    result = export_atlas_pack(
        "modern-small",
        province_input=province_input,
        output_dir=output_dir,
        scenarios=("modern-baseline",),
    )
    assert result.include_identity_paint is True
    cultures = json.loads(
        (
            output_dir / "scenarios" / "modern-baseline" / "cultures.geojson"
        ).read_text(encoding="utf-8")
    )
    unassigned = [
        f
        for f in cultures["features"]
        if f["properties"].get("is_unassigned") is True
    ]
    assert len(unassigned) == 1
    assert unassigned[0]["properties"]["culture"] is None
    assert unassigned[0]["properties"]["culture_color"] == "#8a8a8a"
    assert unassigned[0]["properties"]["display_name"] == "unassigned"
    assert unassigned[0]["properties"]["province_count"] == 2


def test_export_atlas_cli_identity_flags(tmp_path, capsys):
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
                "demo-1444",
                "--no-identity-dissolve",
                "--format",
                "json",
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["include_identity_paint"] is True
    assert payload["include_identity_dissolve"] is False
    assert payload["unique_culture_count"] >= 1
    assert (output_dir / "scenarios" / "demo-1444" / "culture_legend.json").is_file()
    assert not (output_dir / "scenarios" / "demo-1444" / "cultures.geojson").exists()

    out2 = tmp_path / "cli-no-paint"
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
                str(out2),
                "--scenario",
                "demo-1444",
                "--no-identity-paint",
                "--format",
                "json",
            ]
        )
        == 0
    )
    payload2 = json.loads(capsys.readouterr().out)
    assert payload2["include_identity_paint"] is False
    assert payload2["include_identity_dissolve"] is False


def test_ownership_table_fields_include_identity_colors():
    assert OWNERSHIP_TABLE_FIELDS[-2:] == ("culture_color", "religion_color")
    assert "culture_color" not in OWNERSHIP_TABLE_FIELDS_BASE


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
        },
    }


def _write_provinces(path: Path, features: list[dict]) -> None:
    path.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": features,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
