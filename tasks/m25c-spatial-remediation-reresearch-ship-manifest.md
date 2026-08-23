# M25C worldwide spatial-remediation re-research ship manifest

Date: `2026-08-22`
Status: **research shipped; decision approved with amendments**

## User goal

Review the five-part spatial-remediation decision bundle one decision at a
time, approve or amend each treatment, and record the resulting implementation
boundary without changing remediation or release bytes.

## Changed files

- `tasks/m25c-spatial-remediation-reresearch.md`
- `tasks/m25c-spatial-remediation-reresearch-ship-manifest.md`
- `tasks/todo.md`
- `tasks/roadmap.md`
- `tasks/history.md`

## Per-file purpose

- `tasks/m25c-spatial-remediation-reresearch.md`: records George Le's five
  approvals and the exact superseding amendments for observability, Southern
  Europe, border applicability, Raichur, and later corridor review.
- `tasks/m25c-spatial-remediation-reresearch-ship-manifest.md`: binds the
  approved documentation and synchronized project ledgers to this shipping
  boundary.
- `tasks/todo.md`: splits first-phase implementation from the separately gated
  later corridor packets and final review.
- `tasks/roadmap.md`: advances M25C from decision pending to approved with
  amendments while preserving all candidate restrictions.
- `tasks/history.md`: records the approvals, amendments, staged boundary, and
  non-mutation result.

## User-goal mapping

- Decision 1 requires full usable-seam coverage, deterministic both-side
  sampling, reviewed non-unknown facets, and explicit rejection diagnostics.
- Decision 2 replaces blanket 464-record restoration with corridor-first,
  record-level work and independently derived Portugal-Castile stable segments.
- Decision 3 makes the five applicability regions candidates rather than
  automatic exemptions and binds qualification to exact revisions and hashes.
- Decision 4 separates Raichur points, zones, and borders and prohibits inferred
  frontier closure without independent exact-date evidence.
- Decision 5 adds separate pre-implementation approval and post-implementation
  verification for every other corridor or border.

## Tests run

- `git diff --check` passed with no whitespace errors.
- Exact changed-file and branch inspection confirmed a five-document boundary
  on `main`, with no unpushed pre-existing commits or generated skill changes.

## Skipped tests

- Python tests, rendering, runtime compilation, certification, and publication
  checks were skipped because this approval changes only Markdown decision and
  task records; no executable code, schema, data, or generated artifact changed.
- No task-document audit ran because `scripts/audit-task-docs.mjs` is absent.

## Adversarial review

The bundle was challenged decision by decision against current evaluator,
schema, packet, assertion, and source behavior. The resulting amendments close
partial-coverage false passes, legacy assignment restoration, candidate-derived
border geometry, automatic non-applicability, same-tradition source
corroboration, inferred Raichur closure, and untraceable batch remediation.

## Residual risk

- Approval is not implementation and does not reduce the current 54 post-render
  non-review blockers.
- Decisions 1-3 still require schema, QA, fixture, provenance, and worldwide
  regression work; their implementation may surface additional constraints.
- Portugal-Castile, Raichur, and every remaining corridor stay fail-closed when
  their source or independent-review conditions cannot be satisfied.

## Rollback note

Revert the documentation commit. Generated diagnostic candidates remain in
ignored `data/processed/` paths; no canonical, accepted-review, runtime,
certificate, demo, publication, or deployment artifact changed.

## Next command

Implement only the approved first phase recorded in
`tasks/m25c-spatial-remediation-reresearch.md`: the amended covered-zero
contract, corridor-first Southern Europe work and independently derived stable
Portugal-Castile segments, and fail-closed qualification of the five
applicability candidates. Keep Raichur hard-border promotion and every other
corridor or border stopped at their separate evidence-review gates.
