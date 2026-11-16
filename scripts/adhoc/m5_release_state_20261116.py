#!/usr/bin/env python3
"""Record the authorized M5 release track's commands and durable progress.

2026-11-16: all logs and state remain beneath the isolated evidence checkout.
This launcher runs one command at a time without shell interpretation; receipts
from the producer and finalizer remain the scientific/provenance evidence.
"""

import argparse
import datetime
import fcntl
import hashlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / ".temp/m5-worker-run-20261116"


def _save(state):
    """Atomically replace progress and retain individual execution records."""
    state["commands"] = sorted(
        (json.loads(path.read_text()) for path in (OUTPUT / "commands").glob("*.json")),
        key=lambda entry: entry["started_at"],
    )
    state["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    for path in (ROOT / ".temp/m5-release-progress.json", OUTPUT / "progress.json"):
        temporary = path.with_suffix(f".{os.getpid()}.pending")
        temporary.write_text(json.dumps(state, indent=2) + "\n")
        temporary.replace(path)
    lines = ["# M5 release verification", "", f"Phase: {state['phase']}",
             f"Updated: {state['updated_at']}", f"Launcher PID: {state['pid']}", "",
             "Published release verified: false", ""]
    for entry in state.get("commands", []):
        lines.append(f"- {entry['label']}: {entry['status']}; PID {entry.get('child_pid')}; "
                     f"exit {entry.get('exit_code')}; log {entry['log']}")
    lines.extend(["", "Blockers:", *[f"- {item}" for item in state.get("blockers", [])]])
    if state.get("process_observation"):
        observed = state["process_observation"]
        lines.extend(["", f"External process: {observed['status']}",
                      f"Evidence: {observed['path']}", f"SHA256: {observed['sha256']}"])
    for path in (ROOT / ".temp/M5_RELEASE_PROGRESS.md", OUTPUT / "M5_RELEASE_PROGRESS.md"):
        temporary = path.with_suffix(f".{os.getpid()}.pending")
        temporary.write_text("\n".join(lines) + "\n")
        temporary.replace(path)


def save(updates):
    """Apply explicit metadata changes to current state while holding the aggregate lock."""
    with (OUTPUT / "progress.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        progress = ROOT / ".temp/m5-release-progress.json"
        state = json.loads(progress.read_text()) if progress.exists() else {}
        state.update(updates)
        _save(state)
        return state


def save_command(path, entry):
    """Atomically publish one independent launcher's current execution record."""
    temporary = path.with_suffix(f".{os.getpid()}.pending")
    temporary.write_text(json.dumps(entry, indent=2) + "\n")
    temporary.replace(path)


def main():
    """Run a bounded task command, preserving its argv, PID, output and status."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", required=True)
    parser.add_argument("--label")
    parser.add_argument("--cwd", type=Path, default=ROOT)
    parser.add_argument("--blocker", action="append")
    parser.add_argument("--results", type=Path)
    parser.add_argument("--observe-process", type=Path)
    parser.add_argument("--process-status")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    os.umask(0o077)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    state = {"phase": args.phase, "pid": os.getpid()}
    if args.blocker:
        state["blockers"] = args.blocker
    if args.results:
        state["results"] = json.loads(args.results.read_text())
    if args.observe_process:
        if not args.process_status:
            parser.error("--process-status required for an external process observation")
        raw = args.observe_process.read_bytes()
        state["process_observation"] = {
            "path": str(args.observe_process.absolute()), "sha256": hashlib.sha256(raw).hexdigest(),
            "status": args.process_status, "record": json.loads(raw),
        }
    state = save(state)
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        return 0
    if not args.label:
        parser.error("--label required for command")
    logs = OUTPUT / "commands"
    logs.mkdir(exist_ok=True)
    logfile = logs / (args.label + ".log")
    command_record = logs / (args.label + ".json")
    entry = {"label": args.label, "argv": command, "cwd": str(args.cwd),
             "log": str(logfile), "status": "running", "started_at": state["updated_at"]}
    with logfile.open("x") as log:
        child = subprocess.Popen(command, cwd=args.cwd, stdout=log, stderr=subprocess.STDOUT)
        entry["child_pid"] = child.pid
        save_command(command_record, entry)
        save({})
        code = child.wait()
    entry.update(exit_code=code, status="passed" if code == 0 else "failed")
    save_command(command_record, entry)
    save({})
    print(json.dumps(entry))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
