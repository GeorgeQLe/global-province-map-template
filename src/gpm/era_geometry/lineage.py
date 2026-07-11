"""ID lineage maps between scaffold and era-aware province IDs (M15)."""

from __future__ import annotations

from typing import Any


def build_lineage_document(
    *,
    pack_id: str,
    era: str,
    scenario_id: str | None,
    rows: list[dict[str, Any]],
    notes: list[str] | None = None,
) -> dict[str, Any]:
    """Build a machine-readable lineage map document."""
    normalized: list[dict[str, Any]] = []
    for row in rows:
        entry = {
            "era_province_id": str(row["era_province_id"]),
            "scaffold_province_id": str(row["scaffold_province_id"]),
            "operation": str(row["operation"]),
        }
        if row.get("display_name"):
            entry["display_name"] = str(row["display_name"])
        if row.get("reason"):
            entry["reason"] = str(row["reason"])
        if row.get("part_index") is not None:
            entry["part_index"] = int(row["part_index"])
        if row.get("part_count") is not None:
            entry["part_count"] = int(row["part_count"])
        if row.get("in_priority_region") is not None:
            entry["in_priority_region"] = bool(row["in_priority_region"])
        if row.get("geometry_mode"):
            entry["geometry_mode"] = str(row["geometry_mode"])
        normalized.append(entry)

    # Stable order: scaffold id, then era id.
    normalized.sort(
        key=lambda item: (item["scaffold_province_id"], item["era_province_id"])
    )

    return {
        "schema_version": "0.1.0",
        "document_type": "era-geometry-lineage",
        "milestone": "M15",
        "pack_id": pack_id,
        "era": era,
        "scenario_id": scenario_id,
        "row_count": len(normalized),
        "rows": normalized,
        "notes": list(notes or []),
    }


def lineage_csv_rows(document: dict[str, Any]) -> list[dict[str, str]]:
    """Flatten lineage rows for CSV export."""
    rows: list[dict[str, str]] = []
    for row in document.get("rows") or []:
        rows.append(
            {
                "era_province_id": str(row.get("era_province_id") or ""),
                "scaffold_province_id": str(row.get("scaffold_province_id") or ""),
                "operation": str(row.get("operation") or ""),
                "display_name": str(row.get("display_name") or ""),
                "part_index": (
                    str(row["part_index"]) if row.get("part_index") is not None else ""
                ),
                "part_count": (
                    str(row["part_count"]) if row.get("part_count") is not None else ""
                ),
                "in_priority_region": (
                    "true"
                    if row.get("in_priority_region") is True
                    else "false"
                    if row.get("in_priority_region") is False
                    else ""
                ),
                "geometry_mode": str(row.get("geometry_mode") or ""),
                "reason": str(row.get("reason") or ""),
            }
        )
    return rows


LINEAGE_CSV_COLUMNS = (
    "era_province_id",
    "scaffold_province_id",
    "operation",
    "display_name",
    "part_index",
    "part_count",
    "in_priority_region",
    "geometry_mode",
    "reason",
)
