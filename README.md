# Global Province Map Template

Reusable roadmap and tooling for a **license-aware global province map platform**
from open geodata.

**Goals:**

1. **Seed EU / Victoria / HOI-style games** — stable provinces, adjacency,
   attributes, scenario ownership, portable export packs (not proprietary
   engine formats).
2. **Power historical explanation and SaaS maps** — era-keyed politics,
   credible choropleths, attribution, progressive period fidelity.

Paradox-adjacent audiences have a sharp eye for anachronisms. Historical
accuracy is a first-class quality goal for official eras. The canonical pipeline
is **source layers → neutral atomic locations → era/profile provinces →
scenario politics and hierarchy → exports**. Modern administrative geometry is
a reference/attribution input and a hard constraint only for modern profiles,
not the permanent historical foundation. See [ROADMAP.md](ROADMAP.md).

Hierarchy the pipeline targets:

- locations: stable atomic paintable cells with versioned split lineage
- provinces: versioned era/profile aggregations of locations
- regions/states: versioned province groupings for production, politics, or administration
- countries / tags: political owners (modern baseline or scenario-era)
- superregions/continents: coarse map groupings

This repository does not include proprietary game data, Paradox map files, or
restricted geodata.

## Initial Data Strategy

The preferred core stack is:

- Natural Earth for land, coastlines, countries, rivers, lakes, and visual basemaps
- geoBoundaries for modern administrative boundary candidates
- GHSL and WorldPop for settlement and population weighting
- OpenHistoricalMap as an optional historical hint layer where coverage and feature licenses are acceptable

OpenStreetMap is useful but should be isolated behind an optional data path because OSM data is licensed under ODbL and may impose share-alike duties on adapted databases.

GADM should not be used in the default template because redistribution and commercial use are restricted without prior permission.

## Target Outputs

The implementation should eventually generate:

- `provinces.geojson` / `provinces.fgb`
- `regions.geojson`
- `locations.geojson`
- `adjacency.csv`
- `province_attributes.parquet`
- `source_manifest.json`
- `attribution.json`
- optional `pmtiles` or vector tiles for review UIs
- game template export packs (definitions, adjacency, localization, scenarios)
- compact engine-neutral runtime packs (dense tables, CSR graphs, scenario
  deltas, LOD/tiled geometry, compatibility and migration metadata)
- atlas / SaaS packages (scenario-joined choropleths, legends, attribution)

## Status

M23 and M24 provide the authoring foundation of the production historical
program. The public release is now **Modern-only**: historical configs, packs,
and the unsigned [1444-v2 candidate](docs/m25-1444-reconstruction.md) are
internal research fixtures, not official-era products. The execution order is
**M25A hard-case casebook → M25B runtime compiler → M25C global 1444 → M26
global 1836 → M27 global 1914 → M28 global 1936**. M23 builds a neutral, cross-admin
[location fabric](docs/m23-location-fabric.md); M24 standardizes the
[start-date research framework](docs/m24-start-date-research-framework.md) with
versioned schemas and fail-closed `gpm qa start-date` pass validation. The
withdrawn v1 candidate retains only C/U claims, and its Brussels/Nord
measurements are regressions, not release certification.

Completed **M25B — Game Runtime Compiler and Reference Pack** validates the
[historical hard-case contract](docs/m25-hard-case-casebook.md) and ships the
documented [`gpm export runtime` contract](docs/m25b-runtime.md):
stable-ID↔dense-index mappings, compact tables and CSR graphs, scenario deltas,
LOD/tiled geometry, a hashed compatibility manifest, migration metadata, an
optional debug-symbol pack, and an engine-neutral reference loader/benchmark.
The synthetic [reference pack](samples/m25b-runtime-reference/) exercises all
eight hard-case classes but is not historical evidence. M7 exports and M19
PMTiles remain foundations rather than duplicate runtime implementations.
Global certification now proceeds **1444, 1836, 1914,
1936**, restoring each public tab only after its worldwide research and runtime
gates pass.

