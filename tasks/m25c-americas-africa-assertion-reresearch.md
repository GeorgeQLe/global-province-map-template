# M25C Americas/Africa assertion re-research

Status: **research complete; approved remediation implemented**
Start date: `1444-11-11`
Research date: `2026-08-21`

## Scope and result

The affected set is exact:

- eight missing positive-border records: regions `005`, `011`, `013`, `014`,
  `017`, `018`, `021`, and `029`;
- nine missing negative-anachronism records: regions `005`, `011`, `013`,
  `014`, `015`, `017`, `018`, `021`, and `029`; and
- one surviving positive-border record requiring renewed review:
  `region-015-border-marinid-zayyanid`.

The recommendation is **not** to manufacture one assertion per warning from
the current status edges. Eight of the nine generators derive actor placement
directly from Natural Earth `ADM0_A3` membership, and region `015` derives it
from the preceding scaffold assignment plus coordinate rules. The
compositional migration correctly removed sovereign/owner/controller meaning
from community-presence rows, but it did not turn those country-derived edges
into dated historical frontiers.

The existing Northern Africa border must therefore be retired. The sources
establish contemporary Marinid and Zayyanid polities, but its boundary geometry
is a shared generated-fabric edge with zero source-georeferencing residual;
that is a self-comparison, not independent evidence for the exact frontier.

## Evidence findings

The reviewed source record supports the following conclusions.

| Region | Evidence finding | Positive-border disposition |
| --- | --- | --- |
| `005` South America | The Met chronology places Inca expansion from `1438`, Chimor's continued existence around `1450`, and the conquest of Chan Chan around `1470`. This proves coexistence, not an exact `1444-11-11` frontier. The packet's Inca and Chimor cells are not adjacent; intervening cells are assigned to a coarse Central Andean field. | No current executable border. Research target: a source-georeferenced Inca/Chimor or Inca/independent-Andean frontier, without forcing adjacency. |
| `011` Western Africa | The Met dates Tuareg control of Timbuktu and Gao to `1443–1468` and the Songhai imperial phase to `1465–1591`. The packet sources do not locate a day-precise Mali/Tuareg/Songhai frontier. | No current executable border. Do not convert Mali, Songhai, Tuareg, Dogon, or other coarse fields into hard lines. |
| `013` Central America | INAH supports the Triple Alliance from the 1428–1433 formation period and identifies Tlaxcala as outside it, but the available maps/text describe tributary places and later/contact-era extents rather than a georeferenceable line on `1444-11-11`. | Candidate only: a Mexica–Tlaxcala frontier after an independently digitized dated source is added. Do not use the current three-cell status seam. |
| `014` Eastern Africa | The sources establish Solomonic Ethiopia and Adal as contemporary rivals, but the historical geography is a changing frontier zone; the packet's Ethiopia/Adal split begins from modern country membership. | Candidate only: an Ethiopia–Adal frontier if a dated scholarly map can be pinned and georeferenced. Do not promote the current 22-edge seam. |
| `015` Northern Africa | The cited Maghrib works establish Marinid Morocco and Zayyanid Tlemcen, but do not independently establish the generated edge between `prv_bfc9324cbcd05ea3266f` and `prv_3b2184bdacf874b3e79c`. Separate reviewed evidence establishes Portuguese control of fortified Ceuta from 1415 and retention after 1443. | Delete `region-015-border-marinid-zayyanid`. Preferred replacement target: the fortified Portuguese-Ceuta/Marinid interface after a Ceuta-capable fabric split and sourced fortification/perimeter geometry. |
| `017` Middle Africa | UNESCO establishes Mbanza Kongo as a capital from the fourteenth century, while its broad territorial description is explicitly for the end of the fifteenth century. That later maximum cannot establish a `1444` Kongo edge. | No current executable border. Do not promote Kongo/community or Kongo/Mbundu status seams. |
| `018` Southern Africa | UNESCO dates Mapungubwe's political dispersal to after `1300` and describes later farming occupation and a shift toward Great Zimbabwe. The packet intentionally models mobile/community presence, not bounded sovereignty. | No political border is supported. Keep the positive-border warning fail-closed pending a framework decision on non-border positive geometry for mobile/community regions. |
| `021` Northern America | NPS describes Coosa as a network of villages and places its detailed political reconstruction in the sixteenth-century contact record. Other packet actors are village, mobile, and community fields; none has a source-fixed `1444` frontier. | No political border is supported. Do not harden culture-area interfaces or the Norse/Thule presence interface. |
| `029` Caribbean | NPS explicitly describes separate villages and communities connected through interaction networks, not a single island-wide polity. The region has no land adjacency between different packet actors; Hispaniola is deliberately one coarse actor field across the later Haiti/Dominican division. | No political border is supported. Do not retroject contact-era cacicazgo maps into `1444` or invent an inter-island land border. |

