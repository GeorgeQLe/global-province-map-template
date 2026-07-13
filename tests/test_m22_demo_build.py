"""M22 `gpm demo build` pipeline tests (small fixture build, no real data)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from gpm.builders.adjacency import build_land_adjacency
from gpm.builders.hierarchy import build_hierarchy
from gpm.cli import main
from gpm.release import DEMO_SCENARIOS, DemoBuildError, build_demo
from gpm.tiles import read_pmtiles_header

from test_m21_hierarchy import _write_fixture_world


@pytest.fixture()
def fixture_build(tmp_path: Path) -> dict[str, Path]:
    """Provinces + adjacency + hierarchy for a small synthetic world."""
    province_input, adjacency_input = _write_fixture_world(tmp_path)
    hierarchy_output = tmp_path / "hierarchy.geojson"
    build_hierarchy(
        "modern-small",
        province_input=province_input,
        adjacency_input=adjacency_input,
        raw_dir=tmp_path / "missing-raw",
        output=hierarchy_output,
    )
    landing = tmp_path / "landing"
    (landing / "demo" / "data").mkdir(parents=True)
    return {
        "provinces": province_input,
        "adjacency": adjacency_input,
        "hierarchy": hierarchy_output,
        "landing": landing,
        "work": tmp_path / "work",
    }


def _run_build(fixture_build: dict[str, Path], **kwargs) -> object:
    return build_demo(
        "modern-small",
        province_input=fixture_build["provinces"],
        adjacency_input=fixture_build["adjacency"],
        hierarchy_input=fixture_build["hierarchy"],
        landing_dir=fixture_build["landing"],
        work_dir=fixture_build["work"],
        tile_max_zoom=3,
        prefer_tippecanoe=False,
        validate=False,
        **kwargs,
    )


def test_demo_build_writes_pmtiles_first_pack(fixture_build):
    data_dir = fixture_build["landing"] / "demo" / "data"
    # Pre-seed legacy assets that the PMTiles-first build must drop.
    (data_dir / "official-1444.geojson").write_text("{}", encoding="utf-8")
    (data_dir / "adjacency.json").write_text("{}", encoding="utf-8")

    result = _run_build(fixture_build)

    assert result.scenario_ids == DEMO_SCENARIOS
    assert result.tile_backend == "native"
    assert result.province_count == 13
    assert result.adjacency_edge_count > 0
    assert result.hierarchy_counts["superregions"] == 1
    assert "official-1444.geojson" in result.dropped_files
    assert "adjacency.json" in result.dropped_files

    for scenario_id in DEMO_SCENARIOS:
        assert not (data_dir / f"{scenario_id}.geojson").exists()
        header = read_pmtiles_header(data_dir / f"{scenario_id}.pmtiles")
        assert header["max_zoom"] == 3
        tileset = json.loads((data_dir / f"{scenario_id}.tileset.json").read_text(encoding="utf-8"))
        assert tileset["pmtiles"] == f"{scenario_id}.pmtiles"
        for suffix in ("legend.json", "culture.legend.json", "religion.legend.json"):
            assert (data_dir / f"{scenario_id}.{suffix}").is_file()
        hero = json.loads((data_dir / f"hero-{scenario_id}.geojson").read_text(encoding="utf-8"))
        assert hero["features"], "hero owner dissolve must have features"
        assert all("owner_color" in f["properties"] for f in hero["features"])
        assert all("province_ids" not in f["properties"] for f in hero["features"])

    for overlay in (
        "hierarchy-areas.geojson",
        "hierarchy-regions.geojson",
        "hierarchy-superregions.geojson",
        "adjacency-lines.geojson",
    ):
        assert (data_dir / overlay).is_file()

    lines = json.loads((data_dir / "adjacency-lines.geojson").read_text(encoding="utf-8"))
    assert lines["gpm"]["edge_count"] == len(lines["features"]) == result.adjacency_edge_count
    assert all(f["geometry"]["type"] == "LineString" for f in lines["features"])


def test_demo_manifest_is_regenerated_programmatically(fixture_build):
    _run_build(fixture_build)
    manifest = json.loads(
        (fixture_build["landing"] / "demo" / "data" / "demo-manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["pmtiles"]["enabled"] is True
    assert manifest["pmtiles"]["max_zoom"] == 3
    assert manifest["pmtiles"]["backend"] == "native"
    assert manifest["hierarchy"]["areas"] == "hierarchy-areas.geojson"
    assert manifest["adjacency"]["lines"] == "adjacency-lines.geojson"
    assert manifest["generated"]["command"] == "uv run gpm demo build"
    assert manifest["generated"]["province_count"] == 13
    assert "future_slots" in manifest
    live_ids = {layer["id"] for layer in manifest["live_layers"]}
    assert {"period-geometry", "boundary-hints", "multi-era-packs", "pmtiles", "hierarchy"} <= live_ids

    by_id = {entry["id"]: entry for entry in manifest["scenarios"]}
    assert set(by_id) == set(DEMO_SCENARIOS)
    for scenario_id, entry in by_id.items():
        assert entry["geojson"] is None  # PMTiles-first: no global GeoJSON
        assert entry["pmtiles"] == f"{scenario_id}.pmtiles"
    assert by_id["official-1444"]["supports_period_geometry"] is True
    assert by_id["official-1444"]["period_geojson"] == "official-1444-period.geojson"
    assert by_id["official-1444"]["boundary_hints"] == "boundary-hints-1444.geojson"
    assert by_id["modern-baseline"]["supports_period_geometry"] is False
    assert "period_geojson" not in by_id["modern-baseline"]


def test_demo_build_preflight_requires_hierarchy(fixture_build):
    fixture_build["hierarchy"].unlink()
    with pytest.raises(DemoBuildError) as excinfo:
        _run_build(fixture_build)
    assert "gpm build hierarchy" in str(excinfo.value)


def test_demo_build_preflight_requires_enriched_provinces(fixture_build):
    # Strip the hierarchy parent fields the builder applied.
    document = json.loads(fixture_build["provinces"].read_text(encoding="utf-8"))
    for feature in document["features"]:
        for key in ("parent_area_id", "parent_geo_region_id", "parent_superregion_id"):
            feature["properties"].pop(key, None)
    fixture_build["provinces"].write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(DemoBuildError) as excinfo:
        _run_build(fixture_build)
    assert "parent_area_id" in str(excinfo.value)


def test_demo_build_partial_scenario_set_skips_validation(fixture_build):
    # A custom scenario subset cannot satisfy the full landing contract, so
    # the validator is skipped instead of failing on files this run was
    # never asked to produce.
    result = build_demo(
        "modern-small",
        province_input=fixture_build["provinces"],
        adjacency_input=fixture_build["adjacency"],
        hierarchy_input=fixture_build["hierarchy"],
        landing_dir=fixture_build["landing"],
        work_dir=fixture_build["work"],
        scenarios=("modern-baseline",),
        tile_max_zoom=2,
        prefer_tippecanoe=False,
        validate=True,
    )
    assert result.scenario_ids == ("modern-baseline",)
    assert result.validated is False
    data_dir = fixture_build["landing"] / "demo" / "data"
    assert (data_dir / "modern-baseline.pmtiles").is_file()
    assert not (data_dir / "official-1444.pmtiles").exists()


def test_demo_build_validation_failure_is_actionable(fixture_build):
    # The fixture landing dir has no index.html etc., so validation must fail
    # loudly when requested.
    with pytest.raises(DemoBuildError) as excinfo:
        build_demo(
            "modern-small",
            province_input=fixture_build["provinces"],
            adjacency_input=fixture_build["adjacency"],
            hierarchy_input=fixture_build["hierarchy"],
            landing_dir=fixture_build["landing"],
            work_dir=fixture_build["work"],
            tile_max_zoom=2,
            prefer_tippecanoe=False,
            validate=True,
        )
    assert "validation failed" in str(excinfo.value)


def test_demo_build_cli(fixture_build, capsys):
    code = main(
        [
            "demo",
            "build",
            "--profile",
            "modern-small",
            "--province-input",
            str(fixture_build["provinces"]),
            "--adjacency-input",
            str(fixture_build["adjacency"]),
            "--hierarchy-input",
            str(fixture_build["hierarchy"]),
            "--landing-dir",
            str(fixture_build["landing"]),
            "--work-dir",
            str(fixture_build["work"]),
            "--tile-max-zoom",
            "2",
            "--no-tippecanoe",
            "--no-validate",
            "--format",
            "json",
        ]
    )
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["validated"] is False
    assert payload["tile_max_zoom"] == 2
    assert payload["province_count"] == 13
