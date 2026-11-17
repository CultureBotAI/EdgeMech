"""Identity extraction must never read another session or expose conversation text."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/adhoc"))
SPEC = importlib.util.spec_from_file_location(
    "worker_identity", ROOT / "scripts/adhoc/identify_m5_worker_20261116.py")
IDENTITY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(IDENTITY)
SESSION = "01a1e6e0-1a0a-73c0-8877-d5338f533607"


@pytest.fixture
def logs(tmp_path):
    (tmp_path / ".temp").mkdir()
    events = tmp_path / ".temp/events.jsonl"
    events.write_text(json.dumps({"type": "thread.started", "thread_id": SESSION}) + "\n")
    sessions = tmp_path / "native"
    sessions.mkdir()
    own = sessions / f"rollout-date-{SESSION}.jsonl"
    entries = [{"type": "session_meta", "payload": {"id": SESSION, "private_prompt": "DO_NOT_EXPOSE"}},
               {"type": "turn_context", "payload": {"model": "actual-model", "effort": "high"}},
               {"type": "response_item", "payload": {"content": "DO_NOT_EXPOSE"}}]
    own.write_text("\n".join(json.dumps(event) for event in entries) + "\n")
    # Invalid unrelated data would fail if the extractor read arbitrary logs.
    (sessions / "another-session.jsonl").write_bytes(b"\xffDO_NOT_EXPOSE")
    return tmp_path, sessions, own, events


def test_identifies_only_own_model_without_exposing_content(logs):
    root, sessions, _, events = logs
    events.write_text(events.read_text() + '{"incomplete":')
    result = IDENTITY.identify(root, ".temp/events.jsonl", sessions)
    assert result["session_id"] == SESSION and result["model"] == "actual-model"
    assert result["observed_reasoning_efforts"] == ["high"]
    assert "DO_NOT_EXPOSE" not in json.dumps(result)


@pytest.mark.parametrize("damage", ["wrong_meta", "missing_model", "mixed_models", "duplicate_file",
                                   "wrong_thread", "multiple_threads", "symlink", "public_events"])
def test_ambiguous_or_unbound_identity_fails(logs, damage):
    root, sessions, own, events = logs
    event_path = ".temp/events.jsonl"
    if damage == "wrong_meta":
        own.write_text(own.read_text().replace(SESSION, "wrong-session"))
    elif damage == "missing_model":
        own.write_text(json.dumps({"type": "session_meta", "payload": {"id": SESSION}}))
    elif damage == "mixed_models":
        with own.open("a") as stream:
            stream.write(json.dumps({"type": "turn_context", "payload": {"model": "another-model"}}))
    elif damage == "duplicate_file":
        (sessions / f"copy-{SESSION}.jsonl").write_bytes(own.read_bytes())
    elif damage in {"wrong_thread", "multiple_threads"}:
        event = json.dumps({"type": "thread.started", "thread_id": "not-a-uuid" if damage == "wrong_thread"
                            else "11a1e6e0-1a0a-73c0-8877-d5338f533607"})
        events.write_text(events.read_text() + event + "\n")
    elif damage == "symlink":
        replacement = root / "copied-log"
        own.rename(replacement)
        own.symlink_to(replacement)
    else:
        event_path = "events.jsonl"
        (root / event_path).write_bytes(events.read_bytes())
    with pytest.raises(ValueError):
        IDENTITY.identify(root, event_path, sessions)
