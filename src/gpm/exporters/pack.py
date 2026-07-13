"""M7 profile export packs: provinces, regions, adjacency, localization, attribution."""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from shapely import unary_union
from shapely.errors import ShapelyError
from shapely.geometry import mapping, shape
from shapely.geometry.base import BaseGeometry

from gpm import __version__
from gpm.config import export_settings, load_profile
from gpm.paths import EXPORT_DIR, PROCESSED_DATA_DIR
from gpm.scenarios import ScenarioError, build_scenario_ownership


class ExportError(RuntimeError):
    """Raised when an export pack cannot be produced."""


# Maps profile export.region_type onto the M21 hierarchy level it should emit
# when a hierarchy.geojson build artifact is available.
REGION_TYPE_TO_HIERARCHY_LEVEL = {
    "state": "area",
    "region": "region",
    "strategic_region": "region",
    "superregion": "superregion",
}


@dataclass(frozen=True)
class ExportPackResult:
    profile_id: str
    layout: str
    region_type: str
    output_dir: str
    pack_manifest: str
    province_count: int
    sea_zone_count: int
    region_count: int
    adjacency_count: int
    localization_entry_count: int
    attribution_record_count: int
    include_geometry: bool
    include_sea_zones: bool
    scenario_ids: tuple[str, ...]
    scenario_ownership_row_count: int
    files_written: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def export_geojson_pack(
    profile_id: str,
    *,
    province_input: Path = PROCESSED_DATA_DIR / "provinces.geojson",
    sea_input: Path | None = None,
    adjacency_input: Path | None = None,
    output_dir: Path | None = None,
) -> ExportPackResult:
    """Export only the GeoJSON portion of a profile pack (provinces/regions/seas)."""
    return export_game_pack(
        profile_id,
        province_input=province_input,
        sea_input=sea_input,
        adjacency_input=adjacency_input,
        output_dir=output_dir,
        geojson_only=True,
    )


