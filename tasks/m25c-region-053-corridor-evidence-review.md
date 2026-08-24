# M25C Task 16 region 053 evidence review

Status: **rejected**
Review date: `2026-08-23`
Start date: `1444-11-11`
Scope: Western Australia–South Australia corridor and Australia and New Zealand positive-border gate

## Disposition

The seam reproduces the modern state line at 1.0; the applicability record omits 15 eligible actor pairs and includes unrelated region-035 evidence.

No corridor, packet, generator, assembled artifact, tolerance, or permission changes are authorized in this review. No evidence-supported old/new mapping exists.

## Frozen hash bindings

| Input | SHA-256 |
| --- | --- |
| `scripts/generate-m25c-region-053-packet.py` | `13ece2b723930134cff611b8152f10e2a0c465cfb089179decc873eca8082cab` |
| `research/start-dates/1444-global-v1/regional-packets/053-australia-new-zealand-2026-08-16.json` | `e2214485680a91b49eb8ce387ab6d3200f318fd7688876aa7d6fccf9dbce8e13` |
| `research/start-dates/1444-global-v1/regional-packets/assets/053/negative-controls.geojson` | `b0b819506cec2b8494ce59e39a02e7efbc15b248eb763874abf6a352c79f19bc` |
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

- Assertion: `region-053-negative-modern-western-australia-south-australia-seam`
- Boundary feature: `forbidden-modern-western-australia-south-australia-seam`
- Relation: `regional_status_boundary_matches_forbidden_modern_seam_ratio_lte`
- Corridor: fixed `75 km`; tolerance: fixed `0.20`; unit: ratio
- Result: `fail`; reference=629.0899325499873 km; usable=629.0899325499873 km; covered=629.0899325499873 km; coverage=1.0; matched=629.0899325499873 km; measurement=1.0; transitions=16; normal samples=126; missing=0; ambiguous=0; eligibility rejections: none.
- Affected-component count: `17`

## Current affected values

- Actors: `scenario-central-desert-communities`; relationships: `customary_tenure, territorial_presence`; facets: `{"authority": "local_decentralized", "habitability": "habitable", "population_presence": "resident", "settlement_pattern": "dispersed", "tenure": "customary_community"}`; components (7): `cmp-prv_73dba07ff3199f95f81f`, `cmp-prv_76943851f79f33e549ca`, `cmp-prv_a3f4ad13c37aba83ff72`, `cmp-prv_a79e09c76cf0c607e2f1`, `cmp-prv_c859302170a531d237a7`, `cmp-prv_d4edc7f99127f08d47dc`, `cmp-prv_fb7581acb4f70057ac0c`
- Actors: `scenario-murray-southeast-communities`; relationships: `customary_tenure, territorial_presence`; facets: `{"authority": "local_decentralized", "habitability": "habitable", "population_presence": "resident", "settlement_pattern": "dispersed", "tenure": "customary_community"}`; components (1): `cmp-prv_a6f87bf7efab85e0b4f1`
- Actors: `scenario-western-desert-communities`; relationships: `customary_tenure, territorial_presence`; facets: `{"authority": "local_decentralized", "habitability": "habitable", "population_presence": "resident", "settlement_pattern": "dispersed", "tenure": "customary_community"}`; components (9): `cmp-prv_050814ceca37acf68eb5`, `cmp-prv_462304966c3311f08638`, `cmp-prv_470f07a3ca9e58144a34`, `cmp-prv_615d857d4d81fb769acb`, `cmp-prv_6267a8d2821eb1a568bf`, `cmp-prv_8235f0ca53b9b49559cf`, `cmp-prv_9a4cf831abfb47f1436e`, `cmp-prv_e21081bd56b9413e5f05`, `cmp-prv_f590e20a8655d6f8e841`

## Applicability and provenance audit

Independent audit: 15 eligible cross-actor pairs; one NONE–Māori interface is ineligible. The applicability source closure also includes three IOA components with region-035 evidence.

The generator/packet review found no permissible path that silently reuses candidate-derived historical geometry or modern-country dispatch. Where the generator does use inherited or ADM0/ADM1 dispatch, coordinate sheets, or candidate shared-edge extraction, that path is a rejection reason and may not be promoted. The packet contains no independently complete exact-date two-sided source-to-component mapping. Checked centers establish positive locations, not territorial extents.

## Source pins

