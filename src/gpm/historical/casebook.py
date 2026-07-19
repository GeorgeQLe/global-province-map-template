"""M25A historical hard-case fixture loader and execution harness.

This module deliberately produces a small test projection, not the M25B runtime
pack.  It makes the casebook executable without implying that a global era has
passed either research or runtime certification.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from shapely.geometry import Point, mapping, shape

from gpm.schemas import SchemaValidationError, validate_historical_territory_status


REQUIRED_CLASSES = {
    "sovereign_microstate",
    "detached_sovereign_territory",
    "foreign_enclave_exclave",
    "free_protected_city",
    "condominium_international_zone",
    "composite_dynastic_territory",
    "dependency_mandate_concession",
    "disputed_territory",
}
REQUIRED_ERAS = {"1444", "1836", "1914", "1936"}
REQUIRED_SURFACES = {
    "schema",
    "canonical_build",
    "runtime_pack",
    "visual",
    "picking",
    "lod",
    "adjacency",
    "save_migration",
}


class CasebookError(ValueError):
    """Raised when an M25A fixture or expectation fails."""


@dataclass(frozen=True)
class CaseExecution:
    fixture_id: str
    case_class: str
    era: str
    surfaces: tuple[str, ...]
    runtime_bytes: bytes
    visual_feature_count: int


def load_casebook(path: Path) -> dict[str, Any]:
    """Load and validate the casebook envelope and its canonical documents."""
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CasebookError(f"cannot load historical casebook {path}: {exc}") from exc
    if not isinstance(document, dict):
        raise CasebookError("casebook must be a JSON object")
    if document.get("schema_version") != "0.1.0":
        raise CasebookError("casebook.schema_version must be 0.1.0")
    if document.get("fixture_type") != "historical-hard-case-casebook":
        raise CasebookError("casebook.fixture_type is invalid")
    if document.get("research_status") != "synthetic-contract-fixture":
        raise CasebookError("casebook must be labelled synthetic-contract-fixture")
    cases = document.get("cases")
    if not isinstance(cases, list) or not cases:
        raise CasebookError("casebook.cases must be a non-empty array")

    seen_ids: set[str] = set()
    classes: set[str] = set()
    eras: set[str] = set()
    for index, case in enumerate(cases):
        path_label = f"casebook.cases[{index}]"
        if not isinstance(case, dict):
            raise CasebookError(f"{path_label} must be an object")
        required = {"fixture_id", "case_class", "era", "canonical", "expectations"}
        missing = sorted(required - set(case))
        if missing:
            raise CasebookError(f"{path_label} missing: {', '.join(missing)}")
        fixture_id = case["fixture_id"]
        if not isinstance(fixture_id, str) or not fixture_id:
            raise CasebookError(f"{path_label}.fixture_id must be a non-empty string")
        if fixture_id in seen_ids:
            raise CasebookError(f"duplicate fixture_id: {fixture_id}")
        seen_ids.add(fixture_id)
        classes.add(str(case["case_class"]))
        eras.add(str(case["era"]))
        try:
            validate_historical_territory_status(case["canonical"])
        except SchemaValidationError as exc:
            raise CasebookError(f"{fixture_id}: {exc}") from exc
        surfaces = case["expectations"].get("surfaces")
        if not isinstance(surfaces, list) or set(surfaces) != REQUIRED_SURFACES:
            raise CasebookError(f"{fixture_id}: expectations.surfaces must cover every M25A surface")

    if classes != REQUIRED_CLASSES:
        raise CasebookError(f"casebook classes differ: missing={sorted(REQUIRED_CLASSES - classes)} extra={sorted(classes - REQUIRED_CLASSES)}")
    if eras != REQUIRED_ERAS:
        raise CasebookError(f"casebook eras must cover {sorted(REQUIRED_ERAS)}")
    return document


def project_fixture_runtime(canonical: dict[str, Any]) -> dict[str, Any]:
    """Derive a deterministic, test-only dense-index projection."""
    components = sorted(canonical["components"], key=lambda row: row["territory_component_id"])
    units = sorted(canonical["political_units"], key=lambda row: row["political_unit_id"])
    provinces = sorted(canonical["provinces"], key=lambda row: row["province_id"])
    statuses = sorted(
        canonical["statuses"],
        key=lambda row: (
            row["subject_id"],
            row["relationship"],
            row["actor_political_unit_id"],
            row["valid_from"],
        ),
    )
    return {
        "format": "m25a-fixture-projection-not-runtime-pack",
        "start_date": canonical["start_date"],
        "components": [
            {
                "dense_index": index,
                "territory_component_id": row["territory_component_id"],
                "political_unit_id": row["political_unit_id"],
                "province_id": row["province_id"],
            }
            for index, row in enumerate(components)
        ],
        "political_units": [
            {"dense_index": index, "political_unit_id": row["political_unit_id"]}
            for index, row in enumerate(units)
        ],
        "provinces": [
            {"dense_index": index, "province_id": row["province_id"]}
            for index, row in enumerate(provinces)
        ],
        "statuses": [
            {
                "dense_index": index,
                "subject_id": row["subject_id"],
                "relationship": row["relationship"],
                "actor_political_unit_id": row["actor_political_unit_id"],
            }
            for index, row in enumerate(statuses)
        ],
    }


def execute_casebook(document: dict[str, Any]) -> tuple[CaseExecution, ...]:
    """Execute every declared schema/canonical/runtime/visual interaction test."""
    executions: list[CaseExecution] = []
    for case in document["cases"]:
        canonical = case["canonical"]
        expected = case["expectations"]
        component_rows = {row["territory_component_id"]: row for row in canonical["components"]}
        component_shapes = {key: shape(row["geometry"]) for key, row in component_rows.items()}

        expected_order = expected["component_order"]
        actual_order = sorted(component_rows)
        _expect(actual_order == expected_order, case, "canonical component ordering changed")

        projection = project_fixture_runtime(canonical)
        runtime_bytes = _canonical_bytes(projection)
        _expect(runtime_bytes == _canonical_bytes(project_fixture_runtime(canonical)), case, "runtime projection is not byte deterministic")
        _expect(
            [row["territory_component_id"] for row in projection["components"]] == expected_order,
            case,
            "runtime component mapping lost identity",
        )

        visual = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "territory_component_id": component_id,
                        "province_id": component_rows[component_id]["province_id"],
                    },
                    "geometry": mapping(component_shapes[component_id]),
                }
                for component_id in actual_order
            ],
        }
        _expect(len(visual["features"]) == len(component_rows), case, "visual projection omitted a component")

        for pick in expected["picks"]:
            point = Point(pick["point"])
            hits = sorted(key for key, geometry in component_shapes.items() if geometry.covers(point))
            _expect(hits == [pick["territory_component_id"]], case, f"picking mismatch at {pick['point']}")
            row = component_rows[hits[0]]
            _expect(row["province_id"] == pick["province_id"], case, "picking returned the wrong province")

        for tolerance in expected["lod_tolerances"]:
            for component_id, geometry in component_shapes.items():
                simplified = geometry.simplify(tolerance, preserve_topology=True)
                _expect(not simplified.is_empty and simplified.is_valid and simplified.area > 0, case, f"LOD removed {component_id}")
        for component_id in expected["supplementary_symbol_component_ids"]:
            _expect(component_id in component_shapes, case, f"LOD symbol references unknown component {component_id}")

        actual_adjacency: set[tuple[str, str]] = set()
        ids = sorted(component_shapes)
        for left_index, left_id in enumerate(ids):
            for right_id in ids[left_index + 1 :]:
                shared = component_shapes[left_id].boundary.intersection(component_shapes[right_id].boundary)
                if shared.length > 0:
                    actual_adjacency.add((left_id, right_id))
        expected_adjacency = {tuple(sorted(pair)) for pair in expected["adjacent_component_pairs"]}
        _expect(actual_adjacency == expected_adjacency, case, "typed adjacency expectation changed")

        province_ids = {row["province_id"] for row in canonical["provinces"]}
        migration = expected["save_migration"]
        for saved_id in migration["saved_province_ids"]:
            target = migration["province_id_map"].get(saved_id, saved_id)
            _expect(target in province_ids, case, f"save migration cannot resolve {saved_id}")

        executions.append(
            CaseExecution(
                fixture_id=case["fixture_id"],
                case_class=case["case_class"],
                era=case["era"],
                surfaces=tuple(sorted(expected["surfaces"])),
                runtime_bytes=runtime_bytes,
                visual_feature_count=len(visual["features"]),
            )
        )
    return tuple(executions)


def _canonical_bytes(document: dict[str, Any]) -> bytes:
    return (json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _expect(condition: bool, case: dict[str, Any], message: str) -> None:
    if not condition:
        raise CasebookError(f"{case['fixture_id']}: {message}")
