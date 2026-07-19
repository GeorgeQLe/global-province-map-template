"""Roadmap contracts for globally certified historical eras."""

from __future__ import annotations

import copy
import json

import pytest
from jsonschema import Draft202012Validator

from gpm.historical import CasebookError, execute_casebook, load_casebook, project_fixture_runtime
from gpm.paths import PROJECT_ROOT
from gpm.schemas import SchemaValidationError, validate_historical_territory_status


CASEBOOK_PATH = PROJECT_ROOT / "tests" / "fixtures" / "m25a" / "casebook.json"


def test_historical_status_schema_is_valid_and_requires_canonical_identities():
    schema = json.loads(
        (PROJECT_ROOT / "schemas" / "historical-territory-status.schema.json").read_text(
            encoding="utf-8"
        )
    )
    Draft202012Validator.check_schema(schema)

    component = schema["properties"]["components"]["items"]
    assert {"territory_component_id", "political_unit_id", "geometry"} <= set(
        component["required"]
    )
    relationships = set(
        schema["properties"]["statuses"]["items"]["properties"]["relationship"]["enum"]
    )
    assert relationships == {
        "sovereign",
        "owner",
        "controller",
        "protector",
        "co-administrator",
        "occupier",
        "mandate-authority",
        "lessee",
        "claimant",
    }


def test_casebook_covers_every_required_class_and_test_surface():
    casebook = (PROJECT_ROOT / "docs" / "m25-hard-case-casebook.md").read_text(
        encoding="utf-8"
    )
    for class_name in (
        "Sovereign microstate",
        "Detached sovereign territory",
        "Foreign enclave / exclave",
        "Free / protected city",
        "Condominium / international zone",
        "Composite / dynastic territory",
        "Dependency / mandate / concession",
        "Disputed territory",
    ):
        assert class_name in casebook
    for surface in (
        "schema",
        "canonical-build",
        "runtime-pack",
        "visual",
        "picking",
        "LOD",
        "adjacency",
        "save/migration",
    ):
        assert surface in casebook


def test_executable_casebook_covers_all_classes_eras_and_surfaces():
    casebook = load_casebook(CASEBOOK_PATH)
    executions = execute_casebook(casebook)

    assert len(executions) == 8
    assert {execution.era for execution in executions} == {"1444", "1836", "1914", "1936"}
    assert all(len(execution.surfaces) == 8 for execution in executions)
    assert all(execution.visual_feature_count >= 1 for execution in executions)
    assert all(b"m25a-fixture-projection-not-runtime-pack" in execution.runtime_bytes for execution in executions)


def test_fixture_projection_is_order_independent_and_byte_deterministic():
    casebook = load_casebook(CASEBOOK_PATH)
    canonical = copy.deepcopy(casebook["cases"][2]["canonical"])
    expected = project_fixture_runtime(canonical)
    canonical["components"].reverse()
    canonical["political_units"].reverse()
    canonical["provinces"].reverse()
    canonical["statuses"].reverse()

    assert project_fixture_runtime(canonical) == expected
    assert [row["dense_index"] for row in expected["components"]] == list(
        range(len(expected["components"]))
    )


def test_historical_status_semantics_fail_closed_on_identity_and_merge_errors():
    casebook = load_casebook(CASEBOOK_PATH)
    canonical = copy.deepcopy(casebook["cases"][2]["canonical"])
    canonical["provinces"][0].pop("shared_administrative_unit_evidence_ids")
    with pytest.raises(SchemaValidationError, match="disconnected province"):
        validate_historical_territory_status(canonical)

    canonical = copy.deepcopy(casebook["cases"][0]["canonical"])
    canonical["statuses"][0]["actor_political_unit_id"] = "pu-unknown"
    with pytest.raises(SchemaValidationError, match="unknown actor"):
        validate_historical_territory_status(canonical)


def test_casebook_executes_picking_and_adjacency_expectations_not_just_labels():
    casebook = load_casebook(CASEBOOK_PATH)
    bad_pick = copy.deepcopy(casebook)
    bad_pick["cases"][0]["expectations"]["picks"][0]["point"] = [9, 9]
    with pytest.raises(CasebookError, match="picking mismatch"):
        execute_casebook(bad_pick)

    bad_adjacency = copy.deepcopy(casebook)
    bad_adjacency["cases"][5]["expectations"]["adjacent_component_pairs"] = []
    with pytest.raises(CasebookError, match="adjacency expectation"):
        execute_casebook(bad_adjacency)
