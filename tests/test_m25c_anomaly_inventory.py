"""Certification-grade schema-0.3 historical anomaly census contracts."""

from __future__ import annotations

import copy
import importlib.util
import json
from argparse import Namespace
from pathlib import Path

import pytest

from gpm.qa.m25c_census import CLASS_SEARCH_TERMS, review_ledger_findings
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
                "source_ids": [f"source-survey-{region_id}"],
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


def _documents(inventory: dict, *, survey_status: str = "reviewed") -> dict:
    source_rows = [
        {
            "source_id": "source-anchor",
            "review_status": "reviewed",
            "source_type": "primary",
            "independence_group": "archive-a",
            "url": "https://archive.example/anchor",
            "valid_from": "1400",
            "valid_to": "1500",
        },
        {
            "source_id": "source-corroboration",
            "review_status": "reviewed",
            "source_type": "academic",
            "independence_group": "publisher-b",
            "url": "https://publisher.example/corroboration",
            "valid_from": "1400",
            "valid_to": "1500",
        },
        {
            "source_id": "source-atlas",
            "review_status": "reviewed",
            "source_type": "academic",
            "independence_group": "atlas",
            "url": "https://atlas.example/world",
            "valid_from": "1400",
            "valid_to": "1500",
        },
    ]
    for region_id in sorted(WORLDWIDE_M49_SUBREGIONS):
        source_rows.append({
            "source_id": f"source-survey-{region_id}",
            "review_status": survey_status,
            "source_type": "academic",
            "independence_group": "regional-survey",
            "url": f"https://survey.example/{region_id}",
            "valid_from": "1400",
            "valid_to": "1500",
        })
    records = []
    for cell in inventory["census"]["cells"]:
        source_id = cell["source_ids"][0]
        records.append({
            "review_id": f"{cell['region_id']}/{cell['type']}",
            "region_id": cell["region_id"],
            "anomaly_type": cell["type"],
            "regional_survey_source_ids": [source_id],
            "source_locators": [{
                "source_id": source_id,
                "url": f"https://survey.example/{cell['region_id']}",
                "locator": f"Chapter {cell['region_id']} > 1400–1450",
            }],
            "queries": [f"{cell['region_id']} 1444 {sorted(CLASS_SEARCH_TERMS[cell['type']])[0]}"],
            "considered_leads": [{
                "lead": f"bounded {cell['region_id']} leads",
                "disposition": "accepted" if cell["anomaly_ids"] else "rejected",
                "failure_basis": [] if cell["anomaly_ids"] else ["insufficient_evidence"],
                "rationale": "Class-specific date and semantic disposition.",
                "supporting_source_ids": [source_id],
            }],
            "rationale": "Class-specific date and semantic disposition.",
            "supporting_source_ids": [source_id],
            "anomaly_ids": cell["anomaly_ids"],
            "conclusion": cell["notes"],
            "status": cell["status"],
        })
    polity_ids = {subject for row in inventory["anomalies"] for subject in row["subject_ids"]}
    return {
        "source_manifest.json": {"sources": source_rows},
        "gazetteer.json": {"polities": [
            {"polity_id": polity_id, "source_ids": ["source-anchor"]}
            for polity_id in sorted(polity_ids)
        ]},
        "anomaly_census_review_ledger.json": {
            "schema_version": "1.0.0",
            "document_type": "m25c_anomaly_census_review_ledger",
            "pass_id": inventory["pass_id"],
            "start_date": inventory["start_date"],
            "records": records,
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


def test_closed_census_does_not_manufacture_a_positive_case_for_every_search_class():
    inventory = _inventory()
    claim = next(row for row in inventory["anomalies"] if row["type"] == "claim")
    inventory["anomalies"].remove(claim)
    _cell(inventory, "005", "claim").update({
        "status": "reviewed_none_found",
        "anomaly_ids": [],
        "notes": "The historically supported title claim is non-geographic and retained outside the anomaly list.",
    })

    validate_anomaly_inventory(inventory)
    assert "claim" in inventory["census"]["types"]
    assert not any(row["type"] == "claim" for row in inventory["anomalies"])


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
    assert builder._canonicalize_inventory(first) == builder._canonicalize_inventory(second)


def test_joint_handoff_reports_unknown_subject_unknown_source_and_unreviewed_surveys():
    builder = _builder_module()
    inventory = _inventory()
    documents = _documents(inventory, survey_status="planned")
    next(
        row for row in documents["source_manifest.json"]["sources"]
        if row["source_id"] == "source-corroboration"
    )["review_status"] = "planned"
    documents["gazetteer.json"] = {"polities": [{"polity_id": "polity-claim"}]}
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
    documents = _documents(inventory)
    findings = []
    builder._validate_anomaly_handoff(inventory, documents, findings)
    assert findings == []


@pytest.mark.parametrize("mutation,code", [
    (lambda ledger: ledger["records"].pop(), "INCOMPLETE_REVIEW_LEDGER"),
    (lambda ledger: ledger["records"][0].update({"queries": []}), "MISSING_CLASS_QUERY"),
    (lambda ledger: ledger["records"][0].update({"considered_leads": []}), "MISSING_LEAD_DISPOSITION"),
    (lambda ledger: ledger["records"][0].update({"rationale": ""}), "MISSING_REVIEW_RATIONALE"),
])
def test_review_ledger_rejects_missing_cells_queries_leads_and_rationale(mutation, code):
    inventory = _inventory()
    documents = _documents(inventory)
    ledger = documents["anomaly_census_review_ledger.json"]
    mutation(ledger)
    findings = review_ledger_findings(
        inventory,
        ledger,
        documents["source_manifest.json"],
    )
    assert code in {row["code"] for row in findings}


def test_review_ledger_rejects_repeated_generic_regional_aliases():
    inventory = _inventory()
    documents = _documents(inventory)
    ledger = documents["anomaly_census_review_ledger.json"]
    for record in ledger["records"]:
        locator = record["source_locators"][0]
        locator.update({"url": "https://survey.example/generic", "locator": "Introduction"})
        source_id = record["regional_survey_source_ids"][0]
        next(
            row for row in documents["source_manifest.json"]["sources"]
            if row["source_id"] == source_id
        )["url"] = locator["url"]
    findings = review_ledger_findings(
        inventory,
        ledger,
        documents["source_manifest.json"],
    )
    assert "DUPLICATED_GENERIC_REGIONAL_SURVEY" in {row["code"] for row in findings}


def test_review_ledger_rejects_unknown_unreviewed_and_mismatched_sources():
    inventory = _inventory()
    documents = _documents(inventory)
    record = documents["anomaly_census_review_ledger.json"]["records"][0]
    source_id = record["regional_survey_source_ids"][0]
    next(
        row for row in documents["source_manifest.json"]["sources"]
        if row["source_id"] == source_id
    )["review_status"] = "planned"
    record["supporting_source_ids"] = ["unknown-source"]
    findings = review_ledger_findings(
        inventory,
        documents["anomaly_census_review_ledger.json"],
        documents["source_manifest.json"],
    )
    codes = {row["code"] for row in findings}
    assert {"UNREVIEWED_REVIEW_SOURCE", "UNKNOWN_REVIEW_SOURCE", "REVIEW_LEDGER_CELL_MISMATCH"} <= codes


def test_review_ledger_rejects_templated_negatives_and_incomplete_failure_basis():
    inventory = _inventory()
    documents = _documents(inventory)
    record = next(
        row for row in documents["anomaly_census_review_ledger.json"]["records"]
        if row["status"] == "reviewed_none_found"
    )
    record["conclusion"] = "No qualifying case was established in the bounded regional and class-specific review."
    record["considered_leads"][0]["failure_basis"] = []
    findings = review_ledger_findings(
        inventory,
        documents["anomaly_census_review_ledger.json"],
        documents["source_manifest.json"],
    )
    codes = {row["code"] for row in findings}
    assert {"TEMPLATED_NEGATIVE_RATIONALE", "INCOMPLETE_LEAD_DISPOSITION"} <= codes


def test_review_ledger_requires_exact_rejected_lead_and_live_url_coverage():
    inventory = _inventory()
    documents = _documents(inventory)
    ledger = documents["anomaly_census_review_ledger.json"]
    rejected = {"records": []}
    access = {"records": []}
    findings = review_ledger_findings(
        inventory,
        ledger,
        documents["source_manifest.json"],
        rejected,
        access,
    )
    codes = {row["code"] for row in findings}
    assert {"REJECTED_LEAD_COVERAGE_MISMATCH", "SOURCE_ACCESS_AUDIT_COVERAGE_MISMATCH"} <= codes


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
