from __future__ import annotations

import hashlib
import heapq
import json
import math
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from shapely import STRtree, normalize, to_wkb, voronoi_polygons
from shapely.errors import ShapelyError
from shapely.geometry import MultiPoint, Point, box, mapping, shape
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from gpm.geo.metrics import geometry_area_sq_km, polygon_parts


class ProvinceRefinementError(RuntimeError):
    """Raised when population-weighted province refinement cannot continue."""


@dataclass(frozen=True)
class RefinementSettings:
    target_province_count: int
    population_weight: float
    min_area_sq_km: float
    min_population: float
    max_split_parts: int
    max_seed_candidates: int = 512


@dataclass(frozen=True)
class ProvinceRefinementResult:
    features: tuple[dict[str, Any], ...]
    split_count: int
    split_parent_count: int
    merged_fragment_count: int
    skipped_invalid_count: int
    population_total: float | None
    population_sample_count: int
    settlement_count: int
    strategy: str
    source_lineage: tuple[str, ...]
    license_lineage: tuple[str, ...]


@dataclass(frozen=True)
class _WeightedPoint:
    point: Point
    weight: float
    stable_id: str
    kind: str


@dataclass(frozen=True)
class _PopulationSummary:
    total: float
    sample_count: int
    hotspots: tuple[_WeightedPoint, ...]


@dataclass
class _Parent:
    feature: dict[str, Any]
    province_id: str
    geometry: BaseGeometry
    area_sq_km: float
    population: float
    population_sample_count: int
    hotspots: tuple[_WeightedPoint, ...]
    settlements: tuple[_WeightedPoint, ...]
    refinable: bool
    desired_parts: int = 1


@dataclass
class _Cell:
    geometry: BaseGeometry
    population: float
    settlement_count: int


class _PopulationSurface:
    source_lineage: tuple[str, ...]
    license_lineage: tuple[str, ...]
    method: str

    def summarize(self, geometry: BaseGeometry, max_hotspots: int) -> _PopulationSummary:
        raise NotImplementedError

    def close(self) -> None:
        return None


class _PointSurface(_PopulationSurface):
    def __init__(
        self,
        points: list[_WeightedPoint],
        *,
        source_lineage: tuple[str, ...],
        license_lineage: tuple[str, ...],
        method: str,
    ) -> None:
        self.points = tuple(points)
        self.geometries = tuple(item.point for item in points)
        self.tree = STRtree(self.geometries) if self.geometries else None
        self.source_lineage = source_lineage
        self.license_lineage = license_lineage
        self.method = method

    def summarize(self, geometry: BaseGeometry, max_hotspots: int) -> _PopulationSummary:
        matches = _points_covered_by(geometry, self.points, self.tree)
        ordered = sorted(matches, key=lambda item: (-item.weight, item.stable_id))
        hotspots = tuple(ordered[:max_hotspots]) if max_hotspots > 0 else ()
        return _PopulationSummary(
            total=sum(item.weight for item in matches),
            sample_count=len(matches),
            hotspots=hotspots,
        )


