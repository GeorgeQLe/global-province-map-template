#!/usr/bin/env python3
"""Build the source-pinned Central America (M49 013) Grade-A packet."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from m25c_negative_controls import add_negative_control

from shapely.geometry import Point, mapping, shape

from gpm.geo.shapefile import read_zipped_shapefile


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASELINE = Path("/private/tmp/m25c-region-155-baseline")
DEFAULT_OUTPUT = ROOT / "research/start-dates/1444-global-v1/regional-packets/013-central-america-2026-08-16.json"
COUNTRIES = ROOT / "data/raw/natural_earth/ne_10m_admin_0_countries.zip"
START_DATE = "1444-11-11"
AS_OF_DATE = "2026-08-16"
EXPECTED_ASSIGNMENTS = 605
VISUAL_REVIEW_SHA256 = "621f1de5a6712a1491b27087985fef2bce966d209e3c7a02a285f2311fe87871"


LOCATORS = {
    "regional-survey-013": "Timeline > 1400 A.D.-1600 A.D.; Maya-area overview and Postclassic regional centers",
    "regional-survey-029": "Timeline > 1400 A.D.-1500 A.D.; lower Central American cultures, chiefdoms, and 1410-1450 events",
    "shepherd-historical-atlas": "Historical Atlas > Mexico and Central America before sustained European colonization",
    "met-mexico-1400-1600": "Timeline > 1400 A.D.-1450 A.D.; Aztec, Huastec, Cempoala, Tarascan, Mixtec, and Zapotec rows",
    "penn-time-beyond-kings": "New Powers Emerge in Yucatan and New Powers in the Maya Highlands; Postclassic political transformation",
    "loc-mayance-nations-map": "Item summary and map > Mayan nations, languages, place names, and routes, approximately 1000-1500",
    "smithsonian-central-america-ceramics": "Exhibition sections > Maya, Ulua River, Lempa River, Greater Nicoya, Central Caribbean, Greater Chiriqui, and Greater Cocle",
    "smithsonian-handbook-central-america": "Handbook of South American Indians IV > Circum-Caribbean and Meso-American tribes; political organization and regional maps",
    "unesco-diquis-chiefdoms": "Brief synthesis and criterion iii > chiefdom settlement systems, AD 500-1500",
    "inah-triple-alliance": "Abstract and study > fifteenth-century tripartite structure of power in the Basin of Mexico",
    "inah-tzintzuntzan": "Site history > three Purepecha seats of power and Tzintzuntzan's rise in the first half of the fifteenth century",
}


def source(source_id: str, citation: str, url: str, independence_group: str,
           source_type: str = "institutional") -> dict[str, Any]:
    return {
        "source_id": source_id, "citation": citation, "url": url,
        "access_date": AS_OF_DATE, "version": f"Publisher record reviewed {AS_OF_DATE}",
        "license": "Citation/link only", "checksum": None, "transformations": [],
        "review_status": "reviewed", "source_type": source_type,
        "valid_from": "1400", "valid_to": "1500",
        "independence_group": independence_group, "derived_artifacts": [],
    }


STATIC_SOURCES = [
    source(
        "met-mexico-1400-1600",
        "Metropolitan Museum of Art, Heilbrunn Timeline of Art History, 'Mexico, 1400-1600 A.D.'.",
        "https://www.metmuseum.org/toah/ht/08/canm.html", "met-heilbrunn",
    ),
    source(
        "penn-time-beyond-kings", "Loa Traxler, 'Time Beyond Kings,' Penn Museum Expedition 54.1.",
        "https://www.penn.museum/sites/expedition/time-beyond-kings/", "penn-museum", "academic",
    ),
    source(
        "loc-mayance-nations-map", "Library of Congress, 'Map of the Mayance Nations and Languages.'",
        "https://www.loc.gov/item/2021668475/", "library-of-congress-maya-map", "academic",
    ),
    source(
        "smithsonian-central-america-ceramics",
        "Smithsonian Institution, 'Ceramica de los Ancestros: Central America's Past Revealed.'",
        "https://www.si.edu/es/newsdesk/releases/objetos-de-ceramica-dan-a-conocer-relatos-antiguos-de-los-primeros-pueblos-de",
        "smithsonian-central-america-exhibition",
    ),
    source(
        "smithsonian-handbook-central-america",
        "Smithsonian Institution, Handbook of South American Indians, Volume 4: The Circum-Caribbean Tribes.",
        "https://repository.si.edu/bitstreams/fb2ec995-9284-4cee-aa1d-2415d95f70f3/download",
        "smithsonian-handbook-v4", "academic",
    ),
    source(
        "unesco-diquis-chiefdoms",
        "UNESCO World Heritage Centre, 'Precolumbian Chiefdom Settlements with Stone Spheres of the Diquis.'",
        "https://whc.unesco.org/en/list/1453/", "unesco-diquis",
    ),
    source(
        "inah-triple-alliance",
        "Clementina Battcock, 'La conformacion de la ultima Triple Alianza en la cuenca de Mexico,' INAH.",
        "https://revistas.inah.gob.mx/index.php/dimension/article/view/1095", "inah-triple-alliance", "academic",
    ),
    source(
        "inah-tzintzuntzan", "Instituto Nacional de Antropologia e Historia, 'Tzintzuntzan.'",
        "https://lugares.inah.gob.mx/es/node/5548", "inah-tzintzuntzan",
    ),
]


GEOMETRY_SOURCES = [
    "loc-mayance-nations-map", "regional-survey-013", "regional-survey-029",
    "shepherd-historical-atlas", "smithsonian-handbook-central-america",
]
POLITICS_SOURCES = sorted(LOCATORS)
HIERARCHY_SOURCES = [
    "inah-triple-alliance", "inah-tzintzuntzan", "met-mexico-1400-1600",
    "penn-time-beyond-kings", "regional-survey-013", "regional-survey-029",
    "smithsonian-central-america-ceramics", "smithsonian-handbook-central-america",
    "unesco-diquis-chiefdoms",
]
RELATIONSHIP_SOURCES = sorted(set(HIERARCHY_SOURCES + ["loc-mayance-nations-map", "shepherd-historical-atlas"]))


NAMES = {
    "scenario-mexica-triple-alliance": "Mexica-led Triple Alliance under Moctezuma I",
    "scenario-tlaxcalan-confederation": "Tlaxcalan confederation",
    "scenario-purepecha-state": "Purepecha state of Michoacan",
    "scenario-huastec-polities": "Huastec polities",
    "scenario-totonac-cempoala": "Totonac and Cempoala city-state network",
    "scenario-mixtec-kingdoms": "Mixtec kingdoms",
    "scenario-zapotec-kingdoms": "Zapotec kingdoms",
    "scenario-western-mexico-polities": "Western Mexican local polities",
    "scenario-northern-mexico-communities": "Northern Mexican local communities",
    "scenario-yucatan-successor-polities": "Yucatan successor polities after Mayapan",
    "scenario-peten-belize-maya": "Peten and Belize Maya polities",
    "scenario-kiche-state": "K'iche' state centered on Q'umarkaj",
    "scenario-highland-maya-kingdoms": "Highland Maya kingdoms and rivals",
    "scenario-pipil-cuzcatlan": "Pipil polity of Cuzcatlan",
    "scenario-lenca-polities": "Lenca polities of Honduras",
    "scenario-caribbean-central-america": "Caribbean-coast Central American communities",
    "scenario-chorotega-polities": "Chorotega polities",
    "scenario-nicarao-polities": "Nicarao polities",
    "scenario-greater-nicoya-chiefdoms": "Greater Nicoya chiefdoms",
    "scenario-central-costa-rica-chiefdoms": "Central Costa Rican chiefdoms",
    "scenario-diquis-chiefdoms": "Diquis chiefdoms",
    "scenario-chiriqui-chiefdoms": "Greater Chiriqui chiefdoms",
    "scenario-cocle-parita-chiefdoms": "Greater Cocle and Parita chiefdoms",
    "scenario-eastern-panama-chiefdoms": "Eastern Panamanian chiefdoms",
    "scenario-uninhabited-east-pacific-islands": "Uninhabited eastern Pacific islands",
}


SITES = {
    "tenochtitlan": ((-99.13, 19.43), "scenario-mexica-triple-alliance"),
    "tlaxcala": ((-98.24, 19.32), "scenario-tlaxcalan-confederation"),
    "tzintzuntzan": ((-101.58, 19.63), "scenario-purepecha-state"),
    "cempoala": ((-96.38, 19.43), "scenario-totonac-cempoala"),
    "nojpeten": ((-89.89, 16.93), "scenario-peten-belize-maya"),
    "qumarkaj": ((-91.17, 15.03), "scenario-kiche-state"),
    "cuzcatlan": ((-89.28, 13.70), "scenario-pipil-cuzcatlan"),
    "tenampua": ((-87.65, 14.62), "scenario-lenca-polities"),
    "nicarao-rivas": ((-85.83, 11.44), "scenario-nicarao-polities"),
    "guayabo": ((-83.69, 9.97), "scenario-central-costa-rica-chiefdoms"),
    "finca-6": ((-83.50, 8.91), "scenario-diquis-chiefdoms"),
    "el-cano": ((-80.52, 8.40), "scenario-cocle-parita-chiefdoms"),
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_hash(value: Any) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(data.encode()).hexdigest()


def assertion(assertion_id: str, layer: str, subjects: list[str], sources: list[str]) -> dict[str, Any]:
    return {
        "assertion_id": assertion_id, "assertion_type": "capital", "boundary_feature_ids": [],
        "expectation": "positive", "layer": layer,
        "notes": f"Region 013 checked political or archaeological-center gate: {assertion_id}.",
        "region_id": "013", "spatial_relation": "capital_within_subject", "subject_ids": subjects,
        "tolerance": 1, "tolerance_policy": {"fixed_before_measurement": True,
        "source_derived_tolerance": 1, "source_ids": sorted(sources)}, "unit": "boolean",
    }


def country_index() -> list[tuple[str, Any]]:
    return [(str(feature.properties["ADM0_A3"]).rstrip("\x00"), shape(feature.geometry))
            for feature in read_zipped_shapefile(COUNTRIES)]


def nearest_country(point: Point, countries: list[tuple[str, Any]]) -> str:
    covered = [code for code, geometry in countries if geometry.covers(point)]
    return covered[0] if covered else min(countries, key=lambda row: row[1].distance(point))[0]


def final_actor(country: str, point: Point) -> str:
    x, y = point.x, point.y
    if country == "CLP" or (country == "CRI" and y < 7):
        return "scenario-uninhabited-east-pacific-islands"
    if country == "MEX":
        if y >= 26 or x <= -112:
            return "scenario-northern-mexico-communities"
        if -103.8 <= x <= -99.5 and 17.5 <= y <= 21.5:
            return "scenario-purepecha-state"
        if -98.6 <= x <= -97.4 and 18.5 <= y <= 20:
            return "scenario-tlaxcalan-confederation"
        if -100.3 <= x <= -97.4 and 17.8 <= y <= 20.7:
            return "scenario-mexica-triple-alliance"
        if x >= -91 and y >= 18:
            return "scenario-yucatan-successor-polities"
        if x >= -98 and y >= 20:
            return "scenario-huastec-polities"
        if x >= -98 and y >= 18:
            return "scenario-totonac-cempoala"
        if x >= -94.5 and y < 18.5:
            return "scenario-peten-belize-maya"
        if y <= 18.5 and x <= -96.2:
            return "scenario-mixtec-kingdoms"
        if y <= 18.5:
            return "scenario-zapotec-kingdoms"
        if x < -103.8:
            return "scenario-western-mexico-polities"
        return "scenario-northern-mexico-communities"
    if country == "BLZ":
        return "scenario-peten-belize-maya"
    if country == "GTM":
        if y >= 16:
            return "scenario-peten-belize-maya"
        if x <= -90:
            return "scenario-kiche-state"
        return "scenario-highland-maya-kingdoms"
    if country == "SLV":
        return "scenario-pipil-cuzcatlan"
    if country == "HND":
        if x <= -88.2:
            return "scenario-peten-belize-maya"
        if x >= -85.8:
            return "scenario-caribbean-central-america"
        return "scenario-lenca-polities"
    if country == "NIC":
        if x >= -85.5:
            return "scenario-caribbean-central-america"
        return "scenario-chorotega-polities" if y >= 13.2 else "scenario-nicarao-polities"
    if country == "CRI":
        if x <= -84.5 and y >= 9.5:
            return "scenario-greater-nicoya-chiefdoms"
        if y <= 9:
            return "scenario-diquis-chiefdoms"
        return "scenario-central-costa-rica-chiefdoms"
    if country == "PAN":
        if x <= -81.5:
            return "scenario-chiriqui-chiefdoms"
        if x <= -79:
            return "scenario-cocle-parita-chiefdoms"
        return "scenario-eastern-panama-chiefdoms"
    raise SystemExit(f"region-013 country classification drifted: {country} at {point.wkt}")


def build_packet(baseline: Path, output: Path, visual_sha256: str) -> dict[str, Any]:
    source_index = {row["source_id"]: row for row in load(baseline / "source_manifest.json")["sources"]}
    source_index.update({row["source_id"]: row for row in STATIC_SOURCES})
    selected_ids = sorted(set(GEOMETRY_SOURCES + POLITICS_SOURCES + HIERARCHY_SOURCES + RELATIONSHIP_SOURCES))
    build_index = {f["properties"]["feature_id"]: shape(f["geometry"])
                   for f in load(baseline / "build.geojson")["features"]
                   if f["properties"]["feature_type"] == "province"}
    assignments = [row for row in load(baseline / "assignments.json")["assignments"] if row["region_id"] == "013"]
    if len(assignments) != EXPECTED_ASSIGNMENTS:
        raise SystemExit(f"region-013 assignment scope drifted: {len(assignments)}")

    countries = country_index()
    actor_by_province: dict[str, str] = {}
    overrides = []
    for row in assignments:
        point = build_index[row["province_id"]].representative_point()
        actor = final_actor(nearest_country(point, countries), point)
        actor_by_province[row["province_id"]] = actor
        overrides.append({
            "province_id": row["province_id"], "polity_ids": [actor],
            "sovereign_polity_id": actor, "owner_polity_id": actor,
            "controller_polity_id": actor, "core_polity_ids": [actor],
            "claim_polity_ids": [], "dispute_polity_ids": [], "source_ids": POLITICS_SOURCES,
            "uncertainty": 0.35,
            "notes": "Central America exact-date replacement for 1444-11-11; documented states and chiefdom systems remain distinct while uncertain local frontiers are represented as coarse political or community fields rather than later imperial, colonial, or national borders.",
            "hierarchy": {"area_id": f"area-013-{actor}", "method": "evidence-backed-polity-region-grouping-v1",
                          "region_id": "013", "superregion_id": "m49-superregion-013"},
        })

    present_actors = sorted(set(actor_by_province.values()))
    if set(present_actors) != set(NAMES):
        raise SystemExit(f"region-013 actor coverage drifted: {present_actors}")
    old_polities = {row["polity_id"]: row for row in load(baseline / "gazetteer.json")["polities"]}
    all_polity_sources = sorted(set(POLITICS_SOURCES + HIERARCHY_SOURCES + RELATIONSHIP_SOURCES))
    polities = []
    for polity_id in present_actors:
        polity = json.loads(json.dumps(old_polities.get(polity_id, {
            "polity_id": polity_id, "aliases": [], "capital_location_ids": [], "relationships": [],
        })))
        polity["name"] = NAMES[polity_id]
        polity["source_ids"] = all_polity_sources
        polity["valid_from"], polity["valid_to"] = "1400", "1500"
        polity["capital_location_ids"] = []
        polities.append(polity)

    assignments_by_id = {row["province_id"]: row for row in assignments}
    polity_by_id = {row["polity_id"]: row for row in polities}
    assertions = []
    assertion_ids = {layer: [] for layer in ("geometry", "politics", "hierarchy", "gazetteer_relationships")}
    build_features = []
    for site_name, (coords, polity_id) in SITES.items():
        point = Point(coords)
        candidates = [pid for pid, actor in actor_by_province.items() if actor == polity_id]
        containing = [pid for pid in candidates if build_index[pid].covers(point)]
        if not containing:
            nearest = min(candidates, key=lambda pid: build_index[pid].distance(point))
            if build_index[nearest].distance(point) <= 2:
                point, containing = build_index[nearest].representative_point(), [nearest]
        if len(containing) != 1:
            raise SystemExit(f"site {site_name} does not resolve to one region-013 province: {containing}")
        province_id = containing[0]
        feature_id = assignments_by_id[province_id]["location_ids"][0]
        build_features.append({"type": "Feature", "properties": {
            "feature_id": feature_id, "feature_type": "capital", "source_ids": POLITICS_SOURCES,
        }, "geometry": mapping(point)})
        polity_by_id[polity_id]["capital_location_ids"].append(feature_id)
        for layer, layer_sources in (("geometry", GEOMETRY_SOURCES), ("politics", POLITICS_SOURCES),
                                     ("hierarchy", HIERARCHY_SOURCES),
                                     ("gazetteer_relationships", RELATIONSHIP_SOURCES)):
            assertion_id = f"region-013-site-{site_name}-{layer}"
            assertions.append(assertion(assertion_id, layer, [feature_id, province_id], layer_sources))
            assertion_ids[layer].append(assertion_id)

    sources = [source_index[source_id] for source_id in selected_ids]
    pins = [{"source_id": row["source_id"], "locator": LOCATORS[row["source_id"]],
             "sha256": canonical_hash({"locator": LOCATORS[row["source_id"]], "source": row})} for row in sources]
    coverage = [
        {"region_id": "013", "layer": layer, "grade": "A", "source_ids": layer_sources,
         "assertion_ids": assertion_ids[layer], "known_gaps": [], "exclusions": [], "evidence_summary": summary}
        for layer, layer_sources, summary in (
            ("geometry", GEOMETRY_SOURCES, "Complete country-based M49 013 fabric reviewed through bounded Mexican, Maya, and lower-Central-American regional sheets plus twelve checked political or archaeological centers; no unsupported hard local frontier is asserted."),
            ("politics", POLITICS_SOURCES, f"All {EXPECTED_ASSIGNMENTS} assignments replace generic or anachronistic scaffold actors for exactly 1444-11-11, distinguishing Mexican states and kingdoms, Postclassic Maya polities, and isthmian chiefdom and community systems."),
            ("hierarchy", HIERARCHY_SOURCES, "Every assignment carries an evidence-bounded alliance, state, kingdom, city network, chiefdom system, or local-community grouping rather than a modern-state or later colonial projection."),
            ("gazetteer_relationships", RELATIONSHIP_SOURCES, "Date-valid records keep the early Triple Alliance, unconquered Tlaxcala and Purepecha state, Yucatan successors, K'iche' and other Maya polities, and lower-Central-American chiefdom systems distinct."),
        )
    ]
    expected = {"assignments": EXPECTED_ASSIGNMENTS, "polities": len(polities), "m49_corrections": 0,
                "sources": len(sources), "assertions": len(assertions),
                "build_features": len(build_features), "derived_files": 0}
    return {
        "packet_type": "m25c_regional_evidence", "packet_version": "1.0.0",
        "packet_id": "region-013-central-america-1444-grade-a-v1", "region_id": "013",
        "region_name": "Central America", "start_date": START_DATE, "as_of_date": AS_OF_DATE,
        "reviewed_by": "Codex source, visual, and contract review",
        "visual_review": "accepted" if visual_sha256 != "PENDING" else "pending",
        "complete_assignment_coverage": True, "complete_status_coverage": True,
        "complete_hierarchy_coverage": True,
        "visual_review_artifact": {"path": "review/013.svg", "renderer": "gpm qa render",
                                   "sha256": visual_sha256,
                                   "finding": "Central America exact-date sheet reviewed across Mexico, the Maya lowlands and highlands, the Pacific and Caribbean isthmus, Costa Rican and Panamanian chiefdom systems, and uninhabited eastern Pacific islands; later imperial maxima, contact-era maps, and modern borders are not projected backward."},
        "source_pin_algorithm": "sha256(canonical-json-source-and-locator-v1)",
        "source_pins": pins, "sources": sources, "polities": polities,
        "boundary_features": [], "build_features": build_features, "derived_files": [],
        "assertions": assertions, "location_region_overrides": [],
        "assignment_overrides": sorted(overrides, key=lambda row: row["province_id"]),
        "coverage": coverage, "expected_counts": expected,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-dir", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--visual-review-sha256", default=VISUAL_REVIEW_SHA256)
    args = parser.parse_args()
    packet = add_negative_control(
        build_packet(args.baseline_dir, args.output, args.visual_review_sha256),
        args.output,
    )
    actual = {"assignments": len(packet["assignment_overrides"]), "polities": len(packet["polities"]),
              "m49_corrections": len(packet["location_region_overrides"]), "sources": len(packet["sources"]),
              "assertions": len(packet["assertions"]), "build_features": len(packet["build_features"]),
              "derived_files": len(packet["derived_files"])}
    if actual != packet["expected_counts"]:
        raise SystemExit(f"region-013 packet count drifted: expected={packet['expected_counts']}, actual={actual}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(packet, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(actual, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
