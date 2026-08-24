# M25C Task 16 region 061 evidence review

Status: **rejected**
Review date: `2026-08-23`
Start date: `1444-11-11`
Scope: American Samoa western–eastern districts corridor and Polynesia positive-border gate

## Disposition

Topology has zero cross-actor pairs, but the record reason is inconsistent and seven Tokelau components carry region-053 actor/source contamination that the region generator cannot reproduce.

No corridor, packet, generator, assembled artifact, tolerance, or permission changes are authorized in this review. The seven contaminated Tokelau province IDs are prv_04396b8c3eb4831d9f51, prv_2b207e3e5b22362d83c8, prv_466519c843037203e8ac, prv_9abfd82d1e7fe389deb4, prv_c1d416e4fbb34535fbe8, prv_c2561841aa5efa4919c7, and prv_e826d75607ccb1a1459b.

## Frozen hash bindings

| Input | SHA-256 |
| --- | --- |
| `scripts/generate-m25c-region-061-packet.py` | `f9a15a3bbf05e9ac341d1cee444ea508cea6fe86ebff488401a35d7f001df2a2` |
| `research/start-dates/1444-global-v1/regional-packets/061-polynesia-2026-08-16.json` | `84602724a380b4210915d8fecbcf4fc5dca5d7cfbc64c8105adc45f83945e7d9` |
| `research/start-dates/1444-global-v1/regional-packets/assets/061/negative-controls.geojson` | `fd83befb30f5f786cb249f93664d4dbe8a3454d25e0fb44944f2f3d968ca9410` |
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

- Assertion: `region-061-negative-modern-american-samoa-western-eastern-district-seam`
- Boundary feature: `forbidden-modern-american-samoa-western-eastern-district-seam`
- Relation: `regional_status_boundary_matches_forbidden_modern_seam_ratio_lte`
- Corridor: fixed `75 km`; tolerance: fixed `0.20`; unit: ratio
- Result: `pass`; reference=5.318228010506736 km; usable=5.318228010506736 km; covered=5.318228010506736 km; coverage=1.0; matched=0.0 km; measurement=0.0; transitions=0; normal samples=2; missing=0; ambiguous=0; eligibility rejections: none.
- Affected-component count: `0`

## Current affected values

- Affected-component inventory is exactly empty; sampled components and preserved values are described below.

The sole sampled component is `cmp-prv_e802430ff5a7801b538c`, with actor
`scenario-samoan-chiefly-communities`, local-decentralized/habitable/resident/
dispersed/customary-community facets, and `territorial_presence` plus
`customary_tenure`. No component value change is proposed.

## Applicability and provenance audit

Independent audit: 183 assembled components, 27 internal edges, zero cross-actor pairs. Seven Tokelau components are absent from the 176-row packet and retain region-053 provenance, so acceptance is blocked.

The generator/packet review found no permissible path that silently reuses candidate-derived historical geometry or modern-country dispatch. Where the generator does use inherited or ADM0/ADM1 dispatch, coordinate sheets, or candidate shared-edge extraction, that path is a rejection reason and may not be promoted. The packet contains no independently complete exact-date two-sided source-to-component mapping. Checked centers establish positive locations, not territorial extents.

## Source pins

| Source | Pin SHA-256 | License | Transformations / derived assets | Exact locator |
| --- | --- | --- | ---: | --- |
| `allen-marquesas-chiefdom` | `24e33053f21defe148ac49fe41de61e18b42d41c8ab36fb2aa2335f95c80bcc5` | Citation/link only | 0 / 0 | Abstract and archaeological discussion > flexible Marquesan chieftain polities |
| `clark-reepmeyer-tonga` | `d9a7f2b01b58dfcc523d722f8304fa7836d8a48a4dc5653f46c5311eeb79d9eb` | Citation/link only | 0 / 0 | Abstract and Heketa-Lapaha discussion > fourteenth-century Tu'i Tonga chiefdom |
| `nps-samoa-history` | `337d91365ccf39820a6ec11576fc64c7fa969450c397a91c8cc5f5128850605a` | Citation/link only | 0 / 0 | History and the Islands of Samoa > pre-contact settlement and shared Samoan heritage |
| `regional-survey-061` | `0d9e8463ab6b86cbcba8dbac58c4b72e28ae15690e2116fffcc2f016bbd0ca9b` | Citation/link only; no source text redistributed | 0 / 0 | Timeline > Oceania, 1400-1600 A.D.; regional chronology and cultural overview |
| `shepherd-historical-atlas` | `39357ed86ef1438fbba8714bc92168364f4e24bac7abc398e3d55334becbd07a` | Public-domain scan; citation and link only | 0 / 0 | Historical Atlas > Pacific island and world historical context |
| `steadman-ana-manuku` | `877d11a43dfc92e0555375ccb2c9672812049f228b996b775b57238b8d86a306` | Citation/link only | 0 / 0 | Extract > Mangaia ritual deposit dated circa 1390-1470 |
| `unesco-henderson-evaluation` | `4c21304273447abf3e2d7475555b6daae2ef4a4ae2ebee854207f9ae785124d2` | Citation/link only | 0 / 0 | Cultural Heritage > Polynesian occupation between the twelfth and fifteenth centuries |
| `unesco-maungaroa` | `20be83445bb1f70326e4f42b77beff042ced252b8c2903381f1d581ea67654a0` | Citation/link only | 0 / 0 | Description > Rarotonga ariki, koutu, marae, and traditional political landscape |
| `unesco-taputapuatea` | `a2e4dc4cd05b574e99f5e5796d91ff4a01657215f1e3c9fb826ee5818d65bcee` | Citation/link only | 0 / 0 | Outstanding Universal Value > 1,000 years of Ma'ohi civilization and marae political functions |
| `unesco-tuvalu-landscape` | `4f95764c3c0b4a3a9594b93d598770340c19817f4444f3229d7e6b50938c4c5f` | Citation/link only | 0 / 0 | Description > stratified clan governance and traditional chiefly institutions |
| `natural-earth-admin1-5.1.1-region-061` | `f68083bcc020c3849d0e046414b969bafeb4a1cd2ac034ee81911f988559c2bc` | Public domain | 1 / 1 | Admin-1 5.1.1 > ISO_3166_2 shared boundary AS-X05~-AS-X01~ |

Historical records with empty transformations/derived assets cannot supply missing linework. Modern Natural Earth records remain negative controls only. Any source used for future geometry requires exact reusable licensing, extraction and CRS details, control points, residuals, uncertainty, and a predeclared error budget.

## QA and permissions

Current region findings: `BORDER_APPLICABILITY_NOT_QUALIFIED`, `MISSING_POSITIVE_BORDER_ASSERTION`. This disposition changes none of them. The frozen worldwide result remains 58 non-review errors and one warning. Candidate, review, certification, runtime, publication, release, and deployment permissions remain unchanged.

## Replacement requirements

A replacement packet must provide an exact `1444-11-11` relation; independent linework, two-sided masks, or a source-based zone spanning the complete usable corridor; exact source pins and license lineage; transformations, controls, residuals and fixed error budget; an exhaustive current-to-proposed mapping for actors, all five facets and relationships; proof that neither modern dispatch nor candidate edges choose or validate values; predeclared affected and neighboring QA impact; and independent hash reproduction. An applicability route additionally requires an exhaustive land-adjacent actor-pair disposition bound to passing positive anchors.
