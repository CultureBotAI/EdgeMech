#!/usr/bin/env python3
"""Plan, run and replay one M5 helper via codex-work in an owned tmux session.

Inputs: exact Git worktree, prompt, wrapper and executable. Outputs: private plan,
metadata, JSONL events, stderr, final response, REPORT.md and mechanical receipt.
Serves the content-review plan implementation, 2026-11-19. This helper is NEVER a
scientific reviewer or calibration gate. A real canary precedes later helpers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pwd
import re
import shlex
import socket
import stat
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HELPER = Path(__file__).resolve()
SHELL_HELPER = HELPER.with_name("codex_work_helper_20261119.sh")
SCHEMA = "edgemech-helper-worker/20261119-v1"
SCOPE = "helper_preparation_only_not_scientific_review"
ARTIFACTS = ("events.jsonl", "stderr.log", "final.md", "REPORT.md", "prompt.md")
NATIVE_MAGICS = {b"\x7fELF", b"\xcf\xfa\xed\xfe", b"\xfe\xed\xfa\xcf",
                 b"\xce\xfa\xed\xfe", b"\xfe\xed\xfa\xce", b"\xca\xfe\xba\xbe",
                 b"\xca\xfe\xba\xbf", b"\xbe\xba\xfe\xca", b"\xbf\xba\xfe\xca"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def stamp():
    return datetime.now(timezone.utc).isoformat()


def write_new(path, value):
    """Exclusive, private durable writes; existing failures are never replaced."""
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as stream:
        stream.write(value)
        stream.flush()
        os.fsync(stream.fileno())


def write_json(path, value):
    write_new(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def no_symlinks(path):
    require(path.is_absolute(), "An absolute path is required")
    require(not any(p.is_symlink() for p in (path, *path.parents)), "Symlink path rejected")


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def file_pin(path, *, allow_symlink=False):
    path = Path(path).absolute()
    if not allow_symlink:
        no_symlinks(path)
    require(path.is_file() and path.stat().st_size, "Missing or empty pinned file")
    return {"path": str(path), "resolved_path": str(path.resolve()), "sha256": sha(path)}


def child_environment(codex_bin):
    """Deterministic across SSH/tmux; work-account auth comes from the existing wrapper.

    No provider keys are copied from ambient shells. This preparation canary does
    not certify CBORG or publisher access; those need their own credential canary.
    """
    user = pwd.getpwuid(os.getuid())
    return {"HOME": user.pw_dir, "USER": user.pw_name, "LOGNAME": user.pw_name,
            "SHELL": "/bin/bash", "LANG": "en_US.UTF-8",
            "PATH": str(Path(codex_bin).parent)
            + ":/Users/marcin/.local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"}


def bindings(root, wrapper, codex_bin):
    root = Path(root)
    no_symlinks(root)
    require(git(root, "rev-parse", "--show-toplevel") == str(root), "Use the worktree root")
    branch = git(root, "branch", "--show-current")
    require(branch and branch not in {"main", "master"}, "Use a dedicated implementation branch")
    origin = git(root, "remote", "get-url", "origin")
    require(origin in {"https://github.com/CultureBotAI/EdgeMech.git",
                       "git@github.com:CultureBotAI/EdgeMech.git"}, "Unexpected repository origin")
    env = child_environment(codex_bin)
    # #215: codex-work runs `command codex`. Put the actual native executable
    # first on PATH; never accept the npm JavaScript trampoline as that pin.
    native = Path(codex_bin).absolute()
    require(native.name == "codex" and not native.is_symlink(),
            "Use the regular native codex executable, not the npm entrypoint symlink")
    with native.open("rb") as stream:
        header = stream.read(256)
    require(b"node" not in header.split(b"\n", 1)[0],
            "Node entrypoints are not native Codex runtime pins")
    require(header[:4] in NATIVE_MAGICS and os.access(native, os.X_OK),
            "Codex must be an executable native Mach-O or ELF binary")
    return {"root": str(root), "branch": branch, "head": git(root, "rev-parse", "HEAD"),
            "origin": origin, "host": socket.gethostname(),
            "launcher": file_pin(HELPER), "shell_launcher": file_pin(SHELL_HELPER),
            "wrapper": file_pin(wrapper), "codex_bin": file_pin(native),
            "python": file_pin(sys.executable, allow_symlink=True),
            "environment": env, "ambient_provider_credentials_inherited": False}


def output_path(root, output):
    root, output = Path(root), Path(output)
    no_symlinks(output)
    base = root / ".temp/helper-workers-20261119"
    require(output.parent == base, "Output must be one direct child of .temp/helper-workers-20261119")
    require(re.fullmatch(r"[a-z0-9][a-z0-9-]{0,70}", output.name), "Invalid output name")
    return output


def check_runtime(plan, *, finished=False):
    b = plan["bindings"]
    require(plan.get("schema") == SCHEMA and plan.get("scope") == SCOPE, "Wrong helper plan")
    current = bindings(b["root"], b["wrapper"]["path"], b["codex_bin"]["path"])
    if finished and plan.get("allow_commit"):
        subprocess.run(["git", "-C", b["root"], "merge-base", "--is-ancestor", b["head"],
                        current["head"]], check=True, capture_output=True)
        current = {**current, "head": b["head"]}
    require(current == b, "Helper runtime changed since planning")
    require(file_pin(plan["task_prompt"]["path"]) == plan["task_prompt"], "Task prompt changed")
    output_path(b["root"], plan["output"])


def canary_check(plan):
    if plan["unit"] == "canary":
        require(plan.get("canary") is None, "Canary cannot inherit a receipt")
        return
    require(plan["unit"] == "helper" and plan.get("canary"), "Later helper requires a canary")
    pin = plan["canary"]
    require(file_pin(pin["path"]) == pin, "Canary receipt changed")
    receipt = json.loads(Path(pin["path"]).read_text())
    prior = check(Path(pin["path"]).parent, publish=False)
    require(prior == receipt and receipt["unit"] == "canary", "Invalid canary receipt")
    require(receipt["bindings"] == plan["bindings"], "Canary used a different runtime/environment")


def make_plan(args):
    root = Path(args.root).absolute()
    output = output_path(root, Path(args.output).absolute())
    require(not output.exists(), "Output already exists; use a new unit name")
    require(not git(root, "status", "--porcelain", "--untracked-files=no"),
            "Commit the launcher and inputs before planning")
    plan = {"schema": SCHEMA, "scope": SCOPE, "unit": args.unit, "mode": args.mode,
            "allow_commit": args.allow_commit,
            "bindings": bindings(root, args.wrapper, args.codex_bin),
            "task_prompt": file_pin(args.prompt), "output": str(output),
            "canary": file_pin(args.canary_receipt) if args.canary_receipt else None}
    require(args.mode != "inspect" or not args.allow_commit, "Inspection cannot commit changes")
    canary_check(plan)
    return plan


def rendered_prompt(plan):
    return (
        "You are a helper for authorized EdgeMech evidence preparation and implementation. "
        "You are NOT a scientific calibration reviewer. Do not create scientific assessments, "
        "promote graph edges, expand the scientific cohort, change thresholds, merge, "
        "push, notify people, read credential files, print secrets or spawn additional workers. "
        "Preserve all prior evidence and outputs. Follow repository AGENTS.md. "
        "Write helper scripts only under scripts/adhoc/ before executing them.\n"
        + ("You may commit only the files explicitly named in the task on this existing branch. "
           if plan["allow_commit"] else "Do not commit changes. ")
        + f"Mode: {plan['mode']}. "
        + ("Read existing repository/evidence only; create only REPORT.md in the output directory. "
           if plan["mode"] == "inspect" else
           "Implement only the bounded task on this dedicated branch; do not edit launcher files. ")
        + f"Output directory: {plan['output']}\n"
        "Write a nonempty REPORT.md there describing concrete findings, inspected paths, "
        "uncertainties, any changed files and validation. Final chat response is a separate artifact. "
        "Never assert scientific correctness merely because this mechanical helper completes.\n\n"
        + Path(plan["task_prompt"]["path"]).read_text()
    )


def run(plan_path, tmux):
    plan = json.loads(plan_path.read_text())
    check_runtime(plan)
    canary_check(plan)
    root = Path(plan["bindings"]["root"])
    require(not git(root, "status", "--porcelain", "--untracked-files=no"), "Dirty starting worktree")
    output = output_path(root, Path(plan["output"]))
    output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    output.mkdir(mode=0o700)
    write_json(output / "plan.json", plan)
    write_new(output / "prompt.md", rendered_prompt(plan))
    session = "edgemech-helper-" + output.name
    write_json(output / "metadata.json", {"schema": SCHEMA, "scope": SCOPE,
               "created_at": stamp(), "session": session, "plan_sha256": sha(output / "plan.json"),
               "rendered_prompt_sha256": sha(output / "prompt.md")})
    command = [sys.executable, str(HELPER), "_execute", "--output", str(output)]
    # The new unique session owns only this job; no send-keys into existing panes.
    subprocess.run([tmux, "new-session", "-d", "-s", session, "-c", str(root),
                    shlex.join(command)], check=True)
    return {"session": session, "output": str(output), "status": "launched",
            "scope": SCOPE, "check": [sys.executable, str(HELPER), "check", "--output", str(output)]}


def execute(output):
    os.umask(0o077)
    # #216: validate the owned destination before writing; retain all subsequent
    # startup failures even when detached tmux exits before a provider starts.
    no_symlinks(output)
    require(output.is_dir() and stat.S_IMODE(output.stat().st_mode) == 0o700,
            "Unsafe helper output directory")
    require(output.parent.name == "helper-workers-20261119"
            and output.parent.parent.name == ".temp", "Unexpected helper output location")
    result = {"started_at": stamp(), "scope": SCOPE, "stage": "startup_replay"}
    try:
        plan = json.loads((output / "plan.json").read_text())
        check_runtime(plan)
        canary_check(plan)
        require(Path(plan["output"]) == output, "Execution output does not match frozen plan")
        meta = json.loads((output / "metadata.json").read_text())
        require(meta["plan_sha256"] == sha(output / "plan.json")
                and meta["rendered_prompt_sha256"] == sha(output / "prompt.md"),
                "Launch inputs changed")
        write_json(output / "lease.json", {"pid": os.getpid(), "started_at": stamp()})
        b = plan["bindings"]
        command = ["/bin/bash", "--noprofile", "--norc", str(SHELL_HELPER), b["wrapper"]["path"],
                   b["codex_bin"]["path"], "exec", "--approve-for-me", "--json", "--color",
                   "never", "-C", b["root"], "--output-last-message", str(output / "final.md"), "-"]
        result.update({"command": command, "stage": "native_execution"})
        with ((output / "prompt.md").open("rb") as prompt, os.fdopen(os.open(
                output / "events.jsonl", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as events,
                os.fdopen(os.open(output / "stderr.log", os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                                  0o600), "wb") as errors):
            child = subprocess.run(command, cwd=b["root"], stdin=prompt, stdout=events,
                                   stderr=errors, env=child_environment(b["codex_bin"]["path"]))
        result["exit_code"] = child.returncode
        result["stage"] = "exit_replay"
        check_runtime(plan, finished=True)
        result["ending_head"] = git(b["root"], "rev-parse", "HEAD")
        result["tracked_changes"] = git(b["root"], "status", "--porcelain", "--untracked-files=no")
        require(plan["mode"] != "inspect" or not result["tracked_changes"],
                "Inspection helper modified tracked files")
        result["artifacts"] = {name: sha(output / name) for name in ARTIFACTS
                               if (output / name).is_file()}
        result["runtime_replayed"] = True
        result["stage"] = "completed"
    except Exception as exc:
        # Exception text can contain arbitrary child output; record only its type.
        result["failure_type"] = type(exc).__name__
    result["finished_at"] = stamp()
    write_json(output / "completion.json", result)


def check(output, *, publish=True):
    no_symlinks(output)
    require(stat.S_IMODE(output.stat().st_mode) == 0o700, "Output directory is not private")
    plan = json.loads((output / "plan.json").read_text())
    check_runtime(plan, finished=True)
    require(Path(plan["output"]) == output, "Receipt output differs from frozen plan")
    meta = json.loads((output / "metadata.json").read_text())
    require(meta["plan_sha256"] == sha(output / "plan.json"), "Frozen plan changed")
    require(meta["rendered_prompt_sha256"] == sha(output / "prompt.md"), "Rendered prompt changed")
    result = json.loads((output / "completion.json").read_text())
    require(result.get("exit_code") == 0 and result.get("runtime_replayed") is True
            and "failure_type" not in result, "Helper did not complete with verified runtime")
    require(plan["mode"] != "inspect" or not result.get("tracked_changes"), "Inspection changed files")
    require(result["ending_head"] == git(plan["bindings"]["root"], "rev-parse", "HEAD"),
            "Worktree HEAD changed after helper completion")
    for name in ARTIFACTS:
        path = output / name
        no_symlinks(path)
        require(path.is_file(), "Expected helper artifact missing")
        require(name == "stderr.log" or path.stat().st_size > 0, "Empty helper artifact")
        require(sha(path) == result["artifacts"].get(name), "Helper artifact hash changed")
        require(stat.S_IMODE(path.stat().st_mode) & 0o077 == 0, "Helper artifact is not private")
    events = [json.loads(line) for line in (output / "events.jsonl").read_text().splitlines() if line]
    require(any(row.get("type") == "thread.started" for row in events), "No native session started")
    require(any(row.get("type") == "turn.completed" for row in events), "No native turn completed")
    require(not any(row.get("type") in {"turn.failed", "error"} for row in events),
            "Native worker reported failure")
    receipt = {"schema": SCHEMA, "scope": SCOPE, "status": "passed", "unit": plan["unit"],
               "mode": plan["mode"], "bindings": plan["bindings"],
               "ending_head": result["ending_head"],
               "output": str(output), "plan_sha256": sha(output / "plan.json"),
               "completion_sha256": sha(output / "completion.json"), "artifacts": result["artifacts"],
               "limits": "Mechanical persistence only; report contents and scientific truth unverified"}
    receipt_path = output / "receipt.json"
    if publish and not receipt_path.exists():
        write_json(receipt_path, receipt)
    if receipt_path.exists():
        require(json.loads(receipt_path.read_text()) == receipt, "Saved receipt no longer replays")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    plan = sub.add_parser("plan")
    for arg in ("root", "prompt", "output", "wrapper", "codex-bin"):
        plan.add_argument("--" + arg, required=True)
    plan.add_argument("--unit", choices=("canary", "helper"), required=True)
    plan.add_argument("--mode", choices=("inspect", "implement"), default="inspect")
    plan.add_argument("--canary-receipt")
    plan.add_argument("--allow-commit", action="store_true")
    launch = sub.add_parser("run")
    launch.add_argument("--plan", type=Path, required=True)
    launch.add_argument("--tmux", default="/opt/homebrew/bin/tmux")
    for name in ("check", "_execute"):
        sub.add_parser(name).add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.action == "plan":
            result = make_plan(args)
        elif args.action == "run":
            result = run(args.plan, args.tmux)
        elif args.action == "check":
            result = check(args.output)
        else:
            execute(args.output)
            return
        print(json.dumps(result, indent=2, sort_keys=True))
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        print(f"Helper rejected: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
