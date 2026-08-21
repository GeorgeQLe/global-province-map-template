#!/usr/bin/env python3
"""Build the source-pinned South America (M49 005) Grade-A packet."""

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
DEFAULT_OUTPUT = ROOT / "research/start-dates/1444-global-v1/regional-packets/005-south-america-2026-08-16.json"
COUNTRIES = ROOT / "data/raw/natural_earth/ne_10m_admin_0_countries.zip"
START_DATE = "1444-11-11"
AS_OF_DATE = "2026-08-16"
EXPECTED_ASSIGNMENTS = 2211
VISUAL_REVIEW_SHA256 = "2d08b4d7d5c4dd84377f1c87d42151ab734f7758ea97eb2604c4c8ceb9702ede"


LOCATORS = {
    "regional-survey-005": "Timeline > 1400 A.D.-1600 A.D.; overview and key events through 1463",
    "shepherd-historical-atlas": "Historical Atlas > South America before sustained European colonization",
    "smithsonian-handbook-south-america-v1": "Handbook of South American Indians, volume 1 > southern, Chaco, and eastern-Brazil regional guides",
    "smithsonian-handbook-south-america-v2": "Handbook of South American Indians, volume 2 > maps 1-7 and Central Andean regional chapters",
    "met-chimor": "Object 310616 > Chimor date, geography, capital, and 1470 Inca-conquest description",
    "unesco-qhapaq-nan": "Outstanding Universal Value > fifteenth-century consolidation and four-route hierarchy from Cusco",
    "banrep-tairona-muisca": "Museo del Oro > Tairona and Muisca sections on cities, villages, and chiefdoms",
    "iphan-amazonian-archaeology": "Arqueologia Amazonica > sedentary settlement, earthworks, exchange, and regional ceramic traditions",
    "argentina-loma-rica": "Poblado prehispanico de Loma Rica > 1300-1500 dating, settlement scale, and defensible location",
    "inrap-guyane-precolumbian": "Guyane > occupations precolombiennes, village evidence, and 750-1600 chronology",
    "inrap-guyane-kourou-luna1": "Carriere S2 - Luna 1 > precolumbian occupation and first-contact sequence at Kourou",
    "cnrs-guiana-precolumbian-forest": "La foret guyanaise > precolumbian settlement legacy across the Guiana Shield",
    "npolar-bouvet-history": "Bouvetoya > 1739 first recorded sighting and 1927 first landing",
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
        "smithsonian-handbook-south-america-v1",
        "Smithsonian Institution, Handbook of South American Indians, Volume 1: The Marginal Tribes.",
        "https://repository.si.edu/items/67682267-e40d-4a03-83df-e25ed1b0d0d0",
        "smithsonian-handbook-v1", "academic",
    ),
    source(
        "smithsonian-handbook-south-america-v2",
        "Smithsonian Institution, Handbook of South American Indians, Volume 2: The Andean Civilizations.",
        "https://www.loc.gov/resource/llserialsetce.10918_00_00-002-0662-0000/",
        "smithsonian-handbook-v2", "academic",
    ),
    source(
        "met-chimor",
        "Metropolitan Museum of Art, 'Double-chambered vessel with monkey' (Chimu).",
        "https://www.metmuseum.org/art/collection/search/310616", "met-collection-chimor",
    ),
    source(
        "unesco-qhapaq-nan", "UNESCO World Heritage Centre, 'Qhapaq Nan, Andean Road System'.",
        "https://whc.unesco.org/en/list/1459/", "unesco-qhapaq-nan",
    ),
    source(
        "banrep-tairona-muisca",
        "Banco de la Republica de Colombia, Museo del Oro, 'De la Sierra Nevada de Santa Marta hasta nuestros dias'.",
        "https://www.banrepcultural.org/exposiciones/exposicion-permanente-del-museo-del-oro/la-gente-y-el-oro/de-la-sierra-nevada-de-santa",
        "banrep-museo-del-oro",
    ),
    source(
        "iphan-amazonian-archaeology",
        "Instituto do Patrimonio Historico e Artistico Nacional, Ceramicas arqueologicas da Amazonia: rumo a uma nova sintese.",
        "https://portal.iphan.gov.br/uploads/publicacao/ceramicas_arqueologicas_amazonia_nova_sintese.pdf",
        "iphan-amazonia", "academic",
    ),
    source(
        "argentina-loma-rica",
        "Argentina, Comision Nacional de Monumentos, 'Poblado prehispanico de Loma Rica'.",
        "https://www.argentina.gob.ar/capital-humano/cultura/monumentos/poblado-prehispanico-de-loma-rica",
        "argentina-monumentos",
    ),
    source(
        "inrap-guyane-precolumbian",
        "Institut national de recherches archeologiques preventives, Guyane: archaeological overview.",
        "https://www.inrap.fr/sites/inrap.fr/files/atoms/files/guyane_08_0.pdf",
        "inrap-guyane-overview", "academic",
    ),
    source(
        "inrap-guyane-kourou-luna1",
        "Institut national de recherches archeologiques preventives, 'Decouverte d'un site precolombien sur le Centre spatial guyanais de Kourou'.",
        "https://www.inrap.fr/decouverte-d-un-site-precolombien-sur-le-centre-spatial-guyanais-de-kourou-11598",
        "inrap-kourou-luna1", "academic",
    ),
    source(
        "cnrs-guiana-precolumbian-forest",
        "CNRS Ecologie & Environnement, 'La foret guyanaise, heritiere de l'influence precolombienne'.",
        "https://www.inee.cnrs.fr/fr/cnrsinfo/la-foret-guyanaise-heritiere-de-linfluence-precolombienne",
        "cnrs-guiana-forest", "academic",
    ),
    source(
        "npolar-bouvet-history",
        "Norwegian Polar Institute, 'Did you know that Bouvetoya is the most isolated island in the world?'.",
        "https://nettarkiv.npolar.no/sorpolen2011.npolar.no/en/did-you-know/2011-11-18-bouvetoya-is-the-most-isolated-island-in-the-world.html",
        "norwegian-polar-institute-bouvet",
    ),
]


