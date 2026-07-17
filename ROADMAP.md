# Roadmap

This roadmap describes work for a **license-aware global province map platform**
that can:

1. **Seed strategy games** in the EU / Victoria / HOI style (stable provinces,
   adjacency, attributes, scenario ownership, export packs).
2. **Power historical explanation and SaaS maps** (era-keyed politics, credible
   choropleths, attribution, optional period-aware geometry).

The shipped modern open-geodata scaffold is prototype infrastructure and a
reference/attribution input, not the permanent geometry foundation or a claim
of historical truth. Paradox-adjacent audiences have a sharp eye for
anachronisms; historical accuracy is a **first-class quality goal** for every
era the project officially supports.

## Product goals

| Audience | Primary needs |
| --- | --- |
| Game teams / modders | Reproducible province IDs, graphs, terrain/pop hooks, start-date politics, portable packs—not proprietary engine formats |
| Historical explainers / education | Date-keyed “who controlled what,” disputed/uncertain flags, source notes, maps that do not look obviously wrong for the era |
| SaaS / map products | Stable APIs of geometry + scenario tables, attribution, multi-era packaging, progressive fidelity by region |

Canonical pipeline:

```text
source layers → neutral atomic locations → era/profile provinces
              → scenario politics and hierarchy → canonical pass
              → runtime compiler → engine-neutral runtime pack
```

Modern administrative geometry is a reference and attribution input, not the
permanent partition of the historical map. It is a hard constraint only for a
modern profile. A **location** is the smallest stable paintable cell; provinces,
areas, regions, and superregions are versioned aggregations of locations and may
change by profile, era, and start date.

## Authoring and runtime architecture

The repository separates three artifact classes. A release claim must identify
which class it covers; a valid authoring pass is not automatically a valid game
runtime pack.

| Class | Purpose | Normal game-runtime distribution |
| --- | --- | --- |
| **Canonical research and authoring artifacts** | Atomic locations, full-detail province geometry, membership and split lineage, source manifests, dated evidence, assignments, coverage, changelogs, and QA results | **No.** These remain reproducible release/evidence inputs. |
| **Compiled runtime assets** | Dense province and hierarchy tables, CSR graphs, scenario state/deltas, LOD geometry or tiles, runtime manifest, hashes, compatibility revision, and migration metadata | **Yes.** This is the engine-neutral game-facing contract. |
| **Optional debug and evidence assets** | Stable-ID symbols, lineage/source lookups, coverage and uncertainty overlays, review renders, and assertion diagnostics | Only as a separate debug-symbol/evidence pack. |

Stable IDs are persistent public identity across compatible packs. Dense indices
are deterministic, pack-local implementation details and must never replace
stable IDs in saves, mods, evidence, or public APIs. Shipping geometry uses
precompiled LOD geometry and/or PMTiles/MVT; game startup never parses the full
canonical GeoJSON. Raw locations and research evidence are excluded from normal
runtime packs.

## Historical accuracy quality bar

For any **officially supported** era (1444, 1836, 1914, or 1936), aim for a **strong
balance**—not pure archival GIS on day one, and not “modern ISO with period skins.”

| Layer | Target bar | Notes |
| --- | --- | --- |
| Owner / controller / cores / claims | **High** | What Paradox-style players notice first |
| Major tags, unions, occupations | **High** for supported start dates | Showcase regions first if global depth lags |
| Culture / religion hints | **Medium–high** where used by games or atlas products | Can be coarser outside priority regions |
| Province shapes (playable) | **Medium+, rising over time** | Must not break the political story in key regions |
| Microborders / every exclave | **Progressive** | Document uncertainty; improve by region |
| Source honesty | **Always** | Lineage, disputed flags, curator notes, license |

An official coverage claim is always **region-, era-, and layer-specific**. In
every priority region it also requires:

- no known recent administrative outline surviving where it contradicts the
  claimed date;
- mandatory spatial golden-border tests, including negative-anachronism cases;
- a published coverage mask and grade for geometry, politics, and hierarchy;
- full-build application of historical geometry. Boundary hints or hard
  overrides that work only against committed samples do not qualify as
  `period-geometry`.

**Engineering bootstrap (complete):** modern scaffold, overlays, packaging, and
sample override tooling (M2–M22). M15, M16, and M20 are
**prototype/infrastructure complete**; their shipped hard overrides are
sample-scoped and are not production historical coverage.

