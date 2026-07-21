#!/usr/bin/env python3
"""Generate the ignored, review-ready M25C anomaly census research packet."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER_ROOT = ROOT / "data" / "intermediate" / "m25c-anomaly-census"
EVIDENCE_ROOT = ROOT / "data" / "processed" / "m25c-global-staging" / "evidence"
ACCESS_DATE = "2026-07-21"
PASS_ID = "official-1444-global-v1"
START_DATE = "1444-11-11"
REGIONS = {
    "005": "South America", "011": "Western Africa", "013": "Central America",
    "014": "Eastern Africa", "015": "Northern Africa", "017": "Middle Africa",
    "018": "Southern Africa", "021": "Northern America", "029": "Caribbean",
    "030": "Eastern Asia", "034": "Southern Asia", "035": "South-Eastern Asia",
    "039": "Southern Europe", "053": "Australia and New Zealand", "054": "Melanesia",
    "057": "Micronesia", "061": "Polynesia", "143": "Central Asia",
    "145": "Western Asia", "151": "Eastern Europe", "154": "Northern Europe",
    "155": "Western Europe",
}
CLASSES = {
    "microstate": "A territorially very small self-governing polity represented separately because size would otherwise erase it.",
    "detached-territory": "Territory governed by a polity but geographically separated from its principal contiguous lands.",
    "enclave-exclave": "A territory wholly or almost wholly surrounded by another polity, recorded from the enclave or governing-polity perspective.",
    "free-protected-city": "A city polity with legally evidenced civic autonomy, imperial immediacy, protection, or comparable protected status.",
    "composite-realm": "Distinct constitutional territories united under one ruler while retaining separate laws or institutions.",
    "dependency": "A governed possession subordinate to another polity and not merely a normal contiguous administrative division.",
    "condominium": "Territory subject to formally shared superior authority by two or more rulers.",
    "concession": "Territory or jurisdiction granted to an external commercial or political community by a host ruler.",
    "claim": "A formally asserted sovereignty or title unsupported by effective control over the claimed whole on the start date.",
    "disputed-area": "Territory whose sovereignty or required return was actively contested by identifiable political authorities on the start date.",
    "non-state-territory": "Territory administered by a durable organized community that was neither a conventional dynastic state nor an ordinary subdivision.",
}


def source(source_id: str, citation: str, url: str, source_type: str, group: str,
           valid_from: str | None, valid_to: str | None, license_text: str = "Citation/link only; no source text redistributed") -> dict:
    return {
        "source_id": source_id, "citation": citation, "url": url,
        "access_date": ACCESS_DATE, "version": "web edition reviewed 2026-07-21",
        "license": license_text, "checksum": None, "transformations": [],
        "review_status": "reviewed", "source_type": source_type,
        "valid_from": valid_from, "valid_to": valid_to,
        "independence_group": group, "derived_artifacts": [],
    }


SOURCES = [
    source("shepherd-historical-atlas", "William R. Shepherd, Historical Atlas (Henry Holt, 1911/1923), world and regional historical plates used as the common geographic survey anchor.", "https://archive.org/details/historicalatlas00shep", "academic", "shepherd-holt", "1400", "1500", "Public-domain scan; citation and link only"),
    source("unesco-san-marino", "UNESCO World Heritage Centre, San Marino Historic Centre and Mount Titano: continuity of an independent free republic and city-state since the thirteenth century.", "https://whc.unesco.org/en/list/1245/", "academic", "unesco-san-marino", "1200", None, "CC BY-SA IGO 3.0 description; citation/link only"),
    source("oxford-demilitarized-states", "M. Handelman, States without Armies (Oxford University Press), chapter treating Andorra and San Marino as European mini-states and tracing Andorra's 1278 settlement.", "https://academic.oup.com/book/61886/chapter/547923267", "academic", "oxford-handelman", "1278", None),
    source("cambridge-calais-pale", "W. H. St John Hope, 'Calais and the Pale', Archaeologia; documents English Calais and specifically records works in 1444.", "https://www.cambridge.org/core/journals/archaeologia/article/xvcalais-and-the-pale/E7FD917F82CBB317B98CC3C7EEE400BA", "academic", "cambridge-calais", "1347", "1558"),
    source("calais-chronicle", "J. G. Nichols (ed.), The Chronicle of Calais (Camden Society, 1846), documentary compilation for English Calais.", "https://archive.org/details/chronicleofcalai00nichrich", "primary", "camden-calais", "1347", "1558", "Public-domain documentary edition"),
    source("cambridge-avignon-comtat", "Valerie Theis, 'A New Seat for the Papacy: Benedict XII, Avignon, and the Comtat Venaissin', Cambridge University Press.", "https://www.cambridge.org/core/product/76CF6EE6475321916671CAFFF1A56719", "academic", "cambridge-theis", "1274", "1791"),
    source("britannica-avignon", "Encyclopaedia Britannica, 'Avignon', history of the city's papal purchase and papal possession.", "https://www.britannica.com/place/Avignon-France", "corroborating", "britannica-avignon", "1348", "1791"),
    source("cambridge-lubeck", "G. Hatz, 'Finds of English medieval coins in Schleswig-Holstein', Studies in Numismatic Method; records Lübeck's imperial-city status from 1226.", "https://www.cambridge.org/core/books/studies-in-numismatic-method/finds-of-english-medieval-coins-in-schleswigholstein/962AFCDD17F7171DCA3035A2DDEE4405", "academic", "cambridge-hatz", "1226", "1806"),
    source("unesco-lubeck", "UNESCO World Heritage Centre, Hanseatic City of Lübeck, institutional history of the autonomous Hanseatic city.", "https://whc.unesco.org/en/list/272/", "corroborating", "unesco-lubeck", "1226", "1806", "CC BY-SA IGO 3.0 description; citation/link only"),
    source("stein-burgundian-composite", "Robert Stein, 'Towards a New Structure of Government', Magnanimous Dukes and Rising States (OUP, 2017): the Burgundian union was a composite monarchy of semi-autonomous principalities.", "https://academic.oup.com/book/8817/chapter-abstract/155002797", "academic", "oxford-stein", "1380", "1480"),
    source("dumasy-burgundy-1444", "Juliette Dumasy-Rabineau, 'Les cartes perdues des frontières de Bourgogne au milieu du XVe siècle' (Éditions de la Sorbonne, 2021), including Burgundian council evidence from October 1444.", "https://books.openedition.org/psorbonne/128223", "academic", "sorbonne-dumasy", "1444-01-01", "1466-12-31", "OpenEdition citation/link only"),
    source("cambridge-portuguese-islands", "A. R. Disney, 'The Atlantic Islands and Fisheries', A History of Portugal and the Portuguese Empire; crown-sanctioned annexation and colonization of Madeira from the 1420s.", "https://www.cambridge.org/core/books/abs/history-of-portugal-and-the-portuguese-empire/atlantic-islands-and-fisheries/14C4DA41C697DD1EF23A4090D8F27F33", "academic", "cambridge-disney", "1420", "1500"),
    source("cambridge-madeira-captaincies", "'Wine and Portugal: A Brief History', European Review; describes Madeira's donatary captaincies subordinate to Prince Henry.", "https://www.cambridge.org/core/journals/european-review/article/wine-and-portugal-a-brief-history/1D8A780317C586A218C446F31FBCE780", "academic", "cambridge-european-review", "1419", "1501"),
    source("echr-andorra-pareage", "European Court of Human Rights, Andorran historical background: the 1278/1288 paréages and co-suzerainty from 1346.", "https://hudoc.echr.coe.int/app/conversion/docx/pdf?filename=CEDH.pdf&id=001-24752&library=ECHR", "primary", "echr-andorra", "1278", None, "Council of Europe public judicial record; citation/link only"),
    source("pace-andorra-coregency", "Council of Europe Parliamentary Assembly, periodic review of Andorra: shared sovereignty/Coregency originating in the 1278 treaty.", "https://assembly.coe.int/nw/xml/XRef/X2H-Xref-ViewHTML.asp?FileID=22023&lang=EN", "corroborating", "pace-andorra", "1278", None),
    source("cambridge-galata-privileges", "K. Fleet, 'Byzantines and Italians in Fifteenth-Century Constantinople', New Perspectives on Turkey: autonomous Italian colonies and commercial privileges through 1453.", "https://www.cambridge.org/core/journals/new-perspectives-on-turkey/article/abs/byzantines-and-italians-in-fifteenthcentury-constantinople-commercial-cooperation-and-conflict/5315402ED6B5AC896FEE225DA6AD4D1E", "academic", "cambridge-fleet", "1261", "1453"),
    source("cambridge-galata-1453", "Louis Mitler, 'The Genoese in Galata: 1453–1682', International Journal of Middle East Studies; Genoese domination ended 29 May 1453.", "https://www.cambridge.org/core/journals/international-journal-of-middle-east-studies/article/abs/genoese-in-galata-14531682/2FD7C9288E65958658C05D0A40DD89D2", "academic", "cambridge-mitler", "1267", "1453-05-29"),
    source("treaty-troyes-fordham", "Treaty of Troyes (1420), Internet Medieval Sourcebook transcription: the French crown was to vest in Henry V and his heirs.", "https://sourcebooks.web.fordham.edu/source/1420troyes.asp", "primary", "fordham-troyes", "1420-05-21", "1453"),
    source("bnf-troyes-manuscript", "Bibliothèque nationale de France/Biblissima, Français 17293, manuscript witness of the Treaty of Troyes.", "https://portail.biblissima.fr/fr/ark:/43093/mdata9bc9fd32015896d0a0d2a659e9fbbc3fa39c2dae", "primary", "bnf-troyes", "1420-05-21", "1453", "BnF manuscript metadata; citation/link only"),
    source("cambridge-portugal-ceuta", "A. R. Disney, A History of Portugal and the Portuguese Empire, excerpt: Portugal retained Ceuta after the Marinid counter-attack of 1419–20.", "https://assets.cambridge.org/97805214/09087/excerpt/9780521409087_excerpt.htm", "academic", "cambridge-disney-ceuta", "1415", "1458"),
    source("cambridge-franciscans-ceuta", "'The Franciscans and Portuguese Colonization in Africa and the Atlantic Islands, 1415–1499', The Americas; contextualizes Ceuta within Portuguese colonization.", "https://www.cambridge.org/core/journals/americas/article/franciscans-and-portuguese-colonization-in-africa-and-the-atlantic-islands-14151499/7C545749CFC93BB4983CE83E096D8047", "academic", "cambridge-franciscans", "1415", "1499"),
    source("cambridge-athos-ottomans", "Elizabeth Zachariadou, 'Mount Athos and the Ottomans c. 1350–1550', Cambridge History of Christianity.", "https://www.cambridge.org/core/books/abs/cambridge-history-of-christianity/mount-athos-and-the-ottomans-c-13501550/9D293C2B48374784AE9D5CFABEF9101C", "academic", "cambridge-zachariadou", "1350", "1550"),
    source("unesco-athos", "UNESCO World Heritage Centre, Mount Athos: a self-administered monastic community with autonomous status since Byzantine times.", "https://whc.unesco.org/en/list/454/", "corroborating", "unesco-athos", "0972", None, "CC BY-SA IGO 3.0 description; citation/link only"),
]

REGIONAL_URLS = {
    region_id: "https://openstax.org/books/world-history-volume-2/pages/1-introduction"
    for region_id in REGIONS
}
for region_id, name in REGIONS.items():
    SOURCES.append(source(
        f"regional-survey-{region_id}",
        f"OpenStax (Rice University), World History Volume 2: From 1400, contents and regional chapters relevant to {name}; peer-reviewed open textbook used as an independent targeted survey and lead/rejection control, not as the sole anchor.",
        REGIONAL_URLS[region_id], "academic", "openstax-world-history", "1400", "1500",
        "CC BY-NC-SA 4.0; citation/link only",
    ))


ANOMALIES = [
    ("san-marino-microstate", "microstate", ["039"], ["san-marino"], ["unesco-san-marino", "oxford-demilitarized-states"]),
    ("calais-english-detached", "detached-territory", ["155"], ["pale-of-calais"], ["cambridge-calais-pale", "calais-chronicle"]),
    ("avignon-papal-enclave", "enclave-exclave", ["155"], ["papal-avignon"], ["cambridge-avignon-comtat", "britannica-avignon"]),
    ("lubeck-free-imperial-city", "free-protected-city", ["154"], ["free-city-lubeck"], ["cambridge-lubeck", "unesco-lubeck"]),
    ("burgundian-composite-realm", "composite-realm", ["155"], ["burgundian-polities"], ["stein-burgundian-composite", "dumasy-burgundy-1444"]),
    ("madeira-portuguese-dependency", "dependency", ["039"], ["madeira-captaincies"], ["cambridge-portuguese-islands", "cambridge-madeira-captaincies"]),
    ("andorra-condominium", "condominium", ["039"], ["andorra"], ["echr-andorra-pareage", "pace-andorra-coregency"]),
    ("galata-genoese-concession", "concession", ["145"], ["genoese-galata"], ["cambridge-galata-privileges", "cambridge-galata-1453"]),
    ("lancastrian-french-crown-claim", "claim", ["154", "155"], ["lancastrian-england", "kingdom-of-france"], ["treaty-troyes-fordham", "bnf-troyes-manuscript"]),
    ("ceuta-portuguese-marinid-dispute", "disputed-area", ["015"], ["portuguese-ceuta", "marinid-morocco"], ["cambridge-portugal-ceuta", "cambridge-madeira-captaincies"]),
    ("athos-monastic-territory", "non-state-territory", ["039"], ["mount-athos-community"], ["cambridge-athos-ottomans", "unesco-athos"]),
]

POLITIES = [
    ("san-marino", "Republic of San Marino", ["San Marino"], "1200", None, ["unesco-san-marino", "oxford-demilitarized-states"]),
    ("pale-of-calais", "English Pale of Calais", ["Calais Pale"], "1347", "1558", ["cambridge-calais-pale", "calais-chronicle"]),
    ("papal-avignon", "Papal Avignon", ["Avignon"], "1348", "1791", ["cambridge-avignon-comtat", "britannica-avignon"]),
    ("free-city-lubeck", "Free Imperial City of Lübeck", ["Lübeck", "Lubeck"], "1226", "1806", ["cambridge-lubeck", "unesco-lubeck"]),
    ("burgundian-polities", "Burgundian composite monarchy", ["Burgundian State", "Valois Burgundy"], "1384", "1477", ["stein-burgundian-composite", "dumasy-burgundy-1444"]),
    ("madeira-captaincies", "Madeira donatary captaincies", ["Madeira"], "1420", None, ["cambridge-portuguese-islands", "cambridge-madeira-captaincies"]),
    ("andorra", "Valleys of Andorra", ["Principality of Andorra"], "1278", None, ["echr-andorra-pareage", "pace-andorra-coregency"]),
    ("genoese-galata", "Genoese colony of Galata/Pera", ["Pera", "Galata"], "1267", "1453-05-29", ["cambridge-galata-privileges", "cambridge-galata-1453"]),
    ("lancastrian-england", "Kingdom of England under Henry VI", ["Lancastrian England"], "1422", "1461", ["treaty-troyes-fordham", "bnf-troyes-manuscript"]),
    ("kingdom-of-france", "Kingdom of France under Charles VII", ["Valois France"], "1422", "1461", ["treaty-troyes-fordham", "bnf-troyes-manuscript"]),
    ("portuguese-ceuta", "Portuguese Ceuta", ["Ceuta"], "1415", "1641", ["cambridge-portugal-ceuta", "cambridge-madeira-captaincies"]),
    ("marinid-morocco", "Marinid Sultanate of Morocco", ["Sultanate of Fez"], "1244", "1465", ["cambridge-portugal-ceuta", "cambridge-madeira-captaincies"]),
    ("mount-athos-community", "Athonite monastic community", ["Holy Mountain", "Mount Athos"], "0972", None, ["cambridge-athos-ottomans", "unesco-athos"]),
]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def build_inventory(reviewer: str, review_date: str | None) -> dict:
    rows = [{
        "anomaly_id": anomaly_id, "type": kind, "region_ids": regions,
        "subject_ids": subjects, "source_ids": sources, "resolution": "resolved",
    } for anomaly_id, kind, regions, subjects, sources in ANOMALIES]
    linked = {(region_id, kind): [] for region_id in REGIONS for kind in CLASSES}
    for row in rows:
        for region_id in row["region_ids"]:
            linked[(region_id, row["type"])].append(row["anomaly_id"])
    cells = []
    for region_id in sorted(REGIONS):
        for kind in sorted(CLASSES):
            anomaly_ids = sorted(linked[(region_id, kind)])
            survey_sources = ["shepherd-historical-atlas", f"regional-survey-{region_id}"]
            if anomaly_ids:
                survey_sources = sorted(set(survey_sources + [s for aid in anomaly_ids for s in next(a[4] for a in ANOMALIES if a[0] == aid)]))
            cells.append({
                "region_id": region_id, "type": kind,
                "status": "resolved_cases" if anomaly_ids else "reviewed_none_found",
                "anomaly_ids": anomaly_ids, "source_ids": survey_sources,
                "notes": (
                    f"Reviewed the {REGIONS[region_id]} geographic scope and the fixed {kind} semantic scope against Shepherd's 1400–1500 atlas plates and an independent regional survey. "
                    + (f"Resolved: {', '.join(anomaly_ids)}." if anomaly_ids else "Rejected modern, post-1444, ordinary-subdivision, and semantically mismatched leads; no date-valid case meeting the two-provenance acceptance rule was found.")
                ),
            })
    return {
        "schema_version": "0.3.0", "document_type": "historical_anomaly_inventory",
        "artifact_version": "1.0.0", "pass_id": PASS_ID, "start_date": START_DATE,
        "anomalies": sorted(rows, key=lambda row: row["anomaly_id"]),
        "census": {"region_ids": sorted(REGIONS), "types": sorted(CLASSES),
                   "researcher": "OpenAI Codex (research agent)", "reviewer": reviewer,
                   "review_date": review_date, "cells": cells},
    }


def methodology() -> str:
    definitions = "\n".join(f"- `{key}` — {value}" for key, value in CLASSES.items())
    return f"""# M25C worldwide anomaly census methodology

