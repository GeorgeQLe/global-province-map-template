#!/usr/bin/env python3
"""Render a deterministic frozen M25C anomaly packet from tracked research."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gpm.qa.m25c_census import review_ledger_findings  # noqa: E402
DEFAULT_RESEARCH = ROOT / "research" / "start-dates" / "1444-global-v1" / "census-research.json"
DEFAULT_OUTPUT = ROOT / "data" / "processed" / "m25c-global-staging" / "evidence"
EXCLUDED_FROM_HASHES = {"SHA256SUMS", "review_acceptance.json"}
SOURCE_MANIFEST_FIELDS = {
    "source_id",
    "citation",
    "url",
    "access_date",
    "version",
    "license",
    "checksum",
    "transformations",
    "review_status",
    "source_type",
    "valid_from",
    "valid_to",
    "independence_group",
    "derived_artifacts",
}


def _load(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"cannot load tracked census research {path}: {exc}") from exc
    if not isinstance(document, dict):
        raise SystemExit("tracked census research must be a JSON object")
    return document


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _validate_research(research: dict[str, Any]) -> None:
    required = {
        "schema_version",
        "document_type",
        "pass_id",
        "start_date",
        "researcher",
        "access_date",
        "rejected_baseline",
        "regions",
        "classes",
        "sources",
        "anomalies",
        "polities",
        "reviews",
        "conflicts",
        "cross_regional_cases",
        "rejected_leads",
    }
    if (
        set(research) != required
        or research.get("schema_version") != "1.0.0"
        or research.get("document_type") != "m25c_anomaly_census_research"
        or research.get("pass_id") != "official-1444-global-v1"
        or research.get("start_date") != "1444-11-11"
    ):
        raise SystemExit("tracked census research has invalid fields or identity")
    regions = research["regions"]
    classes = research["classes"]
    reviews = research["reviews"]
    if not isinstance(regions, dict) or len(regions) != 22:
        raise SystemExit("tracked census research must define exactly 22 regions")
    if not isinstance(classes, dict) or len(classes) != 11:
        raise SystemExit("tracked census research must define exactly 11 classes")
    if not isinstance(reviews, list) or len(reviews) != 242:
        raise SystemExit("tracked census research must contain exactly 242 reviews")
    expected = {
        (region_id, anomaly_type)
        for region_id in regions
        for anomaly_type in classes
    }
    actual = {
        (row.get("region_id"), row.get("anomaly_type"))
        for row in reviews
        if isinstance(row, dict)
    }
    if actual != expected or len(actual) != len(reviews):
        raise SystemExit("tracked census reviews must exactly cover the 22 × 11 matrix")
    negative_cells = {
        (row.get("region_id"), row.get("anomaly_type"))
        for row in reviews
        if isinstance(row, dict) and row.get("status") == "reviewed_none_found"
    }
    rejected_leads = research["rejected_leads"]
    if not isinstance(rejected_leads, list):
        raise SystemExit("tracked rejected leads must be an array")
    rejected_cells = {
        (row.get("region_id"), row.get("anomaly_type"))
        for row in rejected_leads
        if isinstance(row, dict)
    }
    if (
        len(rejected_cells) != len(rejected_leads)
        or rejected_cells != negative_cells
    ):
        raise SystemExit(
            "tracked rejected leads must exactly match reviewed-none-found cells"
        )
    source_ids = {
        row.get("source_id")
        for row in research["sources"]
        if isinstance(row, dict)
    }
    if len(source_ids) != len(research["sources"]) or None in source_ids:
        raise SystemExit("tracked census source IDs must be unique and nonempty")
    for review in reviews:
        identity = review["review_id"]
        references = set(review.get("supporting_source_ids") or [])
        references.update(review.get("regional_survey_source_ids") or [])
        if references - source_ids:
            raise SystemExit(
                f"tracked review {identity} references unknown sources: "
                f"{sorted(references - source_ids)}"
            )
    for anomaly in research["anomalies"]:
        if not isinstance(anomaly.get("canonical_model"), dict) or not anomaly["canonical_model"]:
            raise SystemExit(
                f"tracked anomaly {anomaly.get('anomaly_id')} requires a canonical_model"
            )
        groups = {
            next(row for row in research["sources"] if row["source_id"] == source_id)["independence_group"]
            for source_id in anomaly.get("source_ids") or []
        }
        if len(groups) < 2:
            raise SystemExit(
                f"tracked anomaly {anomaly.get('anomaly_id')} requires two independent provenance groups"
            )


def _validate_source_access_audit(research: dict[str, Any], audit: dict[str, Any]) -> None:
    if (
        set(audit) != {"schema_version", "document_type", "pass_id", "checked_on", "records"}
        or audit.get("schema_version") != "1.0.0"
        or audit.get("document_type") != "m25c_source_access_audit"
        or audit.get("pass_id") != research.get("pass_id")
    ):
        raise SystemExit("tracked source-access audit has invalid fields or identity")
    expected = {row["source_id"]: row["url"] for row in research["sources"]}
    rows = audit.get("records")
    actual = {
        row.get("source_id"): row.get("url")
        for row in rows if isinstance(row, dict)
    } if isinstance(rows, list) else {}
    if len(actual) != len(rows or []) or actual != expected:
        raise SystemExit("tracked source-access audit must exactly cover census sources and URLs")
    for row in rows:
        if (
            set(row) != {"source_id", "url", "checked_on", "method", "result", "http_status", "notes"}
            or row["result"] != "reachable"
            or row["method"] not in {"automated_get", "browser_open", "browser_search"}
            or row["checked_on"] != audit["checked_on"]
        ):
            raise SystemExit(f"source-access audit is unresolved or invalid for {row.get('source_id')}")


def _build_inventory(research: dict[str, Any]) -> dict[str, Any]:
    anomalies = [
        {
            key: row[key]
            for key in (
                "anomaly_id",
                "type",
                "region_ids",
                "subject_ids",
                "source_ids",
                "resolution",
            )
        }
        for row in research["anomalies"]
    ]
    cells = [
        {
            "region_id": row["region_id"],
            "type": row["anomaly_type"],
            "status": row["status"],
            "anomaly_ids": sorted(row["anomaly_ids"]),
            "source_ids": sorted(row["supporting_source_ids"]),
            "notes": row["conclusion"],
        }
        for row in research["reviews"]
    ]
    return {
        "schema_version": "0.3.0",
        "document_type": "historical_anomaly_inventory",
        "artifact_version": "1.0.0",
        "pass_id": research["pass_id"],
        "start_date": research["start_date"],
        "anomalies": sorted(anomalies, key=lambda row: row["anomaly_id"]),
        "census": {
            "region_ids": sorted(research["regions"]),
            "types": sorted(research["classes"]),
            "researcher": research["researcher"],
            "reviewer": None,
            "review_date": None,
            "cells": sorted(cells, key=lambda row: (row["region_id"], row["type"])),
        },
    }


def _build_source_manifest(research: dict[str, Any]) -> dict[str, Any]:
    sources = [
        {key: row[key] for key in SOURCE_MANIFEST_FIELDS}
        for row in research["sources"]
    ]
    return {
        "schema_version": "0.3.0",
        "document_type": "start_date_source_manifest",
        "artifact_version": "1.0.0",
        "pass_id": research["pass_id"],
        "start_date": research["start_date"],
        "sources": sorted(sources, key=lambda row: row["source_id"]),
        "conflict_resolution_notes": [
            row["resolution"] for row in research["conflicts"]
        ],
    }


def _build_gazetteer(research: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "0.3.0",
        "document_type": "polity_gazetteer",
        "artifact_version": "1.0.0",
        "pass_id": research["pass_id"],
        "start_date": research["start_date"],
        "polities": [
            {
                "polity_id": row["polity_id"],
                "name": row["canonical_name"],
                "aliases": row["aliases"],
                "valid_from": row["valid_from"],
                "valid_to": row["valid_to"],
                "capital_location_ids": [],
                "relationships": row.get("relationships", []),
                "source_ids": row["source_ids"],
            }
            for row in sorted(research["polities"], key=lambda row: row["polity_id"])
        ],
    }


def _methodology(research: dict[str, Any]) -> str:
    definitions = "\n".join(
        f"- `{key}` — {row['definition']}"
        for key, row in sorted(research["classes"].items())
    )
    return f"""# M25C worldwide anomaly census methodology

