from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import PurePosixPath
from typing import Any


@dataclass(frozen=True)
class PlannedLayer:
    id: str
    description: str


@dataclass(frozen=True)
class SourceDefinition:
    id: str
    name: str
    source_url: str | None
    license: str
    license_posture: str
    attribution_text: str
    adapter: str | None
    layers: tuple[str, ...]
    enabled_by_default: bool
    eligible_for_default_build: bool
    optional: bool
    isolated: bool
    restricted: bool


@dataclass(frozen=True)
class PlannedDownload:
    source_id: str
    artifact_id: str
    layer_id: str
    url: str
    expected_path: str
    version: str | None
    original_format: str | None
    license: str
    attribution_text: str
    default: bool
    optional: bool
    isolated: bool
    restricted: bool

    @property
    def default_build(self) -> bool:
        return self.default

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_manifest_artifact(self) -> dict[str, Any]:
        return {
            "id": self.artifact_id,
            "layer_id": self.layer_id,
            "status": "planned",
            "url": self.url,
            "path": self.expected_path,
            "access_date": None,
            "version": self.version,
            "original_format": self.original_format,
            "bytes": None,
            "checksum": None,
        }


@dataclass(frozen=True)
class AdapterDescription:
    source_id: str
    display_name: str
    planned_layers: tuple[PlannedLayer, ...]
    license: str | None = None
    license_posture: str | None = None
    attribution_text: str | None = None


class BaseSourceAdapter:
    planned_layers: tuple[PlannedLayer, ...] = ()

    def __init__(self, definition: SourceDefinition) -> None:
        self.definition = definition
        self._validate_catalog_layers()

    @property
    def source_id(self) -> str:
        return self.definition.id

    @property
    def display_name(self) -> str:
        return self.definition.name

    def describe(self) -> AdapterDescription:
        return AdapterDescription(
            source_id=self.source_id,
            display_name=self.display_name,
            license=self.definition.license,
            license_posture=self.definition.license_posture,
            attribution_text=self.definition.attribution_text,
            planned_layers=self.planned_layers,
        )

    def planned_downloads(self) -> tuple[PlannedDownload, ...]:
        raise NotImplementedError

    def manifest_record(self) -> dict[str, Any]:
        downloads = self.planned_downloads()
        return {
            "id": self.source_id,
            "name": self.display_name,
            "status": "planned",
            "source_url": self.definition.source_url,
            "access_date": None,
            "version": _summarize_values(download.version for download in downloads),
            "original_format": _summarize_values(download.original_format for download in downloads),
            "checksum": None,
            "license": self.definition.license,
            "attribution_text": self.definition.attribution_text,
            "default_build": bool(self.definition.enabled_by_default),
            "optional": bool(self.definition.optional),
            "isolated": bool(self.definition.isolated),
            "restricted": bool(self.definition.restricted),
            "enabled": True,
            "layers": [layer.id for layer in self.planned_layers],
            "artifacts": [download.to_manifest_artifact() for download in downloads],
            "transformation_steps": [],
            "downstream_files": [],
        }

    def _download(
        self,
        layer_id: str,
        url: str,
        expected_path: str,
        *,
        artifact_id: str | None = None,
        version: str | None = None,
        original_format: str | None = None,
    ) -> PlannedDownload:
        if not expected_path.startswith("data/raw/"):
            raise ValueError(f"Planned download path must be under data/raw/: {expected_path}")
        path = PurePosixPath(expected_path)
        return PlannedDownload(
            source_id=self.source_id,
            artifact_id=artifact_id or path.stem,
            layer_id=layer_id,
            url=url,
            expected_path=expected_path,
            version=version,
            original_format=original_format or _format_from_path(path),
            license=self.definition.license,
            attribution_text=self.definition.attribution_text,
            default=bool(self.definition.enabled_by_default),
            optional=bool(self.definition.optional),
            isolated=bool(self.definition.isolated),
            restricted=bool(self.definition.restricted),
        )

    def _validate_catalog_layers(self) -> None:
        adapter_layers = {layer.id for layer in self.planned_layers}
        catalog_layers = set(self.definition.layers)
        if adapter_layers != catalog_layers:
            missing = sorted(catalog_layers - adapter_layers)
            extra = sorted(adapter_layers - catalog_layers)
            details = []
            if missing:
                details.append(f"missing from adapter: {', '.join(missing)}")
            if extra:
                details.append(f"missing from catalog: {', '.join(extra)}")
            joined = "; ".join(details)
            raise ValueError(f"Adapter layer mismatch for {self.source_id}: {joined}")


def _format_from_path(path: PurePosixPath) -> str | None:
    suffix = path.suffix.removeprefix(".").lower()
    return suffix or None


def _summarize_values(values: Any) -> str | None:
    unique = sorted({value for value in values if value is not None})
    if not unique:
        return None
    if len(unique) == 1:
        return unique[0]
    return "mixed: " + ", ".join(unique)
