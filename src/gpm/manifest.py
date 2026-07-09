from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import __version__
from .paths import RAW_DATA_DIR
from .sources.adapters.base import BaseSourceAdapter
from .sources.artifacts import (
    SourceArtifact,
    inspect_local_source_artifacts,
    source_manifest_record,
)
from .sources.registry import resolve_source_adapters


def build_planned_source_manifest(
    profile_id: str,
    source_ids: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Build a no-download manifest preview for the selected profile."""
    adapters = resolve_source_adapters(profile_id, source_ids)
    return _manifest_document(
        profile_id,
        manifest_type="planned",
        sources=[adapter.manifest_record() for adapter in adapters],
    )


def build_downloaded_source_manifest(
    profile_id: str,
    adapters: Iterable[BaseSourceAdapter],
    artifacts_by_source: dict[str, tuple[SourceArtifact, ...]],
) -> dict[str, Any]:
    """Build a manifest from artifacts returned by the downloader."""
    sources = []
    for adapter in adapters:
        artifacts = artifacts_by_source.get(adapter.source_id, ())
        sources.append(source_manifest_record(adapter, artifacts))
    return _manifest_document(profile_id, manifest_type="build", sources=sources)


def build_local_source_manifest(
    profile_id: str,
    source_ids: Iterable[str] | None = None,
    *,
    raw_dir: Path = RAW_DATA_DIR,
) -> dict[str, Any]:
    """Build a manifest by hashing artifacts already present under raw_dir."""
    adapters = resolve_source_adapters(profile_id, source_ids)
    sources = [
        source_manifest_record(adapter, inspect_local_source_artifacts(adapter, raw_dir=raw_dir))
        for adapter in adapters
    ]
    return _manifest_document(profile_id, manifest_type="build", sources=sources)


def _manifest_document(profile_id: str, *, manifest_type: str, sources: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "0.1.0",
        "manifest_type": manifest_type,
        "build": {
            "profile_id": profile_id,
            "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
            "generator_version": __version__,
        },
        "sources": sources,
    }