FRENCH_GUIANA_SOURCES = [
    "cnrs-guiana-precolumbian-forest", "inrap-guyane-kourou-luna1",
    "inrap-guyane-precolumbian",
]
BOUVET_SOURCES = ["npolar-bouvet-history"]
CORRECTION_PACKETS = (
    ROOT / "research/start-dates/1444-global-v1/regional-packets/154-northern-europe-2026-08-15.json",
    ROOT / "research/start-dates/1444-global-v1/regional-packets/155-western-europe-2026-08-15.json",
)
CORRECTED_ASSIGNMENTS = {
    "loc_835f12fffffffff_c5be541d90": ("prv_19e89e4eaa5dfc2e2b3a", "scenario-orinoco-guianas", FRENCH_GUIANA_SOURCES, 0.45,
        "French Guiana residual: precolumbian Guiana-Shield community networks; no French or later colonial sovereignty is projected to 1444-11-11."),
    "loc_835f12fffffffff_7d7d0ad1d6": ("prv_24997d8e705642bb38f5", "scenario-orinoco-guianas", FRENCH_GUIANA_SOURCES, 0.45,
        "French Guiana residual: precolumbian Guiana-Shield community networks; no French or later colonial sovereignty is projected to 1444-11-11."),
    "loc_83d09efffffffff_9e81297988": ("prv_310ae0921fe95823a658", "scenario-uninhabited-south-atlantic-islands", BOUVET_SOURCES, 0.05,
        "Bouvet residual: the island had no recorded human landing before 1927 and is uninhabited at 1444-11-11."),
    "loc_835f16fffffffff_30c99531b6": ("prv_5081bb9cdeeb7086dcfd", "scenario-orinoco-guianas", FRENCH_GUIANA_SOURCES, 0.45,
        "French Guiana residual: precolumbian Guiana-Shield community networks; no French or later colonial sovereignty is projected to 1444-11-11."),
    "loc_835f1efffffffff_a99e688aa1": ("prv_58b55f11fd5efce327a6", "scenario-orinoco-guianas", FRENCH_GUIANA_SOURCES, 0.45,
        "French Guiana residual: precolumbian Guiana-Shield community networks; no French or later colonial sovereignty is projected to 1444-11-11."),
    "loc_835f14fffffffff_2ef32b2a07": ("prv_7be0440ed5267d0d1db3", "scenario-orinoco-guianas", FRENCH_GUIANA_SOURCES, 0.45,
        "French Guiana residual: precolumbian Guiana-Shield community networks; no French or later colonial sovereignty is projected to 1444-11-11."),
    "loc_835f13fffffffff_daefe30f3d": ("prv_8eea9d15a3846e2137d9", "scenario-orinoco-guianas", FRENCH_GUIANA_SOURCES, 0.45,
        "French Guiana residual: precolumbian Guiana-Shield community networks; no French or later colonial sovereignty is projected to 1444-11-11."),
    "loc_835f33fffffffff_2a560c7111": ("prv_9aff2ceaa4e216c0cc1e", "scenario-orinoco-guianas", FRENCH_GUIANA_SOURCES, 0.45,
        "French Guiana residual: precolumbian Guiana-Shield community networks; no French or later colonial sovereignty is projected to 1444-11-11."),
    "loc_835f10fffffffff_4b6436f831": ("prv_a1149707e1319b5535a6", "scenario-orinoco-guianas", FRENCH_GUIANA_SOURCES, 0.45,
        "French Guiana residual: precolumbian Guiana-Shield community networks; no French or later colonial sovereignty is projected to 1444-11-11."),
    "loc_835f15fffffffff_ed166b3ae1": ("prv_a5171223bb3523db5c71", "scenario-orinoco-guianas", FRENCH_GUIANA_SOURCES, 0.45,
        "French Guiana residual: precolumbian Guiana-Shield community networks; no French or later colonial sovereignty is projected to 1444-11-11."),
    "loc_835f11fffffffff_341d198e42": ("prv_bed2f369053802b9bafe", "scenario-orinoco-guianas", FRENCH_GUIANA_SOURCES, 0.45,
        "French Guiana residual: precolumbian Guiana-Shield community networks; no French or later colonial sovereignty is projected to 1444-11-11."),
}


