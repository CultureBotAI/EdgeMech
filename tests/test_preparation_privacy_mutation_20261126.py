"""Issue238/228: fresh privacy controls and preserved synthetic-only staging."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FILES = ["scripts/adhoc/preparation_privacy_mutation_20261126.py",
         "scripts/adhoc/preparation_public_projection_20261126.py",
         "scripts/adhoc/preparation_receipt_20261126.py",
         "scripts/adhoc/preparation_readback_20261126.py",
         "tests/test_preparation_public_projection_20261126.py"]


@pytest.mark.parametrize("destination", ["valid", "existing", "symlink", "traversal"])
def test_fresh_mutation_processes_and_staging_guards(tmp_path, destination):
    root = tmp_path / "synthetic-checkout"
    for name in FILES:
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    originals = {name: (root / name).read_bytes() for name in FILES}
    staging = root / ".temp/fulltext/preparation-repairs-236-238"
    staging.mkdir(parents=True)
    output = staging / "mutation"
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "retained").write_bytes(b"unchanged")
    if destination == "existing":
        output.mkdir()
        (output / "retained").write_bytes(b"unchanged")
    elif destination == "symlink":
        output.symlink_to(outside)
    elif destination == "traversal":
        output = staging / ".." / "leaked"
    result = subprocess.run([sys.executable, FILES[0], "--output", str(output)], cwd=root,
        env={"PATH": os.defpath, "TMPDIR": str(tmp_path),
             "PYTHONPYCACHEPREFIX": str(tmp_path / "pycache")},
        capture_output=True, timeout=30, check=False)
    (tmp_path / "stdout").write_bytes(result.stdout)
    (tmp_path / "stderr").write_bytes(result.stderr)
    (tmp_path / "exit-code").write_text(str(result.returncode))
    assert all((root / name).read_bytes() == raw for name, raw in originals.items())
    assert (outside / "retained").read_bytes() == b"unchanged"
    assert list(outside.iterdir()) == [outside / "retained"]
    if destination == "valid":
        assert result.returncode == 0, result.stderr.decode()
        receipt = json.loads((output / "result.json").read_bytes())
        assert receipt["passed"] is True
        assert [run["exit_code"] for run in receipt["runs"]] == [0, 1, 1]
        assert [len(run["failures"]) for run in receipt["runs"]] == [0, 7, 5]
        assert all(run["meaningful"] and not run["errors"] for run in receipt["runs"])
    else:
        assert result.returncode != 0
        assert not (output / "result.json").exists()
        assert not (staging.parent / "leaked").exists()
        if destination == "existing":
            assert (output / "retained").read_bytes() == b"unchanged"
