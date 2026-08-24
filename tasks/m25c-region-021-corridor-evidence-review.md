# M25C Task 16 region 021 evidence review

Status: **rejected**
Review date: `2026-08-23`
Start date: `1444-11-11`
Scope: United States–Canada corridor and Northern America positive-border gate

## Disposition

The negative seam passes, but an exhaustive audit finds 14 eligible cross-actor land-adjacent pairs omitted by the empty applicability candidate.

No corridor, packet, generator, assembled artifact, tolerance, or permission changes are authorized in this review. No evidence-supported old/new mapping exists.

## Frozen hash bindings

| Input | SHA-256 |
| --- | --- |
| `scripts/generate-m25c-region-021-packet.py` | `1a4a64dda91285c227ebf7a3de8bd8fdc9f93854583fe90f88047ac8cd646fb2` |
| `research/start-dates/1444-global-v1/regional-packets/021-northern-america-2026-08-16.json` | `c6cc7ba9a335894dd4c1aae581da825d4af2c06b7a48c9ab3045adb4a4da3694` |
| `research/start-dates/1444-global-v1/regional-packets/assets/021/negative-controls.geojson` | `90b6a27ec57157118767f0135c7554cf7aa09e4b67fc146de0de08e3d53ab0f9` |
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

- Assertion: `region-021-negative-modern-us-canada-seam`
- Boundary feature: `forbidden-modern-us-canada-seam`
- Relation: `regional_status_boundary_matches_forbidden_modern_seam_ratio_lte`
- Corridor: fixed `75 km`; tolerance: fixed `0.20`; unit: ratio
- Result: `pass`; reference=7789.849675411947 km; usable=7789.849675411947 km; covered=7789.849418641007 km; coverage=0.9999999670377542; matched=1445.4349693899164 km; measurement=0.18555364090687387; transitions=14; normal samples=1558; missing=0; ambiguous=0; eligibility rejections: unknown_required_facet=183.
- Affected-component count: `180`

## Current affected values

