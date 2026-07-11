# M17 Curation Workflow Hardening

M17 hardens the **continuous curation and community workflow** after multi-era
packs (M16): external scenario bundles, ownership diffs, expanded golden-border
suites, and a contribution checklist.

## Why

Curated politics cannot live only as in-repo JSON edited by maintainers:

- Community and SaaS curators need a **portable bundle** with license lineage
- Reviewers need **before/after diffs** (tag counts, contested provinces)
- Official eras need **golden borders**, not only min owner floors
- Scaffold ID / era-geometry revisions need a clear **deprecation policy**

## What shipped

| Artifact | Role |
| --- | --- |
| `gpm curation list\|validate\|import\|diff\|checklist` | CLI |
| `src/gpm/curation/` | Bundles, diffs, checklist |
| `schemas/curator-bundle.schema.json` | External bundle manifest |
| `schemas/scenario-diff-report.schema.json` | Ownership diff report |
| `schemas/golden-checks.schema.json` | Golden floors + borders contract |
| Expanded `gpm qa scenario` golden checks | M17 border suite |
| `samples/curator-bundle-example/` | Community bundle template |

## External curator bundles

A bundle is a directory:

```
my-bundle/
  bundle_manifest.json
  scenarios/<scenario-id>.json
  golden/<scenario-id>.json      # optional but recommended
  README.md                      # recommended
```

### Manifest fields

| Field | Required | Purpose |
| --- | --- | --- |
| `bundle_id` | yes | Stable id (`^[a-z0-9][a-z0-9._-]*$`) |
| `display_name` | yes | Human label |
| `license` | yes | SPDX or short license name for bundle contents |
| `scenarios[]` | yes | `scenario_id`, `path`, optional `golden_path` |
| `source_lineage` | recommended | Where politics claims came from |
| `license_lineage` | recommended | License chain for review |
| `checklist` | recommended | Self-attested PR fields |
| `deprecation` | optional | Pin / supersede policy |

Paths in the manifest must be **relative** and must not contain `..`.

### Commands

```bash
uv run gpm curation list
uv run gpm curation validate --bundle samples/curator-bundle-example
uv run gpm curation import \
  --bundle samples/curator-bundle-example \
  --output-dir /tmp/community-bundle
uv run gpm curation checklist --bundle samples/curator-bundle-example
```

Import copies the tree and writes `import_manifest.json` for inventory.

Bundles are discovered under `samples/`, `bundles/`, and `curator_bundles/`
(when present), or by explicit path.

## Ownership diffs

```bash
uv run gpm curation diff \
  --base-scenario modern-baseline \
  --target-scenario official-1836 \
  --province-input data/processed/provinces.geojson \
  --report-output data/processed/scenarios/diff-1836.json

# Or compare two ownership tables without re-resolve
uv run gpm curation diff \
  --base-ownership data/processed/scenarios/modern-baseline/ownership.csv \
  --target-ownership data/processed/scenarios/official-1836/ownership.csv
```

### Diff report contents

- **Status:** `identical` or `changed`
- **Owner / controller / disputed** change counts
- **Added / removed** province IDs
- **Owner count deltas** (tag → base/target/delta)
- **Contested provinces** (disputed or claim changes)
- **Change list** (per-province field-level before/after)

Schema: `schemas/scenario-diff-report.schema.json`.

Use diffs in PR review to summarize politics edits without eyeballing full
scenario JSON.

## Golden-border suites

`gpm qa scenario` already loads
`configs/scenarios/golden/<scenario-id>.json` when present. M17 extends the
golden document:

| Key | Severity on fail | Meaning |
| --- | --- | --- |
| `province_owners` | error | Province must have exact owner (M11) |
| `min_owner_counts` | error | Owner must own ≥ N provinces (M11) |
| `max_owner_counts` | error | Owner must own ≤ N provinces |
| `required_owners` | error | Tag must appear at least once |
| `forbidden_owners` | error | Tag must not appear |
| `disputed_provinces` | error | Province disputed flag must match |
| `border_pairs` | error | Specific province pair owners (+ optional adjacency) |
| `owner_adjacencies` | error | Min land/strait edges between two owner tags |

### Example

```json
{
  "schema_version": "0.1.0",
  "scenario_id": "official-1836",
  "min_owner_counts": { "FRA": 40, "PRU": 5 },
  "max_owner_counts": { "TEX": 50 },
  "required_owners": ["BEL", "TEX"],
  "forbidden_owners": ["GER"],
  "province_owners": {
    "ne_example-abc": "FRA"
  },
  "disputed_provinces": {
    "ne_example-disputed": true
  },
  "border_pairs": [
    {
      "left_province_id": "ne_left",
      "right_province_id": "ne_right",
      "left_owner": "FRA",
      "right_owner": "PRU",
      "require_adjacent": true
    }
  ],
  "owner_adjacencies": [
    {
      "owner_a": "FRA",
      "owner_b": "PRU",
      "min_shared_edges": 1
    }
  ]
}
```

