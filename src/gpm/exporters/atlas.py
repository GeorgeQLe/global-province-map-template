"""M10 atlas / SaaS export face: scenario-joined choropleths, tag legends, web tables."""

from __future__ import annotations

import colorsys
import csv
import hashlib
import json
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
from gpm.config import load_profile
from gpm.exporters.pack import ExportError, _build_attribution_records
from gpm.paths import EXPORT_DIR, PROCESSED_DATA_DIR
from gpm.scenarios import ScenarioError, load_scenario, resolve_ownership_records

ATLAS_SCHEMA_VERSION = "0.1.0"
DEFAULT_ATLAS_SCENARIOS: tuple[str, ...] = ("modern-baseline",)
FALLBACK_FILL = "#b0b0b0"
UNKNOWN_FILL = "#8a8a8a"
DISPUTED_OUTLINE = "#c0392b"

PROVINCE_TABLE_FIELDS = (
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
)

OWNERSHIP_TABLE_FIELDS = (
    "province_id",
    "scenario_id",
    "start_date",
    "end_date",
    "owner",
    "controller",
    "cores",
    "claims",
    "culture",
    "religion",
    "disputed",
    "assignment_source",
    "parent_country_id",
    "parent_region_id",
    "display_name",
    "notes",
    "owner_color",
    "controller_color",
)


