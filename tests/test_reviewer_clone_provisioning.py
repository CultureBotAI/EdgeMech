"""Issue #206: provisioning preserves failed clones and cannot authorize reviewers."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HELPER = Path(__file__).resolve().parents[1] / "scripts/adhoc/provision_reviewer_clone_20261117.py"


@pytest.fixture
def provisioning(tmp_path):
    spec = importlib.util.spec_from_file_location("provision_reviewer_clone", HELPER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    args = argparse.Namespace(revision="a" * 40, destination=tmp_path / "reviewer",
                              python=Path(sys.executable), uv=Path(sys.executable), plan=True)
    return module, args


def test_plan_does_not_create_clone_or_spawn_process(provisioning, monkeypatch):
    module, args = provisioning
    monkeypatch.setattr(module, "run_command", lambda *_: pytest.fail("Plan spawned a process"))
    result = module.provision(args)
    assert not args.destination.exists()
    assert result["origin"] == module.ORIGIN
    assert result["commands"][0][-2:] == [module.ORIGIN, str(args.destination)]
    assert result["commands"][2][-2:] == ["--detach", args.revision]
    assert "--locked" in result["commands"][3]
    assert not result["authorizes_reviewer_launch"]
    assert not result["scientific_gate_passed"]


@pytest.mark.parametrize("revision", ["main", "abcdef1", "A" * 40, "a" * 39, "a" * 40 + " "])
def test_nonexact_revision_is_rejected(provisioning, revision):
    module, args = provisioning
    args.revision = revision
    with pytest.raises(ValueError, match="exact full"):
        module.plan(args)


@pytest.mark.parametrize("existing", ["directory", "file", "dangling_symlink"])
def test_existing_destination_is_never_reused(provisioning, existing):
    module, args = provisioning
    if existing == "directory":
        args.destination.mkdir()
        (args.destination / "retained.txt").write_text("historical failure")
    elif existing == "file":
        args.destination.write_text("historical failure")
    else:
        args.destination.symlink_to(args.destination.parent / "absent")
    with pytest.raises(ValueError, match="already exists"):
        module.provision(args)
    assert os.path.lexists(args.destination)


def test_environment_cannot_redirect_venv_or_inherit_credentials(provisioning, monkeypatch):
    module, args = provisioning
    monkeypatch.setenv("UV_PROJECT_ENVIRONMENT", "/outside/retained-venv")
    monkeypatch.setenv("VIRTUAL_ENV", "/outside/retained-venv")
    monkeypatch.setenv("PYTHONPATH", "/outside/python")
    monkeypatch.setenv("CBORG_API_KEY", "test-only-placeholder")
    child = module.environment(args.destination)
    assert child["UV_PROJECT_ENVIRONMENT"] == str(args.destination / ".venv")
    assert child["UV_PYTHON_DOWNLOADS"] == "never"
    assert not {"VIRTUAL_ENV", "PYTHONPATH", "CBORG_API_KEY"} & child.keys()


@pytest.fixture
def actual_checkout(provisioning, monkeypatch):
    module, args = provisioning
    source = args.destination.parent / "source"
    source.mkdir()
    subprocess.run(["git", "init", str(source)], check=True, capture_output=True)
    helper = source / module.RELATIVE_HELPER
    helper.parent.mkdir(parents=True)
    helper.write_bytes(HELPER.read_bytes())
    (source / ".gitignore").write_text(".temp/\n.venv/\n")
    subprocess.run(["git", "-C", str(source), "add", "."], check=True)
    subprocess.run(["git", "-C", str(source), "-c", "user.name=Fixture",
                    "-c", "user.email=fixture@example.invalid", "commit", "-m", "Fixture"],
                   check=True, capture_output=True)
    args.revision = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"],
                                            text=True).strip()
    args.plan = False
    controls = {"bad_origin": False, "bad_helper": False, "install_failure": False,
                "wrong_host": False, "calls": []}

    def run(command, root):
        controls["calls"].append(command)
        if command[1] == "clone":
            subprocess.run(["git", "clone", "--no-hardlinks", str(source), str(root)],
                           check=True, capture_output=True)
            subprocess.run(["git", "-C", str(root), "remote", "set-url", "origin",
                            "https://github.com/other/repository.git" if controls["bad_origin"]
                            else module.ORIGIN], check=True)
            if controls["bad_helper"]:
                (root / module.RELATIVE_HELPER).write_text("modified helper\n")
        elif "checkout" in command:
            subprocess.run(command, check=True, capture_output=True)
        elif command[1] == "sync":
            (root / ".venv").mkdir()
            (root / ".venv/retained-partial-install").write_text("retain after failure")
            if controls["install_failure"]:
                raise RuntimeError("simulated install failure")
        elif "--inspect-root" in command:
            return json.dumps({"host": "wrong-host" if controls["wrong_host"]
                               else module.platform.node(),
                               "python_base_executable": str(args.python)})
        return ""

    monkeypatch.setattr(module, "run_command", run)
    return module, args, controls


def test_success_receipt_is_persisted_and_non_authorizing(actual_checkout):
    module, args, controls = actual_checkout
    receipt = module.provision(args)
    assert json.loads((args.destination / module.RECEIPT).read_text()) == receipt
    assert receipt["status"] == "passed"
    assert receipt["steps_completed"] == 6
    assert receipt["capability"] == "clone-and-dependency-setup-only"
    assert not receipt["authorizes_reviewer_launch"]
    assert not receipt["scientific_gate_passed"]
    assert module.git(args.destination, "rev-parse", "HEAD") == args.revision
    assert any(command[1:3] == ["pip", "check"] for command in controls["calls"])


@pytest.mark.parametrize("fault", ["bad_origin", "bad_helper"])
def test_invalid_checkout_cannot_install_or_pass(actual_checkout, fault):
    module, args, controls = actual_checkout
    controls[fault] = True
    with pytest.raises(ValueError):
        module.provision(args)
    assert not any(command[1] == "sync" for command in controls["calls"])
    receipt = json.loads((args.destination / module.RECEIPT).read_text())
    assert receipt["status"] == "failed"
    assert args.destination.is_dir()


def test_failed_install_preserves_artifacts_and_refuses_retry(actual_checkout):
    module, args, controls = actual_checkout
    controls["install_failure"] = True
    with pytest.raises(RuntimeError, match="simulated install failure"):
        module.provision(args)
    path = args.destination / module.RECEIPT
    retained = path.read_bytes()
    assert json.loads(retained)["status"] == "failed"
    assert (args.destination / ".venv/retained-partial-install").read_text()
    with pytest.raises(ValueError, match="already exists"):
        module.provision(args)
    assert path.read_bytes() == retained


def test_wrong_host_probe_cannot_pass(actual_checkout):
    module, args, controls = actual_checkout
    controls["wrong_host"] = True
    with pytest.raises(ValueError, match="different host"):
        module.provision(args)
    assert json.loads((args.destination / module.RECEIPT).read_text())["status"] == "failed"


def test_probe_rejects_coordinator_interpreter(provisioning):
    module, args = provisioning
    with pytest.raises(ValueError, match="outside clone venv"):
        module.inspect_environment(args.destination)


def test_probe_rejects_system_packages(provisioning, monkeypatch):
    module, args = provisioning
    venv = args.destination / ".venv"
    venv.mkdir(parents=True)
    (venv / "pyvenv.cfg").write_text("include-system-site-packages = true\n")
    monkeypatch.setattr(module.sys, "prefix", str(venv))
    monkeypatch.setattr(module.sys, "base_prefix", "/system-python")
    with pytest.raises(ValueError, match="includes system packages"):
        module.inspect_environment(args.destination)


def test_symlink_parent_is_rejected(provisioning):
    module, args = provisioning
    alias = args.destination.parent / "alias"
    alias.symlink_to(args.destination.parent, target_is_directory=True)
    args.destination = alias / "reviewer"
    with pytest.raises(ValueError, match="traverse symlinks"):
        module.plan(args)
