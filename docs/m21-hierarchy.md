# M21 — Four-level hierarchy (province → area → region → superregion)

`gpm build hierarchy` turns the flat province layer into a real
Paradox-style nesting:

| Level | Entity prefix | Scale (global admin-1 build) | Source of grouping |
| --- | --- | --- | --- |
| Province | `ne_` | 4,603 | Natural Earth admin-1 (admin-0 fallback) |
| Area | `ar_` | ~660 | Deterministic greedy clustering of admin-1 codes over the land-adjacency graph |
| Region | `rg_` | ~170 | One per country; micro-states coalesced by NE admin-0 subregion; mega-countries split by the NE admin-1 `region` attribute |
| Superregion | `sr_` | 8 | One per NE continent |

## Running it

```bash
uv run gpm build provinces      # requires the Natural Earth raw zips
uv run gpm build adjacency
uv run gpm build hierarchy      # writes hierarchy.geojson + enriches provinces
```

Outputs:

- `data/processed/hierarchy.geojson` — area/region/superregion features with
  `region_type`, dissolved geometry, member lists (`member_region_ids`,
  `admin1_codes`, `province_ids`), a precomputed `label_point`, and lineage.
- `data/processed/provinces.geojson` is enriched **in place** with three new
  additive fields per land province: `parent_area_id`, `parent_geo_region_id`,
  `parent_superregion_id`. The existing `parent_region_id` (the source admin-1
  code) is **not** repurposed — scenario region rules, refinement inheritance,
  and province ID hashing all depend on it.

`gpm export pack` prefers real hierarchy entities when `hierarchy.geojson`
sits next to the province input (`[export] region_type` selects the level:
`state → area`, `region`/`strategic_region → region`,
`superregion → superregion`); the legacy `parent_region_id` dissolve remains
the fallback for sample scaffolds.

`gpm.exporters.export_hierarchy_layers` emits slim simplified overlay layers
(`areas.geojson`, `regions.geojson`, `superregions.geojson`) with label
points and a deterministic `area_color`, sized for direct web use.

## Determinism and stability contract

- Areas cluster **admin-1 codes, never province hashes**. Seeds are the
  lexicographically smallest unassigned codes; growth follows the strongest
  shared border (ties broken lexicographically); undersized clusters merge by
  longest shared border, islands by nearest centroid. Same inputs → byte-equal
  output (modulo the `generated_at` stamp).
- Entity IDs are `ar_/rg_/sr_` + slug + 12-hex sha256 over a canonical
  identity document (country + sorted admin-1 codes for areas; grouping kind +
  key for regions; continent for superregions) — the same scheme as province
  IDs.
- **M4 split stability:** a future density split produces children that
  inherit `parent_region_id`. Because clustering never counts provinces, the
  admin-1 graph is unchanged, so re-running `gpm build hierarchy` reproduces
  identical area IDs and reassigns the children by lookup. This is covered by
  `test_area_ids_stable_under_simulated_m4_split`.

## Configuration (`[hierarchy]` in profiles)

```toml
[hierarchy]
area_target_size = 8            # admin-1 units per area (≈ provinces today)
area_min_size = 3
area_max_size = 15
mega_region_area_threshold = 4  # areas needed before a country may split
mega_region_min_area_sq_km = 2000000  # …and it must be continental-scale
region_target_size = 10         # fallback chunk size for attribute-less megas
```

The `mega_region_min_area_sq_km` gate keeps municipality-dense micro-states
(Malta has 68 NE admin-1 units, North Macedonia 84) as single regions while
USA / Russia / China / India split along their NE `region` attribute.

Reserved for the density milestone: `split_large_areas` (re-splitting areas
that grow past `area_max_size` provinces after M4 splits).
