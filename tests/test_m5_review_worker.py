"""A worker exit code alone cannot authorize fan-out or overwrite retained runs."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import stat
import subprocess
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
    codex.write_bytes(b"\x7fELFfixture-native-executable")
    codex.chmod(0o700)
    prompt = root / "prompt.md"
    prompt.write_text("Run one bounded canary and persist the required proof.\n")
    args = argparse.Namespace(plan=False, run=True, prompt=prompt, output_root=root / "canary",
                              codex=codex, workdir=root, role="canary", canary_receipt=None,
                              add_dir=[])
    (root / "uv.lock").write_text("fixture locked runtime\n")
    case = root / module.FRESH47
    case.mkdir(parents=True)
    (case / "packet.json").write_text(json.dumps({"occurrence_id": "frozen-fresh47"}))
    (case / "receipt.json").write_text(json.dumps(
        {"occurrence_id": "frozen-fresh47", "case_id": "fresh-47"}))
    cohort = root / "artifacts/edge-calibration-20261115/cohort.json"
    cohort.parent.mkdir(parents=True)
    cohort.write_text(json.dumps({"cases": [
        {"occurrence_id": "frozen-fresh47", "case_id": "fresh-47"}]}))
    controls = {"exit_code": 0, "artifact": None, "corrupt": False, "calls": 0,
                "validator_exit": 0, "validator_commands": [], "arbitrary_only": False}
    monkeypatch.setattr(module.subprocess, "check_output", lambda command, **kw:
                        "" if "status" in command else "a" * 40 + "\n")
    monkeypatch.setattr(module, "load_cborg", lambda environment: None)
    monkeypatch.setenv("CBORG_API_KEY", "fixture-key-not-a-real-credential")
    monkeypatch.setattr(module.importlib.metadata, "distributions", lambda: [])

    def validator(command, **kwargs):
        controls["validator_commands"].append(command)
        return subprocess.CompletedProcess(command, controls["validator_exit"], b"verified\n", b"")

    monkeypatch.setattr(module.subprocess, "run", validator)

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
            artifacts = []
            for name in (("arbitrary.txt",) if controls["arbitrary_only"] else
                         ("packet.json", "receipt.json")):
                evidence = self.output / name
                if controls["arbitrary_only"]:
                    evidence.write_text("not a replayed packet")
                elif name == "packet.json" and controls["artifact"] is not None:
                    evidence.write_text(controls["artifact"])
                else:
                    evidence.write_bytes((case / name).read_bytes())
                artifacts.append({"path": str(evidence),
                                  "sha256": "0" * 64 if controls["corrupt"]
                                  else module.digest(evidence)})
            result = {
                "status": "passed",
                "checks": [{"name": name, "passed": True} for name in sorted(module.CHECKS)],
                "artifacts": artifacts,
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
    assert module.verify_receipt(output / "canary-receipt.json", state, args.workdir,
                                 module.child_environment(args.workdir))["sha256"]
    assert len(controls["validator_commands"]) == 4
    assert stat.S_IMODE(output.stat().st_mode) == 0o700
    for name in ("metadata.json", "canary-receipt.json", "events.jsonl", "stderr.log", "final.md"):
        assert stat.S_IMODE((output / name).stat().st_mode) == 0o600
    assert "--approve-for-me" in controls["command"]
    assert "--sandbox" not in controls["command"]  # conflicts with --approve-for-me
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


@pytest.mark.parametrize("key", ["git_head", "helper_sha256", "codex_path", "codex_sha256",
                                 "host", "python_executable", "python_prefix", "python_version",
                                 "lock_sha256", "distributions_sha256", "environment_sha256"])
def test_incompatible_runtime_cannot_reuse_canary(worker, key):
    module, args, controls = worker
    module.launch(args)
    bindings = json.loads((args.output_root / "metadata.json").read_text())
    bindings[key] = "different"
    with pytest.raises(ValueError, match="runtime changed"):
        module.verify_receipt(args.output_root / "canary-receipt.json", bindings, args.workdir,
                              module.child_environment(args.workdir))


def test_changed_artifact_blocks_follow_on_launch_before_process_or_output(worker):
    module, args, controls = worker
    module.launch(args)
    args.canary_receipt = args.output_root / "canary-receipt.json"
    (args.output_root / "packet.json").write_text("altered evidence")
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


def test_hash_valid_arbitrary_artifact_does_not_substitute_for_packet_replay(worker):
    module, args, controls = worker
    controls["arbitrary_only"] = True
    with pytest.raises(ValueError, match="Missing or empty canary artifact"):
        module.launch(args)
    assert not (args.output_root / "canary-receipt.json").exists()


def test_wrong_case_even_when_copy_matches_source_is_rejected(worker):
    module, args, controls = worker
    packet = args.workdir / module.FRESH47 / "packet.json"
    packet.write_text(json.dumps({"occurrence_id": "another-case"}))
    with pytest.raises(ValueError, match="not the frozen fresh-47 occurrence"):
        module.launch(args)
    assert not controls["validator_commands"]


def test_parent_validator_failure_overrides_success_claim(worker):
    module, args, controls = worker
    controls["validator_exit"] = 1
    with pytest.raises(ValueError, match="Independent validator failed"):
        module.launch(args)
    assert not (args.output_root / "canary-receipt.json").exists()
    assert json.loads((args.output_root / "validator-results.json").read_text())[0]["exit_code"] == 1


def test_follow_on_reexecutes_validator_and_refuses_new_failure(worker):
    module, args, controls = worker
    module.launch(args)
    args.canary_receipt = args.output_root / "canary-receipt.json"
    args.output_root = args.workdir / "calibration"
    args.role = "calibration"
    controls["validator_exit"] = 1
    with pytest.raises(ValueError, match="Independent validator failed"):
        module.launch(args)
    assert controls["calls"] == 1 and not args.output_root.exists()


@pytest.mark.parametrize("changed", ["host", "python", "environment"])
def test_actual_runtime_change_blocks_follow_on_worker(worker, monkeypatch, changed):
    module, args, controls = worker
    module.launch(args)
    args.canary_receipt = args.output_root / "canary-receipt.json"
    args.output_root = args.workdir / "calibration"
    args.role = "calibration"
    if changed == "host":
        monkeypatch.setattr(module.socket, "gethostname", lambda: "different-host")
    elif changed == "python":
        monkeypatch.setattr(module.sys, "version", "different-python-runtime")
    else:
        monkeypatch.setenv("PATH", "/different/runtime/path")
    with pytest.raises(ValueError, match="Canary runtime changed"):
        module.launch(args)
    assert controls["calls"] == 1 and not args.output_root.exists()


def test_codex_wrapper_is_not_a_native_runtime_binding(worker):
    module, args, controls = worker
    args.codex.write_text("#!/usr/bin/env node\n// wrapper\n")
    with pytest.raises(ValueError, match="native Codex executable"):
        module.launch(args)
    assert controls["calls"] == 0


def test_same_selected_venv_can_run_in_another_same_head_worktree(worker, monkeypatch):
    module, args, controls = worker
    monkeypatch.setattr(module.sys, "prefix", str(args.workdir / ".venv"))
    module.launch(args)
    args.canary_receipt = args.output_root / "canary-receipt.json"
    original = args.workdir
    args.workdir = original / "coordinator"
    args.workdir.mkdir()
    shutil.copyfile(original / "uv.lock", args.workdir / "uv.lock")
    shutil.copytree(original / "artifacts", args.workdir / "artifacts")
    shutil.copytree(original / ".temp", args.workdir / ".temp")
    args.output_root = args.workdir / "run"
    args.role = "calibration"
    assert module.launch(args) == 0
    assert controls["calls"] == 2
