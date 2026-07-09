# Roadmap

This roadmap describes the work needed to create a reusable, license-aware global province map generator for strategy games and globe products.

## Guiding Principles

- Build from open geodata with clear attribution and reproducible source manifests.
- Keep the generated geometry independent from proprietary game maps.
- Separate permissive core data from share-alike or restricted optional layers.
- Generate stable IDs so downstream games and products can safely attach history, economy, diplomacy, and simulation data.
- Treat historical accuracy as a curated layer on top of a generated geographic scaffold.

## Phase 0: Scope and Legal Baseline

- Pick the first supported map mode: modern world baseline.
- Define future historical modes: 1936, 1836, 1444, and custom eras.
- Confirm default source licenses:
  - Natural Earth: public domain.
  - geoBoundaries: CC BY 4.0.
  - GHSL: open/free Copernicus/JRC data.
  - WorldPop: CC BY 4.0.
  - OpenHistoricalMap: mostly CC0, with per-feature license exceptions.
  - OpenStreetMap: ODbL, optional pipeline only.
  - GADM: excluded unless permission is obtained.
- Create attribution and source-manifest requirements before ingesting any data.
- Decide whether the generated dataset will be distributed as data, code-only recipes, or both.

## Phase 1: Repository and Tooling Foundation

- Choose the implementation stack.
  - Recommended: Python, GeoPandas, Shapely, Pyogrio, Rasterio, DuckDB, H3, NetworkX.
  - Optional viewer: TypeScript, MapLibre GL, PMTiles.
- Add project layout:
  - `src/` for pipeline code.
  - `configs/` for generation profiles.
  - `data/raw/` ignored by git.
  - `data/intermediate/` ignored by git.
  - `data/processed/` ignored by git unless publishing small samples.
  - `docs/` for data policy, schema, and methodology.
  - `tests/` for topology and schema checks.
- Add a command-line entrypoint:
  - `sources download`
  - `sources manifest`
  - `build provinces`
  - `build adjacency`
  - `export geojson`
  - `qa topology`
  - `qa render`

## Phase 2: Source Inventory and Ingestion

- Implement source adapters for Natural Earth layers:
  - land polygons
  - coastline
  - admin-0 countries
  - admin-1 states/provinces
  - rivers and lakes
  - geographic regions and continents
- Implement geoBoundaries ingestion:
  - country files
  - global composites
  - admin levels ADM0 through the deepest reliable level per country
- Implement population and settlement ingestion:
  - GHSL built-up grid
  - GHSL population grid
  - WorldPop population density or count rasters
- Record source metadata:
  - URL
  - access date
  - version
  - license
  - checksum
  - processing steps
- Normalize all vectors to a canonical CRS and geometry validity standard.

## Phase 3: Canonical Data Model

- Define stable entity schemas:
  - `location`
  - `province`
  - `region`
  - `country`
  - `superregion`
  - `sea_zone`
- Define required province fields:
  - stable ID
  - display name
  - geometry
  - land/sea type
  - parent region ID
  - parent country ID for the baseline scenario
  - area
  - estimated population
  - terrain class
  - coastal flag
  - island flag
  - source lineage
  - license lineage
- Define graph outputs:
  - land adjacency
  - sea adjacency
  - strait adjacency
  - river crossing hints
  - port-to-sea links

## Phase 4: Province Generation

- Build a clean global land mask.
- Clip administrative units to land and water boundaries.
- Select candidate admin levels per country based on:
  - total area
  - population density
  - available boundary quality
  - gameplay target province count
- Split oversized candidates using:
  - population-weighted seeds
  - settlement clusters
  - rivers and mountain barriers
  - H3 or Voronoi partitioning
  - coast-aware boundaries
- Merge undersized fragments using:
  - shared border length
  - same parent admin unit
  - island grouping rules
  - population and area thresholds
- Generate sea zones separately:
  - coastal sea bands
  - ocean regions
  - chokepoints and straits
  - port access zones
- Create deterministic IDs from source lineage and geometry hashes.

## Phase 5: Attributes and Gameplay Readiness

