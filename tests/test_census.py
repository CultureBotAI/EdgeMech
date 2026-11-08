"""Synthetic transport conformance; no fixture grants scientific approval."""

import gc
import hashlib
import json
import os
import stat
from copy import deepcopy
from io import BytesIO
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from kg_microbe_curation.identity import CurationError, canonical_json, occurrence_id, sha256_json
from kg_microbe_curation.native import NATIVE_CONTRACT, native_assertion_id

from edgemech import census
from edgemech.census import CENSUS_SCHEMA, run_census, verify_census


def native_assertion(*, status="supported", alternative=False):
    locator = {"repository": "Example/FixtureMech", "commit": "a" * 40,
               "path": "native/mappings.tsv", "selector": {"row": 1 if not alternative else 2}}
    review = {**locator, "path": "native/review.json"}
    original = {"subject": "Fixture:1", "predicate": "skos:exactMatch", "object": "CHEBI:1",
                "condition": "synthetic second condition" if alternative else "synthetic condition"}
    decision = {"status": status, "reason": "Synthetic native fixture only"}
    item = {
        "contract": NATIVE_CONTRACT,
        "native_locator": {**locator, "source_sha256": "b" * 64,
                           "payload_sha256": sha256_json(original)},
        "payload": {"subject": "Fixture:1", "predicate": "skos:exactMatch", "object": "CHEBI:1",
                    "context": {"scope": "native_mapping_payload_only"},
                    "interpretation": {"normalization_contract": "fixture-exact/v1",
                                       "normalizer_contract_sha256": "c" * 64,
                                       "schema_sha256": "d" * 64, "prefix_map_sha256": "e" * 64},
                    "native_payload": original},
        "evidence": [
            {"evidence_id": "source", "locator": locator, "sha256": "b" * 64, "ancestry": ["shared"]},
            {"evidence_id": "review", "locator": review, "sha256": "f" * 64, "ancestry": ["shared"]},
        ],
        "native_review": {"status": status, "locator": review, "sha256": "f" * 64,
                          "payload": decision, "payload_sha256": sha256_json(decision),
                          "rationale": "Inherited synthetic scope"},
        "assurance": {"supported": "inherited_native_review", "withheld": "native_withheld_decision",
                      "unassessed": "unassessed"}[status],
        "limitations": ["Synthetic transport conformance only; no KG scientific review."],
        "independent_scientific_review": False,
    }
    item["assertion_id"] = native_assertion_id(item)
    return item


def export_native(path, assertions):
    path.mkdir()
    data = b"".join(canonical_json(item) + b"\n" for item in assertions)
    counts = {}
    for item in assertions:
        status = item["native_review"]["status"]
        counts[status] = counts.get(status, 0) + 1
    manifest = {"schema_version": 1, "contract": NATIVE_CONTRACT,
                "source_commit": "a" * 40, "rows": len(assertions), "native_status_counts": counts,
                "assertions_sha256": hashlib.sha256(data).hexdigest(), "assertions_bytes": len(data),
                "independent_scientific_reviews": 0, "kg_occurrences_approved": 0}
    (path / "assertions.jsonl").write_bytes(data)
    (path / "manifest.json").write_bytes(canonical_json(manifest))
    return path


def snapshot(path, rows, header=("subject", "predicate", "object"), *, endings=None):
    path.mkdir()
    endings = endings or [b"\n"] * len(rows)
    body = "\t".join(header).encode() + b"\r\n"
    body += b"".join("\t".join(row).encode() + ending for row, ending in zip(rows, endings, strict=True))
    members = {"merged-kg_edges.tsv": body, "merged-kg_nodes.tsv": b"id\nFixture:1\n"}
    manifest = {"manifest_version": 1, "provenance": {"commit": "synthetic-fixture", "producer": "fixture"},
                "members": {}}
    for name, data in members.items():
        (path / name).write_bytes(data)
        manifest["members"][name] = {"bytes": len(data), "rows": len(data.splitlines()) - 1,
                                     "sha256": hashlib.sha256(data).hexdigest()}
    encoded = canonical_json(manifest)
    (path / "manifest.json").write_bytes(encoded)
    return path, hashlib.sha256(encoded).hexdigest()


def records(receipt):
    manifest = json.loads(receipt.read_bytes())
    return [row for item in manifest["partitions"]
            for row in pq.read_table(receipt.parent / item["path"]).to_pylist()]


