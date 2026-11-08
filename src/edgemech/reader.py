"""Bounded local reader responses for immutable ledger artifacts (EdgeMech #12).

No host, publication permission, scientific review or biological projection is
created here. A caller must obtain the expected manifest digest independently.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import stat
from pathlib import Path

from kg_microbe_curation.identity import CurationError, canonical_json, occurrence_id

from edgemech import storage
from edgemech.pins import check_contracts
from edgemech.storage.parquet import file_hash, query_connection, safe_path, verify_partition

READER_CONTRACT = "edgemech-reader/v1"
MAX_PAGE_SIZE = 100
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
MAX_SCAN_BYTES = 64 * 1024 * 1024
MAX_CURSOR_BYTES = 2048
MAX_CHUNK_BYTES = 1024 * 1024
_ID_PREFIX = "urn:kg-microbe:occurrence:v1:"


def _integer(value, maximum, label):
    if type(value) is not int or not 1 <= value <= maximum:
        raise CurationError(f"{label} must be an integer between 1 and {maximum}")
    return value


def _pinned(manifest: Path, digest: str):
    check_contracts()
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise CurationError("expected manifest SHA256 is required")
    manifest = safe_path(manifest)
    _unchanged(manifest, digest)
    generation, document = storage._manifest(manifest)
    _unchanged(manifest, digest)
    return manifest, generation, document


def _unchanged(path, digest):
    if file_hash(path) != digest:
        raise CurationError("artifact differs from its pinned SHA256")


def _after(cursor, kind, digest, query):
    if cursor is None:
        return ""
    if not isinstance(cursor, str) or len(cursor) > MAX_CURSOR_BYTES:
        raise CurationError("invalid or oversized cursor")
    try:
        raw = base64.b64decode(cursor, altchars=b"-_", validate=True)
        value = json.loads(raw)
        if canonical_json(value) != raw:
            raise ValueError("noncanonical")
    except (ValueError, UnicodeError, TypeError, RecursionError) as error:
        raise CurationError("invalid cursor") from error
    if (not isinstance(value, dict)
            or set(value) != {"contract", "kind", "manifest_sha256", "query", "after"}
            or value["contract"] != READER_CONTRACT or value["kind"] != kind
            or value["manifest_sha256"] != digest or value["query"] != query
            or not isinstance(value["after"], str) or not value["after"]):
        raise CurationError("cursor does not bind this manifest and query")
    return value["after"]


def _cursor(kind, digest, query, after):
    encoded = base64.urlsafe_b64encode(canonical_json({
        "contract": READER_CONTRACT, "kind": kind, "manifest_sha256": digest,
        "query": query, "after": after,
    })).decode("ascii")
    if len(encoded) > MAX_CURSOR_BYTES:
        raise CurationError("cursor exceeds byte budget; use bulk artifacts")
    return encoded


def _response(kind, digest, payload, maximum):
    _integer(maximum, MAX_RESPONSE_BYTES, "max_response_bytes")
    result = {"contract": READER_CONTRACT, "kind": kind, "manifest_sha256": digest,
              "scientific_review_performed": False, "publication_authority": False, **payload}
    if len(canonical_json(result)) > maximum:
        raise CurationError("reader response exceeds byte budget; reduce the page or use bulk artifacts")
    return result


def detail(manifest: Path, identifier: str, *, expected_manifest_sha256: str,
           max_response_bytes: int = MAX_RESPONSE_BYTES) -> dict:
    """Return exact source and actual current/history state; no scientific approval added."""
    _integer(max_response_bytes, MAX_RESPONSE_BYTES, "max_response_bytes")
    if not isinstance(identifier, str) or not re.fullmatch(_ID_PREFIX + r"[0-9a-f]{64}", identifier):
        raise CurationError("invalid exact occurrence ID")
    manifest, _, _ = _pinned(manifest, expected_manifest_sha256)
    payload = storage.lookup(manifest, identifier)
    _unchanged(manifest, expected_manifest_sha256)
    return _response("detail", expected_manifest_sha256, {"result": payload}, max_response_bytes)


def search(manifest: Path, *, expected_manifest_sha256: str, prefix: str = "",
           page_size: int = 25, cursor: str | None = None,
           max_response_bytes: int = MAX_RESPONSE_BYTES,
           max_scan_bytes: int = MAX_SCAN_BYTES) -> dict:
    """Page exact occurrence identity metadata in ID order, never deduplicating edges.

    This bounded fallback scans the occurrence table; no production search index
    is implied. Above the byte budget use the downloadable analytical artifacts.
    Summaries do not include review state; request detail for retained decisions.
    """
    _integer(page_size, MAX_PAGE_SIZE, "page_size")
    _integer(max_response_bytes, MAX_RESPONSE_BYTES, "max_response_bytes")
    _integer(max_scan_bytes, MAX_SCAN_BYTES, "max_scan_bytes")
    if not isinstance(prefix, str) or not re.fullmatch(r"(?:" + _ID_PREFIX + r"[0-9a-f]{0,64})?", prefix):
        raise CurationError("prefix must be empty or a canonical occurrence-ID prefix")
    digest = expected_manifest_sha256
    manifest, generation, document = _pinned(manifest, digest)
    query = {"prefix": prefix, "page_size": page_size}
    after = _after(cursor, "search", digest, query)
    if after and (not re.fullmatch(_ID_PREFIX + r"[0-9a-f]{64}", after) or not after.startswith(prefix)):
        raise CurationError("invalid search cursor position")
    partitions = document["tables"]["occurrences"]["partitions"]
    scan_bytes = sum(part["bytes"] for part in partitions)
    if scan_bytes > max_scan_bytes:
        raise CurationError("search exceeds scan-byte budget; use an index or bulk artifacts")
    for part in partitions:
        verify_partition(generation, "occurrences", part, document["layout"]["buckets"])
    rows = []
    if partitions:
        with query_connection() as connection:
            connection.from_parquet([str(generation / part["path"]) for part in partitions],
                                    hive_partitioning=False).create_view("occurrences")
            # Bound strings before materializing result rows, even in a malformed
            # but internally hash-consistent artifact supplied by the caller.
            invalid = connection.execute(
                "SELECT COUNT(*) FROM occurrences WHERE length(occurrence_id) != ? "
                "OR length(row_sha256) != 64 OR member != ?",
                [len(_ID_PREFIX) + 64, document["source"]["edge_member"]],
            ).fetchall()[0][0]
            if invalid:
                raise CurationError("invalid occurrence identity metadata width or member")
            rows = connection.execute(
                "SELECT occurrence_id,member,row_number,row_sha256 FROM occurrences "
                "WHERE starts_with(occurrence_id, ?) AND occurrence_id > ? "
                "ORDER BY occurrence_id LIMIT ?", [prefix, after, page_size + 1],
            ).fetchall()
    items, previous = [], after
    for identifier, member, number, row_digest in rows:
        expected = occurrence_id(
            manifest_sha256=document["source"]["source_manifest_sha256"], member=member,
            member_sha256=document["source"]["edge_member_sha256"], row_number=number,
            row_sha256=row_digest,
        )
        if (identifier != expected or identifier <= previous
                or member != document["source"]["edge_member"]):
            raise CurationError("invalid or duplicate occurrence identity in search results")
        previous = identifier
        items.append({"occurrence_id": identifier, "member": member,
                      "row_number": number, "row_sha256": row_digest})
    following = (_cursor("search", digest, query, items[page_size - 1]["occurrence_id"])
                 if len(items) > page_size else None)
    _unchanged(manifest, digest)
    for part in partitions:
        _unchanged(generation / part["path"], part["sha256"])
    return _response("search", digest, {
        "query": query, "items": items[:page_size], "next_cursor": following,
        "scan_bytes": scan_bytes, "verification_scope": "occurrence_partitions_and_selected_identity_metadata",
    }, max_response_bytes)


def _objects(manifest, document, digest):
    objects = [{"path": manifest.name, "sha256": digest, "bytes": manifest.stat().st_size,
                "media_type": "application/json", "table": None, "rows": None}]
    for name, table in document["tables"].items():
        for part in table["partitions"]:
            objects.append({**part, "table": name, "media_type": "application/vnd.apache.parquet"})
    return sorted(objects, key=lambda item: item["path"])


def downloads(manifest: Path, *, expected_manifest_sha256: str, page_size: int = 25,
              cursor: str | None = None, max_response_bytes: int = MAX_RESPONSE_BYTES) -> dict:
    """Page declared immutable object descriptors, relative to this manifest's directory.

    Descriptors are not URLs or permission to publish. File bytes are checked by
    stream_download; this catalogue checks only the manifest and its contract.
    """
    _integer(page_size, MAX_PAGE_SIZE, "page_size")
    _integer(max_response_bytes, MAX_RESPONSE_BYTES, "max_response_bytes")
    digest = expected_manifest_sha256
    manifest, _, document = _pinned(manifest, digest)
    query = {"page_size": page_size}
    after = _after(cursor, "downloads", digest, query)
    objects = _objects(manifest, document, digest)
    if after and after not in {item["path"] for item in objects}:
        raise CurationError("download cursor does not identify a declared object")
    selected = [item for item in objects if item["path"] > after][:page_size + 1]
    following = (_cursor("downloads", digest, query, selected[page_size - 1]["path"])
                 if len(selected) > page_size else None)
    _unchanged(manifest, digest)
    return _response("downloads", digest, {
        "items": selected[:page_size], "next_cursor": following,
        "path_base": "manifest_directory", "verification_scope": "manifest_declared_objects_only",
    }, max_response_bytes)


def stream_download(manifest: Path, object_path: str, *, expected_manifest_sha256: str,
                    max_bytes: int, chunk_bytes: int = MAX_CHUNK_BYTES):
    """Yield one complete declared object; success requires consuming the iterator.

    max_bytes is a caller-selected total transfer budget, not a memory allocation.
    Each chunk is at most 1 MiB. Bytes are hashed before transfer and again while
    streaming; consumers must discard incomplete output if iteration fails.
    No external fetch, response caching, range semantics or publication occurs.
    """
    _integer(max_bytes, 2**63 - 1, "max_bytes")
    _integer(chunk_bytes, MAX_CHUNK_BYTES, "chunk_bytes")
    digest = expected_manifest_sha256
    manifest, generation, document = _pinned(manifest, digest)
    selected = next((item for item in _objects(manifest, document, digest)
                     if item["path"] == object_path), None)
    if selected is None:
        raise CurationError("download path is not a declared immutable object")
    if selected["bytes"] > max_bytes:
        raise CurationError("download exceeds total-byte budget")
    path = safe_path(generation / selected["path"])
    if path.stat().st_size != selected["bytes"]:
        raise CurationError("download size differs from manifest")
    _unchanged(path, selected["sha256"])
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_size != selected["bytes"]:
            raise CurationError("download is not the declared regular file")
        count, checksum = 0, hashlib.sha256()
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            while chunk := handle.read(min(chunk_bytes, selected["bytes"] - count + 1)):
                count += len(chunk)
                if count > selected["bytes"]:
                    raise CurationError("download grew beyond its declared size")
                checksum.update(chunk)
                yield chunk
        after = os.fstat(descriptor)
        if ((before.st_size, before.st_mtime_ns, before.st_ino)
                != (after.st_size, after.st_mtime_ns, after.st_ino)
                or count != selected["bytes"] or checksum.hexdigest() != selected["sha256"]):
            raise CurationError("download changed during transfer")
        _unchanged(path, selected["sha256"])
        _unchanged(manifest, digest)
    finally:
        os.close(descriptor)