def export_game_pack(
    profile_id: str,
    *,
    province_input: Path = PROCESSED_DATA_DIR / "provinces.geojson",
    sea_input: Path | None = None,
    adjacency_input: Path | None = None,
    hierarchy_input: Path | None = None,
    output_dir: Path | None = None,
    geojson_only: bool = False,
    scenarios: tuple[str, ...] | list[str] = (),
    allow_unknown_overrides: bool = False,
) -> ExportPackResult:
    """Write a profile-specific game template pack under exports/<profile_id>/."""
    profile = load_profile(profile_id)
    settings = export_settings(profile)
    pack_root = (output_dir or (EXPORT_DIR / profile_id)).resolve()

    if not province_input.is_file():
        raise ExportError(f"Province input does not exist: {province_input}")

    provinces_collection = _load_feature_collection(province_input, "province")
    land_features = list(provinces_collection["features"])
    if not land_features:
        raise ExportError(f"Province input has no features: {province_input}")

    resolved_sea = _resolve_optional_input(
        sea_input,
        default=province_input.parent / "sea_zones.geojson",
        enabled=bool(settings["include_sea_zones"]),
    )
    sea_features: list[dict[str, Any]] = []
    if resolved_sea is not None:
        sea_collection = _load_feature_collection(resolved_sea, "sea zone")
        sea_features = list(sea_collection["features"])

    resolved_adjacency = _resolve_optional_input(
        adjacency_input,
        default=province_input.parent / "adjacency.csv",
        enabled=not geojson_only,
    )
    adjacency_rows: list[dict[str, str]] = []
    if resolved_adjacency is not None:
        adjacency_rows = _load_adjacency_csv(resolved_adjacency)

    generated_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    region_type = str(settings["region_type"])
    include_geometry = bool(settings["include_geometry"])
    language = str(settings["localization_language"])
    definition_format = str(settings["definition_format"])

    resolved_hierarchy = _resolve_optional_input(
        hierarchy_input,
        default=province_input.parent / "hierarchy.geojson",
        enabled=True,
    )
    region_features: list[dict[str, Any]] | None = None
    region_id_scheme = "parent-region-id-v1"
    if resolved_hierarchy is not None:
        region_features = _regions_from_hierarchy(
            resolved_hierarchy,
            region_type=region_type,
            include_geometry=include_geometry,
        )
        if region_features is not None:
            region_id_scheme = "hierarchy-sha256-v1"
    if region_features is None:
        # Fallback: label-only dissolve over parent_region_id (sample scaffolds).
        region_features = _build_region_features(
            land_features,
            region_type=region_type,
            include_geometry=include_geometry,
        )

    pack_root.mkdir(parents=True, exist_ok=True)
    files_written: list[str] = []
    scenario_ids = tuple(dict.fromkeys(str(item).strip() for item in scenarios if str(item).strip()))
    scenario_ownership_row_count = 0
    if scenario_ids and geojson_only:
        raise ExportError("Scenarios cannot be embedded in geojson-only packs; use export pack.")

    geojson_dir = pack_root / "geojson"
    geojson_dir.mkdir(parents=True, exist_ok=True)

    provinces_out = geojson_dir / "provinces.geojson"
    _write_json(
        provinces_out,
        _export_feature_collection(
            name="provinces",
            profile_id=profile_id,
            generated_at=generated_at,
            features=land_features if include_geometry else _strip_geometries(land_features),
            extra_gpm={
                "milestone": "M7",
                "layer": "provinces",
                "source_path": str(province_input),
            },
        ),
    )
    files_written.append(_rel(provinces_out, pack_root))

    if sea_features:
        seas_out = geojson_dir / "sea_zones.geojson"
        _write_json(
            seas_out,
            _export_feature_collection(
                name="sea_zones",
                profile_id=profile_id,
                generated_at=generated_at,
                features=sea_features if include_geometry else _strip_geometries(sea_features),
                extra_gpm={
                    "milestone": "M7",
                    "layer": "sea_zones",
                    "source_path": str(resolved_sea),
                },
            ),
        )
        files_written.append(_rel(seas_out, pack_root))

    regions_out = geojson_dir / "regions.geojson"
    _write_json(
        regions_out,
        _export_feature_collection(
            name="regions",
            profile_id=profile_id,
            generated_at=generated_at,
            features=region_features,
            extra_gpm={
                "milestone": "M7",
                "layer": "regions",
                "region_type": region_type,
                "id_scheme": region_id_scheme,
            },
        ),
    )
    files_written.append(_rel(regions_out, pack_root))

    localization_entries: list[dict[str, str]] = []
    attribution_records: list[dict[str, Any]] = []

    if not geojson_only:
        definitions_dir = pack_root / "definitions"
        localization_dir = pack_root / "localization"
        tables_dir = pack_root / "tables"
        definitions_dir.mkdir(parents=True, exist_ok=True)
        localization_dir.mkdir(parents=True, exist_ok=True)
        tables_dir.mkdir(parents=True, exist_ok=True)

        province_defs = [_province_definition(feature) for feature in land_features]
        sea_defs = [_province_definition(feature) for feature in sea_features]
        region_defs = [_region_definition(feature) for feature in region_features]
        province_defs.sort(key=lambda item: item["province_id"])
        sea_defs.sort(key=lambda item: item["province_id"])
        region_defs.sort(key=lambda item: item["region_id"])

        if definition_format == "json":
            provinces_def_path = definitions_dir / "provinces.json"
            regions_def_path = definitions_dir / "regions.json"
            _write_json(
                provinces_def_path,
                {
                    "schema_version": "0.1.0",
                    "profile_id": profile_id,
                    "generated_at": generated_at,
                    "count": len(province_defs),
                    "provinces": province_defs,
                },
            )
            _write_json(
                regions_def_path,
                {
                    "schema_version": "0.1.0",
                    "profile_id": profile_id,
                    "generated_at": generated_at,
                    "region_type": region_type,
                    "count": len(region_defs),
                    "regions": region_defs,
                },
            )
            files_written.extend(
                [_rel(provinces_def_path, pack_root), _rel(regions_def_path, pack_root)]
            )
            if sea_defs:
                seas_def_path = definitions_dir / "sea_zones.json"
                _write_json(
                    seas_def_path,
                    {
                        "schema_version": "0.1.0",
                        "profile_id": profile_id,
                        "generated_at": generated_at,
                        "count": len(sea_defs),
                        "sea_zones": sea_defs,
                    },
                )
                files_written.append(_rel(seas_def_path, pack_root))
        else:
            provinces_def_path = definitions_dir / "provinces.csv"
            regions_def_path = definitions_dir / "regions.csv"
            _write_definition_csv(provinces_def_path, province_defs, "province")
            _write_definition_csv(regions_def_path, region_defs, "region")
            files_written.extend(
                [_rel(provinces_def_path, pack_root), _rel(regions_def_path, pack_root)]
            )
            if sea_defs:
                seas_def_path = definitions_dir / "sea_zones.csv"
                _write_definition_csv(seas_def_path, sea_defs, "province")
                files_written.append(_rel(seas_def_path, pack_root))

        adjacency_out = definitions_dir / "adjacency.csv"
        _write_adjacency_csv(adjacency_out, adjacency_rows)
        files_written.append(_rel(adjacency_out, pack_root))

        localization_entries = _build_localization_entries(
            province_defs=province_defs,
            sea_defs=sea_defs,
            region_defs=region_defs,
        )
        localization_path = localization_dir / f"{language}.json"
        yaml_path = localization_dir / f"{language}.yml"
        _write_json(
            localization_path,
            {
                "schema_version": "0.1.0",
                "language": language,
                "profile_id": profile_id,
                "generated_at": generated_at,
                "count": len(localization_entries),
                "entries": localization_entries,
            },
        )
        _write_localization_yml(yaml_path, language, localization_entries)
        files_written.extend(
            [_rel(localization_path, pack_root), _rel(yaml_path, pack_root)]
        )

        terrain_path = tables_dir / "terrain.csv"
        population_path = tables_dir / "population.csv"
        _write_terrain_table(terrain_path, province_defs + sea_defs)
        _write_population_table(population_path, province_defs + sea_defs)
        files_written.extend([_rel(terrain_path, pack_root), _rel(population_path, pack_root)])

        attribution_records = _build_attribution_records(
            land_features + sea_features,
            files_written,
        )
        attribution_path = pack_root / "attribution.json"
        _write_json(
            attribution_path,
            {"schema_version": "0.1.0", "records": attribution_records},
        )
        files_written.append(_rel(attribution_path, pack_root))

        if scenario_ids:
            scenario_root = pack_root / "scenarios"
            scenario_root.mkdir(parents=True, exist_ok=True)
            for scenario_id in scenario_ids:
                try:
                    scenario_result = build_scenario_ownership(
                        scenario_id,
                        profile_id=profile_id,
                        province_input=province_input,
                        output_dir=scenario_root / scenario_id,
                        allow_unknown_overrides=allow_unknown_overrides,
                    )
                except ScenarioError as exc:
                    raise ExportError(str(exc)) from exc
                scenario_ownership_row_count += scenario_result.ownership_row_count
                for name in scenario_result.files_written:
                    files_written.append(f"scenarios/{scenario_id}/{name}")

        readme_path = pack_root / "README.md"
        readme_path.write_text(
            _pack_readme(
                profile_id=profile_id,
                layout=str(settings["layout"]),
                region_type=region_type,
                language=language,
                include_sea_zones=bool(sea_features),
                geojson_only=False,
                scenario_ids=scenario_ids,
            ),
            encoding="utf-8",
        )
        files_written.append(_rel(readme_path, pack_root))
    else:
        readme_path = pack_root / "README.md"
        readme_path.write_text(
            _pack_readme(
                profile_id=profile_id,
                layout=str(settings["layout"]),
                region_type=region_type,
                language=language,
                include_sea_zones=bool(sea_features),
                geojson_only=True,
                scenario_ids=(),
            ),
            encoding="utf-8",
        )
        files_written.append(_rel(readme_path, pack_root))

    files_written = sorted(set(files_written))
    manifest = {
        "schema_version": "0.1.0",
        "milestone": "M8" if scenario_ids else "M7",
        "pack_type": "geojson" if geojson_only else "game-template",
        "profile_id": profile_id,
        "layout": settings["layout"],
        "region_type": region_type,
        "generated_at": generated_at,
        "generator_version": __version__,
        "include_geometry": include_geometry,
        "include_sea_zones": bool(settings["include_sea_zones"]),
        "definition_format": definition_format if not geojson_only else None,
        "localization_language": language if not geojson_only else None,
        "scenarios": list(scenario_ids),
        "inputs": {
            "provinces": str(province_input),
            "sea_zones": None if resolved_sea is None else str(resolved_sea),
            "adjacency": None if resolved_adjacency is None else str(resolved_adjacency),
        },
        "counts": {
            "provinces": len(land_features),
            "sea_zones": len(sea_features),
            "regions": len(region_features),
            "adjacency_rows": len(adjacency_rows),
            "localization_entries": len(localization_entries),
            "attribution_records": len(attribution_records),
            "scenario_ownership_rows": scenario_ownership_row_count,
        },
        "files": files_written,
        "profile_label": profile.get("profile", {}).get("label"),
        "profile_description": profile.get("profile", {}).get("description"),
        "target_province_count": profile.get("generation", {}).get("target_province_count"),
        "target_region_count": profile.get("generation", {}).get("target_region_count"),
    }
    manifest_path = pack_root / "pack_manifest.json"
    _write_json(manifest_path, manifest)
    if _rel(manifest_path, pack_root) not in files_written:
        files_written = sorted([*files_written, _rel(manifest_path, pack_root)])
        manifest["files"] = files_written
        _write_json(manifest_path, manifest)

    return ExportPackResult(
        profile_id=profile_id,
        layout=str(settings["layout"]),
        region_type=region_type,
        output_dir=str(pack_root),
        pack_manifest=str(manifest_path),
        province_count=len(land_features),
        sea_zone_count=len(sea_features),
        region_count=len(region_features),
        adjacency_count=len(adjacency_rows),
        localization_entry_count=len(localization_entries),
        attribution_record_count=len(attribution_records),
        include_geometry=include_geometry,
        include_sea_zones=bool(settings["include_sea_zones"]),
        scenario_ids=scenario_ids,
        scenario_ownership_row_count=scenario_ownership_row_count,
        files_written=tuple(files_written),
    )


