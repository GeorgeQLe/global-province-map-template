"""M19 PMTiles / vector tiles."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from gpm.cli import main
from gpm.exporters import export_atlas_pack
from gpm.schemas import SchemaValidationError, validate_tileset_manifest
from gpm.tiles import (
    TileBuildError,
    build_pmtiles_from_features,
    build_pmtiles_from_geojson,
    export_tiles_from_atlas,
    read_pmtiles_header,
    read_pmtiles_tile,
)
from gpm.tiles.mvt import encode_tile
from gpm.tiles.pmtiles_io import read_pmtiles_metadata, zxy_to_tileid, tileid_to_zxy
from shapely.geometry import box


def test_zxy_tileid_roundtrip():
    for z, x, y in [(0, 0, 0), (1, 0, 1), (2, 3, 1), (5, 10, 20)]:
        tid = zxy_to_tileid(z, x, y)
        assert tileid_to_zxy(tid) == (z, x, y)


def test_encode_tile_produces_mvt_bytes():
    feature = {
        "geometry": box(0.1, 0.1, 0.4, 0.4),
        "properties": {"province_id": "land_a", "owner": "FRA", "owner_color": "#112233"},
    }
    data = encode_tile(
        [("provinces", [feature])],
        west=0.0,
        south=0.0,
        east=1.0,
        north=1.0,
    )
    assert isinstance(data, bytes)
    assert len(data) > 10


def test_build_pmtiles_native_and_read_header(tmp_path):
    features = [
        {
            "geometry": box(2.0, 48.0, 3.0, 49.0),
            "properties": {
                "province_id": "land_paris",
                "display_name": "Paris",
                "owner": "FRA",
                "owner_color": "#336699",
            },
        },
        {
            "geometry": box(3.0, 48.0, 4.0, 49.0),
            "properties": {
                "province_id": "land_east",
                "display_name": "East",
                "owner": "FRA",
                "owner_color": "#336699",
            },
        },
    ]
    out = tmp_path / "test.pmtiles"
    result = build_pmtiles_from_features(
        features,
        out,
        layer_name="ownership",
        min_zoom=0,
        max_zoom=4,
        backend="native",
    )
    assert Path(result.output_path).is_file()
    assert result.feature_count == 2
    assert result.tile_count >= 1
    assert result.backend == "native"
    assert result.min_zoom == 0
    assert result.max_zoom == 4
    assert Path(result.tileset_manifest).is_file()

    header = read_pmtiles_header(out)
    assert header["version"] == 3
    assert header["min_zoom"] == 0
    assert header["max_zoom"] == 4
    assert header["addressed_tiles_count"] == result.tile_count
    assert header["tile_type"].name == "MVT" or int(header["tile_type"]) == 1

    magic = out.read_bytes()[:7]
    assert magic == b"PMTiles"

    # At least one tile should exist near Paris at z=3.
    found = False
    for x in range(0, 8):
        for y in range(0, 8):
            tile = read_pmtiles_tile(out, 3, x, y)
            if tile:
                found = True
                assert len(tile) > 0
                break
        if found:
            break
    assert found, "expected at least one non-empty tile at z=3"

    manifest = json.loads(Path(result.tileset_manifest).read_text(encoding="utf-8"))
    validate_tileset_manifest(manifest)
    assert manifest["milestone"] == "M19"
    assert manifest["pmtiles"] == "test.pmtiles"
    assert manifest["layer_name"] == "ownership"

    meta = read_pmtiles_metadata(out)
    assert "vector_layers" in meta
    assert meta["vector_layers"][0]["id"] == "ownership"


def test_build_pmtiles_from_geojson_cli(tmp_path):
    geojson = tmp_path / "provinces.geojson"
    _write_geojson(
        geojson,
        [
            _feature("a", 0, 0, 1, 1, owner="FRA"),
            _feature("b", 1, 0, 2, 1, owner="ENG"),
        ],
    )
    out = tmp_path / "out.pmtiles"
    code = main(
        [
            "export",
            "tiles",
            "--input",
            str(geojson),
            "--output",
            str(out),
            "--layer",
            "provinces",
            "--min-zoom",
            "0",
            "--max-zoom",
            "3",
            "--no-tippecanoe",
            "--format",
            "json",
        ]
    )
    assert code == 0
    assert out.is_file()
    header = read_pmtiles_header(out)
    assert header["max_zoom"] == 3


def test_export_atlas_with_tiles(tmp_path):
    province_input = tmp_path / "provinces.geojson"
    output_dir = tmp_path / "atlas-out"
    _write_provinces(
        province_input,
        [
            _land("land_a", 0, 0, 1, 1, country="FRA"),
            _land("land_b", 1, 0, 2, 1, country="FRA"),
            _land("land_c", 0, 1, 1, 2, country="GBR"),
        ],
    )
    result = export_atlas_pack(
        "modern-small",
        province_input=province_input,
        output_dir=output_dir,
        scenarios=("demo-1444",),
        include_tiles=True,
        tile_min_zoom=0,
        tile_max_zoom=3,
        prefer_tippecanoe=False,
    )
    assert result.include_tiles is True
    assert result.tile_file_count >= 1
    ownership_tiles = output_dir / "scenarios" / "demo-1444" / "ownership.pmtiles"
    assert ownership_tiles.is_file()
    base_tiles = output_dir / "tiles" / "provinces.pmtiles"
    assert base_tiles.is_file()
    manifest = json.loads(Path(result.atlas_manifest).read_text(encoding="utf-8"))
    assert manifest["milestone"] == "M19"
    assert manifest["include_tiles"] is True
    assert "PMTiles" in manifest["formats"]["geometry"]
    assert any("ownership.pmtiles" in f for f in manifest["files"])


def test_export_tiles_from_atlas_dir(tmp_path):
    province_input = tmp_path / "provinces.geojson"
    atlas_dir = tmp_path / "atlas"
    _write_provinces(
        province_input,
        [
            _land("land_a", 0, 0, 1, 1, country="FRA"),
            _land("land_b", 1, 0, 2, 1, country="GBR"),
        ],
    )
    export_atlas_pack(
        "modern-small",
        province_input=province_input,
        output_dir=atlas_dir,
        scenarios=("modern-baseline",),
        include_tiles=False,
    )
    results = export_tiles_from_atlas(
        atlas_dir,
        min_zoom=0,
        max_zoom=2,
        prefer_tippecanoe=False,
    )
    assert len(results) >= 1
    assert any(Path(r.output_path).name == "ownership.pmtiles" for r in results)


def test_empty_features_raises():
    with pytest.raises(TileBuildError):
        build_pmtiles_from_features([], "/tmp/none.pmtiles")


def test_tileset_manifest_validation_rejects_bad_backend():
    with pytest.raises(SchemaValidationError):
        validate_tileset_manifest(
            {
                "schema_version": "0.1.0",
                "milestone": "M19",
                "pack_type": "tileset",
                "generated_at": "2026-01-01T00:00:00Z",
                "generator_version": "0.1.0",
                "backend": "magic",
                "layer_name": "provinces",
                "pmtiles": "x.pmtiles",
                "feature_count": 1,
                "tile_count": 1,
                "min_zoom": 0,
                "max_zoom": 1,
                "bounds": {"west": 0, "south": 0, "east": 1, "north": 1},
            }
        )


def test_cli_tiles_requires_input():
    assert main(["export", "tiles"]) == 1


def _write_geojson(path: Path, features: list[dict]) -> None:
    path.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}),
        encoding="utf-8",
    )


def _feature(pid: str, minx, miny, maxx, maxy, **props) -> dict:
    return {
        "type": "Feature",
        "properties": {"province_id": pid, "display_name": pid, **props},
        "geometry": {
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
        },
    }


def _land(pid: str, minx, miny, maxx, maxy, *, country: str = "FRA") -> dict:
    return {
        "type": "Feature",
        "properties": {
            "province_id": pid,
            "display_name": pid,
            "kind": "land",
            "parent_region_id": "REG-1",
            "parent_country_id": country,
            "area_sq_km": 100.0,
            "estimated_population": 1000,
            "terrain_class": "plains",
            "coastal": False,
            "island": False,
        },
        "geometry": {
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
        },
    }


def _write_provinces(path: Path, features: list[dict]) -> None:
    path.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}),
        encoding="utf-8",
    )
