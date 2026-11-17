#!/usr/bin/env python3
"""Launch one durable M5 review worker; inputs are a prompt and a pinned canary.

Outputs: private events, stderr, final response, metadata and verified canary receipt.
Serves the user-authorized M5 calibration/release work of 2026-11-16. Never fans out,
selects a model, sends messages, copies credentials, or changes review thresholds.
Issues #137/#138: parent-process input replay and exact host/Python/runtime binding.
Issue #176: canonical repository identity and a separate same-clone save/check gate.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import shlex
import shutil
import socket
import stat
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from kg_microbe_governance.artifacts.scripts.record_review import (
    REPORT_ROOT,
    read_bytes,
    relative_path,
    repository_identity,
)
from kg_microbe_reviews import load_document, read_review, validate_review

ROOT = Path(__file__).resolve().parents[2]
HELPER = Path(__file__).resolve()
CHECKS = {"runtime_contracts", "fresh47_packet_replay", "credential_available"}
SCHEMA = "edgemech-m5-worker/v3"
SCOPE = "operational_bootstrap_only_not_scientific_calibration"
PRODUCTION_SCOPE = "same_clone_production_save_check_only_not_scientific_calibration"
REPOSITORY = "CultureBotAI/EdgeMech"
RUNTIME_KEYS = ("git_head", "helper_sha256", "codex_path", "codex_sha256", "host",
                "python_executable", "python_prefix", "python_version", "python_sha256",
                "lock_sha256", "distributions_sha256", "environment_sha256",
                "repository_identity", "repository_origin")
FRESH47 = Path(".temp/edge-calibration-20261115/fresh-47")
EXECUTION_SUFFIXES = {".py", ".pyi", ".sh", ".bash", ".zsh", ".r", ".jq", ".sql",
                      ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".pl", ".rb", ".ipynb"}


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(path):
    result = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def json_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


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


def child_environment(root):
    environment = os.environ.copy()
    prefixes = [Path(sys.prefix) / "bin", Path.home() / ".local/bin",
                Path.home() / ".nvm/versions/node/v22.16.0/bin", Path("/opt/homebrew/bin")]
    environment["PATH"] = os.pathsep.join(map(str, prefixes)) + os.pathsep + environment.get(
        "PATH", os.defpath)
    environment["PYTHONPATH"] = str(root / "src")
    environment["VIRTUAL_ENV"] = sys.prefix
    environment.pop("PYTHONHOME", None)
    return environment


def repository_bindings(root):
    """Use the pinned shared parser; a valid but unrelated GitHub origin is insufficient."""
    identity = repository_identity(root)
    require(identity.casefold() == REPOSITORY.casefold(), "Worker origin is not EdgeMech")
    origin = subprocess.check_output(["git", "-C", str(root), "remote", "get-url", "origin"],
                                     text=True).strip()
    return {"repository_identity": identity, "repository_origin": origin}


def runtime_bindings(root, environment):
    distributions = []
    for package in importlib.metadata.distributions():
        distributions.append({
            "name": package.metadata.get("Name", "").lower(), "version": package.version,
            "metadata": {name: hashlib.sha256((package.read_text(name) or "").encode()).hexdigest()
                         for name in ("RECORD", "direct_url.json")},
        })
    distributions.sort(key=lambda item: json.dumps(item, sort_keys=True))
    # Source imports follow each same-HEAD worktree. The selected venv and PATH
    # remain literal, including when that shared venv lives beneath the canary root.
    safe_environment = {
        key: environment.get(key, "")
        for key in ("PATH", "PYTHONPATH", "VIRTUAL_ENV")
    }
    if safe_environment["PYTHONPATH"] == str(root / "src"):
        safe_environment["PYTHONPATH"] = "<WORKDIR>/src"
    return {"host": socket.gethostname(), "python_executable": str(Path(sys.executable).absolute()),
            "python_prefix": str(Path(sys.prefix).resolve()), "python_version": sys.version,
            "python_sha256": digest(sys.executable), "lock_sha256": digest(root / "uv.lock"),
            "distributions_sha256": json_digest(distributions),
            "environment_sha256": json_digest(safe_environment)}


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


def replay_bootstrap(output, root, environment, persist=False):
    """Independently validate exact persisted inputs; agent booleans cannot pass this gate."""
    cohort = json.loads((root / "artifacts/edge-calibration-20261115/cohort.json").read_text())
    cases = [case for case in cohort["cases"] if case.get("case_id") == "fresh-47"]
    require(len(cases) == 1, "Expected exactly one frozen fresh-47 case")
    originals = {}
    for name in ("packet.json", "receipt.json"):
        original = checked_file(root / FRESH47 / name, root)
        copied = checked_file(output / name, output)
        require(digest(original) == digest(copied), f"Canary {name} differs from actual fresh-47")
        document = json.loads(copied.read_text())
        require(document.get("occurrence_id") == cases[0]["occurrence_id"],
                f"Canary {name} is not the frozen fresh-47 occurrence")
        if name == "receipt.json":
            require(document.get("case_id") == "fresh-47", "Canary receipt has the wrong case")
        originals[name] = digest(original)
    commands = [
        ("runtime_contracts", [sys.executable, "-B", "-m", "edgemech", "check-contracts"]),
        ("fresh47_packet_replay", [sys.executable, "-B", str(root / "scripts/adhoc/"
           "prepare_calibration_20261115.py"), "--check", "fresh-47"]),
    ]
    validations = []
    for name, command in commands:
        completed = subprocess.run(command, cwd=root, env=environment, capture_output=True)
        validation = {"name": name, "command": command, "exit_code": completed.returncode,
                      "stdout_sha256": hashlib.sha256(completed.stdout).hexdigest(),
                      "stderr_sha256": hashlib.sha256(completed.stderr).hexdigest()}
        validations.append(validation)
        if persist:
            for stream in ("stdout", "stderr"):
                path = output / f"validator-{name}.{stream}"
                descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(descriptor, "wb") as target:
                    target.write(getattr(completed, stream))
            atomic_json(output / "validator-results.json", validations)
        require(completed.returncode == 0, f"Independent validator failed: {name}")
    return {"artifacts": originals, "validators": validations}


def relative_pin(root, value):
    path = str(relative_path(value))
    return {"path": path, "sha256": digest(checked_file(root / path, root))}


def execution_inventory(root):
    """Bounded scripts/src scan includes hidden and Git-ignored helpers, not inline execution."""
    result = []
    for directory in (root / "scripts", root / "src"):
        require(not directory.is_symlink(), "Reviewer execution directory is a symlink")
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*")):
            require(not path.is_symlink(), "Reviewer execution path is a symlink")
            if path.is_file() and (path.suffix.casefold() in EXECUTION_SUFFIXES
                                   or stat.S_IMODE(path.stat().st_mode) & 0o111):
                result.append({**relative_pin(root, str(path.relative_to(root))),
                               "executable": bool(stat.S_IMODE(path.stat().st_mode) & 0o111)})
    return result


def production_spec(root, review_path, packet_path, proofs_path, manifest_path):
    """Bind authored bytes before a child starts; canonical paths come from shared CLAW."""
    inputs = {name: relative_pin(root, value) for name, value in (
        ("review", review_path), ("packet", packet_path), ("proofs", proofs_path))}
    authored = load_document(read_bytes(root, inputs["review"]["path"]))
    validate_review(authored)
    review = str(relative_path(f"{REPORT_ROOT}/{authored['review_id']}/review.yaml"))
    return {"workdir": str(root), "inputs": inputs,
            "package": relative_pin(root, manifest_path), "review_id": authored["review_id"],
            "authored_sha256": json_digest(authored), "review": review,
            "execution_files": execution_inventory(root),
            "source_inputs": [relative_pin(root, pin["path"])
                              for pin in authored["source"]["inputs"]]}


def production_current(root, spec):
    require(spec.get("workdir") == str(root), "Production canary belongs to another clone")
    current = production_spec(root, *(spec["inputs"][name]["path"]
                                     for name in ("review", "packet", "proofs")),
                              spec["package"]["path"])
    require(current == spec, "Production canary input or package changed")
    return current


def production_validator(name, command, root, environment, output=None):
    completed = subprocess.run(command, cwd=root, env=environment, capture_output=True)
    record = {"name": name, "command": command, "exit_code": completed.returncode,
              "stdout_sha256": hashlib.sha256(completed.stdout).hexdigest(),
              "stderr_sha256": hashlib.sha256(completed.stderr).hexdigest()}
    if output is not None:
        for stream in ("stdout", "stderr"):
            path = output / f"validator-{name}.{stream}"
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "wb") as target:
                target.write(getattr(completed, stream))
        atomic_json(output / f"validator-{name}.json", record)
    require(completed.returncode == 0, f"Independent validator failed: {name}")
    result = json.loads(completed.stdout)
    require(isinstance(result, dict), f"Invalid validator response: {name}")
    return record, result


def production_command(root, spec, action):
    review = spec["review"] if action == "check" else spec["inputs"]["review"]["path"]
    return [sys.executable, "-B", "-m", "edgemech.occurrence_review", action,
            "--root", str(root), "--review", review,
            "--packet", spec["inputs"]["packet"]["path"],
            "--proofs", spec["inputs"]["proofs"]["path"]]


def verify_package(root, manifest_path, environment, output=None):
    pin = relative_pin(root, manifest_path)
    record, result = production_validator("production-package", [sys.executable, "-B",
        str(root / "scripts/adhoc/calibration_round_20261116.py"), "--root", str(root),
        "verify", "--manifest", pin["path"]], root, environment, output)
    require(result.get("manifest_sha256") == pin["sha256"], "Package verifier read different bytes")
    return record


def prepare_production(root, spec, environment):
    production_current(root, spec)
    target = (root / spec["review"]).parent
    require(not target.exists() and not target.is_symlink(),
            "Production canary target already exists; use a new operational review ID")
    verify_package(root, spec["package"]["path"], environment)
    manifest = json.loads(read_bytes(root, spec["package"]["path"]))
    require(any(case.get("packet_path") == spec["inputs"]["packet"]["path"]
                for case in manifest["cases"]), "Production packet is outside the frozen cohort")
    production_validator("production-input", production_command(root, spec, "validate"),
                         root, environment)


def inspect_production_pair(root, spec):
    persisted = read_review(root, spec["review"])
    require(json_digest(persisted) == spec["authored_sha256"],
            "Saved production review changed the authored content")
    markdown = str(Path(spec["review"]).with_name("review.md"))
    return {"review": relative_pin(root, spec["review"]),
            "markdown": relative_pin(root, markdown)}


def save_production(root, spec, environment, output):
    """The parent executes the real save/check, never an agent's claimed success."""
    prepare_production(root, spec, environment)
    package_check = verify_package(root, spec["package"]["path"], environment, output)
    saved, result = production_validator("production-save", production_command(root, spec, "save"),
                                        root, environment, output)
    require(result.get("review") == spec["review"], "Save returned another canonical review")
    outputs = inspect_production_pair(root, spec)
    require(result.get("review_sha256") == outputs["review"]["sha256"],
            "Save returned the wrong review hash")
    checked, _ = production_validator("production-check", production_command(root, spec, "check"),
                                      root, environment, output)
    production_current(root, spec)
    require(inspect_production_pair(root, spec) == outputs, "Production output changed during replay")
    return {"spec": spec, "outputs": outputs, "validators": [package_check, saved, checked]}


