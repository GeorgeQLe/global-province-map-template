# M25 Review-Sheet Ship Manifest

## User goal

Wrap up and publish the current M25 session without claiming acceptance before
the required independent human review.

## Changed files and per-file purpose

- `src/gpm/qa/render.py` and `tests/test_m25_v2_contract.py`: render a stable
  main map plus per-constraint focus insets, legends, scale bars,
  georeferencing controls/residuals, negative-control labels, and deterministic
  SVG output; pin the new behavior with focused tests.
- `scripts/build-m25-v2-pass.py`,
  `schemas/historical-boundary-registry.schema.json`, and `src/gpm/schemas.py`:
  record and validate an exact source-substrate substring for each certified
  frontier, and distinguish georeferencing residual budgets from measured
  full-build Hausdorff tolerances.
- `research/start-dates/1444-v2/{boundaries.geojson,derived/*.geojson,dossier.md}`:
  publish the structured substring provenance and clarified tolerance claim.
- `research/start-dates/1444-v2/review/*.svg` and the pass, source, and review
  manifests: regenerate the five deterministic review sheets and repin every
  changed artifact hash.
- `tasks/{todo,roadmap,history}.md`: retain M25 as active, document the improved
  review surface and exact remaining human gate, and record this session.
- Existing unpushed commit `f679987`: pin the paintability report timestamp so
  complete v2 builds are byte-identical and widen the paintability clip window
  safely for larger tolerances.

## User-goal mapping

- Shipping readiness: review artifacts expose the evidence a human must inspect
  and can be reproduced from exact substrate measures.
- Honesty gate: M25 remains unsigned and unaccepted; no release claim is made.
- Regression safety: schema, runtime validation, rendering, production-pass,
  and complete repository tests cover the shipping boundary.

## Tests run

- `.venv/bin/pytest -q tests/test_m25_v2_contract.py tests/test_m25_v2_production_pass.py`:
  15 passed after the adversarial-review fix.
- `.venv/bin/pytest -q`: 285 passed with no warnings.
- `.venv/bin/python scripts/build-m25-v2-pass.py assemble`: reproduced all five
  frontier Hausdorff and five modern negative-control measurements.
- `.venv/bin/python scripts/build-m25-v2-pass.py render`: regenerated all five
  region sheets and their manifest.
- `git diff --check`: passed.

## Skipped tests

- No separate lint, typecheck, or build commands are configured in
  `pyproject.toml`; the complete executable pytest suite and direct assembler /
  renderer runs exercise the changed Python, schema, and generated artifacts.
- The canonical unsigned `gpm qa start-date` command is intentionally expected
  to fail until the independent review is signed. The production-pass test
  applies a test-only signature to a copy and verifies every non-review gate.

## Adversarial review

- Inspected the full source/schema/generated-artifact diff and regenerated the
  artifacts from the modified assembler and renderer.
- Found that the first structured-reference schema draft required only `kind`,
  which could admit a non-reproducible object. Tightened both JSON Schema and
  runtime validation to require the measure units, ordered numeric interval,
  and substrate merge rule; added positive and reversed-interval tests.
- Confirmed generated skill roots are unchanged and outside the shipping
  boundary. Searched the textual diff for credential-like material; none was
  found.

## Residual risk

- SVG scale bars use an explicitly approximate equirectangular conversion;
  they are review aids, not measurement evidence. Golden assertions remain the
  authoritative computed distances.
- Historical acceptance still depends on an independent human inspecting all
  five sheets and georeferencing records. This is the intentional M25 blocker.

## Rollback note

Revert the new session commit and existing `f679987` independently on `main` if
needed; do not rewrite published history. Regenerate the v2 pass afterward so
manifest hashes match the restored implementation.

## Next command

`python scripts/build-m25-v2-pass.py sign-review --reviewer "<name>"` after an
independent human has completed the documented inspection.
