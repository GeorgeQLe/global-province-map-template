# M10 Atlas / SaaS Export Face

M10 is the second export face of the dual-face pipeline. Game packs (M7/M8)
target engines and mod tools; **atlas packs** target web maps, historical
explanation UIs, and SaaS-style consumption. **M18** extends the same face with
culture/religion paint (see `docs/m18-culture-religion.md`); pack `milestone`
is now `M18` while `schema_version` remains `0.1.0`.

Atlas packages join **scenario politics onto modern scaffold geometry**, emit
**tag legends with stable colors**, and ship **flat tables** alongside GeoJSON
choropleths. They do not rewrite province polygons.

## Commands

```bash
uv run gpm build provinces
uv run gpm scenario build --scenario modern-baseline   # optional pre-step
uv run gpm export atlas
uv run gpm export atlas --scenario modern-baseline --scenario demo-1444
uv run gpm export atlas --no-base-geometry --no-owner-dissolve
```

### `gpm export atlas`

Writes an atlas pack under `exports/atlas/<profile-id>/` (override with
`--output-dir`):

| Path | Contents |
| --- | --- |
| `geojson/provinces.geojson` | Optional base land geometry |
| `tables/provinces.csv` | Land province attributes for joins |
| `attribution.json` | License notices |
| `atlas_manifest.json` | Pack metadata and file inventory |
| `README.md` | How to consume the pack |
| `scenarios/<id>/ownership_choropleth.geojson` | Province polygons + ownership + colors |
| `scenarios/<id>/owners.geojson` | Owner-dissolved multipolygons |
| `scenarios/<id>/uncertainty.geojson` | Disputed / foreign-controlled / UNK |
| `scenarios/<id>/legend.json` | Tag catalog, colors, MapLibre helpers |
| `scenarios/<id>/tags.csv` | Flat legend table |
| `scenarios/<id>/ownership.csv` | Ownership rows with color columns |
| `scenarios/<id>/ownership.json` | Same ownership rows as JSON |
| `scenarios/<id>/countries.json` | Tags with display names and fills |
| `scenarios/<id>/scenario_manifest.json` | Per-scenario counts and paint config |

Options:

- `--province-input` land province GeoJSON (default `data/processed/provinces.geojson`)
- `--output-dir` pack root (default `exports/atlas/<profile-id>`)
- `--scenario` scenario id (repeatable; default `modern-baseline`)
- `--allow-unknown-overrides` ignore unmatched province overrides
- `--no-base-geometry` skip `geojson/provinces.geojson`
- `--no-owner-dissolve` skip `owners.geojson`
- `--format text|json` summary format
- `--profile` generation profile (must exist)

Missing province input fails with exit code 1. At least one scenario is
required.

## Choropleth join

Each land province feature in `ownership_choropleth.geojson` keeps geometry and
receives political properties from the same resolution pipeline as M8:

1. baseline (`owner = controller = parent_country_id`)
2. country rules
3. region rules
4. province overrides

Additional atlas fields on every feature:

| Field | Purpose |
| --- | --- |
| `owner_color` | Deterministic fill hex for the owner tag |
| `controller_color` | Deterministic fill hex for the controller tag |
| `uncertain` | `true` when disputed, owner≠controller, or owner is `UNK` |

## Tag colors and legends

Colors are **deterministic**: `sha256(tag) → HSL → #rrggbb`. The same tag
always paints the same color across rebuilds and scenarios. `UNK` uses a fixed
gray (`#8a8a8a`).

`legend.json` includes:

- sorted tag rows with display names and province counts
- `styles.maplibre_fill_color` — a ready `match` expression on `owner`
- `styles.maplibre_fill_color_property` — `["get", "owner_color"]` alternative
- `styles.css_custom_properties` — `--tag-<tag>: #hex` map for HTML legends

## Uncertainty layer

`uncertainty.geojson` is the subset of choropleth features where any of:

- `disputed == true`
- `owner != controller`
- `owner == UNK`

Suggested outline color is recorded as `#c0392b` in the scenario manifest and
legend (`disputed_outline_color`).

## Owner dissolve

When enabled (default), `owners.geojson` unions all provinces per owner into
one multipolygon feature with `province_count`, `province_ids`, and
`owner_color`. Useful for coarse country-level choropleths without client-side
dissolve.

## Relation to game packs

| Face | Command | Audience |
| --- | --- | --- |
| Game template | `gpm export pack` | Engines, mod tools, adjacency graphs |
| Atlas / SaaS | `gpm export atlas` | Web maps, explanation UIs, APIs |

Both faces share the same province geometry and scenario definitions. Game packs
embed scenario **tables**; atlas packs embed scenario **joined geometry +
legends**.

## Formats

M10 ships **GeoJSON**, **CSV**, and **JSON** only (stdlib + Shapely). Optional
tile/columnar formats called out in the roadmap (PMTiles, FlatGeobuf,
GeoParquet, TopoJSON) are listed in `atlas_manifest.json` under
`formats.optional_future` for downstream conversion—not generated in-tree yet.

## Schema

`schemas/atlas-manifest.schema.json` describes the atlas pack manifest.
`gpm.schemas.validate_atlas_manifest` checks core invariants.

## How to consume (MapLibre sketch)

```js
map.addSource("ownership", {
  type: "geojson",
  data: "/scenarios/demo-1444/ownership_choropleth.geojson",
});
map.addLayer({
  id: "owners-fill",
  type: "fill",
  source: "ownership",
  paint: {
    "fill-color": ["get", "owner_color"],
    "fill-opacity": 0.75,
  },
});
// Optional: load legend.json for a side panel of tags/colors.
```

## Relation to later milestones

| Milestone | Adds |
| --- | --- |
| M11 | Scenario politics QA + review authoring (**complete**; see m11-scenario-qa.md) |
| M12 | First official era `official-1836` (`curated-politics`) — complete |
| M13 | Second official era (`official-1444`) |
| M14 | License-audited beta (game + atlas faces) — complete |
| M15–M16 | Period geometry and multi-era packs |
| M17 | Curation workflow hardening |
