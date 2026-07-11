# Roadmap Progress

Updated: 2026-07-11

Product direction (see root `ROADMAP.md`): dual audience for **strategy-game
seeds** and **historical / SaaS maps**, with a **strong historical accuracy
bar** for official eras. Modern scaffold is foundation; curated politics and
later era-aware geometry are first-class tracks.

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
- M15 era-aware geometry v1: complete. Pack format + `gpm era-geometry` for soft
  boundary hints and hard overrides; WE 1444 pack `we-1444-v1` with ID lineage
  maps; sample and demo layers; docs `docs/m15-era-geometry.md`.
- M16 multi-era geometry + politics packs: complete. `we-multi-era-v1` with
  region quality matrix and migration notes; era geometry packs for 1836 and
  1936; `official-1936` curated politics; `gpm multi-era`; sample + demo;
  docs `docs/m16-multi-era.md`.
- M17 curation workflow hardening: complete. External curator bundles,
  ownership diffs, expanded golden-border suites, contribution checklist;
  `gpm curation`; sample `samples/curator-bundle-example/`;
  docs `docs/m17-curation.md`.

## Next

- Post-M17 product work: culture/religion atlas paint, PMTiles / vector tiles,
  broader period geometry beyond the WE priority region (see root ROADMAP).
