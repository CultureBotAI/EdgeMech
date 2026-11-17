#!/usr/bin/env python3
"""Whole-bundle quote accounting and quote-free public derivatives for M5 round02.

Runs canonical proof replay before inventory. Groups verified publication aliases
across every reviewer/case, deduplicates whitespace-equivalent excerpts, preserves
private originals, and only accepts exact regenerated public projection bytes.
Unknown files, symlinks, post-gate prose changes, incomplete batch coverage and
unreplayable metadata fail closed. Preparation itself does not publish or approve.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).absolute().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.dont_write_bytecode = True

from kg_microbe_reviews import load_document  # noqa: E402

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
    return cohort


def derive(config):
    cohort = coverage(config)
    originals = {case["case_id"]: case["occurrence_id"] for case in cohort["cases"]}
    groups, files, sources = [], {}, []
    for spec in sorted(config["reviews"], key=lambda s: (s["reviewer"], s["case_id"])):
        root = safe_path(Path(spec["root"]).absolute())
        review_raw, review_pin = read_pin(root, spec["review"])
        proof_raw, proof_pin = read_pin(root, spec["proofs"])
        packet_raw, packet_pin = read_pin(root, spec["packet"])
        review, proofs, packet = load_document(review_raw), json.loads(proof_raw), json.loads(packet_raw)
        replay = validate_occurrence_review(root, review, spec["packet"], spec["proofs"])
        require(replay["occurrence_id"] == originals[spec["case_id"]], "Wrong original occurrence")
        evidence = {item["evidence_id"]: item for item in review["evidence"]}
        evidence_index = []
        for proof in proofs["proofs"]:
            item = evidence[proof["evidence_id"]]
            if proof["kind"] == "packet":
                continue
            raw, _ = read_pin(root, proof["input"]["path"])
            if proof["kind"] == "europepmc_abstract":
                _, aliases = _europepmc_abstract(raw, proof)
            elif proof["kind"] == "jats":
                _, aliases = _jats(raw, proof)
            else:
                require(proof["kind"] == "authority", "Unsupported quote source")
                aliases = {"authority:" + proof["reference"] + "#" + proof["version"],
                           "authority-raw-sha256:" + digest(raw)}
            origin = {"reviewer": spec["reviewer"], "case_id": spec["case_id"],
                      "evidence_id_sha256": text_hash(item["evidence_id"])}
            add_quote(groups, aliases, item["quote"], origin)
            evidence_index.append({"source_identities": public_aliases(aliases),
                                   "quote_sha256": text_hash(" ".join(item["quote"].split())),
                                   "raw_sha256": proof["input"]["sha256"]})
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
                      "private_inputs": source,
                      "source_evidence": evidence_index, "quotation_words": 0,
                      "canonical_review": False, "kg_admissions": 0,
                      "calibration_rating": config["mode"] == "round"}
        files[f"{spec['reviewer']}-{spec['case_id']}.json"] = encoded(projection)
    inventory = quote_inventory(groups)
    inventory_document = {"schema": SCHEMA, "coverage": {"mode": config["mode"],
                          "reviews": len(sources), "expected": 20 if config["mode"] == "round" else 1},
                          "scope": "All evidence excerpts in every specified private canonical review; "
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
            "source_coverage": sources, "private_originals_published": False,
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
