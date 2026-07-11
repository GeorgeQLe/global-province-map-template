from __future__ import annotations

import csv
import io
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from shapely import STRtree
from shapely.errors import ShapelyError
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry

from gpm.config import load_profile, qa_thresholds, sea_zone_settings
from gpm.geo.metrics import EARTH_RADIUS_KM, geometry_length_km
from gpm.paths import PROCESSED_DATA_DIR


ADJACENCY_COLUMNS = (
    "from_province_id",
    "to_province_id",
    "adjacency_type",
    "bidirectional",
    "crossing_type",
    "shared_border_km",
    "source_lineage",
)


class AdjacencyBuildError(RuntimeError):
    """Raised when canonical adjacency generation cannot continue."""


@dataclass(frozen=True)
class AdjacencyBuildResult:
    profile_id: str
    province_input: str
    sea_input: str | None
    output: str
    province_count: int
    sea_zone_count: int
    candidate_pair_count: int
    adjacency_count: int
    land_adjacency_count: int
    sea_adjacency_count: int
    port_to_sea_count: int
    strait_count: int
    min_shared_border_km: float
    strait_max_distance_km: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class _Province:
    province_id: str
    geometry: BaseGeometry
    source_lineage: tuple[str, ...]
    kind: str
    parent_land_province_id: str | None = None
    sea_class: str | None = None


def build_land_adjacency(
    profile_id: str,
    *,
    province_input: Path = PROCESSED_DATA_DIR / "provinces.geojson",
    sea_input: Path | None = None,
    output: Path = PROCESSED_DATA_DIR / "adjacency.csv",
) -> AdjacencyBuildResult:
    """Build canonical adjacency CSV for land, sea, port-to-sea, and strait links.

    Land edges require lineal shared borders above the profile QA threshold.
    When sea zones are present, sea-to-sea shared borders, port-to-sea parent
    links, and coastal land-to-land strait shortcuts within the strategy
    distance are also emitted.

    If ``sea_input`` is omitted, the builder looks for ``sea_zones.geojson`` next
    to the province input. Missing sea files leave the graph land-only.
    """
    profile = load_profile(profile_id)
    min_shared_border_km = qa_thresholds(profile)["min_shared_border_km"]
    land_provinces = _load_provinces(province_input, kinds={"land"}, label="province")
    if sea_input is None:
        sea_input = province_input.parent / "sea_zones.geojson"
    sea_path = _optional_sea_path(sea_input)
    sea_zones: list[_Province] = []
    if sea_path is not None:
        sea_zones = _load_provinces(sea_path, kinds={"sea"}, label="sea zone")
        sea_min_shared = float(sea_zone_settings(profile)["min_shared_border_km"])
        strait_max_distance_km = float(sea_zone_settings(profile)["strait_max_distance_km"])
    else:
        sea_min_shared = min_shared_border_km
        strait_max_distance_km = None

    rows: list[dict[str, str]] = []
    candidate_pair_count = 0

    land_rows, land_candidates = _shared_border_rows(
        land_provinces,
        adjacency_type="land",
        crossing_type="shared_border",
        min_shared_border_km=min_shared_border_km,
    )
    rows.extend(land_rows)
    candidate_pair_count += land_candidates
    land_adjacent_pairs = {
        (row["from_province_id"], row["to_province_id"]) for row in land_rows
    }

    sea_rows: list[dict[str, str]] = []
    port_rows: list[dict[str, str]] = []
    strait_rows: list[dict[str, str]] = []
    if sea_zones:
        sea_rows, sea_candidates = _shared_border_rows(
            sea_zones,
            adjacency_type="sea",
            crossing_type="shared_border",
            min_shared_border_km=sea_min_shared,
        )
        rows.extend(sea_rows)
        candidate_pair_count += sea_candidates

        port_rows = _port_to_sea_rows(land_provinces, sea_zones)
        rows.extend(port_rows)

        assert strait_max_distance_km is not None
        strait_rows, strait_candidates = _strait_rows(
            land_provinces,
            sea_zones,
            land_adjacent_pairs=land_adjacent_pairs,
            max_distance_km=strait_max_distance_km,
        )
        rows.extend(strait_rows)
        candidate_pair_count += strait_candidates

    rows.sort(
        key=lambda row: (
            row["adjacency_type"],
            row["from_province_id"],
            row["to_province_id"],
            row["crossing_type"],
        )
    )
    payload = io.StringIO(newline="")
    writer = csv.DictWriter(payload, fieldnames=ADJACENCY_COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload.getvalue(), encoding="utf-8", newline="")
    except OSError as exc:
        raise AdjacencyBuildError(f"Cannot write adjacency CSV {output}: {exc}") from exc

    return AdjacencyBuildResult(
        profile_id=profile_id,
        province_input=str(province_input),
        sea_input=None if sea_path is None else str(sea_path),
        output=str(output),
        province_count=len(land_provinces),
        sea_zone_count=len(sea_zones),
        candidate_pair_count=candidate_pair_count,
        adjacency_count=len(rows),
        land_adjacency_count=len(land_rows),
        sea_adjacency_count=len(sea_rows),
        port_to_sea_count=len(port_rows),
        strait_count=len(strait_rows),
        min_shared_border_km=min_shared_border_km,
        strait_max_distance_km=strait_max_distance_km,
    )


