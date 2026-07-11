# Recipe: Public alpha modern scaffold

Recipe id: `alpha-modern-scaffold`  
Profile: `modern-small`  
Milestone: `M9`  
Generator version: `0.1.0`

## Environment

```bash
uv sync
```

```bash
uv pip install -e '.[dev]'
```

- Run commands from the repository root with the gpm entrypoint available.
- Do not commit data/raw/ or full data/processed/ global builds.
- Sample subsets may be committed under samples/ when size is modest.

## Steps

### 1. Download Natural Earth (and other default) source artifacts

Raw data stays under data/raw/ (gitignored). Dry-run omits --execute.

```bash
uv run gpm sources download --execute --profile modern-small
```

### 2. Record downloaded source checksums and metadata

Emit a build source manifest for the release lineage.

```bash
uv run gpm sources manifest --from-raw --profile modern-small
```

### 3. Generate modern land province draft

Writes data/processed/provinces.geojson and intermediate candidates. Omit population/settlement flags for the unrefined M2/M3 draft.

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

### 8. Resolve scenario ownership overlay: demo-1444

Politics overlay only; does not rewrite province geometry.

```bash
uv run gpm scenario build --scenario demo-1444 --profile modern-small
```

### 9. Package public alpha release bundle

Writes release_manifest.json, ACCURACY.md, recipe files, attribution, and an embedded game template pack.

```bash
uv run gpm release alpha --profile modern-small --scenario modern-baseline --scenario demo-1444 --country FRA --country BEL --country NLD --country LUX --country DEU --tag alpha-0.1.0-sample-we
```
