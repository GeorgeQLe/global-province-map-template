"""Deterministic SVG review sheets for start-date reconstruction passes."""

from __future__ import annotations

import hashlib
import html
import json
import math
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


MAIN_W, MAIN_H = 1000.0, 740.0
COLUMN_W = 440.0
COLUMN_X = MAIN_W + 10.0
CANVAS_W = MAIN_W + 10.0 + COLUMN_W
INSET_W, INSET_H = COLUMN_W - 20.0, 210.0
KM_PER_DEGREE = 111.32
ADAPTIVE_FRAME_TRIGGER_RATIO = 12.0
ADAPTIVE_FRAME_PADDING_RATIO = 1.5
ADAPTIVE_FRAME_MINIMUM_SPAN = 0.25


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
    if manifest.get("schema_version") == "0.3.0":
        inventory = _artifact_json(root, artifacts, "anomaly_inventory")
        by_type: dict[str, list[dict[str, Any]]] = {}
        for anomaly in inventory.get("anomalies") or []:
            by_type.setdefault(str(anomaly.get("type")), []).append(anomaly)
        for anomaly_type, anomalies in sorted(by_type.items()):
            name = f"anomaly-{anomaly_type}.svg"
            path = out / name
            path.write_text(_render_anomaly_svg(manifest, anomaly_type, anomalies), encoding="utf-8")
            rendered.append({"region_id": f"anomaly:{anomaly_type}", "sheet_type": "anomaly", "path": name, "sha256": _sha256(path)})
    review_manifest = {
        "schema_version": manifest.get("schema_version", "0.2.0"),
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


def _render_anomaly_svg(manifest: dict[str, Any], anomaly_type: str, anomalies: list[dict[str, Any]]) -> str:
    rows = "".join(
        f'<text x="36" y="{112 + index * 24}">{html.escape(str(item["anomaly_id"]))} · {html.escape(str(item["resolution"]))}</text>'
        for index, item in enumerate(anomalies)
    )
    height = max(180, 140 + len(anomalies) * 24)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="900" height="{height}" viewBox="0 0 900 {height}">'
        '<rect width="100%" height="100%" fill="#fff"/>'
        f'<text x="36" y="48" font-size="24">M25C anomaly review · {html.escape(anomaly_type)}</text>'
        f'<text x="36" y="78">{html.escape(manifest["pass_id"])} · {html.escape(manifest["start_date"])}</text>'
        f'{rows}</svg>\n'
    )


class _Panel:
    """Equirectangular projection of a geographic frame onto a pixel rectangle."""

    def __init__(self, frame: tuple[float, float, float, float], rect: tuple[float, float, float, float]):
        minx, miny, maxx, maxy = frame
        self.px, self.py, self.pw, self.ph = rect
        self.scale = min(self.pw / max(maxx - minx, 1e-12), self.ph / max(maxy - miny, 1e-12))
        # centre the frame inside the pixel rectangle
        self.ox = self.px + (self.pw - (maxx - minx) * self.scale) / 2.0
        self.oy = self.py + (self.ph - (maxy - miny) * self.scale) / 2.0
        self.minx, self.miny, self.maxy = minx, miny, maxy
        self.center_lat = (miny + maxy) / 2.0
        self.geo_frame = frame

    def point(self, coord: tuple[float, float]) -> str:
        x = self.ox + (coord[0] - self.minx) * self.scale
        y = self.oy + (self.maxy - coord[1]) * self.scale
        return f"{x:.3f},{y:.3f}"

    def xy(self, coord: tuple[float, float]) -> tuple[float, float]:
        x = self.ox + (coord[0] - self.minx) * self.scale
        y = self.oy + (self.maxy - coord[1]) * self.scale
        return x, y

    def paths(self, geometry: Any) -> list[str]:
        if geometry.geom_type == "Polygon":
            rings = [geometry.exterior, *geometry.interiors]
            return ["M " + " L ".join(self.point(tuple(coord)) for coord in ring.coords) + " Z" for ring in rings]
        if geometry.geom_type == "MultiPolygon":
            return [item for polygon in geometry.geoms for item in self.paths(polygon)]
        if geometry.geom_type == "LineString":
            return ["M " + " L ".join(self.point(tuple(coord)) for coord in geometry.coords)]
        if geometry.geom_type == "MultiLineString":
            return [item for line in geometry.geoms for item in self.paths(line)]
        if geometry.geom_type == "Point":
            x, y = self.point((geometry.x, geometry.y)).split(",")
            return [f"M {x},{y} m -3,0 a 3,3 0 1,0 6,0 a 3,3 0 1,0 -6,0"]
        return []

    def intersects(self, bounds: tuple[float, float, float, float]) -> bool:
        fminx, fminy, fmaxx, fmaxy = self.geo_frame
        return not (bounds[2] < fminx or bounds[0] > fmaxx or bounds[3] < fminy or bounds[1] > fmaxy)

    def scale_bar(self) -> str:
        """Approximate scale bar anchored at the panel's lower-left corner."""
        km_per_px = KM_PER_DEGREE * max(math.cos(math.radians(self.center_lat)), 0.05) / self.scale
        bar_km = 1.0
        for candidate in (1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000):
            bar_km = float(candidate)
            if bar_km / km_per_px >= 60.0:
                break
        bar_px = bar_km / km_per_px
        x, y = self.px + 12.0, self.py + self.ph - 12.0
        label = f"≈{bar_km:g} km"
        return (
            f'<g class="scale-bar"><line x1="{x:.1f}" y1="{y:.1f}" x2="{x + bar_px:.1f}" y2="{y:.1f}"/>'
            f'<line x1="{x:.1f}" y1="{y - 4:.1f}" x2="{x:.1f}" y2="{y + 4:.1f}"/>'
            f'<line x1="{x + bar_px:.1f}" y1="{y - 4:.1f}" x2="{x + bar_px:.1f}" y2="{y + 4:.1f}"/>'
            f'<text x="{x + bar_px / 2:.1f}" y="{y - 6:.1f}" text-anchor="middle">{html.escape(label)}</text></g>'
        )