def _optional_sea_path(sea_input: Path | None) -> Path | None:
    if sea_input is None:
        return None
    if not sea_input.exists():
        return None
    if not sea_input.is_file():
        raise AdjacencyBuildError(f"Sea-zone input is not a file: {sea_input}")
    return sea_input


def _shared_border_rows(
    provinces: list[_Province],
    *,
    adjacency_type: str,
    crossing_type: str,
    min_shared_border_km: float,
) -> tuple[list[dict[str, str]], int]:
    geometries = [province.geometry for province in provinces]
    tree = STRtree(geometries)
    rows: list[dict[str, str]] = []
    candidate_pair_count = 0
    try:
        for index, province in enumerate(provinces):
            for candidate_index_value in tree.query(province.geometry):
                candidate_index = int(candidate_index_value)
                if candidate_index <= index:
                    continue
                candidate_pair_count += 1
                candidate = provinces[candidate_index]
                shared_boundary = province.geometry.boundary.intersection(candidate.geometry.boundary)
                shared_border_km = geometry_length_km(shared_boundary)
                if shared_border_km + 1e-12 < min_shared_border_km:
                    continue
                from_id, to_id = sorted((province.province_id, candidate.province_id))
                lineage = sorted(set(province.source_lineage) | set(candidate.source_lineage))
                rows.append(
                    {
                        "from_province_id": from_id,
                        "to_province_id": to_id,
                        "adjacency_type": adjacency_type,
                        "bidirectional": "true",
                        "crossing_type": crossing_type,
                        "shared_border_km": _format_distance(shared_border_km),
                        "source_lineage": json.dumps(lineage, ensure_ascii=False, separators=(",", ":")),
                    }
                )
    except ShapelyError as exc:
        raise AdjacencyBuildError(f"Geometry overlay failed while building adjacency: {exc}") from exc
    return rows, candidate_pair_count


def _port_to_sea_rows(
    land_provinces: list[_Province],
    sea_zones: list[_Province],
) -> list[dict[str, str]]:
    land_by_id = {province.province_id: province for province in land_provinces}
    rows: list[dict[str, str]] = []
    for sea in sea_zones:
        parent_id = sea.parent_land_province_id
        if not parent_id or parent_id not in land_by_id:
            continue
        land = land_by_id[parent_id]
        from_id, to_id = sorted((land.province_id, sea.province_id))
        lineage = sorted(set(land.source_lineage) | set(sea.source_lineage))
        rows.append(
            {
                "from_province_id": from_id,
                "to_province_id": to_id,
                "adjacency_type": "port_to_sea",
                "bidirectional": "true",
                "crossing_type": "port",
                "shared_border_km": "",
                "source_lineage": json.dumps(lineage, ensure_ascii=False, separators=(",", ":")),
            }
        )
    rows.sort(key=lambda row: (row["from_province_id"], row["to_province_id"]))
    return rows


