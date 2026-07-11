from __future__ import annotations

import hashlib
import json
import math
import unicodedata
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

from shapely import make_valid, normalize, to_wkb
from shapely.errors import ShapelyError
from shapely.geometry import box, mapping, shape
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from gpm import __version__
from gpm.config import load_profile, sea_zone_settings
from gpm.geo.metrics import EARTH_RADIUS_KM, geometry_area_sq_km, polygon_parts
from gpm.geo.shapefile import ShapefileReadError, read_zipped_shapefile
from gpm.paths import PROCESSED_DATA_DIR, RAW_DATA_DIR
from gpm.sources.registry import resolve_source_adapters


class SeaBuildError(RuntimeError):
    """Raised when sea-zone generation cannot continue."""


@dataclass(frozen=True)
class SeaBuildResult:
    profile_id: str
    strategy: str
    province_input: str
    sea_output: str
    province_output: str | None
    land_province_count: int
    coastal_province_count: int
    coastal_sea_zone_count: int
    ocean_sea_zone_count: int
    sea_zone_count: int
    coastal_buffer_km: float
    ocean_cell_size_deg: float
    strait_max_distance_km: float
    land_mask_source: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class _LandProvince:
    province_id: str
    display_name: str
    geometry: BaseGeometry
    source_lineage: tuple[str, ...]
    license_lineage: tuple[str, ...]
    parent_country_id: str | None
    parent_region_id: str | None


def build_sea_zones(
    profile_id: str,
    *,
    province_input: Path = PROCESSED_DATA_DIR / "provinces.geojson",
    sea_output: Path = PROCESSED_DATA_DIR / "sea_zones.geojson",
    province_output: Path | None = None,
    raw_dir: Path = RAW_DATA_DIR,
    update_provinces: bool = True,
) -> SeaBuildResult:
    """Generate coastal and ocean sea zones plus coastal flags from land provinces.

    Sea zones are gameplay-first abstractions derived from open Natural Earth land
    polygons (or the union of land provinces when the land mask is unavailable):
    a coastal band is claimed by each land province that reaches the water, and the
    remaining ocean is partitioned into a deterministic lon/lat grid.
    """
    profile = load_profile(profile_id)
    settings = sea_zone_settings(profile)
    coastal_buffer_km = float(settings["coastal_buffer_km"])
    ocean_cell_size_deg = float(settings["ocean_cell_size_deg"])
    strait_max_distance_km = float(settings["strait_max_distance_km"])
    min_sea_area_sq_km = float(settings["min_sea_area_sq_km"])
    strategy = str(settings["strategy"])

    land_provinces, province_document = _load_land_provinces(province_input)
    if not land_provinces:
        raise SeaBuildError(f"No land provinces found in {province_input}")

    land_mask, land_mask_source, land_lineage, land_license = _load_land_mask(
        raw_dir,
        land_provinces,
        profile_id=profile_id,
    )
    buffer_deg = _km_to_degrees(coastal_buffer_km)
    try:
        land_mask = make_valid(land_mask)
        # Domain is driven by land-province extent so local fixture builds stay
        # cheap even when a global Natural Earth land mask is present.
        province_union = unary_union([province.geometry for province in land_provinces])
        domain = _domain_for_mask(province_union, buffer_deg)
        land_in_domain = _as_polygonal(make_valid(land_mask.intersection(domain)))
        if land_in_domain.is_empty:
            land_in_domain = make_valid(province_union)
        ocean = _as_polygonal(make_valid(domain.difference(land_in_domain)))
        if ocean.is_empty:
            raise SeaBuildError("Ocean geometry is empty after subtracting the land mask.")

        coastal_features, coastal_ids = _build_coastal_zones(
            land_provinces,
            land_mask=land_in_domain,
            ocean=ocean,
            buffer_deg=buffer_deg,
            min_sea_area_sq_km=min_sea_area_sq_km,
            strategy=strategy,
            land_lineage=land_lineage,
            land_license=land_license,
        )
        claimed_coastal = unary_union([shape(feature["geometry"]) for feature in coastal_features])
        if claimed_coastal.is_empty:
            deep_ocean = ocean
        else:
            deep_ocean = _as_polygonal(make_valid(ocean.difference(claimed_coastal)))
        ocean_features = _build_ocean_zones(
            deep_ocean,
            cell_size_deg=ocean_cell_size_deg,
            min_sea_area_sq_km=min_sea_area_sq_km,
            strategy=strategy,
            land_lineage=land_lineage,
            land_license=land_license,
        )
    except ShapelyError as exc:
        raise SeaBuildError(f"Geometry overlay failed while building sea zones: {exc}") from exc

    sea_features = sorted(
        [*coastal_features, *ocean_features],
        key=lambda feature: feature["properties"]["province_id"],
    )
    _ensure_unique_ids(sea_features)

    generated_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    sea_document = {
        "type": "FeatureCollection",
        "name": "sea_zones",
        "gpm": {
            "schema_version": "0.1.0",
            "id_scheme": "sea-geometry-sha256-v1",
            "profile_id": profile_id,
            "generated_at": generated_at,
            "generator_version": __version__,
            "milestone": "M6",
            "sea_zone_strategy": strategy,
            "coastal_buffer_km": coastal_buffer_km,
            "ocean_cell_size_deg": ocean_cell_size_deg,
            "strait_max_distance_km": strait_max_distance_km,
            "min_sea_area_sq_km": min_sea_area_sq_km,
            "land_mask_source": land_mask_source,
            "draft_notes": [
                "M6 sea zones are gameplay-first abstractions, not legal EEZ or IHO boundaries.",
                "Coastal zones are land-province influence bands over open water.",
                "Ocean zones are deterministic lon/lat grid cells over remaining water.",
                "Port-to-sea and strait links are produced by `gpm build adjacency` when sea zones are present.",
            ],
        },
        "features": sea_features,
    }
    _write_json(sea_output, sea_document)

    province_output_path: Path | None = None
    if update_provinces:
        province_output_path = province_output or province_input
        updated = _apply_coastal_flags(province_document, coastal_ids)
        _write_json(province_output_path, updated)

    return SeaBuildResult(
        profile_id=profile_id,
        strategy=strategy,
        province_input=str(province_input),
        sea_output=str(sea_output),
        province_output=None if province_output_path is None else str(province_output_path),
        land_province_count=len(land_provinces),
        coastal_province_count=len(coastal_ids),
        coastal_sea_zone_count=len(coastal_features),
        ocean_sea_zone_count=len(ocean_features),
        sea_zone_count=len(sea_features),
        coastal_buffer_km=coastal_buffer_km,
        ocean_cell_size_deg=ocean_cell_size_deg,
        strait_max_distance_km=strait_max_distance_km,
        land_mask_source=land_mask_source,
    )


