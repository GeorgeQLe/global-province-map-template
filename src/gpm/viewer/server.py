"""Local HTTP server and data preparation for the interactive review viewer."""

from __future__ import annotations

import csv
import json
import mimetypes
import threading
import webbrowser
from dataclasses import asdict, dataclass, field
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from gpm.config import load_profile
from gpm.exporters.atlas import identity_fill_color, tag_fill_color
from gpm.paths import PROCESSED_DATA_DIR
from gpm.qa.scenario import ScenarioPoliticsQAError, run_scenario_politics_qa
from gpm.scenarios import (
    ScenarioError,
    apply_province_override,
    list_scenarios,
    load_scenario,
    remove_province_override,
    resolve_ownership_records,
)


class ReviewError(RuntimeError):
    """Raised when the interactive review viewer cannot start."""


def _enrich_ownership_colors(row: dict[str, Any]) -> dict[str, Any]:
    """Attach deterministic owner/controller/culture/religion fill colors."""
    item = dict(row)
    item["owner_color"] = tag_fill_color(str(row.get("owner") or ""))
    item["controller_color"] = tag_fill_color(str(row.get("controller") or ""))
    item["culture_color"] = identity_fill_color(row.get("culture"))
    item["religion_color"] = identity_fill_color(row.get("religion"))
    return item


@dataclass(frozen=True)
class ReviewServeResult:
    profile_id: str
    host: str
    port: int
    url: str
    province_input: str
    adjacency_input: str | None
    qa_report_input: str | None
    scenario_id: str | None
    province_count: int
    adjacency_count: int
    qa_status: str | None
    qa_error_count: int
    qa_warning_count: int
    politics_qa_status: str | None
    politics_qa_error_count: int
    politics_qa_warning_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ReviewDataset:
    profile_id: str
    province_input: Path
    adjacency_input: Path | None
    qa_report_input: Path | None
    province_count: int
    adjacency_count: int
    qa_status: str | None
    qa_error_count: int
    qa_warning_count: int
    gpm_meta: dict[str, Any]
    adjacency_index: dict[str, list[dict[str, Any]]]
    qa_report: dict[str, Any] | None
    findings_by_province: dict[str, list[dict[str, Any]]]
    scenario_id: str | None = None
    scenario_path: Path | None = None
    scenario_document: dict[str, Any] | None = None
    ownership_by_id: dict[str, dict[str, Any]] = field(default_factory=dict)
    politics_qa_report: dict[str, Any] | None = None
    politics_findings_by_province: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    politics_qa_status: str | None = None
    politics_qa_error_count: int = 0
    politics_qa_warning_count: int = 0
    authoring_enabled: bool = False
    land_province_ids: set[str] = field(default_factory=set)
    m23_inputs: dict[str, Path] = field(default_factory=dict)

    def meta_payload(self) -> dict[str, Any]:
        endpoints = {
            "provinces": "/api/provinces.geojson",
            "adjacency": "/api/adjacency.json",
            "qa": "/api/qa.json",
            "meta": "/api/meta",
            "province": "/api/province/{province_id}",
            "scenarios": "/api/scenarios",
        }
        if self.scenario_id:
            endpoints.update(
                {
                    "ownership": "/api/ownership.json",
                    "politics_qa": "/api/politics-qa.json",
                    "scenario": "/api/scenario",
                    "override": "/api/scenario/override",
                }
            )
        for key in self.m23_inputs:
            endpoints[key] = f"/api/m23/{key}"
        return {
            "profile_id": self.profile_id,
            "province_input": str(self.province_input),
            "adjacency_input": None if self.adjacency_input is None else str(self.adjacency_input),
            "qa_report_input": None if self.qa_report_input is None else str(self.qa_report_input),
            "scenario_id": self.scenario_id,
            "scenario_path": None if self.scenario_path is None else str(self.scenario_path),
            "authoring_enabled": self.authoring_enabled,
            "province_count": self.province_count,
            "adjacency_count": self.adjacency_count,
            "qa_status": self.qa_status,
            "qa_error_count": self.qa_error_count,
            "qa_warning_count": self.qa_warning_count,
            "politics_qa_status": self.politics_qa_status,
            "politics_qa_error_count": self.politics_qa_error_count,
            "politics_qa_warning_count": self.politics_qa_warning_count,
            "ownership_row_count": len(self.ownership_by_id),
            "gpm": self.gpm_meta,
            "m23_inputs": {key: str(path) for key, path in self.m23_inputs.items()},
            "endpoints": endpoints,
        }

    def reload_scenario_ownership(self) -> None:
        """Re-resolve ownership and politics QA after curator edits."""
        if not self.scenario_id or self.scenario_path is None:
            return
        scenario = load_scenario(self.scenario_id, scenario_path=self.scenario_path)
        self.scenario_document = scenario
        collection = json.loads(self.province_input.read_text(encoding="utf-8"))
        land_features = [
            feature
            for feature in collection.get("features") or []
            if isinstance(feature, dict)
            and isinstance(feature.get("properties"), dict)
            and feature["properties"].get("kind", "land") in (None, "land")
        ]
        records, _stats = resolve_ownership_records(
            scenario,
            land_features,
            allow_unknown_overrides=True,
        )
        self.ownership_by_id = {row["province_id"]: row for row in records}
        self._refresh_politics_qa()

    def _refresh_politics_qa(self) -> None:
        if not self.scenario_id:
            self.politics_qa_report = None
            self.politics_findings_by_province = {
                province_id: [] for province_id in self.land_province_ids
            }
            self.politics_qa_status = None
            self.politics_qa_error_count = 0
            self.politics_qa_warning_count = 0
            return
        try:
            result = run_scenario_politics_qa(
                self.profile_id,
                self.scenario_id,
                province_input=self.province_input,
                adjacency_input=self.adjacency_input,
                scenario_path=self.scenario_path,
                allow_unknown_overrides=True,
                report_output=self.province_input.parent
                / "scenarios"
                / self.scenario_id
                / "politics_qa.json",
            )
            report_path = Path(result.report_output)
            self.politics_qa_report = json.loads(report_path.read_text(encoding="utf-8"))
            self.politics_qa_status = result.status
            self.politics_qa_error_count = result.error_count
            self.politics_qa_warning_count = result.warning_count
        except (ScenarioPoliticsQAError, ScenarioError, OSError, json.JSONDecodeError):
            self.politics_qa_report = None
            self.politics_qa_status = None
            self.politics_qa_error_count = 0
            self.politics_qa_warning_count = 0

        self.politics_findings_by_province = {
            province_id: [] for province_id in self.land_province_ids
        }
        if isinstance(self.politics_qa_report, dict):
            findings = self.politics_qa_report.get("findings")
            if isinstance(findings, list):
                for finding in findings:
                    if not isinstance(finding, dict):
                        continue
                    compact = {
                        "code": finding.get("code"),
                        "severity": finding.get("severity"),
                        "message": finding.get("message"),
                        "affected_ids": list(finding.get("affected_ids") or []),
                        "measurements": finding.get("measurements") or {},
                    }
                    for affected_id in compact["affected_ids"]:
                        if isinstance(affected_id, str) and affected_id in self.politics_findings_by_province:
                            self.politics_findings_by_province[affected_id].append(compact)


