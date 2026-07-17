from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from shapely.geometry import mapping, shape
from shapely.ops import unary_union
from shapely.strtree import STRtree

from gpm.geo.shapefile import read_zipped_shapefile
from gpm.schemas import (
    SchemaValidationError,
    validate_location_fabric_manifest,
    validate_location_lineage,
)


class FabricQAError(RuntimeError):
    """Raised when M23 fabric QA inputs are malformed."""


@dataclass(frozen=True)
class FabricQAResult:
    status: str
    location_count: int
    adjacency_count: int
    error_count: int
    warning_count: int
    report_output: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PaintabilityQAResult:
    status: str
    boundary_count: int
    crossing_count: int
    request_count: int
    report_output: str
    split_requests_output: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_fabric_qa(*, location_input: Path, adjacency_input: Path | None = None,
                  intersections_input: Path | None = None, lineage_input: Path | None = None,
                  manifest_input: Path | None = None, land_input: Path | None = None,
                  report_output: Path | None = None, tolerance: float = 1e-8) -> FabricQAResult:
    location_path = Path(location_input)
    collection = _read_json(location_path, "Location input")
    if collection.get("type") != "FeatureCollection" or not isinstance(collection.get("features"), list):
        raise FabricQAError("Location input must be a GeoJSON FeatureCollection.")
    features = collection["features"]
    findings: list[dict[str, Any]] = []
    ids: list[str] = []
    geoms = []
    for index, feature in enumerate(features):
        props = feature.get("properties") if isinstance(feature, dict) else None
        location_id = props.get("location_id") if isinstance(props, dict) else None
        if not isinstance(location_id, str) or not location_id:
            findings.append(_finding("missing_location_id", "error", f"Feature {index} has no location_id."))
            continue
        ids.append(location_id)
        try:
            geom = shape(feature["geometry"])
        except Exception as exc:
            findings.append(_finding("invalid_geometry", "error", f"{location_id}: {exc}", [location_id]))
            continue
        if geom.is_empty or not geom.is_valid or geom.area <= 0:
            findings.append(_finding("invalid_geometry", "error", f"{location_id} has invalid/empty geometry.", [location_id]))
        geoms.append((location_id, geom))
    duplicates = sorted(item for item, count in Counter(ids).items() if count > 1)
    if duplicates:
        findings.append(_finding("duplicate_location_ids", "error", "Duplicate location IDs.", duplicates))

    geometry_values = [item[1] for item in geoms]
    if geometry_values:
        tree = STRtree(geometry_values)
        overlaps: list[str] = []
        for left_index, (left_id, left) in enumerate(geoms):
            for raw_right in tree.query(left, predicate="intersects"):
                right_index = int(raw_right)
                if right_index <= left_index:
                    continue
                overlap = left.intersection(geometry_values[right_index]).area
                if overlap > tolerance:
                    overlaps.extend((left_id, geoms[right_index][0]))
        if overlaps:
            findings.append(_finding("location_overlaps", "error", "Location interiors overlap.", sorted(set(overlaps))))

    adjacency_path = Path(adjacency_input or location_path.with_name("location_adjacency.csv"))
    adjacency_rows = _required_csv(
        adjacency_path, "Adjacency",
        {"from_location_id", "to_location_id", "shared_border_km", "adjacency_type"}, findings,
    )
    known = set(ids)
    seen_edges: set[tuple[str, str]] = set()
    for row in adjacency_rows:
        left, right = row.get("from_location_id", ""), row.get("to_location_id", "")
        edge = tuple(sorted((left, right)))
        if not left or not right or left == right or left not in known or right not in known:
            findings.append(_finding("invalid_adjacency", "error", f"Invalid adjacency row: {left!r}, {right!r}."))
        elif edge in seen_edges:
            findings.append(_finding("duplicate_adjacency", "error", f"Duplicate adjacency: {edge}."))
        seen_edges.add(edge)

    intersections_path = Path(intersections_input or location_path.with_name("location_admin_intersections.csv"))
    intersection_rows = _required_csv(
        intersections_path, "Admin intersections",
        {"location_id", "reference_layer", "reference_id", "intersection_area_sq_km", "location_share"},
        findings,
    )
    shares: dict[tuple[str, str], float] = {}
    for row in intersection_rows:
        try:
            share = float(row.get("location_share") or 0)
        except ValueError:
            share = -1
        if share < 0 or share > 1 + 1e-6:
            findings.append(_finding("invalid_intersection_share", "error", f"Invalid share for {row.get('location_id')}."))
        key = (row.get("location_id", ""), row.get("reference_layer", ""))
        shares[key] = shares.get(key, 0.0) + max(share, 0.0)
    incomplete_by_layer: dict[str, list[str]] = {}
    for (location_id, layer), total in sorted(shares.items()):
        if abs(total - 1.0) > 2e-4:
            incomplete_by_layer.setdefault(layer, []).append(location_id)
    for layer, location_ids in sorted(incomplete_by_layer.items()):
        findings.append(_finding(
            f"{layer}_incomplete_reference_coverage", "warning",
            f"{len(location_ids)} locations have {layer} intersection shares outside tolerance; "
            "reference-layer coverage may be intentionally incomplete.",
            sorted(location_ids),
        ))

    lineage_path = Path(lineage_input or location_path.with_name("location_lineage.json"))
    lineage = _required_json(lineage_path, "Lineage", findings)
    manifest_path = Path(manifest_input or location_path.with_name("location_fabric_manifest.json"))
    manifest = _required_json(manifest_path, "Manifest", findings)
    if lineage:
        try:
            validate_location_lineage(lineage)
        except SchemaValidationError as exc:
            findings.append(_finding("malformed_lineage", "error", str(exc)))
    if manifest:
        try:
            validate_location_fabric_manifest(manifest)
        except SchemaValidationError as exc:
            findings.append(_finding("malformed_manifest", "error", str(exc)))
    if manifest:
        actual = (manifest.get("actual_location_count") if isinstance(manifest, dict) else None)
        if actual != len(features):
            findings.append(_finding("manifest_count_mismatch", "error", f"Manifest says {actual}; file has {len(features)} locations."))
        meta = collection.get("gpm") or {}
        for key in ("fabric_id", "fabric_revision", "geometry_revision"):
            if str(manifest.get(key)) != str(meta.get(key)):
                findings.append(_finding("manifest_revision_mismatch", "error", f"Manifest/location {key} mismatch."))
        for declared in manifest.get("files") or []:
            declared_path = _resolve_manifest_path(str(declared), manifest_path)
            if not declared_path.is_file():
                findings.append(_finding(
                    "manifest_declared_file_missing", "error",
                    f"Manifest-declared file not found: {declared_path}",
                ))
    if lineage and manifest:
        for key in ("fabric_id", "fabric_revision", "source_fabric_revision", "output_fabric_revision"):
            if str(lineage.get(key)) != str(manifest.get(key)):
                findings.append(_finding(
                    "lineage_revision_mismatch", "error",
                    f"Lineage and manifest {key} differ.",
                ))
    meta = collection.get("gpm") if isinstance(collection.get("gpm"), dict) else {}
    for location_id, _geom in geoms:
        feature = next((item for item in features if (item.get("properties") or {}).get("location_id") == location_id), None)
        props = (feature or {}).get("properties") or {}
        if str(props.get("fabric_revision")) != str(meta.get("fabric_revision")):
            findings.append(_finding(
                "location_revision_mismatch", "error",
                f"{location_id} revision differs from collection metadata.", [location_id],
            ))

    resolved_land = Path(land_input) if land_input is not None else _manifest_land_path(manifest, manifest_path)
    if resolved_land is None:
        findings.append(_finding("land_input_missing", "error", "Manifest does not declare a land input."))
    elif geometry_values:
        try:
            land = _load_land(resolved_land)
        except FabricQAError as exc:
            findings.append(_finding("malformed_land_input", "error", str(exc)))
            land = None
        if land is not None:
            fabric = unary_union(geometry_values)
            missing_area = land.difference(fabric.buffer(tolerance)).area
            outside_area = fabric.difference(land.buffer(tolerance)).area
            if missing_area > tolerance:
                findings.append(_finding("land_coverage_gap", "error", f"Uncovered planar land area: {missing_area:.12f}."))
            if outside_area > tolerance:
                findings.append(_finding("outside_land", "error", f"Fabric outside planar land area: {outside_area:.12f}."))

    errors = sum(item["severity"] == "error" for item in findings)
    warnings = sum(item["severity"] == "warning" for item in findings)
    status = "pass" if errors == 0 else "fail"
    report_path = Path(report_output or location_path.with_name("fabric_qa.json"))
    report = {
        "schema_version": "0.1.0",
        "report_type": "fabric_qa",
        "status": status,
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "inputs": {
            "locations": str(location_path), "adjacency": str(adjacency_path),
            "intersections": str(intersections_path), "lineage": str(lineage_path),
            "manifest": str(manifest_path), "land": None if resolved_land is None else str(resolved_land),
        },
        "summary": {"location_count": len(features), "adjacency_count": len(adjacency_rows), "error_count": errors, "warning_count": warnings},
        "findings": findings,
    }
    _write_json(report_path, report)
    return FabricQAResult(status, len(features), len(adjacency_rows), errors, warnings, str(report_path))


