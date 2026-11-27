"""Synthetic descriptor lifetime and persisted readback boundaries for issue242."""

import importlib.util
import os
import stat
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "private_attempt_test", ROOT / "scripts/adhoc/restart_private_attempt_20261126.py")
helper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper)


@pytest.mark.parametrize("fail", [False, True])
def test_all_retained_directory_descriptors_release_after_body(tmp_path, fail):
    target = tmp_path / "attempt"
    descriptors = set()
    try:
        with helper.private_attempt(target, tmp_path) as output:
            for parent, _, child in output.links:
                descriptors.update((parent, child))
            with output.create("progress.jsonl", text=True) as stream:
                stream.write('{"partition":1}\n')
                stream.flush()
                if fail:
                    raise RuntimeError("injected body failure")
    except RuntimeError:
        assert fail
    assert descriptors
    for descriptor in descriptors:
        with pytest.raises(OSError):
            os.fstat(descriptor)
    assert (target / "progress.jsonl").read_bytes() == b'{"partition":1}\n'


@pytest.mark.parametrize("kind", ["symlink", "fifo", "different_inode"])
def test_readback_rejects_replaced_leaf_without_following_or_blocking(tmp_path, monkeypatch, kind):
    target, external = tmp_path / "attempt", tmp_path / "external"
    external.write_bytes(b"untouched external bytes")
    original_open = os.open
    replaced = False

    def open_file(path, flags, mode=0o777, *, dir_fd=None):
        nonlocal replaced
        if os.fspath(path) == "result.json" and not flags & os.O_CREAT and not replaced:
            replaced = True
            (target / "result.json").rename(target / "retained-original")
            if kind == "symlink":
                (target / "result.json").symlink_to(external)
            elif kind == "fifo":
                os.mkfifo(target / "result.json")
            else:
                (target / "result.json").write_bytes(b"original output")
        return original_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(os, "open", open_file)
    with pytest.raises((ValueError, OSError)):
        with helper.private_attempt(target, tmp_path) as output:
            output.save("result.json", b"original output")
    assert replaced
    assert external.read_bytes() == b"untouched external bytes"
    assert (target / "retained-original").read_bytes() == b"original output"


def test_file_flush_failure_retains_partial_attempt_and_releases_descriptors(tmp_path, monkeypatch):
    original_fsync = os.fsync
    descriptors = set()
    target = tmp_path / "attempt"

    def fsync(descriptor):
        if stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise OSError("injected output flush failure")
        return original_fsync(descriptor)

    monkeypatch.setattr(os, "fsync", fsync)
    with pytest.raises(OSError, match="injected output flush failure"):
        with helper.private_attempt(target, tmp_path) as output:
            for parent, _, child in output.links:
                descriptors.update((parent, child))
            output.save("result.json", b"retained partial attempt")
    assert (target / "result.json").read_bytes() == b"retained partial attempt"
    for descriptor in descriptors:
        with pytest.raises(OSError):
            os.fstat(descriptor)
    with pytest.raises(FileExistsError):
        with helper.private_attempt(target, tmp_path):
            pytest.fail("an existing partial attempt must not be entered again")
