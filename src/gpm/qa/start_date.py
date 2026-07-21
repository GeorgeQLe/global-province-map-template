"""M24 start-date research-pass contract validation."""

from __future__ import annotations

import hashlib
import csv
import json
import math
import re
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any, Callable

from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform as shapely_transform, unary_union
from shapely.strtree import STRtree

from gpm.schemas import (
    SchemaValidationError,
    WORLDWIDE_M49_SUBREGIONS,
    validate_historical_boundary_registry,
    validate_historical_territory_status,
    validate_location_assignments,
    validate_polity_gazetteer,
    validate_spatial_golden_borders,
    validate_start_date_changelog,
    validate_start_date_coverage,
    validate_start_date_pass_manifest,
    validate_start_date_qa_report,
    validate_start_date_source_manifest,
)


class StartDateQAError(RuntimeError):
    """Raised when an M24 pass cannot be loaded or checked."""


@dataclass(frozen=True)
class StartDateQAResult:
    pass_id: str
    start_date: str
    status: str
    artifact_count: int
    error_count: int
    warning_count: int
    report_output: str

    @property
    def passed(self) -> bool:
        return self.status == "pass"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_ARTIFACT_VALIDATORS: dict[str, Callable[[dict[str, Any]], None]] = {
    "source_manifest": validate_start_date_source_manifest,
    "boundary_registry": validate_historical_boundary_registry,
    "polity_gazetteer": validate_polity_gazetteer,
    "location_assignments": validate_location_assignments,
    "golden_borders": validate_spatial_golden_borders,
    "coverage_matrix": validate_start_date_coverage,
    "changelog": validate_start_date_changelog,
    "canonical_historical_status": validate_historical_territory_status,
    "world_coverage_mask": lambda document: _validate_world_coverage_mask(document),
    "anomaly_inventory": lambda document: validate_anomaly_inventory(document),
}
_DOSSIER_SECTIONS = (
    "scope", "research questions", "citations", "transformations and conflicts",
    "exclusions", "uncertainty",
)
HISTORICAL_ANOMALY_TYPES = frozenset({
    "microstate", "detached-territory", "enclave-exclave", "free-protected-city",
    "composite-realm", "dependency", "condominium", "concession", "claim",
    "disputed-area", "non-state-territory",
})
ANOMALY_CENSUS_STATUSES = frozenset({"resolved_cases", "reviewed_none_found"})


def run_start_date_qa(
    *, pass_dir: Path, manifest_input: Path | None = None, report_output: Path | None = None,
    pending_review: bool = False,
) -> StartDateQAResult:
    """Validate one independently releasable M24 research pass, fail closed."""
    root = Path(pass_dir).resolve()
    manifest_path = Path(manifest_input).resolve() if manifest_input else root / "pass_manifest.json"
    manifest = _load_json(manifest_path, "Pass manifest")
    try:
        validate_start_date_pass_manifest(manifest)
    except SchemaValidationError as exc:
        raise StartDateQAError(f"Invalid pass manifest {manifest_path}: {exc}") from exc

    findings: list[dict[str, Any]] = []
    documents: dict[str, dict[str, Any]] = {}
    artifact_paths: dict[str, Path] = {}
    geometry: dict[str, Any] | None = None
    for kind, record in manifest["artifacts"].items():
        path = _contained_path(root, record["path"], kind, findings)
        if path is None:
            continue
        artifact_paths[kind] = path
        if path.is_symlink():
            _finding(findings, "SYMLINK_ARTIFACT", "error", f"{kind} may not be a symlink.", [kind])
            continue
        if not path.is_file():
            _finding(findings, "MISSING_ARTIFACT", "error", f"{kind}: {path}", [kind])
            continue
        if _sha256(path) != record["sha256"].lower():
            _finding(findings, "CHECKSUM_MISMATCH", "error", f"Checksum mismatch for {kind}.", [kind])
        if kind == "dossier":
            _check_dossier(path, findings)
            continue
        try:
            document = _load_json(path, kind.replace("_", " ").title())
            if kind == "full_build_geometry":
                _validate_full_build(document)
                geometry = document
            else:
                _ARTIFACT_VALIDATORS[kind](document)
                documents[kind] = document
            if document.get("artifact_version") != record["version"]:
                _finding(findings, "ARTIFACT_VERSION_MISMATCH", "error", f"{kind} version does not match its manifest record.", [kind])
        except (StartDateQAError, SchemaValidationError) as exc:
            _finding(findings, "INVALID_ARTIFACT", "error", f"{kind}: {exc}", [kind])

    path_owners: dict[Path, list[str]] = {}
    for kind, path in artifact_paths.items():
        path_owners.setdefault(path.resolve(), []).append(kind)
    for owners in path_owners.values():
        if len(owners) > 1:
            _finding(findings, "DUPLICATE_ARTIFACT_PATH", "error", "Multiple artifact roles use the same file.", sorted(owners))

    assertion_results: list[dict[str, Any]] = []
    expected_documents = set(manifest["artifacts"]).intersection(_ARTIFACT_VALIDATORS)
    if set(documents) == expected_documents and geometry is not None:
        if manifest["schema_version"] in {"0.2.0", "0.3.0"}:
            _check_derived_source_artifacts(root, documents["source_manifest"], findings)
            _check_release_sidecars(root, manifest, documents["location_assignments"], geometry, findings)
        _check_fabric_sidecars(root, manifest, documents["location_assignments"], geometry, findings)
        assertion_results = _check_cross_artifact_contract(manifest, documents, geometry, findings)
        if manifest["schema_version"] == "0.3.0":
            _check_global_contract(root, manifest, documents, geometry, findings)

    if pending_review:
        if manifest.get("schema_version") != "0.3.0":
            raise StartDateQAError("Pending-review preflight is restricted to schema 0.3.0 worldwide passes")
        review_codes = {"INVALID_INDEPENDENT_REVIEW"}
        for finding in findings:
            if finding["severity"] == "error" and finding["code"] in review_codes:
                finding["severity"] = "warning"
                finding["message"] = "Pending independent review gate: " + finding["message"]
    findings.sort(key=lambda item: (item["severity"] != "error", item["code"], item["affected_ids"]))
    assertion_results.sort(key=lambda item: item["assertion_id"])
    errors = sum(item["severity"] == "error" for item in findings)
    warnings = sum(item["severity"] == "warning" for item in findings)
    status = "fail" if errors else "pass"
    out_path = Path(report_output) if report_output else root / "start_date_qa.json"
    report = {
        "schema_version": manifest["schema_version"], "report_type": "start_date_research_qa",
        "milestone": "M25C" if manifest["schema_version"] == "0.3.0" else ("M25" if manifest["schema_version"] in {"0.2.0", "0.3.0"} else "M24"),
        "pass_id": manifest["pass_id"], "start_date": manifest["start_date"], "status": status,
        "inputs": {"pass_dir": str(root), "manifest": str(manifest_path)},
        "summary": {"artifact_count": len(artifact_paths), "error_count": errors, "warning_count": warnings},
        "assertion_results": assertion_results, "findings": findings,
    }
    validate_start_date_qa_report(report)
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except OSError as exc:
        raise StartDateQAError(f"Cannot write M24 QA report {out_path}: {exc}") from exc
    return StartDateQAResult(manifest["pass_id"], manifest["start_date"], status, len(artifact_paths), errors, warnings, str(out_path))


