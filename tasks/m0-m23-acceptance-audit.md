# M0–M23 Comprehensive Acceptance Audit

Date: 2026-07-13 (America/New_York)

Scope: the current worktree, including the M23 implementation. M15, M16, and
M20 are assessed only as prototype/infrastructure milestones. M24–M28 remain
future work. No push, release publication, Vercel deployment, or production
promotion was performed.

## Executive verdict

Repository-local acceptance passes after remediation. There are no remaining
local release-blocking test, schema, topology, scenario-politics, license,
landing, hierarchy, demo-manifest, or fabric-QA errors. The only milestone
warnings are public-surface lag: GitHub `main` and the Vercel production alias
still expose the pre-remediation M22 commit because external writes were out of
scope. The deployed demo remains functional, but its manifest and generated
assets are older than this accepted worktree.

Final complete suite: **238 passed**. `git diff --check` and landing dry-run
validation also passed.

## Canonical acceptance matrix

| Milestone | Claimed scope and implementation entry points | Automated/reproducible evidence | Public evidence | Verdict |
|---|---|---|---|---|
| M0 | Planning, source policy, roadmap; `README.md`, `ROADMAP.md`, `DATA_SOURCES.md`, `tasks/*` | Source-policy/registry/schema tests; documentation contradiction audit | Files present on GitHub `main` | **pass** |
| M1 | Natural Earth/geoBoundaries planning, downloads, checksums, manifests; `gpm sources`, `gpm.sources.*` | `test_source_artifacts`, `test_source_manifest_schema`, `test_source_registry`; installed-wheel `sources manifest` | Source/config files present on GitHub | **pass** |
| M2 | Explicit legacy Natural Earth land draft; `gpm build provinces --legacy-modern-admin` | Two 4,603-feature builds; candidate/province hashes identical | Pre-remediation implementation on GitHub | **pass** |
| M3 | Stable IDs, 10,779-edge adjacency, strict topology QA; builders and `gpm.qa.topology` | Duplicate hashes; complete QA, 0 errors/376 warnings; focused ID/adjacency/topology tests | Deployed demo still uses old 10,781-edge assets | **pass** |
| M4 | Deterministic refinement/split/merge with lineage; `gpm.builders.refinement` | `test_m4_refinement`, CLI error/fixture coverage | Not a public runtime surface | **pass** |
| M5 | Packaged review server/UI and authoring surface; `gpm review`, `gpm.viewer` | `test_m5_review`; viewer static assets present in installed wheel | Not publicly claimed as hosted review API | **pass** |
| M6 | Seas, ports, straits and mixed adjacency; `gpm build seas` | `test_m6_seas`, adjacency regression suite | Not separately hosted | **pass** |
| M7 | Game pack and GeoJSON exports; `gpm export pack|geojson` | `test_m7_export`; alpha/beta inventories exact | Generated samples present on GitHub | **pass** |
| M8 | Scenario overlay schema/list/validate/build; `gpm scenario` | `test_m8_scenarios`; installed-wheel scenario listing | Four eras exposed in deployed demo | **pass** |
| M9 | Alpha packaging, attribution, recipe, accuracy labels; `gpm release alpha` | Full 4,603-province rebuild; 30/30 files declared/present; passing topology snapshot | Committed sample on GitHub | **pass** |
| M10 | Atlas/SaaS face, dissolves, legends, uncertainty; `gpm export atlas` | `test_m10_atlas`; beta atlas rebuilt for four scenarios | Deployed choropleths load | **pass** |
| M11 | Scenario-politics QA and review authoring | `test_m11_scenario_qa`; complete adjacency/golden analysis | Inspector/paint UI loads | **pass** |
| M12 | Official 1836 curated-politics contract | Golden QA: 4,603 rows, 188 owner tags, 0 errors | 1836 deployed tab loads | **pass** |
| M13 | Official 1444 curated-politics contract | Golden QA: 4,603 rows, 198 owner tags, 0 errors | 1444 deployed tab loads | **pass** |
| M14 | License-audited beta, isolated/restricted behavior, game + atlas faces | 105/105 files declared/present; license audit `passed=true`; topology pass | Beta sample/source present on GitHub | **pass** |
| M14.5 | Static landing/demo validation and deploy tooling | Landing validator and tests pass; exact HTTP/range probes and browser smoke pass | Production is functional but behind accepted local assets | **warning** |
| M15 | Prototype era-geometry pack/apply/lineage, sample-scoped WE 1444 | `test_m15_era_geometry`; pack list/validate and samples | Period toggle works; not treated as certified coverage | **pass (prototype)** |
| M16 | Prototype multi-era packaging and official-1936 politics | `test_m16_multi_era`; 1936 golden QA now 0 errors after subdivision-code repair | 1936 deployed tab loads, but deployed politics predate repair | **pass (prototype)** |
| M17 | External curation bundles, diffs, checklist, golden borders | `test_m17_curation`; installed-wheel bundle validation | Example bundle present on GitHub | **pass** |
| M18 | Culture/religion paint, legends, dissolves | `test_m18_culture_religion`; browser toggles succeed | Both deployed paint modes render | **pass** |
| M19 | MVT/PMTiles v3 writer and range reads | `test_m19_pmtiles`; four deterministic archives; valid `PMTiles\x03` range response | Production returns HTTP 206 and immutable caching | **pass** |
| M20 | Prototype CE packs and WE+CE composition | `test_m20_broader_period_geometry`; configs/samples/docs | Sample period assets deploy; no production-certification claim | **pass (prototype)** |
| M21 | Stable province/area/region/superregion entities and exports | `test_m21_hierarchy`; normalized production rebuild: 659/169/8 | Old production has 660/169/8 until redeploy | **pass** |
| M22 | Four-scenario global PMTiles-first demo and manifest | Two normalized demo builds match after removing generated timestamps; 4,603 provinces, 10,779 edges, z0–7; local validation passes | Functional but stale production manifest/assets | **warning** |
| M23 | Neutral atomic fabric, split lineage, aggregation, review/export separation | Two byte-identical 30,003-location/52,142-edge builds; strict QA 0 errors; 31 admin-0 and 40 admin-1 warning members; 22,000-province 1444 aggregation | Current M23 source/docs are not yet pushed or deployed | **warning** |

