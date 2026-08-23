# M25C worldwide spatial-remediation re-research

Status: **research complete; remediation decision required**
Start date: `1444-11-11`
Research date: `2026-08-22`

## Scope and result

This read-only gate re-examined the 19 modern-seam controls, the three
zero-transition results, and the 19 missing positive-border findings in the
fresh `1.0.0-assembled.1` worldwide candidate. It does not change an
assignment, assertion, source pin, boundary asset, schema, QA tolerance, or
candidate permission.

The baseline is reproduced exactly: 16 seam assertions fail, including three
null/non-executable measurements, while regions `021`, `029`, and `054` pass.
All regions except `151`, `154`, and `155` lack a positive border. A complete
render would therefore still leave the documented 54 non-review errors.

The evidence does **not** support manufacturing 19 territorial lines. The
recommended remediation has three distinct tracks:

1. repair modern-country dispatch in 13 continental packet status sheets, but
   only from independently located historical evidence;
2. correct the seam evaluator's observability contract so a covered modern
   seam lying wholly inside one eligible reviewed historical signature is an
   executable zero, while missing or all-unknown coverage still fails closed;
   and
3. replace the universal positive-border requirement with an explicit,
   reviewed applicability record. A region with no source-supported hard
   territorial line must supply a positive hard spatial anchor and a signed
   `not_applicable` border determination, not an invented border.

Only Southern Europe's Portugal-Castile frontier is ready for direct promotion.
Southern Asia's Raichur Doab is the strongest next digitization candidate, but
the September 1444 inscription establishes control/tribute and forts rather
than one closed frontier line. The other proposed lines need new dated
georeferencing before they may become hard constraints.

## Reproduced seam baseline

Every row uses the fixed `75 km` corridor and `0.20` maximum. `Transitions` is
the full regional compositional-transition count, not the number of matched
segments.

| Region | Exact assertion record | Measurement | Transitions | Result |
| --- | --- | ---: | ---: | --- |
| `005` | `region-005-negative-modern-peru-bolivia-seam` | `0.906572` | 26 | fail |
| `011` | `region-011-negative-modern-mali-niger-seam` | `0.704108` | 34 | fail |
| `013` | `region-013-negative-modern-mexico-guatemala-seam` | `0.950171` | 45 | fail |
| `014` | `region-014-negative-modern-ethiopia-somalia-seam` | `1.000000` | 19 | fail |
| `015` | `region-015-negative-modern-morocco-algeria-seam` | `1.000000` | 14 | fail |
| `017` | `region-017-negative-modern-angola-drc-seam` | `0.610298` | 22 | fail |
| `018` | `region-018-negative-modern-botswana-south-africa-seam` | `0.875523` | 10 | fail |
| `021` | `region-021-negative-modern-us-canada-seam` | `0.183933` | 19 | pass |
| `029` | `region-029-negative-modern-haiti-dominican-seam` | `0.000000` | 2 | pass |
| `030` | `region-030-negative-modern-china-mongolia-seam` | `0.838880` | 9 | fail |
| `034` | `region-034-negative-modern-india-bangladesh-seam` | `0.798541` | 32 | fail |
| `035` | `region-035-negative-modern-thailand-myanmar-seam` | `1.000000` | 39 | fail |
| `039` | `region-039-negative-modern-italy-slovenia-seam` | null | 0 | non-executable fail |
| `053` | `region-053-negative-modern-western-australia-south-australia-seam` | `1.000000` | 16 | fail |
| `054` | `region-054-negative-modern-central-province-national-capital-district-seam` | `0.000000` | 7 | pass |
| `057` | `region-057-negative-modern-yaren-meneng-seam` | null | 0 | non-executable fail |
| `061` | `region-061-negative-modern-american-samoa-western-eastern-district-seam` | null | 0 | non-executable fail |
| `143` | `region-143-negative-modern-kazakhstan-uzbekistan-seam` | `1.000000` | 15 | fail |
| `145` | `region-145-negative-modern-saudi-arabia-yemen-seam` | `1.000000` | 10 | fail |

The exact affected component IDs remain in each assertion result's
`affected_component_ids` array in the generated QA report. Implementation must
snapshot that pre-change set in its ship manifest and explain every changed
component; region-wide signature replacement is forbidden.

