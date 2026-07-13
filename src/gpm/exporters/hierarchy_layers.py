"""Export slim hierarchy overlay layers (areas / regions / superregions).

Reads the M21 ``hierarchy.geojson`` build artifact and writes one simplified
GeoJSON per level with lean properties, sized for direct use as demo overlay
sources (border lines + label points). Heavy membership lists stay in the
build artifact; these layers only carry ids, names, parents, counts, a
precomputed ``label_point``, and a deterministic ``area_color``.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from shapely.errors import ShapelyError
from shapely.geometry import mapping, shape

from gpm import __version__
from gpm.exporters.atlas import tag_fill_color
from gpm.exporters.pack import ExportError
from gpm.paths import PROCESSED_DATA_DIR

HIERARCHY_LAYER_FILES = {
    "area": "areas.geojson",
    "region": "regions.geojson",
    "superregion": "superregions.geojson",
}
# ~2 km at the equator; hierarchy borders render at 0.6–2.8 px so heavy
# simplification keeps the overlay files small without visible artifacts.
# Coarser levels tolerate coarser geometry (they render thicker and larger).
DEFAULT_SIMPLIFY_TOLERANCE_DEG = 0.02
LEVEL_TOLERANCE_MULTIPLIER = {"area": 1.0, "region": 2.0, "superregion": 4.0}
# 4 decimal places ≈ 11 m — far below one pixel at overlay zooms.
COORDINATE_PRECISION = 4


@dataclass(frozen=True)
class HierarchyLayersResult:
    hierarchy_input: str
    output_dir: str
    simplify_tolerance_deg: float
    area_count: int
    region_count: int
    superregion_count: int
    files_written: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def export_hierarchy_layers(
    hierarchy_input: Path = PROCESSED_DATA_DIR / "hierarchy.geojson",
    output_dir: Path | None = None,
    *,
    simplify_tolerance_deg: float = DEFAULT_SIMPLIFY_TOLERANCE_DEG,
) -> HierarchyLayersResult:
    """Write areas.geojson / regions.geojson / superregions.geojson overlays."""
    hierarchy_input = Path(hierarchy_input)
    if not hierarchy_input.is_file():
        raise ExportError(f"Hierarchy input does not exist: {hierarchy_input}")
    try:
        document = json.loads(hierarchy_input.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ExportError(f"Cannot read hierarchy GeoJSON {hierarchy_input}: {exc}") from exc
    if not isinstance(document, dict) or document.get("type") != "FeatureCollection":
        raise ExportError(f"Hierarchy input must be a GeoJSON FeatureCollection: {hierarchy_input}")

    output_dir = Path(output_dir) if output_dir is not None else hierarchy_input.parent / "hierarchy_layers"
    output_dir.mkdir(parents=True, exist_ok=True)

    by_level: dict[str, list[dict[str, Any]]] = {level: [] for level in HIERARCHY_LAYER_FILES}
    for feature in document.get("features") or []:
        if not isinstance(feature, dict):
            continue
        properties = feature.get("properties")
        if not isinstance(properties, dict):
            continue
        level = properties.get("region_type")
        if level not in by_level:
            continue
        by_level[level].append(_slim_feature(feature, properties, level, simplify_tolerance_deg))

    generated_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    files_written: list[str] = []
    for level, filename in HIERARCHY_LAYER_FILES.items():
        features = sorted(by_level[level], key=lambda f: f["properties"]["region_id"])
        path = output_dir / filename
        payload = {
            "type": "FeatureCollection",
            "name": f"hierarchy_{level}s",
            "gpm": {
                "schema_version": "0.1.0",
                "milestone": "M21",
                "layer": f"hierarchy_{level}s",
                "generated_at": generated_at,
                "generator_version": __version__,
                "simplify_tolerance_deg": simplify_tolerance_deg,
                "feature_count": len(features),
                "source_path": str(hierarchy_input),
            },
            "features": features,
        }
        path.write_text(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        files_written.append(filename)

    return HierarchyLayersResult(
        hierarchy_input=str(hierarchy_input),
        output_dir=str(output_dir),
        simplify_tolerance_deg=simplify_tolerance_deg,
        area_count=len(by_level["area"]),
        region_count=len(by_level["region"]),
        superregion_count=len(by_level["superregion"]),
        files_written=tuple(files_written),
    )


def _slim_feature(
    feature: dict[str, Any],
    properties: dict[str, Any],
    level: str,
    simplify_tolerance_deg: float,
) -> dict[str, Any]:
    region_id = str(properties.get("region_id") or "")
    slim: dict[str, Any] = {
        "region_id": region_id,
        "display_name": properties.get("display_name") or region_id,
        "region_type": level,
        "parent_country_id": properties.get("parent_country_id"),
        "parent_region_id": properties.get("parent_region_id"),
        "parent_superregion_id": properties.get("parent_superregion_id"),
        "province_count": properties.get("province_count"),
        "label_point": properties.get("label_point"),
    }
    if level == "area":
        slim["area_color"] = tag_fill_color(region_id)
    geometry = feature.get("geometry")
    if geometry is not None and simplify_tolerance_deg > 0:
        tolerance = simplify_tolerance_deg * LEVEL_TOLERANCE_MULTIPLIER.get(level, 1.0)
        try:
            geom = shape(geometry)
            simplified = geom.simplify(tolerance, preserve_topology=True)
            if not simplified.is_empty:
                geometry = _round_coordinates(mapping(simplified))
        except (ShapelyError, TypeError, ValueError) as exc:
            raise ExportError(f"Cannot simplify hierarchy geometry for {region_id}: {exc}") from exc
    return {"type": "Feature", "geometry": geometry, "properties": slim}


def _round_coordinates(geometry: dict[str, Any]) -> dict[str, Any]:
    def visit(value: Any) -> Any:
        if isinstance(value, (list, tuple)):
            return [visit(item) for item in value]
        if isinstance(value, float):
            return round(value, COORDINATE_PRECISION)
        return value

    rounded = dict(geometry)
    if "coordinates" in rounded:
        rounded["coordinates"] = visit(rounded["coordinates"])
    return rounded
