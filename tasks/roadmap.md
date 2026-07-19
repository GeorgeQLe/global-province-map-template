# Roadmap Progress

Updated: 2026-07-19

Product direction (see root `ROADMAP.md`): dual audience for **strategy-game
seeds** and **historical / SaaS maps**, with a **strong historical accuracy
bar** for official eras. The future production pipeline is source layers →
neutral atomic locations → era/profile provinces → scenario politics and
hierarchy → canonical pass → runtime compiler → engine-neutral runtime pack.
Modern admin geometry is reference input and a hard constraint only for modern
profiles.

## Canonical claim matrix

`ROADMAP.md` is canonical. This matrix maps every milestone to its current
claim, implementation entry point, executable evidence, public artifact, and
remaining gap. “Prototype” is intentionally not equivalent to production
historical coverage.

| Milestone | Status | Implementation | Executable evidence | Public artifact | Remaining gap |
| --- | --- | --- | --- | --- | --- |
| M0 | complete | `ROADMAP.md`, `DATA_SOURCES.md`, `tasks/` | policy/schema tests | repository docs | none in scope |
| M1 | complete | `gpm sources`; `gpm.sources` | source artifact/manifest/registry tests | configs and schemas | live source availability varies |
| M2 | complete | `gpm build provinces --legacy-modern-admin` | duplicate legacy build | modern scaffold samples | compatibility path only |
| M3 | complete | IDs, adjacency, `gpm qa topology` | deterministic build and topology tests | demo adjacency | documented warnings |
| M4 | complete | `gpm.builders.refinement` | `test_m4_refinement.py` | methodology docs | none in scope |
| M5 | complete | `gpm review` | `test_m5_review.py` | packaged viewer | local authoring surface |
| M6 | complete | `gpm build seas`; mixed adjacency | `test_m6_seas.py` | exportable sea data | gameplay policy varies |
| M7 | complete | `gpm export pack/geojson` | `test_m7_export.py` | alpha/beta game packs | reused by M25B; not runtime compiler |
| M8 | complete | `gpm scenario` | `test_m8_scenarios.py` | scenario configs | overlay tooling, not era certification |
| M9 | complete | `gpm release alpha` | `test_m9_release.py` | alpha sample | scaffold accuracy only |
| M10 | complete | `gpm export atlas` | `test_m10_atlas.py` | beta atlas/demo | none in scope |
| M11 | complete | `gpm qa scenario`; review authoring | `test_m11_scenario_qa.py` | review UI | not full research acceptance |
| M12 | complete | `official-1836` politics | scenario golden QA | deployed scenario/sample | curated politics, not period geometry/runtime |
| M13 | complete | `official-1444` politics | scenario golden QA | deployed scenario/sample | curated politics, not M25 reconstruction |
| M14 | complete | `gpm release beta` | `test_m14_beta.py` | beta sample | scaffold geometry remains labeled |
| M14.5 | complete | landing/demo and `gpm release site` | landing validator/browser audit | deployed landing/demo | none in scope |
| M15 | prototype/infrastructure complete | `gpm era-geometry`; WE packs | `test_m15_era_geometry.py` | WE sample/demo | sample-scoped; reused, not certified |
| M16 | prototype/infrastructure complete | `gpm multi-era`; era packs | `test_m16_multi_era.py` | multi-era sample/demo | sample-scoped geometry |
| M17 | complete | `gpm curation` | `test_m17_curation.py` | curator bundle sample | continuing curation |
| M18 | complete | culture/religion atlas paint | `test_m18_culture_religion.py` | demo paint modes | curated hints only |
| M19 | complete | `gpm export tiles`; PMTiles writer | `test_m19_pmtiles.py` | PMTiles demo archives | reused by M25B; not runtime compiler |
| M20 | prototype/infrastructure complete | CE packs and pack composition | `test_m20_broader_period_geometry.py` | WE+CE samples/demo | sample-scoped; not certified coverage |
| M21 | complete | `gpm build hierarchy` | `test_m21_hierarchy.py` | hierarchy overlays | historical memberships need accepted passes |
| M22 reset | complete | `gpm demo build`; release validator | Modern-only demo and uncertified-era rejection tests | global Modern PMTiles demo | historical tabs await global certification |
| M23 | complete | `gpm build locations/provinces`; fabric QA | duplicate 30,003-location and 22,000-province builds | source/docs; no hosted fabric claimed | documented reference warnings/build-drift audit note |
| M24 | complete | schemas and `gpm qa start-date` | `test_m24_start_date_framework.py` | contract and rejected-pass evidence | framework only; does not certify an era |
| M25A | complete | hard-case casebook + typed-status schema | eight executable per-class canonical/runtime/visual/picking/LOD/adjacency/save fixtures | research artifacts only | synthetic contract fixtures, not historical evidence |
| M25B | complete | `gpm export runtime`; `gpm.runtime` | `test_m25b_runtime.py`; duplicate-build/budget benchmarks | synthetic runtime reference pack | global-scale budgets re-run per certified era |
| M25C | planned; v2 pilot preserved | global 1444 pass; v2 assembler/evidence | worldwide research and runtime validation | unsigned v2 research candidate only | complete worldwide inventory and geometry |
| M26 | planned | global 1836 pass + runtime delta/migration | worldwide research and runtime validation | none yet | begins after M25C |
| M27 | planned | 1914 canonical pass + runtime delta/migration | future research and runtime validation | none yet | begins after M26 |
| M28 | planned | 1936 canonical pass + runtime delta/migration | future research and runtime validation | none yet | begins after M27 |

