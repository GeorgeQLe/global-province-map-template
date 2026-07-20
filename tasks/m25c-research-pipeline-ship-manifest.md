# M25C Research Pipeline Ship Manifest

## User goal

Ship the completed M25C worldwide research assembly workflow cleanly to the
default branch, with task state, validation, and residual risk recorded.

## Changed files

- `research/start-dates/1444-global-v1/README.md`
- `schemas/start-date-pass-manifest.schema.json`
- `scripts/build-m25c-global-pass.py`
- `src/gpm/cli.py`
- `src/gpm/qa/render.py`
- `src/gpm/qa/start_date.py`
- `src/gpm/schemas.py`
- `tests/test_m25c_global_certification.py`
- `tasks/todo.md`
- `tasks/roadmap.md`
- `tasks/history.md`
- `tasks/m25c-research-pipeline-ship-manifest.md`

## Per-file purpose

- `research/start-dates/1444-global-v1/README.md`: documents the input-driven
  research and independent-review workflow and its non-release boundary.
- `schemas/start-date-pass-manifest.schema.json`: permits schema-0.3 manifests
  to encode the pending independent-review state.
- `scripts/build-m25c-global-pass.py`: implements deterministic inventory,
  fabric, evidence, split, aggregation, assembly, render, preflight, and human
  acceptance stages while excluding runtime and certification stages.
- `src/gpm/cli.py`: exposes pending-review start-date preflight.
- `src/gpm/qa/render.py`: makes anomaly sheets independently reviewable by
  including their subject and source IDs.
- `src/gpm/qa/start_date.py`: enforces complete anomaly classes, reviewed global
  references, exact worldwide province count, and review-only preflight.
- `src/gpm/schemas.py`: validates the schema-0.3 pending-review state without
  allowing it in earlier schemas.
- `tests/test_m25c_global_certification.py`: covers pending-review schema and
  deterministic M49 enrichment behavior.
- `tasks/todo.md`, `tasks/roadmap.md`, and `tasks/history.md`: reconcile current,
  milestone, and session state.
- `tasks/m25c-research-pipeline-ship-manifest.md`: records this exact shipping
  boundary and quality gate.

## User-goal mapping

The implementation supplies the reproducible research workflow required before
M25C certification. The documentation and task records prevent that workflow
from being mistaken for completed worldwide research or an accepted public
release. The tests and QA gates keep pending review separate from acceptance.

## Tests run

- Executable verification: `uv run pytest` — 312 passed in 73.49 seconds, with
  no warnings.
- Source hygiene: `git diff --check` — passed.
- Security hygiene: changed-file credential-pattern scan — no matches.

## Skipped tests

- The real end-to-end worldwide research build was not run because this session
  did not include the reviewed anomaly inventory, schema-0.3 evidence bundle,
  accepted M23 fabric sidecars, or independent human review. Synthetic and
  contract tests exercise the executable workflow without inventing those
  research inputs.
- No deploy test is relevant: the repository has no explicit manual deploy
  contract, and this change intentionally produces no public release artifact.

## Adversarial review

Reviewed the shipping diff against the fail-closed boundary. Pending-review
mode downgrades only the independent-review finding for schema 0.3 preflight;
artifact checksum, coverage, source-review, exact-count, and all other errors
remain blocking. Acceptance rejects generator identities, changed review
renders, incomplete region/anomaly sheets, and any ordinary QA failure. The
builder exposes no runtime compilation, certification, demo promotion, or
public-release stage.

## Residual risk

Natural Earth enrichment and the full 22,000-province workflow have not been
executed against the eventual real curator inputs in this session. Input-shape
or performance issues may surface during that build. All such failures remain
pre-release and fail closed; M25C stays active until the real pass is reviewed.

## Rollback note

Revert the M25C research-pipeline shipping commit. The previous pending lineage
and certification boundary remain recoverable from its parent commit; no
database, hosted artifact, or deployment migration is involved.

## Next command

`$exec`
