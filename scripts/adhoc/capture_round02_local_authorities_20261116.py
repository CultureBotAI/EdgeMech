"""Capture owner Git objects and replay three local identifiers without judging edges."""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import io
import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

KG_REV = "d6baf5b90003a2032747559d94c00f86a7a4c615"
KG_CURRENT = "b631cacf5bca2f5f993e85bacb96578919cc7d92"
ASSAY_REV = "b797ce9d06189ba69c52c29098fbae5fe59e1442"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)
    return {"path": str(path), "sha256": sha(raw)}


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def git_bytes(repo, rev, path):
    return subprocess.check_output(["git", "-C", str(repo), "show", f"{rev}:{path}"])


def function(tree, name):
    found = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name]
    if len(found) != 1:
        raise ValueError(f"Expected one owner function {name}")
    return found[0]


def replay_attribute(transform, utils, column, literal):
    """Execute retained owner's actual method with its emission sink replaced by a collector."""
    namespace = {"json": json, "hashlib": hashlib, "Optional": object,
                 "MICROBEDECODER": "microbedecoder", "SOURCE_ATTRIBUTE_PREFIX": "kgmicrobe.source_attribute:",
                 "_SLUG_STRIP": re.compile(r"[^a-z0-9]+")}
    nodes = [ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0),
             function(ast.parse(utils), "slugify_label"),
             function(ast.parse(transform), "_mint_placeholder")]
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), "<pinned-owner-method>", "exec"), namespace)
    captured = []
    sink = SimpleNamespace(_phenotype_curation=None, _stats=Counter(), _unmapped={},
                           _ensure_terminal_node=lambda *a, **kw: captured.append((a, kw)))
    curie = namespace["_mint_placeholder"](sink, literal, None, "kgmicrobe.source_attribute:", "biolink:Attribute", column)
    args, kwargs = captured[0]
    return {"id": curie, "category": args[1], "name": args[2], "description": kwargs["description"]}


def replay_process(scopes, utils, row):
    """Execute the pinned ProcessScope class, including its definition-bearing description."""
    from dataclasses import dataclass
    namespace = {"json": json, "hashlib": hashlib, "dataclass": dataclass,
                 "MICROBEDECODER": "microbedecoder", "PATHWAY_PREFIX": "kgmicrobe.pathway:",
                 "_SLUG_STRIP": re.compile(r"[^a-z0-9]+"), "__name__": __name__}
    cls = next(n for n in ast.parse(scopes).body if isinstance(n, ast.ClassDef) and n.name == "ProcessScope")
    nodes = [function(ast.parse(utils), "slugify_label"), cls]
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), "<pinned-owner-class>", "exec"), namespace)
    obj = namespace["ProcessScope"](**row)
    return {"id": obj.curie, "category": "biolink:BiologicalProcess", "name": row["source_literal"], "description": obj.description}


def capture(root, output, kg, assay, original, case):
    target = output / case
    target.mkdir(parents=True, exist_ok=False)
    src = json.loads((original / case / "source.json").read_text())
    records = []
    for i, record in enumerate(src["records"]):
        raw = record["text"].encode()
        if sha(raw) != record["text_sha256"]:
            raise ValueError("Retained native source text hash mismatch")
        pin = write(target / f"source-record-{i}.txt", raw)
        records.append({**pin, **{k: record[k] for k in ("locator", "retrieval_url", "extractor", "source_relative_path")}})
    def owner(repo, rev, path, name):
        raw = git_bytes(repo, rev, path)
        pin = write(target / name, raw)
        pins.append({**pin, "git_commit": rev, "owner_path": path})
        return raw.decode()
    pins = []
    utils = owner(kg, KG_REV, "kg_microbe/transform_utils/microbedecoder/utils.py", "microbedecoder-utils.py")
    owner(kg, KG_REV, "kg_microbe/transform_utils/constants.py", "kg-constants.py")
    if case == "fresh-47":
        transform = owner(kg, KG_REV, "kg_microbe/transform_utils/microbedecoder/microbedecoder.py", "microbedecoder.py")
        owner(kg, KG_CURRENT, "kg_microbe/transform_utils/microbedecoder/observation_audit.py", "current-observation-audit.py")
        generated = replay_attribute(transform, utils, "BacDive_Salt_concentration", "0-10")
    elif case == "fresh-32":
        scopes = owner(kg, KG_REV, "kg_microbe/transform_utils/microbedecoder/process_scopes.py", "process-scopes.py")
        table = owner(kg, KG_REV, "mappings/canonical/microbedecoder_process_scope_definitions.tsv", "process-definitions.tsv")
        row = next(r for r in csv.DictReader(io.StringIO(table), delimiter="\t") if r["source_literal"] == "sulfite_respiration")
        generated = replay_process(scopes, utils, row)
    elif case == "first-01":
        owner(kg, KG_REV, "kg_microbe/utils/mapping_file_utils.py", "mapping-file-utils.py")
        owner(kg, KG_REV, "download.yaml", "download.yaml")
        raw = owner(assay, ASSAY_REV, "data/assay_kits_simple.json", "assay-kits-simple.json")
        owner(assay, ASSAY_REV, "src/bacdive_assay_metadata/metadata_builder.py", "assay-metadata-builder.py")
        kit = next(k for k in json.loads(raw)["api_kits"] if k["kit_name"] == "API 20E")
        well = next(w for w in kit["wells"] if w["name"] == "CIT")
        # Exact generator projection; production generator replay is also required in owner canary.
        generated = {"id": f"kgmicrobe.assay:{kit['kit_name']}_{well['name']}".replace(" ", "_"),
                     "category": "biolink:Procedure", "name": f"{kit['kit_name']} - {well['label'][0]}",
                     "description": f"{well['description'][0]}. Kit: {kit['kit_name']}, Well: {well['name']}, Type: {well['type'][0]}"}
    else:
        raise ValueError("Unsupported bounded case")
    original_node = src["edge"]["original_object_node"]
    for key in ("id", "name", "description"):
        if generated[key] != original_node[key]:
            raise ValueError(f"Regenerated original node differs: {key}")
    if generated["category"] != src["edge"]["object_category"]:
        raise ValueError("Regenerated category differs")
    write(target / "regenerated-node.json", json_bytes(generated))
    receipt = {"case_id": case, "occurrence_id": src["edge"]["occurrence_id"], "owner_inputs": pins,
               "native_records": records, "generated": generated,
               "replay_scope": "local definition-bearing node reproduction; not independent biological support or complete sampled build certification",
               "sampled_producer_binding": "Historical M5 report identifies d6baf5b90003a2032747559d94c00f86a7a4c615; exact generated node matches. No cryptographic build receipt from that commit to all sampled graph bytes recovered.",
               "unavailable": ["Complete sampled graph build provenance", "Generating FAPROTAX version for organism-assignment CSV"],
               "authority_files": [p["path"] for p in pins]}
    write(target / "receipt.json", json_bytes(receipt))
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--kg", type=Path, required=True)
    parser.add_argument("--assay", type=Path, required=True)
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--case", choices=["first-01", "fresh-32", "fresh-47"], required=True)
    args = parser.parse_args()
    result = capture(args.root, args.output, args.kg, args.assay, args.original, args.case)
    print(json.dumps({"case": args.case, "owner_inputs": len(result["owner_inputs"]), "native_records": len(result["native_records"]), "node_replay": "matched"}))


if __name__ == "__main__":
    main()
