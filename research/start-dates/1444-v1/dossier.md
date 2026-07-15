# M25 1444 research dossier

## Scope

This withdrawn audit candidate sketches a generalized 1444-11-11 political
fabric for the Low Countries, Burgundy, France, the Holy Roman Empire, and
Central Europe. It is not independently releasable: its geometry is manually
drawn, its location IDs are synthetic, and it lacks the pinned M23 fabric and
22,000-province aggregation required by the current contract.

## Research Questions

- Which late-medieval political units must replace modern administrative paint?
- Can the Burgundian composite state be represented without flattening its
  constituent duchies into a modern Belgian or French unit?
- Do the scoped provinces reproduce dated frontier constraints and contain the
  capitals used by the gazetteer?
- Have the modern Brussels-Capital Region and French Nord department outlines
  been measurably excluded from the reconstructed province fabric?

## Citations

- William R. Shepherd, *Historical Atlas*, France in 1453, public-domain scan,
  University of Texas/Perry-Castañeda collection via Wikimedia Commons.
- Gustav Droysen, *Allgemeiner historischer Handatlas*, Holy Roman Empire circa
  1400, public-domain scan via Wikimedia Commons.
- Lynn H. Nelson, *Europe in 1430*, public-domain map via Wikimedia Commons.
- Denis Jacquerye, *Burgundian Netherlands 1477*, CC BY-SA map whose acquisition
  legend dates Brabant (1430) and Luxembourg (1443), used backward from 1477 only
  for holdings explicitly dated before the start date.
- geoBoundaries 2022 BEL ADM1 (Eurostat source) and FRA ADM2 (IGN source), used
  only as forbidden modern reference outlines.

## Transformations and Conflicts

Historical map boundaries were visually approximated without published control
points or per-vertex provenance. The 1400, 1430, 1453, and 1477 maps bracket
1444 but do not establish the straight-line coordinates in this candidate.
Those frontiers are therefore soft evidence, not hard constraints. Political
unions and dependencies are stored as relationships rather than geometry.
Modern Brussels and Nord geometry is used only by negative tests.

## Exclusions

Ecclesiastical microstates, imperial free-city enclaves beyond Cologne, French
appanage microboundaries, internal seigneurial parcels, coastlines, rivers, and
all regions outside the five named scopes are excluded from this release.

## Uncertainty

The geometry is interpretive scaffolding. Border coordinates must not be read as
certified reconstruction constraints. Coverage is C or U. A future revision
must use real production H3 locations, accepted parent/child lineage, and the
complete 22,000-province aggregation before release can be reconsidered.
