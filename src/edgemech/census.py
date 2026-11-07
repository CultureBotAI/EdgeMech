"""Exact native-scope conformance over every pinned KG source occurrence.

An SPO match is a candidate only. Inherited eligibility requires an embedded
``native_assertion`` JSON envelope exactly matching a validated native export,
and ``native_scope`` equal to that envelope's explicit context scope. This is
transport conformance, not a biological projection rule or scientific review.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
from collections import Counter
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
from kg_microbe_curation.artifact import validate_relative_path
from kg_microbe_curation.identity import (
    CurationError,
    canonical_json,
    occurrence_id,
    sha256_json,
)
from kg_microbe_curation.native import (
    MAX_NATIVE_BYTES,
    NATIVE_CONTRACT,
    validate_native_assertion,
)

from .storage.parquet import MAX_ROW_BYTES, file_hash, safe_path

CENSUS_FORMAT = "edgemech-native-overlap-census/v1"
CLASSIFICATIONS = (
    "exact_eligible", "incompatible_scope", "ambiguous_mapping",
    "unavailable_evidence_export", "unmatched",
)
BATCH_ROWS = 20_000
MAX_BATCH_BYTES = 32 * 1024 * 1024
MAX_METADATA_BYTES = 16 * 1024 * 1024
MAX_CANDIDATES = 10_000
CENSUS_SCHEMA = pa.schema([
    ("row_number", pa.int64()), ("occurrence_id", pa.string()),
    ("row_sha256", pa.string()), ("source_row", pa.binary()),
    ("classification", pa.string()), ("candidate_assertion_ids", pa.list_(pa.string())),
    ("eligible_assertion_ids", pa.list_(pa.string())),
    ("endpoint_candidate_count", pa.int64()), ("reasons", pa.list_(pa.string())),
])


def _sha(value):
    if not isinstance(value, str) or re.fullmatch("[0-9a-f]{64}", value) is None:
        raise CurationError("Expected a lowercase SHA-256 digest")
    return value


def _integer(value):
    if type(value) is not int or value < 0:
        raise CurationError("Expected an exact nonnegative integer")
    return value


def _object_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise CurationError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _json(data):
    try:
        result = json.loads(data, object_pairs_hook=_object_pairs)
        canonical_json(result)
        return result
    except (ValueError, UnicodeError, RecursionError) as error:
        raise CurationError(f"Invalid JSON: {error}") from error


@contextmanager
def _read_handle(path):
    path = safe_path(path)
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise CurationError("Census input must be a regular file")
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            yield handle
        after = os.fstat(descriptor)
        if (before.st_size, before.st_mtime_ns, before.st_ino) != (
            after.st_size, after.st_mtime_ns, after.st_ino
        ):
            raise CurationError("Census input changed while reading")
    finally:
        os.close(descriptor)


def _metadata(path):
    path = safe_path(path)
    with _read_handle(path) as handle:
        data = handle.read(MAX_METADATA_BYTES + 1)
    if len(data) > MAX_METADATA_BYTES:
        raise CurationError("Metadata exceeds 16 MiB")
    value = _json(data)
    if type(value) is not dict:
        raise CurationError("Metadata must be an object")
    return data, value


@contextmanager
def _catalog():
    with tempfile.TemporaryDirectory(prefix="edgemech-census-query-") as temporary:
        connection = duckdb.connect(str(Path(temporary) / "native.duckdb"), config={
            "memory_limit": "256MB", "threads": "2", "temp_directory": temporary,
        })
        try:
            connection.execute("CREATE TABLE native (id VARCHAR PRIMARY KEY, subject VARCHAR, "
                               "predicate VARCHAR, object VARCHAR, document VARCHAR)")
            connection.execute("CREATE TABLE evidence (binding VARCHAR)")
            connection.execute("CREATE TABLE ancestry (binding VARCHAR)")
            yield connection
        finally:
            connection.close()


def _native_exports(connection, exports, destination=None, expected=None):
    """Verify every native line and persist immutable original export bytes."""
    descriptors, total = [], 0
    connection.execute("BEGIN TRANSACTION")
    if expected is not None and len(expected) != len(exports):
        raise CurationError("Expected one native manifest pin per export")
    for position, export in enumerate(exports):
        manifest_path = Path(export)
        if manifest_path.is_dir():
            manifest_path = manifest_path / "manifest.json"
        data, manifest = _metadata(manifest_path)
        digest = hashlib.sha256(data).hexdigest()
        if expected is not None and digest != _sha(expected[position]):
            raise CurationError("Native export manifest hash mismatch")
        if manifest.get("contract") != NATIVE_CONTRACT or manifest.get("schema_version") != 1:
            raise CurationError("Unsupported native export manifest")
        if manifest.get("independent_scientific_reviews") != 0 or manifest.get("kg_occurrences_approved") != 0:
            raise CurationError("Native transport cannot claim independent scientific approvals")
        _integer(manifest.get("rows"))
        _integer(manifest.get("assertions_bytes"))
        _sha(manifest.get("assertions_sha256"))
        if type(manifest.get("native_status_counts")) is not dict:
            raise CurationError("Native export must declare status counts")
        if any(key not in {"supported", "withheld", "unassessed"}
               for key in manifest["native_status_counts"]):
            raise CurationError("Unknown native review status")
        for value in manifest["native_status_counts"].values():
            _integer(value)
        source = safe_path(manifest_path.parent / "assertions.jsonl")
        output = None
        if destination is not None:
            target = destination / "native" / f"export-{position:04d}"
            target.mkdir(parents=True)
            (target / "manifest.json").write_bytes(data)
            output = (target / "assertions.jsonl").open("wb")
        hasher, size, rows, statuses = hashlib.sha256(), 0, 0, Counter()
        try:
            with _read_handle(source) as handle:
                while line := handle.readline(MAX_NATIVE_BYTES + 2):
                    if len(line) > MAX_NATIVE_BYTES + 1:
                        raise CurationError("Native JSONL row exceeds its bound")
                    hasher.update(line)
                    size += len(line)
                    if output is not None:
                        output.write(line)
                    assertion = _json(line)
                    validate_native_assertion(assertion)
                    if manifest.get("source_commit") is not None and (
                        assertion["native_locator"]["commit"] != manifest["source_commit"]
                    ):
                        raise CurationError("Native source commit differs from export pin")
                    encoded = canonical_json(assertion).decode("utf-8")
                    existing_rows = connection.execute(
                        "SELECT document FROM native WHERE id=?", [assertion["assertion_id"]]
                    ).fetchall()
                    existing = existing_rows[0] if existing_rows else None
                    if existing is not None and existing[0] != encoded:
                        raise CurationError("Conflicting duplicate native assertion")
                    if existing is None:
                        payload = assertion["payload"]
                        connection.execute("INSERT INTO native VALUES (?,?,?,?,?)", [
                            assertion["assertion_id"], payload["subject"], payload["predicate"],
                            payload["object"], encoded,
                        ])
                        for evidence in assertion["evidence"]:
                            locator = evidence["locator"]
                            binding = {key: locator[key] for key in ("repository", "commit", "path")}
                            binding["sha256"] = evidence["sha256"]
                            connection.execute("INSERT INTO evidence VALUES (?)", [sha256_json(binding)])
                            for ancestor in evidence["ancestry"]:
                                connection.execute("INSERT INTO ancestry VALUES (?)", [sha256_json({
                                    "repository": locator["repository"], "commit": locator["commit"],
                                    "ancestor": ancestor,
                                })])
                    rows += 1
                    statuses[assertion["native_review"]["status"]] += 1
        finally:
            if output is not None:
                output.close()
        if (size, rows, hasher.hexdigest()) != (
            manifest["assertions_bytes"], manifest["rows"], manifest["assertions_sha256"]
        ) or dict(statuses) != manifest["native_status_counts"]:
            raise CurationError("Native export file hashes, rows or counters do not reconcile")
        if file_hash(manifest_path) != digest:
            raise CurationError("Native manifest changed while reading")
        descriptors.append({
            "path": f"native/export-{position:04d}/manifest.json", "sha256": digest,
            "assertions_sha256": hasher.hexdigest(), "rows": rows,
            "source_commit": manifest.get("source_commit"),
        })
        total += rows
    connection.execute("CREATE TABLE endpoints AS SELECT subject,object,count(*) AS n "
                       "FROM native GROUP BY subject,object")
    connection.execute("CREATE TABLE triples AS SELECT subject,predicate,object," 
                       "list(id ORDER BY id) AS ids FROM native GROUP BY subject,predicate,object")
    distinct = connection.execute("SELECT count(*) FROM native").fetchall()[0][0]
    accounting = {"export_rows": total, "distinct_assertions": distinct,
                  "duplicate_assertion_rows": total - distinct,
                  "distinct_native_observations": None, "distinct_native_claims": None,
                  "independent_experiments": None}
    for table in ("evidence", "ancestry"):
        references, unique = connection.execute(
            f"SELECT count(*),count(DISTINCT binding) FROM {table}"
        ).fetchall()[0]
        accounting[f"{table}_references"] = references
        accounting[f"distinct_{table}_bindings"] = unique
        accounting[f"shared_{table}_references"] = references - unique
    connection.execute("COMMIT").fetchall()
    return descriptors, accounting


def _decode_row(raw, header):
    try:
        text = raw.decode("utf-8")
    except UnicodeError as error:
        raise CurationError("Source row is not UTF-8") from error
    text = text[:-2] if text.endswith("\r\n") else text[:-1] if text.endswith("\n") else text
    fields = text.split("\t")
    if len(fields) != len(header):
        raise CurationError("Source row width differs from its header")
    return dict(zip(header, fields, strict=True))


def _classifier(connection):
    @lru_cache(maxsize=4)
    def assertion(identifier):
        rows = connection.execute("SELECT document FROM native WHERE id=?", [identifier]).fetchall()
        if not rows:
            raise CurationError("Candidate assertion is missing from native inventory")
        return _json(rows[0][0])

    def classify(source, candidates, endpoint_count):
        if len(candidates) > MAX_CANDIDATES:
            raise CurationError("A source occurrence exceeds the bounded candidate limit")
        if not candidates:
            if endpoint_count:
                return "incompatible_scope", [], ["endpoint_candidate_has_different_predicate"]
            return "unmatched", [], ["no_exact_subject_predicate_object_candidate"]
        native, native_bytes = [], 0
        for identifier in candidates:
            item = assertion(identifier)
            native_bytes += len(canonical_json(item))
            if native_bytes > MAX_BATCH_BYTES:
                raise CurationError("Candidate native payloads exceed the bounded byte limit")
            native.append(item)
        embedded = None
        if source.get("native_assertion"):
            try:
                embedded = _json(source["native_assertion"])
                validate_native_assertion(embedded)
            except CurationError:
                return "incompatible_scope", [], ["invalid_embedded_native_assertion"]
        eligible, reasons = [], set()
        for item in native:
            if item["native_review"]["status"] != "supported":
                reasons.add("native_" + item["native_review"]["status"])
                continue
            scope = item["payload"]["context"].get("scope")
            if not isinstance(scope, str) or not scope or source.get("native_scope") != scope:
                reasons.add("missing_or_different_explicit_native_scope")
                continue
            if embedded is None or canonical_json(embedded) != canonical_json(item):
                reasons.add("missing_or_different_complete_native_payload_evidence_binding")
                continue
            optional_bindings = {
                "native_assertion_id": item["assertion_id"],
                "native_payload_sha256": item["native_locator"]["payload_sha256"],
                "native_evidence_sha256": sha256_json(item["evidence"]),
                "native_context_sha256": sha256_json(item["payload"]["context"]),
                "native_interpretation_sha256": sha256_json(item["payload"]["interpretation"]),
                "native_review_sha256": item["native_review"]["sha256"],
            }
            if any(key in source and source[key] != value for key, value in optional_bindings.items()):
                reasons.add("contradictory_optional_native_binding")
                continue
            eligible.append(item["assertion_id"])
        if len(eligible) == 1:
            return "exact_eligible", eligible, ["exact_inherited_scope_transport_conformance_only"]
        if len(eligible) > 1:
            return "ambiguous_mapping", [], ["multiple_exact_inherited_bindings"]
        supported = [item for item in native if item["native_review"]["status"] == "supported"]
        if len(supported) > 1:
            return "ambiguous_mapping", [], sorted(reasons | {"multiple_native_candidates_without_exact_binding"})
        if all(item["native_review"]["status"] == "unassessed" for item in native):
            return "unavailable_evidence_export", [], sorted(reasons)
        return "incompatible_scope", [], sorted(reasons)

    return classify


def _classify_batch(connection, classify, records, header, source):
    decoded = [_decode_row(raw, header) for _, raw in records]
    input_rows = pa.Table.from_pylist([
        {"position": index, "subject": row["subject"], "predicate": row["predicate"],
         "object": row["object"]} for index, row in enumerate(decoded)
    ], schema=pa.schema([("position", pa.int64()), ("subject", pa.string()),
                         ("predicate", pa.string()), ("object", pa.string())]))
    connection.register("source_batch", input_rows)
    matches = connection.execute(
        "SELECT b.position,t.ids,coalesce(e.n,0) FROM source_batch b "
        "LEFT JOIN triples t ON b.subject=t.subject AND b.predicate=t.predicate AND b.object=t.object "
        "LEFT JOIN endpoints e ON b.subject=e.subject AND b.object=e.object ORDER BY b.position"
    ).fetchall()
    connection.unregister("source_batch")
    result = []
    for position, candidates, endpoints in matches:
        number, raw = records[position]
        candidates = candidates or []
        category, eligible, reasons = classify(decoded[position], candidates, endpoints)
        row_sha = hashlib.sha256(raw).hexdigest()
        result.append({
            "row_number": number, "occurrence_id": occurrence_id(
                manifest_sha256=source["manifest_sha256"], member=source["edge_member"],
                member_sha256=source["edge_member_sha256"], row_number=number, row_sha256=row_sha,
            ), "row_sha256": row_sha, "source_row": raw, "classification": category,
            "candidate_assertion_ids": candidates, "eligible_assertion_ids": eligible,
            "endpoint_candidate_count": endpoints, "reasons": reasons,
        })
    return result


def _snapshot(snapshot, expected):
    data, manifest = _metadata(snapshot / "manifest.json")
    if hashlib.sha256(data).hexdigest() != _sha(expected):
        raise CurationError("Source manifest hash mismatch")
    members = manifest.get("members")
    if type(members) is not dict or not members or type(manifest.get("provenance")) is not dict:
        raise CurationError("Snapshot requires member digests and producer provenance")
    edges = []
    for name, member in members.items():
        validate_relative_path(name)
        if type(member) is not dict:
            raise CurationError("Invalid source member descriptor")
        _integer(member.get("bytes"))
        _integer(member.get("rows"))
        _sha(member.get("sha256"))
        if name.endswith("_edges.tsv"):
            edges.append(name)
    if len(edges) != 1:
        raise CurationError("Expected exactly one pinned KG edge member")
    return data, manifest, edges[0]


def _verify_source(source, original):
    """Anchor every selected row to its actual hash-verified source member."""
    snapshot = safe_path(Path(source["snapshot_path"]))
    _, current, edge = _snapshot(snapshot, source["manifest_sha256"])
    if current != original or edge != source["edge_member"]:
        raise CurationError("Original source manifest changed")
    prefix = hashlib.sha256()
    for name, member in original["members"].items():
        digest, size, rows = hashlib.sha256(), 0, -1
        with _read_handle(snapshot / name) as handle:
            while raw := handle.readline(MAX_ROW_BYTES + 1):
                if len(raw) > MAX_ROW_BYTES:
                    raise CurationError("Source row exceeds the bounded row size")
                digest.update(raw)
                size += len(raw)
                rows += 1
                if name == edge and rows <= source["selected_rows"]:
                    prefix.update(raw)
                    if rows == 0 and raw.hex() != source["header_hex"]:
                        raise CurationError("Source header byte binding mismatch")
        if (size, rows, digest.hexdigest()) != (member["bytes"], member["rows"], member["sha256"]):
            raise CurationError(f"Original source member hash, bytes or rows mismatch: {name}")
    if file_hash(snapshot / "manifest.json") != source["manifest_sha256"]:
        raise CurationError("Source manifest changed during verification")
    return prefix.hexdigest()


def _write_partition(stage, records):
    name = f"partitions/rows-{records[0]['row_number']:012d}-{records[-1]['row_number']:012d}.parquet"
    path = stage / name
    path.parent.mkdir(exist_ok=True)
    pq.write_table(pa.Table.from_pylist(records, schema=CENSUS_SCHEMA), path,
                   compression="zstd", row_group_size=BATCH_ROWS)
    return {"path": name, "sha256": file_hash(path), "bytes": path.stat().st_size,
            "rows": len(records), "first_row": records[0]["row_number"],
            "last_row": records[-1]["row_number"]}


def _fsync_directory(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def run_census(snapshot: Path, native_exports: list[Path], output: Path,
               expected_manifest_sha256: str, limit: int | None = None, *,
               expected_native_manifest_sha256: list[str] | None = None) -> Path:
    """Verify all input bytes and atomically publish one immutable census directory.

    ``limit`` selects an initial occurrence prefix; every source member including
    unselected tails is still hashed and counted. Existing outputs are refused.
    """
    snapshot, output = safe_path(snapshot), safe_path(output, exists=False)
    if limit is not None and (type(limit) is not int or limit < 1):
        raise CurationError("Census limit must be a positive exact integer")
    if output.exists():
        raise CurationError("Refusing to replace an existing census output")
    data, manifest, edge_member = _snapshot(snapshot, expected_manifest_sha256)
    source = {"manifest_sha256": expected_manifest_sha256,
              "snapshot_path": str(snapshot),
              "edge_member": edge_member, "edge_member_sha256": manifest["members"][edge_member]["sha256"],
              "producer_provenance_sha256": sha256_json(manifest["provenance"]),
              "source_rows": manifest["members"][edge_member]["rows"]}
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".census-stage-", dir=output.parent) as temporary:
        stage = Path(temporary) / "generation"
        stage.mkdir()
        (stage / "source-manifest.json").write_bytes(data)
        with _catalog() as connection:
            exports, native_counts = _native_exports(connection, native_exports, stage,
                                                       expected_native_manifest_sha256)
            classify = _classifier(connection)
            partitions, counts, selected, endpoint_rows, candidate_rows = [], Counter(), 0, 0, 0
            header = None
            for name, member in manifest["members"].items():
                path = safe_path(snapshot / name)
                digest, size, count, batch, batch_bytes = hashlib.sha256(), 0, -1, [], 0
                with _read_handle(path) as handle:
                    while raw := handle.readline(MAX_ROW_BYTES + 1):
                        if len(raw) > MAX_ROW_BYTES:
                            raise CurationError("Source row exceeds the bounded row size")
                        digest.update(raw)
                        size += len(raw)
                        count += 1
                        if name == edge_member and count == 0:
                            header = list(_decode_row(raw, range(len(raw.split(b"\t")))).values())
                            source["header_hex"] = raw.hex()
                            if len(set(header)) != len(header) or not {"subject", "predicate", "object"}.issubset(header):
                                raise CurationError("Invalid or duplicate KG edge header")
                        if name == edge_member and count > 0 and (limit is None or count <= limit):
                            batch.append((count, raw))
                            batch_bytes += len(raw)
                        if batch and (len(batch) >= BATCH_ROWS or batch_bytes >= MAX_BATCH_BYTES):
                            result = _classify_batch(connection, classify, batch, header, source)
                            partitions.append(_write_partition(stage, result))
                            counts.update(row["classification"] for row in result)
                            endpoint_rows += sum(row["endpoint_candidate_count"] > 0 for row in result)
                            candidate_rows += sum(bool(row["candidate_assertion_ids"]) for row in result)
                            selected += len(result)
                            batch, batch_bytes = [], 0
                if (size, count, digest.hexdigest()) != (member["bytes"], member["rows"], member["sha256"]):
                    raise CurationError(f"Source member bytes, rows or hash mismatch: {name}")
                if batch:
                    result = _classify_batch(connection, classify, batch, header, source)
                    partitions.append(_write_partition(stage, result))
                    counts.update(row["classification"] for row in result)
                    endpoint_rows += sum(row["endpoint_candidate_count"] > 0 for row in result)
                    candidate_rows += sum(bool(row["candidate_assertion_ids"]) for row in result)
                    selected += len(result)
            if header is None:
                raise CurationError("Missing edge header")
            if file_hash(snapshot / "manifest.json") != expected_manifest_sha256:
                raise CurationError("Source manifest changed during census")
            source.update(selected_rows=selected, complete_export=selected == source["source_rows"],
                          header=header, selection="initial_source_row_prefix", limit=limit)
            receipt = {
                "contract": CENSUS_FORMAT, "source": source, "native_exports": exports,
                "native_accounting": native_counts, "partitions": partitions,
                "counts": {name: counts[name] for name in CLASSIFICATIONS},
                "endpoint_candidate_occurrences": endpoint_rows,
                "spo_candidate_occurrences": candidate_rows,
                "independent_scientific_reviews": 0, "kg_occurrences_approved": 0,
                "eligibility_semantics": "exact inherited-scope transport conformance only",
            }
            receipt_path = stage / "census-manifest.json"
            receipt_path.write_bytes(canonical_json(receipt) + b"\n")
        verify_census(receipt_path)
        for path in stage.rglob("*"):
            if path.is_file():
                with path.open("rb") as handle:
                    os.fsync(handle.fileno())
        for directory, _, _ in os.walk(stage, topdown=False):
            _fsync_directory(Path(directory))
        if output.exists() or output.is_symlink():
            raise CurationError("Census destination appeared during staging")
        stage.rename(output)
        _fsync_directory(output.parent)
    return output / "census-manifest.json"


def verify_census(receipt: Path) -> dict:
    """Replay conformance from persisted native envelopes and exact source rows."""
    receipt = safe_path(receipt)
    _, manifest = _metadata(receipt)
    if manifest.get("contract") != CENSUS_FORMAT:
        raise CurationError("Unsupported census contract")
    if manifest.get("independent_scientific_reviews") != 0 or manifest.get("kg_occurrences_approved") != 0:
        raise CurationError("Census cannot assert scientific approvals")
    root, source = receipt.parent, manifest["source"]
    source_data, original = _metadata(root / "source-manifest.json")
    if hashlib.sha256(source_data).hexdigest() != _sha(source["manifest_sha256"]):
        raise CurationError("Persisted source manifest hash mismatch")
    if sha256_json(original["provenance"]) != source["producer_provenance_sha256"]:
        raise CurationError("Producer provenance binding mismatch")
    member = original["members"][source["edge_member"]]
    if (member["sha256"], member["rows"]) != (source["edge_member_sha256"], source["source_rows"]):
        raise CurationError("Source edge member binding mismatch")
    selected = _integer(source["selected_rows"])
    if selected > source["source_rows"] or source["complete_export"] != (selected == source["source_rows"]):
        raise CurationError("Source census population does not reconcile")
    expected_rows = source["source_rows"] if source["limit"] is None else min(source["limit"], source["source_rows"])
    if selected != expected_rows or source["selection"] != "initial_source_row_prefix":
        raise CurationError("Source selection differs from the declared prefix")
    try:
        header_bytes = bytes.fromhex(source["header_hex"])
    except (ValueError, TypeError) as error:
        raise CurationError("Invalid source header byte encoding") from error
    if list(_decode_row(header_bytes, range(len(header_bytes.split(b"\t")))).values()) != source["header"]:
        raise CurationError("Source header columns differ from exact header bytes")
    selected_source_sha256 = _verify_source(source, original)
    persisted_source = hashlib.sha256(header_bytes)
    exports = []
    for item in manifest["native_exports"]:
        validate_relative_path(item["path"])
        exports.append(safe_path(root / item["path"]))
    with _catalog() as connection:
        export_descriptors, native_counts = _native_exports(
            connection, exports, expected=[item["sha256"] for item in manifest["native_exports"]]
        )
        if export_descriptors != manifest["native_exports"] or native_counts != manifest["native_accounting"]:
            raise CurationError("Native inventory accounting mismatch")
        classify = _classifier(connection)
        counts, total, endpoint_rows, candidate_rows, paths = Counter(), 0, 0, 0, []
        seen = set()
        for partition in manifest["partitions"]:
            validate_relative_path(partition["path"])
            if partition["path"] in seen or not partition["path"].endswith(".parquet"):
                raise CurationError("Duplicate or invalid census partition path")
            seen.add(partition["path"])
            path = safe_path(root / partition["path"])
            if path.stat().st_size != partition["bytes"] or file_hash(path) != _sha(partition["sha256"]):
                raise CurationError("Census partition file binding mismatch")
            parquet = pq.ParquetFile(path)
            if parquet.schema_arrow != CENSUS_SCHEMA or parquet.metadata.num_rows != partition["rows"]:
                raise CurationError("Census partition schema or row count mismatch")
            if partition["first_row"] != total + 1 or partition["last_row"] != total + partition["rows"]:
                raise CurationError("Census partition row range does not reconcile")
            for batch in parquet.iter_batches(batch_size=BATCH_ROWS):
                persisted = batch.to_pylist()
                for offset, row in enumerate(persisted, total + 1):
                    if row["row_number"] != offset:
                        raise CurationError("Census source positions are missing, duplicated or unordered")
                recomputed = _classify_batch(connection, classify,
                                            [(row["row_number"], row["source_row"]) for row in persisted],
                                            source["header"], source)
                if recomputed != persisted:
                    raise CurationError("Persisted occurrence or classification differs from exact replay")
                for row in persisted:
                    persisted_source.update(row["source_row"])
                counts.update(row["classification"] for row in persisted)
                endpoint_rows += sum(row["endpoint_candidate_count"] > 0 for row in persisted)
                candidate_rows += sum(bool(row["candidate_assertion_ids"]) for row in persisted)
                total += len(persisted)
            paths.append(str(path))
        expected_counts = {name: counts[name] for name in CLASSIFICATIONS}
        if total != selected or expected_counts != manifest["counts"]:
            raise CurationError("Census counts do not reconcile")
        if persisted_source.hexdigest() != selected_source_sha256:
            raise CurationError("Persisted source rows differ from the pinned original prefix")
        if (endpoint_rows, candidate_rows) != (manifest["endpoint_candidate_occurrences"], manifest["spo_candidate_occurrences"]):
            raise CurationError("Census candidate counters do not reconcile")
        if paths:
            grouped = connection.from_parquet(paths, hive_partitioning=False).aggregate(
                "classification,count(*) AS n", "classification"
            ).fetchall()
            if dict(grouped) != dict(counts):
                raise CurationError("DuckDB census reconciliation failed")
    return manifest
