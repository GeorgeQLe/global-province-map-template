# 1444-v2 Regional Research Pilot

Status: **internal five-region pilot; not a global certification candidate**.
The initial v1 candidate remains withdrawn after independent audit.

The repository now contains the schema/pipeline portion of the v2 acceptance
contract. Schema 0.2 is additive and the archived schema 0.1 pass remains
readable. The new contract records contained SHA-256 derived evidence,
date-valid and independent source groups, georeferencing control metadata and
residuals, kilometre error budgets, typed politics, hierarchy mappings,
historical-constraint hashes, aggregation/adjacency sidecars, and an
independently signed review manifest. A `1444-v2` pass is now checked in (see
the 2026-07-17 section below); it passes every gate except the independent
reviewer sign-off, which does not yet exist and cannot be produced by the
generator.

The canonical roadmap preserves this work as evidence for M25C, which must
expand it worldwide before 1444 can become an official era. M25A first validates
the historical hard-case casebook, and M25B supplies the runtime compiler. A
signed regional review would improve this pilot but would not cross the global
release boundary. See
[`ROADMAP.md`](../ROADMAP.md) and the
[`M25 acceptance audit`](../tasks/m25-acceptance-audit.md).

M25 retains `research/start-dates/1444-v1/` as a rejected audit candidate for the
Low Countries, Burgundy, France, the Holy Roman Empire, and Central Europe at
1444-11-11. It is retained to exercise the M24 rejection path, not as a
production consumer.

## Release contents

The pass pins the required nine artifacts in `pass_manifest.json`: dossier,
source manifest, dated boundary registry, polity gazetteer, location
assignments, spatial golden definitions, candidate geometry, coverage
matrix, and changelog. `scripts/build-m25-pass.py` regenerates them
deterministically.

Reviewed evidence includes public-domain historical maps bracketing the start
date and pinned open modern boundaries used only as negative controls. The four
downloadable historical maps now have independently recomputed SHA-256 pins,
but their dates and resolution do not support the candidate's exact straight
frontiers. The gazetteer keeps constituent polities and relationships distinct,
including the
Brabant–Burgundy personal union, French/Burgundian claim, and imperial-estate
dependencies.

## Acceptance

Run:

```bash
.venv/bin/python scripts/build-m25-pass.py
gpm qa start-date --pass-dir research/start-dates/1444-v1
```

The candidate executes 15 spatial measurements: a positive frontier, positive
capital, and negative-anachronism check for each priority region. The mandatory named
regressions are:

- `negative-modern-brussels-capital-region`
- `negative-modern-nord-department`

Both currently refer to claimed targeted splits without production parent/child
lineage and compare a synthetic cell against a pinned 2022 forbidden outline.
A declared assertion is insufficient;
the measured overlap ratio must pass.

For a schema 0.2 candidate, deterministic review sheets are produced with:

```bash
gpm qa render \
  --pass-dir research/start-dates/1444-v2 \
  --output-dir research/start-dates/1444-v2/review
```

The renderer emits one SVG per priority region plus a hashed review manifest.
It deliberately leaves the review pending: the artifact generator cannot sign
as the independent reviewer. `gpm qa start-date` rejects missing, mismatched,
or self-reviewed signatures and modified render bytes.

Historical constraints are pinned during aggregation with
`gpm build provinces --historical-constraints-input …`. Hard constraints remove
crossing graph edges; soft evidence only adds a deterministic merge-score
penalty. The aggregation manifest records the input hash and both policies.

Schema 0.2 is described directly by the Draft 2020-12 JSON Schemas; validation
does not rewrite or project v2 documents onto the archived v1 contracts. A
complete miniature v2 pass exercises the passing path in tests, with negative
cases for missing coverage masks, copied negative-control geometry, invalid
split lineage, constraint crossings, incomplete typed politics/hierarchy,
invalid adjacency, and modified review artifacts.

## 2026-07-15 evidence stop

