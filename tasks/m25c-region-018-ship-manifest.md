# M25C Southern Africa Grade-A Promotion Ship Manifest

## User goal

Promote Southern Africa (M49 018), the final Africa/Americas region at 225
assignments, with an exact-date, source-pinned, four-layer Grade-A packet while
preserving the non-public worldwide certification boundary.

## Changed files

- `research/start-dates/1444-global-v1/regional-packets/018-southern-africa-2026-08-16.json`
- `research/start-dates/1444-global-v1/regional-packets/README.md`
- `scripts/generate-m25c-region-018-packet.py`
- `tasks/history.md`
- `tasks/m25c-region-018-ship-manifest.md`
- `tasks/roadmap.md`
- `tasks/todo.md`
- `tests/test_m25c_global_certification.py`

## Per-file purpose

- The dated packet carries the complete source, assignment, gazetteer,
  assertion, coverage, and accepted-render records.
- The generator deterministically rebuilds that packet from the accepted
  baseline and tracked Natural Earth country fabric.
- The packet index summarizes the accepted regional interpretation and scope.
- Todo, roadmap, and history advance M25C from seventeen to eighteen promoted
  regions while retaining the non-public certification boundary.
- The focused certification test fixes packet counts, required and forbidden
  actors, render digest, and the absence of M49 corrections.
- This manifest records the exact shipping, verification, risk, rollback, and
  next-work boundary.

## User-goal mapping

The packet replaces all 225 assignments with eight conservative
successor-polity, farming, pastoral, forager, or uninhabited-island fabrics for
exactly `1444-11-11`. Eight pinned sources, eight checked sites, and 32
assertions close all four Grade-A rows. It distinguishes the
Limpopo-Shashe successor field from Sotho-Tswana, Nguni-speaking, Khoe, San,
northern Namibian, Cape, and Southern Ocean island fabrics without projecting
later kingdoms, modern states, or colonial borders backward. No hard local
frontier is asserted. Eighteen regions are now promoted; four regions and 16
Grade-A rows remain.

## Verification boundary

The generator fixes assignment scope, actor coverage, canonical source pins,
checked-site containment, packet counts, and deterministic JSON. Whole-world
provisional assembly, QA, rendered-sheet inspection, focused and complete
tests, package build, compilation, and diff checks form the shipping gate.
Ordinary human acceptance, runtime certification, publication, and deployment
remain unavailable until all 22 regions are Grade A.

## Tests run

- `.venv/bin/python scripts/generate-m25c-region-018-packet.py` produced 225
  assignments, eight polities, eight sources, 32 assertions, eight build
  features, no hard-frontier asset, and no M49 correction.
- Regeneration to a fresh directory matched the tracked packet byte-for-byte.
- A fresh worldwide provisional assembly passed QA with zero errors, 12
  expected non-public certification warnings, 72 Grade-A rows, and exactly four
  incomplete regions.
- `.venv/bin/gpm qa render` produced the deterministic region 018 review sheet;
  full-resolution visual inspection accepted SHA-256
  `5b6086afc19995c54413496414280806c15837a77955ae975a95e858fd933adf`.
- Focused and complete repository tests, compilation, package build, and diff
  checks passed as recorded at handoff.

## Skipped tests

Ordinary human acceptance, runtime compilation, worldwide certification,
publication, deployment, and production smoke testing remain intentionally
unavailable while four regional packets are incomplete. No standalone lint or
typecheck command is configured in `pyproject.toml`.

## Adversarial review

The domain-specific adversarial review used the fail-closed packet qualifier,
focused certification contracts, fresh worldwide assembly, and full-resolution
render review as the quality-sweep equivalent. It challenged partial
replacement, invalid canonical pins, duplicate IDs, date-inapplicable evidence,
unsupported hard boundaries, missing four-layer coverage, checked-site
containment, surviving scaffold actors, render drift, and changes to the
worldwide certification boundary. The review confirmed that all 225 assignments
resolve exactly once, all seven former scaffold actor types are absent, no M49
correction is introduced, and only the four intended Oceania regions remain
incomplete. No unresolved packet defect was found.

## Residual risk

Written evidence is sparse for many local political boundaries in 1444, while
archaeological and linguistic sequences do not justify immutable ethnic
frontiers. The packet therefore uses coarse regional community fields with
0.35 uncertainty and keeps later named kingdoms out of the exact-date sheet.

## Rollback note

Revert the promotion changes to remove the packet, generator, test, and task
records. No public runtime or deployment requires rollback.

## Next command

`$exec` — promote Australia and New Zealand (M49 053), the largest remaining
Oceania region at 1,199 assignments.
