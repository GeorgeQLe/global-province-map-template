"""M11 scenario politics QA: automated ownership and tag checks."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict, deque
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from gpm.config import load_profile
from gpm.paths import PROCESSED_DATA_DIR, PROCESSED_SCENARIO_DIR, SCENARIO_GOLDEN_DIR
from gpm.scenarios import ScenarioError, load_scenario, resolve_ownership_records
from gpm.schemas import validate_scenario_politics_qa_report

SCENARIO_QA_SCHEMA_VERSION = "0.1.0"
DEFAULT_MAX_OWNER_COMPONENTS = 25
DEFAULT_MIN_PROVINCES_FOR_FRAGMENT_CHECK = 8
UNKNOWN_TAG = "UNK"


class ScenarioPoliticsQAError(RuntimeError):
    """Raised when scenario politics QA cannot load inputs or complete its report."""


@dataclass(frozen=True)
class ScenarioPoliticsQAResult:
    profile_id: str
    scenario_id: str
    report_output: str
    status: str
    land_province_count: int
    ownership_row_count: int
    owner_tag_count: int
    error_count: int
    warning_count: int
    adjacency_analysis: str
    golden_analysis: str

    @property
    def passed(self) -> bool:
        return self.status == "pass"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_scenario_politics_qa(
    profile_id: str,
    scenario_id: str,
    *,
    province_input: Path = PROCESSED_DATA_DIR / "provinces.geojson",
    adjacency_input: Path | None = PROCESSED_DATA_DIR / "adjacency.csv",
    scenario_path: Path | None = None,
    scenario_dir: Path | None = None,
    ownership_input: Path | None = None,
    golden_input: Path | None = None,
    report_output: Path | None = None,
    allow_unknown_overrides: bool = False,
    max_owner_components: int = DEFAULT_MAX_OWNER_COMPONENTS,
    min_provinces_for_fragment_check: int = DEFAULT_MIN_PROVINCES_FOR_FRAGMENT_CHECK,
) -> ScenarioPoliticsQAResult:
    """Resolve (or load) ownership and emit a politics QA report for one scenario."""
    load_profile(profile_id)
    scenario = load_scenario(
        scenario_id,
        scenario_dir=scenario_dir,
        scenario_path=scenario_path,
    )
    actual_id = str(scenario["scenario_id"])

    province_path = Path(province_input)
    land_features, land_ids = _load_land_features(province_path)
    records = _load_or_resolve_records(
        scenario,
        land_features,
        ownership_input=ownership_input,
        allow_unknown_overrides=allow_unknown_overrides,
    )

    adjacency_path = _optional_file(adjacency_input)
    land_adjacency = _load_land_adjacency(adjacency_path) if adjacency_path is not None else None
    golden_path = _resolve_golden_path(actual_id, golden_input)
    golden = _load_golden(golden_path) if golden_path is not None else None

    findings: list[dict[str, Any]] = []
    _check_coverage(land_ids, records, findings)
    _check_required_fields(records, findings)
    _check_unknown_and_orphan_tags(scenario, records, findings)
    _check_unk_owners(records, findings)

    adjacency_analysis = "skipped"
    if land_adjacency is None:
        _add_finding(
            findings,
            "ADJACENCY_ANALYSIS_SKIPPED",
            "warning",
            [],
            "Land adjacency was not available; owner-component sanity checks were skipped.",
        )
    else:
        adjacency_analysis = "complete"
        _check_owner_components(
            records,
            land_adjacency,
            findings,
            max_owner_components=max_owner_components,
            min_provinces_for_fragment_check=min_provinces_for_fragment_check,
        )

    golden_analysis = "skipped"
    if golden is not None:
        golden_analysis = "complete"
        _check_golden(records, golden, findings)

    findings.sort(key=_finding_sort_key)
    error_count = sum(item["severity"] == "error" for item in findings)
    warning_count = sum(item["severity"] == "warning" for item in findings)
    status = "fail" if error_count else "pass"
    owner_tags = sorted({str(row["owner"]) for row in records if row.get("owner")})

    out_path = (
        Path(report_output)
        if report_output is not None
        else PROCESSED_SCENARIO_DIR / actual_id / "politics_qa.json"
    )

    report = {
        "schema_version": SCENARIO_QA_SCHEMA_VERSION,
        "report_type": "scenario_politics_qa",
        "milestone": "M11",
        "profile_id": profile_id,
        "scenario_id": actual_id,
        "status": status,
        "inputs": {
            "province_input": str(province_path),
            "adjacency_input": None if adjacency_path is None else str(adjacency_path),
            "scenario_definition": scenario.get("_path"),
            "ownership_input": None if ownership_input is None else str(ownership_input),
            "golden_input": None if golden_input is None else str(golden_input),
        },
        "thresholds": {
            "max_owner_components": max_owner_components,
            "min_provinces_for_fragment_check": min_provinces_for_fragment_check,
        },
        "summary": {
            "land_province_count": len(land_ids),
            "ownership_row_count": len(records),
            "owner_tag_count": len(owner_tags),
            "error_count": error_count,
            "warning_count": warning_count,
            "unknown_tag_finding_count": sum(
                1 for item in findings if item["code"].startswith("UNKNOWN_")
            ),
            "orphan_tag_finding_count": sum(
                1 for item in findings if item["code"].startswith("ORPHAN_")
            ),
            "analysis": {
                "adjacency": adjacency_analysis,
                "golden": golden_analysis,
            },
        },
        "findings": findings,
    }
    validate_scenario_politics_qa_report(report)

    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        raise ScenarioPoliticsQAError(f"Cannot write scenario politics QA report {out_path}: {exc}") from exc

    return ScenarioPoliticsQAResult(
        profile_id=profile_id,
        scenario_id=actual_id,
        report_output=str(out_path),
        status=status,
        land_province_count=len(land_ids),
        ownership_row_count=len(records),
        owner_tag_count=len(owner_tags),
        error_count=error_count,
        warning_count=warning_count,
        adjacency_analysis=adjacency_analysis,
        golden_analysis=golden_analysis,
    )


def _load_land_features(path: Path) -> tuple[list[dict[str, Any]], set[str]]:
    if not path.is_file():
        raise ScenarioPoliticsQAError(f"Province input does not exist: {path}")
    try:
        collection = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ScenarioPoliticsQAError(f"Province input is not valid JSON: {path}: {exc}") from exc
    except OSError as exc:
        raise ScenarioPoliticsQAError(f"Unable to read province input {path}: {exc}") from exc

    if not isinstance(collection, dict) or collection.get("type") != "FeatureCollection":
        raise ScenarioPoliticsQAError(f"Province input must be a GeoJSON FeatureCollection: {path}")
    features = collection.get("features")
    if not isinstance(features, list):
        raise ScenarioPoliticsQAError(f"Province input features must be an array: {path}")

    land_features: list[dict[str, Any]] = []
    land_ids: set[str] = set()
    for index, feature in enumerate(features):
        if not isinstance(feature, dict):
            continue
        properties = feature.get("properties")
        if not isinstance(properties, dict):
            continue
        kind = properties.get("kind", "land")
        if kind not in (None, "land"):
            continue
        province_id = properties.get("province_id")
        if not isinstance(province_id, str) or not province_id.strip():
            raise ScenarioPoliticsQAError(f"Land province feature {index} is missing province_id")
        province_id = province_id.strip()
        if province_id in land_ids:
            raise ScenarioPoliticsQAError(f"Duplicate land province_id in input: {province_id}")
        land_ids.add(province_id)
        land_features.append(feature)

    if not land_features:
        raise ScenarioPoliticsQAError(f"Province input has no land features: {path}")
    return land_features, land_ids


def _load_or_resolve_records(
    scenario: dict[str, Any],
    land_features: list[dict[str, Any]],
    *,
    ownership_input: Path | None,
    allow_unknown_overrides: bool,
) -> list[dict[str, Any]]:
    if ownership_input is not None:
        path = Path(ownership_input)
        if not path.is_file():
            raise ScenarioPoliticsQAError(f"Ownership input does not exist: {path}")
        try:
            if path.suffix.lower() == ".csv":
                return _load_ownership_csv(path)
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ScenarioPoliticsQAError(f"Ownership JSON is invalid: {path}: {exc}") from exc
        except OSError as exc:
            raise ScenarioPoliticsQAError(f"Unable to read ownership input {path}: {exc}") from exc
        if isinstance(payload, dict) and isinstance(payload.get("records"), list):
            return [dict(row) for row in payload["records"] if isinstance(row, dict)]
        if isinstance(payload, list):
            return [dict(row) for row in payload if isinstance(row, dict)]
        raise ScenarioPoliticsQAError(
            f"Ownership JSON must be a record list or object with records: {path}"
        )

    try:
        records, _stats = resolve_ownership_records(
            scenario,
            land_features,
            allow_unknown_overrides=allow_unknown_overrides,
        )
    except ScenarioError as exc:
        raise ScenarioPoliticsQAError(str(exc)) from exc
    return records


def _load_ownership_csv(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                cores = _parse_json_list_cell(row.get("cores"))
                claims = _parse_json_list_cell(row.get("claims"))
                disputed_raw = (row.get("disputed") or "").strip().lower()
                records.append(
                    {
                        "province_id": (row.get("province_id") or "").strip(),
                        "scenario_id": (row.get("scenario_id") or "").strip() or None,
                        "owner": (row.get("owner") or "").strip() or None,
                        "controller": (row.get("controller") or "").strip() or None,
                        "cores": cores,
                        "claims": claims,
                        "culture": (row.get("culture") or "").strip() or None,
                        "religion": (row.get("religion") or "").strip() or None,
                        "disputed": disputed_raw in {"1", "true", "yes"},
                        "assignment_source": (row.get("assignment_source") or "").strip() or None,
                        "parent_country_id": (row.get("parent_country_id") or "").strip() or None,
                        "parent_region_id": (row.get("parent_region_id") or "").strip() or None,
                        "display_name": (row.get("display_name") or "").strip() or None,
                        "notes": (row.get("notes") or "").strip() or None,
                    }
                )
    except OSError as exc:
        raise ScenarioPoliticsQAError(f"Unable to read ownership CSV {path}: {exc}") from exc
    return records


def _parse_json_list_cell(value: str | None) -> list[str]:
    if value is None or value == "":
        return []
    text = value.strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return [part.strip() for part in text.split(",") if part.strip()]
    if isinstance(parsed, list):
        return [str(item) for item in parsed if str(item).strip()]
    if parsed is None:
        return []
    return [str(parsed)]


def _optional_file(path: Path | None) -> Path | None:
    if path is None:
        return None
    resolved = Path(path)
    if not resolved.exists():
        return None
    if not resolved.is_file():
        raise ScenarioPoliticsQAError(f"Path is not a file: {resolved}")
    return resolved


def _load_land_adjacency(path: Path) -> dict[str, set[str]]:
    graph: dict[str, set[str]] = defaultdict(set)
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                raise ScenarioPoliticsQAError(f"Adjacency CSV has no header: {path}")
            for row in reader:
                left = (row.get("from_province_id") or "").strip()
                right = (row.get("to_province_id") or "").strip()
                adj_type = (row.get("adjacency_type") or "land").strip().lower()
                if not left or not right:
                    continue
                if adj_type not in {"land", "strait"}:
                    continue
                graph[left].add(right)
                graph[right].add(left)
    except OSError as exc:
        raise ScenarioPoliticsQAError(f"Unable to read adjacency CSV {path}: {exc}") from exc
    return dict(graph)


def _resolve_golden_path(
    scenario_id: str,
    golden_input: Path | None,
) -> Path | None:
    """Return an explicit golden path, or the bundled default when present.

    Bundled convention: ``configs/scenarios/golden/<scenario_id>.json``.
    """
    if golden_input is not None:
        return Path(golden_input)
    default_path = SCENARIO_GOLDEN_DIR / f"{scenario_id}.json"
    if default_path.is_file():
        return default_path
    return None


def _load_golden(path: Path) -> dict[str, Any]:
    resolved = Path(path)
    if not resolved.is_file():
        raise ScenarioPoliticsQAError(f"Golden check file does not exist: {resolved}")
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ScenarioPoliticsQAError(f"Golden check file is not valid JSON: {resolved}: {exc}") from exc
    except OSError as exc:
        raise ScenarioPoliticsQAError(f"Unable to read golden check file {resolved}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ScenarioPoliticsQAError(f"Golden check file must be a JSON object: {resolved}")
    return payload


def _check_coverage(
    land_ids: set[str],
    records: list[dict[str, Any]],
    findings: list[dict[str, Any]],
) -> None:
    seen: list[str] = []
    for row in records:
        province_id = row.get("province_id")
        if not isinstance(province_id, str) or not province_id.strip():
            _add_finding(
                findings,
                "MALFORMED_OWNERSHIP_ROW",
                "error",
                [],
                "Ownership row is missing province_id.",
            )
            continue
        seen.append(province_id.strip())

    counts = Counter(seen)
    for province_id, count in sorted(counts.items()):
        if count > 1:
            _add_finding(
                findings,
                "DUPLICATE_OWNERSHIP_ROW",
                "error",
                [province_id],
                f"Ownership table has {count} rows for province {province_id!r}.",
                occurrence_count=count,
            )

    unique_ids = set(counts)
    for province_id in sorted(land_ids - unique_ids):
        _add_finding(
            findings,
            "MISSING_OWNERSHIP_ROW",
            "error",
            [province_id],
            f"Land province {province_id!r} has no ownership row.",
        )
    for province_id in sorted(unique_ids - land_ids):
        _add_finding(
            findings,
            "EXTRA_OWNERSHIP_ROW",
            "error",
            [province_id],
            f"Ownership row references unknown or non-land province {province_id!r}.",
        )


def _check_required_fields(records: list[dict[str, Any]], findings: list[dict[str, Any]]) -> None:
    for row in records:
        province_id = row.get("province_id")
        if not isinstance(province_id, str) or not province_id.strip():
            continue
        province_id = province_id.strip()
        owner = row.get("owner")
        controller = row.get("controller")
        if not isinstance(owner, str) or not owner.strip():
            _add_finding(
                findings,
                "MISSING_OWNER",
                "error",
                [province_id],
                f"Province {province_id!r} is missing owner.",
            )
        if not isinstance(controller, str) or not controller.strip():
            _add_finding(
                findings,
                "MISSING_CONTROLLER",
                "error",
                [province_id],
                f"Province {province_id!r} is missing controller.",
            )


def _check_unknown_and_orphan_tags(
    scenario: dict[str, Any],
    records: list[dict[str, Any]],
    findings: list[dict[str, Any]],
) -> None:
    countries = scenario.get("countries") if isinstance(scenario.get("countries"), dict) else {}
    catalog = {str(tag).strip() for tag in countries if str(tag).strip()}
    enforce_catalog = bool(catalog)

    owners: set[str] = set()
    controllers: set[str] = set()
    cores: set[str] = set()
    claims: set[str] = set()
    core_provinces: dict[str, list[str]] = defaultdict(list)
    claim_provinces: dict[str, list[str]] = defaultdict(list)

    for row in records:
        province_id = row.get("province_id")
        if not isinstance(province_id, str) or not province_id.strip():
            continue
        province_id = province_id.strip()
        owner = _tag_or_none(row.get("owner"))
        controller = _tag_or_none(row.get("controller"))
        if owner:
            owners.add(owner)
        if controller:
            controllers.add(controller)
        for core in _tag_list(row.get("cores")):
            cores.add(core)
            core_provinces[core].append(province_id)
        for claim in _tag_list(row.get("claims")):
            claims.add(claim)
            claim_provinces[claim].append(province_id)

    if enforce_catalog:
        for role, tags, code in (
            ("owner", owners, "UNKNOWN_OWNER_TAG"),
            ("controller", controllers, "UNKNOWN_CONTROLLER_TAG"),
            ("core", cores, "UNKNOWN_CORE_TAG"),
            ("claim", claims, "UNKNOWN_CLAIM_TAG"),
        ):
            for tag in sorted(tags):
                if tag == UNKNOWN_TAG:
                    continue
                if tag not in catalog:
                    affected = (
                        core_provinces[tag][:20]
                        if role == "core"
                        else claim_provinces[tag][:20]
                        if role == "claim"
                        else [
                            str(row["province_id"])
                            for row in records
                            if _tag_or_none(row.get(role if role != "core" else "owner")) == tag
                        ][:20]
                    )
                    if role == "owner":
                        affected = [
                            str(row["province_id"])
                            for row in records
                            if _tag_or_none(row.get("owner")) == tag
                        ][:20]
                    elif role == "controller":
                        affected = [
                            str(row["province_id"])
                            for row in records
                            if _tag_or_none(row.get("controller")) == tag
                        ][:20]
                    _add_finding(
                        findings,
                        code,
                        "warning",
                        sorted(affected),
                        f"Tag {tag!r} is used as {role} but is not defined in scenario.countries.",
                        tag=tag,
                        role=role,
                    )

    for core in sorted(cores):
        if core == UNKNOWN_TAG:
            continue
        if core not in owners:
            _add_finding(
                findings,
                "ORPHAN_CORE",
                "warning",
                sorted(core_provinces[core])[:40],
                f"Core tag {core!r} never appears as owner of any province.",
                tag=core,
                province_count=len(core_provinces[core]),
            )
    for claim in sorted(claims):
        if claim == UNKNOWN_TAG:
            continue
        if claim not in owners:
            _add_finding(
                findings,
                "ORPHAN_CLAIM",
                "warning",
                sorted(claim_provinces[claim])[:40],
                f"Claim tag {claim!r} never appears as owner of any province.",
                tag=claim,
                province_count=len(claim_provinces[claim]),
            )


def _check_unk_owners(records: list[dict[str, Any]], findings: list[dict[str, Any]]) -> None:
    unk_ids = [
        str(row["province_id"])
        for row in records
        if isinstance(row.get("province_id"), str) and _tag_or_none(row.get("owner")) == UNKNOWN_TAG
    ]
    if not unk_ids:
        return
    _add_finding(
        findings,
        "UNK_OWNER",
        "warning",
        sorted(unk_ids)[:50],
        f"{len(unk_ids)} province(s) have owner UNK (missing modern parent_country_id or explicit unknown).",
        province_count=len(unk_ids),
    )


def _check_owner_components(
    records: list[dict[str, Any]],
    adjacency: dict[str, set[str]],
    findings: list[dict[str, Any]],
    *,
    max_owner_components: int,
    min_provinces_for_fragment_check: int,
) -> None:
    by_owner: dict[str, list[str]] = defaultdict(list)
    for row in records:
        province_id = row.get("province_id")
        owner = _tag_or_none(row.get("owner"))
        if not isinstance(province_id, str) or not province_id.strip() or not owner:
            continue
        if owner == UNKNOWN_TAG:
            continue
        by_owner[owner].append(province_id.strip())

    for owner, province_ids in sorted(by_owner.items()):
        if len(province_ids) < min_provinces_for_fragment_check:
            continue
        component_count, largest = _component_stats(province_ids, adjacency)
        if component_count > max_owner_components:
            _add_finding(
                findings,
                "FRAGMENT_OWNER_COMPONENTS",
                "warning",
                sorted(province_ids)[:40],
                (
                    f"Owner {owner!r} has {component_count} disconnected land/strait components "
                    f"(threshold {max_owner_components}) across {len(province_ids)} provinces."
                ),
                owner=owner,
                component_count=component_count,
                province_count=len(province_ids),
                largest_component_size=largest,
                configured_limit=max_owner_components,
            )


def _component_stats(province_ids: list[str], adjacency: dict[str, set[str]]) -> tuple[int, int]:
    remaining = set(province_ids)
    components = 0
    largest = 0
    while remaining:
        start = next(iter(remaining))
        queue: deque[str] = deque([start])
        remaining.remove(start)
        size = 0
        while queue:
            current = queue.popleft()
            size += 1
            for neighbor in adjacency.get(current, ()):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    queue.append(neighbor)
        components += 1
        largest = max(largest, size)
    return components, largest


def _check_golden(
    records: list[dict[str, Any]],
    golden: dict[str, Any],
    findings: list[dict[str, Any]],
) -> None:
    by_id = {
        str(row["province_id"]): row
        for row in records
        if isinstance(row.get("province_id"), str) and row["province_id"]
    }

    province_owners = golden.get("province_owners")
    if province_owners is not None:
        if not isinstance(province_owners, dict):
            _add_finding(
                findings,
                "GOLDEN_CONFIG_INVALID",
                "error",
                [],
                "golden.province_owners must be an object of province_id → owner tag.",
            )
        else:
            for province_id, expected_owner in sorted(province_owners.items(), key=lambda item: str(item[0])):
                pid = str(province_id)
                expected = str(expected_owner).strip()
                row = by_id.get(pid)
                if row is None:
                    _add_finding(
                        findings,
                        "GOLDEN_OWNER_MISMATCH",
                        "error",
                        [pid],
                        f"Golden owner check missing province {pid!r}.",
                        expected_owner=expected,
                    )
                    continue
                actual = _tag_or_none(row.get("owner"))
                if actual != expected:
                    _add_finding(
                        findings,
                        "GOLDEN_OWNER_MISMATCH",
                        "error",
                        [pid],
                        f"Golden owner for {pid!r}: expected {expected!r}, found {actual!r}.",
                        expected_owner=expected,
                        actual_owner=actual,
                    )

    min_owner_counts = golden.get("min_owner_counts")
    if min_owner_counts is not None:
        if not isinstance(min_owner_counts, dict):
            _add_finding(
                findings,
                "GOLDEN_CONFIG_INVALID",
                "error",
                [],
                "golden.min_owner_counts must be an object of owner tag → minimum province count.",
            )
        else:
            counts = Counter(
                tag
                for row in records
                if (tag := _tag_or_none(row.get("owner"))) is not None
            )
            for owner, minimum in sorted(min_owner_counts.items(), key=lambda item: str(item[0])):
                tag = str(owner).strip()
                try:
                    required = int(minimum)
                except (TypeError, ValueError):
                    _add_finding(
                        findings,
                        "GOLDEN_CONFIG_INVALID",
                        "error",
                        [],
                        f"golden.min_owner_counts[{tag!r}] must be an integer.",
                    )
                    continue
                actual = counts.get(tag, 0)
                if actual < required:
                    affected = [
                        str(row["province_id"])
                        for row in records
                        if _tag_or_none(row.get("owner")) == tag
                        and isinstance(row.get("province_id"), str)
                    ][:40]
                    _add_finding(
                        findings,
                        "GOLDEN_MIN_COUNT_FAILED",
                        "error",
                        affected,
                        f"Owner {tag!r} has {actual} province(s); golden minimum is {required}.",
                        owner=tag,
                        actual_count=actual,
                        minimum_count=required,
                    )


def _tag_or_none(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _tag_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return _parse_json_list_cell(value)
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()] if str(value).strip() else []


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
            "affected_ids": sorted({item for item in affected_ids if item}),
            "message": message,
            "measurements": measurements,
        }
    )


def _finding_sort_key(finding: dict[str, Any]) -> tuple[Any, ...]:
    severity_rank = 0 if finding.get("severity") == "error" else 1
    return (
        severity_rank,
        str(finding.get("code") or ""),
        tuple(finding.get("affected_ids") or []),
        str(finding.get("message") or ""),
    )
