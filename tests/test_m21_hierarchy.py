"""M21 hierarchy builder: areas, regions, superregions."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from gpm.builders.adjacency import build_land_adjacency
from gpm.builders.hierarchy import HierarchyBuildError, build_hierarchy
from gpm.cli import main
from gpm.config import ConfigError, hierarchy_settings, load_profile
from gpm.exporters import export_game_pack, export_hierarchy_layers
from gpm.schemas import load_schema


def _grid_province(pid: str, admin1: str, country: str, minx: float, miny: float,
                   maxx: float, maxy: float) -> dict:
    return {
        "type": "Feature",
        "properties": {
            "province_id": pid,
            "display_name": pid.replace("_", " ").title(),
            "kind": "land",
            "parent_region_id": admin1,
            "parent_country_id": country,
            "area_sq_km": 100.0,
            "estimated_population": None,
            "terrain_class": "unclassified",
            "coastal": False,
            "island": False,
            "source_lineage": ["test:fixture"],
            "license_lineage": ["Test public domain"],
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [[minx, miny], [maxx, miny], [maxx, maxy], [minx, maxy], [minx, miny]]
            ],
        },
    }


def _write_fixture_world(tmp_path: Path, *, split_province: bool = False) -> tuple[Path, Path]:
    """A 4x3 admin-1 grid country (AAA) plus a single-admin1 neighbour (BBB).

    With ``split_province``, one AAA province is divided into two half-squares
    that inherit the same parent_region_id — simulating an M4 density split.
    """
    features = []
    for row in range(3):
        for col in range(4):
            admin1 = f"AA-{row}{col}"
            pid = f"prov_aaa_{row}{col}"
            minx, miny = float(col), float(row)
            if split_province and row == 0 and col == 0:
                features.append(
                    _grid_province(f"{pid}_west", admin1, "AAA", minx, miny, minx + 0.5, miny + 1)
                )
                features.append(
                    _grid_province(f"{pid}_east", admin1, "AAA", minx + 0.5, miny, minx + 1, miny + 1)
                )
            else:
                features.append(_grid_province(pid, admin1, "AAA", minx, miny, minx + 1, miny + 1))
    # BBB sits east of the grid, sharing a border with AAA's last column.
    features.append(_grid_province("prov_bbb_00", "BB-00", "BBB", 4.0, 0.0, 5.0, 1.0))

    province_input = tmp_path / "provinces.geojson"
    province_input.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "name": "provinces",
                "gpm": {"schema_version": "0.1.0", "profile_id": "modern-small"},
                "features": features,
            }
        ),
        encoding="utf-8",
    )
    adjacency_output = tmp_path / "adjacency.csv"
    build_land_adjacency(
        "modern-small", province_input=province_input, output=adjacency_output
    )
    return province_input, adjacency_output


def _hierarchy_features(path: Path, region_type: str) -> list[dict]:
    document = json.loads(path.read_text(encoding="utf-8"))
    return [
        feature
        for feature in document["features"]
        if feature["properties"]["region_type"] == region_type
    ]


def test_hierarchy_builds_areas_regions_superregions(tmp_path):
    province_input, adjacency_input = _write_fixture_world(tmp_path)
    output = tmp_path / "hierarchy.geojson"
    result = build_hierarchy(
        "modern-small",
        province_input=province_input,
        adjacency_input=adjacency_input,
        raw_dir=tmp_path / "missing-raw",
        output=output,
    )
    assert result.province_count == 13
    assert result.area_count >= 2
    assert result.region_count == 2  # one per country (no NE attrs)
    assert result.superregion_count == 1
    assert result.natural_earth_attributes is False

    areas = _hierarchy_features(output, "area")
    settings = hierarchy_settings(load_profile("modern-small"))
    aaa_areas = [a for a in areas if a["properties"]["parent_country_id"] == "AAA"]
    assert len(aaa_areas) == 2
    for area in aaa_areas:
        assert settings["area_min_size"] <= len(area["properties"]["admin1_codes"]) <= settings["area_max_size"]
    # Areas never cross countries.
    for area in areas:
        countries = {code.split("-")[0] for code in area["properties"]["admin1_codes"]}
        assert len(countries) == 1

    # Full province coverage, exactly once.
    covered = [pid for area in areas for pid in area["properties"]["province_ids"]]
    assert sorted(covered) == sorted(set(covered))
    assert len(covered) == 13

    # Parent chains resolve.
    regions = {f["properties"]["region_id"]: f for f in _hierarchy_features(output, "region")}
    superregions = {f["properties"]["region_id"]: f for f in _hierarchy_features(output, "superregion")}
    for area in areas:
        region_id = area["properties"]["parent_region_id"]
        assert region_id in regions
        assert area["properties"]["parent_superregion_id"] in superregions
        assert area["properties"]["region_id"] in regions[region_id]["properties"]["member_region_ids"]


def test_hierarchy_enriches_provinces_in_place(tmp_path):
    province_input, adjacency_input = _write_fixture_world(tmp_path)
    output = tmp_path / "hierarchy.geojson"
    build_hierarchy(
        "modern-small",
        province_input=province_input,
        adjacency_input=adjacency_input,
        raw_dir=tmp_path / "missing-raw",
        output=output,
    )
    document = json.loads(province_input.read_text(encoding="utf-8"))
    assert document["gpm"]["hierarchy"]["updated_province_count"] == 13
    for feature in document["features"]:
        properties = feature["properties"]
        assert properties["parent_area_id"].startswith("ar_")
        assert properties["parent_geo_region_id"].startswith("rg_")
        assert properties["parent_superregion_id"].startswith("sr_")
        # The original admin-1 linkage is preserved, not repurposed.
        assert properties["parent_region_id"].startswith(("AA-", "BB-"))


def test_hierarchy_is_deterministic_across_reruns(tmp_path):
    province_input, adjacency_input = _write_fixture_world(tmp_path)
    out_a = tmp_path / "hierarchy_a.geojson"
    out_b = tmp_path / "hierarchy_b.geojson"
    for out in (out_a, out_b):
        build_hierarchy(
            "modern-small",
            province_input=province_input,
            adjacency_input=adjacency_input,
            raw_dir=tmp_path / "missing-raw",
            output=out,
            update_provinces=False,
        )
    doc_a = json.loads(out_a.read_text(encoding="utf-8"))
    doc_b = json.loads(out_b.read_text(encoding="utf-8"))
    # Everything except the generation timestamp is byte-identical.
    doc_a["gpm"].pop("generated_at")
    doc_b["gpm"].pop("generated_at")
    assert json.dumps(doc_a, sort_keys=True) == json.dumps(doc_b, sort_keys=True)


def test_area_ids_stable_under_simulated_m4_split(tmp_path):
    baseline_dir = tmp_path / "baseline"
    split_dir = tmp_path / "split"
    baseline_dir.mkdir()
    split_dir.mkdir()
    province_a, adjacency_a = _write_fixture_world(baseline_dir)
    province_b, adjacency_b = _write_fixture_world(split_dir, split_province=True)

    out_a = baseline_dir / "hierarchy.geojson"
    out_b = split_dir / "hierarchy.geojson"
    build_hierarchy(
        "modern-small",
        province_input=province_a,
        adjacency_input=adjacency_a,
        raw_dir=tmp_path / "missing-raw",
        output=out_a,
    )
    build_hierarchy(
        "modern-small",
        province_input=province_b,
        adjacency_input=adjacency_b,
        raw_dir=tmp_path / "missing-raw",
        output=out_b,
    )

    ids_a = sorted(f["properties"]["region_id"] for f in _hierarchy_features(out_a, "area"))
    ids_b = sorted(f["properties"]["region_id"] for f in _hierarchy_features(out_b, "area"))
    assert ids_a == ids_b

    # Split children land in the same area their parent occupied.
    enriched = json.loads(province_b.read_text(encoding="utf-8"))
    by_id = {f["properties"]["province_id"]: f["properties"] for f in enriched["features"]}
    parent_area_baseline = {
        f["properties"]["province_id"]: f["properties"]["parent_area_id"]
        for f in json.loads(province_a.read_text(encoding="utf-8"))["features"]
    }
    expected_area = parent_area_baseline["prov_aaa_00"]
    assert by_id["prov_aaa_00_west"]["parent_area_id"] == expected_area
    assert by_id["prov_aaa_00_east"]["parent_area_id"] == expected_area


def test_hierarchy_features_satisfy_region_entity_schema(tmp_path):
    province_input, adjacency_input = _write_fixture_world(tmp_path)
    output = tmp_path / "hierarchy.geojson"
    build_hierarchy(
        "modern-small",
        province_input=province_input,
        adjacency_input=adjacency_input,
        raw_dir=tmp_path / "missing-raw",
        output=output,
        update_provinces=False,
    )
    schema = load_schema("region-entity")
    required = schema["properties"]["properties"]["required"]
    allowed_types = set(schema["properties"]["properties"]["properties"]["region_type"]["enum"])
    document = json.loads(output.read_text(encoding="utf-8"))
    assert document["features"], "hierarchy must emit features"
    for feature in document["features"]:
        assert feature["type"] == "Feature"
        assert isinstance(feature["geometry"], dict)
        properties = feature["properties"]
        for key in required:
            assert key in properties, f"missing {key}"
        assert properties["region_type"] in allowed_types
        assert properties["province_count"] == len(properties["province_ids"])
        assert isinstance(properties["label_point"], list) and len(properties["label_point"]) == 2


def test_pack_export_prefers_hierarchy_and_falls_back(tmp_path):
    province_input, adjacency_input = _write_fixture_world(tmp_path)
    hierarchy_output = tmp_path / "hierarchy.geojson"
    build_hierarchy(
        "modern-small",
        province_input=province_input,
        adjacency_input=adjacency_input,
        raw_dir=tmp_path / "missing-raw",
        output=hierarchy_output,
        update_provinces=False,
    )

    # hierarchy.geojson lives next to the provinces → preferred automatically.
    pack_dir = tmp_path / "pack-hierarchy"
    export_game_pack(
        "modern-small",
        province_input=province_input,
        adjacency_input=adjacency_input,
        output_dir=pack_dir,
    )
    regions_doc = json.loads((pack_dir / "geojson" / "regions.geojson").read_text(encoding="utf-8"))
    assert regions_doc["gpm"]["id_scheme"] == "hierarchy-sha256-v1"
    assert all(
        f["properties"]["region_id"].startswith("rg_") for f in regions_doc["features"]
    )

    # Without hierarchy.geojson the legacy parent_region_id dissolve remains.
    fallback_root = tmp_path / "fallback"
    fallback_root.mkdir()
    fallback_provinces = fallback_root / "provinces.geojson"
    fallback_provinces.write_text(province_input.read_text(encoding="utf-8"), encoding="utf-8")
    (fallback_root / "adjacency.csv").write_text(
        adjacency_input.read_text(encoding="utf-8"), encoding="utf-8"
    )
    pack_dir_fallback = tmp_path / "pack-fallback"
    export_game_pack(
        "modern-small",
        province_input=fallback_provinces,
        output_dir=pack_dir_fallback,
    )
    fallback_doc = json.loads(
        (pack_dir_fallback / "geojson" / "regions.geojson").read_text(encoding="utf-8")
    )
    assert fallback_doc["gpm"]["id_scheme"] == "parent-region-id-v1"
    region_ids = {f["properties"]["region_id"] for f in fallback_doc["features"]}
    assert "AA-00" in region_ids


def test_export_hierarchy_layers_writes_slim_overlays(tmp_path):
    province_input, adjacency_input = _write_fixture_world(tmp_path)
    hierarchy_output = tmp_path / "hierarchy.geojson"
    build_hierarchy(
        "modern-small",
        province_input=province_input,
        adjacency_input=adjacency_input,
        raw_dir=tmp_path / "missing-raw",
        output=hierarchy_output,
        update_provinces=False,
    )
    result = export_hierarchy_layers(hierarchy_output, tmp_path / "layers")
    assert result.area_count >= 2
    assert result.region_count == 2
    assert result.superregion_count == 1
    assert set(result.files_written) == {"areas.geojson", "regions.geojson", "superregions.geojson"}
    areas_doc = json.loads((tmp_path / "layers" / "areas.geojson").read_text(encoding="utf-8"))
    for feature in areas_doc["features"]:
        properties = feature["properties"]
        assert properties["area_color"].startswith("#")
        assert isinstance(properties["label_point"], list)
        assert "province_ids" not in properties  # heavy lists stay in the build artifact
        assert feature["geometry"]["type"] in {"Polygon", "MultiPolygon"}


def test_hierarchy_cli_runs_and_reports(tmp_path, capsys):
    province_input, adjacency_input = _write_fixture_world(tmp_path)
    code = main(
        [
            "build",
            "hierarchy",
            "--profile",
            "modern-small",
            "--province-input",
            str(province_input),
            "--adjacency-input",
            str(adjacency_input),
            "--raw-dir",
            str(tmp_path / "missing-raw"),
            "--output",
            str(tmp_path / "hierarchy.geojson"),
            "--format",
            "json",
        ]
    )
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["area_count"] >= 2
    assert payload["updated_province_count"] == 13


def test_province_enrichment_write_is_atomic(tmp_path, monkeypatch):
    province_input, adjacency_input = _write_fixture_world(tmp_path)
    original_payload = province_input.read_text(encoding="utf-8")

    from pathlib import Path as _Path

    real_write_text = _Path.write_text

    def failing_write_text(self, *args, **kwargs):
        if self.name.startswith("provinces.geojson"):
            raise OSError("disk full")
        return real_write_text(self, *args, **kwargs)

    monkeypatch.setattr(_Path, "write_text", failing_write_text)
    with pytest.raises(OSError):
        build_hierarchy(
            "modern-small",
            province_input=province_input,
            adjacency_input=adjacency_input,
            raw_dir=tmp_path / "missing-raw",
            output=tmp_path / "hierarchy.geojson",
        )
    monkeypatch.undo()
    # The in-place target survives untouched; no temp file left behind.
    assert province_input.read_text(encoding="utf-8") == original_payload
    assert not (tmp_path / "provinces.geojson.tmp").exists()
    json.loads(province_input.read_text(encoding="utf-8"))


def test_hierarchy_requires_inputs(tmp_path):
    with pytest.raises(HierarchyBuildError):
        build_hierarchy(
            "modern-small",
            province_input=tmp_path / "missing.geojson",
            adjacency_input=tmp_path / "missing.csv",
            raw_dir=tmp_path,
            output=tmp_path / "hierarchy.geojson",
        )


def test_hierarchy_settings_validation():
    profile = load_profile("modern-small")
    settings = hierarchy_settings(profile)
    assert settings["area_min_size"] <= settings["area_target_size"] <= settings["area_max_size"]
    with pytest.raises(ConfigError):
        hierarchy_settings({"hierarchy": {"area_target_size": 0}})
    with pytest.raises(ConfigError):
        hierarchy_settings({"hierarchy": {"area_target_size": 99}})
