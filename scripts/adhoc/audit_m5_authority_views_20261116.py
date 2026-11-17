#!/usr/bin/env python3
"""Inventory pinned reviewer authorities/navigation for EdgeMech #175 (2026-11-16).

Inputs: a retained round manifest and its read-only repository root. Outputs:
private inventory with exact source hashes, matching UTF-8 byte offsets and
navigation targets. Keyword matches are inspection leads, never a blinding pass.
No source bodies are embedded here. No original or manifest is modified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path

ROLES = {"authority", "evidence", "instructions", "navigation_receipt", "reviewer_view"}
LEADS = re.compile(
    r"benchmark|calibration|adjudicat|coordinator|historical (?:review|label|judg)|"
    r"SUPPORTED_AS_STATED|CONTRADICTED_AS_STATED|NOT_ASSESSABLE|"
    r"\b(?:verdict|gold standard|reviewed|evaluation)\b", re.IGNORECASE,
)
LINKS = re.compile(r"(?:https?://[^\s\"'<>]+|\.temp/[^\s\"'<>]+)")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def checked(root, relative):
    value = Path(relative)
    if value.is_absolute() or ".." in value.parts:
        raise ValueError("Input path must remain relative to its repository")
    path = root / value
    for parent in (path, *path.parents):
        if parent == root:
            break
        if parent.is_symlink():
            raise ValueError("Symlink input is not permitted")
    if not path.is_file():
        raise ValueError(f"Missing input: {relative}")
    return path


def matches(raw):
    result, offset = [], 0
    for line_number, line in enumerate(raw.splitlines(keepends=True), 1):
        value = line.decode("utf-8")
        if LEADS.search(value):
            result.append({"line": line_number, "byte_start": offset,
                           "byte_end": offset + len(line), "text": value.rstrip("\r\n")})
        offset += len(line)
    return result


def inventory(root, manifest_path):
    root = root.resolve()
    raw_manifest = checked(root, manifest_path).read_bytes()
    manifest = json.loads(raw_manifest)
    result = []
    seen = set()
    for pin in manifest["files"]:
        if pin["path"] in seen:
            raise ValueError("Repeated manifest file")
        seen.add(pin["path"])
        if pin["role"] not in ROLES:
            continue
        raw = checked(root, pin["path"]).read_bytes()
        if sha(raw) != pin["sha256"]:
            raise ValueError(f"Retained input changed: {pin['path']}")
        text = raw.decode("utf-8")
        result.append({"path": pin["path"], "role": pin["role"],
                       "sha256": sha(raw), "bytes": len(raw),
                       "lines": len(raw.splitlines()), "version": pin.get("version"),
                       "evidence_ids": pin.get("evidence_ids", []),
                       "inspection_leads": matches(raw),
                       "navigation_targets": sorted(set(LINKS.findall(text)))})
    return {"schema": "edgemech.authority-view-inventory/v1",
            "manifest_sha256": sha(raw_manifest), "source_root": str(root),
            "helper_sha256": sha(Path(__file__).read_bytes()), "files": result,
            "ignored_files_included": True,
            "scope": "Every declared authority, evidence, instruction, navigation and view file; "
                     "Git ignores do not affect direct manifest reads. No semantic blinding pass.",
            "scientific_ratings": 0}


def write_private(path, value):
    path = path.absolute()
    if path.exists() or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("Output must be a new nonsymlink path")
    missing, parent = [], path.parent
    while not parent.exists():
        missing.append(parent)
        parent = parent.parent
    for directory in reversed(missing):
        directory.mkdir(mode=0o700)
    raw = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    if path.read_bytes() != raw:
        raise ValueError("Persisted inventory differs")
    return {"path": str(path), "sha256": sha(raw), "files": len(value["files"])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--print-leads", action="store_true")
    args = parser.parse_args()
    result = inventory(args.source_root, args.manifest)
    print(json.dumps(write_private(args.output, result)))
    if args.print_leads:
        for item in result["files"]:
            print(json.dumps({"path": item["path"], "role": item["role"],
                              "bytes": item["bytes"], "leads": [
                                  {"line": lead["line"], "text": lead["text"][:240]}
                                  for lead in item["inspection_leads"]]}))


if __name__ == "__main__":
    main()