def _strait_rows(
    land_provinces: list[_Province],
    sea_zones: list[_Province],
    *,
    land_adjacent_pairs: set[tuple[str, str]],
    max_distance_km: float,
) -> tuple[list[dict[str, str]], int]:
    """Emit land-to-land strait links for coastal provinces separated only by water."""
    coastal_parent_ids = {
        sea.parent_land_province_id
        for sea in sea_zones
        if sea.sea_class == "coastal" and sea.parent_land_province_id
    }
    coastal_land = [province for province in land_provinces if province.province_id in coastal_parent_ids]
    if len(coastal_land) < 2:
        return [], 0

    max_distance_deg = max_distance_km / (2 * math.pi * EARTH_RADIUS_KM / 360.0)
    geometries = [province.geometry for province in coastal_land]
    tree = STRtree(geometries)
    rows: list[dict[str, str]] = []
    candidate_pair_count = 0
    try:
        for index, province in enumerate(coastal_land):
            search = province.geometry.buffer(max_distance_deg)
            for candidate_index_value in tree.query(search):
                candidate_index = int(candidate_index_value)
                if candidate_index <= index:
                    continue
                candidate_pair_count += 1
                candidate = coastal_land[candidate_index]
                pair = tuple(sorted((province.province_id, candidate.province_id)))
                if pair in land_adjacent_pairs:
                    continue
                distance_deg = province.geometry.distance(candidate.geometry)
                distance_km = distance_deg * (2 * math.pi * EARTH_RADIUS_KM / 360.0)
                if distance_km + 1e-12 > max_distance_km:
                    continue
                # Require a water gap: polygons must not touch on land.
                if province.geometry.touches(candidate.geometry) or province.geometry.intersects(
                    candidate.geometry
                ):
                    continue
                lineage = sorted(set(province.source_lineage) | set(candidate.source_lineage))
                rows.append(
                    {
                        "from_province_id": pair[0],
                        "to_province_id": pair[1],
                        "adjacency_type": "strait",
                        "bidirectional": "true",
                        "crossing_type": "strait",
                        "shared_border_km": _format_distance(distance_km),
                        "source_lineage": json.dumps(lineage, ensure_ascii=False, separators=(",", ":")),
                    }
                )
    except ShapelyError as exc:
        raise AdjacencyBuildError(f"Geometry overlay failed while detecting straits: {exc}") from exc
    rows.sort(key=lambda row: (row["from_province_id"], row["to_province_id"]))
    return rows, candidate_pair_count


def _load_provinces(path: Path, *, kinds: set[str], label: str) -> list[_Province]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise AdjacencyBuildError(f"{label.capitalize()} input does not exist: {path}") from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AdjacencyBuildError(f"Cannot read {label} GeoJSON {path}: {exc}") from exc
    if not isinstance(document, dict) or document.get("type") != "FeatureCollection":
        raise AdjacencyBuildError(f"{label.capitalize()} input must be a GeoJSON FeatureCollection: {path}")
    features = document.get("features")
    if not isinstance(features, list):
        raise AdjacencyBuildError(f"{label.capitalize()} GeoJSON features must be an array: {path}")

    provinces: list[_Province] = []
    seen_ids: set[str] = set()
    for index, feature in enumerate(features):
        feature_label = f"features[{index}]"
        if not isinstance(feature, dict) or not isinstance(feature.get("properties"), dict):
            raise AdjacencyBuildError(f"{label.capitalize()} {feature_label} must have an object properties member.")
        properties = feature["properties"]
        kind = properties.get("kind")
        if kind not in kinds:
            continue
        province_id = properties.get("province_id")
        if not isinstance(province_id, str) or not province_id:
            raise AdjacencyBuildError(f"{label.capitalize()} {feature_label} must have a non-empty province_id.")
        if province_id in seen_ids:
            raise AdjacencyBuildError(f"Duplicate province_id in {label} input: {province_id}")
        seen_ids.add(province_id)
        geometry_mapping = feature.get("geometry")
        if not isinstance(geometry_mapping, dict) or geometry_mapping.get("type") not in {
            "Polygon",
            "MultiPolygon",
        }:
            raise AdjacencyBuildError(
                f"{label.capitalize()} {province_id} must have Polygon or MultiPolygon geometry."
            )
        try:
            geometry = shape(geometry_mapping)
        except (ShapelyError, TypeError, ValueError) as exc:
            raise AdjacencyBuildError(f"Malformed geometry for {label} {province_id}: {exc}") from exc
        if geometry.is_empty:
            raise AdjacencyBuildError(f"{label.capitalize()} {province_id} has empty geometry.")
        source_lineage = properties.get("source_lineage")
        if not isinstance(source_lineage, list) or not all(
            isinstance(item, str) and item for item in source_lineage
        ):
            raise AdjacencyBuildError(f"{label.capitalize()} {province_id} has malformed source_lineage.")
        parent_land = properties.get("parent_land_province_id")
        sea_class = properties.get("sea_class")
        provinces.append(
            _Province(
                province_id=province_id,
                geometry=geometry,
                source_lineage=tuple(source_lineage),
                kind=str(kind),
                parent_land_province_id=parent_land if isinstance(parent_land, str) else None,
                sea_class=sea_class if isinstance(sea_class, str) else None,
            )
        )
    provinces.sort(key=lambda province: province.province_id)
    return provinces


def _format_distance(value: float) -> str:
    return f"{value:.6f}".rstrip("0").rstrip(".")
