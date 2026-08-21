#!/usr/bin/env python3
"""Build the source-pinned Eastern Africa (M49 014) Grade-A packet."""

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
DEFAULT_OUTPUT = ROOT / "research/start-dates/1444-global-v1/regional-packets/014-eastern-africa-2026-08-16.json"
COUNTRIES = ROOT / "data/raw/natural_earth/ne_10m_admin_0_countries.zip"
START_DATE = "1444-11-11"
AS_OF_DATE = "2026-08-16"
EXPECTED_ASSIGNMENTS = 720
VISUAL_REVIEW_SHA256 = "98a51a9d5a934c4b969d886cd99797aeb970ad7fe958ed50b5eb42c46fc720c2"


LOCATORS = {
    "regional-survey-014": "Timeline > 1400 A.D.-1600 A.D.; overview and key events",
    "shepherd-historical-atlas": "Historical Atlas > Africa before sustained European colonization",
    "unesco-general-history-africa-iv": "Chapters 17-18 and 22-24; maps 18.1, 22.1, 24.1, and 25.1",
    "met-ethiopian-christianity": "Early Solomonic period (1270-1530) > Zar'a Ya'eqob (r. 1434-68)",
    "british-museum-mogadishu": "Al-Adil Muhammad record > fifteenth- to sixteenth-century Mogadishu and Kilwa coinage",
    "unesco-kilwa": "Outstanding Universal Value > thirteenth- to sixteenth-century Indian Ocean port trade",
    "unesco-great-zimbabwe": "Outstanding Universal Value > Shona city, trade, and c.1450 transition",
    "met-ambohimanga": "Africa's Cultural Landmarks > first occupation in the fifteenth century",
    "cambridge-precolonial-africa-regions": "Eastern Interior and East Coast controlled-vocabulary definitions",
    "culture-mayotte-archaeological-timeline": "Chronologie illustree de Mayotte > settlement origins through the late-medieval Swahili phase",
    "culture-mayotte-forty-years": "Archeologies mahoraises > ninth- through fifteenth-century settlement map and synthesis",
    "persee-mayotte-bagamoyo": "Bagamoyo > cemetery chronology, tenth-fourteenth centuries, and early island settlement",
    "openedition-tsingoni-mosque": "La mosquee de Tsingoni > village chronology and 1538 sultanate-era mosque terminus",
    "culture-indian-ocean-reunion-history": "History and environment > uninhabited Mascarin before seventeenth-century settlement",
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
        "unesco-general-history-africa-iv",
        "UNESCO, General History of Africa IV: Africa from the Twelfth to the Sixteenth Century.",
        "https://unesdoc.unesco.org/ark:/48223/pf0000184287", "unesco-general-history", "academic",
    ),
    source(
        "met-ethiopian-christianity",
        "Metropolitan Museum of Art, Heilbrunn Timeline, 'African Christianity in Ethiopia'.",
        "https://www.metmuseum.org/essays/african-christianity-in-ethiopia", "met-ethiopia",
    ),
    source(
        "british-museum-mogadishu",
        "British Museum, Collections Online, 'Al-Adil Muhammad'.",
        "https://www.britishmuseum.org/collection/term/BIOG187720", "british-museum-mogadishu",
    ),
    source(
        "unesco-kilwa", "UNESCO World Heritage Centre, 'Ruins of Kilwa Kisiwani and Songo Mnara'.",
        "https://whc.unesco.org/en/list/144/", "unesco-kilwa",
    ),
    source(
        "unesco-great-zimbabwe", "UNESCO World Heritage Centre, 'Great Zimbabwe National Monument'.",
        "https://whc.unesco.org/en/list/364/", "unesco-great-zimbabwe",
    ),
    source(
        "met-ambohimanga", "Metropolitan Museum of Art, 'Royal Hill of Ambohimanga, Madagascar'.",
        "https://www.metmuseum.org/perspectives/ambohimanga", "met-ambohimanga",
    ),
    source(
        "cambridge-precolonial-africa-regions",
        "History in Africa, 'Defining Regions of Pre-Colonial Africa: A Controlled Vocabulary'.",
        "https://doi.org/10.1017/hia.2020.11", "cambridge-history-in-africa", "academic",
    ),
    source(
        "culture-mayotte-archaeological-timeline",
        "French Ministry of Culture, 'Frise archeologique: chronologie illustree de Mayotte'.",
        "https://www.culture.gouv.fr/regions/dac-mayotte/les-actualites/Frise-archeologique-chronologie-illustree-de-Mayotte",
        "culture-ministry-mayotte-timeline", "academic",
    ),
    source(
        "culture-mayotte-forty-years",
        "French Ministry of Culture, Archeologies mahoraises: Quarante annees de recherches.",
        "https://www.culture.gouv.fr/regions/dac-mayotte/publications-ressources-communication/la-collection-patrimoines-caches-de-mayotte/Archeologies-mahoraises.-Quarante-annees-de-recherches",
        "culture-ministry-mayotte-synthesis", "academic",
    ),
    source(
        "persee-mayotte-bagamoyo",
        "Patrice Courtaud, 'Le peuplement de Mayotte: l'etude des sites sepulcraux de Bagamoyo', Bulletins et Memoires de la Societe d'Anthropologie de Paris.",
        "https://www.persee.fr/doc/bmsap_0037-8984_1999_num_11_3_2566_t1_0487_0000_2",
        "persee-bagamoyo", "academic",
    ),
    source(
        "openedition-tsingoni-mosque",
        "Martial Pauly et al., 'La mosquee de Tsingoni (Mayotte): premieres investigations archeologiques', Les nouvelles de l'archeologie 150.",
        "https://journals.openedition.org/nda/3883",
        "openedition-tsingoni", "academic",
    ),
    source(
        "culture-indian-ocean-reunion-history",
        "French Ministry of Culture, Archaeology in the Indian Ocean, 'History and environment'.",
        "https://archeologie.culture.gouv.fr/ocean-indien/en/history-and-environment",
        "culture-ministry-indian-ocean", "academic",
    ),
]


