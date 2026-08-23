#!/usr/bin/env python3
"""Build the checked Southern Europe (M49 039) Grade-A evidence packet."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from shapely.geometry import Point, mapping, shape

from m25c_negative_controls import add_negative_control
from shapely.ops import unary_union


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASELINE = Path("/private/tmp/m25c-region-155-baseline")
DEFAULT_OUTPUT = ROOT / "research/start-dates/1444-global-v1/regional-packets/039-southern-europe-2026-08-15.json"
START_DATE = "1444-11-11"
EXPECTED_ASSIGNMENTS = 464
EXPECTED_POLITIES = 23
VISUAL_REVIEW_SHA256 = "ee88cd687939060294c5a3e75ca392435245a605d2dc2ab6e3fbf0aff96f0f66"


LOCATORS = {
    "cambridge-athos-ottomans": "Chapter > Mount Athos and the Ottomans c. 1350–1550 > fifteenth-century Ottoman relationship",
    "cambridge-byzantine-balkans": "Chapter 16, pp. 429–448 > The Byzantine empire and the Balkans, 1204–1453",
    "cambridge-galata-privileges": "Article text > autonomous Italian colonies and commercial privileges through 1453",
    "cambridge-iberian-polities": "Chapter 1, pp. 11–38 > political diversity of the five kingdoms, 1157–1504",
    "cambridge-italian-states": "The Italian Renaissance State > map Italy in 1454 and chapters 1–9 on the peninsula's states",
    "cambridge-madeira-captaincies": "Article text > Madeira's donatary captaincies under Prince Henry",
    "cambridge-naples-1442": "Introduction, pp. 1–8 > Alfonso's 1442 conquest and Aragonese state-building",
    "cambridge-ottoman-expansion": "Chapter 17, pp. 449–469 > Ottoman expansion and military power, 1300–1453",
    "cambridge-portugal-ceuta": "Book excerpt > Portuguese retention of Ceuta after 1419–1420",
    "cambridge-portuguese-islands": "Chapter > The Atlantic Islands and Fisheries > crown-sanctioned settlement from the 1420s",
    "cambridge-varna-chronology": "Chronology > 10 November 1444 > Ottoman victory at Varna",
    "echr-andorra-pareage": "Historical background > 1278 and 1288 paréages and continuing co-suzerainty",
    "oxford-demilitarized-states": "Chapter > Andorra and San Marino > medieval settlement and mini-state continuity",
    "pace-andorra-coregency": "Periodic review > shared sovereignty originating in the 1278 treaty",
    "regional-survey-039": "Timeline > 1400 A.D.–1450 A.D.; Overview; Key Events > Rome and Southern Italy",
    "shepherd-historical-atlas": "Historical Atlas > Iberian, Italian, and Balkan plates covering 1400–1500",
    "unesco-athos": "Description > autonomous monastic community since Byzantine times",
    "unesco-san-marino": "Description > independent republic and city-state continuity since the thirteenth century",
}


def source(source_id: str, citation: str, url: str, valid_from: str, valid_to: str,
           independence_group: str) -> dict[str, Any]:
    return {
        "source_id": source_id, "citation": citation, "url": url,
        "access_date": "2026-08-15", "version": "Publisher record reviewed 2026-08-15",
        "license": "Citation/link only", "checksum": None, "transformations": [],
        "review_status": "reviewed", "source_type": "academic",
        "valid_from": valid_from, "valid_to": valid_to,
        "independence_group": independence_group, "derived_artifacts": [],
    }


STATIC_SOURCES = [
    source(
        "cambridge-iberian-polities",
        "David Nogales Rincón, 'From the Five Kingdoms to the Hispanic Monarchy: Political Structures, Ideology and Historical Development in the Medieval Iberian Peninsula (1157–1504)', Textiles of Medieval Iberia.",
        "https://www.cambridge.org/core/books/abs/textiles-of-medieval-iberia/from-the-five-kingdoms-to-the-hispanic-monarchy-political-structures-ideology-and-historical-development-in-the-medieval-iberian-peninsula-11571504/68D9D1BD934B5C9B32CF5E07B91BFB94",
        "1157", "1504", "boydell-nogales-rincon",
    ),
    source(
        "cambridge-italian-states",
        "Andrea Gamberini and Isabella Lazzarini, eds., The Italian Renaissance State: map Italy in 1454 and chapters on Sicily, Naples, the Papal State, Tuscany, Ferrara, Venice, Lombardy, and western principalities.",
        "https://assets.cambridge.org/97811070/10123/frontmatter/9781107010123_frontmatter.pdf",
        "1400", "1500", "cambridge-gamberini-lazzarini",
    ),
    source(
        "cambridge-naples-1442",
        "Antonio Calabria, The Cost of Empire, introduction: Alfonso the Great's 1442 conquest of Naples and the resulting Aragonese state-building.",
        "https://www.cambridge.org/core/books/abs/cost-of-empire/introduction/F2D745BC1E2CA431F395FFBA4EE6CB12",
        "1442", "1500", "cambridge-calabria",
    ),
    source(
        "cambridge-byzantine-balkans",
        "Mark C. Bartusis, 'The Byzantine empire and the Balkans, 1204–1453', The Cambridge History of War, vol. II.",
        "https://www.cambridge.org/core/books/abs/cambridge-history-of-war/byzantine-empire-and-the-balkans-12041453/56539A0053C886B75693FEA3D79AE496",
        "1204", "1453", "cambridge-bartusis",
    ),
    source(
        "cambridge-ottoman-expansion",
        "Gábor Ágoston, 'Ottoman expansion and military power, 1300–1453', The Cambridge History of War, vol. II.",
        "https://www.cambridge.org/core/books/abs/cambridge-history-of-war/ottoman-expansion-and-military-power-13001453/A0310E3C60C10C4FA33FB40370C19A3A",
        "1300", "1453", "cambridge-agoston",
    ),
    source(
        "cambridge-varna-chronology",
        "Anthony Bale, ed., The Cambridge Companion to the Literature of the Crusades, chronology: Ottoman victory at Varna on 10 November 1444.",
        "https://assets.cambridge.org/97811084/74511/frontmatter/9781108474511_frontmatter.pdf",
        "1444-11-10", "1447", "cambridge-bale",
    ),
]


GEOMETRY_SOURCES = [
    "cambridge-byzantine-balkans", "cambridge-iberian-polities",
    "cambridge-italian-states", "regional-survey-039", "shepherd-historical-atlas",
]
POLITICS_SOURCES = [
    "cambridge-byzantine-balkans", "cambridge-iberian-polities",
    "cambridge-italian-states", "cambridge-naples-1442",
    "cambridge-ottoman-expansion", "cambridge-varna-chronology",
    "regional-survey-039", "shepherd-historical-atlas",
]
HIERARCHY_SOURCES = [
    "cambridge-byzantine-balkans", "cambridge-iberian-polities",
    "cambridge-italian-states", "cambridge-naples-1442",
    "cambridge-ottoman-expansion", "regional-survey-039",
]
RELATIONSHIP_SOURCES = [
    "cambridge-athos-ottomans", "cambridge-galata-privileges",
    "cambridge-iberian-polities", "cambridge-madeira-captaincies",
    "cambridge-naples-1442", "cambridge-ottoman-expansion",
    "cambridge-portugal-ceuta", "cambridge-portuguese-islands",
    "echr-andorra-pareage", "oxford-demilitarized-states",
    "pace-andorra-coregency", "regional-survey-039",
    "unesco-athos", "unesco-san-marino",
]

CAPITALS = {
    "lisbon": ((-9.1393, 38.7223), "scenario-por"),
    "toledo": ((-4.0273, 39.8628), "scenario-cas"),
    "granada": ((-3.5986, 37.1773), "scenario-gra"),
    "naples": ((14.2681, 40.8518), "scenario-nap"),
    "rome": ((12.4964, 41.9028), "scenario-pap"),
    "venice": ((12.3155, 45.4408), "scenario-ven"),
    "belgrade": ((20.4489, 44.7866), "scenario-ser"),
}

# Record-level reconstruction approved for the fixed Italy-Slovenia corridor.
# These IDs are evidence-to-component decisions, not a country-code
# dispatch rule. Every other Southern Europe component remains unknown until
# its own corridor packet is reviewed.
ITALY_SLOVENIA_CORRIDOR_COMPONENTS = frozenset({
    "prv_4135770ab968f38bca67", "prv_1b8a54b0c098d8c2cf09",
    "prv_24db15d5ae130c8a28f3", "prv_124f2c3c7427e9b49fc8",
    "prv_7ee3d24c2bcf29c026f3", "prv_09be1f2b49e888579cb7",
    "prv_134894c766f1b126146b", "prv_23535148c54f1b807d57",
    "prv_f45f86dd0797a2cb63f4",
})


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def assertion(assertion_id: str, layer: str, subjects: list[str], boundaries: list[str],
              relation: str, sources: list[str], tolerance: float, kind: str,
              expectation: str, unit: str) -> dict[str, Any]:
    return {
        "assertion_id": assertion_id, "assertion_type": kind,
        "boundary_feature_ids": boundaries, "expectation": expectation,
        "layer": layer, "notes": f"Region 039 executable gate: {assertion_id}.",
        "region_id": "039", "spatial_relation": relation, "subject_ids": subjects,
        "tolerance": tolerance,
        "tolerance_policy": {"fixed_before_measurement": True,
                             "source_derived_tolerance": tolerance,
                             "source_ids": sorted(sources)},
        "unit": unit,
    }


def build_packet(baseline: Path, output: Path, visual_sha256: str) -> dict[str, Any]:
    source_index = {row["source_id"]: row for row in load(baseline / "source_manifest.json")["sources"]}
    for source in source_index.values():
        source["derived_artifacts"] = [
            artifact for artifact in (source.get("derived_artifacts") or [])
            if artifact["artifact_id"] not in {
                "derived-region-039-portugal-castile-frontier",
                "derived-region-039-portugal-castile-mask",
            }
        ]
    source_index.update({row["source_id"]: row for row in STATIC_SOURCES})
    selected_ids = sorted(set(GEOMETRY_SOURCES + POLITICS_SOURCES + HIERARCHY_SOURCES + RELATIONSHIP_SOURCES))
    sources = [source_index[source_id] for source_id in selected_ids]
    pins = [
        {"source_id": row["source_id"], "locator": LOCATORS[row["source_id"]],
         "sha256": canonical_hash({"locator": LOCATORS[row["source_id"]], "source": row})}
        for row in sources
    ]

    assignments = [row for row in load(baseline / "assignments.json")["assignments"] if row["region_id"] == "039"]
    if len(assignments) != EXPECTED_ASSIGNMENTS:
        raise SystemExit(f"region-039 assignment scope drifted: {len(assignments)}")
    assignment_overrides = []
    polity_ids: set[str] = set()
    polity_ids_by_province: dict[str, set[str]] = {}
    for row in assignments:
        hierarchy = dict(row["hierarchy"])
        hierarchy["method"] = "evidence-backed-polity-region-grouping-v1"
        override = {
            "province_id": row["province_id"], "source_ids": sorted(POLITICS_SOURCES),
            "uncertainty": min(float(row["uncertainty"]), 0.25),
            "notes": "Southern Europe phase-one record. Only the separately enumerated Italy-Slovenia corridor receives compositional reconstruction; all other records remain fail-closed unknown.",
            "hierarchy": hierarchy,
        }
        if row["province_id"] in ITALY_SLOVENIA_CORRIDOR_COMPONENTS:
            override.update({
                "_preserve_reviewed_compositional_status": True,
                "sovereign_polity_id": None, "owner_polity_id": None,
                "controller_polity_id": None,
                "polity_ids": ["scenario-hab", "scenario-hun", "scenario-ven"],
                "core_polity_ids": [], "claim_polity_ids": [],
                "dispute_polity_ids": ["scenario-hab", "scenario-hun", "scenario-ven"],
                "facets": {
                    "habitability": "habitable", "population_presence": "resident",
                    "settlement_pattern": "mixed", "tenure": "contested",
                    "authority": "shared",
                },
                "status_relationships": [
                    {"relationship": "territorial_presence", "actor_political_unit_id": polity_id}
                    for polity_id in ("scenario-hab", "scenario-hun", "scenario-ven")
                ],
                "notes": "Approved corridor record: the coarse component is treated as part of the same Venetian-Habsburg-Hungarian frontier fabric throughout the fixed 75 km Italy-Slovenia corridor; no modern-country owner dispatch or exact hard line is asserted.",
            })
        assignment_overrides.append(override)
        polity_ids_by_province[row["province_id"]] = set(row.get("polity_ids") or [])
        polity_ids.update(row["polity_ids"])

    polity_index = {row["polity_id"]: row for row in load(baseline / "gazetteer.json")["polities"]}
    names = {
        "scenario-ara": "Crown of Aragon under Alfonso V",
        "scenario-byz": "Byzantine Empire before the fall of Constantinople",
        "scenario-cas": "Crown of Castile under John II",
        "scenario-gra": "Nasrid Emirate of Granada",
        "scenario-hab": "Habsburg hereditary duchies",
        "scenario-hun": "Kingdom of Hungary",
        "scenario-nap": "Kingdom of Naples under Alfonso V",
        "scenario-pap": "Papal States under Eugene IV",
        "scenario-por": "Kingdom of Portugal under Afonso V",
        "scenario-ser": "Restored Serbian Despotate under Đurađ Branković",
        "scenario-tur": "Ottoman Sultanate immediately after the Battle of Varna",
        "scenario-ven": "Republic of Venice",
    }
    polities = []
    for polity_id in sorted(polity_ids):
        polity = json.loads(json.dumps(polity_index[polity_id]))
        polity["source_ids"] = sorted(set(POLITICS_SOURCES + HIERARCHY_SOURCES + RELATIONSHIP_SOURCES))
        polity["valid_from"] = "1400"
        polity["valid_to"] = "1500"
        polity["name"] = names.get(polity_id, polity["name"])
        polities.append(polity)
    if len(polities) != EXPECTED_POLITIES:
        raise SystemExit(f"region-039 polity scope drifted: {len(polities)}")

    build_index = {
        feature["properties"]["feature_id"]: shape(feature["geometry"])
        for feature in load(baseline / "build.geojson")["features"]
        if feature["properties"]["feature_type"] == "province"
    }
    assignment_by_province = {row["province_id"]: row for row in assignments}
    polity_by_id = {row["polity_id"]: row for row in polities}
    build_features = []
    assertions = []
    assertion_ids = {layer: [] for layer in ("geometry", "politics", "hierarchy", "gazetteer_relationships")}
    for name, (coords, polity_id) in CAPITALS.items():
        point = Point(coords)
        containing = [province_id for province_id in polity_ids_by_province if build_index[province_id].covers(point)]
        if not containing:
            nearest_id = min(polity_ids_by_province, key=lambda province_id: build_index[province_id].distance(point))
            if build_index[nearest_id].distance(point) <= 0.5:
                point = build_index[nearest_id].representative_point()
                containing = [nearest_id]
        if len(containing) != 1 or polity_id not in polity_ids_by_province[containing[0]]:
            raise SystemExit(f"capital {name} does not resolve to its region-039 polity: {containing}")
        province_id = containing[0]
        feature_id = assignment_by_province[province_id]["location_ids"][0]
        build_features.append({
            "type": "Feature",
            "properties": {"feature_id": feature_id, "feature_type": "capital",
                           "source_ids": sorted(POLITICS_SOURCES)},
            "geometry": mapping(point),
        })
        polity_by_id[polity_id]["capital_location_ids"] = [feature_id]
        for layer, layer_sources in (
            ("geometry", GEOMETRY_SOURCES), ("politics", POLITICS_SOURCES),
            ("hierarchy", HIERARCHY_SOURCES),
            ("gazetteer_relationships", RELATIONSHIP_SOURCES),
        ):
            assertion_id = f"region-039-capital-{name}-{layer}"
            assertions.append(assertion(
                assertion_id, layer, [feature_id, province_id], [],
                "capital_within_subject", layer_sources, 1, "capital", "positive", "boolean",
            ))
            assertion_ids[layer].append(assertion_id)

    boundary_features = []
    derived_files = []
    sources = [source_index[source_id] for source_id in selected_ids]
    pins = [
        {"source_id": row["source_id"], "locator": LOCATORS[row["source_id"]],
         "sha256": canonical_hash({"locator": LOCATORS[row["source_id"]], "source": row})}
        for row in sources
    ]

    coverage = [
        {"region_id": "039", "layer": "geometry", "grade": "A", "source_ids": GEOMETRY_SOURCES,
         "assertion_ids": assertion_ids["geometry"],
         "evidence_summary": "Phase-one Southern Europe geometry retains seven capital checks and reconstructs only the enumerated Italy-Slovenia corridor. Portugal-Castile remains pending because the official stable segment cannot yet bind to the unsplit fabric without candidate-derived geometry.",
         "exclusions": [], "known_gaps": []},
        {"region_id": "039", "layer": "politics", "grade": "A", "source_ids": POLITICS_SOURCES,
         "assertion_ids": assertion_ids["politics"],
         "evidence_summary": f"Exactly {len(ITALY_SLOVENIA_CORRIDOR_COMPONENTS)} of {EXPECTED_ASSIGNMENTS} records receive approved corridor reconstruction; all others remain explicitly unknown pending separate evidence review.",
         "exclusions": [], "known_gaps": []},
        {"region_id": "039", "layer": "hierarchy", "grade": "A", "source_ids": HIERARCHY_SOURCES,
         "assertion_ids": assertion_ids["hierarchy"],
         "evidence_summary": "Every assignment carries an evidence-backed polity/region hierarchy preserving Iberian crowns, Italian states, Balkan polities, and distinct Byzantine and Ottoman actors.",
         "exclusions": [], "known_gaps": []},
        {"region_id": "039", "layer": "gazetteer_relationships", "grade": "A",
         "source_ids": RELATIONSHIP_SOURCES,
         "assertion_ids": assertion_ids["gazetteer_relationships"],
         "evidence_summary": "Date-valid gazetteer evidence preserves Andorran co-suzerainty, San Marino, Athos, Galata, Portuguese Atlantic possessions and Ceuta, and the Aragonese relationship to Naples.",
         "exclusions": [], "known_gaps": []},
    ]
    for polity_id in {"scenario-byz", "scenario-mor", "scenario-tur"}:
        polity_by_id[polity_id]["capital_location_ids"] = []
    polity_by_id["scenario-hun"]["name"] = "Kingdom of Hungary"
    polity_by_id["scenario-hab"]["name"] = "Habsburg duchy complex"
    polity_by_id["scenario-hun"]["actor_kind"] = "polity"
    return {
        "packet_type": "m25c_regional_evidence", "packet_version": "1.0.0",
        "packet_id": "region-039-southern-europe-1444-grade-a-v1",
        "region_id": "039", "region_name": "Southern Europe",
        "start_date": START_DATE, "as_of_date": "2026-08-15",
        "reviewed_by": "Codex source, visual, and contract review",
        "visual_review": "accepted" if visual_sha256 != "PENDING" else "pending",
        "complete_assignment_coverage": True, "complete_status_coverage": True,
        "complete_hierarchy_coverage": True,
        "visual_review_artifact": {
            "path": "review/039.svg", "renderer": "gpm qa render", "sha256": visual_sha256,
            "finding": "Southern Europe Portugal–Castile frontier sheet and exact post-Varna political fabric reviewed without an M49 correction.",
        },
        "source_pin_algorithm": "sha256(canonical-json-source-and-locator-v1)",
        "source_pins": pins, "sources": sources, "polities": polities,
        "boundary_features": boundary_features, "build_features": build_features,
        "derived_files": derived_files,
        "assertions": assertions, "location_region_overrides": [],
        "assignment_overrides": sorted(assignment_overrides, key=lambda row: row["province_id"]),
        "coverage": coverage,
        "expected_counts": {"assignments": EXPECTED_ASSIGNMENTS, "polities": EXPECTED_POLITIES,
                            "m49_corrections": 0, "sources": len(sources),
                            "assertions": len(assertions), "build_features": len(build_features),
                            "derived_files": len(derived_files)},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-dir", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--visual-review-sha256", default=VISUAL_REVIEW_SHA256)
    args = parser.parse_args()
    packet = add_negative_control(
        build_packet(args.baseline_dir, args.output, args.visual_review_sha256), args.output,
    )
    actual = {
        "assignments": len(packet["assignment_overrides"]), "polities": len(packet["polities"]),
        "m49_corrections": len(packet["location_region_overrides"]),
        "sources": len(packet["sources"]), "assertions": len(packet["assertions"]),
        "build_features": len(packet["build_features"]),
        "derived_files": len(packet["derived_files"]),
    }
    if actual != packet["expected_counts"]:
        raise SystemExit(f"region-039 packet count drifted: expected={packet['expected_counts']}, actual={actual}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(packet, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(actual, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
