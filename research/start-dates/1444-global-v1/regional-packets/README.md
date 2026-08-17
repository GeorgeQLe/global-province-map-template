# M25C regional evidence packets

This directory accepts dated `m25c_regional_evidence` JSON packets for deterministic
replacement of provisional records. A packet must pin its `region_id`, `start_date`,
`as_of_date`, and `source_pins`. Packets are merged by region, date, and packet ID.

Grade A is reserved for packets whose four coverage rows declare no gaps or
exclusions and cite exact-date reviewed sources plus passing spatial assertions.
The provisional generator does not infer, widen, or auto-promote those claims.

`155-western-europe-2026-08-15.json` is the first accepted four-layer Grade-A
packet. It replaces 385 geographically scoped assignments, adds 20 executable
region assertions, and corrects 39 atomic locations that Natural Earth's
sovereign-country metadata leaked into Western Europe even though UN M49 lists
their Caribbean, South American, or Eastern African areas separately. Source
pins are SHA-256 digests of each complete canonical JSON source record plus its
exact locator; a syntactic placeholder digest does not qualify a packet.

`154-northern-europe-2026-08-15.json` is the second accepted packet. It
corrects Bouvet Island to South America `005`, replaces all 1,367 remaining
Northern Europe assignments, and models Denmark, Norway, and Sweden as
distinct constituent kingdoms of the sourced Kalmar Union. England, Scotland,
the Crown-linked Channel Islands and Isle of Man, the English and Gaelic Irish
polities, Lithuania, the Livonian Order, Novgorod, and Lübeck retain explicit
date-valid records. Its 23 assertions cover three political frontiers, six
capital locations across three layers, and modern Ireland/Åland negative
controls. Three packet assets are copied only after containment, regular-file,
unique-ID, checksum, temporal, and independent-corroboration checks pass.

`151-eastern-europe-2026-08-15.json` is the third accepted packet. It replaces
all 2,178 Eastern Europe assignments, adds 15 authoritative polity records and
five executable assertions, and binds ten complete source records to exact
locators. The exact date matters: `1444-11-11` is the day after the Battle of
Varna, so the Polish and Hungarian records explicitly describe the resulting
interregnum and succession state while Lithuania remains distinct. No M49
correction applies: under the pinned country-based UN partition, the complete
Russian Federation footprint belongs to subregion `151`, including its Asian
territory and antimeridian islands.

`039-southern-europe-2026-08-15.json` is the fourth accepted packet. It replaces
all 464 Southern Europe assignments, supplies 23 authoritative polity records,
18 canonical source pins, seven checked capital features, 29 executable
assertions, and two checksum-pinned frontier assets. Its exact `1444-11-11`
interpretation is the day after Varna and preserves distinct Iberian crowns,
Italian states, Balkan polities, Byzantium, and the Ottoman Sultanate. The
Portugal–Castile hard frontier is independently pinned and rendered. Under the
country-based M49 partition, Spain's and Portugal's complete territories remain
in `039`, so no geographic correction applies.

`145-western-asia-2026-08-15.json` is the fifth accepted packet. It replaces
all 768 Western Asia assignments, supplies eight authoritative polity records,
11 canonical source pins, seven checked capital features, 29 executable
assertions, and two checksum-pinned Ottoman-Qara Qoyunlu frontier assets. Its
exact `1444-11-11` interpretation is the day after Varna. It removes the modern
Northern Cyprus and Palestine actors, repairs one Muscovy leak in Azerbaijan,
and replaces every uncurated Arabian assignment with a bounded Rasulid-Yemen or
explicitly fragmented local-Arabian record. The country-based M49 sheet needs
no region correction.

`015-northern-africa-2026-08-16.json` is the sixth accepted packet. It replaces
all 643 Northern Africa assignments, supplies nine date-valid political records,
ten canonical source pins, six checked capital features, 25 executable
assertions, and two checksum-pinned Marinid-Zayyanid frontier assets. Its exact
date is `1444-11-11`. The sheet distinguishes the Marinid, Zayyanid, Hafsid, and
Mamluk states from the Kingdoms of Dongola and Alodia and from local Saharan,
Beja, and Darfur-Kordofan polities. Portugal's possession of Ceuta remains in
the already-promoted Southern Europe packet because the pinned M49 partition is
country-based and assigns Spain's complete modern footprint to region `039`.

