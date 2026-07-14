from __future__ import annotations

import csv
import json
import math
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from shapely import STRtree, make_valid
from shapely.errors import ShapelyError
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union
from shapely.validation import explain_validity

from gpm.builders.adjacency import ADJACENCY_COLUMNS
from gpm.config import load_profile, qa_thresholds
from gpm.geo.metrics import geometry_area_sq_km, geometry_length_km, polygon_parts
from gpm.geo.shapefile import ShapefileReadError, read_zipped_shapefile
from gpm.paths import PROCESSED_DATA_DIR, RAW_DATA_DIR
from gpm.schemas import validate_topology_qa_report


class TopologyQAError(RuntimeError):
    """Raised when topology QA cannot load inputs or complete its report."""


# Boolean operations on lon/lat polygons can leave sub-square-metre rounding
# residue. Treat less than one square metre as numeric noise, not source data
# outside the declared land mask.
NUMERICAL_AREA_EPSILON_SQ_KM = 1e-6


@dataclass(frozen=True)
class TopologyQAResult:
    profile_id: str
    report_output: str
    status: str
    province_count: int
    adjacency_count: int
    error_count: int
    warning_count: int
    coverage_analysis: str
    graph_analysis: str

    @property
    def passed(self) -> bool:
        return self.status == "pass"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class _Province:
    feature_index: int
    province_id: str
    kind: str | None
    properties: dict[str, Any]
    geometry: BaseGeometry | None
    geometry_valid: bool


@dataclass(frozen=True)
class _AdjacencyRow:
    row_number: int
    values: dict[str, str | None]


def run_topology_qa(
    profile_id: str,
    *,
    province_input: Path = PROCESSED_DATA_DIR / "provinces.geojson",
    adjacency_input: Path = PROCESSED_DATA_DIR / "adjacency.csv",
    raw_data: Path = RAW_DATA_DIR,
    report_output: Path = PROCESSED_DATA_DIR / "topology_qa.json",
) -> TopologyQAResult:
    profile = load_profile(profile_id)
    thresholds = qa_thresholds(profile)
    findings: list[dict[str, Any]] = []
    provinces = _load_provinces(province_input, findings)
    adjacency_rows = _load_adjacency(adjacency_input)
    mask_path, land_mask, mask_valid = _load_land_mask(raw_data, findings)

    counts = Counter(province.province_id for province in provinces if province.province_id)
    for province_id, count in sorted(counts.items()):
        if count > 1:
            _add_finding(
                findings,
                "DUPLICATE_PROVINCE_ID",
                "error",
                [province_id],
                f"Province ID {province_id!r} occurs {count} times.",
                occurrence_count=count,
            )

    valid_land = {
        province.province_id: province
        for province in provinces
        if province.kind == "land"
        and province.geometry_valid
        and province.geometry is not None
        and counts[province.province_id] == 1
    }
    land_ids = {
        province.province_id
        for province in provinces
        if province.kind == "land" and counts[province.province_id] == 1
    }
    province_geometry_incomplete = (
        any(not province.geometry_valid for province in provinces)
        or any(count > 1 for count in counts.values())
        or any(finding["code"] == "MISSING_PROVINCE_ID" for finding in findings)
    )
    if not any(province.kind == "land" for province in provinces):
        _add_finding(findings, "NO_LAND_PROVINCES", "error", [], "No land provinces were found.")
        province_geometry_incomplete = True

    coverage_complete = not province_geometry_incomplete and mask_valid
    graph_complete = not province_geometry_incomplete
    if not coverage_complete or not graph_complete:
        skipped = []
        if not coverage_complete:
            skipped.append("coverage")
        if not graph_complete:
            skipped.append("geometry-dependent graph")
        _add_finding(
            findings,
            "ANALYSIS_INCOMPLETE",
            "warning",
            [],
            f"Analysis incomplete ({', '.join(skipped)}): required geometry or IDs are invalid.",
        )
    coverage_analysis = "complete" if coverage_complete else "incomplete"
    graph_analysis = "complete" if graph_complete else "incomplete"
    if coverage_complete:
        assert land_mask is not None
        _validate_coverage(valid_land, land_mask, thresholds, findings)

    valid_graph_edges, seen_pairs = _validate_adjacency_rows(
        adjacency_rows,
        counts,
        valid_land,
        land_ids,
        thresholds,
        findings,
        geometry_complete=graph_complete,
    )
    if graph_complete:
        expected_pairs = _expected_adjacency_pairs(valid_land, thresholds["min_shared_border_km"])
        for from_id, to_id in sorted(set(expected_pairs) - seen_pairs):
            _add_finding(
                findings,
                "MISSING_ADJACENCY_EDGE",
                "error",
                [from_id, to_id],
                "A qualifying shared land border is absent from the adjacency CSV.",
                shared_border_km=expected_pairs[(from_id, to_id)],
            )
        _validate_graph(sorted(valid_land), valid_graph_edges, findings)

    findings.sort(key=_finding_sort_key)
    error_count = sum(finding["severity"] == "error" for finding in findings)
    warning_count = sum(finding["severity"] == "warning" for finding in findings)
    status = "fail" if error_count else "pass"
    isolated_count = sum(finding["code"] == "ISOLATED_PROVINCE" for finding in findings)
    component_findings = [finding for finding in findings if finding["code"] == "CONNECTED_COMPONENTS"]
    component_count = (
        int(component_findings[0]["measurements"]["component_count"])
        if component_findings
        else (1 if valid_land and graph_complete else 0)
    )
    report = {
        "schema_version": "0.1.0",
        "report_type": "topology_qa",
        "profile_id": profile_id,
        "status": status,
        "inputs": {
            "province_input": str(province_input),
            "adjacency_input": str(adjacency_input),
            "natural_earth_admin0_mask": str(mask_path),
        },
        "thresholds": thresholds,
        "summary": {
            "province_count": len(provinces),
            "land_province_count": sum(province.kind == "land" for province in provinces),
            "adjacency_count": len(adjacency_rows),
            "error_count": error_count,
            "warning_count": warning_count,
            "isolated_province_count": isolated_count,
            "connected_component_count": component_count,
            "analysis": {"coverage": coverage_analysis, "graph": graph_analysis},
        },
        "findings": findings,
    }
    validate_topology_qa_report(report)
    try:
        report_output.parent.mkdir(parents=True, exist_ok=True)
        report_output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        raise TopologyQAError(f"Cannot write topology QA report {report_output}: {exc}") from exc

    return TopologyQAResult(
        profile_id=profile_id,
        report_output=str(report_output),
        status=status,
        province_count=len(provinces),
        adjacency_count=len(adjacency_rows),
        error_count=error_count,
        warning_count=warning_count,
        coverage_analysis=coverage_analysis,
        graph_analysis=graph_analysis,
    )


