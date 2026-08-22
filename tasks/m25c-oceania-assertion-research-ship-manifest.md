# M25C Oceania assertion research ship manifest

## User goal

Research missing assertions for Oceania regions `053`, `054`, `057`, and `061`,
identify exact evidence-backed records, and recommend remediation without
implementing it before reviewer approval.

## Changed files

- `tasks/m25c-oceania-assertion-research.md`
- `tasks/todo.md`
- `tasks/roadmap.md`
- `tasks/history.md`
- `tasks/m25c-oceania-assertion-research-ship-manifest.md`

## Per-file purpose

- The research record defines the exact four-region scope, explains why
  Admin-0 controls do not work for island Oceania, specifies four Admin-1
  assertions, records fresh measurements, evaluates alternatives, and requests
  a reviewer decision.
- The todo marks research complete and preserves implementation as the next
  decision-gated step.
- The roadmap records the measured failure/pass/non-executable split without
  claiming remediation.
- The history records the research outcome and unchanged release boundary.
- This manifest records the exact shipping boundary and verification.

## User-goal mapping

The research specifies one exact, non-empty Natural Earth Admin-1 `5.1.1` seam
for each requested region and pins the archive checksum, ISO subdivision pair,
assertion ID, length, corridor, tolerance, transition count, and measurement.
It recommends one measured failure (`053`), one pass (`054`), and two
fail-closed non-executable controls (`057`, `061`). No packet, generated asset,
schema, QA implementation, runtime, certification, publication, or deployment
state changes in this boundary.

## Verification

- Generated a fresh temporary worldwide assembly from all 22 current regional
  packets. Existing intended certification blockers produced 27 errors: 13
  seam failures, 13 downstream uncertified-Grade-A findings, and the known
  Southern Europe non-executable finding.
- Read the pinned Natural Earth Admin-1 archive and confirmed all four proposed
  shared boundaries are deterministic, valid, non-empty `LineString` or
  `MultiLineString` geometries.
- Confirmed the archive SHA-256 is
  `efc59726337323058f9446210adc96673179cd344e053666ee3d28cb58ba2b05`.
- Measured candidates against the fresh canonical status assembly: `053`
  `1.0` with 16 transitions, `054` `0.0` with seven transitions, and `057` and
  `061` zero transitions with null fail-closed outcomes.
- Enumerated alternate internal Natural Earth seams to challenge candidate
  selection. Retained controls were chosen for modern legal provenance and
  historical-source scope, not because they maximize failures.
- `git diff --check` passed.

## Skipped tests

- Unit tests, lint, typecheck, package build, and runtime certification are
  inapplicable because this boundary changes only research and task Markdown.
- Packet regeneration and remediation QA are intentionally deferred until the
  reviewer approves or amends the recommendation.

## Adversarial review

The review rejected empty or external-region Admin-0 lines, historically
ambiguous Palau and independent-Samoa divisions, vacuous zero-transition
passes, maritime relations unsupported by the canonical land model, tolerance
changes, and fabricated positive borders. It distinguished disconnected-island
non-executability from absence of historical political diversity. No secret,
credential, private-key material, or prohibited release-credential file was
read or introduced.

## Residual risk

The recommendations are not implemented or independently approved. Four
regions still lack negative assertions, 19 still lack independently
georeferenced positive borders, and 13 existing seam failures block worldwide
certification. The proposed `057` and `061` controls would remain
non-executable until their canonical land fabric contains a sourced
land-adjacent status distinction.

## Rollback note

Revert this research change to remove only the research record, manifest, and
task-ledger updates. No generated evidence, runtime artifact, review acceptance,
deployment, or external state must be restored.

## Next command

After the reviewer approves or amends the four-part decision in
`tasks/m25c-oceania-assertion-research.md`, implement the approved Oceania
assertion remediation and verify its spatial and source-pinning gates.
