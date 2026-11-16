"""Retain command evidence when independent M5 launchers finish out of order."""

import importlib.util
import json
from pathlib import Path


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