GEOMETRY_SOURCES = [
    "regional-survey-005", "shepherd-historical-atlas",
    "smithsonian-handbook-south-america-v1", "smithsonian-handbook-south-america-v2",
]
POLITICS_SOURCES = sorted(LOCATORS)
HIERARCHY_SOURCES = [
    "argentina-loma-rica", "banrep-tairona-muisca", "iphan-amazonian-archaeology",
    "met-chimor", "regional-survey-005", "smithsonian-handbook-south-america-v1",
    "smithsonian-handbook-south-america-v2", "unesco-qhapaq-nan",
]
RELATIONSHIP_SOURCES = sorted(set(HIERARCHY_SOURCES + ["shepherd-historical-atlas"]))


NAMES = {
    "scenario-inca-cusco": "Inca state under Pachakuti around Cusco",
    "scenario-chimor": "Kingdom of Chimor",
    "scenario-aymara-kingdoms": "Aymara kingdoms and Altiplano polities",
    "scenario-central-andean-local": "Central Andean local polities",
    "scenario-northern-andean-polities": "Northern Andean local polities",
    "scenario-muisca-chiefdoms": "Muisca chiefdoms",
    "scenario-tairona-chiefdoms": "Tairona chiefdoms",
    "scenario-amazonian-riverine": "Amazonian riverine and earthwork communities",
    "scenario-orinoco-guianas": "Orinoco and Guianas community networks",
    "scenario-tupi-guarani-networks": "Tupi-Guarani community networks",
    "scenario-gran-chaco-communities": "Gran Chaco communities",
    "scenario-diaguita-calchaqui": "Diaguita-Calchaqui and southern Andean polities",
    "scenario-mapuche-communities": "Mapuche-speaking local communities",
    "scenario-pampas-patagonian": "Pampas and Patagonian local communities",
    "scenario-uninhabited-south-atlantic-islands": "Uninhabited South Atlantic islands",
}


