# M25C best-reasonable supplemental evidence ship manifest

Date: `2026-08-24`

## User goal

Make the best reasonable attempt to obtain pair-specific and
component-specific evidence for all 43 deferred M25C findings, while keeping
approximate evidence distinct from Grade-A certification.

## Changed files

- `scripts/generate-m25c-best-reasonable-evidence.py`
- `tests/test_m25c_best_reasonable_evidence.py`
- `research/start-dates/1444-global-v1/replacement-evidence/best-reasonable-v1/README.md`
- `research/start-dates/1444-global-v1/replacement-evidence/best-reasonable-v1/manifest.json`
- `research/start-dates/1444-global-v1/replacement-evidence/best-reasonable-v1/pair-evidence.json`
- `research/start-dates/1444-global-v1/replacement-evidence/best-reasonable-v1/component-evidence.json`
- `research/start-dates/1444-global-v1/replacement-evidence/best-reasonable-v1/finding-routes.json`
- `tasks/m25c-best-reasonable-supplemental-evidence.md`
- `tasks/m25c-best-reasonable-supplemental-evidence-ship-manifest.md`
- `tasks/todo.md`
- `tasks/roadmap.md`
- `tasks/history.md`
- `tasks/lessons.md`

## Per-file purpose

- The generator validates pinned external bytes, spatially joins all deferred
  pair/component surfaces, emits record hashes, and pins every regional input.
- The executable test verifies exact frozen identities and counts, manifest and
  record hashes, confidence totals, route types, feature-ID auditability, and
  the pending-review boundary.
- The five packet files explain and carry the 43-route, 180-pair, and
  512-component evidence surface with exact source and artifact hashes.
- The supplemental task record explains the confidence and certification
  policy and hands off independent review.
- The todo, roadmap, and history record the completed research step without
  claiming implementation or certification.
- The lessons entry records the user's correction from exact-only evidence to
  a best-reasonable attempt and the repeatable guardrails for future work.
- This manifest defines the exact shipping boundary and verification evidence.

## User-goal mapping

- Pair-specific evidence: `pair-evidence.json` binds all 180 frozen nonzero
  actor pairs to exact incident components, matched feature IDs, reviewed
  regional source IDs, confidence, rationale, and limitations.
- Component-specific evidence: `component-evidence.json` binds all 512 deferred
  corridor components to exact current state, representative points, spatial
  features, reviewed sources, confidence, and limitations.
- All 43 findings: `finding-routes.json` maps each deferred finding to its exact
  pair or component records.
- Best reasonable, not overstated: all records remain pending independent
  review, and bracketing or incompletely sourced geometry is limited to zonal
  or documented Grade-B/C use unless separate Grade-A gates pass.

## Tests run

- Executable verification: `.venv/bin/pytest -q
  tests/test_m25c_best_reasonable_evidence.py
  tests/test_m25c_replacement_evidence.py` — `8 passed in 2.89s`, with no
  warnings.
- Executable syntax verification: `.venv/bin/python -m py_compile
  scripts/generate-m25c-best-reasonable-evidence.py
  tests/test_m25c_best_reasonable_evidence.py` — passed with no output.
- Determinism verification: regenerated all JSON artifacts into a fresh
  temporary directory and compared them byte-for-byte; no generated-artifact
  differences were found.
- Patch hygiene: `git diff --check` — passed with no output.
- Secret-pattern scan over the changed source, tests, task records, and packet
  README — no matches.

## Skipped tests

- The full repository suite was not run because this change adds an isolated
  research generator and immutable packet; the focused suite exercises the new
  generator contract plus the existing M25C replacement-evidence contract.
- No lint or type-check command is configured in `pyproject.toml`, and no
  Makefile, Justfile, or package script supplies one. Python compilation and
  focused executable tests cover the relevant validation surface.
- No build was run because no packaged runtime code, schema, or distribution
  input changed.
- The ship skill's referenced `docs/quality-gate-contract.md` is absent; the
  manifest and adversarial-review requirements stated in the skill were
  applied directly.

## Adversarial review

An explicitly justified local equivalent review traced every generator input,
record identity, self-hash, output hash, confidence transition, and review
state. It found and fixed three auditability gaps before ship:

1. Pair summaries exposed matched names but not the exact matched feature IDs.
   Pair records now include all and sourced feature-ID lists per evidence
   surface, with executable assertions.
2. The manifest pinned the primary applicability/status inputs but omitted the
   regional packet and dossier files that also influence output. It now pins
   the path and SHA-256 of all 22 regional packets and all 18 dossiers, with
   executable hash verification.
3. Pair aggregation initially allowed enough names from one approximate
   snapshot to qualify as medium despite the documented both-snapshots rule.
   The generator now requires sourced OHM or named matches in both 1400 and
   1492, and an executable assertion enforces that transition. The honest
   result is 127 medium- and 53 low-confidence pairs.

The review also regenerated the packet independently and confirmed stable
bytes. No unresolved correctness finding remains inside the stated research
boundary.

## Residual risk

- Historical Basemaps snapshots bracket the target by 44 and 48 years and use
  approximate `BORDERPRECISION=1` geometry.
- Only 21 of 113 usable OHM polygons carry source tags; feature-level lineage
  still requires human-quality independent review.
- Regional citations may establish context without establishing a precise
  pair interface or component line.
- `medium` and `low` are evidence-strength labels, not approval decisions.
- The assembled-pass contract still requires gap-free Grade A, so accepted
  Grade-B/C reconstruction alone cannot open Task 17.

## Rollback note

Revert the shipping commit to remove the generator, test, packet, and task-doc
updates together. No runtime artifact, permission, tolerance, regional packet,
or assembled candidate was mutated, so no data migration or operational
rollback is required.

## Correction enforcement

The shipping boundary includes `tasks/lessons.md`. The new generator and test
make the correction repeatable by requiring a complete confidence-graded
43/180/512 evidence surface while preserving source qualification, exact hash
lineage, and pending independent review.

## Next command

`$exec independently review the M25C best-reasonable evidence packet record by
record, recording narrow acceptance or rejection and an honest geometry grade`