- Actors: `scenario-columbia-plateau`; relationships: `customary_tenure, territorial_presence`; facets: `{"authority": "local_decentralized", "habitability": "habitable", "population_presence": "resident", "settlement_pattern": "dispersed", "tenure": "customary_community"}`; components (14): `cmp-prv_13209b581b2c146cb5d1`, `cmp-prv_3c6dd17496148f9c64d5`, `cmp-prv_52c548ff8c78c74be39c`, `cmp-prv_5ba1002a0774e84a74ca`, `cmp-prv_804d6646cfe97ba8117c`, `cmp-prv_91157c9fb8e27229cfe8`, `cmp-prv_b5cbadf798df1f6a6296`, `cmp-prv_ccb32243586bf8723de2`, `cmp-prv_d2cb3e1529714068b064`, `cmp-prv_d50e63b89026a954455d`, `cmp-prv_dc7ee46e02c051fba1de`, `cmp-prv_e50f6517462b69eac774`, `cmp-prv_e8efb6c47e9a68ff9036`, `cmp-prv_f2424f28db0282cb8e71`
- Actors: `scenario-eastern-woodlands`; relationships: `customary_tenure, territorial_presence`; facets: `{"authority": "local_decentralized", "habitability": "habitable", "population_presence": "resident", "settlement_pattern": "dispersed", "tenure": "customary_community"}`; components (38): `cmp-prv_02fe5abcb51976c42c9c`, `cmp-prv_0868d9ef21a65b0c6dbc`, `cmp-prv_0f8eb0b9efe951b1371b`, `cmp-prv_13ceec4f20b059db540a`, `cmp-prv_1ac6ffbaf1fb703da7be`, `cmp-prv_200d3ecc115dba948570`, `cmp-prv_287e3e2000adad37c452`, `cmp-prv_293a8ed560287f2f17c0`, `cmp-prv_3376450c0dc54683f0c4`, `cmp-prv_41261ce81f6e7547fd78`, `cmp-prv_4600d7cfd77148348bb5`, `cmp-prv_466961ca6e4f89fb7b0f`, `cmp-prv_5d8343f37e3cd63c46ac`, `cmp-prv_7088dbaa5b433ada6aff`, `cmp-prv_70ddadd285cc4bcd7876`, `cmp-prv_73f0393647e0762921bf`, `cmp-prv_87a34e5f2d87df0437ac`, `cmp-prv_95efe37d9a718ca6074e`, `cmp-prv_9ca04b01e19243d644c8`, `cmp-prv_9f3591766cacdf304156`, `cmp-prv_9fdef2a4728fcfdc4121`, `cmp-prv_a1e4f497e4a9cd8265f8`, `cmp-prv_a3145071319c09d690b6`, `cmp-prv_ab59e720fe2edc6b0c5b`, `cmp-prv_b23719ff6e6bd337e573`, `cmp-prv_b32ad5889826db5f9236`, `cmp-prv_b4cd62e6d1e36b4f036e`, `cmp-prv_c6669ba2b1b144a912ad`, `cmp-prv_cb270018f6e0a12336ed`, `cmp-prv_cda14341a49fbad3dab9`, `cmp-prv_d2a1cace5818ea055319`, `cmp-prv_d4fcb8289b49ecf5e39c`, `cmp-prv_db5f98f21fb095cd9740`, `cmp-prv_e7c738ed7ef3f8f67ab9`, `cmp-prv_f8484a00005362e536ea`, `cmp-prv_fcd152ee09c4424e8572`, `cmp-prv_fd4b33cadfcca301c562`, `cmp-prv_fff37d5416164b670621`
- Actors: `scenario-iroquoian-villages`; relationships: `customary_tenure, territorial_presence`; facets: `{"authority": "local_decentralized", "habitability": "habitable", "population_presence": "resident", "settlement_pattern": "dispersed", "tenure": "customary_community"}`; components (57): `cmp-prv_0136671cf00a130c7720`, `cmp-prv_065bda4b5fce01da8da9`, `cmp-prv_0e337789a4fc06bd6e94`, `cmp-prv_0f82ae101a70b8f4a876`, `cmp-prv_10d03c1d09a9f5368b34`, `cmp-prv_155fcdf48eef9e8c3b23`, `cmp-prv_197cd5feee363db0479b`, `cmp-prv_1d2fbe7a4c1fa1f26a64`, `cmp-prv_23b81468e3eacb81eadd`, `cmp-prv_25a3e430a2ed843fca12`, `cmp-prv_2b3cec93c4610c9affe5`, `cmp-prv_2e3238446e8f9b202a58`, `cmp-prv_33c73a907d5200a838bd`, `cmp-prv_36a4355f8a840522890e`, `cmp-prv_4742a442cd15d1a5c63d`, `cmp-prv_481ccafac8de85019738`, `cmp-prv_48ca5af7177abf4f1957`, `cmp-prv_49573a5cd48a7817be7e`, `cmp-prv_57265fa75ea16cf3966e`, `cmp-prv_5eba9c7c052e672e6eae`, `cmp-prv_5f9163e7ed2e7fb04185`, `cmp-prv_6272b0d9d896b91fe907`, `cmp-prv_658ca101b0302d0ea5af`, `cmp-prv_686b77007a2e541b6714`, `cmp-prv_6aa8013da2757f9c844c`, `cmp-prv_6c13fd18821cbae1229a`, `cmp-prv_6ebd9d96d3dce8ecc7cd`, `cmp-prv_75df9d8fb61c6fddc873`, `cmp-prv_7db55b692778ff9bce2e`, `cmp-prv_7e05b01d27a5385ff1d2`, `cmp-prv_82ca128fe2b4a5b6772e`, `cmp-prv_856221e7158c9aea1807`, `cmp-prv_8d2d891ce22f3eb44def`, `cmp-prv_9dac7c428c1639cc715f`, `cmp-prv_a6c481692b84514be988`, `cmp-prv_a99c982fbc93a5f0c875`, `cmp-prv_b070632eae87c6aa5871`, `cmp-prv_b0968b637e8202cb2b4d`, `cmp-prv_b15be656ef6f6159f8ee`, `cmp-prv_b51affb69a369f7fe464`, `cmp-prv_b82a00727b528c06007c`, `cmp-prv_b860363cb5bc71ce2b44`, `cmp-prv_baa47a16726e9399368b`, `cmp-prv_bb4235e3f8858b9da4fb`, `cmp-prv_d7a8470664e9344970cc`, `cmp-prv_dad365ca6a9d35df55f3`, `cmp-prv_dc6a8de5ae6f17f861b4`, `cmp-prv_e5953a66f574f997ad6a`, `cmp-prv_e59ad88fced0641a1fd4`, `cmp-prv_eea9f143cb9f9419e62c`, `cmp-prv_ef64418bbab0a2d30e2a`, `cmp-prv_f083bafc3c7b0082f955`, `cmp-prv_f382505db658cbe2e203`, `cmp-prv_f9927a707797e6967c8b`, `cmp-prv_fa100d2f6bcda7a78cca`, `cmp-prv_fd154b96e7ebd9e5286d`, `cmp-prv_fe0b55e2539cf1124737`
- Actors: `scenario-northwest-coast`; relationships: `customary_tenure, territorial_presence`; facets: `{"authority": "local_decentralized", "habitability": "habitable", "population_presence": "resident", "settlement_pattern": "dispersed", "tenure": "customary_community"}`; components (45): `cmp-prv_05c5d291a71219f251e8`, `cmp-prv_0818302aa4c0aa89ec03`, `cmp-prv_0e26ad2010e711cd284e`, `cmp-prv_0fa0c8727ad9d45ea5ea`, `cmp-prv_14b7c0a1310a9534c573`, `cmp-prv_175381bdbf495812bc77`, `cmp-prv_18be59924653369dc4e4`, `cmp-prv_1a48042b33d54a5166ff`, `cmp-prv_1d5283d43492f269c232`, `cmp-prv_215104947078e0de24d9`, `cmp-prv_2ca62a1b4bf3aff468ac`, `cmp-prv_305bcc5066304e472a85`, `cmp-prv_3145d30c8fd31a9033b4`, `cmp-prv_3cabeaccb5ce556007e6`, `cmp-prv_44672e94653fa30b08fa`, `cmp-prv_45e4229b0cef372f6b39`, `cmp-prv_50f21ac2416844a4415a`, `cmp-prv_55ff9b06ffd3a87ecaf0`, `cmp-prv_617477cf60caee8554af`, `cmp-prv_67ccde2336c9d7e5d374`, `cmp-prv_6e414bb66568d267d0cb`, `cmp-prv_754039db67b893178de0`, `cmp-prv_870a1f302c68264f6059`, `cmp-prv_8fbc3656fbe73429cb23`, `cmp-prv_9af8351b7154f0c6a326`, `cmp-prv_9b55cfb003ba2880f8f7`, `cmp-prv_a0534a07b151d026c7c2`, `cmp-prv_a0f662afc265bae6062c`, `cmp-prv_a31217a98f89271793eb`, `cmp-prv_b53f5613fc8180d57049`, `cmp-prv_b94d451fb6a1430937aa`, `cmp-prv_b95308960667c52936c1`, `cmp-prv_cad164bc128e24798afa`, `cmp-prv_ce443cdd1aa0725f03e4`, `cmp-prv_ce9646fd9d23587ef89d`, `cmp-prv_d6f3f43976685c6fdc9e`, `cmp-prv_e71f6f17049e1ea72a72`, `cmp-prv_f4556789b94dca7f577d`, `cmp-prv_f661f431dc778c6ac87c`, `cmp-prv_f777994a54cd05e9c56e`, `cmp-prv_f786e253309948d67921`, `cmp-prv_fa7e303f4cb5b2b7eeed`, `cmp-prv_fcd631c4aa5dab3bf461`, `cmp-prv_ff794949d96c958abbc5`, `cmp-prv_ffb81dee54391469091f`
- Actors: `scenario-plains-communities`; relationships: `customary_tenure, seasonal_use, territorial_presence`; facets: `{"authority": "local_decentralized", "habitability": "habitable", "population_presence": "seasonal", "settlement_pattern": "mobile", "tenure": "customary_community"}`; components (26): `cmp-prv_00a126bea2b4d598f6bb`, `cmp-prv_0744b210d9d9047541dc`, `cmp-prv_1164031bc846372073f4`, `cmp-prv_120a28842399b82deca0`, `cmp-prv_164a7548f7ba78095fa7`, `cmp-prv_1ded2d776e0cd5119a57`, `cmp-prv_36b10a8614a10ca534ba`, `cmp-prv_3742ee68ae3b2115fb73`, `cmp-prv_462f1f0879b52aedefb4`, `cmp-prv_4c6f05e4a5844a86b791`, `cmp-prv_63766618af8ff29aed55`, `cmp-prv_665f3afff5cb2ca47635`, `cmp-prv_673602de29eb6a6c508d`, `cmp-prv_68b0e229884d840cffc3`, `cmp-prv_9549030292047c0f0b1b`, `cmp-prv_a1b553e40fe0146484a3`, `cmp-prv_b1095d3f4e7dea5d3b42`, `cmp-prv_b180b28a47ec543dc4bd`, `cmp-prv_b24ae0cbeee3c2a9005f`, `cmp-prv_d0c9ede0e62b57c03c2e`, `cmp-prv_d15618a6f75c826ed56c`, `cmp-prv_d54dc1952188f46d24d8`, `cmp-prv_d670e1d148264a2b31d4`, `cmp-prv_dc951e05f815c4ecb668`, `cmp-prv_dd59680000e83afd5275`, `cmp-prv_f1c48a634b0af341b32d`

