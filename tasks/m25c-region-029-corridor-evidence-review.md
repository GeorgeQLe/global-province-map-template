# M25C Task 16 region 029 evidence review

Status: **rejected**
Review date: `2026-08-23`
Start date: `1444-11-11`
Scope: Haiti–Dominican Republic corridor and Caribbean positive-border gate

## Disposition

The negative seam passes, but 1492 reconstructed Taíno chiefdom maps do not establish an exact 1444 border and no complete applicability audit exists.

No corridor, packet, generator, assembled artifact, tolerance, or permission changes are authorized in this review. No evidence-supported old/new mapping exists.

## Frozen hash bindings

| Input | SHA-256 |
| --- | --- |
| `scripts/generate-m25c-region-029-packet.py` | `fea37adb354655d6cb9212470393b4973be782eea47100ba29f3575b63c82bf6` |
| `research/start-dates/1444-global-v1/regional-packets/029-caribbean-2026-08-16.json` | `22f06dcd561070fa9ee35eacc56c53dcdc2cf7b0a1b95024a66d49cfb861acf7` |
| `research/start-dates/1444-global-v1/regional-packets/assets/029/negative-controls.geojson` | `0f90431bd5f9d44eff94af2c386bb00e8d6a8ab44d1484cd449eeda80647268b` |
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

- Assertion: `region-029-negative-modern-haiti-dominican-seam`
- Boundary feature: `forbidden-modern-haiti-dominican-seam`
- Relation: `regional_status_boundary_matches_forbidden_modern_seam_ratio_lte`
- Corridor: fixed `75 km`; tolerance: fixed `0.20`; unit: ratio
- Result: `pass`; reference=259.42268516001866 km; usable=259.42268516001866 km; covered=259.42268516001866 km; coverage=1.0; matched=0.0 km; measurement=0.0; transitions=2; normal samples=52; missing=0; ambiguous=0; eligibility rejections: none.
- Affected-component count: `0`

## Current affected values

- Affected-component inventory is exactly empty; sampled components and preserved values are described below.

The three sampled components are `cmp-prv_10957e3931341658c957`,
`cmp-prv_5885e61148151e99beed`, and `cmp-prv_a4e37068e4fcc658a45f`.
Each has null `political_unit_id`, local-decentralized/habitable/resident/
nucleated/customary-community facets, and `territorial_presence` plus
`customary_tenure` relationships to `scenario-hispaniola-taino-chiefdoms`.
No value change is proposed.

## Applicability and provenance audit

No complete land-adjacent actor-pair audit supports not_applicable on this packet.

The generator/packet review found no permissible path that silently reuses candidate-derived historical geometry or modern-country dispatch. Where the generator does use inherited or ADM0/ADM1 dispatch, coordinate sheets, or candidate shared-edge extraction, that path is a rejection reason and may not be promoted. The packet contains no independently complete exact-date two-sided source-to-component mapping. Checked centers establish positive locations, not territorial extents.

## Source pins

