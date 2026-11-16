"""Bounded occurrence profile over pinned CLAW reviews; no native admission.

Local dimensions refine the existing assessment outcomes. Retained bytes and
literal quotations are replayed independently of authored scientific judgments.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from kg_microbe_governance.artifacts.scripts.record_review import read_bytes
from kg_microbe_reviews import (
    ReviewError,
    load_document,
    read_review,
    save_review,
    validate_review,
)

from .literature_cache import MAX_BYTES, LiteratureCache, abstract_text, full_text, verify_quote
from .occurrence_packet import validate_packet
from .pins import check_contracts

PROFILE = "edgemech-occurrence-review/v1"
PAPER_KINDS = {"jats", "europepmc_abstract"}
CLAIM = {
    "SUPPORTED_AS_STATED": "supported", "CONTRADICTED_AS_STATED": "concern",
    "CONFLICTING_EVIDENCE": "concern", "INSUFFICIENT_EVIDENCE": "unknown",
    "NOT_ASSESSABLE": "unknown", "UNASSESSED": "unknown",
}
MODEL = {"CORRECT": "supported", "INCORRECT": "concern", "UNRESOLVED": "unknown",
         "UNASSESSED": "unknown"}
CATEGORIES = {
    "claim": CLAIM,
    "literature": {"SUPPORTS": "supported", "REFUTES": "concern",
                   "CONFLICTING": "concern", "PARTIAL": "unknown", "NO_MATCH": "unknown",
                   "UNAVAILABLE": "unknown", "NOT_APPLICABLE": "not_applicable",
                   "UNASSESSED": "unknown"},
    "relation": MODEL, "subject_node": MODEL, "object_node": MODEL,
    "source_fidelity": {"SUPPORTED": "supported", "CONTRADICTED": "concern",
                        "NOT_ASSESSABLE": "unknown", "UNASSESSED": "unknown"},
}
DETAILS = {
    "claim": {"assertion_scope"}, "literature": {"search_scope"},
    "relation": {"direction", "domain_range", "specificity", "qualifiers"},
    "subject_node": {"identity", "label", "category_fit", "rank_or_type",
                     "definition", "authority_version"},
    "object_node": {"identity", "label", "category_fit", "rank_or_type",
                    "definition", "authority_version"},
    "source_fidelity": {"source_binding"},
}


def _require(condition, message):
    if not condition:
        raise ReviewError(message)


def _text(value, name):
    _require(isinstance(value, str) and bool(value.strip()), f"Missing {name}")
    return value


def _digest(raw):
    return hashlib.sha256(raw).hexdigest()


def _pinned(root, pin, inputs):
    path = pin["path"]
    _require(inputs.get(path) == pin["sha256"], f"Input not bound to review: {path}")
    raw = read_bytes(root, path)
    _require(_digest(raw) == pin["sha256"], f"Retained input changed: {path}")
    return raw


def _identifier(value, name, pattern):
    _require(isinstance(value, str) and re.fullmatch(pattern, value) is not None,
             f"Invalid primary {name}")
    return value


def _optional_identifier(value, name, pattern):
    if value is None or value == "":
        return None
    return _identifier(value, name, pattern)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, "Duplicate JSON metadata key")
        result[key] = value
    return result


def _europepmc_abstract(raw, proof):
    """Bind a MED core result to its primary identifiers before extracting text."""
    _require(len(raw) <= MAX_BYTES, "Abstract response exceeds bounded input size")
    _require(proof.get("inspected_extent") == "abstract",
             "Abstract evidence inspected_extent must be exactly abstract")
    pmid = _identifier(proof.get("pmid"), "PMID", r"[1-9][0-9]*")
    try:
        response = json.loads(raw, object_pairs_hook=_unique_object)
    except (ValueError, UnicodeDecodeError) as error:
        raise ReviewError("Malformed Europe PMC core JSON") from error
    _require(isinstance(response, dict) and isinstance(response.get("resultList"), dict),
             "Europe PMC core response requires resultList")
    results = response["resultList"].get("result")
    _require(isinstance(results, list) and 0 < len(results) <= 1000
             and all(isinstance(item, dict) for item in results),
             "Europe PMC core response requires a bounded result list")
    _require(type(response.get("hitCount")) is int and response["hitCount"] == len(results),
             "Abstract replay requires a complete, untruncated result list")
    med_records = []
    for item in results:
        _require(isinstance(item.get("source"), str), "Primary result source is malformed")
        if item["source"] != "MED":
            continue
        item_id = _identifier(item.get("id"), "MED identifier", r"[1-9][0-9]*")
        item_pmid = _identifier(item.get("pmid"), "PMID", r"[1-9][0-9]*")
        _require(item_id == item_pmid, "Primary MED identifier and PMID disagree")
        med_records.append(item)
    matches = [item for item in med_records if item["pmid"] == pmid]
    _require(len(matches) == 1, "Abstract requires one exact primary MED PMID result")
    record = matches[0]
    title = _text(record.get("title"), "primary article title")
    _require(_text(proof.get("title"), "article title") == title,
             "Primary article title mismatch")
    doi_pattern = r"10\.[0-9]{4,9}/[^\s]+"
    doi = _optional_identifier(record.get("doi"), "DOI", doi_pattern)
    declared_doi = _optional_identifier(proof.get("doi"), "DOI", doi_pattern)
    doi = doi.lower() if doi else None
    declared_doi = declared_doi.lower() if declared_doi else None
    _require(declared_doi == doi, "Primary article DOI mismatch")
    pmcid = _optional_identifier(record.get("pmcid"), "PMCID", r"PMC[1-9][0-9]*")
    if "pmcid" in proof:
        declared_pmcid = _optional_identifier(proof["pmcid"], "PMCID", r"PMC[1-9][0-9]*")
        _require(declared_pmcid == pmcid, "Primary PMCID mismatch")
    identities = {"pmid:" + pmid}
    if doi:
        identities.add("doi:" + doi)
        _require(proof.get("reference") == "https://doi.org/" + doi, "DOI URL mismatch")
    else:
        _text(proof.get("missing_doi_reason"), "missing DOI reason")
        _require(proof.get("reference") == "https://pubmed.ncbi.nlm.nih.gov/" + pmid + "/",
                 "Missing DOI requires bound PMID URL")
    if pmcid:
        identities.add("pmcid:" + pmcid)
    # Do not choose one conflicting MED record by title after matching a DOI.
    # Other provider indexes (e.g. PMC) are not selected as MED primary records.
    for other in med_records:
        if other is record:
            continue
        other_doi = other.get("doi")
        other_pmcid = other.get("pmcid")
        _require(not (doi and isinstance(other_doi, str) and other_doi.lower() == doi)
                 and not (pmcid and other_pmcid == pmcid),
                 "Ambiguous primary publication aliases in MED results")
    markup = _text(record.get("abstractText"), "primary abstractText")
    text = abstract_text(markup)
    _require(bool(text.strip()), "Primary abstract has no readable text")
    return text, identities


def _jats(raw, proof):
    article = ET.fromstring(raw)
    meta = article.find("./front/article-meta")
    _require(meta is not None and article.find("./body") is not None,
             "JATS requires primary article metadata and body")
    ids = {}
    for element in meta.findall("article-id"):
        key = element.get("pub-id-type")
        value = "".join(element.itertext()).strip()
        _require(key not in ids, "Duplicate primary article identifier")
        ids[key] = value
    title = meta.find("./title-group/article-title")
    _require(title is not None, "Primary article title absent")
    actual_title = " ".join("".join(title.itertext()).split())
    _require(proof["title"] == actual_title, "Primary article title mismatch")
    doi = ids.get("doi", "").lower()
    _require(proof.get("doi", "").lower() == doi, "Primary article DOI mismatch")
    pmc = ids.get("pmc", ids.get("pmcid", "")).removeprefix("PMC")
    _require(pmc.isdigit() and proof["pmcid"] == "PMC" + pmc, "Primary PMCID mismatch")
    if "pmc" in ids and "pmcid" in ids:
        _require(ids["pmcid"].removeprefix("PMC") == pmc, "Conflicting primary PMCID aliases")
    identities = {"pmcid:PMC" + pmc}
    if ids.get("pmid"):
        pmid = _identifier(ids["pmid"], "PMID", r"[1-9][0-9]*")
        identities.add("pmid:" + pmid)
    if "pmid" in proof:
        _require(proof["pmid"] == ids.get("pmid"), "Primary PMID mismatch")
    if doi:
        identities.add("doi:" + doi)
        _require(proof["reference"] == "https://doi.org/" + doi, "DOI URL mismatch")
    else:
        _text(proof.get("missing_doi_reason"), "missing DOI reason")
        _require(proof["reference"] == "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC" + pmc + "/",
                 "Missing DOI requires bound PMCID URL")
    return full_text(raw, "PMC" + pmc), identities


def _budget_quote(groups, identities, quote):
    """Unite verified DOI/PMID/PMCID aliases across retained representations."""
    related = [group for group in groups if identities & group["identities"]]
    quotes = {quote}
    for group in related:
        identities |= group["identities"]
        quotes |= group["quotes"]
        groups.remove(group)
    _require(sum(len(value.split()) for value in quotes) <= 25,
             "Quotes exceed bounded 25-word excerpt per source")
    groups.append({"identities": identities, "quotes": quotes})


def _replay_evidence(root, review, packet_path, packet, sidecar, inputs):
    _require(sidecar.get("profile") == PROFILE, "Evidence profile mismatch")
    _require(sidecar.get("occurrence_id") == packet["occurrence_id"],
             "Evidence belongs to another occurrence")
    proofs = {}
    quotation_groups = []
    evidence = {item["evidence_id"]: item for item in review["evidence"]}
    for proof in sidecar["proofs"]:
        eid = proof["evidence_id"]
        _require(eid not in proofs and eid in evidence, "Duplicate or unbound evidence proof")
        item = evidence[eid]
        _require(proof.get("scope") in {"exact", "partial", "context"}, "Invalid evidence scope")
        _text(proof.get("scope_rationale"), "evidence scope rationale")
        _text(proof.get("inspected_extent"), "inspected extent")
        _require(proof["support"] == item["support"], "Evidence support role mismatch")
        axes = proof["axes"]
        _require(isinstance(axes, list) and axes and len(set(axes)) == len(axes)
                 and set(axes) <= CATEGORIES.keys(), "Invalid evidence axis binding")
        raw = _pinned(root, proof["input"], inputs)
        _require(item.get("snapshot_sha256") == _digest(raw), "Evidence raw hash mismatch")
        _require(proof["reference"] == item["reference"], "Evidence reference mismatch")
        _text(item.get("locator"), "evidence locator")
        if proof["kind"] == "packet":
            _require(proof["input"]["path"] == packet_path and item["kind"] == "record_content",
                     "Source evidence must bind the verified packet")
            _require(set(axes) <= {"source_fidelity", "subject_node", "object_node", "relation"},
                     "Copied source content cannot establish independent claim/literature support")
            _require(not item.get("quote"), "Packet evidence is a locator, not a paper quote")
        elif proof["kind"] in PAPER_KINDS | {"authority"}:
            if proof["kind"] in PAPER_KINDS:
                _require(item["kind"] == "primary_source", "Paper must be primary-source evidence")
                if {"claim", "literature"} & set(axes):
                    _require({"claim", "literature"} <= set(axes),
                             "Paper claim/literature evidence must bind both axes")
                if proof["kind"] == "europepmc_abstract":
                    _require(item["locator"].startswith("abstract;"),
                             "Abstract evidence locator must start with abstract;")
                    text, identities = _europepmc_abstract(raw, proof)
                    kind = "abstract"
                else:
                    text, identities = _jats(raw, proof)
                    kind = "oa_fulltext"
            else:
                _require(item["kind"] == "authority", "Authority proof must identify authority evidence")
                _text(proof.get("version"), "authority version")
                _require("literature" not in axes, "Authority evidence is not experimental literature")
                text, kind = raw.decode("utf-8"), "authority_text"
                identities = {"authority:" + proof["reference"] + "#" + proof["version"]}
            document = LiteratureCache._document(
                {"response_sha256": _digest(raw)}, kind, text)
            quote = verify_quote(document, item.get("quote"))
            _budget_quote(quotation_groups, identities, quote["quote"])
            for field in ("text_sha256", "start", "end", "extractor"):
                _require(proof.get(field) == quote[field], f"Quote proof mismatch: {field}")
            _require(f"chars {quote['start']}:{quote['end']}" in item["locator"],
                     "Quote locator must include verified offsets")
        else:
            raise ReviewError("Unsupported evidence replay kind; retain explicit unresolved outcome")
        proofs[eid] = proof
    _require(proofs.keys() == evidence.keys(), "Every evidence item needs a retained replay proof")
    return proofs


def validate_occurrence_review(root: Path, review: dict, packet_path: str, proofs_path: str):
    """Replay one occurrence's inputs, then enforce authored categorical consistency."""
    check_contracts()
    validate_review(review)
    _require(review["skill"] == PROFILE and review["repository"] == "CultureBotAI/EdgeMech",
             "Wrong occurrence profile/repository")
    inputs = {item["path"]: item["sha256"] for item in review["source"]["inputs"]}
    for path, digest in inputs.items():
        _pinned(root, {"path": path, "sha256": digest}, inputs)
    _require(packet_path in inputs and proofs_path in inputs, "Packet and proof sidecar must be pinned")
    packet = load_document(read_bytes(root, packet_path))
    validate_packet(packet, root=root)
    for pin in packet["inputs"].values():
        _pinned(root, pin, inputs)
    sidecar = load_document(read_bytes(root, proofs_path))
    oid = packet["occurrence_id"]
    _require(review["kind"] == "record" and len(review["targets"]) == 1,
             "This bounded profile accepts exactly one occurrence")
    target = review["targets"][0]
    _require(target["target_id"] == oid and target["path"] == packet_path
             and target.get("selector") == "occurrence_id=" + oid,
             "Target must bind the original packet occurrence")
    proofs = _replay_evidence(root, review, packet_path, packet, sidecar, inputs)
    axes = {}
    for assessment in review["assessments"]:
        dims = {item["name"]: item for item in assessment.get("dimensions", [])}
        _require({"axis", "category", "scope"} <= dims.keys(), "Missing categorical dimensions")
        axis, category = dims["axis"]["value"], dims["category"]["value"]
        _require(axis in CATEGORIES and axis not in axes, "Unknown or duplicate assessment axis")
        _require(category in CATEGORIES[axis] and assessment["outcome"] == CATEGORIES[axis][category],
                 "Category does not match canonical outcome")
        _require(assessment["target_ids"] == [oid], "Assessment is not bound to original occurrence")
        _require(DETAILS[axis] <= dims.keys(), f"Missing {axis} modeling/scope explanations")
        for dimension in dims.values():
            _text(dimension["value"], "dimension explanation")
            _require(set(dimension["evidence_ids"]) <= set(assessment["evidence_ids"]),
                     "Dimension evidence must belong to its assessment")
        if category == "UNASSESSED":
            _require(review["completion"] != "completed", "Completed reviews cannot contain unassessed axes")
        linked = [proofs[eid] for eid in assessment["evidence_ids"]]
        _require(all(axis in proof["axes"] for proof in linked), "Evidence is bound to another axis")
        _require(set(assessment["evidence_ids"]) == {
            eid for eid, proof in proofs.items() if axis in proof["axes"]
        }, "Assessment omits applicable evidence declared for its axis")
        roles = {proof["support"] for proof in linked if proof["scope"] == "exact"}
        if axis == "claim":
            _require(all(p["kind"] in PAPER_KINDS | {"authority"} for p in linked),
                     "Claim judgment requires independent literature or authority evidence")
            required = {"SUPPORTED_AS_STATED": {"supports"}, "CONTRADICTED_AS_STATED": {"refutes"},
                        "CONFLICTING_EVIDENCE": {"supports", "refutes"}}.get(category, set())
            _require(required <= roles, "Claim category lacks exact-scope supporting/refuting evidence")
            if category in {"SUPPORTED_AS_STATED", "CONTRADICTED_AS_STATED"}:
                _require(not {"supports", "refutes"} <= roles, "Opposing exact evidence requires conflict")
        elif axis == "literature":
            _require(all(p["kind"] in PAPER_KINDS for p in linked),
                     "Literature requires replayable paper text")
            required = {"SUPPORTS": {"supports"}, "REFUTES": {"refutes"},
                        "CONFLICTING": {"supports", "refutes"}}.get(category, set())
            _require(required <= roles, "Literature category lacks exact-scope evidence")
            if category in {"SUPPORTS", "REFUTES"}:
                _require(not {"supports", "refutes"} <= roles, "Opposing exact literature requires conflict")
            if category == "PARTIAL":
                _require(any(p["support"] == "partial" for p in linked), "Partial evidence absent")
            if category in {"NO_MATCH", "UNAVAILABLE", "NOT_APPLICABLE", "UNASSESSED"}:
                _require(not linked, "Evidence absence/inapplicability cannot conceal linked paper text")
        elif category in {"CORRECT", "INCORRECT"}:
            role = "supports" if category == "CORRECT" else "refutes"
            authority_roles = {p["support"] for p in linked
                               if p["kind"] == "authority" and p["scope"] == "exact"}
            _require(not {"supports", "refutes"} <= authority_roles,
                     "Opposing exact modeling authorities require UNRESOLVED")
            _require(any(p["kind"] == "authority" and p["scope"] == "exact"
                         and p["support"] == role for p in linked),
                     "Resolved modeling judgment requires versioned authority evidence")
        elif axis == "source_fidelity" and category in {"SUPPORTED", "CONTRADICTED"}:
            role = "supports" if category == "SUPPORTED" else "refutes"
            source_roles = {p["support"] for p in linked
                            if p["kind"] == "packet" and p["scope"] == "exact"}
            _require(not {"supports", "refutes"} <= source_roles,
                     "Opposing exact source evidence requires NOT_ASSESSABLE")
            _require(any(p["kind"] == "packet" and p["scope"] == "exact"
                         and p["support"] == role for p in linked),
                     "Source judgment requires exact-scope packet evidence with a matching support role")
        axes[axis] = category
    _require(axes.keys() == CATEGORIES.keys(), "Every occurrence requires all six assessment axes")
    # A supported scoped statement can have a defective or unresolved encoding.
    # Preserve both authored judgments; shared verdict/completion checks and the
    # aggregate pass gate below prevent transport validity becoming approval.
    if review["verdict"] == "pass":
        _require(axes["claim"] == "SUPPORTED_AS_STATED"
                 and all(axes[a] == "CORRECT" for a in ("relation", "subject_node", "object_node")),
                 "Unqualified pass requires resolved claim and modeling judgments")
    for path, digest in inputs.items():
        _pinned(root, {"path": path, "sha256": digest}, inputs)
    return {"profile": PROFILE, "occurrence_id": oid, "assessments": axes,
            "verified_evidence": len(proofs), "verified_quotes": sum(p["kind"] != "packet"
                                                                       for p in proofs.values()),
            "kg_admissions": 0, "native_capability_enabled": False}


def save_occurrence_review(root, review, packet_path, proofs_path):
    validate_occurrence_review(root, review, packet_path, proofs_path)
    path = save_review(root, review)
    relative = str(path.relative_to(root.absolute()))
    persisted = read_review(root, relative)
    receipt = validate_occurrence_review(root, persisted, packet_path, proofs_path)
    return {**receipt, "review": relative, "review_sha256": _digest(path.read_bytes())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("validate", "save", "check"))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--review", required=True)
    parser.add_argument("--packet", required=True)
    parser.add_argument("--proofs", required=True)
    args = parser.parse_args()
    root = args.root.absolute()
    review = (read_review(root, args.review) if args.action == "check"
              else load_document(read_bytes(root, args.review)))
    operation = save_occurrence_review if args.action == "save" else validate_occurrence_review
    print(json.dumps(operation(root, review, args.packet, args.proofs), sort_keys=True))


if __name__ == "__main__":
    main()
