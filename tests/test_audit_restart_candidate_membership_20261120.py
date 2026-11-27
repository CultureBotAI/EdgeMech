"""Synthetic exact-ID accounting; no actual census or scientific reviews."""

import hashlib
import importlib.util
import json
import os
import sys
from copy import deepcopy
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from kg_microbe_curation.identity import CurationError, occurrence_id

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "candidate_membership", ROOT / "scripts/adhoc/audit_restart_candidate_membership_20261120.py",
)
helper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def identity(source, position, raw):
    return occurrence_id(manifest_sha256=source["manifest_sha256"],
                         member=source["edge_member"],
                         member_sha256=source["edge_member_sha256"],
                         row_number=position, row_sha256=digest(raw))


def persist_partition(root, descriptor, rows, schema=None):
    path = root / descriptor["path"]
    pq.write_table(pa.Table.from_pylist(rows, schema=schema or helper.CENSUS_SCHEMA), path)
    raw = path.read_bytes()
    descriptor.update(sha256=digest(raw), bytes=len(raw))


@pytest.fixture
def data(tmp_path):
    source = {"manifest_sha256": "a" * 64, "edge_member_sha256": "b" * 64,
              "edge_member": "merged-kg_edges.tsv", "source_rows": 3, "selected_rows": 3,
              "complete_export": True, "limit": None, "selection": "initial_source_row_prefix"}
    rows = []
    # Identical raw rows must remain distinct by their exact source positions.
    for number, raw in enumerate([b"s\tp\to\n", b"s\tp\to\n", b"s2\tp2\to2\r\n"], 1):
        rows.append({"row_number": number, "occurrence_id": identity(source, number, raw),
                     "row_sha256": digest(raw), "source_row": raw,
                     "classification": "unmatched", "candidate_assertion_ids": [],
                     "eligible_assertion_ids": [], "endpoint_candidate_count": 0, "reasons": []})
    descriptors = [{"path": "one.parquet", "rows": 2, "first_row": 1, "last_row": 2},
                   {"path": "two.parquet", "rows": 1, "first_row": 3, "last_row": 3}]
    for descriptor, partition_rows in zip(descriptors, [rows[:2], rows[2:]], strict=True):
        persist_partition(tmp_path, descriptor, partition_rows)
    manifest = {"contract": helper.CENSUS_FORMAT, "independent_scientific_reviews": 0,
                "kg_occurrences_approved": 0, "source": source, "partitions": descriptors}
    ids = [row["occurrence_id"] for row in rows]
    return tmp_path, manifest, rows, ids


def test_exact_source_positions_survive_identical_spo_and_other_version_is_unseen(data):
    root, manifest, rows, ids = data
    other = identity({**manifest["source"], "manifest_sha256": "c" * 64}, 1,
                     rows[0]["source_row"])
    before = {p.name: p.read_bytes() for p in root.iterdir()}
    with (root / "progress.jsonl").open("x") as progress:
        result = helper.scan(root, manifest, [other, *ids], progress=progress)
    matches = result["matched_candidates"]
    assert len(matches) == 3 and {row["occurrence_id"] for row in matches} == set(ids)
    assert {row["row_number"] for row in matches} == {1, 2, 3}
    assert ids[0] != ids[1] and rows[0]["row_sha256"] == rows[1]["row_sha256"]
    assert result["ids_not_observed_in_scanned_partitions"] == [other]
    assert result["all_declared_partitions_scanned"] is True and result["rows_scanned"] == 3
    assert result["baseline_membership_qualified"] is False
    assert result["full_census_native_and_source_replay_verified"] is False
    assert result["full_target_frozen"] is False
    assert result["queue_A_count"] is None and result["queue_B_count"] is None
    assert result["scientific_review_coverage"] == 0
    assert [json.loads(line)["cumulative_rows"] for line in
            (root / "progress.jsonl").read_text().splitlines()] == [2, 3]
    assert all((root / name).read_bytes() == raw for name, raw in before.items())


