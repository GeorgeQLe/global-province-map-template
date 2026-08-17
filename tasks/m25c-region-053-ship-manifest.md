# M25C Australia and New Zealand Grade-A Promotion Ship Manifest

## User goal

Promote Australia and New Zealand (M49 053), the largest remaining Oceania
region at 1,199 assignments, with an exact-date, source-pinned, four-layer
Grade-A packet while preserving the non-public worldwide certification
boundary.

## Changed files

- `research/start-dates/1444-global-v1/regional-packets/053-australia-new-zealand-2026-08-16.json`
- `research/start-dates/1444-global-v1/regional-packets/README.md`
- `scripts/generate-m25c-region-053-packet.py`
- `tasks/history.md`
- `tasks/m25c-region-053-ship-manifest.md`
- `tasks/roadmap.md`
- `tasks/todo.md`
- `tests/test_m25c_global_certification.py`

## Per-file purpose

- The dated packet carries the complete source, assignment, gazetteer,
  assertion, correction, coverage, and accepted-render records.
- The generator deterministically rebuilds the packet from the accepted
  baseline and tracked Natural Earth country fabric.
- The packet index summarizes the accepted regional interpretation and scope.
- Todo, roadmap, and history advance M25C from eighteen to nineteen promoted
  regions while retaining the non-public certification boundary.
- The focused certification test fixes packet counts, required and forbidden
  actors, render digest, and all seven M49 corrections.
- This manifest records shipping, verification, risk, rollback, and next work.

## User-goal mapping

The packet replaces all 1,199 assignments with 14 conservative Aboriginal,
Maori, Polynesian, or uninhabited-island fabrics for exactly `1444-11-11`.
Twelve pinned sources, eight checked sites, and 32 assertions close all four
Grade-A rows. It preserves broad Aboriginal regional diversity, distinct Maori
iwi and hapu fabrics, and the late Norfolk Polynesian settlement without
projecting modern language-map boundaries or pan-Indigenous polities backward.
Seven Tokelau locations are corrected to M49 Polynesia `061`. Nineteen regions
are now promoted; three regions and 12 Grade-A rows remain.

## Verification boundary

The generator fixes assignment scope, actor coverage, canonical source pins,
checked-site containment, Tokelau correction scope, packet counts, and
deterministic JSON. Whole-world provisional assembly, QA, rendered-sheet
inspection, focused and complete tests, package build, compilation, and diff
checks form the shipping gate. Ordinary human acceptance, runtime
certification, publication, and deployment remain unavailable until all 22
regions are Grade A.

## Tests run

- `.venv/bin/python scripts/generate-m25c-region-053-packet.py` produced 1,199
  assignments, 14 polities, twelve sources, 32 assertions, eight build features,
  seven M49 corrections, and no hard-frontier asset.
- Regeneration to a fresh directory matched the tracked packet byte-for-byte.
- A fresh worldwide provisional assembly passed QA with zero errors, 12
  expected non-public certification warnings, 76 Grade-A rows, and exactly
  three incomplete regions.
- `.venv/bin/gpm qa render` produced the deterministic region 053 review sheet;
  full-resolution visual inspection accepted SHA-256
  `2b3d18fcd8920ce1359d768a03aee2ba8cfe846aed0404f8868ee37e2e53e7e6`.
- Focused and complete repository tests, compilation, package build, and diff
  checks passed as recorded at handoff.

## Skipped tests

Ordinary human acceptance, runtime compilation, worldwide certification,
publication, deployment, and production smoke testing remain intentionally
unavailable while three regional packets are incomplete. No standalone lint
or typecheck command is configured in `pyproject.toml`.

## Adversarial review

The fail-closed packet qualifier, focused certification contracts, fresh
worldwide assembly, and full-resolution render review challenged partial
replacement, invalid pins, duplicate IDs, date-inapplicable evidence,
unsupported hard boundaries, missing coverage, checked-site containment,
surviving scaffold actors, correction drift, render drift, and changes to the
worldwide certification boundary. All 1,199 assignments resolve exactly once,
all four scaffold actor types are absent, seven and only seven Tokelau
locations move to `061`, and only the three intended Oceania regions remain
incomplete.

## Residual risk

Written exact-date evidence is sparse for many local political boundaries,
and modern language and nation maps are unsuitable as fixed 1444 borders. The
packet therefore uses coarse geographic community fields with 0.35 uncertainty
and does not imply a single Aboriginal, Maori, or pan-Indigenous state.

## Rollback note

Revert the promotion changes to remove the packet, generator, test, and task
records. No public runtime or deployment requires rollback.

## Next command

`$exec` — promote Melanesia (M49 054), the largest remaining Oceania region at
414 assignments.
