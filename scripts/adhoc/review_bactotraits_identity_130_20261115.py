#!/usr/bin/env python3
"""2026-11-15: author one source-identity investigation review for EdgeMech #130.

Inputs: unchanged fresh-05 source/occurrence/abstract, four captured catalogs,
their receipts and extractor, and two maintained KG-Microbe owner-file snapshots.
Outputs: fresh private proof stage and a new canonical partial structured review.
This is a self-review, excluded from independent calibration. No network calls,
source corrections, graph admissions, or changes to historical reviews occur.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import capture_strain_authorities_130_20261115 as capture
import run_abstract_canary_20261115 as base

ROOT = base.ROOT
AUTHORITY_DIRECTORY = ROOT / ".temp/identity130/authorities"
CAPTURE_SCRIPT = "scripts/adhoc/capture_strain_authorities_130_20261115.py"
CAPTURE_SHA = "56b1ef847187e15a80a00e7b197f28435fcb465bdb0c3954cc097ffbe07388f1"
THIS_SCRIPT = "scripts/adhoc/review_bactotraits_identity_130_20261115.py"
PREVIOUS_ID = "20261116T052355Z-fresh05-abstract-adapter"
PREVIOUS_PATH = "reviews/structured/" + PREVIOUS_ID + "/review.yaml"
PREVIOUS_SHA = "b1ca23d2c1d2854f73c85564d2cad27572736465c06ef47345319266664b3427"
KGM = Path("/Users/marcin/Documents/VIMSS/ontology/KG-Hub/KG-Microbe/kg-microbe")
KGM_COMMIT = "ef27b97a0b450767da54235c6105b5250c178adc"
OWNER_PATHS = [
    {"repository": "Knowledge-Graph-Hub/kg-microbe", "path": "download.yaml",
     "role": "Maintained BactoTraits source download and checksum pin"},
    {"repository": "Knowledge-Graph-Hub/kg-microbe",
     "path": "kg_microbe/transform_utils/bactotraits/bactotraits.py",
     "role": "Maintained BacDive-ID to NCBI identity join and BactoTraits transform"},
]
AUTHORITY_PINS = {
    "dsm19353": {
        "raw": "d416237bc389c88a12185f6981a97faf10cfb091c579b6fb10f721a24c9e1921",
        "text": "8fa3d180a19442d947a7bbdd86cf1efd78f6ca891fe2acbc42f2c6a9d15c6d82",
        "receipt": "99b8f7dde10107d7e6510f2cfb2ded46ca4dfba3e8b6e6230ef7990dc49e8bbf",
        "quote": "19353, Type strain dsm-19353 dsm19353 dsm 19353 Thioprofundum lithotrophicum\n"
                 "Strain designation:\n106\nOther collection no.\nor WDCM no.:\nJCM 14586",
        "summary": "DSM 19353 and JCM 14586 identify Thioprofundum lithotrophicum strain 106, "
                   "not the nominal Rubritalea strain."},
    "jcm14586": {
        "raw": "6ee861e0a76f89b937aa79249450267985202f26a326ce629d0119d1b36effaf",
        "text": "93d5aec6c739d6bd48c4c4aa66416c7dfe4220ff9ca5c572a1010ad02be0440f",
        "receipt": "8906c5337592813bbcf2767bc45cfe08f5520a45922e00df0545f84e01071b9c",
        "quote": "BacDive ID: 17847.\nNCBI Taxonomy ID: 571898.",
        "summary": "JCM 14586's complete catalog page corroborates strain 106/DSM 19353 and "
                   "binds it to BacDive 17847 and NCBI 571898. It documents the original-paper "
                   "JCM 14596 typographical error; that typo is not a new equivalent accession."},
    "dsm18772": {
        "raw": "e6ce0ea2affb04b490b537478a4b804371e187e3eb44f29cff2a99e0875b7079",
        "text": "99c07d7d2dfeb73ed1fbb69e8213c8034146e51140b2a80f160bd59faead79c8",
        "receipt": "c4dff78887cf1fc393286867e2954d2d39198ff521dec8417984cdecb3359328",
        "quote": "18772, Type strain dsm-18772 dsm18772 dsm 18772 Rubritalea squalenifaciens\n"
                 "Strain designation:\nHOact 23\nOther collection no.\nor WDCM no.:\n"
                 "MBIC08254,NBRC 103619",
        "summary": "The nominal Rubritalea squalenifaciens type strain has DSM 18772, "
                   "HOact 23, MBIC08254 and NBRC 103619 aliases."},
    "bacdive17851": {
        "raw": "1a6b1f17cea659277484d7461db6ad3f50e6e32a85c6bf5abdc472e8a489b592",
        "text": "29f41098eb41eb4a6ca0d46abe5ecd746e8cc5dbb4edac5cb6b8233bd6cdd7bc",
        "receipt": "6a0e0f46648056fa529748d5010db3df04600a40fb86ab1da2edeba85ac26ea9",
        "quote": "BacDive ID\n17851\nType strain\nStrain Designation\nHOact 23\nCulture col. no.\n"
                 "DSM 18772\nMBIC 08254\nNBRC 103619\nHOact 23\nNCBI tax ID(s)\n1123071\n407226",
        "summary": "Current BacDive 17851 retains the Rubritalea culture aliases. Its inspected "
                   "sequence sections distinguish strain/genome 1123071 from species/16S 407226; "
                   "this catalog is not independent NCBI ontology adjudication."},
}
SERVICE_PINS = {
    "cborg-service-provenance.json":
        "f9e7ce85c9c9a2738d14384f46251797ad5d213f1efb1d7b8a2ce95d76b289d0",
    "cborg-tavily-dsm18772.json":
        "49096c6b7b7607d1071415bac9e70ab298326c9628d45f7b2aa36351e1611481",
}
AUTHORITY_IDS = ["catalog-" + name for name in AUTHORITY_PINS]
SOURCE_IDS = ["packet-source", *AUTHORITY_IDS]


def canonical_utc_timestamp(value):
    """Convert an aware capture instant to CLAW's UTC-Z form without changing it (#133)."""
    if not isinstance(value, str) or re.search(r"[.,]\d{7,}", value):
        raise ValueError("Capture timestamp must be an ISO instant with at most microsecond precision")
    instant = datetime.fromisoformat(value)
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError("Capture timestamp requires an explicit timezone offset")
    utc = instant.astimezone(timezone.utc)
    precision = "microseconds" if utc.microsecond else "seconds"
    return utc.isoformat(timespec=precision).removesuffix("+00:00") + "Z"