class _RasterSurface(_PopulationSurface):
    def __init__(
        self,
        path: Path,
        *,
        source_lineage: tuple[str, ...],
        license_lineage: tuple[str, ...],
    ) -> None:
        try:
            import rasterio
        except ImportError as exc:  # pragma: no cover - dependency failure path
            raise ProvinceRefinementError(
                "GeoTIFF population inputs require Rasterio; install the project dependencies first."
            ) from exc

        try:
            self.dataset = rasterio.open(path)
        except (OSError, rasterio.errors.RasterioError) as exc:
            raise ProvinceRefinementError(f"Cannot open population raster {path}: {exc}") from exc
        if self.dataset.count < 1:
            self.dataset.close()
            raise ProvinceRefinementError(f"Population raster has no bands: {path}")
        if self.dataset.crs is None:
            self.dataset.close()
            raise ProvinceRefinementError(f"Population raster must declare a CRS: {path}")
        self.source_lineage = source_lineage
        self.license_lineage = license_lineage
        self.method = "population-raster-cell-sum"

    def summarize(self, geometry: BaseGeometry, max_hotspots: int) -> _PopulationSummary:
        import numpy as np
        from rasterio.errors import WindowError
        from rasterio.features import geometry_mask, geometry_window
        from rasterio.warp import transform, transform_geom
        from rasterio.windows import transform as window_transform

        try:
            raster_geometry = transform_geom(
                "EPSG:4326",
                self.dataset.crs,
                mapping(geometry),
                antimeridian_cutting=True,
                precision=12,
            )
            window = geometry_window(self.dataset, [raster_geometry])
        except (ValueError, WindowError) as exc:
            if isinstance(exc, WindowError):
                return _PopulationSummary(0.0, 0, ())
            raise ProvinceRefinementError(f"Cannot project province geometry into population raster: {exc}") from exc

        data = self.dataset.read(1, window=window, masked=True)
        transform_for_window = window_transform(window, self.dataset.transform)
        inside = geometry_mask(
            [raster_geometry],
            out_shape=data.shape,
            transform=transform_for_window,
            invert=True,
            all_touched=False,
        )
        values = np.asarray(data.filled(np.nan), dtype="float64")
        valid = inside & np.isfinite(values) & (values > 0)
        if not np.any(valid):
            return _PopulationSummary(0.0, 0, ())

        valid_rows, valid_cols = np.nonzero(valid)
        valid_values = values[valid]
        total = float(valid_values.sum())
        hotspots: tuple[_WeightedPoint, ...] = ()
        if max_hotspots > 0:
            take = min(max_hotspots, len(valid_values))
            if take == len(valid_values):
                chosen = np.arange(len(valid_values))
            else:
                chosen = np.argpartition(valid_values, -take)[-take:]
            chosen = sorted(
                (int(index) for index in chosen),
                key=lambda index: (
                    -float(valid_values[index]),
                    int(valid_rows[index]),
                    int(valid_cols[index]),
                ),
            )
            raster_xs: list[float] = []
            raster_ys: list[float] = []
            for index in chosen:
                x, y = self.dataset.xy(
                    int(valid_rows[index] + window.row_off),
                    int(valid_cols[index] + window.col_off),
                )
                raster_xs.append(float(x))
                raster_ys.append(float(y))
            longitudes, latitudes = transform(self.dataset.crs, "EPSG:4326", raster_xs, raster_ys)
            items = []
            for rank, (index, longitude, latitude) in enumerate(
                zip(chosen, longitudes, latitudes, strict=True)
            ):
                point = Point(float(longitude), float(latitude))
                if not geometry.covers(point):
                    continue
                items.append(
                    _WeightedPoint(
                        point=point,
                        weight=float(valid_values[index]),
                        stable_id=f"raster:{valid_rows[index]}:{valid_cols[index]}:{rank}",
                        kind="population",
                    )
                )
            hotspots = tuple(items)
        return _PopulationSummary(total, len(valid_values), hotspots)

    def close(self) -> None:
        self.dataset.close()


