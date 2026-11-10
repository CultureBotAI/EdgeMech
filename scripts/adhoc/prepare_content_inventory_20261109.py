"""Prepare pinned review inputs, not decisions (2026-11-09).

Inputs: census manifest + SHA-256 and its pinned snapshot. Output: new workspace
inventory directory. Serves the 17M plan review/implementation PR. One partition
is the canary; --all uses exactly the same launcher and processing path.
"""
import argparse
import json
from pathlib import Path

from edgemech.content_inventory import prepare_inventory

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    result = prepare_inventory(args.manifest, args.sha256, args.output,
                               partition_limit=None if args.all else 1)
    print(json.dumps({key: result[key] for key in (
        "rows", "complete_population", "scientific_reviews", "elapsed_seconds", "profile"
    )}, indent=2))
