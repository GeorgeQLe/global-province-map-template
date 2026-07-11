import csv
import json
from pathlib import Path

from gpm.builders.adjacency import build_land_adjacency
from gpm.builders.seas import build_sea_zones
from gpm.cli import main
from gpm.config import sea_zone_settings, load_profile


def test_sea_zone_settings_resolve_strategy_presets():
    profile = load_profile("modern-small")
    settings = sea_zone_settings(profile)
    assert settings["strategy"] == "simple-coastal-and-ocean"
    assert settings["coastal_buffer_km"] == 150.0
    assert settings["ocean_cell_size_deg"] == 45.0

    eu = sea_zone_settings(load_profile("eu-like"))
    assert eu["strategy"] == "dense-coastal-seas-and-straits"
    assert eu["coastal_buffer_km"] == 75.0


def test_build_sea_zones_creates_coastal_and_ocean_and_is_deterministic(tmp_path):
    province_input = tmp_path / "provinces.geojson"
    sea_output = tmp_path / "sea_zones.geojson"
    _write_provinces(
        province_input,
        [
            _land("land_west", _polygon(0, 0, 1, 1), name="West"),
            _land("land_east", _polygon(2.0, 0, 3.0, 1), name="East"),
        ],
    )

    first = build_sea_zones(
        "modern-small",
        province_input=province_input,
        sea_output=sea_output,
        raw_dir=tmp_path / "raw",
        update_provinces=True,
    )
    second_output = tmp_path / "sea_zones_2.geojson"
    second = build_sea_zones(
        "modern-small",
        province_input=province_input,
        sea_output=second_output,
        raw_dir=tmp_path / "raw",
        update_provinces=False,
    )

    assert first.sea_zone_count == second.sea_zone_count
    assert first.coastal_sea_zone_count >= 2
    assert first.ocean_sea_zone_count >= 1
    assert first.coastal_province_count == 2
    assert sea_output.read_bytes() == second_output.read_bytes()

    seas = json.loads(sea_output.read_text(encoding="utf-8"))
    assert seas["type"] == "FeatureCollection"
    assert seas["name"] == "sea_zones"
    assert seas["gpm"]["milestone"] == "M6"
    assert seas["gpm"]["id_scheme"] == "sea-geometry-sha256-v1"
    assert seas["gpm"]["sea_zone_strategy"] == "simple-coastal-and-ocean"
    properties = [feature["properties"] for feature in seas["features"]]
    assert all(item["kind"] == "sea" for item in properties)
    assert {item["sea_class"] for item in properties} >= {"coastal", "ocean"}
    coastal = [item for item in properties if item["sea_class"] == "coastal"]
    assert {item["parent_land_province_id"] for item in coastal} == {"land_west", "land_east"}
    assert all(item["province_id"].startswith("sea_") for item in properties)
    assert [item["province_id"] for item in properties] == sorted(
        item["province_id"] for item in properties
    )

    updated = json.loads(province_input.read_text(encoding="utf-8"))
    assert updated["gpm"]["coastal_flags_updated_by"] == "M6"
    coastal_flags = {
        feature["properties"]["province_id"]: feature["properties"]["coastal"]
        for feature in updated["features"]
    }
    assert coastal_flags == {"land_west": True, "land_east": True}


