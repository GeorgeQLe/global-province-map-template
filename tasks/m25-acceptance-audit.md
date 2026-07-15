# M25 Independent Acceptance Audit

Date: 2026-07-14 (America/New_York)

## Verdict

**FAIL. M25 is active; `official-1444-reconstruction-v1` is withdrawn and is
not independently releasable.** The prior PASS measured a self-consistent
15-province drawing, not a historical reconstruction embedded in the canonical
30,003-location/22,000-province M23 build. Its boundary coordinates were copied
into both generator output and golden constraints, so five zero-distance
frontier results were circular evidence.

The audit preserved the nine top-level roles, hardened the M24/M25 contract,
downgraded coverage from B/C to C/U, pinned all nine retrieved source responses,
and regenerated the candidate as an intentional 14-error FAIL. The production
M23 pipeline was independently rebuilt twice, but production fabric availability
does not supply the missing historical research or accepted split lineage.

## Acceptance matrix

| Gate | Evidence | Verdict |
|---|---|---|
| Nine top-level artifact roles and hashes | All nine exist and match `pass_manifest.json` | pass |
| Source retrieval/provenance | Nine URLs retrieved; versions, authors/licenses, dates, and SHA-256 recorded below | pass for retrieval only |
| Per-boundary historical traceability | No control points, georeferencing record, digitized source layer, or vertex-to-source record | fail |
| M23 location existence | Candidate uses 15 synthetic `loc-*` names absent from the production fabric | fail |
| Targeted split lineage | Brussels/Nord are labeled accepted but have no production parent/child event | fail |
| Province identity | Candidate uses hand-written `province-*` IDs, not membership-derived `prv_*` IDs | fail |
| Full `eu-like` build | Candidate has 15 provinces, not 22,000 | fail |
| Geometry from membership unions | No pinned membership/location sidecars exist in the candidate | fail |
| Spatial validity/topology | Candidate geometries are individually valid, unique, and have no positive-area interior overlap | pass, but fixture-only |
| Historical frontier tests | Five 0.0 Hausdorff results reuse generator constants and soft, wrong-date evidence | fail |
| Brussels/Nord regressions | Ratios recompute to 0.0986515672 and 0.0222609260; zero-tolerance mutations fail | pass as regression only |
| Coverage grades | Geometry/politics/relationships C; hierarchy U; no A/B remains | pass after downgrade |
| Deterministic M23/M25 generation | Two current M23 fabric and neutral aggregation builds are byte-identical; candidate regeneration is deterministic | pass |
| Visual review renders | No pass-contained five-region review renders or modern-overlay renders exist | fail |
| Release/status claims | README, roadmap, todo, history, and M25 contract now identify the candidate as withdrawn | pass |

## Baseline evidence

The dirty worktree was preserved. Before remediation the focused suite reported
34 passes and one sandbox-only localhost bind failure. With localhost access the
same M23 server test is expected to run; the failure was `EPERM` binding
`127.0.0.1:0`, not an assertion failure.

Initial artifact SHA-256 values:

| Artifact | Baseline SHA-256 |
|---|---|
| `assignments.json` | `6996ab320089436696ad2ddabb63b82dceab16c52101acc1af7f368fbb87c2a5` |
| `boundaries.geojson` | `95ec8dfc0a128fbd7f0e7d6bbcd01f8e3fb1b356e98e4e9e914c9c632a36fd1a` |
| `build.geojson` | `e640a6346acc1338afc3078f412635bf140f123565ddb9d922f70d83dbecdb8c` |
| `changelog.json` | `872ad4d353b1273fb24639304c86a5d059e168ce0a3140714f0da0417b83f192` |
| `coverage.json` | `56393cbd253b0547b72a737b5d18387a439d3aefd9ea1f445f775505992cc56e` |
| `dossier.md` | `e62f872dd8bb3dca4af572a1abea48a4dde33fef9a02ad4c120e781a0e4a5843` |
| `gazetteer.json` | `562edac6db70779e0a71031d4a3e8414ab0c2ab9cda138a7e3452976d1132d28` |
| `golden.json` | `4728e47c1773371230fb37b820e5dc0ac6bf413ee751e35e333b318b8430da9c` |
| `pass_manifest.json` | `ebbdb71fcbf742f7b4dcc8c13ffe117cea5add5b5ada46f271da7fdac6efd292` |
| `source_manifest.json` | `5ae31d0cb7fe2466c5d5cad5ee729ddf843cf6009eca593ff19c2065a504b05d` |
| `start_date_qa.json` | `f5eead8ad669211f59c7c303dfa122a7c4ddb78c25da015b21534361fa4ddd05` |

Regenerated audit-candidate SHA-256 values:

