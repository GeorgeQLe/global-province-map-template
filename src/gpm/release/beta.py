"""M14 license-audited beta release packaging (game + atlas faces)."""

from __future__ import annotations

import shutil
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from gpm import __version__
from gpm.config import ConfigError, load_profile
from gpm.exporters.atlas import export_atlas_pack
from gpm.exporters.pack import ExportError, export_game_pack
from gpm.paths import PROCESSED_DATA_DIR, PROJECT_ROOT
from gpm.release.alpha import ReleaseError, _prepare_inputs, _write_json
from gpm.release.license_audit import (
    LicenseAuditError,
    audit_public_release,
    license_audit_markdown,
)
from gpm.release.quality import (
    QUALITY_TIER_CURATED_POLITICS,
    QUALITY_TIER_SCAFFOLD_BASELINE,
    accuracy_label,
    accuracy_markdown,
)
from gpm.release.recipes import beta_license_audited_recipe, recipe_markdown
from gpm.release.sample import SampleError, load_feature_collection

DEFAULT_BETA_SCENARIOS: tuple[str, ...] = (
    "modern-baseline",
    "official-1836",
    "official-1444",
)
DEFAULT_SAMPLE_COUNTRIES: tuple[str, ...] = ("FRA", "BEL", "NLD", "LUX", "DEU")
BETA_GEOMETRY_TIER = QUALITY_TIER_SCAFFOLD_BASELINE


