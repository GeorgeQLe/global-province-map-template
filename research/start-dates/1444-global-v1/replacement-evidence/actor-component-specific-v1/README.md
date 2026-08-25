# M25C actor/component-specific full-geometry evidence

Status: **research complete; pending independent review; not implemented**

This packet strengthens the evidence for the 32 ordinary-QA routes that remain
rejected after the best-reasonable review. It replaces representative-point
inference with full-polygon measurements against the exact pinned Cliopatria
1444 source slice, aggregates those measurements over each current actor's
complete component inventory, and binds the result to all 180 rejected actor
pairs and all 32 rejected finding routes.

## Result

- All 206 previously rejected components are measured in full.
- 187 components have zero intersection with any Cliopatria 1444 polity.
- 19 components have only minor source overlap; none reaches 50% coverage and
  the maximum is `0.411179697`.
- The 180 pair records cover 107 exact current actors. All 180 remain
  insufficient: no pair has distinct source-zone support of at least 50% on
  both actor sides, and geometry alone cannot establish actor identity.
- The 32 finding routes remain pending independent review and unimplemented.

The result is stronger negative evidence. It rules out the possibility that
the earlier representative-point method merely missed broad Cliopatria
coverage, but it does not supply the missing actor-to-citation claims,
component coverage, or independently derived border linework.

## Files

- `component-specific-evidence.json` records exact full-polygon source
  intersections, geodesic areas, coverage ratios, current actors, and prior
  rejection hashes for all 206 rejected components.
- `actor-specific-evidence.json` aggregates the complete assembled component
  inventory for each of the 107 actors involved in rejected pairs.
- `pair-specific-evidence.json` binds both actor records and the exact incident
  components for all 180 rejected pairs.
- `finding-routes.json` binds the stronger records back to every remaining
  rejected ordinary-QA route.
- `manifest.json` pins all source, assembled, prior-evidence, and review inputs
  plus every generated artifact.

## Decision boundary

Spatial overlap does not prove that a synthetic current actor is identical to
a Cliopatria polity. Cliopatria's approximately `0.07°` smoothing and
unquantified historical-border uncertainty also cannot establish exact
linework or Grade-A precision. No regional packet, assembled artifact,
tolerance, permission, or Task 17 state changes in this research step.

Reproduce and verify with:

```bash
.venv/bin/python scripts/generate-m25c-actor-component-evidence.py
.venv/bin/pytest -q tests/test_m25c_actor_component_evidence.py
```
