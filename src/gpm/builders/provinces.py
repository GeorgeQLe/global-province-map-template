from __future__ import annotations

import hashlib
import json
import unicodedata
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

from shapely import normalize, to_wkb
from shapely.geometry import shape
from shapely.errors import ShapelyError

from gpm import __version__
from gpm.builders.refinement import (
    ProvinceRefinementError,
    ProvinceRefinementResult,
    RefinementSettings,
    refine_land_provinces,
)
from gpm.config import load_profile, province_refinement_settings
from gpm.geo.shapefile import ShapefileReadError, geometry_area_sq_km, read_zipped_shapefile
from gpm.paths import INTERMEDIATE_DATA_DIR, PROCESSED_DATA_DIR, RAW_DATA_DIR
from gpm.sources.registry import resolve_source_adapters


class ProvinceBuildError(RuntimeError):
    """Raised when province draft generation cannot continue."""


@dataclass(frozen=True)
class ProvinceBuildResult:
    profile_id: str
    target_province_count: int
    candidate_output: str
    province_output: str
    candidate_count: int
    province_count: int
    admin1_count: int
    admin0_fallback_count: int
    refinement_applied: bool
    refinement_strategy: str | None
    split_count: int
    split_parent_count: int
    merged_fragment_count: int
    skipped_invalid_count: int
    population_total: float | None
    population_sample_count: int
    settlement_count: int
    population_input: str | None
    settlement_input: str | None
    source_artifacts: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_land_province_draft(
    profile_id: str,
    *,
    raw_dir: Path = RAW_DATA_DIR,
    intermediate_dir: Path = INTERMEDIATE_DATA_DIR,
    processed_dir: Path = PROCESSED_DATA_DIR,
    candidate_output: Path | None = None,
    province_output: Path | None = None,
    refine: bool = False,
    target_province_count: int | None = None,
    population_input: Path | None = None,
    settlement_input: Path | None = None,
    population_license_lineage: tuple[str, ...] = (),
    settlement_license_lineage: tuple[str, ...] = (),
) -> ProvinceBuildResult:
    """Build Natural Earth candidates and optionally apply the M4 refinement."""
    profile = load_profile(profile_id)
    settings_values = province_refinement_settings(
        profile,
        target_province_count=target_province_count,
    )
    target_count = int(settings_values["target_province_count"])
    artifacts = _natural_earth_artifact_paths(profile_id, raw_dir)
    _require_artifacts(artifacts)

    try:
        admin1_features = read_zipped_shapefile(artifacts["admin1_states_provinces"])
        admin0_features = read_zipped_shapefile(artifacts["admin0_countries"])
    except ShapefileReadError as exc:
        raise ProvinceBuildError(str(exc)) from exc

    generated_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    source_lineage_admin1 = _source_lineage("natural_earth", "admin1_states_provinces", artifacts)
    source_lineage_admin0 = _source_lineage("natural_earth", "admin0_countries", artifacts)
    license_lineage = ("Natural Earth public domain",)

    admin1_provinces = [
        _province_feature(
            feature.geometry,
            feature.properties,
            source_layer="admin1_states_provinces",
            source_lineage=source_lineage_admin1,
            license_lineage=license_lineage,
            index=index,
        )
        for index, feature in enumerate(admin1_features, start=1)
        if feature.geometry.get("coordinates")
    ]
    represented_countries = {
        province["properties"]["parent_country_id"]
        for province in admin1_provinces
        if province["properties"]["parent_country_id"]
    }

    admin0_fallbacks = []
    for index, feature in enumerate(admin0_features, start=1):
        country_id = _country_id(feature.properties)
        if country_id in represented_countries:
            continue
        if not feature.geometry.get("coordinates"):
            continue
        admin0_fallbacks.append(
            _province_feature(
                feature.geometry,
                feature.properties,
                source_layer="admin0_countries",
                source_lineage=source_lineage_admin0,
                license_lineage=license_lineage,
                index=index,
            )
        )

    provinces = sorted(
        [*admin1_provinces, *admin0_fallbacks],
        key=lambda item: item["properties"]["province_id"],
    )
    _ensure_unique_province_ids(provinces)
    candidates = [_candidate_from_province(feature) for feature in provinces]
    refinement_requested = (
        refine
        or target_province_count is not None
        or population_input is not None
        or settlement_input is not None
    )
    refinement_result: ProvinceRefinementResult | None = None
    if refinement_requested:
        try:
            refinement_result = refine_land_provinces(
                provinces,
                settings=RefinementSettings(**settings_values),
                population_input=population_input,
                settlement_input=settlement_input,
                population_license_lineage=population_license_lineage,
                settlement_license_lineage=settlement_license_lineage,
            )
        except ProvinceRefinementError as exc:
            raise ProvinceBuildError(str(exc)) from exc
        provinces = list(refinement_result.features)
        _ensure_unique_province_ids(provinces)

    candidate_output = candidate_output or intermediate_dir / "land_province_candidates.geojson"
    province_output = province_output or processed_dir / "provinces.geojson"
    candidate_document = _feature_collection(
        profile_id,
        target_count,
        generated_at,
        candidates,
        artifacts=artifacts,
        layer_kind="land_province_candidates",
        refinement=None,
    )
    province_document = _feature_collection(
        profile_id,
        target_count,
        generated_at,
        provinces,
        artifacts=artifacts,
        layer_kind="provinces",
        refinement=refinement_result,
    )

    _write_json(candidate_output, candidate_document)
    _write_json(province_output, province_document)

    return ProvinceBuildResult(
        profile_id=profile_id,
        target_province_count=target_count,
        candidate_output=str(candidate_output),
        province_output=str(province_output),
        candidate_count=len(candidates),
        province_count=len(provinces),
        admin1_count=len(admin1_provinces),
        admin0_fallback_count=len(admin0_fallbacks),
        refinement_applied=refinement_result is not None,
        refinement_strategy=refinement_result.strategy if refinement_result is not None else None,
        split_count=refinement_result.split_count if refinement_result is not None else 0,
        split_parent_count=refinement_result.split_parent_count if refinement_result is not None else 0,
        merged_fragment_count=(
            refinement_result.merged_fragment_count if refinement_result is not None else 0
        ),
        skipped_invalid_count=(
            refinement_result.skipped_invalid_count if refinement_result is not None else 0
        ),
        population_total=refinement_result.population_total if refinement_result is not None else None,
        population_sample_count=(
            refinement_result.population_sample_count if refinement_result is not None else 0
        ),
        settlement_count=refinement_result.settlement_count if refinement_result is not None else 0,
        population_input=str(population_input) if population_input is not None else None,
        settlement_input=str(settlement_input) if settlement_input is not None else None,
        source_artifacts=tuple(_manifest_path(path) for path in artifacts.values()),
    )


