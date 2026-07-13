from __future__ import annotations

import tomllib
import math
from pathlib import Path
from typing import Any

from .paths import CONFIG_DIR, PROFILE_DIR


DEFAULT_PROFILE_ID = "modern-small"
QA_THRESHOLD_KEYS = (
    "max_overlap_area_sq_km",
    "max_gap_component_area_sq_km",
    "min_shared_border_km",
)
REFINEMENT_KEYS = (
    "population_weight",
    "min_area_sq_km",
    "min_population",
    "max_split_parts",
    "max_seed_candidates",
)
SEA_SETTING_KEYS = (
    "coastal_buffer_km",
    "ocean_cell_size_deg",
    "strait_max_distance_km",
    "min_sea_area_sq_km",
    "min_shared_border_km",
)
HIERARCHY_SETTING_KEYS = (
    "area_target_size",
    "area_min_size",
    "area_max_size",
    "mega_region_area_threshold",
    "mega_region_min_area_sq_km",
    "region_target_size",
)
# M21 hierarchy defaults; profiles override under [hierarchy].
# Mega-country region splits require BOTH enough areas and a continental-scale
# footprint, so municipality-dense micro-states (Malta, North Macedonia) stay
# single regions while USA/RUS/CHN/IND split by the NE admin-1 region attribute.
DEFAULT_HIERARCHY_SETTINGS: dict[str, int] = {
    "area_target_size": 8,
    "area_min_size": 3,
    "area_max_size": 15,
    "mega_region_area_threshold": 4,
    "mega_region_min_area_sq_km": 2_000_000,
    "region_target_size": 10,
}
EXPORT_SETTING_KEYS = (
    "layout",
    "region_type",
    "include_sea_zones",
    "include_geometry",
    "definition_format",
    "localization_language",
)
# Profile export pack layouts. Optional [export] keys override the preset.
EXPORT_LAYOUT_PRESETS: dict[str, dict[str, Any]] = {
    "generic": {
        "region_type": "region",
        "include_sea_zones": True,
        "include_geometry": True,
        "definition_format": "json",
        "localization_language": "english",
    },
    "eu-like": {
        "region_type": "region",
        "include_sea_zones": True,
        "include_geometry": True,
        "definition_format": "json",
        "localization_language": "english",
    },
    "victoria-like": {
        "region_type": "state",
        "include_sea_zones": True,
        "include_geometry": True,
        "definition_format": "json",
        "localization_language": "english",
    },
    "hoi-like": {
        "region_type": "strategic_region",
        "include_sea_zones": True,
        "include_geometry": True,
        "definition_format": "json",
        "localization_language": "english",
    },
}
REGION_TYPES = frozenset({"state", "region", "strategic_region", "superregion"})
DEFINITION_FORMATS = frozenset({"json", "csv"})
# Gameplay-first strategy presets. Profiles may override values under [sea].
SEA_ZONE_STRATEGY_PRESETS: dict[str, dict[str, float]] = {
    "simple-coastal-and-ocean": {
        "coastal_buffer_km": 150.0,
        "ocean_cell_size_deg": 45.0,
        "strait_max_distance_km": 40.0,
        "min_sea_area_sq_km": 250.0,
        "min_shared_border_km": 0.01,
    },
    "coast-aware": {
        "coastal_buffer_km": 100.0,
        "ocean_cell_size_deg": 30.0,
        "strait_max_distance_km": 30.0,
        "min_sea_area_sq_km": 100.0,
        "min_shared_border_km": 0.01,
    },
    "trade-coasts-and-oceans": {
        "coastal_buffer_km": 120.0,
        "ocean_cell_size_deg": 40.0,
        "strait_max_distance_km": 50.0,
        "min_sea_area_sq_km": 150.0,
        "min_shared_border_km": 0.01,
    },
    "strategic-seas-and-chokepoints": {
        "coastal_buffer_km": 100.0,
        "ocean_cell_size_deg": 25.0,
        "strait_max_distance_km": 80.0,
        "min_sea_area_sq_km": 100.0,
        "min_shared_border_km": 0.01,
    },
    "dense-coastal-seas-and-straits": {
        "coastal_buffer_km": 75.0,
        "ocean_cell_size_deg": 20.0,
        "strait_max_distance_km": 60.0,
        "min_sea_area_sq_km": 50.0,
        "min_shared_border_km": 0.01,
    },
}


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


