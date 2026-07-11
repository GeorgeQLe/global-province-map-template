import copy
import json

import pytest

from conftest import PROJECT_ROOT
from gpm.manifest import build_planned_source_manifest
from gpm.schemas import SchemaValidationError, load_schema, validate_source_manifest


def test_schema_files_are_machine_readable_json_schema_documents():
    schema_paths = sorted((PROJECT_ROOT / "schemas").glob("*.schema.json"))
    assert {path.name for path in schema_paths} == {
        "adjacency-record.schema.json",
        "atlas-manifest.schema.json",
        "attribution-record.schema.json",
        "curator-bundle.schema.json",
        "era-geometry-lineage.schema.json",
        "era-geometry-pack.schema.json",
        "golden-checks.schema.json",
        "license-audit-report.schema.json",
        "multi-era-migration-notes.schema.json",
        "multi-era-pack.schema.json",
        "province-entity.schema.json",
        "region-entity.schema.json",
        "release-manifest.schema.json",
        "scenario-definition.schema.json",
        "scenario-diff-report.schema.json",
        "scenario-ownership-record.schema.json",
        "scenario-politics-qa-report.schema.json",
        "source-manifest.schema.json",
        "tileset-manifest.schema.json",
        "topology-qa-report.schema.json",
    }

    for path in schema_paths:
        with path.open("r", encoding="utf-8") as file:
            schema = json.load(file)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["type"] == "object"


def test_source_manifest_schema_accepts_planned_default_manifest():
    schema = load_schema("source-manifest")
    manifest = build_planned_source_manifest("modern-small")

    assert schema["properties"]["schema_version"]["const"] == "0.1.0"
    validate_source_manifest(manifest)
    assert [source["id"] for source in manifest["sources"]] == ["natural_earth", "geoboundaries"]
    assert manifest["sources"][0]["version"] == "natural-earth-10m"
    assert manifest["sources"][0]["artifacts"][0]["status"] == "planned"


def test_source_manifest_schema_rejects_missing_required_field():
    manifest = build_planned_source_manifest("modern-small")
    invalid = copy.deepcopy(manifest)
    del invalid["sources"][0]["license"]

    with pytest.raises(SchemaValidationError, match="license"):
        validate_source_manifest(invalid)