def refine_land_provinces(
    features: list[dict[str, Any]],
    *,
    settings: RefinementSettings,
    population_input: Path | None = None,
    settlement_input: Path | None = None,
    population_license_lineage: tuple[str, ...] = (),
    settlement_license_lineage: tuple[str, ...] = (),
) -> ProvinceRefinementResult:
    """Split and merge land provinces using deterministic population-aware seeds."""
    _validate_settings(settings)
    if not features:
        raise ProvinceRefinementError("Province refinement requires at least one input feature.")

    population_surface = _load_population_surface(
        population_input,
        license_lineage=population_license_lineage,
    )
    try:
        settlements, settlement_lineage, settlement_licenses = _load_point_dataset(
            settlement_input,
            dataset_kind="settlement",
            default_weight=1.0,
            explicit_license_lineage=settlement_license_lineage,
        )
    except Exception:
        if population_surface is not None:
            population_surface.close()
        raise
    settlement_tree = STRtree([item.point for item in settlements]) if settlements else None
    using_settlements_as_population = population_surface is None and bool(settlements)
    if using_settlements_as_population:
        population_surface = _PointSurface(
            settlements,
            source_lineage=settlement_lineage,
            license_lineage=settlement_licenses,
            method="settlement-population-sum",
        )

    try:
        parents = _load_parents(features, population_surface, settlements, settlement_tree, settings)
        _allocate_parts(parents, settings)
        output_features: list[dict[str, Any]] = []
        split_count = 0
        split_parent_count = 0
        merged_fragment_count = 0
        for parent in parents:
            cells = _split_parent(parent, population_surface, settings)
            if len(cells) > 1:
                split_parent_count += 1
                split_count += len(cells) - 1
            cells, merged = _merge_tiny_cells(cells, settings, population_available=population_surface is not None)
            merged_fragment_count += merged
            output_features.extend(
                _features_from_cells(
                    parent,
                    cells,
                    population_method=population_surface.method if population_surface is not None else "unavailable",
                    source_lineage=_combined_lineage(
                        population_surface.source_lineage if population_surface is not None else (),
                        settlement_lineage,
                    ),
                    license_lineage=_combined_lineage(
                        population_surface.license_lineage if population_surface is not None else (),
                        settlement_licenses,
                    ),
                )
            )
    finally:
        if population_surface is not None:
            population_surface.close()

    output_features.sort(key=lambda item: item["properties"]["province_id"])
    province_ids = [item["properties"]["province_id"] for item in output_features]
    if len(province_ids) != len(set(province_ids)):
        raise ProvinceRefinementError("M4 refinement produced duplicate deterministic province IDs.")

    population_total = sum(parent.population for parent in parents) if population_surface is not None else None
    strategy = "population-weighted-voronoi" if population_surface is not None else "area-weighted-voronoi"
    source_lineage = _combined_lineage(
        population_surface.source_lineage if population_surface is not None else (),
        settlement_lineage,
    )
    license_lineage = _combined_lineage(
        population_surface.license_lineage if population_surface is not None else (),
        settlement_licenses,
    )
    return ProvinceRefinementResult(
        features=tuple(output_features),
        split_count=split_count,
        split_parent_count=split_parent_count,
        merged_fragment_count=merged_fragment_count,
        skipped_invalid_count=sum(not parent.refinable for parent in parents),
        population_total=population_total,
        population_sample_count=sum(parent.population_sample_count for parent in parents),
        settlement_count=len(settlements),
        strategy=strategy,
        source_lineage=source_lineage,
        license_lineage=license_lineage,
    )


def _validate_settings(settings: RefinementSettings) -> None:
    if settings.target_province_count <= 0:
        raise ProvinceRefinementError("Refinement target_province_count must be positive.")
    if not 0 <= settings.population_weight <= 1:
        raise ProvinceRefinementError("Refinement population_weight must be between 0 and 1.")
    if settings.min_area_sq_km < 0 or settings.min_population < 0:
        raise ProvinceRefinementError("Refinement minimum area and population cannot be negative.")
    if settings.max_split_parts < 1:
        raise ProvinceRefinementError("Refinement max_split_parts must be at least 1.")
    if settings.max_seed_candidates < settings.max_split_parts:
        raise ProvinceRefinementError("Refinement max_seed_candidates must cover max_split_parts.")


def _load_population_surface(
    path: Path | None,
    *,
    license_lineage: tuple[str, ...],
) -> _PopulationSurface | None:
    if path is None:
        return None
    expanded = path.expanduser()
    if not expanded.is_file():
        raise ProvinceRefinementError(f"Population input does not exist: {path}")
    suffix = expanded.suffix.lower()
    if suffix in {".tif", ".tiff"}:
        if not any(item for item in license_lineage if item):
            raise ProvinceRefinementError(
                "Population raster requires at least one --population-license/license-lineage notice."
            )
        return _RasterSurface(
            expanded,
            source_lineage=(f"population:{expanded.resolve()}",),
            license_lineage=license_lineage,
        )
    points, source_lineage, embedded_licenses = _load_point_dataset(
        expanded,
        dataset_kind="population",
        default_weight=None,
        explicit_license_lineage=license_lineage,
    )
    return _PointSurface(
        points,
        source_lineage=source_lineage,
        license_lineage=embedded_licenses,
        method="population-point-sum",
    )


