# M25C Task 16 region 145 evidence review

Status: **rejected**
Review date: `2026-08-23`
Start date: `1444-11-11`
Scope: Saudi Arabia–Yemen corridor and Western Asia positive-border gate

## Disposition

The seam reproduces the complete modern line at 1.0; inherited dispatch and a stale candidate-derived Ottoman–Qara edge/mask path disqualify the packet.

No corridor, packet, generator, assembled artifact, tolerance, or permission changes are authorized in this review. No evidence-supported old/new mapping exists.

## Frozen hash bindings

| Input | SHA-256 |
| --- | --- |
| `scripts/generate-m25c-region-145-packet.py` | `4f68b9e42253ff69d0d14012b1d8fb70b3cd2c0c73941068767ccea2be523d5a` |
| `research/start-dates/1444-global-v1/regional-packets/145-western-asia-2026-08-15.json` | `14a98dbf36884cd9eec5f6f446cc8b1ce929553df5da0c983e696d8b51a97658` |
| `research/start-dates/1444-global-v1/regional-packets/assets/145/negative-controls.geojson` | `0c45e78be92a7528c3d57148c1a86f0845258f4d14a9c2247c01899cf643f5c9` |
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

- Assertion: `region-145-negative-modern-saudi-arabia-yemen-seam`
- Boundary feature: `forbidden-modern-saudi-arabia-yemen-seam`
- Relation: `regional_status_boundary_matches_forbidden_modern_seam_ratio_lte`
- Corridor: fixed `75 km`; tolerance: fixed `0.20`; unit: ratio
- Result: `fail`; reference=1199.5228998211442 km; usable=1199.5228998211442 km; covered=1199.522899821144 km; coverage=0.9999999999999998; matched=1199.5228998211442 km; measurement=1.0; transitions=4; normal samples=240; missing=0; ambiguous=0; eligibility rejections: unknown_required_facet=346.
- Affected-component count: `31`

## Current affected values

- Actors: `scenario-mam`; relationships: `controller, owner, sovereign`; facets: `{"authority": "administered", "habitability": "habitable", "population_presence": "resident", "settlement_pattern": "nucleated", "tenure": "polity_associated"}`; components (16): `cmp-prv_10837a2172966f5f2860`, `cmp-prv_19e334909b82ba0c124b`, `cmp-prv_390b0f50ec60dc9c5e75`, `cmp-prv_3ff2b1069fc865edff0e`, `cmp-prv_49176f1b895dafa01d2c`, `cmp-prv_5986861fd8626e34dff4`, `cmp-prv_71b2ef86f14e58f91e0a`, `cmp-prv_72db9c7ffa787827b62b`, `cmp-prv_7492b1be2c3c5dab3767`, `cmp-prv_7c3b73ba5054c5be2090`, `cmp-prv_93925f31a9b8c6b84f6a`, `cmp-prv_a99edfebe691a1ce6534`, `cmp-prv_ba45d7ee730668e915b8`, `cmp-prv_d1a7f25a63511596cd73`, `cmp-prv_d2aa7847a8a86038808b`, `cmp-prv_f5652a851683274e873e`
- Actors: `scenario-rasulid`; relationships: `controller, owner, sovereign`; facets: `{"authority": "administered", "habitability": "habitable", "population_presence": "resident", "settlement_pattern": "nucleated", "tenure": "polity_associated"}`; components (15): `cmp-prv_0e4f9dad3046d99be0da`, `cmp-prv_1d12145e0161b2782f52`, `cmp-prv_411771195d07cc70e98a`, `cmp-prv_48e592251f9b66a19550`, `cmp-prv_6945e4d6ae969c94f035`, `cmp-prv_7e19876155939d9c9215`, `cmp-prv_8a7d619e7a05e0455529`, `cmp-prv_9de3013e2fcf0eabe509`, `cmp-prv_a5a16abbdff35b7ea297`, `cmp-prv_b670e14e6dfccfaf5ef1`, `cmp-prv_bcfe8332d10b33d7a097`, `cmp-prv_c1dbb60b624bca2ce88f`, `cmp-prv_c3d50b921ee8e1bf7825`, `cmp-prv_c8ecc6ff2d1acaadb50a`, `cmp-prv_de81297b9a89a81b5987`

## Applicability and provenance audit

No complete land-adjacent actor-pair audit supports not_applicable on this packet.

The generator/packet review found no permissible path that silently reuses candidate-derived historical geometry or modern-country dispatch. Where the generator does use inherited or ADM0/ADM1 dispatch, coordinate sheets, or candidate shared-edge extraction, that path is a rejection reason and may not be promoted. The packet contains no independently complete exact-date two-sided source-to-component mapping. Checked centers establish positive locations, not territorial extents.

## Source pins

