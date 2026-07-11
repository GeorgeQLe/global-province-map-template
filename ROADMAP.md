# Roadmap

This roadmap describes work for a **license-aware global province map platform**
that can:

1. **Seed strategy games** in the EU / Victoria / HOI style (stable provinces,
   adjacency, attributes, scenario ownership, export packs).
2. **Power historical explanation and SaaS maps** (era-keyed politics, credible
   choropleths, attribution, optional period-aware geometry).

The modern open-geodata scaffold is the **engineering foundation**, not the final
claim of historical truth. Paradox-adjacent audiences have a sharp eye for
anachronisms; historical accuracy is a **first-class quality goal** for every
era the project officially supports.

## Product goals

| Audience | Primary needs |
| --- | --- |
| Game teams / modders | Reproducible province IDs, graphs, terrain/pop hooks, start-date politics, portable packs—not proprietary engine formats |
| Historical explainers / education | Date-keyed “who controlled what,” disputed/uncertain flags, source notes, maps that do not look obviously wrong for the era |
| SaaS / map products | Stable APIs of geometry + scenario tables, attribution, multi-era packaging, progressive fidelity by region |

Shared pipeline:

```text
geographic scaffold → attributes & graph → scenario politics → optional era geometry
        → export face (game pack | atlas / SaaS)
```

## Historical accuracy quality bar

For any **officially supported** era (e.g. 1444, 1836, 1936), aim for a **strong
balance**—not pure archival GIS on day one, and not “modern ISO with period skins.”

| Layer | Target bar | Notes |
| --- | --- | --- |
| Owner / controller / cores / claims | **High** | What Paradox-style players notice first |
| Major tags, unions, occupations | **High** for supported start dates | Showcase regions first if global depth lags |
| Culture / religion hints | **Medium–high** where used by games or atlas products | Can be coarser outside priority regions |
| Province shapes (playable) | **Medium+, rising over time** | Must not break the political story in key regions |
| Microborders / every exclave | **Progressive** | Document uncertainty; improve by region |
| Source honesty | **Always** | Lineage, disputed flags, curator notes, license |

**Engineering bootstrap (done / in progress):** modern scaffold + overlay tooling
(M2–M8).  
**Product bar (future work):** curated politics, then era-aware geometry where
overlays alone cannot pass a gamer or historian sniff test.

## Guiding Principles

- Build from open geodata with clear attribution and reproducible source manifests.
- Keep generated data independent from proprietary game maps and engine formats.
- Separate permissive core data from share-alike or restricted optional layers.
- Generate stable IDs so games and SaaS products can attach history, economy,
  diplomacy, and simulation data safely.
- Treat **geometry** and **historical politics** as separate layers that can
  evolve on different cadences—but both must serve accuracy goals for supported eras.
- Prefer **one addressable province graph** with scenario overlays; add
  **era-specific geometry** only where political overlays cannot credibly
  represent the period.
- Ship **two export faces** from the same core: game template packs and
  atlas/SaaS-oriented map packages.
- Optimize for **progressive fidelity**: global coverage first, depth by priority
  region and era, with explicit quality tiers (scaffold / curated politics /
  period geometry).
- Never claim Paradox-grade accuracy for demo remaps or uncurated baselines.

## Phase 0: Scope and Legal Baseline

- Pick the first supported map mode: modern world baseline scaffold.
- Define first-class historical eras for product support: **1836**, **1444**,
  **1936**, plus custom eras.
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
- Define required province fields:
  - stable ID
  - display name
  - geometry
  - land/sea type
  - parent region ID
  - parent country ID for the modern baseline scaffold
  - area
  - estimated population
  - terrain class
  - coastal flag
  - island flag
  - source lineage
  - license lineage
- Define scenario politics fields:
  - owner, controller, cores, claims
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
- Keep IDs stable enough for multi-era scenarios and downstream save/mod data.

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
  - generic globe / SaaS product regions

## Phase 6: Historical Politics Layers

Politics are curated tables over a geographic scaffold. Tooling precedes full
historical completeness; **official eras must clear the accuracy bar above**.

- Keep geometry and historical ownership as separate concerns in the data model.
- Start with modern generated geography as the default scaffold.
- Scenario tables (ownership overlays):
  - owner by date
  - controller by date
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
  - Manual curation for high-quality 1444, 1836, and 1936 scenarios
- Quality tiers for each official scenario:
  - `scaffold-baseline` — modern parent projection only
  - `curated-politics` — human-reviewed tags for priority regions / global tags
  - `period-geometry` — era-aware shapes where required (Phase 6b)