def _check_cross_artifact_contract(
    manifest: dict[str, Any], documents: dict[str, dict[str, Any]], geometry: dict[str, Any], findings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    expected = (manifest["pass_id"], manifest["start_date"])
    for kind, document in {**documents, "full_build_geometry": geometry}.items():
        if (document.get("pass_id"), document.get("start_date")) != expected:
            _finding(findings, "PASS_IDENTITY_MISMATCH", "error", f"{kind} does not identify {expected}.", [kind])
    if geometry["geometry_revision"] != manifest["geometry_revision"]:
        _finding(findings, "GEOMETRY_REVISION_MISMATCH", "error", "Full build does not use the pinned geometry revision.", [])

    source_records = {item["source_id"]: item for item in documents["source_manifest"]["sources"]}
    sources = set(source_records)
    polity_records = {item["polity_id"]: item for item in documents["polity_gazetteer"]["polities"]}
    polities = set(polity_records)
    negative_reference_ids = {
        boundary_id
        for assertion in documents["golden_borders"]["assertions"]
        if assertion["expectation"] == "negative_anachronism"
        for boundary_id in assertion["boundary_feature_ids"]
    }
    boundary_records: dict[str, dict[str, Any]] = {}
    for feature in documents["boundary_registry"]["features"]:
        props = feature["properties"]
        boundary_records[props["feature_id"]] = feature
        owner = props["feature_id"]
        _unknown_refs(findings, "UNKNOWN_BOUNDARY_SOURCE", props["source_ids"], sources, owner)
        _unknown_refs(findings, "UNKNOWN_BOUNDARY_POLITY", list(props["side_polity_ids"].values()), polities, owner)
        if owner not in negative_reference_ids:
            _check_temporal(findings, owner, props["valid_from"], props["valid_to"], manifest["start_date"], "BOUNDARY_DATE_OUT_OF_RANGE")
        if manifest["start_date"] not in props["start_date_programs"]:
            _finding(findings, "BOUNDARY_NOT_APPLICABLE", "error", f"{owner} omits this start-date program.", [owner])
        if props["classification"] == "hard_constraint":
            unreviewed = [s for s in props["source_ids"] if s in source_records and source_records[s]["review_status"] != "reviewed"]
            if unreviewed:
                _finding(findings, "UNREVIEWED_HARD_CONSTRAINT", "error", f"Hard constraint {owner} uses unreviewed sources.", [owner, *unreviewed])
            if manifest["schema_version"] in {"0.2.0", "0.3.0"} and owner not in negative_reference_ids:
                _check_v2_hard_boundary(findings, owner, props, source_records, manifest["start_date"])
    if manifest["schema_version"] in {"0.2.0", "0.3.0"}:
        negative_geometries = [
            shape(boundary_records[feature_id]["geometry"])
            for feature_id in negative_reference_ids if feature_id in boundary_records
        ]
        for owner, feature in boundary_records.items():
            if owner in negative_reference_ids or feature["properties"]["classification"] != "hard_constraint":
                continue
            geometry_value = shape(feature["geometry"])
            if any(geometry_value.equals(reference) for reference in negative_geometries):
                _finding(findings, "COPIED_NEGATIVE_CONTROL_GEOMETRY", "error", f"Hard boundary {owner} duplicates a forbidden modern outline.", [owner])

    relationship_ids: set[str] = set()
    for polity in polity_records.values():
        owner = polity["polity_id"]
        _unknown_refs(findings, "UNKNOWN_POLITY_SOURCE", polity["source_ids"], sources, owner)
        _check_temporal(findings, owner, polity["valid_from"], polity["valid_to"], manifest["start_date"], "POLITY_DATE_OUT_OF_RANGE")
        for relationship in polity["relationships"]:
            rid = relationship["relationship_id"]
            if rid in relationship_ids:
                _finding(findings, "DUPLICATE_RELATIONSHIP_ID", "error", f"Duplicate relationship ID {rid}.", [rid])
            relationship_ids.add(rid)
            _unknown_refs(findings, "UNKNOWN_RELATIONSHIP_POLITY", [relationship["target_polity_id"]], polities, owner)
            _unknown_refs(findings, "UNKNOWN_RELATIONSHIP_SOURCE", relationship["source_ids"], sources, rid)
            _check_temporal(findings, rid, relationship["valid_from"], relationship["valid_to"], manifest["start_date"], "RELATIONSHIP_DATE_OUT_OF_RANGE")

    assignments = documents["location_assignments"]
    if assignments["fabric_revision"] != manifest["fabric_revision"]:
        _finding(findings, "FABRIC_REVISION_MISMATCH", "error", "Assignments do not use the pinned M23 fabric revision.", [])
    locations: set[str] = set()
    provinces: set[str] = set()
    location_to_province: dict[str, str] = {}
    province_to_polities: dict[str, set[str]] = {}
    for row in assignments["assignments"]:
        locations.update(row["location_ids"]); provinces.add(row["province_id"])
        location_to_province.update({location: row["province_id"] for location in row["location_ids"]})
        province_to_polities.setdefault(row["province_id"], set()).update(row["polity_ids"])
        _unknown_refs(findings, "UNKNOWN_ASSIGNMENT_POLITY", row["polity_ids"], polities, row["assignment_id"])
        _unknown_refs(findings, "UNKNOWN_ASSIGNMENT_SOURCE", row["source_ids"], sources, row["assignment_id"])
        if manifest["schema_version"] in {"0.2.0", "0.3.0"}:
            typed = [row["sovereign_polity_id"], row["owner_polity_id"], row["controller_polity_id"], *row["core_polity_ids"], *row["claim_polity_ids"], *row["dispute_polity_ids"]]
            _unknown_refs(findings, "UNKNOWN_TYPED_POLITICS_POLITY", typed, polities, row["assignment_id"])
            if row["region_id"] in set(manifest["scope"]["priority_regions"]) and not row.get("hierarchy"):
                _finding(findings, "MISSING_HIERARCHY_MAPPING", "error", "Priority-region assignment lacks hierarchy mapping.", [row["assignment_id"]])
    for polity in polity_records.values():
        _unknown_refs(findings, "UNKNOWN_CAPITAL_LOCATION", polity["capital_location_ids"], locations, polity["polity_id"])
    for request in assignments["targeted_split_requests"]:
        _unknown_refs(findings, "UNKNOWN_SPLIT_LOCATION", request["location_ids"], locations, request["request_id"])
        _unknown_refs(findings, "UNKNOWN_SPLIT_SOURCE", request["source_ids"], sources, request["request_id"])

    build_features = {feature["properties"]["feature_id"]: shape(feature["geometry"]) for feature in geometry["features"]}
    missing_provinces = sorted(provinces - build_features.keys())
    if missing_provinces:
        _finding(findings, "MISSING_BUILD_PROVINCE", "error", "Assigned provinces are absent from the full build.", missing_provinces)
    results = _execute_assertions(documents["golden_borders"], build_features, boundary_records, findings)
    result_by_id = {item["assertion_id"]: item for item in results}

    priority = set(manifest["scope"]["priority_regions"])
    assertions = documents["golden_borders"]["assertions"]
    capital_locations = {location for polity in polity_records.values() for location in polity["capital_location_ids"]}
    for assertion in assertions:
        if manifest["schema_version"] == "0.3.0":
            _unknown_refs(
                findings, "UNKNOWN_TOLERANCE_SOURCE",
                assertion["tolerance_policy"]["source_ids"], sources, assertion["assertion_id"],
            )
        if assertion["expectation"] == "positive":
            soft = [
                boundary_id for boundary_id in assertion["boundary_feature_ids"]
                if boundary_records[boundary_id]["properties"]["classification"] != "hard_constraint"
            ]
            if soft:
                _finding(findings, "POSITIVE_ASSERTION_USES_SOFT_EVIDENCE", "error", f"{assertion['assertion_id']} relies on non-constraint evidence.", [assertion["assertion_id"], *soft])
            if manifest["schema_version"] in {"0.2.0", "0.3.0"} and assertion["spatial_relation"] == "border_matches_boundary_hausdorff_km_lte":
                minimum = max(boundary_records[boundary_id]["properties"].get("error_budget_km", 0.0) for boundary_id in assertion["boundary_feature_ids"])
                if assertion["tolerance"] < minimum:
                    _finding(findings, "GOLDEN_TOLERANCE_BELOW_ERROR_BUDGET", "error", f"{assertion['assertion_id']} tolerance is below its measured error budget.", [assertion["assertion_id"]])
        if assertion["assertion_type"] == "capital":
            capital, province = assertion["subject_ids"]
            if capital not in capital_locations:
                _finding(findings, "UNKNOWN_ASSERTED_CAPITAL", "error", f"{assertion['assertion_id']} does not reference a gazetteer capital location.", [assertion["assertion_id"]])
            if location_to_province.get(capital) != province:
                _finding(findings, "CAPITAL_ASSIGNMENT_MISMATCH", "error", f"{assertion['assertion_id']} does not test the capital's assigned province.", [assertion["assertion_id"], capital, province])
        elif assertion["assertion_type"] == "border":
            sides = set(boundary_records[assertion["boundary_feature_ids"][0]]["properties"]["side_polity_ids"].values())
            subject_polities = [province_to_polities.get(subject, set()) for subject in assertion["subject_ids"]]
            if not all(subject_polities) or not all(any(side in polities for side in sides) for polities in subject_polities) or not sides.issubset(set().union(*subject_polities)):
                _finding(findings, "BORDER_SIDE_ASSIGNMENT_MISMATCH", "error", f"{assertion['assertion_id']} subjects do not represent both dated boundary sides.", [assertion["assertion_id"]])
    for region in sorted(priority):
        region_items = [a for a in assertions if a["region_id"] == region]
        for kind in ("border", "capital"):
            if not any(a["assertion_type"] == kind and a["expectation"] == "positive" for a in region_items):
                _finding(findings, f"MISSING_POSITIVE_{kind.upper()}_ASSERTION", "error", f"Priority region {region} needs a positive {kind} assertion.", [region])
        if not any(a["expectation"] == "negative_anachronism" for a in region_items):
            _finding(findings, "MISSING_NEGATIVE_ANACHRONISM", "error", f"Priority region {region} needs a negative-anachronism assertion.", [region])

    required_layers = {"geometry", "politics", "hierarchy", "gazetteer_relationships"}
    rows = {(item["region_id"], item["layer"]): item for item in documents["coverage_matrix"]["coverage"]}
    for region in manifest["scope"]["regions"]:
        for layer in required_layers:
            if (region, layer) not in rows:
                _finding(findings, "MISSING_COVERAGE_ROW", "error", f"Missing coverage for {region}/{layer}.", [region, layer])
    if manifest["schema_version"] == "0.2.0":
        required_grades = {"geometry": "B", "politics": "B", "gazetteer_relationships": "B", "hierarchy": "C"}
        for region in manifest["scope"]["priority_regions"]:
            for layer, grade in required_grades.items():
                row = rows.get((region, layer))
                if row is not None and row["grade"] != grade:
                    _finding(findings, "M25_COVERAGE_GRADE_MISMATCH", "error", f"{region}/{layer} must be grade {grade}.", [region, layer])
    assertion_defs = {a["assertion_id"]: a for a in assertions}
    for (region, layer), row in rows.items():
        _unknown_refs(findings, "UNKNOWN_COVERAGE_SOURCE", row["source_ids"], sources, region)
        _unknown_refs(findings, "UNKNOWN_COVERAGE_ASSERTION", row["assertion_ids"], set(assertion_defs), region)
        if row["grade"] == "A":
            reviewed = bool(row["source_ids"]) and all(s in source_records and source_records[s]["review_status"] == "reviewed" for s in row["source_ids"])
            scoped = bool(row["assertion_ids"]) and all(assertion_defs[a]["region_id"] == region and assertion_defs[a]["layer"] == layer for a in row["assertion_ids"] if a in assertion_defs)
            passing = all(result_by_id.get(a, {}).get("status") == "pass" for a in row["assertion_ids"])
            if not (reviewed and scoped and passing):
                _finding(findings, "UNCERTIFIED_A_GRADE", "error", f"A grade for {region}/{layer} is not supported by matching reviewed evidence and executed gates.", [region, layer])
        elif row["grade"] == "B":
            if not row["known_gaps"]:
                _finding(findings, "UNDOCUMENTED_GRADE_GAP", "error", f"B grade for {region}/{layer} must document gaps.", [region, layer])
            reviewed = bool(row["source_ids"]) and all(s in source_records and source_records[s]["review_status"] == "reviewed" for s in row["source_ids"])
            scoped = bool(row["assertion_ids"]) and all(assertion_defs[a]["region_id"] == region and assertion_defs[a]["layer"] == layer for a in row["assertion_ids"] if a in assertion_defs)
            passing = all(result_by_id.get(a, {}).get("status") == "pass" for a in row["assertion_ids"])
            if not (reviewed and scoped and passing):
                _finding(findings, "UNCERTIFIED_B_GRADE", "error", f"B grade for {region}/{layer} lacks reviewed, scoped, passing reconstruction evidence.", [region, layer])
        elif row["grade"] == "C" and not row["known_gaps"]:
            _finding(findings, "UNDOCUMENTED_GRADE_GAP", "error", f"C grade for {region}/{layer} must document gaps.", [region, layer])
        elif row["grade"] == "U" and (row["source_ids"] or row["assertion_ids"] or row["evidence_summary"]):
            _finding(findings, "U_GRADE_CERTIFICATION_CLAIM", "error", f"U grade for {region}/{layer} may not claim certification evidence.", [region, layer])
    if documents["changelog"]["version"] != manifest["version"]:
        _finding(findings, "CHANGELOG_VERSION_MISMATCH", "error", "Changelog version does not match the pass version.", [])
    return results


def _check_fabric_sidecars(
    root: Path,
    manifest: dict[str, Any],
    assignments: dict[str, Any],
    geometry: dict[str, Any],
    findings: list[dict[str, Any]],
) -> None:
    """Verify the transitive M23 evidence pinned by the assignments artifact."""
    loaded: dict[str, Path] = {}
    for role, record in assignments["fabric_sidecars"].items():
        path = _contained_path(root, record["path"], f"fabric_sidecar:{role}", findings)
        if path is None:
            continue
        if path.is_symlink():
            _finding(findings, "SYMLINK_FABRIC_SIDECAR", "error", f"{role} may not be a symlink.", [role])
            continue
        if not path.is_file():
            _finding(findings, "MISSING_FABRIC_SIDECAR", "error", f"Missing {role}: {path}.", [role])
            continue
        if _sha256(path) != record["sha256"].lower():
            _finding(findings, "FABRIC_SIDECAR_CHECKSUM_MISMATCH", "error", f"Checksum mismatch for {role}.", [role])
        loaded[role] = path
    if len(loaded) != 4:
        return
    try:
        fabric = _load_json(loaded["fabric_manifest"], "Fabric manifest")
        locations_doc = _load_json(loaded["locations"], "Locations")
        lineage = _load_json(loaded["lineage"], "Location lineage")
        with loaded["province_membership"].open("r", encoding="utf-8", newline="") as file:
            memberships = list(csv.DictReader(file))
    except (OSError, UnicodeError, csv.Error, StartDateQAError) as exc:
        _finding(findings, "INVALID_FABRIC_SIDECAR", "error", str(exc), [])
        return

    expected_revision = assignments["fabric_revision"]
    fabric_id = str(fabric.get("fabric_id") or "")
    revision = str(fabric.get("fabric_revision") or "")
    accepted_revisions = {revision, f"{fabric_id}-r{revision}"}
    if expected_revision not in accepted_revisions or manifest["fabric_revision"] != expected_revision:
        _finding(findings, "FABRIC_REVISION_MISMATCH", "error", "Pinned fabric manifest does not match the pass revision.", [])
    features = locations_doc.get("features")
    if locations_doc.get("type") != "FeatureCollection" or not isinstance(features, list):
        _finding(findings, "INVALID_LOCATIONS_SIDECAR", "error", "Locations sidecar is not a FeatureCollection.", [])
        return
    locations: dict[str, BaseGeometry] = {}
    for feature in features:
        location_id = (feature.get("properties") or {}).get("location_id")
        if not isinstance(location_id, str) or not location_id or location_id in locations:
            _finding(findings, "DUPLICATE_OR_INVALID_FABRIC_LOCATION", "error", "Fabric location IDs must be unique and non-empty.", [str(location_id)])
            continue
        try:
            location_geometry = shape(feature["geometry"])
        except Exception:
            _finding(findings, "INVALID_FABRIC_LOCATION_GEOMETRY", "error", f"Invalid geometry for {location_id}.", [location_id])
            continue
        if location_geometry.is_empty or not location_geometry.is_valid or location_geometry.geom_type not in {"Polygon", "MultiPolygon"}:
            _finding(findings, "INVALID_FABRIC_LOCATION_GEOMETRY", "error", f"Invalid geometry for {location_id}.", [location_id])
            continue
        locations[location_id] = location_geometry
    assigned_ids = {location for row in assignments["assignments"] for location in row["location_ids"]}
    _unknown_refs(findings, "UNKNOWN_FABRIC_LOCATION", sorted(assigned_ids), set(locations), "assignments")
    if manifest["schema_version"] == "0.3.0" and assigned_ids != set(locations):
        _finding(
            findings, "INCOMPLETE_WORLD_LAND_MASK", "error",
            "Worldwide assignments must include every playable fabric location exactly once.",
            sorted(set(locations) - assigned_ids),
        )

    lineage_by_request = {
        event.get("request_id"): event for event in lineage.get("events", [])
        if isinstance(event, dict) and isinstance(event.get("request_id"), str)
    }
    for request in assignments["targeted_split_requests"]:
        if request["status"] == "accepted":
            event = lineage_by_request.get(request["request_id"])
            parents = event.get("parent_location_ids", []) if event else []
            children = set(event.get("child_location_ids", [])) if event else set()
            missing = sorted(set(request["location_ids"]) - children)
            if not parents or missing:
                _finding(findings, "ACCEPTED_SPLIT_WITHOUT_LINEAGE", "error", f"Accepted split {request['request_id']} has no parent/child lineage.", [request["request_id"], *missing])

    required_columns = {"province_id", "location_id", "piece_id"}
    if not memberships or not required_columns.issubset(memberships[0]):
        _finding(findings, "INVALID_PROVINCE_MEMBERSHIP", "error", "Province membership sidecar has invalid columns or no rows.", [])
        return
    province_members: dict[str, list[tuple[str, str]]] = {}
    membership_locations: set[str] = set()
    for row in memberships:
        province_id, location_id, piece_id = row.get("province_id", ""), row.get("location_id", ""), row.get("piece_id", "")
        province_members.setdefault(province_id, []).append((location_id, piece_id))
        if location_id in membership_locations:
            _finding(findings, "DUPLICATE_MEMBERSHIP_LOCATION", "error", f"Location {location_id} occurs more than once in membership.", [location_id])
        membership_locations.add(location_id)
        if location_id not in locations:
            _finding(findings, "UNKNOWN_MEMBERSHIP_LOCATION", "error", f"Membership references unknown location {location_id}.", [location_id])
    expected_count = assignments["expected_province_count"]
    if len(province_members) != expected_count:
        _finding(findings, "INCOMPLETE_FULL_BUILD", "error", f"Expected {expected_count} membership-derived provinces, found {len(province_members)}.", [])

    build_provinces = {
        feature["properties"]["feature_id"]: shape(feature["geometry"])
        for feature in geometry["features"] if feature["properties"]["feature_type"] == "province"
    }
    if len(build_provinces) != expected_count:
        _finding(findings, "INCOMPLETE_FULL_BUILD", "error", f"Expected {expected_count} province geometries, found {len(build_provinces)}.", [])
    for province_id, members in province_members.items():
        expected_id = _derived_province_id(
            sorted(members), assignments["aggregation_profile"], assignments["start_date"],
            assignments["aggregation_revision"], assignments["geometry_revision"],
        )
        if province_id != expected_id:
            _finding(findings, "NON_DERIVED_PROVINCE_ID", "error", f"Province ID {province_id} is not derived from ordered membership.", [province_id])
        if province_id not in build_provinces or any(location_id not in locations for location_id, _ in members):
            continue
        union = unary_union([locations[location_id] for location_id, _piece_id in members])
        if not build_provinces[province_id].equals(union):
            _finding(findings, "PROVINCE_MEMBERSHIP_GEOMETRY_MISMATCH", "error", f"Geometry differs from the location union for {province_id}.", [province_id])


def _derived_province_id(
    members: list[tuple[str, str]], profile_id: str, start_date: str,
    aggregation_revision: str, geometry_revision: str,
) -> str:
    payload = json.dumps({
        "members": members, "profile_id": profile_id, "start_date": start_date,
        "aggregation_revision": str(aggregation_revision), "geometry_revision": str(geometry_revision),
    }, sort_keys=True, separators=(",", ":"))
    return f"prv_{hashlib.sha256(payload.encode()).hexdigest()[:20]}"


def _execute_assertions(golden: dict[str, Any], build: dict[str, BaseGeometry], boundaries: dict[str, dict[str, Any]], findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results = []
    for assertion in golden["assertions"]:
        aid, relation = assertion["assertion_id"], assertion["spatial_relation"]
        missing = [item for item in assertion["subject_ids"] if item not in build]
        missing += [item for item in assertion["boundary_feature_ids"] if item not in boundaries]
        measurement: float | None = None
        if missing:
            status = "fail"
            _finding(findings, "UNKNOWN_SPATIAL_SUBJECT", "error", f"{aid} references missing spatial IDs.", [aid, *missing])
        else:
            subjects = [build[item] for item in assertion["subject_ids"]]
            refs = [shape(boundaries[item]["geometry"]) for item in assertion["boundary_feature_ids"]]
            if relation == "border_matches_boundary_hausdorff_lte":
                shared = subjects[0].boundary.intersection(subjects[1].boundary)
                measurement = shared.hausdorff_distance(refs[0]) if not shared.is_empty else None
                status = "pass" if measurement is not None and measurement <= assertion["tolerance"] else "fail"
            elif relation == "border_matches_boundary_hausdorff_km_lte":
                shared = subjects[0].boundary.intersection(subjects[1].boundary)
                measurement = _hausdorff_km(shared, refs[0]) if not shared.is_empty else None
                status = "pass" if measurement is not None and measurement <= assertion["tolerance"] else "fail"
            elif relation == "capital_within_subject":
                measurement = 1.0 if subjects[1].covers(subjects[0]) else 0.0
                status = "pass" if measurement == 1.0 else "fail"
            else:  # forbidden_outline_overlap_ratio_lte
                denominator = refs[0].area
                measurement = subjects[0].intersection(refs[0]).area / denominator if denominator else 1.0
                status = "pass" if measurement <= assertion["tolerance"] else "fail"
        result = {"assertion_id": aid, "spatial_relation": relation, "unit": assertion["unit"], "tolerance": assertion["tolerance"], "measurement": measurement, "status": status}
        results.append(result)
        if status != "pass":
            _finding(findings, "SPATIAL_ASSERTION_FAILED", "error", f"Executed spatial assertion {aid} failed.", [aid])
    return results


def _validate_world_coverage_mask(document: dict[str, Any]) -> None:
    required = {"schema_version", "document_type", "artifact_version", "pass_id", "start_date", "fabric_revision", "type", "features"}
    if set(document) != required or document.get("schema_version") != "0.3.0" or document.get("document_type") != "world_coverage_mask" or document.get("type") != "FeatureCollection":
        raise SchemaValidationError("world coverage mask has invalid or unexpected top-level fields")
    seen: set[str] = set()
    for index, feature in enumerate(document["features"]):
        props = feature.get("properties") if isinstance(feature, dict) else None
        if feature.get("type") != "Feature" or not isinstance(props, dict):
            raise SchemaValidationError(f"world coverage mask feature {index} is invalid")
        location_id, region_id = props.get("location_id"), props.get("region_id")
        if not isinstance(location_id, str) or not location_id or location_id in seen:
            raise SchemaValidationError("world coverage mask location IDs must be unique and non-empty")
        if not isinstance(region_id, str) or not region_id:
            raise SchemaValidationError(f"world coverage mask {location_id} lacks region_id")
        geometry = shape(feature.get("geometry"))
        if geometry.is_empty or not geometry.is_valid or geometry.geom_type not in {"Polygon", "MultiPolygon"}:
            raise SchemaValidationError(f"world coverage mask {location_id} has invalid geometry")
        seen.add(location_id)
    if not seen:
        raise SchemaValidationError("world coverage mask must contain playable land")


def validate_anomaly_inventory(document: dict[str, Any]) -> None:
    """Validate a closed, independently reviewed worldwide anomaly census."""
    required = {
        "schema_version", "document_type", "artifact_version", "pass_id",
        "start_date", "anomalies", "census",
    }
    if set(document) != required or document.get("schema_version") != "0.3.0" or document.get("document_type") != "historical_anomaly_inventory":
        raise SchemaValidationError("anomaly inventory has invalid or unexpected top-level fields")
    allowed = HISTORICAL_ANOMALY_TYPES
    seen: set[str] = set()
    if not isinstance(document["anomalies"], list):
        raise SchemaValidationError("anomaly inventory.anomalies must be an array")
    anomaly_index: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(document["anomalies"]):
        path = f"anomaly inventory.anomalies[{index}]"
        _require = ("anomaly_id", "type", "region_ids", "subject_ids", "source_ids", "resolution")
        if not isinstance(item, dict) or any(key not in item for key in _require):
            raise SchemaValidationError(f"{path} is incomplete")
        anomaly_id = item["anomaly_id"]
        if not isinstance(anomaly_id, str) or not anomaly_id or anomaly_id in seen or _is_placeholder_identifier(anomaly_id):
            raise SchemaValidationError(f"{path}.anomaly_id must be unique and non-placeholder")
        if not isinstance(item["type"], str) or item["type"] not in allowed or item["resolution"] != "resolved":
            raise SchemaValidationError(f"{path} has unsupported type or unresolved status")
        for field in ("region_ids", "subject_ids", "source_ids"):
            values = item[field]
            if (
                not isinstance(values, list) or not values
                or not all(isinstance(value, str) and value and not _is_placeholder_identifier(value) for value in values)
                or len(values) != len(set(values))
            ):
                raise SchemaValidationError(f"{path}.{field} must contain unique, non-placeholder IDs")
        invalid_regions = set(item["region_ids"]) - WORLDWIDE_M49_SUBREGIONS
        if invalid_regions:
            raise SchemaValidationError(f"{path}.region_ids contains invalid M49 subregions: {sorted(invalid_regions)}")
        seen.add(anomaly_id)
        anomaly_index[anomaly_id] = item
    present = {item["type"] for item in document["anomalies"]}
    if present != allowed:
        raise SchemaValidationError(
            "anomaly inventory must represent every required class; "
            f"missing={sorted(allowed - present)}"
        )

    census = document["census"]
    census_required = {"region_ids", "types", "researcher", "reviewer", "review_date", "cells"}
    if not isinstance(census, dict) or set(census) != census_required:
        raise SchemaValidationError("anomaly inventory.census has invalid or unexpected fields")
    if (
        not isinstance(census["region_ids"], list)
        or not all(isinstance(value, str) for value in census["region_ids"])
        or set(census["region_ids"]) != WORLDWIDE_M49_SUBREGIONS or len(census["region_ids"]) != 22
    ):
        raise SchemaValidationError("anomaly inventory.census.region_ids must be the exact 22-subregion M49 partition")
    if (
        not isinstance(census["types"], list)
        or not all(isinstance(value, str) for value in census["types"])
        or set(census["types"]) != allowed or len(census["types"]) != 11
    ):
        raise SchemaValidationError("anomaly inventory.census.types must contain all 11 anomaly classes exactly once")
    researcher, reviewer = census["researcher"], census["reviewer"]
    if (
        not isinstance(researcher, str) or not researcher.strip()
        or not isinstance(reviewer, str) or not reviewer.strip()
        or researcher.strip().casefold() == reviewer.strip().casefold()
        or _is_placeholder_identifier(researcher) or _is_placeholder_identifier(reviewer)
    ):
        raise SchemaValidationError("anomaly inventory.census review requires distinct, named researcher and reviewer identities")
    try:
        date.fromisoformat(census["review_date"])
    except (TypeError, ValueError):
        raise SchemaValidationError("anomaly inventory.census.review_date must be an ISO date") from None

    cells = census["cells"]
    if not isinstance(cells, list) or len(cells) != 242:
        raise SchemaValidationError("anomaly inventory.census.cells must contain exactly 242 cells")
    cell_index: dict[tuple[str, str], dict[str, Any]] = {}
    linked: dict[str, set[tuple[str, str]]] = {anomaly_id: set() for anomaly_id in anomaly_index}
    for index, cell in enumerate(cells):
        path = f"anomaly inventory.census.cells[{index}]"
        fields = {"region_id", "type", "status", "anomaly_ids", "source_ids", "notes"}
        if not isinstance(cell, dict) or set(cell) != fields:
            raise SchemaValidationError(f"{path} has invalid or unexpected fields")
        region_id, anomaly_type = cell["region_id"], cell["type"]
        key = (region_id, anomaly_type)
        if (
            not isinstance(region_id, str) or not isinstance(anomaly_type, str)
            or region_id not in WORLDWIDE_M49_SUBREGIONS or anomaly_type not in allowed
        ):
            raise SchemaValidationError(f"{path} has an invalid region or anomaly class")
        if key in cell_index:
            raise SchemaValidationError(f"anomaly inventory.census has duplicate cell {region_id}/{anomaly_type}")
        cell_index[key] = cell
        if cell["status"] not in ANOMALY_CENSUS_STATUSES:
            raise SchemaValidationError(f"{path}.status must close the census without pending or unknown states")
        if not isinstance(cell["notes"], str) or not cell["notes"].strip():
            raise SchemaValidationError(f"{path}.notes must explain the reviewed conclusion")
        for field in ("anomaly_ids", "source_ids"):
            values = cell[field]
            if not isinstance(values, list) or not all(
                isinstance(value, str) and value and not _is_placeholder_identifier(value) for value in values
            ) or len(values) != len(set(values)):
                raise SchemaValidationError(f"{path}.{field} must contain unique, non-placeholder IDs")
        if not cell["source_ids"]:
            raise SchemaValidationError(f"{path}.source_ids must identify reviewed survey sources")
        if cell["status"] == "reviewed_none_found":
            if cell["anomaly_ids"]:
                raise SchemaValidationError(f"{path} reviewed_none_found may not link anomaly IDs")
        elif not cell["anomaly_ids"]:
            raise SchemaValidationError(f"{path} resolved_cases must link matching anomaly IDs")
        for anomaly_id in cell["anomaly_ids"]:
            anomaly = anomaly_index.get(anomaly_id)
            if anomaly is None:
                raise SchemaValidationError(f"{path} links unknown anomaly {anomaly_id}")
            if anomaly["type"] != anomaly_type or region_id not in anomaly["region_ids"]:
                raise SchemaValidationError(f"{path} link does not match anomaly {anomaly_id} class/region")
            linked[anomaly_id].add(key)

    expected_cells = {
        (region_id, anomaly_type)
        for region_id in WORLDWIDE_M49_SUBREGIONS
        for anomaly_type in allowed
    }
    if set(cell_index) != expected_cells:
        missing = sorted(expected_cells - set(cell_index))
        raise SchemaValidationError(f"anomaly inventory.census is incomplete; missing={missing}")
    for anomaly_id, anomaly in anomaly_index.items():
        expected_links = {(region_id, anomaly["type"]) for region_id in anomaly["region_ids"]}
        if not linked[anomaly_id]:
            raise SchemaValidationError(f"orphan anomaly {anomaly_id} is not linked by a census cell")
        if linked[anomaly_id] != expected_links:
            raise SchemaValidationError(
                f"anomaly {anomaly_id} census links do not match its declared regions; "
                f"missing={sorted(expected_links - linked[anomaly_id])}"
            )


def _is_placeholder_identifier(value: Any) -> bool:
    normalized = str(value).strip().casefold()
    return normalized in {"pending", "placeholder", "todo", "tbd", "unknown"} or normalized.startswith("pending-")


def _check_global_contract(
    root: Path, manifest: dict[str, Any], documents: dict[str, dict[str, Any]],
    geometry: dict[str, Any], findings: list[dict[str, Any]],
) -> None:
    scope = manifest["scope"]
    partition = set(scope["partition"]["subregions"])
    assignments = documents["location_assignments"]
    mask = documents["world_coverage_mask"]
    canonical = documents["canonical_historical_status"]
    inventory = documents["anomaly_inventory"]
    source_records = {row["source_id"]: row for row in documents["source_manifest"]["sources"]}
    source_ids = set(source_records)
    reviewed_source_ids = {source_id for source_id, row in source_records.items() if row["review_status"] == "reviewed"}
    polity_ids = {row["polity_id"] for row in documents["polity_gazetteer"]["polities"]}
    for anomaly in inventory["anomalies"]:
        _unknown_refs(findings, "UNKNOWN_ANOMALY_SOURCE", anomaly["source_ids"], source_ids, anomaly["anomaly_id"])
        _unknown_refs(findings, "UNKNOWN_ANOMALY_SUBJECT", anomaly["subject_ids"], polity_ids, anomaly["anomaly_id"])
        _unknown_refs(findings, "UNREVIEWED_ANOMALY_SOURCE", anomaly["source_ids"], reviewed_source_ids, anomaly["anomaly_id"])
    for cell in inventory["census"]["cells"]:
        identity = f"{cell['region_id']}/{cell['type']}"
        _unknown_refs(findings, "UNKNOWN_ANOMALY_SOURCE", cell["source_ids"], source_ids, identity)
        _unknown_refs(findings, "UNREVIEWED_ANOMALY_SOURCE", cell["source_ids"], reviewed_source_ids, identity)
    for polity in documents["polity_gazetteer"]["polities"]:
        _unknown_refs(findings, "UNREVIEWED_GLOBAL_POLITY_SOURCE", polity["source_ids"], reviewed_source_ids, polity["polity_id"])
        for relationship in polity["relationships"]:
            _unknown_refs(findings, "UNREVIEWED_GLOBAL_RELATIONSHIP_SOURCE", relationship["source_ids"], reviewed_source_ids, relationship["relationship_id"])
    for assignment in assignments["assignments"]:
        _unknown_refs(findings, "UNREVIEWED_GLOBAL_ASSIGNMENT_SOURCE", assignment["source_ids"], reviewed_source_ids, assignment["assignment_id"])
    for kind in ("components", "political_units", "provinces", "statuses"):
        for index, row in enumerate(canonical[kind]):
            evidence = row.get("evidence_ids") or row.get("shared_administrative_unit_evidence_ids") or []
            if evidence:
                _unknown_refs(findings, "UNREVIEWED_CANONICAL_EVIDENCE", evidence, reviewed_source_ids, f"{kind}:{index}")
    mask_record = manifest["artifacts"]["world_coverage_mask"]
    if scope["world_coverage_mask_sha256"] != mask_record["sha256"]:
        _finding(findings, "WORLD_MASK_HASH_MISMATCH", "error", "Scope and artifact table pin different world masks.", [])
    if mask["fabric_revision"] != manifest["fabric_revision"]:
        _finding(findings, "WORLD_MASK_FABRIC_MISMATCH", "error", "World mask does not use the pinned fabric revision.", [])
    mask_locations = {feature["properties"]["location_id"] for feature in mask["features"]}
    mask_regions = {feature["properties"]["region_id"] for feature in mask["features"]}
    assigned_locations = {location for row in assignments["assignments"] for location in row["location_ids"]}
    assignment_regions = {row["region_id"] for row in assignments["assignments"]}
    if mask_locations != assigned_locations:
        missing, extra = sorted(mask_locations - assigned_locations), sorted(assigned_locations - mask_locations)
        _finding(findings, "INCOMPLETE_WORLD_ASSIGNMENT", "error", "Assignments must cover the world mask exactly once.", [*missing, *extra])
    if mask_regions != partition or assignment_regions != partition:
        _finding(findings, "INVALID_WORLD_PARTITION", "error", "Mask and assignments must use every and only pinned certification region.", sorted((mask_regions | assignment_regions) ^ partition))
    coverage = documents["coverage_matrix"]
    rows = {(row["region_id"], row["layer"]): row for row in coverage["coverage"]}
    for region in sorted(partition):
        for layer in ("geometry", "politics", "hierarchy", "gazetteer_relationships"):
            row = rows.get((region, layer))
            if row is None or row["grade"] != "A" or row["exclusions"] or row["known_gaps"]:
                _finding(findings, "GLOBAL_COVERAGE_NOT_A", "error", f"{region}/{layer} must be gap-free grade A.", [region, layer])
    if coverage["exclusions"] or coverage["known_gaps"]:
        _finding(findings, "GLOBAL_COVERAGE_GAPS", "error", "Worldwide coverage may not declare exclusions or known gaps.", [])
    if canonical["start_date"] != manifest["start_date"]:
        _finding(findings, "CANONICAL_DATE_MISMATCH", "error", "Canonical status uses a different start date.", [])
    build_geometry = {feature["properties"]["feature_id"]: shape(feature["geometry"]) for feature in geometry["features"] if feature["properties"]["feature_type"] == "province"}
    build_provinces = set(build_geometry)
    if assignments["expected_province_count"] != 22_000 or len(build_provinces) != 22_000:
        _finding(findings, "INVALID_GLOBAL_PROVINCE_COUNT", "error", "Worldwide eu-like aggregation must contain exactly 22,000 provinces.", [])
    canonical_provinces = {row["province_id"] for row in canonical["provinces"]}
    if build_provinces != canonical_provinces:
        _finding(findings, "CANONICAL_PROVINCE_MISMATCH", "error", "Canonical and research build province IDs differ.", sorted(build_provinces ^ canonical_provinces))
    components = {row["territory_component_id"]: shape(row["geometry"]) for row in canonical["components"]}
    for province in canonical["provinces"]:
        province_id = province["province_id"]
        if province_id in build_geometry:
            canonical_geometry = unary_union([components[item] for item in province["territory_component_ids"]])
            if not canonical_geometry.equals(build_geometry[province_id]):
                _finding(findings, "CANONICAL_GEOMETRY_MISMATCH", "error", "Canonical component union differs from research geometry.", [province_id])
    statuses = {(row["subject_id"], row["relationship"]) for row in canonical["statuses"]}
    for component_id in components:
        missing = [relation for relation in ("sovereign", "owner", "controller") if (component_id, relation) not in statuses]
        if missing:
            _finding(findings, "MISSING_TYPED_COMPONENT_STATUS", "error", "Every component needs sovereign, owner, and controller status.", [component_id, *missing])


def _validate_full_build(document: dict[str, Any]) -> None:
    required = {"schema_version", "document_type", "artifact_version", "pass_id", "start_date", "geometry_revision", "type", "features"}
    if not isinstance(document, dict) or set(document) != required or document.get("schema_version") not in {"0.1.0", "0.2.0", "0.3.0"} or document.get("document_type") != "start_date_full_build_geometry" or document.get("type") != "FeatureCollection":
        raise SchemaValidationError("full build has invalid or unexpected top-level fields")
    if not isinstance(document["features"], list) or not document["features"]:
        raise SchemaValidationError("full build features must be non-empty")
    seen: set[str] = set()
    province_ids: list[str] = []
    province_geometries: list[BaseGeometry] = []
    for feature in document["features"]:
        if not isinstance(feature, dict) or set(feature) != {"type", "properties", "geometry"} or feature.get("type") != "Feature":
            raise SchemaValidationError("full build feature has invalid fields")
        props = feature.get("properties")
        if not isinstance(props, dict) or set(props) != {"feature_id", "feature_type"} or props.get("feature_type") not in {"province", "capital"}:
            raise SchemaValidationError("full build feature properties are invalid")
        fid = props.get("feature_id")
        if not isinstance(fid, str) or not fid or fid in seen:
            raise SchemaValidationError("full build feature IDs must be unique non-empty strings")
        seen.add(fid)
        try:
            geometry = shape(feature["geometry"])
            expected_type = "Point" if props["feature_type"] == "capital" else None
            if not geometry.is_valid or geometry.is_empty or (expected_type and geometry.geom_type != expected_type) or (props["feature_type"] == "province" and geometry.geom_type not in {"Polygon", "MultiPolygon"}):
                raise ValueError("geometry type or validity does not match feature_type")
        except Exception as exc: raise SchemaValidationError(f"invalid full-build geometry for {fid}: {exc}") from exc
        if props["feature_type"] == "province":
            province_ids.append(fid)
            province_geometries.append(geometry)
    tree = STRtree(province_geometries)
    for left_index, left in enumerate(province_geometries):
        for right_index in tree.query(left):
            right_index = int(right_index)
            if right_index <= left_index:
                continue
            if left.intersection(province_geometries[right_index]).area > 1e-12:
                raise SchemaValidationError(
                    f"full-build province interiors overlap: {province_ids[left_index]}, {province_ids[right_index]}"
                )


def _check_dossier(path: Path, findings: list[dict[str, Any]]) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        _finding(findings, "MALFORMED_DOSSIER", "error", f"Dossier is not readable UTF-8: {exc}", ["dossier"])
        return
    headings = {match.group(1).strip().lower() for match in re.finditer(r"^#{1,6}\s+(.+?)\s*$", text, re.MULTILINE)}
    missing = [section for section in _DOSSIER_SECTIONS if section not in headings]
    if missing:
        _finding(findings, "INCOMPLETE_DOSSIER", "error", f"Dossier is missing required sections: {', '.join(missing)}.", ["dossier"])


def _check_derived_source_artifacts(root: Path, source_manifest: dict[str, Any], findings: list[dict[str, Any]]) -> None:
    seen: set[str] = set()
    for source in source_manifest["sources"]:
        for artifact in source["derived_artifacts"]:
            artifact_id = artifact["artifact_id"]
            if artifact_id in seen:
                _finding(findings, "DUPLICATE_DERIVED_ARTIFACT_ID", "error", "Derived artifact IDs must be unique.", [artifact_id])
            seen.add(artifact_id)
            path = _contained_path(root, artifact["path"], f"derived:{artifact_id}", findings)
            if path is None or not path.is_file():
                _finding(findings, "MISSING_DERIVED_ARTIFACT", "error", f"Missing derived artifact {artifact_id}.", [artifact_id])
            elif _sha256(path) != artifact["sha256"].lower():
                _finding(findings, "DERIVED_ARTIFACT_CHECKSUM_MISMATCH", "error", f"Checksum mismatch for {artifact_id}.", [artifact_id])


def _check_v2_hard_boundary(
    findings: list[dict[str, Any]], owner: str, props: dict[str, Any],
    source_records: dict[str, dict[str, Any]], start_date: str,
) -> None:
    sources = [source_records[sid] for sid in props["source_ids"] if sid in source_records]
    qualifying = [source for source in sources if source["source_type"] in {"academic", "primary"} and _contains_date(source.get("valid_from"), source.get("valid_to"), start_date)]
    independence = {source["independence_group"] for source in sources if source["source_type"] not in {"soft_corroboration", "negative_control"}}
    if not qualifying:
        _finding(findings, "MISSING_DATE_VALID_RECONSTRUCTION", "error", f"Hard boundary {owner} lacks date-valid academic or primary evidence.", [owner])
    if len(independence) < 2:
        _finding(findings, "MISSING_INDEPENDENT_CORROBORATION", "error", f"Hard boundary {owner} lacks independent corroboration.", [owner])
    artifacts = [artifact for source in sources for artifact in source["derived_artifacts"]]
    artifact_ids = {artifact["artifact_id"] for artifact in artifacts}
    if props["derived_geometry_artifact_id"] not in artifact_ids:
        _finding(findings, "UNPINNED_DERIVED_BOUNDARY_GEOMETRY", "error", f"Hard boundary {owner} does not reference geometry derived from its cited sources.", [owner])
    if not any(artifact["role"] == "coverage_mask" for artifact in artifacts):
        _finding(findings, "MISSING_POLITY_COVERAGE_MASK", "error", f"Hard boundary {owner} lacks a cited polity coverage mask.", [owner])
    georef = props["georeferencing"]
    if props["error_budget_km"] < georef["residual_error_km"]:
        _finding(findings, "ERROR_BUDGET_BELOW_RESIDUAL", "error", f"Hard boundary {owner} error budget is below measured residual.", [owner])


def _check_release_sidecars(
    root: Path, manifest: dict[str, Any], assignments: dict[str, Any],
    geometry: dict[str, Any], findings: list[dict[str, Any]],
) -> None:
    loaded: dict[str, Path] = {}
    for role, record in assignments["release_sidecars"].items():
        path = _contained_path(root, record["path"], f"release_sidecar:{role}", findings)
        if path is None or not path.is_file():
            _finding(findings, "MISSING_RELEASE_SIDECAR", "error", f"Missing release sidecar {role}.", [role])
        elif _sha256(path) != record["sha256"].lower():
            _finding(findings, "RELEASE_SIDECAR_CHECKSUM_MISMATCH", "error", f"Checksum mismatch for {role}.", [role])
        else:
            loaded[role] = path
    aggregation_path = loaded.get("aggregation_manifest")
    if aggregation_path:
        aggregation = _load_json(aggregation_path, "Aggregation manifest")
        policy = aggregation.get("historical_constraint_policy") or {}
        if policy.get("sha256") != assignments["constraint_sha256"]:
            _finding(findings, "CONSTRAINT_HASH_MISMATCH", "error", "Aggregation manifest does not pin the assignment constraint hash.", [])
        if aggregation.get("actual_province_count") != assignments["expected_province_count"]:
            _finding(findings, "AGGREGATION_COUNT_MISMATCH", "error", "Aggregation manifest count differs from assignments.", [])
    adjacency_path = loaded.get("adjacency")
    if adjacency_path:
        province_ids = {
            feature["properties"]["feature_id"] for feature in geometry["features"]
            if feature["properties"]["feature_type"] == "province"
        }
        try:
            with adjacency_path.open("r", encoding="utf-8", newline="") as file:
                rows = list(csv.DictReader(file))
        except (OSError, csv.Error) as exc:
            _finding(findings, "INVALID_FULL_BUILD_ADJACENCY", "error", str(exc), [])
            rows = []
        required = {"from_province_id", "to_province_id"}
        if rows and not required.issubset(rows[0]):
            _finding(findings, "INVALID_FULL_BUILD_ADJACENCY", "error", "Adjacency sidecar has invalid columns.", [])
        seen_edges: set[tuple[str, str]] = set()
        for row in rows:
            left, right = row.get("from_province_id", ""), row.get("to_province_id", "")
            edge = tuple(sorted((left, right)))
            if not left or not right or left == right or left not in province_ids or right not in province_ids:
                _finding(findings, "INVALID_FULL_BUILD_ADJACENCY", "error", "Adjacency references an invalid province pair.", [left, right])
            if edge in seen_edges:
                _finding(findings, "DUPLICATE_FULL_BUILD_ADJACENCY", "error", "Adjacency contains a duplicate undirected edge.", [left, right])
            seen_edges.add(edge)
    review_record = manifest["review"]
    review_path = _contained_path(root, review_record["manifest_path"], "review_manifest", findings)
    if review_path is None or not review_path.is_file():
        _finding(findings, "MISSING_REVIEW_MANIFEST", "error", "Independent review manifest is missing.", [])
        return
    if _sha256(review_path) != review_record["sha256"].lower():
        _finding(findings, "REVIEW_MANIFEST_CHECKSUM_MISMATCH", "error", "Review manifest checksum mismatch.", [])
        return
    review = _load_json(review_path, "Review manifest")
    if review.get("reviewer") != review_record["reviewer"] or review.get("generator") != review_record["generator"] or review.get("status") != "accepted":
        _finding(findings, "INVALID_INDEPENDENT_REVIEW", "error", "Review signature/status does not match the pass manifest.", [])
    rendered_regions = {
        str(render.get("region_id", "")) for render in review.get("renders", [])
        if render.get("sheet_type", "region") == "region"
    }
    expected_regions = set(manifest["scope"]["priority_regions"])
    if rendered_regions != expected_regions:
        _finding(findings, "INCOMPLETE_REVIEW_COVERAGE", "error", "Review renders do not exactly cover the priority regions.", sorted(expected_regions - rendered_regions))
    if manifest["schema_version"] == "0.3.0":
        inventory_path = _contained_path(root, manifest["artifacts"]["anomaly_inventory"]["path"], "anomaly_inventory", findings)
        inventory = _load_json(inventory_path, "Anomaly inventory") if inventory_path and inventory_path.is_file() else {"anomalies": []}
        expected_anomalies = {f"anomaly:{item['type']}" for item in inventory["anomalies"]}
        rendered_anomalies = {
            str(render.get("region_id", "")) for render in review.get("renders", [])
            if render.get("sheet_type") == "anomaly"
        }
        if rendered_anomalies != expected_anomalies:
            _finding(findings, "INCOMPLETE_ANOMALY_REVIEW", "error", "Review renders do not cover every anomaly class.", sorted(expected_anomalies - rendered_anomalies))
    review_parent = Path(review_record["manifest_path"]).parent
    for render in review.get("renders", []):
        relative = review_parent / str(render.get("path", ""))
        path = _contained_path(root, str(relative), f"review_render:{render.get('region_id', '')}", findings)
        if path is None or not path.is_file() or _sha256(path) != str(render.get("sha256", "")).lower():
            _finding(findings, "TAMPERED_REVIEW_RENDER", "error", "Review render is missing or has been modified.", [str(render.get("region_id", ""))])


def _contains_date(lower: str | None, upper: str | None, target: str) -> bool:
    try:
        target_date = date.fromisoformat(target)
        low = _date_bound(lower, False); high = _date_bound(upper, True)
        return (low is None or low <= target_date) and (high is None or target_date <= high)
    except ValueError:
        return False


def _hausdorff_km(left: BaseGeometry, right: BaseGeometry) -> float:
    center_lat = (left.centroid.y + right.centroid.y) / 2.0
    x_scale = 111.320 * math.cos(math.radians(center_lat))
    y_scale = 110.574
    project = lambda x, y, z=None: (x * x_scale, y * y_scale)
    return shapely_transform(project, left).hausdorff_distance(shapely_transform(project, right))


def _check_temporal(findings: list[dict[str, Any]], owner: str, lower: str | None, upper: str | None, target: str, code: str) -> None:
    try:
        target_date = date.fromisoformat(target)
        low = _date_bound(lower, False); high = _date_bound(upper, True)
    except ValueError:
        _finding(findings, "INVALID_TEMPORAL_RANGE", "error", f"{owner} has malformed dates.", [owner]); return
    if (low and high and low > high) or (low and target_date < low) or (high and target_date > high):
        _finding(findings, code, "error", f"{owner} is not valid at {target}.", [owner])


def _date_bound(value: str | None, upper: bool) -> date | None:
    if value is None: return None
    if re.fullmatch(r"\d{4}", value): return date(int(value), 12 if upper else 1, 31 if upper else 1)
    if re.fullmatch(r"\d{4}-\d{2}", value):
        year, month = map(int, value.split("-"));
        if upper:
            from calendar import monthrange
            return date(year, month, monthrange(year, month)[1])
        return date(year, month, 1)
    return date.fromisoformat(value)


def _unknown_refs(findings: list[dict[str, Any]], code: str, values: list[str], known: set[str], owner: str) -> None:
    missing = sorted(set(values) - known)
    if missing: _finding(findings, code, "error", f"{owner} references unknown IDs: {', '.join(missing)}.", [owner, *missing])


def _contained_path(root: Path, value: str, kind: str, findings: list[dict[str, Any]]) -> Path | None:
    raw = Path(value)
    if raw.is_absolute() or ".." in raw.parts:
        _finding(findings, "ARTIFACT_OUTSIDE_PASS", "error", f"{kind} escapes the pass directory.", [kind]); return None
    candidate = root / raw
    try: candidate.resolve().relative_to(root)
    except ValueError:
        _finding(findings, "ARTIFACT_OUTSIDE_PASS", "error", f"{kind} escapes the pass directory.", [kind]); return None
    return candidate


def _load_json(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file(): raise StartDateQAError(f"{label} does not exist: {path}")
    try: value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc: raise StartDateQAError(f"{label} is not valid readable JSON: {path}: {exc}") from exc
    if not isinstance(value, dict): raise StartDateQAError(f"{label} must be a JSON object: {path}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""): digest.update(chunk)
    return digest.hexdigest()


def _finding(findings: list[dict[str, Any]], code: str, severity: str, message: str, affected_ids: list[str]) -> None:
    findings.append({"code": code, "severity": severity, "message": message, "affected_ids": affected_ids})
