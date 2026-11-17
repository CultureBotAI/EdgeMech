"""A worker exit code alone cannot authorize fan-out or overwrite retained runs."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import stat
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
from kg_microbe_governance.artifacts.scripts.record_review import repository_identity
from test_occurrence_review import case as case

HELPER = Path(__file__).resolve().parents[1] / "scripts/adhoc/run_m5_review_worker_20261116.py"


@pytest.fixture
def worker(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("m5_worker", HELPER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    root = tmp_path.resolve()
    codex = root / "codex"
    codex.write_bytes(b"\x7fELFfixture-native-executable")
    codex.chmod(0o700)
    prompt = root / "prompt.md"
    prompt.write_text("Run one bounded canary and persist the required proof.\n")
    args = argparse.Namespace(plan=False, run=True, prompt=prompt, output_root=root / "canary",
                              codex=codex, workdir=root, role="canary", canary_receipt=None,
                              add_dir=[])
    (root / "uv.lock").write_text("fixture locked runtime\n")
    case = root / module.FRESH47
    case.mkdir(parents=True)
    (case / "packet.json").write_text(json.dumps({"occurrence_id": "frozen-fresh47"}))
    (case / "receipt.json").write_text(json.dumps(
        {"occurrence_id": "frozen-fresh47", "case_id": "fresh-47"}))
    cohort = root / "artifacts/edge-calibration-20261115/cohort.json"
    cohort.parent.mkdir(parents=True)
    cohort.write_text(json.dumps({"cases": [
        {"occurrence_id": "frozen-fresh47", "case_id": "fresh-47"}]}))
    controls = {"exit_code": 0, "artifact": None, "corrupt": False, "calls": 0,
                "validator_exit": 0, "validator_commands": [], "arbitrary_only": False,
                "identity": module.REPOSITORY, "origin": "https://github.com/CultureBotAI/EdgeMech.git"}
    monkeypatch.setattr(module, "repository_identity", lambda root: controls["identity"])
    monkeypatch.setattr(module, "load_cborg", lambda environment: None)
    monkeypatch.setenv("CBORG_API_KEY", "fixture-key-not-a-real-credential")
    monkeypatch.setattr(module.importlib.metadata, "distributions", lambda: [])

    def validator(command, **kwargs):
        controls["validator_commands"].append(command)
        return subprocess.CompletedProcess(command, controls["validator_exit"], b"verified\n", b"")

    class Process:
        def __init__(self, command, *, stdin, stdout, stderr, cwd, env):
            controls["calls"] += 1
            controls["command"] = command
            self.pid = 12345
            self.returncode = controls["exit_code"]
            self.output = Path(env["EDGEMECH_WORKER_OUTPUT_ROOT"])
            stdout.write(b'{"type":"thread.started"}\n')

        def communicate(self, prompt_bytes):
            (self.output / "final.md").write_text("Canary finished.\n")
            artifacts = []
            for name in (("arbitrary.txt",) if controls["arbitrary_only"] else
                         ("packet.json", "receipt.json")):
                evidence = self.output / name
                if controls["arbitrary_only"]:
                    evidence.write_text("not a replayed packet")
                elif name == "packet.json" and controls["artifact"] is not None:
                    evidence.write_text(controls["artifact"])
                else:
                    evidence.write_bytes((case / name).read_bytes())
                artifacts.append({"path": str(evidence),
                                  "sha256": "0" * 64 if controls["corrupt"]
                                  else module.digest(evidence)})
            result = {
                "status": "passed",
                "checks": [{"name": name, "passed": True} for name in sorted(module.CHECKS)],
                "artifacts": artifacts,
            }
            (self.output / "canary-result.json").write_text(json.dumps(result))

    # Keep the shared CLAW helper's subprocess module real: its Git and bundle
    # validation must remain independently exercisable by production tests.
    monkeypatch.setattr(module, "subprocess", SimpleNamespace(
        run=validator, Popen=Process, PIPE=subprocess.PIPE,
        SubprocessError=subprocess.SubprocessError,
        check_output=lambda command, **kw: ("" if "status" in command else
            controls["origin"] + "\n" if "remote" in command else "a" * 40 + "\n")))
    return module, args, controls


def test_plan_is_read_only_and_does_not_load_credentials_or_start_worker(worker, monkeypatch):
    module, args, controls = worker
    args.plan = True
    monkeypatch.setattr(module, "load_cborg", lambda env: pytest.fail("plan read credentials"))
    assert module.launch(args) == 0
    assert controls["calls"] == 0
    assert not args.output_root.exists()


def test_successful_canary_persists_replayable_private_receipt_and_no_model_override(worker):
    module, args, controls = worker
    assert module.launch(args) == 0
    output = args.output_root
    state = json.loads((output / "metadata.json").read_text())
    assert state["status"] == "passed" and state["exit_code"] == 0
    assert state["worker_pid"] == 12345
    assert "fixture-key" not in (output / "metadata.json").read_text()
    assert module.verify_receipt(output / "canary-receipt.json", state, args.workdir,
                                 module.child_environment(args.workdir))["sha256"]
    assert len(controls["validator_commands"]) == 4
    assert stat.S_IMODE(output.stat().st_mode) == 0o700
    for name in ("metadata.json", "canary-receipt.json", "events.jsonl", "stderr.log", "final.md"):
        assert stat.S_IMODE((output / name).stat().st_mode) == 0o600
    assert "--approve-for-me" in controls["command"]
    assert "--sandbox" not in controls["command"]  # conflicts with --approve-for-me
    assert "--model" not in controls["command"] and "-m" not in controls["command"]
    with pytest.raises(ValueError, match="already exists"):
        module.launch(args)
    assert controls["calls"] == 1


@pytest.mark.parametrize("control,value,error", [
    ("exit_code", 9, "exited with code 9"),
    ("artifact", "", "empty canary artifact"),
    ("corrupt", True, "hash mismatch"),
])
def test_nonzero_exit_or_invalid_artifact_never_creates_passing_receipt(worker, control, value, error):
    module, args, controls = worker
    controls[control] = value
    with pytest.raises(ValueError, match=error):
        module.launch(args)
    assert not (args.output_root / "canary-receipt.json").exists()
    assert json.loads((args.output_root / "metadata.json").read_text())["status"] == "failed"


@pytest.mark.parametrize("key", ["git_head", "helper_sha256", "codex_path", "codex_sha256",
                                 "host", "python_executable", "python_prefix", "python_version",
                                 "lock_sha256", "distributions_sha256", "environment_sha256",
                                 "repository_identity", "repository_origin"])
def test_incompatible_runtime_cannot_reuse_canary(worker, key):
    module, args, controls = worker
    module.launch(args)
    bindings = json.loads((args.output_root / "metadata.json").read_text())
    bindings[key] = "different"
    with pytest.raises(ValueError, match="runtime changed"):
        module.verify_receipt(args.output_root / "canary-receipt.json", bindings, args.workdir,
                              module.child_environment(args.workdir))


def test_changed_artifact_blocks_follow_on_launch_before_process_or_output(worker):
    module, args, controls = worker
    module.launch(args)
    args.canary_receipt = args.output_root / "canary-receipt.json"
    (args.output_root / "packet.json").write_text("altered evidence")
    args.output_root = args.workdir / "calibration"
    args.role = "calibration"
    with pytest.raises(ValueError, match="hash mismatch"):
        module.launch(args)
    assert controls["calls"] == 1 and not args.output_root.exists()


def test_no_receipt_blocks_follow_on_launch(worker):
    module, args, controls = worker
    args.role = "release"
    with pytest.raises(ValueError, match="passing canary receipt is required"):
        module.launch(args)
    assert controls["calls"] == 0 and not args.output_root.exists()


def test_canary_that_changes_tracked_runtime_cannot_authorize_follow_on_work(worker, monkeypatch):
    module, args, controls = worker

    def git_state(command, **kwargs):
        if "status" in command:
            return " M src/edgemech/occurrence_review.py\n" if controls["calls"] else ""
        return "a" * 40 + "\n"

    monkeypatch.setattr(module.subprocess, "check_output", git_state)
    with pytest.raises(ValueError, match="changed tracked runtime"):
        module.launch(args)
    assert not (args.output_root / "canary-receipt.json").exists()


def test_missing_required_check_invalidates_canary_receipt(worker):
    module, args, controls = worker
    module.launch(args)
    path = args.output_root / "canary-result.json"
    result = json.loads(path.read_text())
    result["checks"] = result["checks"][:-1]
    path.write_text(json.dumps(result))
    with pytest.raises(ValueError, match="mandatory canary checks"):
        module.validate_canary_result(args.output_root)


def test_hash_valid_arbitrary_artifact_does_not_substitute_for_packet_replay(worker):
    module, args, controls = worker
    controls["arbitrary_only"] = True
    with pytest.raises(ValueError, match="Missing or empty canary artifact"):
        module.launch(args)
    assert not (args.output_root / "canary-receipt.json").exists()


def test_wrong_case_even_when_copy_matches_source_is_rejected(worker):
    module, args, controls = worker
    packet = args.workdir / module.FRESH47 / "packet.json"
    packet.write_text(json.dumps({"occurrence_id": "another-case"}))
    with pytest.raises(ValueError, match="not the frozen fresh-47 occurrence"):
        module.launch(args)
    assert not controls["validator_commands"]


def test_parent_validator_failure_overrides_success_claim(worker):
    module, args, controls = worker
    controls["validator_exit"] = 1
    with pytest.raises(ValueError, match="Independent validator failed"):
        module.launch(args)
    assert not (args.output_root / "canary-receipt.json").exists()
    assert json.loads((args.output_root / "validator-results.json").read_text())[0]["exit_code"] == 1


def test_follow_on_reexecutes_validator_and_refuses_new_failure(worker):
    module, args, controls = worker
    module.launch(args)
    args.canary_receipt = args.output_root / "canary-receipt.json"
    args.output_root = args.workdir / "calibration"
    args.role = "calibration"
    controls["validator_exit"] = 1
    with pytest.raises(ValueError, match="Independent validator failed"):
        module.launch(args)
    assert controls["calls"] == 1 and not args.output_root.exists()


@pytest.mark.parametrize("changed", ["host", "python", "environment"])
def test_actual_runtime_change_blocks_follow_on_worker(worker, monkeypatch, changed):
    module, args, controls = worker
    module.launch(args)
    args.canary_receipt = args.output_root / "canary-receipt.json"
    args.output_root = args.workdir / "calibration"
    args.role = "calibration"
    if changed == "host":
        monkeypatch.setattr(module.socket, "gethostname", lambda: "different-host")
    elif changed == "python":
        monkeypatch.setattr(module.sys, "version", "different-python-runtime")
    else:
        monkeypatch.setenv("PATH", "/different/runtime/path")
    with pytest.raises(ValueError, match="Canary runtime changed"):
        module.launch(args)
    assert controls["calls"] == 1 and not args.output_root.exists()


def test_codex_wrapper_is_not_a_native_runtime_binding(worker):
    module, args, controls = worker
    args.codex.write_text("#!/usr/bin/env node\n// wrapper\n")
    with pytest.raises(ValueError, match="native Codex executable"):
        module.launch(args)
    assert controls["calls"] == 0


def test_same_selected_venv_can_run_in_another_same_head_worktree(worker, monkeypatch):
    module, args, controls = worker
    monkeypatch.setattr(module.sys, "prefix", str(args.workdir / ".venv"))
    module.launch(args)
    args.canary_receipt = args.output_root / "canary-receipt.json"
    original = args.workdir
    args.workdir = original / "coordinator"
    args.workdir.mkdir()
    shutil.copyfile(original / "uv.lock", args.workdir / "uv.lock")
    shutil.copytree(original / "artifacts", args.workdir / "artifacts")
    shutil.copytree(original / ".temp", args.workdir / ".temp")
    args.output_root = args.workdir / "run"
    args.role = "calibration"
    assert module.launch(args) == 0
    assert controls["calls"] == 2


@pytest.mark.parametrize("origin,accepted", [
    ("https://github.com/CultureBotAI/EdgeMech.git", True),
    ("git@github.com:CultureBotAI/EdgeMech.git", True),
    ("/some/local/coordinator", False),
    ("https://github.com/CultureBotAI/OtherMech.git", False),
])
def test_176_real_shared_origin_parser_precedes_child_and_output(worker, monkeypatch, origin, accepted):
    module, args, controls = worker
    subprocess.run(["git", "init", "-q", str(args.workdir)], check=True)
    subprocess.run(["git", "-C", str(args.workdir), "remote", "add", "origin", origin], check=True)
    subprocess.run(["git", "-C", str(args.workdir), "-c", "user.name=Fixture",
                    "-c", "user.email=fixture@example.invalid", "commit", "--allow-empty", "-qm", "Fixture"],
                   check=True)
    monkeypatch.setattr(module, "repository_identity", repository_identity)
    monkeypatch.setattr(module.subprocess, "check_output", subprocess.check_output)
    args.plan = True
    if accepted:
        assert module.launch(args) == 0
        assert module.repository_bindings(args.workdir)["repository_identity"] == module.REPOSITORY
    else:
        with pytest.raises(ValueError, match="origin"):
            module.launch(args)
    assert controls["calls"] == 0 and not args.output_root.exists()


def test_176_origin_changed_after_canary_blocks_child(worker):
    module, args, controls = worker
    module.launch(args)
    args.canary_receipt = args.output_root / "canary-receipt.json"
    args.output_root = args.workdir / "coordinator"
    args.role = "calibration"
    controls["origin"] = "git@github.com:CultureBotAI/EdgeMech.git"
    with pytest.raises(ValueError, match="runtime changed: repository_origin"):
        module.launch(args)
    assert controls["calls"] == 1 and not args.output_root.exists()


def test_176_legacy_receipt_is_preserved_and_cannot_authorize_new_runtime(worker):
    module, args, controls = worker
    module.launch(args)
    receipt = args.output_root / "canary-receipt.json"
    old = json.loads(receipt.read_text())
    old["schema"] = "edgemech-m5-worker/v2"
    receipt.write_text(json.dumps(old))
    before = receipt.read_bytes()
    args.canary_receipt = receipt
    args.output_root = args.workdir / "coordinator"
    args.role = "calibration"
    with pytest.raises(ValueError, match="not a passing worker receipt"):
        module.launch(args)
    assert receipt.read_bytes() == before
    assert controls["calls"] == 1 and not args.output_root.exists()


@pytest.fixture
def production_worker(worker, case, monkeypatch):
    module, args, controls = worker
    root, review, _ = case
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "remote", "add", "origin",
                    "https://github.com/CultureBotAI/EdgeMech.git"], check=True)
    subprocess.run(["git", "-C", str(root), "-c", "user.name=Fixture",
                    "-c", "user.email=fixture@example.invalid", "commit", "--allow-empty", "-qm", "Fixture"],
                   check=True)
    review["source"]["git_revision"] = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    (root / "review.json").write_text(json.dumps(review))
    (root / "manifest.json").write_text(json.dumps({"cases": [{"packet_path": "packet.json"}]}))
    shutil.copytree(HELPER.parents[2] / "src", root / "src", ignore=shutil.ignore_patterns("__pycache__"))
    args.production_review = "review.json"
    args.production_packet = "packet.json"
    args.production_proofs = "proofs.json"
    args.package_manifest = "manifest.json"
    controls.update(production_commands=[], package_failure=False, save_failure=False)
    bootstrap_validator = module.subprocess.run

    def production_validator(command, **kwargs):
        if "edgemech.occurrence_review" in command:
            controls["production_commands"].append(command)
            if controls["save_failure"] and "save" in command:
                return subprocess.CompletedProcess(command, 1, b"", b"fixture save failure")
            return subprocess.run(command, **kwargs)
        if any(str(arg).endswith("calibration_round_20261116.py") for arg in command):
            controls["production_commands"].append(command)
            result = {"manifest_sha256": module.digest(root / "manifest.json")}
            return subprocess.CompletedProcess(command, int(controls["package_failure"]),
                                               json.dumps(result).encode(), b"")
        return bootstrap_validator(command, **kwargs)

    monkeypatch.setattr(module.subprocess, "run", production_validator)
    monkeypatch.setattr(module.subprocess, "check_output", subprocess.check_output)
    monkeypatch.setattr(module, "repository_identity", repository_identity)
    return module, args, controls


def reviewer_args(args):
    args.canary_receipt = args.output_root / "canary-receipt.json"
    args.output_root = args.workdir / "reviewer"
    args.role = "reviewer"
    args.production_review = args.production_packet = args.production_proofs = None


def test_176_parent_runs_real_save_check_and_reviewer_replays_same_clone(production_worker):
    module, args, controls = production_worker
    assert module.launch(args) == 0
    receipt = json.loads((args.output_root / "canary-receipt.json").read_text())
    assert receipt["scope"] == module.PRODUCTION_SCOPE
    production = receipt["production"]
    assert production["spec"]["workdir"] == str(args.workdir)
    pair = production["outputs"]
    assert (args.workdir / pair["review"]["path"]).stat().st_size > 0
    assert (args.workdir / pair["markdown"]["path"]).stat().st_size > 0
    assert [record["name"] for record in production["validators"]] == [
        "production-package", "production-save", "production-check"]
    assert sum("save" in command for command in controls["production_commands"]) == 1
    reviewer_args(args)
    assert module.launch(args) == 0
    assert controls["calls"] == 2
    assert sum("save" in command for command in controls["production_commands"]) == 1
    assert sum("check" in command for command in controls["production_commands"]) == 3
    state = json.loads((args.output_root / "metadata.json").read_text())
    assert state["status"] == "completed"
    assert state["ending_replay"]["production_replay"]["outputs"] == pair


def test_176_production_plan_validates_without_saving_or_starting_child(production_worker):
    module, args, controls = production_worker
    args.plan = True
    assert module.launch(args) == 0
    assert controls["calls"] == 0 and not args.output_root.exists()
    assert not any("save" in command for command in controls["production_commands"])


def test_176_existing_pair_cannot_pass_as_new_production_canary(production_worker):
    module, args, controls = production_worker
    target = args.workdir / module.REPORT_ROOT / "20000101T000000Z-fixture"
    target.mkdir(parents=True)
    with pytest.raises(ValueError, match="target already exists"):
        module.launch(args)
    assert controls["calls"] == 0 and not args.output_root.exists()


def test_176_invalid_authored_proof_blocks_before_child(production_worker):
    module, args, controls = production_worker
    (args.workdir / "proofs.json").write_text("{}")
    with pytest.raises(ValueError, match="production-input"):
        module.launch(args)
    assert controls["calls"] == 0 and not args.output_root.exists()


def test_176_production_packet_must_be_in_current_frozen_cohort(production_worker):
    module, args, controls = production_worker
    (args.workdir / "manifest.json").write_text(json.dumps({"cases": [{"packet_path": "other.json"}]}))
    with pytest.raises(ValueError, match="outside the frozen cohort"):
        module.launch(args)
    assert controls["calls"] == 0 and not args.output_root.exists()


@pytest.mark.parametrize("changed", ["origin", "authored_input", "canonical_target"])
def test_176_child_mutation_cannot_certify_production_save(production_worker, monkeypatch, changed):
    module, args, controls = production_worker
    communicate = module.subprocess.Popen.communicate

    def mutate(process, prompt_bytes):
        communicate(process, prompt_bytes)
        if changed == "origin":
            subprocess.run(["git", "-C", str(args.workdir), "remote", "set-url", "origin",
                            "git@github.com:CultureBotAI/EdgeMech.git"], check=True)
        elif changed == "authored_input":
            path = args.workdir / "review.json"
            path.write_text(path.read_text() + "\n")
        else:
            (args.workdir / module.REPORT_ROOT / "20000101T000000Z-fixture").mkdir(parents=True)

    monkeypatch.setattr(module.subprocess.Popen, "communicate", mutate)
    with pytest.raises(ValueError):
        module.launch(args)
    assert not (args.output_root / "canary-receipt.json").exists()
    assert not any("save" in command for command in controls["production_commands"])


def test_176_actual_save_failure_never_creates_production_receipt(production_worker):
    module, args, controls = production_worker
    controls["save_failure"] = True
    with pytest.raises(ValueError, match="production-save"):
        module.launch(args)
    assert not (args.output_root / "canary-receipt.json").exists()
    assert json.loads((args.output_root / "metadata.json").read_text())["status"] == "failed"


def test_176_preparation_receipt_never_authorizes_reviewer(worker):
    module, args, controls = worker
    module.launch(args)
    reviewer_args(args)
    args.package_manifest = "manifest.json"
    with pytest.raises(ValueError, match="wrong capability scope"):
        module.launch(args)
    assert controls["calls"] == 1 and not args.output_root.exists()


@pytest.mark.parametrize("changed", ["review", "proofs", "packet", "package", "source", "output", "pins"])
def test_176_changed_production_inputs_outputs_or_package_pins_block_reviewer(production_worker, changed):
    module, args, controls = production_worker
    module.launch(args)
    reviewer_args(args)
    if changed == "pins":
        # The manifest itself is unchanged; the existing round verifier reports
        # a changed referenced input. A manifest-hash-only guard would miss this.
        controls["package_failure"] = True
    elif changed == "output":
        target = args.workdir / module.REPORT_ROOT / "20000101T000000Z-fixture/review.md"
        target.write_text("changed saved rendering")
    else:
        filename = {"review": "review.json", "proofs": "proofs.json", "packet": "packet.json",
                    "package": "manifest.json", "source": "source.json"}[changed]
        target = args.workdir / filename
        target.write_text(target.read_text() + "\n")
    with pytest.raises(ValueError):
        module.launch(args)
    assert controls["calls"] == 1 and not args.output_root.exists()


def test_176_production_receipt_cannot_move_to_another_same_head_clone(production_worker):
    module, args, controls = production_worker
    module.launch(args)
    reviewer_args(args)
    original = args.workdir
    other = original.parent / "other-clone"
    shutil.copytree(original, other)
    args.workdir = other
    args.output_root = other / "reviewer"
    with pytest.raises(ValueError, match="another clone"):
        module.launch(args)
    assert controls["calls"] == 1 and not args.output_root.exists()


@pytest.mark.parametrize("changed", ["origin", "package", "source", "head", "tracked_runtime", "hidden_helper"])
def test_187_reviewer_drift_fails_at_exit_and_preserves_outputs(production_worker, monkeypatch, changed):
    module, args, controls = production_worker
    root = args.workdir
    marker = root / "src/immutable_fixture.py"
    marker.write_text("# pre-reviewed fixture helper\n")
    (root / ".gitignore").write_text("scripts/.private/\n")
    subprocess.run(["git", "-C", str(root), "add", "src/immutable_fixture.py"], check=True)
    subprocess.run(["git", "-C", str(root), "-c", "user.name=Fixture",
                    "-c", "user.email=fixture@example.invalid", "commit", "-qm", "Freeze helper"], check=True)
    review = json.loads((root / "review.json").read_text())
    review["source"]["git_revision"] = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    (root / "review.json").write_text(json.dumps(review))
    assert module.launch(args) == 0
    reviewer_args(args)
    communicate = module.subprocess.Popen.communicate

    def mutate(process, prompt_bytes):
        communicate(process, prompt_bytes)
        if changed == "origin":
            subprocess.run(["git", "-C", str(root), "remote", "set-url", "origin",
                            "git@github.com:CultureBotAI/EdgeMech.git"], check=True)
        elif changed in {"package", "source"}:
            target = root / ("manifest.json" if changed == "package" else "source.json")
            target.write_text(target.read_text() + "\n")
        elif changed == "head":
            subprocess.run(["git", "-C", str(root), "-c", "user.name=Fixture",
                            "-c", "user.email=fixture@example.invalid", "commit", "--allow-empty",
                            "-qm", "Unapproved reviewer change"], check=True)
        elif changed == "tracked_runtime":
            marker.write_text("# changed runtime\n")
        else:
            target = root / "scripts/.private/new_helper.py"
            target.parent.mkdir(parents=True)
            target.write_text("# new ignored helper after freeze\n")

    monkeypatch.setattr(module.subprocess.Popen, "communicate", mutate)
    with pytest.raises(ValueError):
        module.launch(args)
    state = json.loads((args.output_root / "metadata.json").read_text())
    assert state["status"] == "failed" and state["exit_code"] == 0
    assert state["error"]
    assert (args.output_root / "events.jsonl").stat().st_size > 0
    assert (args.output_root / "final.md").stat().st_size > 0
    assert controls["calls"] == 2


def test_187_execution_inventory_includes_ignored_hidden_code_but_allows_new_data(worker):
    module, args, _ = worker
    root = args.workdir
    helper = root / "scripts/.private/helper.py"
    helper.parent.mkdir(parents=True)
    helper.write_text("# ignored helper\n")
    (root / ".gitignore").write_text("scripts/.private/\n")
    before = module.execution_inventory(root)
    assert [pin["path"] for pin in before] == ["scripts/.private/helper.py"]
    (helper.parent / "proof.json").write_text('{"proof":"new data"}')
    assert module.execution_inventory(root) == before
    helper.write_text("# changed ignored helper\n")
    assert module.execution_inventory(root) != before
