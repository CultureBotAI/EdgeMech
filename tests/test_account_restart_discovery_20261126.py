"""Saved references preserve multiplicity and never qualify or reopen source rows."""

import importlib.util
import json
import os
import sys
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "discovery_account", ROOT / "scripts/adhoc/account_restart_discovery_20261126.py",
)
helper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper)
A, B, C = "a" * 64, "b" * 64, "c" * 64


def artifact(tmp_path, name, raw):
    path = tmp_path / name
    path.write_bytes(raw)
    return {"label": name.replace(".", "-"), "path": str(path), "sha256": helper.sha(raw)}


def invoke(tmp_path, inventories, scopes=(), **kwargs):
    manifest = {"version": 1, "inventories": inventories, "scopes": list(scopes)}
    path = tmp_path / "manifest.json"
    raw = json.dumps(manifest).encode()
    path.write_bytes(raw)
    return helper.account(path, helper.sha(raw), **kwargs)


def inventory(tmp_path, raw, encoding="sha256-lines", name="inventory"):
    return {**artifact(tmp_path, name, raw), "encoding": encoding}


def scope(tmp_path, raw, encoding="json-array", field="sha256", kind="structural_projection"):
    return {**artifact(tmp_path, "scope", raw), "encoding": encoding,
            "field": field, "asserted_kind": kind}


def test_multiplicity_cross_inventory_drift_and_missing_scope_are_distinct(tmp_path, monkeypatch):
    first = inventory(tmp_path, f"{A}  /never-open/row.json\n{A}  /never-open/row.json\n".encode())
    second = inventory(tmp_path, f"{B}  /never-open/row.json\0{A}  /never-open/other.tsv\0".encode(),
                       "sha256-nul", "second")
    evidence = scope(tmp_path, json.dumps([{"sha256": A}, {"sha256": C}]).encode())
    original = helper._read_handle

    def guarded(path):
        assert str(path).startswith(str(tmp_path))  # Inventory source locators must never be opened.
        return original(path)

    monkeypatch.setattr(helper, "_read_handle", guarded)
    result = invoke(tmp_path, [first, second], [evidence])
    assert result["inventory_records"] == 4
    assert result["distinct_inventoried_hashes"] == 2
    assert result["hashes_with_scope_reference"] == result["hashes_without_scope_reference"] == 1
    assert result["variants"][0]["inventory_counts"] == {"inventory": 2, "second": 1}
    assert result["scope_hashes_absent_from_inventories"][0]["sha256"] == C
    assert result["conflicting_locator_bindings"] == [
        {"locator_sha256": helper.sha(b"/never-open/row.json"), "content_sha256s": [A, B]}]
    assert "/never-open" not in json.dumps(result)
    assert result["scientific_review_coverage"] == 0
    assert result["queue_A_count"] is result["queue_B_count"] is None
    assert result["full_target_frozen"] is False
    assert result["baseline_cutoff_frozen"] is False


def test_escaped_lines_and_raw_nul_names_preserve_same_locator_identity():
    escaped = f"\\{A}  /private/line\\nback\\\\tab\tfile.json\n".encode()
    plain = A.encode() + b"  /private/line\nback\\tab\tfile.json\0"
    left = list(helper.inventory_rows(escaped, "sha256-lines", helper.Budget()))
    right = list(helper.inventory_rows(plain, "sha256-nul", helper.Budget()))
    assert left == right
    assert left[0][1] == b"/private/line\nback\\tab\tfile.json"


@pytest.mark.parametrize("raw", [
    f"{A}  /row".encode(), f"{A}  relative\n".encode(), f"{A} /row\n".encode(),
    f"\\{A}  /bad\\q\n".encode(), f"{A}  /row\n\n".encode(), b"z" * 64 + b"  /row\n",
    A.encode() + b"  /nul\0value\n", A.encode() + b"  /bad\xff\n",
])
def test_malformed_inventory_never_silently_drops_a_record(raw):
    with pytest.raises((ValueError, UnicodeError)):
        list(helper.inventory_rows(raw, "sha256-lines", helper.Budget()))


