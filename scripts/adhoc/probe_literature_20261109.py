"""Run one anonymous literature canary for the 17M plan PR (2026-11-09).

Inputs: explicit DOI/PMID and new output directory. Outputs: retained raw response
and hash-bound retrieval manifest. Does not generate supporting quotes or verdicts.
"""
import argparse
import json
from pathlib import Path

from edgemech.literature_probe import probe

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--identifier", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(probe(args.identifier, args.output), indent=2))
