"""M14 license-audited beta release tests."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from gpm.cli import main
from gpm.release import (
    BETA_GEOMETRY_TIER,
    DEFAULT_BETA_SCENARIOS,
    LicenseAuditError,
    audit_public_release,
    beta_license_audited_recipe,
    build_beta_release,
    license_audit_markdown,
    recipe_markdown,
)
from gpm.release.quality import QUALITY_TIER_CURATED_POLITICS, QUALITY_TIER_SCAFFOLD_BASELINE
from gpm.schemas import SchemaValidationError, validate_license_audit_report, validate_release_manifest


def test_license_audit_passes_for_clean_natural_earth_features():
    features = [
        _land_feature("land_a", _polygon(0, 0, 1, 1), country="FRA"),
        _sea_feature("sea_a", _polygon(-0.5, -0.5, 0, 0), parent="land_a"),
    ]
    result = audit_public_release(
        profile_id="modern-small",
        features=features,
        release_channel="beta",
    )
    assert result.passed is True
    assert result.error_count == 0
    assert "natural_earth" in result.public_source_ids
    assert "geoboundaries" in result.public_source_ids
    assert "gadm" in result.restricted_source_ids
    assert "openstreetmap" in result.isolated_source_ids
    assert any(record.get("public_path") for record in result.attribution_records)
    assert any(record.get("isolation_notice") for record in result.attribution_records)
    doc = result.to_dict()
    validate_license_audit_report(doc)
    markdown = license_audit_markdown(doc)
    assert "PASSED" in markdown
    assert "gadm" in markdown.lower() or "GADM" in markdown or "`gadm`" in markdown


def test_license_audit_rejects_odbl_and_missing_lineage():
    dirty = [
        {
            "type": "Feature",
            "geometry": _polygon(0, 0, 1, 1),
            "properties": {
                "province_id": "land_dirty",
                "kind": "land",
                "parent_country_id": "FRA",
                "parent_region_id": "FR-IDF",
                "license_lineage": ["OpenStreetMap ODbL"],
                "source_lineage": ["openstreetmap:roads"],
            },
        },
        {
            "type": "Feature",
            "geometry": _polygon(1, 0, 2, 1),
            "properties": {
                "province_id": "land_missing",
                "kind": "land",
                "parent_country_id": "DEU",
                "parent_region_id": "DE-BE",
            },
        },
    ]
    with pytest.raises(LicenseAuditError):
        audit_public_release(
            profile_id="modern-small",
            features=dirty,
            release_channel="beta",
            fail_on_errors=True,
        )
    soft = audit_public_release(
        profile_id="modern-small",
        features=dirty,
        release_channel="beta",
        fail_on_errors=False,
    )
    assert soft.passed is False
    codes = {item.code for item in soft.findings if item.severity == "error"}
    assert "odbl-openstreetmap" in codes
    assert "missing-feature-license-lineage" in codes


def test_beta_recipe_includes_audit_and_dual_faces():
    recipe = beta_license_audited_recipe(
        profile_id="modern-small",
        scenarios=DEFAULT_BETA_SCENARIOS,
        sample_countries=("FRA", "DEU"),
        release_tag="beta-test",
        include_atlas=True,
    )
    assert recipe["recipe_id"] == "beta-license-audited"
    assert recipe["milestone"] == "M14"
    step_ids = [step["id"] for step in recipe["steps"]]
    assert "download-sources" in step_ids
    assert "release-beta" in step_ids
    assert "qa-scenario-official-1836" in step_ids
    assert "qa-scenario-official-1444" in step_ids
    release_step = next(step for step in recipe["steps"] if step["id"] == "release-beta")
    assert "release" in release_step["command"]
    assert "beta" in release_step["command"]
    assert "--country" in release_step["command"]
    md = recipe_markdown(recipe)
    assert "release beta" in md
    assert "license" in md.lower() or "License" in md or "beta" in md


def test_build_beta_release_writes_dual_faces_and_audit(tmp_path):
    province_input = tmp_path / "provinces.geojson"
    sea_input = tmp_path / "sea_zones.geojson"
    adjacency_input = tmp_path / "adjacency.csv"
    output_dir = tmp_path / "releases" / "beta-test"

    _write_provinces(
        province_input,
        [
            _land_feature("land_a", _polygon(0, 0, 1, 1), name="Alpha", region="FR-IDF", country="FRA"),
            _land_feature("land_b", _polygon(1, 0, 2, 1), name="Beta", region="FR-HDF", country="FRA"),
            _land_feature("land_c", _polygon(0, 1, 1, 2), name="Gamma", region="DE-BE", country="DEU"),
            _land_feature("land_d", _polygon(2, 0, 3, 1), name="Delta", region="ES-MD", country="ESP"),
        ],
    )
    _write_seas(
        sea_input,
        [
            _sea_feature("sea_a", _polygon(-0.5, -0.5, 0, 0), parent="land_a"),
        ],
    )
    _write_adjacency(
        adjacency_input,
        [
            {
                "from_province_id": "land_a",
                "to_province_id": "land_b",
                "adjacency_type": "land",
                "bidirectional": "true",
                "crossing_type": "shared_border",
                "shared_border_km": "1.0",
                "source_lineage": '["test"]',
            },
            {
                "from_province_id": "land_a",
                "to_province_id": "sea_a",
                "adjacency_type": "port_to_sea",
                "bidirectional": "true",
                "crossing_type": "port",
                "shared_border_km": "0.5",
                "source_lineage": '["test"]',
            },
            {
                "from_province_id": "land_c",
                "to_province_id": "land_d",
                "adjacency_type": "land",
                "bidirectional": "true",
                "crossing_type": "shared_border",
                "shared_border_km": "1.0",
                "source_lineage": '["test"]',
            },
        ],
    )

    result = build_beta_release(
        "modern-small",
        province_input=province_input,
        sea_input=sea_input,
        adjacency_input=adjacency_input,
        output_dir=output_dir,
        release_tag="beta-test",
        scenarios=("modern-baseline", "official-1836", "official-1444"),
        sample_countries=("FRA", "DEU"),
        allow_unknown_overrides=True,
    )

    assert result.release_tag == "beta-test"
    assert result.is_sample is True
    assert result.sample_countries == ("FRA", "DEU")
    assert result.province_count == 3
    assert result.sea_zone_count == 1
    assert result.adjacency_count == 2
    assert result.geometry_quality_tier == BETA_GEOMETRY_TIER
    assert result.politics_quality_tier == QUALITY_TIER_CURATED_POLITICS
    assert result.license_audit_passed is True
    assert result.atlas_dir
    assert result.attribution_record_count >= 1

    manifest_path = Path(result.release_manifest)
    assert manifest_path.is_file()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    validate_release_manifest(manifest)
    assert manifest["milestone"] == "M14"
    assert manifest["release_channel"] == "beta"
    assert manifest["license_audit_passed"] is True
    assert manifest["quality_tiers"]["geometry"] == "scaffold-baseline"
    assert manifest["quality_tiers"]["politics"] == "curated-politics"
    assert set(manifest["scenario_set"]) == {
        "modern-baseline",
        "official-1836",
        "official-1444",
    }
    assert "game" in manifest["faces"]
    assert "atlas" in manifest["faces"]

    assert (output_dir / "LICENSE_AUDIT.md").is_file()
    assert (output_dir / "license_audit.json").is_file()
    assert (output_dir / "ACCURACY.md").is_file()
    assert (output_dir / "accuracy_label.json").is_file()
    assert (output_dir / "RECIPE.md").is_file()
    assert (output_dir / "recipe.json").is_file()
    assert (output_dir / "attribution.json").is_file()
    assert (output_dir / "README.md").is_file()
    assert (output_dir / "sample" / "provinces.geojson").is_file()
    assert (output_dir / "pack" / "pack_manifest.json").is_file()
    assert (output_dir / "pack" / "scenarios" / "modern-baseline" / "ownership.csv").is_file()
    assert (output_dir / "pack" / "scenarios" / "official-1836" / "ownership.csv").is_file()
    assert (output_dir / "pack" / "scenarios" / "official-1444" / "ownership.csv").is_file()
    assert (output_dir / "atlas" / "atlas_manifest.json").is_file()
    assert (output_dir / "atlas" / "geojson" / "ownership_choropleth.geojson").is_file() or any(
        (output_dir / "atlas").rglob("*.geojson")
    )

    audit = json.loads((output_dir / "license_audit.json").read_text(encoding="utf-8"))
    validate_license_audit_report(audit)
    assert audit["passed"] is True
    assert "gadm" in audit["restricted_source_ids"]
    assert "openstreetmap" in audit["isolated_source_ids"]

    attribution = json.loads((output_dir / "attribution.json").read_text(encoding="utf-8"))
    assert attribution["pack_type"] == "license-audited"
    assert attribution["release_channel"] == "beta"
    assert attribution["records"]

    accuracy = json.loads((output_dir / "accuracy_label.json").read_text(encoding="utf-8"))
    assert accuracy["release_channel"] == "beta"
    assert accuracy["politics_quality_tier"] == "curated-politics"


def test_build_beta_release_scaffold_politics_without_official(tmp_path):
    province_input = tmp_path / "provinces.geojson"
    output_dir = tmp_path / "scaffold-only"
    _write_provinces(
        province_input,
        [
            _land_feature("land_a", _polygon(0, 0, 1, 1), country="FRA"),
        ],
    )
    result = build_beta_release(
        "modern-small",
        province_input=province_input,
        output_dir=output_dir,
        release_tag="beta-scaffold",
        scenarios=("modern-baseline",),
        include_atlas=True,
        allow_unknown_overrides=True,
    )
    assert result.politics_quality_tier == QUALITY_TIER_SCAFFOLD_BASELINE
    assert result.license_audit_passed is True
    assert Path(result.atlas_dir).is_dir()


def test_build_beta_release_rejects_dirty_lineage(tmp_path):
    province_input = tmp_path / "provinces.geojson"
    output_dir = tmp_path / "dirty"
    _write_provinces(
        province_input,
        [
            {
                "type": "Feature",
                "geometry": _polygon(0, 0, 1, 1),
                "properties": {
                    "province_id": "land_a",
                    "display_name": "Dirty",
                    "kind": "land",
                    "parent_country_id": "FRA",
                    "parent_region_id": "FR-IDF",
                    "area_sq_km": 1000.0,
                    "estimated_population": 5000.0,
                    "terrain_class": "plains",
                    "coastal": False,
                    "island": False,
                    "source_lineage": ["gadm:admin1"],
                    "license_lineage": ["GADM restricted"],
                },
            }
        ],
    )
    with pytest.raises(Exception) as exc_info:
        build_beta_release(
            "modern-small",
            province_input=province_input,
            output_dir=output_dir,
            release_tag="beta-dirty",
            scenarios=(),
            include_atlas=False,
            fail_on_license_errors=True,
        )
    assert "License audit" in str(exc_info.value) or "Forbidden" in str(exc_info.value)


def test_release_beta_cli_json(tmp_path, capsys):
    province_input = tmp_path / "provinces.geojson"
    output_dir = tmp_path / "cli-out"
    _write_provinces(
        province_input,
        [
            _land_feature("land_a", _polygon(0, 0, 1, 1), country="FRA"),
            _land_feature("land_b", _polygon(1, 0, 2, 1), country="DEU"),
        ],
    )
    assert (
        main(
            [
                "release",
                "beta",
                "--profile",
                "modern-small",
                "--province-input",
                str(province_input),
                "--output-dir",
                str(output_dir),
                "--tag",
                "beta-cli",
                "--country",
                "FRA",
                "--scenario",
                "modern-baseline",
                "--allow-unknown-overrides",
                "--format",
                "json",
            ]
        )
        == 0
    )
    summary = json.loads(capsys.readouterr().out)
    assert summary["release_tag"] == "beta-cli"
    assert summary["province_count"] == 1
    assert summary["is_sample"] is True
    assert summary["license_audit_passed"] is True
    assert summary["politics_quality_tier"] == "scaffold-baseline"
    assert Path(summary["release_manifest"]).is_file()
    assert (output_dir / "LICENSE_AUDIT.md").is_file()
    assert (output_dir / "atlas").is_dir()
    assert (output_dir / "pack").is_dir()


def test_release_beta_cli_no_atlas(tmp_path, capsys):
    province_input = tmp_path / "provinces.geojson"
    output_dir = tmp_path / "no-atlas"
    _write_provinces(
        province_input,
        [_land_feature("land_a", _polygon(0, 0, 1, 1), country="FRA")],
    )
    assert (
        main(
            [
                "release",
                "beta",
                "--province-input",
                str(province_input),
                "--output-dir",
                str(output_dir),
                "--tag",
                "beta-no-atlas",
                "--scenario",
                "modern-baseline",
                "--no-atlas",
                "--allow-unknown-overrides",
                "--format",
                "json",
            ]
        )
        == 0
    )
    summary = json.loads(capsys.readouterr().out)
    assert summary["atlas_dir"] == ""
    assert not (output_dir / "atlas").exists()
    assert (output_dir / "pack").is_dir()


def test_validate_license_audit_report_rejects_bad_type():
    report = {
        "schema_version": "0.1.0",
        "report_type": "not-audit",
        "milestone": "M14",
        "passed": True,
        "profile_id": "modern-small",
        "release_channel": "beta",
        "error_count": 0,
        "warning_count": 0,
        "public_source_ids": [],
        "isolated_source_ids": [],
        "restricted_source_ids": [],
        "findings": [],
        "attribution_records": [],
    }
    with pytest.raises(SchemaValidationError):
        validate_license_audit_report(report)


def _write_provinces(path: Path, features: list[dict]) -> None:
    path.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "name": "provinces",
                "gpm": {"profile_id": "modern-small", "id_scheme": "test"},
                "features": features,
            }
        ),
        encoding="utf-8",
    )


def _write_seas(path: Path, features: list[dict]) -> None:
    path.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "name": "sea_zones",
                "gpm": {"profile_id": "modern-small", "milestone": "M6"},
                "features": features,
            }
        ),
        encoding="utf-8",
    )


def _write_adjacency(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "from_province_id",
        "to_province_id",
        "adjacency_type",
        "bidirectional",
        "crossing_type",
        "shared_border_km",
        "source_lineage",
    ]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _land_feature(
    province_id: str,
    geometry: dict,
    *,
    name: str | None = None,
    region: str = "REG-1",
    country: str = "AAA",
) -> dict:
    return {
        "type": "Feature",
        "geometry": geometry,
        "properties": {
            "province_id": province_id,
            "display_name": name or province_id,
            "kind": "land",
            "parent_country_id": country,
            "parent_region_id": region,
            "area_sq_km": 1000.0,
            "estimated_population": 5000.0,
            "terrain_class": "plains",
            "coastal": False,
            "island": False,
            "source_lineage": [f"natural_earth:admin1:{province_id}"],
            "license_lineage": ["Natural Earth public domain"],
        },
    }


def _sea_feature(province_id: str, geometry: dict, *, parent: str) -> dict:
    return {
        "type": "Feature",
        "geometry": geometry,
        "properties": {
            "province_id": province_id,
            "display_name": f"Waters of {parent}",
            "kind": "sea",
            "parent_country_id": "FRA",
            "parent_region_id": "FR-IDF",
            "area_sq_km": 250.0,
            "estimated_population": None,
            "terrain_class": "ocean",
            "coastal": False,
            "island": False,
            "sea_class": "coastal",
            "parent_land_province_id": parent,
            "source_lineage": [f"natural_earth:land:{province_id}"],
            "license_lineage": ["Natural Earth public domain"],
        },
    }


def _polygon(minx: float, miny: float, maxx: float, maxy: float) -> dict:
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [minx, miny],
                [maxx, miny],
                [maxx, maxy],
                [minx, maxy],
                [minx, miny],
            ]
        ],
    }
