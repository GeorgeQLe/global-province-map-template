# M8 Historical Scenario Proof of Concept

M8 layers **political ownership** on top of the **modern geographic scaffold**.
Province polygons stay the same; scenarios write owner/controller/cores/claims
tables as curated overrides rather than baking historical borders into
geometry.

## Commands

```bash
uv run gpm scenario list
uv run gpm scenario validate --scenario modern-baseline
uv run gpm scenario build --scenario modern-baseline
uv run gpm scenario build --scenario demo-1444 --profile eu-like
uv run gpm export pack --scenario modern-baseline --scenario demo-1444
```

### `gpm scenario list`

Lists JSON definitions under `configs/scenarios/`.

### `gpm scenario validate`

Validates schema invariants for a scenario id (or `--scenario-path`) without
reading province geometry.

### `gpm scenario build`

Resolves one ownership row per **land** province and writes:

| Path | Contents |
| --- | --- |
| `data/processed/scenarios/<id>/ownership.csv` | Flat ownership table |
| `data/processed/scenarios/<id>/ownership.json` | Same rows as JSON |
| `data/processed/scenarios/<id>/countries.json` | Tags used + display names |
| `data/processed/scenarios/<id>/scenario_manifest.json` | Counts, lineage, files |

Options:

- `--scenario` id under `configs/scenarios/` (required unless using path only)
- `--scenario-path` explicit JSON file
- `--province-input` land province GeoJSON (default `data/processed/provinces.geojson`)
- `--output-dir` override output root
- `--profile` generation profile (validates profile exists; advisory for
  `generation.historical_overrides`)
- `--allow-unknown-overrides` ignore `province_overrides` whose ids are absent
- `--format text|json` summary format

Sea features (`kind = sea`) are skipped. Missing province input fails with exit
code 1.

### Export embedding

```bash
uv run gpm export pack --scenario modern-baseline --scenario demo-1444
```

Copies resolved scenario trees under `exports/<profile>/scenarios/<id>/`. Pack
manifests with scenarios set `milestone` to `M8`.

## Assignment precedence

Each land province starts from the modern scaffold, then rules apply in order.
**Later layers win field-by-field.**

1. **Baseline** — `owner = controller = parent_country_id`, `cores = [parent_country_id]`.
   Missing country becomes `UNK`.
2. **Country rules** — match `parent_country_id`.
3. **Region rules** — match `parent_region_id`.
4. **Province overrides** — match exact `province_id`.

Scenario `defaults` supply default culture/religion/disputed when not set by a
rule. Setting `owner` without `controller` also updates controller to the new
owner.

`assignment_source` on each row records which layer last applied:
`baseline`, `country_rule`, `region_rule`, or `province_override`.

## Scenario definition format

Bundled examples:

- `configs/scenarios/modern-baseline.json` — pure baseline projection
- `configs/scenarios/demo-1444.json` — coarse 1444-style country/region remaps
- `configs/scenarios/official-1836.json` — official curated-politics 1836 era
  (see [m12-1836.md](m12-1836.md))

Minimal shape:

```json
{
  "schema_version": "0.1.0",
  "scenario_id": "demo-1444",
  "label": "Demo 1444-style ownership overlay",
  "era": "1444",
  "start_date": "1444-11-11",
  "end_date": null,
  "description": "...",
  "countries": {
    "FRA": { "display_name": "France", "tag": "FRA" }
  },
  "defaults": {
    "culture": null,
    "religion": null,
    "disputed": false
  },
  "country_rules": [
    {
      "match_parent_country_id": "FRA",
      "owner": "FRA",
      "controller": "FRA",
      "cores": ["FRA"],
      "culture": "french",
      "religion": "catholic"
    }
  ],
  "region_rules": [
    {
      "match_parent_region_id": "FR-HDF",
      "owner": "BUR",
      "controller": "BUR",
      "cores": ["BUR", "FRA"]
    }
  ],
  "province_overrides": [
    {
      "province_id": "ne_example-abc123def456",
      "owner": "ENG",
      "controller": "ENG",
      "cores": ["ENG", "FRA"],
      "claims": ["FRA"],
      "disputed": true,
      "notes": "Curated occupation"
    }
  ]
}
```

Contracts live in:

- `schemas/scenario-definition.schema.json`
- `schemas/scenario-ownership-record.schema.json`

## Ownership record fields

| Field | Meaning |
| --- | --- |
| `province_id` | Stable land province id from the geographic scaffold |
| `scenario_id` | Scenario this row belongs to |
| `start_date` / `end_date` | Scenario validity window |
| `owner` | Political owner tag |
| `controller` | Military/occupying controller tag |
| `cores` | Core tags (JSON array in CSV) |
| `claims` | Claim tags (JSON array in CSV) |
| `culture` / `religion` | Optional gameplay hints |
| `disputed` | Boolean disputed status |
| `assignment_source` | Which rule layer last wrote the row |
| `parent_country_id` / `parent_region_id` | Modern scaffold parents (debug/join) |
| `display_name` | Province display name at build time |
| `notes` | Curator notes from the winning rule |

## Authoring workflow

1. Generate modern provinces (`gpm build provinces`, optional seas/adjacency).
2. Copy a scenario JSON under `configs/scenarios/` or pass `--scenario-path`.
3. Prefer bulk `country_rules` / `region_rules` for coarse eras.
4. Pin exceptions with `province_overrides` using real generated `province_id`s.
5. `gpm scenario validate` then `gpm scenario build`.
6. Optionally embed with `gpm export pack --scenario <id>`.

Do **not** fork province geometry per era. Keep one scaffold and many scenario
tables.

## What this POC is not

- Not a complete 1444/1836/1936 historical dataset
- Not OpenHistoricalMap ingestion (still optional future source work)
- Not date-ranged multi-row history per province (one row per province per
  scenario for now)
- Not culture/religion population microsimulation

`demo-1444` intentionally uses coarse modern-admin remaps for pedagogy. For the
first official curated era, use `official-1836` (M12) rather than treating demo
remaps as production politics.

## Profile flag

Profiles may set `generation.historical_overrides = true` (eu-like,
victoria-like, hoi-like). That flag is advisory documentation for intended use;
`gpm scenario build` accepts any valid profile.
