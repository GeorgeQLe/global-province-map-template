# M25C region 013 corridor evidence-review ship manifest

## User goal

Review the next separate Task 16 evidence packet, region `013`, without
changing its corridor unless the packet independently qualifies.

## Changed files

- `tasks/m25c-region-013-corridor-evidence-review.md`
- `tasks/m25c-region-013-corridor-evidence-review-ship-manifest.md`
- `tasks/history.md`
- `tasks/todo.md`

## Per-file purpose

The evidence review binds the current generator, regional packet, negative
control, assembled artifacts, exact assertion diagnostics, and empty eligible
affected-component set. It records why the packet's broad syntheses, atlas
maps, and checked centers do not qualify either a complete Mexico-Guatemala
corridor reconstruction or a positive border. This manifest defines the
shipped boundary and verification. History records the rejected
implementation, and the active todo retains Task 16 as open while routing past
the completed region `013` review.

## User-goal mapping

The review confirms that every region assignment first depends on Natural
Earth `ADM0_A3` and that the historical actor chooser contains separate `MEX`,
`GTM`, and neighboring-country branches. The current stricter evaluator also
finds only `0.05028550174174008` eligible seam coverage and 171 missing side
samples, so it correctly leaves the ratio null. The packet contains no
independently georeferenced historical boundary, complete two-sided fabric, or
enumerated evidence-to-component old/new mapping.

The generator, regional packet, negative-control asset, `75 km` corridor,
`0.20` tolerance, positive-border backlog, and all review, certification,
runtime, publication, and deployment permissions remain unchanged.

## Tests run

- A fresh exact assembled-pass generation completed successfully under
  `/private/tmp/task16-region013-review`.
- Complete rendering produced all 30 expected review sheets.
- Ordinary preflight reproduced region `013`'s four fail-closed findings and
  wrote the hash-bound report. The rendered worldwide result remained
  intentionally failing, with 58 non-review errors and one warning.
- SHA-256 checks reproduced the review-bound generator, packet, negative
  control, assembled artifacts, adjacency, and fabric-manifest hashes.
- Focused seam tests passed all 12 cases.
- `git diff --check` passed.

## Skipped tests

The complete repository suite, package build, and duplicate assembly were not
repeated because no source code, packet, generated asset, schema,
configuration, or runtime behavior changed. The focused seam tests exercise
the only executable contract referenced by this documentation review; current
assembled measurements and the complete render were freshly regenerated and
hash-bound rather than promoted.

No task-document audit ran because `scripts/audit-task-docs.mjs` is absent.

## Adversarial review

The exact diff was checked for accidental generator or packet edits, relaxed
tolerances, changed negative-control geometry, invented positive borders,
unapproved component values, stale use of the pre-phase-1 ratio, and
release-state changes. The review separately challenged partial eligible
coverage, global source attachment, checked-center substitution, broad atlas
maps, and self-validation from current status edges. None supplies the missing
full-seam, exact-date, independently derived spatial mapping, so the review
rejects rather than extrapolates.

## Residual risk

Region `013` retains its non-executable seam, failed spatial assertion,
missing-positive-border finding, and downstream uncertified geometry grade.
Resolving them requires a new packet with complete independent spatial
coverage and licensing or, for border non-applicability, a complete reviewed
land-adjacency disposition.

## Rollback note

Revert the documentation commit to remove this review and its tracking record.
No runtime or generated artifact rollback is required.

## Next command

`$exec` — review the next separate Task 16 evidence packet, region `014`,
without changing its corridor until the packet independently qualifies.
