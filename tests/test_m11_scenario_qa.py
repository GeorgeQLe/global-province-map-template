import json
from pathlib import Path

import pytest

from gpm.cli import main
from gpm.qa.scenario import ScenarioPoliticsQAError, run_scenario_politics_qa
from gpm.scenarios import apply_province_override, load_scenario
from gpm.schemas import SchemaValidationError, validate_scenario_politics_qa_report
from gpm.viewer import prepare_review_dataset, serve_review
from gpm.viewer.server import ReviewError


def _polygon(x0, y0, x1, y1):
    return {
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
    }


def _land(province_id, geometry, *, country="FRA", region="FR-1", name=None):
    return {
        "type": "Feature",
        "geometry": geometry,
        "properties": {
            "province_id": province_id,
            "display_name": name or province_id,
            "kind": "land",
            "parent_region_id": region,
            "parent_country_id": country,
            "area_sq_km": 100.0,
            "estimated_population": 1000.0,
            "terrain_class": None,
            "coastal": False,
            "island": False,
            "source_lineage": ["test"],
            "license_lineage": ["public domain"],
        },
    }


def _write_provinces(path, features):
    path.write_text(
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


def _write_adjacency(path, pairs):
    lines = [
        "from_province_id,to_province_id,adjacency_type,bidirectional,crossing_type,shared_border_km,source_lineage"
    ]
    for left, right in pairs:
        lines.append(f'{left},{right},land,true,shared_border,10,"[]"')
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_scenario(path, document):
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


def _base_scenario(**overrides):
    document = {
        "schema_version": "0.1.0",
        "scenario_id": "qa-fixture",
        "label": "QA fixture",
        "era": "test",
        "start_date": "1444-11-11",
        "countries": {
            "FRA": {"display_name": "France"},
            "ENG": {"display_name": "England"},
            "BUR": {"display_name": "Burgundy"},
        },
        "defaults": {"culture": None, "religion": None, "disputed": False},
        "country_rules": [
            {
                "match_parent_country_id": "FRA",
                "owner": "FRA",
                "controller": "FRA",
                "cores": ["FRA"],
            }
        ],
        "region_rules": [],
        "province_overrides": [],
    }
    document.update(overrides)
    return document


def test_scenario_politics_qa_passes_clean_ownership(tmp_path):
    province_input = tmp_path / "provinces.geojson"
    adjacency = tmp_path / "adjacency.csv"
    scenario_path = tmp_path / "qa-fixture.json"
    report_output = tmp_path / "politics_qa.json"

    _write_provinces(
        province_input,
        [
            _land("land_a", _polygon(0, 0, 1, 1), country="FRA", region="FR-1"),
            _land("land_b", _polygon(1, 0, 2, 1), country="FRA", region="FR-1"),
            _land("land_c", _polygon(0, 1, 1, 2), country="FRA", region="FR-2"),
        ],
    )
    _write_adjacency(adjacency, [("land_a", "land_b"), ("land_a", "land_c")])
    _write_scenario(scenario_path, _base_scenario())

    result = run_scenario_politics_qa(
        "modern-small",
        "qa-fixture",
        province_input=province_input,
        adjacency_input=adjacency,
        scenario_path=scenario_path,
        report_output=report_output,
    )
    assert result.passed
    assert result.status == "pass"
    assert result.land_province_count == 3
    assert result.ownership_row_count == 3
    assert Path(result.report_output).is_file()

    report = json.loads(report_output.read_text(encoding="utf-8"))
    assert report["report_type"] == "scenario_politics_qa"
    assert report["milestone"] == "M11"
    validate_scenario_politics_qa_report(report)
    assert report["summary"]["error_count"] == 0


def test_scenario_politics_qa_flags_missing_owner_unknown_and_orphan_tags(tmp_path):
    province_input = tmp_path / "provinces.geojson"
    scenario_path = tmp_path / "qa-fixture.json"
    report_output = tmp_path / "politics_qa.json"
    ownership_input = tmp_path / "ownership.json"

    _write_provinces(
        province_input,
        [
            _land("land_a", _polygon(0, 0, 1, 1), country="FRA"),
            _land("land_b", _polygon(1, 0, 2, 1), country="FRA"),
        ],
    )
    _write_scenario(scenario_path, _base_scenario())
    ownership_input.write_text(
        json.dumps(
            {
                "records": [
                    {
                        "province_id": "land_a",
                        "owner": "FRA",
                        "controller": "FRA",
                        "cores": ["FRA", "GHOST"],
                        "claims": ["PHANTOM"],
                    },
                    {
                        "province_id": "land_b",
                        "owner": "",
                        "controller": "ZZZ",
                        "cores": [],
                        "claims": [],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    result = run_scenario_politics_qa(
        "modern-small",
        "qa-fixture",
        province_input=province_input,
        adjacency_input=tmp_path / "missing-adjacency.csv",
        scenario_path=scenario_path,
        ownership_input=ownership_input,
        report_output=report_output,
    )
    assert not result.passed
    report = json.loads(report_output.read_text(encoding="utf-8"))
    codes = {item["code"] for item in report["findings"]}
    assert "MISSING_OWNER" in codes
    assert "UNKNOWN_CONTROLLER_TAG" in codes
    assert "UNKNOWN_CORE_TAG" in codes or "ORPHAN_CORE" in codes
    assert "ORPHAN_CLAIM" in codes
    assert "ADJACENCY_ANALYSIS_SKIPPED" in codes
    validate_scenario_politics_qa_report(report)


def test_scenario_politics_qa_golden_checks(tmp_path):
    province_input = tmp_path / "provinces.geojson"
    scenario_path = tmp_path / "qa-fixture.json"
    golden_path = tmp_path / "golden.json"
    report_output = tmp_path / "politics_qa.json"

    _write_provinces(
        province_input,
        [
            _land("land_a", _polygon(0, 0, 1, 1), country="FRA"),
            _land("land_b", _polygon(1, 0, 2, 1), country="GBR"),
        ],
    )
    _write_scenario(
        scenario_path,
        _base_scenario(
            country_rules=[
                {
                    "match_parent_country_id": "FRA",
                    "owner": "FRA",
                    "controller": "FRA",
                    "cores": ["FRA"],
                },
                {
                    "match_parent_country_id": "GBR",
                    "owner": "ENG",
                    "controller": "ENG",
                    "cores": ["ENG"],
                },
            ]
        ),
    )
    golden_path.write_text(
        json.dumps(
            {
                "province_owners": {"land_a": "ENG"},
                "min_owner_counts": {"FRA": 5},
            }
        ),
        encoding="utf-8",
    )

    result = run_scenario_politics_qa(
        "modern-small",
        "qa-fixture",
        province_input=province_input,
        adjacency_input=None,
        scenario_path=scenario_path,
        golden_input=golden_path,
        report_output=report_output,
    )
    assert not result.passed
    report = json.loads(report_output.read_text(encoding="utf-8"))
    codes = {item["code"] for item in report["findings"]}
    assert "GOLDEN_OWNER_MISMATCH" in codes
    assert "GOLDEN_MIN_COUNT_FAILED" in codes


def test_cli_qa_scenario_json(tmp_path, capsys):
    province_input = tmp_path / "provinces.geojson"
    scenario_path = tmp_path / "qa-fixture.json"
    report_output = tmp_path / "politics_qa.json"
    _write_provinces(
        province_input,
        [_land("land_a", _polygon(0, 0, 1, 1), country="FRA")],
    )
    _write_scenario(scenario_path, _base_scenario())

    code = main(
        [
            "qa",
            "scenario",
            "--scenario",
            "qa-fixture",
            "--scenario-path",
            str(scenario_path),
            "--province-input",
            str(province_input),
            "--adjacency-input",
            str(tmp_path / "missing.csv"),
            "--report-output",
            str(report_output),
            "--format",
            "json",
        ]
    )
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "pass"
    assert payload["scenario_id"] == "qa-fixture"
    assert report_output.is_file()


def test_apply_province_override_writes_scenario(tmp_path):
    scenario_path = tmp_path / "edit-me.json"
    _write_scenario(
        scenario_path,
        _base_scenario(scenario_id="edit-me", province_overrides=[]),
    )
    result = apply_province_override(
        "edit-me",
        "land_a",
        {
            "owner": "ENG",
            "controller": "ENG",
            "cores": ["ENG", "FRA"],
            "claims": ["FRA"],
            "disputed": True,
            "notes": "Curated occupation",
        },
        scenario_path=scenario_path,
    )
    assert result.action == "created"
    assert result.province_override_count == 1
    document = json.loads(scenario_path.read_text(encoding="utf-8"))
    assert document["province_overrides"][0]["owner"] == "ENG"
    assert document["province_overrides"][0]["disputed"] is True

    result2 = apply_province_override(
        "edit-me",
        "land_a",
        {"owner": "BUR", "notes": "Updated"},
        scenario_path=scenario_path,
    )
    assert result2.action == "updated"
    document = json.loads(scenario_path.read_text(encoding="utf-8"))
    assert document["province_overrides"][0]["owner"] == "BUR"
    assert document["province_overrides"][0]["controller"] == "ENG"

    result3 = apply_province_override(
        "edit-me",
        "land_a",
        {},
        scenario_path=scenario_path,
    )
    assert result3.action == "removed"
    document = json.loads(scenario_path.read_text(encoding="utf-8"))
    assert document["province_overrides"] == []


def test_review_with_scenario_serves_ownership_and_authoring(tmp_path):
    province_input = tmp_path / "provinces.geojson"
    scenario_path = tmp_path / "qa-fixture.json"
    _write_provinces(
        province_input,
        [
            _land("land_a", _polygon(0, 0, 1, 1), country="FRA"),
            _land("land_b", _polygon(1, 0, 2, 1), country="FRA"),
        ],
    )
    _write_scenario(scenario_path, _base_scenario())

    dataset = prepare_review_dataset(
        "modern-small",
        province_input=province_input,
        adjacency_input=None,
        qa_report_input=None,
        scenario_path=scenario_path,
        run_politics_qa=True,
    )
    assert dataset.scenario_id == "qa-fixture"
    assert dataset.authoring_enabled
    assert "land_a" in dataset.ownership_by_id
    assert dataset.ownership_by_id["land_a"]["owner"] == "FRA"

    handle = serve_review(dataset=dataset, host="127.0.0.1", port=0, open_browser=False, block=False)
    try:
        from urllib.request import Request, urlopen

        base = handle.result.url.rstrip("/")
        with urlopen(f"{base}/api/meta") as response:
            meta = json.loads(response.read().decode("utf-8"))
        assert meta["scenario_id"] == "qa-fixture"
        assert meta["authoring_enabled"] is True
        assert meta["endpoints"]["ownership"] == "/api/ownership.json"

        with urlopen(f"{base}/api/ownership.json") as response:
            ownership = json.loads(response.read().decode("utf-8"))
        assert ownership["available"] is True
        assert ownership["count"] == 2

        body = json.dumps(
            {
                "province_id": "land_a",
                "owner": "ENG",
                "controller": "ENG",
                "cores": ["ENG"],
                "disputed": True,
                "notes": "Review edit",
            }
        ).encode("utf-8")
        request = Request(
            f"{base}/api/scenario/override",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request) as response:
            saved = json.loads(response.read().decode("utf-8"))
        assert saved["ok"] is True
        assert saved["result"]["action"] == "created"
        assert saved["ownership"]["owner"] == "ENG"

        document = json.loads(scenario_path.read_text(encoding="utf-8"))
        assert document["province_overrides"][0]["owner"] == "ENG"
    finally:
        handle.shutdown()


def test_prepare_review_dataset_requires_provinces(tmp_path):
    with pytest.raises(ReviewError, match="Province GeoJSON not found"):
        prepare_review_dataset(
            "modern-small",
            province_input=tmp_path / "missing.geojson",
            adjacency_input=None,
            qa_report_input=None,
        )


def test_validate_scenario_politics_qa_report_rejects_bad_status():
    report = {
        "schema_version": "0.1.0",
        "report_type": "scenario_politics_qa",
        "milestone": "M11",
        "profile_id": "modern-small",
        "scenario_id": "x",
        "status": "pass",
        "inputs": {
            "province_input": "p",
            "adjacency_input": None,
            "scenario_definition": None,
            "ownership_input": None,
            "golden_input": None,
        },
        "thresholds": {
            "max_owner_components": 25,
            "min_provinces_for_fragment_check": 8,
        },
        "summary": {
            "land_province_count": 1,
            "ownership_row_count": 1,
            "owner_tag_count": 1,
            "error_count": 1,
            "warning_count": 0,
            "unknown_tag_finding_count": 0,
            "orphan_tag_finding_count": 0,
            "analysis": {"adjacency": "skipped", "golden": "skipped"},
        },
        "findings": [
            {
                "code": "MISSING_OWNER",
                "severity": "error",
                "affected_ids": ["a"],
                "message": "missing",
                "measurements": {},
            }
        ],
    }
    with pytest.raises(SchemaValidationError):
        validate_scenario_politics_qa_report(report)


def test_bundled_modern_baseline_scenario_loads():
    scenario = load_scenario("modern-baseline")
    assert scenario["scenario_id"] == "modern-baseline"
