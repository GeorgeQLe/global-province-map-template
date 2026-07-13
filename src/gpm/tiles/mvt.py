"""Minimal Mapbox Vector Tile (MVT) encoder for polygon features.

Implements enough of the MVT protobuf schema to encode Polygon / MultiPolygon
features with string, number, and boolean properties. Geometry uses the
standard command stream (MoveTo / LineTo / ClosePath) with zig-zag deltas
relative to a 0–extent tile grid (default extent 4096).
"""

from __future__ import annotations

import hashlib
import math
import struct
from io import BytesIO
from typing import Any

from shapely.geometry import mapping, shape
from shapely.geometry.base import BaseGeometry

# MVT geometry commands
CMD_MOVE_TO = 1
CMD_LINE_TO = 2
CMD_CLOSE_PATH = 7

GEOM_UNKNOWN = 0
GEOM_POINT = 1
GEOM_LINESTRING = 2
GEOM_POLYGON = 3

DEFAULT_EXTENT = 4096


def write_varint(buf: BytesIO, value: int) -> None:
    """Write an unsigned protobuf varint."""
    if value < 0:
        raise ValueError("varint must be non-negative")
    while True:
        bits = value & 0x7F
        value >>= 7
        if value:
            buf.write(bytes([bits | 0x80]))
        else:
            buf.write(bytes([bits]))
            break


def write_key(buf: BytesIO, field_number: int, wire_type: int) -> None:
    write_varint(buf, (field_number << 3) | wire_type)


def write_bytes_field(buf: BytesIO, field_number: int, data: bytes) -> None:
    write_key(buf, field_number, 2)
    write_varint(buf, len(data))
    buf.write(data)


def write_string_field(buf: BytesIO, field_number: int, value: str) -> None:
    write_bytes_field(buf, field_number, value.encode("utf-8"))


def write_uint32_field(buf: BytesIO, field_number: int, value: int) -> None:
    write_key(buf, field_number, 0)
    write_varint(buf, value)


def write_uint64_field(buf: BytesIO, field_number: int, value: int) -> None:
    write_key(buf, field_number, 0)
    write_varint(buf, value)


def _write_double_field(buf: BytesIO, field_number: int, value: float) -> None:
    write_key(buf, field_number, 1)  # 64-bit
    buf.write(struct.pack("<d", float(value)))


def zigzag_encode(n: int) -> int:
    return (n << 1) ^ (n >> 31)


def command_integer(cmd_id: int, count: int) -> int:
    return (cmd_id & 0x7) | (count << 3)


MERCATOR_MAX_LAT = 85.05112878


def _mercator_y(lat: float) -> float:
    lat = max(min(lat, MERCATOR_MAX_LAT), -MERCATOR_MAX_LAT)
    return math.log(math.tan(math.pi / 4.0 + math.radians(lat) / 2.0))


def lonlat_to_tile_xy(
    lon: float,
    lat: float,
    *,
    west: float,
    south: float,
    east: float,
    north: float,
    extent: int = DEFAULT_EXTENT,
) -> tuple[int, int]:
    """Project WGS84 lon/lat into MVT tile pixel coordinates (y down).

    Tile bounds come from Web Mercator tiles, and renderers interpret tile
    y as a Mercator fraction — latitude must go through the Mercator
    projection, not linear interpolation (linear y drifts by whole countries
    at low zooms). Longitude → x is genuinely linear in Mercator.
    """
    # Guard zero-size tiles.
    width = east - west or 1e-12
    x = int(round((lon - west) / width * extent))
    y_top = _mercator_y(north)
    y_bottom = _mercator_y(south)
    height = y_top - y_bottom or 1e-12
    y = int(round((y_top - _mercator_y(lat)) / height * extent))
    return x, y


