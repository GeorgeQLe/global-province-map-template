# M25C exact actor/component/line source attempt

Status: **research complete; no qualifying exact-date records; not implemented**

This packet audits eight newly checked discovery and geometry sources against
the frozen 107 actors, 206 rejected components, 180 rejected pairs, and 32
remaining finding routes. It replaces regional-source fan-out with exact
record bindings wherever the new source permits one. It does not confuse an
exact binding with an exact historical claim.

## New measurable evidence

The peer-reviewed Perreault digitization of Driver et al.'s 1953
ethnolinguistic map supplies 584 named polygons. The five upstream shapefile
parts are checksum-pinned without redistributing the 24 MB source. Full
equal-area intersections produce:

- 74 rejected components with one or more named source-feature intersections;
- 32 actors whose incident components all bind to named source features; and
- 53 pairs with complete named source-feature binding on both actor sides.

These are materially more exact actor-to-citation and component mappings than
the prior regional citation fan-out. They still do not qualify the records:
the data paper says the source observations span the sixteenth through
twentieth centuries, describes generalized and sometimes enlarged ranges, and
does not provide a 1444 snapshot. The paper reports CC BY-NC 2.5 for the data
while the Zenodo record reports CC BY 4.0, so the packet also preserves a
license conflict rather than choosing the more permissive label.

## Other exact locators

The audit records exact page, plate, or documentation locators for the
Schwartzberg South Asia plates, D-PLACE, AIATSIS, Native Land Digital,
Euratlas, SUNGEO, and World Historical Gazetteer. Each fails at least one
mandatory gate: target date, polygon/line geometry, actor identity, licensing,
or reproducible access. The copyrighted Schwartzberg plates are cited but not
stored, traced, or redistributed.

## Decision

No actor record establishes identity between a synthetic aggregate and every
source feature at `1444-11-11`. No component has a licensed exact-date polygon,
and no pair has an independently derived exact shared line. Consequently all
32 routes remain rejected, zero records are submitted for independent
acceptance, and no packet, assembled artifact, tolerance, grade, QA result,
permission, or Task 17 state changes.

## Reproduction

Download the five shapefile parts from Zenodo record `17289576` under a common
basename, install `pyshp` and `pyproj` in an isolated research environment, and
run:

```bash
PYTHONPATH=src python scripts/generate-m25c-exact-source-evidence.py \
  --driver-base /path/to/driver
.venv/bin/pytest -q tests/test_m25c_exact_source_evidence.py
```

The generator verifies the source-part hashes through the generated manifest;
the focused test pins the expected hashes and all frozen record counts.
