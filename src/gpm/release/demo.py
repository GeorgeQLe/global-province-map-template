"""M22 `gpm demo build`: regenerate landing/demo/data from the real build.

Pipeline (temp work under data/processed/demo_build/ by default):

1. Preflight — require provinces + adjacency + hierarchy (with hierarchy
   parent fields applied) and fail with an actionable message otherwise.
2. Atlas export per scenario (ownership choropleth + legends).
3. PMTiles per scenario (native z0–7 default; tippecanoe when available
   allows deeper zooms).
4. Hierarchy overlay layers + precomputed adjacency centroid lines.
5. Copy/rename into landing/demo/data/, dropping the full global GeoJSON
   scenario files (PMTiles-first demo) while keeping the period-geometry
   sample assets unchanged.
6. Regenerate demo-manifest.json programmatically.
7. Optionally finish by running the landing-site validator.
"""

from __future__ import annotations

import csv
import json
import shutil
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from shapely.errors import ShapelyError
from shapely.geometry import mapping, shape

from gpm import __version__
from gpm.exporters import export_atlas_pack, export_hierarchy_layers
from gpm.exporters.pack import ExportError
from gpm.paths import PROCESSED_DATA_DIR, PROJECT_ROOT
from gpm.release.alpha import ReleaseError
from gpm.scenarios import ScenarioError, load_scenario
from gpm.tiles import TileBuildError, build_pmtiles_from_geojson

DEMO_SCENARIOS: tuple[str, ...] = (
    "official-1444",
    "official-1836",
    "official-1936",
    "modern-baseline",
)
DEMO_SCENARIO_LABELS = {
    "official-1444": "1444 · EU-leaning",
    "official-1836": "1836 · Victoria-leaning",
    "official-1936": "1936 · HOI-leaning",
    "modern-baseline": "Modern · Baseline",
}
# Period-geometry sample assets (M15–M20) stay hard-wired to the curated
# sample packs; recurating them for Natural Earth IDs is separate work.
PERIOD_ASSETS = {
    "official-1444": "1444",
    "official-1836": "1836",
    "official-1936": "1936",
}
HIERARCHY_LAYER_TARGETS = {
    "areas.geojson": "hierarchy-areas.geojson",
    "regions.geojson": "hierarchy-regions.geojson",
    "superregions.geojson": "hierarchy-superregions.geojson",
}
DEFAULT_TILE_MIN_ZOOM = 0
DEFAULT_TILE_MAX_ZOOM = 7
ADJACENCY_COORD_PRECISION = 4
# The landing hero renders a ~360px SVG choropleth: aggressive simplification
# and coarse coordinates keep the per-scenario hero owner dissolve tiny.
HERO_SIMPLIFY_TOLERANCE_DEG = 0.1
HERO_COORD_PRECISION = 2


class DemoBuildError(ReleaseError):
    """Raised when the demo build pipeline cannot continue."""


