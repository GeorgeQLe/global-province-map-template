# Roadmap Progress

Updated: 2026-07-13

Product direction (see root `ROADMAP.md`): dual audience for **strategy-game
seeds** and **historical / SaaS maps**, with a **strong historical accuracy
bar** for official eras. The future production pipeline is source layers →
neutral atomic locations → era/profile provinces → scenario politics and
hierarchy → exports. Modern admin geometry is reference input and a hard
constraint only for modern profiles.

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
- M22 global PMTiles-first demo: complete. Four scenario archives over the
  4,603-province global build, hero dissolves, hierarchy and adjacency overlays,
  regenerated manifest, and cache-safe public entrypoints.
- M23 historically paintable location fabric: complete. Neutral cross-admin
  H3 cells, stable location IDs, configurable modern-boundary influence,
  versioned aggregations, QA, and targeted split lineage ship through explicit
  `gpm build locations` and neutral-default `gpm build provinces` commands.
  Production acceptance: 30,003 locations, 52,142 adjacency rows, strict QA
  with zero errors, deterministic duplicate build, and documented Natural
  Earth incomplete-coverage warnings (31 admin-0 / 40 admin-1).

## Next

- M24 start-date research framework: dossiers, dated boundary registry, polity/
  dependency gazetteer, uncertainty, spatial golden borders, coverage matrices,
  and changelogs. Contract: `docs/m24-start-date-research-framework.md`.
- M25 1444 reconstruction (including mandatory Brussels/Nord negative-
  anachronism regression), M26 1836, M27 official 1914 imperial-era, and M28
  1936. Each pass is independently versioned/releasable with regional grades.
