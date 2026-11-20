"""Failure preservation tests for source restoration, with tiny private fixtures."""

import hashlib
import importlib.machinery
import importlib.util
import json
import os
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get(
    "EDGE_RESTORE_HELPER_UNDER_TEST", ROOT / "scripts/adhoc/restore_restart_source_20261120.py"
))
SPEC = importlib.util.spec_from_loader(
    "restore_source", importlib.machinery.SourceFileLoader("restore_source", str(SOURCE))
)
helper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper)


@pytest.fixture
def snapshot(tmp_path):
    source = tmp_path / "recovered"
    source.mkdir()
    data = b"subject\tpredicate\tobject\nA\tP\tB\n"
    (source / "merged-kg_edges.tsv").write_bytes(data)
    manifest = {"members": {"merged-kg_edges.tsv": {
        "bytes": len(data), "rows": 1, "sha256": hashlib.sha256(data).hexdigest()
    }}}
    raw = json.dumps(manifest).encode()
    (source / "manifest.json").write_bytes(raw)
    return source, tmp_path / "original", manifest, hashlib.sha256(raw).hexdigest()


def test_exact_copy_preserves_manifest_bytes_and_publishes_it_last(snapshot, monkeypatch):
    source, destination, manifest, digest = snapshot
    original_open = Path.open
    writes = []

    def observe(path, mode="r", *args, **kwargs):
        if path.parent == destination and mode == "xb":
            writes.append(path.name)
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observe)
    result = helper.restore_absent(source, destination, manifest, digest)
    assert writes == ["merged-kg_edges.tsv", ".source-manifest.pending"]
    assert result["manifest_published_last"]
    for name in ["merged-kg_edges.tsv", "manifest.json"]:
        assert (destination / name).read_bytes() == (source / name).read_bytes()


def test_existing_destination_is_never_overwritten(snapshot):
    source, destination, manifest, digest = snapshot
    destination.mkdir()
    (destination / "valuable").write_text("preserve")
    with pytest.raises(FileExistsError):
        helper.restore_absent(source, destination, manifest, digest)
    assert sorted(p.name for p in destination.iterdir()) == ["valuable"]
    assert (destination / "valuable").read_text() == "preserve"


def test_changed_member_retains_failed_attempt_without_manifest_and_refuses_retry(snapshot):
    source, destination, manifest, digest = snapshot
    (source / "merged-kg_edges.tsv").write_bytes(b"changed")
    with pytest.raises(ValueError, match="input hash changed"):
        helper.restore_absent(source, destination, manifest, digest)
    assert (destination / "merged-kg_edges.tsv").read_bytes() == b"changed"
    assert not (destination / "manifest.json").exists()
    with pytest.raises(FileExistsError):
        helper.restore_absent(source, destination, manifest, digest)


def test_changed_manifest_fails_before_destination_mutation(snapshot):
    source, destination, manifest, digest = snapshot
    (source / "manifest.json").write_bytes(b"{}")
    with pytest.raises(ValueError, match="manifest bytes changed"):
        helper.restore_absent(source, destination, manifest, digest)
    assert not destination.exists()


def test_deadline_leaves_reserved_failed_attempt_without_completion_marker(snapshot):
    source, destination, manifest, digest = snapshot
    with pytest.raises(TimeoutError):
        helper.restore_absent(source, destination, manifest, digest, seconds=0)
    assert destination.is_dir()
    assert not (destination / "manifest.json").exists()


def test_destination_symlink_is_rejected(snapshot):
    source, destination, manifest, digest = snapshot
    destination.symlink_to(source, target_is_directory=True)
    with pytest.raises(ValueError, match="symlinks"):
        helper.restore_absent(source, destination, manifest, digest)
    assert (source / "manifest.json").is_file()


