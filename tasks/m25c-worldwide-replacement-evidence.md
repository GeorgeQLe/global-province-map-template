# M25C worldwide replacement evidence before Task 17

Status: **independently reviewed; partial acceptance; supplemental evidence required; not implemented**

Date: 2026-08-24

## Decision boundary

This task obtains a new independent geometry source and turns the frozen 56
ordinary-QA errors into separately hash-bound approval surfaces. It does not
approve its own research, mutate any regional packet or assembled artifact,
change a tolerance, accept the pending-review warning, or advance Task 17.

The exact baseline remains:

| Finding | Count |
| --- | ---: |
| `BORDER_APPLICABILITY_NOT_QUALIFIED` | 4 |
| `MISSING_POSITIVE_BORDER_ASSERTION` | 18 |
| `NON_EXECUTABLE_SEAM_ASSERTION` | 8 |
| `SPATIAL_ASSERTION_FAILED` | 13 |
| `UNCERTIFIED_A_GRADE` | 13 |
| **Total** | **56** |

## New source and qualification

Seshat's Cliopatria `v0.2.0` is pinned to commit
`ad28a691b7c07c1fca89d0e0636d324667d2a258`, archive SHA-256
`d01ae3a20d358cc5d54f69d9d725d390767d9c8759ac89ad6f90c58d106f3370`,
and unpacked-GeoJSON SHA-256
`5df3b5868cfab8f76030853fa2346ed3cd71171ad807b6f72d783ee2dce6839e`.
The 2025 *Scientific Data* method paper is peer reviewed and the data is CC BY
4.0. The authors document source-map reconstruction, specialist regional
references, expert Seshat review, native EPSG:4326 output, approximately
`0.07°` smoothing, and unquantified historical-border uncertainty. The
deterministic slice contains all and only 144 records whose inclusive year
range contains 1444.

The packet proposes a `20 km` source-native error budget. This is not silently
accepted: the reviewer must decide whether it adequately covers the published
native resolution and uncertainty for each proposed use.

## Independently approvable surfaces

### Direct historical borders

These eight candidates are exact shared-boundary intersections of two untouched
same-snapshot source polygons. No modern control or assembled-candidate edge
selects the result.

| Region | Source pair |
| --- | --- |
| `014` | Ethiopian Empire / Adal Sultanate |
| `015` | Marinid Sultanate / Zayyanid dynasty |
| `030` | Ming Dynasty / Four Oirats |
| `034` | Vijayanagara Empire / Bahmani Sultanate |
| `035` | Khmer Empire / Ayutthaya Kingdom |
| `039` | Kingdom of Portugal / Crown of Castile |
| `143` | Chagatai Khanate / Timurid Empire |
| `145` | Rasulid Dynasty / Mamluk Sultanate |

### Border-applicability candidates

The schema-valid candidate document keeps every decision unsigned. It binds the
complete assembled component inventory, source-record hashes, passing capital
anchors, and an exhaustive current land-adjacent cross-actor audit.

| Region | Proposed reason | Components | Cross-actor pairs |
| --- | --- | ---: | ---: |
| `005` | `evidence_supports_zone_not_line` | 2,211 | 26 |
| `011` | `evidence_supports_zone_not_line` | 639 | 34 |
| `013` | `non_territorial_fabric` | 605 | 45 |
| `017` | `evidence_supports_zone_not_line` | 528 | 22 |
| `018` | `non_territorial_fabric` | 225 | 10 |
| `021` | `non_territorial_fabric` | 3,986 | 19 |
| `029` | `non_territorial_fabric` | 396 | 2 |
| `053` | `non_territorial_fabric` | 1,195 | 15 |
| `054` | `evidence_supports_zone_not_line` | 414 | 7 |
| `061` | `no_land_adjacency` | 183 | 0 |

Every nonzero pair is enumerated with both actors and all incident component
IDs. The pair disposition is a proposal matching the regional reason, not a
self-approval. Region `061` now includes the seven formerly omitted Tokelau
components and independently reproduces zero cross-actor land pairs.

### Corridor component dossiers

One dossier per affected region includes every frozen finding and every
component within the exact projected 75 km modern-control corridor. Each row
binds current actor, all five facets, relationships, evidence IDs, distance to
the control, and the untouched Cliopatria representative-point result. The 18
dossiers contain all 56 findings exactly once.

Source silence is never promoted to historical truth. Rows marked
`outside_cliopatria_polity_coverage` or `overlapping_polities` require an
explicit decision and cannot authorize an edit by inference. This preserves
the stricter Task 16 rejection rule while still making the new positive
geometry and corroborating component evidence reviewable.

## Expected impact if approved and implemented

- The eight direct candidates provide independent, date-valid positive-border
  geometry for their eight regions.
- The ten applicability candidates provide a decision route for the other ten
  missing-positive findings, including the four existing fail-closed records.
- The component dossiers provide exact evidence-to-component inputs for serial
  seam/status remediation; they do not claim that partial source coverage is a
  completed remap.
- Approval alone changes no QA result. Only a later serial implementation,
  duplicate regeneration, affected/neighboring/worldwide QA, and zero-error
  preflight can open Task 17.

## Reproduction and verification

```bash
.venv/bin/python scripts/generate-m25c-replacement-evidence.py \
  --cliopatria-input /path/to/cliopatria_polities_only.geojson
.venv/bin/pytest -q tests/test_m25c_replacement_evidence.py
```

The generator refuses source drift. The tests verify source dates, line
geometry, schema validity, record hashes, artifact hashes, all-region coverage,
the exact 56-finding accounting, and the unchanged Task 17 state.

## Requested independent decisions

1. Accept or reject Cliopatria `v0.2.0` as an independent academic geometry
   source for this pass and accept or amend the proposed `20 km` error budget.
2. Decide each of the eight direct-border candidates independently.
3. Decide each of the ten applicability records independently, including every
   enumerated cross-actor pair disposition.
4. For each corridor dossier, approve only explicitly covered component rows;
   require supplemental evidence for every uncovered or overlapping row before
   implementation.

## Independent review outcome

The record-by-record review is complete in
`tasks/m25c-worldwide-replacement-evidence-independent-review.md`. Cliopatria
and the operational 20 km mapping budget are accepted with explicit scope
limits. All eight direct-border candidates and region `061`'s exhaustive
`no_land_adjacency` record are accepted. The other nine applicability records
and all 180 of their actor-pair dispositions require pair-specific supplemental
evidence. Of 757 corridor rows, 245 single-polity representative-point matches
are accepted narrowly and 512 uncovered or overlapping rows require
supplemental evidence.

At the frozen-finding level the result is 13 accepts, zero rejects, and 43
supplemental-evidence requests. No implementation, candidate mutation,
tolerance change, permission change, or Task 17 advancement is authorized by
the review itself.
