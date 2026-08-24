# M25C Task 16 region 057 evidence review

Status: **approval candidate; implementation deferred**
Review date: `2026-08-23`
Start date: `1444-11-11`
Scope: Yaren–Meneng corridor and Micronesia positive-border gate

## Disposition

Two independent audits reproduce 175 components, 13 internal edges, zero cross-actor pairs, one Nauru component, and eight passing anchors. This qualifies a serial no_land_adjacency applicability-record update; no mutation occurs in this run.

No corridor, packet, generator, assembled artifact, tolerance, or permission changes are authorized in this review. Proposed record-only mapping after this run: keep reason `no_land_adjacency` and `eligible_land_adjacent_actor_pairs: []`; replace the pending determination with the reproduced 175-component/13-edge/zero-pair statement; change `independent_review` from pending to a dated approval bound to the final unsigned record hash. The inventory hash is `575ae149139a84c428ceaac8231abe264356cf14a34547252babc5e3c666c867`; the current unsigned record hash is `0727cf4bea5d4c6cb7dcd1b91e35ba84c2b953732bd05697c68487b725435c86`. Components, seams, tolerances, geometry, packets, and permissions remain unchanged.

## Frozen hash bindings

| Input | SHA-256 |
| --- | --- |
| `scripts/generate-m25c-region-057-packet.py` | `0ad5b5a7e73f6a4483c0a5431475488e6ffd676aa700dd98a6908a0970cc1fa7` |
| `research/start-dates/1444-global-v1/regional-packets/057-micronesia-2026-08-16.json` | `738a78ec46c7e92bdc4ec7ac2cce611ac3b810a5f4077bae719f66e7f6fc0c3a` |
| `research/start-dates/1444-global-v1/regional-packets/assets/057/negative-controls.geojson` | `65dd4fe9feb290f67d0850fb323cb0ea76a64188569033d00150eddace662160` |
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

- Assertion: `region-057-negative-modern-yaren-meneng-seam`
- Boundary feature: `forbidden-modern-yaren-meneng-seam`
- Relation: `regional_status_boundary_matches_forbidden_modern_seam_ratio_lte`
- Corridor: fixed `75 km`; tolerance: fixed `0.20`; unit: ratio
- Result: `pass`; reference=1.9779682681512087 km; usable=1.9779682681512087 km; covered=1.9779682681512087 km; coverage=1.0; matched=0.0 km; measurement=0.0; transitions=0; normal samples=1; missing=0; ambiguous=0; eligibility rejections: unknown_required_facet=6.
- Affected-component count: `0`

## Current affected values

- Affected-component inventory is exactly empty; sampled components and preserved values are described below.

The sole sampled component is `cmp-prv_4e745baf4be695a48074`, with actor
`scenario-nauru-island-community`, local-decentralized/habitable/resident/
dispersed/customary-community facets, `territorial_presence` and
`customary_tenure`, and uncertainty `0.35`. No component value changes.

## Applicability and provenance audit

Independent audits agree: 175 components; 13 raw internal edges; zero cross-actor and eligible pairs; strict known-facet subset 169 components/12 edges; exactly one Nauru component cmp-prv_4e745baf4be695a48074.

The generator/packet review found no permissible path that silently reuses candidate-derived historical geometry or modern-country dispatch. Where the generator does use inherited or ADM0/ADM1 dispatch, coordinate sheets, or candidate shared-edge extraction, that path is a rejection reason and may not be promoted. The packet contains no independently complete exact-date two-sided source-to-component mapping. Checked centers establish positive locations, not territorial extents.

## Source pins