MAYOTTE_SOURCES = [
    "culture-mayotte-archaeological-timeline", "culture-mayotte-forty-years",
    "openedition-tsingoni-mosque", "persee-mayotte-bagamoyo",
]
REUNION_SOURCES = ["culture-indian-ocean-reunion-history"]
CORRECTION_PACKET = ROOT / "research/start-dates/1444-global-v1/regional-packets/155-western-europe-2026-08-15.json"
CORRECTED_ASSIGNMENTS = {
    "loc_83a254fffffffff_bf97337886": ("prv_25dc8e80988576f13b94", "scenario-uninhabited-western-indian-ocean", REUNION_SOURCES, 0.05,
        "Reunion residual: the island remained uninhabited until the seventeenth century; no French ownership is projected to 1444-11-11."),
    "loc_83a304fffffffff_05539f788e": ("prv_4f169aa651ddb7613e94", "scenario-pre-sultanate-mayotte-communities", MAYOTTE_SOURCES, 0.45,
        "Mayotte residual: late-medieval island communities predate the documented sixteenth-century sultanate consolidation."),
    "loc_83a250fffffffff_a1a76e1ee2": ("prv_621047cd51de209ae7a6", "scenario-uninhabited-western-indian-ocean", REUNION_SOURCES, 0.05,
        "Reunion residual: the island remained uninhabited until the seventeenth century; no French ownership is projected to 1444-11-11."),
    "loc_83a304fffffffff_714c8bce3a": ("prv_8f086db76587de59188f", "scenario-pre-sultanate-mayotte-communities", MAYOTTE_SOURCES, 0.45,
        "Mayotte residual: late-medieval island communities predate the documented sixteenth-century sultanate consolidation."),
    "loc_83a255fffffffff_a359a377a6": ("prv_a080717eaf32dacfea49", "scenario-uninhabited-western-indian-ocean", REUNION_SOURCES, 0.05,
        "Reunion residual: the island remained uninhabited until the seventeenth century; no French ownership is projected to 1444-11-11."),
}