def run_fixture(tmp_path, assertions, rows, header=("subject", "predicate", "object"), **kwargs):
    source, digest = snapshot(tmp_path / "snapshot", rows, header, endings=kwargs.pop("endings", None))
    native = export_native(tmp_path / "native", assertions)
    pin = hashlib.sha256((native / "manifest.json").read_bytes()).hexdigest()
    return run_census(source, [native], tmp_path / "result", digest,
                      expected_native_manifest_sha256=[pin], **kwargs)


def test_spo_only_is_not_eligible_and_exact_rows_and_multiplicity_survive(tmp_path):
    row = ("Fixture:1", "skos:exactMatch", "CHEBI:1")
    receipt = run_fixture(tmp_path, [native_assertion()], [row, row, ("Fixture:2", "p", "o")],
                          endings=[b"\r\n", b"\n", b""])
    result = verify_census(receipt)
    persisted = records(receipt)
    assert result["counts"] == {"exact_eligible": 0, "incompatible_scope": 2,
                                "ambiguous_mapping": 0, "unavailable_evidence_export": 0, "unmatched": 1}
    assert persisted[0]["source_row"].endswith(b"\r\n")
    assert persisted[1]["source_row"].endswith(b"\n")
    assert not persisted[2]["source_row"].endswith(b"\n")
    assert len({row["occurrence_id"] for row in persisted}) == 3
    assert result["kg_occurrences_approved"] == result["independent_scientific_reviews"] == 0
    assert result["native_accounting"]["independent_experiments"] is None
    assert result["native_accounting"]["shared_ancestry_references"] == 1


def test_explicit_complete_binding_has_inherited_transport_eligibility_only(tmp_path):
    assertion = native_assertion()
    header = ("subject", "predicate", "object", "native_assertion", "native_scope")
    row = ("Fixture:1", "skos:exactMatch", "CHEBI:1", canonical_json(assertion).decode(),
           "native_mapping_payload_only")
    receipt = run_fixture(tmp_path, [assertion], [row], header)
    persisted = records(receipt)[0]
    assert persisted["classification"] == "exact_eligible"
    assert persisted["eligible_assertion_ids"] == [assertion["assertion_id"]]
    assert verify_census(receipt)["kg_occurrences_approved"] == 0


@pytest.mark.parametrize("change", ["scope", "payload", "evidence", "optional_hash", "predicate"])
def test_context_evidence_and_predicate_mismatches_never_reuse(tmp_path, change):
    assertion = native_assertion()
    embedded = deepcopy(assertion)
    predicate, scope, optional = "skos:exactMatch", "native_mapping_payload_only", sha256_json(assertion["evidence"])
    if change == "scope":
        scope = "whole_record"
    elif change == "payload":
        embedded["payload"]["native_payload"]["condition"] = "different"
    elif change == "evidence":
        embedded["evidence"][0]["sha256"] = "0" * 64
    elif change == "optional_hash":
        optional = "0" * 64
    else:
        predicate = "biolink:related_to"
    row = ("Fixture:1", predicate, "CHEBI:1", canonical_json(embedded).decode(), scope, optional)
    header = ("subject", "predicate", "object", "native_assertion", "native_scope", "native_evidence_sha256")
    receipt = run_fixture(tmp_path, [assertion], [row], header)
    item = records(receipt)[0]
    assert item["classification"] == "incompatible_scope"
    assert item["eligible_assertion_ids"] == []
    if change == "predicate":
        assert item["endpoint_candidate_count"] == 1 and not item["candidate_assertion_ids"]


@pytest.mark.parametrize("status, expected", [("withheld", "incompatible_scope"),
                                             ("unassessed", "unavailable_evidence_export")])
def test_native_nonapproval_preserves_scope_without_global_ban(tmp_path, status, expected):
    receipt = run_fixture(tmp_path, [native_assertion(status=status)],
                          [("Fixture:1", "skos:exactMatch", "CHEBI:1")])
    item = records(receipt)[0]
    assert item["classification"] == expected
    assert item["reasons"] == ["native_" + status]
    assert item["eligible_assertion_ids"] == []


