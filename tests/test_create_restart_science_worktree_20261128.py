"""Offline mutation-boundary checks for the prospective #228/#238 producer."""

import importlib.util
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest

SPEC = importlib.util.spec_from_file_location(
    "science_worktree", Path(__file__).parents[1]
    / "scripts/adhoc/create_restart_science_worktree_20261128.py")
helper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper)


@pytest.fixture
def setup(tmp_path, monkeypatch):
    owner = tmp_path / "owner"
    campaign = owner / ".temp/restart-20261120"
    campaign.mkdir(parents=True)
    claw = tmp_path / "claw"
    claw.mkdir()
    args = SimpleNamespace(owner=owner, claw=claw, destination=campaign / "science",
                           output=campaign / "attempt", expected_head="1" * 40,
                           base="2" * 40, branch="campaign/science", apply=True)
    state = {"owner": args.expected_head, "canonical": "3" * 40, "writes": 0,
             "release": False, "refuse": False, "change": None, "fail_copy": False}

    def git(root, *cmd):
        if cmd == ("remote", "get-url", "origin"):
            return helper.ORIGIN
        if cmd == ("rev-parse", "HEAD"):
            return state["owner"] if root == owner else args.base
        if cmd == ("rev-parse", args.base + "^{commit}"):
            return args.base
        if cmd[:2] == ("worktree", "add"):
            state["writes"] += 1
            args.destination.mkdir()
            if state["fail_copy"]:
                raise OSError("injected checkout failure")
            return ""
        if cmd == ("status", "--porcelain"):
            return ""
        raise AssertionError(cmd)

    @contextmanager
    def lock(*_args, **_kwargs):
        if state["refuse"]:
            raise RuntimeError("lease refused")
        if state["change"]:
            state[state["change"]] = "4" * 40
        try:
            yield
        finally:
            state["release"] = True

    target = SimpleNamespace(open=lambda: SimpleNamespace(
        head=SimpleNamespace(commit=SimpleNamespace(hexsha=state["canonical"]))))
    monkeypatch.setattr(helper, "git", git)
    monkeypatch.setattr(helper, "LockManager", lambda: SimpleNamespace(lock=lock))
    monkeypatch.setattr(helper, "merged_repository_environment", lambda _path: {})
    monkeypatch.setattr(helper, "RepositorySettings", SimpleNamespace(
        from_environment=lambda **_kw: SimpleNamespace(get_target=lambda _key: target)))
    monkeypatch.setenv("OPENCLAW_ORCHESTRATION_ROOT", str(claw))
    return args, state


def test_plan_does_not_create_attempt_or_worktree(setup):
    args, state = setup
    args.apply = False
    assert helper.create(args)["mutation"] is False
    assert not args.output.exists() and not args.destination.exists()
    assert state["writes"] == 0


@pytest.mark.parametrize("boundary", ["lease", "owner", "canonical"])
def test_mutation_requires_lease_and_unchanged_owners(setup, boundary):
    args, state = setup
    if boundary == "lease":
        state["refuse"] = True
    else:
        state["change"] = boundary
    with pytest.raises((ValueError, RuntimeError)):
        helper.create(args)
    assert state["writes"] == 0 and not args.destination.exists()
    assert (args.output / "failure.json").is_file()
    if boundary != "lease":
        assert state["release"]


def test_failed_copy_releases_lease_preserves_attempt_and_refuses_retry(setup):
    args, state = setup
    state["fail_copy"] = True
    with pytest.raises(OSError, match="injected"):
        helper.create(args)
    assert state["release"] and state["writes"] == 1
    assert args.destination.is_dir() and (args.output / "failure.json").is_file()
    before = (args.output / "failure.json").read_bytes()
    with pytest.raises(ValueError, match="attempt exists"):
        helper.create(args)
    assert state["writes"] == 1
    assert (args.output / "failure.json").read_bytes() == before


def test_success_is_scoped_to_empty_worktree_and_releases_lease(setup):
    args, state = setup
    result = helper.create(args)
    assert result["status"] == "created" and state["release"]
    assert result["scientific_review_coverage"] == 0
    assert result["worker_input"] is False and result["canonical_save"] is False
    assert (args.output / "completion.json").is_file()