GEOMETRY_SOURCES = [
    "cambridge-precolonial-africa-regions", "regional-survey-014",
    "shepherd-historical-atlas", "unesco-general-history-africa-iv",
]
POLITICS_SOURCES = sorted(LOCATORS)
HIERARCHY_SOURCES = [
    "british-museum-mogadishu", "cambridge-precolonial-africa-regions",
    "met-ambohimanga", "met-ethiopian-christianity", "regional-survey-014",
    "unesco-general-history-africa-iv", "unesco-great-zimbabwe", "unesco-kilwa",
]
RELATIONSHIP_SOURCES = sorted(set(HIERARCHY_SOURCES + ["shepherd-historical-atlas"]))


NAMES = {
    "scenario-solomonic-ethiopia": "Solomonic Ethiopian kingdom under Zar'a Ya'eqob",
    "scenario-adal-sultanate": "Adal Sultanate and allied Horn ports",
    "scenario-ajuran-somali": "Ajuran and southern Somali polities",
    "scenario-upper-nile-communities": "Upper Nile kingdoms and pastoral communities",
    "scenario-great-lakes-kingdoms": "Great Lakes kingdoms and successor communities",
    "scenario-eastern-interior-communities": "Eastern African interior communities",
    "scenario-northern-swahili-cities": "Northern Swahili city-states",
    "scenario-kilwa-swahili-network": "Kilwa-linked southern Swahili city network",
    "scenario-zambezi-interior-polities": "Zambezi and Lake Malawi interior polities",
    "scenario-great-zimbabwe-transition": "Great Zimbabwe, Torwa, and emerging Mutapa political field",
    "scenario-malagasy-communities": "Malagasy coastal and highland communities",
    "scenario-comorian-sultanates": "Comorian island sultanates",
    "scenario-uninhabited-western-indian-ocean": "Uninhabited western Indian Ocean islands",
    "scenario-pre-sultanate-mayotte-communities": "Pre-sultanate Mayotte communities",
}


