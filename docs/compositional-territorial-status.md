# Compositional territorial status

Canonical historical-status `0.2.0` does not equate population or assignment
coverage with nation-state ownership. Every territory component records five
independent facets: habitability, population presence, settlement pattern,
tenure, and authority. Political actors have an `actor_kind`; component primary
actors and sovereign/owner/controller relationships are nullable. Province
facets are derived from their components and become `mixed` when values differ.

Namespaced extensions use `x-<namespace>:<value>` for both dimensions and
values. Unnamespaced free-form dimensions or values are rejected.

Downstream scenarios use `territorial-status-overlay` documents. Pass them in
order with repeated `gpm export runtime --overlay <path>` options. Later
documents win. Within a document, province operations expand to components
before component operations, so component edits remain the most specific.
Unknown targets, stale compatibility revisions, duplicate operations, and
non-exact removals fail closed. Overlay provenance is retained in the resolved
canonical state.

Runtime packs compiled from canonical v2 use runtime schema `2.0.0`. Facets and
their scenario deltas are stored separately from actor relationships, and the
component table uses `0xffffffff` as the nullable-actor sentinel. `RuntimePack`
adds `scenario_facets()` and `resolved_territory_state()`; `scenario_statuses()`
continues to expose actor relationships. Runtime schema `1.0.0` remains readable
without behavior changes.

Atlas choropleths preserve null owner/controller values, use neutral gray for
unowned territory, expose the five facets as properties, and exclude null
owners from owner dissolves.