Research identity: **{research["researcher"]}**
Start-date instant: **{research["start_date"]}**
Pass: **{research["pass_id"]}**

## Acceptance rule

A positive anomaly requires date-valid support for the fixed semantic from reviewed evidence with at least two independent provenance groups. A negative record is a bounded conclusion from an exact regional survey locator plus a class-specific query and disposition log; it is not a claim that the literature is exhausted.

## Fixed class definitions

{definitions}

## Review contract

The tracked research crosses 22 non-Antarctic UN M49 regions with eleven classes. `anomaly_census_review_ledger.json` preserves one record per cell, exact locators, queries, considered leads, dispositions, rationale, supporting source IDs, and the 1444-11-11 conclusion. Human acceptance is stored only in `review_acceptance.json`; it never changes this packet's frozen research bytes.
"""


def _dossier(research: dict[str, Any]) -> str:
    return f"""# Worldwide 1444 anomaly census dossier

## Scope

This frozen packet contains the 242-cell M25C anomaly census for {research["start_date"]}. It does not certify or promote the wider M25C pass.

## Research questions

For each M49 region and anomaly class, the review asks whether a date-valid polity or territory meets the fixed semantic and whether the recorded evidence supports acceptance or a bounded negative conclusion.

## Citations

`source_manifest.json` identifies reviewed sources. `anomaly_census_review_ledger.json` supplies exact URLs and locators for every regional survey and the class-specific audit trail. `anomaly_evidence_reviews.json` preserves the positive-case locator review.

