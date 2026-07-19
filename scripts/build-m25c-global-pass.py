#!/usr/bin/env python3
"""Build the fail-closed M25C 1444 worldwide certification lineage.

The generator never signs review work or invents missing historical evidence.
Early stages can therefore create a deterministic pending candidate, while
assembly/certification stop until curated inputs meet the schema 0.3.0 gates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gpm.qa.certification import certify_era  # noqa: E402
from gpm.qa.render import render_start_date_pass  # noqa: E402
from gpm.qa.start_date import run_start_date_qa  # noqa: E402
from gpm.runtime import compile_runtime_pack  # noqa: E402

PASS_ID = "official-1444-global-v1"
START_DATE = "1444-11-11"
DEFAULT_OUTPUT = ROOT / "research" / "start-dates" / "1444-global-v1"
PILOT = ROOT / "research" / "start-dates" / "1444-v2"
ANOMALY_TYPES = (
    "microstate", "detached-territory", "enclave-exclave", "free-protected-city",
    "composite-realm", "dependency", "condominium", "concession", "claim",
    "disputed-area", "non-state-territory",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("inventory", "fabric", "aggregation", "assembly", "render", "canonical", "runtime", "certification", "full-pipeline"))
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--inventory-input", type=Path)
    parser.add_argument("--fabric-input", type=Path)
    parser.add_argument("--runtime-dir", type=Path)
    parser.add_argument("--certification-output", type=Path)
    args = parser.parse_args()
    stages = ("inventory", "fabric", "aggregation", "assembly", "render", "canonical", "runtime", "certification") if args.stage == "full-pipeline" else (args.stage,)
    for stage in stages:
        globals()[f"stage_{stage.replace('-', '_')}"](args)
    return 0


def stage_inventory(args: argparse.Namespace) -> None:
    output = args.output_dir.resolve()
    (output / "provenance").mkdir(parents=True, exist_ok=True)
    pilot_files = {
        path.relative_to(PILOT).as_posix(): _sha256(path)
        for path in sorted(PILOT.rglob("*")) if path.is_file()
    }
    _write(output / "provenance" / "1444-v2-seed.json", {
        "schema_version": "1.0.0", "source_lineage": "1444-v2",
        "reuse_policy": "read-only-hash-pinned-evidence-only",
        "promotion_prohibited": True, "files": pilot_files,
    })
    if args.inventory_input:
        inventory = _load(args.inventory_input)
    else:
        inventory = {
            "schema_version": "0.3.0", "document_type": "historical_anomaly_inventory",
            "artifact_version": "1.0.0", "pass_id": PASS_ID, "start_date": START_DATE,
            "anomalies": [
                {"anomaly_id": f"pending-{kind}", "type": kind, "subject_ids": ["pending"],
                 "source_ids": ["pending"], "resolution": "pending_evidence"}
                for kind in ANOMALY_TYPES
            ],
        }
    _write(output / "anomaly_inventory.json", inventory)
    _write(output / "candidate_status.json", {
        "pass_id": PASS_ID, "start_date": START_DATE,
        "status": "pending_historical_evidence_and_independent_review",
        "public_release_allowed": False,
    })


def stage_fabric(args: argparse.Namespace) -> None:
    if args.fabric_input is None:
        raise SystemExit("fabric stage requires --fabric-input from the accepted M23 playable land fabric")
    document = _load(args.fabric_input)
    features = document.get("features") or []
    if not features:
        raise SystemExit("fabric input contains no playable locations")
    missing = [str((feature.get("properties") or {}).get("location_id")) for feature in features if not (feature.get("properties") or {}).get("m49_subregion")]
    if missing:
        raise SystemExit(f"fabric locations lack pinned M49 subregions: {', '.join(missing[:10])}")
    output = args.output_dir.resolve()
    (output / "sidecars").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(args.fabric_input, output / "sidecars" / "locations.geojson")
    mask = {
        "schema_version": "0.3.0", "document_type": "world_coverage_mask", "artifact_version": "1.0.0",
        "pass_id": PASS_ID, "start_date": START_DATE, "fabric_revision": "1444-global-r1",
        "type": "FeatureCollection", "features": [
            {"type": "Feature", "geometry": feature["geometry"], "properties": {
                "location_id": feature["properties"]["location_id"],
                "region_id": feature["properties"]["m49_subregion"],
            }} for feature in sorted(features, key=lambda item: item["properties"]["location_id"])
            if feature["properties"].get("m49_subregion") != "Antarctica"
        ],
    }
    _write(output / "world_coverage_mask.geojson", mask)


def stage_aggregation(args: argparse.Namespace) -> None:
    _require_resolved_inventory(args.output_dir)
    required = (args.output_dir / "assignments.json", args.output_dir / "build.geojson")
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise SystemExit("aggregation requires reviewed worldwide inputs; missing: " + ", ".join(missing))


def stage_assembly(args: argparse.Namespace) -> None:
    _require_resolved_inventory(args.output_dir)
    result = run_start_date_qa(pass_dir=args.output_dir)
    if not result.passed:
        raise SystemExit(f"worldwide assembly failed research QA with {result.error_count} error(s)")


def stage_render(args: argparse.Namespace) -> None:
    result = render_start_date_pass(pass_dir=args.output_dir, output_dir=args.output_dir / "review")
    print(json.dumps(result.to_dict(), sort_keys=True))


def stage_canonical(args: argparse.Namespace) -> None:
    canonical = args.output_dir / "historical-territory-status.json"
    if not canonical.is_file():
        raise SystemExit("canonical stage requires the reviewed historical-territory-status.json")
    result = run_start_date_qa(pass_dir=args.output_dir)
    if not result.passed:
        raise SystemExit("canonical conversion is blocked until worldwide research QA passes")


def stage_runtime(args: argparse.Namespace) -> None:
    canonical = args.output_dir / "historical-territory-status.json"
    runtime = (args.runtime_dir or args.output_dir / "runtime").resolve()
    compile_runtime_pack(canonical, runtime, pack_id=PASS_ID)


def stage_certification(args: argparse.Namespace) -> None:
    runtime = (args.runtime_dir or args.output_dir / "runtime").resolve()
    output = (args.certification_output or args.output_dir / "global_certification.json").resolve()
    result = certify_era(pass_dir=args.output_dir, runtime_dir=runtime, output=output)
    print(json.dumps(result.to_dict(), sort_keys=True))


def _require_resolved_inventory(output: Path) -> None:
    inventory = _load(output / "anomaly_inventory.json")
    unresolved = [row["anomaly_id"] for row in inventory.get("anomalies", []) if row.get("resolution") != "resolved"]
    if unresolved:
        raise SystemExit(f"unresolved worldwide anomalies block release: {', '.join(unresolved)}")


def _load(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
