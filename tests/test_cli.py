import json

from gpm.cli import main
from gpm.schemas import validate_source_manifest


def test_stub_cli_commands_print_helpful_placeholder_output(capsys):
    commands = [
        ["build", "provinces"],
        ["build", "adjacency"],
        ["export", "geojson"],
        ["qa", "topology"],
        ["qa", "render"],
    ]

    for command in commands:
        assert main(command) == 0
        output = capsys.readouterr().out
        assert "Phase 1 placeholder" in output
        assert "Profile: modern-small" in output


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
        ["qa", "topology", "--profile", "missing-profile"],
        ["qa", "render", "--profile", "missing-profile"],
    ]

    for command in commands:
        assert main(command) == 1
        captured = capsys.readouterr()
        assert "Unknown profile 'missing-profile'" in captured.err
        assert "Traceback" not in captured.err
