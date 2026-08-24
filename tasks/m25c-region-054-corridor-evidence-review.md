# M25C Task 16 region 054 evidence review

Status: **rejected**
Review date: `2026-08-23`
Start date: `1444-11-11`
Scope: Central Province–National Capital District corridor and Melanesia positive-border gate

## Disposition

The seam passes, but the applicability record omits seven eligible actor pairs and does not bind pair-specific zone-not-line evidence.

No corridor, packet, generator, assembled artifact, tolerance, or permission changes are authorized in this review. No evidence-supported old/new mapping exists.

## Frozen hash bindings

| Input | SHA-256 |
| --- | --- |
| `scripts/generate-m25c-region-054-packet.py` | `1861d7dbffbf8bf3251b7b619b0d4372a364568ccafc6623d05037445779a051` |
| `research/start-dates/1444-global-v1/regional-packets/054-melanesia-2026-08-16.json` | `e4e2e05ac3c78ff5eed5b684b8d8644bd5d565455ab2502162283d9175041780` |
| `research/start-dates/1444-global-v1/regional-packets/assets/054/negative-controls.geojson` | `a5cbc09ef7217113ffadb6e8957a2336311a42fe8a80bbdaa43a0f7198643afe` |
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

- Assertion: `region-054-negative-modern-central-province-national-capital-district-seam`
- Boundary feature: `forbidden-modern-central-province-national-capital-district-seam`
- Relation: `regional_status_boundary_matches_forbidden_modern_seam_ratio_lte`
- Corridor: fixed `75 km`; tolerance: fixed `0.20`; unit: ratio
- Result: `pass`; reference=44.3039628840024 km; usable=44.3039628840024 km; covered=44.303962884002395 km; coverage=0.9999999999999999; matched=0.0 km; measurement=0.0; transitions=7; normal samples=9; missing=0; ambiguous=0; eligibility rejections: none.
- Affected-component count: `0`

## Current affected values

- Affected-component inventory is exactly empty; sampled components and preserved values are described below.

Both sampled components, `cmp-prv_cf4c757fdbd71dcbc81b` and
`cmp-prv_ef15f4baa5e3896458af`, retain
`scenario-new-guinea-south-coast-communities`, local-decentralized/habitable/
resident/dispersed/customary-community facets, and `territorial_presence` plus
`customary_tenure`. No value change is proposed.

## Applicability and provenance audit

Independent audit: seven eligible pairs: Bismarck/Bougainville–Highlands, Bismarck/Bougainville–South Coast, Central–Western Solomons, Central/Southern–Northern Vanuatu, Eastern–Western Fiji, Highlands–North Coast, and Highlands–South Coast.

The generator/packet review found no permissible path that silently reuses candidate-derived historical geometry or modern-country dispatch. Where the generator does use inherited or ADM0/ADM1 dispatch, coordinate sheets, or candidate shared-edge extraction, that path is a rejection reason and may not be promoted. The packet contains no independently complete exact-date two-sided source-to-component mapping. Checked centers establish positive locations, not territorial extents.

## Source pins

| Source | Pin SHA-256 | License | Transformations / derived assets | Exact locator |
| --- | --- | --- | ---: | --- |
| `anu-degei-descendants` | `bd8a2b0a22106f4e4731ef152f134873c1d593036c29675c64475cabc8789c83` | Citation/link only | 0 / 0 | Introduction and polity chapters > distinct western Fijian political formations and limits of retrospective oral history |
| `anu-fiji-prehistory` | `43404fbc438bb430de2a8f4a0036ebe3f1315ab4ed7afe1855fc085b1df728de` | Citation/link only | 0 / 0 | Chapters 5-7 and 12-16 > Viti Levu, Beqa, Mago, chronology, and post-Lapita change |
| `anu-island-melanesia` | `25ee8c60c3ae752823c11478b7f3bd183bdbd362f32edad28f259d6f95a3ddc2` | Citation/link only | 0 / 0 | Overview and chapters 3-7 > regional diversity, landscapes, exchange, and cultural practice |
| `anu-vanuatu-puzzle` | `e8a332796206d86fcad3c96ba244c9e758f8b79dc062ac1d551583add28e51b3` | Citation/link only | 0 / 0 | Archaeology of North, South and Centre > later cultural transformations across the archipelago |
| `jso-new-caledonia` | `9cbecb35107d9ddd632647fe70163a408618ce85477e3ffac2f38361cffd84bb` | Citation/link only | 0 / 0 | Abstract and dated site discussion > second-millennium pre-European Kanak use of Grande Terre uplands |
| `regional-survey-054` | `7253b62afd0db20c5495cd0b6e8f11de13ecfeed3d5493a5c7b6cf00578aa3c2` | Citation/link only; no source text redistributed | 0 / 0 | Timeline > Oceania, 1400-1600 A.D.; regional chronology and cultural overview |
| `shepherd-historical-atlas` | `a56b73473291009273b2bcde0aa79206ff2d9e4875170bb634a2c40fbff1ca0e` | Public-domain scan; citation and link only | 0 / 0 | Historical Atlas > Australia, New Zealand, and Pacific island context |
| `unesco-kuk` | `91ddb03f0480773479e0aac22baad489d3ec1d5dd12ad48878a65ee4b5fccecd` | Citation/link only | 0 / 0 | Outstanding Universal Value > persistent traditional highland land use from 4000 BP to the present |
| `unesco-roi-mata-nomination` | `271a4cbe32fdfcfd27e81a7b98e32374c66be6255d53982629b09c0f927a634f` | Citation/link only | 0 / 0 | History and Development > chiefly title systems from 1200-1000 BP and the 1452 Kuwae disruption |
| `walter-sheppard-roviana` | `20f200175a0bddf9b5ebe45641cce2ef381810316e88b111662fa35169cc8455` | Citation/link only | 0 / 0 | Settlement chronology > faced shrines and coastal Roviana development from the fourteenth century |
| `natural-earth-admin1-5.1.1-region-054` | `43fc3297a1f9af96f0b4aa4c5cdfbc8b939adc2761f25829e9752f25e015384f` | Public domain | 1 / 1 | Admin-1 5.1.1 > ISO_3166_2 shared boundary PG-CPM-PG-NCD |

Historical records with empty transformations/derived assets cannot supply missing linework. Modern Natural Earth records remain negative controls only. Any source used for future geometry requires exact reusable licensing, extraction and CRS details, control points, residuals, uncertainty, and a predeclared error budget.

## QA and permissions

Current region findings: `BORDER_APPLICABILITY_NOT_QUALIFIED`, `MISSING_POSITIVE_BORDER_ASSERTION`. This disposition changes none of them. The frozen worldwide result remains 58 non-review errors and one warning. Candidate, review, certification, runtime, publication, release, and deployment permissions remain unchanged.

## Replacement requirements

A replacement packet must provide an exact `1444-11-11` relation; independent linework, two-sided masks, or a source-based zone spanning the complete usable corridor; exact source pins and license lineage; transformations, controls, residuals and fixed error budget; an exhaustive current-to-proposed mapping for actors, all five facets and relationships; proof that neither modern dispatch nor candidate edges choose or validate values; predeclared affected and neighboring QA impact; and independent hash reproduction. An applicability route additionally requires an exhaustive land-adjacent actor-pair disposition bound to passing positive anchors.
