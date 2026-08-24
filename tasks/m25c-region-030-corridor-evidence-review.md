# M25C Task 16 region 030 evidence review

Status: **rejected**
Review date: `2026-08-23`
Start date: `1444-11-11`
Scope: China–Mongolia corridor and Eastern Asia positive-border gate

## Disposition

Inherited baseline dispatch chooses corridor actors, and the stale generator can recreate a circular candidate-derived Ming–Oirat edge.

No corridor, packet, generator, assembled artifact, tolerance, or permission changes are authorized in this review. No evidence-supported old/new mapping exists.

## Frozen hash bindings

| Input | SHA-256 |
| --- | --- |
| `scripts/generate-m25c-region-030-packet.py` | `f6cd827dd76e6bc4b1a1ffd3e1e20450bda0d630eddfcb4ff9f17a56c824af69` |
| `research/start-dates/1444-global-v1/regional-packets/030-eastern-asia-2026-08-16.json` | `a7553c0428cfe299bfbff6f172cbc66f7a66a9ef40dfd033ae7685ddcc000efb` |
| `research/start-dates/1444-global-v1/regional-packets/assets/030/negative-controls.geojson` | `a115dc81883273d137ef3cce92587259d26a10c770292fbc966322a5b8bf5958` |
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

- Assertion: `region-030-negative-modern-china-mongolia-seam`
- Boundary feature: `forbidden-modern-china-mongolia-seam`
- Relation: `regional_status_boundary_matches_forbidden_modern_seam_ratio_lte`
- Corridor: fixed `75 km`; tolerance: fixed `0.20`; unit: ratio
- Result: `fail`; reference=4465.649860500567 km; usable=4383.504958385515 km; covered=1667.053024268568 km; coverage=0.3803013889785946; matched=140.22187253166044 km; measurement=None; transitions=2; normal samples=877; missing=542; ambiguous=0; eligibility rejections: unknown_required_facet=723.
- Affected-component count: `41`

## Current affected values

- Actors: `scenario-mng`; relationships: `controller, owner, sovereign`; facets: `{"authority": "administered", "habitability": "habitable", "population_presence": "resident", "settlement_pattern": "nucleated", "tenure": "polity_associated"}`; components (34): `cmp-prv_042f5bf5740581649f7f`, `cmp-prv_0ba7945db618e6d9b534`, `cmp-prv_1314aaed2a796a1600c3`, `cmp-prv_2feb805ca958e59f32d2`, `cmp-prv_31bd5f4a485868b986db`, `cmp-prv_367267800ecebb822736`, `cmp-prv_367cbf5bde584bdb27fa`, `cmp-prv_3b8ba99613ba9e724fc4`, `cmp-prv_3f8a7050b966b264a7eb`, `cmp-prv_40eaa55ad1919e48b1f3`, `cmp-prv_453dd8a38f17827407bd`, `cmp-prv_4a5789951692fa67405f`, `cmp-prv_4c579f0f11f8f61fc73f`, `cmp-prv_545916d525f9e6eceedc`, `cmp-prv_5d308d27f303a7d6b1a1`, `cmp-prv_79713cbb02663a55f6f0`, `cmp-prv_7bdf5bc309142da14afa`, `cmp-prv_80eecd3d198a6458543c`, `cmp-prv_831ba83052c6961b8548`, `cmp-prv_84d23146a6f4902a3ebf`, `cmp-prv_8bf7efd6fc930364be17`, `cmp-prv_8cda69ef8f8341640769`, `cmp-prv_98dcb13eefe63056d143`, `cmp-prv_9accddcfdc34ec4cc80b`, `cmp-prv_a1e8abc2a9652acbf5a9`, `cmp-prv_a4e4df6d7ad5bbd65916`, `cmp-prv_ace39db3fa2370102513`, `cmp-prv_b5029e19bc6e947f6401`, `cmp-prv_be9223e6cbd6ce2b6ed2`, `cmp-prv_c7c76c81059aceeeba46`, `cmp-prv_d221a93a8f4ef4ca798d`, `cmp-prv_dfc78028d0aac062c0af`, `cmp-prv_f0b7bb9c734683e608dd`, `cmp-prv_fcb5d952e41371d242cd`
- Actors: `scenario-moghulistan`; relationships: `controller, owner, sovereign`; facets: `{"authority": "administered", "habitability": "habitable", "population_presence": "resident", "settlement_pattern": "nucleated", "tenure": "polity_associated"}`; components (7): `cmp-prv_2d3d08276989b2a29ed3`, `cmp-prv_5cafaeeb57b3262b0762`, `cmp-prv_798648d243a6911d0b4f`, `cmp-prv_b20365bc8e976996c302`, `cmp-prv_d2ef2ab81b685ca0be82`, `cmp-prv_d9ff72fa7a072619a848`, `cmp-prv_dbe8ed57217f25b35e26`

