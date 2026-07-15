# M24 Acceptance Audit

Date: 2026-07-13
Verdict: **PASS — zero blocking findings**

This audit covers the uncommitted M24 implementation against
`docs/m24-start-date-research-framework.md`. It does not certify any M25
historical reconstruction or real-world research data.

## Acceptance matrix

| Requirement | Contract / implementation | Adversarial evidence | Result |
|---|---|---|---|
| Independently releasable pass | `start-date-pass-manifest.schema.json`; `validate_start_date_pass_manifest` | exact nine-role artifact table; unexpected roles and duplicate paths rejected | Pass |
| Version and checksum pins | manifest `artifact_version`, artifact record versions, SHA-256; `run_start_date_qa` | version/revision/checksum mismatch tests | Pass |
| Safe pass containment | `_contained_path`; symlink and duplicate-path gates | traversal, internal symlink, malformed/missing artifact tests | Pass |
| Research dossier | required Scope, Research Questions, Citations, Transformations and Conflicts, Exclusions, and Uncertainty headings | incomplete and unreadable dossier gates | Pass |
| Source lineage | `start-date-source-manifest.schema.json`; reviewed-source checks | duplicate/unknown/unreviewed source and checksum-shape coverage | Pass |
| Dated boundary registry | `historical-boundary-registry.schema.json`; temporal and side-polity checks | invalid ranges, unknown sources/polities, equal sides, invalid geometry | Pass |
| Polity/dependency gazetteer | `polity-gazetteer.schema.json`; typed relationships and capital references | duplicate IDs, relationship source/target/date, unknown capital tests | Pass |
| Location assignments/splits | `start-date-location-assignments.schema.json`; fabric pin and evidence references | duplicate assignment/location/request IDs, unknown polity/source/location tests | Pass |
| Full-build geometry | required `full_build_geometry` artifact; revision and SHA-256 pins | missing province, invalid/duplicate feature, wrong type/revision tests | Pass |
| Golden definitions | `spatial-golden-borders.schema.json`; no input status/measurement | unsupported relation/unit/cardinality/type mutations rejected | Pass |
| Executed spatial QA | `border_matches_boundary_hausdorff_lte`, `capital_within_subject`, `forbidden_outline_overlap_ratio_lte` in `gpm.qa.start_date` | adjacent polygons, dated frontier, capital point, forbidden outline, and failing geometry mutation | Pass |
| Priority-region gates | positive border, positive capital, and negative-anachronism definitions required per priority region | missing/failing assertion paths fail the pass | Pass |
| Coverage certification | `start-date-coverage.schema.json`; source/assertion IDs tied to the same region/layer and computed result | A evidence mismatch; B/C missing gaps; U certification claim | Pass |
| Changelog | `start-date-changelog.schema.json`; pass-version match | schema and version mismatch tests | Pass |
| QA report | `start-date-qa-report.schema.json`; computed `assertion_results` and finding-count invariants | deterministic repeated output and schema mutation tests | Pass |
| CLI compatibility | `gpm qa start-date --pass-dir <path>` | installed-wheel valid exit 0 and invalid exit 1 smoke tests | Pass |
| Draft 2020-12 schemas | all nine M24 schemas; `jsonschema` runtime dependency | `Draft202012Validator.check_schema` plus schema/validator mutation parity | Pass |
| Distribution | setuptools data-files and package discovery | wheel contains all nine schemas and `gpm/qa/start_date.py`; clean-venv execution outside source tree | Pass |

## Verification record

- `uv run pytest -q` — **256 passed**.
- Focused M24 suite — **18 passed**, including deterministic output and
  table-driven failure cases.
- `git diff --check` — passed.
- `uv build --out-dir /tmp/gpm-m24-dist` — sdist and wheel built successfully.
- Wheel inspection — all nine M24 schemas and `gpm/qa/start_date.py` present.
- Clean `/tmp/gpm-m24-venv` install — valid miniature pass returned exit 0;
  checksum-invalid pass returned exit 1 and did not certify.
- Repository build artifacts — no new repository-local build artifacts were
  left by verification (build outputs were written under `/tmp`).

## Blocking findings

None.

## M25 boundary

M25 must supply actual 1444 research data and the Brussels/Nord regression.
Those historical claims and datasets are intentionally outside M24 acceptance.
