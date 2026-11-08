"""Versioned, bounded local reader conformance using real migrated artifacts (#12)."""

import hashlib
import json

import pytest
from kg_microbe_curation.identity import CurationError, canonical_json
from test_storage import ledger_input as ledger_input

from edgemech import reader, storage
from edgemech.storage.parquet import file_hash


@pytest.fixture
def artifact(ledger_input, tmp_path):
    ledger, export, occurrences = ledger_input
    manifest = storage.migrate_sqlite(ledger, export, tmp_path / "store",
                                     buckets=2, row_group_size=2)
    return manifest, file_hash(manifest), occurrences


def test_search_preserves_multiplicity_and_deterministic_keyset_pages(artifact):
    manifest, digest, occurrences = artifact
    expected = sorted(item["occurrence_id"] for item in occurrences)
    whole = reader.search(manifest, expected_manifest_sha256=digest)
    assert [item["occurrence_id"] for item in whole["items"]] == expected
    assert len(expected) == 3  # Two biologically identical rows remain separate occurrences.
    assert whole["next_cursor"] is None
    assert whole["contract"] == reader.READER_CONTRACT
    assert whole["manifest_sha256"] == digest
    assert whole["scientific_review_performed"] is whole["publication_authority"] is False
    assert "review_state" not in whole["items"][0]
    assert len(canonical_json(whole)) <= reader.MAX_RESPONSE_BYTES
    cursor, actual = None, []
    for _ in range(3):
        page = reader.search(manifest, expected_manifest_sha256=digest, page_size=1, cursor=cursor)
        assert len(page["items"]) == 1
        actual.extend(item["occurrence_id"] for item in page["items"])
        cursor = page["next_cursor"]
    assert cursor is None
    assert actual == expected
    assert reader.search(manifest, expected_manifest_sha256=digest, prefix=expected[0])["items"] == [
        whole["items"][0]
    ]
    empty = reader.search(manifest, expected_manifest_sha256=digest,
                          prefix="urn:kg-microbe:occurrence:v1:" + "f" * 64)
    assert empty["items"] == [] and empty["next_cursor"] is None


def test_detail_preserves_exact_source_actual_state_and_complete_history(artifact):
    manifest, digest, occurrences = artifact
    detail = reader.detail(manifest, occurrences[0]["occurrence_id"], expected_manifest_sha256=digest)
    assert detail["kind"] == "detail"
    result = detail["result"]
    assert result["occurrence"]["source_row"] == occurrences[0]["source_row"]
    assert result["current_decision"]["review_state"] == "deferred"
    assert result["current_decision"]["disposition"] == "withheld"
    assert len(result["history"]) == 2
    assert result["verification_scope"] == "selected_partitions_only"
    assert detail["scientific_review_performed"] is False


def test_manifest_query_and_operation_bound_cursors(artifact):
    manifest, digest, _ = artifact
    cursor = reader.search(manifest, expected_manifest_sha256=digest, page_size=1)["next_cursor"]
    for options in ({"page_size": 2}, {"page_size": 1, "prefix": "urn:kg-microbe:occurrence:v1:a"}):
        with pytest.raises(CurationError, match="cursor"):
            reader.search(manifest, expected_manifest_sha256=digest, cursor=cursor, **options)
    with pytest.raises(CurationError, match="cursor"):
        reader.downloads(manifest, expected_manifest_sha256=digest, page_size=1, cursor=cursor)
    manifest.write_bytes(manifest.read_bytes() + b"\n")
    with pytest.raises(CurationError, match="cursor"):
        reader.search(manifest, expected_manifest_sha256=file_hash(manifest), page_size=1, cursor=cursor)


def test_invalid_and_oversized_requests_fail_closed(artifact):
    manifest, digest, occurrences = artifact
    bad = [{"page_size": 101}, {"page_size": True}, {"page_size": 0},
           {"max_response_bytes": reader.MAX_RESPONSE_BYTES + 1}, {"max_response_bytes": 1},
           {"max_scan_bytes": 0}, {"max_scan_bytes": reader.MAX_SCAN_BYTES + 1},
           {"prefix": "' OR true --"}, {"prefix": "urn:kg-microbe:occurrence:v1:" + "a" * 65},
           {"cursor": "?"}, {"cursor": "A" * (reader.MAX_CURSOR_BYTES + 1)}]
    for options in bad:
        with pytest.raises(CurationError):
            reader.search(manifest, expected_manifest_sha256=digest, **options)
    for bad_digest in ("", "g" * 64, "0" * 64):
        with pytest.raises(CurationError):
            reader.downloads(manifest, expected_manifest_sha256=bad_digest)
    with pytest.raises(CurationError, match="byte budget"):
        reader.detail(manifest, occurrences[0]["occurrence_id"], expected_manifest_sha256=digest,
                      max_response_bytes=100)
    with pytest.raises(CurationError, match="byte budget"):
        reader.downloads(manifest, expected_manifest_sha256=digest, max_response_bytes=100)
    with pytest.raises(CurationError, match="invalid exact"):
        reader.detail(manifest, "../wrong", expected_manifest_sha256=digest)


