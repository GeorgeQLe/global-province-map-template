"""Fail-closed M25C anomaly review-ledger and acceptance-sidecar contracts."""

from __future__ import annotations

import copy
import re
from datetime import date
from typing import Any

from gpm.schemas import WORLDWIDE_M49_SUBREGIONS


COMMON_ATLAS_SOURCE_ID = "shepherd-historical-atlas"
EXPECTED_CELL_COUNT = 242
EXPECTED_CLASS_COUNT = 11
ALLOWED_SURVEY_SOURCE_TYPES = {"academic", "archival", "institutional", "primary"}
ALLOWED_FAILURE_BASES = {
    "control",
    "date",
    "geography",
    "insufficient_evidence",
    "institutional_status",
    "sovereignty",
}
GENERIC_NEGATIVE_PHRASES = {
    "no qualifying case was established in the bounded regional and class-specific review",
    "ordinary realms, internal divisions, later developments, and semantic mismatches were excluded",
}
CLASS_SEARCH_TERMS = {
    "claim": {"dynastic claim", "formal title", "claimed sovereignty"},
    "composite-realm": {"composite monarchy", "personal union", "separate laws"},
    "concession": {"concession", "foreign quarter", "commercial colony", "extraterritorial"},
    "condominium": {"condominium", "co-sovereignty", "shared suzerainty"},
    "dependency": {"dependency", "tributary possession", "subordinate possession", "captaincy"},
    "detached-territory": {"detached possession", "overseas possession", "noncontiguous territory"},
    "disputed-area": {"disputed sovereignty", "contested possession", "promised restitution"},
    "enclave-exclave": {"enclave", "exclave", "surrounded territory"},
    "free-protected-city": {"free city", "protected city", "imperial immediacy", "autonomous city"},
    "microstate": {"small sovereign polity", "city-state", "miniature polity"},
    "non-state-territory": {"monastic territory", "tribal administration", "organized non-state polity"},
}
ACCEPTANCE_FIELDS = {
    "schema_version",
    "document_type",
    "pass_id",
    "start_date",
    "reviewer",
    "review_date",
    "decision",
    "frozen_sha256sums_sha256",
    "reviewed_scope_counts",
}


def _finding(
    findings: list[dict[str, Any]],
    code: str,
    *,
    region_id: str = "",
    anomaly_type: str = "",
    source_id: str = "",
    message: str,
) -> None:
    affected = [value for value in (region_id, anomaly_type, source_id) if value]
    findings.append(
        {
            "code": code,
            "region_id": region_id,
            "anomaly_type": anomaly_type,
            "source_id": source_id,
            "affected_ids": affected,
            "message": message,
        }
    )


def _date_bound(value: Any, *, upper: bool) -> date | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("date bound is not a string")
    if re.fullmatch(r"\d{4}", value):
        return date(int(value), 12 if upper else 1, 31 if upper else 1)
    if re.fullmatch(r"\d{4}-\d{2}", value):
        year, month = (int(part) for part in value.split("-"))
        if upper:
            from calendar import monthrange

            return date(year, month, monthrange(year, month)[1])
        return date(year, month, 1)
    return date.fromisoformat(value)


def _covers(source: dict[str, Any], target: str) -> bool:
    try:
        target_date = date.fromisoformat(target)
        lower = _date_bound(source.get("valid_from"), upper=False)
        upper = _date_bound(source.get("valid_to"), upper=True)
    except (TypeError, ValueError):
        return False
    return (lower is None or lower <= target_date) and (upper is None or target_date <= upper)