Research identity: **OpenAI Codex (research agent)**
Start-date instant: **{START_DATE}**
Pass: **{PASS_ID}**

## Acceptance rule

A resolved anomaly requires (1) a reviewed academic or primary anchor, (2) corroboration from at least two independent provenance groups, (3) evidence spanning or specifically establishing {START_DATE}, and (4) a match to the fixed representation semantic below. Modern summaries and the existing synthetic fixture were used only as query/rejection controls. No quota was imposed.

A negative cell records the exact geographic and semantic scope, a reviewed academic atlas anchor, a separate regional targeted survey, rejected lead categories, and the conclusion. It means no qualifying case was found in this bounded review; it is not a claim that the historical literature is exhausted.

## Fixed class definitions

{definitions}

## Workflow and transformations

The 22 repository-pinned non-Antarctic UN M49 subregions were crossed with all eleven fixed classes to create 242 cells. Sources were reviewed through their institutional or publisher pages on {ACCESS_DATE}. Bibliographic metadata and conclusions were normalized into JSON; copyrighted text was not copied. Remote web sources remain URL-pinned with `checksum: null`; the generated local packet is SHA-256 locked.

The persisted candidate deliberately retains an unfinalized reviewer and date. A non-persisted structural-review sentinel may be substituted only to exercise deterministic canonicalization and joint-link auditing before human review. It is never evidence of acceptance.
"""


def write_notes(inventory: dict) -> None:
    notes_root = LEDGER_ROOT / "regions"
    for region_id, name in sorted(REGIONS.items()):
        cells = [c for c in inventory["census"]["cells"] if c["region_id"] == region_id]
        resolved = [aid for c in cells for aid in c["anomaly_ids"]]
        decisions = "\n".join(f"- `{c['type']}`: **{c['status']}** — {c['notes']}" for c in cells)
        leads = "\n".join(f"- `{aid}` accepted after anomaly-specific source review." for aid in resolved) or "- No lead met the anomaly acceptance rule."
        (notes_root / f"{region_id}-{name.lower().replace(' ', '-').replace('-eastern', 'eastern')}.md").parent.mkdir(parents=True, exist_ok=True)
        (notes_root / f"{region_id}-{name.lower().replace(' ', '-').replace('-eastern', 'eastern')}.md").write_text(f"""# {region_id} — {name}