## Guiding Principles

- Build from open geodata with clear attribution and reproducible source manifests.
- Keep generated data independent from proprietary game maps and engine formats.
- Separate permissive core data from share-alike or restricted optional layers.
- Assign stable identity primarily to neutral atomic locations so games and
  SaaS products can attach history, economy, diplomacy, and simulation data.
- Treat **geometry** and **historical politics** as separate layers that can
  evolve on different cadences—but both must serve accuracy goals for supported eras.
- Derive province IDs from ordered location membership plus profile, era, and
  geometry revision. Treat modern administrative membership as intersection-
  based or many-to-many, never as a mandatory single parent.
- Ship **two export faces** from the same core: game template packs and
  atlas/SaaS-oriented map packages.
- Optimize for **progressive fidelity**: global coverage first, depth by priority
  region and era, with explicit quality tiers (scaffold / curated politics /
  period geometry).
- Never claim Paradox-grade accuracy for demo remaps or uncurated baselines.

## Phase 0: Scope and Legal Baseline

- Pick the first supported map mode: modern world baseline scaffold.
- Define first-class historical eras for product support: **1444**, **1836**,
  **1914**, **1936**, plus custom eras.
- Confirm default source licenses:
  - Natural Earth: public domain.
  - geoBoundaries: CC BY 4.0.
  - GHSL: open/free Copernicus/JRC data.
  - WorldPop: CC BY 4.0.
  - OpenHistoricalMap: mostly CC0, with per-feature license exceptions.
  - OpenStreetMap: ODbL, optional pipeline only.
  - GADM: excluded unless permission is obtained.
- Create attribution and source-manifest requirements before ingesting any data.
- Decide whether the generated dataset will be distributed as data, code-only
  recipes, or both.
- Document the dual audience (game seed vs historical map / SaaS) in product copy.

## Phase 1: Repository and Tooling Foundation

- Choose the implementation stack.
  - Recommended: Python, GeoPandas, Shapely, Pyogrio, Rasterio, DuckDB, H3, NetworkX.
  - Optional viewer: TypeScript, MapLibre GL, PMTiles.
- Add project layout:
  - `src/` for pipeline code.
  - `configs/` for generation profiles and scenario definitions.
  - `data/raw/` ignored by git.
  - `data/intermediate/` ignored by git.
  - `data/processed/` ignored by git unless publishing small samples.
  - `docs/` for data policy, schema, and methodology.
  - `tests/` for topology and schema checks.
- Add a command-line entrypoint covering sources, build, scenario, export, QA,
  and review.

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
- Plan historical hint sources (later phases):
  - OpenHistoricalMap extracts where licenses allow
  - License-reviewed historical atlas / boundary datasets
  - Curator-authored scenario tables as first-class “sources”
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
  - `country` / political `tag`
  - `superregion`
  - `sea_zone`
  - `scenario` / ownership record
- Define required location fields:
  - stable location ID and fabric revision
  - display name
  - geometry
  - land/sea type
  - area
  - estimated population
  - terrain class
  - coastal flag
  - island flag
  - source lineage
  - license lineage
- Define province fields as an aggregation contract:
  - derived province ID
  - ordered location membership
  - profile, era/start date, and geometry revision
  - versioned parent area/region/superregion relationships
  - modern administrative intersections where applicable (many-to-many)
- Define scenario politics fields:
  - sovereignty, owner, controller, occupation, vassalage, personal unions,
    cores, and claims
  - culture / religion hints
  - disputed / uncertainty
  - validity dates
  - assignment source (baseline vs curated rule)
- Define graph outputs:
  - land adjacency
  - sea adjacency
  - strait adjacency
  - river crossing hints
  - port-to-sea links

## Phase 4: Location Fabric and Province Generation

- Build a clean global land mask.
- Build a neutral tessellation of stable atomic paintable locations. Allow
  historical borders, terrain, coasts, settlements, population, and gameplay
  needs to influence cells across modern administrative lines.
- Use modern administrative units as reference/attribution layers. Their
  influence is configurable and becomes a hard constraint only in modern
  profiles.
- Select location density based on:
  - total area
  - population density
  - available boundary quality
  - gameplay target province count
- Split oversized or historically unpaintable cells using:
  - population-weighted seeds
  - settlement clusters
  - rivers and mountain barriers
  - H3 or Voronoi partitioning
  - coast-aware boundaries
