# M25C Asia/Europe assertion re-research

Status: **research complete; reviewer decision required**
Start date: `1444-11-11`
Research date: `2026-08-21`

## Scope and result

The affected set is exact:

- six missing negative-anachronism records: regions `030`, `034`, `035`,
  `039`, `143`, and `145`; and
- six surviving positive-border records requiring renewed review:
  `region-030-border-ming-oirat`,
  `region-034-border-bahmani-vijayanagara`,
  `region-035-border-ayutthaya-cambodia`,
  `region-039-border-portugal-castile`,
  `region-143-border-timurid-moghulistan`, and
  `region-145-border-ottoman-qara-qoyunlu`.

No Asia/Europe region is currently missing a positive-border record, but all
six surviving records are circular. Each reference geometry was created by
`fabric-shared-boundary-extraction-wgs84` from the same generated province
edge later compared to it, with a recorded residual error of `0.0 km`. The
sources establish contemporary actors and broad political geography; they do
not independently georeference those exact edges. This is the same provenance
defect for which the reviewer retired the Northern Africa Marinid-Zayyanid
gate.

The recommendation is to retire all six circular positive borders, add six
exact modern inland-seam controls, and make the compositional seam relation
fail closed when a region has zero executable status transitions. The latter
is necessary because Southern Europe currently collapses all 464 assignments
to identical all-`unknown` facets with null actors and no active status
relationships. An Italy-Slovenia control therefore measures `0.0` only because
there is nothing to test, not because the region has passed an anachronism
check.

## Evidence findings

| Region | Historical and modern-boundary finding | Positive-border disposition |
| --- | --- | --- |
| `030` Eastern Asia | Cambridge describes Ming rule as coexisting with Mongol and Oirat centers of power and the northern frontier as changing engagement, defense, allegiance, and conflict. The present China-Mongolia line is a surveyed modern state boundary recorded in a twentieth-century treaty and boundary atlas, not a `1444` Ming-Oirat line. | Retire `region-030-border-ming-oirat`. Re-add only after an independently digitized, dated frontier source replaces the generated two-cell edge. |
| `034` Southern Asia | Iranica and UNESCO support a fifteenth-century Bengal Sultanate and Muslim urban fabric on both sides of today's India-Bangladesh line. India's Ministry of External Affairs describes the present line through the 1974 Land Boundary Agreement and its 2011 settlement protocol. The modern seam cannot delimit Bengal in `1444`. | Retire `region-034-border-bahmani-vijayanagara`. The Bahmani and Vijayanagara states are well supported, but the current one-edge geometry is not independently georeferenced. |
| `035` South-eastern Asia | The packet assigns actors from Natural Earth `ADM0_A3` country membership before applying coordinate rules. Thailand's Ministry of Foreign Affairs says the Thailand-Myanmar boundary results from Anglo-Siamese instruments of 1868, 1883, and 1894 plus later instruments. UNESCO separately establishes contemporary Ayutthaya, Innwa, and Hanthawaddy centers, not the modern country line. | Retire `region-035-border-ayutthaya-cambodia`. Its current actor split begins directly from modern Thailand and Cambodia membership, so its extracted edge is especially circular. |
| `039` Southern Europe | The packet's reviewed sources establish multiple Iberian, Italian, Balkan, Byzantine, and Ottoman polities. Slovenia's government describes the Italy-Slovenia line as treaty-defined and records the 1946 boundary commission and 1947 Paris settlement. Yet the compositional migration leaves all 464 regional assignments with null actors, all-`unknown` facets, and zero status relationships, so no modern seam can currently be tested non-vacuously. | Retire `region-039-border-portugal-castile`. Portugal-Castile is a promising replacement target, but the present asset is still only a generated shared edge and needs independent historical georeferencing. |
| `143` Central Asia | Iranica places Timurid Transoxania under Shah Rukh and Ulugh Beg, Uzbeks on the northern Syr Darya by about `1445`, and independent Moghulistan around Issyk-Kul and the Ili. The UN records the exact Kazakhstan-Uzbekistan state-border demarcation in a treaty concluded in `2022`, with detailed modern maps and marker coordinates. | Retire `region-143-border-timurid-moghulistan`. The sources support the broad political distinction but not the extracted one-edge line. |
| `145` Western Asia | The packet sources establish Ottoman, Qara Qoyunlu, Mamluk, Rasulid, and local Arabian fabrics. The UN records that the definitive Saudi Arabia-Yemen boundary was fixed by the `2000` treaty, incorporating a `1934` section and newly delimiting another section. It is not a medieval Rasulid/local-Arabian frontier. | Retire `region-145-border-ottoman-qara-qoyunlu`. Re-add only from an independently georeferenced dated frontier source. |

