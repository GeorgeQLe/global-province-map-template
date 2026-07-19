# Interactive demo

Static MapLibre product demo over the **full global Natural Earth modern
baseline build** (4,600+ modern-scaffold admin-1 provinces, PMTiles-first) with
the **M21 area/region/superregion hierarchy** and **M18 culture/religion paint**.
Historical packs remain internal research fixtures until an entire exact start
date passes global research and runtime certification.

## Live

- Scenario: `modern-baseline` only
- Global polygons stream as **PMTiles vector tiles** (`<scenario>.pmtiles`);
  no full-world GeoJSON ships with the demo. The inspector reads rendered
  vector features (`queryRenderedFeatures`) at any zoom.
- **M21 hierarchy:** nested area (0.6 px) < region (1.6 px) < superregion
  (2.8 px) border lines, region/superregion labels from precomputed label
  points, and a hierarchy paint mode (`area_color`).
- Adjacency overlay: precomputed centroid lines (`adjacency-lines.geojson`)
  from the global adjacency CSV (land + strait edges).
- **M18:** culture / religion atlas paint (curated hints; unassigned is gray)
- Inspector: owner / controller / cores / claims / culture / religion /
  area / region / superregion

## Regenerate

All generated data under `data/` (PMTiles, tilesets, legends, hierarchy
overlays, adjacency lines, `demo-manifest.json`) is produced by one command
from the processed global build:

```bash
uv run gpm build provinces          # Natural Earth ingest (requires raw zips)
uv run gpm build adjacency
uv run gpm build hierarchy          # M21 areas/regions/superregions
uv run gpm demo build \
  --location-input data/processed/locations.geojson \
  --membership-input data/processed/province_membership.csv \
  --aggregation-manifest data/processed/province_aggregation_manifest.json
```

`gpm demo build` finishes by running the landing-site validator. Options:

- `--tile-max-zoom 10` with tippecanoe installed for deeper zooms
  (`--no-tippecanoe` forces the pure-Python backend, default z0–7).
- `--no-validate` to skip validation (e.g. partial rebuilds).

M15–M20 historical files remain in their research/config locations and are not
copied into this public directory. A historical tab may return only with a
worldwide certification artifact accepted by both research and runtime gates;
regional artifacts never qualify.

## Preview

PMTiles requires HTTP **range requests**, which `python -m http.server` does
not support. From `landing/`, use a range-capable static server:

```bash
npx serve -l 4173 .
# or: uv run --with rangehttpserver python -m RangeHTTPServer 4173
# open http://127.0.0.1:4173/demo  (root-absolute /demo/* asset URLs)
```

(Vercel production hosting serves ranges natively.)
