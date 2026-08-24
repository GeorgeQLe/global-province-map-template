# M25C worldwide replacement-evidence independent review

Status: **reviewed record by record; partial acceptance; supplemental evidence required before implementation**

Review date: `2026-08-24`
Start date: `1444-11-11`
Reviewer: `Codex independent evidence review`

## Decision boundary

This review decides the frozen replacement-evidence surfaces without editing a
regional packet, assembled artifact, source tolerance, release permission, or
Task 17 state. Decisions are bound to the checked-in Cliopatria evidence tree
and the record hashes in its manifest. Any byte change requires a new review.

The three permitted decisions are `accept`, `reject`, and
`supplemental_evidence_required`. Acceptance means that the cited evidence is
sufficient to authorize the narrowly described later implementation; it does
not accept the resulting packet or waive regeneration and QA. A supplemental
decision is fail-closed and authorizes no edit.

## Source and error-budget decision

**Accept** Cliopatria `v0.2.0`, commit
`ad28a691b7c07c1fca89d0e0636d324667d2a258`, as an independent academic
geometry source for this pass. Its same-snapshot, year-inclusive polygons are
fit for candidate historical-polity coverage and shared-boundary derivation.
This acceptance does not turn source silence into absence, resolve overlapping
polities, or establish any facet other than polity coverage.

**Accept** `20 km` as an operational source-handling budget for this pass. It
comfortably exceeds the published approximately `0.07 degree` smoothing scale
at the affected latitudes. It is not a claim that Cliopatria's unquantified
historical-border uncertainty is at most 20 km, and it may not be used to move,
invent, join, or extrapolate a source line. The untouched source line remains
the evidence; the budget is only for mapping that line to the accepted fabric.

## Direct-border decisions

Each candidate below was considered separately. All eight are **accepted** as
soft, independently derived positive-border geometry because both named source
polygons cover 1444 and the candidate is their untouched shared-boundary
intersection. Later implementation must preserve the exact source geometry,
source intervals, provenance, and 20 km operational budget.

| Region | Source pair | Decision |
| --- | --- | --- |
| `014` | Ethiopian Empire / Adal Sultanate | `accept` |
| `015` | Marinid Sultanate / Zayyanid dynasty | `accept` |
| `030` | Ming Dynasty / Four Oirats | `accept` |
| `034` | Vijayanagara Empire / Bahmani Sultanate | `accept` |
| `035` | Khmer Empire / Ayutthaya Kingdom | `accept` |
| `039` | Kingdom of Portugal / Crown of Castile | `accept` |
| `143` | Chagatai Khanate / Timurid Empire | `accept` |
| `145` | Rasulid Dynasty / Mamluk Sultanate | `accept` |

## Applicability-record decisions

Region `061` is **accepted**. Its complete 183-component inventory, included
Tokelau correction, passing anchors, and exhaustive land-adjacency audit
independently reproduce zero cross-actor pairs. This supports only the exact
`no_land_adjacency` record; it does not assert cultural or political uniformity
and does not modify the negative control.

The other nine records are **supplemental evidence required**. Their exhaustive
audits establish that cross-actor pairs exist, but every pair is assigned the
same regional disposition without pair-specific cited evidence. A region-wide
label cannot independently decide whether each adjacency is territorial,
zonal, relational, contested, or an artifact of the current reconstruction.

| Region | Pairs | Proposed reason | Decision |
| --- | ---: | --- | --- |
| `005` | 26 | `evidence_supports_zone_not_line` | `supplemental_evidence_required` |
| `011` | 34 | `evidence_supports_zone_not_line` | `supplemental_evidence_required` |
| `013` | 45 | `non_territorial_fabric` | `supplemental_evidence_required` |
| `017` | 22 | `evidence_supports_zone_not_line` | `supplemental_evidence_required` |
| `018` | 10 | `non_territorial_fabric` | `supplemental_evidence_required` |
| `021` | 19 | `non_territorial_fabric` | `supplemental_evidence_required` |
| `029` | 2 | `non_territorial_fabric` | `supplemental_evidence_required` |
| `053` | 15 | `non_territorial_fabric` | `supplemental_evidence_required` |
| `054` | 7 | `evidence_supports_zone_not_line` | `supplemental_evidence_required` |
| `061` | 0 | `no_land_adjacency` | `accept` |

