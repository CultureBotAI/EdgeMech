#!/usr/bin/env python3
"""Summarize saved EdgeMech validation receipts for #766/#767; 2026-11-07.

Inputs: storage receipts and optional census run receipts; no artifact mutation.
Output: compact Markdown evidence, with exact receipt/manifest hashes.
"""

import argparse
import hashlib
import json
from pathlib import Path

SQLITE_SHA256 = "85d0f98093a595308f9246cc9c517dbaf5ef26086d65650f0cff025609498ade"
SNAPSHOT_SHA256 = "f585e55a616d3771f382c91c78713cb8d74812c7ba177576090ccd5f9e6654b2"
EXPECTED_COUNTERS = {
    "review_state": {"unprocessed": 999, "deferred": 1},
    "disposition": {"withheld": 1000},
    "lifecycle": {"active": 1000},
    "conflict_state": {"not_assessed": 1000},
}


def checked_manifest(path, digest):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError("Persisted manifest differs from receipt")
    return json.loads(raw)


def check_storage(record):
    manifest = checked_manifest(Path(record["manifest"]), record["manifest_sha256"])
    if (
        record["contract"] != "edgemech-storage-canary/v1"
        or record["source_sqlite_sha256"] != SQLITE_SHA256
        or record["source_sqlite_bytes"] != 806912
        or record["scientific_approvals_created"] != 0
        or not record["verification"]["verified"]
        or record["verification"]["rows"] != 1000
        or record["status"]["counters"] != EXPECTED_COUNTERS
        or record["status"]["source"]["source_manifest_sha256"] != SNAPSHOT_SHA256
        or record["verification"]["table_rows"]["bundles"] != 1
        or record["verification"]["table_rows"]["history"] != 1
        or manifest["source"] != record["status"]["source"]
        or manifest["counters"] != EXPECTED_COUNTERS
    ):
        raise ValueError("Receipt is not the pinned 1,000-row migration experiment")


