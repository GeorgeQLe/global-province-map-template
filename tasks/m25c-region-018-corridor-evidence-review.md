# M25C Task 16 region 018 evidence review

Status: **rejected**
Review date: `2026-08-23`
Start date: `1444-11-11`
Scope: Botswana–South Africa corridor and Southern Africa positive-border gate

## Disposition

Natural Earth ADM0_A3 dispatch chooses Botswana and South Africa actor sheets; the current packet has no exact-date two-sided geometry or exhaustive component mapping.

No corridor, packet, generator, assembled artifact, tolerance, or permission changes are authorized in this review. No evidence-supported old/new mapping exists.

## Frozen hash bindings

| Input | SHA-256 |
| --- | --- |
| `scripts/generate-m25c-region-018-packet.py` | `f2553b1f2a3b11daf52f8d2147c1b74538f9720847b96a2c7b48a9c09493635c` |
| `research/start-dates/1444-global-v1/regional-packets/018-southern-africa-2026-08-16.json` | `8e491e1044fda6b6c1f27e995733c8eececbbc85c79f16ff72ee440c505e7915` |
| `research/start-dates/1444-global-v1/regional-packets/assets/018/negative-controls.geojson` | `b3cd615771e2ce34981f403554cd1c055af07d805f2efea454d8c4abe6970c88` |
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

- Assertion: `region-018-negative-modern-botswana-south-africa-seam`
- Boundary feature: `forbidden-modern-botswana-south-africa-seam`
- Relation: `regional_status_boundary_matches_forbidden_modern_seam_ratio_lte`
- Corridor: fixed `75 km`; tolerance: fixed `0.20`; unit: ratio
- Result: `fail`; reference=1610.8238118888994 km; usable=1610.8238118888994 km; covered=1463.735356911798 km; coverage=0.9086874344099611; matched=1060.437318872306 km; measurement=None; transitions=8; normal samples=323; missing=29; ambiguous=0; eligibility rejections: unknown_required_facet=8.
- Affected-component count: `28`

## Current affected values

- Actors: `scenario-sotho-tswana-communities`; relationships: `customary_tenure, territorial_presence`; facets: `{"authority": "local_decentralized", "habitability": "habitable", "population_presence": "resident", "settlement_pattern": "dispersed", "tenure": "customary_community"}`; components (11): `cmp-prv_11cba6352444d544ec4b`, `cmp-prv_1a3e65ddb6443f6d3df5`, `cmp-prv_20bd6db0f984e305f64d`, `cmp-prv_26ed1dac6952277c3b8e`, `cmp-prv_2918d0ae32ba789cd0e6`, `cmp-prv_30d12e316d3432972bf7`, `cmp-prv_7d22ee39028dbeb8e2e4`, `cmp-prv_9bee683f2eda4ddd8c85`, `cmp-prv_bbdf940c37f06e4e424d`, `cmp-prv_eaead8569bfb820c39da`, `cmp-prv_f7f3ede99d2c97302c22`
- Actors: `scenario-kalahari-san-communities`; relationships: `customary_tenure, seasonal_use, territorial_presence`; facets: `{"authority": "local_decentralized", "habitability": "habitable", "population_presence": "seasonal", "settlement_pattern": "mobile", "tenure": "customary_community"}`; components (8): `cmp-prv_11f7f7de8caebb732e81`, `cmp-prv_1df9533336e7c8cd9e52`, `cmp-prv_2fc66eead8366d36b42a`, `cmp-prv_3077870a352255857b6f`, `cmp-prv_642bf95d4b8f6bbeb6de`, `cmp-prv_8dc076f7b8045709a75a`, `cmp-prv_92872ee68a865166be9e`, `cmp-prv_9ff5d2944c5a3c0f3fcc`
- Actors: `scenario-khoe-pastoral-communities`; relationships: `customary_tenure, seasonal_use, territorial_presence`; facets: `{"authority": "local_decentralized", "habitability": "habitable", "population_presence": "seasonal", "settlement_pattern": "mobile", "tenure": "customary_community"}`; components (9): `cmp-prv_2258aab03a039ca95936`, `cmp-prv_5c5cbee6f5739596fa94`, `cmp-prv_6a23e42559c51cee19af`, `cmp-prv_6b5821d05be6a6f63628`, `cmp-prv_79d5099762ddbfeab266`, `cmp-prv_965f4f93e1f64f01c8ea`, `cmp-prv_9b3e93ec18d0cbdf31dd`, `cmp-prv_d39efb815610cebc3d80`, `cmp-prv_e47a9171988040979f11`

