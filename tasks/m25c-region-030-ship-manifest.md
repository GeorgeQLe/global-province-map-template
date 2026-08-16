# M25C Eastern Asia Grade-A Promotion Ship Manifest

## User goal

Promote the next risk-first M25C region with an exact-date, source-pinned,
four-layer Grade-A evidence packet while preserving the non-public worldwide
certification boundary.

## Changed files

- `research/start-dates/1444-global-v1/regional-packets/030-eastern-asia-2026-08-16.json`
- `research/start-dates/1444-global-v1/regional-packets/assets/030/boundaries.geojson`
- `research/start-dates/1444-global-v1/regional-packets/README.md`
- `scripts/generate-m25c-region-030-packet.py`
- `tasks/history.md`
- `tasks/m25c-region-030-ship-manifest.md`
- `tasks/roadmap.md`
- `tasks/todo.md`
- `tests/test_m25c_global_certification.py`

## Per-file purpose

The dated packet and derived boundary asset carry the accepted Eastern Asia
evidence, complete assignment replacements, checked Ming-Oirat frontier, and
source-pinned political sheet. The generator deterministically rebuilds those
artifacts and fails closed on assignment, capital, frontier, source-pin, or
count drift. Documentation advances M25C to seven promoted regions, and the
certification test fixes the real packet's counts, visual digest, and removal
of modern-scaffold actors.

## User-goal mapping

Risk-first selection advances from Northern Africa to Eastern Asia, the largest
and most anachronism-prone remaining Asian sheet. Exact-date validity is pinned
to `1444-11-11`; source pins hash each complete canonical source record and
exact locator; four gap-free Grade-A rows cover geometry, politics, hierarchy,
and gazetteer relationships. All 1,941 regional assignments are replaced while
the worldwide non-public gates remain unchanged.

## Tests run

- `.venv/bin/python scripts/generate-m25c-region-030-packet.py`: deterministic
  packet generation produced 1,941 assignments, eight polities, nine
  sources, 21 assertions, five build features, one derived file, and zero M49
  corrections.
- `.venv/bin/python scripts/generate-m25c-provisional-pass.py ... --qa`: clean
  22-region provisional assembly passed with zero errors. Its 12 warnings are
  accepted because they identify the intentionally non-public lineage,
  incomplete remaining regions, and pending downstream review gates.
- `.venv/bin/gpm qa render ...`: review render and visual inspection accepted SHA-256
  `995c0fe202ab3c93d9266fc1706da7fe513076aada09db811969a2ed88807abc`.
- `.venv/bin/pytest -q tests/test_m25c_global_certification.py tests/test_m25c_packet_signing.py`:
  37 passed. `.venv/bin/pytest -q`: 372 passed.
- `uv build` produced the source distribution and wheel successfully.
- Deterministic regeneration, JSON/source-pin/asset checks, Python compilation,
  and `git diff --check` passed.

## Skipped tests

Ordinary human acceptance, runtime compilation, certification, publication,
and deployment remain unavailable while 15 regional packets are incomplete.

## Adversarial review

The domain-specific review combined the Grade-A packet qualifier's tamper and
containment cases, a clean whole-world merge, exact source-pin recomputation,
deterministic regeneration, rendered-sheet inspection, and changed-file
self-review. It explicitly checked for partial assignment replacement,
provisional source leakage, duplicate IDs, date-inapplicable sources,
placeholder pins, uncorroborated hard boundaries, stale or escaping derived
assets, missing four-layer rows, M49 drift, and the continued presence of the
modern Hong Kong, Macao, or Muscovy actors. The first merge exposed a missing
derived-geometry declaration and the first capital pass exposed an incorrect
Karakorum actor threshold; both were fixed before the clean verification runs.
No unresolved structural or executable finding remains.

## Residual risk

The historical sheet deliberately uses coarse, source-supported political
fabrics for Jurchen lands, Tibet, Mongolia, and Moghulistan where the accepted
M23 fabric cannot support a defensible exact local frontier. The Ming-Oirat
hard constraint is a checked shared-fabric segment, not a claim that the full
frontier has been newly digitized.

## Rollback note

Revert the promotion changes to remove the packet, generator, boundary asset,
tests, and task records. No public runtime or deployment requires rollback.

## Next command

`$exec` — promote the next M25C Asian region in risk-first order.