The decision shown for a nonzero region applies independently to every
enumerated `eligible_land_adjacent_actor_pairs` row in that record—180 pair
rows total, with no exception. Supplemental evidence must bind the exact actor
pair and incident component IDs and explain the appropriate border relation.
No pair disposition is approved by aggregation.

## Corridor-component decisions

Every one of the 757 corridor-component rows receives an explicit decision by
its frozen `source_classification`:

- Each of the 245 `single_polity` rows is **accepted** only for the named
  Cliopatria representative-point polity match. This does not independently
  accept all five current facets, relationships, or a whole-component polygon.
- Each of the 509 `outside_cliopatria_polity_coverage` rows is
  **supplemental evidence required**. Source silence cannot authorize an
  assignment or an unknown value.
- Each of the three `overlapping_polities` rows is **supplemental evidence
  required**. A representative point with multiple source matches cannot select
  one actor or relationship.

This classification-bound rule is exhaustive, deterministic, and has no
exceptions. It decides each hash-bound row independently while avoiding an
unsupported inference from one row to its neighbors.

| Region | Accepted `single_polity` rows | Supplemental rows |
| --- | ---: | ---: |
| `005` | 0 | 22 |
| `011` | 4 | 18 |
| `013` | 3 | 16 |
| `014` | 0 | 25 |
| `015` | 17 | 18 |
| `017` | 11 | 36 |
| `018` | 0 | 32 |
| `021` | 0 | 233 |
| `029` | 0 | 11 |
| `030` | 95 | 0 |
| `034` | 27 | 28 |
| `035` | 33 | 16 |
| `039` | 4 | 6 |
| `053` | 0 | 18 |
| `054` | 0 | 5 |
| `061` | 0 | 1 |
| `143` | 39 | 8 |
| `145` | 12 | 19 |
| **Total** | **245** | **512** |

## Frozen-finding decisions

The 56 frozen finding records were then decided independently. A finding is
accepted only when every evidence surface needed for its narrow remediation is
accepted. Partial corridor coverage is not enough to accept a seam or Grade-A
remediation.

