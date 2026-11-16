#!/usr/bin/env python3
"""Hash every nested artifact in the two explicitly retained v3 replay stages.

2026-11-16: read-only preservation check for M5 release verification. This
walk is confined to the named evidence roots and includes hidden cache files.
"""

import argparse
import hashlib
import json
from pathlib import Path

RETAINED = Path(
    "/Users/marcin/agent-work/EdgeMech/retained-pr135-pr1867-20261116/"
    "kg-candidate/data/validation-bactotraits-130"
)


def inventory():
    """Verify all receipt-bound bytes and inventory every nested regular file."""
    result = {}
    for name in ("baseline-v3-20261116", "candidate-v3-20261116"):
        root = RETAINED / name
        files = {}
        for path in sorted(root.rglob("*")):
            if path.is_symlink():
                raise ValueError(f"Unexpected symlink: {path}")
            if path.is_file():
                raw = path.read_bytes()
                files[str(path.relative_to(root))] = {
                    "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)
                }
        receipt = json.loads((root / "receipt.json").read_text())
        for relative, expected in receipt["artifacts"].items():
            if files[relative] != expected:
                raise ValueError(f"Retained receipt artifact differs: {name}/{relative}")
        result[name] = files
    return result


def main():
    """Save a new manifest or compare all current retained files with an old one."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--compare", type=Path)
    args = parser.parse_args()
    result = inventory()
    if args.compare and json.loads(args.compare.read_text()) != result:
        raise ValueError("Retained evidence inventory changed")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        stream.write(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"files": sum(map(len, result.values())), "unchanged": bool(args.compare)}))


if __name__ == "__main__":
    main()
