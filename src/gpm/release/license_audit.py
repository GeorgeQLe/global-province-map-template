"""M14 license audit for public beta releases.

Ensures published datasets only contain cleaned, redistributable lineage:
no restricted sources, no share-alike/ODbL contamination in the default
public path, and a complete attribution pack with isolation notes for
sources that must stay off the public release path.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

from gpm.config import default_source_ids, load_profile, load_source_catalog

# License postures that may ship in the public (core) release path.
PUBLIC_SAFE_POSTURES: frozenset[str] = frozenset(
    {
        "public-domain",
        "attribution-required",
        "citation-required",
    }
)

# Postures that require isolation or exclusion from public releases.
ISOLATED_OR_RESTRICTED_POSTURES: frozenset[str] = frozenset(
    {
        "share-alike-database",
        "restricted",
        "review-per-feature",
    }
)

# Patterns in feature license_lineage / source_lineage that must not appear
# in a public beta package.
FORBIDDEN_LINEAGE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("restricted-gadm", re.compile(r"\bgadm\b", re.IGNORECASE)),
    ("odbl-openstreetmap", re.compile(r"\b(odbl|openstreetmap|open\s*street\s*map)\b", re.IGNORECASE)),
    ("restricted-generic", re.compile(r"\brestricted\b", re.IGNORECASE)),
    ("share-alike", re.compile(r"share[\s-]*alike", re.IGNORECASE)),
)

SEVERITY_ERROR = "error"
SEVERITY_WARNING = "warning"
SEVERITY_INFO = "info"


class LicenseAuditError(RuntimeError):
    """Raised when a license audit finds blocking violations."""


@dataclass
class LicenseFinding:
    code: str
    severity: str
    message: str
    source_id: str | None = None
    detail: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        return {key: value for key, value in payload.items() if value is not None}


@dataclass
class LicenseAuditResult:
    passed: bool
    profile_id: str
    release_channel: str
    findings: list[LicenseFinding] = field(default_factory=list)
    catalog_sources: list[dict[str, Any]] = field(default_factory=list)
    public_source_ids: list[str] = field(default_factory=list)
    isolated_source_ids: list[str] = field(default_factory=list)
    restricted_source_ids: list[str] = field(default_factory=list)
    feature_license_lineage: list[str] = field(default_factory=list)
    feature_source_lineage: list[str] = field(default_factory=list)
    attribution_records: list[dict[str, Any]] = field(default_factory=list)
    isolation_notes: list[str] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for item in self.findings if item.severity == SEVERITY_ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for item in self.findings if item.severity == SEVERITY_WARNING)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "0.1.0",
            "report_type": "license-audit",
            "milestone": "M14",
            "passed": self.passed,
            "profile_id": self.profile_id,
            "release_channel": self.release_channel,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "public_source_ids": list(self.public_source_ids),
            "isolated_source_ids": list(self.isolated_source_ids),
            "restricted_source_ids": list(self.restricted_source_ids),
            "feature_license_lineage": list(self.feature_license_lineage),
            "feature_source_lineage": list(self.feature_source_lineage),
            "catalog_sources": list(self.catalog_sources),
            "attribution_records": list(self.attribution_records),
            "isolation_notes": list(self.isolation_notes),
            "findings": [item.to_dict() for item in self.findings],
            "policy": {
                "public_safe_postures": sorted(PUBLIC_SAFE_POSTURES),
                "isolated_or_restricted_postures": sorted(ISOLATED_OR_RESTRICTED_POSTURES),
                "forbidden_lineage_codes": [code for code, _ in FORBIDDEN_LINEAGE_PATTERNS],
                "notes": [
                    "Public beta may only ship core-path sources with public-safe postures.",
                    "ODbL / share-alike databases stay on optional-isolated paths.",
                    "Restricted sources (e.g. GADM) stay excluded unless permission is obtained.",
                    "Every redistributed feature must carry license_lineage.",
                ],
            },
        }


def audit_public_release(
    *,
    profile_id: str,
    features: list[dict[str, Any]],
    release_channel: str = "beta",
    require_feature_license_lineage: bool = True,
    fail_on_errors: bool = True,
) -> LicenseAuditResult:
    """Audit catalog policy + feature lineage for a public release package.

    Raises :class:`LicenseAuditError` when *fail_on_errors* is true and any
    error-severity findings are present.
    """
    profile = load_profile(profile_id)
    catalog = load_source_catalog()
    profile_defaults = set(default_source_ids(profile))

    findings: list[LicenseFinding] = []
    catalog_sources: list[dict[str, Any]] = []
    public_ids: list[str] = []
    isolated_ids: list[str] = []
    restricted_ids: list[str] = []
    isolation_notes: list[str] = []

    for source_id, source in sorted(catalog.items()):
        posture = str(source.get("license_posture") or "")
        restricted = bool(source.get("restricted"))
        isolated = bool(source.get("isolated"))
        optional = bool(source.get("optional"))
        eligible = bool(source.get("eligible_for_default_build"))
        enabled = bool(source.get("enabled_by_default"))
        default_path = str(source.get("default_path") or "")
        entry = {
            "source_id": source_id,
            "name": source.get("name"),
            "license": source.get("license"),
            "license_posture": posture,
            "attribution_text": source.get("attribution_text"),
            "source_url": source.get("source_url"),
            "restricted": restricted,
            "isolated": isolated,
            "optional": optional,
            "eligible_for_default_build": eligible,
            "enabled_by_default": enabled,
            "default_path": default_path,
            "in_profile_default": source_id in profile_defaults,
        }
        catalog_sources.append(entry)

        if restricted:
            restricted_ids.append(source_id)
            isolation_notes.append(
                f"{source_id}: restricted — excluded from public releases "
                f"({source.get('license')})."
            )
            if source_id in profile_defaults:
                findings.append(
                    LicenseFinding(
                        code="restricted-in-profile-default",
                        severity=SEVERITY_ERROR,
                        message=(
                            f"Restricted source '{source_id}' is listed in profile "
                            f"'{profile_id}' sources.default."
                        ),
                        source_id=source_id,
                    )
                )
            if eligible:
                findings.append(
                    LicenseFinding(
                        code="restricted-marked-eligible",
                        severity=SEVERITY_ERROR,
                        message=(
                            f"Restricted source '{source_id}' is marked "
                            "eligible_for_default_build."
                        ),
                        source_id=source_id,
                    )
                )
            continue

        if isolated or posture in ISOLATED_OR_RESTRICTED_POSTURES:
            isolated_ids.append(source_id)
            isolation_notes.append(
                f"{source_id}: isolated/optional path — posture `{posture}` "
                f"({source.get('license')}). Not mixed into public beta packs."
            )
            if source_id in profile_defaults:
                findings.append(
                    LicenseFinding(
                        code="isolated-in-profile-default",
                        severity=SEVERITY_ERROR,
                        message=(
                            f"Isolated or non-public posture source '{source_id}' is in "
                            f"profile '{profile_id}' sources.default."
                        ),
                        source_id=source_id,
                        detail=posture,
                    )
                )
            if eligible and posture == "share-alike-database":
                findings.append(
                    LicenseFinding(
                        code="share-alike-marked-eligible",
                        severity=SEVERITY_ERROR,
                        message=(
                            f"Share-alike source '{source_id}' is marked "
                            "eligible_for_default_build."
                        ),
                        source_id=source_id,
                    )
                )
            continue

        if posture in PUBLIC_SAFE_POSTURES and source_id in profile_defaults:
            public_ids.append(source_id)
        elif posture and posture not in PUBLIC_SAFE_POSTURES and not restricted and not isolated:
            findings.append(
                LicenseFinding(
                    code="unknown-posture",
                    severity=SEVERITY_WARNING,
                    message=f"Source '{source_id}' has uncategorized license posture '{posture}'.",
                    source_id=source_id,
                    detail=posture,
                )
            )

    for source_id in sorted(profile_defaults):
        source = catalog.get(source_id)
        if source is None:
            findings.append(
                LicenseFinding(
                    code="unknown-profile-source",
                    severity=SEVERITY_ERROR,
                    message=f"Profile default source '{source_id}' is not in the catalog.",
                    source_id=source_id,
                )
            )
            continue
        if not source.get("eligible_for_default_build", False):
            findings.append(
                LicenseFinding(
                    code="ineligible-profile-default",
                    severity=SEVERITY_ERROR,
                    message=(
                        f"Profile default source '{source_id}' is not "
                        "eligible_for_default_build."
                    ),
                    source_id=source_id,
                )
            )
        posture = str(source.get("license_posture") or "")
        if posture in PUBLIC_SAFE_POSTURES and source_id not in public_ids:
            public_ids.append(source_id)

    feature_licenses: set[str] = set()
    feature_sources: set[str] = set()
    features_missing_license = 0
    for feature in features:
        properties = feature.get("properties") or {}
        if not isinstance(properties, dict):
            continue
        licenses = _string_list(properties.get("license_lineage"))
        sources = _string_list(properties.get("source_lineage"))
        if not licenses:
            features_missing_license += 1
        for item in licenses:
            feature_licenses.add(item)
            _check_forbidden_lineage(item, "license_lineage", findings)
        for item in sources:
            feature_sources.add(item)
            _check_forbidden_lineage(item, "source_lineage", findings)

    if require_feature_license_lineage and features_missing_license:
        findings.append(
            LicenseFinding(
                code="missing-feature-license-lineage",
                severity=SEVERITY_ERROR,
                message=(
                    f"{features_missing_license} feature(s) lack license_lineage; "
                    "public beta requires license lineage on every exported feature."
                ),
                detail=str(features_missing_license),
            )
        )
    elif features_missing_license:
        findings.append(
            LicenseFinding(
                code="missing-feature-license-lineage",
                severity=SEVERITY_WARNING,
                message=f"{features_missing_license} feature(s) lack license_lineage.",
                detail=str(features_missing_license),
            )
        )

    attribution_records = build_attribution_pack(
        catalog=catalog,
        public_source_ids=public_ids,
        feature_license_lineage=sorted(feature_licenses),
        isolation_notes=isolation_notes,
    )
    if not attribution_records:
        findings.append(
            LicenseFinding(
                code="empty-attribution-pack",
                severity=SEVERITY_ERROR,
                message="Attribution pack is empty; public releases must include notices.",
            )
        )

    if not any(
        record.get("source_id") in public_ids or record.get("required")
        for record in attribution_records
    ):
        findings.append(
            LicenseFinding(
                code="no-required-attribution",
                severity=SEVERITY_WARNING,
                message="No required attribution records were produced for public sources.",
            )
        )

    findings.append(
        LicenseFinding(
            code="isolation-policy-documented",
            severity=SEVERITY_INFO,
            message=(
                "Restricted and share-alike sources are documented for isolation "
                "and excluded from the public beta path."
            ),
        )
    )

    error_findings = [item for item in findings if item.severity == SEVERITY_ERROR]
    result = LicenseAuditResult(
        passed=not error_findings,
        profile_id=profile_id,
        release_channel=release_channel,
        findings=findings,
        catalog_sources=catalog_sources,
        public_source_ids=sorted(set(public_ids)),
        isolated_source_ids=sorted(set(isolated_ids)),
        restricted_source_ids=sorted(set(restricted_ids)),
        feature_license_lineage=sorted(feature_licenses),
        feature_source_lineage=sorted(feature_sources),
        attribution_records=attribution_records,
        isolation_notes=isolation_notes,
    )
    if fail_on_errors and error_findings:
        summary = "; ".join(item.message for item in error_findings[:5])
        extra = f" (+{len(error_findings) - 5} more)" if len(error_findings) > 5 else ""
        raise LicenseAuditError(
            f"License audit failed with {len(error_findings)} error(s): {summary}{extra}"
        )
    return result


def build_attribution_pack(
    *,
    catalog: dict[str, dict[str, Any]],
    public_source_ids: list[str],
    feature_license_lineage: list[str],
    isolation_notes: list[str],
    downstream_outputs: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Build a cleaned attribution pack for public redistribution."""
    downstream = list(downstream_outputs or [])
    records: list[dict[str, Any]] = []
    seen: set[str] = set()

    for source_id in public_source_ids:
        source = catalog.get(source_id) or {}
        key = f"catalog:{source_id}"
        if key in seen:
            continue
        seen.add(key)
        records.append(
            {
                "source_id": source_id,
                "title": source.get("name") or source_id,
                "license": source.get("license") or "unspecified",
                "license_posture": source.get("license_posture"),
                "attribution_text": source.get("attribution_text")
                or source.get("license")
                or source_id,
                "url": source.get("source_url") or "https://example.invalid/",
                "required": True,
                "public_path": True,
                "downstream_outputs": list(downstream),
            }
        )

    # Capture any feature license strings not already covered by catalog titles.
    for license_text in feature_license_lineage:
        lowered = license_text.lower()
        matched_id = None
        for source_id, source in catalog.items():
            name = str(source.get("name") or "").lower()
            if name and name in lowered:
                matched_id = source_id
                break
            if source_id.replace("_", " ") in lowered:
                matched_id = source_id
                break
        key = f"feature:{matched_id or license_text}"
        if key in seen or (matched_id and f"catalog:{matched_id}" in seen):
            continue
        seen.add(key)
        records.append(
            {
                "source_id": matched_id or "derived",
                "title": (catalog.get(matched_id) or {}).get("name")
                if matched_id
                else "Derived feature lineage",
                "license": license_text,
                "attribution_text": license_text,
                "url": (catalog.get(matched_id) or {}).get("source_url")
                or "https://example.invalid/",
                "required": True,
                "public_path": True,
                "downstream_outputs": list(downstream),
            }
        )

    # Explicit isolation notices (not redistributable content, but required
    # documentation that restricted/ODbL paths are not mixed in).
    for note in isolation_notes:
        source_id = note.split(":", 1)[0].strip()
        key = f"isolation:{source_id}"
        if key in seen:
            continue
        seen.add(key)
        source = catalog.get(source_id) or {}
        records.append(
            {
                "source_id": source_id,
                "title": f"{source.get('name') or source_id} (isolated / excluded)",
                "license": source.get("license") or "see catalog",
                "license_posture": source.get("license_posture"),
                "attribution_text": note,
                "url": source.get("source_url") or "https://example.invalid/",
                "required": False,
                "public_path": False,
                "isolation_notice": True,
                "downstream_outputs": [],
            }
        )

    records.sort(key=lambda row: (not row.get("public_path", True), row.get("source_id") or ""))
    return records


