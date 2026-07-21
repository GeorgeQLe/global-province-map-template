"""Certification-grade schema-0.3 historical anomaly census contracts."""

from __future__ import annotations

import copy
import importlib.util
import json
from argparse import Namespace
from pathlib import Path

import pytest

from gpm.qa.start_date import HISTORICAL_ANOMALY_TYPES, validate_anomaly_inventory
from gpm.schemas import SchemaValidationError, WORLDWIDE_M49_SUBREGIONS


ROOT = Path(__file__).resolve().parents[1]


def _builder_module():
    path = ROOT / "scripts" / "build-m25c-global-pass.py"
    spec = importlib.util.spec_from_file_location("m25c_anomaly_builder", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _inventory() -> dict:
    anomalies = [
        {
            "anomaly_id": f"case-{anomaly_type}",
            "type": anomaly_type,
            "region_ids": ["005"],
            "subject_ids": [f"polity-{anomaly_type}"],
            "source_ids": ["source-anchor", "source-corroboration"],
            "resolution": "resolved",
        }
        for anomaly_type in sorted(HISTORICAL_ANOMALY_TYPES)
    ]
    links = {("005", row["type"]): [row["anomaly_id"]] for row in anomalies}
    cells = []
    for region_id in sorted(WORLDWIDE_M49_SUBREGIONS):
        for anomaly_type in sorted(HISTORICAL_ANOMALY_TYPES):
            anomaly_ids = links.get((region_id, anomaly_type), [])
            cells.append({
                "region_id": region_id,
                "type": anomaly_type,
                "status": "resolved_cases" if anomaly_ids else "reviewed_none_found",
                "anomaly_ids": anomaly_ids,
                "source_ids": ["source-survey"],
                "notes": "Reviewed date-valid academic and primary survey sources; linked cases where found.",
            })
    return {
        "schema_version": "0.3.0",
        "document_type": "historical_anomaly_inventory",
        "artifact_version": "1.0.0",
        "pass_id": "official-1444-global-v1",
        "start_date": "1444-11-11",
        "anomalies": anomalies,
        "census": {
            "region_ids": sorted(WORLDWIDE_M49_SUBREGIONS),
            "types": sorted(HISTORICAL_ANOMALY_TYPES),
            "researcher": "Researcher Example",
            "reviewer": "Reviewer Example",
            "review_date": "2026-07-20",
            "cells": cells,
        },
    }


def _cell(inventory: dict, region_id: str, anomaly_type: str) -> dict:
    return next(
        row for row in inventory["census"]["cells"]
        if row["region_id"] == region_id and row["type"] == anomaly_type
    )


def test_valid_242_cell_census_supports_multiple_cross_region_and_cross_class_cases():
    inventory = _inventory()
    microstate = next(row for row in inventory["anomalies"] if row["type"] == "microstate")
    microstate["region_ids"].append("013")
    _cell(inventory, "013", "microstate").update({
        "status": "resolved_cases", "anomaly_ids": [microstate["anomaly_id"]],
    })
    inventory["anomalies"].append({
        "anomaly_id": "case-microstate-second",
        "type": "microstate",
        "region_ids": ["005"],
        "subject_ids": ["polity-shared"],
        "source_ids": ["source-anchor", "source-corroboration"],
        "resolution": "resolved",
    })
    _cell(inventory, "005", "microstate")["anomaly_ids"].append("case-microstate-second")
    claim = next(row for row in inventory["anomalies"] if row["type"] == "claim")
    claim["subject_ids"] = ["polity-shared"]

    validate_anomaly_inventory(inventory)
    assert len(inventory["census"]["cells"]) == 242


@pytest.mark.parametrize("mutation,match", [
    (lambda doc: doc["census"]["cells"].pop(), "exactly 242"),
    (lambda doc: doc["census"]["cells"].__setitem__(1, copy.deepcopy(doc["census"]["cells"][0])), "duplicate cell"),
    (lambda doc: doc["anomalies"][0].__setitem__("resolution", "pending_evidence"), "unresolved"),
    (lambda doc: doc["anomalies"][0].__setitem__("anomaly_id", "pending-case"), "non-placeholder"),
    (lambda doc: doc["anomalies"][0]["region_ids"].__setitem__(0, "999"), "invalid M49"),
    (lambda doc: doc["anomalies"][0].__setitem__("type", "unsupported"), "unsupported type"),
    (lambda doc: _cell(doc, "005", "microstate")["source_ids"].clear(), "reviewed survey sources"),
    (lambda doc: doc["census"].__setitem__("reviewer", "researcher example"), "distinct, named"),
    (lambda doc: doc["census"].__setitem__("review_date", "20 July 2026"), "ISO date"),
])
def test_census_rejects_incomplete_placeholder_invalid_and_unreviewed_closure(mutation, match):
    inventory = _inventory()
    mutation(inventory)
    with pytest.raises(SchemaValidationError, match=match):
        validate_anomaly_inventory(inventory)


def test_census_rejects_mismatched_links_and_orphan_anomalies():
    inventory = _inventory()
    microstate_cell = _cell(inventory, "005", "microstate")
    microstate_cell["anomaly_ids"] = ["case-claim"]
    with pytest.raises(SchemaValidationError, match="does not match"):
        validate_anomaly_inventory(inventory)

    inventory = _inventory()
    microstate_cell = _cell(inventory, "005", "microstate")
    microstate_cell.update({"status": "reviewed_none_found", "anomaly_ids": []})
    with pytest.raises(SchemaValidationError, match="orphan anomaly"):
        validate_anomaly_inventory(inventory)


@pytest.mark.parametrize("field,value,match", [
    ("schema_version", "0.2.0", "wrong schema/pass/date"),
    ("pass_id", "wrong-pass", "wrong schema/pass/date"),
    ("start_date", "1444-11-12", "wrong schema/pass/date"),
])
def test_inventory_rejects_wrong_schema_pass_or_date(field, value, match):
    inventory = _inventory()
    inventory[field] = value
    builder = _builder_module()
    with pytest.raises(SystemExit, match=match):
        builder._validate_inventory(inventory)


def test_inventory_build_is_byte_deterministic_under_input_reordering(tmp_path):
    builder = _builder_module()
    first = _inventory()
    second = copy.deepcopy(first)
    second["anomalies"].reverse()
    second["census"]["cells"].reverse()
    second["census"]["region_ids"].reverse()
    second["census"]["types"].reverse()
    input_a, input_b = tmp_path / "a.json", tmp_path / "b.json"
    input_a.write_text(json.dumps(first))
    input_b.write_text(json.dumps(second))
    output_a, output_b = tmp_path / "out-a", tmp_path / "out-b"
    builder.stage_inventory(Namespace(output_dir=output_a, inventory_input=input_a))
    builder.stage_inventory(Namespace(output_dir=output_b, inventory_input=input_b))
    assert (output_a / "anomaly_inventory.json").read_bytes() == (output_b / "anomaly_inventory.json").read_bytes()


def test_joint_handoff_reports_unknown_subject_unknown_source_and_unreviewed_surveys():
    builder = _builder_module()
    inventory = _inventory()
    documents = {
        "source_manifest.json": {"sources": [
            {"source_id": "source-anchor", "review_status": "reviewed", "source_type": "academic", "independence_group": "anchor"},
            {"source_id": "source-corroboration", "review_status": "planned", "source_type": "corroborating", "independence_group": "corroboration"},
            {"source_id": "source-survey", "review_status": "planned", "source_type": "academic", "independence_group": "survey"},
        ]},
        "gazetteer.json": {"polities": [{"polity_id": "polity-claim"}]},
    }
    inventory["anomalies"][0]["source_ids"].append("source-missing")
    findings = []
    builder._validate_anomaly_handoff(inventory, documents, findings)
    rules = {row["rule"] for row in findings}
    assert {
        "UNKNOWN_ANOMALY_SUBJECT", "UNKNOWN_ANOMALY_SOURCE", "UNREVIEWED_ANOMALY_SOURCE",
    } <= rules


def test_joint_handoff_accepts_reviewed_independent_sources_and_sourced_polities():
    builder = _builder_module()
    inventory = _inventory()
    source_rows = [
        {
            "source_id": "source-anchor", "review_status": "reviewed",
            "source_type": "primary", "independence_group": "archive-a",
        },
        {
            "source_id": "source-corroboration", "review_status": "reviewed",
            "source_type": "academic", "independence_group": "publisher-b",
        },
        {
            "source_id": "source-survey", "review_status": "reviewed",
            "source_type": "academic", "independence_group": "survey-c",
        },
    ]
    polity_ids = {subject for row in inventory["anomalies"] for subject in row["subject_ids"]}
    documents = {
        "source_manifest.json": {"sources": source_rows},
        "gazetteer.json": {"polities": [
            {"polity_id": polity_id, "source_ids": ["source-anchor"]}
            for polity_id in sorted(polity_ids)
        ]},
    }
    findings = []
    builder._validate_anomaly_handoff(inventory, documents, findings)
    assert findings == []


@pytest.mark.parametrize("message,rule", [
    ("anomaly inventory.census.cells must contain exactly 242 cells", "INCOMPLETE_ANOMALY_CENSUS"),
    ("cell link does not match anomaly case-a class/region", "INVALID_CENSUS_LINK"),
    ("orphan anomaly case-a is not linked", "ORPHAN_ANOMALY"),
    ("census review requires distinct, named researcher and reviewer identities", "INVALID_CENSUS_REVIEW"),
])
def test_handoff_maps_census_defects_to_actionable_rejection_rules(message, rule):
    assert _builder_module()._inventory_rejection_rule(message) == rule


def test_placeholder_seed_is_preserved_as_a_negative_fixture():
    fixture = json.loads((ROOT / "tests/fixtures/m25c/placeholder-anomaly-inventory.json").read_text())
    with pytest.raises(SchemaValidationError):
        validate_anomaly_inventory(fixture)