Canonical research/authoring artifacts remain reproducible evidence inputs.
Normal game-runtime packs exclude raw locations and research evidence, use
precompiled LOD geometry or PMTiles/MVT rather than startup-parsed full GeoJSON,
and treat stable IDs as public identity while dense indices remain pack-local.
Official-era claims require both research acceptance and runtime-pack
validation. Stable province IDs derive from location membership plus profile,
era, and geometry revision.
`gpm build provinces` now consumes `data/processed/locations.geojson` by
default; the former Natural Earth scaffold is available only through the
explicit `--legacy-modern-admin` compatibility flag. Targeted splits require a
distinct `--output-fabric-revision`, preserving unchanged location IDs while
recording source/output revision lineage.

M22 global PMTiles-first demo is in place. `gpm demo build` now regenerates a
**Modern-only** public bundle
`landing/demo/data/` from the processed **full global build** (4,603 Natural
Earth admin-1 provinces): atlas exports and per-scenario ownership **PMTiles**
(the only global polygon source — no full-world GeoJSON ships), simplified
hierarchy border overlays with label points, precomputed adjacency centroid
lines, hero owner dissolves for the landing page, and a programmatically
regenerated `demo-manifest.json`, finishing with landing-site validation.
See `landing/demo/README.md`.

M21 four-level hierarchy is in place. `gpm build hierarchy` builds
**province → area → region → superregion** as real entities with stable
sha256 IDs: areas cluster admin-1 codes over the land-adjacency graph
(deterministic greedy agglomeration in the current modern scaffold),
regions are per-country with micro-state coalescing and NE-attribute
mega-country splits, superregions map to continents. Provinces gain
`parent_area_id` / `parent_geo_region_id` / `parent_superregion_id`;
`gpm export pack` prefers hierarchy entities when present. See
[docs/m21-hierarchy.md](docs/m21-hierarchy.md). This shipped hierarchy is
prototype infrastructure; M23 replaces its single-admin-parent assumption for
historical work. The older [density note](docs/m23-density-design-note.md) is
supporting research, not the M23 contract.

M19 PMTiles / vector tiles are in place. `gpm export tiles` compiles GeoJSON
into single-file **PMTiles** (Mapbox Vector Tiles) with a pure-Python backend
(tippecanoe used automatically when installed). `gpm export atlas --tiles`
writes `ownership.pmtiles` per scenario; the public demo can load a PMTiles
vector source. See [docs/m19-pmtiles.md](docs/m19-pmtiles.md).

M18 culture / religion atlas paint is in place. `gpm export atlas` emits
`culture_color` / `religion_color`, identity legends, and optional dissolved
multipolygons; review viewer and the public demo paint culture/religion modes.
Culture/religion remain curated scenario hints (not Paradox-grade ethnography).
See [docs/m18-culture-religion.md](docs/m18-culture-religion.md).

M17 curation workflow hardening is in place. `gpm curation` lists, validates,
and imports **external curator bundles**, diffs ownership tables (tag counts,
contested provinces), and runs a **contribution checklist**. Golden politics
checks now include max counts, required/forbidden owners, disputed flags, and
**golden borders** (province pairs + owner-adjacency floors). Sample:
`samples/curator-bundle-example/`. See
[docs/m17-curation.md](docs/m17-curation.md).

M20 multi-region composition infrastructure is **prototype/infrastructure
complete**. Central Europe packs
`ce-1444-v1` / `ce-1836-v1` / `ce-1936-v1` extend period shapes beyond Western
Europe. Multi-era slots may list `era_geometry_pack_ids` for ordered
multi-region composition; `europe-multi-era-v1` pairs WE + CE for
**1444 / 1836 / 1936** with a multi-row region quality matrix. Scaffold sample
`samples/scaffold-we-ce/`; samples `samples/era-geometry-ce-1444/` and
`samples/multi-era-europe-v1/`. Demo uses the WE+CE scaffold and Europe period
layers. Their hard overrides target committed samples, so they do not establish
production historical coverage or full-build `period-geometry`. See
[docs/m20-broader-period-geometry.md](docs/m20-broader-period-geometry.md).

M16 multi-era geometry + politics pack infrastructure is **prototype/
infrastructure complete**. `gpm multi-era` lists,
validates, builds, and emits **migration notes** for packs that pair era
geometry with curated politics across multiple official eras, with a
**region quality matrix** (geometry + politics tiers per region). Bundled pack
`we-multi-era-v1` covers **1444 / 1836 / 1936** with geometry packs
`we-1444-v1`, `we-1836-v1`, and `we-1936-v1` (WE-only; see M20 for Europe-wide
composition). Geometry is illustrative/sample-scoped until M25–M28 full-build
passes certify named regions. Official HOI-leaning scenario `official-1936` ships
curated-politics overlays, golden floors, and a `hoi-like` recipe. Sample:
`samples/multi-era-we-v1/`. See
[docs/m16-multi-era.md](docs/m16-multi-era.md).

