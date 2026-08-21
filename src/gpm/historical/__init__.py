"""Executable research fixtures for historical representation contracts."""

from .casebook import (
    CasebookError,
    execute_casebook,
    load_casebook,
    project_fixture_runtime,
)
from .territorial_status import (
    TerritorialStatusOverlayError,
    load_territorial_status_overlay,
    resolve_territorial_status,
    resolved_territory_state,
    validate_territorial_status_overlay,
)

__all__ = [
    "CasebookError",
    "execute_casebook",
    "load_casebook",
    "project_fixture_runtime",
    "TerritorialStatusOverlayError",
    "load_territorial_status_overlay",
    "resolve_territorial_status",
    "resolved_territory_state",
    "validate_territorial_status_overlay",
]
