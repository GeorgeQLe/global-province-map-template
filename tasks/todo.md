# Todo

## Active

- M25C worldwide historical evidence and reviewed fabric assignment: replace
  the fail-closed pending anomaly inventory with sourced, resolved records,
  assemble the 22-part M49 pass, and obtain independent acceptance.

## Up next (from roadmap)

- M25C global 1444 certification: preserve 1444-v2 as a five-region pilot, then
  complete worldwide inventory, geometry, politics, status, and runtime gates.
- M26 global 1836 certification, reusing the runtime contract and publishing deltas or migrations.
- M27 official 1914 imperial-era pass: German, Austro-Hungarian, Russian, and
  Ottoman empires, reusing the runtime contract.
- M28 1936 reconstruction: interwar borders, mandates, colonies, and strategic
  groupings, reusing the runtime contract. Official-era claims require both
  research acceptance and runtime-pack validation.

## Completed

- [x] M25C certification boundary and pending worldwide lineage: additive
  schema 0.3 contracts, exact 22-part M49 scope, source-locked tolerance rules,
  deterministic pilot provenance, canonical/runtime certification gates,
  bundle integrity validation, and certification-gated 1444 demo promotion.

- [x] M25B game runtime compiler and reference pack: deterministic
  `gpm export runtime`, stable/dense mappings, fixed-width core tables, typed
  CSR graphs, scenario base/deltas, triangulated LOD plus PMTiles geometry,
  hashed revision/migration contract, optional debug symbols, reference loader,
  benchmark harness, and the eight-case synthetic conformance pack.

- [x] M25A historical hard-case casebook: all eight geometry/political classes
  across the four target-era slots, canonical identity and typed-status
  validation, and executable deterministic projection, visual, picking, LOD,
  adjacency, and save/migration fixtures. Synthetic geometry is contract-only.

- [x] M24 start-date research framework: nine pinned pass artifacts, dated
  boundary and polity contracts, typed uncertainty/relationships, full-build
  spatial results, regional coverage gates, schemas, and fail-closed CLI QA.

- [x] M23 historically paintable location fabric: neutral-default province
  builds, versioned split migration, complete source/license lineage,
  fail-closed fabric QA, dated cross-admin fixture, review/export wiring, and
  deterministic 30,003-location production acceptance.

- [x] M22 global PMTiles-first public demo: four native z0–7 scenario archives
  over 4,603 provinces, hero owner dissolves, hierarchy and adjacency overlays,
  generated manifest, PMTiles-only global polygons, cache-safe entrypoints, and
  `gpm demo build` regeneration/validation.
- [x] M21 province → area → region → superregion hierarchy: stable entities,
  province parent fields, hierarchy export layers, CLI/docs/tests.
- [x] M20 broader period geometry prototype/infrastructure: Central Europe packs
  (`ce-1444-v1` / `ce-1836-v1` / `ce-1936-v1`), multi-pack composition
  (`era_geometry_pack_ids`, `apply_era_geometry_packs`), multi-era pack
  `europe-multi-era-v1`, WE+CE scaffold sample, demo refresh, docs
  `docs/m20-broader-period-geometry.md`, tests `tests/test_m20_broader_period_geometry.py`.
  Hard overrides are sample-scoped and do not establish production coverage.
- [x] M19 PMTiles / vector tiles: pure-Python MVT + PMTiles v3 writer,
  `gpm export tiles` (+ `--atlas-dir`), `gpm export atlas --tiles`, tippecanoe
  optional backend, tileset schema/manifest, demo PMTiles vector source + sample
  archives, docs `docs/m19-pmtiles.md`, tests `tests/test_m19_pmtiles.py`.
- [x] M18 culture / religion atlas paint layers: `culture_color` /
  `religion_color` on atlas choropleths, identity legends + optional dissolve,
  `gpm export atlas --no-identity-paint|--no-identity-dissolve`, review viewer
  + demo paint modes, sample/demo regen, docs `docs/m18-culture-religion.md`.
- [x] M17 curation workflow hardening: external curator bundles with manifests,
  `gpm curation list|validate|import|diff|checklist`, ownership diffs (tag
  counts / contested provinces), expanded golden-border suite in
  `gpm qa scenario`, contribution checklist + deprecation policy, sample
  `samples/curator-bundle-example/`, docs `docs/m17-curation.md`.