M15 era-aware geometry v1 is **prototype/infrastructure complete**.
`gpm era-geometry` lists, validates, and
applies era-geometry prototype packs: soft historical boundary hints, optional hard
province overrides/splits for a priority region, and scaffold↔era **ID lineage
maps**. Bundled pack `we-1444-v1` targets Western Europe for `official-1444`.
The bundled hard overrides are sample-scoped; boundary hints alone do not meet
the production `period-geometry` bar. Sample:
`samples/era-geometry-we-1444/`. See
[docs/m15-era-geometry.md](docs/m15-era-geometry.md).

M14.5 public landing page is in place. A static marketing site under `landing/`
describes dual audiences, the pipeline, honest quality tiers, and license policy.
An interactive MapLibre **demo** at `landing/demo/` loads the WE+CE sample
(1444 / 1836 / 1936 / modern ownership, adjacency, inspector) plus multi-region
period geometry / boundary hints. `gpm release site` validates the
page + demo assets and can ensure a GitHub remote (`gh`), commit/push, and
deploy to Vercel. See [docs/m14.5-landing.md](docs/m14.5-landing.md).

M14 license-audited beta release packaging is in place. `gpm release beta` builds
a public beta bundle with a **license audit** (no restricted/ODbL contamination),
cleaned attribution pack with isolation notices, honest accuracy labels, a **game
template pack**, and an **atlas / SaaS face**. Default scenarios are
`modern-baseline`, `official-1836`, `official-1444`, and `official-1936`
(politics tier `curated-politics` when official eras are included; geometry
remains `scaffold-baseline` unless a multi-era pack is applied). Sample:
`samples/beta-license-audited/`. See
[docs/m14-beta-release.md](docs/m14-beta-release.md).

M13 second curated official scenario is in place. `official-1444` is a
**curated-politics** ownership overlay for the EU-leaning 1444-11-11 start date:
Europe-first elevated depth (HRE, Italian states, Iberia, France/Burgundy, British
Isles, east Europe) plus global major tags over the modern scaffold. Golden floors
live under `configs/scenarios/golden/official-1444.json`. Recommended profile:
`eu-like`. See [docs/m13-1444.md](docs/m13-1444.md). The pedagogical `demo-1444`
scenario remains scaffold-baseline only.

M12 first curated official scenario is in place. `official-1836` is a
**curated-politics** ownership overlay for the Victoria-leaning 1836 start date:
global major-power tags with elevated Europe, North America, and colonial theater
depth over the modern scaffold. Golden floors live under
`configs/scenarios/golden/official-1836.json` and auto-load for
`gpm qa scenario --scenario official-1836`. Recommended profile:
`victoria-like`. See [docs/m12-1836.md](docs/m12-1836.md).

M11 scenario politics QA and review authoring are in place. `gpm qa scenario`
checks ownership coverage, unknown/orphan tags, UNK owners, owner-component
sanity, and optional golden borders. `gpm review --scenario <id>` paints
owner/controller layers, politics QA overlays, and lets curators save
`province_overrides` into scenario JSON. See
[docs/m11-scenario-qa.md](docs/m11-scenario-qa.md).

M10 atlas / SaaS export face is in place. `gpm export atlas` writes scenario-
joined ownership choropleths, deterministic tag legends (MapLibre-ready),
uncertainty layers, owner-dissolved multipolygons, and web-friendly CSV/JSON
tables under `exports/atlas/<profile-id>/`—the second export face alongside
game packs. See [docs/m10-atlas.md](docs/m10-atlas.md).

M9 public alpha release packaging is in place. `gpm release alpha` builds a
release bundle with a game template pack, sample layers, reproducible recipe,
attribution, release tag, and honest accuracy labels (`scaffold-baseline` for
geometry and politics). Country filters (`--country` / `--sample-we`) produce
commit-friendly samples. A bundled illustrative sample lives under
`samples/alpha-modern-scaffold/`. See [docs/m9-alpha-release.md](docs/m9-alpha-release.md).

