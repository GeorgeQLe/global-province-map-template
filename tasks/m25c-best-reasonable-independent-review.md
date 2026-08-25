# M25C best-reasonable evidence independent review

Status: **reviewed record by record; narrow Grade C acceptance; not implemented**

Review date: `2026-08-24`
Start date: `1444-11-11`
Reviewer: `Codex independent evidence review`

## Decision boundary

This review binds the checked-in best-reasonable manifest and all 692 evidence
records without changing a regional packet, component, assignment, source
tolerance, assembled artifact, permission, QA result, or Task 17 state. The
machine-readable decisions are in
`research/start-dates/1444-global-v1/replacement-evidence/best-reasonable-v1/review-decisions.json`.
Every decision includes its source record hash and its own canonical hash.

The review does not equate the packet's `medium` label with acceptance. It
accepts only the scope actually observable from the source surface and uses
`U` where even a documented approximate reconstruction is unsupported.

## Pair decisions

All **180 pair records are rejected** for implementation, including all 127
medium-confidence rows. The records bind exact pair and incident-component
IDs, but attach every regional source ID to every pair without mapping a
qualifying claim to either actor. Their spatial summaries aggregate names and
counts and do not preserve a feature-to-actor or feature-to-each-component
mapping. The incident geometry and adjacency are also the frozen candidate's,
not independently derived linework.

This does not claim that the proposed `evidence_supports_zone_not_line` or
`non_territorial_fabric` dispositions are historically false. It means this
packet does not independently prove them. Pair geometry grade is therefore
`not_applicable`, and all twelve pair-routed finding records remain rejected.

## Component decisions

A component is accepted only when a named approximate polygon contains its
representative point in both the pinned 1400 and 1492 snapshots. This is the
narrowest repeatable signal the packet exposes across both temporal brackets.
It supports only a disclosed **Grade C geometry scaffold**:

- 306 component records: `accept`, geometry grade `C`;
- 206 component records: `reject`, geometry grade `U`.

Grade C does not accept a current political actor, any of the five facets, a
relationship, a complete polygon, or a source-derived edge. Known gaps remain:
the snapshots are 44 years before and 48 years after the target date, only a
representative point was tested, `BORDERPRECISION=1` is approximate, and no
edge error or whole-component containment measurement exists.

The OHM `sourced_feature_ids` flag does not raise any row to Grade B. The
sidecar packet omits the feature's actual source value and enough date-lineage
detail for independent qualification. The fourteen component rows touching a
source-tagged OHM feature are decided by the same two-bracket rule as every
other row; none receives special promotion.

| Region | Grade C accept | Ungraded reject |
| --- | ---: | ---: |
| `005` | 10 | 12 |
| `011` | 3 | 15 |
| `013` | 1 | 15 |
| `014` | 25 | 0 |
| `015` | 4 | 14 |
| `017` | 36 | 0 |
| `018` | 32 | 0 |
| `021` | 140 | 93 |
| `029` | 10 | 1 |
| `034` | 15 | 13 |
| `035` | 2 | 14 |
| `039` | 3 | 3 |
| `053` | 18 | 0 |
| `054` | 0 | 5 |
| `061` | 1 | 0 |
| `143` | 4 | 4 |
| `145` | 2 | 17 |
| **Total** | **306** | **206** |

## Finding-route decisions

A component route is accepted only when every routed component is separately
accepted. Acceptance authorizes only a later serial, explicitly incomplete
Grade C reconstruction; it does not make a failed seam pass or clear the
Grade-A certification requirement. Every pair route is rejected because every
underlying pair record is rejected.

The eleven accepted Grade C routes are:

- regions `014`, `017`, and `018`: `NON_EXECUTABLE_SEAM_ASSERTION`,
  `SPATIAL_ASSERTION_FAILED`, and `UNCERTIFIED_A_GRADE`;
- region `053`: `SPATIAL_ASSERTION_FAILED` and `UNCERTIFIED_A_GRADE`.

The other 32 finding routes are rejected: twelve pair routes with geometry
grade `not_applicable` and twenty incomplete component routes with geometry
grade `U`.

## Honest-grade conclusion

No record qualifies for Grade A or Grade B. The accepted Grade C records can
support an honest provisional reconstruction with explicit gaps, but cannot
open Task 17 or the assembled-pass acceptance gate. Serial implementation must
preserve the exact review hashes, retain the downgrade, and regenerate
affected, neighboring, and worldwide QA before any further review.

## Verification

```bash
.venv/bin/python scripts/record-m25c-best-reasonable-review.py
.venv/bin/pytest -q \
  tests/test_m25c_best_reasonable_review.py \
  tests/test_m25c_best_reasonable_evidence.py \
  tests/test_m25c_replacement_evidence.py
```
