# M25C Task 16 region 011 corridor evidence review

Status: **reviewed; rejected before implementation**
Review date: `2026-08-23`
Start date: `1444-11-11`
Scope: Mali-Niger negative-control corridor and Western Africa positive-border gate

## Disposition

Do not implement a region `011` corridor reconstruction, positive border, or
border-applicability record from the current evidence packet. Preserve all
tolerances, assertions, assignments, candidate permissions, and release
permissions unchanged.

The packet establishes date-relevant Mali, Tuareg, Songhai, Hausa, Mossi, and
other broad Western African political fabrics and eight positive centers. It
does not supply an independently georeferenced, exact-date, two-sided
territorial line or a source-to-component mapping for the fixed Mali-Niger
corridor. More decisively, the current generator resolves every province
representative point to Natural Earth `ADM0_A3` before dispatching historical
actors through country-specific branches, including distinct `MLI` and `NER`
branches. Task 16 expressly forbids modern-country dispatch.

The current stricter seam evaluator also finds only partial eligible coverage,
so it correctly refuses to produce a ratio. Relabeling the same
candidate-derived geometry cannot qualify as historical remediation, and a
positive border cannot be manufactured from the resulting status edges.

This is a completed separate review, not an implementation approval. No old
value has an approved proposed replacement.

## Hash-bound review inputs

| Input | SHA-256 |
| --- | --- |
| `scripts/generate-m25c-region-011-packet.py` | `e1e628ac6c3bdb069a10958b0fb88bc0763a3f129d46556dcb6fefe0375edb44` |
| `011-western-africa-2026-08-16.json` | `d336c39095ee78d46fb840ca7681895c6b401d854b6ab4c3f01a050395e3049c` |
| `assets/011/negative-controls.geojson` | `e7043fffdc24026370112f67cef2864ca13350fce87d7dbb7024b4c9255d6b50` |
| assembled `historical-territory-status.json` | `bcdb93f3d828bf87643e36f4d848499bfb6e67da87c5f52fe3474fce301ff080` |
| assembled `build.geojson` | `351542020590ed5b473b8f198a8e776d1d967c804e19e729b721ca74a6801e72` |
| assembled `golden.json` | `2ef4feede67d460631ab70ffd43b295d921af8d1b109698370722a1b836db4b8` |
| assembled `start_date_preflight.json` | `14ae15ae70b0608b72625268939ded67caa477c66e0d0341bbaac0548a5a81af` |
| assembled `sidecars/adjacency.csv` | `31a9e46a40011dd0a17508cf75ca92acb5334f8253ea160a5617b8e5140e5ff9` |
| assembled `sidecars/location_fabric_manifest.json` | `65882451f8e079bebf10d35dfe3c0ace740c6e7c184cd7fcfc1ccf84b4bafbf6` |

The reviewed status artifact is schema `0.2.0`, artifact
`1.0.0-assembled.1`, compatibility revision `2`, and scenario
`official-1444-global-v1`. The fabric manifest records geometry revision `1`.
Any hash or revision change requires a new separate review.

## Assertion and predeclared measurement

The exact existing assertion is
`region-011-negative-modern-mali-niger-seam`, using boundary feature
`forbidden-modern-mali-niger-seam` and relation
`regional_status_boundary_matches_forbidden_modern_seam_ratio_lte`.

- Corridor: fixed `75 km`
- Unit: ratio
- Maximum: fixed `0.20`
- Reference and usable length: `843.7078279840698 km`
- Covered reference: `174.18870486197656 km`
- Coverage ratio: `0.20645619144980298`
- Matched eligible-transition length: `44.53635431779734 km`
- Measurement: null; non-executable
- Transitions: `6`
- Normal samples: `169`
- Missing side samples: `134`; ambiguous side samples: `0`
- Unknown-required-facet rejections: `429`
- Result: fail closed

The current preflight consequently retains
`MISSING_POSITIVE_BORDER_ASSERTION`, `NON_EXECUTABLE_SEAM_ASSERTION`,
`SPATIAL_ASSERTION_FAILED`, and downstream `UNCERTIFIED_A_GRADE` for region
`011`. The pre-phase-1 ratio is not a current executable result and must not be
used to approve edits under the stricter complete-coverage contract.

## Exact affected-component inventory

The evaluator reports five affected components. Their current values and the
review disposition are:

| Current value | Exact component IDs | Modern dispatch input | Proposed value |
| --- | --- | --- | --- |
| `scenario-songhai-kingdom`; `administered`, `nucleated`, `polity_associated` | `cmp-prv_18887afe97533756c7f6`, `cmp-prv_adc62ca6e72eaa2b7ad9`, `cmp-prv_bf91a4b3014bb0d8f029` | `NER` | None approved |
| `scenario-mossi-kingdoms`; `administered`, `nucleated`, `polity_associated` | `cmp-prv_4e392654faa82e414319`, `cmp-prv_5d9ab48bc515b28bc177` | `BFA` | None approved |

