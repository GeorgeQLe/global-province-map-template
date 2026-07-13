# M23 (design note) — Game-like province density

Status: **not implemented**. This note fixes the contract and records the
Paradox design-theory research so the density milestone can start from a
settled brief. The M21 hierarchy and M22 demo were built with these hooks in
mind.

## Contract with the existing pipeline

1. **Split mechanism** is the existing M4 refinement
   (`gpm build provinces --refine …`): children inherit `parent_region_id`
   (the admin-1 code) from their parent.
2. **Hierarchy stability**: re-running `gpm build hierarchy` after a split
   reassigns children to areas by `parent_region_id` lookup with **unchanged
   area IDs** (areas cluster admin-1 codes, never province hashes; tested in
   `test_area_ids_stable_under_simulated_m4_split`).
3. **Oversized areas**: after splitting, areas keep their admin-1 membership
   but hold many more provinces. The reserved `[hierarchy] split_large_areas`
   option will re-split such areas *within* their admin-1 sets, minting child
   area IDs with lineage back to the stable parent.
4. **Iconic-location seeding** plugs into M4 refinement seeding (settlement
   seeds with forced placement), *not* into the hierarchy builder.
5. The demo needs no schema change: `gpm demo build` re-tiles whatever the
   processed build contains.

## Confirmed Paradox design principles (dev diaries / wikis / credible analysis)

1. **Population density is the primary density driver**, log-compressed —
   dense provinces where people lived (HRE, N. Italy, S. India), sparse where
   not (Siberia, Sahara). But **capped by pacing**: sparse land deliberately
   gets *fewer* provinces so traversal isn't tedious and empty regions aren't
   buffed (EU4 1.29 dev diaries).
2. **Historical political fragmentation is a separate axis** — regions that
   must host many playable tags (HRE, Sengoku Japan, Italian city-states) need
   ≥1 province per historical polity regardless of population.
3. **Iconic locations get extra weight decoupled from population** — HOI4
   victory points are strategic/flavor-weighted ("or simply for game play
   reasons"), and EU5 has population-less "corridor" locations purely for
   famous passes/straits.
4. **Wastelands/chokepoints are engineered, not just mapped** — EU4 added
   impassables specifically to create natural borders and sever strategic
   routes (Hengduan, Changthang).
5. **Terrain sets movement cost** (EU5: mountains +100%, hills +50%), so
   target uniform *travel time* per province within a theater, not uniform
   area.
6. **Mid-tier grouping sizes**: EU4 area = 2–5 provinces, region ≈ 10 areas,
   17 superregions, 6 continents; EU5 area = 25–75 locations (~7 locations per
   EU4-province-equivalent); HOI4 state ≈ 16 provinces, strategic region ≈ 3–4
   states; Vic3 strategic region ≈ 11–19 state regions.
7. **Reference totals**: EU4 3,272 land provinces; EU5 27,518 locations; Vic2
   2,705 provinces; Vic3 ~620–690 state regions / 36–58 strategic regions;
   HOI4 ~13–14k provinces / ~834 states / ~227 strategic regions.
8. **Curation beats generation** — EU5 ran 16 months of public map review with
   thousands of hand fixes. Encode as: generated baseline + hand-curated
   override/seed layer (fits the existing M17 curation/override tooling).

## Weighting sketch

```
W(cell) = [ w_pop·log(1+ρ/ρ_ref) + w_frag·F + w_coast·C + w_terr·V ] · M(terrain)
          · (1−H) + w_icon·I
```

- `F` — historical-fragmentation prior (HRE, Japan, Italy priors per era)
- `M` — movement-cost normalizer (target uniform travel time)
- `H` — habitability mask (→ wasteland polygons + corridor provinces)
- `I` — curated iconic-seed field (battle sites, passes, straits, holy
  cities) with **forced seed placement** — an iconic site always becomes its
  own province, HOI4-VP style.

Post-passes: travel-time equalization, min/max area clamps, chokepoint
reduction, curated override layer.

## Profile targets this implies

- `eu-like`: ~3,000–3,500 land provinces → ~750–900 areas (2–5 each) →
  ~75–100 regions → ~17 superregions. (The current profile's 22,000 target is
  EU5-location-scale; consider renaming or retargeting.)
- `victoria-like`: ~2,500–2,800 provinces → 600–700 states (3–6 each) →
  40–60 strategic regions.
- `hoi-like`: ~13,500 provinces → ~830 states (~16 each) → ~225 strategic
  regions, with VP-style iconic weights on ~5–10% of provinces.

The M21 defaults (`area_target_size = 8` admin-1 units) were chosen for the
current 4,603-province admin-1 build; once density splitting lands, retune
toward the per-game norms above (eu-like ~4, hoi-like ~16).
