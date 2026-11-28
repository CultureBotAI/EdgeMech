"""Issue228 successor: synthetic native-source archives stay inert and append-only."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts/adhoc"


@pytest.fixture
def audit_copy(tmp_path):
    root = tmp_path / "synthetic-checkout"
    scripts = root / "scripts/adhoc"
    scripts.mkdir(parents=True)
    for name in ("preparation_receipt_20261126.py", "preparation_repair_audit_20261126.py"):
        shutil.copyfile(SCRIPTS / name, scripts / name)
    work = root / ".temp/preparation-repairs-236-238-20261126"
    work.mkdir(parents=True)
    return root, work


def execute(audit_copy, *args):
    root, work = audit_copy
    result = subprocess.run([sys.executable, str(root / "scripts/adhoc/preparation_repair_audit_20261126.py"),
                             *map(str, args)], cwd=root, capture_output=True, timeout=8,
                            env={"PATH": os.defpath, "TMPDIR": str(root.parent),
                                 "PYTHONPYCACHEPREFIX": str(root.parent / "pycache")})
    logs = root.parent / "invocations"
    logs.mkdir(exist_ok=True)
    index = len(list(logs.glob("*.stdout")))
    (logs / f"{index}.stdout").write_bytes(result.stdout)
    (logs / f"{index}.stderr").write_bytes(result.stderr)
    return result


def synthetic_history(root):
    items = []
    for timestamp, payload in [
        ("2000-01-01T00:00:00Z", {"type": "custom_tool_call", "name": "exec",
                                "call_id": "excluded", "input": "earlier source"}),
        ("2000-01-01T00:00:01Z", {"type": "custom_tool_call", "name": "exec",
                                "call_id": "included", "input": "NEVER EXECUTE THIS HISTORICAL SOURCE\n"}),
        ("2000-01-01T00:00:02Z", {"type": "custom_tool_call_output", "call_id": "included",
                                "output": "historical synthetic output"}),
        ("2000-01-01T00:00:03Z", {"type": "function_call", "name": "wait",
                                "call_id": "unpaired", "arguments": '{"synthetic":true}'}),
    ]:
        items.append((json.dumps({"timestamp": timestamp, "type": "response_item",
                                  "payload": payload}) + "\n").encode())
    history = root / "synthetic-native.jsonl"
    history.write_bytes(b"".join(items) + b'{"unfinished":')
    return history, items


def test_historical_sources_preserve_exact_bytes_and_pairing(audit_copy):
    root, work = audit_copy
    history, items = synthetic_history(root)
    original = history.read_bytes()
    result = execute(audit_copy, "archive", "--history", history,
                     "--after", "2000-01-01T00:00:00Z", "--until", "2000-01-01T00:00:03Z",
                     "--output", work / "archive")
    assert result.returncode == 0
    assert history.read_bytes() == original
    assert (work / "archive/native-tool-records.jsonl").read_bytes() == b"".join(items[1:])
    assert (work / "archive/producer-0000.original.txt").read_bytes() == b"NEVER EXECUTE THIS HISTORICAL SOURCE\n"
    manifest = json.loads((work / "archive/manifest.json").read_bytes())
    assert manifest["historical_executions_replayed"] is False
    assert [c["execution_evidence"] for c in manifest["calls"]] == [
        "paired_native_output", "output_not_in_snapshot"]
    assert manifest["calls"][0]["original_timestamp"] == "2000-01-01T00:00:01Z"


@pytest.mark.parametrize("bad", ["traversal", "existing", "history_symlink"])
def test_archive_invalid_destinations_leave_existing_bytes(audit_copy, bad):
    root, work = audit_copy
    history, _ = synthetic_history(root)
    original = history.read_bytes()
    output = work / "archive"
    if bad == "traversal":
        output = work / ".." / ".." / "leaked"
    elif bad == "existing":
        output.mkdir()
        (output / "retained").write_bytes(b"retain")
    else:
        alias = root / "alias.jsonl"
        alias.symlink_to(history)
        history = alias
    result = execute(audit_copy, "archive", "--history", history,
                     "--after", "2000-01-01T00:00:00Z", "--output", output)
    assert result.returncode != 0
    assert history.read_bytes() == original
    assert not (root / "leaked").exists()
    if bad == "existing":
        assert (output / "retained").read_bytes() == b"retain"
    else:
        assert not output.exists()


def test_command_failure_is_retained_as_failure(audit_copy):
    root, work = audit_copy
    result = execute(audit_copy, "run", "--output", work / "failure", "--",
                     sys.executable, "-c", "print('synthetic failure');raise SystemExit(7)")
    assert result.returncode == 7
    receipt = json.loads((work / "failure/receipt.json").read_bytes())
    assert receipt["exit_code"] == 7
    assert receipt["classification"] == "OFFLINE_ENGINEERING_REPAIR_COMMAND_NOT_CANARY"
    assert (work / "failure/stdout").read_bytes() == b"synthetic failure\n"


def test_command_cache_symlink_refuses_before_execution(audit_copy):
    root, work = audit_copy
    outside = root.parent / "outside"
    outside.mkdir()
    (outside / "retained").write_bytes(b"retain")
    (work / "tmp").symlink_to(outside)
    result = execute(audit_copy, "run", "--output", work / "run", "--",
                     sys.executable, "-c", "from pathlib import Path;Path('ran').touch()")
    assert result.returncode != 0
    assert not (root / "ran").exists()
    assert not (work / "run").exists()
    assert (outside / "retained").read_bytes() == b"retain"


@pytest.mark.parametrize("mode", ["valid", "tracked_symlink", "existing_output"])
def test_build_snapshot_pins_working_bytes_and_preserves_sources(audit_copy, mode):
    root, work = audit_copy
    payload = root / "candidate.txt"
    payload.write_bytes(b"synthetic candidate")
    for command in (["git", "init", "-q"], ["git", "add", "candidate.txt"]):
        subprocess.run(command, cwd=root, check=True, capture_output=True)
    payload.write_bytes(b"updated working bytes")
    output = work / "build"
    outside = root.parent / "outside"
    outside.write_bytes(b"untouched")
    if mode == "tracked_symlink":
        payload.unlink()
        payload.symlink_to(outside)
    elif mode == "existing_output":
        output.mkdir()
        (output / "retained").write_bytes(b"retain")
    result = execute(audit_copy, "snapshot", "--output", output)
    assert outside.read_bytes() == b"untouched"
    if mode == "valid":
        assert result.returncode == 0
        assert payload.read_bytes() == b"updated working bytes"
        assert (output / "source/candidate.txt").read_bytes() == payload.read_bytes()
        receipt = json.loads((output / "manifest.json").read_bytes())
        assert receipt["source_files"] == 1
        assert receipt["originals_unchanged"] is True
    else:
        assert result.returncode != 0
        assert not (output / "manifest.json").exists()
        assert not (output / "source").exists()
        if mode == "existing_output":
            assert (output / "retained").read_bytes() == b"retain"
