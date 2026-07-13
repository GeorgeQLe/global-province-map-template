"""Build multi-era geometry + politics packages (M16)."""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from gpm import __version__
from gpm.era_geometry import (
    EraGeometryError,
    apply_era_geometry_pack,
    apply_era_geometry_packs,
)
from gpm.multi_era.migration import build_migration_document, migration_markdown
from gpm.multi_era.packs import (
    MultiEraPackError,
    load_multi_era_pack,
    resolve_era_geometry_pack_ids,
    validate_multi_era_pack,
)
from gpm.paths import PROCESSED_DATA_DIR
from gpm.scenarios import ScenarioError, build_scenario_ownership, load_scenario


class MultiEraError(RuntimeError):
    """Raised when a multi-era pack cannot be built."""


@dataclass(frozen=True)
class MultiEraBuildResult:
    pack_id: str
    display_name: str
    output_dir: str
    era_count: int
    eras: tuple[str, ...]
    scenario_ids: tuple[str, ...]
    era_geometry_pack_ids: tuple[str, ...]
    region_matrix_row_count: int
    migration_json: str
    migration_md: str
    manifest_output: str
    files_written: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_multi_era_pack(
    pack_id: str,
    *,
    province_input: Path = PROCESSED_DATA_DIR / "provinces.geojson",
    output_dir: Path | None = None,
    pack_path: Path | None = None,
    recompute_adjacency: bool = False,
    profile_id: str | None = None,
    apply_geometry: bool = True,
    resolve_politics: bool = True,
) -> MultiEraBuildResult:
    """Assemble a multi-era package: geometry apply, politics resolve, migration notes.

    For each era slot:
    - optionally apply the linked era-geometry pack onto the scaffold
    - optionally resolve the linked scenario ownership onto the (era) provinces
    Writes a region quality matrix, migration notes, and a top-level manifest.
    """
    try:
        pack = load_multi_era_pack(pack_id, path=pack_path)
    except MultiEraPackError as exc:
        raise MultiEraError(str(exc)) from exc
    validate_multi_era_pack(pack)

    if not province_input.is_file():
        raise MultiEraError(f"Province input does not exist: {province_input}")

    out_dir = (
        output_dir
        if output_dir is not None
        else PROCESSED_DATA_DIR / "multi_era" / str(pack["pack_id"])
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    eras_dir = out_dir / "eras"
    eras_dir.mkdir(parents=True, exist_ok=True)

    generated_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    files_written: list[str] = []
    era_summaries: list[dict[str, Any]] = []
    lineage_paths: dict[str, str] = {}

    for slot in pack["eras"]:
        era = str(slot["era"])
        scenario_id = str(slot["scenario_id"])
        geom_pack_ids = resolve_era_geometry_pack_ids(slot)
        geom_pack_id = geom_pack_ids[0] if len(geom_pack_ids) == 1 else (
            "+".join(geom_pack_ids) if geom_pack_ids else None
        )
        era_out = eras_dir / era
        era_out.mkdir(parents=True, exist_ok=True)

        province_layer = province_input
        geom_result: dict[str, Any] | None = None

        if apply_geometry and geom_pack_ids:
            try:
                if len(geom_pack_ids) == 1:
                    applied = apply_era_geometry_pack(
                        geom_pack_ids[0],
                        province_input=province_input,
                        output_dir=era_out / "geometry",
                        recompute_adjacency=recompute_adjacency,
                        profile_id=profile_id or slot.get("recommended_profile"),
                    )
                else:
                    applied = apply_era_geometry_packs(
                        geom_pack_ids,
                        province_input=province_input,
                        output_dir=era_out / "geometry",
                        recompute_adjacency=recompute_adjacency,
                        profile_id=profile_id or slot.get("recommended_profile"),
                    )
            except EraGeometryError as exc:
                raise MultiEraError(
                    f"Era {era}: failed to apply geometry pack(s) "
                    f"{geom_pack_ids}: {exc}"
                ) from exc
            province_layer = Path(applied.provinces_output)
            geom_result = applied.to_dict()
            lineage_paths[era] = applied.lineage_json_output
            for path_str in applied.files_written:
                files_written.append(
                    f"eras/{era}/geometry/{Path(path_str).name}"
                )
        else:
            # Copy scaffold provinces as the era geometry baseline.
            dest = era_out / "geometry"
            dest.mkdir(parents=True, exist_ok=True)
            scaffold_out = dest / "provinces.geojson"
            shutil.copy2(province_input, scaffold_out)
            province_layer = scaffold_out
            files_written.append(f"eras/{era}/geometry/provinces.geojson")
            quality_scope = {
                "schema_version": "0.1.0",
                "pack_id": pack["pack_id"],
                "era": era,
                "geometry_quality_tier": slot["geometry_quality_tier"],
                "note": (
                    "No era-geometry pack linked; scaffold provinces used as-is."
                    if not geom_pack_ids
                    else "Geometry apply skipped by build flag."
                ),
            }
            scope_path = dest / "quality_scope.json"
            scope_path.write_text(
                json.dumps(quality_scope, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            files_written.append(f"eras/{era}/geometry/quality_scope.json")

        politics_result: dict[str, Any] | None = None
        if resolve_politics:
            try:
                load_scenario(scenario_id)
                built = build_scenario_ownership(
                    scenario_id,
                    profile_id=profile_id
                    or slot.get("recommended_profile")
                    or "modern-small",
                    province_input=province_layer,
                    output_dir=era_out / "politics",
                )
            except ScenarioError as exc:
                raise MultiEraError(
                    f"Era {era}: failed to resolve politics for {scenario_id}: {exc}"
                ) from exc
            politics_result = built.to_dict()
            for name in built.files_written:
                files_written.append(f"eras/{era}/politics/{Path(name).name}")

        era_manifest = {
            "schema_version": "0.1.0",
            "era": era,
            "scenario_id": scenario_id,
            "era_geometry_pack_id": geom_pack_id,
            "era_geometry_pack_ids": geom_pack_ids,
            "geometry_quality_tier": slot["geometry_quality_tier"],
            "politics_quality_tier": slot["politics_quality_tier"],
            "recommended_profile": slot.get("recommended_profile"),
            "province_layer": str(province_layer),
            "geometry_apply": geom_result,
            "politics_resolve": politics_result,
            "notes": slot.get("notes"),
        }
        era_manifest_path = era_out / "era_manifest.json"
        era_manifest_path.write_text(
            json.dumps(era_manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        files_written.append(f"eras/{era}/era_manifest.json")
        era_summaries.append(
            {
                "era": era,
                "scenario_id": scenario_id,
                "era_geometry_pack_id": geom_pack_id,
                "era_geometry_pack_ids": geom_pack_ids,
                "geometry_quality_tier": slot["geometry_quality_tier"],
                "politics_quality_tier": slot["politics_quality_tier"],
                "recommended_profile": slot.get("recommended_profile"),
                "has_geometry_apply": geom_result is not None,
                "has_politics_resolve": politics_result is not None,
                "province_count": (
                    (geom_result or {}).get("province_count_out")
                    or (politics_result or {}).get("land_province_count")
                ),
            }
        )

    # Region quality matrix (pass-through + stamp)
    matrix_doc = {
        "schema_version": "0.1.0",
        "document_type": "region-quality-matrix",
        "pack_id": pack["pack_id"],
        "priority_region": pack["priority_region"],
        "priority_regions": pack.get("priority_regions")
        or [pack["priority_region"]],
        "rows": pack["region_quality_matrix"],
        "generated_at": generated_at,
        "generator_version": __version__,
    }
    matrix_path = out_dir / "region_quality_matrix.json"
    matrix_path.write_text(
        json.dumps(matrix_doc, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    files_written.append("region_quality_matrix.json")

    migration_doc = build_migration_document(
        pack,
        era_lineage_paths=lineage_paths,
        generated_at=generated_at,
    )
    migration_json_path = out_dir / "migration_notes.json"
    migration_md_path = out_dir / "MIGRATION.md"
    migration_json_path.write_text(
        json.dumps(migration_doc, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    migration_md_path.write_text(migration_markdown(migration_doc), encoding="utf-8")
    files_written.extend(["migration_notes.json", "MIGRATION.md"])

    # README
    readme = _readme_body(pack, era_summaries)
    readme_path = out_dir / "README.md"
    readme_path.write_text(readme, encoding="utf-8")
    files_written.append("README.md")

    # Copy pack definition for reproducibility
    pack_copy = out_dir / "pack.json"
    pack_copy.write_text(
        json.dumps(pack, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    files_written.append("pack.json")

    manifest = {
        "schema_version": "0.1.0",
        "manifest_type": "multi-era-pack",
        "pack_id": pack["pack_id"],
        "display_name": pack["display_name"],
        "generated_at": generated_at,
        "generator_version": __version__,
        "province_input": str(province_input),
        "priority_region": pack["priority_region"],
        "era_count": len(era_summaries),
        "eras": era_summaries,
        "region_quality_matrix_rows": len(pack["region_quality_matrix"]),
        "apply_geometry": apply_geometry,
        "resolve_politics": resolve_politics,
        "recompute_adjacency": recompute_adjacency,
        "files": sorted(set(files_written)),
        "source_notes": pack.get("source_notes") or [],
        "do_not_claim": pack.get("do_not_claim") or [],
    }
    manifest_path = out_dir / "multi_era_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    files_written.append("multi_era_manifest.json")

    return MultiEraBuildResult(
        pack_id=str(pack["pack_id"]),
        display_name=str(pack["display_name"]),
        output_dir=str(out_dir),
        era_count=len(era_summaries),
        eras=tuple(str(s["era"]) for s in era_summaries),
        scenario_ids=tuple(str(s["scenario_id"]) for s in era_summaries),
        era_geometry_pack_ids=tuple(
            pid
            for s in era_summaries
            for pid in (
                s.get("era_geometry_pack_ids")
                or ([s["era_geometry_pack_id"]] if s.get("era_geometry_pack_id") else [])
            )
        ),
        region_matrix_row_count=len(pack["region_quality_matrix"]),
        migration_json=str(migration_json_path),
        migration_md=str(migration_md_path),
        manifest_output=str(manifest_path),
        files_written=tuple(sorted(set(files_written))),
    )


def _readme_body(pack: dict[str, Any], era_summaries: list[dict[str, Any]]) -> str:
    lines = [
        f"# Multi-era pack: `{pack['pack_id']}`",
        "",
        pack["display_name"],
        "",
        "## Eras",
        "",
        "| Era | Scenario | Geometry pack | Geometry | Politics |",
        "| --- | --- | --- | --- | --- |",
    ]
    for slot in era_summaries:
        pack_ids = slot.get("era_geometry_pack_ids") or []
        if pack_ids:
            gp = " + ".join(pack_ids)
        else:
            gp = slot.get("era_geometry_pack_id") or "—"
        lines.append(
            "| {era} | `{sc}` | `{gp}` | `{gt}` | `{pt}` |".format(
                era=slot["era"],
                sc=slot["scenario_id"],
                gp=gp,
                gt=slot["geometry_quality_tier"],
                pt=slot["politics_quality_tier"],
            )
        )
    lines.extend(
        [
            "",
            "## Layout",
            "",
            "- `eras/<era>/geometry/` — applied (or scaffold) province layer + lineage",
            "- `eras/<era>/politics/` — resolved ownership tables for the era scenario",
            "- `region_quality_matrix.json` — per-region quality tiers by era",
            "- `MIGRATION.md` / `migration_notes.json` — consumer migration notes",
            "- `multi_era_manifest.json` — build inventory",
            "",
            "## Honest limits",
            "",
        ]
    )
    for item in pack.get("do_not_claim") or []:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)