@dataclass(frozen=True)
class AtlasExportResult:
    profile_id: str
    pack_type: str
    output_dir: str
    atlas_manifest: str
    province_count: int
    scenario_ids: tuple[str, ...]
    scenario_ownership_row_count: int
    tag_count: int
    legend_entry_count: int
    attribution_record_count: int
    include_base_geometry: bool
    include_owner_dissolve: bool
    files_written: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def export_atlas_pack(
    profile_id: str,
    *,
    province_input: Path = PROCESSED_DATA_DIR / "provinces.geojson",
    output_dir: Path | None = None,
    scenarios: tuple[str, ...] | list[str] | None = None,
    allow_unknown_overrides: bool = False,
    include_base_geometry: bool = True,
    include_owner_dissolve: bool = True,
) -> AtlasExportResult:
    """Write an atlas / SaaS package under exports/atlas/<profile_id>/."""
    load_profile(profile_id)
    if not province_input.is_file():
        raise ExportError(f"Province input does not exist: {province_input}")

    scenario_ids = tuple(
        dict.fromkeys(
            str(item).strip()
            for item in (scenarios if scenarios is not None else DEFAULT_ATLAS_SCENARIOS)
            if str(item).strip()
        )
    )
    if not scenario_ids:
        raise ExportError(
            "Atlas export requires at least one scenario. "
            "Pass --scenario <id> (for example modern-baseline)."
        )

    collection = _load_feature_collection(province_input, "province")
    land_features = _land_features(collection["features"])
    if not land_features:
        raise ExportError(f"Province input has no land features: {province_input}")

    pack_root = (output_dir or (EXPORT_DIR / "atlas" / profile_id)).resolve()
    pack_root.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    files_written: list[str] = []
    scenario_summaries: list[dict[str, Any]] = []
    ownership_row_total = 0
    legend_entry_total = 0
    tag_ids: set[str] = set()

    tables_dir = pack_root / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)
    province_table_path = tables_dir / "provinces.csv"
    _write_province_table(province_table_path, land_features)
    files_written.append(_rel(province_table_path, pack_root))

    if include_base_geometry:
        geojson_dir = pack_root / "geojson"
        geojson_dir.mkdir(parents=True, exist_ok=True)
        base_path = geojson_dir / "provinces.geojson"
        _write_json(
            base_path,
            _feature_collection(
                name="provinces",
                profile_id=profile_id,
                generated_at=generated_at,
                features=land_features,
                extra_gpm={
                    "milestone": "M10",
                    "layer": "provinces",
                    "pack_type": "atlas",
                    "source_path": str(province_input),
                },
            ),
        )
        files_written.append(_rel(base_path, pack_root))

    scenarios_root = pack_root / "scenarios"
    scenarios_root.mkdir(parents=True, exist_ok=True)

    for scenario_id in scenario_ids:
        try:
            scenario = load_scenario(scenario_id)
            records, stats = resolve_ownership_records(
                scenario,
                land_features,
                allow_unknown_overrides=allow_unknown_overrides,
            )
        except ScenarioError as exc:
            raise ExportError(str(exc)) from exc

        scenario_dir = scenarios_root / scenario_id
        scenario_dir.mkdir(parents=True, exist_ok=True)
        ownership_by_id = {row["province_id"]: row for row in records}
        colors = _color_map_for_records(records)
        countries = _country_catalog(scenario, records)
        display_by_tag = {item["tag"]: item["display_name"] for item in countries}

        choropleth_features = _build_choropleth_features(
            land_features,
            ownership_by_id,
            colors,
        )
        choropleth_path = scenario_dir / "ownership_choropleth.geojson"
        _write_json(
            choropleth_path,
            _feature_collection(
                name=f"ownership_choropleth_{scenario_id}",
                profile_id=profile_id,
                generated_at=generated_at,
                features=choropleth_features,
                extra_gpm={
                    "milestone": "M10",
                    "layer": "ownership_choropleth",
                    "pack_type": "atlas",
                    "scenario_id": scenario_id,
                    "era": scenario["era"],
                    "start_date": scenario["start_date"],
                    "end_date": scenario.get("end_date"),
                    "paint_field": "owner",
                    "color_field": "owner_color",
                },
            ),
        )
        files_written.append(_rel(choropleth_path, pack_root))

        uncertainty_features = [
            feature
            for feature in choropleth_features
            if _is_uncertain(feature.get("properties") or {})
        ]
        uncertainty_path = scenario_dir / "uncertainty.geojson"
        _write_json(
            uncertainty_path,
            _feature_collection(
                name=f"uncertainty_{scenario_id}",
                profile_id=profile_id,
                generated_at=generated_at,
                features=uncertainty_features,
                extra_gpm={
                    "milestone": "M10",
                    "layer": "uncertainty",
                    "pack_type": "atlas",
                    "scenario_id": scenario_id,
                    "criteria": [
                        "disputed == true",
                        "owner != controller",
                        "owner == UNK",
                    ],
                    "outline_color": DISPUTED_OUTLINE,
                },
            ),
        )
        files_written.append(_rel(uncertainty_path, pack_root))

        owner_feature_count = 0
        if include_owner_dissolve:
            owner_features = _dissolve_by_owner(
                choropleth_features,
                colors=colors,
                display_by_tag=display_by_tag,
            )
            owner_feature_count = len(owner_features)
            owners_path = scenario_dir / "owners.geojson"
            _write_json(
                owners_path,
                _feature_collection(
                    name=f"owners_{scenario_id}",
                    profile_id=profile_id,
                    generated_at=generated_at,
                    features=owner_features,
                    extra_gpm={
                        "milestone": "M10",
                        "layer": "owners",
                        "pack_type": "atlas",
                        "scenario_id": scenario_id,
                        "paint_field": "owner",
                        "color_field": "owner_color",
                        "dissolve": "owner",
                    },
                ),
            )
            files_written.append(_rel(owners_path, pack_root))

        legend = _build_legend(
            scenario=scenario,
            records=records,
            colors=colors,
            display_by_tag=display_by_tag,
            generated_at=generated_at,
            profile_id=profile_id,
        )
        legend_path = scenario_dir / "legend.json"
        _write_json(legend_path, legend)
        files_written.append(_rel(legend_path, pack_root))

        tags_path = scenario_dir / "tags.csv"
        _write_tags_csv(tags_path, legend["tags"])
        files_written.append(_rel(tags_path, pack_root))

        ownership_csv = scenario_dir / "ownership.csv"
        ownership_json = scenario_dir / "ownership.json"
        countries_json = scenario_dir / "countries.json"
        _write_ownership_csv(ownership_csv, records, colors)
        _write_json(
            ownership_json,
            {
                "schema_version": ATLAS_SCHEMA_VERSION,
                "milestone": "M10",
                "scenario_id": scenario_id,
                "profile_id": profile_id,
                "era": scenario["era"],
                "start_date": scenario["start_date"],
                "end_date": scenario.get("end_date"),
                "generated_at": generated_at,
                "generator_version": __version__,
                "count": len(records),
                "records": [
                    {
                        **row,
                        "owner_color": colors.get(row["owner"], FALLBACK_FILL),
                        "controller_color": colors.get(row["controller"], FALLBACK_FILL),
                    }
                    for row in records
                ],
            },
        )
        _write_json(
            countries_json,
            {
                "schema_version": ATLAS_SCHEMA_VERSION,
                "milestone": "M10",
                "scenario_id": scenario_id,
                "generated_at": generated_at,
                "count": len(countries),
                "countries": [
                    {
                        **item,
                        "color": colors.get(item["tag"], FALLBACK_FILL),
                        "province_count": sum(
                            1 for row in records if row["owner"] == item["tag"]
                        ),
                    }
                    for item in countries
                ],
            },
        )
        files_written.extend(
            [
                _rel(ownership_csv, pack_root),
                _rel(ownership_json, pack_root),
                _rel(countries_json, pack_root),
            ]
        )

        scenario_manifest = {
            "schema_version": ATLAS_SCHEMA_VERSION,
            "milestone": "M10",
            "pack_type": "atlas-scenario",
            "scenario_id": scenario_id,
            "label": scenario["label"],
            "era": scenario["era"],
            "start_date": scenario["start_date"],
            "end_date": scenario.get("end_date"),
            "profile_id": profile_id,
            "generated_at": generated_at,
            "generator_version": __version__,
            "counts": {
                "ownership_rows": len(records),
                "choropleth_features": len(choropleth_features),
                "uncertainty_features": len(uncertainty_features),
                "owner_features": owner_feature_count,
                "legend_tags": len(legend["tags"]),
                "owner_tags": stats["owner_tag_count"],
                "country_rule_hits": stats["country_rule_hits"],
                "region_rule_hits": stats["region_rule_hits"],
                "province_override_hits": stats["province_override_hits"],
                "baseline_only": stats["baseline_only_count"],
            },
            "paint": {
                "field": "owner",
                "color_field": "owner_color",
                "fallback_color": FALLBACK_FILL,
                "disputed_outline": DISPUTED_OUTLINE,
            },
            "files": sorted(
                path.name
                for path in scenario_dir.iterdir()
                if path.is_file()
            ),
        }
        scenario_manifest_path = scenario_dir / "scenario_manifest.json"
        # Write after collecting final file list for this scenario.
        scenario_files = sorted(
            {
                "ownership_choropleth.geojson",
                "uncertainty.geojson",
                "legend.json",
                "tags.csv",
                "ownership.csv",
                "ownership.json",
                "countries.json",
                "scenario_manifest.json",
            }
            | ({"owners.geojson"} if include_owner_dissolve else set())
        )
        scenario_manifest["files"] = scenario_files
        _write_json(scenario_manifest_path, scenario_manifest)
        files_written.append(_rel(scenario_manifest_path, pack_root))

        ownership_row_total += len(records)
        legend_entry_total += len(legend["tags"])
        tag_ids.update(item["tag"] for item in legend["tags"])
        scenario_summaries.append(
            {
                "scenario_id": scenario_id,
                "era": scenario["era"],
                "start_date": scenario["start_date"],
                "ownership_rows": len(records),
                "legend_tags": len(legend["tags"]),
                "uncertainty_features": len(uncertainty_features),
            }
        )

    attribution_records = _build_attribution_records(land_features, files_written)
    # Append scenario-authoring notice when any scenario license lineage exists.
    for scenario_id in scenario_ids:
        try:
            scenario = load_scenario(scenario_id)
        except ScenarioError:
            continue
        for license_text in scenario.get("license_lineage") or []:
            if not isinstance(license_text, str) or not license_text.strip():
                continue
            attribution_records.append(
                {
                    "source_id": "scenario",
                    "title": f"Scenario {scenario_id}",
                    "license": license_text,
                    "attribution_text": license_text,
                    "url": "https://example.invalid/",
                    "required": True,
                    "downstream_outputs": [
                        path
                        for path in files_written
                        if path.startswith(f"scenarios/{scenario_id}/")
                    ],
                }
            )
    # Deduplicate by source_id|license.
    attribution_records = _dedupe_attribution(attribution_records)
    attribution_path = pack_root / "attribution.json"
    _write_json(
        attribution_path,
        {"schema_version": ATLAS_SCHEMA_VERSION, "records": attribution_records},
    )
    files_written.append(_rel(attribution_path, pack_root))

    readme_path = pack_root / "README.md"
    readme_path.write_text(
        _atlas_readme(
            profile_id=profile_id,
            scenario_ids=scenario_ids,
            include_base_geometry=include_base_geometry,
            include_owner_dissolve=include_owner_dissolve,
        ),
        encoding="utf-8",
    )
    files_written.append(_rel(readme_path, pack_root))

    files_written = sorted(set(files_written))
    manifest = {
        "schema_version": ATLAS_SCHEMA_VERSION,
        "milestone": "M10",
        "pack_type": "atlas",
        "profile_id": profile_id,
        "generated_at": generated_at,
        "generator_version": __version__,
        "scenarios": list(scenario_ids),
        "include_base_geometry": include_base_geometry,
        "include_owner_dissolve": include_owner_dissolve,
        "inputs": {"provinces": str(province_input)},
        "counts": {
            "provinces": len(land_features),
            "scenarios": len(scenario_ids),
            "scenario_ownership_rows": ownership_row_total,
            "unique_tags": len(tag_ids),
            "legend_entries": legend_entry_total,
            "attribution_records": len(attribution_records),
        },
        "scenario_summaries": scenario_summaries,
        "formats": {
            "geometry": ["GeoJSON"],
            "tables": ["CSV", "JSON"],
            "optional_future": ["PMTiles", "FlatGeobuf", "GeoParquet", "TopoJSON"],
        },
        "files": files_written,
        "notes": [
            "Atlas packs join scenario politics onto modern scaffold geometry for web maps.",
            "Colors are deterministic per tag (sha256 → HSL) and stable across rebuilds.",
            "Uncertainty layer flags disputed, foreign-controlled, and UNK-owned provinces.",
            "PMTiles / FlatGeobuf / GeoParquet are not generated in M10; consume GeoJSON or convert downstream.",
        ],
    }
    manifest_path = pack_root / "atlas_manifest.json"
    _write_json(manifest_path, manifest)
    if _rel(manifest_path, pack_root) not in files_written:
        files_written = sorted([*files_written, _rel(manifest_path, pack_root)])
        manifest["files"] = files_written
        _write_json(manifest_path, manifest)

    return AtlasExportResult(
        profile_id=profile_id,
        pack_type="atlas",
        output_dir=str(pack_root),
        atlas_manifest=str(manifest_path),
        province_count=len(land_features),
        scenario_ids=scenario_ids,
        scenario_ownership_row_count=ownership_row_total,
        tag_count=len(tag_ids),
        legend_entry_count=legend_entry_total,
        attribution_record_count=len(attribution_records),
        include_base_geometry=include_base_geometry,
        include_owner_dissolve=include_owner_dissolve,
        files_written=tuple(files_written),
    )


