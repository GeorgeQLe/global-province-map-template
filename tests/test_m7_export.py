import csv
import json
from pathlib import Path

from gpm.cli import main
from gpm.config import export_settings, load_profile
from gpm.exporters import export_game_pack, export_geojson_pack


def test_export_settings_resolve_layout_presets():
    modern = export_settings(load_profile("modern-small"))
    assert modern["layout"] == "generic"
    assert modern["region_type"] == "region"
    assert modern["include_sea_zones"] is True

    victoria = export_settings(load_profile("victoria-like"))
    assert victoria["layout"] == "victoria-like"
    assert victoria["region_type"] == "state"

    hoi = export_settings(load_profile("hoi-like"))
    assert hoi["layout"] == "hoi-like"
    assert hoi["region_type"] == "strategic_region"

    eu = export_settings(load_profile("eu-like"))
    assert eu["layout"] == "eu-like"
    assert eu["region_type"] == "region"


def test_export_game_pack_writes_definitions_regions_localization(tmp_path):
    province_input = tmp_path / "provinces.geojson"
    adjacency_input = tmp_path / "adjacency.csv"
    sea_input = tmp_path / "sea_zones.geojson"
    output_dir = tmp_path / "exports" / "modern-small"

    _write_provinces(
        province_input,
        [
            _land("land_a", _polygon(0, 0, 1, 1), name="Alpha", region="REG-1", country="AAA"),
            _land("land_b", _polygon(1, 0, 2, 1), name="Beta", region="REG-1", country="AAA"),
            _land("land_c", _polygon(0, 1, 1, 2), name="Gamma", region="REG-2", country="AAA"),
        ],
    )
    _write_seas(
        sea_input,
        [
            _sea("sea_a", _polygon(-0.5, -0.5, 0, 0), parent="land_a"),
        ],
    )
    _write_adjacency(
        adjacency_input,
        [
            {
                "from_province_id": "land_a",
                "to_province_id": "land_b",
                "adjacency_type": "land",
                "bidirectional": "true",
                "crossing_type": "shared_border",
                "shared_border_km": "1.0",
                "source_lineage": '["test"]',
            }
        ],
    )

    result = export_game_pack(
        "modern-small",
        province_input=province_input,
        sea_input=sea_input,
        adjacency_input=adjacency_input,
        output_dir=output_dir,
    )

    assert result.province_count == 3
    assert result.sea_zone_count == 1
    assert result.region_count == 2
    assert result.adjacency_count == 1
    assert result.localization_entry_count == 3 + 1 + 2
    assert result.layout == "generic"
    assert result.region_type == "region"
    assert Path(result.pack_manifest).is_file()

    manifest = json.loads(Path(result.pack_manifest).read_text(encoding="utf-8"))
    assert manifest["milestone"] == "M7"
    assert manifest["pack_type"] == "game-template"
    assert manifest["counts"]["regions"] == 2

    provinces_geo = json.loads((output_dir / "geojson" / "provinces.geojson").read_text())
    assert provinces_geo["gpm"]["milestone"] == "M7"
    assert len(provinces_geo["features"]) == 3

    regions_geo = json.loads((output_dir / "geojson" / "regions.geojson").read_text())
    region_props = [feature["properties"] for feature in regions_geo["features"]]
    assert {item["region_id"] for item in region_props} == {"REG-1", "REG-2"}
    assert all(item["region_type"] == "region" for item in region_props)
    reg1_feature = next(
        feature
        for feature in regions_geo["features"]
        if feature["properties"]["region_id"] == "REG-1"
    )
    assert reg1_feature["properties"]["province_ids"] == ["land_a", "land_b"]
    assert reg1_feature["geometry"] is not None

    province_defs = json.loads((output_dir / "definitions" / "provinces.json").read_text())
    assert province_defs["count"] == 3
    assert {item["province_id"] for item in province_defs["provinces"]} == {
        "land_a",
        "land_b",
        "land_c",
    }

    localization = json.loads((output_dir / "localization" / "english.json").read_text())
    keys = {entry["key"] for entry in localization["entries"]}
    assert "PROVINCE_land_a" in keys
    assert "REGION_REG-1" in keys
    assert "SEA_sea_a" in keys
    yml = (output_dir / "localization" / "english.yml").read_text(encoding="utf-8")
    assert yml.startswith("l_english:")
    assert 'PROVINCE_land_a:0 "Alpha"' in yml

    with (output_dir / "definitions" / "adjacency.csv").open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    assert len(rows) == 1
    assert rows[0]["from_province_id"] == "land_a"

    attribution = json.loads((output_dir / "attribution.json").read_text())
    assert attribution["schema_version"] == "0.1.0"
    assert attribution["records"]
    assert all("attribution_text" in record for record in attribution["records"])

    assert (output_dir / "tables" / "terrain.csv").is_file()
    assert (output_dir / "tables" / "population.csv").is_file()
    assert (output_dir / "README.md").is_file()


def test_export_geojson_only_skips_definitions(tmp_path):
    province_input = tmp_path / "provinces.geojson"
    output_dir = tmp_path / "geojson-pack"
    _write_provinces(
        province_input,
        [
            _land("land_a", _polygon(0, 0, 1, 1), region="R1"),
            _land("land_b", _polygon(1, 0, 2, 1), region="R1"),
        ],
    )
    result = export_geojson_pack(
        "modern-small",
        province_input=province_input,
        output_dir=output_dir,
    )
    assert result.adjacency_count == 0
    assert result.localization_entry_count == 0
    assert (output_dir / "geojson" / "provinces.geojson").is_file()
    assert (output_dir / "geojson" / "regions.geojson").is_file()
    assert not (output_dir / "definitions").exists()
    assert not (output_dir / "localization").exists()
    manifest = json.loads(Path(result.pack_manifest).read_text(encoding="utf-8"))
    assert manifest["pack_type"] == "geojson"


