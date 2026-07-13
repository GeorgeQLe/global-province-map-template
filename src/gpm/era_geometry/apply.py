"""Apply an era-geometry pack to a modern scaffold province layer (M15)."""

from __future__ import annotations

import copy
import csv
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from gpm import __version__
from gpm.era_geometry.lineage import (
    LINEAGE_CSV_COLUMNS,
    build_lineage_document,
    lineage_csv_rows,
)
from gpm.era_geometry.packs import (
    EraGeometryPackError,
    load_era_geometry_pack,
    validate_era_geometry_pack,
)
from gpm.paths import PROCESSED_DATA_DIR


class EraGeometryError(RuntimeError):
    """Raised when era-geometry application cannot continue."""


@dataclass(frozen=True)
class EraGeometryApplyResult:
    pack_id: str
    era: str
    scenario_id: str | None
    quality_tier: str
    priority_region_id: str
    province_input: str
    output_dir: str
    province_count_in: int
    province_count_out: int
    priority_region_count: int
    hard_override_applied: int
    hard_override_skipped: int
    boundary_hint_count: int
    lineage_row_count: int
    geometry_modes: tuple[str, ...]
    provinces_output: str
    boundary_hints_output: str
    lineage_json_output: str
    lineage_csv_output: str
    manifest_output: str
    files_written: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def apply_era_geometry_packs(
    pack_ids: list[str] | tuple[str, ...],
    *,
    province_input: Path = PROCESSED_DATA_DIR / "provinces.geojson",
    output_dir: Path | None = None,
    recompute_adjacency: bool = False,
    adjacency_output: Path | None = None,
    profile_id: str | None = None,
) -> EraGeometryApplyResult:
    """Apply one or more era-geometry packs in order, merging hints and lineage.

    Used by multi-region multi-era builds (M20): e.g. WE then CE packs for the
    same era. Packs must not hard-override the same scaffold province IDs.
    Intermediate steps use a temporary directory (not committed under output).
    """
    ids = [str(p).strip() for p in pack_ids if str(p).strip()]
    if not ids:
        raise EraGeometryError("apply_era_geometry_packs requires at least one pack id")
    if len(ids) == 1:
        return apply_era_geometry_pack(
            ids[0],
            province_input=province_input,
            output_dir=output_dir,
            recompute_adjacency=recompute_adjacency,
            adjacency_output=adjacency_output,
            profile_id=profile_id,
        )

    import tempfile

    out_dir = (
        output_dir
        if output_dir is not None
        else PROCESSED_DATA_DIR / "era_geometry" / "+".join(ids)
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    current_input = province_input
    step_results: list[EraGeometryApplyResult] = []
    # Intermediate steps live in a temp tree so committed samples stay clean.
    with tempfile.TemporaryDirectory(prefix="gpm_era_compose_") as tmp:
        steps_dir = Path(tmp)
        for index, pack_id in enumerate(ids):
            step_out = steps_dir / f"{index:02d}_{pack_id}"
            # Adjacency only on the final step to avoid intermediate graph noise.
            is_last = index == len(ids) - 1
            result = apply_era_geometry_pack(
                pack_id,
                province_input=current_input,
                output_dir=step_out,
                recompute_adjacency=is_last and recompute_adjacency,
                adjacency_output=(
                    (adjacency_output or (out_dir / "adjacency.csv"))
                    if is_last and recompute_adjacency
                    else None
                ),
                profile_id=profile_id,
            )
            step_results.append(result)
            current_input = Path(result.provinces_output)

        # Snapshot intermediate paths we still need after temp cleanup.
        last_provinces_text = Path(step_results[-1].provinces_output).read_text(
            encoding="utf-8"
        )
        step_hint_docs: list[dict[str, Any]] = []
        step_lineage_docs: list[dict[str, Any]] = []
        last_adjacency_text = None
        for result in step_results:
            hints_path = Path(result.boundary_hints_output)
            if hints_path.is_file():
                try:
                    step_hint_docs.append(
                        json.loads(hints_path.read_text(encoding="utf-8"))
                    )
                except json.JSONDecodeError:
                    pass
            lineage_path = Path(result.lineage_json_output)
            if lineage_path.is_file():
                try:
                    step_lineage_docs.append(
                        json.loads(lineage_path.read_text(encoding="utf-8"))
                    )
                except json.JSONDecodeError:
                    pass
        if recompute_adjacency:
            for path_str in step_results[-1].files_written:
                if path_str.endswith("adjacency.csv"):
                    last_adjacency_text = Path(path_str).read_text(encoding="utf-8")
                    break

    # Merge boundary hints from all steps (snapshotted before temp cleanup).
    merged_hints: list[dict[str, Any]] = []
    seen_hint_ids: set[str] = set()
    for hints_doc in step_hint_docs:
        for feature in hints_doc.get("features") or []:
            props = feature.get("properties") or {}
            hint_id = str(props.get("hint_id") or "")
            if hint_id and hint_id in seen_hint_ids:
                continue
            if hint_id:
                seen_hint_ids.add(hint_id)
            merged_hints.append(feature)

    # Lineage: merge by era_province_id. Later hard_overrides replace earlier
    # rows; pure scaffold pass-throughs do not clobber prior hard work.
    lineage_by_era_id: dict[str, dict[str, Any]] = {}
    for lineage_doc in step_lineage_docs:
        for row in lineage_doc.get("rows") or []:
            era_id = str(row.get("era_province_id") or "")
            if not era_id:
                continue
            existing = lineage_by_era_id.get(era_id)
            new_mode = str(row.get("geometry_mode") or "")
            new_op = str(row.get("operation") or "")
            if existing is not None and new_mode == "scaffold":
                # Keep earlier hard-override / split lineage.
                continue
            if (
                existing is not None
                and new_op == "identity"
                and existing.get("operation") not in {None, "identity"}
            ):
                continue
            lineage_by_era_id[era_id] = dict(row)

    last = step_results[-1]
    final_provinces = out_dir / "provinces.geojson"
    final_provinces.write_text(last_provinces_text, encoding="utf-8")

    generated_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    pack_ids_joined = "+".join(ids)
    first_pack = load_era_geometry_pack(ids[0])
    last_pack = load_era_geometry_pack(ids[-1])
    priority_regions = []
    for pack_id in ids:
        pack = load_era_geometry_pack(pack_id)
        region = pack.get("priority_region") or {}
        if region:
            priority_regions.append(region)

    hints_fc = {
        "type": "FeatureCollection",
        "name": f"boundary_hints_{pack_ids_joined}",
        "features": merged_hints,
        "gpm": {
            "schema_version": "0.1.0",
            "milestone": "M20",
            "layer": "boundary_hints",
            "pack_ids": list(ids),
            "pack_id": pack_ids_joined,
            "era": last_pack.get("era") or first_pack.get("era"),
            "feature_count": len(merged_hints),
            "generated_at": generated_at,
            "generator_version": __version__,
            "paint": {
                "line_color": "#f59e0b",
                "line_width": 2.5,
                "line_dasharray": [2, 1],
                "fill_color": "#f59e0b",
                "fill_opacity": 0.12,
            },
        },
    }
    hints_path = out_dir / "boundary_hints.geojson"
    _write_json(hints_path, hints_fc)

    lineage_rows = list(lineage_by_era_id.values())
    lineage_doc = build_lineage_document(
        pack_id=pack_ids_joined,
        era=str(last_pack.get("era") or first_pack.get("era") or ""),
        scenario_id=last_pack.get("scenario_id") or first_pack.get("scenario_id"),
        rows=lineage_rows,
        notes=[
            f"Composed era-geometry packs (M20): {', '.join(ids)}",
            "scaffold_province_id remains the stable join key across steps.",
        ],
    )
    lineage_json_path = out_dir / "lineage.json"
    lineage_csv_path = out_dir / "lineage.csv"
    _write_json(lineage_json_path, lineage_doc)
    _write_lineage_csv(lineage_csv_path, lineage_doc)

    quality_path = out_dir / "quality_scope.json"
    _write_json(
        quality_path,
        {
            "schema_version": "0.1.0",
            "pack_id": pack_ids_joined,
            "composed_pack_ids": list(ids),
            "era": last_pack.get("era") or first_pack.get("era"),
            "quality_tier": "period-geometry",
            "priority_regions": priority_regions,
            "priority_region": priority_regions[0] if priority_regions else {},
            "period_true_scope": [
                str((r or {}).get("id") or "") for r in priority_regions if r
            ],
            "scaffold_backed_scope": ["outside priority_regions", "seas", "rest of world"],
            "source_notes": [
                f"Composed from packs: {', '.join(ids)}",
            ],
            "do_not_claim": [
                "period-correct province geometry worldwide",
                "Paradox-grade completeness for any single region",
            ],
        },
    )

    files_written = [
        str(final_provinces),
        str(hints_path),
        str(lineage_json_path),
        str(lineage_csv_path),
        str(quality_path),
    ]
    if recompute_adjacency and last_adjacency_text is not None:
        adj_final = adjacency_output or (out_dir / "adjacency.csv")
        adj_final = Path(adj_final)
        adj_final.parent.mkdir(parents=True, exist_ok=True)
        adj_final.write_text(last_adjacency_text, encoding="utf-8")
        files_written.append(str(adj_final))

    manifest = {
        "schema_version": "0.1.0",
        "manifest_type": "era-geometry-composed",
        "milestone": "M20",
        "pack_id": pack_ids_joined,
        "composed_pack_ids": list(ids),
        "era": last_pack.get("era") or first_pack.get("era"),
        "scenario_id": last_pack.get("scenario_id") or first_pack.get("scenario_id"),
        "display_name": f"Composed: {' + '.join(ids)}",
        "quality_tier": "period-geometry",
        "priority_regions": priority_regions,
        "geometry_modes": ["boundary_hints", "hard_overrides"],
        "counts": {
            "provinces_in": step_results[0].province_count_in,
            "provinces_out": last.province_count_out,
            "priority_region_provinces": sum(r.priority_region_count for r in step_results),
            "hard_overrides_applied": sum(r.hard_override_applied for r in step_results),
            "hard_overrides_skipped": sum(r.hard_override_skipped for r in step_results),
            "boundary_hints": len(merged_hints),
            "lineage_rows": len(lineage_rows),
            "composed_steps": len(ids),
        },
        "step_results": [r.to_dict() for r in step_results],
        "inputs": {
            "province_input": str(province_input),
            "pack_ids": list(ids),
        },
        "files": [
            "provinces.geojson",
            "boundary_hints.geojson",
            "lineage.json",
            "lineage.csv",
            "quality_scope.json",
            "era_geometry_manifest.json",
        ]
        + (["adjacency.csv"] if recompute_adjacency else []),
        "generated_at": generated_at,
        "generator_version": __version__,
    }
    manifest_path = out_dir / "era_geometry_manifest.json"
    _write_json(manifest_path, manifest)
    files_written.append(str(manifest_path))

    return EraGeometryApplyResult(
        pack_id=pack_ids_joined,
        era=str(last_pack.get("era") or first_pack.get("era") or ""),
        scenario_id=last_pack.get("scenario_id") or first_pack.get("scenario_id"),
        quality_tier="period-geometry",
        priority_region_id="+".join(
            str((r or {}).get("id") or "") for r in priority_regions if r
        ),
        province_input=str(province_input),
        output_dir=str(out_dir),
        province_count_in=step_results[0].province_count_in,
        province_count_out=last.province_count_out,
        priority_region_count=sum(r.priority_region_count for r in step_results),
        hard_override_applied=sum(r.hard_override_applied for r in step_results),
        hard_override_skipped=sum(r.hard_override_skipped for r in step_results),
        boundary_hint_count=len(merged_hints),
        lineage_row_count=len(lineage_rows),
        geometry_modes=("boundary_hints", "hard_overrides"),
        provinces_output=str(final_provinces),
        boundary_hints_output=str(hints_path),
        lineage_json_output=str(lineage_json_path),
        lineage_csv_output=str(lineage_csv_path),
        manifest_output=str(manifest_path),
        files_written=tuple(files_written),
    )


def apply_era_geometry_pack(
    pack_id: str,
    *,
    province_input: Path = PROCESSED_DATA_DIR / "provinces.geojson",
    output_dir: Path | None = None,
    pack_path: Path | None = None,
    recompute_adjacency: bool = False,
    adjacency_output: Path | None = None,
    profile_id: str | None = None,
) -> EraGeometryApplyResult:
    """Apply soft boundary hints and/or hard province overrides to a scaffold.

    Hard overrides that reference missing scaffold province IDs are skipped
    (counted) so the same pack can ship sample-ID demos and soft hints for
    full Natural Earth builds.
    """
    try:
        pack = load_era_geometry_pack(pack_id, path=pack_path)
    except EraGeometryPackError as exc:
        raise EraGeometryError(str(exc)) from exc

    if not province_input.is_file():
        raise EraGeometryError(f"Province input does not exist: {province_input}")

    try:
        collection = json.loads(province_input.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise EraGeometryError(f"Invalid province GeoJSON: {exc}") from exc
    if not isinstance(collection, dict) or collection.get("type") != "FeatureCollection":
        raise EraGeometryError("Province input must be a GeoJSON FeatureCollection")

    features_in = list(collection.get("features") or [])
    if not features_in:
        raise EraGeometryError("Province input has no features")

    out_dir = (
        output_dir
        if output_dir is not None
        else PROCESSED_DATA_DIR / "era_geometry" / str(pack["pack_id"])
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    region = pack["priority_region"]
    parent_country_ids = {
        str(c).strip().upper()
        for c in (region.get("parent_country_ids") or [])
        if str(c).strip()
    }
    bbox = region.get("bbox")
    modes = tuple(pack.get("geometry_modes") or ())

    by_id: dict[str, dict[str, Any]] = {}
    for feature in features_in:
        props = feature.get("properties") or {}
        pid = props.get("province_id")
        if not isinstance(pid, str) or not pid.strip():
            raise EraGeometryError("Every province feature needs a non-empty province_id")
        if pid in by_id:
            raise EraGeometryError(f"Duplicate province_id in input: {pid}")
        by_id[pid] = feature

    overrides_by_scaffold: dict[str, dict[str, Any]] = {}
    for override in pack.get("hard_overrides") or []:
        scaffold_id = str(override["scaffold_province_id"])
        if scaffold_id in overrides_by_scaffold:
            raise EraGeometryError(
                f"Multiple hard_overrides target scaffold_province_id {scaffold_id!r}"
            )
        overrides_by_scaffold[scaffold_id] = override

    lineage_rows: list[dict[str, Any]] = []
    features_out: list[dict[str, Any]] = []
    applied = 0
    skipped = 0
    priority_count = 0

    for scaffold_id, feature in by_id.items():
        props = dict(feature.get("properties") or {})
        in_priority = _in_priority_region(feature, parent_country_ids, bbox)
        if in_priority:
            priority_count += 1

        # Preserve original scaffold id when composing packs (M20 multi-step).
        original_scaffold_id = str(
            props.get("scaffold_province_id") or scaffold_id
        )

        override = overrides_by_scaffold.get(scaffold_id)
        if override is None or "hard_overrides" not in modes:
            features_out.append(_annotate_feature(feature, pack, in_priority, "scaffold"))
            lineage_rows.append(
                {
                    "era_province_id": scaffold_id,
                    "scaffold_province_id": original_scaffold_id,
                    "operation": "identity",
                    "display_name": props.get("display_name"),
                    "in_priority_region": in_priority,
                    "geometry_mode": "scaffold",
                }
            )
            continue

        if scaffold_id not in by_id:
            skipped += 1
            continue

        operation = override["operation"]
        reason = override.get("reason")

        if operation == "identity":
            era_id = str(override.get("era_province_id") or scaffold_id)
            out = _annotate_feature(feature, pack, in_priority, "identity")
            out["properties"]["province_id"] = era_id
            out["properties"]["scaffold_province_id"] = original_scaffold_id
            features_out.append(out)
            lineage_rows.append(
                {
                    "era_province_id": era_id,
                    "scaffold_province_id": original_scaffold_id,
                    "operation": "identity",
                    "display_name": out["properties"].get("display_name"),
                    "in_priority_region": in_priority,
                    "geometry_mode": "hard_overrides",
                    "reason": reason,
                }
            )
            applied += 1
            continue

        if operation == "replace":
            era_id = str(override.get("era_province_id") or scaffold_id)
            out = copy.deepcopy(feature)
            out["geometry"] = copy.deepcopy(override["geometry"])
            out_props = dict(out.get("properties") or {})
            out_props["province_id"] = era_id
            out_props["scaffold_province_id"] = original_scaffold_id
            if override.get("display_name"):
                out_props["display_name"] = override["display_name"]
            for key in (
                "parent_region_id",
                "parent_country_id",
                "terrain_class",
                "coastal",
                "island",
            ):
                if key in override and override[key] is not None:
                    out_props[key] = override[key]
            out["properties"] = out_props
            features_out.append(
                _annotate_feature(out, pack, in_priority, "hard_overrides")
            )
            lineage_rows.append(
                {
                    "era_province_id": era_id,
                    "scaffold_province_id": original_scaffold_id,
                    "operation": "replace",
                    "display_name": out_props.get("display_name"),
                    "in_priority_region": in_priority,
                    "geometry_mode": "hard_overrides",
                    "reason": reason,
                }
            )
            applied += 1
            continue

        if operation == "split":
            children = override["children"]
            part_count = len(children)
            for part_index, child in enumerate(children, start=1):
                era_id = str(child["era_province_id"])
                out = copy.deepcopy(feature)
                out["geometry"] = copy.deepcopy(child["geometry"])
                out_props = dict(out.get("properties") or {})
                out_props["province_id"] = era_id
                out_props["scaffold_province_id"] = original_scaffold_id
                out_props["display_name"] = child.get("display_name") or (
                    f"{props.get('display_name') or scaffold_id} ({part_index})"
                )
                out_props["era_split_parent_id"] = scaffold_id
                out_props["era_split_part_index"] = part_index
                out_props["era_split_part_count"] = part_count
                for key in (
                    "parent_region_id",
                    "parent_country_id",
                    "terrain_class",
                    "coastal",
                    "island",
                    "estimated_population",
                    "area_sq_km",
                ):
                    if key in child and child[key] is not None:
                        out_props[key] = child[key]
                # Split population/area evenly when not overridden.
                if "estimated_population" not in child and isinstance(
                    props.get("estimated_population"), (int, float)
                ):
                    out_props["estimated_population"] = float(
                        props["estimated_population"]
                    ) / part_count
                if "area_sq_km" not in child and isinstance(
                    props.get("area_sq_km"), (int, float)
                ):
                    out_props["area_sq_km"] = float(props["area_sq_km"]) / part_count
                out["properties"] = out_props
                features_out.append(
                    _annotate_feature(out, pack, in_priority, "hard_overrides")
                )
                lineage_rows.append(
                    {
                        "era_province_id": era_id,
                        "scaffold_province_id": original_scaffold_id,
                        "operation": "split_child",
                        "display_name": out_props.get("display_name"),
                        "part_index": part_index,
                        "part_count": part_count,
                        "in_priority_region": in_priority,
                        "geometry_mode": "hard_overrides",
                        "reason": reason,
                    }
                )
            applied += 1
            continue

        raise EraGeometryError(f"Unsupported hard override operation: {operation}")

    # Count hard overrides whose scaffold IDs were absent from input.
    for scaffold_id in overrides_by_scaffold:
        if scaffold_id not in by_id:
            skipped += 1

    # Pack-authored lineage rows (documentation) merge after generated rows
    # only when they introduce new era ids not already present.
    existing_era_ids = {row["era_province_id"] for row in lineage_rows}
    for row in pack.get("lineage") or []:
        if row["era_province_id"] not in existing_era_ids:
            lineage_rows.append(dict(row))
            existing_era_ids.add(row["era_province_id"])

    generated_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    provinces_fc = {
        "type": "FeatureCollection",
        "name": f"provinces_{pack['pack_id']}",
        "features": features_out,
        "gpm": {
            "schema_version": "0.1.0",
            "milestone": "M15",
            "layer": "era_provinces",
            "pack_id": pack["pack_id"],
            "era": pack["era"],
            "scenario_id": pack.get("scenario_id"),
            "quality_tier": pack["quality_tier"],
            "priority_region_id": region["id"],
            "geometry_modes": list(modes),
            "feature_count": len(features_out),
            "generated_at": generated_at,
            "generator_version": __version__,
            "source_province_input": str(province_input),
        },
    }

    hints_fc = _boundary_hints_collection(pack, generated_at)
    lineage_doc = build_lineage_document(
        pack_id=str(pack["pack_id"]),
        era=str(pack["era"]),
        scenario_id=pack.get("scenario_id"),
        rows=lineage_rows,
        notes=list(pack.get("source_notes") or []),
    )

    provinces_path = out_dir / "provinces.geojson"
    hints_path = out_dir / "boundary_hints.geojson"
    lineage_json_path = out_dir / "lineage.json"
    lineage_csv_path = out_dir / "lineage.csv"
    manifest_path = out_dir / "era_geometry_manifest.json"
    quality_path = out_dir / "quality_scope.json"

    _write_json(provinces_path, provinces_fc)
    _write_json(hints_path, hints_fc)
    _write_json(lineage_json_path, lineage_doc)
    _write_lineage_csv(lineage_csv_path, lineage_doc)
    _write_json(
        quality_path,
        {
            "schema_version": "0.1.0",
            "pack_id": pack["pack_id"],
            "era": pack["era"],
            "quality_tier": pack["quality_tier"],
            "priority_region": region,
            "period_true_scope": pack.get("period_true_scope")
            or [region["id"]],
            "scaffold_backed_scope": pack.get("scaffold_backed_scope")
            or ["outside priority_region"],
            "source_notes": pack.get("source_notes") or [],
            "do_not_claim": pack.get("do_not_claim") or [],
        },
    )

    files_written = [
        str(provinces_path),
        str(hints_path),
        str(lineage_json_path),
        str(lineage_csv_path),
        str(quality_path),
    ]

    if recompute_adjacency:
        from gpm.builders.adjacency import AdjacencyBuildError, build_land_adjacency

        adj_path = adjacency_output or (out_dir / "adjacency.csv")
        try:
            build_land_adjacency(
                profile_id or "modern-small",
                province_input=provinces_path,
                sea_input=None,
                output=adj_path,
            )
        except AdjacencyBuildError as exc:
            raise EraGeometryError(f"Adjacency recompute failed: {exc}") from exc
        files_written.append(str(adj_path))

    manifest = {
        "schema_version": "0.1.0",
        "manifest_type": "era-geometry",
        "milestone": "M15",
        "pack_id": pack["pack_id"],
        "era": pack["era"],
        "start_date": pack.get("start_date"),
        "scenario_id": pack.get("scenario_id"),
        "display_name": pack["display_name"],
        "quality_tier": pack["quality_tier"],
        "priority_region": region,
        "geometry_modes": list(modes),
        "counts": {
            "provinces_in": len(features_in),
            "provinces_out": len(features_out),
            "priority_region_provinces": priority_count,
            "hard_overrides_applied": applied,
            "hard_overrides_skipped": skipped,
            "boundary_hints": len(pack.get("boundary_hints") or []),
            "lineage_rows": len(lineage_doc["rows"]),
        },
        "inputs": {
            "province_input": str(province_input),
            "pack_id": pack["pack_id"],
        },
        "files": [
            "provinces.geojson",
            "boundary_hints.geojson",
            "lineage.json",
            "lineage.csv",
            "quality_scope.json",
            "era_geometry_manifest.json",
        ]
        + (["adjacency.csv"] if recompute_adjacency else []),
        "generated_at": generated_at,
        "generator_version": __version__,
        "source_notes": pack.get("source_notes") or [],
        "do_not_claim": pack.get("do_not_claim") or [],
    }
    _write_json(manifest_path, manifest)
    files_written.append(str(manifest_path))

    # Re-validate pack was well-formed (defense in depth).
    validate_era_geometry_pack(pack)

    return EraGeometryApplyResult(
        pack_id=str(pack["pack_id"]),
        era=str(pack["era"]),
        scenario_id=pack.get("scenario_id"),
        quality_tier=str(pack["quality_tier"]),
        priority_region_id=str(region["id"]),
        province_input=str(province_input),
        output_dir=str(out_dir),
        province_count_in=len(features_in),
        province_count_out=len(features_out),
        priority_region_count=priority_count,
        hard_override_applied=applied,
        hard_override_skipped=skipped,
        boundary_hint_count=len(pack.get("boundary_hints") or []),
        lineage_row_count=len(lineage_doc["rows"]),
        geometry_modes=modes,
        provinces_output=str(provinces_path),
        boundary_hints_output=str(hints_path),
        lineage_json_output=str(lineage_json_path),
        lineage_csv_output=str(lineage_csv_path),
        manifest_output=str(manifest_path),
        files_written=tuple(files_written),
    )


def _annotate_feature(
    feature: dict[str, Any],
    pack: dict[str, Any],
    in_priority: bool,
    geometry_mode: str,
) -> dict[str, Any]:
    out = copy.deepcopy(feature)
    props = dict(out.get("properties") or {})
    prior_pack = props.get("era_geometry_pack_id")
    prior_mode = props.get("era_geometry_mode")
    prior_tier = props.get("geometry_quality_tier")
    # When composing packs (M20), keep the pack/mode that last hard-touched
    # the province rather than overwriting with a later scaffold pass-through.
    if geometry_mode == "scaffold" and prior_mode and prior_mode != "scaffold":
        props["era_geometry_pack_id"] = prior_pack
        props["era_geometry_mode"] = prior_mode
    else:
        props["era_geometry_pack_id"] = pack["pack_id"]
        props["era_geometry_mode"] = geometry_mode
    props["era"] = pack["era"]
    # Priority region if this pack matches OR a prior pack already marked it.
    props["era_priority_region"] = bool(in_priority or props.get("era_priority_region"))
    if in_priority and geometry_mode != "scaffold":
        props["geometry_quality_tier"] = pack["quality_tier"]
    elif prior_tier == "period-geometry":
        props["geometry_quality_tier"] = "period-geometry"
    else:
        props["geometry_quality_tier"] = (
            pack["quality_tier"]
            if in_priority and geometry_mode != "scaffold"
            else "scaffold-baseline"
        )
    if not props.get("scaffold_province_id"):
        props["scaffold_province_id"] = props.get("province_id")
    # Preserve license/source lineage; tag era-geometry curator work.
    source = list(props.get("source_lineage") or [])
    tag = f"era_geometry:{pack['pack_id']}"
    if tag not in source:
        source.append(tag)
    props["source_lineage"] = source
    out["properties"] = props
    return out


def _in_priority_region(
    feature: dict[str, Any],
    parent_country_ids: set[str],
    bbox: list[float] | None,
) -> bool:
    props = feature.get("properties") or {}
    country = str(props.get("parent_country_id") or "").strip().upper()
    if parent_country_ids and country in parent_country_ids:
        return True
    if bbox and feature.get("geometry"):
        try:
            from shapely.geometry import shape

            geom = shape(feature["geometry"])
            if geom.is_empty:
                return False
            minx, miny, maxx, maxy = geom.bounds
            bminx, bminy, bmaxx, bmaxy = bbox
            # Any overlap with the priority bbox counts.
            return not (maxx < bminx or minx > bmaxx or maxy < bminy or miny > bmaxy)
        except Exception:
            return False
    return False


def _boundary_hints_collection(pack: dict[str, Any], generated_at: str) -> dict[str, Any]:
    features: list[dict[str, Any]] = []
    for hint in pack.get("boundary_hints") or []:
        props = {
            "hint_id": hint["hint_id"],
            "label": hint["label"],
            "kind": hint.get("kind") or "frontier",
            "confidence": hint.get("confidence") or "illustrative",
            "era": pack["era"],
            "pack_id": pack["pack_id"],
            "notes": hint.get("notes"),
            "related_tags": hint.get("related_tags") or [],
        }
        features.append(
            {
                "type": "Feature",
                "geometry": copy.deepcopy(hint["geometry"]),
                "properties": props,
            }
        )
    return {
        "type": "FeatureCollection",
        "name": f"boundary_hints_{pack['pack_id']}",
        "features": features,
        "gpm": {
            "schema_version": "0.1.0",
            "milestone": "M15",
            "layer": "boundary_hints",
            "pack_id": pack["pack_id"],
            "era": pack["era"],
            "feature_count": len(features),
            "generated_at": generated_at,
            "generator_version": __version__,
            "paint": {
                "line_color": "#f59e0b",
                "line_width": 2.5,
                "line_dasharray": [2, 1],
                "fill_color": "#f59e0b",
                "fill_opacity": 0.12,
            },
        },
    }


def _write_json(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_lineage_csv(path: Path, lineage_doc: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = lineage_csv_rows(lineage_doc)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(LINEAGE_CSV_COLUMNS))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