def _load_land_provinces(path: Path) -> tuple[list[_LandProvince], dict[str, Any]]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SeaBuildError(f"Province input does not exist: {path}") from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SeaBuildError(f"Cannot read province GeoJSON {path}: {exc}") from exc
    if not isinstance(document, dict) or document.get("type") != "FeatureCollection":
        raise SeaBuildError(f"Province input must be a GeoJSON FeatureCollection: {path}")
    features = document.get("features")
    if not isinstance(features, list):
        raise SeaBuildError(f"Province GeoJSON features must be an array: {path}")

    provinces: list[_LandProvince] = []
    seen: set[str] = set()
    for index, feature in enumerate(features):
        label = f"features[{index}]"
        if not isinstance(feature, dict) or not isinstance(feature.get("properties"), dict):
            raise SeaBuildError(f"Province {label} must have an object properties member.")
        properties = feature["properties"]
        if properties.get("kind") != "land":
            continue
        province_id = properties.get("province_id")
        if not isinstance(province_id, str) or not province_id:
            raise SeaBuildError(f"Land province {label} must have a non-empty province_id.")
        if province_id in seen:
            raise SeaBuildError(f"Duplicate province_id in sea input: {province_id}")
        seen.add(province_id)
        geometry_mapping = feature.get("geometry")
        if not isinstance(geometry_mapping, dict) or geometry_mapping.get("type") not in {
            "Polygon",
            "MultiPolygon",
        }:
            raise SeaBuildError(f"Land province {province_id} must have Polygon or MultiPolygon geometry.")
        try:
            geometry = make_valid(shape(geometry_mapping))
        except (ShapelyError, TypeError, ValueError) as exc:
            raise SeaBuildError(f"Malformed geometry for province {province_id}: {exc}") from exc
        if geometry.is_empty:
            raise SeaBuildError(f"Province {province_id} has empty geometry.")
        source_lineage = _string_list(properties.get("source_lineage"), f"{province_id}.source_lineage")
        license_lineage = _string_list(properties.get("license_lineage"), f"{province_id}.license_lineage")
        display_name = properties.get("display_name")
        if not isinstance(display_name, str) or not display_name:
            display_name = province_id
        parent_country = properties.get("parent_country_id")
        parent_region = properties.get("parent_region_id")
        provinces.append(
            _LandProvince(
                province_id=province_id,
                display_name=display_name,
                geometry=geometry,
                source_lineage=tuple(source_lineage),
                license_lineage=tuple(license_lineage),
                parent_country_id=parent_country if isinstance(parent_country, str) else None,
                parent_region_id=parent_region if isinstance(parent_region, str) else None,
            )
        )
    provinces.sort(key=lambda item: item.province_id)
    return provinces, document