def load_authorities():
    base.checked_input(ROOT / CAPTURE_SCRIPT, CAPTURE_SHA)
    base.checked_input(ROOT / PREVIOUS_PATH, PREVIOUS_SHA)
    records = {}
    for name, expected in AUTHORITY_PINS.items():
        raws = {kind: base.checked_input(AUTHORITY_DIRECTORY / (name + suffix), expected[kind])
                for kind, suffix in (("raw", ".html"), ("text", ".txt"), ("receipt", ".json"))}
        receipt = json.loads(raws["receipt"])
        base.require(receipt["name"] == name and receipt["requested_url"] == capture.URLS[name]
                     == receipt["final_url"] and receipt["status"] == 200,
                     "Authority receipt identity or response status differs")
        base.require(receipt["script_sha256"] == CAPTURE_SHA
                     and receipt["extractor"] == "catalog-html-text/v1"
                     and receipt["authenticated"] is False
                     and receipt["channel"] == "anonymous_primary_catalog"
                     and receipt["http_calls"] == 1, "Authority capture provenance differs")
        for kind in ("raw", "text"):
            suffix = ".html" if kind == "raw" else ".txt"
            base.require(receipt[kind + "_sha256"] == expected[kind]
                         and receipt[kind + "_bytes"] == len(raws[kind])
                         and receipt[kind + "_path"] == str(
                             (AUTHORITY_DIRECTORY / (name + suffix)).relative_to(ROOT)),
                         "Authority receipt content binding differs")
        extractor = capture.Text()
        extractor.feed(raws["raw"].decode(receipt["charset"], errors="strict"))
        text = "\n".join(" ".join(line.split()) for line in "".join(extractor.parts).splitlines()
                         if line.strip()) + "\n"
        base.require(text.encode() == raws["text"], "Authority text derivative does not replay")
        document = base.LiteratureCache._document({"response_sha256": expected["text"]},
                                                 "authority_text", text)
        span = base.verify_quote(document, expected["quote"])
        base.require(len(expected["quote"].split()) <= 25, "Authority quote exceeds source budget")
        records[name] = {"raws": raws, "receipt": receipt, "span": span}
    service_raws = {name: base.checked_input(AUTHORITY_DIRECTORY / name, sha)
                    for name, sha in SERVICE_PINS.items()}
    service = json.loads(service_raws["cborg-service-provenance.json"])
    base.require(len(service["tool_calls"]) == 3
                 and all(call["auth_mode"] == "keyed" for call in service["tool_calls"])
                 and service["publisher_tdm_calls"] == service["valency_calls"] == 0,
                 "Recorded service usage differs")
    owners = {}
    for owner in OWNER_PATHS:
        owners[owner["path"]] = subprocess.check_output(
            ["git", "-C", str(KGM), "show", KGM_COMMIT + ":" + owner["path"]])
    base.require(all(owners.values()), "Maintained owner snapshot is empty")
    return records, service_raws, owners


