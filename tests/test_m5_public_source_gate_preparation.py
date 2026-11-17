"""Publication preparation never invents independent review or hides inventory drift."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts" / "adhoc"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location(
    "prepare_m5_public_source_gate_20261116", SCRIPTS / "prepare_m5_public_source_gate_20261116.py")
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


@pytest.fixture
def proposal(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / ".gitignore").write_text(".temp/\n")
    subprocess.run(["git", "add", ".gitignore"], cwd=tmp_path, check=True)
    subprocess.run(["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@invalid",
                    "commit", "-qm", "base"], cwd=tmp_path, check=True)
    (tmp_path / "new.txt").write_text("Original test text.\n")
    (tmp_path / ".temp").mkdir()
    value = {"root": str(tmp_path), "baseline": "HEAD", "quote_catalog_reviews": [],
             "extra_files": [], "excluded_private_files": []}
    inventory = {"files": helper.public_inventory(value)}
    inventory_raw = helper.publication.encoded(inventory)
    (tmp_path / ".temp/inventory.json").write_bytes(inventory_raw)
    attestation = {"reviewer": "independent-reviewer", "all_files_inspected": True,
                   "no_unaccounted_external_quotations": True,
                   "reviewed_inventory": {"path": ".temp/inventory.json",
                   "sha256": helper.publication.digest(inventory_raw)}}
    raw = helper.publication.encoded(attestation)
    (tmp_path / ".temp/attestation.json").write_bytes(raw)
    value["review_attestation"] = {"path": ".temp/attestation.json",
                                  "sha256": helper.publication.digest(raw)}
    return value


def test_prepare_invokes_actual_gate_with_exact_independent_attestation(proposal):
    result = helper.execute(proposal, "coordinator", "gate", ".temp/gate-output")
    assert result["passed"] and not result["published"]
    root = Path(proposal["root"])
    config = json.loads((root / ".temp/gate-output/config.json").read_bytes())
    assert config["review_attestation"]["reviewer"] == "independent-reviewer"
    assert config["review_attestation_source"] == proposal["review_attestation"]
    assert (root / ".temp/gate-output").stat().st_mode & 0o777 == 0o700
    assert (root / ".temp/gate-output/config.json").stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize("damage", ["added", "changed", "omitted"])
def test_changed_added_or_omitted_inventory_rejected_by_actual_gate(proposal, damage):
    config = helper.prepare(proposal, "coordinator")
    root = Path(proposal["root"])
    if damage == "added":
        (root / "addition.txt").write_text("More text\n")
    elif damage == "changed":
        (root / "new.txt").write_text("Changed\n")
    else:
        config["files"] = []
    with pytest.raises(ValueError):
        helper.source_gate.gate(config)


def test_self_attestation_and_uninspected_addition_are_rejected(proposal):
    with pytest.raises(ValueError, match="separate identified reviewer"):
        helper.prepare(proposal, " independent-reviewer ")
    (Path(proposal["root"]) / "addition.txt").write_text("New uninspected file\n")
    with pytest.raises(ValueError, match="exact current public inventory"):
        helper.prepare(proposal, "coordinator")


def test_plan_never_creates_attestation(proposal):
    proposal.pop("review_attestation")
    result = helper.execute(proposal, "coordinator", "plan", ".temp/unsigned-plan")
    inventory = json.loads(Path(result["path"]).read_bytes())
    assert "review_attestation" not in inventory
    assert "all_files_inspected" not in inventory
    with pytest.raises(KeyError):
        helper.prepare(proposal, "coordinator")


def test_catalog_pin_is_replayed_without_reusing_old_attestation(proposal):
    root = Path(proposal["root"])
    raw = helper.publication.encoded({"quote_catalog_reviews": [],
                                     "review_attestation": {"reviewer": "untrusted"},
                                     "files": ["not reused"]})
    (root / ".temp/old-config.json").write_bytes(raw)
    proposal["quote_catalog_config"] = {"path": ".temp/old-config.json",
                                        "sha256": helper.publication.digest(raw)}
    config = helper.prepare(proposal, "coordinator")
    assert config["review_attestation"]["reviewer"] == "independent-reviewer"
    assert all(isinstance(file, dict) for file in config["files"])
    (root / ".temp/old-config.json").write_bytes(raw + b"changed")
    with pytest.raises(ValueError, match="Pinned document changed"):
        helper.prepare(proposal, "coordinator")


def test_attestation_source_hash_is_required(proposal):
    (Path(proposal["root"]) / ".temp/attestation.json").write_text("{}")
    with pytest.raises(ValueError, match="Pinned document changed"):
        helper.prepare(proposal, "coordinator")
