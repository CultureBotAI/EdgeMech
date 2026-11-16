"""A worker exit code alone cannot authorize fan-out or overwrite retained runs."""

from __future__ import annotations

import argparse
import importlib.util
import json
import stat
from pathlib import Path

import pytest

HELPER = Path(__file__).resolve().parents[1] / "scripts/adhoc/run_m5_review_worker_20261116.py"


@pytest.fixture
def worker(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("m5_worker", HELPER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    root = tmp_path.resolve()
    codex = root / "codex"
    codex.write_text("#!/bin/sh\nexit 0\n")
    codex.chmod(0o700)
    prompt = root / "prompt.md"
    prompt.write_text("Run one bounded canary and persist the required proof.\n")
    args = argparse.Namespace(plan=False, run=True, prompt=prompt, output_root=root / "canary",
                              codex=codex, workdir=root, role="canary", canary_receipt=None,
                              add_dir=[])
    controls = {"exit_code": 0, "artifact": "verified packet", "corrupt": False, "calls": 0}
    monkeypatch.setattr(module.subprocess, "check_output", lambda command, **kw:
                        "" if "status" in command else "a" * 40 + "\n")
    monkeypatch.setattr(module, "load_cborg", lambda environment: None)
    monkeypatch.setenv("CBORG_API_KEY", "fixture-key-not-a-real-credential")

    class Process:
        def __init__(self, command, *, stdin, stdout, stderr, cwd, env):
            controls["calls"] += 1
            controls["command"] = command
            self.pid = 12345
            self.returncode = controls["exit_code"]
            self.output = Path(env["EDGEMECH_WORKER_OUTPUT_ROOT"])
            stdout.write(b'{"type":"thread.started"}\n')

        def communicate(self, prompt_bytes):
            (self.output / "final.md").write_text("Canary finished.\n")
            evidence = self.output / "packet-replay.json"
            evidence.write_text(controls["artifact"])
            result = {
                "status": "passed",
                "checks": [{"name": name, "passed": True} for name in sorted(module.CHECKS)],
                "artifacts": [{"path": str(evidence),
                               "sha256": "0" * 64 if controls["corrupt"] else module.digest(evidence)}],
            }
            (self.output / "canary-result.json").write_text(json.dumps(result))

    monkeypatch.setattr(module.subprocess, "Popen", Process)
    return module, args, controls


def test_plan_is_read_only_and_does_not_load_credentials_or_start_worker(worker, monkeypatch):
    module, args, controls = worker
    args.plan = True
    monkeypatch.setattr(module, "load_cborg", lambda env: pytest.fail("plan read credentials"))
    assert module.launch(args) == 0
    assert controls["calls"] == 0
    assert not args.output_root.exists()


def test_successful_canary_persists_replayable_private_receipt_and_no_model_override(worker):
    module, args, controls = worker
    assert module.launch(args) == 0
    output = args.output_root
    state = json.loads((output / "metadata.json").read_text())
    assert state["status"] == "passed" and state["exit_code"] == 0
    assert state["worker_pid"] == 12345
    assert "fixture-key" not in (output / "metadata.json").read_text()
    assert module.verify_receipt(output / "canary-receipt.json", state)["sha256"]
    assert stat.S_IMODE(output.stat().st_mode) == 0o700
    for name in ("metadata.json", "canary-receipt.json", "events.jsonl", "stderr.log", "final.md"):
        assert stat.S_IMODE((output / name).stat().st_mode) == 0o600
    assert "--approve-for-me" in controls["command"]
    assert "workspace-write" in controls["command"]
    assert "--model" not in controls["command"] and "-m" not in controls["command"]
    with pytest.raises(ValueError, match="already exists"):
        module.launch(args)
    assert controls["calls"] == 1


@pytest.mark.parametrize("control,value,error", [
    ("exit_code", 9, "exited with code 9"),
    ("artifact", "", "empty canary artifact"),
    ("corrupt", True, "hash mismatch"),
])
def test_nonzero_exit_or_invalid_artifact_never_creates_passing_receipt(worker, control, value, error):
    module, args, controls = worker
    controls[control] = value
    with pytest.raises(ValueError, match=error):
        module.launch(args)
    assert not (args.output_root / "canary-receipt.json").exists()
    assert json.loads((args.output_root / "metadata.json").read_text())["status"] == "failed"


@pytest.mark.parametrize("key", ["git_head", "helper_sha256", "codex_path", "codex_sha256"])
def test_incompatible_runtime_cannot_reuse_canary(worker, key):
    module, args, controls = worker
    module.launch(args)
    bindings = json.loads((args.output_root / "metadata.json").read_text())
    bindings[key] = "different"
    with pytest.raises(ValueError, match="runtime changed"):
        module.verify_receipt(args.output_root / "canary-receipt.json", bindings)


def test_changed_artifact_blocks_follow_on_launch_before_process_or_output(worker):
    module, args, controls = worker
    module.launch(args)
    args.canary_receipt = args.output_root / "canary-receipt.json"
    (args.output_root / "packet-replay.json").write_text("altered evidence")
    args.output_root = args.workdir / "calibration"
    args.role = "calibration"
    with pytest.raises(ValueError, match="hash mismatch"):
        module.launch(args)
    assert controls["calls"] == 1 and not args.output_root.exists()


def test_no_receipt_blocks_follow_on_launch(worker):
    module, args, controls = worker
    args.role = "release"
    with pytest.raises(ValueError, match="passing canary receipt is required"):
        module.launch(args)
    assert controls["calls"] == 0 and not args.output_root.exists()


def test_canary_that_changes_tracked_runtime_cannot_authorize_follow_on_work(worker, monkeypatch):
    module, args, controls = worker

    def git_state(command, **kwargs):
        if "status" in command:
            return " M src/edgemech/occurrence_review.py\n" if controls["calls"] else ""
        return "a" * 40 + "\n"

    monkeypatch.setattr(module.subprocess, "check_output", git_state)
    with pytest.raises(ValueError, match="changed tracked runtime"):
        module.launch(args)
    assert not (args.output_root / "canary-receipt.json").exists()


def test_missing_required_check_invalidates_canary_receipt(worker):
    module, args, controls = worker
    module.launch(args)
    path = args.output_root / "canary-result.json"
    result = json.loads(path.read_text())
    result["checks"] = result["checks"][:-1]
    path.write_text(json.dumps(result))
    with pytest.raises(ValueError, match="mandatory canary checks"):
        module.validate_canary_result(args.output_root)
