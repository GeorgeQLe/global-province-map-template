# History

## 2026-07-10 - Demo label font fix + redeploy

- Fixed MapLibre province labels in `landing/demo/demo.js`: demotiles hosts
  `Noto Sans Regular`; `Open Sans Regular` 404'd and blocked GeoJSON tiling.
- Shipped to main and redeployed landing to Vercel production.

## 2026-07-10 - M14.5 Interactive Demo + Hero Choropleth

- Added `landing/demo/` MapLibre product demo with beta Western Europe sample
  eras (1444 / 1836 / modern), adjacency, inspector, and reserved M15+ slots.
- Replaced abstract hero tessellation with a real SVG choropleth fed from the
  same demo GeoJSON; linked marketing page into `/demo`.
- Extended `gpm release site` validation for demo files/snippets; updated
  cache headers, docs, README/ROADMAP, and tests.
- Next project task: implement M15 era-aware geometry v1 for priority regions.

## 2026-07-10 - M14.5 Public Landing Page + Vercel Deploy

- Added static marketing site under `landing/` (project thesis, dual audiences,
  pipeline, quality tiers, license policy, get-started).
- Added `gpm release site`: validate required files/content, optional
  `--ensure-repo` via `gh`, `--push` commit of landing assets, and `--deploy`
  to Vercel (`vercel deploy --yes [--prod]`).
- Added `docs/m14.5-landing.md` and tests for validation + CLI dry-run.
- Next project task: implement M15 era-aware geometry v1 for priority regions.

## 2026-07-10 - M14 License-Audited Beta Release

- Added `gpm release beta`: dual-face public beta (game `pack/` + atlas
  `atlas/`), default scenarios `modern-baseline` / `official-1836` /
  `official-1444`, and honest tiers (geometry scaffold-baseline; politics
  curated-politics when official eras are embedded).
- Added license audit (`gpm.release.license_audit`): catalog policy checks,
  forbidden lineage detection (GADM / ODbL / share-alike), feature
  `license_lineage` requirement, cleaned attribution pack with isolation
  notices, `LICENSE_AUDIT.md` + `license_audit.json`.
- Added recipe `configs/recipes/beta-license-audited.json`, sample
  `samples/beta-license-audited/`, schema
  `schemas/license-audit-report.schema.json`, tests, and
  `docs/m14-beta-release.md`.
- Next project task was M14.5 public landing page (completed later the same day).

## 2026-07-10 - M13 Second Curated Official Scenario (1444)

- Added `configs/scenarios/official-1444.json`: curated-politics ownership
  overlay for the EU-leaning 1444-11-11 start date with Europe-first elevated
  depth (HRE, Italy, Iberia, France/Burgundy, British Isles, east Europe) and
  global major tags (Ming, Ottomans, Mamluks, India majors).
- Added golden floors at `configs/scenarios/golden/official-1444.json` and
  recipe `configs/recipes/official-1444-curated.json` (`eu-like`).
- Extended accuracy labeling for `official-1444` and multi-official-era
  do-not-claim wording; kept `demo-1444` as scaffold-baseline pedagogy only.
- Added tests, `docs/m13-1444.md`, and status updates across README/ROADMAP/tasks.
- Chose 1444 over 1936 for M13 (demo path + `eu-like` alignment); 1936 remains
  open for a later official-era milestone.
- Next project task was M14 license-audited beta release (completed later the
  same day).

## 2026-07-10 - M12 First Curated Official Scenario (1836)

- Added `configs/scenarios/official-1836.json`: curated-politics ownership
  overlay for the Victoria-leaning 1836 start date with global major-power
  country rules and elevated Europe / North America / colonial region rules.
- Added scenario metadata fields: `quality_tier`, `official_era`,
  `recommended_profile`, `priority_theaters` (schema + validation).
- Added golden floors at `configs/scenarios/golden/official-1836.json` with
  auto-discovery from `gpm qa scenario`.
- Fixed shapefile NUL-padded region/country id matching so region rules hit
  real Natural Earth `iso_3166_2` values.
- Updated accuracy labeling for `official-1836`, recipe
  `configs/recipes/official-1836-curated.json`, tests, and `docs/m12-1836.md`.
- Next project task: implement M13 second curated official scenario (1444 or
  1936).

## 2026-07-10 - M11 Scenario Politics QA + Review Authoring

- Added `gpm qa scenario`: CI-gating politics QA for ownership coverage,
  unknown/orphan tags, UNK owners, owner-component sanity (via adjacency), and
  optional golden province_owners / min_owner_counts checks.
- Extended `gpm review --scenario` with owner/controller/assignment color modes,
  politics QA overlays, ownership inspector, and POST/DELETE override authoring
  that rewrites scenario `province_overrides`.
