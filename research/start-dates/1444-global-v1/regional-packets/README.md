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
