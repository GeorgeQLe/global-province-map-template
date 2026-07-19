from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .paths import SCHEMA_DIR


class SchemaValidationError(ValueError):
    """Raised when a document does not satisfy a project schema check."""


def load_schema(name: str) -> dict[str, Any]:
    filename = name if name.endswith(".json") else f"{name}.schema.json"
    path = SCHEMA_DIR / filename
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def validate_source_manifest(manifest: dict[str, Any]) -> None:
    """Small built-in validator for the source manifest contract.

    The JSON Schema files are the canonical machine-readable contracts. This
    validator keeps Phase 1 tests dependency-free until the geospatial stack is
    introduced.
    """
    schema = load_schema("source-manifest")
    _require_object(manifest, "manifest")
    _require_keys(manifest, schema["required"], "manifest")
    if manifest["schema_version"] != schema["properties"]["schema_version"]["const"]:
        raise SchemaValidationError("manifest.schema_version must be 0.1.0")
    if manifest["manifest_type"] not in {"planned", "build"}:
        raise SchemaValidationError("manifest.manifest_type must be planned or build")

    build = manifest["build"]
    _require_object(build, "manifest.build")
    _require_keys(build, ["profile_id", "generated_at", "generator_version"], "manifest.build")

    sources = manifest["sources"]
    if not isinstance(sources, list) or not sources:
        raise SchemaValidationError("manifest.sources must be a non-empty list")
    seen_ids: set[str] = set()
    for index, source in enumerate(sources):
        path = f"manifest.sources[{index}]"
        _require_object(source, path)
        _require_keys(
            source,
            [
                "id",
                "name",
                "status",
                "source_url",
                "access_date",
                "version",
                "original_format",
                "checksum",
                "license",
                "attribution_text",
                "default_build",
                "optional",
                "isolated",
                "restricted",
                "enabled",
                "layers",
                "artifacts",
                "transformation_steps",
                "downstream_files",
            ],
            path,
        )
        if source["id"] in seen_ids:
            raise SchemaValidationError(f"{path}.id duplicates source id '{source['id']}'")
        seen_ids.add(source["id"])
        for key in ["default_build", "optional", "isolated", "restricted", "enabled"]:
            if not isinstance(source[key], bool):
                raise SchemaValidationError(f"{path}.{key} must be a boolean")
        for key in ["layers", "transformation_steps", "downstream_files"]:
            if not isinstance(source[key], list):
                raise SchemaValidationError(f"{path}.{key} must be a list")
        if source["status"] not in {"planned", "downloaded", "processed", "excluded"}:
            raise SchemaValidationError(f"{path}.status has unsupported value '{source['status']}'")
        _require_nullable_string(source["source_url"], f"{path}.source_url")
        _require_nullable_string(source["access_date"], f"{path}.access_date")
        _require_nullable_string(source["version"], f"{path}.version")
        _require_nullable_string(source["original_format"], f"{path}.original_format")
        _require_nullable_string(source["checksum"], f"{path}.checksum")
        _validate_artifacts(source["artifacts"], path)


def validate_location_fabric_manifest(manifest: dict[str, Any]) -> None:
    """Validate the revision and input-lineage invariants of an M23 fabric manifest."""
    schema = load_schema("location-fabric-manifest")
    _require_object(manifest, "manifest")
    _require_keys(manifest, schema["required"], "manifest")
    if manifest["schema_version"] != "0.1.0" or manifest["manifest_type"] != "location_fabric":
        raise SchemaValidationError("invalid M23 location fabric manifest type or version")
    if manifest["fabric_revision"] != manifest["output_fabric_revision"]:
        raise SchemaValidationError("manifest.fabric_revision must equal output_fabric_revision")
    inputs = manifest["inputs"]
    if not isinstance(inputs, list) or not inputs:
        raise SchemaValidationError("manifest.inputs must be a non-empty list")
    for index, item in enumerate(inputs):
        path = f"manifest.inputs[{index}]"
        _require_object(item, path)
        _require_keys(item, ["role", "path", "format", "license_lineage"], path)
        if item["role"] not in {"land", "admin0", "admin1", "population", "settlement", "terrain", "historical"}:
            raise SchemaValidationError(f"{path}.role is unsupported")
        if not isinstance(item["path"], str) or not item["path"]:
            raise SchemaValidationError(f"{path}.path must be a non-empty string")
        if not isinstance(item["license_lineage"], list) or not item["license_lineage"]:
            raise SchemaValidationError(f"{path}.license_lineage must be non-empty")
    if not any(item["role"] == "land" for item in inputs):
        raise SchemaValidationError("manifest.inputs must declare the land source")
    if not isinstance(manifest["files"], list) or not all(isinstance(item, str) and item for item in manifest["files"]):
        raise SchemaValidationError("manifest.files must contain non-empty paths")


def validate_location_lineage(lineage: dict[str, Any]) -> None:
    """Validate source/output revisions and parent/child migration records."""
    schema = load_schema("location-lineage")
    _require_object(lineage, "lineage")
    _require_keys(lineage, schema["required"], "lineage")
    if lineage["fabric_revision"] != lineage["output_fabric_revision"]:
        raise SchemaValidationError("lineage.fabric_revision must equal output_fabric_revision")
    if not isinstance(lineage["events"], list):
        raise SchemaValidationError("lineage.events must be a list")
    for index, event in enumerate(lineage["events"]):
        path = f"lineage.events[{index}]"
        _require_object(event, path)
        _require_keys(event, ["operation", "parent_location_ids", "child_location_ids"], path)
        for key in ("parent_location_ids", "child_location_ids"):
            if not isinstance(event[key], list) or not all(isinstance(item, str) and item for item in event[key]):
                raise SchemaValidationError(f"{path}.{key} must contain location IDs")


def validate_release_manifest(manifest: dict[str, Any]) -> None:
    """Validate core invariants of an M9 release manifest document."""
    schema = load_schema("release-manifest")
    _require_object(manifest, "manifest")
    _require_keys(manifest, schema["required"], "manifest")
    if manifest["schema_version"] != schema["properties"]["schema_version"]["const"]:
        raise SchemaValidationError("manifest.schema_version must be 0.1.0")
    if manifest["manifest_type"] != "release":
        raise SchemaValidationError("manifest.manifest_type must be release")
    if manifest["release_channel"] not in {"alpha", "beta", "stable"}:
        raise SchemaValidationError("manifest.release_channel must be alpha, beta, or stable")
    tiers = manifest["quality_tiers"]
    _require_object(tiers, "manifest.quality_tiers")
    _require_keys(tiers, ["geometry", "politics"], "manifest.quality_tiers")
    allowed_tiers = {"scaffold-baseline", "curated-politics", "period-geometry"}
    for key in ("geometry", "politics"):
        if tiers[key] not in allowed_tiers:
            raise SchemaValidationError(
                f"manifest.quality_tiers.{key} must be one of {sorted(allowed_tiers)}"
            )
    if not isinstance(manifest["scenario_set"], list):
        raise SchemaValidationError("manifest.scenario_set must be a list")
    if not isinstance(manifest["is_sample"], bool):
        raise SchemaValidationError("manifest.is_sample must be a boolean")
    counts = manifest["counts"]
    _require_object(counts, "manifest.counts")
    for key in ("provinces", "sea_zones", "adjacency_rows"):
        if key not in counts:
            raise SchemaValidationError(f"manifest.counts missing required key: {key}")
        if not isinstance(counts[key], int) or counts[key] < 0:
            raise SchemaValidationError(f"manifest.counts.{key} must be a non-negative integer")
    if not isinstance(manifest["files"], list) or not all(
        isinstance(item, str) and item for item in manifest["files"]
    ):
        raise SchemaValidationError("manifest.files must be a list of non-empty strings")


