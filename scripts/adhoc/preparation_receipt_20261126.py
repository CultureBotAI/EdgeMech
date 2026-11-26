#!/usr/bin/env python3
"""Retain one preparation command and its exact output without replacing attempts.

Purpose: issue228 provenance for the excluded native preparation canary.
Inputs: an explicit command argv and unique attempt label, or local files to pin.
Outputs: private stdout/stderr, UTC/resource receipt and append-only command ledger
under this checkout's .temp/restart-preparation-01; no scientific assessments.
UTC date: 2026-11-26. Author: native preparation worker, dispatch for units 2/3.
This is a receipt writer, not a launcher; it never creates agents or answers prompts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import resource
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / ".temp/restart-preparation-01"


def utc():
    return datetime.now(timezone.utc).isoformat()


def pin(path):
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}


def write_new(path, data):
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    if path.read_bytes() != data:
        raise OSError("Persisted byte readback differs")
    return pin(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("label")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if not args.label.replace("-", "").isalnum() or not args.command:
        parser.error("Unique alphanumeric/hyphen label and explicit command required")
    command = args.command[1:] if args.command[0] == "--" else args.command
    os.umask(0o077)
    output = BASE / "commands" / args.label
    if any(p.is_symlink() for p in (output, *output.parents)):
        raise ValueError("Symlink output path")
    output.mkdir(parents=True, exist_ok=False)
    env = os.environ.copy()
    for key, directory in {
        "TMPDIR": "tmp", "UV_CACHE_DIR": "uv-cache", "XDG_CACHE_HOME": "cache",
        "PYTHONPYCACHEPREFIX": "pycache", "RUFF_CACHE_DIR": "ruff-cache",
        "UV_PYTHON_INSTALL_DIR": "python", "UV_PROJECT_ENVIRONMENT": "venv",
    }.items():
        path = BASE / directory
        path.mkdir(exist_ok=True)
        env[key] = str(path)
    start = utc()
    clock = time.monotonic()
    error = None
    with (output / "stdout").open("xb") as stdout, (output / "stderr").open("xb") as stderr:
        try:
            result = subprocess.run(command, cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                                    stdout=stdout, stderr=stderr, timeout=1800, check=False)
            code = result.returncode
        except (OSError, subprocess.TimeoutExpired) as exc:
            code = None
            error = f"{type(exc).__name__}: {exc}"
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    record = {
        "classification": "EXCLUDED_PREPARATION_CANARY", "scientific_review_coverage": 0,
        "occurrence": None, "A_B_attempt": False, "label": args.label,
        "started_at_utc": start, "finished_at_utc": utc(), "command": command,
        "cwd": str(ROOT), "exit_code": code, "error": error,
        "elapsed_seconds": time.monotonic() - clock,
        "child_peak_rss_platform_units": usage.ru_maxrss,
        "rss_unit": "bytes on macOS; peak child process, not worker total or pool sum",
        "helper": pin(Path(__file__)),
        "stdout": pin(output / "stdout"), "stderr": pin(output / "stderr"),
    }
    receipt = write_new(output / "receipt.json", (json.dumps(record, indent=2) + "\n").encode())
    with (BASE / "command-outcomes.jsonl").open("a") as ledger:
        ledger.write(json.dumps({**receipt, "label": args.label, "exit_code": code}) + "\n")
        ledger.flush()
        os.fsync(ledger.fileno())
    print(json.dumps({"receipt": receipt, "exit_code": code, "error": error}))
    return code if code is not None and 0 <= code <= 255 else 1


if __name__ == "__main__":
    raise SystemExit(main())
