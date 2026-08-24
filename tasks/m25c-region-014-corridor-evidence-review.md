# M25C Task 16 region 014 corridor evidence review

Status: **reviewed; rejected before implementation**
Review date: `2026-08-23`
Start date: `1444-11-11`
Scope: Ethiopia-Somalia negative-control corridor and Eastern Africa positive-border gate

## Disposition

Do not implement a region `014` corridor reconstruction, positive border, or
border-applicability record from the current evidence packet. Preserve all
tolerances, assertions, assignments, candidate permissions, and release
permissions unchanged.

The packet establishes date-relevant Solomonic Ethiopia, Adal, Somali and
Swahili polities, interior political fields, island communities, and eight
positive centers. It does not supply an independently georeferenced,
exact-date, two-sided territorial line or a source-to-component mapping for
the fixed Ethiopia-Somalia corridor. More decisively, the current generator
resolves every province representative point to Natural Earth `ADM0_A3`
before dispatching historical actors through country-specific branches,
including separate `ETH`/`ERI`, `DJI`/`SOL`, and `SOM` branches. Task 16
expressly forbids modern-country dispatch.

The current stricter seam evaluator finds only partial eligible coverage and
correctly refuses to produce a ratio. Relabeling the same candidate-derived
geometry cannot qualify as historical remediation, and a positive border
cannot be manufactured from the resulting status edges.

This is a completed separate review, not an implementation approval. No old
value has an approved proposed replacement.

## Hash-bound review inputs

| Input | SHA-256 |
| --- | --- |
| `scripts/generate-m25c-region-014-packet.py` | `0a487001ae4a2d4217affba8455f17d076f7b39d2ec812b24c3737d5358f3de1` |
| `014-eastern-africa-2026-08-16.json` | `f5d73689ebddccd284b6bcdd7f38b0c814b113e6b84aa8a7477a7e66b50fb9a0` |
| `assets/014/negative-controls.geojson` | `6a6117c893bc7756d8f3845a1b87815e5066d3bbb0335e6064d86b60746616e8` |
| assembled `historical-territory-status.json` | `bcdb93f3d828bf87643e36f4d848499bfb6e67da87c5f52fe3474fce301ff080` |
| assembled `build.geojson` | `351542020590ed5b473b8f198a8e776d1d967c804e19e729b721ca74a6801e72` |
| assembled `golden.json` | `2ef4feede67d460631ab70ffd43b295d921af8d1b109698370722a1b836db4b8` |
| assembled `start_date_preflight.json` | `5726ea9e8b1b0a28129767bf595f9115f61c795acfd89b079edd168642e6805f` |
| assembled `sidecars/adjacency.csv` | `31a9e46a40011dd0a17508cf75ca92acb5334f8253ea160a5617b8e5140e5ff9` |
| assembled `sidecars/location_fabric_manifest.json` | `65882451f8e079bebf10d35dfe3c0ace740c6e7c184cd7fcfc1ccf84b4bafbf6` |

The reviewed status artifact is schema `0.2.0`, artifact
`1.0.0-assembled.1`, compatibility revision `2`, and scenario
`official-1444-global-v1`. The fabric manifest records geometry revision `1`.
Any hash or revision change requires a new separate review.

## Assertion and predeclared measurement

The exact existing assertion is
`region-014-negative-modern-ethiopia-somalia-seam`, using boundary feature
`forbidden-modern-ethiopia-somalia-seam` and relation
`regional_status_boundary_matches_forbidden_modern_seam_ratio_lte`.

- Corridor: fixed `75 km`
- Unit: ratio
- Maximum: fixed `0.20`
- Reference and usable length: `859.140267941493 km`
- Covered reference: `446.8760302018785 km`
- Coverage ratio: `0.5201432721487925`
- Matched eligible-transition length: `112.09505447498434 km`
- Measurement: null; non-executable
- Transitions: `10`
- Normal samples: `172`
- Missing side samples: `83`; ambiguous side samples: `0`
- Unknown-required-facet rejections: `169`
- Result: fail closed

The current preflight consequently retains
`MISSING_POSITIVE_BORDER_ASSERTION`, `NON_EXECUTABLE_SEAM_ASSERTION`,
`SPATIAL_ASSERTION_FAILED`, and downstream `UNCERTIFIED_A_GRADE` for region
`014`. The pre-phase-1 ratio is not a current executable result and must not be
used to approve edits under the stricter complete-coverage contract.

## Exact affected-component inventory

The evaluator reports 14 affected components. Their current values group as
follows; no proposed value is approved.

| Current actor and relationships | Current facets | Component IDs | Count |
| --- | --- | --- | ---: |
| `scenario-adal-sultanate`; `sovereign`, `owner`, `controller` | `administered`, `habitable`, `resident`, `nucleated`, `polity_associated` | `cmp-prv_044dfecf49ad03e35362`, `cmp-prv_0e06f25fb7efccaa8284`, `cmp-prv_34fa8dfdace4d03d4120`, `cmp-prv_3a657822abe4460a9995`, `cmp-prv_51006c5ccfa2a9bd551a`, `cmp-prv_66de2c7c93ba30bcdb4a`, `cmp-prv_76cf2b6e219c9d429da2`, `cmp-prv_7b125f62ac1a4260da29`, `cmp-prv_7d4622c51b2005967d3a`, `cmp-prv_c563780a5929daf2fdbb`, `cmp-prv_c74fc7000280040f91f9`, `cmp-prv_d8f23a73c22b40a2130a` | 12 |
| `scenario-solomonic-ethiopia`; `sovereign`, `owner`, `controller` | `administered`, `habitable`, `resident`, `nucleated`, `polity_associated` | `cmp-prv_e3f31b81263f8da64f79` | 1 |
| `scenario-northern-swahili-cities`; `territorial_presence`, `customary_tenure` | `local_decentralized`, `habitable`, `resident`, `nucleated`, `customary_community` | `cmp-prv_0ec1e99e804bf706c999` | 1 |

