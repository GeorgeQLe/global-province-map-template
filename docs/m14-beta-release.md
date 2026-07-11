# M14 License-Audited Beta Release

M14 packages a **public beta** with:

- cleaned, redistributable source lineage
- a full **attribution pack** plus isolation notices
- **restricted-path isolation** (GADM / ODbL stay out of the public pack)
- **dual export faces**: game template pack and atlas / SaaS pack
- honest accuracy labels (geometry still scaffold; politics may be curated)

It builds on M9 alpha packaging and M10–M13 product content (atlas face,
official-1836, official-1444).

## Commands

```bash
# Full processed layer → releases/<tag>/
uv run gpm release beta --profile modern-small

# Western Europe sample subset (commit-friendly size when run on real data)
uv run gpm release beta --sample-we --tag beta-0.1.0-sample-we

# Explicit country filter + official scenarios
uv run gpm release beta \
  --country FRA --country BEL --country DEU \
  --scenario modern-baseline \
  --scenario official-1836 \
  --scenario official-1444 \
  --output-dir samples/my-beta

# Game pack only (skip atlas face)
uv run gpm release beta --no-atlas --tag beta-game-only

# Geometry pack without scenarios (also skips atlas)
uv run gpm release beta --no-scenarios --tag beta-geo-only
```

### `gpm release beta`

Reads processed provinces (and optional seas / adjacency), runs a **license
audit**, and writes a release bundle:

| Path | Contents |
| --- | --- |
| `release_manifest.json` | Tag, vintage, quality tiers, faces, file inventory |
| `license_audit.json` / `LICENSE_AUDIT.md` | Audit status, isolation notes, findings |
| `ACCURACY.md` / `accuracy_label.json` | Human + machine accuracy labels |
| `RECIPE.md` / `recipe.json` | Reproducible generator steps |
| `attribution.json` | Cleaned attribution pack (public + isolation notices) |
| `sample/` | Province / sea / adjacency inputs used for the packs |
| `pack/` | M7/M8 game template pack |
| `atlas/` | M10 atlas / SaaS face (when scenarios are present) |
| `topology_qa.json` | Optional copy when present beside provinces |
| `README.md` | How to consume the release |

Options:

- `--profile` generation / export profile (default `modern-small`)
- `--province-input` / `--sea-input` / `--adjacency-input`
- `--output-dir` (default `releases/<tag>/`)
- `--tag` release tag (default `beta-<version>-<YYYYMMDD>`)
- `--scenario` embed ownership overlays (repeatable; defaults to
  `modern-baseline`, `official-1836`, `official-1444`)
- `--no-scenarios` skip scenario embedding (also skips atlas)
- `--no-atlas` game pack only
- `--country` modern `parent_country_id` sample filter (repeatable)
- `--sample-we` convenience filter: FRA, BEL, NLD, LUX, DEU
- `--allow-unknown-overrides` ignore unmatched scenario province overrides
- `--allow-license-errors` write audit but do not fail (not for public packs)
- `--data-vintage` optional vintage label
- `--format text|json`

Missing province input fails with exit code 1. License audit errors fail the
release unless `--allow-license-errors` is set.

## License audit

The audit gates public packaging on:

1. **Catalog policy** — profile defaults must be eligible, non-restricted, and
   non-share-alike.
2. **Feature lineage** — every feature must carry `license_lineage`; tokens
   matching GADM, ODbL/OpenStreetMap, restricted, or share-alike fail the audit.
3. **Attribution pack** — public-path notices for catalog defaults plus
   isolation notices documenting excluded paths.

| Path class | Examples | Public beta |
| --- | --- | --- |
| Core / public-safe | Natural Earth (PD), geoBoundaries (CC BY) | Yes |
| Deferred public-safe | GHSL, WorldPop (when used) | Yes if lineage present |
| Optional isolated | OpenStreetMap (ODbL) | No — stay isolated |
| Restricted | GADM | No — excluded |

Isolation notices appear in `attribution.json` with `"public_path": false` and
`"isolation_notice": true`. They document policy; they are not redistributable
layers.

Schema: `schemas/license-audit-report.schema.json`  
Validator: `gpm.schemas.validate_license_audit_report`

## Quality tiers

| Layer | Default for M14 beta |
| --- | --- |
| Geometry | `scaffold-baseline` (period geometry is M15+) |
| Politics | `curated-politics` when any `official-*` scenario is embedded; otherwise `scaffold-baseline` |

Still do **not** claim:

- Paradox-grade historical accuracy worldwide
- Period-correct province geometry
- Legal maritime boundaries
- Complete global politics outside priority theaters

## Bundled sample

Committed illustrative sample:

```text
samples/beta-license-audited/
```

Six land provinces and three coastal seas for FRA / BEL / NLD / LUX / DEU with
modern-baseline, official-1836, and official-1444 on both game and atlas faces,
plus license audit and accuracy labels. Geometry is **illustrative** (same
hand-authored sample polygons as the alpha sample)—use the recipe on downloaded
sources for a real scaffold.

Bundled recipe definition:

```text
configs/recipes/beta-license-audited.json
```

## Release tagging

Default tag pattern:

```text
beta-<generator-version>-<UTC-date>
```

Example: `beta-0.1.0-20260710`

Manifest extras vs alpha:

- `release_channel` = `beta`
- `milestone` = `M14`
- `license_audit_path` / `license_audit_passed`
- `faces.game` and `faces.atlas`

## Reproduce a license-audited beta

```bash
uv run gpm sources download --execute --profile modern-small
uv run gpm sources manifest --from-raw --profile modern-small
uv run gpm build provinces --profile modern-small
uv run gpm build seas --profile modern-small
uv run gpm build adjacency --profile modern-small
uv run gpm qa topology --profile modern-small
uv run gpm scenario build --scenario modern-baseline
uv run gpm scenario build --scenario official-1836
uv run gpm scenario build --scenario official-1444
uv run gpm qa scenario --scenario official-1836
uv run gpm qa scenario --scenario official-1444
uv run gpm release beta --sample-we --tag beta-0.1.0-sample-we
```

Full global betas are large; keep them under gitignored `releases/`. Prefer
country samples or GitHub Releases / object storage for distribution.

## Relation to other milestones

| Milestone | Relation |
| --- | --- |
| M9 | Alpha packaging (game pack only, scaffold scenarios) |
| M10 | Atlas face embedded in beta |
| M12–M13 | Official era scenarios shipped in default beta scenario set |
| **M14** | License audit + dual faces + cleaned attribution |
| M15–M16 | Period geometry and multi-era packs |
| M17 | Curation workflow hardening |
