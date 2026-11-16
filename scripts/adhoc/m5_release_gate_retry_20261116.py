#!/usr/bin/env python3
"""Record an environment-only retry after M5 gate scratch-context failures.

2026-11-16 provenance: the first standard gate put pytest scratch inside KG,
changing path normalization and Git discovery. Use durable scratch outside any
checkout; preserve the old record and all failures. No gate, assertions, source,
tox selectors, or filesystem guards are changed. Required results stay in OUT.
"""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def durable_scratch(path):
    """Reject exact temporary roots and every descendant after resolving aliases (#162)."""
    scratch = path.resolve(strict=True)
    forbidden = (Path("/tmp").resolve(), Path("/private/tmp"), Path("/private/var/folders"))
    if not scratch.is_dir() or any(scratch == root or scratch.is_relative_to(root) for root in forbidden):
        raise ValueError("Use a durable existing scratch directory")
    return scratch


def main():
    """Write a versioned environment record after verifying the scratch boundary."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--previous", required=True, type=Path)
    parser.add_argument("--scratch-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        scratch = durable_scratch(args.scratch_root)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    probe = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=scratch,
                           text=True, capture_output=True, check=False)
    if probe.returncode != 128 or "not a git repository" not in probe.stderr:
        parser.error("Scratch must be outside all Git checkouts")
    before = args.previous.read_bytes()
    environment = json.loads(before)
    previous_tmp = environment["set"]["TMPDIR"]
    environment["set"]["TMPDIR"] = str(scratch)
    args.output.mkdir(parents=True, exist_ok=False)
    destination = args.output / "environment.json"
    destination.write_text(json.dumps(environment, indent=2) + "\n")
    receipt = {"previous": str(args.previous), "previous_sha256": hashlib.sha256(before).hexdigest(),
               "environment": str(destination),
               "environment_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
               "delta": {"set.TMPDIR": {"before": previous_tmp, "after": str(scratch)}},
               "git_probe": {"returncode": probe.returncode, "stderr": probe.stderr.strip()},
               "helper_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "scope": "Environment-only preparation; no test or gate executed."}
    (args.output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
