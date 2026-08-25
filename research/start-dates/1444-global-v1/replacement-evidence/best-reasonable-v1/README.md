# M25C best-reasonable supplemental evidence

Status: **research complete; pending independent review; not implemented**

This packet supplies an explicit best-available attempt for every one of the
43 deferred frozen findings. It binds all 180 nonzero actor-pair records and
all 512 previously uncovered or overlapping corridor-component records to
three supplemental surfaces:

- Historical Basemaps snapshots for 1400 and 1492, pinned to commit
  `62d8f1a03a71f2d3ff17f2d166f7553f256bce68`. These are approximate,
  bracketing cultural/political zones, not exact 1444 borders.
- An OpenHistoricalMap `admin_level=2` query evaluated at `1444-11-11`.
  Individual OHM features count as stronger corroboration only when their own
  source tags and dates pass review.
- The reviewed, date-relevant regional source records already pinned in each
  regional packet. These provide historical context but are not silently
  treated as component-specific geometry.

## Files

- `pair-evidence.json` contains one hash-bound record for every exact actor
  pair and its complete incident-component inventory.
- `component-evidence.json` contains one hash-bound record for every deferred
  corridor component, including exact current values, representative point,
  spatial matches, confidence, and limitations.
- `finding-routes.json` maps all 43 deferred findings to the exact pair or
  component records needed for review.
- `manifest.json` pins sources, frozen inputs, output hashes, counts, and the
  non-implementation boundary.

## Interpretation

`medium` means the row has either source-tagged exact-date OHM corroboration or
named matches in both bracketing Historical Basemaps snapshots. `low` means
only one approximate snapshot, unnamed geometry, or regional context is
available. Neither label is approval.

The reasonable completion policy is deliberately asymmetric: approximate
evidence may support a frontier zone, non-territorial applicability decision,
or documented Grade-B/C reconstruction. It cannot support surveyed precision
or a gap-free Grade-A claim. Independent review must decide every record before
any serial implementation.

## Reproduction

Download the exact pinned external inputs, reproduce the OHM query in
`manifest.json`, verify their SHA-256 values, and run:

```bash
.venv/bin/python scripts/generate-m25c-best-reasonable-evidence.py \
  --historical-1400 /path/to/world_1400.geojson \
  --historical-1492 /path/to/world_1492.geojson \
  --ohm-snapshot /path/to/ohm-1444-geom.json
```

No regional packet, assembled artifact, tolerance, permission, or Task 17
state is changed by this research packet.