| Source | Pin SHA-256 | License | Transformations / derived assets | Exact locator |
| --- | --- | --- | ---: | --- |
| `cambridge-anatolia-1300-1451` | `3dc0784c5a237fce56dc89f6a212d4cab45d7b5c9d032daf12dd70f4c6c4301c` | Citation/link only | 0 / 0 | Chapter 4 > Anatolia, 1300-1451 > Ottoman recovery and the surviving Anatolian political fabric before 1453 |
| `cambridge-georgia-collegial` | `49d18c71c8325000368c62320555c45eccbacc51050b15ccec80b9be9846ac71` | Citation/link only | 0 / 0 | Article extract > fifteenth-century Bagratids and the kingdom's dissolution only at the end of the century |
| `cambridge-islamic-fleets` | `eaa8f460771034e48b2ac4bc67ff865b686c97af2653db7a7e3e83cef2960047` | Citation/link only | 0 / 0 | Chapter summary > Rasulid Yemen, Aden, and the Red Sea-Indian Ocean route through the fifteenth century |
| `cambridge-lusignan-cyprus` | `a29bb142b5123484c5587aff5eb4e897120525df501401f2efde2996d99bc0ad` | Citation/link only | 0 / 0 | Chapter text > Lusignan dynasty rule of Cyprus, 1192-1473 |
| `cambridge-mamluk-sultanate` | `b455a35a630919d4094cdad1f212ea2c5244174a3cbc0458931b96340bb2c6a3` | Citation/link only | 0 / 0 | Book description > Mamluk rule of Egypt, Syria, and the Arabian Red Sea hinterland, 1250-1517 |
| `cambridge-ottoman-expansion` | `6c3bdaf7bba1cfd8f195c902cf178a4c10e83509439aa47715f003deb838283d` | Citation/link only | 0 / 0 | Chapter 17, pp. 449-469 > Ottoman expansion and military power, 1300-1453 |
| `cambridge-varna-chronology` | `013786b1123358fe3a3322d9a17681810c4367931faa677810643ee784524069` | Citation/link only | 0 / 0 | Chronology > 10 November 1444 > Ottoman victory at Varna |
| `cambridge-western-asia-persian-gulf` | `9b6c9929496b47ca0c179cb1330daf1fbcca73394080a73d503236438d755ba4` | Citation/link only | 0 / 0 | Chapter 17, pp. 515-521 > Jahan Shah, Qara Qoyunlu Iraq, and the fifteenth-century Persian Gulf |
| `met-arabian-peninsula` | `5f9be1a4404f8fce980a14bf40b11870261e02d61932569a1c26d75c637f6c34` | Citation/link only | 0 / 0 | Timeline > 1400 A.D.-1450 A.D.; Key Events > Rasulids, Mamluk ties, and fragmented Arabian rule |
| `regional-survey-145` | `45a39a7266977e03b075366fdeb2f385ffeb7e4ae09454c3db8c304021f6fdec` | Citation/link only; no source text redistributed | 0 / 0 | Timeline > 1400 A.D.-1450 A.D.; Overview; Key Events > Anatolia and the Caucasus |
| `shepherd-historical-atlas` | `c4bfd6f0380fd3718011672a833a89c0fb7c127f9fcd0416bd0a61cd4e475da4` | Public-domain scan; citation and link only | 0 / 0 | Historical Atlas > Anatolia, Caucasus, Syria, Mesopotamia, and Arabia plates covering 1400-1500 |
| `natural-earth-admin0-5.1.1-region-145` | `a993b6862091d0edcbab92b0c2eeb86d821dff35b98b061991d39f0d19204bbc` | Public domain | 1 / 1 | Admin-0 countries 5.1.1 > ADM0_A3 shared boundary SAU-YEM |

Historical records with empty transformations/derived assets cannot supply missing linework. Modern Natural Earth records remain negative controls only. Any source used for future geometry requires exact reusable licensing, extraction and CRS details, control points, residuals, uncertainty, and a predeclared error budget.

## QA and permissions

Current region findings: `MISSING_POSITIVE_BORDER_ASSERTION`, `SPATIAL_ASSERTION_FAILED`, `UNCERTIFIED_A_GRADE`. This disposition changes none of them. The frozen worldwide result remains 58 non-review errors and one warning. Candidate, review, certification, runtime, publication, release, and deployment permissions remain unchanged.

## Replacement requirements

A replacement packet must provide an exact `1444-11-11` relation; independent linework, two-sided masks, or a source-based zone spanning the complete usable corridor; exact source pins and license lineage; transformations, controls, residuals and fixed error budget; an exhaustive current-to-proposed mapping for actors, all five facets and relationships; proof that neither modern dispatch nor candidate edges choose or validate values; predeclared affected and neighboring QA impact; and independent hash reproduction. An applicability route additionally requires an exhaustive land-adjacent actor-pair disposition bound to passing positive anchors.
