# M25C Oceania assertion remediation ship manifest

## User goal

Implement the approved negative assertions for Oceania regions `053`, `054`,
`057`, and `061`, verify their spatial and source-pinning gates, and preserve
all certification and publication boundaries.

## Implementation outcome

- Extended the shared Natural Earth control helper from 15 Admin-0 controls to
  a 19-control inventory that also supports the pinned Admin-1 `5.1.1` archive.
- Added exact WA-SA, Central-NCD, Yaren-Meneng, and American Samoa
  Western-Eastern district seam records and one checksum-pinned GeoJSON asset
  to each Oceania packet.
- Routed all four Oceania generators through the shared helper and preserved
  the fixed `75 km` corridor, `0.20` tolerance, and fail-closed zero-transition
  behavior.
- Hardened shared-source cleanup so retired generated-edge artifacts cannot be
  reintroduced through an inherited canonical source record.

## Changed files and purpose

- `scripts/m25c_negative_controls.py`: support exact Admin-0/Admin-1 control
  metadata, checksums, extraction fields, citations, and lineage cleanup.
- `scripts/generate-m25c-region-{053,054,057,061}-packet.py`: apply the shared
  control during deterministic packet generation.
- Four Oceania packet JSON files and `assets/{053,054,057,061}/negative-controls.geojson`:
  add source-pinned executable evidence.
- `tests/test_m25c_modern_seam_controls.py` and
  `tests/test_m25c_global_certification.py`: enforce the 19-control inventory,
  exact Admin-1 units/checksum/assets, one negative per affected region, and
  retired-lineage absence.
- Packet README, roadmaps, todo, history, and research record: document approval,
  implementation, measured blockers, and the next decision-gated task.
- This manifest: record verification and residual risk.

## User-goal mapping

The four packet sources, assertions, boundary features, and assets implement
the exact reviewer-approved Admin-1 unit pairs. Shared helper and generator
changes make the records reproducible and checksum-pinned; focused tests enforce
their geometry and inventory. Task and roadmap updates preserve the requested
decision boundary and accurately route the next work. No unrelated assignment,
status, tolerance, schema, runtime, certification, or publication change is
included.

## Tests run

- Executable focused seam and certification suite: `58 passed in 24.83s`.
- Executable complete repository suite: `406 passed in 46.17s`.
- Executable Python compilation: `python -m compileall -q src scripts tests`
  passed without output or warnings.
- Executable fresh worldwide provisional assembly: 701 assertions; 16 intended spatial
  failures, 16 downstream uncertified-Grade-A findings, and three
  non-executable findings. Total expected error count: 35.
- Exact Oceania outcomes: `053` `1.0` / 16 transitions; `054` `0.0` / seven;
  `057` and `061` null / zero transitions.
- All four derived assets match their packet SHA-256 declarations and the
  deterministic shared boundaries extracted from the pinned archive.
- Documentation/repository check: `git diff --check` passed.

## Skipped tests

- No separate lint or static-type command is configured in the repository
  contract files. The complete pytest suite and Python bytecode compilation
  cover the available executable validation surfaces.
- Package build was not repeated because no packaging metadata, dependency,
  installed-package surface, or bundled Python module changed; the modified
  scripts and data are exercised directly by the focused and complete suites.

## Adversarial review

The review enumerated alternative internal Admin-1 seams, rejected empty and
external-region controls, verified fixed-before-measurement provenance, and
recomputed each proposed result against a fresh worldwide assembly. During
regeneration it detected a retired Southern Europe derived-artifact reference
in an inherited scratch-baseline source record. The shared helper now strips
the complete retired-artifact inventory, and a repository-wide regression test
prevents recurrence. The final diff, generated checksums, task state, and
credential/private-key patterns were reviewed before staging.

## Residual risk

Sixteen seam failures and 19 missing independently georeferenced positive
borders continue to block certification. The Micronesia and Polynesia controls
remain non-executable because their current canonical models have no
land-adjacent status transition. No release, signature, runtime, certification,
publication, or deployment state changed.

## Rollback note

Revert this implementation to remove the four sources, assertions, boundary
features, assets, generator routing, tests, and documentation updates. No
external publication or deployment requires rollback.

## Next command

Research the fail-closed transition from provisional generation to a promotable
assembled-pass mode, as item 12 in `tasks/todo.md`; do not implement that
transition before reviewer approval.
