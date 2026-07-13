# Era geometry sample: `ce-1444-v1`

Central Europe 1444 period-geometry pack applied to the WE+CE scaffold sample
(`samples/scaffold-we-ce/`).

## What changed

| Scaffold ID | Operation | Era ID(s) |
| --- | --- | --- |
| `sample_cz_bohemia` | split | `era_cz_prague` + `era_cz_bohemia_residual` |
| `sample_hu_pannon` | replace | `era_hu_pannon` |
| `sample_at_vienna` | identity | `sample_at_vienna` |
| `sample_pl_mazovia` | identity | `sample_pl_mazovia` |
| WE sample provinces | scaffold pass-through | unchanged |

Soft boundary hints cover Bohemian Crown, Ottoman–Hungarian, Habsburg–Hungarian,
Polish–Lithuanian approach, and Silesian fringe bands.

## Rebuild

```bash
uv run gpm era-geometry apply \
  --pack ce-1444-v1 \
  --province-input samples/scaffold-we-ce/provinces.geojson \
  --output-dir samples/era-geometry-ce-1444
```

## Honest limits

- Priority-region scoped (AUT / CZE / POL / HUN modern parents)
- Illustrative soft hints, not legal 1444 frontiers
- Hard overrides target sample province IDs
- Not Paradox-grade HRE / Bohemian Crown completeness