- Merge undersized fragments without requiring a shared modern admin parent,
  while preserving location lineage.
- Aggregate locations into profile- and date-specific provinces using:
  - shared border length
  - optional modern-admin affinity for modern profiles
  - island grouping rules
  - population and area thresholds
- Generate sea zones separately:
  - coastal sea bands
  - ocean regions
  - chokepoints and straits
  - port access zones
- Create deterministic location IDs from fabric lineage and normalized geometry.
- Create province IDs from location membership, profile, era, and geometry
  revision. Failed start-date paintability tests may request targeted location
  splits; publish each resulting fabric revision and parent/child lineage.

## Phase 5: Attributes and Gameplay Readiness

- Estimate population per location and aggregate it to provinces from GHSL or
  WorldPop rasters.
- Calculate area, coastline length, centroid, bounding box, and compactness for
  locations and derived provinces.
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
  - generic globe / SaaS product regions
- Compile stable IDs into deterministic dense, pack-local indices for
  simulation arrays while retaining reversible stable-ID mappings.
- Precompute compact province/hierarchy tables and CSR adjacency for land, sea,
  straits, and port links; runtime code must not reconstruct topology.
- Generate triangulated, progressively simplified LOD geometry plus tiled
  PMTiles/MVT archives suitable for viewport streaming and picking.
- Build spatial indexes for point/viewport province picking without scanning or
  unioning full polygon collections.
- Publish scenario base tables and deterministic deltas so unchanged geometry
  membership does not force duplicate geometry archives.
- Version save compatibility independently from pack content hashes and test
  stable-ID migration whenever membership or identity changes.
- Benchmark deterministic compilation, startup, memory, archive size, and local
  viewport tile latency against a documented CI runner and the canonical
  22,000-province `eu-like` profile.

## Phase 6: Historical Politics Layers

Politics are curated tables over versioned location/province aggregations. Tooling precedes full
historical completeness; **official eras must clear the accuracy bar above**.

- Keep location geometry, province aggregation, and historical politics as
  separate versioned concerns.
- Scenario tables (ownership overlays):
  - sovereignty and owner by date
  - controller and occupation by date
  - dependency/vassal status and personal-union relationships
  - culture/language hints
  - religion hints
  - claims and cores
  - disputed / uncertain status
  - curator notes and source lineage
- Override tooling (not baked-in one-off geometry hacks):
  - country rules
  - region rules
  - province overrides
  - later: date-ranged multi-row history per province
- Review historical data sources before use:
  - OpenHistoricalMap for hints where coverage and feature licenses allow
  - Historical atlas datasets only after per-source license review
  - Manual curation for high-quality 1444, 1836, 1914, and 1936 scenarios
- Maintain a dated historical-boundary registry. Each feature records validity
  dates, source and license lineage, confidence, related polities, boundary
  semantics, and whether it is a hard constraint or soft evidence.
- Quality tiers for each official scenario:
  - `scaffold-baseline` — modern parent projection only
  - `curated-politics` — human-reviewed tags for priority regions / global tags
  - `period-geometry` — full-build era-aware shapes certified for named
    regions; boundary hints alone never satisfy this tier
- Showcase path: pick **priority regions** (e.g. Western/Central Europe for
  EU/Vicky-style credibility) and deepen them before claiming global perfection.

## Phase 6b: Era-Aware Geometry (when politics alone is not enough)

Paradox gamers and historical maps both fail the sniff test when period politics
are painted on modern admin shapes that tell the wrong story (e.g. modern
nation-state outlines for 1444). This phase is a **real track**, not optional
trivia.

- Define when an era needs geometry changes vs political overlay only.
- Apply dated hard constraints and soft evidence to location aggregation;
  retain boundary-hint overlays as research/debug aids rather than certification.
- Prefer **lineage-preserving IDs** (split/merge maps, parent links) so game and
  SaaS consumers can migrate data across geometry revisions.
- Ingest license-cleared historical boundary sources for priority eras/regions.
- Recompute or subset adjacency for era geometry packs where shapes change.
- Document quality with separate region/era/layer coverage masks and grades.
- Do **not** hardcode proprietary Paradox province layouts.

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
- Add **scenario politics QA**:
  - every land province has owner/controller for official scenarios
  - unknown tags flagged
  - orphan cores/claims
  - large contiguous owner components sanity checks
  - mandatory spatial golden-border and negative-anachronism checks in every
    claimed priority region
  - semantic checks for sovereignty, control, occupation, dependencies,
    personal unions, claims, and uncertainty