def license_audit_markdown(report: dict[str, Any]) -> str:
    """Render a human-readable LICENSE_AUDIT.md body."""
    status = "PASSED" if report.get("passed") else "FAILED"
    lines = [
        "# License audit",
        "",
        f"**Status:** {status}  ",
        f"**Profile:** `{report.get('profile_id')}`  ",
        f"**Channel:** `{report.get('release_channel')}`  ",
        f"**Errors:** {report.get('error_count', 0)} · "
        f"**Warnings:** {report.get('warning_count', 0)}",
        "",
        "## Policy",
        "",
    ]
    for note in (report.get("policy") or {}).get("notes") or []:
        lines.append(f"- {note}")

    lines.extend(
        [
            "",
            "## Public path sources",
            "",
        ]
    )
    public_ids = report.get("public_source_ids") or []
    if public_ids:
        for source_id in public_ids:
            lines.append(f"- `{source_id}`")
    else:
        lines.append("- (none listed)")

    lines.extend(["", "## Isolated / restricted (not in public pack)", ""])
    isolated = list(report.get("isolated_source_ids") or [])
    restricted = list(report.get("restricted_source_ids") or [])
    if isolated or restricted:
        for source_id in sorted(set(isolated + restricted)):
            kind = "restricted" if source_id in restricted else "isolated"
            lines.append(f"- `{source_id}` ({kind})")
    else:
        lines.append("- (none)")

    notes = report.get("isolation_notes") or []
    if notes:
        lines.extend(["", "### Isolation notes", ""])
        for note in notes:
            lines.append(f"- {note}")

    lines.extend(
        [
            "",
            "## Feature lineage observed",
            "",
            "### license_lineage",
            "",
        ]
    )
    for item in report.get("feature_license_lineage") or []:
        lines.append(f"- {item}")
    if not report.get("feature_license_lineage"):
        lines.append("- (none)")
    lines.extend(["", "### source_lineage", ""])
    for item in report.get("feature_source_lineage") or []:
        lines.append(f"- `{item}`")
    if not report.get("feature_source_lineage"):
        lines.append("- (none)")

    lines.extend(["", "## Findings", ""])
    findings = report.get("findings") or []
    if not findings:
        lines.append("- No findings.")
    else:
        for finding in findings:
            severity = str(finding.get("severity", "info")).upper()
            code = finding.get("code", "unknown")
            message = finding.get("message", "")
            lines.append(f"- **{severity}** `{code}`: {message}")

    lines.extend(
        [
            "",
            "## Attribution pack",
            "",
            "See `attribution.json` for machine-readable redistribution notices.",
            "Isolation notices document excluded paths; they are not redistributable layers.",
            "",
        ]
    )
    return "\n".join(lines)


def _check_forbidden_lineage(
    text: str,
    field: str,
    findings: list[LicenseFinding],
) -> None:
    for code, pattern in FORBIDDEN_LINEAGE_PATTERNS:
        if pattern.search(text):
            findings.append(
                LicenseFinding(
                    code=code,
                    severity=SEVERITY_ERROR,
                    message=(
                        f"Forbidden {field} token for public release: {text!r} "
                        f"(matched {code})."
                    ),
                    detail=text,
                )
            )


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, (list, tuple)):
        items: list[str] = []
        for entry in value:
            if isinstance(entry, str) and entry.strip():
                items.append(entry.strip())
        return items
    return []
