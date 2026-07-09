from __future__ import annotations

import hashlib
import tempfile
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any
from urllib import error, request

from gpm import __version__
from gpm.paths import PROJECT_ROOT, RAW_DATA_DIR
from gpm.sources.adapters.base import BaseSourceAdapter, PlannedDownload


class SourceArtifactError(RuntimeError):
    """Raised when source artifacts cannot be downloaded or inspected."""


@dataclass(frozen=True)
class SourceArtifact:
    source_id: str
    artifact_id: str
    layer_id: str
    status: str
    url: str
    path: str
    access_date: str
    version: str | None
    original_format: str | None
    bytes: int
    checksum: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_manifest_artifact(self) -> dict[str, Any]:
        return {
            "id": self.artifact_id,
            "layer_id": self.layer_id,
            "status": self.status,
            "url": self.url,
            "path": self.path,
            "access_date": self.access_date,
            "version": self.version,
            "original_format": self.original_format,
            "bytes": self.bytes,
            "checksum": self.checksum,
        }


def download_source_artifacts(
    adapters: Iterable[BaseSourceAdapter],
    *,
    raw_dir: Path = RAW_DATA_DIR,
    force: bool = False,
    timeout: float = 60.0,
) -> dict[str, tuple[SourceArtifact, ...]]:
    """Download every planned artifact for the supplied adapters."""
    access_date = _access_date()
    artifacts_by_source: dict[str, tuple[SourceArtifact, ...]] = {}
    for adapter in adapters:
        artifacts = [
            _download_or_reuse(
                planned,
                raw_dir=raw_dir,
                force=force,
                timeout=timeout,
                access_date=access_date,
            )
            for planned in adapter.planned_downloads()
        ]
        artifacts_by_source[adapter.source_id] = tuple(artifacts)
    return artifacts_by_source


def inspect_local_source_artifacts(
    adapter: BaseSourceAdapter,
    *,
    raw_dir: Path = RAW_DATA_DIR,
) -> tuple[SourceArtifact, ...]:
    """Build artifact records from files that already exist under raw_dir."""
    access_date = _access_date()
    return tuple(
        _artifact_from_file(
            planned,
            _target_path(planned, raw_dir),
            status="downloaded",
            access_date=access_date,
        )
        for planned in adapter.planned_downloads()
    )


def source_manifest_record(adapter: BaseSourceAdapter, artifacts: tuple[SourceArtifact, ...]) -> dict[str, Any]:
    if not artifacts:
        raise SourceArtifactError(f"Source '{adapter.source_id}' did not produce any artifacts.")

    record = adapter.manifest_record()
    record.update(
        {
            "status": "downloaded",
            "access_date": _summarize_values(artifact.access_date for artifact in artifacts),
            "version": _summarize_values(artifact.version for artifact in artifacts),
            "original_format": _summarize_values(artifact.original_format for artifact in artifacts),
            "checksum": _combined_checksum(artifacts),
            "artifacts": [artifact.to_manifest_artifact() for artifact in artifacts],
            "transformation_steps": [
                "Downloaded source artifacts exactly as published; no geospatial transformations applied."
            ],
        }
    )
    return record


def _download_or_reuse(
    planned: PlannedDownload,
    *,
    raw_dir: Path,
    force: bool,
    timeout: float,
    access_date: str,
) -> SourceArtifact:
    target = _target_path(planned, raw_dir)
    if target.exists() and not force:
        return _artifact_from_file(planned, target, status="existing", access_date=access_date)

    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        byte_count, checksum = _download_to_path(planned.url, target, timeout=timeout)
    except (OSError, error.URLError, SourceArtifactError) as exc:
        raise SourceArtifactError(f"Failed to download {planned.url} to {target}: {exc}") from exc

    return _artifact_record(
        planned,
        target,
        status="downloaded",
        access_date=access_date,
        byte_count=byte_count,
        checksum=checksum,
    )


def _download_to_path(url: str, target: Path, *, timeout: float) -> tuple[int, str]:
    tmp_path: Path | None = None
    hasher = hashlib.sha256()
    byte_count = 0
    request_headers = {"User-Agent": f"global-province-map-template/{__version__}"}
    url_request = request.Request(url, headers=request_headers)

    try:
        with request.urlopen(url_request, timeout=timeout) as response:
            status = getattr(response, "status", None)
            if status is not None and status >= 400:
                raise SourceArtifactError(f"HTTP {status}")

            with tempfile.NamedTemporaryFile(
                "wb",
                dir=target.parent,
                prefix=f".{target.name}.",
                suffix=".tmp",
                delete=False,
            ) as temp_file:
                tmp_path = Path(temp_file.name)
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    hasher.update(chunk)
                    byte_count += len(chunk)
                    temp_file.write(chunk)
        tmp_path.replace(target)
    except Exception:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)
        raise

    return byte_count, f"sha256:{hasher.hexdigest()}"


def _artifact_from_file(
    planned: PlannedDownload,
    target: Path,
    *,
    status: str,
    access_date: str,
) -> SourceArtifact:
    if not target.exists():
        raise SourceArtifactError(f"Expected source artifact is missing: {target}")
    if not target.is_file():
        raise SourceArtifactError(f"Expected source artifact is not a file: {target}")

    byte_count, checksum = _hash_file(target)
    return _artifact_record(
        planned,
        target,
        status=status,
        access_date=access_date,
        byte_count=byte_count,
        checksum=checksum,
    )


def _artifact_record(
    planned: PlannedDownload,
    target: Path,
    *,
    status: str,
    access_date: str,
    byte_count: int,
    checksum: str,
) -> SourceArtifact:
    return SourceArtifact(
        source_id=planned.source_id,
        artifact_id=planned.artifact_id,
        layer_id=planned.layer_id,
        status=status,
        url=planned.url,
        path=_manifest_path(target),
        access_date=access_date,
        version=planned.version,
        original_format=planned.original_format,
        bytes=byte_count,
        checksum=checksum,
    )


def _target_path(planned: PlannedDownload, raw_dir: Path) -> Path:
    parts = PurePosixPath(planned.expected_path).parts
    if len(parts) < 3 or parts[0:2] != ("data", "raw"):
        raise SourceArtifactError(f"Planned download path must be under data/raw/: {planned.expected_path}")
    return raw_dir.expanduser() / Path(*parts[2:])


def _manifest_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return str(resolved)


def _hash_file(path: Path) -> tuple[int, str]:
    hasher = hashlib.sha256()
    byte_count = 0
    with path.open("rb") as file:
        while True:
            chunk = file.read(1024 * 1024)
            if not chunk:
                break
            hasher.update(chunk)
            byte_count += len(chunk)
    return byte_count, f"sha256:{hasher.hexdigest()}"


def _combined_checksum(artifacts: tuple[SourceArtifact, ...]) -> str:
    payload = "\n".join(
        f"{artifact.path}\t{artifact.checksum}"
        for artifact in sorted(artifacts, key=lambda item: (item.layer_id, item.artifact_id, item.path))
    )
    return f"sha256:{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"


def _summarize_values(values: Any) -> str | None:
    unique = sorted({value for value in values if value is not None})
    if not unique:
        return None
    if len(unique) == 1:
        return unique[0]
    return "mixed: " + ", ".join(unique)


def _access_date() -> str:
    return datetime.now(UTC).date().isoformat()