def qa_thresholds(profile: dict[str, Any]) -> dict[str, float]:
    qa = profile.get("qa")
    if not isinstance(qa, dict):
        raise ConfigError("Profile must define a [qa] table.")
    thresholds: dict[str, float] = {}
    for key in QA_THRESHOLD_KEYS:
        value = qa.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ConfigError(f"Profile qa.{key} must be a positive number.")
        parsed = float(value)
        if not math.isfinite(parsed) or parsed <= 0:
            raise ConfigError(f"Profile qa.{key} must be a positive number.")
        thresholds[key] = parsed
    return thresholds


def province_refinement_settings(
    profile: dict[str, Any],
    *,
    target_province_count: int | None = None,
) -> dict[str, int | float]:
    refinement = profile.get("refinement")
    if not isinstance(refinement, dict):
        raise ConfigError("Profile must define a [refinement] table.")
    generation = profile.get("generation")
    if not isinstance(generation, dict):
        raise ConfigError("Profile must define a [generation] table.")
    configured_target = generation.get("target_province_count")
    target = configured_target if target_province_count is None else target_province_count
    if isinstance(target, bool) or not isinstance(target, int) or target <= 0:
        raise ConfigError("Refinement target_province_count must be a positive integer.")

    missing = [key for key in REFINEMENT_KEYS if key not in refinement]
    if missing:
        raise ConfigError(f"Profile refinement missing key(s): {', '.join(missing)}.")
    population_weight = _finite_number(refinement["population_weight"], "refinement.population_weight")
    min_area = _finite_number(refinement["min_area_sq_km"], "refinement.min_area_sq_km")
    min_population = _finite_number(refinement["min_population"], "refinement.min_population")
    if not 0 <= population_weight <= 1:
        raise ConfigError("Profile refinement.population_weight must be between 0 and 1.")
    if min_area < 0 or min_population < 0:
        raise ConfigError("Profile refinement minimum area and population cannot be negative.")

    max_split_parts = refinement["max_split_parts"]
    max_seed_candidates = refinement["max_seed_candidates"]
    for key, value in (
        ("max_split_parts", max_split_parts),
        ("max_seed_candidates", max_seed_candidates),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ConfigError(f"Profile refinement.{key} must be a positive integer.")
    if max_seed_candidates < max_split_parts:
        raise ConfigError(
            "Profile refinement.max_seed_candidates must be at least refinement.max_split_parts."
        )
    return {
        "target_province_count": target,
        "population_weight": population_weight,
        "min_area_sq_km": min_area,
        "min_population": min_population,
        "max_split_parts": max_split_parts,
        "max_seed_candidates": max_seed_candidates,
    }


def sea_zone_settings(profile: dict[str, Any]) -> dict[str, float | str]:
    """Resolve M6 sea-zone parameters from generation.sea_zone_strategy and optional [sea]."""
    generation = profile.get("generation")
    if not isinstance(generation, dict):
        raise ConfigError("Profile must define a [generation] table.")
    strategy = generation.get("sea_zone_strategy")
    if not isinstance(strategy, str) or not strategy.strip():
        raise ConfigError("Profile generation.sea_zone_strategy must be a non-empty string.")
    strategy = strategy.strip()
    if strategy not in SEA_ZONE_STRATEGY_PRESETS:
        known = ", ".join(sorted(SEA_ZONE_STRATEGY_PRESETS))
        raise ConfigError(
            f"Unknown sea_zone_strategy '{strategy}'. Known strategies: {known}."
        )
    settings: dict[str, float] = dict(SEA_ZONE_STRATEGY_PRESETS[strategy])
    overrides = profile.get("sea")
    if overrides is not None:
        if not isinstance(overrides, dict):
            raise ConfigError("Profile [sea] table must be a mapping when present.")
        for key in SEA_SETTING_KEYS:
            if key not in overrides:
                continue
            value = _finite_number(overrides[key], f"sea.{key}")
            if value <= 0:
                raise ConfigError(f"Profile sea.{key} must be a positive number.")
            settings[key] = value
    return {
        "strategy": strategy,
        "coastal_buffer_km": settings["coastal_buffer_km"],
        "ocean_cell_size_deg": settings["ocean_cell_size_deg"],
        "strait_max_distance_km": settings["strait_max_distance_km"],
        "min_sea_area_sq_km": settings["min_sea_area_sq_km"],
        "min_shared_border_km": settings["min_shared_border_km"],
    }


def hierarchy_settings(profile: dict[str, Any]) -> dict[str, int]:
    """Resolve M21 hierarchy parameters from the optional [hierarchy] table."""
    overrides = profile.get("hierarchy")
    settings = dict(DEFAULT_HIERARCHY_SETTINGS)
    if overrides is not None:
        if not isinstance(overrides, dict):
            raise ConfigError("Profile [hierarchy] table must be a mapping when present.")
        for key in HIERARCHY_SETTING_KEYS:
            if key not in overrides:
                continue
            value = overrides[key]
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ConfigError(f"Profile hierarchy.{key} must be a positive integer.")
            settings[key] = value
    if not settings["area_min_size"] <= settings["area_target_size"] <= settings["area_max_size"]:
        raise ConfigError(
            "Profile hierarchy sizes must satisfy area_min_size <= area_target_size <= area_max_size."
        )
    return settings


def export_settings(profile: dict[str, Any]) -> dict[str, Any]:
    """Resolve M7 export pack parameters from optional [export] and layout preset."""
    profile_meta = profile.get("profile")
    if not isinstance(profile_meta, dict):
        raise ConfigError("Profile must define a [profile] table.")
    profile_id = profile_meta.get("id")
    if not isinstance(profile_id, str) or not profile_id.strip():
        raise ConfigError("Profile profile.id must be a non-empty string.")

    overrides = profile.get("export")
    if overrides is None:
        overrides = {}
    if not isinstance(overrides, dict):
        raise ConfigError("Profile [export] table must be a mapping when present.")

    layout = overrides.get("layout")
    if layout is None:
        layout = profile_id if profile_id in EXPORT_LAYOUT_PRESETS else "generic"
    if not isinstance(layout, str) or not layout.strip():
        raise ConfigError("Profile export.layout must be a non-empty string.")
    layout = layout.strip()
    if layout not in EXPORT_LAYOUT_PRESETS:
        known = ", ".join(sorted(EXPORT_LAYOUT_PRESETS))
        raise ConfigError(f"Unknown export.layout '{layout}'. Known layouts: {known}.")

    settings: dict[str, Any] = dict(EXPORT_LAYOUT_PRESETS[layout])
    settings["layout"] = layout

    if "region_type" in overrides:
        region_type = overrides["region_type"]
        if not isinstance(region_type, str) or region_type not in REGION_TYPES:
            known = ", ".join(sorted(REGION_TYPES))
            raise ConfigError(f"Profile export.region_type must be one of: {known}.")
        settings["region_type"] = region_type

    for bool_key in ("include_sea_zones", "include_geometry"):
        if bool_key in overrides:
            value = overrides[bool_key]
            if not isinstance(value, bool):
                raise ConfigError(f"Profile export.{bool_key} must be a boolean.")
            settings[bool_key] = value

    if "definition_format" in overrides:
        definition_format = overrides["definition_format"]
        if not isinstance(definition_format, str) or definition_format not in DEFINITION_FORMATS:
            known = ", ".join(sorted(DEFINITION_FORMATS))
            raise ConfigError(f"Profile export.definition_format must be one of: {known}.")
        settings["definition_format"] = definition_format

    if "localization_language" in overrides:
        language = overrides["localization_language"]
        if not isinstance(language, str) or not language.strip():
            raise ConfigError("Profile export.localization_language must be a non-empty string.")
        settings["localization_language"] = language.strip().lower()

    return settings


def _finite_number(value: Any, path: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigError(f"Profile {path} must be a finite number.")
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ConfigError(f"Profile {path} must be a finite number.")
    return parsed
