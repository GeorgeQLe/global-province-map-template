#!/usr/bin/env python3
"""Record the independent review of the M25C best-reasonable evidence packet.

This script serializes an already-made review policy. It does not generate new
research or infer stronger evidence from the packet's confidence labels.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "research/start-dates/1444-global-v1/replacement-evidence/best-reasonable-v1"
OUTPUT = PACKET / "review-decisions.json"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def signed(record: dict[str, Any]) -> dict[str, Any]:
    record["decision_sha256"] = canonical_hash(record)
    return record


def component_is_grade_c(record: dict[str, Any]) -> bool:
    evidence = record["spatial_corroboration"]
    return (
        evidence["historical_basemap_1400"]["named_match_count"] > 0
        and evidence["historical_basemap_1492"]["named_match_count"] > 0
    )


def build() -> dict[str, Any]:
    manifest = load(PACKET / "manifest.json")
    pairs = load(PACKET / "pair-evidence.json")["records"]
    components = load(PACKET / "component-evidence.json")["records"]
    findings = load(PACKET / "finding-routes.json")["records"]

    # No pair is accepted. The exact pair and incident IDs are useful indexing,
    # but the source surface is still an aggregate: every regional source ID is
    # attached to every pair, and feature names/counts are not mapped to either
    # actor or to each incident component. That cannot independently establish
    # either proposed applicability disposition.
    pair_decisions = [
        signed({
            "pair_id": row["pair_id"],
            "region_id": row["region_id"],
            "evidence_record_sha256": row["record_sha256"],
            "decision": "reject",
            "accepted_scope": "none",
            "geometry_grade": "not_applicable",
            "reason": (
                "The record aggregates region-wide citations and candidate-derived incident "
                "components without mapping a qualifying source claim to either actor. Named "
                "representative-point matches do not independently establish the proposed pair "
                "disposition or a positive boundary."
            ),
        })
        for row in pairs
    ]

    component_decisions = []
    accepted_component_ids = set()
    for row in components:
        if component_is_grade_c(row):
            accepted_component_ids.add(row["component_id"])
            decision = {
                "component_id": row["component_id"],
                "region_id": row["region_id"],
                "evidence_record_sha256": row["record_sha256"],
                "decision": "accept",
                "accepted_scope": "documented_approximate_geometry_scaffold_only",
                "geometry_grade": "C",
                "known_gaps": [
                    "The source snapshots bracket 1444-11-11 by 44 and 48 years.",
                    "Only the component representative point was tested against source polygons.",
                    "No source-derived component edge, error measurement, or complete containment test is present.",
                    "Political actor, facets, relationships, and Grade A/B are not accepted.",
                ],
                "reason": (
                    "A named approximate source polygon contains the representative point in both "
                    "bracketing snapshots. This supports only a disclosed Grade C scaffold."
                ),
            }
        else:
            decision = {
                "component_id": row["component_id"],
                "region_id": row["region_id"],
                "evidence_record_sha256": row["record_sha256"],
                "decision": "reject",
                "accepted_scope": "none",
                "geometry_grade": "U",
                "reason": (
                    "The record lacks named representative-point corroboration in both bracketing "
                    "snapshots. Any source-tagged OpenHistoricalMap match is also insufficient here "
                    "because the packet omits the feature's source value and date-lineage detail "
                    "needed for independent qualification."
                ),
            }
        component_decisions.append(signed(decision))

    finding_decisions = []
    for row in findings:
        component_route = bool(row["component_evidence_ids"])
        accepted = component_route and all(
            component_id in accepted_component_ids
            for component_id in row["component_evidence_ids"]
        )
        if accepted:
            decision = {
                "region_id": row["region_id"],
                "finding_code": row["finding_code"],
                "evidence_record_sha256": row["record_sha256"],
                "decision": "accept",
                "accepted_scope": "serial_documented_grade_c_reconstruction_only",
                "geometry_grade": "C",
                "reason": (
                    "Every routed component has separately accepted two-snapshot representative-point "
                    "corroboration. The route may be implemented only as an explicitly incomplete Grade C "
                    "reconstruction and does not clear a Grade A, seam, QA, or certification gate by itself."
                ),
            }
        else:
            decision = {
                "region_id": row["region_id"],
                "finding_code": row["finding_code"],
                "evidence_record_sha256": row["record_sha256"],
                "decision": "reject",
                "accepted_scope": "none",
                "geometry_grade": "not_applicable" if row["pair_evidence_ids"] else "U",
                "reason": (
                    "All routed pair records are rejected because they lack pair-to-citation claim mapping."
                    if row["pair_evidence_ids"] else
                    "At least one routed component lacks the evidence needed even for a Grade C reconstruction."
                ),
            }
        finding_decisions.append(signed(decision))

    accepted_components = sum(row["decision"] == "accept" for row in component_decisions)
    accepted_findings = sum(row["decision"] == "accept" for row in finding_decisions)
    return {
        "document_type": "m25c_best_reasonable_independent_review",
        "schema_version": "1.0.0",
        "start_date": "1444-11-11",
        "review_date": "2026-08-24",
        "reviewer": "Codex independent evidence review",
        "status": "reviewed; narrow Grade C acceptance; not implemented",
        "reviewed_artifacts": [
            {
                "path": artifact["path"],
                "sha256": artifact["sha256"],
            }
            for artifact in manifest["artifacts"]
        ] + [{"path": "manifest.json", "sha256": file_hash(PACKET / "manifest.json")}],
        "decision_policy": {
            "pair_records": (
                "Reject unless the record maps qualifying evidence claims to both exact actors and the "
                "complete incident-component surface; this packet does not do so."
            ),
            "component_records": (
                "Accept only named representative-point corroboration in both the 1400 and 1492 "
                "snapshots, and only as Grade C geometry scaffolding."
            ),
            "openhistoricalmap": (
                "Do not elevate a row from its OHM sourced-feature flag because the review packet does "
                "not expose the source value or enough date-lineage metadata to qualify that feature."
            ),
            "finding_routes": (
                "Accept a component route only when every routed component is accepted; reject every "
                "pair route because every routed pair is rejected."
            ),
        },
        "pair_decisions": pair_decisions,
        "component_decisions": component_decisions,
        "finding_decisions": finding_decisions,
        "totals": {
            "pair_accept": 0,
            "pair_reject": len(pair_decisions),
            "component_accept_grade_c": accepted_components,
            "component_reject_ungraded": len(component_decisions) - accepted_components,
            "finding_accept_grade_c": accepted_findings,
            "finding_reject": len(finding_decisions) - accepted_findings,
        },
        "implementation_boundary": [
            "Acceptance does not approve current political actors, facets, relationships, or source-derived borders.",
            "No decision is Grade A or Grade B.",
            "Accepted records may be implemented only serially with recorded Grade C gaps and regenerated QA.",
            "No assembled artifact, tolerance, permission, runtime output, publication state, or Task 17 state changes here.",
        ],
    }


def main() -> None:
    OUTPUT.write_text(
        json.dumps(build(), indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