| Artifact | Audited SHA-256 |
|---|---|
| `assignments.json` | `080d48f8dd90fa3c89310950d78c7c51bc1ef5a245f226309d7ffc198dbfce46` |
| `boundaries.geojson` | `af79c31ce1701897033b834b76bdb2cd38c64a32fb531b160c359efede08aca6` |
| `build.geojson` | `e640a6346acc1338afc3078f412635bf140f123565ddb9d922f70d83dbecdb8c` |
| `coverage.json` | `d013f0956d573b4dfbd8fc321f9047c1d95797e0b241a8e90d9693aacf103ed4` |
| `dossier.md` | `ab9188bf9b44a3f00a34a038694e994d1d328e2282b8002ee6a0f7bb07c97461` |
| `pass_manifest.json` | `094b3bc41d3ba1a9214d3e4d697c8780f3c830006275ddb7b68670d5a0d37ad8` |
| `source_manifest.json` | `ba62d39ea54e2261b70b5744ae54487aa7be6b50fb0e5c793e66b6f90f143b33` |
| `start_date_qa.json` | `5da36ab64ed081d5213a8dcebdb85ab8723d2c921eba6dc718a74dafcfb23d76` |

The unchanged changelog, gazetteer, golden definitions, and candidate geometry
retain their baseline hashes; their presence does not imply acceptance.

## Source evidence record

All cited URLs were independently downloaded on the audit date. Historical
maps are geographically relevant at atlas scale, but only bracket 1444; none is
a day-exact surveyed boundary source. The three `api/current` hashes pin the
retrieved metadata response and may change when geoBoundaries changes “current.”

