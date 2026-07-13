# M20 Broader Period Geometry (Beyond Western Europe)

M20 expands the **period-geometry** track past the M15/M16 Western Europe
priority region by adding **Central Europe** packs for all three official eras
and a **composed multi-region multi-era pack** that applies WE + CE geometry
together.

It sits after M19 PMTiles / vector tiles.

## Why

Roadmap showcase path: deepen **priority regions** (Western / Central Europe)
before claiming global period-correct shapes. Soft frontier bands and hard
overrides in a second theater make the historical sniff test work for Habsburg,
Bohemian Crown, Polish, and Hungarian stories without a full-world redraw.

## What shipped

| Artifact | Role |
| --- | --- |
| `configs/era_geometry/ce-1444-v1.json` | Central Europe 1444 period geometry |
| `configs/era_geometry/ce-1836-v1.json` | Central Europe 1836 period geometry |
| `configs/era_geometry/ce-1936-v1.json` | Central Europe 1936 period geometry |
| `configs/multi_era/europe-multi-era-v1.json` | WE + CE multi-era composition |
| `apply_era_geometry_packs(...)` | Ordered multi-pack apply + merged hints/lineage |
| `era_geometry_pack_ids` on multi-era era slots | Compose multiple packs per era |
| `samples/scaffold-we-ce/` | Expanded scaffold (WE beta + CE sample provinces) |
| `samples/era-geometry-ce-1444/` | Applied CE 1444 sample |
| `samples/multi-era-europe-v1/` | Built multi-region multi-era sample |
| Demo | Live WE+CE scaffold + Europe period layers / hints |

## Priority regions

| Region | Modern ISO parents | Packs |
| --- | --- | --- |
| Western Europe | FRA, BEL, NLD, LUX, DEU | `we-1444-v1`, `we-1836-v1`, `we-1936-v1` |
| Central Europe | AUT, CZE, POL, HUN | `ce-1444-v1`, `ce-1836-v1`, `ce-1936-v1` |

Composite multi-era pack `europe-multi-era-v1` uses `priority_region`
`western-and-central-europe` and a `priority_regions` list for both theaters.
Region quality matrix marks **both** as `period-geometry` for 1444 / 1836 / 1936.

## Central Europe geometry highlights

| Pack | Soft hints (examples) | Hard overrides (sample) |
| --- | --- | --- |
| `ce-1444-v1` | Bohemian Crown, Ottoman–Hungarian, Habsburg–Hungarian, Polish approach, Silesia band | Split Bohemia → Prague + residual; reshape Pannonia |
| `ce-1836-v1` | Austrian Empire core, Galicia corridor, Hungarian lands, Bohemian crownland | Reshape Vienna; identities for Bohemia / Mazovia / Pannonia |
| `ce-1936-v1` | Sudeten fringe, Anschluss approach, Polish corridor, Hungarian revisionist fringe | Reshape Bohemia 1936; identities elsewhere |

## Multi-pack composition

Multi-era era slots may declare:

```json
"era_geometry_pack_ids": ["we-1444-v1", "ce-1444-v1"]
```

Build applies packs **left-to-right**, merges boundary hints, and merges lineage
so later scaffold pass-throughs do not clobber earlier hard overrides. Original
`scaffold_province_id` is preserved across steps.

```bash
uv run gpm multi-era list
uv run gpm multi-era validate --pack europe-multi-era-v1

uv run gpm multi-era build \
  --pack europe-multi-era-v1 \
  --province-input samples/scaffold-we-ce/provinces.geojson \
  --output-dir samples/multi-era-europe-v1 \
  --profile modern-small
```

Single-region CE apply:

```bash
uv run gpm era-geometry apply \
  --pack ce-1444-v1 \
  --province-input samples/scaffold-we-ce/provinces.geojson \
  --output-dir samples/era-geometry-ce-1444
```

## Quality matrix (europe-multi-era-v1)

| Region | Geometry (all eras) | Politics |
| --- | --- | --- |
| Western Europe | `period-geometry` | `curated-politics` |
| Central Europe | `period-geometry` | `curated-politics` |
| Europe elevated (outside WE/CE hard overrides) | `scaffold-baseline` | `curated-politics` |
| Global majors | `scaffold-baseline` | `curated-politics` |
| Rest of world | `scaffold-baseline` | `scaffold-baseline` |

## Demo

`landing/demo/` loads the WE+CE scaffold (10 land provinces) and period layers
from `europe-multi-era-v1` (merged WE + CE boundary hints; hard overrides in
both theaters). Geometry status text shows the multi-era pack id.

## Relation to other milestones

| Milestone | Relation |
| --- | --- |
| M15 | First WE period-geometry pack |
| M16 | WE multi-era + 1836/1936 WE packs |
| M17–M19 | Curation, culture paint, PMTiles |
| **M20** | Second priority region + multi-region composition |

## Honest limits

- Still **not** period-correct geometry worldwide
- Soft hints are **illustrative**, not legal frontiers
- Hard overrides target **sample** province IDs (`sample_*`)
- Outside WE + CE priority parents, modern scaffold is retained
- Not Paradox-grade HRE / Bohemian Crown / Austrian Empire / interwar microborders
- Not derived from proprietary game maps
