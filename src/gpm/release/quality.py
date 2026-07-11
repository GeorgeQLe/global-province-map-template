"""Honest accuracy labeling and quality tiers for public releases.

Quality tiers (from ROADMAP Phase 6 / Phase 10):

- scaffold-baseline — modern parent projection only; not curated history
- curated-politics — human-reviewed tags for priority regions / global tags
- period-geometry — era-aware shapes where modern scaffold fails the sniff test
"""

from __future__ import annotations

from typing import Any

# Canonical tier ids. Prefer these strings in manifests and docs.
QUALITY_TIER_SCAFFOLD_BASELINE = "scaffold-baseline"
QUALITY_TIER_CURATED_POLITICS = "curated-politics"
QUALITY_TIER_PERIOD_GEOMETRY = "period-geometry"

QUALITY_TIERS: tuple[str, ...] = (
    QUALITY_TIER_SCAFFOLD_BASELINE,
    QUALITY_TIER_CURATED_POLITICS,
    QUALITY_TIER_PERIOD_GEOMETRY,
)

TIER_DESCRIPTIONS: dict[str, str] = {
    QUALITY_TIER_SCAFFOLD_BASELINE: (
        "Modern open-geodata scaffold only. Politics project modern "
        "parent_country_id (or coarse demo remaps). Not a claim of historical "
        "accuracy for any pre-modern or wartime era."
    ),
    QUALITY_TIER_CURATED_POLITICS: (
        "Human-reviewed owner/controller/cores/claims for priority regions "
        "and/or global major tags. Geometry may still be modern scaffold."
    ),
    QUALITY_TIER_PERIOD_GEOMETRY: (
        "Era-aware province shapes or boundary hints where modern admin "
        "outlines would fail a historian or Paradox-eye sniff test."
    ),
}

# Public alpha ships only scaffold-baseline for both geometry and politics.
ALPHA_GEOMETRY_TIER = QUALITY_TIER_SCAFFOLD_BASELINE
ALPHA_POLITICS_TIER = QUALITY_TIER_SCAFFOLD_BASELINE


