# M25C Task 16 region 015 corridor evidence review

Status: **reviewed; rejected before implementation**
Review date: `2026-08-23`
Start date: `1444-11-11`
Scope: Morocco-Algeria negative-control corridor and Northern Africa positive-border gate

## Disposition

Do not implement a region `015` corridor reconstruction, positive border, or
border-applicability record from the current evidence packet. Preserve all
tolerances, assertions, assignments, candidate permissions, and release
permissions unchanged.

The packet establishes date-relevant Marinid, Zayyanid, Hafsid, Mamluk,
Saharan, Beja, Darfur-Kordofan, Dongola, and Alodia actors and six positive
centers. It does not supply an independently georeferenced, exact-date,
two-sided territorial line or a source-to-component mapping for the fixed
Morocco-Algeria corridor.

The current generator begins each replacement with the baseline
`owner_polity_id`. Its `final_actor` function returns every non-Mamluk baseline
actor unchanged, including the Marinid and Zayyanid actors on this corridor;
only the southern Mamluk sheet receives coordinate-based subdivision. No
historical source geometry chooses the Maghrib actor split. The current
executable result reproduces the complete modern `MAR-DZA` seam at ratio
`1.0`, confirming that the inherited modern-country split remains in the
candidate. Task 16 expressly forbids modern-country dispatch or relabeling the
same candidate-derived geometry.

The previously generated Marinid-Zayyanid border cannot qualify the packet:
it was extracted from the candidate's own shared province edge, compared back
to itself, and retired as circular evidence. The current packet correctly
contains no historical boundary or historical derived asset.

This is a completed separate review, not an implementation approval. No old
value has an approved proposed replacement.

## Hash-bound review inputs

| Input | SHA-256 |
| --- | --- |
| `scripts/generate-m25c-region-015-packet.py` | `db1290cf85d6118ce3715b2c01a76519ca173dbff6b134c5690eb10cc5b69776` |
| `015-northern-africa-2026-08-16.json` | `3d5e9e73ffaafb4358bfcf634e05546bbaac51c83a6f85b6b25afc22b65588fa` |
| `assets/015/negative-controls.geojson` | `100d0fd0a07fd886da8459df45acd56dddcde31904a2b1a91955bd8a006cde36` |
| assembled `historical-territory-status.json` | `bcdb93f3d828bf87643e36f4d848499bfb6e67da87c5f52fe3474fce301ff080` |
| assembled `build.geojson` | `351542020590ed5b473b8f198a8e776d1d967c804e19e729b721ca74a6801e72` |
| assembled `golden.json` | `2ef4feede67d460631ab70ffd43b295d921af8d1b109698370722a1b836db4b8` |
| assembled `start_date_preflight.json` | `45d51cb813d20603b651bc79822b32cabea0d7d8e216627fd9af2f91836668d7` |
| assembled `sidecars/adjacency.csv` | `31a9e46a40011dd0a17508cf75ca92acb5334f8253ea160a5617b8e5140e5ff9` |
| assembled `sidecars/location_fabric_manifest.json` | `65882451f8e079bebf10d35dfe3c0ace740c6e7c184cd7fcfc1ccf84b4bafbf6` |

The reviewed status artifact is schema `0.2.0`, artifact
`1.0.0-assembled.1`, compatibility revision `2`, and scenario
`official-1444-global-v1`. The fabric manifest records geometry revision `1`.
Any hash or revision change requires a new separate review.

## Assertion and predeclared measurement

The exact existing assertion is
`region-015-negative-modern-morocco-algeria-seam`, using boundary feature
`forbidden-modern-morocco-algeria-seam` and relation
`regional_status_boundary_matches_forbidden_modern_seam_ratio_lte`.

- Corridor: fixed `75 km`
- Unit: ratio
- Maximum: fixed `0.20`
- Reference, usable, and covered length: `1572.8105766747265 km`
- Coverage ratio: `1.0`
- Matched eligible-transition length: `1572.8105766747265 km`
- Measurement: `1.0`
- Transitions: `8`
- Normal samples: `315`
- Missing side samples: `0`; ambiguous side samples: `0`
- Unknown-required-facet rejections: `68`
- Result: executable failure

