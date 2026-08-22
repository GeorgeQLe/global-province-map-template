# M25C Assembled-Pass Transition Ship Manifest

## User goal

Implement the approved fail-closed two-gate M25C transition: truthfully relabel
an exactly complete worldwide replacement as an assembled certification-review
candidate, but keep it non-accepting until complete rendering and ordinary
pending-review QA report zero non-review errors. Do not remediate research
defects or create runtime, certification, publication, or deployment output.

## Changed files

- `README.md`
- `schemas/historical-territory-status.schema.json`
- `scripts/build-m25c-global-pass.py`
- `scripts/generate-m25c-provisional-pass.py`
- `src/gpm/qa/m25c_assembled.py`
- `src/gpm/qa/start_date.py`
- `tasks/history.md`
- `tasks/m25c-assembled-pass-transition-research.md`
- `tasks/m25c-assembled-pass-transition-ship-manifest.md`
- `tasks/roadmap.md`
- `tasks/todo.md`
- `tests/test_m25c_assembled_transition.py`

All listed changes belong to this M25C transition. The research record and task
documentation began as uncommitted work from the preceding approved research
step; they are intentionally preserved and completed in this shipping boundary.
No unrelated worktree change is included.

## Per-file purpose

- `README.md` documents the default-safe and assembled command paths and the
  current blocked result.
- `schemas/historical-territory-status.schema.json` types the optional canonical
  QA mode and provisional marker while preserving older artifacts.
- `scripts/generate-m25c-provisional-pass.py` adds explicit mode selection,
  pinned-input checks, truthful metadata, staging, qualification, and atomic
  promotion.
- `scripts/build-m25c-global-pass.py` makes generic assembly, preflight, and
  review acceptance recompute their authoritative gates.
- `src/gpm/qa/m25c_assembled.py` provides the single shared final-artifact and
  accepted-input qualifier.
- `src/gpm/qa/start_date.py` independently rejects mixed or surviving
  certification-review lineage.
- `tests/test_m25c_assembled_transition.py` covers the new state transition and
  adversarial failure paths.
- `tasks/m25c-assembled-pass-transition-research.md` records approval and the
  verified blocked outcome.
- `tasks/todo.md`, `tasks/roadmap.md`, and `tasks/history.md` reconcile milestone
  state and route the later remediation separately.
- This manifest records the exact quality and rollback boundary.

## User-goal mapping

- `scripts/generate-m25c-provisional-pass.py` keeps provisional generation as
  the default and adds explicit `--assembly-mode assembled-pass`, mode-specific
  output, required pinned packet/acceptance inputs, ordinary assembled QA, and
  rollback-safe same-filesystem promotion.
- `src/gpm/qa/m25c_assembled.py` is the shared fail-closed qualifier used by
  generation and generic assembly. It validates exact world closure, accepted
  inputs, reviewed citations, non-provisional lineage, versions, candidate
  permissions, containment, symlinks, and hashes.
- `scripts/build-m25c-global-pass.py` refuses unqualified assembly, recomputes
  authoritative preflight state, and runs complete-render plus zero-error QA
  before changing review bytes.
- `src/gpm/qa/start_date.py` rejects mixed M25C certification-review lineage,
  provisional canonical/aggregation flags, mixed versions, and the legacy
  source sentinel.
- `schemas/historical-territory-status.schema.json` adds typed optional
  `qa_mode` and `provisional` fields without changing older-artifact behavior.
- `tests/test_m25c_assembled_transition.py` covers explicit opt-in, exact
  closure, tampering, mixed lineage, path/symlink rejection, rollback, status
  transitions, pre-mutation review refusal, and generic relabel rejection.

## Verification boundary

The full assembled build renders 22 region sheets and eight represented anomaly
class sheets. Ordinary pending-review QA returns exactly 54 non-review errors:
16 `SPATIAL_ASSERTION_FAILED`, 16 `UNCERTIFIED_A_GRADE`, three
`NON_EXECUTABLE_SEAM_ASSERTION`, and 19
`MISSING_POSITIVE_BORDER_ASSERTION`, plus only the pending-review warning.