## Applicability and provenance audit

No complete land-adjacent actor-pair audit supports not_applicable on this packet.

The generator/packet review found no permissible path that silently reuses candidate-derived historical geometry or modern-country dispatch. Where the generator does use inherited or ADM0/ADM1 dispatch, coordinate sheets, or candidate shared-edge extraction, that path is a rejection reason and may not be promoted. The packet contains no independently complete exact-date two-sided source-to-component mapping. Checked centers establish positive locations, not territorial extents.

## Source pins

| Source | Pin SHA-256 | License | Transformations / derived assets | Exact locator |
| --- | --- | --- | ---: | --- |
| `cambridge-joseon-sejong` | `85a6e6511e4e2d0ecf29bb12a11dd0e9cf94382c49bc0068519787c4accf803a` | Citation/link only | 0 / 0 | Introduction summary > King Sejong reigned 1418-1450 and strengthened the Joseon throne |
| `cambridge-ming-allies` | `b4fe1f5d8660b3a4a1724484541a62cd2b35de630b91201a4e74bf982659b51c` | Citation/link only | 0 / 0 | Chapter 5 summary > Ming rulership coexisted with Oirat and other neighboring centers of power in the mid-fifteenth century |
| `cambridge-ming-oirat-frontier` | `393faa631550fb02cca8c911758997508858120a1fa0ac334ac6150ef0d8bb6c` | Citation/link only | 0 / 0 | Sample chapter > Western Mongols/Oirats under Esen after 1431 and before the 1449 Tumu campaign |
| `cambridge-ming-reigns` | `56e9257c31e1bbfa98467f35699daaff3e571231f0ce7d983c309e9d41254338` | Citation/link only | 0 / 0 | Frontmatter p. viii > Zhengtong emperor, first reign 1436-1449 |
| `cambridge-phagmodrupa` | `d2a1215ba3c2fb9628fcc658f5140862cbf22c2dd3e695ad077c6a6827019aae` | Citation/link only | 0 / 0 | Article text > Phagmodrupa hegemons ruled much of Central Tibet from the fourteenth to seventeenth centuries |
| `macao-government-brief-history` | `b9301d19c107cbd0bb93a9c18dc188404710e2147d43f0e3ba4a56c78c1757ce` | Citation/link only | 0 / 0 | Brief History > Portuguese reached Macao only in the early 1550s and established a city with local permission |
| `met-japan-muromachi` | `eb8f65148ebf29a77b1dac21c3508e45a38063d2ca1629e57d3e97130f136b90` | Citation/link only | 0 / 0 | Chronology > Muromachi period 1392-1573; Overview > Ashikaga military government and provincial daimyo |
| `regional-survey-030` | `5b538034d9be7d8fcc9d3c3e14a78b684c18ca5c0526e1cfda4bab4ed8e84be2` | Citation/link only; no source text redistributed | 0 / 0 | Timeline > 1400 A.D.-1600 A.D.; Overview > China under the Ming dynasty |
| `shepherd-historical-atlas` | `f3444978fe55bc7c8ba757d9099ec58f8544b2df77669e1a1def8f5f76e866d8` | Public-domain scan; citation and link only | 0 / 0 | Historical Atlas > East Asia plates covering 1400-1500 |
| `natural-earth-admin0-5.1.1-region-030` | `f078f1fb6d7dffe7d4dff18fff0b7edd0f978f3d04fbf44ea0f8dcf4ebc71c9d` | Public domain | 1 / 1 | Admin-0 countries 5.1.1 > ADM0_A3 shared boundary CHN-MNG |

Historical records with empty transformations/derived assets cannot supply missing linework. Modern Natural Earth records remain negative controls only. Any source used for future geometry requires exact reusable licensing, extraction and CRS details, control points, residuals, uncertainty, and a predeclared error budget.

## QA and permissions

Current region findings: `MISSING_POSITIVE_BORDER_ASSERTION`, `NON_EXECUTABLE_SEAM_ASSERTION`, `SPATIAL_ASSERTION_FAILED`, `UNCERTIFIED_A_GRADE`. This disposition changes none of them. The frozen worldwide result remains 58 non-review errors and one warning. Candidate, review, certification, runtime, publication, release, and deployment permissions remain unchanged.

## Replacement requirements

A replacement packet must provide an exact `1444-11-11` relation; independent linework, two-sided masks, or a source-based zone spanning the complete usable corridor; exact source pins and license lineage; transformations, controls, residuals and fixed error budget; an exhaustive current-to-proposed mapping for actors, all five facets and relationships; proof that neither modern dispatch nor candidate edges choose or validate values; predeclared affected and neighboring QA impact; and independent hash reproduction. An applicability route additionally requires an exhaustive land-adjacent actor-pair disposition bound to passing positive anchors.
