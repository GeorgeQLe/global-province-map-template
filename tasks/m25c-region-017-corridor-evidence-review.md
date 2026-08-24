# M25C Task 16 region 017 evidence review

Status: **rejected**
Review date: `2026-08-23`
Start date: `1444-11-11`
Scope: Angola–DRC corridor and Middle Africa positive-border gate

## Disposition

Natural Earth ADM0_A3 dispatch chooses the corridor actors; 37 affected components have only partial eligible coverage and no independent historical spatial mapping.

No corridor, packet, generator, assembled artifact, tolerance, or permission changes are authorized in this review. No evidence-supported old/new mapping exists.

## Frozen hash bindings

| Input | SHA-256 |
| --- | --- |
| `scripts/generate-m25c-region-017-packet.py` | `3c4c2f2a48834c11d7a8c2e13b7e8eef9c72890abba9e9ca9b9eb6dd149b59ae` |
| `research/start-dates/1444-global-v1/regional-packets/017-middle-africa-2026-08-16.json` | `a576ce1320bbf31027d36ca70da614ade4acc23868867b7f2d5e1fbe797264e7` |
| `research/start-dates/1444-global-v1/regional-packets/assets/017/negative-controls.geojson` | `2c90ae1c2b242fb905c893e9259abece0e899f2555e03b218691899d8a5d3cdc` |
| `data/processed/m25c-global-staging/evidence/review_acceptance.json` | `9dd3956527de782039551cadbef10e908953a0a686d791fec10d560a312bbb0a` |
| `assembled historical-territory-status.json` | `bcdb93f3d828bf87643e36f4d848499bfb6e67da87c5f52fe3474fce301ff080` |
| `assembled assignments.json` | `8b49507e9d373b422c2402da2cb550e8fc855ce7a8f140110bf7831cfecd7a85` |
| `assembled build.geojson` | `351542020590ed5b473b8f198a8e776d1d967c804e19e729b721ca74a6801e72` |
| `assembled boundaries.geojson` | `a41a45a1e4e1135ad82e208094dca1edea79d944fc2857f96ddbdabc295988b1` |
| `assembled source_manifest.json` | `181955b1ae583c4487a5d7e10325e2b19e7f60f842b7b0d1b9453eb64f5cde81` |
| `assembled golden.json` | `2ef4feede67d460631ab70ffd43b295d921af8d1b109698370722a1b836db4b8` |
| `assembled positive-border-applicability.json` | `34ba7bfc58c72e428b28b9c4434bf0e0d1d5d95f4de537434c1f9267a440e4bf` |
| `assembled start_date_preflight.json` | `6d15b5707273ed51a07eb22aaa062fbf1e9876a383d0f8b6cbccb363474f1cfe` |
| `assembled sidecars/adjacency.csv` | `31a9e46a40011dd0a17508cf75ca92acb5334f8253ea160a5617b8e5140e5ff9` |
| `assembled sidecars/location_fabric_manifest.json` | `65882451f8e079bebf10d35dfe3c0ace740c6e7c184cd7fcfc1ccf84b4bafbf6` |

The frozen artifact is schema `0.2.0`, artifact `1.0.0-assembled.1`, compatibility revision `2`, scenario `official-1444-global-v1`, with the accepted fabric and geometry revisions. Any evidence-input hash change requires a new review.

## Exact assertion and measurement

- Assertion: `region-017-negative-modern-angola-drc-seam`
- Boundary feature: `forbidden-modern-angola-drc-seam`
- Relation: `regional_status_boundary_matches_forbidden_modern_seam_ratio_lte`
- Corridor: fixed `75 km`; tolerance: fixed `0.20`; unit: ratio
- Result: `fail`; reference=2310.6093113160623 km; usable=2310.6093113160623 km; covered=1684.9609244307312 km; coverage=0.7292279643203817; matched=483.1898532533686 km; measurement=None; transitions=9; normal samples=463; missing=125; ambiguous=0; eligibility rejections: unknown_required_facet=97.
- Affected-component count: `37`