def validate_license_audit_report(report: dict[str, Any]) -> None:
    """Validate core invariants of an M14 license audit report document."""
    schema = load_schema("license-audit-report")
    _require_object(report, "report")
    _require_keys(report, schema["required"], "report")
    if report["schema_version"] != schema["properties"]["schema_version"]["const"]:
        raise SchemaValidationError("report.schema_version must be 0.1.0")
    if report["report_type"] != "license-audit":
        raise SchemaValidationError("report.report_type must be license-audit")
    if not isinstance(report["passed"], bool):
        raise SchemaValidationError("report.passed must be a boolean")
    if report["release_channel"] not in {"alpha", "beta", "stable"}:
        raise SchemaValidationError("report.release_channel must be alpha, beta, or stable")
    for key in ("error_count", "warning_count"):
        if not isinstance(report[key], int) or report[key] < 0:
            raise SchemaValidationError(f"report.{key} must be a non-negative integer")
    for key in ("public_source_ids", "isolated_source_ids", "restricted_source_ids", "findings", "attribution_records"):
        if not isinstance(report[key], list):
            raise SchemaValidationError(f"report.{key} must be a list")
    for index, finding in enumerate(report["findings"]):
        path = f"report.findings[{index}]"
        _require_object(finding, path)
        _require_keys(finding, ["code", "severity", "message"], path)
        if finding["severity"] not in {"error", "warning", "info"}:
            raise SchemaValidationError(f"{path}.severity must be error, warning, or info")


def validate_atlas_manifest(manifest: dict[str, Any]) -> None:
    """Validate core invariants of an M10 atlas pack manifest document."""
    schema = load_schema("atlas-manifest")
    _require_object(manifest, "manifest")
    _require_keys(manifest, schema["required"], "manifest")
    if manifest["schema_version"] != schema["properties"]["schema_version"]["const"]:
        raise SchemaValidationError("manifest.schema_version must be 0.1.0")
    if manifest["pack_type"] != "atlas":
        raise SchemaValidationError("manifest.pack_type must be atlas")
    if not isinstance(manifest["scenarios"], list) or not manifest["scenarios"]:
        raise SchemaValidationError("manifest.scenarios must be a non-empty list")
    if not all(isinstance(item, str) and item for item in manifest["scenarios"]):
        raise SchemaValidationError("manifest.scenarios must contain non-empty strings")
    counts = manifest["counts"]
    _require_object(counts, "manifest.counts")
    for key in (
        "provinces",
        "scenarios",
        "scenario_ownership_rows",
        "unique_tags",
        "legend_entries",
        "attribution_records",
    ):
        if key not in counts:
            raise SchemaValidationError(f"manifest.counts missing required key: {key}")
        if not isinstance(counts[key], int) or counts[key] < 0:
            raise SchemaValidationError(f"manifest.counts.{key} must be a non-negative integer")
    if not isinstance(manifest["files"], list) or not all(
        isinstance(item, str) and item for item in manifest["files"]
    ):
        raise SchemaValidationError("manifest.files must be a list of non-empty strings")


def validate_tileset_manifest(manifest: dict[str, Any]) -> None:
    """Validate core invariants of an M19 tileset (PMTiles) manifest."""
    schema = load_schema("tileset-manifest")
    _require_object(manifest, "manifest")
    _require_keys(manifest, schema["required"], "manifest")
    if manifest["schema_version"] != schema["properties"]["schema_version"]["const"]:
        raise SchemaValidationError("manifest.schema_version must be 0.1.0")
    if manifest["pack_type"] != "tileset":
        raise SchemaValidationError("manifest.pack_type must be tileset")
    if manifest["backend"] not in {"native", "tippecanoe"}:
        raise SchemaValidationError("manifest.backend must be native or tippecanoe")
    for key in ("feature_count", "tile_count", "min_zoom", "max_zoom"):
        if not isinstance(manifest[key], int) or manifest[key] < 0:
            raise SchemaValidationError(f"manifest.{key} must be a non-negative integer")
    if manifest["max_zoom"] < manifest["min_zoom"]:
        raise SchemaValidationError("manifest.max_zoom must be >= min_zoom")
    bounds = manifest["bounds"]
    _require_object(bounds, "manifest.bounds")
    for key in ("west", "south", "east", "north"):
        if key not in bounds or not isinstance(bounds[key], (int, float)):
            raise SchemaValidationError(f"manifest.bounds.{key} must be a number")
    if not isinstance(manifest["layer_name"], str) or not manifest["layer_name"]:
        raise SchemaValidationError("manifest.layer_name must be a non-empty string")
    if not isinstance(manifest["pmtiles"], str) or not manifest["pmtiles"]:
        raise SchemaValidationError("manifest.pmtiles must be a non-empty string")



def validate_scenario_definition(document: dict[str, Any]) -> None:
    """Validate core invariants of an M8 scenario definition document."""
    # Prefer the dedicated scenario module validator so CLI and loaders share one path.
    from gpm.scenarios.resolve import ScenarioError, validate_scenario_document

    try:
        validate_scenario_document(document)
    except ScenarioError as exc:
        raise SchemaValidationError(str(exc)) from exc


