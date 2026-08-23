# M25C region 005 corridor evidence-review ship manifest

## User goal

Qualify and implement a historically sourced replacement for the 21-component
Peru-Bolivia corridor only if two independent, license-compatible sources
cover every affected component. Stop without generator or packet changes when
the evidence gate cannot be met, while leaving the separate positive-border
requirement open.

## Changed files

- `tasks/m25c-region-005-corridor-evidence-review.md`
- `tasks/m25c-region-005-corridor-evidence-review-ship-manifest.md`
- `tasks/history.md`
- `tasks/todo.md`

## Per-file purpose

The evidence review binds the current generator, regional packet, negative
control, assembled artifacts, exact assertion measurement, and all 21 affected
components. It records why the nominated handbook, Arkush chronology, and
Stanish survey do not qualify a complete replacement fabric. This manifest
defines the shipped boundary and verification. History records the rejected
implementation, and the active todo retains Task 16 as open while routing past
the completed region `005` review.

## User-goal mapping

The review confirms that the current corridor split depends on Natural Earth
`ADM0_A3`, which is forbidden as historical evidence. The nominated sources
provide broad Andean or partial Titicaca-basin context but no independently
georeferenced, exact-date, two-sided fabric covering the complete fixed
`951.4017615694846 km` corridor. No component has an approved old/new mapping,
so the plan's fail-closed condition applies before implementation.

The generator, regional packet, negative-control asset, `75 km` corridor,
`0.20` tolerance, positive-border backlog, and all review, certification,
runtime, publication, and deployment permissions remain unchanged.

## Tests run

- `UV_CACHE_DIR=/private/tmp/gpm-uv-cache uv run pytest -q tests/test_m25c_modern_seam_controls.py`
  passed all 12 tests.
- `git diff --check` passed.
- SHA-256 checks reproduced the review-bound generator, packet, and negative
  control hashes.

## Skipped tests

The complete repository suite, package build, duplicate assembly, and render
verification were not repeated because no source code, packet, generated
asset, schema, configuration, or runtime behavior changed. The focused seam
tests exercise the only executable contract referenced by this documentation
review; the existing assembled measurements are hash-bound rather than
regenerated or promoted.

No task-document audit ran because `scripts/audit-task-docs.mjs` is absent.

## Adversarial review

The exact diff was checked for accidental generator or packet edits, relaxed
tolerances, changed negative-control geometry, invented positive borders,
unapproved component values, release-state changes, and claims unsupported by
the three nominated sources. The specialist studies cover northern or
southwestern parts of the Titicaca basin rather than the complete seam, and
the handbook does not provide a predeclared derivation or component mapping.
The review therefore rejects rather than extrapolates.

## Residual risk

Region `005` retains its executable spatial failure, missing-positive-border
finding, and downstream uncertified geometry grade. Resolving them requires a
new evidence packet with complete independent spatial coverage and licensing;
the dry-run feasibility result is not evidence and remains unapproved.

## Rollback note

Revert the documentation commit to remove this review and its tracking record.
No runtime or generated artifact rollback is required.

## Next command

`$exec` — review the next separate Task 16 evidence packet, region `011`,
without changing its corridor until the packet independently qualifies.