def check_census(path, record):
    if not path.name.endswith(".run.json"):
        raise ValueError("Expected an adjacent census run receipt")
    manifest = checked_manifest(
        path.with_name(path.name.removesuffix(".run.json")) / "census-manifest.json",
        record["manifest_sha256"],
    )
    if (
        record["format"] != "edgemech-census-run/v1"
        or manifest["source"]["manifest_sha256"] != SNAPSHOT_SHA256
        or record["source_rows"] != 17637435
        or record["selected_rows"] != manifest["source"]["selected_rows"]
        or record["counts"] != manifest["counts"]
        or sum(record["counts"].values()) != record["selected_rows"]
        or record["native_accounting"] != manifest["native_accounting"]
        or record["scientific_approvals_created"] != 0
        or manifest["kg_occurrences_approved"] != 0
    ):
        raise ValueError("Receipt is not a reconciled census of the pinned snapshot")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--storage", type=Path, action="append", required=True)
    parser.add_argument("--census", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    lines = ["# EdgeMech validation evidence — 2026-11-07", "",
             "Generated from persisted receipts by `scripts/adhoc/summarize_validation_20261107.py`.",
             "Bulk stores and full receipts remain in ignored `workspace/validation-20261107/`.", "",
             "## SQLite migration", "",
             "Each measurement migrates the same verified 1,000-row ledger in a separate process.",
             "Migration time includes complete replay and verification; reconciliation is a second full audit.",
             "Peak memory is process RSS, including Python, Arrow and DuckDB. These small-input measurements",
             "do not establish a production layout, graph-wide performance or review quality.", "",
             "| Buckets | Row group | Files | Parquet bytes | Migration s | Reconcile s | Lookup ms | Peak MiB |",
             "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    storage = []
    for path in args.storage:
        raw = path.read_bytes()
        record = json.loads(raw)
        check_storage(record)
        storage.append((path, raw, record))
        layout, timing = record["layout"], record["timings_seconds"]
        lines.append(f"| {layout['buckets']} | {layout['row_group_size']} | {record['partition_files']} | "
                     f"{record['parquet_bytes']} | {timing['migration_including_verify']:.3f} | "
                     f"{timing['reconciliation']:.3f} | {timing['lookup'] * 1000:.3f} | "
                     f"{record['peak_rss_bytes'] / 1024**2:.2f} |")
    first = storage[0][2]
    lines.extend(["", f"Input SQLite: `{first['source_sqlite_sha256']}` ({first['source_sqlite_bytes']} bytes).",
                  "All authoritative fields, occurrence IDs, raw rows, memberships, current decisions",
                  "and historical canonical bundles are compared through replay. The canary preserves",
                  "999 unprocessed plus one deferred decision, all withheld, with one historical bundle.",
                  "It creates zero scientific approvals.", ""])
    for path, raw, record in storage:
        lines.extend([f"- `{path.parent.name}` receipt SHA-256: `{hashlib.sha256(raw).hexdigest()}`;",
                      f"  artifact manifest: `{record['manifest_sha256']}`."])
    lines.extend(["", "## Native overlap census", "",
                  "The source is the historical 20260929 KG-Microbe snapshot, not a newly published release.",
                  "Its manifest SHA-256 is `f585e55a616d3771f382c91c78713cb8d74812c7ba177576090ccd5f9e6654b2`",
                  "and its recorded producer is `1408e7099-dirty`. Exact inherited-scope eligibility is",
                  "separate from scientific approval. Matching endpoints alone cannot approve a KG claim.", ""])
    for path in args.census:
        raw = path.read_bytes()
        record = json.loads(raw)
        manifest = check_census(path, record)
        lines.extend([f"### {path.name}", "",
                      f"Selected occurrences: {record['selected_rows']:,} / {record['source_rows']:,}.",
                      f"Distinct native assertions: {record['native_accounting']['distinct_assertions']:,}.",
                      f"Endpoint-candidate occurrences: {manifest['endpoint_candidate_occurrences']:,}; "
                      f"exact SPO candidates: {manifest['spo_candidate_occurrences']:,}.",
                      f"Persisted Parquet: {record['partition_files']:,} files, {record['parquet_bytes']:,} bytes.",
                      f"Elapsed including verification: {record['elapsed_seconds_including_verification']:.3f} s; "
                      f"peak parent process RSS: {record['peak_rss_bytes'] / 1024**2:.2f} MiB.",
                      f"Native validation workers: {record.get('native_validation_workers', 1)}. "
                      "Parent RSS excludes worker processes; no aggregate pool-memory peak is claimed.", "",
                      "| Classification | Occurrences |", "| --- | ---: |"])
        lines.extend(f"| {key} | {value:,} |" for key, value in record["counts"].items())
        if not {"native_assertion", "native_scope"}.issubset(manifest["source"]["header"]):
            lines.extend(["", "The pinned KG header lacks complete native assertion/scope bindings.",
                          "Zero exact eligibility therefore does not establish zero biological overlap.",
                          "These counts cover the declared native export surfaces, not every scientific",
                          "claim or evidence record held by the four Mechs."])
        lines.extend(["", f"Receipt SHA-256: `{hashlib.sha256(raw).hexdigest()}`.",
                      f"Census manifest SHA-256: `{record['manifest_sha256']}`.",
                      "Every original source member, including unselected tails, was hash/row verified.",
                      "Persisted rows and classifications were replayed before atomic publication.",
                      "Native observation/claim/experiment totals remain unknown where native IDs are absent.", ""])
        accounting = record["native_accounting"]
        lines.extend(["Native evidence accounting (references are not independent experiments):", "",
                      "| Binding kind | References | Distinct bindings | Shared references |",
                      "| --- | ---: | ---: | ---: |"])
        for kind in ("evidence", "ancestry"):
            lines.append(f"| {kind} | {accounting[f'{kind}_references']:,} | "
                         f"{accounting[f'distinct_{kind}_bindings']:,} | "
                         f"{accounting[f'shared_{kind}_references']:,} |")
        lines.extend(["", f"Census implementation SHA-256: `{record.get('census_source_sha256', 'not recorded')}`.",
                      f"Launcher SHA-256: `{record.get('launcher_sha256', 'not recorded')}`.", ""])
        lines.append("Native export manifest pins:")
        lines.append("")
        for export in manifest["native_exports"]:
            native_path = path.with_name(path.name.removesuffix(".run.json")) / export["path"]
            native_manifest = checked_manifest(native_path, export["sha256"])
            with (native_path.parent / "assertions.jsonl").open() as stream:
                first_native = json.loads(next(stream))
            lines.append(f"- {first_native['native_locator']['repository']}: `{export['sha256']}`; "
                         f"source `{export['source_commit']}`; {export['rows']:,} assertions; "
                         f"native statuses `{json.dumps(native_manifest['native_status_counts'], sort_keys=True)}`.")
        lines.append("")
    if not args.census:
        lines.extend(["No census receipt was supplied to this report.", ""])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines).rstrip() + "\n")


if __name__ == "__main__":
    main()
