import re

import pytest

from gpm.builders.provinces import (
    ProvinceBuildError,
    _ensure_unique_province_ids,
    _province_feature,
    _province_id,
)


def test_source_geometry_ids_ignore_ring_and_multipart_representation_order():
    ring_a = [[0, 0], [2, 0], [2, 1], [0, 1], [0, 0]]
    ring_b = [[3, 0], [4, 0], [4, 1], [3, 1], [3, 0]]
    polygon = {"type": "Polygon", "coordinates": [ring_a]}
    reversed_polygon = {"type": "Polygon", "coordinates": [list(reversed(ring_a))]}
    rotated_polygon = {"type": "Polygon", "coordinates": [[*ring_a[2:-1], *ring_a[:3]]]}
    multipart = {"type": "MultiPolygon", "coordinates": [[ring_a], [ring_b]]}
    reordered_multipart = {
        "type": "MultiPolygon",
        "coordinates": [[list(reversed(ring_b))], [list(reversed(ring_a))]],
    }

    kwargs = {"source_layer": "admin1_states_provinces", "country_id": "AAA", "region_id": "AAA-1"}
    expected = _province_id(polygon, **kwargs)
    assert _province_id(reversed_polygon, **kwargs) == expected
    assert _province_id(rotated_polygon, **kwargs) == expected
    assert _province_id(multipart, **kwargs) == _province_id(reordered_multipart, **kwargs)
    assert re.fullmatch(r"ne_aaa-aaa-1-[0-9a-f]{12}", expected)


def test_source_geometry_ids_change_with_geometry_but_not_display_name():
    geometry = {
        "type": "Polygon",
        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
    }
    changed = {
        "type": "Polygon",
        "coordinates": [[[0, 0], [1.1, 0], [1, 1], [0, 1], [0, 0]]],
    }
    kwargs = {"source_layer": "admin1_states_provinces", "country_id": "AAA", "region_id": "AAA-1"}
    assert _province_id(geometry, **kwargs) != _province_id(changed, **kwargs)

    first = _province_feature(
        geometry,
        {"name": "Old name", "adm0_a3": "AAA", "iso_3166_2": "AAA-1"},
        source_layer="admin1_states_provinces",
        source_lineage=("source:a",),
        license_lineage=("license",),
        index=1,
    )
    renamed = _province_feature(
        geometry,
        {"name": "New name", "adm0_a3": "AAA", "iso_3166_2": "AAA-1"},
        source_layer="admin1_states_provinces",
        source_lineage=("source:a",),
        license_lineage=("license",),
        index=99,
    )
    assert first["properties"]["province_id"] == renamed["properties"]["province_id"]


def test_source_feature_order_does_not_change_generated_ids():
    source_features = [
        (
            {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
            {"name": "One", "adm0_a3": "AAA", "iso_3166_2": "AAA-1"},
        ),
        (
            {"type": "Polygon", "coordinates": [[[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]]},
            {"name": "Two", "adm0_a3": "AAA", "iso_3166_2": "AAA-2"},
        ),
    ]

    def build_ids(features):
        return sorted(
            _province_feature(
                geometry,
                properties,
                source_layer="admin1_states_provinces",
                source_lineage=("source:a",),
                license_lineage=("license",),
                index=index,
            )["properties"]["province_id"]
            for index, (geometry, properties) in enumerate(features, start=1)
        )

    assert build_ids(source_features) == build_ids(list(reversed(source_features)))


def test_duplicate_deterministic_ids_fail_cleanly():
    feature = {"properties": {"province_id": "ne_duplicate-0123456789ab"}}
    with pytest.raises(ProvinceBuildError, match="collision"):
        _ensure_unique_province_ids([feature, feature])