| Region | Frozen finding record | Decision |
| --- | --- | --- |
| `005` | `MISSING_POSITIVE_BORDER_ASSERTION` | `supplemental_evidence_required` |
| `005` | `SPATIAL_ASSERTION_FAILED` | `supplemental_evidence_required` |
| `005` | `UNCERTIFIED_A_GRADE` | `supplemental_evidence_required` |
| `011` | `MISSING_POSITIVE_BORDER_ASSERTION` | `supplemental_evidence_required` |
| `011` | `NON_EXECUTABLE_SEAM_ASSERTION` | `supplemental_evidence_required` |
| `011` | `SPATIAL_ASSERTION_FAILED` | `supplemental_evidence_required` |
| `011` | `UNCERTIFIED_A_GRADE` | `supplemental_evidence_required` |
| `013` | `MISSING_POSITIVE_BORDER_ASSERTION` | `supplemental_evidence_required` |
| `013` | `NON_EXECUTABLE_SEAM_ASSERTION` | `supplemental_evidence_required` |
| `013` | `SPATIAL_ASSERTION_FAILED` | `supplemental_evidence_required` |
| `013` | `UNCERTIFIED_A_GRADE` | `supplemental_evidence_required` |
| `014` | `MISSING_POSITIVE_BORDER_ASSERTION` | `accept` |
| `014` | `NON_EXECUTABLE_SEAM_ASSERTION` | `supplemental_evidence_required` |
| `014` | `SPATIAL_ASSERTION_FAILED` | `supplemental_evidence_required` |
| `014` | `UNCERTIFIED_A_GRADE` | `supplemental_evidence_required` |
| `015` | `MISSING_POSITIVE_BORDER_ASSERTION` | `accept` |
| `015` | `SPATIAL_ASSERTION_FAILED` | `supplemental_evidence_required` |
| `015` | `UNCERTIFIED_A_GRADE` | `supplemental_evidence_required` |
| `017` | `MISSING_POSITIVE_BORDER_ASSERTION` | `supplemental_evidence_required` |
| `017` | `NON_EXECUTABLE_SEAM_ASSERTION` | `supplemental_evidence_required` |
| `017` | `SPATIAL_ASSERTION_FAILED` | `supplemental_evidence_required` |
| `017` | `UNCERTIFIED_A_GRADE` | `supplemental_evidence_required` |
| `018` | `MISSING_POSITIVE_BORDER_ASSERTION` | `supplemental_evidence_required` |
| `018` | `NON_EXECUTABLE_SEAM_ASSERTION` | `supplemental_evidence_required` |
| `018` | `SPATIAL_ASSERTION_FAILED` | `supplemental_evidence_required` |
| `018` | `UNCERTIFIED_A_GRADE` | `supplemental_evidence_required` |
| `021` | `BORDER_APPLICABILITY_NOT_QUALIFIED` | `supplemental_evidence_required` |
| `021` | `MISSING_POSITIVE_BORDER_ASSERTION` | `supplemental_evidence_required` |
| `029` | `MISSING_POSITIVE_BORDER_ASSERTION` | `supplemental_evidence_required` |
| `030` | `MISSING_POSITIVE_BORDER_ASSERTION` | `accept` |
| `030` | `NON_EXECUTABLE_SEAM_ASSERTION` | `accept` |
| `030` | `SPATIAL_ASSERTION_FAILED` | `accept` |
| `030` | `UNCERTIFIED_A_GRADE` | `accept` |
| `034` | `MISSING_POSITIVE_BORDER_ASSERTION` | `accept` |
| `034` | `SPATIAL_ASSERTION_FAILED` | `supplemental_evidence_required` |
| `034` | `UNCERTIFIED_A_GRADE` | `supplemental_evidence_required` |
| `035` | `MISSING_POSITIVE_BORDER_ASSERTION` | `accept` |
| `035` | `NON_EXECUTABLE_SEAM_ASSERTION` | `supplemental_evidence_required` |
| `035` | `SPATIAL_ASSERTION_FAILED` | `supplemental_evidence_required` |
| `035` | `UNCERTIFIED_A_GRADE` | `supplemental_evidence_required` |
| `039` | `MISSING_POSITIVE_BORDER_ASSERTION` | `accept` |
| `053` | `BORDER_APPLICABILITY_NOT_QUALIFIED` | `supplemental_evidence_required` |
| `053` | `MISSING_POSITIVE_BORDER_ASSERTION` | `supplemental_evidence_required` |
| `053` | `SPATIAL_ASSERTION_FAILED` | `supplemental_evidence_required` |
| `053` | `UNCERTIFIED_A_GRADE` | `supplemental_evidence_required` |
| `054` | `BORDER_APPLICABILITY_NOT_QUALIFIED` | `supplemental_evidence_required` |
| `054` | `MISSING_POSITIVE_BORDER_ASSERTION` | `supplemental_evidence_required` |
| `061` | `BORDER_APPLICABILITY_NOT_QUALIFIED` | `accept` |
| `061` | `MISSING_POSITIVE_BORDER_ASSERTION` | `accept` |
| `143` | `MISSING_POSITIVE_BORDER_ASSERTION` | `accept` |
| `143` | `NON_EXECUTABLE_SEAM_ASSERTION` | `supplemental_evidence_required` |
| `143` | `SPATIAL_ASSERTION_FAILED` | `supplemental_evidence_required` |
| `143` | `UNCERTIFIED_A_GRADE` | `supplemental_evidence_required` |
| `145` | `MISSING_POSITIVE_BORDER_ASSERTION` | `accept` |
| `145` | `SPATIAL_ASSERTION_FAILED` | `supplemental_evidence_required` |
| `145` | `UNCERTIFIED_A_GRADE` | `supplemental_evidence_required` |

Totals: **13 accept**, **0 reject**, **43 supplemental evidence required**.

## Implementation gate

No implementation may begin as a worldwide bundle. The accepted surfaces are
eligible only for later serial changes with their exact hashes and stated
scope. The 43 supplemental findings, 180 nonzero actor-pair dispositions, and
512 uncovered or overlapping component rows remain fail-closed. Ordinary QA is
therefore not clean, and Task 17 remains blocked.
