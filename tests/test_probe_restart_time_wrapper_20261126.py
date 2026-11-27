"""Synthetic wrapper controls cannot rewrite historical census outcomes."""

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "time_wrapper_probe", ROOT / "scripts/adhoc/probe_restart_time_wrapper_20261126.py",
)
helper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper)


@pytest.fixture
def setup(tmp_path, monkeypatch):
    monkeypatch.setattr(helper, "ROOT", tmp_path)
    (tmp_path / ".temp").mkdir()
    audit = tmp_path / "audit.json"
    audit.write_text(json.dumps({"census": {
        "actual_outer_exit_code": 1, "terminal_success_claimed": False,
        "native_child_exit_status_separately_observed": None,
        "result_json_equals_manifest": True,
        "independent_scientific_reviews": 0, "kg_occurrences_approved": 0,
        "terminal": {"actual_retained_item": {"status": "failed", "exit_code": 1,
                     "command": ["never-execute-a-command-from-this-audit"]}},
    }}))
    calls = []

    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, 1 if argv[0] == "/usr/bin/time" else 0,
                                           b"", helper.WARNING if len(argv) > 1 else b"")

    monkeypatch.setattr(helper.subprocess, "run", run)
    return audit, tmp_path / ".temp/results", calls


def execute(setup):
    audit, results, _ = setup
    return helper.probe(audit, helper.digest(audit.read_bytes()), results)


def test_fixed_controls_reuse_audit_and_preserve_failed_original(setup):
    audit, results, calls = setup
    original = audit.read_bytes()
    result = execute(setup)
    assert result["disposition"] == "TIMING_WRAPPER_WARNING_REPRODUCED_WITH_SYNTHETIC_TRUE"
    assert [argv for argv, _ in calls] == [("/usr/bin/true",),
                                          ("/usr/bin/time", "-l", "/usr/bin/true")]
    assert all(options["timeout"] == 15 and options["stdin"] == subprocess.DEVNULL
               for _, options in calls)
    report = json.loads((results / "receipt.json").read_bytes())
    assert report["original_outer_exit_code"] == 1 and report["original_child_exit_code"] is None
    assert report["metadata_audit_replayed"] is False and report["full_census_reverified"] is False
    assert report["original_full_replay_gate"] == "PENDING_INDEPENDENT_EVIDENCE_DISPOSITION"
    assert report["scientific_review_coverage"] == 0 and report["queue_A_count"] is None
    for outcome in report["outcomes"]:
        for channel in ("stdout", "stderr"):
            saved = (results / f'{outcome["name"]}.{channel}').read_bytes()
            assert outcome[channel] == {"sha256": helper.digest(saved), "bytes": len(saved)}
    assert audit.read_bytes() == original


def test_different_current_wrapper_outcome_never_rewrites_original(setup, monkeypatch):
    monkeypatch.setattr(helper.subprocess, "run", lambda argv, **kw:
                        subprocess.CompletedProcess(argv, 0, b"", b"resource report"))
    result = execute(setup)
    assert result["disposition"] == "CURRENT_WRAPPER_OUTCOME_DIFFERS_OR_IS_UNRESOLVED"
    assert result["original_outer_exit_code"] == 1 and result["original_child_exit_code"] is None


def test_timed_out_control_persists_partial_output_and_cli_fails(setup, monkeypatch):
    audit, results, _ = setup

    def timeout(argv, **kwargs):
        raise subprocess.TimeoutExpired(argv, 15, output=b"partial", stderr=b"diagnostic")

    monkeypatch.setattr(helper.subprocess, "run", timeout)
    monkeypatch.setattr(sys, "argv", ["probe", "--audit", str(audit), "--audit-sha256",
                                     helper.digest(audit.read_bytes()), "--results", str(results)])
    assert helper.main() == 1
    report = json.loads((results / "receipt.json").read_bytes())
    assert all(row["exit_code"] is None and row["error"] == "timeout" for row in report["outcomes"])
    assert (results / "direct_true.stdout").read_bytes() == b"partial"
    assert report["original_child_exit_code"] is None


def test_existing_attempt_never_runs_again_or_overwrites_bytes(setup):
    _, results, calls = setup
    execute(setup)
    before = {p.name: p.read_bytes() for p in results.iterdir()}
    with pytest.raises(FileExistsError):
        execute(setup)
    assert len(calls) == 2 and {p.name: p.read_bytes() for p in results.iterdir()} == before


def test_bad_audit_pin_prevents_any_probe_or_output(setup):
    audit, results, calls = setup
    with pytest.raises(ValueError, match="pin mismatch"):
        helper.probe(audit, "f" * 64, results)
    assert calls == [] and not results.exists()


@pytest.mark.parametrize(("key", "value"), [
    ("actual_outer_exit_code", 0), ("actual_outer_exit_code", True),
    ("terminal_success_claimed", True), ("native_child_exit_status_separately_observed", 0),
    ("result_json_equals_manifest", False), ("independent_scientific_reviews", 1),
    ("kg_occurrences_approved", False),
])
def test_audit_cannot_promote_unknown_exit_or_scientific_counts(setup, key, value):
    audit, results, calls = setup
    data = json.loads(audit.read_bytes())
    data["census"][key] = value
    audit.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        execute(setup)
    assert calls == [] and not results.exists()


def test_duplicate_audit_keys_refused_before_probe(setup):
    audit, results, calls = setup
    audit.write_text('{"census":{},"census":{}}')
    with pytest.raises(ValueError, match="Duplicate JSON key"):
        execute(setup)
    assert calls == [] and not results.exists()