def prepare_review_dataset(
    profile_id: str,
    *,
    province_input: Path = PROCESSED_DATA_DIR / "provinces.geojson",
    adjacency_input: Path | None = PROCESSED_DATA_DIR / "adjacency.csv",
    qa_report_input: Path | None = PROCESSED_DATA_DIR / "topology_qa.json",
    location_input: Path | None = None,
    modern_reference_input: Path | None = None,
    lineage_input: Path | None = None,
    paintability_input: Path | None = None,
    aggregation_manifest_input: Path | None = None,
    scenario_id: str | None = None,
    scenario_path: Path | None = None,
    run_politics_qa: bool = True,
) -> ReviewDataset:
    """Load and index processed outputs used by the interactive review viewer."""
    load_profile(profile_id)
    province_path = Path(province_input)
    if not province_path.is_file():
        raise ReviewError(f"Province GeoJSON not found: {province_path}")

    try:
        collection = json.loads(province_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ReviewError(f"Province GeoJSON is not valid JSON: {province_path}: {error}") from error
    if not isinstance(collection, dict) or collection.get("type") != "FeatureCollection":
        raise ReviewError(f"Province input must be a GeoJSON FeatureCollection: {province_path}")

    features = collection.get("features")
    if not isinstance(features, list):
        raise ReviewError(f"Province FeatureCollection is missing a features array: {province_path}")

    province_ids: set[str] = set()
    land_province_ids: set[str] = set()
    for index, feature in enumerate(features):
        if not isinstance(feature, dict):
            raise ReviewError(f"Province feature {index} is not an object.")
        properties = feature.get("properties")
        if not isinstance(properties, dict):
            raise ReviewError(f"Province feature {index} is missing properties.")
        province_id = properties.get("province_id")
        if not isinstance(province_id, str) or not province_id:
            raise ReviewError(f"Province feature {index} is missing province_id.")
        if province_id in province_ids:
            raise ReviewError(f"Duplicate province_id in review input: {province_id}")
        province_ids.add(province_id)
        if properties.get("kind", "land") in (None, "land"):
            land_province_ids.add(province_id)

    gpm_meta = collection.get("gpm")
    if not isinstance(gpm_meta, dict):
        gpm_meta = {}

    adjacency_path = _optional_existing_path(adjacency_input, label="Adjacency CSV")
    adjacency_index: dict[str, list[dict[str, Any]]] = {province_id: [] for province_id in province_ids}
    adjacency_count = 0
    if adjacency_path is not None:
        adjacency_index, adjacency_count = _load_adjacency_index(adjacency_path, province_ids)

    qa_path = _optional_existing_path(qa_report_input, label="Topology QA report")
    qa_report: dict[str, Any] | None = None
    findings_by_province: dict[str, list[dict[str, Any]]] = {province_id: [] for province_id in province_ids}
    qa_status: str | None = None
    qa_error_count = 0
    qa_warning_count = 0
    if qa_path is not None:
        qa_report = _load_json_object(qa_path, label="Topology QA report")
        qa_status = str(qa_report.get("status") or "unknown")
        summary = qa_report.get("summary")
        if isinstance(summary, dict):
            qa_error_count = int(summary.get("error_count") or 0)
            qa_warning_count = int(summary.get("warning_count") or 0)
        findings = qa_report.get("findings")
        if isinstance(findings, list):
            for finding in findings:
                if not isinstance(finding, dict):
                    continue
                compact = {
                    "code": finding.get("code"),
                    "severity": finding.get("severity"),
                    "message": finding.get("message"),
                    "affected_ids": list(finding.get("affected_ids") or []),
                    "measurements": finding.get("measurements") or {},
                }
                for affected_id in compact["affected_ids"]:
                    if isinstance(affected_id, str) and affected_id in findings_by_province:
                        findings_by_province[affected_id].append(compact)

    dataset = ReviewDataset(
        profile_id=profile_id,
        province_input=province_path.resolve(),
        adjacency_input=None if adjacency_path is None else adjacency_path.resolve(),
        qa_report_input=None if qa_path is None else qa_path.resolve(),
        province_count=len(province_ids),
        adjacency_count=adjacency_count,
        qa_status=qa_status,
        qa_error_count=qa_error_count,
        qa_warning_count=qa_warning_count,
        gpm_meta=gpm_meta,
        adjacency_index=adjacency_index,
        qa_report=qa_report,
        findings_by_province=findings_by_province,
        land_province_ids=land_province_ids,
        politics_findings_by_province={province_id: [] for province_id in land_province_ids},
        m23_inputs={
            key: Path(value).resolve()
            for key, value in {
                "locations": location_input,
                "modern_reference": modern_reference_input,
                "lineage": lineage_input,
                "paintability": paintability_input,
                "province_aggregation": aggregation_manifest_input,
            }.items()
            if value is not None and Path(value).is_file()
        },
    )

    if scenario_id or scenario_path:
        try:
            scenario = load_scenario(
                scenario_id or "from-path",
                scenario_path=scenario_path,
            )
        except ScenarioError as error:
            raise ReviewError(str(error)) from error
        dataset.scenario_id = str(scenario["scenario_id"])
        dataset.scenario_path = Path(scenario["_path"]).resolve()
        dataset.scenario_document = scenario
        dataset.authoring_enabled = dataset.scenario_path.is_file()
        land_features = [
            feature
            for feature in features
            if isinstance(feature, dict)
            and isinstance(feature.get("properties"), dict)
            and feature["properties"].get("kind", "land") in (None, "land")
        ]
        try:
            records, _stats = resolve_ownership_records(
                scenario,
                land_features,
                allow_unknown_overrides=True,
            )
        except ScenarioError as error:
            raise ReviewError(str(error)) from error
        dataset.ownership_by_id = {row["province_id"]: row for row in records}
        if run_politics_qa:
            dataset._refresh_politics_qa()

    return dataset


@dataclass
class ReviewServerHandle:
    """Runtime handle for a started local review server."""

    result: ReviewServeResult
    httpd: ThreadingHTTPServer
    thread: threading.Thread | None = None

    def shutdown(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        if self.thread is not None and self.thread.is_alive():
            self.thread.join(timeout=2.0)


def serve_review(
    profile_id: str | None = None,
    *,
    dataset: ReviewDataset | None = None,
    province_input: Path = PROCESSED_DATA_DIR / "provinces.geojson",
    adjacency_input: Path | None = PROCESSED_DATA_DIR / "adjacency.csv",
    qa_report_input: Path | None = PROCESSED_DATA_DIR / "topology_qa.json",
    scenario_id: str | None = None,
    scenario_path: Path | None = None,
    host: str = "127.0.0.1",
    port: int = 8765,
    open_browser: bool = True,
    block: bool = True,
) -> ReviewServeResult | ReviewServerHandle:
    """Start the local interactive review server.

    When ``block`` is true (CLI default), this call serves until interrupted and
    returns a :class:`ReviewServeResult`. Tests can pass ``block=False`` to get a
    :class:`ReviewServerHandle` that can be shut down cleanly.
    """
    if dataset is None:
        if profile_id is None:
            raise ReviewError("serve_review requires profile_id or a prepared dataset.")
        dataset = prepare_review_dataset(
            profile_id,
            province_input=province_input,
            adjacency_input=adjacency_input,
            qa_report_input=qa_report_input,
            scenario_id=scenario_id,
            scenario_path=scenario_path,
        )
    elif profile_id is not None and profile_id != dataset.profile_id:
        raise ReviewError(
            f"Profile mismatch: argument {profile_id!r} != dataset {dataset.profile_id!r}."
        )
    static_root = _static_root()
    handler = partial(_ReviewRequestHandler, dataset=dataset, static_root=static_root)
    try:
        httpd = ThreadingHTTPServer((host, port), handler)
    except OSError as error:
        raise ReviewError(f"Unable to bind review server on {host}:{port}: {error}") from error

    bound_host, bound_port = httpd.server_address[:2]
    url = f"http://{bound_host}:{bound_port}/"
    result = ReviewServeResult(
        profile_id=dataset.profile_id,
        host=str(bound_host),
        port=int(bound_port),
        url=url,
        province_input=str(dataset.province_input),
        adjacency_input=None if dataset.adjacency_input is None else str(dataset.adjacency_input),
        qa_report_input=None if dataset.qa_report_input is None else str(dataset.qa_report_input),
        scenario_id=dataset.scenario_id,
        province_count=dataset.province_count,
        adjacency_count=dataset.adjacency_count,
        qa_status=dataset.qa_status,
        qa_error_count=dataset.qa_error_count,
        qa_warning_count=dataset.qa_warning_count,
        politics_qa_status=dataset.politics_qa_status,
        politics_qa_error_count=dataset.politics_qa_error_count,
        politics_qa_warning_count=dataset.politics_qa_warning_count,
    )

    if open_browser:
        threading.Timer(0.35, lambda: webbrowser.open(url)).start()

    if not block:
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        return ReviewServerHandle(result=result, httpd=httpd, thread=thread)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping review server.")
    finally:
        httpd.shutdown()
        httpd.server_close()
    return result


def _optional_existing_path(path: Path | None, *, label: str) -> Path | None:
    if path is None:
        return None
    resolved = Path(path)
    if not resolved.exists():
        return None
    if not resolved.is_file():
        raise ReviewError(f"{label} path is not a file: {resolved}")
    return resolved


def _load_adjacency_index(
    path: Path,
    province_ids: set[str],
) -> tuple[dict[str, list[dict[str, Any]]], int]:
    index: dict[str, list[dict[str, Any]]] = {province_id: [] for province_id in province_ids}
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            required = {"from_province_id", "to_province_id", "shared_border_km", "adjacency_type"}
            if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
                raise ReviewError(
                    f"Adjacency CSV is missing required columns {sorted(required)}: {path}"
                )
            row_count = 0
            for row in reader:
                left = (row.get("from_province_id") or "").strip()
                right = (row.get("to_province_id") or "").strip()
                if not left or not right:
                    continue
                edge = {
                    "neighbor_id": right,
                    "shared_border_km": _as_float(row.get("shared_border_km")),
                    "adjacency_type": row.get("adjacency_type") or "land",
                    "crossing_type": row.get("crossing_type") or "shared_border",
                    "bidirectional": (row.get("bidirectional") or "true").lower() != "false",
                }
                reverse = {
                    "neighbor_id": left,
                    "shared_border_km": edge["shared_border_km"],
                    "adjacency_type": edge["adjacency_type"],
                    "crossing_type": edge["crossing_type"],
                    "bidirectional": edge["bidirectional"],
                }
                if left in index:
                    index[left].append(edge)
                if right in index:
                    index[right].append(reverse)
                row_count += 1
    except OSError as error:
        raise ReviewError(f"Unable to read adjacency CSV: {path}: {error}") from error

    for neighbors in index.values():
        neighbors.sort(key=lambda item: (-(item["shared_border_km"] or 0.0), item["neighbor_id"]))
    return index, row_count


def _load_json_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ReviewError(f"{label} is not valid JSON: {path}: {error}") from error
    except OSError as error:
        raise ReviewError(f"Unable to read {label}: {path}: {error}") from error
    if not isinstance(payload, dict):
        raise ReviewError(f"{label} must be a JSON object: {path}")
    return payload


def _as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _static_root() -> Path:
    return Path(__file__).resolve().parent / "static"


class _ReviewRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args: Any, dataset: ReviewDataset, static_root: Path, **kwargs: Any) -> None:
        self.dataset = dataset
        self.static_root = static_root
        super().__init__(*args, **kwargs)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        # Keep CLI output focused on startup summary, not every asset request.
        return

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        if path in {"/", "/index.html"}:
            self._serve_static("index.html")
            return
        if path.startswith("/static/"):
            self._serve_static(path.removeprefix("/static/"))
            return
        if path == "/api/meta":
            self._send_json(self.dataset.meta_payload())
            return
        if path == "/api/provinces.geojson":
            self._send_file(self.dataset.province_input, content_type="application/geo+json")
            return
        if path.startswith("/api/m23/"):
            layer = path.removeprefix("/api/m23/")
            source = self.dataset.m23_inputs.get(layer)
            if source is None:
                self._send_error_json(404, f"M23 review layer not available: {layer}")
            else:
                content_type = "application/geo+json" if source.suffix.lower() in {".geojson", ".json"} else "text/csv"
                self._send_file(source, content_type=content_type)
            return
        if path == "/api/adjacency.json":
            self._send_json({"adjacency": self.dataset.adjacency_index})
            return
        if path == "/api/qa.json":
            if self.dataset.qa_report is None:
                self._send_json({"available": False, "report": None})
            else:
                self._send_json({"available": True, "report": self.dataset.qa_report})
            return
        if path == "/api/scenarios":
            summaries = [item.to_dict() for item in list_scenarios()]
            self._send_json({"scenarios": summaries, "active": self.dataset.scenario_id})
            return
        if path == "/api/ownership.json":
            if not self.dataset.scenario_id:
                self._send_json({"available": False, "scenario_id": None, "records": []})
                return
            records = sorted(self.dataset.ownership_by_id.values(), key=lambda row: row["province_id"])
            enriched = [_enrich_ownership_colors(row) for row in records]
            self._send_json(
                {
                    "available": True,
                    "scenario_id": self.dataset.scenario_id,
                    "count": len(enriched),
                    "records": enriched,
                }
            )
            return
        if path == "/api/politics-qa.json":
            if self.dataset.politics_qa_report is None:
                self._send_json({"available": False, "report": None})
            else:
                self._send_json({"available": True, "report": self.dataset.politics_qa_report})
            return
        if path == "/api/scenario":
            if not self.dataset.scenario_id or self.dataset.scenario_document is None:
                self._send_json({"available": False, "scenario": None})
                return
            document = {
                key: value
                for key, value in self.dataset.scenario_document.items()
                if key != "_path"
            }
            self._send_json(
                {
                    "available": True,
                    "scenario_id": self.dataset.scenario_id,
                    "scenario_path": str(self.dataset.scenario_path),
                    "authoring_enabled": self.dataset.authoring_enabled,
                    "scenario": document,
                }
            )
            return
        if path.startswith("/api/province/"):
            province_id = path.removeprefix("/api/province/").strip()
            if not province_id or province_id not in self.dataset.adjacency_index:
                self._send_error_json(404, f"Unknown province_id: {province_id}")
                return
            ownership = self.dataset.ownership_by_id.get(province_id)
            ownership_payload = (
                _enrich_ownership_colors(ownership) if ownership is not None else None
            )
            self._send_json(
                {
                    "province_id": province_id,
                    "adjacency": self.dataset.adjacency_index.get(province_id, []),
                    "findings": self.dataset.findings_by_province.get(province_id, []),
                    "politics_findings": self.dataset.politics_findings_by_province.get(province_id, []),
                    "ownership": ownership_payload,
                }
            )
            return
        self._send_error_json(404, f"Not found: {path}")

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        if path == "/api/scenario/override":
            self._handle_override_write(delete=False)
            return
        self._send_error_json(404, f"Not found: {path}")

    def do_DELETE(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        if path == "/api/scenario/override":
            self._handle_override_write(delete=True)
            return
        self._send_error_json(404, f"Not found: {path}")

    def _handle_override_write(self, *, delete: bool) -> None:
        if not self.dataset.authoring_enabled or not self.dataset.scenario_id:
            self._send_error_json(400, "Scenario authoring is not enabled for this review session.")
            return
        try:
            payload = self._read_json_body()
        except ReviewError as error:
            self._send_error_json(400, str(error))
            return

        province_id = payload.get("province_id")
        if not isinstance(province_id, str) or not province_id.strip():
            self._send_error_json(400, "province_id is required")
            return
        province_id = province_id.strip()
        if province_id not in self.dataset.land_province_ids:
            self._send_error_json(400, f"Unknown land province_id: {province_id}")
            return

        try:
            if delete:
                result = remove_province_override(
                    self.dataset.scenario_id,
                    province_id,
                    scenario_path=self.dataset.scenario_path,
                    write=True,
                )
            else:
                fields = {
                    key: payload[key]
                    for key in (
                        "owner",
                        "controller",
                        "cores",
                        "claims",
                        "culture",
                        "religion",
                        "disputed",
                        "notes",
                    )
                    if key in payload
                }
                result = apply_province_override(
                    self.dataset.scenario_id,
                    province_id,
                    fields,
                    scenario_path=self.dataset.scenario_path,
                    write=True,
                )
            self.dataset.reload_scenario_ownership()
        except ScenarioError as error:
            self._send_error_json(400, str(error))
            return
        except Exception as error:  # noqa: BLE001
            self._send_error_json(500, f"Failed to write override: {error}")
            return

        ownership = self.dataset.ownership_by_id.get(province_id)
        ownership_payload = (
            _enrich_ownership_colors(ownership) if ownership is not None else None
        )
        self._send_json(
            {
                "ok": True,
                "result": result.to_dict(),
                "ownership": ownership_payload,
                "politics_qa_status": self.dataset.politics_qa_status,
                "politics_qa_error_count": self.dataset.politics_qa_error_count,
                "politics_qa_warning_count": self.dataset.politics_qa_warning_count,
                "politics_findings": self.dataset.politics_findings_by_province.get(province_id, []),
            }
        )

    def _read_json_body(self) -> dict[str, Any]:
        length_header = self.headers.get("Content-Length", "0")
        try:
            length = int(length_header)
        except ValueError as error:
            raise ReviewError("Invalid Content-Length") from error
        if length < 0 or length > 1_000_000:
            raise ReviewError("Request body too large or invalid")
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ReviewError(f"Request body must be JSON: {error}") from error
        if not isinstance(payload, dict):
            raise ReviewError("Request body must be a JSON object")
        return payload

    def _serve_static(self, relative_path: str) -> None:
        # Flat static assets only; reject nested paths and traversal.
        if (
            not relative_path
            or relative_path != Path(relative_path).name
            or relative_path in {".", ".."}
        ):
            self._send_error_json(403, "Forbidden")
            return
        candidate = (self.static_root / relative_path).resolve()
        try:
            candidate.relative_to(self.static_root.resolve())
        except ValueError:
            self._send_error_json(403, "Forbidden")
            return
        if not candidate.is_file():
            self._send_error_json(404, f"Static asset not found: {relative_path}")
            return
        content_type = mimetypes.guess_type(str(candidate))[0] or "application/octet-stream"
        self._send_file(candidate, content_type=content_type)

    def _send_file(self, path: Path, *, content_type: str) -> None:
        try:
            payload = path.read_bytes()
        except OSError as error:
            self._send_error_json(500, f"Unable to read {path.name}: {error}")
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def _send_json(self, payload: dict[str, Any], *, status: int = 200) -> None:
        body = json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_error_json(self, status: int, message: str) -> None:
        self._send_json({"error": message}, status=status)
