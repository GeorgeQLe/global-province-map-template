# M25C anomaly alignment decisions

## Scope

These decisions govern the canonical 1444-11-11 historical model. They are
intended for reuse by historical maps, map applications, and games. Canonical
history is not tailored to one game's province system: a consumer may project a
canonical entity as a province, city, holding, building, relationship, or map
symbol, but must retain canonical IDs and document any loss of spatial or
political detail.

The province is therefore not the canonical floor. Subprovince polities,
institutions, settlements, and relationships remain addressable even when a
consumer cannot draw them as independent polygons.

## Agreed historical treatments

| Case | Census treatment | Canonical treatment |
| --- | --- | --- |
| Andorra | Retain under the `condominium` review bucket with revised semantics | One distinct Andorran polity and territory; a co-principality with two concurrent co-sovereigns, not divided territory and not ordinary French or Spanish ownership. |
| Mount Athos | Retain as `non-state-territory` | Ottoman territorial sovereignty with an Athonite monastic community exercising durable internal self-government; not an internationally sovereign state. |
| Avignon and the Comtat Venaissin | Move from `enclave-exclave` to `detached-territory` | A papal detached territorial complex whose constituent identities remain separately addressable. Enclave or exclave is a geometry attribute, not the primary political class. |
| Burgundian realm | Retain as `composite-realm` | A dynastic composite monarchy under Philip the Good. Constituent territories retain their laws, estates, institutions, titles, succession rules, and their own external hierarchy relationships. |
| Calais and the Pale | Retain as `detached-territory` | The entire fortified English Pale, not the city alone; a crown possession with nested city, port, forts, and settlements. |
| Ceuta | Move from `disputed-area` to `detached-territory` | A Portuguese fortified overseas possession. The 1437 unfulfilled restitution agreement remains a historical diplomatic event, but the inspected evidence does not establish an active territorial dispute on 1444-11-11. |
| Galata/Pera | Retain under the `concession` review bucket with revised semantics | An autonomous commercial enclave: Byzantine territorial overlordship, Genoese administration, and the self-governing Commune of Pera under its podestà. It was not a fully independent state or ordinary Genoese sovereign territory. |
| Lancastrian claim to France | Remove from positive geographic anomalies | Retain as a canonical historical `claim` relationship from Henry VI's England to the French crown. It changes neither geometry nor actual territorial control; gameplay mechanics and claim overlays are consumer projections. |
| Lübeck | Retain as `free-protected-city` | An imperially immediate city polity directly subordinate to the Empire without an intermediate territorial lord. Hanseatic membership is a separate non-territorial association. |
| Madeira | Retain as `dependency` with revised semantics | A Portuguese overseas donatary territory under Prince Henry. Machico was formally granted in 1440; Funchal and Porto Santo were de facto administrations whose surviving formal grants postdate the start date. |
| San Marino | Retain as `microstate` | An independent communal republic using its pre-1463 Mount Titano territory. Modern borders and the 1463 acquisitions must not be backdated. |

## Census consequences

The review matrix remains exactly 22 regions by 11 search classes, or 242
cells. A class does not need a positive geographic case merely to remain a
required search class. After alignment, the tracked baseline contains ten
positive geographic anomaly records across nine positive cells:

- `claim`, `disputed-area`, and `enclave-exclave` remain required review classes
  but have no accepted geographic case in the current evidence set.
- The two Lancastrian regional `claim` cells conclude that the claim is
  historically supported but non-geographic and is retained in the gazetteer
  relationship layer.
- Ceuta's `disputed-area` cell concludes that an active 1444 dispute is not
  established; Ceuta moves to Northern Africa's `detached-territory` cell.
- Avignon moves into Western Europe's `detached-territory` cell alongside
  Calais; the `enclave-exclave` cell becomes a bounded negative conclusion.

George Le approved these treatments and the completed 242-cell evidence audit
on 2026-08-14. Acceptance is carried by the packet-only sidecar; the generated
inventory and frozen candidate status remain unsigned and non-public, and no
public release is authorized.
