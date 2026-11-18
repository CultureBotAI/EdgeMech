#!/usr/bin/env python3
"""Provision a fresh reviewer clone; inputs: exact revision/tool paths; output: receipt.

Issue #206, 2026-11-17. This proves setup only, never canonical save or scientific readiness.
Failed destinations remain intact. No credentials, evidence, or old reviews are copied.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import subprocess
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path

ORIGIN = "https://github.com/CultureBotAI/EdgeMech.git"
CLAW_ORIGIN = "https://github.com/CultureBotAI/culturebotai-claw.git"
HELPER = Path(__file__).resolve()
RELATIVE_HELPER = Path("scripts/adhoc") / HELPER.name
RECEIPT = Path(".temp/reviewer-provisioning/receipt.json")
SCHEMA = "edgemech-reviewer-clone-provisioning/v1"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical_name(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def environment(root):
    # Do not inherit credentials or environment redirects from the coordinator.
    child = {key: value for key, value in os.environ.items()
             if key in {"HOME", "PATH", "TMPDIR", "LANG", "LC_ALL", "SYSTEMROOT"}}
    child.update(PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1",
                 UV_PROJECT_ENVIRONMENT=str(root / ".venv"), UV_PYTHON_DOWNLOADS="never",
                 GIT_TERMINAL_PROMPT="0")
    return child


def git(root, *arguments):
    return subprocess.check_output(["git", "-C", str(root), *arguments], text=True,
                                   env=environment(root)).strip()


def inspect_environment(root):
    """Executed by the newly installed clone interpreter, not the coordinator."""
    root = root.resolve()
    require(Path(sys.prefix).resolve() == root / ".venv", "Interpreter is outside clone venv")
    require(sys.prefix != sys.base_prefix, "Interpreter is not a virtual environment")
    config = (root / ".venv/pyvenv.cfg").read_text()
    require(re.search(r"^include-system-site-packages\s*=\s*false\s*$", config,
                      re.MULTILINE | re.IGNORECASE), "Venv includes system packages")
    import edgemech
    from edgemech.pins import check_contracts

    require(Path(edgemech.__file__).resolve().parent == root / "src/edgemech",
            "EdgeMech import does not come from this clone")
    pins = json.loads((root / "src/edgemech/contract-pins.json").read_text())
    shared = importlib.metadata.distribution("kg-microbe-orchestration")
    direct = json.loads(shared.read_text("direct_url.json") or "{}")
    require(direct.get("url") == CLAW_ORIGIN
            and direct.get("vcs_info", {}).get("vcs") == "git"
            and direct.get("vcs_info", {}).get("commit_id") == pins["commit"],
            "Installed CLAW source/commit differs from reviewed contract pin")
    lock = tomllib.loads((root / "uv.lock").read_text())
    locked = {(canonical_name(item["name"]), item["version"]) for item in lock["package"]}
    packages = sorted([{"name": canonical_name(item.metadata["Name"]),
                        "version": item.version,
                        "direct_url": json.loads(item.read_text("direct_url.json") or "null")}
                       for item in importlib.metadata.distributions()], key=lambda item: item["name"])
    require(all((item["name"], item["version"]) in locked for item in packages),
            "Installed distribution version is outside uv.lock")
    contracts = check_contracts()
    require(contracts.get("verified") is True and contracts["claw_commit"] == pins["commit"],
            "Installed contract verification failed")
    return {"host": platform.node(), "platform": platform.platform(),
            "python_executable": sys.executable, "python_prefix": sys.prefix,
            "python_base_prefix": sys.base_prefix, "python_version": platform.python_version(),
            "python_base_executable": sys._base_executable,
            "venv_config_sha256": digest(root / ".venv/pyvenv.cfg"),
            "pyproject_sha256": digest(root / "pyproject.toml"),
            "lock_sha256": digest(root / "uv.lock"), "contracts": contracts,
            "distributions": packages}


def plan(args):
    require(re.fullmatch(r"[0-9a-f]{40}", args.revision) is not None,
            "Revision must be an exact full lowercase 40-character commit")
    root = args.destination.expanduser().absolute()
    require(root.parent.is_dir(), "Destination parent must already exist")
    require(root.parent.resolve() == root.parent, "Destination parent must not traverse symlinks")
    require(not root.exists() and not root.is_symlink(),
            "Destination already exists; preserve it and choose a fresh path")
    for name, path in (("uv", args.uv), ("Python", args.python)):
        require(path.is_absolute() and path.is_file() and os.access(path, os.X_OK),
                f"{name} must name an absolute executable on this machine")
    python = root / ".venv/bin/python"
    return {"schema": SCHEMA, "mode": "plan", "destination": str(root),
            "origin": ORIGIN, "revision": args.revision, "receipt": str(root / RECEIPT),
            "authorizes_reviewer_launch": False, "scientific_gate_passed": False,
            "commands": [
                ["git", "clone", "--no-checkout", "--no-hardlinks", "--origin", "origin",
                 ORIGIN, str(root)],
                ["git", "-C", str(root), "fetch", "--no-tags", "origin", args.revision],
                ["git", "-C", str(root), "checkout", "--detach", args.revision],
                [str(args.uv), "sync", "--locked", "--extra", "dev", "--python", str(args.python),
                 "--no-config"],
                [str(args.uv), "pip", "check", "--python", str(python), "--no-config"],
                [str(python), "-B", str(root / RELATIVE_HELPER), "--inspect-root", str(root)],
            ]}


def run_command(command, root):
    completed = subprocess.run(command, cwd=root if root.exists() else root.parent,
                               env=environment(root), capture_output=True, text=True)
    if completed.returncode:
        raise RuntimeError(f"Command failed ({completed.returncode}): {command[0]} "
                           f"{command[1]}\n{completed.stderr[-4000:]}")
    return completed.stdout


def verify_checkout(root, revision):
    require(git(root, "remote", "get-url", "origin") == ORIGIN, "Clone origin is not canonical")
    require(git(root, "rev-parse", "HEAD") == revision, "Clone HEAD differs from requested commit")
    require(not git(root, "status", "--porcelain", "--untracked-files=no"),
            "Clone has changed tracked files")
    require(digest(root / RELATIVE_HELPER) == digest(HELPER),
            "Requested commit contains a different provisioning helper")


def write_receipt(root, receipt):
    path = root / RECEIPT
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True)
        stream.write("\n")


def provision(args):
    proposed = plan(args)
    if args.plan:
        return proposed
    root = Path(proposed["destination"])
    # Reserve the fresh path atomically; a competing creator must not receive our receipt.
    root.mkdir()
    receipt = {**proposed, "mode": "run", "status": "failed", "steps_completed": 0,
               "started_at": datetime.now(timezone.utc).isoformat(),
               "coordinator_host": platform.node(), "helper_sha256": digest(HELPER),
               "uv_sha256": digest(args.uv), "requested_python": str(args.python),
               "capability": "clone-and-dependency-setup-only",
               "requires": ["frozen evidence package", "same-clone production save/readback",
                            "passing scientific calibration"]}
    try:
        for index, command in enumerate(proposed["commands"]):
            if index == 3:
                verify_checkout(root, args.revision)
                require(not (root / ".venv").exists() and not (root / ".venv").is_symlink(),
                        "Fresh checkout unexpectedly contains a venv")
            output = run_command(command, root)
            receipt["steps_completed"] = index + 1
            if index == len(proposed["commands"]) - 1:
                receipt["environment"] = json.loads(output)
        verify_checkout(root, args.revision)
        require(receipt["environment"]["host"] == receipt["coordinator_host"],
                "Environment probe returned a different host")
        require(Path(receipt["environment"]["python_base_executable"]).resolve()
                == args.python.resolve(), "Venv used a different base interpreter")
        receipt["status"] = "passed"
    except Exception as error:
        receipt["error"] = str(error)
        if root.is_dir() and not root.is_symlink():
            receipt["finished_at"] = datetime.now(timezone.utc).isoformat()
            write_receipt(root, receipt)
        raise
    receipt["finished_at"] = datetime.now(timezone.utc).isoformat()
    write_receipt(root, receipt)
    require(json.loads((root / RECEIPT).read_text()) == receipt, "Receipt failed disk readback")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inspect-root", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--revision")
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--python", type=Path)
    parser.add_argument("--uv", type=Path, default=Path("/Users/marcin/.local/bin/uv"))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--plan", action="store_true")
    mode.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if args.inspect_root:
        result = inspect_environment(args.inspect_root)
    else:
        require(args.revision and args.destination and args.python and (args.plan or args.run),
                "Require --revision, --destination, --python and exactly one of --plan/--run")
        result = provision(args)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