def accuracy_label(
    *,
    geometry_tier: str = ALPHA_GEOMETRY_TIER,
    politics_tier: str = ALPHA_POLITICS_TIER,
    scenarios: tuple[str, ...] | list[str] = (),
    profile_id: str | None = None,
    release_channel: str = "alpha",
) -> dict[str, Any]:
    """Machine-readable accuracy label for a release bundle."""
    _validate_tier(geometry_tier, "geometry_tier")
    _validate_tier(politics_tier, "politics_tier")
    scenario_ids = tuple(dict.fromkeys(str(s).strip() for s in scenarios if str(s).strip()))

    scenario_notes: list[str] = []
    includes_official_eras: list[str] = []
    for scenario_id in scenario_ids:
        if scenario_id == "modern-baseline":
            scenario_notes.append(
                "modern-baseline: projects each land province's modern "
                "parent_country_id to owner/controller. Scaffold only."
            )
        elif scenario_id == "demo-1444":
            scenario_notes.append(
                "demo-1444: coarse country/region remaps for tooling demos. "
                "Not curated 1444 politics; prefer official-1444 for product claims."
            )
        elif scenario_id == "official-1836":
            includes_official_eras.append("official-1836")
            scenario_notes.append(
                "official-1836: curated-politics 1836 ownership overlay with "
                "elevated Europe / North America / colonial theater depth. "
                "Geometry remains modern scaffold; not Paradox-grade completeness."
            )
        elif scenario_id == "official-1444":
            includes_official_eras.append("official-1444")
            scenario_notes.append(
                "official-1444: curated-politics 1444 ownership overlay with "
                "Europe-first elevated depth (HRE, Italy, Iberia, France/Burgundy, "
                "British Isles, east Europe) plus global major tags. "
                "Geometry remains modern scaffold; not Paradox-grade completeness."
            )
        else:
            scenario_notes.append(
                f"{scenario_id}: treat as uncurated overlay unless separately "
                "labeled curated-politics or higher."
            )

    do_not_claim = [
        "Paradox-grade historical accuracy",
        "period-correct province geometry worldwide",
        "legal maritime boundaries (sea zones are gameplay abstractions)",
        "complete population fidelity without documented raster inputs",
    ]
    if politics_tier == QUALITY_TIER_SCAFFOLD_BASELINE:
        do_not_claim.append("curated official 1444 / 1836 / 1936 politics")
        do_not_claim.append("production-ready historical start-date tags")
    elif politics_tier == QUALITY_TIER_CURATED_POLITICS:
        do_not_claim.append(
            "complete global historical politics outside priority theaters"
        )
        missing_official = [
            era
            for era in ("1444", "1836", "1936")
            if f"official-{era}" not in includes_official_eras
        ]
        if missing_official:
            do_not_claim.append(
                "curated official "
                + " / ".join(missing_official)
                + " politics"
                + (
                    f" ({', '.join(includes_official_eras)} included)"
                    if includes_official_eras
                    else ""
                )
            )
    if geometry_tier == QUALITY_TIER_SCAFFOLD_BASELINE:
        do_not_claim.append("era-aware borders for pre-modern or wartime maps")

    summary = (
        f"{release_channel.capitalize()} release: geometry={geometry_tier}, "
        f"politics={politics_tier}. Modern open-geodata scaffold is the "
        "engineering foundation—not a final claim of historical truth."
    )
    if profile_id:
        summary = f"Profile `{profile_id}`. " + summary

    honest_statements = [
        "Province polygons come from modern Natural Earth (and optional "
        "admin candidates), not from proprietary game maps.",
        "Scenario ownership is a separate layer; geometry is not rewritten "
        "per era unless a period-geometry tier is claimed.",
        "Redistribute with attribution.json and the release manifest.",
    ]
    if includes_official_eras:
        eras = ", ".join(includes_official_eras)
        honest_statements.insert(
            2,
            f"{eras}: curated-politics era program(s)—major-power tags and "
            "priority theaters are human-reviewed overlays, not period geometry.",
        )
    else:
        honest_statements.insert(
            2,
            "demo remaps and baseline projection are scaffolding tools, not "
            "official era programs (see official-1444 / official-1836 for "
            "curated eras).",
        )

    return {
        "schema_version": "0.1.0",
        "release_channel": release_channel,
        "geometry_quality_tier": geometry_tier,
        "politics_quality_tier": politics_tier,
        "geometry_quality_description": TIER_DESCRIPTIONS[geometry_tier],
        "politics_quality_description": TIER_DESCRIPTIONS[politics_tier],
        "summary": summary,
        "scenario_notes": scenario_notes,
        "honest_statements": honest_statements,
        "do_not_claim": do_not_claim,
        "quality_tier_catalog": [
            {"id": tier, "description": TIER_DESCRIPTIONS[tier]} for tier in QUALITY_TIERS
        ],
    }


def accuracy_markdown(label: dict[str, Any]) -> str:
    """Human-readable ACCURACY.md body from an accuracy label document."""
    lines = [
        "# Accuracy label",
        "",
        label["summary"],
        "",
        "## Quality tiers",
        "",
        f"| Layer | Tier |",
        f"| --- | --- |",
        f"| Geometry | `{label['geometry_quality_tier']}` |",
        f"| Politics | `{label['politics_quality_tier']}` |",
        "",
        f"**Geometry:** {label['geometry_quality_description']}",
        "",
        f"**Politics:** {label['politics_quality_description']}",
        "",
        "## Honest statements",
        "",
    ]
    for item in label.get("honest_statements") or []:
        lines.append(f"- {item}")
    lines.extend(["", "## Do not claim", ""])
    for item in label.get("do_not_claim") or []:
        lines.append(f"- {item}")
    scenario_notes = label.get("scenario_notes") or []
    if scenario_notes:
        lines.extend(["", "## Scenario notes", ""])
        for note in scenario_notes:
            lines.append(f"- {note}")
    lines.extend(
        [
            "",
            "## Catalog",
            "",
            "Official product tiers (progressive fidelity):",
            "",
        ]
    )
    for entry in label.get("quality_tier_catalog") or []:
        lines.append(f"- `{entry['id']}` — {entry['description']}")
    lines.append("")
    return "\n".join(lines)


def _validate_tier(value: str, field: str) -> None:
    if value not in QUALITY_TIERS:
        allowed = ", ".join(QUALITY_TIERS)
        raise ValueError(f"{field} must be one of: {allowed} (got {value!r})")
