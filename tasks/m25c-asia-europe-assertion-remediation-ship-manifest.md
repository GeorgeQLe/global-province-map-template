# M25C Asia/Europe assertion remediation ship manifest

## User goal

Implement the approved four-part assertion bundle for regions `030`, `034`,
`035`, `039`, `143`, and `145` without changing certification, signing,
publication, or runtime state, and leave Oceania research as the next
decision-gated task.

## Implementation outcome

- Extended the shared Natural Earth control generator from nine to fifteen
  exact country pairs using the pinned Admin-0 5.1.1 archive, fixed `75 km`
  corridor, and `0.20` tolerance.
- Added data-driven retirement metadata and removed six circular positive
  assertions, six boundary features/assets, and the assertion-only polity-mask
  assets for `039` and `145`, including coverage and derived-source references.
- Routed all six regional generators through the shared helper. Each packet
  preserves its net assertion count, adds one source, and now has exactly one
  derived negative-control asset.
- Made zero-transition seam assertions non-executable and fail closed with a
  null measurement and dedicated diagnostic, without changing schema or wire
  versions.
- Cleared two invalid region-`034` capital references during deterministic
  regeneration so the committed packet remains schema-valid.

## Changed files and per-file purpose

- `scripts/m25c_negative_controls.py`: generalize legacy-assertion retirement
  and define the six new pinned seam controls.
- `scripts/generate-m25c-region-{015,030,034,035,039,143,145}-packet.py`: route
  affected packet generation through the shared helper; region `034` also
  removes two capital references that no longer resolve after regeneration.
- `src/gpm/qa/start_date.py`: fail seam assertions closed when no compositional
  transition is executable.
- `tests/test_m25c_modern_seam_controls.py` and
  `tests/test_m25c_global_certification.py`: cover the 15-control inventory,
  retirement lineage, checksums, determinism, and zero-transition failure.
- `research/start-dates/1444-global-v1/regional-packets/{030,034,035,039,143,145}-*.json`
  and their `assets/*`: regenerate the six packets, add one pinned
  `negative-controls.geojson` each, and remove six obsolete boundary plus two
  assertion-only polity-mask assets.
- `research/start-dates/1444-global-v1/regional-packets/README.md`: document the
  new controls, retired circular assertions, and current failure inventory.
- `ROADMAP.md`, `tasks/roadmap.md`, `tasks/todo.md`, and `tasks/history.md`:
  record completion and route the next decision-gated Oceania research task.
- `tasks/m25c-asia-europe-assertion-reresearch.md`: record reviewer approval and
  the implemented measurements.
- This manifest: record the exact shipping boundary and quality evidence.

## User-goal mapping

- The shared helper, six generators, regenerated packets, and retired assets
  implement the approved assertion bundle exactly.
- The QA change and regression tests enforce the requested fail-closed
  zero-transition behavior without weakening certification.
- Roadmap, todo, research, history, and packet documentation preserve the
  decision boundary and make Oceania research the next executable task.

## Verification

- Focused seam and global-certification tests cover all 15 deterministic,
  nonempty, line-valued controls and their packet/checksum identity, the exact
  retired inventory, real nonmatching passes, invalid references, and the
  synthetic zero-transition failure.
- Focused schema, seam, certification, and packet-signing verification passed
  87 tests; the complete repository suite passed 405 tests.
- The six generators reproduce packet and GeoJSON bytes deterministically from
  the accepted clean baseline.
- Fresh worldwide provisional QA reports 13 spatial seam failures, 13
  downstream uncertified Grade-A errors, and one dedicated non-executable error.
  The prior controls retain seven failures and the `021`/`029` passes. New
  measurements are `0.8388803144`, `0.7985413935`, three `1.0` results, and a
  null/zero-transition `039` result.
- The remaining inventories are exactly four missing Oceania negatives and 19
  missing positives. No guard was waived and no pack was certified, signed,
  published, or deployed.
- Python compilation, the sdist/wheel package build, and `git diff --check`
  completed successfully.

### Tests run

- Executable: `.venv/bin/python -m pytest -q` — `405 passed in 56.41s`.
- Executable: `.venv/bin/python -m compileall -q src scripts tests` — passed.
- Executable/package: `uv build` — sdist and wheel built successfully.
- Documentation/repository: `git diff --check` — passed.
- Security hygiene: the shipping diff passed a targeted credential/private-key
  pattern scan.

### Skipped tests

- No dedicated lint or static-type command is configured in `pyproject.toml`,
  and the repository has no `CLAUDE.md`, Makefile, Justfile, Ruff, or mypy
  contract, so no additional lint/typecheck command was applicable.
- Generator byte-for-byte regeneration was not repeated during final wrap-up:
  the manifest records the already completed clean-baseline reproduction, and
  the full suite independently rechecks committed packet/checksum identity.
- Fresh worldwide QA was not repeated during final wrap-up because its known
  13 fail-closed seam findings are the intended research blockers, not test
  regressions; the recorded measurements and inventory are unchanged.

### Adversarial review

The final diff was reviewed by risk surface: shared retirement metadata and
asset deletion counts, generator routing, null-measurement behavior, exact
packet/source/assertion counts, checksum pinning, task-state accuracy, and
secret patterns. The full suite then exercised unrelated repository behavior
as well as the focused seam and certification regressions. No unaddressed
shipping finding or warning remains.

## Residual risk

The controls intentionally expose unresolved historical reconstruction rather
than certify it: 13 seam failures and 19 missing independently georeferenced
positive borders remain. Southern Europe still has no executable compositional
transition. These are fail-closed M25C research blockers; no runtime,
publication, signing, or deployment state changes in this boundary.

## Residual blockers and next work

Thirteen seam failures and 19 missing positive borders continue to block M25C
certification. Southern Europe's compositional status reconstruction remains
non-executable. The next task is read-only assertion research for Oceania
regions `053`, `054`, `057`, and `061`; remediation remains reviewer-gated.

## Rollback note

Revert this remediation commit to restore the six circular packet assertions
and eight obsolete assets and remove the six new negative controls. No external
publication or deployment state requires rollback.

## Next command

`$exec` to research missing assertions for Oceania regions `053`, `054`, `057`,
and `061`; do not remediate until the reviewer records a decision.