def assessment(axis, area, summary, details):
    ids = (base.PAPER_IDS if axis in {"claim", "literature"}
           else SOURCE_IDS if axis in {"subject_node", "source_fidelity"}
           else ["packet-source"])
    dimensions = {"axis": axis, "category": base.AXES[axis],
                  "scope": "Original fresh-05 occurrence; bounded source-identity investigation",
                  **details}
    return {"assessment_id": axis.replace("_", "-"), "area": area,
            "topic": "Source-identity investigation: " + axis.replace("_", " "),
            "outcome": base.CATEGORIES[axis][base.AXES[axis]], "summary": summary,
            "target_ids": [base.OCCURRENCE], "evidence_ids": ids,
            "dimensions": [{"name": name, "value": value,
                            "definition": "Authored bounded source-identity judgment: " + name,
                            "evidence_ids": ids} for name, value in dimensions.items()]}


def authored_assessments():
    return [
        assessment("claim", "grounding",
                   "The retained abstract reports nonmotility for the nominal DSM 18772 strain. "
                   "The original identifier-bound graph assertion remains not assessable: "
                   "the source row mixes identities and formal predicate/node checks remain incomplete.",
                   {"assertion_scope": "NCBITaxon:1123071 biolink:has_phenotype METPO:1000703, "
                    "with original DSM 18772/non motile labels. The accession conflict is not "
                    "a biological refutation and is not repaired by replacing the subject."}),
        assessment("literature", "evidence",
                   "The same two DOI/PMID-bound abstract quotations partly address nonmotility "
                   "for HOact23/DSM 18772. Catalog identity checks add no full-paper assay evidence "
                   "and do not establish ownership of every trait in the mixed source row.",
                   {"search_scope": "Retained complete abstract only, DOI " + base.DOI +
                    ", PMID " + base.PMID + "; no new paper search or full-paper inspection.",
                    "literature_channel": "europepmc_abstract_retained; separate catalog discovery "
                    "used 3 CBORG Tavily calls and 4 anonymous primary-catalog GETs; no TDM.",
                    "inspected_extent": "Complete retained abstract and its two unchanged short snippets."}),
        assessment("relation", "representation",
                   "Culture accession disambiguation does not validate has_phenotype/RO:0002200. "
                   "A scoped versioned predicate authority assessment remains outstanding.",
                   {"direction": "Original organism-to-phenotype direction preserved.",
                    "domain_range": "No new versioned domain/range proof authored.",
                    "specificity": "Relation fitness for the original nonmotility statement unresolved.",
                    "qualifiers": "Abstract and catalogs do not supply complete assay conditions "
                    "or warrant a universal-condition reading."}),
        assessment("subject_node", "identity",
                   "Current DSMZ/BacDive catalogs verify the nominal DSM 18772/HOact23 culture "
                   "link. DSM 19353/JCM 14586 instead identify Thioprofundum strain 106. Formal "
                   "NCBI/Biolink identity, rank and category assessment remains unresolved.",
                   {"identity": "NCBITaxon:1123071 retained. BacDive 17851 distinguishes genome "
                    "1123071 from species/16S 407226. The competing culture pair maps through "
                    "JCM to BacDive 17847/NCBI 571898, not an equivalent Rubritalea accession.",
                    "label": "Original Rubritalea squalenifaciens DSM 18772 label preserved.",
                    "category_fit": "biolink:OrganismTaxon retained; catalog agreement is not "
                    "formal Biolink category validation.",
                    "rank_or_type": "Catalogs distinguish type-strain aliases and species/genome "
                    "identifiers; independent NCBI rank/status verification remains incomplete.",
                    "definition": "No complete versioned node-definition proof authored.",
                    "authority_version": "Four independently captured catalog snapshots are bound "
                    "by capture timestamps, raw/text hashes and receipts; the unresolved source "
                    "join prevents treating them as complete original-assertion validation."}),
        assessment("object_node", "representation",
                   "Nonmotility is reported for the nominal isolate, but this identity review "
                   "does not adjudicate METPO:1000703 definition or graph category fitness.",
                   {"identity": "Original METPO:1000703 retained; no replacement proposed.",
                    "label": "Original non motile label retained.",
                    "category_fit": "biolink:PhenotypicQuality requires a scoped authority check.",
                    "rank_or_type": "Nominal phenotype class; formal typing remains unresolved.",
                    "definition": "No new versioned METPO definition proof authored.",
                    "authority_version": "Preparation authorities are not substituted for new "
                    "inspected and scoped modeling evidence."}),
        assessment("source_fidelity", "provenance",
                   "The incompatible culture links are now independently confirmed. The row's "
                   "BacDive ID/name and collection codes refer to different taxa; the maintained "
                   "transform selects NCBI by BacDive ID. A safe field replacement and verified "
                   "row correction have not been established.",
                   {"source_binding": "Original BactoTraits row 8521 and all retained source "
                    "records remain unchanged. Maintained owner snapshots at " + KGM_COMMIT +
                    " identify the download pin and BacDive-to-NCBI join. Quarantine is a "
                    "proposed action, not an implemented or independently verified graph fix."}),
    ]


