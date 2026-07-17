from __future__ import annotations

import csv
import json
from pathlib import Path
from urllib.request import urlopen

import pytest
from shapely.geometry import shape
from shapely.ops import unary_union

import gpm.cli as cli
from gpm.builders.aggregation import aggregate_location_provinces
from gpm.builders.adjacency import build_land_adjacency
from gpm.builders.hierarchy import build_hierarchy
from gpm.builders.locations import LocationBuildError, build_location_fabric
from gpm.exporters import export_geojson_pack
from gpm.qa.fabric import run_fabric_qa, run_paintability_qa
from gpm.schemas import validate_location_fabric_manifest, validate_location_lineage
from gpm.viewer import prepare_review_dataset, serve_review
from test_build_provinces import _write_polygon_zip


def _write(path: Path, value: dict) -> Path:
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def _feature(geometry: dict, **properties: object) -> dict:
    return {"type": "Feature", "geometry": geometry, "properties": properties}


def _polygon(west: float, south: float, east: float, north: float) -> dict:
    return {
        "type": "Polygon",
        "coordinates": [[[west, south], [east, south], [east, north], [west, north], [west, south]]],
    }


def _inputs(tmp_path: Path) -> tuple[Path, Path]:
    land = _write(tmp_path / "land.geojson", {
        "type": "FeatureCollection",
        "license_lineage": ["fixture CC0"],
        "features": [_feature(_polygon(-3, -2, 3, 2), reference_id="neutral-land")],
    })
    admin = _write(tmp_path / "admin.geojson", {
        "type": "FeatureCollection",
        "license_lineage": ["fixture CC0"],
        "features": [
            _feature(_polygon(-3, -2, 0, 2), reference_id="WEST"),
            _feature(_polygon(0, -2, 3, 2), reference_id="EAST"),
        ],
    })
    return land, admin


def test_location_fabric_is_deterministic_and_covers_land(tmp_path: Path) -> None:
    land, admin = _inputs(tmp_path)
    first = tmp_path / "first"
    second = tmp_path / "second"
    result = build_location_fabric(
        land_input=land, admin0_input=admin, output_dir=first,
        target_location_count=24, generated_at="2026-01-01T00:00:00+00:00",
    )
    build_location_fabric(
        land_input=land, admin0_input=admin, output_dir=second,
        target_location_count=24, generated_at="2026-01-01T00:00:00+00:00",
    )
    assert result.location_count >= 24
    assert (first / "locations.geojson").read_bytes() == (second / "locations.geojson").read_bytes()
    assert (first / "location_adjacency.csv").read_bytes() == (second / "location_adjacency.csv").read_bytes()
    locations = json.loads((first / "locations.geojson").read_text())
    fabric = unary_union([shape(feature["geometry"]) for feature in locations["features"]])
    assert fabric.symmetric_difference(shape(_polygon(-3, -2, 3, 2))).area < 1e-8
    qa = run_fabric_qa(location_input=first / "locations.geojson", land_input=land)
    assert qa.status == "pass"


def test_optional_signal_requires_license_and_changes_refinement(tmp_path: Path) -> None:
    land, admin = _inputs(tmp_path)
    signal = _write(tmp_path / "population.geojson", {
        "type": "FeatureCollection",
        "features": [_feature({"type": "Point", "coordinates": [2, 0]}, value=1000)],
    })
    try:
        build_location_fabric(
            land_input=land, admin0_input=admin, population_input=signal,
            output_dir=tmp_path / "bad", target_location_count=12,
        )
    except LocationBuildError as exc:
        assert "license" in str(exc).lower()
    else:
        raise AssertionError("unlicensed optional input was accepted")
    result = build_location_fabric(
        land_input=land, admin0_input=admin, population_input=signal,
        population_license_lineage=("fixture CC0",), output_dir=tmp_path / "good",
        target_location_count=24,
    )
    assert "population" not in result.missing_signals


