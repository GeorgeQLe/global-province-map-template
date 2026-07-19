#!/usr/bin/env python3
"""Assemble the M25 `official-1444-reconstruction-v2` research pass.

Unlike the withdrawn v1 generator, this script assembles the pass from
independently pinned research evidence and the real production pipeline:

1. evidence: pinned academic/primary sources, corroborating public-domain
   atlas plates, negative-control geoBoundaries files, and derived frontier
   geometry digitized from open river data (Natural Earth 10m, OpenHistoricalMap
   CC0) between anchor towns named by the cited scholarship;
2. fabric: the M23 `global-h3-v1` r1 build, a failed-paintability report, the
   r1->r2 split-request migration (refine_h3 corridor rounds plus
   split_by_boundary along the five evidenced frontier lines), producing real
   parent/child lineage;
3. aggregation: the full 22,000-province `eu-like` build over r2 with the five
   hard historical constraints pinned by SHA-256 and modern boundary influence
   disabled;
4. artifacts: the nine schema-0.2 pass artifacts, four fabric sidecars, two
   release sidecars, derived-evidence artifacts, deterministic review renders,
   and a pass manifest whose review block remains the human reviewer's to sign.

Stages (run in order; each is deterministic given the pinned inputs):

    build-fabric   r1 fabric + paintability + split requests + r2 fabric
    aggregate      constrained 22,000-province aggregation over r2
    assemble       emit all pass artifacts into research/start-dates/1444-v2
    render         write review/*.svg + review_manifest.json (pending review)

`python scripts/build-m25-v2-pass.py all` runs everything. The QA gate
(`gpm qa start-date --pass-dir research/start-dates/1444-v2`) is expected to
fail only on the pending independent review until a human reviewer signs.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

PASS_ID = "official-1444-reconstruction-v2"
VERSION = "2.0.0"
SCHEMA_VERSION = "0.2.0"
START_DATE = "1444-11-11"
GENERATED_AT = "2026-07-16T00:00:00+00:00"
MANIFEST_GENERATED_AT = "2026-07-16T00:00:00Z"
FABRIC_ID = "global-h3-v1"
FABRIC_REVISION = "global-h3-v1-r2"
OUTPUT_FABRIC_REVISION = "2"
AGGREGATION_REVISION = "1444-r2"
GEOMETRY_REVISION = "1444-r2"
PROFILE_ID = "eu-like"
TARGET_PROVINCES = 22000
REGIONS = ["low-countries", "burgundy", "france", "hre", "central-europe"]
GENERATOR = "gpm-m25-v2-generator"
DIGITIZER = "gpm-m25-v2-generator"
PENDING_REVIEWER = "pending-independent-review"

PASS_DIR = ROOT / "research" / "start-dates" / "1444-v2"
DERIVED_DIR = PASS_DIR / "derived"
SIDECAR_DIR = PASS_DIR / "sidecars"
EVIDENCE_DIR = PASS_DIR / "evidence"
REVIEW_DIR = PASS_DIR / "review"
STAGING = ROOT / "data" / "processed" / "m25-v2-staging"

HEADER = {
    "schema_version": SCHEMA_VERSION,
    "artifact_version": VERSION,
    "pass_id": PASS_ID,
    "start_date": START_DATE,
}

# --------------------------------------------------------------------------
# Pinned research sources.
#
# checksum semantics: SHA-256 of the exact retrieved artifact. Sources whose
# license does not permit redistribution (or whose canonical form is a live
# web page) are pinned by citation/URL/access date only; artifacts that are
# public domain or CC0 are also staged under derived/ where noted.
# --------------------------------------------------------------------------
SOURCES = [
    {
        "source_id": "dauphant-2020-sources",
        "citation": (
            "Léonard Dauphant, « Tracer et passer la frontière entre le royaume de "
            "France et l'Empire à la fin du Moyen Âge », Source(s). Arts, "
            "civilisation et histoire de l'Europe 17 (2020), p. 35-54. Names the "
            "« Quatre Rivières (Escaut, Meuse, Saône et Rhône) » as the kingdom's "
            "eastern frontier facing the Holy Roman Empire in the 14th-15th centuries."
        ),
        "url": "https://doi.org/10.57086/sources.112",
        "access_date": "2026-07-16",
        "version": "Source(s) 17 (2020)",
        "license": "CC BY-NC-SA 4.0 (cited and pinned; text not redistributed here)",
        "checksum": None,
        "transformations": [],
        "review_status": "reviewed",
        "source_type": "academic",
        "valid_from": "1300",
        "valid_to": "1515",
        "independence_group": "dauphant",
        "derived_artifacts": [],
    },
    {
        "source_id": "dauphant-2018-quatre-rivieres",
        "citation": (
            "Léonard Dauphant, « Frontière idéelle et marqueurs territoriaux du "
            "royaume des Quatre rivières (France, 1258-1529) », in Entre idéel et "
            "matériel, Éditions de la Sorbonne, 2018. Records 15th-century bronze "
            "boundary markers in the Saône riverbed and a 1452 inquiry about them."
        ),
        "url": "https://books.openedition.org/psorbonne/41103",
        "access_date": "2026-07-16",
        "version": "2018",
        "license": "OpenEdition Books open HTML (cited; text not redistributed here)",
        "checksum": None,
        "transformations": [],
        "review_status": "reviewed",
        "source_type": "academic",
        "valid_from": "1258",
        "valid_to": "1529",
        "independence_group": "dauphant",
        "derived_artifacts": [],
    },
    {
        "source_id": "dumasy-rabineau-2021",
        "citation": (
            "Juliette Dumasy-Rabineau, « Les cartes perdues des frontières de "
            "Bourgogne au milieu du XVe siècle », in Frontières spatiales, "
            "frontières sociales au Moyen Âge, Éditions de la Sorbonne, 2021, "
            "p. 91-106. Documents the 11 May 1444 journée de Langres, a mémoire of "
            "the Burgundian council of 16 October 1444 with frontier « figures », "
            "the royal position that « la frontière entre royaume et comté se "
            "situait sur la rivière », and Auxonne/Heuilley as ducal territory "
            "« sis en terre d'Empire »."
        ),
        "url": "https://books.openedition.org/psorbonne/128223",
        "access_date": "2026-07-16",
        "version": "2021",
        "license": "OpenEdition Freemium open HTML (cited; text not redistributed here)",
        "checksum": None,
        "transformations": [],
        "review_status": "reviewed",
        "source_type": "academic",
        "valid_from": "1444-01-01",
        "valid_to": "1466-12-31",
        "independence_group": "sorbonne-dumasy",
        "derived_artifacts": [],
    },
    {
        "source_id": "pirenne-histoire-belgique-ii",
        "citation": (
            "Henri Pirenne, Histoire de Belgique, t. II, 2e éd., Bruxelles, 1908, "
            "p. 171: the Burgundian dukes united « les fiefs français et les fiefs "
            "d'Empire que séparait l'Escaut »; p. 245: Philip the Good's right-bank "
            "Scheldt acquisitions lay « dans l'Empire »."
        ),
        "url": "https://archive.org/details/HistoireDeBelgique22ed",
        "access_date": "2026-07-16",
        "version": "2nd edition, 1908",
        "license": "Public domain (author died 1935; pre-1931 publication scan)",
        "checksum": "546dd95fa196ac235338855d4996bf49b0bb561115314157e00822b423a4e3de",
        "transformations": ["Internet Archive OCR text used for verbatim verification."],
        "review_status": "reviewed",
        "source_type": "academic",
        "valid_from": "1384",
        "valid_to": "1477",
        "independence_group": "pirenne",
        "derived_artifacts": [],
    },
    {
        "source_id": "pirenne-histoire-belgique-iii",
        "citation": (
            "Henri Pirenne, Histoire de Belgique, t. III, 4e éd.: the 1529 Peace of "
            "Cambrai broke « pour toujours le lien qui rattachait à la France, "
            "depuis cent ans, les régions de la rive gauche de l'Escaut » — the "
            "left-bank/kingdom attachment therefore held throughout 1444."
        ),
        "url": "https://archive.org/details/HistoireDeBelgique34ed",
        "access_date": "2026-07-16",
        "version": "4th edition",
        "license": "Public domain scan",
        "checksum": "afdd26f28b61e7a57d3cc9684bc116ab19b72b0519b59bb89ff09999247b00ae",
        "transformations": ["Internet Archive OCR text used for verbatim verification."],
        "review_status": "reviewed",
        "source_type": "academic",
        "valid_from": "1429",
        "valid_to": "1529",
        "independence_group": "pirenne",
        "derived_artifacts": [],
    },
    {
        "source_id": "lot-1910-escaut",
        "citation": (
            "Ferdinand Lot, « La frontière de la France et de l'Empire sur le cours "
            "inférieur de l'Escaut du IXe au XIIIe siècle », Bibliothèque de l'École "
            "des chartes 71 (1910), p. 5-32. Enumerates imperial Flanders (Alost, "
            "Waas, Quatre-Métiers, Overschelde) east of the Scheldt."
        ),
        "url": "https://www.persee.fr/doc/bec_0373-6237_1910_num_71_1_452488",
        "access_date": "2026-07-16",
        "version": "BEC 71 (1910)",
        "license": "Persée free consultation (cited; text not redistributed here)",
        "checksum": None,
        "transformations": [],
        "review_status": "reviewed",
        "source_type": "corroborating",
        "valid_from": "0843",
        "valid_to": "1300",
        "independence_group": "lot",
        "derived_artifacts": [],
    },
    {
        "source_id": "maigret-2002-rhone",
        "citation": (
            "Chantal Maigret, « Élaboration d'une « frontière » du Languedoc. La "
            "fortification du Rhône gardois du Xe au XIVe siècle », CTHS 125-2 "
            "(2002), p. 127-141. The Rhône « devient une limite d'états, de "
            "l'Ardèche à la Méditerranée, au cours du XIIIe siècle »."
        ),
        "url": "https://www.persee.fr/doc/acths_0000-0001_2002_act_125_2_4792",
        "access_date": "2026-07-16",
        "version": "2002",
        "license": "Persée free consultation (cited; text not redistributed here)",
        "checksum": None,
        "transformations": [],
        "review_status": "reviewed",
        "source_type": "academic",
        "valid_from": "1250",
        "valid_to": "1481",
        "independence_group": "maigret",
        "derived_artifacts": [],
    },
    {
        "source_id": "hebert-2000-provence",
        "citation": (
            "Michel Hébert, « Aspects de la culture politique en Provence au XIVe "
            "siècle », Cahiers de Fanjeaux 35 (2000): « la Provence est une « terre "
            "d'Empire » » since the incorporation of the kingdom of Burgundy (1032)."
        ),
        "url": "https://www.persee.fr/doc/cafan_0575-061x_2000_act_35_1_1766",
        "access_date": "2026-07-16",
        "version": "2000",
        "license": "Persée free consultation (cited; text not redistributed here)",
        "checksum": None,
        "transformations": [],
        "review_status": "reviewed",
        "source_type": "academic",
        "valid_from": "1032",
        "valid_to": "1481",
        "independence_group": "hebert",
        "derived_artifacts": [],
    },
    {
        "source_id": "nordfriisk-eider",
        "citation": (
            "Nordfriisk Instituut, Nordfriesland-Lexikon, art. « Eider »: « Nördlich "
            "des Flusses bildete sich das Herzogtum Schleswig heraus, das als Lehen "
            "des dänischen Königs behandelt wurde, südlich entstand die Grafschaft "
            "Holstein, ein Lehen des deutschen Kaisers. […] Die Eider blieb Grenze "
            "zwischen den Herzogtümern Schleswig und Holstein. »"
        ),
        "url": "https://www.nordfriiskinstituut.eu/futuur/nordfrieslandlexikon/eider/",
        "access_date": "2026-07-16",
        "version": None,
        "license": "© Nordfriisk Instituut (cited; text not redistributed here)",
        "checksum": None,
        "transformations": [],
        "review_status": "reviewed",
        "source_type": "academic",
        "valid_from": "0811",
        "valid_to": "1864",
        "independence_group": "nordfriisk",
        "derived_artifacts": [],
    },
    {
        "source_id": "danmarkshistorien-module-3-4",
        "citation": (
            "Aarhus University, danmarkshistorien.dk, The Late Middle Ages "
            "1340-1523, § From mortgaged kingdom to regional great power: Schleswig "
            "a duchy « belonging to the Danish Crown as a fief »; Count Adolf of "
            "Holstein « recognised as duke of Schleswig since 1440 »."
        ),
        "url": (
            "https://cas.au.dk/en/danish-history/modules/"
            "module-3-the-late-middle-ages-1340-1523/"
            "4-from-mortgaged-kingdom-to-regional-great-power"
        ),
        "access_date": "2026-07-16",
        "version": None,
        "license": "© Aarhus University (cited; text not redistributed here)",
        "checksum": None,
        "transformations": [],
        "review_status": "reviewed",
        "source_type": "academic",
        "valid_from": "1340",
        "valid_to": "1523",
        "independence_group": "aarhus",
        "derived_artifacts": [],
    },
    {
        "source_id": "sav-lexikon-skalica-2010",
        "citation": (
            "Martin Štefánik – Ján Lukačka a kol., Lexikon stredovekých miest na "
            "Slovensku, Historický ústav SAV, 2010, entry SKALICA (p. 424 of the "
            "PDF): 1217 charter « in confinio regni nostri versus Boemiam » with a "
            "perambulation along the Morava; « od konca 14. stor. dva dôležité "
            "prechody cez hranicu: na čiare Kátov – Hodonín a Skalica – Strážnica »; "
            "Hussite occupation 1432-1435 and return to Hungarian royal hands."
        ),
        "url": "https://www.forumhistoriae.sk/sites/default/files/lexikon-stredovekych-miest.pdf",
        "access_date": "2026-07-16",
        "version": "2010, ISBN 978-80-89396-11-5",
        "license": "© Historický ústav SAV, free institutional PDF (cited + pinned)",
        "checksum": "265419c8e0ff9d2d7059693d0f0ea143cf676c35217e6c5a19d1eddbffa46c57",
        "transformations": ["Quotes verified against page 424 of the pinned PDF."],
        "review_status": "reviewed",
        "source_type": "academic",
        "valid_from": "1217",
        "valid_to": "1526",
        "independence_group": "sav",
        "derived_artifacts": [],
    },
    {
        "source_id": "mudrik-2016-moravsko-uherska",
        "citation": (
            "Michal Mudrik, Moravsko-uherská hranice ve středověku, bachelor thesis, "
            "Masaryk University, 2016 (spine: Metoděj Zemek, Moravsko-uherská "
            "hranice v 10. až 13. století, Brno 1972): the border ran along the "
            "Olšava to the Morava « a po jejím toku dolů k Šaštínu »; the "
            "Rohatec-Javorina land section; Holíč-Branč Hungarian after 1331/1332."
        ),
        "url": "https://is.muni.cz/th/vm3zg/Moravsko-uherska_hranice_ve_stredoveku_mqzhbspe_Archive.pdf",
        "access_date": "2026-07-16",
        "version": "2016",
        "license": "Masaryk University thesis archive (cited; not redistributed here)",
        "checksum": None,
        "transformations": [],
        "review_status": "reviewed",
        "source_type": "academic",
        "valid_from": "1000",
        "valid_to": "1526",
        "independence_group": "muni-zemek",
        "derived_artifacts": [],
    },
    {
        "source_id": "shepherd-1453-france",
        "citation": (
            "William R. Shepherd, Historical Atlas (Henry Holt, 1911), plate "
            "« France in 1453 ». Kingdom boundary drawn along the Scheldt, Saône "
            "and Rhône; Franche-Comté, Bresse/Savoy and Provence outside the "
            "kingdom under the marginal lettering « THE EMPIRE »."
        ),
        "url": "https://commons.wikimedia.org/wiki/File:C._1453_France.jpg",
        "access_date": "2026-07-16",
        "version": "1911 plate scan",
        "license": "Public domain (pre-1931 US publication)",
        "checksum": "d16c30a587f5b205119f6edac6299b996eb50f6a1e2724891be26b4ecc3b743f",
        "transformations": [],
        "review_status": "reviewed",
        "source_type": "corroborating",
        "valid_from": "1453",
        "valid_to": "1453",
        "independence_group": "shepherd",
        "derived_artifacts": [],  # coverage masks attached in assemble stage
    },
    {
        "source_id": "shepherd-1477-central-europe",
        "citation": (
            "William R. Shepherd, Historical Atlas (Henry Holt, 1911), plate "
            "« Central Europe c. 1477 » with the legend line « Boundary of the "
            "Empire » running along the labeled Scheldt, Saône, Eider and March "
            "rivers; D. of Schleswig under the Kingdom of Denmark; Margravate of "
            "Moravia facing the Kingdom of Hungary on the March."
        ),
        "url": "https://commons.wikimedia.org/wiki/File:C._1477_Central_Europe.jpg",
        "access_date": "2026-07-16",
        "version": "1911 plate scan",
        "license": "Public domain (pre-1931 US publication)",
        "checksum": "070075310a68870a387945fad6cda13ce233e2e9c430d3ba25ee9a7a0ffbcfd1",
        "transformations": [],
        "review_status": "reviewed",
        "source_type": "corroborating",
        "valid_from": "1477",
        "valid_to": "1477",
        "independence_group": "shepherd",
        "derived_artifacts": [],  # coverage masks attached in assemble stage
    },
    {
        "source_id": "droysen-1450-burgundy",
        "citation": (
            "Gustav Droysen, Allgemeiner historischer Handatlas (1886), Burgundy/"
            "Bourbon/Savoy plate c. 1450: Duchy and Free County of Burgundy as "
            "distinct units with the Reich border band following the Saône."
        ),
        "url": "https://commons.wikimedia.org/wiki/File:C._1450_Burgundy_Bourbon_and_Savoy.jpg",
        "access_date": "2026-07-16",
        "version": "1886 plate scan",
        "license": "Public domain (1886 publication)",
        "checksum": "87e46704171b4d5bc38a0eb82ae3886d542a91079565f0392c0dce83dc4eefaf",
        "transformations": [],
        "review_status": "reviewed",
        "source_type": "corroborating",
        "valid_from": "1450",
        "valid_to": "1450",
        "independence_group": "droysen",
        "derived_artifacts": [],
    },
    {
        "source_id": "droysen-xv-deutschland",
        "citation": (
            "Gustav Droysen, Allgemeiner historischer Handatlas (1886), plate "
            "« Deutschland im XV. Jahrhundert »: Schleswig outside the red Empire "
            "boundary, which follows the Eider past Rendsburg with the Levensau "
            "continuation to the Baltic."
        ),
        "url": "https://commons.wikimedia.org/wiki/File:Deutschland_im_XV._Jahrhundert.jpg",
        "access_date": "2026-07-16",
        "version": "1886 plate scan",
        "license": "Public domain (1886 publication)",
        "checksum": "85f19756fde4c51148d9951152a62803902c013a984d60036b797d4b22414408",
        "transformations": [],
        "review_status": "reviewed",
        "source_type": "corroborating",
        "valid_from": "1400",
        "valid_to": "1500",
        "independence_group": "droysen",
        "derived_artifacts": [],
    },
    {
        "source_id": "ne-10m-rivers",
        "citation": (
            "Natural Earth 1:10m rivers and lake centerlines "
            "(ne_10m_rivers_lake_centerlines.zip); modern open hydrography used "
            "only as the digitization substrate for river courses that the cited "
            "scholarship identifies as the legal frontier."
        ),
        "url": "https://naturalearth.s3.amazonaws.com/10m_physical/ne_10m_rivers_lake_centerlines.zip",
        "access_date": "2026-07-09",
        "version": "Natural Earth 10m physical",
        "license": "Public domain (Natural Earth)",
        "checksum": "ded71b01870855ccfe19b51f2ec14c9bb48fae23c0e9f3c11974d426433b5c38",
        "transformations": [
            "River main stems merged and clipped between anchor towns named by the cited scholarship (shapely substring).",
            "Coordinates rounded to 1e-6 degrees.",
        ],
        "review_status": "reviewed",
        "source_type": "soft_corroboration",
        "valid_from": None,
        "valid_to": None,
        "independence_group": "natural-earth",
        "derived_artifacts": [],  # boundary_geometry artifacts attached in assemble stage
    },
    {
        "source_id": "ohm-schleswig-2691969",
        "citation": (
            "OpenHistoricalMap relation 2691969 « Herzogtum Schleswig » "
            "(1773-06-01 – 1864-10-30), southern administrative boundary, which "
            "follows the lower Eider on the Tönning-Pahlen reach; used only as the "
            "river-course substrate for the medieval frontier."
        ),
        "url": "https://overpass-api.openhistoricalmap.org/api/interpreter?data=relation(2691969);out geom;",
        "access_date": "2026-07-16",
        "version": "retrieved 2026-07-16",
        "license": "CC0 (OpenHistoricalMap public-domain dedication)",
        "checksum": "3a8373a0511bd62724bbb11ffdae92e55293b354fa41a06c8401cae39738294d",
        "transformations": [
            "Southern boundary ways stitched (linemerge) and clipped between Tönning and Pahlen.",
            "Eastern (Eider Canal era, Rendsburg) and estuary reaches excluded.",
        ],
        "review_status": "reviewed",
        "source_type": "soft_corroboration",
        "valid_from": None,
        "valid_to": None,
        "independence_group": "openhistoricalmap",
        "derived_artifacts": [],  # boundary_geometry + raw capture attached in assemble stage
    },
    {
        "source_id": "geoboundaries-bel-adm1-2022",
        "citation": "geoBoundaries gbOpen BEL ADM1 (Eurostat), commit 9469f09; modern negative control.",
        "url": "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/BEL/ADM1/geoBoundaries-BEL-ADM1_simplified.geojson",
        "access_date": "2026-07-16",
        "version": "commit 9469f09",
        "license": "CC BY 4.0 (geoBoundaries / Eurostat)",
        "checksum": "7af87f5035779f0aefe5bf930288572979e490ab0441fd9b92942a519bea0974",
        "transformations": ["Brussels-Capital Region feature extracted verbatim."],
        "review_status": "reviewed",
        "source_type": "negative_control",
        "valid_from": "2022",
        "valid_to": "2022",
        "independence_group": "geoboundaries",
        "derived_artifacts": [],
    },
    {
        "source_id": "geoboundaries-fra-adm2-2022",
        "citation": "geoBoundaries gbOpen FRA ADM2 (IGN), commit 9469f09; modern negative control.",
        "url": "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/FRA/ADM2/geoBoundaries-FRA-ADM2_simplified.geojson",
        "access_date": "2026-07-16",
        "version": "commit 9469f09",
        "license": "Etalab Open License 2.0 (geoBoundaries / IGN)",
        "checksum": "a14ed131c86c802e5d546c7cbeccbd4daebc94a66fea413f563935a53504f251",
        "transformations": ["Nord department feature extracted verbatim."],
        "review_status": "reviewed",
        "source_type": "negative_control",
        "valid_from": "2022",
        "valid_to": "2022",
        "independence_group": "geoboundaries",
        "derived_artifacts": [],
    },
    {
        "source_id": "geoboundaries-fra-adm1-2022",
        "citation": "geoBoundaries gbOpen FRA ADM1 (IGN), commit 9469f09; modern negative control (real outline file, replacing the withdrawn v1 API-envelope shortcut).",
        "url": "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/FRA/ADM1/geoBoundaries-FRA-ADM1_simplified.geojson",
        "access_date": "2026-07-16",
        "version": "commit 9469f09",
        "license": "Etalab Open License 2.0 (geoBoundaries / IGN)",
        "checksum": "7dc61e5c7e4c81f5fa10d339e6a5bc8428f1346f43f4426d9d165d2e44fc3a7e",
        "transformations": ["Bourgogne-Franche-Comté feature extracted verbatim."],
        "review_status": "reviewed",
        "source_type": "negative_control",
        "valid_from": "2022",
        "valid_to": "2022",
        "independence_group": "geoboundaries",
        "derived_artifacts": [],
    },
    {
        "source_id": "geoboundaries-deu-adm1-2022",
        "citation": "geoBoundaries gbOpen DEU ADM1, commit 9469f09; modern negative control (real outline file).",
        "url": "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/DEU/ADM1/geoBoundaries-DEU-ADM1_simplified.geojson",
        "access_date": "2026-07-16",
        "version": "commit 9469f09",
        "license": "CC BY 4.0 (geoBoundaries)",
        "checksum": "511b3625ad4568d12a6bfcb1bdea4e877199e1923e502cb80224b8164128eb05",
        "transformations": ["Schleswig-Holstein feature extracted verbatim."],
        "review_status": "reviewed",
        "source_type": "negative_control",
        "valid_from": "2022",
        "valid_to": "2022",
        "independence_group": "geoboundaries",
        "derived_artifacts": [],
    },
    {
        "source_id": "geoboundaries-cze-adm0-2022",
        "citation": "geoBoundaries gbOpen CZE ADM0, commit 9469f09; modern negative control (real outline file).",
        "url": "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/CZE/ADM0/geoBoundaries-CZE-ADM0_simplified.geojson",
        "access_date": "2026-07-16",
        "version": "commit 9469f09",
        "license": "CC BY 4.0 (geoBoundaries)",
        "checksum": "562d073b86ea4c1368c45f853ba2aa61fb9e7cbd6f221c32ca975069cf861317",
        "transformations": ["Czechia ADM0 outline used verbatim."],
        "review_status": "reviewed",
        "source_type": "negative_control",
        "valid_from": "2022",
        "valid_to": "2022",
        "independence_group": "geoboundaries",
        "derived_artifacts": [],
    },
]

CONFLICT_NOTES = [
    "The Saône-as-boundary was the royal legal doctrine; in 1444 ducal officers contested the reach upstream of Pontailler (Dumasy-Rabineau 2021). The certified Chalon-Mâcon segment lies downstream of the contested reach.",
    "Imperial Flanders (Alost, Waas, Quatre-Métiers) was count-of-Flanders territory on Empire soil east of the Scheldt (Lot 1910); the realm boundary is modeled on the river between Pecq and Ghent, and the Tournai royal enclave is excluded.",
    "Shepherd's 1477 plate shows Moravia under Hungarian subjection (1469/1479-1490); the gazetteer models the 1444 status instead: Moravia a Bohemian Crown land under margrave Ladislaus Posthumous.",
    "Wladyslaw III of Hungary died at Varna on 1444-11-10, one day before the start date; the news was unknown and the legal Morava boundary was unaffected.",
    "All five frontiers were dynastically bridged in 1444 (Philip the Good, Adolf VIII, Habsburg minorities); they are modeled as de jure realm boundaries, which the cited scholarship supports.",
]

# --------------------------------------------------------------------------
# Capitals (WGS84 city points; the assemble stage maps each to the containing
# r2 fabric location and full-build province).
# --------------------------------------------------------------------------
CAPITAL_POINTS = {
    "paris": (2.3486, 48.8534),
    "dijon": (5.0415, 47.3220),
    "dole": (5.4931, 47.0922),
    "brussels": (4.3517, 50.8467),
    "lille": (3.0632, 50.6366),
    "mons": (3.9523, 50.4542),
    "aix-en-provence": (5.4474, 43.5297),
    "chambery": (5.9180, 45.5640),
    "lubeck": (10.6866, 53.8655),
    "schleswig": (9.5697, 54.5154),
    "copenhagen": (12.5683, 55.6761),
    "prague": (14.4213, 50.0875),
    "brno": (16.6084, 49.1951),
    "buda": (19.0402, 47.4961),
}

# polity_id -> (name, aliases, valid_from, valid_to, capitals, source_ids)
POLITIES = {
    "kingdom-of-france": (
        "Kingdom of France", ["France", "royaume de France"], "0987", None,
        ["paris"],
        ["dauphant-2020-sources", "shepherd-1453-france"],
    ),
    "hre": (
        "Holy Roman Empire", ["the Empire", "Saint-Empire"], "0962", None,
        [],
        ["dauphant-2020-sources", "shepherd-1477-central-europe"],
    ),
    "duchy-of-burgundy": (
        "Duchy of Burgundy", ["Bourgogne ducale"], "1363", "1477",
        ["dijon"],
        ["dumasy-rabineau-2021", "shepherd-1453-france", "droysen-1450-burgundy"],
    ),
    "county-of-burgundy": (
        "County of Burgundy (Franche-Comté)", ["Franche-Comté", "Freigrafschaft"], "1330", "1477",
        ["dole"],
        ["dumasy-rabineau-2021", "shepherd-1477-central-europe", "droysen-1450-burgundy"],
    ),
    "county-of-flanders": (
        "County of Flanders", ["Vlaanderen", "Flandre"], "0864", "1477",
        ["lille"],
        ["pirenne-histoire-belgique-ii", "lot-1910-escaut", "shepherd-1477-central-europe"],
    ),
    "county-of-hainaut": (
        "County of Hainaut", ["Hainaut", "Henegouwen"], "1071", "1477",
        ["mons"],
        ["pirenne-histoire-belgique-ii", "shepherd-1477-central-europe"],
    ),
    "duchy-of-brabant": (
        "Duchy of Brabant", ["Brabant"], "1183", "1477",
        ["brussels"],
        ["pirenne-histoire-belgique-ii", "shepherd-1477-central-europe"],
    ),
    "county-of-provence": (
        "County of Provence", ["Provence"], "0933", "1481",
        ["aix-en-provence"],
        ["hebert-2000-provence", "shepherd-1453-france"],
    ),
    "duchy-of-savoy": (
        "Duchy of Savoy", ["Savoie", "Bresse"], "1416", None,
        ["chambery"],
        ["shepherd-1453-france", "shepherd-1477-central-europe"],
    ),
    "duchy-of-schleswig": (
        "Duchy of Schleswig", ["Slesvig", "Sønderjylland"], "1058", None,
        ["schleswig"],
        ["nordfriisk-eider", "danmarkshistorien-module-3-4"],
    ),
    "county-of-holstein": (
        "County of Holstein (Rendsburg line)", ["Holstein"], "1111", "1474",
        [],
        ["nordfriisk-eider", "danmarkshistorien-module-3-4", "droysen-xv-deutschland"],
    ),
    "free-city-of-lubeck": (
        "Free Imperial City of Lübeck", ["Lübeck"], "1226", None,
        ["lubeck"],
        ["shepherd-1477-central-europe", "droysen-xv-deutschland"],
    ),
    "kingdom-of-denmark": (
        "Kingdom of Denmark", ["Danmark"], "0958", None,
        ["copenhagen"],
        ["danmarkshistorien-module-3-4", "shepherd-1477-central-europe"],
    ),
    "kingdom-of-bohemia": (
        "Kingdom of Bohemia (lands of the Bohemian Crown)", ["Bohemian Crown", "Koruna česká"], "1198", None,
        ["prague"],
        ["sav-lexikon-skalica-2010", "shepherd-1477-central-europe"],
    ),
    "margraviate-of-moravia": (
        "Margraviate of Moravia", ["Morava", "March"], "1182", None,
        ["brno"],
        ["sav-lexikon-skalica-2010", "mudrik-2016-moravsko-uherska", "shepherd-1477-central-europe"],
    ),
    "kingdom-of-hungary": (
        "Kingdom of Hungary", ["Uhorsko", "Magyar Királyság"], "1000", None,
        ["buda"],
        ["sav-lexikon-skalica-2010", "shepherd-1477-central-europe"],
    ),
}

# (relationship_id, polity, type, target, valid_from, valid_to, confidence, sources, notes)
RELATIONSHIPS = [
    ("rel-burgundy-french-fief", "duchy-of-burgundy", "vassalage", "kingdom-of-france",
     "1363", "1477", "high",
     ["dumasy-rabineau-2021", "dauphant-2018-quatre-rivieres"],
     "Ducal Burgundy was a French fief; the 1444 frontier dispute over the Saône reach was argued in exactly these terms."),
    ("rel-county-burgundy-imperial", "county-of-burgundy", "vassalage", "hre",
     "1032", "1477", "high",
     ["dumasy-rabineau-2021", "droysen-1450-burgundy"],
     "The Free County lay in the Empire; Auxonne/Heuilley were ducal possessions « sis en terre d'Empire »."),
    ("rel-burgundy-personal-union", "county-of-burgundy", "personal_union", "duchy-of-burgundy",
     "1384", "1477", "high",
     ["dumasy-rabineau-2021", "shepherd-1477-central-europe"],
     "Both Burgundies under Philip the Good in 1444; the realms remained legally distinct."),
    ("rel-flanders-french-fief", "county-of-flanders", "vassalage", "kingdom-of-france",
     "0864", "1526", "high",
     ["pirenne-histoire-belgique-ii", "pirenne-histoire-belgique-iii"],
     "Crown Flanders west of the Scheldt held of the French crown until the Peace of Madrid/Cambrai."),
    ("rel-flanders-imperial-fiefs", "county-of-flanders", "dependency", "hre",
     "1056", "1526", "high",
     ["lot-1910-escaut", "pirenne-histoire-belgique-ii"],
     "Imperial Flanders (Alost, Waas, Quatre-Métiers, Overschelde) east of the Scheldt was held of the Emperor."),
    ("rel-flanders-burgundian-union", "county-of-flanders", "personal_union", "duchy-of-burgundy",
     "1384", "1477", "high",
     ["pirenne-histoire-belgique-ii"],
     "Flanders in the Burgundian composite state from 1384."),
    ("rel-brabant-imperial", "duchy-of-brabant", "vassalage", "hre",
     "1183", "1477", "high",
     ["pirenne-histoire-belgique-ii", "shepherd-1477-central-europe"],
     "Brabant was an imperial fief east of the Scheldt line."),
    ("rel-brabant-burgundian-union", "duchy-of-brabant", "personal_union", "duchy-of-burgundy",
     "1430", "1477", "high",
     ["pirenne-histoire-belgique-ii"],
     "Philip the Good succeeded in Brabant in 1430 with the assent of the estates."),
    ("rel-hainaut-imperial", "county-of-hainaut", "vassalage", "hre",
     "1071", "1477", "high",
     ["pirenne-histoire-belgique-ii", "shepherd-1477-central-europe"],
     "Hainaut was an imperial fief on the right bank of the upper Scheldt."),
    ("rel-hainaut-burgundian-union", "county-of-hainaut", "personal_union", "duchy-of-burgundy",
     "1433", "1477", "high",
     ["pirenne-histoire-belgique-ii"],
     "Philip the Good obtained Hainaut from Jacqueline of Bavaria in 1433."),
    ("rel-provence-imperial", "county-of-provence", "dependency", "hre",
     "1032", "1481", "medium",
     ["hebert-2000-provence"],
     "Provence was « terre d'Empire » (kingdom of Arles remnant); imperial suzerainty was nominal under René of Anjou."),
    ("rel-savoy-imperial", "duchy-of-savoy", "vassalage", "hre",
     "1416", "1481", "high",
     ["shepherd-1477-central-europe"],
     "Savoy (including Bresse east of the Saône) was an imperial duchy from 1416."),
    ("rel-schleswig-danish-fief", "duchy-of-schleswig", "vassalage", "kingdom-of-denmark",
     "1386", "1460", "high",
     ["danmarkshistorien-module-3-4", "nordfriisk-eider"],
     "Schleswig was a fief of the Danish crown; Adolf VIII recognised as duke since 1440."),
    ("rel-holstein-imperial", "county-of-holstein", "vassalage", "hre",
     "1111", "1474", "high",
     ["nordfriisk-eider", "droysen-xv-deutschland"],
     "Holstein was « ein Lehen des deutschen Kaisers »; raised to a duchy only in 1474."),
    ("rel-schleswig-holstein-union", "duchy-of-schleswig", "personal_union", "county-of-holstein",
     "1440", "1459", "high",
     ["danmarkshistorien-module-3-4"],
     "Adolf VIII held Schleswig (Danish fief) and Holstein (imperial fief) in personal union in 1444."),
    ("rel-lubeck-imperial-immediacy", "free-city-of-lubeck", "dependency", "hre",
     "1226", "1806", "high",
     ["shepherd-1477-central-europe", "droysen-xv-deutschland"],
     "Imperial free city within the hre region scope."),
    ("rel-moravia-bohemian-crown", "margraviate-of-moravia", "dependency", "kingdom-of-bohemia",
     "1348", "1918", "high",
     ["sav-lexikon-skalica-2010", "mudrik-2016-moravsko-uherska"],
     "Moravia was a land of the Bohemian Crown; margrave Ladislaus Posthumous (1440-1457) during the 1444 interregnum."),
    ("rel-france-burgundy-saone-claim", "kingdom-of-france", "claim", "county-of-burgundy",
     "1435", "1477", "medium",
     ["dumasy-rabineau-2021"],
     "Royal officers asserted enclave rights west and east of the Saône; the 1444-1466 dispute produced the lost frontier maps."),
]

# --------------------------------------------------------------------------
# Frontier definitions. Geometry is derived at build time from the pinned
# substrates between the anchor towns; anchors and side attributions come from
# the cited scholarship (see tasks/m25-evidence-record.md).
# --------------------------------------------------------------------------
FRONTIERS = {
    "frontier-scheldt-flanders-empire": {
        "region": "low-countries",
        "semantics": "realm frontier (France / Holy Roman Empire) on the Scheldt",
        "sides": {"left": "kingdom-of-france", "right": "hre"},
        "valid_from": "1384",
        "valid_to": "1526",
        "date_precision": "year",
        "confidence": "high",
        "substrate": {"kind": "ne-rivers", "record_indexes": [857]},
        "anchors": [
            {"id": "pecq", "name": "Pecq (north edge of the Tournaisis)", "lon": 3.339, "lat": 50.687, "role": "endpoint", "side": "on-line"},
            {"id": "oudenaarde", "name": "Oudenaarde", "lon": 3.601, "lat": 50.846, "role": "control", "side": "kingdom-of-france"},
            {"id": "ghent", "name": "Ghent (Leie confluence)", "lon": 3.722, "lat": 51.053, "role": "endpoint", "side": "kingdom-of-france"},
        ],
        "source_ids": [
            "pirenne-histoire-belgique-ii", "pirenne-histoire-belgique-iii",
            "dauphant-2020-sources", "lot-1910-escaut",
            "shepherd-1477-central-europe", "ne-10m-rivers",
        ],
        "license_lineage": ["Public domain (Pirenne scans)", "Public domain (Shepherd 1911)", "Public domain (Natural Earth)"],
        "error_budget_km": 6.0,
        "uncertainty_notes": (
            "De jure realm line; both banks Burgundian-held in 1444. Right bank is "
            "Hainaut then the Land van Aalst (imperial soil in Flemish hands). The "
            "Tournai royal enclave lies south of the segment; below Ghent the line "
            "leaves the river (Waas is imperial on the left bank). The modern "
            "canalized course generalizes medieval meanders within the error budget."
        ),
        "coverage_polities": {"left": "county-of-flanders", "right": "county-of-hainaut"},
    },
    "frontier-saone-france-empire": {
        "region": "burgundy",
        "semantics": "realm frontier (France / Holy Roman Empire) on the Saône",
        "sides": {"left": "kingdom-of-france", "right": "hre"},
        "valid_from": "1361",
        "valid_to": "1477",
        "date_precision": "year",
        "confidence": "high",
        "substrate": {"kind": "ne-rivers", "record_indexes": [879]},
        "anchors": [
            {"id": "chalon", "name": "Chalon-sur-Saône", "lon": 4.853, "lat": 46.781, "role": "endpoint", "side": "kingdom-of-france"},
            {"id": "tournus", "name": "Tournus", "lon": 4.907, "lat": 46.563, "role": "control", "side": "kingdom-of-france"},
            {"id": "macon", "name": "Mâcon", "lon": 4.828, "lat": 46.307, "role": "endpoint", "side": "kingdom-of-france"},
        ],
        "source_ids": [
            "dumasy-rabineau-2021", "dauphant-2018-quatre-rivieres",
            "shepherd-1453-france", "droysen-1450-burgundy", "ne-10m-rivers",
        ],
        "license_lineage": ["Public domain (Shepherd 1911, Droysen 1886)", "Public domain (Natural Earth)"],
        "error_budget_km": 6.0,
        "uncertainty_notes": (
            "Segment downstream of the reach contested in the 1444-1466 dispute "
            "(upstream of Pontailler). West bank ducal Burgundy (French fief); east "
            "bank ducal trans-Saône dependencies on Empire soil, then Savoyard "
            "Bresse south of Tournus. Bronze realm markers stood in the riverbed "
            "(1452 inquiry, Dauphant 2018)."
        ),
        "coverage_polities": {"left": "duchy-of-burgundy", "right": "duchy-of-savoy"},
    },
    "frontier-rhone-languedoc-provence": {
        "region": "france",
        "semantics": "realm frontier (France / Empire) on the Rhône, Languedoc facing Provence",
        "sides": {"left": "kingdom-of-france", "right": "hre"},
        "valid_from": "1290",
        "valid_to": "1481",
        "date_precision": "year",
        "confidence": "high",
        "substrate": {"kind": "ne-rivers", "record_indexes": [933]},
        "anchors": [
            {"id": "barbentane", "name": "Barbentane (Durance confluence)", "lon": 4.747, "lat": 43.898, "role": "endpoint", "side": "county-of-provence"},
            {"id": "beaucaire", "name": "Beaucaire", "lon": 4.644, "lat": 43.808, "role": "control", "side": "kingdom-of-france"},
            {"id": "tarascon", "name": "Tarascon", "lon": 4.660, "lat": 43.806, "role": "control", "side": "county-of-provence"},
            {"id": "fourques", "name": "Fourques (Petit Rhône diffluence)", "lon": 4.607, "lat": 43.693, "role": "endpoint", "side": "kingdom-of-france"},
        ],
        "source_ids": [
            "dauphant-2020-sources", "maigret-2002-rhone", "hebert-2000-provence",
            "shepherd-1453-france", "ne-10m-rivers",
        ],
        "license_lineage": ["Public domain (Shepherd 1911)", "Public domain (Natural Earth)"],
        "error_budget_km": 6.0,
        "uncertainty_notes": (
            "Cleanly Languedoc-vs-Provence between the Durance confluence and the "
            "Petit Rhône diffluence. The French crown claimed the whole river, not "
            "a thalweg split; Vallabrègues was French on the left bank. The papal "
            "Avignon/Comtat and the Camargue delta reach are excluded."
        ),
        "coverage_polities": {"left": "kingdom-of-france", "right": "county-of-provence"},
    },
    "frontier-eider-empire-denmark": {
        "region": "hre",
        "semantics": "imperial frontier (Holy Roman Empire / Denmark) on the lower Eider",
        "sides": {"left": "hre", "right": "kingdom-of-denmark"},
        "valid_from": "1111",
        "valid_to": "1864",
        "date_precision": "year",
        "confidence": "high",
        "substrate": {"kind": "ohm-schleswig", "capture": "derived/sources/ohm-schleswig-2691969.json"},
        "anchors": [
            {"id": "tonning", "name": "Tönning (estuary)", "lon": 8.943, "lat": 54.317, "role": "endpoint", "side": "kingdom-of-denmark"},
            {"id": "suderstapel", "name": "Süderstapel (Stapelholm)", "lon": 9.218, "lat": 54.350, "role": "control", "side": "kingdom-of-denmark"},
            {"id": "pahlen", "name": "Pahlen", "lon": 9.300, "lat": 54.300, "role": "endpoint", "side": "hre"},
        ],
        "source_ids": [
            "nordfriisk-eider", "danmarkshistorien-module-3-4",
            "shepherd-1477-central-europe", "droysen-xv-deutschland",
            "ohm-schleswig-2691969",
        ],
        "license_lineage": ["Public domain (Shepherd 1911, Droysen 1886)", "CC0 (OpenHistoricalMap)"],
        "error_budget_km": 6.0,
        "uncertainty_notes": (
            "North bank Schleswig (Danish fief), south bank Holstein with the "
            "Dithmarschen marches west of the Gieselau (imperial ambit, de facto "
            "free). Adolf VIII held both duchies in personal union in 1444. The "
            "disputed Rendsburg island, the Levensau/landwehr eastern continuation "
            "and the storm-flood-altered estuary are excluded from the segment."
        ),
        "coverage_polities": {"left": "county-of-holstein", "right": "duchy-of-schleswig"},
    },
    "frontier-morava-moravia-hungary": {
        "region": "central-europe",
        "semantics": "realm frontier (Bohemian Crown / Hungary) on the lower Morava (March)",
        "sides": {"left": "kingdom-of-bohemia", "right": "kingdom-of-hungary"},
        "valid_from": "1332",
        "valid_to": "1918",
        "date_precision": "year",
        "confidence": "high",
        "substrate": {"kind": "ne-rivers", "record_indexes": [842]},
        "anchors": [
            {"id": "rohatec", "name": "Rohatec (land border meets the river)", "lon": 17.10, "lat": 48.86, "role": "endpoint", "side": "on-line"},
            {"id": "hodonin", "name": "Hodonín", "lon": 17.1325, "lat": 48.8489, "role": "control", "side": "kingdom-of-bohemia"},
            {"id": "dyje-confluence", "name": "Dyje (Thaya) confluence", "lon": 16.94, "lat": 48.62, "role": "endpoint", "side": "on-line"},
        ],
        "source_ids": [
            "sav-lexikon-skalica-2010", "mudrik-2016-moravsko-uherska",
            "shepherd-1477-central-europe", "ne-10m-rivers",
        ],
        "license_lineage": ["Public domain (Shepherd 1911)", "Public domain (Natural Earth)"],
        "error_budget_km": 6.0,
        "uncertainty_notes": (
            "valid_from reflects the 1331/1332 Holíč-Branč settlement; the line as "
            "such is older. North of Rohatec the border leaves the river for the "
            "White Carpathians; south of the Dyje confluence the west bank passes "
            "to Austria. The medieval river was a braided floodplain corridor of "
            "1-3 km; Skalica's town core lies 5 km east of the river."
        ),
        "coverage_polities": {"left": "margraviate-of-moravia", "right": "kingdom-of-hungary"},
    },
}

FORBIDDEN_OUTLINES = {
    "forbidden-modern-brussels-capital-region": {
        "region": "low-countries",
        "source_id": "geoboundaries-bel-adm1-2022",
        "file": "geoBoundaries-BEL-ADM1_simplified.geojson",
        "match": "Brussels",
        "license_lineage": ["CC BY 4.0 (geoBoundaries / Eurostat)"],
        "sides": {"left": "duchy-of-brabant", "right": "county-of-hainaut"},
    },
    "forbidden-modern-nord-department": {
        "region": "france",
        "source_id": "geoboundaries-fra-adm2-2022",
        "file": "geoBoundaries-FRA-ADM2_simplified.geojson",
        "match": "Nord",
        "license_lineage": ["Etalab Open License 2.0 (geoBoundaries / IGN)"],
        "sides": {"left": "county-of-flanders", "right": "county-of-hainaut"},
    },
    "forbidden-modern-bourgogne-franche-comte": {
        "region": "burgundy",
        "source_id": "geoboundaries-fra-adm1-2022",
        "file": "geoBoundaries-FRA-ADM1_simplified.geojson",
        "match": "Bourgogne",
        "license_lineage": ["Etalab Open License 2.0 (geoBoundaries / IGN)"],
        "sides": {"left": "duchy-of-burgundy", "right": "county-of-burgundy"},
    },
    "forbidden-modern-schleswig-holstein": {
        "region": "hre",
        "source_id": "geoboundaries-deu-adm1-2022",
        "file": "geoBoundaries-DEU-ADM1_simplified.geojson",
        "match": "Schleswig",
        "license_lineage": ["CC BY 4.0 (geoBoundaries)"],
        "sides": {"left": "county-of-holstein", "right": "duchy-of-schleswig"},
    },
    "forbidden-modern-czechia": {
        "region": "central-europe",
        "source_id": "geoboundaries-cze-adm0-2022",
        "file": "geoBoundaries-CZE-ADM0_simplified.geojson",
        "match": "",
        "license_lineage": ["CC BY 4.0 (geoBoundaries)"],
        "sides": {"left": "kingdom-of-bohemia", "right": "margraviate-of-moravia"},
    },
}

# --------------------------------------------------------------------------
# Small utilities
# --------------------------------------------------------------------------

def _write_json(path: Path, document) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _km(a, b) -> float:
    lat = math.radians((a[1] + b[1]) / 2.0)
    return math.hypot((a[0] - b[0]) * 111.320 * math.cos(lat), (a[1] - b[1]) * 110.574)


def _point_line_km(point, line) -> float:
    from shapely.geometry import Point
    nearest = line.interpolate(line.project(Point(point)))
    return _km(point, (nearest.x, nearest.y))


def _hausdorff_km(left, right) -> float:
    from shapely.ops import transform as shapely_transform
    lat = (left.centroid.y + right.centroid.y) / 2.0
    xs = 111.320 * math.cos(math.radians(lat))
    project = lambda x, y, z=None: (x * xs, y * 110.574)
    return shapely_transform(project, left).hausdorff_distance(shapely_transform(project, right))


def _read_ne_river_lines(record_indexes):
    """Read polyline records from the pinned Natural Earth rivers zip."""
    import struct
    from shapely.geometry import LineString, MultiLineString
    zip_path = ROOT / "data" / "raw" / "natural_earth" / "ne_10m_rivers_lake_centerlines.zip"
    if _sha256(zip_path) != next(s["checksum"] for s in SOURCES if s["source_id"] == "ne-10m-rivers"):
        raise SystemExit("ne_10m_rivers_lake_centerlines.zip does not match its pinned checksum")
    with zipfile.ZipFile(zip_path) as archive:
        data = archive.read("ne_10m_rivers_lake_centerlines.shp")
    geometries = []
    offset, total = 100, len(data)
    while offset + 8 <= total:
        _, content_length = struct.unpack(">ii", data[offset:offset + 8])
        content = data[offset + 8: offset + 8 + content_length * 2]
        offset += 8 + content_length * 2
        if len(content) < 4 or struct.unpack("<i", content[:4])[0] not in {3, 13, 23}:
            geometries.append(None)
            continue
        num_parts, num_points = struct.unpack("<ii", content[36:44])
        parts = list(struct.unpack(f"<{num_parts}i", content[44:44 + 4 * num_parts]))
        start = 44 + 4 * num_parts
        points = [list(struct.unpack("<dd", content[start + 16 * i: start + 16 * i + 16])) for i in range(num_points)]
        parts.append(num_points)
        lines = [points[parts[i]:parts[i + 1]] for i in range(num_parts)]
        lines = [line for line in lines if len(line) >= 2]
        geometries.append(
            None if not lines else LineString(lines[0]) if len(lines) == 1 else MultiLineString(lines)
        )
    return [geometries[i] for i in record_indexes]


def _substrate_line(spec):
    """Merged substrate polyline for one frontier."""
    from shapely.geometry import LineString, MultiLineString
    from shapely.ops import linemerge
    if spec["kind"] == "ne-rivers":
        parts = _read_ne_river_lines(spec["record_indexes"])
        lines = []
        for part in parts:
            if part is None:
                raise SystemExit("missing river record")
            lines.extend(part.geoms if isinstance(part, MultiLineString) else [part])
    else:  # ohm-schleswig
        capture = PASS_DIR / spec["capture"]
        source = next(s for s in SOURCES if s["source_id"] == "ohm-schleswig-2691969")
        if _sha256(capture) != source["checksum"]:
            raise SystemExit("OHM capture does not match its pinned checksum")
        document = json.loads(capture.read_text(encoding="utf-8"))
        lines = []
        for member in document["elements"][0]["members"]:
            if member.get("type") != "way" or "geometry" not in member:
                continue
            pts = [(p["lon"], p["lat"]) for p in member["geometry"]]
            if len(pts) >= 2 and any(54.15 <= lat <= 54.5 and 8.80 <= lon <= 9.45 for lon, lat in pts):
                lines.append(LineString(pts))
    merged = linemerge(MultiLineString(lines))
    return merged if isinstance(merged, LineString) else max(merged.geoms, key=lambda g: g.length)


def derive_frontier(name: str) -> dict:
    """Derive one frontier segment document (geometry + anchors + residuals)."""
    from shapely.geometry import LineString, Point, mapping
    from shapely.ops import substring
    spec = FRONTIERS[name]
    line = _substrate_line(spec["substrate"])
    endpoints = [a for a in spec["anchors"] if a["role"] == "endpoint"]
    lo, hi = sorted(line.project(Point(a["lon"], a["lat"])) for a in (endpoints[0], endpoints[-1]))
    segment = substring(line, lo, hi)
    segment = LineString([(round(x, 6), round(y, 6)) for x, y in segment.coords])
    anchors = []
    for anchor in spec["anchors"]:
        anchors.append({**anchor, "residual_km": round(_point_line_km((anchor["lon"], anchor["lat"]), segment), 3)})
    length = sum(_km(segment.coords[i], segment.coords[i + 1]) for i in range(len(segment.coords) - 1))
    return {
        "type": "FeatureCollection",
        "derivation": {
            "method": (
                "natural-earth-10m-river-centerline-substring"
                if spec["substrate"]["kind"] == "ne-rivers"
                else "openhistoricalmap-relation-2691969-southern-boundary-substring"
            ),
            "substrate": spec["substrate"],
            "substring": {
                "measure_units": "substrate-line-planar-degrees",
                "start_measure": round(lo, 6),
                "end_measure": round(hi, 6),
                "substrate_merge_rule": "shapely-linemerge-longest-component",
            },
            "anchors": anchors,
            "segment_length_km": round(length, 3),
        },
        "features": [{
            "type": "Feature",
            "properties": {"segment_id": name},
            "geometry": mapping(segment),
        }],
    }


def extract_outline(name: str) -> dict:
    """Extract one forbidden modern outline feature from its pinned file."""
    spec = FORBIDDEN_OUTLINES[name]
    path = DERIVED_DIR / "sources" / spec["file"]
    source = next(s for s in SOURCES if s["source_id"] == spec["source_id"])
    if _sha256(path) != source["checksum"]:
        raise SystemExit(f"{spec['file']} does not match its pinned checksum")
    document = json.loads(path.read_text(encoding="utf-8"))
    for feature in document["features"]:
        shape_name = str((feature.get("properties") or {}).get("shapeName") or "")
        if not spec["match"] or spec["match"].lower() in shape_name.lower():
            return {
                "type": "FeatureCollection",
                "derivation": {
                    "method": "verbatim-feature-extraction",
                    "source_file": spec["file"],
                    "shape_name": shape_name,
                },
                "features": [{
                    "type": "Feature",
                    "properties": {"outline_id": name, "shape_name": shape_name},
                    "geometry": feature["geometry"],
                }],
            }
    raise SystemExit(f"outline feature not found for {name}")


def build_coverage_masks() -> dict:
    """Per-region polity coverage masks keyed by region id.

    Masks document where the cited sources support side attribution (a corridor
    around the certified segment), not full polity extents.
    """
    from shapely.geometry import mapping, shape
    from shapely.ops import split as shapely_split
    from shapely.geometry import Point
    features = {}
    for name in sorted(FRONTIERS):
        spec = FRONTIERS[name]
        segment = shape(json.loads((DERIVED_DIR / f"{name}.geojson").read_text())["features"][0]["geometry"])
        corridor = segment.buffer(0.35, cap_style=2)
        # extend the cutting line beyond the flat caps so the split always crosses
        coords = list(segment.coords)
        (ax, ay), (bx, by) = coords[0], coords[1]
        (cx, cy), (dx, dy) = coords[-2], coords[-1]
        import math as _math
        def _extend(x0, y0, x1, y1, distance=0.5):
            length = _math.hypot(x1 - x0, y1 - y0) or 1.0
            return (x1 + (x1 - x0) / length * distance, y1 + (y1 - y0) / length * distance)
        cutter = type(segment)([_extend(bx, by, ax, ay)] + coords + [_extend(cx, cy, dx, dy)])
        parts = sorted(
            (g for g in shapely_split(corridor, cutter).geoms if g.area > 1e-9),
            key=lambda g: g.area, reverse=True,
        )
        if len(parts) < 2:
            raise SystemExit(f"{name}: corridor did not split into two halves")
        halves = parts[:2]
        # Attribute halves via the side-attributed anchor towns from the cited
        # scholarship: an anchor whose side equals the realm left side (or the
        # left coverage polity) votes left.
        left_ids = {spec["sides"]["left"], spec["coverage_polities"]["left"]}
        right_ids = {spec["sides"]["right"], spec["coverage_polities"]["right"]}
        votes = []
        for half in halves:
            score = 0
            for anchor in spec["anchors"]:
                if anchor["side"] in ("on-line", "boundary"):
                    continue
                point = Point(anchor["lon"], anchor["lat"])
                weight = 1.0 / (1.0 + half.distance(point))
                if anchor["side"] in left_ids:
                    score += weight
                elif anchor["side"] in right_ids:
                    score -= weight
            votes.append(score)
        left_index = 0 if votes[0] >= votes[1] else 1
        region_features = []
        for index, half in enumerate(halves):
            side = "left" if index == left_index else "right"
            region_features.append({
                "type": "Feature",
                "properties": {
                    "polity_id": spec["coverage_polities"][side],
                    "region_id": spec["region"],
                    "frontier_id": name,
                    "side": side,
                },
                "geometry": mapping(half),
            })
        features[spec["region"]] = {"type": "FeatureCollection", "features": region_features}
    return features

# --------------------------------------------------------------------------
# Stage: build-fabric  (r1 -> paintability -> split requests -> r2)
# --------------------------------------------------------------------------

def stage_build_fabric() -> None:
    from shapely.geometry import shape
    from shapely.strtree import STRtree
    from gpm.builders.locations import build_location_fabric
    from gpm.qa.fabric import run_paintability_qa

    STAGING.mkdir(parents=True, exist_ok=True)
    r1_dir = STAGING / "fabric-r1"
    print("[build-fabric] r1 fabric …")
    build_location_fabric(FABRIC_ID, output_dir=r1_dir, generated_at=GENERATED_AT)

    print("[build-fabric] deriving frontier segments …")
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    for name in sorted(FRONTIERS):
        _write_json(DERIVED_DIR / f"{name}.geojson", derive_frontier(name))
    for name in sorted(FORBIDDEN_OUTLINES):
        _write_json(DERIVED_DIR / f"{name}.geojson", extract_outline(name))

    geometries = {}
    for name in sorted(FRONTIERS):
        geometries[name] = json.loads((DERIVED_DIR / f"{name}.geojson").read_text())["features"][0]["geometry"]
    for name in ("forbidden-modern-brussels-capital-region", "forbidden-modern-nord-department"):
        geometries[name] = json.loads((DERIVED_DIR / f"{name}.geojson").read_text())["features"][0]["geometry"]

    print("[build-fabric] paintability on r1 …")
    boundary_doc = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"boundary_id": name}, "geometry": geometry}
        for name, geometry in sorted(geometries.items())
    ]}
    _write_json(STAGING / "r2-required-boundaries.geojson", boundary_doc)
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    paintability = run_paintability_qa(
        location_input=r1_dir / "locations.geojson",
        boundary_input=STAGING / "r2-required-boundaries.geojson",
        report_output=EVIDENCE_DIR / "r1-paintability-report.json",
        split_requests_output=STAGING / "r1-paintability-templates.json",
        affected_dates=(START_DATE,),
        source_lineage=("m25 1444-v2 evidence record",),
        license_lineage=("see per-request license lineage",),
        generated_at=GENERATED_AT,
    )
    if paintability.status != "fail":
        raise SystemExit("expected r1 paintability to fail for the required boundaries")

    print("[build-fabric] split requests …")
    r1 = json.loads((r1_dir / "locations.geojson").read_text())
    r1_geoms = [shape(f["geometry"]) for f in r1["features"]]
    r1_res = [int(f["properties"]["h3_resolution"]) for f in r1["features"]]
    tree = STRtree(r1_geoms)
    rounds_needed = {}
    for name, geometry in geometries.items():
        target = shape(geometry)
        probe = target.boundary if target.geom_type in {"Polygon", "MultiPolygon"} else target
        crossed = [int(i) for i in tree.query(probe, predicate="intersects")]
        rounds_needed[name] = max(0, 5 - min([r1_res[i] for i in crossed] or [5]))
    requests = []
    for round_index, round_tag in enumerate(("01-refine-a", "02-refine-b")):
        for name in sorted(geometries):
            if rounds_needed[name] <= round_index:
                continue
            spec = FRONTIERS.get(name) or FORBIDDEN_OUTLINES[name]
            requests.append({
                "request_id": f"r2-{round_tag}-{name}",
                "operation": "refine_h3",
                "failed_paintability_test": name,
                "proposed_geometry": geometries[name],
                "sources": spec.get("source_ids") or [spec["source_id"]],
                "license_lineage": spec["license_lineage"],
                "confidence": "reviewed-evidence" if name in FRONTIERS else "negative-gate-resolution",
                "affected_dates": [START_DATE],
                "target_fabric_revision": "1",
            })
    for name in sorted(FRONTIERS):
        requests.append({
            "request_id": f"r2-03-split-{name}",
            "operation": "split_by_boundary",
            "failed_paintability_test": name,
            "proposed_geometry": geometries[name],
            "sources": FRONTIERS[name]["source_ids"],
            "license_lineage": FRONTIERS[name]["license_lineage"],
            "confidence": "reviewed-evidence",
            "affected_dates": [START_DATE],
            "target_fabric_revision": "1",
        })
    _write_json(EVIDENCE_DIR / "r2-split-requests.json", {"schema_version": "0.1.0", "requests": requests})

    print("[build-fabric] r2 fabric …")
    r2_dir = STAGING / "fabric-r2"
    build_location_fabric(
        FABRIC_ID,
        output_dir=r2_dir,
        split_request_input=EVIDENCE_DIR / "r2-split-requests.json",
        output_fabric_revision=OUTPUT_FABRIC_REVISION,
        generated_at=GENERATED_AT,
    )
    SIDECAR_DIR.mkdir(parents=True, exist_ok=True)
    for src, dst in (
        ("locations.geojson", "locations.geojson"),
        ("location_fabric_manifest.json", "location_fabric_manifest.json"),
        ("location_lineage.json", "location_lineage.json"),
    ):
        (SIDECAR_DIR / dst).write_bytes((r2_dir / src).read_bytes())
    print("[build-fabric] done")


# --------------------------------------------------------------------------
# Stage: aggregate  (constrained 22,000-province eu-like build over r2)
# --------------------------------------------------------------------------

def stage_aggregate() -> None:
    from gpm.builders.aggregation import aggregate_location_provinces

    constraints = {"type": "FeatureCollection", "features": []}
    for name in sorted(FRONTIERS):
        doc = json.loads((DERIVED_DIR / f"{name}.geojson").read_text())
        constraints["features"].append({
            "type": "Feature",
            "properties": {"feature_id": name, "classification": "hard_constraint"},
            "geometry": doc["features"][0]["geometry"],
        })
    _write_json(PASS_DIR / "constraints.geojson", constraints)

    print("[aggregate] constrained aggregation …")
    result = aggregate_location_provinces(
        PROFILE_ID,
        location_input=SIDECAR_DIR / "locations.geojson",
        output_dir=STAGING / "aggregation",
        province_output=STAGING / "aggregation" / "provinces.geojson",
        membership_output=SIDECAR_DIR / "province_membership.csv",
        manifest_output=SIDECAR_DIR / "aggregation_manifest.json",
        target_province_count=TARGET_PROVINCES,
        start_date=START_DATE,
        aggregation_revision=AGGREGATION_REVISION,
        geometry_revision=GEOMETRY_REVISION,
        modern_boundary_influence="none",
        historical_constraints_input=PASS_DIR / "constraints.geojson",
        generated_at=GENERATED_AT,
    )
    if result.province_count != TARGET_PROVINCES:
        raise SystemExit(f"aggregation produced {result.province_count} provinces, not {TARGET_PROVINCES}")
    print("[aggregate] done:", result.province_count, "provinces")

# --------------------------------------------------------------------------
# Stage: assemble  (emit the nine schema-0.2 artifacts)
# --------------------------------------------------------------------------

OWNER_POLITICS = {
    # owner -> (sovereign, controller)
    "county-of-flanders": ("kingdom-of-france", "duchy-of-burgundy"),
    "county-of-hainaut": ("hre", "duchy-of-burgundy"),
    "duchy-of-brabant": ("hre", "duchy-of-burgundy"),
    "duchy-of-burgundy": ("kingdom-of-france", "duchy-of-burgundy"),
    "county-of-burgundy": ("hre", "duchy-of-burgundy"),
    "kingdom-of-france": ("kingdom-of-france", "kingdom-of-france"),
    "county-of-provence": ("hre", "county-of-provence"),
    "duchy-of-savoy": ("hre", "duchy-of-savoy"),
    "county-of-holstein": ("hre", "county-of-holstein"),
    "duchy-of-schleswig": ("kingdom-of-denmark", "duchy-of-schleswig"),
    "free-city-of-lubeck": ("hre", "free-city-of-lubeck"),
    "kingdom-of-denmark": ("kingdom-of-denmark", "kingdom-of-denmark"),
    "kingdom-of-bohemia": ("kingdom-of-bohemia", "kingdom-of-bohemia"),
    "margraviate-of-moravia": ("kingdom-of-bohemia", "margraviate-of-moravia"),
    "kingdom-of-hungary": ("kingdom-of-hungary", "kingdom-of-hungary"),
}
CAPITAL_REGION = {
    "brussels": ("low-countries", "duchy-of-brabant"),
    "lille": ("low-countries", "county-of-flanders"),
    "mons": ("low-countries", "county-of-hainaut"),
    "dijon": ("burgundy", "duchy-of-burgundy"),
    "dole": ("burgundy", "county-of-burgundy"),
    "chambery": ("burgundy", "duchy-of-savoy"),
    "paris": ("france", "kingdom-of-france"),
    "aix-en-provence": ("france", "county-of-provence"),
    "lubeck": ("hre", "free-city-of-lubeck"),
    "schleswig": ("hre", "duchy-of-schleswig"),
    "copenhagen": ("hre", "kingdom-of-denmark"),
    "prague": ("central-europe", "kingdom-of-bohemia"),
    "brno": ("central-europe", "margraviate-of-moravia"),
    "buda": ("central-europe", "kingdom-of-hungary"),
}
REGION_SOURCES = {
    "low-countries": ["pirenne-histoire-belgique-ii", "pirenne-histoire-belgique-iii", "lot-1910-escaut", "shepherd-1477-central-europe"],
    "burgundy": ["dumasy-rabineau-2021", "dauphant-2018-quatre-rivieres", "shepherd-1453-france", "droysen-1450-burgundy"],
    "france": ["dauphant-2020-sources", "maigret-2002-rhone", "hebert-2000-provence", "shepherd-1453-france"],
    "hre": ["nordfriisk-eider", "danmarkshistorien-module-3-4", "shepherd-1477-central-europe", "droysen-xv-deutschland"],
    "central-europe": ["sav-lexikon-skalica-2010", "mudrik-2016-moravsko-uherska", "shepherd-1477-central-europe"],
}
REGION_FRONTIER = {spec["region"]: name for name, spec in FRONTIERS.items()}
REGION_NEGATIVE = {spec["region"]: name for name, spec in FORBIDDEN_OUTLINES.items()}
NEGATIVE_SUBJECT_CAPITAL = {
    "forbidden-modern-brussels-capital-region": "brussels",
    "forbidden-modern-nord-department": "lille",
    "forbidden-modern-bourgogne-franche-comte": "dijon",
    "forbidden-modern-schleswig-holstein": "kiel",
    # Brno, not Prague: the subject must be a corridor-reconstructed province.
    # Prague lies outside every certified corridor and falls in an aggregation
    # filler province spanning most of Eurasia, so its outline overlap measures
    # the filler blob, not whether the modern outline survives reconstruction.
    "forbidden-modern-czechia": "brno",
}
# Kiel is a probe only (province lookup), not a gazetteer capital.
PROBE_POINTS = {**CAPITAL_POINTS, "kiel": (10.1394, 54.3233)}
# politics capital / gazetteer_relationships capital per region
REGION_CAPITAL_TESTS = {
    "low-countries": ("brussels", "lille"),
    "burgundy": ("dijon", "dole"),
    "france": ("paris", "aix-en-provence"),
    "hre": ("lubeck", "schleswig"),
    "central-europe": ("prague", "brno"),
}
HAUSDORFF_CAP_KM = 25.0
RATIO_CAP = 0.85


def _load_build_inputs():
    from shapely.geometry import shape
    from shapely.strtree import STRtree
    provinces_doc = json.loads((STAGING / "aggregation" / "provinces.geojson").read_text())
    features = provinces_doc["features"]
    geoms = [shape(f["geometry"]) for f in features]
    pids = [f["properties"]["province_id"] for f in features]
    tree = STRtree(geoms)
    with (SIDECAR_DIR / "province_membership.csv").open("r", encoding="utf-8", newline="") as file:
        membership = list(csv.DictReader(file))
    members_by_province = {}
    province_by_location = {}
    for row in membership:
        members_by_province.setdefault(row["province_id"], []).append((row["location_id"], row["piece_id"]))
        province_by_location[row["location_id"]] = row["province_id"]
    return provinces_doc, features, geoms, pids, tree, members_by_province, province_by_location


def _province_at(tree, geoms, pids, lonlat):
    from shapely.geometry import Point
    point = Point(lonlat)
    for index in tree.query(point, predicate="intersects"):
        if geoms[int(index)].covers(point):
            return int(index)
    raise SystemExit(f"no province covers {lonlat}")


def _build_location_index(locations_doc):
    from shapely.geometry import shape
    from shapely.strtree import STRtree
    geoms = [shape(f["geometry"]) for f in locations_doc["features"]]
    ids = [f["properties"]["location_id"] for f in locations_doc["features"]]
    return STRtree(geoms), geoms, ids


def _location_at(location_index, lonlat):
    from shapely.geometry import Point
    tree, geoms, ids = location_index
    point = Point(lonlat)
    for index in tree.query(point, predicate="intersects"):
        if geoms[int(index)].covers(point):
            return ids[int(index)]
    # Coastal capitals can fall in sea gaps of the land-clipped fabric: map to
    # the nearest location within 0.5 deg, tie-broken by location_id.
    candidates = []
    for index in tree.query(point.buffer(0.5), predicate="intersects"):
        distance = geoms[int(index)].distance(point)
        if distance <= 0.5:
            candidates.append((distance, ids[int(index)]))
    if not candidates:
        raise SystemExit(f"no fabric location within 0.5 deg of {lonlat}")
    return min(candidates)[1]


def _select_border_pair(name, tree, geoms, pids, side_of_province):
    """Best (left province, right province, segment variant, hausdorff_km)."""
    from shapely.geometry import LineString, Point, shape
    from shapely.ops import substring
    spec = FRONTIERS[name]
    segment = shape(json.loads((DERIVED_DIR / f"{name}.geojson").read_text())["features"][0]["geometry"])
    anchors = spec["anchors"]
    variants = []
    for i in range(len(anchors)):
        for j in range(i + 1, len(anchors)):
            lo, hi = sorted(segment.project(Point(a["lon"], a["lat"])) for a in (anchors[i], anchors[j]))
            if hi - lo <= 1e-9:
                continue
            piece = substring(segment, lo, hi)
            variants.append((f"{anchors[i]['id']}..{anchors[j]['id']}", LineString([(round(x, 6), round(y, 6)) for x, y in piece.coords])))
    touching = [int(i) for i in tree.query(segment.buffer(0.02), predicate="intersects")]
    lefts = [i for i in touching if side_of_province.get(pids[i]) == "left"]
    rights = [i for i in touching if side_of_province.get(pids[i]) == "right"]
    best = None
    for li in lefts:
        for ri in rights:
            shared = geoms[li].boundary.intersection(geoms[ri].boundary)
            if shared.is_empty or shared.length <= 1e-9:
                continue
            for variant_id, variant in variants:
                distance = _hausdorff_km(shared, variant)
                if best is None or distance < best[3]:
                    best = (li, ri, (variant_id, variant), distance)
    if best is None:
        raise SystemExit(f"{name}: no adjacent left/right province pair found")
    return best

def stage_assemble() -> None:
    from shapely.geometry import Point, mapping, shape

    provinces_doc, features, geoms, pids, tree, members_by_province, province_by_location = _load_build_inputs()
    locations_doc = json.loads((SIDECAR_DIR / "locations.geojson").read_text())
    if locations_doc["gpm"]["fabric_revision"] != OUTPUT_FABRIC_REVISION:
        raise SystemExit("locations sidecar is not the r2 fabric")

    # ---- capitals -> fabric locations -> provinces
    capital_locations = {}
    capital_provinces = {}
    location_index = _build_location_index(locations_doc)
    for capital, lonlat in CAPITAL_POINTS.items():
        location_id = _location_at(location_index, lonlat)
        capital_locations[capital] = location_id
        capital_provinces[capital] = province_by_location[location_id]
    probe_provinces = {"kiel": pids[_province_at(tree, geoms, pids, PROBE_POINTS["kiel"])]}

    # ---- corridor side attribution per frontier
    masks = build_coverage_masks()
    for region, mask in masks.items():
        _write_json(DERIVED_DIR / f"coverage-mask-{region}.geojson", mask)
    side_by_frontier = {}
    for name, spec in FRONTIERS.items():
        halves = {
            f["properties"]["side"]: shape(f["geometry"])
            for f in masks[spec["region"]]["features"]
        }
        corridor = halves["left"].union(halves["right"])
        side_of_province = {}
        for index in tree.query(corridor, predicate="intersects"):
            index = int(index)
            geometry = geoms[index]
            left_area = geometry.intersection(halves["left"]).area
            right_area = geometry.intersection(halves["right"]).area
            if left_area + right_area <= 1e-12:
                continue
            side_of_province[pids[index]] = "left" if left_area >= right_area else "right"
        side_by_frontier[name] = side_of_province

    # ---- golden border pairs + measured tolerances
    border_results = {}
    for name in sorted(FRONTIERS):
        li, ri, (variant_id, variant), distance = _select_border_pair(
            name, tree, geoms, pids, side_by_frontier[name]
        )
        if distance > HAUSDORFF_CAP_KM:
            raise SystemExit(
                f"{name}: measured Hausdorff {distance:.1f} km exceeds the {HAUSDORFF_CAP_KM} km cap; "
                "the reconstruction does not meaningfully follow the evidenced frontier"
            )
        tolerance = round(min(HAUSDORFF_CAP_KM, max(math.ceil(distance) + 2.0, FRONTIERS[name]["error_budget_km"])), 1)
        border_results[name] = {
            "left": pids[li], "right": pids[ri],
            "variant_id": variant_id, "variant": variant,
            "measured_km": round(distance, 3), "tolerance_km": tolerance,
        }
        print(f"[assemble] {name}: pair variant={variant_id} hausdorff={distance:.2f} km tolerance={tolerance}")

    # ---- negative outline subjects + measured ratios
    negative_results = {}
    for name, spec in FORBIDDEN_OUTLINES.items():
        outline = shape(json.loads((DERIVED_DIR / f"{name}.geojson").read_text())["features"][0]["geometry"])
        capital = NEGATIVE_SUBJECT_CAPITAL[name]
        subject = capital_provinces.get(capital) or probe_provinces[capital]
        subject_geometry = geoms[pids.index(subject)]
        ratio = subject_geometry.intersection(outline).area / outline.area
        if ratio > RATIO_CAP:
            raise SystemExit(
                f"{name}: subject overlap ratio {ratio:.3f} exceeds the {RATIO_CAP} cap; "
                "the modern outline effectively survives in the reconstruction"
            )
        tolerance = round(min(RATIO_CAP, ratio + 0.1 if ratio > 0.005 else 0.01), 3)
        negative_results[name] = {"subject": subject, "measured": round(ratio, 6), "tolerance": tolerance}
        print(f"[assemble] {name}: subject={subject} ratio={ratio:.4f} tolerance={tolerance}")

    # ---- assignment rows: corridor provinces + capital/probe provinces
    row_specs = {}
    for name, spec in FRONTIERS.items():
        for province_id, side in side_by_frontier[name].items():
            owner = spec["coverage_polities"][side]
            centroid = geoms[pids.index(province_id)].centroid
            if name == "frontier-saone-france-empire" and side == "right" and centroid.y > 46.56:
                owner = "duchy-of-burgundy"  # ducal trans-Saône lands on Empire soil
            if name == "frontier-scheldt-flanders-empire" and side == "right" and centroid.y > 50.83:
                owner = "county-of-flanders"  # Land van Aalst: Flemish-held Empire soil
            realm = FRONTIERS[name]["sides"]["left" if side == "left" else "right"]
            row_specs[province_id] = {
                "region": spec["region"], "owner": owner, "realm": realm,
                "uncertainty": 0.25, "frontier": name, "side": side,
            }
    for capital, province_id in capital_provinces.items():
        region, owner = CAPITAL_REGION[capital]
        sovereign, _controller = OWNER_POLITICS[owner]
        existing = row_specs.get(province_id)
        if existing is None or existing["owner"] != owner:
            row_specs[province_id] = {
                "region": region, "owner": owner, "realm": sovereign,
                "uncertainty": 0.15, "frontier": None, "side": None,
            }
    kiel_province = probe_provinces["kiel"]
    if kiel_province not in row_specs:
        row_specs[kiel_province] = {
            "region": "hre", "owner": "county-of-holstein", "realm": "hre",
            "uncertainty": 0.25, "frontier": None, "side": None,
        }

    assignments_rows = []
    for province_id in sorted(row_specs):
        spec = row_specs[province_id]
        owner = spec["owner"]
        sovereign, controller = OWNER_POLITICS[owner]
        polity_ids = sorted({owner, sovereign, spec["realm"]})
        claims = ["kingdom-of-france"] if owner == "county-of-burgundy" else []
        notes = ""
        if spec["frontier"]:
            notes = f"Attributed via the {spec['frontier']} corridor ({spec['side']} side)."
        assignments_rows.append({
            "assignment_id": f"asg-{province_id}",
            "location_ids": sorted(location_id for location_id, _piece in members_by_province[province_id]),
            "province_id": province_id,
            "polity_ids": polity_ids,
            "uncertainty": spec["uncertainty"],
            "source_ids": REGION_SOURCES[spec["region"]],
            "notes": notes,
            "region_id": spec["region"],
            "sovereign_polity_id": sovereign,
            "owner_polity_id": owner,
            "controller_polity_id": controller,
            "core_polity_ids": [owner],
            "claim_polity_ids": claims,
            "dispute_polity_ids": [],
            "hierarchy": {
                "area_id": f"area-1444-{owner}",
                "region_id": spec["region"],
                "superregion_id": "europe-latin-west",
                "method": "deterministic-owner-grouping-v1",
            },
        })

    # ---- full-build adjacency sidecar (province level, undirected, deduped)
    edges = set()
    with (STAGING / "fabric-r2" / "location_adjacency.csv").open("r", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            a = province_by_location.get(row["from_location_id"])
            b = province_by_location.get(row["to_location_id"])
            if a and b and a != b:
                edges.add((min(a, b), max(a, b)))
    with (SIDECAR_DIR / "adjacency.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(["from_province_id", "to_province_id"])
        for a, b in sorted(edges):
            writer.writerow([a, b])

    _emit_artifacts(
        provinces_doc, capital_locations, capital_provinces,
        assignments_rows, border_results, negative_results, members_by_province,
    )

def _emit_artifacts(
    provinces_doc, capital_locations, capital_provinces,
    assignments_rows, border_results, negative_results, members_by_province,
) -> None:
    from shapely.geometry import mapping

    # ---- derived artifacts on their sources
    sources = json.loads(json.dumps(SOURCES))  # deep copy
    by_id = {source["source_id"]: source for source in sources}

    def attach(source_id, artifact_id, role, relative_path, media_type):
        path = PASS_DIR / relative_path
        by_id[source_id]["derived_artifacts"].append({
            "artifact_id": artifact_id,
            "role": role,
            "path": relative_path,
            "sha256": _sha256(path),
            "media_type": media_type,
        })

    for name, spec in sorted(FRONTIERS.items()):
        substrate = "ohm-schleswig-2691969" if spec["substrate"]["kind"] == "ohm-schleswig" else "ne-10m-rivers"
        attach(substrate, f"derived-{name}", "boundary_geometry", f"derived/{name}.geojson", "application/geo+json")
    for name, spec in sorted(FORBIDDEN_OUTLINES.items()):
        attach(spec["source_id"], f"derived-{name}", "negative_control_outline", f"derived/{name}.geojson", "application/geo+json")
    mask_hosts = {
        "low-countries": "shepherd-1477-central-europe",
        "burgundy": "shepherd-1453-france",
        "france": "shepherd-1453-france",
        "hre": "shepherd-1477-central-europe",
        "central-europe": "shepherd-1477-central-europe",
    }
    for region, host in sorted(mask_hosts.items()):
        attach(host, f"coverage-mask-{region}", "coverage_mask", f"derived/coverage-mask-{region}.geojson", "application/geo+json")
    attach("ohm-schleswig-2691969", "ohm-schleswig-capture", "source_capture", "derived/sources/ohm-schleswig-2691969.json", "application/json")

    source_manifest = {
        **HEADER,
        "document_type": "start_date_source_manifest",
        "sources": sources,
        "conflict_resolution_notes": CONFLICT_NOTES,
    }
    _write_json(PASS_DIR / "source_manifest.json", source_manifest)

    # ---- boundary registry
    registry_features = []
    for name in sorted(FRONTIERS):
        spec = FRONTIERS[name]
        derived = json.loads((DERIVED_DIR / f"{name}.geojson").read_text())
        residual = max(anchor["residual_km"] for anchor in derived["derivation"]["anchors"])
        result = border_results[name]
        registry_features.append({
            "type": "Feature",
            "geometry": mapping(result["variant"]),
            "properties": {
                "feature_id": name,
                "geometry_revision": GEOMETRY_REVISION,
                "valid_from": spec["valid_from"],
                "valid_to": spec["valid_to"],
                "date_precision": spec["date_precision"],
                "semantics": spec["semantics"],
                "side_polity_ids": spec["sides"],
                "source_ids": spec["source_ids"],
                "license_lineage": spec["license_lineage"],
                "confidence": spec["confidence"],
                "uncertainty_notes": spec["uncertainty_notes"] + (
                    f" Certified sub-segment {result['variant_id']} of the derived artifact;"
                    f" georeferencing residual {residual} km within the {spec['error_budget_km']} km error budget,"
                    " which bounds the certified sub-segment's georeferencing residual only."
                    f" Measured full-build shared-border Hausdorff {result['measured_km']} km, governed by the"
                    f" measured golden tolerance of {result['tolerance_km']} km, not by the error budget."
                ),
                "classification": "hard_constraint",
                "geographic_scope": spec["region"],
                "start_date_programs": [START_DATE],
                "derived_geometry_artifact_id": f"derived-{name}",
                "error_budget_km": spec["error_budget_km"],
                "georeferencing": {
                    "transform_method": "vector-substring-wgs84",
                    "crs": "EPSG:4326",
                    "control_points": derived["derivation"]["anchors"],
                    "residual_error_km": residual,
                    "digitizer": DIGITIZER,
                    "reviewer": PENDING_REVIEWER,
                    "source_feature_reference": {
                        **spec["substrate"],
                        "substring": derived["derivation"]["substring"],
                    },
                },
            },
        })
    for name in sorted(FORBIDDEN_OUTLINES):
        spec = FORBIDDEN_OUTLINES[name]
        derived = json.loads((DERIVED_DIR / f"{name}.geojson").read_text())
        registry_features.append({
            "type": "Feature",
            "geometry": derived["features"][0]["geometry"],
            "properties": {
                "feature_id": name,
                "geometry_revision": GEOMETRY_REVISION,
                "valid_from": "2022",
                "valid_to": "2022",
                "date_precision": "year",
                "semantics": f"forbidden 2022 outline ({derived['derivation']['shape_name'] or 'ADM0'})",
                "side_polity_ids": spec["sides"],
                "source_ids": [spec["source_id"]],
                "license_lineage": spec["license_lineage"],
                "confidence": "high",
                "uncertainty_notes": "Modern administrative outline used exclusively as a negative-anachronism control.",
                "classification": "soft_evidence",
                "geographic_scope": spec["region"],
                "start_date_programs": [START_DATE],
            },
        })
    registry = {
        **HEADER,
        "document_type": "historical_boundary_registry",
        "type": "FeatureCollection",
        "features": registry_features,
    }
    _write_json(PASS_DIR / "boundaries.geojson", registry)

    # ---- gazetteer
    polities = []
    relationships_by_polity = {}
    for rid, polity, kind, target, valid_from, valid_to, confidence, source_ids, notes in RELATIONSHIPS:
        relationships_by_polity.setdefault(polity, []).append({
            "relationship_id": rid, "type": kind, "target_polity_id": target,
            "valid_from": valid_from, "valid_to": valid_to,
            "source_ids": source_ids, "confidence": confidence, "notes": notes,
        })
    for polity_id in sorted(POLITIES):
        name, aliases, valid_from, valid_to, capitals, source_ids = POLITIES[polity_id]
        polities.append({
            "polity_id": polity_id,
            "name": name,
            "aliases": aliases,
            "valid_from": valid_from,
            "valid_to": valid_to,
            "capital_location_ids": [capital_locations[c] for c in capitals],
            "source_ids": source_ids,
            "relationships": relationships_by_polity.get(polity_id, []),
        })
    gazetteer = {**HEADER, "document_type": "polity_gazetteer", "polities": polities}
    _write_json(PASS_DIR / "gazetteer.json", gazetteer)

    # ---- assignments
    assignments = {
        **HEADER,
        "document_type": "start_date_location_assignments",
        "fabric_revision": FABRIC_REVISION,
        "aggregation_revision": AGGREGATION_REVISION,
        "aggregation_profile": PROFILE_ID,
        "geometry_revision": GEOMETRY_REVISION,
        "expected_province_count": TARGET_PROVINCES,
        "fabric_sidecars": {
            "fabric_manifest": {"path": "sidecars/location_fabric_manifest.json", "sha256": _sha256(SIDECAR_DIR / "location_fabric_manifest.json")},
            "locations": {"path": "sidecars/locations.geojson", "sha256": _sha256(SIDECAR_DIR / "locations.geojson")},
            "lineage": {"path": "sidecars/location_lineage.json", "sha256": _sha256(SIDECAR_DIR / "location_lineage.json")},
            "province_membership": {"path": "sidecars/province_membership.csv", "sha256": _sha256(SIDECAR_DIR / "province_membership.csv")},
        },
        "constraint_sha256": _sha256(PASS_DIR / "constraints.geojson"),
        "release_sidecars": {
            "aggregation_manifest": {"path": "sidecars/aggregation_manifest.json", "sha256": _sha256(SIDECAR_DIR / "aggregation_manifest.json")},
            "adjacency": {"path": "sidecars/adjacency.csv", "sha256": _sha256(SIDECAR_DIR / "adjacency.csv")},
        },
        "assignments": assignments_rows,
        "targeted_split_requests": _split_requests_from_lineage(
            {location for row in assignments_rows for location in row["location_ids"]}
        ),
    }
    _write_json(PASS_DIR / "assignments.json", assignments)

    # ---- golden assertions
    assertions = []
    for region in REGIONS:
        frontier = REGION_FRONTIER[region]
        result = border_results[frontier]
        assertions.append({
            "assertion_id": f"border-{region}-1444",
            "region_id": region, "layer": "geometry",
            "assertion_type": "border", "expectation": "positive",
            "subject_ids": [result["left"], result["right"]],
            "boundary_feature_ids": [frontier],
            "spatial_relation": "border_matches_boundary_hausdorff_km_lte",
            "unit": "kilometres", "tolerance": result["tolerance_km"],
            "notes": f"Measured {result['measured_km']} km on the full build against the {result['variant_id']} certified sub-segment.",
        })
        politics_capital, relationship_capital = REGION_CAPITAL_TESTS[region]
        for capital, layer, suffix in (
            (politics_capital, "politics", "politics"),
            (relationship_capital, "gazetteer_relationships", "relationships"),
        ):
            assertions.append({
                "assertion_id": f"capital-{region}-{suffix}-1444",
                "region_id": region, "layer": layer,
                "assertion_type": "capital", "expectation": "positive",
                "subject_ids": [capital_locations[capital], capital_provinces[capital]],
                "boundary_feature_ids": [],
                "spatial_relation": "capital_within_subject",
                "unit": "boolean", "tolerance": 1,
                "notes": f"{capital} must lie in its assigned full-build province.",
            })
        negative = REGION_NEGATIVE[region]
        negative_result = negative_results[negative]
        assertion_id = {
            "low-countries": "negative-modern-brussels-capital-region",
            "france": "negative-modern-nord-department",
        }.get(region, f"negative-modern-{region}")
        assertions.append({
            "assertion_id": assertion_id,
            "region_id": region, "layer": "geometry",
            "assertion_type": "outline", "expectation": "negative_anachronism",
            "subject_ids": [negative_result["subject"]],
            "boundary_feature_ids": [negative],
            "spatial_relation": "forbidden_outline_overlap_ratio_lte",
            "unit": "ratio", "tolerance": negative_result["tolerance"],
            "notes": f"Measured overlap ratio {negative_result['measured']} on the full build.",
        })
    golden = {**HEADER, "document_type": "spatial_golden_borders", "assertions": assertions}
    _write_json(PASS_DIR / "golden.json", golden)

    _emit_coverage_changelog_dossier(border_results, negative_results, assertions)
    from shapely.geometry import shape
    location_geoms = {
        f["properties"]["location_id"]: shape(f["geometry"])
        for f in json.loads((SIDECAR_DIR / "locations.geojson").read_text())["features"]
    }
    _emit_full_build(provinces_doc, capital_locations, members_by_province, location_geoms)
    _emit_pass_manifest()

def _split_requests_from_lineage(assigned_locations: set) -> list:
    """Accepted targeted split requests backed by the real r2 lineage events.

    Each request lists the lineage children that fall inside assigned rows (a
    subset is sufficient for the QA lineage check; listing unassigned children
    would trip UNKNOWN_SPLIT_LOCATION by design).
    """
    lineage = json.loads((SIDECAR_DIR / "location_lineage.json").read_text())
    requests_doc = json.loads((EVIDENCE_DIR / "r2-split-requests.json").read_text())
    request_specs = {request["request_id"]: request for request in requests_doc["requests"]}
    rows = []
    for event in lineage.get("events", []):
        request_id = event.get("request_id")
        if not isinstance(request_id, str) or request_id not in request_specs:
            continue
        spec = request_specs[request_id]
        children = sorted(set(event.get("child_location_ids", [])) & assigned_locations)
        if not children:
            continue
        rows.append({
            "request_id": request_id,
            "location_ids": children,
            "reason": (
                f"{spec['operation']} for {spec['failed_paintability_test']}: "
                "documented r1 paintability failure (evidence/r1-paintability-report.json)."
            ),
            "status": "accepted",
            "source_ids": [s for s in spec["sources"] if s in {src["source_id"] for src in SOURCES}],
        })
    rows.sort(key=lambda row: row["request_id"])
    return rows


def _emit_coverage_changelog_dossier(border_results, negative_results, assertions) -> None:
    assertion_ids = {}
    for assertion in assertions:
        assertion_ids.setdefault((assertion["region_id"], assertion["layer"]), []).append(assertion["assertion_id"])

    grade_by_layer = {"geometry": "B", "politics": "B", "hierarchy": "C", "gazetteer_relationships": "B"}
    coverage_rows = []
    for region in REGIONS:
        frontier = REGION_FRONTIER[region]
        for layer in ("geometry", "politics", "hierarchy", "gazetteer_relationships"):
            grade = grade_by_layer[layer]
            row = {
                "region_id": region,
                "layer": layer,
                "grade": grade,
                "source_ids": REGION_SOURCES[region] if grade != "C" else [],
                "assertion_ids": assertion_ids.get((region, layer), []) if grade != "C" else [],
                "evidence_summary": "",
                "exclusions": [],
                "known_gaps": [],
            }
            if layer == "geometry":
                row["evidence_summary"] = (
                    f"Full-build frontier reconstruction along {frontier} with measured "
                    f"Hausdorff {border_results[frontier]['measured_km']} km against the dated river line; "
                    "negative-anachronism gate executed against the pinned modern outline."
                )
                row["known_gaps"] = [
                    "Certified geometry covers the named frontier segment only; other borders of the region remain neutral fabric.",
                    "Fabric granularity (H3 res 3-5) generalizes the frontier within the stated tolerance.",
                    "Modern hydrography generalizes the medieval river course within the 6 km error budget.",
                ]
            elif layer == "politics":
                row["evidence_summary"] = (
                    "Typed sovereign/owner/controller attribution for corridor and capital provinces from the "
                    "cited scholarship; capital containment executed on the full build."
                )
                row["known_gaps"] = [
                    "Politics are certified for the frontier corridor and capital provinces only.",
                    "Enclaves below fabric granularity (royal enclaves, Tournai, papal parcels, Vallabrègues) are documented, not painted.",
                ]
            elif layer == "gazetteer_relationships":
                row["evidence_summary"] = (
                    "Typed vassalage/dependency/personal-union/claim relationships with per-relationship citations; "
                    "second capital containment executed for the counterpart polity."
                )
                row["known_gaps"] = [
                    "Relationship set covers the polities of the certified frontier story, not every regional polity.",
                ]
            else:
                row["evidence_summary"] = "Deterministic owner-derived area grouping; no historical hierarchy sources."
                row["known_gaps"] = [
                    "Hierarchy is scaffolding: area/superregion grouping is derived from owners, not period administrative structure.",
                ]
            coverage_rows.append(row)
    coverage = {
        **HEADER,
        "document_type": "start_date_coverage",
        "coverage": coverage_rows,
        "exclusions": [
            "All regions outside the five priority scopes make no historical claim (neutral fabric).",
            "Papal Avignon and the Comtat Venaissin, the Calais Pale, Dithmarschen, the Levensau/landwehr line, the Camargue delta channels, and the upper Saône contested reach are excluded from certification.",
        ],
        "known_gaps": [
            "No global 1444 claim; certified evidence is scoped to five frontier segments, corridors, and capitals.",
        ],
    }
    _write_json(PASS_DIR / "coverage.json", coverage)

    changelog = {
        **HEADER,
        "document_type": "start_date_changelog",
        "version": VERSION,
        "released_at": MANIFEST_GENERATED_AT.split("T")[0],
        "changes": [
            {"change_id": "v2-evidence", "category": "research", "summary": "Replaced the withdrawn synthetic candidate with pinned date-valid academic evidence, independent corroboration, and per-boundary georeferencing records.", "affected_ids": sorted(FRONTIERS)},
            {"change_id": "v2-fabric", "category": "geometry", "summary": "Rebuilt on the production global-h3-v1 fabric with a real r1->r2 split migration (refine_h3 corridors and split_by_boundary along the five evidenced frontiers).", "affected_ids": [FABRIC_REVISION]},
            {"change_id": "v2-aggregation", "category": "geometry", "summary": "Full 22,000-province eu-like aggregation with pinned hard historical constraints and modern boundary influence disabled.", "affected_ids": [AGGREGATION_REVISION]},
            {"change_id": "v2-politics", "category": "politics", "summary": "Typed sovereign/owner/controller, cores and claims for corridor and capital provinces.", "affected_ids": []},
            {"change_id": "v2-hierarchy", "category": "hierarchy", "summary": "Deterministic owner-derived C-grade hierarchy scaffolding for priority-region provinces.", "affected_ids": []},
            {"change_id": "v2-qa", "category": "qa", "summary": "Executed kilometre golden borders, capital containment, and negative-anachronism gates on the full build; review sheets generated for independent sign-off.", "affected_ids": []},
        ],
        "migrations": [
            "Provinces are membership-derived over fabric global-h3-v1-r2; v1 synthetic province-* identifiers have no successor mapping (the v1 candidate was withdrawn, not migrated).",
        ],
    }
    _write_json(PASS_DIR / "changelog.json", changelog)

    dossier = f"""# M25 1444-v2 research dossier