def _pad_frame(bounds: tuple[float, float, float, float], ratio: float, minimum_span: float) -> tuple[float, float, float, float]:
    minx, miny, maxx, maxy = bounds
    span = max(maxx - minx, maxy - miny, minimum_span)
    pad = span * ratio
    cx, cy = (minx + maxx) / 2.0, (miny + maxy) / 2.0
    half = span / 2.0 + pad
    return (cx - half, cy - half, cx + half, cy + half)


def _merge_bounds(all_bounds: list[tuple[float, float, float, float]]) -> tuple[float, float, float, float]:
    return (
        min(b[0] for b in all_bounds), min(b[1] for b in all_bounds),
        max(b[2] for b in all_bounds), max(b[3] for b in all_bounds),
    )


def _maximum_span(bounds: tuple[float, float, float, float]) -> float:
    return max(bounds[2] - bounds[0], bounds[3] - bounds[1])


def _main_frame(
    province_bounds: list[tuple[float, float, float, float]],
    constraint_bounds: list[tuple[float, float, float, float]],
    evidence_bounds: list[tuple[float, float, float, float]],
) -> tuple[float, float, float, float]:
    """Choose the main review frame without allowing modern controls to affect it.

    The ordinary frame preserves the historical behaviour: it covers assigned
    provinces and historical evidence with five percent padding. When assigned
    province geometry is an extreme outlier relative to the evidence footprint,
    use a broader evidence-centred square instead.
    """
    if not province_bounds and not constraint_bounds:
        raise StartDateRenderError("Cannot frame a region without provinces or historical evidence.")

    if province_bounds and evidence_bounds:
        province_span = _maximum_span(_merge_bounds(province_bounds))
        evidence_envelope = _merge_bounds(evidence_bounds)
        evidence_span = max(_maximum_span(evidence_envelope), 1e-12)
        if province_span > ADAPTIVE_FRAME_TRIGGER_RATIO * evidence_span:
            return _pad_frame(
                evidence_envelope,
                ADAPTIVE_FRAME_PADDING_RATIO,
                ADAPTIVE_FRAME_MINIMUM_SPAN,
            )

    # Control points belong to the trigger envelope, but keeping them out of
    # the ordinary frame preserves the renderer's historical framing exactly.
    ordinary_bounds = _merge_bounds([*province_bounds, *constraint_bounds])
    pad = max(_maximum_span(ordinary_bounds), 1e-9) * 0.05
    return (
        ordinary_bounds[0] - pad,
        ordinary_bounds[1] - pad,
        ordinary_bounds[2] + pad,
        ordinary_bounds[3] + pad,
    )


def _feature_css(props: dict[str, Any]) -> str:
    if str(props.get("feature_id", "")).startswith("forbidden-modern-"):
        return "forbidden-modern"
    return str(props.get("classification", "soft_evidence")).replace("_", "-")


