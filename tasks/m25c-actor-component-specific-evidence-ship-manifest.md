# M25C actor/component-specific evidence ship manifest

Date: `2026-08-24`
Status: **research complete; pending independent review; no remediation authorized**

## User goal

Obtain stronger actor/component-specific evidence for the remaining ordinary-QA
blockers before Task 17 can open, without weakening the review, Grade-A, or
release gates.

## Changed files

- `scripts/generate-m25c-actor-component-evidence.py`
- `tests/test_m25c_actor_component_evidence.py`
- `research/start-dates/1444-global-v1/replacement-evidence/actor-component-specific-v1/README.md`
- `research/start-dates/1444-global-v1/replacement-evidence/actor-component-specific-v1/manifest.json`
- `research/start-dates/1444-global-v1/replacement-evidence/actor-component-specific-v1/component-specific-evidence.json`
- `research/start-dates/1444-global-v1/replacement-evidence/actor-component-specific-v1/actor-specific-evidence.json`
- `research/start-dates/1444-global-v1/replacement-evidence/actor-component-specific-v1/pair-specific-evidence.json`
- `research/start-dates/1444-global-v1/replacement-evidence/actor-component-specific-v1/finding-routes.json`
- `tasks/m25c-actor-component-specific-evidence.md`
- `tasks/m25c-actor-component-specific-evidence-ship-manifest.md`
- `README.md`
- `tasks/todo.md`
- `tasks/roadmap.md`
- `tasks/history.md`

## Per-file purpose

- The generator performs full-polygon source intersections, complete actor
  aggregation, exact pair binding, route binding, input/output hashing, and
  fail-closed recommendations.
- The executable test verifies the frozen rejected surfaces, record hashes,
  actor identities, full-geometry method, exact evidence-class totals, output
  hashes, input hashes, and pending-review boundary.
- The packet README explains interpretation and reproduction. Its manifest
  pins the assembled input, prior evidence and review records, all 22 regional
  packets used for actor names, the source slice, and every generated output.
- The four evidence documents carry the exact 206-component, 107-actor,
  180-pair, and 32-route research surface.
- The research task records method, result, alternatives, expected QA impact,
  and the no-implementation boundary.
- The project README and task state documents record the stronger negative
  evidence without changing Task 17 or release status.
- This manifest defines the exact shipping boundary and quality evidence.

## User-goal mapping

- Component-specific strength: every rejected component is measured over its
  complete polygon instead of only its representative point, retaining exact
  source-feature identity and overlap area.
- Actor-specific strength: every actor in a rejected pair is bound to its
  complete assembled component inventory and named source-zone attribution.
- Pair-specific strength: every rejected pair binds both exact actor records
  and all exact incident components while separating zonal overlap from border
  proof.
- Remaining blockers: all 32 rejected routes bind to the stronger records and
  prior independent-review decisions.
- Honest Task 17 boundary: 187 components remain outside source coverage, 19
  have only minor overlap below 50%, and all 180 pairs remain insufficient, so
  no remediation or Task 17 transition is claimed.

## Tests run

- Executable full configured suite: `.venv/bin/pytest -q` — `441 passed in
  63.42s`, with no warnings.
- Executable focused suite after the final manifest-pinning update:
  `.venv/bin/pytest -q tests/test_m25c_actor_component_evidence.py` — `4 passed
  in 0.16s`, with no warnings.
- Executable evidence regression suite:
  `.venv/bin/pytest -q tests/test_m25c_actor_component_evidence.py
  tests/test_m25c_best_reasonable_evidence.py
  tests/test_m25c_replacement_evidence.py` — `12 passed in 0.40s`, with no
  warnings.
- Executable syntax verification: `.venv/bin/python -m py_compile
  scripts/generate-m25c-actor-component-evidence.py` — passed with no output.
- Determinism verification: regenerated every generated packet file and
  compared SHA-256 inventories byte-for-byte; no differences were found.
- Patch hygiene: `git diff --check` — passed with no output.

## Skipped tests

- No separate lint, typecheck, or build command is configured in
  `pyproject.toml`, and the repository has no root `CLAUDE.md`, Makefile,
  Justfile, package scripts, `setup.cfg`, or `Cargo.toml` supplying one. The
  full pytest suite, Python compilation, generator execution, and deterministic
  output comparison cover the applicable executable surface.
- Ordinary assembled preflight and rendering were not rerun because this is a
  read-only research generator and immutable evidence packet; no regional
  packet, assembled artifact, QA rule, tolerance, or runtime path changed.
- The ship skill's referenced `docs/quality-gate-contract.md` is absent; the
  manifest and adversarial-review requirements stated in the skill were
  applied directly.
- No conversation export was requested. Deploy is skipped because the
  repository has no `deploy.md` or `tasks/deploy.md` manual deploy contract.

## Adversarial review

No configured `quality-sweep` or `expert-review` lane exists, so an explicitly
justified equivalent audit challenged the following failure modes:

1. **Point-sampling false negatives.** Every rejected component is intersected
   in full; 187 still have zero coverage and the other 19 remain below 50%.
2. **Source overlap overstated as identity.** Actor records explicitly retain
   `identity_assessment=not_established_by_geometry`; pair recommendations
   cannot treat spatial agreement as proof that synthetic and source actors
   are identical.
3. **Zonal overlap overstated as a border.** Pair records distinguish source
   zones from exact linework and require independent border evidence.
4. **Partial input lineage.** The audit found that actor display names depended
   on regional packets; the generator and manifest now pin all 22 packet files,
   and tests verify every input hash.
5. **Unenforced summary claim.** The audit found that the reported eight actors
   with any source coverage was not manifest-bound. The final generator emits
   the exact actor-class census, and the focused test asserts all `107/8` actor
   totals and classes.
6. **Route omission or accidental implementation.** Tests compare exact prior
   rejected component and pair IDs, assert all 32 route records, and require
   `pending_independent_review` plus `not_implemented` throughout.

No unresolved correctness finding remains inside this research boundary.

## Residual risk

- Cliopatria uses approximately `0.07°` smoothing and retains unquantified
  historical-border uncertainty.
- Geometry cannot prove identity between the project's synthetic community or
  polity actors and a source entity.
- Source silence does not prove that an uncovered landscape was empty,
  uninhabited, or ungoverned.
- Nineteen minor overlaps include possible actor conflicts and require human
  review; none is promoted automatically.
- Task 17 remains blocked on new actor-to-citation claims, component coverage,
  independently derived linework, gap-free Grade A, and zero-error ordinary QA.

## Rollback note

Revert the shipping commit to remove the generator, tests, evidence packet,
research report, and task-document updates together. No regional packet,
assembled candidate, QA tolerance, permission, runtime artifact, or public
state changed, so no data migration or operational rollback is required.

## Next command

`$exec` — obtain new exact actor-to-citation and component/line sources for the
206 rejected components and 180 rejected pairs, then submit any qualifying
records for independent review before remediation.