M8 historical scenario overlays are in place. `gpm scenario build` layers
owner/controller/cores/claims tables on the modern province scaffold via
baseline projection plus country, region, and province overrides—without
rewriting geometry. Bundled scenarios include `modern-baseline`, `demo-1444`,
and official curated-politics eras `official-1836` and `official-1444`.
`gpm export pack --scenario <id>` embeds resolved ownership trees. See
[docs/m8-scenarios.md](docs/m8-scenarios.md),
[docs/m12-1836.md](docs/m12-1836.md), and
[docs/m13-1444.md](docs/m13-1444.md).

M7 export packs are in place. `gpm export pack` writes profile-specific game
template packs under `exports/<profile-id>/` with province/region definitions,
adjacency, localization stubs, terrain/population tables, attribution, and
GeoJSON. `gpm export geojson` writes only the GeoJSON subset. Region type and
layout follow each profile's `[export]` table (`generic`, `eu-like`,
`victoria-like`, `hoi-like`). See [docs/m7-export.md](docs/m7-export.md).

M6 sea zones, ports, and straits are in place. `gpm build seas` creates coastal
and ocean sea-zone GeoJSON from land provinces (and optional Natural Earth
land), marks coastal land provinces, and prepares parent links for ports.
`gpm build adjacency` then emits land, sea, port-to-sea, and strait edges when
sea zones are present. Sea zones are gameplay-first abstractions, not legal
maritime boundaries. See [docs/m6-seas.md](docs/m6-seas.md).

M5 interactive review is in place. `gpm review` serves a local MapLibre viewer
over processed province GeoJSON, optional adjacency CSV, and optional topology
QA JSON. With M11, pass `--scenario` for ownership choropleths, politics QA,
and curator override authoring. See [docs/m5-review-viewer.md](docs/m5-review-viewer.md)
and [docs/m11-scenario-qa.md](docs/m11-scenario-qa.md).

M4 population-weighted split/merge refinement is in place. `gpm build
provinces` accepts population-count GeoTIFFs or population-point GeoJSON plus
optional settlement-point GeoJSON. It allocates each profile's province budget
between source provinces, creates deterministic population/settlement-seeded
Voronoi parts, merges tiny sibling fragments, conserves source coverage and
population totals, and records input/license lineage in every refined feature.
See [docs/m4-refinement.md](docs/m4-refinement.md) for the input contract and
algorithm.

M3 deterministic IDs, canonical land adjacency, and topology QA are also in place.
Province IDs are derived from source identity plus normalized geometry, so
equivalent ring orientation, ring starting point, input order, and multipart
ordering do not change IDs. `gpm build adjacency` writes one sorted undirected
row per qualifying shared land border, and `gpm qa topology` writes a
CI-gating JSON report for geometry, coverage, and graph checks.

M2 first modern global land province generation remains the draft geometry
source. The CLI ingests downloaded Natural Earth admin boundary zips into an
ignored canonical intermediate GeoJSON layer and writes the processed land
province draft that M3 consumes.

M1 source adapter implementation is also in place for Natural Earth and
geoBoundaries. The CLI can dry-run planned artifacts, download raw source files
into ignored local storage, calculate checksums, and write source manifests.
See [tasks/roadmap.md](tasks/roadmap.md) for the implementation plan and
[docs/phase-1-scaffold.md](docs/phase-1-scaffold.md) for how the current
package, configs, schemas, and tests map to that roadmap.

Quick verification:

```bash
uv run --extra dev pytest
uv run gpm sources download
uv run gpm sources manifest
```

Optional real source download:

```bash
uv run gpm sources download --execute
uv run gpm sources manifest --from-raw
uv run gpm build locations --fabric global-h3-v1
uv run gpm build provinces --location-input data/processed/locations.geojson
uv run gpm build provinces \
  --population-input /path/to/population.tif \
  --population-license "WorldPop CC BY 4.0" \
  --settlement-input /path/to/settlements.geojson
uv run gpm build seas
uv run gpm build adjacency
uv run gpm qa topology
uv run gpm export pack
uv run gpm export geojson
uv run gpm export atlas --scenario modern-baseline --scenario demo-1444
uv run gpm scenario list
uv run gpm scenario build --scenario modern-baseline
uv run gpm scenario build --scenario demo-1444 --profile eu-like
uv run gpm export pack --scenario modern-baseline --scenario demo-1444
uv run gpm release alpha --sample-we --tag alpha-0.1.0-sample-we
uv run gpm release beta --sample-we --tag beta-0.1.0-sample-we
uv run gpm review
```

