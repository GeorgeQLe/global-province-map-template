# M19 PMTiles / Vector Tiles

M19 adds **web-scale vector tile packaging** for atlas and review consumers.
Province and ownership choropleth GeoJSON can be compiled into a single-file
**PMTiles** archive of **Mapbox Vector Tiles (MVT)** without requiring a tile
server.

## Why

- Full global GeoJSON choropleths are large for browsers
- Static hosting (GitHub Releases, object storage, Vercel) works best with
  range-requestable archives
- MapLibre already speaks vector tiles; PMTiles is the portable container
- Atlas packs already emit the paint properties tiles need (`owner_color`,
  `culture_color`, …)

## What shipped

| Surface | Change |
| --- | --- |
| `gpm export tiles` | GeoJSON → `.pmtiles` + `.tileset.json` |
| `gpm export tiles --atlas-dir` | Tile every scenario choropleth in an atlas pack |
| `gpm export atlas --tiles` | Optional integrated PMTiles generation |
| Pure-Python backend | No tippecanoe required (default CI path) |
| tippecanoe backend | Used automatically when the binary is on `PATH` |
| Schema | `schemas/tileset-manifest.schema.json` |
| Demo | Optional PMTiles vector source for sample ownership |

## Commands

```bash
# Single GeoJSON → tiles pack under exports/tiles/<stem>/
uv run gpm export tiles --input data/processed/provinces.geojson

# Explicit output path
uv run gpm export tiles \
  --input path/to/ownership_choropleth.geojson \
  --output path/to/ownership.pmtiles \
  --layer ownership \
  --min-zoom 0 --max-zoom 8

# Tile an existing atlas pack (scenarios/*/ownership.pmtiles + tiles/provinces.pmtiles)
uv run gpm export tiles --atlas-dir exports/atlas/modern-small

# Atlas export with tiles in one step
uv run gpm export atlas --scenario official-1444 --tiles --tile-max-zoom 8

# Force pure-Python even if tippecanoe is installed
uv run gpm export tiles --input sample.geojson --no-tippecanoe
```

## Backends

| Backend | When | Notes |
| --- | --- | --- |
| `native` | Always available | Pure Python MVT + PMTiles v3 writer (stdlib + Shapely) |
| `tippecanoe` | `tippecanoe` on `PATH` and not `--no-tippecanoe` | Better simplification / densest-drop for large global sets |

Native does **not** generalize or drop features at low zoom. For multi-megabyte
global province sets, install [Felt tippecanoe](https://github.com/felt/tippecanoe)
(v2.17+ writes PMTiles directly).

## Outputs

### Single tileset

```text
exports/tiles/<stem>/
  provinces.pmtiles      # PMTiles v3, gzip MVT
  provinces.tileset.json # GPM tileset manifest + MapLibre hints
```

### Inside an atlas pack (`--tiles` or `export tiles --atlas-dir`)

```text
scenarios/<id>/ownership.pmtiles
scenarios/<id>/ownership.tileset.json
tiles/provinces.pmtiles          # when base geometry is present
tiles/provinces.tileset.json
```

### Tileset manifest (core fields)

| Field | Purpose |
| --- | --- |
| `backend` | `native` or `tippecanoe` |
| `layer_name` | MVT source-layer id |
| `pmtiles` | Archive filename |
| `min_zoom` / `max_zoom` | Zoom range |
| `bounds` | WGS84 west/south/east/north |
| `maplibre.source` | `{ "type": "vector", "url": "pmtiles://…" }` |

## MapLibre consumption

```html
<script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js"></script>
<script src="https://unpkg.com/pmtiles@3.2.1/dist/pmtiles.js"></script>
```

```js
const protocol = new pmtiles.Protocol();
maplibregl.addProtocol("pmtiles", protocol.tile);

map.addSource("ownership", {
  type: "vector",
  url: "pmtiles:///path/or/https/url/to/ownership.pmtiles",
});
map.addLayer({
  id: "ownership-fill",
  type: "fill",
  source: "ownership",
  "source-layer": "ownership", // layer name from export
  paint: {
    "fill-color": ["coalesce", ["get", "owner_color"], "#b0b0b0"],
    "fill-opacity": 0.78,
  },
});
```

HTTP hosts must support **byte-range requests** (`Accept-Ranges: bytes`).

## Property whitelist

Tiles keep a bounded property set for paint and inspect:

`province_id`, `display_name`, `owner`, `controller`, `owner_color`,
`controller_color`, `culture`, `religion`, `culture_color`, `religion_color`,
`assignment_source`, `disputed`, `uncertain`, parents, area/population flags.

Nested objects are dropped; simple arrays become comma-joined strings.

## Defaults

| Flag | Default |
| --- | --- |
| `--min-zoom` / `--tile-min-zoom` | `0` |
| `--max-zoom` / `--tile-max-zoom` | `8` |
| `--layer` | `provinces` (atlas scenarios use `ownership`) |

Zoom 8 is a practical web overview for country/province choropleths. Raise
`--max-zoom` for closer inspection of dense regions.

## Dual faces

| Face | Tiles |
| --- | --- |
| Game pack (`gpm export pack`) | No (engines want tables + GeoJSON) |
| Atlas pack (`gpm export atlas --tiles`) | Yes (optional) |
| Standalone (`gpm export tiles`) | Yes |

## Honesty bar

- PMTiles packaging does **not** improve historical accuracy
- Native backend preserves source vertices (no cartographic simplification)
- Demo sample remains a small Western Europe subset; tiles prove the delivery path
- FlatGeobuf / GeoParquet / TopoJSON remain optional future formats

## Related

- M10 atlas export face — `docs/m10-atlas.md`
- M18 culture/religion paint — `docs/m18-culture-religion.md`
- Review viewer (GeoJSON today) — `docs/m5-review-viewer.md`
- PMTiles spec — https://github.com/protomaps/PMTiles