## Current affected values

- Actors: `scenario-kongo-kingdom`; relationships: `controller, owner, sovereign`; facets: `{"authority": "administered", "habitability": "habitable", "population_presence": "resident", "settlement_pattern": "nucleated", "tenure": "polity_associated"}`; components (9): `cmp-prv_0f360a62a230a442e594`, `cmp-prv_27d5ed4f44cf8cc75e8e`, `cmp-prv_3c536af9cf4ffd421235`, `cmp-prv_515d2e3ac2c1978d4e89`, `cmp-prv_755cc783f6c87bb472b5`, `cmp-prv_c57168f198a2f4c4a969`, `cmp-prv_ca153cb9e5063e4d27b1`, `cmp-prv_f24ffe10288e870f123f`, `cmp-prv_fe00d0a4759f1ad3cd99`
- Actors: `scenario-central-congo-communities`; relationships: `customary_tenure, territorial_presence`; facets: `{"authority": "local_decentralized", "habitability": "habitable", "population_presence": "resident", "settlement_pattern": "dispersed", "tenure": "customary_community"}`; components (19): `cmp-prv_05e8c34b0572493503aa`, `cmp-prv_1b150bbed546e22f9d34`, `cmp-prv_2d2a2259b7261b17fb74`, `cmp-prv_33618a764ce5c11efdd3`, `cmp-prv_46264e0f9a559d415fdb`, `cmp-prv_56ed6304eea1e815ef8c`, `cmp-prv_66b846dfb31f558fef53`, `cmp-prv_6aa121844a49738c2a0a`, `cmp-prv_6b26ca4a8f4d33063cc5`, `cmp-prv_94f418c2ba3ee16efa93`, `cmp-prv_b2360fb041b153e051ad`, `cmp-prv_b7fde006f6fac56380e6`, `cmp-prv_c39335ceb792857dc4c7`, `cmp-prv_c732004af57f653ac83c`, `cmp-prv_d487afbb8ff22afbb76f`, `cmp-prv_dcd02a7c0fe9450c6848`, `cmp-prv_e56915374fa43aeb08d4`, `cmp-prv_ebe8a2d0b8a55b79275f`, `cmp-prv_ef2faf356159ea5d87f2`
- Actors: `scenario-tio-anziku-polities`; relationships: `customary_tenure, territorial_presence`; facets: `{"authority": "local_decentralized", "habitability": "habitable", "population_presence": "resident", "settlement_pattern": "dispersed", "tenure": "customary_community"}`; components (3): `cmp-prv_6dd1dd39f3106b17e3a0`, `cmp-prv_73ca3fd109504459a630`, `cmp-prv_e950bd0a71bc0f17490d`
- Actors: `scenario-upemba-polities`; relationships: `customary_tenure, territorial_presence`; facets: `{"authority": "local_decentralized", "habitability": "habitable", "population_presence": "resident", "settlement_pattern": "dispersed", "tenure": "customary_community"}`; components (6): `cmp-prv_46f5fc2915d104edad84`, `cmp-prv_4abaa76ee0a13ce276c6`, `cmp-prv_6d97b73473e658e36b3a`, `cmp-prv_93cda587b244b36beef0`, `cmp-prv_de7e94aa1c34f5d30933`, `cmp-prv_f44a75c70a10972636c1`

## Applicability and provenance audit

No complete land-adjacent actor-pair audit supports not_applicable on this packet.

The generator/packet review found no permissible path that silently reuses candidate-derived historical geometry or modern-country dispatch. Where the generator does use inherited or ADM0/ADM1 dispatch, coordinate sheets, or candidate shared-edge extraction, that path is a rejection reason and may not be promoted. The packet contains no independently complete exact-date two-sided source-to-component mapping. Checked centers establish positive locations, not territorial extents.

## Source pins

