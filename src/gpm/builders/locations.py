from __future__ import annotations

import csv
import hashlib
import heapq
import json
import math
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

import h3
from shapely import make_valid, normalize, to_wkb
from shapely.affinity import translate
from shapely.geometry import GeometryCollection, LineString, MultiPolygon, Polygon, mapping, shape
from shapely.ops import split, unary_union
from shapely.strtree import STRtree

from gpm import __version__
from gpm.builders.provinces import _natural_earth_artifact_paths
from gpm.geo.shapefile import geometry_area_sq_km, read_zipped_shapefile
from gpm.paths import CONFIG_DIR, PROCESSED_DATA_DIR, RAW_DATA_DIR


class LocationBuildError(RuntimeError):
    """Raised when the M23 location fabric cannot be built."""


@dataclass(frozen=True)
class LocationBuildResult:
    fabric_id: str
    fabric_revision: str
    target_location_count: int
    location_count: int
    baseline_cell_count: int
    refined_parent_count: int
    split_request_count: int
    locations_output: str
    adjacency_output: str
    intersections_output: str
    lineage_output: str
    manifest_output: str
    missing_signals: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class _Signal:
    name: str
    path: str
    geometries: tuple[Any, ...]
    values: tuple[float, ...]
    tree: STRtree
    license_lineage: tuple[str, ...]


@dataclass(frozen=True)
class _LandIndex:
    geometries: tuple[Any, ...]
    tree: STRtree


def load_fabric_config(fabric_id: str = "global-h3-v1") -> dict[str, Any]:
    path = CONFIG_DIR / "fabrics" / f"{fabric_id}.json"
    if not path.is_file():
        available = ", ".join(item.stem for item in sorted((CONFIG_DIR / "fabrics").glob("*.json")))
        raise LocationBuildError(f"Unknown fabric '{fabric_id}'. Available fabrics: {available or 'none'}.")
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LocationBuildError(f"Cannot read fabric configuration {path}: {exc}") from exc
    required = {
        "fabric_id", "fabric_revision", "geometry_revision", "baseline_h3_resolution",
        "maximum_h3_resolution", "target_location_count", "weights",
    }
    missing = sorted(required - document.keys())
    if missing:
        raise LocationBuildError(f"Fabric configuration is missing: {', '.join(missing)}")
    if document["fabric_id"] != fabric_id:
        raise LocationBuildError(f"Fabric id mismatch in {path}.")
    return document


