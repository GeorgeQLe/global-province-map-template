# M25C actor/component-specific evidence for remaining ordinary-QA blockers

Status: **research complete; pending independent review; no remediation authorized**

Date: `2026-08-24`

## Goal and scope

Test whether the 32 routes rejected by the best-reasonable review were an
artifact of representative-point sampling, and provide the exact actor- and
component-specific evidence required before any further remediation decision.
The frozen decision surface is 206 rejected components, 180 rejected pairs,
107 actors, and 32 rejected finding routes.

## Method

The generator intersects each exact assembled component polygon with every
`POLITY` polygon in the checksum-pinned Cliopatria v0.2.0 1444 slice. Areas are
measured geodesically on a sphere. It then:

1. records every nontrivial source intersection and union coverage ratio for
   each rejected component;
2. aggregates the complete assembled component inventory for every actor in a
   rejected pair, retaining named source-polity, Seshat, Wikidata, and feature
   hashes;
3. compares the dominant source zones for each exact actor pair; and
4. binds those records back to all remaining finding routes and prior review
   hashes.

The packet is at
`research/start-dates/1444-global-v1/replacement-evidence/actor-component-specific-v1/`.

## Evidence result

Full geometry does not rescue the rejected records:

- 187 of 206 rejected components have zero Cliopatria polity coverage;
- 19 have minor overlap between `0.011761928` and `0.411179697`;
- zero rejected components reach 50% coverage;
- only eight of the 107 pair-surface actors have any source coverage at all;
- none of the 180 pairs has distinct source-zone support at or above 50% on
  both sides.

The 19 partial intersections occur in regions `011`, `013`, `015`, `034`,
`035`, `143`, and `145`. They are retained record by record, including cases
where the source polity conflicts with the current actor. They are not rounded
up into a component or pair approval.

## Recommendation and alternatives

Recommendation: retain all 32 routes fail-closed. The next useful research
must introduce sources that make explicit claims about the exact current actor
and cover the exact affected component or independently derive the needed
line. Repeating point, centroid, or broad regional-citation matching against
the current three source surfaces will not address the observed gaps.

Alternatives considered:

- Treat any overlap as Grade C: rejected because every newly observed overlap
  is below 50% and some contradict the current actor label.
- Infer actor identity from spatial agreement: rejected because geometry does
  not establish historical entity identity.
- Use source polygon edges as positive borders: rejected because the source's
  smoothing and uncertainty do not establish the exact actor-pair line.
- Mark uncovered areas non-territorial: rejected because source silence is not
  evidence of an empty or ungoverned landscape.

## Expected QA impact and implementation boundary

Expected immediate QA impact is zero. The assembled candidate remains at 56
non-review errors plus one pending-review warning, with every permission false.
No packet, status, geometry, assertion, tolerance, assembled artifact, or
release state is changed. Independent review is required before any serial
implementation, and the evidence currently supports no implementation route.

Task 17 remains closed.

## Verification

```bash
.venv/bin/python scripts/generate-m25c-actor-component-evidence.py
.venv/bin/pytest -q \
  tests/test_m25c_actor_component_evidence.py \
  tests/test_m25c_best_reasonable_evidence.py \
  tests/test_m25c_replacement_evidence.py
```
