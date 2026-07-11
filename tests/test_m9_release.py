import csv
import json
from pathlib import Path

from gpm.cli import main
from gpm.release import (
    ALPHA_GEOMETRY_TIER,
    ALPHA_POLITICS_TIER,
    QUALITY_TIERS,
    accuracy_label,
    accuracy_markdown,
    build_alpha_release,
    modern_scaffold_recipe,
    recipe_markdown,
)
from gpm.release.sample import (
    filter_adjacency,
    filter_provinces_by_countries,
    filter_seas_for_land,
)
from gpm.schemas import validate_release_manifest


def test_quality_tiers_and_accuracy_label():
    assert "scaffold-baseline" in QUALITY_TIERS
    label = accuracy_label(
        scenarios=("modern-baseline", "demo-1444"),
        profile_id="modern-small",
    )
    assert label["geometry_quality_tier"] == ALPHA_GEOMETRY_TIER
    assert label["politics_quality_tier"] == ALPHA_POLITICS_TIER
    assert label["geometry_quality_tier"] == "scaffold-baseline"
    assert any("demo-1444" in note for note in label["scenario_notes"])
    assert any("Paradox" in item for item in label["do_not_claim"])
    markdown = accuracy_markdown(label)
    assert "scaffold-baseline" in markdown
    assert "Do not claim" in markdown


def test_modern_scaffold_recipe_includes_release_step():
    recipe = modern_scaffold_recipe(
        profile_id="modern-small",
        scenarios=("modern-baseline",),
        sample_countries=("FRA", "DEU"),
        release_tag="alpha-test",
    )
    assert recipe["recipe_id"] == "alpha-modern-scaffold"
    assert recipe["milestone"] == "M9"
    step_ids = [step["id"] for step in recipe["steps"]]
    assert "download-sources" in step_ids
    assert "build-provinces" in step_ids
    assert "release-alpha" in step_ids
    release_step = next(step for step in recipe["steps"] if step["id"] == "release-alpha")
    assert "--country" in release_step["command"]
    assert "FRA" in release_step["command"]
    md = recipe_markdown(recipe)
    assert "uv run" in md
    assert "release alpha" in md


def test_sample_filters_country_seas_and_adjacency():
    land = [
        _land("land_fr", country="FRA"),
        _land("land_de", country="DEU"),
        _land("land_es", country="ESP"),
    ]
    seas = [
        _sea("sea_fr", parent="land_fr"),
        _sea("sea_es", parent="land_es"),
        _ocean("sea_ocean"),
    ]
    adj = [
        {
            "from_province_id": "land_de",
            "to_province_id": "land_fr",
            "adjacency_type": "land",
            "bidirectional": "true",
            "crossing_type": "shared_border",
            "shared_border_km": "1.0",
            "source_lineage": "[]",
        },
        {
            "from_province_id": "land_es",
            "to_province_id": "land_fr",
            "adjacency_type": "land",
            "bidirectional": "true",
            "crossing_type": "shared_border",
            "shared_border_km": "1.0",
            "source_lineage": "[]",
        },
        {
            "from_province_id": "land_fr",
            "to_province_id": "sea_fr",
            "adjacency_type": "port_to_sea",
            "bidirectional": "true",
            "crossing_type": "port",
            "shared_border_km": "0.5",
            "source_lineage": "[]",
        },
    ]
    selected = filter_provinces_by_countries(land, {"FRA", "DEU"})
    assert {f["properties"]["province_id"] for f in selected} == {"land_fr", "land_de"}
    land_ids = {"land_fr", "land_de"}
    seas_kept = filter_seas_for_land(seas, land_ids)
    assert {f["properties"]["province_id"] for f in seas_kept} == {"sea_fr"}
    keep = land_ids | {"sea_fr"}
    adj_kept = filter_adjacency(adj, keep)
    assert len(adj_kept) == 2
    endpoints = {
        (row["from_province_id"], row["to_province_id"]) for row in adj_kept
    }
    assert ("land_de", "land_fr") in endpoints
    assert ("land_fr", "sea_fr") in endpoints


