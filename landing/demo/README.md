# Interactive demo

Static MapLibre product demo for the license-audited beta sample.

## Live

- Scenarios: `official-1444`, `official-1836`, `modern-baseline`
- Layers: owner choropleth, assignment source, adjacency graph, labels
- Inspector: owner / controller / cores / claims / assignment lineage
- Data: copied from `samples/beta-license-audited/` (Western Europe, 6 provinces)

## Reserved room

Disabled UI slots document the near-term roadmap without over-claiming:

| Slot | Milestone |
| --- | --- |
| Period geometry / boundary hints | M15 |
| Multi-era geometry + politics packs | M16 |
| Official 1936 era tab | M16+ |
| Culture & religion paint, PMTiles, curation diffs | M17+ |

## Preview

From `landing/`:

```bash
python -m http.server 4173
# open http://127.0.0.1:4173/demo  (root-absolute /demo/* asset URLs)
```
