from __future__ import annotations

import csv
import hashlib
import heapq
import json
import math
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from shapely import normalize
from shapely.geometry import mapping, shape
from shapely.ops import unary_union
from shapely.strtree import STRtree

from gpm import __version__
from gpm.config import load_profile
from gpm.geo.shapefile import geometry_area_sq_km
from gpm.paths import PROCESSED_DATA_DIR


class ProvinceAggregationError(RuntimeError):
    """Raised when location-derived provinces cannot be aggregated."""


@dataclass(frozen=True)
class ProvinceAggregationResult:
    profile_id: str
    start_date: str
    target_province_count: int
    province_count: int
    input_location_count: int
    input_piece_count: int
    merge_count: int
    modern_boundary_influence: str
    province_output: str
    membership_output: str
    manifest_output: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class _Node:
    key: int
    geometry: Any
    members: list[tuple[str, str]]
    population: float
    terrain: set[str]
    historical: float
    reference_id: str | None
    neighbors: dict[int, float]
    active: bool = True
    version: int = 0

    @property
    def area(self) -> float:
        return float(self.geometry.area)


def aggregate_location_provinces(
    profile_id: str,
    *,
    location_input: Path,
    output_dir: Path = PROCESSED_DATA_DIR,
    province_output: Path | None = None,
    membership_output: Path | None = None,
    manifest_output: Path | None = None,
    target_province_count: int | None = None,
    start_date: str | None = None,
    aggregation_revision: str = "1",
    geometry_revision: str | None = None,
    modern_boundary_influence: str | None = None,
    modern_pieces_input: Path | None = None,
    generated_at: str | None = None,
) -> ProvinceAggregationResult:
    profile = load_profile(profile_id)
    generation = profile.get("generation") or {}
    target = int(target_province_count or generation.get("target_province_count") or 1)
    if target < 1:
        raise ProvinceAggregationError("target_province_count must be positive.")
    profile_era = str((profile.get("profile") or {}).get("era") or "undated")
    date = start_date or profile_era
    configured_influence = (profile.get("aggregation") or {}).get("modern_boundary_influence")
    influence = modern_boundary_influence or configured_influence or (
        "hard" if profile_id.startswith("modern-") else "soft"
    )
    if influence not in {"hard", "soft", "none"}:
        raise ProvinceAggregationError("modern_boundary_influence must be hard, soft, or none.")

    location_path = Path(location_input)
    collection = _read_collection(location_path, "Location input")
    location_features = collection["features"]
    fabric_meta = collection.get("gpm") if isinstance(collection.get("gpm"), dict) else {}
    fabric_revision = str(fabric_meta.get("fabric_revision") or "unknown")
    geom_revision = str(geometry_revision or fabric_meta.get("geometry_revision") or "1")

    piece_features: list[dict[str, Any]]
    resolved_pieces_input: Path | None = None
    if influence == "hard":
        candidate = modern_pieces_input or location_path.with_name("location_admin_pieces.geojson")
        if Path(candidate).is_file():
            resolved_pieces_input = Path(candidate)
            all_pieces = _read_collection(resolved_pieces_input, "Modern intersection pieces")["features"]
            piece_features = _select_hard_pieces(all_pieces, location_features)
        else:
            raise ProvinceAggregationError(
                "Hard modern-boundary aggregation requires location_admin_pieces.geojson "
                "next to the location input or --modern-pieces-input."
            )
    else:
        piece_features = []
        for feature in location_features:
            props = feature.get("properties") or {}
            location_id = props.get("location_id")
            if not isinstance(location_id, str) or not location_id:
                raise ProvinceAggregationError("Location feature is missing location_id.")
            piece_features.append({
                "type": "Feature",
                "geometry": feature["geometry"],
                "properties": {
                    **props,
                    "location_id": location_id,
                    "piece_id": "whole",
                    "reference_id": None,
                },
            })
    if not piece_features:
        raise ProvinceAggregationError("Location aggregation has no usable pieces.")

    location_props = {
        feature["properties"]["location_id"]: feature["properties"]
        for feature in location_features
        if isinstance(feature.get("properties"), dict) and isinstance(feature["properties"].get("location_id"), str)
    }
    nodes = _initial_nodes(piece_features, location_props)
    _connect_nodes(nodes, influence=influence)
    initial_count = len(nodes)
    merge_count = _merge_graph(nodes, target=target, influence=influence)
    active = sorted((node for node in nodes.values() if node.active), key=lambda node: node.members)

    intersection_rows = _load_intersection_rows(location_path.with_name("location_admin_intersections.csv"))
    provinces: list[dict[str, Any]] = []
    memberships: list[dict[str, Any]] = []
    for node in active:
        members = sorted(node.members)
        province_id = _province_id(
            members,
            profile_id=profile_id,
            start_date=date,
            aggregation_revision=aggregation_revision,
            geometry_revision=geom_revision,
        )
        country_id = _dominant_reference(members, intersection_rows, "admin0")
        region_id = _dominant_reference(members, intersection_rows, "admin1")
        geometry = normalize(node.geometry)
        source_lineage = sorted({
            item
            for location_id, _piece_id in members
            for item in (location_props.get(location_id, {}).get("source_lineage") or [])
            if isinstance(item, str)
        })
        license_lineage = sorted({
            item
            for location_id, _piece_id in members
            for item in (location_props.get(location_id, {}).get("license_lineage") or [])
            if isinstance(item, str)
        })
        provinces.append({
            "type": "Feature",
            "geometry": mapping(geometry),
            "properties": {
                "province_id": province_id,
                "display_name": province_id,
                "kind": "land",
                "parent_country_id": country_id,
                "parent_region_id": region_id,
                "area_sq_km": round(geometry_area_sq_km(mapping(geometry)), 6),
                "estimated_population": round(node.population, 6) if node.population else None,
                "terrain_class": sorted(node.terrain)[0] if len(node.terrain) == 1 else "mixed" if node.terrain else "unclassified",
                "coastal": False,
                "island": False,
                "location_count": len({location_id for location_id, _piece_id in members}),
                "piece_count": len(members),
                "profile_id": profile_id,
                "start_date": date,
                "fabric_revision": fabric_revision,
                "aggregation_revision": str(aggregation_revision),
                "geometry_revision": geom_revision,
                "modern_boundary_influence": influence,
                "source_lineage": source_lineage,
                "license_lineage": license_lineage,
            },
        })
        for location_id, piece_id in members:
            memberships.append({
                "province_id": province_id,
                "location_id": location_id,
                "piece_id": piece_id,
            })
    provinces.sort(key=lambda feature: feature["properties"]["province_id"])
    memberships.sort(key=lambda row: (row["province_id"], row["location_id"], row["piece_id"]))

    timestamp = generated_at or datetime.now(UTC).replace(microsecond=0).isoformat()
    output_dir = Path(output_dir)
    province_output = province_output or output_dir / "provinces.geojson"
    membership_output = membership_output or output_dir / "province_membership.csv"
    manifest_output = manifest_output or output_dir / "province_aggregation_manifest.json"
    province_document = {
        "type": "FeatureCollection",
        "gpm": {
            "layer_kind": "location_derived_provinces",
            "profile_id": profile_id,
            "start_date": date,
            "fabric_id": fabric_meta.get("fabric_id"),
            "fabric_revision": fabric_revision,
            "aggregation_revision": str(aggregation_revision),
            "geometry_revision": geom_revision,
            "modern_boundary_influence": influence,
            "generated_at": timestamp,
            "generator_version": __version__,
        },
        "features": provinces,
    }
    manifest = {
        "schema_version": "0.1.0",
        "manifest_type": "province_aggregation",
        "profile_id": profile_id,
        "start_date": date,
        "fabric_id": fabric_meta.get("fabric_id"),
        "fabric_revision": fabric_revision,
        "aggregation_revision": str(aggregation_revision),
        "geometry_revision": geom_revision,
        "modern_boundary_influence": influence,
        "generated_at": timestamp,
        "generator_version": __version__,
        "algorithm": "deterministic-contiguous-best-adjacent-graph-merge",
        "target_province_count": target,
        "actual_province_count": len(provinces),
        "input_location_count": len(location_features),
        "input_piece_count": initial_count,
        "merge_count": merge_count,
        "inputs": {
            "locations": str(location_path),
            "modern_pieces": str(resolved_pieces_input) if resolved_pieces_input else None,
        },
        "files": [Path(province_output).name, Path(membership_output).name],
    }
    _write_json(Path(province_output), province_document)
    _write_csv(Path(membership_output), memberships)
    _write_json(Path(manifest_output), manifest)
    return ProvinceAggregationResult(
        profile_id=profile_id,
        start_date=date,
        target_province_count=target,
        province_count=len(provinces),
        input_location_count=len(location_features),
        input_piece_count=initial_count,
        merge_count=merge_count,
        modern_boundary_influence=influence,
        province_output=str(province_output),
        membership_output=str(membership_output),
        manifest_output=str(manifest_output),
    )