def test_hard_and_soft_aggregation_and_paintability(tmp_path: Path) -> None:
    land, admin = _inputs(tmp_path)
    output = tmp_path / "fabric"
    build_location_fabric(
        land_input=land, admin0_input=admin, output_dir=output, target_location_count=24,
    )
    intersections = list(csv.DictReader((output / "location_admin_intersections.csv").open()))
    assert any(row["reference_id"] == "WEST" for row in intersections)
    assert any(row["reference_id"] == "EAST" for row in intersections)

    soft = aggregate_location_provinces(
        "eu-like", location_input=output / "locations.geojson",
        output_dir=tmp_path / "soft", target_province_count=5,
        modern_boundary_influence="soft", generated_at="2026-01-01T00:00:00+00:00",
    )
    assert soft.province_count == 5
    soft_repeat = aggregate_location_provinces(
        "eu-like", location_input=output / "locations.geojson",
        output_dir=tmp_path / "soft-repeat", target_province_count=5,
        modern_boundary_influence="soft", generated_at="2026-01-01T00:00:00+00:00",
    )
    for name in ("provinces.geojson", "province_membership.csv", "province_aggregation_manifest.json"):
        assert (tmp_path / "soft" / name).read_bytes() == (tmp_path / "soft-repeat" / name).read_bytes()
    adjacency = build_land_adjacency(
        "eu-like", province_input=tmp_path / "soft" / "provinces.geojson",
        output=tmp_path / "soft" / "adjacency.csv",
    )
    hierarchy = build_hierarchy(
        "eu-like", province_input=tmp_path / "soft" / "provinces.geojson",
        adjacency_input=Path(adjacency.output), output=tmp_path / "soft" / "hierarchy.geojson",
    )
    assert hierarchy.area_count > 0
    hierarchy_doc = json.loads((tmp_path / "soft" / "hierarchy.geojson").read_text())
    assert hierarchy_doc["gpm"]["id_scheme"] == "location-membership-sha256-v1"
    hard = aggregate_location_provinces(
        "modern-small", location_input=output / "locations.geojson",
        output_dir=tmp_path / "hard", target_province_count=6,
        modern_boundary_influence="hard", generated_at="2026-01-01T00:00:00+00:00",
    )
    assert hard.province_count == 6

    boundary = _write(tmp_path / "boundary.geojson", {
        "type": "FeatureCollection",
        "features": [_feature({"type": "LineString", "coordinates": [[-2.5, 0.25], [2.5, 0.25]]}, boundary_id="required")],
    })
    paint = run_paintability_qa(
        location_input=output / "locations.geojson", boundary_input=boundary,
        affected_dates=("1836-01-01",), license_lineage=("fixture CC0",),
    )
    assert paint.status == "fail"
    requests = json.loads(Path(paint.split_requests_output).read_text())["requests"]
    assert requests[0]["operation"] == "split_by_boundary"


def test_custom_reference_inputs_require_and_record_actual_licenses(tmp_path: Path) -> None:
    land, admin = _inputs(tmp_path)
    unlicensed = _write(tmp_path / "unlicensed.geojson", {
        "type": "FeatureCollection", "features": [_feature(_polygon(-3, -2, 3, 2))],
    })
    with pytest.raises(LocationBuildError, match="--land-license"):
        build_location_fabric(
            land_input=unlicensed, output_dir=tmp_path / "bad", target_location_count=12,
        )
    explicit_output = tmp_path / "explicit-license"
    build_location_fabric(
        land_input=unlicensed, land_license_lineage=("explicit fixture CC0",),
        output_dir=explicit_output, target_location_count=12,
    )
    explicit_manifest = json.loads((explicit_output / "location_fabric_manifest.json").read_text())
    assert explicit_manifest["inputs"][0]["license_lineage"] == ["explicit fixture CC0"]

    signal = _write(tmp_path / "terrain.geojson", {
        "type": "FeatureCollection", "license_lineage": ["terrain fixture CC0"],
        "features": [_feature(_polygon(-3, -2, 3, 2), value=2)],
    })
    output = tmp_path / "fabric"
    build_location_fabric(
        land_input=land, admin0_input=admin, terrain_input=signal,
        output_dir=output, target_location_count=12,
    )
    manifest = json.loads((output / "location_fabric_manifest.json").read_text())
    validate_location_fabric_manifest(manifest)
    assert {(item["role"], item["path"]) for item in manifest["inputs"]} == {
        ("land", str(land)), ("admin0", str(admin)), ("terrain", str(signal)),
    }
    assert "Natural Earth public domain" not in manifest["license_lineage"]
    locations = json.loads((output / "locations.geojson").read_text())
    assert all(str(signal) in feature["properties"]["source_lineage"] for feature in locations["features"])
    assert all("terrain fixture CC0" in feature["properties"]["license_lineage"] for feature in locations["features"])