def _load_provinces(path: Path, findings: list[dict[str, Any]]) -> list[_Province]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise TopologyQAError(f"Province input does not exist: {path}") from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise TopologyQAError(f"Cannot read province GeoJSON {path}: {exc}") from exc
    if not isinstance(document, dict) or document.get("type") != "FeatureCollection":
        raise TopologyQAError(f"Province input must be a GeoJSON FeatureCollection: {path}")
    features = document.get("features")
    if not isinstance(features, list):
        raise TopologyQAError(f"Province GeoJSON features must be an array: {path}")

    provinces: list[_Province] = []
    for index, feature in enumerate(features):
        fallback_id = f"feature[{index}]"
        if not isinstance(feature, dict):
            _add_finding(findings, "MALFORMED_PROVINCE", "error", [fallback_id], "Feature must be an object.")
            provinces.append(_Province(index, fallback_id, None, {}, None, False))
            continue
        properties = feature.get("properties")
        if not isinstance(properties, dict):
            properties = {}
            _add_finding(
                findings,
                "MALFORMED_PROVINCE",
                "error",
                [fallback_id],
                "Feature properties must be an object.",
            )
        province_id_value = properties.get("province_id")
        province_id = province_id_value if isinstance(province_id_value, str) and province_id_value else fallback_id
        if province_id == fallback_id:
            _add_finding(
                findings,
                "MISSING_PROVINCE_ID",
                "error",
                [fallback_id],
                "Province must have a non-empty string province_id.",
            )
        kind = properties.get("kind") if isinstance(properties.get("kind"), str) else None
        if kind == "land":
            for parent_key, code in (
                ("parent_country_id", "MISSING_PARENT_COUNTRY"),
                ("parent_region_id", "MISSING_PARENT_REGION"),
            ):
                if not isinstance(properties.get(parent_key), str) or not properties[parent_key]:
                    _add_finding(
                        findings,
                        code,
                        "error",
                        [province_id],
                        f"Land province {province_id!r} requires a non-empty {parent_key}.",
                    )

        geometry_mapping = feature.get("geometry")
        geometry: BaseGeometry | None = None
        geometry_valid = True
        if not isinstance(geometry_mapping, dict) or geometry_mapping.get("type") not in {
            "Polygon",
            "MultiPolygon",
        }:
            _add_finding(
                findings,
                "INVALID_GEOMETRY_TYPE",
                "error",
                [province_id],
                "Province geometry must be Polygon or MultiPolygon.",
            )
            geometry_valid = False
        else:
            try:
                geometry = shape(geometry_mapping)
            except (ShapelyError, TypeError, ValueError) as exc:
                _add_finding(
                    findings,
                    "MALFORMED_GEOMETRY",
                    "error",
                    [province_id],
                    f"Province geometry cannot be parsed: {exc}",
                )
                geometry_valid = False
            if geometry is not None and geometry.is_empty:
                _add_finding(findings, "EMPTY_GEOMETRY", "error", [province_id], "Province geometry is empty.")
                geometry_valid = False
            if geometry is not None and not geometry.is_valid:
                _add_finding(
                    findings,
                    "INVALID_GEOMETRY",
                    "error",
                    [province_id],
                    f"Province geometry is invalid: {explain_validity(geometry)}",
                )
                geometry_valid = False
        provinces.append(_Province(index, province_id, kind, properties, geometry, geometry_valid))
    return provinces


