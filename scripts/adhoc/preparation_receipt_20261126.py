#!/usr/bin/env python3
"""Retain one preparation command and its exact output without replacing attempts.

Purpose: issue228 provenance for the excluded native preparation canary.
Inputs: an explicit command argv and unique attempt label, or local files to pin.
Outputs: private stdout/stderr, UTC/resource receipt and append-only command ledger
under this checkout's .temp/restart-preparation-01; no scientific assessments.
UTC date: 2026-11-26. Author: native preparation worker, dispatch for units 2/3.
This is a receipt writer, not a launcher; it never creates agents or answers prompts.
Issue236 repair after coordinator triage; original issue228 executed bytes retained
at SHA256 96df338fd0f2c02b69d21a8870929e715df9c04edc0dcf651ed8fe576caf4c64.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import resource
import stat
import subprocess
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / ".temp/restart-preparation-01"
CACHE_DIRECTORIES = {
    "TMPDIR": "tmp", "UV_CACHE_DIR": "uv-cache", "XDG_CACHE_HOME": "cache",
    "PYTHONPYCACHEPREFIX": "pycache", "RUFF_CACHE_DIR": "ruff-cache",
    "UV_PYTHON_INSTALL_DIR": "python", "UV_PROJECT_ENVIRONMENT": "venv",
}


def utc():
    return datetime.now(timezone.utc).isoformat()


def checked_path(path, kind, *, base=None, absent=False, required=False):
    """Reject traversal, escapes and unsafe components without creating anything."""
    path = Path(path)
    if ".." in path.parts:
        raise ValueError("Traversal is forbidden")
    path = path.absolute()
    base = BASE if base is None else base
    path.relative_to(base)
    parts = path.relative_to(ROOT).parts
    current = ROOT
    for index, part in enumerate((None, *parts)):
        if part is not None:
            current = current / part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            if current == path and required:
                raise
            continue
        if stat.S_ISLNK(mode):
            raise ValueError("Symlink path component")
        final = index == len(parts)
        if final and absent:
            raise FileExistsError("Destination already exists")
        expected_directory = not final or kind == "directory"
        if not (stat.S_ISDIR(mode) if expected_directory else stat.S_ISREG(mode)):
            raise ValueError("Nonregular file or nondirectory path component")
    path.resolve(strict=False).relative_to(base.resolve(strict=False))
    return path


@contextmanager
def directory(path, *, create=False):
    """Walk through directory descriptors; never follow a substituted symlink."""
    path = checked_path(path, "directory", base=ROOT, required=not create)
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fd = os.open(ROOT, flags)
    try:
        for part in path.relative_to(ROOT).parts:
            if create:
                try:
                    os.mkdir(part, mode=0o700, dir_fd=fd)
                except FileExistsError:
                    pass
            child = os.open(part, flags, dir_fd=fd)
            os.close(fd)
            fd = child
        yield fd
    finally:
        os.close(fd)


@contextmanager
def regular_file(path, *, append=False, read=False):
    path = checked_path(path, "file", base=ROOT if read else BASE,
                        absent=not (append or read), required=read)
    flags = os.O_RDONLY if read else os.O_WRONLY | os.O_CREAT | (
        os.O_APPEND if append else os.O_EXCL)
    with directory(path.parent) as parent:
        fd = os.open(path.name, flags | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600, dir_fd=parent)
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise ValueError("Nonregular file descriptor")
            stream = os.fdopen(fd, "rb" if read else "ab" if append else "wb")
        except BaseException:
            os.close(fd)
            raise
        with stream:
            yield stream


def read_regular(path):
    with regular_file(path, read=True) as stream:
        data = stream.read(32 * 1024 * 1024 + 1)
    if len(data) > 32 * 1024 * 1024:
        raise ValueError("Private receipt input exceeds byte bound")
    return data


def pin(path):
    data = read_regular(path)
    return {"path": str(path), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}


def write_new(path, data):
    with regular_file(path) as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    if read_regular(path) != data:
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
    if not command:
        parser.error("Nonempty explicit command required")
    os.umask(0o077)
    output = BASE / "commands" / args.label
    # Preflight every writable endpoint before output, cache or ledger creation.
    checked_path(output, "directory", absent=True)
    ledger_path = checked_path(BASE / "command-outcomes.jsonl", "file")
    for name in CACHE_DIRECTORIES.values():
        checked_path(BASE / name, "directory")
    for name in ("stdout", "stderr", "receipt.json"):
        checked_path(output / name, "file", absent=True)
    with directory(BASE / "commands", create=True) as parent:
        os.mkdir(args.label, mode=0o700, dir_fd=parent)
    env = os.environ.copy()
    with regular_file(ledger_path, append=True) as ledger:
        for key, name in CACHE_DIRECTORIES.items():
            path = BASE / name
            with directory(path, create=True):
                pass
            env[key] = str(path)
        start = utc()
        clock = time.monotonic()
        error = None
        with regular_file(output / "stdout") as stdout, regular_file(output / "stderr") as stderr:
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
        ledger.write((json.dumps({**receipt, "label": args.label, "exit_code": code}) + "\n").encode())
        ledger.flush()
        os.fsync(ledger.fileno())
    print(json.dumps({"receipt": receipt, "exit_code": code, "error": error}))
    return code if code is not None and 0 <= code <= 255 else 1


if __name__ == "__main__":
    raise SystemExit(main())