def test_split_migration_requires_new_revision_and_preserves_unchanged_ids(tmp_path: Path) -> None:
    land, admin = _inputs(tmp_path)
    source_dir = tmp_path / "source"
    build_location_fabric(
        land_input=land, admin0_input=admin, output_dir=source_dir,
        target_location_count=24, generated_at="2026-01-01T00:00:00+00:00",
    )
    boundary = {"type": "LineString", "coordinates": [[-2.75, 0.314], [2.75, 0.314]]}
    requests = _write(tmp_path / "requests.json", {
        "schema_version": "0.1.0",
        "requests": [{
            "request_id": "migrate_1444_boundary", "operation": "split_by_boundary",
            "failed_paintability_test": "fixture-crossing", "proposed_geometry": boundary,
            "sources": ["fixture research"], "license_lineage": ["fixture CC0"],
            "confidence": "high", "affected_dates": ["1444-11-11"],
            "target_fabric_revision": "1",
        }],
    })
    with pytest.raises(LocationBuildError, match="required"):
        build_location_fabric(
            land_input=land, admin0_input=admin, split_request_input=requests,
            output_dir=tmp_path / "missing-revision", target_location_count=24,
        )
    with pytest.raises(LocationBuildError, match="differ"):
        build_location_fabric(
            land_input=land, admin0_input=admin, split_request_input=requests,
            output_fabric_revision="1", output_dir=tmp_path / "same-revision",
            target_location_count=24,
        )
    with pytest.raises(LocationBuildError, match="only valid"):
        build_location_fabric(
            land_input=land, admin0_input=admin, output_fabric_revision="2",
            output_dir=tmp_path / "no-request", target_location_count=24,
        )

    migrated_dir = tmp_path / "migrated"
    build_location_fabric(
        land_input=land, admin0_input=admin, split_request_input=requests,
        output_fabric_revision="2", output_dir=migrated_dir, target_location_count=24,
        generated_at="2026-01-01T00:00:00+00:00",
    )
    source = json.loads((source_dir / "locations.geojson").read_text())
    migrated = json.loads((migrated_dir / "locations.geojson").read_text())
    lineage = json.loads((migrated_dir / "location_lineage.json").read_text())
    manifest = json.loads((migrated_dir / "location_fabric_manifest.json").read_text())
    validate_location_lineage(lineage)
    validate_location_fabric_manifest(manifest)
    event = next(item for item in lineage["events"] if item.get("request_id") == "migrate_1444_boundary")
    source_ids = {item["properties"]["location_id"] for item in source["features"]}
    migrated_ids = {item["properties"]["location_id"] for item in migrated["features"]}
    parents = set(event["parent_location_ids"])
    children = set(event["child_location_ids"])
    assert parents and children and parents.isdisjoint(children)
    assert source_ids - parents <= migrated_ids
    assert children <= migrated_ids - source_ids
    assert all(item["properties"]["fabric_revision"] == "2" for item in migrated["features"])
    assert lineage["source_fabric_revision"] == "1"
    assert lineage["output_fabric_revision"] == "2"
    assert manifest["source_fabric_revision"] == "1"
    assert manifest["output_fabric_revision"] == "2"


