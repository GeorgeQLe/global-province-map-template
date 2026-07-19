"""Compile canonical historical documents into the M25B runtime contract.

The compiler is intentionally the only GIS-aware part of this package.  The
reference loader reads fixed-width tables, CSR arrays, and already prepared
geometry; it never reconstructs topology or reads canonical GeoJSON.
"""

from __future__ import annotations

import hashlib
import gzip
import json
import os
import struct
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from shapely.geometry import shape
from shapely.ops import triangulate

from gpm import __version__
from gpm.historical.casebook import load_casebook
from gpm.schemas import (
    SchemaValidationError,
    validate_historical_territory_status,
    validate_runtime_pack_manifest,
)
from gpm.tiles.build import build_pmtiles_from_features


FORMAT_VERSION = "1.0.0"
UINT32_MAX = 0xFFFFFFFF
RELATIONSHIPS = (
    "sovereign", "owner", "controller", "core", "claim", "dispute", "protector", "co-administrator",
    "occupier", "mandate-authority", "lessee", "claimant",
)
SUBJECT_KINDS = {"component": 0, "province": 1, "political_unit": 2}


class RuntimeCompileError(ValueError):
    """Raised when canonical input cannot be compiled without information loss."""


@dataclass(frozen=True)
class RuntimeCompileResult:
    output_dir: str
    runtime_manifest: str
    pack_id: str
    compatibility_revision: str
    province_count: int
    component_count: int
    political_unit_count: int
    scenario_count: int
    file_count: int
    core_bytes: int
    geometry_bytes: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compile_runtime_pack(
    canonical_input: Path | str,
    output_dir: Path | str,
    *,
    pack_id: str | None = None,
    compatibility_revision: str = "1",
    previous_revision: str | None = None,
    include_debug_symbols: bool = False,
    min_zoom: int = 0,
    max_zoom: int = 4,
) -> RuntimeCompileResult:
    """Compile one canonical status document or an M25A casebook.

    Casebooks become a multi-scenario conformance pack.  A normal canonical
    status document becomes one scenario keyed by its start date.
    """
    source = Path(canonical_input)
    destination = Path(output_dir)
    if destination.exists() and any(destination.iterdir()):
        raise RuntimeCompileError(f"runtime output directory is not empty: {destination}")
    scenarios, migrations, source_kind = _load_scenarios(source)
    resolved_pack_id = pack_id or source.stem.replace("_", "-")
    if not resolved_pack_id or not compatibility_revision:
        raise RuntimeCompileError("pack_id and compatibility_revision must be non-empty")

    parent = destination.parent.resolve()
    parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{destination.name}-", dir=parent) as temporary:
        root = Path(temporary)
        result = _compile(
            scenarios,
            migrations,
            root,
            pack_id=resolved_pack_id,
            compatibility_revision=compatibility_revision,
            previous_revision=previous_revision,
            source_kind=source_kind,
            include_debug_symbols=include_debug_symbols,
            min_zoom=min_zoom,
            max_zoom=max_zoom,
        )
        destination.mkdir(parents=True, exist_ok=True)
        for child in sorted(root.iterdir(), key=lambda item: item.name):
            os.replace(child, destination / child.name)
    return RuntimeCompileResult(
        output_dir=str(destination.resolve()),
        runtime_manifest=str((destination / "runtime_manifest.json").resolve()),
        **result,
    )


def _load_scenarios(source: Path) -> tuple[list[tuple[str, dict[str, Any]]], dict[str, str], str]:
    try:
        document = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeCompileError(f"cannot load canonical input {source}: {exc}") from exc
    if document.get("fixture_type") == "historical-hard-case-casebook":
        casebook = load_casebook(source)
        scenarios = []
        migration: dict[str, str] = {}
        for case in casebook["cases"]:
            scenario_id = str(case["fixture_id"])
            scenarios.append((scenario_id, case["canonical"]))
            migration.update(case["expectations"]["save_migration"]["province_id_map"])
        return scenarios, migration, "m25a-casebook"
    try:
        validate_historical_territory_status(document)
    except SchemaValidationError as exc:
        raise RuntimeCompileError(str(exc)) from exc
    scenario_id = str(document.get("scenario_id") or document["start_date"])
    migration = dict(document.get("province_id_map") or document.get("migration", {}).get("province_id_map") or {})
    return [(scenario_id, document)], migration, "canonical-status"


