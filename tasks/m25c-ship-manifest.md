# M25C Certification Boundary Ship Manifest

## User goal

Ship the completed session boundary for the fail-closed M25C worldwide 1444
certification infrastructure, without deploying.

## Changed files

- `landing/demo/demo.js`
- `research/start-dates/1444-global-v1/README.md`
- `research/start-dates/1444-global-v1/anomaly_inventory.json`
- `research/start-dates/1444-global-v1/candidate_status.json`
- `research/start-dates/1444-global-v1/provenance/1444-v2-seed.json`
- `schemas/global-certification-manifest.schema.json`
- `schemas/historical-boundary-registry.schema.json`
- `schemas/historical-territory-status.schema.json`
- `schemas/polity-gazetteer.schema.json`
- `schemas/spatial-golden-borders.schema.json`
- `schemas/start-date-changelog.schema.json`
- `schemas/start-date-coverage.schema.json`
- `schemas/start-date-location-assignments.schema.json`
- `schemas/start-date-pass-manifest.schema.json`
- `schemas/start-date-qa-report.schema.json`
- `schemas/start-date-source-manifest.schema.json`
- `scripts/build-m25c-global-pass.py`
- `src/gpm/cli.py`
- `src/gpm/qa/__init__.py`
- `src/gpm/qa/certification.py`
- `src/gpm/qa/render.py`
- `src/gpm/qa/start_date.py`
- `src/gpm/release/demo.py`
- `src/gpm/release/site.py`
- `src/gpm/runtime/compiler.py`
- `src/gpm/schemas.py`
- `tasks/history.md`
- `tasks/m25c-ship-manifest.md`
- `tasks/roadmap.md`
- `tasks/todo.md`
- `tests/test_historical_certification_contract.py`
- `tests/test_m25c_global_certification.py`
- `tests/test_source_manifest_schema.py`

No unrelated worktree changes are excluded: all listed changes form the single
M25C session boundary. Generated `.codex/skills/**` and `.claude/skills/**`
roots are unchanged and are not part of the commit.

## Per-file purpose

- `landing/demo/demo.js`: render live era tabs from the validated generated
  manifest so a certified 1444 scenario can appear without a static UI edit.
- `research/start-dates/1444-global-v1/README.md`: document the permanent pass
  identity, pending status, hard gates, and regeneration command.
- `research/start-dates/1444-global-v1/anomaly_inventory.json`: enumerate every
  required worldwide anomaly class as unresolved rather than invent evidence.
- `research/start-dates/1444-global-v1/candidate_status.json`: explicitly forbid
  public release of the pending candidate.
- `research/start-dates/1444-global-v1/provenance/1444-v2-seed.json`: hash-pin
  every file in the preserved unsigned five-region pilot.
- `schemas/global-certification-manifest.schema.json`: define the accepted,
  hashed, all-gates-pass certification envelope.
- `schemas/historical-boundary-registry.schema.json`: admit additive schema 0.3
  worldwide boundary records.
- `schemas/historical-territory-status.schema.json`: admit schema 0.3 canonical
  worldwide status and its expanded relationship vocabulary.
- `schemas/polity-gazetteer.schema.json`: admit additive schema 0.3 polity data.
- `schemas/spatial-golden-borders.schema.json`: require source-locked tolerance
  policy for schema 0.3 assertions.
- `schemas/start-date-changelog.schema.json`: admit schema 0.3 changelogs.
- `schemas/start-date-coverage.schema.json`: admit schema 0.3 coverage matrices.
- `schemas/start-date-location-assignments.schema.json`: require schema 0.3
  worldwide assignment and release-sidecar fields.
- `schemas/start-date-pass-manifest.schema.json`: define the exact 22-part M49
  worldwide scope and required M25C artifacts.
- `schemas/start-date-qa-report.schema.json`: identify schema 0.3 M25C reports.
- `schemas/start-date-source-manifest.schema.json`: carry the reviewed-source
  contract into schema 0.3.
- `scripts/build-m25c-global-pass.py`: provide deterministic, fail-closed stages
  from pending inventory through certification.
- `src/gpm/cli.py`: expose certification input on demo builds and the
  `gpm qa certify-era` command.
