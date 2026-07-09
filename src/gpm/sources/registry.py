from __future__ import annotations

import importlib
from collections.abc import Iterable
from typing import Any

from gpm.config import default_source_ids, load_profile, load_source_catalog
from gpm.sources.adapters.base import BaseSourceAdapter, SourceDefinition


class SourceRegistryError(ValueError):
    """Raised when source adapter resolution cannot continue."""


class RestrictedSourceError(SourceRegistryError):
    """Raised when a restricted source is selected without an override."""


def list_source_definitions() -> list[SourceDefinition]:
    definitions = []
    for source_id, source in load_source_catalog().items():
        definitions.append(_definition_from_catalog(source_id, source))
    return definitions


def resolve_source_adapters(
    profile_id: str,
    requested_source_ids: Iterable[str] | None = None,
) -> list[BaseSourceAdapter]:
    profile = load_profile(profile_id)
    catalog = load_source_catalog()
    selected_ids = list(requested_source_ids) if requested_source_ids is not None else default_source_ids(profile)
    if not selected_ids:
        raise SourceRegistryError("At least one source must be selected.")

    adapters: list[BaseSourceAdapter] = []
    for source_id in selected_ids:
        source = catalog.get(source_id)
        if source is None:
            available = ", ".join(sorted(catalog))
            raise SourceRegistryError(f"Unknown source '{source_id}'. Available sources: {available}.")
        definition = _definition_from_catalog(source_id, source)
        adapters.append(_load_adapter(definition))
    return adapters


def _definition_from_catalog(source_id: str, source: dict[str, Any]) -> SourceDefinition:
    return SourceDefinition(
        id=source_id,
        name=source["name"],
        source_url=source.get("source_url"),
        license=source["license"],
        license_posture=source["license_posture"],
        attribution_text=source["attribution_text"],
        adapter=source.get("adapter") or None,
        layers=tuple(source.get("layers", [])),
        enabled_by_default=bool(source["enabled_by_default"]),
        eligible_for_default_build=bool(source["eligible_for_default_build"]),
        optional=bool(source["optional"]),
        isolated=bool(source["isolated"]),
        restricted=bool(source["restricted"]),
    )


def _load_adapter(definition: SourceDefinition) -> BaseSourceAdapter:
    if definition.restricted:
        raise RestrictedSourceError(
            f"Source '{definition.id}' is restricted and cannot be planned by M1 without an explicit override."
        )
    if not definition.adapter:
        raise SourceRegistryError(f"Source '{definition.id}' does not have an M1 adapter configured.")

    module = importlib.import_module(definition.adapter)
    create_adapter = getattr(module, "create_adapter", None)
    if create_adapter is None:
        raise SourceRegistryError(f"Adapter module '{definition.adapter}' does not expose create_adapter().")
    adapter = create_adapter(definition)
    if not isinstance(adapter, BaseSourceAdapter):
        raise SourceRegistryError(f"Adapter module '{definition.adapter}' returned an invalid adapter.")
    return adapter
