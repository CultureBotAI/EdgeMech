#!/usr/bin/env python3
"""2026-11-15: replay one retained primary abstract for EdgeMech issue #127.

Inputs: pinned fresh-05 occurrence/source/prepared packet and Europe PMC core JSON.
Outputs: exclusive private inputs/proofs/receipt and one canonical partial review.
This authored adapter canary records the source conflict in #130; it is excluded
from the independent ten-case calibration matrices. No requests, corrections or
graph admissions occur. Run --plan before the single explicit --run invocation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import stat
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).absolute().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "src"))

from kg_microbe_governance.artifacts.scripts.record_review import (  # noqa: E402
    inspect_source,
    read_bytes,
)

from edgemech.literature_cache import LiteratureCache, verify_quote  # noqa: E402
from edgemech.occurrence_packet import build_packet, validate_packet  # noqa: E402
from edgemech.occurrence_review import (  # noqa: E402
    CATEGORIES,
    PROFILE,
    _europepmc_abstract,
    save_occurrence_review,
    validate_occurrence_review,
)
from edgemech.pins import check_contracts  # noqa: E402
from edgemech.storage.parquet import safe_path  # noqa: E402

OCCURRENCE = (
    "urn:kg-microbe:occurrence:v1:"
    "1e9dec218a07f7e480add8ff273e3a9285f79d57746ca74041702839207a8136"
)
RETAINED = Path(
    "/Users/marcin/Documents/VIMSS/ontology/Mechs/EdgeMech/.temp/"
    "edge-calibration-20261115/fresh-05"
)
RETAINED_PINS = {
    "occurrence.json": "7b537e0809c90529f7663866359bace6b7d9bd5c7547c74cf4faf88268430426",
    "source.json": "9ff02c936f66ec58ad26b25f6176cf96d1f2f92bb556b6c4e7c971995a42f8e7",
    "packet.json": "9a456958680990e4d6742b2bc012579d6e48d5d2adefdfcd24c6f0b6ab56b34b",
}
COHORT = "artifacts/edge-calibration-20261115/cohort.json"
COHORT_SHA = "1dc756b0ba628756baf544cacf36f0a1ab2e4c68eed6724ee281205f22d606ee"
PAPER = Path(
    "/Users/marcin/agent-work/EdgeMech/edge-sample-review-20261112-data/phase2/literature/"
    "cache/82d96c9481a6d11eefc5976e65b2863e10bed3cedf8b02f9b09cdb92802cf807.response"
)
PAPER_SHA = "82d96c9481a6d11eefc5976e65b2863e10bed3cedf8b02f9b09cdb92802cf807"
DOI, PMID = "10.1099/ijs.0.65010-0", "17625207"
TITLE = (
    "Rubritalea squalenifaciens sp. nov., a squalene-producing marine bacterium "
    "belonging to subdivision 1 of the phylum 'Verrucomicrobia'."
)
QUOTES = {
    "abstract-nonmotility": (
        "The strain, designated HOact23(T), was a non-motile, "
        "rod-shaped (0.44-0.53x0.65-0.79 microm) bacterium."
    ),
    "abstract-strain": "type strain HOact23(T) (=MBIC08254(T)=DSM 18772(T))",
}
SOURCE_CONFLICT_ISSUE = "https://github.com/CultureBotAI/EdgeMech/issues/130"
PAPER_IDS = list(QUOTES)
AXES = {
    "claim": "NOT_ASSESSABLE", "literature": "PARTIAL", "relation": "UNRESOLVED",
    "subject_node": "UNRESOLVED", "object_node": "UNRESOLVED",
    "source_fidelity": "NOT_ASSESSABLE",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def checked_input(path, expected):
    path = safe_path(path.absolute())
    raw = read_bytes(path.parent, path.name)
    require(digest(raw) == expected, f"Retained input hash mismatch: {path}")
    return raw


def pin(path):
    path = safe_path(path)
    return {"path": str(path.relative_to(ROOT)), "sha256": digest(path.read_bytes())}


def write_new(path, raw):
    safe_path(path, exists=False)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    require(read_bytes(path.parent, path.name) == raw, f"Persisted bytes differ: {path}")


def write_json(path, value):
    write_new(path, (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode())


def paper_identity():
    return {"kind": "europepmc_abstract", "doi": DOI, "pmid": PMID,
            "title": TITLE, "reference": "https://doi.org/" + DOI,
            "inspected_extent": "abstract"}


def load_inputs(retained, paper):
    raws = {name: checked_input(retained / name, expected)
            for name, expected in RETAINED_PINS.items()}
    occurrence, source, prepared = (json.loads(raws[name])
                                    for name in ("occurrence.json", "source.json", "packet.json"))
    cohort = json.loads(checked_input(ROOT / COHORT, COHORT_SHA))
    cases = [case for case in cohort["cases"] if case["case_id"] == "fresh-05"]
    require(len(cases) == 1 and cases[0]["occurrence_id"] == OCCURRENCE,
            "Frozen calibration selection differs")
    require(occurrence["occurrence_id"] == source["edge"]["occurrence_id"]
            == prepared["occurrence_id"] == OCCURRENCE, "Retained occurrence identity differs")
    require(prepared["original_occurrence"] == source["edge"], "Retained packet source differs")
    for role, name in (("occurrence", "occurrence.json"), ("source", "source.json")):
        require(prepared["inputs"][role] == {
            "path": ".temp/edge-calibration-20261115/fresh-05/" + name,
            "sha256": RETAINED_PINS[name]}, "Retained packet input pin differs")
    require(cases[0]["original_assertion"] == prepared["original_assertion"],
            "Prepared assertion differs from cohort binding")
    paper_raw = checked_input(paper, PAPER_SHA)
    text, identities = _europepmc_abstract(paper_raw, paper_identity())
    require({"doi:" + DOI, "pmid:" + PMID} <= identities, "Primary aliases were not verified")
    document = LiteratureCache._document({"response_sha256": PAPER_SHA}, "abstract", text)
    spans = {eid: verify_quote(document, quote) for eid, quote in QUOTES.items()}
    require(sum(len(quote.split()) for quote in set(QUOTES.values())) <= 25,
            "Canary quotes exceed the shared publication budget")
    return raws, occurrence, source, paper_raw, spans


def destination(staging):
    relative = Path(staging)
    require(not relative.is_absolute() and len(relative.parts) == 2
            and relative.parts[0] == ".temp" and ".." not in relative.parts,
            "Staging must name a fresh directory directly below repository .temp")
    path = safe_path(ROOT / relative, exists=False)
    command = ["git", "check-ignore", "--no-index", "--quiet", str(relative / "abstract.json")]
    ignored = subprocess.run(command, cwd=ROOT, check=False)
    require(ignored.returncode == 0, "Private staging must be gitignored")
    tracked = subprocess.run(["git", "ls-files", "--", str(relative)], cwd=ROOT,
                             capture_output=True, check=True)
    require(not tracked.stdout, "Private staging contains tracked files")
    require(not path.exists(), "Canary staging already exists; choose a new run directory")
    temporary = safe_path(ROOT / ".temp", exists=False)
    if temporary.exists():
        require(temporary.is_dir() and stat.S_IMODE(temporary.stat().st_mode) == 0o700,
                "Existing .temp must have private mode 0700")
    return relative, path, shlex.join(command), ignored.returncode


def assessment(axis, area, summary, details):
    evidence_ids = PAPER_IDS if axis in {"claim", "literature"} else ["packet-source"]
    dimensions = {"axis": axis, "category": AXES[axis],
                  "scope": "Original fresh-05 occurrence; partial adapter canary, not calibration rating",
                  **details}
    return {"assessment_id": axis.replace("_", "-"), "area": area,
            "topic": "Fresh-05 " + axis.replace("_", " "),
            "outcome": CATEGORIES[axis][AXES[axis]], "summary": summary,
            "target_ids": [OCCURRENCE], "evidence_ids": evidence_ids,
            "dimensions": [{"name": name, "value": value,
                            "definition": "Authored bounded canary judgment: " + name,
                            "evidence_ids": evidence_ids} for name, value in dimensions.items()]}


def authored_assessments():
    return [
        assessment("claim", "grounding",
                   "The abstract directly reports nonmotility for HOact23 and identifies it as "
                   "DSM 18772. The original identifier-bound assertion is not settled in this "
                   "canary: the source row has conflicting culture accessions and versioned "
                   "NCBI/METPO/relation checks are incomplete. This is not a biological refutation.",
                   {"assertion_scope": "NCBITaxon:1123071 biolink:has_phenotype METPO:1000703, "
                    "with original labels Rubritalea squalenifaciens DSM 18772 and non motile. "
                    "Do not replace the graph assertion with an accession-only claim."}),
        assessment("literature", "evidence",
                   "Two literal abstract snippets identify the nominal DSM 18772 strain and its "
                   "nonmotility. They partially address the original graph assertion; the source "
                   "accession conflict and graph-identifier/model correspondence are unresolved. "
                   "No full paper was inspected or claimed.",
                   {"search_scope": "Only the retained Europe PMC core response for DOI " + DOI +
                    "; its sole primary MED result, PMID, title, complete abstract and two exact "
                    "snippets were inspected. No new search, retrieval, citation-array inference "
                    "or exhaustive absence claim.",
                    "literature_channel": "europepmc_abstract_retained; zero provider calls",
                    "inspected_extent": "Complete retained abstract and primary metadata only; "
                    "no full text inspected.",
                    "primary_identity": "Exact primary title, DOI " + DOI + " and PMID " + PMID +
                    " verified together in the sole retained MED result."}),
        assessment("relation", "representation",
                   "The retained has_phenotype predicate and RO:0002200 relation require "
                   "versioned authority assessment; this abstract adapter does not certify them.",
                   {"direction": "Original taxon-to-phenotype direction retained; formal fit unresolved.",
                    "domain_range": "No independently pinned relation/domain/range proof authored here.",
                    "specificity": "Nonmotility is the nominal phenotype; graph predicate fitness "
                    "is not established by an abstract match.",
                    "qualifiers": "The abstract describes the named strain; assay details and "
                    "any universal-condition interpretation remain outside inspected text."}),
        assessment("subject_node", "identity",
                   "The original strain label and BacDive/LPSN context align with DSM 18772, "
                   "but the BactoTraits row also lists DSM 19353 and JCM 14586. No equivalence "
                   "for those conflicting accessions or independent NCBI authority was established.",
                   {"identity": "NCBITaxon:1123071 retained; BacDive 17851 names that strain ID, "
                    "while BactoTraits row 8521 carries conflicting collection codes.",
                    "label": "Original label Rubritalea squalenifaciens DSM 18772 preserved.",
                    "category_fit": "biolink:OrganismTaxon retained, not independently certified.",
                    "rank_or_type": "Retained BacDive record marks 1123071 at strain level; "
                    "independent versioned NCBI rank/status verification remains unavailable.",
                    "definition": "Paper and source identity context do not resolve all source "
                    "crosswalk fields or establish a formal node-definition proof.",
                    "authority_version": "Retained LPSN 785725 declares version 1; no new canonical "
                    "NCBI/Biolink authority evidence was authored in this canary."}),
        assessment("object_node", "representation",
                   "The original object label is non motile. The paper supports that descriptive "
                   "trait for its isolate, but versioned METPO identity, definition and category "
                   "fitness were not adjudicated in this abstract-adapter canary.",
                   {"identity": "Original METPO:1000703 preserved without a replacement mapping.",
                    "label": "Retained original label non motile.",
                    "category_fit": "biolink:PhenotypicQuality retained; nonempty category is not "
                    "semantic validation.",
                    "rank_or_type": "Phenotype class, not organism, measurement or assay procedure; "
                    "formal typing still requires authority review.",
                    "definition": "No versioned METPO definition proof was authored here.",
                    "authority_version": "Authority snapshot availability in the preparation "
                    "cohort does not substitute for an inspected, scoped proof."}),
        assessment("source_fidelity", "provenance",
                   "BactoTraits row 8521 records non-motile=1 and motile=0 and points to "
                   "BacDive 17851, but its collection-code field conflicts with that strain's "
                   "DSM 18772 identity. Exact copying is replayable; fidelity of the complete "
                   "strain-bound assertion remains not assessable pending reconciliation.",
                   {"source_binding": "Pinned BactoTraits CSV row 8521, BacDive 17851, LPSN GSS "
                    "row 27332 and LPSN API 785725 are retained unchanged. The CSV collection codes "
                    "DSM 19353/JCM 14586 are not silently joined as equivalents of DSM 18772."}),
    ]


def review_document(packet_pin, proofs_pin, copied_pins, spans, started, finished, ignored_check):
    target = {"target_id": OCCURRENCE, "path": packet_pin["path"],
              "selector": "occurrence_id=" + OCCURRENCE, "kind": "snapshot_row",
              "record_class": "ReleaseOccurrence", "label": "Fresh-05 nonmotility abstract canary",
              "ownership_note": "Frozen graph/source bytes remain immutable; maintained source "
              "join ownership must be resolved before any correction."}
    inputs = [proofs_pin["path"], *[p["path"] for p in copied_pins], COHORT,
              "artifacts/edge-calibration-20261115/protocol.json",
              "src/edgemech/occurrence_review.py", "src/edgemech/occurrence_packet.py",
              "src/edgemech/literature_cache.py", "src/edgemech/contract-pins.json",
              "schema/record_review.yaml", "docs/record-review-profile.md",
              "scripts/adhoc/run_abstract_canary_20261115.py"]
    inspected = inspect_source(ROOT, [target], inputs)
    paper_pin = next(p for p in copied_pins if p["path"].endswith("/abstract.json"))
    evidence = [{"evidence_id": "packet-source", "kind": "record_content",
                 "reference": packet_pin["path"], "locator": "original_assertion; endpoints; "
                 "source_records: BactoTraits CSV row 8521, BacDive 17851, LPSN 785725",
                 "accessed_at": started, "support": "context_only",
                 "snapshot_sha256": packet_pin["sha256"],
                 "summary": "Exact retained source/endpoint context includes incompatible "
                 "collection-code fields; this is not independent biological proof."}]
    for eid, quote in QUOTES.items():
        span = spans[eid]
        evidence.append({"evidence_id": eid, "kind": "primary_source",
                         "reference": "https://doi.org/" + DOI,
                         "locator": f"abstract; PMID {PMID}; chars {span['start']}:{span['end']}; "
                         f"text_sha256={span['text_sha256']}", "accessed_at": started,
                         "support": "partial", "quote": quote,
                         "snapshot_sha256": paper_pin["sha256"],
                         "summary": "Literal primary abstract excerpt inspected in full abstract "
                         "context; nominal DSM 18772 strain match does not settle disputed source "
                         "accessions or the entire identifier-bound graph assertion."})
    command, exit_code = ignored_check
    return {
        "schema_version": "1.0.0",
        "review_id": finished.replace("-", "").replace(":", "") + "-fresh05-abstract-adapter",
        "kind": "record", "repository": "CultureBotAI/EdgeMech",
        "title": "Fresh-05 primary-abstract replay canary with unresolved strain binding",
        "started_at": started, "finished_at": finished,
        "reviewer": {"identity": "Codex agent", "kind": "agent", "independence": "self_review",
                     "independence_basis": "New judgments authored from the retained abstract "
                     "and complete source packet for an adapter canary. Historical labels were "
                     "visible; this is not an independent calibration rating or agreement result."},
        "skill": PROFILE, "completion": "partial", "verdict": "needs_curation",
        "scientific_review": True,
        "summary": "One retained occurrence has two DOI/PMID-bound abstract quote proofs and "
        "six explicitly limited assessments. The source strain-accession inconsistency is "
        "recorded separately from biological truth. Required identity/modeling work remains "
        "unavailable; calibration matrices, graph status and population coverage are unchanged.",
        "source": inspected["source"], "targets": [target],
        "scope": {"description": "One partial source/literature adapter canary for fresh-05.",
                  "selection": "Fixed retained case from the prepared cohort; no new sampling "
                  "and no independent calibration rating.", "coverage": "partial",
                  "population_size": 1, "reviewed_target_ids": [OCCURRENCE],
                  "exclusions": [{"target": "Independent ten-case calibration scoring",
                                  "reason": "Evidence freeze and two independent reviewers are pending."},
                                 {"target": "Other 99 retained occurrences and deferred 9900",
                                  "reason": "Single adapter canary only; no review expansion."}]},
        "checks": [
            {"check_id": "private-staging", "name": "Ignored private staging preflight",
             "status": "passed", "required": True, "target_ids": [OCCURRENCE],
             "command": command, "exit_code": exit_code, "expected_exit_code": 0,
             "summary": "Git ignore check passed; no tracked destination files; fresh private "
             "directory and exclusive 0600 files enforce no overwrite."},
            {"check_id": "source-packet", "name": "Exact retained source and endpoint replay",
             "status": "passed", "required": True, "target_ids": [OCCURRENCE],
             "evidence_ids": ["packet-source"],
             "summary": "Fixed input hashes and cohort identity checked; build_packet and "
             "validate_packet replayed the newly persisted occurrence/source bytes."},
            {"check_id": "abstract-identity-quotes", "name": "Primary abstract identity and quotes",
             "status": "passed", "required": True, "target_ids": [OCCURRENCE],
             "evidence_ids": PAPER_IDS,
             "summary": "The abstract adapter selected the exact MED/PMID primary result, "
             "verified DOI/title identity, extracted the complete abstract, and verify_quote "
             "matched both literal excerpts with hashes/offsets within one 25-word budget. "
             "No full text was inspected or claimed."},
            {"check_id": "pinned-contracts", "name": "Pinned CLAW contract byte verification",
             "status": "passed", "required": True, "target_ids": [OCCURRENCE],
             "summary": "check_contracts returned successfully before review construction."},
            {"check_id": "source-identity-resolution", "name": "Independent strain-binding resolution",
             "status": "unavailable", "required": True, "target_ids": [OCCURRENCE],
             "evidence_ids": ["packet-source"],
             "summary": "The observed collection-code conflict has not been reconciled by "
             "the maintained owner or independent identity authorities."},
            {"check_id": "versioned-modeling", "name": "Predicate and both endpoint authorities",
             "status": "unavailable", "required": True, "target_ids": [OCCURRENCE],
             "summary": "Scoped versioned NCBI/METPO/Biolink/RO proofs were not authored in "
             "this canary; all modeling axes remain unresolved and review completion partial."}],
        "evidence": evidence, "assessments": authored_assessments(),
        "findings": [{"finding_id": "source-accession-conflict",
                      "issue_key": "bactotraits-row8521-conflicting-strain-accessions",
                      "category": "identity", "severity": "major", "status": "open",
                      "certainty": "confirmed", "title": "Source row carries conflicting strain accessions",
                      "description": "BactoTraits CSV row 8521 associates BacDive 17851 and the "
                      "Rubritalea squalenifaciens name with collection codes DSM 19353/JCM 14586. "
                      "The linked BacDive 17851 record and retained LPSN/primary abstract instead "
                      "bind DSM 18772/HOact23. The inconsistency is confirmed; which source field "
                      "or join needs correction is unresolved. No equivalence is invented.",
                      "target_ids": [OCCURRENCE],
                      "field_paths": ["source_records[0].text: culture collection codes",
                                      "source_records[0].text: Bacdive_ID"],
                      "evidence_ids": ["packet-source", *PAPER_IDS],
                      "ownership_note": "BactoTraits source table and KG-Microbe BactoTraits "
                      "join owners require triage before a proposed correction; maintained "
                      "owner paths remain unknown.",
                      "external_issues": [SOURCE_CONFLICT_ISSUE]}],
        "actions": [{"action_id": "reconcile-source-accessions",
                     "finding_ids": ["source-accession-conflict"], "target_ids": [OCCURRENCE],
                     "description": "Trace the exact BactoTraits row 8521 join, independently resolve "
                     "the competing collection identifiers and preserve source/model uncertainty "
                     "until a maintained correction or justified no-change decision is verified.",
                     "ownership_note": "Maintained source/transform owner investigation is tracked "
                     "in issue 130; exact owner paths remain unresolved.",
                     "acceptance_checks": ["Retain the row 8521 text hash and exact occurrence binding.",
                                           "No alias inferred from shared species name alone.",
                                           "A proposed correction has independent identity provenance "
                                           "and is verified against regenerated candidate bytes."]}],
        "limitations": [
            "Partial self-review adapter canary, excluded from both independent calibration matrices.",
            "Only the retained primary abstract was inspected; no full paper or Methods assay review.",
            "The nominal strain's nonmotility is not silently promoted to a resolved graph claim "
            "while source binding and versioned modeling remain unresolved.",
            "The source discrepancy does not establish a biological contradiction or prove which "
            "upstream field is wrong.",
            "Zero provider calls and no graph correction/admission; all historical bytes remain intact.",
            "Private source and response bodies stay in ignored staging; canonical output contains "
            "bounded quotes, identifiers, locators and hashes."],
        "links": ["https://github.com/CultureBotAI/EdgeMech/issues/127", SOURCE_CONFLICT_ISSUE,
                  "https://doi.org/" + DOI],
        "tags": ["bounded-canary", "abstract-evidence", "excluded-from-calibration-scoring"],
    }


def run(retained, paper, staging):
    started = utc_now()
    raws, occurrence, source, paper_raw, spans = load_inputs(retained, paper)
    check_contracts()
    relative, stage, command, exit_code = destination(staging)
    (ROOT / ".temp").mkdir(mode=0o700, exist_ok=True)
    stage.mkdir(mode=0o700)
    for name in ("occurrence.json", "source.json"):
        write_new(stage / name, raws[name])
    write_new(stage / "prepared-packet.json", raws["packet.json"])
    write_new(stage / "abstract.json", paper_raw)
    occurrence_pin, source_pin = pin(stage / "occurrence.json"), pin(stage / "source.json")
    packet = build_packet(occurrence, source, occurrence_input=occurrence_pin,
                          source_input=source_pin, root=ROOT)
    write_json(stage / "packet.json", packet)
    validate_packet(json.loads(read_bytes(stage, "packet.json")), root=ROOT)
    packet_pin, paper_pin = pin(stage / "packet.json"), pin(stage / "abstract.json")
    proofs = [{"evidence_id": "packet-source", "kind": "packet", "input": packet_pin,
               "reference": packet_pin["path"], "support": "context_only", "scope": "exact",
               "scope_rationale": "Exact frozen source context, including the unresolved "
               "strain-accession conflict; not independent biological proof.",
               "inspected_extent": "Complete retained occurrence, both endpoints and all four "
               "source records: BactoTraits row 8521, BacDive 17851, LPSN GSS row 27332 "
               "and API 785725.",
               "axes": ["source_fidelity", "relation", "subject_node", "object_node"]}]
    for eid, span in spans.items():
        proofs.append({**paper_identity(), "evidence_id": eid, "input": paper_pin,
                       "support": "partial", "scope": "partial",
                       "scope_rationale": "Direct nominal DSM 18772/HOact23 nonmotility evidence; "
                       "the original graph identifiers/model and conflicting source accessions "
                       "are not completely resolved by this abstract.",
                       "axes": ["claim", "literature"],
                       **{key: span[key] for key in ("text_sha256", "start", "end", "extractor")}})
    write_json(stage / "proofs.json", {"profile": PROFILE, "occurrence_id": OCCURRENCE,
                                      "proofs": proofs})
    proofs_pin = pin(stage / "proofs.json")
    copied_pins = [occurrence_pin, source_pin, pin(stage / "prepared-packet.json"), paper_pin]
    finished = utc_now()
    review = review_document(packet_pin, proofs_pin, copied_pins, spans, started, finished,
                             (command, exit_code))
    write_json(stage / "authored-review.json", review)
    validate_occurrence_review(ROOT, review, packet_pin["path"], proofs_pin["path"])
    result = save_occurrence_review(ROOT, review, packet_pin["path"], proofs_pin["path"])
    receipt = {**result, "staging": str(relative), "provider_calls": 0,
               "calibration_rating": False, "calibration_pass": False,
               "review_completion": review["completion"], "primary_abstract_sha256": PAPER_SHA,
               "original_preparation_pins": RETAINED_PINS, "packet": packet_pin,
               "proofs": proofs_pin, "quotation_words": sum(len(q.split()) for q in QUOTES.values())}
    write_json(stage / "receipt.json", receipt)
    require(json.loads(read_bytes(stage, "receipt.json")) == receipt,
            "Persisted receipt differs")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", action="store_true", help="Verify pinned inputs and destination; no writes")
    mode.add_argument("--run", action="store_true", help="Persist exactly one fresh-05 canary")
    parser.add_argument("--retained-directory", type=Path, default=RETAINED)
    parser.add_argument("--paper", type=Path, default=PAPER)
    parser.add_argument("--staging", default=".temp/abstract-canary-fresh05-127-20261115")
    args = parser.parse_args()
    if args.plan:
        load_inputs(args.retained_directory, args.paper)
        destination(args.staging)
        result = {"action": "plan", "writes": 0, "provider_calls": 0,
                  "occurrence_id": OCCURRENCE, "staging": args.staging,
                  "original_preparation_pins": RETAINED_PINS, "primary_abstract_sha256": PAPER_SHA,
                  "assessments": AXES, "completion": "partial", "calibration_rating": False,
                  "quotation_words": sum(len(q.split()) for q in QUOTES.values())}
    else:
        result = run(args.retained_directory, args.paper, args.staging)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
