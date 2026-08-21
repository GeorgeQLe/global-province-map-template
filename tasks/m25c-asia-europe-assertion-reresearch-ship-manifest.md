# M25C Asia/Europe assertion re-research ship manifest

## User goal

Research the missing assertions for the affected Asia and Europe regions,
identify the exact records and evidence, and recommend a fail-closed
remediation without implementing it before reviewer approval.

## Changed files

- `tasks/m25c-asia-europe-assertion-reresearch.md`
- `tasks/todo.md`
- `tasks/roadmap.md`
- `tasks/history.md`
- `tasks/m25c-asia-europe-assertion-reresearch-ship-manifest.md`

## Per-file purpose

- The research record defines the exact six-region scope, evidence findings,
  six proposed modern-seam assertions, circular-border dispositions,
  alternatives, expected QA impact, and reviewer decision.
- The todo marks research complete and preserves implementation as the next
  decision-gated step.
- The roadmap records the measured risk and Southern Europe status-collapse
  blocker.
- The history records the session outcome without claiming implementation or
  certification.
- This manifest records the exact shipping boundary and verification.

## User-goal mapping

The research identifies regions `030`, `034`, `035`, `039`, `143`, and `145`;
specifies one exact Natural Earth 5.1.1 inland-seam control for each; measures
five current seam coincidences; identifies Southern Europe's zero-transition
non-executability; and recommends retiring six circular generated-edge border
assertions. No packet, assignment, status, tolerance, schema, QA behavior,
runtime pack, signature, review acceptance, certification, publication, or
deployment state changes in this shipping boundary.

## Tests run

Executable research verification:

- Generated a fresh temporary worldwide pass from all 22 current migrated
  regional packets successfully.
- Measured the proposed controls against that assembly: `030` `0.8389`, `034`
  `0.7985`, `035` `1.0`, `143` `1.0`, and `145` `1.0`; `039` had zero
  transitions and therefore exposed the fail-open case.
- Executed the existing nine seam assertions against the fresh assembly and
  confirmed seven failures plus the unchanged `021` and `029` passes; the two
  passing controls have 19 and two regional transitions respectively.

Documentation/task verification:

- `git diff --check` passed.
- Exact packet inspection confirmed every one of the six surviving positive
  borders uses `fabric-shared-boundary-extraction-wgs84` with `0.0 km`
  residual.
- Exact assembled-status inspection confirmed region `039` has 464
  assignments/components, one all-unknown facet signature, zero non-null
  political units, and zero active component statuses.
- No `scripts/audit-task-docs.mjs` exists, so no task-doc audit applies.

## Skipped tests

- Lint, typecheck, unit tests, package build, and runtime certification are
  inapplicable because this boundary changes only research and task Markdown;
  no executable source, scripts, configuration, schemas, generated assets, or
  dependencies changed.
- Remediation QA is intentionally deferred because the user requested research
  and the todo contract prohibits implementation before reviewer approval.

## Adversarial review

An explicit diff and source audit challenged the scope, candidate seams,
tolerances, and apparent passes. It rejected historically plausible long-lived
interfaces such as Portugal-Spain as negative controls, rejected external-region
seams that pass only through scope exclusion, and detected Southern Europe's
vacuous zero-transition result. It also compared all six positive gates with
the previously rejected Northern Africa provenance pattern and found the same
generated-edge self-comparison. No secret, credential, private-key material,
or prohibited release-credential file was read or introduced.

## Residual risk

The research recommendations are not yet implemented or independently
accepted. Seven existing Americas/Africa seam failures still block
certification; ten regions still lack negative assertions; thirteen regions
still lack positive borders; Southern Europe has no executable compositional
transition; and the six reviewed positive borders remain circular until the
reviewer authorizes remediation.

## Rollback note

Revert the research shipping commit. This removes only the research record,
manifest, and task-ledger updates; no generated evidence, runtime artifact,
review acceptance, deployment, or external state must be restored.

## Next command

After the reviewer approves or amends the four-part decision in
`tasks/m25c-asia-europe-assertion-reresearch.md`, run `$exec` to implement the
approved Asia/Europe assertion remediation and verify its spatial and
source-pinning gates.
