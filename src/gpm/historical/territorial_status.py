"""Compositional territory-state derivation and fail-closed scenario overlays."""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any, Iterable

from gpm.schemas import SchemaValidationError, TERRITORIAL_FACETS, derive_province_facets, load_schema, validate_historical_territory_status


class TerritorialStatusOverlayError(ValueError):
    """Raised when an overlay is stale, ambiguous, or cannot be applied exactly."""


def load_territorial_status_overlay(path: Path | str) -> dict[str, Any]:
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TerritorialStatusOverlayError(f"cannot load territorial-status overlay {path}: {exc}") from exc
    validate_territorial_status_overlay(document)
    return document


def validate_territorial_status_overlay(document: dict[str, Any]) -> None:
    from gpm.schemas import _validate_json_schema
    try:
        _validate_json_schema(document, load_schema("territorial-status-overlay"), "territorial status overlay")
    except SchemaValidationError as exc:
        raise TerritorialStatusOverlayError(str(exc)) from exc
    seen: set[str] = set()
    for operation in document["operations"]:
        if operation["op"] == "set_facet":
            identity = json.dumps([operation["op"], operation["target_kind"], operation["target_id"], operation["dimension"]])
            _validate_facet_value(operation["dimension"], operation["value"])
        else:
            relation = operation["relationship"]
            identity = json.dumps([operation["op"], operation["target_kind"], operation["target_id"], relation["relationship"], relation["actor_political_unit_id"]])
        if identity in seen:
            raise TerritorialStatusOverlayError(f"duplicate overlay operation: {operation}")
        seen.add(identity)


def resolve_territorial_status(canonical: dict[str, Any], overlays: Iterable[dict[str, Any] | Path | str] = ()) -> dict[str, Any]:
    """Apply documents in caller order; province operations precede component operations."""
    overlay_list = list(overlays)
    validate_historical_territory_status(canonical)
    if canonical.get("schema_version") != "0.2.0":
        if overlay_list:
            raise TerritorialStatusOverlayError("overlays require canonical historical-status schema 0.2.0")
        return copy.deepcopy(canonical)
    resolved = copy.deepcopy(canonical)
    applied: list[dict[str, Any]] = []
    for raw in overlay_list:
        overlay = load_territorial_status_overlay(raw) if isinstance(raw, (str, Path)) else copy.deepcopy(raw)
        validate_territorial_status_overlay(overlay)
        if str(overlay["base_compatibility_revision"]) != str(canonical["compatibility_revision"]):
            raise TerritorialStatusOverlayError(f"overlay {overlay['overlay_id']} targets compatibility revision {overlay['base_compatibility_revision']}, not {canonical['compatibility_revision']}")
        operations = [row for row in overlay["operations"] if row["target_kind"] == "province"]
        operations += [row for row in overlay["operations"] if row["target_kind"] == "component"]
        for operation in operations:
            _apply_operation(resolved, operation, overlay)
        resolved["scenario_id"] = overlay["scenario_id"]
        applied.append({"overlay_id": overlay["overlay_id"], "scenario_id": overlay["scenario_id"], "provenance": overlay["provenance"]})
    if applied:
        resolved["applied_overlays"] = applied
    validate_historical_territory_status(resolved)
    return resolved


def resolved_territory_state(canonical: dict[str, Any]) -> dict[str, Any]:
    """Return inspectable component states and facets derived at province level."""
    validate_historical_territory_status(canonical)
    relationships: dict[str, list[dict[str, Any]]] = {}
    for row in canonical["statuses"]:
        relationships.setdefault(row["subject_id"], []).append(copy.deepcopy(row))
    components = []
    for row in sorted(canonical["components"], key=lambda item: item["territory_component_id"]):
        actors = {name: None for name in ("sovereign", "owner", "controller")}
        for relation in relationships.get(row["territory_component_id"], []):
            if relation["relationship"] in actors:
                actors[relation["relationship"]] = relation["actor_political_unit_id"]
        components.append({"territory_component_id": row["territory_component_id"], "province_id": row["province_id"], "political_unit_id": row.get("political_unit_id"), "facets": copy.deepcopy(row.get("facets", {})), **actors, "relationships": sorted(relationships.get(row["territory_component_id"], []), key=_relationship_sort_key)})
    province_facets = derive_province_facets(canonical) if canonical.get("schema_version") == "0.2.0" else {}
    provinces = [{"province_id": row["province_id"], "facets": province_facets.get(row["province_id"], {}), "territory_component_ids": list(row["territory_component_ids"])} for row in sorted(canonical["provinces"], key=lambda item: item["province_id"])]
    return {"scenario_id": canonical.get("scenario_id") or canonical["start_date"], "components": components, "provinces": provinces}