All five rows are `habitable` and `resident`, carry sovereign/owner/controller
relationships, and globally attach the same eight broad historical source IDs.
None of their reviewed locators enumerates these component IDs, assigns both
sides of the corridor independently of `ADM0_A3`, or provides a transformation
and error budget from historical geometry to the component fabric.

The full region contains 641 components: 117 administered/nucleated rows, 71
decentralized/dispersed community rows, 22 uninhabited rows, and 431 all-unknown
rows. The seam evaluator rejects 429 unknown-facet components relevant to its
corridor search. A five-component transition inventory therefore cannot stand
in for complete two-sided corridor coverage.

## Evidence review

The relevant pinned locators are:

| Source pin | Packet SHA-256 | What it supports | What it does not support |
| --- | --- | --- | --- |
| `regional-survey-011` | `b6a21df37a645a4b92aa24c7d5e4aaa9bb8c75002b30e67b6ecca84993f81568` | Broad `1400-1500` chronology for Tuareg, Mali, Songhai, Akan, and Dogon | A complete exact-date corridor fabric or component mapping |
| `met-western-sudan-empires` | `33d9f69c0102b4ef24fd0f8b052d56cf3fca2cefb77784b3f4bc42ff26ccef76` | Medieval Western Sudan empires and the absence of fixed geopolitical boundaries | A hard two-sided `1444-11-11` frontier |
| `met-sahel-empires` | `1747196b01b19e65a682ecfde884997b59265a2e0162e0ef4336193742c6f638` | Mali and later imperial Songhai chronology | Day-precise Songhai extent or line geometry at the start date |
| `unesco-general-history-africa-iv` | `cec079c183575f84e8ad7aa6086f8f589c93d76657d5a56c14285baf16733560` | Chapters and regional maps for broad twelfth- to sixteenth-century context | Packet-supplied control points, residuals, error budget, or exhaustive old/new mapping |
| `shepherd-historical-atlas` | `689fb187c0507f98d0ee9b215785e32eab7ec00b17d33d8475bc88090f853103` | A public-domain historical-atlas scan and broad African plates | An exact enumerated plate extraction, dated georeferencing, or component binding |
| `british-museum-african-kingdoms` | `d9658cb45df7d942a952cfe5f44af0391a5fd3d7fe92187b4c300244a5cf7ed7` | High-level Mali, Songhai, Benin, and Ife chronology | Corridor linework or two-sided assignments |
| `smarthistory-africa-to-1600` | `bd74d5db70301eb816dff7694ad1c85405a3bcd1411571b4f7336c00b261fbe6` | Broad pre-1600 actor context | Exact-date territorial geometry |
| `cambridge-precolonial-africa-regions` | `98e295b97c245b8a0f7a6256acb13b9de150c383b3af8b70d43aa5ce7eb1635f` | Regional controlled vocabulary | A historical boundary or spatial derivation |
| `natural-earth-admin0-5.1.1-region-011` | `daf0f627c3b7e99bcb7005c847d849d93e71da8aa060cd51863ea66b51b2c072` | The modern negative-control reference only | Any positive historical actor assignment or frontier |

The repository's `2026-08-14` access audit records `regional-survey-011` as
reachable through browser retrieval after automated access rejection and the
Shepherd atlas as reachable by automated retrieval. The review makes no claim
beyond the packet's pinned locators and the repository's already reviewed
source record.

The packet has eight point build features for checked centers, no historical
boundary feature, and no historical derived file. Its only boundary and only
derived file are the modern Mali-Niger negative control. All non-Shepherd
historical source licenses are recorded as citation/link only, and the packet
records no transformations. Thus the packet contains neither reusable
historical linework nor a provenance chain from any source map to the current
component geometry.

## Rejection reasons

1. The generator's `nearest_country`/`final_actor` path makes Natural Earth
   `ADM0_A3` membership an input to historical actor assignment. Its explicit
   `MLI`, `NER`, and neighboring-country branches violate the gate against
   modern-country dispatch.
2. Only `20.645619%` of the usable seam is covered by eligible status evidence;
   134 deterministic side samples are missing. The assertion is therefore
   non-executable under the approved complete-coverage contract.
3. The evidence has no independently derived exact-date line, two-sided mask,
   source control points, transformation, residual, or predeclared error budget
   for `1444-11-11`.
4. The evidence-to-record mapping is global and coarse. It cannot justify an
   enumerated old-to-new value for the five affected components, much less the
   unknown corridor coverage that must be reconstructed.
5. The packet's checked centers prove positive locations, not a political
   border. A current status edge is candidate-derived and cannot validate
   itself as an independent positive-border assertion.
6. `not_applicable` is also unsupported. The packet models multiple bounded
   states and polities and supplies no complete land-adjacent actor-pair audit.

## Required replacement packet

A future region `011` packet may be reviewed only if it supplies all of the
following before edits:

- one exact claimed historical relation, not merely actor coexistence, a
  center, modern membership, or later maximum extent;
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