def validate_topology_qa_report(report: dict[str, Any]) -> None:
    """Validate the core invariants of the topology QA report contract."""
    schema = load_schema("topology-qa-report")
    _require_object(report, "report")
    _require_keys(report, schema["required"], "report")
    if report["schema_version"] != schema["properties"]["schema_version"]["const"]:
        raise SchemaValidationError("report.schema_version must be 0.1.0")
    if report["report_type"] != "topology_qa":
        raise SchemaValidationError("report.report_type must be topology_qa")
    if report["status"] not in {"pass", "fail"}:
        raise SchemaValidationError("report.status must be pass or fail")

    _require_object(report["inputs"], "report.inputs")
    _require_keys(
        report["inputs"],
        ["province_input", "adjacency_input", "natural_earth_admin0_mask"],
        "report.inputs",
    )
    _require_object(report["thresholds"], "report.thresholds")
    _require_keys(
        report["thresholds"],
        ["max_overlap_area_sq_km", "max_gap_component_area_sq_km", "min_shared_border_km"],
        "report.thresholds",
    )
    _require_object(report["summary"], "report.summary")
    _require_keys(
        report["summary"],
        [
            "province_count",
            "land_province_count",
            "adjacency_count",
            "error_count",
            "warning_count",
            "isolated_province_count",
            "connected_component_count",
            "analysis",
        ],
        "report.summary",
    )
    _validate_findings_list(report["findings"], report["summary"], "report")
    expected_status = "fail" if report["summary"]["error_count"] else "pass"
    if report["status"] != expected_status:
        raise SchemaValidationError("report.status does not match error findings")


def validate_era_geometry_pack(document: dict[str, Any]) -> None:
    """Validate core invariants of an M15 era-geometry pack definition."""
    from gpm.era_geometry.packs import EraGeometryPackError
    from gpm.era_geometry.packs import validate_era_geometry_pack as _validate

    try:
        _validate(document)
    except EraGeometryPackError as exc:
        raise SchemaValidationError(str(exc)) from exc


def validate_multi_era_pack(document: dict[str, Any]) -> None:
    """Validate core invariants of an M16 multi-era pack definition."""
    from gpm.multi_era.packs import MultiEraPackError
    from gpm.multi_era.packs import validate_multi_era_pack as _validate

    try:
        _validate(document)
    except MultiEraPackError as exc:
        raise SchemaValidationError(str(exc)) from exc


def validate_multi_era_migration_notes(document: dict[str, Any]) -> None:
    """Validate core invariants of an M16 multi-era migration notes document."""
    schema = load_schema("multi-era-migration-notes")
    _require_object(document, "migration")
    _require_keys(document, schema["required"], "migration")
    if document["schema_version"] != schema["properties"]["schema_version"]["const"]:
        raise SchemaValidationError("migration.schema_version must be 0.1.0")
    if document["document_type"] != "multi-era-migration-notes":
        raise SchemaValidationError(
            "migration.document_type must be multi-era-migration-notes"
        )
    if not isinstance(document["pack_id"], str) or not document["pack_id"]:
        raise SchemaValidationError("migration.pack_id must be a non-empty string")
    if not isinstance(document["summary"], str) or not document["summary"].strip():
        raise SchemaValidationError("migration.summary must be a non-empty string")
    eras = document["eras"]
    if not isinstance(eras, list) or len(eras) < 2:
        raise SchemaValidationError("migration.eras must be a list of at least two eras")
    guidance = document["consumer_guidance"]
    if not isinstance(guidance, list) or not all(isinstance(item, str) for item in guidance):
        raise SchemaValidationError("migration.consumer_guidance must be a list of strings")


def validate_era_geometry_lineage(document: dict[str, Any]) -> None:
    """Validate core invariants of an M15 era-geometry lineage map."""
    schema = load_schema("era-geometry-lineage")
    _require_object(document, "lineage")
    _require_keys(document, schema["required"], "lineage")
    if document["schema_version"] != schema["properties"]["schema_version"]["const"]:
        raise SchemaValidationError("lineage.schema_version must be 0.1.0")
    if document["document_type"] != "era-geometry-lineage":
        raise SchemaValidationError("lineage.document_type must be era-geometry-lineage")
    if not isinstance(document["pack_id"], str) or not document["pack_id"]:
        raise SchemaValidationError("lineage.pack_id must be a non-empty string")
    if not isinstance(document["era"], str) or not document["era"]:
        raise SchemaValidationError("lineage.era must be a non-empty string")
    if not isinstance(document["row_count"], int) or document["row_count"] < 0:
        raise SchemaValidationError("lineage.row_count must be a non-negative integer")
    rows = document["rows"]
    if not isinstance(rows, list):
        raise SchemaValidationError("lineage.rows must be a list")
    if document["row_count"] != len(rows):
        raise SchemaValidationError("lineage.row_count does not match len(rows)")
    allowed_ops = {
        "identity",
        "replace",
        "split_child",
        "merge_parent",
        "reshape",
    }
    for index, row in enumerate(rows):
        path = f"lineage.rows[{index}]"
        _require_object(row, path)
        _require_keys(
            row,
            ["era_province_id", "scaffold_province_id", "operation"],
            path,
        )
        for key in ("era_province_id", "scaffold_province_id", "operation"):
            if not isinstance(row[key], str) or not row[key].strip():
                raise SchemaValidationError(f"{path}.{key} must be a non-empty string")
        if row["operation"] not in allowed_ops:
            raise SchemaValidationError(
                f"{path}.operation must be one of {sorted(allowed_ops)}"
            )


def validate_curator_bundle(document: dict[str, Any]) -> None:
    """Validate core invariants of an M17 curator-bundle manifest."""
    from gpm.curation.bundles import CuratorBundleError
    from gpm.curation.bundles import validate_curator_bundle as _validate

    try:
        _validate(document, check_files=False, check_scenarios=False)
    except CuratorBundleError as exc:
        raise SchemaValidationError(str(exc)) from exc


def validate_scenario_diff_report(report: dict[str, Any]) -> None:
    """Validate core invariants of an M17 ownership diff report."""
    schema = load_schema("scenario-diff-report")
    _require_object(report, "report")
    _require_keys(report, schema["required"], "report")
    if report["schema_version"] != schema["properties"]["schema_version"]["const"]:
        raise SchemaValidationError("report.schema_version must be 0.1.0")
    if report["report_type"] != "scenario_ownership_diff":
        raise SchemaValidationError("report.report_type must be scenario_ownership_diff")
    if report.get("milestone") != "M17":
        raise SchemaValidationError("report.milestone must be M17")
    if report["status"] not in {"identical", "changed"}:
        raise SchemaValidationError("report.status must be identical or changed")
    _require_object(report["base"], "report.base")
    _require_object(report["target"], "report.target")
    _require_object(report["summary"], "report.summary")
    _require_keys(
        report["summary"],
        [
            "base_row_count",
            "target_row_count",
            "shared_province_count",
            "owner_change_count",
            "controller_change_count",
            "disputed_change_count",
            "added_province_count",
            "removed_province_count",
            "contested_province_count",
        ],
        "report.summary",
    )
    if not isinstance(report["owner_count_delta"], dict):
        raise SchemaValidationError("report.owner_count_delta must be an object")
    if not isinstance(report["changes"], list):
        raise SchemaValidationError("report.changes must be a list")


