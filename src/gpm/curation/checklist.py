"""Contribution checklist for curator bundles and scenario PRs (M17)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from gpm.curation.bundles import (
    CuratorBundleError,
    load_curator_bundle,
    validate_curator_bundle,
)

# Items reviewers expect for an official or community scenario contribution.
CHECKLIST_ITEMS: tuple[tuple[str, str], ...] = (
    ("sources_documented", "Source lineage is documented (source_lineage / notes)"),
    ("licenses_reviewed", "Licenses reviewed; no restricted sources in public path"),
    ("no_restricted_sources", "Bundle attests no_restricted_sources"),
    ("golden_borders_present", "Golden floors and/or golden borders are present"),
    ("scenario_files_valid", "Scenario JSON files validate against project rules"),
    ("manifest_valid", "Bundle manifest validates"),
    ("qa_pass_claimed", "Author claims gpm qa scenario pass (self-attested)"),
)


@dataclass(frozen=True)
class ChecklistResult:
    bundle_id: str
    path: str
    status: str
    passed_count: int
    failed_count: int
    warning_count: int
    items: tuple[dict[str, Any], ...]

    @property
    def passed(self) -> bool:
        return self.status == "pass"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_contribution_checklist(
    bundle: str | Path,
    *,
    search_dirs: list[Path] | None = None,
    require_qa_claimed: bool = False,
) -> ChecklistResult:
    """Evaluate a curator bundle against the community contribution checklist.

    Returns ``status=pass`` when all hard requirements succeed. Self-attested
    ``qa_pass_claimed`` is a warning unless ``require_qa_claimed`` is true.
    """
    document = load_curator_bundle(bundle, search_dirs=search_dirs)
    root = Path(document["_root"])
    items: list[dict[str, Any]] = []

    # Manifest validity
    try:
        validate_curator_bundle(
            document,
            bundle_root=root,
            check_files=True,
            check_scenarios=True,
        )
        items.append(_item("manifest_valid", True, "Bundle manifest and files are valid."))
        items.append(_item("scenario_files_valid", True, "All scenario files validate."))
    except CuratorBundleError as exc:
        items.append(_item("manifest_valid", False, str(exc), severity="error"))
        items.append(
            _item(
                "scenario_files_valid",
                False,
                "Skipped or failed because bundle validation failed.",
                severity="error",
            )
        )

    attested = document.get("checklist") if isinstance(document.get("checklist"), dict) else {}
    source_lineage = document.get("source_lineage") or []
    license_lineage = document.get("license_lineage") or []
    has_sources = bool(source_lineage) or bool(attested.get("sources_documented"))
    items.append(
        _item(
            "sources_documented",
            has_sources,
            "source_lineage present or checklist.sources_documented=true"
            if has_sources
            else "Add source_lineage or set checklist.sources_documented=true",
            severity="error" if not has_sources else "info",
        )
    )

    has_licenses = bool(license_lineage) or bool(document.get("license")) or bool(
        attested.get("licenses_reviewed")
    )
    items.append(
        _item(
            "licenses_reviewed",
            has_licenses,
            "license / license_lineage present"
            if has_licenses
            else "Set license and review licenses for every source",
            severity="error" if not has_licenses else "info",
        )
    )

    no_restricted = attested.get("no_restricted_sources")
    items.append(
        _item(
            "no_restricted_sources",
            no_restricted is True,
            "checklist.no_restricted_sources=true"
            if no_restricted is True
            else "Set checklist.no_restricted_sources=true after license review",
            severity="error" if no_restricted is not True else "info",
        )
    )

    golden_count = sum(
        1
        for entry in document.get("scenarios") or []
        if isinstance(entry, dict) and entry.get("golden_path")
    )
    golden_ok = golden_count > 0 or bool(attested.get("golden_borders_present"))
    items.append(
        _item(
            "golden_borders_present",
            golden_ok,
            f"{golden_count} golden file(s) linked"
            if golden_ok
            else "Add golden_path entries or set checklist.golden_borders_present",
            severity="error" if not golden_ok else "info",
        )
    )

    qa_claimed = attested.get("qa_pass_claimed") is True
    qa_severity = "error" if require_qa_claimed and not qa_claimed else (
        "warning" if not qa_claimed else "info"
    )
    items.append(
        _item(
            "qa_pass_claimed",
            qa_claimed,
            "Author attested gpm qa scenario pass"
            if qa_claimed
            else "Run gpm qa scenario and set checklist.qa_pass_claimed=true",
            severity=qa_severity,
        )
    )

    # Deprecation policy awareness (informational)
    deprecation = document.get("deprecation")
    if isinstance(deprecation, dict) and deprecation.get("policy"):
        items.append(
            _item(
                "deprecation_policy",
                True,
                f"Deprecation policy noted: {str(deprecation.get('policy'))[:120]}",
                severity="info",
            )
        )
    else:
        items.append(
            _item(
                "deprecation_policy",
                True,
                "No deprecation block (optional for community bundles)",
                severity="info",
            )
        )

    error_fails = [item for item in items if item["severity"] == "error" and not item["passed"]]
    warnings = [item for item in items if item["severity"] == "warning" and not item["passed"]]
    passed = [item for item in items if item["passed"]]
    status = "pass" if not error_fails else "fail"

    return ChecklistResult(
        bundle_id=str(document.get("bundle_id")),
        path=str(root),
        status=status,
        passed_count=len(passed),
        failed_count=len(error_fails),
        warning_count=len(warnings),
        items=tuple(items),
    )


def _item(
    code: str,
    passed: bool,
    message: str,
    *,
    severity: str = "info",
) -> dict[str, Any]:
    label = dict(CHECKLIST_ITEMS).get(code, code)
    return {
        "code": code,
        "label": label,
        "passed": passed,
        "severity": severity,
        "message": message,
    }