def tag_fill_color(tag: str) -> str:
    """Deterministic pastel-strong hex fill for a political tag."""
    if not tag or tag == "UNK":
        return UNKNOWN_FILL
    digest = hashlib.sha256(tag.encode("utf-8")).hexdigest()
    # Spread hue; keep mid saturation/lightness for map readability.
    hue = int(digest[0:2], 16) / 255.0
    sat = 0.48 + (int(digest[2:4], 16) / 255.0) * 0.28  # 0.48–0.76
    light = 0.40 + (int(digest[4:6], 16) / 255.0) * 0.16  # 0.40–0.56
    r, g, b = colorsys.hls_to_rgb(hue, light, sat)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


def _color_map_for_records(records: list[dict[str, Any]]) -> dict[str, str]:
    tags: set[str] = set()
    for row in records:
        tags.add(str(row["owner"]))
        tags.add(str(row["controller"]))
        for core in row.get("cores") or []:
            tags.add(str(core))
        for claim in row.get("claims") or []:
            tags.add(str(claim))
    return {tag: tag_fill_color(tag) for tag in tags}


def _build_choropleth_features(
    land_features: list[dict[str, Any]],
    ownership_by_id: dict[str, dict[str, Any]],
    colors: dict[str, str],
) -> list[dict[str, Any]]:
    features: list[dict[str, Any]] = []
    for feature in land_features:
        props = feature.get("properties") or {}
        if not isinstance(props, dict):
            continue
        province_id = props.get("province_id")
        if not isinstance(province_id, str):
            continue
        row = ownership_by_id.get(province_id)
        if row is None:
            continue
        owner = str(row["owner"])
        controller = str(row["controller"])
        joined = {
            **{key: props.get(key) for key in (
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
            )},
            "scenario_id": row["scenario_id"],
            "start_date": row["start_date"],
            "end_date": row["end_date"],
            "owner": owner,
            "controller": controller,
            "cores": list(row.get("cores") or []),
            "claims": list(row.get("claims") or []),
            "culture": row.get("culture"),
            "religion": row.get("religion"),
            "disputed": bool(row.get("disputed")),
            "assignment_source": row.get("assignment_source"),
            "notes": row.get("notes"),
            "owner_color": colors.get(owner, FALLBACK_FILL),
            "controller_color": colors.get(controller, FALLBACK_FILL),
            "uncertain": _is_uncertain(
                {
                    "owner": owner,
                    "controller": controller,
                    "disputed": bool(row.get("disputed")),
                }
            ),
        }
        features.append(
            {
                "type": "Feature",
                "geometry": feature.get("geometry"),
                "properties": joined,
            }
        )
    features.sort(key=lambda item: str((item.get("properties") or {}).get("province_id") or ""))
    return features


