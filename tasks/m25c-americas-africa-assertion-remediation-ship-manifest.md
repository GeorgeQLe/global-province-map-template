# M25C Americas/Africa assertion remediation ship manifest

## User goal

Implement the approved Americas/Africa assertion remediation only: retire the
circular Northern Africa Marinid-Zayyanid border, add nine pinned Natural Earth
modern inland-seam negative controls, preserve every positive-border and failed
seam gate, and repair worldwide generator ordering without certifying or
publishing a runtime pack.

## Changed files

- Contracts and QA: `schemas/historical-boundary-registry.schema.json`,
  `schemas/spatial-golden-borders.schema.json`,
  `schemas/start-date-qa-report.schema.json`, `src/gpm/schemas.py`, and
  `src/gpm/qa/start_date.py`.
- Shared generation: `scripts/m25c_negative_controls.py`,
  `src/gpm/historical/packet_migration.py`, and
  `scripts/generate-m25c-provisional-pass.py`.
- Regional generators: `scripts/generate-m25c-region-005-packet.py`,
  `scripts/generate-m25c-region-011-packet.py`,
  `scripts/generate-m25c-region-013-packet.py`,
  `scripts/generate-m25c-region-014-packet.py`,
  `scripts/generate-m25c-region-015-packet.py`,
  `scripts/generate-m25c-region-017-packet.py`,
  `scripts/generate-m25c-region-018-packet.py`,
  `scripts/generate-m25c-region-021-packet.py`, and
  `scripts/generate-m25c-region-029-packet.py`.
- Packet definitions: the nine region packet JSON files for `005`, `011`,
  `013`, `014`, `015`, `017`, `018`, `021`, and `029`, plus
  `research/start-dates/1444-global-v1/regional-packets/README.md`.
- Packet assets: nine new `assets/<region>/negative-controls.geojson` files;
  deleted `assets/015/boundaries.geojson` and
  `assets/015/polity-masks.geojson`.
- Tests: `tests/test_m25c_modern_seam_controls.py` and
  `tests/test_m25c_global_certification.py`.
- Research and project records: `docs/m24-start-date-research-framework.md`,
  `tasks/m25c-americas-africa-assertion-reresearch.md`,
  `tasks/m25c-region-015-ship-manifest.md`, `tasks/todo.md`,
  `tasks/roadmap.md`, `tasks/history.md`, and this manifest.

## Per-file purpose

- The schema and QA files define the `0.3.0`-only seam relation, constrain
  nullable modern-control sides, calculate compositional seam coincidence, and
  expose deterministic diagnostics.
- The shared and regional generators extract checksum-pinned Natural Earth
  seams, migrate packets consistently, retire region `015`'s circular assets,
  and validate/clean legacy scaffold references before applying packets.
- The packet JSON and GeoJSON files carry the nine independently reproducible
  region controls and remove the obsolete Northern Africa frontier lineage.
- The tests exercise schema restrictions, synthetic seam behavior, all nine
  Natural Earth pairs and hashes, inventory invariants, and generator ordering.
- The docs record the approved research decision, exact QA outcome, remaining
  blockers, and next decision-gated work.

## User-goal mapping

- Circular assertion retired: `region-015-border-marinid-zayyanid`, its
  boundary feature, its two derived files, and source artifact references are
  absent; actors and assignments are unchanged.
- Nine controls added: each affected region has exactly one line-valued,
  region-subject, 75 km / 0.20 seam assertion and one checksum-pinned modern
  control asset from Natural Earth Admin-0 5.1.1.
- Fail-closed behavior preserved: `021` and `029` pass; `005`, `011`, `013`,
  `014`, `015`, `017`, and `018` fail with component inventories. No tolerance,
  status assignment, coverage grade, runtime, signing, certification, or
  publication change was made.
- Worldwide ordering repaired: legacy reference counts and provisional
  references are validated and cleaned before migrated regional packets are
  applied.

## Tests run

Executable verification:

- Focused schema, seam, packet, compositional-status, and worldwide tests:
  `68 passed`.
- Complete test suite: `403 passed in 42.56s`.
- Package build: `uv build` completed successfully and produced sdist/wheel
  artifacts in the ignored build output.
- Compilation: Python `compileall` completed successfully.
- Determinism: all nine regional generators and their GeoJSON assets were
  regenerated twice and compared byte-for-byte.
- Worldwide provisional QA: ran without weakening
  `SPATIAL_ASSERTION_FAILED`; it intentionally retained the seven seam failures
  and their seven downstream uncertified Grade-A findings. Its five warnings
  are also accepted provisional-state guards: incomplete anomaly review,
  incomplete review coverage, invalid independent review, the ten-region
  missing-negative inventory, and the thirteen-region missing-positive
  inventory.
- Repository hygiene: `git diff --check` passed.

Documentation/task verification:

- Inspected `tasks/todo.md`, `tasks/roadmap.md`, and `tasks/history.md` for
  matching completion state and next-work routing.
- No `scripts/audit-task-docs.mjs` exists, so no task-doc audit command applies.

## Skipped tests

- No separate lint or static type-check command is configured in
  `pyproject.toml`, a Makefile, Justfile, or package script; the complete pytest
  run, package build, compilation, and diff check cover the executable boundary
  available in this repository.
- Deployment is outside this remediation and the repository has no
  `deploy.md` or `tasks/deploy.md` manual deploy contract.

## Adversarial review

An explicit diff and invariant audit checked the failure-prone edges: older
golden-suite relations remain version-restricted and behaviorally unchanged;
the new assertion requires its own region as its sole subject, exactly one line
reference, ratio units, and the fixed 75 km corridor; null historical sides are
accepted only for `0.3.0` soft evidence and are rejected by cross-document QA
unless referenced exclusively by negative assertions; zero-length and non-line
seams fail closed; signature construction ignores evidence/certainty/owner
aliases while including all five facets and sorted active actor pairs; and the
worldwide generator performs approved scaffold cleanup before packet merge.
No unresolved implementation defect was found.

## Residual risk

The seven seam failures are accepted evidence of unresolved modern scaffold
leakage, not waived test failures. They block certification alongside nine
unresolved Americas/Africa positive borders. The global missing-positive count
is intentionally 13 after retiring region `015`; missing-negative regions are
10. Historical-status remediation remains a later reviewer-gated task.

## Rollback note

Revert this shipping commit as one unit to restore the previous schema, QA,
generator, packet, asset, test, and documentation state. Do not selectively
restore the retired region `015` frontier as accepted evidence: its circular
provenance remains invalid.

## Next command

`$exec` — research missing assertions for the affected Asia and Europe regions
and present exact recommendations without changing implementation state.
