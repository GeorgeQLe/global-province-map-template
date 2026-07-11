import json

import pytest
from shapely.geometry import shape
from shapely.ops import unary_union

from gpm.builders.refinement import (
    ProvinceRefinementError,
    RefinementSettings,
    refine_land_provinces,
)


def test_population_weighted_refinement_is_deterministic_and_conserves_inputs(tmp_path):
    provinces = [
        _province("ne_aaa-one-000000000001", "AAA", "AAA-1", 0, 0, 1, 1),
        _province("ne_bbb-two-000000000002", "BBB", "BBB-1", 2, 0, 3, 1),
    ]
    population_path = _write_points(
        tmp_path / "population.geojson",
        [
            ("dense", 0.2, 0.5, 1_000),
            ("sparse", 2.5, 0.5, 10),
        ],
        lineage=["worldpop:test-fixture"],
        licenses=["WorldPop CC BY 4.0 test fixture"],
    )
    settlement_path = _write_points(
        tmp_path / "settlements.geojson",
        [
            ("capital", 0.8, 0.5, 500),
            ("town", 2.5, 0.5, 10),
        ],
        lineage=["settlements:test-fixture"],
        licenses=["Settlement test fixture license"],
    )
    settings = RefinementSettings(
        target_province_count=4,
        population_weight=0.75,
        min_area_sq_km=1,
        min_population=1,
        max_split_parts=8,
        max_seed_candidates=32,
    )

    first = refine_land_provinces(
        provinces,
        settings=settings,
        population_input=population_path,
        settlement_input=settlement_path,
    )
    second = refine_land_provinces(
        list(reversed(provinces)),
        settings=settings,
        population_input=population_path,
        settlement_input=settlement_path,
    )

    assert first.features == second.features
    assert len(first.features) == 4
    assert first.split_count == 2
    assert first.split_parent_count == 1
    assert first.merged_fragment_count == 0
    assert first.population_total == pytest.approx(1_010)
    assert first.population_sample_count == 2
    assert first.settlement_count == 2
    assert first.strategy == "population-weighted-voronoi"
    assert "worldpop:test-fixture" in first.source_lineage
    assert "WorldPop CC BY 4.0 test fixture" in first.license_lineage

    output_geometries = [shape(feature["geometry"]) for feature in first.features]
    input_geometry = unary_union([shape(feature["geometry"]) for feature in provinces])
    assert unary_union(output_geometries).symmetric_difference(input_geometry).area == pytest.approx(0)
    assert sum(geometry.area for geometry in output_geometries) == pytest.approx(input_geometry.area)
    assert sum(feature["properties"]["estimated_population"] for feature in first.features) == pytest.approx(
        1_010
    )
    assert sum(feature["properties"]["settlement_count"] for feature in first.features) == 2
    split_features = [
        feature
        for feature in first.features
        if feature["properties"]["refinement_parent_id"] == "ne_aaa-one-000000000001"
    ]
    assert len(split_features) == 3
    assert all(feature["properties"]["province_id"].startswith("m4_") for feature in split_features)
    assert [feature["properties"]["province_id"] for feature in first.features] == sorted(
        feature["properties"]["province_id"] for feature in first.features
    )


def test_refinement_merges_tiny_generated_sibling_fragments(tmp_path):
    provinces = [_province("ne_aaa-one-000000000001", "AAA", "AAA-1", 0, 0, 1, 1)]
    population_path = _write_points(
        tmp_path / "population.geojson",
        [("only", 0.1, 0.5, 10)],
    )
    settings = RefinementSettings(
        target_province_count=2,
        population_weight=1,
        min_area_sq_km=20_000,
        min_population=1_000,
        max_split_parts=4,
        max_seed_candidates=16,
    )

    result = refine_land_provinces(
        provinces,
        settings=settings,
        population_input=population_path,
        population_license_lineage=("Population test fixture license",),
    )

    assert result.split_count == 1
    assert result.merged_fragment_count == 1
    assert len(result.features) == 1
    assert shape(result.features[0]["geometry"]).symmetric_difference(
        shape(provinces[0]["geometry"])
    ).area == pytest.approx(0)
    assert result.features[0]["properties"]["estimated_population"] == pytest.approx(10)