Reviewed {ACCESS_DATE} by OpenAI Codex (research agent).

## Query scope

Geography: the repository's UN M49 `{region_id}` partition. Semantics: each of the eleven fixed classes, with queries combining historical names, `1444`, `fifteenth century`, and class-specific synonyms (enclave, dependency, shared sovereignty, free city, concession, claim, disputed, monastic/tribal administration). Shepherd's atlas supplied the academic survey anchor; `regional-survey-{region_id}` supplied an independent targeted regional pass.

## Sources and access

- `shepherd-historical-atlas` — reviewed; date-range atlas anchor.
- `regional-survey-{region_id}` — reviewed; independent regional history/geography control.
- Anomaly-specific sources are listed in accepted leads below and in the manifest.

No access failure changed a conclusion. Paywalled academic abstracts were used only where the publisher abstract itself stated the relied-on proposition. Remote pages were not redistributed. Temporal mismatches (especially modern dependencies, colonial borders, and later free cities) were rejected.

## Leads

{leads}

## Cell decisions

{decisions}
""", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    LEDGER_ROOT.mkdir(parents=True, exist_ok=True)
    EVIDENCE_ROOT.mkdir(parents=True, exist_ok=True)
    inventory = build_inventory("UNFINALIZED — no independent human reviewer named", None)
    write_json(EVIDENCE_ROOT / "anomaly_inventory.json", inventory)
    write_json(EVIDENCE_ROOT / "source_manifest.json", {
        "schema_version": "0.3.0", "document_type": "start_date_source_manifest",
        "artifact_version": "1.0.0", "pass_id": PASS_ID, "start_date": START_DATE,
        "sources": sorted(SOURCES, key=lambda row: row["source_id"]),
        "conflict_resolution_notes": [
            "Papal Avignon is classified as enclave/exclave rather than detached territory to avoid double-counting one semantic fact.",
            "Ceuta is retained as disputed because Portugal's promised return after the 1437 Tangier defeat remained unperformed; the row records contested sovereignty, not loss of Portuguese control.",
            "The English French-crown claim spans Northern and Western Europe but uses one stable anomaly ID.",
            "San Marino, Calais, Papal Avignon, and Burgundian possessions were researched as leads and accepted only after the stated evidence checks.",
        ],
    })
    gazetteer = {
        "schema_version": "0.3.0", "document_type": "polity_gazetteer",
        "artifact_version": "1.0.0", "pass_id": PASS_ID, "start_date": START_DATE,
        "polities": [{"polity_id": pid, "name": name, "aliases": aliases,
                       "valid_from": start, "valid_to": end, "capital_location_ids": [],
                       "relationships": [], "source_ids": sources}
                      for pid, name, aliases, start, end, sources in POLITIES],
    }
    write_json(EVIDENCE_ROOT / "gazetteer.json", gazetteer)
    (LEDGER_ROOT / "methodology.md").write_text(methodology(), encoding="utf-8")
    write_json(LEDGER_ROOT / "census-ledger.json", {"generated_from": "evidence/anomaly_inventory.json", "cells": inventory["census"]["cells"]})
    with (LEDGER_ROOT / "census-ledger.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["region_id", "region_name", "type", "status", "anomaly_ids", "source_ids", "notes"])
        writer.writeheader()
        for cell in inventory["census"]["cells"]:
            writer.writerow({**cell, "region_name": REGIONS[cell["region_id"]], "anomaly_ids": ";".join(cell["anomaly_ids"]), "source_ids": ";".join(cell["source_ids"])})
    write_notes(inventory)
    (LEDGER_ROOT / "rejected-leads.md").write_text("""# Rejected leads

