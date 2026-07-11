import json
from urllib.request import urlopen

from gpm.cli import main
from gpm.viewer import prepare_review_dataset, serve_review
from gpm.viewer.server import ReviewError


def _write_provinces(path, features):
    path.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "name": "provinces",
                "gpm": {
                    "schema_version": "0.1.0",
                    "id_scheme": "source-geometry-sha256-v1",
                    "profile_id": "modern-small",
                },
                "features": features,
            }
        ),
        encoding="utf-8",
    )


def _province(province_id, country_id, x0, y0, x1, y1, **extra):
    properties = {
        "province_id": province_id,
        "display_name": province_id,
        "kind": "land",
        "parent_region_id": country_id,
        "parent_country_id": country_id,
        "area_sq_km": 100.0,
        "estimated_population": 1000.0,
        "terrain_class": None,
        "coastal": False,
        "island": False,
        "source_lineage": ["natural_earth:test"],
        "license_lineage": ["public domain"],
        "refinement_strategy": extra.pop("refinement_strategy", "area-weighted-voronoi"),
    }
    properties.update(extra)
    return {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [x0, y0],
                    [x1, y0],
                    [x1, y1],
                    [x0, y1],
                    [x0, y0],
                ]
            ],
        },
        "properties": properties,
    }


def _write_adjacency(path, rows):
    lines = [
        "from_province_id,to_province_id,adjacency_type,bidirectional,crossing_type,shared_border_km,source_lineage"
    ]
    for left, right, border in rows:
        lines.append(
            f'{left},{right},land,true,shared_border,{border},"[""natural_earth:test""]"'
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_qa(path, findings):
    path.write_text(
        json.dumps(
            {
                "schema_version": "0.1.0",
                "report_type": "topology_qa",
                "profile_id": "modern-small",
                "status": "fail" if any(item["severity"] == "error" for item in findings) else "pass",
                "inputs": {
                    "province_input": "provinces.geojson",
                    "adjacency_input": "adjacency.csv",
                    "natural_earth_admin0_mask": "mask.zip",
                },
                "thresholds": {
                    "max_overlap_area_sq_km": 1.0,
                    "max_gap_component_area_sq_km": 10.0,
                    "min_shared_border_km": 0.01,
                },
                "summary": {
                    "province_count": 2,
                    "land_province_count": 2,
                    "adjacency_count": 1,
                    "error_count": sum(1 for item in findings if item["severity"] == "error"),
                    "warning_count": sum(1 for item in findings if item["severity"] == "warning"),
                    "isolated_province_count": 0,
                    "connected_component_count": 1,
                    "analysis": {"coverage": "complete", "graph": "complete"},
                },
                "findings": findings,
            }
        ),
        encoding="utf-8",
    )


def test_prepare_review_dataset_indexes_adjacency_and_qa(tmp_path):
    provinces = tmp_path / "provinces.geojson"
    adjacency = tmp_path / "adjacency.csv"
    qa = tmp_path / "topology_qa.json"
    _write_provinces(
        provinces,
        [
            _province("ne_aaa-one", "AAA", 0, 0, 1, 1),
            _province("ne_bbb-two", "BBB", 1, 0, 2, 1, refinement_strategy="source-geometry-preserved"),
        ],
    )
    _write_adjacency(adjacency, [("ne_aaa-one", "ne_bbb-two", 12.5)])
    _write_qa(
        qa,
        [
            {
                "code": "INVALID_GEOMETRY",
                "severity": "error",
                "affected_ids": ["ne_aaa-one"],
                "message": "bad ring",
                "measurements": {},
            }
        ],
    )

    dataset = prepare_review_dataset(
        "modern-small",
        province_input=provinces,
        adjacency_input=adjacency,
        qa_report_input=qa,
    )

    assert dataset.province_count == 2
    assert dataset.adjacency_count == 1
    assert dataset.qa_status == "fail"
    assert dataset.qa_error_count == 1
    assert dataset.adjacency_index["ne_aaa-one"][0]["neighbor_id"] == "ne_bbb-two"
    assert dataset.adjacency_index["ne_bbb-two"][0]["neighbor_id"] == "ne_aaa-one"
    assert dataset.findings_by_province["ne_aaa-one"][0]["code"] == "INVALID_GEOMETRY"
    assert dataset.findings_by_province["ne_bbb-two"] == []
    meta = dataset.meta_payload()
    assert meta["endpoints"]["provinces"] == "/api/provinces.geojson"
    assert meta["gpm"]["id_scheme"] == "source-geometry-sha256-v1"


def test_prepare_review_dataset_allows_missing_optional_inputs(tmp_path):
    provinces = tmp_path / "provinces.geojson"
    _write_provinces(provinces, [_province("ne_aaa-one", "AAA", 0, 0, 1, 1)])

    dataset = prepare_review_dataset(
        "modern-small",
        province_input=provinces,
        adjacency_input=tmp_path / "missing-adjacency.csv",
        qa_report_input=tmp_path / "missing-qa.json",
    )

    assert dataset.adjacency_input is None
    assert dataset.qa_report_input is None
    assert dataset.adjacency_count == 0
    assert dataset.qa_status is None


def test_prepare_review_dataset_rejects_missing_provinces(tmp_path):
    try:
        prepare_review_dataset(
            "modern-small",
            province_input=tmp_path / "missing.geojson",
            adjacency_input=None,
            qa_report_input=None,
        )
        assert False, "expected ReviewError"
    except ReviewError as error:
        assert "not found" in str(error)


def test_review_cli_reports_missing_province_input(tmp_path, capsys):
    assert (
        main(
            [
                "review",
                "--province-input",
                str(tmp_path / "missing.geojson"),
                "--adjacency-input",
                str(tmp_path / "missing.csv"),
                "--qa-report",
                str(tmp_path / "missing.json"),
                "--no-open",
            ]
        )
        == 1
    )
    captured = capsys.readouterr()
    assert "not found" in captured.err
    assert "Traceback" not in captured.err


def test_review_server_serves_static_assets_and_apis(tmp_path):
    provinces = tmp_path / "provinces.geojson"
    adjacency = tmp_path / "adjacency.csv"
    qa = tmp_path / "topology_qa.json"
    _write_provinces(
        provinces,
        [
            _province("ne_aaa-one", "AAA", 0, 0, 1, 1),
            _province("ne_bbb-two", "BBB", 1, 0, 2, 1),
        ],
    )
    _write_adjacency(adjacency, [("ne_aaa-one", "ne_bbb-two", 4.0)])
    _write_qa(
        qa,
        [
            {
                "code": "TINY_FRAGMENT",
                "severity": "warning",
                "affected_ids": ["ne_bbb-two"],
                "message": "small area",
                "measurements": {"area_sq_km": 0.1},
            }
        ],
    )

    dataset = prepare_review_dataset(
        "modern-small",
        province_input=provinces,
        adjacency_input=adjacency,
        qa_report_input=qa,
    )
    handle = serve_review(dataset=dataset, host="127.0.0.1", port=0, open_browser=False, block=False)
    try:
        base = handle.result.url.rstrip("/")
        with urlopen(f"{base}/") as response:
            html = response.read().decode("utf-8")
        assert "Global Province Map" in html
        assert "/static/app.js" in html

        with urlopen(f"{base}/static/app.js") as response:
            js = response.read().decode("utf-8")
        assert "color-mode" in js

        with urlopen(f"{base}/api/meta") as response:
            meta = json.loads(response.read().decode("utf-8"))
        assert meta["province_count"] == 2
        assert meta["adjacency_count"] == 1
        assert meta["qa_status"] == "pass"

        with urlopen(f"{base}/api/provinces.geojson") as response:
            collection = json.loads(response.read().decode("utf-8"))
        assert len(collection["features"]) == 2

        with urlopen(f"{base}/api/adjacency.json") as response:
            adjacency_payload = json.loads(response.read().decode("utf-8"))
        assert adjacency_payload["adjacency"]["ne_aaa-one"][0]["shared_border_km"] == 4.0

        with urlopen(f"{base}/api/qa.json") as response:
            qa_payload = json.loads(response.read().decode("utf-8"))
        assert qa_payload["available"] is True
        assert qa_payload["report"]["findings"][0]["code"] == "TINY_FRAGMENT"

        with urlopen(f"{base}/api/province/ne_bbb-two") as response:
            province_payload = json.loads(response.read().decode("utf-8"))
        assert province_payload["province_id"] == "ne_bbb-two"
        assert province_payload["findings"][0]["code"] == "TINY_FRAGMENT"
        assert province_payload["adjacency"][0]["neighbor_id"] == "ne_aaa-one"
    finally:
        handle.shutdown()
