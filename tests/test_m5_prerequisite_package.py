"""Prerequisite staging must not rebind changed evidence or overwrite old work."""
from __future__ import annotations

import json
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_calibration_preparation import preparation as preparation

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "adhoc"))
import prepare_m5_prerequisite_package_20261117 as package  # noqa: E402


@pytest.fixture
def staging(tmp_path, monkeypatch):
    root, source = tmp_path / "new", tmp_path / "retained"
    root.mkdir()
    source.mkdir()
    (root / "runtime.py").write_text("new runtime\n")
    (source / "evidence.txt").write_text("retained source\n")
    manifest = {"files": [
        {"path": "runtime.py", "role": "proof_adapter", "sha256": "old-runtime-hash"},
        {"path": "evidence.txt", "role": "authority", "version": "1",
         "sha256": package.rounds.digest((source / "evidence.txt").read_bytes())},
        {"path": "old-prompt.md", "role": "instructions", "sha256": "historical"},
    ], "cases": []}
    fixture = {"review": {"scientific_review": False, "verdict": "not_assessed"},
               "assessments": [{"category": "NOT_ASSESSABLE"}] * 6}

    def put(name, value):
        raw = json.dumps(value).encode()
        (source / name).write_bytes(raw)
        return package.rounds.digest(raw)

    def git(command, **kwargs):
        if "status" in command:
            return ""
        if "remote" in command:
            return "https://github.com/CultureBotAI/EdgeMech.git\n"
        if "ls-files" in command:
            return "runtime.py\n"
        if "rev-parse" in command:
            return "a" * 40
        raise AssertionError(command)

    monkeypatch.setattr(package.subprocess, "check_output", git)
    monkeypatch.setattr(package.subprocess, "run", lambda *a, **kw: SimpleNamespace(returncode=0))

    def invoke():
        return package.plan(root, source, "manifest.json", put("manifest.json", manifest),
                            "spec.json", put("spec.json", fixture), ".temp/new-package")

    return root, source, manifest, fixture, invoke


def staged_ledger(staging, monkeypatch):
    root, source, _, _, invoke = staging
    _, _, _, actions = invoke()
    (root / "evidence.txt").write_bytes((source / "evidence.txt").read_bytes())
    monkeypatch.setattr(package.worker, "execution_inventory", lambda root: [])
    return root, {"runtime_commit": "a" * 40, "actions": actions,
                  "execution_inventory": [], "prerequisite_documents": []}


def test_transition_rejects_authority_drift_after_approved_plan(staging, monkeypatch):
    root, ledger = staged_ledger(staging, monkeypatch)
    package.verify_transition(root, ledger)
    (root / "evidence.txt").write_text("different authority\n")
    with pytest.raises(ValueError, match="Planned input changed"):
        package.verify_transition(root, ledger)


@pytest.mark.parametrize("change", ["head", "execution"])
def test_transition_rejects_runtime_drift(staging, monkeypatch, change):
    root, ledger = staged_ledger(staging, monkeypatch)
    if change == "head":
        ledger["runtime_commit"] = "b" * 40
    else:
        ledger["execution_inventory"] = [{"path": "different.py", "sha256": "changed"}]
    with pytest.raises(ValueError, match="Runtime commit changed|Execution inventory changed"):
        package.verify_transition(root, ledger)


def test_nonprivate_output_rejected_before_any_input_read(staging):
    root, source, _, _, _ = staging
    with pytest.raises(ValueError, match="private .temp"):
        package.plan(root, source, "missing.json", "unused", "missing-spec.json", "unused",
                     "artifacts/new-package")
    assert not (root / "artifacts").exists()
    assert not (root / "evidence.txt").exists()


def test_unignored_output_rejected_before_any_input_read(staging, monkeypatch):
    root, source, _, _, _ = staging
    monkeypatch.setattr(package.subprocess, "run", lambda *a, **kw: SimpleNamespace(returncode=1))
    with pytest.raises(ValueError, match="gitignored"):
        package.plan(root, source, "missing.json", "unused", "missing-spec.json", "unused",
                     ".temp/new-package")
    assert not (root / ".temp").exists()


