# M25C Polynesia Grade-A Promotion Ship Manifest

## User goal

Promote Polynesia (M49 061), the largest remaining Oceania region at 176
assignments, with an exact-date, source-pinned, four-layer Grade-A packet while
preserving the non-public worldwide certification boundary.

## Changed files

- `research/start-dates/1444-global-v1/regional-packets/061-polynesia-2026-08-16.json`
- `research/start-dates/1444-global-v1/regional-packets/README.md`
- `scripts/generate-m25c-region-061-packet.py`
- `tasks/history.md`
- `tasks/m25c-region-061-ship-manifest.md`
- `tasks/roadmap.md`
- `tasks/todo.md`
- `tests/test_m25c_global_certification.py`

## Per-file purpose

- The dated packet carries complete source, assignment, gazetteer, assertion,
  coverage, and accepted-render records for region 061.
- The generator deterministically rebuilds that packet from the accepted
  baseline and tracked Natural Earth country fabric.
- The packet index records Polynesia's accepted historical interpretation and
  explains how the prior Tokelau correction composes with this promotion.
- Todo, roadmap, and history advance M25C from twenty to twenty-one promoted
  regions while preserving the non-public certification boundary.
- The certification test fixes packet counts, required and forbidden actors,
  the render digest, and the absence of new M49 corrections.
- This manifest records the exact shipping, verification, risk, rollback, and
  next-work boundary.

## User-goal mapping

The packet replaces all 176 native region-061 assignments with fifteen
conservative island-community, chieftain-polity, or uninhabited-island fabrics
for exactly `1444-11-11`. Ten pinned sources, eight checked sites, and 32
assertions close all four Grade-A rows. It preserves the fourteenth-century
Tu'i Tonga chiefdom while avoiding modern dependencies, fixed ethnic borders,
later dynasties, or a pan-Polynesian state. The seven Tokelau locations remain
owned by accepted region 053's M49 correction. Twenty-one regions are now
promoted; Micronesia and four Grade-A rows remain.

## Verification boundary

The generator fixes assignment scope, actor coverage, canonical source pins,
checked-site containment, packet counts, and deterministic JSON. Fresh worldwide
assembly, provisional QA, deterministic sheet rendering, focused and complete
tests, compilation, package build, and diff checks form the shipping gate.
Ordinary human acceptance, runtime certification, publication, and deployment
remain unavailable until all 22 regions are Grade A.

## Tests run

- Packet generation produced 176 assignments, fifteen polities, ten sources,
  32 assertions, eight build features, no hard-frontier asset, and no M49
  correction.
- Fresh worldwide assembly passed QA with zero errors, 12 expected non-public
  warnings, 84 Grade-A rows, and exactly one incomplete region.
- The deterministic promoted region-061 review sheet was inspected and accepted
  at SHA-256 `a3fb0c1f3d719bdd9aa893c5e3b2da38758c5b046cb98c7cb1adeb6fece59c9e`.
- All 44 global-certification tests and all 386 repository tests passed; the new
  generator compiled cleanly, regeneration matched byte-for-byte, and
  `git diff --check` passed. `uv build --wheel` also produced the package wheel
  successfully using the configured setuptools backend.

## Skipped tests

Ordinary human acceptance, runtime compilation, worldwide certification,
publication, deployment, and production smoke testing remain intentionally
unavailable while Micronesia is incomplete. No standalone lint or typecheck
command is configured in `pyproject.toml`.

## Adversarial review

The fail-closed packet qualifier, focused actor/count regression contract,
fresh worldwide assembly, full repository suite, deterministic regeneration,
and promoted-sheet inspection challenged partial replacement, invalid pins,
duplicate IDs, date-inapplicable evidence, unsupported hard boundaries,
missing coverage, checked-site containment, surviving scaffold actors, render
drift, and changes to the worldwide certification boundary. All 176 native
assignments resolve exactly once, all nine modern dependency scaffold actors
are absent, Tokelau remains supplied by accepted region 053, and only M49 057
remains incomplete.

## Residual risk

Written exact-date evidence is sparse for local political boundaries. The packet
therefore uses coarse island, atoll, valley, and chiefly fabrics with 0.35
uncertainty and draws no hard local frontier.

## Rollback note

Revert the promotion changes to remove the packet, generator, test, and task
records. No public runtime or deployment requires rollback.

## Next command

`$exec` — promote Micronesia (M49 057), the final incomplete M25C region.
