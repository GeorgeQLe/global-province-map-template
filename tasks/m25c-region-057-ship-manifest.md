# M25C Micronesia Grade-A Promotion Ship Manifest

## User goal

Promote Micronesia (M49 057), the final incomplete M25C region, with an
exact-date, source-pinned, four-layer Grade-A packet and close the regional
evidence-promotion phase without bypassing worldwide certification gates.

## Changed files

- `research/start-dates/1444-global-v1/regional-packets/057-micronesia-2026-08-16.json`
- `research/start-dates/1444-global-v1/regional-packets/README.md`
- `scripts/generate-m25c-region-057-packet.py`
- `tasks/history.md`
- `tasks/m25c-region-057-ship-manifest.md`
- `tasks/roadmap.md`
- `tasks/todo.md`
- `tests/test_m25c_global_certification.py`

## Per-file purpose

- The dated packet carries complete source, assignment, gazetteer, assertion,
  coverage, and accepted-render records for region 057.
- The generator deterministically rebuilds that packet from the accepted
  baseline and tracked Natural Earth country fabric.
- The packet index records Micronesia's accepted historical interpretation and
  closes the 22-region packet sequence.
- Todo, roadmap, and history advance M25C from twenty-one to twenty-two promoted
  regions and route the next work to ordinary worldwide research review.
- The certification test fixes packet counts, required and forbidden actors,
  the render digest, and the absence of an M49 correction.
- This manifest records the shipping, verification, risk, rollback, and
  next-work boundary.

## User-goal mapping

The packet replaces all 175 native region-057 assignments with thirteen
conservative island-community, atoll-network, voyaging, chiefly, or
uninhabited-island fabrics for exactly `1444-11-11`. Ten pinned sources, eight
checked sites, and 32 assertions close all four Grade-A rows. It preserves the
Saudeleur polity on Pohnpei and Leluh on Kosrae while avoiding modern
dependencies, colonial relationships, fixed ethnic borders, or a
pan-Micronesian state. All 22 regions and all 88 rows are now Grade A.

## Verification boundary

The generator fixes assignment scope, actor coverage, canonical source pins,
checked-site containment, packet counts, and deterministic JSON. Fresh worldwide
assembly, provisional QA, deterministic sheet rendering, focused and complete
tests, compilation, package build, and diff checks form the shipping gate.
Ordinary research acceptance, runtime certification, publication, and deployment
remain separate gates and are not performed by this regional promotion.

## Tests run

- Packet generation produced 175 assignments, thirteen polities, ten sources,
  32 assertions, eight build features, no hard-frontier asset, and no M49
  correction.
- Fresh worldwide assembly passed provisional QA with zero errors, 88 Grade-A
  rows, and no remaining regional evidence gap.
- The deterministic promoted region-057 review sheet was inspected and accepted
  at SHA-256 `d81edf89684cfdf97f65faa1c5a891df1a47a552aef38a5b5e858e4ddea8c7dc`.
- All 45 global-certification tests and all 387 repository tests passed; the new
  generator compiled cleanly, regeneration matched byte-for-byte, and
  `git diff --check` passed. `uv build --wheel` also produced the package wheel
  successfully using the configured setuptools backend.

## Skipped tests

Ordinary human acceptance, runtime compilation, worldwide certification,
publication, deployment, and production smoke testing remain intentionally
separate. No standalone lint or typecheck command is configured in
`pyproject.toml`.

## Adversarial review

The fail-closed packet qualifier, focused actor/count regression contract,
fresh worldwide assembly, full repository suite, deterministic regeneration,
and promoted-sheet inspection challenge partial replacement, invalid pins,
duplicate IDs, date-inapplicable evidence, unsupported hard boundaries,
missing coverage, checked-site containment, surviving scaffold actors, render
drift, and changes to the worldwide certification boundary.

## Residual risk

Written exact-date evidence is sparse for many atolls and small islands. The
packet therefore uses coarse island, chain, atoll-network, village, voyaging,
and chiefly fabrics with 0.35 uncertainty and draws no hard local frontier.

## Rollback note

Revert the promotion changes to remove the packet, generator, test, and task
records. No public runtime or deployment requires rollback.

## Next command

`$exec` — run the ordinary M25C worldwide research QA and human-review sequence.
