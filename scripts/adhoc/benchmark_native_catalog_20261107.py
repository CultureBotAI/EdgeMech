#!/usr/bin/env python3
"""Measure 1,000 pinned native rows before census scaling changes, 2026-11-07.

Inputs: one verified native export and its manifest SHA-256. Outputs: exclusive
JSON timing receipt for the EdgeMech census scaling issue under CLAW #767.
No census publication or unbounded job is performed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import resource
import sys
import time
from io import BytesIO
from pathlib import Path

from kg_microbe_curation.identity import canonical_json, sha256_json
from kg_microbe_curation.native import MAX_NATIVE_BYTES, validate_native_assertion

import edgemech.census
from edgemech.census import (
    _catalog,
    _insert_native_batch,
    _json,
    _metadata,
    _native_line_batches,
    _read_handle,
    _validated_native_batches,
)
from edgemech.pins import check_contracts
from edgemech.storage.parquet import file_hash


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-export", type=Path, required=True)
    parser.add_argument("--native-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--optimized-workers", type=int, choices=range(1, 5))
    args = parser.parse_args()
    pins = check_contracts()
    manifest_path = args.native_export / "manifest.json"
    data, manifest = _metadata(manifest_path)
    if hashlib.sha256(data).hexdigest() != args.native_sha256:
        raise ValueError("Manifest pin mismatch")
    source = args.native_export / "assertions.jsonl"
    if source.stat().st_size != manifest["assertions_bytes"] or file_hash(source) != manifest["assertions_sha256"]:
        raise ValueError("Native export byte binding mismatch")
    lines = []
    with _read_handle(source) as handle:
        for _ in range(1000):
            line = handle.readline(MAX_NATIVE_BYTES + 2)
            if not line or len(line) > MAX_NATIVE_BYTES + 1:
                raise ValueError("Expected 1,000 bounded native lines")
            lines.append(line)
    common = {"format": "edgemech-native-catalog-benchmark/v1", "contract_pins": pins,
              "native_manifest_sha256": args.native_sha256,
              "native_assertions_sha256": manifest["assertions_sha256"],
              "rows": len(lines), "bytes": sum(map(len, lines)),
              "benchmark_helper_sha256": file_hash(Path(__file__)),
              "census_source_sha256": file_hash(Path(edgemech.census.__file__))}
    if args.optimized_workers is not None:
        with _catalog() as connection:
            connection.execute("BEGIN TRANSACTION")
            started, sql_seconds, batches, rows = time.perf_counter(), 0.0, 0, 0
            for _, records in _validated_native_batches(
                _native_line_batches(BytesIO(b"".join(lines))), args.optimized_workers,
                manifest.get("source_commit"),
            ):
                sql_started = time.perf_counter()
                _insert_native_batch(connection, records)
                sql_seconds += time.perf_counter() - sql_started
                batches += 1
                rows += len(records)
            connection.execute("COMMIT")
            seconds = time.perf_counter() - started
            distinct = connection.execute("SELECT count(*) FROM native").fetchall()[0][0]
            if rows != 1000:
                raise ValueError("Optimized catalogue did not consume all 1,000 rows")
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        child_peak = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
        receipt = {**common, "mode": "bounded-production-catalog", "workers": args.optimized_workers,
                   "distinct_assertions": distinct, "catalog_seconds": seconds,
                   "bulk_sql_seconds": sql_seconds, "batches": batches,
                   "parent_peak_rss_bytes": peak if sys.platform == "darwin" else peak * 1024,
                   "children_ru_maxrss_bytes": child_peak if sys.platform == "darwin" else child_peak * 1024,
                   "rss_scope": "parent peak and OS child accounting; not a simultaneous pool peak"}
        write_receipt(args.output, receipt)
        return
    started = time.perf_counter()
    assertions = []
    for line in lines:
        assertion = _json(line)
        validate_native_assertion(assertion)
        assertions.append(assertion)
    validated = time.perf_counter()
    records = []
    for assertion in assertions:
        evidence, ancestry = [], []
        for entry in assertion["evidence"]:
            locator = entry["locator"]
            binding = {key: locator[key] for key in ("repository", "commit", "path")}
            evidence.append(sha256_json({**binding, "sha256": entry["sha256"]}))
            ancestry.extend(sha256_json({"repository": locator["repository"],
                                        "commit": locator["commit"], "ancestor": ancestor})
                            for ancestor in entry["ancestry"])
        payload = assertion["payload"]
        records.append(([assertion["assertion_id"], payload["subject"], payload["predicate"],
                         payload["object"], canonical_json(assertion).decode()], evidence, ancestry))
    encoded = time.perf_counter()
    with _catalog() as connection:
        connection.execute("BEGIN TRANSACTION")
        sql_started = time.perf_counter()
        statements = 0
        for row, evidence, ancestry in records:
            existing = connection.execute("SELECT document FROM native WHERE id=?", [row[0]]).fetchall()
            statements += 1
            if existing:
                if existing[0][0] != row[4]:
                    raise ValueError("Conflicting duplicate native assertion")
                continue
            connection.execute("INSERT INTO native VALUES (?,?,?,?,?)", row)
            statements += 1
            for table, values in (("evidence", evidence), ("ancestry", ancestry)):
                for value in values:
                    connection.execute(f"INSERT INTO {table} VALUES (?)", [value])
                    statements += 1
        connection.execute("COMMIT")
        sql_done = time.perf_counter()
        distinct = connection.execute("SELECT count(*) FROM native").fetchall()[0][0]
    receipt = {**common, "mode": "serial-per-row-sql-baseline", "distinct_assertions": distinct,
               "decode_validate_seconds": validated - started,
               "encode_evidence_bindings_seconds": encoded - validated,
               "serial_sql_seconds": sql_done - sql_started, "sql_statements": statements}
    write_receipt(args.output, receipt)


def write_receipt(path, receipt):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as handle:
        json.dump(receipt, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