def test_prefix_uses_exact_matching_but_cannot_claim_complete_membership(data):
    root, manifest, _, ids = data
    result = helper.scan(root, manifest, ids, max_partitions=1)
    assert result["all_declared_partitions_scanned"] is False
    assert result["rows_scanned"] == 2 and result["partitions_scanned"] == 1
    assert result["ids_not_observed_in_scanned_partitions"] == [ids[2]]
    assert result["baseline_membership_qualified"] is False


@pytest.mark.parametrize("bad", [[], ["not-an-id"], ["urn:kg-microbe:occurrence:v1:" + "A" * 64],
                                  [False], {"candidate_union_ids": []}])
def test_bad_candidate_shape_or_empty_input_is_not_silently_accepted(bad):
    with pytest.raises(ValueError):
        helper.candidate_ids(bad)


def test_duplicate_candidates_are_not_silently_deduplicated(data):
    _, _, _, ids = data
    with pytest.raises(ValueError, match="duplicate candidate"):
        helper.candidate_ids([ids[0], ids[0]])


@pytest.mark.parametrize("seconds", [0, -1, True, 1.5, float("nan"), float("inf"), 1801])
def test_invalid_or_unbounded_time_budget_refused_before_io(data, seconds, monkeypatch):
    root, manifest, _, ids = data
    monkeypatch.setattr(helper, "_read_handle", lambda _: pytest.fail("read before valid budget"))
    with pytest.raises(ValueError, match="deadline"):
        helper.scan(root, manifest, ids, seconds=seconds)


@pytest.mark.parametrize("limit", [0, -1, True, 1.2, 3])
def test_invalid_partition_limit_is_not_a_full_scan(data, limit):
    root, manifest, _, ids = data
    with pytest.raises(ValueError, match="partition limit"):
        helper.scan(root, manifest, ids, max_partitions=limit)


@pytest.mark.parametrize("field,value", [("complete_export", False), ("limit", 3),
                                          ("selection", "sample"), ("selected_rows", 2),
                                          ("source_rows", True), ("edge_member", "../edges.tsv")])
def test_incomplete_or_invalid_source_declarations_fail(data, field, value):
    root, manifest, _, ids = data
    manifest["source"][field] = value
    with pytest.raises((ValueError, CurationError)):
        helper.scan(root, manifest, ids)


@pytest.mark.parametrize("field,value", [("independent_scientific_reviews", 1),
                                          ("independent_scientific_reviews", False),
                                          ("kg_occurrences_approved", True)])
def test_declared_scientific_approval_or_boolean_zero_refused(data, field, value):
    root, manifest, _, ids = data
    manifest[field] = value
    with pytest.raises((ValueError, CurationError)):
        helper.scan(root, manifest, ids)


@pytest.mark.parametrize("field,value", [("rows", 1), ("first_row", True), ("last_row", 4),
                                          ("bytes", False), ("sha256", "f" * 64),
                                          ("path", "../one.parquet")])
def test_descriptor_tampering_rejected(data, field, value):
    root, manifest, _, ids = data
    manifest["partitions"][0][field] = value
    with pytest.raises((ValueError, CurationError)):
        helper.scan(root, manifest, ids)


def test_duplicate_partition_path_and_wrong_total_rejected(data):
    root, manifest, _, ids = data
    bad = deepcopy(manifest)
    bad["partitions"][1]["path"] = "one.parquet"
    with pytest.raises(ValueError, match="duplicate"):
        helper.scan(root, bad, ids)
    bad = deepcopy(manifest)
    bad["source"].update(source_rows=4, selected_rows=4)
    with pytest.raises(ValueError, match="complete partition count"):
        helper.scan(root, bad, ids)