def _is_uncertain(properties: dict[str, Any]) -> bool:
    owner = properties.get("owner")
    controller = properties.get("controller")
    if properties.get("disputed") is True:
        return True
    if owner == "UNK":
        return True
    if owner is not None and controller is not None and owner != controller:
        return True
    return False


def _dissolve_by_owner(
    choropleth_features: list[dict[str, Any]],
    *,
    colors: dict[str, str],
    display_by_tag: dict[str, str],
) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for feature in choropleth_features:
        props = feature.get("properties") or {}
        owner = props.get("owner")
        if not isinstance(owner, str) or not owner:
            continue
        groups[owner].append(feature)

    dissolved: list[dict[str, Any]] = []
    for owner in sorted(groups):
        members = groups[owner]
        geometry, area_sq_km = _union_geometries(members)
        province_ids = sorted(
            {
                str(member["properties"]["province_id"])
                for member in members
                if isinstance(member.get("properties"), dict)
                and isinstance(member["properties"].get("province_id"), str)
            }
        )
        disputed_count = sum(
            1
            for member in members
            if isinstance(member.get("properties"), dict)
            and member["properties"].get("disputed") is True
        )
        dissolved.append(
            {
                "type": "Feature",
                "geometry": geometry,
                "properties": {
                    "owner": owner,
                    "display_name": display_by_tag.get(owner, owner),
                    "owner_color": colors.get(owner, FALLBACK_FILL),
                    "province_count": len(province_ids),
                    "province_ids": province_ids,
                    "area_sq_km": round(area_sq_km, 3),
                    "disputed_province_count": disputed_count,
                },
            }
        )
    return dissolved