def build_location_fabric(
    fabric_id: str = "global-h3-v1",
    *,
    raw_dir: Path = RAW_DATA_DIR,
    output_dir: Path = PROCESSED_DATA_DIR,
    land_input: Path | None = None,
    admin0_input: Path | None = None,
    admin1_input: Path | None = None,
    population_input: Path | None = None,
    settlement_input: Path | None = None,
    terrain_input: Path | None = None,
    historical_signal_input: Path | None = None,
    split_request_input: Path | None = None,
    output_fabric_revision: str | None = None,
    land_license_lineage: tuple[str, ...] = (),
    admin0_license_lineage: tuple[str, ...] = (),
    admin1_license_lineage: tuple[str, ...] = (),
    population_license_lineage: tuple[str, ...] = (),
    settlement_license_lineage: tuple[str, ...] = (),
    terrain_license_lineage: tuple[str, ...] = (),
    historical_license_lineage: tuple[str, ...] = (),
    target_location_count: int | None = None,
    generated_at: str | None = None,
) -> LocationBuildResult:
    """Build a deterministic, clipped, mixed-resolution global H3 location fabric."""
    config = load_fabric_config(fabric_id)
    source_revision = str(config["fabric_revision"])
    if split_request_input is not None and not output_fabric_revision:
        raise LocationBuildError("--output-fabric-revision is required with --split-request-input.")
    if split_request_input is None and output_fabric_revision is not None:
        raise LocationBuildError("--output-fabric-revision is only valid with --split-request-input.")
    output_revision = str(output_fabric_revision or source_revision)
    if split_request_input is not None and output_revision == source_revision:
        raise LocationBuildError("Output fabric revision must differ from the source fabric revision.")
    target = int(target_location_count or config["target_location_count"])
    baseline_resolution = int(config["baseline_h3_resolution"])
    maximum_resolution = int(config["maximum_h3_resolution"])
    if target < 1 or not 0 <= baseline_resolution <= maximum_resolution <= 15:
        raise LocationBuildError("Invalid fabric target or H3 resolution range.")

    land_features, admin0_features, admin1_features, reference_inputs = _load_reference_features(
        raw_dir=raw_dir,
        land_input=land_input,
        admin0_input=admin0_input,
        admin1_input=admin1_input,
        land_licenses=land_license_lineage,
        admin0_licenses=admin0_license_lineage,
        admin1_licenses=admin1_license_lineage,
    )
    land = _polygonal_union(feature["geometry"] for feature in land_features)
    if land.is_empty:
        raise LocationBuildError("Land input contains no polygonal geometry.")
    land_index = _land_index(land)

    signal_specs = (
        ("population", population_input, population_license_lineage),
        ("settlement", settlement_input, settlement_license_lineage),
        ("terrain", terrain_input, terrain_license_lineage),
        ("historical", historical_signal_input, historical_license_lineage),
    )
    signals: dict[str, _Signal] = {}
    for name, path, explicit_licenses in signal_specs:
        if path is not None:
            signals[name] = _load_signal(name, path, explicit_licenses)
    missing_signals = tuple(name for name, path, _licenses in signal_specs if path is None)

    cells: dict[str, list[Any]] = {}
    for cell in _all_cells_at_resolution(baseline_resolution):
        parts = _clip_cell(cell, land_index)
        if parts:
            cells[cell] = parts
    baseline_cell_count = len(cells)
    if not cells:
        raise LocationBuildError("No H3 cells intersect the supplied land mask.")

    lineage_events: list[dict[str, Any]] = []
    refined_parents: set[str] = set()
    weights = dict(config.get("weights") or {})
    location_count = sum(len(parts) for parts in cells.values())
    refinement_queue = [
        (-_cell_score(parts, signals, weights), cell)
        for cell, parts in cells.items()
        if h3.get_resolution(cell) < maximum_resolution
    ]
    heapq.heapify(refinement_queue)
    while location_count < target and refinement_queue:
        _negative_score, parent = heapq.heappop(refinement_queue)
        if parent not in cells or h3.get_resolution(parent) >= maximum_resolution:
            continue
        parent_parts = cells.pop(parent)
        child_cells: list[str] = []
        refined = _refine_partition(parent, parent_parts)
        for child, parts in refined.items():
            if parts:
                cells[child] = parts
                child_cells.append(child)
                if h3.get_resolution(child) < maximum_resolution:
                    heapq.heappush(
                        refinement_queue,
                        (-_cell_score(parts, signals, weights), child),
                    )
        if not child_cells:
            cells[parent] = parent_parts
            break
        location_count += sum(len(cells[child]) for child in child_cells) - len(parent_parts)
        refined_parents.add(parent)
        lineage_events.append({
            "operation": "refine_h3",
            "parent_h3_index": parent,
            "child_h3_indexes": child_cells,
            "parent_location_ids": sorted(_location_id(parent, part) for part in parent_parts),
            "child_location_ids": sorted(
                _location_id(child, part) for child in child_cells for part in cells[child]
            ),
        })

    features = _remove_planar_overlaps(_location_features(
        cells, config, signals, reference_inputs, output_revision, source_revision,
    ))
    # Polar planar cleanup can discard a handful of fully duplicated chord
    # slivers. Continue with the next deterministic refinement batch so the
    # published fabric still meets its declared land-location budget.
    while len(features) < target and refinement_queue:
        _negative_score, parent = heapq.heappop(refinement_queue)
        if parent not in cells or h3.get_resolution(parent) >= maximum_resolution:
            continue
        parent_parts = cells.pop(parent)
        child_cells = []
        for child, parts in _refine_partition(parent, parent_parts).items():
            cells[child] = parts
            child_cells.append(child)
            if h3.get_resolution(child) < maximum_resolution:
                heapq.heappush(refinement_queue, (-_cell_score(parts, signals, weights), child))
        if not child_cells:
            cells[parent] = parent_parts
            break
        refined_parents.add(parent)
        lineage_events.append({
            "operation": "refine_h3",
            "parent_h3_index": parent,
            "child_h3_indexes": child_cells,
            "parent_location_ids": sorted(_location_id(parent, part) for part in parent_parts),
            "child_location_ids": sorted(
                _location_id(child, part) for child in child_cells for part in cells[child]
            ),
        })
        features = _remove_planar_overlaps(_location_features(
            cells, config, signals, reference_inputs, output_revision, source_revision,
        ))
    features = _fill_planar_land_gaps(features, land)
    split_requests = _load_split_requests(split_request_input, config)
    if split_requests:
        features, request_events = _apply_split_requests(features, split_requests, land, config)
        lineage_events.extend(request_events)
    features = _remove_planar_overlaps(features)
    features.sort(key=lambda feature: feature["properties"]["location_id"])
    final_ids_by_h3: dict[str, list[str]] = {}
    for feature in features:
        final_ids_by_h3.setdefault(feature["properties"]["h3_index"], []).append(
            feature["properties"]["location_id"]
        )
    for event in lineage_events:
        child_indexes = event.get("child_h3_indexes")
        if isinstance(child_indexes, list):
            event["child_location_ids"] = sorted(
                location_id for child in child_indexes for location_id in final_ids_by_h3.get(child, [])
            )

    adjacency_rows = build_location_adjacency_rows(features)
    intersections, admin_pieces = build_admin_intersections(
        features,
        admin0_features=admin0_features,
        admin1_features=admin1_features,
    )
    timestamp = generated_at or datetime.now(UTC).replace(microsecond=0).isoformat()
    output_dir = Path(output_dir)
    locations_output = output_dir / "locations.geojson"
    adjacency_output = output_dir / "location_adjacency.csv"
    intersections_output = output_dir / "location_admin_intersections.csv"
    lineage_output = output_dir / "location_lineage.json"
    manifest_output = output_dir / "location_fabric_manifest.json"
    pieces_output = output_dir / "location_admin_pieces.geojson"

    input_records = [*reference_inputs]
    for name, path, _licenses in signal_specs:
        if path is not None:
            signal = signals[name]
            input_records.append({
                "role": name,
                "path": signal.path,
                "format": "geojson",
                "license_lineage": list(signal.license_lineage),
            })
    source_paths = sorted({record["path"] for record in input_records})
    common_lineage = sorted({
        notice for record in input_records for notice in record["license_lineage"]
    })
    collection = {
        "type": "FeatureCollection",
        "gpm": {
            "layer_kind": "locations",
            "fabric_id": fabric_id,
            "fabric_revision": output_revision,
            "source_fabric_revision": source_revision,
            "output_fabric_revision": output_revision,
            "geometry_revision": str(config["geometry_revision"]),
            "generated_at": timestamp,
            "generator_version": __version__,
            "target_location_count": target,
            "actual_location_count": len(features),
            "source_lineage": source_paths,
            "license_lineage": common_lineage,
        },
        "features": features,
    }
    lineage = {
        "schema_version": "0.1.0",
        "fabric_id": fabric_id,
        "fabric_revision": output_revision,
        "source_fabric_revision": source_revision,
        "output_fabric_revision": output_revision,
        "generated_at": timestamp,
        "events": sorted(lineage_events, key=lambda row: json.dumps(row, sort_keys=True)),
    }
    manifest = {
        "schema_version": "0.1.0",
        "manifest_type": "location_fabric",
        "fabric_id": fabric_id,
        "fabric_revision": output_revision,
        "source_fabric_revision": source_revision,
        "output_fabric_revision": output_revision,
        "geometry_revision": str(config["geometry_revision"]),
        "generated_at": timestamp,
        "generator_version": __version__,
        "h3": {
            "library_version": h3.__version__,
            "baseline_resolution": baseline_resolution,
            "maximum_resolution": maximum_resolution,
            "ordering": "lexicographically sorted",
        },
        "target_location_count": target,
        "actual_location_count": len(features),
        "baseline_cell_count": baseline_cell_count,
        "refined_parent_count": len(refined_parents),
        "split_request_count": len(split_requests),
        "signals": {
            name: {
                "available": name in signals,
                "path": signals[name].path if name in signals else None,
                "license_lineage": list(signals[name].license_lineage) if name in signals else [],
            }
            for name in ("population", "settlement", "terrain", "historical")
        },
        "missing_optional_signals": list(missing_signals),
        "weight_renormalization": "available-inputs-only",
        "source_lineage": source_paths,
        "license_lineage": common_lineage,
        "inputs": input_records,
        "files": [
            locations_output.name, adjacency_output.name, intersections_output.name,
            lineage_output.name, pieces_output.name,
        ],
        "counts": {
            "locations": len(features),
            "adjacency_rows": len(adjacency_rows),
            "admin_intersections": len(intersections),
            "admin_pieces": len(admin_pieces),
            "lineage_events": len(lineage_events),
        },
    }
    _write_json(locations_output, collection)
    _write_csv(adjacency_output, adjacency_rows, (
        "from_location_id", "to_location_id", "shared_border_km", "adjacency_type",
    ))
    _write_csv(intersections_output, intersections, (
        "location_id", "reference_layer", "reference_id", "intersection_area_sq_km", "location_share",
    ))
    _write_json(lineage_output, lineage)
    _write_json(pieces_output, {
        "type": "FeatureCollection",
        "gpm": {"layer_kind": "location_admin_pieces", "fabric_id": fabric_id},
        "features": admin_pieces,
    })
    _write_json(manifest_output, manifest)
    return LocationBuildResult(
        fabric_id=fabric_id,
        fabric_revision=output_revision,
        target_location_count=target,
        location_count=len(features),
        baseline_cell_count=baseline_cell_count,
        refined_parent_count=len(refined_parents),
        split_request_count=len(split_requests),
        locations_output=str(locations_output),
        adjacency_output=str(adjacency_output),
        intersections_output=str(intersections_output),
        lineage_output=str(lineage_output),
        manifest_output=str(manifest_output),
        missing_signals=missing_signals,
    )


