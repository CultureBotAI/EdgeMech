"""Offline failure/ownership tests; never create a tmux server or real agent."""

from contextlib import contextmanager
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = spec_from_file_location(
    "restart_launcher", ROOT / "scripts/adhoc/launch_restart_preparation_20261120.py"
)
launcher = module_from_spec(SPEC)
SPEC.loader.exec_module(launcher)


@pytest.fixture
def harness(tmp_path, monkeypatch):
    campaign = tmp_path / "campaign"
    coordinator = campaign / "coordinator-checkout"
    coordinator.mkdir(parents=True)
    (campaign / "REQUEST.md").write_text("authorized test request")
    native = tmp_path / "native"
    native.write_text("test executable placeholder")
    wrapper = tmp_path / "wrapper"
    wrapper.write_text("test wrapper placeholder")
    state = {"held": False, "released": False, "launches": 0, "fail_clone": False,
             "lock_refused": False, "residual_lock": False, "canonical_checks": 0}
    mutations = []

    class Manager:
        def __init__(self, config):
            pass

        @contextmanager
        def lock(self, resource, operation, timeout):
            assert resource == "edgemech" and timeout == 900
            if state["lock_refused"]:
                raise RuntimeError("lock refused")
            state["held"] = True
            try:
                yield
            finally:
                state["held"] = False
                state["released"] = True

        def check_lock(self, resource):
            return state["residual_lock"]

        def is_global_locked(self):
            return False

    class Target:
        path = tmp_path / "canonical"

        def open(self):
            state["canonical_checks"] += 1
            return SimpleNamespace(head=SimpleNamespace(commit=SimpleNamespace(hexsha="canonical")))

    settings = SimpleNamespace(
        from_environment=lambda **kw: SimpleNamespace(get_target=lambda key: Target())
    )
    monkeypatch.setitem(launcher.sys.modules, "plugins.lock_manager",
                        SimpleNamespace(LockManager=Manager))
    monkeypatch.setitem(launcher.sys.modules, "plugins.repository_settings", SimpleNamespace(
        RepositorySettings=settings, merged_repository_environment=lambda path: {}
    ))

    def run(argv, *, cwd=None):
        if "list-sessions" in argv:
            return "unrelated-session"
        if "list-panes" in argv:
            return "unrelated-session|%0|1|/unrelated"
        if argv[0] == "/usr/bin/file":
            return "Mach-O 64-bit executable arm64"
        if argv[-1] == "--help":
            return "--no-daemon"
        if argv[:3] == ["git", "rev-parse", "HEAD"]:
            return launcher.INITIAL_HEAD
        if argv[:4] == ["git", "remote", "get-url", "origin"]:
            return launcher.ORIGIN
        if argv[:2] == ["git", "status"]:
            return ""
        if argv[0] == "git":
            assert state["held"]
            mutations.append(argv)
            if argv[1] == "clone":
                if state["fail_clone"]:
                    raise RuntimeError("synthetic clone failure")
                Path(argv[-1]).mkdir()
            return ""
        if "new-session" in argv:
            assert not state["held"] and state["released"]
            assert "-N" in argv and "-A" not in argv
            assert "--no-daemon" in argv[argv.index("-c", argv.index("/bin/sh")) + 1]
            state["launches"] += 1
            return "%9001"
        raise AssertionError(argv)

    monkeypatch.setattr(launcher, "run", run)
    monkeypatch.setattr(launcher, "REQUEST_SHA", launcher.digest(campaign / "REQUEST.md"))
    monkeypatch.setattr(launcher.sys, "argv", ["launcher", "--claw-root", str(tmp_path),
        "--coordinator-root", str(coordinator), "--campaign-root", str(campaign),
        "--native", str(native), "--wrapper", str(wrapper),
        "--tmux-bin", str(tmp_path / "tmux"), "--tmux-socket", str(tmp_path / "socket"),
        "--session", "test-preparation"])
    return campaign, state, mutations


def test_launch_after_owned_context_releases_and_no_second_attempt(harness):
    campaign, state, mutations = harness
    launcher.main()
    assert state["launches"] == 1 and state["canonical_checks"] == 2
    assert (campaign / "preparation-launch-01/03-launch.json").is_file()
    count = len(mutations)
    with pytest.raises(SystemExit, match="retained preparation attempt"):
        launcher.main()
    assert len(mutations) == count and state["launches"] == 1


def test_clone_failure_preserves_receipt_and_releases_without_launch(harness):
    campaign, state, _ = harness
    state["fail_clone"] = True
    with pytest.raises(RuntimeError, match="synthetic clone failure"):
        launcher.main()
    assert state["released"] and not state["held"] and state["launches"] == 0
    assert "synthetic clone failure" in (campaign / "preparation-launch-01/02-failed.json").read_text()


def test_refused_lease_creates_no_clone_or_agent(harness):
    campaign, state, mutations = harness
    state["lock_refused"] = True
    with pytest.raises(RuntimeError, match="lock refused"):
        launcher.main()
    assert not mutations and state["launches"] == 0
    assert not (campaign / "preparation-worker-01").exists()
    assert (campaign / "preparation-launch-01/02-failed.json").is_file()


def test_residual_lock_blocks_agent_after_context_exit(harness):
    campaign, state, _ = harness
    state["residual_lock"] = True
    with pytest.raises(RuntimeError, match="lease still active"):
        launcher.main()
    assert state["launches"] == 0
    assert (campaign / "preparation-launch-01/02-lock-still-active.json").is_file()


def test_stage_receipt_refuses_overwrite_of_retained_attempt(tmp_path):
    path = launcher.receipt(tmp_path, "original", {"state": "failed"})
    original = path.read_bytes()
    with pytest.raises(FileExistsError):
        launcher.receipt(tmp_path, "original", {"state": "replacement"})
    assert path.read_bytes() == original