def test_refine_request_is_a_noop_when_the_grid_is_exhausted(tmp_path: Path) -> None:
    """refine_h3 stops silently at maximum resolution; split_by_boundary stays strict."""
    land, admin = _inputs(tmp_path)
    source_dir = tmp_path / "source"
    build_location_fabric(
        land_input=land, admin0_input=admin, output_dir=source_dir,
        target_location_count=24, generated_at="2026-01-01T00:00:00+00:00",
    )
    locations = json.loads((source_dir / "locations.geojson").read_text())
    maximum = max(item["properties"]["h3_resolution"] for item in locations["features"])
    target = next(
        item for item in locations["features"]
        if item["properties"]["h3_resolution"] == maximum
    )
    request = {
        "request_id": "refine_exhausted", "operation": "refine_h3",
        "failed_paintability_test": "fixture", "proposed_geometry": target["geometry"],
        "sources": ["fixture research"], "license_lineage": ["fixture CC0"],
        "confidence": "high", "affected_dates": ["1444-11-11"],
        "target_fabric_revision": "1",
    }
    # Force every affected location to already sit at the configured maximum
    # by refining twice: the second identical request must not raise.
    requests = _write(tmp_path / "requests.json", {
        "schema_version": "0.1.0",
        "requests": [
            {**request, "request_id": "refine_once"},
            {**request, "request_id": "refine_again_a"},
            {**request, "request_id": "refine_again_b"},
        ],
    })
    migrated_dir = tmp_path / "migrated"
    build_location_fabric(
        land_input=land, admin0_input=admin, split_request_input=requests,
        output_fabric_revision="2", output_dir=migrated_dir, target_location_count=24,
        generated_at="2026-01-01T00:00:00+00:00",
    )
    lineage = json.loads((migrated_dir / "location_lineage.json").read_text())
    recorded = {item.get("request_id") for item in lineage["events"]}
    issued = {"refine_once", "refine_again_a", "refine_again_b"}
    # at least one exhausted round produced no event instead of failing the build
    assert recorded & issued != issued


def test_fabric_qa_is_fail_closed_and_resolves_land_from_manifest(tmp_path: Path) -> None:
    land, admin = _inputs(tmp_path)
    output = tmp_path / "fabric"
    build_location_fabric(
        land_input=land, admin0_input=admin, output_dir=output, target_location_count=12,
    )
    assert run_fabric_qa(location_input=output / "locations.geojson").status == "pass"
    (output / "location_adjacency.csv").unlink()
    failed = run_fabric_qa(location_input=output / "locations.geojson")
    report = json.loads(Path(failed.report_output).read_text())
    assert failed.status == "fail"
    assert "missing_or_malformed_adjacency" in {item["code"] for item in report["findings"]}


def test_fabric_qa_supports_manifest_declared_natural_earth_zip_land(tmp_path: Path) -> None:
    land, admin = _inputs(tmp_path)
    output = tmp_path / "fabric"
    build_location_fabric(
        land_input=land, admin0_input=admin, output_dir=output, target_location_count=12,
    )
    land_zip = tmp_path / "ne_10m_land.zip"
    _write_polygon_zip(land_zip, "ne_10m_land", [
        ({"name": "fixture-land"}, [[-3, -2], [3, -2], [3, 2], [-3, 2], [-3, -2]]),
    ])
    manifest_path = output / "location_fabric_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    land_record = next(item for item in manifest["inputs"] if item["role"] == "land")
    land_record["path"] = str(land_zip)
    land_record["format"] = "natural-earth-zip"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    assert run_fabric_qa(location_input=output / "locations.geojson").status == "pass"


def test_fabric_qa_rejects_corrupt_sidecars_and_revision_mismatches(tmp_path: Path) -> None:
    land, admin = _inputs(tmp_path)
    output = tmp_path / "fabric"
    build_location_fabric(
        land_input=land, admin0_input=admin, output_dir=output, target_location_count=12,
    )
    lineage_path = output / "location_lineage.json"
    original = json.loads(lineage_path.read_text())
    lineage_path.write_text("{", encoding="utf-8")
    corrupt = run_fabric_qa(location_input=output / "locations.geojson")
    corrupt_report = json.loads(Path(corrupt.report_output).read_text())
    assert "missing_or_malformed_lineage" in {item["code"] for item in corrupt_report["findings"]}

    original["fabric_revision"] = "other"
    original["output_fabric_revision"] = "other"
    lineage_path.write_text(json.dumps(original), encoding="utf-8")
    mismatch = run_fabric_qa(location_input=output / "locations.geojson")
    mismatch_report = json.loads(Path(mismatch.report_output).read_text())
    assert "lineage_revision_mismatch" in {item["code"] for item in mismatch_report["findings"]}