@pytest.mark.parametrize("changes, message", [
    ({"review_id": "bad"}, "Review ID"),
    ({"timestamp": "2026-11-18T01:00:00Z"}, "timestamp differ"),
    ({"package_id": ""}, "package ID"),
    ({"prerequisite_document": ["missing.md"]}, "Missing input"),
])
def test_metadata_rejected_before_staging(tmp_path, changes, message):
    values = {"package_id": "engineering-prerequisites", "review_id": "20261118T000000Z-canary",
              "timestamp": "2026-11-18T00:00:00Z", "prerequisite_document": []}
    values.update(changes)
    with pytest.raises(ValueError, match=message):
        package.metadata_preflight(tmp_path, SimpleNamespace(**values))
    assert not list(tmp_path.iterdir())


def test_plan_distinguishes_runtime_refresh_from_immutable_evidence(staging):
    root, _, _, _, invoke = staging
    _, _, _, actions = invoke()
    assert [a["action"] for a in actions] == [
        "bind_current_runtime", "copy_exact_retained_input", "omit_historical_instructions"]
    assert not (root / "evidence.txt").exists()
    assert not (root / ".temp").exists()


def test_changed_retained_evidence_fails_before_persistence(staging):
    root, source, _, _, invoke = staging
    (source / "evidence.txt").write_text("different evidence\n")
    with pytest.raises(ValueError, match="Retained evidence changed"):
        invoke()
    assert not (root / ".temp").exists()


def test_tracked_authority_cannot_be_refreshed_as_runtime(staging):
    _, _, manifest, _, invoke = staging
    manifest["files"][0]["role"] = "authority"
    with pytest.raises(ValueError, match="Non-runtime tracked evidence changed"):
        invoke()


def test_existing_private_input_is_preserved_even_if_equal(staging):
    root, source, _, _, invoke = staging
    original = (source / "evidence.txt").read_bytes()
    (root / "evidence.txt").write_bytes(original)
    with pytest.raises(ValueError, match="already exists"):
        invoke()
    assert (root / "evidence.txt").read_bytes() == original


@pytest.mark.parametrize("mutation", ["scientific", "resolved"])
def test_scientific_fixture_cannot_be_recycled_as_operational(staging, mutation):
    _, _, _, fixture, invoke = staging
    if mutation == "scientific":
        fixture["review"]["scientific_review"] = True
    else:
        fixture["assessments"][0] = {"category": "SUPPORTED_AS_STATED"}
    with pytest.raises(ValueError, match="Scientific fixture|remain unresolved"):
        invoke()


@pytest.fixture
def retained_bootstrap(preparation, tmp_path, monkeypatch):
    maintained, source, archive = preparation
    receipt = maintained.prepare(source, archive, maintained.CANARY)
    root = tmp_path / "new-reviewer"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    for path in [".gitignore", *maintained.CODE_PATHS, str(maintained.PROTOCOL),
                 str(maintained.COHORT), *[item[0] for item in maintained.PUBLIC.values()]]:
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / path, target)
    manifest = {"cases": [{"case_id": maintained.CANARY,
                            "occurrence_id": receipt["occurrence_id"]}],
                "files": [{**pin, "role": "original_input"}
                          for pin in receipt["artifacts"].values()]}
    receipt_sha = maintained.digest((source / package.BOOTSTRAP_RECEIPT).read_bytes())
    monkeypatch.setattr(package, "bootstrap", maintained)
    return maintained, root, source, archive, manifest, receipt_sha


