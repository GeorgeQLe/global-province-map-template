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
from gpm.tiles.mvt import GEOM_POLYGON, GEOM_UNKNOWN, encode_tile, geometry_commands
from gpm.tiles.pmtiles_io import (
    PmtilesWriter,
    read_pmtiles_header as read_header_direct,
    read_pmtiles_metadata,
    zxy_to_tileid,
    tileid_to_zxy,
)
from shapely.geometry import MultiPolygon, Polygon, box


def _unzigzag(value: int) -> int:
    return (value >> 1) ^ (-(value & 1))


def _decode_rings(commands: list[int]) -> list[list[tuple[int, int]]]:
    """Decode an MVT polygon command stream into closed rings of tile coords."""
    rings: list[list[tuple[int, int]]] = []
    ring: list[tuple[int, int]] = []
    x = y = 0
    i = 0
    while i < len(commands):
        cmd = commands[i]
        i += 1
        cmd_id = cmd & 0x7
        count = cmd >> 3
        if cmd_id in (1, 2):  # MoveTo / LineTo
            if cmd_id == 1:
                ring = []
            for _ in range(count):
                x += _unzigzag(commands[i])
                y += _unzigzag(commands[i + 1])
                i += 2
                ring.append((x, y))
        elif cmd_id == 7:  # ClosePath
            rings.append(ring)
    return rings


def _signed_area2(points: list[tuple[int, int]]) -> int:
    total = 0
    for index in range(len(points)):
        x0, y0 = points[index]
        x1, y1 = points[(index + 1) % len(points)]
        total += x0 * y1 - x1 * y0
    return total


def test_tile_y_uses_web_mercator_projection():
    from gpm.tiles.mvt import lonlat_to_tile_xy

    # z0 world tile: the equator maps to the vertical midpoint under Mercator…
    bounds = {"west": -180.0, "south": -85.05112878, "east": 180.0, "north": 85.05112878}
    x, y = lonlat_to_tile_xy(0.0, 0.0, extent=4096, **bounds)
    assert (x, y) == (2048, 2048)
    # …but 60°N sits at ln(tan(75°))/π of the half-height, NOT at the linear
    # position (~603). Linear latitude drifts whole countries at low zooms.
    import math

    _, y60 = lonlat_to_tile_xy(0.0, 60.0, extent=4096, **bounds)
    expected = round((math.pi - math.log(math.tan(math.radians(75)))) / (2 * math.pi) * 4096)
    assert y60 == expected
    assert abs(y60 - 1190) <= 1


def test_polygon_winding_enforced_for_exterior_and_hole():
    # Exterior deliberately clockwise in lon/lat, hole counter-clockwise —
    # the encoder must normalize both to MVT v2 winding regardless of input.
    exterior = [(0.1, 0.1), (0.1, 0.9), (0.9, 0.9), (0.9, 0.1)]
    hole = [(0.3, 0.3), (0.7, 0.3), (0.7, 0.7), (0.3, 0.7)]
    for polygon in (Polygon(exterior, [hole]), Polygon(list(reversed(exterior)), [list(reversed(hole))])):
        geom_type, commands = geometry_commands(polygon, west=0.0, south=0.0, east=1.0, north=1.0)
        assert geom_type == GEOM_POLYGON
        rings = _decode_rings(commands)
        assert len(rings) == 2
        assert _signed_area2(rings[0]) > 0, "exterior ring must have positive tile-space area"
        assert _signed_area2(rings[1]) < 0, "interior ring must have negative tile-space area"


def test_multipolygon_winding_and_ring_grouping():
    poly_a = Polygon([(0.05, 0.05), (0.45, 0.05), (0.45, 0.45), (0.05, 0.45)])
    poly_b = Polygon(
        [(0.55, 0.55), (0.95, 0.55), (0.95, 0.95), (0.55, 0.95)],
        [[(0.65, 0.65), (0.85, 0.65), (0.85, 0.85), (0.65, 0.85)]],
    )
    geom_type, commands = geometry_commands(
        MultiPolygon([poly_a, poly_b]), west=0.0, south=0.0, east=1.0, north=1.0
    )
    assert geom_type == GEOM_POLYGON
    rings = _decode_rings(commands)
    assert len(rings) == 3
    signs = [_signed_area2(ring) for ring in rings]
    assert signs[0] > 0 and signs[1] > 0 and signs[2] < 0


def test_degenerate_rings_dropped_after_quantization():
    sliver = Polygon([(0.5, 0.5), (0.5 + 1e-9, 0.5), (0.5 + 1e-9, 0.5 + 1e-9)])
    geom_type, commands = geometry_commands(sliver, west=0.0, south=0.0, east=1.0, north=1.0)
    assert geom_type == GEOM_UNKNOWN
    assert commands == []

    # A degenerate hole is dropped but the exterior survives.
    poly = Polygon(
        [(0.1, 0.1), (0.9, 0.1), (0.9, 0.9), (0.1, 0.9)],
        [[(0.5, 0.5), (0.5 + 1e-9, 0.5), (0.5 + 1e-9, 0.5 + 1e-9)]],
    )
    geom_type, commands = geometry_commands(poly, west=0.0, south=0.0, east=1.0, north=1.0)
    assert geom_type == GEOM_POLYGON
    assert len(_decode_rings(commands)) == 1


def test_pmtiles_dedup_is_content_based(tmp_path):
    out = tmp_path / "dedup.pmtiles"
    writer = PmtilesWriter(out)
    payload = b"identical-tile-bytes"
    writer.write_tile(zxy_to_tileid(1, 0, 0), payload)
    writer.write_tile(zxy_to_tileid(1, 1, 0), b"unique-tile-bytes")
    writer.write_tile(zxy_to_tileid(1, 1, 1), payload)
    writer.finalize(
        metadata={"name": "dedup-test"},
        min_zoom=1,
        max_zoom=1,
        bounds=(-180.0, -85.0, 180.0, 85.0),
        tile_compression=1,  # Compression.NONE
    )
    header = read_header_direct(out)
    assert header["addressed_tiles_count"] == 3
    assert header["tile_contents_count"] == 2
    assert read_pmtiles_tile(out, 1, 1, 1) == payload


def test_pmtiles_archive_is_byte_deterministic(tmp_path):
    features = [
        {
            "geometry": box(2.0, 48.0, 3.0, 49.0),
            "properties": {"province_id": "land_a", "owner": "FRA", "owner_color": "#336699"},
        },
        {
            "geometry": box(3.0, 48.0, 4.0, 49.0),
            "properties": {"province_id": "land_b", "owner": "ENG", "owner_color": "#663399"},
        },
    ]
    out_a = tmp_path / "a.pmtiles"
    out_b = tmp_path / "b.pmtiles"
    build_pmtiles_from_features(features, out_a, min_zoom=0, max_zoom=3, write_manifest=False)
    build_pmtiles_from_features(features, out_b, min_zoom=0, max_zoom=3, write_manifest=False)
    assert out_a.read_bytes() == out_b.read_bytes()


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
