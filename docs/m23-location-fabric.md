# M23 — Historically Paintable Location Fabric

Status: **implemented; canonical M23 contract**.

M23 replaces the assumption that a modern administrative province is the
permanent parent of every playable cell. It establishes a shared fabric of
neutral atomic **locations** from which profile- and start-date-specific
provinces can be assembled.

Canonical pipeline:

```text
source layers → neutral atomic locations → era/profile provinces
              → scenario politics and hierarchy → exports
```

The earlier [density design note](m23-density-design-note.md) remains useful
game-design research. Its parent-admin-constrained implementation contract is
superseded by this document.

## Entity contract

### Location

A location is the smallest stable, addressable, paintable cell. Stable identity
belongs primarily here. A location records geometry, fabric revision, parent/
child lineage, terrain and population signals, source/license lineage, and
intersections with reference layers.

Locations may cross modern administrative boundaries. Modern membership is an
intersection table or other many-to-many relationship; it is not a required
single parent. Modern boundaries may be a hard constraint for a modern profile,
but their influence is configurable for historical profiles.

### Province and hierarchy

A province is a versioned aggregation of one or more locations. Its ID is
derived from ordered location membership plus profile, era/start date, and
geometry revision. Areas, regions, states, and superregions are likewise
versioned aggregations rather than permanent properties of a location.

Scenario politics attaches to the appropriate province aggregation and models
sovereignty, control, occupation, vassalage/dependency, personal unions, cores,
claims, and uncertainty separately.

## Fabric construction

1. Normalize land, coast, hydrography, terrain, settlement, population,
   historical-boundary, and modern-reference source layers.
2. Generate a deterministic neutral tessellation. Population, terrain, travel
   time, coastlines, settlements, strategic/iconic sites, and historical
   fragmentation influence cell density and shape.
3. Treat dated historical hard constraints as required edges where confidence
   and scope justify them. Treat soft evidence as scoring input, never as a
   certified border by itself.
4. Measure topology, compactness, travel time, settlement capture, and
   paintability without forcing cells to stay inside one modern admin parent.
5. Publish location IDs, adjacency, attributes, reference-layer intersections,
   and a fabric manifest.

The initial fabric is informed by the priority dates 1444, 1836, 1914, and 1936
without attempting to encode every dated province directly into the tessellation.
Detailed reconstruction and certification remain per-start-date work.

## Identity and revisions

- Equivalent geometry and lineage inputs reproduce the same location IDs.
- A fabric release has an explicit revision; downstream packs pin it.
- A split gives each child a new stable ID and records parent/child lineage.
- Unchanged locations retain IDs across revisions.
- Province and hierarchy IDs change when their membership, profile, era, or
  declared geometry revision changes.

## Aggregation and paintability feedback

Each start-date reconstruction assigns locations to provinces and political
relationships, then runs spatial golden-border tests. If no valid aggregation
can paint a required border, the failure may request a **targeted location
split**. That request must identify the failed test, proposed constraint,
sources, confidence, affected dates, and expected downstream migrations.

Accepted requests produce a new versioned fabric revision and lineage map.
They do not silently mutate existing start-date releases.

## M23 deliverables

- versioned neutral location layer and adjacency graph;
- stable location-ID and split-lineage contract;
- source/license manifest and modern-layer intersection table;
- configurable weighting and modern-boundary influence by profile;
- province aggregation manifest and deterministic derived-ID contract;
- paintability evaluation that can emit targeted split requests;
- migration fixture proving unchanged IDs and split lineage;
- review layers that show locations, aggregations, coverage, and modern source
  geometry separately.

## Commands and artifacts

The neutral fabric is the default province input:

```bash
uv run gpm build locations --fabric global-h3-v1
uv run gpm build provinces --profile eu-like \
  --start-date 1444-11-11
uv run gpm build adjacency
uv run gpm build hierarchy --profile eu-like
uv run gpm qa fabric
uv run gpm qa paintability --boundary-input /path/to/required-borders.geojson
```

Use `--location-input` to select another fabric. The pre-M23 builder is kept
only as `gpm build provinces --legacy-modern-admin`; its candidate, refinement,
population, and settlement flags are invalid on the neutral path.

Custom land/admin reference inputs must carry embedded `license_lineage` or
matching repeatable `--land-license`, `--admin0-license`, and
`--admin1-license` notices. A split migration must name
`--output-fabric-revision`; it is rejected if absent, unchanged from the source
revision, or supplied without `--split-request-input`.

The location build writes `locations.geojson`, `location_adjacency.csv`,
`location_admin_intersections.csv`, `location_lineage.json`, and
`location_fabric_manifest.json`. It also writes
`location_admin_pieces.geojson` for hard modern aggregation. Province
aggregation writes `provinces.geojson`, `province_membership.csv`, and
`province_aggregation_manifest.json`. Export packs keep these atomic and
membership artifacts separate from derived province geometry.

Optional population, settlement, terrain, and historical-signal GeoJSON must
carry embedded `license_lineage` or an explicit matching CLI license notice.
Missing signals are recorded and weights are renormalized over the inputs that
are available.

## Acceptance

M23 is complete only when the full build uses the neutral fabric, at least one
historical test fixture crosses a modern administrative boundary, IDs and
lineage are deterministic, and exports keep atomic locations separate from
derived provinces. It does not itself certify any historical start date.

Acceptance is automated in `tests/test_m23_locations.py`:

- fixed-timestamp builds and split migrations assert deterministic IDs,
  unchanged-ID preservation, actual-split-only lineage, and revision rules;
- custom reference/signal fixtures assert complete input and license lineage;
- fail-closed QA fixtures cover required sidecars, manifest-resolved land, and
  revision consistency;
- `tests/fixtures/m23/1444-cross-admin.json` proves a dated derived province
  contains locations on both sides of a modern boundary;
- review endpoints and export layout assertions keep atomic locations,
  membership rows, and derived provinces separate.

The canonical 30,000-target build produces 30,003 locations and 52,142
adjacency rows. Strict fabric QA reports zero errors. Natural Earth leaves 31
admin-0 and 40 admin-1 location shares incomplete; these are retained as the
stable warning codes `admin0_incomplete_reference_coverage` and
`admin1_incomplete_reference_coverage`.
