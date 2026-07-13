"""Build PMTiles archives from GeoJSON / atlas packs (M19)."""

from __future__ import annotations

import gzip
import json
import math
import shutil
import subprocess
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Sequence

from shapely import make_valid
from shapely.geometry import MultiPolygon, box, shape
from shapely.geometry.base import BaseGeometry
from shapely.strtree import STRtree

from gpm import __version__
from gpm.paths import EXPORT_DIR

from .mvt import DEFAULT_EXTENT, encode_tile
from .pmtiles_io import (
    Compression,
    PmtilesWriter,
    TileType,
    read_pmtiles_header,
    zxy_to_tileid,
)

TILES_SCHEMA_VERSION = "0.1.0"
DEFAULT_MIN_ZOOM = 0
DEFAULT_MAX_ZOOM = 8
DEFAULT_LAYER_NAME = "provinces"

# Native-backend per-zoom generalization: simplify to ~1 tile pixel and drop
# polygons whose bounding box spans fewer than ~2 tile pixels in both axes.
NATIVE_SIMPLIFY_PIXELS = 1.0
NATIVE_DROP_FEATURE_PIXELS = 2.0
# Clip buffer around each tile, as a fraction of the tile extent. Clipping
# exactly at tile bounds puts polygon edges on the seam and outline layers
# then draw a visible tile grid; buffered clips push those edges off-tile
# (coordinates outside 0..extent are valid MVT geometry).
NATIVE_CLIP_BUFFER_FRACTION = 64 / DEFAULT_EXTENT

# Properties useful for MapLibre paint/inspect; keeps tile size bounded.
DEFAULT_PROPERTY_KEYS = frozenset(
    {
        "province_id",
        "display_name",
        "kind",
        "owner",
        "controller",
        "owner_color",
        "controller_color",
        "culture",
        "religion",
        "culture_color",
        "religion_color",
        "assignment_source",
        "disputed",
        "uncertain",
        "cores",  # lists are comma-joined by the MVT encoder (values are scalar)
        "claims",
        "parent_country_id",
        "parent_region_id",
        "parent_area_id",
        "parent_geo_region_id",
        "parent_superregion_id",
        "area_color",
        "scenario_id",
        "area_sq_km",
        "estimated_population",
        "coastal",
        "island",
        "terrain_class",
        "notes",
        "type",  # adjacency edge type, etc.
    }
)


class TileBuildError(ValueError):
    """Raised when PMTiles generation fails."""


@dataclass(frozen=True)
class TileBuildResult:
    output_path: str
    layer_name: str
    feature_count: int
    tile_count: int
    min_zoom: int
    max_zoom: int
    bounds: tuple[float, float, float, float]
    backend: str
    tileset_manifest: str | None
    files_written: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["bounds"] = list(self.bounds)
        data["files_written"] = list(self.files_written)
        return data


def tile_bounds(z: int, x: int, y: int) -> tuple[float, float, float, float]:
    """Return (west, south, east, north) in WGS84 for a Web Mercator tile."""
    n = 2.0**z
    west = x / n * 360.0 - 180.0
    east = (x + 1) / n * 360.0 - 180.0
    north = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    south = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n))))
    return west, south, east, north


def lonlat_to_tile(lon: float, lat: float, z: int) -> tuple[int, int]:
    lat = max(min(lat, 85.05112878), -85.05112878)
    n = 2.0**z
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n)
    x = max(0, min(int(n) - 1, x))
    y = max(0, min(int(n) - 1, y))
    return x, y


def _feature_bounds(geom: BaseGeometry) -> tuple[float, float, float, float]:
    minx, miny, maxx, maxy = geom.bounds
    return float(minx), float(miny), float(maxx), float(maxy)


def _union_bounds(
    bounds_list: Sequence[tuple[float, float, float, float]],
) -> tuple[float, float, float, float]:
    if not bounds_list:
        return (-180.0, -85.0, 180.0, 85.0)
    west = min(b[0] for b in bounds_list)
    south = min(b[1] for b in bounds_list)
    east = max(b[2] for b in bounds_list)
    north = max(b[3] for b in bounds_list)
    return west, south, east, north


