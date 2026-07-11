# Sample: Western Europe 1444 era geometry (M15)

Priority-region **period-geometry** proof for `official-1444`.

| Artifact | Role |
| --- | --- |
| `provinces.geojson` | Era-aware provinces (hard overrides + identity maps) |
| `boundary_hints.geojson` | Soft historical frontier bands |
| `lineage.json` / `lineage.csv` | Scaffold ↔ era province ID map |
| `quality_scope.json` | What is period-true vs scaffold-backed |
| `adjacency.csv` | Land adjacency recomputed on era provinces |
| `era_geometry_manifest.json` | Apply summary |

## Pack

- Pack id: `we-1444-v1` (`configs/era_geometry/we-1444-v1.json`)
- Priority region: Western Europe (`FRA`, `BEL`, `NLD`, `LUX`, `DEU`)
- Modes: `boundary_hints` + `hard_overrides`
- Quality tier: `period-geometry` (region-scoped only)

## Rebuild

```bash
uv run gpm era-geometry apply \
  --pack we-1444-v1 \
  --province-input samples/beta-license-audited/sample/provinces.geojson \
  --output-dir samples/era-geometry-we-1444 \
  --recompute-adjacency \
  --profile modern-small
```

## Honest limits

- Hard overrides target **beta sample** `province_id`s; they skip on full
  Natural Earth builds (soft hints still apply).
- Not Paradox-grade HRE microborders or global period shapes.
- Illustrative curator frontiers — not a legal 1444 boundary product.
