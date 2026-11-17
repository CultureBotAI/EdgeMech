#!/usr/bin/env python3
"""Read only the current launch's session/model identity from retained native logs.

2026-11-16, EdgeMech #180/#181/#187. Input: this worker's launcher events JSONL
and the native sessions directory. Output: identifiers, input hashes and matching
session path only; never messages, prompts, credentials or other session content.
No model/effort override, remote request, session continuation or scoring occurs.
The events file must be beneath this clone's private .temp directory. The native
log is selected by that file's sole thread.started UUID before reading any log.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import calibration_round_20261116 as rounds

UUID = re.compile(r"^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$")


def identify(root, events_path, sessions_root):
    rounds.require(Path(events_path).parts and Path(events_path).parts[0] == ".temp",
                   "Worker events must be private beneath .temp")
    event_file = rounds.safe(root, events_path)
    events_raw = event_file.read_bytes()
    threads = set()
    for line in events_raw.splitlines():
        try:
            event = json.loads(line)
        except (ValueError, UnicodeDecodeError):
            continue  # An active final line may not yet be complete.
        if event.get("type") == "thread.started":
            identifier = event.get("thread_id")
            rounds.require(isinstance(identifier, str) and UUID.fullmatch(identifier),
                           "Invalid own-session thread UUID")
            threads.add(identifier)
    rounds.require(len(threads) == 1, "Exactly one own worker thread identity required")
    session_id = next(iter(threads))
    rounds.require(sessions_root.is_dir() and not sessions_root.is_symlink(),
                   "Native sessions directory is unavailable or indirect")
    paths = [p for p in sessions_root.rglob(f"*{session_id}.jsonl") if p.is_file()]
    rounds.require(len(paths) == 1, "Exactly one matching native session log required")
    path = paths[0]
    rounds.require(not any(p.is_symlink() for p in (path, *path.parents)),
                   "Matching session path is indirect")
    raw = path.read_bytes()
    metadata_ids, models, efforts = set(), set(), set()
    for line in raw.splitlines():
        try:
            event = json.loads(line)
        except (ValueError, UnicodeDecodeError):
            continue
        payload = event.get("payload", {})
        if event.get("type") == "session_meta":
            metadata_ids.add(payload.get("id"))
        if event.get("type") == "turn_context":
            model = payload.get("model")
            if isinstance(model, str) and model.strip():
                models.add(model)
            effort = payload.get("effort", payload.get("reasoning_effort"))
            if isinstance(effort, str) and effort.strip():
                efforts.add(effort)
    rounds.require(metadata_ids == {session_id}, "Native session metadata differs from own thread")
    rounds.require(len(models) == 1 and next(iter(models)) not in {"unknown", "configured_default"},
                   "Actual model identity unavailable or changed within this session")
    return {"schema": "edgemech-worker-identity/v1", "session_id": session_id,
            "model": next(iter(models)), "observed_reasoning_efforts": sorted(efforts),
            "events": {"path": events_path, "sha256": hashlib.sha256(events_raw).hexdigest()},
            "native_session": {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest()},
            "scope": "observed_own_session_identity_only_not_scientific_independence"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--events", required=True)
    parser.add_argument("--sessions-root", type=Path, default=Path.home() / ".codex/sessions")
    args = parser.parse_args()
    result = identify(args.root.absolute(), args.events, args.sessions_root.absolute())
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