def validate_scenario_politics_qa_report(report: dict[str, Any]) -> None:
    """Validate the core invariants of the M11 scenario politics QA report."""
    schema = load_schema("scenario-politics-qa-report")
    _require_object(report, "report")
    _require_keys(report, schema["required"], "report")
    if report["schema_version"] != schema["properties"]["schema_version"]["const"]:
        raise SchemaValidationError("report.schema_version must be 0.1.0")
    if report["report_type"] != "scenario_politics_qa":
        raise SchemaValidationError("report.report_type must be scenario_politics_qa")
    if report.get("milestone") != "M11":
        raise SchemaValidationError("report.milestone must be M11")
    if report["status"] not in {"pass", "fail"}:
        raise SchemaValidationError("report.status must be pass or fail")
    if not isinstance(report.get("profile_id"), str) or not report["profile_id"]:
        raise SchemaValidationError("report.profile_id must be a non-empty string")
    if not isinstance(report.get("scenario_id"), str) or not report["scenario_id"]:
        raise SchemaValidationError("report.scenario_id must be a non-empty string")

    _require_object(report["inputs"], "report.inputs")
    _require_keys(
        report["inputs"],
        [
            "province_input",
            "adjacency_input",
            "scenario_definition",
            "ownership_input",
            "golden_input",
        ],
        "report.inputs",
    )
    _require_object(report["thresholds"], "report.thresholds")
    _require_keys(
        report["thresholds"],
        ["max_owner_components", "min_provinces_for_fragment_check"],
        "report.thresholds",
    )
    _require_object(report["summary"], "report.summary")
    _require_keys(
        report["summary"],
        [
            "land_province_count",
            "ownership_row_count",
            "owner_tag_count",
            "error_count",
            "warning_count",
            "unknown_tag_finding_count",
            "orphan_tag_finding_count",
            "analysis",
        ],
        "report.summary",
    )
    analysis = report["summary"]["analysis"]
    _require_object(analysis, "report.summary.analysis")
    _require_keys(analysis, ["adjacency", "golden"], "report.summary.analysis")
    for key in ("adjacency", "golden"):
        if analysis[key] not in {"complete", "incomplete", "skipped"}:
            raise SchemaValidationError(
                f"report.summary.analysis.{key} must be complete, incomplete, or skipped"
            )
    _validate_findings_list(report["findings"], report["summary"], "report")
    expected_status = "fail" if report["summary"]["error_count"] else "pass"
    if report["status"] != expected_status:
        raise SchemaValidationError("report.status does not match error findings")


def validate_start_date_pass_manifest(document: dict[str, Any]) -> None:
    """Validate the M24 independently releasable pass manifest."""
    schema = load_schema("start-date-pass-manifest")
    _m24_header(document, "manifest", "start_date_research_pass", schema)
    _require_keys(document, ["version", "era", "fabric_revision", "geometry_revision", "generated_at", "scope", "artifacts"], "manifest")
    if document["artifact_version"] != document["version"]:
        raise SchemaValidationError("manifest.artifact_version must equal manifest.version")
    scope = document["scope"]
    _require_object(scope, "manifest.scope")
    _require_keys(scope, ["regions", "priority_regions", "layers"], "manifest.scope")
    for key in ("regions", "priority_regions", "layers"):
        _string_list(scope[key], f"manifest.scope.{key}", nonempty=True)
    if not set(scope["priority_regions"]).issubset(scope["regions"]):
        raise SchemaValidationError("manifest.scope.priority_regions must be included in regions")
    required_layers = {"geometry", "politics", "hierarchy", "gazetteer_relationships"}
    if not required_layers.issubset(scope["layers"]):
        raise SchemaValidationError(f"manifest.scope.layers must include {sorted(required_layers)}")
    artifacts = document["artifacts"]
    _require_object(artifacts, "manifest.artifacts")
    required = ["dossier", "source_manifest", "boundary_registry", "polity_gazetteer", "location_assignments", "golden_borders", "full_build_geometry", "coverage_matrix", "changelog"]
    _require_keys(artifacts, required, "manifest.artifacts")
    for kind in required:
        record = artifacts[kind]
        _require_object(record, f"manifest.artifacts.{kind}")
        _require_keys(record, ["path", "version", "sha256"], f"manifest.artifacts.{kind}")
        _nonempty_string(record["path"], f"manifest.artifacts.{kind}.path")
        _nonempty_string(record["version"], f"manifest.artifacts.{kind}.version")
        if not isinstance(record["sha256"], str) or not re.fullmatch(r"[0-9a-fA-F]{64}", record["sha256"]):
            raise SchemaValidationError(f"manifest.artifacts.{kind}.sha256 must be a 64-character hexadecimal digest")
    if document["schema_version"] == "0.2.0":
        _require_keys(document, ["review"], "manifest")
        review = document["review"]
        _require_object(review, "manifest.review")
        _require_keys(review, ["manifest_path", "sha256", "generator", "reviewer", "status"], "manifest.review")
        for key in ("manifest_path", "generator", "reviewer"):
            _nonempty_string(review[key], f"manifest.review.{key}")
        if review["generator"] == review["reviewer"]:
            raise SchemaValidationError("manifest.review reviewer must be independent from generator")
        if review["status"] != "accepted":
            raise SchemaValidationError("manifest.review.status must be accepted")
        if not isinstance(review["sha256"], str) or not re.fullmatch(r"[0-9a-fA-F]{64}", review["sha256"]):
            raise SchemaValidationError("manifest.review.sha256 must be a SHA-256 digest")


def validate_start_date_source_manifest(document: dict[str, Any]) -> None:
    schema = load_schema("start-date-source-manifest")
    _m24_header(document, "source manifest", "start_date_source_manifest", schema)
    _require_keys(document, ["sources", "conflict_resolution_notes"], "source manifest")
    sources = document["sources"]
    if not isinstance(sources, list) or not sources:
        raise SchemaValidationError("source manifest.sources must be non-empty")
    seen: set[str] = set()
    for index, source in enumerate(sources):
        path = f"source manifest.sources[{index}]"
        _require_object(source, path)
        _require_keys(source, ["source_id", "citation", "url", "access_date", "version", "license", "checksum", "transformations", "review_status"], path)
        source_id = _nonempty_string(source["source_id"], f"{path}.source_id")
        if source_id in seen:
            raise SchemaValidationError(f"{path}.source_id duplicates {source_id}")
        seen.add(source_id)
        for key in ("citation", "license"):
            _nonempty_string(source[key], f"{path}.{key}")
        for key in ("url", "access_date", "version", "checksum"):
            _nullable_string(source[key], f"{path}.{key}")
        _string_list(source["transformations"], f"{path}.transformations")
        if source["review_status"] not in {"planned", "reviewed", "rejected"}:
            raise SchemaValidationError(f"{path}.review_status is unsupported")
        if document["schema_version"] == "0.2.0":
            _require_keys(source, ["source_type", "valid_from", "valid_to", "independence_group", "derived_artifacts"], path)
            if source["source_type"] not in {"academic", "primary", "corroborating", "soft_corroboration", "negative_control"}:
                raise SchemaValidationError(f"{path}.source_type is unsupported")
            for key in ("valid_from", "valid_to"):
                _nullable_string(source[key], f"{path}.{key}")
            _nonempty_string(source["independence_group"], f"{path}.independence_group")
            if not isinstance(source["derived_artifacts"], list):
                raise SchemaValidationError(f"{path}.derived_artifacts must be an array")
            for ai, artifact in enumerate(source["derived_artifacts"]):
                apath = f"{path}.derived_artifacts[{ai}]"
                _require_object(artifact, apath)
                _require_keys(artifact, ["artifact_id", "role", "path", "sha256", "media_type"], apath)
                for key in ("artifact_id", "role", "path", "media_type"):
                    _nonempty_string(artifact[key], f"{apath}.{key}")
                if not isinstance(artifact["sha256"], str) or not re.fullmatch(r"[0-9a-fA-F]{64}", artifact["sha256"]):
                    raise SchemaValidationError(f"{apath}.sha256 must be a SHA-256 digest")
    _string_list(document["conflict_resolution_notes"], "source manifest.conflict_resolution_notes")


