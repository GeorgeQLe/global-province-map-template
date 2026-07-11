"""Migration notes for multi-era geometry + politics packs (M16)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from gpm import __version__


def build_migration_document(
    pack: dict[str, Any],
    *,
    era_lineage_paths: dict[str, str] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build a machine-readable migration notes document for consumers."""
    stamp = generated_at or datetime.now(UTC).replace(microsecond=0).isoformat()
    eras = pack.get("eras") or []
    notes = pack.get("migration_notes") if isinstance(pack.get("migration_notes"), dict) else {}
    lineage_paths = era_lineage_paths or {}

    era_slots: list[dict[str, Any]] = []
    for slot in eras:
        era = str(slot.get("era") or "")
        entry: dict[str, Any] = {
            "era": era,
            "scenario_id": slot.get("scenario_id"),
            "era_geometry_pack_id": slot.get("era_geometry_pack_id"),
            "geometry_quality_tier": slot.get("geometry_quality_tier"),
            "politics_quality_tier": slot.get("politics_quality_tier"),
            "recommended_profile": slot.get("recommended_profile"),
            "lineage_path": lineage_paths.get(era),
            "notes": slot.get("notes"),
        }
        era_slots.append(entry)

    consumer_guidance = list(notes.get("consumer_guidance") or [])
    if not consumer_guidance:
        consumer_guidance = [
            "Pin save/mod data to era province IDs when an era-geometry pack is applied.",
            "Use lineage.json / lineage.csv to migrate scaffold IDs to era IDs.",
            "Politics (owner/controller/cores/claims) are scenario overlays — "
            "rebuild them after geometry revisions.",
            "Quality tiers are region-scoped; do not assume global period geometry.",
        ]

    breaking = list(notes.get("breaking_changes") or [])
    do_not_claim = list(notes.get("do_not_claim") or pack.get("do_not_claim") or [])

    return {
        "schema_version": "0.1.0",
        "document_type": "multi-era-migration-notes",
        "pack_id": pack.get("pack_id"),
        "display_name": pack.get("display_name"),
        "generated_at": stamp,
        "generator_version": __version__,
        "summary": notes.get("summary")
        or (
            f"Migration notes for multi-era pack `{pack.get('pack_id')}`: "
            "scaffold ↔ era ID lineage, cross-era packaging, and quality tiers."
        ),
        "lineage_strategy": notes.get("lineage_strategy")
        or (
            "Each era-geometry pack emits its own lineage map. Scaffold IDs are "
            "stable across eras; era IDs may split/replace within a pack version. "
            "Cross-era joins should use scaffold_province_id as the join key."
        ),
        "eras": era_slots,
        "region_quality_matrix": pack.get("region_quality_matrix") or [],
        "consumer_guidance": consumer_guidance,
        "breaking_changes": breaking,
        "do_not_claim": do_not_claim,
        "cross_era_join": {
            "recommended_key": "scaffold_province_id",
            "era_id_field": "era_province_id",
            "notes": [
                "Do not assume era_province_id equality across different eras.",
                "A split in 1444 (e.g. Cologne) may not exist in 1836/1936 packs.",
                "Politics attach to the province layer used for that era build.",
            ],
        },
    }


def migration_markdown(document: dict[str, Any]) -> str:
    """Render MIGRATION.md from a migration notes document."""
    lines = [
        f"# Migration notes: `{document.get('pack_id')}`",
        "",
        document.get("summary") or "",
        "",
        "## Lineage strategy",
        "",
        document.get("lineage_strategy") or "",
        "",
        "## Eras in this pack",
        "",
        "| Era | Scenario | Geometry pack | Geometry tier | Politics tier | Profile |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for slot in document.get("eras") or []:
        lines.append(
            "| {era} | `{scenario}` | `{geom}` | `{gt}` | `{pt}` | `{prof}` |".format(
                era=slot.get("era") or "—",
                scenario=slot.get("scenario_id") or "—",
                geom=slot.get("era_geometry_pack_id") or "—",
                gt=slot.get("geometry_quality_tier") or "—",
                pt=slot.get("politics_quality_tier") or "—",
                prof=slot.get("recommended_profile") or "—",
            )
        )

    lines.extend(["", "## Cross-era joins", ""])
    join = document.get("cross_era_join") or {}
    lines.append(
        f"Recommended join key: `{join.get('recommended_key', 'scaffold_province_id')}`."
    )
    for note in join.get("notes") or []:
        lines.append(f"- {note}")

    matrix = document.get("region_quality_matrix") or []
    if matrix:
        lines.extend(["", "## Region quality matrix", ""])
        for row in matrix:
            lines.append(f"### {row.get('label') or row.get('region_id')}")
            lines.append("")
            lines.append("| Era | Geometry | Politics |")
            lines.append("| --- | --- | --- |")
            by_era = row.get("by_era") or {}
            for era in sorted(by_era.keys()):
                tiers = by_era[era]
                lines.append(
                    f"| {era} | `{tiers.get('geometry')}` | `{tiers.get('politics')}` |"
                )
            lines.append("")

    guidance = document.get("consumer_guidance") or []
    if guidance:
        lines.extend(["## Consumer guidance", ""])
        for item in guidance:
            lines.append(f"- {item}")
        lines.append("")

    breaking = document.get("breaking_changes") or []
    if breaking:
        lines.extend(["## Breaking changes", ""])
        for item in breaking:
            lines.append(f"- {item}")
        lines.append("")

    claims = document.get("do_not_claim") or []
    if claims:
        lines.extend(["## Do not claim", ""])
        for item in claims:
            lines.append(f"- {item}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
