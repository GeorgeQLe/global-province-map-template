# M25C Oceania assertion research

Status: **approved and implemented on 2026-08-21**
Start date: `1444-11-11`
Research date: `2026-08-21`

## Scope and result

The remaining missing-negative inventory is exact: Oceania regions `053`
(Australia and New Zealand), `054` (Melanesia), `057` (Micronesia), and `061`
(Polynesia). Each packet has positive site-containment assertions but no
negative-anachronism assertion. No Oceania packet currently has an
independently georeferenced positive border, and this research does not propose
one.

Admin-0 inland seams are not a sound common control for these four island
regions. Region `053` has no shared Australia-New Zealand land boundary;
regions `057` and `061` consist almost entirely of separated islands; and the
Indonesia-Papua New Guinea international line lies on the country-based M49
edge between regions `035` and `054`, so it would test regional scope exclusion
rather than Melanesian reconstruction.

The recommendation is therefore to use four exact modern Admin-1 seams from
the already downloaded Natural Earth `5.1.1` archive. They use the existing
schema-`0.3.0` compositional seam relation, fixed `75 km` corridor, and `0.20`
maximum ratio. This preserves one contract worldwide while selecting a
truthfully modern, land-valued control inside each region.

Fresh worldwide measurement produces one explicit failure, one pass, and two
non-executable failures:

- `053` reproduces the Western Australia-South Australia line exactly;
- `054` does not reproduce the Central Province-National Capital District line;
- `057` and `061` have no land-adjacent compositional status transition
  anywhere in their regions, so their seam assertions must fail closed with a
  null measurement rather than pass at a vacuous zero.

The latter two results are not evidence that Micronesian or Polynesian society
was undifferentiated. Their packets distinguish many island polities, but those
actors occupy disconnected islands. The current seam relation has no
land-adjacent transition to execute.

## Evidence findings

| Region | Modern-control and historical finding | Research disposition |
| --- | --- | --- |
| `053` Australia and New Zealand | Geoscience Australia records that the WA-SA border was fixed by a `1922` agreement around the 129th meridian and later survey work. AIATSIS warns that Aboriginal language, social, and nation-group locations are general, with boundaries neither exact nor fixed. The packet nevertheless changes compositional status exactly on the full modern WA-SA line. | Add the WA-SA seam as a negative control. Its `1.0` result is a direct modern-scaffold leak and must block certification. |
| `054` Melanesia | Papua New Guinea's Constitution creates the National Capital District and requires its boundary to be defined by Organic Law; the national Finance Department classifies NCD and Central as current province-level divisions. The packet's archaeological sources support local New Guinea community fabrics, not this constitutional capital-district perimeter. | Add the Central-NCD seam. Its measured `0.0` is a legitimate executable pass because region `054` has seven other land-adjacent status transitions. |
| `057` Micronesia | The Republic of Nauru currently uses Yaren and Meneng as separate districts and constituencies, and a UN map records their district geometry. The packet models one Nauru island community and contains no evidence for the exact modern district line in `1444`. | Add the Yaren-Meneng seam, but retain fail-closed non-executability until a land-adjacent historical status distinction exists. Do not infer that the modern line is historically false in every local sense; the assertion rejects only its unsupported exact reproduction as a territorial-status seam. |
| `061` Polynesia | The U.S. Census Bureau treats American Samoa's Eastern and Western districts as present-day primary legal subdivisions and publishes their boundary. NPS describes ancient Samoan governance through `aiga`, villages, and `matai`, while the U.S. territorial administration began in `1900`. The packet intentionally uses one broad Samoan chiefly-community actor on Tutuila. | Add the Western-Eastern district seam, but retain fail-closed non-executability until the region has a land-adjacent status transition. The exact current district line is not independently evidenced for `1444`. |

Primary, institutional, and academic evidence consulted:

- Natural Earth, *Admin 1 - States, Provinces*, version `5.1.1`:
  <https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-1-states-provinces/>
- Geoscience Australia, *Border Lengths - States and Territories*:
  <https://www.ga.gov.au/scientific-topics/national-location-information/dimensions/border-lengths>
- AIATSIS, *Map of Indigenous Australia*:
  <https://aiatsis.gov.au/explore/map-indigenous-australia>
- Papua New Guinea Ombudsman Commission, *Constitution of the Independent
  State of Papua New Guinea*, sections 4-5:
  <https://www.ombudsman.gov.pg/legislation/png-constitution/>
- Papua New Guinea Department of Finance, *Provincial and District Finance
  Office*:
  <https://www.finance.gov.pg/about-us-2/provincial-and-district-finance-office/>
- Republic of Nauru, *Who comprises Parliament?*:
  <https://www.nauru.gov.nr/parliament-of-naoero/about-parliament/who-comprises-parliament.aspx>
- United Nations Digital Library, Nauru district map `NMP/63/145`:
  <https://digitallibrary.un.org/record/3935468/files/T_1619-EN.pdf>
- U.S. Census Bureau, *Geography Program Glossary - American Samoa* and the
  `2020` Eastern District reference map:
  <https://www.census.gov/programs-surveys/geography/about/glossary.html> and
  <https://www2.census.gov/geo/maps/DC2020/GARM20/GARM2020_ST60_AS.pdf>
- U.S. National Park Service, *History and the Islands of Samoa*:
  <https://www.nps.gov/npsa/learn/historyculture/history-and-the-islands-of-samoa.htm>
- U.S. National Archives, *Records of the Government of American Samoa*:
  <https://www.archives.gov/research/guide-fed-records/groups/284.html>