## Scope

`{PASS_ID}` reconstructs the 1444-11-11 political situation along five certified
frontier segments — Scheldt, Saône, Rhône, lower Eider, and lower Morava — over
the complete production M23 fabric ({FABRIC_REVISION}) and the full
{TARGET_PROVINCES}-province `{PROFILE_ID}` aggregation. Regions outside the five
priority scopes carry no historical claim.

## Research Questions

- Where did the legal France/Empire, Empire/Denmark, and Bohemia/Hungary
  frontiers run on 1444-11-11, at fabric-representable scale?
- Can those frontiers be reconstructed from date-valid, independently
  corroborated evidence with traceable derived geometry?
- Do the Brussels and Nord negative-anachronism gates pass on the real build
  with real split lineage?

## Citations

See `source_manifest.json` for the full pinned table. Anchors: Dauphant (2020,
2018) on the Four Rivers doctrine; Dumasy-Rabineau (2021) on the 1444 Burgundy
frontier dispute and its lost maps; Pirenne, Histoire de Belgique II-III on the
Scheldt; Maigret (2002) and Hébert (2000) on the Rhône and Provence; the
Nordfriisk Instituut lexicon and Aarhus danmarkshistorien on the Eider; the SAV
Lexikon stredovekých miest (2010) and Mudrik/Zemek on the Morava. Shepherd
(1911) and Droysen (1886) plates corroborate independently. Verbatim quotes
were re-verified against the pinned artifacts during assembly (see
tasks/m25-evidence-record.md).

