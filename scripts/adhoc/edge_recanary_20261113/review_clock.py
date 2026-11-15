"""Measure real per-edge reading/adjudication time for recanary PR76, 2026-11-13.

Inputs: private edge packets and separately authored decisions. Outputs: private
immutable decisions and begin/finish receipts. Begin must precede packet reading;
finish persists the decision before stopping the timer. This does not time replay.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path


def _identity(axis, edge_id):
    if axis not in {"source", "scientific"} or not re.fullmatch(r"[A-Za-z0-9_-]+", str(edge_id)):
        raise ValueError("Use source/scientific axis and a safe edge identifier")
    return str(edge_id)


def _write(path, value, *, exclusive=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x" if exclusive else "w") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def begin_review(root, axis, edge_id, packet_path):
    """Persist start BEFORE reading the packet; return packet and timer receipt."""
    edge_id = _identity(axis, edge_id)
    root, packet_path = Path(root), Path(packet_path).resolve()
    timer = root / "timing" / axis / f"{edge_id}.json"
    if timer.exists():
        raise ValueError("Review already started; finish or explicitly document abandonment")
    started = time.monotonic_ns()
    receipt = {
        "axis": axis,
        "edge_id": edge_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "started_monotonic_ns": started,
        "packet_path": str(packet_path),
        "status": "started",
    }
    _write(timer, receipt, exclusive=True)
    raw = packet_path.read_bytes()
    receipt["packet_sha256"] = hashlib.sha256(raw).hexdigest()
    _write(timer, receipt)
    return {"timer": receipt, "packet": json.loads(raw)}


def finish_review(root, axis, edge_id, decision):
    """Persist the independently authored decision, then stop the original timer."""
    edge_id = _identity(axis, edge_id)
    root = Path(root)
    timer = root / "timing" / axis / f"{edge_id}.json"
    receipt = json.loads(timer.read_text())
    if receipt["status"] != "started" or receipt["axis"] != axis or receipt["edge_id"] != edge_id:
        raise ValueError("Expected the matching active review timer")
    raw = Path(receipt["packet_path"]).read_bytes()
    if hashlib.sha256(raw).hexdigest() != receipt["packet_sha256"]:
        raise ValueError("Review packet changed after reading began")
    destination = root / "decisions" / axis / f"{edge_id}.json"
    _write(destination, decision, exclusive=True)
    stopped = time.monotonic_ns()
    if stopped < receipt["started_monotonic_ns"]:
        raise ValueError("Monotonic clock moved backwards; cannot measure this review")
    receipt.update(
        status="finished",
        stopped_at=datetime.now(timezone.utc).isoformat(),
        stopped_monotonic_ns=stopped,
        elapsed_seconds=(stopped - receipt["started_monotonic_ns"]) / 1e9,
        decision_path=str(destination),
        decision_sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),
    )
    _write(timer, receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["begin", "finish"])
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--axis", choices=["source", "scientific"], required=True)
    parser.add_argument("--edge-id", required=True)
    parser.add_argument("--packet", type=Path)
    parser.add_argument("--decision", type=Path)
    args = parser.parse_args()
    if args.action == "begin":
        if args.packet is None:
            parser.error("--packet is required for begin")
        result = begin_review(args.root, args.axis, args.edge_id, args.packet)
    else:
        if args.decision is None:
            parser.error("--decision is required for finish")
        result = finish_review(
            args.root, args.axis, args.edge_id, json.loads(args.decision.read_text())
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
