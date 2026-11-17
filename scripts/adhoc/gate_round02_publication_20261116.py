#!/usr/bin/env python3
"""Whole-bundle quote accounting and quote-free public derivatives for M5 round02.

Runs canonical proof replay before inventory. Groups verified publication aliases
across every reviewer/case, deduplicates whitespace-equivalent excerpts, preserves
private originals, and only accepts exact regenerated public projection bytes.
Unknown files, symlinks, post-gate prose changes, incomplete batch coverage and
unreplayable metadata fail closed. Preparation itself does not publish or approve.

Round config also requires package_sha256 and reviewers keyed reviewer-a/b, each
with root, sealed matrix path and exact canonical_identity. Matrix receipts bind
the expected actual model/session and initial per-case categories.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).absolute().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.dont_write_bytecode = True

from kg_microbe_reviews import load_document  # noqa: E402

from edgemech.literature_cache import LiteratureCache, verify_quote  # noqa: E402
from edgemech.occurrence_packet import validate_packet  # noqa: E402
from edgemech.occurrence_review import (  # noqa: E402
    CATEGORIES,
    _europepmc_abstract,
    _jats,
    validate_occurrence_review,
)
from edgemech.storage.parquet import safe_path  # noqa: E402

SCHEMA = "edgemech-round02-publication-gate/v1"


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def text_hash(value):
    return digest(str(value).encode())


def read_pin(root, relative):
    path = Path(relative)
    require(not path.is_absolute() and ".." not in path.parts, "Input must be root relative")
    raw = safe_path(root / path).read_bytes()
    return raw, {"path": str(path), "sha256": digest(raw)}


def add_quote(groups, aliases, quote, origin):
    """Union metadata-verified aliases, including transitive DOI/PMID/PMCID bridges."""
    aliases = set(aliases)
    require(bool(aliases), "Quote lacks verified source identity")
    quote = " ".join(quote.split())
    require(bool(quote), "Empty quoted excerpt")
    joined = [g for g in groups if g["aliases"] & aliases]
    quotes = {quote: [origin]}
    for group in joined:
        aliases |= group["aliases"]
        for prior, locations in group["quotes"].items():
            quotes.setdefault(prior, []).extend(locations)
        groups.remove(group)
    # Earlier groups can become connected by aliases collected from a later one.
    while True:
        joined = [g for g in groups if g["aliases"] & aliases]
        if not joined:
            break
        for group in joined:
            aliases |= group["aliases"]
            for prior, locations in group["quotes"].items():
                quotes.setdefault(prior, []).extend(locations)
            groups.remove(group)
    groups.append({"aliases": aliases, "quotes": quotes})


def public_aliases(aliases):
    """Authority version prose is private; publication identifiers remain usable."""
    return sorted("authority-sha256:" + text_hash(a) if a.startswith("authority:") else a
                  for a in aliases)


def quote_inventory(groups):
    result = []
    for group in groups:
        excerpts = [{"quote_sha256": text_hash(q), "words": len(q.split()),
                     "occurrences": sorted(locations, key=lambda x: json.dumps(x, sort_keys=True))}
                    for q, locations in group["quotes"].items()]
        words = sum(item["words"] for item in excerpts)
        result.append({"source_identities": public_aliases(group["aliases"]),
                       "deduplicated_quote_words": words, "maximum_words": 25,
                       "within_budget": words <= 25,
                       "excerpts": sorted(excerpts, key=lambda x: x["quote_sha256"])})
    return sorted(result, key=lambda x: x["source_identities"])


def coverage(config):
    require(config["mode"] in {"canary", "round"}, "Unknown publication mode")
    specs = config["reviews"]
    require(isinstance(specs, list), "Reviews must be a list")
    keys = [(s["reviewer"], s["case_id"]) for s in specs]
    require(len(keys) == len(set(keys)), "Repeated reviewer/case")
    cohort = json.loads((ROOT / "artifacts/edge-calibration-20261115/cohort.json").read_text())
    expected = {case["case_id"] for case in cohort["cases"]}
    require(all(cid in expected for _, cid in keys), "Unknown original cohort case")
    if config["mode"] == "round":
        require(set(keys) == {(r, c) for r in ("reviewer-a", "reviewer-b") for c in expected},
                "Round publication requires both reviewers and all ten cases")
    else:
        require(len(specs) == 1 and keys[0][0] == "operational-canary",
                "Canary must contain one operational unit, excluded from scoring")
    canonical_pairs = [(str(Path(spec["root"]).resolve()),
                        str((Path(spec["root"]) / spec["review"]).resolve())) for spec in specs]
    require(len(canonical_pairs) == len(set(canonical_pairs)),
            "Repeated canonical root/review pair across reviewer/case labels")
    return cohort


def reviewer_bindings(config):
    if config["mode"] == "canary":
        return {}
    declared = config.get("reviewers", {})
    require(set(declared) == {"reviewer-a", "reviewer-b"},
            "Round requires expected reviewer bindings from sealed matrices")
    bindings = {}
    for rid, item in declared.items():
        root = safe_path(Path(item["root"]).absolute())
        raw, pin = read_pin(root, item["matrix"])
        receipt_raw, receipt_pin = read_pin(root, item["matrix"] + ".receipt.json")
        matrix, receipt = json.loads(raw), json.loads(receipt_raw)
        reviewer = matrix["reviewer"]
        require(receipt["matrix_path"] == item["matrix"] and
                receipt["matrix_sha256"] == pin["sha256"] and
                receipt["reviewer"] == reviewer and
                receipt["package_sha256"] == matrix["package_sha256"] == config["package_sha256"],
                "Sealed reviewer matrix/receipt/package binding differs")
        require(matrix["round_id"] == "m5-calibration-20261116-round02" and
                reviewer["id"] == rid and reviewer.get("session_id") and
                reviewer.get("model") not in {None, "", "unknown", "configured_default"},
                "Expected actual reviewer identity/model/session unavailable")
        require(all(isinstance(reviewer[key], str) and
                    re.fullmatch(r"[A-Za-z0-9_.:-]+", reviewer[key])
                    for key in ("model", "session_id")), "Actual reviewer metadata must be identifiers")
        require(item.get("canonical_identity"), "Expected canonical reviewer identity missing")
        cases = {case["case_id"]: case for case in matrix["cases"]}
        require(len(cases) == len(matrix["cases"]), "Repeated sealed matrix case")
        bindings[rid] = {"root": str(root.resolve()), "reviewer": reviewer,
                         "canonical_identity": item["canonical_identity"], "cases": cases,
                         "matrix": pin, "matrix_receipt": receipt_pin}
    require(len({b["reviewer"]["session_id"] for b in bindings.values()}) == 2 and
            len({b["canonical_identity"] for b in bindings.values()}) == 2,
            "The two reviewer labels must bind distinct sessions and canonical identities")
    return bindings


def bind_review(spec, review, proofs, replay, bindings, seen_ids):
    require(review["review_id"] not in seen_ids, "Repeated canonical review_id")
    seen_ids.add(review["review_id"])
    if not bindings:
        return
    bound = bindings[spec["reviewer"]]
    require(str(Path(spec["root"]).resolve()) == bound["root"], "Review root differs from reviewer binding")
    require(review["reviewer"]["identity"] == bound["canonical_identity"] and
            review["reviewer"].get("model") == bound["reviewer"]["model"],
            "Canonical reviewer identity/model differs from sealed reviewer binding")
    if "identity" in proofs:
        require(all(proofs["identity"].get(key) == bound["reviewer"][key]
                    for key in ("id", "model", "session_id")),
                "Proof session identity differs from sealed reviewer binding")
    initial = bound["cases"][spec["case_id"]]
    initial_axes = {a["axis"]: a["category"] for a in initial["assessments"]}
    require(initial["occurrence_id"] == replay["occurrence_id"] and
            len(initial["assessments"]) == 6 and set(initial_axes) == set(CATEGORIES) and
            initial_axes == replay["assessments"],
            "Canonical case/categories differ from the sealed initial matrix")



def quotation_catalog(root, review, proofs):
    """Replay quotation bytes/metadata even when a draft's semantic validation fails.

    This only establishes literal source accounting. It neither changes support
    roles nor treats a source report as independent scientific support.
    """
    evidence = {item["evidence_id"]: item for item in review["evidence"]}
    require(len(evidence) == len(review["evidence"]), "Repeated evidence identity")
    proof_ids = [p["evidence_id"] for p in proofs["proofs"]]
    require(len(proof_ids) == len(set(proof_ids)) and set(proof_ids) == set(evidence),
            "Quotation inventory requires every cited/provided proof exactly once")
    inputs = {item["path"]: item["sha256"] for item in review["source"]["inputs"]}
    result = []
    for proof in proofs["proofs"]:
        item = evidence[proof["evidence_id"]]
        if proof["kind"] == "packet":
            require(not item.get("quote"), "Packet proof cannot conceal a quotation")
            continue
        raw, pin = read_pin(root, proof["input"]["path"])
        require(inputs.get(pin["path"]) == pin["sha256"] == proof["input"]["sha256"] ==
                item["snapshot_sha256"], "Quoted source bytes are not exactly bound")
        require(item["reference"] == proof["reference"], "Quotation reference differs")
        if proof["kind"] == "europepmc_abstract":
            text, aliases = _europepmc_abstract(raw, proof)
            kind = "abstract"
        elif proof["kind"] == "jats":
            text, aliases = _jats(raw, proof)
            kind = "oa_fulltext"
        else:
            require(proof["kind"] == "authority" and proof.get("version"), "Unknown quoted source")
            text, kind = raw.decode("utf-8"), "authority_text"
            aliases = {"authority:" + proof["reference"] + "#" + proof["version"],
                       "authority-raw-sha256:" + digest(raw)}
        document = LiteratureCache._document({"response_sha256": digest(raw)}, kind, text)
        quotation = verify_quote(document, item.get("quote"))
        require(all(proof.get(key) == quotation[key] for key in ("text_sha256", "start", "end", "extractor")),
                "Quotation offsets or extractor differ")
        require(f"chars {quotation['start']}:{quotation['end']}" in item["locator"],
                "Quotation locator does not bind verified offsets")
        quote = " ".join(quotation["quote"].split())
        result.append({"quote": quote, "aliases": aliases, "sha256": text_hash(quote),
                       "evidence_id": item["evidence_id"], "raw_sha256": digest(raw)})
    return result



def bind_original_inputs(root, review, proofs, packet, spec, original_occurrence):
    """Bind original bytes and occurrence even if semantic input validation fails."""
    inputs = {item["path"]: item["sha256"] for item in review["source"]["inputs"]}
    require(len(inputs) == len(review["source"]["inputs"]), "Duplicate authored source input")
    for path, expected in inputs.items():
        _, actual = read_pin(root, path)
        require(actual["sha256"] == expected, "Authored source input changed")
    for path in (spec["packet"], spec["proofs"]):
        _, actual = read_pin(root, path)
        require(inputs.get(path) == actual["sha256"], "Packet/proof sidecar is not bound to authored input")
    require(packet["occurrence_id"] == proofs["occurrence_id"] == original_occurrence,
            "Packet/proof occurrence differs from original cohort")
    require(len(review["targets"]) == 1, "Exactly one original occurrence target required")
    target = review["targets"][0]
    require(target["target_id"] == original_occurrence and target["path"] == spec["packet"] and
            target.get("selector") == "occurrence_id=" + original_occurrence,
            "Authored target path/selector differs from original packet occurrence")
    validate_packet(packet, root=root)


def review_replay(root, review, proofs, spec, source_mode):
    require(source_mode in {"canonical_review", "authored_input"}, "Unknown publication source mode")
    try:
        result = validate_occurrence_review(root, review, spec["packet"], spec["proofs"])
        return result, {"status": "passed", "scope": "Production input validation; not persistence"}
    except Exception as error:
        if source_mode != "authored_input":
            raise
        axes = {}
        for assessment in review["assessments"]:
            dims = {d["name"]: d["value"] for d in assessment["dimensions"]}
            require(dims["axis"] not in axes, "Duplicate authored assessment axis")
            axes[dims["axis"]] = dims["category"]
        require(len(review["targets"]) == 1, "Draft requires one original occurrence target")
        return {"occurrence_id": review["targets"][0]["target_id"], "assessments": axes}, {
            "status": "failed", "scope": "Original authored input; failure preserved without correction",
            "error_type": type(error).__name__, "error_sha256": text_hash(str(error))}


def derive(config):
    cohort = coverage(config)
    source_mode = config.get("source_mode", "canonical_review")
    originals = {case["case_id"]: case["occurrence_id"] for case in cohort["cases"]}
    groups, files, sources = [], {}, []
    bindings, seen_ids = reviewer_bindings(config), set()
    for spec in sorted(config["reviews"], key=lambda s: (s["reviewer"], s["case_id"])):
        root = safe_path(Path(spec["root"]).absolute())
        review_raw, review_pin = read_pin(root, spec["review"])
        proof_raw, proof_pin = read_pin(root, spec["proofs"])
        packet_raw, packet_pin = read_pin(root, spec["packet"])
        review, proofs, packet = load_document(review_raw), json.loads(proof_raw), json.loads(packet_raw)
        bind_original_inputs(root, review, proofs, packet, spec, originals[spec["case_id"]])
        replay, validation = review_replay(root, review, proofs, spec, source_mode)
        require(replay["occurrence_id"] == originals[spec["case_id"]], "Wrong original occurrence")
        bind_review(spec, review, proofs, replay, bindings, seen_ids)
        evidence_index = []
        for quotation in quotation_catalog(root, review, proofs):
            origin = {"reviewer": spec["reviewer"], "case_id": spec["case_id"],
                      "evidence_id_sha256": text_hash(quotation["evidence_id"])}
            add_quote(groups, quotation["aliases"], quotation["quote"], origin)
            evidence_index.append({"source_identities": public_aliases(quotation["aliases"]),
                                   "quote_sha256": quotation["sha256"],
                                   "raw_sha256": quotation["raw_sha256"]})
        assessments = []
        for assessment in review["assessments"]:
            dims = {d["name"]: d["value"] for d in assessment["dimensions"]}
            axis, category = dims["axis"], dims["category"]
            require(axis in CATEGORIES and category in CATEGORIES[axis], "Unrecognized categories")
            assessments.append({"axis": axis, "category": category,
                                "scope_sha256": text_hash(dims["scope"]),
                                "authored_assessment_sha256": digest(encoded(assessment))})
        require(review["completion"] in {"partial", "completed", "blocked", "aborted"},
                "Unknown completion status")
        require(review["verdict"] in {"pass", "pass_with_notes", "needs_curation", "blocked", "fail"},
                "Unknown aggregate verdict")
        source = {"reviewer": spec["reviewer"], "case_id": spec["case_id"],
                  "review": review_pin, "proofs": proof_pin, "packet": packet_pin}
        sources.append(source)
        projection = {"schema": SCHEMA, "mode": config["mode"], "reviewer": spec["reviewer"],
                      "case_id": spec["case_id"], "occurrence_id": packet["occurrence_id"],
                      "assessments": sorted(assessments, key=lambda a: a["axis"]),
                      "completion": review["completion"], "verdict": review["verdict"],
                      "private_inputs": source, "source_mode": source_mode,
                      "production_input_validation": validation,
                      "canonical_persistence_asserted": False,
                      "source_evidence": evidence_index, "quotation_words": 0,
                      "canonical_review": False, "kg_admissions": 0,
                      "calibration_rating": config["mode"] == "round"}
        files[f"{spec['reviewer']}-{spec['case_id']}.json"] = encoded(projection)
    inventory = quote_inventory(groups)
    inventory_document = {"schema": SCHEMA, "coverage": {"mode": config["mode"],
                          "reviews": len(sources), "expected": 20 if config["mode"] == "round" else 1},
                          "scope": "All evidence excerpts in every specified private review or authored draft; "
                          "public derivative files contain hashes and categorical fields only.",
                          "private_source_inventory": inventory,
                          "private_originals_within_budget": all(g["within_budget"] for g in inventory),
                          "private_originals_modified": False,
                          "public_derivative_quote_words": 0}
    files["quote-inventory.json"] = encoded(inventory_document)
    gate = {"schema": SCHEMA, "mode": config["mode"], "passed": True,
            "public_quotes": "zero_by_exact_schema_projection",
            "self_file": "publication-gate.json",
            "self_hash_location": "private receipt.json public_file_pins",
            "all_proposed_public_files": [{"path": name, "sha256": digest(raw)}
                                          for name, raw in sorted(files.items())],
            "source_coverage": sources, "private_originals_published": False, "source_mode": source_mode,
            "sealed_reviewer_bindings": {rid: {
                "reviewer": {key: bound["reviewer"][key] for key in ("id", "model", "session_id")},
                "matrix": bound["matrix"], "matrix_receipt": bound["matrix_receipt"]}
                for rid, bound in bindings.items()},
            "private_originals_within_budget": inventory_document["private_originals_within_budget"],
            "private_over_budget_source_count": sum(not g["within_budget"] for g in inventory),
            "scope": "Publication quotation gate only; no scientific or calibration approval."}
    # Gate itself is generated from enumerations, paths, hashes and verified IDs.
    files["publication-gate.json"] = encoded(gate)
    return files, gate


def inspect_candidate(destination, expected):
    require(destination.is_dir() and not destination.is_symlink(), "Candidate directory invalid")
    entries = list(destination.rglob("*"))
    require(all(not path.is_symlink() for path in entries), "Candidate includes symlink")
    actual = {str(path.relative_to(destination)) for path in entries if path.is_file()}
    require(actual == set(expected), "Public file inventory incomplete or has unaccounted files")
    for name, raw in expected.items():
        require((destination / name).read_bytes() == raw,
                f"Proposed public bytes differ from quote-free projection: {name}")
    return [{"path": name, "sha256": digest(raw)} for name, raw in sorted(expected.items())]


def create(config, stage):
    require(not stage.exists(), "Publication stage must be new")
    files, gate = derive(config)
    stage.mkdir(mode=0o700, parents=True)
    public = stage / "proposed-public"
    public.mkdir(mode=0o700)
    for name, raw in files.items():
        with (public / name).open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    pins = inspect_candidate(public, files)
    receipt = {"schema": SCHEMA, "config_sha256": digest(encoded(config)),
               "helper_sha256": digest(Path(__file__).read_bytes()), "public_file_pins": pins,
               "gate": gate, "published": False}
    with (stage / "receipt.json").open("xb") as stream:
        stream.write(encoded(receipt))
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "check"))
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--stage", type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(safe_path(args.config.absolute()).read_text())
    stage = safe_path(args.stage.absolute(), exists=args.action == "check")
    require(".temp" in stage.parts, "Stage must remain in private .temp until reviewed")
    if args.action == "prepare":
        result = create(config, stage)
    else:
        files, gate = derive(config)
        pins = inspect_candidate(stage / "proposed-public", files)
        receipt = json.loads((stage / "receipt.json").read_text())
        require(receipt["config_sha256"] == digest(encoded(config)) and
                receipt["helper_sha256"] == digest(Path(__file__).read_bytes()) and
                receipt["public_file_pins"] == pins, "Publication receipt changed or runtime differs")
        result = {"passed": gate["passed"], "public_files_verified": len(pins), "published": False}
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