Border checks that need adjacency emit
`GOLDEN_BORDER_ADJACENCY_SKIPPED` warnings when adjacency input is missing
(same default path as politics QA: `data/processed/adjacency.csv`).

Schema: `schemas/golden-checks.schema.json`.

### New finding codes

| Code | Severity |
| --- | --- |
| `GOLDEN_MAX_COUNT_FAILED` | error |
| `GOLDEN_REQUIRED_OWNER_MISSING` | error |
| `GOLDEN_FORBIDDEN_OWNER` | error |
| `GOLDEN_DISPUTED_MISMATCH` | error |
| `GOLDEN_BORDER_OWNER_MISMATCH` | error |
| `GOLDEN_BORDER_NOT_ADJACENT` | error |
| `GOLDEN_OWNER_ADJACENCY_FAILED` | error |
| `GOLDEN_BORDER_ADJACENCY_SKIPPED` | warning |

## Community contribution path

### PR checklist (scenario / bundle)

1. **Sources documented** — `source_lineage` on scenario and/or bundle
2. **Licenses reviewed** — `license` + `license_lineage`; no GADM / proprietary maps
3. **No restricted sources** — checklist attests public path is clean
4. **Golden present** — floors and/or famous borders for the PR scope
5. **QA pass** — `gpm qa scenario` (and topology if geometry touched)
6. **Diff attached** — `gpm curation diff` against the base scenario when changing politics
7. **Honest quality tier** — do not claim `period-geometry` without an era-geometry pack

### Automated checklist

```bash
uv run gpm curation checklist --bundle path/to/bundle
uv run gpm curation checklist --bundle path/to/bundle --require-qa-claimed
```

Hard failures: invalid manifest/scenarios, missing license/sources, missing
golden, missing `no_restricted_sources`.  
`qa_pass_claimed` is a **warning** unless `--require-qa-claimed`.

### Deprecation policy (scaffold / era IDs)

1. **Do not silently rewrite** published scenario tags when province IDs change
2. **Pin** the scaffold (or multi-era pack version) the politics were authored on
3. **Supersede** with a new `bundle_id` / scenario revision and set
   `deprecation.superseded_by` on the old bundle
4. Prefer **`scaffold_province_id`** as the long-lived join key when using
   era-geometry lineage (see M15/M16 migration notes)
5. Game mods and SaaS consumers should **pin pack/scenario versions** in their
   own manifests; corrections ship as new versions

## Recommended curator workflow

```bash
# 1. Author or import a bundle / edit a scenario
uv run gpm curation validate --bundle samples/curator-bundle-example

# 2. Resolve + QA with golden suite
uv run gpm scenario build \
  --scenario-path samples/curator-bundle-example/scenarios/community-demo-1444.json \
  --province-input samples/beta-license-audited/sample/provinces.geojson
uv run gpm qa scenario \
  --scenario community-demo-1444 \
  --scenario-path samples/curator-bundle-example/scenarios/community-demo-1444.json \
  --golden samples/curator-bundle-example/golden/community-demo-1444.json \
  --province-input samples/beta-license-audited/sample/provinces.geojson

# 3. Diff against baseline for PR notes
uv run gpm curation diff \
  --base-scenario modern-baseline \
  --target-scenario-path samples/curator-bundle-example/scenarios/community-demo-1444.json \
  --province-input samples/beta-license-audited/sample/provinces.geojson

# 4. Checklist before open PR
uv run gpm curation checklist --bundle samples/curator-bundle-example
```

Optional review authoring remains `gpm review --scenario` (M11).

## Relation to other milestones

| Milestone | Relation |
| --- | --- |
| M11 | Politics QA + review authoring; basic golden floors |
| M12–M13 / M16 | Official era scenarios and multi-era packs |
| **M17** | External bundles, diffs, golden borders, contribution path |
| Later | Culture/religion paint in demo, PMTiles, SaaS tile endpoints |

## Honest limits

- Diffs are **table-level**, not rendered map images (report is choropleth-ready)
- Golden `border_pairs` need **stable province IDs** in the active scaffold
- Community bundles are **not** automatically trusted for official-era marketing
- License audit for public beta releases remains `gpm release beta` (M14)
- Culture & religion fields already flow through ownership; dedicated atlas paint
  UI is still a reserved demo slot
