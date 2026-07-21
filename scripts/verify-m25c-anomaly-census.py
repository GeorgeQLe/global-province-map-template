#!/usr/bin/env python3
"""Verify and re-hash the ignored M25C pre-review anomaly packet."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
from argparse import Namespace
from pathlib import Path

from gpm.qa.start_date import validate_anomaly_inventory
from gpm.schemas import SchemaValidationError, validate_polity_gazetteer, validate_start_date_source_manifest


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "intermediate" / "m25c-anomaly-census"
EVIDENCE = ROOT / "data" / "processed" / "m25c-global-staging" / "evidence"


def load(name: str) -> dict:
    return json.loads((EVIDENCE / name).read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    sources, gazetteer, inventory = load("source_manifest.json"), load("gazetteer.json"), load("anomaly_inventory.json")
    validate_start_date_source_manifest(sources)
    validate_polity_gazetteer(gazetteer)
    candidate_findings: list[str] = []
    try:
        validate_anomaly_inventory(inventory)
    except SchemaValidationError as exc:
        candidate_findings.append(str(exc))
    expected = ["anomaly inventory.census.review_date must be an ISO date"]
    if candidate_findings != expected:
        raise SystemExit(f"unexpected persisted-candidate findings: {candidate_findings}")

    structural = json.loads(json.dumps(inventory))
    structural["census"]["reviewer"] = "Structural Review Sentinel (not persisted)"
    structural["census"]["review_date"] = "2026-07-21"
    validate_anomaly_inventory(structural)
    spec = importlib.util.spec_from_file_location("m25c_builder", ROOT / "scripts" / "build-m25c-global-pass.py")
    assert spec and spec.loader
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    joint_findings: list[dict] = []
    builder._validate_anomaly_handoff(structural, {"source_manifest.json": sources, "gazetteer.json": gazetteer}, joint_findings)
    if joint_findings:
        raise SystemExit(json.dumps(joint_findings, indent=2))

    with tempfile.TemporaryDirectory() as temporary:
        temporary_root = Path(temporary)
        first_input = temporary_root / "first.json"
        second_input = temporary_root / "second.json"
        first_input.write_text(json.dumps(structural), encoding="utf-8")
        reordered = json.loads(json.dumps(structural))
        for field in ("anomalies",):
            reordered[field].reverse()
        for field in ("cells", "region_ids", "types"):
            reordered["census"][field].reverse()
        second_input.write_text(json.dumps(reordered), encoding="utf-8")
        builder.stage_inventory(Namespace(output_dir=temporary_root / "one", inventory_input=first_input))
        builder.stage_inventory(Namespace(output_dir=temporary_root / "two", inventory_input=second_input))
        first = (temporary_root / "one" / "anomaly_inventory.json").read_bytes()
        second = (temporary_root / "two" / "anomaly_inventory.json").read_bytes()
        if first != second:
            raise SystemExit("canonical inventory builds are not byte-identical")
        canonical_hash = hashlib.sha256(first).hexdigest()

    report = {
        "schema_version": "0.1.0", "report_type": "m25c_anomaly_pre_review_audit",
        "pass_id": "official-1444-global-v1", "start_date": "1444-11-11",
        "source_manifest_schema": "pass", "gazetteer_schema": "pass",
        "structural_inventory_schema": "pass", "joint_findings": [],
        "candidate_expected_findings": candidate_findings,
        "canonical_builds_byte_identical": True, "canonical_inventory_sha256": canonical_hash,
        "human_review_complete": False, "public_release_allowed": False,
    }
    (EVIDENCE / "pre-review-audit.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    files = sorted(
        [path for path in EVIDENCE.rglob("*") if path.is_file() and path.name != "SHA256SUMS"]
        + [path for path in LEDGER.rglob("*") if path.is_file()]
    )
    (EVIDENCE / "SHA256SUMS").write_text(
        "".join(f"{digest(path)}  {path.relative_to(ROOT).as_posix()}\n" for path in files), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
