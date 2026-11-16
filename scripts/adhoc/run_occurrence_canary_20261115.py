#!/usr/bin/env python3
"""2026-11-15: replay one retained edge through the occurrence review profile (#105).

Inputs: exact retained edge47 packet and primary JATS article, pinned below.
Outputs: new private .temp packet/proofs/receipt and canonical immutable review pair.
This launcher authors only the explicitly declared edge47 judgments below; it does
not classify other occurrences, fetch evidence, correct graph bytes or grant admission.
Use --plan first. The live path uses exclusive writes and verifies persisted bytes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from kg_microbe_governance.artifacts.scripts.record_review import (  # noqa: E402
    inspect_source,
    read_bytes,
)

from edgemech.literature_cache import LiteratureCache, full_text, verify_quote  # noqa: E402
from edgemech.occurrence_packet import build_packet, validate_packet  # noqa: E402
from edgemech.occurrence_review import (  # noqa: E402
    CATEGORIES,
    PROFILE,
    save_occurrence_review,
    validate_occurrence_review,
)
from edgemech.pins import check_contracts  # noqa: E402

OCCURRENCE = (
    "urn:kg-microbe:occurrence:v1:"
    "358f925d6342994dbe5598a3d3d2cdfafe3ad30028b7305c3cf21242cf3a9b57"
)
SOURCE = Path(
    "/Users/marcin/agent-work/EdgeMech/edge-sample-review-20261112-data/"
    "phase2/source/packets/47.json"
)
SOURCE_SHA = "0b5f705f26bbec14781575580bf10b508af15bf2358c0912c5d820966c175e5e"
PAPER = Path(
    "/Users/marcin/agent-work/EdgeMech/retained-pr107-20261115/.temp/fulltext/"
    "salt-evidence-47-20261115/primary2024/20261115T081148Z-46a97b9852af/europepmc.xml"
)
PAPER_SHA = "df87ed3eabcefee07f32f61c7b909e616dd072b1cd7ee7dafff42f5872345838"
DOI = "10.3390/ani14101394"
PMCID = "PMC11117391"
TITLE = (
    "Genotypic and Phenotypic Characteristics of Lactic Acid Bacteria Associated with "
    "Forage Plants in the Native Grassland of Western Inner Mongolia and Their "
    "Application for Alfalfa Silage Fermentation"
)
QUOTE = "Salt tolerance was observed in the MRS broth containing 3.0% and 6.5% of NaCl"
PREVIOUS = "20261115T081452Z-edge47-salt-source-and-paper"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def checked_input(path, expected):
    path = path.absolute()
    raw = read_bytes(path.parent, path.name)
    if digest(raw) != expected:
        raise ValueError(f"Retained evidence hash mismatch: {path}")
    return raw


def write_new(path, raw):
    with path.open("xb") as stream:
        stream.write(raw)
    if path.read_bytes() != raw:
        raise ValueError(f"Persisted bytes differ: {path}")


def write_json(path, document):
    write_new(path, (json.dumps(document, indent=2, ensure_ascii=False) + "\n").encode())


def pin(root, path):
    return {"path": str(path.relative_to(root)), "sha256": digest(path.read_bytes())}


def load_inputs(source, paper):
    source_raw, paper_raw = checked_input(source, SOURCE_SHA), checked_input(paper, PAPER_SHA)
    packet = json.loads(source_raw)
    if packet["edge"]["occurrence_id"] != OCCURRENCE:
        raise ValueError("Canary source occurrence differs")
    article = ET.fromstring(paper_raw)
    meta = article.find("./front/article-meta")
    if meta is None or article.find("./body") is None:
        raise ValueError("Primary article metadata and full body required")
    identifiers = {node.get("pub-id-type"): "".join(node.itertext()).strip()
                   for node in meta.findall("article-id")}
    title_node = meta.find("./title-group/article-title")
    title = " ".join("".join(title_node.itertext()).split()) if title_node is not None else ""
    if (identifiers.get("doi") != DOI or identifiers.get("pmcid") != PMCID
            or identifiers.get("pmid") != "38791612" or title != TITLE):
        raise ValueError("Primary article identity differs")
    text = full_text(paper_raw, PMCID)
    document = LiteratureCache._document({"response_sha256": PAPER_SHA}, "oa_fulltext", text)
    proof = verify_quote(document, QUOTE)
    if len(QUOTE.split()) > 25:
        raise ValueError("Canary quotation exceeds its word bound")
    return source_raw, paper_raw, packet, proof


def assessment(axis, category, area, summary, details, evidence_ids):
    dimensions = {"axis": axis, "category": category,
                  "scope": "Exact original edge47 occurrence; no replacement assertion", **details}
    return {
        "assessment_id": axis.replace("_", "-"), "area": area,
        "topic": "Occurrence " + axis.replace("_", " "),
        "outcome": CATEGORIES[axis][category], "summary": summary,
        "target_ids": [OCCURRENCE], "evidence_ids": evidence_ids,
        "dimensions": [{"name": name, "value": value,
                        "definition": "Explicit edge47 reviewer judgment: " + name,
                        "evidence_ids": evidence_ids} for name, value in dimensions.items()],
    }


def authored_assessments():
    return [
        assessment("claim", "NOT_ASSESSABLE", "grounding",
                   "The original edge connects a species to an explicitly reported source-value "
                   "attribute. Its description excludes a decoded phenotype or an assertion about "
                   "every taxon member. A biological truth judgment is blocked by unresolved modeled "
                   "meaning and assay scope; this review does not replace it with a species-wide "
                   "0-10% growth assertion. Exact copying is assessed under source fidelity.",
                   {"assertion_scope": "Original lpsn:783091 --biolink:has_attribute--> retained "
                    "source attribute for literal 0-10. The recovered BacDive observation is "
                    "strain-specific NaCl positive growth, percent basis and assay conditions "
                    "unspecified; GI38 is not the original strain."}, ["paper-methods"]),
        assessment("literature", "PARTIAL", "evidence",
                   "The inspected 2024 primary article describes an assay at 3.0% and 6.5% NaCl "
                   "and identifies GI38 as W. halotolerans. The quoted Methods text is partial "
                   "organism-matched context, not verification of DSM 20190/CIP 103005's full range.",
                   {"search_scope": "Replay only of the retained complete JATS article, including "
                    "primary identifiers, Methods 2.3 and Results 3.3; no new search or retrieval. "
                    "Original 1983/1993 article bodies are not inspected in this run. The figure "
                    "interpretation in the prior review is not represented as a new quote proof."},
                   ["paper-methods"]),
        assessment("relation", "UNRESOLVED", "representation",
                   "The frozen predicate and relation are retained. A versioned authority check "
                   "of their formal and semantic fitness has not been completed.",
                   {"direction": "Retained subject-to-source-attribute direction; semantic fit unresolved.",
                    "domain_range": "No pinned Biolink or SIO definition was inspected in this run.",
                    "specificity": "has_attribute describes the reported value; appropriateness "
                    "for a strain observation remains unresolved.",
                    "qualifiers": "The recovered strain, unit, substance, polarity and unknown "
                    "assay scope are presentation context, not new graph qualifiers."}, ["packet-source"]),
        assessment("subject_node", "UNRESOLVED", "identity",
                   "The frozen LPSN endpoint and source-strain evidence are retained. Node identity "
                   "and category evidence must be assessed under versioned authorities before a "
                   "categorical correctness verdict; discordant NCBI fields remain excluded.",
                   {"identity": "lpsn:783091 names Weissella halotolerans; source record uses "
                    "BacDive 6845. Do not substitute discordant CSV NCBI 219301.",
                    "label": "Retained original label Weissella halotolerans.",
                    "category_fit": "biolink:OrganismTaxon is retained, not independently certified.",
                    "rank_or_type": "LPSN record describes species; BacDive measurement concerns "
                    "a type strain. Their scopes remain distinct.",
                    "definition": "Original node description and complete LPSN record are preserved "
                    "in the packet; no new species-wide phenotype is asserted.",
                    "authority_version": "Retained LPSN record declares version 1; formal "
                    "Biolink category validation is unavailable in this run."}, ["packet-source"]),
        assessment("object_node", "UNRESOLVED", "representation",
                   "The original hash attribute denotes a source-field value. A categorical "
                   "modeling judgment awaits a versioned category and observation-model review.",
                   {"identity": "Exact original source-attribute identifier is preserved in the packet.",
                    "label": "Retained label: reported Salt concentration: 0-10 (source value).",
                    "category_fit": "biolink:Attribute is retained; a populated category is not proof "
                    "of appropriate modeling.",
                    "rank_or_type": "Reported source attribute, not a decoded phenotype or chemical entity.",
                    "definition": "Original description explicitly excludes a claim that every "
                    "taxon member has the trait; concentration, percent basis and assay remain separate.",
                    "authority_version": "No pinned Biolink Attribute definition was inspected; "
                    "the frozen source-node description is contextual evidence only."}, ["packet-source"]),
        assessment("source_fidelity", "SUPPORTED", "provenance",
                   "The exact frozen CSV row reports 0-10 and percent, and the matching BacDive "
                   "observation reports NaCl, positive growth and reference 119830. This supports "
                   "the reported-value interpretation, without independently establishing biology.",
                   {"source_binding": "Exact occurrence and original endpoints; CSV record 20904 "
                    "LPSN 783091 to BacDive 6845, literal concentration/unit to halophily @ref "
                    "119830. CIP catalogue reference retained; percent basis and assay conditions "
                    "stay unknown. No join by species name alone."}, ["packet-source"]),
    ]


def review_document(root, packet_pin, proofs_pin, source_pin, paper_pin, quote, started, finished):
    target = {"target_id": OCCURRENCE, "path": packet_pin["path"],
              "selector": "occurrence_id=" + OCCURRENCE,
              "label": "Edge47 reported salt source value with categorical assessment axes",
              "record_class": "ReleaseOccurrence", "kind": "snapshot_row",
              "ownership_note": "Frozen occurrence and evidence remain immutable. Presentation "
              "belongs to EdgeMech; any scientific correction requires the maintained upstream owner."}
    inputs = [proofs_pin["path"], source_pin["path"], paper_pin["path"],
              "src/edgemech/occurrence_review.py", "src/edgemech/occurrence_packet.py",
              "src/edgemech/literature_cache.py", "src/edgemech/contract-pins.json",
              "schema/record_review.yaml", "scripts/adhoc/run_occurrence_canary_20261115.py",
              f"reviews/structured/{PREVIOUS}/review.yaml"]
    inspected = inspect_source(root, [target], inputs)
    finding = {"repository": "CultureBotAI/EdgeMech", "review_id": PREVIOUS}
    return {
        "schema_version": "1.0.0",
        "review_id": finished.replace("-", "").replace(":", "") + "-edge47-occurrence-profile",
        "kind": "record", "repository": "CultureBotAI/EdgeMech",
        "title": "Edge47 categorical occurrence profile canary using retained evidence",
        "started_at": started, "finished_at": finished,
        "reviewer": {"identity": "Codex agent", "kind": "agent", "independence": "self_review",
                     "independence_basis": "The agent authored this bounded launcher and its "
                     "declared judgments. Replay validates provenance, not independent scientific agreement."},
        "skill": PROFILE, "completion": "completed", "verdict": "needs_curation",
        "scientific_review": True,
        "summary": "One retained occurrence has six explicit categorical assessments, complete "
        "source measurement context and one replayed DOI-bound partial literature quote. Claim "
        "meaning and relation/node modeling remain unresolved. No graph correction or admission.",
        "source": inspected["source"],
        "scope": {"description": "One retained edge47 occurrence and both original endpoint records.",
                  "selection": "Previously selected context/partial-evidence canary; no new sampling.",
                  "coverage": "full", "population_size": 1, "reviewed_target_ids": [OCCURRENCE],
                  "exclusions": [{"target": "Other 99 retained canaries and remaining 9,900 occurrences",
                                  "reason": "No calibration or batch expansion in this execution."}]},
        "targets": [target],
        "checks": [
            {"check_id": "input-packet-replay", "name": "Pinned source and endpoint packet replay",
             "status": "passed", "required": True, "target_ids": [OCCURRENCE],
             "summary": "Fixed input SHA-256 checks and build_packet/validate_packet succeeded; "
             "newly persisted packet bytes were read back and matched.", "evidence_ids": ["packet-source"]},
            {"check_id": "paper-quote-replay", "name": "Primary JATS identity and literal quote replay",
             "status": "passed", "required": True, "target_ids": [OCCURRENCE],
             "summary": "Raw JATS hash, DOI/PMCID/PMID/title and exact quote offsets verified "
             "with the retained full-text extractor; this does not establish entailment.",
             "evidence_ids": ["paper-methods"]},
            {"check_id": "pinned-contracts", "name": "Installed CLAW contract byte verification",
             "status": "passed", "required": True, "target_ids": [OCCURRENCE],
             "summary": "check_contracts completed before review construction."},
            {"check_id": "modeling-authorities", "name": "Versioned relation and node authority assessment",
             "status": "unavailable", "required": False, "target_ids": [OCCURRENCE],
             "summary": "No pinned Biolink/SIO authority proof in this canary; all three modeling "
             "axes explicitly remain unresolved. This check is required for their resolution."}],
        "evidence": [
            {"evidence_id": "packet-source", "kind": "record_content",
             "reference": packet_pin["path"], "locator": "original_assertion; endpoints; "
             "measurement_context; source_records with exact retained selectors and hashes",
             "accessed_at": started, "support": "supports", "snapshot_sha256": packet_pin["sha256"],
             "summary": "Exact source-value binding and original node records; source-report "
             "support is not independent claim or category correctness."},
            {"evidence_id": "paper-methods", "kind": "primary_source",
             "reference": "https://doi.org/" + DOI,
             "locator": f"{PMCID}; Methods 2.3 sec2dot3-animals-14-01394; "
             f"chars {quote['start']}:{quote['end']}; text_sha256={quote['text_sha256']}",
             "accessed_at": started, "support": "partial", "quote": QUOTE,
             "snapshot_sha256": PAPER_SHA,
             "summary": "Methods describe two tested concentrations. The article's GI38 isolate "
             "is not shown equivalent to the source strain; no complete 0-10% range is established."}],
        "assessments": authored_assessments(),
        "findings": [
            {"finding_id": "quantity-context", "issue_key": "edge47-joint-measurement-context",
             "category": "representation", "severity": "minor", "status": "open",
             "certainty": "confirmed", "title": "Complete source context needs verified integration",
             "description": "This candidate packet assembles the previously omitted measurement "
             "context. Independent acceptance and integration review remain pending; the historical "
             "graph and review bytes are unchanged.", "target_ids": [OCCURRENCE],
             "field_paths": ["measurement_context"], "evidence_ids": ["packet-source"],
             "owner_paths": [{"repository": "CultureBotAI/EdgeMech",
                              "path": "src/edgemech/occurrence_packet.py",
                              "role": "Source-aware review packet assembly"}],
             "previous_occurrences": [{**finding, "finding_id": "quantity-context"}],
             "external_issues": ["https://github.com/CultureBotAI/EdgeMech/issues/105"]},
            {"finding_id": "discordant-crosswalk",
             "issue_key": "microbedecoder-record20904-ncbi-crosswalk", "category": "identity",
             "severity": "major", "status": "deferred", "certainty": "confirmed",
             "title": "Excluded NCBI crosswalk still needs maintained-owner reconciliation",
             "description": "The retained source row includes the unrelated NCBI identity "
             "Brachybacterium muris/219301. The packet binds the measurement by LPSN/BacDive "
             "identifiers and does not adopt that crosswalk.", "target_ids": [OCCURRENCE],
             "field_paths": ["NCBI_Genus", "NCBI_Species", "NCBI_Taxonomy_ID"],
             "evidence_ids": ["packet-source"],
             "ownership_note": "Upstream MicrobeDecoder/KG-Microbe join owner; exact owner "
             "and current remediation require separate investigation.",
             "disposition_reason": "This canary preserves the exclusion and existing issue; "
             "it does not establish an upstream correction.",
             "previous_occurrences": [{**finding, "finding_id": "discordant-crosswalk"}],
             "external_issues": ["https://github.com/CultureBotAI/EdgeMech/issues/106"]}],
        "actions": [
            {"action_id": "verify-context-integration", "finding_ids": ["quantity-context"],
             "target_ids": [OCCURRENCE], "description": "Independently review and integrate "
             "the candidate context presentation before resolving issue 105.",
             "owner_paths": [{"repository": "CultureBotAI/EdgeMech",
                              "path": "src/edgemech/occurrence_packet.py",
                              "role": "Maintained packet adapter"}],
             "acceptance_checks": ["NaCl, 0-10, %, growth, positive, strain and reference appear "
                                   "together from exact source bindings.",
                                   "Reject mismatched source, strain, unit and reference records.",
                                   "Unknown percent basis and assay conditions remain unknown."]},
            {"action_id": "retain-crosswalk-exclusion", "finding_ids": ["discordant-crosswalk"],
             "target_ids": [OCCURRENCE], "description": "Retain the NCBI exclusion pending "
             "independent upstream reconciliation of exact row 20904.",
             "ownership_note": "Upstream join-owner triage is tracked in issue 106.",
             "acceptance_checks": ["Any proposed replacement has exact source provenance and "
                                   "independent identity verification; regenerated candidate "
                                   "bytes are checked before graph correction is claimed."]}],
        "limitations": [
            "Self-review canary; no independent scientific agreement or reviewer calibration.",
            "The exact original statement is a reported attribute, not an independently verified "
            "biological range. No fabricated species-wide interpretation replaces it.",
            "Partial GI38 paper evidence does not establish the original source strain's entire "
            "0-10% range, percentage basis or assay conditions.",
            "Relation, subject-node and object-node judgments remain unresolved pending "
            "versioned authority assessment; no graph correction or native admission occurred.",
            "Retained evidence only, with zero provider calls. Figure conclusions from the "
            "previous review are not represented as newly replayed figure proofs.",
            "Private source and full-text bytes remain under ignored .temp; public outputs "
            "contain one bounded quotation and identifiers, hashes and locators."],
        "related_reviews": [{"repository": "CultureBotAI/EdgeMech", "review_id": PREVIOUS,
                             "relationship": "Adds categorical axes while preserving the prior "
                             "source and partial-literature scope and unresolved findings."}],
        "links": ["https://github.com/CultureBotAI/EdgeMech/issues/105",
                  "https://github.com/CultureBotAI/EdgeMech/issues/106", "https://doi.org/" + DOI],
        "tags": ["bounded-canary", "categorical-assessment", "source-provenance"],
    }


def run(root, source, paper, staging):
    started = utc_now()
    source_raw, paper_raw, original, quote = load_inputs(source, paper)
    check_contracts()
    relative = Path(staging)
    if relative.is_absolute() or len(relative.parts) != 2 or relative.parts[0] != ".temp":
        raise ValueError("Staging must name a fresh directory directly below repository .temp")
    ignored = subprocess.run(["git", "-C", str(root), "check-ignore", "--no-index", "--quiet",
                              str(relative / "source47.json")], check=False)
    if ignored.returncode != 0:
        raise ValueError("Private canary staging must be gitignored")
    temporary = root / ".temp"
    if temporary.is_symlink():
        raise ValueError("Private staging parent cannot be a symlink")
    temporary.mkdir(exist_ok=True)
    stage = root / relative
    stage.mkdir(mode=0o700)
    source_path, paper_path = stage / "source47.json", stage / "primary2024.xml"
    write_new(source_path, source_raw)
    write_new(paper_path, paper_raw)
    source_pin, paper_pin = pin(root, source_path), pin(root, paper_path)
    packet = build_packet(original["edge"], original, occurrence_input=source_pin,
                          source_input=source_pin, root=root)
    packet_path, proofs_path = stage / "packet.json", stage / "proofs.json"
    write_json(packet_path, packet)
    validate_packet(json.loads(packet_path.read_bytes()), root=root)
    packet_pin = pin(root, packet_path)
    proofs = {"profile": PROFILE, "occurrence_id": OCCURRENCE, "proofs": [
        {"evidence_id": "packet-source", "kind": "packet", "input": packet_pin,
         "reference": packet_pin["path"], "support": "supports", "scope": "exact",
         "scope_rationale": "Exact original source-value occurrence and retained endpoints; "
         "not independent biology or node-category validation.",
         "inspected_extent": "Original source packet, both endpoint records, CSV20904, "
         "BacDive6845 halophily/reference and retained LPSN identity record.",
         "axes": ["source_fidelity", "relation", "subject_node", "object_node"]},
        {"evidence_id": "paper-methods", "kind": "jats", "input": paper_pin,
         "reference": "https://doi.org/" + DOI, "support": "partial", "scope": "partial",
         "scope_rationale": "Paper assay for distinct isolate GI38; the original source strain "
         "and full reported range are not independently tested by this quotation.",
         "inspected_extent": "Primary JATS identifiers/title, Methods2.3, Results3.3; "
         "complete body retained. No new image proof in this execution.",
         "axes": ["claim", "literature"], "title": TITLE, "doi": DOI, "pmcid": PMCID,
         **{key: quote[key] for key in ("text_sha256", "start", "end", "extractor")}}]}
    write_json(proofs_path, proofs)
    finished = utc_now()
    review = review_document(root, packet_pin, pin(root, proofs_path), source_pin,
                             paper_pin, quote, started, finished)
    write_json(stage / "authored-review.json", review)
    validate_occurrence_review(root, review, packet_pin["path"], str(proofs_path.relative_to(root)))
    result = save_occurrence_review(root, review, packet_pin["path"],
                                    str(proofs_path.relative_to(root)))
    receipt = {**result, "provider_calls": 0, "staging": str(relative),
               "source_packet_sha256": SOURCE_SHA, "primary_jats_sha256": PAPER_SHA,
               "packet": packet_pin, "proofs": pin(root, proofs_path)}
    receipt_path = stage / "receipt.json"
    write_json(receipt_path, receipt)
    if json.loads(receipt_path.read_bytes()) != receipt:
        raise ValueError("Persisted canary receipt differs")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--source-packet", type=Path, default=SOURCE)
    parser.add_argument("--paper", type=Path, default=PAPER)
    parser.add_argument("--staging", default=".temp/occurrence-canary-edge47-20261115")
    parser.add_argument("--plan", action="store_true", help="Verify retained inputs; write nothing")
    args = parser.parse_args()
    root = args.root.absolute()
    if args.plan:
        load_inputs(args.source_packet, args.paper)
        result = {"action": "plan", "writes": 0, "provider_calls": 0,
                  "occurrence_id": OCCURRENCE, "staging": args.staging,
                  "source_packet_sha256": SOURCE_SHA, "primary_jats_sha256": PAPER_SHA,
                  "axes": {axis: category for axis, category in (
                      ("claim", "NOT_ASSESSABLE"), ("literature", "PARTIAL"),
                      ("relation", "UNRESOLVED"), ("subject_node", "UNRESOLVED"),
                      ("object_node", "UNRESOLVED"), ("source_fidelity", "SUPPORTED"))}}
    else:
        result = run(root, args.source_packet, args.paper, args.staging)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
