from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from .paths import CONFIG_DIR, PROFILE_DIR


DEFAULT_PROFILE_ID = "modern-small"


class ConfigError(ValueError):
    """Raised when a generation profile or source catalog is malformed."""


def load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as file:
        return tomllib.load(file)


def list_profile_paths() -> list[Path]:
    return sorted(PROFILE_DIR.glob("*.toml"))


def list_profile_ids() -> list[str]:
    return [path.stem for path in list_profile_paths()]


def load_profile(profile_id: str = DEFAULT_PROFILE_ID) -> dict[str, Any]:
    path = PROFILE_DIR / f"{profile_id}.toml"
    if not path.exists():
        available = ", ".join(list_profile_ids()) or "none"
        raise ConfigError(f"Unknown profile '{profile_id}'. Available profiles: {available}.")
    profile = load_toml(path)
    actual_id = profile.get("profile", {}).get("id")
    if actual_id != profile_id:
        raise ConfigError(f"Profile id mismatch in {path}: expected '{profile_id}', found '{actual_id}'.")
    return profile


def load_source_catalog() -> dict[str, dict[str, Any]]:
    catalog_path = CONFIG_DIR / "sources.toml"
    catalog = load_toml(catalog_path)
    sources = catalog.get("sources")
    if not isinstance(sources, dict) or not sources:
        raise ConfigError(f"Source catalog at {catalog_path} must define a non-empty [sources] table.")
    return sources


def default_source_ids(profile: dict[str, Any]) -> list[str]:
    sources = profile.get("sources", {})
    defaults = sources.get("default", [])
    if not isinstance(defaults, list):
        raise ConfigError("Profile sources.default must be a list.")
    return list(defaults)


def excluded_source_ids(profile: dict[str, Any]) -> list[str]:
    sources = profile.get("sources", {})
    excluded = sources.get("excluded", [])
    if not isinstance(excluded, list):
        raise ConfigError("Profile sources.excluded must be a list.")
    return list(excluded)
