#!/usr/bin/env python3
"""Prepare an exact public-file gate from authored data (2026-11-16; #183/#192).

Inputs: root/baseline, explicit private exclusions and extra files, optional
hash-pinned existing quote catalog config, and a separate independent review
attestation. Outputs: private exclusive inventory/config/receipt files. Reuses
the maintained source gate and never invents an attestation or publishes files.
Inventory mode creates reviewable data only; gate mode requires independent
inspection of that exact inventory. Source/quote bodies are never embedded here.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import gate_round02_public_sources_20261116 as source_gate

publication = source_gate.publication


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        publication.require(key not in result, f"Duplicate JSON field: {key}")
        result[key] = value
    return result


def read_json(path):
    return json.loads(publication.safe_path(path).read_bytes(), object_pairs_hook=unique_object)


def read_pinned(root, pin):
    publication.require(isinstance(pin, dict) and set(pin) == {"path", "sha256"},
                        "Expected an existing document path/hash pin")
    path = Path(pin["path"])
    if not path.is_absolute():
        publication.require(".." not in path.parts, "Pinned path escapes root")
        path = root / path
    raw = publication.safe_path(path).read_bytes()
    publication.require(publication.digest(raw) == pin["sha256"], "Pinned document changed")
    return json.loads(raw, object_pairs_hook=unique_object)


def public_inventory(proposal):
    root = publication.safe_path(Path(proposal["root"]).absolute())
    actual = source_gate.proposed_sources(root, proposal["baseline"])
    excluded = proposal.get("excluded_private_files", [])
    excluded_paths = {item["path"] for item in excluded}
    publication.require(len(excluded_paths) == len(excluded), "Repeated private exclusion")
    publication.require(excluded_paths <= actual, "Excluded path is not a proposed Git file")
    paths = actual - excluded_paths
    extras = proposal.get("extra_files", [])
    publication.require(isinstance(extras, list) and len(set(extras)) == len(extras),
                        "Extra files must be distinct absolute path strings")
    for extra in extras:
        publication.require(Path(extra).is_absolute(), "Extra files must use absolute paths")
        publication.require(extra not in paths, "Repeated public file")
        paths.add(extra)
    result = []
    for relative in sorted(paths):
        path = Path(relative)
        source = publication.safe_path(path if path.is_absolute() else root / path)
        result.append({"path": relative, "sha256": publication.digest(source.read_bytes())})
    return result


def independent_attestation(proposal, inventory, preparer):
    root = publication.safe_path(Path(proposal["root"]).absolute())
    publication.require(preparer.strip(), "Preparer identity is required")
    declaration = read_pinned(root, proposal["review_attestation"])
    publication.require(isinstance(declaration.get("reviewer"), str)
                        and declaration["reviewer"].strip()
                        and declaration["reviewer"].strip() != preparer.strip(),
                        "A separate identified reviewer must supply the attestation")
    publication.require(declaration.get("all_files_inspected") is True
                        and declaration.get("no_unaccounted_external_quotations") is True,
                        "Explicit independent complete-file quotation attestation required")
    publication.require(("reviewed_files" in declaration) != ("reviewed_inventory" in declaration),
                        "Attestation must bind exactly one reviewed file inventory")
    reviewed = declaration.get("reviewed_files")
    if "reviewed_inventory" in declaration:
        reviewed = read_pinned(root, declaration["reviewed_inventory"])["files"]
    publication.require(isinstance(reviewed, list), "Reviewed inventory must be a list")
    publication.require(sorted(reviewed, key=lambda item: item["path"]) == inventory,
                        "Independent review does not bind the exact current public inventory")
    return declaration


def prepare(proposal, preparer):
    root = publication.safe_path(Path(proposal["root"]).absolute())
    inventory = public_inventory(proposal)
    declaration = independent_attestation(proposal, inventory, preparer)
    publication.require(isinstance(proposal.get("quote_catalog_reviews", []), list),
                        "Quote catalog reviews must be a list")
    specs = list(proposal.get("quote_catalog_reviews", []))
    catalog_pin = proposal.get("quote_catalog_config")
    if catalog_pin is not None:
        old_config = read_pinned(root, catalog_pin)
        specs = list(old_config["quote_catalog_reviews"]) + specs
    quotes = source_gate.catalog(specs)
    files = []
    for item in inventory:
        path = Path(item["path"])
        source = publication.safe_path(path if path.is_absolute() else root / path)
        raw = source.read_bytes()
        publication.require(publication.digest(raw) == item["sha256"], "File changed during preparation")
        values = source_gate.literals(source, raw)
        matches = [quote for quote in quotes if any(quote["quote"] in value for value in values)]
        files.append({**item, "classification": "catalog_literals" if matches
                      else "no_external_quotation",
                      "quote_sha256s": sorted({quote["sha256"] for quote in matches})})
    return {"root": str(root), "baseline": proposal["baseline"],
            "review_attestation": declaration,
            "review_attestation_source": proposal["review_attestation"],
            "quote_catalog_config_source": catalog_pin,
            "quote_catalog_reviews": specs, "files": files,
            "excluded_private_files": proposal.get("excluded_private_files", []),
            "preparer": preparer, "helper_sha256": publication.digest(Path(__file__).read_bytes())}


def output_directory(root, relative):
    path = Path(relative)
    publication.require(not path.is_absolute() and ".." not in path.parts
                        and path.parts and path.parts[0] == ".temp",
                        "Outputs must be new repository-relative .temp directories")
    target = root / path
    publication.require(not target.exists(), "Output directory already exists")
    publication.safe_path(target, exists=False)
    missing, parent = [], target
    while not parent.exists():
        missing.append(parent)
        parent = parent.parent
    for directory in reversed(missing):
        directory.mkdir(mode=0o700)
    return target


def write_new(path, value):
    raw = publication.encoded(value)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    publication.require(path.read_bytes() == raw, "Persisted gate artifact differs")


def execute(proposal, preparer, operation, output):
    root = publication.safe_path(Path(proposal["root"]).absolute())
    destination = output_directory(root, output)
    if operation in {"inventory", "plan"}:
        result = {"files": public_inventory(proposal),
                  "scope": "Proposed file hashes for independent inspection; not approval"}
        write_new(destination / "inventory.json", result)
        return {"path": str(destination / "inventory.json"), "files": len(result["files"]),
                "attestation_generated": False}
    config = prepare(proposal, preparer)
    write_new(destination / "config.json", config)
    try:
        receipt = source_gate.gate(config)
    except Exception as error:
        write_new(destination / "failure.json", {"error_type": type(error).__name__,
                                                 "error": str(error), "published": False})
        raise
    write_new(destination / "receipt.json", receipt)
    return {"path": str(destination / "receipt.json"), "passed": receipt["passed"],
            "files": len(receipt["files"]), "source_groups": len(receipt["sources"]),
            "published": False, "attestation_generated": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("plan", "inventory", "gate"))
    parser.add_argument("--proposal", type=Path, required=True)
    parser.add_argument("--preparer", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = execute(read_json(args.proposal), args.preparer, args.operation, args.output)
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("passed", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