def _union_geometries(
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
        # Approximate planar area in deg² → rough km² near equator is fine for summaries.
        area_sq_km = float(merged.area) * (111.32**2)
        return mapping(merged), area_sq_km
    except (ShapelyError, TypeError, ValueError):
        return None, 0.0


def _build_legend(
    *,
    scenario: dict[str, Any],
    records: list[dict[str, Any]],
    colors: dict[str, str],
    display_by_tag: dict[str, str],
    generated_at: str,
    profile_id: str,
) -> dict[str, Any]:
    owner_counts: dict[str, int] = defaultdict(int)
    controller_counts: dict[str, int] = defaultdict(int)
    for row in records:
        owner_counts[str(row["owner"])] += 1
        controller_counts[str(row["controller"])] += 1

    tags: list[dict[str, Any]] = []
    all_tags = sorted(set(owner_counts) | set(controller_counts) | set(colors))
    for tag in all_tags:
        tags.append(
            {
                "tag": tag,
                "display_name": display_by_tag.get(tag, tag),
                "color": colors.get(tag, FALLBACK_FILL),
                "fill_color": colors.get(tag, FALLBACK_FILL),
                "owner_province_count": owner_counts.get(tag, 0),
                "controller_province_count": controller_counts.get(tag, 0),
                "roles": _tag_roles(tag, owner_counts, controller_counts),
            }
        )
    tags.sort(key=lambda item: (-item["owner_province_count"], item["tag"]))

    # MapLibre-friendly match expression for fill-color.
    match_expr: list[Any] = ["match", ["get", "owner"]]
    for item in tags:
        if item["owner_province_count"] > 0:
            match_expr.extend([item["tag"], item["fill_color"]])
    match_expr.append(FALLBACK_FILL)

    return {
        "schema_version": ATLAS_SCHEMA_VERSION,
        "milestone": "M10",
        "scenario_id": scenario["scenario_id"],
        "label": scenario["label"],
        "era": scenario["era"],
        "start_date": scenario["start_date"],
        "end_date": scenario.get("end_date"),
        "profile_id": profile_id,
        "generated_at": generated_at,
        "generator_version": __version__,
        "paint_field": "owner",
        "color_field": "owner_color",
        "fallback_color": FALLBACK_FILL,
        "disputed_outline_color": DISPUTED_OUTLINE,
        "count": len(tags),
        "tags": tags,
        "styles": {
            "maplibre_fill_color": match_expr,
            "maplibre_fill_color_property": ["get", "owner_color"],
            "css_custom_properties": {
                f"--tag-{_css_safe(item['tag'])}": item["fill_color"] for item in tags
            },
        },
    }


def _tag_roles(
    tag: str,
    owner_counts: dict[str, int],
    controller_counts: dict[str, int],
) -> list[str]:
    roles: list[str] = []
    if owner_counts.get(tag, 0) > 0:
        roles.append("owner")
    if controller_counts.get(tag, 0) > 0:
        roles.append("controller")
    return roles or ["referenced"]


def _css_safe(tag: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in tag)


def _country_catalog(
    scenario: dict[str, Any],
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    declared = scenario.get("countries") if isinstance(scenario.get("countries"), dict) else {}
    tags: set[str] = set()
    for record in records:
        tags.add(str(record["owner"]))
        tags.add(str(record["controller"]))
        tags.update(str(item) for item in record.get("cores") or [])
        tags.update(str(item) for item in record.get("claims") or [])
    countries: list[dict[str, Any]] = []
    for tag in sorted(tags):
        meta = declared.get(tag) if isinstance(declared.get(tag), dict) else {}
        display = meta.get("display_name") if isinstance(meta, dict) else None
        if not isinstance(display, str) or not display.strip():
            display = tag
        entry: dict[str, Any] = {"tag": tag, "display_name": display}
        if isinstance(meta, dict) and meta.get("notes"):
            entry["notes"] = meta["notes"]
        countries.append(entry)
    return countries


def _land_features(features: list[Any]) -> list[dict[str, Any]]:
    land: list[dict[str, Any]] = []
    for feature in features:
        if not isinstance(feature, dict):
            continue
        props = feature.get("properties")
        if not isinstance(props, dict):
            continue
        if props.get("kind", "land") not in (None, "land"):
            continue
        land.append(feature)
    return land


def _load_feature_collection(path: Path, label: str) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ExportError(f"Invalid {label} GeoJSON at {path}: {exc}") from exc
    except OSError as exc:
        raise ExportError(f"Unable to read {label} GeoJSON at {path}: {exc}") from exc
    if not isinstance(document, dict) or document.get("type") != "FeatureCollection":
        raise ExportError(f"{label} input must be a GeoJSON FeatureCollection: {path}")
    features = document.get("features")
    if not isinstance(features, list):
        raise ExportError(f"{label} FeatureCollection is missing a features array: {path}")
    return document


def _feature_collection(
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
            "schema_version": ATLAS_SCHEMA_VERSION,
            "milestone": "M10",
            "profile_id": profile_id,
            "generated_at": generated_at,
            "generator_version": __version__,
            "feature_count": len(features),
            **extra_gpm,
        },
        "features": features,
    }


def _write_province_table(path: Path, land_features: list[dict[str, Any]]) -> None:
    rows: list[dict[str, Any]] = []
    for feature in land_features:
        props = feature.get("properties") or {}
        if not isinstance(props, dict):
            continue
        rows.append({field: props.get(field) for field in PROVINCE_TABLE_FIELDS})
    rows.sort(key=lambda row: str(row.get("province_id") or ""))
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(PROVINCE_TABLE_FIELDS))
        writer.writeheader()
        for row in rows:
            serialized = {
                field: "" if row.get(field) is None else row.get(field)
                for field in PROVINCE_TABLE_FIELDS
            }
            for key in ("coastal", "island"):
                value = row.get(key)
                if isinstance(value, bool):
                    serialized[key] = "true" if value else "false"
            writer.writerow(serialized)


