# M25C synthetic aggregate actor model revision ship manifest

Date: `2026-08-24`

Disposition: **research shipped; one revision recommended; no remediation**.

## User goal

Obtain a licensed exact-date actor polygon or independently derived shared line
for one named rejected record, or revise the synthetic aggregate actor model.

## Outcome

The model-revision branch was completed for `scenario-chorotega-polities` in
region `013`. The actor's one component is selected by a modern Nicaragua and
latitude heuristic, while its only measurable named polygon bindings are later
Matagalpa, Silam, Ulva, Yosco, and Maribichicoa surfaces. The recommended model
is an identity-unresolved community fabric with no ownership, control,
sovereignty, known authority, or implied hard borders.

No exact-date polygon or shared line was claimed. The one component, prior
actor records, and three incident rejected pairs are hash-bound. Implementation
is pending independent review, and region `013` remains fail-closed until a
complete adjacency applicability audit is independently accepted.

## Changed files

- `scripts/generate-m25c-synthetic-actor-model-revision.py`
- `tests/test_m25c_synthetic_actor_model_revision.py`
- `research/start-dates/1444-global-v1/replacement-evidence/synthetic-actor-model-revision-v1/README.md`
- `research/start-dates/1444-global-v1/replacement-evidence/synthetic-actor-model-revision-v1/chorotega-model-revision.json`
- `research/start-dates/1444-global-v1/replacement-evidence/synthetic-actor-model-revision-v1/manifest.json`
- `tasks/m25c-synthetic-actor-model-revision.md`
- `tasks/m25c-synthetic-actor-model-revision-ship-manifest.md`
- `tasks/history.md`
- `tasks/todo.md`

## Per-file purpose

- The generator extracts and hash-binds the exact actor, component, pair, and
  region-generator records, then emits the proposed semantic revision.
- The test module verifies deterministic reproduction, record/artifact hashes,
  the exact one-component/three-pair scope, and the fail-closed model fields.
- The research packet README, decision JSON, and manifest document the evidence,
  frozen inputs, alternatives, decision boundary, and zero immediate QA impact.
- The task report and ship manifest record the recommendation and shipping
  boundary; history and todo preserve the completed research and next review.

## User-goal mapping

- Named rejected record: `scenario-chorotega-polities` is explicitly bound to
  its one component and three incident rejected pairs.
- Synthetic-model revision: the territorial polity aggregate is replaced in
  the proposal by an identity-unresolved `community` with uncertain presence.
- Fail-closed handling: no exact-date polygon or shared line is claimed, and no
  implementation or region-level applicability approval is performed.

## Verification

```bash
.venv/bin/pytest -q \
  tests/test_m25c_synthetic_actor_model_revision.py \
  tests/test_m25c_exact_source_evidence.py \
  tests/test_m25c_actor_component_evidence.py \
  tests/test_m25c_best_reasonable_evidence.py \
  tests/test_m25c_replacement_evidence.py
```

Result: `19 passed`.

```bash
.venv/bin/python -m py_compile \
  scripts/generate-m25c-synthetic-actor-model-revision.py
git diff --check
```

Result: both pass without output.

## Adversarial review

A failure-oriented diff review checked for temporal back-projection, selective
pair removal, unbound generator assumptions, accidental packet implementation,
weakened regional applicability, and permission or QA changes. It found that
the first packet version stated the modern Nicaragua-plus-latitude dispatch
without hash-binding the region generator. The generator is now a frozen input,
and regeneration explicitly refuses if the exact Chorotega dispatch clause
changes. No unresolved finding authorizes geometry or applicability promotion.

## Skipped tests

The full repository suite was not run because the change adds a read-only,
deterministic research packet and does not alter application or runtime code.
The new suite and all four upstream M25C evidence suites verify the exact
frozen records, hash chain, fail-closed boundary, and deterministic generation.
No visual testing applies because no UI or rendered map changed.

## Residual risk

- The proposed neutral fabric fixes an overclaimed identity but supplies no
  positive historical identity for the component.
- Pair semantics cannot be applied selectively to qualify the region; the
  existing complete-inventory and independent-review requirements remain.
- The later Driver polygons have a documented date mismatch and conflicting
  license metadata, so they remain mismatch evidence only.

## Rollback note

Revert this research change to remove the generator, decision packet, tests,
and task-document entries together. No data or operational rollback is needed.

## Next command

`$exec` — independently review the exact hash-bound Chorotega actor-model
revision; if accepted, implement it serially and regenerate the complete region
`013` adjacency applicability audit before rerunning worldwide QA.
