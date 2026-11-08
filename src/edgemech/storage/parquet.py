"""Bounded streaming Parquet I/O and complete-field logical hashes."""

from __future__ import annotations

import hashlib
import os
import stat
import tempfile
from contextlib import contextmanager
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
from kg_microbe_curation.artifact import validate_relative_path
from kg_microbe_curation.identity import CurationError, canonical_json

from .schema import TABLE_KEYS, TABLE_SCHEMAS

MAX_ROW_BYTES = 32 * 1024 * 1024


def safe_path(path: Path, *, exists: bool = True) -> Path:
    """Reject symlinks in every path component, including output ancestors."""
    path = Path(path)
    if ".." in path.parts:
        raise CurationError("path traversal is not allowed")
    path = path.absolute()
    for component in (*reversed(path.parents), path):
        if component.is_symlink():
            raise CurationError(f"symlink is not allowed: {component}")
    if exists and not path.exists():
        raise CurationError(f"missing artifact: {path}")
    return path


def file_hash(path: Path) -> str:
    safe_path(path)
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise CurationError("artifact must be a regular file")
        digest = hashlib.sha256()
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            while chunk := handle.read(1024 * 1024):
                digest.update(chunk)
        after = os.fstat(descriptor)
        if (before.st_size, before.st_mtime_ns, before.st_ino) != (
            after.st_size, after.st_mtime_ns, after.st_ino
        ):
            raise CurationError("artifact changed while hashing")
        return digest.hexdigest()
    finally:
        os.close(descriptor)


def fsync_directory(path: Path) -> None:
    descriptor = os.open(
        path,
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
    )
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def bucket_for(key: str, buckets: int) -> int:
    return int.from_bytes(hashlib.sha256(key.encode("utf-8")).digest(), "big") % buckets


@contextmanager
def query_connection():
    """Bound DuckDB RAM and place transient spill data in a private directory."""
    with tempfile.TemporaryDirectory(prefix="edgemech-query-") as directory:
        connection = duckdb.connect(config={
            "memory_limit": "512MB", "threads": "2", "temp_directory": directory,
            "enable_external_access": "true",
        })
        try:
            yield connection
        finally:
            connection.close()


def table_rows(generation: Path, name: str, descriptor: dict, *, ordered: bool = True):
    paths = []
    for item in descriptor["partitions"]:
        validate_relative_path(item["path"])
        paths.append(str(safe_path(generation / item["path"])))
    if not paths:
        return
    with query_connection() as connection:
        relation = connection.from_parquet(paths, hive_partitioning=False)
        if ordered:
            relation = relation.order(",".join('"' + field + '"' for field in TABLE_KEYS[name]))
        reader = relation.to_arrow_reader(batch_size=16)
        for batch in reader:
            columns = [column.to_pylist() for column in batch.columns]
            yield from zip(*columns, strict=True)


def logical_hash(rows, name: str) -> tuple[str, int]:
    """Hash canonical full rows in primary-key order; reject duplicate primary keys."""
    digest, count, previous = hashlib.sha256(), 0, None
    indexes = [TABLE_SCHEMAS[name].names.index(key) for key in TABLE_KEYS[name]]
    for row in rows:
        key = tuple(row[index] for index in indexes)
        if previous is not None and key <= previous:
            raise CurationError(f"duplicate or unordered primary key in {name}")
        previous = key
        digest.update(canonical_json(list(row)) + b"\n")
        count += 1
    return digest.hexdigest(), count


