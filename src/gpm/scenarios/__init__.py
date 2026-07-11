"""M8 historical scenario ownership overlays over modern geography."""

from .authoring import (
    ScenarioOverrideWriteResult,
    apply_province_override,
    list_province_overrides,
    remove_province_override,
)
from .resolve import (
    ScenarioError,
    ScenarioBuildResult,
    ScenarioSummary,
    build_scenario_ownership,
    list_scenarios,
    load_scenario,
    resolve_ownership_records,
    validate_scenario_document,
)

__all__ = [
    "ScenarioError",
    "ScenarioBuildResult",
    "ScenarioSummary",
    "ScenarioOverrideWriteResult",
    "apply_province_override",
    "build_scenario_ownership",
    "list_province_overrides",
    "list_scenarios",
    "load_scenario",
    "remove_province_override",
    "resolve_ownership_records",
    "validate_scenario_document",
]