def test_build_alpha_release_writes_bundle(tmp_path):
    province_input = tmp_path / "provinces.geojson"
    sea_input = tmp_path / "sea_zones.geojson"
    adjacency_input = tmp_path / "adjacency.csv"
    output_dir = tmp_path / "releases" / "alpha-test"

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

    result = build_alpha_release(
        "modern-small",
        province_input=province_input,
        sea_input=sea_input,
        adjacency_input=adjacency_input,
        output_dir=output_dir,
        release_tag="alpha-test",
        scenarios=("modern-baseline", "demo-1444"),
        sample_countries=("FRA", "DEU"),
        allow_unknown_overrides=True,
    )

    assert result.release_tag == "alpha-test"
    assert result.is_sample is True
    assert result.sample_countries == ("FRA", "DEU")
    assert result.province_count == 3  # FRA x2 + DEU
    assert result.sea_zone_count == 1
    assert result.adjacency_count == 2  # land_a-land_b + land_a-sea_a
    assert result.geometry_quality_tier == "scaffold-baseline"
    assert result.politics_quality_tier == "scaffold-baseline"

    manifest_path = Path(result.release_manifest)
    assert manifest_path.is_file()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    validate_release_manifest(manifest)
    assert manifest["milestone"] == "M9"
    assert manifest["release_channel"] == "alpha"
    assert manifest["quality_tiers"]["geometry"] == "scaffold-baseline"
    assert manifest["scenario_set"] == ["modern-baseline", "demo-1444"]
    assert manifest["is_sample"] is True
    assert set(manifest["sample_countries"]) == {"FRA", "DEU"}

    assert (output_dir / "ACCURACY.md").is_file()
    assert (output_dir / "accuracy_label.json").is_file()
    assert (output_dir / "RECIPE.md").is_file()
    assert (output_dir / "recipe.json").is_file()
    assert (output_dir / "attribution.json").is_file()
    assert (output_dir / "README.md").is_file()
    assert (output_dir / "sample" / "provinces.geojson").is_file()
    assert (output_dir / "pack" / "pack_manifest.json").is_file()
    assert (output_dir / "pack" / "definitions" / "provinces.json").is_file()
    assert (output_dir / "pack" / "scenarios" / "modern-baseline" / "ownership.csv").is_file()
    assert (output_dir / "pack" / "scenarios" / "demo-1444" / "ownership.csv").is_file()

    sample_provinces = json.loads(
        (output_dir / "sample" / "provinces.geojson").read_text(encoding="utf-8")
    )
    ids = {
        feature["properties"]["province_id"] for feature in sample_provinces["features"]
    }
    assert ids == {"land_a", "land_b", "land_c"}
    assert "land_d" not in ids

    accuracy = json.loads((output_dir / "accuracy_label.json").read_text(encoding="utf-8"))
    assert accuracy["geometry_quality_tier"] == "scaffold-baseline"
    assert "Paradox-grade" in " ".join(accuracy["do_not_claim"])


def test_build_alpha_release_full_input_without_country_filter(tmp_path):
    province_input = tmp_path / "provinces.geojson"
    output_dir = tmp_path / "full"
    _write_provinces(
        province_input,
        [
            _land_feature("land_a", _polygon(0, 0, 1, 1), country="FRA"),
            _land_feature("land_b", _polygon(1, 0, 2, 1), country="ESP"),
        ],
    )
    result = build_alpha_release(
        "modern-small",
        province_input=province_input,
        output_dir=output_dir,
        release_tag="alpha-full",
        scenarios=(),
        sample_countries=None,
    )
    assert result.is_sample is False
    assert result.province_count == 2
    assert result.scenario_ids == ()
    manifest = json.loads(Path(result.release_manifest).read_text(encoding="utf-8"))
    assert manifest["scenario_set"] == []
    assert manifest["is_sample"] is False


