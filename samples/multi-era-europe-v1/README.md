# Multi-era pack: `europe-multi-era-v1`

Western + Central Europe multi-era geometry + politics v1

## Eras

| Era | Scenario | Geometry pack | Geometry | Politics |
| --- | --- | --- | --- | --- |
| 1444 | `official-1444` | `we-1444-v1 + ce-1444-v1` | `period-geometry` | `curated-politics` |
| 1836 | `official-1836` | `we-1836-v1 + ce-1836-v1` | `period-geometry` | `curated-politics` |
| 1936 | `official-1936` | `we-1936-v1 + ce-1936-v1` | `period-geometry` | `curated-politics` |

## Layout

- `eras/<era>/geometry/` — applied (or scaffold) province layer + lineage
- `eras/<era>/politics/` — resolved ownership tables for the era scenario
- `region_quality_matrix.json` — per-region quality tiers by era
- `MIGRATION.md` / `migration_notes.json` — consumer migration notes
- `multi_era_manifest.json` — build inventory

## Honest limits

- period-correct province geometry worldwide
- Paradox-grade completeness for any single era or region
- legal historical frontiers — soft hints are illustrative