## Transformations and conflicts

The generator performs deterministic projection and sorting only. Research conclusions, canonical models, conflicts, cross-regional links, and rejected leads come from tracked `census-research.json`. Ceuta is rendered as a Portuguese detached possession; the unperformed 1437 restitution promise is retained as a diplomatic event and does not establish an active geographic dispute on 1444-11-11. The Lancastrian title claim is retained as a gazetteer relationship rather than a positive geographic anomaly.

## Exclusions

The packet contains no geometry, fabric assignment, canonical status, runtime data, assembled-pass acceptance, certification, or release artifact.

## Uncertainty

Negative cells are bounded review findings, not proof that historical literature is exhausted. Remote sources are URL-pinned and live-status audited but are not content-checksummed.

## Review state

Researcher: **{research["researcher"]}**. No reviewer or review date is embedded in the frozen inventory. `human_review_complete` and `public_release_allowed` remain false until a valid sidecar is created by a distinct human.
"""


def _write_hashes(output: Path) -> None:
    files = sorted(
        path
        for path in output.rglob("*")
        if path.is_file() and path.name not in EXCLUDED_FROM_HASHES
    )
    (output / "SHA256SUMS").write_text(
        "".join(
            f"{_sha256(path)}  {path.relative_to(output).as_posix()}\n"
            for path in files
        ),
        encoding="utf-8",
    )


def generate(
    research_path: Path,
    output: Path,
    source_access_audit_path: Path | None = None,
) -> None:
    research = _load(research_path)
    _validate_research(research)
    audit_path = source_access_audit_path or research_path.with_name("source-access-audit.json")
    source_access_audit = _load(audit_path)
    _validate_source_access_audit(research, source_access_audit)
    if (output / "review_acceptance.json").exists():
        raise SystemExit("refusing to regenerate a packet with an acceptance sidecar")

    inventory = _build_inventory(research)
    source_manifest = _build_source_manifest(research)
    ledger = {
        "schema_version": "1.0.0",
        "document_type": "m25c_anomaly_census_review_ledger",
        "pass_id": research["pass_id"],
        "start_date": research["start_date"],
        "records": sorted(
            research["reviews"],
            key=lambda row: (row["region_id"], row["anomaly_type"]),
        ),
    }
    ledger_findings = review_ledger_findings(
        inventory,
        ledger,
        source_manifest,
        {
            "pass_id": research["pass_id"],
            "start_date": research["start_date"],
            "records": research["rejected_leads"],
        },
        source_access_audit,
    )
    if ledger_findings:
        raise SystemExit(
            "tracked census research is not closable:\n"
            + json.dumps(ledger_findings, indent=2, sort_keys=True)
        )
    output.mkdir(parents=True, exist_ok=True)
    _write_json(output / "anomaly_inventory.json", inventory)
    _write_json(output / "anomaly_census_review_ledger.json", ledger)
    _write_json(output / "source_manifest.json", source_manifest)
    _write_json(output / "source-access-audit.json", source_access_audit)
    _write_json(output / "gazetteer.json", _build_gazetteer(research))
    _write_json(
        output / "anomaly_evidence_reviews.json",
        {
            "pass_id": research["pass_id"],
            "start_date": research["start_date"],
            "anomalies": [
                {
                    "anomaly_id": row["anomaly_id"],
                    "evidence_reviews": row["evidence_reviews"],
                    "canonical_model": row["canonical_model"],
                }
                for row in research["anomalies"]
            ],
        },
    )
    _write_json(
        output / "conflicts.json",
        {
            "pass_id": research["pass_id"],
            "start_date": research["start_date"],
            "records": research["conflicts"],
        },
    )
    _write_json(
        output / "cross-regional-cases.json",
        {
            "pass_id": research["pass_id"],
            "start_date": research["start_date"],
            "records": research["cross_regional_cases"],
        },
    )
    _write_json(
        output / "rejected-leads.json",
        {
            "pass_id": research["pass_id"],
            "start_date": research["start_date"],
            "records": research["rejected_leads"],
        },
    )
    _write_json(
        output / "candidate_status.json",
        {
            "pass_id": research["pass_id"],
            "start_date": research["start_date"],
            "status": "research_complete_pending_independent_human_review",
            "researcher": research["researcher"],
            "reviewer": None,
            "review_date": None,
            "human_review_complete": False,
            "public_release_allowed": False,
            "pending": [
                "independent human anomaly-census review",
                "fabric",
                "worldwide evidence",
                "assembly",
                "runtime certification",
                "release",
            ],
        },
    )
    (output / "methodology.md").write_text(_methodology(research), encoding="utf-8")
    (output / "dossier.md").write_text(_dossier(research), encoding="utf-8")
    (output / "REVIEW.md").write_text(
        """# Independent anomaly-census review