- Estimate population per province from GHSL or WorldPop rasters.
- Calculate area, coastline length, centroid, bounding box, and compactness.
- Assign terrain classes from open land-cover or elevation sources after license review.
- Add settlement features:
  - capital candidate
  - largest settlement candidate
  - port candidate
  - infrastructure density proxy
- Add balancing profiles:
  - EU-like smaller provinces and many countries
  - Victoria-like states and population/economy emphasis
  - HOI-like states, supply regions, and strategic areas
  - generic globe-product regions

## Phase 6: Historical Layers

- Treat geometry and historical ownership as separate concerns.
- Start with modern generated geography as the stable scaffold.
- Add historical scenario tables:
  - owner by date
  - controller by date
  - culture/language hints
  - religion hints
  - claims and cores
  - disputed status
- Review historical data sources before use.
  - OpenHistoricalMap can provide hints where available.
  - Historical atlas datasets may be useful but require per-source license review.
  - Manual curation will be required for high-quality 1444, 1836, and 1936 scenarios.
- Build tooling for overrides instead of hardcoding historical facts into generated geometry.

## Phase 7: QA and Validation

- Add automated topology checks:
  - valid geometries
  - no self-intersections
  - no unintended overlaps
  - no unexpected gaps inside land masks
  - no orphan provinces
  - no missing parent regions
  - no duplicate IDs
- Add graph checks:
  - adjacency symmetry
  - connected land components by continent or island group
  - sea-zone connectivity
  - valid port-to-sea links
- Add data checks:
  - population totals within expected tolerance
  - area totals within expected tolerance
  - required attribution present
  - restricted sources absent from default builds
- Add visual QA:
  - static render snapshots
  - interactive map viewer
  - layer toggles for source, province, region, adjacency, and errors

## Phase 8: Interactive Review App

- Build a MapLibre-based viewer.
- Support loading generated vector tiles or GeoJSON samples.
- Add inspector tools:
  - province ID
  - parent hierarchy
  - source lineage
  - license lineage
  - population and area
  - adjacency list
- Add QA overlays:
  - topology errors
  - oversized provinces
  - tiny fragments
  - missing names
  - suspicious coastal links
- Add manual override authoring:
  - split hints
  - merge hints
  - rename hints
  - parent-region overrides

## Phase 9: Exports and Templates

- Export canonical geospatial formats:
  - GeoJSON
  - FlatGeobuf
  - GeoParquet
  - TopoJSON
  - PMTiles
- Export game-oriented formats:
  - province definitions
  - region/state definitions
  - adjacency tables
  - localization stubs
  - scenario ownership tables
  - terrain and population tables
- Add sample profiles:
  - `modern-small`
  - `modern-detailed`
  - `hoi-like`
  - `victoria-like`
  - `eu-like`
- Document how generated files should be consumed by engines or downstream games.

## Phase 10: Release Process

- Produce a reproducible build manifest for each release.
- Publish source manifests and attribution with every generated dataset.
- Publish small sample datasets in git.
- Publish full generated datasets through GitHub Releases or object storage if file sizes are large.
- Tag releases by data vintage and generator version.
- Provide changelogs for:
  - source updates
  - geometry changes
  - schema changes
  - attribution changes

## Milestones

- M0: Planning repository created with roadmap and data policy.
- M1: Source adapters and manifests for Natural Earth and geoBoundaries.
- M2: First modern global land province draft.
- M3: Deterministic IDs, adjacency graph, and basic QA.
- M4: Population-weighted split/merge algorithm.
- M5: Interactive review viewer.
- M6: Sea zones, ports, and straits.
- M7: Export profiles for game templates.
- M8: Historical scenario proof of concept.
- M9: Public alpha dataset release.
- M10: License-audited beta release.

## Open Questions

- What should the default target province count be?
- Should the default public dataset include generated geometry, or only the generator and reproducible recipes?
- How much ODbL data, if any, should be allowed in official builds?
- Which historical eras deserve first-class support?
- Should sea zones be gameplay-first abstractions or derived from open maritime boundaries?
- What is the right balance between admin-realistic and gameplay-readable provinces?
- Should stable IDs prioritize source lineage, geometry location, or human-readable slugs?