Primary, institutional, and academic evidence consulted:

- Natural Earth, *Admin 0 - Countries*, the pinned modern de facto boundary
  source: <https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-0-countries/>
- United Nations Treaty Series, Mongolia-China border treaty and surveyed
  boundary protocol: <https://treaties.un.org/doc/publication/unts/volume%20984/volume-984-i-14375-english.pdf>
- David M. Robinson, Cambridge University Press, *Ming China and its Allies*:
  <https://www.cambridge.org/core/books/abs/ming-china-and-its-allies/allies-and-commensurability/18121EEE53D282570B82E1D5A50B92DE>
- Government of India, Ministry of External Affairs, India-Bangladesh Land
  Boundary Agreement materials:
  <https://www.mea.gov.in/uploads/publicationdocs/24529_lba_mea_booklet_final.pdf>
  and <https://www.mea.gov.in/Uploads/PublicationDocs/25214_faq_final.pdf>
- Encyclopaedia Iranica, *Bengal i. Persian Muslim elements in the history of
  Bengal*: <https://www.iranicaonline.org/articles/bengal/bengal-i-persian-muslim-elements-in-the-history-of-bengal/>
- UNESCO, *Historic Mosque City of Bagerhat*:
  <https://whc.unesco.org/en/list/321/>
- Thailand Ministry of Foreign Affairs, official boundary history:
  <https://treaties.mfa.go.th/th/content/%E0%B8%82%E0%B9%89%E0%B8%AD%E0%B8%A1%E0%B8%B9%E0%B8%A5%E0%B9%80%E0%B8%82%E0%B8%95%E0%B9%80%E0%B9%80%E0%B9%80%E0%B8%94%E0%B8%99>
- UNESCO, *Historic City of Ayutthaya* and *Mon cities: Bago, Hanthawaddy*:
  <https://en.unesco.org/silkroad/silk-road-themes/world-heritage-sites/historic-city-ayutthaya>
  and <https://whc.unesco.org/en/tentativelists/826/>
- Government of Slovenia, Italy-Slovenia state-boundary record and 1946-1947
  boundary history: <https://www.gov.si/teme/drzavna-meja/> and
  <https://www.gov.si/en/news/2021-08-02-memorandum-and-letter-of-the-regional-national-liberation-committee-for-the-slovenian-littoral-and-trieste-presented-to-the-inter-allied-boundary-commission/>
- Encyclopaedia Iranica, *Central Asia v. In the Mongol and Timurid Periods*:
  <https://www.iranicaonline.org/articles/central-asia-v/>
- United Nations Treaty Collection, Kazakhstan-Uzbekistan state-border
  demarcation treaty: <https://treaties.un.org/Pages/showDetails.aspx?objid=080000028065d9e3>
- United Nations, Saudi Arabia-Yemen International Border Treaty:
  <https://www.un.org/Depts/los/LEGISLATIONANDTREATIES/PDFFILES/TREATIES/YEM-SAU2000IBT.PDF>

## Exact negative-anachronism recommendation

Use the already approved schema-`0.3.0` relation
`regional_status_boundary_matches_forbidden_modern_seam_ratio_lte`, the pinned
Natural Earth Admin-0 `5.1.1` archive SHA-256
`ce1ac7036499a0edd641fbc093cd209a98f96a49d2eca8480aaacad35138a7f6`, a
fixed `75 km` corridor, and maximum ratio `0.20`.