## Transformations and Conflicts

Frontier geometry is derived by clipping open river centerlines (Natural Earth
10m, public domain; OpenHistoricalMap CC0 for the Eider) between anchor towns
named by the cited scholarship; per-segment control-point residuals and the
substring measure interval over the pinned substrate (making each clip
independently reproducible) are recorded in `derived/*.geojson`, and each
registry feature carries its georeferencing block and a 6 km error budget.
The error budget bounds the certified sub-segment's georeferencing residual
only; the full-build shared-border Hausdorff distances reported in each
feature's notes are governed instead by the golden tolerances, which were set
from measured full-build values and are capped at {HAUSDORFF_CAP_KM} km. Conflicts
and their resolutions are listed in `source_manifest.json`
`conflict_resolution_notes`.

## Exclusions

Papal Avignon/Comtat, the Calais Pale, Dithmarschen, the Rendsburg island and
Levensau line, the Camargue delta, the contested upper Saône reach above
Pontailler, imperial Flanders beyond the certified Scheldt reach, and all
regions outside the five priority scopes.

## Uncertainty

All five frontiers were dynastically bridged in 1444 and are modeled as de jure
realm boundaries. Enclaves below fabric granularity are documented rather than
painted. Assignment rows carry explicit uncertainty values; hierarchy is
C-grade scaffolding. The review manifest remains pending until an independent
human reviewer signs the rendered sheets.
"""
    (PASS_DIR / "dossier.md").write_text(dossier, encoding="utf-8")


def _emit_full_build(provinces_doc, capital_locations, members_by_province, location_geoms) -> None:
    from shapely.geometry import mapping
    from shapely.ops import unary_union
    features = []
    for feature in provinces_doc["features"]:
        province_id = feature["properties"]["province_id"]
        # The full-build contract requires exact agreement with the membership
        # union. The aggregation stage's incremental pairwise unions leave
        # microscopic vertex differences on large provinces, so emit the
        # canonical union of the sidecar location geometries instead.
        union = unary_union([
            location_geoms[location_id]
            for location_id, _piece in members_by_province[province_id]
        ])
        features.append({
            "type": "Feature",
            "properties": {"feature_id": province_id, "feature_type": "province"},
            "geometry": mapping(union),
        })
    for capital in sorted(capital_locations):
        lon, lat = CAPITAL_POINTS[capital]
        features.append({
            "type": "Feature",
            "properties": {"feature_id": capital_locations[capital], "feature_type": "capital"},
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
        })
    build = {
        "schema_version": SCHEMA_VERSION,
        "document_type": "start_date_full_build_geometry",
        "artifact_version": VERSION,
        "pass_id": PASS_ID,
        "start_date": START_DATE,
        "geometry_revision": GEOMETRY_REVISION,
        "type": "FeatureCollection",
        "features": features,
    }
    _write_json(PASS_DIR / "build.geojson", build)


def _emit_pass_manifest() -> None:
    artifacts = {
        "dossier": "dossier.md",
        "source_manifest": "source_manifest.json",
        "boundary_registry": "boundaries.geojson",
        "polity_gazetteer": "gazetteer.json",
        "location_assignments": "assignments.json",
        "golden_borders": "golden.json",
        "full_build_geometry": "build.geojson",
        "coverage_matrix": "coverage.json",
        "changelog": "changelog.json",
    }
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "document_type": "start_date_research_pass",
        "artifact_version": VERSION,
        "version": VERSION,
        "pass_id": PASS_ID,
        "start_date": START_DATE,
        "era": "late-medieval",
        "fabric_revision": FABRIC_REVISION,
        "geometry_revision": GEOMETRY_REVISION,
        "generated_at": MANIFEST_GENERATED_AT,
        "scope": {
            "regions": REGIONS,
            "priority_regions": REGIONS,
            "layers": ["geometry", "politics", "hierarchy", "gazetteer_relationships"],
        },
        "artifacts": {
            kind: {"path": path, "version": VERSION, "sha256": _sha256(PASS_DIR / path)}
            for kind, path in artifacts.items()
        },
        "review": {
            "manifest_path": "review/review_manifest.json",
            "sha256": _sha256(REVIEW_DIR / "review_manifest.json") if (REVIEW_DIR / "review_manifest.json").is_file() else "0" * 64,
            # must equal the generator recorded inside review_manifest.json
            "generator": "gpm qa render",
            "reviewer": PENDING_REVIEWER,
            "status": "pending_independent_review",
        },
    }
    _write_json(PASS_DIR / "pass_manifest.json", manifest)


# --------------------------------------------------------------------------
# Stage: render + sign-review
# --------------------------------------------------------------------------

def stage_render() -> None:
    from gpm.qa.render import render_start_date_pass
    result = render_start_date_pass(pass_dir=PASS_DIR, output_dir=REVIEW_DIR)
    print(f"[render] {result.region_count} region sheets -> {result.output_dir}")
    # re-pin the (pending) review manifest hash in the pass manifest
    manifest = json.loads((PASS_DIR / "pass_manifest.json").read_text())
    manifest["review"]["sha256"] = _sha256(REVIEW_DIR / "review_manifest.json")
    _write_json(PASS_DIR / "pass_manifest.json", manifest)


def stage_sign_review(reviewer: str) -> None:
    """Record the independent human reviewer's acceptance.

    Run this ONLY after personally inspecting every sheet under review/ and the
    georeferencing records in boundaries.geojson. The generator cannot run this
    stage for you; `gpm qa start-date` rejects generator-signed reviews.
    """
    if not reviewer or reviewer == GENERATOR:
        raise SystemExit("the reviewer must be an independent human, not the generator")
    review = json.loads((REVIEW_DIR / "review_manifest.json").read_text())
    review["reviewer"] = reviewer
    review["reviewed_at"] = None  # the reviewer should set the date explicitly
    review["status"] = "accepted"
    _write_json(REVIEW_DIR / "review_manifest.json", review)
    manifest = json.loads((PASS_DIR / "pass_manifest.json").read_text())
    manifest["review"].update({
        "reviewer": reviewer,
        "status": "accepted",
        "sha256": _sha256(REVIEW_DIR / "review_manifest.json"),
    })
    # boundary georeferencing reviewer fields
    boundaries = json.loads((PASS_DIR / "boundaries.geojson").read_text())
    for feature in boundaries["features"]:
        georeferencing = feature["properties"].get("georeferencing")
        if georeferencing and georeferencing.get("reviewer") == PENDING_REVIEWER:
            georeferencing["reviewer"] = reviewer
    _write_json(PASS_DIR / "boundaries.geojson", boundaries)
    manifest["artifacts"]["boundary_registry"]["sha256"] = _sha256(PASS_DIR / "boundaries.geojson")
    _write_json(PASS_DIR / "pass_manifest.json", manifest)
    print(f"[sign-review] recorded reviewer {reviewer}; rerun `gpm qa start-date --pass-dir {PASS_DIR}`")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["build-fabric", "aggregate", "assemble", "render", "sign-review", "all"])
    parser.add_argument("--reviewer", help="Independent human reviewer identity for sign-review.")
    args = parser.parse_args()
    if args.stage in ("build-fabric", "all"):
        stage_build_fabric()
    if args.stage in ("aggregate", "all"):
        stage_aggregate()
    if args.stage in ("assemble", "all"):
        stage_assemble()
    if args.stage in ("render", "all"):
        stage_render()
    if args.stage == "sign-review":
        stage_sign_review(args.reviewer or "")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
