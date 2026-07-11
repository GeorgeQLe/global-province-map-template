"""M9 public alpha dataset release packaging."""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from gpm import __version__
from gpm.config import ConfigError, load_profile
from gpm.exporters.pack import ExportError, export_game_pack
from gpm.paths import PROCESSED_DATA_DIR, PROJECT_ROOT
from gpm.release.quality import (
    ALPHA_GEOMETRY_TIER,
    ALPHA_POLITICS_TIER,
    accuracy_label,
    accuracy_markdown,
)
from gpm.release.recipes import modern_scaffold_recipe, recipe_markdown
from gpm.release.sample import (
    SampleError,
    filter_adjacency,
    filter_provinces_by_countries,
    filter_seas_for_land,
    load_adjacency_csv,
    load_feature_collection,
    write_adjacency_csv,
    write_feature_collection,
)

DEFAULT_ALPHA_SCENARIOS: tuple[str, ...] = ("modern-baseline", "demo-1444")
DEFAULT_SAMPLE_COUNTRIES: tuple[str, ...] = ("FRA", "BEL", "NLD", "LUX", "DEU")


class ReleaseError(RuntimeError):
    """Raised when an alpha release bundle cannot be produced."""


@dataclass(frozen=True)
class AlphaReleaseResult:
    release_tag: str
    profile_id: str
    output_dir: str
    release_manifest: str
    pack_dir: str
    province_count: int
    sea_zone_count: int
    adjacency_count: int
    scenario_ids: tuple[str, ...]
    sample_countries: tuple[str, ...]
    geometry_quality_tier: str
    politics_quality_tier: str
    is_sample: bool
    files_written: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_alpha_release(
    profile_id: str = "modern-small",
    *,
    province_input: Path = PROCESSED_DATA_DIR / "provinces.geojson",
    sea_input: Path | None = None,
    adjacency_input: Path | None = None,
    output_dir: Path | None = None,
    release_tag: str | None = None,
    scenarios: tuple[str, ...] | list[str] = DEFAULT_ALPHA_SCENARIOS,
    sample_countries: tuple[str, ...] | list[str] | None = None,
    allow_unknown_overrides: bool = False,
    include_topology_qa_copy: bool = True,
    topology_qa_input: Path | None = None,
    data_vintage: str | None = None,
) -> AlphaReleaseResult:
    """Package a public alpha release: pack + recipe + attribution + accuracy labels.

    When *sample_countries* is non-empty, province/sea/adjacency inputs are
    filtered to those modern ISO codes before packaging. Empty/None means use
    the full processed inputs (full global alpha artifact).
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
            milestone="M9",
            release_channel="alpha",
        )

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

        # Attribution at release root (copy of pack attribution for visibility).
        pack_attribution = pack_dir / "attribution.json"
        if pack_attribution.is_file():
            root_attribution = release_root / "attribution.json"
            shutil.copy2(pack_attribution, root_attribution)
            files_written.append("attribution.json")
            attribution_records = json.loads(pack_attribution.read_text(encoding="utf-8")).get(
                "records", []
            )
        else:
            attribution_records = []

        label = accuracy_label(
            geometry_tier=ALPHA_GEOMETRY_TIER,
            politics_tier=ALPHA_POLITICS_TIER,
            scenarios=scenario_ids,
            profile_id=profile_id,
            release_channel="alpha",
        )
        accuracy_path = release_root / "ACCURACY.md"
        accuracy_path.write_text(accuracy_markdown(label), encoding="utf-8")
        files_written.append("ACCURACY.md")
        accuracy_json_path = release_root / "accuracy_label.json"
        _write_json(accuracy_json_path, label)
        files_written.append("accuracy_label.json")

        recipe = modern_scaffold_recipe(
            profile_id=profile_id,
            scenarios=scenario_ids,
            include_seas=bool(counts["sea_zone_count"]),
            sample_countries=countries,
            release_tag=tag,
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

        # Optional sample inputs for offline consumers who do not want the pack tree only.
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
            ),
            encoding="utf-8",
        )
        files_written.append("README.md")

        files_written = sorted(set(files_written))
        manifest = {
            "schema_version": "0.1.0",
            "manifest_type": "release",
            "milestone": "M9",
            "release_channel": "alpha",
            "release_tag": tag,
            "data_vintage": vintage,
            "generated_at": generated_at.isoformat(),
            "generator_version": __version__,
            "profile_id": profile_id,
            "scenario_set": list(scenario_ids),
            "quality_tiers": {
                "geometry": ALPHA_GEOMETRY_TIER,
                "politics": ALPHA_POLITICS_TIER,
            },
            "accuracy_label_path": "accuracy_label.json",
            "is_sample": bool(countries),
            "sample_countries": list(countries),
            "inputs": {
                "provinces": str(province_input),
                "sea_zones": None if sea_path is None else str(sea_input or province_input.parent / "sea_zones.geojson"),
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
            "pack": {
                "path": "pack",
                "pack_manifest": "pack/pack_manifest.json",
                "pack_type": "game-template",
            },
            "files": files_written,
            "notes": [
                "Public alpha: modern geographic scaffold with honest accuracy labels.",
                "Not an official curated historical era release.",
                "Sea zones are gameplay abstractions, not legal maritime boundaries.",
            ],
        }
        manifest_path = release_root / "release_manifest.json"
        _write_json(manifest_path, manifest)
        if "release_manifest.json" not in files_written:
            files_written = sorted([*files_written, "release_manifest.json"])
            manifest["files"] = files_written
            _write_json(manifest_path, manifest)

        return AlphaReleaseResult(
            release_tag=tag,
            profile_id=profile_id,
            output_dir=str(release_root),
            release_manifest=str(manifest_path),
            pack_dir=str(pack_dir),
            province_count=counts["province_count"],
            sea_zone_count=counts["sea_zone_count"],
            adjacency_count=counts["adjacency_count"],
            scenario_ids=scenario_ids,
            sample_countries=countries,
            geometry_quality_tier=ALPHA_GEOMETRY_TIER,
            politics_quality_tier=ALPHA_POLITICS_TIER,
            is_sample=bool(countries),
            files_written=tuple(files_written),
        )
    finally:
        # Staging inputs are only needed during packaging.
        if work_dir.exists():
            shutil.rmtree(work_dir, ignore_errors=True)


def _prepare_inputs(
    *,
    work_dir: Path,
    province_input: Path,
    sea_input: Path | None,
    adjacency_input: Path | None,
    sample_countries: tuple[str, ...],
    profile_id: str,
    generated_at: str,
    milestone: str = "M9",
    release_channel: str = "alpha",
) -> tuple[Path, Path | None, Path | None, dict[str, int]]:
    try:
        province_doc = load_feature_collection(province_input, "province")
    except SampleError as exc:
        raise ReleaseError(str(exc)) from exc
    land_features = list(province_doc["features"])
    if not land_features:
        raise ReleaseError(f"Province input has no features: {province_input}")

    resolved_sea = _resolve_optional(sea_input, province_input.parent / "sea_zones.geojson")
    resolved_adj = _resolve_optional(adjacency_input, province_input.parent / "adjacency.csv")

    sea_features: list[dict[str, Any]] = []
    if resolved_sea is not None:
        try:
            sea_doc = load_feature_collection(resolved_sea, "sea zone")
        except SampleError as exc:
            raise ReleaseError(str(exc)) from exc
        sea_features = list(sea_doc["features"])

    adjacency_rows: list[dict[str, str]] = []
    if resolved_adj is not None:
        try:
            adjacency_rows = load_adjacency_csv(resolved_adj)
        except SampleError as exc:
            raise ReleaseError(str(exc)) from exc

    if sample_countries:
        countries = set(sample_countries)
        land_features = filter_provinces_by_countries(land_features, countries)
        if not land_features:
            raise ReleaseError(
                "Sample country filter matched no land provinces: "
                + ", ".join(sample_countries)
            )
        land_ids = {
            str(feature["properties"]["province_id"])
            for feature in land_features
            if isinstance(feature.get("properties"), dict)
            and isinstance(feature["properties"].get("province_id"), str)
        }
        sea_features = filter_seas_for_land(sea_features, land_ids)
        sea_ids = {
            str(feature["properties"]["province_id"])
            for feature in sea_features
            if isinstance(feature.get("properties"), dict)
            and isinstance(feature["properties"].get("province_id"), str)
        }
        keep_ids = land_ids | sea_ids
        adjacency_rows = filter_adjacency(adjacency_rows, keep_ids)

    gpm_meta = {
        "schema_version": "0.1.0",
        "milestone": milestone,
        "profile_id": profile_id,
        "generated_at": generated_at,
        "generator_version": __version__,
        "release_channel": release_channel,
        "sample_countries": list(sample_countries),
    }
    province_path = work_dir / "provinces.geojson"
    write_feature_collection(
        province_path,
        name="provinces",
        features=land_features,
        gpm_meta={**gpm_meta, "layer": "provinces", "feature_count": len(land_features)},
    )

    sea_path: Path | None = None
    if sea_features:
        sea_path = work_dir / "sea_zones.geojson"
        write_feature_collection(
            sea_path,
            name="sea_zones",
            features=sea_features,
            gpm_meta={**gpm_meta, "layer": "sea_zones", "feature_count": len(sea_features)},
        )

    adjacency_path: Path | None = None
    if adjacency_rows or resolved_adj is not None:
        adjacency_path = work_dir / "adjacency.csv"
        write_adjacency_csv(adjacency_path, adjacency_rows)

    counts = {
        "province_count": len(land_features),
        "sea_zone_count": len(sea_features),
        "adjacency_count": len(adjacency_rows),
    }
    return province_path, sea_path, adjacency_path, counts


def _resolve_optional(explicit: Path | None, default: Path) -> Path | None:
    path = default if explicit is None else explicit
    if path.is_file():
        return path
    if explicit is not None:
        raise ReleaseError(f"Optional release input does not exist: {explicit}")
    return None


def _default_release_tag(generated_at: datetime) -> str:
    return f"alpha-{__version__}-{generated_at.strftime('%Y%m%d')}"


def _release_readme(
    *,
    release_tag: str,
    profile_id: str,
    scenario_ids: tuple[str, ...],
    sample_countries: tuple[str, ...],
    province_count: int,
    sea_zone_count: int,
    is_sample: bool,
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
    return f"""# GPM public alpha release: `{release_tag}`

