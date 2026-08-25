# M25C synthetic aggregate actor model revision

Status: **research complete; revision recommended; no remediation authorized**

Date: `2026-08-24`

## Named rejected record

Revise `scenario-chorotega-polities` (`Chorotega polities`) in region `013`.
The actor covers component `cmp-prv_4839d93e9052a93c9eff` and participates in
three rejected pairs: with the Lenca, Caribbean-coast Central American, and
Nicarao aggregates.

## Evidence and diagnosis

The regional generator does not use a 1444 Chorotega polygon. It first selects
modern Natural Earth Nicaragua and then assigns the actor when the component
centroid is at or north of latitude `13.2`. The packet nevertheless declares
the result an `actor_kind: polity`, even though the component has null
sovereign, owner, and controller fields, unknown authority, and only a
`territorial_presence` relationship.

The exact-source audit supplies a complete named-feature binding for the one
incident component, but its later generalized ethnolinguistic polygons name
Matagalpa, Silam, Ulva, Yosco, and Maribichicoa—not Chorotega. Because that
source begins in the sixteenth century and mixes later observations, it cannot
be projected back to `1444-11-11`. It does, however, independently demonstrate
that the current synthetic aggregate is not identical to the measurable source
surface.

## Recommendation

After independent review, replace the aggregate with
`scenario-northern-nicaragua-community-fabric-unresolved`, named `Northern
Nicaraguan community fabric (1444 identity unresolved)`. Set actor kind to
`community`; retain only uncertain `territorial_presence`; keep sovereignty,
ownership, control, and authority null or unknown; and mark the actor as
ineligible to imply a hard border.

The three incident pairs should become community-fabric transitions, not hard
border claims. This does not automatically make region `013` exempt from a
positive border: its full land-adjacent actor-pair inventory must be regenerated,
hash-bound, and independently reviewed under the existing applicability gate.

## Alternatives and tradeoffs

- Retain the Chorotega polity label: preserves a familiar name but keeps an
  exact actor and hard-border implication that the sources do not establish.
- Rename the actor to the Driver features: creates better later-map agreement
  by committing an explicit temporal anachronism.
- Remove human presence: avoids synthetic identity at the cost of treating
  uncertainty as evidence of an empty landscape.

## Expected QA impact and boundary

Immediate QA impact is zero because this is a decision packet only. No regional
packet, generator dispatch, canonical status, assembled artifact, finding,
tolerance, permission, or Task 17 state changes. If approved and implemented,
the three pair records would leave the hard-border candidate surface, but the
region-level finding remains fail-closed until the exhaustive applicability
review passes.

The reproducible packet is at
`research/start-dates/1444-global-v1/replacement-evidence/synthetic-actor-model-revision-v1/`.
