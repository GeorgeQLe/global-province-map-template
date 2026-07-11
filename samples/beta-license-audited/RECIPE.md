# Recipe: Public beta license-audited dual-face release

Recipe id: `beta-license-audited`  
Profile: `modern-small`  
Milestone: `M14`  
Generator version: `0.1.0`

## Environment

```bash
uv sync
```

```bash
uv pip install -e '.[dev]'
```

- Run commands from the repository root with the gpm entrypoint available.
- Do not mix ODbL or restricted sources into public beta packs.
- Do not commit data/raw/ or full data/processed/ global builds.
- Sample subsets may be committed under samples/ when size is modest.

## Steps

### 1. Download core (public-safe) source artifacts only

Uses profile defaults. Restricted (GADM) and share-alike (OSM) sources are not on the default path and must stay isolated.

```bash
uv run gpm sources download --execute --profile modern-small
```

### 2. Record downloaded source checksums and metadata

Emit a build source manifest for the release lineage.

```bash
uv run gpm sources manifest --from-raw --profile modern-small
```

### 3. Generate modern land province draft

Writes data/processed/provinces.geojson. Features must carry license_lineage for the beta license audit.

```bash
uv run gpm build provinces --profile modern-small
```

### 4. Generate coastal and ocean sea zones

Gameplay-first sea zones; not legal maritime boundaries.

```bash
uv run gpm build seas --profile modern-small
```

### 5. Generate land (and marine) adjacency

Marine edges appear only when sea_zones.geojson is present.

```bash
uv run gpm build adjacency --profile modern-small
```

### 6. Run topology QA

CI-gating geometry, coverage, and graph checks.

```bash
uv run gpm qa topology --profile modern-small
```

### 7. Resolve scenario ownership overlay: modern-baseline

Politics overlay only; does not rewrite province geometry.

```bash
uv run gpm scenario build --scenario modern-baseline --profile modern-small
```

### 8. Resolve scenario ownership overlay: official-1836

Politics overlay only; does not rewrite province geometry.

```bash
uv run gpm scenario build --scenario official-1836 --profile modern-small
```

### 9. Run politics QA for official-1836

Coverage, tag, component, and golden-floor checks.

```bash
uv run gpm qa scenario --scenario official-1836 --profile modern-small
```

### 10. Resolve scenario ownership overlay: official-1444

Politics overlay only; does not rewrite province geometry.

```bash
uv run gpm scenario build --scenario official-1444 --profile modern-small
```

### 11. Run politics QA for official-1444

Coverage, tag, component, and golden-floor checks.

```bash
uv run gpm qa scenario --scenario official-1444 --profile modern-small
```

### 12. Package license-audited beta (game + atlas faces)

Writes release_manifest.json, LICENSE_AUDIT.md, attribution pack, ACCURACY.md, recipe files, game pack/, and optional atlas/.

```bash
uv run gpm release beta --profile modern-small --scenario modern-baseline --scenario official-1836 --scenario official-1444 --country FRA --country BEL --country NLD --country LUX --country DEU --tag beta-0.1.0-sample-we
```
