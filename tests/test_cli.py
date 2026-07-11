import json
from io import BytesIO

from gpm.cli import main
from gpm.schemas import validate_source_manifest


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


def test_stub_cli_commands_print_helpful_placeholder_output(capsys):
    assert main(["qa", "render"]) == 0
    output = capsys.readouterr().out
    assert "Phase 1 placeholder" in output
    assert "Profile: modern-small" in output


def test_qa_render_points_to_interactive_review_command(capsys):
    assert main(["qa", "render"]) == 0
    output = capsys.readouterr().out
    assert "gpm review" in output


def test_sources_download_dry_run_includes_default_adapters(capsys):
    assert main(["sources", "download", "--profile", "modern-small"]) == 0
    output = capsys.readouterr().out

    assert "dry run only; no datasets were downloaded" in output
    assert "Natural Earth (natural_earth)" in output
    assert "geoBoundaries (geoboundaries)" in output
    assert "data/raw/natural_earth/ne_10m_land.zip" in output
    assert "data/raw/geoboundaries/gbopen_all_adm0_api.json" in output


def test_sources_download_json_is_parseable_planned_records(capsys):
    assert main(["sources", "download", "--format", "json"]) == 0
    output = capsys.readouterr().out
    records = json.loads(output)

    assert {record["source_id"] for record in records} == {"natural_earth", "geoboundaries"}
    assert {record["layer_id"] for record in records} >= {"land", "adm0", "adm1", "adm2_plus"}
    assert all(record["expected_path"].startswith("data/raw/") for record in records)
    assert all(record["default"] is True for record in records)
    assert all(record["restricted"] is False for record in records)


def test_sources_download_source_filter_limits_output(capsys):
    assert main(["sources", "download", "--source", "natural_earth", "--format", "json"]) == 0
    output = capsys.readouterr().out
    records = json.loads(output)

    assert {record["source_id"] for record in records} == {"natural_earth"}
    assert {record["layer_id"] for record in records} == {
        "land",
        "coastline",
        "admin0_countries",
        "admin1_states_provinces",
        "rivers_lakes",
    }


def test_sources_download_execute_writes_manifest_and_artifacts(tmp_path, monkeypatch, capsys):
    def fake_urlopen(url_request, timeout):
        return FakeResponse(f"downloaded:{url_request.full_url}".encode("utf-8"))

    monkeypatch.setattr("gpm.sources.artifacts.request.urlopen", fake_urlopen)
    raw_dir = tmp_path / "raw"
    manifest_path = tmp_path / "source_manifest.json"

    assert (
        main(
            [
                "sources",
                "download",
                "--execute",
                "--source",
                "natural_earth",
                "--raw-dir",
                str(raw_dir),
                "--manifest-output",
                str(manifest_path),
            ]
        )
        == 0
    )
    output = capsys.readouterr().out
    assert "downloaded or verified source artifacts" in output
    assert str(manifest_path) in output
    assert (raw_dir / "natural_earth" / "ne_10m_land.zip").is_file()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    validate_source_manifest(manifest)
    assert manifest["manifest_type"] == "build"
    assert manifest["sources"][0]["status"] == "downloaded"
    assert manifest["sources"][0]["artifacts"][0]["checksum"].startswith("sha256:")


def test_sources_download_rejects_restricted_gadm(capsys):
    assert main(["sources", "download", "--source", "gadm"]) == 1
    captured = capsys.readouterr()

    assert "restricted" in captured.err
    assert "gadm" in captured.err


def test_sources_manifest_cli_prints_valid_json_manifest(capsys):
    assert main(["sources", "manifest"]) == 0
    output = capsys.readouterr().out
    manifest = json.loads(output)

    assert manifest["manifest_type"] == "planned"
    assert [source["id"] for source in manifest["sources"]] == ["natural_earth", "geoboundaries"]


def test_sources_manifest_output_writes_valid_manifest(tmp_path, capsys):
    output_path = tmp_path / "source_manifest.json"

    assert main(["sources", "manifest", "--output", str(output_path)]) == 0
    captured = capsys.readouterr()
    assert str(output_path) in captured.out

    manifest = json.loads(output_path.read_text(encoding="utf-8"))
    validate_source_manifest(manifest)
    assert [source["id"] for source in manifest["sources"]] == ["natural_earth", "geoboundaries"]


def test_unknown_profile_returns_clean_cli_error(capsys):
    commands = [
        ["sources", "download", "--profile", "missing-profile"],
        ["sources", "manifest", "--profile", "missing-profile"],
        ["build", "provinces", "--profile", "missing-profile"],
        ["build", "adjacency", "--profile", "missing-profile"],
        ["export", "geojson", "--profile", "missing-profile"],
        ["export", "pack", "--profile", "missing-profile"],
        ["qa", "topology", "--profile", "missing-profile"],
        ["qa", "render", "--profile", "missing-profile"],
        ["review", "--profile", "missing-profile"],
    ]

    for command in commands:
        assert main(command) == 1
        captured = capsys.readouterr()
        assert "Unknown profile 'missing-profile'" in captured.err
        assert "Traceback" not in captured.err