def make_review(packet_pin, proofs_pin, copied_pins, paper_spans, records,
                started, finished, ignored_check):
    review = base.review_document(packet_pin, proofs_pin, copied_pins, paper_spans,
                                  started, finished, ignored_check)
    review.update(
        review_id=finished.replace("-", "").replace(":", "") + "-fresh05-source-identity",
        title="Fresh-05 source identity investigation confirms incompatible culture accessions",
        summary="Primary catalog snapshots confirm that DSM 19353/JCM 14586 and DSM 18772 "
        "belong to distinct taxa. No safe source-field replacement, independently verified "
        "correction or resolved graph claim follows. Six newly authored categorical assessments "
        "remain conservative; the review is partial and excluded from independent calibration.",
        assessments=authored_assessments(),
        scope={"description": "One occurrence's source identity investigation after abstract replay.",
               "selection": "Fresh-05 retained original occurrence and source conflict #130.",
               "coverage": "partial", "population_size": 1,
               "reviewed_target_ids": [base.OCCURRENCE],
               "exclusions": [{"target": "Independent ten-case calibration scoring",
                               "reason": "Self-review with historical labels visible; no new rating."},
                              {"target": "Neighbor-row finding #132",
                               "reason": "Contextual follow-up only; not an additional reviewed target."},
                              {"target": "Other retained occurrences and remaining 9900",
                               "reason": "No review expansion or population inference."}]},
        tags=["source-identity-investigation", "partial-review", "excluded-from-calibration-scoring"])
    review["reviewer"]["independence_basis"] = (
        "New authored source-identity judgments using retained source/abstract and current catalogs. "
        "Historical reviews and labels were visible; excluded from independent calibration matrices.")
    target = review["targets"][0]
    target.update(label="Fresh-05 source strain identity investigation", owner_paths=OWNER_PATHS,
                  ownership_note="Source publisher controls the BactoTraits table; maintained "
                  "KG-Microbe download/join paths are identified at " + KGM_COMMIT + ".")
    inputs = [item["path"] for item in review["source"]["inputs"]]
    review["source"] = base.inspect_source(
        ROOT, [target], [*inputs, CAPTURE_SCRIPT, THIS_SCRIPT, PREVIOUS_PATH])["source"]
    for name, record in records.items():
        expected, span = AUTHORITY_PINS[name], record["span"]
        text_pin = next(pin for pin in copied_pins if pin["path"].endswith("/" + name + ".txt"))
        review["evidence"].append({
            "evidence_id": "catalog-" + name, "kind": "authority", "support": "context_only",
            "reference": capture.URLS[name],
            "accessed_at": canonical_utc_timestamp(record["receipt"]["fetched_at"]),
            "quote": expected["quote"], "snapshot_sha256": text_pin["sha256"],
            "locator": f"catalog identity; chars {span['start']}:{span['end']}; "
                       f"text_sha256={span['text_sha256']}", "summary": expected["summary"]})
    review["checks"].append({
        "check_id": "catalog-identity-replay", "name": "Captured catalog identity provenance",
        "status": "passed", "required": True, "target_ids": [base.OCCURRENCE],
        "evidence_ids": AUTHORITY_IDS,
        "summary": "All four raw HTML/text/receipt hashes and the capture helper hash matched; "
        "the deterministic text derivative and bounded quotes replayed. Culture identities "
        "were independently disambiguated before authoring this review."})
    review["checks"].append({
        "check_id": "maintained-owner-snapshots", "name": "Maintained download and transform snapshots",
        "status": "passed", "required": True, "target_ids": [base.OCCURRENCE],
        "summary": "Nonempty download.yaml and BactoTraits transform bytes were read from the "
        "Git object at " + KGM_COMMIT + " and retained as pinned inputs. This is owner tracing, "
        "not a source patch or regeneration check."})
    check = next(check for check in review["checks"] if check["check_id"] == "source-identity-resolution")
    check.update(name="Verified source-row correction", evidence_ids=SOURCE_IDS,
                 summary="Catalog identities are disambiguated, but no safe field replacement "
                 "or implemented source-row quarantine has been independently verified on "
                 "regenerated candidate bytes. The original graph claim remains unresolved.")
    finding = review["findings"][0]
    finding.update(
        description="BactoTraits row 8521 names Rubritalea squalenifaciens/BacDive 17851 but "
        "lists DSM 19353/JCM 14586. Captured DSMZ/JCM authorities place that collection pair "
        "in Thioprofundum lithotrophicum strain 106/BacDive 17847/NCBI 571898. DSMZ and current "
        "BacDive 17851 instead bind the nominal Rubritalea to DSM 18772/HOact23/MBIC08254/"
        "NBRC103619. The incompatible identity fields are confirmed; the intended ownership "
        "of all source traits and a safe replacement remain unresolved.",
        evidence_ids=[*SOURCE_IDS, *base.PAPER_IDS], owner_paths=OWNER_PATHS,
        ownership_note="Source publisher owns table correction; KG-Microbe owns download/join "
        "and any reviewed row-quarantine policy at the listed maintained paths.",
        previous_occurrences=[{"repository": "CultureBotAI/EdgeMech", "review_id": PREVIOUS_ID,
                               "finding_id": "source-accession-conflict"}])
    action = review["actions"][0]
    action.update(
        action_id="quarantine-and-verify-source-identity",
        description="Propose a complete-reviewed-row-hash-bound quarantine at the maintained "
        "BactoTraits transform; do not silently substitute accession or taxon fields. Establish "
        "the intended source identity with the table owner, preserve the before/after proposal "
        "and independently verify regenerated candidate occurrences before claiming correction.",
        owner_paths=OWNER_PATHS,
        ownership_note="The maintained owner paths are known; no correction or quarantine is "
        "claimed merged by this investigation.",
        acceptance_checks=["Retain original row hash, occurrence and all conflicting fields.",
                           "Quarantine acceptance is keyed by the complete reviewed row hash and "
                           "exact row identity; retain whole-source-file hash as receipt provenance, "
                           "not as a requirement to reject an otherwise unchanged reviewed row.",
                           "Do not replace graph subject 1123071 with 571898 from accessions alone.",
                           "Add a regression against mixed-strain joins without altering unrelated rows.",
                           "Independently verify candidate regeneration and affected occurrences."])
    review["limitations"] = [
        "Partial self-review; not an independent calibration rating, agreement result or gold label.",
        "Complete catalog pages and the retained abstract were inspected; no full scientific paper.",
        "Four catalog snapshots resolve competing aliases, not all original statement/model semantics.",
        "The confirmed source conflict does not establish biological refutation or a safe field repair.",
        "Neighbor investigation #132 is context only and contributes no new reviewed occurrence here.",
        "Investigation used 3 successful CBORG Tavily calls and 4 anonymous catalog GETs; no "
        "Valency, publisher TDM or licensed-library full text. This replay launcher makes zero requests.",
        "Original source bytes/reviews remain intact; no source patch, native capability or graph admission.",
        "Private catalog/source bodies remain ignored; canonical review contains bounded snippets and hashes."]
    review["links"] = [base.SOURCE_CONFLICT_ISSUE,
                       "https://github.com/CultureBotAI/EdgeMech/issues/132",
                       "https://doi.org/" + base.DOI,
                       *["https://github.com/Knowledge-Graph-Hub/kg-microbe/blob/" + KGM_COMMIT +
                         "/" + owner["path"] for owner in OWNER_PATHS]]
    return review