| Source | Authorship/date/license and relevance | Retrieved SHA-256 | Audit finding |
|---|---|---|---|
| [France 1453](https://commons.wikimedia.org/wiki/File:France_1453_shepherd.jpg) | William R. Shepherd; map represents 1453; 1923 atlas scan; public domain; relevant to France/Burgundy/Calais | `123742af7f7e8390d16ca01817e14b5cfc1e066233ea8be31ce2ccf72146008e` | Nine years late; cannot establish exact 1444 coordinates |
| [HRE c.1400](https://commons.wikimedia.org/wiki/File:Heiliges_R%C3%B6misches_Reich_1400.png) | Gustav Droysen; 1886 atlas; represents c.1400; public domain; relevant to HRE/Central Europe | `44bc2f48fc19a8ee00bb3b534387feeafdaca9597648948923b1ff4cf96d6cd4` | About 44 years early and generalized |
| [Europe 1430](https://commons.wikimedia.org/wiki/File:Europe_in_1430.PNG) | Lynn H. Nelson; represents 1430; public-domain dedication; Europe-wide 600×650 raster | `e75c37a522cfad805b66728f8e45b8a828d9ff6e0d137072d809456df6794d61` | Corroborative overview only |
| [Burgundian Netherlands 1477](https://commons.wikimedia.org/wiki/File:Map_Burgundian_Netherlands_1477-fr.svg) | Denis Jacquerye; represents 1477 with acquisition legend; CC BY-SA 2.5; relevant to Low Countries | `55be2e03be689ad12d964486e118466fb58d675866a4672f03c2fee7386d88d9` | Legend supports acquisition years, not unchanged 1444 borders or the asserted personal-union type |
| BEL ADM1 commit `9469f09` | geoBoundaries 2022 / Eurostat; CC BY 4.0; modern negative control | `7af87f5035779f0aefe5bf930288572979e490ab0441fd9b92942a519bea0974` | Existing pin reproduced |
| FRA ADM2 commit `9469f09` | geoBoundaries 2022 / IGN; Etalab Open License 2.0; Nord negative control | `a14ed131c86c802e5d546c7cbeccbd4daebc94a66fea413f563935a53504f251` | Existing pin reproduced |
| FRA ADM1 current metadata | geoBoundaries current API; modern negative control | `26b876de5b03c99399ccec16a367deb8681c4953eecede32ac6f5d4fb581bf09` | API response pinned; candidate uses only an undocumented envelope |
| DEU ADM1 current metadata | geoBoundaries current API; modern negative control | `65af06f80e837028997c396d2c67d74fb1e1752d884e9a0638d5c736ee8c345a` | API response pinned; candidate uses only an undocumented envelope |
| CZE ADM0 current metadata | geoBoundaries current API; modern negative control | `26452c32c6013dabb946428b8b97e43c52982b7eb7112075237fc415262a3e28` | API response pinned; candidate uses only an undocumented envelope |

The atlas files can support review questions about Brabant, Liège, Burgundy,
Calais, Cologne, the Palatinate, Bohemia, and Habsburg lands. They do not by
themselves verify every capital, dependency, claim, or territorial relationship
in the gazetteer. Those records remain C-grade scaffolding pending polity-level
sources. The five historical frontier features now carry their represented map
dates and `soft_evidence`; `gpm qa start-date` rejects their positive gates.

## Independent M23 reconstruction

Two clean builds used fixed `generated_at=2026-07-13T00:00:00+00:00`, the
repository Natural Earth inputs, `global-h3-v1`, and `eu-like` at 1444-11-11.
Both current runs produced 30,003 locations, 52,142 adjacency rows, and 22,000
provinces. Fabric QA passed with zero errors and the documented two warnings:
31 admin-0 and 40 admin-1 incomplete-reference locations.

Byte-identical fabric hashes across both runs:

- locations: `3acfbe76f6d5f8154104d5c3d721e98346b95238747dfeece3e7702cfbff2afb`
- adjacency: `78e12f204d07a26f3051003db8f00de418358b65681888e5f77383efba6f3180`
- admin intersections: `717c16482e924cc6ffe16f7158205f26dba6b67bca1defcea0c5423d9880ae45`
- lineage: `0f8480108bb34fe1709f47f8ac09d18b3746d866506075f7ee245aa48676db63`
- fabric manifest: `af807ad7cf4e8ef438ef3e9309bc0d144bed8a9a478ba75aa154ce97e46c24c3`

Byte-identical aggregation hashes across both runs:

- provinces: `f1dbc9dfd1b2b096a453bbed147a02802c71cec676a0df9f9e8183d808b6c83d`
- province membership: `b25e3ca1a94bfb0e08ddc695d70c229bf0884e76b4fc95bd90fcec10c6e0a6db`
- aggregation manifest: `d560c149d95cb2b3e34b55b5a10faddb27169f6a865dba74f5bf441c56ea6d5d`

The prior M0–M23 audit’s adjacency, intersections, and lineage hashes reproduce;
its recorded locations and manifest hashes do not reproduce with the current
tree. The two current runs agree with each other, so this is historical-build
drift to resolve before using the old hashes as release evidence.

## Contract remediation

The assignments schema now requires `aggregation_profile`,
`geometry_revision`, `expected_province_count`, and four SHA-256 sidecars:
fabric manifest, atomic locations, lineage, and province membership. QA checks
containment, symlinks, checksums, fabric revision, location validity/existence,
accepted-split child lineage, duplicate memberships, ordered membership-derived
province IDs, exact membership unions, declared build count, and province
interior overlaps. Positive border assertions fail when their boundary is only
soft evidence.

Adversarial tests cover missing/substituted sidecars, unknown locations,
accepted splits without lineage, non-derived IDs, membership/geometry mismatch,
incomplete builds, overlapping interiors, soft-evidence promotion, and material
Brussels/Nord tolerance changes.

## Spatial measurements and renders

The candidate still computes five capital containments at 1.0. Its five frontier
Hausdorff measurements are 0.0 because generator constants create both sides of
the comparison; they are not independent evidence. Modern overlap ratios are:

- Brussels-Capital Region: `0.09865156718879299` at tolerance `0.12`
- Nord department: `0.022260925989308848` at tolerance `0.25`
- Burgundy envelope: `0.0009469696969697074`
- North Rhine-Westphalia envelope: `0.0006879606879606904`
- Czechia envelope: `0.0018952062430323585`

No pass-contained renders exist for the five regions, capitals, relationships,
split lineage, or modern overlays. Visual acceptance is therefore not claimed.

## Commands and remaining work

Final automated results after the schema 0.2 gap closure: focused M23–M25 suite
**50 passed**; complete repository suite **277 passed**; duplicate M25 candidate
generation had no byte differences;
fabric QA passed with 0 errors/2 documented warnings. The M25 start-date gate
correctly reports FAIL with 14 errors and no warnings. The sdist and wheel built
successfully, the wheel contains the hardened schemas/QA module, and a clean
temporary installation reproduced the same 14-error FAIL against a copied pass.

Representative executed commands:

```text
sha256sum research/start-dates/1444-v1/*
uv run pytest -q tests/test_m23_locations.py tests/test_m24_start_date_framework.py tests/test_m25_1444_reconstruction.py tests/test_m25_v2_contract.py
uv run python -c 'build_location_fabric(... fixed generated_at ...)'  # twice
uv run python -c 'aggregate_location_provinces(... target=22000 ...)' # twice
uv run gpm qa fabric ...
uv run python scripts/build-m25-pass.py
uv run gpm qa start-date --pass-dir research/start-dates/1444-v1
uv run pytest -q
git diff --check
uv build
```

Release-blocking remaining work is substantive research, not a tolerance tweak:
create per-boundary georeferencing/traceability, obtain polity-level sources,
apply evidence-backed assignments to real fabric IDs inside the complete build,
process any Brussels/Nord split through an actual revised M23 lineage, include
the four pinned sidecars, produce review renders, and rerun the full acceptance
suite. Until then M15/M20 are not superseded and M25 remains active.

The 2026-07-15 roadmap review leaves this FAIL verdict unchanged. Its planned
M25.5 runtime compiler depends on an accepted M25 canonical pass; runtime design
or packaging cannot substitute for the missing historical evidence, real
lineage, full build, QA, or visual review described above. See `ROADMAP.md`.
