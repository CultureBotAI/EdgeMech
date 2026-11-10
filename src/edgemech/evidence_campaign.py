"""Small pinned occurrence cohorts and deduplicated citation queues.

These are retrieval work products, not new shared scientific-review contracts.
Canonical identities and raw source rows remain those of the pinned census.
"""
from __future__ import annotations

import base64
import bisect
import hashlib
import json
import os
import re
from collections import defaultdict
from pathlib import Path

import duckdb
import pyarrow.parquet as pq
from kg_microbe_curation.identity import CurationError, occurrence_id

from .census import _decode_row, _metadata
from .content_inventory import _checked_file, _space, _write_json
from .literature_probe import identifier
from .storage.parquet import file_hash, safe_path

REFERENCE_FIELDS = ("publications", "source_citation", "prego_evidence", "prego_evidence_url")
DOI = re.compile(r"\b10\.[0-9]{4,9}/[^\s<>\"|\\]+", re.I)
PMID = re.compile(r"(?:\bPMID\s*:\s*|https?://pubmed\.ncbi\.nlm\.nih\.gov/)([1-9][0-9]*)", re.I)


def references(fields):
    """Extract explicit identifiers; never resolve a bibliography by guessing."""
    found = {}
    warnings = []
    encoded = fields.get("source_citation_base64", "")
    if encoded:
        try:
            raw = base64.b64decode(encoded, validate=True)
            if fields.get("primary_knowledge_source") in {
                "infores:microbedecoder-literature", "infores:bergey-manual"
            } and fields.get("value_encoding") == "backslash":
                # KG-Microbe's documented literal-TSV producer policy. Keep the
                # original bytes; replacement decoding applies only to display.
                decoded = raw.decode("utf-8", errors="replace")
                decoded = (decoded.replace("\\", "\\\\").replace("\t", "\\t")
                           .replace("\r", "\\r").replace("\n", "\\n"))
            else:
                decoded = raw.decode("utf-8")
            if decoded != fields.get("source_citation", ""):
                warnings.append("citation_base64_plaintext_mismatch")
        except (ValueError, UnicodeError):
            warnings.append("invalid_citation_base64")
    for field in REFERENCE_FIELDS:
        text = fields.get(field, "")
        for match in DOI.finditer(text):
            token = match.group().rstrip(".,;")
            for left, right in (("(", ")"), ("[", "]"), ("{", "}")):
                while token.endswith(right) and token.count(right) > token.count(left):
                    token = token[:-1]
            try:
                kind, value = identifier(token)
            except CurationError:
                warnings.append("invalid_identifier_candidate")
                continue
            key = f"{kind}:{value}"
            found.setdefault(key, []).append({"field": field, "raw": match.group(),
                                               "start": match.start(), "end": match.end()})
        for match in PMID.finditer(text):
            key = f"pmid:{match.group(1)}"
            found.setdefault(key, []).append({"field": field, "raw": match.group(),
                                               "start": match.start(), "end": match.end()})
    return found, sorted(set(warnings))