def test_ambiguous_candidates_remain_ambiguous(tmp_path):
    receipt = run_fixture(tmp_path, [native_assertion(), native_assertion(alternative=True)],
                          [("Fixture:1", "skos:exactMatch", "CHEBI:1")])
    item = records(receipt)[0]
    assert item["classification"] == "ambiguous_mapping"
    assert len(item["candidate_assertion_ids"]) == 2
    assert item["eligible_assertion_ids"] == []


def test_duplicate_export_rows_do_not_multiply_candidates(tmp_path):
    assertion = native_assertion()
    receipt = run_fixture(tmp_path, [assertion, assertion], [("Fixture:1", "skos:exactMatch", "CHEBI:1")])
    assert len(records(receipt)[0]["candidate_assertion_ids"]) == 1
    assert verify_census(receipt)["native_accounting"]["duplicate_assertion_rows"] == 1


def test_four_spawn_workers_preserve_serial_bytes_dedup_and_accounting(tmp_path, monkeypatch):
    monkeypatch.setattr(census, "NATIVE_BATCH_ROWS", 1)
    supported = native_assertion()
    withheld = native_assertion(status="withheld")
    unassessed = native_assertion(status="unassessed")
    native = export_native(tmp_path / "native", [supported, withheld, unassessed, supported, withheld])
    extra = export_native(tmp_path / "extra", [supported])
    source, digest = snapshot(tmp_path / "snapshot", [("Fixture:1", "skos:exactMatch", "CHEBI:1")])
    serial = run_census(source, [native, extra], tmp_path / "serial", digest)
    parallel = run_census(source, [native, extra], tmp_path / "parallel", digest, workers=4)
    assert serial.read_bytes() == parallel.read_bytes()
    assert records(serial) == records(parallel)
    result = verify_census(parallel, workers=4)
    assert result["native_accounting"]["distinct_assertions"] == 3
    assert result["native_accounting"]["duplicate_assertion_rows"] == 3
    assert result["native_accounting"]["evidence_references"] == 6
    assert result["native_accounting"]["ancestry_references"] == 6
    assert result["native_accounting"]["shared_ancestry_references"] == 5


@pytest.mark.parametrize("workers", [0, 5, -1, True, 1.0, None])
def test_worker_count_is_bounded_and_exact_before_io(tmp_path, workers):
    with pytest.raises(CurationError, match="workers"):
        run_census(tmp_path / "missing", [], tmp_path / "result", "a" * 64, workers=workers)
    with pytest.raises(CurationError, match="workers"):
        verify_census(tmp_path / "missing", workers=workers)
    assert not (tmp_path / "result").exists()


def test_native_queue_is_bounded_ordered_and_cancels_on_failure(monkeypatch):
    submitted, consumed, cancelled, produced = [], [], [], []

    class Future:
        def __init__(self, number):
            self.number = number

        def result(self):
            consumed.append(self.number)
            if self.number == 3:
                raise CurationError("injected worker failure")
            return [self.number]

        def cancel(self):
            cancelled.append(self.number)

    class Executor:
        def __init__(self, **kwargs):
            assert kwargs["max_workers"] == 4
            assert kwargs["mp_context"].get_start_method() == "spawn"
            assert kwargs["initializer"] is census.check_contracts

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def submit(self, function, batch, source_commit):
            assert function is census._validate_native_batch
            submitted.append(batch[0])
            assert len(submitted) - len(consumed) <= 4
            return Future(batch[0])

    def batches():
        for number in range(100):
            produced.append(number)
            yield [number]

    monkeypatch.setattr(census, "ProcessPoolExecutor", Executor)
    generator = census._validated_native_batches(batches(), 4, None)
    assert next(generator) == ([0], [0])
    assert produced == [0, 1, 2, 3]
    assert next(generator) == ([1], [1])
    assert next(generator) == ([2], [2])
    with pytest.raises(CurationError, match="worker failure"):
        next(generator)
    assert consumed == [0, 1, 2, 3]
    assert produced == list(range(7))
    assert cancelled == [4, 5, 6]


def test_native_input_batches_bound_rows_and_bytes_preserving_every_byte(monkeypatch):
    monkeypatch.setattr(census, "NATIVE_BATCH_ROWS", 2)
    monkeypatch.setattr(census, "NATIVE_BATCH_BYTES", 7)
    raw = b"a\nb\nc\n12345678\nd\n"
    batches = list(census._native_line_batches(BytesIO(raw)))
    assert batches == [[b"a\n", b"b\n"], [b"c\n"], [b"12345678\n"], [b"d\n"]]
    assert b"".join(line for batch in batches for line in batch) == raw
    monkeypatch.setattr(census, "MAX_NATIVE_BYTES", 5)
    with pytest.raises(CurationError, match="exceeds its bound"):
        list(census._native_line_batches(BytesIO(b"123456\n")))


