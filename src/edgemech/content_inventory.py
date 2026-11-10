"""Pinned, deterministic preparation for content review; never scientific approval.

This derived inventory is not a shared review contract. Canonical occurrences
remain owned by CLAW and evidence/decisions remain in their native repositories.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import time
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
from kg_microbe_curation.identity import CurationError, occurrence_id

from .census import CENSUS_FORMAT, _decode_row, _metadata
from .storage.parquet import file_hash, safe_path

FIELDS = (
    "subject", "predicate", "object", "relation", "primary_knowledge_source",
    "knowledge_level", "agent_type", "publications", "source_citation",
    "source_citation_base64", "prego_evidence", "source_record", "source_column",
    "value", "value_encoding", "has_percentage", "original_subject", "original_object",
)
EVIDENCE = ("publications", "source_citation", "source_citation_base64", "prego_evidence")
SCHEMA = pa.schema([
    ("row_number", pa.int64()), ("occurrence_id", pa.string()), ("row_sha256", pa.string()),
    *[(name, pa.string()) for name in FIELDS],
])


def _checked_file(root, entry):
    relative = Path(entry["path"])
    if relative.is_absolute() or ".." in relative.parts:
        raise CurationError("Invalid partition path")
    path = safe_path(root / relative)
    if path.stat().st_size != entry["bytes"] or file_hash(path) != entry["sha256"]:
        raise CurationError("Input partition integrity mismatch")
    return path


def _space(path, reserve_bytes):
    if shutil.disk_usage(path).free < reserve_bytes:
        raise CurationError("Free disk space is below the configured reserve")


def _write_json(path, data):
    # Exclusive destination: the manifest is written last, after read-back checks.
    with path.open("x") as handle:
        json.dump(data, handle, sort_keys=True, indent=2)
        handle.write("\n")


def prepare_inventory(manifest_path: Path, expected_sha256: str, output: Path, *,
                      partition_limit: int | None = 1, reserve_bytes: int = 10 * 1024**3):
    """Stream selected whole partitions, verify identities, join pinned nodes, profile exactly.

    Defaults to one real partition. A partial run does not verify unselected
    partitions, replay native decisions, or certify the entire source export.
    """
    started = time.monotonic()
    manifest_path = safe_path(manifest_path)
    data, manifest = _metadata(manifest_path)
    if hashlib.sha256(data).hexdigest() != expected_sha256:
        raise CurationError("Census manifest hash mismatch")
    if manifest.get("contract") != CENSUS_FORMAT:
        raise CurationError("Unexpected census contract")
    if partition_limit is not None and (type(partition_limit) is not int or partition_limit < 1):
        raise CurationError("Partition limit must be positive or None")
    source = manifest["source"]
    source_data, original = _metadata(manifest_path.parent / "source-manifest.json")
    if hashlib.sha256(source_data).hexdigest() != source["manifest_sha256"]:
        raise CurationError("Source manifest hash mismatch")
    member = original["members"][source["edge_member"]]
    if (member["sha256"], member["rows"]) != (
        source["edge_member_sha256"], source["source_rows"]
    ):
        raise CurationError("Source edge binding mismatch")
    header = source["header"]
    if len(set(header)) != len(header) or not {"subject", "predicate", "object"} <= set(header):
        raise CurationError("Invalid source header")
    header_bytes = bytes.fromhex(source["header_hex"])
    if header_bytes.decode().rstrip("\r\n").split("\t") != header:
        raise CurationError("Source header mismatch")
    partitions = manifest["partitions"]
    next_row = 1
    for entry in partitions:
        if entry["first_row"] != next_row or entry["last_row"] != next_row + entry["rows"] - 1:
            raise CurationError("Noncontiguous partition descriptors")
        if entry["rows"] <= 0:
            raise CurationError("Empty partition")
        next_row = entry["last_row"] + 1
    if next_row - 1 != source["selected_rows"]:
        raise CurationError("Partition coverage mismatch")
    selected = partitions if partition_limit is None else partitions[:partition_limit]
    if not selected:
        raise CurationError("No partitions selected")
    node_entry = original["members"]["merged-kg_nodes.tsv"]
    nodes = safe_path(Path(source["snapshot_path"]) / "merged-kg_nodes.tsv")
    if nodes.stat().st_size != node_entry["bytes"] or file_hash(nodes) != node_entry["sha256"]:
        raise CurationError("Node source integrity mismatch")
    output = safe_path(output, exists=False)
    _space(output.parent, reserve_bytes)
    output.mkdir()  # Refuse replacement, including failed previous runs.
    (output / "partitions").mkdir()
    connection = duckdb.connect(str(output / "inventory.duckdb"), config={
        "memory_limit": "512MB", "threads": "2", "max_temp_directory_size": "4GB",
        "temp_directory": str(output / "spill"), "preserve_insertion_order": "false",
    })
    descriptors = []
    prefix_hash = hashlib.sha256(header_bytes)
    row_number = 0
    try:
        connection.execute("CREATE TABLE nodes AS SELECT id, name, category FROM read_csv(?, "
                           "delim='\t', header=true, all_varchar=true, quote='', "
                           "escape='', nullstr='', strict_mode=true)", [str(nodes)])
        count, unique, missing = connection.execute(
            "SELECT count(*),count(DISTINCT id),count(*) FILTER(WHERE id IS NULL) FROM nodes"
        ).fetchall()[0]
        if count != node_entry["rows"] or count != unique or missing:
            raise CurationError("Node IDs must be unique and nonempty; node count must match")
        if file_hash(nodes) != node_entry["sha256"]:
            raise CurationError("Nodes changed during indexing")
        for index, entry in enumerate(selected):
            _space(output, reserve_bytes)
            path = _checked_file(manifest_path.parent, entry)
            destination = output / "partitions" / f"inventory-{index:05d}.parquet"
            writer = None
            start = row_number
            try:
                for batch in pq.ParquetFile(path).iter_batches(batch_size=20_000, columns=[
                    "row_number", "occurrence_id", "row_sha256", "source_row",
                ]):
                    records = []
                    for item in batch.to_pylist():
                        row_number += 1
                        raw = item["source_row"]
                        digest = hashlib.sha256(raw).hexdigest()
                        expected_id = occurrence_id(
                            manifest_sha256=source["manifest_sha256"], member=source["edge_member"],
                            member_sha256=source["edge_member_sha256"], row_number=row_number,
                            row_sha256=digest,
                        )
                        if (item["row_number"], item["row_sha256"], item["occurrence_id"]) != (
                            row_number, digest, expected_id
                        ):
                            raise CurationError("Occurrence identity mismatch")
                        prefix_hash.update(raw)
                        fields = _decode_row(raw, header)
                        records.append({"row_number": row_number, "occurrence_id": expected_id,
                                        "row_sha256": digest,
                                        **{key: fields.get(key, "") for key in FIELDS}})
                    connection.register("batch", pa.Table.from_pylist(records, schema=SCHEMA))
                    table = connection.execute(
                        "SELECT b.*, s.id IS NOT NULL AS subject_present_in_nodes, "
                        "o.id IS NOT NULL AS object_present_in_nodes, "
                        "s.name AS subject_label,s.category AS subject_category, "
                        "o.name AS object_label,o.category AS object_category, "
                        "CASE WHEN s.id IS NULL OR o.id IS NULL THEN 'missing_node' "
                        "WHEN coalesce(trim(s.name),'')='' OR coalesce(trim(o.name),'')='' "
                        "OR coalesce(trim(s.category),'')='' OR coalesce(trim(o.category),'')='' "
                        "THEN 'missing_label_or_category' ELSE 'present' END AS endpoint_status, "
                        "'unassessed' AS content_status FROM batch b "
                        "LEFT JOIN nodes s ON b.subject=s.id LEFT JOIN nodes o ON b.object=o.id "
                        "ORDER BY b.row_number"
                    ).to_arrow_table()
                    connection.unregister("batch")
                    if table.num_rows != len(records):
                        raise CurationError("Node join multiplied occurrences")
                    if writer is None:
                        writer = pq.ParquetWriter(destination, table.schema, compression="zstd")
                    writer.write_table(table)
            finally:
                if writer is not None:
                    writer.close()
            if row_number - start != entry["rows"] or row_number != entry["last_row"]:
                raise CurationError("Partition row count mismatch")
            _checked_file(manifest_path.parent, entry)  # Detect input changes during scan.
            # Compare persisted output identities with the canonical input in both directions.
            mismatch = connection.execute(
                "SELECT count(*) FROM ((SELECT row_number,occurrence_id,row_sha256 "
                "FROM read_parquet(?) EXCEPT ALL SELECT row_number,occurrence_id,row_sha256 "
                "FROM read_parquet(?)) UNION ALL (SELECT row_number,occurrence_id,row_sha256 "
                "FROM read_parquet(?) EXCEPT ALL SELECT row_number,occurrence_id,row_sha256 "
                "FROM read_parquet(?)))", [str(destination), str(path), str(path), str(destination)]
            ).fetchall()[0][0]
            if mismatch:
                raise CurationError("Persisted occurrence parity mismatch")
            descriptors.append({"path": str(destination.relative_to(output)),
                                "rows": row_number - start, "bytes": destination.stat().st_size,
                                "sha256": file_hash(destination), "source_path": entry["path"],
                                "source_sha256": entry["sha256"]})
        full = row_number == source["source_rows"]
        if full and prefix_hash.hexdigest() != source["edge_member_sha256"]:
            raise CurationError("Reconstructed full source hash mismatch")
        files = [str(output / item["path"]) for item in descriptors]
        connection.read_parquet(files).create_view("inventory")
        evidence_condition = " OR ".join(f"{name}<>''" for name in EVIDENCE)
        result = connection.execute(
            "SELECT primary_knowledge_source,count(*) AS occurrences, "
            "count(DISTINCT (subject,predicate,object)) AS distinct_spo, "
            "count(DISTINCT subject) AS distinct_subjects,count(DISTINCT object) AS distinct_objects, "
            "count(DISTINCT (predicate,object)) AS distinct_predicate_objects, "
            f"count(*) FILTER(WHERE {evidence_condition}) AS inline_evidence_occurrences, "
            "count(*) FILTER(WHERE endpoint_status='missing_node') AS missing_node_occurrences, "
            "count(*) FILTER(WHERE endpoint_status='missing_label_or_category') "
            "AS incomplete_node_occurrences FROM inventory GROUP BY primary_knowledge_source "
            "ORDER BY occurrences DESC,primary_knowledge_source"
        )
        names = [item[0] for item in result.description]
        profile = [dict(zip(names, row, strict=True)) for row in result.fetchall()]
        if sum(item["occurrences"] for item in profile) != row_number:
            raise CurationError("Profile reconciliation failed")
        if file_hash(manifest_path) != expected_sha256:
            raise CurationError("Census manifest changed during run")
        receipt = {"artifact_type": "content-review-preparation/v1", "scientific_reviews": 0,
                   "scientific_approvals": 0, "content_status": "unassessed",
                   "census_manifest_sha256": expected_sha256, "source": source,
                   "nodes_sha256": node_entry["sha256"], "rows": row_number,
                   "complete_population": full, "selected_source_sha256": prefix_hash.hexdigest(),
                   "partitions": descriptors, "profile": profile,
                   "elapsed_seconds": round(time.monotonic() - started, 3),
                   "limitations": ["Endpoint presence is not semantic validity.",
                                   "Inline evidence is unverified; absence remains explicit.",
                                   "Native review decisions have not been replayed.",
                                   "Unselected partition bytes were not verified."]}
        _write_json(output / "manifest.json", receipt)
        return receipt
    finally:
        connection.close()
