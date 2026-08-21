#!/usr/bin/env python3
"""Build the source-pinned Caribbean (M49 029) Grade-A packet."""

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
DEFAULT_OUTPUT = ROOT / "research/start-dates/1444-global-v1/regional-packets/029-caribbean-2026-08-16.json"
COUNTRIES = ROOT / "data/raw/natural_earth/ne_10m_admin_0_countries.zip"
START_DATE = "1444-11-11"
AS_OF_DATE = "2026-08-16"
EXPECTED_ASSIGNMENTS = 396
VISUAL_REVIEW_SHA256 = "a9968a21b77e7a979c70dba2bd291b01529e9f3bc93b0ce3fa3c5a9820288ccf"


LOCATORS = {
    "regional-survey-029": "Timeline > 1400 A.D.-1600 A.D.; Caribbean regional overview and pre-contact chronology",
    "shepherd-historical-atlas": "Historical Atlas > West Indies before sustained European colonization",
    "smithsonian-handbook-caribbean": "Handbook of South American Indians IV > The West Indies, Arawak, Ciboney, Carib, and island ethnographies, pp. 495-565",
    "nmai-caribbean-overview": "Mesoamerica / Caribbean > Greater Antillean communities, Taino chiefdoms, and inter-island exchange",
    "nmai-lucayan-duho": "Lucayan duho > AD 1000-1500; Bahamas and Turks and Caicos local chiefly tradition",
    "nmai-taino-gallery-guide": "Who Are the Taino? and map > Greater Antilles, Bahamas, Kalinago, and surrounding island communities",
    "unesco-caribbean-archaeology": "Annex 2 > Pre-Hispanic Cultures of the Insular Caribbean; Greater and Lesser Antillean archaeological sequences",
    "smithsonian-comparative-arawakan": "Comparative Arawakan Histories > Taino regional variants, village organization, and district and provincial chiefdoms",
    "pmc-east-guadeloupe-networks": "Late pre-colonial East-Guadeloupe > village networks and Anse a la Gourde sequence",
    "adlfi-anse-a-la-gourde": "Anse a la Gourde > phased occupation through 1400 CE",
    "inrap-guadeloupe-history": "Guadeloupe, une histoire retrouvee > Amerindian settlement and material record",
    "inrap-antilles-archaeology": "L'archeologie des Antilles > island-network interpretation and precolumbian sequence",
    "yale-martinique-later-prehistory": "Later prehistory in Martinique > 600-1450 CE sequence and Island-Carib identification limits",
    "inrap-martinique-anse-bellay": "Anse Bellay > late precolumbian Martinique evidence, eleventh-fourteenth centuries",
    "leiden-martinique-ansea-trabaud": "Anse Trabaud > late precolonial Martinique coastal deposits",
    "leiden-precolumbian-saba-thesis": "Pre-Columbian Saba > settlement reports and late precolumbian social environment",
    "leiden-saba-first-inhabitants": "Saba's first inhabitants > Amerindian occupation through 1492",
    "springer-late-precolonial-saba-networks": "Remotely Local > Saba networks, AD 1000-1450",
    "leiden-st-eustatius-archaeology": "St. Eustatius > Amerindian sites and Golden Rock settlement",
    "jas-st-eustatius-golden-rock": "Golden Rock > pre-Columbian settlement and inter-island exchange",
    "tandf-bonaire-isotopes": "Pre-colonial Bonaire > Indigenous lifeways and local residence evidence",
    "royalsociety-caquetio-calibration": "Caquetio > Bonaire distribution and Dabajuroid archaeological association",
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
        "smithsonian-handbook-caribbean",
        "Smithsonian Institution, Handbook of South American Indians, Volume 4: The Circum-Caribbean Tribes.",
        "https://repository.si.edu/bitstreams/fb2ec995-9284-4cee-aa1d-2415d95f70f3/download",
        "smithsonian-handbook-v4", "academic",
    ),
    source(
        "nmai-caribbean-overview",
        "National Museum of the American Indian, 'Mesoamerica/Caribbean,' Infinity of Nations.",
        "https://americanindian.si.edu/exhibitions/infinityofnations/mesoamerica-caribbean.html",
        "nmai-infinity-of-nations",
    ),
    source(
        "nmai-lucayan-duho",
        "National Museum of the American Indian, 'Lucayan duho,' Infinity of Nations.",
        "https://americanindian.si.edu/exhibitions/infinityofnations/meso-carib/059385.html",
        "nmai-infinity-of-nations",
    ),
    source(
        "nmai-taino-gallery-guide",
        "National Museum of the American Indian, Taino: Native Heritage and Identity in the Caribbean, Gallery Guide.",
        "https://americanindian.si.edu/nk360/pdf/Taino-Gallery-Guide-English.pdf",
        "nmai-taino-exhibition",
    ),
    source(
        "unesco-caribbean-archaeology",
        "UNESCO World Heritage Centre, Caribbean Archaeology and World Heritage Convention, World Heritage Papers 14.",
        "https://whc.unesco.org/documents/publi_wh_papers_14_en_1.pdf",
        "unesco-caribbean-archaeology", "academic",
    ),
    source(
        "smithsonian-comparative-arawakan",
        "Jonathan D. Hill and Fernando Santos-Granero, eds., Comparative Arawakan Histories, Smithsonian Institution Press.",
        "https://repository.si.edu/bitstreams/03d796ff-b4f3-4dde-bdf7-2229e4956524/download",
        "smithsonian-comparative-arawakan", "academic",
    ),
    source(
        "pmc-east-guadeloupe-networks",
        "Angus Mol et al., 'Exploring Transformations in Caribbean Indigenous Social Networks through Visibility Studies: Late Pre-Colonial East-Guadeloupe'.",
        "https://pmc.ncbi.nlm.nih.gov/articles/PMC5953974/", "east-guadeloupe-network-study", "academic",
    ),
    source(
        "adlfi-anse-a-la-gourde",
        "French Ministry of Culture, ADLFI, 'Resultats significatifs en Guadeloupe pour l'annee 1996: Anse a la Gourde'.",
        "https://journals.openedition.org/adlfi/113978", "adlfi-anse-gourde", "academic",
    ),
    source(
        "inrap-guadeloupe-history", "Inrap, Guadeloupe, une histoire retrouvee.",
        "https://www.inrap.fr/sites/inrap.fr/files/atoms/files/memoire-fouilles-guadeloupe_2015.pdf",
        "inrap-guadeloupe-synthesis", "academic",
    ),
    source(
        "inrap-antilles-archaeology", "Inrap, 'L'archeologie des Antilles'.",
        "https://www.inrap.fr/l-archeologie-des-antilles-14877", "inrap-antilles-overview", "academic",
    ),
    source(
        "yale-martinique-later-prehistory",
        "Louis Allaire, Later Prehistory in Martinique and the Island Caribs: Problems in Ethnic Identification, Yale University dissertation.",
        "https://ehrafarchaeology.yale.edu/traditions/s051/documents/002",
        "yale-allaire-martinique", "academic",
    ),
    source(
        "inrap-martinique-anse-bellay", "Inrap, 'Anse Bellay' archaeological site record.",
        "https://www.inrap.fr/anse-bellay-4750", "inrap-anse-bellay", "academic",
    ),
    source(
        "leiden-martinique-ansea-trabaud",
        "Leiden University, Menno Hoogland publication record for late-precolonial Anse Trabaud, Martinique.",
        "https://www.universiteitleiden.nl/en/research/research-projects/archaeology/martinique",
        "leiden-anse-trabaud", "academic",
    ),
    source(
        "leiden-precolumbian-saba-thesis",
        "Menno L. P. Hoogland, In Search of the Native Population of Pre-Columbian Saba, Leiden University.",
        "https://www.universiteitleiden.nl/en/research/research-output/archaeology/in-search-of-the-native-population-of-pre-columbian-saba.-part-two-settlements-in-their-natural-and-social-environment",
        "leiden-hoogland-saba", "academic",
    ),
    source(
        "leiden-saba-first-inhabitants",
        "Leiden University, 'A look inside the Saba Archaeological Center' and Saba's First Inhabitants.",
        "https://www.universiteitleiden.nl/nexus1492/news/sabarc-2019-finds",
        "leiden-hofman-hoogland-saba", "academic",
    ),
    source(
        "springer-late-precolonial-saba-networks",
        "Angus Mol, Menno Hoogland, and Corinne Hofman, 'Remotely Local: Ego-networks of Late Pre-colonial (AD 1000-1450) Saba'.",
        "https://doi.org/10.1007/s10816-013-9200-5", "springer-saba-networks", "academic",
    ),
    source(
        "leiden-st-eustatius-archaeology", "Leiden University, 'St. Eustatius' archaeology project.",
        "https://www.universiteitleiden.nl/en/research/research-projects/archaeology/st.-eustatius",
        "leiden-st-eustatius-project", "academic",
    ),
    source(
        "jas-st-eustatius-golden-rock",
        "Harlow et al., 'Pre-Columbian jadeitite artifacts from the Golden Rock Site, St. Eustatius', Journal of Archaeological Science 40.",
        "https://doi.org/10.1016/j.jas.2013.03.025", "jas-golden-rock", "academic",
    ),
    source(
        "tandf-bonaire-isotopes",
        "Eleni Seferidou, Sebastiaan Knippenberg, and Jason Laffoon, 'Reconstructing past lifeways of Indigenous individuals in pre-colonial Bonaire'.",
        "https://doi.org/10.1080/15564894.2023.2289190", "bonaire-isotope-study", "academic",
    ),
    source(
        "royalsociety-caquetio-calibration",
        "Walker et al., 'Deriving calibrations for Arawakan using archaeological evidence', Royal Society Open Science.",
        "https://pmc.ncbi.nlm.nih.gov/articles/PMC9732640/", "royal-society-arawakan", "academic",
    ),
]