- Add visual QA:
  - static render snapshots (modern + era ownership choropleths)
  - interactive map viewer
  - layer toggles for neutral locations, aggregation boundaries, scenario,
    coverage masks, uncertainty, adjacency, and errors
  - separate modern-source debug layers that cannot be mistaken for historical
    province geometry

## Phase 8: Interactive Review App

- Build a MapLibre-based viewer.
- Support loading generated vector tiles or GeoJSON samples.
- Add inspector tools:
  - stable location ID, derived province ID, and fabric/aggregation revisions
  - versioned parent hierarchy and location membership
  - source lineage
  - license lineage
  - population and area
  - adjacency list
  - scenario owner / controller / cores / claims
- Add QA overlays:
  - topology errors
  - oversized provinces
  - tiny fragments
  - missing names
  - suspicious coastal links
  - anachronistic modern-country paint under historical scenarios
  - coverage masks and recent-administration-outline regressions
- Add manual override authoring:
  - targeted location split requests with lineage
  - province aggregation / rename hints
  - versioned hierarchy overrides
  - scenario province ownership edits
  - disputed / note fields for curator workflow

## Phase 9: Exports and Templates (dual faces)

### Game-oriented packs

- Province / region / sea definitions
- Adjacency tables
- Localization stubs
- Scenario ownership tables
- Terrain and population tables
- Profiles: `modern-small`, `modern-detailed`, `hoi-like`, `victoria-like`, `eu-like`

### Atlas / SaaS / explanation packs

- Ownership joined to geometry for choropleths (per scenario / date)
- Country/tag legend and color suggestions
- Attribution and uncertainty layers
- Optional PMTiles / vector tiles for web maps (**M19 shipped**: `gpm export tiles`)
- API-friendly tables (GeoJSON, FlatGeobuf, GeoParquet, CSV/Parquet)

### Shared

- Canonical geospatial formats: GeoJSON, FlatGeobuf, GeoParquet, TopoJSON, PMTiles
- Document consumption for engines, mod tools, and map SaaS
- Never ship proprietary Paradox map formats as first-party outputs
- Export atomic locations separately from derived provinces and hierarchies.
- Include profile/start-date aggregation manifests, coverage masks, dated
  boundary lineage, and location-fabric migration maps.

## Phase 10: Release Process

- Produce a reproducible build manifest for each release.
- Publish source manifests and attribution with every generated dataset.
- Publish small sample datasets in git (including a **credible era sample**, not
  only modern geometry).
- Publish full generated datasets through GitHub Releases or object storage.
- Tag releases by location-fabric revision, aggregation revision, data vintage,
  generator version, **scenario set**, and **quality tier**.
- Provide changelogs for:
  - source updates
  - geometry changes
  - scenario / politics changes
  - schema changes
  - attribution changes
- Label accuracy honestly: scaffold vs curated-politics vs period-geometry.
- Release each start-date pass independently with regional coverage grades;
  never imply global period coverage from a regional pass.

## Phase 11: Official Era Programs

Run era work as explicit programs with acceptance criteria, not one-off demos.

Each program consumes the M24 research artifacts and, after M25.5, the shared
runtime contract. Its canonical pass is independently versioned and publishes
region/era/layer coverage rather than an implied global claim. An official
game-runtime release requires both canonical research acceptance and runtime-
pack validation.

### 1836 (Victoria-leaning showcase)

- Global scaffold + curated politics for major powers
- Priority depth: Europe, North America, key colonial theaters
- Population-era notes where open data allows; mark estimates clearly
- Game pack profile alignment with `victoria-like`

### 1444 (EU-leaning showcase)

- Curated politics for Europe first; expand outward
- Address geometry failure modes (modern nation outlines that break the period)
- Cores/claims/disputed density appropriate to the era’s storytelling
- Game pack profile alignment with `eu-like`

### 1914 (imperial-era showcase)

- German, Austro-Hungarian, Russian, and Ottoman imperial structures
- Sovereignty, dependencies, personal unions, colonial control, and uncertainty
- Mandatory spatial tests for imperial and dependency boundaries
- Game/atlas grouping suitable for a pre-First World War start date

