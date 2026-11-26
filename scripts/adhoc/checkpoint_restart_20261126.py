#!/usr/bin/env python3
"""Persist an owned preparation checkpoint, preserving each previous state.

Purpose: resumable coordinator metadata; never scientific assessment or approval.
Inputs: explicit private campaign root, existing owned state file and expected
SHA256, a JSON object of updates, and a unique checkpoint basename.
Outputs: exclusive before/after checkpoint files and an atomic current-state
replacement. All invocation/runtime bindings stay private. UTC date: 2026-11-26.
Issues #228/#239: new parameterized successor, not the producer of historical
inline recovery checkpoints. Original executed producers/receipts remain private.
Do not use this helper to recreate historical events or repeat a live canary.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from plugins.lock_manager import LockManager

from edgemech.census import _json, _read_handle

MAX_BYTES = 2 * 1024 * 1024
OWNED = {"COORDINATOR-ACCEPTANCE.json", "COORDINATOR-PROGRESS.json", "FIRST-WORKER.json"}


def read(path):
    with _read_handle(path) as handle:
        raw = handle.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("checkpoint input too large")
    return raw


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def directory(path):
    if not path.is_absolute() or ".." in path.parts:
        raise ValueError("require absolute directory without traversal")
    for part in (path, *path.parents):
        if part.is_symlink() or not part.is_dir():
            raise ValueError("checkpoint directory must be existing and nonsymlink")
    return path


def exclusive(path, raw):
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    if read(path) != raw:
        raise ValueError("checkpoint readback mismatch")


def flush(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def checkpoint(campaign, current_name, expected_sha256, updates_path, name):
    directory(campaign)
    snapshots = directory(campaign / "coordinator-checkpoints")
    if current_name not in OWNED or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,95}", name):
        raise ValueError("invalid owned state or unique checkpoint name")
    # One per-state owner covers both comparisons and the final replacement.
    # This private metadata lease never spans tests, hooks, commits or workers.
    manager = LockManager({"locks_dir": campaign / ".coordinator-state-locks",
                           "my_id": f"restart-checkpoint-{os.getpid()}"})
    with manager.lock(current_name, "persist-preparation-checkpoint", timeout=300):
        return _checkpoint_locked(campaign, snapshots, current_name,
                                  expected_sha256, updates_path, name)


def _checkpoint_locked(campaign, snapshots, current_name, expected_sha256, updates_path, name):
    current = campaign / current_name
    original, updates_raw = read(current), read(updates_path)
    if sha(original) != expected_sha256:
        raise ValueError("current state changed; preserve and replan")
    state, updates = _json(original), _json(updates_raw)
    if not isinstance(state, dict) or not isinstance(updates, dict):
        raise ValueError("state and updates must be JSON objects")
    record = {**state, **updates}
    if (record.get("scientific_review_coverage") != 0
            or type(record.get("scientific_review_coverage")) is not int
            or record.get("queue_A_count") is not None or record.get("queue_B_count") is not None
            or record.get("A_count") is not None or record.get("B_count") is not None
            or record.get("full_target_frozen", False) is not False
            or record.get("baseline_cutoff_frozen", False) is not False
            or record.get("full_AB_frozen", False) is not False):
        raise ValueError("preparation checkpoint cannot promote scientific gates")
    record["checkpoint_producer"] = {
        "sha256": sha(read(Path(__file__))), "utc": datetime.now(timezone.utc).isoformat(),
        "previous_state_sha256": expected_sha256, "updates_sha256": sha(updates_raw),
        "historical_execution_recreated": False,
    }
    encoded = (json.dumps(record, indent=2, allow_nan=False) + "\n").encode()
    before, after = snapshots / f"{name}-before.json", snapshots / f"{name}.json"
    pending = campaign / f".{name}.pending"
    # Complete validation precedes writes; every attempted filename is exclusive.
    # Partial attempts remain for inspection, never silently removed or retried.
    exclusive(before, original)
    exclusive(after, encoded)
    flush(snapshots)
    exclusive(pending, encoded)
    flush(campaign)
    if read(current) != original:
        raise ValueError("current state changed during checkpoint; pending bytes retained")
    os.replace(pending, current)
    flush(campaign)
    if read(current) != encoded:
        raise ValueError("current-state readback mismatch; checkpoint retained")
    return {"checkpoint_sha256": sha(encoded), "previous_state_sha256": sha(original)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign-root", type=Path, required=True)
    parser.add_argument("--current", choices=sorted(OWNED), required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--updates", type=Path, required=True)
    parser.add_argument("--name", required=True)
    args = parser.parse_args()
    os.umask(0o077)
    print(json.dumps(checkpoint(args.campaign_root, args.current, args.expected_sha256,
                                args.updates, args.name), sort_keys=True))


if __name__ == "__main__":
    main()
