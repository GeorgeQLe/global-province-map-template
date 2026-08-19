# M25C Polity/Source Cleanup Ship Manifest

## User goal

Implement the reviewer-approved record-by-record cleanup of the surviving M25C
provisional polity/source references, preserve the fail-closed certification
boundary, verify ordinary worldwide research QA, and advance the task ledger to
the next evidence-remediation step.

## Changed files

- `scripts/generate-m25c-provisional-pass.py`
- `tests/test_m25c_global_certification.py`
- `tasks/todo.md`
- `tasks/roadmap.md`
- `tasks/history.md`
- `tasks/m25c-polity-source-cleanup-ship-manifest.md`

## Per-file purpose

- `scripts/generate-m25c-provisional-pass.py` encodes the approved reviewed and
  pruned polity sets, replaces the approved legacy core aliases, removes the
  exact obsolete boundary and assertion sets, deletes the exhausted scaffold
  source, and rejects any unexpected input or surviving reference.
- `tests/test_m25c_global_certification.py` exercises the exact cleanup contract
  against a controlled complete fixture and verifies the resulting source,
  polity, boundary, assertion, and assignment state.
- `tasks/todo.md` completes the research and implementation decisions and names
  assertion research as the next active step.
- `tasks/roadmap.md` records the source-clean M25C state and its remaining
  assertion, review, runtime, and publication gates.
- `tasks/history.md` records the cleanup outcome and executable validation.
- This manifest records the exact shipping boundary, verification, review,
  residual risk, rollback, and next command.

## User-goal mapping

The generator applies only the approved sets and counts, retains scaffold
polities only when a reviewed replacement source exists, refuses to remove any
still-referenced polity or asserted provisional boundary, and proves the
provisional source identifier is absent from every assembled evidence artifact.
The task and roadmap updates advance only the approved cleanup work; assertion
research, independent review, runtime certification, and publication remain
explicitly open.

## Tests run

- Executable targeted regression: `uv run --extra dev pytest -q
  tests/test_m25c_global_certification.py::test_approved_polity_source_cleanup_is_exact_and_fail_closed`
  — 1 passed.
- Executable complete suite: `uv run --extra dev pytest -q` — 389 passed in
  17.76 seconds, with no failures or test warnings.
- Executable worldwide assembly/internal QA: a fresh 22-packet pass produced
  229 sources, 336 polities, 22 boundaries, and 689 assertions with no surviving
  `official-1444-modern-scaffold-provisional` reference; QA passed with zero
  errors and five accepted pre-render warnings.
- Executable render/pending-review QA: `gpm qa render` produced all 30 applicable
  region and anomaly sheets; `gpm qa start-date --pending-review` passed with
  zero errors and three accepted warnings.
- Executable syntax/package checks: `python -m compileall` passed for `src` and
  the changed generator; `uv build` produced the wheel and source distribution.
- Source and documentation hygiene: `git diff --check` and a changed-file
  credential/private-key pattern scan passed. No task-doc audit script exists.

## Skipped tests

- No standalone lint or typecheck command is declared in `pyproject.toml`, the
  README, a Makefile, or a Justfile, so there is no project lint/typecheck lane
  to run; compilation and the complete executable suite cover Python validity.
- Runtime compilation, certification, publication, and production smoke tests
  were intentionally skipped because missing assertions and independent human
  review still make the provisional lineage non-certifiable and non-public.
- No deployment ran because the repository has no `deploy.md` or
  `tasks/deploy.md` manual deploy contract.

## Adversarial review

An explicit equivalent adversarial sweep inspected every changed code path and
the exact shipping diff. A fresh invocation without regional packet inputs was
deliberately rejected with `approved cleanup found unexpected provisional polity
records`, demonstrating that incomplete or stale evidence cannot silently cross
the cleanup boundary. The canonical 22-packet invocation then proved exact
record counts, reviewed replacement sources, no live references to pruned
polities, no asserted pruned boundaries, and zero source-id residue. Complete
QA exercised schema, checksum, path-containment, reference-closure, topology,
and spatial assertion gates. No unresolved executable failure remains.

The five pre-render warnings are accepted and expected: missing region renders,
missing anomaly renders, pending independent review, missing negative-
anachronism assertions, and missing positive-border assertions. Rendering
closes the first two, leaving only the three intended research/review blockers.

## Residual risk

The approved cleanup is intentionally coupled to exact current record sets and
counts; a future packet change affecting those inputs will fail closed and will
require a new reviewed decision. Nineteen regions still lack a negative-
anachronism assertion, twelve still lack a positive-border assertion, and the
worldwide bundle remains unsigned. These are explicit blockers, not accepted
release risk.

## Rollback note

Revert the M25C polity/source cleanup commit. This restores the prior
provisional source, polity, core, boundary, and pilot-assertion state together
with its tests and task records. No database, deployed service, accepted review,
certificate, or irreversible migration is involved.

## Next command

`$exec`