Inspect all positive anomaly evidence reviews and all 242 ledger records. Record requested changes outside the packet. If research changes are required, edit tracked `census-research.json`, discard this packet, and regenerate it. Do not patch frozen output.

Acceptance uses `verify-m25c-anomaly-census.py sign --reviewer "<human name>" --review-date YYYY-MM-DD`. Signing creates only `review_acceptance.json`; assembled-pass `accept-review` remains a separate later gate.
""",
        encoding="utf-8",
    )
    (output / "INDEX.md").write_text(
        """# Frozen M25C anomaly-census packet

- `anomaly_inventory.json` — schema-0.3 inventory with 242 frozen cells
- `anomaly_census_review_ledger.json` — region/class evidence and disposition log
- `source_manifest.json` — reviewed source metadata
- `source-access-audit.json` — live automated/browser access dispositions
- `gazetteer.json` — anomaly subject records
- `anomaly_evidence_reviews.json` — positive-case exact-locator reviews
- `conflicts.json` — classification and evidence conflicts
- `cross-regional-cases.json` — stable cross-region anomaly links
- `rejected-leads.json` — negative-cell lead dispositions
- `candidate_status.json` — non-public pending state
- `SHA256SUMS` — frozen hashes; excludes only itself and `review_acceptance.json`
- `REVIEW.md` — human review and signing protocol
""",
        encoding="utf-8",
    )
    _write_hashes(output)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--research-input", type=Path, default=DEFAULT_RESEARCH)
    parser.add_argument("--source-access-audit", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    generate(
        args.research_input.resolve(),
        args.output_dir.resolve(),
        args.source_access_audit.resolve() if args.source_access_audit else None,
    )


if __name__ == "__main__":
    main()
