# Migration notes: `we-multi-era-v1`

Scaffold province IDs are the stable cross-era join key. Era geometry packs may split or replace IDs within a version; use each pack's lineage.json to migrate. Politics are scenario overlays rebuilt per era.

## Lineage strategy

Each era-geometry pack emits its own lineage map (scaffold_province_id → era_province_id). Do not assume era IDs match across 1444/1836/1936. Cross-era analytics should join on scaffold_province_id.

## Eras in this pack

| Era | Scenario | Geometry pack | Geometry tier | Politics tier | Profile |
| --- | --- | --- | --- | --- | --- |
| 1444 | `official-1444` | `we-1444-v1` | `period-geometry` | `curated-politics` | `eu-like` |
| 1836 | `official-1836` | `we-1836-v1` | `period-geometry` | `curated-politics` | `victoria-like` |
| 1936 | `official-1936` | `we-1936-v1` | `period-geometry` | `curated-politics` | `hoi-like` |

## Cross-era joins

Recommended join key: `scaffold_province_id`.
- Do not assume era_province_id equality across different eras.
- A split in 1444 (e.g. Cologne) may not exist in 1836/1936 packs.
- Politics attach to the province layer used for that era build.

## Region quality matrix

### Western Europe (priority region)

| Era | Geometry | Politics |
| --- | --- | --- |
| 1444 | `period-geometry` | `curated-politics` |
| 1836 | `period-geometry` | `curated-politics` |
| 1936 | `period-geometry` | `curated-politics` |

### Europe elevated theaters (outside WE hard overrides)

| Era | Geometry | Politics |
| --- | --- | --- |
| 1444 | `scaffold-baseline` | `curated-politics` |
| 1836 | `scaffold-baseline` | `curated-politics` |
| 1936 | `scaffold-baseline` | `curated-politics` |

### Global major-power tags

| Era | Geometry | Politics |
| --- | --- | --- |
| 1444 | `scaffold-baseline` | `curated-politics` |
| 1836 | `scaffold-baseline` | `curated-politics` |
| 1936 | `scaffold-baseline` | `curated-politics` |

### Outside elevated theaters

| Era | Geometry | Politics |
| --- | --- | --- |
| 1444 | `scaffold-baseline` | `scaffold-baseline` |
| 1836 | `scaffold-baseline` | `scaffold-baseline` |
| 1936 | `scaffold-baseline` | `scaffold-baseline` |

## Consumer guidance

- Pin game saves and mod data to era province IDs when consuming a period-geometry layer.
- Use lineage.json / lineage.csv under eras/<era>/geometry/ to migrate scaffold-only packs.
- Rebuild ownership tables after geometry revisions — politics do not rewrite polygons.
- Read region_quality_matrix.json before claiming period geometry outside Western Europe.
- Profile alignment: eu-like (1444), victoria-like (1836), hoi-like (1936).

## Breaking changes

- we-1444-v1 splits sample_de_rhineland into era_de_cologne + era_de_rhineland_residual.
- we-1836-v1 replaces sample_be_flanders with era_be_flanders_1836.
- we-1936-v1 replaces sample_de_rhineland with era_de_rhineland_1936 (different from 1444 split).

## Do not claim

- period-correct province geometry worldwide
- identical province IDs across all three eras
- Paradox-grade HRE / German Confederation / interwar microborders
