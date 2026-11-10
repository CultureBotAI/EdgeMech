"""Inspect original citation fields for a retrieval canary, 2026-11-09.

Input: prepared Parquet shard(s). Output: first five distinct publication fields
(or DOI-bearing fields with --doi) for the 17M review PR. No support is inferred.
"""
import argparse
import re

import pyarrow.parquet as pq

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("paths", nargs="+")
parser.add_argument("--doi", action="store_true")
args = parser.parse_args()
seen = set()
for path in args.paths:
    values = pq.read_table(path, columns=["publications"]).column(0).to_pylist()
    for value in values:
        if not value or value in seen or (args.doi and not re.search(r"10\.\d{4,9}/", value)):
            continue
        seen.add(value)
        print(value)
        if len(seen) == 5:
            raise SystemExit(0)