def validate_historical_boundary_registry(document: dict[str, Any]) -> None:
    schema = load_schema("historical-boundary-registry")
    _m24_header(document, "boundary registry", "historical_boundary_registry", schema)
    if document.get("type") != "FeatureCollection" or not isinstance(document.get("features"), list):
        raise SchemaValidationError("boundary registry must be a GeoJSON FeatureCollection")
    seen: set[str] = set()
    for index, feature in enumerate(document["features"]):
        path = f"boundary registry.features[{index}]"
        _require_object(feature, path)
        if feature.get("type") != "Feature" or not isinstance(feature.get("geometry"), dict):
            raise SchemaValidationError(f"{path} must be a GeoJSON Feature with geometry")
        try:
            from shapely.geometry import shape
            geometry = shape(feature["geometry"])
        except Exception as exc:
            raise SchemaValidationError(f"{path}.geometry is invalid: {exc}") from exc
        if geometry.is_empty or not geometry.is_valid or geometry.geom_type not in {"LineString", "MultiLineString", "Polygon", "MultiPolygon"}:
            raise SchemaValidationError(f"{path}.geometry must be a valid non-empty line or polygon")
        props = feature.get("properties")
        _require_object(props, f"{path}.properties")
        required = ["feature_id", "geometry_revision", "valid_from", "valid_to", "date_precision", "semantics", "side_polity_ids", "source_ids", "license_lineage", "confidence", "uncertainty_notes", "classification", "geographic_scope", "start_date_programs"]
        _require_keys(props, required, f"{path}.properties")
        feature_id = _nonempty_string(props["feature_id"], f"{path}.properties.feature_id")
        if feature_id in seen:
            raise SchemaValidationError(f"duplicate boundary feature_id: {feature_id}")
        seen.add(feature_id)
        for key in ("geometry_revision", "semantics", "confidence", "uncertainty_notes", "geographic_scope"):
            _nonempty_string(props[key], f"{path}.properties.{key}")
        for key in ("valid_from", "valid_to"):
            _nullable_string(props[key], f"{path}.properties.{key}")
        if props["date_precision"] not in {"day", "month", "year", "decade", "circa", "unknown"}:
            raise SchemaValidationError(f"{path}.properties.date_precision is unsupported")
        if props["classification"] not in {"hard_constraint", "soft_evidence"}:
            raise SchemaValidationError(f"{path}.properties.classification is unsupported")
        sides = props["side_polity_ids"]
        _require_object(sides, f"{path}.properties.side_polity_ids")
        _require_keys(sides, ["left", "right"], f"{path}.properties.side_polity_ids")
        if set(sides) != {"left", "right"} or sides["left"] == sides["right"]:
            raise SchemaValidationError(f"{path}.properties.side_polity_ids must name distinct left/right polities")
        for side in ("left", "right"):
            _nonempty_string(sides[side], f"{path}.properties.side_polity_ids.{side}")
        for key in ("source_ids", "license_lineage", "start_date_programs"):
            _string_list(props[key], f"{path}.properties.{key}", nonempty=True)
        if document["schema_version"] == "0.2.0" and props["classification"] == "hard_constraint":
            _require_keys(props, ["derived_geometry_artifact_id", "georeferencing", "error_budget_km"], f"{path}.properties")
            _nonempty_string(props["derived_geometry_artifact_id"], f"{path}.properties.derived_geometry_artifact_id")
            if not isinstance(props["error_budget_km"], (int, float)) or props["error_budget_km"] < 0:
                raise SchemaValidationError(f"{path}.properties.error_budget_km must be non-negative")
            geo = props["georeferencing"]
            _require_object(geo, f"{path}.properties.georeferencing")
            _require_keys(geo, ["transform_method", "crs", "control_points", "residual_error_km", "digitizer", "reviewer", "source_feature_reference"], f"{path}.properties.georeferencing")
            for key in ("transform_method", "crs", "digitizer", "reviewer"):
                _nonempty_string(geo[key], f"{path}.properties.georeferencing.{key}")
            reference = geo["source_feature_reference"]
            if isinstance(reference, dict):
                _nonempty_string(reference.get("kind"), f"{path}.properties.georeferencing.source_feature_reference.kind")
                substring = reference.get("substring")
                _require_object(substring, f"{path}.properties.georeferencing.source_feature_reference.substring")
                _require_keys(
                    substring,
                    ["measure_units", "start_measure", "end_measure", "substrate_merge_rule"],
                    f"{path}.properties.georeferencing.source_feature_reference.substring",
                )
                _nonempty_string(
                    substring["measure_units"],
                    f"{path}.properties.georeferencing.source_feature_reference.substring.measure_units",
                )
                _nonempty_string(
                    substring["substrate_merge_rule"],
                    f"{path}.properties.georeferencing.source_feature_reference.substring.substrate_merge_rule",
                )
                start_measure = substring["start_measure"]
                end_measure = substring["end_measure"]
                if (
                    isinstance(start_measure, bool) or not isinstance(start_measure, (int, float))
                    or isinstance(end_measure, bool) or not isinstance(end_measure, (int, float))
                ):
                    raise SchemaValidationError(
                        f"{path}.properties.georeferencing.source_feature_reference.substring "
                        "start_measure and end_measure must be numbers"
                    )
                if start_measure < 0 or end_measure <= start_measure:
                    raise SchemaValidationError(
                        f"{path}.properties.georeferencing.source_feature_reference.substring "
                        "must satisfy 0 <= start_measure < end_measure"
                    )
            else:
                _nonempty_string(reference, f"{path}.properties.georeferencing.source_feature_reference")
            if geo["digitizer"] == geo["reviewer"]:
                raise SchemaValidationError(f"{path}.properties.georeferencing reviewer must differ from digitizer")
            if not isinstance(geo["control_points"], list) or len(geo["control_points"]) < 3:
                raise SchemaValidationError(f"{path}.properties.georeferencing.control_points needs at least three points")
            if not isinstance(geo["residual_error_km"], (int, float)) or geo["residual_error_km"] < 0:
                raise SchemaValidationError(f"{path}.properties.georeferencing.residual_error_km must be non-negative")


