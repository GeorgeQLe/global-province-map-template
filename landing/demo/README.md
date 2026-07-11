# Interactive demo

Static MapLibre product demo for the license-audited beta sample plus **M16
multi-era** geometry + politics packs for the Western Europe priority region.

## Live

- Scenarios: `official-1444`, `official-1836`, `official-1936`, `modern-baseline`
- Layers: owner choropleth, assignment source, adjacency graph, labels
- **M16:** period geometry + historical boundary hints for **1444 / 1836 / 1936**
- Multi-era pack: `we-multi-era-v1` (region quality matrix + migration notes)
- Inspector: owner / controller / cores / claims / scaffold lineage fields
- Data: `samples/beta-license-audited/` + `samples/multi-era-we-v1/`

## Shipped tooling (not map layers)

| Capability | Milestone |
| --- | --- |
| Curation diffs, golden borders, external bundles | M17 (`gpm curation`) |

## Reserved room

| Slot | Milestone |
| --- | --- |
| Culture & religion paint | M18+ |
| PMTiles / vector tiles | M18+ |

## Preview

From `landing/`:

```bash
python -m http.server 4173
# open http://127.0.0.1:4173/demo  (root-absolute /demo/* asset URLs)
```
