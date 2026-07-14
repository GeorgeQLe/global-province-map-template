import csv
import json

import pytest

from gpm.builders.adjacency import ADJACENCY_COLUMNS, build_land_adjacency
from gpm.cli import main
from gpm.qa.topology import TopologyQAError, run_topology_qa
from gpm.schemas import validate_topology_qa_report
from test_build_provinces import _write_polygon_zip


def test_topology_qa_passes_complete_fixture_and_cli_json_summary(tmp_path, capsys):
    province_input = tmp_path / "provinces.geojson"
    adjacency_input = tmp_path / "adjacency.csv"
    report_output = tmp_path / "topology.json"
    mask = _write_mask(tmp_path, _ring(0, 0, 2, 1))
    _write_geojson(
        province_input,
        [_feature("p_a", _polygon(0, 0, 1, 1)), _feature("p_b", _polygon(1, 0, 2, 1))],
    )
    build_land_adjacency("modern-small", province_input=province_input, output=adjacency_input)

    assert main(
        [
            "qa",
            "topology",
            "--province-input",
            str(province_input),
            "--adjacency-input",
            str(adjacency_input),
            "--raw-data",
            str(mask),
            "--report-output",
            str(report_output),
            "--summary-format",
            "json",
        ]
    ) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["status"] == "pass"
    assert summary["error_count"] == 0
    report = json.loads(report_output.read_text(encoding="utf-8"))
    validate_topology_qa_report(report)
    assert report["findings"] == []
    assert report["summary"]["analysis"] == {"coverage": "complete", "graph": "complete"}


@pytest.mark.parametrize(
    ("start_x", "expected_status", "expected_severity"),
    [(1.00001, "pass", "warning"), (1.001, "fail", "error")],
)
def test_topology_qa_applies_gap_component_thresholds(
    tmp_path, start_x, expected_status, expected_severity
):
    province_input = tmp_path / "provinces.geojson"
    adjacency_input = tmp_path / "adjacency.csv"
    mask = _write_mask(tmp_path, _ring(0, 0, 2, 1))
    _write_geojson(
        province_input,
        [_feature("p_a", _polygon(0, 0, 1, 1)), _feature("p_b", _polygon(start_x, 0, 2, 1))],
    )
    build_land_adjacency("modern-small", province_input=province_input, output=adjacency_input)
    result = run_topology_qa(
        "modern-small",
        province_input=province_input,
        adjacency_input=adjacency_input,
        raw_data=mask,
        report_output=tmp_path / "report.json",
    )
    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    gap = next(finding for finding in report["findings"] if finding["code"] == "LAND_COVERAGE_GAP")
    assert result.status == expected_status
    assert gap["severity"] == expected_severity


@pytest.mark.parametrize(
    ("overlap", "expected_status", "expected_severity"),
    [(0.00001, "pass", "warning"), (0.01, "fail", "error")],
)
def test_topology_qa_applies_overlap_thresholds(tmp_path, overlap, expected_status, expected_severity):
    province_input = tmp_path / "provinces.geojson"
    adjacency_input = tmp_path / "adjacency.csv"
    mask = _write_mask(tmp_path, _ring(0, 0, 2, 1))
    _write_geojson(
        province_input,
        [
            _feature("p_a", _polygon(0, 0, 1 + overlap, 1)),
            _feature("p_b", _polygon(1, 0, 2, 1)),
        ],
    )
    build_land_adjacency("modern-small", province_input=province_input, output=adjacency_input)
    result = run_topology_qa(
        "modern-small",
        province_input=province_input,
        adjacency_input=adjacency_input,
        raw_data=mask,
        report_output=tmp_path / "report.json",
    )
    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    overlap_finding = next(finding for finding in report["findings"] if finding["code"] == "PROVINCE_OVERLAP")
    assert result.status == expected_status
    assert overlap_finding["severity"] == expected_severity


def test_topology_qa_ignores_sub_square_metre_outside_mask_rounding(tmp_path):
    province_input = tmp_path / "provinces.geojson"
    adjacency_input = tmp_path / "adjacency.csv"
    mask = _write_mask(tmp_path, _ring(0, 0, 1, 1))
    _write_geojson(province_input, [_feature("p_a", _polygon(0, 0, 1 + 1e-13, 1))])
    _write_adjacency(adjacency_input, [])
    result = run_topology_qa(
        "modern-small",
        province_input=province_input,
        adjacency_input=adjacency_input,
        raw_data=mask,
        report_output=tmp_path / "report.json",
    )
    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert result.status == "pass"
    assert "COVERAGE_OUTSIDE_MASK" not in {item["code"] for item in report["findings"]}


def test_invalid_geometry_and_duplicate_ids_mark_dependent_analysis_incomplete(tmp_path):
    province_input = tmp_path / "provinces.geojson"
    adjacency_input = tmp_path / "adjacency.csv"
    mask = _write_mask(tmp_path, _ring(0, 0, 2, 2))
    bowtie = {
        "type": "Polygon",
        "coordinates": [[[0, 0], [2, 2], [0, 2], [2, 0], [0, 0]]],
    }
    feature = _feature("duplicate", bowtie)
    _write_geojson(province_input, [feature, feature])
    _write_adjacency(adjacency_input, [])

    result = run_topology_qa(
        "modern-small",
        province_input=province_input,
        adjacency_input=adjacency_input,
        raw_data=mask,
        report_output=tmp_path / "report.json",
    )
    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    codes = {finding["code"] for finding in report["findings"]}
    assert result.status == "fail"
    assert {"DUPLICATE_PROVINCE_ID", "INVALID_GEOMETRY", "ANALYSIS_INCOMPLETE"} <= codes
    assert report["summary"]["analysis"] == {"coverage": "incomplete", "graph": "incomplete"}
    assert "LAND_COVERAGE_GAP" not in codes