## Applicability and provenance audit

No complete land-adjacent actor-pair audit supports not_applicable on this packet.

The generator/packet review found no permissible path that silently reuses candidate-derived historical geometry or modern-country dispatch. Where the generator does use inherited or ADM0/ADM1 dispatch, coordinate sheets, or candidate shared-edge extraction, that path is a rejection reason and may not be promoted. The packet contains no independently complete exact-date two-sided source-to-component mapping. Checked centers establish positive locations, not territorial extents.

## Source pins

| Source | Pin SHA-256 | License | Transformations / derived assets | Exact locator |
| --- | --- | --- | ---: | --- |
| `met-arts-africa-map` | `e6efeeef5e96c80557a377a5f13433a6708584336f11655ed38158b9674a6550` | Citation/link only | 0 / 0 | Southern Africa > San artistic record and continent-wide regional context |
| `regional-survey-018` | `601b324ab6955a3ef1db210891970c365de4963f3fc366f03452e510bf5598bb` | Citation/link only; no source text redistributed | 0 / 0 | Timeline > 1400 A.D.-1600 A.D.; Southern African regional overview and chronology |
| `sahistory-precolonial-southern-africa` | `70ef649ee7990a91b2ad04af4ff2f2d8c596e1143f8cd0834d497ecb12b50178` | Citation/link only | 0 / 0 | Pre-colonial farmers > post-Mapungubwe Sotho-Tswana movement and established San and Khoekhoe communities |
| `shepherd-historical-atlas` | `c8e8d3c1434d72a94d650d107e96d723fec179bb95cdcd6b7f40626b774cdf3b` | Public-domain scan; citation and link only | 0 / 0 | Historical Atlas > Africa before sustained European colonization |
| `unesco-general-history-africa-iv` | `1a0ff09a56e664b1871c24f88edc20bdebc5b7ab4bada1a7d77201de3a477e1f` | Citation/link only | 0 / 0 | Chapters 21 and 23, The Zambezi and Limpopo basins, 1100-1500, and Southern Africa: its peoples and social structures |
| `unesco-mapungubwe` | `03fc992152651bc523fc19343d84d3c5e2e03e26d07ea2ced05d197b28daf9a4` | Citation/link only | 0 / 0 | Outstanding Universal Value > Mapungubwe kingdom, trading network, and fourteenth-century abandonment |
| `unesco-tsodilo` | `f283d6c642c9b4e61739959761518f4a750cca749518598d1076651a55fe9f74` | Citation/link only | 0 / 0 | Outstanding Universal Value > long-lived Kalahari settlement, ritual, and rock-art landscape |
| `unesco-twyfelfontein` | `9a2d440232a9ca4a2a90e037f0ee80120acc40cfb9861150795305c0c73352f3` | Citation/link only | 0 / 0 | Outstanding Universal Value > hunter-gatherer and pastoral community records in north-western Namibia |
| `natural-earth-admin0-5.1.1-region-018` | `ef8d40185b13f13ab8d52cade0d6d238c3147c9c7f4d7f86aff79dcfefe69d5a` | Public domain | 1 / 1 | Admin-0 countries 5.1.1 > ADM0_A3 shared boundary BWA-ZAF |

Historical records with empty transformations/derived assets cannot supply missing linework. Modern Natural Earth records remain negative controls only. Any source used for future geometry requires exact reusable licensing, extraction and CRS details, control points, residuals, uncertainty, and a predeclared error budget.

## QA and permissions

Current region findings: `MISSING_POSITIVE_BORDER_ASSERTION`, `NON_EXECUTABLE_SEAM_ASSERTION`, `SPATIAL_ASSERTION_FAILED`, `UNCERTIFIED_A_GRADE`. This disposition changes none of them. The frozen worldwide result remains 58 non-review errors and one warning. Candidate, review, certification, runtime, publication, release, and deployment permissions remain unchanged.

## Replacement requirements

A replacement packet must provide an exact `1444-11-11` relation; independent linework, two-sided masks, or a source-based zone spanning the complete usable corridor; exact source pins and license lineage; transformations, controls, residuals and fixed error budget; an exhaustive current-to-proposed mapping for actors, all five facets and relationships; proof that neither modern dispatch nor candidate edges choose or validate values; predeclared affected and neighboring QA impact; and independent hash reproduction. An applicability route additionally requires an exhaustive land-adjacent actor-pair disposition bound to passing positive anchors.