def validate_polity_gazetteer(document: dict[str, Any]) -> None:
    schema = load_schema("polity-gazetteer")
    _m24_header(document, "gazetteer", "polity_gazetteer", schema)
    if not isinstance(document.get("polities"), list) or not document["polities"]:
        raise SchemaValidationError("gazetteer.polities must be non-empty")
    allowed = {"sovereignty", "control", "occupation", "vassalage", "dependency", "personal_union", "claim", "disputed"}
    seen: set[str] = set()
    for index, polity in enumerate(document["polities"]):
        path = f"gazetteer.polities[{index}]"
        _require_object(polity, path)
        _require_keys(polity, ["polity_id", "name", "aliases", "valid_from", "valid_to", "capital_location_ids", "relationships", "source_ids"], path)
        polity_id = _nonempty_string(polity["polity_id"], f"{path}.polity_id")
        if polity_id in seen:
            raise SchemaValidationError(f"duplicate polity_id: {polity_id}")
        seen.add(polity_id)
        _nonempty_string(polity["name"], f"{path}.name")
        for key in ("aliases", "capital_location_ids", "source_ids"):
            _string_list(polity[key], f"{path}.{key}")
        for key in ("valid_from", "valid_to"):
            _nullable_string(polity[key], f"{path}.{key}")
        if not isinstance(polity["relationships"], list):
            raise SchemaValidationError(f"{path}.relationships must be an array")
        for ri, relation in enumerate(polity["relationships"]):
            rpath = f"{path}.relationships[{ri}]"
            _require_object(relation, rpath)
            _require_keys(relation, ["relationship_id", "type", "target_polity_id", "valid_from", "valid_to", "source_ids", "confidence", "notes"], rpath)
            if relation["type"] not in allowed:
                raise SchemaValidationError(f"{rpath}.type is unsupported")
            for key in ("relationship_id", "target_polity_id", "confidence", "notes"):
                _nonempty_string(relation[key], f"{rpath}.{key}")
            _string_list(relation["source_ids"], f"{rpath}.source_ids", nonempty=True)


def validate_location_assignments(document: dict[str, Any]) -> None:
    schema = load_schema("start-date-location-assignments")
    _m24_header(document, "assignments", "start_date_location_assignments", schema)
    _require_keys(document, ["fabric_revision", "aggregation_revision", "aggregation_profile", "geometry_revision", "expected_province_count", "fabric_sidecars", "assignments", "targeted_split_requests"], "assignments")
    for key in ("fabric_revision", "aggregation_revision", "aggregation_profile", "geometry_revision"):
        _nonempty_string(document[key], f"assignments.{key}")
    if not isinstance(document["expected_province_count"], int) or document["expected_province_count"] < 1:
        raise SchemaValidationError("assignments.expected_province_count must be a positive integer")
    sidecars = document["fabric_sidecars"]
    _require_object(sidecars, "assignments.fabric_sidecars")
    _require_keys(sidecars, ["fabric_manifest", "locations", "lineage", "province_membership"], "assignments.fabric_sidecars")
    for role, record in sidecars.items():
        _require_object(record, f"assignments.fabric_sidecars.{role}")
        _require_keys(record, ["path", "sha256"], f"assignments.fabric_sidecars.{role}")
        _nonempty_string(record["path"], f"assignments.fabric_sidecars.{role}.path")
        if not isinstance(record["sha256"], str) or not re.fullmatch(r"[0-9a-fA-F]{64}", record["sha256"]):
            raise SchemaValidationError(f"assignments.fabric_sidecars.{role}.sha256 must be a SHA-256 digest")
    if document["schema_version"] == "0.2.0":
        _require_keys(document, ["constraint_sha256", "release_sidecars"], "assignments")
        if not isinstance(document["constraint_sha256"], str) or not re.fullmatch(r"[0-9a-fA-F]{64}", document["constraint_sha256"]):
            raise SchemaValidationError("assignments.constraint_sha256 must be a SHA-256 digest")
        release_sidecars = document["release_sidecars"]
        _require_object(release_sidecars, "assignments.release_sidecars")
        _require_keys(release_sidecars, ["aggregation_manifest", "adjacency"], "assignments.release_sidecars")
        for role, record in release_sidecars.items():
            _require_object(record, f"assignments.release_sidecars.{role}")
            _require_keys(record, ["path", "sha256"], f"assignments.release_sidecars.{role}")
            _nonempty_string(record["path"], f"assignments.release_sidecars.{role}.path")
            if not isinstance(record["sha256"], str) or not re.fullmatch(r"[0-9a-fA-F]{64}", record["sha256"]):
                raise SchemaValidationError(f"assignments.release_sidecars.{role}.sha256 must be a SHA-256 digest")
    if not isinstance(document["assignments"], list):
        raise SchemaValidationError("assignments.assignments must be an array")
    seen_locations: set[str] = set()
    seen_assignments: set[str] = set()
    for index, row in enumerate(document["assignments"]):
        path = f"assignments.assignments[{index}]"
        _require_object(row, path)
        _require_keys(row, ["assignment_id", "location_ids", "province_id", "polity_ids", "uncertainty", "source_ids", "notes"], path)
        assignment_id = _nonempty_string(row["assignment_id"], f"{path}.assignment_id")
        if assignment_id in seen_assignments:
            raise SchemaValidationError(f"duplicate assignment_id: {assignment_id}")
        seen_assignments.add(assignment_id)
        locations = _string_list(row["location_ids"], f"{path}.location_ids", nonempty=True)
        duplicates = seen_locations.intersection(locations)
        if duplicates:
            raise SchemaValidationError(f"locations assigned more than once: {sorted(duplicates)}")
        seen_locations.update(locations)
        _nonempty_string(row["province_id"], f"{path}.province_id")
        _string_list(row["polity_ids"], f"{path}.polity_ids", nonempty=True)
        _string_list(row["source_ids"], f"{path}.source_ids", nonempty=True)
        if not isinstance(row["uncertainty"], (int, float)) or not 0 <= row["uncertainty"] <= 1:
            raise SchemaValidationError(f"{path}.uncertainty must be between 0 and 1")
        if document["schema_version"] == "0.2.0":
            _require_keys(row, ["region_id", "sovereign_polity_id", "owner_polity_id", "controller_polity_id", "core_polity_ids", "claim_polity_ids", "dispute_polity_ids", "hierarchy"], path)
            for key in ("region_id", "sovereign_polity_id", "owner_polity_id", "controller_polity_id"):
                _nonempty_string(row[key], f"{path}.{key}")
            for key in ("core_polity_ids", "claim_polity_ids", "dispute_polity_ids"):
                _string_list(row[key], f"{path}.{key}")
            hierarchy = row["hierarchy"]
            _require_object(hierarchy, f"{path}.hierarchy")
            _require_keys(hierarchy, ["area_id", "region_id", "superregion_id", "method"], f"{path}.hierarchy")
            for key in ("area_id", "region_id", "superregion_id", "method"):
                _nonempty_string(hierarchy[key], f"{path}.hierarchy.{key}")
    if not isinstance(document["targeted_split_requests"], list):
        raise SchemaValidationError("assignments.targeted_split_requests must be an array")
    seen_requests: set[str] = set()
    for index, request in enumerate(document["targeted_split_requests"]):
        path = f"assignments.targeted_split_requests[{index}]"
        _require_object(request, path)
        _require_keys(request, ["request_id", "location_ids", "reason", "status", "source_ids"], path)
        request_id = _nonempty_string(request["request_id"], f"{path}.request_id")
        if request_id in seen_requests:
            raise SchemaValidationError(f"duplicate split request_id: {request_id}")
        seen_requests.add(request_id)
        _nonempty_string(request["reason"], f"{path}.reason")
        for key in ("location_ids", "source_ids"):
            _string_list(request[key], f"{path}.{key}", nonempty=True)
        if request["status"] not in {"requested", "accepted", "rejected", "superseded"}:
            raise SchemaValidationError(f"{path}.status is unsupported")


