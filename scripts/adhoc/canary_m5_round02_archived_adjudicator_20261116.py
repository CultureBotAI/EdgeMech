#!/usr/bin/env python3
"""Bounded retrospective check of an exact archived private adjudicator driver.

The .py.txt source is historical provenance, not an approved batch entrypoint.
Its original batch ran before coordinator review. This wrapper checks frozen
inputs first and calls its actual inspect_case function for one fresh-47 only.
No reviewer input is saved or edited. Quote-bearing output remains private.
"""
from __future__ import annotations

import argparse
import importlib.machinery
import importlib.util
import json
from pathlib import Path

import replay_m5_round02_pairs_20261116 as replay

ARCHIVE = Path(__file__).with_name("archive_m5_round02_adjudicator_replay_20261116.py.txt")
EXECUTED_SHA256 = "09ccaf067b0a45155362f14aa48c86fa4d62384d4718a92e046b3ef3a15c3e53"


def load_archive():
    replay.require(replay.sha(ARCHIVE.read_bytes()) == EXECUTED_SHA256,
                   "Archived executed source changed")
    loader = importlib.machinery.SourceFileLoader("archived_round02_adjudicator", str(ARCHIVE))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def canary(config, original, output, reviewer):
    replay.expected_entries(config)
    replay.require(not output.exists() and ".temp" in output.absolute().parts,
                   "Use a new exclusive private canary directory")
    replay.require(not any(p.is_symlink() for p in (output, *output.absolute().parents)),
                   "Output path must not traverse a symlink")
    original_raw = original.read_bytes()
    replay.require(replay.sha(original_raw) == EXECUTED_SHA256 == replay.sha(ARCHIVE.read_bytes()),
                   "Archive does not preserve the exact executed private driver")
    output.mkdir(mode=0o700, parents=True)
    ctx = replay.context(config, reviewer, output / "context")
    # The coordinator adapter bytes were checked against the frozen manifest by
    # context() before this historical driver's production imports can execute.
    module = load_archive()
    root = ctx["root"]
    index_path = root / ".temp/round02-reviewer/reviewer-result.json"
    index_raw = index_path.read_bytes()
    index = json.loads(index_raw)
    case = next(c for c in ctx["manifest"]["cases"] if c["case_id"] == "fresh-47")
    matrix_case = next(c for c in ctx["matrix"]["cases"] if c["case_id"] == "fresh-47")
    indexed = next(c for c in index["cases"] if c["case_id"] == "fresh-47")
    pins = {p["path"]: p for p in ctx["manifest"]["files"]}
    evidence = {eid: p for p in pins.values() for eid in p.get("evidence_ids", [])}
    result = module.inspect_case(root, output / "fresh-47", reviewer, case, matrix_case,
                                 indexed, pins, evidence)
    replay.require(replay.sha(index_path.read_bytes()) == replay.sha(index_raw) and
                   replay.sha(original.read_bytes()) == EXECUTED_SHA256,
                   "Original execution index or private driver changed")
    replay.verify_frozen_inputs(root, ctx["manifest"])
    inspection = json.loads(Path(result["path"]).read_bytes())
    for item in inspection["source_input_pins"]:
        path = Path(item["path"])
        replay.require(item["exists"] and replay.sha(path.read_bytes()) == item["sha256"],
                       "Original authored input changed during canary")
    artifacts = [{"path": str(p.absolute()), "sha256": replay.sha(p.read_bytes())}
                 for p in sorted(output.rglob("*")) if p.is_file()]
    receipt = {"schema": "edgemech-archival-adjudicator-canary/v1",
               "scope": "Retrospective one-unit execution of exact archived source; no batch approval or scientific pass",
               "original_batch_pre_reviewed": False, "archive_is_production_entrypoint": False,
               "archive": {"path": str(ARCHIVE), "sha256": EXECUTED_SHA256},
               "original_private_driver": {"path": str(original.absolute()), "sha256": EXECUTED_SHA256},
               "wrapper_sha256": replay.sha(Path(__file__).read_bytes()),
               "reviewer": reviewer, "case_id": "fresh-47", "contexts": ctx["meta"],
               "result": result, "artifact_pins": artifacts,
               "canonical_pairs_added": 0, "scientific_calibration_pass": False}
    replay.write(output / "receipt.json", receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reviewer", choices=("reviewer-a", "reviewer-b"), default="reviewer-b")
    args = parser.parse_args()
    receipt = canary(json.loads(args.config.read_text()), args.original, args.output, args.reviewer)
    print(json.dumps({"case_id": "fresh-47", "original_batch_pre_reviewed": False,
                      "result": receipt["result"], "canonical_pairs_added": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
