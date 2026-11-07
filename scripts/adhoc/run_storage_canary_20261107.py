#!/usr/bin/env python3
"""Migrate and benchmark a pinned SQLite ledger for CLAW #766/#951; 2026-11-07.

Inputs: immutable SQLite/export directory, expected SHA256/row count, new output.
Outputs: verified immutable Parquet store plus timing/memory/input-output receipt.
Use this same launcher for one canary before any benchmark parameter batch.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import resource
import sqlite3
import sys
import time
from pathlib import Path

from edgemech import storage
from edgemech.storage.parquet import file_hash


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--export", type=Path, required=True)
    parser.add_argument("--ledger-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-rows", type=int, default=1000)
    parser.add_argument("--buckets", type=int, default=16)
    parser.add_argument("--row-group-size", type=int, default=8192)
    args = parser.parse_args()
    args.output = args.output.absolute()
    if file_hash(args.ledger) != args.ledger_sha256:
        raise ValueError("SQLite input differs from explicit canary pin")
    if args.output.exists() or args.output.is_symlink():
        raise ValueError("Refusing to replace prior run output")
    with sqlite3.connect(args.ledger.resolve().as_uri() + "?mode=ro", uri=True) as source:
        selected = source.execute(
            "SELECT occurrence_id FROM occurrences ORDER BY row_number LIMIT 1"
        ).fetchone()[0]
    args.output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    manifest = storage.migrate_sqlite(
        args.ledger, args.export, args.output / "store",
        buckets=args.buckets, row_group_size=args.row_group_size,
    )
    migration_seconds = time.perf_counter() - started
    started = time.perf_counter()
    verification = storage.verify(manifest)
    reconciliation_seconds = time.perf_counter() - started
    if verification["rows"] != args.expected_rows:
        raise ValueError("Persisted row count differs from expected canary")
    started = time.perf_counter()
    first_lookup = storage.lookup(manifest, selected)
    lookup_seconds = time.perf_counter() - started
    status = storage.stats(manifest)
    pointer = json.loads((args.output / "store/CURRENT").read_bytes())
    if (args.output / "store" / pointer["manifest"]) != manifest:
        raise ValueError("Published pointer does not name verified generation")
    if pointer["sha256"] != file_hash(manifest):
        raise ValueError("Published pointer digest differs from persisted manifest")
    descriptor = json.loads(manifest.read_bytes())
    partitions = [part for table in descriptor["tables"].values() for part in table["partitions"]]
    if not partitions or any((manifest.parent / part["path"]).stat().st_size == 0 for part in partitions):
        raise ValueError("Storage canary did not persist nonempty Parquet files")
    if file_hash(args.ledger) != args.ledger_sha256:
        raise ValueError("SQLite input changed during canary")
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    receipt = {
        "contract": "edgemech-storage-canary/v1", "manifest": str(manifest.resolve()),
        "manifest_sha256": pointer["sha256"], "source_sqlite_sha256": args.ledger_sha256,
        "source_sqlite_bytes": args.ledger.stat().st_size,
        "partition_files": len(partitions), "parquet_bytes": sum(p["bytes"] for p in partitions),
        "layout": descriptor["layout"], "verification": verification, "status": status,
        "lookup_occurrence": selected, "lookup_history_entries": len(first_lookup["history"]),
        "lookup_current_decision": first_lookup["current_decision"],
        "timings_seconds": {"migration_including_verify": migration_seconds,
                            "reconciliation": reconciliation_seconds, "lookup": lookup_seconds},
        "peak_rss_bytes": rss if sys.platform == "darwin" else rss * 1024,
        "python": sys.version, "scientific_approvals_created": 0,
        "implementation_sha256": {
            str(path.relative_to(Path(storage.__file__).parent)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(Path(storage.__file__).parent.glob("*.py"))
        },
    }
    temporary = args.output / ".receipt.json.tmp"
    with temporary.open("x") as handle:
        json.dump(receipt, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    temporary.rename(args.output / "receipt.json")
    print(json.dumps({"receipt": str(args.output / "receipt.json"),
                      "rows": verification["rows"], "partitions": len(partitions),
                      "manifest_sha256": pointer["sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