def encode_ring_commands(
    coords: list[tuple[float, float]],
    *,
    west: float,
    south: float,
    east: float,
    north: float,
    extent: int,
    cursor: list[int],
    close_ring: bool = True,
) -> list[int]:
    """Encode a ring (or line) into MVT command integers; mutates cursor [x,y]."""
    if len(coords) < 2:
        return []
    # Drop closing duplicate if present for polygon rings — ClosePath handles it.
    points = list(coords)
    if close_ring and len(points) >= 2 and points[0] == points[-1]:
        points = points[:-1]
    if not points:
        return []

    commands: list[int] = []
    # MoveTo first point
    x0, y0 = lonlat_to_tile_xy(
        points[0][0], points[0][1], west=west, south=south, east=east, north=north, extent=extent
    )
    commands.append(command_integer(CMD_MOVE_TO, 1))
    commands.append(zigzag_encode(x0 - cursor[0]))
    commands.append(zigzag_encode(y0 - cursor[1]))
    cursor[0], cursor[1] = x0, y0

    if len(points) > 1:
        commands.append(command_integer(CMD_LINE_TO, len(points) - 1))
        for lon, lat in points[1:]:
            x, y = lonlat_to_tile_xy(
                lon, lat, west=west, south=south, east=east, north=north, extent=extent
            )
            commands.append(zigzag_encode(x - cursor[0]))
            commands.append(zigzag_encode(y - cursor[1]))
            cursor[0], cursor[1] = x, y

    if close_ring:
        commands.append(command_integer(CMD_CLOSE_PATH, 1))
    return commands


def quantize_ring(
    coords: list[tuple[float, float]],
    *,
    west: float,
    south: float,
    east: float,
    north: float,
    extent: int,
) -> list[tuple[int, int]]:
    """Project a lon/lat ring into tile space, dropping consecutive duplicates."""
    points: list[tuple[int, int]] = []
    for lon, lat in coords:
        xy = lonlat_to_tile_xy(lon, lat, west=west, south=south, east=east, north=north, extent=extent)
        if not points or points[-1] != xy:
            points.append(xy)
    # Drop closing duplicate — ClosePath handles it.
    if len(points) >= 2 and points[0] == points[-1]:
        points.pop()
    return points


def ring_signed_area2(points: list[tuple[int, int]]) -> int:
    """Twice the signed shoelace area of a closed tile-space ring (y down).

    Per the MVT v2 spec's surveyor's formula, exterior rings must have positive
    area and interior rings negative area in tile coordinates.
    """
    total = 0
    count = len(points)
    for index in range(count):
        x0, y0 = points[index]
        x1, y1 = points[(index + 1) % count]
        total += x0 * y1 - x1 * y0
    return total


def _encode_quantized_ring(points: list[tuple[int, int]], cursor: list[int]) -> list[int]:
    commands: list[int] = [command_integer(CMD_MOVE_TO, 1)]
    x0, y0 = points[0]
    commands.append(zigzag_encode(x0 - cursor[0]))
    commands.append(zigzag_encode(y0 - cursor[1]))
    cursor[0], cursor[1] = x0, y0
    commands.append(command_integer(CMD_LINE_TO, len(points) - 1))
    for x, y in points[1:]:
        commands.append(zigzag_encode(x - cursor[0]))
        commands.append(zigzag_encode(y - cursor[1]))
        cursor[0], cursor[1] = x, y
    commands.append(command_integer(CMD_CLOSE_PATH, 1))
    return commands


def _polygon_ring_commands(
    rings: list[list[tuple[float, float]]],
    *,
    west: float,
    south: float,
    east: float,
    north: float,
    extent: int,
    cursor: list[int],
) -> list[int]:
    """Encode one polygon (exterior + holes) with MVT v2 winding enforced.

    Degenerate rings (collapsed to fewer than 3 distinct points or zero area
    after quantization) are dropped; if the exterior collapses the whole
    polygon is dropped, holes included.
    """
    commands: list[int] = []
    for ring_index, ring in enumerate(rings):
        points = quantize_ring(ring, west=west, south=south, east=east, north=north, extent=extent)
        if len(points) < 3:
            if ring_index == 0:
                return []
            continue
        area2 = ring_signed_area2(points)
        if area2 == 0:
            if ring_index == 0:
                return []
            continue
        want_positive = ring_index == 0
        if (area2 > 0) != want_positive:
            points = [points[0], *reversed(points[1:])]
        commands.extend(_encode_quantized_ring(points, cursor))
    return commands