Primary or institutional evidence consulted:

- Metropolitan Museum of Art, *Central and Southern Andes, 1400–1600 A.D.*,
  timeline and key events:
  <https://www.metmuseum.org/toah/ht/08/sanc.html>
- Metropolitan Museum of Art, *Western and Central Sudan, 1400–1600 A.D.*,
  `1443–1468` and `1465–1591` chronology:
  <https://www.metmuseum.org/toah/ht/08/afu.html>
- Instituto Nacional de Antropologia e Historia, Triple Alliance formation and
  Tlaxcala/frontier materials:
  <https://revistas.inah.gob.mx/index.php/dimension/article/view/1095> and
  <https://www.inah.gob.mx/images/suplementos/20201612_tlacuache_964.pdf>
- UNESCO, *Mbanza Kongo, Vestiges of the Capital of the former Kingdom of
  Kongo*: <https://whc.unesco.org/en/list/1511/> and the nomination evaluation
  at <https://whc.unesco.org/document/159705>
- UNESCO, Mapungubwe trans-boundary history:
  <https://whc.unesco.org/en/tentativelists/5557>
- U.S. National Park Service, *Coosa Chiefdom — 1400–1600 CE*:
  <https://www.nps.gov/liri/learn/historyculture/coosa-chiefdom-1400-1600-ce.htm>
- U.S. National Park Service, *Caribbean Trade and Networks*:
  <https://www.nps.gov/articles/caribbean-trade-and-networks.htm>
- United Nations Second Administrative Level Boundaries, the recommended
  authoritative modern-control geometry source: <https://salb.un.org/en>

## Exact negative-anachronism recommendation

The existing `forbidden_outline_overlap_ratio_lte` relation is not adequate for
the migrated model. It accepts only one province subject and divides its
intersection by a modern polygon's area. A small province passes trivially,
while an historically larger actor can fail merely because it legitimately
contains the later outline. Neither result detects the defect at issue:
country-derived historical status boundaries coinciding with modern inland
seams.

Approve a narrowly scoped replacement relation before adding these records:

`regional_status_boundary_matches_forbidden_modern_seam_ratio_lte`

Its measurement is the fraction of a pinned modern **inland** administrative
seam lying within a predeclared fabric-scale corridor around any compositional
actor-transition boundary in that region. Coastlines are excluded. The subject
is the region's complete component/status set, including nullable-owner
components; it is not a single province or an owner-only dissolve. Fix the
corridor from the pinned fabric error budget before execution and fix the
maximum ratio at `0.20`. A result over `0.20` fails and requires reconstruction,
not tolerance inflation.

Add exactly these records after the relation and a reviewed, checksum-pinned
UN SALB or national-authority seam asset exist:

