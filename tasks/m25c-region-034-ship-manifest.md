# M25C Southern Asia Grade-A Promotion Ship Manifest

## User goal

Promote Southern Asia (UN M49 034) as the next risk-first Asian M25C region
with an exact-date, source-pinned, four-layer Grade-A evidence packet while
preserving the non-public worldwide certification boundary.

## Changed files

- `research/start-dates/1444-global-v1/regional-packets/034-southern-asia-2026-08-16.json`
- `research/start-dates/1444-global-v1/regional-packets/assets/034/boundaries.geojson`
- `research/start-dates/1444-global-v1/regional-packets/README.md`
- `scripts/generate-m25c-region-034-packet.py`
- `tasks/history.md`
- `tasks/m25c-region-034-ship-manifest.md`
- `tasks/roadmap.md`
- `tasks/todo.md`
- `tests/test_m25c_global_certification.py`

## Per-file purpose

The dated packet and derived boundary asset carry the accepted Southern Asia
evidence, complete assignment replacements, checked Bahmani–Vijayanagara
frontier, and source-pinned political sheet. The generator deterministically
rebuilds those artifacts and fails closed on assignment, capital, frontier,
source-pin, or count drift. Documentation advances M25C to eight promoted
regions, and the certification test fixes the real packet's counts, visual
digest, island treatment, and removal of modern Maldives and BIOT actors.

## User-goal mapping

Risk-first selection advances from Eastern Asia to Southern Asia. Exact-date
validity is pinned to `1444-11-11`; source pins hash each complete canonical
source record and exact locator; four gap-free Grade-A rows cover geometry,
politics, hierarchy, and gazetteer relationships. All 910 regional assignments
are replaced while the worldwide non-public gates remain unchanged.

The sheet separates the declining Sayyid Sultanate of Delhi from independent
regional sultanates and kingdoms, distinguishes Timurid and Qara Qoyunlu
fabrics, preserves Sri Lankan and Himalayan polities, and represents the
Maldives Sultanate and uninhabited Chagos without projecting modern actors
backward.

## Tests run

- Deterministic packet generation produced 910 assignments, 20 polities, nine
  sources, 53 assertions, thirteen build features, one derived file, and zero
  M49 corrections; a clean regeneration matched the packet and asset byte for
  byte.
- Complete 22-region provisional assembly and QA passed with zero errors and
  12 accepted provisional warnings. Coverage is exactly 32 A, 14 B, and 42 C
  rows, leaving 14 regions and 56 Grade-A rows.
- The Southern Asia review sheet was rendered and visually inspected. A clean
  second render reproduced accepted SHA-256
  `6f7d463396142edcd69616c2732687b740c55c41dc7d5c700d1f22b60106f000`.
- `.venv/bin/pytest -q tests/test_m25c_global_certification.py tests/test_m25c_packet_signing.py`
  passed 38 tests.
- `.venv/bin/pytest -q` passed all 373 repository tests.
- `uv build` produced the source distribution and wheel successfully.
- JSON parsing, Python compilation, and `git diff --check` passed.

## Skipped tests

Ordinary human acceptance, runtime compilation, certification, publication,
and deployment remain unavailable while 14 regional packets are incomplete.

## Adversarial review

The domain-specific review combined the Grade-A packet qualifier's tamper and
containment cases, a clean whole-world merge, exact source-pin recomputation,
deterministic regeneration, rendered-sheet inspection, and changed-file
self-review. It checked for partial assignment replacement, provisional source
leakage, duplicate IDs, date-inapplicable sources, placeholder pins,
uncorroborated hard boundaries, stale or escaping derived assets, missing
four-layer rows, M49 drift, modern Maldives/BIOT actors, and anachronistic
projection of Delhi across independent regional states. No unresolved
structural or executable finding remains.

## Residual risk

The political sheet deliberately uses coarse, source-supported fabrics for
Rajput, Bhutanese, Nepalese, and some Iranian and northwestern subcontinental
territories where the accepted M23 fabric cannot support a defensible exact
local frontier. The Bahmani–Vijayanagara hard constraint is a checked shared-
fabric segment, not a claim that the complete frontier has been newly
digitized.

## Rollback note

Revert the promotion changes to remove the packet, generator, boundary asset,
tests, and task records. No public runtime or deployment requires rollback.

## Next command

`$exec` — promote the next M25C Asian region in risk-first order.