def _control_points(props: dict[str, Any]) -> list[dict[str, Any]]:
    georeferencing = props.get("georeferencing")
    if not isinstance(georeferencing, dict):
        return []
    points = georeferencing.get("control_points")
    if not isinstance(points, list):
        return []
    return [
        point for point in points
        if isinstance(point, dict)
        and isinstance(point.get("lon"), (int, float)) and isinstance(point.get("lat"), (int, float))
    ]


def _historical_evidence_bounds(
    boundary_records: list[dict[str, Any]],
) -> list[tuple[float, float, float, float]]:
    """Return constraint and control-point bounds, excluding modern controls."""
    bounds: list[tuple[float, float, float, float]] = []
    for record in boundary_records:
        if record["css"] == "forbidden-modern":
            continue
        bounds.append(record["bounds"])
        bounds.extend(
            (float(point["lon"]), float(point["lat"]), float(point["lon"]), float(point["lat"]))
            for point in _control_points(record["props"])
        )
    return bounds


def _draw_provinces(body: list[str], panel: _Panel, province_records: list[dict[str, Any]], *, with_ids: bool) -> None:
    for record in province_records:
        if not panel.intersects(record["bounds"]):
            continue
        paths = panel.paths(record["geometry"])
        for index, path in enumerate(paths):
            if with_ids:
                suffix = "" if len(paths) == 1 else f"-part{index + 1}"
                identity = f'id="{html.escape(record["feature_id"])}{suffix}" '
            else:
                identity = ""
            body.append(f'<path class="province" {identity}{record["attrs"]} d="{path}"/>')


def _draw_boundary(body: list[str], panel: _Panel, record: dict[str, Any], *, with_ids: bool) -> None:
    paths = panel.paths(record["geometry"])
    for index, path in enumerate(paths):
        if with_ids:
            suffix = "" if len(paths) == 1 else f"-part{index + 1}"
            identity = f'id="{html.escape(record["feature_id"])}{suffix}" '
        else:
            identity = ""
        body.append(f'<path class="constraint {record["css"]}" {identity}d="{path}"/>')


def _draw_control_points(body: list[str], panel: _Panel, props: dict[str, Any]) -> None:
    for index, point in enumerate(_control_points(props)):
        x, y = panel.xy((float(point["lon"]), float(point["lat"])))
        if not (panel.px <= x <= panel.px + panel.pw and panel.py <= y <= panel.py + panel.ph):
            continue
        name = str(point.get("name") or point.get("id") or "control point")
        residual = point.get("residual_km")
        label = name if not isinstance(residual, (int, float)) else f"{name} ({residual:g} km)"
        # keep labels inside the panel and stagger them so close-by points stay legible
        if x > panel.px + panel.pw / 2.0:
            anchor, tx = "end", x - 6.0
        else:
            anchor, tx = "start", x + 6.0
        ty = y - 5.0 if index % 2 == 0 else y + 12.0
        body.append(
            f'<g class="control-point"><circle cx="{x:.1f}" cy="{y:.1f}" r="3.2"/>'
            f'<text x="{tx:.1f}" y="{ty:.1f}" text-anchor="{anchor}">{html.escape(label)}</text></g>'
        )


def _legend(x: float, y: float) -> str:
    rows = [
        ('<rect x="{x}" y="{cy}" width="18" height="10" class="legend-province"/>', "province (fill = owner colour, opacity = 1 − uncertainty)"),
        ('<line x1="{x}" y1="{my}" x2="{x2}" y2="{my}" class="constraint hard-constraint"/>', "hard constraint (certified frontier sub-segment)"),
        ('<line x1="{x}" y1="{my}" x2="{x2}" y2="{my}" class="constraint soft-evidence"/>', "soft evidence"),
        ('<line x1="{x}" y1="{my}" x2="{x2}" y2="{my}" class="constraint forbidden-modern"/>', "forbidden modern outline (negative control; excluded from framing)"),
        ('<g class="control-point"><circle cx="{mx}" cy="{my}" r="3.2"/></g>', "georeferencing control point (name, residual km)"),
        ('<rect x="{x}" y="{cy}" width="18" height="10" class="focus-box"/>', "inset frame on the main map"),
    ]
    parts = [f'<text x="{x:.1f}" y="{y:.1f}" class="panel-title">Legend</text>']
    for index, (swatch, text) in enumerate(rows):
        cy = y + 10.0 + index * 17.0
        parts.append(swatch.format(x=f"{x:.1f}", x2=f"{x + 18:.1f}", cy=f"{cy:.1f}", mx=f"{x + 9:.1f}", my=f"{cy + 5:.1f}"))
        parts.append(f'<text x="{x + 24:.1f}" y="{cy + 9:.1f}">{html.escape(text)}</text>')
    return "".join(parts)