def prepare_cohort(inventory_path: Path, inventory_sha256: str, census_path: Path,
                   source_name: str, output: Path, limit: int | None = 1):
    """Select at most 10,000 exact occurrences; preserve full raw context and labels."""
    if limit is not None and (type(limit) is not int or not 1 <= limit <= 10000):
        raise CurationError("Limit must be 1..10000 or None")
    inventory_path, census_path = safe_path(inventory_path), safe_path(census_path)
    data, inventory = _metadata(inventory_path)
    if hashlib.sha256(data).hexdigest() != inventory_sha256:
        raise CurationError("Inventory pin mismatch")
    data, census = _metadata(census_path)
    if hashlib.sha256(data).hexdigest() != inventory["census_manifest_sha256"]:
        raise CurationError("Census pin mismatch")
    files = [str(_checked_file(inventory_path.parent, part)) for part in inventory["partitions"]]
    with duckdb.connect(config={"memory_limit": "256MB", "threads": "2"}) as db:
        db.read_parquet(files).create_view("inventory")
        total = db.execute("SELECT count(*) FROM inventory WHERE primary_knowledge_source=?",
                           [source_name]).fetchall()[0][0]
        if not total or (limit is None and total > 10000):
            raise CurationError("Empty cohort or cohort exceeds 10000-occurrence bound")
        result = db.execute("SELECT * FROM inventory WHERE primary_knowledge_source=? "
                            "ORDER BY row_number LIMIT ?", [source_name, limit or 10000])
        names = [column[0] for column in result.description]
        chosen = [dict(zip(names, values, strict=True)) for values in result.fetchall()]
    requested = {row["row_number"]: row for row in chosen}
    partitions = census["partitions"]
    starts = [part["first_row"] for part in partitions]
    groups = defaultdict(set)
    for number in requested:
        index = bisect.bisect_right(starts, number) - 1
        if index < 0 or number > partitions[index]["last_row"]:
            raise CurationError("Occurrence outside census partitions")
        groups[index].add(number)
    records = []
    source = census["source"]
    for index, numbers in sorted(groups.items()):
        path = _checked_file(census_path.parent, partitions[index])
        for batch in pq.ParquetFile(path).iter_batches(columns=[
            "row_number", "occurrence_id", "row_sha256", "source_row"
        ]):
            for row in batch.to_pylist():
                number = row["row_number"]
                if number not in numbers:
                    continue
                raw = row["source_row"]
                digest = hashlib.sha256(raw).hexdigest()
                expected = occurrence_id(manifest_sha256=source["manifest_sha256"],
                                         member=source["edge_member"],
                                         member_sha256=source["edge_member_sha256"],
                                         row_number=number, row_sha256=digest)
                selected = requested[number]
                if (row["occurrence_id"], row["row_sha256"], selected["occurrence_id"],
                    selected["row_sha256"]) != (expected, digest, expected, digest):
                    raise CurationError("Canonical occurrence binding mismatch")
                fields = _decode_row(raw, source["header"])
                if fields["primary_knowledge_source"] != source_name:
                    raise CurationError("Inventory source disagrees with original row")
                refs, warnings = references(fields)
                records.append({"row_number": number, "occurrence_id": expected,
                                "row_sha256": digest, "source_row_base64": base64.b64encode(raw).decode(),
                                "fields": fields, "labels": {key: selected[key] for key in (
                                    "subject_label", "subject_category", "object_label", "object_category"
                                )}, "references": refs, "warnings": warnings})
    records.sort(key=lambda row: row["row_number"])
    if len(records) != len(chosen) or len({r["occurrence_id"] for r in records}) != len(records):
        raise CurationError("Cohort occurrence parity failure")
    queue = defaultdict(list)
    for row in records:
        if not row["warnings"]:
            for ref in row["references"]:
                queue[ref].append(row["occurrence_id"])
    output = safe_path(output, exists=False)
    _space(output.parent, 2 * 1024**3)
    output.mkdir()
    original = safe_path(census_path.parent / "source-manifest.json").read_bytes()
    if hashlib.sha256(original).hexdigest() != source["manifest_sha256"]:
        raise CurationError("Original source manifest hash mismatch")
    with (output / "source-manifest.json").open("xb") as handle:
        handle.write(original)
        handle.flush()
        os.fsync(handle.fileno())
    _write_json(output / "occurrences.json", records)
    _write_json(output / "queue.json", dict(sorted(queue.items())))
    receipt = {"source_name": source_name, "population": total, "selected": len(records),
               "inventory_sha256": inventory_sha256, "census_sha256": file_hash(census_path),
               "source": source, "queue_identifiers": len(queue),
               "without_explicit_identifier": sum(not row["references"] for row in records),
               "blocked_citation_encoding": sum(bool(row["warnings"]) for row in records),
               "occurrences_sha256": file_hash(output / "occurrences.json"),
               "queue_sha256": file_hash(output / "queue.json"), "scientific_approvals": 0}
    _write_json(output / "manifest.json", receipt)
    return receipt


def load_cohort(path: Path):
    path = safe_path(path)
    _, manifest = _metadata(path / "manifest.json")
    values = []
    for name in ("occurrences", "queue"):
        file = safe_path(path / f"{name}.json")
        if file.stat().st_size > 64 * 1024**2:
            raise CurationError("Cohort file exceeds bound")
        data = file.read_bytes()
        if hashlib.sha256(data).hexdigest() != manifest[f"{name}_sha256"]:
            raise CurationError(f"{name} hash mismatch")
        values.append(json.loads(data))
    source = manifest["source"]
    derived_queue = defaultdict(list)
    for row in values[0]:
        raw = base64.b64decode(row["source_row_base64"], validate=True)
        digest = hashlib.sha256(raw).hexdigest()
        expected = occurrence_id(manifest_sha256=source["manifest_sha256"],
                                 member=source["edge_member"],
                                 member_sha256=source["edge_member_sha256"],
                                 row_number=row["row_number"], row_sha256=digest)
        if row["row_sha256"] != digest or row["occurrence_id"] != expected:
            raise CurationError("Cohort raw occurrence identity mismatch")
        if _decode_row(raw, source["header"]) != row["fields"]:
            raise CurationError("Cohort fields differ from raw bytes")
        refs, warnings = references(row["fields"])
        if (refs, warnings) != (row["references"], row["warnings"]):
            raise CurationError("Cohort citation bindings differ from raw fields")
        if not warnings:
            for ref in refs:
                derived_queue[ref].append(expected)
    if dict(derived_queue) != values[1]:
        raise CurationError("Cohort queue is not bound to occurrences")
    return manifest, *values
