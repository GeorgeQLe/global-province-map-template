"""M14.5 public landing page validation and CLI tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from gpm.cli import main
from gpm.paths import PROJECT_ROOT
from gpm.release import (
    REQUIRED_DEMO_FILES,
    REQUIRED_DEMO_HTML_SNIPPETS,
    REQUIRED_HTML_SNIPPETS,
    REQUIRED_LANDING_FILES,
    ReleaseError,
    default_landing_dir,
    release_landing_site,
    validate_landing_site,
)


def test_default_landing_dir_points_at_repo_landing():
    path = default_landing_dir()
    assert path == PROJECT_ROOT / "landing"
    assert path.is_dir()


def test_bundled_landing_site_validates():
    result = validate_landing_site()
    assert result.valid is True
    assert result.missing_files == ()
    assert result.missing_snippets == ()
    assert result.missing_demo_files == ()
    assert result.missing_demo_snippets == ()
    assert result.html_bytes > 1000
    assert result.demo_html_bytes > 1000
    for name in REQUIRED_LANDING_FILES:
        assert name in result.files_present
    for name in REQUIRED_DEMO_FILES:
        assert name in result.demo_files_present
    html = Path(result.landing_dir, "index.html").read_text(encoding="utf-8")
    for snippet in REQUIRED_HTML_SNIPPETS:
        assert snippet in html
    demo_html = Path(result.landing_dir, "demo", "index.html").read_text(encoding="utf-8")
    for snippet in REQUIRED_DEMO_HTML_SNIPPETS:
        assert snippet in demo_html
    manifest = json.loads(
        Path(result.landing_dir, "demo", "data", "demo-manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert "future_slots" in manifest
    assert any(s.get("id") == "period-geometry" for s in manifest["future_slots"])
    assert len(manifest.get("scenarios", [])) >= 3


def test_validate_landing_site_rejects_missing_files(tmp_path: Path):
    landing = tmp_path / "landing"
    landing.mkdir()
    (landing / "index.html").write_text("<html><body>Global Province Map</body></html>", encoding="utf-8")
    result = validate_landing_site(landing)
    assert result.valid is False
    assert "styles.css" in result.missing_files
    assert "app.js" in result.missing_files
    assert "vercel.json" in result.missing_files


def test_validate_landing_site_rejects_missing_snippets(tmp_path: Path):
    landing = tmp_path / "landing"
    landing.mkdir()
    for name in REQUIRED_LANDING_FILES:
        if name == "index.html":
            (landing / name).write_text(
                "<!DOCTYPE html><title>Empty</title><body>no project copy</body>",
                encoding="utf-8",
            )
        else:
            (landing / name).write_text("{}", encoding="utf-8")
    result = validate_landing_site(landing)
    assert result.valid is False
    assert len(result.missing_snippets) == len(REQUIRED_HTML_SNIPPETS)


def test_release_landing_site_dry_run_on_bundled():
    result = release_landing_site(dry_run=True)
    assert result.validation.valid is True
    assert result.dry_run is True
    assert result.deployed is False
    assert result.pushed is False
    assert any("Dry run" in message for message in result.messages)


def test_release_landing_site_fails_on_invalid(tmp_path: Path):
    landing = tmp_path / "landing"
    landing.mkdir()
    with pytest.raises(ReleaseError, match="validation failed"):
        release_landing_site(landing_dir=landing, dry_run=True)


def test_cli_release_site_dry_run_text(capsys):
    code = main(["release", "site", "--dry-run"])
    assert code == 0
    out = capsys.readouterr().out
    assert "M14.5" in out
    assert "Validation: passed" in out
    assert "dry-run" in out.lower()


def test_cli_release_site_dry_run_json(capsys):
    code = main(["release", "site", "--dry-run", "--format", "json"])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["dry_run"] is True
    assert payload["validation"]["valid"] is True
    assert "index.html" in payload["validation"]["files_present"]


def test_cli_release_site_missing_dir_fails(tmp_path: Path, capsys):
    code = main(["release", "site", "--landing-dir", str(tmp_path / "nope"), "--dry-run"])
    assert code == 1
    err = capsys.readouterr().err
    assert "does not exist" in err or "Landing" in err
