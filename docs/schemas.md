# Schemas

The canonical contracts live in `schemas/*.schema.json` and use JSON Schema
draft 2020-12.

- `source-manifest.schema.json` records source metadata, license posture,
  source-level checksums, per-artifact checksums, processing steps, and
  downstream files.
- `attribution-record.schema.json` records notices required by generated
  datasets and exports.
- `province-entity.schema.json` describes canonical province GeoJSON features.
- `region-entity.schema.json` describes region/state GeoJSON features.
- `adjacency-record.schema.json` describes land, sea, strait, river crossing,
  and port-to-sea adjacency rows.

Phase 1 includes a small dependency-free validator for source manifests in
`gpm.schemas`. Future milestones can replace or supplement it with a full JSON
Schema validator once the geospatial dependency stack is introduced.
