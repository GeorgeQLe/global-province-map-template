from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from .builders.adjacency import AdjacencyBuildError, build_land_adjacency
from .builders.hierarchy import HierarchyBuildError, build_hierarchy
from .builders.provinces import ProvinceBuildError, build_land_province_draft
from .builders.seas import SeaBuildError, build_sea_zones
from .config import DEFAULT_PROFILE_ID, ConfigError, load_profile
from .curation import (
    ChecklistResult,
    CuratorBundleError,
    OwnershipDiffError,
    diff_ownership,
    import_curator_bundle,
    list_curator_bundles,
    load_curator_bundle,
    load_ownership_side,
    run_contribution_checklist,
    validate_curator_bundle,
)
from .exporters import (
    ExportError,
    export_atlas_pack,
    export_game_pack,
    export_geojson_pack,
    export_tiles_from_atlas,
    export_tiles_pack,
)
from .tiles import TileBuildError
from .manifest import (
    build_downloaded_source_manifest,
    build_local_source_manifest,
    build_planned_source_manifest,
)
from .era_geometry import (
    EraGeometryError,
    apply_era_geometry_pack,
    list_era_geometry_packs,
    load_era_geometry_pack,
    validate_era_geometry_pack,
)
from .era_geometry.packs import EraGeometryPackError
from .multi_era import (
    MultiEraError,
    build_migration_document,
    build_multi_era_pack,
    list_multi_era_packs,
    load_multi_era_pack,
    migration_markdown,
    validate_multi_era_pack,
)
from .multi_era.packs import MultiEraPackError
from .paths import EXPORT_DIR, INTERMEDIATE_DATA_DIR, PROCESSED_DATA_DIR, RAW_DATA_DIR, SAMPLE_DIR
from .qa.scenario import ScenarioPoliticsQAError, run_scenario_politics_qa
from .qa.topology import TopologyQAError, run_topology_qa
from .release import (
    DEFAULT_ALPHA_SCENARIOS,
    DEFAULT_BETA_SCENARIOS,
    DEFAULT_SAMPLE_COUNTRIES,
    DEMO_SCENARIOS,
    DemoBuildError,
    ReleaseError,
    build_alpha_release,
    build_beta_release,
    build_demo,
    release_landing_site,
)
from .scenarios import (
    ScenarioError,
    build_scenario_ownership,
    list_scenarios,
    load_scenario,
)
from .schemas import validate_source_manifest
from .sources.artifacts import SourceArtifactError, download_source_artifacts
from .sources.registry import SourceRegistryError, resolve_source_adapters
from .viewer import ReviewError, prepare_review_dataset, serve_review


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "handler"):
        parser.print_help()
        return 2
    return args.handler(args)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gpm",
        description="Generate EU/Victoria/HOI-style global province maps from open geodata.",
    )
    subcommands = parser.add_subparsers(dest="group")

    sources = subcommands.add_parser("sources", help="Manage source downloads and manifests.")
    source_commands = sources.add_subparsers(dest="command")
    download = source_commands.add_parser("download", help="Download or plan source artifacts.")
    _add_profile_arg(download)
    _add_source_arg(download)
    _add_raw_dir_arg(download)
    download.add_argument(
        "--execute",
        action="store_true",
        help="Fetch source artifacts. Omit for a dry-run plan.",
    )
    download.add_argument(
        "--force",
        action="store_true",
        help="Re-download artifacts even when target files already exist.",
    )
    download.add_argument(
        "--manifest-output",
        type=Path,
        help="Path for the downloaded source manifest. Defaults to <raw-dir>/source_manifest.json.",
    )
    download.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="Per-request timeout in seconds when --execute is used. Defaults to 60.",
    )
    download.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format. Dry runs emit planned records; executed downloads emit the manifest.",
    )
    download.set_defaults(handler=_sources_download)
    manifest = source_commands.add_parser("manifest", help="Print a planned source manifest.")
    _add_profile_arg(manifest)
    _add_source_arg(manifest)
    _add_raw_dir_arg(manifest)
    manifest.add_argument(
        "--from-raw",
        action="store_true",
        help="Hash local raw artifacts and emit a downloaded/build manifest instead of a planned manifest.",
    )
    manifest.add_argument(
        "--output",
        type=Path,
        help="Optional path for writing the planned manifest JSON. Defaults to stdout only.",
    )
    manifest.set_defaults(handler=_sources_manifest)

    build = subcommands.add_parser("build", help="Build generated map layers.")
    build_commands = build.add_subparsers(dest="command")
    provinces = build_commands.add_parser(
        "provinces",
        help="Build land province candidates and optional M4 population-weighted refinement.",
    )
    _add_profile_arg(provinces)
    _add_raw_dir_arg(provinces)
    provinces.add_argument(
        "--intermediate-dir",
        type=Path,
        default=INTERMEDIATE_DATA_DIR,
        help=f"Directory for canonical intermediate layers. Defaults to {INTERMEDIATE_DATA_DIR}.",
    )
    provinces.add_argument(
        "--processed-dir",
        type=Path,
        default=PROCESSED_DATA_DIR,
        help=f"Directory for processed map layers. Defaults to {PROCESSED_DATA_DIR}.",
    )
    provinces.add_argument(
        "--candidate-output",
        type=Path,
        help="Optional explicit path for land province candidate GeoJSON.",
    )
    provinces.add_argument(
        "--province-output",
        type=Path,
        help="Optional explicit path for processed province GeoJSON.",
    )
    provinces.add_argument(
        "--refine",
        action="store_true",
        help="Apply M4 area-weighted refinement even when no population or settlement input is supplied.",
    )
    provinces.add_argument(
        "--target-province-count",
        type=int,
        help="Override the profile's M4 target count. Supplying this option enables refinement.",
    )
    provinces.add_argument(
        "--population-input",
        type=Path,
        help="WGS84 population-point GeoJSON or georeferenced population-count GeoTIFF.",
    )
    provinces.add_argument(
        "--settlement-input",
        type=Path,
        help="WGS84 settlement-point GeoJSON used as population-weighted split seeds.",
    )
    provinces.add_argument(
        "--population-license",
        action="append",
        default=[],
        help="License-lineage notice for the population input; may be repeated.",
    )
    provinces.add_argument(
        "--settlement-license",
        action="append",
        default=[],
        help="License-lineage notice for the settlement input; may be repeated.",
    )
    provinces.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format for the build summary.",
    )
    provinces.set_defaults(handler=_build_provinces)
    adjacency = build_commands.add_parser(
        "adjacency",
        help="Build canonical adjacency CSV (land, and marine edges when sea zones exist).",
    )
    _add_profile_arg(adjacency)
    adjacency.add_argument(
        "--province-input",
        type=Path,
        default=PROCESSED_DATA_DIR / "provinces.geojson",
        help="Province GeoJSON input. Defaults to data/processed/provinces.geojson.",
    )
    adjacency.add_argument(
        "--sea-input",
        type=Path,
        default=None,
        help=(
            "Sea-zone GeoJSON input. Defaults to sea_zones.geojson next to the province "
            "input when present; missing files leave the graph land-only."
        ),
    )
    adjacency.add_argument(
        "--output",
        type=Path,
        default=PROCESSED_DATA_DIR / "adjacency.csv",
        help="Adjacency CSV output. Defaults to data/processed/adjacency.csv.",
    )
    adjacency.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format for the build summary.",
    )
    adjacency.set_defaults(handler=_build_adjacency)

    hierarchy = build_commands.add_parser(
        "hierarchy",
        help="Build the M21 area/region/superregion hierarchy and enrich provinces with parent fields.",
    )
    _add_profile_arg(hierarchy)
    _add_raw_dir_arg(hierarchy)
    hierarchy.add_argument(
        "--province-input",
        type=Path,
        default=PROCESSED_DATA_DIR / "provinces.geojson",
        help="Province GeoJSON input. Defaults to data/processed/provinces.geojson.",
    )
    hierarchy.add_argument(
        "--adjacency-input",
        type=Path,
        default=PROCESSED_DATA_DIR / "adjacency.csv",
        help="Adjacency CSV input. Defaults to data/processed/adjacency.csv.",
    )
    hierarchy.add_argument(
        "--output",
        type=Path,
        default=PROCESSED_DATA_DIR / "hierarchy.geojson",
        help="Hierarchy GeoJSON output. Defaults to data/processed/hierarchy.geojson.",
    )
    hierarchy.add_argument(
        "--province-output",
        type=Path,
        help="Optional path for enriched provinces. Defaults to overwriting --province-input.",
    )
    hierarchy.add_argument(
        "--no-update-provinces",
        action="store_true",
        help="Do not rewrite provinces with parent hierarchy fields.",
    )
    hierarchy.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format for the build summary.",
    )
    hierarchy.set_defaults(handler=_build_hierarchy)

    seas = build_commands.add_parser(
        "seas",
        help="Build coastal and ocean sea zones, mark coastal land provinces, and prepare port/strait inputs.",
    )
    _add_profile_arg(seas)
    _add_raw_dir_arg(seas)
    seas.add_argument(
        "--province-input",
        type=Path,
        default=PROCESSED_DATA_DIR / "provinces.geojson",
        help="Land province GeoJSON input. Defaults to data/processed/provinces.geojson.",
    )
    seas.add_argument(
        "--sea-output",
        type=Path,
        default=PROCESSED_DATA_DIR / "sea_zones.geojson",
        help="Sea-zone GeoJSON output. Defaults to data/processed/sea_zones.geojson.",
    )
    seas.add_argument(
        "--province-output",
        type=Path,
        help=(
            "Optional path for land provinces with updated coastal flags. "
            "Defaults to overwriting --province-input when coastal updates are enabled."
        ),
    )
    seas.add_argument(
        "--no-update-provinces",
        action="store_true",
        help="Do not rewrite land provinces with coastal flags.",
    )
    seas.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format for the build summary.",
    )
    seas.set_defaults(handler=_build_seas)

    export = subcommands.add_parser("export", help="Export generated outputs.")
    export_commands = export.add_subparsers(dest="command")
    geojson = export_commands.add_parser(
        "geojson",
        help="Export provinces, derived regions, and optional sea zones as GeoJSON.",
    )
    _add_profile_arg(geojson)
    _add_export_common_args(geojson)
    geojson.set_defaults(handler=_export_geojson)
    pack = export_commands.add_parser(
        "pack",
        help=(
            "Export a profile-specific game template pack: province/region definitions, "
            "adjacency, localization stubs, tables, attribution, and GeoJSON."
        ),
    )
    _add_profile_arg(pack)
    _add_export_common_args(pack)
    pack.add_argument(
        "--scenario",
        action="append",
        dest="scenarios",
        help=(
            "Scenario id to embed under scenarios/<id>/ in the pack. May be repeated. "
            "Builds ownership tables from the province input at export time."
        ),
    )
    pack.add_argument(
        "--allow-unknown-overrides",
        action="store_true",
        help="When embedding scenarios, ignore province_overrides that do not match land IDs.",
    )
    pack.set_defaults(handler=_export_pack)
    atlas = export_commands.add_parser(
        "atlas",
        help=(
            "Export an atlas / SaaS package: scenario-joined choropleths, tag legends, "
            "uncertainty layers, and web-friendly tables (second export face)."
        ),
    )
    _add_profile_arg(atlas)
    atlas.add_argument(
        "--province-input",
        type=Path,
        default=PROCESSED_DATA_DIR / "provinces.geojson",
        help="Land province GeoJSON input. Defaults to data/processed/provinces.geojson.",
    )
    atlas.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=f"Atlas pack output directory. Defaults to {EXPORT_DIR}/atlas/<profile-id>.",
    )
    atlas.add_argument(
        "--scenario",
        action="append",
        dest="scenarios",
        help=(
            "Scenario id for choropleth/legend layers. May be repeated. "
            "Defaults to modern-baseline when omitted."
        ),
    )
    atlas.add_argument(
        "--allow-unknown-overrides",
        action="store_true",
        help="Ignore province_overrides that do not match land IDs.",
    )
    atlas.add_argument(
        "--no-base-geometry",
        action="store_true",
        help="Skip writing geojson/provinces.geojson base layer (scenario choropleths still write).",
    )
    atlas.add_argument(
        "--no-owner-dissolve",
        action="store_true",
        help="Skip writing owners.geojson dissolved multipolygons per scenario.",
    )
    atlas.add_argument(
        "--no-identity-paint",
        action="store_true",
        help=(
            "Skip culture/religion colors, legends, and dissolve "
            "(exact pre-M18 ownership paint surface)."
        ),
    )
    atlas.add_argument(
        "--no-identity-dissolve",
        action="store_true",
        help="Skip cultures.geojson / religions.geojson (identity paint still ships).",
    )
    atlas.add_argument(
        "--tiles",
        action="store_true",
        help=(
            "Also write PMTiles vector tiles (ownership.pmtiles per scenario, "
            "tiles/provinces.pmtiles for base geometry)."
        ),
    )
    atlas.add_argument(
        "--tile-min-zoom",
        type=int,
        default=0,
        help="Minimum zoom for --tiles (default 0).",
    )
    atlas.add_argument(
        "--tile-max-zoom",
        type=int,
        default=8,
        help="Maximum zoom for --tiles (default 8).",
    )
    atlas.add_argument(
        "--no-tippecanoe",
        action="store_true",
        help="Force pure-Python tile backend even when tippecanoe is installed.",
    )
    atlas.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format for the export summary.",
    )
    atlas.set_defaults(handler=_export_atlas)

    tiles = export_commands.add_parser(
        "tiles",
        help=(
            "Export PMTiles / Mapbox Vector Tiles from GeoJSON or an atlas pack "
            "(web-scale delivery; pure-Python backend, tippecanoe when available)."
        ),
    )
    tiles.add_argument(
        "--input",
        type=Path,
        default=None,
        help="Input GeoJSON (FeatureCollection). Required unless --atlas-dir is set.",
    )
    tiles.add_argument(
        "--atlas-dir",
        type=Path,
        default=None,
        help=(
            "Existing atlas pack directory. Writes ownership.pmtiles under each "
            "scenarios/<id>/ and optional tiles/provinces.pmtiles."
        ),
    )
    tiles.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=f"Output directory for a single GeoJSON input. Defaults to {EXPORT_DIR}/tiles/<stem>.",
    )
    tiles.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Explicit .pmtiles output path (single GeoJSON input only).",
    )
    tiles.add_argument(
        "--layer",
        default="provinces",
        help="Vector tile layer name (default: provinces).",
    )
    tiles.add_argument(
        "--min-zoom",
        type=int,
        default=0,
        help="Minimum zoom level (default 0).",
    )
    tiles.add_argument(
        "--max-zoom",
        type=int,
        default=8,
        help="Maximum zoom level (default 8).",
    )
    tiles.add_argument(
        "--no-tippecanoe",
        action="store_true",
        help="Force pure-Python backend even when tippecanoe is installed.",
    )
    tiles.add_argument(
        "--scenario",
        action="append",
        dest="scenarios",
        help="When using --atlas-dir, limit to these scenario ids (repeatable).",
    )
    tiles.add_argument(
        "--no-base",
        action="store_true",
        help="When using --atlas-dir, skip tiles/provinces.pmtiles base layer.",
    )
    tiles.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format for the export summary.",
    )
    tiles.set_defaults(handler=_export_tiles)

    scenario = subcommands.add_parser(
        "scenario",
        help="Build historical/baseline ownership overlays over modern province geometry.",
    )
    scenario_commands = scenario.add_subparsers(dest="command")
    scenario_list = scenario_commands.add_parser(
        "list",
        help="List bundled scenario definitions under configs/scenarios/.",
    )
    scenario_list.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format for the scenario list.",
    )
    scenario_list.set_defaults(handler=_scenario_list)
    scenario_validate = scenario_commands.add_parser(
        "validate",
        help="Validate a scenario definition without writing ownership tables.",
    )
    scenario_validate.add_argument(
        "--scenario",
        required=True,
        help="Scenario id under configs/scenarios/ (for example modern-baseline or demo-1444).",
    )
    scenario_validate.add_argument(
        "--scenario-path",
        type=Path,
        help="Optional explicit scenario JSON path instead of --scenario id lookup.",
    )
    scenario_validate.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format for the validation summary.",
    )
    scenario_validate.set_defaults(handler=_scenario_validate)
    scenario_build = scenario_commands.add_parser(
        "build",
        help=(
            "Resolve ownership/controller tables for a scenario over processed land provinces. "
            "Geometry is not modified; only political attributes are written."
        ),
    )
    _add_profile_arg(scenario_build)
    scenario_build.add_argument(
        "--scenario",
        required=True,
        help="Scenario id under configs/scenarios/ (for example modern-baseline or demo-1444).",
    )
    scenario_build.add_argument(
        "--scenario-path",
        type=Path,
        help="Optional explicit scenario JSON path instead of --scenario id lookup.",
    )
    scenario_build.add_argument(
        "--province-input",
        type=Path,
        default=PROCESSED_DATA_DIR / "provinces.geojson",
        help="Land province GeoJSON input. Defaults to data/processed/provinces.geojson.",
    )
    scenario_build.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Scenario output directory. Defaults to data/processed/scenarios/<scenario-id>.",
    )
    scenario_build.add_argument(
        "--allow-unknown-overrides",
        action="store_true",
        help="Ignore province_overrides that do not match land province IDs (emit a count only).",
    )
    scenario_build.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format for the build summary.",
    )
    scenario_build.set_defaults(handler=_scenario_build)

    qa = subcommands.add_parser("qa", help="Run quality checks and review outputs.")
    qa_commands = qa.add_subparsers(dest="command")
    topology = qa_commands.add_parser("topology", help="Validate province topology and land adjacency.")
    _add_profile_arg(topology)
    topology.add_argument(
        "--province-input",
        type=Path,
        default=PROCESSED_DATA_DIR / "provinces.geojson",
        help="Province GeoJSON input. Defaults to data/processed/provinces.geojson.",
    )
    topology.add_argument(
        "--adjacency-input",
        type=Path,
        default=PROCESSED_DATA_DIR / "adjacency.csv",
        help="Adjacency CSV input. Defaults to data/processed/adjacency.csv.",
    )
    topology.add_argument(
        "--raw-data",
        "--raw-dir",
        dest="raw_data",
        type=Path,
        default=RAW_DATA_DIR,
        help="Raw-data directory or Natural Earth admin-0 zip. Defaults to data/raw.",
    )
    topology.add_argument(
        "--report-output",
        type=Path,
        default=PROCESSED_DATA_DIR / "topology_qa.json",
        help="JSON report output. Defaults to data/processed/topology_qa.json.",
    )
    topology.add_argument(
        "--format",
        "--summary-format",
        dest="format",
        choices=["text", "json"],
        default="text",
        help="Output format for the QA summary.",
    )
    topology.set_defaults(handler=_qa_topology)
    scenario_qa = qa_commands.add_parser(
        "scenario",
        help=(
            "Validate scenario politics: ownership coverage, tags, orphan cores/claims, "
            "owner-component sanity, and optional golden checks."
        ),
    )
    _add_profile_arg(scenario_qa)
    scenario_qa.add_argument(
        "--scenario",
        required=True,
        help=(
            "Scenario id under configs/scenarios/ "
            "(for example modern-baseline, demo-1444, official-1836, or official-1444)."
        ),
    )
    scenario_qa.add_argument(
        "--scenario-path",
        type=Path,
        help="Optional explicit scenario JSON path instead of --scenario id lookup.",
    )
    scenario_qa.add_argument(
        "--province-input",
        type=Path,
        default=PROCESSED_DATA_DIR / "provinces.geojson",
        help="Province GeoJSON input. Defaults to data/processed/provinces.geojson.",
    )
    scenario_qa.add_argument(
        "--adjacency-input",
        type=Path,
        default=PROCESSED_DATA_DIR / "adjacency.csv",
        help=(
            "Adjacency CSV for owner-component checks. Defaults to data/processed/adjacency.csv. "
            "Missing files skip adjacency analysis with a warning."
        ),
    )
    scenario_qa.add_argument(
        "--ownership-input",
        type=Path,
        default=None,
        help=(
            "Optional pre-built ownership CSV/JSON. When omitted, ownership is resolved "
            "from the scenario definition and province input."
        ),
    )
    scenario_qa.add_argument(
        "--golden",
        type=Path,
        default=None,
        help=(
            "Optional golden check JSON (province_owners / min_owner_counts). "
            "When omitted, configs/scenarios/golden/<scenario-id>.json is used if present."
        ),
    )
    scenario_qa.add_argument(
        "--report-output",
        type=Path,
        default=None,
        help="JSON report output. Defaults to data/processed/scenarios/<id>/politics_qa.json.",
    )
    scenario_qa.add_argument(
        "--allow-unknown-overrides",
        action="store_true",
        help="Ignore province_overrides that do not match land province IDs when resolving.",
    )
    scenario_qa.add_argument(
        "--max-owner-components",
        type=int,
        default=25,
        help="Warn when an owner has more disconnected land/strait components than this. Default 25.",
    )
    scenario_qa.add_argument(
        "--min-provinces-for-fragment-check",
        type=int,
        default=8,
        help="Only run fragment checks for owners with at least this many provinces. Default 8.",
    )
    scenario_qa.add_argument(
        "--format",
        "--summary-format",
        dest="format",
        choices=["text", "json"],
        default="text",
        help="Output format for the QA summary.",
    )
    scenario_qa.set_defaults(handler=_qa_scenario)
    render = qa_commands.add_parser("render", help="Placeholder for visual render QA.")
    _add_profile_arg(render)
    render.set_defaults(handler=_qa_render)

    review = subcommands.add_parser(
        "review",
        help="Serve the interactive MapLibre review viewer for processed outputs.",
    )
    _add_profile_arg(review)
    review.add_argument(
        "--province-input",
        type=Path,
        default=PROCESSED_DATA_DIR / "provinces.geojson",
        help="Province GeoJSON input. Defaults to data/processed/provinces.geojson.",
    )
    review.add_argument(
        "--adjacency-input",
        type=Path,
        default=PROCESSED_DATA_DIR / "adjacency.csv",
        help="Adjacency CSV input. Defaults to data/processed/adjacency.csv. Missing files are skipped.",
    )
    review.add_argument(
        "--qa-report",
        type=Path,
        default=PROCESSED_DATA_DIR / "topology_qa.json",
        help="Topology QA JSON report. Defaults to data/processed/topology_qa.json. Missing files are skipped.",
    )
    review.add_argument(
        "--scenario",
        default=None,
        help=(
            "Optional scenario id to load ownership choropleth layers, politics QA, "
            "and curator province-override authoring."
        ),
    )
    review.add_argument(
        "--scenario-path",
        type=Path,
        default=None,
        help="Optional explicit scenario JSON path (enables authoring against that file).",
    )
    review.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host interface for the local review server. Defaults to 127.0.0.1.",
    )
    review.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Port for the local review server. Defaults to 8765.",
    )
    review.add_argument(
        "--no-open",
        action="store_true",
        help="Do not open a browser tab automatically.",
    )
    review.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Startup summary format. The server still starts after printing JSON.",
    )
    review.set_defaults(handler=_review)

    release = subcommands.add_parser(
        "release",
        help="Package public dataset releases with recipes, attribution, and accuracy labels.",
    )
    release_commands = release.add_subparsers(dest="command")
    alpha = release_commands.add_parser(
        "alpha",
        help=(
            "Build an M9 public alpha release bundle: game pack, sample layers, "
            "reproducible recipe, attribution, and honest accuracy labeling."
        ),
    )
    _add_profile_arg(alpha)
    alpha.add_argument(
        "--province-input",
        type=Path,
        default=PROCESSED_DATA_DIR / "provinces.geojson",
        help="Land province GeoJSON input. Defaults to data/processed/provinces.geojson.",
    )
    alpha.add_argument(
        "--sea-input",
        type=Path,
        default=None,
        help="Sea-zone GeoJSON. Defaults to sea_zones.geojson next to provinces when present.",
    )
    alpha.add_argument(
        "--adjacency-input",
        type=Path,
        default=None,
        help="Adjacency CSV. Defaults to adjacency.csv next to provinces when present.",
    )
    alpha.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=(
            "Release output directory. Defaults to releases/<tag>/. "
            f"Use {SAMPLE_DIR}/<name> for commit-friendly samples."
        ),
    )
    alpha.add_argument(
        "--tag",
        default=None,
        help="Release tag (also used as default directory name). Defaults to alpha-<version>-<date>.",
    )
    alpha.add_argument(
        "--scenario",
        action="append",
        dest="scenarios",
        help=(
            "Scenario id to embed. May be repeated. "
            "Defaults to modern-baseline and demo-1444 when neither --scenario nor "
            "--no-scenarios is given."
        ),
    )
    alpha.add_argument(
        "--no-scenarios",
        action="store_true",
        help="Do not embed any scenarios in the alpha pack.",
    )
    alpha.add_argument(
        "--country",
        action="append",
        dest="countries",
        help=(
            "Modern parent_country_id filter for a sample subset (e.g. FRA). "
            "May be repeated. When set, only matching land provinces (and linked coastal seas) "
            "are packaged. Defaults to no filter (full input)."
        ),
    )
    alpha.add_argument(
        "--sample-we",
        action="store_true",
        help=(
            "Convenience: sample Western Europe scaffold countries "
            f"({', '.join(DEFAULT_SAMPLE_COUNTRIES)})."
        ),
    )
    alpha.add_argument(
        "--allow-unknown-overrides",
        action="store_true",
        help="When embedding scenarios, ignore province_overrides that do not match land IDs.",
    )
    alpha.add_argument(
        "--data-vintage",
        default=None,
        help="Optional data vintage label (defaults to UTC date of packaging).",
    )
    alpha.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format for the release summary.",
    )
    alpha.set_defaults(handler=_release_alpha)

    beta = release_commands.add_parser(
        "beta",
        help=(
            "Build an M14 license-audited beta release: game + atlas faces, "
            "cleaned attribution pack, restricted-path isolation audit."
        ),
    )
    _add_profile_arg(beta)
    beta.add_argument(
        "--province-input",
        type=Path,
        default=PROCESSED_DATA_DIR / "provinces.geojson",
        help="Land province GeoJSON input. Defaults to data/processed/provinces.geojson.",
    )
    beta.add_argument(
        "--sea-input",
        type=Path,
        default=None,
        help="Sea-zone GeoJSON. Defaults to sea_zones.geojson next to provinces when present.",
    )
    beta.add_argument(
        "--adjacency-input",
        type=Path,
        default=None,
        help="Adjacency CSV. Defaults to adjacency.csv next to provinces when present.",
    )
    beta.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=(
            "Release output directory. Defaults to releases/<tag>/. "
            f"Use {SAMPLE_DIR}/<name> for commit-friendly samples."
        ),
    )
    beta.add_argument(
        "--tag",
        default=None,
        help="Release tag (also used as default directory name). Defaults to beta-<version>-<date>.",
    )
    beta.add_argument(
        "--scenario",
        action="append",
        dest="scenarios",
        help=(
            "Scenario id to embed. May be repeated. "
            "Defaults to modern-baseline, official-1836, and official-1444 when neither "
            "--scenario nor --no-scenarios is given."
        ),
    )
    beta.add_argument(
        "--no-scenarios",
        action="store_true",
        help="Do not embed any scenarios (also disables the atlas face).",
    )
    beta.add_argument(
        "--country",
        action="append",
        dest="countries",
        help=(
            "Modern parent_country_id filter for a sample subset (e.g. FRA). "
            "May be repeated. When set, only matching land provinces (and linked coastal seas) "
            "are packaged. Defaults to no filter (full input)."
        ),
    )
    beta.add_argument(
        "--sample-we",
        action="store_true",
        help=(
            "Convenience: sample Western Europe scaffold countries "
            f"({', '.join(DEFAULT_SAMPLE_COUNTRIES)})."
        ),
    )
    beta.add_argument(
        "--allow-unknown-overrides",
        action="store_true",
        help="When embedding scenarios, ignore province_overrides that do not match land IDs.",
    )
    beta.add_argument(
        "--no-atlas",
        action="store_true",
        help="Skip the atlas / SaaS face (game pack only).",
    )
    beta.add_argument(
        "--allow-license-errors",
        action="store_true",
        help=(
            "Do not fail the release when the license audit reports errors "
            "(still writes license_audit.json). Not recommended for public packaging."
        ),
    )
    beta.add_argument(
        "--data-vintage",
        default=None,
        help="Optional data vintage label (defaults to UTC date of packaging).",
    )
    beta.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format for the release summary.",
    )
    beta.set_defaults(handler=_release_beta)

    site = release_commands.add_parser(
        "site",
        help=(
            "M14.5 public landing page: validate static site under landing/, "
            "optionally ensure a GitHub repo, commit/push, and deploy to Vercel."
        ),
    )
    site.add_argument(
        "--landing-dir",
        type=Path,
        default=None,
        help="Landing site directory. Defaults to <project-root>/landing/.",
    )
    site.add_argument(
        "--ensure-repo",
        action="store_true",
        help=(
            "If git remote 'origin' (or --remote) is missing, create a GitHub "
            "repository with the gh CLI and attach it as the remote."
        ),
    )
    site.add_argument(
        "--repo-name",
        default=None,
        help="GitHub repository name when using --ensure-repo. Defaults to the project directory name.",
    )
    site.add_argument(
        "--repo-owner",
        default=None,
        help="GitHub owner/org for --ensure-repo. Defaults to the authenticated gh user.",
    )
    site.add_argument(
        "--private",
        action="store_true",
        help="Create a private GitHub repository when using --ensure-repo (default: public).",
    )
    site.add_argument(
        "--remote",
        default="origin",
        help="Git remote name for ensure/push. Defaults to origin.",
    )
    site.add_argument(
        "--push",
        action="store_true",
        help="Commit landing page changes (if any) and push the current branch.",
    )
    site.add_argument(
        "--branch",
        default=None,
        help="Branch to push. Defaults to the current branch.",
    )
    site.add_argument(
        "--commit-message",
        default=None,
        help="Commit message used when --push creates a commit.",
    )
    site.add_argument(
        "--deploy",
        action="store_true",
        help="Deploy landing/ to Vercel with the vercel CLI (requires auth).",
    )
    site.add_argument(
        "--preview",
        action="store_true",
        help="With --deploy, create a preview deployment instead of production.",
    )
    site.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate only; skip ensure-repo, push, and deploy side effects.",
    )
    site.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format for the release summary.",
    )
    site.set_defaults(handler=_release_site)

    era_geometry = subcommands.add_parser(
        "era-geometry",
        help=(
            "M15 era-aware geometry packs: list, validate, and apply boundary "
            "hints / hard province overrides with ID lineage maps."
        ),
    )
    era_commands = era_geometry.add_subparsers(dest="command")
    era_list = era_commands.add_parser(
        "list",
        help="List bundled era-geometry packs under configs/era_geometry/.",
    )
    era_list.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format.",
    )
    era_list.set_defaults(handler=_era_geometry_list)

    era_validate = era_commands.add_parser(
        "validate",
        help="Validate an era-geometry pack definition.",
    )
    era_validate.add_argument(
        "--pack",
        required=True,
        help="Pack id (filename stem under configs/era_geometry/) or path.",
    )
    era_validate.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format.",
    )
    era_validate.set_defaults(handler=_era_geometry_validate)

    era_apply = era_commands.add_parser(
        "apply",
        help=(
            "Apply an era-geometry pack to a scaffold province layer. Writes "
            "period provinces, boundary hints, lineage maps, and a manifest."
        ),
    )
    era_apply.add_argument(
        "--pack",
        required=True,
        help="Pack id (filename stem under configs/era_geometry/) or path.",
    )
    era_apply.add_argument(
        "--province-input",
        type=Path,
        default=PROCESSED_DATA_DIR / "provinces.geojson",
        help="Scaffold province GeoJSON. Defaults to data/processed/provinces.geojson.",
    )
    era_apply.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=(
            "Output directory. Defaults to "
            "data/processed/era_geometry/<pack-id>/."
        ),
    )
    era_apply.add_argument(
        "--recompute-adjacency",
        action="store_true",
        help="Recompute land adjacency for the era province layer after apply.",
    )
    _add_profile_arg(era_apply)
    era_apply.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format for the apply summary.",
    )
    era_apply.set_defaults(handler=_era_geometry_apply)

    multi_era = subcommands.add_parser(
        "multi-era",
        help=(
            "M16 multi-era geometry + politics packs: list, validate, build, "
            "and emit migration notes with per-region quality tiers."
        ),
    )
    multi_commands = multi_era.add_subparsers(dest="command")
    multi_list = multi_commands.add_parser(
        "list",
        help="List bundled multi-era packs under configs/multi_era/.",
    )
    multi_list.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format.",
    )
    multi_list.set_defaults(handler=_multi_era_list)

    multi_validate = multi_commands.add_parser(
        "validate",
        help="Validate a multi-era pack definition.",
    )
    multi_validate.add_argument(
        "--pack",
        required=True,
        help="Pack id (filename stem under configs/multi_era/) or path.",
    )
    multi_validate.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format.",
    )
    multi_validate.set_defaults(handler=_multi_era_validate)

    multi_build = multi_commands.add_parser(
        "build",
        help=(
            "Build a multi-era package: apply linked geometry packs, resolve "
            "scenario politics, write region quality matrix and migration notes."
        ),
    )
    multi_build.add_argument(
        "--pack",
        required=True,
        help="Pack id (filename stem under configs/multi_era/) or path.",
    )
    multi_build.add_argument(
        "--province-input",
        type=Path,
        default=PROCESSED_DATA_DIR / "provinces.geojson",
        help="Scaffold province GeoJSON. Defaults to data/processed/provinces.geojson.",
    )
    multi_build.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory. Defaults to data/processed/multi_era/<pack-id>/.",
    )
    multi_build.add_argument(
        "--recompute-adjacency",
        action="store_true",
        help="Recompute land adjacency after each era-geometry apply.",
    )
    multi_build.add_argument(
        "--no-geometry",
        action="store_true",
        help="Skip era-geometry apply; copy scaffold provinces per era.",
    )
    multi_build.add_argument(
        "--no-politics",
        action="store_true",
        help="Skip scenario ownership resolve.",
    )
    _add_profile_arg(multi_build)
    multi_build.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format for the build summary.",
    )
    multi_build.set_defaults(handler=_multi_era_build)

    multi_migration = multi_commands.add_parser(
        "migration",
        help="Emit migration notes (JSON + Markdown) for a multi-era pack.",
    )
    multi_migration.add_argument(
        "--pack",
        required=True,
        help="Pack id (filename stem under configs/multi_era/) or path.",
    )
    multi_migration.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional directory to write migration_notes.json and MIGRATION.md.",
    )
    multi_migration.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
        help="Stdout format (files written when --output-dir is set).",
    )
    multi_migration.set_defaults(handler=_multi_era_migration)

    curation = subcommands.add_parser(
        "curation",
        help=(
            "M17 curation workflow: external curator bundles, ownership diffs, "
            "golden-border suites, and contribution checklists."
        ),
    )
    curation_commands = curation.add_subparsers(dest="command")

    curation_list = curation_commands.add_parser(
        "list",
        help="List discovered curator bundles under samples/ (and bundles/).",
    )
    curation_list.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format.",
    )
    curation_list.set_defaults(handler=_curation_list)

    curation_validate = curation_commands.add_parser(
        "validate",
        help="Validate an external curator bundle manifest and scenario files.",
    )
    curation_validate.add_argument(
        "--bundle",
        required=True,
        help="Bundle id, directory path, or path to bundle_manifest.json.",
    )
    curation_validate.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format.",
    )
    curation_validate.set_defaults(handler=_curation_validate)

    curation_import = curation_commands.add_parser(
        "import",
        help="Copy a validated curator bundle into an output directory.",
    )
    curation_import.add_argument(
        "--bundle",
        required=True,
        help="Bundle id, directory path, or path to bundle_manifest.json.",
    )
    curation_import.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Destination directory for the imported bundle.",
    )
    curation_import.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace the output directory if it already has files.",
    )
    curation_import.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format.",
    )
    curation_import.set_defaults(handler=_curation_import)

    curation_diff = curation_commands.add_parser(
        "diff",
        help=(
            "Diff ownership between two scenarios or ownership tables: "
            "tag counts, owner/controller/disputed changes, contested provinces."
        ),
    )
    curation_diff.add_argument(
        "--base-scenario",
        default=None,
        help="Base scenario id under configs/scenarios/.",
    )
    curation_diff.add_argument(
        "--base-scenario-path",
        type=Path,
        default=None,
        help="Base scenario JSON path.",
    )
    curation_diff.add_argument(
        "--base-ownership",
        type=Path,
        default=None,
        help="Base ownership CSV/JSON (skips resolve for the base side).",
    )
    curation_diff.add_argument(
        "--target-scenario",
        default=None,
        help="Target scenario id under configs/scenarios/.",
    )
    curation_diff.add_argument(
        "--target-scenario-path",
        type=Path,
        default=None,
        help="Target scenario JSON path.",
    )
    curation_diff.add_argument(
        "--target-ownership",
        type=Path,
        default=None,
        help="Target ownership CSV/JSON (skips resolve for the target side).",
    )
    curation_diff.add_argument(
        "--province-input",
        type=Path,
        default=PROCESSED_DATA_DIR / "provinces.geojson",
        help="Land province GeoJSON when resolving scenarios. Defaults to data/processed/provinces.geojson.",
    )
    curation_diff.add_argument(
        "--report-output",
        type=Path,
        default=None,
        help="Optional JSON report path (scenario ownership diff).",
    )
    curation_diff.add_argument(
        "--max-changes",
        type=int,
        default=None,
        help="Truncate the change list in the report to this many rows.",
    )
    curation_diff.add_argument(
        "--allow-unknown-overrides",
        action="store_true",
        help="Ignore province_overrides that do not match land province IDs when resolving.",
    )
    curation_diff.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format for the diff summary.",
    )
    curation_diff.set_defaults(handler=_curation_diff)

    curation_checklist = curation_commands.add_parser(
        "checklist",
        help="Run the community contribution checklist against a curator bundle.",
    )
    curation_checklist.add_argument(
        "--bundle",
        required=True,
        help="Bundle id, directory path, or path to bundle_manifest.json.",
    )
    curation_checklist.add_argument(
        "--require-qa-claimed",
        action="store_true",
        help="Treat missing checklist.qa_pass_claimed as a hard failure.",
    )
    curation_checklist.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format.",
    )
    curation_checklist.set_defaults(handler=_curation_checklist)

    demo = subcommands.add_parser(
        "demo",
        help="Build and refresh the landing-page interactive demo data pack.",
    )
    demo_commands = demo.add_subparsers(dest="command")
    demo_build = demo_commands.add_parser(
        "build",
        help=(
            "Regenerate landing/demo/data from the processed global build: atlas exports, "
            "per-scenario PMTiles, hierarchy overlays, adjacency lines, and the demo manifest."
        ),
    )
    _add_profile_arg(demo_build)
    demo_build.add_argument(
        "--province-input",
        type=Path,
        default=PROCESSED_DATA_DIR / "provinces.geojson",
        help="Province GeoJSON input. Defaults to data/processed/provinces.geojson.",
    )
    demo_build.add_argument(
        "--adjacency-input",
        type=Path,
        default=PROCESSED_DATA_DIR / "adjacency.csv",
        help="Adjacency CSV input. Defaults to data/processed/adjacency.csv.",
    )
    demo_build.add_argument(
        "--hierarchy-input",
        type=Path,
        default=PROCESSED_DATA_DIR / "hierarchy.geojson",
        help="Hierarchy GeoJSON input. Defaults to data/processed/hierarchy.geojson.",
    )
    demo_build.add_argument(
        "--landing-dir",
        type=Path,
        help="Landing site directory. Defaults to <project>/landing.",
    )
    demo_build.add_argument(
        "--work-dir",
        type=Path,
        help="Temporary build directory. Defaults to data/processed/demo_build.",
    )
    demo_build.add_argument(
        "--scenario",
        action="append",
        default=[],
        help="Scenario id to include; may be repeated. Defaults to the four demo eras.",
    )
    demo_build.add_argument(
        "--tile-min-zoom",
        type=int,
        default=0,
        help="Minimum PMTiles zoom. Defaults to 0.",
    )
    demo_build.add_argument(
        "--tile-max-zoom",
        type=int,
        default=7,
        help="Maximum PMTiles zoom. Defaults to 7 (native backend); use 10 with tippecanoe.",
    )
    demo_build.add_argument(
        "--no-tippecanoe",
        action="store_true",
        help="Force the pure-Python tile backend even when tippecanoe is installed.",
    )
    demo_build.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip the landing-site validation step after the build.",
    )
    demo_build.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format for the build summary.",
    )
    demo_build.set_defaults(handler=_demo_build)

    return parser


