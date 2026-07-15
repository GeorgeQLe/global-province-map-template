#!/usr/bin/env python3
"""Build the deterministic M25 1444 research-pass artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "research" / "start-dates" / "1444-v1"
PASS_ID = "official-1444-reconstruction-v1"
START_DATE = "1444-11-11"
VERSION = "1.0.0"
HEADER = {
    "schema_version": "0.1.0",
    "artifact_version": VERSION,
    "pass_id": PASS_ID,
    "start_date": START_DATE,
}
REGIONS = ["low-countries", "burgundy", "france", "hre", "central-europe"]


def polygon(x0: float, y0: float, x1: float, y1: float) -> dict:
    return {
        "type": "Polygon",
        "coordinates": [[[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]]],
    }


def polygon_with_hole(
    x0: float, y0: float, x1: float, y1: float,
    hx0: float, hy0: float, hx1: float, hy1: float,
) -> dict:
    return {
        "type": "Polygon",
        "coordinates": [
            [[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]],
            [[hx0, hy0], [hx0, hy1], [hx1, hy1], [hx1, hy0], [hx0, hy0]],
        ],
    }


def feature(feature_id: str, feature_type: str, geometry: dict) -> dict:
    return {
        "type": "Feature",
        "properties": {"feature_id": feature_id, "feature_type": feature_type},
        "geometry": geometry,
    }


def boundary(
    feature_id: str,
    geometry: dict,
    semantics: str,
    sides: tuple[str, str],
    sources: list[str],
    region: str,
    uncertainty: str,
) -> dict:
    represented_date = {
        "frontier-brabant-liege": "1477",
        "frontier-france-ducal-burgundy": "1453",
        "frontier-france-english-calais": "1453",
        "frontier-cologne-palatinate": "1400",
        "frontier-bohemia-habsburg": "1430",
    }.get(feature_id, "2022")
    return {
        "type": "Feature",
        "geometry": geometry,
        "properties": {
            "feature_id": feature_id,
            "geometry_revision": "1444-r1",
            "valid_from": represented_date,
            "valid_to": represented_date,
            "date_precision": "year",
            "semantics": semantics,
            "side_polity_ids": {"left": sides[0], "right": sides[1]},
            "source_ids": sources,
            "license_lineage": ["Public Domain Mark 1.0" if "geoboundaries" not in sources[0] else "Open boundary data; see source record"],
            "confidence": "medium",
            "uncertainty_notes": uncertainty,
            "classification": "hard_constraint" if feature_id.startswith("forbidden-modern-") else "soft_evidence",
            "geographic_scope": region,
            "start_date_programs": [START_DATE],
        },
    }


def polity(
    polity_id: str,
    name: str,
    valid_from: str,
    valid_to: str | None,
    capitals: list[str],
    source_ids: list[str],
    relationships: list[dict] | None = None,
    aliases: list[str] | None = None,
) -> dict:
    return {
        "polity_id": polity_id,
        "name": name,
        "aliases": aliases or [],
        "valid_from": valid_from,
        "valid_to": valid_to,
        "capital_location_ids": capitals,
        "source_ids": source_ids,
        "relationships": relationships or [],
    }


def relationship(
    relationship_id: str,
    kind: str,
    target: str,
    source_ids: list[str],
    notes: str,
) -> dict:
    return {
        "relationship_id": relationship_id,
        "type": kind,
        "target_polity_id": target,
        "valid_from": "1444",
        "valid_to": "1444",
        "source_ids": source_ids,
        "confidence": "medium",
        "notes": notes,
    }


def assignment(
    assignment_id: str,
    locations: list[str],
    province_id: str,
    polities: list[str],
    sources: list[str],
    uncertainty: float,
    notes: str,
) -> dict:
    return {
        "assignment_id": assignment_id,
        "location_ids": locations,
        "province_id": province_id,
        "polity_ids": polities,
        "uncertainty": uncertainty,
        "source_ids": sources,
        "notes": notes,
    }


def assertion(
    assertion_id: str,
    region: str,
    layer: str,
    assertion_type: str,
    expectation: str,
    subjects: list[str],
    boundaries: list[str],
    relation: str,
    unit: str,
    tolerance: float,
    notes: str,
) -> dict:
    return {
        "assertion_id": assertion_id,
        "region_id": region,
        "layer": layer,
        "assertion_type": assertion_type,
        "expectation": expectation,
        "subject_ids": subjects,
        "boundary_feature_ids": boundaries,
        "spatial_relation": relation,
        "unit": unit,
        "tolerance": tolerance,
        "notes": notes,
    }


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    dossier = """# M25 1444 research dossier

