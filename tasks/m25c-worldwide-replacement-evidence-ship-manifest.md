# M25C worldwide replacement-evidence ship manifest

Date: 2026-08-24

## User goal

Obtain independently approvable replacement evidence for all 56 frozen
ordinary-QA blockers before Task 17, without implementing or self-approving the
evidence.

## Changed files

- `README.md`
- `tasks/history.md`
- `tasks/roadmap.md`
- `tasks/todo.md`
- `tasks/m25c-worldwide-replacement-evidence.md`
- `tasks/m25c-worldwide-replacement-evidence-ship-manifest.md`
- `scripts/generate-m25c-replacement-evidence.py`
- `tests/test_m25c_replacement_evidence.py`
- `research/start-dates/1444-global-v1/replacement-evidence/cliopatria-v0.2.0/README.md`
- `research/start-dates/1444-global-v1/replacement-evidence/cliopatria-v0.2.0/manifest.json`
- `research/start-dates/1444-global-v1/replacement-evidence/cliopatria-v0.2.0/cliopatria-1444.geojson`
- `research/start-dates/1444-global-v1/replacement-evidence/cliopatria-v0.2.0/direct-border-candidates.geojson`
- `research/start-dates/1444-global-v1/replacement-evidence/cliopatria-v0.2.0/applicability-review-candidates.json`
- `research/start-dates/1444-global-v1/replacement-evidence/cliopatria-v0.2.0/regions/005.json`
- `research/start-dates/1444-global-v1/replacement-evidence/cliopatria-v0.2.0/regions/011.json`
- `research/start-dates/1444-global-v1/replacement-evidence/cliopatria-v0.2.0/regions/013.json`
- `research/start-dates/1444-global-v1/replacement-evidence/cliopatria-v0.2.0/regions/014.json`
- `research/start-dates/1444-global-v1/replacement-evidence/cliopatria-v0.2.0/regions/015.json`
- `research/start-dates/1444-global-v1/replacement-evidence/cliopatria-v0.2.0/regions/017.json`
- `research/start-dates/1444-global-v1/replacement-evidence/cliopatria-v0.2.0/regions/018.json`
- `research/start-dates/1444-global-v1/replacement-evidence/cliopatria-v0.2.0/regions/021.json`
- `research/start-dates/1444-global-v1/replacement-evidence/cliopatria-v0.2.0/regions/029.json`
- `research/start-dates/1444-global-v1/replacement-evidence/cliopatria-v0.2.0/regions/030.json`
- `research/start-dates/1444-global-v1/replacement-evidence/cliopatria-v0.2.0/regions/034.json`
- `research/start-dates/1444-global-v1/replacement-evidence/cliopatria-v0.2.0/regions/035.json`
- `research/start-dates/1444-global-v1/replacement-evidence/cliopatria-v0.2.0/regions/039.json`
- `research/start-dates/1444-global-v1/replacement-evidence/cliopatria-v0.2.0/regions/053.json`
- `research/start-dates/1444-global-v1/replacement-evidence/cliopatria-v0.2.0/regions/054.json`
- `research/start-dates/1444-global-v1/replacement-evidence/cliopatria-v0.2.0/regions/061.json`
- `research/start-dates/1444-global-v1/replacement-evidence/cliopatria-v0.2.0/regions/143.json`
- `research/start-dates/1444-global-v1/replacement-evidence/cliopatria-v0.2.0/regions/145.json`

## Per-file purpose

- The four existing project/task ledgers record that evidence is available but
  unsigned, the candidate is unchanged, and Task 17 remains closed.
- The two new task documents define the approval boundary, evidence inventory,
  limitations, validation, residual risk, and reviewer handoff.
- The generator pins Cliopatria `v0.2.0`, refuses checksum drift, derives all
  review surfaces deterministically, and hashes generated and frozen inputs.
