"""Deterministic Natural Earth inland-seam controls for M25C regional packets."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from shapely.geometry import mapping, shape

from gpm.geo.shapefile import read_zipped_shapefile
from gpm.historical.packet_migration import migrate_packet


ROOT = Path(__file__).resolve().parents[1]
COUNTRIES = ROOT / "data/raw/natural_earth/ne_10m_admin_0_countries.zip"
STATES_PROVINCES = ROOT / "data/raw/natural_earth/ne_10m_admin_1_states_provinces.zip"
NATURAL_EARTH_SHA256 = "ce1ac7036499a0edd641fbc093cd209a98f96a49d2eca8480aaacad35138a7f6"
NATURAL_EARTH_ADMIN1_SHA256 = "efc59726337323058f9446210adc96673179cd344e053666ee3d28cb58ba2b05"
RELATION = "regional_status_boundary_matches_forbidden_modern_seam_ratio_lte"

CONTROLS = {
    "005": ("PER", "BOL", "peru-bolivia-seam"),
    "011": ("MLI", "NER", "mali-niger-seam"),
    "013": ("MEX", "GTM", "mexico-guatemala-seam"),
    "014": ("ETH", "SOM", "ethiopia-somalia-seam"),
    "015": ("MAR", "DZA", "morocco-algeria-seam"),
    "017": ("AGO", "COD", "angola-drc-seam"),
    "018": ("BWA", "ZAF", "botswana-south-africa-seam"),
    "021": ("USA", "CAN", "us-canada-seam"),
    "029": ("HTI", "DOM", "haiti-dominican-seam"),
    "030": ("CHN", "MNG", "china-mongolia-seam"),
    "034": ("IND", "BGD", "india-bangladesh-seam"),
    "035": ("THA", "MMR", "thailand-myanmar-seam"),
    "039": ("ITA", "SVN", "italy-slovenia-seam"),
    "143": ("KAZ", "UZB", "kazakhstan-uzbekistan-seam"),
    "145": ("SAU", "YEM", "saudi-arabia-yemen-seam"),
    "053": ("AU-WA", "AU-SA", "western-australia-south-australia-seam"),
    "054": ("PG-CPM", "PG-NCD", "central-province-national-capital-district-seam"),
    "057": ("NR-14", "NR-11", "yaren-meneng-seam"),
    "061": ("AS-X05~", "AS-X01~", "american-samoa-western-eastern-district-seam"),
}

ADMIN1_CONTROLS = frozenset({"053", "054", "057", "061"})

RETIREMENTS = {
    "015": {
        "assertion_id": "region-015-border-marinid-zayyanid",
        "boundary_id": "region-015-marinid-zayyanid-frontier",
        "asset_ids": {"region-015-boundaries", "region-015-polity-masks"},
        "artifact_ids": {
            "derived-region-015-marinid-zayyanid-frontier",
            "derived-region-015-polity-masks",
        },
        "filenames": {"boundaries.geojson", "polity-masks.geojson"},
    },
    "030": {
        "assertion_id": "region-030-border-ming-oirat",
        "boundary_id": "region-030-ming-oirat-frontier",
        "asset_ids": {"region-030-boundaries"},
        "artifact_ids": {"derived-region-030-ming-oirat-frontier"},
        "filenames": {"boundaries.geojson"},
    },
    "034": {
        "assertion_id": "region-034-border-bahmani-vijayanagara",
        "boundary_id": "region-034-bahmani-vijayanagara-frontier",
        "asset_ids": {"region-034-boundaries"},
        "artifact_ids": {"derived-region-034-bahmani-vijayanagara-frontier"},
        "filenames": {"boundaries.geojson"},
    },
    "035": {
        "assertion_id": "region-035-border-ayutthaya-cambodia",
        "boundary_id": "region-035-ayutthaya-cambodia-frontier",
        "asset_ids": {"region-035-boundaries"},
        "artifact_ids": {"derived-region-035-ayutthaya-cambodia-frontier"},
        "filenames": {"boundaries.geojson"},
    },
    "143": {
        "assertion_id": "region-143-border-timurid-moghulistan",
        "boundary_id": "region-143-timurid-moghulistan-frontier",
        "asset_ids": {"region-143-boundaries"},
        "artifact_ids": {"derived-region-143-timurid-moghulistan-frontier"},
        "filenames": {"boundaries.geojson"},
    },
    "145": {
        "assertion_id": "region-145-border-ottoman-qara-qoyunlu",
        "boundary_id": "region-145-ottoman-qara-qoyunlu-frontier",
        "asset_ids": {"region-145-boundaries", "region-145-polity-masks"},
        "artifact_ids": {
            "derived-region-145-ottoman-qara-qoyunlu-frontier",
            "derived-region-145-ottoman-qara-qoyunlu-mask",
        },
        "filenames": {"boundaries.geojson", "polity-masks.geojson"},
    },
}


def _canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _archive_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_control(region_id: str):
    """Return the non-empty shared modern boundary for one approved code pair."""
    left_code, right_code, _suffix = CONTROLS[region_id]
    is_admin1 = region_id in ADMIN1_CONTROLS
    archive = STATES_PROVINCES if is_admin1 else COUNTRIES
    code_field = "iso_3166_2" if is_admin1 else "ADM0_A3"
    units = {
        str(feature.properties[code_field]).rstrip("\x00"): shape(feature.geometry)
        for feature in read_zipped_shapefile(archive)
    }
    missing = {left_code, right_code} - set(units)
    if missing:
        raise SystemExit(f"Natural Earth control {region_id} is missing unit codes: {sorted(missing)}")
    seam = units[left_code].boundary.intersection(units[right_code].boundary)
    if seam.is_empty or not seam.is_valid or seam.geom_type not in {"LineString", "MultiLineString"} or seam.length <= 0:
        raise SystemExit(f"Natural Earth control {region_id} has no non-empty shared inland boundary")
    return seam


def add_negative_control(packet: dict[str, Any], output: Path) -> dict[str, Any]:
    """Retire configured circular gates and add one reviewed modern seam."""
    region_id = packet["region_id"]
    left_code, right_code, suffix = CONTROLS[region_id]
    is_admin1 = region_id in ADMIN1_CONTROLS
    archive = STATES_PROVINCES if is_admin1 else COUNTRIES
    archive_sha256 = NATURAL_EARTH_ADMIN1_SHA256 if is_admin1 else NATURAL_EARTH_SHA256
    admin_level = "Admin-1" if is_admin1 else "Admin-0"
    source_slug = "admin1" if is_admin1 else "admin0"
    source_title = "Admin 1 – States, Provinces" if is_admin1 else "Admin 0 – Countries"
    source_url = (
        "https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-1-states-provinces/"
        if is_admin1 else
        "https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-0-countries/"
    )
    if _archive_hash(archive) != archive_sha256:
        raise SystemExit(f"pinned Natural Earth {admin_level} 5.1.1 archive checksum drifted")

    if region_id in RETIREMENTS:
        _retire_legacy_assertion(packet, output, RETIREMENTS[region_id])

    retired_artifact_ids = {
        artifact_id
        for retirement in RETIREMENTS.values()
        for artifact_id in retirement["artifact_ids"]
    }
    for source in packet["sources"]:
        source["derived_artifacts"] = [
            row for row in source.get("derived_artifacts") or []
            if row["artifact_id"] not in retired_artifact_ids
        ]

    source_id = f"natural-earth-{source_slug}-5.1.1-region-{region_id}"
    boundary_id = f"forbidden-modern-{suffix}"
    assertion_id = f"region-{region_id}-negative-modern-{suffix}"
    asset_id = f"region-{region_id}-negative-controls"
    asset_relative = f"assets/{region_id}/negative-controls.geojson"
    asset_target = f"regional-assets/{region_id}/negative-controls.geojson"
    code_field = "ISO_3166_2" if is_admin1 else "ADM0_A3"
    locator = f"{admin_level} 5.1.1 > {code_field} shared boundary {left_code}-{right_code}"
    seam = extract_control(region_id)

    boundary = {
        "type": "Feature",
        "properties": {
            "feature_id": boundary_id,
            "geometry_revision": "natural-earth-5.1.1",
            "valid_from": "2022",
            "valid_to": None,
            "date_precision": "year",
            "semantics": f"Modern inland {admin_level} seam between {left_code} and {right_code}; negative control only.",
            "side_polity_ids": None,
            "reference_unit_ids": [left_code, right_code],
            "source_ids": [source_id],
            "license_lineage": ["Natural Earth public domain"],
            "confidence": "high",
            "uncertainty_notes": "Shared polygon boundary excludes coastlines by construction.",
            "classification": "soft_evidence",
            "geographic_scope": region_id,
            "start_date_programs": [packet["start_date"]],
        },
        "geometry": mapping(seam),
    }
    asset = {"type": "FeatureCollection", "features": [boundary]}
    data = (json.dumps(asset, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    asset_path = output.parent / asset_relative
    asset_path.parent.mkdir(parents=True, exist_ok=True)
    asset_path.write_bytes(data)
    asset_sha256 = hashlib.sha256(data).hexdigest()

    source = {
        "source_id": source_id,
        "citation": f"Natural Earth, {source_title}, version 5.1.1.",
        "url": source_url,
        "access_date": packet["as_of_date"],
        "version": "5.1.1 (2022)",
        "license": "Public domain",
        "checksum": archive_sha256,
        "transformations": [f"Extracted the shared {left_code}-{right_code} polygon boundary; coastlines excluded automatically."],
        "review_status": "reviewed",
        "source_type": "negative_control",
        "valid_from": "2022",
        "valid_to": None,
        "independence_group": f"natural-earth-{source_slug}-modern-control-{region_id}",
        "derived_artifacts": [{
            "artifact_id": asset_id,
            "role": "negative_control_geometry",
            "path": asset_target,
            "sha256": asset_sha256,
            "media_type": "application/geo+json",
        }],
    }
    assertion = {
        "assertion_id": assertion_id,
        "region_id": region_id,
        "layer": "geometry",
        "assertion_type": "seam",
        "expectation": "negative_anachronism",
        "subject_ids": [region_id],
        "boundary_feature_ids": [boundary_id],
        "spatial_relation": RELATION,
        "unit": "ratio",
        "tolerance": 0.20,
        "measurement_parameters": {"corridor_km": 75},
        "tolerance_policy": {
            "fixed_before_measurement": True,
            "source_derived_tolerance": 0.20,
            "source_ids": [source_id],
        },
        "notes": f"Fail when compositional status transitions reproduce more than 20% of the modern {left_code}-{right_code} inland seam.",
    }
    derived = {
        "asset_id": asset_id,
        "path": asset_relative,
        "target_path": asset_target,
        "sha256": asset_sha256,
        "source_ids": [source_id],
        "valid_from": "2022",
        "valid_to": None,
        "role": "negative_control_geometry",
    }

    packet["sources"].append(source)
    packet["source_pins"].append({
        "source_id": source_id,
        "locator": locator,
        "sha256": _canonical_hash({"locator": locator, "source": source}),
    })
    locator_by_source = {row["source_id"]: row["locator"] for row in packet["source_pins"]}
    packet["source_pins"] = [
        {
            "source_id": row["source_id"],
            "locator": locator_by_source[row["source_id"]],
            "sha256": _canonical_hash({"locator": locator_by_source[row["source_id"]], "source": row}),
        }
        for row in packet["sources"]
    ]
    packet["boundary_features"].append(boundary)
    packet["assertions"].append(assertion)
    packet["derived_files"].append(derived)
    geometry_row = next(row for row in packet["coverage"] if row["layer"] == "geometry")
    geometry_row["assertion_ids"].append(assertion_id)
    packet["expected_counts"]["sources"] += 1
    packet["expected_counts"]["assertions"] += 1
    packet["expected_counts"]["derived_files"] += 1
    return migrate_packet(packet)


def _retire_legacy_assertion(packet: dict[str, Any], output: Path, retirement: dict[str, Any]) -> None:
    assertion_id = retirement["assertion_id"]
    boundary_id = retirement["boundary_id"]
    packet["assertions"] = [row for row in packet["assertions"] if row["assertion_id"] != assertion_id]
    packet["boundary_features"] = [
        row for row in packet["boundary_features"] if row["properties"]["feature_id"] != boundary_id
    ]
    packet["derived_files"] = [
        row for row in packet["derived_files"] if row["asset_id"] not in retirement["asset_ids"]
    ]
    for source in packet["sources"]:
        source["derived_artifacts"] = [
            row for row in source.get("derived_artifacts") or []
            if row["artifact_id"] not in retirement["artifact_ids"]
        ]
    for row in packet["coverage"]:
        row["assertion_ids"] = [value for value in row["assertion_ids"] if value != assertion_id]
    packet["expected_counts"]["assertions"] -= 1
    packet["expected_counts"]["derived_files"] -= len(retirement["asset_ids"])
    for filename in retirement["filenames"]:
        path = output.parent / "assets" / packet["region_id"] / filename
        if path.exists():
            path.unlink()
