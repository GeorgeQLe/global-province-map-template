"""M11 curator authoring helpers for scenario province overrides."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from gpm.scenarios.resolve import ScenarioError, load_scenario, validate_scenario_document

EDITABLE_FIELDS = (
    "owner",
    "controller",
    "cores",
    "claims",
    "culture",
    "religion",
    "disputed",
    "notes",
)


@dataclass(frozen=True)
class ScenarioOverrideWriteResult:
    scenario_id: str
    scenario_path: str
    province_id: str
    action: str
    province_override_count: int
    override: dict[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def apply_province_override(
    scenario_id: str,
    province_id: str,
    fields: dict[str, Any],
    *,
    scenario_path: Path | None = None,
    scenario_dir: Path | None = None,
    write: bool = True,
) -> ScenarioOverrideWriteResult:
    """Upsert a province_override into a scenario definition and optionally write it back."""
    province_id = province_id.strip()
    if not province_id:
        raise ScenarioError("province_id must be a non-empty string")

    scenario = load_scenario(scenario_id, scenario_dir=scenario_dir, scenario_path=scenario_path)
    path = Path(scenario["_path"])
    document = _document_for_write(scenario)
    overrides = list(document.get("province_overrides") or [])
    cleaned = _clean_override_fields(fields)

    existing_index = next(
        (
            index
            for index, item in enumerate(overrides)
            if isinstance(item, dict) and str(item.get("province_id") or "").strip() == province_id
        ),
        None,
    )

    if not cleaned:
        if existing_index is None:
            action = "noop"
            override: dict[str, Any] | None = None
        else:
            overrides.pop(existing_index)
            action = "removed"
            override = None
    else:
        override = {"province_id": province_id, **cleaned}
        if existing_index is None:
            overrides.append(override)
            action = "created"
        else:
            # Merge with prior override so partial form posts do not wipe fields.
            merged = dict(overrides[existing_index])
            merged.update(override)
            override = merged
            overrides[existing_index] = override
            action = "updated"

    overrides.sort(key=lambda item: str(item.get("province_id") or ""))
    document["province_overrides"] = overrides
    validate_scenario_document(document, path=path)

    if write:
        _write_scenario_json(path, document)

    return ScenarioOverrideWriteResult(
        scenario_id=str(document["scenario_id"]),
        scenario_path=str(path),
        province_id=province_id,
        action=action,
        province_override_count=len(overrides),
        override=override,
    )


def remove_province_override(
    scenario_id: str,
    province_id: str,
    *,
    scenario_path: Path | None = None,
    scenario_dir: Path | None = None,
    write: bool = True,
) -> ScenarioOverrideWriteResult:
    """Remove a province_override entry if present."""
    return apply_province_override(
        scenario_id,
        province_id,
        {},
        scenario_path=scenario_path,
        scenario_dir=scenario_dir,
        write=write,
    )


def list_province_overrides(
    scenario_id: str,
    *,
    scenario_path: Path | None = None,
    scenario_dir: Path | None = None,
) -> list[dict[str, Any]]:
    scenario = load_scenario(scenario_id, scenario_dir=scenario_dir, scenario_path=scenario_path)
    overrides = scenario.get("province_overrides") or []
    return [dict(item) for item in overrides if isinstance(item, dict)]


def _document_for_write(scenario: dict[str, Any]) -> dict[str, Any]:
    document = deepcopy(scenario)
    document.pop("_path", None)
    return document


def _clean_override_fields(fields: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(fields, dict):
        raise ScenarioError("Override fields must be an object")
    cleaned: dict[str, Any] = {}
    for key in EDITABLE_FIELDS:
        if key not in fields:
            continue
        value = fields[key]
        if key in {"cores", "claims"}:
            cleaned[key] = _as_string_list(value, key)
        elif key == "disputed":
            cleaned[key] = _as_bool(value)
        elif key in {"owner", "controller", "culture", "religion", "notes"}:
            if value is None or value == "":
                # Explicit null/empty means "leave field unset" for partial forms when
                # merging; for create we simply omit.
                continue
            if not isinstance(value, str):
                raise ScenarioError(f"Override field {key!r} must be a string or null")
            text = value.strip()
            if text:
                cleaned[key] = text
        else:
            cleaned[key] = value

    # Empty owner after explicit request is invalid if provided as whitespace-only.
    if "owner" in fields and fields["owner"] is not None and "owner" not in cleaned:
        if isinstance(fields["owner"], str) and fields["owner"].strip() == "":
            raise ScenarioError("owner must be a non-empty string when provided")
    return cleaned


def _as_string_list(value: Any, key: str) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        if text.startswith("["):
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError as exc:
                raise ScenarioError(f"{key} must be a JSON array or comma-separated list") from exc
            if not isinstance(parsed, list):
                raise ScenarioError(f"{key} must be a list")
            return [str(item).strip() for item in parsed if str(item).strip()]
        return [part.strip() for part in text.split(",") if part.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    raise ScenarioError(f"{key} must be a list or string")


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _write_scenario_json(path: Path, document: dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(document, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        raise ScenarioError(f"Unable to write scenario file {path}: {exc}") from exc