The current preflight consequently retains `SPATIAL_ASSERTION_FAILED`,
`MISSING_POSITIVE_BORDER_ASSERTION`, and downstream `UNCERTIFIED_A_GRADE` for
region `015`.

## Exact corridor component inventory

The evaluator reports 34 affected components. Their current values group as
follows; no proposed value is approved.

| Current actor and relationships | Current facets | Component IDs | Count |
| --- | --- | --- | ---: |
| `scenario-mor`; `sovereign`, `owner`, `controller` | `administered`, `habitable`, `resident`, `nucleated`, `polity_associated` | `cmp-prv_0cbd6b585c399bf8b251`, `cmp-prv_0feecb4f065e3d1f291a`, `cmp-prv_1fcddf25dcc32217ad88`, `cmp-prv_21e1b5df0a32d8bfcff8`, `cmp-prv_527fcb9fb9a051dc776f`, `cmp-prv_699f9b74b7469deb72cd`, `cmp-prv_6ccde1f12bca7f8e1517`, `cmp-prv_6ed893f8f84031de9175`, `cmp-prv_70dc7d4158931889e154`, `cmp-prv_713e5d932463ca4e6964`, `cmp-prv_83ee9f6cd2593419f84c`, `cmp-prv_860888c8b4e812b9ee67`, `cmp-prv_afda53f38757ed9f3f13`, `cmp-prv_b02de91dae63d60e2d5f`, `cmp-prv_bea4833b7d6907692068`, `cmp-prv_bfc9324cbcd05ea3266f`, `cmp-prv_daaa6b43acd6179e0b54`, `cmp-prv_ed7d5bf80d42ddec8ca1` | 18 |
| `scenario-tlc`; `sovereign`, `owner`, `controller` | `administered`, `habitable`, `resident`, `nucleated`, `polity_associated` | `cmp-prv_11fd9af3ac4e24f7d965`, `cmp-prv_1c9487014f99ae738110`, `cmp-prv_29e667bdbfb94a33c2a1`, `cmp-prv_2c111520b4dd11459759`, `cmp-prv_3b2184bdacf874b3e79c`, `cmp-prv_4295ce0e6495d0170935`, `cmp-prv_4f7b4787ce058b1a704c`, `cmp-prv_5c8faabd357f5b75b209`, `cmp-prv_831c6703ea45d989817c`, `cmp-prv_8b86a2fb0f91fc7d9cd0`, `cmp-prv_92348870bf2d0e06adb8`, `cmp-prv_95191940c54724ff5fec`, `cmp-prv_a813a8f8122dd84b6590`, `cmp-prv_c14cea4c94ca6928cec9`, `cmp-prv_dc69507d93f6a73ffc2b`, `cmp-prv_f1237876fc0d89376857` | 16 |

The packet globally attaches the same broad source set to these rows. None of
the reviewed locators enumerates the component IDs, assigns both sides
independently of the inherited baseline actors, or supplies a transformation
and error budget from historical geometry to the component fabric.

## Evidence review

The most relevant pinned locators are:

