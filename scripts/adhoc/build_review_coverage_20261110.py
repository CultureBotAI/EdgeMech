"""Build a corrected derived coverage view for issue #35, 2026-11-10.

Inputs: pinned legacy ledger, cohort, retrieval, cache and canonical adjudication.
Output: immutable JSON view under workspace; preserves historical artifacts.
"""
import argparse
import json
from pathlib import Path

from edgemech.review_coverage import build_coverage


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("ledger", "cohort", "retrieval", "cache", "adjudication", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    for name in ("ledger", "cohort", "retrieval", "adjudication"):
        parser.add_argument("--" + name + "-sha", required=True)
    result = build_coverage(**vars(parser.parse_args()))
    print(json.dumps({key: value for key, value in result.items()
                      if not key.endswith("_ids") or isinstance(value, int)}, indent=2))


if __name__ == "__main__":
    main()