def _load_adjacency(path: Path) -> list[_AdjacencyRow]:
    try:
        file = path.open("r", encoding="utf-8", newline="")
    except FileNotFoundError as exc:
        raise TopologyQAError(f"Adjacency input does not exist: {path}") from exc
    except OSError as exc:
        raise TopologyQAError(f"Cannot read adjacency CSV {path}: {exc}") from exc
    try:
        with file:
            reader = csv.DictReader(file, strict=True)
            if reader.fieldnames is None:
                raise TopologyQAError(f"Adjacency CSV has no header: {path}")
            missing = [column for column in ADJACENCY_COLUMNS if column not in reader.fieldnames]
            if missing:
                raise TopologyQAError(f"Adjacency CSV is missing column(s): {', '.join(missing)}")
            return [_AdjacencyRow(index, dict(row)) for index, row in enumerate(reader, start=2)]
    except csv.Error as exc:
        raise TopologyQAError(f"Malformed adjacency CSV {path}: {exc}") from exc


def _load_land_mask(
    raw_data: Path, findings: list[dict[str, Any]]
) -> tuple[Path, BaseGeometry | None, bool]:
    mask_path = (
        raw_data
        if raw_data.is_file()
        else raw_data / "natural_earth" / "ne_10m_admin_0_countries.zip"
    )
    if not mask_path.is_file():
        raise TopologyQAError(f"Natural Earth admin-0 mask input does not exist: {mask_path}")
    try:
        source_features = read_zipped_shapefile(mask_path)
    except ShapefileReadError as exc:
        raise TopologyQAError(f"Cannot read Natural Earth admin-0 mask {mask_path}: {exc}") from exc
    geometries: list[BaseGeometry] = []
    invalid_count = 0
    for index, feature in enumerate(source_features):
        affected_id = _mask_feature_id(feature.properties, index)
        try:
            geometry = shape(feature.geometry)
        except (ShapelyError, TypeError, ValueError) as exc:
            invalid_count += 1
            _add_finding(
                findings,
                "INVALID_MASK_GEOMETRY",
                "error",
                [affected_id],
                f"Natural Earth admin-0 mask geometry cannot be parsed: {exc}",
            )
            continue
        if geometry.is_empty or not geometry.is_valid:
            reason = "empty" if geometry.is_empty else explain_validity(geometry)
            repaired = make_valid(geometry) if not geometry.is_empty else geometry
            repaired_polygons = [part for part in polygon_parts(repaired) if not part.is_empty]
            if repaired_polygons:
                geometry = unary_union(repaired_polygons)
                _add_finding(
                    findings,
                    "MASK_GEOMETRY_REPAIRED",
                    "warning",
                    [affected_id],
                    f"Natural Earth admin-0 mask geometry was repaired with make_valid: {reason}",
                )
            else:
                invalid_count += 1
                _add_finding(
                    findings,
                    "INVALID_MASK_GEOMETRY",
                    "error",
                    [affected_id],
                    f"Natural Earth admin-0 mask geometry is invalid: {reason}",
                )
                continue
        geometries.append(geometry)
    if not geometries:
        raise TopologyQAError(f"Natural Earth admin-0 mask contains no polygon geometry: {mask_path}")
    if invalid_count:
        return mask_path, None, False
    try:
        mask = unary_union(geometries)
    except ShapelyError as exc:
        raise TopologyQAError(f"Cannot dissolve Natural Earth admin-0 mask {mask_path}: {exc}") from exc
    if mask.is_empty or not mask.is_valid:
        _add_finding(
            findings,
            "INVALID_MASK_GEOMETRY",
            "error",
            [],
            f"Dissolved Natural Earth admin-0 mask is invalid: {explain_validity(mask)}",
        )
        return mask_path, None, False
    return mask_path, mask, True