def _inset_caption(label: str, record: dict[str, Any]) -> list[str]:
    props = record["props"]
    if record["css"] == "forbidden-modern":
        return [f"Inset {label} — {record['feature_id']}", "negative control: modern outline vs 1444 provinces"]
    lines = [f"Inset {label} — {record['feature_id']} ({record['css'].replace('-', ' ')})"]
    georeferencing = props.get("georeferencing")
    if isinstance(georeferencing, dict):
        residual = georeferencing.get("residual_error_km")
        budget = props.get("error_budget_km")
        detail = f"{georeferencing.get('transform_method', '?')} @ {georeferencing.get('crs', '?')}"
        if isinstance(residual, (int, float)):
            detail += f"; max residual {residual:g} km"
            if isinstance(budget, (int, float)):
                detail += f" ≤ budget {budget:g} km"
        lines.append(detail)
    return lines


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
    if not province_features and not scoped_boundaries:
        province_features = [
            feature for feature in build.get("features", [])
            if (feature.get("properties") or {}).get("feature_id")
        ]
    province_records = []
    for feature in sorted(province_features, key=lambda row: row["properties"]["feature_id"]):
        if not feature.get("geometry"):
            continue
        fid = feature["properties"]["feature_id"]
        assignment = province_assignments.get(fid, {})
        owner = assignment.get("owner_polity_id") or ((assignment.get("polity_ids") or ["unassigned"])[0])
        hierarchy = assignment.get("hierarchy") or {}
        uncertainty = float(assignment.get("uncertainty", 1.0))
        color = "#" + hashlib.sha256(str(owner).encode()).hexdigest()[:6]
        geometry = shape(feature["geometry"])
        province_records.append({
            "feature_id": fid,
            "geometry": geometry,
            "bounds": geometry.bounds,
            "attrs": (
                f'data-owner="{html.escape(str(owner))}" data-area="{html.escape(str(hierarchy.get("area_id", "unmapped")))}" '
                f'data-uncertainty="{uncertainty:.3f}" fill="{color}" fill-opacity="{max(0.2, 1.0 - uncertainty):.3f}"'
            ),
        })
    boundary_records = []
    for feature in sorted(scoped_boundaries, key=lambda row: row["properties"]["feature_id"]):
        if not feature.get("geometry"):
            continue
        props = feature["properties"]
        geometry = shape(feature["geometry"])
        boundary_records.append({
            "feature_id": props["feature_id"],
            "props": props,
            "geometry": geometry,
            "bounds": geometry.bounds,
            "css": _feature_css(props),
        })
    if not province_records and not boundary_records:
        raise StartDateRenderError(f"Region {region} has no renderable geometry.")

    # Main framing normally covers all assigned provinces and historical
    # evidence. If province geometry is an extreme outlier, frame a padded
    # evidence envelope instead. Forbidden-modern negative controls never
    # contribute to either calculation.
    province_bounds = [record["bounds"] for record in province_records]
    constraint_bounds = [
        record["bounds"] for record in boundary_records
        if record["css"] != "forbidden-modern"
    ]
    evidence_bounds = _historical_evidence_bounds(boundary_records)
    frame = _main_frame(province_bounds, constraint_bounds, evidence_bounds)
    main = _Panel(frame, (0.0, 0.0, MAIN_W, MAIN_H))

    # One focus inset per historical constraint (framed on the constraint and
    # its control points), then one negative-control inset per forbidden outline.
    inset_records = (
        [record for record in boundary_records if record["css"] != "forbidden-modern"]
        + [record for record in boundary_records if record["css"] == "forbidden-modern"]
    )
    legend_height = 130.0
    caption_height = 34.0
    inset_stride = INSET_H + caption_height + 14.0
    canvas_h = max(MAIN_H, 40.0 + legend_height + len(inset_records) * inset_stride)

    body: list[str] = []
    body.append(f'<rect width="{CANVAS_W:g}" height="{canvas_h:g}" fill="#ffffff"/>')
    body.append(f'<rect width="{MAIN_W:g}" height="{canvas_h:g}" fill="#f7f3e8"/>')
    title = html.escape(f'{manifest["pass_id"]} — {region}')
    body.append(f'<text x="35" y="25" class="sheet-title">{title}</text>')

    body.append(f'<g clip-path="url(#clip-main)">')
    _draw_provinces(body, main, province_records, with_ids=True)
    for record in boundary_records:
        if not main.intersects(record["bounds"]):
            continue
        _draw_boundary(body, main, record, with_ids=True)
    body.append("</g>")
    body.append(main.scale_bar())

    clip_defs = [f'<clipPath id="clip-main"><rect x="0" y="0" width="{MAIN_W:g}" height="{canvas_h:g}"/></clipPath>']
    legend_x = COLUMN_X + 10.0
    body.append(_legend(legend_x, 30.0))

    labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for index, record in enumerate(inset_records):
        label = labels[index % len(labels)]
        top = 40.0 + legend_height + index * inset_stride
        rect = (legend_x, top + caption_height, INSET_W, INSET_H)
        control_bounds = [record["bounds"]] + [
            (point["lon"], point["lat"], point["lon"], point["lat"])
            for point in _control_points(record["props"])
        ]
        pad_ratio = 0.15 if record["css"] == "forbidden-modern" else 0.45
        inset_frame = _pad_frame(_merge_bounds(control_bounds), pad_ratio, 0.02)
        panel = _Panel(inset_frame, rect)
        clip_defs.append(
            f'<clipPath id="clip-inset-{label}"><rect x="{rect[0]:.1f}" y="{rect[1]:.1f}" width="{rect[2]:.1f}" height="{rect[3]:.1f}"/></clipPath>'
        )
        for line_index, caption in enumerate(_inset_caption(label, record)):
            body.append(f'<text x="{legend_x:.1f}" y="{top + 12 + line_index * 14:.1f}" class="panel-title">{html.escape(caption)}</text>')
        body.append(f'<rect x="{rect[0]:.1f}" y="{rect[1]:.1f}" width="{rect[2]:.1f}" height="{rect[3]:.1f}" class="inset-frame"/>')
        body.append(f'<g clip-path="url(#clip-inset-{label})">')
        _draw_provinces(body, panel, province_records, with_ids=False)
        _draw_boundary(body, panel, record, with_ids=False)
        body.append("</g>")
        _draw_control_points(body, panel, record["props"])
        body.append(panel.scale_bar())
        # focus box on the main map marking this inset's geographic frame
        fx0, fy0 = main.xy((inset_frame[0], inset_frame[3]))
        fx1, fy1 = main.xy((inset_frame[2], inset_frame[1]))
        fx0, fy0 = max(fx0, 1.0), max(fy0, 1.0)
        fx1, fy1 = min(fx1, MAIN_W - 1.0), min(fy1, canvas_h - 1.0)
        if fx1 > fx0 and fy1 > fy0:
            body.append(f'<rect x="{fx0:.1f}" y="{fy0:.1f}" width="{fx1 - fx0:.1f}" height="{fy1 - fy0:.1f}" class="focus-box"/>')
            body.append(f'<text x="{fx0 + 3:.1f}" y="{fy0 + 13:.1f}" class="focus-label">{label}</text>')

    style = (
        "text{font-family:sans-serif;font-size:10px;fill:#333}"
        ".sheet-title{font-size:16px;fill:#111}"
        ".panel-title{font-size:11px;font-weight:bold;fill:#111}"
        ".province{stroke:#222;stroke-width:.7;vector-effect:non-scaling-stroke}"
        ".constraint{fill:none;stroke-width:3;vector-effect:non-scaling-stroke}"
        ".hard-constraint{stroke:#111}"
        ".soft-evidence{stroke:#d28b00;stroke-dasharray:7 5}"
        ".forbidden-modern{stroke:#d00000;stroke-dasharray:2 4}"
        ".legend-province{fill:#8faf6f;fill-opacity:.75;stroke:#222;stroke-width:.7}"
        ".inset-frame{fill:#fdfcf7;stroke:#888;stroke-width:1}"
        ".focus-box{fill:none;stroke:#0050c8;stroke-width:1.2;stroke-dasharray:5 3}"
        ".focus-label{fill:#0050c8;font-weight:bold;font-size:11px}"
        ".control-point circle{fill:#0050c8;stroke:#fff;stroke-width:1}"
        ".control-point text{fill:#0050c8}"
        ".scale-bar line{stroke:#111;stroke-width:1.5}"
        ".scale-bar text{fill:#111}"
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W:g}" height="{canvas_h:g}" viewBox="0 0 {CANVAS_W:g} {canvas_h:g}">\n'
        f'<title>{title}</title><desc>Deterministic M25 review: provinces, ownership, hierarchy, uncertainty, historical constraints with '
        'georeferencing control points and residuals, focus insets, and forbidden modern outlines as negative controls.</desc>\n'
        f"<style>{style}</style>\n<defs>{''.join(clip_defs)}</defs>\n"
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
