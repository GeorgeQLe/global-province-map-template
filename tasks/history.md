# History

## 2026-07-17 - M25 1444-v2 assembly pending independent review

- Broke the 2026-07-15 evidence stop honestly by narrowing the certification
  claim to one long-lived legal frontier segment per priority region (Scheldt,
  Saône, Rhône, lower Eider, lower Morava), each backed by a date-valid
  academic anchor plus an independent corroborating provenance chain; every
  load-bearing quote was re-verified first-hand and every source pinned by
  SHA-256 in `tasks/m25-evidence-record.md`.
- Assembled the full `official-1444-reconstruction-v2` pass with the
  deterministic `scripts/build-m25-v2-pass.py` (build-fabric, aggregate,
  assemble, render): production `global-h3-v1` fabric with real r1→r2 split
  lineage, constrained 22,000-province aggregation with modern boundary
  influence disabled, measured golden-border tolerances under hard honesty
  caps (25 km Hausdorff, 0.85 overlap ratio; the assembler aborts rather than
  weaken them), corridor-side politics/hierarchy, adjacency sidecars, and
  deterministic five-region SVG review sheets.
- Executed all 20 spatial assertions on the full build, including the
  mandatory Brussels/Nord negative regressions with real measured ratios
  (0.4636 and 0.0577). The Czechia negative subject is the Brno corridor
  province because Prague lies outside every certified corridor in an
  aggregation filler province. Full-build province geometry is emitted as the
  exact union of sidecar location members.
- `gpm qa start-date --pass-dir research/start-dates/1444-v2` fails only on
  the pending independent review, by design; a test-signed copy passes every
  other gate with zero non-review errors
  (`tests/test_m25_v2_production_pass.py`). Two fresh end-to-end runs produce
  byte-identical artifacts (hash snapshots in
  `data/processed/m25-v2-hashes-run{1,2}.txt`).
- Made every certified frontier clip independently reproducible by recording
  its exact measure interval and merge rule over the pinned source substrate;
  the structured schema and runtime validator now reject missing, nonnumeric,
  or reversed substring measures.
- Reworked the five deterministic SVG review sheets around a stable main map
  plus one focus inset per historical frontier and modern negative control,
  including legends, scale bars, georeferencing control labels, residuals,
  error budgets, and main-map focus boxes. Targeted tests pin the structured
  reference contract, inset content, negative-control labeling, and byte
  determinism.
- Ship validation on the assembled boundary: the full suite passed all 285
  tests with no warnings; the unsigned canonical QA command
  exited 1 solely because `manifest.review.status` is not yet `accepted`, as
  required by the fail-closed review contract. Diff whitespace and targeted
  credential-pattern scans were clean.
- Pipeline changes in `src/gpm`: `builders/locations.py` split-request
  application now uses an STRtree with a geometry cache (25+ min → ~1 min) and
  treats refine_h3 requests on an exhausted grid as benign no-ops while
  split_by_boundary stays strict; `qa/fabric.py` paintability QA clips the
  global edge network to the boundary envelope before buffering (~60 min →
  seconds). Both are covered by the existing fabric tests plus a new
  exhausted-grid regression test.
- Next project task: independent human review of the v2 review sheets and
  georeferencing records, then sign-review and the final QA gate.

## 2026-07-15 - M25 v2 acceptance infrastructure

- Added native Draft 2020-12 schema 0.2 validation while preserving the rejected
  schema 0.1 `official-1444-reconstruction-v1` fixture and its exact 14-error
  gate; v2 documents are no longer projected onto v1 contracts.
- Added hashed derived-evidence, georeferencing/residual, independent-source,
  kilometre golden-border, typed-politics, hierarchy, constraint-hash,
  aggregation/adjacency, and independent-review checks.
- Added historical-constraint-aware aggregation and deterministic five-region
  SVG review-sheet generation via `gpm qa render`.
- Added a complete passing miniature v2 pass and adversarial gates for missing
  coverage masks, copied modern geometry, invalid lineage, hard-constraint
  crossings, incomplete politics/hierarchy, bad adjacency, and tampered review
  artifacts. The focused M23–M25 suite now has 50 passing tests and the complete
  repository suite has 277.
- Rechecked source availability and stopped before production r2: the surfaced
  Burgundy scholarship, circa-1500/16th-century HRE datasets, and 1558 Brabant
  raster do not provide date-valid, independently corroborated reconstruction
  for every certified 1444 frontier in all five priority regions.
- Kept M25 active: no v2 artifact or acceptance claim was created without the
  missing B-grade research, real r1→r2 split lineage, and human reviewer.

## 2026-07-15 - Comprehensive Roadmap and Runtime Review