- Added `schemas/scenario-politics-qa-report.schema.json`, authoring helpers,
  fixture tests, and `docs/m11-scenario-qa.md`.
- Next project task was M12 first curated official scenario (1836) (completed
  later the same day).

## 2026-07-10 - M10 Atlas / SaaS Export Face

- Added `gpm export atlas`: second export face under `exports/atlas/<profile>/`.
- Scenario-joined `ownership_choropleth.geojson` with owner/controller colors.
- Deterministic tag legends (`legend.json`, `tags.csv`) with MapLibre match
  expressions and CSS custom properties.
- Uncertainty layer (disputed, owner≠controller, UNK) and optional owner-
  dissolved multipolygons.
- Web-friendly `tables/provinces.csv` plus per-scenario ownership CSV/JSON.
- Added `schemas/atlas-manifest.schema.json`, validator, tests, and
  `docs/m10-atlas.md`. PMTiles/FlatGeobuf/GeoParquet remain optional downstream.
- Next project task was M11 scenario politics QA + review authoring (completed
  later the same day).

## 2026-07-10 - M9 Public Alpha Dataset Release

- Added `gpm release alpha` packaging: game template pack, sample layers,
  release manifest, attribution, generator recipe (JSON + Markdown), and
  honest accuracy labels (`scaffold-baseline` for geometry and politics).
- Quality-tier catalog documents progressive fidelity through
  `curated-politics` and `period-geometry` without claiming them for alpha.
- Sample country filters (`--country`, `--sample-we`) produce commit-friendly
  subsets; full releases land under gitignored `releases/`.
- Bundled illustrative sample at `samples/alpha-modern-scaffold/` and recipe
  definition at `configs/recipes/alpha-modern-scaffold.json`.
- Added `schemas/release-manifest.schema.json`, validator, fixture tests, and
  `docs/m9-alpha-release.md`.
- Next project task was M10 atlas / SaaS export face (completed later the
  same day).

## 2026-07-10 - Roadmap: Dual Audience and Stronger Historical Bar

- Expanded root `ROADMAP.md` for strategy-game seeds **and** historical
  explanation / SaaS maps.
- Added historical accuracy quality bar (politics high; geometry progressive
  but first-class for official eras).
- Added Phase 6b era-aware geometry, dual export faces, official era programs
  (1836 / 1444 / 1936), curation workflow, and milestones M9–M17.
- Aligned `tasks/roadmap.md` and `tasks/todo.md` with the new sequence.
- Next project task was M9 public alpha dataset release (completed later the
  same day).

## 2026-07-10 - M8 Historical Scenario Proof of Concept

- Added scenario definitions under `configs/scenarios/` with
  `modern-baseline` (scaffold projection) and `demo-1444` (coarse era remaps).
- Implemented ownership resolution that never rewrites province geometry:
  baseline from `parent_country_id`, then country rules, region rules, and
  province overrides (later layers win field-by-field).
- Added `gpm scenario list|validate|build` writing ownership CSV/JSON, country
  catalogs, and scenario manifests under `data/processed/scenarios/<id>/`.
- Extended `gpm export pack --scenario` to embed resolved scenario trees.
- Added schemas, fixture-backed tests, and `docs/m8-scenarios.md`.
- Next project task: implement M9 public alpha dataset release (completed later
  the same day).

## 2026-07-10 - M7 Export Profiles for Game Templates

- Replaced the `gpm export geojson` placeholder with real GeoJSON export and
  added `gpm export pack` for full game template packs.
- Packs write profile-specific trees under `exports/<profile-id>/` with
  province/region GeoJSON, definition tables, adjacency CSV, English
  localization stubs (JSON + YAML), terrain/population tables, attribution,
  pack manifest, and README.
- Regions are derived by grouping land provinces on `parent_region_id`, with
  profile `region_type` of `region`, `state`, or `strategic_region`.
- Added optional `[export]` profile tables and layout presets (`generic`,
  `eu-like`, `victoria-like`, `hoi-like`).
- Added fixture-backed tests, `docs/m7-export.md`, and schema/docs updates.
- Next project task: implement M8 historical scenario proof of concept
  (completed later the same day).

## 2026-07-10 - M6 Sea Zones, Ports, and Straits

- Added `gpm build seas`, which derives gameplay-first coastal and ocean sea
  zones from land provinces and optional Natural Earth land polygons.
- Coastal water is claimed by deterministic per-province buffers; remaining
  ocean is partitioned on a lon/lat grid. Sea-zone IDs hash normalized geometry
  plus coastal parent or ocean grid identity.
- Land provinces are marked `coastal=true` when they receive a coastal sea zone
  (unless `--no-update-provinces`).
- Extended `gpm build adjacency` to emit `sea`, `port_to_sea`, and `strait`
  rows when `sea_zones.geojson` is present; land-only behavior is unchanged
  when sea zones are missing.
