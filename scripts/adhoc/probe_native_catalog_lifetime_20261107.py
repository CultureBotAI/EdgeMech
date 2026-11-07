#!/usr/bin/env python3
"""Probe Arrow ownership across tiny native-catalog transactions, 2026-11-07.

Inputs: pinned MIM native export, sixteen validated prefix rows, sixteen
shared-contract file pins. Output: exclusive JSON memory-lifetime receipt
for the EdgeMech large-catalog finding under CLAW #767. Core code is read-only.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import time
from pathlib import Path

import duckdb
import pyarrow as pa
from kg_microbe_curation.native import MAX_NATIVE_BYTES

import edgemech.census
from edgemech.census import (
    _catalog,
    _insert_native_batch,
    _metadata,
    _read_handle,
    _validate_native_batch,
)
from edgemech.pins import check_contracts
from edgemech.storage.parquet import file_hash

ROWS = 16
BATCH_ROWS = 4


def snapshot(events, phase, **details):
    gc.collect()
    events.append({"phase": phase, "arrow_allocated_bytes": pa.total_allocated_bytes(), **details})


class ObservedConnection:
    """Record Arrow-pool bytes without retaining Arrow tables in observations."""

    def __init__(self, connection, events):
        self.connection = connection
        self.events = events
        self.batch = 0

    def execute(self, query, *args, **kwargs):
        result = self.connection.execute(query, *args, **kwargs)
        if query.startswith("INSERT INTO"):
            snapshot(self.events, "after_insert", batch=self.batch, table=query.split()[2])
        return result

    def register(self, name, table):
        self.batch += 1
        self.connection.register(name, table)
        snapshot(self.events, "after_register", batch=self.batch, table_bytes=table.nbytes)

    def unregister(self, name):
        self.connection.unregister(name)
        snapshot(self.events, "after_unregister", batch=self.batch)


def probe(records, outer_transaction):
    events = []
    snapshot(events, "before_catalog")
    started = time.perf_counter()
    with _catalog() as connection:
        observed = ObservedConnection(connection, events)
        snapshot(events, "after_catalog_open")
        if outer_transaction:
            connection.execute("BEGIN TRANSACTION")
            snapshot(events, "after_begin")
        for start in range(0, len(records), BATCH_ROWS):
            _insert_native_batch(observed, records[start : start + BATCH_ROWS])
            snapshot(events, "after_batch_return", batch=observed.batch)
        counts = {
            table: connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            for table in ("native", "evidence", "ancestry")
        }
        if counts != {
            "native": len(records),
            "evidence": sum(len(row["evidence"]) for row in records),
            "ancestry": sum(len(row["ancestry"]) for row in records),
        }:
            raise ValueError("Probe did not persist the expected native/evidence/ancestry counters")
        actual = connection.execute("SELECT id,document FROM native ORDER BY id").fetchall()
        expected = sorted((row["id"], row["document"]) for row in records)
        if actual != expected:
            raise ValueError("Probe native document identity differs")
        snapshot(events, "after_all_batches", counters=counts)
        if outer_transaction:
            connection.execute("COMMIT")
            snapshot(events, "after_commit")
        else:
            snapshot(events, "after_autocommitted_inserts")
    snapshot(events, "after_close")
    return {"outer_transaction": outer_transaction, "seconds": time.perf_counter() - started,
            "events": events, "counters": counts}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-export", type=Path, required=True)
    parser.add_argument("--native-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--plan", action="store_true")
    args = parser.parse_args()
    if args.output.exists() or args.output.is_symlink():
        raise ValueError("Probe output must be new")
    contracts = check_contracts()
    if contracts["files"] != 16:
        raise ValueError("Expected the reviewed sixteen-file contract closure")
    source_file = Path(edgemech.census.__file__)
    census_hash = file_hash(source_file)
    data, manifest = _metadata(args.native_export / "manifest.json")
    if hashlib.sha256(data).hexdigest() != args.native_sha256:
        raise ValueError("Native manifest pin mismatch")
    source = args.native_export / "assertions.jsonl"
    if source.stat().st_size != manifest["assertions_bytes"] or file_hash(source) != manifest["assertions_sha256"]:
        raise ValueError("Native assertion file hash or byte count mismatch")
    lines = []
    with _read_handle(source) as handle:
        for _ in range(ROWS):
            line = handle.readline(MAX_NATIVE_BYTES + 2)
            if not line or len(line) > MAX_NATIVE_BYTES + 1:
                raise ValueError("Expected sixteen bounded native prefix rows")
            lines.append(line)
    records = _validate_native_batch(lines, manifest["source_commit"])
    if len({row["id"] for row in records}) != ROWS:
        raise ValueError("Prefix must contain sixteen distinct validated assertions")
    common = {
        "format": "edgemech-native-catalog-arrow-lifetime/v1", "contract_pins": contracts,
        "native_export": str(args.native_export.resolve()),
        "native_manifest_sha256": args.native_sha256,
        "native_assertions_sha256": manifest["assertions_sha256"],
        "native_source_commit": manifest["source_commit"],
        "prefix_sha256": hashlib.sha256(b"".join(lines)).hexdigest(),
        "prefix_rows": ROWS, "prefix_bytes": sum(map(len, lines)), "batch_rows": BATCH_ROWS,
        "census_source_sha256": census_hash, "helper_sha256": file_hash(Path(__file__)),
        "duckdb_version": duckdb.__version__, "pyarrow_version": pa.__version__,
        "duckdb_memory_limit": "256MB", "arrow_pool": pa.default_memory_pool().backend_name,
        "measurement": "gc.collect then pa.total_allocated_bytes; allocator bytes, not process RSS",
    }
    if args.plan:
        print(json.dumps({**common, "plan": "Two tiny catalogs: four batches each; no census publication"}, sort_keys=True))
        return
    results = [probe(records, outer_transaction=True), probe(records, outer_transaction=False)]
    if file_hash(source_file) != census_hash or check_contracts() != contracts:
        raise ValueError("Catalog implementation or shared contracts changed during the probe")
    receipt = {**common, "results": results}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as handle:
        json.dump(receipt, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    if json.loads(args.output.read_text()) != receipt:
        raise ValueError("Persisted probe receipt differs")
    print(json.dumps({"receipt": str(args.output), "sha256": file_hash(args.output),
                      "results": results}, sort_keys=True))


if __name__ == "__main__":
    main()