def test_nonregular_audit_does_not_block_or_probe(setup):
    audit, results, calls = setup
    audit.unlink()
    os.mkfifo(audit)
    with pytest.raises(ValueError):
        helper.probe(audit, "a" * 64, results)
    assert calls == [] and not results.exists()


@pytest.mark.parametrize("kind", ["traversal", "symlink"])
def test_output_escape_refused_without_side_effects(setup, kind):
    audit, results, calls = setup
    outside = results.parents[1] / "outside"
    outside.mkdir()
    if kind == "traversal":
        results = results.parent / ".." / "outside" / "new"
    else:
        link = results.parent / "link"
        link.symlink_to(outside, target_is_directory=True)
        results = link / "new"
    with pytest.raises(ValueError):
        helper.probe(audit, helper.digest(audit.read_bytes()), results)
    assert calls == [] and list(outside.iterdir()) == []


def test_receipt_failure_preserves_attempt_without_success_or_retry(setup, monkeypatch):
    _, results, calls = setup
    save = helper.save

    def fail_receipt(path, raw, **kwargs):
        if path.name == "receipt.json":
            raise OSError("injected receipt failure")
        return save(path, raw, **kwargs)

    monkeypatch.setattr(helper, "save", fail_receipt)
    with pytest.raises(OSError, match="injected receipt failure"):
        execute(setup)
    assert not (results / "receipt.json").exists()
    assert len(list(results.iterdir())) == 4 and len(calls) == 2
    with pytest.raises(FileExistsError):
        execute(setup)
    assert len(calls) == 2


@pytest.mark.parametrize("kind", ["timeout", "launch_error"])
def test_timed_only_failure_is_nonzero_and_preserves_both_outcomes(setup, monkeypatch, kind):
    audit, results, _ = setup

    def run(argv, **kwargs):
        if argv[0] == "/usr/bin/true":
            return subprocess.CompletedProcess(argv, 0, b"direct", b"")
        if kind == "timeout":
            raise subprocess.TimeoutExpired(argv, 15, output=b"timed partial", stderr=b"diagnostic")
        raise OSError("injected timed launch failure")

    monkeypatch.setattr(helper.subprocess, "run", run)
    monkeypatch.setattr(sys, "argv", ["probe", "--audit", str(audit), "--audit-sha256",
                                     helper.digest(audit.read_bytes()), "--results", str(results)])
    code = helper.main()
    report = json.loads((results / "receipt.json").read_bytes())
    direct, timed = report["outcomes"]
    assert direct["exit_code"] == 0 and direct["error"] is None
    assert timed["exit_code"] is None
    assert timed["error"] == ("timeout" if kind == "timeout" else "OSError")
    assert (results / "direct_true.stdout").read_bytes() == b"direct"
    assert (results / "timed_true.stdout").read_bytes() == (
        b"timed partial" if kind == "timeout" else b"")
    assert report["original_outer_exit_code"] == 1 and report["original_child_exit_code"] is None
    assert code == 1, "a timed-only missing terminal must not return CLI success"
    assert report["disposition"] == "SYNTHETIC_CONTROL_FAILED_OR_TIMED_OUT"


@pytest.mark.parametrize("timed_exit", [0, 2, -9])
def test_completed_timed_exit_is_distinct_from_missing_terminal(setup, monkeypatch, timed_exit):
    audit, results, _ = setup
    monkeypatch.setattr(helper.subprocess, "run", lambda argv, **kw:
                        subprocess.CompletedProcess(argv, 0 if len(argv) == 1 else timed_exit,
                                                    b"", b"observed current outcome"))
    monkeypatch.setattr(sys, "argv", ["probe", "--audit", str(audit), "--audit-sha256",
                                     helper.digest(audit.read_bytes()), "--results", str(results)])
    assert helper.main() == 0
    report = json.loads((results / "receipt.json").read_bytes())
    assert report["outcomes"][1]["exit_code"] == timed_exit
    assert report["outcomes"][1]["error"] is None
    assert report["disposition"] == "CURRENT_WRAPPER_OUTCOME_DIFFERS_OR_IS_UNRESOLVED"


@pytest.mark.parametrize("stage", ["parent_at_mkdir", "parent_before_open",
                                   "attempt_before_later_open", "attempt_before_receipt"])
def test_replaced_output_directory_never_redirects_bytes(setup, monkeypatch, stage):
    _, results, _ = setup
    root = results.parents[1]
    redirected = root / "redirected"
    redirected.mkdir()
    initial_entries = []
    if stage == "parent_before_open":
        (redirected / results.name).mkdir()
        initial_entries = [results.name]
    fired = False

    def replace():
        nonlocal fired
        if fired:
            return
        fired = True
        target = results.parent if stage.startswith("parent_") else results
        target.rename(root / "retained-original-directory")
        target.symlink_to(redirected, target_is_directory=True)

    original_mkdir, original_save = os.mkdir, helper.save

    def mkdir(path, mode=0o777, *, dir_fd=None):
        if stage == "parent_at_mkdir" and os.fspath(path) in {str(results), results.name}:
            replace()
        return original_mkdir(path, mode, dir_fd=dir_fd)

    def save(path, raw, **kwargs):
        trigger = {"parent_before_open": "direct_true.stdout",
                   "attempt_before_later_open": "timed_true.stdout",
                   "attempt_before_receipt": "receipt.json"}.get(stage)
        if path.name == trigger:
            replace()
        return original_save(path, raw, **kwargs)

    monkeypatch.setattr(os, "mkdir", mkdir)
    monkeypatch.setattr(helper, "save", save)
    with pytest.raises(Exception):
        execute(setup)
    assert fired, "the replacement interleaving must actually run"
    entries = sorted(path.relative_to(redirected).as_posix() for path in redirected.rglob("*"))
    assert entries == initial_entries, "no output may enter the redirected destination"
