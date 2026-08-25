# Synthetic aggregate actor model revision v1

This decision packet revises one named rejected actor model without claiming
new historical geometry. `scenario-chorotega-polities` is currently a `polity`
assigned to one component by a modern Nicaragua plus latitude heuristic. Its
three incident actor pairs are therefore treated as candidate hard borders by
the replacement-evidence surface.

The exact-source pass does not corroborate that identity. Its later Driver
binding names Matagalpa, Silam, Ulva, Yosco, and Maribichicoa features, not
Chorotega. That binding is useful as evidence that the aggregate label is not
source-identical; it is not a valid source for 1444 geometry.

The recommended model replaces the territorial polity aggregate with
`scenario-northern-nicaragua-community-fabric-unresolved`, actor kind
`community`, linked only by uncertain `territorial_presence`. Ownership,
control, sovereignty, and authority remain null or unknown. Its three incident
transitions must not imply hard borders.

This is research, not remediation. The regional packet, generator, assembled
artifact, QA counts, tolerances, permissions, and Task 17 state are unchanged.
Even after approval, this one actor revision cannot qualify region 013: a
complete hash-bound land-adjacency audit and independent review are still
required.

Reproduce with:

```bash
.venv/bin/python scripts/generate-m25c-synthetic-actor-model-revision.py
.venv/bin/pytest -q tests/test_m25c_synthetic_actor_model_revision.py
```
