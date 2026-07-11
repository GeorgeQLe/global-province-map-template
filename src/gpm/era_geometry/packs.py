"""Load, list, and validate era-geometry pack definitions (M15)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from gpm.paths import CONFIG_DIR

ERA_GEOMETRY_DIR = CONFIG_DIR / "era_geometry"
ALLOWED_MODES = frozenset({"boundary_hints", "hard_overrides"})
ALLOWED_OPERATIONS = frozenset({"replace", "split", "identity"})
ALLOWED_LINEAGE_OPS = frozenset(
    {"identity", "replace", "split_child", "merge_parent", "reshape"}
)
ALLOWED_QUALITY_TIERS = frozenset(
    {"scaffold-baseline", "curated-politics", "period-geometry"}
)


class EraGeometryPackError(ValueError):
    """Raised when an era-geometry pack cannot be loaded or validated."""


@dataclass(frozen=True)
class EraGeometryPackSummary:
    pack_id: str
    path: str
    era: str
    scenario_id: str | None
    quality_tier: str
    priority_region_id: str
    geometry_modes: tuple[str, ...]
    boundary_hint_count: int
    hard_override_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def era_geometry_dir(root: Path | None = None) -> Path:
    if root is not None:
        return root / "configs" / "era_geometry"
    return ERA_GEOMETRY_DIR


def list_era_geometry_packs(root: Path | None = None) -> list[EraGeometryPackSummary]:
    """List bundled era-geometry pack definitions."""
    directory = era_geometry_dir(root)
    if not directory.is_dir():
        return []
    summaries: list[EraGeometryPackSummary] = []
    for path in sorted(directory.glob("*.json")):
        if path.name.startswith("."):
            continue
        try:
            document = load_era_geometry_pack(path.stem, path=path)
        except EraGeometryPackError:
            continue
        summaries.append(_summarize(document, path))
    return summaries


def load_era_geometry_pack(
    pack_id: str,
    *,
    path: Path | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    """Load and validate an era-geometry pack by id or explicit path."""
    pack_path = path
    if pack_path is None:
        candidate = era_geometry_dir(root) / f"{pack_id}.json"
        if not candidate.is_file():
            raise EraGeometryPackError(
                f"Era-geometry pack not found: {pack_id} ({candidate})"
            )
        pack_path = candidate
    if not pack_path.is_file():
        raise EraGeometryPackError(f"Era-geometry pack path does not exist: {pack_path}")
    try:
        document = json.loads(pack_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise EraGeometryPackError(
            f"Invalid JSON in era-geometry pack {pack_path}: {exc}"
        ) from exc
    validate_era_geometry_pack(document)
    if path is None and document.get("pack_id") != pack_id:
        raise EraGeometryPackError(
            f"Pack id mismatch: requested {pack_id!r}, document has "
            f"{document.get('pack_id')!r}"
        )
    return document


def validate_era_geometry_pack(document: dict[str, Any]) -> None:
    """Validate core invariants of an M15 era-geometry pack definition."""
    if not isinstance(document, dict):
        raise EraGeometryPackError("era-geometry pack must be a JSON object")

    required = [
        "schema_version",
        "pack_id",
        "era",
        "display_name",
        "quality_tier",
        "priority_region",
        "geometry_modes",
    ]
    for key in required:
        if key not in document:
            raise EraGeometryPackError(f"era-geometry pack missing required key: {key}")

    if document["schema_version"] != "0.1.0":
        raise EraGeometryPackError(
            f"era-geometry pack.schema_version must be 0.1.0 "
            f"(got {document['schema_version']!r})"
        )
    if not isinstance(document["pack_id"], str) or not document["pack_id"].strip():
        raise EraGeometryPackError("pack_id must be a non-empty string")
    if not isinstance(document["era"], str) or not document["era"].strip():
        raise EraGeometryPackError("era must be a non-empty string")
    if not isinstance(document["display_name"], str) or not document["display_name"].strip():
        raise EraGeometryPackError("display_name must be a non-empty string")
    if document["quality_tier"] not in ALLOWED_QUALITY_TIERS:
        raise EraGeometryPackError(
            f"quality_tier must be one of {sorted(ALLOWED_QUALITY_TIERS)}"
        )

    region = document["priority_region"]
    if not isinstance(region, dict):
        raise EraGeometryPackError("priority_region must be an object")
    for key in ("id", "label"):
        if not isinstance(region.get(key), str) or not region[key].strip():
            raise EraGeometryPackError(f"priority_region.{key} must be a non-empty string")
    parent_ids = region.get("parent_country_ids")
    if parent_ids is not None:
        if not isinstance(parent_ids, list) or not all(
            isinstance(item, str) and item.strip() for item in parent_ids
        ):
            raise EraGeometryPackError(
                "priority_region.parent_country_ids must be a list of non-empty strings"
            )
    bbox = region.get("bbox")
    if bbox is not None:
        if (
            not isinstance(bbox, list)
            or len(bbox) != 4
            or not all(isinstance(v, (int, float)) for v in bbox)
        ):
            raise EraGeometryPackError(
                "priority_region.bbox must be [min_lon, min_lat, max_lon, max_lat]"
            )

    modes = document["geometry_modes"]
    if not isinstance(modes, list) or not modes:
        raise EraGeometryPackError("geometry_modes must be a non-empty list")
    for mode in modes:
        if mode not in ALLOWED_MODES:
            raise EraGeometryPackError(
                f"geometry_modes entry {mode!r} not in {sorted(ALLOWED_MODES)}"
            )

    scenario_id = document.get("scenario_id")
    if scenario_id is not None and (
        not isinstance(scenario_id, str) or not scenario_id.strip()
    ):
        raise EraGeometryPackError("scenario_id must be a non-empty string when present")

    hints = document.get("boundary_hints", [])
    if hints is None:
        hints = []
    if not isinstance(hints, list):
        raise EraGeometryPackError("boundary_hints must be a list")
    for index, hint in enumerate(hints):
        _validate_boundary_hint(hint, f"boundary_hints[{index}]")

    overrides = document.get("hard_overrides", [])
    if overrides is None:
        overrides = []
    if not isinstance(overrides, list):
        raise EraGeometryPackError("hard_overrides must be a list")
    for index, override in enumerate(overrides):
        _validate_hard_override(override, f"hard_overrides[{index}]")

    lineage = document.get("lineage", [])
    if lineage is None:
        lineage = []
    if not isinstance(lineage, list):
        raise EraGeometryPackError("lineage must be a list")
    for index, row in enumerate(lineage):
        _validate_lineage_row(row, f"lineage[{index}]")

    for key in ("source_notes", "do_not_claim", "period_true_scope", "scaffold_backed_scope"):
        value = document.get(key)
        if value is None:
            continue
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise EraGeometryPackError(f"{key} must be a list of strings")

    # Soft or hard content required so the pack is not an empty claim.
    if "boundary_hints" in modes and not hints:
        raise EraGeometryPackError(
            "geometry_modes includes boundary_hints but boundary_hints is empty"
        )
    if "hard_overrides" in modes and not overrides:
        raise EraGeometryPackError(
            "geometry_modes includes hard_overrides but hard_overrides is empty"
        )


def _validate_boundary_hint(hint: dict[str, Any], path: str) -> None:
    if not isinstance(hint, dict):
        raise EraGeometryPackError(f"{path} must be an object")
    for key in ("hint_id", "label", "geometry"):
        if key not in hint:
            raise EraGeometryPackError(f"{path} missing required key: {key}")
    if not isinstance(hint["hint_id"], str) or not hint["hint_id"].strip():
        raise EraGeometryPackError(f"{path}.hint_id must be a non-empty string")
    if not isinstance(hint["label"], str) or not hint["label"].strip():
        raise EraGeometryPackError(f"{path}.label must be a non-empty string")
    geometry = hint["geometry"]
    if not isinstance(geometry, dict) or "type" not in geometry:
        raise EraGeometryPackError(f"{path}.geometry must be a GeoJSON geometry object")
    if geometry["type"] not in {
        "LineString",
        "MultiLineString",
        "Polygon",
        "MultiPolygon",
    }:
        raise EraGeometryPackError(
            f"{path}.geometry.type must be LineString, MultiLineString, "
            "Polygon, or MultiPolygon"
        )
    kind = hint.get("kind", "frontier")
    if not isinstance(kind, str) or not kind.strip():
        raise EraGeometryPackError(f"{path}.kind must be a non-empty string")
    confidence = hint.get("confidence")
    if confidence is not None and confidence not in {"high", "medium", "low", "illustrative"}:
        raise EraGeometryPackError(
            f"{path}.confidence must be high, medium, low, or illustrative"
        )


def _validate_hard_override(override: dict[str, Any], path: str) -> None:
    if not isinstance(override, dict):
        raise EraGeometryPackError(f"{path} must be an object")
    operation = override.get("operation")
    if operation not in ALLOWED_OPERATIONS:
        raise EraGeometryPackError(
            f"{path}.operation must be one of {sorted(ALLOWED_OPERATIONS)}"
        )
    scaffold_id = override.get("scaffold_province_id")
    if not isinstance(scaffold_id, str) or not scaffold_id.strip():
        raise EraGeometryPackError(
            f"{path}.scaffold_province_id must be a non-empty string"
        )
    reason = override.get("reason")
    if reason is not None and (not isinstance(reason, str) or not reason.strip()):
        raise EraGeometryPackError(f"{path}.reason must be a non-empty string when present")

    if operation == "replace":
        era_id = override.get("era_province_id") or scaffold_id
        if not isinstance(era_id, str) or not era_id.strip():
            raise EraGeometryPackError(f"{path}.era_province_id must be a non-empty string")
        if "geometry" not in override or not isinstance(override["geometry"], dict):
            raise EraGeometryPackError(f"{path}.geometry is required for replace")
    elif operation == "split":
        children = override.get("children")
        if not isinstance(children, list) or len(children) < 2:
            raise EraGeometryPackError(
                f"{path}.children must be a list of at least two child provinces"
            )
        seen: set[str] = set()
        for c_index, child in enumerate(children):
            c_path = f"{path}.children[{c_index}]"
            if not isinstance(child, dict):
                raise EraGeometryPackError(f"{c_path} must be an object")
            era_id = child.get("era_province_id")
            if not isinstance(era_id, str) or not era_id.strip():
                raise EraGeometryPackError(f"{c_path}.era_province_id must be a non-empty string")
            if era_id in seen:
                raise EraGeometryPackError(f"{c_path}.era_province_id duplicates {era_id!r}")
            seen.add(era_id)
            if "geometry" not in child or not isinstance(child["geometry"], dict):
                raise EraGeometryPackError(f"{c_path}.geometry is required")
            display = child.get("display_name")
            if display is not None and (not isinstance(display, str) or not display.strip()):
                raise EraGeometryPackError(
                    f"{c_path}.display_name must be a non-empty string when present"
                )
    elif operation == "identity":
        # Explicit no-op mapping for documentation / lineage completeness.
        era_id = override.get("era_province_id") or scaffold_id
        if not isinstance(era_id, str) or not era_id.strip():
            raise EraGeometryPackError(f"{path}.era_province_id must be a non-empty string")


def _validate_lineage_row(row: dict[str, Any], path: str) -> None:
    if not isinstance(row, dict):
        raise EraGeometryPackError(f"{path} must be an object")
    for key in ("era_province_id", "scaffold_province_id", "operation"):
        if key not in row:
            raise EraGeometryPackError(f"{path} missing required key: {key}")
        if not isinstance(row[key], str) or not str(row[key]).strip():
            raise EraGeometryPackError(f"{path}.{key} must be a non-empty string")
    if row["operation"] not in ALLOWED_LINEAGE_OPS:
        raise EraGeometryPackError(
            f"{path}.operation must be one of {sorted(ALLOWED_LINEAGE_OPS)}"
        )


def _summarize(document: dict[str, Any], path: Path) -> EraGeometryPackSummary:
    modes = tuple(document.get("geometry_modes") or ())
    region = document.get("priority_region") or {}
    return EraGeometryPackSummary(
        pack_id=str(document["pack_id"]),
        path=str(path),
        era=str(document["era"]),
        scenario_id=document.get("scenario_id"),
        quality_tier=str(document["quality_tier"]),
        priority_region_id=str(region.get("id") or ""),
        geometry_modes=modes,
        boundary_hint_count=len(document.get("boundary_hints") or []),
        hard_override_count=len(document.get("hard_overrides") or []),
    )
