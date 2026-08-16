# M25C Central Asia Grade-A Promotion Ship Manifest

## User goal

Promote Central Asia (UN M49 143), the remaining Asian M25C region, with an
exact-date, source-pinned, four-layer Grade-A evidence packet while preserving
the non-public worldwide certification boundary.

## Changed files

- `research/start-dates/1444-global-v1/regional-packets/143-central-asia-2026-08-16.json`
- `research/start-dates/1444-global-v1/regional-packets/assets/143/boundaries.geojson`
- `research/start-dates/1444-global-v1/regional-packets/README.md`
- `scripts/generate-m25c-region-143-packet.py`
- `tasks/history.md`
- `tasks/m25c-region-143-ship-manifest.md`
- `tasks/roadmap.md`
- `tasks/todo.md`
- `tests/test_m25c_global_certification.py`

## Per-file purpose

The dated packet carries the complete region evidence, assignment
replacements, source records and pins, polity sheet, assertions, M49
corrections, and review digest. The generator deterministically rebuilds the
packet and its boundary asset from the accepted baseline and tracked Natural
Earth country fabric. The packet index, todo, roadmap, and history advance
M25C to ten promoted regions and close the Asian promotion sequence. The test
fixes packet counts, review digest, historical actors, removed scaffold actors,
and M49 correction targets.

## User-goal mapping

The packet replaces all 310 assignments and pins validity to `1444-11-11`.
Four gap-free Grade-A rows cover geometry, politics, hierarchy, and gazetteer
relationships. The sheet distinguishes Timurid Transoxiana, Khurasan, and
Khwarazm from Abu'l-Khayr's Uzbek ulus, Moghulistan, Nogai–Manghit, Syr Darya,
and local Turkmen fabrics. Two Russian locations move to M49 `151`, and one
Iranian location moves to `145`.

## Verification boundary

The generator checks source pins, assignment and actor classification, capital
containment, frontier adjacency, asset checksum, correction count, and packet
counts. Whole-world provisional assembly, QA, render review, focused tests,
the complete suite, package build, parsing, compilation, and diff checks form
the shipping gate. Ordinary acceptance, runtime compilation, certification,
publication, and deployment remain unavailable until all 22 regions have
four-layer Grade-A coverage.

## Tests run

- Deterministic generation produced 310 assignments, eight polities, seven
  sources, 17 assertions, four build features, one derived file, and three M49
  corrections.
- Complete 22-region assembly and provisional QA passed with zero errors and
  12 accepted provisional warnings; coverage is 40 A, 12 B, and 36 C rows.
- The deterministic region 143 review sheet was visually inspected and matched
  SHA-256 `cf8220bb99658d6b45f1d6ffc6cd42b6535f01282e26656432f2799e14d6ebd0`.
- Focused M25C certification and signing tests passed all 40 cases.
- The complete repository suite passed all 375 tests.
- `uv build` produced the source distribution and wheel; Python compilation,
  JSON loading, deterministic regeneration, and `git diff --check` passed.

## Skipped tests

Ordinary human acceptance, runtime compilation, worldwide certification,
publication, deployment, and production smoke testing remain intentionally
unavailable while 12 regional packets are incomplete.

## Adversarial review

The targeted review checks partial replacement, placeholder or invalid source
pins, duplicate IDs, date-inapplicable evidence, uncorroborated hard
boundaries, stale assets, missing four-layer evidence, capital containment,
modern scaffold leakage, M49 drift, and unintended certification-boundary
changes. Deterministic regeneration, whole-world QA, focused tamper tests,
render inspection, and the complete suite close the executable review.

## Residual risk

The accepted M23 fabric cannot support defensible exact local frontiers across
the Central Asian steppe and deserts. The packet therefore uses explicit
coarse steppe and frontier fabrics with 0.3 uncertainty. The checked
Timurid–Moghulistan boundary is one independently corroborated shared-fabric
segment, not a claim that the complete frontier has been newly digitized.

## Rollback note

Revert the promotion changes to remove the packet, generator, boundary asset,
tests, and task records. No public runtime or deployment requires rollback.

## Next command

`$exec` — promote the next M25C African or American region in risk-first order.