def test_bulk_insert_rejects_conflicts_within_and_across_batches():
    record = census._validate_native_batch([canonical_json(native_assertion())], "a" * 40)[0]
    conflicting = {**record, "document": "conflicting"}
    with census._catalog() as connection:
        with pytest.raises(CurationError, match="Conflicting duplicate"):
            census._insert_native_batch(connection, [record, conflicting])
        census._insert_native_batch(connection, [record, record])
        census._insert_native_batch(connection, [record])
        assert connection.execute("SELECT count(*) FROM native").fetchall()[0][0] == 1
        assert connection.execute("SELECT count(*) FROM evidence").fetchall()[0][0] == 2
        with pytest.raises(CurationError, match="Conflicting duplicate"):
            census._insert_native_batch(connection, [conflicting])


def test_native_inventory_releases_arrow_between_batches(tmp_path, monkeypatch):
    assertions = []
    for number in range(6):
        assertion = native_assertion()
        assertion["native_locator"]["selector"] = {"row": number + 1}
        assertion["assertion_id"] = native_assertion_id(assertion)
        assertions.append(assertion)
    native = export_native(tmp_path / "native", assertions)
    monkeypatch.setattr(census, "NATIVE_BATCH_ROWS", 2)
    original = census._insert_native_batch
    observed = []
    gc.collect()
    baseline = pa.total_allocated_bytes()

    def observe(connection, records):
        gc.collect()
        observed.append(pa.total_allocated_bytes())
        original(connection, records)

    monkeypatch.setattr(census, "_insert_native_batch", observe)
    with census._catalog() as connection:
        _, accounting = census._native_exports(connection, [native])
        gc.collect()
        assert pa.total_allocated_bytes() == baseline
        assert accounting["export_rows"] == accounting["distinct_assertions"] == 6
        assert accounting["evidence_references"] == accounting["ancestry_references"] == 12
    assert observed == [baseline] * 3


def test_failed_native_batch_rolls_back_all_tables_and_allows_retry(monkeypatch):
    first = census._validate_native_batch([canonical_json(native_assertion())], "a" * 40)[0]
    second = census._validate_native_batch(
        [canonical_json(native_assertion(alternative=True))], "a" * 40
    )[0]
    original = census._insert_native_batch

    def fail_after_insert(connection, records):
        original(connection, records)
        raise RuntimeError("Injected failure before batch commit")

    def counts(connection):
        return [connection.execute(f"SELECT count(*) FROM {table}").fetchall()[0][0]
                for table in ("native", "evidence", "ancestry")]

    with census._catalog() as connection:
        census._commit_native_batch(connection, [first])
        assert counts(connection) == [1, 2, 2]
        monkeypatch.setattr(census, "_insert_native_batch", fail_after_insert)
        with pytest.raises(RuntimeError, match="Injected failure"):
            census._commit_native_batch(connection, [second])
        assert counts(connection) == [1, 2, 2]
        monkeypatch.setattr(census, "_insert_native_batch", original)
        census._commit_native_batch(connection, [second])
        assert counts(connection) == [2, 4, 4]


def test_spawn_validation_errors_leave_no_published_census(tmp_path):
    assertion = native_assertion()
    assertion["payload"]["native_payload"]["condition"] = "unbound mutation"
    source, digest = snapshot(tmp_path / "snapshot", [("s", "p", "o")])
    native = export_native(tmp_path / "native", [assertion])
    with pytest.raises(CurationError):
        run_census(source, [native], tmp_path / "result", digest, workers=4)
    assert not (tmp_path / "result").exists()


