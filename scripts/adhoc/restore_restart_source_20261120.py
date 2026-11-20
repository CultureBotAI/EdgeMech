#!/usr/bin/env python3
"""Restore a recovered, pinned source snapshot without overwriting existing data.

Purpose: enable the maintained full census verifier at its original bound path.
Inputs: private recovery receipt, census manifest, CLAW root and fresh result root.
Outputs: private plan/attempt receipts and, only with --apply, the absent original
source snapshot. No source-host access, credential transfer, Git commit or launch.
UTC date: 2026-11-20. Issues: CultureBotAI/EdgeMech#228 (helper provenance),
CultureBotAI/EdgeMech#231 (atomic publication and guarded-read review findings).
Provenance: consumes parent-owned recovery; original bootstrap and recovered bytes
remain unchanged. This is transport restoration, with scientific review coverage 0.
All operational paths/bindings are private inputs and receipts, never public logs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from edgemech.census import _fsync_directory, _metadata, _read_handle, _snapshot, _verify_source
from edgemech.storage.parquet import file_hash, safe_path

CENSUS_SHA = "a2b8353349816fd067ab3a7112fd1c2f5ee9c02971591ea52f31e9b981cbdd2e"
SOURCE_SHA = "f585e55a616d3771f382c91c78713cb8d74812c7ba177576090ccd5f9e6654b2"


def write_json(path: Path, value: dict) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def no_symlinks(path: Path) -> Path:
    path = path.absolute()
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("snapshot paths must not traverse symlinks")
    return path


def publish_manifest(destination: Path, manifest_bytes: bytes, expected: str) -> None:
    """Publish only flushed, hash-verified bytes; retain pending bytes on failure."""
    pending = destination / ".source-manifest.pending"
    marker = destination / "manifest.json"
    with pending.open("xb") as stream:
        stream.write(manifest_bytes)
        stream.flush()
        os.fsync(stream.fileno())
    with _read_handle(pending) as stream:
        readback = stream.read(len(manifest_bytes) + 1)
    if readback != manifest_bytes or hashlib.sha256(readback).hexdigest() != expected:
        raise ValueError("pending manifest readback differs")
    _fsync_directory(destination)
    _fsync_directory(destination.parent)
    os.link(pending, marker, follow_symlinks=False)  # Atomic, never replaces a marker.
    _fsync_directory(destination)
    with _read_handle(marker) as stream:
        if stream.read(len(manifest_bytes) + 1) != manifest_bytes:
            raise ValueError("published manifest readback differs")
    pending.unlink()  # Success only; failed reservations and pending bytes are retained.
    _fsync_directory(destination)


def restore_absent(source: Path, destination: Path, manifest: dict,
                   manifest_sha: str, *, seconds: float = 120) -> dict:
    """Called under the owner's short lease; leaves failed reservations intact."""
    no_symlinks(source)
    no_symlinks(destination)
    if destination.exists():
        raise FileExistsError("source destination exists; inspect without overwriting")
    if not destination.parent.is_dir():
        raise ValueError("snapshot parent must already exist")
    names = list(manifest["members"])
    if any(Path(name).name != name for name in names):
        raise ValueError("this bounded restore supports direct regular snapshot members only")
    if "manifest.json" in names:
        raise ValueError("manifest cannot also be a data member")
    expected = {name: value["sha256"] for name, value in manifest["members"].items()}
    manifest_bytes, _ = _metadata(source / "manifest.json")
    if hashlib.sha256(manifest_bytes).hexdigest() != manifest_sha:
        raise ValueError("original source manifest bytes changed")
    deadline = time.monotonic() + seconds
    destination.mkdir(mode=0o700)  # Exclusive reservation; never replace a failed attempt.
    copied = []
    for name in names:
        if time.monotonic() >= deadline:
            raise TimeoutError("bounded source restoration deadline exceeded")
        original = safe_path(source / name)
        digest = hashlib.sha256()
        count = 0
        with _read_handle(original) as incoming, (destination / name).open("xb") as outgoing:
            while block := incoming.read(4 * 1024 * 1024):
                if time.monotonic() >= deadline:
                    raise TimeoutError("bounded source restoration deadline exceeded")
                outgoing.write(block)
                digest.update(block)
                count += len(block)
            outgoing.flush()
            os.fsync(outgoing.fileno())
        if digest.hexdigest() != expected[name]:
            raise ValueError(f"copy input hash changed: {name}")
        if count != manifest["members"][name]["bytes"]:
            raise ValueError(f"copy input size changed: {name}")
        readback = hashlib.sha256()
        with _read_handle(destination / name) as stream:
            while block := stream.read(4 * 1024 * 1024):
                if time.monotonic() >= deadline:
                    raise TimeoutError("bounded source readback deadline exceeded")
                readback.update(block)
        if readback.hexdigest() != expected[name]:
            raise ValueError(f"persisted copy failed hash readback: {name}")
        copied.append({"member": name, "bytes": count, "sha256": expected[name]})
    if time.monotonic() >= deadline:
        raise TimeoutError("bounded source restoration deadline exceeded")
    publish_manifest(destination, manifest_bytes, manifest_sha)
    copied.append({"member": "manifest.json", "bytes": len(manifest_bytes),
                   "sha256": manifest_sha})
    return {"copied": copied, "manifest_published_last": True}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claw-root", type=Path, required=True)
    parser.add_argument("--recovery-receipt", type=Path, required=True)
    parser.add_argument("--census", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    result_root = no_symlinks(args.results)
    result_root.mkdir(mode=0o700)  # Fresh attempt, including plans.
    record = {
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "apply" if args.apply else "plan",
        "helper_sha256": file_hash(Path(__file__)),
        "scientific_review_coverage": 0, "status": "preparing",
    }
    try:
        claw = no_symlinks(args.claw_root)
        sys.path[:0] = [str(claw), str(claw / "src")]
        from kg_microbe_fleet.roots import resolve_kg_microbe_root
        from plugins.lock_manager import LockManager
        from plugins.repository_settings import (
            RepositorySettings,
            RepositoryTarget,
            merged_repository_environment,
        )

        env = merged_repository_environment(claw / ".env")
        settings = RepositorySettings.from_environment(environ=env)
        edge = settings.get_target("edgemech")
        kg_root = resolve_kg_microbe_root(claw_root=claw, environ=env)
        if kg_root is None:
            raise ValueError("source-owner repository is not configured")
        # KG-Microbe is the input corpus, not a Mech manifest row. Use its maintained
        # resolver and the same RepositoryTarget exact-origin validator.
        target = RepositoryTarget("kg-microbe", kg_root, "Knowledge-Graph-Hub/kg-microbe")
        repo = target.open()
        git_before = repo.git.status("--porcelain=v1", "--untracked-files=all")
        receipt_bytes, recovery = _metadata(args.recovery_receipt)
        census_bytes, census = _metadata(args.census)
        if hashlib.sha256(census_bytes).hexdigest() != CENSUS_SHA:
            raise ValueError("census differs from the accepted full-population reference")
        if recovery.get("state") != "PRIVATE_STAGING_TRANSFER_AND_BYTE_READBACK_COMPLETE":
            raise ValueError("parent recovery is not complete")
        if recovery.get("census_manifest_sha256") != CENSUS_SHA:
            raise ValueError("recovery receipt census binding differs")
        archive = recovery["source_archive"]
        recovered = no_symlinks(Path(archive["extracted_directory"]))
        raw_manifest, manifest, _ = _snapshot(recovered, SOURCE_SHA)
        if census["source"]["manifest_sha256"] != SOURCE_SHA:
            raise ValueError("census source pin differs")
        if archive["manifest_sha256"] != SOURCE_SHA:
            raise ValueError("recovery source pin differs")
        if archive["members"] != {
            name: {"bytes": item["bytes"], "sha256": item["sha256"]}
            for name, item in manifest["members"].items()
        }:
            raise ValueError("parent source member bindings differ")
        destination = no_symlinks(Path(census["source"]["snapshot_path"]))
        relative = destination.relative_to(kg_root)
        if len(relative.parts) != 3 or relative.parts[:2] != ("data", "merged"):
            raise ValueError("destination is not an original merged-snapshot directory")
        if not re.fullmatch(r"[0-9]{8}", relative.name):
            raise ValueError("snapshot directory must be the pinned YYYYMMDD")
        if destination.exists():
            raise FileExistsError("original snapshot destination exists; no overwrite")
        if repo.git.check_ignore(str(relative / "manifest.json")) == "":
            raise ValueError("restored snapshot must remain ignored research data")
        required_bytes = sum(item["bytes"] for item in manifest["members"].values())
        if shutil.disk_usage(destination.parent).free < required_bytes + 10 * 1024**3:
            raise ValueError("insufficient space for source copy plus 10 GiB reserve")
        # In-memory relocation for independent source validation only. Neither
        # retained manifest is rewritten; full census replay will use original path.
        selected_source_hash = _verify_source(
            {**census["source"], "snapshot_path": str(recovered)}, manifest
        )
        record.update({
            "status": "verified_plan", "canonical_edgemech": str(edge.path),
            "source_owner": str(kg_root), "source_owner_head": repo.head.commit.hexsha,
            "source": str(recovered), "destination": str(destination),
            "recovery_receipt_sha256": hashlib.sha256(receipt_bytes).hexdigest(),
            "census_sha256": CENSUS_SHA, "source_manifest_sha256": SOURCE_SHA,
            "source_prefix_sha256": selected_source_hash,
            "member_count": len(manifest["members"]), "member_bytes": required_bytes,
            "original_manifest_bytes": len(raw_manifest),
        })
        write_json(result_root / "plan.json", record)
        if args.apply:
            os.environ["OPENCLAW_ORCHESTRATION_ROOT"] = str(claw)
            with LockManager().lock("kg-microbe", "restore-pinned-edge-census-source", timeout=900):
                current = target.open()
                if current.git.status("--porcelain=v1", "--untracked-files=all") != git_before:
                    raise ValueError("source owner worktree changed before restoration")
                record["copy_readback"] = restore_absent(recovered, destination, manifest, SOURCE_SHA)
            if target.open().git.status("--porcelain=v1", "--untracked-files=all") != git_before:
                raise ValueError("source owner Git state changed during restoration")
            record["status"] = "restored_source_bytes_verified_full_census_replay_pending"
        record["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        write_json(result_root / "receipt.json", record)
        print(json.dumps({"status": record["status"], "scientific_review_coverage": 0}))
    except BaseException as exc:
        record.update(status="failed", error_type=type(exc).__name__, error=str(exc),
                      finished_at_utc=datetime.now(timezone.utc).isoformat())
        write_json(result_root / "failure.json", record)
        raise


if __name__ == "__main__":
    main()