| Source | Pin SHA-256 | License | Transformations / derived assets | Exact locator |
| --- | --- | --- | ---: | --- |
| `craib-micronesian-prehistory` | `f3bc974a9664c45c8a8f118f179a74dc2e4d73b164be35c5c636aacd40abac33` | Citation/link only | 0 / 0 | Abstract > western and eastern Micronesian settlement and stratified high-island societies |
| `nps-assan-latte` | `837a60853f07413a17f8a4c49927209cd8ae2e1f9d003eb30b1cf42a6d57f4b5` | Citation/link only | 0 / 0 | Ancient Assan > active Latte-period occupation, 1100-1540 CE |
| `ono-intoh-tobi` | `03b1f015c1df390e524bc9e64c00e623f96166e493969d9150096b0b61e5b598` | Citation/link only | 0 / 0 | Abstract > Tobi occupation dated to the fifteenth and sixteenth centuries |
| `rainbird-carolines` | `ccf785b874c7b0956d2dde3da81afc9251114dff697e15f639d7a3490989b22e` | Citation/link only | 0 / 0 | Chapter 6 summary > Palau, Yap, Carolinian atolls, and high-island distinctions |
| `regional-survey-057` | `d0644ef6481fa03879895432598f89e505db3534eb182e4ab6ca3865f4f75dc2` | Citation/link only; no source text redistributed | 0 / 0 | Timeline > Oceania, 1400-1600 A.D.; regional chronology and cultural overview |
| `richards-leluh-tombs` | `9a886c06a084d4288fb37c7a0b5bc9ecec5693412f773d06124af1592ccbc266` | Citation/link only | 0 / 0 | Results and discussion > Leluh royal tomb chronology and eastern Micronesian political centre |
| `shepherd-historical-atlas` | `39357ed86ef1438fbba8714bc92168364f4e24bac7abc398e3d55334becbd07a` | Public-domain scan; citation and link only | 0 / 0 | Historical Atlas > Pacific island and world historical context |
| `thomas-kiribati-ecology` | `53e217ace44b326630d03b069582a0e39663693c970123f31ecbcdea09302897` | Citation/link only | 0 / 0 | Archaeology > Gilbert settlement and Line/Phoenix occupation-abandonment evidence |
| `unesco-nan-madol` | `b0e7c90d05bafd6f0725caf32d7a58316a75e9ecf1f55caa65693fc7fc13fd82` | Citation/link only | 0 / 0 | Outstanding Universal Value > Saudeleur ceremonial centre and chiefly society, 1200-1500 CE |
| `yamaguchi-majuro` | `d65d6d5802bee7e851308c1ac884b6a294353037a4387c18386e65503288923b` | Citation/link only | 0 / 0 | Abstract > Majuro colonization and long-lived pit-agriculture landscape |
| `natural-earth-admin1-5.1.1-region-057` | `75d2b16236327a5a9f7bd2f5127e8019bc8dbf9fdc3c81bff91778e1fd74142d` | Public domain | 1 / 1 | Admin-1 5.1.1 > ISO_3166_2 shared boundary NR-14-NR-11 |

Historical records with empty transformations/derived assets cannot supply missing linework. Modern Natural Earth records remain negative controls only. Any source used for future geometry requires exact reusable licensing, extraction and CRS details, control points, residuals, uncertainty, and a predeclared error budget.

## QA and permissions

Current region findings: `BORDER_APPLICABILITY_NOT_QUALIFIED`, `MISSING_POSITIVE_BORDER_ASSERTION`. This disposition changes none of them. The frozen worldwide result remains 58 non-review errors and one warning. Candidate, review, certification, runtime, publication, release, and deployment permissions remain unchanged.

## Replacement requirements

A replacement packet must provide an exact `1444-11-11` relation; independent linework, two-sided masks, or a source-based zone spanning the complete usable corridor; exact source pins and license lineage; transformations, controls, residuals and fixed error budget; an exhaustive current-to-proposed mapping for actors, all five facets and relationships; proof that neither modern dispatch nor candidate edges choose or validate values; predeclared affected and neighboring QA impact; and independent hash reproduction. An applicability route additionally requires an exhaustive land-adjacent actor-pair disposition bound to passing positive anchors.