## Production-scale evidence

### Legacy global compatibility pipeline

Two clean temporary builds produced 4,603 provinces. After remediation both
province documents and adjacency tables are byte-identical:

- `provinces.geojson`: `e4f73577b495c08426360907dea32e8f0c837c658594b53f6ba9a83b6639ae4b`
- `adjacency.csv`: `bce724da6155ed3c72ad23039b5eace7b20980eaf2de112da4d95f4c192ab4ef`
- adjacency rows: 10,779
- topology QA: pass, 0 errors, 376 warnings, complete coverage and graph analysis
- hierarchy: 659 areas, 169 regions, 8 superregions

The warning set is non-blocking: islands/connected components, mask repair, and
sub-threshold gap/overlap artifacts. Positive-area disputed overlaps, large
gaps, and admin-layer outside-mask conflicts are no longer present.

### Releases

- Alpha: 4,603 provinces, 10,779 adjacency rows, two scenarios, 30 declared and
  30 actual files; manifest SHA-256
  `d70cc5939140996d7baef7d1ace9cb44aa22751f483cfbbd4da759c5bc1d66f8`.
- Beta: 4,603 provinces, 10,779 adjacency rows, four scenarios, 105 declared and
  105 actual files; manifest SHA-256
  `b95f96781a74dfce9dfe154a5a227cf79385a44ac5eb6e442a0542769e2b2ff6`.
- Both copied passing zero-error topology reports. Beta license audit passed
  with five attribution records and no restricted-source leakage.

### M22 demo

Two builds produced identical PMTiles and normalized JSON/GeoJSON after only
explicit generated timestamps/paths were removed. Canonical PMTiles hashes:

