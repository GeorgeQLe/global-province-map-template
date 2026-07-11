from __future__ import annotations

import math
import struct
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ShapefileReadError(RuntimeError):
    """Raised when a zipped shapefile cannot be read."""


@dataclass(frozen=True)
class ShapeFeature:
    geometry: dict[str, Any]
    properties: dict[str, Any]


def read_zipped_shapefile(path: Path) -> list[ShapeFeature]:
    """Read Polygon/MultiPolygon features from a zipped ESRI shapefile.

    This intentionally supports only the subset needed for Natural Earth
    administrative and land polygon layers. It avoids introducing GDAL/GEOS
    dependencies while M2 is still producing a first draft.
    """
    if not path.is_file():
        raise ShapefileReadError(f"Missing zipped shapefile: {path}")

    try:
        with zipfile.ZipFile(path) as archive:
            shp_name = _single_member(archive, ".shp", path)
            dbf_name = _single_member(archive, ".dbf", path)
            geometries = _read_shp(archive.read(shp_name))
            records = _read_dbf(archive.read(dbf_name))
    except zipfile.BadZipFile as exc:
        raise ShapefileReadError(f"Invalid zip archive: {path}") from exc

    if len(geometries) != len(records):
        raise ShapefileReadError(
            f"Geometry/attribute count mismatch in {path}: {len(geometries)} geometries, "
            f"{len(records)} records."
        )

    return [
        ShapeFeature(geometry=geometry, properties=properties)
        for geometry, properties in zip(geometries, records, strict=True)
        if geometry is not None
    ]


def geometry_area_sq_km(geometry: dict[str, Any]) -> float:
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates")
    if geometry_type == "Polygon":
        return _polygon_area_sq_km(coordinates)
    if geometry_type == "MultiPolygon":
        return sum(_polygon_area_sq_km(polygon) for polygon in coordinates)
    return 0.0


def _single_member(archive: zipfile.ZipFile, suffix: str, path: Path) -> str:
    matches = sorted(name for name in archive.namelist() if name.lower().endswith(suffix))
    if not matches:
        raise ShapefileReadError(f"Archive {path} does not contain a {suffix} member.")
    return matches[0]


def _read_shp(data: bytes) -> list[dict[str, Any] | None]:
    if len(data) < 100:
        raise ShapefileReadError("Shapefile is shorter than the 100-byte header.")
    file_code = struct.unpack(">i", data[0:4])[0]
    if file_code != 9994:
        raise ShapefileReadError("Shapefile header has an invalid file code.")

    geometries: list[dict[str, Any] | None] = []
    offset = 100
    while offset < len(data):
        if offset + 8 > len(data):
            raise ShapefileReadError("Truncated shapefile record header.")
        _, content_length_words = struct.unpack(">2i", data[offset : offset + 8])
        offset += 8
        content_length = content_length_words * 2
        content = data[offset : offset + content_length]
        offset += content_length
        if len(content) < 4:
            raise ShapefileReadError("Truncated shapefile record content.")

        shape_type = struct.unpack("<i", content[0:4])[0]
        if shape_type == 0:
            geometries.append(None)
            continue
        if shape_type not in {5, 15, 25}:
            raise ShapefileReadError(f"Unsupported shapefile shape type {shape_type}; expected Polygon.")
        geometries.append(_read_polygon_record(content))

    return geometries


def _read_polygon_record(content: bytes) -> dict[str, Any]:
    if len(content) < 44:
        raise ShapefileReadError("Truncated polygon record.")

    part_count, point_count = struct.unpack("<2i", content[36:44])
    parts_offset = 44
    points_offset = parts_offset + (part_count * 4)
    points_end = points_offset + (point_count * 16)
    if len(content) < points_end:
        raise ShapefileReadError("Truncated polygon points.")

    part_starts = list(struct.unpack(f"<{part_count}i", content[parts_offset:points_offset]))
    points = [
        list(struct.unpack("<2d", content[points_offset + index * 16 : points_offset + (index + 1) * 16]))
        for index in range(point_count)
    ]

    rings = []
    for part_index, start in enumerate(part_starts):
        end = part_starts[part_index + 1] if part_index + 1 < len(part_starts) else point_count
        ring = points[start:end]
        if len(ring) >= 4:
            rings.append(_closed_ring(ring))

    return _rings_to_geojson_geometry(rings)


def _rings_to_geojson_geometry(rings: list[list[list[float]]]) -> dict[str, Any]:
    if not rings:
        return {"type": "Polygon", "coordinates": []}

    signed_areas = [_signed_ring_area(ring) for ring in rings]
    has_clockwise = any(area < 0 for area in signed_areas)
    has_counter_clockwise = any(area > 0 for area in signed_areas)

    if has_clockwise and has_counter_clockwise:
        exteriors = [ring for ring, area in zip(rings, signed_areas, strict=True) if area < 0]
        holes = [ring for ring, area in zip(rings, signed_areas, strict=True) if area > 0]
    else:
        exteriors = rings
        holes = []

    polygons = [[_orient_ring(exterior, outer=True)] for exterior in exteriors]
    for hole in holes:
        target_index = _containing_exterior_index(hole[0], exteriors)
        oriented_hole = _orient_ring(hole, outer=False)
        if target_index is None:
            polygons.append([_orient_ring(hole, outer=True)])
        else:
            polygons[target_index].append(oriented_hole)

    if len(polygons) == 1:
        return {"type": "Polygon", "coordinates": polygons[0]}
    return {"type": "MultiPolygon", "coordinates": polygons}