def _compile(
    scenarios: list[tuple[str, dict[str, Any]]],
    migrations: dict[str, str],
    root: Path,
    *,
    pack_id: str,
    compatibility_revision: str,
    previous_revision: str | None,
    source_kind: str,
    include_debug_symbols: bool,
    min_zoom: int,
    max_zoom: int,
) -> dict[str, Any]:
    for name in ("core", "graphs", "scenarios", "geometry"):
        (root / name).mkdir(parents=True, exist_ok=True)

    components = _unique_rows(scenarios, "components", "territory_component_id")
    provinces = _unique_rows(scenarios, "provinces", "province_id")
    units = _unique_rows(scenarios, "political_units", "political_unit_id")
    external_ids = sorted({str(value) for _, doc in scenarios for value in doc.get("external_actor_ids", [])})
    unit_ids = sorted(set(units) | set(external_ids))
    component_ids, province_ids = sorted(components), sorted(provinces)
    hierarchy_ids = {
        level: sorted({value for row in provinces.values() if (value := _hierarchy_value(row, level))})
        for level in ("area", "region", "superregion")
    }
    maps = {
        "components": component_ids,
        "provinces": province_ids,
        "political_units": unit_ids,
        "relationships": list(RELATIONSHIPS),
        "scenarios": [scenario_id for scenario_id, _ in sorted(scenarios)],
        "areas": hierarchy_ids["area"],
        "regions": hierarchy_ids["region"],
        "superregions": hierarchy_ids["superregion"],
    }
    _write_json(root / "core" / "stable_ids.json", maps)
    component_index = {value: index for index, value in enumerate(component_ids)}
    province_index = {value: index for index, value in enumerate(province_ids)}
    unit_index = {value: index for index, value in enumerate(unit_ids)}

    component_records = []
    for stable_id in component_ids:
        row = components[stable_id]
        component_records.append((
            unit_index[row["political_unit_id"]], province_index[row["province_id"]],
            1 if row.get("historically_required") else 0,
            1 if row.get("minimum_area_merge_exempt") else 0,
        ))
    _write_table(root / "core" / "components.bin", b"GPMCMP1\0", "<IIBBxx", component_records)

    province_members: list[int] = []
    province_records = []
    for stable_id in province_ids:
        row = provinces[stable_id]
        members = sorted(component_index[item] for item in row["territory_component_ids"])
        offset = len(province_members)
        province_members.extend(members)
        province_records.append((
            offset,
            len(members),
            _optional_index(_hierarchy_value(row, "area"), hierarchy_ids["area"]),
            _optional_index(_hierarchy_value(row, "region"), hierarchy_ids["region"]),
            _optional_index(_hierarchy_value(row, "superregion"), hierarchy_ids["superregion"]),
        ))
    _write_table(root / "core" / "provinces.bin", b"GPMPRV1\0", "<IIIII", province_records)
    _write_u32(root / "core" / "province_components.bin", province_members)

    _write_table(root / "core" / "political_units.bin", b"GPMUNT1\0", "<I", [(index,) for index in range(len(unit_ids))])

    ordered_scenarios = sorted(scenarios, key=lambda item: item[0])
    scenario_meta = []
    base_rows: list[tuple[int, ...]] | None = None
    for scenario_index, (scenario_id, document) in enumerate(ordered_scenarios):
        rows = _status_records(document, component_index, province_index, unit_index)
        union_path = f"scenarios/unions-{scenario_index:03d}.bin"
        _write_unions(root / union_path, document.get("union_relationships", []), unit_index)
        if scenario_index == 0:
            base_rows = rows
            filename = "base.bin"
            _write_table(root / "scenarios" / filename, b"GPMSTA1\0", "<BBHII", rows)
            mode = "base"
        else:
            assert base_rows is not None
            base_set, current_set = set(base_rows), set(rows)
            removed, added = sorted(base_set - current_set), sorted(current_set - base_set)
            filename = f"delta-{scenario_index:03d}.bin"
            _write_delta(root / "scenarios" / filename, removed, added)
            mode = "delta"
        scenario_meta.append({"dense_index": scenario_index, "scenario_id": scenario_id,
                              "start_date": document["start_date"], "mode": mode,
                              "path": f"scenarios/{filename}", "union_path": union_path})
    _write_json(root / "scenarios" / "index.json", {"base_scenario": ordered_scenarios[0][0], "scenarios": scenario_meta})

    graph_edges = _graph_edges(components, component_index, province_index, scenarios)
    graph_counts: dict[str, int] = {}
    for graph_type in ("land", "sea", "strait", "port"):
        edges = graph_edges[graph_type]
        _write_csr(root / "graphs" / f"{graph_type}.csr", len(province_ids), edges)
        graph_counts[graph_type] = len(edges)

    pmtiles_features, triangle_counts = _write_geometry(
        root, components, component_ids, component_index, province_index
    )
    try:
        tile_result = build_pmtiles_from_features(
            pmtiles_features, root / "geometry" / "map.pmtiles", layer_name="runtime_provinces",
            min_zoom=min_zoom, max_zoom=max_zoom, write_manifest=False, backend="native",
            property_keys=frozenset({"province", "component"}),
            name=f"{pack_id} runtime geometry", description="M25B precompiled runtime geometry",
        )
    except Exception as exc:  # noqa: BLE001 - normalize tile errors at contract boundary
        raise RuntimeCompileError(f"cannot compile runtime PMTiles: {exc}") from exc

    _write_json(root / "migration.json", {
        "schema_version": FORMAT_VERSION,
        "from_compatibility_revision": previous_revision,
        "to_compatibility_revision": compatibility_revision,
        "unchanged_stable_ids_compatible": True,
        "province_id_map": {key: migrations[key] for key in sorted(migrations)},
    })
    if include_debug_symbols:
        (root / "debug").mkdir()
        _write_json(root / "debug" / "symbols.json", {
            "notice": "Optional debug symbols; not required by the runtime loader.",
            "components": components,
            "provinces": provinces,
            "political_units": units,
        })

    files = _file_records(root)
    core_bytes = sum(item["bytes"] for item in files if item["path"].startswith(("core/", "graphs/", "scenarios/")))
    geometry_bytes = sum(item["bytes"] for item in files if item["path"].startswith("geometry/"))
    core_compressed_bytes = sum(
        len(gzip.compress((root / item["path"]).read_bytes(), mtime=0))
        for item in files
        if item["path"].startswith(("core/", "graphs/", "scenarios/"))
    )
    initial_compressed_bytes = core_compressed_bytes + len(
        gzip.compress((root / "geometry" / "lod0.tri").read_bytes(), mtime=0)
    )
    manifest = {
        "schema_version": FORMAT_VERSION,
        "pack_type": "gpm-game-runtime",
        "pack_id": pack_id,
        "compatibility_revision": compatibility_revision,
        "generator": {"name": "gpm", "version": __version__, "milestone": "M25B"},
        "canonical_input_kind": source_kind,
        "deterministic": True,
        "counts": {"components": len(component_ids), "provinces": len(province_ids),
                   "political_units": len(unit_ids), "scenarios": len(ordered_scenarios),
                   "triangles_by_lod": triangle_counts, "tiles": tile_result.tile_count,
                   "graph_edges": graph_counts},
        "entrypoints": {"stable_ids": "core/stable_ids.json", "scenario_index": "scenarios/index.json",
                        "migration": "migration.json", "lowest_lod": "geometry/lod0.tri",
                        "pmtiles": "geometry/map.pmtiles"},
        "debug_symbols_included": include_debug_symbols,
        "size_metrics": {
            "core_uncompressed_bytes": core_bytes,
            "core_individually_gzip_bytes": core_compressed_bytes,
            "initial_core_plus_lod0_gzip_bytes": initial_compressed_bytes,
            "geometry_archive_bytes": geometry_bytes,
        },
        "files": files,
    }
    validate_runtime_pack_manifest(manifest)
    _write_json(root / "runtime_manifest.json", manifest)
    return {"pack_id": pack_id, "compatibility_revision": compatibility_revision,
            "province_count": len(province_ids), "component_count": len(component_ids),
            "political_unit_count": len(unit_ids), "scenario_count": len(ordered_scenarios),
            "file_count": len(files) + 1, "core_bytes": core_bytes, "geometry_bytes": geometry_bytes}


