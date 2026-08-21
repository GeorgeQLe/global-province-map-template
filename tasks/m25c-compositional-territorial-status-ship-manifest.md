# M25C Compositional Territorial-Status Ship Manifest

Date: 2026-08-21

## User goal

Ship the completed worldwide compositional territorial-status migration cleanly
to the primary branch, preserving research and runtime fail-closed boundaries.

## Changed files

- `README.md`
- `ROADMAP.md`
- `docs/compositional-territorial-status.md`
- `research/start-dates/1444-global-v1/regional-packets/005-south-america-2026-08-16.json`
- `research/start-dates/1444-global-v1/regional-packets/011-western-africa-2026-08-16.json`
- `research/start-dates/1444-global-v1/regional-packets/013-central-america-2026-08-16.json`
- `research/start-dates/1444-global-v1/regional-packets/014-eastern-africa-2026-08-16.json`
- `research/start-dates/1444-global-v1/regional-packets/015-northern-africa-2026-08-16.json`
- `research/start-dates/1444-global-v1/regional-packets/017-middle-africa-2026-08-16.json`
- `research/start-dates/1444-global-v1/regional-packets/018-southern-africa-2026-08-16.json`
- `research/start-dates/1444-global-v1/regional-packets/021-northern-america-2026-08-16.json`
- `research/start-dates/1444-global-v1/regional-packets/029-caribbean-2026-08-16.json`
- `research/start-dates/1444-global-v1/regional-packets/030-eastern-asia-2026-08-16.json`
- `research/start-dates/1444-global-v1/regional-packets/034-southern-asia-2026-08-16.json`
- `research/start-dates/1444-global-v1/regional-packets/035-south-eastern-asia-2026-08-16.json`
- `research/start-dates/1444-global-v1/regional-packets/039-southern-europe-2026-08-15.json`
- `research/start-dates/1444-global-v1/regional-packets/053-australia-new-zealand-2026-08-16.json`
- `research/start-dates/1444-global-v1/regional-packets/054-melanesia-2026-08-16.json`
- `research/start-dates/1444-global-v1/regional-packets/057-micronesia-2026-08-16.json`
- `research/start-dates/1444-global-v1/regional-packets/061-polynesia-2026-08-16.json`
- `research/start-dates/1444-global-v1/regional-packets/143-central-asia-2026-08-16.json`
- `research/start-dates/1444-global-v1/regional-packets/145-western-asia-2026-08-15.json`
- `research/start-dates/1444-global-v1/regional-packets/151-eastern-europe-2026-08-15.json`
- `research/start-dates/1444-global-v1/regional-packets/154-northern-europe-2026-08-15.json`
- `research/start-dates/1444-global-v1/regional-packets/155-western-europe-2026-08-15.json`
- `research/start-dates/1444-global-v1/regional-packets/README.md`
- `schemas/historical-territory-status.schema.json`
- `schemas/polity-gazetteer.schema.json`
- `schemas/runtime-pack.schema.json`
- `schemas/start-date-location-assignments.schema.json`
- `schemas/territorial-status-overlay.schema.json`
- `scripts/generate-m25c-provisional-pass.py`
- `scripts/migrate-territorial-status-packets.py`
- `src/gpm/cli.py`
- `src/gpm/exporters/__init__.py`
- `src/gpm/exporters/atlas.py`
- `src/gpm/historical/__init__.py`
- `src/gpm/historical/territorial_status.py`
- `src/gpm/qa/certification.py`
- `src/gpm/qa/start_date.py`
- `src/gpm/runtime/compiler.py`
- `src/gpm/runtime/loader.py`
- `src/gpm/schemas.py`
- `tasks/history.md`
- `tasks/m25c-compositional-territorial-status-ship-manifest.md`
- `tasks/roadmap.md`
- `tasks/todo.md`
- `tests/test_compositional_territorial_status.py`
- `tests/test_historical_certification_contract.py`
- `tests/test_m25c_global_certification.py`
- `tests/test_source_manifest_schema.py`

## Per-file purpose

- Root and feature documentation describe the compositional model, compatibility
  boundary, completed milestone slice, and next research gate.
- The 22 regional packet JSON files and their README carry the migrated actor
  profiles, facets, relationships, nullable primary actors, and removal census.
- The five schemas define canonical `0.2.0`, assignment/gazetteer `0.4.0`,
  runtime `2.0.0`, and ordered overlay contracts.
- The migration and provisional-pass scripts make the worldwide transformation
  deterministic and preserve it during regenerated assembly.
- Historical, schema, CLI, atlas, QA, compiler, and loader modules implement
  resolution, validation, export, runtime encoding, v1 compatibility, and
  canonical/runtime parity.
- The four test files cover schema discovery, validation, all-packet census,
  overlay ordering, neutral atlas behavior, and runtime round trips.
- Task history, roadmap, todo, and this manifest record completion, evidence,
  residual risk, and the next decision-gated task.

## User-goal mapping

Every changed executable and data file is required either to represent the
worldwide compositional status contract or to preserve it through validation,
runtime compilation/loading, and atlas projection. Documentation and task files
state the same boundary without claiming assertion cleanup or certification.

## Tests run

- `.venv/bin/pytest -q tests/test_m24_start_date_framework.py tests/test_compositional_territorial_status.py tests/test_m25c_global_certification.py tests/test_historical_certification_contract.py tests/test_source_manifest_schema.py` — 86 passed.
- `.venv/bin/pytest -q` — 395 passed in 18.09 seconds with no warnings.
- Clean-room `scripts/migrate-territorial-status-packets.py` run over copied
  packet JSON — reproduced all 22 JSON files exactly; census was 22,000
  assignments and 219 removed pseudo-owner rows.
- `git diff --check` — passed.
- Gitleaks scan of the pending diff — no leaks found.

## Skipped tests

- Browser/visual review was skipped because no rendered UI artifact changed;
  atlas behavior is exercised through component-feature and dissolve tests.
- Global runtime performance and certification gates remain intentionally
  deferred until M25C assertion evidence and independent review are complete;
  this change does not claim certification or publication readiness.
- Task-doc audit was skipped because `scripts/audit-task-docs.mjs` is absent.

## Adversarial review

A failure-oriented changed-file review inspected overlay ordering, nullable
actors, schema transitions, runtime v1/v2 decoding, facet parity, generated
packet reproducibility, and QA reference checks. It found that typed-polity
validation was keyed to the pass-manifest version rather than assignment schema
`0.4.0`; `src/gpm/qa/start_date.py` now keys the check to assignment schema and
keeps null primary actors out of unknown-reference checks. Targeted and full
tests pass after the correction.

Gitleaks' all-history scan reported `generic-api-key` at
`artifacts/m25c-anomaly-alignment-slides.html:491` in commit `b44a0af`. Redacted
inspection proved the match is a `STORAGE_KEY` constant used only with browser
`localStorage.getItem` and `localStorage.setItem`; it is an accepted historical
false positive, not a credential and not part of this diff.

## Residual risk

The compositional data was migrated by conservative actor-name classification,
so status-derived positive-border and negative-anachronism assertions may no
longer describe the corrected outlines. Certification and publication remain
fail-closed, and `tasks/todo.md` requires region-by-region evidence review
before remediation. Runtime performance at worldwide certified scale is also
unclaimed until that later gate.

## Rollback note

Revert the shipping commit to restore canonical/runtime v1 and the prior packet
model. Do not partially revert only schemas or generated packets because their
versions and runtime encodings form one compatibility boundary.

## Next command

`$exec` to re-research the affected Americas/Africa positive-border and
negative-anachronism assertions and present exact recommendations without
remediation.