- Showcase path: pick **priority regions** (e.g. Western/Central Europe for
  EU/Vicky-style credibility) and deepen them before claiming global perfection.

## Phase 6b: Era-Aware Geometry (when politics alone is not enough)

Paradox gamers and historical maps both fail the sniff test when period politics
are painted on modern admin shapes that tell the wrong story (e.g. modern
nation-state outlines for 1444). This phase is a **real track**, not optional
trivia.

- Define when an era needs geometry changes vs political overlay only.
- Support **era geometry modes** or **boundary-hint overlays** without forcing
  a full world redraw every patch:
  - soft: historical boundary hints / disputed frontier bands on modern scaffold
  - hard: alternate province polygons for priority regions in a given era
- Prefer **lineage-preserving IDs** (split/merge maps, parent links) so game and
  SaaS consumers can migrate data across geometry revisions.
- Ingest license-cleared historical boundary sources for priority eras/regions.
- Recompute or subset adjacency for era geometry packs where shapes change.
- Document quality: which continents/regions are period-true vs scaffold-backed.
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
  - optional golden checks for famous borders / capitals in priority regions
- Add visual QA:
  - static render snapshots (modern + era ownership choropleths)
  - interactive map viewer
  - layer toggles for source, province, region, adjacency, scenario, and errors

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
  - scenario owner / controller / cores / claims
- Add QA overlays:
  - topology errors
  - oversized provinces
  - tiny fragments
  - missing names
  - suspicious coastal links
  - anachronistic modern-country paint under historical scenarios
- Add manual override authoring:
  - split / merge / rename hints
  - parent-region overrides
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
- Optional PMTiles / vector tiles for web maps
- API-friendly tables (GeoJSON, FlatGeobuf, GeoParquet, CSV/Parquet)

### Shared

- Canonical geospatial formats: GeoJSON, FlatGeobuf, GeoParquet, TopoJSON, PMTiles
- Document consumption for engines, mod tools, and map SaaS
- Never ship proprietary Paradox map formats as first-party outputs

## Phase 10: Release Process

- Produce a reproducible build manifest for each release.
- Publish source manifests and attribution with every generated dataset.
- Publish small sample datasets in git (including a **credible era sample**, not
  only modern geometry).
- Publish full generated datasets through GitHub Releases or object storage.
- Tag releases by data vintage, generator version, **scenario set**, and
  **quality tier**.
- Provide changelogs for:
  - source updates
  - geometry changes
  - scenario / politics changes
  - schema changes
  - attribution changes
- Label accuracy honestly: scaffold vs curated-politics vs period-geometry.

## Phase 11: Official Era Programs

Run era work as explicit programs with acceptance criteria, not one-off demos.

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

### 1936 (HOI-leaning showcase)

- Interwar ownership and contested areas
- Strategic regions / supply-oriented grouping compatibility with `hoi-like`
- Colonial and mandate politics called out as curated tables

### Custom eras

- Document authoring workflow for third-party and SaaS custom start dates
- Validate against the same scenario schema and QA gates

## Phase 12: Continuous Curation and Community Workflow

- Scenario PR / review checklist (sources, licenses, golden borders)
- Diff tools: ownership choropleth before/after, tag counts, contested provinces
- Allow external curator datasets with manifests (not only in-repo JSON)
- Deprecation policy when province IDs or era geometry revisions ship
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

Near-term product path:

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
- **M15: Era-aware geometry v1 (priority region)** — period shapes or boundary
  hints where modern scaffold fails the historical sniff test; ID lineage maps.
- **M16: Multi-era geometry + politics packs** — ship at least two official eras
  with documented quality tiers per region; migration notes for consumers.
- **M17: Curation workflow hardening** — external scenario bundles, diffs,
  golden-border tests, community contribution path.

## Open Questions

- What should the default target province count be for game vs atlas products?
- Should the default public dataset include generated geometry, or only the
  generator and reproducible recipes?
- How much ODbL data, if any, should be allowed in official builds?
- Order of full-depth eras after the first showcase: 1444 vs 1936 vs custom?
- Which regions are mandatory for “official era” marketing claims?
- Should sea zones be gameplay-first abstractions or derived from open maritime
  boundaries (and do atlas products want a different sea model)?
- What is the right balance between admin-realistic and gameplay-readable
  provinces when historical fidelity rises?
- Should stable IDs prioritize source lineage, geometry location, or
  human-readable slugs—especially across era geometry revisions?
- How should SaaS versioning work for scenario corrections without breaking game
  mods that pinned an older pack?
- What minimum golden-border / golden-tag tests define “Paradox-eye” acceptance
  for an official era?