@dataclass(frozen=True)
class DemoBuildResult:
    profile_id: str
    landing_data_dir: str
    work_dir: str
    scenario_ids: tuple[str, ...]
    province_count: int
    tile_backend: str
    tile_min_zoom: int
    tile_max_zoom: int
    adjacency_edge_count: int
    hierarchy_counts: dict[str, int]
    dropped_files: tuple[str, ...]
    files_written: tuple[str, ...]
    validated: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_demo(
    profile_id: str = "modern-small",
    *,
    province_input: Path = PROCESSED_DATA_DIR / "provinces.geojson",
    adjacency_input: Path = PROCESSED_DATA_DIR / "adjacency.csv",
    hierarchy_input: Path = PROCESSED_DATA_DIR / "hierarchy.geojson",
    location_input: Path | None = None,
    membership_input: Path | None = None,
    aggregation_manifest_input: Path | None = None,
    landing_dir: Path | None = None,
    work_dir: Path | None = None,
    scenarios: tuple[str, ...] | list[str] = DEMO_SCENARIOS,
    tile_min_zoom: int = DEFAULT_TILE_MIN_ZOOM,
    tile_max_zoom: int = DEFAULT_TILE_MAX_ZOOM,
    prefer_tippecanoe: bool = True,
    validate: bool = True,
) -> DemoBuildResult:
    """Regenerate the landing demo data pack from the processed global build."""
    landing_dir = (landing_dir or (PROJECT_ROOT / "landing")).resolve()
    data_dir = landing_dir / "demo" / "data"
    work_dir = (work_dir or (PROCESSED_DATA_DIR / "demo_build")).resolve()
    scenario_ids = tuple(dict.fromkeys(str(item).strip() for item in scenarios if str(item).strip()))
    if not scenario_ids:
        raise DemoBuildError("Demo build requires at least one scenario.")

    provinces = _preflight(
        province_input=province_input,
        adjacency_input=adjacency_input,
        hierarchy_input=hierarchy_input,
        data_dir=data_dir,
    )
    m23_inputs = _m23_demo_inputs(
        location_input=location_input,
        membership_input=membership_input,
        aggregation_manifest_input=aggregation_manifest_input,
    )

    work_dir.mkdir(parents=True, exist_ok=True)
    files_written: list[str] = []

    # --- atlas export (choropleth + legends per scenario) ----------------------
    atlas_dir = work_dir / "atlas"
    try:
        export_atlas_pack(
            profile_id,
            province_input=province_input,
            output_dir=atlas_dir,
            scenarios=scenario_ids,
            include_base_geometry=False,
            # Owner dissolve feeds the landing hero choropleth (hero-<id>.geojson).
            include_owner_dissolve=True,
            include_identity_paint=True,
            include_identity_dissolve=False,
            include_tiles=False,
        )
    except ExportError as exc:
        raise DemoBuildError(f"Atlas export failed: {exc}") from exc

    # --- PMTiles per scenario ---------------------------------------------------
    tiles_dir = work_dir / "tiles"
    tiles_dir.mkdir(parents=True, exist_ok=True)
    backend = "native"
    scenario_tilesets: dict[str, dict[str, Any]] = {}
    for scenario_id in scenario_ids:
        choropleth = atlas_dir / "scenarios" / scenario_id / "ownership_choropleth.geojson"
        if not choropleth.is_file():
            raise DemoBuildError(f"Atlas export did not produce {choropleth}")
        try:
            result = build_pmtiles_from_geojson(
                choropleth,
                tiles_dir / f"{scenario_id}.pmtiles",
                layer_name="ownership",
                min_zoom=tile_min_zoom,
                max_zoom=tile_max_zoom,
                prefer_tippecanoe=prefer_tippecanoe,
                name=f"ownership-{scenario_id}",
                description=f"Ownership choropleth tiles for scenario {scenario_id}",
            )
        except TileBuildError as exc:
            raise DemoBuildError(f"PMTiles build failed for {scenario_id}: {exc}") from exc
        backend = result.backend
        scenario_tilesets[scenario_id] = result.to_dict()

    # --- hierarchy overlays + adjacency lines -----------------------------------
    try:
        hierarchy_result = export_hierarchy_layers(hierarchy_input, work_dir / "hierarchy_layers")
    except ExportError as exc:
        raise DemoBuildError(f"Hierarchy layer export failed: {exc}") from exc

    adjacency_lines_path = work_dir / "adjacency-lines.geojson"
    edge_count = _write_adjacency_lines(provinces, adjacency_input, adjacency_lines_path)

    # --- copy into landing/demo/data ---------------------------------------------
    data_dir.mkdir(parents=True, exist_ok=True)
    for scenario_id in scenario_ids:
        scenario_dir = atlas_dir / "scenarios" / scenario_id
        for source_name, target_name in (
            ("legend.json", f"{scenario_id}.legend.json"),
            ("culture_legend.json", f"{scenario_id}.culture.legend.json"),
            ("religion_legend.json", f"{scenario_id}.religion.legend.json"),
        ):
            shutil.copyfile(scenario_dir / source_name, data_dir / target_name)
            files_written.append(target_name)
        for suffix in (".pmtiles", ".tileset.json"):
            source = tiles_dir / f"{scenario_id}{suffix}"
            shutil.copyfile(source, data_dir / source.name)
            files_written.append(source.name)
        hero_name = f"hero-{scenario_id}.geojson"
        _write_hero_geojson(scenario_dir / "owners.geojson", data_dir / hero_name)
        files_written.append(hero_name)

    for source_name, target_name in HIERARCHY_LAYER_TARGETS.items():
        shutil.copyfile(Path(hierarchy_result.output_dir) / source_name, data_dir / target_name)
        files_written.append(target_name)

    shutil.copyfile(adjacency_lines_path, data_dir / adjacency_lines_path.name)
    files_written.append(adjacency_lines_path.name)

    # PMTiles-first: drop the full global scenario GeoJSON and the legacy
    # sample adjacency assets from the shipped demo.
    dropped: list[str] = []
    for scenario_id in scenario_ids:
        dropped.extend(_drop(data_dir / f"{scenario_id}.geojson"))
    dropped.extend(_drop(data_dir / "adjacency.json"))
    dropped.extend(_drop(data_dir / "adjacency.csv"))

    # --- manifest ------------------------------------------------------------------
    manifest = _demo_manifest(
        profile_id=profile_id,
        scenario_ids=scenario_ids,
        scenario_tilesets=scenario_tilesets,
        province_count=len(provinces),
        backend=backend,
        tile_min_zoom=tile_min_zoom,
        tile_max_zoom=tile_max_zoom,
        hierarchy_counts={
            "areas": hierarchy_result.area_count,
            "regions": hierarchy_result.region_count,
            "superregions": hierarchy_result.superregion_count,
        },
        adjacency_edge_count=edge_count,
        m23_inputs=m23_inputs,
    )
    manifest_path = data_dir / "demo-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )
    files_written.append(manifest_path.name)

    validated = False
    if validate and not set(DEMO_SCENARIOS) <= set(scenario_ids):
        # The landing validator requires the full default scenario set; a
        # partial rebuild cannot satisfy it, so skip rather than fail on
        # files this run was never asked to produce.
        validate = False
    if validate:
        from gpm.release.site import validate_landing_site

        validation = validate_landing_site(landing_dir)
        if not validation.valid:
            missing = [
                *validation.missing_files,
                *validation.missing_demo_files,
                *validation.missing_snippets,
                *validation.missing_demo_snippets,
            ]
            raise DemoBuildError(
                "Demo build finished but landing-site validation failed; missing: "
                + ", ".join(missing)
            )
        validated = True

    return DemoBuildResult(
        profile_id=profile_id,
        landing_data_dir=str(data_dir),
        work_dir=str(work_dir),
        scenario_ids=scenario_ids,
        province_count=len(provinces),
        tile_backend=backend,
        tile_min_zoom=tile_min_zoom,
        tile_max_zoom=tile_max_zoom,
        adjacency_edge_count=edge_count,
        hierarchy_counts={
            "areas": hierarchy_result.area_count,
            "regions": hierarchy_result.region_count,
            "superregions": hierarchy_result.superregion_count,
        },
        dropped_files=tuple(sorted(dropped)),
        files_written=tuple(sorted(set(files_written))),
        validated=validated,
    )