def test_partial_manifest_write_cannot_expose_completion_marker(snapshot, monkeypatch):
    source, destination, manifest, digest = snapshot
    original_open = Path.open

    @contextmanager
    def partial_writer(path, mode, *args, **kwargs):
        with original_open(path, mode, *args, **kwargs) as stream:
            def write(data):
                stream.write(data[:5])
                stream.flush()
                raise OSError("injected partial manifest write")
            yield SimpleNamespace(write=write)

    def inject(path, mode="r", *args, **kwargs):
        if path.parent == destination and path.name in {"manifest.json", ".source-manifest.pending"}:
            if mode == "xb":
                return partial_writer(path, mode, *args, **kwargs)
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", inject)
    with pytest.raises(OSError, match="partial manifest write"):
        helper.restore_absent(source, destination, manifest, digest)
    assert not (destination / "manifest.json").exists()
    assert (destination / ".source-manifest.pending").read_bytes()


def test_manifest_fsync_failure_cannot_expose_completion_marker(snapshot, monkeypatch):
    source, destination, manifest, digest = snapshot
    real_fsync = os.fsync

    def inject(fd):
        inode = os.fstat(fd).st_ino
        for name in ("manifest.json", ".source-manifest.pending"):
            path = destination / name
            if path.exists() and path.stat().st_ino == inode:
                raise OSError("injected manifest fsync failure")
        return real_fsync(fd)

    monkeypatch.setattr(os, "fsync", inject)
    with pytest.raises(OSError, match="manifest fsync failure"):
        helper.restore_absent(source, destination, manifest, digest)
    assert not (destination / "manifest.json").exists()
    assert (destination / ".source-manifest.pending").is_file()


def test_directory_flush_failure_before_publish_has_no_marker(snapshot, monkeypatch):
    source, destination, manifest, digest = snapshot

    def fail(path):
        raise OSError("injected directory flush failure")

    monkeypatch.setattr(helper, "_fsync_directory", fail)
    with pytest.raises(OSError, match="directory flush failure"):
        helper.restore_absent(source, destination, manifest, digest)
    assert not (destination / "manifest.json").exists()
    assert (destination / ".source-manifest.pending").is_file()


def test_atomic_publication_never_replaces_concurrent_marker(snapshot, monkeypatch):
    source, destination, manifest, digest = snapshot
    real_link = os.link

    def race(src, dst, **kwargs):
        Path(dst).write_bytes(b"concurrent marker")
        return real_link(src, dst, **kwargs)

    monkeypatch.setattr(os, "link", race)
    with pytest.raises(FileExistsError):
        helper.restore_absent(source, destination, manifest, digest)
    assert (destination / "manifest.json").read_bytes() == b"concurrent marker"
    assert (destination / ".source-manifest.pending").is_file()


@pytest.mark.parametrize("name", ["merged-kg_edges.tsv", "manifest.json"])
def test_nonregular_source_refuses_without_blocking(snapshot, name):
    source, destination, manifest, digest = snapshot
    path = source / name
    path.unlink()
    os.mkfifo(path)
    code = """
import importlib.machinery, importlib.util, json, sys
from pathlib import Path
spec = importlib.util.spec_from_loader('probe', importlib.machinery.SourceFileLoader('probe', sys.argv[1]))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
try:
    module.restore_absent(Path(sys.argv[2]), Path(sys.argv[3]), json.loads(sys.argv[4]), sys.argv[5])
except Exception as error:
    assert 'regular file' in str(error), str(error)
else:
    raise AssertionError('nonregular source accepted')
"""
    subprocess.run([sys.executable, "-c", code, str(SOURCE), str(source), str(destination),
                    json.dumps(manifest), digest], check=True, timeout=10, capture_output=True)
    assert not (destination / "manifest.json").exists()


def test_nonregular_persisted_readback_refuses(snapshot, monkeypatch):
    source, destination, manifest, digest = snapshot
    original_read = helper._read_handle

    def replace_before_read(path):
        if Path(path) == destination / "merged-kg_edges.tsv":
            Path(path).unlink()
            os.mkfifo(path)
        return original_read(path)

    monkeypatch.setattr(helper, "_read_handle", replace_before_read)
    with pytest.raises(ValueError, match="regular file"):
        helper.restore_absent(source, destination, manifest, digest)
    assert not (destination / "manifest.json").exists()


