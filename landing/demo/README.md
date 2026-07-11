# Interactive demo

Static MapLibre product demo for the license-audited beta sample plus **M16
multi-era** geometry + politics packs for the Western Europe priority region,
with **M18 culture/religion paint** and **M19 PMTiles** vector delivery.

## Live

- Scenarios: `official-1444`, `official-1836`, `official-1936`, `modern-baseline`
- Layers: owner choropleth, **culture**, **religion**, assignment source,
  adjacency graph, labels
- **M16:** period geometry + historical boundary hints for **1444 / 1836 / 1936**
- **M18:** culture / religion atlas paint (curated hints; unassigned is gray)
- **M19:** optional **PMTiles vector source** (ownership layer; GeoJSON still
  powers inspector / period geometry)
- Multi-era pack: `we-multi-era-v1` (region quality matrix + migration notes)
- Inspector: owner / controller / cores / claims / culture / religion / lineage
- Data: `samples/beta-license-audited/` + `samples/multi-era-we-v1/`

## Shipped tooling (not only map layers)

| Capability | Milestone |
| --- | --- |
| Curation diffs, golden borders, external bundles | M17 (`gpm curation`) |
| Culture / religion atlas paint | M18 (`gpm export atlas`) |
| PMTiles / vector tiles | M19 (`gpm export tiles`, `gpm export atlas --tiles`) |

## Reserved room

| Slot | Milestone |
| --- | --- |
| Broader period geometry | M20+ |

## Regenerate PMTiles

```bash
for f in official-1444 official-1836 official-1936 modern-baseline; do
  uv run gpm export tiles \
    --input "landing/demo/data/${f}.geojson" \
    --output "landing/demo/data/${f}.pmtiles" \
    --layer ownership \
    --min-zoom 0 --max-zoom 6 \
    --no-tippecanoe
done
```

## Preview

From `landing/`:

```bash
python -m http.server 4173
# open http://127.0.0.1:4173/demo  (root-absolute /demo/* asset URLs)
```
