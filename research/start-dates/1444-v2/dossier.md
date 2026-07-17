# M25 1444-v2 research dossier

## Scope

`official-1444-reconstruction-v2` reconstructs the 1444-11-11 political situation along five certified
frontier segments — Scheldt, Saône, Rhône, lower Eider, and lower Morava — over
the complete production M23 fabric (global-h3-v1-r2) and the full
22000-province `eu-like` aggregation. Regions outside the five
priority scopes carry no historical claim.

## Research Questions

- Where did the legal France/Empire, Empire/Denmark, and Bohemia/Hungary
  frontiers run on 1444-11-11, at fabric-representable scale?
- Can those frontiers be reconstructed from date-valid, independently
  corroborated evidence with traceable derived geometry?
- Do the Brussels and Nord negative-anachronism gates pass on the real build
  with real split lineage?

## Citations

See `source_manifest.json` for the full pinned table. Anchors: Dauphant (2020,
2018) on the Four Rivers doctrine; Dumasy-Rabineau (2021) on the 1444 Burgundy
frontier dispute and its lost maps; Pirenne, Histoire de Belgique II-III on the
Scheldt; Maigret (2002) and Hébert (2000) on the Rhône and Provence; the
Nordfriisk Instituut lexicon and Aarhus danmarkshistorien on the Eider; the SAV
Lexikon stredovekých miest (2010) and Mudrik/Zemek on the Morava. Shepherd
(1911) and Droysen (1886) plates corroborate independently. Verbatim quotes
were re-verified against the pinned artifacts during assembly (see
tasks/m25-evidence-record.md).

## Transformations and Conflicts

Frontier geometry is derived by clipping open river centerlines (Natural Earth
10m, public domain; OpenHistoricalMap CC0 for the Eider) between anchor towns
named by the cited scholarship; per-segment control-point residuals are
recorded in `derived/*.geojson` and each registry feature carries its
georeferencing block and a 6 km error budget. Golden tolerances were set from
measured full-build values and are capped at 25.0 km. Conflicts
and their resolutions are listed in `source_manifest.json`
`conflict_resolution_notes`.

## Exclusions

Papal Avignon/Comtat, the Calais Pale, Dithmarschen, the Rendsburg island and
Levensau line, the Camargue delta, the contested upper Saône reach above
Pontailler, imperial Flanders beyond the certified Scheldt reach, and all
regions outside the five priority scopes.

## Uncertainty

All five frontiers were dynastically bridged in 1444 and are modeled as de jure
realm boundaries. Enclaves below fabric granularity are documented rather than
painted. Assignment rows carry explicit uncertainty values; hierarchy is
C-grade scaffolding. The review manifest remains pending until an independent
human reviewer signs the rendered sheets.
