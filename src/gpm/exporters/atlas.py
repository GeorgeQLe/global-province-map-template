"""Atlas / SaaS export face: ownership + culture/religion paint, legends, web tables.

M10 delivered owner choropleths; M18 adds culture/religion identity paint.
"""

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

OWNERSHIP_TABLE_FIELDS_BASE = (
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
OWNERSHIP_TABLE_FIELDS = (
    *OWNERSHIP_TABLE_FIELDS_BASE,
    "culture_color",
    "religion_color",
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
    include_identity_paint: bool
    include_identity_dissolve: bool
    include_tiles: bool
    unique_culture_count: int
    unique_religion_count: int
    tile_file_count: int
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
    include_identity_paint: bool = True,
    include_identity_dissolve: bool = True,
    include_tiles: bool = False,
    tile_min_zoom: int = 0,
    tile_max_zoom: int = 8,
    prefer_tippecanoe: bool = True,
) -> AtlasExportResult:
    """Write an atlas / SaaS package under exports/atlas/<profile_id>/."""
    if not include_identity_paint:
        include_identity_dissolve = False
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
    culture_ids: set[str] = set()
    religion_ids: set[str] = set()

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
                    "milestone": "M18",
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
        culture_colors = (
            _identity_color_map(records, "culture") if include_identity_paint else {}
        )
        religion_colors = (
            _identity_color_map(records, "religion") if include_identity_paint else {}
        )
        countries = _country_catalog(scenario, records)
        display_by_tag = {item["tag"]: item["display_name"] for item in countries}

        culture_assigned = sum(
            1
            for row in records
            if row.get("culture") is not None and str(row.get("culture")).strip()
        )
        religion_assigned = sum(
            1
            for row in records
            if row.get("religion") is not None and str(row.get("religion")).strip()
        )
        culture_unassigned = len(records) - culture_assigned
        religion_unassigned = len(records) - religion_assigned
        unique_cultures = set(culture_colors)
        unique_religions = set(religion_colors)
        culture_ids.update(unique_cultures)
        religion_ids.update(unique_religions)

        choropleth_features = _build_choropleth_features(
            land_features,
            ownership_by_id,
            colors,
            culture_colors=culture_colors if include_identity_paint else None,
            religion_colors=religion_colors if include_identity_paint else None,
            include_identity_paint=include_identity_paint,
        )
        paint_fields = ["owner", "controller"]
        color_fields = {
            "owner": "owner_color",
            "controller": "controller_color",
        }
        if include_identity_paint:
            paint_fields.extend(["culture", "religion"])
            color_fields["culture"] = "culture_color"
            color_fields["religion"] = "religion_color"

        choropleth_path = scenario_dir / "ownership_choropleth.geojson"
        _write_json(
            choropleth_path,
            _feature_collection(
                name=f"ownership_choropleth_{scenario_id}",
                profile_id=profile_id,
                generated_at=generated_at,
                features=choropleth_features,
                extra_gpm={
                    "milestone": "M18",
                    "layer": "ownership_choropleth",
                    "pack_type": "atlas",
                    "scenario_id": scenario_id,
                    "era": scenario["era"],
                    "start_date": scenario["start_date"],
                    "end_date": scenario.get("end_date"),
                    "paint_field": "owner",
                    "color_field": "owner_color",
                    "paint_fields": paint_fields,
                    "color_fields": color_fields,
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
                    "milestone": "M18",
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
            owner_features = _dissolve_by_key(
                choropleth_features,
                key="owner",
                color_field="owner_color",
                colors=colors,
                display_by_id=display_by_tag,
                include_unassigned=False,
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
                        "milestone": "M18",
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

        culture_feature_count = 0
        religion_feature_count = 0
        if include_identity_paint:
            culture_legend = _build_identity_legend(
                field="culture",
                scenario=scenario,
                records=records,
                colors=culture_colors,
                generated_at=generated_at,
                profile_id=profile_id,
            )
            religion_legend = _build_identity_legend(
                field="religion",
                scenario=scenario,
                records=records,
                colors=religion_colors,
                generated_at=generated_at,
                profile_id=profile_id,
            )
            culture_legend_path = scenario_dir / "culture_legend.json"
            religion_legend_path = scenario_dir / "religion_legend.json"
            _write_json(culture_legend_path, culture_legend)
            _write_json(religion_legend_path, religion_legend)
            files_written.append(_rel(culture_legend_path, pack_root))
            files_written.append(_rel(religion_legend_path, pack_root))

            cultures_csv = scenario_dir / "cultures.csv"
            religions_csv = scenario_dir / "religions.csv"
            _write_identity_csv(cultures_csv, culture_legend["entries"])
            _write_identity_csv(religions_csv, religion_legend["entries"])
            files_written.append(_rel(cultures_csv, pack_root))
            files_written.append(_rel(religions_csv, pack_root))

            if include_identity_dissolve:
                culture_features = _dissolve_by_key(
                    choropleth_features,
                    key="culture",
                    color_field="culture_color",
                    colors=culture_colors,
                    include_unassigned=True,
                )
                religion_features = _dissolve_by_key(
                    choropleth_features,
                    key="religion",
                    color_field="religion_color",
                    colors=religion_colors,
                    include_unassigned=True,
                )
                culture_feature_count = len(culture_features)
                religion_feature_count = len(religion_features)
                cultures_path = scenario_dir / "cultures.geojson"
                religions_path = scenario_dir / "religions.geojson"
                _write_json(
                    cultures_path,
                    _feature_collection(
                        name=f"cultures_{scenario_id}",
                        profile_id=profile_id,
                        generated_at=generated_at,
                        features=culture_features,
                        extra_gpm={
                            "milestone": "M18",
                            "layer": "cultures",
                            "pack_type": "atlas",
                            "scenario_id": scenario_id,
                            "paint_field": "culture",
                            "color_field": "culture_color",
                            "dissolve": "culture",
                        },
                    ),
                )
                _write_json(
                    religions_path,
                    _feature_collection(
                        name=f"religions_{scenario_id}",
                        profile_id=profile_id,
                        generated_at=generated_at,
                        features=religion_features,
                        extra_gpm={
                            "milestone": "M18",
                            "layer": "religions",
                            "pack_type": "atlas",
                            "scenario_id": scenario_id,
                            "paint_field": "religion",
                            "color_field": "religion_color",
                            "dissolve": "religion",
                        },
                    ),
                )
                files_written.append(_rel(cultures_path, pack_root))
                files_written.append(_rel(religions_path, pack_root))

        ownership_csv = scenario_dir / "ownership.csv"
        ownership_json = scenario_dir / "ownership.json"
        countries_json = scenario_dir / "countries.json"
        _write_ownership_csv(
            ownership_csv,
            records,
            colors,
            culture_colors=culture_colors if include_identity_paint else None,
            religion_colors=religion_colors if include_identity_paint else None,
            include_identity_paint=include_identity_paint,
        )
        ownership_records_out = []
        for row in records:
            enriched = {
                **row,
                "owner_color": colors.get(row["owner"], FALLBACK_FILL),
                "controller_color": colors.get(row["controller"], FALLBACK_FILL),
            }
            if include_identity_paint:
                enriched["culture_color"] = identity_fill_color(row.get("culture"))
                enriched["religion_color"] = identity_fill_color(row.get("religion"))
            ownership_records_out.append(enriched)
        _write_json(
            ownership_json,
            {
                "schema_version": ATLAS_SCHEMA_VERSION,
                "milestone": "M18",
                "scenario_id": scenario_id,
                "profile_id": profile_id,
                "era": scenario["era"],
                "start_date": scenario["start_date"],
                "end_date": scenario.get("end_date"),
                "generated_at": generated_at,
                "generator_version": __version__,
                "count": len(records),
                "records": ownership_records_out,
            },
        )
        _write_json(
            countries_json,
            {
                "schema_version": ATLAS_SCHEMA_VERSION,
                "milestone": "M18",
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

        paint_modes = [
            {
                "field": "owner",
                "color_field": "owner_color",
                "legend": "legend.json",
                "dissolve": "owners.geojson" if include_owner_dissolve else None,
            },
            {
                "field": "controller",
                "color_field": "controller_color",
                "legend": None,
                "dissolve": None,
                "note": (
                    "Colors on choropleth only; no dedicated controller legend "
                    "file in M10/M18"
                ),
            },
        ]
        if include_identity_paint:
            paint_modes.append(
                {
                    "field": "culture",
                    "color_field": "culture_color",
                    "legend": "culture_legend.json",
                    "dissolve": (
                        "cultures.geojson" if include_identity_dissolve else None
                    ),
                }
            )
            paint_modes.append(
                {
                    "field": "religion",
                    "color_field": "religion_color",
                    "legend": "religion_legend.json",
                    "dissolve": (
                        "religions.geojson" if include_identity_dissolve else None
                    ),
                }
            )

        counts = {
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
        }
        if include_identity_paint:
            counts.update(
                {
                    "unique_cultures": len(unique_cultures),
                    "unique_religions": len(unique_religions),
                    "culture_assigned": culture_assigned,
                    "culture_unassigned": culture_unassigned,
                    "religion_assigned": religion_assigned,
                    "religion_unassigned": religion_unassigned,
                    "culture_features": culture_feature_count,
                    "religion_features": religion_feature_count,
                }
            )

        scenario_files: set[str] = {
            "ownership_choropleth.geojson",
            "uncertainty.geojson",
            "legend.json",
            "tags.csv",
            "ownership.csv",
            "ownership.json",
            "countries.json",
            "scenario_manifest.json",
        }
        if include_owner_dissolve:
            scenario_files.add("owners.geojson")
        if include_identity_paint:
            scenario_files.update(
                {
                    "culture_legend.json",
                    "religion_legend.json",
                    "cultures.csv",
                    "religions.csv",
                }
            )
        if include_identity_paint and include_identity_dissolve:
            scenario_files.update({"cultures.geojson", "religions.geojson"})

        scenario_manifest = {
            "schema_version": ATLAS_SCHEMA_VERSION,
            "milestone": "M18",
            "pack_type": "atlas-scenario",
            "scenario_id": scenario_id,
            "label": scenario["label"],
            "era": scenario["era"],
            "start_date": scenario["start_date"],
            "end_date": scenario.get("end_date"),
            "profile_id": profile_id,
            "generated_at": generated_at,
            "generator_version": __version__,
            "counts": counts,
            "paint": {
                "field": "owner",
                "color_field": "owner_color",
                "default_field": "owner",
                "default_color_field": "owner_color",
                "fallback_color": FALLBACK_FILL,
                "unassigned_color": UNKNOWN_FILL,
                "disputed_outline": DISPUTED_OUTLINE,
                "modes": paint_modes,
            },
            "files": sorted(scenario_files),
        }
        scenario_manifest_path = scenario_dir / "scenario_manifest.json"
        _write_json(scenario_manifest_path, scenario_manifest)
        files_written.append(_rel(scenario_manifest_path, pack_root))

        ownership_row_total += len(records)
        legend_entry_total += len(legend["tags"])
        tag_ids.update(item["tag"] for item in legend["tags"])
        summary = {
            "scenario_id": scenario_id,
            "era": scenario["era"],
            "start_date": scenario["start_date"],
            "ownership_rows": len(records),
            "legend_tags": len(legend["tags"]),
            "uncertainty_features": len(uncertainty_features),
        }
        if include_identity_paint:
            summary.update(
                {
                    "unique_cultures": len(unique_cultures),
                    "unique_religions": len(unique_religions),
                    "culture_assigned": culture_assigned,
                    "culture_unassigned": culture_unassigned,
                    "religion_assigned": religion_assigned,
                    "religion_unassigned": religion_unassigned,
                }
            )
        scenario_summaries.append(summary)

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
            include_identity_paint=include_identity_paint,
            include_identity_dissolve=include_identity_dissolve,
        ),
        encoding="utf-8",
    )
    files_written.append(_rel(readme_path, pack_root))

    files_written = sorted(set(files_written))
    tile_file_count = 0
    if include_tiles:
        from gpm.tiles import TileBuildError, export_tiles_from_atlas

        try:
            tile_results = export_tiles_from_atlas(
                pack_root,
                scenarios=scenario_ids,
                min_zoom=tile_min_zoom,
                max_zoom=tile_max_zoom,
                prefer_tippecanoe=prefer_tippecanoe,
                include_base=include_base_geometry,
            )
        except TileBuildError as exc:
            raise ExportError(str(exc)) from exc
        for tile_result in tile_results:
            for name in tile_result.files_written:
                # Tile files land under scenarios/<id>/ or tiles/.
                candidate = Path(tile_result.output_path).parent / name
                rel = _rel(candidate, pack_root)
                if rel not in files_written:
                    files_written.append(rel)
                tile_file_count += 1 if name.endswith(".pmtiles") else 0

    notes = [
        "Atlas packs join scenario politics onto modern scaffold geometry for web maps.",
        "Colors are deterministic per tag (sha256 → HSL) and stable across rebuilds.",
        "Uncertainty layer flags disputed, foreign-controlled, and UNK-owned provinces.",
        "Supersedes M10 atlas face; culture/religion identity paint added in M18.",
        "PMTiles vector tiles available via --tiles (M19) or gpm export tiles.",
    ]
    if include_identity_paint:
        notes.extend(
            [
                "Culture/religion paint is curated scenario hints, not Paradox-grade ethnography.",
                "Unassigned culture/religion provinces use unassigned gray (#8a8a8a).",
                "Prefer property-based fill (['get','culture_color']) over large match expressions for full packs.",
            ]
        )
    if include_tiles:
        notes.append(
            "PMTiles archives use Mapbox Vector Tiles (MVT); load with MapLibre + pmtiles protocol."
        )
    geometry_formats = ["GeoJSON"]
    optional_future = ["FlatGeobuf", "GeoParquet", "TopoJSON"]
    if include_tiles:
        geometry_formats.append("PMTiles")
    else:
        optional_future = ["PMTiles", *optional_future]
    manifest = {
        "schema_version": ATLAS_SCHEMA_VERSION,
        "milestone": "M19" if include_tiles else "M18",
        "pack_type": "atlas",
        "profile_id": profile_id,
        "generated_at": generated_at,
        "generator_version": __version__,
        "scenarios": list(scenario_ids),
        "include_base_geometry": include_base_geometry,
        "include_owner_dissolve": include_owner_dissolve,
        "include_identity_paint": include_identity_paint,
        "include_identity_dissolve": include_identity_dissolve,
        "include_tiles": include_tiles,
        "inputs": {"provinces": str(province_input)},
        "counts": {
            "provinces": len(land_features),
            "scenarios": len(scenario_ids),
            "scenario_ownership_rows": ownership_row_total,
            "unique_tags": len(tag_ids),
            "legend_entries": legend_entry_total,
            "unique_cultures": len(culture_ids),
            "unique_religions": len(religion_ids),
            "attribution_records": len(attribution_records),
            "tile_files": tile_file_count,
        },
        "scenario_summaries": scenario_summaries,
        "formats": {
            "geometry": geometry_formats,
            "tables": ["CSV", "JSON"],
            "optional_future": optional_future,
        },
        "files": files_written,
        "notes": notes,
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
        include_identity_paint=include_identity_paint,
        include_identity_dissolve=include_identity_dissolve,
        include_tiles=include_tiles,
        unique_culture_count=len(culture_ids),
        unique_religion_count=len(religion_ids),
        tile_file_count=tile_file_count,
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


def _area_fill_color(area_id: Any) -> str:
    """Deterministic fill for the hierarchy paint mode (hash color per area)."""
    if not isinstance(area_id, str) or not area_id:
        return UNKNOWN_FILL
    return tag_fill_color(area_id)


def identity_fill_color(value: str | None) -> str:
    """Deterministic fill for culture or religion; null/empty → UNKNOWN_FILL."""
    if value is None:
        return UNKNOWN_FILL
    text = str(value).strip()
    if not text:
        return UNKNOWN_FILL
    return tag_fill_color(text)


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


def _identity_color_map(records: list[dict[str, Any]], field: str) -> dict[str, str]:
    """Build color map for culture or religion values (non-null only)."""
    values: set[str] = set()
    for row in records:
        raw = row.get(field)
        if raw is None:
            continue
        text = str(raw).strip()
        if text:
            values.add(text)
    return {value: tag_fill_color(value) for value in values}


def _build_choropleth_features(
    land_features: list[dict[str, Any]],
    ownership_by_id: dict[str, dict[str, Any]],
    colors: dict[str, str],
    *,
    culture_colors: dict[str, str] | None = None,
    religion_colors: dict[str, str] | None = None,
    include_identity_paint: bool = False,
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
                "parent_area_id",
                "parent_geo_region_id",
                "parent_superregion_id",
                "area_sq_km",
                "estimated_population",
                "terrain_class",
                "coastal",
                "island",
            )},
            "area_color": _area_fill_color(props.get("parent_area_id")),
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
        if include_identity_paint:
            culture_val = row.get("culture")
            religion_val = row.get("religion")
            culture_key = (
                str(culture_val).strip()
                if culture_val is not None and str(culture_val).strip()
                else None
            )
            religion_key = (
                str(religion_val).strip()
                if religion_val is not None and str(religion_val).strip()
                else None
            )
            c_map = culture_colors or {}
            r_map = religion_colors or {}
            joined["culture_color"] = (
                c_map.get(culture_key, UNKNOWN_FILL) if culture_key else UNKNOWN_FILL
            )
            joined["religion_color"] = (
                r_map.get(religion_key, UNKNOWN_FILL) if religion_key else UNKNOWN_FILL
            )
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
    """Owner dissolve — skips empty owners (M10 BC)."""
    return _dissolve_by_key(
        choropleth_features,
        key="owner",
        color_field="owner_color",
        colors=colors,
        display_by_id=display_by_tag,
        include_unassigned=False,
    )


def _dissolve_by_key(
    choropleth_features: list[dict[str, Any]],
    *,
    key: str,
    color_field: str,
    colors: dict[str, str],
    display_by_id: dict[str, str] | None = None,
    include_unassigned: bool = False,
) -> list[dict[str, Any]]:
    """Dissolve choropleth features by an ownership or identity key."""
    groups: dict[str | None, list[dict[str, Any]]] = defaultdict(list)
    for feature in choropleth_features:
        props = feature.get("properties") or {}
        if not isinstance(props, dict):
            continue
        raw = props.get(key)
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            group_key: str | None = None
        else:
            group_key = str(raw).strip()
        if group_key is None and not include_unassigned:
            continue
        groups[group_key].append(feature)

    display = display_by_id or {}
    dissolved: list[dict[str, Any]] = []
    # Assigned groups first (sorted), unassigned last when present.
    ordered_keys = sorted(k for k in groups if k is not None)
    if None in groups:
        ordered_keys.append(None)

    for group_key in ordered_keys:
        members = groups[group_key]
        geometry, area_sq_km = _union_geometries(members)
        province_ids = sorted(
            {
                str(member["properties"]["province_id"])
                for member in members
                if isinstance(member.get("properties"), dict)
                and isinstance(member["properties"].get("province_id"), str)
            }
        )
        is_unassigned = group_key is None
        if is_unassigned:
            props_out: dict[str, Any] = {
                key: None,
                "is_unassigned": True,
                "display_name": "unassigned",
                color_field: UNKNOWN_FILL,
                "province_count": len(province_ids),
                "province_ids": province_ids,
                "area_sq_km": round(area_sq_km, 3),
            }
        else:
            props_out = {
                key: group_key,
                "is_unassigned": False,
                "display_name": display.get(group_key, group_key),
                color_field: colors.get(group_key, FALLBACK_FILL if key == "owner" else UNKNOWN_FILL),
                "province_count": len(province_ids),
                "province_ids": province_ids,
                "area_sq_km": round(area_sq_km, 3),
            }
            if key == "owner":
                disputed_count = sum(
                    1
                    for member in members
                    if isinstance(member.get("properties"), dict)
                    and member["properties"].get("disputed") is True
                )
                props_out["disputed_province_count"] = disputed_count
        dissolved.append(
            {
                "type": "Feature",
                "geometry": geometry,
                "properties": props_out,
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
        "milestone": "M18",
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


def _build_identity_legend(
    *,
    field: str,
    scenario: dict[str, Any],
    records: list[dict[str, Any]],
    colors: dict[str, str],
    generated_at: str,
    profile_id: str,
) -> dict[str, Any]:
    """Build culture or religion legend with coverage counts and MapLibre helpers."""
    if field not in {"culture", "religion"}:
        raise ExportError(f"Identity legend field must be culture or religion, got {field}")
    color_field = f"{field}_color"
    counts: dict[str, int] = defaultdict(int)
    unassigned = 0
    for row in records:
        raw = row.get(field)
        if raw is None or not str(raw).strip():
            unassigned += 1
            continue
        counts[str(raw).strip()] += 1

    entries: list[dict[str, Any]] = []
    for identity_id in sorted(counts, key=lambda item: (-counts[item], item)):
        fill = colors.get(identity_id, tag_fill_color(identity_id))
        entries.append(
            {
                "id": identity_id,
                "display_name": identity_id,
                "color": fill,
                "fill_color": fill,
                "province_count": counts[identity_id],
            }
        )

    match_expr: list[Any] = ["match", ["get", field]]
    for item in entries:
        match_expr.extend([item["id"], item["fill_color"]])
    match_expr.append(UNKNOWN_FILL)

    css_prefix = "culture" if field == "culture" else "religion"
    return {
        "schema_version": ATLAS_SCHEMA_VERSION,
        "milestone": "M18",
        "scenario_id": scenario["scenario_id"],
        "label": scenario["label"],
        "era": scenario["era"],
        "start_date": scenario["start_date"],
        "end_date": scenario.get("end_date"),
        "profile_id": profile_id,
        "generated_at": generated_at,
        "generator_version": __version__,
        "paint_field": field,
        "color_field": color_field,
        "fallback_color": FALLBACK_FILL,
        "unassigned_color": UNKNOWN_FILL,
        "unassigned_province_count": unassigned,
        "assigned_province_count": len(records) - unassigned,
        "count": len(entries),
        "entries": entries,
        "styles": {
            "maplibre_fill_color": match_expr,
            "maplibre_fill_color_property": ["get", color_field],
            "css_custom_properties": {
                f"--{css_prefix}-{_css_safe(item['id'])}": item["fill_color"]
                for item in entries
            },
        },
    }


def _write_identity_csv(path: Path, entries: list[dict[str, Any]]) -> None:
    fieldnames = ["id", "display_name", "color", "fill_color", "province_count"]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for item in entries:
            writer.writerow(
                {
                    "id": item["id"],
                    "display_name": item["display_name"],
                    "color": item["color"],
                    "fill_color": item["fill_color"],
                    "province_count": item["province_count"],
                }
            )


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
            "milestone": "M18",
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
    *,
    culture_colors: dict[str, str] | None = None,
    religion_colors: dict[str, str] | None = None,
    include_identity_paint: bool = True,
) -> None:
    fields = (
        list(OWNERSHIP_TABLE_FIELDS)
        if include_identity_paint
        else list(OWNERSHIP_TABLE_FIELDS_BASE)
    )
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for row in records:
            out = {
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
            if include_identity_paint:
                out["culture_color"] = identity_fill_color(row.get("culture"))
                out["religion_color"] = identity_fill_color(row.get("religion"))
            writer.writerow(out)


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
    include_identity_paint: bool = True,
    include_identity_dissolve: bool = True,
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
    if include_identity_paint:
        identity_rows = (
            "| `culture_legend.json` / `cultures.csv` | Culture catalog + MapLibre helpers |\n"
            "| `religion_legend.json` / `religions.csv` | Religion catalog + MapLibre helpers |\n"
        )
        if include_identity_dissolve:
            identity_rows += (
                "| `cultures.geojson` / `religions.geojson` | Identity dissolved multipolygons |\n"
            )
        identity_note = (
            "Culture and religion paint use curated scenario hints. Unassigned "
            "provinces are gray (`#8a8a8a`). Prefer `['get','culture_color']` fill "
            "over large match expressions for full-world packs."
        )
        choropleth_desc = (
            "Province polygons with owner/controller/culture/religion + color fields"
        )
    else:
        identity_rows = ""
        identity_note = "Identity (culture/religion) paint was disabled for this pack."
        choropleth_desc = "Province polygons with owner/controller + `owner_color`"
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
| `ownership_choropleth.geojson` | {choropleth_desc} |
| `owners.geojson` | Owner-dissolved multipolygons (optional) |
| `uncertainty.geojson` | Disputed, foreign-controlled, or UNK-owned provinces |
| `legend.json` | Owner tag catalog, colors, MapLibre style helpers |
| `tags.csv` | Flat owner legend for tables/UI |
{identity_rows}| `ownership.csv` / `ownership.json` | API-friendly ownership rows (+ colors) |
| `countries.json` | Tags with display names and fill colors |

{owner_note}

{identity_note}

## How to consume (MapLibre / web)

1. Load `scenarios/<id>/ownership_choropleth.geojson` as a GeoJSON source.
2. Paint ownership with `["get", "owner_color"]`, or use `legend.json` →
   `styles.maplibre_fill_color` match expression.
3. Paint culture/religion with `["get", "culture_color"]` /
   `["get", "religion_color"]` (preferred property-based path).
4. Overlay `uncertainty.geojson` with a red outline for contested provinces.
5. Render legends from `legend.json` / `culture_legend.json` / `religion_legend.json`.
6. Join `tables/provinces.csv` or scenario `ownership.csv` for non-map UIs.
7. Keep `attribution.json` with any redistributed dataset.

## Notes

- Geometry is the modern open-geodata scaffold unless a later era geometry pack
  is used. Politics are scenario overlays (see M8).
- Colors are deterministic per string id (`sha256` → HSL) and stable across rebuilds.
- Culture/religion are curated hints, not Paradox-grade ethnographic maps.
- Optional PMTiles vector tiles: pass ``--tiles`` (or run ``gpm export tiles``)
  to write ``ownership.pmtiles`` per scenario and ``tiles/provinces.pmtiles``.
- FlatGeobuf / GeoParquet / TopoJSON remain optional downstream conversions.

Generated by Global Province Map Template (atlas face).
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