- Profile `generation.sea_zone_strategy` presets drive buffer, grid, and strait
  distances, with optional `[sea]` overrides.
- Added fixture-backed tests, `docs/m6-seas.md`, and schema/docs updates.
- Next project task: implement M7 export profiles for game templates (completed
  later the same day).

## 2026-07-10 - M5 Interactive Review Viewer

- Added `gpm review`, a local MapLibre review server that loads processed
  province GeoJSON, optional adjacency CSV, and optional topology QA reports.
- Bundled a no-build static viewer with province coloring modes (country, area,
  population, refinement, QA), click inspector, adjacency navigation, QA finding
  focus, search, and basemap/QA overlay toggles.
- Indexed adjacency bidirectionally and joined topology findings to province
  ids for the inspector and map overlays.
- Added fixture-backed server/API tests, package static asset packaging, and
  `docs/m5-review-viewer.md`.
- Next project task: implement M6 sea zones, ports, and straits (completed later
  the same day).

## 2026-07-10 - M4 Population-Weighted Split/Merge Refinement

- Extended `gpm build provinces` with opt-in M4 refinement while retaining the
  unchanged M2 candidate layer and backward-compatible no-input draft path.
- Added WGS84 population-point GeoJSON, georeferenced population-count GeoTIFF,
  and settlement-point GeoJSON ingestion with explicit source and license
  lineage propagation.
- Added deterministic profile-budget allocation, population/settlement-aware
  farthest-point seed selection, clipped ordered Voronoi splitting, stable
  parent-plus-geometry child IDs, and within-parent tiny-fragment merging.
- Added per-profile refinement weights and thresholds, M4 province attributes,
  CLI summaries and errors, population conservation/topology/determinism tests,
  and a real raster fixture test.
- Next project task: implement the M5 interactive review viewer (completed later
  the same day).

## 2026-07-10 - M3 Deterministic IDs, Adjacency, and Topology QA

- Replaced order-dependent province IDs with source-identity and normalized
  geometry SHA-256 IDs, with collision detection and explicit GeoJSON metadata.
- Implemented spatial-indexed canonical land adjacency generation with shared
  line measurement, threshold filtering, deterministic CSV ordering, and
  combined lineage.
- Implemented CI-gating topology QA for province geometry and hierarchy,
  Natural Earth admin-0 coverage, adjacency semantics and measurements,
  isolated provinces, and connected components.
- Added a topology QA report schema, per-profile QA thresholds, Shapely 2.1,
  synthetic geometry/graph tests, CLI tests, and exit-code coverage.
- Verified 4,603 draft provinces locally: adjacency evaluated 15,357 STRtree
  candidates instead of about 10.6 million all-pairs combinations and emitted
  10,781 land edges. QA correctly failed on one invalid province and one invalid
  Natural Earth admin-0 mask feature, marking dependent analysis incomplete
  without repairing either geometry.
- Next project task: implement the M4 population-weighted split/merge algorithm.

## 2026-07-09 - M2 First Modern Global Land Province Draft

- Implemented `gpm build provinces` as a real generation path instead of a
  placeholder command.
- Added a stdlib Natural Earth zipped shapefile reader for Polygon and
  MultiPolygon layers so the first draft can run without a heavy GIS dependency
  stack.
- Generated canonical land province candidates from Natural Earth admin-1
  boundaries and processed province GeoJSON, with admin-0 country fallbacks for
  countries lacking admin-1 coverage.
- Added fixture-backed tests for shapefile ingestion, province output contracts,
  CLI JSON summaries, and missing raw artifact errors.
- Next project task: add topology QA and first adjacency generation.

## 2026-07-09 - M1 Source Adapter Implementation

- Implemented real Natural Earth and geoBoundaries source artifact downloads
  behind `gpm sources download --execute`, while preserving the default dry-run
  planning behavior.
- Added atomic raw artifact writes, local raw artifact inspection, SHA-256
  checksum capture, access dates, version/original-format metadata, and
  persisted downloaded/build source manifests.
- Extended source manifests with per-artifact records and added deterministic
  mocked-download tests for the downloader and CLI path.
- Next project task: generate the first modern global land province draft from
  downloaded source artifacts.

## 2026-07-09 - Phase 1 Scaffold Wrap-Up

- Added the Python project scaffold and `gpm` CLI command surface for source
  planning, future builds, exports, and QA.
- Added license-aware source policy config, generation profiles, JSON schemas,
  source adapter stubs, and tests for the Phase 1 contract.
- Added documentation that maps the scaffold to the roadmap and explains schema
  ownership.
- Hardened the package boundary so installed wheels can find bundled configs
  and schemas, and so unknown CLI profiles return clean errors.
- Next project task: implement M1 source adapter downloads and persisted source
  manifests without committing raw geodata.
