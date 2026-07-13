"""Load, list, and validate multi-era pack definitions (M16)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from gpm.paths import CONFIG_DIR
from gpm.release.quality import QUALITY_TIERS

MULTI_ERA_DIR = CONFIG_DIR / "multi_era"
ALLOWED_QUALITY_TIERS = frozenset(QUALITY_TIERS)


class MultiEraPackError(ValueError):
    """Raised when a multi-era pack cannot be loaded or validated."""


@dataclass(frozen=True)
class MultiEraPackSummary:
    pack_id: str
    path: str
    display_name: str
    priority_region_id: str
    era_count: int
    eras: tuple[str, ...]
    scenario_ids: tuple[str, ...]
    era_geometry_pack_ids: tuple[str, ...]
    region_matrix_row_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def multi_era_dir(root: Path | None = None) -> Path:
    if root is not None:
        return root / "configs" / "multi_era"
    return MULTI_ERA_DIR


def list_multi_era_packs(root: Path | None = None) -> list[MultiEraPackSummary]:
    """List bundled multi-era pack definitions."""
    directory = multi_era_dir(root)
    if not directory.is_dir():
        return []
    summaries: list[MultiEraPackSummary] = []
    for path in sorted(directory.glob("*.json")):
        if path.name.startswith("."):
            continue
        try:
            document = load_multi_era_pack(path.stem, path=path)
        except MultiEraPackError:
            continue
        summaries.append(_summarize(document, path))
    return summaries


def load_multi_era_pack(
    pack_id: str,
    *,
    path: Path | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    """Load and validate a multi-era pack by id or explicit path."""
    pack_path = path
    if pack_path is None:
        candidate = multi_era_dir(root) / f"{pack_id}.json"
        if not candidate.is_file():
            raise MultiEraPackError(
                f"Multi-era pack not found: {pack_id} ({candidate})"
            )
        pack_path = candidate
    if not pack_path.is_file():
        raise MultiEraPackError(f"Multi-era pack path does not exist: {pack_path}")
    try:
        document = json.loads(pack_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise MultiEraPackError(
            f"Invalid JSON in multi-era pack {pack_path}: {exc}"
        ) from exc
    validate_multi_era_pack(document)
    if path is None and document.get("pack_id") != pack_id:
        raise MultiEraPackError(
            f"Pack id mismatch: requested {pack_id!r}, document has "
            f"{document.get('pack_id')!r}"
        )
    return document


def validate_multi_era_pack(document: dict[str, Any]) -> None:
    """Validate core invariants of an M16 multi-era pack definition."""
    if not isinstance(document, dict):
        raise MultiEraPackError("multi-era pack must be a JSON object")

    required = [
        "schema_version",
        "pack_id",
        "display_name",
        "priority_region",
        "eras",
        "region_quality_matrix",
    ]
    for key in required:
        if key not in document:
            raise MultiEraPackError(f"multi-era pack missing required key: {key}")

    if document["schema_version"] != "0.1.0":
        raise MultiEraPackError(
            f"multi-era pack.schema_version must be 0.1.0 "
            f"(got {document['schema_version']!r})"
        )
    if not isinstance(document["pack_id"], str) or not document["pack_id"].strip():
        raise MultiEraPackError("pack_id must be a non-empty string")
    if not isinstance(document["display_name"], str) or not document["display_name"].strip():
        raise MultiEraPackError("display_name must be a non-empty string")

    region = document["priority_region"]
    if not isinstance(region, dict):
        raise MultiEraPackError("priority_region must be an object")
    for key in ("id", "label"):
        if not isinstance(region.get(key), str) or not region[key].strip():
            raise MultiEraPackError(
                f"priority_region.{key} must be a non-empty string"
            )
    parent_ids = region.get("parent_country_ids")
    if parent_ids is not None:
        if not isinstance(parent_ids, list) or not all(
            isinstance(item, str) and item.strip() for item in parent_ids
        ):
            raise MultiEraPackError(
                "priority_region.parent_country_ids must be a list of non-empty strings"
            )

    eras = document["eras"]
    if not isinstance(eras, list) or len(eras) < 2:
        raise MultiEraPackError(
            "eras must be a list of at least two era slots (multi-era pack)"
        )
    seen_eras: set[str] = set()
    for index, slot in enumerate(eras):
        _validate_era_slot(slot, f"eras[{index}]", seen_eras)

    matrix = document["region_quality_matrix"]
    if not isinstance(matrix, list) or not matrix:
        raise MultiEraPackError("region_quality_matrix must be a non-empty list")
    for index, row in enumerate(matrix):
        _validate_matrix_row(row, f"region_quality_matrix[{index}]", seen_eras)

    migration = document.get("migration_notes")
    if migration is not None:
        if not isinstance(migration, dict):
            raise MultiEraPackError("migration_notes must be an object when present")
        summary = migration.get("summary")
        if summary is not None and (
            not isinstance(summary, str) or not summary.strip()
        ):
            raise MultiEraPackError(
                "migration_notes.summary must be a non-empty string when present"
            )
        for key in ("consumer_guidance", "breaking_changes", "do_not_claim"):
            value = migration.get(key)
            if value is None:
                continue
            if not isinstance(value, list) or not all(
                isinstance(item, str) for item in value
            ):
                raise MultiEraPackError(f"migration_notes.{key} must be a list of strings")

    for key in ("source_notes", "do_not_claim"):
        value = document.get(key)
        if value is None:
            continue
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise MultiEraPackError(f"{key} must be a list of strings")


def _validate_era_slot(slot: Any, path: str, seen_eras: set[str]) -> None:
    if not isinstance(slot, dict):
        raise MultiEraPackError(f"{path} must be an object")
    for key in ("era", "scenario_id", "politics_quality_tier", "geometry_quality_tier"):
        if key not in slot:
            raise MultiEraPackError(f"{path} missing required key: {key}")
    era = slot["era"]
    if not isinstance(era, str) or not era.strip():
        raise MultiEraPackError(f"{path}.era must be a non-empty string")
    if era in seen_eras:
        raise MultiEraPackError(f"{path}.era duplicates {era!r}")
    seen_eras.add(era)

    scenario_id = slot["scenario_id"]
    if not isinstance(scenario_id, str) or not scenario_id.strip():
        raise MultiEraPackError(f"{path}.scenario_id must be a non-empty string")

    for tier_key in ("politics_quality_tier", "geometry_quality_tier"):
        tier = slot[tier_key]
        if tier not in ALLOWED_QUALITY_TIERS:
            raise MultiEraPackError(
                f"{path}.{tier_key} must be one of {sorted(ALLOWED_QUALITY_TIERS)}"
            )

    geom_pack = slot.get("era_geometry_pack_id")
    if geom_pack is not None and (
        not isinstance(geom_pack, str) or not geom_pack.strip()
    ):
        raise MultiEraPackError(
            f"{path}.era_geometry_pack_id must be a non-empty string when present"
        )

    # M20: optional multi-region composition list (applied in order).
    geom_packs = slot.get("era_geometry_pack_ids")
    if geom_packs is not None:
        if not isinstance(geom_packs, list) or not geom_packs:
            raise MultiEraPackError(
                f"{path}.era_geometry_pack_ids must be a non-empty list when present"
            )
        if not all(isinstance(item, str) and item.strip() for item in geom_packs):
            raise MultiEraPackError(
                f"{path}.era_geometry_pack_ids must be a list of non-empty strings"
            )
        if geom_pack is not None and geom_pack not in geom_packs:
            raise MultiEraPackError(
                f"{path}.era_geometry_pack_id must appear in era_geometry_pack_ids "
                "when both are set"
            )

    profile = slot.get("recommended_profile")
    if profile is not None and (not isinstance(profile, str) or not profile.strip()):
        raise MultiEraPackError(
            f"{path}.recommended_profile must be a non-empty string when present"
        )

    notes = slot.get("notes")
    if notes is not None and not isinstance(notes, str):
        raise MultiEraPackError(f"{path}.notes must be a string when present")


def _validate_matrix_row(row: Any, path: str, known_eras: set[str]) -> None:
    if not isinstance(row, dict):
        raise MultiEraPackError(f"{path} must be an object")
    for key in ("region_id", "label", "by_era"):
        if key not in row:
            raise MultiEraPackError(f"{path} missing required key: {key}")
    if not isinstance(row["region_id"], str) or not row["region_id"].strip():
        raise MultiEraPackError(f"{path}.region_id must be a non-empty string")
    if not isinstance(row["label"], str) or not row["label"].strip():
        raise MultiEraPackError(f"{path}.label must be a non-empty string")
    by_era = row["by_era"]
    if not isinstance(by_era, dict) or not by_era:
        raise MultiEraPackError(f"{path}.by_era must be a non-empty object")
    for era, tiers in by_era.items():
        if era not in known_eras:
            raise MultiEraPackError(
                f"{path}.by_era has era {era!r} not listed in pack eras"
            )
        if not isinstance(tiers, dict):
            raise MultiEraPackError(f"{path}.by_era[{era!r}] must be an object")
        for tier_key in ("geometry", "politics"):
            if tier_key not in tiers:
                raise MultiEraPackError(
                    f"{path}.by_era[{era!r}] missing required key: {tier_key}"
                )
            if tiers[tier_key] not in ALLOWED_QUALITY_TIERS:
                raise MultiEraPackError(
                    f"{path}.by_era[{era!r}].{tier_key} must be one of "
                    f"{sorted(ALLOWED_QUALITY_TIERS)}"
                )


def resolve_era_geometry_pack_ids(slot: dict[str, Any]) -> list[str]:
    """Return ordered era-geometry pack ids for a multi-era era slot (M20)."""
    multi = slot.get("era_geometry_pack_ids")
    if isinstance(multi, list) and multi:
        return [str(item).strip() for item in multi if str(item).strip()]
    single = slot.get("era_geometry_pack_id")
    if isinstance(single, str) and single.strip():
        return [single.strip()]
    return []


def _summarize(document: dict[str, Any], path: Path) -> MultiEraPackSummary:
    eras = document.get("eras") or []
    era_ids = tuple(str(slot.get("era") or "") for slot in eras)
    scenario_ids = tuple(str(slot.get("scenario_id") or "") for slot in eras)
    geom_ids: list[str] = []
    for slot in eras:
        for pack_id in resolve_era_geometry_pack_ids(slot):
            if pack_id not in geom_ids:
                geom_ids.append(pack_id)
    region = document.get("priority_region") or {}
    return MultiEraPackSummary(
        pack_id=str(document["pack_id"]),
        path=str(path),
        display_name=str(document["display_name"]),
        priority_region_id=str(region.get("id") or ""),
        era_count=len(eras),
        eras=era_ids,
        scenario_ids=scenario_ids,
        era_geometry_pack_ids=tuple(geom_ids),
        region_matrix_row_count=len(document.get("region_quality_matrix") or []),
    )
