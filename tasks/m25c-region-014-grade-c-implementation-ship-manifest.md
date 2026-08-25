# M25C region 014 Grade C implementation ship manifest

Date: `2026-08-24`
Status: **three accepted routes implemented; candidate remains blocked**

## User goal

Serially implement only region `014`'s three independently accepted Grade C
routes, preserve every reviewed hash and explicit gap, regenerate the affected
candidate evidence without opening any release permission, and ship the result
cleanly on `main`.

## Changed files and per-file purpose

- `scripts/generate-m25c-provisional-pass.py` — verifies the accepted review
  bundle and routes, applies the exact `014/geometry` downgrade, and records the
  three ordered changes only during assembled generation.
- `src/gpm/qa/m25c_assembled.py` — defines the six accepted gaps and rejects
  any assembled coverage exception outside the exact region `014` Grade C row
  and serial changelog suffix.
- `tests/test_m25c_global_certification.py` — exercises review-hash drift,
  exact gap preservation, and ordered route recording.
- `tests/test_m25c_assembled_transition.py` — updates the valid assembled
  fixture and verifies unreviewed coverage drift remains rejected.
- `tests/test_m25c_replacement_evidence.py` — resolves a manifest-pinned frozen
  input from its immutable archive before consulting the regenerated live tree.
- `research/start-dates/1444-global-v1/replacement-evidence/cliopatria-v0.2.0/frozen-inputs/start_date_preflight.json`
  — preserves the exact pre-implementation QA input accepted by the review.
- `research/start-dates/1444-global-v1/replacement-evidence/cliopatria-v0.2.0/README.md`
  — documents that frozen-input boundary.
- `research/start-dates/1444-global-v1/replacement-evidence/best-reasonable-v1/README.md`
  — records region `014` implementation and the eight remaining accepted
  routes.
- `README.md` — reports the current fail-closed candidate result.
- `tasks/m25c-best-reasonable-independent-review.md` — preserves the review
  decision while recording its partial serial implementation.
- `tasks/m25c-best-reasonable-supplemental-evidence.md` — updates the evidence
  packet's implementation status.
- `tasks/todo.md` — records the completed region `014` sub-boundary and leaves
  Task 17 blocked.
- `tasks/roadmap.md` — updates M25C progress and residual work.
- `tasks/history.md` — records the session outcome and QA state.
- `tasks/m25c-region-014-grade-c-implementation-ship-manifest.md` — defines
  this exact shipping boundary and its verification evidence.

## User-goal mapping

The generator and qualifier changes implement and constrain the approved
runtime behavior; the three test files prove its fail-closed boundaries; the
archived QA input preserves review lineage; and the README/task files report
the honest Grade C result, unchanged permissions, and remaining work.

## Implemented boundary

The assembled generator serially applies region `014`'s accepted routes in the
reviewed order:

1. `NON_EXECUTABLE_SEAM_ASSERTION` — decision
   `bc3d93698bbc6ff49adaf2dcc455321345c31fa7cf8a831903fc168a5170bec5`;
   evidence record
   `d57cf08e19249caab988cc7c4a2e1e8865bd269b5d3d50de7aaf575223ba1f3e`.
2. `SPATIAL_ASSERTION_FAILED` — decision
   `7ebb8826c48b59fbbf66d5cca5fbf0fca58359ff5ee56375a19d038eea33e70c`;
   evidence record
   `19dc79fe11921eb85f98c3e17b8196b69910e13e65e6557b2c6ab302f189af88`.
3. `UNCERTIFIED_A_GRADE` — decision
   `fc71a2e7669af0dcdd199a2074d490749b9c28c335188dbe8787225c8f6c5ad6`;
   evidence record
   `aee36988504f4403426a27bf3fba2c288f9313c663a391f494e30e59ab87025c`.

Generation requires review-decision SHA-256
`d16873c6ea3a10ca8127ddef04099c101cc8c7322e81c023ca4c56e9dc6acebd`,
rechecks all four artifact hashes pinned by that review, and requires the exact
25 accepted region `014` component decisions. Any drift stops generation and
requires a new independent review.

## Honest Grade C result

