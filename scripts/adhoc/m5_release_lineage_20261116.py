#!/usr/bin/env python3
"""Inspect bounded retained source lineage for the M5 BactoTraits correction.

2026-11-16: read only the original CSV, the declared BacDive lookup, the old
BactoTraits intermediates and three explicitly selected source edge files.
Also inspect the distinct Madin source row for an equivalent historical edge.
Keep occurrence ordinals and hashes. This does not establish graph-wide absence,
current release freshness, trait falsity or a replacement organism identity.
The selected files are inspected directly, including ignored data; no discovery
walk or remote request is performed. Results use an exclusive output directory.
"""

import argparse
import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

CANONICAL = Path("/Users/marcin/Documents/VIMSS/ontology/KG-Hub/KG-Microbe/kg-microbe")
CODE = Path("/Users/marcin/agent-work/EdgeMech/m5-kg-bactotraits-release-20261116")
SOURCE_SHA = "18316d7a0b6c2bef6fcb96a7659c2e3f3734c14786f383c2a93fefe2ae226a4b"
ROW_SHA = "345fd2d00ee93334d975085716692dd4d4c530d5529f04c5b07af0766d5a512a"
SUBJECT = "NCBITaxon:1123071"
OBJECT = "METPO:1000703"


def sha256(path):
    """Hash a selected regular file without retaining its contents in memory."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def identity(path):
    """Record content and filesystem identity for one explicitly selected input."""
    before = path.stat()
    result = {
        "path": str(path),
        "bytes": before.st_size,
        "mtime_ns": before.st_mtime_ns,
        "inode": before.st_ino,
        "sha256": sha256(path),
    }
    after = path.stat()
    assert (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns) == (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
    ), f"Input changed while hashing: {path}"
    return result


def rows(path, *, raw=False, delimiter="\t"):
    """Stream exact CSV/TSV records with data-row ordinals, including duplicates."""
    with path.open(encoding="ISO-8859-1" if raw else "utf-8", newline="") as stream:
        reader = csv.reader(stream, delimiter=";" if raw else delimiter)
        if raw:
            next(reader)
            next(reader)
        header = next(reader)
        assert len(header) == len(set(header)), f"Duplicate header: {path}"
        for ordinal, values in enumerate(reader, 1):
            assert len(values) == len(header), f"Malformed row {ordinal}: {path}"
            yield ordinal, dict(zip(header, values, strict=True))


def scan(path, selector, *, raw=False, delimiter="\t"):
    """Retain matching complete records and verify source identity after reading."""
    pin = identity(path)
    matches = []
    count = 0
    for count, row in rows(path, raw=raw, delimiter=delimiter):
        if selector(row):
            matches.append({"source_data_row": count, "row": row})
    assert identity(path) == pin, f"Input changed during scan: {path}"
    return {
        "input": pin,
        "data_rows": count,
        "matches": matches,
        "matched_occurrences": len(matches),
    }


def inspect(root):
    """Trace the reviewed selector, accession occurrences and retained joins."""
    raw = scan(
        root / "data/raw/BactoTraits_databaseV2_Jun2022.csv",
        lambda row: (
            row["Bacdive_ID"] == "17851"
            or "19353" in row["culture collection codes"]
            or "14586" in row["culture collection codes"]
        ),
        raw=True,
    )
    assert raw["input"]["sha256"] == SOURCE_SHA, "Original BactoTraits bytes changed"
    selected = [m for m in raw["matches"] if m["row"]["Bacdive_ID"] == "17851"]
    assert len(selected) == 1 and selected[0]["source_data_row"] == 8521
    raw_row = selected[0]["row"]
    row_digest = hashlib.sha256(
        json.dumps(raw_row, ensure_ascii=False, indent=2, sort_keys=True).encode()
    ).hexdigest()
    assert row_digest == ROW_SHA, "Reviewed complete original row changed"
    lookup = scan(
        root / "kg_microbe/transform_utils/bacdive/tmp/bacdive.tsv",
        lambda row: row["bacdive_id"] == "bacdive:17851" or row["ncbitaxon_id"] == SUBJECT,
    )
    intermediates = {}
    for filename in ("bactotraits.tsv", "bactotraits_mapping.tsv"):
        intermediates[filename] = scan(
            root / "kg_microbe/transform_utils/bactotraits/tmp" / filename,
            lambda row: (
                row.get("Bacdive_ID") in ("17851", "bacdive:17851")
                or row.get("ncbitaxon_id") == SUBJECT
            ),
        )
    products = {}
    for source in ("bactotraits", "bacdive", "madin_etal"):
        item = scan(
            root / "data/transformed" / source / "edges.tsv",
            lambda row: row.get("subject") == SUBJECT and row.get("object") == OBJECT,
        )
        products[source] = item
    madin = scan(
        root / "data/raw/madin_etal.csv", lambda row: row["tax_id"] == "1123071", delimiter=","
    )
    implementations = {
        name: identity(CODE / name)
        for name in (
            "kg_microbe/transform_utils/bactotraits/bactotraits.py",
            "kg_microbe/transform_utils/bactotraits/identity_quarantine.py",
            "kg_microbe/transform_utils/madin_etal/madin_etal.py",
            "mappings/canonical/bactotraits_identity_quarantine.json",
            "merge.yaml",
        )
    }
    return {
        "profile": "m5-bactotraits-retained-lineage/v1",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "helper_sha256": sha256(Path(__file__)),
        "raw_source": raw,
        "selected_complete_row_sha256": row_digest,
        "bacdive_lookup": lookup,
        "historical_intermediates": intermediates,
        "historical_source_graph_occurrences": products,
        "independent_madin_raw_occurrences": madin,
        "inspected_implementation_and_config": implementations,
        "scope": "Selected original CSV, lookup, two old intermediates, three old source edge files and Madin raw CSV; ignored files included by direct path.",
        "graph_wide_absence_verified": False,
        "current_source_freshness_verified": False,
        "published_release_verified": False,
        "scientific_trait_truth_resolved": False,
        "neighboring_rows_quarantined": False,
    }


def main():
    """Plan or execute one bounded source lineage inspection."""
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--plan", action="store_true")
    actions.add_argument("--run", action="store_true")
    parser.add_argument("--input-root", type=Path, default=CANONICAL)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output already exists; select a fresh exclusive directory")
    csv.field_size_limit(16 * 1024 * 1024)
    if args.plan:
        print(
            json.dumps(
                {
                    "action": "plan",
                    "input_root": str(args.input_root),
                    "output": str(args.output),
                    "network_calls": 0,
                    "source_files": 8,
                    "concurrency": 1,
                    "writes": 0,
                }
            )
        )
        return
    os.umask(0o077)
    args.output.mkdir(parents=True, mode=0o700)
    result = inspect(args.input_root)
    receipt = args.output / "receipt.json"
    with receipt.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(
        json.dumps(
            {
                "receipt": str(receipt),
                "sha256": sha256(receipt),
                "matches_by_source": {
                    key: value["matched_occurrences"]
                    for key, value in result["historical_source_graph_occurrences"].items()
                },
            }
        )
    )


if __name__ == "__main__":
    main()
