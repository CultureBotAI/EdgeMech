"""Preparation metadata writes preserve old bytes and refuse changed ownership."""

import importlib.util
import json
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "restart_checkpoint", ROOT / "scripts/adhoc/checkpoint_restart_20261126.py",
)
helper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper)


@pytest.fixture
def campaign(tmp_path):
    root = tmp_path / "campaign"
    root.mkdir()
    (root / "coordinator-checkpoints").mkdir()
    state = {"scientific_review_coverage": 0, "queue_A_count": None, "queue_B_count": None,
             "full_target_frozen": False, "note": "original"}
    (root / "COORDINATOR-PROGRESS.json").write_text(json.dumps(state))
    return root


def invoke(root, updates, name="checkpoint01", expected=None):
    path = root / "updates.json"
    path.write_text(json.dumps(updates))
    current = root / "COORDINATOR-PROGRESS.json"
    return helper.checkpoint(root, current.name, expected or helper.sha(current.read_bytes()),
                             path, name)


def test_checkpoint_preserves_exact_before_and_current_readback(campaign):
    current = campaign / "COORDINATOR-PROGRESS.json"
    original = current.read_bytes()
    receipt = invoke(campaign, {"note": "recovered", "census_child_exit": None})
    saved = campaign / "coordinator-checkpoints"
    assert (saved / "checkpoint01-before.json").read_bytes() == original
    assert current.read_bytes() == (saved / "checkpoint01.json").read_bytes()
    assert receipt["checkpoint_sha256"] == helper.sha(current.read_bytes())
    after = json.loads(current.read_bytes())
    assert after["note"] == "recovered" and after["census_child_exit"] is None
    assert after["checkpoint_producer"]["historical_execution_recreated"] is False
    assert after["checkpoint_producer"]["sha256"] == helper.sha(Path(helper.__file__).read_bytes())
    with pytest.raises(FileExistsError):
        invoke(campaign, {"note": "must not overwrite"})
    assert current.read_bytes() == (saved / "checkpoint01.json").read_bytes()


@pytest.mark.parametrize("updates", [
    {"scientific_review_coverage": 1}, {"scientific_review_coverage": False},
    {"queue_A_count": 1}, {"B_count": 1}, {"full_target_frozen": True},
    {"full_AB_frozen": True}, {"baseline_cutoff_frozen": True},
])
def test_scientific_gate_updates_refused_before_any_checkpoint(campaign, updates):
    original = (campaign / "COORDINATOR-PROGRESS.json").read_bytes()
    with pytest.raises(ValueError, match="scientific gates"):
        invoke(campaign, updates)
    assert (campaign / "COORDINATOR-PROGRESS.json").read_bytes() == original
    assert list((campaign / "coordinator-checkpoints").iterdir()) == []


def test_wrong_prior_pin_refuses_all_output(campaign):
    with pytest.raises(ValueError, match="current state changed"):
        invoke(campaign, {}, expected="0" * 64)
    assert list((campaign / "coordinator-checkpoints").iterdir()) == []


@pytest.mark.parametrize("bad_name", ["../outside", "sub/path", "", "x" * 97])
def test_checkpoint_name_cannot_escape_owned_directory(campaign, bad_name):
    with pytest.raises(ValueError, match="checkpoint name"):
        invoke(campaign, {}, name=bad_name)
    assert list((campaign / "coordinator-checkpoints").iterdir()) == []


def test_root_owned_rollup_cannot_be_updated(campaign):
    with pytest.raises(ValueError, match="owned state"):
        helper.checkpoint(campaign, "progress.json", "0" * 64, campaign / "missing", "new")


def test_snapshot_directory_symlink_refuses_without_touching_outside(campaign, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    snapshots = campaign / "coordinator-checkpoints"
    snapshots.rmdir()
    snapshots.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="nonsymlink"):
        invoke(campaign, {})
    assert list(outside.iterdir()) == []


def test_concurrent_state_change_retains_evidence_and_new_owner_bytes(campaign, monkeypatch):
    current = campaign / "COORDINATOR-PROGRESS.json"
    exclusive = helper.exclusive

    def replaced_owner(path, raw):
        exclusive(path, raw)
        if path.name.endswith(".pending"):
            current.write_text('{"new_owner":true}')

    monkeypatch.setattr(helper, "exclusive", replaced_owner)
    with pytest.raises(ValueError, match="changed during checkpoint"):
        invoke(campaign, {"note": "ours"})
    assert current.read_text() == '{"new_owner":true}'
    assert (campaign / ".checkpoint01.pending").is_file()
    assert (campaign / "coordinator-checkpoints/checkpoint01-before.json").is_file()


def test_concurrent_writer_refused_between_comparison_and_replace(campaign, monkeypatch):
    current = campaign / "COORDINATOR-PROGRESS.json"
    original = current.read_bytes()
    first_updates = campaign / "first-updates.json"
    first_updates.write_text('{"note":"first"}')
    at_replace, release_first = threading.Event(), threading.Event()
    outcomes = []
    replace = helper.os.replace

    def wait_before_replace(source, destination):
        if source.name == ".first.pending":
            at_replace.set()
            if not release_first.wait(5):
                raise TimeoutError("bounded concurrency test")
        replace(source, destination)

    def first():
        try:
            outcomes.append(helper.checkpoint(campaign, current.name, helper.sha(original),
                                               first_updates, "first"))
        except BaseException as error:
            outcomes.append(error)

    monkeypatch.setattr(helper.os, "replace", wait_before_replace)
    thread = threading.Thread(target=first)
    thread.start()
    try:
        assert at_replace.wait(5), "first writer never reached replacement boundary"
        with pytest.raises(RuntimeError, match="acquire lock"):
            invoke(campaign, {"note": "second"}, name="second", expected=helper.sha(original))
        assert current.read_bytes() == original
        assert not (campaign / "coordinator-checkpoints/second-before.json").exists()
    finally:
        release_first.set()
        thread.join(5)
    assert not thread.is_alive() and len(outcomes) == 1
    assert isinstance(outcomes[0], dict), outcomes
    assert json.loads(current.read_bytes())["note"] == "first"
    # Once the first lease releases, its old expected state still cannot be reused.
    with pytest.raises(ValueError, match="current state changed"):
        invoke(campaign, {}, name="stale", expected=helper.sha(original))
    invoke(campaign, {"note": "fresh"}, name="fresh")
    assert json.loads(current.read_bytes())["note"] == "fresh"


def test_write_failure_releases_only_its_context(campaign, monkeypatch):
    exclusive = helper.exclusive

    def failed_write(path, raw):
        raise OSError("injected copy failure")

    monkeypatch.setattr(helper, "exclusive", failed_write)
    with pytest.raises(OSError, match="injected copy failure"):
        invoke(campaign, {}, name="failed")
    monkeypatch.setattr(helper, "exclusive", exclusive)
    invoke(campaign, {"note": "context released"}, name="afterfailure")
    assert json.loads((campaign / "COORDINATOR-PROGRESS.json").read_text())["note"] == "context released"


def test_duplicate_update_keys_refused_and_context_released(campaign):
    updates = campaign / "duplicate-updates.json"
    updates.write_text('{"note":"first","note":"second"}')
    current = campaign / "COORDINATOR-PROGRESS.json"
    original = current.read_bytes()
    with pytest.raises(ValueError, match="Duplicate JSON key"):
        helper.checkpoint(campaign, current.name, helper.sha(original), updates, "duplicate")
    assert current.read_bytes() == original
    assert list((campaign / "coordinator-checkpoints").iterdir()) == []
    invoke(campaign, {"note": "released"}, name="afterduplicate")