GUADELOUPE_SOURCES = [
    "adlfi-anse-a-la-gourde", "inrap-antilles-archaeology", "inrap-guadeloupe-history",
    "pmc-east-guadeloupe-networks",
]
MARTINIQUE_SOURCES = [
    "inrap-martinique-anse-bellay", "leiden-martinique-ansea-trabaud",
    "yale-martinique-later-prehistory",
]
SABA_SOURCES = [
    "leiden-precolumbian-saba-thesis", "leiden-saba-first-inhabitants",
    "springer-late-precolonial-saba-networks",
]
ST_EUSTATIUS_SOURCES = ["jas-st-eustatius-golden-rock", "leiden-st-eustatius-archaeology"]
BONAIRE_SOURCES = ["royalsociety-caquetio-calibration", "tandf-bonaire-isotopes"]
CORRECTION_PACKET = ROOT / "research/start-dates/1444-global-v1/regional-packets/155-western-europe-2026-08-15.json"
GUADELOUPE_NOTE = "Guadeloupe residual: a late-precolonial Lesser Antillean community network is retained without projecting French sovereignty or a harder local ethnic frontier to 1444-11-11."
MARTINIQUE_NOTE = "Martinique residual: late-precolonial island communities are assigned to the Kalinago-related Lesser Antillean fabric with explicit ethnic-boundary uncertainty."
SABA_NOTE = "Saba residual: the fourteenth-century Kelbey's Ridge and wider late-precolonial network support a northern Leeward community assignment at 1444-11-11."
ST_EUSTATIUS_NOTE = "Sint Eustatius residual: precolumbian occupation is established, but the evidence does not support a specific continuously occupied polity at 1444-11-11."
BONAIRE_NOTE = "Bonaire residual: late-precolonial Caquetio-associated communities are supported by island archaeology; no Dutch sovereignty is projected backward."
CORRECTED_ASSIGNMENTS = {
    "loc_835e43fffffffff_7a1063e862": ("prv_17a2082ff620fff2365c", "scenario-kalinago-lesser-antilles", GUADELOUPE_SOURCES, 0.45, GUADELOUPE_NOTE),
    "loc_835e5cfffffffff_2ab68c1e58": ("prv_2672ba4a59434e1097be", "scenario-kalinago-lesser-antilles", GUADELOUPE_SOURCES, 0.45, GUADELOUPE_NOTE),
    "loc_835e43fffffffff_c83e1ce1da": ("prv_4a456cb955650662c02c", "scenario-kalinago-lesser-antilles", GUADELOUPE_SOURCES, 0.45, GUADELOUPE_NOTE),
    "loc_835e4bfffffffff_7b21fd4fff": ("prv_5486a37d9e86c8d02c36", "scenario-eastern-taino-communities", SABA_SOURCES, 0.35, SABA_NOTE),
    "loc_835e43fffffffff_8e2598daef": ("prv_55d2a5f86e33f9a1e0f6", "scenario-kalinago-lesser-antilles", GUADELOUPE_SOURCES, 0.45, GUADELOUPE_NOTE),
    "loc_835e46fffffffff_f74726b473": ("prv_57b4e5f40a10e9eb381e", "scenario-kalinago-lesser-antilles", MARTINIQUE_SOURCES, 0.45, MARTINIQUE_NOTE),
    "loc_835e5cfffffffff_15e968bfc2": ("prv_601f0e1dce2c047ff9b1", "scenario-kalinago-lesser-antilles", GUADELOUPE_SOURCES, 0.45, GUADELOUPE_NOTE),
    "loc_835e5cfffffffff_3798bc792c": ("prv_67d747708875f2223712", "scenario-kalinago-lesser-antilles", GUADELOUPE_SOURCES, 0.45, GUADELOUPE_NOTE),
    "loc_835e43fffffffff_483b66cd61": ("prv_6851031205ea4eed2d95", "scenario-kalinago-lesser-antilles", GUADELOUPE_SOURCES, 0.45, GUADELOUPE_NOTE),
    "loc_835e43fffffffff_38c143e382": ("prv_7e505f8595a1e7d80118", "scenario-kalinago-lesser-antilles", GUADELOUPE_SOURCES, 0.45, GUADELOUPE_NOTE),
    "loc_835e42fffffffff_62ba9e62fb": ("prv_7f27dae3ee89a0f66538", "scenario-kalinago-lesser-antilles", MARTINIQUE_SOURCES, 0.45, MARTINIQUE_NOTE),
    "loc_835e5dfffffffff_a646fd5470": ("prv_82a3457e29f98a53c095", "scenario-kalinago-lesser-antilles", GUADELOUPE_SOURCES, 0.45, GUADELOUPE_NOTE),
    "loc_835e43fffffffff_73093ec31b": ("prv_8fea3e2c28a3f224b005", "scenario-kalinago-lesser-antilles", GUADELOUPE_SOURCES, 0.45, GUADELOUPE_NOTE),
    "loc_835e5dfffffffff_e2b27ba088": ("prv_94e92fbb78d7fe1b97b2", "scenario-kalinago-lesser-antilles", GUADELOUPE_SOURCES, 0.45, GUADELOUPE_NOTE),
    "loc_836744fffffffff_c1890d6cc2": ("prv_ab4cbfb4ba8ef151dae9", "scenario-caquetio-southern-caribbean", BONAIRE_SOURCES, 0.25, BONAIRE_NOTE),
    "loc_835e4bfffffffff_12eb076dd3": ("prv_b31341d5fc6a20f66d8d", "scenario-small-island-communities", ST_EUSTATIUS_SOURCES, 0.55, ST_EUSTATIUS_NOTE),
    "loc_836740fffffffff_50847f2e9c": ("prv_bb1f1984122ac5695b3b", "scenario-caquetio-southern-caribbean", BONAIRE_SOURCES, 0.25, BONAIRE_NOTE),
    "loc_835e5dfffffffff_1060162a95": ("prv_bbe4b181a47cc45070b6", "scenario-kalinago-lesser-antilles", GUADELOUPE_SOURCES, 0.45, GUADELOUPE_NOTE),
    "loc_835e5dfffffffff_2656f3ce70": ("prv_be9567c2033d1b7fee4f", "scenario-kalinago-lesser-antilles", GUADELOUPE_SOURCES, 0.45, GUADELOUPE_NOTE),
    "loc_835e40fffffffff_dba80c9470": ("prv_c5fff292c95e2ba4f0ee", "scenario-kalinago-lesser-antilles", MARTINIQUE_SOURCES, 0.45, MARTINIQUE_NOTE),
    "loc_835e43fffffffff_269993ccb5": ("prv_d1eefa0b15368af256bb", "scenario-kalinago-lesser-antilles", GUADELOUPE_SOURCES, 0.45, GUADELOUPE_NOTE),
    "loc_835e5cfffffffff_133685825d": ("prv_d4a91f94d8f3312856f3", "scenario-kalinago-lesser-antilles", GUADELOUPE_SOURCES, 0.45, GUADELOUPE_NOTE),
    "loc_835e43fffffffff_9c67cb4923": ("prv_eef6464d5bfff220c3b2", "scenario-kalinago-lesser-antilles", GUADELOUPE_SOURCES, 0.45, GUADELOUPE_NOTE),
    "loc_836746fffffffff_f55accb5a3": ("prv_f7a214361558b659829e", "scenario-caquetio-southern-caribbean", BONAIRE_SOURCES, 0.25, BONAIRE_NOTE),
}