def _mask_feature_id(properties: dict[str, Any], index: int) -> str:
    by_lower = {str(key).lower(): value for key, value in properties.items()}
    for key in ("adm0_a3", "iso_a3", "name", "admin"):
        value = by_lower.get(key)
        if value is not None and str(value).strip().strip("\0").strip():
            return str(value).strip().strip("\0").strip()
    return f"admin0_mask_feature[{index}]"


def _validate_coverage(
    provinces: dict[str, _Province],
    land_mask: BaseGeometry,
    thresholds: dict[str, float],
    findings: list[dict[str, Any]],
) -> None:
    items = sorted(provinces.items())
    geometries = [province.geometry for _, province in items]
    assert all(geometry is not None for geometry in geometries)
    tree = STRtree(geometries)
    for index, (province_id, province) in enumerate(items):
        assert province.geometry is not None
        for candidate_value in tree.query(province.geometry):
            candidate_index = int(candidate_value)
            if candidate_index <= index:
                continue
            candidate_id, candidate = items[candidate_index]
            assert candidate.geometry is not None
            overlap = province.geometry.intersection(candidate.geometry)
            overlap_area = geometry_area_sq_km(overlap)
            if overlap_area > 0:
                limit = thresholds["max_overlap_area_sq_km"]
                severity = "error" if overlap_area > limit else "warning"
                _add_finding(
                    findings,
                    "PROVINCE_OVERLAP",
                    severity,
                    [province_id, candidate_id],
                    "Land provinces overlap by a positive area.",
                    overlap_area_sq_km=overlap_area,
                    configured_limit_sq_km=limit,
                )
        outside_area = geometry_area_sq_km(province.geometry.difference(land_mask))
        if outside_area > NUMERICAL_AREA_EPSILON_SQ_KM:
            _add_finding(
                findings,
                "COVERAGE_OUTSIDE_MASK",
                "error",
                [province_id],
                "Province coverage extends outside the Natural Earth admin-0 mask.",
                outside_area_sq_km=outside_area,
            )

    union = unary_union(geometries)
    gap_components = []
    for component in polygon_parts(land_mask.difference(union)):
        area = geometry_area_sq_km(component)
        if area > 0:
            gap_components.append((area, component.bounds))
    gap_components.sort(key=lambda item: (-item[0], item[1]))
    limit = thresholds["max_gap_component_area_sq_km"]
    for index, (area, _bounds) in enumerate(gap_components, start=1):
        severity = "error" if area > limit else "warning"
        _add_finding(
            findings,
            "LAND_COVERAGE_GAP",
            severity,
            [],
            f"Natural Earth mask gap component {index} has positive uncovered area.",
            gap_component_area_sq_km=area,
            configured_limit_sq_km=limit,
        )


