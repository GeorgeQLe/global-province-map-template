# M6 Sea Zones, Ports, and Straits

M6 generates gameplay-first sea zones from open land geography, marks coastal
land provinces, and extends the adjacency graph with sea, port-to-sea, and
strait links.

Sea zones are **not** legal maritime boundaries (EEZ, IHO seas). They are
reproducible abstractions suitable for strategy-game movement and trade.

## Commands

```bash
uv run gpm build provinces
uv run gpm build seas
uv run gpm build adjacency
uv run gpm qa topology
uv run gpm review
```

### `gpm build seas`

Reads land provinces and optionally Natural Earth land polygons, then writes:

| Output | Default path | Contents |
| --- | --- | --- |
| Sea zones | `data/processed/sea_zones.geojson` | `kind=sea` features |
| Coastal flags | rewrites `provinces.geojson` unless `--no-update-provinces` | `coastal=true` for land that received a coastal sea zone |

Options:

- `--province-input` land province GeoJSON
- `--sea-output` sea-zone GeoJSON destination
- `--province-output` optional alternate path for coastal-flag updates
- `--no-update-provinces` leave land provinces unchanged
- `--raw-dir` for optional Natural Earth `ne_10m_land.zip`
- `--profile` selects `generation.sea_zone_strategy` and optional `[sea]` overrides

### `gpm build adjacency`

Still builds land shared-border edges. When `sea_zones.geojson` is present next
to the province input (or passed with `--sea-input`), it also emits:

| `adjacency_type` | `crossing_type` | Meaning |
| --- | --- | --- |
| `land` | `shared_border` | Shared land border above `qa.min_shared_border_km` |
| `sea` | `shared_border` | Shared sea-zone border above `sea.min_shared_border_km` |
| `port_to_sea` | `port` | Coastal land province ↔ its coastal sea zone |
| `strait` | `strait` | Non-adjacent coastal land provinces within strait distance |

Missing sea files leave the graph land-only (backward compatible with M3).

## Algorithm

1. Build a land mask from Natural Earth land when the raw zip is available;
   otherwise union the land province polygons.
2. Define a working domain from the **land-province extent** plus padding so
   fixture and regional builds stay cheap even if a global land mask exists.
3. Ocean = domain − land.
4. For each land province in deterministic ID order, claim coastal water as
   `buffer(province) − land`, intersected with ocean and not already claimed.
   Claims below `min_sea_area_sq_km` are dropped.
5. Partition remaining ocean with a fixed lon/lat grid of
   `ocean_cell_size_deg`.
6. Assign stable IDs: `sea_coastal-<parent-slug>-<hash>` or
   `sea_ocean-<col>-<row>-<hash>` from normalized geometry.
7. Mark land provinces with a coastal sea claim as `coastal=true`.
8. Adjacency adds port links for every coastal parent, sea-to-sea shared
   borders, and land-to-land straits when two coastal provinces are within
   `strait_max_distance_km`, do not share a land border, and do not touch.

## Profile strategies

`generation.sea_zone_strategy` selects a preset. Optional `[sea]` keys override
individual numbers:

| Strategy | Coastal buffer | Ocean cell | Strait max |
| --- | ---: | ---: | ---: |
| `simple-coastal-and-ocean` | 150 km | 45° | 40 km |
| `coast-aware` | 100 km | 30° | 30 km |
| `trade-coasts-and-oceans` | 120 km | 40° | 50 km |
| `strategic-seas-and-chokepoints` | 100 km | 25° | 80 km |
| `dense-coastal-seas-and-straits` | 75 km | 20° | 60 km |

```toml
[generation]
sea_zone_strategy = "simple-coastal-and-ocean"

[sea]
coastal_buffer_km = 120.0
ocean_cell_size_deg = 30.0
strait_max_distance_km = 45.0
min_sea_area_sq_km = 100.0
min_shared_border_km = 0.01
```

## Sea-zone feature fields

Beyond the shared province entity fields (`province_id`, `kind=sea`, area,
lineage, …):

- `sea_class`: `coastal` or `ocean`
- `parent_land_province_id`: set for coastal zones
- `sea_zone_strategy`: profile strategy used
- `ocean_grid_col` / `ocean_grid_row`: set for ocean cells

FeatureCollection metadata records strategy parameters under `gpm` with
`milestone = "M6"` and `id_scheme = "sea-geometry-sha256-v1"`.

## Out of scope for M6

- Legal maritime boundaries or named IHO seas
- River crossings (`river_crossing` adjacency remains unused)
- Lake provinces
- Viewer sea-layer polish beyond loading combined adjacency (M5 still focuses
  on land provinces; sea GeoJSON can be inspected as a separate layer later)
- Full global performance tuning for multi-million-vertex land masks
