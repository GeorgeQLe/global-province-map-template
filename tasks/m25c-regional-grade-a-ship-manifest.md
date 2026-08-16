# M25C First Regional Grade-A Promotions Ship Manifest

## User goal

Promote the first two M25C worldwide evidence regions from provisional records
to exact-date, source-pinned, four-layer Grade-A packets; harden regional packet
qualification and assembly; and keep the incomplete worldwide lineage explicitly
non-public and non-certifiable.

## Changed files

- `research/start-dates/1444-global-v1/anomaly_inventory.json`
- `research/start-dates/1444-global-v1/census-research.json`
- `research/start-dates/1444-global-v1/regional-packets/README.md`
- `research/start-dates/1444-global-v1/regional-packets/154-northern-europe-2026-08-15.json`
- `research/start-dates/1444-global-v1/regional-packets/155-western-europe-2026-08-15.json`
- `research/start-dates/1444-global-v1/regional-packets/assets/154/boundaries.geojson`
- `research/start-dates/1444-global-v1/regional-packets/assets/154/negative-controls.geojson`
- `research/start-dates/1444-global-v1/regional-packets/assets/154/polity-masks.geojson`
- `research/start-dates/1444-global-v1/source-access-audit.json`
- `scripts/generate-m25c-provisional-pass.py`
- `scripts/generate-m25c-region-154-packet.py`
- `scripts/generate-m25c-region-155-packet.py`
- `tasks/history.md`
- `tasks/m25c-regional-grade-a-ship-manifest.md`
- `tasks/roadmap.md`
- `tasks/todo.md`
- `tests/test_m25c_global_certification.py`

## Per-file purpose

- The anomaly inventory and census research preserve the accepted 242-cell
  Kalmar/Luebeck/Lancastrian reconciliation that region 154 consumes.
- The regional README documents the accepted region-154 and region-155 packet
  boundaries, M49 corrections, source-pin policy, and checked asset contract.
- The region-154 packet replaces 1,367 Northern Europe assignments, supplies 18
  reviewed polities and 23 executable assertions, and declares one Bouvet M49
  correction plus three checksum-pinned derived assets.
- The region-155 packet replaces 385 Western Europe assignments, supplies 19
  reviewed polities and 20 executable assertions, and corrects 39 locations
  whose sovereign metadata placed them in the wrong geographic M49 region.
- The three region-154 GeoJSON assets preserve checked hard boundaries, negative
  controls, and polity masks under packet-relative checksums.
- The source-access audit records the reviewed Cambridge Kalmar source route.
- The provisional-pass generator applies packet M49 overrides before grouping,
  merges authoritative sources and polities, admits checked capital points,
  copies only qualified packet assets, and reports the remaining regional gaps.
- The two regional generators reproduce the accepted packets and their pinned
  source, assignment, polity, assertion, correction, and asset counts.
- The M25C tests exercise both accepted packets and reject tampered source pins,
  missing or escaping assets, and invalid or duplicate capital features.
- Todo, roadmap, history, and this manifest record the two completed promotions,
  the unchanged non-public boundary, validation, risk, rollback, and next work.

## User-goal mapping

Regions 154 and 155 now replace provisional evidence across geometry, politics,
hierarchy, and gazetteer relationships without weakening ordinary certification.
Qualification binds source records to exact locators, validates independent and
date-applicable derived assets, and applies geographic corrections before the
worldwide pass is grouped. The assembled coverage remains honest: 8 Grade-A
rows are promoted and 80 rows across 20 regions still block certification.

## Tests run

- Executable complete suite: `uv run --extra dev pytest -q` — 366 passed in
  50.42 seconds, with no failures or warnings.
- Executable deterministic regional generation: both regional generators ran
  against their preserved baselines; `cmp` proved the two packets and all three
  region-154 assets byte-identical to the checked-in files.
- Executable worldwide assembly/QA: `generate-m25c-provisional-pass.py` assembled
  a fresh 288 MB pass with both packet inputs; provisional QA passed with zero
  errors and 12 expected evidence/review warnings. Coverage contained exactly
  8 Grade-A, 20 Grade-B, and 60 Grade-C rows, with all 20 remaining regions named.
- Executable syntax/data validation: all three changed generators passed
  `py_compile`; all changed JSON and GeoJSON files passed `jq empty`.
- Source hygiene: `git diff --check` and the changed-file private-key/provider
  token pattern scan passed.

## Skipped tests

- Ordinary research acceptance, runtime compilation, certification, publication,
  and deployment were not run because 20 regions and 80 Grade-A rows remain by
  design; those gates must continue to reject this provisional lineage.
- The accepted regional review SVGs were not re-rendered during wrap-up. Their
  accepted SHA-256 digests remain pinned in the packets, while the regenerated
  packet bytes, derived geometry, executable spatial gates, and full provisional
  QA were reverified.
- No task-doc audit ran because `scripts/audit-task-docs.mjs` is absent.

## Adversarial review

Targeted review exercised canonical source-pin tampering, derived-file checksum
and containment failures, duplicate capital rejection, authoritative source and
polity replacement, M49 correction ordering, copied-asset containment, and the
unchanged provisional certification boundary. No unresolved finding remains.
The 12 provisional-QA warnings are accepted and expected: they enumerate the
remaining evidence grades, missing regional assertion/review coverage, provisional
scenario evidence, and absent independent worldwide acceptance.

## Residual risk

The regional generators depend on preserved local baseline assemblies to
reproduce their checked-in packets. Historical interpretation remains limited to
the cited and reviewed region-154 and region-155 claims. The worldwide lineage is
not releasable until all 20 remaining regional packets replace the 80 provisional
coverage rows and the ordinary human-review, runtime, and certification gates pass.

## Rollback note

Revert the shipping commit to remove both Grade-A packets, their derived assets,
the packet-generation/qualification changes, and the associated task records;
the prior provisional worldwide pass then remains the active non-public baseline.

## Next command

`$exec` — promote M49 region 151 (Eastern Europe) with the next exact-date,
source-pinned four-layer packet.
