"""Synthetic #228 dispatch checks; no real tmux/socket/worker interaction."""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HELPER = Path(__file__).parents[1] / "scripts/adhoc/dispatch_restart_preparation_task_20261128.sh"
FAKE = r'''
import json, os, sys
from pathlib import Path
args = sys.argv[1:]
log = Path(os.environ["FAKE_LOG"])
with log.open("a") as stream:
    stream.write(json.dumps(args) + "\n")
if os.environ.get("FAIL_COMMAND") in args:
    sys.exit(1)
if "display-message" in args:
    print("ambient|789|/dev/ambient|0" if "client_readonly" in args[-1] else os.environ["PANE"])
elif "list-clients" in args:
    print(os.environ["CLIENT"])
elif "capture-pane" in args:
    changed = os.environ.get("CHANGE_AFTER_LOAD") and "load-buffer" in log.read_text()
    print("changed" if changed else os.environ["SCREEN"])
elif "list-buffers" in args:
    print(os.environ.get("BUFFERS", ""))
'''


@pytest.fixture
def dispatch(tmp_path):
    fake = tmp_path / "fake-tmux"
    fake.write_text(f"#!{sys.executable}\n" + FAKE)
    fake.chmod(0o700)
    prompt = tmp_path / "task.md"
    prompt.write_text("Authorized synthetic task\n")
    log = tmp_path / "calls.jsonl"
    pane = "owned|%9|123|/dev/test|/owned"
    client = "control|456|/dev/control|0"
    env = {**os.environ, "FAKE_LOG": str(log), "PANE": pane,
           "CLIENT": client, "SCREEN": "empty"}

    def run(mode, changes=None):
        child = {**env, **(changes or {})}
        result = subprocess.run([
            "/bin/bash", str(HELPER), mode, str(fake), "fake-socket", "%9", pane,
            "control", client, hashlib.sha256(b"empty\n").hexdigest(), str(prompt),
            hashlib.sha256(prompt.read_bytes()).hexdigest(), "owned-buffer"],
            env=child, capture_output=True, text=True, timeout=10)
        calls = [json.loads(line) for line in log.read_text().splitlines()]
        return result, calls

    return run


def test_paste_never_sends_enter(dispatch):
    result, calls = dispatch("paste")
    assert result.returncode == 0, result.stderr
    assert any("paste-buffer" in call for call in calls)
    assert not any("send-keys" in call for call in calls)
    assert "paste_attempted_at_utc=" in result.stdout


def test_submit_uses_explicit_client_and_never_repastes(dispatch):
    result, calls = dispatch("submit")
    assert result.returncode == 0, result.stderr
    sends = [call for call in calls if "send-keys" in call]
    assert len(sends) == 1 and sends[0][-6:] == ["send-keys", "-c", "control", "-t", "%9", "Enter"]
    assert not any("paste-buffer" in call or "load-buffer" in call for call in calls)
    assert "submit_attempted_at_utc=" in result.stdout


@pytest.mark.parametrize("mode", ["paste", "submit"])
@pytest.mark.parametrize("changes", [
    {"CLIENT": "control|456|/dev/control|1"},
    {"CLIENT": "other|456|/dev/control|0"},
    {"PANE": "different"},
    {"SCREEN": "question or changed composer"},
])
def test_changed_identity_client_or_screen_refuses_input(dispatch, mode, changes):
    result, calls = dispatch(mode, changes)
    assert result.returncode != 0
    assert not any("paste-buffer" in call or "send-keys" in call for call in calls)


def test_screen_change_after_load_preserves_composer_without_paste(dispatch):
    result, calls = dispatch("paste", {"CHANGE_AFTER_LOAD": "1"})
    assert result.returncode != 0
    assert any("load-buffer" in call for call in calls)
    assert not any("paste-buffer" in call or "send-keys" in call for call in calls)


def test_existing_named_buffer_is_not_overwritten(dispatch):
    result, calls = dispatch("paste", {"BUFFERS": "owned-buffer"})
    assert result.returncode != 0
    assert not any("load-buffer" in call or "paste-buffer" in call for call in calls)


@pytest.mark.parametrize("command", ["list-clients", "display-message", "capture-pane", "list-buffers"])
def test_failed_observation_never_performs_input(dispatch, command):
    result, calls = dispatch("paste", {"FAIL_COMMAND": command})
    assert result.returncode != 0
    assert not any("paste-buffer" in call or "send-keys" in call for call in calls)