| Source | Pin SHA-256 | License | Transformations / derived assets | Exact locator |
| --- | --- | --- | ---: | --- |
| `british-museum-african-kingdoms` | `b2756b860bdbbca99e1c17ef06dc582093290de15accf3b7f531baae3922e809` | Citation/link only | 0 / 0 | Timeline > Kingdom of Kongo and its Central African context |
| `met-arts-africa-kongo` | `0f91b4d05815b78b6a4696908acbeb22863dc2d3644d39c312b377c10fbbb2d3` | Citation/link only | 0 / 0 | Kongo: A Mighty Civilization > Nzinga a Nkwu, Mbanza Kongo, and pre-contact regional trade networks |
| `met-kongo-christianity` | `42f902e854e2956f2d1a6fe5d8f72d9c8073c2fb2b9cc47dc8afd05b14447a9e` | Citation/link only | 0 / 0 | Historical overview > thirteenth-century emergence traditions and late-fifteenth-century Portuguese contact |
| `met-kongo-power-majesty` | `c9a0c974d865abfed1f736981b612907ce25b3a4567a1bb28104ffc40987ef05` | Citation/link only | 0 / 0 | Exhibition overview > Kongo civilization from the fifteenth century and its regional setting |
| `regional-survey-017` | `fed41d4709ca773e5b30c415f2bd8b8539c931a50280dab9d195f673a2d5ced5` | Citation/link only; no source text redistributed | 0 / 0 | Timeline > 1400 A.D.-1600 A.D.; Central African regional overview and Kongo chronology |
| `shepherd-historical-atlas` | `02e62afa6f8ddd846408214730fffeae583c817efd3e891328db0483141030dd` | Public-domain scan; citation and link only | 0 / 0 | Historical Atlas > Africa before sustained European colonization and Central African regional plates |
| `smarthistory-africa-to-1600` | `b8defe81dd2e2d96edd67e9e9749b23815618122389108c1d02b3b79cd91ab14` | Citation/link only | 0 / 0 | Central Africa > Kongo before 1600 and continent-wide historical overview |
| `unesco-general-history-africa-iv` | `3fe3ecd7a9c545b1835f156deb8ceccc508290465b95b58da93c80a0ada23c21` | Citation/link only | 0 / 0 | Chapter 22, Equatorial Africa and Angola: migrations and the emergence of the first states; map 22.1, Central Africa c. 1500 |
| `natural-earth-admin0-5.1.1-region-017` | `19a0ea5fbf79b88d729b37243105d0608c5f3a1872441e39887870c753c805a3` | Public domain | 1 / 1 | Admin-0 countries 5.1.1 > ADM0_A3 shared boundary AGO-COD |

Historical records with empty transformations/derived assets cannot supply missing linework. Modern Natural Earth records remain negative controls only. Any source used for future geometry requires exact reusable licensing, extraction and CRS details, control points, residuals, uncertainty, and a predeclared error budget.

## QA and permissions

Current region findings: `MISSING_POSITIVE_BORDER_ASSERTION`, `NON_EXECUTABLE_SEAM_ASSERTION`, `SPATIAL_ASSERTION_FAILED`, `UNCERTIFIED_A_GRADE`. This disposition changes none of them. The frozen worldwide result remains 58 non-review errors and one warning. Candidate, review, certification, runtime, publication, release, and deployment permissions remain unchanged.

## Replacement requirements

A replacement packet must provide an exact `1444-11-11` relation; independent linework, two-sided masks, or a source-based zone spanning the complete usable corridor; exact source pins and license lineage; transformations, controls, residuals and fixed error budget; an exhaustive current-to-proposed mapping for actors, all five facets and relationships; proof that neither modern dispatch nor candidate edges choose or validate values; predeclared affected and neighboring QA impact; and independent hash reproduction. An applicability route additionally requires an exhaustive land-adjacent actor-pair disposition bound to passing positive anchors.
