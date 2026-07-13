# Scaffold sample: Western + Central Europe

Expanded modern-scaffold province sample for **M20** broader period geometry.

| Region | Province IDs | Modern ISO |
| --- | --- | --- |
| Western Europe | `sample_fr_*`, `sample_be_*`, `sample_nl_*`, `sample_de_*`, `sample_lu_*` | FRA BEL NLD DEU LUX |
| Central Europe | `sample_at_vienna`, `sample_cz_bohemia`, `sample_pl_mazovia`, `sample_hu_pannon` | AUT CZE POL HUN |

Use as `--province-input` when applying CE packs or building `europe-multi-era-v1`.

```bash
uv run gpm era-geometry apply --pack ce-1444-v1 \
  --province-input samples/scaffold-we-ce/provinces.geojson \
  --output-dir samples/era-geometry-ce-1444

uv run gpm multi-era build --pack europe-multi-era-v1 \
  --province-input samples/scaffold-we-ce/provinces.geojson \
  --output-dir samples/multi-era-europe-v1
```

Polygons are pedagogical rectangles (same style as the beta WE sample), not
Natural Earth extracts.
