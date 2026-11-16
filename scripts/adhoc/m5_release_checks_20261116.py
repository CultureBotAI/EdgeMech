#!/usr/bin/env python3
"""Run one recorded M5 KG check through the prepared offline environment.

Provenance: consumes m5_release_gate_setup_20261116.py's environment record.
This launcher records operational execution only. The repository's unchanged
run_pr_gates.py remains responsible for final-candidate and full-suite gates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


def write(path: Path, record: dict) -> None:
    """Atomically update this invocation's live receipt."""
    pending = path.with_suffix(".pending")
    pending.write_text(json.dumps(record, indent=2) + "\n")
    pending.replace(path)


def main() -> int:
    """Run a single explicitly supplied command with durable logs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--environment-record", required=True, type=Path)
    parser.add_argument("--kg-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("Supply a command after --")
    args.output.mkdir(parents=True, exist_ok=False)
    specification = json.loads(args.environment_record.read_text())
    environment = dict(os.environ)
    for key in list(environment):
        if key in specification["unset"] or any(key.startswith(p) for p in specification["unset_prefixes"]):
            environment.pop(key)
    environment.update(specification["set"])
    record = {"started_at": datetime.now(timezone.utc).isoformat(), "cwd": str(args.kg_root),
              "command": command, "environment_record": str(args.environment_record),
              "environment_record_sha256": hashlib.sha256(args.environment_record.read_bytes()).hexdigest(),
              "helper_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "status": "running"}
    receipt = args.output / "receipt.json"
    log_path = args.output / "command.log"
    started = time.monotonic()
    with log_path.open("x") as log:
        process = subprocess.Popen(command, cwd=args.kg_root, env=environment, stdout=log, stderr=subprocess.STDOUT)
        record["pid"] = process.pid
        write(receipt, record)
        print(json.dumps({"pid": process.pid, "receipt": str(receipt), "log": str(log_path)}), flush=True)
        code = process.wait()
    record.update(status="complete" if code == 0 else "failed", exit_code=code,
                  completed_at=datetime.now(timezone.utc).isoformat(), seconds=round(time.monotonic() - started, 3),
                  log_sha256=hashlib.sha256(log_path.read_bytes()).hexdigest())
    write(receipt, record)
    print(json.dumps(record, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
