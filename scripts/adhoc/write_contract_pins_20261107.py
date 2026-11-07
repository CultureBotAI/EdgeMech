#!/usr/bin/env python3
"""Record reviewed CLAW contract bytes for #766/#767, 2026-11-07.

Input: clean detached CLAW checkout at the exact caller-supplied commit.
Output: packaged contract-pins.json (refuses replacement).
"""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

FILES = (
    "identity.py", "contract.py", "artifact.py", "native.py",
    "schema/bundle.json", "schema/artifact.json", "schema/native_assertion.json",
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claw-root", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
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
        "repository": "CultureBotAI/culturebotai-claw", "commit": commit,
        "package": "kg_microbe_curation", "files": {
            name: hashlib.sha256((args.claw_root / "src/kg_microbe_curation" / name).read_bytes()).hexdigest()
            for name in FILES
        },
    }
    with args.output.open("x") as handle:
        json.dump(document, handle, indent=2, sort_keys=True)
        handle.write("\n")


if __name__ == "__main__":
    main()