`gpm build locations --fabric global-h3-v1` builds the canonical 30,000-cell
neutral land fabric, adjacency, modern-reference intersections, split lineage,
and manifest. `gpm build provinces --location-input ...` deterministically
aggregates those locations for the selected profile/start date and writes the
province membership and aggregation manifests.

`gpm build provinces` without `--location-input` is the deprecated compatibility
path. It uses Natural Earth admin-1 boundaries as land province
candidates and Natural Earth admin-0 country polygons as fallbacks where
admin-1 coverage is absent. It always writes the unchanged source candidates to
`data/intermediate/land_province_candidates.geojson` and
the processed result to `data/processed/provinces.geojson`. With no refinement
inputs or `--refine`, the processed result remains the M2/M3-compatible draft.
Supplying `--population-input`, `--settlement-input`,
`--target-province-count`, or `--refine` enables M4.

`gpm build seas` reads processed land provinces and optional Natural Earth
land polygons, writes `data/processed/sea_zones.geojson`, and updates land
`coastal` flags unless `--no-update-provinces` is set. Coastal sea zones are
per-province water claims; ocean zones are grid cells over remaining water.

`gpm build adjacency` reads `data/processed/provinces.geojson` by default and
writes `data/processed/adjacency.csv`. Land edges require lineal shared
boundaries at least the profile's `qa.min_shared_border_km`; point/corner
contact does not create adjacency. When `sea_zones.geojson` is present, the
same CSV also includes sea shared borders, port-to-sea links, and strait
shortcuts.

`gpm qa topology` compares province coverage to the Natural Earth admin-0 mask,
validates the canonical adjacency table, and writes
`data/processed/topology_qa.json`. Errors and operational failures return exit
code 1. Warnings such as valid isolated islands or multiple land components do
not fail the command. The QA workflow observes invalid geometry and marks
dependent analysis incomplete; it never repairs geometry silently.

`gpm export pack` reads processed provinces (and optional seas/adjacency) and
writes a profile-specific pack under `exports/<profile-id>/` with definitions,
localization stubs, tables, attribution, and GeoJSON. `gpm export geojson`
writes only the geometry layers. Neither command invents proprietary engine
formats; packs are portable open-data templates. Pass `--scenario <id>` to
embed M8 ownership overlays under `scenarios/<id>/`.

`gpm export atlas` is the second export face for web maps and SaaS-style
consumers. It writes `exports/atlas/<profile-id>/` with scenario-joined
ownership choropleths, deterministic tag legends, uncertainty layers, optional
owner-dissolved multipolygons, and CSV/JSON tables. Defaults to
`--scenario modern-baseline` when no scenarios are listed. See
[docs/m10-atlas.md](docs/m10-atlas.md).

`gpm scenario build` reads land provinces and a scenario definition from
`configs/scenarios/` (or `--scenario-path`) and writes ownership CSV/JSON under
`data/processed/scenarios/<id>/`. Geometry is unchanged; only political
attributes are resolved. Unknown province overrides fail unless
`--allow-unknown-overrides` is set.

`gpm release alpha` packages processed outputs into a public alpha release under
`releases/<tag>/` (or `--output-dir`) with `release_manifest.json`,
`ACCURACY.md`, `RECIPE.md`, `attribution.json`, `sample/` layers, and a full
`pack/` tree. Quality tiers are always labeled honestly for this channel
(`scaffold-baseline`). Use `--sample-we` or `--country` for subsets; the
committed sample under `samples/alpha-modern-scaffold/` is illustrative.

`gpm release beta` packages a **license-audited** public beta with the same
core files plus `LICENSE_AUDIT.md` / `license_audit.json`, a cleaned
attribution pack, dual faces (`pack/` game + `atlas/` SaaS), and default
official-era scenarios. The audit fails closed on restricted or ODbL lineage.
See [docs/m14-beta-release.md](docs/m14-beta-release.md).

`gpm review` starts a local review server (default `http://127.0.0.1:8765/`)
for the processed province layer. It optionally loads adjacency and topology QA
outputs when present, and opens a browser unless `--no-open` is passed.