@pytest.mark.parametrize("encoding,raw", [
    ("json-array", b'[{"sha256":{"private_prose":"never stringify"}}]'),
    ("json-array", b'[{"note":"missing direct hash"}]'),
    ("jsonl", b'{"sha256":"' + A.encode() + b'"}'),
    ("jsonl", b'{"sha256":"' + A.encode() + b'"}\n\n'),
    ("json-object", b'{"sha256":"' + A.encode() + b'","sha256":"' + B.encode() + b'"}'),
])
def test_nested_missing_duplicate_or_incomplete_scope_refused(encoding, raw):
    with pytest.raises(ValueError):
        list(helper.scope_rows(raw, encoding, "sha256", helper.Budget()))


@pytest.mark.parametrize("encoding", ["json-array", "jsonl", "json-object"])
def test_scope_encodings_preserve_repeated_references_without_qualification(tmp_path, encoding):
    row = {"bundle_sha256": A, "scientific_review_coverage": 999, "verdict": "pass"}
    raw = json.dumps([row, row]).encode() if encoding == "json-array" else json.dumps(row).encode()
    if encoding == "jsonl":
        raw = raw + b"\n" + raw + b"\n"
    source = inventory(tmp_path, f"{A}  /unopened/file.yaml\n".encode())
    evidence = scope(tmp_path, raw, encoding, "bundle_sha256", "reference_only")
    result = invoke(tmp_path, [source], [evidence])
    assert result["inputs"][1]["rows"] == (1 if encoding == "json-object" else 2)
    assert result["inputs"][1]["asserted_kind"] == "reference_only"
    assert result["variants"][0]["scope_references"] == ["scope"]
    assert result["scientific_review_coverage"] == 0


def test_changed_artifact_pin_refuses_before_output(tmp_path):
    entry = inventory(tmp_path, f"{A}  /unopened/file\n".encode())
    Path(entry["path"]).write_bytes(f"{B}  /unopened/file\n".encode())
    with pytest.raises(ValueError, match="hash mismatch"):
        invoke(tmp_path, [entry])


@pytest.mark.parametrize("encoding,delimiter", [("sha256-lines", "\n"), ("sha256-nul", "\0")])
def test_saved_hash_receipt_is_a_repeated_reference_not_an_open_or_qualification(
    tmp_path, monkeypatch, encoding, delimiter,
):
    source = inventory(tmp_path, f"{A}  /unopened/source.sqlite\n".encode())
    raw = (f"{A}  /unopened/source.sqlite{delimiter}" * 2).encode()
    evidence = scope(tmp_path, raw, encoding, "sha256", "reference_only")
    original = helper._read_handle

    def guarded(path):
        assert str(path).startswith(str(tmp_path))
        return original(path)

    monkeypatch.setattr(helper, "_read_handle", guarded)
    result = invoke(tmp_path, [source], [evidence])
    assert result["inputs"][1]["rows"] == 2
    assert result["inputs"][1]["asserted_kind"] == "reference_only"
    assert result["hashes_with_scope_reference"] == 1
    assert result["scientific_review_coverage"] == 0
    assert "/unopened" not in json.dumps(result)
    with pytest.raises(ValueError, match="requires sha256"):
        list(helper.scope_rows(raw, encoding, "bundle_sha256", helper.Budget()))


def test_duplicate_labels_and_unknown_manifest_fields_refused(tmp_path):
    entry = inventory(tmp_path, f"{A}  /unopened/file\n".encode())
    with pytest.raises(ValueError, match="duplicate label"):
        invoke(tmp_path, [entry, entry])
    entry["qualification"] = "approved"
    with pytest.raises(ValueError, match="entry fields"):
        invoke(tmp_path, [entry])


def test_byte_row_and_time_bounds_are_enforced(tmp_path, monkeypatch):
    path = tmp_path / "input"
    path.write_bytes(b"12345")
    with pytest.raises(ValueError, match="byte bound"):
        helper.read_pinned(str(path), helper.sha(b"12345"), helper.Budget(), 4)
    monkeypatch.setattr(helper, "MAX_ROWS", 1)
    with pytest.raises(ValueError, match="aggregate bound"):
        list(helper.inventory_rows(f"{A}  /one\n{A}  /two\n".encode(), "sha256-lines", helper.Budget()))
    budget = helper.Budget()
    budget.deadline = -1
    with pytest.raises(ValueError, match="deadline"):
        helper.read_pinned(str(path), helper.sha(b"12345"), budget)


