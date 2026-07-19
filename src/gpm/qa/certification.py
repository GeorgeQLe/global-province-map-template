"""M25C worldwide historical-era certification."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from gpm.runtime import RuntimeCompileError, RuntimeLoadError, RuntimePack, compile_runtime_pack
from gpm.schemas import (
    SchemaValidationError,
    validate_global_certification_manifest,
    validate_historical_territory_status,
    validate_runtime_pack_manifest,
)

from .start_date import StartDateQAError, run_start_date_qa


class EraCertificationError(RuntimeError):
    """Raised when any worldwide research or runtime gate fails."""


@dataclass(frozen=True)
class EraCertificationResult:
    certification_id: str
    pass_id: str
    status: str
    output: str
    benchmark_output: str
    province_count: int
    component_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


PERFORMANCE_LIMITS = {
    "core_uncompressed_bytes": 16 * 1024 * 1024,
    "core_individually_gzip_bytes": 8 * 1024 * 1024,
    "initial_core_plus_lod0_gzip_bytes": 8 * 1024 * 1024,
    "geometry_archive_bytes": 128 * 1024 * 1024,
    "load_p95_ms": 1000.0,
    "tile_read_p95_ms": 25.0,
}


def certify_era(*, pass_dir: Path, runtime_dir: Path, output: Path) -> EraCertificationResult:
    """Emit an accepted manifest only after every M25C gate passes."""
    pass_root, runtime_root, output_path = Path(pass_dir).resolve(), Path(runtime_dir).resolve(), Path(output).resolve()
    pass_manifest_path = pass_root / "pass_manifest.json"
    pass_manifest = _load_json(pass_manifest_path, "research pass")
    if pass_manifest.get("schema_version") != "0.3.0" or (pass_manifest.get("scope") or {}).get("kind") != "worldwide":
        raise EraCertificationError("M25C certification requires a schema 0.3.0 worldwide research pass")
    try:
        qa_result = run_start_date_qa(pass_dir=pass_root)
    except StartDateQAError as exc:
        raise EraCertificationError(str(exc)) from exc
    if not qa_result.passed:
        raise EraCertificationError(f"research QA failed with {qa_result.error_count} error(s)")

    canonical_record = pass_manifest["artifacts"]["canonical_historical_status"]
    canonical_path = _pass_artifact(pass_root, canonical_record["path"])
    canonical = _load_json(canonical_path, "canonical historical status")
    try:
        validate_historical_territory_status(canonical)
    except SchemaValidationError as exc:
        raise EraCertificationError(f"invalid canonical historical status: {exc}") from exc

    runtime_manifest_path = runtime_root / "runtime_manifest.json"
    runtime_manifest = _load_json(runtime_manifest_path, "runtime manifest")
    try:
        validate_runtime_pack_manifest(runtime_manifest)
    except SchemaValidationError as exc:
        raise EraCertificationError(f"invalid runtime manifest: {exc}") from exc
    if runtime_manifest.get("pack_id") != pass_manifest["pass_id"]:
        raise EraCertificationError("runtime pack_id must equal the global research pass_id")
    if runtime_manifest.get("debug_symbols_included") is not False:
        raise EraCertificationError("certified runtime packs may not contain debug symbols")
    if any(any(token in row.get("path", "").lower() for token in ("evidence", "source", "debug")) for row in runtime_manifest.get("files", [])):
        raise EraCertificationError("certified runtime packs may not contain evidence/debug material")
    try:
        runtime = RuntimePack(runtime_root)
    except RuntimeLoadError as exc:
        raise EraCertificationError(f"runtime validation failed: {exc}") from exc
    _check_runtime_parity(canonical, runtime, runtime_manifest)
    _check_deterministic_compilation(canonical_path, pass_manifest["pass_id"], runtime_manifest["compatibility_revision"])

    benchmark = RuntimePack.benchmark(runtime_root, iterations=3)
    benchmark_document = _benchmark_document(runtime_manifest, benchmark)
    failures = [name for name, result in benchmark_document["gates"].items() if result != "pass"]
    if failures:
        raise EraCertificationError("runtime performance gate(s) failed: " + ", ".join(failures))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    benchmark_path = output_path.with_name(f"{output_path.stem}-runtime-benchmark.json")
    _write_json(benchmark_path, benchmark_document)

    review = pass_manifest["review"]
    review_path = _pass_artifact(pass_root, review["manifest_path"])
    qa_path = Path(qa_result.report_output).resolve()
    certification = {
        "schema_version": "1.0.0",
        "certification_type": "gpm-global-era-certification",
        "status": "accepted",
        "certification_id": pass_manifest["pass_id"],
        "pass_id": pass_manifest["pass_id"],
        "start_date": pass_manifest["start_date"],
        "scope": "worldwide",
        "public_scenario_id": "official-1444",
        "compatibility_revision": runtime_manifest["compatibility_revision"],
        "artifacts": {
            "research_pass": _record(output_path, pass_manifest_path),
            "research_qa": _record(output_path, qa_path),
            "canonical_historical_status": _record(output_path, canonical_path),
            "independent_review": _record(output_path, review_path),
            "runtime_manifest": _record(output_path, runtime_manifest_path),
            "runtime_benchmark": _record(output_path, benchmark_path),
        },
        "gates": {
            "research": "pass", "world_partition": "pass", "coverage": "pass",
            "canonical_runtime_parity": "pass", "runtime_determinism": "pass",
            "runtime_performance": "pass", "independent_review": "pass",
        },
    }
    try:
        validate_global_certification_manifest(certification)
    except SchemaValidationError as exc:
        raise EraCertificationError(f"cannot emit certification: {exc}") from exc
    _write_json(output_path, certification)
    return EraCertificationResult(
        certification["certification_id"], certification["pass_id"], "accepted",
        str(output_path), str(benchmark_path), runtime_manifest["counts"]["provinces"],
        runtime_manifest["counts"]["components"],
    )


def validate_certification_bundle(path: Path | str) -> dict[str, Any]:
    """Validate an accepted manifest and every pinned artifact byte."""
    manifest_path = Path(path).resolve()
    document = _load_json(manifest_path, "global certification")
    try:
        validate_global_certification_manifest(document)
    except SchemaValidationError as exc:
        raise EraCertificationError(str(exc)) from exc
    for role, record in document["artifacts"].items():
        artifact = _bundle_artifact(manifest_path.parent, record["path"], role)
        if not artifact.is_file() or _sha256(artifact) != record["sha256"]:
            raise EraCertificationError(f"certification artifact is missing or altered: {role}")
    benchmark_path = _bundle_artifact(
        manifest_path.parent,
        document["artifacts"]["runtime_benchmark"]["path"],
        "runtime_benchmark",
    )
    benchmark = _load_json(benchmark_path, "runtime benchmark")
    if benchmark.get("status") != "pass" or any(value != "pass" for value in (benchmark.get("gates") or {}).values()):
        raise EraCertificationError("runtime benchmark is not accepted")
    return document


def _check_runtime_parity(canonical: dict[str, Any], runtime: RuntimePack, manifest: dict[str, Any]) -> None:
    ids = runtime.ids
    expected = {
        "components": sorted(row["territory_component_id"] for row in canonical["components"]),
        "provinces": sorted(row["province_id"] for row in canonical["provinces"]),
        "political_units": sorted({row["political_unit_id"] for row in canonical["political_units"]} | set(canonical.get("external_actor_ids") or [])),
    }
    for kind, stable_ids in expected.items():
        if ids[kind] != stable_ids:
            raise EraCertificationError(f"canonical/runtime stable-ID parity failed for {kind}")
        for index, stable_id in enumerate(stable_ids):
            if runtime.dense_index(kind, stable_id) != index or runtime.stable_id(kind, index) != stable_id:
                raise EraCertificationError(f"canonical/runtime dense-ID round trip failed for {kind}")
    scenario_id = str(canonical.get("scenario_id") or canonical["start_date"])
    actual = {(row["subject_id"], row["relationship"], row["actor_political_unit_id"]) for row in runtime.scenario_statuses(scenario_id)}
    expected_status = {(row["subject_id"], row["relationship"], row["actor_political_unit_id"]) for row in canonical["statuses"]}
    if actual != expected_status:
        raise EraCertificationError("canonical/runtime typed-status parity failed")
    for province in canonical["provinces"]:
        hierarchy = province.get("hierarchy") or province
        if not all(hierarchy.get(f"{level}_id") for level in ("area", "region", "superregion")):
            raise EraCertificationError(f"canonical hierarchy is incomplete for {province['province_id']}")
    for row in canonical.get("adjacency") or []:
        graph = str(row.get("type", "land"))
        left = str(row.get("from_province_id") or row.get("from"))
        right = str(row.get("to_province_id") or row.get("to"))
        left_index, right_index = runtime.dense_index("provinces", left), runtime.dense_index("provinces", right)
        if right_index not in runtime.neighbors(left_index, graph=graph) or left_index not in runtime.neighbors(right_index, graph=graph):
            raise EraCertificationError(f"canonical/runtime adjacency parity failed for {left}/{right}")
    migration = json.loads((runtime.root / manifest["entrypoints"]["migration"]).read_text(encoding="utf-8"))
    for old_id, new_id in migration.get("province_id_map", {}).items():
        if new_id not in expected["provinces"] or runtime.migration_target(old_id) != new_id:
            raise EraCertificationError(f"invalid save migration: {old_id} -> {new_id}")
    if manifest["counts"]["scenarios"] != 1:
        raise EraCertificationError("certified era runtime must contain exactly one scenario")


def _check_deterministic_compilation(canonical: Path, pack_id: str, compatibility_revision: str) -> None:
    try:
        with tempfile.TemporaryDirectory(prefix="gpm-m25c-") as temporary:
            root = Path(temporary)
            left, right = root / "left", root / "right"
            compile_runtime_pack(canonical, left, pack_id=pack_id, compatibility_revision=compatibility_revision, max_zoom=0)
            compile_runtime_pack(canonical, right, pack_id=pack_id, compatibility_revision=compatibility_revision, max_zoom=0)
            if _tree_hashes(left) != _tree_hashes(right):
                raise EraCertificationError("two clean M25B compilations were not byte-identical")
    except RuntimeCompileError as exc:
        raise EraCertificationError(f"deterministic runtime recompilation failed: {exc}") from exc


def _benchmark_document(runtime_manifest: dict[str, Any], benchmark: dict[str, Any]) -> dict[str, Any]:
    sizes = runtime_manifest["size_metrics"]
    measurements = {
        **{key: sizes[key] for key in PERFORMANCE_LIMITS if key in sizes},
        "load_p95_ms": benchmark["load_ms"]["p95"],
        "tile_read_p95_ms": benchmark["tile_read_ms"]["p95"],
    }
    gates = {key: "pass" if measurements[key] <= limit else "fail" for key, limit in PERFORMANCE_LIMITS.items()}
    return {
        "schema_version": "1.0.0", "report_type": "m25c-runtime-benchmark",
        "pack_id": runtime_manifest["pack_id"], "status": "pass" if all(value == "pass" for value in gates.values()) else "fail",
        "measurements": measurements, "limits": PERFORMANCE_LIMITS, "gates": gates,
    }


def _record(manifest_path: Path, artifact: Path) -> dict[str, str]:
    return {"path": os.path.relpath(artifact, manifest_path.parent), "sha256": _sha256(artifact)}


def _pass_artifact(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise EraCertificationError(f"research artifact escapes pass directory: {relative}") from exc
    return path


def _bundle_artifact(root: Path, relative: str, role: str) -> Path:
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise EraCertificationError(
            f"certification artifact escapes bundle directory: {role}"
        ) from exc
    return path


def _tree_hashes(root: Path) -> dict[str, str]:
    return {path.relative_to(root).as_posix(): _sha256(path) for path in sorted(root.rglob("*")) if path.is_file()}


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise EraCertificationError(f"cannot read {label} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise EraCertificationError(f"{label} must be a JSON object")
    return value


def _write_json(path: Path, document: dict[str, Any]) -> None:
    path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