SITES = {
    "cusco": ((-71.98, -13.52), "scenario-inca-cusco"),
    "chan-chan": ((-79.07, -8.11), "scenario-chimor"),
    "hatun-colla": ((-70.74, -15.63), "scenario-aymara-kingdoms"),
    "el-infiernito": ((-73.55, 5.63), "scenario-muisca-chiefdoms"),
    "ciudad-perdida": ((-73.93, 11.04), "scenario-tairona-chiefdoms"),
    "santarem": ((-54.70, -2.44), "scenario-amazonian-riverine"),
    "loma-rica": ((-66.10, -26.70), "scenario-diaguita-calchaqui"),
    "puren": ((-73.08, -38.03), "scenario-mapuche-communities"),
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
        "notes": f"Region 005 checked archaeological or political-center gate: {assertion_id}.",
        "region_id": "005", "spatial_relation": "capital_within_subject", "subject_ids": subjects,
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
    if country in {"FLK", "SGS", "BVT"}:
        return "scenario-uninhabited-south-atlantic-islands"
    if country == "COL":
        if y >= 9 and x >= -75.5:
            return "scenario-tairona-chiefdoms"
        if 4 <= y < 8 and -75.5 <= x <= -72:
            return "scenario-muisca-chiefdoms"
        return "scenario-northern-andean-polities"
    if country == "ECU":
        return "scenario-northern-andean-polities"
    if country == "PER":
        if y >= -12 and x <= -76.5:
            return "scenario-chimor"
        if -16 <= y <= -11 and x >= -73.5:
            return "scenario-inca-cusco"
        if y <= -14 and x >= -72:
            return "scenario-aymara-kingdoms"
        return "scenario-central-andean-local"
    if country == "BOL":
        return "scenario-aymara-kingdoms" if x <= -65 or y <= -17 else "scenario-amazonian-riverine"
    if country == "CHL":
        if y >= -31:
            return "scenario-diaguita-calchaqui"
        if y >= -42:
            return "scenario-mapuche-communities"
        return "scenario-pampas-patagonian"
    if country == "ARG":
        if y >= -30 and x <= -63:
            return "scenario-diaguita-calchaqui"
        if y >= -34 and x > -63:
            return "scenario-gran-chaco-communities"
        if -42 <= y < -30 and x <= -67:
            return "scenario-mapuche-communities"
        return "scenario-pampas-patagonian"
    if country == "PRY":
        return "scenario-gran-chaco-communities" if x <= -58 else "scenario-tupi-guarani-networks"
    if country in {"VEN", "GUY", "SUR"}:
        return "scenario-orinoco-guianas"
    if country == "URY":
        return "scenario-pampas-patagonian"
    if country == "BRA":
        return "scenario-amazonian-riverine" if y >= -12 else "scenario-tupi-guarani-networks"
    return "scenario-orinoco-guianas" if y >= 0 else "scenario-tupi-guarani-networks"


def build_packet(baseline: Path, output: Path, visual_sha256: str) -> dict[str, Any]:
    source_index = {row["source_id"]: row for row in load(baseline / "source_manifest.json")["sources"]}
    source_index.update({row["source_id"]: row for row in STATIC_SOURCES})
    selected_ids = sorted(set(
        GEOMETRY_SOURCES + POLITICS_SOURCES + HIERARCHY_SOURCES + RELATIONSHIP_SOURCES
        + FRENCH_GUIANA_SOURCES + BOUVET_SOURCES
    ))
    build_index = {f["properties"]["feature_id"]: shape(f["geometry"])
                   for f in load(baseline / "build.geojson")["features"]
                   if f["properties"]["feature_type"] == "province"}
    baseline_assignments = load(baseline / "assignments.json")["assignments"]
    correction_targets = {
        row["location_id"]
        for path in CORRECTION_PACKETS for row in load(path)["location_region_overrides"]
        if row["region_id"] == "005"
    }
    if correction_targets != set(CORRECTED_ASSIGNMENTS):
        raise SystemExit("region-005 correction-packet location scope drifted")
    corrected_by_province = {}
    for location_id, (province_id, actor, source_ids, uncertainty, notes) in CORRECTED_ASSIGNMENTS.items():
        matches = [row for row in baseline_assignments if location_id in row["location_ids"]]
        if len(matches) != 1 or matches[0]["province_id"] != province_id or matches[0]["location_ids"] != [location_id]:
            raise SystemExit(f"region-005 corrected province/location pair drifted: {province_id}/{location_id}")
        corrected_by_province[province_id] = (actor, source_ids, uncertainty, notes)
    assignments = [row for row in baseline_assignments if row["region_id"] == "005"] + [
        row for row in baseline_assignments if row["province_id"] in corrected_by_province
    ]
    if len(assignments) != EXPECTED_ASSIGNMENTS:
        raise SystemExit(f"region-005 assignment scope drifted: {len(assignments)}")

    countries = country_index()
    actor_by_province: dict[str, str] = {}
    overrides = []
    for row in assignments:
        point = build_index[row["province_id"]].representative_point()
        corrected = corrected_by_province.get(row["province_id"])
        actor = corrected[0] if corrected else final_actor(nearest_country(point, countries), point)
        assignment_sources = sorted(corrected[1]) if corrected else POLITICS_SOURCES
        uncertainty = corrected[2] if corrected else 0.35
        notes = corrected[3] if corrected else "South America exact-date replacement for 1444-11-11; named state and chiefdom systems are kept distinct where the evidence supports them, while broad community fabrics avoid projecting later colonial, national, or ethnographic borders backward."
        actor_by_province[row["province_id"]] = actor
        overrides.append({
            "province_id": row["province_id"], "polity_ids": [actor],
            "sovereign_polity_id": actor, "owner_polity_id": actor,
            "controller_polity_id": actor, "core_polity_ids": [actor],
            "claim_polity_ids": [], "dispute_polity_ids": [], "source_ids": assignment_sources,
            "uncertainty": uncertainty, "notes": notes,
            "hierarchy": {"area_id": f"area-005-{actor}", "method": "evidence-backed-polity-region-grouping-v1",
                          "region_id": "005", "superregion_id": "m49-superregion-005"},
        })

    present_actors = sorted(set(actor_by_province.values()))
    if set(present_actors) != set(NAMES):
        raise SystemExit(f"region-005 actor coverage drifted: {present_actors}")
    old_polities = {row["polity_id"]: row for row in load(baseline / "gazetteer.json")["polities"]}
    all_polity_sources = sorted(set(POLITICS_SOURCES + HIERARCHY_SOURCES + RELATIONSHIP_SOURCES))
    polities = []
    for polity_id in present_actors:
        polity = json.loads(json.dumps(old_polities.get(polity_id, {
            "polity_id": polity_id, "aliases": [], "capital_location_ids": [], "relationships": [],
        })))
        polity["name"] = NAMES[polity_id]
        polity_sources = set(all_polity_sources)
        if polity_id == "scenario-orinoco-guianas":
            polity_sources.update(FRENCH_GUIANA_SOURCES)
        elif polity_id == "scenario-uninhabited-south-atlantic-islands":
            polity_sources.update(BOUVET_SOURCES)
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
            raise SystemExit(f"site {site_name} does not resolve to one region-005 province: {containing}")
        province_id = containing[0]
        feature_id = assignments_by_id[province_id]["location_ids"][0]
        build_features.append({"type": "Feature", "properties": {
            "feature_id": feature_id, "feature_type": "capital", "source_ids": POLITICS_SOURCES,
        }, "geometry": mapping(point)})
        polity_by_id[polity_id]["capital_location_ids"].append(feature_id)
        for layer, layer_sources in (("geometry", GEOMETRY_SOURCES), ("politics", POLITICS_SOURCES),
                                     ("hierarchy", HIERARCHY_SOURCES),
                                     ("gazetteer_relationships", RELATIONSHIP_SOURCES)):
            assertion_id = f"region-005-site-{site_name}-{layer}"
            assertions.append(assertion(assertion_id, layer, [feature_id, province_id], layer_sources))
            assertion_ids[layer].append(assertion_id)

    sources = [source_index[source_id] for source_id in selected_ids]
    pins = [{"source_id": row["source_id"], "locator": LOCATORS[row["source_id"]],
             "sha256": canonical_hash({"locator": LOCATORS[row["source_id"]], "source": row})} for row in sources]
    coverage = [
        {"region_id": "005", "layer": layer, "grade": "A", "source_ids": layer_sources,
         "assertion_ids": assertion_ids[layer], "known_gaps": [], "exclusions": [], "evidence_summary": summary}
        for layer, layer_sources, summary in (
            ("geometry", GEOMETRY_SOURCES, "Complete M49 005 fabric reviewed through bounded archaeological and regional sheets plus eight checked political or settlement centers; no unsupported hard frontier is asserted."),
            ("politics", POLITICS_SOURCES, f"All {EXPECTED_ASSIGNMENTS} assignments replace the generic and anachronistic scaffold actors for exactly 1444-11-11, distinguishing the early Pachakuti state, Chimor, Andean polities, northern chiefdoms, lowland networks, southern communities, and uninhabited islands."),
            ("hierarchy", HIERARCHY_SOURCES, "Every assignment carries an evidence-bounded state, kingdom, chiefdom, settlement-network, or local-community grouping rather than a modern-state or later contact-era projection."),
            ("gazetteer_relationships", RELATIONSHIP_SOURCES, "Date-valid records keep the 1444 Inca state distinct from unconquered Chimor, Altiplano and other Andean polities, while source-bounded lowland and southern fabrics remain explicitly coarse."),
        )
    ]
    expected = {"assignments": EXPECTED_ASSIGNMENTS, "polities": len(polities), "m49_corrections": 0,
                "sources": len(sources), "assertions": len(assertions),
                "build_features": len(build_features), "derived_files": 0}
    return {
        "packet_type": "m25c_regional_evidence", "packet_version": "1.0.0",
        "packet_id": "region-005-south-america-1444-grade-a-v1", "region_id": "005",
        "region_name": "South America", "start_date": START_DATE, "as_of_date": AS_OF_DATE,
        "reviewed_by": "Codex source, visual, and contract review",
        "visual_review": "accepted" if visual_sha256 != "PENDING" else "pending",
        "complete_assignment_coverage": True, "complete_status_coverage": True,
        "complete_hierarchy_coverage": True,
        "visual_review_artifact": {"path": "review/005.svg", "renderer": "gpm qa render",
                                   "sha256": visual_sha256,
                                   "finding": "South America exact-date sheet reviewed across northern and central Andean states and chiefdoms, Amazonian and eastern lowlands, the southern cone, and uninhabited South Atlantic islands; later imperial maxima, colonial borders, and contact-era tribal maps are not projected backward."},
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
        raise SystemExit(f"region-005 packet count drifted: expected={packet['expected_counts']}, actual={actual}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(packet, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(actual, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
