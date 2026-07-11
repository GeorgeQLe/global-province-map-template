"""External curator scenario bundles with manifests (M17).

A curator bundle is a self-contained directory of scenario definitions and
optional golden check files that can live outside ``configs/scenarios/``.
"""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from gpm.paths import PROJECT_ROOT, SAMPLE_DIR
from gpm.scenarios import ScenarioError, load_scenario, validate_scenario_document

CURATOR_BUNDLE_SCHEMA_VERSION = "0.1.0"
BUNDLE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
MANIFEST_NAMES = ("bundle_manifest.json", "curator_bundle.json", "manifest.json")


class CuratorBundleError(RuntimeError):
    """Raised when a curator bundle cannot be loaded or validated."""


@dataclass(frozen=True)
class CuratorBundleSummary:
    bundle_id: str
    display_name: str
    license: str
    path: str
    scenario_ids: tuple[str, ...]
    golden_count: int
    author: str | None = None
    recommended_profile: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def list_curator_bundles(*, search_dirs: list[Path] | None = None) -> list[CuratorBundleSummary]:
    """Discover curator bundles under sample and optional search directories."""
    roots = search_dirs if search_dirs is not None else _default_search_dirs()
    summaries: list[CuratorBundleSummary] = []
    seen: set[str] = set()
    for root in roots:
        if not root.is_dir():
            continue
        for candidate in sorted(root.iterdir()):
            if not candidate.is_dir():
                continue
            manifest_path = _find_manifest(candidate)
            if manifest_path is None:
                continue
            try:
                document = load_curator_bundle(candidate)
                summary = _summary_from_document(document, candidate)
            except CuratorBundleError:
                continue
            if summary.bundle_id in seen:
                continue
            seen.add(summary.bundle_id)
            summaries.append(summary)
    return summaries


def load_curator_bundle(
    bundle: str | Path,
    *,
    search_dirs: list[Path] | None = None,
) -> dict[str, Any]:
    """Load a curator bundle by directory path, manifest path, or bundle id."""
    root, manifest_path = _resolve_bundle_root(bundle, search_dirs=search_dirs)
    try:
        document = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CuratorBundleError(f"Bundle manifest is not valid JSON: {manifest_path}: {exc}") from exc
    except OSError as exc:
        raise CuratorBundleError(f"Unable to read bundle manifest {manifest_path}: {exc}") from exc
    if not isinstance(document, dict):
        raise CuratorBundleError(f"Bundle manifest must be a JSON object: {manifest_path}")
    validate_curator_bundle(document, bundle_root=root, check_files=False)
    document = dict(document)
    document["_path"] = str(manifest_path)
    document["_root"] = str(root)
    return document


