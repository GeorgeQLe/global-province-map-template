# Global Province Map Template

Reusable roadmap and tooling plan for generating strategy-game-style global province maps from open geodata.

The goal is to produce a reproducible world map hierarchy suitable for EU/Victoria/HOI-style games and globe-based products:

- locations: smallest addressable geographic units
- provinces: playable/owned land or sea units
- regions/states: province groupings for production, politics, or administration
- countries: political owners or modern reference entities
- superregions/continents: coarse map groupings

This repository starts as a planning and implementation template. It does not include proprietary game data, Paradox map files, or restricted geodata.

## Initial Data Strategy

The preferred core stack is:

- Natural Earth for land, coastlines, countries, rivers, lakes, and visual basemaps
- geoBoundaries for modern administrative boundary candidates
- GHSL and WorldPop for settlement and population weighting
- OpenHistoricalMap as an optional historical hint layer where coverage and feature licenses are acceptable

OpenStreetMap is useful but should be isolated behind an optional data path because OSM data is licensed under ODbL and may impose share-alike duties on adapted databases.

GADM should not be used in the default template because redistribution and commercial use are restricted without prior permission.

## Target Outputs

The implementation should eventually generate:

- `provinces.geojson` / `provinces.fgb`
- `regions.geojson`
- `locations.geojson`
- `adjacency.csv`
- `province_attributes.parquet`
- `source_manifest.json`
- `attribution.json`
- optional `pmtiles` or vector tiles for review UIs
- optional game-engine export packs

## Status

M1 source adapter implementation is in place for Natural Earth and
geoBoundaries. The CLI can dry-run planned artifacts, download raw source files
into ignored local storage, calculate checksums, and write source manifests.
See [ROADMAP.md](ROADMAP.md) for the implementation plan and
[docs/phase-1-scaffold.md](docs/phase-1-scaffold.md) for how the current
package, configs, schemas, and tests map to that roadmap.

Quick verification:

```bash
uv run --extra dev pytest
uv run gpm sources download
uv run gpm sources manifest
```

Optional real source download:

```bash
uv run gpm sources download --execute
uv run gpm sources manifest --from-raw
```
