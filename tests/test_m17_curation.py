"""M17: external curator bundles, ownership diffs, golden-border suites, checklist."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from gpm.cli import main
from gpm.curation import (
    CuratorBundleError,
    diff_ownership,
    import_curator_bundle,
    list_curator_bundles,
    load_curator_bundle,
    run_contribution_checklist,
    validate_curator_bundle,
)
from gpm.paths import SAMPLE_DIR, SCENARIO_GOLDEN_DIR
from gpm.qa.scenario import run_scenario_politics_qa
from gpm.schemas import (
    SchemaValidationError,
    validate_curator_bundle as schema_validate_bundle,
    validate_scenario_diff_report,
)
from gpm.scenarios import validate_scenario_document


def _land(province_id, *, country="FRA", region="FR-01", name=None):
    return {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
        },
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


def _write_provinces(path: Path, features: list[dict]) -> None:
    path.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_adjacency(path: Path, pairs: list[tuple[str, str]]) -> None:
    lines = [
        "from_province_id,to_province_id,adjacency_type,bidirectional,"
        "crossing_type,shared_border_km,source_lineage"
    ]
    for left, right in pairs:
        lines.append(f'{left},{right},land,true,shared_border,10,"[]"')
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _scenario(**overrides):
    document = {
        "schema_version": "0.1.0",
        "scenario_id": "m17-fixture",
        "label": "M17 fixture",
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
            },
            {
                "match_parent_country_id": "GBR",
                "owner": "ENG",
                "controller": "ENG",
                "cores": ["ENG"],
            },
        ],
        "region_rules": [],
        "province_overrides": [],
    }
    document.update(overrides)
    return document


def _write_bundle(root: Path, *, scenario: dict, golden: dict | None = None) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "scenarios").mkdir(exist_ok=True)
    (root / "golden").mkdir(exist_ok=True)
    scenario_rel = "scenarios/m17-fixture.json"
    (root / scenario_rel).write_text(json.dumps(scenario, indent=2) + "\n", encoding="utf-8")
    golden_rel = None
    if golden is not None:
        golden_rel = "golden/m17-fixture.json"
        (root / golden_rel).write_text(json.dumps(golden, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "schema_version": "0.1.0",
        "document_type": "curator-bundle",
        "bundle_id": "m17-test-bundle",
        "display_name": "M17 test bundle",
        "license": "CC0-1.0",
        "source_lineage": ["test fixture"],
        "license_lineage": ["CC0-1.0"],
        "scenarios": [
            {
                "scenario_id": scenario["scenario_id"],
                "path": scenario_rel,
                **({"golden_path": golden_rel} if golden_rel else {}),
            }
        ],
        "checklist": {
            "sources_documented": True,
            "licenses_reviewed": True,
            "golden_borders_present": golden is not None,
            "qa_pass_claimed": True,
            "no_restricted_sources": True,
        },
        "deprecation": {
            "policy": "Republish under a new bundle_id when scaffold IDs change.",
        },
    }
    (root / "bundle_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return root


def test_sample_curator_bundle_validates():
    path = SAMPLE_DIR / "curator-bundle-example"
    assert path.is_dir()
    document = load_curator_bundle(path)
    validate_curator_bundle(document, bundle_root=path, check_files=True, check_scenarios=True)
    schema_validate_bundle(document)
    assert document["bundle_id"] == "curator-bundle-example"
    assert document["document_type"] == "curator-bundle"
    assert len(document["scenarios"]) >= 1

    summaries = list_curator_bundles()
    by_id = {item.bundle_id: item for item in summaries}
    assert "curator-bundle-example" in by_id
    assert by_id["curator-bundle-example"].golden_count >= 1


def test_cli_curation_list_and_validate():
    assert main(["curation", "list", "--format", "json"]) == 0
    assert main(["curation", "validate", "--bundle", "curator-bundle-example"]) == 0
    assert main(["curation", "checklist", "--bundle", "samples/curator-bundle-example"]) == 0


def test_import_curator_bundle(tmp_path: Path):
    out = tmp_path / "imported"
    result = import_curator_bundle(
        SAMPLE_DIR / "curator-bundle-example",
        output_dir=out,
    )
    assert result["bundle_id"] == "curator-bundle-example"
    assert (out / "bundle_manifest.json").is_file()
    assert (out / "import_manifest.json").is_file()
    assert (out / "scenarios" / "community-demo-1444.json").is_file()


def test_bundle_rejects_path_escape(tmp_path: Path):
    root = tmp_path / "bad"
    root.mkdir()
    manifest = {
        "schema_version": "0.1.0",
        "document_type": "curator-bundle",
        "bundle_id": "bad-bundle",
        "display_name": "Bad",
        "license": "CC0-1.0",
        "scenarios": [
            {"scenario_id": "x", "path": "../outside.json"},
        ],
    }
    (root / "bundle_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(CuratorBundleError, match="relative path"):
        validate_curator_bundle(manifest, bundle_root=root, check_files=False)


def test_ownership_diff_detects_owner_change(tmp_path: Path):
    base = [
        {"province_id": "a", "owner": "FRA", "controller": "FRA", "disputed": False, "cores": [], "claims": []},
        {"province_id": "b", "owner": "ENG", "controller": "ENG", "disputed": False, "cores": [], "claims": []},
    ]
    target = [
        {"province_id": "a", "owner": "BUR", "controller": "BUR", "disputed": True, "cores": ["BUR"], "claims": ["FRA"]},
        {"province_id": "b", "owner": "ENG", "controller": "ENG", "disputed": False, "cores": [], "claims": []},
        {"province_id": "c", "owner": "FRA", "controller": "FRA", "disputed": False, "cores": [], "claims": []},
    ]
    report_path = tmp_path / "diff.json"
    result = diff_ownership(
        base,
        target,
        base_meta={"label": "base", "scenario_id": "base", "source": "base"},
        target_meta={"label": "target", "scenario_id": "target", "source": "target"},
        report_output=report_path,
    )
    assert result.status == "changed"
    assert result.owner_change_count == 1
    assert result.disputed_change_count == 1
    assert result.added_province_count == 1
    assert result.contested_province_count >= 1
    assert "FRA" in result.report["owner_count_delta"] or "BUR" in result.report["owner_count_delta"]
    validate_scenario_diff_report(result.report)
    assert report_path.is_file()


def test_ownership_diff_identical():
    rows = [
        {"province_id": "a", "owner": "FRA", "controller": "FRA", "disputed": False},
    ]
    result = diff_ownership(rows, rows)
    assert result.status == "identical"
    assert result.owner_change_count == 0
    validate_scenario_diff_report(result.report)


def test_cli_curation_diff_from_ownership_files(tmp_path: Path):
    base_path = tmp_path / "base.json"
    target_path = tmp_path / "target.json"
    base_path.write_text(
        json.dumps(
            {
                "records": [
                    {"province_id": "p1", "owner": "FRA", "controller": "FRA", "disputed": False},
                ]
            }
        ),
        encoding="utf-8",
    )
    target_path.write_text(
        json.dumps(
            {
                "records": [
                    {"province_id": "p1", "owner": "ENG", "controller": "ENG", "disputed": False},
                ]
            }
        ),
        encoding="utf-8",
    )
    report = tmp_path / "out.json"
    code = main(
        [
            "curation",
            "diff",
            "--base-ownership",
            str(base_path),
            "--target-ownership",
            str(target_path),
            "--report-output",
            str(report),
            "--format",
            "json",
        ]
    )
    assert code == 0
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["status"] == "changed"
    assert payload["summary"]["owner_change_count"] == 1


def test_golden_border_suite_extensions(tmp_path: Path):
    provinces = tmp_path / "provinces.geojson"
    adjacency = tmp_path / "adjacency.csv"
    scenario_path = tmp_path / "scenario.json"
    golden_path = tmp_path / "golden.json"
    report_path = tmp_path / "qa.json"

    _write_provinces(
        provinces,
        [
            _land("p_fra", country="FRA", region="FR-01"),
            _land("p_eng", country="GBR", region="GB-ENG"),
            _land("p_mid", country="FRA", region="FR-02"),
        ],
    )
    _write_adjacency(adjacency, [("p_fra", "p_mid"), ("p_mid", "p_eng")])
    scenario = _scenario(
        province_overrides=[
            {
                "province_id": "p_mid",
                "owner": "BUR",
                "controller": "BUR",
                "cores": ["BUR"],
                "disputed": True,
            }
        ]
    )
    scenario_path.write_text(json.dumps(scenario, indent=2) + "\n", encoding="utf-8")
    golden = {
        "min_owner_counts": {"FRA": 1, "ENG": 1},
        "max_owner_counts": {"BUR": 5},
        "required_owners": ["FRA", "ENG", "BUR"],
        "forbidden_owners": ["XXX"],
        "province_owners": {"p_mid": "BUR"},
        "disputed_provinces": {"p_mid": True},
        "border_pairs": [
            {
                "left_province_id": "p_fra",
                "right_province_id": "p_mid",
                "left_owner": "FRA",
                "right_owner": "BUR",
                "require_adjacent": True,
            }
        ],
        "owner_adjacencies": [
            {"owner_a": "FRA", "owner_b": "BUR", "min_shared_edges": 1},
        ],
    }
    golden_path.write_text(json.dumps(golden, indent=2) + "\n", encoding="utf-8")

    result = run_scenario_politics_qa(
        "modern-small",
        "m17-fixture",
        province_input=provinces,
        adjacency_input=adjacency,
        scenario_path=scenario_path,
        golden_input=golden_path,
        report_output=report_path,
    )
    assert result.passed, report_path.read_text(encoding="utf-8")
    assert result.golden_analysis == "complete"


def test_golden_border_fails_on_wrong_owner(tmp_path: Path):
    provinces = tmp_path / "provinces.geojson"
    adjacency = tmp_path / "adjacency.csv"
    scenario_path = tmp_path / "scenario.json"
    golden_path = tmp_path / "golden.json"

    _write_provinces(
        provinces,
        [
            _land("p_fra", country="FRA"),
            _land("p_eng", country="GBR"),
        ],
    )
    _write_adjacency(adjacency, [("p_fra", "p_eng")])
    scenario_path.write_text(json.dumps(_scenario(), indent=2) + "\n", encoding="utf-8")
    golden_path.write_text(
        json.dumps(
            {
                "border_pairs": [
                    {
                        "left_province_id": "p_fra",
                        "right_province_id": "p_eng",
                        "left_owner": "ENG",
                        "right_owner": "FRA",
                    }
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    result = run_scenario_politics_qa(
        "modern-small",
        "m17-fixture",
        province_input=provinces,
        adjacency_input=adjacency,
        scenario_path=scenario_path,
        golden_input=golden_path,
        report_output=tmp_path / "qa.json",
    )
    assert not result.passed
    report = json.loads((tmp_path / "qa.json").read_text(encoding="utf-8"))
    codes = {item["code"] for item in report["findings"]}
    assert "GOLDEN_BORDER_OWNER_MISMATCH" in codes


def test_golden_forbidden_and_max_count(tmp_path: Path):
    provinces = tmp_path / "provinces.geojson"
    scenario_path = tmp_path / "scenario.json"
    golden_path = tmp_path / "golden.json"
    _write_provinces(provinces, [_land("p1", country="FRA"), _land("p2", country="FRA")])
    scenario_path.write_text(json.dumps(_scenario(), indent=2) + "\n", encoding="utf-8")
    golden_path.write_text(
        json.dumps(
            {
                "max_owner_counts": {"FRA": 1},
                "forbidden_owners": ["FRA"],
                "required_owners": ["ENG"],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    result = run_scenario_politics_qa(
        "modern-small",
        "m17-fixture",
        province_input=provinces,
        adjacency_input=None,
        scenario_path=scenario_path,
        golden_input=golden_path,
        report_output=tmp_path / "qa.json",
    )
    assert not result.passed
    report = json.loads((tmp_path / "qa.json").read_text(encoding="utf-8"))
    codes = {item["code"] for item in report["findings"]}
    assert "GOLDEN_MAX_COUNT_FAILED" in codes
    assert "GOLDEN_FORBIDDEN_OWNER" in codes
    assert "GOLDEN_REQUIRED_OWNER_MISSING" in codes


def test_contribution_checklist(tmp_path: Path):
    root = _write_bundle(
        tmp_path / "bundle",
        scenario=_scenario(),
        golden={"min_owner_counts": {"FRA": 1}},
    )
    result = run_contribution_checklist(root)
    assert result.passed
    assert result.bundle_id == "m17-test-bundle"

    # Missing no_restricted_sources fails hard
    manifest_path = root / "bundle_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["checklist"]["no_restricted_sources"] = False
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    failed = run_contribution_checklist(root)
    assert not failed.passed


def test_schema_validate_curator_bundle_rejects_bad():
    with pytest.raises(SchemaValidationError):
        schema_validate_bundle({"schema_version": "0.1.0"})


def test_bundled_official_goldens_still_present():
    for name in ("official-1444", "official-1836", "official-1936"):
        path = SCENARIO_GOLDEN_DIR / f"{name}.json"
        assert path.is_file()
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert "min_owner_counts" in payload


def test_sample_scenario_document_valid():
    path = SAMPLE_DIR / "curator-bundle-example" / "scenarios" / "community-demo-1444.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    validate_scenario_document(document)


def test_demo_manifest_marks_curation_as_shipped():
    manifest = json.loads(
        Path("landing/demo/data/demo-manifest.json").read_text(encoding="utf-8")
    )
    live_ids = {s["id"] for s in manifest.get("live_layers") or []}
    future_ids = {s["id"] for s in manifest.get("future_slots") or []}
    assert "curation-diff" in live_ids
    assert "curation-diff" not in future_ids
