# M25C Eastern Europe Grade-A Promotion Ship Manifest

## User goal

Promote UN M49 region 151 (Eastern Europe) with an exact-date, source-pinned,
four-layer Grade-A evidence packet while preserving the non-public worldwide
certification boundary.

## Changed files

- `research/start-dates/1444-global-v1/regional-packets/151-eastern-europe-2026-08-15.json`
- `research/start-dates/1444-global-v1/regional-packets/README.md`
- `scripts/generate-m25c-region-151-packet.py`
- `tasks/history.md`
- `tasks/m25c-region-151-ship-manifest.md`
- `tasks/roadmap.md`
- `tasks/todo.md`
- `tests/test_m25c_global_certification.py`

## Outcome

The packet replaces all 2,178 region-151 provisional assignments, promotes all
four coverage rows to gap-free Grade A, replaces 15 polity records, pins ten
complete reviewed source records plus exact locators, and adds five executable
spatial assertions. Its `1444-11-11` interpretation explicitly postdates the
10 November Battle of Varna. The reviewed UN M49 sheet needs no correction and
retains the entire Russian Federation footprint required by the country-based
partition.

The worldwide provisional pass now contains 12 Grade-A rows. Nineteen regions
and 76 Grade-A rows still block ordinary review acceptance, certification,
runtime publication, and demo promotion.

## Per-file purpose

- The region-151 packet is the accepted, source-pinned Grade-A replacement.
- The regional README documents its exact-date and country-based M49 boundary.
- The region-151 generator reproduces the packet and fails closed on count drift.
- History records the promotion and accepted review digest.
- Roadmap and todo advance M25C to three promoted regions and route region 039.
- The certification test qualifies the real packet and checks its counts,
  post-Varna label, review digest, and absence of provisional assignment sources.
- This manifest records the shipping boundary, validation, risk, and rollback.

## User-goal mapping

"Exact-date" is enforced by `start_date: 1444-11-11`, date-applicable coverage
sources, and the post-Varna polity labels. "Source-pinned" is enforced by ten
SHA-256 hashes over each complete canonical source record plus its exact locator.
"Four-layer" is enforced by four gap-free Grade-A coverage rows and executable
geometry, politics, hierarchy, and gazetteer-relationship assertions. Promotion
is exercised by the worldwide merge and provisional QA, while the incomplete
global lineage remains explicitly non-certifiable.

## Validation

- Deterministic regional generator count contract: 2,178 assignments, 15
  polities, ten sources, five assertions, and zero M49 corrections.
- Full provisional worldwide generation and QA: zero errors and 12 expected
  provisional warnings.
- Region-151 review sheet rendered and visually inspected; accepted SHA-256
  `2ecf89be71b36d59ac8ea05c90e8dde5bff80c1e839003a67ec5311cf7cf5d2b`.
- Focused certification suite: 25 passed in 1.10 seconds.
- Complete repository suite: 367 passed in 45.55 seconds.

## Skipped tests

- Ordinary human acceptance, runtime compilation, certification, publication,
  and deployment were skipped because 19 regional packets remain incomplete;
  those gates must continue to reject this provisional worldwide lineage.
- No task-doc audit ran because `scripts/audit-task-docs.mjs` is absent.

## Adversarial review

The regional qualifier recomputed every canonical source pin, rejected any
provisional assignment source, checked all four Grade-A rows and date bounds,
and exercised the packet inside a complete 22-region assembly. Deterministic
regeneration was byte-identical. The rendered sheet was visually inspected for
M49 leakage; the apparent transcontinental Russia footprint and antimeridian
islands were retained because this repository's pinned M49 partition is
country-based and Russia has no separately classified M49 dependencies. A
changed-file private-key/provider-token scan and `git diff --check` passed.

## Residual risk and rollback

Historical interpretation is bounded by the cited sources and the accepted
M23 r2 fabric. M49 region 151 is country-based rather than purely geographic,
so the sheet intentionally spans Russia's Asian extent. The packet retains the
accepted scaffold's province-level political granularity rather than claiming
new hand-digitized borders across the entire transcontinental sheet.

## Rollback note

Revert the shipping commit to remove the region-151 packet, generator, tests,
and task records and restore the prior two-region provisional state. No public
runtime or deployment requires rollback because this lineage remains internal.

## Next command

`$exec` — promote M49 region 039 (Southern Europe) with the next exact-date,
source-pinned four-layer packet.
