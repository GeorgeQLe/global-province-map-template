# M25C worldwide replacement-evidence packet

Status: **pending independent review; no candidate input is changed**

This directory accounts for all 56 ordinary-QA errors on the frozen assembled
candidate and exposes each underlying regional evidence decision separately.
It is a research packet before Task 17, not an accepted pass, implementation,
or release artifact.

## Independent source

The new geometry source is Bennett et al.'s peer-reviewed Cliopatria dataset
from the Seshat Global History Databank, version `v0.2.0`, pinned at commit
`ad28a691b7c07c1fca89d0e0636d324667d2a258`. The source is CC BY 4.0 and
publishes native EPSG:4326 polity polygons with inclusive `FromYear` and
`ToYear` ranges. The extracted snapshot contains exactly the 144 records whose
range includes 1444, so `1444-11-11` is inside every selected record.

- Data archive SHA-256:
  `d01ae3a20d358cc5d54f69d9d725d390767d9c8759ac89ad6f90c58d106f3370`
- Unpacked GeoJSON SHA-256:
  `5df3b5868cfab8f76030853fa2346ed3cd71171ad807b6f72d783ee2dce6839e`
- Method paper and citation: Bennett et al., *Scientific Data* 12, 247 (2025),
  <https://doi.org/10.1038/s41597-025-04516-9>
- License: <https://creativecommons.org/licenses/by/4.0/>
- Exact source revision:
  <https://github.com/Seshat-Global-History-Databank/cliopatria/tree/ad28a691b7c07c1fca89d0e0636d324667d2a258>

The paper documents hand reconstruction from cited historical maps, specialist
regional references, subsequent Seshat review, EPSG:4326 output, roughly
`0.07°` smoothing, and unquantified residual historical-border uncertainty.
Those limitations are retained in every dossier. The proposed `20 km` budget
is deliberately conservative and is itself a reviewer decision.

## Review surfaces

- `manifest.json` pins the source, six frozen candidate inputs, every generated
  artifact, all 18 region dossiers, and the unchanged 56-error baseline.
- `cliopatria-1444.geojson` is the deterministic, unmodified 1444 source slice.
- `direct-border-candidates.geojson` contains eight exact shared-boundary
  intersections for regions `014`, `015`, `030`, `034`, `035`, `039`, `143`,
  and `145`. Neither candidate geometry nor a modern negative control selects
  these lines.
- `applicability-review-candidates.json` contains ten schema-valid, unsigned,
  hash-bound proposals. It enumerates every component and every current
  land-adjacent cross-actor pair for `005`, `011`, `013`, `017`, `018`, `021`,
  `029`, `053`, and `054`; `061` independently reproduces 183 components and
  zero cross-actor land pairs.
- `regions/*.json` maps every component within the fixed 75 km control corridor
  to its current values and its exact Cliopatria representative-point result.
  All 56 frozen findings occur in exactly one dossier.

## Approval boundary

The source, error budget, eight direct borders, ten applicability records, and
each component mapping are separate decisions. A source polygon's silence is
not treated as proof of an empty or ungoverned landscape. Accordingly, rows
classified `outside_cliopatria_polity_coverage` or `overlapping_polities` may
not authorize an edit without an explicit reviewer disposition.

Approval still would not mutate packets automatically. Approved decisions must
be implemented serially, then reproduced against affected, neighboring, and
ordinary worldwide QA. Task 17 remains closed until that implementation yields
zero non-review errors.

## Reproduction

After downloading and unzipping the pinned source archive outside the tracked
tree:

```bash
.venv/bin/python scripts/generate-m25c-replacement-evidence.py \
  --cliopatria-input /path/to/cliopatria_polities_only.geojson
```

The generator refuses any unpacked source whose SHA-256 differs from the pin.
