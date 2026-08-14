#!/usr/bin/env python3
"""Verify or human-sign a frozen M25C anomaly-census packet."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gpm.qa.m25c_census import (  # noqa: E402
    acceptance_findings,
    invalid_reviewer_identity,
    overlay_acceptance,
    review_ledger_findings,
)
from gpm.qa.start_date import validate_anomaly_inventory  # noqa: E402
from gpm.schemas import (  # noqa: E402
    SchemaValidationError,
    validate_polity_gazetteer,
    validate_start_date_source_manifest,
)


DEFAULT_PACKET = ROOT / "data" / "processed" / "m25c-global-staging" / "evidence"
EXCLUDED_FROM_HASHES = {"SHA256SUMS", "review_acceptance.json"}


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"cannot load JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"JSON document must be an object: {path}")
    return value


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _hash_findings(packet: Path) -> list[str]:
    sums_path = packet / "SHA256SUMS"
    if not sums_path.is_file() or sums_path.is_symlink():
        return ["missing or symlinked SHA256SUMS"]
    records: dict[str, str] = {}
    findings: list[str] = []
    for line_number, line in enumerate(sums_path.read_text(encoding="utf-8").splitlines(), 1):
        match = re.fullmatch(r"([0-9a-f]{64})  ([^\r\n]+)", line)
        if not match:
            findings.append(f"SHA256SUMS line {line_number} is malformed")
            continue
        expected, relative_text = match.groups()
        relative = Path(relative_text)
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or relative.name in EXCLUDED_FROM_HASHES
            or relative_text in records
        ):
            findings.append(f"SHA256SUMS line {line_number} has an invalid or duplicate path")
            continue
        path = packet / relative
        try:
            path.resolve().relative_to(packet.resolve())
        except ValueError:
            findings.append(f"hashed path escapes packet: {relative_text}")
            continue
        records[relative_text] = expected
        if path.is_symlink() or not path.is_file():
            findings.append(f"hashed file is missing or symlinked: {relative_text}")
        elif _digest(path) != expected:
            findings.append(f"frozen hash mismatch: {relative_text}")
    actual = {
        path.relative_to(packet).as_posix()
        for path in packet.rglob("*")
        if path.is_file() and path.name not in EXCLUDED_FROM_HASHES
    }
    if set(records) != actual:
        missing = sorted(actual - set(records))
        stale = sorted(set(records) - actual)
        findings.append(f"hashed-file enumeration mismatch: unlisted={missing}, missing={stale}")
    return findings


def _builder_module():
    spec = importlib.util.spec_from_file_location(
        "m25c_builder_for_census_verification",
        ROOT / "scripts" / "build-m25c-global-pass.py",
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _validate_packet(packet: Path, *, state: str) -> dict[str, Any]:
    hash_findings = _hash_findings(packet)
    if hash_findings:
        raise SystemExit("frozen packet hash verification failed: " + "; ".join(hash_findings))

    source_manifest = _load(packet / "source_manifest.json")
    gazetteer = _load(packet / "gazetteer.json")
    inventory = _load(packet / "anomaly_inventory.json")
    ledger = _load(packet / "anomaly_census_review_ledger.json")
    rejected_leads = _load(packet / "rejected-leads.json")
    source_access_audit = _load(packet / "source-access-audit.json")
    try:
        validate_start_date_source_manifest(source_manifest)
        validate_polity_gazetteer(gazetteer)
    except SchemaValidationError as exc:
        raise SystemExit(f"packet schema validation failed: {exc}") from exc

    ledger_issues = review_ledger_findings(
        inventory,
        ledger,
        source_manifest,
        rejected_leads,
        source_access_audit,
    )
    if ledger_issues:
        raise SystemExit(
            "review ledger rejected:\n"
            + json.dumps(ledger_issues, indent=2, sort_keys=True)
        )

    acceptance_path = packet / "review_acceptance.json"
    if state == "pending":
        if acceptance_path.exists():
            raise SystemExit("pending verification refuses a packet with review_acceptance.json")
        effective = json.loads(json.dumps(inventory))
        effective["census"]["reviewer"] = "Pending Packet Structural Validator"
        effective["census"]["review_date"] = "2026-08-06"
        reviewer = None
        review_date = None
    else:
        if not acceptance_path.is_file() or acceptance_path.is_symlink():
            raise SystemExit("accepted verification requires a regular review_acceptance.json")
        acceptance = _load(acceptance_path)
        sidecar_findings = acceptance_findings(
            acceptance,
            frozen_sha256sums_sha256=_digest(packet / "SHA256SUMS"),
            inventory=inventory,
        )
        if sidecar_findings:
            raise SystemExit("acceptance sidecar rejected: " + "; ".join(sidecar_findings))
        effective = overlay_acceptance(inventory, acceptance)
        reviewer = acceptance["reviewer"]
        review_date = acceptance["review_date"]

    try:
        validate_anomaly_inventory(effective)
    except SchemaValidationError as exc:
        raise SystemExit(f"effective inventory rejected: {exc}") from exc

    builder = _builder_module()
    joint_findings: list[dict[str, Any]] = []
    builder._validate_anomaly_handoff(
        effective,
        {
            "source_manifest.json": source_manifest,
            "gazetteer.json": gazetteer,
            "anomaly_census_review_ledger.json": ledger,
        },
        joint_findings,
    )
    if joint_findings:
        raise SystemExit(
            "joint anomaly handoff rejected:\n"
            + json.dumps(joint_findings, indent=2, sort_keys=True)
        )

    status = _load(packet / "candidate_status.json")
    if status.get("human_review_complete") is not False or status.get("public_release_allowed") is not False:
        raise SystemExit("frozen candidate status must remain non-public and unmodified")
    return {
        "schema_version": "1.0.0",
        "report_type": "m25c_anomaly_census_packet_verification",
        "pass_id": inventory["pass_id"],
        "start_date": inventory["start_date"],
        "state": state,
        "status": "pass",
        "frozen_sha256sums_sha256": _digest(packet / "SHA256SUMS"),
        "reviewer": reviewer,
        "review_date": review_date,
        "reviewed_scope_counts": {
            "regions": len(inventory["census"]["region_ids"]),
            "classes": len(inventory["census"]["types"]),
            "cells": len(inventory["census"]["cells"]),
            "anomalies": len(inventory["anomalies"]),
        },
        "joint_findings": [],
        "human_review_complete": state == "accepted",
        "public_release_allowed": False,
    }


def _sign(packet: Path, *, reviewer: str, review_date: str) -> dict[str, Any]:
    sidecar_path = packet / "review_acceptance.json"
    if sidecar_path.exists():
        raise SystemExit("refusing duplicate signature: review_acceptance.json already exists")
    pending_report = _validate_packet(packet, state="pending")
    inventory = _load(packet / "anomaly_inventory.json")
    if invalid_reviewer_identity(reviewer, inventory["census"]["researcher"]):
        raise SystemExit("reviewer must be a distinct named human, not a placeholder or generator")
    try:
        date.fromisoformat(review_date)
    except ValueError as exc:
        raise SystemExit("--review-date must be a valid YYYY-MM-DD date") from exc
    acceptance = {
        "schema_version": "1.0.0",
        "document_type": "m25c_anomaly_census_review_acceptance",
        "pass_id": inventory["pass_id"],
        "start_date": inventory["start_date"],
        "reviewer": reviewer.strip(),
        "review_date": review_date,
        "decision": "accepted",
        "frozen_sha256sums_sha256": pending_report["frozen_sha256sums_sha256"],
        "reviewed_scope_counts": pending_report["reviewed_scope_counts"],
    }
    try:
        with sidecar_path.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(acceptance, indent=2, sort_keys=True) + "\n")
    except FileExistsError as exc:
        raise SystemExit("refusing duplicate signature: review_acceptance.json already exists") from exc
    return {
        "status": "signed",
        "sidecar": str(sidecar_path),
        "reviewer": acceptance["reviewer"],
        "review_date": acceptance["review_date"],
        "frozen_sha256sums_sha256": acceptance["frozen_sha256sums_sha256"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet-dir", type=Path, default=DEFAULT_PACKET)
    subparsers = parser.add_subparsers(dest="command", required=True)
    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--state", choices=("pending", "accepted"), required=True)
    sign_parser = subparsers.add_parser("sign")
    sign_parser.add_argument("--reviewer", required=True)
    sign_parser.add_argument("--review-date", required=True)
    args = parser.parse_args()
    packet = args.packet_dir.resolve()
    report = (
        _validate_packet(packet, state=args.state)
        if args.command == "verify"
        else _sign(packet, reviewer=args.reviewer, review_date=args.review_date)
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