def test_parallel_public_verifier_revalidates_rehashed_native_payload(tmp_path):
    receipt = run_fixture(tmp_path, [native_assertion()], [("s", "p", "o")])
    manifest = json.loads(receipt.read_bytes())
    native_path = receipt.parent / manifest["native_exports"][0]["path"]
    export = json.loads(native_path.read_bytes())
    data_path = native_path.parent / "assertions.jsonl"
    assertion = json.loads(data_path.read_bytes())
    assertion["payload"]["native_payload"]["condition"] = "unbound mutation"
    encoded = canonical_json(assertion) + b"\n"
    data_path.write_bytes(encoded)
    export.update(assertions_sha256=hashlib.sha256(encoded).hexdigest(), assertions_bytes=len(encoded))
    native_path.write_bytes(canonical_json(export))
    manifest["native_exports"][0].update(sha256=hashlib.sha256(native_path.read_bytes()).hexdigest(),
                                         assertions_sha256=export["assertions_sha256"])
    receipt.write_bytes(canonical_json(manifest))
    with pytest.raises(CurationError):
        verify_census(receipt, workers=4)


def test_spawn_worker_checks_source_commit_pin(tmp_path):
    source, digest = snapshot(tmp_path / "snapshot", [("s", "p", "o")])
    native = export_native(tmp_path / "native", [native_assertion()])
    path = native / "manifest.json"
    manifest = json.loads(path.read_bytes())
    manifest["source_commit"] = "b" * 40
    path.write_bytes(canonical_json(manifest))
    with pytest.raises(CurationError, match="source commit"):
        run_census(source, [native], tmp_path / "result", digest, workers=4)
    assert not (tmp_path / "result").exists()


@pytest.mark.parametrize("operation", ["census", "verify-census"])
def test_cli_forwards_explicit_worker_count(tmp_path, monkeypatch, capsys, operation):
    from edgemech.__main__ import main

    received = {}

    def invoke(*args, **kwargs):
        received.update(kwargs)
        return tmp_path / "receipt.json" if operation == "census" else {"verified": True}

    if operation == "census":
        monkeypatch.setattr(census, "run_census", invoke)
        arguments = ["--snapshot", str(tmp_path), "--source-sha256", "a" * 64,
                     "--native-export", str(tmp_path), "--native-sha256", "b" * 64,
                     "--output", str(tmp_path / "output")]
    else:
        monkeypatch.setattr(census, "verify_census", invoke)
        arguments = [str(tmp_path / "receipt.json")]
    monkeypatch.setattr("sys.argv", ["edgemech", operation, *arguments, "--workers", "4"])
    assert main() == 0
    assert received["workers"] == 4
    assert json.loads(capsys.readouterr().out)


@pytest.mark.parametrize("member", ["merged-kg_edges.tsv", "merged-kg_nodes.tsv"])
def test_limit_still_verifies_unselected_tails_and_all_source_members(tmp_path, member):
    source, digest = snapshot(tmp_path / "snapshot", [("s", "p", "o"), ("s2", "p", "o")])
    with (source / member).open("ab") as handle:
        handle.write(b"unselected corruption\n")
    with pytest.raises(CurationError, match="Source member"):
        run_census(source, [], tmp_path / "result", digest, limit=1)
    assert not (tmp_path / "result").exists()


def test_bounded_selection_covers_exact_prefix_and_refuses_replacement(tmp_path):
    receipt = run_fixture(tmp_path, [], [("s", "p", "o"), ("s", "p", "o")], limit=1)
    result = verify_census(receipt)
    assert result["source"]["selected_rows"] == 1 and result["source"]["source_rows"] == 2
    assert result["source"]["complete_export"] is False
    with pytest.raises(CurationError, match="replace"):
        run_census(tmp_path / "snapshot", [], receipt.parent, result["source"]["manifest_sha256"])


def test_native_input_pin_and_file_tampering_fail_before_publication(tmp_path):
    source, digest = snapshot(tmp_path / "snapshot", [("s", "p", "o")])
    native = export_native(tmp_path / "native", [native_assertion()])
    with pytest.raises(CurationError, match="manifest hash mismatch"):
        run_census(source, [native], tmp_path / "result", digest,
                   expected_native_manifest_sha256=["0" * 64])
    with (native / "assertions.jsonl").open("ab") as handle:
        handle.write((native / "assertions.jsonl").read_bytes())
    with pytest.raises(CurationError, match="do not reconcile"):
        run_census(source, [native], tmp_path / "result", digest)
    assert not (tmp_path / "result").exists()


def test_failed_persisted_verification_publishes_nothing(tmp_path, monkeypatch):
    source, digest = snapshot(tmp_path / "snapshot", [("s", "p", "o")])

    def reject(receipt, **kwargs):
        assert receipt.is_file()
        assert list((receipt.parent / "partitions").glob("*.parquet"))
        raise CurationError("Injected persisted-verification failure")

    monkeypatch.setattr(census, "verify_census", reject)
    with pytest.raises(CurationError, match="Injected"):
        run_census(source, [], tmp_path / "result", digest)
    assert not (tmp_path / "result").exists()


