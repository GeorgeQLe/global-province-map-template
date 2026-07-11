import csv
import json

import pytest

from gpm.builders.adjacency import AdjacencyBuildError, build_land_adjacency
from gpm.cli import main


def test_adjacency_uses_line_contacts_sums_multipart_borders_and_is_deterministic(tmp_path):
    province_input = tmp_path / "provinces.geojson"
    first_output = tmp_path / "first.csv"
    second_output = tmp_path / "second.csv"
    multipart = {
        "type": "MultiPolygon",
        "coordinates": [[_ring(0, 0, 1, 1)], [_ring(0, 2, 1, 3)]],
    }
    features = [
        _feature("p_b", _polygon(1, 0, 2, 3), ["source:b"]),
        _feature("p_corner", _polygon(2, 3, 3, 4), ["source:c"]),
        _feature("p_a", multipart, ["source:a", "source:common"]),
    ]
    _write_geojson(province_input, features)

    result = build_land_adjacency("modern-small", province_input=province_input, output=first_output)
    build_land_adjacency("modern-small", province_input=province_input, output=second_output)

    assert first_output.read_bytes() == second_output.read_bytes()
    assert result.province_count == 3
    assert result.candidate_pair_count < 3
    with first_output.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    assert [(row["from_province_id"], row["to_province_id"]) for row in rows] == [("p_a", "p_b")]
    assert rows[0]["bidirectional"] == "true"
    assert rows[0]["adjacency_type"] == "land"
    assert rows[0]["crossing_type"] == "shared_border"
    assert float(rows[0]["shared_border_km"]) > 200
    assert json.loads(rows[0]["source_lineage"]) == ["source:a", "source:b", "source:common"]


def test_adjacency_cli_json_summary_and_clean_input_errors(tmp_path, capsys):
    province_input = tmp_path / "provinces.geojson"
    output = tmp_path / "adjacency.csv"
    _write_geojson(
        province_input,
        [_feature("p_a", _polygon(0, 0, 1, 1)), _feature("p_b", _polygon(1, 0, 2, 1))],
    )
    assert main(
        [
            "build",
            "adjacency",
            "--province-input",
            str(province_input),
            "--output",
            str(output),
            "--format",
            "json",
        ]
    ) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["adjacency_count"] == 1
    assert summary["output"] == str(output)

    assert main(["build", "adjacency", "--province-input", str(tmp_path / "missing")]) == 1
    assert "does not exist" in capsys.readouterr().err

    malformed = tmp_path / "malformed.geojson"
    malformed.write_text("not-json", encoding="utf-8")
    with pytest.raises(AdjacencyBuildError, match="Cannot read"):
        build_land_adjacency("modern-small", province_input=malformed, output=output)


def test_adjacency_excludes_sub_threshold_shared_line(tmp_path):
    province_input = tmp_path / "provinces.geojson"
    output = tmp_path / "adjacency.csv"
    _write_geojson(
        province_input,
        [
            _feature("p_a", _polygon(0, 0, 1, 1)),
            _feature("p_b", _polygon(1, 0, 2, 0.00001)),
        ],
    )
    result = build_land_adjacency("modern-small", province_input=province_input, output=output)
    assert result.candidate_pair_count == 1
    assert result.adjacency_count == 0


def _feature(province_id, geometry, lineage=None):
    return {
        "type": "Feature",
        "geometry": geometry,
        "properties": {
            "province_id": province_id,
            "kind": "land",
            "parent_country_id": "AAA",
            "parent_region_id": "AAA-1",
            "source_lineage": lineage or ["source:test"],
        },
    }


def _polygon(min_x, min_y, max_x, max_y):
    return {"type": "Polygon", "coordinates": [_ring(min_x, min_y, max_x, max_y)]}


def _ring(min_x, min_y, max_x, max_y):
    return [
        [min_x, min_y],
        [max_x, min_y],
        [max_x, max_y],
        [min_x, max_y],
        [min_x, min_y],
    ]


def _write_geojson(path, features):
    path.write_text(json.dumps({"type": "FeatureCollection", "features": features}), encoding="utf-8")
