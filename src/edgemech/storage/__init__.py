"""Lossless SQLite migration into immutable, independently verified generations.

CLAW #951: complete-field comparisons and replay validate migration integrity.
Transport integrity and inherited evidence never grant scientific approval.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import sqlite3
import tempfile
import uuid
from contextlib import closing
from itertools import zip_longest
from pathlib import Path

from kg_microbe_curation import ledger as native
from kg_microbe_curation.artifact import ARTIFACT_CONTRACT, validate_artifact_manifest
from kg_microbe_curation.contract import unprocessed_decision, validate_bundle, validate_occurrence
from kg_microbe_curation.identity import CONTRACT, CurationError, canonical_json

from .parquet import (
    bucket_for,
    file_hash,
    logical_hash,
    query_connection,
    safe_path,
    table_rows,
    verify_partition,
    write_partitioned_table,
)
from .schema import AUTHORITATIVE, DIMENSIONS, TABLE_KEYS, TABLE_SCHEMAS

MAX_LOOKUP_BYTES = 2 * 1024 * 1024
RECONCILIATION_CONTRACT = "edgemech-source-table-reconciliation/v1"


def _json(path: Path):
    safe_path(path)
    return native._read_json(path)[1]


def _sql_rows(connection, name):
    columns = ",".join('"' + column + '"' for column in TABLE_SCHEMAS[name].names)
    keys = ",".join('"' + column + '"' for column in TABLE_KEYS[name])
    return connection.execute(f'SELECT {columns} FROM "{name}" ORDER BY {keys}')


def _compare(left, right, name):
    marker = object()
    for a, b in zip_longest(left, right, fillvalue=marker):
        if a is marker or b is marker or tuple(a) != tuple(b):
            raise CurationError(f"complete-field reconciliation failed for {name}")


def _source_table_digests(connection):
    result = {}
    for name in AUTHORITATIVE:
        digest, count = logical_hash(_sql_rows(connection, name), name)
        result[name] = {"logical_sha256": digest, "rows": count}
    return result


def _reconcile_source_tables(expected, generation, tables):
    """Compare independent source hashes with persisted complete-field readback."""
    actual = {}
    for name in AUTHORITATIVE:
        digest, count = logical_hash(table_rows(generation, name, tables[name]), name)
        actual[name] = {"logical_sha256": digest, "rows": count}
        if expected[name] != actual[name]:
            raise CurationError(f"source-to-output logical table mismatch: {name}")
    return {"contract": RECONCILIATION_CONTRACT, "verified": True,
            "source_tables": expected, "persisted_tables": actual}


def _assert_no_journal(path):
    for suffix in ("-wal", "-shm", "-journal"):
        sibling = Path(str(path) + suffix)
        if sibling.exists() or sibling.is_symlink():
            raise CurationError("SQLite journal/WAL sidecar exists; supply a quiescent checkpointed ledger")


def _check_sqlite_columns(connection):
    names = {row[0] for row in connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )}
    if names != set(AUTHORITATIVE):
        raise CurationError("unsupported SQLite table set; refusing to discard source tables")
    for name in AUTHORITATIVE:
        fields = [row[1] for row in connection.execute(f'PRAGMA table_info("{name}")')]
        if fields != TABLE_SCHEMAS[name].names:
            raise CurationError(f"unsupported SQLite columns in {name}; refusing field loss")


def _history(connection):
    metadata = native._metadata(connection)
    revision = hashlib.sha256(canonical_json({
        "format": native.LEDGER_FORMAT, "input_sha256": metadata["input_sha256"]
    })).hexdigest()
    total = connection.execute("SELECT COUNT(*) FROM bundles").fetchone()[0]
    for sequence in range(total):
        children = connection.execute(
            "SELECT bundle_sha256,parent_revision,revision,document FROM bundles WHERE parent_revision=?",
            (revision,),
        ).fetchmany(2)
        if len(children) != 1:
            raise CurationError("bundle history is forked or disconnected")
        digest, parent, following, document = children[0]
        if len(document.encode()) > native.MAX_JSON_BYTES:
            raise CurationError("historical bundle exceeds the canonical byte bound")
        bundle = native._decode(document.encode())
        encoded = canonical_json(bundle)
        if encoded.decode() != document or hashlib.sha256(encoded).hexdigest() != digest:
            raise CurationError("bundle bytes are noncanonical or their hash differs")
        expected = hashlib.sha256(canonical_json({
            "parent_revision": parent, "bundle_sha256": digest,
        })).hexdigest()
        if expected != following:
            raise CurationError("bundle history revision hash mismatch")
        yield sequence, digest, parent, following, bundle
        revision = following
    if metadata["revision"] != revision or metadata["applied_bundles"] != total:
        raise CurationError("history terminal revision or applied count mismatch")


def _replay(source, baseline: Path):
    for _, _, parent, _, bundle in _history(source):
        native.apply_bundle(baseline, bundle, expected_revision=parent)
    with closing(native._connect(baseline, readonly=True)) as replayed:
        for name in AUTHORITATIVE:
            _compare(_sql_rows(source, name), _sql_rows(replayed, name), name)


def _derived(connection, name):
    for sequence, digest, parent, following, bundle in _history(connection):
        if name == "history":
            yield digest, sequence, parent, following
        elif name == "memberships":
            for position, identifier in enumerate(bundle["occurrence_ids"]):
                yield identifier, digest, position
        elif name == "evidence":
            for reference in bundle["reviews"]:
                for position, item in enumerate(reference["document"]["source"]["inputs"]):
                    yield digest, reference["review_id"], position, "review_input", canonical_json(item).decode()
        else:
            identifier = {"observations": "observation_id", "claims": "claim_id", "reviews": "review_id"}[name]
            for item in bundle[name]:
                yield digest, item[identifier], canonical_json(item).decode()


def _input_hashes(ledger: Path, export: Path):
    _assert_no_journal(ledger)
    manifest = _json(export / "manifest.json")
    paths = [ledger, export / "manifest.json", export / "source-manifest.json"]
    for descriptor in manifest.get("shards", []):
        # Native ingestion also validates names; reject unsafe paths before hashing.
        paths.append(export / native._basename(descriptor["file"]))
    return {str(path): file_hash(path) for path in paths}


def _fsync_directory(path):
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_json(path, document):
    with path.open("xb") as handle:
        handle.write(canonical_json(document) + b"\n")
        handle.flush()
        os.fsync(handle.fileno())


def _publish_pointer(store: Path, manifest: Path):
    temporary = store / (".CURRENT-" + uuid.uuid4().hex)
    try:
        _write_json(temporary, {
            "manifest": manifest.relative_to(store).as_posix(),
            "sha256": file_hash(manifest),
        })
        os.link(temporary, store / "CURRENT")  # Exclusive and atomic; never replaces a reader's head.
        _fsync_directory(store)
    finally:
        temporary.unlink(missing_ok=True)


def migrate_sqlite(
    ledger: Path, export: Path, store: Path, *, buckets: int = 16, row_group_size: int = 8192
) -> Path:
    """Create a new store; preserve all source fields and verify before publishing.

    Refuses live WAL/journal state rather than silently ignoring committed pages.
    Input digests are checked before and after a consistent read-only transaction.
    Failed runs may leave an empty store or a complete unpublished generation;
    they never publish CURRENT, replace an existing store, or delete user data.
    """
    ledger, export = safe_path(ledger), safe_path(export)
    store = safe_path(store, exists=False)
    if store.exists() or store.is_symlink():
        raise CurationError("refusing to replace an existing store")
    if store.is_relative_to(export) or ledger.is_relative_to(store):
        raise CurationError("output must be separate from immutable inputs")
    before = _input_hashes(ledger, export)
    exported = _json(export / "manifest.json")
    store.mkdir(parents=False, exist_ok=False)
    generations = store / "generations"
    generations.mkdir()
    generation_id = uuid.uuid4().hex
    staging = generations / (".staging-" + generation_id)
    staging.mkdir()
    final = generations / generation_id
    try:
        with closing(native._connect(ledger, readonly=True)) as source:
            source.execute("BEGIN")
            _check_sqlite_columns(source)
            if source.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                raise CurationError("SQLite integrity check failed")
            if source.execute("PRAGMA foreign_key_check").fetchone():
                raise CurationError("SQLite references are broken")
            # Reconstruct solely through the canonical producer/ledger boundary.
            with tempfile.TemporaryDirectory(prefix="replay-", dir=staging) as directory:
                baseline = Path(directory) / "baseline.sqlite"
                native.ingest_export(export, baseline)
                _replay(source, baseline)
            source_tables = _source_table_digests(source)
            metadata = native._metadata(source)
            tables = {}
            for name in TABLE_SCHEMAS:
                rows = _sql_rows(source, name) if name in AUTHORITATIVE else _derived(source, name)
                tables[name] = write_partitioned_table(
                    staging, name, rows, buckets=buckets, row_group_size=row_group_size,
                )
            counters = {dimension: {} for dimension in DIMENSIONS}
            for dimension, value, count in _sql_rows(source, "coverage_counts"):
                counters[dimension][value] = count
            manifest = {
                "contract": ARTIFACT_CONTRACT, "identity_contract": CONTRACT,
                "generation": generation_id, "parent_manifest_sha256": None,
                "source": {
                    "input_manifest_sha256": metadata["input_sha256"],
                    "source_manifest_sha256": metadata["source_manifest_sha256"],
                    "sqlite_sha256": before[str(ledger)], "ledger_revision": metadata["revision"],
                    "selected_rows": metadata["selected_rows"], "source_rows": metadata["source_rows"],
                    "complete_export": metadata["complete_export"],
                    "edge_member": metadata["edge_member"],
                    "edge_member_sha256": exported["members"][metadata["edge_member"]]["sha256"],
                },
                "layout": {"partitioning": "sha256-first-key-modulo/v1", "buckets": buckets,
                           "row_group_size": row_group_size},
                "tables": tables, "counters": counters,
                "assurance": {"source_verification": metadata["source_verification"],
                              "scientific_review": False},
            }
            validate_artifact_manifest(manifest)
            _write_json(staging / "manifest.json", manifest)
            result = verify(staging / "manifest.json")
            reconciliation = _reconcile_source_tables(source_tables, staging, tables)
            after = _input_hashes(ledger, export)
            if before != after:
                raise CurationError("migration input changed; refusing publication")
            _write_json(staging / "migration-receipt.json", {
                "input_hashes_before": before, "input_hashes_after": after,
                "manifest_sha256": file_hash(staging / "manifest.json"),
                "verification": result,
                "source_table_reconciliation": reconciliation,
            })
        # Flush every newly created directory before making the complete generation reachable.
        for directory, _, _ in os.walk(staging, topdown=False):
            _fsync_directory(Path(directory))
        staging.rename(final)
        _fsync_directory(generations)
        _publish_pointer(store, final / "manifest.json")
        # CURRENT being durable does not persist the newly created store name.
        _fsync_directory(store.parent)
        return final / "manifest.json"
    except (sqlite3.Error, OSError, KeyError, TypeError, ValueError) as exc:
        raise CurationError(f"migration failed: {exc}") from exc
    finally:
        if staging.exists():
            shutil.rmtree(staging)  # Only this invocation's exclusively created staging tree.


def _manifest(path: Path):
    path = safe_path(path)
    document = _json(path)
    validate_artifact_manifest(document)
    return path.parent, document


def _reconstruct_sqlite(generation: Path, document: dict, database: Path):
    with closing(sqlite3.connect(database)) as connection:
        native._create_schema(connection)
        # Foreign keys require occurrences and bundles before current projections.
        for name in ("metadata", "occurrences", "bundles", "current_decisions", "coverage_counts"):
            placeholders = ",".join("?" for _ in TABLE_SCHEMAS[name])
            connection.executemany(
                f'INSERT INTO "{name}" VALUES ({placeholders})',
                table_rows(generation, name, document["tables"][name]),
            )
        connection.commit()


def _baseline_from_verified_rows(source, database: Path, descriptor: dict):
    metadata = native._metadata(source)
    expected = {
        "input_sha256": descriptor["input_manifest_sha256"],
        "source_manifest_sha256": descriptor["source_manifest_sha256"],
        "revision": descriptor["ledger_revision"], "selected_rows": descriptor["selected_rows"],
        "source_rows": descriptor["source_rows"], "complete_export": descriptor["complete_export"],
        "edge_member": descriptor["edge_member"],
    }
    if any(metadata.get(key) != value for key, value in expected.items()):
        raise CurationError("artifact source and retained metadata disagree")
    if metadata.get("format") != native.LEDGER_FORMAT:
        raise CurationError("unsupported retained ledger format")
    header = metadata.get("header")
    if not isinstance(header, list) or not header or len(set(header)) != len(header):
        raise CurationError("invalid retained header")
    with closing(sqlite3.connect(database)) as baseline:
        native._create_schema(baseline)
        count = 0
        for row in source.execute("SELECT * FROM occurrences ORDER BY row_number"):
            identifier, member, number, digest, raw = row
            count += 1
            if number != count or member != descriptor["edge_member"]:
                raise CurationError("source row ordering or member differs")
            validate_occurrence({
                "occurrence_id": identifier, "member": member, "row_number": number,
                "row_sha256": digest, "source_row": raw,
                "manifest_sha256": descriptor["source_manifest_sha256"],
                "member_sha256": descriptor["edge_member_sha256"],
            })
            body = raw.removesuffix("\n").removesuffix("\r")
            if "\n" in body or len(body.split("\t")) != len(header):
                raise CurationError("source row physical width mismatch")
            baseline.execute("INSERT INTO occurrences VALUES (?,?,?,?,?)", tuple(row))
            default = unprocessed_decision(identifier)
            baseline.execute("INSERT INTO current_decisions VALUES (?,?,?,?,?,NULL)",
                             (identifier, *(default[field] for field in DIMENSIONS)))
        if count != descriptor["selected_rows"]:
            raise CurationError("occurrence population differs")
        for key, raw in _sql_rows(source, "metadata"):
            baseline.execute("INSERT INTO metadata VALUES (?,?)", (key, raw))
        native._set_metadata(baseline, "applied_bundles", 0)
        native._set_metadata(baseline, "revision", hashlib.sha256(canonical_json({
            "format": native.LEDGER_FORMAT, "input_sha256": metadata["input_sha256"],
        })).hexdigest())
        if count:
            baseline.executemany("INSERT INTO coverage_counts VALUES (?,?,?)", (
                (field, unprocessed_decision("")[field], count) for field in DIMENSIONS
            ))
        baseline.commit()


def verify(manifest: Path) -> dict:
    """Check physical files, complete logical rows, identities, history and projections.

    This checks consistency with the manifest's pinned identities; without the
    original export it does not reauthenticate the upstream release publisher.
    """
    generation, document = _manifest(manifest)
    before = file_hash(Path(manifest))
    try:
        for name, descriptor in document["tables"].items():
            for partition in descriptor["partitions"]:
                verify_partition(generation, name, partition, document["layout"]["buckets"])
            digest, count = logical_hash(table_rows(generation, name, descriptor), name)
            if digest != descriptor["logical_sha256"] or count != descriptor["rows"]:
                raise CurationError(f"logical table hash or count mismatch: {name}")
        with tempfile.TemporaryDirectory(prefix="edgemech-verify-") as directory:
            # macOS's system temp prefix traverses /var -> /private/var. Resolve
            # only our newly allocated scratch directory, never caller inputs.
            scratch = Path(directory).resolve()
            source_path = scratch / "retained.sqlite"
            baseline = scratch / "baseline.sqlite"
            _reconstruct_sqlite(generation, document, source_path)
            with closing(native._connect(source_path, readonly=True)) as source:
                _baseline_from_verified_rows(source, baseline, document["source"])
                _replay(source, baseline)
                counters = {dimension: {} for dimension in DIMENSIONS}
                for dimension, value, count in _sql_rows(source, "coverage_counts"):
                    counters[dimension][value] = count
                if counters != document["counters"]:
                    raise CurationError("manifest counters differ from retained counters")
                if native._metadata(source)["source_verification"] != document["assurance"]["source_verification"]:
                    raise CurationError("manifest assurance differs from retained metadata")
                # Derived tables are indexes, never a second authority for a review.
                derived_root = scratch / "derived"
                derived_root.mkdir()
                for name in TABLE_SCHEMAS.keys() - set(AUTHORITATIVE):
                    expected = write_partitioned_table(
                        derived_root, name, _derived(source, name), buckets=1,
                    )
                    if any(expected[key] != document["tables"][name][key]
                           for key in ("logical_sha256", "rows")):
                        raise CurationError(f"derived index differs from retained bundles: {name}")
        # Catch inputs replaced during the multi-pass verification, not just while hashing.
        if file_hash(Path(manifest)) != before:
            raise CurationError("manifest changed during verification")
        for descriptor in document["tables"].values():
            for partition in descriptor["partitions"]:
                if file_hash(generation / partition["path"]) != partition["sha256"]:
                    raise CurationError("partition changed during verification")
    except (sqlite3.Error, OSError, KeyError, TypeError, ValueError) as exc:
        raise CurationError(f"artifact verification failed: {exc}") from exc
    return {"verified": True, "manifest_sha256": before,
            "verification_scope": "all_files_logical_rows_identities_history_current_projections",
            "scientific_review": False, "rows": document["source"]["selected_rows"],
            "table_rows": {name: value["rows"] for name, value in document["tables"].items()}}


def stats(manifest: Path) -> dict:
    """Constant-time manifest accounting; this does not scan or freshly verify partitions."""
    _, document = _manifest(manifest)
    return {"generation": document["generation"], "source": document["source"],
            "counters": document["counters"],
            "table_rows": {name: table["rows"] for name, table in document["tables"].items()},
            "verification_scope": "manifest_shape_and_declared_accounting_only",
            "scientific_review": False}


def lookup(manifest: Path, occurrence_id: str) -> dict:
    """Return exact occurrence and its complete bundle history, or fail above 2 MiB.

    Only touched partitions are reverified, so a fast lookup is not a full audit.
    Explicit bounds fail closed rather than silently truncating retained evidence.
    """
    generation, document = _manifest(manifest)
    buckets = document["layout"]["buckets"]
    budget = MAX_LOOKUP_BYTES
    manifest_digest = file_hash(Path(manifest))
    touched = {}

    def selected(name, key):
        nonlocal budget
        prefix = f"{name}/bucket-{bucket_for(key, buckets):04d}/"
        partitions = [part for part in document["tables"][name]["partitions"]
                      if part["path"].startswith(prefix)]
        for part in partitions:
            verify_partition(generation, name, part, buckets)
            touched[part["path"]] = part["sha256"]
        if not partitions:
            return []
        paths = [str(generation / part["path"]) for part in partitions]
        with query_connection() as connection:
            connection.from_parquet(paths, hive_partitioning=False).create_view("selected")
            field = TABLE_SCHEMAS[name].names[0]
            cursor = connection.execute(f'SELECT * FROM selected WHERE "{field}"=?', [key])
            result = []
            while row := cursor.fetchone():
                item = dict(zip(TABLE_SCHEMAS[name].names, row, strict=True))
                budget -= len(canonical_json(item))
                if budget < 0:
                    raise CurationError("lookup exceeds 2 MiB; use the partitioned artifact for full history")
                result.append(item)
        return result

    occurrence = selected("occurrences", occurrence_id)
    current = selected("current_decisions", occurrence_id)
    if len(occurrence) != 1 or len(current) != 1:
        raise CurationError("unknown or duplicate release occurrence")
    validate_occurrence({**occurrence[0],
                         "manifest_sha256": document["source"]["source_manifest_sha256"],
                         "member_sha256": document["source"]["edge_member_sha256"]})
    memberships = selected("memberships", occurrence_id)
    history = []
    sequences = set()
    for membership in memberships:
        digest = membership["bundle_sha256"]
        bundles = selected("bundles", digest)
        revisions = selected("history", digest)
        if len(bundles) != 1 or len(revisions) != 1:
            raise CurationError("incomplete retained occurrence history")
        raw = bundles[0]["document"].encode()
        bundle = native._decode(raw)
        if canonical_json(bundle) != raw or hashlib.sha256(raw).hexdigest() != digest:
            raise CurationError("lookup bundle bytes do not match their identity")
        validate_bundle(bundle, expected_input_sha256=document["source"]["input_manifest_sha256"])
        position = membership["position"]
        if not 0 <= position < len(bundle["occurrence_ids"]) or bundle["occurrence_ids"][position] != occurrence_id:
            raise CurationError("lookup membership differs from its bundle")
        revision = revisions[0]
        if (revision["sequence"] in sequences or revision["sequence"] < 0
                or any(revision[field] != bundles[0][field] for field in ("parent_revision", "revision"))
                or revision["revision"] != hashlib.sha256(canonical_json({
                    "parent_revision": revision["parent_revision"], "bundle_sha256": digest,
                })).hexdigest()):
            raise CurationError("lookup history index differs from its bundle")
        sequences.add(revision["sequence"])
        history.append({"bundle": bundles[0], "history": revisions[0], "membership": membership})
    history.sort(key=lambda item: item["history"]["sequence"])
    if history:
        latest = history[-1]["bundle"]
        decisions = native._decode(latest["document"].encode())["decisions"]
        expected = next(item for item in decisions if item["occurrence_id"] == occurrence_id)
        expected_bundle = latest["bundle_sha256"]
    else:
        expected, expected_bundle = unprocessed_decision(occurrence_id), None
    if (current[0]["bundle_sha256"] != expected_bundle
            or any(current[0][field] != expected[field] for field in DIMENSIONS)):
        raise CurationError("lookup current projection differs from retained history")
    result = {"occurrence": occurrence[0], "current_decision": current[0],
              "history": history,
              "verification_scope": "selected_partitions_only", "scientific_review": False}
    if len(canonical_json(result)) > MAX_LOOKUP_BYTES:
        raise CurationError("lookup exceeds 2 MiB; use the partitioned artifact for full history")
    if file_hash(Path(manifest)) != manifest_digest or any(
        file_hash(generation / path) != digest for path, digest in touched.items()
    ):
        raise CurationError("lookup artifact changed during reading")
    return result


__all__ = ["TABLE_KEYS", "TABLE_SCHEMAS", "lookup", "migrate_sqlite", "stats", "verify",
           "write_partitioned_table"]