Only the `014/geometry` coverage row changes. It is Grade C and records all
accepted gaps: the 1400/1492 dates bracket the target; only one representative
point per component was tested; no source-derived edge, error measurement, or
whole-component containment exists; political actors, facets, relationships,
and Grade A/B remain unaccepted; and the Ethiopia-Somalia negative control
remains both non-executable and failed. No component, actor, relationship,
assertion tolerance, or seam geometry changed.

The replacement-evidence packet's pre-implementation worldwide QA snapshot is
archived at `cliopatria-v0.2.0/frozen-inputs/start_date_preflight.json` with its
original reviewed SHA-256
`659d36cb28745782718ca5fab23830817eb48ad31d3016c1fa081e01ef3c52c6`;
the live regenerated QA therefore does not invalidate that review lineage.

## QA regenerated

- Relevant implementation, review, evidence, seam, and assembly contracts:
  `89 passed`.
- Review render: all `30` sheets regenerated, including `014.svg`.
- Affected region `014`: `33` assertions, `32` pass and the retained
  Ethiopia-Somalia seam fails.
- Ordinary worldwide preflight: expected fail with `56` non-review errors and
  `1` pending-review warning. Counts are four applicability, 18 missing
  positive-border, eight non-executable seam, 13 spatial, 12 uncertified
  Grade-A, and one Grade-C global-coverage blocker.
- Candidate status remains `assembled_pending_research_qa`; public release,
  review acceptance, certification, and runtime publication remain false.

## Tests run

Executable pre-ship verification on `2026-08-24`:

- `.venv/bin/pytest` — `437 passed in 59.50s`; no warnings.
- `git diff --check` — passed.
- `python3 -m json.tool` on the archived preflight — passed.
- Archived preflight size and SHA-256 were rechecked against the evidence
  manifest — passed at
  `659d36cb28745782718ca5fab23830817eb48ad31d3016c1fa081e01ef3c52c6`.
- High-confidence credential/private-key indicator scan over the shipping
  boundary — no matches.

Documentation-only evidence: task/history/roadmap state was inspected against
the exact diff. No `scripts/audit-task-docs.mjs` exists in this repository, so
there is no configured task-document audit to run.

## Skipped tests

No separate lint, typecheck, or build command is configured in `pyproject.toml`,
and the repository has no root `CLAUDE.md`, `Makefile`, `Justfile`,
`package.json`, `setup.cfg`, or `Cargo.toml` defining one. The full configured
pytest suite is therefore the executable project gate. The already regenerated
30-sheet render and ordinary worldwide QA were not repeated during wrap-up;
their exact results are recorded above and the shipped code/tests do not claim
that the candidate is clean.

## Adversarial review

No configured `quality-sweep` or `expert-review` lane exists, so the equivalent
targeted audit challenged the implementation with review-file hash drift,
reviewed-artifact drift, route decision/scope/hash mismatch, incomplete or
extra component decisions, an altered Grade C gap list, an extra coverage
exception, and a missing or reordered changelog suffix. The implementation or
tests fail closed for each boundary. The audit also confirmed that provisional
generation does not apply the routes and that the archived reviewed input is
manifest-bound rather than silently replaced by the regenerated live report.

## Residual risk

The accepted source geometry is intentionally Grade C: dates bracket the target
and component testing is representative-point-only, without source-derived
edges, error measurement, or full-containment proof. The retained seam failure,
the global Grade-A blocker, 55 other non-review errors, and the pending-review
warning remain explicit. All review, certification, runtime, and public-release
permissions remain false, limiting this risk to the non-public research
candidate.

## Rollback note

Revert the shipping commit to restore region `014`'s prior Grade-A packet claim
and live-input lookup. Do not delete the archived pre-implementation QA file
independently: it is part of the review-lineage boundary introduced by this
change.

## Residual work

Eight accepted Grade C routes remain for serial implementation in regions
`017`, `018`, and `053`. All rejected routes remain fail-closed and require
stronger evidence. Task 17 cannot open until coverage is gap-free Grade A and
ordinary QA has zero errors.

## Next command

`$exec` — serially implement the remaining accepted Grade C routes, beginning
with the next exact route in the reviewed decision order.
