#!/usr/bin/env python3
"""Run bounded/full exact-scope census for CLAW #767; 2026-11-07.

Inputs: pinned KG snapshot, pinned native manifests, unique output directory.
Outputs: immutable verified census and adjacent timing/resource receipt.
Run once with --limit before the same command path without a limit.
"""

from __future__ import annotations

import argparse
import json
import resource
import sys
import time
from pathlib import Path

import duckdb

import edgemech.census
from edgemech.census import run_census
from edgemech.pins import check_contracts
from edgemech.storage.parquet import file_hash


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--native-export", type=Path, action="append", required=True)
    parser.add_argument("--native-sha256", action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--workers", type=int, choices=range(1, 5), default=1)
    args = parser.parse_args()
    pins = check_contracts()
    started = time.perf_counter()
    manifest_path = run_census(
        args.snapshot, args.native_export, args.output, args.source_sha256, args.limit,
        expected_native_manifest_sha256=args.native_sha256,
        workers=args.workers,
    )
    seconds = time.perf_counter() - started
    manifest = json.loads(manifest_path.read_bytes())
    partitions = manifest["partitions"]
    if partitions:
        with duckdb.connect(config={"memory_limit": "256MB", "threads": "2"}) as connection:
            stored = connection.from_parquet(
                [str(manifest_path.parent / item["path"]) for item in partitions],
                hive_partitioning=False,
            ).aggregate("classification,count(*) AS n", "classification").fetchall()
        if dict(stored) != {key: value for key, value in manifest["counts"].items() if value}:
            raise ValueError("Persisted Parquet counters differ from census manifest")
        if any((manifest_path.parent / item["path"]).stat().st_size <= 0 for item in partitions):
            raise ValueError("Census did not persist nonempty partitions")
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    receipt = {
        "format": "edgemech-census-run/v1", "manifest_sha256": file_hash(manifest_path),
        "census_source_sha256": file_hash(Path(edgemech.census.__file__)),
        "launcher_sha256": file_hash(Path(__file__)),
        "contract_pins": pins, "selected_rows": manifest["source"]["selected_rows"],
        "source_rows": manifest["source"]["source_rows"], "counts": manifest["counts"],
        "native_accounting": manifest["native_accounting"],
        "partition_files": len(partitions), "parquet_bytes": sum(p["bytes"] for p in partitions),
        "elapsed_seconds_including_verification": seconds,
        "peak_rss_bytes": peak if sys.platform == "darwin" else peak * 1024,
        "native_validation_workers": args.workers,
        "peak_rss_scope": "parent_process_excludes_workers",
        "scientific_approvals_created": 0,
    }
    path = manifest_path.parent.with_name(manifest_path.parent.name + ".run.json")
    with path.open("x") as handle:
        json.dump(receipt, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"manifest": str(manifest_path), "receipt": str(path),
                      "rows": receipt["selected_rows"], "counts": receipt["counts"]}, sort_keys=True))


if __name__ == "__main__":
    main()