## Completed

- M0 planning repository: complete. The roadmap and data-source policy are in
  place.
- Phase 1 repository/tooling foundation: complete. The repository now has a
  Python package scaffold, command-line entrypoint, source policy config,
  generation profiles, schemas, tests, and Phase 1 documentation.
- M1 source adapters and manifests: complete. Natural Earth and geoBoundaries
  adapters can dry-run planned artifacts, download raw source files into ignored
  local storage, capture checksums/access/version metadata, and persist build
  manifests.
- M2 first modern global land province draft: complete. `gpm build provinces`
  now reads downloaded Natural Earth admin boundary zips, writes canonical land
  province candidates, and emits an initial processed land province GeoJSON
  layer.
- M3 deterministic IDs, adjacency, and topology QA: complete. Province IDs are
  reproducible from source identity and normalized geometry, land adjacency is
  spatial-indexed and canonical, and CI-gating QA reports geometry, coverage,
  and graph findings without repairing inputs.
- M4 population-weighted split/merge algorithm: complete. Profile-budgeted
  deterministic Voronoi splitting consumes population rasters/points and
  settlement seeds, merges tiny sibling fragments, and preserves input and
  license lineage.
- M5 interactive review viewer: complete. `gpm review` serves a local MapLibre
  UI over processed provinces, adjacency, and topology QA with inspector,
  lineage, refinement coloring, and finding overlays.
- M6 sea zones, ports, and straits: complete. `gpm build seas` emits coastal and
  ocean sea zones with stable IDs and coastal land flags; `gpm build adjacency`
  adds sea, port-to-sea, and strait edges when sea zones are present.
- M7 export profiles for game templates: complete. `gpm export pack` writes
  province/region/adjacency definitions, localization stubs, tables,
  attribution, and GeoJSON under `exports/<profile-id>/`; `gpm export geojson`
  writes the geometry subset. Profile `[export]` tables select layout and
  region type.
- M8 historical scenario proof of concept: complete. Scenario JSON definitions
  layer owner/controller/cores/claims over modern provinces via baseline
  projection plus country/region/province overrides. `gpm scenario list|validate|build`
  write processed scenario tables; `gpm export pack --scenario` embeds them.
  Overlay tooling only—not yet curated official-era accuracy.
- M9 public alpha dataset release: complete. `gpm release alpha` packages packs,
  recipes, attribution, release tags, and scaffold-baseline accuracy labels;
  committed sample under `samples/alpha-modern-scaffold/`.
- M10 atlas / SaaS export face: complete. `gpm export atlas` writes scenario-
  joined choropleths, deterministic tag legends, uncertainty layers, owner-
  dissolved multipolygons, and web-friendly CSV/JSON tables under
  `exports/atlas/<profile-id>/`.