- [x] M16 multi-era geometry + politics pack prototype/infrastructure: `we-multi-era-v1` with region
  quality matrix + migration notes, era geometry packs `we-1836-v1` /
  `we-1936-v1`, official-1936 curated politics + golden floors, `gpm multi-era`,
  sample `samples/multi-era-we-v1/`, demo 1936 + multi-era live layers, and
  `docs/m16-multi-era.md`. Geometry coverage is illustrative/sample-scoped.
- [x] M15 era-aware geometry v1 prototype/infrastructure: pack format, `gpm era-geometry`, WE 1444 pack
  (`we-1444-v1`) with boundary hints + hard overrides, ID lineage maps, sample
  `samples/era-geometry-we-1444/`, demo toggles, and `docs/m15-era-geometry.md`.
  Hard overrides are sample-scoped and do not establish production coverage.
- [x] M14.5 demo: interactive MapLibre demo under `landing/demo/` (beta WE sample
  eras, adjacency, inspector) plus hero choropleth on the marketing page;
  validation extended for demo assets; reserved UI slots for M15+.
- [x] M14.5 public landing page: static site under `landing/`,
  `gpm release site` validation + optional `--ensure-repo` / `--push` /
  `--deploy` (Vercel), docs `docs/m14.5-landing.md`.
- [x] M14 license-audited beta release: `gpm release beta` with license audit,
  cleaned attribution pack, restricted-path isolation, dual game + atlas faces,
  official-era defaults, sample `samples/beta-license-audited/`, and
  `docs/m14-beta-release.md`.
- [x] M13 second curated official scenario (1444): `official-1444` curated-politics
  overlay with Europe-first elevated depth and global major tags, golden floors,
  `eu-like` recipe, accuracy labeling, and `docs/m13-1444.md`. (1936 deferred.)
- [x] M12 first curated official scenario (1836): `official-1836` curated-politics
  overlay with elevated Europe / North America / colonial theaters, golden
  floors, schema quality-tier metadata, and `docs/m12-1836.md`.
- [x] M11 scenario politics QA + review authoring: `gpm qa scenario` ownership
  coverage/tag/orphan/component/golden checks; `gpm review --scenario` owner
  layers, politics QA overlays, and province_override authoring.
- [x] M10 atlas / SaaS export face: scenario-joined choropleths, tag legends,
  uncertainty layers, owner dissolve, and web-friendly tables via
  `gpm export atlas`.
- [x] M9 public alpha dataset release: sample modern scaffold datasets,
  reproducible recipes, attribution packaging, release tagging, and honest
  accuracy labeling (scaffold vs curated politics vs period geometry).
- [x] M8 historical scenario proof of concept: ownership/controller tables over
  the modern geographic scaffold, with country/region/province override
  tooling rather than baked-in historical geometry.
- [x] M7 export profiles for game templates: province/region/adjacency packs,
  localization stubs, and profile-specific export layouts via `gpm export pack`
  and `gpm export geojson`.
- [x] M6 sea zones, ports, and straits: coastal and ocean sea zones from open
  land geography, coastal land flags, port-to-sea links, sea adjacency, and
  land-to-land strait shortcuts via `gpm build seas` and extended adjacency.
- [x] M5 interactive review viewer: local MapLibre server loads processed
  provinces, adjacency, and topology QA, with attribute inspection, lineage
  display, refinement coloring, and QA finding overlays.
- [x] M4 population-weighted split/merge algorithm: ingest population-count
  GeoTIFF or point GeoJSON plus settlement points, allocate profile targets,
  split with deterministic weighted Voronoi seeds, merge tiny sibling
  fragments, and preserve population/coverage/lineage.
- [x] M3 deterministic IDs, land adjacency, and topology QA: hash normalized
  source geometry into reproducible IDs, generate canonical shared-border CSV,
  and emit CI-gating geometry, coverage, and graph reports.
- [x] M2 first modern global land province draft: ingest downloaded Natural
  Earth admin boundary artifacts into canonical intermediate geometry and
  generate an initial processed land province layer.
- [x] M1 source adapter implementation: download Natural Earth and geoBoundaries
  source artifacts, calculate checksums, record access/version metadata, and write
  source manifests without committing raw geodata.
- [x] Phase 1 repository/tooling scaffold: Python package, `gpm` CLI stubs,
  source catalog, generation profiles, JSON schemas, tests, and documentation.

## Blockers

- None.