@pytest.mark.parametrize("change", ["position", "raw", "row_hash", "occurrence", "schema", "count"])
def test_rehashed_partition_still_requires_row_positions_schema_and_exact_identity(data, change):
    root, manifest, rows, ids = data
    first = deepcopy(rows[:2])
    schema = None
    if change == "position":
        first[0]["row_number"] = 2
    elif change == "raw":
        first[0]["source_row"] = b"different\trow\tbytes\n"
    elif change == "row_hash":
        first[0]["row_sha256"] = "e" * 64
    elif change == "occurrence":
        first[0]["occurrence_id"] = ids[1]
    elif change == "schema":
        schema = pa.schema([("row_number", pa.int64())])
    else:
        first.pop()
    persist_partition(root, manifest["partitions"][0], first, schema)
    with pytest.raises(ValueError):
        helper.scan(root, manifest, ids)


@pytest.mark.parametrize("kind", ["symlink", "fifo"])
def test_nonregular_partition_is_refused(data, kind):
    root, manifest, _, ids = data
    original = root / "one.parquet"
    original.rename(root / "saved.parquet")
    if kind == "symlink":
        original.symlink_to(root / "saved.parquet")
    else:
        os.mkfifo(original)
    with pytest.raises(CurationError):
        helper.scan(root, manifest, ids)


def test_deadline_stops_before_partition_read(data, monkeypatch):
    root, manifest, _, ids = data
    ticks = iter([0, 2])
    monkeypatch.setattr(helper.time, "monotonic", lambda: next(ticks))
    monkeypatch.setattr(helper, "_read_handle", lambda _: pytest.fail("read beyond deadline"))
    with pytest.raises(TimeoutError):
        helper.scan(root, manifest, ids, seconds=1)


@pytest.mark.parametrize("content", [b'{"x":1,"x":2}', b'{"x":NaN}'])
def test_pinned_metadata_still_rejects_duplicate_keys_and_nonfinite_json(tmp_path, content):
    path = tmp_path / "bad.json"
    path.write_bytes(content)
    with pytest.raises(CurationError):
        helper.read_pinned(path, digest(content))


def test_wrong_metadata_pin_and_nonregular_metadata_refused(tmp_path):
    path = tmp_path / "input.json"
    path.write_bytes(b"[]")
    with pytest.raises(ValueError, match="pin mismatch"):
        helper.read_pinned(path, "f" * 64)
    path.unlink()
    os.mkfifo(path)
    with pytest.raises(CurationError):
        helper.read_pinned(path, "f" * 64)


@pytest.fixture
def cli(data, monkeypatch):
    root, manifest, _, ids = data
    monkeypatch.setattr(helper, "ROOT", root)
    monkeypatch.setattr(helper, "check_contracts", lambda: None)
    (root / ".temp").mkdir()
    census = root / "manifest.json"
    census.write_text(json.dumps(manifest))
    candidates = root / "candidates.json"
    candidates.write_text(json.dumps({"candidate_union_ids": ids, "private_note": "never copy"}))
    output = root / ".temp/attempt"
    argv = ["membership", "--census", str(census), "--census-sha256", digest(census.read_bytes()),
            "--candidates", str(candidates), "--candidates-sha256", digest(candidates.read_bytes()),
            "--candidate-field", "candidate_union_ids", "--results", str(output)]
    monkeypatch.setattr(sys, "argv", argv)
    return root, output, argv


def test_main_retains_pinned_plan_progress_result_and_refuses_second_invocation(cli):
    root, output, _ = cli
    helper.main()
    result = json.loads((output / "result.json").read_bytes())
    assert result["candidate_count"] == 3 and result["candidate_field"] == "candidate_union_ids"
    assert result["scientific_review_coverage"] == 0 and result["queue_A_count"] is None
    assert len((output / "partition-progress.jsonl").read_text().splitlines()) == 2
    assert "never copy" not in (output / "result.json").read_text()
    before = {p.name: p.read_bytes() for p in output.iterdir()}
    with pytest.raises(FileExistsError):
        helper.main()
    assert {p.name: p.read_bytes() for p in output.iterdir()} == before