def validate_curator_bundle(
    document: dict[str, Any],
    *,
    bundle_root: Path | None = None,
    check_files: bool = True,
    check_scenarios: bool = True,
) -> None:
    """Validate a curator-bundle manifest and optionally its on-disk scenario files."""
    if not isinstance(document, dict):
        raise CuratorBundleError("Bundle manifest must be an object")
    for key in (
        "schema_version",
        "document_type",
        "bundle_id",
        "display_name",
        "license",
        "scenarios",
    ):
        if key not in document:
            raise CuratorBundleError(f"Bundle manifest missing required field: {key}")
    if document["schema_version"] != CURATOR_BUNDLE_SCHEMA_VERSION:
        raise CuratorBundleError(
            f"schema_version must be {CURATOR_BUNDLE_SCHEMA_VERSION!r}, "
            f"got {document['schema_version']!r}"
        )
    if document["document_type"] != "curator-bundle":
        raise CuratorBundleError("document_type must be 'curator-bundle'")
    bundle_id = document["bundle_id"]
    if not isinstance(bundle_id, str) or not BUNDLE_ID_RE.match(bundle_id):
        raise CuratorBundleError(
            "bundle_id must match ^[a-z0-9][a-z0-9._-]*$"
        )
    if not isinstance(document["display_name"], str) or not document["display_name"].strip():
        raise CuratorBundleError("display_name must be a non-empty string")
    if not isinstance(document["license"], str) or not document["license"].strip():
        raise CuratorBundleError("license must be a non-empty string")

    scenarios = document["scenarios"]
    if not isinstance(scenarios, list) or not scenarios:
        raise CuratorBundleError("scenarios must be a non-empty list")

    seen_ids: set[str] = set()
    for index, entry in enumerate(scenarios):
        path = f"scenarios[{index}]"
        if not isinstance(entry, dict):
            raise CuratorBundleError(f"{path} must be an object")
        scenario_id = entry.get("scenario_id")
        rel_path = entry.get("path")
        if not isinstance(scenario_id, str) or not BUNDLE_ID_RE.match(scenario_id):
            raise CuratorBundleError(f"{path}.scenario_id is invalid")
        if scenario_id in seen_ids:
            raise CuratorBundleError(f"{path}.scenario_id duplicates {scenario_id!r}")
        seen_ids.add(scenario_id)
        if not isinstance(rel_path, str) or not rel_path.strip():
            raise CuratorBundleError(f"{path}.path must be a non-empty string")
        if Path(rel_path).is_absolute() or ".." in Path(rel_path).parts:
            raise CuratorBundleError(f"{path}.path must be a relative path without '..'")
        golden_path = entry.get("golden_path")
        if golden_path is not None:
            if not isinstance(golden_path, str) or not golden_path.strip():
                raise CuratorBundleError(f"{path}.golden_path must be a non-empty string when present")
            if Path(golden_path).is_absolute() or ".." in Path(golden_path).parts:
                raise CuratorBundleError(f"{path}.golden_path must be a relative path without '..'")

    for list_key in ("source_lineage", "license_lineage"):
        value = document.get(list_key)
        if value is None:
            continue
        if not isinstance(value, list) or not all(
            isinstance(item, str) and item.strip() for item in value
        ):
            raise CuratorBundleError(f"{list_key} must be a list of non-empty strings when present")

    checklist = document.get("checklist")
    if checklist is not None:
        if not isinstance(checklist, dict):
            raise CuratorBundleError("checklist must be an object when present")
        for flag in (
            "sources_documented",
            "licenses_reviewed",
            "golden_borders_present",
            "qa_pass_claimed",
            "no_restricted_sources",
        ):
            if flag in checklist and not isinstance(checklist[flag], bool):
                raise CuratorBundleError(f"checklist.{flag} must be a boolean when present")

    deprecation = document.get("deprecation")
    if deprecation is not None and not isinstance(deprecation, dict):
        raise CuratorBundleError("deprecation must be an object when present")

    if not check_files or bundle_root is None:
        return

    root = Path(bundle_root)
    if not root.is_dir():
        raise CuratorBundleError(f"Bundle root is not a directory: {root}")

    for index, entry in enumerate(document["scenarios"]):
        rel_path = str(entry["path"])
        scenario_file = (root / rel_path).resolve()
        if not str(scenario_file).startswith(str(root.resolve())):
            raise CuratorBundleError(f"scenarios[{index}].path escapes bundle root: {rel_path}")
        if not scenario_file.is_file():
            raise CuratorBundleError(f"Scenario file missing: {scenario_file}")
        if check_scenarios:
            try:
                scenario = json.loads(scenario_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise CuratorBundleError(
                    f"Unable to read scenario {scenario_file}: {exc}"
                ) from exc
            if not isinstance(scenario, dict):
                raise CuratorBundleError(f"Scenario must be a JSON object: {scenario_file}")
            try:
                validate_scenario_document(scenario, path=scenario_file)
            except ScenarioError as exc:
                raise CuratorBundleError(
                    f"Invalid scenario in bundle ({rel_path}): {exc}"
                ) from exc
            declared = str(entry["scenario_id"])
            actual = str(scenario.get("scenario_id", ""))
            if actual != declared:
                raise CuratorBundleError(
                    f"scenarios[{index}].scenario_id {declared!r} does not match "
                    f"file scenario_id {actual!r}"
                )
        golden_rel = entry.get("golden_path")
        if golden_rel:
            golden_file = (root / str(golden_rel)).resolve()
            if not str(golden_file).startswith(str(root.resolve())):
                raise CuratorBundleError(
                    f"scenarios[{index}].golden_path escapes bundle root: {golden_rel}"
                )
            if not golden_file.is_file():
                raise CuratorBundleError(f"Golden file missing: {golden_file}")
            try:
                golden = json.loads(golden_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise CuratorBundleError(f"Unable to read golden file {golden_file}: {exc}") from exc
            if not isinstance(golden, dict):
                raise CuratorBundleError(f"Golden file must be a JSON object: {golden_file}")


def import_curator_bundle(
    bundle: str | Path,
    *,
    output_dir: Path,
    search_dirs: list[Path] | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Copy a validated curator bundle into ``output_dir`` for local use.

    Writes a small import manifest summarizing copied scenarios and golden files.
    """
    document = load_curator_bundle(bundle, search_dirs=search_dirs)
    root = Path(document["_root"])
    validate_curator_bundle(document, bundle_root=root, check_files=True, check_scenarios=True)

    out = Path(output_dir)
    if out.exists() and any(out.iterdir()) and not overwrite:
        raise CuratorBundleError(
            f"Output directory is not empty (pass overwrite=True to replace): {out}"
        )
    if out.exists() and overwrite:
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    # Copy entire tree (manifest + scenarios + golden + docs).
    for item in root.iterdir():
        dest = out / item.name
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)

    files_copied: list[str] = []
    for path in sorted(out.rglob("*")):
        if path.is_file():
            files_copied.append(str(path.relative_to(out)))

    import_manifest = {
        "schema_version": CURATOR_BUNDLE_SCHEMA_VERSION,
        "document_type": "curator-bundle-import",
        "bundle_id": document["bundle_id"],
        "source_root": str(root),
        "output_dir": str(out),
        "scenario_ids": [entry["scenario_id"] for entry in document["scenarios"]],
        "files": files_copied,
    }
    import_path = out / "import_manifest.json"
    import_path.write_text(
        json.dumps(import_manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return import_manifest


def scenario_path_in_bundle(document: dict[str, Any], scenario_id: str) -> Path:
    """Return the absolute path to a scenario file inside a loaded bundle."""
    root = Path(document.get("_root") or ".")
    for entry in document.get("scenarios") or []:
        if entry.get("scenario_id") == scenario_id:
            return root / str(entry["path"])
    raise CuratorBundleError(f"Scenario {scenario_id!r} not listed in bundle")


def golden_path_in_bundle(document: dict[str, Any], scenario_id: str) -> Path | None:
    """Return the absolute golden path for a scenario if declared."""
    root = Path(document.get("_root") or ".")
    for entry in document.get("scenarios") or []:
        if entry.get("scenario_id") == scenario_id:
            golden = entry.get("golden_path")
            if not golden:
                return None
            return root / str(golden)
    raise CuratorBundleError(f"Scenario {scenario_id!r} not listed in bundle")


def load_bundle_scenario(document: dict[str, Any], scenario_id: str) -> dict[str, Any]:
    """Load and validate one scenario from a bundle."""
    path = scenario_path_in_bundle(document, scenario_id)
    return load_scenario(scenario_id, scenario_path=path)


def _default_search_dirs() -> list[Path]:
    dirs = [
        SAMPLE_DIR,
        PROJECT_ROOT / "bundles",
        PROJECT_ROOT / "curator_bundles",
    ]
    return dirs


def _find_manifest(directory: Path) -> Path | None:
    for name in MANIFEST_NAMES:
        candidate = directory / name
        if candidate.is_file():
            return candidate
    return None


def _resolve_bundle_root(
    bundle: str | Path,
    *,
    search_dirs: list[Path] | None,
) -> tuple[Path, Path]:
    path = Path(bundle)
    if path.is_file():
        root = path.parent
        return root, path
    if path.is_dir():
        manifest = _find_manifest(path)
        if manifest is None:
            raise CuratorBundleError(
                f"No bundle manifest ({', '.join(MANIFEST_NAMES)}) in {path}"
            )
        return path, manifest

    # Treat as bundle_id lookup.
    bundle_id = str(bundle)
    for root in search_dirs if search_dirs is not None else _default_search_dirs():
        if not root.is_dir():
            continue
        # Direct child named after id, or any manifest with matching id.
        direct = root / bundle_id
        if direct.is_dir():
            manifest = _find_manifest(direct)
            if manifest is not None:
                return direct, manifest
        for candidate in sorted(root.iterdir()):
            if not candidate.is_dir():
                continue
            manifest = _find_manifest(candidate)
            if manifest is None:
                continue
            try:
                payload = json.loads(manifest.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(payload, dict) and payload.get("bundle_id") == bundle_id:
                return candidate, manifest
    raise CuratorBundleError(f"Curator bundle not found: {bundle}")


def _summary_from_document(document: dict[str, Any], root: Path) -> CuratorBundleSummary:
    scenarios = document.get("scenarios") or []
    scenario_ids = tuple(str(entry["scenario_id"]) for entry in scenarios if isinstance(entry, dict))
    golden_count = sum(
        1 for entry in scenarios if isinstance(entry, dict) and entry.get("golden_path")
    )
    return CuratorBundleSummary(
        bundle_id=str(document["bundle_id"]),
        display_name=str(document["display_name"]),
        license=str(document["license"]),
        path=str(root),
        scenario_ids=scenario_ids,
        golden_count=golden_count,
        author=document.get("author") if isinstance(document.get("author"), str) else None,
        recommended_profile=(
            document.get("recommended_profile")
            if isinstance(document.get("recommended_profile"), str)
            else None
        ),
    )