- modern: `d622c6f869cdf0d18acd4836397da26d16f1cc095c52a4470d1ed9e7cd31e249`
- 1444: `5c129b7e77d07e36a1cb1b0841dcc95050685095af22ff99668eda91b7229324`
- 1836: `e04e178ba173aa700961e37030f464a166b9c450c256d01fa619611cdbd1f297`
- 1936: `effeb31d0141e4f62d9332a4f909502a5d7467b2e8b718c4905049c3c0714410`

The regenerated local manifest references exactly four scenarios, 659/169/8
hierarchy overlays, 10,779 adjacency edges, PMTiles-only global polygons, and
M24–M28 (not M23+) as future reconstruction work.

### M23 neutral fabric

Fixed timestamp: `2026-07-13T00:00:00+00:00`.

- locations: 30,003, SHA-256
  `15629175e3426fccd14bdc92affd54629235fd3a65d7dcffdfce8652ec9c9c6b`
- adjacency rows: 52,142, SHA-256
  `78e12f204d07a26f3051003db8f00de418358b65681888e5f77383efba6f3180`
- admin intersections SHA-256
  `717c16482e924cc6ffe16f7158205f26dba6b67bca1defcea0c5423d9880ae45`
- lineage SHA-256
  `0f8480108bb34fe1709f47f8ac09d18b3746d866506075f7ee245aa48676db63`
- manifest SHA-256
  `f132d7db0afbad5727dbb9ddbd5bccc7a2a6693a512935e2a516b8d3f4b98355`
- strict fabric QA: pass, 0 errors, two aggregate warnings identifying exactly
  31 admin-0 and 40 admin-1 incomplete-reference locations
- `eu-like`, 1444-11-11 aggregation: 22,000 provinces from 30,003 locations

## Packaging and CLI evidence

`uv build` produced both sdist and wheel. A clean temporary environment installed
the wheel and successfully listed scenarios, era-geometry packs, multi-era
packs, and curator bundles, and generated a planned source manifest. The
installed data root contains all three official golden files, all configs and
schemas, viewer static assets, and the curator sample. CLI help/error paths are
covered by the complete suite; beta help now accurately lists the default 1936
scenario.

## Read-only public-surface evidence

- GitHub: `https://github.com/GeorgeQLe/global-province-map-template`, default
  branch `main`, remote head `929445252c5efb29de82f14454efb45778450a74`
  (`2026-07-13T15:22:10Z`). Root source, docs, landing, schemas, samples, and tests
  are visible. The accepted M23/remediation work remains local by instruction.
- Vercel project: `george-les-projects/landing`; production deployment
  `landing-2nvbf5nwb-george-les-projects.vercel.app`; production alias checked:
  `https://landing-six-iota-32.vercel.app`.
- `/` returned HTTP 200; `/demo` loaded in a real headless browser; all four
  scenario tabs reached their expected labels/quality tiers; period geometry is
  enabled only for 1444/1836/1936; culture, religion, and hierarchy paint toggles
  all worked; a MapLibre canvas rendered.
- PMTiles byte-range probe returned HTTP 206, `Content-Range: bytes
  0-126/15723223`, `Cache-Control: public, max-age=31536000, immutable`, and a
  valid PMTiles v3 header.
- The deployed manifest was generated `2026-07-13T15:08:10Z` and still has the
  old 660-area/10,781-edge counts and obsolete M23+ density slot. This is a
  deployment-lag warning, not silently accepted as current evidence.

## Remediations made

1. Deterministically clip/partition legacy Natural Earth admin conflicts, remove
   disputed positive-area overlaps, and assign mask gaps without changing the
   4,603-feature budget.
2. Ignore only sub-square-metre boolean-operation residue in outside-mask QA;
   meaningful outside coverage remains an error.
3. Make alpha/beta packaging fail closed when an available topology snapshot is
   malformed, failing, or nonzero-error.
4. Package `configs/scenarios/golden/*.json` in wheels and add a regression
   assertion for the data-files contract.
