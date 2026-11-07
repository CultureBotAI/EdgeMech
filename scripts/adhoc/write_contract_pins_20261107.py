#!/usr/bin/env python3
"""Record reviewed CLAW contract bytes for #766/#767, 2026-11-07.

Input: clean detached CLAW checkout at the exact caller-supplied commit.
Output: packaged contract-pins.json (replacement requires --replace).
"""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

PACKAGES = {
    "kg_microbe_curation": (
        "__init__.py", "identity.py", "contract.py", "ledger.py", "artifact.py", "native.py",
        "schema/bundle.json", "schema/artifact.json", "schema/native_assertion.json",
    ),
    "kg_microbe_reviews": ("__init__.py",),
    "kg_microbe_governance": (
        "__init__.py", "artifacts/scripts/record_review.py", "artifacts/schema/record_review.yaml",
        "artifacts/__init__.py", "artifacts/scripts/__init__.py",
        "artifacts/scripts/check_vendored_sync.py",
    ),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claw-root", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    commit = subprocess.check_output(
        ["git", "-C", str(args.claw_root), "rev-parse", "HEAD"], text=True,
    ).strip()
    if commit != args.commit or len(commit) != 40:
        raise ValueError("CLAW checkout differs from reviewed commit")
    dirty = subprocess.check_output(
        ["git", "-C", str(args.claw_root), "status", "--porcelain"], text=True,
    )
    if dirty:
        raise ValueError("CLAW contract checkout must be clean")
    document = {
        "format": "edgemech-contract-pins/v2",
        "repository": "CultureBotAI/culturebotai-claw", "commit": commit,
        "packages": {
            package: {
                name: hashlib.sha256((args.claw_root / "src" / package / name).read_bytes()).hexdigest()
                for name in names
            }
            for package, names in PACKAGES.items()
        },
    }
    with args.output.open("w" if args.replace else "x") as handle:
        json.dump(document, handle, indent=2, sort_keys=True)
        handle.write("\n")


if __name__ == "__main__":
    main()