| Source | Pin SHA-256 | License | Transformations / derived assets | Exact locator |
| --- | --- | --- | ---: | --- |
| `adlfi-anse-a-la-gourde` | `7931e1aff7dd3552645c06a7129c0ba89111305bd68f26264aaa4aecbb75982c` | Citation/link only | 0 / 0 | Anse a la Gourde > phased occupation through 1400 CE |
| `inrap-antilles-archaeology` | `da901c4f4169532585c2d338351fedd576772d9bcc67589e62ae22cfea566b7e` | Citation/link only | 0 / 0 | L'archeologie des Antilles > island-network interpretation and precolumbian sequence |
| `inrap-guadeloupe-history` | `b03d7c92616a0d1b1bff4c0c4b196145f51dfb04e296aeaa3bdb55f4d3d881f6` | Citation/link only | 0 / 0 | Guadeloupe, une histoire retrouvee > Amerindian settlement and material record |
| `inrap-martinique-anse-bellay` | `41520efc072afc137645d5a3fe9af9fba78b97707028edd1e06808162f2eef3f` | Citation/link only | 0 / 0 | Anse Bellay > late precolumbian Martinique evidence, eleventh-fourteenth centuries |
| `jas-st-eustatius-golden-rock` | `41ff15e3bf5669e7015e2717991bd8d3bc511abb15f8350d203202d27fabd268` | Citation/link only | 0 / 0 | Golden Rock > pre-Columbian settlement and inter-island exchange |
| `leiden-martinique-ansea-trabaud` | `42a3656b47157ba6c8d48ac7ae09a2c43bf20835d8b13f4a51d77d5c5a945343` | Citation/link only | 0 / 0 | Anse Trabaud > late precolonial Martinique coastal deposits |
| `leiden-precolumbian-saba-thesis` | `6bf7ef09a5cfb87269c58ad8c1ebf60fcb29b8dfbc41084cda348c4e0cc09d0d` | Citation/link only | 0 / 0 | Pre-Columbian Saba > settlement reports and late precolumbian social environment |
| `leiden-saba-first-inhabitants` | `afbb73be0310e8eac23b4ee475da8d54c01cf978252ace15017ec5296e6e454b` | Citation/link only | 0 / 0 | Saba's first inhabitants > Amerindian occupation through 1492 |
| `leiden-st-eustatius-archaeology` | `8faeab9188a45597c2e2645e48de68aa9d4d371a66e42b3daf6261873cd8914b` | Citation/link only | 0 / 0 | St. Eustatius > Amerindian sites and Golden Rock settlement |
| `nmai-caribbean-overview` | `69db8361b16500b0a00b25c3eb7e246f520d73018aef382e86011bff43eae5ab` | Citation/link only | 0 / 0 | Mesoamerica / Caribbean > Greater Antillean communities, Taino chiefdoms, and inter-island exchange |
| `nmai-lucayan-duho` | `306dc56613e7b1d93a527624e2760f799cd2035f130e93c17256cf1718e87517` | Citation/link only | 0 / 0 | Lucayan duho > AD 1000-1500; Bahamas and Turks and Caicos local chiefly tradition |
| `nmai-taino-gallery-guide` | `8920d75f1d530275f80b18a6a86d6d47b938a98ca6209c69bc6ff6f42ce177c1` | Citation/link only | 0 / 0 | Who Are the Taino? and map > Greater Antilles, Bahamas, Kalinago, and surrounding island communities |
| `pmc-east-guadeloupe-networks` | `58cf4433656577a18903df180726e6ccecf63c27d8a8189b72e64c6357465339` | Citation/link only | 0 / 0 | Late pre-colonial East-Guadeloupe > village networks and Anse a la Gourde sequence |
| `regional-survey-029` | `7db55825156991730f78122225d174849840f63f6e7434cf8110f20beb14aa78` | Citation/link only; no source text redistributed | 0 / 0 | Timeline > 1400 A.D.-1600 A.D.; Caribbean regional overview and pre-contact chronology |
| `royalsociety-caquetio-calibration` | `b622562d8efc1023558b2a1008667aad65287a1872c6875eccaa659205a2075c` | Citation/link only | 0 / 0 | Caquetio > Bonaire distribution and Dabajuroid archaeological association |
| `shepherd-historical-atlas` | `09cca3941de0e4c8fd25e7ae58edb8e8da0bb0fa9ef13e2e03aab51ab21bef71` | Public-domain scan; citation and link only | 0 / 0 | Historical Atlas > West Indies before sustained European colonization |
| `smithsonian-comparative-arawakan` | `fe388213934004404dba948fb1f5fa81c5eb33860bb7527ad3299e9a927e1bb5` | Citation/link only | 0 / 0 | Comparative Arawakan Histories > Taino regional variants, village organization, and district and provincial chiefdoms |
| `smithsonian-handbook-caribbean` | `bfffc0b8c82c914a679681f7fc550f62354f8129da0e30cd08fb3d6a36fbe858` | Citation/link only | 0 / 0 | Handbook of South American Indians IV > The West Indies, Arawak, Ciboney, Carib, and island ethnographies, pp. 495-565 |
| `springer-late-precolonial-saba-networks` | `cb72fce9c1019bd1420229c19582523df40049e1ec4c7fc6a215d03313bb9bb5` | Citation/link only | 0 / 0 | Remotely Local > Saba networks, AD 1000-1450 |
| `tandf-bonaire-isotopes` | `e58d85a32fff899b37f6f0c07177daf15b4b37d056e7c174d0d8d29e8b91d95f` | Citation/link only | 0 / 0 | Pre-colonial Bonaire > Indigenous lifeways and local residence evidence |
| `unesco-caribbean-archaeology` | `865379e892c667d3a2fc082bf8d8eaa5c368aef239bae5709312ce9dca79251a` | Citation/link only | 0 / 0 | Annex 2 > Pre-Hispanic Cultures of the Insular Caribbean; Greater and Lesser Antillean archaeological sequences |
| `yale-martinique-later-prehistory` | `177d825da15e07f4af31ff5509cdc3c4750edd448dabdc664c7e80bb4bbfbcec` | Citation/link only | 0 / 0 | Later prehistory in Martinique > 600-1450 CE sequence and Island-Carib identification limits |
| `natural-earth-admin0-5.1.1-region-029` | `48485bf38a1816139cf34a2ee87e6569006fc48138332492d2746cdfe835d7dd` | Public domain | 1 / 1 | Admin-0 countries 5.1.1 > ADM0_A3 shared boundary HTI-DOM |

Historical records with empty transformations/derived assets cannot supply missing linework. Modern Natural Earth records remain negative controls only. Any source used for future geometry requires exact reusable licensing, extraction and CRS details, control points, residuals, uncertainty, and a predeclared error budget.

## QA and permissions

Current region findings: `MISSING_POSITIVE_BORDER_ASSERTION`. This disposition changes none of them. The frozen worldwide result remains 58 non-review errors and one warning. Candidate, review, certification, runtime, publication, release, and deployment permissions remain unchanged.

## Replacement requirements

A replacement packet must provide an exact `1444-11-11` relation; independent linework, two-sided masks, or a source-based zone spanning the complete usable corridor; exact source pins and license lineage; transformations, controls, residuals and fixed error budget; an exhaustive current-to-proposed mapping for actors, all five facets and relationships; proof that neither modern dispatch nor candidate edges choose or validate values; predeclared affected and neighboring QA impact; and independent hash reproduction. An applicability route additionally requires an exhaustive land-adjacent actor-pair disposition bound to passing positive anchors.