def _read_collection(path: Path, label: str) -> dict[str, Any]:
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProvinceAggregationError(f"Cannot read {label} {path}: {exc}") from exc
    if document.get("type") != "FeatureCollection" or not isinstance(document.get("features"), list):
        raise ProvinceAggregationError(f"{label} must be a GeoJSON FeatureCollection: {path}")
    return document


def _select_hard_pieces(pieces: list[dict[str, Any]], locations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_location: dict[str, list[dict[str, Any]]] = {}
    for piece in pieces:
        props = piece.get("properties") or {}
        location_id = props.get("location_id")
        if isinstance(location_id, str):
            by_location.setdefault(location_id, []).append(piece)
    selected: list[dict[str, Any]] = []
    for location in locations:
        location_id = location["properties"]["location_id"]
        candidates = by_location.get(location_id, [])
        admin1 = [piece for piece in candidates if piece["properties"].get("reference_layer") == "admin1"]
        chosen = admin1 or [piece for piece in candidates if piece["properties"].get("reference_layer") == "admin0"]
        if not chosen:
            raise ProvinceAggregationError(f"Hard aggregation has no modern-reference piece for {location_id}.")
        selected.extend(chosen)
    return sorted(selected, key=lambda feature: str(feature["properties"].get("piece_id")))


def _initial_nodes(pieces: list[dict[str, Any]], location_props: dict[str, dict[str, Any]]) -> dict[int, _Node]:
    nodes: dict[int, _Node] = {}
    for index, feature in enumerate(sorted(pieces, key=lambda item: (str(item["properties"].get("location_id")), str(item["properties"].get("piece_id"))))):
        props = feature["properties"]
        location_id = str(props["location_id"])
        piece_id = str(props.get("piece_id") or "whole")
        source = location_props.get(location_id, {})
        population = source.get("population_signal") or source.get("estimated_population") or 0.0
        terrain = source.get("terrain_class")
        nodes[index] = _Node(
            key=index,
            geometry=shape(feature["geometry"]),
            members=[(location_id, piece_id)],
            population=float(population) if isinstance(population, (int, float)) else 0.0,
            terrain={str(terrain)} if terrain else set(),
            historical=float(source.get("historical_signal") or 0.0),
            reference_id=str(props.get("reference_id")) if props.get("reference_id") is not None else None,
            neighbors={},
        )
    return nodes


def _connect_nodes(nodes: dict[int, _Node], *, influence: str) -> None:
    ordered = [nodes[index] for index in sorted(nodes)]
    geoms = [node.geometry for node in ordered]
    tree = STRtree(geoms)
    for left_index, left in enumerate(ordered):
        for raw_right in tree.query(left.geometry, predicate="intersects"):
            right_index = int(raw_right)
            if right_index <= left_index:
                continue
            right = ordered[right_index]
            if influence == "hard" and left.reference_id != right.reference_id:
                continue
            border = left.geometry.boundary.intersection(right.geometry.boundary).length
            if border <= 1e-12:
                continue
            left.neighbors[right.key] = border
            right.neighbors[left.key] = border


def _merge_score(left: _Node, right: _Node, *, influence: str) -> float:
    border = left.neighbors.get(right.key, 0.0)
    balance = abs(math.log((left.area + 1e-12) / (right.area + 1e-12)))
    population_balance = abs(math.log((left.population + 1.0) / (right.population + 1.0)))
    terrain_barrier = 1.0 if left.terrain and right.terrain and left.terrain.isdisjoint(right.terrain) else 0.0
    historical_barrier = abs(left.historical - right.historical)
    modern_penalty = 0.0 if influence in {"none", "hard"} or left.reference_id == right.reference_id else 2.0
    return border * 1000.0 - balance - 0.2 * population_balance - terrain_barrier - historical_barrier - modern_penalty


def _merge_graph(nodes: dict[int, _Node], *, target: int, influence: str) -> int:
    active_count = len(nodes)
    heap: list[tuple[float, tuple[tuple[str, str], ...], int, int, int, int]] = []

    def push(left: _Node, right: _Node) -> None:
        if not left.active or not right.active or right.key not in left.neighbors:
            return
        first, second = (left, right) if left.members < right.members else (right, left)
        score = _merge_score(first, second, influence=influence)
        heapq.heappush(heap, (-score, tuple(first.members + second.members), first.key, second.key, first.version, second.version))

    for left in nodes.values():
        for neighbor_key in sorted(left.neighbors):
            if left.key < neighbor_key:
                push(left, nodes[neighbor_key])
    merges = 0
    while active_count > target and heap:
        _neg_score, _tie, left_key, right_key, left_version, right_version = heapq.heappop(heap)
        left, right = nodes[left_key], nodes[right_key]
        if not left.active or not right.active or left.version != left_version or right.version != right_version:
            continue
        if right.key not in left.neighbors:
            continue
        left.geometry = unary_union([left.geometry, right.geometry])
        left.members = sorted(left.members + right.members)
        left.population += right.population
        left.terrain.update(right.terrain)
        left.historical = max(left.historical, right.historical)
        if left.reference_id != right.reference_id:
            left.reference_id = None
        left.version += 1
        right.active = False
        right.version += 1
        left.neighbors.pop(right.key, None)
        combined: dict[int, float] = dict(left.neighbors)
        for neighbor_key, border in right.neighbors.items():
            if neighbor_key != left.key and nodes[neighbor_key].active:
                combined[neighbor_key] = combined.get(neighbor_key, 0.0) + border
            nodes[neighbor_key].neighbors.pop(right.key, None)
        left.neighbors = {}
        for neighbor_key, border in combined.items():
            neighbor = nodes[neighbor_key]
            if not neighbor.active:
                continue
            left.neighbors[neighbor_key] = border
            neighbor.neighbors[left.key] = border
            push(left, neighbor)
        active_count -= 1
        merges += 1
    if active_count > target:
        raise ProvinceAggregationError(
            f"Contiguity/boundary constraints stopped aggregation at {active_count}, above target {target}."
        )
    return merges


def _province_id(members: list[tuple[str, str]], *, profile_id: str, start_date: str,
                 aggregation_revision: str, geometry_revision: str) -> str:
    payload = json.dumps({
        "members": members,
        "profile_id": profile_id,
        "start_date": start_date,
        "aggregation_revision": str(aggregation_revision),
        "geometry_revision": str(geometry_revision),
    }, sort_keys=True, separators=(",", ":"))
    return f"prv_{hashlib.sha256(payload.encode()).hexdigest()[:20]}"


def _load_intersection_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def _dominant_reference(members: list[tuple[str, str]], rows: list[dict[str, str]], layer: str) -> str | None:
    member_ids = {location_id for location_id, _piece_id in members}
    totals: dict[str, float] = {}
    for row in rows:
        if row.get("location_id") in member_ids and row.get("reference_layer") == layer:
            reference_id = row.get("reference_id")
            if reference_id:
                totals[reference_id] = totals.get(reference_id, 0.0) + float(row.get("intersection_area_sq_km") or 0.0)
    return min(totals, key=lambda key: (-totals[key], key)) if totals else None


def _write_json(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=("province_id", "location_id", "piece_id"), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
