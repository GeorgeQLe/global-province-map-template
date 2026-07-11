# Phase 1 Scaffold

This repository now contains the Phase 1 foundation described in `ROADMAP.md`.
It is intentionally a code and contract scaffold only: no raw geodata is
downloaded, generated, or committed.

## Roadmap Mapping

- `pyproject.toml` defines the Python project and the `gpm` CLI entrypoint.
- `src/gpm/` contains the command-line stubs, config loaders, source manifest
  helper, schema loader, and the future source adapter package.
- `configs/profiles/` contains the initial generation profiles from Phase 9:
  `modern-small`, `modern-detailed`, `hoi-like`, `victoria-like`, and `eu-like`.
- `configs/sources.toml` records the Phase 0 data policy in machine-readable
  form.
- `schemas/` contains JSON Schema contracts for source manifests, attribution
  records, province entities, region entities, and adjacency records.
- `tests/` checks that profiles parse, default source policy stays permissive,
  restricted sources are excluded, and the stub CLI runs.
- `data/raw/`, `data/intermediate/`, and `data/processed/` are ignored by git
  and reserved for local future runs.

## Source Policy

The default profile path includes only Natural Earth and geoBoundaries. GHSL and
WorldPop downloads remain deferred default candidates because their upstream
catalog/version selection still needs dedicated source adapters. M4 can consume
user-supplied population-count rasters or point exports now, with explicit
lineage and license notices. OpenHistoricalMap is optional.

OpenStreetMap is marked optional and isolated because ODbL-derived databases
must not be mixed into the permissive default build path. GADM is marked
restricted and excluded from default builds unless permission is obtained.

## M1 Source Adapters

M1 implements the adapters named in `configs/sources.toml`:

- `gpm.sources.adapters.natural_earth`
- `gpm.sources.adapters.geoboundaries`

`gpm sources download` still defaults to a dry run. Use
`gpm sources download --execute` to fetch raw artifacts into ignored local
storage under `data/raw/`, calculate SHA-256 checksums, and write
`source_manifest.json`. Use `gpm sources manifest --from-raw` to rebuild a
downloaded/build manifest from files that already exist locally.

Source manifests now include source-level metadata plus per-artifact URL, path,
access date, version, original format, byte count, and checksum. Downloaded raw
datasets remain outside git through the repository ignore rules.

## M2 Province Draft

M2 replaces the `gpm build provinces` placeholder with a first land province
generation path. The command expects the M1 Natural Earth raw artifacts to exist
under `data/raw/natural_earth/` and reads:

- `ne_10m_admin_1_states_provinces.zip`
- `ne_10m_admin_0_countries.zip`

The generated intermediate candidate layer is written to
`data/intermediate/land_province_candidates.geojson`. The processed province
draft is written to `data/processed/provinces.geojson`.

The M2 draft uses Natural Earth admin-1 features as province candidates and
Natural Earth admin-0 polygons as fallbacks for countries without admin-1
coverage. Coastal, island, terrain, and population classifications remain draft
attributes for later milestones; topology validation itself is implemented by
M3.

## M3 IDs, Adjacency, and Topology QA

M3 replaces the adjacency and topology QA placeholders. Province builds now
emit source-and-normalized-geometry SHA-256 IDs and record their ID scheme in
GeoJSON metadata. `gpm build adjacency` uses an STRtree candidate search and
writes canonical undirected shared-border rows to
`data/processed/adjacency.csv`.

`gpm qa topology` validates province geometry and hierarchy, coverage against
the Natural Earth admin-0 mask, and the adjacency graph. Its deterministic
report is written to `data/processed/topology_qa.json`. Configurable area and
border thresholds live in each profile's `[qa]` table. Invalid geometry is
reported and dependent analysis is marked incomplete rather than repaired.

## M4 Population-Weighted Refinement

M4 extends `gpm build provinces` with optional population GeoTIFF/point inputs,
settlement-point inputs, deterministic profile target allocation, clipped
Voronoi splitting, tiny sibling-fragment merging, and stable child IDs. The M2
candidate output remains unchanged. With no M4 flag or input, the processed
output also retains its M2/M3-compatible behavior.

Each profile's `[refinement]` table defines the area/population blend, minimum
fragment thresholds, per-parent split cap, and seed candidate cap. Input and
license lineage is propagated to every processed feature. Invalid source
geometry is preserved and reported rather than repaired. The complete input
and algorithm contract is documented in `docs/m4-refinement.md`.

## M5 Interactive Review Viewer

M5 adds `gpm review`, a local MapLibre UI served by the Python package. It loads
`data/processed/provinces.geojson` plus optional adjacency and topology QA
outputs, and exposes inspector, lineage, refinement, and QA overlays without a
Node build step. Details live in `docs/m5-review-viewer.md`. Static render
snapshots remain deferred behind the `gpm qa render` placeholder.

## M7 Export Packs

M7 replaces the `gpm export geojson` placeholder and adds `gpm export pack`.
Each generation profile has an `[export]` table controlling layout, region type,
geometry inclusion, definition format, and localization language. Packs land
under `exports/<profile-id>/` with province/region/adjacency definitions,
localization stubs, tables, attribution, and GeoJSON. Details live in
`docs/m7-export.md`.

## M8 Scenario Ownership Overlays

M8 adds curated historical/baseline ownership tables on top of modern province
geometry. Scenario JSON lives in `configs/scenarios/`; `gpm scenario build`
writes ownership CSV/JSON under `data/processed/scenarios/<id>/` using baseline
projection plus country, region, and province overrides. Export packs can embed
scenarios with `--scenario`. Details live in `docs/m8-scenarios.md`.