`030-eastern-asia-2026-08-16.json` is the seventh accepted packet. It replaces
all 1,941 Eastern Asia assignments, supplies eight date-valid political records,
nine canonical source pins, five checked capital features, 21 executable
assertions, and a checksum-pinned Ming-Oirat frontier asset. Its exact date is
`1444-11-11`. The sheet distinguishes Ming China, Joseon under Sejong,
Muromachi Japan during the Ashikaga succession interval, Oirat and Northern
Yuan Mongol fabrics, Phagmodrupa-led Tibet, Jurchen polities, and Moghulistan.
It removes the anachronistic Hong Kong, Macao, and Muscovy scaffold actors; no
country-based M49 correction applies.

`034-southern-asia-2026-08-16.json` is the eighth accepted packet. It replaces
all 910 Southern Asia assignments, supplies 20 date-valid political records,
nine canonical source pins, thirteen checked capital features, 53 executable
assertions, and a checksum-pinned Bahmani–Vijayanagara frontier asset. Its
exact date is `1444-11-11`. The sheet keeps the Sayyid Delhi, Gujarat, Malwa,
Jaunpur, Bengal, Bahmani, Vijayanagara, Timurid, Qara Qoyunlu, Kashmir, Sindh,
Himalayan, Sri Lankan, and island fabrics distinct. It replaces the modern
Maldives and BIOT scaffold actors with the dated Maldives Sultanate and an
explicitly uninhabited Chagos record; no country-based M49 correction applies.

`035-south-eastern-asia-2026-08-16.json` is the ninth accepted packet. It
replaces all 1,759 South-Eastern Asia assignments, supplies 29 date-valid
political records, seven canonical source pins, fourteen checked capital
features, 57 executable assertions, and a checksum-pinned
Ayutthaya-Cambodia frontier asset. Its exact date is `1444-11-11`. The sheet
distinguishes the mainland courts from the maritime and archipelagic polities,
replaces 1,256 uncurated assignments and the colliding modern scaffold codes,
and records uninhabited South China Sea islets explicitly. Three Christmas and
Cocos (Keeling) Island locations are corrected to M49 region `053`.

`143-central-asia-2026-08-16.json` is the tenth and final accepted Asian
packet. It replaces all 310 Central Asia assignments, supplies eight
date-valid political records, seven canonical source pins, four checked urban
features, 17 executable assertions, and a checksum-pinned
Timurid–Moghulistan frontier asset. Its exact date is `1444-11-11`. The sheet
distinguishes Shah Rukh and Ulugh Beg's Timurid administrations from
Abu'l-Khayr's Uzbek ulus, Moghulistan under Esen Buqa II, the Nogai–Manghit
steppe, Syr Darya frontier polities, and local Turkmen fabrics. It removes the
modern Uzbek, Muscovite, and generic Chagatai scaffold actors. Two Russian
locations are corrected to M49 region `151`, and one Iranian location is
corrected to region `145`.

`021-northern-america-2026-08-16.json` is the eleventh accepted packet and
the first risk-first Americas promotion. It replaces all 3,986 Northern
America assignments, supplies 13 date-valid political records, eleven
canonical source pins, eight checked archaeological or political centers,
and 32 executable assertions. The exact-date sheet distinguishes late Norse
Greenland from Thule and ancestral Inuit communities and retains separate
subarctic, Northwest Coast, Columbia Plateau, California/Great Basin, Plains,
Puebloan, Hohokam, Mississippian, Iroquoian, Eastern Woodlands, and
uninhabited-island fabrics. These are deliberately coarse source-bounded
political groupings: later contact-era tribal maps and modern state borders
are not projected backward. Under the country-based M49 partition, Greenland,
Bermuda, Saint Pierre and Miquelon, and United States minor islands remain in
`021`, so no geographic correction applies.

`005-south-america-2026-08-16.json` is the twelfth accepted packet and the
largest remaining Africa/Americas promotion. It replaces all 2,200 South
America assignments, supplies 15 date-valid political or community records,
nine canonical source pins, eight checked archaeological or political centers,
and 32 executable assertions. The exact-date sheet keeps Pachakuti's early Inca
state distinct from unconquered Chimor, Aymara kingdoms, other Andean polities,
Muisca and Tairona chiefdoms, and deliberately coarse lowland and southern
community fabrics. It removes the generic modern scaffold and the anachronistic
Falklands actor, recording South Atlantic islands as uninhabited; later Inca
maxima, colonial borders, and contact-era tribal maps are not projected back to
`1444-11-11`. No additional country-based M49 correction applies.