### 1936 (HOI-leaning showcase)

- Interwar ownership and contested areas
- Strategic regions / supply-oriented grouping compatibility with `hoi-like`
- Colonial and mandate politics called out as curated tables

### Custom eras

- Document authoring workflow for third-party and SaaS custom start dates
- Validate against the same scenario schema and QA gates

## Phase 12: Continuous Curation and Community Workflow

- Scenario PR / review checklist (sources, licenses, golden borders) — **done (M17)**
- Diff tools: ownership choropleth before/after, tag counts, contested provinces — **done (M17)**
- Allow external curator datasets with manifests (not only in-repo JSON) — **done (M17)**
- Deprecation policy when province IDs or era geometry revisions ship — **done (M17)**
- Optional integration points for SaaS (tiles, versioned scenario bundles)

## Milestones

Completed foundation:

- M0: Planning repository created with roadmap and data policy.
- M1: Source adapters and manifests for Natural Earth and geoBoundaries.
- M2: First modern global land province draft.
- M3: Deterministic IDs, adjacency graph, and basic QA. Complete (2026-07-10).
- M4: Population-weighted split/merge algorithm. Complete (2026-07-10).
- M5: Interactive review viewer. Complete (2026-07-10).
- M6: Sea zones, ports, and straits. Complete (2026-07-10).
- M7: Export profiles for game templates. Complete (2026-07-10).
- M8: Historical scenario proof of concept (overlay tooling). Complete (2026-07-10).
- M9: Public alpha dataset release. Complete (2026-07-10).
- M10: Atlas / SaaS export face. Complete (2026-07-10).
- M11: Scenario politics QA + review authoring. Complete (2026-07-10).
- M12: First curated official scenario (1836). Complete (2026-07-10).
- M13: Second curated official scenario (1444). Complete (2026-07-10).
- M14: License-audited beta release. Complete (2026-07-10).
- M14.5: Public landing page + GitHub publish + Vercel deploy. Complete (2026-07-10).
- M14.5 demo: Interactive MapLibre demo under `landing/demo/` with live beta
  sample eras and reserved UI slots for M15+ work. Complete (2026-07-10).
- M15: Era-aware geometry v1 tooling and Western Europe 1444 sample. **Prototype/
  infrastructure complete** (2026-07-10); hard overrides are sample-scoped and
  do not establish production historical coverage.
- M16: Multi-era geometry + politics pack infrastructure for 1444 / 1836 / 1936.
  **Prototype/infrastructure complete** (2026-07-11); region labels describe
  illustrative samples, not full-build period-geometry certification.
- M17: Curation workflow hardening (external bundles, diffs, golden borders,
  contribution path). Complete (2026-07-11).
- M18: Culture / religion atlas paint layers. Complete (2026-07-11).
- M19: PMTiles / vector tiles. Complete (2026-07-11).
- M20: Central Europe sample packs and multi-region composition infrastructure.
  **Prototype/infrastructure complete** (2026-07-11); sample-scoped hard
  overrides do not establish production historical coverage.
- M21: Four-level hierarchy — province → area → region → superregion as real
  entities with stable sha256 IDs (`gpm build hierarchy`). Complete
  (2026-07-11).
- M22: Global PMTiles-first demo over the full Natural Earth build
  (`gpm demo build`: atlas exports, per-scenario PMTiles, hierarchy overlays,
  adjacency lines, regenerated manifest + validation). Complete (2026-07-11).

Shipped prototype/infrastructure path:

- **M9: Public alpha dataset release** — reproducible sample modern scaffold,
  docs, attribution, generator recipes; honest accuracy labeling. **Complete.**
- **M10: Atlas / SaaS export face** — scenario-joined choropleth packages,
  tag legends, web-friendly tables alongside game packs. **Complete.**
- **M11: Scenario politics QA + review authoring** — automated ownership checks;
  viewer support for scenario layers and curator edits. **Complete.**
- **M12: First curated official scenario (1836 priority)** — global tags with
  elevated Europe / key-theater depth; quality tier `curated-politics`.
  **Complete** (`official-1836` + golden floors).
- **M13: Second curated official scenario (1444 or 1936)** — second era program
  with the same bar; choose based on game vs atlas demand.
  **Complete** (`official-1444` + golden floors; 1936 deferred).
