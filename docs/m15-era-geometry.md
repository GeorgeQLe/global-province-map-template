# M15 Era-Aware Geometry v1 (Priority Region)

Status: **prototype/infrastructure complete**. The shipped hard overrides are
sample-scoped and do not constitute production historical coverage. Boundary
hints alone are not sufficient for a `period-geometry` claim; certification
requires full-build application and spatial QA in M25–M28.

M15 ships the first period-geometry prototype track: soft historical **boundary
hints**, optional **hard province overrides** for a priority region, and
**ID lineage maps** so consumers can migrate data across geometry revisions.

It sits after the M14 license-audited beta and M14.5 public demo. Full multi-era
geometry packs are **M16** (`we-multi-era-v1`, additional era packs, official-1936).

## Why

Curated politics on modern admin shapes often fails a historian or Paradox-eye
sniff test (modern DE-NW as “Cologne,” modern nation outlines for 1444). Soft
frontier bands and priority-region hard overrides address that **without** a
full-world redraw every patch.

## What shipped

| Artifact | Role |
| --- | --- |
| `configs/era_geometry/we-1444-v1.json` | Priority-region pack (Western Europe · 1444) |
| `gpm era-geometry list\|validate\|apply` | CLI for packs |
| `src/gpm/era_geometry/` | Load, validate, apply, lineage helpers |
| `schemas/era-geometry-pack.schema.json` | Pack contract |
| `schemas/era-geometry-lineage.schema.json` | Lineage map contract |
| `samples/era-geometry-we-1444/` | Applied sample + README |
| Demo toggles | Period geometry + boundary hints on 1444 |
| Quality labeling | Illustrative priority-region sample; not full-build certification |

## Geometry modes

| Mode | Effect | Topology |
| --- | --- | --- |
| `boundary_hints` | Soft LineString / Polygon frontier bands | Overlay only; scaffold IDs unchanged |
| `hard_overrides` | `replace`, `split`, or `identity` on scaffold provinces | Rewrites / splits polygons; emits lineage |

Hard overrides that reference missing `scaffold_province_id`s are **skipped**
(counted). That lets the same pack ship sample-ID demos while still providing
soft hints on full Natural Earth builds.

## Commands

```bash
uv run gpm era-geometry list
uv run gpm era-geometry validate --pack we-1444-v1

# Apply to processed scaffold (or the beta WE sample)
uv run gpm era-geometry apply \
  --pack we-1444-v1 \
  --province-input samples/beta-license-audited/sample/provinces.geojson \
  --output-dir samples/era-geometry-we-1444 \
  --recompute-adjacency \
  --profile modern-small
```

### Outputs (`data/processed/era_geometry/<pack-id>/` by default)

| Path | Contents |
| --- | --- |
| `provinces.geojson` | Era-aware (or annotated scaffold) provinces |
| `boundary_hints.geojson` | Soft frontier features |
| `lineage.json` / `lineage.csv` | Scaffold ↔ era province ID map |
| `quality_scope.json` | Period-true vs scaffold-backed scope |
| `era_geometry_manifest.json` | Counts, modes, file inventory |
| `adjacency.csv` | Optional; only with `--recompute-adjacency` |

## Pack `we-1444-v1`

| Field | Value |
| --- | --- |
| Era / scenario | `1444` / `official-1444` |
| Priority region | Western Europe (`FRA`, `BEL`, `NLD`, `LUX`, `DEU`) |
| Quality tier | `period-geometry` prototype label (sample-scoped) |
| Soft hints | Burgundian Low Countries, Franco-Burgundian, Rhine corridor, Channel/Calais, Low Countries band |
| Hard overrides (sample IDs) | Split Rhineland → Cologne + residual; reshape Flanders & Luxembourg; identity for Paris / Normandy / Holland |

## Lineage map

Each row maps:

- `era_province_id` — addressable ID after apply  
- `scaffold_province_id` — modern scaffold parent  
- `operation` — `identity` · `replace` · `split_child` · `merge_parent` · `reshape`

Game and SaaS consumers should attach saves/mods to **era** IDs when using a
period pack, and use lineage to migrate from scaffold-only packs.

## Quality labeling

`gpm.release.quality.accuracy_label` with `geometry_tier=period-geometry`
states that period shapes are **priority-region scoped** and still forbids
worldwide period-correct geometry claims.

Public beta packaging (`gpm release beta`) remains scaffold-baseline geometry
by default until a release explicitly claims the period-geometry tier.

## Demo

`landing/demo/` gains live toggles:

- **Period geometry (1444)** — hard overrides / splits for the WE sample  
- **Historical boundary hints** — soft amber frontier bands (default on for 1444)

Scaffold choropleths remain the default province layer until the period toggle
is enabled.

## Relation to other milestones

| Milestone | Relation |
| --- | --- |
| M8–M13 | Politics overlays on modern scaffold |
| M14 / M14.5 | Beta sample + public demo scaffolding |
| **M15** | Era-aware geometry v1 for a priority region |
| M16 | Multi-era geometry + politics packs (incl. 1936) — prototype/infrastructure complete |
| M17 | Diffs, golden borders, external curator bundles |

## Honest limits

- Not Paradox-grade HRE microborders or French appanage completeness  
- Soft hints are **illustrative**, not legal 1444 frontiers  
- Hard overrides in the shipped pack target **sample** province IDs  
- Outside the priority region, modern scaffold geometry is retained  
- Not derived from proprietary game maps  
