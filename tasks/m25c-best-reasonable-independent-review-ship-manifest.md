# M25C best-reasonable independent-review ship manifest

Date: `2026-08-24`

## User goal

Independently review every M25C best-reasonable pair, component, and finding
route, recording narrow acceptance or rejection with honest geometry grades.

## Changed files

- `scripts/record-m25c-best-reasonable-review.py`
- `tests/test_m25c_best_reasonable_review.py`
- `research/start-dates/1444-global-v1/replacement-evidence/best-reasonable-v1/review-decisions.json`
- `research/start-dates/1444-global-v1/replacement-evidence/best-reasonable-v1/README.md`
- `tasks/m25c-best-reasonable-independent-review.md`
- `tasks/m25c-best-reasonable-independent-review-ship-manifest.md`
- `tasks/m25c-best-reasonable-supplemental-evidence.md`
- `tasks/todo.md`
- `tasks/roadmap.md`
- `tasks/history.md`

## Per-file purpose

- The review recorder serializes the independently chosen fail-closed policy
  and produces stable, per-record decision hashes.
- The executable test binds every decision to its exact evidence record,
  verifies input-artifact hashes, enforces Grade C/U totals, and proves that
  finding acceptance is complete and component-only.
- The review sidecar records all 180 pair, 512 component, and 43 finding-route
  decisions without mutating the frozen evidence manifest.
- The packet README records the review outcome while preserving the external
  sidecar boundary.
- The independent-review record explains the evidence failures, acceptance
  scope, grade policy, regional totals, and implementation gate.
- The supplemental task, todo, roadmap, and history advance project state from
  pending review to narrow Grade C acceptance without claiming implementation
  or certification.
- This manifest defines the exact shipping boundary and validation evidence.

## User-goal mapping

- Independent record coverage: the sidecar contains one hash-bound decision
  for every evidence record and finding route.
- Narrow acceptance/rejection: all 180 pair dispositions are rejected because
  the source surface does not map a qualifying claim to both actors; 306
  components are accepted only for the observable two-bracket point signal and
  206 are rejected.
- Honest geometry grades: accepted component records and eleven complete
  component-only routes are Grade C; rejected component surfaces are `U`;
  pair geometry is `not_applicable`. No record is Grade A or Grade B.
- Fail-closed implementation: no packet, component, assignment, QA result,
  tolerance, permission, runtime artifact, publication state, or Task 17 state
  changes in this shipping boundary.

## Tests run

- Executable full-suite verification: `.venv/bin/pytest -q` — `435 passed in
  148.16s`, with no warnings.
- Executable focused verification after final hash-binding assertions:
  `.venv/bin/pytest -q tests/test_m25c_best_reasonable_review.py
  tests/test_m25c_best_reasonable_evidence.py
  tests/test_m25c_replacement_evidence.py` — `11 passed in 0.39s`, with no
  warnings.
- Executable syntax verification: `.venv/bin/python -m py_compile
  scripts/record-m25c-best-reasonable-review.py` — passed with no output.
- Determinism verification: two consecutive review-sidecar generations
  produced SHA-256
  `d16873c6ea3a10ca8127ddef04099c101cc8c7322e81c023ca4c56e9dc6acebd`.
- Patch hygiene: `git diff --check` — passed with no output.
- Secret-pattern filename scan over every changed file — no matches.
- Task-doc audit: skipped because `scripts/audit-task-docs.mjs` is absent.

## Skipped tests

- No lint or type-check command is configured in `pyproject.toml`, and the
  repository has no Makefile, Justfile, or package script supplying one.
  Python compilation plus focused and full executable tests cover the changed
  script and contract.
- No build was run because no package configuration, runtime code, schema, or
  distribution input changed; the generated sidecar is exercised directly by
  the executable tests.
- The ship skill's referenced `docs/quality-gate-contract.md` is absent. Its
  manifest and adversarial-review requirements were applied directly here.

## Adversarial review

An explicitly justified local equivalent adversarial review challenged each
possible promotion path rather than trusting the packet's `medium` label:

1. Pair records were checked for actor-specific claim lineage. Even rows with
   complete named point coverage aggregate every regional citation and do not
   map a qualifying claim to both exact actors, so all 180 remain rejected.
2. Source-tagged OHM matches were checked for independently reviewable lineage.
   The evidence records expose only feature IDs, not the source value and full
   date-lineage detail, so no OHM flag promotes a component to Grade B.
3. Component acceptance was restricted to named representative-point matches
   in both approximate brackets. The accepted scope explicitly excludes whole
   polygons, source-derived edges, actors, facets, and relationships.
4. Finding routes were recomputed from their exact routed IDs. A component
   route is accepted only when every component is accepted, and every pair
   route is rejected. Executable tests enforce this atomicity and each source
   record hash.

No unresolved correctness finding remains inside the stated review-only
boundary.

## Residual risk

- Grade C acceptance rests on one representative point per component and on
  approximate snapshots 44 years before and 48 years after the target date.
- The accepted scope does not supply reconstruction linework; serial
  implementation must retain explicit gaps and may still fail spatial QA.
- The sidecar is a repository review record, not the final human acceptance
  signature required by the assembled-pass contract.
- The 180 rejected pair records and 206 rejected components still require
  stronger pair-to-citation or component geometry evidence.

## Rollback note

Revert the shipping commit to remove the review recorder, sidecar, tests, and
documentation updates together. No runtime or canonical data migration and no
operational rollback are required because implementation and release state
were not changed.

## Next command

`$exec serially implement the eleven accepted M25C Grade C finding routes,
preserving review hashes, explicit gaps, and fail-closed worldwide QA`
