# M9 Public Alpha Dataset Release

M9 packages a **public alpha** of the modern geographic scaffold with
reproducible recipes, attribution, release tagging, and **honest accuracy
labels**. It does **not** claim curated historical politics or period geometry.

## Commands

```bash
# Full processed layer → releases/<tag>/
uv run gpm release alpha --profile modern-small

# Western Europe sample subset (commit-friendly size when run on real data)
uv run gpm release alpha --sample-we --tag alpha-0.1.0-sample-we

# Explicit country filter + scenarios
uv run gpm release alpha \
  --country FRA --country BEL --country DEU \
  --scenario modern-baseline --scenario demo-1444 \
  --output-dir samples/my-sample

# Geometry-only pack (no embedded scenarios)
uv run gpm release alpha --no-scenarios --tag alpha-geo-only
```

### `gpm release alpha`

Reads processed provinces (and optional seas / adjacency) and writes a release
bundle:

| Path | Contents |
| --- | --- |
| `release_manifest.json` | Tag, data vintage, quality tiers, file inventory |
| `ACCURACY.md` / `accuracy_label.json` | Human + machine accuracy labels |
| `RECIPE.md` / `recipe.json` | Reproducible generator steps |
| `attribution.json` | License notices for redistribution |
| `sample/` | Province / sea / adjacency inputs used for the pack |
| `pack/` | Full M7/M8 game template pack (definitions, geojson, scenarios) |
| `topology_qa.json` | Optional copy when present beside provinces |
| `README.md` | How to consume the release |

Options:

- `--profile` generation / export profile (default `modern-small`)
- `--province-input` / `--sea-input` / `--adjacency-input`
- `--output-dir` (default `releases/<tag>/`)
- `--tag` release tag (default `alpha-<version>-<YYYYMMDD>`)
- `--scenario` embed ownership overlays (repeatable; defaults to
  `modern-baseline` and `demo-1444`)
- `--no-scenarios` skip scenario embedding
- `--country` modern `parent_country_id` sample filter (repeatable)
- `--sample-we` convenience filter: FRA, BEL, NLD, LUX, DEU
- `--allow-unknown-overrides` ignore unmatched scenario province overrides
- `--data-vintage` optional vintage label
- `--format text|json`

Missing province input fails with exit code 1. Missing optional sea / adjacency
files are skipped.

## Quality tiers (honest labeling)

| Tier | Meaning |
| --- | --- |
| `scaffold-baseline` | Modern open-geodata scaffold; politics project modern parents or coarse demos |
| `curated-politics` | Human-reviewed tags (future official eras; not this alpha) |
| `period-geometry` | Era-aware shapes where modern outlines fail (future; not this alpha) |

**Public alpha always labels both geometry and politics as `scaffold-baseline`.**

Do **not** claim:

- Paradox-grade historical accuracy
- Official curated 1444 / 1836 / 1936 politics
- Period-correct province geometry worldwide
- Legal maritime boundaries (sea zones are gameplay abstractions)

`demo-1444` is a **tooling demo** overlay. It is not an official era product.

## Bundled sample

Committed illustrative sample:

```text
samples/alpha-modern-scaffold/
```

Six land provinces and three coastal seas for FRA / BEL / NLD / LUX / DEU with
modern-baseline and demo-1444 packs, accuracy labels, and a recipe. Geometry is
**illustrative** (hand-authored sample polygons), not a full Natural Earth
extract—use the recipe on downloaded sources for a real scaffold.

Bundled recipe definition:

```text
configs/recipes/alpha-modern-scaffold.json
```

## Release tagging

Default tag pattern:

```text
alpha-<generator-version>-<UTC-date>
```

Example: `alpha-0.1.0-20260710`

Manifest fields for consumers:

- `release_channel` = `alpha`
- `data_vintage`
- `generator_version`
- `scenario_set`
- `quality_tiers.geometry` / `quality_tiers.politics`
- `is_sample` + `sample_countries` when filtered

## Reproduce a modern scaffold alpha

```bash
uv run gpm sources download --execute --profile modern-small
uv run gpm sources manifest --from-raw --profile modern-small
uv run gpm build provinces --profile modern-small
uv run gpm build seas --profile modern-small
uv run gpm build adjacency --profile modern-small
uv run gpm qa topology --profile modern-small
uv run gpm scenario build --scenario modern-baseline
uv run gpm scenario build --scenario demo-1444
uv run gpm release alpha --sample-we --tag alpha-0.1.0-sample-we
```

Full global alphas are large; keep them under gitignored `releases/`. Prefer
country samples or GitHub Releases / object storage for distribution.

## Schema

`schemas/release-manifest.schema.json` describes the release manifest contract.
`gpm.schemas.validate_release_manifest` checks core invariants.

## Relation to later milestones

| Milestone | Adds |
| --- | --- |
| M10 | Atlas / SaaS export face (see [m10-atlas.md](m10-atlas.md)) |
| M11 | Scenario politics QA + review authoring (**complete**) |
| M12 | First official era `official-1836` (`curated-politics`) — complete |
| M13 | Second official era (`official-1444`) |
| M14 | License-audited beta (complete; see [m14-beta-release.md](m14-beta-release.md)) |
| M15–M16 | Period geometry and multi-era packs |
| M17 | Curation workflow hardening |