def _prefer_areal_geometry(
    geom: BaseGeometry, *, source_type: str
) -> BaseGeometry | None:
    """Keep polygons when clipping polygons; otherwise preserve source dimension."""
    if geom.is_empty:
        return None
    if source_type in {"Polygon", "MultiPolygon"}:
        polys: list[BaseGeometry] = []
        if geom.geom_type == "Polygon":
            polys = [geom]
        elif geom.geom_type == "MultiPolygon":
            polys = list(geom.geoms)
        elif geom.geom_type == "GeometryCollection":
            for part in geom.geoms:
                if part.geom_type == "Polygon":
                    polys.append(part)
                elif part.geom_type == "MultiPolygon":
                    polys.extend(list(part.geoms))
        else:
            return None
        polys = [p for p in polys if not p.is_empty]
        if not polys:
            return None
        if len(polys) == 1:
            return polys[0]
        return MultiPolygon(polys)
    return geom


def _load_geojson_features(path: Path) -> list[dict[str, Any]]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("type") == "FeatureCollection":
        features = document.get("features") or []
    elif document.get("type") == "Feature":
        features = [document]
    else:
        raise TileBuildError(f"{path} is not a GeoJSON Feature or FeatureCollection")
    prepared: list[dict[str, Any]] = []
    for feature in features:
        if not isinstance(feature, dict):
            continue
        geom_doc = feature.get("geometry")
        if not geom_doc:
            continue
        try:
            geom = shape(geom_doc)
        except Exception as exc:  # noqa: BLE001 — surface bad geometry
            raise TileBuildError(f"invalid geometry in {path}: {exc}") from exc
        if geom.is_empty:
            continue
        prepared.append(
            {
                "geometry": geom,
                "properties": dict(feature.get("properties") or {}),
                "id": feature.get("id"),
            }
        )
    return prepared


def _tiles_covering_bounds(
    bounds: tuple[float, float, float, float], z: int
) -> Iterable[tuple[int, int, int]]:
    west, south, east, north = bounds
    # Clamp to Web Mercator latitude range.
    south = max(south, -85.05112878)
    north = min(north, 85.05112878)
    if east < west or north < south:
        return []
    x_min, y_max = lonlat_to_tile(west, south, z)  # south → larger y
    x_max, y_min = lonlat_to_tile(east, north, z)  # north → smaller y
    if x_min > x_max:
        x_min, x_max = x_max, x_min
    if y_min > y_max:
        y_min, y_max = y_max, y_min
    n = 1 << z
    x_min = max(0, min(n - 1, x_min))
    x_max = max(0, min(n - 1, x_max))
    y_min = max(0, min(n - 1, y_min))
    y_max = max(0, min(n - 1, y_max))
    for x in range(x_min, x_max + 1):
        for y in range(y_min, y_max + 1):
            yield z, x, y


def _prepare_zoom_geometries(
    geoms: Sequence[BaseGeometry], z: int, *, extent: int = DEFAULT_EXTENT
) -> list[BaseGeometry | None]:
    """Per-zoom generalization for the native backend.

    Returns one entry per input geometry: a simplified geometry, or ``None``
    when the feature is too small to matter at this zoom. Simplification is
    quantization-aware (~1 tile pixel), so low zooms stay fast and small.
    """
    pixel_deg = 360.0 / ((1 << z) * extent)
    tolerance = pixel_deg * NATIVE_SIMPLIFY_PIXELS
    min_span = pixel_deg * NATIVE_DROP_FEATURE_PIXELS
    prepared: list[BaseGeometry | None] = []
    for geom in geoms:
        if geom.geom_type in {"Polygon", "MultiPolygon"}:
            minx, miny, maxx, maxy = geom.bounds
            if (maxx - minx) < min_span and (maxy - miny) < min_span:
                prepared.append(None)
                continue
        simplified = geom.simplify(tolerance, preserve_topology=False)
        if simplified.is_empty:
            prepared.append(None)
            continue
        if not simplified.is_valid:
            simplified = make_valid(simplified)
            if simplified.is_empty:
                prepared.append(None)
                continue
        prepared.append(simplified)
    return prepared


def _tippecanoe_available() -> bool:
    return shutil.which("tippecanoe") is not None


def _build_with_tippecanoe(
    geojson_path: Path,
    output_path: Path,
    *,
    layer_name: str,
    min_zoom: int,
    max_zoom: int,
) -> None:
    cmd = [
        "tippecanoe",
        "-o",
        str(output_path),
        "-l",
        layer_name,
        "-Z",
        str(min_zoom),
        "-z",
        str(max_zoom),
        "--projection=EPSG:4326",
        "--no-feature-limit",
        "--no-tile-size-limit",
        "--drop-densest-as-needed",
        "--extend-zooms-if-still-dropping",
        "--force",
        str(geojson_path),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or str(exc)).strip()
        raise TileBuildError(f"tippecanoe failed: {detail}") from exc