def review_ledger_findings(
    inventory: dict[str, Any],
    ledger: dict[str, Any],
    source_manifest: dict[str, Any],
    rejected_leads: dict[str, Any] | None = None,
    source_access_audit: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Return actionable region/class/source findings for one frozen census."""
    findings: list[dict[str, Any]] = []
    expected_identity = (inventory.get("pass_id"), inventory.get("start_date"))
    if (
        ledger.get("schema_version") != "1.0.0"
        or ledger.get("document_type") != "m25c_anomaly_census_review_ledger"
        or (ledger.get("pass_id"), ledger.get("start_date")) != expected_identity
    ):
        _finding(
            findings,
            "INVALID_REVIEW_LEDGER_IDENTITY",
            message="Review ledger schema, document type, pass, or start-date identity is invalid.",
        )
        return findings

    records = ledger.get("records")
    if not isinstance(records, list) or len(records) != EXPECTED_CELL_COUNT:
        _finding(
            findings,
            "INCOMPLETE_REVIEW_LEDGER",
            message=f"Review ledger must contain exactly {EXPECTED_CELL_COUNT} records.",
        )
        records = records if isinstance(records, list) else []

    source_rows = source_manifest.get("sources")
    source_rows = source_rows if isinstance(source_rows, list) else []
    sources = {
        row.get("source_id"): row
        for row in source_rows
        if isinstance(row, dict) and isinstance(row.get("source_id"), str)
    }
    atlas = sources.get(COMMON_ATLAS_SOURCE_ID, {})
    atlas_group = atlas.get("independence_group")
    inventory_cells = {
        (row.get("region_id"), row.get("type")): row
        for row in (inventory.get("census") or {}).get("cells", [])
        if isinstance(row, dict)
    }
    ledger_index: dict[tuple[Any, Any], dict[str, Any]] = {}
    region_survey_ids: dict[str, set[str]] = {}
    regional_locator_owner: dict[tuple[str, str], str] = {}
    negative_cells: set[tuple[str, str]] = set()

    required = {
        "review_id",
        "region_id",
        "anomaly_type",
        "regional_survey_source_ids",
        "source_locators",
        "queries",
        "considered_leads",
        "rationale",
        "supporting_source_ids",
        "anomaly_ids",
        "conclusion",
        "status",
    }
    for record in records:
        if not isinstance(record, dict):
            _finding(findings, "INVALID_REVIEW_LEDGER_RECORD", message="Review ledger record is not an object.")
            continue
        region_id = str(record.get("region_id") or "")
        anomaly_type = str(record.get("anomaly_type") or "")
        identity = (region_id, anomaly_type)
        if set(record) != required:
            _finding(
                findings,
                "INVALID_REVIEW_LEDGER_RECORD",
                region_id=region_id,
                anomaly_type=anomaly_type,
                message="Review ledger record has missing or unexpected fields.",
            )
            continue
        if record["review_id"] != f"{region_id}/{anomaly_type}":
            _finding(
                findings,
                "REVIEW_LEDGER_ID_MISMATCH",
                region_id=region_id,
                anomaly_type=anomaly_type,
                message="review_id must equal {region_id}/{anomaly_type}.",
            )
        if identity in ledger_index:
            _finding(
                findings,
                "DUPLICATE_REVIEW_LEDGER_CELL",
                region_id=region_id,
                anomaly_type=anomaly_type,
                message="Review ledger contains a duplicate region/class cell.",
            )
        ledger_index[identity] = record

        cell = inventory_cells.get(identity)
        if cell is None:
            _finding(
                findings,
                "REVIEW_LEDGER_CELL_MISMATCH",
                region_id=region_id,
                anomaly_type=anomaly_type,
                message="Review ledger region/class has no matching inventory cell.",
            )
        else:
            for ledger_field, cell_field in (
                ("status", "status"),
                ("anomaly_ids", "anomaly_ids"),
                ("supporting_source_ids", "source_ids"),
            ):
                left = record.get(ledger_field)
                right = cell.get(cell_field)
                normalized_left = sorted(left) if isinstance(left, list) else left
                normalized_right = sorted(right) if isinstance(right, list) else right
                if normalized_left != normalized_right:
                    _finding(
                        findings,
                        "REVIEW_LEDGER_CELL_MISMATCH",
                        region_id=region_id,
                        anomaly_type=anomaly_type,
                        message=f"Ledger {ledger_field} disagrees with inventory {cell_field}.",
                    )

        for field, code in (
            ("queries", "MISSING_CLASS_QUERY"),
            ("considered_leads", "MISSING_LEAD_DISPOSITION"),
            ("rationale", "MISSING_REVIEW_RATIONALE"),
            ("conclusion", "MISSING_REVIEW_CONCLUSION"),
        ):
            value = record.get(field)
            if (
                (field in {"queries", "considered_leads"} and (not isinstance(value, list) or not value))
                or (field in {"rationale", "conclusion"} and (not isinstance(value, str) or not value.strip()))
            ):
                _finding(
                    findings,
                    code,
                    region_id=region_id,
                    anomaly_type=anomaly_type,
                    message=f"Review record requires a nonempty {field}.",
                )
        queries = record.get("queries")
        if isinstance(queries, list) and any(not isinstance(item, str) or not item.strip() for item in queries):
            _finding(
                findings,
                "MISSING_CLASS_QUERY",
                region_id=region_id,
                anomaly_type=anomaly_type,
                message="Every class-specific query must be a nonempty string.",
            )
        if isinstance(queries, list) and queries:
            query_text = " ".join(item for item in queries if isinstance(item, str)).casefold()
            terms = CLASS_SEARCH_TERMS.get(anomaly_type, set())
            if not ({"1444", "fifteenth century"} & {token for token in ("1444", "fifteenth century") if token in query_text}) or not any(term in query_text for term in terms):
                _finding(
                    findings,
                    "GENERIC_OR_TEMPORALLY_UNBOUNDED_QUERY",
                    region_id=region_id,
                    anomaly_type=anomaly_type,
                    message="Search log must include the start-date/period and a class-specific historical synonym.",
                )

        survey_ids = record.get("regional_survey_source_ids")
        if not isinstance(survey_ids, list) or not survey_ids:
            _finding(
                findings,
                "MISSING_REGIONAL_SURVEY",
                region_id=region_id,
                anomaly_type=anomaly_type,
                message="Review record requires at least one regional survey source.",
            )
            survey_ids = []
        region_survey_ids.setdefault(region_id, set()).update(
            source_id for source_id in survey_ids if isinstance(source_id, str)
        )

        locator_rows = record.get("source_locators")
        locator_rows = locator_rows if isinstance(locator_rows, list) else []
        locators = {
            row.get("source_id"): row
            for row in locator_rows
            if isinstance(row, dict) and set(row) == {"source_id", "url", "locator"}
        }
        for source_id in survey_ids:
            source = sources.get(source_id)
            if source is None:
                _finding(
                    findings,
                    "UNKNOWN_REVIEW_SOURCE",
                    region_id=region_id,
                    anomaly_type=anomaly_type,
                    source_id=str(source_id),
                    message="Regional survey source is absent from source_manifest.json.",
                )
                continue
            if source.get("review_status") != "reviewed":
                _finding(
                    findings,
                    "UNREVIEWED_REVIEW_SOURCE",
                    region_id=region_id,
                    anomaly_type=anomaly_type,
                    source_id=str(source_id),
                    message="Regional survey source is not reviewed.",
                )
            if source.get("source_type") not in ALLOWED_SURVEY_SOURCE_TYPES:
                _finding(
                    findings,
                    "INVALID_REGIONAL_SURVEY_TYPE",
                    region_id=region_id,
                    anomaly_type=anomaly_type,
                    source_id=str(source_id),
                    message="Regional survey must be academic, primary, archival, or institutional.",
                )
            if source.get("independence_group") == atlas_group:
                _finding(
                    findings,
                    "REGIONAL_SURVEY_NOT_INDEPENDENT",
                    region_id=region_id,
                    anomaly_type=anomaly_type,
                    source_id=str(source_id),
                    message="Regional survey must be independent of the common atlas.",
                )
            if not _covers(source, str(inventory.get("start_date") or "")):
                _finding(
                    findings,
                    "REGIONAL_SURVEY_DATE_GAP",
                    region_id=region_id,
                    anomaly_type=anomaly_type,
                    source_id=str(source_id),
                    message="Regional survey temporal range does not cover 1444-11-11.",
                )
            locator = locators.get(source_id)
            if (
                locator is None
                or locator.get("url") != source.get("url")
                or not isinstance(locator.get("locator"), str)
                or not locator["locator"].strip()
            ):
                _finding(
                    findings,
                    "MISSING_OR_MISMATCHED_SOURCE_LOCATOR",
                    region_id=region_id,
                    anomaly_type=anomaly_type,
                    source_id=str(source_id),
                    message="Regional survey requires the manifest URL and a precise nonempty locator.",
                )
                continue
            pair = (str(locator["url"]), locator["locator"].strip())
            owner = regional_locator_owner.setdefault(pair, region_id)
            if owner != region_id:
                _finding(
                    findings,
                    "DUPLICATED_GENERIC_REGIONAL_SURVEY",
                    region_id=region_id,
                    anomaly_type=anomaly_type,
                    source_id=str(source_id),
                    message=f"Regional URL/locator duplicates the coverage claimed for region {owner}.",
                )

        supporting = record.get("supporting_source_ids")
        supporting = supporting if isinstance(supporting, list) else []
        for source_id in supporting:
            source = sources.get(source_id)
            if source is None:
                _finding(
                    findings,
                    "UNKNOWN_REVIEW_SOURCE",
                    region_id=region_id,
                    anomaly_type=anomaly_type,
                    source_id=str(source_id),
                    message="Supporting source is absent from source_manifest.json.",
                )
            elif source.get("review_status") != "reviewed":
                _finding(
                    findings,
                    "UNREVIEWED_REVIEW_SOURCE",
                    region_id=region_id,
                    anomaly_type=anomaly_type,
                    source_id=str(source_id),
                    message="Supporting source is not reviewed.",
                )
            else:
                if not _covers(source, str(inventory.get("start_date") or "")):
                    _finding(
                        findings,
                        "REVIEW_SOURCE_DATE_GAP",
                        region_id=region_id,
                        anomaly_type=anomaly_type,
                        source_id=str(source_id),
                        message="Supporting source temporal range does not cover 1444-11-11.",
                    )
                locator = locators.get(source_id)
                if (
                    locator is None
                    or locator.get("url") != source.get("url")
                    or not isinstance(locator.get("locator"), str)
                    or not locator["locator"].strip()
                ):
                    _finding(
                        findings,
                        "MISSING_OR_MISMATCHED_SOURCE_LOCATOR",
                        region_id=region_id,
                        anomaly_type=anomaly_type,
                        source_id=str(source_id),
                        message="Every supporting source requires the manifest URL and a precise locator.",
                    )

        accepted_lead = False
        leads = record.get("considered_leads")
        for lead in leads if isinstance(leads, list) else []:
            if (
                not isinstance(lead, dict)
                or set(lead) != {
                    "lead", "disposition", "failure_basis", "rationale", "supporting_source_ids",
                }
                or not isinstance(lead.get("lead"), str)
                or not lead["lead"].strip()
                or lead.get("disposition") not in {"accepted", "rejected"}
                or not isinstance(lead.get("failure_basis"), list)
                or any(item not in ALLOWED_FAILURE_BASES for item in lead.get("failure_basis", []))
                or (lead.get("disposition") == "rejected" and not lead.get("failure_basis"))
                or (lead.get("disposition") == "accepted" and bool(lead.get("failure_basis")))
                or not isinstance(lead.get("rationale"), str)
                or not lead["rationale"].strip()
                or not isinstance(lead.get("supporting_source_ids"), list)
                or not lead["supporting_source_ids"]
            ):
                _finding(
                    findings,
                    "INCOMPLETE_LEAD_DISPOSITION",
                    region_id=region_id,
                    anomaly_type=anomaly_type,
                    message="Every considered lead requires a lead, disposition, rationale, and supporting sources.",
                )
                continue
            accepted_lead |= lead["disposition"] == "accepted"
            for source_id in lead["supporting_source_ids"]:
                source = sources.get(source_id)
                if source is None:
                    _finding(
                        findings,
                        "UNKNOWN_REVIEW_SOURCE",
                        region_id=region_id,
                        anomaly_type=anomaly_type,
                        source_id=str(source_id),
                        message="Lead disposition references an unknown source.",
                    )
                elif source.get("review_status") != "reviewed":
                    _finding(
                        findings,
                        "UNREVIEWED_REVIEW_SOURCE",
                        region_id=region_id,
                        anomaly_type=anomaly_type,
                        source_id=str(source_id),
                        message="Lead disposition references an unreviewed source.",
                    )
                if source_id not in locators:
                    _finding(
                        findings,
                        "MISSING_OR_MISMATCHED_SOURCE_LOCATOR",
                        region_id=region_id,
                        anomaly_type=anomaly_type,
                        source_id=str(source_id),
                        message="Every lead-disposition source requires an exact URL/locator row.",
                    )
        anomaly_ids = record.get("anomaly_ids")
        if bool(anomaly_ids) != accepted_lead:
            _finding(
                findings,
                "LEAD_CONCLUSION_MISMATCH",
                region_id=region_id,
                anomaly_type=anomaly_type,
                message="Accepted/rejected lead dispositions disagree with the record's anomaly links.",
            )
        if record.get("status") == "reviewed_none_found":
            negative_cells.add(identity)
            prose = " ".join(
                [str(record.get("rationale") or ""), str(record.get("conclusion") or "")]
                + [str(lead.get("rationale") or "") for lead in leads if isinstance(lead, dict)]
            ).casefold()
            if any(phrase in prose for phrase in GENERIC_NEGATIVE_PHRASES):
                _finding(
                    findings,
                    "TEMPLATED_NEGATIVE_RATIONALE",
                    region_id=region_id,
                    anomaly_type=anomaly_type,
                    message="Negative rationale uses a prohibited generic closure phrase.",
                )
        elif record.get("status") != "resolved_cases":
            _finding(
                findings,
                "UNRESOLVED_REVIEW_CELL",
                region_id=region_id,
                anomaly_type=anomaly_type,
                message="Review cell is neither a resolved positive nor a confirmed negative.",
            )

    expected_cells = {
        (region_id, anomaly_type)
        for region_id in WORLDWIDE_M49_SUBREGIONS
        for anomaly_type in (inventory.get("census") or {}).get("types", [])
    }
    if set(ledger_index) != expected_cells or len(expected_cells) != EXPECTED_CELL_COUNT:
        _finding(
            findings,
            "INCOMPLETE_REVIEW_LEDGER",
            message="Review ledger does not exactly cover the inventory's 22 × 11 matrix.",
        )
    if set(inventory_cells) != set(ledger_index):
        _finding(
            findings,
            "REVIEW_LEDGER_CELL_MISMATCH",
            message="Inventory and review ledger cell identities differ.",
        )
    for anomaly in inventory.get("anomalies") or []:
        anomaly_id = str(anomaly.get("anomaly_id") or "")
        groups: set[str] = set()
        for source_id in anomaly.get("source_ids") or []:
            source = sources.get(source_id)
            if source is None:
                _finding(findings, "UNKNOWN_REVIEW_SOURCE", source_id=str(source_id), message=f"Anomaly {anomaly_id} references an unknown source.")
                continue
            if source.get("review_status") != "reviewed" or not _covers(source, str(inventory.get("start_date") or "")):
                _finding(findings, "INVALID_POSITIVE_EVIDENCE", source_id=str(source_id), message=f"Anomaly {anomaly_id} source is unreviewed or temporally invalid.")
            group = source.get("independence_group")
            if isinstance(group, str) and group:
                groups.add(group)
        if len(groups) < 2:
            _finding(findings, "INSUFFICIENT_POSITIVE_PROVENANCE", message=f"Anomaly {anomaly_id} requires two independent provenance groups.")
    for region_id in sorted(WORLDWIDE_M49_SUBREGIONS):
        survey_ids = region_survey_ids.get(region_id, set())
        if len(survey_ids) != 1:
            _finding(
                findings,
                "INCONSISTENT_REGIONAL_SURVEY",
                region_id=region_id,
                message="All eleven records for a region must use one stable region-specific survey source.",
            )

    if rejected_leads is not None:
        if (
            not isinstance(rejected_leads, dict)
            or rejected_leads.get("pass_id") != inventory.get("pass_id")
            or rejected_leads.get("start_date") != inventory.get("start_date")
        ):
            _finding(findings, "INVALID_REJECTED_LEAD_IDENTITY", message="Rejected-lead pass/date identity is invalid.")
        rows = rejected_leads.get("records") if isinstance(rejected_leads, dict) else None
        rows = rows if isinstance(rows, list) else []
        rejected_index: dict[tuple[str, str], dict[str, Any]] = {}
        required_rejected = {
            "lead_id", "region_id", "anomaly_type", "lead", "disposition",
            "failure_basis", "rationale", "source_ids",
        }
        for row in rows:
            if not isinstance(row, dict) or set(row) != required_rejected:
                _finding(findings, "INVALID_REJECTED_LEAD_RECORD", message="Rejected-lead record has invalid fields.")
                continue
            key = (row["region_id"], row["anomaly_type"])
            if key in rejected_index:
                _finding(findings, "DUPLICATE_REJECTED_LEAD_CELL", region_id=key[0], anomaly_type=key[1], message="Rejected-lead cell is duplicated.")
            rejected_index[key] = row
            review = ledger_index.get(key, {})
            review_leads = review.get("considered_leads") or []
            if (
                row.get("lead_id") != f"{key[0]}/{key[1]}/bounded-survey-leads"
                or row.get("disposition") != "rejected"
                or len(review_leads) != 1
                or not isinstance(review_leads[0], dict)
                or row.get("lead") != review_leads[0].get("lead")
                or row.get("failure_basis") != review_leads[0].get("failure_basis")
                or row.get("rationale") != review_leads[0].get("rationale")
                or sorted(row.get("source_ids") or []) != sorted(review_leads[0].get("supporting_source_ids") or [])
            ):
                _finding(findings, "REJECTED_LEAD_MISMATCH", region_id=key[0], anomaly_type=key[1], message="Rejected-lead record must exactly mirror its negative review lead.")
        if set(rejected_index) != negative_cells:
            _finding(findings, "REJECTED_LEAD_COVERAGE_MISMATCH", message="Rejected-lead records must match negative cells exactly.")

    if source_access_audit is not None:
        if (
            not isinstance(source_access_audit, dict)
            or source_access_audit.get("schema_version") != "1.0.0"
            or source_access_audit.get("document_type") != "m25c_source_access_audit"
            or source_access_audit.get("pass_id") != inventory.get("pass_id")
        ):
            _finding(findings, "INVALID_SOURCE_ACCESS_AUDIT_IDENTITY", message="Source-access audit identity is invalid.")
        audit_rows = source_access_audit.get("records") if isinstance(source_access_audit, dict) else None
        audit_rows = audit_rows if isinstance(audit_rows, list) else []
        audited: dict[str, dict[str, Any]] = {}
        required_audit = {"source_id", "url", "checked_on", "method", "result", "http_status", "notes"}
        for row in audit_rows:
            if not isinstance(row, dict) or set(row) != required_audit:
                _finding(findings, "INVALID_SOURCE_ACCESS_AUDIT", message="Source-access audit record has invalid fields.")
                continue
            source_id = row.get("source_id")
            if source_id in audited:
                _finding(findings, "DUPLICATE_SOURCE_ACCESS_AUDIT", source_id=str(source_id), message="Source-access audit record is duplicated.")
            audited[source_id] = row
            source = sources.get(source_id)
            if source is None or row.get("url") != source.get("url"):
                _finding(findings, "SOURCE_ACCESS_AUDIT_MISMATCH", source_id=str(source_id), message="Source-access audit URL/source does not match the manifest.")
            if row.get("result") != "reachable" or row.get("method") not in {"automated_get", "browser_open", "browser_search"}:
                _finding(findings, "UNRESOLVED_SOURCE_ACCESS", source_id=str(source_id), message="Source URL has no successful automated or browser-confirmed access record.")
            try:
                date.fromisoformat(row.get("checked_on"))
            except (TypeError, ValueError):
                _finding(findings, "INVALID_SOURCE_ACCESS_AUDIT", source_id=str(source_id), message="Source-access checked_on must be an ISO date.")
        if set(audited) != set(sources):
            _finding(findings, "SOURCE_ACCESS_AUDIT_COVERAGE_MISMATCH", message="Source-access audit must cover every manifest source exactly once.")
    return sorted(
        findings,
        key=lambda row: (
            row["code"],
            row["region_id"],
            row["anomaly_type"],
            row["source_id"],
        ),
    )


def invalid_reviewer_identity(reviewer: Any, researcher: Any = "") -> bool:
    if not isinstance(reviewer, str) or not reviewer.strip():
        return True
    normalized = reviewer.strip().casefold()
    if normalized == str(researcher or "").strip().casefold():
        return True
    banned = {
        "generator",
        "gpm qa render",
        "openai codex",
        "openai codex (research agent)",
        "pending-independent-review",
        "reviewer",
        "reviewer name",
        "human reviewer",
        "placeholder",
        "tbd",
        "todo",
        "unknown",
        "test reviewer",
        "reviewer example",
        "structural review sentinel (not persisted)",
    }
    return normalized in banned or any(token in normalized for token in ("placeholder", "generator"))


def acceptance_findings(
    acceptance: dict[str, Any],
    *,
    frozen_sha256sums_sha256: str,
    inventory: dict[str, Any],
) -> list[str]:
    findings: list[str] = []
    if set(acceptance) != ACCEPTANCE_FIELDS:
        findings.append("acceptance sidecar has missing or unexpected fields")
    if (
        acceptance.get("schema_version") != "1.0.0"
        or acceptance.get("document_type") != "m25c_anomaly_census_review_acceptance"
        or acceptance.get("pass_id") != inventory.get("pass_id")
        or acceptance.get("start_date") != inventory.get("start_date")
    ):
        findings.append("acceptance sidecar has the wrong schema/pass/date identity")
    if acceptance.get("decision") != "accepted":
        findings.append("acceptance sidecar decision must be accepted")
    if invalid_reviewer_identity(
        acceptance.get("reviewer"),
        (inventory.get("census") or {}).get("researcher"),
    ):
        findings.append("acceptance reviewer must be a distinct named human")
    try:
        date.fromisoformat(acceptance.get("review_date"))
    except (TypeError, ValueError):
        findings.append("acceptance review_date must be a valid ISO date")
    if acceptance.get("frozen_sha256sums_sha256") != frozen_sha256sums_sha256:
        findings.append("acceptance sidecar does not match the frozen SHA256SUMS")
    counts = acceptance.get("reviewed_scope_counts")
    expected_counts = {
        "regions": 22,
        "classes": 11,
        "cells": 242,
        "anomalies": len(inventory.get("anomalies") or []),
    }
    if counts != expected_counts:
        findings.append(f"acceptance reviewed_scope_counts must equal {expected_counts}")
    return findings


def overlay_acceptance(inventory: dict[str, Any], acceptance: dict[str, Any]) -> dict[str, Any]:
    """Return an accepted inventory copy without mutating frozen packet bytes."""
    result = copy.deepcopy(inventory)
    result["census"]["reviewer"] = acceptance["reviewer"].strip()
    result["census"]["review_date"] = acceptance["review_date"]
    return result