## The three zero-transition controls

### `039` Southern Europe

All 464 packet assignments currently have five `unknown` facets and no status
relationships. This is genuine missing compositional evidence, not proof that
the Italy-Slovenia seam is absent. Rebuild the assignments from the packet's
already reviewed dated actors and relationships, including Portugal, Castile,
the Italian states, Balkan polities, Byzantium, and the Ottomans. The seam must
then execute against non-unknown coverage and remain at or below `0.20`.

### `057` Micronesia

Nauru is one component assigned to one Nauru island community. The modern
Yaren-Meneng line crosses that component without creating a status transition.
The region has many different island actors, but disconnected islands cannot
produce land-adjacent transitions. Requiring an unrelated transition elsewhere
in Micronesia does not make the Nauru observation less vacuous.

### `061` Polynesia

The modern Western-Eastern district line likewise crosses a uniform Samoan
chiefly-community signature. Other Polynesian actors occupy disconnected
islands. The National Park Service describes governance through `aiga`,
`matai`, and village councils, while the modern GIS record notes that
administrative lines could change with political and traditional village
relations. These sources do not support inventing a `1444` district transition.

### Recommended executable-zero contract

Retain the same assertion IDs, relation name, `75 km` corridor, and `0.20`
tolerance. Change only observability:

- compute eligible, reviewed historical-component coverage along and on both
  sides of the reference seam;
- return an executable `0.0` when eligible non-unknown coverage spans the seam
  and no compositional transition enters the corridor;
- continue to return null/fail when coverage is absent, only unknown, invalid,
  or does not sample both sides; and
- add deterministic diagnostics for covered reference kilometres, left/right
  sampled component IDs, eligibility rejection reasons, and transition count.

This makes `057` and `061` executable passes without inventing status edges.
It does **not** make current `039` pass: its all-unknown sheet remains
ineligible until repaired.