def _load_land_mask(
    raw_dir: Path,
    land_provinces: list[_LandProvince],
    *,
    profile_id: str,
) -> tuple[BaseGeometry, str, tuple[str, ...], tuple[str, ...]]:
    land_path = _natural_earth_land_path(profile_id, raw_dir)
    if land_path is not None and land_path.is_file():
        try:
            features = read_zipped_shapefile(land_path)
        except ShapefileReadError as exc:
            raise SeaBuildError(str(exc)) from exc
        geometries = []
        for feature in features:
            try:
                geometries.append(make_valid(shape(feature.geometry)))
            except (ShapelyError, TypeError, ValueError):
                continue
        if not geometries:
            raise SeaBuildError(f"Natural Earth land archive produced no usable polygons: {land_path}")
        land = unary_union(geometries)
        lineage = (f"natural_earth:land:{_manifest_path(land_path)}",)
        license_lineage = ("Natural Earth public domain",)
        return land, f"natural_earth:land:{_manifest_path(land_path)}", lineage, license_lineage

    land = unary_union([province.geometry for province in land_provinces])
    lineage = sorted({item for province in land_provinces for item in province.source_lineage})
    license_lineage = sorted({item for province in land_provinces for item in province.license_lineage})
    if not license_lineage:
        license_lineage = ["unknown-license"]
    return land, "land-province-union", tuple(lineage), tuple(license_lineage)


def _natural_earth_land_path(profile_id: str, raw_dir: Path) -> Path | None:
    try:
        adapters = resolve_source_adapters(profile_id, ["natural_earth"])
    except Exception:
        return None
    for download in adapters[0].planned_downloads():
        if download.layer_id != "land":
            continue
        return _raw_artifact_path(download.expected_path, raw_dir)
    return None


def _raw_artifact_path(expected_path: str, raw_dir: Path) -> Path:
    parts = PurePosixPath(expected_path).parts
    if len(parts) < 3 or parts[0:2] != ("data", "raw"):
        raise SeaBuildError(f"Planned source artifact path must be under data/raw/: {expected_path}")
    return raw_dir.expanduser() / Path(*parts[2:])


def _domain_for_mask(land_mask: BaseGeometry, buffer_deg: float) -> BaseGeometry:
    minx, miny, maxx, maxy = land_mask.bounds
    # Expand slightly past the coastal buffer so ocean cells exist around land.
    pad = max(buffer_deg * 2.0, 1.0)
    return box(
        max(-180.0, minx - pad),
        max(-90.0, miny - pad),
        min(180.0, maxx + pad),
        min(90.0, maxy + pad),
    )


