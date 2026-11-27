"""Confine readiness attempt output to retained no-follow directory descriptors.

Purpose: B2-PATH-02 repair shared by the membership and timing helpers.
Inputs: explicit attempt path below a private root; bounded caller-owned bytes.
Outputs: exclusive attempt/files with file and directory flush and pinned readback.
Date: 2026-11-26 UTC. Issues #228/#242. New successor source, not a historical
producer. Directory identity changes fail closed; partial attempts remain intact.
No source/census/provider/canonical operation or scientific qualification occurs.
"""

from __future__ import annotations

import hashlib
import os
import stat
from contextlib import ExitStack, contextmanager
from pathlib import Path

DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW


def identity(value):
    return value.st_dev, value.st_ino


class _Writer:
    def __init__(self, stream, text):
        self.stream, self.text = stream, text
        self.sha256, self.size = hashlib.sha256(), 0

    def write(self, value):
        raw = value.encode("utf-8") if self.text else value
        written = self.stream.write(raw)
        if written != len(raw):
            raise OSError("short private output write")
        self.sha256.update(raw)
        self.size += written
        return len(value)

    def flush(self):
        return self.stream.flush()

    def fileno(self):
        return self.stream.fileno()


class Attempt:
    def __init__(self, descriptor, links):
        self.descriptor, self.links = descriptor, links

    def check(self):
        for parent, name, child in self.links:
            current = os.stat(name, dir_fd=parent, follow_symlinks=False)
            retained = os.fstat(child)
            if not stat.S_ISDIR(current.st_mode) or identity(current) != identity(retained):
                raise ValueError("private output directory identity changed")

    def _readback(self, name, expected_identity, size, digest):
        self.check()
        descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                             dir_fd=self.descriptor)
        with os.fdopen(descriptor, "rb") as stream:
            current = os.fstat(stream.fileno())
            if not stat.S_ISREG(current.st_mode) or identity(current) != expected_identity:
                raise ValueError("private output readback identity changed")
            observed, count = hashlib.sha256(), 0
            while block := stream.read(min(1024 * 1024, size + 1 - count)):
                observed.update(block)
                count += len(block)
                if count > size:
                    raise ValueError("private output readback grew")
            if count != size or observed.hexdigest() != digest:
                raise ValueError("private output readback differs")
        self.check()

    @contextmanager
    def create(self, name, *, text=False):
        if not isinstance(name, str) or not name or name in {".", ".."} or "/" in name:
            raise ValueError("private output requires a single file name")
        self.check()
        descriptor = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
                             | os.O_NONBLOCK, 0o600, dir_fd=self.descriptor)
        with os.fdopen(descriptor, "wb") as stream:
            retained = os.fstat(stream.fileno())
            if not stat.S_ISREG(retained.st_mode):
                raise ValueError("private output is not regular")
            self.check()
            writer = _Writer(stream, text)
            try:
                yield writer
            finally:
                writer.flush()
                os.fsync(writer.fileno())
                self._readback(name, identity(retained), writer.size, writer.sha256.hexdigest())
                os.fsync(self.descriptor)

    def save(self, name, raw):
        with self.create(name) as stream:
            stream.write(raw)
        return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


@contextmanager
def private_attempt(path, private_root):
    """Retain every ancestor descriptor through attempt creation and all writes."""
    path, private_root = Path(path).absolute(), Path(private_root).absolute()
    if ".." in path.parts or ".." in private_root.parts:
        raise ValueError("private output traversal refused")
    relative = path.relative_to(private_root)
    if not relative.parts:
        raise ValueError("private output must name a new attempt")
    with ExitStack() as stack:
        descriptor = os.open(path.anchor, DIRECTORY_FLAGS)
        stack.callback(os.close, descriptor)
        links = []
        for name in path.parts[1:-1]:
            try:
                child = os.open(name, DIRECTORY_FLAGS, dir_fd=descriptor)
            except OSError as error:
                raise ValueError("private output parent must be an existing no-follow directory") from error
            stack.callback(os.close, child)
            links.append((descriptor, name, child))
            descriptor = child
        # Existing attempts, including symlinks, cannot be reused or overwritten.
        Attempt(descriptor, links).check()
        os.mkdir(path.name, mode=0o700, dir_fd=descriptor)
        parent = descriptor
        try:
            child = os.open(path.name, DIRECTORY_FLAGS, dir_fd=parent)
        except OSError as error:
            raise ValueError("private attempt directory changed during creation") from error
        stack.callback(os.close, child)
        links.append((parent, path.name, child))
        output = Attempt(child, links)
        output.check()
        os.fsync(parent)
        try:
            yield output
        finally:
            os.fsync(child)
            os.fsync(parent)
        output.check()