Milestone **M9** public alpha dataset package.

{sample_note}

## Quality (honest labels)

| Layer | Tier |
| --- | --- |
| Geometry | `scaffold-baseline` |
| Politics | `scaffold-baseline` |

Read **[ACCURACY.md](ACCURACY.md)** before marketing or teaching with this data.
This is a **modern open-geodata scaffold**, not a curated historical atlas and
not Paradox-grade era accuracy.

## Contents

| Path | Purpose |
| --- | --- |
| `release_manifest.json` | Release tag, vintage, quality tiers, file inventory |
| `ACCURACY.md` / `accuracy_label.json` | Human + machine accuracy labels |
| `RECIPE.md` / `recipe.json` | Reproducible generator steps |
| `attribution.json` | License notices for redistribution |
| `sample/` | Province / sea / adjacency inputs used for the pack |
| `pack/` | Game template pack (definitions, geojson, localization, scenarios) |
| `topology_qa.json` | Optional topology QA snapshot when available |

Embedded scenarios: {scenarios}

## Reproduce

See [RECIPE.md](RECIPE.md). Short form:

```bash
uv run gpm sources download --execute --profile {profile_id}
uv run gpm build provinces --profile {profile_id}
uv run gpm build seas --profile {profile_id}
uv run gpm build adjacency --profile {profile_id}
uv run gpm release alpha --profile {profile_id} --tag {release_tag}
```

## Consume

1. Load `pack/definitions/` for game tables.
2. Join scenario ownership on `province_id` under `pack/scenarios/<id>/`.
3. Keep `attribution.json` with any redistributed copy.
4. Do **not** claim curated politics or period geometry for this alpha.

Generated by Global Province Map Template M9 (`{__version__}`).
"""


def _write_json(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