## Applicability and provenance audit

Independent audit: 14 eligible cross-actor pairs (Columbia Plateau–Northwest Coast/Plains/Subarctic; Eastern Woodlands–Iroquoian/Mississippian/Plains/Subarctic; Hohokam–Puebloan; Iroquoian–Subarctic; Mississippian–Plains; Northwest Coast–Subarctic; Plains–Puebloan/Subarctic; Subarctic–Thule/Inuit).

The generator/packet review found no permissible path that silently reuses candidate-derived historical geometry or modern-country dispatch. Where the generator does use inherited or ADM0/ADM1 dispatch, coordinate sheets, or candidate shared-edge extraction, that path is a rejection reason and may not be promoted. The packet contains no independently complete exact-date two-sided source-to-component mapping. Checked centers establish positive locations, not territorial extents.

## Source pins

| Source | Pin SHA-256 | License | Transformations / derived assets | Exact locator |
| --- | --- | --- | ---: | --- |
| `canada-precolumbian-north-america` | `27dc137d505024b36d36ed15cc07e1445653a725644568b565ea96c4f688ebd7` | Citation/link only | 0 / 0 | Regional survey > fortified Iroquoian villages, Northwest Coast societies, and Arctic Thule descendants |
| `nps-coosa-chiefdom` | `7f6d2908b57d592034b8efa13ec084236556205955ab6ec66c5af51d7ee1ee60` | Citation/link only | 0 / 0 | Coosa Chiefdom > 1400-1600 CE political and settlement description |
| `nps-fort-vancouver-indian-country` | `7624f155eb6afb290612ce28db14e9022fa674daf507e6e35abc64f3d8a01f89` | Citation/link only | 0 / 0 | Indian Country, pre-1824 > dense Columbia Basin and lower-river village networks |
| `nps-hohokam-culture` | `ba372fd43b93c3d020193b32939c4dc6a6065ae6e0cd5167a5bea97f22ec8e1c` | Citation/link only | 0 / 0 | Hohokam Culture > Classic-period villages through about A.D. 1450 |
| `nps-mississippian-period` | `cd6f69ea0c7930279072f49c974639663d2710d647aba421cae53c439bb8ef78` | Citation/link only | 0 / 0 | Mississippian Period > large centers in decline or abandonment by the mid-1400s |
| `parks-canada-auyuittuq-thule` | `53e121402e87f8a389df0977f2a3cce60d3178a165f3f1dd1b17771888576be0` | Citation/link only | 0 / 0 | Pre-contact history > Thule predominance by A.D. 1200 and persistence through earliest contact |
| `parks-canada-droulers` | `4d7b78743c4a6a55e4c7003033eb385722e553d690701b8ec3a30872ff90661d` | Citation/link only | 0 / 0 | Backgrounder > mid-15th-century St. Lawrence Iroquoian village |
| `regional-survey-021` | `94eb346170f5c929ea2c5167ebee624599ae7dc2625c802409b2a3bd4b5cb1b1` | Citation/link only; no source text redistributed | 0 / 0 | Timeline > 1400 A.D.-1600 A.D.; North American regional overview and key events |
| `shepherd-historical-atlas` | `70268d749dac5a28e077ef9304d679757983749d79c9f41d4244fc43eab1fc66` | Public-domain scan; citation and link only | 0 / 0 | Historical Atlas > North America before sustained European colonization |
| `smithsonian-handbook-north-america` | `99f0354f0fdaef509fae117af3dc9c93dd7eb632988661e6e0be284c28735016` | Citation/link only | 0 / 0 | Handbook overview > culture-area volumes and cautions on diagrammatic territorial guides |
| `unesco-kujataa-norse` | `34403763a8d9f5e6d026361250a96894046ac3e386ecd2f1aa204db509ba1bb0` | Citation/link only | 0 / 0 | Outstanding Universal Value > Norse Greenlandic farming settlement from the 10th to 15th centuries |
| `natural-earth-admin0-5.1.1-region-021` | `1f8340c913a5e164b699ccf7dc6f01cb861a3f1ee57bb137f38fb7b64c87b8ef` | Public domain | 1 / 1 | Admin-0 countries 5.1.1 > ADM0_A3 shared boundary USA-CAN |

Historical records with empty transformations/derived assets cannot supply missing linework. Modern Natural Earth records remain negative controls only. Any source used for future geometry requires exact reusable licensing, extraction and CRS details, control points, residuals, uncertainty, and a predeclared error budget.

## QA and permissions

Current region findings: `BORDER_APPLICABILITY_NOT_QUALIFIED`, `MISSING_POSITIVE_BORDER_ASSERTION`. This disposition changes none of them. The frozen worldwide result remains 58 non-review errors and one warning. Candidate, review, certification, runtime, publication, release, and deployment permissions remain unchanged.

## Replacement requirements

A replacement packet must provide an exact `1444-11-11` relation; independent linework, two-sided masks, or a source-based zone spanning the complete usable corridor; exact source pins and license lineage; transformations, controls, residuals and fixed error budget; an exhaustive current-to-proposed mapping for actors, all five facets and relationships; proof that neither modern dispatch nor candidate edges choose or validate values; predeclared affected and neighboring QA impact; and independent hash reproduction. An applicability route additionally requires an exhaustive land-adjacent actor-pair disposition bound to passing positive anchors.
