# M25C Caribbean Grade-A Promotion Ship Manifest

## User goal

Promote Caribbean (M49 029), the largest remaining Africa/Americas region at
372 assignments, with an exact-date, source-pinned, four-layer Grade-A packet
while preserving the non-public worldwide certification boundary.

## Changed files

- `research/start-dates/1444-global-v1/regional-packets/029-caribbean-2026-08-16.json`
- `research/start-dates/1444-global-v1/regional-packets/README.md`
- `scripts/generate-m25c-region-029-packet.py`
- `tasks/history.md`
- `tasks/m25c-region-029-ship-manifest.md`
- `tasks/roadmap.md`
- `tasks/todo.md`
- `tests/test_m25c_global_certification.py`

## Per-file purpose

- The dated packet carries the complete source, assignment, gazetteer,
  assertion, coverage, and accepted-render records.
- The generator deterministically rebuilds that packet from the accepted
  baseline and tracked Natural Earth country fabric.
- The packet index summarizes the accepted regional interpretation and scope.
- Todo, roadmap, and history advance M25C from sixteen to seventeen promoted
  regions while retaining the non-public certification boundary.
- The focused certification test fixes packet counts, required and forbidden
  actors, render digest, and the absence of additional M49 corrections.
- This manifest records the exact shipping, verification, risk, rollback, and
  next-work boundary.

## User-goal mapping

The packet replaces all 372 assignments with 11 conservative chiefdom or
community fabrics for exactly `1444-11-11`. Eight pinned sources, eight checked
archaeological sites, and 32 assertions close all four Grade-A rows. Exact
region, complete replacement, unique IDs, canonical source pins, accepted
visual review, and spatial assertions are fail-closed contracts.

The sheet distinguishes Lucayan communities; Cuban, Hispaniolan, Boriken, and
Jamaican Taino fabrics; Guanahatabey western Cuba; northern and southern Lesser
Antillean communities; Trinidadian and southern-Caribbean fabrics; and small or
seasonally used islands without projecting modern island governments or one
pan-Caribbean polity backward. No hard local frontier is asserted. Seventeen
regions are now promoted; five regions and 20 Grade-A rows remain.

## Verification boundary

The generator fixes assignment scope, actor coverage, canonical source pins,
checked-site containment, packet counts, and deterministic JSON. Whole-world
provisional assembly, QA, rendered-sheet inspection, focused and complete
tests, package build, compilation, and diff checks form the shipping gate.
Ordinary human acceptance, runtime certification, publication, and deployment
remain unavailable until all 22 regions are Grade A.

## Tests run

- `.venv/bin/python scripts/generate-m25c-region-029-packet.py` produced 372
  assignments, 11 polities, eight sources, 32 assertions, eight build
  features, no hard-frontier asset, and no M49 correction.
- Regeneration to a fresh `mktemp` directory followed by `cmp` matched the
  tracked packet byte-for-byte.
- `.venv/bin/python scripts/generate-m25c-provisional-pass.py --output-dir
  /private/tmp/m25c-region-029-final-pass --regional-packets-dir
  research/start-dates/1444-global-v1/regional-packets --qa` passed with zero
  errors, 12 expected non-public warnings, 68 Grade-A rows, and exactly five
  incomplete regions. The warnings are accepted certification-boundary
  findings caused by the five intentionally incomplete regions and pending
  worldwide review; none is a Caribbean packet error.
- `.venv/bin/gpm qa render` produced the deterministic region 029 review sheet;
  full-resolution visual inspection accepted SHA-256
  `ce83e796b976bfd6ca81678425766c99eab5eeda532dfe4a4b66c9f9a413ecba`.
- `.venv/bin/pytest -q tests/test_m25c_global_certification.py` passed all 40
  focused cases. `.venv/bin/pytest -q` passed all 382 repository tests.
- `.venv/bin/python -m compileall -q src
  scripts/generate-m25c-region-029-packet.py`, `git diff --check`, and
  `UV_CACHE_DIR=/private/tmp/m25c-uv-cache uv build` all passed; the build
  produced the source distribution and wheel.

## Skipped tests

Ordinary human acceptance, runtime compilation, worldwide certification,
publication, deployment, and production smoke testing remain intentionally
unavailable while five regional packets are incomplete. No standalone lint or
typecheck command is configured in `pyproject.toml`.

## Adversarial review

The domain-specific adversarial review used the fail-closed packet qualifier,
focused certification contracts, fresh worldwide assembly, and full-resolution
render review as the quality-sweep equivalent. It challenged partial
replacement, invalid canonical pins, duplicate IDs, date-inapplicable evidence,
unsupported hard boundaries, missing four-layer coverage, checked-site
containment, surviving scaffold actors, render drift, and changes to the
worldwide certification boundary. The review confirmed that 24 Caribbean
locations corrected and politically represented by the earlier region 155
packet remain intentionally outside these 372 overrides; this is inherited
accepted evidence, not missing coverage. No unresolved packet defect was found.

## Residual risk

The evidence does not support exact local borders across most Caribbean islands
in 1444, and some ethnonyms come from later contact records. The packet
therefore uses coarse island chiefdom and community fields with 0.35
uncertainty, separates well-supported regional traditions, and avoids claims of
uniform sovereignty or immutable cultural boundaries.

## Rollback note

Revert the promotion changes to remove the packet, generator, test, and task
records. No public runtime or deployment requires rollback.

## Next command

`$exec` — promote Southern Africa (M49 018), the final remaining
Africa/Americas region at 225 assignments.
