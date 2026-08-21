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
NATURAL_EARTH_SHA256 = "ce1ac7036499a0edd641fbc093cd209a98f96a49d2eca8480aaacad35138a7f6"
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
}


def _canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _archive_hash() -> str:
    return hashlib.sha256(COUNTRIES.read_bytes()).hexdigest()


def extract_control(region_id: str):
    """Return the non-empty shared Admin-0 boundary for one approved code pair."""
    left_code, right_code, _suffix = CONTROLS[region_id]
    countries = {
        str(feature.properties["ADM0_A3"]).rstrip("\x00"): shape(feature.geometry)
        for feature in read_zipped_shapefile(COUNTRIES)
    }
    missing = {left_code, right_code} - set(countries)
    if missing:
        raise SystemExit(f"Natural Earth control {region_id} is missing country codes: {sorted(missing)}")
    seam = countries[left_code].boundary.intersection(countries[right_code].boundary)
    if seam.is_empty or not seam.is_valid or seam.geom_type not in {"LineString", "MultiLineString"} or seam.length <= 0:
        raise SystemExit(f"Natural Earth control {region_id} has no non-empty shared inland boundary")
    return seam


def add_negative_control(packet: dict[str, Any], output: Path, *, retire_region_015: bool = False) -> dict[str, Any]:
    """Add one reviewed modern seam and, for 015, retire its circular legacy gate."""
    region_id = packet["region_id"]
    left_code, right_code, suffix = CONTROLS[region_id]
    if _archive_hash() != NATURAL_EARTH_SHA256:
        raise SystemExit("pinned Natural Earth Admin-0 5.1.1 archive checksum drifted")

    if retire_region_015:
        _retire_region_015(packet, output)

    source_id = f"natural-earth-admin0-5.1.1-region-{region_id}"
    boundary_id = f"forbidden-modern-{suffix}"
    assertion_id = f"region-{region_id}-negative-modern-{suffix}"
    asset_id = f"region-{region_id}-negative-controls"
    asset_relative = f"assets/{region_id}/negative-controls.geojson"
    asset_target = f"regional-assets/{region_id}/negative-controls.geojson"
    locator = f"Admin-0 countries 5.1.1 > ADM0_A3 shared boundary {left_code}-{right_code}"
    seam = extract_control(region_id)

    boundary = {
        "type": "Feature",
        "properties": {
            "feature_id": boundary_id,
            "geometry_revision": "natural-earth-5.1.1",
            "valid_from": "2022",
            "valid_to": None,
            "date_precision": "year",
            "semantics": f"Modern inland Admin-0 seam between {left_code} and {right_code}; negative control only.",
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
        "citation": "Natural Earth, Admin 0 – Countries, version 5.1.1.",
        "url": "https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-0-countries/",
        "access_date": packet["as_of_date"],
        "version": "5.1.1 (2022)",
        "license": "Public domain",
        "checksum": NATURAL_EARTH_SHA256,
        "transformations": [f"Extracted the shared {left_code}-{right_code} polygon boundary; coastlines excluded automatically."],
        "review_status": "reviewed",
        "source_type": "negative_control",
        "valid_from": "2022",
        "valid_to": None,
        "independence_group": f"natural-earth-admin0-modern-control-{region_id}",
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


def _retire_region_015(packet: dict[str, Any], output: Path) -> None:
    assertion_id = "region-015-border-marinid-zayyanid"
    boundary_id = "region-015-marinid-zayyanid-frontier"
    derived_ids = {
        "derived-region-015-marinid-zayyanid-frontier",
        "derived-region-015-polity-masks",
    }
    packet["assertions"] = [row for row in packet["assertions"] if row["assertion_id"] != assertion_id]
    packet["boundary_features"] = [
        row for row in packet["boundary_features"] if row["properties"]["feature_id"] != boundary_id
    ]
    packet["derived_files"] = [
        row for row in packet["derived_files"] if row["asset_id"] not in {
            "region-015-boundaries", "region-015-polity-masks"
        }
    ]
    for source in packet["sources"]:
        source["derived_artifacts"] = [
            row for row in source.get("derived_artifacts") or [] if row["artifact_id"] not in derived_ids
        ]
    for row in packet["coverage"]:
        row["assertion_ids"] = [value for value in row["assertion_ids"] if value != assertion_id]
    packet["expected_counts"]["assertions"] -= 1
    packet["expected_counts"]["derived_files"] -= 2
    for filename in ("boundaries.geojson", "polity-masks.geojson"):
        path = output.parent / "assets" / "015" / filename
        if path.exists():
            path.unlink()
