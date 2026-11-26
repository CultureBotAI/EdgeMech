#!/usr/bin/env python3
"""Account for retained discovery references without reopening source locators.

Purpose: reconcile finite saved hash inventories with pinned evidence scopes.
Inputs: a pinned private JSON manifest, inventories and JSON/JSONL/hash scope artifacts.
Output: one exclusive, durable path-free metadata report; no live state updates.
Date: 2026-11-26. Issue #228. New parameterized source, not the producer of earlier
inline recovery queries/checkpoints. Original commands and receipts stay private.
Scope kinds are assertions supplied by the manifest, not independently verified
inspection or scientific qualification. No source restoration or census replay.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import time
from collections import Counter, defaultdict
from pathlib import Path

from edgemech.census import _json, _read_handle

DIGEST = re.compile(r"[0-9a-f]{64}\Z")
LABEL = re.compile(r"[a-z][a-z0-9_-]{0,63}\Z")
KINDS = {"read_observation", "structural_projection", "reference_only"}
MAX_FILE = 64 * 1024 * 1024
MAX_TOTAL = 256 * 1024 * 1024
MAX_ROWS = 500_000
MAX_OUTPUT = 64 * 1024 * 1024


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def token(value, pattern, name):
    require(isinstance(value, str) and pattern.fullmatch(value), f"invalid {name}")
    return value


class Budget:
    def __init__(self, seconds=60):
        require(type(seconds) in (int, float) and 0 < seconds <= 120, "invalid time bound")
        self.deadline = time.monotonic() + seconds
        self.bytes = self.rows = 0

    def check(self, *, byte_count=0, rows=0):
        self.bytes += byte_count
        self.rows += rows
        require(self.bytes <= MAX_TOTAL and self.rows <= MAX_ROWS, "aggregate bound exceeded")
        require(time.monotonic() <= self.deadline, "cooperative deadline exceeded")


def read_pinned(path, expected, budget, limit=MAX_FILE):
    token(expected, DIGEST, "input digest")
    require(isinstance(path, str) and "\0" not in path, "invalid input path")
    path = Path(path)
    require(path.is_absolute() and ".." not in path.parts, "require explicit absolute input")
    chunks, size = [], 0
    with _read_handle(path) as stream:
        while True:
            budget.check()
            chunk = stream.read(min(65536, limit + 1 - size))
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
            budget.check(byte_count=len(chunk))
            require(size <= limit, "input byte bound exceeded")
    raw = b"".join(chunks)
    require(sha(raw) == expected, "input hash mismatch")
    return raw


def unescape_locator(raw):
    result = bytearray()
    index = 0
    escapes = {ord("n"): 10, ord("r"): 13, ord("\\"): 92}
    while index < len(raw):
        byte = raw[index]
        if byte == 92:
            index += 1
            require(index < len(raw) and raw[index] in escapes, "invalid locator escape")
            byte = escapes[raw[index]]
        result.append(byte)
        index += 1
    return bytes(result)


def inventory_rows(raw, encoding, budget):
    require(isinstance(encoding, str) and encoding in {"sha256-lines", "sha256-nul"},
            "unknown inventory encoding")
    separator = b"\n" if encoding == "sha256-lines" else b"\0"
    require(raw and raw.endswith(separator), "inventory must have a final delimiter")
    for record in raw.split(separator)[:-1]:
        budget.check(rows=1)
        escaped = encoding == "sha256-lines" and record.startswith(b"\\")
        if escaped:
            record = record[1:]
        require(len(record) > 66 and record[64:66] in (b"  ", b" *"), "invalid hash record")
        digest = token(record[:64].decode("ascii"), DIGEST, "inventory digest")
        locator = unescape_locator(record[66:]) if escaped else record[66:]
        require(b"\0" not in locator, "NUL in locator")
        name = locator.decode("utf-8")
        require(Path(name).is_absolute(), "inventory locator must be absolute")
        yield digest, locator, name


def scope_rows(raw, encoding, field, budget):
    require(isinstance(encoding, str) and encoding in {
        "json-array", "jsonl", "json-object", "sha256-lines", "sha256-nul"},
            "unknown scope encoding")
    require(isinstance(field, str) and field in {"sha256", "bundle_sha256"},
            "unsupported scope hash field")
    if encoding in {"sha256-lines", "sha256-nul"}:
        require(field == "sha256", "hash stream requires sha256 field")
        for digest, _, _ in inventory_rows(raw, encoding, budget):
            yield digest
        return
    if encoding == "jsonl":
        require(raw and raw.endswith(b"\n"), "JSONL scope must have a final newline")
        entries = (_json(line) for line in raw.split(b"\n")[:-1])
    else:
        value = _json(raw)
        entries = [value] if encoding == "json-object" else value
        require(isinstance(entries, list), "scope must be an array")
    for entry in entries:
        budget.check(rows=1)
        require(isinstance(entry, dict) and field in entry, "scope row missing direct hash")
        yield token(entry[field], DIGEST, "scope digest")


def manifest_entries(manifest, name):
    entries = manifest.get(name)
    require(isinstance(entries, list) and len(entries) <= 128, "invalid manifest entry count")
    labels = set()
    required = {"label", "path", "sha256", "encoding"}
    if name == "scopes":
        required |= {"field", "asserted_kind"}
    for entry in entries:
        require(isinstance(entry, dict) and set(entry) == required, "invalid manifest entry fields")
        label = token(entry["label"], LABEL, "scope label")
        require(label not in labels, "duplicate label")
        labels.add(label)
        if name == "scopes":
            require(isinstance(entry["asserted_kind"], str) and entry["asserted_kind"] in KINDS,
                    "invalid asserted scope kind")
        yield entry


def account(manifest_path, expected, *, seconds=60):
    budget = Budget(seconds)
    raw = read_pinned(str(manifest_path), expected, budget, 1024 * 1024)
    manifest = _json(raw)
    require(isinstance(manifest, dict) and set(manifest) == {"version", "inventories", "scopes"},
            "invalid manifest fields")
    require(type(manifest["version"]) is int and manifest["version"] == 1, "invalid version")
    inventories = list(manifest_entries(manifest, "inventories"))
    scopes = list(manifest_entries(manifest, "scopes"))
    require(inventories, "at least one inventory is required")
    variants = {}
    locations = defaultdict(set)
    inputs = []
    for entry in inventories:
        data = read_pinned(entry["path"], entry["sha256"], budget)
        count = 0
        for digest, locator, name in inventory_rows(data, entry["encoding"], budget):
            count += 1
            item = variants.setdefault(digest, {"counts": Counter(), "suffixes": set(), "scopes": set()})
            item["counts"][entry["label"]] += 1
            suffix = Path(name).suffix.casefold()
            item["suffixes"].add(suffix if re.fullmatch(r"\.[a-z0-9]{1,12}", suffix) else "[other]")
            locations[sha(locator)].add(digest)
        inputs.append({"label": entry["label"], "sha256": entry["sha256"], "rows": count,
                       "role": "inventory", "encoding": entry["encoding"]})
    scope_only = defaultdict(set)
    for entry in scopes:
        data = read_pinned(entry["path"], entry["sha256"], budget)
        count = 0
        for digest in scope_rows(data, entry["encoding"], entry["field"], budget):
            count += 1
            if digest in variants:
                variants[digest]["scopes"].add(entry["label"])
            else:
                scope_only[digest].add(entry["label"])
        inputs.append({"label": entry["label"], "sha256": entry["sha256"], "rows": count,
                       "role": "scope", "encoding": entry["encoding"], "field": entry["field"],
                       "asserted_kind": entry["asserted_kind"]})
    rows = [{"sha256": digest, "inventory_counts": dict(sorted(item["counts"].items())),
             "suffix_groups": sorted(item["suffixes"]), "scope_references": sorted(item["scopes"])}
            for digest, item in sorted(variants.items())]
    budget.check()
    result = {
        "kind": "retained-discovery-reference-accounting/v1", "manifest_sha256": expected,
        "inputs": inputs, "inventory_records": sum(sum(row["inventory_counts"].values()) for row in rows),
        "distinct_inventoried_hashes": len(rows),
        "hashes_with_scope_reference": sum(bool(row["scope_references"]) for row in rows),
        "hashes_without_scope_reference": sum(not row["scope_references"] for row in rows),
        "variants": rows,
        "scope_hashes_absent_from_inventories": [
            {"sha256": digest, "scope_references": sorted(labels)}
            for digest, labels in sorted(scope_only.items())],
        "conflicting_locator_bindings": [
            {"locator_sha256": locator, "content_sha256s": sorted(hashes)}
            for locator, hashes in sorted(locations.items()) if len(hashes) > 1],
        "limitations": ["Scope labels/kinds are supplied assertions; only artifact pins and references are checked.",
                        "Inventory locators are never opened; omitted evidence and full discovery remain unresolved.",
                        "No occurrence membership, scientific qualification or historical execution is inferred.",
                        "Deadline is cooperative; use a separate outer timeout when required."],
        "scientific_review_coverage": 0, "queue_A_count": None, "queue_B_count": None,
        "full_target_frozen": False, "baseline_cutoff_frozen": False,
    }
    return result


def output_directory(path):
    """Open every directory component without following a replacement symlink."""
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    descriptor = os.open(path.anchor, flags)
    try:
        for component in path.parts[1:]:
            successor = os.open(component, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = successor
        return descriptor
    except OSError as error:
        os.close(descriptor)
        raise ValueError("invalid output parent") from error


def publish(path, result):
    raw = (json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    require(len(raw) <= MAX_OUTPUT, "output bound exceeded")
    require(path.is_absolute() and ".." not in path.parts, "require absolute output without traversal")
    directory = output_directory(path.parent)
    try:
        descriptor = os.open(path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                             0o600, dir_fd=directory)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.fsync(directory)
        descriptor = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        with os.fdopen(descriptor, "rb") as stream:
            require(stat.S_ISREG(os.fstat(stream.fileno()).st_mode), "nonregular output readback")
            require(stream.read(MAX_OUTPUT + 1) == raw, "output readback mismatch")
        return sha(raw)
    finally:
        os.close(directory)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--helper-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-seconds", type=float, default=60)
    args = parser.parse_args()
    read_pinned(str(Path(__file__).absolute()), args.helper_sha256, Budget(), 1024 * 1024)
    result = account(args.manifest, args.manifest_sha256, seconds=args.max_seconds)
    result["producer_sha256"] = args.helper_sha256
    print(json.dumps({"output_sha256": publish(args.output, result),
                      "scientific_review_coverage": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
