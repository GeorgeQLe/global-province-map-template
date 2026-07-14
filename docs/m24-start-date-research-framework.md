# M24 — Start-Date Research Framework

Status: **planned; canonical research and certification contract**.

M24 defines the repeatable evidence, reconstruction, uncertainty, and spatial
QA workflow used by the independently releasable 1444, 1836, 1914, and 1936
passes. A start-date release makes only region-, era-, and layer-specific
coverage claims.

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
- **B — reconstructed:** substantial dated reconstruction with documented gaps;
- **C — scaffolded:** usable assignments but known modern/reference influence;
- **U — unassessed:** no historical claim.

Each start-date pass pins all artifact versions and can ship independently.
No regional grade may be promoted into an implicit global claim.

## Program order

- M25: 1444 — Low Countries, Burgundy, France, HRE, Central Europe first.
- M26: 1836 — post-Napoleonic Europe and priority colonial theaters.
- M27: 1914 — German, Austro-Hungarian, Russian, and Ottoman empires.
- M28: 1936 — interwar borders, mandates, colonies, and strategic groupings.
