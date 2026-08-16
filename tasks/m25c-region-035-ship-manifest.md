# M25C South-Eastern Asia Grade-A Promotion Ship Manifest

## User goal

Promote South-Eastern Asia (UN M49 035) as the next risk-first Asian M25C
region with an exact-date, source-pinned, four-layer Grade-A evidence packet
while preserving the non-public worldwide certification boundary.

## Changed files

- `research/start-dates/1444-global-v1/regional-packets/035-south-eastern-asia-2026-08-16.json`
- `research/start-dates/1444-global-v1/regional-packets/assets/035/boundaries.geojson`
- `research/start-dates/1444-global-v1/regional-packets/README.md`
- `scripts/generate-m25c-region-035-packet.py`
- `tasks/history.md`
- `tasks/m25c-region-035-ship-manifest.md`
- `tasks/roadmap.md`
- `tasks/todo.md`
- `tests/test_m25c_global_certification.py`

## Per-file purpose

The dated packet carries the accepted region evidence, full assignment
replacement, source records and pins, polity sheet, assertions, M49
corrections, and review digest. The generator deterministically rebuilds the
packet and its boundary asset from the accepted baseline and tracked Natural
Earth country fabric. The packet index, todo, roadmap, and history advance
M25C to nine promoted regions. The certification test fixes the packet counts,
review digest, removed scaffold actors, required historical actors, and island
correction target. This manifest records the complete shipping boundary.

## User-goal mapping

Risk-first selection advances from Southern Asia to South-Eastern Asia. The
packet replaces all 1,759 assignments, including 1,256 uncurated rows, and
keeps mainland courts, maritime sultanates, archipelagic polities, and local
political fabrics distinct. Exact-date validity is pinned to `1444-11-11`;
four gap-free Grade-A rows cover geometry, politics, hierarchy, and gazetteer
relationships. Three Christmas and Cocos locations are corrected to M49 053.

## Verification boundary

The generator checks source pins, assignment and actor classification, capital
containment, frontier adjacency, asset checksum, correction count, and all
packet counts. Whole-world provisional assembly, QA, rendered review, focused
tests, the complete suite, package build, parsing, compilation, and diff checks
form the shipping gate. Ordinary acceptance, runtime compilation,
certification, publication, and deployment remain unavailable until all 22
regions have four-layer Grade A coverage.

## Tests run

- Clean regeneration matched the packet and boundary asset byte for byte.
- Complete 22-region assembly and provisional QA passed with zero errors and
  12 accepted provisional warnings; coverage is 36 Grade-A and 52 remaining
  rows.
- The deterministic region 035 review sheet was visually inspected and matched
  SHA-256 `8931349ecff68ab92179bd23c964bf85292a0b12a4b640bc56b2e6c22b6af6d2`.
- Focused M25C certification and signing tests passed 39 cases.
- The complete repository suite passed all 374 tests.
- `uv build`, Python compilation, JSON loading, and `git diff --check` passed.

## Skipped tests

Ordinary human acceptance, runtime compilation, worldwide certification,
publication, deployment, and production smoke testing remain intentionally
unavailable while 13 regional packets are incomplete. They are downstream
gates, not executable validation for this non-public regional promotion.

## Adversarial review

No configured `quality-sweep` or `expert-review` lane exists, so the equivalent
targeted review checked the exact diff and generated artifacts for partial
assignment replacement, placeholder or invalid source pins, duplicate IDs,
date-inapplicable sources, uncorroborated hard boundaries, escaping or stale
derived assets, absent four-layer evidence, capital containment failures,
modern scaffold-code leakage, M49 island drift, and unintended changes to the
certification/publication boundary. Clean whole-world assembly, the packet
qualifier's fail-closed checks, deterministic regeneration, focused tamper
tests, rendered-sheet inspection, and the full suite found no unresolved
executable issue.

## Residual risk

The sheet deliberately uses coarse source-supported political fabrics for
interior Borneo, Sulawesi, Papua, parts of Sumatra, Mindanao, and the eastern
archipelago where the accepted M23 fabric cannot support defensible exact
local frontiers. The Ayutthaya-Cambodia hard constraint is a checked shared-
fabric segment, not a claim that the complete frontier has been newly
digitized. These limitations remain explicit in actor names, uncertainty, and
the non-public certification boundary.

## Rollback note

Revert the promotion changes to remove the packet, generator, boundary asset,
tests, and task records. No public runtime or deployment requires rollback.

## Next command

`$exec` — promote the next M25C Asian region in risk-first order.
