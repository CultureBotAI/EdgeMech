"""Helper persistence/lineage failures use a fake provider, never a paid worker."""

import argparse
import importlib.util
import json
import os
import subprocess
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "m5_helper", Path(__file__).resolve().parents[1]
    / "scripts/adhoc/run_m5_helper_20261119.py")
worker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(worker)


def call(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


@pytest.fixture
def setup(tmp_path, monkeypatch):
    # Only fixtures accept the fake Python provider; production requires a
    # native Mach-O/ELF file so no unbound script interpreter is involved.
    monkeypatch.setattr(worker, "NATIVE_MAGICS", worker.NATIVE_MAGICS | {b"#!/u"})
    root = tmp_path / "repo"
    root.mkdir()
    call(root, "init", "-b", "helper-test")
    call(root, "config", "user.name", "Fixture")
    call(root, "config", "user.email", "fixture@example.invalid")
    call(root, "remote", "add", "origin", "https://github.com/CultureBotAI/EdgeMech.git")
    (root / ".gitignore").write_text(".temp/\n")
    (root / "prompt.md").write_text("Inspect the named witness; write the requested report.\n")
    call(root, "add", ".")
    call(root, "commit", "-m", "Fixture inputs")
    binary = tmp_path / "bin/codex"
    binary.parent.mkdir()
    binary.write_text(
        "#!/usr/bin/env python3\n"
        "import json, pathlib, sys\n"
        "sys.stdin.read()\n"
        "final = pathlib.Path(sys.argv[sys.argv.index('--output-last-message') + 1])\n"
        "final.write_text('Helper complete; inspect REPORT.md.\\n')\n"
        "(final.parent / 'REPORT.md').write_text('Inspected fixture input; no scientific review.\\n')\n"
        "print(json.dumps({'type': 'thread.started', 'thread_id': 'fixture'}))\n"
        "print(json.dumps({'type': 'turn.completed'}))\n"
    )
    binary.chmod(0o700)
    wrapper = tmp_path / "accounts.sh"
    wrapper.write_text('codex-work() { command codex "$@"; }\n')
    monkeypatch.setenv("CBORG_API_KEY", "fixture-secret-never-print")
    return root, binary, wrapper


def plan_for(setup, name="canary", unit="canary", mode="inspect", allow_commit=False,
             canary_receipt=None):
    root, binary, wrapper = setup
    return worker.make_plan(argparse.Namespace(
        root=str(root), prompt=str(root / "prompt.md"),
        output=str(root / ".temp/helper-workers-20261119" / name),
        wrapper=str(wrapper), codex_bin=str(binary), unit=unit, mode=mode,
        allow_commit=allow_commit, canary_receipt=canary_receipt))


def stage_and_execute(plan):
    output = Path(plan["output"])
    output.mkdir(parents=True, mode=0o700)
    worker.write_json(output / "plan.json", plan)
    worker.write_new(output / "prompt.md", worker.rendered_prompt(plan))
    worker.write_json(output / "metadata.json", {
        "plan_sha256": worker.sha(output / "plan.json"),
        "rendered_prompt_sha256": worker.sha(output / "prompt.md"),
    })
    previous = os.umask(0o077)
    try:
        worker.execute(output)
    finally:
        os.umask(previous)
    return output


def test_real_shell_path_persists_distinct_artifacts_without_secret(setup):
    plan = plan_for(setup)
    assert "fixture-secret" not in json.dumps(plan)
    output = stage_and_execute(plan)
    receipt = worker.check(output)
    assert receipt["status"] == "passed"
    assert receipt["scope"] == worker.SCOPE
    assert worker.check(output) == receipt
    assert (output / "REPORT.md").read_text() != (output / "final.md").read_text()
    assert "fixture-secret" not in json.dumps(receipt)
    helper = plan_for(setup, "followup", "helper", canary_receipt=str(output / "receipt.json"))
    assert helper["canary"]["sha256"] == worker.sha(output / "receipt.json")


def test_npm_trampoline_and_changed_native_are_rejected(setup):
    root, binary, wrapper = setup
    plan = plan_for(setup)
    binary.write_text(binary.read_text() + "# native replaced\n")
    with pytest.raises(ValueError, match="runtime changed"):
        worker.check_runtime(plan)
    binary.write_text("#!/usr/bin/env node\nconsole.log('not a native runtime');\n")
    with pytest.raises(ValueError, match="Node entrypoints"):
        worker.bindings(root, wrapper, binary)
    link = binary.parent / "npm/codex"
    link.parent.mkdir()
    link.symlink_to(binary)
    with pytest.raises(ValueError, match="regular native"):
        worker.bindings(root, wrapper, link)


def test_startup_drift_persists_failure_without_starting_provider(setup):
    plan = plan_for(setup)
    output = Path(plan["output"])
    output.mkdir(parents=True, mode=0o700)
    worker.write_json(output / "plan.json", plan)
    worker.write_new(output / "prompt.md", worker.rendered_prompt(plan))
    worker.write_json(output / "metadata.json", {
        "plan_sha256": worker.sha(output / "plan.json"),
        "rendered_prompt_sha256": worker.sha(output / "prompt.md"),
    })
    Path(plan["task_prompt"]["path"]).write_text("Changed after detached launch\n")
    worker.execute(output)
    result = json.loads((output / "completion.json").read_text())
    assert result["stage"] == "startup_replay"
    assert result["failure_type"] == "ValueError"
    assert not (output / "events.jsonl").exists()
    assert not (output / "REPORT.md").exists()


def test_later_helper_requires_canary(setup):
    with pytest.raises(ValueError, match="requires a canary"):
        plan_for(setup, "followup", "helper")


def test_prompt_drift_rejected_before_provider(setup):
    plan = plan_for(setup)
    (setup[0] / "prompt.md").write_text("Changed task")
    with pytest.raises(ValueError, match="prompt changed"):
        worker.check_runtime(plan)


def test_first_unit_can_implement_and_record_commit_lineage(setup):
    plan = plan_for(setup, mode="implement", allow_commit=True)
    output = stage_and_execute(plan)
    root = setup[0]
    (root / "new-helper.txt").write_text("Fixture implementation")
    call(root, "add", "new-helper.txt")
    call(root, "commit", "-m", "Fixture implementation")
    # Simulate the worker's final snapshot after its allowed commit.
    completion = json.loads((output / "completion.json").read_text())
    completion["ending_head"] = call(root, "rev-parse", "HEAD")
    (output / "completion.json").write_text(json.dumps(completion))
    receipt = worker.check(output)
    assert receipt["ending_head"] != receipt["bindings"]["head"]
    with pytest.raises(ValueError, match="different runtime"):
        plan_for(setup, "followup", "helper", canary_receipt=str(output / "receipt.json"))


def test_zero_exit_missing_report_does_not_pass(setup):
    output = stage_and_execute(plan_for(setup))
    (output / "REPORT.md").unlink()
    with pytest.raises(ValueError, match="artifact missing"):
        worker.check(output)
    assert not (output / "receipt.json").exists()


def test_report_tampering_fails_readback(setup):
    output = stage_and_execute(plan_for(setup))
    worker.check(output)
    (output / "REPORT.md").write_text("Changed report")
    with pytest.raises(ValueError, match="hash changed"):
        worker.check(output)


def test_duplicate_execution_preserves_first_outputs(setup):
    output = stage_and_execute(plan_for(setup))
    before = worker.sha(output / "events.jsonl")
    with pytest.raises(FileExistsError):
        worker.execute(output)
    assert worker.sha(output / "events.jsonl") == before


def test_symlink_output_rejected(setup):
    root = setup[0]
    (root / ".temp").symlink_to(root.parent, target_is_directory=True)
    with pytest.raises(ValueError, match="Symlink"):
        plan_for(setup)


def test_run_owns_new_session_and_freezes_plan(setup, monkeypatch):
    plan = plan_for(setup)
    plan_path = setup[0].parent / "plan.json"
    worker.write_json(plan_path, plan)
    commands = []
    original = subprocess.run

    def fake_tmux(command, **kwargs):
        if command[0] == "/fake/tmux":
            commands.append(command)
            return subprocess.CompletedProcess(command, 0)
        return original(command, **kwargs)

    monkeypatch.setattr(subprocess, "run", fake_tmux)
    result = worker.run(plan_path, "/fake/tmux")
    assert commands[0][1:5] == ["new-session", "-d", "-s", "edgemech-helper-canary"]
    assert "send-keys" not in commands[0]
    output = Path(result["output"])
    assert json.loads((output / "plan.json").read_text()) == plan
    with pytest.raises(FileExistsError):
        worker.run(plan_path, "/fake/tmux")
