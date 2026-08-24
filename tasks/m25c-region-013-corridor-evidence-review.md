# M25C Task 16 region 013 corridor evidence review

Status: **reviewed; rejected before implementation**
Review date: `2026-08-23`
Start date: `1444-11-11`
Scope: Mexico-Guatemala negative-control corridor and Central America positive-border gate

## Disposition

Do not implement a region `013` corridor reconstruction, positive border, or
border-applicability record from the current evidence packet. Preserve all
tolerances, assertions, assignments, candidate permissions, and release
permissions unchanged.

The packet establishes date-relevant Mexican states, Postclassic Maya
polities, lower-Central-American chiefdom systems, and twelve positive centers.
It does not supply an independently georeferenced, exact-date, two-sided
territorial line or a source-to-component mapping for the fixed
Mexico-Guatemala corridor. More decisively, the current generator resolves
every province representative point to Natural Earth `ADM0_A3` before
dispatching historical actors through country-specific branches, including
distinct `MEX` and `GTM` branches. Task 16 expressly forbids modern-country
dispatch.

The current stricter seam evaluator finds only partial eligible coverage and
correctly refuses to produce a ratio. Relabeling the same candidate-derived
geometry cannot qualify as historical remediation, and a positive border
cannot be manufactured from the resulting status edges.

This is a completed separate review, not an implementation approval. No old
value has an approved proposed replacement.

## Hash-bound review inputs

| Input | SHA-256 |
| --- | --- |
| `scripts/generate-m25c-region-013-packet.py` | `c6d1f63efb9e1f4da0fabbc74281ace92514324733be99049b5295a94df0a2c8` |
| `013-central-america-2026-08-16.json` | `ac5452926e0f9c12c1d61cf8451557819b6ecf3d120748aa9a212c697bf57618` |
| `assets/013/negative-controls.geojson` | `5a645eba71a8a465e99220822918fbf8c05fdb7d5643969060f431bccd132245` |
| assembled `historical-territory-status.json` | `bcdb93f3d828bf87643e36f4d848499bfb6e67da87c5f52fe3474fce301ff080` |
| assembled `build.geojson` | `351542020590ed5b473b8f198a8e776d1d967c804e19e729b721ca74a6801e72` |
| assembled `golden.json` | `2ef4feede67d460631ab70ffd43b295d921af8d1b109698370722a1b836db4b8` |
| assembled `start_date_preflight.json` | `f83d3f7ff250b4922d4b4cab2445d8ec775288bcdcfcdc120094d8f48991a1a2` |
| assembled `sidecars/adjacency.csv` | `31a9e46a40011dd0a17508cf75ca92acb5334f8253ea160a5617b8e5140e5ff9` |
| assembled `sidecars/location_fabric_manifest.json` | `65882451f8e079bebf10d35dfe3c0ace740c6e7c184cd7fcfc1ccf84b4bafbf6` |

The reviewed status artifact is schema `0.2.0`, artifact
`1.0.0-assembled.1`, compatibility revision `2`, and scenario
`official-1444-global-v1`. The fabric manifest records geometry revision `1`.
Any hash or revision change requires a new separate review.

## Assertion and predeclared measurement

The exact existing assertion is
`region-013-negative-modern-mexico-guatemala-seam`, using boundary feature
`forbidden-modern-mexico-guatemala-seam` and relation
`regional_status_boundary_matches_forbidden_modern_seam_ratio_lte`.

- Corridor: fixed `75 km`
- Unit: ratio
- Maximum: fixed `0.20`
- Reference and usable length: `895.8332466578588 km`
- Covered reference: `45.04742428512243 km`
- Coverage ratio: `0.05028550174174008`
- Matched eligible-transition length: `0.0 km`
- Measurement: null; non-executable
- Transitions: `14`
- Normal samples: `180`
- Missing side samples: `171`; ambiguous side samples: `0`
- Unknown-required-facet rejections: `197`
- Result: fail closed

The current preflight consequently retains
`MISSING_POSITIVE_BORDER_ASSERTION`, `NON_EXECUTABLE_SEAM_ASSERTION`,
`SPATIAL_ASSERTION_FAILED`, and downstream `UNCERTIFIED_A_GRADE` for region
`013`. The pre-phase-1 ratio is not a current executable result and must not be
used to approve edits under the stricter complete-coverage contract.

## Exact affected-component inventory

The evaluator reports no eligible affected components. The only component
resolved by deterministic left and right sampling is
`cmp-prv_981651d83dbca8a120b9`; both sides resolve to that same component. Its
current value is `scenario-kiche-state` with `administered`, `habitable`,
`resident`, `nucleated`, and `polity_associated` facets. No proposed value is
approved.

The full region contains 605 components: 38 administered/nucleated polity
rows, 82 decentralized/nucleated community rows, 285
decentralized/dispersed community rows, three uninhabited rows, and 197
all-unknown rows. The seam evaluator rejects 197 unknown-facet components
relevant to its corridor search. A single same-component sampled island cannot
stand in for complete two-sided corridor coverage.