@dataclass(frozen=True)
class BetaReleaseResult:
    release_tag: str
    profile_id: str
    output_dir: str
    release_manifest: str
    pack_dir: str
    atlas_dir: str
    province_count: int
    sea_zone_count: int
    adjacency_count: int
    scenario_ids: tuple[str, ...]
    sample_countries: tuple[str, ...]
    geometry_quality_tier: str
    politics_quality_tier: str
    is_sample: bool
    license_audit_passed: bool
    attribution_record_count: int
    files_written: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_beta_release(
    profile_id: str = "modern-small",
    *,
    province_input: Path = PROCESSED_DATA_DIR / "provinces.geojson",
    sea_input: Path | None = None,
    adjacency_input: Path | None = None,
    output_dir: Path | None = None,
    release_tag: str | None = None,
    scenarios: tuple[str, ...] | list[str] = DEFAULT_BETA_SCENARIOS,
    sample_countries: tuple[str, ...] | list[str] | None = None,
    allow_unknown_overrides: bool = False,
    include_topology_qa_copy: bool = True,
    topology_qa_input: Path | None = None,
    data_vintage: str | None = None,
    include_atlas: bool = True,
    fail_on_license_errors: bool = True,
) -> BetaReleaseResult:
    """Package a license-audited public beta: game pack + atlas + audit + attribution.

    When *sample_countries* is non-empty, province/sea/adjacency inputs are
    filtered to those modern ISO codes before packaging.
    """
    try:
        load_profile(profile_id)
    except ConfigError as exc:
        raise ReleaseError(str(exc)) from exc

    if not province_input.is_file():
        raise ReleaseError(f"Province input does not exist: {province_input}")

    scenario_ids = tuple(dict.fromkeys(str(s).strip() for s in scenarios if str(s).strip()))
    countries = tuple(
        dict.fromkeys(
            str(c).strip().upper()
            for c in (sample_countries or ())
            if str(c).strip()
        )
    )
    generated_at = datetime.now(UTC).replace(microsecond=0)
    tag = release_tag or _default_release_tag(generated_at)
    vintage = data_vintage or generated_at.date().isoformat()
    politics_tier = _politics_tier_for_scenarios(scenario_ids)

    release_root = (output_dir or (PROJECT_ROOT / "releases" / tag)).resolve()
    release_root.mkdir(parents=True, exist_ok=True)

    work_dir = release_root / "_inputs"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    files_written: list[str] = []
    try:
        province_path, sea_path, adjacency_path, counts = _prepare_inputs(
            work_dir=work_dir,
            province_input=province_input,
            sea_input=sea_input,
            adjacency_input=adjacency_input,
            sample_countries=countries,
            profile_id=profile_id,
            generated_at=generated_at.isoformat(),
            milestone="M14",
            release_channel="beta",
        )

        try:
            province_doc = load_feature_collection(province_path, "province")
        except SampleError as exc:
            raise ReleaseError(str(exc)) from exc
        land_and_optional_sea: list[dict[str, Any]] = list(province_doc["features"])
        if sea_path is not None and sea_path.is_file():
            try:
                sea_doc = load_feature_collection(sea_path, "sea zone")
            except SampleError as exc:
                raise ReleaseError(str(exc)) from exc
            land_and_optional_sea.extend(sea_doc["features"])

        try:
            audit = audit_public_release(
                profile_id=profile_id,
                features=land_and_optional_sea,
                release_channel="beta",
                fail_on_errors=fail_on_license_errors,
            )
        except LicenseAuditError as exc:
            raise ReleaseError(str(exc)) from exc

        pack_dir = release_root / "pack"
        if pack_dir.exists():
            shutil.rmtree(pack_dir)
        try:
            pack_result = export_game_pack(
                profile_id,
                province_input=province_path,
                sea_input=sea_path,
                adjacency_input=adjacency_path,
                output_dir=pack_dir,
                scenarios=scenario_ids,
                allow_unknown_overrides=allow_unknown_overrides,
            )
        except ExportError as exc:
            raise ReleaseError(str(exc)) from exc

        for relative in pack_result.files_written:
            files_written.append(f"pack/{relative}")

        atlas_dir_path: Path | None = None
        if include_atlas:
            if not scenario_ids:
                raise ReleaseError(
                    "Beta atlas face requires at least one scenario. "
                    "Pass --scenario or omit --no-scenarios."
                )
            atlas_dir_path = release_root / "atlas"
            if atlas_dir_path.exists():
                shutil.rmtree(atlas_dir_path)
            try:
                atlas_result = export_atlas_pack(
                    profile_id,
                    province_input=province_path,
                    output_dir=atlas_dir_path,
                    scenarios=scenario_ids,
                    allow_unknown_overrides=allow_unknown_overrides,
                )
            except ExportError as exc:
                raise ReleaseError(str(exc)) from exc
            for relative in atlas_result.files_written:
                files_written.append(f"atlas/{relative}")

        # Cleaned attribution pack from the license audit (catalog + isolation).
        audit_doc = audit.to_dict()
        # Attach downstream outputs after packs exist.
        downstream = sorted(
            {
                path
                for path in files_written
                if path.endswith((".geojson", ".csv", ".json", ".yml", ".md"))
            }
        )
        attribution_records = []
        for record in audit.attribution_records:
            updated = dict(record)
            if updated.get("public_path", True):
                updated["downstream_outputs"] = list(downstream)
            attribution_records.append(updated)
        audit_doc["attribution_records"] = attribution_records

        attribution_path = release_root / "attribution.json"
        _write_json(
            attribution_path,
            {
                "schema_version": "0.1.0",
                "pack_type": "license-audited",
                "release_channel": "beta",
                "records": attribution_records,
            },
        )
        files_written.append("attribution.json")

        # Keep pack attribution in sync when present.
        pack_attribution = pack_dir / "attribution.json"
        if pack_attribution.is_file():
            shutil.copy2(attribution_path, pack_attribution)

        license_audit_json = release_root / "license_audit.json"
        _write_json(license_audit_json, audit_doc)
        files_written.append("license_audit.json")
        license_audit_md = release_root / "LICENSE_AUDIT.md"
        license_audit_md.write_text(license_audit_markdown(audit_doc), encoding="utf-8")
        files_written.append("LICENSE_AUDIT.md")

        label = accuracy_label(
            geometry_tier=BETA_GEOMETRY_TIER,
            politics_tier=politics_tier,
            scenarios=scenario_ids,
            profile_id=profile_id,
            release_channel="beta",
        )
        accuracy_path = release_root / "ACCURACY.md"
        accuracy_path.write_text(accuracy_markdown(label), encoding="utf-8")
        files_written.append("ACCURACY.md")
        accuracy_json_path = release_root / "accuracy_label.json"
        _write_json(accuracy_json_path, label)
        files_written.append("accuracy_label.json")

        recipe = beta_license_audited_recipe(
            profile_id=profile_id,
            scenarios=scenario_ids,
            include_seas=bool(counts["sea_zone_count"]),
            sample_countries=countries,
            release_tag=tag,
            include_atlas=include_atlas,
        )
        recipe_json_path = release_root / "recipe.json"
        recipe_md_path = release_root / "RECIPE.md"
        _write_json(recipe_json_path, recipe)
        recipe_md_path.write_text(recipe_markdown(recipe), encoding="utf-8")
        files_written.extend(["recipe.json", "RECIPE.md"])

        if include_topology_qa_copy:
            qa_src = topology_qa_input or (province_input.parent / "topology_qa.json")
            if qa_src.is_file():
                qa_dst = release_root / "topology_qa.json"
                shutil.copy2(qa_src, qa_dst)
                files_written.append("topology_qa.json")

        sample_geo_dir = release_root / "sample"
        sample_geo_dir.mkdir(parents=True, exist_ok=True)
        sample_provinces = sample_geo_dir / "provinces.geojson"
        shutil.copy2(province_path, sample_provinces)
        files_written.append("sample/provinces.geojson")
        if sea_path is not None and sea_path.is_file():
            sample_seas = sample_geo_dir / "sea_zones.geojson"
            shutil.copy2(sea_path, sample_seas)
            files_written.append("sample/sea_zones.geojson")
        if adjacency_path is not None and adjacency_path.is_file():
            sample_adj = sample_geo_dir / "adjacency.csv"
            shutil.copy2(adjacency_path, sample_adj)
            files_written.append("sample/adjacency.csv")

        readme_path = release_root / "README.md"
        readme_path.write_text(
            _release_readme(
                release_tag=tag,
                profile_id=profile_id,
                scenario_ids=scenario_ids,
                sample_countries=countries,
                province_count=counts["province_count"],
                sea_zone_count=counts["sea_zone_count"],
                is_sample=bool(countries),
                politics_tier=politics_tier,
                include_atlas=include_atlas,
                license_passed=audit.passed,
            ),
            encoding="utf-8",
        )
        files_written.append("README.md")

        files_written = sorted(set(files_written))
        faces: dict[str, Any] = {
            "game": {
                "path": "pack",
                "pack_manifest": "pack/pack_manifest.json",
                "pack_type": "game-template",
            }
        }
        if atlas_dir_path is not None:
            faces["atlas"] = {
                "path": "atlas",
                "pack_manifest": "atlas/atlas_manifest.json",
                "pack_type": "atlas-saas",
            }

        manifest = {
            "schema_version": "0.1.0",
            "manifest_type": "release",
            "milestone": "M14",
            "release_channel": "beta",
            "release_tag": tag,
            "data_vintage": vintage,
            "generated_at": generated_at.isoformat(),
            "generator_version": __version__,
            "profile_id": profile_id,
            "scenario_set": list(scenario_ids),
            "quality_tiers": {
                "geometry": BETA_GEOMETRY_TIER,
                "politics": politics_tier,
            },
            "accuracy_label_path": "accuracy_label.json",
            "license_audit_path": "license_audit.json",
            "license_audit_passed": audit.passed,
            "is_sample": bool(countries),
            "sample_countries": list(countries),
            "inputs": {
                "provinces": str(province_input),
                "sea_zones": None
                if sea_path is None
                else str(sea_input or province_input.parent / "sea_zones.geojson"),
                "adjacency": None
                if adjacency_path is None
                else str(adjacency_input or province_input.parent / "adjacency.csv"),
            },
            "counts": {
                "provinces": counts["province_count"],
                "sea_zones": counts["sea_zone_count"],
                "adjacency_rows": counts["adjacency_count"],
                "attribution_records": len(attribution_records),
                "scenarios": len(scenario_ids),
            },
            "pack": faces["game"],
            "faces": faces,
            "files": files_written,
            "notes": [
                "Public beta: license-audited sources with cleaned attribution pack.",
                "Restricted and share-alike paths are isolated and not mixed into this package.",
                "Geometry remains scaffold-baseline; politics may be curated-politics for official eras.",
                "Sea zones are gameplay abstractions, not legal maritime boundaries.",
                "Not Paradox-grade historical completeness worldwide.",
            ],
        }
        manifest_path = release_root / "release_manifest.json"
        _write_json(manifest_path, manifest)
        if "release_manifest.json" not in files_written:
            files_written = sorted([*files_written, "release_manifest.json"])
            manifest["files"] = files_written
            _write_json(manifest_path, manifest)

        return BetaReleaseResult(
            release_tag=tag,
            profile_id=profile_id,
            output_dir=str(release_root),
            release_manifest=str(manifest_path),
            pack_dir=str(pack_dir),
            atlas_dir=str(atlas_dir_path) if atlas_dir_path is not None else "",
            province_count=counts["province_count"],
            sea_zone_count=counts["sea_zone_count"],
            adjacency_count=counts["adjacency_count"],
            scenario_ids=scenario_ids,
            sample_countries=countries,
            geometry_quality_tier=BETA_GEOMETRY_TIER,
            politics_quality_tier=politics_tier,
            is_sample=bool(countries),
            license_audit_passed=audit.passed,
            attribution_record_count=len(attribution_records),
            files_written=tuple(files_written),
        )
    finally:
        if work_dir.exists():
            shutil.rmtree(work_dir, ignore_errors=True)


