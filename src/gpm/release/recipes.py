"""Reproducible generator recipes for public releases."""

from __future__ import annotations

from typing import Any

from gpm import __version__


def modern_scaffold_recipe(
    *,
    profile_id: str,
    scenarios: tuple[str, ...] | list[str] = (),
    include_seas: bool = True,
    include_topology_qa: bool = True,
    population_input: str | None = None,
    settlement_input: str | None = None,
    sample_countries: tuple[str, ...] | list[str] = (),
    release_tag: str | None = None,
) -> dict[str, Any]:
    """Build a machine-readable recipe that reproduces an alpha modern scaffold."""
    scenario_ids = tuple(dict.fromkeys(str(s).strip() for s in scenarios if str(s).strip()))
    countries = tuple(dict.fromkeys(str(c).strip().upper() for c in sample_countries if str(c).strip()))

    steps: list[dict[str, Any]] = [
        {
            "id": "download-sources",
            "title": "Download Natural Earth (and other default) source artifacts",
            "command": [
                "gpm",
                "sources",
                "download",
                "--execute",
                "--profile",
                profile_id,
            ],
            "notes": "Raw data stays under data/raw/ (gitignored). Dry-run omits --execute.",
        },
        {
            "id": "source-manifest",
            "title": "Record downloaded source checksums and metadata",
            "command": [
                "gpm",
                "sources",
                "manifest",
                "--from-raw",
                "--profile",
                profile_id,
            ],
            "notes": "Emit a build source manifest for the release lineage.",
        },
        {
            "id": "build-provinces",
            "title": "Generate modern land province draft",
            "command": _province_command(
                profile_id,
                population_input=population_input,
                settlement_input=settlement_input,
            ),
            "notes": (
                "Writes data/processed/provinces.geojson and intermediate candidates. "
                "Omit population/settlement flags for the unrefined M2/M3 draft."
            ),
        },
    ]
    if include_seas:
        steps.append(
            {
                "id": "build-seas",
                "title": "Generate coastal and ocean sea zones",
                "command": ["gpm", "build", "seas", "--profile", profile_id],
                "notes": "Gameplay-first sea zones; not legal maritime boundaries.",
            }
        )
    steps.append(
        {
            "id": "build-adjacency",
            "title": "Generate land (and marine) adjacency",
            "command": ["gpm", "build", "adjacency", "--profile", profile_id],
            "notes": "Marine edges appear only when sea_zones.geojson is present.",
        }
    )
    if include_topology_qa:
        steps.append(
            {
                "id": "qa-topology",
                "title": "Run topology QA",
                "command": ["gpm", "qa", "topology", "--profile", profile_id],
                "notes": "CI-gating geometry, coverage, and graph checks.",
            }
        )
    for scenario_id in scenario_ids:
        steps.append(
            {
                "id": f"scenario-{scenario_id}",
                "title": f"Resolve scenario ownership overlay: {scenario_id}",
                "command": [
                    "gpm",
                    "scenario",
                    "build",
                    "--scenario",
                    scenario_id,
                    "--profile",
                    profile_id,
                ],
                "notes": "Politics overlay only; does not rewrite province geometry.",
            }
        )

    release_cmd = [
        "gpm",
        "release",
        "alpha",
        "--profile",
        profile_id,
    ]
    for scenario_id in scenario_ids:
        release_cmd.extend(["--scenario", scenario_id])
    for country in countries:
        release_cmd.extend(["--country", country])
    if release_tag:
        release_cmd.extend(["--tag", release_tag])
    steps.append(
        {
            "id": "release-alpha",
            "title": "Package public alpha release bundle",
            "command": release_cmd,
            "notes": (
                "Writes release_manifest.json, ACCURACY.md, recipe files, attribution, "
                "and an embedded game template pack."
            ),
        }
    )

    return {
        "schema_version": "0.1.0",
        "recipe_id": "alpha-modern-scaffold",
        "label": "Public alpha modern scaffold",
        "milestone": "M9",
        "generator_version": __version__,
        "profile_id": profile_id,
        "scenarios": list(scenario_ids),
        "sample_countries": list(countries),
        "include_seas": include_seas,
        "include_topology_qa": include_topology_qa,
        "population_input": population_input,
        "settlement_input": settlement_input,
        "steps": steps,
        "environment": {
            "python": ">=3.11",
            "install": ["uv sync", "uv pip install -e '.[dev]'"],
            "notes": [
                "Run commands from the repository root with the gpm entrypoint available.",
                "Do not commit data/raw/ or full data/processed/ global builds.",
                "Sample subsets may be committed under samples/ when size is modest.",
            ],
        },
    }


