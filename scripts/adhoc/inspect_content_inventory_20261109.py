"""Read back inventory artifacts and emit a compact receipt (2026-11-09).

Inputs: preparation manifest. Output: JSON on stdout for the 17M plan PR.
This verifies persisted shard hashes and counts, not scientific correctness.
"""
import argparse
import json
from pathlib import Path

import pyarrow.parquet as pq

from edgemech.storage.parquet import file_hash

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--compare-to", type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_bytes())
    rows = size = 0
    for entry in manifest["partitions"]:
        path = args.manifest.parent / entry["path"]
        if file_hash(path) != entry["sha256"] or path.stat().st_size != entry["bytes"]:
            raise ValueError("Persisted artifact hash/size mismatch")
        count = pq.ParquetFile(path).metadata.num_rows
        if count != entry["rows"]:
            raise ValueError("Persisted artifact count mismatch")
        rows += count
        size += entry["bytes"]
    if rows != manifest["rows"]:
        raise ValueError("Manifest count mismatch")
    if args.compare_to:
        other = json.loads(args.compare_to.read_bytes())
        if len(other["partitions"]) != len(manifest["partitions"]):
            raise ValueError("Comparison partition count differs")
        for left, right in zip(manifest["partitions"], other["partitions"], strict=True):
            first = pq.read_table(args.manifest.parent / left["path"]).sort_by("row_number")
            second = pq.read_table(args.compare_to.parent / right["path"]).sort_by("row_number")
            if not first.equals(second):
                differences = [name for name in first.column_names
                               if first[name].to_pylist() != second[name].to_pylist()]
                if first.column_names != second.column_names or differences:
                    raise ValueError(f"Comparison output differs logically: {differences}")
    print(json.dumps({
        "manifest_sha256": file_hash(args.manifest), "verified_rows": rows,
        "verified_shards": len(manifest["partitions"]), "parquet_bytes": size,
        "complete_population": manifest["complete_population"],
        "scientific_reviews": manifest["scientific_reviews"],
        "missing_node_occurrences": sum(p["missing_node_occurrences"] for p in manifest["profile"]),
        "incomplete_node_occurrences": sum(p["incomplete_node_occurrences"]
                                           for p in manifest["profile"]),
        "inline_evidence_occurrences": sum(p["inline_evidence_occurrences"]
                                           for p in manifest["profile"]),
        "elapsed_seconds": manifest["elapsed_seconds"],
        "logical_comparison_passed": True if args.compare_to else None,
    }, indent=2))
