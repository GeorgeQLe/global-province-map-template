# M16 Multi-Era Geometry + Politics Packs

M16 ships **paired geometry + politics** for at least two official eras (here:
**three** — 1444, 1836, and 1936), with **documented quality tiers per region**
and **migration notes** for consumers.

It sits after M15 era-aware geometry v1 (single priority-region pack for 1444)
and completes the Phase 11 official era track with the deferred **1936**
HOI-leaning program.

## Why

Game and SaaS consumers need more than one era at a time, with clear answers to:

- Which regions are period-true vs scaffold-backed?
- How do province IDs migrate when geometry packs split or replace provinces?
- How do politics and geometry version together without silent breakage?

## What shipped

| Artifact | Role |
| --- | --- |
| `configs/multi_era/we-multi-era-v1.json` | Multi-era pack (1444 + 1836 + 1936) |
| `configs/era_geometry/we-1836-v1.json` | Second era geometry pack |
| `configs/era_geometry/we-1936-v1.json` | Interwar era geometry pack |
| `configs/scenarios/official-1936.json` | Third official curated-politics scenario |
| `configs/scenarios/golden/official-1936.json` | Golden tag floors |
| `gpm multi-era list\|validate\|build\|migration` | CLI |
| `src/gpm/multi_era/` | Pack load/validate, build, migration notes |
| `schemas/multi-era-pack.schema.json` | Pack contract |
| `schemas/multi-era-migration-notes.schema.json` | Migration contract |
| `samples/multi-era-we-v1/` | Built sample + `MIGRATION.md` |
| Demo | Live 1936 tab + period geometry for all three eras |

## Multi-era pack model

A multi-era pack declares:

1. **Priority region** (same shape as era-geometry packs)
2. **Era slots** — each with `scenario_id`, optional `era_geometry_pack_id`,
   geometry/politics quality tiers, and recommended profile
3. **Region quality matrix** — per-region geometry + politics tiers by era
4. **Migration notes** — lineage strategy, consumer guidance, breaking changes

Minimum: **two** era slots. Bundled `we-multi-era-v1` ships three.

## Commands

```bash
uv run gpm multi-era list
uv run gpm multi-era validate --pack we-multi-era-v1
uv run gpm multi-era migration --pack we-multi-era-v1 --output-dir /tmp/mig

# Build full package (geometry apply + politics resolve + notes)
uv run gpm multi-era build \
  --pack we-multi-era-v1 \
  --province-input samples/beta-license-audited/sample/provinces.geojson \
  --output-dir samples/multi-era-we-v1 \
  --profile modern-small
```

### Outputs (`data/processed/multi_era/<pack-id>/` by default)

| Path | Contents |
| --- | --- |
| `eras/<era>/geometry/` | Applied (or scaffold) provinces, hints, lineage |
| `eras/<era>/politics/` | Resolved ownership tables for the era scenario |
| `region_quality_matrix.json` | Per-region quality tiers by era |
| `MIGRATION.md` / `migration_notes.json` | Consumer migration notes |
| `multi_era_manifest.json` | Build inventory |
| `pack.json` | Copy of the pack definition |

## official-1936

| Field | Value |
| --- | --- |
| `scenario_id` | `official-1936` |
| `era` / `start_date` | `1936` / `1936-01-01` |
| `quality_tier` | `curated-politics` |
| `official_era` | `true` |
| `recommended_profile` | `hoi-like` |
| `priority_theaters` | `europe`, `east-asia`, `colonial-mandates`, `contested-interwar` |

Elevated content includes:

- Interwar majors (GER, ITA, JAP, SOV, ENG, FRA, USA, CHI)
- Contested stories: Rhineland, Sudeten claims, Danzig corridor, Ethiopian invasion
- Manchukuo / ROC split on Chinese scaffold regions
- Independent Austria (pre-Anschluss)
- Colonial and mandate tables (French, British, Belgian, Portuguese, Italian)

```bash
uv run gpm scenario validate --scenario official-1936
uv run gpm scenario build --scenario official-1936 --profile hoi-like
uv run gpm qa scenario --scenario official-1936 --profile hoi-like
```

## Quality tiers per region

Example matrix rows in `we-multi-era-v1`:

| Region | Geometry (all eras) | Politics |
| --- | --- | --- |
| Western Europe priority | `period-geometry` | `curated-politics` |
| Europe elevated theaters | `scaffold-baseline` | `curated-politics` |
| Global major tags | `scaffold-baseline` | `curated-politics` |
| Rest of world | `scaffold-baseline` | `scaffold-baseline` |

## Migration notes for consumers

1. **Join key across eras:** `scaffold_province_id` (not era IDs)
2. **Pin saves/mods** to era province IDs when using a period-geometry layer
3. **Rebuild politics** after geometry revisions — ownership is an overlay
4. **Read the matrix** before claiming period geometry outside the priority region
5. **Breaking ID changes in v1 packs:**
   - 1444 splits `sample_de_rhineland` → Cologne + residual
   - 1836 replaces Flanders sample ID
   - 1936 replaces Rhineland sample ID (different from the 1444 split)

## Era geometry packs (M16 additions)

| Pack | Era | Soft hints (examples) | Hard overrides (sample) |
| --- | --- | --- | --- |
| `we-1444-v1` | 1444 | Burgundy / Rhine / Channel | Cologne split, Flanders reshape |
| `we-1836-v1` | 1836 | Belgian southern, Prussian Rhine | Flanders reshape, identities |
| `we-1936-v1` | 1936 | Maginot, Rhineland DMZ band | Rhineland reshape, identities |

## Demo

`landing/demo/` ships live tabs for **1444 · 1836 · 1936 · Modern**, with period
geometry and boundary-hint toggles for all three historical eras. Multi-era packs
move from “reserved” into live layers.

## Relation to other milestones

| Milestone | Relation |
| --- | --- |
| M12–M13 | Official politics for 1836 and 1444 |
| M15 | First era-geometry pack (`we-1444-v1`) |
| **M16** | Multi-era packaging, second/third geometry packs, official-1936 |
| M17 | Diffs, golden borders, external curator bundles — complete |

## Honest limits

- Period geometry remains **priority-region scoped** (Western Europe)
- Soft hints are **illustrative**, not legal frontiers
- Hard overrides in shipped packs target **sample** province IDs
- Politics are curated overlays — residual modern ISO baselines may remain
- Not Paradox-grade HRE / Confederation / interwar microborders
- Not derived from proprietary game maps
