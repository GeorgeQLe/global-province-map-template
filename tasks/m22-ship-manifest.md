# M20–M22 Ship Manifest

## User goal

Publish the complete M20–M22 implementation as one coherent `main` release,
validate an exact Vercel preview, and leave production promotion gated on
explicit approval. M23 remains design-only.

## Changed files and per-file purpose

- `src/gpm/era_geometry/{__init__,apply}.py`,
  `src/gpm/multi_era/{__init__,build,packs}.py`, M20 configs/schemas/samples,
  and `tests/test_m20_broader_period_geometry.py`: compose Western and Central
  Europe period packs while preserving lineage.
- `src/gpm/builders/{provinces,hierarchy}.py`, `src/gpm/config.py`, hierarchy
  profile tables, entity schemas, `src/gpm/exporters/{pack,hierarchy_layers}.py`,
  `docs/m21-hierarchy.md`, and `tests/test_m21_hierarchy.py`: implement and
  export stable province → area → region → superregion hierarchy.
- `src/gpm/tiles/{build,mvt,pmtiles_io}.py`, `src/gpm/release/demo.py`,
  `src/gpm/{cli,release/__init__}.py`, `src/gpm/exporters/atlas.py`, and the
  M19/M22 tests: generate deterministic native z0–7 PMTiles and the complete
  PMTiles-first demo contract.
- `landing/demo/data/*`: four global scenario PMTiles archives, sidecar
  manifests/legends, curated period assets, hero dissolves, hierarchy overlays,
  adjacency lines, lineage, and regenerated `demo-manifest.json`; legacy global
  scenario GeoJSON and sample adjacency files are deleted.
- `landing/{index.html,app.js,styles.css,vercel.json}` and
  `landing/demo/{index.html,demo.js,demo.css,README.md}`: expose the M22 global
  experience, inspector/layer controls, cache-busted entrypoints, manifest
  revalidation, and PMTiles caching.
- `src/gpm/qa/topology.py` and `tests/test_topology_qa.py`: repair a recoverable
  Natural Earth mask before complete coverage analysis.
- `README.md`, `ROADMAP.md`, `docs/{m14.5-landing,m20-broader-period-geometry,
  m23-density-design-note}.md`, and `tasks/{todo,roadmap,history}.md`: reconcile
  M20–M22 as complete and M23 as design-only.
- Remaining changed schemas, configs, samples, and tests are direct fixtures or
  contract coverage for the implementation groups above.

## User-goal mapping

- M20: multi-region period geometry and Europe multi-era sample.
- M21: stable four-level hierarchy and public overlays.
- M22: four PMTiles-only global scenarios, generated counts/assets, global UI,
  cache hardening, and deterministic rebuild command.
- Rollout safety: one release commit on `main`; preview first; no production
  promotion without explicit approval.

## Executable verification

- `uv run pytest`: 223 passed.
- Canonical generation: provinces → adjacency → hierarchy →
  `uv run gpm demo build --no-tippecanoe`.
- `uv run gpm release site --dry-run`: passed.
- Manifest/header integrity: 4,603 provinces; 660/169/8 hierarchy entities;
  10,781 edges; four native PMTiles archives at z0–7; no global scenario
  GeoJSON.
- Range-capable local browser smoke: 2 passed across desktop/mobile; four eras,
  paint/layer controls, modern disabling, period geometry, pan/zoom, and hero
  switcher exercised.
- `git diff --check`: passed. No file exceeds 95 MB.

## Skipped tests

- None before commit. Preview HTTP, deployed range responses, screenshots, and
  browser-console/network checks occur after Vercel creates the exact preview.

## Adversarial review

- Inspected the complete diff/stat and deletion boundary, searched textual
  changes for credential-like material, verified every manifest reference and
  PMTiles header, confirmed removed global GeoJSON is absent, and checked the
  GitHub per-file size limit.
- Confirmed `gpm demo build` preserves the curated M20 period-geometry assets
  rather than deriving them from the global M22 build.

## Residual risk

- Full topology QA completes but reports Natural Earth source conflicts: 577
  admin-1/admin-0 mask mismatches, five disputed-territory overlaps, 271
  islands/isolates, and fragmented global components. These are visible QA
  findings, not test regressions; M22 does not repair or adjudicate source
  borders.
- Native tiles intentionally stop at z7. Game-like density and deeper tiles are
  deferred to M23/future delivery work.

## Rollback note

The release is one commit. Before promotion, discard the preview. After an
approved promotion, Vercel can immediately promote the prior deployment; do
not rewrite the release commit in response to a deployment-only failure.

## Next command

`vercel deploy --yes` from `landing/`, followed by preview-only HTTP, range,
browser, screenshot, and hash validation.