def _build_coastal_zones(
    land_provinces: list[_LandProvince],
    *,
    land_mask: BaseGeometry,
    ocean: BaseGeometry,
    buffer_deg: float,
    min_sea_area_sq_km: float,
    strategy: str,
    land_lineage: tuple[str, ...],
    land_license: tuple[str, ...],
) -> tuple[list[dict[str, Any]], set[str]]:
    """Claim coastal water with per-province buffers (avoids global land buffering)."""
    if ocean.is_empty:
        return [], set()

    features: list[dict[str, Any]] = []
    coastal_ids: set[str] = set()
    claimed_parts: list[BaseGeometry] = []

    # Claim order is deterministic by province_id (already sorted).
    for province in land_provinces:
        buffered = make_valid(province.geometry.buffer(buffer_deg))
        claim = _as_polygonal(make_valid(buffered.difference(land_mask).intersection(ocean)))
        if claimed_parts:
            claim = _as_polygonal(make_valid(claim.difference(unary_union(claimed_parts))))
        if claim.is_empty:
            continue
        area = geometry_area_sq_km(claim)
        if area + 1e-12 < min_sea_area_sq_km:
            continue
        coastal_ids.add(province.province_id)
        claimed_parts.append(claim)
        source_lineage = sorted(set(province.source_lineage) | set(land_lineage))
        license_lineage = sorted(set(province.license_lineage) | set(land_license))
        features.append(
            _sea_feature(
                claim,
                sea_class="coastal",
                strategy=strategy,
                display_name=f"Coastal waters of {province.display_name}",
                parent_land_province_id=province.province_id,
                parent_country_id=province.parent_country_id,
                parent_region_id=province.parent_region_id,
                source_lineage=source_lineage,
                license_lineage=license_lineage,
            )
        )
    return features, coastal_ids


def _build_ocean_zones(
    deep_ocean: BaseGeometry,
    *,
    cell_size_deg: float,
    min_sea_area_sq_km: float,
    strategy: str,
    land_lineage: tuple[str, ...],
    land_license: tuple[str, ...],
) -> list[dict[str, Any]]:
    if deep_ocean.is_empty:
        return []
    minx, miny, maxx, maxy = deep_ocean.bounds
    # Snap the grid origin so identical domains produce identical cells.
    origin_x = math.floor(minx / cell_size_deg) * cell_size_deg
    origin_y = math.floor(miny / cell_size_deg) * cell_size_deg
    features: list[dict[str, Any]] = []
    x = origin_x
    while x < maxx - 1e-12:
        y = origin_y
        while y < maxy - 1e-12:
            cell = box(x, y, x + cell_size_deg, y + cell_size_deg)
            piece = _as_polygonal(make_valid(deep_ocean.intersection(cell)))
            if not piece.is_empty:
                area = geometry_area_sq_km(piece)
                if area + 1e-12 >= min_sea_area_sq_km:
                    col = int(round((x - origin_x) / cell_size_deg))
                    row = int(round((y - origin_y) / cell_size_deg))
                    features.append(
                        _sea_feature(
                            piece,
                            sea_class="ocean",
                            strategy=strategy,
                            display_name=f"Ocean cell {col},{row}",
                            parent_land_province_id=None,
                            parent_country_id=None,
                            parent_region_id=None,
                            source_lineage=list(land_lineage),
                            license_lineage=list(land_license),
                            grid_col=col,
                            grid_row=row,
                        )
                    )
            y += cell_size_deg
        x += cell_size_deg
    return features


def _sea_feature(
    geometry: BaseGeometry,
    *,
    sea_class: str,
    strategy: str,
    display_name: str,
    parent_land_province_id: str | None,
    parent_country_id: str | None,
    parent_region_id: str | None,
    source_lineage: list[str],
    license_lineage: list[str],
    grid_col: int | None = None,
    grid_row: int | None = None,
) -> dict[str, Any]:
    canonical = normalize(geometry)
    geometry_mapping = mapping(canonical)
    province_id = _sea_province_id(
        geometry_mapping,
        sea_class=sea_class,
        parent_land_province_id=parent_land_province_id,
        grid_col=grid_col,
        grid_row=grid_row,
    )
    properties: dict[str, Any] = {
        "province_id": province_id,
        "display_name": display_name,
        "kind": "sea",
        "sea_class": sea_class,
        "parent_region_id": parent_region_id,
        "parent_country_id": parent_country_id,
        "parent_land_province_id": parent_land_province_id,
        "area_sq_km": round(geometry_area_sq_km(canonical), 3),
        "estimated_population": None,
        "terrain_class": "sea",
        "coastal": sea_class == "coastal",
        "island": False,
        "source_lineage": source_lineage,
        "license_lineage": license_lineage,
        "sea_zone_strategy": strategy,
    }
    if grid_col is not None:
        properties["ocean_grid_col"] = grid_col
    if grid_row is not None:
        properties["ocean_grid_row"] = grid_row
    return {
        "type": "Feature",
        "geometry": geometry_mapping,
        "properties": properties,
    }