def replay_production(root, production, manifest_path, environment):
    require(isinstance(production, dict), "Missing same-clone production save/check receipt")
    spec = production.get("spec", {})
    production_current(root, spec)
    require(relative_pin(root, manifest_path) == spec["package"],
            "Reviewer package differs from production canary")
    require(inspect_production_pair(root, spec) == production.get("outputs"),
            "Production canary output changed")
    package_check = verify_package(root, manifest_path, environment)
    checked, _ = production_validator("production-check", production_command(root, spec, "check"),
                                      root, environment)
    return {"spec": spec, "outputs": production["outputs"],
            "validators": [package_check, checked]}


def assert_immutable_execution(root, bindings, environment, label):
    require(digest(HELPER) == bindings["helper_sha256"]
            and digest(bindings["codex_path"]) == bindings["codex_sha256"],
            f"{label} runtime files changed during execution")
    head = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"],
                                   text=True).strip()
    require(head == bindings["git_head"], f"{label} Git head changed during execution")
    require(not subprocess.check_output(
        ["git", "-C", str(root), "status", "--porcelain", "--untracked-files=no"],
        text=True).strip(), f"{label} changed tracked runtime files")
    repository = repository_bindings(root)
    require(repository == {key: bindings[key] for key in repository},
            f"{label} repository identity or origin changed during execution")
    runtime = runtime_bindings(root, environment)
    require(runtime == {key: bindings[key] for key in runtime},
            f"{label} host or Python runtime changed during execution")


