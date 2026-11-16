#!/usr/bin/env python3
"""Launch one durable M5 review worker; inputs are a prompt and a pinned canary.

Outputs: private events, stderr, final response, metadata and verified canary receipt.
Serves the user-authorized M5 calibration/release work of 2026-11-16. Never fans out,
selects a model, sends messages, copies credentials, or changes review thresholds.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import shutil
import socket
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HELPER = Path(__file__).resolve()
CHECKS = {"runtime_contracts", "fresh47_packet_replay", "credential_available"}
SCHEMA = "edgemech-m5-worker/v1"


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path, value):
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex)
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def child_environment():
    environment = os.environ.copy()
    prefixes = [Path.home() / ".local/bin",
                Path.home() / ".nvm/versions/node/v22.16.0/bin", Path("/opt/homebrew/bin")]
    environment["PATH"] = os.pathsep.join(map(str, prefixes)) + os.pathsep + environment.get(
        "PATH", os.defpath)
    return environment


def load_cborg(environment):
    """Read only the named key, without evaluating shell code or reporting its value."""
    if environment.get("CBORG_API_KEY"):
        return
    path = Path.home() / ".config/cborg.env"
    if not path.is_file():
        return
    for line in path.read_text().splitlines():
        stripped = line.strip().removeprefix("export ")
        if not stripped.startswith("CBORG_API_KEY="):
            continue
        try:
            values = shlex.split(stripped.split("=", 1)[1], comments=True)
        except ValueError:
            raise ValueError("Invalid CBORG key assignment") from None
        require(len(values) == 1 and bool(values[0]), "Invalid CBORG key assignment")
        environment["CBORG_API_KEY"] = values[0]
        return


def checked_file(path, root):
    require(isinstance(path, (str, Path)), "Invalid canary artifact path")
    path = Path(path)
    require(path.is_absolute(), "Canary artifact must have an absolute path")
    require(path.is_relative_to(root), "Canary artifact is outside its output root")
    require(not any(part.is_symlink() for part in (path, *path.parents)),
            "Canary artifact path contains a symlink")
    require(path.resolve().is_relative_to(root), "Canary artifact escapes its output root")
    require(path.is_file() and path.stat().st_size > 0, "Missing or empty canary artifact")
    return path


def validate_canary_result(output):
    result_path = checked_file(output / "canary-result.json", output)
    result = json.loads(result_path.read_text())
    require(isinstance(result, dict), "Invalid canary result")
    require(result.get("status") == "passed", "Canary did not pass")
    checks = result.get("checks", [])
    require(isinstance(checks, list) and checks, "Missing canary checks")
    require(all(isinstance(check, dict) and check.get("passed") is True for check in checks),
            "A canary check did not pass")
    names = [check.get("name") for check in checks]
    require(all(isinstance(name, str) for name in names), "Invalid canary check name")
    require(len(set(names)) == len(names) and CHECKS.issubset(names),
            "Missing or repeated mandatory canary checks")
    artifacts = result.get("artifacts", [])
    require(isinstance(artifacts, list) and artifacts, "Missing canary artifacts")
    paths = []
    for artifact in artifacts:
        require(isinstance(artifact, dict), "Invalid canary artifact")
        path = checked_file(artifact.get("path", ""), output)
        require(path != result_path, "Canary result cannot be its own evidence")
        require(digest(path) == artifact.get("sha256"), "Canary artifact hash mismatch")
        paths.append(str(path))
    require(len(set(paths)) == len(paths), "Repeated canary artifact")
    return result


def verify_receipt(path, bindings):
    path = Path(path).absolute()
    checked_file(path, path.parent)
    receipt = json.loads(path.read_text())
    require(isinstance(receipt, dict), "Invalid canary receipt")
    require(receipt.get("schema") == SCHEMA and receipt.get("status") == "passed",
            "Canary receipt is not a passing worker receipt")
    for key in ("git_head", "helper_sha256", "codex_path", "codex_sha256"):
        require(receipt.get(key) == bindings[key], f"Canary runtime changed: {key}")
    metadata = checked_file(path.parent / "metadata.json", path.parent)
    require(digest(metadata) == receipt.get("metadata_sha256"), "Canary metadata changed")
    state = json.loads(metadata.read_text())
    require(isinstance(state, dict), "Invalid canary metadata")
    require(all(state.get(key) == bindings[key] for key in
                ("git_head", "helper_sha256", "codex_path", "codex_sha256")),
            "Canary metadata runtime differs from receipt")
    require(state.get("role") == "canary" and state.get("status") == "passed"
            and state.get("exit_code") == 0, "Canary process did not complete successfully")
    result = validate_canary_result(path.parent)
    require(digest(path.parent / "canary-result.json") == receipt.get("result_sha256"),
            "Canary result changed")
    require(state.get("prompt_sha256") == receipt.get("prompt_sha256"),
            "Canary prompt binding changed")
    require(state.get("executed_prompt_sha256") == receipt.get("executed_prompt_sha256"),
            "Canary executed prompt binding changed")
    require(result == receipt.get("result"), "Canary receipt/result differ")
    return {"path": str(path), "sha256": digest(path)}


def launch(args):
    environment = child_environment()
    codex = Path(args.codex or shutil.which("codex", path=environment["PATH"]) or "")
    require(codex.is_file() and os.access(codex, os.X_OK), "Codex executable unavailable")
    codex = codex.resolve()
    root = Path(args.workdir).resolve()
    head = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"],
                                   text=True).strip()
    require(not subprocess.check_output(
        ["git", "-C", str(root), "status", "--porcelain", "--untracked-files=no"],
        text=True).strip(), "Tracked worktree changes require a committed runtime before launch")
    prompt = Path(args.prompt).resolve()
    require(prompt.is_file() and prompt.stat().st_size > 0, "Missing or empty prompt")
    prompt_bytes = prompt.read_bytes()
    output = Path(args.output_root).absolute()
    require(not output.exists() and not output.is_symlink(), "Output root already exists")
    require(output.parent.resolve() == output.parent, "Output parent must be canonical")
    bindings = {"git_head": head, "helper_sha256": digest(HELPER),
                "codex_path": str(codex), "codex_sha256": digest(codex)}
    canary = None
    if args.role != "canary":
        require(args.canary_receipt, "A passing canary receipt is required")
        canary = verify_receipt(args.canary_receipt, bindings)
    command = [str(codex), "exec", "--approve-for-me", "--sandbox", "workspace-write",
               "--json", "--color", "never", "-C", str(root), "-o", str(output / "final.md")]
    for directory in args.add_dir:
        directory = Path(directory).resolve(strict=True)
        require(directory.is_dir(), "Additional writable path is not a directory")
        command.extend(["--add-dir", str(directory)])
    command.append("-")
    execution_prompt = prompt_bytes + (
        f"\n\nRUN CONTEXT\nRole: {args.role}\nWorkdir: {root}\n"
        f"Output root: {output}\n"
        "Write this invocation's required worker results beneath that absolute output root.\n"
    ).encode()
    state = {"schema": SCHEMA, **bindings, "role": args.role, "workdir": str(root),
             "output_root": str(output), "prompt_path": str(prompt),
             "prompt_sha256": hashlib.sha256(prompt_bytes).hexdigest(),
             "executed_prompt_sha256": hashlib.sha256(execution_prompt).hexdigest(),
             "canary": canary, "command": command,
             "host": socket.gethostname(), "launcher_pid": os.getpid(), "model": "configured_default"}
    if args.plan:
        print(json.dumps({**state, "status": "plan_only"}, indent=2))
        return 0
    load_cborg(environment)
    require(bool(environment.get("CBORG_API_KEY")), "CBORG credential unavailable")
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    os.chmod(output, 0o700)
    environment["EDGEMECH_WORKER_OUTPUT_ROOT"] = str(output)
    state.update(status="starting", started_at=now(),
                 credential_available=bool(environment.get("CBORG_API_KEY")))
    atomic_json(output / "metadata.json", state)
    try:
        with open(output / "events.jsonl", "xb") as events, open(output / "stderr.log", "xb") as errors:
            os.chmod(events.name, 0o600)
            os.chmod(errors.name, 0o600)
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=events, stderr=errors,
                                       cwd=root, env=environment)
            state.update(status="running", worker_pid=process.pid)
            atomic_json(output / "metadata.json", state)
            process.communicate(execution_prompt)
            state["exit_code"] = process.returncode
        require(process.returncode == 0, f"Worker exited with code {process.returncode}")
        require((output / "final.md").is_file() and (output / "final.md").stat().st_size > 0,
                "Worker produced no final response")
        os.chmod(output / "final.md", 0o600)
        state["ending_git_head"] = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
        if args.role == "canary":
            require(digest(HELPER) == bindings["helper_sha256"]
                    and digest(codex) == bindings["codex_sha256"],
                    "Canary runtime files changed during execution")
            require(state["ending_git_head"] == head,
                "Canary Git head changed during execution")
            require(not subprocess.check_output(
                ["git", "-C", str(root), "status", "--porcelain", "--untracked-files=no"],
                text=True).strip(), "Canary changed tracked runtime files")
        result = validate_canary_result(output) if args.role == "canary" else None
        state.update(status="passed" if result is not None else "completed", finished_at=now())
        atomic_json(output / "metadata.json", state)
        if result is not None:
            receipt = {"schema": SCHEMA, **bindings, "status": "passed", "result": result,
                       "prompt_sha256": state["prompt_sha256"],
                       "executed_prompt_sha256": state["executed_prompt_sha256"],
                       "result_sha256": digest(output / "canary-result.json"),
                       "metadata_sha256": digest(output / "metadata.json")}
            atomic_json(output / "canary-receipt.json", receipt)
        print(json.dumps({"status": state["status"], "metadata": str(output / "metadata.json")}))
        return 0
    except Exception as error:
        state.update(status="failed", finished_at=now(), error=str(error))
        atomic_json(output / "metadata.json", state)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", action="store_true")
    mode.add_argument("--run", action="store_true")
    parser.add_argument("--prompt", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--workdir", type=Path, default=ROOT)
    parser.add_argument("--codex", type=Path)
    parser.add_argument("--role", choices=("canary", "calibration", "release"), required=True)
    parser.add_argument("--canary-receipt", type=Path)
    parser.add_argument("--add-dir", type=Path, action="append", default=[])
    args = parser.parse_args()
    try:
        return launch(args)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"Worker launch failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
