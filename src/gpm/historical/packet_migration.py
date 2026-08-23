"""Conservative packet-to-compositional-status migration shared by generators."""

from __future__ import annotations

import json
from typing import Any


STATE_TOKENS = ("state", "kingdom", "empire", "sultanate", "emirate", "khanate", "caliphate", "duchy", "republic", "principality", "crown", "administration", "sultanates", "dynasty", "county", "bishopric", "papal", "electorate", "margraviate")
MOBILE_TOKENS = ("mobile", "pastoral", "nomad", "forager", "transhum")
COMMUNITY_TOKENS = ("communit", "village", "clan", "iwi", "hapu", "peoples", "fabric", "woodland", "riverine", "puebloan")


def actor_kind(polity_id: str, name: str) -> str:
    text = f"{polity_id} {name}".casefold()
    if "uninhabited" in text:
        return "unknown"
    if any(token in text for token in MOBILE_TOKENS):
        return "mobile_community"
    if "chiefdom" in text or "chieftain" in text:
        return "chiefdom"
    if "city" in text and any(token in text for token in ("network", "league", "cities")):
        return "city_network"
    if "network" in text or any(token in text for token in COMMUNITY_TOKENS):
        return "community"
    if any(token in text for token in STATE_TOKENS):
        return "state"
    return "polity"


def facets_for(kind: str, *, uninhabited: bool = False) -> dict[str, str]:
    if uninhabited:
        return {"habitability": "uninhabitable", "population_presence": "none", "settlement_pattern": "none", "tenure": "none", "authority": "none"}
    if kind == "state":
        return {"habitability": "habitable", "population_presence": "resident", "settlement_pattern": "nucleated", "tenure": "polity_associated", "authority": "administered"}
    if kind == "mobile_community":
        return {"habitability": "habitable", "population_presence": "seasonal", "settlement_pattern": "mobile", "tenure": "customary_community", "authority": "local_decentralized"}
    if kind in {"community", "chiefdom", "city_network"}:
        settlement = "nucleated" if kind in {"chiefdom", "city_network"} else "dispersed"
        return {"habitability": "habitable", "population_presence": "resident", "settlement_pattern": settlement, "tenure": "customary_community", "authority": "local_decentralized"}
    return {dimension: "unknown" for dimension in ("habitability", "population_presence", "settlement_pattern", "tenure", "authority")}


def migrate_packet(packet: dict[str, Any]) -> dict[str, Any]:
    result = json.loads(json.dumps(packet))
    names = {row["polity_id"]: row.get("name", "") for row in result.get("polities", [])}
    kinds = {polity_id: actor_kind(polity_id, name) for polity_id, name in names.items()}
    used: set[str] = set()
    actor_sources: dict[str, set[str]] = {}
    removed = 0
    for row in result.get("assignment_overrides", []):
        if row.pop("_preserve_reviewed_compositional_status", False):
            for relationship in row.get("status_relationships") or []:
                actor = relationship["actor_political_unit_id"]
                used.add(actor)
                actor_sources.setdefault(actor, set()).update(row["source_ids"])
            continue
        actors = [value for value in (row.get("owner_polity_id"), row.get("controller_polity_id"), row.get("sovereign_polity_id")) if value]
        actor = actors[0] if actors else (row.get("polity_ids") or [None])[0]
        if actor is None and row.get("status_relationships"):
            actor = row["status_relationships"][0].get("actor_political_unit_id")
        uninhabited = bool(actor and "uninhabited" in actor.casefold()) or (row.get("facets") or {}).get("habitability") == "uninhabitable"
        kind = kinds.get(actor, actor_kind(str(actor or ""), names.get(actor, "")))
        row["facets"] = facets_for(kind, uninhabited=uninhabited)
        row["status_relationships"] = []
        if uninhabited:
            removed += 1
            row.update({"sovereign_polity_id": None, "owner_polity_id": None, "controller_polity_id": None, "polity_ids": [], "core_polity_ids": [], "claim_polity_ids": [], "dispute_polity_ids": []})
            continue
        if actor is None:
            row.update({"sovereign_polity_id": None, "owner_polity_id": None, "controller_polity_id": None})
            row["facets"] = facets_for("polity")
            continue
        used.add(actor)
        actor_sources.setdefault(actor, set()).update(row["source_ids"])
        base = {"actor_political_unit_id": actor}
        if kind == "state":
            row["status_relationships"] = [{"relationship": relationship, **base} for relationship in ("sovereign", "owner", "controller")]
        else:
            row.update({"sovereign_polity_id": None, "owner_polity_id": None, "controller_polity_id": None, "core_polity_ids": [], "claim_polity_ids": [], "dispute_polity_ids": []})
            relationships = ["territorial_presence"]
            if kind == "mobile_community": relationships.append("seasonal_use")
            if kind in {"community", "mobile_community", "chiefdom", "city_network"}: relationships.append("customary_tenure")
            row["status_relationships"] = [{"relationship": relationship, **base} for relationship in relationships]
    migrated_polities = []
    for polity in result.get("polities", []):
        polity_id = polity["polity_id"]
        if "uninhabited" in polity_id.casefold():
            continue
        polity["actor_kind"] = kinds[polity_id]
        polity.setdefault("territory_component_ids", [])
        migrated_polities.append(polity)
    profiled = {row["polity_id"] for row in migrated_polities}
    for polity_id in sorted(used - profiled):
        kind = actor_kind(polity_id, "")
        migrated_polities.append({"polity_id": polity_id, "name": polity_id.replace("-", " ").title(), "actor_kind": kind, "territory_component_ids": [], "aliases": [], "capital_location_ids": [], "relationships": [], "source_ids": sorted(actor_sources[polity_id]), "valid_from": "1400", "valid_to": "1500"})
    migrated_polities.sort(key=lambda row: row["polity_id"])
    result["polities"] = migrated_polities
    result["expected_counts"]["polities"] = len(migrated_polities)
    result.update({"packet_version": "2.0.0", "territorial_status_schema_version": "0.2.0", "location_assignment_schema_version": "0.4.0", "compatibility_revision": "2"})
    result["territorial_status_migration"] = {"policy": "conservative-compositional-v1", "uninhabited_pseudo_owner_rows_removed": removed, "actor_profiles": len(migrated_polities)}
    return result
