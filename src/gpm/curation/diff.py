"""Ownership diff tools for curation review (M17).

Compare two resolved ownership tables (from scenarios or ownership files) and
emit tag counts, province-level changes, and contested-province summaries.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from gpm.paths import PROCESSED_DATA_DIR
from gpm.scenarios import ScenarioError, load_scenario, resolve_ownership_records
from gpm.schemas import SchemaValidationError, validate_scenario_diff_report

DIFF_SCHEMA_VERSION = "0.1.0"


class OwnershipDiffError(RuntimeError):
    """Raised when an ownership diff cannot be computed."""


@dataclass(frozen=True)
class OwnershipDiffResult:
    status: str
    report_output: str | None
    base_label: str
    target_label: str
    owner_change_count: int
    controller_change_count: int
    disputed_change_count: int
    added_province_count: int
    removed_province_count: int
    contested_province_count: int
    report: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["report"] = self.report
        return payload


def load_ownership_side(
    *,
    scenario_id: str | None = None,
    scenario_path: Path | None = None,
    ownership_input: Path | None = None,
    province_input: Path = PROCESSED_DATA_DIR / "provinces.geojson",
    allow_unknown_overrides: bool = False,
    label: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Load ownership records from a scenario resolve or an ownership file.

    Returns ``(records, meta)`` where meta includes label/scenario_id/source.
    """
    if ownership_input is not None:
        path = Path(ownership_input)
        records = _load_ownership_file(path)
        scenario_from_rows = next(
            (str(row["scenario_id"]) for row in records if row.get("scenario_id")),
            None,
        )
        meta = {
            "label": label or path.name,
            "scenario_id": scenario_from_rows or scenario_id,
            "source": str(path),
        }
        return records, meta

    if scenario_id is None and scenario_path is None:
        raise OwnershipDiffError(
            "Provide --scenario / --scenario-path or --ownership for each diff side."
        )

    sid = scenario_id or "from-path"
    try:
        scenario = load_scenario(sid, scenario_path=scenario_path)
    except ScenarioError as exc:
        raise OwnershipDiffError(str(exc)) from exc
    land_features = _load_land_features(Path(province_input))
    try:
        records, _stats = resolve_ownership_records(
            scenario,
            land_features,
            allow_unknown_overrides=allow_unknown_overrides,
        )
    except ScenarioError as exc:
        raise OwnershipDiffError(str(exc)) from exc
    meta = {
        "label": label or str(scenario.get("scenario_id")),
        "scenario_id": str(scenario.get("scenario_id")),
        "source": str(scenario.get("_path") or scenario_path or scenario_id),
    }
    return records, meta