def test_refinement_sums_georeferenced_population_raster(tmp_path):
    numpy = pytest.importorskip("numpy")
    rasterio = pytest.importorskip("rasterio")
    from rasterio.transform import from_bounds
    from rasterio.warp import transform_bounds

    raster_path = tmp_path / "population.tif"
    bounds = transform_bounds("EPSG:4326", "EPSG:3857", 0, 0, 2, 1)
    with rasterio.open(
        raster_path,
        "w",
        driver="GTiff",
        width=2,
        height=1,
        count=1,
        dtype="float32",
        crs="EPSG:3857",
        transform=from_bounds(*bounds, width=2, height=1),
        nodata=-9999,
    ) as dataset:
        dataset.write(numpy.array([[100, 25]], dtype="float32"), 1)

    result = refine_land_provinces(
        [_province("ne_aaa-one-000000000001", "AAA", "AAA-1", 0, 0, 2, 1)],
        settings=RefinementSettings(
            target_province_count=2,
            population_weight=1,
            min_area_sq_km=1,
            min_population=0,
            max_split_parts=4,
            max_seed_candidates=16,
        ),
        population_input=raster_path,
        population_license_lineage=("Raster fixture license",),
    )

    assert len(result.features) == 2
    assert result.population_total == pytest.approx(125)
    assert sum(feature["properties"]["estimated_population"] for feature in result.features) == pytest.approx(
        125
    )
    assert all(
        feature["properties"]["population_estimation_method"] == "population-raster-cell-sum"
        for feature in result.features
    )
    assert "Raster fixture license" in result.license_lineage


def test_refinement_rejects_population_points_without_values(tmp_path):
    path = tmp_path / "invalid.geojson"
    path.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [0.5, 0.5]},
                        "properties": {},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ProvinceRefinementError, match="requires a non-negative population/value field"):
        refine_land_provinces(
            [_province("ne_aaa-one-000000000001", "AAA", "AAA-1", 0, 0, 1, 1)],
            settings=RefinementSettings(1, 1, 0, 0, 2, 4),
            population_input=path,
        )


def test_refinement_preserves_and_reports_invalid_source_geometry():
    invalid = _province("ne_aaa-invalid-000000000001", "AAA", "AAA-1", 0, 0, 1, 1)
    invalid["geometry"]["coordinates"] = [
        [[0, 0], [1, 1], [1, 0], [0, 1], [0, 0]]
    ]
    valid = _province("ne_bbb-valid-000000000002", "BBB", "BBB-1", 2, 0, 3, 1)

    result = refine_land_provinces(
        [invalid, valid],
        settings=RefinementSettings(3, 0, 0, 0, 4, 8),
    )

    assert result.skipped_invalid_count == 1
    preserved = next(
        feature
        for feature in result.features
        if feature["properties"]["province_id"] == "ne_aaa-invalid-000000000001"
    )
    assert preserved["geometry"] == invalid["geometry"]
    assert preserved["properties"]["refinement_strategy"] == "source-geometry-preserved"
    assert preserved["properties"]["refinement_skipped_reason"] == "invalid-source-geometry"


def test_refinement_requires_population_license_lineage(tmp_path):
    population_path = _write_points(
        tmp_path / "population.geojson",
        [("sample", 0.5, 0.5, 10)],
    )

    with pytest.raises(ProvinceRefinementError, match="license_lineage"):
        refine_land_provinces(
            [_province("ne_aaa-one-000000000001", "AAA", "AAA-1", 0, 0, 1, 1)],
            settings=RefinementSettings(1, 1, 0, 0, 2, 4),
            population_input=population_path,
        )


def _province(province_id, country_id, region_id, min_x, min_y, max_x, max_y):
    return {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [min_x, min_y],
                    [max_x, min_y],
                    [max_x, max_y],
                    [min_x, max_y],
                    [min_x, min_y],
                ]
            ],
        },
        "properties": {
            "province_id": province_id,
            "display_name": region_id,
            "kind": "land",
            "parent_region_id": region_id,
            "parent_country_id": country_id,
            "area_sq_km": 0,
            "estimated_population": None,
            "terrain_class": "unclassified",
            "coastal": False,
            "island": False,
            "source_lineage": ["natural-earth:test"],
            "license_lineage": ["Natural Earth public domain"],
            "source_layer": "admin1_states_provinces",
        },
    }


def _write_points(path, records, *, lineage=None, licenses=None):
    path.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "gpm": {
                    "source_lineage": lineage or [],
                    "license_lineage": licenses or [],
                },
                "features": [
                    {
                        "type": "Feature",
                        "id": identifier,
                        "geometry": {"type": "Point", "coordinates": [longitude, latitude]},
                        "properties": {"population": population},
                    }
                    for identifier, longitude, latitude, population in records
                ],
            }
        ),
        encoding="utf-8",
    )
    return path