def run_paintability_qa(*, location_input: Path, boundary_input: Path,
                        report_output: Path | None = None, split_requests_output: Path | None = None,
                        affected_dates: tuple[str, ...] = (), confidence: str = "review-required",
                        source_lineage: tuple[str, ...] = (), license_lineage: tuple[str, ...] = (),
                        tolerance: float = 1e-8, generated_at: str | None = None) -> PaintabilityQAResult:
    locations = _read_json(Path(location_input), "Location input")
    boundaries = _read_json(Path(boundary_input), "Boundary input")
    if locations.get("type") != "FeatureCollection" or boundaries.get("type") != "FeatureCollection":
        raise FabricQAError("Location and boundary inputs must be GeoJSON FeatureCollections.")
    location_features = locations.get("features") or []
    location_geoms = [shape(item["geometry"]) for item in location_features]
    location_edges = unary_union([geom.boundary for geom in location_geoms])
    tree = STRtree(location_geoms)
    requests: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    fabric_revision = str((locations.get("gpm") or {}).get("fabric_revision") or "unknown")
    for index, feature in enumerate(boundaries.get("features") or [], start=1):
        boundary_id = str((feature.get("properties") or {}).get("boundary_id") or f"boundary_{index:05d}")
        geom = shape(feature["geometry"])
        line = geom.boundary if geom.geom_type in {"Polygon", "MultiPolygon"} else geom
        # Only edges within the line's neighborhood can affect the difference:
        # clip the global edge network before applying the tolerance buffer.
        # The clip window must exceed the tolerance or nearby edges outside the
        # envelope would be dropped and reported as false crossings.
        local_edges = location_edges.intersection(line.envelope.buffer(max(0.01, 2.0 * tolerance)))
        interior_crossing = line.difference(local_edges.buffer(tolerance))
        affected_ids = sorted({
            location_features[int(raw)]["properties"]["location_id"]
            for raw in tree.query(line, predicate="intersects")
            if not line.intersection(location_geoms[int(raw)]).difference(
                location_geoms[int(raw)].boundary.buffer(tolerance)
            ).is_empty
        })
        if interior_crossing.is_empty or interior_crossing.length <= tolerance or not affected_ids:
            continue
        request_id = f"paint_{boundary_id}_{index:05d}"
        findings.append(_finding("boundary_crosses_location", "error", f"Required boundary {boundary_id} crosses location interiors.", affected_ids))
        requests.append({
            "request_id": request_id,
            "operation": "split_by_boundary",
            "failed_paintability_test": boundary_id,
            "proposed_geometry": mapping(line),
            "sources": list(source_lineage) or [str(boundary_input)],
            "license_lineage": list(license_lineage) or ["REQUIRED: add boundary dataset license"],
            "confidence": confidence,
            "affected_dates": list(affected_dates),
            "target_fabric_revision": fabric_revision,
            "affected_location_ids": affected_ids,
        })
    status = "pass" if not requests else "fail"
    report_path = Path(report_output or Path(location_input).with_name("paintability_qa.json"))
    requests_path = Path(split_requests_output or Path(location_input).with_name("paintability_split_requests.json"))
    report = {
        "schema_version": "0.1.0", "report_type": "paintability_qa", "status": status,
        "generated_at": generated_at or datetime.now(UTC).replace(microsecond=0).isoformat(),
        "boundary_count": len(boundaries.get("features") or []), "crossing_count": len(requests),
        "findings": findings, "split_requests_output": str(requests_path),
    }
    _write_json(report_path, report)
    _write_json(requests_path, {"schema_version": "0.1.0", "requests": requests})
    return PaintabilityQAResult(status, len(boundaries.get("features") or []), len(requests), len(requests), str(report_path), str(requests_path))


