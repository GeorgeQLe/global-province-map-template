#!/usr/bin/env python3
"""Build the decision-gated M25C Chorotega aggregate-model revision packet."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXACT = ROOT / "research/start-dates/1444-global-v1/replacement-evidence/exact-source-v1"
PRIOR = ROOT / "research/start-dates/1444-global-v1/replacement-evidence/actor-component-specific-v1"
REGION = ROOT / "research/start-dates/1444-global-v1/regional-packets/013-central-america-2026-08-16.json"
REGION_GENERATOR = ROOT / "scripts/generate-m25c-region-013-packet.py"
OUTPUT = ROOT / "research/start-dates/1444-global-v1/replacement-evidence/synthetic-actor-model-revision-v1"
ACTOR_ID = "scenario-chorotega-polities"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record_hash(record: dict[str, Any]) -> str:
    return canonical_hash({key: value for key, value in record.items() if key != "record_sha256"})


def write_json(name: str, value: Any) -> dict[str, Any]:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    path = OUTPUT / name
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"path": name, "bytes": path.stat().st_size, "sha256": file_hash(path)}


def only(records: list[dict[str, Any]], key: str, value: str) -> dict[str, Any]:
    matches = [record for record in records if record[key] == value]
    if len(matches) != 1:
        raise SystemExit(f"expected one {key}={value}, found {len(matches)}")
    return matches[0]


def main() -> None:
    exact_actor_path = EXACT / "actor-citation-evidence.json"
    exact_pair_path = EXACT / "pair-evidence.json"
    prior_actor_path = PRIOR / "actor-specific-evidence.json"
    region = load(REGION)
    exact_actor = only(load(exact_actor_path)["records"], "actor_id", ACTOR_ID)
    prior_actor = only(load(prior_actor_path)["records"], "actor_id", ACTOR_ID)
    polity = only(region["polities"], "polity_id", ACTOR_ID)
    assignment = only(region["assignment_overrides"], "province_id", "prv_4839d93e9052a93c9eff")
    dispatch_clause = 'return "scenario-chorotega-polities" if y >= 13.2 else "scenario-nicarao-polities"'
    if dispatch_clause not in REGION_GENERATOR.read_text(encoding="utf-8"):
        raise SystemExit("region 013 Chorotega dispatch changed; fresh model analysis required")
    pairs = sorted(
        (
            record for record in load(exact_pair_path)["records"]
            if ACTOR_ID in {record["left_actor_id"], record["right_actor_id"]}
        ),
        key=lambda record: record["pair_id"],
    )
    if len(pairs) != 3:
        raise SystemExit(f"expected three incident Chorotega pairs, found {len(pairs)}")

    bindings = exact_actor["component_to_citation_bindings"]
    if [row["component_id"] for row in bindings] != exact_actor["incident_component_inventory"]:
        raise SystemExit("Chorotega component binding no longer matches its incident inventory")
    feature_bindings = bindings[0]["source_feature_bindings"]

    pair_revisions = []
    for pair in pairs:
        neighbor = pair["right_actor_id"] if pair["left_actor_id"] == ACTOR_ID else pair["left_actor_id"]
        revision = {
            "pair_id": pair["pair_id"],
            "neighbor_actor_id": neighbor,
            "incident_component_ids": pair["incident_component_ids"],
            "prior_exact_source_record_sha256": pair["record_sha256"],
            "proposed_semantics": "community_fabric_transition_not_hard_border",
            "independent_shared_line_obtained": False,
            "positive_border_disposition": "not_applicable_only_if_independent_region_013_adjacency_review_accepts_the_revised_model",
            "implementation_status": "not_implemented_pending_reviewer_decision",
        }
        revision["record_sha256"] = record_hash(revision)
        pair_revisions.append(revision)

    actor_revision = {
        "actor_id": ACTOR_ID,
        "current_name": polity["name"],
        "region_id": "013",
        "component_ids": exact_actor["incident_component_inventory"],
        "prior_actor_specific_record_sha256": prior_actor["record_sha256"],
        "prior_exact_source_record_sha256": exact_actor["record_sha256"],
        "current_model": {
            "actor_kind": polity["actor_kind"],
            "assignment_polity_ids": assignment["polity_ids"],
            "status_relationships": assignment["status_relationships"],
            "authority_facet": assignment["facets"]["authority"],
            "generator_dispatch": "Natural Earth NIC country membership, then centroid latitude >= 13.2 degrees",
        },
        "named_later_source_features": [
            {
                "source_feature_id": row["source_feature_id"],
                "name": row["name"],
                "language_family": row["language_family"],
                "component_area_ratio": row["component_area_ratio"],
                "feature_sha256": row["feature_sha256"],
            }
            for row in feature_bindings
        ],
        "diagnosis": [
            "The current polity label is assigned by a modern-country and latitude heuristic rather than an exact-date Chorotega polygon.",
            "The only measurable polygon binding is a later generalized ethnolinguistic surface and names Matagalpa, Silam, Ulva, Yosco, and Maribichicoa rather than Chorotega.",
            "A territorial_presence relationship with unknown authority supports a coarse community fabric, not a hard polity boundary.",
        ],
        "proposed_model": {
            "replacement_actor_id": "scenario-northern-nicaragua-community-fabric-unresolved",
            "name": "Northern Nicaraguan community fabric (1444 identity unresolved)",
            "actor_kind": "community",
            "relationship": "territorial_presence",
            "certainty": "uncertain",
            "authority_facet": "unknown",
            "sovereign_polity_id": None,
            "owner_polity_id": None,
            "controller_polity_id": None,
            "hard_border_eligible": False,
        },
        "recommendation": "approve_for_serial_implementation_after_independent_review",
        "implementation_status": "not_implemented_pending_reviewer_decision",
        "expected_immediate_qa_impact": {
            "non_review_errors": 0,
            "warnings": 0,
            "reason": "This research packet changes no canonical or assembled artifact. Even after approval, region 013 requires a complete independently reviewed adjacency audit before any positive-border exemption can pass.",
        },
    }
    actor_revision["record_sha256"] = record_hash(actor_revision)

    revision_doc = {
        "document_type": "m25c-synthetic-aggregate-actor-model-revision",
        "schema_version": "1.0.0",
        "start_date": "1444-11-11",
        "decision_status": "recommended_pending_independent_review",
        "actor_revision": actor_revision,
        "incident_pair_revisions": pair_revisions,
        "alternatives": [
            {
                "alternative": "retain_chorotega_polity",
                "disposition": "rejected",
                "tradeoff": "Preserves a familiar label but continues to imply an exact actor identity and three hard borders unsupported by the sources.",
            },
            {
                "alternative": "rename_to_the_later_driver_features",
                "disposition": "rejected",
                "tradeoff": "Would improve agreement with a later map while projecting sixteenth-to-twentieth-century observations backward to 1444.",
            },
            {
                "alternative": "remove_all_human_presence",
                "disposition": "rejected",
                "tradeoff": "Avoids synthetic identity but falsely converts source uncertainty into evidence of an empty landscape.",
            },
        ],
        "decision_boundary": [
            "No exact-date actor polygon or independently derived shared line was obtained.",
            "The later Driver geometry is mismatch evidence only and is not promoted into 1444 geometry.",
            "The proposed community fabric must not qualify region 013 by itself; all land-adjacent pairs still require a complete hash-bound applicability audit and independent acceptance.",
            "No packet, QA result, tolerance, permission, or Task 17 state is changed.",
        ],
    }
    artifact = write_json("chorotega-model-revision.json", revision_doc)
    manifest = {
        "document_type": "m25c-synthetic-actor-model-revision-manifest",
        "schema_version": "1.0.0",
        "start_date": "1444-11-11",
        "status": "research complete; one aggregate-model revision recommended; not implemented",
        "frozen_inputs": [
            {"path": str(path.relative_to(ROOT)), "sha256": file_hash(path)}
            for path in (REGION, REGION_GENERATOR, prior_actor_path, exact_actor_path, exact_pair_path)
        ],
        "totals": {
            "named_actor_revisions": 1,
            "incident_components": 1,
            "incident_pairs": 3,
            "exact_date_actor_polygons_obtained": 0,
            "independent_shared_lines_obtained": 0,
            "implementation_changes": 0,
            "immediate_qa_change": 0,
        },
        "artifacts": [artifact],
    }
    write_json("manifest.json", manifest)
    print(json.dumps(manifest["totals"], sort_keys=True))


if __name__ == "__main__":
    main()