- The regression test proves exact 56-finding accounting, recomputes each direct
  line from its two cited source polygons, validates unsigned applicability
  records, and verifies every generated and frozen-input hash.
- The evidence README and manifest carry attribution, provenance, reproduction,
  source uncertainty, accounting, and immutable hashes.
- The source slice preserves all 144 date-valid records unchanged; the direct
  border file contains eight candidate-independent shared-boundary candidates;
  and the applicability file contains ten exhaustive, unsigned audits.
- The 18 regional dossiers bind every frozen error exactly once to the affected
  components and their independent source classifications.

## User-goal mapping

| Goal requirement | Evidence in this diff |
| --- | --- |
| All remaining blockers | Manifest and dossiers account for all 56 frozen errors exactly once across all 18 affected regions. |
| Replacement evidence | Pinned peer-reviewed 1444 source slice, eight direct borders, ten applicability audits, and 18 corridor dossiers. |
| Independently approvable | Each record is hash-bound, unsigned, provenance-bearing, and separated from implementation; gaps and overlaps fail closed. |
| Before Task 17 | No candidate artifact or permission changed; Task 17 remains unchecked and the frozen preflight still fails at 56 errors. |

## Tests run

- `.venv/bin/python -m py_compile scripts/generate-m25c-replacement-evidence.py`
- `.venv/bin/pytest -q tests/test_m25c_replacement_evidence.py tests/test_m25c_modern_seam_controls.py tests/test_m25c_global_certification.py` — `65 passed in 43.00s`.
- Two clean generations from the pinned GeoJSON produced byte-identical trees;
  each tree's ordered file-hash digest was
  `7c7be1ab0370e2eb6d01e4ed38c2bee2d9eb5c398a5e432693ba3a5dcd3c2678`.
- Every checked-in generated artifact exactly matched a third clean generation;
  the evidence README is the sole authored companion file.
- A deliberately wrong input (`README.md`) was rejected at the pinned source
  checksum boundary before generation.
- `scripts/build-m25c-global-pass.py preflight` exited `1` as expected with the
  frozen `56` errors and one warning; the report remained byte-identical at
  SHA-256 `659d36cb28745782718ca5fab23830817eb48ad31d3016c1fa081e01ef3c52c6`.
- `git diff --check` passed.

## Skipped tests

- The full repository suite was not rerun because the changed executable scope
  is the evidence generator and its M25C contracts; the focused 65-test set
  covers that generator, seam controls, schemas, certification gates, and the
  unchanged fail-closed baseline. No lint, typecheck, or build command is
  configured in `pyproject.toml`.
- Deployment was not run because the repository has no `deploy.md` or
  `tasks/deploy.md` deployment contract, and this research packet changes no
  deployable artifact.

## Adversarial review

The quality sweep tried source drift, nondeterministic regeneration, hash drift
in every frozen and generated input, substituted border geometry, incomplete
finding accounting, accidental signatures, and accidental Task 17 advancement.
It found two test-coverage gaps: frozen-input hashes were recorded but not
asserted, and border lines were validated without exact source recomputation.
Both checks were added and pass. No correctness, safety, security, or contract
defect remains known in the shipped scope.

## Residual risk

Cliopatria publishes approximate native resolution and unquantified historical
border uncertainty. The proposed `20 km` budget, every direct border, every
applicability disposition, and every covered component therefore still require
independent acceptance. Source silence and overlapping-polity rows cannot
authorize edits; supplemental evidence may be required. Approval alone will
not clear QA: later serial implementation and renewed worldwide validation are
mandatory.

## Rollback note

Revert the shipping commit to remove the generator, tests, task updates, and
entire replacement-evidence directory. No data migration or candidate rollback
is needed because this work changes only research and validation surfaces.

## Next command

Perform independent record-by-record review of
`tasks/m25c-worldwide-replacement-evidence.md`; record explicit accept, reject,
or supplemental-evidence decisions before invoking any implementation work.