def _load_point_dataset(
    path: Path | None,
    *,
    dataset_kind: str,
    default_weight: float | None,
    explicit_license_lineage: tuple[str, ...],
) -> tuple[list[_WeightedPoint], tuple[str, ...], tuple[str, ...]]:
    if path is None:
        return [], (), tuple(sorted(set(explicit_license_lineage)))
    expanded = path.expanduser()
    if not expanded.is_file():
        raise ProvinceRefinementError(f"{dataset_kind.title()} input does not exist: {path}")
    if expanded.suffix.lower() not in {".json", ".geojson"}:
        raise ProvinceRefinementError(
            f"{dataset_kind.title()} point input must be GeoJSON: {expanded}"
        )
    try:
        document = json.loads(expanded.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ProvinceRefinementError(f"Cannot read {dataset_kind} GeoJSON {expanded}: {exc}") from exc
    if not isinstance(document, dict) or document.get("type") != "FeatureCollection":
        raise ProvinceRefinementError(f"{dataset_kind.title()} input must be a GeoJSON FeatureCollection.")
    crs = document.get("crs")
    if crs is not None and not _is_wgs84_crs(crs):
        raise ProvinceRefinementError(f"{dataset_kind.title()} GeoJSON must use WGS84 longitude/latitude.")
    raw_features = document.get("features")
    if not isinstance(raw_features, list):
        raise ProvinceRefinementError(f"{dataset_kind.title()} GeoJSON features must be an array.")

    points: list[_WeightedPoint] = []
    for index, feature in enumerate(raw_features):
        if not isinstance(feature, dict):
            raise ProvinceRefinementError(f"{dataset_kind.title()} feature[{index}] must be an object.")
        geometry_mapping = feature.get("geometry")
        if not isinstance(geometry_mapping, dict) or geometry_mapping.get("type") != "Point":
            raise ProvinceRefinementError(
                f"{dataset_kind.title()} feature[{index}] geometry must be a GeoJSON Point."
            )
        try:
            point = shape(geometry_mapping)
        except (ShapelyError, TypeError, ValueError) as exc:
            raise ProvinceRefinementError(
                f"Cannot parse {dataset_kind} feature[{index}] geometry: {exc}"
            ) from exc
        if point.is_empty or not point.is_valid:
            raise ProvinceRefinementError(f"{dataset_kind.title()} feature[{index}] point is invalid.")
        properties = feature.get("properties")
        if not isinstance(properties, dict):
            properties = {}
        weight = _point_weight(properties, default_weight)
        if weight is None:
            raise ProvinceRefinementError(
                f"{dataset_kind.title()} feature[{index}] requires a non-negative population/value field."
            )
        stable_id = str(feature.get("id") or properties.get("id") or f"feature[{index}]")
        points.append(_WeightedPoint(point, weight, stable_id, dataset_kind))

    metadata = document.get("gpm") if isinstance(document.get("gpm"), dict) else {}
    embedded_lineage = _string_array(metadata.get("source_lineage"))
    embedded_licenses = _string_array(metadata.get("license_lineage"))
    source_lineage = _combined_lineage(
        embedded_lineage,
        (f"{dataset_kind}:{expanded.resolve()}",),
    )
    licenses = _combined_lineage(embedded_licenses, explicit_license_lineage)
    if not licenses:
        option = "--population-license" if dataset_kind == "population" else "--settlement-license"
        raise ProvinceRefinementError(
            f"{dataset_kind.title()} input must declare gpm.license_lineage or provide {option}."
        )
    return points, source_lineage, licenses


def _is_wgs84_crs(crs: Any) -> bool:
    encoded = json.dumps(crs, sort_keys=True).lower()
    return any(token in encoded for token in ("epsg:4326", "urn:ogc:def:crs:ogc:1.3:crs84", "crs84"))


def _point_weight(properties: dict[str, Any], default: float | None) -> float | None:
    by_lower = {str(key).lower(): value for key, value in properties.items()}
    for key in (
        "population",
        "population_count",
        "estimated_population",
        "pop_max",
        "pop_min",
        "pop",
        "value",
        "weight",
    ):
        value = by_lower.get(key)
        if value is None or isinstance(value, bool):
            continue
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(parsed) and parsed >= 0:
            return parsed
    return default


def _load_parents(
    features: list[dict[str, Any]],
    population_surface: _PopulationSurface | None,
    settlements: list[_WeightedPoint],
    settlement_tree: STRtree | None,
    settings: RefinementSettings,
) -> list[_Parent]:
    parents: list[_Parent] = []
    seen_ids: set[str] = set()
    for index, feature in enumerate(features):
        if not isinstance(feature, dict) or feature.get("type") != "Feature":
            raise ProvinceRefinementError(f"Province feature[{index}] must be a GeoJSON Feature.")
        properties = feature.get("properties")
        if not isinstance(properties, dict):
            raise ProvinceRefinementError(f"Province feature[{index}] properties must be an object.")
        province_id = properties.get("province_id")
        if not isinstance(province_id, str) or not province_id:
            raise ProvinceRefinementError(f"Province feature[{index}] requires a province_id.")
        if province_id in seen_ids:
            raise ProvinceRefinementError(f"Province refinement input duplicates ID {province_id!r}.")
        seen_ids.add(province_id)
        try:
            geometry = shape(feature.get("geometry"))
        except (ShapelyError, TypeError, ValueError) as exc:
            raise ProvinceRefinementError(f"Cannot parse province {province_id!r} geometry: {exc}") from exc
        if geometry.geom_type not in {"Polygon", "MultiPolygon"} or geometry.is_empty:
            raise ProvinceRefinementError(
                f"Province {province_id!r} must have non-empty Polygon/MultiPolygon geometry."
            )
        population = (
            population_surface.summarize(geometry, settings.max_seed_candidates)
            if population_surface is not None
            else _PopulationSummary(0.0, 0, ())
        )
        covered_settlements = tuple(_points_covered_by(geometry, settlements, settlement_tree))
        parents.append(
            _Parent(
                feature=feature,
                province_id=province_id,
                geometry=geometry,
                area_sq_km=geometry_area_sq_km(geometry),
                population=population.total,
                population_sample_count=population.sample_count,
                hotspots=population.hotspots,
                settlements=covered_settlements,
                refinable=geometry.is_valid,
            )
        )
    return sorted(parents, key=lambda item: item.province_id)


def _points_covered_by(
    geometry: BaseGeometry,
    points: tuple[_WeightedPoint, ...] | list[_WeightedPoint],
    tree: STRtree | None,
) -> list[_WeightedPoint]:
    if tree is None:
        return []
    matches = []
    for raw_index in tree.query(geometry):
        index = int(raw_index)
        item = points[index]
        if geometry.covers(item.point):
            matches.append(item)
    return matches


def _allocate_parts(parents: list[_Parent], settings: RefinementSettings) -> None:
    parent_count = len(parents)
    target = settings.target_province_count
    if target < parent_count:
        raise ProvinceRefinementError(
            f"Refinement target {target} is below the {parent_count} source province count; "
            "M4 only merges fragments created within a source province."
        )
    capacity = sum(settings.max_split_parts if parent.refinable else 1 for parent in parents)
    if target > capacity:
        raise ProvinceRefinementError(
            f"Refinement target {target} exceeds max_split_parts capacity {capacity}."
        )
    if target == parent_count:
        return

    refinable_parents = [parent for parent in parents if parent.refinable]
    total_area = sum(parent.area_sq_km for parent in refinable_parents)
    total_population = sum(parent.population for parent in refinable_parents)
    use_population = total_population > 0 and settings.population_weight > 0
    area_weight = 1.0 - settings.population_weight if use_population else 1.0
    population_weight = settings.population_weight if use_population else 0.0

    weights: list[float] = []
    for parent in parents:
        if not parent.refinable:
            weights.append(0.0)
            continue
        area_share = (
            parent.area_sq_km / total_area if total_area > 0 else 1 / len(refinable_parents)
        )
        population_share = parent.population / total_population if total_population > 0 else 0.0
        weights.append((area_weight * area_share) + (population_weight * population_share))

    heap: list[tuple[float, str, int]] = []
    for index, (parent, weight) in enumerate(zip(parents, weights, strict=True)):
        if not parent.refinable:
            continue
        heapq.heappush(heap, (-weight / 1.5, parent.province_id, index))
    for _ in range(target - parent_count):
        while heap:
            _, _, index = heapq.heappop(heap)
            parent = parents[index]
            if parent.desired_parts < settings.max_split_parts:
                break
        else:  # pragma: no cover - capacity check makes this unreachable
            raise ProvinceRefinementError("Refinement part allocation exhausted unexpectedly.")
        parent.desired_parts += 1
        if parent.desired_parts < settings.max_split_parts:
            heapq.heappush(
                heap,
                (
                    -weights[index] / (parent.desired_parts + 0.5),
                    parent.province_id,
                    index,
                ),
            )


def _split_parent(
    parent: _Parent,
    population_surface: _PopulationSurface | None,
    settings: RefinementSettings,
) -> list[_Cell]:
    if parent.desired_parts == 1 or not parent.refinable:
        return [_Cell(parent.geometry, parent.population, len(parent.settlements))]
    seeds = _select_seeds(parent, parent.desired_parts)
    if len(seeds) < 2:
        return [_Cell(parent.geometry, parent.population, len(parent.settlements))]
    try:
        diagram = voronoi_polygons(
            MultiPoint([item.point for item in seeds]),
            extend_to=parent.geometry.envelope,
            ordered=True,
        )
        geometries = []
        for raw_cell in diagram.geoms:
            clipped = _polygonal_geometry(parent.geometry.intersection(raw_cell))
            if not clipped.is_empty:
                geometries.append(clipped)
    except (ShapelyError, ValueError) as exc:
        raise ProvinceRefinementError(f"Cannot split province {parent.province_id!r}: {exc}") from exc
    if len(geometries) < 2:
        return [_Cell(parent.geometry, parent.population, len(parent.settlements))]

    raw_populations = [
        population_surface.summarize(geometry, 0).total if population_surface is not None else 0.0
        for geometry in geometries
    ]
    population_sum = sum(raw_populations)
    if population_surface is not None and parent.population > 0:
        if population_sum > 0:
            raw_populations = [value * parent.population / population_sum for value in raw_populations]
        else:
            total_area = sum(geometry_area_sq_km(geometry) for geometry in geometries)
            raw_populations = [
                parent.population * geometry_area_sq_km(geometry) / total_area for geometry in geometries
            ]
    return [
        _Cell(
            geometry=geometry,
            population=raw_population,
            settlement_count=sum(geometry.covers(item.point) for item in parent.settlements),
        )
        for geometry, raw_population in zip(geometries, raw_populations, strict=True)
    ]


def _select_seeds(parent: _Parent, count: int) -> list[_WeightedPoint]:
    candidates_by_coordinate: dict[tuple[float, float], _WeightedPoint] = {}
    for item in (*parent.settlements, *parent.hotspots):
        key = (round(item.point.x, 12), round(item.point.y, 12))
        existing = candidates_by_coordinate.get(key)
        if existing is None or _seed_bias(item) > _seed_bias(existing):
            candidates_by_coordinate[key] = item

    min_x, min_y, max_x, max_y = parent.geometry.bounds
    grid_side = max(3, math.ceil(math.sqrt(count * 10)))
    cell_width = (max_x - min_x) / grid_side if max_x > min_x else 0
    cell_height = (max_y - min_y) / grid_side if max_y > min_y else 0
    for row in range(grid_side):
        for column in range(grid_side):
            cell = box(
                min_x + column * cell_width,
                min_y + row * cell_height,
                min_x + (column + 1) * cell_width,
                min_y + (row + 1) * cell_height,
            )
            center = Point(
                min_x + (column + 0.5) * cell_width,
                min_y + (row + 0.5) * cell_height,
            )
            if parent.geometry.covers(center):
                point = center
            elif parent.geometry.intersects(cell):
                intersection = parent.geometry.intersection(cell)
                if intersection.is_empty:
                    continue
                point = intersection.representative_point()
            else:
                continue
            key = (round(point.x, 12), round(point.y, 12))
            candidates_by_coordinate.setdefault(
                key,
                _WeightedPoint(point, 0.0, f"grid:{row:04d}:{column:04d}", "grid"),
            )

    for index, part in enumerate(polygon_parts(parent.geometry)):
        point = part.representative_point()
        key = (round(point.x, 12), round(point.y, 12))
        candidates_by_coordinate.setdefault(
            key,
            _WeightedPoint(point, 0.0, f"part:{index:04d}", "grid"),
        )
    candidates = sorted(candidates_by_coordinate.values(), key=lambda item: item.stable_id)
    if len(candidates) <= count:
        return candidates

    first_index = max(range(len(candidates)), key=lambda index: (_seed_bias(candidates[index]), -index))
    selected = [candidates.pop(first_index)]
    while candidates and len(selected) < count:
        best_index = max(
            range(len(candidates)),
            key=lambda index: (
                _minimum_seed_distance_sq(candidates[index].point, selected)
                * (1.0 + _seed_bias(candidates[index])),
                -index,
            ),
        )
        selected.append(candidates.pop(best_index))
    return selected


def _seed_bias(item: _WeightedPoint) -> float:
    kind_bias = 2.0 if item.kind == "settlement" else (1.0 if item.kind == "population" else 0.0)
    return kind_bias + math.log1p(item.weight)


def _minimum_seed_distance_sq(point: Point, selected: list[_WeightedPoint]) -> float:
    return min(_lon_lat_distance_sq(point, item.point) for item in selected)


def _lon_lat_distance_sq(first: Point, second: Point) -> float:
    mean_latitude = math.radians((first.y + second.y) / 2)
    delta_x = (first.x - second.x) * math.cos(mean_latitude)
    delta_y = first.y - second.y
    return (delta_x * delta_x) + (delta_y * delta_y)


def _polygonal_geometry(geometry: BaseGeometry) -> BaseGeometry:
    parts = list(polygon_parts(geometry))
    if not parts:
        return geometry.__class__()
    return parts[0] if len(parts) == 1 else unary_union(parts)


def _merge_tiny_cells(
    cells: list[_Cell],
    settings: RefinementSettings,
    *,
    population_available: bool,
) -> tuple[list[_Cell], int]:
    merged_count = 0
    while len(cells) > 1:
        tiny_indices = [
            index
            for index, cell in enumerate(cells)
            if _is_tiny_cell(cell, settings, population_available=population_available)
        ]
        if not tiny_indices:
            break
        source_index = min(
            tiny_indices,
            key=lambda index: (
                geometry_area_sq_km(cells[index].geometry),
                cells[index].population,
                cells[index].geometry.wkb_hex,
            ),
        )
        source = cells[source_index]
        neighbor_indices = [index for index in range(len(cells)) if index != source_index]
        target_index = max(
            neighbor_indices,
            key=lambda index: (
                source.geometry.boundary.intersection(cells[index].geometry.boundary).length,
                -source.geometry.distance(cells[index].geometry),
                geometry_area_sq_km(cells[index].geometry),
                cells[index].geometry.wkb_hex,
            ),
        )
        target = cells[target_index]
        merged = _Cell(
            geometry=unary_union([source.geometry, target.geometry]),
            population=source.population + target.population,
            settlement_count=source.settlement_count + target.settlement_count,
        )
        for index in sorted((source_index, target_index), reverse=True):
            cells.pop(index)
        cells.append(merged)
        merged_count += 1
    return cells, merged_count


def _is_tiny_cell(
    cell: _Cell,
    settings: RefinementSettings,
    *,
    population_available: bool,
) -> bool:
    area = geometry_area_sq_km(cell.geometry)
    extremely_small = settings.min_area_sq_km > 0 and area < settings.min_area_sq_km * 0.05
    below_area = settings.min_area_sq_km > 0 and area < settings.min_area_sq_km
    below_population = (
        population_available
        and settings.min_population > 0
        and cell.population < settings.min_population
    )
    return extremely_small or (below_area and below_population)


def _features_from_cells(
    parent: _Parent,
    cells: list[_Cell],
    *,
    population_method: str,
    source_lineage: tuple[str, ...],
    license_lineage: tuple[str, ...],
) -> list[dict[str, Any]]:
    ordered_cells = sorted(
        cells,
        key=lambda cell: (
            round(cell.geometry.representative_point().y, 12),
            round(cell.geometry.representative_point().x, 12),
            cell.geometry.wkb_hex,
        ),
    )
    part_count = len(ordered_cells)
    features = []
    for part_index, cell in enumerate(ordered_cells, start=1):
        properties = dict(parent.feature["properties"])
        if part_count > 1:
            properties["province_id"] = _refined_province_id(parent.province_id, cell.geometry)
            properties["display_name"] = f"{properties['display_name']} {part_index}"
        properties["area_sq_km"] = round(geometry_area_sq_km(cell.geometry), 3)
        properties["estimated_population"] = (
            round(cell.population, 3) if population_method != "unavailable" else None
        )
        properties["settlement_count"] = cell.settlement_count
        properties["population_estimation_method"] = population_method
        properties["refinement_parent_id"] = parent.province_id
        if parent.refinable:
            properties["refinement_strategy"] = (
                "population-weighted-voronoi"
                if population_method != "unavailable"
                else "area-weighted-voronoi"
            )
        else:
            properties["refinement_strategy"] = "source-geometry-preserved"
            properties["refinement_skipped_reason"] = "invalid-source-geometry"
        properties["refinement_part_index"] = part_index
        properties["refinement_part_count"] = part_count
        properties["source_lineage"] = list(
            _combined_lineage(tuple(properties.get("source_lineage", ())), source_lineage)
        )
        properties["license_lineage"] = list(
            _combined_lineage(tuple(properties.get("license_lineage", ())), license_lineage)
        )
        features.append(
            {
                "type": "Feature",
                "geometry": (
                    parent.feature["geometry"]
                    if not parent.refinable and part_count == 1
                    else mapping(normalize(cell.geometry))
                ),
                "properties": properties,
            }
        )
    return features


def _refined_province_id(parent_id: str, geometry: BaseGeometry) -> str:
    canonical_wkb = to_wkb(normalize(geometry), byte_order=1, include_srid=False)
    digest = hashlib.sha256(parent_id.encode("utf-8") + b"\0" + canonical_wkb).hexdigest()[:12]
    slug = _slug_token(parent_id.removeprefix("ne_"))[:48].rstrip("-") or "province"
    return f"m4_{slug}-{digest}"


def _slug_token(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", errors="ignore").decode("ascii")
    token = []
    previous_dash = False
    for character in value.lower():
        if character.isalnum():
            token.append(character)
            previous_dash = False
        elif not previous_dash:
            token.append("-")
            previous_dash = True
    return "".join(token).strip("-")


def _string_array(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, str) and item)


def _combined_lineage(*groups: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted({item for group in groups for item in group if item}))