- M11 scenario politics QA + review authoring: complete. `gpm qa scenario`
  validates ownership coverage, tags, orphan cores/claims, owner components,
  and golden checks. `gpm review --scenario` paints ownership layers and
  writes curator province_overrides into scenario JSON.
- M12 first curated official scenario (1836): complete. `official-1836` ships
  as curated-politics with elevated Europe / North America / colonial theater
  depth, golden tag floors, and official-era metadata.
- M13 second curated official scenario (1444): complete. `official-1444` ships
  as curated-politics with Europe-first elevated depth, global major tags,
  golden floors, and `eu-like` recipe. Interwar 1936 deferred to a later
  milestone.
- M14 license-audited beta release: complete. `gpm release beta` packages game +
  atlas faces with license audit, cleaned attribution, restricted-path
  isolation, and official-era defaults; sample under
  `samples/beta-license-audited/`.
- M14.5 public landing page: complete. Static site under `landing/` describes
  dual audiences, pipeline, quality tiers, and license policy.
  `gpm release site` validates and can ensure a GitHub remote, push, and deploy
  to Vercel.
- M15 era-aware geometry v1: **prototype/infrastructure complete**. Pack format
  + `gpm era-geometry` for soft
  boundary hints and hard overrides; WE 1444 pack `we-1444-v1` with ID lineage
  maps; sample and demo layers. Hard overrides are sample-scoped and do not
  establish production coverage; docs `docs/m15-era-geometry.md`.
- M16 multi-era geometry + politics packs: **prototype/infrastructure
  complete**. `we-multi-era-v1` with
  region quality matrix and migration notes; era geometry packs for 1836 and
  1936; `official-1936` curated politics; `gpm multi-era`; sample + demo;
  docs `docs/m16-multi-era.md`. Geometry labels remain illustrative until
  full-build reconstruction passes certify named regions.
- M17 curation workflow hardening: complete. External curator bundles,
  ownership diffs, expanded golden-border suites, contribution checklist;
  `gpm curation`; sample `samples/curator-bundle-example/`;
  docs `docs/m17-curation.md`.
- M18 culture / religion atlas paint layers: complete. Atlas identity paint
  (`culture_color` / `religion_color`, legends, dissolve), demo + review
  viewer modes, sample refresh; docs `docs/m18-culture-religion.md`.
- M19 PMTiles / vector tiles: complete. Pure-Python MVT + PMTiles writer,
  `gpm export tiles`, atlas `--tiles`, demo vector source; docs
  `docs/m19-pmtiles.md`.
- M20 broader period geometry: **prototype/infrastructure complete**. Central
  Europe packs
  `ce-1444-v1` / `ce-1836-v1` / `ce-1936-v1`; multi-pack composition via
  `era_geometry_pack_ids` and `apply_era_geometry_packs`; multi-era pack
  `europe-multi-era-v1`; scaffold `samples/scaffold-we-ce/`; samples + demo;
  docs `docs/m20-broader-period-geometry.md`. Hard overrides are sample-scoped.
- M21 four-level hierarchy: complete. Stable area, region, and superregion
  entities; enriched province parents; hierarchy exports and demo overlays;
  docs `docs/m21-hierarchy.md`.
- M22 public reset: complete. One Modern baseline archive over the 4,603-province
  global build, hero dissolve, hierarchy and adjacency overlays, regenerated
  manifest, and fail-closed uncertified-era validation.
- M23 historically paintable location fabric: complete. Neutral cross-admin
  H3 cells, stable location IDs, configurable modern-boundary influence,
  versioned aggregations, QA, and targeted split lineage ship through explicit
  `gpm build locations` and neutral-default `gpm build provinces` commands.
  Production acceptance: 30,003 locations, 52,142 adjacency rows, strict QA
  with zero errors, deterministic duplicate build, and documented Natural
  Earth incomplete-coverage warnings (31 admin-0 / 40 admin-1).

## Next

- M25C global 1444 certification. The 1444-v2 candidate remains an unsigned
  five-region pilot and evidence set, not a release boundary.
- M26 1836, M27 official 1914 imperial-era, and M28 1936 reuse that runtime
  contract. They publish scenario-only deltas when geometry membership is
  unchanged and explicit migration metadata when it changes.