def verify_receipt(path, bindings, root, environment, *, reviewer_package=None):
    path = Path(path).absolute()
    checked_file(path, path.parent)
    receipt = json.loads(path.read_text())
    require(isinstance(receipt, dict), "Invalid canary receipt")
    require(receipt.get("schema") == SCHEMA and receipt.get("status") == "passed",
            "Canary receipt is not a passing worker receipt")
    scope = PRODUCTION_SCOPE if reviewer_package is not None else SCOPE
    require(receipt.get("scope") == scope, "Canary receipt has the wrong capability scope")
    for key in RUNTIME_KEYS:
        require(receipt.get(key) == bindings[key], f"Canary runtime changed: {key}")
    metadata = checked_file(path.parent / "metadata.json", path.parent)
    require(digest(metadata) == receipt.get("metadata_sha256"), "Canary metadata changed")
    state = json.loads(metadata.read_text())
    require(isinstance(state, dict), "Invalid canary metadata")
    require(all(state.get(key) == bindings[key] for key in RUNTIME_KEYS),
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
    replay = replay_bootstrap(path.parent, root, environment)
    require(replay["artifacts"] == receipt.get("independent_replay", {}).get("artifacts"),
            "Canary independently replayed artifacts changed")
    production = None
    if reviewer_package is not None:
        require(receipt.get("production") == state.get("production"),
                "Production metadata differs from receipt")
        production = replay_production(root, receipt.get("production"), reviewer_package, environment)
    return {"path": str(path), "sha256": digest(path), "current_replay": replay,
            "production_replay": production}


def launch(args):
    root = Path(args.workdir).resolve()
    environment = child_environment(root)
    repository = repository_bindings(root)
    codex = Path(args.codex or shutil.which("codex", path=environment["PATH"]) or "")
    require(codex.is_file() and os.access(codex, os.X_OK), "Codex executable unavailable")
    codex = codex.resolve()
    with codex.open("rb") as stream:
        require(stream.read(4) in (b"\x7fELF", b"\xcf\xfa\xed\xfe", b"\xfe\xed\xfa\xcf",
                                  b"\xca\xfe\xba\xbe", b"\xbe\xba\xfe\xca"),
                "Use the native Codex executable, not a shell or JavaScript wrapper")
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
                "codex_path": str(codex), "codex_sha256": digest(codex),
                **runtime_bindings(root, environment), **repository}
    production_args = [getattr(args, "production_" + name, None)
                       for name in ("review", "packet", "proofs")]
    package = getattr(args, "package_manifest", None)
    production = None
    if any(production_args):
        require(args.role == "canary" and all(production_args) and package,
                "Production canary requires all three inputs and package manifest with role canary")
        production = production_spec(root, *production_args, package)
        prepare_production(root, production, environment)
    elif args.role == "reviewer":
        require(package, "Reviewer requires the frozen package manifest")
    else:
        require(package is None, "Package manifest requires production canary or reviewer role")
    canary = None
    if args.role != "canary":
        require(args.canary_receipt, "A passing canary receipt is required")
        canary = verify_receipt(args.canary_receipt, bindings, root, environment,
                               reviewer_package=package if args.role == "reviewer" else None)
    # Automatic approval review already selects workspace-write (CLI issue #142).
    command = [str(codex), "exec", "--approve-for-me",
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
    if production is not None:
        execution_prompt += (
            "\nPRODUCTION CANARY CONTEXT\nThe parent will execute the real production save/check "
            "after your operational replay. Do not edit the authored production inputs, package, "
            "or create the canonical target yourself. Complete only the seeded replay-canary "
            "prompt; do not re-prepare existing inputs. This is not a scientific rating.\n"
        ).encode()
    state = {"schema": SCHEMA, **bindings, "role": args.role, "workdir": str(root),
             "output_root": str(output), "prompt_path": str(prompt),
             "prompt_sha256": hashlib.sha256(prompt_bytes).hexdigest(),
             "executed_prompt_sha256": hashlib.sha256(execution_prompt).hexdigest(),
             "canary": canary, "production_plan": production, "command": command,
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
        if args.role in {"canary", "reviewer"}:
            assert_immutable_execution(root, bindings, environment, args.role.title())
        if args.role == "reviewer":
            state["ending_replay"] = verify_receipt(args.canary_receipt, bindings, root, environment,
                                                    reviewer_package=package)
            # Validators are read-only. Recheck after running them before declaring completion.
            assert_immutable_execution(root, bindings, environment, "Reviewer")
            production_current(root, state["ending_replay"]["production_replay"]["spec"])
        result = validate_canary_result(output) if args.role == "canary" else None
        independent = None
        if result is not None:
            independent = replay_bootstrap(output, root, environment, persist=True)
            assert_immutable_execution(root, bindings, environment, "Canary")
            state["independent_replay"] = independent
            if production is not None:
                state["production"] = save_production(root, production, environment, output)
                assert_immutable_execution(root, bindings, environment, "Production canary")
        state.update(status="passed" if result is not None else "completed", finished_at=now())
        atomic_json(output / "metadata.json", state)
        if result is not None:
            receipt = {"schema": SCHEMA, **bindings, "status": "passed", "result": result,
                       "scope": PRODUCTION_SCOPE if production is not None else SCOPE,
                       "production": state.get("production"),
                       "independent_replay": independent,
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
    parser.add_argument("--role", choices=("canary", "calibration", "release", "reviewer"), required=True)
    parser.add_argument("--canary-receipt", "--production-receipt", dest="canary_receipt", type=Path)
    parser.add_argument("--package-manifest")
    parser.add_argument("--production-review")
    parser.add_argument("--production-packet")
    parser.add_argument("--production-proofs")
    parser.add_argument("--add-dir", type=Path, action="append", default=[])
    args = parser.parse_args()
    try:
        return launch(args)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"Worker launch failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
