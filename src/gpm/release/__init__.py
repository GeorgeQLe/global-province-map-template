"""Public release packaging, accuracy labeling, and license audit."""

from gpm.release.alpha import (
    DEFAULT_ALPHA_SCENARIOS,
    DEFAULT_SAMPLE_COUNTRIES,
    AlphaReleaseResult,
    ReleaseError,
    build_alpha_release,
)
from gpm.release.beta import (
    BETA_GEOMETRY_TIER,
    DEFAULT_BETA_SCENARIOS,
    BetaReleaseResult,
    build_beta_release,
)
from gpm.release.demo import (
    DEMO_SCENARIOS,
    DemoBuildError,
    DemoBuildResult,
    build_demo,
)
from gpm.release.license_audit import (
    LicenseAuditError,
    LicenseAuditResult,
    audit_public_release,
    build_attribution_pack,
    license_audit_markdown,
)
from gpm.release.quality import (
    ALPHA_GEOMETRY_TIER,
    ALPHA_POLITICS_TIER,
    QUALITY_TIER_CURATED_POLITICS,
    QUALITY_TIER_PERIOD_GEOMETRY,
    QUALITY_TIER_SCAFFOLD_BASELINE,
    QUALITY_TIERS,
    accuracy_label,
    accuracy_markdown,
)
from gpm.release.recipes import (
    beta_license_audited_recipe,
    modern_scaffold_recipe,
    recipe_markdown,
)
from gpm.release.site import (
    LANDING_DIR_NAME,
    REQUIRED_DEMO_FILES,
    REQUIRED_DEMO_HTML_SNIPPETS,
    REQUIRED_HTML_SNIPPETS,
    REQUIRED_LANDING_FILES,
    LandingValidationResult,
    SiteReleaseResult,
    default_landing_dir,
    release_landing_site,
    validate_landing_site,
)

# Beta reuses the same Western Europe sample country convenience set.
DEFAULT_BETA_SAMPLE_COUNTRIES = DEFAULT_SAMPLE_COUNTRIES

__all__ = [
    "ALPHA_GEOMETRY_TIER",
    "ALPHA_POLITICS_TIER",
    "BETA_GEOMETRY_TIER",
    "AlphaReleaseResult",
    "BetaReleaseResult",
    "DEFAULT_ALPHA_SCENARIOS",
    "DEFAULT_BETA_SCENARIOS",
    "DEFAULT_BETA_SAMPLE_COUNTRIES",
    "DEFAULT_SAMPLE_COUNTRIES",
    "DEMO_SCENARIOS",
    "DemoBuildError",
    "DemoBuildResult",
    "LANDING_DIR_NAME",
    "LicenseAuditError",
    "LicenseAuditResult",
    "LandingValidationResult",
    "QUALITY_TIER_CURATED_POLITICS",
    "QUALITY_TIER_PERIOD_GEOMETRY",
    "QUALITY_TIER_SCAFFOLD_BASELINE",
    "QUALITY_TIERS",
    "REQUIRED_DEMO_FILES",
    "REQUIRED_DEMO_HTML_SNIPPETS",
    "REQUIRED_HTML_SNIPPETS",
    "REQUIRED_LANDING_FILES",
    "ReleaseError",
    "SiteReleaseResult",
    "accuracy_label",
    "accuracy_markdown",
    "audit_public_release",
    "beta_license_audited_recipe",
    "build_alpha_release",
    "build_demo",
    "build_attribution_pack",
    "build_beta_release",
    "default_landing_dir",
    "license_audit_markdown",
    "modern_scaffold_recipe",
    "recipe_markdown",
    "release_landing_site",
    "validate_landing_site",
]
