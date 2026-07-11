# M5 Interactive Review Viewer

M5 adds a local MapLibre review UI for inspecting processed province geometry,
M3 topology QA findings, land adjacency, and M4 refinement attributes.

## Command

```bash
uv run gpm review
```

Defaults:

| Input | Default path |
| --- | --- |
| Provinces | `data/processed/provinces.geojson` |
| Adjacency | `data/processed/adjacency.csv` |
| Topology QA | `data/processed/topology_qa.json` |

The province GeoJSON is required. Adjacency and QA inputs are optional; if a
path is missing, the viewer starts without that panel/overlay data.

Useful flags:

```bash
uv run gpm review \
  --profile modern-small \
  --province-input data/processed/provinces.geojson \
  --adjacency-input data/processed/adjacency.csv \
  --qa-report data/processed/topology_qa.json \
  --host 127.0.0.1 \
  --port 8765 \
  --no-open
```

`--format json` prints a machine-readable startup summary before the server
blocks. Press Ctrl+C to stop.

## What the viewer shows

- Province polygons from the processed FeatureCollection
- Color modes: country, area, population, refinement strategy, QA status
- Click inspector for hierarchy, area/population, source/license lineage, and
  refinement fields
- Adjacency neighbors with shared-border length and jump-to-neighbor actions
- Topology QA findings list with zoom-to-affected-province behavior
- Optional dark basemap and QA outline overlay toggles
- Search by province id or display name

## Local server API

The CLI starts a stdlib HTTP server that serves:

| Path | Payload |
| --- | --- |
| `/` | MapLibre review UI |
| `/static/*` | Bundled viewer assets |
| `/api/meta` | Dataset counts, paths, and profile metadata |
| `/api/provinces.geojson` | Processed province FeatureCollection |
| `/api/adjacency.json` | Bidirectional adjacency index by province id |
| `/api/qa.json` | Topology QA report wrapper |
| `/api/province/{id}` | Per-province adjacency and linked findings |

No Node.js build step is required. MapLibre GL is loaded from a CDN when the
browser opens the local page.

## Recommended workflow

```bash
uv run gpm build provinces
uv run gpm build adjacency
uv run gpm qa topology
uv run gpm review
```

After an M4 refinement build, color by refinement strategy or population to
review split/merge outcomes and inspect child province lineage.

## Scenario layers (M11)

```bash
uv run gpm review --scenario demo-1444
```

With `--scenario` / `--scenario-path`, the viewer loads ownership, politics QA,
owner/controller/assignment color modes, and curator province-override
authoring. See [m11-scenario-qa.md](m11-scenario-qa.md).

## Out of scope for M5

- Static PNG/snapshot render QA (`gpm qa render` remains a placeholder)
- Geometry split/merge/rename override authoring (still future work)
- PMTiles / vector-tile packaging
- Dedicated sea-zone map layer in the viewer (M6 writes `sea_zones.geojson` and
  marine adjacency; load them separately until the review UI is extended)