def _add_profile_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--profile",
        default=DEFAULT_PROFILE_ID,
        help=f"Generation profile id. Defaults to {DEFAULT_PROFILE_ID}.",
    )


def _add_source_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--source",
        action="append",
        dest="sources",
        help="Source id to plan. May be provided more than once. Defaults to profile sources.default.",
    )


def _add_raw_dir_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=RAW_DATA_DIR,
        help=f"Directory for raw source artifacts. Defaults to {RAW_DATA_DIR}.",
    )


def _add_export_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--province-input",
        type=Path,
        default=PROCESSED_DATA_DIR / "provinces.geojson",
        help="Land province GeoJSON input. Defaults to data/processed/provinces.geojson.",
    )
    parser.add_argument(
        "--sea-input",
        type=Path,
        default=None,
        help=(
            "Sea-zone GeoJSON input. Defaults to sea_zones.geojson next to the province "
            "input when present; omitted when missing or when the profile disables seas."
        ),
    )
    parser.add_argument(
        "--adjacency-input",
        type=Path,
        default=None,
        help=(
            "Adjacency CSV input for full packs. Defaults to adjacency.csv next to the "
            "province input when present. Ignored by export geojson."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=f"Pack output directory. Defaults to {EXPORT_DIR}/<profile-id>.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format for the export summary.",
    )


def _sources_download(args: argparse.Namespace) -> int:
    try:
        adapters = resolve_source_adapters(args.profile, args.sources)
    except (ConfigError, SourceRegistryError) as error:
        _print_error(error)
        return 1

    if args.execute:
        try:
            artifacts_by_source = download_source_artifacts(
                adapters,
                raw_dir=args.raw_dir,
                force=args.force,
                timeout=args.timeout,
            )
            manifest = build_downloaded_source_manifest(args.profile, adapters, artifacts_by_source)
            validate_source_manifest(manifest)
        except SourceArtifactError as error:
            _print_error(error)
            return 1

        manifest_output = args.manifest_output or args.raw_dir / "source_manifest.json"
        manifest_output.parent.mkdir(parents=True, exist_ok=True)
        manifest_output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if args.format == "json":
            print(json.dumps(manifest, indent=2, sort_keys=True))
            return 0

        artifact_count = sum(len(artifacts) for artifacts in artifacts_by_source.values())
        print("gpm sources download: downloaded or verified source artifacts.")
        print(f"Profile: {args.profile}")
        print(f"Raw data dir: {args.raw_dir}")
        print(f"Manifest: {manifest_output}")
        print(f"Artifact records: {artifact_count}")
        for artifacts in artifacts_by_source.values():
            for artifact in artifacts:
                print(f"- {artifact.source_id}/{artifact.layer_id}/{artifact.artifact_id}")
                print(f"  Status: {artifact.status}")
                print(f"  Path: {artifact.path}")
                print(f"  Bytes: {artifact.bytes}")
                print(f"  Checksum: {artifact.checksum}")
        return 0

    records = [record for adapter in adapters for record in adapter.planned_downloads()]
    if args.format == "json":
        print(json.dumps([record.to_dict() for record in records], indent=2, sort_keys=True))
        return 0

    print("gpm sources download: dry run only; no datasets were downloaded.")
    print(f"Profile: {args.profile}")
    print(f"Source plan: {', '.join(f'{adapter.display_name} ({adapter.source_id})' for adapter in adapters)}")
    print(f"Planned records: {len(records)}")
    for record in records:
        print(f"- {record.source_id}/{record.layer_id}")
        print(f"  URL: {record.url}")
        print(f"  Expected path: {record.expected_path}")
        print(f"  License: {record.license}")
        print(
            "  Policy: "
            f"default={record.default}, "
            f"optional={record.optional}, "
            f"isolated={record.isolated}, "
            f"restricted={record.restricted}"
        )
    return 0


def _sources_manifest(args: argparse.Namespace) -> int:
    try:
        if args.from_raw:
            manifest = build_local_source_manifest(args.profile, args.sources, raw_dir=args.raw_dir)
        else:
            manifest = build_planned_source_manifest(args.profile, args.sources)
        validate_source_manifest(manifest)
    except (ConfigError, SourceRegistryError, SourceArtifactError) as error:
        _print_error(error)
        return 1

    encoded = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        print(encoded, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
        print(f"Wrote source manifest: {args.output}")
    return 0


def _build_provinces(args: argparse.Namespace) -> int:
    try:
        result = build_land_province_draft(
            args.profile,
            raw_dir=args.raw_dir,
            intermediate_dir=args.intermediate_dir,
            processed_dir=args.processed_dir,
            candidate_output=args.candidate_output,
            province_output=args.province_output,
            refine=args.refine,
            target_province_count=args.target_province_count,
            population_input=args.population_input,
            settlement_input=args.settlement_input,
            population_license_lineage=tuple(args.population_license),
            settlement_license_lineage=tuple(args.settlement_license),
        )
    except (ConfigError, SourceRegistryError, ProvinceBuildError) as error:
        _print_error(error)
        return 1

    if args.format == "json":
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return 0

    if result.refinement_applied:
        print("gpm build provinces: generated M4 population/settlement-aware land provinces.")
    else:
        print("gpm build provinces: generated M2 first modern land province draft.")
    print(f"Profile: {result.profile_id}; target province count: {result.target_province_count}")
    print(f"Candidate intermediate: {result.candidate_output}")
    print(f"Processed provinces: {result.province_output}")
    print(f"Province features: {result.province_count}")
    print(f"Natural Earth admin-1 features: {result.admin1_count}")
    print(f"Natural Earth admin-0 fallbacks: {result.admin0_fallback_count}")
    if result.refinement_applied:
        print(f"Refinement strategy: {result.refinement_strategy}")
        print(
            "Refinement operations: "
            f"{result.split_count} splits across {result.split_parent_count} parents; "
            f"{result.merged_fragment_count} tiny-fragment merges; "
            f"{result.skipped_invalid_count} invalid source geometries preserved"
        )
        print(
            f"Population samples: {result.population_sample_count}; "
            f"settlements: {result.settlement_count}; population total: {result.population_total}"
        )
    return 0


def _build_adjacency(args: argparse.Namespace) -> int:
    try:
        result = build_land_adjacency(
            args.profile,
            province_input=args.province_input,
            sea_input=args.sea_input,
            output=args.output,
        )
    except (ConfigError, AdjacencyBuildError) as error:
        _print_error(error)
        return 1
    if args.format == "json":
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return 0
    if result.sea_zone_count:
        print("gpm build adjacency: generated land and marine adjacency.")
    else:
        print("gpm build adjacency: generated canonical undirected land adjacency.")
    print(f"Profile: {result.profile_id}")
    print(f"Province input: {result.province_input}")
    print(f"Sea input: {result.sea_input or '(none)'}")
    print(f"Adjacency output: {result.output}")
    print(f"Land provinces: {result.province_count}; sea zones: {result.sea_zone_count}")
    print(f"Spatial-index candidate pairs: {result.candidate_pair_count}")
    print(
        "Adjacency rows: "
        f"{result.adjacency_count} total "
        f"({result.land_adjacency_count} land, "
        f"{result.sea_adjacency_count} sea, "
        f"{result.port_to_sea_count} port_to_sea, "
        f"{result.strait_count} strait)"
    )
    print(f"Minimum shared border: {result.min_shared_border_km} km")
    if result.strait_max_distance_km is not None:
        print(f"Strait max distance: {result.strait_max_distance_km} km")
    return 0


def _build_hierarchy(args: argparse.Namespace) -> int:
    try:
        result = build_hierarchy(
            args.profile,
            province_input=args.province_input,
            adjacency_input=args.adjacency_input,
            raw_dir=args.raw_dir,
            output=args.output,
            update_provinces=not args.no_update_provinces,
            province_output=args.province_output,
        )
    except (ConfigError, HierarchyBuildError) as error:
        _print_error(error)
        return 1
    if args.format == "json":
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return 0
    print("gpm build hierarchy: generated M21 area/region/superregion hierarchy.")
    print(f"Profile: {result.profile_id}")
    print(f"Province input: {result.province_input}")
    print(f"Adjacency input: {result.adjacency_input}")
    print(f"Hierarchy output: {result.output}")
    print(
        f"Entities: {result.area_count} areas, {result.region_count} regions, "
        f"{result.superregion_count} superregions over {result.province_count} land provinces"
    )
    if result.province_output:
        print(f"Enriched provinces: {result.province_output} ({result.updated_province_count} updated)")
    else:
        print("Province enrichment skipped (--no-update-provinces).")
    if not result.natural_earth_attributes:
        print(
            "Natural Earth attribute zips not found; used one-region-per-country and "
            "a single fallback superregion."
        )
    return 0


def _demo_build(args: argparse.Namespace) -> int:
    scenarios = tuple(args.scenario) if args.scenario else DEMO_SCENARIOS
    try:
        result = build_demo(
            args.profile,
            province_input=args.province_input,
            adjacency_input=args.adjacency_input,
            hierarchy_input=args.hierarchy_input,
            landing_dir=args.landing_dir,
            work_dir=args.work_dir,
            scenarios=scenarios,
            tile_min_zoom=args.tile_min_zoom,
            tile_max_zoom=args.tile_max_zoom,
            prefer_tippecanoe=not args.no_tippecanoe,
            validate=not args.no_validate,
        )
    except (ConfigError, DemoBuildError, ReleaseError) as error:
        _print_error(error)
        return 1
    if args.format == "json":
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return 0
    print("gpm demo build: refreshed the landing demo data pack.")
    print(f"Profile: {result.profile_id}")
    print(f"Demo data: {result.landing_data_dir}")
    print(f"Scenarios: {', '.join(result.scenario_ids)}")
    print(
        f"Tiles: backend {result.tile_backend}, zoom {result.tile_min_zoom}–{result.tile_max_zoom}"
    )
    print(
        "Hierarchy overlays: "
        f"{result.hierarchy_counts['areas']} areas, "
        f"{result.hierarchy_counts['regions']} regions, "
        f"{result.hierarchy_counts['superregions']} superregions"
    )
    print(f"Adjacency edges: {result.adjacency_edge_count}")
    if result.dropped_files:
        print(f"Dropped legacy demo files: {', '.join(result.dropped_files)}")
    print(f"Landing-site validation: {'passed' if result.validated else 'skipped'}")
    return 0


def _build_seas(args: argparse.Namespace) -> int:
    try:
        result = build_sea_zones(
            args.profile,
            province_input=args.province_input,
            sea_output=args.sea_output,
            province_output=args.province_output,
            raw_dir=args.raw_dir,
            update_provinces=not args.no_update_provinces,
        )
    except (ConfigError, SeaBuildError) as error:
        _print_error(error)
        return 1
    if args.format == "json":
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return 0
    print("gpm build seas: generated coastal and ocean sea zones.")
    print(f"Profile: {result.profile_id}; strategy: {result.strategy}")
    print(f"Province input: {result.province_input}")
    print(f"Sea output: {result.sea_output}")
    print(f"Province coastal updates: {result.province_output or '(skipped)'}")
    print(f"Land mask: {result.land_mask_source}")
    print(
        f"Sea zones: {result.sea_zone_count} "
        f"({result.coastal_sea_zone_count} coastal, {result.ocean_sea_zone_count} ocean)"
    )
    print(
        f"Coastal land provinces: {result.coastal_province_count} / {result.land_province_count}"
    )
    print(
        f"Coastal buffer: {result.coastal_buffer_km} km; "
        f"ocean cell: {result.ocean_cell_size_deg}°; "
        f"strait max: {result.strait_max_distance_km} km"
    )
    return 0


def _export_geojson(args: argparse.Namespace) -> int:
    try:
        result = export_geojson_pack(
            args.profile,
            province_input=args.province_input,
            sea_input=args.sea_input,
            adjacency_input=args.adjacency_input,
            output_dir=args.output_dir,
        )
    except (ConfigError, ExportError) as error:
        _print_error(error)
        return 1
    return _print_export_result(result, args.format, command="export geojson")


def _export_pack(args: argparse.Namespace) -> int:
    try:
        result = export_game_pack(
            args.profile,
            province_input=args.province_input,
            sea_input=args.sea_input,
            adjacency_input=args.adjacency_input,
            output_dir=args.output_dir,
            scenarios=tuple(args.scenarios or ()),
            allow_unknown_overrides=bool(args.allow_unknown_overrides),
        )
    except (ConfigError, ExportError, ScenarioError) as error:
        _print_error(error)
        return 1
    return _print_export_result(result, args.format, command="export pack")


def _export_atlas(args: argparse.Namespace) -> int:
    try:
        result = export_atlas_pack(
            args.profile,
            province_input=args.province_input,
            output_dir=args.output_dir,
            scenarios=tuple(args.scenarios) if args.scenarios else None,
            allow_unknown_overrides=bool(args.allow_unknown_overrides),
            include_base_geometry=not bool(args.no_base_geometry),
            include_owner_dissolve=not bool(args.no_owner_dissolve),
            include_identity_paint=not bool(args.no_identity_paint),
            include_identity_dissolve=not bool(args.no_identity_dissolve),
            include_tiles=bool(args.tiles),
            tile_min_zoom=int(args.tile_min_zoom),
            tile_max_zoom=int(args.tile_max_zoom),
            prefer_tippecanoe=not bool(args.no_tippecanoe),
        )
    except (ConfigError, ExportError, ScenarioError) as error:
        _print_error(error)
        return 1
    return _print_atlas_result(result, args.format)


def _export_tiles(args: argparse.Namespace) -> int:
    try:
        if args.atlas_dir is not None:
            results = export_tiles_from_atlas(
                args.atlas_dir,
                scenarios=tuple(args.scenarios) if args.scenarios else None,
                min_zoom=int(args.min_zoom),
                max_zoom=int(args.max_zoom),
                prefer_tippecanoe=not bool(args.no_tippecanoe),
                include_base=not bool(args.no_base),
            )
            if args.format == "json":
                print(
                    json.dumps(
                        [item.to_dict() for item in results],
                        indent=2,
                        sort_keys=True,
                    )
                )
                return 0
            print(f"gpm export tiles: wrote {len(results)} PMTiles archive(s) from atlas.")
            for item in results:
                print(
                    f"- {item.output_path} "
                    f"({item.feature_count} features, {item.tile_count} tiles, "
                    f"z{item.min_zoom}-{item.max_zoom}, backend={item.backend})"
                )
            return 0

        if args.input is None:
            _print_error("gpm export tiles requires --input GeoJSON or --atlas-dir.")
            return 1

        if args.output is not None:
            from gpm.tiles import build_pmtiles_from_geojson

            result = build_pmtiles_from_geojson(
                args.input,
                args.output,
                layer_name=args.layer,
                min_zoom=int(args.min_zoom),
                max_zoom=int(args.max_zoom),
                prefer_tippecanoe=not bool(args.no_tippecanoe),
            )
        else:
            result = export_tiles_pack(
                input_geojson=args.input,
                output_dir=args.output_dir,
                layer_name=args.layer,
                min_zoom=int(args.min_zoom),
                max_zoom=int(args.max_zoom),
                prefer_tippecanoe=not bool(args.no_tippecanoe),
            )
    except (TileBuildError, OSError) as error:
        _print_error(error)
        return 1
    return _print_tiles_result(result, args.format)


def _scenario_list(args: argparse.Namespace) -> int:
    summaries = list_scenarios()
    if args.format == "json":
        print(json.dumps([item.to_dict() for item in summaries], indent=2, sort_keys=True))
        return 0
    if not summaries:
        print("gpm scenario list: no scenario definitions found under configs/scenarios/.")
        return 0
    print(f"gpm scenario list: {len(summaries)} scenario(s).")
    for item in summaries:
        tier = item.quality_tier or "unspecified"
        official = " official" if item.official_era else ""
        print(
            f"- {item.scenario_id}: {item.label} "
            f"(era={item.era}, start={item.start_date}, "
            f"tier={tier}{official}, "
            f"rules={item.country_rule_count}c/{item.region_rule_count}r/"
            f"{item.province_override_count}p)"
        )
    return 0


def _scenario_validate(args: argparse.Namespace) -> int:
    try:
        scenario = load_scenario(
            args.scenario,
            scenario_path=args.scenario_path,
        )
    except ScenarioError as error:
        _print_error(error)
        return 1
    payload = {
        "scenario_id": scenario["scenario_id"],
        "label": scenario["label"],
        "era": scenario["era"],
        "start_date": scenario["start_date"],
        "end_date": scenario.get("end_date"),
        "path": scenario.get("_path"),
        "quality_tier": scenario.get("quality_tier"),
        "official_era": bool(scenario.get("official_era", False)),
        "recommended_profile": scenario.get("recommended_profile"),
        "priority_theaters": list(scenario.get("priority_theaters") or []),
        "country_rule_count": len(scenario.get("country_rules") or []),
        "region_rule_count": len(scenario.get("region_rules") or []),
        "province_override_count": len(scenario.get("province_overrides") or []),
        "country_definition_count": len(scenario.get("countries") or {}),
        "valid": True,
    }
    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    print("gpm scenario validate: ok.")
    print(f"Scenario: {payload['scenario_id']} ({payload['label']})")
    print(f"Path: {payload['path']}")
    print(f"Era: {payload['era']}; start: {payload['start_date']}; end: {payload['end_date']}")
    tier = payload["quality_tier"] or "unspecified"
    official = "yes" if payload["official_era"] else "no"
    print(f"Quality tier: {tier}; official era: {official}")
    if payload["recommended_profile"]:
        print(f"Recommended profile: {payload['recommended_profile']}")
    if payload["priority_theaters"]:
        print(f"Priority theaters: {', '.join(payload['priority_theaters'])}")
    print(
        "Rules: "
        f"{payload['country_rule_count']} country, "
        f"{payload['region_rule_count']} region, "
        f"{payload['province_override_count']} province overrides; "
        f"{payload['country_definition_count']} country definitions"
    )
    return 0


def _scenario_build(args: argparse.Namespace) -> int:
    try:
        result = build_scenario_ownership(
            args.scenario,
            profile_id=args.profile,
            province_input=args.province_input,
            output_dir=args.output_dir,
            scenario_path=args.scenario_path,
            allow_unknown_overrides=bool(args.allow_unknown_overrides),
        )
    except (ConfigError, ScenarioError) as error:
        _print_error(error)
        return 1
    if args.format == "json":
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return 0
    print("gpm scenario build: wrote ownership overlay tables.")
    print(f"Scenario: {result.scenario_id}; era: {result.era}; start: {result.start_date}")
    print(f"Profile: {result.profile_id}")
    print(f"Province input: {result.province_input}")
    print(f"Output: {result.output_dir}")
    print(f"Manifest: {result.scenario_manifest}")
    print(
        f"Rows: {result.ownership_row_count} ownership "
        f"({result.land_province_count} land provinces); "
        f"{result.owner_tag_count} owner tags"
    )
    print(
        "Assignment hits: "
        f"{result.country_rule_hits} country_rule, "
        f"{result.region_rule_hits} region_rule, "
        f"{result.province_override_hits} province_override, "
        f"{result.baseline_only_count} baseline-only"
    )
    if result.unknown_override_count:
        print(f"Unknown province overrides ignored: {result.unknown_override_count}")
    print(f"Files written: {len(result.files_written)}")
    for path in result.files_written:
        print(f"- {path}")
    return 0


def _release_alpha(args: argparse.Namespace) -> int:
    if args.no_scenarios:
        scenarios: tuple[str, ...] = ()
    elif args.scenarios:
        scenarios = tuple(args.scenarios)
    else:
        scenarios = DEFAULT_ALPHA_SCENARIOS

    if args.sample_we:
        countries = list(DEFAULT_SAMPLE_COUNTRIES)
        if args.countries:
            countries.extend(args.countries)
    else:
        countries = list(args.countries or [])

    try:
        result = build_alpha_release(
            args.profile,
            province_input=args.province_input,
            sea_input=args.sea_input,
            adjacency_input=args.adjacency_input,
            output_dir=args.output_dir,
            release_tag=args.tag,
            scenarios=scenarios,
            sample_countries=countries or None,
            allow_unknown_overrides=bool(args.allow_unknown_overrides),
            data_vintage=args.data_vintage,
        )
    except (ConfigError, ReleaseError, ExportError, ScenarioError) as error:
        _print_error(error)
        return 1

    if args.format == "json":
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return 0

    sample_note = (
        f"sample countries={', '.join(result.sample_countries)}"
        if result.is_sample
        else "full processed input"
    )
    print("gpm release alpha: packaged public alpha dataset release.")
    print(f"Tag: {result.release_tag}")
    print(f"Profile: {result.profile_id}")
    print(f"Output: {result.output_dir}")
    print(f"Manifest: {result.release_manifest}")
    print(f"Pack: {result.pack_dir}")
    print(
        f"Quality: geometry={result.geometry_quality_tier}, "
        f"politics={result.politics_quality_tier}"
    )
    print(
        f"Counts: {result.province_count} provinces, "
        f"{result.sea_zone_count} sea zones, "
        f"{result.adjacency_count} adjacency rows ({sample_note})"
    )
    scenarios_text = ", ".join(result.scenario_ids) if result.scenario_ids else "(none)"
    print(f"Scenarios: {scenarios_text}")
    print(f"Files written: {len(result.files_written)}")
    for path in result.files_written:
        print(f"- {path}")
    return 0


def _release_site(args: argparse.Namespace) -> int:
    try:
        result = release_landing_site(
            landing_dir=args.landing_dir,
            ensure_repo=bool(args.ensure_repo),
            repo_name=args.repo_name,
            repo_owner=args.repo_owner,
            repo_visibility="private" if args.private else "public",
            remote_name=args.remote,
            push=bool(args.push),
            commit_message=args.commit_message,
            branch=args.branch,
            deploy=bool(args.deploy),
            production=not bool(args.preview),
            dry_run=bool(args.dry_run),
        )
    except ReleaseError as error:
        _print_error(error)
        return 1

    if args.format == "json":
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return 0

    print("gpm release site: M14.5 public landing page.")
    print(f"Landing dir: {result.landing_dir}")
    print(f"Validation: {'passed' if result.validation.valid else 'failed'}")
    print(f"HTML size: {result.validation.html_bytes} bytes")
    if result.dry_run:
        print("Mode: dry-run (no git/Vercel side effects)")
    if result.repo_url:
        created = " (created)" if result.repo_created else ""
        print(f"Repo: {result.repo_url}{created}")
    if result.pushed:
        print(f"Pushed: yes (HEAD {result.commit_sha or 'unknown'})")
    if result.deployed:
        print("Deployed: yes")
        if result.deployment_url:
            print(f"URL: {result.deployment_url}")
        if result.inspect_url:
            print(f"Inspect: {result.inspect_url}")
    elif not result.dry_run and not args.deploy:
        print("Deployed: no (pass --deploy)")
    for message in result.messages:
        print(f"- {message}")
    return 0


def _release_beta(args: argparse.Namespace) -> int:
    if args.no_scenarios:
        scenarios: tuple[str, ...] = ()
        include_atlas = False
    elif args.scenarios:
        scenarios = tuple(args.scenarios)
        include_atlas = not bool(args.no_atlas)
    else:
        scenarios = DEFAULT_BETA_SCENARIOS
        include_atlas = not bool(args.no_atlas)

    if args.sample_we:
        countries = list(DEFAULT_SAMPLE_COUNTRIES)
        if args.countries:
            countries.extend(args.countries)
    else:
        countries = list(args.countries or [])

    try:
        result = build_beta_release(
            args.profile,
            province_input=args.province_input,
            sea_input=args.sea_input,
            adjacency_input=args.adjacency_input,
            output_dir=args.output_dir,
            release_tag=args.tag,
            scenarios=scenarios,
            sample_countries=countries or None,
            allow_unknown_overrides=bool(args.allow_unknown_overrides),
            data_vintage=args.data_vintage,
            include_atlas=include_atlas,
            fail_on_license_errors=not bool(args.allow_license_errors),
        )
    except (ConfigError, ReleaseError, ExportError, ScenarioError) as error:
        _print_error(error)
        return 1

    if args.format == "json":
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return 0

    sample_note = (
        f"sample countries={', '.join(result.sample_countries)}"
        if result.is_sample
        else "full processed input"
    )
    print("gpm release beta: packaged license-audited beta dataset release.")
    print(f"Tag: {result.release_tag}")
    print(f"Profile: {result.profile_id}")
    print(f"Output: {result.output_dir}")
    print(f"Manifest: {result.release_manifest}")
    print(f"Game pack: {result.pack_dir}")
    if result.atlas_dir:
        print(f"Atlas pack: {result.atlas_dir}")
    print(
        f"Quality: geometry={result.geometry_quality_tier}, "
        f"politics={result.politics_quality_tier}"
    )
    print(f"License audit: {'passed' if result.license_audit_passed else 'failed'}")
    print(
        f"Counts: {result.province_count} provinces, "
        f"{result.sea_zone_count} sea zones, "
        f"{result.adjacency_count} adjacency rows, "
        f"{result.attribution_record_count} attribution records ({sample_note})"
    )
    scenarios_text = ", ".join(result.scenario_ids) if result.scenario_ids else "(none)"
    print(f"Scenarios: {scenarios_text}")
    print(f"Files written: {len(result.files_written)}")
    for path in result.files_written:
        print(f"- {path}")
    return 0


def _print_export_result(result, format_name: str, *, command: str) -> int:
    if format_name == "json":
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return 0
    print(f"gpm {command}: wrote profile export pack.")
    print(f"Profile: {result.profile_id}; layout: {result.layout}; region type: {result.region_type}")
    print(f"Output: {result.output_dir}")
    print(f"Manifest: {result.pack_manifest}")
    print(
        f"Counts: {result.province_count} provinces, "
        f"{result.sea_zone_count} sea zones, "
        f"{result.region_count} regions, "
        f"{result.adjacency_count} adjacency rows"
    )
    if result.localization_entry_count:
        print(
            f"Localization entries: {result.localization_entry_count}; "
            f"attribution records: {result.attribution_record_count}"
        )
    if result.scenario_ids:
        print(
            f"Scenarios: {', '.join(result.scenario_ids)} "
            f"({result.scenario_ownership_row_count} ownership rows)"
        )
    print(f"Files written: {len(result.files_written)}")
    for path in result.files_written:
        print(f"- {path}")
    return 0


def _print_atlas_result(result, format_name: str) -> int:
    if format_name == "json":
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return 0
    print("gpm export atlas: wrote atlas / SaaS pack.")
    print(f"Profile: {result.profile_id}; pack type: {result.pack_type}")
    print(f"Output: {result.output_dir}")
    print(f"Manifest: {result.atlas_manifest}")
    print(
        f"Counts: {result.province_count} provinces, "
        f"{result.scenario_ownership_row_count} ownership rows, "
        f"{result.tag_count} tags, "
        f"{result.legend_entry_count} legend entries"
    )
    scenarios_text = ", ".join(result.scenario_ids) if result.scenario_ids else "(none)"
    print(f"Scenarios: {scenarios_text}")
    print(
        f"Base geometry: {'yes' if result.include_base_geometry else 'no'}; "
        f"owner dissolve: {'yes' if result.include_owner_dissolve else 'no'}; "
        f"identity paint: {'yes' if result.include_identity_paint else 'no'}; "
        f"identity dissolve: {'yes' if result.include_identity_dissolve else 'no'}; "
        f"tiles: {'yes' if result.include_tiles else 'no'}; "
        f"attribution records: {result.attribution_record_count}"
    )
    if result.include_identity_paint:
        print(
            f"Identity: {result.unique_culture_count} cultures, "
            f"{result.unique_religion_count} religions"
        )
    if result.include_tiles:
        print(f"PMTiles files: {result.tile_file_count}")
    print(f"Files written: {len(result.files_written)}")
    for path in result.files_written:
        print(f"- {path}")
    return 0


def _print_tiles_result(result, format_name: str) -> int:
    if format_name == "json":
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return 0
    print("gpm export tiles: wrote PMTiles archive.")
    print(f"Output: {result.output_path}")
    if result.tileset_manifest:
        print(f"Manifest: {result.tileset_manifest}")
    print(
        f"Layer: {result.layer_name}; features: {result.feature_count}; "
        f"tiles: {result.tile_count}; zoom: {result.min_zoom}-{result.max_zoom}; "
        f"backend: {result.backend}"
    )
    west, south, east, north = result.bounds
    print(f"Bounds: west={west:.4f} south={south:.4f} east={east:.4f} north={north:.4f}")
    print(f"Files written: {len(result.files_written)}")
    for path in result.files_written:
        print(f"- {path}")
    return 0


def _qa_topology(args: argparse.Namespace) -> int:
    try:
        result = run_topology_qa(
            args.profile,
            province_input=args.province_input,
            adjacency_input=args.adjacency_input,
            raw_data=args.raw_data,
            report_output=args.report_output,
        )
    except (ConfigError, TopologyQAError) as error:
        _print_error(error)
        return 1
    if args.format == "json":
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        print(f"gpm qa topology: {result.status}.")
        print(f"Profile: {result.profile_id}")
        print(f"Report: {result.report_output}")
        print(f"Provinces: {result.province_count}; adjacency rows: {result.adjacency_count}")
        print(f"Findings: {result.error_count} errors, {result.warning_count} warnings")
        print(f"Analysis: coverage={result.coverage_analysis}, graph={result.graph_analysis}")
    return 0 if result.passed else 1


def _qa_scenario(args: argparse.Namespace) -> int:
    try:
        result = run_scenario_politics_qa(
            args.profile,
            args.scenario,
            province_input=args.province_input,
            adjacency_input=args.adjacency_input,
            scenario_path=args.scenario_path,
            ownership_input=args.ownership_input,
            golden_input=args.golden,
            report_output=args.report_output,
            allow_unknown_overrides=bool(args.allow_unknown_overrides),
            max_owner_components=int(args.max_owner_components),
            min_provinces_for_fragment_check=int(args.min_provinces_for_fragment_check),
        )
    except (ConfigError, ScenarioPoliticsQAError, ScenarioError) as error:
        _print_error(error)
        return 1
    if args.format == "json":
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        print(f"gpm qa scenario: {result.status}.")
        print(f"Profile: {result.profile_id}; scenario: {result.scenario_id}")
        print(f"Report: {result.report_output}")
        print(
            f"Rows: {result.ownership_row_count} ownership "
            f"({result.land_province_count} land provinces); "
            f"{result.owner_tag_count} owner tags"
        )
        print(f"Findings: {result.error_count} errors, {result.warning_count} warnings")
        print(
            f"Analysis: adjacency={result.adjacency_analysis}, golden={result.golden_analysis}"
        )
    return 0 if result.passed else 1


def _qa_render(args: argparse.Namespace) -> int:
    if _load_profile_or_report(args.profile) is None:
        return 1
    print("gpm qa render: Phase 1 placeholder; render snapshots are not implemented yet.")
    print(f"Profile: {args.profile}")
    print("Use `gpm review` for the interactive MapLibre review viewer.")
    print("Use `gpm qa scenario --scenario <id>` for automated politics QA.")
    return 0


def _review(args: argparse.Namespace) -> int:
    try:
        dataset = prepare_review_dataset(
            args.profile,
            province_input=args.province_input,
            adjacency_input=args.adjacency_input,
            qa_report_input=args.qa_report,
            scenario_id=args.scenario,
            scenario_path=args.scenario_path,
        )
        startup = {
            "profile_id": dataset.profile_id,
            "host": args.host,
            "port": args.port,
            "url": f"http://{args.host}:{args.port}/",
            "province_input": str(dataset.province_input),
            "adjacency_input": None if dataset.adjacency_input is None else str(dataset.adjacency_input),
            "qa_report_input": None if dataset.qa_report_input is None else str(dataset.qa_report_input),
            "scenario_id": dataset.scenario_id,
            "scenario_path": None if dataset.scenario_path is None else str(dataset.scenario_path),
            "authoring_enabled": dataset.authoring_enabled,
            "province_count": dataset.province_count,
            "adjacency_count": dataset.adjacency_count,
            "qa_status": dataset.qa_status,
            "qa_error_count": dataset.qa_error_count,
            "qa_warning_count": dataset.qa_warning_count,
            "politics_qa_status": dataset.politics_qa_status,
            "politics_qa_error_count": dataset.politics_qa_error_count,
            "politics_qa_warning_count": dataset.politics_qa_warning_count,
            "ownership_row_count": len(dataset.ownership_by_id),
        }
        if args.format == "json":
            print(json.dumps(startup, indent=2, sort_keys=True), flush=True)
        else:
            print("gpm review: serving interactive MapLibre viewer.")
            print(f"Profile: {dataset.profile_id}")
            print(f"URL: {startup['url']}")
            print(f"Province input: {dataset.province_input}")
            print(
                "Adjacency input: "
                + ("(none)" if dataset.adjacency_input is None else str(dataset.adjacency_input))
            )
            print(
                "QA report: "
                + ("(none)" if dataset.qa_report_input is None else str(dataset.qa_report_input))
            )
            if dataset.scenario_id:
                print(
                    f"Scenario: {dataset.scenario_id} "
                    f"({len(dataset.ownership_by_id)} ownership rows; "
                    f"authoring={'on' if dataset.authoring_enabled else 'off'})"
                )
                if dataset.politics_qa_status is not None:
                    print(
                        f"Politics QA: {dataset.politics_qa_status} "
                        f"({dataset.politics_qa_error_count} errors, "
                        f"{dataset.politics_qa_warning_count} warnings)"
                    )
            else:
                print("Scenario: (none) — pass --scenario <id> for ownership layers.")
            print(f"Provinces: {dataset.province_count}; adjacency rows: {dataset.adjacency_count}")
            if dataset.qa_status is not None:
                print(
                    f"Topology QA: {dataset.qa_status} "
                    f"({dataset.qa_error_count} errors, {dataset.qa_warning_count} warnings)"
                )
            print("Press Ctrl+C to stop the server.")
        serve_review(
            dataset=dataset,
            host=args.host,
            port=args.port,
            open_browser=not args.no_open,
            block=True,
        )
    except (ConfigError, ReviewError) as error:
        _print_error(error)
        return 1
    return 0


def _load_profile_or_report(profile_id: str) -> dict | None:
    try:
        return load_profile(profile_id)
    except ConfigError as error:
        _print_error(error)
        return None


def _era_geometry_list(args: argparse.Namespace) -> int:
    summaries = list_era_geometry_packs()
    if args.format == "json":
        print(json.dumps([item.to_dict() for item in summaries], indent=2, sort_keys=True))
        return 0
    if not summaries:
        print("gpm era-geometry list: no packs found under configs/era_geometry/.")
        return 0
    print(f"gpm era-geometry list: {len(summaries)} pack(s).")
    for item in summaries:
        modes = ", ".join(item.geometry_modes)
        scenario = item.scenario_id or "—"
        print(
            f"- {item.pack_id}  era={item.era}  scenario={scenario}  "
            f"tier={item.quality_tier}  region={item.priority_region_id}  "
            f"modes=[{modes}]  hints={item.boundary_hint_count}  "
            f"overrides={item.hard_override_count}"
        )
    return 0


def _era_geometry_validate(args: argparse.Namespace) -> int:
    pack_arg = str(args.pack)
    pack_path = Path(pack_arg)
    try:
        if pack_path.is_file() or pack_arg.endswith(".json"):
            document = load_era_geometry_pack(pack_path.stem, path=pack_path)
        else:
            document = load_era_geometry_pack(pack_arg)
        validate_era_geometry_pack(document)
    except (EraGeometryError, EraGeometryPackError) as error:
        _print_error(error)
        return 1
    payload = {
        "pack_id": document["pack_id"],
        "era": document["era"],
        "scenario_id": document.get("scenario_id"),
        "quality_tier": document["quality_tier"],
        "priority_region_id": document["priority_region"]["id"],
        "geometry_modes": document["geometry_modes"],
        "boundary_hint_count": len(document.get("boundary_hints") or []),
        "hard_override_count": len(document.get("hard_overrides") or []),
        "valid": True,
    }
    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    print(f"gpm era-geometry validate: pack `{payload['pack_id']}` is valid.")
    print(f"Era: {payload['era']}")
    print(f"Scenario: {payload['scenario_id'] or '—'}")
    print(f"Quality tier: {payload['quality_tier']}")
    print(f"Priority region: {payload['priority_region_id']}")
    print(f"Modes: {', '.join(payload['geometry_modes'])}")
    print(
        f"Boundary hints: {payload['boundary_hint_count']}; "
        f"hard overrides: {payload['hard_override_count']}"
    )
    return 0


def _era_geometry_apply(args: argparse.Namespace) -> int:
    pack_arg = str(args.pack)
    pack_path = Path(pack_arg)
    pack_id = pack_path.stem if pack_path.is_file() or pack_arg.endswith(".json") else pack_arg
    explicit_path = pack_path if pack_path.is_file() or pack_arg.endswith(".json") else None
    try:
        result = apply_era_geometry_pack(
            pack_id,
            province_input=args.province_input,
            output_dir=args.output_dir,
            pack_path=explicit_path,
            recompute_adjacency=bool(args.recompute_adjacency),
            profile_id=args.profile,
        )
    except EraGeometryError as error:
        _print_error(error)
        return 1
    if args.format == "json":
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return 0
    print(f"gpm era-geometry apply: pack `{result.pack_id}` applied.")
    print(f"Era: {result.era}  tier={result.quality_tier}")
    print(f"Priority region: {result.priority_region_id}")
    print(f"Province input: {result.province_input}")
    print(f"Output dir: {result.output_dir}")
    print(
        f"Provinces: {result.province_count_in} → {result.province_count_out} "
        f"(priority region: {result.priority_region_count})"
    )
    print(
        f"Hard overrides: applied={result.hard_override_applied} "
        f"skipped={result.hard_override_skipped}"
    )
    print(
        f"Boundary hints: {result.boundary_hint_count}; "
        f"lineage rows: {result.lineage_row_count}"
    )
    print(f"Provinces: {result.provinces_output}")
    print(f"Boundary hints: {result.boundary_hints_output}")
    print(f"Lineage: {result.lineage_json_output}")
    print(f"Manifest: {result.manifest_output}")
    return 0


def _multi_era_list(args: argparse.Namespace) -> int:
    summaries = list_multi_era_packs()
    if args.format == "json":
        print(json.dumps([item.to_dict() for item in summaries], indent=2, sort_keys=True))
        return 0
    if not summaries:
        print("gpm multi-era list: no packs found under configs/multi_era/.")
        return 0
    print(f"gpm multi-era list: {len(summaries)} pack(s).")
    for item in summaries:
        eras = ", ".join(item.eras)
        scenarios = ", ".join(item.scenario_ids)
        print(
            f"- {item.pack_id}  eras=[{eras}]  scenarios=[{scenarios}]  "
            f"region={item.priority_region_id}  "
            f"matrix_rows={item.region_matrix_row_count}  "
            f"geometry_packs={len(item.era_geometry_pack_ids)}"
        )
    return 0


def _multi_era_validate(args: argparse.Namespace) -> int:
    pack_arg = str(args.pack)
    pack_path = Path(pack_arg)
    try:
        if pack_path.is_file() or pack_arg.endswith(".json"):
            document = load_multi_era_pack(pack_path.stem, path=pack_path)
        else:
            document = load_multi_era_pack(pack_arg)
        validate_multi_era_pack(document)
    except (MultiEraError, MultiEraPackError) as error:
        _print_error(error)
        return 1
    from gpm.multi_era.packs import resolve_era_geometry_pack_ids

    eras = [str(slot.get("era")) for slot in document.get("eras") or []]
    scenarios = [str(slot.get("scenario_id")) for slot in document.get("eras") or []]
    geom_packs: list[str] = []
    for slot in document.get("eras") or []:
        for pack_id in resolve_era_geometry_pack_ids(slot):
            if pack_id not in geom_packs:
                geom_packs.append(pack_id)
    payload = {
        "pack_id": document["pack_id"],
        "display_name": document["display_name"],
        "priority_region_id": (document.get("priority_region") or {}).get("id"),
        "era_count": len(eras),
        "eras": eras,
        "scenario_ids": scenarios,
        "era_geometry_pack_ids": geom_packs,
        "region_matrix_row_count": len(document.get("region_quality_matrix") or []),
    }
    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    print(f"gpm multi-era validate: pack `{payload['pack_id']}` is valid.")
    print(f"Display name: {payload['display_name']}")
    print(f"Priority region: {payload['priority_region_id']}")
    print(f"Eras ({payload['era_count']}): {', '.join(payload['eras'])}")
    print(f"Scenarios: {', '.join(payload['scenario_ids'])}")
    print(
        f"Geometry packs: {', '.join(payload['era_geometry_pack_ids']) or '—'}"
    )
    print(f"Region quality matrix rows: {payload['region_matrix_row_count']}")
    return 0


def _multi_era_build(args: argparse.Namespace) -> int:
    pack_arg = str(args.pack)
    pack_path = Path(pack_arg)
    pack_id = pack_path.stem if pack_path.is_file() or pack_arg.endswith(".json") else pack_arg
    explicit_path = pack_path if pack_path.is_file() or pack_arg.endswith(".json") else None
    try:
        result = build_multi_era_pack(
            pack_id,
            province_input=args.province_input,
            output_dir=args.output_dir,
            pack_path=explicit_path,
            recompute_adjacency=bool(args.recompute_adjacency),
            profile_id=args.profile,
            apply_geometry=not bool(args.no_geometry),
            resolve_politics=not bool(args.no_politics),
        )
    except MultiEraError as error:
        _print_error(error)
        return 1
    if args.format == "json":
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return 0
    print(f"gpm multi-era build: pack `{result.pack_id}` built.")
    print(f"Display name: {result.display_name}")
    print(f"Output dir: {result.output_dir}")
    print(f"Eras ({result.era_count}): {', '.join(result.eras)}")
    print(f"Scenarios: {', '.join(result.scenario_ids)}")
    print(
        f"Geometry packs: {', '.join(result.era_geometry_pack_ids) or '—'}"
    )
    print(f"Region quality matrix rows: {result.region_matrix_row_count}")
    print(f"Migration notes: {result.migration_md}")
    print(f"Manifest: {result.manifest_output}")
    print(f"Files written: {len(result.files_written)}")
    return 0


def _multi_era_migration(args: argparse.Namespace) -> int:
    pack_arg = str(args.pack)
    pack_path = Path(pack_arg)
    try:
        if pack_path.is_file() or pack_arg.endswith(".json"):
            document = load_multi_era_pack(pack_path.stem, path=pack_path)
        else:
            document = load_multi_era_pack(pack_arg)
        migration = build_migration_document(document)
    except (MultiEraError, MultiEraPackError) as error:
        _print_error(error)
        return 1

    if args.output_dir is not None:
        out_dir = Path(args.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        json_path = out_dir / "migration_notes.json"
        md_path = out_dir / "MIGRATION.md"
        json_path.write_text(
            json.dumps(migration, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        md_path.write_text(migration_markdown(migration), encoding="utf-8")

    if args.format == "json":
        print(json.dumps(migration, indent=2, sort_keys=True))
        return 0
    if args.format == "markdown":
        print(migration_markdown(migration), end="")
        return 0
    print(f"gpm multi-era migration: pack `{migration.get('pack_id')}`.")
    print(migration.get("summary") or "")
    print(f"Eras: {', '.join(str(s.get('era')) for s in migration.get('eras') or [])}")
    print(f"Consumer guidance items: {len(migration.get('consumer_guidance') or [])}")
    if args.output_dir is not None:
        print(f"Wrote: {Path(args.output_dir) / 'migration_notes.json'}")
        print(f"Wrote: {Path(args.output_dir) / 'MIGRATION.md'}")
    return 0


def _curation_list(args: argparse.Namespace) -> int:
    summaries = list_curator_bundles()
    if args.format == "json":
        print(json.dumps([item.to_dict() for item in summaries], indent=2, sort_keys=True))
        return 0
    if not summaries:
        print("gpm curation list: no curator bundles found under samples/ or bundles/.")
        return 0
    print(f"gpm curation list: {len(summaries)} bundle(s).")
    for item in summaries:
        scenarios = ", ".join(item.scenario_ids) or "—"
        print(
            f"- {item.bundle_id}: {item.display_name} "
            f"(license={item.license}, scenarios=[{scenarios}], "
            f"golden={item.golden_count})"
        )
    return 0


def _curation_validate(args: argparse.Namespace) -> int:
    try:
        document = load_curator_bundle(args.bundle)
        root = Path(document["_root"])
        validate_curator_bundle(
            document,
            bundle_root=root,
            check_files=True,
            check_scenarios=True,
        )
    except CuratorBundleError as error:
        _print_error(error)
        return 1
    payload = {
        "bundle_id": document["bundle_id"],
        "display_name": document["display_name"],
        "license": document["license"],
        "path": document.get("_root"),
        "scenario_ids": [entry["scenario_id"] for entry in document.get("scenarios") or []],
        "golden_paths": [
            entry.get("golden_path")
            for entry in document.get("scenarios") or []
            if entry.get("golden_path")
        ],
        "valid": True,
    }
    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    print(f"gpm curation validate: bundle `{payload['bundle_id']}` is valid.")
    print(f"Display name: {payload['display_name']}")
    print(f"License: {payload['license']}")
    print(f"Path: {payload['path']}")
    print(f"Scenarios: {', '.join(payload['scenario_ids'])}")
    print(f"Golden files: {len(payload['golden_paths'])}")
    return 0


def _curation_import(args: argparse.Namespace) -> int:
    try:
        result = import_curator_bundle(
            args.bundle,
            output_dir=args.output_dir,
            overwrite=bool(args.overwrite),
        )
    except CuratorBundleError as error:
        _print_error(error)
        return 1
    if args.format == "json":
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    print(f"gpm curation import: bundle `{result['bundle_id']}` imported.")
    print(f"Source: {result['source_root']}")
    print(f"Output: {result['output_dir']}")
    print(f"Scenarios: {', '.join(result['scenario_ids'])}")
    print(f"Files: {len(result['files'])}")
    return 0


def _curation_diff(args: argparse.Namespace) -> int:
    try:
        base_records, base_meta = load_ownership_side(
            scenario_id=args.base_scenario,
            scenario_path=args.base_scenario_path,
            ownership_input=args.base_ownership,
            province_input=args.province_input,
            allow_unknown_overrides=bool(args.allow_unknown_overrides),
            label="base",
        )
        target_records, target_meta = load_ownership_side(
            scenario_id=args.target_scenario,
            scenario_path=args.target_scenario_path,
            ownership_input=args.target_ownership,
            province_input=args.province_input,
            allow_unknown_overrides=bool(args.allow_unknown_overrides),
            label="target",
        )
        result = diff_ownership(
            base_records,
            target_records,
            base_meta=base_meta,
            target_meta=target_meta,
            report_output=args.report_output,
            max_changes=args.max_changes,
        )
    except OwnershipDiffError as error:
        _print_error(error)
        return 1
    if args.format == "json":
        print(json.dumps(result.report, indent=2, sort_keys=True))
        return 0
    print(f"gpm curation diff: {result.status}.")
    print(f"Base: {result.base_label}  Target: {result.target_label}")
    print(
        f"Owner changes: {result.owner_change_count}; "
        f"controller: {result.controller_change_count}; "
        f"disputed: {result.disputed_change_count}"
    )
    print(
        f"Added provinces: {result.added_province_count}; "
        f"removed: {result.removed_province_count}; "
        f"contested: {result.contested_province_count}"
    )
    delta = result.report.get("owner_count_delta") or {}
    if delta:
        print("Owner count deltas (non-zero):")
        for tag, row in sorted(delta.items()):
            print(
                f"  {tag}: {row['base']} → {row['target']} "
                f"({row['delta']:+d})"
            )
    else:
        print("Owner count deltas: none")
    changes = result.report.get("changes") or []
    preview = changes[:12]
    if preview:
        print(f"Change preview ({len(preview)} of {len(changes)}):")
        for item in preview:
            print(
                f"  {item['change_type']}: {item['province_id']} "
                f"{item.get('base_owner')} → {item.get('target_owner')}"
            )
    if result.report_output:
        print(f"Report: {result.report_output}")
    return 0


def _curation_checklist(args: argparse.Namespace) -> int:
    try:
        result: ChecklistResult = run_contribution_checklist(
            args.bundle,
            require_qa_claimed=bool(args.require_qa_claimed),
        )
    except CuratorBundleError as error:
        _print_error(error)
        return 1
    if args.format == "json":
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return 0 if result.passed else 1
    print(f"gpm curation checklist: {result.status}.")
    print(f"Bundle: {result.bundle_id}")
    print(f"Path: {result.path}")
    print(
        f"Items: {result.passed_count} passed, "
        f"{result.failed_count} failed, "
        f"{result.warning_count} warnings"
    )
    for item in result.items:
        mark = "ok" if item["passed"] else item["severity"]
        print(f"  [{mark}] {item['code']}: {item['message']}")
    return 0 if result.passed else 1


def _print_error(error: Exception) -> None:
    print(f"error: {error}", file=sys.stderr)