def _apply_operation(document: dict[str, Any], operation: dict[str, Any], overlay: dict[str, Any]) -> None:
    components = {row["territory_component_id"]: row for row in document["components"]}
    provinces = {row["province_id"]: row for row in document["provinces"]}
    if operation["target_kind"] == "province":
        province = provinces.get(operation["target_id"])
        if province is None:
            raise TerritorialStatusOverlayError(f"unknown province target: {operation['target_id']}")
        targets = list(province["territory_component_ids"])
    else:
        if operation["target_id"] not in components:
            raise TerritorialStatusOverlayError(f"unknown component target: {operation['target_id']}")
        targets = [operation["target_id"]]
    for component_id in targets:
        if operation["op"] == "set_facet":
            components[component_id]["facets"][operation["dimension"]] = operation["value"]
            components[component_id].setdefault("facet_provenance", {})[operation["dimension"]] = {"overlay_id": overlay["overlay_id"], "provenance": copy.deepcopy(overlay["provenance"])}
            continue
        candidate = {"subject_id": component_id, **copy.deepcopy(operation["relationship"])}
        if operation["op"] == "remove_relationship":
            matches = [row for row in document["statuses"] if all(row.get(key) == value for key, value in candidate.items())]
            if len(matches) != 1:
                raise TerritorialStatusOverlayError(f"relationship removal did not match exactly one existing row: {candidate}")
            document["statuses"].remove(matches[0])
        else:
            identity = (component_id, candidate["relationship"], candidate["actor_political_unit_id"])
            document["statuses"] = [row for row in document["statuses"] if (row["subject_id"], row["relationship"], row["actor_political_unit_id"]) != identity]
            candidate["overlay_provenance"] = {"overlay_id": overlay["overlay_id"], "provenance": copy.deepcopy(overlay["provenance"])}
            document["statuses"].append(candidate)
    document["statuses"].sort(key=_relationship_sort_key)


def _extension(value: str) -> bool:
    return re.fullmatch(r"x-[a-z0-9][a-z0-9-]*:[a-z0-9][a-z0-9_.-]*", value) is not None


def _validate_facet_value(dimension: str, value: str) -> None:
    allowed = {"habitability": {"habitable", "marginal", "uninhabitable", "unknown"}, "population_presence": {"none", "transient", "seasonal", "resident", "mixed", "unknown"}, "settlement_pattern": {"none", "mobile", "semi_mobile", "dispersed", "nucleated", "mixed", "unknown"}, "tenure": {"none", "customary_community", "polity_associated", "shared", "contested", "unknown"}, "authority": {"none", "local_decentralized", "tributary_influence", "administered", "occupied", "shared", "contested", "unknown"}}
    if dimension not in allowed and not _extension(dimension):
        raise TerritorialStatusOverlayError(f"unsupported facet dimension: {dimension}")
    if dimension in allowed and value not in allowed[dimension] and not _extension(value):
        raise TerritorialStatusOverlayError(f"unsupported {dimension} value: {value}")
    if dimension not in allowed and not (_extension(value) or re.fullmatch(r"[a-z0-9][a-z0-9_.-]*", value)):
        raise TerritorialStatusOverlayError(f"invalid namespaced facet value: {dimension}={value}")


def _relationship_sort_key(row: dict[str, Any]) -> tuple[str, ...]:
    return (str(row.get("subject_id", "")), str(row.get("relationship", "")), str(row.get("actor_political_unit_id", "")), str(row.get("valid_from", "")), str(row.get("valid_to", "")))
