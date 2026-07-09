import hashlib
from io import BytesIO

import pytest

from gpm.manifest import build_downloaded_source_manifest, build_local_source_manifest
from gpm.schemas import validate_source_manifest
from gpm.sources.artifacts import SourceArtifactError, download_source_artifacts
from gpm.sources.registry import resolve_source_adapters


class FakeResponse:
    status = 200

    def __init__(self, payload: bytes) -> None:
        self._payload = BytesIO(payload)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self, size=-1):
        return self._payload.read(size)


def test_download_source_artifacts_writes_files_and_manifest_records(tmp_path, monkeypatch):
    def fake_urlopen(url_request, timeout):
        payload = f"payload:{url_request.full_url}".encode("utf-8")
        return FakeResponse(payload)

    monkeypatch.setattr("gpm.sources.artifacts.request.urlopen", fake_urlopen)
    adapter = resolve_source_adapters("modern-small", ["natural_earth"])[0]
    raw_dir = tmp_path / "raw"

    artifacts_by_source = download_source_artifacts((adapter,), raw_dir=raw_dir, timeout=1)
    artifacts = artifacts_by_source["natural_earth"]

    assert len(artifacts) == 5
    first = artifacts[0]
    payload = f"payload:{first.url}".encode("utf-8")
    assert (raw_dir / "natural_earth" / "ne_10m_land.zip").read_bytes() == payload
    assert first.status == "downloaded"
    assert first.bytes == len(payload)
    assert first.checksum == f"sha256:{hashlib.sha256(payload).hexdigest()}"

    manifest = build_downloaded_source_manifest("modern-small", (adapter,), artifacts_by_source)
    validate_source_manifest(manifest)
    source = manifest["sources"][0]
    assert manifest["manifest_type"] == "build"
    assert source["status"] == "downloaded"
    assert source["version"] == "natural-earth-10m"
    assert source["original_format"] == "zip"
    assert source["checksum"].startswith("sha256:")
    assert len(source["artifacts"]) == 5
    assert source["artifacts"][0]["checksum"] == first.checksum


def test_local_source_manifest_reports_missing_raw_artifacts(tmp_path):
    with pytest.raises(SourceArtifactError, match="missing"):
        build_local_source_manifest("modern-small", ["natural_earth"], raw_dir=tmp_path / "raw")