- **M14: License-audited beta release** — cleaned sources, attribution pack,
  restricted-path isolation, public beta datasets for game + atlas faces.
  **Complete** (`gpm release beta` + license audit + dual faces).
- **M14.5: Public landing page + deploy** — project marketing site under
  `landing/`, `gpm release site` for validation, optional GitHub ensure/push,
  and Vercel deploy. **Complete.**
- **M15: Era-aware geometry v1 (priority region)** — pack, override, hint, and
  lineage tooling. **Prototype/infrastructure complete** (`we-1444-v1`, CLI,
  sample + demo); hard geometry is sample-scoped, not production coverage.
- **M16: Multi-era geometry + politics packs** — ship at least two official eras
  with documented quality tiers per region; migration notes for consumers.
  **Prototype/infrastructure complete** (`we-multi-era-v1`, `we-1836-v1` /
  `we-1936-v1`, `official-1936`, CLI, sample + demo); geometry claims remain
  illustrative until a full-build start-date pass certifies them.
- **M17: Curation workflow hardening** — external scenario bundles, diffs,
  golden-border tests, community contribution path.
  **Complete** (`gpm curation`, golden-border suite, sample curator bundle).
- **M18: Culture / religion atlas paint layers** — identity colors, legends,
  optional dissolve on atlas packs; demo + review viewer paint modes.
  **Complete** (`culture_color` / `religion_color`, identity legends, demo).
- **M19: PMTiles / vector tiles** — pure-Python MVT + PMTiles writer, atlas
  `--tiles`, demo vector source.
  **Complete** (`gpm export tiles`, tileset schema, demo PMTiles).
- **M20: Broader period geometry** — second priority region (Central Europe) and
  multi-region multi-era composition beyond Western Europe.
  **Prototype/infrastructure complete** (`ce-*-v1`, `europe-multi-era-v1`,
  `apply_era_geometry_packs`, WE+CE sample + demo); hard overrides are
  sample-scoped.
- **M21: Four-level hierarchy** — areas (clustered admin-1 groups), regions,
  and superregions as real entities with stable IDs; provinces enriched with
  `parent_area_id` / `parent_geo_region_id` / `parent_superregion_id`; pack
  export prefers hierarchy entities. **Complete** (`gpm build hierarchy`,
  `docs/m21-hierarchy.md`).
- **M22: Global PMTiles-first demo** — landing demo backed by the full global
  build (4,603 provinces): per-scenario ownership PMTiles as the only polygon
  source, `queryRenderedFeatures` inspector, nested hierarchy borders + paint
  mode, precomputed adjacency lines, hero owner dissolves, one-command
  regeneration. **Complete** (`gpm demo build`).

Production authoring and runtime program:

- **M23 — Historically Paintable Location Fabric** — **Complete.** Builds neutral cross-admin
  atomic cells with stable location IDs; use population, terrain, settlements,
  history, travel time, and gameplay weighting; make modern-boundary influence
  configurable. Define aggregation revisions and allow targeted split feedback
  from failed paintability tests. Canonical contract:
  `docs/m23-location-fabric.md`; earlier density research remains supporting
  context in `docs/m23-density-design-note.md`. Production acceptance built
  30,003 locations twice with byte-identical fixed-timestamp artifacts, passed
  strict QA with zero errors, and aggregated the `eu-like` 1444 profile to
  22,000 derived provinces. Natural Earth incomplete coverage remains as
  documented warnings for 31 admin-0 and 40 admin-1 location shares.
- **M24 — Start-Date Research Framework** — standardize research dossiers,
  source manifests, dated boundary registry, polity/dependency gazetteer,
  uncertainty, reconstruction, spatial QA, coverage matrices, and changelogs.
  **Complete.** Versioned schemas plus fail-closed `gpm qa start-date` validate
  complete passes, cross-artifact lineage/revisions, executed spatial results, and
  regional release grades. Contract: `docs/m24-start-date-research-framework.md`.