def beta_license_audited_recipe(
    *,
    profile_id: str,
    scenarios: tuple[str, ...] | list[str] = (),
    include_seas: bool = True,
    include_topology_qa: bool = True,
    include_scenario_qa: bool = True,
    population_input: str | None = None,
    settlement_input: str | None = None,
    sample_countries: tuple[str, ...] | list[str] = (),
    release_tag: str | None = None,
    include_atlas: bool = True,
) -> dict[str, Any]:
    """Build a machine-readable recipe that reproduces a license-audited beta."""
    scenario_ids = tuple(dict.fromkeys(str(s).strip() for s in scenarios if str(s).strip()))
    countries = tuple(dict.fromkeys(str(c).strip().upper() for c in sample_countries if str(c).strip()))

    steps: list[dict[str, Any]] = [
        {
            "id": "download-sources",
            "title": "Download core (public-safe) source artifacts only",
            "command": [
                "gpm",
                "sources",
                "download",
                "--execute",
                "--profile",
                profile_id,
            ],
            "notes": (
                "Uses profile defaults. Restricted (GADM) and share-alike (OSM) sources "
                "are not on the default path and must stay isolated."
            ),
        },
        {
            "id": "source-manifest",
            "title": "Record downloaded source checksums and metadata",
            "command": [
                "gpm",
                "sources",
                "manifest",
                "--from-raw",
                "--profile",
                profile_id,
            ],
            "notes": "Emit a build source manifest for the release lineage.",
        },
        {
            "id": "build-provinces",
            "title": "Generate modern land province draft",
            "command": _province_command(
                profile_id,
                population_input=population_input,
                settlement_input=settlement_input,
            ),
            "notes": (
                "Writes data/processed/provinces.geojson. Features must carry "
                "license_lineage for the beta license audit."
            ),
        },
    ]
    if include_seas:
        steps.append(
            {
                "id": "build-seas",
                "title": "Generate coastal and ocean sea zones",
                "command": ["gpm", "build", "seas", "--profile", profile_id],
                "notes": "Gameplay-first sea zones; not legal maritime boundaries.",
            }
        )
    steps.append(
        {
            "id": "build-adjacency",
            "title": "Generate land (and marine) adjacency",
            "command": ["gpm", "build", "adjacency", "--profile", profile_id],
            "notes": "Marine edges appear only when sea_zones.geojson is present.",
        }
    )
    if include_topology_qa:
        steps.append(
            {
                "id": "qa-topology",
                "title": "Run topology QA",
                "command": ["gpm", "qa", "topology", "--profile", profile_id],
                "notes": "CI-gating geometry, coverage, and graph checks.",
            }
        )
    for scenario_id in scenario_ids:
        steps.append(
            {
                "id": f"scenario-{scenario_id}",
                "title": f"Resolve scenario ownership overlay: {scenario_id}",
                "command": [
                    "gpm",
                    "scenario",
                    "build",
                    "--scenario",
                    scenario_id,
                    "--profile",
                    profile_id,
                ],
                "notes": "Politics overlay only; does not rewrite province geometry.",
            }
        )
        if include_scenario_qa and scenario_id.startswith("official-"):
            steps.append(
                {
                    "id": f"qa-scenario-{scenario_id}",
                    "title": f"Run politics QA for {scenario_id}",
                    "command": [
                        "gpm",
                        "qa",
                        "scenario",
                        "--scenario",
                        scenario_id,
                        "--profile",
                        profile_id,
                    ],
                    "notes": "Coverage, tag, component, and golden-floor checks.",
                }
            )

    release_cmd = [
        "gpm",
        "release",
        "beta",
        "--profile",
        profile_id,
    ]
    for scenario_id in scenario_ids:
        release_cmd.extend(["--scenario", scenario_id])
    for country in countries:
        release_cmd.extend(["--country", country])
    if release_tag:
        release_cmd.extend(["--tag", release_tag])
    if not include_atlas:
        release_cmd.append("--no-atlas")
    steps.append(
        {
            "id": "release-beta",
            "title": "Package license-audited beta (game + atlas faces)",
            "command": release_cmd,
            "notes": (
                "Writes release_manifest.json, LICENSE_AUDIT.md, attribution pack, "
                "ACCURACY.md, recipe files, game pack/, and optional atlas/."
            ),
        }
    )

    return {
        "schema_version": "0.1.0",
        "recipe_id": "beta-license-audited",
        "label": "Public beta license-audited dual-face release",
        "milestone": "M14",
        "generator_version": __version__,
        "profile_id": profile_id,
        "scenarios": list(scenario_ids),
        "sample_countries": list(countries),
        "include_seas": include_seas,
        "include_topology_qa": include_topology_qa,
        "include_atlas": include_atlas,
        "population_input": population_input,
        "settlement_input": settlement_input,
        "steps": steps,
        "environment": {
            "python": ">=3.11",
            "install": ["uv sync", "uv pip install -e '.[dev]'"],
            "notes": [
                "Run commands from the repository root with the gpm entrypoint available.",
                "Do not mix ODbL or restricted sources into public beta packs.",
                "Do not commit data/raw/ or full data/processed/ global builds.",
                "Sample subsets may be committed under samples/ when size is modest.",
            ],
        },
    }


