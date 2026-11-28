#!/usr/bin/env python3
"""Create one isolated source/provenance worktree, never launch a worker.

Purpose: the reviewed Boundary4 separate-distribution choice, 2026-11-28 UTC.
Inputs: explicit CLAW/owner/destination roots, exact owner/base commits and branch.
Outputs: a new Git worktree and exclusive private invocation/completion receipts.
Issues #228/#238/#220. New prospective producer; no historical action replay.
Preserves the executed preparation branch and its canonical pairs. No provider,
scientific save, prompt input, publication, merge or environment change is made.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from plugins.lock_manager import LockManager
from plugins.repository_settings import RepositorySettings, merged_repository_environment

ORIGIN = "https://github.com/CultureBotAI/EdgeMech.git"


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args],
                                   text=True, timeout=60).strip()


def directory(path):
    if not path.is_absolute() or ".." in path.parts:
        raise ValueError("absolute nonsymlink directory required")
    if any(p.is_symlink() or not p.is_dir() for p in (path, *path.parents)):
        raise ValueError("absolute nonsymlink directory required")
    return path


def receipt(path, value):
    raw = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def verify_owner(owner, expected):
    if git(owner, "remote", "get-url", "origin") != ORIGIN:
        raise ValueError("owner origin differs")
    if git(owner, "rev-parse", "HEAD") != expected:
        raise ValueError("owner head changed")


def create(args):
    owner, claw = directory(args.owner), directory(args.claw)
    directory(args.destination.parent)
    directory(args.output.parent)
    for value in (args.expected_head, args.base):
        if not re.fullmatch(r"[0-9a-f]{40}", value):
            raise ValueError("exact commit required")
    if not re.fullmatch(r"campaign/[a-z0-9-]+", args.branch):
        raise ValueError("owned campaign branch required")
    for path in (args.destination, args.output):
        if not path.is_relative_to(owner / ".temp/restart-20261120"):
            raise ValueError("new paths must be inside the owned durable campaign tree")
        if path.exists() or path.is_symlink():
            raise ValueError("attempt exists; preserve and inspect, never overwrite")
    verify_owner(owner, args.expected_head)
    if git(owner, "rev-parse", args.base + "^{commit}") != args.base:
        raise ValueError("base commit differs")
    target = RepositorySettings.from_environment(
        environ=merged_repository_environment(claw / ".env")).get_target("edgemech")
    canonical_head = target.open().head.commit.hexsha
    plan = {"utc": datetime.now(timezone.utc).isoformat(),
            "owner": str(owner), "owner_head": args.expected_head,
            "base": args.base, "branch": args.branch, "destination": str(args.destination),
            "canonical_head": canonical_head, "helper_sha256": hashlib.sha256(
                Path(__file__).read_bytes()).hexdigest(), "scientific_review_coverage": 0}
    if not args.apply:
        return {**plan, "mode": "plan", "mutation": False}
    args.output.mkdir(mode=0o700)
    receipt(args.output / "plan.json", plan)
    os.environ["OPENCLAW_ORCHESTRATION_ROOT"] = str(claw)
    try:
        with LockManager().lock("edgemech", "create-isolated-science-worktree", timeout=300):
            verify_owner(owner, args.expected_head)
            if target.open().head.commit.hexsha != canonical_head:
                raise ValueError("canonical owner changed before transition")
            if args.destination.exists() or args.destination.is_symlink():
                raise ValueError("destination appeared before transition")
            git(owner, "worktree", "add", "-b", args.branch, str(args.destination), args.base)
        if git(args.destination, "rev-parse", "HEAD") != args.base:
            raise ValueError("new worktree head differs")
        if git(args.destination, "status", "--porcelain"):
            raise ValueError("new worktree is not clean")
        result = {**plan, "finished_at": datetime.now(timezone.utc).isoformat(),
                  "status": "created", "worker_input": False, "canonical_save": False}
        receipt(args.output / "completion.json", result)
        return result
    except BaseException as error:
        receipt(args.output / "failure.json", {"utc": datetime.now(timezone.utc).isoformat(),
                                               "error_type": type(error).__name__,
                                               "partial_worktree_preserved": True})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("owner", "claw", "destination", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    for name in ("expected-head", "base", "branch"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--apply", action="store_true")
    os.umask(0o077)
    print(json.dumps(create(parser.parse_args()), sort_keys=True))


if __name__ == "__main__":
    main()
