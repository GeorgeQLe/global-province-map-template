# M4 Population-Weighted Refinement

M4 refines the Natural Earth province draft without changing the canonical M2
candidate layer. It is opt-in: any of `--refine`, `--target-province-count`,
`--population-input`, or `--settlement-input` enables the refinement path.

## Inputs

`--population-input` accepts either:

- a georeferenced single-band GeoTIFF whose non-negative cell values are
  population counts; any raster CRS supported by Rasterio is transformed to
  and from WGS84; or
- a WGS84 GeoJSON FeatureCollection of Point features. Each feature needs one
  of `population`, `population_count`, `estimated_population`, `pop_max`,
  `pop_min`, `pop`, `value`, or `weight`.

`--settlement-input` accepts a WGS84 GeoJSON FeatureCollection of Point
features. The same numeric fields are used as seed weights; a missing value
defaults to one. If no separate population input is supplied, settlement
weights also provide the province population estimate.

Point GeoJSON can declare provenance in a top-level object:

```json
{
  "type": "FeatureCollection",
  "gpm": {
    "source_lineage": ["worldpop:2025"],
    "license_lineage": ["WorldPop CC BY 4.0"]
  },
  "features": []
}
```

Raster formats cannot carry this project-specific array reliably, so pass
`--population-license` once per required notice. The corresponding settlement
option is `--settlement-license`. A license-lineage notice is required for
every supplied point or raster input; the build fails cleanly if it is absent.
All paths, embedded lineage, and license notices are propagated to refined
province features and the FeatureCollection M4 summary.

## Algorithm

1. Sum population samples or raster cells inside every source province and
   index settlement points spatially.
2. Allocate the profile target count with a deterministic divisor method. Each
   source province receives one part first; remaining parts use the profile's
   configured area/population blend and `max_split_parts` cap.
3. Choose seeds from high-weight population cells and settlements, then fill
   spatial gaps using deterministic grid representatives and weighted
   farthest-point selection.
4. Generate ordered Voronoi cells and clip them to the source province. Parts
   never cross a source province boundary.
5. Re-sum population and rescale child estimates to conserve each parent's
   population total. Merge fragments below both the configured area and
   population thresholds into the sibling with the longest shared border.
6. Derive split IDs from the source parent ID plus normalized output geometry.
   Feature order, source ring orientation, and repeated builds do not affect
   the result.

Invalid source polygons are not silently repaired. They are preserved without
splitting, marked with `refinement_strategy = "source-geometry-preserved"` and
`refinement_skipped_reason = "invalid-source-geometry"`, and counted in the
build summary. Existing topology QA will continue to fail on those features so
the upstream problem remains visible.

The target is a budget before tiny-fragment merging. Consequently, a build may
finish below the requested count when generated cells fall under safety
thresholds. M4 does not merge unrelated source administrative units; a target
below the M2 source count is rejected.

## Example

```bash
uv run gpm build provinces \
  --profile victoria-like \
  --population-input data/raw/worldpop/population.tif \
  --population-license "WorldPop CC BY 4.0" \
  --settlement-input data/raw/settlements/places.geojson

uv run gpm build adjacency
uv run gpm qa topology
```

Adjacency and topology QA must be regenerated after M4 because split IDs and
boundaries replace the no-refinement processed layer.