def _unique_rows(scenarios: Iterable[tuple[str, dict[str, Any]]], collection: str, id_key: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for scenario_id, document in scenarios:
        for row in document.get(collection, []):
            stable_id = str(row[id_key])
            identity = _identity_projection(collection, row)
            if stable_id in result and _identity_projection(collection, result[stable_id]) != identity:
                raise RuntimeCompileError(f"{scenario_id}: stable ID {stable_id!r} changes identity across scenarios")
            result.setdefault(stable_id, row)
    return result


def _identity_projection(collection: str, row: dict[str, Any]) -> Any:
    if collection == "components":
        return (row.get("political_unit_id"), row.get("province_id"), row.get("geometry"))
    if collection == "provinces":
        return tuple(sorted(row.get("territory_component_ids", [])))
    return tuple(sorted(row.get("territory_component_ids", [])))


def _status_records(document: dict[str, Any], components: dict[str, int], provinces: dict[str, int], units: dict[str, int]) -> list[tuple[int, ...]]:
    records = []
    for row in document["statuses"]:
        subject = row["subject_id"]
        if subject in components:
            kind, subject_index = SUBJECT_KINDS["component"], components[subject]
        elif subject in provinces:
            kind, subject_index = SUBJECT_KINDS["province"], provinces[subject]
        elif subject in units:
            kind, subject_index = SUBJECT_KINDS["political_unit"], units[subject]
        else:
            raise RuntimeCompileError(f"status has unknown subject: {subject}")
        try:
            relation = RELATIONSHIPS.index(row["relationship"])
            actor = units[row["actor_political_unit_id"]]
        except (ValueError, KeyError) as exc:
            raise RuntimeCompileError(f"status cannot resolve relationship/actor: {row}") from exc
        records.append((kind, relation, 0, subject_index, actor))
    return sorted(set(records))


def _graph_edges(components: dict[str, dict[str, Any]], component_index: dict[str, int], province_index: dict[str, int], scenarios: list[tuple[str, dict[str, Any]]]) -> dict[str, set[tuple[int, int]]]:
    result = {key: set() for key in ("land", "sea", "strait", "port")}
    ids = sorted(components)
    geometries = {key: shape(components[key]["geometry"]) for key in ids}
    for _, document in scenarios:
        scenario_ids = sorted(row["territory_component_id"] for row in document["components"])
        for left_pos, left_id in enumerate(scenario_ids):
            for right_id in scenario_ids[left_pos + 1:]:
                if geometries[left_id].boundary.intersection(geometries[right_id].boundary).length > 0:
                    left = province_index[components[left_id]["province_id"]]
                    right = province_index[components[right_id]["province_id"]]
                    if left != right:
                        result["land"].add(tuple(sorted((left, right))))
        for row in document.get("adjacency", []):
            graph_type = str(row.get("type", "land"))
            if graph_type not in result:
                raise RuntimeCompileError(f"unsupported adjacency type: {graph_type}")
            left_id = row.get("from_province_id") or row.get("from")
            right_id = row.get("to_province_id") or row.get("to")
            try:
                result[graph_type].add(tuple(sorted((province_index[left_id], province_index[right_id]))))
            except KeyError as exc:
                raise RuntimeCompileError(f"adjacency references unknown province: {row}") from exc
    return result


def _write_geometry(root: Path, components: dict[str, dict[str, Any]], component_ids: list[str], component_index: dict[str, int], province_index: dict[str, int]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    features = []
    counts = {}
    geometries = [(stable_id, shape(components[stable_id]["geometry"])) for stable_id in component_ids]
    for lod, tolerance in enumerate((0.25, 0.05, 0.0)):
        triangles: list[tuple[int, int, tuple[float, ...]]] = []
        for stable_id, original in geometries:
            geometry = original.simplify(tolerance, preserve_topology=True) if tolerance else original
            for triangle in triangulate(geometry):
                clipped = triangle.intersection(geometry)
                for polygon in _polygon_parts(clipped):
                    coords = list(polygon.exterior.coords)[:-1]
                    if len(coords) == 3 and polygon.area > 0:
                        flat = tuple(float(value) for point in coords for value in point)
                        triangles.append((component_index[stable_id], province_index[components[stable_id]["province_id"]], flat))
        triangles.sort()
        _write_triangles(root / "geometry" / f"lod{lod}.tri", triangles)
        counts[str(lod)] = len(triangles)
    for stable_id, geometry in geometries:
        features.append({"geometry": geometry, "id": component_index[stable_id],
                         "properties": {"component": component_index[stable_id],
                                        "province": province_index[components[stable_id]["province_id"]]}})
    return features, counts


def _polygon_parts(geometry: Any) -> list[Any]:
    if geometry.geom_type == "Polygon":
        return [geometry]
    if geometry.geom_type in {"MultiPolygon", "GeometryCollection"}:
        return [part for child in geometry.geoms for part in _polygon_parts(child)]
    return []


def _write_table(path: Path, magic: bytes, record_format: str, rows: Iterable[tuple[int, ...]]) -> None:
    records = list(rows)
    record_size = struct.calcsize(record_format)
    payload = bytearray(magic + struct.pack("<II", len(records), record_size))
    for row in records:
        payload.extend(struct.pack(record_format, *row))
    path.write_bytes(payload)


def _write_u32(path: Path, values: Iterable[int]) -> None:
    rows = [(value,) for value in values]
    _write_table(path, b"GPMU321\0", "<I", rows)


def _write_delta(path: Path, removed: list[tuple[int, ...]], added: list[tuple[int, ...]]) -> None:
    fmt = "<BBHII"
    payload = bytearray(b"GPMDEL1\0" + struct.pack("<III", len(removed), len(added), struct.calcsize(fmt)))
    for row in removed + added:
        payload.extend(struct.pack(fmt, *row))
    path.write_bytes(payload)


def _write_unions(path: Path, rows: list[dict[str, Any]], unit_index: dict[str, int]) -> None:
    records: list[tuple[int, int, int]] = []
    members: list[int] = []
    for row in sorted(rows, key=lambda item: (item["relationship"], item["actor_political_unit_id"])):
        if row["relationship"] != "personal_union":
            raise RuntimeCompileError(f"unsupported political-unit relationship: {row['relationship']}")
        try:
            actor = unit_index[row["actor_political_unit_id"]]
            member_indices = sorted(unit_index[value] for value in row["member_political_unit_ids"])
        except KeyError as exc:
            raise RuntimeCompileError(f"union relationship references unknown political unit: {row}") from exc
        offset = len(members)
        members.extend(member_indices)
        records.append((actor, offset, len(member_indices)))
    payload = bytearray(b"GPMUNI1\0" + struct.pack("<II", len(records), len(members)))
    for record in records:
        payload.extend(struct.pack("<III", *record))
    if members:
        payload.extend(struct.pack(f"<{len(members)}I", *members))
    path.write_bytes(payload)


def _write_csr(path: Path, node_count: int, undirected_edges: set[tuple[int, int]]) -> None:
    neighbors = [[] for _ in range(node_count)]
    for left, right in sorted(undirected_edges):
        if left == right:
            continue
        neighbors[left].append(right)
        neighbors[right].append(left)
    offsets = [0]
    flat = []
    for row in neighbors:
        flat.extend(sorted(set(row)))
        offsets.append(len(flat))
    payload = bytearray(b"GPMCSR1\0" + struct.pack("<II", node_count, len(flat)))
    payload.extend(struct.pack(f"<{len(offsets)}I", *offsets))
    if flat:
        payload.extend(struct.pack(f"<{len(flat)}I", *flat))
    path.write_bytes(payload)


def _write_triangles(path: Path, triangles: list[tuple[int, int, tuple[float, ...]]]) -> None:
    payload = bytearray(b"GPMTRI1\0" + struct.pack("<I", len(triangles)))
    for component, province, coordinates in triangles:
        payload.extend(struct.pack("<II6f", component, province, *coordinates))
    path.write_bytes(payload)


def _optional_index(value: Any, values: list[str]) -> int:
    return values.index(value) if value in values else UINT32_MAX


def _hierarchy_value(row: dict[str, Any], level: str) -> str | None:
    hierarchy = row.get("hierarchy") or {}
    value = hierarchy.get(f"{level}_id") or row.get(f"parent_{level}_id")
    return str(value) if value else None


def _write_json(path: Path, document: Any) -> None:
    path.write_bytes((json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8"))


def _file_records(root: Path) -> list[dict[str, Any]]:
    records = []
    for path in sorted((item for item in root.rglob("*") if item.is_file()), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        data = path.read_bytes()
        records.append({"path": relative, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    return records
