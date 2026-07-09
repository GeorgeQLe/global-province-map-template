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
