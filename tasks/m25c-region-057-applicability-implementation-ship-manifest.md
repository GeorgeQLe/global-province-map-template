# M25C region 057 applicability implementation ship manifest

Date: `2026-08-23`
Status: **implementation complete; worldwide candidate remains blocked**

## User goal

Serially implement region `057`'s independently approved
`no_land_adjacency` applicability record and rerun affected and worldwide QA.

## Changed files

- `scripts/generate-m25c-provisional-pass.py`
- `tests/test_m25c_global_certification.py`
- `README.md`
- `tasks/todo.md`
- `tasks/roadmap.md`
- `tasks/history.md`
- `tasks/m25c-region-057-applicability-implementation-ship-manifest.md`

## Per-file purpose

- `scripts/generate-m25c-provisional-pass.py`: applies the region `057`
  approval only in assembled mode and refuses any unsigned-record hash drift.
- `tests/test_m25c_global_certification.py`: proves provisional output remains
  pending, exact assembled approval succeeds, and post-review drift fails.
- `README.md`, `tasks/todo.md`, `tasks/roadmap.md`, and `tasks/history.md`: record
  the completed Task 16 state and exact remaining worldwide inventory.
- This manifest records the implementation boundary, executable verification,
  expected worldwide blockers, rollback, and next-work route.

## User-goal mapping

- Serial applicability implementation: only assembled-pass region `057` moves
  from pending to accepted; provisional output and the other four records stay
  pending.
- Independently approved bytes: the exact unsigned record is pinned to its
  approved SHA-256 and generation stops if any bound input changes.
- Affected QA: focused contracts and every region `057` result pass with no
  remaining region finding.
- Worldwide QA: a fresh generation, 30-sheet render, and ordinary preflight
  reproduce the exact expected two-error improvement without enabling a
  permission.

## Implemented record

The record retains reason `no_land_adjacency`, an empty
`eligible_land_adjacent_actor_pairs` array, 175 components, eight passing hard
anchors, and the reviewed source/revision bindings. Its determination records
13 internal adjacency edges and zero cross-actor or eligible land-adjacent
pairs. Independent review is accepted on `2026-08-23` at unsigned-record
SHA-256 `861b65efd997a11cd22af9beff76515fcffffcfd5e58d65af6aaa9d6ac21fb30`.

## Tests run

- Final affected contract suite, including the new assembled-only/hash-drift
  regression: `32 passed`.
- The new regression plus the worldwide negative-control inventory regression:
  `2 passed` in its earlier focused run.
- Fresh assembled generation: succeeded with the frozen packet, negative
  control, and acceptance-input hashes reproduced exactly.
- Render: all `30` sheets generated.
- Region `057`: no findings; the Yaren-Meneng seam, applicability assertion,
  and all 32 site-layer assertions pass.
- Ordinary worldwide preflight: expected non-clean result of `56` non-review
  errors and `1` warning. Remaining errors are four applicability, 18 missing
  positive-border, eight non-executable seam, 13 spatial, and 13 downstream
  Grade-A findings.
- `git diff --check`: passed.

## Skipped tests

- The complete repository suite and package build were not repeated. The
  implementation changes one generator record branch covered by the focused
  generator/QA/assembly/schema contracts, then exercises the real worldwide
  generator, renderer, and preflight end to end. `pyproject.toml` configures no
  separate lint or typecheck command.
- No deploy test applies because the repository has no `deploy.md` or
  `tasks/deploy.md` manual deployment contract.

## Adversarial review

The review challenged accidental provisional approval, approval leakage to the
other four records, recomputed acceptance after component/source drift, and
unintended corridor or permission changes. The generator restricts approval to
assembled region `057`, compares the complete unsigned record to a fixed hash,
and raises on drift. A regression executes pending, accepted, and tampered
paths; fresh artifact hashes reproduce every frozen corridor input, region
`057` has no findings, unrelated QA counts remain stable, and all four candidate
permissions remain false.

## Residual risk

No corridor, packet, tolerance, component, geometry, source, runtime,
certification, publication, release, or deployment permission changed. The
other four applicability candidates remain pending and the assembled candidate
cannot advance to independent review until ordinary worldwide QA is clean.

## Rollback note

Revert the generator, regression, and documentation changes, then regenerate
the assembled candidate to restore region `057`'s pending record and the prior
58-error worldwide result. No public or runtime artifact requires rollback.

## Next command

`$exec` — obtain independently approvable replacement evidence for the
remaining ordinary worldwide QA blockers before Task 17 review rendering.