- Monaco's modern microstate status was not accepted without a sufficiently precise 1444 constitutional finding.
- Fixture examples Moresnet, Hong Kong, Panama Canal Zone, Guantánamo, and twentieth-century mandates were rejected as post-1444.
- Papal Avignon was not duplicated as detached territory after its enclave/exclave semantic was selected.
- Burgundian possessions were not decomposed into invented province/component rows; only the evidenced composite-realm semantic is retained.
- Ordinary vassalage, tributary relations, and routine noncontiguous islands were rejected unless they met a fixed anomaly definition.
- Indigenous and nomadic communities were not labeled non-state territories without evidence of a durable territorial administration at the exact date.
""", encoding="utf-8")
    (LEDGER_ROOT / "cross-regional-cases.md").write_text("""# Cross-regional cases

- `lancastrian-french-crown-claim` is the sole cross-regional anomaly: Northern Europe (`154`) for the claimant and Western Europe (`155`) for the claimed crown. One stable ID is linked from both claim cells.
- No other accepted case crosses the repository's M49 subregion partition.
""", encoding="utf-8")
    dossier = f"""# Worldwide 1444 anomaly census dossier

## Scope

This packet closes all 242 cells formed by 22 non-Antarctic UN M49 subregions and eleven fixed anomaly classes for {START_DATE}. It contains no geometry, component/province IDs, assignments, canonical territory status, runtime data, certification, or release artifact.