def _closed_ring(ring: list[list[float]]) -> list[list[float]]:
    if ring[0] == ring[-1]:
        return ring
    return [*ring, ring[0]]


def _orient_ring(ring: list[list[float]], *, outer: bool) -> list[list[float]]:
    area = _signed_ring_area(ring)
    if outer and area < 0:
        return list(reversed(ring))
    if not outer and area > 0:
        return list(reversed(ring))
    return ring


def _containing_exterior_index(point: list[float], exteriors: list[list[list[float]]]) -> int | None:
    for index, exterior in enumerate(exteriors):
        if _point_in_ring(point, exterior):
            return index
    return None


def _point_in_ring(point: list[float], ring: list[list[float]]) -> bool:
    x, y = point
    inside = False
    j = len(ring) - 1
    for i, start in enumerate(ring):
        xi, yi = start
        xj, yj = ring[j]
        intersects = (yi > y) != (yj > y)
        if intersects:
            x_intersection = ((xj - xi) * (y - yi) / (yj - yi)) + xi
            if x < x_intersection:
                inside = not inside
        j = i
    return inside


def _polygon_area_sq_km(polygon: list[list[list[float]]]) -> float:
    if not polygon:
        return 0.0
    outer_area = _ring_area_sq_km(polygon[0])
    hole_area = sum(_ring_area_sq_km(hole) for hole in polygon[1:])
    return max(0.0, outer_area - hole_area)


def _ring_area_sq_km(ring: list[list[float]]) -> float:
    if len(ring) < 4:
        return 0.0
    mean_latitude = sum(point[1] for point in ring[:-1]) / max(1, len(ring) - 1)
    km_per_degree = 111.32
    return abs(_signed_ring_area(ring)) * (km_per_degree**2) * abs(math.cos(math.radians(mean_latitude)))


def _signed_ring_area(ring: list[list[float]]) -> float:
    area = 0.0
    for start, end in zip(ring, ring[1:], strict=False):
        area += (start[0] * end[1]) - (end[0] * start[1])
    return area / 2.0


def _read_dbf(data: bytes) -> list[dict[str, Any]]:
    if len(data) < 32:
        raise ShapefileReadError("DBF is shorter than its header.")

    record_count = struct.unpack("<I", data[4:8])[0]
    header_length = struct.unpack("<H", data[8:10])[0]
    record_length = struct.unpack("<H", data[10:12])[0]
    fields = _read_dbf_fields(data, header_length)

    records = []
    offset = header_length
    for _ in range(record_count):
        if offset + record_length > len(data):
            raise ShapefileReadError("Truncated DBF record.")
        record = data[offset : offset + record_length]
        offset += record_length
        if record[:1] == b"*":
            records.append({})
            continue

        position = 1
        parsed: dict[str, Any] = {}
        for field in fields:
            raw_value = record[position : position + field.length]
            position += field.length
            parsed[field.name] = _parse_dbf_value(raw_value, field)
        records.append(parsed)

    return records


@dataclass(frozen=True)
class _DbfField:
    name: str
    field_type: str
    length: int
    decimals: int


def _read_dbf_fields(data: bytes, header_length: int) -> list[_DbfField]:
    fields = []
    offset = 32
    while offset < header_length:
        if data[offset] == 0x0D:
            break
        descriptor = data[offset : offset + 32]
        if len(descriptor) < 32:
            raise ShapefileReadError("Truncated DBF field descriptor.")
        name = _decode_text(descriptor[0:11].split(b"\x00", 1)[0])
        field_type = chr(descriptor[11])
        fields.append(
            _DbfField(
                name=name,
                field_type=field_type,
                length=descriptor[16],
                decimals=descriptor[17],
            )
        )
        offset += 32
    return fields


def _parse_dbf_value(raw_value: bytes, field: _DbfField) -> Any:
    value = _decode_text(raw_value).strip()
    if value == "":
        return None
    if field.field_type in {"N", "F"}:
        try:
            if field.decimals == 0 and "." not in value:
                return int(value)
            return float(value)
        except ValueError:
            return value
    if field.field_type == "L":
        return value.upper() in {"Y", "T", "1"}
    return value


def _decode_text(value: bytes) -> str:
    for encoding in ("utf-8", "latin-1"):
        try:
            return value.decode(encoding)
        except UnicodeDecodeError:
            continue
    return value.decode("latin-1", errors="replace")
