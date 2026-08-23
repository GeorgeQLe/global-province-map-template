# M25C Task 16 region 005 corridor evidence review

Status: **reviewed; rejected before implementation**
Review date: `2026-08-23`
Start date: `1444-11-11`
Scope: Peru-Bolivia negative-control corridor and South America positive-border gate

## Disposition

Do not implement a region `005` corridor reconstruction, positive border, or
border-applicability record from the current evidence packet. Preserve all
tolerances, assertions, assignments, candidate permissions, and release
permissions unchanged.

The packet establishes date-relevant Inca, Chimor, Aymara/Altiplano, and broad
Andean fabrics and several positive centers. It does not supply an independently
georeferenced, exact-date, two-sided territorial line or a source-to-component
mapping for the fixed Peru-Bolivia corridor. More decisively, the current
generator derives the corridor split by resolving each representative point to
Natural Earth `ADM0_A3` and dispatching `PER` and `BOL` through separate
branches. Task 16 expressly forbids modern-country dispatch. The resulting
modern-seam match therefore cannot be repaired by relabeling the same
candidate-derived geometry, and it cannot qualify as a historical positive
border.

This is a completed separate review, not an implementation approval. No old
value has an approved proposed replacement.

## Hash-bound review inputs

| Input | SHA-256 |
| --- | --- |
| `scripts/generate-m25c-region-005-packet.py` | `74e579b0005970a5a54b12b1525edaeede00b9efb22c9732bff2e568e55d668e` |
| `005-south-america-2026-08-16.json` | `6b7f88420e8027f8daca9ad17e738af7db2882ceb194ee9d79c8215e633831c4` |
| `assets/005/negative-controls.geojson` | `7a1d5f6fb945ff83aeb3325aceae204469c7b15cd33a6ee9986e096c5dc589df` |
| assembled `historical-territory-status.json` | `bcdb93f3d828bf87643e36f4d848499bfb6e67da87c5f52fe3474fce301ff080` |
| assembled `build.geojson` | `351542020590ed5b473b8f198a8e776d1d967c804e19e729b721ca74a6801e72` |
| assembled `golden.json` | `2ef4feede67d460631ab70ffd43b295d921af8d1b109698370722a1b836db4b8` |
| assembled `start_date_preflight.json` | `4136b379760ab62cab303e7f85a3c10349bbd6f98380257ff8a351947f8e4c6e` |
| assembled `sidecars/adjacency.csv` | `31a9e46a40011dd0a17508cf75ca92acb5334f8253ea160a5617b8e5140e5ff9` |
| assembled `sidecars/location_fabric_manifest.json` | `65882451f8e079bebf10d35dfe3c0ace740c6e7c184cd7fcfc1ccf84b4bafbf6` |

The reviewed status artifact is schema `0.2.0`, artifact
`1.0.0-assembled.1`, compatibility revision `2`, and scenario
`official-1444-global-v1`. The fabric manifest records geometry revision `1`.
Any hash or revision change requires a new separate review.

## Assertion and predeclared measurement

The exact existing assertion is
`region-005-negative-modern-peru-bolivia-seam`, using boundary feature
`forbidden-modern-peru-bolivia-seam` and relation
`regional_status_boundary_matches_forbidden_modern_seam_ratio_lte`.

- Corridor: fixed `75 km`
- Unit: ratio
- Maximum: fixed `0.20`
- Reference length: `951.4017615694846 km`
- Usable and covered reference: `951.4017615694846 km` (`1.0` coverage)
- Matched length: `850.063334242125 km`
- Measurement: `0.8934851380134233`
- Transitions: `13`
- Normal samples: `191`; missing or ambiguous side samples: `0`
- Result: executable failure

The current preflight consequently retains
`SPATIAL_ASSERTION_FAILED`, `MISSING_POSITIVE_BORDER_ASSERTION`, and downstream
`UNCERTIFIED_A_GRADE` for region `005`.

## Exact corridor component inventory

