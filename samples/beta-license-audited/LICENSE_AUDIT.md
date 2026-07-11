# License audit

**Status:** PASSED  
**Profile:** `modern-small`  
**Channel:** `beta`  
**Errors:** 0 · **Warnings:** 0

## Policy

- Public beta may only ship core-path sources with public-safe postures.
- ODbL / share-alike databases stay on optional-isolated paths.
- Restricted sources (e.g. GADM) stay excluded unless permission is obtained.
- Every redistributed feature must carry license_lineage.

## Public path sources

- `geoboundaries`
- `natural_earth`

## Isolated / restricted (not in public pack)

- `gadm` (restricted)
- `open_historical_map` (isolated)
- `openstreetmap` (isolated)

### Isolation notes

- gadm: restricted — excluded from public releases (Restricted non-commercial/academic use).
- open_historical_map: isolated/optional path — posture `review-per-feature` (Mostly CC0, with per-feature exceptions). Not mixed into public beta packs.
- openstreetmap: isolated/optional path — posture `share-alike-database` (ODbL). Not mixed into public beta packs.

## Feature lineage observed

### license_lineage

- Natural Earth public domain

### source_lineage

- `natural_earth:admin1_states_provinces`
- `natural_earth:land`

## Findings

- **INFO** `isolation-policy-documented`: Restricted and share-alike sources are documented for isolation and excluded from the public beta path.

## Attribution pack

See `attribution.json` for machine-readable redistribution notices.
Isolation notices document excluded paths; they are not redistributable layers.
