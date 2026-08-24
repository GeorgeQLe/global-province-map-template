# M25C worldwide replacement-evidence review ship manifest

Date: `2026-08-24`

## User goal

Independently accept, reject, or request supplemental evidence for every
worldwide replacement-evidence record before implementation, then wrap up the
session with current project ledgers, validation, commit, and push.

## Changed files

- `tasks/m25c-worldwide-replacement-evidence-independent-review.md`
- `tasks/m25c-worldwide-replacement-evidence.md`
- `tasks/todo.md`
- `tasks/roadmap.md`
- `tasks/history.md`
- `tasks/m25c-worldwide-replacement-evidence-review-ship-manifest.md`

## Per-file purpose

- The independent-review ledger records source, error-budget, eight direct
  border, ten applicability, 180 actor-pair, 757 corridor-component, and 56
  frozen-finding decisions with fail-closed scope.
- The replacement-evidence handoff records the completed review outcome while
  preserving its non-implementation boundary.
- The active todo identifies the accepted routes, exact supplemental backlog,
  unchanged blocker, and Task 17 gate.
- The roadmap updates M25C progress and remaining gap from pending decisions to
  partial acceptance plus supplemental research.
- History records the session outcome and confirms that no candidate or
  permission state changed.
- This manifest defines the exact shipping boundary, verification, risk, and
  next route.

## User-goal mapping

| Requirement | Shipped evidence |
| --- | --- |
| Decide every record independently | The review ledger covers all eight borders, ten applicability records, 180 pair rows, 757 component rows, and 56 frozen findings with exhaustive rules and totals. |
| Preserve fail-closed evidence standards | Uncovered, overlapping, and non-pair-specific evidence receives `supplemental_evidence_required`; no source silence is promoted to truth. |
| Decide before implementation | The review and all project ledgers state that no packet, candidate, tolerance, permission, runtime, or Task 17 state changed. |
| Leave actionable project state | Todo, roadmap, and history identify 43 deferred frozen findings and the exact supplemental-evidence classes. |

## Tests run

- Executable contract verification:
  `.venv/bin/pytest -q tests/test_m25c_replacement_evidence.py` — `4 passed`
  in `0.33s` with no warnings.
- Documentation/task validation: `git diff --check` — passed.
- Decision-accounting check: the frozen-finding table contains exactly 56
  records, including exactly 13 `accept` decisions; the source artifacts
  independently reproduce 180 actor-pair rows and 757 corridor rows split into
  245 single-polity, 509 uncovered, and three overlapping rows.

## Skipped tests

- The full Python suite, lint, typecheck, and build were not rerun because this
  boundary changes only Markdown review and project ledgers. No executable,
  schema, generator, source data, assembled artifact, or runtime behavior
  changed. The focused executable evidence test already verifies the frozen
  evidence accounting, hashes, geometry derivation, and unsigned state.
- Browser and deployment tests are inapplicable because no user-facing or
  deployable asset changed.

## Adversarial review

The review challenged source independence, temporal applicability, the
unquantified historical-border uncertainty, use of a universal operational
budget, source silence, overlapping source polygons, representative-point
overreach, region-wide applicability labels, and accidental partial-corridor
promotion. The final decisions accept the source only for polity coverage and
untouched shared-boundary derivation, constrain `20 km` to fabric mapping, and
fail closed on every incomplete surface. Counts were recomputed directly from
the frozen JSON and GeoJSON rather than copied from the authored summary.

## Residual risk

Cliopatria remains a smoothed interpretation with unquantified historical
boundary uncertainty. Accepted direct borders are therefore soft evidence,
not surveyed precision. The 43 supplemental frozen findings, 180 nonzero
actor-pair dispositions, and 512 uncovered or overlapping component rows still
authorize no edit. Even the 13 accepted routes require serial implementation,
duplicate regeneration, affected and neighboring QA, and ordinary worldwide
QA before they can change candidate status.

## Rollback note

Revert the session commit to remove the independent-review ledger and restore
the prior pending-decision wording in project ledgers. No data rollback or
regeneration is needed because this session changes documentation only.

## Next command

Use `$exec` to obtain pair-specific and component-specific supplemental
evidence for the 43 deferred frozen findings before any serial implementation.
