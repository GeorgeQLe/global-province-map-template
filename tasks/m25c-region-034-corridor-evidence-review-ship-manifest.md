# M25C region 034 evidence-review ship manifest

## User goal

Review region `034` (India–Bangladesh / Raichur) on the frozen Task 16 baseline without mutating evidence inputs.

## Changed files

- `tasks/m25c-region-034-corridor-evidence-review.md`
- `tasks/m25c-region-034-corridor-evidence-review-ship-manifest.md`
- `tasks/todo.md`
- `tasks/history.md`

## User-goal mapping

Disposition: **rejected**. The seam fails at full coverage; no independent Raichur point, zone, or line qualifies, and the stale generator can recreate a retired candidate-derived edge. The review rejects implementation and preserves every input and permission.

## Tests run

- One frozen assembled snapshot generated successfully and rendered all 30 sheets.
- Ordinary preflight reproduced exactly 58 non-review errors and one warning.
- `tests/test_m25c_modern_seam_controls.py` is run once for the unchanged snapshot after integration.
- Hash, assertion-row, affected-inventory, source-pin, and artifact checks are programmatically verified after all region files are integrated.
- `git diff --check`, documentation audit when available, staged secret scan, and documentation-only boundary checks run before push.

## Skipped tests

The full repository suite and build are not repeated because this commit changes documentation/task records only and the executable frozen snapshot is unchanged.

## Adversarial review

The fifth-wave cross-review challenged every disposition for inconsistent measurements, omitted adjacency pairs, modern dispatch, candidate-derived geometry, source contamination, and permission drift. Region `034` retained the disposition recorded above.

## Residual risk

Ordinary QA remains intentionally non-clean. Region `057` is the only approval candidate and its applicability-record implementation is deferred to a later serial phase; all other reviewed proposals require replacement evidence.

## Rollback note

Revert this documentation commit. No runtime or generated artifact rollback is required.

## Next command

`$exec` — serially implement and verify the independently reproduced region `057` applicability-record approval without changing the frozen corridor baseline.
