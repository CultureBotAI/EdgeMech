#!/usr/bin/env python3
"""Launch the single excluded native preparation worker; never send TUI input.

Purpose: guarded standalone codex-work bootstrap for the authorized native campaign.
Inputs: explicit CLAW/coordinator/campaign roots, accepted request and commit,
and private tmux executable/socket/session binding passed as CLI arguments.
Outputs: isolated clone, retained tmux pane, immutable private stage receipts.
UTC date: 2026-11-20. Issue: CultureBotAI/EdgeMech#228 (helper provenance).
Provenance: new implementation of the installed boss guarded-bootstrap protocol;
does not modify, import, or rerun the original coordinator mutation helpers.
The executed initial version and receipt remain in private campaign storage;
only their hashes/result summary are tracked in scripts/adhoc/provenance/.
This maintained revision uses the
current CLAW AGENTS context-manager contract; it has not been rerun to recreate
historical evidence. Existing attempt guards prohibit a second worker launch.
Scientific coverage is always zero. Interactive prompts require separate handling
by the authorized human/root; this helper cannot answer or paste into any pane.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REQUEST_SHA = "4af8b1cc2fe98032d5ff7f1d7ddb659e491310d3dfd0bcb7a370645c97048a4d"
INITIAL_HEAD = "945c421c648fe09858eabf1f2a4447ab27f9eae3"
ORIGIN = "https://github.com/CultureBotAI/EdgeMech.git"


def run(argv: list[str], *, cwd: Path | None = None) -> str:
    return subprocess.run(
        argv, cwd=cwd, check=True, capture_output=True, text=True, timeout=60
    ).stdout.strip()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def receipt(root: Path, stage: str, data: dict) -> Path:
    path = root / f"{stage}.json"
    record = {
        "at_utc": datetime.now(timezone.utc).isoformat(),
        "stage": stage,
        "scientific_review_coverage": 0,
        "classification": "EXCLUDED_PREPARATION_CANARY",
        "helper_path": str(Path(__file__).resolve()),
        "helper_sha256": digest(Path(__file__)),
        **data,
    }
    with path.open("x") as stream:
        json.dump(record, stream, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claw-root", type=Path, required=True)
    parser.add_argument("--coordinator-root", type=Path, required=True)
    parser.add_argument("--campaign-root", type=Path, required=True)
    parser.add_argument("--native", type=Path, required=True)
    parser.add_argument("--wrapper", type=Path, required=True)
    parser.add_argument("--tmux-bin", type=Path, required=True)
    parser.add_argument("--tmux-socket", type=Path, required=True)
    parser.add_argument("--session", required=True)
    args = parser.parse_args()
    if not args.tmux_bin.is_absolute() or not args.tmux_socket.is_absolute():
        raise SystemExit("tmux executable/socket inputs must be absolute")
    if not args.session or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-"
                               for c in args.session):
        raise SystemExit("session must contain only lowercase letters, digits, hyphens")
    tmux_bin, socket, session = str(args.tmux_bin), str(args.tmux_socket), args.session
    claw = args.claw_root.resolve()
    coordinator = args.coordinator_root.resolve()
    campaign = args.campaign_root.resolve()
    if campaign != coordinator.parent or coordinator.name != "coordinator-checkout":
        raise SystemExit("unexpected owned campaign/coordinator layout")
    if digest(campaign / "REQUEST.md") != REQUEST_SHA:
        raise SystemExit("request hash changed")
    if run(["git", "rev-parse", "HEAD"], cwd=coordinator) != INITIAL_HEAD:
        raise SystemExit("accepted coordinator runtime changed; re-plan before launch")
    if run(["git", "remote", "get-url", "origin"], cwd=coordinator) != ORIGIN:
        raise SystemExit("coordinator origin mismatch")
    # Existing GUI server only. No -A and no fallback server/socket.
    tmux = [tmux_bin, "-N", "-S", socket]
    sessions = run([*tmux, "list-sessions", "-F", "#S"]).splitlines()
    panes = run([*tmux, "list-panes", "-a", "-F",
                 "#{session_name}|#{pane_id}|#{pane_pid}|#{pane_current_path}"])
    if session in sessions:
        raise SystemExit("preparation session already exists; inspect, never relaunch")
    destination = campaign / "preparation-worker-01"
    evidence = campaign / "preparation-launch-01"
    if destination.exists() or evidence.exists():
        raise SystemExit("retained preparation attempt exists; inspect, never overwrite")
    native = args.native.resolve(strict=True)
    wrapper = args.wrapper.resolve(strict=True)
    native_kind = run(["/usr/bin/file", "-b", str(native)])
    if "Mach-O" not in native_kind and "ELF" not in native_kind:
        raise SystemExit("native must be the actual binary")
    help_text = run([str(native), "--help"])
    if "--no-daemon" not in help_text:
        raise SystemExit("standalone execution mode is unsupported")
    sys.path[:0] = [str(claw), str(claw / "src")]
    from plugins.lock_manager import LockManager
    from plugins.repository_settings import RepositorySettings, merged_repository_environment

    target = RepositorySettings.from_environment(
        environ=merged_repository_environment(claw / ".env")
    ).get_target("edgemech")
    repository = target.open()  # validates the manifest-resolved Git identity
    canonical_head = repository.head.commit.hexsha
    evidence.mkdir(mode=0o700)
    receipt(evidence, "01-plan", {
        "request_sha256": REQUEST_SHA, "checkout": str(destination),
        "head": INITIAL_HEAD, "canonical_root": str(target.path),
        "canonical_head": canonical_head, "session": session, "socket": socket,
        "tmux_bin": tmux_bin,
        "inventory": panes.splitlines(), "native": str(native),
        "native_sha256": digest(native), "wrapper": str(wrapper),
        "wrapper_sha256": digest(wrapper), "occurrence_id": None,
        "full_AB_frozen": False, "prompt_delivery": "not_attempted",
    })
    os.environ["OPENCLAW_ORCHESTRATION_ROOT"] = str(claw)
    manager = LockManager({"my_id": f"edge-preparation-{os.getpid()}"})
    try:
        # CLAW AGENTS requires the lease-owned context manager in new code.
        # All six subprocesses are bounded at 60s, below this short lease.
        with manager.lock("edgemech", "create-restart-preparation-01", timeout=900):
            target.open()  # revalidate canonical ownership at metadata transition
            if run(["git", "rev-parse", "HEAD"], cwd=coordinator) != INITIAL_HEAD:
                raise RuntimeError("accepted coordinator runtime changed")
            run(["git", "clone", "--shared", "--no-checkout", str(coordinator),
                 str(destination)])
            run(["git", "remote", "set-url", "origin", ORIGIN], cwd=destination)
            run(["git", "checkout", "-b", "campaign/lbnl-preparation-20261120-01",
                 INITIAL_HEAD], cwd=destination)
            if run(["git", "status", "--porcelain=v1"], cwd=destination):
                raise RuntimeError("new preparation checkout is not clean")
            receipt(evidence, "02-checkout", {
                "checkout": str(destination), "head": run(["git", "rev-parse", "HEAD"],
                                                           cwd=destination),
                "branch": "campaign/lbnl-preparation-20261120-01",
            })
    except BaseException as exc:
        receipt(evidence, "02-failed", {"error_type": type(exc).__name__,
                                        "error": str(exc)})
        raise
    if manager.check_lock("edgemech") or manager.is_global_locked():
        receipt(evidence, "02-lock-still-active", {"state": "NO_LAUNCH_ACTIVE_LOCK"})
        raise RuntimeError("repository/global lease still active; agent launch refused")
    driver = destination / "scripts/adhoc/codex_work_helper_20261119.sh"
    # Fixed bootstrap receives literal paths, never task text. Retain on exit
    # before cd or agent startup; normal installed shell function/permissions.
    bootstrap = (
        '"$1" -N -S "$2" set-option -p -t "$TMUX_PANE" remain-on-exit on '
        '&& cd -- "$3" && PATH="$4:$PATH" && export PATH '
        '&& exec /bin/bash --noprofile --norc "$5" "$6" "$7" --no-daemon'
    )
    try:
        pane = run([*tmux, "new-session", "-d", "-s", session, "-n", "primary",
                    "-c", str(destination), "-P", "-F", "#{pane_id}",
                    "/bin/sh", "-c", bootstrap, "sh", tmux_bin, socket,
                    str(destination), str(native.parent), str(driver), str(wrapper), str(native)])
        path = receipt(evidence, "03-launch", {
            "pane": pane, "session": session, "socket": socket,
            "checkout": str(destination), "head": INITIAL_HEAD,
            "state": "LAUNCHED_INPUT_NOT_INSPECTED", "thread_id": None,
            "native_pid": None, "model": None, "effort": None,
            "prompt_delivery": "not_attempted", "metadata_lock_released": True,
        })
        print(path)
    except BaseException as exc:
        receipt(evidence, "03-failed", {"error_type": type(exc).__name__,
                                        "error": str(exc)})
        raise


if __name__ == "__main__":
    main()