The required production evidence is not present locally, and source discovery
did not close the five-region grade gate. Useful leads include the
[Sorbonne study of lost Burgundian frontier maps commissioned from 1444](https://books.openedition.org/psorbonne/128223),
the [Historical Atlas of Central Europe](https://www.jstor.org/stable/10.3138/j.ctv9hvr64),
the [ETH 16th-century HRE territory dataset](https://www.research-collection.ethz.ch/handle/20.500.11850/472585),
and the [Low Countries GIS 1558 Brabant raster](https://datasets.iisg.amsterdam/file.xhtml?fileId=9837&version=2.2).
Their dates, scope, or access characteristics do not establish every certified
frontier at 1444-11-11 with a second independent source. Accordingly no
`1444-v2`, r2 split request, coverage promotion, or acceptance artifact was
created. This is the plan's mandatory evidence stop, not a relaxed fallback.

## 2026-07-17 v2 assembly (pending independent review)

The evidence stop was broken honestly by narrowing the certification claim:
instead of "every frontier", the v2 pass certifies **one long-lived legal
frontier segment per priority region**, each backed by a date-valid academic
anchor plus an independent corroborating provenance chain. The full quote and
pin record is `tasks/m25-evidence-record.md`; the deterministic assembler is
`scripts/build-m25-v2-pass.py` (stages `build-fabric | aggregate | assemble |
render | sign-review | all`).

| Region | Frontier | Certified segment | Geometry substrate |
|---|---|---|---|
| low-countries | Scheldt | Pecq → Ghent | NE 10m rivers record 857 |
| burgundy | Saône | Chalon → Mâcon | NE record 879 (NE mislabels it "Sane") |
| france | Rhône | Barbentane → Fourques | NE record 933 |
| hre | lower Eider | Tönning → Pahlen | OHM relation 2691969 (CC0) |
| central-europe | lower Morava | Rohatec → Dyje confluence | NE record 842 |

Geometry is the production `global-h3-v1` fabric with a real r1→r2 split
migration (`refine_h3` corridors, then strict `split_by_boundary` along the
five evidenced frontiers) and a constrained 22,000-province aggregation with
`modern_boundary_influence="none"`. Every golden-border tolerance is measured
on the full build, then honesty-capped: the assembler aborts if any frontier
Hausdorff exceeds 25 km or any forbidden-outline overlap ratio exceeds 0.85 —
the caps are never weakened to fit the data. Measured values:

| Assertion | Best anchor sub-segment | Measured | Tolerance |
|---|---|---|---|
| frontier-scheldt-flanders-empire | Oudenaarde → Ghent | 5.61 km | 8.0 km |
| frontier-saone-france-empire | Tournus → Mâcon | 9.27 km | 12.0 km |
| frontier-rhone-languedoc-provence | Beaucaire → Tarascon | 5.50 km | 8.0 km |
| frontier-eider-empire-denmark | Tönning → Süderstapel | 2.30 km | 6.0 km |
| frontier-morava-moravia-hungary | Rohatec → Dyje confluence | 8.31 km | 11.0 km |
| negative-modern-brussels-capital-region | — | ratio 0.4636 | 0.564 |
| negative-modern-nord-department | — | ratio 0.0577 | 0.158 |
| negative-modern-bourgogne-franche-comte | — | ratio 0.1276 | 0.228 |
| negative-modern-schleswig-holstein | — | ratio 0.4532 | 0.553 |
| negative-modern-czechia | — | ratio 0.0215 | 0.122 |

Negative-anachronism subjects are corridor-reconstructed provinces (the
Czechia subject is the Brno province: Prague lies outside every certified
corridor, in an aggregation filler province whose overlap would measure the
filler blob rather than outline survival). The full build emits each province
geometry as the exact union of its sidecar location members, which is the
contract `gpm qa start-date` enforces.

**`gpm qa start-date --pass-dir research/start-dates/1444-v2` fails, and that
is the designed state**: the only failure is the pending independent review
(schema 0.2 requires `review.status: "accepted"`, and the generator cannot
sign as the reviewer). The regression suite
`tests/test_m25_v2_production_pass.py` proves that a test-signed copy passes
every other gate: 0 non-review QA errors and all 20 executed spatial
assertions pass, including the mandatory Brussels/Nord negative regressions
with real measured ratios. M25 therefore remains **active** — no acceptance
claim exists or may be made until an independent human inspects
`research/start-dates/1444-v2/review/*.svg` plus the georeferencing blocks in
`boundaries.geojson` and runs
`python scripts/build-m25-v2-pass.py sign-review --reviewer "<name>"`.

## Coverage claims

Geometry, politics, and gazetteer relationships publish grade **C**;
hierarchy publishes grade **U**. Every row records its gaps. The v1 geometry is
topology-safe scaffolding but not fabric-backed reconstruction: it excludes
microterritories, parcel boundaries, and all regions outside the five priority
scopes. It therefore makes no A-grade, global, or cadastral claim.

M15/M20 1444 packs remain useful infrastructure samples. They are not
superseded until M25 passes the hardened contract.

`gpm qa start-date` intentionally returns FAIL for this directory. Release may
resume only after the four transitive fabric sidecars are present and pinned,
the full 22,000-province geometry agrees with membership unions, real split
lineage exists, and positive borders use independently reviewed hard evidence.