def test_release_alpha_cli_json(tmp_path, capsys):
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
                "alpha",
                "--profile",
                "modern-small",
                "--province-input",
                str(province_input),
                "--output-dir",
                str(output_dir),
                "--tag",
                "alpha-cli",
                "--country",
                "FRA",
                "--no-scenarios",
                "--format",
                "json",
            ]
        )
        == 0
    )
    summary = json.loads(capsys.readouterr().out)
    assert summary["release_tag"] == "alpha-cli"
    assert summary["province_count"] == 1
    assert summary["is_sample"] is True
    assert summary["sample_countries"] == ["FRA"]
    assert Path(summary["release_manifest"]).is_file()
    assert (output_dir / "ACCURACY.md").is_file()


def test_release_alpha_cli_missing_provinces(tmp_path, capsys):
    assert (
        main(
            [
                "release",
                "alpha",
                "--province-input",
                str(tmp_path / "missing.geojson"),
            ]
        )
        == 1
    )
    captured = capsys.readouterr()
    assert "does not exist" in captured.err
    assert "Traceback" not in captured.err


def test_release_alpha_cli_sample_we(tmp_path, capsys):
    province_input = tmp_path / "provinces.geojson"
    output_dir = tmp_path / "we-out"
    _write_provinces(
        province_input,
        [
            _land_feature("land_fr", _polygon(0, 0, 1, 1), country="FRA"),
            _land_feature("land_be", _polygon(1, 0, 2, 1), country="BEL"),
            _land_feature("land_es", _polygon(2, 0, 3, 1), country="ESP"),
        ],
    )
    assert (
        main(
            [
                "release",
                "alpha",
                "--province-input",
                str(province_input),
                "--output-dir",
                str(output_dir),
                "--sample-we",
                "--no-scenarios",
                "--tag",
                "alpha-we",
                "--format",
                "json",
            ]
        )
        == 0
    )
    summary = json.loads(capsys.readouterr().out)
    assert summary["province_count"] == 2
    assert "FRA" in summary["sample_countries"]
    assert "BEL" in summary["sample_countries"]


def test_validate_release_manifest_rejects_bad_tier():
    import pytest
    from gpm.schemas import SchemaValidationError

    manifest = {
        "schema_version": "0.1.0",
        "manifest_type": "release",
        "milestone": "M9",
        "release_channel": "alpha",
        "release_tag": "t",
        "data_vintage": "2026-07-10",
        "generated_at": "2026-07-10T00:00:00+00:00",
        "generator_version": "0.1.0",
        "profile_id": "modern-small",
        "scenario_set": [],
        "quality_tiers": {"geometry": "nope", "politics": "scaffold-baseline"},
        "is_sample": False,
        "counts": {"provinces": 0, "sea_zones": 0, "adjacency_rows": 0},
        "files": ["README.md"],
    }
    with pytest.raises(SchemaValidationError):
        validate_release_manifest(manifest)


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


def _land(province_id: str, *, country: str) -> dict:
    return {
        "type": "Feature",
        "geometry": _polygon(0, 0, 1, 1),
        "properties": {
            "province_id": province_id,
            "kind": "land",
            "parent_country_id": country,
        },
    }


def _sea(province_id: str, *, parent: str) -> dict:
    return {
        "type": "Feature",
        "geometry": _polygon(0, 0, 0.5, 0.5),
        "properties": {
            "province_id": province_id,
            "kind": "sea",
            "sea_class": "coastal",
            "parent_land_province_id": parent,
        },
    }


def _ocean(province_id: str) -> dict:
    return {
        "type": "Feature",
        "geometry": _polygon(10, 10, 20, 20),
        "properties": {
            "province_id": province_id,
            "kind": "sea",
            "sea_class": "ocean",
            "parent_land_province_id": None,
        },
    }


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
            "source_lineage": [f"source:{province_id}"],
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
            "source_lineage": [f"source:{province_id}"],
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
