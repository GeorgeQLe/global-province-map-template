# M25 — 1444 Research and Reconstruction Pass

Status: **active; initial v1 candidate withdrawn after independent audit**.

The repository now contains the schema/pipeline portion of the v2 acceptance
contract. Schema 0.2 is additive and the archived schema 0.1 pass remains
readable. The new contract records contained SHA-256 derived evidence,
date-valid and independent source groups, georeferencing control metadata and
residuals, kilometre error budgets, typed politics, hierarchy mappings,
historical-constraint hashes, aggregation/adjacency sidecars, and an
independently signed review manifest. No `1444-v2` pass is checked in because
the required B-grade historical evidence and independent reviewer sign-off do
not yet exist; generating plausible-looking geometry would not satisfy this
contract.

The canonical roadmap keeps M25 focused on restoring fabric-backed B
geometry/politics/relationship and C hierarchy coverage across all five
priority regions. Planned M25.5 compiles an accepted M25 pass for game runtime;
it does not relax or replace this milestone's research gate. See
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