5. Replace obsolete numeric Chinese subdivision codes in `official-1936` with
   the current Natural Earth alpha codes and correct the complete Germany floor
   from 20 to 18.
6. Replace the obsolete demo M23+ density future slot with the M24–M28 certified
   reconstruction program and regenerate every M22 demo artifact locally.
7. Correct beta CLI help so it names all four default scenarios.

## Commands run

Representative commands (all outputs were under temporary directories unless
the command intentionally refreshed `landing/demo/data/`):

```text
uv run pytest -q
git diff --check
uv build --out-dir /tmp/gpm-audit-dist-fixed
uv run gpm build provinces --legacy-modern-admin ...
uv run gpm build adjacency ...
uv run gpm qa topology ...
uv run gpm qa scenario --scenario official-{1444,1836,1936} ...
uv run gpm release alpha ...
uv run gpm release beta ...
uv run gpm build hierarchy ...
uv run gpm demo build --no-tippecanoe ...
gpm build locations (Python API with fixed generated_at, twice)
gpm qa fabric ...
aggregate_location_provinces("eu-like", start_date="1444-11-11", target=22000)
vercel ls landing
vercel inspect <production deployment>
curl -I <production alias>/
curl -H "Range: bytes=0-126" <production alias>/demo/data/official-1444.pmtiles
```

## Remaining warnings and external actions

- The accepted local landing/demo build has not been deployed and the repository
  has not been pushed. Publishing either requires separate authorization.
- M15, M16, and M20 remain sample-scoped prototype infrastructure; no audit
  result upgrades them to production historical certification.
- M23 does not certify 1444, 1836, 1914, or 1936. That evidence work remains
  M24–M28.

## Ship manifest

- **User goal:** audit and remediate every completed M0–M23 milestone, retain
  prototype scope for M15/M16/M20, and prepare the accepted repository and
  generated landing assets for publication.
- **Changed files and purpose:** `README.md`, `ROADMAP.md`, `docs/*.md`, and
  `tasks/*.md` reconcile milestone contracts and evidence; `configs/fabrics/*`,
  profile/scenario configs, schemas, and fixtures define the M23 fabric and
  repaired 1936 contract; `src/gpm/builders/*`, `qa/*`, `release/*`, CLI,
  exporters, schemas, and viewer files implement neutral-fabric aggregation,
  topology normalization, fail-closed releases, hierarchy/demo integration,
  and review support; `tests/*` provide milestone regressions; `pyproject.toml`
  and `uv.lock` package the new runtime/schema dependencies and golden files;
  `landing/demo/data/*`, landing documentation, and sample accuracy labels are
  regenerated accepted public artifacts.
- **User-goal mapping:** the acceptance matrix maps every M0–M23 claim to its
  implementation, executable evidence, public evidence, and verdict; the
  remediation list maps each code/config change to a confirmed blocker.
- **Executable tests:** `uv run pytest -q` (238 passed), installed-wheel smoke,
  duplicate legacy/M22/M23 builds, strict topology/scenario/license/fabric QA,
  landing validation, PMTiles range reads, and real-browser scenario/paint QA.
- **Documentation-only checks:** milestone contradiction review and task-status
  reconciliation; these supplement rather than replace executable validation.
- **Skipped tests:** none relevant to the shipping boundary. Public writes were
  intentionally deferred until explicit authorization.
- **Adversarial review:** the comprehensive audit independently rebuilt all
  milestone-defining pipelines, compared duplicate outputs, installed the
  wheel in a clean environment, and probed the deployed public surface. This
  exposed and fixed topology, release-gating, packaging, 1936, and stale-demo
  issues.
- **Residual risk:** M15/M16/M20 remain prototype-only; M23 reference coverage
  retains the documented 31 admin-0/40 admin-1 warnings; historical
  certification remains M24–M28.
- **Rollback note:** revert the shipping commit and redeploy the preceding
  Vercel production deployment; no data migration or external database state
  is involved.
- **Next command:** implement the M24 contract in
  `docs/m24-start-date-research-framework.md`.
