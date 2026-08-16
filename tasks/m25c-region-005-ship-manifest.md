# M25C South America Grade-A Promotion Ship Manifest

## User goal

Promote South America (M49 005), the largest remaining Africa/Americas region,
with an exact-date, source-pinned, four-layer Grade-A packet while preserving
the non-public worldwide certification boundary.

## Changed files

- `research/start-dates/1444-global-v1/regional-packets/005-south-america-2026-08-16.json`
- `research/start-dates/1444-global-v1/regional-packets/README.md`
- `scripts/generate-m25c-region-005-packet.py`
- `tasks/history.md`
- `tasks/m25c-region-005-ship-manifest.md`
- `tasks/roadmap.md`
- `tasks/todo.md`
- `tests/test_m25c_global_certification.py`

## Per-file purpose

The dated packet carries the complete South America evidence, assignment
replacements, source records and pins, polity sheet, assertions, and accepted
review digest. The generator deterministically rebuilds that packet from the
accepted baseline and tracked Natural Earth country fabric. The packet index,
todo, roadmap, and history advance M25C to twelve promoted regions. The
certification test fixes packet counts, the review digest, removed scaffold
actors, and required date-valid actors. This manifest records the exact
shipping boundary and its validation evidence.

## User-goal mapping

South America was the largest remaining Africa/Americas sheet with 2,200
assignments, of which 2,159 used the generic provisional actor and 41 used an
anachronistic Falklands actor. The replacement pins exact validity to
`1444-11-11`, hashes complete source records plus exact locators, and supplies
four gap-free Grade-A rows for geometry, politics, hierarchy, and gazetteer
relationships.

The sheet distinguishes Pachakuti's early Inca state, unconquered Chimor,
Aymara and other Andean polities, Muisca and Tairona chiefdoms, Amazonian and
other lowland networks, southern community fabrics, and uninhabited South
Atlantic islands. It deliberately avoids fabricated hard frontiers and does
not project later Inca maxima, colonial borders, or contact-era tribal maps
backward.

## Verification boundary

The generator fixes assignment scope, actor coverage, source pins, checked-site
containment, packet counts, and deterministic JSON. Whole-world provisional
assembly, QA, render review, focused tests, the complete suite, package build,
compilation, and diff checks form the shipping gate. Human acceptance, runtime
certification, publication, and deployment remain unavailable until all 22
regions have four-layer Grade-A coverage.

## Tests run

- Deterministic generation produced 2,200 assignments, 15 polities, nine
  sources, 32 assertions, eight build features, no derived hard-frontier file,
  and no M49 corrections; clean regeneration matched byte-for-byte.
- Complete 22-region assembly and provisional QA passed with zero errors and
  12 expected non-public warnings.
- The deterministic region 005 review sheet was visually inspected and matched
  SHA-256 `7275a21a0e8eea8acf508d0e8518e8432f1c2c4164958d6cfa1592b180bf64c2`.
- Focused M25C certification tests passed all 35 cases. The complete repository
  suite passed all 377 tests on the final diff.
- `uv build` produced the source distribution and wheel. Python compilation,
  JSON loading, canonical pin recomputation, duplicate-ID checks, deterministic
  regeneration, and `git diff --check` passed.

## Skipped tests

Ordinary human acceptance, runtime compilation, worldwide certification,
publication, deployment, and production smoke testing remain intentionally
unavailable while ten regional packets are incomplete. They are downstream
gates, not executable validation for this non-public regional promotion.

## Adversarial review

No configured `quality-sweep` or `expert-review` lane exists, so the equivalent
targeted review checked the exact diff and generated packet for partial
assignment replacement, placeholder or invalid source pins, duplicate IDs,
date-inapplicable sources, fabricated or uncorroborated hard boundaries,
missing four-layer evidence, checked-site containment failures, generic modern
scaffold leakage, M49 drift, non-deterministic regeneration, and unintended
changes to the certification or publication boundary. The review found that a
new Met source duplicated the existing regional-survey page; it was replaced
with a distinct Met Chimor collection record before final regeneration. The
fail-closed packet qualifier, clean whole-world assembly, source-pin
recomputation, rendered-sheet inspection, focused tamper tests, and complete
repository suite found no remaining executable issue.

## Residual risk

The accepted M23 fabric and surviving evidence cannot support defensible exact
local borders for most 1444 South American communities. The packet therefore
uses explicit coarse political fabrics with 0.35 uncertainty, checked centers,
and no hard boundary. These groupings are evidence-bounded replacements for a
generic actor, not claims of uniform sovereignty or immutable culture areas.

## Rollback note

Revert the promotion changes to remove the packet, generator, tests, and task
records. No public runtime or deployment requires rollback.

## Next command

`$exec` — promote the next M25C African or American region in risk-first order.