def validate_spatial_golden_borders(document: dict[str, Any]) -> None:
    schema = load_schema("spatial-golden-borders")
    _m24_header(document, "golden suite", "spatial_golden_borders", schema)
    if not isinstance(document.get("assertions"), list) or not document["assertions"]:
        raise SchemaValidationError("golden suite.assertions must be non-empty")
    seen: set[str] = set()
    for index, assertion in enumerate(document["assertions"]):
        path = f"golden suite.assertions[{index}]"
        _require_object(assertion, path)
        _require_keys(assertion, ["assertion_id", "region_id", "layer", "assertion_type", "expectation", "subject_ids", "boundary_feature_ids", "spatial_relation", "unit", "tolerance", "notes"], path)
        for key in ("assertion_id", "region_id", "layer", "spatial_relation", "unit", "notes"):
            _nonempty_string(assertion[key], f"{path}.{key}")
        if assertion["assertion_id"] in seen:
            raise SchemaValidationError(f"duplicate assertion_id: {assertion['assertion_id']}")
        seen.add(assertion["assertion_id"])
        if assertion["assertion_type"] not in {"border", "capital", "outline"}:
            raise SchemaValidationError(f"{path}.assertion_type is unsupported")
        if assertion["expectation"] not in {"positive", "negative_anachronism"}:
            raise SchemaValidationError(f"{path}.expectation is unsupported")
        _string_list(assertion["subject_ids"], f"{path}.subject_ids", nonempty=True)
        _string_list(assertion["boundary_feature_ids"], f"{path}.boundary_feature_ids")
        if not isinstance(assertion["tolerance"], (int, float)) or assertion["tolerance"] < 0:
            raise SchemaValidationError(f"{path}.tolerance must be non-negative")
        relation = assertion["spatial_relation"]
        expected = {
            "border_matches_boundary_hausdorff_lte": ("border", "positive", 2, 1, "coordinate_units"),
            "border_matches_boundary_hausdorff_km_lte": ("border", "positive", 2, 1, "kilometres"),
            "capital_within_subject": ("capital", "positive", 2, 0, "boolean"),
            "forbidden_outline_overlap_ratio_lte": ("outline", "negative_anachronism", 1, 1, "ratio"),
        }
        if relation not in expected:
            raise SchemaValidationError(f"{path}.spatial_relation is unsupported")
        kind, expectation, subjects, boundaries, unit = expected[relation]
        if (assertion["assertion_type"], assertion["expectation"], len(assertion["subject_ids"]), len(assertion["boundary_feature_ids"]), assertion["unit"]) != (kind, expectation, subjects, boundaries, unit):
            raise SchemaValidationError(f"{path} does not match the {relation} contract")
        if relation == "capital_within_subject" and assertion["tolerance"] != 1:
            raise SchemaValidationError(f"{path}.tolerance must be 1 for capital containment")
        if relation == "forbidden_outline_overlap_ratio_lte" and assertion["tolerance"] > 1:
            raise SchemaValidationError(f"{path}.tolerance must be at most 1 for a ratio")


def validate_start_date_coverage(document: dict[str, Any]) -> None:
    schema = load_schema("start-date-coverage")
    _m24_header(document, "coverage matrix", "start_date_coverage", schema)
    _require_keys(document, ["coverage", "exclusions", "known_gaps"], "coverage matrix")
    if not isinstance(document["coverage"], list) or not document["coverage"]:
        raise SchemaValidationError("coverage matrix.coverage must be non-empty")
    seen: set[tuple[str, str]] = set()
    for index, row in enumerate(document["coverage"]):
        path = f"coverage matrix.coverage[{index}]"
        _require_object(row, path)
        _require_keys(row, ["region_id", "layer", "grade", "source_ids", "assertion_ids", "evidence_summary", "exclusions", "known_gaps"], path)
        key = (_nonempty_string(row["region_id"], f"{path}.region_id"), _nonempty_string(row["layer"], f"{path}.layer"))
        if key in seen:
            raise SchemaValidationError(f"duplicate coverage row: {key}")
        seen.add(key)
        if row["grade"] not in {"A", "B", "C", "U"}:
            raise SchemaValidationError(f"{path}.grade is unsupported")
        _nonempty_string(row["evidence_summary"], f"{path}.evidence_summary", allow_empty=row["grade"] == "U")
        for field in ("source_ids", "assertion_ids", "exclusions", "known_gaps"):
            _string_list(row[field], f"{path}.{field}")
    for field in ("exclusions", "known_gaps"):
        _string_list(document[field], f"coverage matrix.{field}")


