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
- `topology-qa-report.schema.json` describes CI-gating topology reports,
  including input paths, configured thresholds, pass/fail status, analysis
  completeness, summary counts, and deterministic findings.
- `scenario-definition.schema.json` describes curated historical/baseline
  ownership overlay definitions (country/region rules and province overrides),
  including optional `quality_tier`, `official_era`, `recommended_profile`, and
  `priority_theaters` for official era programs (M12+).
- `scenario-ownership-record.schema.json` describes resolved per-province
  owner/controller/cores/claims rows for a scenario.
- `release-manifest.schema.json` describes public release bundles (tag,
  vintage, quality tiers, scenario set, sample filters, file inventory).
- `atlas-manifest.schema.json` describes atlas / SaaS export packs (scenario
  set, choropleth/legend counts, file inventory).
- `scenario-politics-qa-report.schema.json` describes M11 politics QA reports
  (ownership coverage, tag/orphan checks, owner components, golden findings).

`gpm.schemas` includes small built-in validators for source manifests,
topology QA reports, scenario definitions, release manifests, atlas
manifests, and scenario politics QA reports. The JSON Schema files remain the
canonical machine-readable contracts.

## M4 Refined Province Fields

M4 processed features add `settlement_count`,
`population_estimation_method`, `refinement_parent_id`,
`refinement_strategy`, `refinement_part_index`, and
`refinement_part_count`. These fields are optional in the province schema so
the unchanged M2 candidate layer and the no-refinement processed draft remain
valid. Refined FeatureCollections declare
`gpm.id_scheme = "source-geometry-sha256-v1+m4-parent-geometry-sha256-v1"`
and include an M4 summary under `gpm.refinement`.
An invalid upstream source polygon is retained with
`refinement_strategy = "source-geometry-preserved"` and an explicit
`refinement_skipped_reason`; M4 never repairs it implicitly.

## M3 Province IDs

Province FeatureCollections declare
`gpm.id_scheme = "source-geometry-sha256-v1"`. IDs have the form
`ne_<slug>-<12-char-sha256>`. The digest includes the Natural Earth source
layer, country and region identity, and Shapely-normalized geometry WKB. It
does not include source feature order, display name, ring orientation, ring
start position, or multipart order. Builds fail if two features resolve to the
same ID.

## M3 Land Adjacency CSV

Land adjacency is represented by one canonical undirected row. The endpoint
IDs are lexicographically ordered, `adjacency_type` is `land`, `bidirectional`
is `true`, and `crossing_type` is `shared_border`. `shared_border_km` is the
combined great-circle length of all shared line components. `source_lineage`
is stored as a JSON-encoded string array inside the CSV cell. Corner-only and
sub-threshold contacts are omitted.

## M6 Sea Zones and Marine Adjacency

Sea-zone FeatureCollections use `kind = "sea"` province features with
`sea_class` of `coastal` or `ocean`, optional `parent_land_province_id`, and
`gpm.id_scheme = "sea-geometry-sha256-v1"`. Coastal land provinces may have
`coastal = true` after `gpm build seas`.

When sea zones are present, adjacency CSV rows also include:

- `adjacency_type = sea`, `crossing_type = shared_border` for sea-to-sea borders
- `adjacency_type = port_to_sea`, `crossing_type = port` for land↔coastal sea
- `adjacency_type = strait`, `crossing_type = strait` for coastal land pairs
  within the profile strait distance that do not share a land border

See [m6-seas.md](m6-seas.md) for strategy presets and generation details.

## M7 Export Packs

`gpm export pack` writes profile-specific packs under `exports/<profile-id>/`
with GeoJSON, definition tables, localization stubs, terrain/population tables,
adjacency, attribution, and a `pack_manifest.json`. `gpm export geojson` writes
only the GeoJSON subset. Regions are derived by grouping land provinces on
`parent_region_id`; `region_type` comes from the profile `[export]` table
(`region`, `state`, or `strategic_region`). Attribution files follow
`attribution-record.schema.json`. See [m7-export.md](m7-export.md).

## M8 Scenario Ownership Overlays

Historical politics are curated tables, not alternate geometry.
`gpm scenario build` projects modern `parent_country_id` as a baseline owner,
then applies scenario `country_rules`, `region_rules`, and `province_overrides`
in that order. Outputs live under `data/processed/scenarios/<id>/`. Export packs
may embed scenarios via `--scenario`. See [m8-scenarios.md](m8-scenarios.md).

## M9 Release Manifests

`gpm release alpha` writes `release_manifest.json` describing a public alpha
dataset bundle: release tag, data vintage, generator version, scenario set,
quality tiers (`scaffold-baseline` / `curated-politics` / `period-geometry`),
sample filters, counts, and file inventory. The schema is
`release-manifest.schema.json`. Accuracy labels ship as `accuracy_label.json`
and `ACCURACY.md`. See [m9-alpha-release.md](m9-alpha-release.md).

## M15 Era Geometry Packs and Lineage

`gpm era-geometry apply` consumes pack definitions under
`configs/era_geometry/` (`era-geometry-pack.schema.json`) and writes a lineage
map (`era-geometry-lineage.schema.json`) plus period provinces and boundary
hints. Soft mode overlays frontier bands; hard mode replace/split/identity
operations rewrite priority-region polygons while preserving scaffold IDs in
lineage rows. See [m15-era-geometry.md](m15-era-geometry.md).

## M16 Multi-Era Packs and Migration Notes

`gpm multi-era build` consumes pack definitions under `configs/multi_era/`
(`multi-era-pack.schema.json`): at least two era slots, each pairing an optional
era-geometry pack with a scenario, plus a region quality matrix. Migration notes
for consumers are `multi-era-migration-notes.schema.json` (also rendered as
`MIGRATION.md`). Cross-era joins use `scaffold_province_id`. See
[m16-multi-era.md](m16-multi-era.md).

## M14 License Audit Reports

`gpm release beta` writes `license_audit.json` (and `LICENSE_AUDIT.md`) describing
catalog policy, feature lineage checks, public vs isolated/restricted sources,
attribution pack records, and findings. The schema is
`license-audit-report.schema.json`. Beta release manifests also set
`release_channel` to `beta`, `license_audit_passed`, and dual `faces` (game +
atlas). See [m14-beta-release.md](m14-beta-release.md).

## M10 Atlas / SaaS Packs

`gpm export atlas` writes `atlas_manifest.json` for web-oriented packs under
`exports/atlas/<profile-id>/`: scenario-joined choropleths, tag legends,
uncertainty layers, and CSV/JSON tables. The schema is
`atlas-manifest.schema.json`. See [m10-atlas.md](m10-atlas.md).

## M11 Scenario Politics QA

`gpm qa scenario` writes `politics_qa.json` for one scenario: ownership coverage,
unknown/orphan tags, UNK owners, owner-component sanity (via adjacency), and
optional golden checks. The schema is
`scenario-politics-qa-report.schema.json`. Review authoring writes
`province_overrides` into scenario definitions via the review server. See
[m11-scenario-qa.md](m11-scenario-qa.md).

## M3 Topology QA

Findings contain `code`, `severity`, sorted `affected_ids`, `message`, and a
`measurements` object. Findings are sorted deterministically. Error findings
set report status to `fail`; warnings alone retain `pass`. Coverage and graph
analysis are explicitly marked `complete` or `incomplete`, so invalid source or
province geometry cannot be mistaken for a successful partial check.
