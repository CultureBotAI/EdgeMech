#!/usr/bin/env python3
"""Export verified M5 row/finalizer evidence beneath this invocation's output root.

2026-11-16: preserve original receipt paths and all nested files unchanged. The
compact result is suitable for Git; complete private receipts remain local.
"""

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KG = ROOT.parent / "m5-kg-bactotraits-release-20261116"
STAGES = (
    "baseline-m5-20261116-r1",
    "candidate-m5-20261116-r1",
    "candidate-finalized-m5-20261116-r1",
)


def identity(path):
    """Identify one bounded evidence file using exact persisted bytes."""
    raw = path.read_bytes()
    return {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def verify(stage):
    """Reject any changed or escaping receipt-bound artifact before export."""
    receipt = json.loads((stage / "receipt.json").read_text())
    for name, expected in receipt["artifacts"].items():
        path = (stage / name).resolve()
        if not path.is_relative_to(stage.resolve()) or identity(path) != expected:
            raise ValueError(f"Receipt artifact differs: {path}")
    return receipt


def main():
    """Copy only the named new stages to an exclusive result root and verify readback."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--plan", action="store_true")
    action.add_argument("--run", action="store_true")
    args = parser.parse_args()
    output = args.output.absolute()
    required = ROOT / ".temp/m5-worker-run-20261116"
    if not output.is_relative_to(required) or output.exists():
        raise ValueError("Use a fresh directory beneath this invocation's required output root")
    results = {}
    receipts = {}
    for name in STAGES:
        stage = KG / "data/validation-bactotraits-130" / name
        receipt = verify(stage)
        receipts[name] = receipt
        results[name] = {
            "original_receipt": str(stage / "receipt.json"),
            "receipt": identity(stage / "receipt.json"),
            "producer_revision": receipt["git_revision"],
            "edges": receipt.get("all_edge_count", receipt.get("finalized_edge_count")),
            "nodes": receipt.get("node_count", receipt.get("finalized_node_count")),
            "quarantine_rows": receipt["quarantine_rows"],
            "finalization_run": receipt["finalization_run"],
            "artifacts": receipt["artifacts"],
        }
    baseline, candidate, finalized = [receipts[name] for name in STAGES]
    if not (
        baseline["mode"] == "baseline"
        and baseline["git_revision"] == "ef27b97a0b450767da54235c6105b5250c178adc"
        and (baseline["all_edge_count"], baseline["node_count"]) == (21, 22)
        and candidate["mode"] == "candidate"
        and (candidate["all_edge_count"], candidate["node_count"], candidate["quarantine_rows"]) == (0, 0, 1)
        and (finalized["finalized_edge_count"], finalized["finalized_node_count"], finalized["quarantine_rows"]) == (0, 0, 1)
        and finalized["finalization_run"] is True
        and finalized["merged_graph_verified"] is False
        and finalized["published_release_verified"] is False
        and baseline["shared_inputs"] == candidate["shared_inputs"] == finalized["shared_inputs"]
        and candidate["baseline_receipt"] == finalized["baseline_receipt"]
        and candidate["baseline_receipt"]["sha256"] == results[STAGES[0]]["receipt"]["sha256"]
        and finalized["candidate_receipt"]["sha256"] == results[STAGES[1]]["receipt"]["sha256"]
    ):
        raise ValueError("Fresh pair/finalization semantics or receipt links differ")
    summary = {
        "profile": "m5-bactotraits-release-verification/v1",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "export_helper_sha256": identity(Path(__file__))["sha256"],
        "fresh_baseline_candidate_pair_verified": True,
        "bounded_source_finalization_verified": True,
        "merged_graph_verified": False,
        "published_release_verified": False,
        "source_row": 8521,
        "bacdive_id": 17851,
        "scientific_claim_resolved": False,
        "neighboring_rows_quarantined": False,
        "results": results,
    }
    if args.plan:
        print(json.dumps({"ready": True, "output": str(output), "stages": list(results)}))
        return
    output.mkdir(mode=0o700)
    for name in STAGES:
        source = KG / "data/validation-bactotraits-130" / name
        destination = output / name
        shutil.copytree(source, destination)
        verify(destination)
        for path in source.rglob("*"):
            if path.is_symlink():
                raise ValueError(f"Unexpected symlink in a new stage: {path}")
            if path.is_file() and identity(path) != identity(destination / path.relative_to(source)):
                raise ValueError(f"Export differs: {path}")
    with (output / "results.json").open("x") as stream:
        stream.write(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"results": str(output / "results.json"), **identity(output / "results.json")}))


if __name__ == "__main__":
    main()
