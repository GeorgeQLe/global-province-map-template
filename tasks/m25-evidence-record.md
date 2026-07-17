# M25 1444-v2 Evidence Record

Date: 2026-07-16 (America/New_York). Generator: `gpm-m25-v2-generator`.

This record documents the research evidence behind
`research/start-dates/1444-v2/` (`official-1444-reconstruction-v2`), how each
claim was verified, and what remains excluded. It complements, and does not
replace, the pinned `source_manifest.json` inside the pass.

## Design

The 2026-07-15 evidence stop found that no single open source certifies "every
frontier" of five regions at 1444-11-11. This pass instead certifies, per
priority region, **one long-lived legal frontier segment** whose validity at
1444-11-11 is established by date-valid academic scholarship and independently
corroborated by a second provenance chain, with derived geometry digitized
from open river data between anchor towns named by the scholarship:

| Region | Frontier | Segment | Sides (realm level) |
|---|---|---|---|
| low-countries | Scheldt | Pecq → Ghent | Kingdom of France / Empire |
| burgundy | Saône | Chalon-sur-Saône → Mâcon | Kingdom of France / Empire |
| france | Rhône | Barbentane → Fourques | Kingdom of France / Empire (Provence) |
| hre | lower Eider | Tönning → Pahlen | Empire (Holstein) / Denmark (Schleswig) |
| central-europe | lower Morava | Rohatec → Dyje confluence | Bohemian Crown / Hungary |

All five frontiers were dynastically bridged in 1444 (Philip the Good, Adolf
VIII, Habsburg minorities); they are modeled as de jure realm boundaries, which
is exactly how the cited scholarship treats them. B-grade claims are scoped to
these segments, their corridors, and the tested capitals — never to whole
regions.

## Per-region evidence

### low-countries — the Scheldt (France/Empire)

- Pirenne, *Histoire de Belgique* II (1908), p. 171: the Burgundian dukes
  united "les fiefs français et les fiefs d'Empire que séparait l'Escaut";
  p. 245: Philip the Good's right-bank possessions lay "dans l'Empire".
  Verified by grep against the pinned Internet Archive OCR text
  (SHA-256 `546dd95f…`).
- Pirenne III, p. 101-102: the 1529 Peace of Cambrai broke "pour toujours le
  lien qui rattachait à la France, depuis cent ans, les régions de la rive
  gauche de l'Escaut" — the left-bank attachment therefore held through 1444.
  Verified against the pinned OCR text (`afdd26f2…`).
- Lot 1910 (Persée) enumerates imperial Flanders east of the river (Alost,
  Waas, Quatre-Métiers, Overschelde) — the reason the certified reach stops at
  Ghent and the Tournaisis is excluded at Pecq.
- Corroboration: Shepherd 1911 plate "Central Europe c. 1477" — the dashed
  "Boundary of the Empire" runs along the labeled "Scheldt R." (visually
  verified on the pinned scan `07007531…`).

### burgundy — the Saône (France/Empire)

- Dumasy-Rabineau 2021 (OpenEdition, quotes re-verified by fetch): the royal
  position that "la frontière entre royaume et comté se situait sur la
  rivière"; the mémoire of 16 October 1444 with frontier "figures"; Auxonne and
  Heuilley ducal but "sis en terre d'Empire". This source documents the 1444
  frontier dispute itself.
- Dauphant 2018/2012: the kingdom of the "quatre rivières"; witnesses attested
  bronze realm markers "dans le lit de la Saône" (1452 inquiry).
- Corroborations: Shepherd "France in 1453" (visually verified, `d16c30a5…`):
  kingdom line on the Saône, Franche-Comté outside; Droysen 1886 c. 1450 plate
  (`87e46704…`).
- The certified Chalon→Mâcon reach lies downstream of the reach contested in
  1444 (upstream of Pontailler); east-bank attribution passes from ducal
  trans-Saône lands (Empire soil) to Savoyard Bresse near Tournus.

### france — the Rhône (Languedoc/Provence)

- Dauphant 2020 (DOI 10.57086/sources.112, quote re-verified by fetch): the
  Four Rivers doctrine, 14th-15th centuries.
- Maigret 2002 (Persée): the Rhône "devient une limite d'états, de l'Ardèche à
  la Méditerranée, au cours du XIIIe siècle".
- Hébert 2000 (Persée): Provence "terre d'Empire" since 1032; suzerainty
  nominal under René of Anjou (union with France only 1481/1486).
- Corroboration: Shepherd "France in 1453" — Provence uncolored outside the
  kingdom under "THE EMPIRE"; Avignon and Orange east of the line.
- Segment Barbentane→Fourques avoids papal Avignon/Comtat (north) and the
  Camargue delta channels (south). Vallabrègues (French on the left bank) is a
  documented sub-cell anomaly.

### hre — the lower Eider (Empire/Denmark)

- Nordfriisk Instituut lexicon (quotes re-verified by fetch): Schleswig north
  of the river "als Lehen des dänischen Königs", Holstein south "ein Lehen des
  deutschen Kaisers"; "Die Eider blieb Grenze …".
- Aarhus danmarkshistorien module 3.4: Schleswig a Danish crown fief; Adolf
  VIII recognised duke of Schleswig since 1440 (personal union with Holstein).
- Corroborations: Shepherd 1477 plate (Schleswig under the Kingdom of Denmark,
  Empire boundary at the Eider); Droysen "Deutschland im XV. Jahrhundert"
  (`85f19756…`).