def _finding(code: str, severity: str, message: str, affected_ids: list[str] | None = None) -> dict[str, Any]:
    return {"code": code, "severity": severity, "message": message, "affected_ids": affected_ids or []}


def _read_json(path: Path, label: str, *, required: bool = True) -> dict[str, Any]:
    if not path.is_file():
        if required:
            raise FabricQAError(f"{label} not found: {path}")
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FabricQAError(f"Cannot read {label} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise FabricQAError(f"{label} must be a JSON object.")
    return value


def _read_csv(path: Path, *, required: bool) -> list[dict[str, str]]:
    if not path.is_file():
        if required:
            raise FabricQAError(f"CSV not found: {path}")
        return []
    with path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def _required_json(path: Path, label: str, findings: list[dict[str, Any]]) -> dict[str, Any]:
    try:
        return _read_json(path, label)
    except FabricQAError as exc:
        findings.append(_finding(f"missing_or_malformed_{label.lower().replace(' ', '_')}", "error", str(exc)))
        return {}


def _required_csv(path: Path, label: str, required_fields: set[str],
                  findings: list[dict[str, Any]]) -> list[dict[str, str]]:
    try:
        if not path.is_file():
            raise FabricQAError(f"{label} not found: {path}")
        with path.open("r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            fields = set(reader.fieldnames or [])
            if not required_fields.issubset(fields):
                raise FabricQAError(
                    f"{label} is missing columns: {', '.join(sorted(required_fields - fields))}"
                )
            return list(reader)
    except (OSError, csv.Error, FabricQAError) as exc:
        findings.append(_finding(f"missing_or_malformed_{label.lower().replace(' ', '_')}", "error", str(exc)))
        return []


def _resolve_manifest_path(value: str, manifest_path: Path) -> Path:
    path = Path(value)
    if path.is_absolute() or path.exists():
        return path
    return manifest_path.parent / path


def _manifest_land_path(manifest: dict[str, Any], manifest_path: Path) -> Path | None:
    for item in manifest.get("inputs") or []:
        if isinstance(item, dict) and item.get("role") == "land" and isinstance(item.get("path"), str):
            return _resolve_manifest_path(item["path"], manifest_path)
    return None


def _load_land(path: Path) -> Any:
    if path.suffix.lower() == ".zip":
        try:
            return unary_union([shape(item.geometry) for item in read_zipped_shapefile(path)])
        except Exception as exc:
            raise FabricQAError(f"Cannot read Natural Earth land ZIP {path}: {exc}") from exc
    document = _read_json(path, "Land input")
    land_features = document.get("features") if document.get("type") == "FeatureCollection" else [document]
    try:
        return unary_union([shape(item["geometry"]) for item in land_features if item.get("geometry")])
    except Exception as exc:
        raise FabricQAError(f"Cannot parse land geometry {path}: {exc}") from exc


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
