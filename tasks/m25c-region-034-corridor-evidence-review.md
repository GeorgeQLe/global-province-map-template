# M25C Task 16 region 034 evidence review

Status: **rejected**
Review date: `2026-08-23`
Start date: `1444-11-11`
Scope: India–Bangladesh / Raichur corridor and Southern Asia positive-border gate

## Disposition

The seam fails at full coverage; no independent Raichur point, zone, or line qualifies, and the stale generator can recreate a retired candidate-derived edge.

No corridor, packet, generator, assembled artifact, tolerance, or permission changes are authorized in this review. No evidence-supported old/new mapping exists.

## Frozen hash bindings

| Input | SHA-256 |
| --- | --- |
| `scripts/generate-m25c-region-034-packet.py` | `27a04a30153d8364d265c318fe1343f5b1b775b2e795bf146ed118ceb629112c` |
| `research/start-dates/1444-global-v1/regional-packets/034-southern-asia-2026-08-16.json` | `13282e87602dfd8909d727021e5618ef632407a33fd0672a5496c07c32f94b2d` |
| `research/start-dates/1444-global-v1/regional-packets/assets/034/negative-controls.geojson` | `d2ced23773460761b8281587ac892991c1eff27ac39ffa8ff61cacdabfa48c14` |
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

- Assertion: `region-034-negative-modern-india-bangladesh-seam`
- Boundary feature: `forbidden-modern-india-bangladesh-seam`
- Relation: `regional_status_boundary_matches_forbidden_modern_seam_ratio_lte`
- Corridor: fixed `75 km`; tolerance: fixed `0.20`; unit: ratio
- Result: `fail`; reference=2382.08845976948 km; usable=2368.69131357248 km; covered=2368.69131357248 km; coverage=1.0; matched=1901.2234460370935 km; measurement=0.798133015690391; transitions=24; normal samples=474; missing=0; ambiguous=0; eligibility rejections: unknown_required_facet=218.
- Affected-component count: `54`

## Current affected values

- Actors: `scenario-ben`; relationships: `controller, owner, sovereign`; facets: `{"authority": "administered", "habitability": "habitable", "population_presence": "resident", "settlement_pattern": "nucleated", "tenure": "polity_associated"}`; components (41): `cmp-prv_05607100605ba59f8fae`, `cmp-prv_0ae597e52e89e62f85aa`, `cmp-prv_0bb6230f22f884c0a943`, `cmp-prv_102fb5a138e67755d986`, `cmp-prv_297054632940bbab9f2f`, `cmp-prv_2c35b77912f1f5fd56d9`, `cmp-prv_2cb8f4df3bccecbae526`, `cmp-prv_2e38db5bde00ade4a19c`, `cmp-prv_344d7212ddda0f1b6a86`, `cmp-prv_3c52bd498afd5da1acc3`, `cmp-prv_3ef6d6ca6f983ccd4e63`, `cmp-prv_454fc98b0ec186699fe3`, `cmp-prv_4ddd8727d2e2a294eb3e`, `cmp-prv_4ff01fe121b07ab65221`, `cmp-prv_52bdb5ae6a08ab4d9d43`, `cmp-prv_5572bcac8892345500f7`, `cmp-prv_5cf9aeaf69057c9e1109`, `cmp-prv_61d1a3ec4b8fe8f5db37`, `cmp-prv_66500b78fac530e49a97`, `cmp-prv_6697834c8ab457a1fdac`, `cmp-prv_6a07a5c3c4fd7cf551bf`, `cmp-prv_70bc912a89f8fd4f1d2d`, `cmp-prv_77fe6d42fa010fbb15ae`, `cmp-prv_7923be9911d35ebee86d`, `cmp-prv_7b1fa0eec215c573e9d1`, `cmp-prv_85f533bec517936e7c6a`, `cmp-prv_88384589fe6537711920`, `cmp-prv_99ca481db4fa3beaa7b5`, `cmp-prv_9e62cb35eaf5ae756afa`, `cmp-prv_a1e8ee78025a9e18d56e`, `cmp-prv_a3c219f0ebc2c01a1a6f`, `cmp-prv_b950e8368e6cd92bddac`, `cmp-prv_ba1e1d08180e82da2777`, `cmp-prv_bc0d496cbb0318553a49`, `cmp-prv_bf9740c8fa0f5d717609`, `cmp-prv_dd345c9abf9794dc5031`, `cmp-prv_df3eacfa867eea43b983`, `cmp-prv_e60f94f9a832b987670c`, `cmp-prv_e803d88372f8f0b53036`, `cmp-prv_ec144310cfbfe376d3d0`, `cmp-prv_f8042e915f7b4270f044`
- Actors: `scenario-del`; relationships: `controller, owner, sovereign`; facets: `{"authority": "administered", "habitability": "habitable", "population_presence": "resident", "settlement_pattern": "nucleated", "tenure": "polity_associated"}`; components (11): `cmp-prv_053e856246cf657683d4`, `cmp-prv_0b63c15666f1c234ce92`, `cmp-prv_0f26923ceb9a3f98d906`, `cmp-prv_0fa45b7c73825a5b22da`, `cmp-prv_203bb0d6d38264b8b3c6`, `cmp-prv_3b0f28da02e0df4fbac0`, `cmp-prv_41063cb9027c776aeb8b`, `cmp-prv_7eb6c65e0e5e4ff2949f`, `cmp-prv_9d259c38431f416dbc15`, `cmp-prv_9f6fc8e9a8d78a5e8e93`, `cmp-prv_e2ebef350bb62f2dbfa3`
- Actors: `scenario-gajapati`; relationships: `controller, owner, sovereign`; facets: `{"authority": "administered", "habitability": "habitable", "population_presence": "resident", "settlement_pattern": "nucleated", "tenure": "polity_associated"}`; components (1): `cmp-prv_40d06792b72db24298ce`
- Actors: `scenario-mrauk-u`; relationships: `controller, owner, sovereign`; facets: `{"authority": "administered", "habitability": "habitable", "population_presence": "resident", "settlement_pattern": "nucleated", "tenure": "polity_associated"}`; components (1): `cmp-prv_f06a7347a11cdf20239d`