Every assignment in the packet is first classified by Natural Earth country.
The `MEX` branch then chooses Mexican and Maya actors by longitude/latitude,
while the `GTM` branch separately chooses Peten-Belize Maya, K'iche', or
highland Maya actors. None of the reviewed locators enumerates corridor
component IDs, assigns both sides independently of `ADM0_A3`, or supplies a
transformation and error budget from historical geometry to the component
fabric.

## Evidence review

The relevant pinned locators are:

| Source pin | Packet SHA-256 | What it supports | What it does not support |
| --- | --- | --- | --- |
| `regional-survey-013` | `4061294f869d96b256baeccc73fbeb043a9ca0ccb34092f07441a3dac4a804db` | Broad `1400-1600` Maya-area chronology and Postclassic centers | A complete exact-date corridor fabric or component mapping |
| `regional-survey-029` | `01ea7b805c48a24a8a79662fe19bfdc42d6021b5aa09e26a9ed55d0332b7e69d` | Broad `1400-1500` lower-Central-American cultures, chiefdoms, and events | A Mexico-Guatemala territorial line |
| `loc-mayance-nations-map` | `fea17ec81060f245d49cc0bf4fc6e1a918ba98129d483fba31eb9ca2f32afb7a` | Mayan nations, languages, place names, and routes over an approximately `1000-1500` span | An exact `1444-11-11` two-sided political boundary or packet-supplied georeferencing |
| `shepherd-historical-atlas` | `7a2d80f5859128c0128953b4eeae68d464cfc2dad0878265f9c558f50868c437` | A public-domain atlas scan and broad Mexico/Central America plate | An enumerated plate extraction, dated transformation, residual, or component binding |
| `smithsonian-handbook-central-america` | `059ba56c4a508caf8dbb412b95087e23b78dfe37825c66a97c157afd13670277` | Broad political organization and regional-map context | A day-precise frontier, complete corridor mask, or error budget |
| `penn-time-beyond-kings` | `c8ee11ec49c1d267800f35f69543cf1ec7ba6e02bb64901971f613675f6e18b4` | Postclassic political transformation in Yucatan and the Maya Highlands | An exhaustive Mexico-Guatemala corridor mapping |
| `natural-earth-admin0-5.1.1-region-013` | `14a271bb1b153c53c4277c81e33e6e59e39160d5997950a879d65418f8db57d4` | The modern `MEX-GTM` negative-control reference only | Any positive historical actor assignment or frontier |

The repository's `2026-08-14` access audit records both regional surveys as
reachable through browser retrieval after automated access rejection and the
Shepherd atlas as reachable by automated retrieval. The review makes no claim
beyond the packet's pinned locators and the repository's already reviewed
source record.

The packet has twelve point build features for checked centers, no historical
boundary feature, and no historical derived file. Its only boundary and only
derived file are the modern Mexico-Guatemala negative control. Every
historical source records an empty transformation and derived-artifact list;
all but the Shepherd scan are citation/link-only. Thus the packet contains
neither reusable historical linework nor a provenance chain from a source map
to the current component geometry.

## Rejection reasons

1. The generator's `nearest_country`/`final_actor` path makes Natural Earth
   `ADM0_A3` membership an input to every historical actor assignment. Its
   explicit `MEX`, `GTM`, and neighboring-country branches violate the gate
   against modern-country dispatch.
2. Only `5.028550%` of the usable seam is covered by eligible status evidence;
   171 deterministic side samples are missing. The assertion is therefore
   non-executable under the approved complete-coverage contract.
3. The evidence has no independently derived exact-date line, two-sided mask,
   source control points, transformation, residual, or predeclared error
   budget for `1444-11-11`.
4. The evidence-to-record mapping is global and coarse. It cannot justify an
   enumerated old-to-new value for any corridor component, much less the
   unknown corridor coverage that must be reconstructed.
5. Nojpeten, Q'umarkaj, and the other checked centers prove positive
   locations, not a political border. A current status edge is
   candidate-derived and cannot validate itself as an independent
   positive-border assertion.
6. `not_applicable` is also unsupported. The packet models multiple bounded
   states and polities and supplies no complete land-adjacent actor-pair audit.

## Required replacement packet

A future region `013` packet may be reviewed only if it supplies all of the
following before edits:

- one exact claimed historical relation, not merely actor coexistence, a
  center, modern membership, language distribution, or later extent;
- independently derived and date-valid linework, a two-sided mask, or an
  explicit source-based corridor fabric spanning the full usable seam;
- exact locators, licensing, transformations, control points, residuals, and a
  fixed error budget;
- an exhaustive mapping from evidence to every proposed component old/new
  value, including relationships and all five facets;
- confirmation, demonstrable from the generator, that neither modern-country
  dispatch nor candidate-derived geometry chooses historical values;
- snapshot hashes, the fixed measurement and tolerance, expected affected and
  neighboring QA changes, and an independent hash review; and
- for a `not_applicable` proposal, the separately required complete
  land-adjacency disposition bound to positive historical anchors.

Until then, expected QA impact is exactly zero: no finding is cleared, no
component changes, and no review, certification, runtime, publication, or
deployment permission changes.
