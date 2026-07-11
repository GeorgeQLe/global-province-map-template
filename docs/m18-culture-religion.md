# M18 Culture / Religion Atlas Paint Layers

M18 extends the atlas / SaaS export face so products can paint **culture** and
**religion** the same way they paint **owner** today. Politics resolution is
unchanged: culture and religion already cascade through scenario rules (M8).
M18 is **paint and packaging** only.

## Why

- Official scenarios already assign culture/religion on country and region rules
- Ownership tables and choropleth features already carry the strings
- Atlas consumers only had `owner_color` / owner legends
- Demo reserved a culture/religion slot; review viewer inspector showed fields
  without paint modes

## What shipped

| Surface | Change |
| --- | --- |
| `gpm export atlas` | `culture_color` / `religion_color`, identity legends, optional dissolve |
| CLI | `--no-identity-paint`, `--no-identity-dissolve` |
| Review viewer | Color modes `culture` / `religion` with server-side colors |
| Demo | Culture/religion layer toggles + sibling legends |
| Samples | Beta atlas scenarios regenerated with identity paint |

## Commands

```bash
# Default: identity paint + dissolve on
uv run gpm export atlas --scenario official-1444 --scenario official-1836

# Skip identity dissolve only (smaller packs)
uv run gpm export atlas --no-identity-dissolve

# Exact pre-M18 ownership paint surface
uv run gpm export atlas --no-identity-paint
```

## Atlas pack layout (per scenario)

```text
scenarios/<id>/
  ownership_choropleth.geojson   # + culture_color, religion_color
  ownership.csv / .json          # + culture_color, religion_color
  legend.json                    # owner (unchanged role)
  culture_legend.json            # NEW
  religion_legend.json           # NEW
  cultures.csv / religions.csv   # NEW
  cultures.geojson               # NEW (if identity dissolve)
  religions.geojson              # NEW (if identity dissolve)
  scenario_manifest.json         # paint.modes + coverage counts
```

### Flag truth table

| Identity paint | Identity dissolve | Choropleth colors | Identity legends | Dissolve GeoJSON |
| --- | --- | --- | --- | --- |
| on (default) | on (default) | yes | yes | yes |
| on | off | yes | yes | no |
| off | ignored | no | no | no |

When paint is **off**, ownership CSV headers match the pre-M18 column set
(ending at `controller_color`).

## Colors

- Non-empty culture/religion id → same algorithm as `tag_fill_color` (`sha256` → HSL)
- Null / empty → unassigned gray `#8a8a8a` (`identity_fill_color`)
- Colors are **not** role-namespaced: string `french` always paints the same

Prefer MapLibre property-based fill for all pack sizes:

```js
map.setPaintProperty("fill", "fill-color",
  ["coalesce", ["get", "culture_color"], "#8a8a8a"]);
```

Full `match` expressions live on legends for small catalogs only.

## Identity legend shape

Sibling files use `entries[]` / `id` (not owner `tags[]` / `tag`):

| Key | Purpose |
| --- | --- |
| `paint_field` | `culture` or `religion` |
| `color_field` | `culture_color` or `religion_color` |
| `unassigned_color` | `#8a8a8a` |
| `unassigned_province_count` | Provinces without a value |
| `entries[].id` | Culture/religion string |
| `entries[].province_count` | Assigned province count |
| `styles.maplibre_fill_color_property` | Preferred fill expression |

Owner `legend.json` remains owner-centric for backward compatibility.

## Dual faces

| Face | Culture/religion data | Colors |
| --- | --- | --- |
| Game pack (`gpm export pack`) | Yes (CSV/JSON strings) | No |
| Atlas pack (`gpm export atlas`) | Yes | Yes |

## Demo

- Layers: **Culture** and **Religion** checkboxes (mutual exclusion)
- Paint priority: assignment → culture → religion → ownership → neutral
- Manifest keys: `culture_legend`, `religion_legend`, period variants
- PMTiles shipped as **M19** (see `docs/m19-pmtiles.md`)

Honesty: culture/religion are **curated scenario hints** (authorial strings;
synonyms like `shiite` / `shia` may differ by era). Unassigned provinces are gray.
Not Paradox-grade ethnography.

## Review viewer

```text
Color by → Culture | Religion
```

Server attaches `culture_color` / `religion_color` on ownership list, province
detail, and override write responses via `identity_fill_color`.

## Honesty bar

Roadmap quality target for culture/religion is **medium–high** where used by
games or atlas products, coarser outside priority regions. M18 ships the paint
pipeline; full global culture completion is curation work, not this milestone.

## Related

- M10 atlas export face — `docs/m10-atlas.md`
- M8 scenario resolve — culture/religion cascade
- M17 curation — diffs include culture/religion field changes