def build_pmtiles_from_features(
    features: Sequence[dict[str, Any]],
    output_path: Path | str,
    *,
    layer_name: str = DEFAULT_LAYER_NAME,
    min_zoom: int = DEFAULT_MIN_ZOOM,
    max_zoom: int = DEFAULT_MAX_ZOOM,
    property_keys: frozenset[str] | None = DEFAULT_PROPERTY_KEYS,
    name: str | None = None,
    description: str | None = None,
    attribution: str | None = None,
    write_manifest: bool = True,
    backend: str = "native",
) -> TileBuildResult:
    """Build a PMTiles archive from in-memory features.

    Each feature dict must include a shapely ``geometry`` and optional
    ``properties`` / ``id``.
    """
    if min_zoom < 0 or max_zoom < min_zoom or max_zoom > 22:
        raise TileBuildError("invalid zoom range: require 0 <= min_zoom <= max_zoom <= 22")
    if not features:
        raise TileBuildError("no features to tile")

    output_path = Path(output_path)
    geoms = [f["geometry"] for f in features]
    bounds_list = [_feature_bounds(g) for g in geoms]
    bounds = _union_bounds(bounds_list)

    writer = PmtilesWriter(output_path)
    tile_count = 0

    for z in range(min_zoom, max_zoom + 1):
        zoom_geoms = _prepare_zoom_geometries(geoms, z)
        kept_indices = [index for index, geom in enumerate(zoom_geoms) if geom is not None]
        if not kept_indices:
            continue
        tree = STRtree([zoom_geoms[index] for index in kept_indices])
        for z_, x, y in _tiles_covering_bounds(bounds, z):
            west, south, east, north = tile_bounds(z_, x, y)
            pad_x = (east - west) * NATIVE_CLIP_BUFFER_FRACTION
            pad_y = (north - south) * NATIVE_CLIP_BUFFER_FRACTION
            tile_poly = box(west - pad_x, south - pad_y, east + pad_x, north + pad_y)
            hits = tree.query(tile_poly)
            if len(hits) == 0:
                continue
            tile_features: list[dict[str, Any]] = []
            for idx in sorted(int(item) for item in hits):
                index = kept_indices[idx]
                feature = features[index]
                geom = zoom_geoms[index]
                try:
                    clipped = geom.intersection(tile_poly)
                except Exception:  # noqa: BLE001 — skip pathological clips
                    continue
                if clipped.is_empty:
                    continue
                clipped = _prefer_areal_geometry(clipped, source_type=geoms[index].geom_type)
                if clipped is None or clipped.is_empty:
                    continue
                tile_features.append(
                    {
                        "geometry": clipped,
                        "properties": feature.get("properties") or {},
                        "id": feature.get("id"),
                    }
                )
            if not tile_features:
                continue
            mvt = encode_tile(
                [(layer_name, tile_features)],
                west=west,
                south=south,
                east=east,
                north=north,
                extent=DEFAULT_EXTENT,
                property_keys=property_keys,
            )
            if not mvt:
                continue
            compressed = gzip.compress(mvt, mtime=0)
            writer.write_tile(zxy_to_tileid(z_, x, y), compressed)
            tile_count += 1

    if tile_count == 0:
        raise TileBuildError("no tiles produced (features may be empty or out of range)")

    metadata: dict[str, Any] = {
        "name": name or layer_name,
        "description": description
        or "Global Province Map Template vector tiles (M19 PMTiles)",
        "version": "0.1.0",
        "type": "overlay",
        "generator": f"gpm {__version__}",
        "generator_backend": backend,
        "vector_layers": [
            {
                "id": layer_name,
                "description": layer_name,
                "minzoom": min_zoom,
                "maxzoom": max_zoom,
                "fields": {
                    key: "String"
                    for key in sorted(property_keys or DEFAULT_PROPERTY_KEYS)
                },
            }
        ],
    }
    if attribution:
        metadata["attribution"] = attribution

    writer.finalize(
        metadata=metadata,
        min_zoom=min_zoom,
        max_zoom=max_zoom,
        bounds=bounds,
        center_zoom=min(max_zoom, max(min_zoom, 4)),
        tile_compression=Compression.GZIP,
        tile_type=TileType.MVT,
    )

    files_written = [output_path.name]
    manifest_path: Path | None = None
    if write_manifest:
        manifest_path = output_path.with_suffix(".tileset.json")
        header = read_pmtiles_header(output_path)
        manifest = {
            "schema_version": TILES_SCHEMA_VERSION,
            "milestone": "M19",
            "pack_type": "tileset",
            "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace(
                "+00:00", "Z"
            ),
            "generator_version": __version__,
            "backend": backend,
            "layer_name": layer_name,
            "pmtiles": output_path.name,
            "feature_count": len(features),
            "tile_count": tile_count,
            "min_zoom": min_zoom,
            "max_zoom": max_zoom,
            "bounds": {
                "west": bounds[0],
                "south": bounds[1],
                "east": bounds[2],
                "north": bounds[3],
            },
            "header": {
                "addressed_tiles_count": header["addressed_tiles_count"],
                "tile_entries_count": header["tile_entries_count"],
                "tile_contents_count": header["tile_contents_count"],
                "tile_type": "mvt",
                "tile_compression": "gzip",
            },
            "maplibre": {
                "source": {
                    "type": "vector",
                    "url": f"pmtiles://{output_path.name}",
                },
                "fill_layer": {
                    "id": f"{layer_name}-fill",
                    "type": "fill",
                    "source": layer_name,
                    "source-layer": layer_name,
                    "paint": {
                        "fill-color": [
                            "coalesce",
                            ["get", "owner_color"],
                            "#b0b0b0",
                        ],
                        "fill-opacity": 0.78,
                    },
                },
            },
            "notes": [
                "PMTiles v3 archive of Mapbox Vector Tiles (MVT).",
                "Serve with HTTP range requests or open locally via the pmtiles protocol.",
                "Native backend simplifies per zoom (~1 tile px) and drops sub-pixel features.",
                "tippecanoe is the recommended backend for global sets above zoom 7.",
            ],
        }
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        files_written.append(manifest_path.name)

    return TileBuildResult(
        output_path=str(output_path),
        layer_name=layer_name,
        feature_count=len(features),
        tile_count=tile_count,
        min_zoom=min_zoom,
        max_zoom=max_zoom,
        bounds=bounds,
        backend=backend,
        tileset_manifest=str(manifest_path) if manifest_path else None,
        files_written=tuple(files_written),
    )


