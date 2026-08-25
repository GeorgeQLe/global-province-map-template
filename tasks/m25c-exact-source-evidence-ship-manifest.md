# M25C exact-source evidence ship manifest

Date: `2026-08-24`

Disposition: **research shipped; zero qualifying records; no remediation**.

## User goal

Obtain new exact actor-to-citation and component/line sources for every
remaining rejected M25C evidence record, preserve the fail-closed boundary,
and submit only genuinely qualifying records for independent review.

## Changed files

- `scripts/generate-m25c-exact-source-evidence.py`
- `tests/test_m25c_exact_source_evidence.py`
- `research/start-dates/1444-global-v1/replacement-evidence/exact-source-v1/README.md`
- `research/start-dates/1444-global-v1/replacement-evidence/exact-source-v1/source-registry.json`
- `research/start-dates/1444-global-v1/replacement-evidence/exact-source-v1/source-audit.json`
- `research/start-dates/1444-global-v1/replacement-evidence/exact-source-v1/actor-citation-evidence.json`
- `research/start-dates/1444-global-v1/replacement-evidence/exact-source-v1/component-line-evidence.json`
- `research/start-dates/1444-global-v1/replacement-evidence/exact-source-v1/pair-evidence.json`
- `research/start-dates/1444-global-v1/replacement-evidence/exact-source-v1/finding-submissions.json`
- `research/start-dates/1444-global-v1/replacement-evidence/exact-source-v1/manifest.json`
- `tasks/m25c-exact-source-evidence.md`
- `tasks/m25c-exact-source-evidence-ship-manifest.md`
- `tasks/history.md`
- `tasks/todo.md`

There were no unrelated pre-existing worktree changes. Generated local skill
roots and `.agents/project.json` are unchanged and excluded from the boundary.

## Per-file purpose

- The generator creates deterministic full-component, actor, pair, and route
  bindings and refuses to run without all five Driver source parts.
- The test module verifies frozen-surface completeness, canonical record and
  artifact hashes, source checksums, positive measurements, and fail-closed
  exact-date/line gates.
- `source-registry.json` records eight exact source locators plus their date,
  geometry, access, and license qualifications; `source-audit.json` adds
  canonical hashes to those records.
- The actor, component, pair, and finding JSON files bind the new source audit
  to all 107 actors, 206 rejected components, 180 pairs, and 32 remaining
  finding routes.
- The packet README and manifest document reproduction, source-file hashes,
  totals, artifact hashes, decision boundaries, and the non-redistribution of
  the upstream shapefile.
- The task report and this manifest record the research conclusion, quality
  boundary, rollback, and next work; history and todo expose the completed
  pass and retained blocker to future sessions.

## User-goal mapping

- Exact actor-to-citation mapping: 32 actors now have complete named Driver
  feature bindings across their incident components; every actor record binds
  exact source-registry hashes.
- Component sources: 74 rejected components now have full equal-area
  intersections with named, hashed source polygons.
- Pair sources: 53 pairs now have complete named-feature bindings on both
  sides, with exact incident-component and actor-record hashes.
- Line and exact-date qualification: all records remain rejected because no
  source establishes the exact synthetic actors and component or shared line
  on `1444-11-11`; zero records are submitted for acceptance.

## Tests run

Executable verification:

```bash
.venv/bin/pytest -q \
  tests/test_m25c_exact_source_evidence.py \
  tests/test_m25c_actor_component_evidence.py \
  tests/test_m25c_best_reasonable_evidence.py \
  tests/test_m25c_replacement_evidence.py
```

Result: the final pre-ship run passed all 16 tests with no warnings.

```bash
.venv/bin/python -m py_compile scripts/generate-m25c-exact-source-evidence.py
git diff --check
```

Result: both passed with no output or warnings.

Documentation/task checks: no `scripts/audit-task-docs.mjs` exists, so no
repository-specific task-doc executable was available.

## Skipped tests

- The full repository test suite was not repeated because the change is an
  isolated research generator and generated evidence packet. The focused test
  plus all three directly upstream M25C evidence suites exercise the changed
  hashes, frozen IDs, generation boundary, and downstream assumptions.
- No lint, static typecheck, or build command is configured in `pyproject.toml`
  or a Makefile/package manifest. Python compilation covers syntax/import
  parsing for the changed executable script.
- Visual testing is not applicable: no UI, rendered map, or runtime artifact
  changed.

## Adversarial review

Method: changed-file failure-oriented self-review plus source/record count
cross-checks and the four executable evidence suites above. The review looked
for temporal promotion, source-ID fan-out without record hashes, missing frozen
regions, optional-source destructive regeneration, candidate-derived linework,
license normalization, and accidental implementation or permission changes.

Findings and fixes:

1. Region `039` had rejected components but no applicable discovery source in
   the registry. Euratlas, SUNGEO, and WHG were explicitly routed to `039` and
   the packet was regenerated.
2. `--driver-base` was optional, allowing an accidental canonical regeneration
   with zero Driver measurements. It is now required.
3. Source IDs alone would have repeated the prior citation fan-out weakness.
   Actor and component records now bind canonical source-record hashes.

No unresolved review finding authorizes acceptance or implementation.

## Residual risk

- The Driver paper reports CC BY-NC 2.5 while Zenodo reports CC BY 4.0. The
  conflict remains explicit and prevents source redistribution or promotion.
- Reproduction downloads five externally hosted source parts and requires
  isolated `pyshp`/`pyproj` tooling not used by the application runtime. The
  generated manifest and test pin every expected source SHA-256, so source
  drift fails verification rather than silently changing evidence.
- Named polygon overlap does not establish that a synthetic aggregate actor is
  identical to the historical source group in 1444. Reviewers will observe
  this as `retain_rejected` and zero qualifying route submissions.

## Rollback note

Revert the shipping commit to remove the registry, generator, evidence packet,
tests, and task-document updates together. No data migration or operational
rollback is required because no regional packet, runtime artifact, QA result,
permission, or release state changed.

## Next command

`$exec` — obtain a licensed exact-date actor polygon or independently derived
shared line for one named rejected record, or revise the synthetic aggregate
actor model before repeating broad atlas discovery.