Add exactly these records after reviewer approval:

| Assertion ID | Region subject | Forbidden inland seam | Maximum ratio | Research measurement |
| --- | --- | --- | ---: | ---: |
| `region-030-negative-modern-china-mongolia-seam` | all `030` components/status transitions | current China-Mongolia boundary | `0.20` | `0.8389` |
| `region-034-negative-modern-india-bangladesh-seam` | all `034` components/status transitions | current India-Bangladesh boundary | `0.20` | `0.7985` |
| `region-035-negative-modern-thailand-myanmar-seam` | all `035` components/status transitions | current Thailand-Myanmar boundary | `0.20` | `1.0000` |
| `region-039-negative-modern-italy-slovenia-seam` | all `039` components/status transitions | current Italy-Slovenia boundary | `0.20` | non-executable: zero transitions |
| `region-143-negative-modern-kazakhstan-uzbekistan-seam` | all `143` components/status transitions | current Kazakhstan-Uzbekistan boundary | `0.20` | `1.0000` |
| `region-145-negative-modern-saudi-arabia-yemen-seam` | all `145` components/status transitions | current Saudi Arabia-Yemen boundary | `0.20` | `1.0000` |

The measurements come from a fresh temporary worldwide assembly of the current
22 migrated packets. Candidate selection avoids boundaries that may preserve a
genuine long-duration historical interface, such as Portugal-Spain, and favors
modern lines whose treaty provenance or historical cross-line polity fabric is
independently documented.

Before adding the Southern Europe record, harden the relation so zero regional
status transitions are non-executable and fail rather than returning a passing
ratio of zero. Apply this generally: a seam-coincidence assertion cannot test a
region that has no executable seam. The existing `021` and `029` controls keep
their outcomes because they have 19 and two transitions respectively; this
change does not disturb any of the nine implemented controls.

## Alternatives and tradeoffs

1. **Recommended: six seam controls, zero-transition fail-closed behavior, and
   six positive-border retirements.** This exposes five measured modern-outline
   leaks and the Southern Europe status-collapse defect without weakening a
   gate. It increases the positive-border research backlog.
2. **Add all six controls without the zero-transition correction.** This would
   falsely clear Southern Europe's missing-negative warning with a vacuous
   `0.0` result. Rejected.
3. **Choose seams that currently pass.** Several external-region seams measure
   zero because the relation only sees components inside one region; using one
   would test scope exclusion rather than historical reconstruction. Rejected.
4. **Keep the six generated positive borders because their actors are
   historically plausible.** Actor coexistence does not georeference an exact
   line, and comparing an extracted fabric edge back to itself cannot be an
   independent spatial assertion. Rejected.
5. **Raise the `0.20` tolerance.** Five candidate measurements range from
   `0.7985` to `1.0`; tolerance inflation would conceal, not resolve, modern
   scaffold influence. Rejected.

## Expected QA impact

- Retiring the six circular borders increases the missing-positive inventory
  from 13 to 19 regions. No positive warning is cleared by this research.
- Adding the six negative controls removes these regions from the ten-region
  missing-negative inventory, leaving exactly four Oceania regions: `053`,
  `054`, `057`, and `061`.
- With zero-transition behavior corrected, all six new controls fail. Together
  with the seven retained Americas/Africa seam failures, 13 explicit
  compositional seam failures block certification.
- Region `039` additionally remains blocked on status reconstruction: its
  reviewed multi-polity source set is not represented by any executable
  compositional transition.
- No tolerance, assignment, coverage grade, review acceptance, runtime pack,
  signature, certification, or publication state should change during the
  remediation.

## Reviewer decision requested

Approve or amend the following bundle before implementation:

1. retire the six circular positive-border assertions and their assertion-only
   derived boundary assets;
2. add the six exact Natural Earth modern inland-seam controls above;
3. make zero-transition compositional seam assertions fail closed and verify
   that the existing nine controls retain their outcomes; and
4. keep all six positive-border requirements, plus Southern Europe's missing
   compositional status distinctions, fail-closed pending independent evidence.