def build_pmtiles_from_geojson(
    geojson_path: Path | str,
    output_path: Path | str | None = None,
    *,
    layer_name: str = DEFAULT_LAYER_NAME,
    min_zoom: int = DEFAULT_MIN_ZOOM,
    max_zoom: int = DEFAULT_MAX_ZOOM,
    prefer_tippecanoe: bool = True,
    property_keys: frozenset[str] | None = DEFAULT_PROPERTY_KEYS,
    name: str | None = None,
    description: str | None = None,
    attribution: str | None = None,
    write_manifest: bool = True,
) -> TileBuildResult:
    """Build PMTiles from a GeoJSON file.

    Uses tippecanoe when available and ``prefer_tippecanoe`` is true; otherwise
    uses the pure-Python native backend.
    """
    geojson_path = Path(geojson_path)
    if not geojson_path.is_file():
        raise TileBuildError(f"GeoJSON input not found: {geojson_path}")

    if output_path is None:
        output_path = geojson_path.with_suffix(".pmtiles")
    else:
        output_path = Path(output_path)

    if prefer_tippecanoe and _tippecanoe_available():
        _build_with_tippecanoe(
            geojson_path,
            output_path,
            layer_name=layer_name,
            min_zoom=min_zoom,
            max_zoom=max_zoom,
        )
        features = _load_geojson_features(geojson_path)
        bounds = _union_bounds([_feature_bounds(f["geometry"]) for f in features])
        header = read_pmtiles_header(output_path)
        files_written = [output_path.name]
        manifest_path = None
        if write_manifest:
            manifest_path = output_path.with_suffix(".tileset.json")
            manifest = {
                "schema_version": TILES_SCHEMA_VERSION,
                "milestone": "M19",
                "pack_type": "tileset",
                "generated_at": datetime.now(UTC)
                .replace(microsecond=0)
                .isoformat()
                .replace("+00:00", "Z"),
                "generator_version": __version__,
                "backend": "tippecanoe",
                "layer_name": layer_name,
                "pmtiles": output_path.name,
                "feature_count": len(features),
                "tile_count": header["addressed_tiles_count"],
                "min_zoom": header["min_zoom"],
                "max_zoom": header["max_zoom"],
                "bounds": {
                    "west": bounds[0],
                    "south": bounds[1],
                    "east": bounds[2],
                    "north": bounds[3],
                },
                "header": {
                    "addressed_tiles_count": header["addressed_tiles_count"],
                    "tile_entries_count": header["tile_entries_count"],
                    "tile_contents_count": header["tile_contents_count"],
                    "tile_type": "mvt",
                },
                "maplibre": {
                    "source": {
                        "type": "vector",
                        "url": f"pmtiles://{output_path.name}",
                    }
                },
                "notes": [
                    "Generated with tippecanoe (preferred quality backend).",
                ],
            }
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            files_written.append(manifest_path.name)
        return TileBuildResult(
            output_path=str(output_path),
            layer_name=layer_name,
            feature_count=len(features),
            tile_count=int(header["addressed_tiles_count"]),
            min_zoom=int(header["min_zoom"]),
            max_zoom=int(header["max_zoom"]),
            bounds=bounds,
            backend="tippecanoe",
            tileset_manifest=str(manifest_path) if manifest_path else None,
            files_written=tuple(files_written),
        )

    features = _load_geojson_features(geojson_path)
    return build_pmtiles_from_features(
        features,
        output_path,
        layer_name=layer_name,
        min_zoom=min_zoom,
        max_zoom=max_zoom,
        property_keys=property_keys,
        name=name,
        description=description,
        attribution=attribution,
        write_manifest=write_manifest,
        backend="native",
    )


