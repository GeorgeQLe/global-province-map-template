# M7 Export Profiles for Game Templates

M7 turns processed provinces, optional sea zones, and adjacency into
**profile-specific game template packs**. Packs are open-geodata derivatives
for engines and tools—not proprietary Paradox or other commercial map formats.

## Commands

```bash
uv run gpm build provinces
uv run gpm build seas
uv run gpm build adjacency
uv run gpm export pack
uv run gpm export geojson
```

### `gpm export pack`

Writes a full pack under `exports/<profile-id>/` (override with `--output-dir`):

| Path | Contents |
| --- | --- |
| `geojson/provinces.geojson` | Land province features |
| `geojson/regions.geojson` | Regions grouped from `parent_region_id` |
| `geojson/sea_zones.geojson` | Optional sea zones when present |
| `definitions/provinces.json` | Province attributes without geometry |
| `definitions/regions.json` | Region membership and hierarchy |
| `definitions/sea_zones.json` | Sea-zone definitions when seas are exported |
| `definitions/adjacency.csv` | Land / sea / port / strait adjacency |
| `localization/<lang>.json` | Machine-readable name stubs |
| `localization/<lang>.yml` | Game-mod style `l_<lang>:` stubs |
| `tables/terrain.csv` | Terrain class per province |
| `tables/population.csv` | Population and area per province |
| `attribution.json` | License notices for redistribution |
| `pack_manifest.json` | Pack metadata and file inventory |
| `README.md` | How to consume the pack |

Options:

- `--province-input` land province GeoJSON (default `data/processed/provinces.geojson`)
- `--sea-input` sea-zone GeoJSON (defaults to `sea_zones.geojson` beside provinces)
- `--adjacency-input` adjacency CSV (defaults to `adjacency.csv` beside provinces)
- `--output-dir` pack root (default `exports/<profile-id>`)
- `--profile` selects layout, region type, and include flags from `[export]`
- `--format text|json` summary format

Missing optional sea or adjacency files are skipped (empty adjacency table).
Missing province input fails with exit code 1.

### `gpm export geojson`

Same inputs and profile resolution, but only writes:

- `geojson/provinces.geojson`
- `geojson/regions.geojson`
- optional `geojson/sea_zones.geojson`
- `pack_manifest.json` (`pack_type = geojson`)
- `README.md`

Use this when a downstream tool only needs geometry layers.

## Region derivation

Land provinces are grouped by `parent_region_id`. When that field is missing:

1. fall back to `country:<parent_country_id>`
2. otherwise `orphan:<province_id>`

Each region feature includes:

- `region_id`, `display_name`, `region_type`
- `parent_country_id`, `parent_superregion_id` (null until superregions exist)
- sorted `province_ids` and `province_count`
- unioned multipolygon geometry when `include_geometry = true`
- combined `source_lineage` / `license_lineage`

`region_type` is profile-specific (`region`, `state`, or `strategic_region`).

## Localization stubs

Every province, sea zone, and region gets an entry:

| Entity | Key pattern | Example |
| --- | --- | --- |
| Province | `PROVINCE_<province_id>` | `PROVINCE_ne_xxx` |
| Sea zone | `SEA_<province_id>` | `SEA_sea_coastal-...` |
| Region | `REGION_<region_id>` | `REGION_US-CA` |

JSON is the machine contract. The YAML file uses a portable game-mod stub:

```yaml
l_english:
 PROVINCE_land_a:0 "Alpha"
 REGION_REG-1:0 "REG 1"
```

These are **stubs**: English `display_name` only. Full localization is a
downstream concern.

## Profile export settings

Optional `[export]` table. Unset keys use a layout preset. Layout defaults to
the profile id when a matching preset exists (`eu-like`, `victoria-like`,
`hoi-like`), otherwise `generic`.

| Layout | Default `region_type` | Typical use |
| --- | --- | --- |
| `generic` | `region` | modern-small, modern-detailed |
| `eu-like` | `region` | dense EU-style provinces |
| `victoria-like` | `state` | state-oriented Vicky-style packs |
| `hoi-like` | `strategic_region` | strategic-area oriented packs |

```toml
[export]
layout = "generic"
region_type = "region"
include_sea_zones = true
include_geometry = true
definition_format = "json"   # or "csv"
localization_language = "english"
```

`definition_format = "csv"` writes province/region/sea definition CSVs instead
of JSON (adjacency, terrain, and population remain CSV either way).

## Attribution

`attribution.json` matches `schemas/attribution-record.schema.json`. Records are
derived from unique `license_lineage` values on exported features, with
best-effort source titles/URLs for Natural Earth, geoBoundaries, WorldPop, and
GHSL. Keep the file with any redistributed pack.

## How to consume

1. Load `definitions/provinces.json` and `definitions/regions.json` as game tables.
2. Join localization keys into UI text.
3. Build movement graphs from `definitions/adjacency.csv`.
4. Use `geojson/` for map rendering or physics when needed.
5. Ship `attribution.json` with redistributed data.

Geometry and IDs remain independent of proprietary game maps. Scenario ownership
tables are available via M8 (`gpm scenario build` and
`gpm export pack --scenario <id>`); see [m8-scenarios.md](m8-scenarios.md).
Additional engine-specific formats remain future work.