def test_212_complete_bootstrap_replays_real_checker_and_keeps_original_bytes(retained_bootstrap):
    maintained, root, source, archive, manifest, receipt_sha = retained_bootstrap
    complete = package.complete_bootstrap_manifest(root, source, manifest, receipt_sha)
    assert len(complete["files"]) == 5 and len(manifest["files"]) == 3
    quartet = [pin for pin in complete["files"] if "required_mode" in pin]
    assert len(quartet) == 4 and {pin["required_mode"] for pin in quartet} == {"0600"}
    public = next(pin for pin in complete["files"] if pin["role"] == "bootstrap_public_projection")
    assert public["sha256"] == maintained.PUBLIC["fresh"][1]
    for pin in quartet:
        package.copy_retained(root, source, pin)
        assert (root / pin["path"]).read_bytes() == (source / pin["path"]).read_bytes()
        assert stat.S_IMODE((root / pin["path"]).stat().st_mode) == 0o600
    actual = maintained.check_case(root, archive, maintained.CANARY)
    assert actual == json.loads((source / package.BOOTSTRAP_RECEIPT).read_bytes())
    assert actual["scientific_status"] == "unassessed"
    assert actual["kg_admissions"] == 0
    assert stat.S_IMODE((root / package.BOOTSTRAP_ROOT).stat().st_mode) == 0o700


def test_212_old_incomplete_staging_and_0400_modes_fail_real_checker(retained_bootstrap):
    maintained, root, source, archive, manifest, receipt_sha = retained_bootstrap
    for pin in manifest["files"]:
        package.rounds.write(root, pin["path"], raw=(source / pin["path"]).read_bytes())
    with pytest.raises(Exception, match="missing artifact"):
        maintained.check_case(root, archive, maintained.CANARY)
    package.rounds.write(root, package.BOOTSTRAP_RECEIPT,
                         raw=(source / package.BOOTSTRAP_RECEIPT).read_bytes())
    with pytest.raises(ValueError, match="Private artifact permissions differ"):
        maintained.check_case(root, archive, maintained.CANARY)


@pytest.mark.parametrize("fault", ["receipt_hash", "configuration", "artifact", "public_projection"])
def test_212_bootstrap_binding_drift_fails_before_copy(retained_bootstrap, fault):
    maintained, root, source, archive, manifest, receipt_sha = retained_bootstrap
    if fault == "receipt_hash":
        receipt_sha = "0" * 64
    elif fault == "configuration":
        with (root / maintained.CODE_PATHS[0]).open("a") as stream:
            stream.write("\n# another runtime\n")
    elif fault == "artifact":
        manifest["files"][0]["sha256"] = "0" * 64
    else:
        (root / maintained.PUBLIC["fresh"][0]).write_text("different public projection")
    with pytest.raises(ValueError,
                       match="Source hash changed|configuration differs|artifact differs|projection"):
        package.complete_bootstrap_manifest(root, source, manifest, receipt_sha)
    assert not (root / ".temp").exists()


def test_212_free_bootstrap_gate_invokes_actual_checker_with_clone_python(
        retained_bootstrap, monkeypatch):
    maintained, root, source, archive, manifest, receipt_sha = retained_bootstrap
    complete = package.complete_bootstrap_manifest(root, source, manifest, receipt_sha)
    for pin in complete["files"]:
        if "required_mode" not in pin:
            continue
        package.copy_retained(root, source, pin)
    commands = []

    def validator(name, command, actual_root, environment):
        commands.append(command)
        assert name == "bootstrap-preparation-check" and actual_root == root
        return {"exit_code": 0, "command": command}, maintained.check_case(
            root, archive, maintained.CANARY)

    monkeypatch.setattr(package.worker, "production_validator", validator)
    result = package.check_bootstrap(root)
    assert result["exit_code"] == 0
    assert commands == [[sys.executable, "-B",
                         str(root / "scripts/adhoc/prepare_calibration_20261115.py"),
                         "--check", "fresh-47"]]
    (root / package.BOOTSTRAP_ROOT / "packet.json").chmod(0o400)
    with pytest.raises(ValueError, match="Private artifact permissions differ"):
        package.check_bootstrap(root)