The full region contains 720 components: 173 administered/nucleated polity
rows, 82 decentralized/nucleated community rows, 195
decentralized/dispersed community rows, 52 decentralized/mobile seasonal
community rows, 49 uninhabited rows, and 169 all-unknown rows. The seam
evaluator rejects those 169 unknown-facet components relevant to its corridor
search. Only partial deterministic both-side coverage is available; it cannot
stand in for complete corridor reconstruction.

Every assignment in the packet is first classified by Natural Earth country.
The generator then chooses actors through explicit country branches and
coordinate rules. The `ETH`/`ERI` branch divides Solomonic Ethiopia from Adal,
the `DJI`/`SOL` branch chooses Adal, and the `SOM` branch divides Adal from
Ajuran/Somali actors. None of the reviewed locators enumerates corridor
component IDs, assigns both sides independently of `ADM0_A3`, or supplies a
transformation and error budget from historical geometry to the component
fabric.

## Evidence review

The most relevant pinned locators are:

| Source pin | Packet SHA-256 | What it supports | What it does not support |
| --- | --- | --- | --- |
| `regional-survey-014` | `3d691626104864e6c1db90dff2fbfae135b54760726c447f5b0bc866d2b3d42b` | Broad `1400-1600` Eastern African chronology and actors | A complete exact-date corridor fabric or component mapping |
| `unesco-general-history-africa-iv` | `cfd5e2cd08bcfd1db3bb8e7dd945d21965993a877b3b8bdb0cb020c9bfaa23a0` | Broad twelfth- to sixteenth-century chapters and regional maps | Packet-supplied control points, residuals, error budget, or exhaustive old/new mapping |
| `met-ethiopian-christianity` | `ccf95413e598c92d48d8c076dd26cd5f2a6fba0e0ff3a3a4d35a4279cbbf5889` | Zar'a Ya'eqob and the date-relevant Solomonic period | An Ethiopia-Adal territorial line |
| `british-museum-mogadishu` | `9cd4886234137acaf9e0894aaa9deddcc24ace7c1795608d6338adf79d671192` | Fifteenth- to sixteenth-century Mogadishu and Kilwa coinage context | A Horn frontier or full corridor disposition |
| `shepherd-historical-atlas` | `c8e8d3c1434d72a94d650d107e96d723fec179bb95cdcd6b7f40626b774cdf3b` | A public-domain atlas scan and broad African plate | An enumerated plate extraction, dated transformation, residual, or component binding |
| `natural-earth-admin0-5.1.1-region-014` | `c0f273de99aef4d203176c2bff34042e5e0de6e5f7c2ad8640b163e7f244b595` | The modern `ETH-SOM` negative-control reference only | Any positive historical actor assignment or frontier |

The repository's `2026-08-14` access audit records the regional survey as
reachable through browser retrieval after automated access rejection and the
Shepherd atlas as reachable by automated retrieval. The review makes no claim
beyond the packet's pinned locators and the repository's already reviewed
source record.

The packet has eight point build features for checked centers, no historical
boundary feature, and no historical derived file. Its only boundary and only
derived file are the modern Ethiopia-Somalia negative control. Every
historical source records an empty transformation and derived-artifact list;
all are citation/link-only, with Shepherd linking to a public-domain scan.
Thus the packet contains neither reusable historical linework nor a
provenance chain from a source map to the current component geometry.

## Rejection reasons

1. The generator's `nearest_country`/`final_actor` path makes Natural Earth
   `ADM0_A3` membership an input to every historical actor assignment. Its
   explicit Horn country branches violate the gate against modern-country
   dispatch.
2. Only `52.014327%` of the usable seam is covered by eligible status evidence;
   83 deterministic side samples are missing. The assertion is therefore
   non-executable under the approved complete-coverage contract.
3. The evidence has no independently derived exact-date line, two-sided mask,
   source control points, transformation, residual, or predeclared error
   budget for `1444-11-11`.
4. The evidence-to-record mapping is global and coarse. It cannot justify an
   enumerated old-to-new value for the 14 affected components or the unknown
   corridor coverage that must be reconstructed.
5. Lalibela, Zeila, Mogadishu, and the other checked centers prove positive
   locations, not a political border. A current status edge is
   candidate-derived and cannot validate itself as an independent
   positive-border assertion.
6. `not_applicable` is also unsupported. The packet models multiple bounded
   states and polities and supplies no complete land-adjacent actor-pair audit.

## Required replacement packet

A future region `014` packet may be reviewed only if it supplies all of the
following before edits:

- one exact claimed historical relation, not merely actor coexistence, a
  center, modern membership, or a later territorial maximum;
- independently derived and date-valid linework, a two-sided mask, or an
  explicit source-based corridor fabric spanning the full usable seam;
- exact locators, licensing, transformations, control points, residuals, and a
  fixed error budget;
- an exhaustive mapping from evidence to every proposed component old/new
  value, including relationships and all five facets;
- confirmation, demonstrable from the generator, that neither modern-country
  dispatch nor candidate-derived geometry chooses historical values;
- snapshot hashes, the fixed measurement and tolerance, expected affected and
  neighboring QA changes, and an independent hash review; and
- for a `not_applicable` proposal, the separately required complete
  land-adjacency disposition bound to positive historical anchors.

Until then, expected QA impact is exactly zero: no finding is cleared, no
component changes, and no review, certification, runtime, publication, or
deployment permission changes.