def test_modified_partition_or_counters_fail_verification(tmp_path):
    receipt = run_fixture(tmp_path, [], [("s", "p", "o")])
    manifest = json.loads(receipt.read_bytes())
    manifest["counts"]["unmatched"] = 0
    receipt.write_bytes(canonical_json(manifest))
    with pytest.raises(CurationError, match="counts do not reconcile"):
        verify_census(receipt)
    manifest["counts"]["unmatched"] = 1
    receipt.write_bytes(canonical_json(manifest))
    path = receipt.parent / manifest["partitions"][0]["path"]
    with path.open("ab") as handle:
        handle.write(b"modified")
    with pytest.raises(CurationError, match="partition file binding"):
        verify_census(receipt)


def test_rehashed_fabricated_rows_cannot_impersonate_original_source(tmp_path):
    receipt = run_fixture(tmp_path, [], [("s", "p", "o")])
    manifest = json.loads(receipt.read_bytes())
    partition = manifest["partitions"][0]
    path = receipt.parent / partition["path"]
    rows = pq.read_table(path).to_pylist()
    rows[0]["source_row"] = b"fabricated\tp\to\n"
    rows[0]["row_sha256"] = hashlib.sha256(rows[0]["source_row"]).hexdigest()
    source = manifest["source"]
    rows[0]["occurrence_id"] = occurrence_id(
        manifest_sha256=source["manifest_sha256"], member=source["edge_member"],
        member_sha256=source["edge_member_sha256"], row_number=1, row_sha256=rows[0]["row_sha256"],
    )
    pq.write_table(pa.Table.from_pylist(rows, schema=CENSUS_SCHEMA), path)
    partition.update(sha256=hashlib.sha256(path.read_bytes()).hexdigest(), bytes=path.stat().st_size)
    receipt.write_bytes(canonical_json(manifest))
    with pytest.raises(CurationError, match="pinned original prefix"):
        verify_census(receipt)


def test_source_tampering_after_publication_is_detected(tmp_path):
    receipt = run_fixture(tmp_path, [], [("s", "p", "o"), ("s2", "p", "o")], limit=1)
    with (tmp_path / "snapshot" / "merged-kg_edges.tsv").open("ab") as handle:
        handle.write(b"tail\tp\to\n")
    with pytest.raises(CurationError, match="Original source member"):
        verify_census(receipt)


def test_source_symlink_is_rejected(tmp_path):
    source, digest = snapshot(tmp_path / "snapshot", [("s", "p", "o")])
    link = tmp_path / "linked"
    link.symlink_to(source, target_is_directory=True)
    with pytest.raises(CurationError, match="symlink"):
        run_census(link, [], tmp_path / "result", digest)


def test_multiple_partitions_reconcile_initial_prefix(tmp_path, monkeypatch):
    monkeypatch.setattr(census, "BATCH_ROWS", 2)
    receipt = run_fixture(tmp_path, [], [("s", "p", "o")] * 5, limit=4)
    result = verify_census(receipt)
    assert [(item["first_row"], item["last_row"]) for item in result["partitions"]] == [(1, 2), (3, 4)]
    assert [row["row_number"] for row in records(receipt)] == [1, 2, 3, 4]


def test_empty_edge_population_is_explicit(tmp_path):
    receipt = run_fixture(tmp_path, [], [])
    result = verify_census(receipt)
    assert result["source"]["complete_export"] and result["source"]["selected_rows"] == 0
    assert result["partitions"] == [] and not any(result["counts"].values())


def test_named_pipe_metadata_fails_without_blocking(tmp_path):
    source = tmp_path / "snapshot"
    source.mkdir()
    os.mkfifo(source / "manifest.json")
    with pytest.raises(CurationError, match="regular file"):
        run_census(source, [], tmp_path / "result", "0" * 64)