Supporting evidence: [NPS Samoan governance](https://www.nps.gov/npsa/learn/historyculture/people.htm),
[American Samoa GIS village-boundary metadata](https://www.oc.nps.edu/CMSP/AS/tut_villages.html), and
[UN historic Nauru district map](https://digitallibrary.un.org/record/3935507/files/T_1589-EN.pdf).

## Region-by-region evidence disposition

| Region and packet | Seam treatment | Positive-border disposition |
| --- | --- | --- |
| `005` `005-south-america-2026-08-16.json` | Re-research only the Peru-Bolivia corridor as cross-border Aymara/Andean fabrics. Do not use modern country membership to choose actor or facet signatures. | **Not ready.** Chimor existed at the date, but the better-documented Inca conquest is later, around the 1470s. Archaeological expansion evidence can locate defended valleys, not an exact `1444-11-11` Inca-Chimor line. Keep the positive border absent pending a dated digitization. [Met chronology](https://82nd-and-fifth.metmuseum.org/toah/ht/08/sanc.html), [Yale eHRAF summary](https://ehrafarchaeology.yale.edu/traditions/se75/documents/024). |
| `011` `011-western-africa-2026-08-16.json` | Replace Mali-Niger dispatch with source-bounded Sahel, Songhai, Hausa, Tuareg, and Kanem-Bornu fabrics that may cross the modern seam. | **Not ready.** Available maps generally show later Songhai maxima or broad zones. No reviewed source fixes a two-sided `1444` line to the fabric resolution. |
| `013` `013-central-america-2026-08-16.json` | Reconstruct Maya and other community fabrics across Mexico-Guatemala; modern citizenship must not split identical evidence. | **Digitization candidate, not ready.** A Mexica-Purepecha fortified frontier is mappable, but published strategic-province evidence emphasizes mid-/late-fifteenth-century and contact-era records. It does not yet pin the line on `1444-11-11`. [ASU strategic-provinces study](https://www.public.asu.edu/~mesmith9/1-CompleteSet/MES-96-AIS-StrategicProvs.pdf), [UC Press extent study](https://www.degruyterbrill.com/document/doi/10.1525/9780520418660/html). |
| `014` `014-eastern-africa-2026-08-16.json` | Replace Ethiopia-Somalia country dispatch with independently located Ethiopian, Adal, Afar/Somali, and pastoral/frontier-zone evidence. | **Not ready.** Ethiopia-Adal was a changing frontier zone; the reviewed packet sources establish rival polities, not a georeferenceable exact line. |
| `015` `015-northern-africa-2026-08-16.json` | Remove Morocco-Algeria membership from Marinid/Zayyanid/Saharan status choice. | **Digitization candidate, not ready.** Reconsider Marinid-Zayyanid or Zayyanid-Hafsid only from a dated atlas plate plus independent textual corroboration. The retired generated Marinid-Zayyanid edge must not return. |
| `017` `017-middle-africa-2026-08-16.json` | Rebuild Angola-DRC corridor assignments from Kongo and neighboring community evidence without modern country dispatch. | **Not ready.** Scholarship describes early Kongo limits as blurred and later records as exaggerated; sixteenth-/seventeenth-century province maps cannot establish `1444`. [Kongo origins study](https://africankingdoms.co.uk/wp-content/uploads/2024/01/02b_Origins-of-Kongo-Oral-Tradition.pdf), [Cambridge eastern-border study](https://www.cambridge.org/core/services/aop-cambridge-core/content/view/7749E8D2DA72D1186387BE71D1BE785C/9781108474184c5_123-140.pdf/eastern_border_of_the_kongo_kingdom_on_relocating_the_hydronym_barbela.pdf). |
| `018` `018-southern-africa-2026-08-16.json` | Treat Botswana-South Africa as cross-border community fabric; do not align Shona/Tswana/Sotho evidence to it. | **Not ready.** UNESCO fixes Great Zimbabwe's site and occupation through about 1450, not a territorial perimeter or two-sided state border. [UNESCO Great Zimbabwe](https://whc.unesco.org/en/list/364), [site plan](https://whc.unesco.org/en/documents/9660). |
| `021` `021-northern-america-2026-08-16.json` | Already passes. Preserve its coarse cross-border Indigenous fabrics and exact control. | **Border not applicable.** The packet intentionally rejects later contact-era tribal maps and hard modern-style lines. Require a reviewed applicability record plus existing positive archaeological/political center anchors; do not fabricate a continental territorial border. |
| `029` `029-caribbean-2026-08-16.json` | Already passes. Preserve the island-wide status treatment. | **Not ready / likely non-applicable at this date.** Maps of five Taíno chiefdoms describe 1492 and are often presented as non-official boundaries. They cannot silently become exact 1444 lines. [UPenn 1492 map](https://dia.upenn.edu/es/maps/CNT0004/), [border-history caveat](https://storymaps.arcgis.com/stories/336555e9b4624fd189d1a8ba54d89003). |
| `030` `030-eastern-asia-2026-08-16.json` | Replace China-Mongolia membership with dated Ming garrisons/open-frontier and Mongol/Oirat fabrics. | **Not ready.** The Great Wall is independent physical geometry, but scholarship places the cartographic borderline concept and major continuous wall defenses later; `1368-1449` was substantially an open frontier. Do not use the full later Ming wall as a `1444` polity border. [Ming border cartography](https://escholarship.org/uc/item/56x161qb), [construction chronology](https://www.nature.com/articles/s40494-024-01198-1). |
| `034` `034-southern-asia-2026-08-16.json` | Extend Bengal and neighboring historical fabrics across the India-Bangladesh seam from dated evidence. | **Priority digitization candidate.** The ASI inscription study records September 1444 evidence and Bahmani control of Raichur forts after the 1443 campaign. Digitize forts and the Krishna/Tungabhadra constraints, but do not claim the whole doab edge as a settled frontier without a second dated source. [ASI inscriptions](https://ignca.gov.in/Asi_data/75161.pdf). |
| `035` `035-south-eastern-asia-2026-08-16.json` | Replace Thailand-Myanmar dispatch with mandala/court and local-community evidence crossing the modern seam. | **Not ready.** Southeast Asian territorial jurisdiction was fluid rather than fixed by permanent boundaries; a circa-1400 regional map is useful for actor placement, not a hard exact-date edge. [Mandala analysis](https://www.journals.uchicago.edu/doi/10.14318/hau3.3.033), [circa-1400 map](https://www.planningmalaysia.org/index.php/pmj/article/download/356/292/682). |
| `039` `039-southern-europe-2026-08-15.json` | Rebuild all 464 unknown/no-relationship assignments from the packet's reviewed actors, then rerun the Italy-Slovenia seam. | **Ready with scoped exception handling.** Promote Portugal-Castile from official Portuguese/Spanish linework, the 1297 Treaty of Alcañices, and a source-derived mask excluding Olivença and later-demarcated/changed segments. The Spanish defense cartography portal states the treaty line is practically the present line. [Treaty/cartography record](https://bibliotecavirtual.defensa.gob.es/BVMDefensa/frontera_hp/en/cms/elemento.do?id=ms%2Ffrontera_hp%2Fpaginas%2FLos_tratados.html), [Portuguese official vector service](https://www.dgterritorio.gov.pt/atividades/cartografia/cartografia-tematica/caop?language=pt). |
| `053` `053-australia-new-zealand-2026-08-16.json` | Remove the WA-SA state line from actor/facet dispatch and preserve Aboriginal country as non-cadastral evidence. | **Border not applicable.** AIATSIS says its group locations are general, not exact or fixed, and unsuitable for land claims. A hard 1444 border would contradict the source. Use a reviewed applicability record and positive settlement/site anchors. [AIATSIS map terms](https://aiatsis.gov.au/explore/map-indigenous-australia). |
| `054` `054-melanesia-2026-08-16.json` | Already passes. Preserve the Central-NCD control. | **Border not applicable.** PNG customary-land research recommends zones of uncertainty over Western cadastral lines. Use reviewed applicability plus positive archaeological/settlement anchors. [PNG boundary-uncertainty study](https://sear.unisq.edu.au/24283/). |
| `057` `057-micronesia-2026-08-16.json` | Apply covered executable-zero semantics; do not split Nauru to make the test run. | **Border not applicable.** One Nauru community occupies one island component and the modern districts are not a sourced 1444 territorial division. Retain positive Leluh/Nan Madol/settlement anchors and a reviewed applicability record. |
| `061` `061-polynesia-2026-08-16.json` | Apply covered executable-zero semantics; do not invent a Samoan district transition. | **Border not applicable.** Evidence supports village- and `matai`-based governance, not the exact modern Western-Eastern district line in 1444. Retain positive settlement/political-center anchors and a reviewed applicability record. [NPS people and governance](https://www.nps.gov/npsa/learn/historyculture/people.htm). |
| `143` `143-central-asia-2026-08-16.json` | Replace Kazakhstan-Uzbekistan membership with Timurid, Moghulistan, Uzbek, Nogai, and Syr Darya evidence. | **Digitization candidate, not ready.** The open-access Ming-diplomat study supplies a regional map and physical anchors, but it does not by itself establish one exact two-polity boundary on the start date. [Timurid regions and Moghulistan](https://knowledge.uchicago.edu/record/11274/files/Timurid-Regions-and-Moghulistan-through-the-Eyes-of-a-Ming-Diplomat.pdf). |
| `145` `145-western-asia-2026-08-15.json` | Replace Saudi-Yemen membership with Rasulid/local Arabian relationships spanning the modern seam. | **Digitization candidate, not ready.** A fifteenth-century Ottoman-Mamluk frontier map exists in scholarship, but much of the interface was a broad frontier involving Dulkadir and Ramadanid intermediaries; later demarcation maps cannot be projected backward. [frontier-map thesis](https://scholarworks.aub.edu.lb/bitstream/handle/10938/10218/t-6060.pdf?isAllowed=y&sequence=1), [Ottoman borderland cartography](https://www.tandfonline.com/doi/full/10.1080/03085694.2022.2130521). |

## Positive-border applicability contract

The current global QA requires both a positive border and a positive capital in
every priority region. That is appropriate only where the historical model and
evidence assert a hard two-sided territorial line. It is unsatisfiable without
fabrication for disconnected-island regions and for source-bounded community
fabrics whose authorities expressly reject exact fixed boundaries.

Add a schema-`0.3.0` regional `positive_border_applicability` record with:

- `region_id`, `start_date`, and `status` (`required` or `not_applicable`);
- non-empty reviewed `source_ids` and exact locators;
- a controlled reason (`no_land_adjacency`, `non_territorial_fabric`, or
  `evidence_supports_zone_not_line`);
- at least one passing positive hard spatial anchor assertion for every
  `not_applicable` region; and
- independent-review coverage and signature binding.

QA must continue to require a passing positive border for `required` regions.
It must reject an applicability record used merely because research is
incomplete, because a candidate border failed, or because digitization is
inconvenient. Initial `not_applicable` candidates are only `021`, `053`, `054`,
`057`, and `061`; `029` remains pending rather than automatically exempt.

## Exact recommended implementation sequence

1. Add covered executable-zero diagnostics and regression fixtures; prove
   `057` and `061` pass while all-unknown `039` still fails closed.
2. Rebuild `039` compositional records, digitize the scoped Portugal-Castile
   official/treaty asset, add the positive assertion, and verify the
   Italy-Slovenia control.
3. Add the reviewed positive-border applicability contract and five initial
   records (`021`, `053`, `054`, `057`, `061`) with existing positive anchors.
4. Digitize and independently review `034` Raichur evidence only if the second
   source establishes exact two-sided geometry; otherwise retain it as pending.
5. Work through the remaining modern seams corridor-by-corridor. For every
   changed component, record old/new facets, relationships, source IDs,
   geometry relation to the forbidden seam, and historical rationale.
6. Do not promote a positive border until its asset is independently derived,
   checksum-pinned, date-valid, licensed, two-sided, and passes a predeclared
   source-derived error budget.
7. Regenerate twice, compare complete trees, render, and rerun ordinary
   pending-review QA after each regional batch. Keep all candidate permissions
   false until the result has zero non-review errors.

## Expected QA impact

The contract correction plus the evidence currently ready can safely remove:

- two `NON_EXECUTABLE_SEAM_ASSERTION` and their two spatial failures (`057`,
  `061`), plus their two downstream uncertified-geometry findings, without
  assignment edits;
- the `039` non-executable/spatial failure and downstream uncertified-geometry
  finding after its status rebuild;
- one missing positive border (`039`); and
- five missing-positive findings through reviewed, source-backed
  non-applicability records, provided their positive anchors pass.

This does not make worldwide QA clean. At least 13 modern-seam failures and 13
downstream uncertified geometry rows remain until corridor-level status
research is implemented. At least 13 border dispositions remain pending
(`029` plus twelve continental candidates), fewer only if independently
georeferenced assets are accepted. No review-ready state should be emitted from
this research result.

## Alternatives and tradeoffs

1. **Recommended: evidence-first mixed treatment.** Fix proven status leakage,
   make zero-transition observability local to the controlled seam, and record
   genuine border non-applicability. This preserves fail-closed behavior and
   avoids fictional geometry, but requires schema/QA work and further regional
   digitization.
2. **Require 19 literal positive borders.** This keeps the current simple gate
   but cannot be satisfied honestly for the five initial non-applicable
   regions. Rejected.
3. **Treat every zero-transition seam as a pass.** This would incorrectly pass
   Southern Europe's all-unknown status sheet. Rejected; coverage and both-side
   observability are mandatory.
4. **Raise tolerances, move controls, or erase negative assertions.** This
   hides modern-scaffold leakage. Rejected.
5. **Promote generated status seams or lightly perturb them.** This is circular
   self-comparison rather than independent evidence. Rejected.
6. **Use later maximum-extent maps as exact 1444 borders.** This creates date
   anachronisms in precisely the gate intended to prevent them. Rejected.

## Reviewer decision requested

Approve or amend this bundle before implementation:

1. covered executable-zero semantics, with all-unknown and uncovered cases
   still null/fail;
2. full Southern Europe status reconstruction and a scoped official/treaty
   Portugal-Castile positive border;
3. a signed positive-border applicability contract and initial exemptions for
   `021`, `053`, `054`, `057`, and `061`;
4. `034` as the first conditional digitization packet, requiring a second dated
   spatial source; and
5. no other positive promotion or seam assignment edit until its exact
   corridor-level evidence packet is separately reviewed.
