"""Preserve frozen scientific state while updating all durable progress copies."""

import copy
import importlib.util
import json
import stat
import sys
from datetime import datetime
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "round02_progress",
    Path(__file__).parents[1] / "scripts/adhoc/record_m5_round02_progress_20261116.py",
)
progress = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(progress)


@pytest.fixture
def existing_progress(tmp_path, monkeypatch):
    run = tmp_path / ".temp/m5-round02-worker-20261116"
    run.mkdir(parents=True)
    monkeypatch.setattr(progress, "ROOT", tmp_path)
    monkeypatch.setattr(progress, "RUN", run)
    state = {
        "phase": "reviewers_completed",
        "next_task": "independent adjudication",
        "updated_at": "2026-11-17T00:31:49+00:00",
        "completed": ["package frozen", "initial matrices sealed"],
        "blockers": ["old phase blocker"],
        "round01": "failed; immutable d197474",
        "package_sha256": "a" * 64,
        "runtime": {"commit": "b" * 40, "model": "gpt-6-astra"},
        "reviewer_status": {
            "reviewer-a": {"status": "completed", "exit_code": 0},
            "reviewer-b": {"status": "completed", "exit_code": 0},
        },
        "running": {"fresh_reviewers": [], "coordinator_worker_pid": 123},
        "canonical_save": {"expected": 20, "saved": 0},
        "gates": {"round02": "failed", "remaining90": "closed"},
        "service_use": [{"service": "anonymous primary API", "calls": 1}],
        "unknown_future_field": {"preserve": ["nested", {"value": 17}]},
    }
    (run / "progress.json").write_text(json.dumps(state))
    # All four pre-existing copies may have broader permissions or stale bytes.
    for path in [run / "PROGRESS.md", tmp_path / ".temp/m5-round02-progress.json",
                 tmp_path / ".temp/M5_ROUND02_PROGRESS.md"]:
        path.write_text("stale mirror")
    for path in [run / "progress.json", run / "PROGRESS.md",
                 tmp_path / ".temp/m5-round02-progress.json",
                 tmp_path / ".temp/M5_ROUND02_PROGRESS.md"]:
        path.chmod(0o644)
    return state


def invoke(monkeypatch, phase, *options):
    monkeypatch.setattr(sys, "argv", ["progress-helper", phase, "--next",
                                    "preserve failed round", *options])
    progress.main()


def persisted_state():
    primary = (progress.RUN / "progress.json").read_bytes()
    prose = b"# M5 round02 progress\n\n" + primary
    expected = {
        progress.RUN / "progress.json": primary,
        progress.RUN / "PROGRESS.md": prose,
        progress.ROOT / ".temp/m5-round02-progress.json": primary,
        progress.ROOT / ".temp/M5_ROUND02_PROGRESS.md": prose,
    }
    for path, content in expected.items():
        assert path.read_bytes() == content
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
        assert not path.with_suffix(path.suffix + ".new").exists()
    return json.loads(primary)


def test_phase_change_preserves_frozen_runtime_reviewers_and_unknown_state(
    existing_progress, monkeypatch,
):
    before = copy.deepcopy(existing_progress)
    invoke(monkeypatch, "adjudicated", "--completed", "initial matrices sealed",
           "--completed", "adjudication complete", "--completed", "adjudication complete",
           "--blocker", "calibration failed")
    after = persisted_state()
    expected = copy.deepcopy(before)
    expected.update(phase="adjudicated", next_task="preserve failed round",
                    completed=[*before["completed"], "adjudication complete"],
                    blockers=["calibration failed"], updated_at=after["updated_at"])
    assert after == expected
    assert datetime.fromisoformat(after["updated_at"]).utcoffset().total_seconds() == 0
    assert existing_progress == before

    # Repeating a completed milestone in a later phase must not create duplicates.
    invoke(monkeypatch, "delivery", "--completed", "adjudication complete",
           "--completed", "delivery checked", "--blocker", "calibration failed")
    expected.update(phase="delivery", completed=[*expected["completed"], "delivery checked"])
    final = persisted_state()
    expected["updated_at"] = final["updated_at"]
    assert final == expected


@pytest.mark.parametrize("blockers", [[], ["missing canonical pairs", "source fidelity below floor"]])
def test_phase_blockers_replace_stale_values_in_all_private_destinations(
    existing_progress, monkeypatch, blockers,
):
    options = [argument for blocker in blockers for argument in ("--blocker", blocker)]
    invoke(monkeypatch, "checked", *options)
    after = persisted_state()
    assert after["blockers"] == blockers
    assert after["completed"] == existing_progress["completed"]
    assert after["package_sha256"] == existing_progress["package_sha256"]
    assert after["reviewer_status"] == existing_progress["reviewer_status"]
