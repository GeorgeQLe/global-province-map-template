# M25C best-reasonable supplemental evidence

Status: **obtained and independently reviewed; region 014 routes implemented at Grade C**

Date: `2026-08-24`

## Goal and standard

Obtain a practical, pair-specific and component-specific best-available
evidence attempt for the 43 deferred frozen findings without describing
approximate reconstruction as surveyed precision. This is deliberately less
absolute than the earlier exact-source search, but it remains explicit about
confidence, source gaps, and the distinction between research and approval.

## Evidence obtained

The generated packet at
`research/start-dates/1444-global-v1/replacement-evidence/best-reasonable-v1/`
contains:

- exactly 180 hash-bound pair records covering every nonzero frozen
  applicability pair and its exact incident component IDs;
- exactly 512 hash-bound component records covering all 509 outside-Cliopatria
  and three overlapping-Cliopatria corridor rows;
- exactly 43 finding routes binding the deferred finding to its required pair
  or component evidence records;
- 127 medium- and 53 low-confidence pair records;
- 312 medium- and 200 low-confidence component records.

Every record cites the reviewed regional source IDs and adds spatial
corroboration from pinned Historical Basemaps 1400/1492 snapshots and an
exact-date OpenHistoricalMap query. The OHM query returned 116 relations; 113
could be polygonized and 21 of those carry nonempty source tags. Feature-level
OHM evidence is stronger only when its source and date lineage survive review.

## Reasonable-use policy

Historical Basemaps is usable as approximate bracketing evidence only: the
snapshots are 44 years before and 48 years after the target date and their
relevant geometry uses ordinal `BORDERPRECISION=1`. It may corroborate a
frontier zone or non-territorial fabric but cannot establish an exact 1444
line. OpenHistoricalMap is exact-date discoverable but unevenly sourced, so an
unsourced OHM feature remains corroboration rather than decisive evidence.

Accordingly:

- `medium` and `low` are evidence-strength labels, not approval decisions;
- a best-reasonable review may approve a zonal applicability record or a
  documented Grade-B/C reconstruction;
- no low-confidence record may be silently promoted to Grade A;
- the assembled-pass contract still requires gap-free Grade A, so accepting a
  Grade-B/C reconstruction can produce an honest provisional result but cannot
  by itself open Task 17.

## Non-implementation boundary

No regional packet, assignment, status, source tolerance, assembled artifact,
QA result, permission, or Task 17 state changes in this research step. Every
record remains `pending_independent_review`; serial implementation can begin
only for separately accepted records and must regenerate pair inventories and
affected, neighboring, and worldwide QA.

## Verification

```bash
.venv/bin/pytest -q \
  tests/test_m25c_best_reasonable_evidence.py \
  tests/test_m25c_replacement_evidence.py
```

The focused suite verifies all source/output hashes, exact 43/180/512
accounting, frozen pair/component identity, confidence totals, finding-type
totals, and the pending-review boundary.

## Independent-review result

The record-by-record review rejects all 180 pair dispositions, accepts 306
component records only as documented Grade C scaffolding, and rejects 206
component records as ungraded. Eleven complete component-only finding routes
may proceed serially at Grade C; 32 routes remain rejected. No record qualifies
for Grade A or Grade B. See
`tasks/m25c-best-reasonable-independent-review.md` and the hash-bound
`review-decisions.json` sidecar.

Region `014`'s three accepted routes are now implemented with the exact review
hashes and recorded Grade C gaps; eight accepted routes remain unimplemented.
