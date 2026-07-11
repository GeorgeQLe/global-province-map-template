"""M16 multi-era geometry + politics packs with quality tiers and migration notes."""

from gpm.multi_era.build import (
    MultiEraBuildResult,
    MultiEraError,
    build_multi_era_pack,
)
from gpm.multi_era.migration import (
    build_migration_document,
    migration_markdown,
)
from gpm.multi_era.packs import (
    MultiEraPackError,
    MultiEraPackSummary,
    list_multi_era_packs,
    load_multi_era_pack,
    validate_multi_era_pack,
)

__all__ = [
    "MultiEraBuildResult",
    "MultiEraError",
    "MultiEraPackError",
    "MultiEraPackSummary",
    "build_migration_document",
    "build_multi_era_pack",
    "list_multi_era_packs",
    "load_multi_era_pack",
    "migration_markdown",
    "validate_multi_era_pack",
]