def recipe_markdown(recipe: dict[str, Any]) -> str:
    """Render a recipe document as a shell-oriented markdown guide."""
    lines = [
        f"# Recipe: {recipe.get('label') or recipe.get('recipe_id')}",
        "",
        f"Recipe id: `{recipe.get('recipe_id')}`  ",
        f"Profile: `{recipe.get('profile_id')}`  ",
        f"Milestone: `{recipe.get('milestone')}`  ",
        f"Generator version: `{recipe.get('generator_version')}`",
        "",
        "## Environment",
        "",
    ]
    env = recipe.get("environment") or {}
    for install in env.get("install") or []:
        lines.append(f"```bash\n{install}\n```")
        lines.append("")
    for note in env.get("notes") or []:
        lines.append(f"- {note}")
    lines.extend(["", "## Steps", ""])
    for index, step in enumerate(recipe.get("steps") or [], start=1):
        title = step.get("title") or step.get("id") or f"step-{index}"
        command = step.get("command") or []
        cmd_str = " ".join(str(part) for part in command)
        lines.append(f"### {index}. {title}")
        lines.append("")
        if step.get("notes"):
            lines.append(str(step["notes"]))
            lines.append("")
        lines.append("```bash")
        lines.append(f"uv run {cmd_str}" if not cmd_str.startswith("uv ") else cmd_str)
        lines.append("```")
        lines.append("")
    return "\n".join(lines)


def _province_command(
    profile_id: str,
    *,
    population_input: str | None,
    settlement_input: str | None,
) -> list[str]:
    command = ["gpm", "build", "provinces", "--profile", profile_id]
    if population_input:
        command.extend(["--population-input", population_input])
    if settlement_input:
        command.extend(["--settlement-input", settlement_input])
    return command