def _validate_adjacency_rows(
    rows: list[_AdjacencyRow],
    province_counts: Counter[str],
    valid_land: dict[str, _Province],
    land_ids: set[str],
    thresholds: dict[str, float],
    findings: list[dict[str, Any]],
    *,
    geometry_complete: bool,
) -> tuple[set[tuple[str, str]], set[tuple[str, str]]]:
    valid_edges: set[tuple[str, str]] = set()
    seen_pairs: set[tuple[str, str]] = set()
    for row in rows:
        values = row.values
        from_id = values.get("from_province_id") or ""
        to_id = values.get("to_province_id") or ""
        affected = sorted(item for item in (from_id, to_id) if item)
        row_valid = True
        if not from_id or not to_id:
            _add_finding(
                findings,
                "MALFORMED_ADJACENCY_ROW",
                "error",
                affected,
                f"Adjacency row {row.row_number} requires both endpoint IDs.",
                row_number=row.row_number,
            )
            continue
        pair = tuple(sorted((from_id, to_id)))
        for endpoint in (from_id, to_id):
            if province_counts[endpoint] == 0:
                _add_finding(
                    findings,
                    "UNKNOWN_ADJACENCY_ENDPOINT",
                    "error",
                    [endpoint],
                    f"Adjacency row {row.row_number} references unknown province {endpoint!r}.",
                    row_number=row.row_number,
                )
                row_valid = False
            elif province_counts[endpoint] > 1:
                row_valid = False
            elif endpoint not in land_ids:
                _add_finding(
                    findings,
                    "NONLAND_ADJACENCY_ENDPOINT",
                    "error",
                    [endpoint],
                    f"Land adjacency row {row.row_number} references a non-land province.",
                    row_number=row.row_number,
                )
                row_valid = False
        if from_id == to_id:
            _add_finding(
                findings,
                "SELF_ADJACENCY_EDGE",
                "error",
                [from_id],
                f"Adjacency row {row.row_number} is a self-edge.",
                row_number=row.row_number,
            )
            row_valid = False
        elif from_id > to_id:
            _add_finding(
                findings,
                "NONCANONICAL_ADJACENCY_PAIR",
                "error",
                affected,
                f"Adjacency row {row.row_number} endpoints are not lexicographically ordered.",
                row_number=row.row_number,
            )
            row_valid = False
        if pair in seen_pairs:
            _add_finding(
                findings,
                "DUPLICATE_ADJACENCY_EDGE",
                "error",
                affected,
                f"Adjacency row {row.row_number} duplicates an undirected pair.",
                row_number=row.row_number,
            )
            row_valid = False
        seen_pairs.add(pair)

        expected_values = {
            "adjacency_type": "land",
            "bidirectional": "true",
            "crossing_type": "shared_border",
        }
        for field, expected in expected_values.items():
            if values.get(field) != expected:
                code = "ASYMMETRIC_ADJACENCY" if field == "bidirectional" else "INVALID_ADJACENCY_SEMANTICS"
                _add_finding(
                    findings,
                    code,
                    "error",
                    affected,
                    f"Adjacency row {row.row_number} requires {field}={expected!r}.",
                    row_number=row.row_number,
                )
                row_valid = False

        try:
            measured = float(values.get("shared_border_km") or "")
        except ValueError:
            measured = -1.0
        if not math.isfinite(measured) or measured <= 0:
            _add_finding(
                findings,
                "INVALID_SHARED_BORDER_MEASUREMENT",
                "error",
                affected,
                f"Adjacency row {row.row_number} requires a positive shared_border_km.",
                row_number=row.row_number,
            )
            row_valid = False
        elif measured < thresholds["min_shared_border_km"]:
            _add_finding(
                findings,
                "SHARED_BORDER_BELOW_THRESHOLD",
                "error",
                affected,
                f"Adjacency row {row.row_number} is below the configured border threshold.",
                row_number=row.row_number,
                shared_border_km=measured,
                configured_minimum_km=thresholds["min_shared_border_km"],
            )
            row_valid = False

        try:
            lineage = json.loads(values.get("source_lineage") or "")
            lineage_valid = isinstance(lineage, list) and all(isinstance(item, str) and item for item in lineage)
        except json.JSONDecodeError:
            lineage_valid = False
        if not lineage_valid:
            _add_finding(
                findings,
                "INVALID_ADJACENCY_LINEAGE",
                "error",
                affected,
                f"Adjacency row {row.row_number} source_lineage must be a JSON string array.",
                row_number=row.row_number,
            )
            row_valid = False

        if geometry_complete and from_id in valid_land and to_id in valid_land and from_id != to_id:
            from_geometry = valid_land[from_id].geometry
            to_geometry = valid_land[to_id].geometry
            assert from_geometry is not None and to_geometry is not None
            actual = geometry_length_km(from_geometry.boundary.intersection(to_geometry.boundary))
            if actual < thresholds["min_shared_border_km"]:
                _add_finding(
                    findings,
                    "INVALID_ADJACENCY_BORDER",
                    "error",
                    affected,
                    "Adjacency endpoints do not share a qualifying lineal border.",
                    measured_shared_border_km=measured,
                    actual_shared_border_km=actual,
                )
                row_valid = False
            elif measured > 0 and abs(measured - actual) > max(0.001, actual * 0.001):
                _add_finding(
                    findings,
                    "SHARED_BORDER_MEASUREMENT_MISMATCH",
                    "error",
                    affected,
                    "Recorded shared-border length differs materially from province geometry.",
                    measured_shared_border_km=measured,
                    actual_shared_border_km=actual,
                )
                row_valid = False
        if row_valid:
            valid_edges.add(pair)
    return valid_edges, seen_pairs