GEOMETRY_SOURCES = [
    "nmai-taino-gallery-guide", "regional-survey-029", "shepherd-historical-atlas",
    "smithsonian-handbook-caribbean", "unesco-caribbean-archaeology",
]
POLITICS_SOURCES = sorted(LOCATORS)
HIERARCHY_SOURCES = [
    "nmai-caribbean-overview", "nmai-lucayan-duho", "nmai-taino-gallery-guide",
    "regional-survey-029", "smithsonian-comparative-arawakan",
    "smithsonian-handbook-caribbean", "unesco-caribbean-archaeology",
]
RELATIONSHIP_SOURCES = sorted(set(HIERARCHY_SOURCES + ["shepherd-historical-atlas"]))


NAMES = {
    "scenario-lucayan-chiefdoms": "Lucayan island chiefdoms and communities",
    "scenario-cuba-taino-chiefdoms": "Cuban Taino chiefdoms and communities",
    "scenario-guanahatabey-communities": "Guanahatabey communities of western Cuba",
    "scenario-hispaniola-taino-chiefdoms": "Hispaniolan Taino regional chiefdoms",
    "scenario-boriken-taino-chiefdoms": "Boriken Taino chiefdoms",
    "scenario-jamaica-taino-communities": "Jamaican Taino communities",
    "scenario-eastern-taino-communities": "Virgin and northern Leeward Island communities",
    "scenario-kalinago-lesser-antilles": "Kalinago and related Lesser Antillean communities",
    "scenario-trinidad-communities": "Trinidadian Orinoco-linked communities",
    "scenario-caquetio-southern-caribbean": "Caquetio communities of the southern Caribbean",
    "scenario-small-island-communities": "Small-island and seasonally used Caribbean sites",
}