def test_export_pack_profile_specific_region_type(tmp_path):
    province_input = tmp_path / "provinces.geojson"
    _write_provinces(
        province_input,
        [_land("land_a", _polygon(0, 0, 1, 1), region="S1")],
    )
    hoi_dir = tmp_path / "hoi"
    result = export_game_pack(
        "hoi-like",
        province_input=province_input,
        output_dir=hoi_dir,
    )
    assert result.region_type == "strategic_region"
    regions = json.loads((hoi_dir / "geojson" / "regions.geojson").read_text())
    assert regions["features"][0]["properties"]["region_type"] == "strategic_region"

    victoria_dir = tmp_path / "victoria"
    result = export_game_pack(
        "victoria-like",
        province_input=province_input,
        output_dir=victoria_dir,
    )
    assert result.region_type == "state"
    regions = json.loads((victoria_dir / "geojson" / "regions.geojson").read_text())
    assert regions["features"][0]["properties"]["region_type"] == "state"


def test_export_pack_is_deterministic(tmp_path):
    province_input = tmp_path / "provinces.geojson"
    _write_provinces(
        province_input,
        [
            _land("land_b", _polygon(1, 0, 2, 1), region="R1", name="B"),
            _land("land_a", _polygon(0, 0, 1, 1), region="R1", name="A"),
        ],
    )
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first = export_game_pack(
        "modern-small",
        province_input=province_input,
        output_dir=first_dir,
    )
    second = export_game_pack(
        "modern-small",
        province_input=province_input,
        output_dir=second_dir,
    )
    # Timestamps differ; compare stable definition payloads.
    first_defs = json.loads((first_dir / "definitions" / "provinces.json").read_text())
    second_defs = json.loads((second_dir / "definitions" / "provinces.json").read_text())
    first_defs.pop("generated_at", None)
    second_defs.pop("generated_at", None)
    assert first_defs == second_defs
    assert first.province_count == second.province_count
    assert first.region_count == second.region_count

    first_loc = json.loads((first_dir / "localization" / "english.json").read_text())
    second_loc = json.loads((second_dir / "localization" / "english.json").read_text())
    first_loc.pop("generated_at", None)
    second_loc.pop("generated_at", None)
    assert first_loc == second_loc


def test_export_pack_cli_json(tmp_path, capsys):
    province_input = tmp_path / "provinces.geojson"
    output_dir = tmp_path / "pack-out"
    _write_provinces(
        province_input,
        [
            _land("land_a", _polygon(0, 0, 1, 1), region="R1"),
            _land("land_b", _polygon(1, 0, 2, 1), region="R2"),
        ],
    )
    assert (
        main(
            [
                "export",
                "pack",
                "--profile",
                "modern-small",
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
    assert summary["profile_id"] == "modern-small"
    assert summary["province_count"] == 2
    assert summary["region_count"] == 2
    assert Path(summary["pack_manifest"]).is_file()
    assert (output_dir / "definitions" / "provinces.json").is_file()


def test_export_geojson_cli_json(tmp_path, capsys):
    province_input = tmp_path / "provinces.geojson"
    output_dir = tmp_path / "geo-out"
    _write_provinces(
        province_input,
        [_land("land_a", _polygon(0, 0, 1, 1), region="R1")],
    )
    assert (
        main(
            [
                "export",
                "geojson",
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
    assert summary["province_count"] == 1
    assert summary["localization_entry_count"] == 0
    assert (output_dir / "geojson" / "provinces.geojson").is_file()


def test_export_pack_cli_reports_missing_provinces(tmp_path, capsys):
    assert (
        main(
            [
                "export",
                "pack",
                "--province-input",
                str(tmp_path / "missing.geojson"),
            ]
        )
        == 1
    )
    captured = capsys.readouterr()
    assert "does not exist" in captured.err
    assert "Traceback" not in captured.err


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


def _write_seas(path: Path, features: list[dict]) -> None:
    path.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "name": "sea_zones",
                "gpm": {"profile_id": "modern-small", "milestone": "M6"},
                "features": features,
            }
        ),
        encoding="utf-8",
    )


def _write_adjacency(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "from_province_id",
        "to_province_id",
        "adjacency_type",
        "bidirectional",
        "crossing_type",
        "shared_border_km",
        "source_lineage",
    ]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _land(
    province_id: str,
    geometry: dict,
    *,
    name: str | None = None,
    region: str = "REG-1",
    country: str = "AAA",
) -> dict:
    return {
        "type": "Feature",
        "geometry": geometry,
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


def _sea(province_id: str, geometry: dict, *, parent: str) -> dict:
    return {
        "type": "Feature",
        "geometry": geometry,
        "properties": {
            "province_id": province_id,
            "display_name": f"Waters of {parent}",
            "kind": "sea",
            "parent_country_id": "AAA",
            "parent_region_id": "REG-1",
            "area_sq_km": 250.0,
            "estimated_population": None,
            "terrain_class": "ocean",
            "coastal": False,
            "island": False,
            "sea_class": "coastal",
            "parent_land_province_id": parent,
            "source_lineage": [f"source:{province_id}"],
            "license_lineage": ["Natural Earth public domain"],
        },
    }


def _polygon(minx: float, miny: float, maxx: float, maxy: float) -> dict:
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [minx, miny],
                [maxx, miny],
                [maxx, maxy],
                [minx, maxy],
                [minx, miny],
            ]
        ],
    }