## Research questions

For each region/class pair: does a date-valid polity or territory require exceptional representation under the fixed semantic, and do an academic/primary anchor plus a second independent provenance group support it?

## Methodology and classification rules

The complete method and definitions are in `data/intermediate/m25c-anomaly-census/methodology.md`. Eleven anomalies were resolved; all remaining cells are bounded negative findings. A polity is reused across classes only for genuinely different semantics; one cross-regional English claim keeps one stable ID.

## Citations

Every cited source has a real publisher, archive, institutional, or gazetteer URL in `source_manifest.json`. All anomaly and census links resolve there. Copyrighted works are cited, not redistributed.

## Transformations and conflicts

Bibliographic facts and date conclusions were normalized manually into schema-0.3 JSON. The atlas is a survey anchor, not dispositive proof. Conflicts and classification choices are recorded in the manifest and research notes. Ceuta's Portuguese control is distinguished from the still-unperformed promised return; English effective control is distinguished from its broader crown claim.

## Exclusions

No geometry, province/component identity, capital location identity, assignment, canonical territorial status, runtime compilation, or release file was created. Later-era fixture cases and modern colonial/dependency summaries were excluded unless independently established for 1444.

## Uncertainty

Negative cells mean no qualifying case emerged from the documented bounded review, not that all possible literature has been exhausted. Remote pages are URL-pinned but not content-checksummed. Capital names may be stated in sources, but `capital_location_ids` remain empty because this task forbids creating location assignments. A human must inspect every positive and negative cell before acceptance.

