"""Observe candidate IDs in pinned census partitions without freezing A/B.

Date: draft 2026-11-20 UTC; prepared for review 2026-11-26 UTC.
Issues: #224 (exact population), #228 (helper provenance).
Purpose: distinguish retained IDs from other source versions using exact IDs,
source-row hashes and pinned CLAW occurrence identity, never an SPO join.
Inputs: SHA256-pinned census manifest and JSON array of unique candidate IDs,
or an explicitly selected candidate_union_ids field from the retained audit.
Outputs: exclusive private attempt directory with plan, per-partition progress,
matched rows, unseen IDs and a provisional summary; failed attempts are retained.
A prefix canary uses the same read path as a complete partition scan. This is
not native-classification replay, assessment qualification, scientific approval,
or permission to freeze the campaign. Original source/census bytes are read-only.
Provenance: maintained census guarded handles/schema and pinned CLAW identities.
The original unexecuted draft is preserved privately. This is a new observation,
not a replay of source restoration, the full verifier or an actual worker canary.
The time budget is cooperative between bounded reads/batches, not a hard process
deadline. Outputs must be under this checkout's private .temp directory.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
from kg_microbe_curation.artifact import validate_relative_path
from kg_microbe_curation.identity import occurrence_id

from edgemech.census import CENSUS_FORMAT, CENSUS_SCHEMA, _integer, _json, _read_handle, _sha
from edgemech.pins import check_contracts

ROOT = Path(__file__).resolve().parents[2]
MAX_METADATA_BYTES = 16 * 1024 * 1024
MAX_CANDIDATES = 100_000
OCCURRENCE = re.compile(r"urn:kg-microbe:occurrence:v1:[0-9a-f]{64}")
OUTPUT_SPEC = importlib.util.spec_from_file_location(
    "restart_private_attempt", Path(__file__).with_name("restart_private_attempt_20261126.py"))
private_output_module = importlib.util.module_from_spec(OUTPUT_SPEC)
OUTPUT_SPEC.loader.exec_module(private_output_module)


def now():
    return datetime.now(timezone.utc).isoformat()


def read_pinned(path, expected):
    _sha(expected)
    with _read_handle(path) as handle:
        data = handle.read(MAX_METADATA_BYTES + 1)
    if len(data) > MAX_METADATA_BYTES or hashlib.sha256(data).hexdigest() != expected:
        raise ValueError("metadata size or SHA256 pin mismatch")
    return _json(data)


def candidate_ids(value):
    if (not isinstance(value, list) or not 1 <= len(value) <= MAX_CANDIDATES
            or any(not isinstance(item, str) or not OCCURRENCE.fullmatch(item) for item in value)):
        raise ValueError("require a bounded array of exact occurrence IDs")
    if len(value) != len(set(value)):
        raise ValueError("duplicate candidate IDs; retain provenance separately, do not silently deduplicate")
    return sorted(value)


def write_json(path, value, *, output):
    data = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    return output.save(path.name, data)["sha256"]


def deadline_check(deadline):
    if time.monotonic() > deadline:
        raise TimeoutError("bounded membership scan deadline exceeded; attempt retained")


def scan(root, manifest, candidates, *, max_partitions=None, seconds=1800, progress=None):
    if (not isinstance(manifest, dict) or manifest.get("contract") != CENSUS_FORMAT
            or _integer(manifest.get("independent_scientific_reviews")) != 0
            or _integer(manifest.get("kg_occurrences_approved")) != 0):
        raise ValueError("expected census transport metadata with no scientific approvals")
    source = manifest["source"]
    total_expected = _integer(source["source_rows"])
    if (not total_expected or source["complete_export"] is not True or source["limit"] is not None
            or source["selection"] != "initial_source_row_prefix"
            or _integer(source["selected_rows"]) != total_expected):
        raise ValueError("require a declared complete source census, not a subset")
    _sha(source["manifest_sha256"])
    _sha(source["edge_member_sha256"])
    validate_relative_path(source["edge_member"])
    partitions = manifest["partitions"]
    if not isinstance(partitions, list) or not partitions:
        raise ValueError("require nonempty partition descriptors")
    if max_partitions is not None and (type(max_partitions) is not int
                                      or not 1 <= max_partitions <= len(partitions)):
        raise ValueError("prefix partition limit must be within declared partitions")
    if type(seconds) is not int or not 1 <= seconds <= 1800:
        raise ValueError("cooperative deadline must be an integer in 1..1800 seconds")
    selected = partitions if max_partitions is None else partitions[:max_partitions]
    deadline = time.monotonic() + seconds
    ids = candidate_ids(candidates)
    values = pa.array(ids, type=pa.string())
    seen_paths, matches, matched_ids = set(), [], set()
    total = 0
    for descriptor in selected:
        deadline_check(deadline)
        relative = descriptor["path"]
        validate_relative_path(relative)
        if relative in seen_paths or not relative.endswith(".parquet"):
            raise ValueError("duplicate or invalid partition path")
        seen_paths.add(relative)
        rows = _integer(descriptor["rows"])
        if (not rows or _integer(descriptor["first_row"]) != total + 1
                or _integer(descriptor["last_row"]) != total + rows
                or total + rows > total_expected):
            raise ValueError("partition row bounds do not reconcile")
        path = root / relative
        partition_total = 0
        before_matches = len(matches)
        with _read_handle(path) as handle:
            hashed, size = hashlib.sha256(), 0
            while block := handle.read(4 * 1024 * 1024):
                deadline_check(deadline)
                hashed.update(block)
                size += len(block)
            if (size != _integer(descriptor["bytes"])
                    or hashed.hexdigest() != _sha(descriptor["sha256"])):
                raise ValueError("partition bytes differ from pinned descriptor")
            handle.seek(0)
            parquet = pq.ParquetFile(handle)
            if parquet.schema_arrow != CENSUS_SCHEMA or parquet.metadata.num_rows != rows:
                raise ValueError("partition schema or count differs")
            for batch in parquet.iter_batches(
                batch_size=20_000, use_threads=False,
                columns=["row_number", "occurrence_id", "row_sha256", "source_row"],
            ):
                deadline_check(deadline)
                first = total + partition_total + 1
                if not batch.column("row_number").equals(pa.array(range(first, first + len(batch)))):
                    raise ValueError("partition source row positions differ")
                selected_rows = batch.filter(pc.is_in(batch.column("occurrence_id"), value_set=values))
                for row in selected_rows.to_pylist():
                    raw_sha = hashlib.sha256(row["source_row"]).hexdigest()
                    exact_id = occurrence_id(
                        manifest_sha256=source["manifest_sha256"], member=source["edge_member"],
                        member_sha256=source["edge_member_sha256"], row_number=row["row_number"],
                        row_sha256=raw_sha,
                    )
                    if raw_sha != row["row_sha256"] or exact_id != row["occurrence_id"]:
                        raise ValueError("matched candidate differs from exact source-row identity")
                    if exact_id in matched_ids:
                        raise ValueError("candidate occurrence matched more than one source position")
                    matched_ids.add(exact_id)
                    matches.append({"occurrence_id": exact_id, "row_number": row["row_number"],
                                    "row_sha256": raw_sha, "partition": relative})
                partition_total += len(batch)
        if partition_total != rows:
            raise ValueError("partition scan count differs")
        total += partition_total
        if progress is not None:
            progress.write(json.dumps({"partition": relative, "sha256": descriptor["sha256"],
                                       "rows": partition_total, "cumulative_rows": total,
                                       "matches": len(matches) - before_matches}) + "\n")
            progress.flush()
            os.fsync(progress.fileno())
    complete = len(selected) == len(partitions)
    deadline_check(deadline)
    if complete and total != total_expected:
        raise ValueError("complete partition count differs from declared source population")
    return {
        "status": "PROVISIONAL_PINNED_PARTITION_MEMBERSHIP_OBSERVATIONS",
        "all_declared_partitions_scanned": complete, "partitions_scanned": len(selected),
        "rows_scanned": total, "candidate_count": len(ids),
        "matched_candidates": sorted(matches, key=lambda row: row["occurrence_id"]),
        "ids_not_observed_in_scanned_partitions": sorted(set(ids) - matched_ids),
        "full_census_native_and_source_replay_verified": False,
        "baseline_membership_qualified": False, "full_target_frozen": False,
        "queue_A_count": None, "queue_B_count": None, "scientific_review_coverage": 0,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--census", type=Path, required=True)
    parser.add_argument("--census-sha256", required=True)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--candidates-sha256", required=True)
    parser.add_argument("--candidate-field", choices=["candidate_union_ids"])
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--max-partitions", type=int)
    parser.add_argument("--seconds", type=int, default=1800)
    args = parser.parse_args()
    os.umask(0o077)
    with private_output_module.private_attempt(args.results, ROOT / ".temp") as output:
        return _main(args, output)


def _main(args, output):
    result_root = args.results
    receipt = {"started_at_utc": now(), "census_sha256": args.census_sha256,
               "candidate_file_sha256": args.candidates_sha256,
               "candidate_field": args.candidate_field,
               "max_partitions": args.max_partitions, "seconds": args.seconds}
    try:
        with _read_handle(Path(__file__)) as handle:
            receipt["helper_sha256"] = hashlib.file_digest(handle, "sha256").hexdigest()
        with _read_handle(Path(private_output_module.__file__)) as handle:
            receipt["output_helper_sha256"] = hashlib.file_digest(handle, "sha256").hexdigest()
        check_contracts()
        manifest = read_pinned(args.census, args.census_sha256)
        candidate_document = read_pinned(args.candidates, args.candidates_sha256)
        if args.candidate_field:
            if not isinstance(candidate_document, dict):
                raise ValueError("explicit candidate field requires a JSON object")
            candidate_document = candidate_document[args.candidate_field]
        candidates = candidate_ids(candidate_document)
        write_json(result_root / "plan.json", receipt, output=output)
        with output.create("partition-progress.jsonl", text=True) as progress:
            result = scan(args.census.parent, manifest, candidates,
                          max_partitions=args.max_partitions, seconds=args.seconds, progress=progress)
        result.update(receipt, finished_at_utc=now())
        write_json(result_root / "result.json", result, output=output)
        print(json.dumps({key: value for key, value in result.items()
                          if key not in {"matched_candidates", "ids_not_observed_in_scanned_partitions"}}
                         | {"matched_candidate_count": len(result["matched_candidates"])}))
    except BaseException as error:
        receipt.update(status="failed", error_type=type(error).__name__, finished_at_utc=now())
        try:
            write_json(result_root / "failure.json", receipt, output=output)
        except BaseException as receipt_error:
            error.add_note(f"Failure receipt could not be persisted: {type(receipt_error).__name__}")
            raise error from receipt_error
        raise


if __name__ == "__main__":
    main()