def _resolve_optional_input(
    explicit: Path | None,
    *,
    default: Path,
    enabled: bool,
) -> Path | None:
    if not enabled:
        return None
    path = default if explicit is None else explicit
    if path.is_file():
        return path
    if explicit is not None:
        raise ExportError(f"Optional export input does not exist: {explicit}")
    return None


def _load_feature_collection(path: Path, label: str) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ExportError(f"Invalid {label} GeoJSON at {path}: {exc}") from exc
    if not isinstance(document, dict) or document.get("type") != "FeatureCollection":
        raise ExportError(f"{label} input must be a GeoJSON FeatureCollection: {path}")
    features = document.get("features")
    if not isinstance(features, list):
        raise ExportError(f"{label} FeatureCollection is missing a features array: {path}")
    return document


def _load_adjacency_csv(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(newline="", encoding="utf-8") as file:
            rows = list(csv.DictReader(file))
    except OSError as exc:
        raise ExportError(f"Unable to read adjacency CSV at {path}: {exc}") from exc
    return rows


def _regions_from_hierarchy(
    hierarchy_input: Path,
    *,
    region_type: str,
    include_geometry: bool,
) -> list[dict[str, Any]] | None:
    """Emit region features from an M21 hierarchy build artifact.

    Returns None when the file has no entities at the level mapped from
    ``region_type`` so callers can fall back to the parent_region_id dissolve.
    """
    level = REGION_TYPE_TO_HIERARCHY_LEVEL.get(region_type, "region")
    document = _load_feature_collection(hierarchy_input, "hierarchy")
    regions: list[dict[str, Any]] = []
    for feature in document["features"]:
        if not isinstance(feature, dict):
            continue
        properties = feature.get("properties")
        if not isinstance(properties, dict) or properties.get("region_type") != level:
            continue
        region_id = properties.get("region_id")
        if not isinstance(region_id, str) or not region_id:
            continue
        province_ids = [
            item for item in (properties.get("province_ids") or []) if isinstance(item, str)
        ]
        regions.append(
            {
                "type": "Feature",
                "geometry": feature.get("geometry") if include_geometry else None,
                "properties": {
                    "region_id": region_id,
                    "display_name": properties.get("display_name") or region_id,
                    "region_type": region_type,
                    "hierarchy_level": level,
                    "parent_country_id": _nullable_str(properties.get("parent_country_id")),
                    "parent_region_id": _nullable_str(properties.get("parent_region_id")),
                    "parent_superregion_id": _nullable_str(properties.get("parent_superregion_id")),
                    "province_ids": province_ids,
                    "province_count": len(province_ids),
                    "member_region_ids": [
                        item
                        for item in (properties.get("member_region_ids") or [])
                        if isinstance(item, str)
                    ],
                    "area_sq_km": _safe_float(properties.get("area_sq_km")) or 0.0,
                    "label_point": properties.get("label_point"),
                    "source_lineage": _as_string_list(properties.get("source_lineage")),
                    "license_lineage": _as_string_list(properties.get("license_lineage")),
                },
            }
        )
    if not regions:
        return None
    regions.sort(key=lambda feature: feature["properties"]["region_id"])
    return regions


def _build_region_features(
    land_features: list[dict[str, Any]],
    *,
    region_type: str,
    include_geometry: bool,
) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for feature in land_features:
        properties = feature.get("properties") or {}
        if not isinstance(properties, dict):
            continue
        region_id = properties.get("parent_region_id")
        if not isinstance(region_id, str) or not region_id.strip():
            country_id = properties.get("parent_country_id")
            if isinstance(country_id, str) and country_id.strip():
                region_id = f"country:{country_id.strip()}"
            else:
                province_id = properties.get("province_id")
                if isinstance(province_id, str) and province_id.strip():
                    region_id = f"orphan:{province_id.strip()}"
                else:
                    continue
        groups[region_id.strip()].append(feature)

    regions: list[dict[str, Any]] = []
    for region_id in sorted(groups):
        members = groups[region_id]
        province_ids = sorted(
            {
                str(member["properties"]["province_id"])
                for member in members
                if isinstance(member.get("properties"), dict)
                and isinstance(member["properties"].get("province_id"), str)
            }
        )
        if not province_ids:
            continue

        first_props = members[0]["properties"]
        display_name = _region_display_name(region_id, first_props)
        parent_country = first_props.get("parent_country_id")
        if not isinstance(parent_country, str):
            parent_country = None

        source_lineage = _unique_strings(
            lineage
            for member in members
            for lineage in _as_string_list((member.get("properties") or {}).get("source_lineage"))
        )
        license_lineage = _unique_strings(
            lineage
            for member in members
            for lineage in _as_string_list((member.get("properties") or {}).get("license_lineage"))
        )

        geometry: dict[str, Any] | None = None
        area_sq_km = 0.0
        if include_geometry:
            geometry, area_sq_km = _union_member_geometries(members)
        else:
            area_sq_km = sum(
                _safe_float((member.get("properties") or {}).get("area_sq_km")) or 0.0
                for member in members
            )

        regions.append(
            {
                "type": "Feature",
                "geometry": geometry,
                "properties": {
                    "region_id": region_id,
                    "display_name": display_name,
                    "region_type": region_type,
                    "parent_country_id": parent_country,
                    "parent_superregion_id": None,
                    "province_ids": province_ids,
                    "province_count": len(province_ids),
                    "area_sq_km": round(area_sq_km, 3),
                    "source_lineage": source_lineage,
                    "license_lineage": license_lineage,
                },
            }
        )
    return regions


def _union_member_geometries(
    members: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, float]:
    geometries: list[BaseGeometry] = []
    for member in members:
        raw = member.get("geometry")
        if raw is None:
            continue
        try:
            geom = shape(raw)
            if geom.is_empty:
                continue
            geometries.append(geom)
        except (ShapelyError, TypeError, ValueError):
            continue
    if not geometries:
        return None, 0.0
    try:
        merged = unary_union(geometries)
        if merged.is_empty:
            return None, 0.0
        # Approximate area in km² using spherical excess-free equirectangular
        # estimate via WGS84 projected bounds; enough for export summaries.
        area_sq_km = _geometry_area_sq_km_approx(merged)
        return mapping(merged), area_sq_km
    except (ShapelyError, TypeError, ValueError):
        return None, 0.0


def _geometry_area_sq_km_approx(geometry: BaseGeometry) -> float:
    """Approximate geodesic area from WGS84 geometry (export summary only)."""
    from gpm.geo.metrics import geometry_area_sq_km

    return float(geometry_area_sq_km(geometry))


def _region_display_name(region_id: str, sample_props: dict[str, Any]) -> str:
    if region_id.startswith("country:"):
        country = region_id.split(":", 1)[1]
        return f"{country} region"
    if region_id.startswith("orphan:"):
        return sample_props.get("display_name") or region_id
    # Prefer a human-readable slug from admin codes.
    cleaned = region_id.replace("_", " ").replace("-", " ").strip()
    return cleaned or region_id


def _province_definition(feature: dict[str, Any]) -> dict[str, Any]:
    properties = feature.get("properties") or {}
    if not isinstance(properties, dict):
        properties = {}
    province_id = properties.get("province_id")
    if not isinstance(province_id, str) or not province_id:
        raise ExportError("Province feature is missing properties.province_id.")
    display_name = properties.get("display_name")
    if not isinstance(display_name, str) or not display_name:
        display_name = province_id
    kind = properties.get("kind")
    if not isinstance(kind, str) or not kind:
        kind = "land"
    return {
        "province_id": province_id,
        "display_name": display_name,
        "kind": kind,
        "parent_region_id": _nullable_str(properties.get("parent_region_id")),
        "parent_country_id": _nullable_str(properties.get("parent_country_id")),
        "area_sq_km": _safe_float(properties.get("area_sq_km")),
        "estimated_population": _safe_float(properties.get("estimated_population")),
        "terrain_class": _nullable_str(properties.get("terrain_class")),
        "coastal": bool(properties.get("coastal", False)),
        "island": bool(properties.get("island", False)),
        "sea_class": _nullable_str(properties.get("sea_class")),
        "parent_land_province_id": _nullable_str(properties.get("parent_land_province_id")),
        "source_lineage": _as_string_list(properties.get("source_lineage")),
        "license_lineage": _as_string_list(properties.get("license_lineage")),
    }


def _region_definition(feature: dict[str, Any]) -> dict[str, Any]:
    properties = feature.get("properties") or {}
    if not isinstance(properties, dict):
        properties = {}
    region_id = properties.get("region_id")
    if not isinstance(region_id, str) or not region_id:
        raise ExportError("Region feature is missing properties.region_id.")
    return {
        "region_id": region_id,
        "display_name": properties.get("display_name") or region_id,
        "region_type": properties.get("region_type") or "region",
        "parent_country_id": _nullable_str(properties.get("parent_country_id")),
        "parent_superregion_id": _nullable_str(properties.get("parent_superregion_id")),
        "province_ids": list(properties.get("province_ids") or []),
        "province_count": int(properties.get("province_count") or 0),
        "area_sq_km": _safe_float(properties.get("area_sq_km")),
        "source_lineage": _as_string_list(properties.get("source_lineage")),
        "license_lineage": _as_string_list(properties.get("license_lineage")),
    }


def _build_localization_entries(
    *,
    province_defs: list[dict[str, Any]],
    sea_defs: list[dict[str, Any]],
    region_defs: list[dict[str, Any]],
) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for item in province_defs:
        entries.append(
            {
                "key": f"PROVINCE_{item['province_id']}",
                "text": str(item["display_name"]),
                "entity_type": "province",
                "entity_id": str(item["province_id"]),
            }
        )
    for item in sea_defs:
        entries.append(
            {
                "key": f"SEA_{item['province_id']}",
                "text": str(item["display_name"]),
                "entity_type": "sea_zone",
                "entity_id": str(item["province_id"]),
            }
        )
    for item in region_defs:
        entries.append(
            {
                "key": f"REGION_{item['region_id']}",
                "text": str(item["display_name"]),
                "entity_type": "region",
                "entity_id": str(item["region_id"]),
            }
        )
    entries.sort(key=lambda row: (row["entity_type"], row["key"]))
    return entries


def _build_attribution_records(
    features: list[dict[str, Any]],
    files_written: list[str],
) -> list[dict[str, Any]]:
    notices: dict[str, dict[str, Any]] = {}
    for feature in features:
        properties = feature.get("properties") or {}
        if not isinstance(properties, dict):
            continue
        licenses = _as_string_list(properties.get("license_lineage"))
        sources = _as_string_list(properties.get("source_lineage"))
        for license_text in licenses:
            source_id = _guess_source_id(license_text, sources)
            key = f"{source_id}|{license_text}"
            if key not in notices:
                notices[key] = {
                    "source_id": source_id,
                    "title": _title_for_source(source_id, license_text),
                    "license": license_text,
                    "attribution_text": license_text,
                    "url": _url_for_source(source_id),
                    "required": True,
                    "downstream_outputs": [],
                }
    downstream = sorted(
        {
            path
            for path in files_written
            if path.endswith((".geojson", ".csv", ".json", ".yml", ".md"))
        }
    )
    records = []
    for key in sorted(notices):
        record = notices[key]
        record["downstream_outputs"] = list(downstream)
        records.append(record)
    if not records:
        records.append(
            {
                "source_id": "unknown",
                "title": "Unknown source lineage",
                "license": "unspecified",
                "attribution_text": "Attribution lineage was not present on exported features.",
                "url": "https://example.invalid/",
                "required": True,
                "downstream_outputs": list(downstream),
            }
        )
    return records


def _guess_source_id(license_text: str, source_lineage: list[str]) -> str:
    lowered = license_text.lower()
    if "natural earth" in lowered:
        return "natural_earth"
    if "geoboundaries" in lowered or "geoBoundaries" in license_text:
        return "geoboundaries"
    if "worldpop" in lowered:
        return "worldpop"
    if "ghsl" in lowered:
        return "ghsl"
    for source in source_lineage:
        if ":" in source:
            return source.split(":", 1)[0]
        if source:
            return source
    return "derived"


def _title_for_source(source_id: str, license_text: str) -> str:
    titles = {
        "natural_earth": "Natural Earth",
        "geoboundaries": "geoBoundaries",
        "worldpop": "WorldPop",
        "ghsl": "GHSL",
    }
    return titles.get(source_id, license_text)


def _url_for_source(source_id: str) -> str:
    urls = {
        "natural_earth": "https://www.naturalearthdata.com/",
        "geoboundaries": "https://www.geoboundaries.org/",
        "worldpop": "https://www.worldpop.org/",
        "ghsl": "https://ghsl.jrc.ec.europa.eu/",
    }
    return urls.get(source_id, "https://example.invalid/")


def _export_feature_collection(
    *,
    name: str,
    profile_id: str,
    generated_at: str,
    features: list[dict[str, Any]],
    extra_gpm: dict[str, Any],
) -> dict[str, Any]:
    return {
        "type": "FeatureCollection",
        "name": name,
        "gpm": {
            "schema_version": "0.1.0",
            "milestone": "M7",
            "profile_id": profile_id,
            "generated_at": generated_at,
            "generator_version": __version__,
            "feature_count": len(features),
            **extra_gpm,
        },
        "features": features,
    }


def _strip_geometries(features: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stripped = []
    for feature in features:
        stripped.append(
            {
                "type": "Feature",
                "geometry": None,
                "properties": feature.get("properties") or {},
            }
        )
    return stripped


def _write_definition_csv(
    path: Path,
    rows: list[dict[str, Any]],
    kind: str,
) -> None:
    if kind == "province":
        fieldnames = [
            "province_id",
            "display_name",
            "kind",
            "parent_region_id",
            "parent_country_id",
            "area_sq_km",
            "estimated_population",
            "terrain_class",
            "coastal",
            "island",
            "sea_class",
            "parent_land_province_id",
            "source_lineage",
            "license_lineage",
        ]
    else:
        fieldnames = [
            "region_id",
            "display_name",
            "region_type",
            "parent_country_id",
            "parent_superregion_id",
            "province_ids",
            "province_count",
            "area_sq_km",
            "source_lineage",
            "license_lineage",
        ]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            serialized = dict(row)
            for key in ("source_lineage", "license_lineage", "province_ids"):
                if key in serialized and isinstance(serialized[key], list):
                    serialized[key] = json.dumps(serialized[key], ensure_ascii=False)
            for key in ("coastal", "island"):
                if key in serialized and isinstance(serialized[key], bool):
                    serialized[key] = "true" if serialized[key] else "false"
            writer.writerow({field: serialized.get(field, "") for field in fieldnames})


def _write_adjacency_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "from_province_id",
        "to_province_id",
        "adjacency_type",
        "bidirectional",
        "crossing_type",
        "shared_border_km",
        "source_lineage",
    ]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def _write_terrain_table(path: Path, defs: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["province_id", "terrain_class", "kind", "coastal", "island"],
        )
        writer.writeheader()
        for item in sorted(defs, key=lambda row: row["province_id"]):
            writer.writerow(
                {
                    "province_id": item["province_id"],
                    "terrain_class": item.get("terrain_class") or "",
                    "kind": item.get("kind") or "",
                    "coastal": "true" if item.get("coastal") else "false",
                    "island": "true" if item.get("island") else "false",
                }
            )


def _write_population_table(path: Path, defs: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["province_id", "estimated_population", "area_sq_km", "kind"],
        )
        writer.writeheader()
        for item in sorted(defs, key=lambda row: row["province_id"]):
            population = item.get("estimated_population")
            area = item.get("area_sq_km")
            writer.writerow(
                {
                    "province_id": item["province_id"],
                    "estimated_population": "" if population is None else population,
                    "area_sq_km": "" if area is None else area,
                    "kind": item.get("kind") or "",
                }
            )


def _write_localization_yml(
    path: Path,
    language: str,
    entries: list[dict[str, str]],
) -> None:
    lines = [f"l_{language}:"]
    for entry in entries:
        # Escape double quotes for a portable game-mod style stub.
        text = str(entry["text"]).replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f' {entry["key"]}:0 "{text}"')
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _pack_readme(
    *,
    profile_id: str,
    layout: str,
    region_type: str,
    language: str,
    include_sea_zones: bool,
    geojson_only: bool,
    scenario_ids: tuple[str, ...] = (),
) -> str:
    sea_note = (
        "Sea zones are included when `sea_zones.geojson` was present at export time."
        if include_sea_zones
        else "Sea zones were not included in this pack."
    )
    if scenario_ids:
        scenario_table_rows = "\n".join(
            f"| `scenarios/{scenario_id}/` | Ownership overlay for scenario `{scenario_id}` |"
            for scenario_id in scenario_ids
        )
        scenario_note = (
            "Scenario ownership tables are curated political overlays. Province geometry "
            "is unchanged. Join `scenarios/<id>/ownership.csv` on `province_id`."
        )
    else:
        scenario_table_rows = ""
        scenario_note = (
            "No scenarios were embedded. Use `gpm scenario build` or "
            "`gpm export pack --scenario <id>` for historical ownership tables."
        )
    if geojson_only:
        body = f"""# GPM GeoJSON export: `{profile_id}`

Layout: `{layout}` · region type: `{region_type}`

## Contents

- `geojson/provinces.geojson` — land provinces
- `geojson/regions.geojson` — regions grouped from `parent_region_id`
- `geojson/sea_zones.geojson` — optional coastal/ocean sea zones
- `pack_manifest.json` — export metadata and file list

{sea_note}

Generated by Global Province Map Template (M7). Geometry is independent of
proprietary game maps.
"""
    else:
        body = f"""# GPM game template pack: `{profile_id}`

Layout: `{layout}` · region type: `{region_type}` · localization: `{language}`

## Contents

| Path | Purpose |
| --- | --- |
| `geojson/provinces.geojson` | Land province polygons |
| `geojson/regions.geojson` | Aggregated region polygons (`region_type={region_type}`) |
| `geojson/sea_zones.geojson` | Optional sea zones |
| `definitions/provinces.json` | Province attributes without geometry |
| `definitions/regions.json` | Region membership and hierarchy |
| `definitions/adjacency.csv` | Land/sea/port/strait adjacency |
| `localization/{language}.json` | Machine-readable name stubs |
| `localization/{language}.yml` | Game-mod style name stubs |
| `tables/terrain.csv` | Terrain class per province |
| `tables/population.csv` | Population and area per province |
| `attribution.json` | License notices for redistribution |
| `pack_manifest.json` | Pack metadata and file inventory |
{scenario_table_rows}

{sea_note}

{scenario_note}

## How to consume

1. Use `definitions/*.json` (or CSV) as the game data tables.
2. Join localization keys such as `PROVINCE_<id>` and `REGION_<id>` into UI text.
3. Load `definitions/adjacency.csv` for movement/graph systems.
4. Join scenario `ownership.csv` on `province_id` for owner/controller/cores/claims.
5. Keep `attribution.json` with any redistributed dataset.
6. Treat geometry under `geojson/` as optional visual or physics input.

Generated by Global Province Map Template (M8 scenario-aware packs, M7 geometry).
Outputs are open-geodata derivatives, not proprietary game map files.
"""
    return body


def _write_json(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def _as_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            if isinstance(item, str) and item.strip():
                result.append(item.strip())
        return result
    return []


def _unique_strings(values: Any) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def _nullable_str(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        parsed = float(value)
        return parsed if math.isfinite(parsed) else None
    return None