- Audited M0–M28 claims against implementation, tests, public artifacts, and
  the M0–M23, M24, and M25 acceptance evidence. Retained M25 as **FAIL/active**
  and preserved its withdrawn candidate as chronological rejection evidence.
- Classified M15, M16, and M20 as prototype/infrastructure complete and marked
  M7 exports and M19 PMTiles as foundations to reuse, not production historical
  coverage or a game-runtime implementation.
- Separated canonical research/authoring artifacts, compiled runtime assets,
  and optional debug/evidence assets. Fixed the `eu-like` runtime target at
  22,000 provinces with persistent stable IDs and pack-local dense indices.
- Inserted planned M25.5 after M25: an engine-neutral runtime compiler,
  reference pack/loader, deterministic compact tables and CSR graphs,
  scenario deltas, LOD/tiled geometry, compatibility revisions, migrations,
  debug symbols, and measurable size/startup/memory/tile-read gates.
- Sequenced M26–M28 through the runtime contract and required both canonical
  research acceptance and runtime-pack validation for official-era claims.
  This review changed roadmap documentation only; runtime implementation remains
  deferred to M25.5.

## 2026-07-14 - M25 Independent Acceptance Audit

- Rejected and withdrew the initial M25 candidate: its 15 synthetic `loc-*`
  assignments and manually coupled rectangles were not the canonical M23
  fabric or the required 22,000-province production aggregation.
- Independently retrieved and hashed the four cited historical maps. Their
  represented dates bracket 1444, but the pass had no georeferencing controls
  or per-boundary traceability, so historical frontiers were downgraded to soft
  evidence and coverage to C/U.
- Hardened `gpm qa start-date` with transitive fabric sidecars, location and
  split-lineage checks, membership-derived IDs and geometry unions, production
  count enforcement, positive hard-evidence gating, and overlap rejection.
- Rebuilt the 30,003-location M23 fabric and 22,000-province neutral aggregation
  twice in temporary storage. This proved the production pipeline remains
  available but does not convert the missing historical reconstruction into a
  release. Final M25 audit verdict: **FAIL; milestone active**.

## 2026-07-14 - M25 1444 Initial Candidate (superseded by audit)

- Generated `official-1444-reconstruction-v1` as a deterministic nine-artifact
  M24 research pass covering the Low Countries, Burgundy, France, the HRE, and
  Central Europe.
- Added reviewed historical-cartography lineage, pinned open modern negative
  controls, a typed polity/dependency gazetteer, and accepted Brussels/Nord
  targeted location splits.
- Initially published B geometry/politics/relationship and C hierarchy grades;
  the independent audit later found these grades unsupported and replaced them
  with C/U.
- Executed 15 full-build spatial gates with zero findings, including the named
  Brussels-Capital Region and French Nord department negative regressions.

## 2026-07-13 - M24 Start-Date Research Framework

- Implemented the nine-artifact start-date pass manifest and machine-readable
  schemas for research sources, dated boundaries, polity relationships,
  location assignments/splits, golden definitions, pinned full-build geometry,
  coverage, and changes.
- Added fail-closed `gpm qa start-date` validation for checksums, containment,
  cross-artifact IDs, source review, revision pins, executed priority-region
  spatial assertions, mandatory coverage layers, A-grade certification, and
  changelog versioning.
- Added a complete miniature geometry pass plus adversarial schema, reference,
  temporal, containment, checksum, grade, spatial, CLI, and packaging coverage.

## 2026-07-13 - Ship M23 and M0–M23 Acceptance Remediation

- Committed and pushed the M23 neutral-fabric implementation plus comprehensive
  M0–M23 acceptance remediation to `main` at `3421971`.
- Redeployed `landing/` to Vercel production at
  `https://landing-six-iota-32.vercel.app`.
- Production smoke checks confirmed landing/demo HTTP 200, the accepted
  4,603-province / 10,779-edge / 659-area manifest, and valid immutable PMTiles
  byte-range delivery.
- Next: implement the M24 start-date research framework contract.

## 2026-07-13 - M0–M23 Comprehensive Acceptance Remediation

- Re-audited every completed milestone with 238 local assertions, installed-wheel
  smoke tests, duplicate global/fabric/demo builds, canonical release rebuilds,
  and read-only GitHub/Vercel/browser checks.
- Deterministically partitioned Natural Earth admin-layer conflicts so the
  4,603-province legacy compatibility build passes strict topology QA with zero
  errors; release packaging now rejects failing topology snapshots.
- Fixed installed-wheel omission of official scenario golden checks and repaired
  obsolete 1936 Chinese subdivision rules plus the Germany golden floor.
- Regenerated the M22 demo at 10,779 edges and 659/169/8 hierarchy entities;
  replaced the obsolete M23+ density future slot with M24–M28 reconstruction work.