| Source | Pin SHA-256 | License | Transformations / derived assets | Exact locator |
| --- | --- | --- | ---: | --- |
| `aiatsis-indigenous-australia-map` | `8292e5d2a083f31080572becf5e7ebe24bd7eb9ab060907345573666ac0ecb16` | Citation/link only | 0 / 0 | Map scope note > general locations of language, social, or nation groups; boundaries explicitly not exact or fixed |
| `australian-government-norfolk-history` | `676241f6c6a421d3b7c4e2464b3ab5fed9cbb09455fed561dbd2b3f2789f9133` | Citation/link only | 0 / 0 | Norfolk Island history > single Polynesian occupation phase from about 1150 to about 1450 |
| `heritage-nz-rangihoua` | `8ce9ba11cd01c1d37ad5b2bed9423edaf6d3cd88eddd0a2dcb453ac747e4e4a3` | Citation/link only | 0 / 0 | Historical narrative > pre-contact Maori settlement and calibrated fourteenth- to fifteenth-century midden dates |
| `regional-survey-053` | `87de969e3f41cad31e46a50c0be8ca476ffca6549ee578b0045c8bddd577b672` | Citation/link only; no source text redistributed | 0 / 0 | Timeline > Oceania, 1400-1600 A.D.; regional chronology and cultural overview |
| `shepherd-historical-atlas` | `a56b73473291009273b2bcde0aa79206ff2d9e4875170bb634a2c40fbff1ca0e` | Public-domain scan; citation and link only | 0 / 0 | Historical Atlas > Australia, New Zealand, and Pacific island context |
| `teara-maori-settlement` | `726a005ac60943c988b89ee12870d44d79bbf1e21a82ecab1eebb46ee8c94438` | Citation/link only | 0 / 0 | When was New Zealand first settled? > radiocarbon and whakapapa evidence for permanent settlement around 1300 |
| `teara-tribal-organisation` | `2fcb9c7d7a58364d9e9ee35cefd0345ddb5f5c2bf0208ad61d9a0ed7868e1044` | Citation/link only | 0 / 0 | Tribal organisation > iwi and hapu as the principal pre-European political groupings |
| `unesco-budj-bim` | `7419da376b0b7c4d9c3eaa00e28bafae9d186f55b2765a01552b6862b55e34c4` | Citation/link only | 0 / 0 | Outstanding Universal Value > Gunditjmara cultural continuity and six-millennia aquaculture system |
| `unesco-kakadu` | `288709e43ff03c4d4d5db961e700fe120f1928b1a1afa7a98c99686e8c24d096` | Citation/link only | 0 / 0 | Outstanding Universal Value > continuous northern Australian cultural landscape, social structure, and ritual record |
| `unesco-murujuga` | `33dd15f6ecaf8eb2affdd1da52cdad1878fb81ddafcf9a0190abf7f66acfef9c` | Citation/link only | 0 / 0 | Outstanding Universal Value > Ngarda-Ngarli cultural continuity, Lore, and northwest Australian land-and-seascape |
| `unesco-uluru` | `de94aaf191fa7d76852d7e374714f9dbfe1e5fab28caaa0b81cc9f38569693f4` | Citation/link only | 0 / 0 | Outstanding Universal Value > Anangu living cultural landscape, Tjukurpa, and tens of thousands of years of continuity |
| `unesco-willandra` | `882cabf59440ad1c8d74e1fb0bce04710cfbab569f3a0e229731a9424a5795b9` | Citation/link only | 0 / 0 | Outstanding Universal Value > Aboriginal occupation record and continuing Traditional Tribal Group connections |
| `natural-earth-admin1-5.1.1-region-053` | `08dcb942d051a0472ca773b0fe9b7c2bdaec1ad07bb86c0e6810cbba4005864d` | Public domain | 1 / 1 | Admin-1 5.1.1 > ISO_3166_2 shared boundary AU-WA-AU-SA |

Historical records with empty transformations/derived assets cannot supply missing linework. Modern Natural Earth records remain negative controls only. Any source used for future geometry requires exact reusable licensing, extraction and CRS details, control points, residuals, uncertainty, and a predeclared error budget.

## QA and permissions

Current region findings: `BORDER_APPLICABILITY_NOT_QUALIFIED`, `MISSING_POSITIVE_BORDER_ASSERTION`, `SPATIAL_ASSERTION_FAILED`, `UNCERTIFIED_A_GRADE`. This disposition changes none of them. The frozen worldwide result remains 58 non-review errors and one warning. Candidate, review, certification, runtime, publication, release, and deployment permissions remain unchanged.

## Replacement requirements

A replacement packet must provide an exact `1444-11-11` relation; independent linework, two-sided masks, or a source-based zone spanning the complete usable corridor; exact source pins and license lineage; transformations, controls, residuals and fixed error budget; an exhaustive current-to-proposed mapping for actors, all five facets and relationships; proof that neither modern dispatch nor candidate edges choose or validate values; predeclared affected and neighboring QA impact; and independent hash reproduction. An applicability route additionally requires an exhaustive land-adjacent actor-pair disposition bound to passing positive anchors.
