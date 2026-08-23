"""Fail-closed qualification for an M25C assembled research candidate."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from gpm.qa.m25c_census import acceptance_findings, overlay_acceptance
from gpm.schemas import WORLDWIDE_M49_SUBREGIONS

PASS_ID = "official-1444-global-v1"
START_DATE = "1444-11-11"
ASSEMBLED_VERSION = "1.0.0-assembled.1"
LAYERS = ("geometry", "politics", "hierarchy", "gazetteer_relationships")
PROVISIONAL_SENTINEL = "official-1444-modern-scaffold-provisional"
ARTIFACT_FILES = (
    "source_manifest.json", "boundaries.geojson", "gazetteer.json",
    "assignments.json", "golden.json", "build.geojson", "coverage.json",
    "changelog.json", "historical-territory-status.json",
    "positive-border-applicability.json",
    "world_coverage_mask.geojson", "anomaly_inventory.json",
    "anomaly_census_review_ledger.json", "dossier.md",
)
ACCEPTED_FABRIC_SHA256 = {
    "location_fabric_manifest.json": "057d35a2ba95c52bcfa139719efa5dd012d66d127c25ecbde8947e8d1a3636de",
    "location_lineage.json": "c0c4c6bfef568df1519096f964f16077c7dc1871fd3b604e1fc96232410a6233",
    "province_membership.csv": "f25c67657e8ef41d2ad064221312c9da47058b44fcd51394382081ca90447e68",
    "location_adjacency.csv": "8fc320c699b914bc2f63bd26db0c361d6f68b18f83d3294163d001b413c4d3ad",
    "locations.geojson": "7d50679c8c9b7cb76657df4c8b58cf1d97e17ee6d12bb765614f67189b95d485",
}
ACCEPTED_WORLD_MASK_SHA256 = "f30ef12f693a6e89bf79741cb2614853bfa1237250afecfed56ddece2aa37f11"


def qualify_accepted_anomaly(inventory_path: Path, acceptance_path: Path) -> dict[str, Any]:
    """Require the inventory bytes to be bound by the accepted frozen sidecar."""
    inventory_path = Path(inventory_path).resolve()
    acceptance_path = Path(acceptance_path).resolve()
    root = inventory_path.parent
    sums_path = root / "SHA256SUMS"
    for path, label in ((inventory_path, "inventory"), (acceptance_path, "acceptance sidecar"), (sums_path, "SHA256SUMS")):
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"accepted anomaly {label} must be a regular file")
    inventory = _load(inventory_path)
    acceptance = _load(acceptance_path)
    findings = acceptance_findings(
        acceptance,
        frozen_sha256sums_sha256=_sha256(sums_path),
        inventory=inventory,
    )
    relative = inventory_path.relative_to(root).as_posix()
    expected = None
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        parts = line.split("  ", 1)
        if len(parts) == 2 and parts[1] == relative:
            expected = parts[0]
            break
    if expected != _sha256(inventory_path):
        findings.append("frozen anomaly inventory does not match SHA256SUMS")
    if findings:
        raise ValueError("accepted anomaly binding rejected: " + "; ".join(findings))
    return overlay_acceptance(inventory, acceptance)


def qualify_fabric_sidecars(sidecars: Path) -> None:
    """Reject missing, linked, malformed, or internally inconsistent fabric inputs."""
    sidecars = Path(sidecars).resolve()
    required = (
        "location_fabric_manifest.json", "location_lineage.json",
        "province_membership.csv", "location_adjacency.csv", "locations.geojson",
    )
    for name in required:
        path = sidecars / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"accepted fabric sidecar must be a regular file: {name}")
        if _sha256(path) != ACCEPTED_FABRIC_SHA256[name]:
            raise ValueError(f"accepted fabric sidecar checksum changed: {name}")
    manifest = _load(sidecars / "location_fabric_manifest.json")
    if manifest.get("actual_location_count") != 30_216:
        raise ValueError("accepted fabric manifest has an unexpected location count")
    for name, required_columns in (
        ("province_membership.csv", {"province_id", "location_id", "piece_id"}),
        ("location_adjacency.csv", {"from_location_id", "to_location_id"}),
    ):
        with (sidecars / name).open(newline="", encoding="utf-8") as handle:
            header = set(next(csv.reader(handle), []))
        if not required_columns.issubset(header):
            raise ValueError(f"accepted fabric sidecar has invalid columns: {name}")


def qualify_assembled_pass(root: Path, *, packets: Iterable[dict[str, Any]] | None = None) -> None:
    """Validate exact assembled closure and truthful final artifact lineage."""
    root = Path(root).resolve()
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"assembled pass may not contain symlinks: {path.relative_to(root)}")
    for name in ARTIFACT_FILES:
        path = root / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"assembled artifact must be a regular file: {name}")

    documents = {name: _load(root / name) for name in ARTIFACT_FILES if name.endswith((".json", ".geojson"))}
    for name, document in documents.items():
        if document.get("artifact_version") != ASSEMBLED_VERSION:
            raise ValueError(f"assembled artifact has a mixed version: {name}")
    assignments = documents["assignments.json"]
    rows = assignments.get("assignments") or []
    province_ids = [str(row.get("province_id") or "") for row in rows]
    if len(rows) != 22_000 or len(set(province_ids)) != 22_000 or "" in province_ids:
        raise ValueError("assembled assignments must contain exactly 22,000 unique provinces")
    assigned = [str(value) for row in rows for value in (row.get("location_ids") or [])]
    mask_ids = [str(feature.get("properties", {}).get("location_id") or "") for feature in documents["world_coverage_mask.geojson"].get("features") or []]
    if len(mask_ids) != 23_582 or len(set(mask_ids)) != 23_582 or Counter(assigned) != Counter(mask_ids):
        raise ValueError("assembled assignments must cover all 23,582 playable locations exactly once")

    coverage = documents["coverage.json"]
    coverage_rows = coverage.get("coverage") or []
    expected = {(region, layer) for region in WORLDWIDE_M49_SUBREGIONS for layer in LAYERS}
    actual = [(row.get("region_id"), row.get("layer")) for row in coverage_rows]
    if len(coverage_rows) != 88 or set(actual) != expected or len(set(actual)) != 88:
        raise ValueError("assembled coverage must contain the exact 88 region/layer rows")
    if coverage.get("known_gaps") or coverage.get("exclusions") or any(
        row.get("grade") != "A" or row.get("known_gaps") or row.get("exclusions")
        for row in coverage_rows
    ):
        raise ValueError("assembled coverage must be gap-free Grade A")

    if packets is not None:
        packet_rows = list(packets)
        regions = [str(packet.get("region_id") or "") for packet in packet_rows]
        if len(packet_rows) != 22 or set(regions) != WORLDWIDE_M49_SUBREGIONS or len(set(regions)) != 22:
            raise ValueError("assembled pass requires exactly one packet for each pinned region")
        overrides = [row for packet in packet_rows for row in (packet.get("assignment_overrides") or [])]
        override_ids = [str(row.get("province_id") or "") for row in overrides]
        if len(overrides) != 22_000 or len(set(override_ids)) != 22_000 or set(override_ids) != set(province_ids):
            raise ValueError("assembled packets must provide exactly one override for every final province")

    source_manifest = documents["source_manifest.json"]
    sources = source_manifest.get("sources") or []
    source_ids = {row.get("source_id") for row in sources}
    reviewed_ids = {row.get("source_id") for row in sources if row.get("review_status") == "reviewed"}
    cited: set[str] = set()
    for name, document in documents.items():
        if name in {"world_coverage_mask.geojson", "build.geojson", "changelog.json"}:
            continue
        _collect_citations(document, cited)
    unresolved = cited - source_ids
    unreviewed = cited - reviewed_ids
    if unresolved:
        raise ValueError("assembled artifacts cite unresolved sources: " + ", ".join(sorted(unresolved)[:20]))
    if unreviewed:
        raise ValueError("assembled artifacts cite unreviewed sources: " + ", ".join(sorted(unreviewed)[:20]))

    canonical = documents["historical-territory-status.json"]
    if len(canonical.get("components") or []) != 22_000 or len(canonical.get("provinces") or []) != 22_000:
        raise ValueError("assembled canonical status must contain exactly 22,000 components and provinces")
    aggregation_record = assignments.get("release_sidecars", {}).get("aggregation_manifest", {})
    aggregation_path = _contained(root, aggregation_record.get("path"), "aggregation manifest")
    aggregation = _load(aggregation_path)
    modes = {
        canonical.get("qa_mode"),
        aggregation.get("qa_mode"),
        documents["assignments.json"].get("qa_mode", "certification_review"),
        documents["coverage.json"].get("qa_mode", "certification_review"),
    }
    manifest_path = root / "pass_manifest.json"
    if manifest_path.exists():
        if manifest_path.is_symlink():
            raise ValueError("assembled pass manifest may not be a symlink")
        manifest = _load(manifest_path)
        modes.add(manifest.get("qa_mode"))
        if manifest.get("artifact_version") != ASSEMBLED_VERSION or manifest.get("version") != ASSEMBLED_VERSION:
            raise ValueError("assembled pass manifest has a mixed artifact version")
        _verify_manifest_hashes(root, manifest)
    if modes != {"certification_review"}:
        raise ValueError("assembled artifacts contain mixed QA modes")
    if canonical.get("artifact_version") != ASSEMBLED_VERSION or aggregation.get("generator_version") != ASSEMBLED_VERSION:
        raise ValueError("assembled artifacts contain mixed versions")
    if aggregation.get("provisional") is not False:
        raise ValueError("assembled aggregation must be non-provisional")
    if canonical.get("provisional") is not False or any(
        row.get("provisional") is not False
        for group in ("components", "provinces") for row in canonical.get(group) or []
    ):
        raise ValueError("assembled canonical status must explicitly reject provisional lineage")

    candidate_path = root / "candidate_status.json"
    if candidate_path.exists():
        if candidate_path.is_symlink() or not candidate_path.is_file():
            raise ValueError("assembled candidate status must be a regular file")
        candidate = _load(candidate_path)
        if candidate.get("status") not in {"assembled_pending_research_qa", "pending_independent_review"}:
            raise ValueError("assembled candidate status has a mixed mode")
        expected_review = candidate.get("status") == "pending_independent_review"
        if candidate.get("review_acceptance_allowed") is not expected_review or any(
            candidate.get(key) is not False for key in (
                "certification_allowed", "runtime_publication_allowed", "public_release_allowed",
            )
        ):
            raise ValueError("assembled candidate permissions contradict its status")

    for name in ARTIFACT_FILES:
        text = (root / name).read_text(encoding="utf-8")
        if PROVISIONAL_SENTINEL in text:
            raise ValueError(f"assembled artifact retains provisional source lineage: {name}")
    _verify_sidecar_hashes(root, assignments)


def _collect_citations(value: Any, result: set[str], key: str | None = None) -> None:
    if isinstance(value, dict):
        for child_key, child in value.items():
            _collect_citations(child, result, child_key)
    elif isinstance(value, list):
        if key in {"source_ids", "evidence_ids"}:
            result.update(str(item) for item in value)
        else:
            for child in value:
                _collect_citations(child, result, key)


def _verify_sidecar_hashes(root: Path, assignments: dict[str, Any]) -> None:
    expected = {
        "fabric_sidecars": {"fabric_manifest", "locations", "lineage", "province_membership"},
        "release_sidecars": {"aggregation_manifest", "adjacency"},
    }
    for group in ("fabric_sidecars", "release_sidecars"):
        records = assignments.get(group) or {}
        if set(records) != expected[group]:
            raise ValueError(f"assembled assignments have incomplete or extra {group}")
        for role, record in records.items():
            path = _contained(root, record.get("path"), f"{group}:{role}")
            if path.is_symlink() or not path.is_file() or _sha256(path) != str(record.get("sha256") or "").lower():
                raise ValueError(f"assembled sidecar is missing, linked, or checksum-invalid: {group}:{role}")


def _verify_manifest_hashes(root: Path, manifest: dict[str, Any]) -> None:
    for role, record in (manifest.get("artifacts") or {}).items():
        if record.get("version") != ASSEMBLED_VERSION:
            raise ValueError(f"assembled manifest artifact has a mixed version: {role}")
        path = _contained(root, record.get("path"), role)
        if path.is_symlink() or not path.is_file() or _sha256(path) != str(record.get("sha256") or "").lower():
            raise ValueError(f"assembled manifest artifact is missing, linked, or checksum-invalid: {role}")


def _contained(root: Path, value: Any, label: str) -> Path:
    relative = Path(str(value or ""))
    if not relative.parts or relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"assembled {label} path escapes the pass")
    path = root / relative
    try:
        path.resolve().relative_to(root)
    except ValueError as exc:
        raise ValueError(f"assembled {label} path escapes the pass") from exc
    return path


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read assembled JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"assembled JSON must be an object: {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
