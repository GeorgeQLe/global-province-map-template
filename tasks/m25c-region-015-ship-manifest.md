# M25C Northern Africa Grade-A Promotion Ship Manifest

> Remediation note (2026-08-21): the generated Marinid-Zayyanid frontier
> described below was subsequently found to be circular evidence and retired.
> Region 015 now carries one Natural Earth Morocco-Algeria modern negative
> control, which fails closed at 1.0. The original promotion record is retained
> here as history, not as the current evidence claim.

## User goal

Promote UN M49 region 015 (Northern Africa) with an exact-date, source-pinned,
four-layer Grade-A evidence packet while preserving the non-public worldwide
certification boundary.

## Changed files

- `research/start-dates/1444-global-v1/regional-packets/015-northern-africa-2026-08-16.json`
- `research/start-dates/1444-global-v1/regional-packets/assets/015/boundaries.geojson`
- `research/start-dates/1444-global-v1/regional-packets/assets/015/polity-masks.geojson`
- `research/start-dates/1444-global-v1/regional-packets/README.md`
- `scripts/generate-m25c-region-015-packet.py`
- `tasks/history.md`
- `tasks/m25c-region-015-ship-manifest.md`
- `tasks/roadmap.md`
- `tasks/todo.md`
- `tests/test_m25c_global_certification.py`

## Per-file purpose

- The dated packet and two derived assets carry the accepted Northern Africa
  evidence, complete assignment replacements, checked frontier, and source-
  pinned polity masks.
- The region-015 generator deterministically rebuilds the packet, source pins,
  exact-date polity split, capital gates, assertions, and asset checksums while
  failing closed on assignment or spatial drift.
- The regional README indexes the sixth accepted packet. Todo, roadmap, and
  history advance M25C to six promoted regions, and this manifest records the
  exact shipping boundary.
- The certification test qualifies the real packet and fixes its counts,
  source lineage, visual digest, and distinct Middle Nile polity records.

## User-goal mapping

"Exact-date" is enforced by `start_date: 1444-11-11` and date-applicable source
and polity records. "Source-pinned" is enforced by SHA-256 over every complete
canonical source record plus its exact locator and by checksums on both derived
assets. "Four-layer" is enforced by gap-free Grade-A geometry, politics,
hierarchy, and gazetteer-relationship coverage. Promotion replaces all 643
regional provisional assignments without weakening worldwide non-public gates.

## Tests run

- Deterministic packet generation: 643 assignments, nine polities, ten sources,
  25 assertions, six build features, two derived files, and zero M49
  corrections.
- Clean 22-region provisional assembly and QA: zero errors and 12 accepted
  provisional warnings.
- Review rendering and visual inspection; a clean second render reproduced
  accepted SHA-256
  `19ba39121d02d71d9c2e9dd58b269bc91339eb23c53ab69a879361ba87b7ec05`.
- `.venv/bin/pytest -q tests/test_m25c_global_certification.py tests/test_m25c_packet_signing.py`
  — 36 passed.
- `.venv/bin/pytest -q` — 368 passed in the sandbox; the three loopback-server
  cases were the only failures and failed solely because socket binding was
  denied. Those exact three tests passed outside the sandbox, for 371 passing
  tests across the complete suite.
- `uv build` — source distribution and wheel built successfully without build
  warnings.
- `.venv/bin/python -m py_compile scripts/generate-m25c-region-015-packet.py`
  and the targeted failure-oriented packet audit passed.
- JSON parsing, packet qualification, source-pin recomputation, derived-asset
  containment/checksum validation, `git diff --check`, and a staged `gitleaks`
  scan passed with no findings.

## Skipped tests

- Ordinary human acceptance, runtime compilation, certification, publication,
  and deployment are intentionally unavailable while 16 regional packets are
  incomplete and the provisional lineage rejects those paths.
- No lint or static-type command is configured in `pyproject.toml`. Python
  execution, the complete test suite, and deterministic regeneration cover the
  changed generator.

## Adversarial review

The failure-oriented review checked for incomplete assignment replacement,
duplicate IDs, placeholder evidence, non-applicable source dates, invalid
canonical pins, uncorroborated hard boundaries, escaping or stale derived
assets, missing four-layer rows, M49 leakage, and visual-hash instability. The
qualifier and regression suite rejected none of the final packet. A clean
full-world rebuild reproduced the visual digest and a separate clean QA build
reported zero errors. The 12 warnings are accepted because they identify the
still-provisional global lineage, incomplete remaining regions, and pending
ordinary review gates rather than defects in promoted region 015.

## Residual risk

The historical sheet is bounded by the cited scholarship and the accepted M23
r2 fabric. Saharan, Beja, Darfur-Kordofan, Dongola, and Alodia assignments use
coarse source-supported political sheets rather than unsupported precise local
frontiers. The hard Marinid-Zayyanid geometry is a checked shared-fabric
segment, not a newly digitized complete frontier. These limitations remain
visible to downstream reviewers through source records and uncertainty fields.

## Rollback note

Revert the shipping commit to remove the packet, generator, assets, tests, and
task records and restore the five-region provisional state. No public runtime
or deployment requires rollback.

## Next command

`$exec` — promote the next M25C region in the risk-first Asia, Africa/Americas,
and Oceania queue with an exact-date, source-pinned four-layer packet.