def test_invalid_mask_geometry_is_repaired_on_load(tmp_path):
    province_input = tmp_path / "provinces.geojson"
    adjacency_input = tmp_path / "adjacency.csv"
    # Bowtie ring: self-intersecting, repairable via make_valid.
    mask = _write_mask(
        tmp_path,
        [[0, 0], [2, 2], [0, 2], [2, 0], [0, 0]],
    )
    _write_geojson(province_input, [_feature("p_a", _polygon(0, 0, 1, 1))])
    _write_adjacency(adjacency_input, [])

    result = run_topology_qa(
        "modern-small",
        province_input=province_input,
        adjacency_input=adjacency_input,
        raw_data=mask,
        report_output=tmp_path / "report.json",
    )
    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    codes = {finding["code"] for finding in report["findings"]}
    assert "MASK_GEOMETRY_REPAIRED" in codes
    assert "INVALID_MASK_GEOMETRY" not in codes
    # Coverage analysis runs to completion against the repaired mask.
    assert report["summary"]["analysis"] == {"coverage": "complete", "graph": "complete"}


def test_qa_validates_adjacency_endpoints_semantics_pairs_and_measurements(tmp_path):
    province_input = tmp_path / "provinces.geojson"
    adjacency_input = tmp_path / "adjacency.csv"
    mask = _write_mask(tmp_path, _ring(0, 0, 2, 1))
    _write_geojson(
        province_input,
        [_feature("p_a", _polygon(0, 0, 1, 1)), _feature("p_b", _polygon(1, 0, 2, 1))],
    )
    base = {
        "from_province_id": "p_b",
        "to_province_id": "p_a",
        "adjacency_type": "land",
        "bidirectional": "false",
        "crossing_type": "shared_border",
        "shared_border_km": "999",
        "source_lineage": "not-json",
    }
    unknown = dict(base, from_province_id="p_a", to_province_id="unknown", bidirectional="true")
    duplicate = dict(base, from_province_id="p_a", to_province_id="p_b", bidirectional="true")
    _write_adjacency(adjacency_input, [base, duplicate, unknown])

    result = run_topology_qa(
        "modern-small",
        province_input=province_input,
        adjacency_input=adjacency_input,
        raw_data=mask,
        report_output=tmp_path / "report.json",
    )
    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    codes = {finding["code"] for finding in report["findings"]}
    assert result.status == "fail"
    assert {
        "ASYMMETRIC_ADJACENCY",
        "DUPLICATE_ADJACENCY_EDGE",
        "INVALID_ADJACENCY_LINEAGE",
        "NONCANONICAL_ADJACENCY_PAIR",
        "SHARED_BORDER_MEASUREMENT_MISMATCH",
        "UNKNOWN_ADJACENCY_ENDPOINT",
    } <= codes


def test_qa_reports_islands_and_components_as_warnings_only(tmp_path):
    province_input = tmp_path / "provinces.geojson"
    adjacency_input = tmp_path / "adjacency.csv"
    _write_geojson(
        province_input,
        [
            _feature("p_a", _polygon(0, 0, 1, 1)),
            _feature("p_b", _polygon(1, 0, 2, 1)),
            _feature("p_island", _polygon(2.1, 0, 3, 1)),
        ],
    )
    mask = _write_mask(tmp_path, _ring(0, 0, 2, 1), name="mask-main.zip")
    _write_multi_mask(mask, [_ring(0, 0, 2, 1), _ring(2.1, 0, 3, 1)])
    build_land_adjacency("modern-small", province_input=province_input, output=adjacency_input)
    result = run_topology_qa(
        "modern-small",
        province_input=province_input,
        adjacency_input=adjacency_input,
        raw_data=mask,
        report_output=tmp_path / "report.json",
    )
    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    codes = [finding["code"] for finding in report["findings"]]
    assert result.status == "pass"
    assert "ISOLATED_PROVINCE" in codes
    assert "CONNECTED_COMPONENTS" in codes
    assert report["summary"]["connected_component_count"] == 2


def test_qa_operational_failures_return_clean_exit(tmp_path, capsys):
    assert main(
        [
            "qa",
            "topology",
            "--province-input",
            str(tmp_path / "missing.geojson"),
            "--adjacency-input",
            str(tmp_path / "missing.csv"),
            "--raw-data",
            str(tmp_path / "missing-raw"),
        ]
    ) == 1
    assert "does not exist" in capsys.readouterr().err

    provinces = tmp_path / "provinces.geojson"
    _write_geojson(provinces, [_feature("p_a", _polygon(0, 0, 1, 1))])
    malformed_csv = tmp_path / "bad.csv"
    malformed_csv.write_text("wrong,header\n", encoding="utf-8")
    with pytest.raises(TopologyQAError, match="missing column"):
        run_topology_qa(
            "modern-small",
            province_input=provinces,
            adjacency_input=malformed_csv,
            raw_data=tmp_path,
            report_output=tmp_path / "report.json",
        )


def _feature(province_id, geometry):
    return {
        "type": "Feature",
        "geometry": geometry,
        "properties": {
            "province_id": province_id,
            "kind": "land",
            "parent_country_id": "AAA",
            "parent_region_id": "AAA-1",
            "source_lineage": ["source:test"],
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


def _write_adjacency(path, rows):
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=ADJACENCY_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _write_mask(tmp_path, ring, name="mask.zip"):
    path = tmp_path / name
    _write_polygon_zip(path, "mask", [({"name": "Mask"}, ring)])
    return path


def _write_multi_mask(path, rings):
    _write_polygon_zip(path, "mask", [({"name": f"Mask {index}"}, ring) for index, ring in enumerate(rings)])