def geometry_commands(
    geom: BaseGeometry,
    *,
    west: float,
    south: float,
    east: float,
    north: float,
    extent: int = DEFAULT_EXTENT,
) -> tuple[int, list[int]]:
    """Return (GeomType, command stream) for a shapely geometry."""
    if geom.is_empty:
        return GEOM_UNKNOWN, []

    gtype = geom.geom_type
    cursor = [0, 0]
    commands: list[int] = []

    if gtype == "Polygon":
        mapping_doc = mapping(geom)
        rings = [[(c[0], c[1]) for c in ring] for ring in mapping_doc["coordinates"]]
        commands.extend(
            _polygon_ring_commands(
                rings, west=west, south=south, east=east, north=north, extent=extent, cursor=cursor
            )
        )
        if not commands:
            return GEOM_UNKNOWN, []
        return GEOM_POLYGON, commands

    if gtype == "MultiPolygon":
        mapping_doc = mapping(geom)
        for polygon in mapping_doc["coordinates"]:
            rings = [[(c[0], c[1]) for c in ring] for ring in polygon]
            commands.extend(
                _polygon_ring_commands(
                    rings,
                    west=west,
                    south=south,
                    east=east,
                    north=north,
                    extent=extent,
                    cursor=cursor,
                )
            )
        if not commands:
            return GEOM_UNKNOWN, []
        return GEOM_POLYGON, commands

    if gtype == "LineString":
        coords = [(c[0], c[1]) for c in mapping(geom)["coordinates"]]
        commands = encode_ring_commands(
            coords,
            west=west,
            south=south,
            east=east,
            north=north,
            extent=extent,
            cursor=cursor,
            close_ring=False,
        )
        return GEOM_LINESTRING, commands

    if gtype == "MultiLineString":
        for line in mapping(geom)["coordinates"]:
            commands.extend(
                encode_ring_commands(
                    [(c[0], c[1]) for c in line],
                    west=west,
                    south=south,
                    east=east,
                    north=north,
                    extent=extent,
                    cursor=cursor,
                    close_ring=False,
                )
            )
        return GEOM_LINESTRING, commands

    if gtype == "Point":
        lon, lat = geom.x, geom.y
        x, y = lonlat_to_tile_xy(
            lon, lat, west=west, south=south, east=east, north=north, extent=extent
        )
        commands = [
            command_integer(CMD_MOVE_TO, 1),
            zigzag_encode(x - cursor[0]),
            zigzag_encode(y - cursor[1]),
        ]
        return GEOM_POINT, commands

    if gtype == "MultiPoint":
        for pt in geom.geoms:
            lon, lat = pt.x, pt.y
            x, y = lonlat_to_tile_xy(
                lon, lat, west=west, south=south, east=east, north=north, extent=extent
            )
            commands.append(command_integer(CMD_MOVE_TO, 1))
            commands.append(zigzag_encode(x - cursor[0]))
            commands.append(zigzag_encode(y - cursor[1]))
            cursor[0], cursor[1] = x, y
        return GEOM_POINT, commands

    # GeometryCollection — encode first non-empty child
    if gtype == "GeometryCollection":
        for child in geom.geoms:
            if not child.is_empty:
                return geometry_commands(
                    child, west=west, south=south, east=east, north=north, extent=extent
                )

    return GEOM_UNKNOWN, []


def encode_value(value: Any) -> bytes:
    """Encode an MVT Value message."""
    buf = BytesIO()
    if value is None:
        write_string_field(buf, 1, "")
    elif isinstance(value, bool):
        write_key(buf, 7, 0)
        write_varint(buf, 1 if value else 0)
    elif isinstance(value, int) and not isinstance(value, bool):
        # Prefer sint for negative, uint for non-negative.
        if value < 0:
            write_key(buf, 6, 0)
            write_varint(buf, (value << 1) ^ (value >> 63))
        else:
            write_uint64_field(buf, 5, value)
    elif isinstance(value, float):
        _write_double_field(buf, 3, value)
    else:
        write_string_field(buf, 1, str(value))
    return buf.getvalue()


def encode_feature(
    *,
    feature_id: int | None,
    tags: list[int],
    geom_type: int,
    geometry: list[int],
) -> bytes:
    buf = BytesIO()
    if feature_id is not None and feature_id >= 0:
        write_uint64_field(buf, 1, feature_id)
    if tags:
        # packed repeated uint32 tags = 2
        packed = BytesIO()
        for tag in tags:
            write_varint(packed, tag)
        write_bytes_field(buf, 2, packed.getvalue())
    write_uint32_field(buf, 3, geom_type)
    if geometry:
        packed = BytesIO()
        for cmd in geometry:
            write_varint(packed, cmd)
        write_bytes_field(buf, 4, packed.getvalue())
    return buf.getvalue()