def _preflight(
    *,
    province_input: Path,
    adjacency_input: Path,
    hierarchy_input: Path,
    data_dir: Path,
) -> list[dict[str, Any]]:
    """Validate inputs and return land province features."""
    problems: list[str] = []
    if not province_input.is_file():
        problems.append(
            f"provinces missing at {province_input} — run `uv run gpm build provinces`"
        )
    if not adjacency_input.is_file():
        problems.append(
            f"adjacency missing at {adjacency_input} — run `uv run gpm build adjacency`"
        )
    if not hierarchy_input.is_file():
        problems.append(
            f"hierarchy missing at {hierarchy_input} — run `uv run gpm build hierarchy`"
        )
    if not data_dir.parent.is_dir():
        problems.append(f"landing demo directory missing at {data_dir.parent}")
    if problems:
        raise DemoBuildError("Demo build preflight failed:\n- " + "\n- ".join(problems))

    try:
        document = json.loads(province_input.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise DemoBuildError(f"Cannot read provinces {province_input}: {exc}") from exc
    features = [
        feature
        for feature in (document.get("features") or [])
        if isinstance(feature, dict)
        and isinstance(feature.get("properties"), dict)
        and feature["properties"].get("kind") == "land"
    ]
    if not features:
        raise DemoBuildError(f"Province input has no land features: {province_input}")
    if not any(feature["properties"].get("parent_area_id") for feature in features):
        raise DemoBuildError(
            "Provinces are missing hierarchy parent fields (parent_area_id). "
            "Run `uv run gpm build hierarchy` after `gpm build adjacency` so the "
            "demo can paint and label the area/region/superregion hierarchy."
        )
    return features


def _m23_demo_inputs(*, location_input: Path | None, membership_input: Path | None,
                     aggregation_manifest_input: Path | None) -> dict[str, Any] | None:
    supplied = (location_input, membership_input, aggregation_manifest_input)
    if not any(item is not None for item in supplied):
        return None
    if not all(item is not None for item in supplied):
        raise DemoBuildError(
            "M23 demo regeneration requires --location-input, --membership-input, "
            "and --aggregation-manifest together."
        )
    missing = [str(path) for path in supplied if path is not None and not Path(path).is_file()]
    if missing:
        raise DemoBuildError(f"M23 demo input(s) missing: {', '.join(missing)}")
    assert location_input is not None and membership_input is not None and aggregation_manifest_input is not None
    try:
        locations = json.loads(Path(location_input).read_text(encoding="utf-8"))
        aggregation = json.loads(Path(aggregation_manifest_input).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DemoBuildError(f"Cannot read M23 demo metadata: {exc}") from exc
    return {
        "location_input": str(location_input),
        "membership_input": str(membership_input),
        "aggregation_manifest": str(aggregation_manifest_input),
        "fabric_id": (locations.get("gpm") or {}).get("fabric_id"),
        "fabric_revision": (locations.get("gpm") or {}).get("fabric_revision"),
        "location_count": len(locations.get("features") or []),
        "aggregation_revision": aggregation.get("aggregation_revision"),
        "geometry_revision": aggregation.get("geometry_revision"),
    }


def _write_hero_geojson(owners_input: Path, output: Path) -> None:
    """Slim, heavily simplified owner dissolve for the landing hero SVG."""
    try:
        document = json.loads(owners_input.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise DemoBuildError(f"Cannot read owner dissolve {owners_input}: {exc}") from exc

    def round_coords(value: Any) -> Any:
        if isinstance(value, (list, tuple)):
            return [round_coords(item) for item in value]
        if isinstance(value, float):
            return round(value, HERO_COORD_PRECISION)
        return value

    features: list[dict[str, Any]] = []
    for feature in document.get("features") or []:
        if not isinstance(feature, dict):
            continue
        properties = feature.get("properties") or {}
        geometry = feature.get("geometry")
        if geometry is None:
            continue
        try:
            geom = shape(geometry).simplify(HERO_SIMPLIFY_TOLERANCE_DEG, preserve_topology=True)
        except (ShapelyError, TypeError, ValueError):
            continue
        if geom.is_empty:
            continue
        geometry = dict(mapping(geom))
        geometry["coordinates"] = round_coords(geometry.get("coordinates"))
        features.append(
            {
                "type": "Feature",
                "geometry": geometry,
                "properties": {
                    "owner": properties.get("owner"),
                    "owner_color": properties.get("owner_color"),
                    "display_name": properties.get("display_name"),
                    "province_count": properties.get("province_count"),
                },
            }
        )
    output.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "name": "hero_owners",
                "gpm": {
                    "schema_version": "0.1.0",
                    "milestone": "M22",
                    "layer": "hero_owners",
                    "generator_version": __version__,
                    "feature_count": len(features),
                },
                "features": features,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )


def _write_adjacency_lines(
    provinces: list[dict[str, Any]], adjacency_input: Path, output: Path
) -> int:
    """Precompute centroid-to-centroid adjacency lines for the demo overlay."""
    centroids: dict[str, tuple[float, float]] = {}
    for feature in provinces:
        province_id = feature["properties"].get("province_id")
        if not isinstance(province_id, str):
            continue
        try:
            point = shape(feature.get("geometry")).representative_point()
        except (ShapelyError, TypeError, ValueError):
            continue
        centroids[province_id] = (
            round(point.x, ADJACENCY_COORD_PRECISION),
            round(point.y, ADJACENCY_COORD_PRECISION),
        )

    features: list[dict[str, Any]] = []
    try:
        with adjacency_input.open("r", encoding="utf-8", newline="") as file:
            for row in csv.DictReader(file):
                edge_type = (row.get("adjacency_type") or "").strip()
                if edge_type not in {"land", "strait"}:
                    continue
                from_id = (row.get("from_province_id") or "").strip()
                to_id = (row.get("to_province_id") or "").strip()
                start = centroids.get(from_id)
                end = centroids.get(to_id)
                if start is None or end is None:
                    continue
                features.append(
                    {
                        "type": "Feature",
                        "geometry": {"type": "LineString", "coordinates": [list(start), list(end)]},
                        "properties": {
                            "from": from_id,
                            "to": to_id,
                            "type": edge_type,
                        },
                    }
                )
    except OSError as exc:
        raise DemoBuildError(f"Cannot read adjacency CSV {adjacency_input}: {exc}") from exc

    features.sort(key=lambda f: (f["properties"]["from"], f["properties"]["to"]))
    output.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "name": "adjacency_lines",
                "gpm": {
                    "schema_version": "0.1.0",
                    "milestone": "M22",
                    "layer": "adjacency_lines",
                    "generator_version": __version__,
                    "edge_count": len(features),
                },
                "features": features,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )
    return len(features)


def _demo_manifest(
    *,
    profile_id: str,
    scenario_ids: tuple[str, ...],
    scenario_tilesets: dict[str, dict[str, Any]],
    province_count: int,
    backend: str,
    tile_min_zoom: int,
    tile_max_zoom: int,
    hierarchy_counts: dict[str, int],
    adjacency_edge_count: int,
    m23_inputs: dict[str, Any] | None,
) -> dict[str, Any]:
    generated_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    scenarios: list[dict[str, Any]] = []
    for scenario_id in scenario_ids:
        try:
            definition = load_scenario(scenario_id)
        except ScenarioError as exc:
            raise DemoBuildError(str(exc)) from exc
        era = PERIOD_ASSETS.get(scenario_id)
        entry: dict[str, Any] = {
            "id": scenario_id,
            "era": definition.get("era"),
            "label": DEMO_SCENARIO_LABELS.get(scenario_id, definition.get("label") or scenario_id),
            "politics_tier": definition.get("quality_tier") or "curated-politics",
            "start_date": definition.get("start_date"),
            # PMTiles-first: no full global GeoJSON ships with the demo.
            "geojson": None,
            "hero": f"hero-{scenario_id}.geojson",
            "pmtiles": f"{scenario_id}.pmtiles",
            "tileset": f"{scenario_id}.tileset.json",
            "legend": f"{scenario_id}.legend.json",
            "culture_legend": f"{scenario_id}.culture.legend.json",
            "religion_legend": f"{scenario_id}.religion.legend.json",
            "status": "live",
            "supports_period_geometry": era is not None,
        }
        if era is not None:
            entry.update(
                {
                    "period_geojson": f"{scenario_id}-period.geojson",
                    "period_legend": f"{scenario_id}-period.legend.json",
                    "period_culture_legend": f"{scenario_id}-period.culture.legend.json",
                    "period_religion_legend": f"{scenario_id}-period.religion.legend.json",
                    "boundary_hints": f"boundary-hints-{era}.geojson",
                    "lineage": f"lineage-{era}.json",
                }
            )
        tileset = scenario_tilesets.get(scenario_id) or {}
        if tileset:
            entry["tile_backend"] = tileset.get("backend")
            entry["tile_count"] = tileset.get("tile_count")
        scenarios.append(entry)

    return {
        "title": "GPM interactive demo",
        "sample": "Global Natural Earth build (M22) + europe-multi-era-v1 period geometry (M20)",
        "geometry_tier": "scaffold-baseline",
        "period_geometry_tier": "period-geometry",
        "period_geometry_pack": "europe-multi-era-v1",
        "multi_era_pack": "europe-multi-era-v1",
        "note": (
            "PMTiles-first global demo over the full Natural Earth admin-1 build "
            f"({province_count} provinces) with the M21 area/region/superregion "
            "hierarchy. Politics are era overlays; culture/religion paint (M18) uses "
            "curated scenario hints. Period geometry / boundary hints stay on the "
            "curated Western/Central Europe sample packs (M20)."
        ),
        "generated": {
            "generated_at": generated_at,
            "generator_version": __version__,
            "profile_id": profile_id,
            "province_count": province_count,
            "command": (
                "uv run gpm demo build --location-input data/processed/locations.geojson "
                "--membership-input data/processed/province_membership.csv "
                "--aggregation-manifest data/processed/province_aggregation_manifest.json"
                if m23_inputs else "uv run gpm demo build"
            ),
        },
        "m23": m23_inputs,
        "pmtiles": {
            "enabled": True,
            "protocol": "pmtiles",
            "source_layer": "ownership",
            "min_zoom": tile_min_zoom,
            "max_zoom": tile_max_zoom,
            "backend": backend,
            "note": "Primary polygon source; the inspector reads rendered vector features.",
        },
        "hierarchy": {
            "areas": "hierarchy-areas.geojson",
            "regions": "hierarchy-regions.geojson",
            "superregions": "hierarchy-superregions.geojson",
            "counts": hierarchy_counts,
        },
        "adjacency": {
            "lines": "adjacency-lines.geojson",
            "edge_count": adjacency_edge_count,
        },
        "live_layers": [
            {
                "id": "ownership",
                "label": "Owner choropleth",
                "desc": "Scenario owner colors from atlas export (PMTiles vector source)",
            },
            {
                "id": "culture",
                "label": "Culture paint",
                "desc": "M18 curated culture hints with deterministic colors",
                "milestone": "M18",
            },
            {
                "id": "religion",
                "label": "Religion paint",
                "desc": "M18 curated religion hints with deterministic colors",
                "milestone": "M18",
            },
            {
                "id": "hierarchy",
                "label": "Area / region / superregion hierarchy",
                "desc": (
                    "M21 nested hierarchy borders and paint over "
                    f"{hierarchy_counts['areas']} areas, {hierarchy_counts['regions']} regions, "
                    f"{hierarchy_counts['superregions']} superregions"
                ),
                "milestone": "M21",
            },
            {
                "id": "assignment",
                "label": "Assignment source",
                "desc": "baseline · country_rule · region_rule · province_override",
            },
            {
                "id": "adjacency",
                "label": "Adjacency graph",
                "desc": "Precomputed land/strait centroid lines from the global adjacency CSV",
            },
            {
                "id": "labels",
                "label": "Province labels",
                "desc": "Stable IDs + display names",
            },
            {
                "id": "inspector",
                "label": "Province inspector",
                "desc": "Owner, controller, cores, claims, culture, religion, hierarchy fields",
            },
            {
                "id": "period-geometry",
                "label": "Period geometry",
                "desc": "M16 multi-era hard overrides / soft shapes for WE+CE sample (1444 · 1836 · 1936)",
                "milestone": "M16",
            },
            {
                "id": "boundary-hints",
                "label": "Historical boundary hints",
                "desc": "M16 soft frontier bands per era without full world redraw",
                "milestone": "M16",
            },
            {
                "id": "multi-era-packs",
                "label": "Multi-era geometry + politics packs",
                "desc": "Paired geometry + politics for 1444/1836/1936 with region quality tiers and migration notes",
                "milestone": "M16",
            },
            {
                "id": "curation-diff",
                "label": "Curation diffs & golden borders",
                "desc": "M17: gpm curation diff/checklist, external bundles, expanded golden-border suites",
                "milestone": "M17",
            },
            {
                "id": "pmtiles",
                "label": "PMTiles / vector tiles",
                "desc": "M19/M22: per-scenario global ownership PMTiles are the primary polygon source",
                "milestone": "M19",
            },
        ],
        "future_slots": [
            {
                "id": "start-date-reconstructions",
                "label": "Certified start-date reconstructions",
                "milestone": "M24–M28",
                "desc": (
                    "Evidence dossiers and full-build regional certification for "
                    "1444, 1836, 1914, and 1936 over the M23 neutral location fabric"
                ),
            },
        ],
        "export_faces": [
            {"id": "pack", "command": "gpm export pack", "label": "Game template pack"},
            {"id": "atlas", "command": "gpm export atlas", "label": "Atlas / SaaS face"},
            {"id": "tiles", "command": "gpm export tiles", "label": "PMTiles / vector tiles"},
        ],
        "scenarios": scenarios,
    }


def _drop(path: Path) -> list[str]:
    if path.is_file():
        path.unlink()
        return [path.name]
    return []