@pytest.mark.parametrize("failure", ["lock_refusal", "owner_changed", "copy_failure"])
def test_main_mutation_boundary_and_context_release(snapshot, monkeypatch, tmp_path, failure):
    source, _, manifest, digest = snapshot
    kg_root = tmp_path / "kg"
    (kg_root / "data/merged").mkdir(parents=True)
    census = {"source": {"manifest_sha256": digest,
                         "snapshot_path": str(kg_root / "data/merged/20000101")}}
    census_path = tmp_path / "census.json"
    census_path.write_text(json.dumps(census))
    census_hash = helper.file_hash(census_path)
    recovery = {"state": "PRIVATE_STAGING_TRANSFER_AND_BYTE_READBACK_COMPLETE",
                "census_manifest_sha256": census_hash, "source_archive": {
                    "extracted_directory": str(source), "manifest_sha256": digest,
                    "members": {n: {"bytes": x["bytes"], "sha256": x["sha256"]}
                                for n, x in manifest["members"].items()}}}
    recovery_path = tmp_path / "recovery.json"
    recovery_path.write_text(json.dumps(recovery))
    state = {"held": False, "released": False, "copies": 0, "status_calls": 0}

    def status(*args):
        state["status_calls"] += 1
        return "changed" if failure == "owner_changed" and state["status_calls"] > 1 else "same"

    repo = SimpleNamespace(git=SimpleNamespace(status=status, check_ignore=lambda path: path),
                           head=SimpleNamespace(commit=SimpleNamespace(hexsha="owner-head")))

    class Target:
        def __init__(self, *args):
            pass

        def open(self):
            return repo

    class Manager:
        @contextmanager
        def lock(self, *args, **kwargs):
            if failure == "lock_refusal":
                raise RuntimeError("injected lease refusal")
            state["held"] = True
            try:
                yield
            finally:
                state["held"] = False
                state["released"] = True

    def fail_copy(*args, **kwargs):
        assert state["held"]
        state["copies"] += 1
        raise OSError("injected copy failure")

    monkeypatch.setattr(helper, "restore_absent", fail_copy)
    monkeypatch.setattr(helper, "CENSUS_SHA", census_hash)
    monkeypatch.setattr(helper, "SOURCE_SHA", digest)
    monkeypatch.setattr(helper, "_snapshot", lambda *args: (
        (source / "manifest.json").read_bytes(), manifest, "merged-kg_edges.tsv"))
    monkeypatch.setattr(helper, "_verify_source", lambda *args: "verified-source-hash")
    monkeypatch.setattr(helper.shutil, "disk_usage", lambda path: SimpleNamespace(free=20 * 1024**3))
    monkeypatch.setitem(sys.modules, "kg_microbe_fleet.roots", SimpleNamespace(
        resolve_kg_microbe_root=lambda **kwargs: kg_root))
    monkeypatch.setitem(sys.modules, "plugins.lock_manager", SimpleNamespace(LockManager=Manager))
    monkeypatch.setitem(sys.modules, "plugins.repository_settings", SimpleNamespace(
        RepositoryTarget=Target, merged_repository_environment=lambda path: {},
        RepositorySettings=SimpleNamespace(from_environment=lambda **kwargs: SimpleNamespace(
            get_target=lambda key: SimpleNamespace(path=tmp_path / "edge")))))
    results = tmp_path / "results"
    monkeypatch.setattr(sys, "argv", ["restore", "--claw-root", str(tmp_path),
        "--recovery-receipt", str(recovery_path), "--census", str(census_path),
        "--results", str(results), "--apply"])
    with pytest.raises((RuntimeError, ValueError, OSError)):
        helper.main()
    assert state["copies"] == (1 if failure == "copy_failure" else 0)
    assert not state["held"]
    assert state["released"] == (failure != "lock_refusal")
    assert json.loads((results / "failure.json").read_text())["status"] == "failed"