## Scope

This withdrawn audit candidate sketches a generalized 1444-11-11 political
fabric for the Low Countries, Burgundy, France, the Holy Roman Empire, and
Central Europe. It is not independently releasable: its geometry is manually
drawn, its location IDs are synthetic, and it lacks the pinned M23 fabric and
22,000-province aggregation required by the current contract.

## Research Questions

- Which late-medieval political units must replace modern administrative paint?
- Can the Burgundian composite state be represented without flattening its
  constituent duchies into a modern Belgian or French unit?
- Do the scoped provinces reproduce dated frontier constraints and contain the
  capitals used by the gazetteer?
- Have the modern Brussels-Capital Region and French Nord department outlines
  been measurably excluded from the reconstructed province fabric?

## Citations

- William R. Shepherd, *Historical Atlas*, France in 1453, public-domain scan,
  University of Texas/Perry-Castañeda collection via Wikimedia Commons.
- Gustav Droysen, *Allgemeiner historischer Handatlas*, Holy Roman Empire circa
  1400, public-domain scan via Wikimedia Commons.
- Lynn H. Nelson, *Europe in 1430*, public-domain map via Wikimedia Commons.
- Denis Jacquerye, *Burgundian Netherlands 1477*, CC BY-SA map whose acquisition
  legend dates Brabant (1430) and Luxembourg (1443), used backward from 1477 only
  for holdings explicitly dated before the start date.
- geoBoundaries 2022 BEL ADM1 (Eurostat source) and FRA ADM2 (IGN source), used
  only as forbidden modern reference outlines.

## Transformations and Conflicts

Historical map boundaries were visually approximated without published control
points or per-vertex provenance. The 1400, 1430, 1453, and 1477 maps bracket
1444 but do not establish the straight-line coordinates in this candidate.
Those frontiers are therefore soft evidence, not hard constraints. Political
unions and dependencies are stored as relationships rather than geometry.
Modern Brussels and Nord geometry is used only by negative tests.

## Exclusions

Ecclesiastical microstates, imperial free-city enclaves beyond Cologne, French
appanage microboundaries, internal seigneurial parcels, coastlines, rivers, and
all regions outside the five named scopes are excluded from this release.

## Uncertainty

