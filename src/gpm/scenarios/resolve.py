"""Resolve curated scenario ownership overlays over modern province geometry.

Geometry is never rewritten. Political attributes (owner, controller, cores,
claims, culture, religion, disputed) are layered via baseline projection and
explicit override rules.
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from gpm import __version__
from gpm.config import load_profile
from gpm.paths import PROCESSED_DATA_DIR, PROCESSED_SCENARIO_DIR, SCENARIO_DIR

SCENARIO_SCHEMA_VERSION = "0.1.0"
ASSIGNMENT_SOURCES = frozenset(
    {"baseline", "country_rule", "region_rule", "province_override"}
)
SCENARIO_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
OWNERSHIP_CSV_FIELDS = (
    "province_id",
    "scenario_id",
    "start_date",
    "end_date",
    "owner",
    "controller",
    "cores",
    "claims",
    "culture",
    "religion",
    "disputed",
    "assignment_source",
    "parent_country_id",
    "parent_region_id",
    "display_name",
    "notes",
)


class ScenarioError(RuntimeError):
    """Raised when a scenario cannot be loaded, validated, or built."""


@dataclass(frozen=True)
class ScenarioSummary:
    scenario_id: str
    label: str
    era: str
    start_date: str
    end_date: str | None
    path: str
    country_rule_count: int
    region_rule_count: int
    province_override_count: int
    quality_tier: str | None = None
    official_era: bool = False
    recommended_profile: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ScenarioBuildResult:
    scenario_id: str
    profile_id: str
    era: str
    start_date: str
    end_date: str | None
    province_input: str
    output_dir: str
    ownership_csv: str
    ownership_json: str
    countries_json: str
    scenario_manifest: str
    land_province_count: int
    ownership_row_count: int
    country_rule_hits: int
    region_rule_hits: int
    province_override_hits: int
    baseline_only_count: int
    unknown_override_count: int
    owner_tag_count: int
    files_written: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def list_scenarios(*, scenario_dir: Path | None = None) -> list[ScenarioSummary]:
    """List scenario definition files under configs/scenarios (or a custom dir)."""
    root = SCENARIO_DIR if scenario_dir is None else scenario_dir
    if not root.is_dir():
        return []
    summaries: list[ScenarioSummary] = []
    for path in sorted(root.glob("*.json")):
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
            validate_scenario_document(document, path=path)
        except (OSError, json.JSONDecodeError, ScenarioError):
            continue
        summaries.append(_summary_from_document(document, path))
    return summaries


def load_scenario(
    scenario_id: str,
    *,
    scenario_dir: Path | None = None,
    scenario_path: Path | None = None,
) -> dict[str, Any]:
    """Load and validate a scenario definition by id or explicit path."""
    if scenario_path is not None:
        path = scenario_path
    else:
        root = SCENARIO_DIR if scenario_dir is None else scenario_dir
        path = root / f"{scenario_id}.json"
    if not path.is_file():
        available = ", ".join(item.scenario_id for item in list_scenarios(scenario_dir=scenario_dir)) or "none"
        raise ScenarioError(
            f"Unknown scenario '{scenario_id}' at {path}. Available scenarios: {available}."
        )
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ScenarioError(f"Scenario file is not valid JSON: {path}: {exc}") from exc
    except OSError as exc:
        raise ScenarioError(f"Unable to read scenario file {path}: {exc}") from exc

    validate_scenario_document(document, path=path)
    actual_id = document["scenario_id"]
    if scenario_path is None and actual_id != scenario_id:
        raise ScenarioError(
            f"Scenario id mismatch in {path}: expected '{scenario_id}', found '{actual_id}'."
        )
    document = dict(document)
    document["_path"] = str(path)
    return document


def validate_scenario_document(
    document: Any,
    *,
    path: Path | None = None,
) -> None:
    """Validate core invariants of a scenario definition document."""
    label = str(path) if path is not None else "scenario"
    if not isinstance(document, dict):
        raise ScenarioError(f"{label} must be a JSON object")
    required = ("schema_version", "scenario_id", "label", "era", "start_date")
    missing = [key for key in required if key not in document]
    if missing:
        raise ScenarioError(f"{label} missing required key(s): {', '.join(missing)}")
    if document["schema_version"] != SCENARIO_SCHEMA_VERSION:
        raise ScenarioError(
            f"{label}.schema_version must be {SCENARIO_SCHEMA_VERSION}, "
            f"found {document['schema_version']!r}"
        )
    scenario_id = document["scenario_id"]
    if not isinstance(scenario_id, str) or not SCENARIO_ID_RE.match(scenario_id):
        raise ScenarioError(
            f"{label}.scenario_id must match {SCENARIO_ID_RE.pattern}, found {scenario_id!r}"
        )
    for key in ("label", "era", "start_date"):
        value = document[key]
        if not isinstance(value, str) or not value.strip():
            raise ScenarioError(f"{label}.{key} must be a non-empty string")
    quality_tier = document.get("quality_tier")
    if quality_tier is not None:
        if not isinstance(quality_tier, str) or not quality_tier.strip():
            raise ScenarioError(f"{label}.quality_tier must be a non-empty string when set")
        allowed_tiers = {
            "scaffold-baseline",
            "curated-politics",
            "period-geometry",
        }
        if quality_tier.strip() not in allowed_tiers:
            raise ScenarioError(
                f"{label}.quality_tier must be one of {sorted(allowed_tiers)}, "
                f"found {quality_tier!r}"
            )
    if "official_era" in document and not isinstance(document.get("official_era"), bool):
        raise ScenarioError(f"{label}.official_era must be a boolean when set")
    priority = document.get("priority_theaters")
    if priority is not None:
        if not isinstance(priority, list) or not all(
            isinstance(item, str) and item.strip() for item in priority
        ):
            raise ScenarioError(f"{label}.priority_theaters must be a list of non-empty strings")
    end_date = document.get("end_date")
    if end_date is not None and (not isinstance(end_date, str) or not end_date.strip()):
        raise ScenarioError(f"{label}.end_date must be a non-empty string or null")

    countries = document.get("countries", {})
    if countries is None:
        countries = {}
    if not isinstance(countries, dict):
        raise ScenarioError(f"{label}.countries must be an object")
    for tag, meta in countries.items():
        if not isinstance(tag, str) or not tag.strip():
            raise ScenarioError(f"{label}.countries keys must be non-empty strings")
        if not isinstance(meta, dict):
            raise ScenarioError(f"{label}.countries[{tag!r}] must be an object")
        display = meta.get("display_name")
        if not isinstance(display, str) or not display.strip():
            raise ScenarioError(
                f"{label}.countries[{tag!r}].display_name must be a non-empty string"
            )

    defaults = document.get("defaults")
    if defaults is not None and not isinstance(defaults, dict):
        raise ScenarioError(f"{label}.defaults must be an object when present")

    for list_key in ("country_rules", "region_rules", "province_overrides"):
        value = document.get(list_key, [])
        if value is None:
            continue
        if not isinstance(value, list):
            raise ScenarioError(f"{label}.{list_key} must be a list")

    for index, rule in enumerate(document.get("country_rules") or []):
        _validate_bulk_rule(rule, f"{label}.country_rules[{index}]", match_key="match_parent_country_id")
    for index, rule in enumerate(document.get("region_rules") or []):
        _validate_bulk_rule(rule, f"{label}.region_rules[{index}]", match_key="match_parent_region_id")
    for index, override in enumerate(document.get("province_overrides") or []):
        _validate_province_override(override, f"{label}.province_overrides[{index}]")


def resolve_ownership_records(
    scenario: dict[str, Any],
    land_features: list[dict[str, Any]],
    *,
    allow_unknown_overrides: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Apply baseline + country/region/province overrides to land province features.

    Later layers win field-by-field. Returns sorted ownership records and hit stats.
    """
    validate_scenario_document(scenario)
    scenario_id = str(scenario["scenario_id"])
    start_date = str(scenario["start_date"])
    end_date = scenario.get("end_date")
    if end_date is not None:
        end_date = str(end_date)
    defaults = scenario.get("defaults") if isinstance(scenario.get("defaults"), dict) else {}
    default_culture = _nullable_str(defaults.get("culture"))
    default_religion = _nullable_str(defaults.get("religion"))
    default_disputed = bool(defaults.get("disputed", False))

    country_rules = list(scenario.get("country_rules") or [])
    region_rules = list(scenario.get("region_rules") or [])
    province_overrides = list(scenario.get("province_overrides") or [])

    country_by_id: dict[str, list[dict[str, Any]]] = {}
    for rule in country_rules:
        key = str(rule["match_parent_country_id"]).strip()
        country_by_id.setdefault(key, []).append(rule)

    region_by_id: dict[str, list[dict[str, Any]]] = {}
    for rule in region_rules:
        key = str(rule["match_parent_region_id"]).strip()
        region_by_id.setdefault(key, []).append(rule)

    override_by_id: dict[str, dict[str, Any]] = {}
    for override in province_overrides:
        province_id = str(override["province_id"]).strip()
        # Later duplicate overrides win (authoring convenience).
        override_by_id[province_id] = override

    land_ids: set[str] = set()
    records: list[dict[str, Any]] = []
    country_rule_hits = 0
    region_rule_hits = 0
    province_override_hits = 0
    baseline_only_count = 0

    for feature in land_features:
        properties = feature.get("properties") or {}
        if not isinstance(properties, dict):
            continue
        kind = properties.get("kind", "land")
        if kind not in (None, "land"):
            continue
        province_id = properties.get("province_id")
        if not isinstance(province_id, str) or not province_id.strip():
            raise ScenarioError("Land province feature is missing province_id")
        province_id = province_id.strip()
        if province_id in land_ids:
            raise ScenarioError(f"Duplicate land province_id in input: {province_id}")
        land_ids.add(province_id)

        parent_country = _nullable_str(properties.get("parent_country_id"))
        parent_region = _nullable_str(properties.get("parent_region_id"))
        display_name = _nullable_str(properties.get("display_name"))

        if parent_country:
            owner = parent_country
            controller = parent_country
            cores = [parent_country]
        else:
            owner = "UNK"
            controller = "UNK"
            cores = []
        claims: list[str] = []
        culture = default_culture
        religion = default_religion
        disputed = default_disputed
        notes: str | None = None
        assignment_source = "baseline"

        for rule in country_by_id.get(parent_country or "", []):
            owner, controller, cores, claims, culture, religion, disputed, notes = _apply_fields(
                rule,
                owner=owner,
                controller=controller,
                cores=cores,
                claims=claims,
                culture=culture,
                religion=religion,
                disputed=disputed,
                notes=notes,
            )
            assignment_source = "country_rule"
            country_rule_hits += 1

        for rule in region_by_id.get(parent_region or "", []):
            owner, controller, cores, claims, culture, religion, disputed, notes = _apply_fields(
                rule,
                owner=owner,
                controller=controller,
                cores=cores,
                claims=claims,
                culture=culture,
                religion=religion,
                disputed=disputed,
                notes=notes,
            )
            assignment_source = "region_rule"
            region_rule_hits += 1

        if province_id in override_by_id:
            override = override_by_id[province_id]
            owner, controller, cores, claims, culture, religion, disputed, notes = _apply_fields(
                override,
                owner=owner,
                controller=controller,
                cores=cores,
                claims=claims,
                culture=culture,
                religion=religion,
                disputed=disputed,
                notes=notes,
            )
            assignment_source = "province_override"
            province_override_hits += 1

        if assignment_source == "baseline":
            baseline_only_count += 1

        records.append(
            {
                "province_id": province_id,
                "scenario_id": scenario_id,
                "start_date": start_date,
                "end_date": end_date,
                "owner": owner,
                "controller": controller,
                "cores": _unique_strings(cores),
                "claims": _unique_strings(claims),
                "culture": culture,
                "religion": religion,
                "disputed": bool(disputed),
                "assignment_source": assignment_source,
                "parent_country_id": parent_country,
                "parent_region_id": parent_region,
                "display_name": display_name,
                "notes": notes,
            }
        )

    unknown_overrides = sorted(set(override_by_id) - land_ids)
    if unknown_overrides and not allow_unknown_overrides:
        preview = ", ".join(unknown_overrides[:8])
        more = "" if len(unknown_overrides) <= 8 else f" (+{len(unknown_overrides) - 8} more)"
        raise ScenarioError(
            "Province override(s) reference unknown land province_id(s): "
            f"{preview}{more}. Use --allow-unknown-overrides to ignore, or fix the scenario."
        )

    records.sort(key=lambda row: row["province_id"])
    stats = {
        "country_rule_hits": country_rule_hits,
        "region_rule_hits": region_rule_hits,
        "province_override_hits": province_override_hits,
        "baseline_only_count": baseline_only_count,
        "unknown_override_count": len(unknown_overrides),
        "owner_tag_count": len({row["owner"] for row in records}),
    }
    return records, stats