The evaluator reports 21 affected components. Their current values and the
review disposition are:

| Current value | Exact component IDs | Proposed value |
| --- | --- | --- |
| `scenario-aymara-kingdoms`; `administered`, `nucleated`, `polity_associated` | `cmp-prv_25711345a021b3b0c8f6`, `cmp-prv_2a2abea6dde8cf13a72f`, `cmp-prv_3d3ce5c55cd0f561a0ea`, `cmp-prv_56b052b837eac242f4c3`, `cmp-prv_62fb7ca86d4a70bcf721`, `cmp-prv_74938a89caab572f953f`, `cmp-prv_7fb8734ec436d4da5d9a`, `cmp-prv_8e4020a2eac6cb7317b6`, `cmp-prv_95f1bb5d63b6d1b2d570`, `cmp-prv_9d9c8cc3410367bb699d`, `cmp-prv_abb615aff26d77f894ce`, `cmp-prv_f1fbd75512a76a1ae568`, `cmp-prv_fdcde264be28c57ebecc` | None approved |
| `scenario-inca-cusco`; `administered`, `nucleated`, `polity_associated` | `cmp-prv_442207513776cbb5712d`, `cmp-prv_db32e7b22fc09648e1f7`, `cmp-prv_e940906cbdb2f1cdcb54`, `cmp-prv_ebee30432e9d4960fa6b`, `cmp-prv_f8a4799c6b5188f87f7b` | None approved |
| no political unit; `local_decentralized`, `dispersed`, `customary_community` | `cmp-prv_288f1a2e53c3d5495bdb`, `cmp-prv_a30c6b9fb800f85409e8`, `cmp-prv_eb3d7a9248ecb13ae234` | None approved |

The packet globally attaches broad source sets to these rows, but none of the
reviewed locators enumerates these component IDs, assigns both sides of the
corridor independently of `PER`/`BOL`, or provides a transformation and error
budget from historical geometry to the component fabric.

## Evidence review

The relevant pinned locators are:

| Source pin | Packet SHA-256 | What it supports | What it does not support |
| --- | --- | --- | --- |
| `regional-survey-005`: Met timeline through 1463 | `4f3d86bf493744252aff3b128e3d0c9a6d14b2d5cd853157c9acad65e760f7d7` | Broad chronology for early Inca expansion | An exact `1444-11-11` perimeter or corridor-side component assignments |
| `met-chimor`: object record and 1470 conquest description | `68aefcf0227266fd6a1c992af786c36196f5610e6a609454fca26f1b3aa9fd4e` | Chimor's separate existence and later conquest chronology | A Peru-Bolivia line; Chimor is not the corridor-side mapping proposed here |
| `smithsonian-handbook-south-america-v2`: maps 1-7 and Central Andean chapters | `ccbfe816e8fb136904162a6c5aa9a2dd1cf9ba1fb304f490efa335e73036b96e` | Broad Central Andean cultural and political context | A predeclared digitization, exact-date line, residual, or component mapping |
| `unesco-qhapaq-nan`: fifteenth-century consolidation and route hierarchy | `953b45bde37060da9d5e6398d359df1331392571810d3248ef1394568ce7ac28` | Cusco-centered network and consolidation | A territorial boundary; roads and political reach are not two-sided border geometry |
| `natural-earth-admin0-5.1.1-region-005`: modern `PER-BOL` shared boundary | `1d2723fc7b8643537c31e6b6cd25e90d7704150f2735408325f78b95c0f504d7` | The modern negative-control reference only | Any positive historical assignment or frontier |

The repository's `2026-08-14` access audit records the Met regional survey as
reachable through browser retrieval after automated access rejection. A fresh
automated retrieval during this review did not return usable source text; the
review therefore relies only on the already pinned reviewed locators and makes
no broader claim from inaccessible material.

### Replacement-source qualification attempt

The three sources nominated for a replacement fabric were checked separately
against the complete fixed corridor before any implementation:

| Candidate | Exact reviewed locator | Qualification result |
| --- | --- | --- |
| Smithsonian/Library of Congress handbook, volume 2 | Library of Congress item `2024894623`; 1944 *Handbook of South American Indians*, volume 2, *The Andean Civilizations*; packet locator `maps 1-7 and Central Andean regional chapters` | Broad regional context only. No predeclared control points, transformation, residual, error budget, or exhaustive component mapping was supplied. The Library of Congress rights statement also warns that reprinted material in the Serial Set can remain copyrighted and requires a separate risk assessment, so a reusable derived map is not license-qualified by the catalog record alone. |
| Elizabeth Arkush, “War, Chronology, and Causality in the Titicaca Basin” | *Latin American Antiquity* 19(4), pp. 339-373, DOI `10.1017/S1045663500004338`; abstract and publisher record | The paper dates northern Titicaca Basin pukara occupation and wall building, with most becoming common after about A.D. 1300. It does not claim a two-sided territorial boundary, does not cover the complete Peru-Bolivia seam, and the publisher download terms do not establish redistribution rights for a derived geometry artifact. |
| Charles Stanish et al., *Archaeological Survey in the Juli-Desaguadero Region of Lake Titicaca Basin, Southern Peru* | Fieldiana Anthropology new series 29 (1997), DOI `10.5962/bhl.title.3578`; chapters 1-5 and appendix 2 as enumerated by the BHL record | The survey covers about 360 km² in the Juli-Pomata area and limited reconnaissance in the Ccapia and Desaguadero areas. Its BHL scan is CC BY-NC-SA 3.0, but its southwestern-basin settlement evidence neither covers the full seam nor defines a complete exact-date two-sided political fabric. |

The fixed negative-control line runs from approximately latitude `-17.51` to
`-10.95` (about `6.55` degrees) and is `951.4017615694846 km` long. The two
specialist studies concern northern or southwestern parts of the Titicaca
basin, and the handbook remains a coarse contextual source. They therefore do
not provide two independent, license-compatible sources covering every one of
the 21 affected components. Because there is no complete coverage, there can
be no defensible source-only GeoJSON, georeferencing controls or residuals,
overlap classification, or old/new mapping to submit for approval. The
replacement-packet procedure stops at this gate.

## Rejection reasons

1. The generator's `nearest_country`/`final_actor` path makes modern
   `ADM0_A3` membership an input to the historical actor split. This violates
   the no-modern-country-dispatch gate.
2. The evidence has no independently derived historical line, two-sided mask,
   source control points, transformation, residual, or predeclared error
   budget for `1444-11-11`.
3. The evidence-to-record mapping is global and coarse. It cannot justify any
   enumerated old-to-new value among the 21 corridor components.
4. A positive Inca-Chimor border would not repair this corridor and is not
   date/geometry qualified: the packet itself locates the Inca conquest of
   Chimor around `1470`, after the start date.
5. `not_applicable` is also unsupported. The packet models multiple bounded
   states/polities and has not supplied the complete land-adjacent actor-pair
   audit required by the applicability contract.

## Required replacement packet

A future region `005` packet may be reviewed only if it supplies all of the
following before edits:

- one exact claimed historical relation, not merely coexistence, route reach,
  modern membership, or later maximum extent;
- independently derived and date-valid linework, a two-sided mask, or an
  explicit source-based corridor fabric;
- exact locators, licensing, transformations, control points, residuals, and a
  fixed error budget;
- an exhaustive mapping from evidence to every proposed component old/new
  value, including relationships and facets;
- confirmation, demonstrable from the generator, that neither modern-country
  dispatch nor candidate-derived geometry chooses the historical values;
- snapshot hashes, fixed measurement and tolerance, expected affected and
  neighboring QA changes, and an independent hash review.

Until then, expected QA impact is exactly zero: no finding is cleared, no
component changes, and no review, certification, runtime, publication, or
deployment permission changes.