| Source pin | Packet SHA-256 | What it supports | What it does not support |
| --- | --- | --- | --- |
| `cambridge-maghrib-islamic-period` | `6be26fd4e86e975140c71932d5a9130fc98bdd21b63a04cf198ac495fab0f039` | Marinid, Zayyanid/Abd al-Wadid, and Hafsid political history | A packet-supplied exact-date corridor extraction, control points, or exhaustive component binding |
| `cambridge-north-africa-dynasties` | `3175ec7f39758b913ef9b2ce89654d3459b0c83cd2601c6fdda92b2123f4c3d3` | Broad fifteenth-century dynasty disposition | A complete `1444-11-11` two-sided frontier fabric |
| `cambridge-post-almohad-maghrib` | `8999e7a2867823b1ef1180b99a91a3ed14feed03f762e298eb8d5d842fe40a60` | Post-Almohad dynasties and chronology | Georeferenced reusable linework or record-level old/new values |
| `cambridge-tlemcen-1439` | `686c09b99f6a934c086788da222b694ac5315d0dd4c444a3e29cd262ffaf2d41` | A date-near Tlemcen case in `843/1439` | The territorial extent of Tlemcen or the full Morocco-Algeria corridor |
| `regional-survey-015` | `c7c66e1121783b0b3a3e158c76659efbd20f250fffb34774778cc3339b82d18d` | Marinid and Zayyanid coexistence in `1400-1450` and broad regional chronology | An exact political line; its map scope is present-day Algeria, Libya, Morocco, and Tunisia |
| `shepherd-historical-atlas` | `893a830bacc5d6e9e52e7023f8a2c4fc228231e58bd6bf38d60fdeeb5614c8d9` | A public-domain atlas scan and broad Africa/Mediterranean plates | An enumerated plate extraction, dated transformation, residual, or component mapping |
| `natural-earth-admin0-5.1.1-region-015` | `8b267e4af48a333e80287f55fa62a6cb5fbd4f2f290f4f0d07363a2c72907d12` | The modern `MAR-DZA` negative-control reference only | Any positive historical actor assignment or frontier |

A fresh publisher/institutional check confirms the same limit. The
[Met chronology](https://www.metmuseum.org/toah/ht/08/afw.html) lists both
Marinid and Zayyanid dynasties in western North Africa for `1400-1450`, but
supplies no two-sided frontier and explicitly scopes its map by present-day
countries. Cambridge exposes the book and a
[list-of-maps record](https://www.cambridge.org/core/books/abs/history-of-the-maghrib-in-the-islamic-period/list-of-maps/6ED69B3EB7D23A24EF0608B3F79A5373),
but the current packet neither identifies a specific qualifying plate nor
records any extraction. The Shepherd locator likewise names only broad
`1400-1500` plates.

All ten historical packet sources have empty `transformations` and
`derived_artifacts`. The packet has six point build features for capitals, no
historical boundary feature, and no historical derived file. Its only boundary
and only derived file are the modern Morocco-Algeria negative control. Thus it
contains no provenance chain from an independently sourced historical map to
the current component geometry.

## Rejection reasons

1. `final_actor` preserves the inherited baseline Marinid/Zayyanid split and
   provides no source-spatial chooser for Maghrib components. The exact `1.0`
   modern-seam match is consistent with the already identified modern-country
   dispatch and violates the Task 16 gate.
2. The evidence has no independently derived exact-date line, two-sided mask,
   control points, transformation, residual, or predeclared error budget for
   `1444-11-11`.
3. The evidence-to-record mapping is global and coarse. It cannot justify an
   enumerated old-to-new value for any of the 34 affected components.
4. The six checked capitals prove positive locations and polity existence,
   not territorial extents or a complete frontier.
5. The retired Marinid-Zayyanid edge was candidate-derived and cannot be
   restored, lightly perturbed, or used to validate current status edges.
6. `not_applicable` is unsupported. The packet models multiple bounded
   states/polities and supplies no complete land-adjacent actor-pair audit.

## Required replacement packet

A future region `015` packet may be reviewed only if it supplies all of the
following before edits:

- one exact claimed historical relation, not merely actor coexistence, a
  capital, modern membership, or a broad dynastic chronology;
- independently derived and date-valid linework, a two-sided mask, or an
  explicit source-based corridor fabric spanning the full usable seam;
- exact locators, licensing, transformations, control points, residuals, and a
  fixed error budget;
- an exhaustive mapping from evidence to every proposed component old/new
  value, including relationships and all five facets;
- confirmation, demonstrable from the generator, that neither inherited
  modern-country dispatch nor candidate-derived geometry chooses values;
- snapshot hashes, the fixed measurement and tolerance, expected affected and
  neighboring QA changes, and an independent hash review; and
- for a `not_applicable` proposal, the separately required complete
  land-adjacency disposition bound to positive historical anchors.

Until then, expected QA impact is exactly zero: no finding is cleared, no
component changes, and no review, certification, runtime, publication, or
deployment permission changes.