def run(staging):
    started = base.utc_now()
    raws, occurrence, source, paper_raw, paper_spans = base.load_inputs(base.RETAINED, base.PAPER)
    records, service_raws, owners = load_authorities()
    base.check_contracts()
    relative, stage, command, exit_code = base.destination(staging)
    stage.mkdir(mode=0o700)
    for name in ("occurrence.json", "source.json"):
        base.write_new(stage / name, raws[name])
    base.write_new(stage / "prepared-packet.json", raws["packet.json"])
    base.write_new(stage / "abstract.json", paper_raw)
    copied_pins = [base.pin(stage / name) for name in
                   ("occurrence.json", "source.json", "prepared-packet.json", "abstract.json")]
    for name, record in records.items():
        for kind, suffix in (("raw", ".html"), ("text", ".txt"), ("receipt", ".json")):
            base.write_new(stage / (name + suffix), record["raws"][kind])
            copied_pins.append(base.pin(stage / (name + suffix)))
    for name, raw in service_raws.items():
        base.write_new(stage / name, raw)
        copied_pins.append(base.pin(stage / name))
    for owner_path, raw in owners.items():
        name = "kg-microbe-" + Path(owner_path).name
        base.write_new(stage / name, raw)
        copied_pins.append(base.pin(stage / name))
    packet = base.build_packet(occurrence, source, occurrence_input=copied_pins[0],
                               source_input=copied_pins[1], root=ROOT)
    base.write_json(stage / "packet.json", packet)
    base.validate_packet(json.loads(base.read_bytes(stage, "packet.json")), root=ROOT)
    packet_pin, paper_pin = base.pin(stage / "packet.json"), base.pin(stage / "abstract.json")
    proofs = [{"evidence_id": "packet-source", "kind": "packet", "input": packet_pin,
               "reference": packet_pin["path"], "support": "context_only", "scope": "exact",
               "scope_rationale": "Original occurrence and complete source context unchanged; "
               "the source identity conflict is not an independent biological proof.",
               "inspected_extent": "Original occurrence/endpoints and all four retained source records.",
               "axes": ["source_fidelity", "relation", "subject_node", "object_node"]}]
    for eid, span in paper_spans.items():
        proofs.append({**base.paper_identity(), "evidence_id": eid, "input": paper_pin,
                       "support": "partial", "scope": "partial",
                       "scope_rationale": "Nominal DSM 18772 nonmotility evidence does not settle "
                       "the mixed source identity or complete graph model.",
                       "axes": ["claim", "literature"],
                       **{key: span[key] for key in ("text_sha256", "start", "end", "extractor")}})
    for name, record in records.items():
        receipt, span = record["receipt"], record["span"]
        proofs.append({"evidence_id": "catalog-" + name, "kind": "authority",
                       "input": base.pin(stage / (name + ".txt")), "reference": capture.URLS[name],
                       "version": receipt["fetched_at"] + "; raw_sha256=" + receipt["raw_sha256"],
                       "support": "context_only", "scope": "context",
                       "scope_rationale": "Verified independent culture-accession identity context; "
                       "not a full resolution of the original source join or node model.",
                       "inspected_extent": "Complete captured catalog identity and sequence sections; "
                       "raw HTML, receipt and deterministic text derivative verified.",
                       "axes": ["subject_node", "source_fidelity"],
                       **{key: span[key] for key in ("text_sha256", "start", "end", "extractor")}})
    base.write_json(stage / "proofs.json", {"profile": base.PROFILE,
                                           "occurrence_id": base.OCCURRENCE, "proofs": proofs})
    proofs_pin = base.pin(stage / "proofs.json")
    finished = base.utc_now()
    review = make_review(packet_pin, proofs_pin, copied_pins, paper_spans, records,
                         started, finished, (command, exit_code))
    base.write_json(stage / "authored-review.json", review)
    base.validate_occurrence_review(ROOT, review, packet_pin["path"], proofs_pin["path"])
    result = base.save_occurrence_review(ROOT, review, packet_pin["path"], proofs_pin["path"])
    receipt = {**result, "staging": str(relative), "provider_calls": 0,
               "historical_investigation_channels": {"cborg_tavily": 3, "anonymous_catalog_gets": 4,
                                                       "publisher_tdm": 0},
               "calibration_rating": False, "calibration_pass": False, "review_completion": "partial",
               "previous_review": PREVIOUS_ID, "maintained_owner_commit": KGM_COMMIT,
               "packet": packet_pin, "proofs": proofs_pin,
               "paper_quotation_words": sum(len(q.split()) for q in base.QUOTES.values()),
               "authority_quotation_words": {name: len(item["quote"].split())
                                               for name, item in AUTHORITY_PINS.items()}}
    base.write_json(stage / "receipt.json", receipt)
    base.require(json.loads(base.read_bytes(stage, "receipt.json")) == receipt,
                 "Persisted review receipt differs")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--plan", action="store_true")
    modes.add_argument("--run", action="store_true")
    parser.add_argument("--staging", default=".temp/identity130-review-20261115")
    args = parser.parse_args()
    if args.plan:
        base.load_inputs(base.RETAINED, base.PAPER)
        load_authorities()
        base.check_contracts()
        base.destination(args.staging)
        result = {"action": "plan", "writes": 0, "provider_calls": 0,
                  "staging": args.staging, "occurrence_id": base.OCCURRENCE,
                  "assessments": base.AXES, "completion": "partial", "calibration_rating": False,
                  "authority_count": len(AUTHORITY_PINS), "maintained_owner_commit": KGM_COMMIT}
    else:
        result = run(args.staging)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