def _expected_adjacency_pairs(
    provinces: dict[str, _Province], min_shared_border_km: float
) -> dict[tuple[str, str], float]:
    items = sorted(provinces.items())
    geometries = [province.geometry for _, province in items]
    tree = STRtree(geometries)
    expected: dict[tuple[str, str], float] = {}
    for index, (province_id, province) in enumerate(items):
        assert province.geometry is not None
        for candidate_value in tree.query(province.geometry):
            candidate_index = int(candidate_value)
            if candidate_index <= index:
                continue
            candidate_id, candidate = items[candidate_index]
            assert candidate.geometry is not None
            distance = geometry_length_km(province.geometry.boundary.intersection(candidate.geometry.boundary))
            if distance + 1e-12 >= min_shared_border_km:
                expected[(province_id, candidate_id)] = _measurement(distance)
    return expected


def _validate_graph(
    province_ids: list[str], edges: set[tuple[str, str]], findings: list[dict[str, Any]]
) -> None:
    graph = {province_id: set() for province_id in province_ids}
    for from_id, to_id in edges:
        if from_id in graph and to_id in graph:
            graph[from_id].add(to_id)
            graph[to_id].add(from_id)
    for province_id in sorted(node for node, neighbors in graph.items() if not neighbors):
        _add_finding(
            findings,
            "ISOLATED_PROVINCE",
            "warning",
            [province_id],
            "Land province has no validated land-adjacency edge; valid islands may be isolated.",
        )

    components: list[list[str]] = []
    remaining = set(graph)
    while remaining:
        start = min(remaining)
        component: list[str] = []
        stack = [start]
        remaining.remove(start)
        while stack:
            node = stack.pop()
            component.append(node)
            for neighbor in sorted(graph[node], reverse=True):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
        components.append(sorted(component))
    components.sort(key=lambda component: (-len(component), component))
    if len(components) > 1:
        _add_finding(
            findings,
            "CONNECTED_COMPONENTS",
            "warning",
            [],
            "Land-adjacency graph has multiple connected components; islands can make this valid.",
            component_count=len(components),
            largest_component_size=len(components[0]),
            smallest_component_size=len(components[-1]),
        )


def _add_finding(
    findings: list[dict[str, Any]],
    code: str,
    severity: str,
    affected_ids: list[str],
    message: str,
    **measurements: Any,
) -> None:
    findings.append(
        {
            "code": code,
            "severity": severity,
            "affected_ids": sorted(set(affected_ids)),
            "message": message,
            "measurements": {key: _measurement(value) for key, value in sorted(measurements.items())},
        }
    )


def _measurement(value: Any) -> Any:
    if isinstance(value, float):
        return float(f"{value:.12g}")
    return value


def _finding_sort_key(finding: dict[str, Any]) -> tuple[Any, ...]:
    return (
        {"error": 0, "warning": 1}.get(finding["severity"], 2),
        finding["code"],
        tuple(finding["affected_ids"]),
        finding["message"],
        json.dumps(finding["measurements"], sort_keys=True, separators=(",", ":")),
    )