def diff_ownership(
    base_records: list[dict[str, Any]],
    target_records: list[dict[str, Any]],
    *,
    base_meta: dict[str, Any] | None = None,
    target_meta: dict[str, Any] | None = None,
    report_output: Path | None = None,
    max_changes: int | None = None,
) -> OwnershipDiffResult:
    """Diff two ownership tables and optionally write a JSON report."""
    base_meta = base_meta or {"label": "base", "scenario_id": None, "source": "base"}
    target_meta = target_meta or {"label": "target", "scenario_id": None, "source": "target"}

    base_by_id = _index_by_province(base_records)
    target_by_id = _index_by_province(target_records)

    base_ids = set(base_by_id)
    target_ids = set(target_by_id)
    shared = base_ids & target_ids
    added = sorted(target_ids - base_ids)
    removed = sorted(base_ids - target_ids)

    changes: list[dict[str, Any]] = []
    owner_change_count = 0
    controller_change_count = 0
    disputed_change_count = 0
    contested_provinces: list[str] = []

    for province_id in sorted(shared):
        left = base_by_id[province_id]
        right = target_by_id[province_id]
        field_changes: dict[str, dict[str, Any]] = {}
        for field in ("owner", "controller", "culture", "religion", "assignment_source"):
            lv = _norm_str(left.get(field))
            rv = _norm_str(right.get(field))
            if lv != rv:
                field_changes[field] = {"base": lv, "target": rv}
        left_disputed = bool(left.get("disputed"))
        right_disputed = bool(right.get("disputed"))
        if left_disputed != right_disputed:
            field_changes["disputed"] = {"base": left_disputed, "target": right_disputed}
        left_cores = _norm_tag_list(left.get("cores"))
        right_cores = _norm_tag_list(right.get("cores"))
        if left_cores != right_cores:
            field_changes["cores"] = {"base": left_cores, "target": right_cores}
        left_claims = _norm_tag_list(left.get("claims"))
        right_claims = _norm_tag_list(right.get("claims"))
        if left_claims != right_claims:
            field_changes["claims"] = {"base": left_claims, "target": right_claims}

        if not field_changes:
            continue
        if "owner" in field_changes:
            owner_change_count += 1
        if "controller" in field_changes:
            controller_change_count += 1
        if "disputed" in field_changes:
            disputed_change_count += 1
        if right_disputed or left_disputed or "claims" in field_changes:
            contested_provinces.append(province_id)

        changes.append(
            {
                "province_id": province_id,
                "change_type": "modified",
                "fields": field_changes,
                "base_owner": _norm_str(left.get("owner")),
                "target_owner": _norm_str(right.get("owner")),
                "display_name": _norm_str(right.get("display_name"))
                or _norm_str(left.get("display_name")),
            }
        )

    for province_id in added:
        row = target_by_id[province_id]
        if bool(row.get("disputed")):
            contested_provinces.append(province_id)
        changes.append(
            {
                "province_id": province_id,
                "change_type": "added",
                "fields": {},
                "base_owner": None,
                "target_owner": _norm_str(row.get("owner")),
                "display_name": _norm_str(row.get("display_name")),
            }
        )
    for province_id in removed:
        row = base_by_id[province_id]
        changes.append(
            {
                "province_id": province_id,
                "change_type": "removed",
                "fields": {},
                "base_owner": _norm_str(row.get("owner")),
                "target_owner": None,
                "display_name": _norm_str(row.get("display_name")),
            }
        )

    base_counts = Counter(
        tag for row in base_records if (tag := _norm_str(row.get("owner"))) is not None
    )
    target_counts = Counter(
        tag for row in target_records if (tag := _norm_str(row.get("owner"))) is not None
    )
    all_tags = sorted(set(base_counts) | set(target_counts))
    owner_count_delta = {
        tag: {
            "base": int(base_counts.get(tag, 0)),
            "target": int(target_counts.get(tag, 0)),
            "delta": int(target_counts.get(tag, 0) - base_counts.get(tag, 0)),
        }
        for tag in all_tags
        if base_counts.get(tag, 0) != target_counts.get(tag, 0)
    }

    # Stable order: modified first by province_id, then added, then removed.
    change_rank = {"modified": 0, "added": 1, "removed": 2}
    changes.sort(key=lambda item: (change_rank.get(item["change_type"], 9), item["province_id"]))
    truncated = False
    if max_changes is not None and max_changes >= 0 and len(changes) > max_changes:
        changes = changes[:max_changes]
        truncated = True

    status = (
        "identical"
        if owner_change_count == 0
        and controller_change_count == 0
        and disputed_change_count == 0
        and not added
        and not removed
        and not owner_count_delta
        else "changed"
    )

    report: dict[str, Any] = {
        "schema_version": DIFF_SCHEMA_VERSION,
        "report_type": "scenario_ownership_diff",
        "milestone": "M17",
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "status": status,
        "base": {
            "label": base_meta.get("label"),
            "scenario_id": base_meta.get("scenario_id"),
            "source": base_meta.get("source"),
        },
        "target": {
            "label": target_meta.get("label"),
            "scenario_id": target_meta.get("scenario_id"),
            "source": target_meta.get("source"),
        },
        "summary": {
            "base_row_count": len(base_records),
            "target_row_count": len(target_records),
            "shared_province_count": len(shared),
            "owner_change_count": owner_change_count,
            "controller_change_count": controller_change_count,
            "disputed_change_count": disputed_change_count,
            "added_province_count": len(added),
            "removed_province_count": len(removed),
            "contested_province_count": len(sorted(set(contested_provinces))),
            "change_list_truncated": truncated,
            "change_list_count": len(changes),
        },
        "owner_count_delta": owner_count_delta,
        "contested_provinces": sorted(set(contested_provinces)),
        "changes": changes,
    }

    try:
        validate_scenario_diff_report(report)
    except SchemaValidationError as exc:
        raise OwnershipDiffError(f"Diff report failed schema validation: {exc}") from exc

    out_str: str | None = None
    if report_output is not None:
        out_path = Path(report_output)
        try:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(
                json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        except OSError as exc:
            raise OwnershipDiffError(f"Cannot write diff report {out_path}: {exc}") from exc
        out_str = str(out_path)

    return OwnershipDiffResult(
        status=status,
        report_output=out_str,
        base_label=str(base_meta.get("label")),
        target_label=str(target_meta.get("label")),
        owner_change_count=owner_change_count,
        controller_change_count=controller_change_count,
        disputed_change_count=disputed_change_count,
        added_province_count=len(added),
        removed_province_count=len(removed),
        contested_province_count=len(set(contested_provinces)),
        report=report,
    )


def _index_by_province(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in records:
        province_id = row.get("province_id")
        if not isinstance(province_id, str) or not province_id.strip():
            continue
        indexed[province_id.strip()] = row
    return indexed


def _norm_str(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        text = str(value).strip()
        return text or None
    text = value.strip()
    return text or None


def _norm_tag_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return sorted(part.strip() for part in text.split(",") if part.strip())
        if isinstance(parsed, list):
            return sorted(str(item).strip() for item in parsed if str(item).strip())
        return [str(parsed).strip()] if str(parsed).strip() else []
    if isinstance(value, list):
        return sorted(str(item).strip() for item in value if str(item).strip())
    return [str(value).strip()] if str(value).strip() else []


def _load_land_features(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise OwnershipDiffError(f"Province input does not exist: {path}")
    try:
        collection = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OwnershipDiffError(f"Unable to read province input {path}: {exc}") from exc
    if not isinstance(collection, dict) or collection.get("type") != "FeatureCollection":
        raise OwnershipDiffError(f"Province input must be a FeatureCollection: {path}")
    features = collection.get("features")
    if not isinstance(features, list):
        raise OwnershipDiffError(f"Province input features must be an array: {path}")
    land: list[dict[str, Any]] = []
    for feature in features:
        if not isinstance(feature, dict):
            continue
        props = feature.get("properties")
        if not isinstance(props, dict):
            continue
        kind = props.get("kind", "land")
        if kind not in (None, "land"):
            continue
        land.append(feature)
    if not land:
        raise OwnershipDiffError(f"Province input has no land features: {path}")
    return land


def _load_ownership_file(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise OwnershipDiffError(f"Ownership input does not exist: {path}")
    try:
        if path.suffix.lower() == ".csv":
            return _load_ownership_csv(path)
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise OwnershipDiffError(f"Ownership JSON is invalid: {path}: {exc}") from exc
    except OSError as exc:
        raise OwnershipDiffError(f"Unable to read ownership input {path}: {exc}") from exc
    if isinstance(payload, dict) and isinstance(payload.get("records"), list):
        return [dict(row) for row in payload["records"] if isinstance(row, dict)]
    if isinstance(payload, list):
        return [dict(row) for row in payload if isinstance(row, dict)]
    raise OwnershipDiffError(
        f"Ownership JSON must be a record list or object with records: {path}"
    )


def _load_ownership_csv(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            disputed_raw = (row.get("disputed") or "").strip().lower()
            records.append(
                {
                    "province_id": (row.get("province_id") or "").strip(),
                    "scenario_id": (row.get("scenario_id") or "").strip() or None,
                    "owner": (row.get("owner") or "").strip() or None,
                    "controller": (row.get("controller") or "").strip() or None,
                    "cores": _norm_tag_list(row.get("cores")),
                    "claims": _norm_tag_list(row.get("claims")),
                    "culture": (row.get("culture") or "").strip() or None,
                    "religion": (row.get("religion") or "").strip() or None,
                    "disputed": disputed_raw in {"1", "true", "yes"},
                    "assignment_source": (row.get("assignment_source") or "").strip() or None,
                    "display_name": (row.get("display_name") or "").strip() or None,
                }
            )
    return records