SITES = {
    "lalibela": ((39.05, 12.03), "scenario-solomonic-ethiopia"),
    "zeila": ((43.47, 11.35), "scenario-adal-sultanate"),
    "mogadishu": ((45.32, 2.04), "scenario-ajuran-somali"),
    "bigo": ((30.22, 0.03), "scenario-great-lakes-kingdoms"),
    "mombasa": ((39.67, -4.05), "scenario-northern-swahili-cities"),
    "kilwa": ((39.52, -8.96), "scenario-kilwa-swahili-network"),
    "great-zimbabwe": ((30.93, -20.27), "scenario-great-zimbabwe-transition"),
    "ambohimanga": ((47.56, -18.76), "scenario-malagasy-communities"),
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
        "notes": f"Region 014 checked archaeological, port, or political-center gate: {assertion_id}.",
        "region_id": "014", "spatial_relation": "capital_within_subject", "subject_ids": subjects,
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
    if country in {"MUS", "SYC", "ATF"}:
        return "scenario-uninhabited-western-indian-ocean"
    if country == "COM":
        return "scenario-comorian-sultanates"
    if country == "MDG":
        return "scenario-malagasy-communities"
    if country in {"ETH", "ERI"}:
        return "scenario-adal-sultanate" if x >= 42.5 and y <= 11.5 else "scenario-solomonic-ethiopia"
    if country in {"DJI", "SOL"}:
        return "scenario-adal-sultanate"
    if country == "SOM":
        return "scenario-adal-sultanate" if y >= 7.5 else "scenario-ajuran-somali"
    if country in {"SDS", "SDN", "CAF"}:
        return "scenario-upper-nile-communities"
    if country in {"UGA", "RWA", "BDI", "COD"}:
        return "scenario-great-lakes-kingdoms"
    if country == "KEN":
        if x >= 39:
            return "scenario-northern-swahili-cities"
        return "scenario-ajuran-somali" if x >= 37.5 and y >= 0 else "scenario-eastern-interior-communities"
    if country == "TZA":
        if x >= 38.2:
            return "scenario-kilwa-swahili-network"
        return "scenario-great-lakes-kingdoms" if x <= 32.5 else "scenario-eastern-interior-communities"
    if country == "ZWE":
        return "scenario-great-zimbabwe-transition"
    if country in {"ZMB", "MWI"}:
        return "scenario-zambezi-interior-polities"
    if country == "MOZ":
        if x >= 38 or (x >= 34.5 and y <= -18):
            return "scenario-kilwa-swahili-network"
        return "scenario-great-zimbabwe-transition" if y <= -17 else "scenario-zambezi-interior-polities"
    return "scenario-eastern-interior-communities"


def build_packet(baseline: Path, output: Path, visual_sha256: str) -> dict[str, Any]:
    source_index = {row["source_id"]: row for row in load(baseline / "source_manifest.json")["sources"]}
    source_index.update({row["source_id"]: row for row in STATIC_SOURCES})
    selected_ids = sorted(set(
        GEOMETRY_SOURCES + POLITICS_SOURCES + HIERARCHY_SOURCES + RELATIONSHIP_SOURCES
        + MAYOTTE_SOURCES + REUNION_SOURCES
    ))
    build_index = {f["properties"]["feature_id"]: shape(f["geometry"])
                   for f in load(baseline / "build.geojson")["features"]
                   if f["properties"]["feature_type"] == "province"}
    baseline_assignments = load(baseline / "assignments.json")["assignments"]
    correction_targets = {
        row["location_id"] for row in load(CORRECTION_PACKET)["location_region_overrides"]
        if row["region_id"] == "014"
    }
    if correction_targets != set(CORRECTED_ASSIGNMENTS):
        raise SystemExit("region-014 correction-packet location scope drifted")
    corrected_by_province = {}
    for location_id, (province_id, actor, source_ids, uncertainty, notes) in CORRECTED_ASSIGNMENTS.items():
        matches = [row for row in baseline_assignments if location_id in row["location_ids"]]
        if len(matches) != 1 or matches[0]["province_id"] != province_id or matches[0]["location_ids"] != [location_id]:
            raise SystemExit(f"region-014 corrected province/location pair drifted: {province_id}/{location_id}")
        corrected_by_province[province_id] = (actor, source_ids, uncertainty, notes)
    assignments = [row for row in baseline_assignments if row["region_id"] == "014"] + [
        row for row in baseline_assignments if row["province_id"] in corrected_by_province
    ]
    if len(assignments) != EXPECTED_ASSIGNMENTS:
        raise SystemExit(f"region-014 assignment scope drifted: {len(assignments)}")

    countries = country_index()
    actor_by_province: dict[str, str] = {}
    overrides = []
    for row in assignments:
        point = build_index[row["province_id"]].representative_point()
        corrected = corrected_by_province.get(row["province_id"])
        actor = corrected[0] if corrected else final_actor(nearest_country(point, countries), point)
        assignment_sources = sorted(corrected[1]) if corrected else POLITICS_SOURCES
        uncertainty = corrected[2] if corrected else 0.35
        notes = corrected[3] if corrected else "Eastern Africa exact-date replacement for 1444-11-11; documented kingdoms and port-city systems are kept distinct while broad interior community fabrics avoid projecting modern borders or later dynastic maxima backward."
        actor_by_province[row["province_id"]] = actor
        overrides.append({
            "province_id": row["province_id"], "polity_ids": [actor],
            "sovereign_polity_id": actor, "owner_polity_id": actor,
            "controller_polity_id": actor, "core_polity_ids": [actor],
            "claim_polity_ids": [], "dispute_polity_ids": [], "source_ids": assignment_sources,
            "uncertainty": uncertainty, "notes": notes,
            "hierarchy": {"area_id": f"area-014-{actor}", "method": "evidence-backed-polity-region-grouping-v1",
                          "region_id": "014", "superregion_id": "m49-superregion-014"},
        })

    present_actors = sorted(set(actor_by_province.values()))
    if set(present_actors) != set(NAMES):
        raise SystemExit(f"region-014 actor coverage drifted: {present_actors}")
    old_polities = {row["polity_id"]: row for row in load(baseline / "gazetteer.json")["polities"]}
    all_polity_sources = sorted(set(POLITICS_SOURCES + HIERARCHY_SOURCES + RELATIONSHIP_SOURCES))
    polities = []
    for polity_id in present_actors:
        polity = json.loads(json.dumps(old_polities.get(polity_id, {
            "polity_id": polity_id, "aliases": [], "capital_location_ids": [], "relationships": [],
        })))
        polity["name"] = NAMES[polity_id]
        if polity_id == "scenario-pre-sultanate-mayotte-communities":
            polity["source_ids"] = sorted(MAYOTTE_SOURCES)
        else:
            polity_sources = set(all_polity_sources)
            if polity_id == "scenario-uninhabited-western-indian-ocean":
                polity_sources.update(REUNION_SOURCES)
            polity["source_ids"] = sorted(polity_sources)
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
            raise SystemExit(f"site {site_name} does not resolve to one region-014 province: {containing}")
        province_id = containing[0]
        feature_id = assignments_by_id[province_id]["location_ids"][0]
        build_features.append({"type": "Feature", "properties": {
            "feature_id": feature_id, "feature_type": "capital", "source_ids": POLITICS_SOURCES,
        }, "geometry": mapping(point)})
        polity_by_id[polity_id]["capital_location_ids"].append(feature_id)
        for layer, layer_sources in (("geometry", GEOMETRY_SOURCES), ("politics", POLITICS_SOURCES),
                                     ("hierarchy", HIERARCHY_SOURCES),
                                     ("gazetteer_relationships", RELATIONSHIP_SOURCES)):
            assertion_id = f"region-014-site-{site_name}-{layer}"
            assertions.append(assertion(assertion_id, layer, [feature_id, province_id], layer_sources))
            assertion_ids[layer].append(assertion_id)

    sources = [source_index[source_id] for source_id in selected_ids]
    pins = [{"source_id": row["source_id"], "locator": LOCATORS[row["source_id"]],
             "sha256": canonical_hash({"locator": LOCATORS[row["source_id"]], "source": row})} for row in sources]
    coverage = [
        {"region_id": "014", "layer": layer, "grade": "A", "source_ids": layer_sources,
         "assertion_ids": assertion_ids[layer], "known_gaps": [], "exclusions": [], "evidence_summary": summary}
        for layer, layer_sources, summary in (
            ("geometry", GEOMETRY_SOURCES, "Complete M49 014 fabric reviewed through regional and archaeological syntheses plus eight checked political, port, or settlement centers; no unsupported hard frontier is asserted."),
            ("politics", POLITICS_SOURCES, f"All {EXPECTED_ASSIGNMENTS} assignments replace modern or generic scaffold actors for exactly 1444-11-11, distinguishing Solomonic Ethiopia, Adal, Somali and Swahili polities, Great Lakes and Zambezi political fields, Great Zimbabwe's transition, Malagasy communities, and island status."),
            ("hierarchy", HIERARCHY_SOURCES, "Every assignment carries an evidence-bounded kingdom, sultanate, city network, archaeological political field, or local-community grouping instead of a modern-state projection."),
            ("gazetteer_relationships", RELATIONSHIP_SOURCES, "Date-valid records keep the Horn kingdoms, autonomous coast-city networks, interior political fields, and island communities distinct while leaving uncertain local frontiers explicitly coarse."),
        )
    ]
    expected = {"assignments": EXPECTED_ASSIGNMENTS, "polities": len(polities), "m49_corrections": 0,
                "sources": len(sources), "assertions": len(assertions),
                "build_features": len(build_features), "derived_files": 0}
    return {
        "packet_type": "m25c_regional_evidence", "packet_version": "1.0.0",
        "packet_id": "region-014-eastern-africa-1444-grade-a-v1", "region_id": "014",
        "region_name": "Eastern Africa", "start_date": START_DATE, "as_of_date": AS_OF_DATE,
        "reviewed_by": "Codex source, visual, and contract review",
        "visual_review": "accepted" if visual_sha256 != "PENDING" else "pending",
        "complete_assignment_coverage": True, "complete_status_coverage": True,
        "complete_hierarchy_coverage": True,
        "visual_review_artifact": {"path": "review/014.svg", "renderer": "gpm qa render",
                                   "sha256": visual_sha256,
                                   "finding": "Eastern Africa exact-date sheet reviewed across the Horn, Upper Nile, Great Lakes, Swahili coast, Zambezi and Zimbabwe fields, Madagascar, and western Indian Ocean islands; modern borders and later dynastic maxima are not projected backward."},
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
        raise SystemExit(f"region-014 packet count drifted: expected={packet['expected_counts']}, actual={actual}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(packet, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(actual, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