Candidate status remains `assembled_pending_research_qa`; review acceptance,
certification, runtime publication, and public release remain false.

## Verification

- Focused M25C transition/certification tests: 63 passed.
- Complete suite: 421 passed in 63.97 seconds. The sandboxed run could not bind
  three existing loopback-server tests; the authoritative outside-sandbox run
  passed all tests.
- Python compilation and `git diff --check`: passed.
- Two independent full assemblies had identical manifest artifact records
  (`a1b12c57f045a88335d70201c33558db244f5785bb61a43a3718001c685c8e8a`)
  and render records
  (`e694a5ba6e62b61eba404b706dbfe66938a7d98be500699d6b273a6dc9ff6be1`).
- Failed `accept-review` preserved manifest SHA-256
  `8323341832ef3881cf943bd4b5e055b68839ba858f98073b998116b921007280`
  and review-manifest SHA-256
  `8cdb4787c584428a26f908976c6b3a62e9d27c504059a560be99bda3e5fb19c2`.

## Tests run

- `.venv/bin/pytest -q tests/test_m25c_assembled_transition.py tests/test_m25c_global_certification.py`
  — 63 passed after the final qualifier hardening.
- `.venv/bin/pytest -q` outside the command sandbox — 421 passed. The outside
  run was required only because three existing viewer tests bind ephemeral
  loopback ports.
- `.venv/bin/python -m compileall -q src scripts tests` and targeted
  `py_compile` — passed without output or warnings.
- `git diff --check` — passed.
- Two full assembled builds and renders — artifact and render records matched.
- Current-world render/preflight — exact expected 54 errors and one warning.
- Current-world `accept-review` negative control — refused before byte mutation.

## Skipped tests

- Runtime compilation, certification, demo promotion, publication, and
  deployment were intentionally skipped because this task must stop at the
  QA-blocked research candidate; exercising a positive release path would
  exceed the approved boundary. Existing regression tests still cover their
  rejection of provisional or uncertified lineage.
- No visual browser inspection was required: the render output is diagnostic,
  not the final human acceptance bundle, and deterministic render hashes plus
  complete render-manifest validation are the relevant executable checks.
- No manual deployment was attempted because the repository has no `deploy.md`
  or `tasks/deploy.md` contract.

## Adversarial review

A failure-oriented exact-diff review challenged packet duplication and closure,
override overlap, coverage gaps, accepted-input tampering, source resolution,
mixed modes and versions, provisional residue, sidecar path escape, nested and
referenced symlinks, transactional swap failure, generic relabeling, stale
candidate permissions, incomplete render acceptance, and mutation-before-QA.
The review added whole-tree symlink rejection and exact pinned source-directory
checks. All findings are fixed and covered by focused tests or full-world
execution; no review finding remains accepted without mitigation.

## Residual risk

- The accepted fabric and world-mask hashes are intentionally pinned constants.
  A future independently accepted fabric revision must update those constants,
  fixtures, and research documentation together; otherwise assembly fails
  closed at input qualification.
- The current evidence remains research-invalid on the enumerated 54 findings.
  Operators will see a nonzero preflight and all permissions false. The first
  follow-up is separately approved seam and positive-border remediation, not a
  review or release command.
- Directory promotion uses same-filesystem atomic renames. A post-promotion
  inability to delete the rollback copy leaves a recoverable hidden backup but
  does not expose a partial candidate.

## Rollback

Revert this implementation change. Generated diagnostic candidates live only in
ignored temporary/processed directories. No accepted review, runtime pack,
certificate, demo, publication, deployment, or irreversible migration exists.

## Next command

`$exec` after a reviewer approves the separately decision-gated remediation of
the 16 failed seams, three non-executable seams, and 19 missing positive borders.