def _politics_tier_for_scenarios(scenario_ids: tuple[str, ...]) -> str:
    if any(scenario_id.startswith("official-") for scenario_id in scenario_ids):
        return QUALITY_TIER_CURATED_POLITICS
    return QUALITY_TIER_SCAFFOLD_BASELINE


def _default_release_tag(generated_at: datetime) -> str:
    return f"beta-{__version__}-{generated_at.strftime('%Y%m%d')}"


def _release_readme(
    *,
    release_tag: str,
    profile_id: str,
    scenario_ids: tuple[str, ...],
    sample_countries: tuple[str, ...],
    province_count: int,
    sea_zone_count: int,
    is_sample: bool,
    politics_tier: str,
    include_atlas: bool,
    license_passed: bool,
) -> str:
    sample_note = (
        f"This bundle is a **sample subset** filtered to modern country codes: "
        f"`{', '.join(sample_countries)}` ({province_count} land provinces, "
        f"{sea_zone_count} sea zones)."
        if is_sample
        else f"This bundle includes the full processed layer for profile `{profile_id}` "
        f"({province_count} land provinces, {sea_zone_count} sea zones)."
    )
    scenarios = ", ".join(f"`{s}`" for s in scenario_ids) or "(none)"
    audit_status = "PASSED" if license_passed else "FAILED"
    atlas_row = (
        "| `atlas/` | Atlas / SaaS face (choropleths, legends, uncertainty, tables) |\n"
        if include_atlas
        else ""
    )
    return f"""# GPM public beta release: `{release_tag}`

Milestone **M14** license-audited beta dataset package (game + atlas faces).

{sample_note}

## Quality (honest labels)

| Layer | Tier |
| --- | --- |
| Geometry | `scaffold-baseline` |
| Politics | `{politics_tier}` |

Read **[ACCURACY.md](ACCURACY.md)** before marketing or teaching with this data.
Geometry is still a **modern open-geodata scaffold**. Official era scenarios
carry **curated-politics** overlays where labeled—not period geometry.

## License audit

**Status: {audit_status}**

See **[LICENSE_AUDIT.md](LICENSE_AUDIT.md)** and `license_audit.json`. Restricted
sources (e.g. GADM) and share-alike databases (e.g. OSM/ODbL) are isolated and
must not appear in this public pack. Redistribute with `attribution.json`.

## Contents

| Path | Purpose |
| --- | --- |
| `release_manifest.json` | Release tag, vintage, quality tiers, faces, file inventory |
| `license_audit.json` / `LICENSE_AUDIT.md` | License audit report + isolation notes |
| `ACCURACY.md` / `accuracy_label.json` | Human + machine accuracy labels |
| `RECIPE.md` / `recipe.json` | Reproducible generator steps |
| `attribution.json` | Cleaned attribution pack for redistribution |
| `sample/` | Province / sea / adjacency inputs used for the packs |
| `pack/` | Game template pack (definitions, geojson, localization, scenarios) |
{atlas_row}| `topology_qa.json` | Optional topology QA snapshot when available |

Embedded scenarios: {scenarios}

## Reproduce

See [RECIPE.md](RECIPE.md). Short form:

```bash
uv run gpm sources download --execute --profile {profile_id}
uv run gpm build provinces --profile {profile_id}
uv run gpm build seas --profile {profile_id}
uv run gpm build adjacency --profile {profile_id}
uv run gpm release beta --profile {profile_id} --tag {release_tag}
```

## Consume

1. **Game face:** load `pack/definitions/` and scenario ownership under `pack/scenarios/<id>/`.
2. **Atlas face:** load `atlas/geojson/` choropleths, `atlas/legend.json`, and `atlas/tables/`.
3. Keep `attribution.json` and the license audit with any redistributed copy.
4. Do **not** claim period geometry worldwide or Paradox-grade completeness.

Generated by Global Province Map Template M14 (`{__version__}`).
"""
