"""M21 hierarchy builder: province → area → region → superregion.

Builds a real 4-level hierarchy from processed provinces plus the land
adjacency graph. Areas cluster at admin-1 granularity (sets of admin-1 codes,
never province hashes) so area IDs stay stable across future M4 density
splits — re-running the builder after a split reassigns child provinces by
``parent_region_id`` lookup with unchanged area IDs.

Regions are one-per-country by default, with micro-states coalesced by
Natural Earth admin-0 subregion within a continent and mega-countries split
by the Natural Earth admin-1 ``region`` attribute (adjacency clustering as a
fallback). Superregions map 1:1 to Natural Earth continents.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from shapely.errors import ShapelyError
from shapely.geometry import mapping, shape
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from gpm import __version__
from gpm.builders.provinces import _first_property, _region_id, _slug_token
from gpm.config import hierarchy_settings, load_profile
from gpm.geo.shapefile import ShapefileReadError, read_zipped_shapefile
from gpm.paths import PROCESSED_DATA_DIR, RAW_DATA_DIR

HIERARCHY_SCHEMA_VERSION = "0.1.0"
HIERARCHY_ID_SCHEME = "hierarchy-sha256-v1"
FALLBACK_CONTINENT = "Unassigned"
LEVEL_ORDER = {"superregion": 0, "region": 1, "area": 2}


class HierarchyBuildError(RuntimeError):
    """Raised when hierarchy generation cannot continue."""


@dataclass(frozen=True)
class HierarchyBuildResult:
    profile_id: str
    province_input: str
    adjacency_input: str
    output: str
    province_output: str | None
    province_count: int
    area_count: int
    region_count: int
    superregion_count: int
    updated_province_count: int
    natural_earth_attributes: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class _LandProvince:
    province_id: str
    country_id: str
    admin1_code: str
    display_name: str
    geometry: BaseGeometry
    area_sq_km: float
    source_lineage: tuple[str, ...]
    license_lineage: tuple[str, ...]


def build_hierarchy(
    profile_id: str,
    *,
    province_input: Path = PROCESSED_DATA_DIR / "provinces.geojson",
    adjacency_input: Path = PROCESSED_DATA_DIR / "adjacency.csv",
    raw_dir: Path = RAW_DATA_DIR,
    output: Path = PROCESSED_DATA_DIR / "hierarchy.geojson",
    update_provinces: bool = True,
    province_output: Path | None = None,
) -> HierarchyBuildResult:
    """Build hierarchy.geojson and enrich provinces with parent fields."""
    profile = load_profile(profile_id)
    settings = hierarchy_settings(profile)

    document = _load_province_document(province_input)
    provinces = _land_provinces(document)
    if not provinces:
        raise HierarchyBuildError(f"Province input has no land provinces: {province_input}")
    if (document.get("gpm") or {}).get("layer_kind") == "location_derived_provinces":
        return _build_location_hierarchy(
            profile_id,
            document=document,
            provinces=provinces,
            settings=settings,
            province_input=province_input,
            adjacency_input=adjacency_input,
            output=output,
            update_provinces=update_provinces,
            province_output=province_output,
        )

    admin1_edges = _collapsed_admin1_edges(adjacency_input, provinces)
    country_attrs, admin1_attrs, ne_available = _natural_earth_attributes(raw_dir)

    # --- areas (per country, at admin-1 granularity) -------------------------
    by_country: dict[str, list[_LandProvince]] = defaultdict(list)
    for province in provinces:
        by_country[province.country_id].append(province)

    areas: list[dict[str, Any]] = []
    node_to_area: dict[tuple[str, str], str] = {}
    for country_id in sorted(by_country):
        members = by_country[country_id]
        nodes = sorted({province.admin1_code for province in members})
        node_geometries = _node_geometries(members)
        clusters = _cluster_nodes(
            nodes,
            admin1_edges.get(country_id, {}),
            node_geometries,
            target_size=settings["area_target_size"],
            min_size=settings["area_min_size"],
            max_size=settings["area_max_size"],
        )
        for cluster in clusters:
            area = _area_entity(country_id, cluster, members, country_attrs)
            areas.append(area)
            for code in cluster:
                node_to_area[(country_id, code)] = area["region_id"]

    # --- regions --------------------------------------------------------------
    regions = _region_entities(
        areas,
        country_attrs,
        admin1_attrs,
        mega_threshold=settings["mega_region_area_threshold"],
        mega_min_area_sq_km=settings["mega_region_min_area_sq_km"],
        region_target_size=settings["region_target_size"],
    )
    area_to_region = {
        area_id: region["region_id"]
        for region in regions
        for area_id in region["properties_member_ids"]
    }

    # --- superregions ----------------------------------------------------------
    superregions = _superregion_entities(regions)
    region_to_superregion = {
        region_id: superregion["region_id"]
        for superregion in superregions
        for region_id in superregion["properties_member_ids"]
    }

    # --- assemble features -----------------------------------------------------
    features: list[dict[str, Any]] = []
    for superregion in superregions:
        features.append(_hierarchy_feature(superregion, parent_id=None))
    for region in regions:
        features.append(
            _hierarchy_feature(region, parent_id=region_to_superregion[region["region_id"]])
        )
    for area in areas:
        region_id = area_to_region[area["region_id"]]
        features.append(
            _hierarchy_feature(
                area,
                parent_id=region_id,
                grandparent_id=region_to_superregion[region_id],
            )
        )
    features.sort(key=lambda f: (LEVEL_ORDER[f["properties"]["region_type"]], f["properties"]["region_id"]))

    generated_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    hierarchy_document = {
        "type": "FeatureCollection",
        "name": "hierarchy",
        "gpm": {
            "schema_version": HIERARCHY_SCHEMA_VERSION,
            "milestone": "M21",
            "id_scheme": HIERARCHY_ID_SCHEME,
            "profile_id": profile_id,
            "generated_at": generated_at,
            "generator_version": __version__,
            "settings": dict(settings),
            "natural_earth_attributes": ne_available,
            "counts": {
                "areas": len(areas),
                "regions": len(regions),
                "superregions": len(superregions),
            },
        },
        "features": features,
    }
    _write_json(output, hierarchy_document)

    # --- enrich provinces in place ---------------------------------------------
    updated_count = 0
    resolved_province_output: Path | None = None
    if update_provinces:
        resolved_province_output = province_output or province_input
        updated_count = _apply_parent_fields(
            document,
            provinces,
            node_to_area=node_to_area,
            area_to_region=area_to_region,
            region_to_superregion=region_to_superregion,
        )
        _write_json(resolved_province_output, document)

    return HierarchyBuildResult(
        profile_id=profile_id,
        province_input=str(province_input),
        adjacency_input=str(adjacency_input),
        output=str(output),
        province_output=None if resolved_province_output is None else str(resolved_province_output),
        province_count=len(provinces),
        area_count=len(areas),
        region_count=len(regions),
        superregion_count=len(superregions),
        updated_province_count=updated_count,
        natural_earth_attributes=ne_available,
    )


def _build_location_hierarchy(
    profile_id: str,
    *,
    document: dict[str, Any],
    provinces: list[_LandProvince],
    settings: dict[str, Any],
    province_input: Path,
    adjacency_input: Path,
    output: Path,
    update_provinces: bool,
    province_output: Path | None,
) -> HierarchyBuildResult:
    """M23 hierarchy path: cluster the derived province graph, never admin codes."""
    by_id = {province.province_id: province for province in provinces}
    graph: dict[str, dict[str, float]] = {province_id: {} for province_id in by_id}
    try:
        with Path(adjacency_input).open("r", encoding="utf-8", newline="") as file:
            for row in csv.DictReader(file):
                if (row.get("adjacency_type") or "").strip() != "land":
                    continue
                left = (row.get("from_province_id") or "").strip()
                right = (row.get("to_province_id") or "").strip()
                if left not in graph or right not in graph:
                    continue
                try:
                    weight = float(row.get("shared_border_km") or 0.0)
                except ValueError:
                    weight = 0.0
                graph[left][right] = graph[left].get(right, 0.0) + weight
                graph[right][left] = graph[right].get(left, 0.0) + weight
    except (OSError, csv.Error) as exc:
        raise HierarchyBuildError(f"Cannot read M23 province adjacency {adjacency_input}: {exc}") from exc

    meta = document.get("gpm") or {}
    era = str(meta.get("start_date") or "undated")
    aggregation_revision = str(meta.get("aggregation_revision") or "1")
    geometry_revision = str(meta.get("geometry_revision") or "1")

    area_groups = _cluster_member_graph(
        sorted(by_id), graph, target=max(1, int(settings["area_target_size"])),
    )
    area_records = [
        _location_hierarchy_record(
            "area", members, by_id, profile_id, era, aggregation_revision, geometry_revision
        )
        for members in area_groups
    ]
    area_by_id = {record["region_id"]: record for record in area_records}
    province_to_area = {
        province_id: record["region_id"]
        for record in area_records for province_id in record["province_ids"]
    }
    area_graph = _collapse_member_graph(graph, province_to_area)
    region_groups = _cluster_member_graph(
        sorted(area_by_id), area_graph, target=max(1, int(settings["region_target_size"])),
    )
    region_records = [
        _location_hierarchy_record_from_children(
            "region", members, area_by_id, profile_id, era, aggregation_revision, geometry_revision
        )
        for members in region_groups
    ]
    region_by_id = {record["region_id"]: record for record in region_records}
    area_to_region = {
        area_id: record["region_id"]
        for record in region_records for area_id in record["member_ids"]
    }
    region_graph = _collapse_member_graph(area_graph, area_to_region)
    super_groups = _cluster_member_graph(
        sorted(region_by_id), region_graph, target=max(1, int(settings["region_target_size"])),
    )
    super_records = [
        _location_hierarchy_record_from_children(
            "superregion", members, region_by_id, profile_id, era, aggregation_revision, geometry_revision
        )
        for members in super_groups
    ]
    region_to_super = {
        region_id: record["region_id"]
        for record in super_records for region_id in record["member_ids"]
    }

    features = []
    for record in super_records:
        features.append(_location_hierarchy_feature(record, None, None))
    for record in region_records:
        features.append(_location_hierarchy_feature(record, region_to_super[record["region_id"]], None))
    for record in area_records:
        parent = area_to_region[record["region_id"]]
        features.append(_location_hierarchy_feature(record, parent, region_to_super[parent]))
    features.sort(key=lambda feature: (LEVEL_ORDER[feature["properties"]["region_type"]], feature["properties"]["region_id"]))
    hierarchy_document = {
        "type": "FeatureCollection", "name": "hierarchy",
        "gpm": {
            "schema_version": HIERARCHY_SCHEMA_VERSION, "milestone": "M23",
            "id_scheme": "location-membership-sha256-v1", "profile_id": profile_id,
            "start_date": era, "aggregation_revision": aggregation_revision,
            "geometry_revision": geometry_revision,
            "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
            "generator_version": __version__, "natural_earth_attributes": False,
            "counts": {"areas": len(area_records), "regions": len(region_records), "superregions": len(super_records)},
        },
        "features": features,
    }
    _write_json(output, hierarchy_document)
    updated = 0
    resolved_output: Path | None = None
    if update_provinces:
        resolved_output = province_output or province_input
        for feature in document["features"]:
            props = feature.get("properties") or {}
            province_id = props.get("province_id")
            if province_id not in province_to_area:
                continue
            area_id = province_to_area[province_id]
            region_id = area_to_region[area_id]
            props["parent_area_id"] = area_id
            props["parent_geo_region_id"] = region_id
            props["parent_superregion_id"] = region_to_super[region_id]
            updated += 1
        _write_json(resolved_output, document)
    return HierarchyBuildResult(
        profile_id=profile_id, province_input=str(province_input), adjacency_input=str(adjacency_input),
        output=str(output), province_output=str(resolved_output) if resolved_output else None,
        province_count=len(provinces), area_count=len(area_records), region_count=len(region_records),
        superregion_count=len(super_records), updated_province_count=updated,
        natural_earth_attributes=False,
    )


def _cluster_member_graph(members: list[str], graph: dict[str, dict[str, float]], *, target: int) -> list[list[str]]:
    remaining = set(members)
    groups: list[list[str]] = []
    while remaining:
        seed = min(remaining)
        group = [seed]
        remaining.remove(seed)
        while len(group) < target:
            candidates = {
                neighbor
                for member in group
                for neighbor in graph.get(member, {})
                if neighbor in remaining
            }
            if not candidates:
                break
            chosen = min(candidates, key=lambda item: (-sum(graph.get(member, {}).get(item, 0.0) for member in group), item))
            group.append(chosen)
            remaining.remove(chosen)
        groups.append(sorted(group))
    return groups


def _collapse_member_graph(graph: dict[str, dict[str, float]], mapping_by_member: dict[str, str]) -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = {group: {} for group in set(mapping_by_member.values())}
    for left, neighbors in graph.items():
        left_group = mapping_by_member[left]
        for right, weight in neighbors.items():
            right_group = mapping_by_member[right]
            if left_group != right_group:
                result[left_group][right_group] = result[left_group].get(right_group, 0.0) + weight
    return result


def _hierarchy_hash(level: str, members: list[str], profile_id: str, era: str,
                    aggregation_revision: str, geometry_revision: str) -> str:
    payload = json.dumps([level, sorted(members), profile_id, era, aggregation_revision, geometry_revision], separators=(",", ":"))
    return f"{level}_{hashlib.sha256(payload.encode()).hexdigest()[:16]}"


def _location_hierarchy_record(level: str, members: list[str], provinces: dict[str, _LandProvince],
                               profile_id: str, era: str, aggregation_revision: str,
                               geometry_revision: str) -> dict[str, Any]:
    return {
        "region_id": _hierarchy_hash(level, members, profile_id, era, aggregation_revision, geometry_revision),
        "member_ids": sorted(members), "province_ids": sorted(members),
        "geometry": unary_union([provinces[item].geometry for item in members]),
        "source_lineage": sorted({value for item in members for value in provinces[item].source_lineage}),
        "license_lineage": sorted({value for item in members for value in provinces[item].license_lineage}),
        "region_type": level,
    }


def _location_hierarchy_record_from_children(level: str, members: list[str], children: dict[str, dict[str, Any]],
                                             profile_id: str, era: str, aggregation_revision: str,
                                             geometry_revision: str) -> dict[str, Any]:
    province_ids = sorted({item for member in members for item in children[member]["province_ids"]})
    return {
        "region_id": _hierarchy_hash(level, members, profile_id, era, aggregation_revision, geometry_revision),
        "member_ids": sorted(members), "province_ids": province_ids,
        "geometry": unary_union([children[item]["geometry"] for item in members]),
        "source_lineage": sorted({value for item in members for value in children[item]["source_lineage"]}),
        "license_lineage": sorted({value for item in members for value in children[item]["license_lineage"]}),
        "region_type": level,
    }


def _location_hierarchy_feature(record: dict[str, Any], parent_id: str | None,
                                grandparent_id: str | None) -> dict[str, Any]:
    return {
        "type": "Feature", "geometry": mapping(record["geometry"]),
        "properties": {
            "region_id": record["region_id"], "display_name": record["region_id"],
            "region_type": record["region_type"], "parent_region_id": parent_id,
            "parent_superregion_id": grandparent_id,
            "province_ids": record["province_ids"], "province_count": len(record["province_ids"]),
            "member_ids": record["member_ids"], "source_lineage": record["source_lineage"],
            "license_lineage": record["license_lineage"],
        },
    }


# ---------------------------------------------------------------------------
# input loading
# ---------------------------------------------------------------------------


def _load_province_document(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise HierarchyBuildError(f"Province input does not exist: {path}") from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise HierarchyBuildError(f"Cannot read province GeoJSON {path}: {exc}") from exc
    if not isinstance(document, dict) or document.get("type") != "FeatureCollection":
        raise HierarchyBuildError(f"Province input must be a GeoJSON FeatureCollection: {path}")
    if not isinstance(document.get("features"), list):
        raise HierarchyBuildError(f"Province GeoJSON features must be an array: {path}")
    return document


def _clean(value: Any) -> str:
    """Strip DBF NUL padding and whitespace from attribute strings."""
    if value is None:
        return ""
    return str(value).replace("\x00", "").strip()


def _land_provinces(document: dict[str, Any]) -> list[_LandProvince]:
    provinces: list[_LandProvince] = []
    for index, feature in enumerate(document["features"]):
        if not isinstance(feature, dict):
            continue
        properties = feature.get("properties")
        if not isinstance(properties, dict) or properties.get("kind") != "land":
            continue
        province_id = _clean(properties.get("province_id"))
        if not province_id:
            raise HierarchyBuildError(f"Land province features[{index}] is missing province_id.")
        country_id = _clean(properties.get("parent_country_id")) or "unassigned"
        admin1_code = _clean(properties.get("parent_region_id")) or country_id
        geometry_mapping = feature.get("geometry")
        try:
            geometry = shape(geometry_mapping)
        except (ShapelyError, TypeError, ValueError) as exc:
            raise HierarchyBuildError(f"Malformed geometry for province {province_id}: {exc}") from exc
        if geometry.is_empty:
            raise HierarchyBuildError(f"Province {province_id} has empty geometry.")
        area = properties.get("area_sq_km")
        provinces.append(
            _LandProvince(
                province_id=province_id,
                country_id=country_id,
                admin1_code=admin1_code,
                display_name=_clean(properties.get("display_name")) or province_id,
                geometry=geometry,
                area_sq_km=float(area) if isinstance(area, (int, float)) else 0.0,
                source_lineage=tuple(properties.get("source_lineage") or ()),
                license_lineage=tuple(properties.get("license_lineage") or ()),
            )
        )
    provinces.sort(key=lambda province: province.province_id)
    return provinces


def _collapsed_admin1_edges(
    adjacency_input: Path, provinces: list[_LandProvince]
) -> dict[str, dict[tuple[str, str], float]]:
    """Collapse province land adjacency onto same-country admin-1 code pairs."""
    node_of = {
        province.province_id: (province.country_id, province.admin1_code)
        for province in provinces
    }
    try:
        file = adjacency_input.open("r", encoding="utf-8", newline="")
    except FileNotFoundError as exc:
        raise HierarchyBuildError(f"Adjacency input does not exist: {adjacency_input}") from exc
    except OSError as exc:
        raise HierarchyBuildError(f"Cannot read adjacency CSV {adjacency_input}: {exc}") from exc
    edges: dict[str, dict[tuple[str, str], float]] = defaultdict(lambda: defaultdict(float))
    with file:
        reader = csv.DictReader(file)
        for row in reader:
            if (row.get("adjacency_type") or "").strip() != "land":
                continue
            from_node = node_of.get((row.get("from_province_id") or "").strip())
            to_node = node_of.get((row.get("to_province_id") or "").strip())
            if from_node is None or to_node is None or from_node == to_node:
                continue
            if from_node[0] != to_node[0]:
                continue  # areas never cross countries
            try:
                weight = float(row.get("shared_border_km") or 0.0)
            except ValueError:
                weight = 0.0
            pair = tuple(sorted((from_node[1], to_node[1])))
            edges[from_node[0]][pair] += weight
    return {country: dict(pairs) for country, pairs in edges.items()}


def _natural_earth_attributes(
    raw_dir: Path,
) -> tuple[dict[str, dict[str, str]], dict[tuple[str, str], dict[str, str]], bool]:
    """Return (country → attrs, (country, admin1 code) → attrs, available).

    Missing raw artifacts degrade gracefully: hierarchy falls back to
    one-region-per-country and a single "Unassigned" continent bucket, which
    keeps sample scaffolds working without Natural Earth downloads.
    """
    admin0_path = raw_dir / "natural_earth" / "ne_10m_admin_0_countries.zip"
    admin1_path = raw_dir / "natural_earth" / "ne_10m_admin_1_states_provinces.zip"
    if not admin0_path.is_file() or not admin1_path.is_file():
        return {}, {}, False
    try:
        admin0_features = read_zipped_shapefile(admin0_path)
        admin1_features = read_zipped_shapefile(admin1_path)
    except ShapefileReadError as exc:
        raise HierarchyBuildError(f"Cannot read Natural Earth attributes: {exc}") from exc

    country_attrs: dict[str, dict[str, str]] = {}
    for feature in admin0_features:
        properties = feature.properties
        country_id = _first_property(properties, "adm0_a3", "iso_a3", "sov_a3", "admin")
        if not country_id:
            continue
        country_attrs[country_id] = {
            "continent": _first_property(properties, "continent") or FALLBACK_CONTINENT,
            "subregion": _first_property(properties, "subregion", "region_wb", "region_un") or "",
            "name": _first_property(properties, "name_en", "name", "admin") or country_id,
        }

    admin1_attrs: dict[tuple[str, str], dict[str, str]] = {}
    for feature in admin1_features:
        properties = feature.properties
        country_id = _first_property(properties, "adm0_a3", "iso_a3", "sov_a3", "admin")
        code = _region_id(properties, "admin1_states_provinces")
        if not country_id or not code:
            continue
        admin1_attrs[(country_id, code)] = {
            "region": _first_property(properties, "region") or "",
            "name": _first_property(properties, "name_en", "name") or code,
        }
    return country_attrs, admin1_attrs, True


# ---------------------------------------------------------------------------
# area clustering
# ---------------------------------------------------------------------------


def _node_geometries(members: list[_LandProvince]) -> dict[str, BaseGeometry]:
    grouped: dict[str, list[BaseGeometry]] = defaultdict(list)
    for province in members:
        grouped[province.admin1_code].append(province.geometry)
    merged: dict[str, BaseGeometry] = {}
    for code, geometries in grouped.items():
        merged[code] = geometries[0] if len(geometries) == 1 else unary_union(geometries)
    return merged


def _cluster_nodes(
    nodes: list[str],
    edges: dict[tuple[str, str], float],
    node_geometries: dict[str, BaseGeometry],
    *,
    target_size: int,
    min_size: int,
    max_size: int,
) -> list[list[str]]:
    """Deterministic greedy agglomeration of admin-1 nodes into areas.

    Seeds are the lexicographically smallest unassigned nodes; clusters grow
    by strongest shared border (ties broken lexicographically) up to
    ``target_size``. Undersized clusters merge into the neighbouring cluster
    with the longest shared border, or by nearest centroid for islands.
    """
    neighbours: dict[str, dict[str, float]] = defaultdict(dict)
    for (a, b), weight in edges.items():
        if a in node_geometries and b in node_geometries:
            neighbours[a][b] = weight
            neighbours[b][a] = weight

    unassigned = set(nodes)
    clusters: list[list[str]] = []
    for seed in nodes:
        if seed not in unassigned:
            continue
        cluster = [seed]
        unassigned.discard(seed)
        while len(cluster) < target_size:
            candidate_weights: dict[str, float] = defaultdict(float)
            for member in cluster:
                for neighbour, weight in neighbours[member].items():
                    if neighbour in unassigned:
                        candidate_weights[neighbour] += weight
            if not candidate_weights:
                break
            best = min(
                candidate_weights,
                key=lambda code: (-candidate_weights[code], code),
            )
            cluster.append(best)
            unassigned.discard(best)
        clusters.append(sorted(cluster))

    # Merge undersized clusters (isolated islands merge by nearest centroid).
    centroids = {code: node_geometries[code].centroid for code in nodes}
    while True:
        clusters.sort(key=lambda cluster: cluster[0])
        small_index = next(
            (
                index
                for index, cluster in sorted(
                    enumerate(clusters), key=lambda item: (len(item[1]), item[1][0])
                )
                if len(cluster) < min_size
            ),
            None,
        )
        if small_index is None or len(clusters) < 2:
            break
        small = clusters[small_index]
        border_weights: dict[int, float] = defaultdict(float)
        for member in small:
            for neighbour, weight in neighbours[member].items():
                for other_index, other in enumerate(clusters):
                    if other_index != small_index and neighbour in other:
                        border_weights[other_index] += weight
        candidates = [
            index
            for index in border_weights
            if len(clusters[index]) + len(small) <= max_size
        ] or list(border_weights)
        if candidates:
            best_index = min(
                candidates,
                key=lambda index: (-border_weights[index], clusters[index][0]),
            )
        else:
            small_centroid = unary_union([centroids[code] for code in small]).centroid
            eligible = [
                index
                for index, other in enumerate(clusters)
                if index != small_index and len(other) + len(small) <= max_size
            ] or [index for index in range(len(clusters)) if index != small_index]
            best_index = min(
                eligible,
                key=lambda index: (
                    round(
                        small_centroid.distance(
                            unary_union([centroids[code] for code in clusters[index]]).centroid
                        ),
                        9,
                    ),
                    clusters[index][0],
                ),
            )
        merged = sorted(clusters[best_index] + small)
        clusters = [
            cluster
            for index, cluster in enumerate(clusters)
            if index not in (small_index, best_index)
        ]
        clusters.append(merged)

    clusters.sort(key=lambda cluster: cluster[0])
    return clusters


# ---------------------------------------------------------------------------
# entity construction
# ---------------------------------------------------------------------------


def _hierarchy_id(prefix: str, slug_parts: list[str], identity: dict[str, Any]) -> str:
    canonical = json.dumps(identity, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]
    label = "-".join(token for token in (_slug_token(part) for part in slug_parts if part) if token)
    if not label:
        label = prefix
    return f"{prefix}_{label}-{digest}"


def _area_entity(
    country_id: str,
    cluster: list[str],
    members: list[_LandProvince],
    country_attrs: dict[str, dict[str, str]],
) -> dict[str, Any]:
    cluster_set = set(cluster)
    provinces = [province for province in members if province.admin1_code in cluster_set]
    identity = {"level": "area", "country_id": country_id, "admin1_codes": list(cluster)}
    area_id = _hierarchy_id("ar", [country_id, cluster[0]], identity)
    geometry = unary_union([province.geometry for province in provinces])
    country_name = country_attrs.get(country_id, {}).get("name", country_id)
    anchor = min(provinces, key=lambda province: (-province.area_sq_km, province.province_id))
    display_name = f"{anchor.display_name} Area"
    return {
        "region_id": area_id,
        "region_type": "area",
        "display_name": display_name,
        "parent_country_id": country_id,
        "country_name": country_name,
        "admin1_codes": list(cluster),
        "province_ids": sorted(province.province_id for province in provinces),
        "geometry": geometry,
        "area_sq_km": round(sum(province.area_sq_km for province in provinces), 3),
        "source_lineage": _merged_lineage(province.source_lineage for province in provinces),
        "license_lineage": _merged_lineage(province.license_lineage for province in provinces),
        "properties_member_ids": [],
    }


def _region_entities(
    areas: list[dict[str, Any]],
    country_attrs: dict[str, dict[str, str]],
    admin1_attrs: dict[tuple[str, str], dict[str, str]],
    *,
    mega_threshold: int,
    mega_min_area_sq_km: int,
    region_target_size: int,
) -> list[dict[str, Any]]:
    by_country: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for area in areas:
        by_country[area["parent_country_id"]].append(area)

    groups: dict[tuple[str, ...], dict[str, Any]] = {}

    def add_group(kind: str, key: tuple[str, ...], display_name: str, country_id: str | None,
                  continent: str, member_areas: list[dict[str, Any]]) -> None:
        identity = {
            "level": "region",
            "kind": kind,
            "key": list(key),
        }
        region_id = _hierarchy_id("rg", [part for part in key], identity)
        groups[(kind, *key)] = {
            "region_id": region_id,
            "region_type": "region",
            "display_name": display_name,
            "parent_country_id": country_id,
            "continent": continent,
            "province_ids": sorted(
                province_id for area in member_areas for province_id in area["province_ids"]
            ),
            "geometry": unary_union([area["geometry"] for area in member_areas]),
            "area_sq_km": round(sum(area["area_sq_km"] for area in member_areas), 3),
            "source_lineage": _merged_lineage(area["source_lineage"] for area in member_areas),
            "license_lineage": _merged_lineage(area["license_lineage"] for area in member_areas),
            "properties_member_ids": sorted(area["region_id"] for area in member_areas),
        }

    micro_by_bucket: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for country_id in sorted(by_country):
        country_areas = sorted(by_country[country_id], key=lambda area: area["region_id"])
        attrs = country_attrs.get(country_id, {})
        continent = attrs.get("continent", FALLBACK_CONTINENT)
        subregion = attrs.get("subregion", "")
        country_name = attrs.get("name", country_id)

        if len(country_areas) < 2 and country_attrs:
            # Micro-state: coalesce by (continent, subregion).
            bucket = (continent, subregion or country_name)
            micro_by_bucket[bucket].extend(country_areas)
            continue

        country_area_sq_km = sum(area["area_sq_km"] for area in country_areas)
        if len(country_areas) >= mega_threshold and country_area_sq_km >= mega_min_area_sq_km:
            split = _split_mega_country(
                country_id,
                country_name,
                country_areas,
                admin1_attrs,
                region_target_size=region_target_size,
            )
            if split is not None:
                for key, display_name, member_areas in split:
                    add_group("attr", key, display_name, country_id, continent, member_areas)
                continue

        add_group("country", (country_id,), country_name, country_id, continent, country_areas)

    for continent, subregion in sorted(micro_by_bucket):
        member_areas = sorted(micro_by_bucket[(continent, subregion)], key=lambda area: area["region_id"])
        add_group("subregion", (continent, subregion), subregion, None, continent, member_areas)

    return sorted(groups.values(), key=lambda region: region["region_id"])


def _split_mega_country(
    country_id: str,
    country_name: str,
    country_areas: list[dict[str, Any]],
    admin1_attrs: dict[tuple[str, str], dict[str, str]],
    *,
    region_target_size: int,
) -> list[tuple[tuple[str, ...], str, list[dict[str, Any]]]] | None:
    """Split a mega-country into regions by the NE admin-1 region attribute.

    Falls back to deterministic chunking over sorted areas when the attribute
    is too sparse; returns None when no split is possible (single region).
    """
    votes_available = 0
    votes_total = 0
    area_region_attr: dict[str, str] = {}
    for area in country_areas:
        counts: dict[str, int] = defaultdict(int)
        for code in area["admin1_codes"]:
            votes_total += 1
            attr = admin1_attrs.get((country_id, code), {}).get("region", "")
            if attr:
                votes_available += 1
                counts[attr] += 1
        if counts:
            area_region_attr[area["region_id"]] = min(
                counts, key=lambda name: (-counts[name], name)
            )

    if votes_total and votes_available / votes_total >= 0.5 and len(set(area_region_attr.values())) >= 2:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for area in country_areas:
            attr = area_region_attr.get(area["region_id"])
            if attr is None:
                # Attach attribute-less areas to the first group deterministically.
                attr = min(set(area_region_attr.values()))
            grouped[attr].append(area)
        return [
            ((country_id, attr), f"{country_name}: {attr}", grouped[attr])
            for attr in sorted(grouped)
        ]

    # Fallback: chunk sorted areas into contiguous groups of region_target_size.
    if len(country_areas) < 2 * region_target_size:
        return None
    chunks: list[tuple[tuple[str, ...], str, list[dict[str, Any]]]] = []
    ordered = sorted(country_areas, key=lambda area: area["region_id"])
    for index in range(0, len(ordered), region_target_size):
        chunk = ordered[index : index + region_target_size]
        if len(chunk) < max(2, region_target_size // 2) and chunks:
            # Fold a trailing runt into the previous chunk.
            key, name, previous = chunks[-1]
            chunks[-1] = (key, name, previous + chunk)
            continue
        first_area = chunk[0]
        key = (country_id, first_area["admin1_codes"][0])
        chunks.append((key, f"{country_name}: {first_area['display_name']}", chunk))
    return chunks if len(chunks) >= 2 else None


def _superregion_entities(regions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_continent: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for region in regions:
        by_continent[region.get("continent") or FALLBACK_CONTINENT].append(region)
    superregions: list[dict[str, Any]] = []
    for continent in sorted(by_continent):
        members = sorted(by_continent[continent], key=lambda region: region["region_id"])
        identity = {"level": "superregion", "continent": continent}
        superregions.append(
            {
                "region_id": _hierarchy_id("sr", [continent], identity),
                "region_type": "superregion",
                "display_name": continent,
                "parent_country_id": None,
                "province_ids": sorted(
                    province_id for region in members for province_id in region["province_ids"]
                ),
                "geometry": unary_union([region["geometry"] for region in members]),
                "area_sq_km": round(sum(region["area_sq_km"] for region in members), 3),
                "source_lineage": _merged_lineage(region["source_lineage"] for region in members),
                "license_lineage": _merged_lineage(region["license_lineage"] for region in members),
                "properties_member_ids": sorted(region["region_id"] for region in members),
            }
        )
    return sorted(superregions, key=lambda superregion: superregion["region_id"])


def _hierarchy_feature(
    entity: dict[str, Any],
    *,
    parent_id: str | None,
    grandparent_id: str | None = None,
) -> dict[str, Any]:
    geometry = entity["geometry"]
    label_point = geometry.representative_point()
    region_type = entity["region_type"]
    properties: dict[str, Any] = {
        "region_id": entity["region_id"],
        "display_name": entity["display_name"],
        "region_type": region_type,
        "parent_country_id": entity.get("parent_country_id"),
        "parent_region_id": parent_id if region_type == "area" else None,
        "parent_superregion_id": (
            parent_id if region_type == "region" else grandparent_id if region_type == "area" else None
        ),
        "province_ids": entity["province_ids"],
        "province_count": len(entity["province_ids"]),
        "member_region_ids": entity["properties_member_ids"],
        "area_sq_km": entity["area_sq_km"],
        "label_point": [round(label_point.x, 6), round(label_point.y, 6)],
        "source_lineage": entity["source_lineage"],
        "license_lineage": entity["license_lineage"],
    }
    if region_type == "area":
        properties["admin1_codes"] = entity["admin1_codes"]
    return {
        "type": "Feature",
        "geometry": mapping(geometry),
        "properties": properties,
    }


def _apply_parent_fields(
    document: dict[str, Any],
    provinces: list[_LandProvince],
    *,
    node_to_area: dict[tuple[str, str], str],
    area_to_region: dict[str, str],
    region_to_superregion: dict[str, str],
) -> int:
    node_of = {
        province.province_id: (province.country_id, province.admin1_code)
        for province in provinces
    }
    updated = 0
    for feature in document["features"]:
        if not isinstance(feature, dict):
            continue
        properties = feature.get("properties")
        if not isinstance(properties, dict) or properties.get("kind") != "land":
            continue
        province_id = _clean(properties.get("province_id"))
        node = node_of.get(province_id)
        if node is None:
            continue
        area_id = node_to_area[node]
        region_id = area_to_region[area_id]
        properties["parent_area_id"] = area_id
        properties["parent_geo_region_id"] = region_id
        properties["parent_superregion_id"] = region_to_superregion[region_id]
        updated += 1
    gpm_block = document.get("gpm")
    if isinstance(gpm_block, dict):
        gpm_block["hierarchy"] = {
            "milestone": "M21",
            "id_scheme": HIERARCHY_ID_SCHEME,
            "updated_province_count": updated,
        }
    return updated


def _merged_lineage(items: Any) -> list[str]:
    merged: set[str] = set()
    for lineage in items:
        merged.update(entry for entry in lineage if entry)
    return sorted(merged)


def _write_json(path: Path, document: dict[str, Any]) -> None:
    """Atomic write: the enrichment rewrites provinces.geojson in place, and a
    crash mid-write must not truncate the primary build artifact."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n"
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp_path.write_text(payload, encoding="utf-8")
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()
