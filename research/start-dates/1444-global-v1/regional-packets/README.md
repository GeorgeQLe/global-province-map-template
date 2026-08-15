# M25C regional evidence packets

This directory accepts dated `m25c_regional_evidence` JSON packets for deterministic
replacement of provisional records. A packet must pin its `region_id`, `start_date`,
`as_of_date`, and `source_pins`. Packets are merged by region, date, and packet ID.

Grade A is reserved for packets whose four coverage rows declare no gaps or
exclusions and cite exact-date reviewed sources plus passing spatial assertions.
The provisional generator does not infer, widen, or auto-promote those claims.