def _sea_province_id(
    geometry: dict[str, Any],
    *,
    sea_class: str,
    parent_land_province_id: str | None,
    grid_col: int | None,
    grid_row: int | None,
) -> str:
    try:
        geometry_wkb = to_wkb(normalize(shape(geometry)), byte_order=1, include_srid=False)
    except (ShapelyError, TypeError, ValueError) as exc:
        raise SeaBuildError(f"Cannot derive a sea-zone ID from malformed geometry: {exc}") from exc
    identity = json.dumps(
        {
            "sea_class": sea_class,
            "parent_land_province_id": parent_land_province_id or "",
            "grid_col": grid_col if grid_col is not None else "",
            "grid_row": grid_row if grid_row is not None else "",
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    digest = hashlib.sha256(identity + b"\0" + geometry_wkb).hexdigest()[:12]
    if sea_class == "coastal" and parent_land_province_id:
        slug = _slug_token(parent_land_province_id) or "coast"
        return f"sea_coastal-{slug}-{digest}"
    if sea_class == "ocean" and grid_col is not None and grid_row is not None:
        return f"sea_ocean-{grid_col}-{grid_row}-{digest}"
    return f"sea_{sea_class}-{digest}"


def _apply_coastal_flags(document: dict[str, Any], coastal_ids: set[str]) -> dict[str, Any]:
    updated = json.loads(json.dumps(document))
    gpm = updated.setdefault("gpm", {})
    if isinstance(gpm, dict):
        gpm["coastal_flags_updated_by"] = "M6"
        gpm["coastal_province_count"] = len(coastal_ids)
    for feature in updated.get("features", []):
        if not isinstance(feature, dict) or not isinstance(feature.get("properties"), dict):
            continue
        properties = feature["properties"]
        if properties.get("kind") != "land":
            continue
        province_id = properties.get("province_id")
        if isinstance(province_id, str):
            properties["coastal"] = province_id in coastal_ids
    return updated


def _ensure_unique_ids(features: list[dict[str, Any]]) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for feature in features:
        province_id = feature["properties"]["province_id"]
        if province_id in seen:
            duplicates.add(province_id)
        seen.add(province_id)
    if duplicates:
        joined = ", ".join(sorted(duplicates))
        raise SeaBuildError(f"Deterministic sea-zone ID collision(s): {joined}")


def _as_polygonal(geometry: BaseGeometry) -> BaseGeometry:
    if geometry.is_empty:
        return geometry
    if geometry.geom_type in {"Polygon", "MultiPolygon"}:
        return geometry
    parts = [part for part in polygon_parts(geometry)]
    if not parts:
        return geometry.intersection(geometry)  # empty polygonal of same type family
    if len(parts) == 1:
        return parts[0]
    return unary_union(parts)


def _string_list(value: Any, label: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise SeaBuildError(f"{label} must be an array of non-empty strings.")
    return list(value)


def _km_to_degrees(distance_km: float) -> float:
    # Equatorial approximation; adequate for gameplay coastal bands.
    return distance_km / (2 * math.pi * EARTH_RADIUS_KM / 360.0)


def _slug_token(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", errors="ignore").decode("ascii")
    token: list[str] = []
    previous_dash = False
    for character in value.lower():
        if character.isalnum():
            token.append(character)
            previous_dash = False
        elif not previous_dash:
            token.append("-")
            previous_dash = True
    return "".join(token).strip("-")


def _write_json(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n"
    try:
        path.write_text(payload, encoding="utf-8")
    except OSError as exc:
        raise SeaBuildError(f"Cannot write sea-zone GeoJSON {path}: {exc}") from exc


def _manifest_path(path: Path) -> str:
    try:
        from gpm.paths import PROJECT_ROOT

        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())