def validate_start_date_changelog(document: dict[str, Any]) -> None:
    schema = load_schema("start-date-changelog")
    _m24_header(document, "changelog", "start_date_changelog", schema)
    _require_keys(document, ["version", "released_at", "changes", "migrations"], "changelog")
    for field in ("version", "released_at"):
        _nonempty_string(document[field], f"changelog.{field}")
    if not isinstance(document["changes"], list) or not document["changes"]:
        raise SchemaValidationError("changelog.changes must be non-empty")
    for index, change in enumerate(document["changes"]):
        path = f"changelog.changes[{index}]"
        _require_object(change, path)
        _require_keys(change, ["change_id", "category", "summary", "affected_ids"], path)
        if change["category"] not in {"geometry", "politics", "hierarchy", "gazetteer", "research", "qa"}:
            raise SchemaValidationError(f"{path}.category is unsupported")
        for field in ("change_id", "summary"):
            _nonempty_string(change[field], f"{path}.{field}")
        _string_list(change["affected_ids"], f"{path}.affected_ids")
    _string_list(document["migrations"], "changelog.migrations")


def validate_start_date_qa_report(report: dict[str, Any]) -> None:
    schema = load_schema("start-date-qa-report")
    _require_object(report, "report")
    _validate_json_schema(report, schema, "report")
    _require_keys(report, schema["required"], "report")
    if report["schema_version"] not in {"0.1.0", "0.2.0"} or report["report_type"] != "start_date_research_qa" or report["milestone"] not in {"M24", "M25"}:
        raise SchemaValidationError("report has invalid M24 QA identity")
    if report["status"] not in {"pass", "fail"}:
        raise SchemaValidationError("report.status must be pass or fail")
    _require_object(report["inputs"], "report.inputs")
    _require_object(report["summary"], "report.summary")
    _require_keys(report["summary"], ["artifact_count", "error_count", "warning_count"], "report.summary")
    if not isinstance(report["findings"], list) or not isinstance(report["assertion_results"], list):
        raise SchemaValidationError("report.findings must be an array")
    errors = sum(isinstance(item, dict) and item.get("severity") == "error" for item in report["findings"])
    warnings = sum(isinstance(item, dict) and item.get("severity") == "warning" for item in report["findings"])
    if (errors, warnings) != (report["summary"]["error_count"], report["summary"]["warning_count"]):
        raise SchemaValidationError("report summary counts do not match findings")
    if report["status"] != ("fail" if errors else "pass"):
        raise SchemaValidationError("report status does not match findings")


def _m24_header(document: Any, path: str, document_type: str, schema: dict[str, Any]) -> None:
    _require_object(document, path)
    _validate_json_schema(document, schema, path)
    _require_keys(document, schema["required"], path)
    if document["schema_version"] not in {"0.1.0", "0.2.0"} or document["document_type"] != document_type:
        raise SchemaValidationError(f"{path} has invalid M24 document type or schema version")
    _nonempty_string(document["pass_id"], f"{path}.pass_id")
    _nonempty_string(document["artifact_version"], f"{path}.artifact_version")
    start_date = _nonempty_string(document["start_date"], f"{path}.start_date")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", start_date):
        raise SchemaValidationError(f"{path}.start_date must use YYYY-MM-DD")


def _nonempty_string(value: Any, path: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        raise SchemaValidationError(f"{path} must be a {'string' if allow_empty else 'non-empty string'}")
    return value


def _nullable_string(value: Any, path: str) -> None:
    if value is not None and not isinstance(value, str):
        raise SchemaValidationError(f"{path} must be a string or null")


def _string_list(value: Any, path: str, *, nonempty: bool = False) -> list[str]:
    if not isinstance(value, list) or (nonempty and not value) or not all(isinstance(item, str) and item.strip() for item in value):
        qualifier = "non-empty " if nonempty else ""
        raise SchemaValidationError(f"{path} must be a {qualifier}array of non-empty strings")
    return value


def _validate_json_schema(document: Any, schema: dict[str, Any], path: str) -> None:
    """Run the canonical Draft 2020-12 contract before semantic validation."""
    try:
        from jsonschema import Draft202012Validator, FormatChecker
        errors = sorted(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(document), key=lambda error: list(error.absolute_path))
    except ImportError as exc:
        raise SchemaValidationError("jsonschema is required for M24 validation") from exc
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path)
        raise SchemaValidationError(f"{path}{'.' + location if location else ''}: {error.message}")


def _validate_findings_list(findings: Any, summary: dict[str, Any], path: str) -> None:
    if not isinstance(findings, list):
        raise SchemaValidationError(f"{path}.findings must be a list")
    for index, finding in enumerate(findings):
        item_path = f"{path}.findings[{index}]"
        _require_object(finding, item_path)
        _require_keys(finding, ["code", "severity", "affected_ids", "message", "measurements"], item_path)
        if finding["severity"] not in {"error", "warning"}:
            raise SchemaValidationError(f"{item_path}.severity must be error or warning")
        if not isinstance(finding["affected_ids"], list) or not all(
            isinstance(item, str) for item in finding["affected_ids"]
        ):
            raise SchemaValidationError(f"{item_path}.affected_ids must be a string array")
        _require_object(finding["measurements"], f"{item_path}.measurements")
    errors = sum(finding["severity"] == "error" for finding in findings)
    warnings = sum(finding["severity"] == "warning" for finding in findings)
    if summary["error_count"] != errors or summary["warning_count"] != warnings:
        raise SchemaValidationError(f"{path} summary finding counts do not match report.findings")


def _require_object(value: Any, path: str) -> None:
    if not isinstance(value, dict):
        raise SchemaValidationError(f"{path} must be an object")


def _require_keys(value: dict[str, Any], keys: list[str], path: str) -> None:
    missing = [key for key in keys if key not in value]
    if missing:
        joined = ", ".join(missing)
        raise SchemaValidationError(f"{path} missing required key(s): {joined}")


def _validate_artifacts(value: Any, source_path: str) -> None:
    if not isinstance(value, list):
        raise SchemaValidationError(f"{source_path}.artifacts must be a list")
    for index, artifact in enumerate(value):
        path = f"{source_path}.artifacts[{index}]"
        _require_object(artifact, path)
        _require_keys(
            artifact,
            [
                "id",
                "layer_id",
                "status",
                "url",
                "path",
                "access_date",
                "version",
                "original_format",
                "bytes",
                "checksum",
            ],
            path,
        )
        if artifact["status"] not in {"planned", "downloaded", "existing"}:
            raise SchemaValidationError(f"{path}.status has unsupported value '{artifact['status']}'")
        for key in ["id", "layer_id", "url", "path"]:
            if not isinstance(artifact[key], str) or not artifact[key]:
                raise SchemaValidationError(f"{path}.{key} must be a non-empty string")
        for key in ["access_date", "version", "original_format", "checksum"]:
            _require_nullable_string(artifact[key], f"{path}.{key}")
        if artifact["bytes"] is not None and (
            not isinstance(artifact["bytes"], int) or artifact["bytes"] < 0
        ):
            raise SchemaValidationError(f"{path}.bytes must be a non-negative integer or null")


def _require_nullable_string(value: Any, path: str) -> None:
    if value is not None and not isinstance(value, str):
        raise SchemaValidationError(f"{path} must be a string or null")
