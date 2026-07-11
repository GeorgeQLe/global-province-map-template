"""Sample subset extraction for commit-friendly alpha datasets."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


class SampleError(RuntimeError):
    """Raised when a sample subset cannot be produced."""


def filter_provinces_by_countries(
    features: list[dict[str, Any]],
    countries: set[str],
) -> list[dict[str, Any]]:
    """Keep land features whose parent_country_id is in *countries* (case-insensitive)."""
    wanted = {code.upper() for code in countries}
    selected: list[dict[str, Any]] = []
    for feature in features:
        properties = feature.get("properties") or {}
        if not isinstance(properties, dict):
            continue
        kind = properties.get("kind") or "land"
        if kind != "land":
            continue
        country = properties.get("parent_country_id")
        if isinstance(country, str) and country.strip().upper() in wanted:
            selected.append(feature)
    return selected


def filter_seas_for_land(
    sea_features: list[dict[str, Any]],
    land_ids: set[str],
) -> list[dict[str, Any]]:
    """Keep coastal seas linked to selected land, plus ocean cells that touch selected seas.

    For alpha samples we keep coastal seas whose parent land is selected. Ocean
    zones without a parent are dropped unless they share adjacency with kept
    seas (handled later when adjacency is filtered). This keeps samples small.
    """
    selected: list[dict[str, Any]] = []
    for feature in sea_features:
        properties = feature.get("properties") or {}
        if not isinstance(properties, dict):
            continue
        sea_class = properties.get("sea_class")
        parent = properties.get("parent_land_province_id")
        if sea_class == "coastal" and isinstance(parent, str) and parent in land_ids:
            selected.append(feature)
        elif sea_class == "ocean":
            # Ocean cells are large; omit from country samples by default.
            continue
        elif not sea_class and isinstance(parent, str) and parent in land_ids:
            selected.append(feature)
    return selected


def filter_adjacency(
    rows: list[dict[str, str]],
    keep_ids: set[str],
) -> list[dict[str, str]]:
    """Keep adjacency rows whose both endpoints are in *keep_ids*."""
    filtered: list[dict[str, str]] = []
    for row in rows:
        left = (row.get("from_province_id") or "").strip()
        right = (row.get("to_province_id") or "").strip()
        if left in keep_ids and right in keep_ids:
            filtered.append(row)
    return filtered


def write_feature_collection(
    path: Path,
    *,
    name: str,
    features: list[dict[str, Any]],
    gpm_meta: dict[str, Any],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    document = {
        "type": "FeatureCollection",
        "name": name,
        "gpm": gpm_meta,
        "features": features,
    }
    path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_adjacency_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "from_province_id",
        "to_province_id",
        "adjacency_type",
        "bidirectional",
        "crossing_type",
        "shared_border_km",
        "source_lineage",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def load_feature_collection(path: Path, label: str) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SampleError(f"Invalid {label} GeoJSON at {path}: {exc}") from exc
    except OSError as exc:
        raise SampleError(f"Unable to read {label} at {path}: {exc}") from exc
    if not isinstance(document, dict) or document.get("type") != "FeatureCollection":
        raise SampleError(f"{label} must be a GeoJSON FeatureCollection: {path}")
    features = document.get("features")
    if not isinstance(features, list):
        raise SampleError(f"{label} FeatureCollection is missing features: {path}")
    return document


def load_adjacency_csv(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(newline="", encoding="utf-8") as file:
            return list(csv.DictReader(file))
    except OSError as exc:
        raise SampleError(f"Unable to read adjacency CSV at {path}: {exc}") from exc