def encode_layer(
    name: str,
    features: list[dict[str, Any]],
    *,
    west: float,
    south: float,
    east: float,
    north: float,
    extent: int = DEFAULT_EXTENT,
    property_keys: frozenset[str] | None = None,
) -> bytes:
    """Encode one MVT layer from feature dicts with shapely geometry + properties."""
    keys: list[str] = []
    key_index: dict[str, int] = {}
    values: list[bytes] = []
    value_index: dict[tuple[str, Any], int] = {}
    encoded_features: list[bytes] = []

    def ensure_key(key: str) -> int:
        if key not in key_index:
            key_index[key] = len(keys)
            keys.append(key)
        return key_index[key]

    def ensure_value(raw: Any) -> int:
        # Normalize for dictionary lookup.
        if isinstance(raw, float):
            lookup: tuple[str, Any] = ("f", raw)
        elif isinstance(raw, bool):
            lookup = ("b", raw)
        elif isinstance(raw, int):
            lookup = ("i", raw)
        elif raw is None:
            lookup = ("n", None)
        else:
            lookup = ("s", str(raw))
        if lookup not in value_index:
            value_index[lookup] = len(values)
            values.append(encode_value(raw if not isinstance(raw, str) else str(raw)))
        return value_index[lookup]

    for index, feature in enumerate(features):
        geom = feature.get("geometry")
        if geom is None:
            continue
        if not isinstance(geom, BaseGeometry):
            geom = shape(geom)
        if geom.is_empty:
            continue
        geom_type, commands = geometry_commands(
            geom, west=west, south=south, east=east, north=north, extent=extent
        )
        if geom_type == GEOM_UNKNOWN or not commands:
            continue

        props = feature.get("properties") or {}
        tags: list[int] = []
        for key, value in props.items():
            if property_keys is not None and key not in property_keys:
                continue
            if value is None:
                continue
            if isinstance(value, (list, dict)):
                # Flatten simple lists; skip nested structures.
                if isinstance(value, list) and all(
                    isinstance(item, (str, int, float, bool)) or item is None for item in value
                ):
                    value = ",".join("" if item is None else str(item) for item in value)
                else:
                    continue
            tags.append(ensure_key(str(key)))
            tags.append(ensure_value(value))

        feature_id = feature.get("id")
        if feature_id is None:
            # Prefer province_id with a stable numeric id when available.
            pid = props.get("province_id")
            if isinstance(pid, str) and pid:
                feature_id = int(hashlib.sha256(pid.encode("utf-8")).hexdigest()[:13], 16)
            else:
                feature_id = index

        if not isinstance(feature_id, int):
            try:
                feature_id = int(feature_id)
            except (TypeError, ValueError):
                feature_id = index

        encoded_features.append(
            encode_feature(
                feature_id=feature_id,
                tags=tags,
                geom_type=geom_type,
                geometry=commands,
            )
        )

    layer = BytesIO()
    # name = 1
    write_string_field(layer, 1, name)
    # features = 2
    for feat_bytes in encoded_features:
        write_bytes_field(layer, 2, feat_bytes)
    # keys = 3
    for key in keys:
        write_string_field(layer, 3, key)
    # values = 4
    for value_bytes in values:
        write_bytes_field(layer, 4, value_bytes)
    # extent = 5
    write_uint32_field(layer, 5, extent)
    # version = 15
    write_uint32_field(layer, 15, 2)
    return layer.getvalue()


def encode_tile(
    layers: list[tuple[str, list[dict[str, Any]]]],
    *,
    west: float,
    south: float,
    east: float,
    north: float,
    extent: int = DEFAULT_EXTENT,
    property_keys: frozenset[str] | None = None,
) -> bytes:
    """Encode a complete MVT tile (repeated Layer layers = 3)."""
    tile = BytesIO()
    for name, features in layers:
        if not features:
            continue
        layer_bytes = encode_layer(
            name,
            features,
            west=west,
            south=south,
            east=east,
            north=north,
            extent=extent,
            property_keys=property_keys,
        )
        write_bytes_field(tile, 3, layer_bytes)
    return tile.getvalue()
