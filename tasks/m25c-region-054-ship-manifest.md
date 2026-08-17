# M25C Melanesia Grade-A Promotion Ship Manifest

## User goal

Promote Melanesia (M49 054), the largest remaining Oceania region at 414
assignments, with an exact-date, source-pinned, four-layer Grade-A packet while
preserving the non-public worldwide certification boundary.

## Changed files

- `research/start-dates/1444-global-v1/regional-packets/054-melanesia-2026-08-16.json`
- `research/start-dates/1444-global-v1/regional-packets/README.md`
- `scripts/generate-m25c-region-054-packet.py`
- `tasks/history.md`
- `tasks/m25c-region-054-ship-manifest.md`
- `tasks/roadmap.md`
- `tasks/todo.md`
- `tests/test_m25c_global_certification.py`

## Per-file purpose

- The dated packet carries the complete source, assignment, gazetteer,
  assertion, coverage, and accepted-render records.
- The generator deterministically rebuilds the packet from the accepted
  baseline and tracked Natural Earth country fabric.
- The packet index summarizes the accepted regional interpretation and scope.
- Todo, roadmap, and history advance M25C from nineteen to twenty promoted
  regions while retaining the non-public certification boundary.
- The focused certification test fixes packet counts, required and forbidden
  actors, render digest, and the absence of M49 corrections.
- This manifest records shipping, verification, risk, rollback, and next work.

## User-goal mapping

The packet replaces all 414 assignments with twelve conservative local
community or chiefly fabrics for exactly `1444-11-11`. Ten pinned sources,
eight checked sites, and 32 assertions close all four Grade-A rows. It keeps
New Guinea, Bismarck-Bougainville, Solomon, Vanuatu, Fijian, and Kanak fabrics
distinct without projecting modern states, fixed ethnic borders,
pan-Melanesian authority, or later paramount chiefdoms backward. No hard local
frontier or country-based M49 correction is asserted. Twenty regions are now
promoted; two regions and eight Grade-A rows remain.

## Verification boundary

The generator fixes assignment scope, actor coverage, canonical source pins,
checked-site containment, packet counts, and deterministic JSON. Whole-world
provisional assembly, QA, rendered-sheet inspection, focused and complete
tests, package build, compilation, and diff checks form the shipping gate.
Ordinary human acceptance, runtime certification, publication, and deployment
remain unavailable until all 22 regions are Grade A.

## Tests run

- `.venv/bin/python scripts/generate-m25c-region-054-packet.py` produced 414
  assignments, twelve polities, ten sources, 32 assertions, eight build
  features, no hard-frontier asset, and no M49 correction.
- Regeneration to a fresh directory matched the tracked packet byte-for-byte.
- A fresh worldwide provisional assembly passed QA with zero errors, 12
  expected non-public certification warnings, 80 Grade-A rows, and exactly two
  incomplete regions.
- `.venv/bin/gpm qa render` produced the deterministic region 054 review sheet;
  full-resolution visual inspection accepted SHA-256
  `b47bc579f3d0753d57cb20cdf2b6fe33ad494075dc65c870f79f16ff614e52c9`.
- Focused and complete repository tests, compilation, package build, and diff
  checks passed as recorded at handoff.

## Skipped tests

Ordinary human acceptance, runtime compilation, worldwide certification,
publication, deployment, and production smoke testing remain intentionally
unavailable while two regional packets are incomplete. No standalone lint or
typecheck command is configured in `pyproject.toml`.

## Adversarial review

The fail-closed packet qualifier, focused certification contracts, fresh
worldwide assembly, and full-resolution render review challenged partial
replacement, invalid pins, duplicate IDs, date-inapplicable evidence,
unsupported hard boundaries, missing coverage, checked-site containment,
surviving scaffold actors, render drift, and changes to the worldwide
certification boundary. All 414 assignments resolve exactly once, all five
modern-country scaffold actors are absent, no M49 correction is introduced,
and only Micronesia and Polynesia remain incomplete.

## Residual risk

Written exact-date evidence is sparse for local political boundaries, and
archaeological sequences plus later oral traditions do not justify immutable
ethnic frontiers. The packet therefore uses coarse island or regional community
fields with 0.35 uncertainty and excludes later named paramount chiefdoms.

## Rollback note

Revert the promotion changes to remove the packet, generator, test, and task
records. No public runtime or deployment requires rollback.

## Next command

`$exec` — promote Polynesia (M49 061), the largest remaining Oceania region at
176 assignments.