- Confirmed two byte-identical 30,003-location fabrics, 52,142 adjacency rows,
  the documented 31/40 reference warnings, and a 22,000-province 1444 aggregation.
- Full evidence and milestone verdicts: `tasks/m0-m23-acceptance-audit.md`.

## 2026-07-13 - M23 Location-Fabric Acceptance

- Made the neutral `locations.geojson` fabric the default province-build path;
  retained the former builder behind `--legacy-modern-admin`.
- Added explicit source/output fabric revisions for targeted split migrations,
  actual-split-only parent/child lineage, unchanged-ID preservation, and a
  dated 1444 cross-modern-admin fixture.
- Replaced hard-coded Natural Earth attribution with structured actual-input
  and license lineage for land, admin, and optional signal inputs.
- Made adjacency, intersections, lineage, manifest, declared-file, revision,
  and land coverage checks fail closed; closed the planar Antarctic cap gap.
- Production acceptance built 30,003 locations and 52,142 adjacency rows twice
  with byte-identical fixed-timestamp outputs, passed strict QA with zero
  errors, retained stable upstream warnings for 31 admin-0 and 40 admin-1 gaps,
  and aggregated the `eu-like` 1444 profile to 22,000 provinces.

## 2026-07-13 - Historical Location-Fabric Roadmap Revision

- Reframed the production pipeline as source layers → neutral atomic locations
  → era/profile provinces → scenario politics and hierarchy → exports.
- Preserved M15, M16, and M20 as **prototype/infrastructure complete** while
  recording that their hard overrides are sample-scoped, not production
  historical coverage.
- Replaced the former parent-constrained M23 density milestone with a neutral
  historically paintable location fabric and added the M24 repeatable
  start-date research/certification framework.
- Sequenced independent reconstruction releases: M25 1444, M26 1836, M27
  official 1914 imperial era, and M28 1936, each with regional coverage grades.
- Added mandatory full-build spatial golden-border tests and the 1444
  Brussels/Nord negative-anachronism regression.

## 2026-07-13 - M20–M22 Release Preparation

- Reconciled M20 prototype period-geometry infrastructure, M21 hierarchy, and
  M22 global PMTiles-first demo as one release boundary; the later roadmap
  revision superseded the original M23 design contract.
- Hardened the public static interface with M22 query-string cache busting,
  manifest revalidation on demo load, and a long-lived immutable PMTiles cache
  rule compatible with byte-range delivery.
- Regenerated and validated the canonical global demo build before preview
  deployment; production promotion remains gated on explicit approval.
- Visual QA removed stale landing “Next” copy and the obsolete M20 future card;
  at that time, only the now-superseded M23 density design was future work.
- Next: review the Vercel preview evidence and approve or decline promotion.

## 2026-07-11 - M20 Broader Period Geometry Prototype (Beyond Western Europe)

- Central Europe era-geometry packs `ce-1444-v1`, `ce-1836-v1`, `ce-1936-v1`
  (soft frontier bands + sample hard overrides for AUT/CZE/POL/HUN).
- Multi-pack composition: `apply_era_geometry_packs`, multi-era
  `era_geometry_pack_ids`, preserved scaffold lineage across steps.
- Multi-era pack `europe-multi-era-v1` composes WE + CE for 1444 / 1836 / 1936
  with multi-region quality matrix.
- Samples: `scaffold-we-ce`, `era-geometry-ce-1444`, `multi-era-europe-v1`.
- Demo refreshed to WE+CE scaffold and Europe period layers / merged hints.
- Docs `docs/m20-broader-period-geometry.md`; tests
  `tests/test_m20_broader_period_geometry.py`.
- Prototype/infrastructure completion only: hard overrides target sample IDs and
  do not constitute production historical coverage.
- Next: further priority regions or denser hard overrides (post-M20).

## 2026-07-11 - Ship M19 PMTiles / Vector Tiles

- Committed and pushed M19 PMTiles / vector tiles (encoder, CLI, atlas
  `--tiles`, demo source, schema, docs, tests) to `main`.
- Deploy skipped: no explicit manual deploy contract (`deploy.md` or
  `tasks/deploy.md`).
- Next: broader period geometry beyond the WE priority region (post-M19).

## 2026-07-11 - M19 PMTiles / Vector Tiles

- Pure-Python MVT encoder + PMTiles v3 writer (`gpm.tiles`); optional tippecanoe
  backend when installed.
- CLI: `gpm export tiles` (GeoJSON or `--atlas-dir`); `gpm export atlas --tiles`.
- Schema `tileset-manifest`; docs `docs/m19-pmtiles.md`; tests
  `tests/test_m19_pmtiles.py`.