- `src/gpm/qa/__init__.py`: export the certification API.
- `src/gpm/qa/certification.py`: enforce research, canonical/runtime parity,
  determinism, performance, review, artifact hashes, and bundle containment.
- `src/gpm/qa/render.py`: carry schema 0.3 worldwide scope into deterministic
  review rendering.
- `src/gpm/qa/start_date.py`: enforce worldwide partition, evidence, coverage,
  hierarchy, review, and artifact gates.
- `src/gpm/release/demo.py`: consume only intact accepted certification bundles
  when generating a public historical scenario.
- `src/gpm/release/site.py`: validate live historical scenarios and their
  certification linkage in the generated site manifest.
- `src/gpm/runtime/compiler.py`: preserve schema 0.3 canonical input identity in
  runtime compilation.
- `src/gpm/schemas.py`: implement semantic validators for the additive schema
  0.3 and global certification contracts.
- `tasks/history.md`: record the session result, evidence, and continuation.
- `tasks/m25c-ship-manifest.md`: record this exact quality-gated ship boundary.
- `tasks/roadmap.md`: mark the M25C boundary complete while keeping worldwide
  historical work in progress.
- `tasks/todo.md`: promote the concrete evidence, fabric, and review work that
  remains and record the completed infrastructure slice.
- `tests/test_historical_certification_contract.py`: update canonical typed
  relationship expectations for the additive contract.
- `tests/test_m25c_global_certification.py`: cover world partition, pilot
  provenance, source-locked tolerances, hash tampering, path escape, and demo
  refusal without certification.
- `tests/test_source_manifest_schema.py`: require the new schema in the shipped
  schema inventory.

## User-goal mapping

The schema, QA, runtime, and release changes make certification both executable
and fail-closed. The checked-in global-v1 research files preserve honest pending
state and exact pilot lineage. The tests prove that incomplete or altered
evidence cannot unlock the public scenario. Task documents distinguish this
completed infrastructure boundary from the unfinished worldwide research.

## Tests run

- `uv run --extra dev pytest tests/test_m25c_global_certification.py tests/test_historical_certification_contract.py tests/test_source_manifest_schema.py` — 15 passed before adversarial review.
- `uv run --extra dev pytest tests/test_m25c_global_certification.py` — 6 passed after adding bundle path containment.
- `uv run --extra dev pytest` — 310 passed on the final executable diff, with no warnings.
- `git diff --check` — passed.
- Changed-file credential-pattern scan — no credential values found; matches
  were ordinary `vercel_token` parameter names and certification filename
  filtering logic.

## Skipped tests

- No separate lint, typecheck, or build command is configured in
  `pyproject.toml`, a `Makefile`, a `Justfile`, or `package.json`; the declared
  full pytest suite is the repository's executable validation surface.
- No browser visual pass was run because no accepted worldwide certification
  bundle exists to render. The UI change only reflects validated manifest data,
  while Python contract tests cover the promotion gate. The first accepted
  bundle still requires a real generated-demo browser smoke test.
- No production-size runtime benchmark was run because the pending global-v1
  lineage intentionally has no reviewed worldwide canonical/runtime pack. The
  certification command itself runs and requires those budgets before it can
  emit an accepted manifest.

## Adversarial review

A changed-file, failure-oriented review traced the certification artifact paths
from validation through demo publication. It found that a hash-valid `../...`
artifact path could escape the certification bundle and be copied publicly.
`validate_certification_bundle` now rejects paths outside the manifest directory,
and `test_certification_bundle_rejects_artifacts_outside_bundle` proves the fix.
No other unresolved finding was accepted.

## Residual risk

The certified happy path has contract-level synthetic coverage but cannot be
exercised end to end at global scale until curated worldwide evidence, accepted
M23 assignments, and independent review exist. The first operator with those
inputs must run the full pipeline, inspect the generated review artifact, run
the embedded runtime benchmark, build the demo, and perform a browser smoke test.
The fail-closed pending status prevents this gap from becoming a public claim.

## Rollback note

Revert the M25C ship commit to remove schema 0.3 certification and certified-demo
promotion as one coherent boundary. The existing schema 0.1/0.2 research paths,
Modern-only public demo, M25A casebook, and M25B runtime remain independently
versioned.

## Next command

`$exec`