def write_partitioned_table(
    generation: Path, name: str, rows, *, buckets: int = 16, row_group_size: int = 8192
) -> dict:
    """Write one known table to a new table directory; never overwrite a partition.

    Input may be any streaming tuple iterator. Complete-field logical hashes use
    a bounded DuckDB external sort, independent of input or partition ordering.
    """
    if name not in TABLE_SCHEMAS:
        raise CurationError(f"unknown table schema: {name}")
    if type(buckets) is not int or not 1 <= buckets <= 4096:
        raise CurationError("buckets must be an integer between 1 and 4096")
    if type(row_group_size) is not int or not 1 <= row_group_size <= 10_000_000:
        raise CurationError("invalid row group size")
    generation = safe_path(generation)
    directory = generation / name
    directory.mkdir(exist_ok=False)
    schema = TABLE_SCHEMAS[name]
    buffers, sizes, parts = {}, {}, []
    total_bytes = 0
    sequences = {}

    def flush(bucket):
        nonlocal total_bytes
        batch = buffers.pop(bucket)
        total_bytes -= sizes.pop(bucket)
        partition = directory / f"bucket-{bucket:04d}"
        partition.mkdir(exist_ok=True)
        sequence = sequences.get(bucket, 0)
        sequences[bucket] = sequence + 1
        path = partition / f"part-{sequence:06d}.parquet"
        columns = [pa.array([row[i] for row in batch], type=field.type)
                   for i, field in enumerate(schema)]
        table = pa.Table.from_arrays(columns, schema=schema)
        with path.open("xb") as handle:
            pq.write_table(table, handle, compression="zstd", row_group_size=row_group_size)
            handle.flush()
            os.fsync(handle.fileno())
        fsync_directory(partition)
        parts.append({"path": path.relative_to(generation).as_posix(),
                      "sha256": file_hash(path), "bytes": path.stat().st_size, "rows": len(batch)})

    for row in rows:
        row = tuple(row)
        if len(row) != len(schema):
            raise CurationError(f"wrong column count in {name}")
        for value, field in zip(row, schema, strict=True):
            expected = int if pa.types.is_integer(field.type) else str
            if value is None and field.nullable:
                continue
            if type(value) is not expected:
                raise CurationError(f"wrong or null value in {name}.{field.name}")
        size = len(canonical_json(list(row)))
        if size > MAX_ROW_BYTES:
            raise CurationError("row exceeds the 32 MiB storage bound")
        bucket = bucket_for(row[0], buckets)
        buffers.setdefault(bucket, []).append(row)
        sizes[bucket] = sizes.get(bucket, 0) + size
        total_bytes += size
        if len(buffers[bucket]) >= row_group_size or sizes[bucket] >= 1024 * 1024:
            flush(bucket)
        while total_bytes >= 8 * 1024 * 1024:
            flush(max(sizes, key=sizes.get))
    for bucket in list(buffers):
        flush(bucket)
    fsync_directory(directory)
    fsync_directory(generation)
    descriptor = {"schema": f"edgemech-table/{name}/v1", "partitions": sorted(
        parts, key=lambda item: item["path"])}
    digest, count = logical_hash(table_rows(generation, name, descriptor), name)
    descriptor.update(logical_sha256=digest, rows=count)
    return descriptor


def verify_partition(generation: Path, name: str, partition: dict, buckets: int) -> None:
    validate_relative_path(partition["path"])
    path = safe_path(generation / partition["path"])
    if path.stat().st_size != partition["bytes"] or file_hash(path) != partition["sha256"]:
        raise CurationError(f"partition hash or size mismatch: {partition['path']}")
    if not pq.read_schema(path).equals(TABLE_SCHEMAS[name], check_metadata=True):
        raise CurationError(f"physical schema mismatch: {partition['path']}")
    count = 0
    for batch in pq.ParquetFile(path).iter_batches(batch_size=16):
        if any(column.null_count for field, column in zip(batch.schema, batch.columns, strict=True)
               if not field.nullable):
            raise CurationError("null in a required physical column")
        keys = batch.column(0).to_pylist()
        for key in keys:
            expected = f"{name}/bucket-{bucket_for(key, buckets):04d}/"
            if not partition["path"].startswith(expected):
                raise CurationError("partition does not match its first-key bucket")
        count += batch.num_rows
    if count != partition["rows"]:
        raise CurationError("partition row count mismatch")