- Demo: ownership PMTiles per scenario, MapLibre `pmtiles` protocol toggle.
- Next: broader period geometry beyond the WE priority region (post-M19).

## 2026-07-11 - Ship M18 Culture / Religion Atlas Paint

- Committed and pushed M18 culture/religion atlas paint (export, viewer, demo,
  samples, docs, tests) to `main`.
- Deploy skipped: no explicit manual deploy contract (`deploy.md` or
  `tasks/deploy.md`).
- Next: PMTiles / vector tiles, broader period geometry (post-M18).

## 2026-07-11 - M18 Culture / Religion Atlas Paint Layers

- Extended `gpm export atlas` with culture/religion colors, identity legends
  (`culture_legend.json` / `religion_legend.json`), optional dissolve, and
  CLI flags `--no-identity-paint` / `--no-identity-dissolve`.
- Review viewer color modes + demo culture/religion layer toggles; demo
  legends and GeoJSON identity colors regenerated.
- Sample beta atlas scenarios refreshed; docs `docs/m18-culture-religion.md`;
  tests `tests/test_m18_culture_religion.py`.
- Next: PMTiles / vector tiles, broader period geometry (post-M18).

## 2026-07-11 - Ship M15–M17 + landing redeploy

- Committed and pushed M15 era geometry, M16 multi-era packs / official-1936,
  and M17 curation workflow to `main`.
- Redeployed `landing/` to Vercel production (`gpm release site --deploy`).
- Next: post-M17 product work (culture/religion paint, PMTiles, broader
  period geometry) from roadmap.

## 2026-07-11 - M17 Curation Workflow Hardening

- Added external curator bundles (`bundle_manifest.json`) with license lineage,
  golden paths, contribution checklist, and deprecation policy fields.
- `gpm curation list|validate|import|diff|checklist` for community workflow.
- Ownership diffs: tag counts, owner/controller/disputed changes, contested
  provinces; schema `scenario-diff-report`.
- Expanded golden-border suite in `gpm qa scenario`: max counts, required /
  forbidden owners, disputed flags, border pairs, owner-adjacency floors.
- Sample `samples/curator-bundle-example/`; docs `docs/m17-curation.md`;
  tests `tests/test_m17_curation.py`.
- Next: culture/religion paint, PMTiles, broader period geometry (post-M17).

## 2026-07-11 - M16 Multi-Era Geometry + Politics Packs

- Added multi-era pack system: `configs/multi_era/`, region quality matrix,
  migration notes, and `gpm multi-era list|validate|build|migration`.
- Era geometry packs `we-1836-v1` and `we-1936-v1` alongside existing
  `we-1444-v1`; multi-era pack `we-multi-era-v1` pairs geometry + politics for
  three official eras with per-region quality tiers.
- Official HOI-leaning scenario `official-1936` (curated-politics) with golden
  floors, recipe, and accuracy-label recognition; beta defaults include 1936.
- Sample under `samples/multi-era-we-v1/`; demo ships live 1936 tab and period
  geometry / boundary hints for 1444 / 1836 / 1936.
- Docs `docs/m16-multi-era.md`; tests `tests/test_m16_multi_era.py`.
- Prototype/infrastructure completion only: hard geometry is sample-scoped.
- Next project task was M17 curation workflow hardening (completed).

## 2026-07-10 - M15 Era-Aware Geometry v1 (Western Europe 1444)

- Added era-geometry pack system: `configs/era_geometry/`, schemas for packs and
  lineage maps, and `gpm era-geometry list|validate|apply`.
- Modes: soft `boundary_hints` overlays + hard `replace`/`split`/`identity`
  overrides with scaffold↔era ID lineage (JSON + CSV).
- Bundled priority pack `we-1444-v1` for official-1444 Western Europe; sample
  under `samples/era-geometry-we-1444/`; demo toggles for period geometry and
  boundary hints; quality labeling notes priority-region scope.
- Docs `docs/m15-era-geometry.md`; tests `tests/test_m15_era_geometry.py`.
- Prototype/infrastructure completion only: hard overrides target sample IDs.
- Next project task was M16 multi-era geometry + politics packs (completed).

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
- Next project task was M15 era-aware geometry v1 (completed later the same day).

## 2026-07-10 - M14.5 Public Landing Page + Vercel Deploy

- Added static marketing site under `landing/` (project thesis, dual audiences,
  pipeline, quality tiers, license policy, get-started).
- Added `gpm release site`: validate required files/content, optional
  `--ensure-repo` via `gh`, `--push` commit of landing assets, and `--deploy`
  to Vercel (`vercel deploy --yes [--prod]`).
- Added `docs/m14.5-landing.md` and tests for validation + CLI dry-run.
- Next project task was M15 era-aware geometry v1 (completed later the same day).

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
