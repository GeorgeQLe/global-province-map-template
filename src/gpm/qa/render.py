"""Deterministic SVG review sheets for start-date reconstruction passes."""

from __future__ import annotations

import hashlib
import html
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from shapely.geometry import shape


class StartDateRenderError(RuntimeError):
    """Raised when review sheets cannot be produced."""


@dataclass(frozen=True)
class StartDateRenderResult:
    pass_id: str
    region_count: int
    output_dir: str
    manifest_output: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def render_start_date_pass(*, pass_dir: Path, output_dir: Path) -> StartDateRenderResult:
    root = Path(pass_dir).resolve()
    out = Path(output_dir)
    manifest = _json(root / "pass_manifest.json")
    artifacts = manifest.get("artifacts") or {}
    build = _artifact_json(root, artifacts, "full_build_geometry")
    boundaries = _artifact_json(root, artifacts, "boundary_registry")
    assignments = _artifact_json(root, artifacts, "location_assignments")
    regions = list((manifest.get("scope") or {}).get("priority_regions") or [])
    if not regions:
        raise StartDateRenderError("Pass manifest has no priority regions.")

    out.mkdir(parents=True, exist_ok=True)
    rendered: list[dict[str, str]] = []
    for region in regions:
        name = f"{region}.svg"
        payload = _render_svg(manifest, region, build, boundaries, assignments)
        path = out / name
        path.write_text(payload, encoding="utf-8")
        rendered.append({"region_id": region, "path": name, "sha256": _sha256(path)})
    review_manifest = {
        "schema_version": "0.2.0",
        "document_type": "start_date_review_manifest",
        "pass_id": manifest["pass_id"],
        "geometry_revision": manifest["geometry_revision"],
        "generated_at": manifest["generated_at"],
        "generator": "gpm qa render",
        "reviewer": None,
        "reviewed_at": None,
        "status": "pending_independent_review",
        "renders": rendered,
    }
    manifest_path = out / "review_manifest.json"
    manifest_path.write_text(json.dumps(review_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return StartDateRenderResult(manifest["pass_id"], len(rendered), str(out), str(manifest_path))


def _render_svg(
    manifest: dict[str, Any], region: str, build: dict[str, Any],
    boundaries: dict[str, Any], assignments: dict[str, Any],
) -> str:
    province_assignments = {
        row["province_id"]: row for row in assignments.get("assignments", [])
        if not row.get("region_id") or row.get("region_id") == region
    }
    province_features = [
        feature for feature in build.get("features", [])
        if (feature.get("properties") or {}).get("feature_type") == "province"
        and (not province_assignments or (feature.get("properties") or {}).get("feature_id") in province_assignments)
    ]
    scoped_boundaries = [
        feature for feature in boundaries.get("features", [])
        if (feature.get("properties") or {}).get("geographic_scope") == region
    ]
    visible = province_features + scoped_boundaries
    if not visible:
        visible = list(build.get("features", []))
    geoms = [shape(feature["geometry"]) for feature in visible if feature.get("geometry")]
    if not geoms:
        raise StartDateRenderError(f"Region {region} has no renderable geometry.")
    minx = min(geom.bounds[0] for geom in geoms); miny = min(geom.bounds[1] for geom in geoms)
    maxx = max(geom.bounds[2] for geom in geoms); maxy = max(geom.bounds[3] for geom in geoms)
    width, height, pad = 1000.0, 700.0, 35.0
    sx = (width - 2 * pad) / max(maxx - minx, 1e-12)
    sy = (height - 2 * pad) / max(maxy - miny, 1e-12)
    scale = min(sx, sy)

    def point(coord: tuple[float, float]) -> str:
        x = pad + (coord[0] - minx) * scale
        y = height - pad - (coord[1] - miny) * scale
        return f"{x:.3f},{y:.3f}"

    def paths(geometry: Any) -> list[str]:
        if geometry.geom_type == "Polygon":
            rings = [geometry.exterior, *geometry.interiors]
            return ["M " + " L ".join(point(tuple(coord)) for coord in ring.coords) + " Z" for ring in rings]
        if geometry.geom_type == "MultiPolygon":
            return [item for polygon in geometry.geoms for item in paths(polygon)]
        if geometry.geom_type == "LineString":
            return ["M " + " L ".join(point(tuple(coord)) for coord in geometry.coords)]
        if geometry.geom_type == "MultiLineString":
            return [item for line in geometry.geoms for item in paths(line)]
        if geometry.geom_type == "Point":
            x, y = point((geometry.x, geometry.y)).split(",")
            return [f"M {x},{y} m -3,0 a 3,3 0 1,0 6,0 a 3,3 0 1,0 -6,0"]
        return []

    body: list[str] = []
    for feature in sorted(province_features, key=lambda row: row["properties"]["feature_id"]):
        fid = feature["properties"]["feature_id"]
        assignment = province_assignments.get(fid, {})
        owner = assignment.get("owner_polity_id") or ((assignment.get("polity_ids") or ["unassigned"])[0])
        hierarchy = assignment.get("hierarchy") or {}
        uncertainty = float(assignment.get("uncertainty", 1.0))
        color = "#" + hashlib.sha256(str(owner).encode()).hexdigest()[:6]
        attrs = (
            f'data-owner="{html.escape(str(owner))}" data-area="{html.escape(str(hierarchy.get("area_id", "unmapped")))}" '
            f'data-uncertainty="{uncertainty:.3f}" fill="{color}" fill-opacity="{max(0.2, 1.0-uncertainty):.3f}"'
        )
        for path in paths(shape(feature["geometry"])):
            body.append(f'<path class="province" id="{html.escape(fid)}" {attrs} d="{path}"/>')
    for feature in sorted(scoped_boundaries, key=lambda row: row["properties"]["feature_id"]):
        props = feature["properties"]
        css = "forbidden-modern" if props["feature_id"].startswith("forbidden-modern-") else props["classification"].replace("_", "-")
        for path in paths(shape(feature["geometry"])):
            body.append(f'<path class="constraint {css}" id="{html.escape(props["feature_id"])}" d="{path}"/>')
    title = html.escape(f'{manifest["pass_id"]} — {region}')
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="740" viewBox="0 0 1000 740">\n'
        f'<title>{title}</title><desc>Deterministic M25 review: provinces, ownership, hierarchy, uncertainty, historical constraints, and forbidden modern outlines.</desc>\n'
        '<style>.province{stroke:#222;stroke-width:.7;vector-effect:non-scaling-stroke}.constraint{fill:none;stroke-width:3;vector-effect:non-scaling-stroke}.hard-constraint{stroke:#111}.soft-evidence{stroke:#d28b00;stroke-dasharray:7 5}.forbidden-modern{stroke:#d00000;stroke-dasharray:2 4}</style>\n'
        f'<rect width="1000" height="740" fill="#f7f3e8"/><text x="35" y="25" font-family="sans-serif" font-size="16">{title}</text>\n'
        + "\n".join(body) + "\n</svg>\n"
    )


def _artifact_json(root: Path, artifacts: dict[str, Any], role: str) -> dict[str, Any]:
    record = artifacts.get(role)
    if not isinstance(record, dict) or not isinstance(record.get("path"), str):
        raise StartDateRenderError(f"Pass manifest does not pin {role}.")
    return _json(root / record["path"])


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StartDateRenderError(f"Cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise StartDateRenderError(f"Expected a JSON object: {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
