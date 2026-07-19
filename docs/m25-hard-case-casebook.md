# M25A Historical Hard-Case Casebook

M25A is the prerequisite for worldwide era production. It proves the canonical
and runtime representation of difficult historical territory before M25C–M28
scale the same contract globally. A regional casebook result is a research
artifact, not an official-era release.

## Identity and representation contract

- `territory_component_id` identifies one connected polygon, including each
  individual enclave fragment.
- `political_unit_id` groups components with the same documented political
  status. Territorial identity remains separate from dynastic, imperial, and
  personal-union relationships.
- `province_id` is a gameplay aggregation. Disconnected components may share a
  province only when sources identify one administrative unit and every typed
  political status matches.
- Status rows type sovereignty and power as `sovereign`, `owner`, `controller`,
  `protector`, `co-administrator`, `occupier`, `mandate-authority`, `lessee`, or
  `claimant`. A condominium therefore has one geometry and multiple typed
  administrators rather than a false single owner.
- Historically required components are exempt from minimum-area merging. If the
  current fabric cannot paint one, the case requires an evidence-backed split
  and fabric-revision migration.
- Microterritories retain exact polygon geometry and at least one independently
  addressable province. A low-zoom symbol may supplement, never replace, the
  polygon.

The machine-readable row contract is
`schemas/historical-territory-status.schema.json`.

The executable synthetic casebook is
`tests/fixtures/m25a/casebook.json`. `gpm.historical.casebook` validates the
canonical rows and executes every declared interaction surface. Its coordinates
are deliberately synthetic unit geometry: case names describe the semantic
hard case being exercised, not accepted historical boundary evidence.

## Required case matrix

| Class | Illustrative cases | Representation test |
| --- | --- | --- |
| Sovereign microstate | Monaco, Andorra, San Marino, Vatican City | Exact polygon; independently addressable province |
| Detached sovereign territory | Papal Avignon / Comtat | Fabric split; sovereignty distinct from surrounding modern country |
| Foreign enclave / exclave | Calais, Baarle fragments | Every connected component retained; no cross-border merge |
| Free / protected city | Kraków, Danzig | Separate political unit plus typed protector/guarantor relationships |
| Condominium / international zone | Neutral Moresnet, Tangier | One geometry with multiple typed administrators |
| Composite / dynastic territory | Burgundian possessions, HRE estates | Polity and territorial identity separated from union/imperial relationships |
| Dependency / mandate / concession | Protectorates, mandates, leases | Sovereignty, administration, control, occupation, and claims distinguished |
| Disputed territory | Conflicting frontiers or control | Evidence-backed geometry plus competing claims; uncertainty is not invented away |

Use multiple examples whenever two cases share geometry but differ in legal or
political semantics. Starting references include the Belgian State Archives on
[Neutral Moresnet](https://www.arch.be/index.php?e=neutral-moresnet.-eine-territoriale-eigenheit-in-belgien-von-1816-bis-1919&l=de&m=neuigkeiten&r=referate),
UN League of Nations records on [Danzig](https://www.un.org/unispal/document/auto-insert-210766/),
and German History in Documents and Images on the [German Confederation](https://germanhistorydocs.org/en/from-vormaerz-to-prussian-dominance-1815-1866/central-europe-1815-1866).

## Per-class acceptance suite

Every class above must have schema, canonical-build, runtime-pack, visual,
picking, LOD, adjacency, and save/migration tests. Tests must show that two
clean runtime compilations are byte-identical and preserve component,
political-unit, province, status, and migration mappings.

For M25A, `runtime-pack` means the deterministic fixture projection exercised by
the casebook harness. The projection is stamped
`m25a-fixture-projection-not-runtime-pack`; it proves the mappings that M25B
must consume but is not the M25B compiler or a distributable pack. Visual tests
materialize one polygon feature per component, picking resolves declared points,
LOD simplification must retain every polygon, adjacency is recomputed from
shared boundaries, and saved province IDs must resolve through the declared
migration map.

The executable matrix covers all four target-era slots:

| Era slot | Executable hard cases |
| --- | --- |
| 1444 | San Marino microstate; detached Papal Avignon; Calais fragments; composite Burgundian possessions |
| 1836 | protected Free City of Kraków; Neutral Moresnet condominium |
| 1914 | Jiaozhou leased concession |
| 1936 | Vilnius disputed territory |

These are representation fixtures only. Historical dates and semantics still
require source-backed regional research before use in an era pass.

## Global era certification gate

For one exact start date, certification requires all of the following:

- complete worldwide polity and territorial-anomaly inventory;
- every documented microstate, exclave, condominium, dependency, concession,
  and disputed territory represented;
- no known contradictory modern administrative outline;
- date-valid, licensed sources and independently reviewed geometry;
- source-derived tolerances fixed before measurement;
- zero unresolved geometry-evidence gaps—missing precise evidence blocks the
  release;
- complete ownership, control, and typed-status coverage; and
- passing topology, adjacency, negative-anachronism, and canonical/runtime
  cross-validation.

The public-site validator must keep Modern as the only visible era until the
manifest points to a worldwide certification artifact with accepted research
and runtime status.