def build_scenario_ownership(
    scenario_id: str,
    *,
    profile_id: str,
    province_input: Path = PROCESSED_DATA_DIR / "provinces.geojson",
    output_dir: Path | None = None,
    scenario_dir: Path | None = None,
    scenario_path: Path | None = None,
    allow_unknown_overrides: bool = False,
) -> ScenarioBuildResult:
    """Load provinces + scenario, resolve ownership, and write processed scenario outputs."""
    # Profile load validates the profile exists; generation.historical_overrides is advisory.
    load_profile(profile_id)
    scenario = load_scenario(
        scenario_id,
        scenario_dir=scenario_dir,
        scenario_path=scenario_path,
    )
    actual_id = str(scenario["scenario_id"])

    if not province_input.is_file():
        raise ScenarioError(f"Province input does not exist: {province_input}")

    try:
        collection = json.loads(province_input.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ScenarioError(f"Province input is not valid JSON: {province_input}: {exc}") from exc
    except OSError as exc:
        raise ScenarioError(f"Unable to read province input {province_input}: {exc}") from exc

    if not isinstance(collection, dict) or collection.get("type") != "FeatureCollection":
        raise ScenarioError(f"Province input must be a GeoJSON FeatureCollection: {province_input}")
    features = collection.get("features")
    if not isinstance(features, list) or not features:
        raise ScenarioError(f"Province input has no features: {province_input}")

    land_features = [
        feature
        for feature in features
        if isinstance(feature, dict)
        and isinstance(feature.get("properties"), dict)
        and feature["properties"].get("kind", "land") in (None, "land")
    ]
    if not land_features:
        raise ScenarioError(f"Province input has no land features: {province_input}")

    records, stats = resolve_ownership_records(
        scenario,
        land_features,
        allow_unknown_overrides=allow_unknown_overrides,
    )

    out_root = (output_dir or (PROCESSED_SCENARIO_DIR / actual_id)).resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(UTC).replace(microsecond=0).isoformat()

    ownership_csv = out_root / "ownership.csv"
    ownership_json = out_root / "ownership.json"
    countries_json = out_root / "countries.json"
    manifest_path = out_root / "scenario_manifest.json"

    _write_ownership_csv(ownership_csv, records)
    countries = _resolved_countries(scenario, records)
    _write_json(
        ownership_json,
        {
            "schema_version": SCENARIO_SCHEMA_VERSION,
            "milestone": "M8",
            "scenario_id": actual_id,
            "profile_id": profile_id,
            "era": scenario["era"],
            "start_date": scenario["start_date"],
            "end_date": scenario.get("end_date"),
            "generated_at": generated_at,
            "generator_version": __version__,
            "count": len(records),
            "records": records,
        },
    )
    _write_json(
        countries_json,
        {
            "schema_version": SCENARIO_SCHEMA_VERSION,
            "milestone": "M8",
            "scenario_id": actual_id,
            "generated_at": generated_at,
            "count": len(countries),
            "countries": countries,
        },
    )

    files_written = sorted(
        [
            ownership_csv.name,
            ownership_json.name,
            countries_json.name,
            manifest_path.name,
        ]
    )
    manifest = {
        "schema_version": SCENARIO_SCHEMA_VERSION,
        "milestone": "M8",
        "scenario_id": actual_id,
        "label": scenario["label"],
        "era": scenario["era"],
        "start_date": scenario["start_date"],
        "end_date": scenario.get("end_date"),
        "description": scenario.get("description"),
        "profile_id": profile_id,
        "generated_at": generated_at,
        "generator_version": __version__,
        "scenario_definition": scenario.get("_path"),
        "province_input": str(province_input),
        "allow_unknown_overrides": allow_unknown_overrides,
        "counts": {
            "land_provinces": len(land_features),
            "ownership_rows": len(records),
            "country_rule_hits": stats["country_rule_hits"],
            "region_rule_hits": stats["region_rule_hits"],
            "province_override_hits": stats["province_override_hits"],
            "baseline_only": stats["baseline_only_count"],
            "unknown_overrides": stats["unknown_override_count"],
            "owner_tags": stats["owner_tag_count"],
            "countries": len(countries),
        },
        "source_lineage": list(scenario.get("source_lineage") or []),
        "license_lineage": list(scenario.get("license_lineage") or []),
        "files": files_written,
        "notes": [
            "Historical ownership is a curated overlay; province geometry is unchanged.",
            "Assignment precedence: baseline ← country_rules ← region_rules ← province_overrides.",
            "Sea provinces are excluded from ownership tables.",
        ],
    }
    _write_json(manifest_path, manifest)

    return ScenarioBuildResult(
        scenario_id=actual_id,
        profile_id=profile_id,
        era=str(scenario["era"]),
        start_date=str(scenario["start_date"]),
        end_date=None if scenario.get("end_date") is None else str(scenario.get("end_date")),
        province_input=str(province_input),
        output_dir=str(out_root),
        ownership_csv=str(ownership_csv),
        ownership_json=str(ownership_json),
        countries_json=str(countries_json),
        scenario_manifest=str(manifest_path),
        land_province_count=len(land_features),
        ownership_row_count=len(records),
        country_rule_hits=stats["country_rule_hits"],
        region_rule_hits=stats["region_rule_hits"],
        province_override_hits=stats["province_override_hits"],
        baseline_only_count=stats["baseline_only_count"],
        unknown_override_count=stats["unknown_override_count"],
        owner_tag_count=stats["owner_tag_count"],
        files_written=tuple(files_written),
    )


def _summary_from_document(document: dict[str, Any], path: Path) -> ScenarioSummary:
    quality_tier = document.get("quality_tier")
    if quality_tier is not None:
        quality_tier = str(quality_tier).strip() or None
    recommended = document.get("recommended_profile")
    if recommended is not None:
        recommended = str(recommended).strip() or None
    return ScenarioSummary(
        scenario_id=str(document["scenario_id"]),
        label=str(document["label"]),
        era=str(document["era"]),
        start_date=str(document["start_date"]),
        end_date=None if document.get("end_date") is None else str(document.get("end_date")),
        path=str(path),
        country_rule_count=len(document.get("country_rules") or []),
        region_rule_count=len(document.get("region_rules") or []),
        province_override_count=len(document.get("province_overrides") or []),
        quality_tier=quality_tier,
        official_era=bool(document.get("official_era", False)),
        recommended_profile=recommended,
    )


def _validate_bulk_rule(rule: Any, path: str, *, match_key: str) -> None:
    if not isinstance(rule, dict):
        raise ScenarioError(f"{path} must be an object")
    match_value = rule.get(match_key)
    if not isinstance(match_value, str) or not match_value.strip():
        raise ScenarioError(f"{path}.{match_key} must be a non-empty string")
    _validate_ownership_fields(rule, path, require_owner=False)


def _validate_province_override(override: Any, path: str) -> None:
    if not isinstance(override, dict):
        raise ScenarioError(f"{path} must be an object")
    province_id = override.get("province_id")
    if not isinstance(province_id, str) or not province_id.strip():
        raise ScenarioError(f"{path}.province_id must be a non-empty string")
    _validate_ownership_fields(override, path, require_owner=False)


def _validate_ownership_fields(document: dict[str, Any], path: str, *, require_owner: bool) -> None:
    if require_owner:
        owner = document.get("owner")
        if not isinstance(owner, str) or not owner.strip():
            raise ScenarioError(f"{path}.owner must be a non-empty string")
    for key in ("owner", "controller"):
        if key in document and document[key] is not None:
            value = document[key]
            if not isinstance(value, str) or not value.strip():
                raise ScenarioError(f"{path}.{key} must be a non-empty string when present")
    for key in ("cores", "claims"):
        if key not in document or document[key] is None:
            continue
        value = document[key]
        if not isinstance(value, list) or not all(
            isinstance(item, str) and item.strip() for item in value
        ):
            raise ScenarioError(f"{path}.{key} must be a list of non-empty strings")
    for key in ("culture", "religion", "notes"):
        if key not in document or document[key] is None:
            continue
        if not isinstance(document[key], str):
            raise ScenarioError(f"{path}.{key} must be a string or null")
    if "disputed" in document and document["disputed"] is not None:
        if not isinstance(document["disputed"], bool):
            raise ScenarioError(f"{path}.disputed must be a boolean")


def _apply_fields(
    patch: dict[str, Any],
    *,
    owner: str,
    controller: str,
    cores: list[str],
    claims: list[str],
    culture: str | None,
    religion: str | None,
    disputed: bool,
    notes: str | None,
) -> tuple[str, str, list[str], list[str], str | None, str | None, bool, str | None]:
    if "owner" in patch and patch["owner"] is not None:
        owner = str(patch["owner"]).strip()
        # Controller follows owner unless explicitly set on this patch.
        if "controller" not in patch or patch["controller"] is None:
            controller = owner
    if "controller" in patch and patch["controller"] is not None:
        controller = str(patch["controller"]).strip()
    if "cores" in patch and patch["cores"] is not None:
        cores = [str(item).strip() for item in patch["cores"] if str(item).strip()]
    if "claims" in patch and patch["claims"] is not None:
        claims = [str(item).strip() for item in patch["claims"] if str(item).strip()]
    if "culture" in patch:
        culture = _nullable_str(patch["culture"])
    if "religion" in patch:
        religion = _nullable_str(patch["religion"])
    if "disputed" in patch and patch["disputed"] is not None:
        disputed = bool(patch["disputed"])
    if "notes" in patch and patch["notes"] is not None:
        notes = str(patch["notes"])
    return owner, controller, cores, claims, culture, religion, disputed, notes


def _resolved_countries(
    scenario: dict[str, Any],
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    declared = scenario.get("countries") if isinstance(scenario.get("countries"), dict) else {}
    tags: set[str] = set()
    for record in records:
        tags.add(record["owner"])
        tags.add(record["controller"])
        tags.update(record["cores"])
        tags.update(record["claims"])
    countries: list[dict[str, Any]] = []
    for tag in sorted(tags):
        meta = declared.get(tag) if isinstance(declared.get(tag), dict) else {}
        display = meta.get("display_name") if isinstance(meta, dict) else None
        if not isinstance(display, str) or not display.strip():
            display = tag
        entry: dict[str, Any] = {
            "tag": tag,
            "display_name": display,
        }
        if isinstance(meta, dict) and isinstance(meta.get("notes"), str):
            entry["notes"] = meta["notes"]
        countries.append(entry)
    return countries


def _write_ownership_csv(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(OWNERSHIP_CSV_FIELDS))
        writer.writeheader()
        for record in records:
            row = {
                "province_id": record["province_id"],
                "scenario_id": record["scenario_id"],
                "start_date": record["start_date"],
                "end_date": "" if record["end_date"] is None else record["end_date"],
                "owner": record["owner"],
                "controller": record["controller"],
                "cores": json.dumps(record["cores"], ensure_ascii=False),
                "claims": json.dumps(record["claims"], ensure_ascii=False),
                "culture": "" if record["culture"] is None else record["culture"],
                "religion": "" if record["religion"] is None else record["religion"],
                "disputed": "true" if record["disputed"] else "false",
                "assignment_source": record["assignment_source"],
                "parent_country_id": record["parent_country_id"] or "",
                "parent_region_id": record["parent_region_id"] or "",
                "display_name": record["display_name"] or "",
                "notes": record["notes"] or "",
            }
            writer.writerow(row)


def _write_json(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _nullable_str(value: Any) -> str | None:
    """Normalize optional string fields from GeoJSON / shapefile sources.

    Natural Earth DBF fields are often fixed-width and arrive with trailing
    NUL bytes. Strip those so region/country rule matching works against clean
    ids such as ``FR-01`` or ``DE-BY``.
    """
    if isinstance(value, str):
        text = value.replace("\x00", "").strip()
        if text:
            return text
    return None


def _unique_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered
