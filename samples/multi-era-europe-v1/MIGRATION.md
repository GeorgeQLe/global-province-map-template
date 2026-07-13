# Migration notes: `europe-multi-era-v1`

Scaffold province IDs are the stable cross-era join key. Each era composes WE + CE era-geometry packs (applied in that order); use lineage.json to migrate. Politics are scenario overlays rebuilt per era.

## Lineage strategy

Composed packs emit a merged lineage map. Do not assume era IDs match across 1444/1836/1936 or across WE vs CE packs. Cross-era analytics should join on scaffold_province_id.

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

### Central Europe (priority region)

| Era | Geometry | Politics |
| --- | --- | --- |
| 1444 | `period-geometry` | `curated-politics` |
| 1836 | `period-geometry` | `curated-politics` |
| 1936 | `period-geometry` | `curated-politics` |

### Europe elevated theaters (outside WE/CE hard overrides)

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
- Read region_quality_matrix.json: period geometry covers Western Europe and Central Europe only.
- Profile alignment: eu-like (1444), victoria-like (1836), hoi-like (1936).

## Breaking changes

- we-1444-v1 splits sample_de_rhineland into era_de_cologne + era_de_rhineland_residual.
- ce-1444-v1 splits sample_cz_bohemia into era_cz_prague + era_cz_bohemia_residual.
- we-1836-v1 replaces sample_be_flanders with era_be_flanders_1836.
- ce-1836-v1 replaces sample_at_vienna with era_at_vienna_1836.
- we-1936-v1 replaces sample_de_rhineland with era_de_rhineland_1936.
- ce-1936-v1 replaces sample_cz_bohemia with era_cz_bohemia_1936.

## Do not claim

- period-correct province geometry worldwide
- identical province IDs across all three eras
- Paradox-grade HRE / Bohemian Crown / Austrian Empire / interwar microborders
