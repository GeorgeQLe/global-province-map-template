# M25A and Public Reset Ship Manifest

## User goal

Wrap up and publish the current session: complete the M25A historical hard-case
contract, make the public release Modern-only until worldwide certification,
preserve 1444-v2 as research evidence, and leave M25B as the active next task.

## Changed files and per-file purpose

- `schemas/historical-territory-status.schema.json`,
  `src/gpm/historical/{__init__.py,casebook.py}`, `src/gpm/schemas.py`,
  `tests/fixtures/m25a/casebook.json`,
  `tests/test_historical_certification_contract.py`, and
  `tests/test_source_manifest_schema.py`: define and execute the M25A canonical
  identity, typed-status, geometry, deterministic fixture projection, visual,
  picking, LOD, adjacency, and save/migration contract.
- `docs/m25-hard-case-casebook.md`, `README.md`, `ROADMAP.md`,
  `docs/m24-start-date-research-framework.md`, and
  `docs/m25-1444-reconstruction.md`: document the hard-case rules, worldwide
  official-era bar, M25A/M25B/M25C sequence, and five-region pilot boundary.
- `src/gpm/release/{demo.py,site.py}`, `landing/{app.js,index.html}`,
  `landing/demo/{README.md,demo.js,index.html}`,
  `landing/demo/data/demo-manifest.json`, `tests/test_m14_5_landing.py`,
  `tests/test_m15_era_geometry.py`, `tests/test_m16_multi_era.py`, and
  `tests/test_m22_demo_build.py`: make demo generation, static copy, controls,
  manifests, and fail-closed release validation Modern-only.
- Deleted public historical assets:
  `landing/demo/data/{boundary-hints-1444.geojson,boundary-hints-1836.geojson,boundary-hints-1936.geojson,hero-official-1444.geojson,hero-official-1836.geojson,hero-official-1936.geojson,lineage-1444.json,lineage-1836.json,lineage-1936.json}`;
  for each of 1444, 1836, and 1936, deleted the corresponding
  `official-ERA.pmtiles`, `official-ERA.tileset.json`,
  `official-ERA.legend.json`, `official-ERA.culture.legend.json`,
  `official-ERA.religion.legend.json`, `official-ERA-period.geojson`,
  `official-ERA-period.legend.json`,
  `official-ERA-period.culture.legend.json`, and
  `official-ERA-period.religion.legend.json`.
- `src/gpm/qa/render.py`, `scripts/build-m25-v2-pass.py`,
  `tests/test_m25_v2_contract.py`,
  `research/start-dates/1444-v2/{pass_manifest.json,start_date_qa.json}`,
  `research/start-dates/1444-v2/review/{central-europe.svg,france.svg,review_manifest.json}`:
  adapt review framing to historical evidence when province bounds are extreme,
  invalidate stale review identities before rerendering, and repin the generated
  evidence and hashes.
- `tasks/{todo.md,roadmap.md,history.md,m25a-ship-manifest.md}`: record M25A as
  complete, make M25B active, capture the session, and preserve the exact ship
  evidence and continuation route.

All tracked worktree changes and listed untracked files belong to this coherent
shipping boundary. No unrelated user changes are excluded. Generated
`.codex/skills/**` and `.claude/skills/**` roots are unchanged and are not part
of the commit.

## User-goal mapping

- M25A completion maps to the schema, executable casebook, fixtures, tests, and
  casebook documentation.
- Public-claim honesty maps to the Modern-only generator/UI/assets, worldwide
  certification validator, and roadmap/documentation reset.
- Reproducible research preservation maps to the adaptive renderer, review
  invalidation step, regenerated SVGs, QA evidence, and pinned hashes.
- Clean continuation maps to task/history reconciliation and M25B routing.

## Tests run

- `uv run pytest`: 296 passed in 15.59 seconds; zero failures and no warnings.
- `git diff --check`: passed.
- Range-capable local static-server smoke (`npx serve -l 8765 landing`) plus
  headless Chromium screenshots: landing rendered a single Modern hero; demo
  rendered only the Modern control and the worldwide-certification placeholder;
  PMTiles returned HTTP 206.
- Direct screenshot inspection of
  `research/start-dates/1444-v2/review/central-europe.svg`: historical evidence
  remained legible in the adaptive main frame and the modern negative control
  remained isolated in its inset.
- Credential-pattern scan across changed source, documentation, research,
  schema, landing, task, and test files: clear. A preliminary binary-patch scan
  produced one coincidental GitHub-token-prefix byte sequence from binary diff
  encoding; no current changed file contains that token pattern.

## Skipped tests

- No lint, typecheck, or build command is configured in `pyproject.toml`, and
  the repository has no Makefile, Justfile, Node package scripts, Cargo config,
  or other declared validation command. The full executable pytest suite is the
  configured verification surface.
- An authenticated production browser smoke was not run because this repository
  has no `deploy.md` or `tasks/deploy.md` manual deploy contract. Local HTTP 206
  delivery and contract tests cover the changed public bundle before its normal
  hosting path picks up `main`.

## Adversarial review

- Used a failure-oriented changed-file review plus targeted scans as the
  quality-sweep equivalent because no configured `quality-sweep` or
  `expert-review` lane is installed. Reviewed identity/reference closure,
  disconnected-province rules, deterministic sorting, stale-review reset,
  renderer outlier and forbidden-modern behavior, public-asset deletion, custom
  scenario behavior, manifest certification enforcement, and stale UI controls.
- Confirmed historical configs and samples remain available outside the public
  landing directory, while default demo regeneration deletes stale public
  historical files.
- Confirmed dormant period-geometry code in `landing/demo/demo.js` has no public
  control or manifest entry and cannot expose an era through the shipped UI;
  the site validator independently rejects uncertified live manifest entries.
- No blocking finding remained after the review. Headless Chromium emitted GPU
  readback performance messages only while capturing screenshots; the range
  server returned the PMTiles request successfully with HTTP 206.

## Residual risk

- The local headless screenshot captured the demo while its asynchronous map
  status still read `Loading`; HTTP 206 delivery succeeded and the full demo
  contract tests passed, but the first hosted smoke after `main` updates should
  confirm that the production CDN completes the Modern PMTiles render.
- The M25A geometry and evidence IDs are intentionally synthetic contract
  fixtures. They prove representation behavior, not historical correctness or
  worldwide coverage; M25C-M28 remain responsible for evidence-backed global
  certification.

## Rollback note

Revert the session commit on `main` without rewriting history. This restores the
prior public historical assets and roadmap state together; regenerate the demo
and 1444-v2 review artifacts afterward so manifests and hashes match the
restored implementation.

## Next command

`$exec` for the active M25B game runtime compiler and reference pack.
