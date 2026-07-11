# M11 Scenario Politics QA + Review Authoring

M11 adds **automated ownership checks** for scenario politics and extends the
interactive review viewer with **scenario choropleth layers** and **curator
province-override authoring**.

Geometry is still never rewritten. Politics remain curated tables over the
modern scaffold (M8); M11 makes those tables CI-gatable and editable in review.

## Commands

```bash
uv run gpm qa scenario --scenario modern-baseline
uv run gpm qa scenario --scenario demo-1444 --golden path/to/golden.json
uv run gpm review --scenario demo-1444
uv run gpm review --scenario-path configs/scenarios/demo-1444.json
```

### `gpm qa scenario`

Resolves (or loads) ownership for one scenario and writes a politics QA report.

| Path | Contents |
| --- | --- |
| `data/processed/scenarios/<id>/politics_qa.json` | Default report (override with `--report-output`) |

Options:

- `--scenario` id under `configs/scenarios/` (required unless using path only)
- `--scenario-path` explicit scenario JSON
- `--province-input` land province GeoJSON (default `data/processed/provinces.geojson`)
- `--adjacency-input` adjacency CSV for owner-component checks (optional; missing skips with warning)
- `--ownership-input` pre-built ownership CSV/JSON (skip re-resolve)
- `--golden` optional golden check JSON (defaults to
  `configs/scenarios/golden/<scenario-id>.json` when present)
- `--report-output` report path
- `--allow-unknown-overrides` when resolving from definition
- `--max-owner-components` fragment threshold (default 25)
- `--min-provinces-for-fragment-check` (default 8)
- `--format text|json`

Exit code is `0` when `status == pass`, else `1` (errors present). Warnings alone
do not fail CI.

### `gpm review --scenario`

Same MapLibre review UI as M5, plus:

- Ownership joined onto provinces (owner / controller / assignment colors)
- Politics QA findings list and dashed overlays
- Inspector ownership panel
- Curator form that writes `province_overrides` into the scenario JSON

## Politics QA checks

| Code | Severity | Meaning |
| --- | --- | --- |
| `MISSING_OWNERSHIP_ROW` | error | Land province has no ownership row |
| `EXTRA_OWNERSHIP_ROW` | error | Ownership row for unknown/non-land id |
| `DUPLICATE_OWNERSHIP_ROW` | error | Multiple rows for one province |
| `MISSING_OWNER` / `MISSING_CONTROLLER` | error | Empty owner or controller |
| `MALFORMED_OWNERSHIP_ROW` | error | Row missing province_id |
| `UNKNOWN_OWNER_TAG` / `UNKNOWN_CONTROLLER_TAG` / `UNKNOWN_CORE_TAG` / `UNKNOWN_CLAIM_TAG` | warning | Tag used but not in `scenario.countries` (only when the catalog is non-empty) |
| `ORPHAN_CORE` / `ORPHAN_CLAIM` | warning | Core/claim tag never appears as an owner |
| `UNK_OWNER` | warning | One or more provinces owned by `UNK` |
| `FRAGMENT_OWNER_COMPONENTS` | warning | Owner has many disconnected land/strait components |
| `ADJACENCY_ANALYSIS_SKIPPED` | warning | No adjacency file; fragment checks skipped |
| `GOLDEN_OWNER_MISMATCH` | error | Province owner ≠ golden expectation |
| `GOLDEN_MIN_COUNT_FAILED` | error | Owner province count below golden minimum |
| `GOLDEN_CONFIG_INVALID` | error | Malformed golden file |

Unknown-tag checks are **skipped when `countries` is empty** (as in
`modern-baseline`), so modern ISO scaffold tags are not spammed as unknown.

### Golden check file

Optional JSON for famous borders / tag floors:

```json
{
  "province_owners": {
    "ne_example-abc123def456": "FRA"
  },
  "min_owner_counts": {
    "FRA": 10,
    "ENG": 5
  }
}
```

## Review authoring

When review starts with `--scenario` or `--scenario-path`:

1. Ownership is resolved live from the definition + province geometry.
2. Politics QA is run into `…/scenarios/<id>/politics_qa.json` beside the
   province input when possible.
3. Selecting a land province shows ownership and an edit form.
4. **Save override** `POST /api/scenario/override` upserts a
   `province_overrides` entry and rewrites the scenario JSON.
5. **Remove override** `DELETE /api/scenario/override` deletes that entry.
6. Ownership and politics QA refresh in-session after each write.

Color modes added for politics: **Owner**, **Controller**, **Assignment
source**, **Politics QA**.

### Local server API (M11 additions)

| Path | Method | Payload |
| --- | --- | --- |
| `/api/ownership.json` | GET | Resolved ownership rows + colors |
| `/api/politics-qa.json` | GET | Politics QA report wrapper |
| `/api/scenario` | GET | Active scenario definition |
| `/api/scenarios` | GET | Bundled scenario list |
| `/api/scenario/override` | POST | Upsert province override |
| `/api/scenario/override` | DELETE | Remove province override |
| `/api/province/{id}` | GET | Also returns `ownership` and `politics_findings` |

## Recommended workflow

```bash
uv run gpm build provinces
uv run gpm build adjacency
uv run gpm scenario build --scenario demo-1444
uv run gpm qa scenario --scenario demo-1444
uv run gpm review --scenario demo-1444
# edit overrides in the UI, then re-validate:
uv run gpm qa scenario --scenario demo-1444
uv run gpm export pack --scenario demo-1444
uv run gpm export atlas --scenario demo-1444
```

## Schema

`schemas/scenario-politics-qa-report.schema.json` describes the report.
`gpm.schemas.validate_scenario_politics_qa_report` checks core invariants.

## Relation to later milestones

| Milestone | Adds |
| --- | --- |
| M12 | First official era `official-1836` (`curated-politics`) — complete |
| M13 | Second official era (`official-1444`) using these gates |
| M14 | License-audited beta (game + atlas faces) — complete |
| M15–M16 | Period geometry and multi-era packs |
| M17 | Diffs, golden-border suites, external curator bundles — complete |
