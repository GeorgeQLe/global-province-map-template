# M25C Task 16 region 143 evidence review

Status: **rejected**
Review date: `2026-08-23`
Start date: `1444-11-11`
Scope: Kazakhstan–Uzbekistan corridor and Central Asia positive-border gate

## Disposition

The seam is non-executable; ADM0 dispatch and a stale candidate-derived Timurid–Moghulistan edge path disqualify the packet.

No corridor, packet, generator, assembled artifact, tolerance, or permission changes are authorized in this review. No evidence-supported old/new mapping exists.

## Frozen hash bindings

| Input | SHA-256 |
| --- | --- |
| `scripts/generate-m25c-region-143-packet.py` | `61c1912de2e00ea1365415cd5a97676fe174bea6f9e81cebf584233cb46d997e` |
| `research/start-dates/1444-global-v1/regional-packets/143-central-asia-2026-08-16.json` | `c2f3208a93722a4bd16aa1ae851805a6f3b6cb22f060a88a8790e4095a16f9a0` |
| `research/start-dates/1444-global-v1/regional-packets/assets/143/negative-controls.geojson` | `8715b02c0505b32b5534772b07a045021027b7e38dcf72d5b271e5b4c38c1573` |
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

- Assertion: `region-143-negative-modern-kazakhstan-uzbekistan-seam`
- Boundary feature: `forbidden-modern-kazakhstan-uzbekistan-seam`
- Relation: `regional_status_boundary_matches_forbidden_modern_seam_ratio_lte`
- Corridor: fixed `75 km`; tolerance: fixed `0.20`; unit: ratio
- Result: `fail`; reference=2181.0871832956723 km; usable=2181.0871832956723 km; covered=517.7748357013324 km; coverage=0.23739300274964842; matched=0.0 km; measurement=None; transitions=0; normal samples=437; missing=334; ambiguous=0; eligibility rejections: unknown_required_facet=290.
- Affected-component count: `0`

## Current affected values

- Affected-component inventory is exactly empty; sampled components and preserved values are described below.

The sampled components are `cmp-prv_34601d92a6a17ee72f6b`,
`cmp-prv_3831dbb44d03eebb3a4b`, `cmp-prv_794f3859ec43c6f5d7f9`,
`cmp-prv_931937374a8880402648`, and `cmp-prv_a4f5e2f3f0d017bf29ef`.
All retain `scenario-timurid-khwarazm`, administered/habitable/resident/
nucleated/polity-associated facets, and sovereign/owner/controller
relationships. No value change is proposed.

## Applicability and provenance audit

No complete land-adjacent actor-pair audit supports not_applicable on this packet.

The generator/packet review found no permissible path that silently reuses candidate-derived historical geometry or modern-country dispatch. Where the generator does use inherited or ADM0/ADM1 dispatch, coordinate sheets, or candidate shared-edge extraction, that path is a rejection reason and may not be promoted. The packet contains no independently complete exact-date two-sided source-to-component mapping. Checked centers establish positive locations, not territorial extents.

## Source pins

| Source | Pin SHA-256 | License | Transformations / derived assets | Exact locator |
| --- | --- | --- | ---: | --- |
| `iranica-abul-khayr-khan` | `6d79b12f84f606a440c02de347a238e9b031b7b22389c00bcb98137c099b4e14` | Citation/link only | 0 / 0 | Abu'l-Khayr Khan > 1428 election; 1430-31 Khwarazm withdrawal; 1446 Syr Darya conquests |
| `iranica-central-asia-v` | `d111bf0d3317146324af3dad56a6b19dea09ce3a2eebf20ffbb8ebfae3c256ca` | Citation/link only | 0 / 0 | Central Asia v > Timurid period: Shah Rukh, Ulugh Beg, and unconquered Moghulistan |
| `iranica-khujand` | `bf53786a8f11f81a394ef0f1ccad72142efdab8ec7d199845980ea79b4de10b1` | Citation/link only | 0 / 0 | Khujand > Timurid empire (1370-1507) administrative district and later 1503 Uzbek seizure |
| `iranica-qepcaq` | `1d07ca4443a21a30ba2837ed9b3e0a6ad6f5956447f0be6e0cb18693a0bbb124` | Citation/link only | 0 / 0 | Qepcaq > fifteenth-century Nogai and Abu'l-Khayr Uzbek hordes; Kazakh breakaway postdates 1444 |
| `regional-survey-143` | `e47029ef41847406855a39d7cbd852ab9c2a736ea6b8ea161b780c6adba69900` | Citation/link only; no source text redistributed | 0 / 0 | Timeline > 1400 A.D.-1600 A.D.; Key Events > Timurid and successor polities |
| `shepherd-historical-atlas` | `05943ebd61a883fd7cad45a50c7e48f621a6b0ad22290a7ac82c3bd9335bb476` | Public-domain scan; citation and link only | 0 / 0 | Historical Atlas > Asia 1400-1500 and Mongol-successor regional plates |
| `unesco-central-asia-timur` | `0548471be4dc3f30e45215902aec132905db713a131ceb3bbb0b3c43e23b611d` | Citation/link only | 0 / 0 | Central Asia under Timur > pp. 346-348, Timurid, Uzbek, and Moghulistan political geography |
| `natural-earth-admin0-5.1.1-region-143` | `d58f88b7250fbc98ef2445b16494fd29a916de700f7d4cd7369ccaab73594341` | Public domain | 1 / 1 | Admin-0 countries 5.1.1 > ADM0_A3 shared boundary KAZ-UZB |

Historical records with empty transformations/derived assets cannot supply missing linework. Modern Natural Earth records remain negative controls only. Any source used for future geometry requires exact reusable licensing, extraction and CRS details, control points, residuals, uncertainty, and a predeclared error budget.

## QA and permissions

Current region findings: `MISSING_POSITIVE_BORDER_ASSERTION`, `NON_EXECUTABLE_SEAM_ASSERTION`, `SPATIAL_ASSERTION_FAILED`, `UNCERTIFIED_A_GRADE`. This disposition changes none of them. The frozen worldwide result remains 58 non-review errors and one warning. Candidate, review, certification, runtime, publication, release, and deployment permissions remain unchanged.

## Replacement requirements

A replacement packet must provide an exact `1444-11-11` relation; independent linework, two-sided masks, or a source-based zone spanning the complete usable corridor; exact source pins and license lineage; transformations, controls, residuals and fixed error budget; an exhaustive current-to-proposed mapping for actors, all five facets and relationships; proof that neither modern dispatch nor candidate edges choose or validate values; predeclared affected and neighboring QA impact; and independent hash reproduction. An applicability route additionally requires an exhaustive land-adjacent actor-pair disposition bound to passing positive anchors.