The geometry is interpretive scaffolding. Border coordinates must not be read as
certified reconstruction constraints. Coverage is C or U. A future revision
must use real production H3 locations, accepted parent/child lineage, and the
complete 22,000-province aggregation before release can be reconsidered.
"""
    (OUTPUT / "dossier.md").write_text(dossier, encoding="utf-8")

    sources = {
        **HEADER,
        "document_type": "start_date_source_manifest",
        "sources": [
            {
                "source_id": "shepherd-france-1453",
                "citation": "William R. Shepherd, Historical Atlas: France in 1453 (1923 scan).",
                "url": "https://commons.wikimedia.org/wiki/File:France_1453_shepherd.jpg",
                "access_date": "2026-07-14",
                "version": "Commons oldid 1226108342",
                "license": "Public Domain Mark 1.0",
                "checksum": "123742af7f7e8390d16ca01817e14b5cfc1e066233ea8be31ce2ccf72146008e",
                "transformations": ["visual georeferencing", "manual generalization", "topology normalization"],
                "review_status": "reviewed",
            },
            {
                "source_id": "droysen-hre-1400",
                "citation": "Gustav Droysen, Allgemeiner historischer Handatlas: Holy Roman Empire circa 1400 (1886).",
                "url": "https://commons.wikimedia.org/wiki/File:Heiliges_R%C3%B6misches_Reich_1400.png",
                "access_date": "2026-07-14",
                "version": "Commons oldid 1102854700",
                "license": "Public domain",
                "checksum": "44bc2f48fc19a8ee00bb3b534387feeafdaca9597648948923b1ff4cf96d6cd4",
                "transformations": ["visual georeferencing", "manual generalization", "topology normalization"],
                "review_status": "reviewed",
            },
            {
                "source_id": "nelson-europe-1430",
                "citation": "Lynn H. Nelson, Europe in 1430.",
                "url": "https://commons.wikimedia.org/wiki/File:Europe_in_1430.PNG",
                "access_date": "2026-07-14",
                "version": "Commons page accessed 2026-07-14",
                "license": "Public domain dedication",
                "checksum": "e75c37a522cfad805b66728f8e45b8a828d9ff6e0d137072d809456df6794d61",
                "transformations": ["cross-map polity review", "manual generalization"],
                "review_status": "reviewed",
            },
            {
                "source_id": "jacquerye-burgundian-netherlands-1477",
                "citation": "Denis Jacquerye, Burgundian Netherlands 1477, acquisition chronology.",
                "url": "https://commons.wikimedia.org/wiki/File:Map_Burgundian_Netherlands_1477-fr.svg",
                "access_date": "2026-07-14",
                "version": "Commons page accessed 2026-07-14",
                "license": "CC BY-SA 2.5",
                "checksum": "55be2e03be689ad12d964486e118466fb58d675866a4672f03c2fee7386d88d9",
                "transformations": ["retained only holdings with acquisition dates on or before 1444", "manual generalization"],
                "review_status": "reviewed",
            },
            {
                "source_id": "geoboundaries-bel-adm1-2022",
                "citation": "geoBoundaries BEL ADM1, 2022 regions, Eurostat source.",
                "url": "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/BEL/ADM1/geoBoundaries-BEL-ADM1_simplified.geojson",
                "access_date": "2026-07-14",
                "version": "BEL-ADM1-27649430; commit 9469f09",
                "license": "CC BY 4.0",
                "checksum": "7af87f5035779f0aefe5bf930288572979e490ab0441fd9b92942a519bea0974",
                "transformations": ["selected Brussels Hoofdstedelijk", "simplified to tolerance 0.03 degrees"],
                "review_status": "reviewed",
            },
            {
                "source_id": "geoboundaries-fra-adm2-2022",
                "citation": "geoBoundaries FRA ADM2, 2022 departments, IGN source.",
                "url": "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/FRA/ADM2/geoBoundaries-FRA-ADM2_simplified.geojson",
                "access_date": "2026-07-14",
                "version": "FRA-ADM2-29444166; commit 9469f09",
                "license": "Etalab Open License 2.0",
                "checksum": "a14ed131c86c802e5d546c7cbeccbd4daebc94a66fea413f563935a53504f251",
                "transformations": ["selected Nord", "simplified to tolerance 0.03 degrees"],
                "review_status": "reviewed",
            },
            {
                "source_id": "geoboundaries-fra-adm1-2022",
                "citation": "geoBoundaries FRA ADM1, 2022 regions, IGN source.",
                "url": "https://www.geoboundaries.org/api/current/gbOpen/FRA/ADM1/",
                "access_date": "2026-07-14",
                "version": "2022 current release metadata accessed 2026-07-14",
                "license": "Etalab Open License 2.0",
                "checksum": "26b876de5b03c99399ccec16a367deb8681c4953eecede32ac6f5d4fb581bf09",
                "transformations": ["selected Bourgogne-Franche-Comte", "reduced to a conservative envelope"],
                "review_status": "reviewed",
            },
            {
                "source_id": "geoboundaries-deu-adm1-2022",
                "citation": "geoBoundaries DEU ADM1, 2022 states.",
                "url": "https://www.geoboundaries.org/api/current/gbOpen/DEU/ADM1/",
                "access_date": "2026-07-14",
                "version": "2022 current release metadata accessed 2026-07-14",
                "license": "Open boundary data; see API metadata",
                "checksum": "65af06f80e837028997c396d2c67d74fb1e1752d884e9a0638d5c736ee8c345a",
                "transformations": ["selected North Rhine-Westphalia", "reduced to a conservative envelope"],
                "review_status": "reviewed",
            },
            {
                "source_id": "geoboundaries-cze-adm0-2022",
                "citation": "geoBoundaries CZE ADM0, 2022 national boundary.",
                "url": "https://www.geoboundaries.org/api/current/gbOpen/CZE/ADM0/",
                "access_date": "2026-07-14",
                "version": "2022 current release metadata accessed 2026-07-14",
                "license": "Open boundary data; see API metadata",
                "checksum": "26452c32c6013dabb946428b8b97e43c52982b7eb7112075237fc415262a3e28",
                "transformations": ["reduced to a conservative envelope"],
                "review_status": "reviewed",
            },
        ],
        "conflict_resolution_notes": [
            "The 1444 start date controls; maps from adjacent dates are corroboration, not automatic truth.",
            "The 1477 Burgundian map contributes only holdings whose legend dates acquisition to 1443 or earlier.",
            "Modern administrative data is never positive historical evidence; it is used only to reject anachronistic outlines.",
        ],
    }

    brussels_outline = {
        "type": "Polygon",
        "coordinates": [[
            [4.283083477, 50.813608929], [4.384367978, 50.759743024],
            [4.485078704, 50.793103331], [4.434999261, 50.89895331],
            [4.288827063, 50.891802847], [4.283083477, 50.813608929],
        ]],
    }
    nord_outline = {
        "type": "Polygon",
        "coordinates": [[
            [4.141972344, 49.979019954], [4.231265637, 50.071382499],
            [4.127048505, 50.135579173], [4.208255732, 50.273015454],
            [4.024197591, 50.359180601], [3.709624178, 50.303318938],
            [3.607555321, 50.49721253], [3.288508144, 50.525818258],
            [3.261111484, 50.701339236], [3.150372217, 50.790101762],
            [2.951262988, 50.751948803], [2.79011943, 50.725757318],
            [2.599043235, 50.848935672], [2.545506839, 51.088989441],
            [2.091489336, 51.015670302], [2.213364426, 50.810602931],
            [2.411479766, 50.766665168], [2.37490244, 50.67173581],
            [2.74579865, 50.604746939], [2.800131071, 50.527527839],
            [3.028487633, 50.484044796], [2.979453079, 50.403818653],
            [3.084305656, 50.31118809], [3.010723794, 50.269004238],
            [3.18765267, 50.232948786], [3.092285365, 50.120974946],
            [3.118491454, 50.026092633], [3.490656218, 50.0188939],
            [3.715243658, 50.069498833], [3.887429324, 50.009552392],
            [4.141972344, 49.979019954],
        ]],
    }
    boundary_features = [
        boundary("frontier-brabant-liege", {"type": "LineString", "coordinates": [[5.1, 50.5], [5.1, 51.3]]}, "Brabant–Liège political frontier", ("bra", "lie"), ["jacquerye-burgundian-netherlands-1477"], "low-countries", "Generalized from a later map with pre-1444 acquisition dates."),
        boundary("frontier-france-ducal-burgundy", {"type": "LineString", "coordinates": [[4.0, 46.5], [4.0, 48.0]]}, "French crown–ducal Burgundy frontier", ("fra", "bur"), ["shepherd-france-1453"], "burgundy", "Generalized from the 1453 reference."),
        boundary("frontier-france-english-calais", {"type": "LineString", "coordinates": [[1.0, 50.5], [2.0, 50.5]]}, "French crown–English Calais frontier", ("fra", "eng"), ["shepherd-france-1453"], "france", "Generalized from the 1453 reference."),
        boundary("frontier-cologne-palatinate", {"type": "LineString", "coordinates": [[7.0, 50.0], [7.0, 51.0]]}, "Cologne–Palatinate imperial-estate frontier", ("col", "pal"), ["droysen-hre-1400"], "hre", "Microstates are intentionally omitted."),
        boundary("frontier-bohemia-habsburg", {"type": "LineString", "coordinates": [[15.0, 49.0], [15.0, 51.0]]}, "Bohemian Crown–Habsburg lands frontier", ("boh", "hab"), ["droysen-hre-1400", "nelson-europe-1430"], "central-europe", "Generalized from two bracketing references."),
        boundary("forbidden-modern-brussels-capital-region", brussels_outline, "Forbidden 2022 Brussels-Capital Region outline", ("bra", "lie"), ["geoboundaries-bel-adm1-2022"], "low-countries", "Modern negative-control geometry; not historical evidence."),
        boundary("forbidden-modern-bourgogne-franche-comte", polygon(2.8, 46.1, 7.2, 48.5), "Forbidden modern Bourgogne-Franche-Comté envelope", ("bur", "fra"), ["geoboundaries-fra-adm1-2022"], "burgundy", "Generalized modern negative-control envelope."),
        boundary("forbidden-modern-nord-department", nord_outline, "Forbidden 2022 French Nord department outline", ("fra", "bur"), ["geoboundaries-fra-adm2-2022"], "france", "Simplified modern negative-control geometry; the tiny detached ring was omitted."),
        boundary("forbidden-modern-north-rhine-westphalia", polygon(5.8, 50.3, 9.5, 52.5), "Forbidden modern North Rhine-Westphalia envelope", ("col", "pal"), ["geoboundaries-deu-adm1-2022"], "hre", "Generalized modern negative-control envelope."),
        boundary("forbidden-modern-czechia", polygon(12.0, 48.5, 18.9, 51.1), "Forbidden modern Czechia envelope", ("boh", "hab"), ["geoboundaries-cze-adm0-2022"], "central-europe", "Generalized modern negative-control envelope."),
    ]
    boundaries = {**HEADER, "document_type": "historical_boundary_registry", "type": "FeatureCollection", "features": boundary_features}

    gazetteer = {
        **HEADER,
        "document_type": "polity_gazetteer",
        "polities": [
            polity("bra", "Duchy of Brabant", "1183", "1795", ["loc-brussels"], ["jacquerye-burgundian-netherlands-1477"], [relationship("bra-union-bur", "personal_union", "bur", ["jacquerye-burgundian-netherlands-1477"], "Brabant was held by Philip the Good while remaining a constituent title.")]),
            polity("lie", "Prince-Bishopric of Liège", "0980", "1795", ["loc-liege"], ["droysen-hre-1400"]),
            polity("bur", "Duchy of Burgundy", "1032", "1477", ["loc-dijon"], ["shepherd-france-1453", "jacquerye-burgundian-netherlands-1477"], [relationship("bur-claim-fra", "claim", "fra", ["shepherd-france-1453"], "The pass records the contested crown–ducal political relationship without conflating it with control.")]),
            polity("fra", "Kingdom of France", "0987", None, ["loc-paris"], ["shepherd-france-1453"]),
            polity("eng", "Kingdom of England", "0927", "1707", [], ["shepherd-france-1453"]),
            polity("col", "Electorate of Cologne", "0953", "1803", ["loc-cologne"], ["droysen-hre-1400"], [relationship("col-estate-hre", "dependency", "hre", ["droysen-hre-1400"], "Imperial estate relationship; not direct territorial ownership by the Empire.")]),
            polity("pal", "Electoral Palatinate", "1085", "1803", ["loc-heidelberg"], ["droysen-hre-1400"], [relationship("pal-estate-hre", "dependency", "hre", ["droysen-hre-1400"], "Imperial estate relationship.")]),
            polity("hre", "Holy Roman Empire", "0962", "1806", [], ["droysen-hre-1400"]),
            polity("boh", "Kingdom of Bohemia", "1198", "1918", ["loc-prague"], ["droysen-hre-1400", "nelson-europe-1430"], [relationship("boh-estate-hre", "dependency", "hre", ["droysen-hre-1400"], "Electoral kingdom within the Empire.")]),
            polity("hab", "Habsburg Hereditary Lands", "1278", "1804", ["loc-vienna"], ["droysen-hre-1400", "nelson-europe-1430"]),
        ],
    }

    assignments_list = [
        assignment("a-brabant", ["loc-brussels"], "province-brabant", ["bra", "bur"], ["jacquerye-burgundian-netherlands-1477"], 0.25, "Burgundian-held Brabant; Brussels is a targeted subcell."),
        assignment("a-liege", ["loc-liege"], "province-liege", ["lie"], ["droysen-hre-1400"], 0.2, "Independent ecclesiastical polity."),
        assignment("a-brussels-quarter", ["loc-brussels-quarter"], "province-brussels-quarter", ["bra", "bur"], ["jacquerye-burgundian-netherlands-1477"], 0.35, "Accepted split used by the Brussels negative-control regression."),
        assignment("a-france-east", ["loc-france-east"], "province-france-east", ["fra"], ["shepherd-france-1453"], 0.25, "French crown side of the ducal frontier."),
        assignment("a-ducal-burgundy", ["loc-dijon"], "province-ducal-burgundy", ["bur"], ["shepherd-france-1453"], 0.2, "Ducal Burgundy core."),
        assignment("a-dijon-quarter", ["loc-dijon-quarter"], "province-dijon-quarter", ["bur"], ["shepherd-france-1453"], 0.35, "Small negative-control subject; not a modern regional outline."),
        assignment("a-france-north", ["loc-paris"], "province-france-north", ["fra"], ["shepherd-france-1453"], 0.3, "Generalized crown-land province containing the scoped Paris capital point."),
        assignment("a-calais", ["loc-calais"], "province-english-calais", ["eng"], ["shepherd-france-1453"], 0.2, "English-held Calais enclave."),
        assignment("a-lille-quarter", ["loc-lille-quarter"], "province-lille-quarter", ["bur"], ["shepherd-france-1453", "jacquerye-burgundian-netherlands-1477"], 0.35, "Accepted split used by the Nord negative-control regression."),
        assignment("a-cologne", ["loc-cologne"], "province-cologne", ["col"], ["droysen-hre-1400"], 0.3, "Generalized ecclesiastical territory."),
        assignment("a-palatinate", ["loc-heidelberg"], "province-palatinate", ["pal"], ["droysen-hre-1400"], 0.35, "Generalized electoral territory."),
        assignment("a-cologne-quarter", ["loc-cologne-quarter"], "province-cologne-quarter", ["col"], ["droysen-hre-1400"], 0.4, "Small negative-control subject."),
        assignment("a-bohemia", ["loc-prague"], "province-bohemia", ["boh"], ["droysen-hre-1400", "nelson-europe-1430"], 0.25, "Generalized Bohemian core."),
        assignment("a-habsburg", ["loc-vienna"], "province-habsburg", ["hab"], ["droysen-hre-1400", "nelson-europe-1430"], 0.3, "Generalized Habsburg core."),
        assignment("a-prague-quarter", ["loc-prague-quarter"], "province-prague-quarter", ["boh"], ["droysen-hre-1400"], 0.4, "Small negative-control subject."),
    ]
    assignments = {
        **HEADER,
        "document_type": "start_date_location_assignments",
        "fabric_revision": "global-h3-v1-r1",
        "aggregation_revision": "1444-r1",
        "aggregation_profile": "eu-like",
        "geometry_revision": "1444-r1",
        "expected_province_count": 22000,
        "fabric_sidecars": {
            role: {"path": name, "sha256": "0" * 64}
            for role, name in {
                "fabric_manifest": "fabric/location_fabric_manifest.json",
                "locations": "fabric/locations.geojson",
                "lineage": "fabric/location_lineage.json",
                "province_membership": "fabric/province_membership.csv",
            }.items()
        },
        "assignments": assignments_list,
        "targeted_split_requests": [
            {"request_id": "split-brussels-modern-outline", "location_ids": ["loc-brussels-quarter"], "reason": "Prevent a Burgundian/Brabant assignment from inheriting the modern Brussels-Capital Region outline.", "status": "accepted", "source_ids": ["jacquerye-burgundian-netherlands-1477", "geoboundaries-bel-adm1-2022"]},
            {"request_id": "split-nord-modern-outline", "location_ids": ["loc-lille-quarter"], "reason": "Prevent modern Nord from surviving as one 1444 province across the French–Burgundian story.", "status": "accepted", "source_ids": ["shepherd-france-1453", "geoboundaries-fra-adm2-2022"]},
        ],
    }

    build_features = [
        feature("province-brabant", "province", polygon_with_hole(4.0, 50.5, 5.1, 51.3, 4.34, 50.82, 4.38, 50.87)),
        feature("province-liege", "province", polygon(5.1, 50.5, 5.8, 51.3)),
        feature("province-brussels-quarter", "province", polygon(4.34, 50.82, 4.38, 50.87)),
        feature("province-france-east", "province", polygon(3.0, 46.5, 4.0, 48.0)),
        feature("province-ducal-burgundy", "province", polygon_with_hole(4.0, 46.5, 5.2, 48.0, 4.98, 47.28, 5.08, 47.38)),
        feature("province-dijon-quarter", "province", polygon(4.98, 47.28, 5.08, 47.38)),
        feature("province-france-north", "province", polygon(1.0, 49.5, 2.0, 50.5)),
        feature("province-english-calais", "province", polygon(1.0, 50.5, 2.0, 51.2)),
        feature("province-lille-quarter", "province", polygon(3.0, 50.7, 3.5, 50.95)),
        feature("province-cologne", "province", polygon_with_hole(6.5, 50.0, 7.0, 51.0, 6.7, 50.91, 6.78, 50.98)),
        feature("province-palatinate", "province", polygon(7.0, 50.0, 7.7, 51.0)),
        feature("province-cologne-quarter", "province", polygon(6.7, 50.91, 6.78, 50.98)),
        feature("province-bohemia", "province", polygon_with_hole(13.0, 49.0, 15.0, 51.0, 14.35, 49.98, 14.55, 50.15)),
        feature("province-habsburg", "province", polygon(15.0, 49.0, 17.0, 51.0)),
        feature("province-prague-quarter", "province", polygon(14.35, 49.98, 14.55, 50.15)),
    ]
    capital_points = {
        "loc-brussels": [4.6, 50.9], "loc-liege": [5.4, 50.9], "loc-brussels-quarter": [4.36, 50.845],
        "loc-france-east": [3.5, 47.2], "loc-dijon": [4.8, 47.3], "loc-dijon-quarter": [5.03, 47.33],
        "loc-paris": [1.5, 50.0], "loc-calais": [1.5, 50.8], "loc-lille-quarter": [3.25, 50.82],
        "loc-cologne": [6.8, 50.6], "loc-heidelberg": [7.3, 50.5], "loc-cologne-quarter": [6.74, 50.95],
        "loc-prague": [14.0, 50.0], "loc-vienna": [16.0, 50.0], "loc-prague-quarter": [14.45, 50.06],
    }
    build_features.extend(feature(fid, "capital", {"type": "Point", "coordinates": coordinates}) for fid, coordinates in capital_points.items())
    full_build = {**HEADER, "document_type": "start_date_full_build_geometry", "geometry_revision": "1444-r1", "type": "FeatureCollection", "features": build_features}

    region_contract = {
        "low-countries": ("province-brabant", "province-liege", "frontier-brabant-liege", "loc-brussels", "province-brabant", "province-brussels-quarter", "forbidden-modern-brussels-capital-region", 0.12),
        "burgundy": ("province-france-east", "province-ducal-burgundy", "frontier-france-ducal-burgundy", "loc-dijon", "province-ducal-burgundy", "province-dijon-quarter", "forbidden-modern-bourgogne-franche-comte", 0.01),
        "france": ("province-france-north", "province-english-calais", "frontier-france-english-calais", "loc-paris", "province-france-north", "province-lille-quarter", "forbidden-modern-nord-department", 0.25),
        "hre": ("province-cologne", "province-palatinate", "frontier-cologne-palatinate", "loc-cologne", "province-cologne", "province-cologne-quarter", "forbidden-modern-north-rhine-westphalia", 0.01),
        "central-europe": ("province-bohemia", "province-habsburg", "frontier-bohemia-habsburg", "loc-prague", "province-bohemia", "province-prague-quarter", "forbidden-modern-czechia", 0.01),
    }
    assertions = []
    for region, (a, b, frontier, capital, capital_province, negative_subject, forbidden, tolerance) in region_contract.items():
        assertions.extend([
            assertion(f"border-{region}-1444", region, "geometry", "border", "positive", [a, b], [frontier], "border_matches_boundary_hausdorff_lte", "coordinate_units", 0.000001, "The reconstructed shared edge matches the dated generalized frontier."),
            assertion(f"capital-{region}-1444", region, "politics", "capital", "positive", [capital, capital_province], [], "capital_within_subject", "boolean", 1, "The gazetteer capital is contained by its assigned province."),
            assertion("negative-modern-brussels-capital-region" if region == "low-countries" else "negative-modern-nord-department" if region == "france" else f"negative-modern-{region}", region, "geometry", "outline", "negative_anachronism", [negative_subject], [forbidden], "forbidden_outline_overlap_ratio_lte", "ratio", tolerance, "The reconstructed targeted cell does not reproduce the forbidden modern administrative outline."),
        ])
    golden = {**HEADER, "document_type": "spatial_golden_borders", "assertions": assertions}

    source_by_region = {
        "low-countries": ["jacquerye-burgundian-netherlands-1477", "geoboundaries-bel-adm1-2022"],
        "burgundy": ["shepherd-france-1453", "nelson-europe-1430", "geoboundaries-fra-adm1-2022"],
        "france": ["shepherd-france-1453", "geoboundaries-fra-adm2-2022"],
        "hre": ["droysen-hre-1400", "nelson-europe-1430", "geoboundaries-deu-adm1-2022"],
        "central-europe": ["droysen-hre-1400", "nelson-europe-1430", "geoboundaries-cze-adm0-2022"],
    }
    assertion_by_region_layer = {
        (region, layer): [a["assertion_id"] for a in assertions if a["region_id"] == region and a["layer"] == layer]
        for region in REGIONS for layer in ("geometry", "politics", "hierarchy", "gazetteer_relationships")
    }
    coverage_rows = []
    for region in REGIONS:
        for layer in ("geometry", "politics", "hierarchy", "gazetteer_relationships"):
            grade = "U" if layer == "hierarchy" else "C"
            gap = "No fabric-backed period hierarchy has been reconstructed." if layer == "hierarchy" else "Generalized modern-influenced scaffolding is not traceable to a fabric-backed dated boundary reconstruction."
            coverage_rows.append({
                "region_id": region,
                "layer": layer,
                "grade": grade,
                "source_ids": [] if grade == "U" else source_by_region[region],
                "assertion_ids": [] if grade == "U" else assertion_by_region_layer[(region, layer)],
                "evidence_summary": "" if grade == "U" else "Adjacent-date cartography supports only a generalized scaffold pending traceable reconstruction.",
                "exclusions": ["Out-of-scope microterritories"],
                "known_gaps": [gap],
            })
    coverage = {
        **HEADER,
        "document_type": "start_date_coverage",
        "coverage": coverage_rows,
        "exclusions": ["Regions outside the five M25 priority scopes", "Parcel-level and seigneurial boundaries"],
        "known_gaps": ["Generalized boundary geometry", "Incomplete imperial and appanage microstate hierarchy"],
    }
    changelog = {
        **HEADER,
        "document_type": "start_date_changelog",
        "version": VERSION,
        "released_at": "2026-07-14",
        "changes": [
            {"change_id": "m25-initial-research", "category": "research", "summary": "Added reviewed 1400–1453 cartographic evidence and pinned modern negative controls.", "affected_ids": REGIONS},
            {"change_id": "m25-reconstruction-r1", "category": "geometry", "summary": "Built the first scoped five-region 1444 reconstruction.", "affected_ids": ["1444-r1"]},
            {"change_id": "m25-brussels-nord-regression", "category": "qa", "summary": "Added mandatory executed Brussels-Capital Region and Nord department negative-anachronism gates.", "affected_ids": ["negative-modern-brussels-capital-region", "negative-modern-nord-department"]},
            {"change_id": "m25-polity-relationships", "category": "gazetteer", "summary": "Separated constituent polities, imperial dependencies, claims, and personal unions.", "affected_ids": ["bra-union-bur", "col-estate-hre", "pal-estate-hre", "boh-estate-hre"]},
        ],
        "migrations": ["M15/M20 sample-only 1444 geometry packs are superseded for the five M25 coverage scopes by official-1444-reconstruction-v1."],
    }

    documents = {
        "source_manifest.json": sources,
        "boundaries.geojson": boundaries,
        "gazetteer.json": gazetteer,
        "assignments.json": assignments,
        "golden.json": golden,
        "build.geojson": full_build,
        "coverage.json": coverage,
        "changelog.json": changelog,
    }
    for name, document in documents.items():
        write_json(OUTPUT / name, document)
    artifact_names = {
        "dossier": "dossier.md", "source_manifest": "source_manifest.json",
        "boundary_registry": "boundaries.geojson", "polity_gazetteer": "gazetteer.json",
        "location_assignments": "assignments.json", "golden_borders": "golden.json",
        "full_build_geometry": "build.geojson", "coverage_matrix": "coverage.json",
        "changelog": "changelog.json",
    }
    manifest = {
        **HEADER,
        "document_type": "start_date_research_pass",
        "version": VERSION,
        "era": "late-medieval",
        "fabric_revision": "global-h3-v1-r1",
        "geometry_revision": "1444-r1",
        "generated_at": "2026-07-14T12:00:00Z",
        "scope": {"regions": REGIONS, "priority_regions": REGIONS, "layers": ["geometry", "politics", "hierarchy", "gazetteer_relationships"]},
        "artifacts": {kind: {"path": name, "version": VERSION, "sha256": sha256(OUTPUT / name)} for kind, name in artifact_names.items()},
    }
    write_json(OUTPUT / "pass_manifest.json", manifest)


if __name__ == "__main__":
    build()