def test_publication_flushes_data_directories_before_manifest_and_parent_after(tmp_path, monkeypatch):
    """Issues #1/#3: verify ordering, without simulating a real power loss."""
    events = []
    fsync, sync_directory, link = os.fsync, census._fsync_directory, os.link

    def record_fsync(descriptor):
        events.append(("directory_fsync" if stat.S_ISDIR(os.fstat(descriptor).st_mode)
                       else "file_fsync", None))
        return fsync(descriptor)

    def record_directory(path):
        events.append(("directory", Path(path)))
        return sync_directory(path)

    def record_link(path, destination, **kwargs):
        events.append(("link", Path(destination)))
        return link(path, destination, **kwargs)

    monkeypatch.setattr(os, "fsync", record_fsync)
    monkeypatch.setattr(census, "_fsync_directory", record_directory)
    monkeypatch.setattr(os, "link", record_link)
    receipt = run_fixture(tmp_path, [], [("s", "p", "o")])
    publication = next(index for index, item in enumerate(events) if item == ("link", receipt))
    first_link = next(index for index, item in enumerate(events) if item[0] == "link")
    first_directory = next(index for index, item in enumerate(events) if item[0] == "directory")
    assert any(item[0] == "file_fsync" for item in events[:first_directory])
    assert not any(item[0] == "file_fsync" for item in events[first_directory:])
    assert first_directory < first_link < publication
    assert ("directory", receipt.parent / "partitions") in events[first_link:publication]
    assert ("directory", receipt.parent) in events[first_link:publication]
    assert events[publication + 1:] == [("directory", receipt.parent), ("directory_fsync", None),
                                       ("directory", receipt.parent.parent), ("directory_fsync", None)]


def test_racing_empty_destination_is_preserved_without_replacement(tmp_path, monkeypatch):
    source, digest = snapshot(tmp_path / "snapshot", [("s", "p", "o")])
    output = tmp_path / "result"
    mkdir, inode = Path.mkdir, []

    def race(path, *args, **kwargs):
        if path == output:
            mkdir(path)
            inode.append(path.stat().st_ino)
        return mkdir(path, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", race)
    with pytest.raises(CurationError, match="preserved unchanged"):
        run_census(source, [], output, digest)
    assert len(inode) == 1 and output.stat().st_ino == inode[0]
    assert list(output.iterdir()) == []


def test_manifest_link_failure_leaves_only_an_unpublished_reservation(tmp_path, monkeypatch):
    source, digest = snapshot(tmp_path / "snapshot", [("s", "p", "o")])
    output = tmp_path / "result"
    link = os.link

    def fail_before_manifest(source_path, destination, **kwargs):
        if Path(destination) == output / "census-manifest.json":
            assert list((output / "partitions").glob("*.parquet"))
            raise OSError("Injected manifest publication failure")
        return link(source_path, destination, **kwargs)

    monkeypatch.setattr(os, "link", fail_before_manifest)
    with pytest.raises(OSError, match="Injected manifest"):
        run_census(source, [], output, digest)
    assert output.is_dir() and not (output / "census-manifest.json").exists()
    assert (output / "source-manifest.json").read_bytes() == (source / "manifest.json").read_bytes()
    with pytest.raises(CurationError, match="replace"):
        run_census(source, [], output, digest)


def test_racing_file_name_inside_reservation_is_not_overwritten(tmp_path, monkeypatch):
    source, digest = snapshot(tmp_path / "snapshot", [("s", "p", "o")])
    output = tmp_path / "result"
    link = os.link

    def race_file(source_path, destination, **kwargs):
        if Path(destination) == output / "source-manifest.json":
            Path(destination).write_bytes(b"another writer's file")
        return link(source_path, destination, **kwargs)

    monkeypatch.setattr(os, "link", race_file)
    with pytest.raises(FileExistsError):
        run_census(source, [], output, digest)
    assert (output / "source-manifest.json").read_bytes() == b"another writer's file"
    assert not (output / "census-manifest.json").exists()


@pytest.mark.parametrize("header, row, error", [
    (("subject", "subject", "object"), ("s", "p", "o"), "duplicate KG edge header"),
    (("subject", "predicate", "unknown"), ("s", "p", "o"), "KG edge header"),
    (("subject", "predicate", "object"), ("s", "p"), "row width"),
])
def test_malformed_header_or_selected_row_fails_before_publication(tmp_path, header, row, error):
    source, digest = snapshot(tmp_path / "snapshot", [row], header)
    with pytest.raises(CurationError, match=error):
        run_census(source, [], tmp_path / "result", digest, limit=1)
    assert not (tmp_path / "result").exists()