def test_1444_derived_province_crosses_modern_admin_boundary(tmp_path: Path) -> None:
    fixture = json.loads((Path(__file__).parent / "fixtures/m23/1444-cross-admin.json").read_text())
    land, admin = _inputs(tmp_path)
    fabric = tmp_path / "fabric"
    build_location_fabric(
        land_input=land, admin0_input=admin, output_dir=fabric, target_location_count=24,
    )
    result = aggregate_location_provinces(
        "eu-like", location_input=fabric / "locations.geojson", output_dir=tmp_path / "derived",
        target_province_count=fixture["target_province_count"], start_date=fixture["start_date"],
        generated_at="2026-01-01T00:00:00+00:00",
    )
    assert result.province_count == 1
    intersections = list(csv.DictReader((fabric / "location_admin_intersections.csv").open()))
    membership = list(csv.DictReader(Path(result.membership_output).open()))
    member_ids = {row["location_id"] for row in membership}
    refs = {row["reference_id"] for row in intersections if row["location_id"] in member_ids}
    assert set(fixture["required_modern_reference_ids"]) <= refs


def test_province_cli_defaults_to_neutral_fabric_and_legacy_flags_are_explicit(tmp_path: Path, monkeypatch, capsys) -> None:
    land, admin = _inputs(tmp_path)
    processed = tmp_path / "processed"
    build_location_fabric(
        land_input=land, admin0_input=admin, output_dir=processed, target_location_count=12,
    )
    monkeypatch.setattr(cli, "PROCESSED_DATA_DIR", processed)
    assert cli.main([
        "build", "provinces", "--profile", "eu-like", "--processed-dir", str(processed),
        "--target-province-count", "1", "--format", "json",
    ]) == 0
    assert json.loads(capsys.readouterr().out)["input_location_count"] >= 12
    assert cli.main(["build", "provinces", "--refine"]) == 1
    assert "require --legacy-modern-admin" in capsys.readouterr().err


def test_review_endpoints_and_export_keep_m23_artifacts_separate(tmp_path: Path) -> None:
    land, admin = _inputs(tmp_path)
    processed = tmp_path / "processed"
    build_location_fabric(
        land_input=land, admin0_input=admin, output_dir=processed, target_location_count=12,
    )
    aggregate = aggregate_location_provinces(
        "eu-like", location_input=processed / "locations.geojson", output_dir=processed,
        target_province_count=3, start_date="1444-11-11",
    )
    dataset = prepare_review_dataset(
        "eu-like", province_input=Path(aggregate.province_output), adjacency_input=None,
        qa_report_input=None, location_input=processed / "locations.geojson",
        lineage_input=processed / "location_lineage.json",
        aggregation_manifest_input=Path(aggregate.manifest_output),
    )
    handle = serve_review(
        dataset=dataset, host="127.0.0.1", port=0, open_browser=False, block=False,
    )
    try:
        base = handle.result.url.rstrip("/")
        with urlopen(f"{base}/api/meta") as response:
            meta = json.load(response)
        assert meta["gpm"]["layer_kind"] == "location_derived_provinces"
        assert {"locations", "lineage", "province_aggregation"} <= set(meta["m23_inputs"])
        with urlopen(f"{base}{meta['endpoints']['locations']}") as response:
            locations = json.load(response)
        assert locations["gpm"]["layer_kind"] == "locations"
        with urlopen(f"{base}{meta['endpoints']['lineage']}") as response:
            assert json.load(response)["fabric_revision"] == "1"
    finally:
        handle.shutdown()

    exported = export_geojson_pack(
        "eu-like", province_input=Path(aggregate.province_output), output_dir=tmp_path / "export",
    )
    pack_root = Path(exported.output_dir)
    manifest = json.loads(Path(exported.pack_manifest).read_text())
    assert (pack_root / "atomic/locations.geojson").is_file()
    assert (pack_root / "tables/province_membership.csv").is_file()
    assert "atomic/locations.geojson" != "provinces.geojson"
    assert manifest["inputs"]["m23_artifacts"]["locations.geojson"] == "atomic/locations.geojson"
    assert manifest["inputs"]["m23_artifacts"]["province_membership.csv"] == "tables/province_membership.csv"