- **M25 — 1444 Research and Reconstruction Pass** — Low Countries, Burgundy,
  France, HRE, and Central Europe first. Mandatory negative-anachronism
  regression: Brussels must not inherit the modern Brussels-region outline and
  Nord must not survive as a modern French administrative outline.
  **Active; v2 candidate assembled, pending independent review.** The
  independent M25 audit found synthetic locations, unproven split lineage,
  manually coupled frontier geometry, and a 15-province fixture mislabeled as
  a full build; that v1 candidate stays withdrawn with claims downgraded to
  C/U (audit: `tasks/m25-acceptance-audit.md`). The 1444-v2 pass rebuilds on
  the production fabric with real r1→r2 split lineage, a constrained
  22,000-province aggregation, evidence-backed golden borders with measured
  tolerances, and executed Brussels/Nord negative regressions
  (`tasks/m25-evidence-record.md`, `docs/m25-1444-reconstruction.md`).
  `gpm qa start-date` fails only on the pending independent human review; no
  release or acceptance claim is allowed until that review is signed and the
  gate passes.
- **M25.5 — Game Runtime Compiler and Reference Pack** — compile an accepted
  canonical pass with the proposed `gpm export runtime` interface. The pack
  contains stable-ID↔dense-index mappings, compact province/hierarchy tables,
  CSR land/sea/strait/port adjacency, scenario base tables and deltas,
  triangulated LOD geometry plus PMTiles/MVT, a hashed runtime manifest with a
  compatibility revision, explicit migration metadata, and an optional
  debug-symbol pack. Ship an engine-neutral reference loader and benchmark
  harness; Unity, Godot, and web adapters remain future thin integrations.
  M7 export contracts and M19 PMTiles are foundations reused by this milestone,
  not superseded implementations. **Planned; implementation begins only after
  an accepted M25 canonical pass, although schema/compiler design may proceed in
  parallel.**
- **M26 — 1836 Research and Reconstruction Pass** — post-Napoleonic Europe and
  priority colonial theaters. Reuse the M25.5 runtime contract; publish
  scenario-only deltas when location/province membership is unchanged, and
  migration metadata when it changes.
- **M27 — Official 1914 Imperial-Era Pass** — German, Austro-Hungarian, Russian,
  and Ottoman empires, including dependencies and control relationships. Reuse
  the runtime contract and the same delta/migration rule.
- **M28 — 1936 Research and Reconstruction Pass** — interwar borders, mandates,
  colonies, occupations, and strategic groupings. Reuse the runtime contract
  and the same delta/migration rule.

Each M25–M28 canonical pass is independently versioned. A pass is officially
releasable only when both its research acceptance gate and M25.5 runtime-pack
validation pass. Acceptance is by published regional coverage grade for each
layer, never an implied global claim.

### M25.5 runtime acceptance

- Two compilations in separate clean directories produce byte-identical files.
- Core simulation tables are at most 16 MiB uncompressed and 8 MiB compressed.
- CSR adjacency is at most 2 MiB for the 22,000-province profile.
- Initial metadata plus the lowest map LOD is at most 8 MiB compressed.
- The complete high-detail geometry archive is at most 128 MiB compressed.
- On the documented CI runner, the reference loader reads core tables in at
  most one second with at most 128 MiB peak RSS.
- Reported local viewport tile-read p95 is at most 25 ms.
- Runtime code performs no polygon unions, topology reconstruction,
  georeferencing, or historical-source processing.
- Runtime IDs, memberships, ownership, hierarchy, and adjacency cross-validate
  against the accepted canonical pass.
- Save/load tests cover stable IDs, dense indices, pack revisions,
  unchanged-pack compatibility, and explicit migration maps.

## Resolved product defaults

- The canonical `eu-like` build contains **22,000 provinces**.
- Stable IDs are persistent public identity; dense indices are pack-local.
- Normal runtime packs exclude raw locations and research evidence.
- Shipping geometry is LOD/tile based and never startup-parsed full GeoJSON.
- Save compatibility is revisioned and migration-tested.
- Official-era claims require both research acceptance and runtime validation.

## Engine- and program-specific questions

- How much ODbL data, if any, should be allowed in official builds?
- Which regions follow the priority regions in each independently released
  start-date pass?
- Should sea zones be gameplay-first abstractions or derived from open maritime
  boundaries (and do atlas products want a different sea model)?
- What is the right balance between admin-realistic and gameplay-readable
  provinces when historical fidelity rises?
- What minimum golden-border / golden-tag tests define “Paradox-eye” acceptance
  for each official era and region?
- Which thin adapter conventions should Unity, Godot, and web integrations use
  without changing the engine-neutral pack contract?
