# Local immutable-artifact reader, version 1

`edgemech.reader` implements `edgemech-reader/v1` for the ledger artifacts in
CultureBotAI/culturebotai-claw#766 and EdgeMech#12. This is a Python interface
that a future browser or server can adapt. It does not deploy a service, fetch
external data, create per-edge pages or authorize publication. Shared scientific
identity and review semantics remain in the pinned CLAW contracts. Remote
publication and access-control policy remain separate work under CLAW#461/#540.

Every call requires a local immutable manifest path and its independently
obtained `expected_manifest_sha256`. The implementation checks the installed
canonical contract pins and the manifest digest before and after use. It does
not establish who published that digest. Use `storage.verify` for a complete
ledger replay and artifact reconciliation; a reader response is not that audit.

```python
from edgemech.reader import detail, downloads, search, stream_download

page = search(manifest, expected_manifest_sha256=trusted_digest, page_size=25)
next_page = search(manifest, expected_manifest_sha256=trusted_digest,
                   page_size=25, cursor=page["next_cursor"])
record = detail(manifest, page["items"][0]["occurrence_id"],
                expected_manifest_sha256=trusted_digest)
files = downloads(manifest, expected_manifest_sha256=trusted_digest)
```

Only request a following page when `next_cursor` is non-null. An empty result
has an empty `items` list and a null cursor. All JSON responses carry `contract`,
`kind`, `manifest_sha256`, `scientific_review_performed: false` and
`publication_authority: false`. These last two fields describe the reader's
authority; they do not erase scientific reviews actually retained in a ledger.

| Operation | Payload and verification scope |
| --- | --- |
| `detail(manifest, identifier, ...)` | `result` contains the existing storage lookup: exact source row, actual current decision and complete retained membership/history. Only touched partitions are verified. No approval is added. |
| `search(manifest, prefix="", page_size=25, cursor=None, ...)` | `items` contains exact `occurrence_id`, `member`, `row_number`, `row_sha256`. It verifies occurrence partitions and selected identity metadata. Distinct rows with identical biological content stay distinct. Review state is available through `detail`, never inferred from a search hit. |
| `downloads(manifest, page_size=25, cursor=None, ...)` | `items` contains the manifest itself and declared Parquet objects, sorted by path. Each descriptor includes `path`, `sha256`, `bytes`, `media_type`, `table`, `rows`. The manifest descriptor has null table/rows. `path_base` is `manifest_directory`; these are real generation-relative paths, not invented URLs. This catalogue verifies manifest declarations only. |
| `stream_download(manifest, object_path, max_bytes=..., chunk_bytes=..., ...)` | Yields bytes from exactly one declared object, checking size/hash and regular-file status before transfer and full streamed hash/size and unchanged files at completion. Traversal, symlinks, undeclared sidecars, other manifests and external URLs are refused. |

Search is deliberately limited to empty prefix or a canonical occurrence ID
prefix (`urn:kg-microbe:occurrence:v1:` followed by up to 64 lowercase hex
digits). A complete ID is an exact match. There is no subject/predicate text
interpretation, endpoint-based claim reuse or biological full-text query.

Search sorts by exact occurrence ID and uses keyset pagination. Download
catalogues sort by relative path. Cursors bind the contract version, operation,
manifest SHA256 and query including page size. Reusing a cursor with another
artifact, prefix, operation or page size fails. Cursors are opaque continuity
tokens, not signed credentials: a caller can deliberately construct a new
position and skip results. They never grant filesystem access.

| Bound | Version 1 behavior |
| --- | --- |
| JSON response | At most 2 MiB of canonical UTF-8 JSON. `max_response_bytes` can lower this. Overflow raises `CurationError`; evidence is not silently truncated. |
| Page size | 1–100 items, excluding the single internal look-ahead row. |
| Cursor | At most 2,048 encoded bytes, on input and output. |
| Search scan | Declared compressed occurrence-partition bytes must total at most 64 MiB; `max_scan_bytes` can lower this. Rejection occurs before partition reads. This is a scan-volume bound, not an elapsed-time or RSS guarantee. |
| Analytical query | The existing DuckDB helper limits database memory to 512 MB and uses a private spill directory. Partition checks stream batches; compression, Arrow and process overhead are additional. |
| Download | Explicit positive `max_bytes` bounds one complete transfer; positive `chunk_bytes` is at most 1 MiB. These bounds concern output bytes and chunk size, not the multiple verification reads. No byte-range or resumable transfer semantics are defined. |

The prefix-search fallback scans all occurrence partitions on every page. It
fails above its scan budget; it is not a production index for the complete
17.6-million-occurrence snapshot. A later indexed reader can use the versioned
payloads while defining its own verified index binding. Bulk artifacts remain
the available route for analytical queries that exceed the reader bounds.

Download consumers must exhaust the generator and discard incomplete output
when iteration raises. Bytes yielded before completion are provisional. A
transport layer should write to its own new temporary destination, verify the
declared digest after complete iteration and publish its receipt last. No
repository or arbitrary local file is automatically made downloadable: only
the pinned manifest and its declared table partitions are allowlisted.

`tests/test_reader.py` exercises real migrated duplicate rows and historical
decisions, stable pagination, digest/query mismatch, response/scan/transfer
bounds, actual persisted download bytes, missing/symlink/changed files and a
mutation during streaming. These tests establish local interface conformance;
they do not establish hosting throughput, authorization or release availability.
