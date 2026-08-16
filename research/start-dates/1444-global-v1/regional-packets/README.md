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