@pytest.mark.parametrize("target", ["outside", "traversal", "symlink"])
def test_main_output_confinement_prevents_output_side_effects(cli, target, monkeypatch):
    root, output, argv = cli
    if target == "outside":
        chosen = root / "public"
    elif target == "traversal":
        chosen = root / ".temp/../public"
    else:
        (root / "elsewhere").mkdir()
        (root / ".temp/link").symlink_to(root / "elsewhere", target_is_directory=True)
        chosen = root / ".temp/link/attempt"
    argv[-1] = str(chosen)
    monkeypatch.setattr(helper, "read_pinned", lambda *_: pytest.fail("read before output validation"))
    with pytest.raises((ValueError, CurationError)):
        helper.main()
    assert not output.exists() and not (root / "public").exists()
    assert not (root / "elsewhere/attempt").exists()


def test_main_retains_failed_attempt_after_bad_pin(cli):
    _, output, argv = cli
    argv[argv.index("--census-sha256") + 1] = "f" * 64
    with pytest.raises(ValueError):
        helper.main()
    failure = json.loads((output / "failure.json").read_bytes())
    assert failure["status"] == "failed" and failure["error_type"] == "ValueError"
    assert not (output / "result.json").exists()


def test_main_retains_plan_and_failure_after_copy_or_result_failure(cli, monkeypatch):
    _, output, _ = cli
    original_write = helper.write_json

    def fail_result(path, value, **kwargs):
        if path.name == "result.json":
            raise OSError("injected result copy failure")
        return original_write(path, value, **kwargs)

    monkeypatch.setattr(helper, "write_json", fail_result)
    with pytest.raises(OSError, match="injected"):
        helper.main()
    assert (output / "plan.json").is_file() and (output / "partition-progress.jsonl").is_file()
    failure = json.loads((output / "failure.json").read_bytes())
    assert failure["error_type"] == "OSError" and not (output / "result.json").exists()


def test_main_retains_timeout_without_result(cli, monkeypatch):
    _, output, _ = cli

    def timeout(*args, **kwargs):
        raise TimeoutError("bounded scan exhausted")

    monkeypatch.setattr(helper, "scan", timeout)
    with pytest.raises(TimeoutError):
        helper.main()
    assert json.loads((output / "failure.json").read_bytes())["error_type"] == "TimeoutError"
    assert not (output / "result.json").exists()


@pytest.mark.parametrize("stage", ["parent_at_mkdir", "parent_before_open",
                                   "attempt_before_later_open", "attempt_before_failure"])
def test_replaced_output_directory_never_redirects_bytes(cli, monkeypatch, stage):
    root, output, _ = cli
    redirected = root / "redirected"
    redirected.mkdir()
    initial_entries = []
    if stage == "parent_before_open":
        (redirected / output.name).mkdir()
        initial_entries = [output.name]
    fired = False

    def replace():
        nonlocal fired
        if fired:
            return
        fired = True
        target = output.parent if stage.startswith("parent_") else output
        target.rename(root / "retained-original-directory")
        target.symlink_to(redirected, target_is_directory=True)

    original_mkdir, original_write, original_scan = os.mkdir, helper.write_json, helper.scan

    def mkdir(path, mode=0o777, *, dir_fd=None):
        if stage == "parent_at_mkdir" and os.fspath(path) in {str(output), output.name}:
            replace()
        return original_mkdir(path, mode, dir_fd=dir_fd)

    def write(path, value, **kwargs):
        trigger = {"parent_before_open": "plan.json",
                   "attempt_before_later_open": "result.json"}.get(stage)
        if path.name == trigger:
            replace()
        return original_write(path, value, **kwargs)

    def scan(*args, **kwargs):
        if stage == "attempt_before_failure":
            replace()
            raise OSError("injected scan failure after directory replacement")
        return original_scan(*args, **kwargs)

    monkeypatch.setattr(os, "mkdir", mkdir)
    monkeypatch.setattr(helper, "write_json", write)
    monkeypatch.setattr(helper, "scan", scan)
    with pytest.raises(Exception):
        helper.main()
    assert fired, "the replacement interleaving must actually run"
    entries = sorted(path.relative_to(redirected).as_posix() for path in redirected.rglob("*"))
    assert entries == initial_entries, "no output may enter the redirected destination"
