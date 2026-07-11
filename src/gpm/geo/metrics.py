from __future__ import annotations

import math
from collections.abc import Iterator

from shapely.geometry.base import BaseGeometry


EARTH_RADIUS_KM = 6371.0088


def geometry_area_sq_km(geometry: BaseGeometry) -> float:
    """Approximate geodesic area for lon/lat Polygon geometry on a sphere."""
    if geometry.is_empty:
        return 0.0
    if geometry.geom_type == "Polygon":
        exterior = _ring_area_sq_km(geometry.exterior.coords)
        holes = sum(_ring_area_sq_km(ring.coords) for ring in geometry.interiors)
        return max(0.0, exterior - holes)
    if geometry.geom_type in {"MultiPolygon", "GeometryCollection"}:
        return sum(geometry_area_sq_km(part) for part in geometry.geoms)
    return 0.0


def geometry_length_km(geometry: BaseGeometry) -> float:
    """Return the great-circle segment length of lineal lon/lat geometry."""
    if geometry.is_empty:
        return 0.0
    if geometry.geom_type in {"LineString", "LinearRing"}:
        coordinates = list(geometry.coords)
        return sum(_haversine_km(start, end) for start, end in zip(coordinates, coordinates[1:]))
    if geometry.geom_type in {"MultiLineString", "GeometryCollection"}:
        return sum(geometry_length_km(part) for part in geometry.geoms)
    return 0.0


def polygon_parts(geometry: BaseGeometry) -> Iterator[BaseGeometry]:
    if geometry.is_empty:
        return
    if geometry.geom_type == "Polygon":
        yield geometry
    elif geometry.geom_type in {"MultiPolygon", "GeometryCollection"}:
        for part in geometry.geoms:
            yield from polygon_parts(part)


def _ring_area_sq_km(coordinates) -> float:
    points = list(coordinates)
    if len(points) < 4:
        return 0.0
    total = 0.0
    for start, end in zip(points, points[1:]):
        lon1, lat1 = math.radians(start[0]), math.radians(start[1])
        lon2, lat2 = math.radians(end[0]), math.radians(end[1])
        delta_lon = lon2 - lon1
        if delta_lon > math.pi:
            delta_lon -= 2 * math.pi
        elif delta_lon < -math.pi:
            delta_lon += 2 * math.pi
        total += delta_lon * (2 + math.sin(lat1) + math.sin(lat2))
    return abs(total) * (EARTH_RADIUS_KM**2) / 2.0


def _haversine_km(start, end) -> float:
    lon1, lat1 = math.radians(start[0]), math.radians(start[1])
    lon2, lat2 = math.radians(end[0]), math.radians(end[1])
    delta_lon = lon2 - lon1
    if delta_lon > math.pi:
        delta_lon -= 2 * math.pi
    elif delta_lon < -math.pi:
        delta_lon += 2 * math.pi
    delta_lat = lat2 - lat1
    value = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(value)))