## Exact negative-anachronism recommendation

Use `regional_status_boundary_matches_forbidden_modern_seam_ratio_lte`, a
fixed `75 km` corridor, and maximum ratio `0.20`. Pin the existing Natural Earth
Admin-1 `5.1.1` archive at SHA-256
`efc59726337323058f9446210adc96673179cd344e053666ee3d28cb58ba2b05`.
Extract each line as the non-empty shared polygon boundary for the exact ISO
Admin-1 pair; coastlines are thereby excluded.

Add exactly these records after reviewer approval:

| Assertion ID | Reference units | Length | Transitions | Research measurement |
| --- | --- | ---: | ---: | ---: |
| `region-053-negative-modern-western-australia-south-australia-seam` | `AU-WA` / `AU-SA` | `629.0899 km` | `16` | `1.0000` fail |
| `region-054-negative-modern-central-province-national-capital-district-seam` | `PG-CPM` / `PG-NCD` | `44.3040 km` | `7` | `0.0000` pass |
| `region-057-negative-modern-yaren-meneng-seam` | `NR-14` / `NR-11` | `1.9780 km` | `0` | non-executable fail; null measurement |
| `region-061-negative-modern-american-samoa-western-eastern-district-seam` | `AS-X05~` / `AS-X01~` | `5.3182 km` | `0` | non-executable fail; null measurement |

The measurements come from a fresh temporary worldwide assembly of all 22
current migrated packets. Candidate selection was fixed from modern legal
provenance and historical-source scope before measurement. It was not chosen to
maximize failures: the NCD control passes, and the two disconnected-island
regions remain explicitly non-executable.

For each boundary registry feature, use truthful modern validity, soft-evidence
classification, null historical sides, exactly two `reference_unit_ids`, and
the applicable `1444-11-11` start-date program. Add one reviewed
`negative_control` source and one checksum-pinned
`assets/<region>/negative-controls.geojson` derived file to each packet. Do not
change assignments, actors, facets, typed relationships, tolerance, or coverage
grade.

## Alternatives and tradeoffs

1. **Recommended: four Admin-1 seams under the existing fail-closed relation.**
   This supplies a line-valued internal control for every Oceania region,
   exposes the exact WA-SA leak, records a real NCD pass, and makes the
   disconnected-island limitation explicit.
2. **Use external Admin-0 seams.** Indonesia-PNG is outside the complete `054`
   regional assignment scope, while the other three regions have no shared
   Admin-0 land line. These controls would measure scope exclusion or empty
   geometry. Rejected.
3. **Treat `057` and `061` as passing because measured overlap is zero.** Both
   have zero executable land transitions, so zero is absence of a test rather
   than evidence. Rejected under the approved fail-closed contract.
4. **Use Palau state or independent Samoa district lines.** Those divisions may
   preserve older local political geography, creating more historical
   ambiguity than the selected Nauru and U.S. territorial administrative
   controls. Rejected for this first negative gate.
5. **Invent an island-to-island or maritime seam relation.** The canonical
   status model currently has land components and land adjacency, not a sourced
   maritime jurisdiction graph. A new relation would exceed this task and risk
   fabricating historical boundaries. Rejected.
6. **Raise the tolerance or waive non-executability.** Either would weaken the
   worldwide contract to accommodate the current reconstruction. Rejected.

## Expected QA impact

- Adding the four assertions removes the final four
  `MISSING_NEGATIVE_ANACHRONISM` findings.
- `053`, `057`, and `061` add spatial failures; `054` adds one passing result.
  The seam inventory becomes 19 controls: 16 failures and three passes (`021`,
  `029`, and `054`).
- `057` and `061` each add a deterministic
  `NON_EXECUTABLE_SEAM_ASSERTION` finding with `transition_count: 0`, an empty
  affected-component list, and null measurement.
- The 19-region independently georeferenced positive-border backlog is
  unchanged.
- No packet, schema or QA behavior, assignment, tolerance, coverage grade,
  visual acceptance, runtime artifact, signature, certification, publication,
  or deployment state changes during this research boundary.

## Reviewer decision requested

Approve or amend the following bundle before implementation:

1. extend the shared Natural Earth control helper to the pinned Admin-1 `5.1.1`
   archive and the four exact unit pairs above;
2. add exactly one modern seam assertion, source pin, boundary feature, and
   derived GeoJSON asset to each Oceania packet;
3. preserve the existing `75 km` / `0.20` contract and fail-closed zero-
   transition behavior, accepting the researched `053` failure, `054` pass,
   and `057`/`061` non-executable failures; and
4. leave all 19 missing positive borders and all certification/publication
   guards unchanged.

## Approved implementation outcome

George Le approved the four-part bundle above. Implementation extended the
shared Natural Earth helper to the pinned Admin-1 `5.1.1` archive, routed all
four Oceania generators through it, and added one source pin, boundary feature,
assertion, and checksum-pinned derived GeoJSON asset per packet. Tests enforce
the exact unit pairs, archive checksum, asset geometry, one-negative-per-region
inventory, and removal of retired generated-edge lineage.

A fresh provisional worldwide assembly reproduced the researched outcomes:
`053` failed at `1.0` with 16 transitions, `054` passed at `0.0` with seven,
and `057`/`061` failed non-executable with zero transitions and null
measurements. The worldwide inventory is now 19 negative controls, 16 failures,
and three passes. No region lacks a negative assertion; 19 regions still lack
an independently georeferenced positive border. No assignment, actor, facet,
relationship, tolerance, schema, runtime, signing, certification, publication,
or deployment state changed.