- Geometry from OpenHistoricalMap relation 2691969 (CC0, pinned capture
  `3a8373a0…`): its 1773-1864 southern Schleswig boundary follows the river on
  the Tönning→Pahlen reach (control residuals ≤ 1.5 km). The Rendsburg island
  (perennially disputed), the Levensau/landwehr eastern line, Dithmarschen west
  of the Gieselau, and the storm-flood-altered estuary are excluded.

### central-europe — the lower Morava (Bohemian Crown/Hungary)

- SAV, *Lexikon stredovekých miest na Slovensku* (2010), SKALICA entry —
  quotes verified directly on p. 424 of the pinned PDF (`265419c8…`): the 1217
  charter "in confinio regni nostri versus Boemiam" with a perambulation along
  the Morava; from the late 14th century two border crossings "na čiare Kátov –
  Hodonín a Skalica – Strážnica"; Hussite occupation of Skalica 1432-1435 and
  return to Hungarian royal hands.
- Mudrik 2016 (MUNI thesis, carrying Zemek 1972): the border ran along the
  Olšava to the Morava "a po jejím toku dolů k Šaštínu"; the Rohatec-Javorina
  land section; Holíč-Branč definitively Hungarian after 1331/1332 (hence
  `valid_from` 1332 for the certified reach).
- Corroboration: Shepherd 1477 plate — "March R." carries the Boundary of the
  Empire between the Margravate of Moravia and the Kingdom of Hungary. The
  plate's 1477 Hungarian subjection of Moravia is deliberately NOT modeled;
  in 1444 Moravia was a Bohemian Crown land under margrave Ladislaus
  Posthumous.
- 1444 context: Władysław III died at Varna on 1444-11-10, one day before the
  start date; the news was unknown and the de jure boundary unaffected.

## Negative controls

Real outline files at geoBoundaries commit `9469f09` (the v1 audit's pin),
replacing the withdrawn v1 API-envelope shortcut for three regions:

| Outline | File SHA-256 |
|---|---|
| BEL ADM1 (Brussels-Capital) | `7af87f5035779f0aefe5bf930288572979e490ab0441fd9b92942a519bea0974` (matches v1 pin) |
| FRA ADM2 (Nord) | `a14ed131c86c802e5d546c7cbeccbd4daebc94a66fea413f563935a53504f251` (matches v1 pin) |
| FRA ADM1 (Bourgogne-Franche-Comté) | `7dc61e5c7e4c81f5fa10d339e6a5bc8428f1346f43f4426d9d165d2e44fc3a7e` |
| DEU ADM1 (Schleswig-Holstein) | `511b3625ad4568d12a6bfcb1bdea4e877199e1923e502cb80224b8164128eb05` |
| CZE ADM0 (Czechia) | `562d073b86ea4c1368c45f853ba2aa61fb9e7cbd6f221c32ca975069cf861317` |

## Generator verification checklist

Every load-bearing claim was re-verified by the generator, not only by the
research agents that surfaced it:

- Dauphant 2020, Dumasy-Rabineau 2021, Nordfriisk "Eider": verbatim quotes
  re-fetched from the live pages.
- Pirenne II/III: quotes grepped from the pinned OCR texts.
- SAV Lexikon: quotes extracted from p. 424 of the pinned PDF.
- Shepherd 1453 and 1477 plates: downloaded, hashed, and visually inspected
  (kingdom line on Saône/Rhône/Scheldt; Empire boundary at Eider and March).
- Droysen plates: pinned; visual inspection by research agent, plate identity
  cross-checked via the maproom.org index.
- geoBoundaries files: downloaded at the pinned commit; BEL ADM1 and FRA ADM2
  hashes reproduce the v1 audit's pins exactly.
- OHM relation 2691969: geometry parsed and corridor-verified; CC0 dedication
  confirmed at openhistoricalmap.org/copyright.

## Rejected sources

- aourednik/historical-basemaps `world_1400/1500.geojson` (GPL-3.0): fails
  point-in-polygon tests in all five theaters (Avignon/Aix/Grenoble inside
  "France"; Gray/Bourg-en-Bresse inside "France"; HRE/Hungary line 15-25 km
  east of the Morava; Rendsburg area in "Kalmar Union"). Not used.
- OHM "Franche Comté de Bourgogne" relation 2812113: starts 1493 (Treaty of
  Senlis); usable as context only, not as 1444 geometry. Not used.
- Wikipedia's "one of the oldest extant boundaries" superlative for the Morava:
  its cited source (Tockner et al., *Rivers of Europe*) only makes the modern
  statement. Not cited.
- Euratlas GIS (1400): commercial license. Not used.
- Engel *The Realm of St Stephen*, Magocsi *Historical Atlas of Central
  Europe*: inaccessible for verification (403/paywall). Listed as leads only,
  not cited as evidence.

## License handling

- Public domain / CC0 artifacts (Pirenne scans, Shepherd/Droysen plates,
  Natural Earth, OHM) are pinned by SHA-256; geometry substrates are staged
  inside the pass where extraction requires them.
- CC BY-NC-SA (Dauphant 2020) and institutional-copyright texts (SAV PDF,
  Nordfriisk, lex.dk, danmarkshistorien) are cited with URL/access date and,
  where a stable file exists, an SHA-256 pin; their content is not
  redistributed in this repository.
- geoBoundaries files carry CC BY 4.0 / Etalab 2.0 attribution in the source
  manifest and are staged as negative-control inputs.