`014-eastern-africa-2026-08-16.json` is the thirteenth accepted packet. It
replaces all 715 Eastern Africa assignments, supplies 13 date-valid political
or community records, nine canonical source pins, eight checked political,
port, archaeological, or settlement centers, and 32 executable assertions.
The exact-date sheet distinguishes Zar'a Ya'eqob's Solomonic Ethiopia, Adal,
Ajuran and southern Somali polities, Great Lakes kingdoms, northern and
Kilwa-linked Swahili cities, Zambezi polities, the Great Zimbabwe transition,
Malagasy communities, Comorian sultanates, and uninhabited remote islands. It
removes all modern-country and generic scaffold actors, draws no unsupported
hard frontier, and does not project later dynastic maxima or colonial borders
back to `1444-11-11`. The five Mayotte and Réunion locations geographically
corrected by region 155 remain represented through that already-promoted
packet; no additional M49 correction is required here.

`011-western-africa-2026-08-16.json` is the fourteenth accepted packet. It
replaces all 641 Western Africa assignments, supplies 15 date-valid political
or community records, eight canonical source pins, eight checked political or
urban centers, and 32 executable assertions. The exact-date sheet preserves
the declining Mali Empire, Tuareg control of Timbuktu and Gao, pre-imperial
Songhai, Jolof and Upper Guinea polities, Mossi kingdoms, emerging Akan states,
Dogon communities, Hausa and Yoruba city networks, Benin, and lower-Niger and
eastern-Sahel fields. It records Cape Verde and Saint Helena's Atlantic islands
as uninhabited and draws no unsupported hard local frontier. One Algerian
location is corrected to M49 region `015` and one Cameroonian location to
region `017`.

`013-central-america-2026-08-16.json` is the fifteenth accepted packet. It
replaces all 605 Central America assignments, supplies 25 date-valid state,
kingdom, chiefdom, or community records, eleven canonical source pins, twelve
checked political or archaeological centers, and 48 executable assertions.
The country-based M49 sheet includes Mexico as well as Belize, Guatemala, El
Salvador, Honduras, Nicaragua, Costa Rica, and Panama. The exact-date sheet
keeps the early Mexica-led Triple Alliance distinct from Tlaxcala and the
Purepecha state; preserves Gulf, southern Mexican, Yucatan-successor, Peten,
Belize, K'iche', other Maya, Pipil, and Lenca fabrics; and distinguishes the
isthmus's Pacific, Caribbean, Costa Rican, and Panamanian chiefdom systems. It
removes the generic Native/uncolonized and anachronistic Clipperton scaffold
actors, records remote eastern Pacific islands as uninhabited, draws no
unsupported hard local frontier, and requires no M49 correction.

`017-middle-africa-2026-08-16.json` is the sixteenth accepted packet. It
replaces all 527 Middle Africa assignments, supplies 13 date-valid kingdom,
regional-polity, or community records, eight canonical source pins, eight
checked political, settlement, or archaeological centers, and 32 executable
assertions. The exact-date sheet keeps Nzinga a Nkwu's Kongo kingdom and
Sayfawa Kanem-Bornu distinct from Sao, Tio-Anziku, Mbundu, Cameroon
Grassfields, equatorial forest, Ubangian, central Congo-basin, and Upemba
political fabrics. It does not project later Luba, Lunda, Loango, Ndongo, or
colonial territorial maxima backward to `1444-11-11`, records Sao Tome and
Principe as uninhabited before Portuguese settlement, draws no unsupported
hard local frontier, and requires no additional M49 correction.

`029-caribbean-2026-08-16.json` is the seventeenth accepted packet. It
replaces all 372 Caribbean assignments, supplies 11 date-valid chiefdom or
community records, eight canonical source pins, eight checked archaeological
sites, and 32 executable assertions. The exact-date sheet distinguishes
Lucayan communities in the Bahamas and Turks and Caicos; Cuban, Hispaniolan,
Boriken, and Jamaican Taino fabrics; Guanahatabey western Cuba; Virgin and
northern Leeward Island communities; Kalinago and related Lesser Antillean
communities; Trinidadian and southern-Caribbean fabrics; and small or
seasonally used islands. It removes every generic and modern-island scaffold
actor, draws no unsupported hard local frontier, and does not flatten the
archipelago's documented cultural diversity into a single pan-Caribbean
polity. The 24 Caribbean locations geographically corrected by region 155
remain represented through that already-promoted packet, so no additional M49
correction is required here.