def _natural_earth_artifact_paths(profile_id: str, raw_dir: Path) -> dict[str, Path]:
    adapters = resolve_source_adapters(profile_id, ["natural_earth"])
    downloads = adapters[0].planned_downloads()
    selected_layers = {"admin1_states_provinces", "admin0_countries"}
    return {
        download.layer_id: _raw_artifact_path(download.expected_path, raw_dir)
        for download in downloads
        if download.layer_id in selected_layers
    }


def _raw_artifact_path(expected_path: str, raw_dir: Path) -> Path:
    parts = PurePosixPath(expected_path).parts
    if len(parts) < 3 or parts[0:2] != ("data", "raw"):
        raise ProvinceBuildError(f"Planned source artifact path must be under data/raw/: {expected_path}")
    return raw_dir.expanduser() / Path(*parts[2:])


def _require_artifacts(artifacts: dict[str, Path]) -> None:
    missing = [path for path in artifacts.values() if not path.is_file()]
    if not missing:
        return

    lines = "\n".join(f"- {path}" for path in missing)
    raise ProvinceBuildError(
        "M2 province generation requires downloaded Natural Earth admin boundary zips. "
        "Run `uv run gpm sources download --execute --source natural_earth` or pass "
        f"`--raw-dir` pointing at an existing raw artifact directory.\nMissing:\n{lines}"
    )


def _province_feature(
    geometry: dict[str, Any],
    source_properties: dict[str, Any],
    *,
    source_layer: str,
    source_lineage: tuple[str, ...],
    license_lineage: tuple[str, ...],
    index: int,
) -> dict[str, Any]:
    country_id = _country_id(source_properties)
    region_id = _region_id(source_properties, source_layer)
    display_name = _display_name(source_properties, source_layer, index)
    province_id = _province_id(
        geometry,
        source_layer=source_layer,
        country_id=country_id,
        region_id=region_id,
    )

    return {
        "type": "Feature",
        "geometry": geometry,
        "properties": {
            "province_id": province_id,
            "display_name": display_name,
            "kind": "land",
            "parent_region_id": region_id,
            "parent_country_id": country_id,
            "area_sq_km": round(geometry_area_sq_km(geometry), 3),
            "estimated_population": _estimated_population(source_properties),
            "terrain_class": "unclassified",
            "coastal": False,
            "island": False,
            "source_lineage": list(source_lineage),
            "license_lineage": list(license_lineage),
            "source_layer": source_layer,
        },
    }


def _candidate_from_province(province: dict[str, Any]) -> dict[str, Any]:
    properties = dict(province["properties"])
    properties["candidate_id"] = properties["province_id"].replace("ne_", "candidate_ne_", 1)
    properties["candidate_strategy"] = "natural-earth-admin-boundary"
    return {
        "type": "Feature",
        "geometry": province["geometry"],
        "properties": properties,
    }


