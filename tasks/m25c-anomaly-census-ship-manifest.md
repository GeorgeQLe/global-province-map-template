# M25C Anomaly Census Ship Manifest

## User goal

Ship the current M25C worldwide anomaly-census work cleanly to the default
branch, preserving the independent-review and non-release boundary.

## Changed files

- `research/start-dates/1444-global-v1/README.md`
- `research/start-dates/1444-global-v1/m25c_rejection_report.json`
- `research/start-dates/1444-global-v1/provenance/1444-v2-seed.json`
- `scripts/build-m25c-global-pass.py`
- `scripts/generate-m25c-anomaly-census.py`
- `scripts/verify-m25c-anomaly-census.py`
- `src/gpm/qa/start_date.py`
- `tests/fixtures/m25c/placeholder-anomaly-inventory.json`
- `tests/test_m25c_anomaly_inventory.py`
- `tests/test_m25c_global_certification.py`
- `tasks/todo.md`
- `tasks/roadmap.md`
- `tasks/history.md`
- `tasks/m25c-anomaly-census-ship-manifest.md`

## Per-file purpose

- `research/start-dates/1444-global-v1/README.md` documents the closed census,
  source-link, reviewer-separation, and canonical handoff requirements.
- `m25c_rejection_report.json` records the placeholder seed's new fail-closed
  census rejection instead of claiming that example class rows are sufficient.
- `provenance/1444-v2-seed.json` pins the ignored build geometry and location
  sidecar required by the accepted pilot handoff.
- `scripts/build-m25c-global-pass.py` canonicalizes census input and aggregates
  inventory/evidence defects before copying or assembly.
- `scripts/generate-m25c-anomaly-census.py` reproducibly creates the ignored,
  frozen pre-review research packet and its evidence ledger.
- `scripts/verify-m25c-anomaly-census.py` checks the packet schemas, links,
  expected pending-review finding, hashes, and byte-deterministic builds.
- `src/gpm/qa/start_date.py` validates all 242 region/class cells, anomaly links,
  reviewer identity, survey citations, and global source references.
- `tests/fixtures/m25c/placeholder-anomaly-inventory.json` preserves the old
  incomplete seed solely as a negative regression fixture.
- `tests/test_m25c_anomaly_inventory.py` exercises closed-census structure,
  link integrity, handoff evidence, rejection rules, and determinism.
- `tests/test_m25c_global_certification.py` uses the negative fixture while
  retaining the existing global certification boundary coverage.
- `tasks/todo.md`, `tasks/roadmap.md`, and `tasks/history.md` reconcile active,
  milestone, and session state without claiming human acceptance.
- This manifest records the exact shipping boundary and quality gate.

## User-goal mapping

The implementation turns the M25C anomaly requirement into a reproducible,
closed worldwide research census and supplies an auditable candidate packet.
Its validation and documentation prevent the generated research from being
mistaken for independently accepted evidence or a certifiable public pass.

## Tests run

- Executable verification: `uv run pytest -q` — 340 passed in 20.32 seconds,
  with no warnings.
- Executable packet verification:
  `uv run python scripts/verify-m25c-anomaly-census.py` — source and gazetteer
  schemas passed, joint findings were empty, and reordered canonical builds
  were byte-identical with SHA-256
  `bd10792df93c93a86a7cb752d9fd665518bab456a1851a11ee074c3c59503e01`.
- Source hygiene: `git diff --check` — passed.
- Security hygiene: changed-file credential-pattern scan — no matches.

## Skipped tests

- The real combined M25C pass build was not run because independent human
  census review, the accepted worldwide fabric handoff, and the remaining
  worldwide assignment/status evidence do not yet exist as accepted inputs.
  The builder remains fail closed until those inputs are supplied.
- No browser or deployment check is relevant: this boundary changes research
  tooling and ignored pre-review artifacts, not a UI or hosted release, and the
  repository has no explicit manual deploy contract.

## Adversarial review

Reviewed the exact diff for ways to substitute examples for a census, omit or
duplicate region/class cells, orphan cases, cross-link the wrong class/region,
reuse the researcher as reviewer, cite missing or unreviewed evidence, depend
on a single provenance group, reference missing polities, disagree across the
two inventory copies, or gain order-dependent bytes. Each path is rejected or
covered by focused tests. The only persisted verifier finding is the deliberate
missing human review date; the candidate status remains non-public.

## Residual risk

The research conclusions and negative cells have not received independent
human historical review. Remote sources are URL-pinned rather than content-
checksummed, and the full geometry/politics assembly has not consumed this
packet. These limitations are explicit blockers, not accepted release risk.

## Rollback note

Revert the anomaly-census shipping commit. Generated research data is ignored
and can be regenerated; no database, hosted artifact, deployment, or migration
is involved.

## Next command

Human review of the frozen packet is required before another executable M25C
assembly command is appropriate.
