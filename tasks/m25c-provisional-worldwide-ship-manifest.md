# M25C Provisional Worldwide Pass Ship Manifest

## User goal

Create a deterministic, non-public worldwide M25C pass from accepted M23/M49,
pilot, anomaly-census, and `official-1444` scenario inputs; make regional
evidence replaceable without weakening certification; and prove provisional
output cannot be accepted, certified, published, or demo-promoted.

## Changed files

- `artifacts/m25c-anomaly-alignment-response.yaml`
- `artifacts/m25c-anomaly-alignment-slides.html`
- `research/start-dates/1444-global-v1/anomaly_inventory.json`
- `research/start-dates/1444-global-v1/candidate_status.json`
- `research/start-dates/1444-global-v1/m25c_rejection_report.json`
- `research/start-dates/1444-global-v1/regional-packets/README.md`
- `research/start-dates/1444-global-v1/sidecars/location_adjacency.csv`
- `research/start-dates/1444-global-v1/sidecars/location_fabric_manifest.json`
- `research/start-dates/1444-global-v1/sidecars/location_lineage.json`
- `research/start-dates/1444-global-v1/sidecars/locations.geojson`
- `research/start-dates/1444-global-v1/sidecars/province_membership.csv`
- `research/start-dates/1444-global-v1/world_coverage_mask.geojson`
- `schemas/start-date-pass-manifest.schema.json`
- `scripts/build-m25c-global-pass.py`
- `scripts/generate-m25c-provisional-pass.py`
- `src/gpm/qa/certification.py`
- `src/gpm/qa/start_date.py`
- `tasks/history.md`
- `tasks/m25c-provisional-worldwide-ship-manifest.md`
- `tasks/roadmap.md`
- `tasks/todo.md`
- `tests/test_m25c_global_certification.py`

## Per-file purpose

- The two alignment artifacts preserve the reviewed engine-neutral anomaly
  decisions and compiled response that feed the locked treatment boundary.
- `anomaly_inventory.json`, `candidate_status.json`, and the rejection report
  replace the placeholder census state with the accepted resolved inventory
  while preserving the non-public handoff status and remaining evidence gaps.
- The regional-packet README records packet ordering and Grade-A policy.
- The five M23 sidecars and M49 mask pin the accepted r2 location geometry,
  lineage, adjacency, membership, and exact 23,582-location playable scope used
  by the generator.
- The pass-manifest schema admits the explicit provisional QA mode.
- The existing global builder recognizes the versioned census ledger and
  rejects provisional manifests at `accept-review`.
- The new provisional generator performs deterministic membership re-splitting,
  spatial scenario transfer, artifact assembly, pilot/anomaly retention,
  canonical status projection, coverage creation, and regional packet merging.
- Certification rejects provisional passes both when creating a certificate
  and when validating a supplied bundle, closing publication/demo forgery paths.
- Start-date QA limits provisional downgrades to evidence/review incompleteness
  and compacts repeated warnings without changing structural failures.
- The M25C tests cover deterministic grouping, ledger versions, weak Grade-A
  packet rejection, review/certification rejection, and forged bundle lineage.
- Todo, roadmap, history, and this manifest record the completed provisional
  boundary, remaining regional research, verification, risk, and rollback.

## User-goal mapping

The shipped generator constructs all required worldwide artifacts from pinned
inputs and marks every provisional claim honestly. The manifest mode and four
separate promotion gates keep that internal output off public paths. Regional
packets replace evidence deterministically and cannot claim Grade A unless the
four-layer, source, corroboration, completeness, and visual-review contract is
satisfied. Ordinary certification-grade research requirements remain unchanged.

## Tests run

- Executable complete suite: `uv run --extra dev pytest -q` — 361 passed in
  22.03 seconds, with no test warnings or failures.
- Executable provisional build/QA: generated a 288 MB pass with 23,582
  exact-once locations, 22,000 provinces, 22 regions, and 88 B/C rows;
  internal QA passed with zero errors and 12 expected provisional warnings.
- Executable render/QA: rendered 30 currently applicable region/anomaly sheets;
  post-render internal QA passed with zero errors and 10 expected warnings.
- Reproducibility: two independent clean output trees were byte-identical;
  both pass manifests hashed to
  `eae4e26ec0bf464c78d336313b2bb4312bb82ec785efd12924b42e91f98024a0`.
- Source hygiene: `git diff --check` passed.

## Skipped tests

- Ordinary certification QA, runtime compilation, runtime benchmarks, and demo
  publication were intentionally not run: the provisional manifest must reject
  those paths until all 88 rows are gap-free Grade A and a human accepts the
  final review bundle. Unit tests exercise those rejection boundaries.
- Eleven anomaly-class sheets are a final-acceptance requirement. The current
  accepted inventory contains eight represented anomaly classes, so provisional
  rendering correctly produced 22 regional plus eight applicable anomaly
  sheets; no absent class was fabricated.
- No separate lint/typecheck/build command is declared for this Python project;
  compilation checks, executable generation, QA, rendering, and the complete
  test suite cover the changed paths.
- No deployment was run because the repository has no `deploy.md` or
  `tasks/deploy.md` manual deploy contract.

## Adversarial review

An explicit equivalent adversarial sweep inspected the exact shipping diff and
tested schema-valid provisional manifests, exact-once resplitting, weak regional
Grade-A claims, accept-review rejection, direct certification rejection, forged
certification-bundle lineage, and uncertified demo behavior. Full internal QA
then exercised checksum, path containment, source/gazetteer closure, accepted
census linkage, canonical/build parity, topology, exact count, and all retained
pilot spatial assertions. Structural failures remained errors; only the named
coverage, planned-source, missing-final-assertion, and pending-review findings
became compact warnings. No unresolved ordinary QA or test failure remains.

## Residual risk

- Worldwide politics outside the accepted pilot remain a modern-scaffold seed,
  not historical evidence. All 22 regions still require exact-date promotion.
- No real regional packet has yet exercised the positive Grade-A merge path;
  the generator rejects incomplete claims, while the first real packet may
  expose integration or performance issues that remain fail-closed.
- The tracked geometry inputs add roughly 147 MB to repository history, with a
  largest file of roughly 87 MB. This is below GitHub's per-file hard limit but
  increases clone size materially.
- Human pass acceptance, certification runtime compilation, performance gates,
  and public release remain explicitly outstanding.

## Rollback note

Revert the M25C provisional-worldwide shipping commit. This removes the
generator, tracked inputs, provisional QA mode, promotion guards, tests, and
task records. No database, hosted artifact, deployment, accepted certification,
or irreversible migration is involved.

## Next command

`$exec`