def _write_ownership_csv(
    path: Path,
    records: list[dict[str, Any]],
    colors: dict[str, str],
) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(OWNERSHIP_TABLE_FIELDS))
        writer.writeheader()
        for row in records:
            writer.writerow(
                {
                    "province_id": row["province_id"],
                    "scenario_id": row["scenario_id"],
                    "start_date": row["start_date"],
                    "end_date": "" if row.get("end_date") is None else row["end_date"],
                    "owner": row["owner"],
                    "controller": row["controller"],
                    "cores": json.dumps(row.get("cores") or [], ensure_ascii=False),
                    "claims": json.dumps(row.get("claims") or [], ensure_ascii=False),
                    "culture": "" if row.get("culture") is None else row["culture"],
                    "religion": "" if row.get("religion") is None else row["religion"],
                    "disputed": "true" if row.get("disputed") else "false",
                    "assignment_source": row.get("assignment_source") or "",
                    "parent_country_id": row.get("parent_country_id") or "",
                    "parent_region_id": row.get("parent_region_id") or "",
                    "display_name": row.get("display_name") or "",
                    "notes": row.get("notes") or "",
                    "owner_color": colors.get(row["owner"], FALLBACK_FILL),
                    "controller_color": colors.get(row["controller"], FALLBACK_FILL),
                }
            )