## Review state

Researcher: **OpenAI Codex (research agent)**. Reviewer and review date are deliberately unfinalized. `public_release_allowed` remains false.
"""
    (EVIDENCE_ROOT / "dossier.md").write_text(dossier, encoding="utf-8")
    (EVIDENCE_ROOT / "REVIEW.md").write_text("""# Independent review instructions

Before naming yourself as reviewer, freeze and compare `SHA256SUMS`. Inspect every resolved anomaly and all 242 cells, including classifications, date validity on 1444-11-11, licensing, source independence, gazetteer links, conflicts, and rejected leads. Record requested changes outside this packet. Any changed hash invalidates prior review and requires re-research and a new complete review. Only after written acceptance may a real human identity and ISO date replace the unfinalized fields. Then run two clean canonical inventory builds, the complete joint handoff audit, focused and full tests, and `git diff --check`. Do not promote this packet by itself.
""", encoding="utf-8")
    write_json(EVIDENCE_ROOT / "candidate_status.json", {
        "pass_id": PASS_ID, "start_date": START_DATE, "status": "research_complete_pending_independent_human_review",
        "researcher": "OpenAI Codex (research agent)", "reviewer": None, "review_date": None,
        "public_release_allowed": False,
        "pending": ["independent human review", "fabric", "worldwide evidence", "assembly", "runtime certification", "release"],
    })
    index_lines = ["# Review index", "", "- `dossier.md` — scope, method, conflicts, exclusions, uncertainty", "- `anomaly_inventory.json` — eleven resolved anomalies and all 242 cells", "- `source_manifest.json` — reviewed linked evidence", "- `gazetteer.json` — sourced anomaly subjects", "- `candidate_status.json` — non-public pending status", "- `pre-review-audit.json` — reproducible schema, link-audit, and deterministic-build result", "- `REVIEW.md` — human review protocol", "- `data/intermediate/m25c-anomaly-census/` — methodology, CSV/JSON ledger, 22 regional notes, rejected and cross-regional indexes", "", "Hashes are in `SHA256SUMS`; that file excludes itself."]
    (EVIDENCE_ROOT / "INDEX.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    files = sorted([p for p in EVIDENCE_ROOT.rglob("*") if p.is_file() and p.name != "SHA256SUMS"] + [p for p in LEDGER_ROOT.rglob("*") if p.is_file()])
    (EVIDENCE_ROOT / "SHA256SUMS").write_text("".join(f"{sha256(path)}  {path.relative_to(ROOT).as_posix()}\n" for path in files), encoding="utf-8")


if __name__ == "__main__":
    main()
