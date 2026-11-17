"""Future package assembly pins the same execution paths as the maintained launcher."""
from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path

import pytest
from test_calibration_round import round_inputs as round_inputs_fixture

round_inputs = round_inputs_fixture
ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts" / "adhoc"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location(
    "assembly_inventory", SCRIPTS / "assemble_m5_round03_20261116.py")
assembly = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(assembly)


def test_real_inventory_and_hidden_ignored_execution_freeze_without_duplicate_fixed_files(
        round_inputs, monkeypatch):
    rounds, root, _, _, config, put = round_inputs
    monkeypatch.setattr(assembly, "rounds", rounds)
    # Use the actual maintained inventory, not a parallel enumerator or a fixed
    # count that silently becomes obsolete when another helper is introduced.
    for item in assembly.worker.execution_inventory(ROOT):
        target = root / item["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / item["path"], target)
    extras = ("scripts/.hidden-fixture.py", "scripts/ignored/.fixture-command")
    (root / ".gitignore").write_text("scripts/.hidden-fixture.py\nscripts/ignored/\n")
    for path in extras:
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# synthetic inventory fixture\n")
    (root / extras[1]).chmod(0o700)
    inventory = assembly.worker.execution_inventory(root)
    declared_paths = assembly.runtime_paths(root)
    assert set(extras) <= declared_paths
    fixed = {rounds.PROTOCOL: "protocol", rounds.COHORT: "cohort",
             "docs/record-review-profile.md": "profile",
             "scripts/adhoc/calibration_round_20261116.py": "round_helper"}
    assert not set(fixed) & declared_paths
    declared = {item["path"]: item for item in config["files"]}
    for path in declared_paths:
        declared.setdefault(path, {"path": path, "role": "proof_adapter"})
    config["files"] = list(declared.values())
    config["round_id"] = assembly.PACKAGE_ID
    put("complete-runtime-config.json", config)
    rounds.freeze(root, "complete-runtime-config.json", "complete-runtime-manifest.json")
    manifest = rounds.read(root, "complete-runtime-manifest.json")
    pins = {item["path"]: item for item in manifest["files"]}
    assert len(pins) == len(manifest["files"])
    assert manifest["round_id"] == assembly.PACKAGE_ID
    assert rounds.RUNTIME_PATHS <= pins.keys()
    for item in inventory:
        assert pins[item["path"]]["sha256"] == item["sha256"]
        assert pins[item["path"]]["role"] == fixed.get(item["path"], "proof_adapter")
    for path, role in fixed.items():
        matches = [item for item in manifest["files"] if item["path"] == path]
        assert len(matches) == 1
        assert matches[0]["role"] == role
    assert len(rounds.verify(root, "complete-runtime-manifest.json")["packet_replay"]) == 10


def test_assembly_inventory_preserves_maintained_symlink_rejection(tmp_path):
    (tmp_path / "scripts").mkdir()
    (tmp_path / "original.py").write_text("# synthetic fixture\n")
    (tmp_path / "scripts" / ".hidden.py").symlink_to(tmp_path / "original.py")
    with pytest.raises(ValueError, match="symlink"):
        assembly.runtime_paths(tmp_path)