@pytest.mark.parametrize("kind", ["symlink", "fifo", "directory"])
def test_nonregular_metadata_refused_without_blocking(tmp_path, kind):
    path = tmp_path / "input"
    if kind == "symlink":
        (tmp_path / "actual").write_bytes(b"[]")
        path.symlink_to(tmp_path / "actual")
    elif kind == "fifo":
        os.mkfifo(path)
    else:
        path.mkdir()
    with pytest.raises((ValueError, OSError)):
        helper.read_pinned(str(path), helper.sha(b"[]"), helper.Budget())


def test_exclusive_publication_allows_only_one_concurrent_writer(tmp_path):
    path = tmp_path / "result.json"
    barrier = threading.Barrier(2)
    outcomes = []

    def write(value):
        barrier.wait()
        try:
            outcomes.append(("written", helper.publish(path, {"value": value})))
        except FileExistsError:
            outcomes.append(("refused", None))

    threads = [threading.Thread(target=write, args=(value,)) for value in (1, 2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)
        assert not thread.is_alive()
    assert sorted(result[0] for result in outcomes) == ["refused", "written"]
    assert json.loads(path.read_bytes())["value"] in (1, 2)
    assert next(value for status, value in outcomes if status == "written") == helper.sha(path.read_bytes())


@pytest.mark.parametrize("failure_call", [1, 2])
def test_publication_fsync_failure_preserves_attempt_without_retry(tmp_path, monkeypatch, failure_call):
    path = tmp_path / "result.json"
    original_fsync = helper.os.fsync
    calls = 0

    def fail_at_selected_flush(descriptor):
        nonlocal calls
        calls += 1
        if calls == failure_call:
            raise OSError("injected")
        return original_fsync(descriptor)

    monkeypatch.setattr(helper.os, "fsync", fail_at_selected_flush)
    with pytest.raises(OSError, match="injected"):
        helper.publish(path, {"attempt": 1})
    assert path.exists()
    before = path.read_bytes()
    with pytest.raises(FileExistsError):
        helper.publish(path, {"attempt": 2})
    assert path.read_bytes() == before


def test_symlink_output_parent_refused_before_creation(tmp_path):
    (tmp_path / "real").mkdir()
    (tmp_path / "linked").symlink_to(tmp_path / "real", target_is_directory=True)
    with pytest.raises(ValueError, match="output parent"):
        helper.publish(tmp_path / "linked" / "result.json", {})
    assert not (tmp_path / "real" / "result.json").exists()


def test_parent_replaced_by_symlink_at_open_cannot_redirect_publication(tmp_path, monkeypatch):
    anchor, outside, held = tmp_path / "anchor", tmp_path / "outside", tmp_path / "held"
    parent = anchor / "leaf"
    parent.mkdir(parents=True)
    (outside / "leaf").mkdir(parents=True)
    original_open = helper.os.open
    switched = False

    def replace_at_open(path, *args, **kwargs):
        nonlocal switched
        if not switched and str(path) in (str(parent), "anchor"):
            anchor.rename(held)
            anchor.symlink_to(outside, target_is_directory=True)
            switched = True
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(helper.os, "open", replace_at_open)
    with pytest.raises(ValueError, match="output parent"):
        helper.publish(parent / "result.json", {"private": "fixture"})
    assert switched
    assert not (outside / "leaf" / "result.json").exists()
    assert not (held / "leaf" / "result.json").exists()


def test_main_checks_source_pin_and_publishes_only_complete_accounting(tmp_path, monkeypatch, capsys):
    entry = inventory(tmp_path, f"{A}  /unopened/fixture.json\n".encode())
    manifest = {"version": 1, "inventories": [entry], "scopes": []}
    raw = json.dumps(manifest).encode()
    path = tmp_path / "manifest.json"
    path.write_bytes(raw)
    output = tmp_path / "result.json"
    argv = [str(SPEC.origin), "--manifest", str(path), "--manifest-sha256", helper.sha(raw),
            "--helper-sha256", "0" * 64, "--output", str(output)]
    monkeypatch.setattr(sys, "argv", argv)
    with pytest.raises(ValueError, match="hash mismatch"):
        helper.main()
    assert not output.exists()
    argv[6] = helper.sha(Path(SPEC.origin).read_bytes())
    helper.main()
    receipt = json.loads(capsys.readouterr().out)
    result = json.loads(output.read_bytes())
    assert receipt["output_sha256"] == helper.sha(output.read_bytes())
    assert result["producer_sha256"] == argv[6]
    assert result["hashes_without_scope_reference"] == 1
    assert result["scientific_review_coverage"] == 0