def _write_tags_csv(path: Path, tags: list[dict[str, Any]]) -> None:
    fieldnames = [
        "tag",
        "display_name",
        "color",
        "fill_color",
        "owner_province_count",
        "controller_province_count",
        "roles",
    ]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for item in tags:
            writer.writerow(
                {
                    "tag": item["tag"],
                    "display_name": item["display_name"],
                    "color": item["color"],
                    "fill_color": item["fill_color"],
                    "owner_province_count": item["owner_province_count"],
                    "controller_province_count": item["controller_province_count"],
                    "roles": json.dumps(item.get("roles") or [], ensure_ascii=False),
                }
            )


def _dedupe_attribution(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: dict[str, dict[str, Any]] = {}
    for record in records:
        key = f"{record.get('source_id')}|{record.get('license')}"
        if key not in seen:
            seen[key] = dict(record)
            continue
        existing = seen[key]
        outputs = set(existing.get("downstream_outputs") or [])
        outputs.update(record.get("downstream_outputs") or [])
        existing["downstream_outputs"] = sorted(outputs)
    return [seen[key] for key in sorted(seen)]


def _atlas_readme(
    *,
    profile_id: str,
    scenario_ids: tuple[str, ...],
    include_base_geometry: bool,
    include_owner_dissolve: bool,
) -> str:
    scenario_rows = "\n".join(
        f"| `scenarios/{sid}/` | Choropleth, legend, ownership tables for `{sid}` |"
        for sid in scenario_ids
    )
    base_row = (
        "| `geojson/provinces.geojson` | Base land province geometry |\n"
        if include_base_geometry
        else ""
    )
    owner_note = (
        "Each scenario also includes `owners.geojson` (dissolved owner multipolygons)."
        if include_owner_dissolve
        else "Owner dissolve was disabled for this pack."
    )
    return f"""# GPM atlas / SaaS pack: `{profile_id}`

Web- and explanation-oriented package: scenario politics joined to geometry,
tag legends with stable colors, and flat tables for maps or APIs.

## Contents

| Path | Purpose |
| --- | --- |
{base_row}| `tables/provinces.csv` | Land province attributes for joins |
| `attribution.json` | License notices for redistribution |
| `atlas_manifest.json` | Pack metadata and file inventory |
{scenario_rows}

### Per-scenario files

| Path | Purpose |
| --- | --- |
| `ownership_choropleth.geojson` | Province polygons with owner/controller + `owner_color` |
| `owners.geojson` | Owner-dissolved multipolygons (optional) |
| `uncertainty.geojson` | Disputed, foreign-controlled, or UNK-owned provinces |
| `legend.json` | Tag catalog, colors, MapLibre style helpers |
| `tags.csv` | Flat legend for tables/UI |
| `ownership.csv` / `ownership.json` | API-friendly ownership rows (+ colors) |
| `countries.json` | Tags with display names and fill colors |

{owner_note}

## How to consume (MapLibre / web)

1. Load `scenarios/<id>/ownership_choropleth.geojson` as a GeoJSON source.
2. Paint fills with `["get", "owner_color"]`, or use `legend.json` →
   `styles.maplibre_fill_color` match expression.
3. Overlay `uncertainty.geojson` with a red outline for contested provinces.
4. Render the legend from `legend.json` / `tags.csv`.
5. Join `tables/provinces.csv` or scenario `ownership.csv` for non-map UIs.
6. Keep `attribution.json` with any redistributed dataset.

## Notes

- Geometry is the modern open-geodata scaffold unless a later era geometry pack
  is used. Politics are scenario overlays (see M8).
- Colors are deterministic per tag (`sha256` → HSL) and stable across rebuilds.
- Optional tile formats (PMTiles, FlatGeobuf, GeoParquet) are not produced by
  M10; convert from GeoJSON/CSV downstream if needed.

Generated by Global Province Map Template (M10 atlas face).
"""


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