def test_search_budget_refuses_before_opening_partitions(artifact, monkeypatch):
    manifest, digest, _ = artifact

    def forbidden(*args, **kwargs):
        raise AssertionError("partition read occurred before budget rejection")

    monkeypatch.setattr(reader, "verify_partition", forbidden)
    with pytest.raises(CurationError, match="scan-byte budget"):
        reader.search(manifest, expected_manifest_sha256=digest, max_scan_bytes=1)


def test_page_refuses_to_emit_an_over_budget_cursor(artifact, monkeypatch):
    manifest, digest, _ = artifact
    monkeypatch.setattr(reader, "MAX_CURSOR_BYTES", 32)
    for operation in (reader.search, reader.downloads):
        with pytest.raises(CurationError, match="cursor exceeds byte budget"):
            operation(manifest, expected_manifest_sha256=digest, page_size=1)


def test_download_catalogue_and_stream_match_real_immutable_files(artifact):
    manifest, digest, _ = artifact
    objects, cursor = [], None
    while True:
        page = reader.downloads(manifest, expected_manifest_sha256=digest, page_size=2, cursor=cursor)
        objects.extend(page["items"])
        assert page["verification_scope"] == "manifest_declared_objects_only"
        assert page["path_base"] == "manifest_directory"
        assert page["publication_authority"] is False
        cursor = page["next_cursor"]
        if cursor is None:
            break
    document = json.loads(manifest.read_bytes())
    expected = {manifest.name, *(part["path"] for table in document["tables"].values()
                                for part in table["partitions"])}
    assert {item["path"] for item in objects} == expected
    assert len(objects) == len(expected)
    assert [item["path"] for item in objects] == sorted(expected)
    for item in objects:
        chunks = list(reader.stream_download(manifest, item["path"], expected_manifest_sha256=digest,
                                             max_bytes=item["bytes"], chunk_bytes=127))
        assert all(0 < len(chunk) <= 127 for chunk in chunks)
        raw = b"".join(chunks)
        assert raw == (manifest.parent / item["path"]).read_bytes()
        assert len(raw) == item["bytes"]
        assert hashlib.sha256(raw).hexdigest() == item["sha256"]
        assert "url" not in item


def test_download_refuses_unlisted_paths_and_excessive_transfers(artifact):
    manifest, digest, _ = artifact
    for path in ("../manifest.json", str(manifest), "migration-receipt.json", "CURRENT"):
        with pytest.raises(CurationError, match="not a declared"):
            list(reader.stream_download(manifest, path, expected_manifest_sha256=digest, max_bytes=100))
    for options in ({"max_bytes": 1}, {"max_bytes": True}, {"max_bytes": 0},
                    {"max_bytes": 100000, "chunk_bytes": reader.MAX_CHUNK_BYTES + 1}):
        with pytest.raises(CurationError):
            list(reader.stream_download(manifest, manifest.name, expected_manifest_sha256=digest, **options))


@pytest.mark.parametrize("damage", ["changed", "symlink", "missing"])
def test_search_and_download_reject_damaged_partition_bytes(artifact, tmp_path, damage):
    manifest, digest, _ = artifact
    part = json.loads(manifest.read_bytes())["tables"]["occurrences"]["partitions"][0]
    path = manifest.parent / part["path"]
    if damage == "changed":
        path.write_bytes(path.read_bytes() + b"x")
    elif damage == "symlink":
        other = tmp_path / "other.parquet"
        other.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(other)
    else:
        path.unlink()
    with pytest.raises(CurationError):
        reader.search(manifest, expected_manifest_sha256=digest)
    with pytest.raises(CurationError):
        list(reader.stream_download(manifest, part["path"], expected_manifest_sha256=digest,
                                    max_bytes=part["bytes"]))
    # The catalogue explicitly describes manifest declarations, not fresh file verification.
    assert reader.downloads(manifest, expected_manifest_sha256=digest)["items"]


def test_stream_detects_change_after_first_chunk(artifact):
    manifest, digest, _ = artifact
    part = json.loads(manifest.read_bytes())["tables"]["occurrences"]["partitions"][0]
    stream = reader.stream_download(manifest, part["path"], expected_manifest_sha256=digest,
                                    max_bytes=part["bytes"], chunk_bytes=8)
    assert len(next(stream)) == 8
    path = manifest.parent / part["path"]
    with path.open("r+b") as handle:
        handle.write(b"BROKEN!!")
    with pytest.raises(CurationError, match="changed during|pinned SHA256"):
        list(stream)
