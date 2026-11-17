#!/usr/bin/env python3
"""Gate an explicitly reviewed complete public source/docs/message proposal.

Unlike generated data projections, arbitrary prose requires an identified review
attestation. Every proposed file is pinned, classified and checked against the
verified quote catalog. New, omitted or changed files invalidate the gate.
The private config records the reviewer's no-unaccounted-quotation attestation;
this scanner does not pretend to discover arbitrary unattributed paraphrases.
"""
from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
from pathlib import Path

import gate_round02_publication_20261116 as publication
from kg_microbe_reviews import load_document

ROOT = Path(__file__).absolute().parents[2]
sys.dont_write_bytecode = True


def proposed_sources(root, baseline):
    """Include ignored-independent tracked diff plus all nonignored proposed files."""
    changed = subprocess.check_output(
        ["git", "diff", "--name-only", baseline, "--"], cwd=root).decode().splitlines()
    untracked = subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard"], cwd=root).decode().splitlines()
    return {p for p in changed + untracked if (root / p).is_file()}


def literals(path, raw):
    strings = [raw.decode()]
    if path.suffix == ".py":
        strings.extend(node.value for node in ast.walk(ast.parse(raw))
                       if isinstance(node, ast.Constant) and isinstance(node.value, str))
    return [" ".join(value.split()) for value in strings]


def catalog(specs):
    result = []
    for spec in specs:
        root = publication.safe_path(Path(spec["root"]).absolute())
        review_raw, _ = publication.read_pin(root, spec["review"])
        proof_raw, _ = publication.read_pin(root, spec["proofs"])
        review, proofs = load_document(review_raw), json.loads(proof_raw)
        publication.validate_occurrence_review(root, review, spec["packet"], spec["proofs"])
        evidence = {e["evidence_id"]: e for e in review["evidence"]}
        for proof in proofs["proofs"]:
            if proof["kind"] == "packet":
                continue
            raw, _ = publication.read_pin(root, proof["input"]["path"])
            if proof["kind"] == "europepmc_abstract":
                _, aliases = publication._europepmc_abstract(raw, proof)
            elif proof["kind"] == "jats":
                _, aliases = publication._jats(raw, proof)
            else:
                aliases = {"authority:" + proof["reference"] + "#" + proof["version"],
                           "authority-raw-sha256:" + publication.digest(raw)}
            quote = " ".join(evidence[proof["evidence_id"]]["quote"].split())
            result.append({"quote": quote, "aliases": aliases,
                           "sha256": publication.text_hash(quote)})
    return result


def gate(config):
    root = publication.safe_path(Path(config["root"]).absolute())
    declaration = config["review_attestation"]
    publication.require(declaration.get("reviewer") and declaration.get("all_files_inspected") is True
                        and declaration.get("no_unaccounted_external_quotations") is True,
                        "Explicit complete-file quotation review attestation required")
    declared = config["files"]
    by_path = {item["path"]: item for item in declared}
    publication.require(len(declared) == len(by_path), "Duplicate proposed file")
    excluded = config.get("excluded_private_files", [])
    excluded_paths = {e["path"] for e in excluded}
    publication.require(not excluded_paths & by_path.keys(), "Private/public paths overlap")
    actual = proposed_sources(root, config["baseline"])
    repo_paths = {p for p in by_path if not Path(p).is_absolute()}
    publication.require(actual == repo_paths | excluded_paths,
                        "Complete proposed Git file inventory differs; re-review additions or exclusions")
    for item in excluded:
        publication.require(item.get("reason") == "private_canonical_original_not_for_publication",
                            "Excluded file requires explicit private-original disposition")
        raw, pin = publication.read_pin(root, item["path"])
        publication.require(pin["sha256"] == item["sha256"], "Excluded private original changed")
        tracked = subprocess.check_output(["git", "ls-files", "--", item["path"]], cwd=root)
        publication.require(not tracked, "Excluded private original is already tracked")
    quotes = catalog(config["quote_catalog_reviews"])
    groups, files = [], []
    for path, item in sorted(by_path.items()):
        source = publication.safe_path(Path(path) if Path(path).is_absolute() else root / path)
        raw = source.read_bytes()
        publication.require(publication.digest(raw) == item["sha256"], "Reviewed public file changed: " + path)
        literal_values = literals(source, raw)
        # Equal wording can occur in independent publications. Preserve every
        # verified source identity; only file classification deduplicates hashes.
        matched = [q for q in quotes
                   if any(q["quote"] in value for value in literal_values)]
        matched_hashes = {q["sha256"] for q in matched}
        classification = "catalog_literals" if matched else "no_external_quotation"
        publication.require(item["classification"] == classification and
                            set(item["quote_sha256s"]) == matched_hashes,
                            "Quoted literal classification changed: " + path)
        for quote in matched:
            publication.add_quote(groups, quote["aliases"], quote["quote"], {"public_path": path})
        files.append({"path": path, "sha256": publication.digest(raw),
                      "classification": classification, "quote_sha256s": sorted(matched_hashes)})
    inventory = publication.quote_inventory(groups)
    return {"schema": "edgemech-round02-public-source-quote-gate/v1",
            "passed": all(g["within_budget"] for g in inventory), "files": files,
            "sources": inventory, "excluded_private_files": excluded,
            "review_attestation": declaration,
            "scope": "Exact complete proposed source/docs/message inventory; identified reviewer "
            "checked arbitrary prose, parser checked recognized literal excerpts. Separate generated "
            "derivative gate must be included before publishing the final whole bundle."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    result = gate(config)
    with args.output.open("xb") as stream:
        stream.write(publication.encoded(result))
    print(json.dumps({"passed": result["passed"], "files": len(result["files"]),
                      "source_groups": len(result["sources"]), "output": str(args.output)}))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