def export_tiles_pack(
    *,
    input_geojson: Path | str,
    output_dir: Path | str | None = None,
    layer_name: str = DEFAULT_LAYER_NAME,
    min_zoom: int = DEFAULT_MIN_ZOOM,
    max_zoom: int = DEFAULT_MAX_ZOOM,
    prefer_tippecanoe: bool = True,
    name: str | None = None,
) -> TileBuildResult:
    """Export a tiles pack directory containing PMTiles + tileset manifest."""
    input_geojson = Path(input_geojson)
    if output_dir is None:
        output_dir = EXPORT_DIR / "tiles" / input_geojson.stem
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{layer_name}.pmtiles"
    return build_pmtiles_from_geojson(
        input_geojson,
        output_path,
        layer_name=layer_name,
        min_zoom=min_zoom,
        max_zoom=max_zoom,
        prefer_tippecanoe=prefer_tippecanoe,
        name=name,
        write_manifest=True,
    )


def export_tiles_from_atlas(
    atlas_dir: Path | str,
    *,
    scenarios: Sequence[str] | None = None,
    min_zoom: int = DEFAULT_MIN_ZOOM,
    max_zoom: int = DEFAULT_MAX_ZOOM,
    prefer_tippecanoe: bool = True,
    include_base: bool = True,
) -> list[TileBuildResult]:
    """Generate PMTiles for scenario choropleths (and optional base geometry)
    inside an existing atlas pack directory.
    """
    atlas_dir = Path(atlas_dir)
    if not atlas_dir.is_dir():
        raise TileBuildError(f"atlas directory not found: {atlas_dir}")

    results: list[TileBuildResult] = []
    scenarios_dir = atlas_dir / "scenarios"
    if scenarios_dir.is_dir():
        scenario_ids = (
            list(scenarios)
            if scenarios
            else sorted(p.name for p in scenarios_dir.iterdir() if p.is_dir())
        )
        for scenario_id in scenario_ids:
            choropleth = scenarios_dir / scenario_id / "ownership_choropleth.geojson"
            if not choropleth.is_file():
                continue
            out = scenarios_dir / scenario_id / "ownership.pmtiles"
            result = build_pmtiles_from_geojson(
                choropleth,
                out,
                layer_name="ownership",
                min_zoom=min_zoom,
                max_zoom=max_zoom,
                prefer_tippecanoe=prefer_tippecanoe,
                name=f"ownership-{scenario_id}",
                description=f"Ownership choropleth tiles for scenario {scenario_id}",
            )
            results.append(result)

    if include_base:
        base = atlas_dir / "geojson" / "provinces.geojson"
        if base.is_file():
            tiles_dir = atlas_dir / "tiles"
            tiles_dir.mkdir(parents=True, exist_ok=True)
            results.append(
                build_pmtiles_from_geojson(
                    base,
                    tiles_dir / "provinces.pmtiles",
                    layer_name="provinces",
                    min_zoom=min_zoom,
                    max_zoom=max_zoom,
                    prefer_tippecanoe=prefer_tippecanoe,
                    name="provinces-base",
                    description="Base land province tiles",
                )
            )

    if not results:
        raise TileBuildError(
            f"no tileable GeoJSON found under atlas directory: {atlas_dir}"
        )
    return results
