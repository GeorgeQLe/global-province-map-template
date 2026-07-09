from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from . import __version__
from .sources.registry import resolve_source_adapters


def build_planned_source_manifest(
    profile_id: str,
    source_ids: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Build a no-download manifest preview for the selected profile."""
    adapters = resolve_source_adapters(profile_id, source_ids)

    return {
        "schema_version": "0.1.0",
        "manifest_type": "planned",
        "build": {
            "profile_id": profile_id,
            "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
            "generator_version": __version__,
        },
        "sources": [adapter.manifest_record() for adapter in adapters],
    }
