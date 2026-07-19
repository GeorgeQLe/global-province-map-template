# M24 — Start-Date Research Framework

Status: **accepted; canonical research and certification contract**.

M24 defines the repeatable evidence, reconstruction, uncertainty, and spatial
QA workflow used by the independently releasable 1444, 1836, 1914, and 1936
passes. Regional grades describe research progress only; an official start-date
release is worldwide and indivisible.

## Required pass artifacts

Every pass ships these versioned artifacts together:

1. **Research dossier and source manifest** — scope, research questions,
   citations, access dates, versions, licenses, checksums, transformations, and
   conflict-resolution notes.
2. **Boundary feature collection** — dated lines/polygons used as constraints or
   evidence, linked to the historical-boundary registry.
3. **Polity/dependency gazetteer** — stable polity IDs, names/aliases, validity,
   capitals, and typed relationships including sovereignty, control,
   occupation, vassalage/dependency, personal unions, and claims.
4. **Location assignments and targeted splits** — assignments against a pinned
   M23 fabric revision, derived provinces, uncertainty, and any evidence-backed
   requests for a later fabric revision.
5. **Golden-border suite** — positive and negative spatial assertions, not only
   tag counts or boundary hints.
6. **Coverage matrix and changelog** — grades by region, era, and layer;
   exclusions; known gaps; geometry/politics/hierarchy changes; migrations.

## Machine-readable pass layout

Each independently releasable pass has a root `pass_manifest.json`. Its
artifact table pins a version, relative path, and SHA-256 digest for the dossier,
source manifest, boundary registry, gazetteer, assignments, golden-border
definitions, full-build geometry, coverage matrix, and changelog. Artifact
paths may not escape the pass root, use symlinks, or share a file across roles.
The assignments artifact transitively pins four additional relative sidecars by
SHA-256: the M23 fabric manifest, atomic locations, split lineage, and province
membership. These do not add top-level artifact roles.
The canonical JSON Schemas are:

- `start-date-pass-manifest.schema.json`
- `start-date-source-manifest.schema.json`
- `historical-boundary-registry.schema.json`
- `polity-gazetteer.schema.json`
- `start-date-location-assignments.schema.json`
- `spatial-golden-borders.schema.json`
- `start-date-coverage.schema.json`
- `start-date-changelog.schema.json`
- `start-date-qa-report.schema.json`

Run the fail-closed gate with:

```bash
gpm qa start-date --pass-dir research/start-dates/<pass-id>
```

The command checks schemas and checksums, pass/start-date identity, source and
polity references, hard-constraint source review, fabric and geometry revision
pins, location existence, accepted-split lineage, membership-derived province
IDs, membership-union geometry, declared full-build count, overlapping province
interiors, full-build spatial results, priority-region positive and negative tests,
the four mandatory coverage layers, A-grade evidence gates, and changelog
versioning. It writes `start_date_qa.json` in the pass root by default. A
non-passing spatial assertion is an error; merely declaring a test does not
certify a pass. `start_date_qa.json` contains the computed `assertion_results`.

Golden assertions are definitions and may not contain author-supplied status or
measurement fields. The executed relations are deliberately limited:

- `border_matches_boundary_hausdorff_lte` measures the coordinate-unit
  Hausdorff distance between the two subject polygons' shared edge and one
  dated boundary-registry geometry.
- `capital_within_subject` returns a boolean measurement for a gazetteer capital
  location point covered by its subject province polygon.
- `forbidden_outline_overlap_ratio_lte` measures intersection area divided by
  the forbidden dated/reference outline area, as a unitless ratio.

Unknown relations and mismatched units, subject counts, assertion types, or
expectations are rejected. The full-build GeoJSON is a required, versioned
artifact with its own manifest SHA-256 pin and geometry-revision identity.

## Dated historical-boundary registry

Each registry feature must include:

- stable feature ID and geometry revision;
- `valid_from` / `valid_to` (with precision when dates are approximate);
- boundary semantics and related polity IDs on each relevant side;
- source and license lineage through the source manifest;
- confidence and uncertainty notes;
- classification as a **hard constraint** or **soft evidence**;
- geographic scope and applicable start-date programs.

Hard classification requires evidence sufficient to constrain reconstruction.
Soft evidence can guide scoring, reviewer attention, or a debug overlay but
cannot establish a `period-geometry` claim.

Positive boundary constraints must be temporally valid at the pass start date.
A boundary referenced exclusively by a `negative_anachronism` assertion may
instead carry its truthful later validity (for example, a 2022 administrative
outline); `start_date_programs` records that it is applicable as a negative
control without falsely dating the modern feature to the historical start.

## Reconstruction workflow

1. Freeze scope, priority regions, layers, start date, and fabric revision.
2. Build the dossier, source manifest, gazetteer, and boundary registry entries.
3. Assign locations and aggregate provinces; record conflicts and uncertainty.
4. Model sovereignty, control, occupation, dependencies, personal unions,
   claims, and disputed status as distinct typed relationships.
5. Run topology, semantic, and mandatory spatial golden-border tests against
   the full build.
6. Request targeted location splits only where aggregation cannot represent a
   required border; accept them through a versioned M23 fabric revision.
7. Publish coverage masks, grades, changelog, migration notes, and release.

## Spatial QA contract

Every claimed priority region must have positive border/capital tests and
negative-anachronism tests. No known recent administrative outline may remain
where it contradicts the claimed date. Tests compare reconstructed geometry to
dated constraints and forbidden modern outlines using measurable spatial
relations and tolerances.

`period-geometry` requires the dated aggregation to be applied and tested in the
full build. A boundary-hint overlay, or a hard override that only matches sample
IDs, is insufficient.

The M25 1444 suite must include the Brussels/Nord regression: Brussels must not
inherit the outline of the modern Brussels-Capital Region, and Nord must not
survive as the outline of the modern French department in the reconstructed
Low Countries/Burgundy/France border story.

## Coverage and release grades

Coverage is published per `(start date, region, layer)` for at least geometry,
politics, hierarchy, and gazetteer relationships. Suggested grades are:

- **A — certified:** full-build spatial and semantic gates pass; reviewed sources;
- **B — reconstructed:** substantial fabric-backed dated reconstruction with
  reviewed, scoped, passing evidence and documented gaps;
- **C — scaffolded:** usable assignments but known modern/reference influence;
- **U — unassessed:** no historical claim.

Each start-date pass pins all artifact versions and may be published as a
canonical research/authoring artifact. An official game-runtime release
additionally requires worldwide A coverage with zero geometry-evidence gaps and
the M25B runtime-pack validation defined in `ROADMAP.md`. No regional grade is
an official-era claim.

An A grade is rejected unless its `source_ids` resolve to reviewed sources and
its `assertion_ids` resolve to passing executed full-build assertions for the
same region and layer. B requires the same reviewed/scoped/passing evidence bar
and explicit gaps; C rows must list known gaps. U rows must have no
source/assertion/evidence certification claim. Every region in pass scope must publish an explicit row
for geometry, politics, hierarchy, and gazetteer relationships, including `U`
rows where no historical claim is made.

## Program order

- M25A: validate all historical geometry/political classes in the hard-case casebook.
- M25B: compile canonical passes into the engine-neutral runtime contract.
- M25C: expand the five-region 1444 pilot into a globally certified pass.
- M26: global 1836 certification; reuse the
  runtime contract and publish scenario deltas or migration metadata.
- M27: global 1914 certification.
- M28: global 1936 certification.
