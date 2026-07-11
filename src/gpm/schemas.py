from __future__ import annotations

import json
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
