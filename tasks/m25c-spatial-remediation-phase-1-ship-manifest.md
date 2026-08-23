# M25C spatial-remediation phase 1 ship manifest

Date: `2026-08-23`
Status: **implementation complete; candidate remains blocked**

## User goal

Implement the approved first spatial-remediation phase from task 15, regenerate
twice, render, run ordinary worldwide QA, preserve every fail-closed boundary,
and ship the session.

## Changed files and per-file purpose

- `src/gpm/qa/start_date.py`: eligible covered-zero seam execution,
  deterministic both-side diagnostics, and fail-closed border-applicability
  qualification restricted to passing positive capital/site anchors.
- `schemas/start-date-qa-report.schema.json`: permits the new seam diagnostics.
- `schemas/positive-border-applicability.schema.json`: defines revision-,
  inventory-, source-, anchor-, and review-bound applicability records.
- `schemas/start-date-pass-manifest.schema.json`: permits the applicability
  artifact in an assembled manifest.
- `src/gpm/schemas.py`: validates the new schema and exact source coverage.
- `src/gpm/qa/m25c_assembled.py`: makes the artifact part of assembled closure.
- `scripts/build-m25c-global-pass.py`: validates and stages the artifact.
- `scripts/generate-m25c-provisional-pass.py`: deterministically generates the
  five pending applicability candidates and pins them in the pass manifest.
- `scripts/generate-m25c-region-039-packet.py`: reconstructs the exact
  nine-record Italy-Slovenia corridor and removes the circular candidate-edge
  Portugal-Castile border.
- `src/gpm/historical/packet_migration.py`: preserves only explicitly marked
  reviewed compositional records during migration.
- `scripts/m25c_negative_controls.py`: removes the obsolete region-039 border
  retirement entry after its generator was corrected directly.
- `src/gpm/geo/shapefile.py`: adds PolyLine support used for official CAOP
  source inspection.
- `research/start-dates/1444-global-v1/regional-packets/039-southern-europe-2026-08-15.json`:
  regenerated exact regional packet.
- `research/start-dates/1444-global-v1/phase1-candidates/`: checksum-pinned,
  unpromoted CAOP segment and provenance/promotion-decision record.
- `tests/test_m25c_modern_seam_controls.py`: covered-zero, unknown/uncovered,
  exact corridor, and applicability tamper/review regression tests.
- `tests/test_m25c_assembled_transition.py`: assembled fixture closure.
- `tests/test_source_manifest_schema.py`: exact schema inventory update.
- `README.md`, `tasks/todo.md`, `tasks/roadmap.md`, `tasks/history.md`, and
  `tasks/m25c-spatial-remediation-phase-1.md`: current status, evidence outcome,
  exact QA inventory, and next gate.

## User-goal mapping

- Amended covered-zero contract: QA implementation, report schema, and seam
  regression fixtures.
- Corridor-first Southern Europe: exactly nine enumerated packet records and a
  regression assertion that no other record is reconstructed.
- Independently derived Portugal-Castile segment: official CAOP candidate and
  provenance manifest; promotion remains false because its conditions fail.
- Five applicability candidates: generated artifact, schema, assembly binding,
  dedicated QA findings, and tamper/pending-review coverage.
- Raichur research: documented no-promotion outcome because no independent
  exact spatial corroboration passed.
- Regeneration/render/QA: duplicate byte-identical trees, 30 sheets, and the
  exact remaining ordinary-QA inventory.

## Tests run

- `.venv/bin/pytest -q`: complete repository suite passed after final review.
- Focused final gate:
  `.venv/bin/pytest -q tests/test_m25c_modern_seam_controls.py tests/test_m25c_assembled_transition.py tests/test_source_manifest_schema.py`
  passed `31` tests.
- Two complete assembled generations compared with `diff -qr`: no difference.
- `scripts/build-m25c-global-pass.py render`: rendered `30` sheets.
- `scripts/build-m25c-global-pass.py preflight`: expected fail with `58`
  non-review errors and `1` pending-review warning.
- `git diff --check` and JSON parsing over changed schemas/candidates: passed.

## Skipped tests

- No separate lint, typecheck, or build command is configured in
  `pyproject.toml`; the complete pytest suite, deterministic assembly, render,
  schema parsing, and ordinary QA cover the available executable gates.
- No deploy test is applicable because the repository has no `deploy.md` or
  `tasks/deploy.md` manual deploy contract.

## Adversarial review

An explicit diff review checked fail-open paths, hash tampering, anchor
substitution, partial seam coverage, unknown facets, circular candidate-edge
geometry, and accidental broad Southern Europe restoration. It found that the
applicability qualifier initially accepted any positive geometry assertion as
an anchor. The qualifier now requires a positive `capital` assertion, and a
regression test proves that post-review record tampering fails qualification.
No unresolved adversarial finding remains.

## Residual risk

Ordinary QA intentionally remains red: five unreviewed applicability records,
19 missing positive borders, eight non-executable seams, 13 failed spatial
assertions, 13 downstream uncertified Grade-A findings, and one expected
pending-independent-review warning. The stricter evaluator exposes partial
coverage that the prior evaluator measured incompletely. All candidate
permissions remain false. Portugal-Castile, Raichur, and every task-16 corridor
remain separate evidence/review gates.

## Rollback note

The pre-change eligible `039` affected-component set was empty. Reverting this
commit and regenerating the packet/pass restores the prior 54-error evaluator
behavior. No release, review acceptance, certification, publication, or
deployment state changed.

## Next command

`$exec` for task 16 only after a specific remaining corridor or positive-border
evidence packet receives its required separate approval.