def _load_reference_features(*, raw_dir: Path, land_input: Path | None, admin0_input: Path | None,
                             admin1_input: Path | None, land_licenses: tuple[str, ...],
                             admin0_licenses: tuple[str, ...], admin1_licenses: tuple[str, ...]
                             ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    if land_input is not None:
        land_features, land_meta = _read_geojson_features(land_input)
        land_notices = _input_licenses("land", land_input, land_meta, land_licenses)
        records = [_input_record("land", land_input, land_notices)]
        if admin0_input:
            admin0_features, admin0_meta = _read_geojson_features(admin0_input)
            admin0_notices = _input_licenses("admin0", admin0_input, admin0_meta, admin0_licenses)
            records.append(_input_record("admin0", admin0_input, admin0_notices))
        else:
            admin0_features = land_features
        if admin1_input:
            admin1_features, admin1_meta = _read_geojson_features(admin1_input)
            admin1_notices = _input_licenses("admin1", admin1_input, admin1_meta, admin1_licenses)
            records.append(_input_record("admin1", admin1_input, admin1_notices))
        else:
            admin1_features = []
        return land_features, admin0_features, admin1_features, records
    artifacts = _natural_earth_artifact_paths("modern-small", Path(raw_dir))
    land_path = Path(raw_dir) / "natural_earth" / "ne_10m_land.zip"
    missing = [path for path in [*artifacts.values(), land_path] if not path.is_file()]
    if missing:
        raise LocationBuildError(
            "Location generation requires Natural Earth admin boundary zips or --land-input. "
            f"Missing: {', '.join(str(path) for path in missing)}"
        )
    admin0 = [
        {"type": "Feature", "geometry": item.geometry, "properties": item.properties}
        for item in read_zipped_shapefile(artifacts["admin0_countries"])
    ]
    admin1 = [
        {"type": "Feature", "geometry": item.geometry, "properties": item.properties}
        for item in read_zipped_shapefile(artifacts["admin1_states_provinces"])
    ]
    land = [
        {"type": "Feature", "geometry": item.geometry, "properties": item.properties}
        for item in read_zipped_shapefile(land_path)
    ]
    return land, admin0, admin1, [
        _input_record("land", land_path, ("Natural Earth public domain",), format="natural-earth-zip"),
        _input_record("admin0", artifacts["admin0_countries"], ("Natural Earth public domain",), format="natural-earth-zip"),
        _input_record("admin1", artifacts["admin1_states_provinces"], ("Natural Earth public domain",), format="natural-earth-zip"),
    ]


def _embedded_licenses(document: dict[str, Any]) -> tuple[str, ...]:
    value = document.get("license_lineage")
    if value is None and isinstance(document.get("gpm"), dict):
        value = document["gpm"].get("license_lineage")
    if isinstance(value, str):
        value = [value]
    return tuple(item.strip() for item in (value or []) if isinstance(item, str) and item.strip())


def _input_licenses(role: str, path: Path, document: dict[str, Any], explicit: tuple[str, ...]) -> tuple[str, ...]:
    notices = tuple(dict.fromkeys([
        *(item.strip() for item in explicit if isinstance(item, str) and item.strip()),
        *_embedded_licenses(document),
    ]))
    if not notices:
        raise LocationBuildError(
            f"Custom {role} input requires embedded license_lineage or --{role}-license: {path}"
        )
    return notices


def _input_record(role: str, path: Path, licenses: tuple[str, ...], *, format: str = "geojson") -> dict[str, Any]:
    return {"role": role, "path": str(Path(path)), "format": format, "license_lineage": list(licenses)}


def _read_geojson_features(path: Path | None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if path is None:
        return [], {}
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LocationBuildError(f"Cannot read GeoJSON {path}: {exc}") from exc
    if document.get("type") == "FeatureCollection":
        features = document.get("features")
        if not isinstance(features, list):
            raise LocationBuildError(f"GeoJSON FeatureCollection has no features array: {path}")
        return [item for item in features if isinstance(item, dict)], document
    if document.get("type") == "Feature":
        return [document], {}
    raise LocationBuildError(f"Expected a GeoJSON Feature or FeatureCollection: {path}")


def _polygonal_union(geometries: Iterable[dict[str, Any]]) -> Any:
    polygons: list[Any] = []
    for raw in geometries:
        try:
            geom = make_valid(shape(raw))
        except Exception as exc:
            raise LocationBuildError(f"Invalid polygon input: {exc}") from exc
        polygons.extend(_polygon_parts(geom))
    return unary_union(polygons) if polygons else GeometryCollection()


def _polygon_parts(geom: Any) -> list[Polygon]:
    if geom.is_empty:
        return []
    if geom.geom_type == "Polygon":
        return [geom]
    if geom.geom_type in {"MultiPolygon", "GeometryCollection"}:
        return [part for child in geom.geoms for part in _polygon_parts(child)]
    return []


def _all_cells_at_resolution(resolution: int) -> list[str]:
    cells: list[str] = []
    for root in sorted(h3.get_res0_cells()):
        cells.extend(sorted(h3.cell_to_children(root, resolution)))
    return sorted(cells)


def _cell_polygon(cell: str) -> Polygon:
    ring = [(longitude, latitude) for latitude, longitude in h3.cell_to_boundary(cell)]
    if max(x for x, _y in ring) - min(x for x, _y in ring) > 180:
        ring = [(x + 360 if x < 0 else x, y) for x, y in ring]
    return Polygon(ring)


def _land_index(land: Any) -> _LandIndex:
    originals = _polygon_parts(land)
    # H3 dateline rings are unwrapped into 179..181 degrees. Only western
    # dateline components need a translated copy for those cells.
    wrapped = [translate(part, xoff=360) for part in originals if part.bounds[0] < -160]
    geometries = tuple([*originals, *wrapped])
    return _LandIndex(geometries, STRtree(geometries))


def _clip_cell(cell: str, land: Any) -> list[Any]:
    cell_polygon = _cell_polygon(cell)
    index = land if isinstance(land, _LandIndex) else _land_index(land)
    candidate_indexes = index.tree.query(cell_polygon, predicate="intersects")
    if len(candidate_indexes) == 0:
        return []
    intersections = [
        cell_polygon.intersection(index.geometries[int(candidate_index)])
        for candidate_index in candidate_indexes
    ]
    clipped = make_valid(unary_union(intersections))
    parts = []
    for part in _polygon_parts(clipped):
        if part.area <= 1e-12:
            continue
        if part.centroid.x > 180:
            part = translate(part, xoff=-360)
        elif part.centroid.x < -180:
            part = translate(part, xoff=360)
        parts.append(normalize(part))
    return sorted(parts, key=_geometry_digest)


def _refine_partition(parent: str, parent_parts: list[Any]) -> dict[str, list[Any]]:
    """Partition the exact planar parent footprint among its H3 children.

    H3 edges are geodesic. GeoJSON renders them as straight chords, so a raw
    mixed-resolution child may otherwise overlap a neighboring coarse parent.
    Clipping to the existing parent and assigning tiny chord residuals keeps
    every refinement a true, gap-free planar partition.
    """
    parent_geom = unary_union(parent_parts)
    children = sorted(h3.cell_to_children(parent, h3.get_resolution(parent) + 1))
    allocated: Any = GeometryCollection()
    child_geometries: dict[str, Any] = {}
    for child in children:
        polygon = _cell_polygon(child)
        if parent_geom.centroid.x < -90 and polygon.centroid.x > 90:
            polygon = translate(polygon, xoff=-360)
        elif parent_geom.centroid.x > 90 and polygon.centroid.x < -90:
            polygon = translate(polygon, xoff=360)
        geom = make_valid(parent_geom.intersection(polygon).difference(allocated))
        polygonal = unary_union(_polygon_parts(geom))
        child_geometries[child] = polygonal
        if not polygonal.is_empty:
            allocated = unary_union([allocated, polygonal])
    residual = make_valid(parent_geom.difference(allocated))
    for part in _polygon_parts(residual):
        candidates = [child for child in children if not child_geometries[child].is_empty]
        if not candidates:
            candidates = children
        chosen = min(
            candidates,
            key=lambda child: (
                -part.boundary.intersection(child_geometries[child].boundary).length,
                part.distance(child_geometries[child]),
                child,
            ),
        )
        child_geometries[chosen] = unary_union([child_geometries[chosen], part])
    return {
        child: sorted((normalize(part) for part in _polygon_parts(make_valid(geom))), key=_geometry_digest)
        for child, geom in child_geometries.items()
        if not geom.is_empty
    }


def _geometry_digest(geom: Any) -> str:
    return hashlib.sha256(to_wkb(normalize(geom), byte_order=1)).hexdigest()[:16]


def _location_id(cell: str, geom: Any) -> str:
    return f"loc_{cell}_{_geometry_digest(geom)[:10]}"


def _load_signal(name: str, path: Path, explicit_licenses: tuple[str, ...]) -> _Signal:
    features, document = _read_geojson_features(path)
    licenses = tuple(dict.fromkeys([*explicit_licenses, *_embedded_licenses(document)]))
    if not licenses:
        raise LocationBuildError(
            f"Optional {name} dataset requires embedded license_lineage or --{name.replace('_', '-')}-license."
        )
    geometries: list[Any] = []
    values: list[float] = []
    value_keys = (name, "value", "weight", "population", "count")
    for feature in features:
        if not feature.get("geometry"):
            continue
        geom = shape(feature["geometry"])
        props = feature.get("properties") or {}
        value = next((props[key] for key in value_keys if isinstance(props.get(key), (int, float)) and not isinstance(props.get(key), bool)), 1.0)
        if math.isfinite(float(value)) and float(value) >= 0:
            geometries.append(geom)
            values.append(float(value))
    if not geometries:
        raise LocationBuildError(f"Optional {name} dataset contains no usable features: {path}")
    return _Signal(name, str(Path(path)), tuple(geometries), tuple(values), STRtree(geometries), licenses)


def _signal_value(signal: _Signal, geom: Any) -> float:
    total = 0.0
    for index in signal.tree.query(geom, predicate="intersects"):
        sample = signal.geometries[int(index)]
        value = signal.values[int(index)]
        if sample.geom_type == "Point":
            total += value if geom.covers(sample) else 0.0
        elif sample.area > 0:
            total += value * (geom.intersection(sample).area / sample.area)
        else:
            total += value
    return total


def _cell_score(parts: list[Any], signals: dict[str, _Signal], weights: dict[str, Any]) -> float:
    geom = unary_union(parts)
    components = [("area", max(geom.area, 0.0))]
    components.extend((name, _signal_value(signal, geom)) for name, signal in signals.items())
    available_weights = {name: max(float(weights.get(name, 1.0)), 0.0) for name, _value in components}
    total_weight = sum(available_weights.values()) or 1.0
    return sum(available_weights[name] * math.log1p(value) for name, value in components) / total_weight


def _location_features(cells: dict[str, list[Any]], config: dict[str, Any], signals: dict[str, _Signal],
                       reference_inputs: list[dict[str, Any]], output_revision: str,
                       source_revision: str) -> list[dict[str, Any]]:
    features: list[dict[str, Any]] = []
    for cell in sorted(cells):
        parts = cells[cell]
        for component_index, geom in enumerate(parts, start=1):
            props: dict[str, Any] = {
                "location_id": _location_id(cell, geom),
                "h3_index": cell,
                "h3_resolution": h3.get_resolution(cell),
                "component_index": component_index,
                "component_count": len(parts),
                "fabric_id": config["fabric_id"],
                "fabric_revision": output_revision,
                "source_fabric_revision": source_revision,
                "geometry_revision": str(config["geometry_revision"]),
                "area_sq_km": round(geometry_area_sq_km(mapping(geom)), 6),
                "source_lineage": sorted({
                    *(record["path"] for record in reference_inputs),
                    *(signal.path for signal in signals.values()),
                    f"H3 {h3.__version__}",
                }),
                "license_lineage": sorted({
                    *(notice for record in reference_inputs for notice in record["license_lineage"]),
                    *(notice for signal in signals.values() for notice in signal.license_lineage),
                    "H3 Apache-2.0",
                }),
            }
            for name, signal in signals.items():
                props[f"{name}_signal"] = round(_signal_value(signal, geom), 6)
            features.append({"type": "Feature", "geometry": mapping(geom), "properties": props})
    return features


def _remove_planar_overlaps(features: list[dict[str, Any]], *, tolerance: float = 1e-10) -> list[dict[str, Any]]:
    """Resolve rare polar chord overlaps while preserving the fabric union.

    Longitude/latitude GeoJSON draws H3 geodesics as straight segments. Near a
    pole those chords can overlap even after hierarchical clipping. Earlier
    stable IDs win the shared sliver; subtracting it from later cells keeps the
    same land union and produces a valid planar paint surface.
    """
    ordered = sorted(features, key=lambda feature: feature["properties"]["location_id"])
    geometries = [shape(feature["geometry"]) for feature in ordered]
    tree = STRtree(geometries)
    cutters: dict[int, list[Any]] = {}
    for left_index, left in enumerate(geometries):
        for raw_right in tree.query(left, predicate="intersects"):
            right_index = int(raw_right)
            if right_index <= left_index:
                continue
            if left.intersection(geometries[right_index]).area > tolerance:
                cutters.setdefault(right_index, []).append(left)
    if not cutters:
        return ordered
    result: list[dict[str, Any]] = []
    for index, feature in enumerate(ordered):
        geom = geometries[index]
        if index in cutters:
            geom = make_valid(geom.difference(unary_union(cutters[index])))
        parts = _polygon_parts(geom)
        if not parts:
            continue
        geometry = normalize(parts[0] if len(parts) == 1 else MultiPolygon(parts))
        item = {"type": "Feature", "geometry": mapping(geometry), "properties": dict(feature["properties"])}
        cell = item["properties"]["h3_index"]
        item["properties"]["location_id"] = _location_id(cell, geometry)
        item["properties"]["area_sq_km"] = round(geometry_area_sq_km(mapping(geometry)), 6)
        if index in cutters:
            item["properties"]["planar_overlap_resolved"] = True
        result.append(item)
    return result


def _fill_planar_land_gaps(features: list[dict[str, Any]], land: Any,
                           *, tolerance: float = 1e-10) -> list[dict[str, Any]]:
    """Assign planar closure residuals, chiefly the south-pole cap, deterministically.

    H3 covers the sphere, but a longitude/latitude polygon cannot directly encode
    the point where every longitude meets at a pole. The chord rendering therefore
    leaves a narrow cap below the southernmost cell edges. Attach each residual
    land component to the location sharing the longest edge (stable ID breaks ties)
    so the published GeoJSON is a closed planar partition of the declared land.
    """
    if not features:
        return features
    geometries = [shape(feature["geometry"]) for feature in features]
    residual = make_valid(land.difference(unary_union(geometries)))
    gaps = [part for part in _polygon_parts(residual) if part.area > tolerance]
    if not gaps:
        return features
    updated = list(features)
    for gap in sorted(gaps, key=_geometry_digest):
        chosen = min(
            range(len(geometries)),
            key=lambda index: (
                -gap.boundary.intersection(geometries[index].boundary).length,
                gap.distance(geometries[index]),
                updated[index]["properties"]["location_id"],
            ),
        )
        geometry = normalize(make_valid(unary_union([geometries[chosen], gap])))
        props = dict(updated[chosen]["properties"])
        props["location_id"] = _location_id(props["h3_index"], geometry)
        props["area_sq_km"] = round(geometry_area_sq_km(mapping(geometry)), 6)
        props["planar_land_gap_resolved"] = True
        updated[chosen] = {"type": "Feature", "geometry": mapping(geometry), "properties": props}
        geometries[chosen] = geometry
    return updated


def build_location_adjacency_rows(features: list[dict[str, Any]], *, minimum_border_km: float = 0.001) -> list[dict[str, Any]]:
    geometries = [shape(feature["geometry"]) for feature in features]
    tree = STRtree(geometries)
    rows: list[dict[str, Any]] = []
    for left_index, left in enumerate(geometries):
        for right_raw in tree.query(left, predicate="intersects"):
            right_index = int(right_raw)
            if right_index <= left_index:
                continue
            shared = left.boundary.intersection(geometries[right_index].boundary)
            if shared.is_empty or shared.length <= 1e-12:
                continue
            # Existing project metrics use an intentionally simple WGS84 approximation.
            midpoint_lat = left.union(geometries[right_index]).centroid.y
            km = shared.length * 111.195 * max(0.25, math.cos(math.radians(midpoint_lat)))
            if km < minimum_border_km:
                continue
            left_id = features[left_index]["properties"]["location_id"]
            right_id = features[right_index]["properties"]["location_id"]
            from_id, to_id = sorted((left_id, right_id))
            rows.append({
                "from_location_id": from_id,
                "to_location_id": to_id,
                "shared_border_km": f"{km:.6f}",
                "adjacency_type": "land",
            })
    return sorted(rows, key=lambda row: (row["from_location_id"], row["to_location_id"]))


def _reference_id(feature: dict[str, Any], layer: str, index: int) -> str:
    props = feature.get("properties") or {}
    keys = ("reference_id", "admin_id", "adm1_code", "iso_3166_2", "iso_a3", "adm0_a3", "sov_a3", "name")
    value = next((props.get(key) for key in keys if props.get(key) not in (None, "", "-99")), None)
    return str(value) if value is not None else f"{layer}_{index:05d}"


def build_admin_intersections(features: list[dict[str, Any]], *, admin0_features: list[dict[str, Any]],
                              admin1_features: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    pieces: list[dict[str, Any]] = []
    for layer, references in (("admin0", admin0_features), ("admin1", admin1_features)):
        ref_items = []
        for index, feature in enumerate(references, start=1):
            try:
                geom = make_valid(shape(feature["geometry"]))
            except Exception:
                continue
            if not geom.is_empty:
                ref_items.append((geom, _reference_id(feature, layer, index)))
        if not ref_items:
            continue
        ref_geoms = [item[0] for item in ref_items]
        tree = STRtree(ref_geoms)
        for feature in features:
            location_geom = shape(feature["geometry"])
            location_id = feature["properties"]["location_id"]
            location_planar_area = max(location_geom.area, 1e-15)
            allocated: Any = GeometryCollection()
            candidates = sorted(
                (int(raw_index) for raw_index in tree.query(location_geom, predicate="intersects")),
                key=lambda reference_index: (ref_items[reference_index][1], reference_index),
            )
            for reference_index in candidates:
                # Reference polygons can contain tiny disputed/rounding overlaps.
                # Materialize a deterministic non-overlapping partition so hard
                # aggregation pieces remain a valid paint surface.
                intersection = make_valid(
                    location_geom.intersection(ref_geoms[reference_index]).difference(allocated)
                )
                for part_index, part in enumerate(_polygon_parts(intersection), start=1):
                    area = geometry_area_sq_km(mapping(part))
                    if area <= 1e-9:
                        continue
                    reference_id = ref_items[reference_index][1]
                    rows.append({
                        "location_id": location_id,
                        "reference_layer": layer,
                        "reference_id": reference_id,
                        "intersection_area_sq_km": f"{area:.6f}",
                        "location_share": f"{min(part.area / location_planar_area, 1.0):.12f}",
                    })
                    piece_id = hashlib.sha256(f"{location_id}|{layer}|{reference_id}|{part_index}|{_geometry_digest(part)}".encode()).hexdigest()[:16]
                    pieces.append({
                        "type": "Feature",
                        "geometry": mapping(normalize(part)),
                        "properties": {
                            "piece_id": f"piece_{piece_id}",
                            "location_id": location_id,
                            "reference_layer": layer,
                            "reference_id": reference_id,
                            "area_sq_km": round(area, 6),
                        },
                    })
                if not intersection.is_empty:
                    allocated = unary_union([allocated, intersection])
    rows.sort(key=lambda row: (row["location_id"], row["reference_layer"], row["reference_id"]))
    pieces.sort(key=lambda item: item["properties"]["piece_id"])
    return rows, pieces


def _load_split_requests(path: Path | None, config: dict[str, Any]) -> list[dict[str, Any]]:
    if path is None:
        return []
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LocationBuildError(f"Cannot read split requests {path}: {exc}") from exc
    requests = document.get("requests") if isinstance(document, dict) else document
    if not isinstance(requests, list):
        raise LocationBuildError("Split request input must be an array or an object with requests.")
    required = {"request_id", "operation", "failed_paintability_test", "proposed_geometry", "sources", "license_lineage", "confidence", "affected_dates", "target_fabric_revision"}
    for index, request in enumerate(requests):
        if not isinstance(request, dict) or required - request.keys():
            missing = sorted(required - request.keys()) if isinstance(request, dict) else sorted(required)
            raise LocationBuildError(f"Split request {index} is missing: {', '.join(missing)}")
        if request["operation"] not in {"refine_h3", "split_by_boundary"}:
            raise LocationBuildError(f"Split request {request['request_id']} has unsupported operation.")
        if str(request["target_fabric_revision"]) != str(config["fabric_revision"]):
            raise LocationBuildError(f"Split request {request['request_id']} targets a different fabric revision.")
        if not request["sources"] or not request["license_lineage"]:
            raise LocationBuildError(f"Split request {request['request_id']} requires source and license lineage.")
    return sorted(requests, key=lambda row: str(row["request_id"]))


def _apply_split_requests(features: list[dict[str, Any]], requests: list[dict[str, Any]], land: Any,
                          config: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    current = list(features)
    events: list[dict[str, Any]] = []
    geometry_cache: dict[str, Any] = {}

    def _cached_geometry(feature: dict[str, Any]) -> Any:
        location_id = feature["properties"]["location_id"]
        geometry = geometry_cache.get(location_id)
        if geometry is None:
            geometry = shape(feature["geometry"])
            geometry_cache[location_id] = geometry
        return geometry

    from shapely.strtree import STRtree

    for request in requests:
        proposed = shape(request["proposed_geometry"])
        tree = STRtree([_cached_geometry(feature) for feature in current])
        affected = [
            current[index]
            for index in sorted(int(raw) for raw in tree.query(proposed, predicate="intersects"))
        ]
        if not affected:
            raise LocationBuildError(f"Split request {request['request_id']} affects no locations.")
        children: list[dict[str, Any]] = []
        parent_ids: list[str] = []
        for parent in affected:
            if request["operation"] == "refine_h3":
                cell = parent["properties"]["h3_index"]
                if h3.get_resolution(cell) >= int(config["maximum_h3_resolution"]):
                    continue
                refined = _refine_partition(cell, [shape(parent["geometry"])])
                child_geometries = [part for child in refined for part in refined[child]]
                child_cells = [child for child in refined for _part in refined[child]]
            else:
                cutter = proposed.boundary if proposed.geom_type in {"Polygon", "MultiPolygon"} else proposed
                try:
                    child_geometries = _polygon_parts(split(shape(parent["geometry"]), cutter))
                except Exception as exc:
                    raise LocationBuildError(f"Cannot apply boundary split {request['request_id']}: {exc}") from exc
                child_cells = [parent["properties"]["h3_index"]] * len(child_geometries)
            if len(child_geometries) < 2:
                continue
            parent_ids.append(parent["properties"]["location_id"])
            current.remove(parent)
            for index, (geom, cell) in enumerate(zip(child_geometries, child_cells, strict=True), start=1):
                props = dict(parent["properties"])
                props.update({
                    "location_id": _location_id(cell, geom),
                    "h3_index": cell,
                    "h3_resolution": h3.get_resolution(cell),
                    "component_index": index,
                    "component_count": len(child_geometries),
                    "area_sq_km": round(geometry_area_sq_km(mapping(geom)), 6),
                    "lineage_parent_id": parent["properties"]["location_id"],
                    "split_request_id": request["request_id"],
                })
                children.append({"type": "Feature", "geometry": mapping(normalize(geom)), "properties": props})
        if not parent_ids:
            if request["operation"] == "refine_h3":
                # The grid is exhausted for this geometry: every affected
                # location is already at maximum resolution or occupies a
                # single H3 child. Refinement is a benign no-op, not an error.
                continue
            raise LocationBuildError(
                f"Split request {request['request_id']} intersects locations but splits none."
            )
        current.extend(children)
        events.append({
            "operation": request["operation"],
            "request_id": request["request_id"],
            "parent_location_ids": sorted(parent_ids),
            "child_location_ids": sorted(child["properties"]["location_id"] for child in children),
            "affected_dates": request["affected_dates"],
            "confidence": request["confidence"],
            "sources": request["sources"],
            "license_lineage": request["license_lineage"],
        })
    return current, events


def _write_json(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