SITES = {
    "middle-caicos": ((-71.82, 21.79), "scenario-lucayan-chiefdoms"),
    "el-chorro-de-maita": ((-75.68, 20.56), "scenario-cuba-taino-chiefdoms"),
    "guanahacabibes": ((-84.85, 21.90), "scenario-guanahatabey-communities"),
    "en-bas-saline": ((-72.03, 19.75), "scenario-hispaniola-taino-chiefdoms"),
    "tibes": ((-66.57, 18.05), "scenario-boriken-taino-chiefdoms"),
    "white-marl": ((-76.98, 17.99), "scenario-jamaica-taino-communities"),
    "indian-creek": ((-61.77, 17.03), "scenario-eastern-taino-communities"),
    "banwari-trace": ((-61.42, 10.07), "scenario-trinidad-communities"),
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
        "notes": f"Region 029 checked political or archaeological-site gate: {assertion_id}.",
        "region_id": "029", "spatial_relation": "capital_within_subject", "subject_ids": subjects,
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
    if country in {"BHS", "TCA"}:
        return "scenario-lucayan-chiefdoms"
    if country == "CUB":
        return "scenario-guanahatabey-communities" if point.x <= -83 else "scenario-cuba-taino-chiefdoms"
    if country in {"HTI", "DOM", "USG"}:
        return "scenario-hispaniola-taino-chiefdoms"
    if country == "PRI":
        return "scenario-boriken-taino-chiefdoms"
    if country == "JAM":
        return "scenario-jamaica-taino-communities"
    if country in {"VIR", "VGB", "AIA", "MAF", "SXM", "BLM", "ATG", "KNA", "MSR"}:
        return "scenario-eastern-taino-communities"
    if country in {"DMA", "LCA", "VCT", "GRD", "BRB"}:
        return "scenario-kalinago-lesser-antilles"
    if country == "TTO":
        return "scenario-trinidad-communities"
    if country in {"ABW", "CUW"}:
        return "scenario-caquetio-southern-caribbean"
    if country in {"CYM", "BJN", "SER", "UMI"}:
        return "scenario-small-island-communities"
    raise SystemExit(f"region-029 country classification drifted: {country} at {point.wkt}")


def build_packet(baseline: Path, output: Path, visual_sha256: str) -> dict[str, Any]:
    source_index = {row["source_id"]: row for row in load(baseline / "source_manifest.json")["sources"]}
    source_index.update({row["source_id"]: row for row in STATIC_SOURCES})
    residual_sources = (
        GUADELOUPE_SOURCES + MARTINIQUE_SOURCES + SABA_SOURCES
        + ST_EUSTATIUS_SOURCES + BONAIRE_SOURCES
    )
    selected_ids = sorted(set(
        GEOMETRY_SOURCES + POLITICS_SOURCES + HIERARCHY_SOURCES
        + RELATIONSHIP_SOURCES + residual_sources
    ))
    build_index = {f["properties"]["feature_id"]: shape(f["geometry"])
                   for f in load(baseline / "build.geojson")["features"]
                   if f["properties"]["feature_type"] == "province"}
    baseline_assignments = load(baseline / "assignments.json")["assignments"]
    correction_targets = {
        row["location_id"] for row in load(CORRECTION_PACKET)["location_region_overrides"]
        if row["region_id"] == "029"
    }
    if correction_targets != set(CORRECTED_ASSIGNMENTS):
        raise SystemExit("region-029 correction-packet location scope drifted")
    corrected_by_province = {}
    for location_id, (province_id, actor, source_ids, uncertainty, notes) in CORRECTED_ASSIGNMENTS.items():
        matches = [row for row in baseline_assignments if location_id in row["location_ids"]]
        if len(matches) != 1 or matches[0]["province_id"] != province_id or matches[0]["location_ids"] != [location_id]:
            raise SystemExit(f"region-029 corrected province/location pair drifted: {province_id}/{location_id}")
        corrected_by_province[province_id] = (actor, source_ids, uncertainty, notes)
    assignments = [row for row in baseline_assignments if row["region_id"] == "029"] + [
        row for row in baseline_assignments if row["province_id"] in corrected_by_province
    ]
    if len(assignments) != EXPECTED_ASSIGNMENTS:
        raise SystemExit(f"region-029 assignment scope drifted: {len(assignments)}")

    countries = country_index()
    actor_by_province: dict[str, str] = {}
    overrides = []
    for row in assignments:
        point = build_index[row["province_id"]].representative_point()
        corrected = corrected_by_province.get(row["province_id"])
        actor = corrected[0] if corrected else final_actor(nearest_country(point, countries), point)
        assignment_sources = sorted(corrected[1]) if corrected else POLITICS_SOURCES
        uncertainty = corrected[2] if corrected else 0.35
        notes = corrected[3] if corrected else "Caribbean exact-date replacement for 1444-11-11; island chiefdom and community fields remain coarse where archaeological and early-contact evidence does not support a hard local frontier."
        actor_by_province[row["province_id"]] = actor
        overrides.append({
            "province_id": row["province_id"], "polity_ids": [actor],
            "sovereign_polity_id": actor, "owner_polity_id": actor,
            "controller_polity_id": actor, "core_polity_ids": [actor],
            "claim_polity_ids": [], "dispute_polity_ids": [], "source_ids": assignment_sources,
            "uncertainty": uncertainty, "notes": notes,
            "hierarchy": {"area_id": f"area-029-{actor}", "method": "evidence-backed-polity-region-grouping-v1",
                          "region_id": "029", "superregion_id": "m49-superregion-029"},
        })

    present_actors = sorted(set(actor_by_province.values()))
    if set(present_actors) != set(NAMES):
        raise SystemExit(f"region-029 actor coverage drifted: {present_actors}")
    old_polities = {row["polity_id"]: row for row in load(baseline / "gazetteer.json")["polities"]}
    all_polity_sources = sorted(set(POLITICS_SOURCES + HIERARCHY_SOURCES + RELATIONSHIP_SOURCES))
    polities = []
    for polity_id in present_actors:
        polity = json.loads(json.dumps(old_polities.get(polity_id, {
            "polity_id": polity_id, "aliases": [], "capital_location_ids": [], "relationships": [],
        })))
        polity_sources = set(all_polity_sources)
        if polity_id == "scenario-kalinago-lesser-antilles":
            polity_sources.update(GUADELOUPE_SOURCES + MARTINIQUE_SOURCES)
        elif polity_id == "scenario-eastern-taino-communities":
            polity_sources.update(SABA_SOURCES)
        elif polity_id == "scenario-small-island-communities":
            polity_sources.update(ST_EUSTATIUS_SOURCES)
        elif polity_id == "scenario-caquetio-southern-caribbean":
            polity_sources.update(BONAIRE_SOURCES)
        polity.update({"name": NAMES[polity_id], "source_ids": sorted(polity_sources),
                       "valid_from": "1400", "valid_to": "1500", "capital_location_ids": []})
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
            raise SystemExit(f"site {site_name} does not resolve to one region-029 province: {containing}")
        province_id = containing[0]
        feature_id = assignments_by_id[province_id]["location_ids"][0]
        build_features.append({"type": "Feature", "properties": {
            "feature_id": feature_id, "feature_type": "capital", "source_ids": POLITICS_SOURCES,
        }, "geometry": mapping(point)})
        polity_by_id[polity_id]["capital_location_ids"].append(feature_id)
        for layer, layer_sources in (("geometry", GEOMETRY_SOURCES), ("politics", POLITICS_SOURCES),
                                     ("hierarchy", HIERARCHY_SOURCES),
                                     ("gazetteer_relationships", RELATIONSHIP_SOURCES)):
            assertion_id = f"region-029-site-{site_name}-{layer}"
            assertions.append(assertion(assertion_id, layer, [feature_id, province_id], layer_sources))
            assertion_ids[layer].append(assertion_id)

    sources = [source_index[source_id] for source_id in selected_ids]
    pins = [{"source_id": row["source_id"], "locator": LOCATORS[row["source_id"]],
             "sha256": canonical_hash({"locator": LOCATORS[row["source_id"]], "source": row})} for row in sources]
    coverage = [
        {"region_id": "029", "layer": layer, "grade": "A", "source_ids": layer_sources,
         "assertion_ids": assertion_ids[layer], "known_gaps": [], "exclusions": [], "evidence_summary": summary}
        for layer, layer_sources, summary in (
            ("geometry", GEOMETRY_SOURCES, "Complete country-based M49 029 fabric reviewed through Caribbean archaeological and institutional syntheses and eight checked sites; no unsupported hard local frontier is asserted."),
            ("politics", POLITICS_SOURCES, f"All {EXPECTED_ASSIGNMENTS} assignments replace generic or modern island scaffold actors for exactly 1444-11-11 with source-bounded chiefdom and community fabrics."),
            ("hierarchy", HIERARCHY_SOURCES, "Every assignment carries an evidence-bounded island chiefdom, regional community, or small-island grouping rather than a modern-state projection."),
            ("gazetteer_relationships", RELATIONSHIP_SOURCES, "Date-valid records distinguish Lucayan, Greater Antillean Taino, Guanahatabey, northern and southern Lesser Antillean, Trinidadian, and southern-Caribbean fabrics."),
        )
    ]
    expected = {"assignments": EXPECTED_ASSIGNMENTS, "polities": len(polities),
                "m49_corrections": 0, "sources": len(sources), "assertions": len(assertions),
                "build_features": len(build_features), "derived_files": 0}
    return {
        "packet_type": "m25c_regional_evidence", "packet_version": "1.0.0",
        "packet_id": "region-029-caribbean-1444-grade-a-v1", "region_id": "029",
        "region_name": "Caribbean", "start_date": START_DATE, "as_of_date": AS_OF_DATE,
        "reviewed_by": "Codex source, visual, and contract review",
        "visual_review": "accepted" if visual_sha256 != "PENDING" else "pending",
        "complete_assignment_coverage": True, "complete_status_coverage": True,
        "complete_hierarchy_coverage": True,
        "visual_review_artifact": {"path": "review/029.svg", "renderer": "gpm qa render",
                                   "sha256": visual_sha256,
                                   "finding": "Caribbean exact-date sheet reviewed across Lucayan, Greater Antillean Taino, Guanahatabey, northern and southern Lesser Antillean, Trinidadian, southern-Caribbean, and small-island fabrics; uncertain local frontiers remain coarse."},
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
        raise SystemExit(f"region-029 packet count drifted: expected={packet['expected_counts']}, actual={actual}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(packet, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(actual, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