def test_adjacency_emits_port_to_sea_sea_and_strait_edges(tmp_path):
    province_input = tmp_path / "provinces.geojson"
    sea_output = tmp_path / "sea_zones.geojson"
    adjacency_output = tmp_path / "adjacency.csv"
    # Two land masses with a water gap under the modern-small 40 km strait threshold
    # (0.2° ≈ 22 km at the equator) and no shared land border.
    _write_provinces(
        province_input,
        [
            _land("land_a", _polygon(0, 0, 1, 1)),
            _land("land_b", _polygon(1.2, 0, 2.2, 1)),
        ],
    )
    seas = build_sea_zones(
        "modern-small",
        province_input=province_input,
        sea_output=sea_output,
        raw_dir=tmp_path / "raw",
        update_provinces=True,
    )
    assert seas.coastal_sea_zone_count >= 2

    result = build_land_adjacency(
        "modern-small",
        province_input=province_input,
        sea_input=sea_output,
        output=adjacency_output,
    )
    assert result.sea_zone_count == seas.sea_zone_count
    assert result.port_to_sea_count >= 2
    assert result.strait_count == 1
    assert result.land_adjacency_count == 0

    with adjacency_output.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    by_type = {}
    for row in rows:
        by_type.setdefault(row["adjacency_type"], []).append(row)

    assert "port_to_sea" in by_type
    assert all(row["crossing_type"] == "port" for row in by_type["port_to_sea"])
    assert all(row["bidirectional"] == "true" for row in by_type["port_to_sea"])

    assert len(by_type["strait"]) == 1
    strait = by_type["strait"][0]
    assert {strait["from_province_id"], strait["to_province_id"]} == {"land_a", "land_b"}
    assert strait["crossing_type"] == "strait"
    assert float(strait["shared_border_km"]) > 0

    if "sea" in by_type:
        assert all(row["crossing_type"] == "shared_border" for row in by_type["sea"])


def test_build_seas_and_adjacency_cli_json(tmp_path, capsys):
    province_input = tmp_path / "provinces.geojson"
    sea_output = tmp_path / "sea_zones.geojson"
    adjacency_output = tmp_path / "adjacency.csv"
    _write_provinces(
        province_input,
        [
            _land("land_a", _polygon(0, 0, 1, 1)),
            _land("land_b", _polygon(1, 0, 2, 1)),
        ],
    )

    assert (
        main(
            [
                "build",
                "seas",
                "--province-input",
                str(province_input),
                "--sea-output",
                str(sea_output),
                "--raw-dir",
                str(tmp_path / "raw"),
                "--format",
                "json",
            ]
        )
        == 0
    )
    sea_summary = json.loads(capsys.readouterr().out)
    assert sea_summary["sea_zone_count"] >= 1
    assert sea_summary["strategy"] == "simple-coastal-and-ocean"
    assert Path(sea_summary["sea_output"]).is_file()

    assert (
        main(
            [
                "build",
                "adjacency",
                "--province-input",
                str(province_input),
                "--sea-input",
                str(sea_output),
                "--output",
                str(adjacency_output),
                "--format",
                "json",
            ]
        )
        == 0
    )
    adj_summary = json.loads(capsys.readouterr().out)
    assert adj_summary["land_adjacency_count"] == 1
    assert adj_summary["port_to_sea_count"] >= 1
    assert adj_summary["sea_zone_count"] == sea_summary["sea_zone_count"]
    assert adjacency_output.is_file()


def test_build_seas_cli_reports_missing_provinces(tmp_path, capsys):
    assert main(["build", "seas", "--province-input", str(tmp_path / "missing.geojson")]) == 1
    captured = capsys.readouterr()
    assert "does not exist" in captured.err
    assert "Traceback" not in captured.err


def test_adjacency_without_sea_zones_stays_land_only(tmp_path):
    province_input = tmp_path / "provinces.geojson"
    output = tmp_path / "adjacency.csv"
    _write_provinces(
        province_input,
        [
            _land("p_a", _polygon(0, 0, 1, 1)),
            _land("p_b", _polygon(1, 0, 2, 1)),
        ],
    )
    result = build_land_adjacency(
        "modern-small",
        province_input=province_input,
        sea_input=tmp_path / "absent_sea_zones.geojson",
        output=output,
    )
    assert result.sea_zone_count == 0
    assert result.port_to_sea_count == 0
    assert result.strait_count == 0
    assert result.land_adjacency_count == 1
    assert result.adjacency_count == 1


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


def _land(province_id: str, geometry: dict, *, name: str | None = None) -> dict:
    return {
        "type": "Feature",
        "geometry": geometry,
        "properties": {
            "province_id": province_id,
            "display_name": name or province_id,
            "kind": "land",
            "parent_country_id": "AAA",
            "parent_region_id": "AAA-1",
            "area_sq_km": 1000.0,
            "estimated_population": None,
            "terrain_class": "unclassified",
            "coastal": False,
            "island": False,
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