| Assertion ID | Region subject | Forbidden inland seam | Maximum ratio |
| --- | --- | --- | ---: |
| `region-005-negative-modern-peru-bolivia-seam` | all `005` components/status transitions | current Peru–Bolivia boundary | `0.20` |
| `region-011-negative-modern-mali-niger-seam` | all `011` components/status transitions | current Mali–Niger boundary | `0.20` |
| `region-013-negative-modern-mexico-guatemala-seam` | all `013` components/status transitions | current Mexico–Guatemala boundary | `0.20` |
| `region-014-negative-modern-ethiopia-somalia-seam` | all `014` components/status transitions | current Ethiopia–Somalia boundary | `0.20` |
| `region-015-negative-modern-morocco-algeria-seam` | all `015` components/status transitions | current Morocco–Algeria boundary | `0.20` |
| `region-017-negative-modern-angola-drc-seam` | all `017` components/status transitions | current Angola–DRC boundary | `0.20` |
| `region-018-negative-modern-botswana-south-africa-seam` | all `018` components/status transitions | current Botswana–South Africa boundary | `0.20` |
| `region-021-negative-modern-us-canada-seam` | all `021` components/status transitions | current contiguous US–Canada inland boundary | `0.20` |
| `region-029-negative-modern-haiti-dominican-seam` | all `029` components/status transitions | current Haiti–Dominican Republic boundary | `0.20` |

The Haiti/Dominican control is an especially useful known-pass case because the
packet deliberately assigns both sides of Hispaniola to the same coarse Taíno
field. Morocco/Algeria is the paired known-risk case because the surviving
Marinid/Zayyanid assertion currently promotes a generated seam in that area.

## Alternatives and tradeoffs

1. **Recommended: relation correction plus fail-closed positive research.**
   This tests the actual compositional regression and refuses unsupported hard
   frontiers. It requires a small schema/QA change and leaves eight positive
   warnings open, plus region `015` open after retiring its current gate.
2. **Keep polygon-overlap negatives.** This is cheaper and schema-compatible,
   but single-cell subjects make the checks largely vacuous after the
   compositional migration. Rejected.
3. **Promote generated status seams as positive borders.** This immediately
   clears warnings but circularly validates modern-country/coordinate
   classification as historical evidence. Rejected.
4. **Treat settlement/capital containment as the positive geometry gate where
   bounded political borders are not historically supportable.** This is
   defensible for regions `018`, `021`, and `029`, and potentially other coarse
   community fabrics, but changes the accepted M24 priority-region contract.
   Escalate as a separate reviewer decision; do not silently reinterpret
   `MISSING_POSITIVE_BORDER`.

## Expected QA impact

- Immediately after the approved remediation begins, deleting the invalid
  region `015` border changes the ordinary inventory from 12 to 13 missing
  positive-border regions until a genuine replacement or contract decision is
  implemented.
- Adding and passing the nine seam assertions removes these nine regions from
  the 19-region negative-anachronism warning, leaving ten Asia/Europe/Oceania
  regions for later research.
- No positive-border warning should be cleared by this research alone.
- Any seam assertion that fails is evidence of remaining modern-outline
  influence in the packet and must block Grade A rather than be waived.
- Certification, publication, runtime promotion, and independent review remain
  blocked throughout this decision gate.

## Reviewer decision requested

Approve or amend the following bundle before implementation:

1. retire `region-015-border-marinid-zayyanid` and its assertion-only derived
   geometry;
2. add the status-boundary/modern-inland-seam relation and the nine exact
   negative controls above;
3. keep all nine Americas/Africa positive-border gates fail-closed pending
   independently georeferenced boundary evidence; and
4. decide separately whether M24 may use a researched non-border positive
   geometry gate for mobile/community regions `018`, `021`, and `029`.

## Implementation outcome

The approved core recommendation was implemented without adopting item 4 or
altering any status assignment. All nine Natural Earth 5.1.1 seams are pinned
and executable. Regions `021` and `029` pass; regions `005`, `011`, `013`,
`014`, `015`, `017`, and `018` fail with deterministic component diagnostics.
The seven failures remain certification blockers. The invalid region `015`
border and its two obsolete assets are removed, and all nine positive-border
requirements remain fail-closed for later independently sourced research.