def _feature_collection(
    profile_id: str,
    target_count: int,
    generated_at: str,
    features: list[dict[str, Any]],
    *,
    artifacts: dict[str, Path],
    layer_kind: str,
    refinement: ProvinceRefinementResult | None,
) -> dict[str, Any]:
    draft_notes = [
        "M2 candidates are built from Natural Earth modern admin boundaries.",
        "Province IDs use normalized geometry hashes and do not depend on feature order.",
    ]
    if refinement is None:
        draft_notes.append("Coastal, island, terrain, and population classifications are placeholders.")
    else:
        draft_notes.extend(
            [
                "M4 processed provinces use deterministic population/settlement-aware Voronoi refinement.",
                "Tiny generated sibling fragments are merged by shared border without crossing source parents.",
                "Coastal, island, and terrain classifications remain placeholders.",
            ]
        )
    return {
        "type": "FeatureCollection",
        "name": layer_kind,
        "gpm": {
            "schema_version": "0.1.0",
            "id_scheme": (
                "source-geometry-sha256-v1"
                if refinement is None
                else "source-geometry-sha256-v1+m4-parent-geometry-sha256-v1"
            ),
            "profile_id": profile_id,
            "generated_at": generated_at,
            "generator_version": __version__,
            "target_province_count": target_count,
            "draft_notes": draft_notes,
            "source_artifacts": [_manifest_path(path) for path in artifacts.values()],
            "refinement": (
                {
                    "milestone": "M4",
                    "strategy": refinement.strategy,
                    "split_count": refinement.split_count,
                    "split_parent_count": refinement.split_parent_count,
                    "merged_fragment_count": refinement.merged_fragment_count,
                    "skipped_invalid_count": refinement.skipped_invalid_count,
                    "population_total": refinement.population_total,
                    "population_sample_count": refinement.population_sample_count,
                    "settlement_count": refinement.settlement_count,
                    "source_lineage": list(refinement.source_lineage),
                    "license_lineage": list(refinement.license_lineage),
                }
                if refinement is not None
                else None
            ),
        },
        "features": features,
    }


def _source_lineage(source_id: str, layer_id: str, artifacts: dict[str, Path]) -> tuple[str, ...]:
    return (f"{source_id}:{layer_id}:{_manifest_path(artifacts[layer_id])}",)


def _write_json(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n"
    path.write_text(payload, encoding="utf-8")


def _manifest_path(path: Path) -> str:
    try:
        from gpm.paths import PROJECT_ROOT

        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def _country_id(properties: dict[str, Any]) -> str | None:
    return _first_property(
        properties,
        "adm0_a3",
        "iso_a3",
        "iso_a2",
        "sov_a3",
        "gu_a3",
        "adm0_code",
        "admin",
    )


def _region_id(properties: dict[str, Any], source_layer: str) -> str | None:
    if source_layer == "admin0_countries":
        return _country_id(properties)
    return _first_property(
        properties,
        "iso_3166_2",
        "adm1_code",
        "postal",
        "fips",
        "gn_id",
        "name",
    )


def _display_name(properties: dict[str, Any], source_layer: str, index: int) -> str:
    fallback = "Country" if source_layer == "admin0_countries" else "Province"
    value = _first_property(
        properties,
        "name_en",
        "name",
        "nameascii",
        "admin",
        "geonunit",
        "region",
    )
    return value or f"{fallback} {index}"


def _estimated_population(properties: dict[str, Any]) -> float | None:
    value = _first_property(properties, "pop_est", "pop_est_d", "gn_pop")
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _first_property(properties: dict[str, Any], *keys: str) -> str | None:
    by_lower = {key.lower(): value for key, value in properties.items()}
    for key in keys:
        value = by_lower.get(key.lower())
        if value is None:
            continue
        # Shapefile DBF strings are often fixed-width with trailing NULs.
        text = str(value).replace("\x00", "").strip()
        if text and text != "-99":
            return text
    return None


def _province_id(
    geometry: dict[str, Any],
    *,
    source_layer: str,
    country_id: str | None,
    region_id: str | None,
) -> str:
    """Return an ID stable across equivalent GeoJSON representations."""
    try:
        canonical_geometry = normalize(shape(geometry))
        geometry_wkb = to_wkb(canonical_geometry, byte_order=1, include_srid=False)
    except (ShapelyError, TypeError, ValueError) as exc:
        raise ProvinceBuildError(f"Cannot derive a province ID from malformed geometry: {exc}") from exc

    identity = json.dumps(
        {
            "country_id": country_id or "",
            "region_id": region_id or "",
            "source_layer": source_layer,
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    digest = hashlib.sha256(identity + b"\0" + geometry_wkb).hexdigest()[:12]
    slug_parts = [country_id, region_id]
    label = "-".join(_slug_token(part) for part in slug_parts if part and _slug_token(part))
    if not label:
        label = _slug_token(source_layer) or "province"
    return f"ne_{label}-{digest}"


def _ensure_unique_province_ids(features: list[dict[str, Any]]) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for feature in features:
        province_id = feature["properties"]["province_id"]
        if province_id in seen:
            duplicates.add(province_id)
        seen.add(province_id)
    if duplicates:
        joined = ", ".join(sorted(duplicates))
        raise ProvinceBuildError(f"Deterministic province ID collision(s): {joined}")


def _slug_token(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", errors="ignore").decode("ascii")
    token = []
    previous_dash = False
    for character in value.lower():
        if character.isalnum():
            token.append(character)
            previous_dash = False
        elif not previous_dash:
            token.append("-")
            previous_dash = True
    return "".join(token).strip("-")
