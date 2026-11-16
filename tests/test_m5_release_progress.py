"""Retain command evidence when independent M5 launchers finish out of order."""

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


def test_stale_launcher_state_cannot_erase_another_command(tmp_path):
    """Rebuild aggregate progress from atomic records, including overlapping commands."""
    helper = Path(__file__).parents[1] / "scripts/adhoc/m5_release_state_20261116.py"
    spec = importlib.util.spec_from_file_location("release_progress", helper)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ROOT = tmp_path
    module.OUTPUT = tmp_path / ".temp/m5-worker-run-20261116"
    logs = module.OUTPUT / "commands"
    logs.mkdir(parents=True)
    baseline = {"label": "baseline", "status": "running", "log": "baseline.log",
                "started_at": "2026-11-16T20:00:00Z"}
    preflight = {"label": "preflight", "status": "passed", "log": "preflight.log",
                 "started_at": "2026-11-16T20:01:00Z"}
    stale_state = {"phase": "baseline", "pid": 1, "commands": [baseline]}
    module.save_command(logs / "baseline.json", baseline)
    module.save(stale_state)
    module.save_command(logs / "preflight.json", preflight)
    module.save({"phase": "preflight", "pid": 2, "blockers": ["current dependency"],
                 "results": {"preflight_passed": True}})
    baseline["status"] = "passed"
    module.save_command(logs / "baseline.json", baseline)
    module.save({})
    result = json.loads((module.OUTPUT / "progress.json").read_text())
    assert result["commands"] == [baseline, preflight]
    assert result["phase"] == "preflight"
    assert result["blockers"] == ["current dependency"]
    assert result["results"] == {"preflight_passed": True}
    assert "preflight: passed" in (module.ROOT / ".temp/M5_RELEASE_PROGRESS.md").read_text()


@pytest.fixture
def progress_module(tmp_path):
    """Keep imported check validation separate from actual release progress."""
    helper = Path(__file__).parents[1] / "scripts/adhoc/m5_release_state_20261116.py"
    spec = importlib.util.spec_from_file_location("release_progress_import", helper)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ROOT = tmp_path
    module.OUTPUT = tmp_path / ".temp/m5-worker-run-20261116"
    return module


def check_receipt(tmp_path, status="complete", code=0):
    """Write authentic-looking operational evidence with a byte-bound test log."""
    log = tmp_path / "command.log"
    log.write_bytes(b"5 passed in 2.94s\n")
    receipt = {"status": status, "command": ["pytest", "five-selected-cases"], "cwd": str(tmp_path),
               "pid": 123, "started_at": "2026-11-16T21:14:40+00:00"}
    if status != "running":
        receipt.update(exit_code=code, completed_at="2026-11-16T21:14:44+00:00", seconds=4.0,
                       log_sha256=hashlib.sha256(log.read_bytes()).hexdigest())
    path = tmp_path / "receipt.json"
    path.write_text(json.dumps(receipt))
    return path, receipt


@pytest.mark.parametrize(("status", "code", "expected"), [("complete", 0, "passed"), ("failed", 1, "failed"),
                                                         ("failed", -9, "failed"), ("running", None, "running")])
def test_import_preserves_valid_observed_terminal_or_running_status(progress_module, tmp_path, status, code, expected):
    """An active process stays running; a signal failure cannot become a passing result."""
    path, _ = check_receipt(tmp_path, status, code)
    entry = progress_module.import_check_record(path, "actual-check")
    assert entry["status"] == expected
    assert entry["exit_code"] == code
    assert entry["source_receipt_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize(("status", "code"), [("complete", 1), ("failed", 0), ("complete", None),
                                             ("complete", False), ("failed", True)])
def test_contradictory_terminal_evidence_is_refused(progress_module, tmp_path, status, code):
    """Boolean, missing and conflicting exit codes never justify terminal progress status."""
    path, _ = check_receipt(tmp_path, status, code)
    with pytest.raises(ValueError, match="contradicts exit code"):
        progress_module.import_check_record(path, "invalid-check")


@pytest.mark.parametrize("field", ["exit_code", "completed_at", "seconds", "log_sha256"])
def test_running_receipt_cannot_carry_terminal_evidence(progress_module, tmp_path, field):
    """A running label cannot conceal any already completed or contradictory field."""
    path, receipt = check_receipt(tmp_path, "running")
    receipt[field] = None
    path.write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match="contains terminal fields"):
        progress_module.import_check_record(path, "invalid-running")


@pytest.mark.parametrize("damage", ["changed", "missing_hash", "missing_log"])
def test_terminal_import_requires_the_actual_receipt_bound_log(progress_module, tmp_path, damage):
    """A claimed passing receipt cannot import changed or absent result evidence."""
    path, receipt = check_receipt(tmp_path)
    log = tmp_path / "command.log"
    if damage == "changed":
        log.write_bytes(b"5 failed\n")
    elif damage == "missing_hash":
        receipt.pop("log_sha256")
        path.write_text(json.dumps(receipt))
    else:
        log.unlink()
    with pytest.raises(ValueError, match="log"):
        progress_module.import_check_record(path, "invalid-log")


def test_failed_import_cannot_replace_existing_command_progress(progress_module, tmp_path, monkeypatch):
    """Validate before updating either the imported command row or aggregate state."""
    path, _ = check_receipt(tmp_path, "complete", 1)
    commands = progress_module.OUTPUT / "commands"
    commands.mkdir(parents=True)
    existing = commands / "retained.json"
    retained = b'{"label":"retained","status":"running"}\n'
    existing.write_bytes(retained)
    monkeypatch.setattr("sys.argv", ["m5_release_state", "--phase", "check", "--label", "retained",
                                     "--import-check", str(path)])
    with pytest.raises(SystemExit) as error:
        progress_module.main()
    assert error.value.code == 2
    assert existing.read_bytes() == retained
    assert not (tmp_path / ".temp/m5-release-progress.json").exists()
