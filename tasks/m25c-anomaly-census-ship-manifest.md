# M25C Negative-Cell Evidence Audit Ship Manifest

## User goal

Audit all 233 negative region/class cells without reopening the locked
geographic treatments; strengthen fail-closed closure validation; refreeze the
242-cell census only after zero unresolved findings; record George Le's
approval; and ship the complete session boundary.

## Changed files

- `.agents/project.json`
- `docs/m25c-anomaly-alignment-decisions.md`
- `research/start-dates/1444-global-v1/README.md`
- `research/start-dates/1444-global-v1/census-research.json`
- `research/start-dates/1444-global-v1/source-access-audit.json`
- `schemas/start-date-pass-manifest.schema.json`
- `schemas/start-date-source-manifest.schema.json`
- `scripts/build-m25c-global-pass.py`
- `scripts/generate-m25c-anomaly-census.py`
- `scripts/verify-m25c-anomaly-census.py`
- `src/gpm/qa/m25c_census.py`
- `src/gpm/qa/start_date.py`
- `src/gpm/schemas.py`
- `tasks/history.md`
- `tasks/lessons.md`
- `tasks/m25c-anomaly-census-ship-manifest.md`
- `tasks/roadmap.md`
- `tasks/todo.md`
- `tests/test_m25c_anomaly_inventory.py`
- `tests/test_m25c_global_certification.py`
- `tests/test_m25c_packet_signing.py`

The generated packet and `review_acceptance.json` live under ignored
`data/processed/`; the sidecar records George Le's local approval dated
2026-08-14 and is intentionally not part of the Git commit.

## Per-file purpose

- `.agents/project.json` records the installed guided-walkthrough pack used for
  manual browser fallbacks.
- `docs/m25c-anomaly-alignment-decisions.md` preserves the locked, engine-neutral
  treatments that the negative audit did not reopen.
- The research README explains the tracked inputs, exact review matrix,
  acceptance sidecar, live-access evidence, and downstream boundary.
- `census-research.json` is the authoritative 22×11 research ledger: ten
  anomalies in nine positive cells, 233 confirmed negatives, explicit failure
  bases, exact locators, and matching rejected leads.
- `source-access-audit.json` records live automated or browser-confirmed access
  for all 45 source URLs.
- The two schemas require the review ledger in schema-0.3 passes and admit
  archival/institutional evidence types.
- The builder requires a valid frozen acceptance sidecar before importing the
  anomaly inventory and carries the review ledger through handoff validation.
- The generator projects tracked research deterministically, validates closure
  before writing, emits the source-access audit, and refuses signed-output
  regeneration.
- The verifier checks hashes, schemas, census/rejection/access ledgers, source
  and gazetteer validity, joint handoff, pending state, and accepted sidecars.
- `m25c_census.py` centralizes region/class/source/locator/query/lead,
  provenance, access, rejection-parity, unresolved-cell, and acceptance rules.
- `start_date.py` and `schemas.py` integrate the ledger and expanded source
  provenance into normal schema-0.3 QA.
- Task/history/roadmap/lessons files record completion, approval, the corrected
  review boundary, residual blockers, and the next executable work.
- The three M25C test modules cover the audit contract, signing immutability,
  downstream overlays, schema integration, and certification boundaries.

## User-goal mapping

The tracked research now gives every negative cell a named lead, controlled
failure basis, targeted historical query, exact source locator, and unique
conclusion. Closure requires exact rejection parity, reachable sources, no
unresolved cells, and two independent provenance groups for positives. The ten
locked geographic anomalies and non-geographic Lancastrian relationship remain
unchanged except that inaccessible Britannica Avignon corroboration was
replaced by UNESCO evidence. George Le's approval was recorded only after the
audit produced no decision exceptions.

## Tests run

- Executable focused verification:
  `.venv/bin/pytest -q tests/test_m25c_anomaly_inventory.py tests/test_m25c_packet_signing.py tests/test_m25c_global_certification.py`
  — 52 passed with no warnings.
- Executable complete suite: `.venv/bin/pytest -q` — 356 passed in 109.04
  seconds with no warnings.
- Executable packet verification: pending verification passed before signing;
  accepted verification passed afterward with 242 cells, ten anomalies, zero
  joint findings, `human_review_complete: true`, and
  `public_release_allowed: false`.
- Reproducibility: two independently generated temporary packet directories
  were byte-identical; final frozen SHA256SUMS digest is
  `42367f817076b764b9508ac5750f372146da97d1889296088d492e17953b9ff9`.
- Source/gazetteer and joint-handoff validation passed through the packet
  verifier. All 45 live-access records are resolved.
- Source hygiene: `git diff --check` passed.

## Skipped tests

- No separate lint, typecheck, or build command is declared by `pyproject.toml`;
  the complete Python suite and packet executables cover the changed code.
- The full worldwide M25C pass was not assembled because remaining worldwide
  evidence and later pass-level inputs are outside this census-audit boundary.
- No deployment was run because the repository has no `deploy.md` or
  `tasks/deploy.md` manual deploy contract.

## Adversarial review

An explicit equivalent adversarial sweep inspected the exact diff and tested
missing/duplicate cells, generic or temporally unbounded searches, templated
negative closure, empty or invalid failure bases, unknown/unreviewed/temporally
invalid sources, missing or mismatched locators, reused generic surveys,
rejection-log drift, unresolved URL access, insufficient positive provenance,
invalid reviewer identities/dates, duplicate signatures, stale signatures,
tampered frozen bytes, and downstream inventory use without acceptance.

The sweep also checked that no alignment decision was silently reopened, the
Lancastrian dispositions are cell-specific, generated packet status remains
non-public, and signing changes only the excluded sidecar. No unresolved
finding or warning remains.

Correction enforcement: `tasks/lessons.md` records that locked decisions must
not be presented as awaiting another review. `tasks/todo.md` and
`tasks/roadmap.md` now route directly from completed census acceptance to
worldwide pass assembly.

## Residual risk

- Remote historical pages are URL- and locator-pinned but not content-
  checksummed; the tracked live-access audit records availability, not immutable
  source content.
- The approval sidecar and frozen packet are intentional ignored build
  artifacts. A clean clone must regenerate the packet and recreate or securely
  transfer the signed sidecar before the downstream inventory stage.
- Remaining worldwide evidence, real-pass assembly, pass-level review, runtime
  certification, and release approval are still outstanding. No public release
  was authorized.

## Rollback note

Revert the session shipping commit to remove the tracked research, validation,
schema, test, and documentation changes. The ignored packet can be regenerated;
remove its local acceptance sidecar only if intentionally revoking the recorded
local approval. No database, deployment, or irreversible migration is involved.

## Next command

```sh
.venv/bin/python scripts/build-m25c-global-pass.py inventory \
  --inventory-input data/processed/m25c-global-staging/evidence/anomaly_inventory.json \
  --acceptance-input data/processed/m25c-global-staging/evidence/review_acceptance.json
```