## Applicability and provenance audit

No complete land-adjacent actor-pair audit supports not_applicable on this packet.

The generator/packet review found no permissible path that silently reuses candidate-derived historical geometry or modern-country dispatch. Where the generator does use inherited or ADM0/ADM1 dispatch, coordinate sheets, or candidate shared-edge extraction, that path is a rejection reason and may not be promoted. The packet contains no independently complete exact-date two-sided source-to-component mapping. Checked centers establish positive locations, not territorial extents.

## Source pins

| Source | Pin SHA-256 | License | Transformations / derived assets | Exact locator |
| --- | --- | --- | ---: | --- |
| `biot-history` | `4ee0c1ede52894e1e38edfc5bdcef4b421381839ff63deb213a9128a9827a23d` | Citation/link only | 0 / 0 | History > Chagos Archipelago uninhabited until the late eighteenth century |
| `iranica-akbar` | `09440cac85b43282815779bb2840261a2e9301798b389287de9256954e95ee59` | Citation/link only | 0 / 0 | Article text > later conquests of independent Bengal, Malwa, Gujarat, Kashmir, Sind, and Orissa |
| `iranica-bahmani` | `3e1570ea927e8e05ba5aef3e26e7b394859e7979b17075b6f5e8370a4fb532f8` | Citation/link only | 0 / 0 | Article opening > Bahmanid kingdom, Deccan extent, and 1347 foundation |
| `iranica-dharval` | `198f05dfa1f48a77841cd4f271552048cbf502f0ca6b3601bc76e6964118b3a8` | Citation/link only | 0 / 0 | Article text > fifteenth-century Malwa and Sharqi Jaunpur courts |
| `iranica-gujarat` | `ab10e787729526f8a96ddf965a89c3fd8c026394f4c478263bad9e2cf57060c9` | Citation/link only | 0 / 0 | Independent kingdom > thirteen Gujarat sultans between 1414 and 1573 |
| `iranica-iran-chronology` | `7fb3cb2871384e6ce811b77d12ab1e48c43eacd7cab86879252b68c6e0bf80c9` | Citation/link only | 0 / 0 | Chronology > 1405 Shah Rukh accession; 1438-1467 Jahan Shah expansion |
| `kotte-municipal-history` | `f2d94523183fb7cc820991045babc52f58659f976600296e79b5dc5e979df496` | Citation/link only | 0 / 0 | History > early fifteenth-century Kotte as the seat of power in Sri Lanka |
| `regional-survey-034` | `d653efe0fdae1c59ca2f4398a0d186d569c3152c3f782c099229c67fb98e7e2f` | Citation/link only; no source text redistributed | 0 / 0 | Timeline > 1400 A.D.-1450 A.D.; Key Events > 1398 and 15th century |
| `shepherd-historical-atlas` | `13baa2c0c622736f89a1ec4d2a34057218ca696b8b43e97fd1e57683b2015f59` | Public-domain scan; citation and link only | 0 / 0 | Historical Atlas > India and adjacent countries plates covering 1400-1500 |
| `natural-earth-admin0-5.1.1-region-034` | `129bbc5b0923eb8935f9c0d8b497f4ade1d68b470ed6f379fbc32b7beb6d838a` | Public domain | 1 / 1 | Admin-0 countries 5.1.1 > ADM0_A3 shared boundary IND-BGD |

Historical records with empty transformations/derived assets cannot supply missing linework. Modern Natural Earth records remain negative controls only. Any source used for future geometry requires exact reusable licensing, extraction and CRS details, control points, residuals, uncertainty, and a predeclared error budget.

## QA and permissions

Current region findings: `MISSING_POSITIVE_BORDER_ASSERTION`, `SPATIAL_ASSERTION_FAILED`, `UNCERTIFIED_A_GRADE`. This disposition changes none of them. The frozen worldwide result remains 58 non-review errors and one warning. Candidate, review, certification, runtime, publication, release, and deployment permissions remain unchanged.

## Replacement requirements

A replacement packet must provide an exact `1444-11-11` relation; independent linework, two-sided masks, or a source-based zone spanning the complete usable corridor; exact source pins and license lineage; transformations, controls, residuals and fixed error budget; an exhaustive current-to-proposed mapping for actors, all five facets and relationships; proof that neither modern dispatch nor candidate edges choose or validate values; predeclared affected and neighboring QA impact; and independent hash reproduction. An applicability route additionally requires an exhaustive land-adjacent actor-pair disposition bound to passing positive anchors.
