"""Lossless storage, replay, tamper and atomic-publication checks for CLAW #951."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from kg_microbe_curation.contract import claim_digest, decision_digest, unprocessed_decision
from kg_microbe_curation.identity import (
    CONTRACT,
    CurationError,
    canonical_json,
    content_id,
    context_id,
    occurrence_id,
    sha256_json,
)
from kg_microbe_curation.ledger import apply_bundle, coverage, ingest_export

from edgemech import storage
from edgemech.storage.parquet import file_hash, logical_hash, table_rows


def digest(data):
    return hashlib.sha256(data).hexdigest()


@pytest.fixture
def ledger_input(tmp_path):
    export = tmp_path / "export"
    export.mkdir()
    header = "subject\tpredicate\tobject\tnote\r\n"
    # Duplicate biological edges, exact CRLF, Unicode, and an unterminated final row.
    rows = ["A:1\tbiolink:related_to\tB:1\tα\r\n",
            "A:1\tbiolink:related_to\tB:1\tα\r\n",
            'A:2\tbiolink:related_to\tB:2\t"literal"\\text']
    raw = (header + "".join(rows)).encode()
    member = {"sha256": digest(raw), "bytes": len(raw), "rows": len(rows)}
    source = {"manifest_version": 1, "members": {"edges.tsv": member}}
    source_bytes = canonical_json(source) + b"\n"
    (export / "source-manifest.json").write_bytes(source_bytes)
    occurrences = []
    for number, row in enumerate(rows, 1):
        fields = {"manifest_sha256": digest(source_bytes), "member": "edges.tsv",
                  "member_sha256": member["sha256"], "row_number": number,
                  "row_sha256": digest(row.encode())}
        occurrences.append({"occurrence_id": occurrence_id(**fields), **fields, "source_row": row})
    shard = b"".join(canonical_json(row) + b"\n" for row in occurrences)
    (export / "rows.jsonl").write_bytes(shard)
    manifest = {
        "contract": CONTRACT, "format": "edge-occurrence-export", "format_version": 1,
        "source_manifest_sha256": digest(source_bytes), "source_manifest": source,
        "source_manifest_file": "source-manifest.json", "input_complete": True,
        "members": {"edges.tsv": {**member, "header": header.rstrip("\r\n").split("\t"),
                                  "header_row": header}},
        "selection": {"edge_member": "edges.tsv", "max_rows": 0,
                      "exported_rows": len(rows), "complete_export": True},
        "shards": [{"file": "rows.jsonl", "sha256": digest(shard), "bytes": len(shard),
                    "rows": len(rows), "first_row": 1, "last_row": len(rows)}],
    }
    (export / "manifest.json").write_bytes(canonical_json(manifest) + b"\n")
    ledger = tmp_path / "ledger.sqlite"
    status = ingest_export(export, ledger)
    for reason in ("First evidence gap.", "Still missing evidence."):
        decision = unprocessed_decision(occurrences[0]["occurrence_id"])
        decision.update(review_state="deferred", rationale=reason)
        bundle = {"contract": CONTRACT, "input_sha256": status["input_sha256"],
                  "occurrence_ids": [occurrences[0]["occurrence_id"]], "decisions": [decision],
                  "observations": [], "claims": [], "reviews": []}
        status = apply_bundle(ledger, bundle, expected_revision=status["revision"])
    return ledger, export, occurrences


def migrate(ledger_input, tmp_path):
    ledger, export, _ = ledger_input
    return storage.migrate_sqlite(ledger, export, tmp_path / "store", buckets=2, row_group_size=2)


def test_new_store_parent_is_durable_after_current(ledger_input, tmp_path, monkeypatch):
    events = []
    flush, publish = storage._fsync_directory, storage._publish_pointer

    def tracked_flush(path):
        events.append(("fsync", path))
        return flush(path)

    def tracked_publish(store, manifest):
        publish(store, manifest)
        assert (store / "CURRENT").is_file()
        events.append(("current_durable", store))

    monkeypatch.setattr(storage, "_fsync_directory", tracked_flush)
    monkeypatch.setattr(storage, "_publish_pointer", tracked_publish)
    migrate(ledger_input, tmp_path)
    assert events[-2:] == [("current_durable", tmp_path / "store"), ("fsync", tmp_path)]


def test_complete_lossless_roundtrip(ledger_input, tmp_path):
    ledger, _, occurrences = ledger_input
    before = file_hash(ledger)
    manifest = migrate(ledger_input, tmp_path)
    document = json.loads(manifest.read_bytes())
    assert storage.verify(manifest)["verified"]
    assert file_hash(ledger) == before
    pointer = json.loads((tmp_path / "store/CURRENT").read_bytes())
    assert pointer["sha256"] == file_hash(manifest)
    assert (tmp_path / "store" / pointer["manifest"]) == manifest
    receipt = json.loads(manifest.with_name("migration-receipt.json").read_bytes())
    assert receipt["input_hashes_before"] == receipt["input_hashes_after"]
    assert receipt["manifest_sha256"] == pointer["sha256"]
    proof = receipt["source_table_reconciliation"]
    assert proof["contract"] == storage.RECONCILIATION_CONTRACT and proof["verified"] is True
    assert set(proof["source_tables"]) == set(storage.AUTHORITATIVE)
    assert proof["source_tables"] == proof["persisted_tables"] == {
        name: {key: document["tables"][name][key] for key in ("logical_sha256", "rows")}
        for name in storage.AUTHORITATIVE
    }
    with sqlite3.connect(ledger) as connection:
        for name in storage.AUTHORITATIVE:
            assert list(table_rows(manifest.parent, name, document["tables"][name])) == [
                tuple(row) for row in storage._sql_rows(connection, name)
            ]
    for occurrence in occurrences:
        found = storage.lookup(manifest, occurrence["occurrence_id"])
        assert found["occurrence"]["source_row"] == occurrence["source_row"]
        assert found["verification_scope"] == "selected_partitions_only"
    found = storage.lookup(manifest, occurrences[0]["occurrence_id"])
    assert len(found["history"]) == 2
    assert [item["history"]["sequence"] for item in found["history"]] == [0, 1]
    assert found["current_decision"]["review_state"] == "deferred"
    assert document["tables"]["memberships"]["rows"] == 2
    for name in ("observations", "claims", "reviews", "evidence"):
        assert document["tables"][name]["rows"] == 0
        assert document["tables"][name]["partitions"] == []
    assert storage.stats(manifest)["counters"]["review_state"] == {"unprocessed": 2, "deferred": 1}


def test_internally_valid_writer_header_change_cannot_publish(ledger_input, tmp_path, monkeypatch):
    """A same-width header change survives replay but loses original source fields."""
    original, mutated = storage.write_partitioned_table, []

    def changed_writer(generation, name, rows, **kwargs):
        def changed_rows():
            for key, value in rows:
                if key == "header":
                    header = json.loads(value)
                    header[0] = "silently_changed_subject"
                    value = canonical_json(header).decode()
                    mutated.append(True)
                yield key, value
        return original(generation, name, changed_rows() if name == "metadata" else rows, **kwargs)

    monkeypatch.setattr(storage, "write_partitioned_table", changed_writer)
    with pytest.raises(CurationError, match="source-to-output logical table mismatch: metadata"):
        migrate(ledger_input, tmp_path)
    assert mutated == [True]
    assert not (tmp_path / "store/CURRENT").exists()
    assert not list((tmp_path / "store/generations").glob("*/manifest.json"))


@pytest.mark.parametrize("mutation", ["tamper", "missing", "symlink"])
def test_partition_damage_fails(ledger_input, tmp_path, mutation):
    manifest = migrate(ledger_input, tmp_path)
    document = json.loads(manifest.read_bytes())
    path = manifest.parent / document["tables"]["occurrences"]["partitions"][0]["path"]
    if mutation == "tamper":
        with path.open("ab") as handle:
            handle.write(b"corrupted")
    elif mutation == "missing":
        path.unlink()
    else:
        target = tmp_path / "copied.parquet"
        target.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(target)
    with pytest.raises(CurationError):
        storage.verify(manifest)


@pytest.mark.parametrize("sql", [
    "UPDATE bundles SET parent_revision='broken' WHERE rowid=2",
    "UPDATE bundles SET parent_revision=(SELECT parent_revision FROM bundles WHERE rowid=1) WHERE rowid=2",
    "UPDATE current_decisions SET review_state='unprocessed' WHERE review_state='deferred'",
    "UPDATE occurrences SET source_row=source_row || ' ' WHERE row_number=1",
    "UPDATE bundles SET document=document || ' '",
    "UPDATE metadata SET value='99' WHERE key='applied_bundles'",
    "UPDATE coverage_counts SET count=count+1 WHERE dimension='disposition'",
])
def test_source_history_and_projection_corruption_refused(ledger_input, tmp_path, sql):
    ledger, _, _ = ledger_input
    with sqlite3.connect(ledger) as connection:
        connection.execute(sql)
    with pytest.raises(CurationError):
        migrate(ledger_input, tmp_path)
    assert not (tmp_path / "store/CURRENT").exists()


def test_publication_failure_has_no_current(ledger_input, tmp_path, monkeypatch):
    def fail(*args):
        raise OSError("injected crash before pointer publication")
    monkeypatch.setattr(storage, "_publish_pointer", fail)
    with pytest.raises(CurationError, match="injected crash"):
        migrate(ledger_input, tmp_path)
    assert not (tmp_path / "store/CURRENT").exists()
    assert not list((tmp_path / "store/generations").glob(".staging-*"))
    # The complete immutable orphan survives for diagnosis; no preexisting path is removed.
    assert len(list((tmp_path / "store/generations").glob("*/manifest.json"))) == 1


def test_verification_failure_has_no_generation(ledger_input, tmp_path, monkeypatch):
    def fail(*args):
        raise CurationError("injected prepublication validation failure")
    monkeypatch.setattr(storage, "verify", fail)
    with pytest.raises(CurationError, match="injected"):
        migrate(ledger_input, tmp_path)
    assert not (tmp_path / "store/CURRENT").exists()
    assert not list((tmp_path / "store/generations").iterdir())


def test_existing_destination_and_symlink_parent_refused(ledger_input, tmp_path):
    target = tmp_path / "store"
    target.mkdir()
    marker = target / "valuable.txt"
    marker.write_text("keep")
    with pytest.raises(CurationError, match="existing store"):
        migrate(ledger_input, tmp_path)
    assert marker.read_text() == "keep"
    linked = tmp_path / "link"
    linked.symlink_to(target, target_is_directory=True)
    with pytest.raises(CurationError, match="symlink"):
        storage.migrate_sqlite(ledger_input[0], ledger_input[1], linked / "new")


def test_wal_state_refused(ledger_input, tmp_path):
    ledger, _, _ = ledger_input
    Path(str(ledger) + "-wal").write_bytes(b"nonempty uncheckpointed state")
    with pytest.raises(CurationError, match="WAL"):
        migrate(ledger_input, tmp_path)
    assert not (tmp_path / "store").exists()


def test_duplicate_primary_keys_refused(tmp_path):
    with pytest.raises(CurationError, match="duplicate"):
        storage.write_partitioned_table(tmp_path, "metadata", [("x", "1"), ("x", "2")])


def test_lookup_limit_is_explicit(ledger_input, tmp_path, monkeypatch):
    manifest = migrate(ledger_input, tmp_path)
    monkeypatch.setattr(storage, "MAX_LOOKUP_BYTES", 100)
    with pytest.raises(CurationError, match="lookup exceeds"):
        storage.lookup(manifest, ledger_input[2][0]["occurrence_id"])


def test_source_change_during_migration_refused(ledger_input, tmp_path, monkeypatch):
    original = storage._input_hashes
    calls = 0

    def changed(*args):
        nonlocal calls
        calls += 1
        result = original(*args)
        if calls == 2:
            result["changed-input"] = "0" * 64
        return result
    monkeypatch.setattr(storage, "_input_hashes", changed)
    with pytest.raises(CurationError, match="input changed"):
        migrate(ledger_input, tmp_path)
    assert not (tmp_path / "store/CURRENT").exists()


@pytest.mark.parametrize("sql", [
    "ALTER TABLE occurrences ADD COLUMN extension TEXT",
    "CREATE TABLE unexpected (value TEXT)",
])
def test_unknown_source_fields_are_not_silently_dropped(ledger_input, tmp_path, sql):
    with sqlite3.connect(ledger_input[0]) as connection:
        connection.execute(sql)
    with pytest.raises(CurationError, match="unsupported SQLite"):
        migrate(ledger_input, tmp_path)


def rewrite_table(manifest, name, field, replacement):
    """Change persisted values and all hashes, so semantic verification must catch it."""
    document = json.loads(manifest.read_bytes())
    for partition in document["tables"][name]["partitions"]:
        path = manifest.parent / partition["path"]
        table = pq.ParquetFile(path).read()
        rows = table.to_pylist()
        for row in rows:
            row[field] = replacement
        pq.write_table(pa.Table.from_pylist(rows, schema=table.schema), path)
        partition.update(sha256=file_hash(path), bytes=path.stat().st_size)
    checksum, _ = logical_hash(table_rows(manifest.parent, name, document["tables"][name]), name)
    document["tables"][name]["logical_sha256"] = checksum
    manifest.write_bytes(canonical_json(document) + b"\n")


@pytest.mark.parametrize("name,field,replacement", [
    ("history", "sequence", 99),
    ("memberships", "position", 99),
    ("current_decisions", "review_state", "in_review"),
])
def test_rehashed_semantic_damage_fails(ledger_input, tmp_path, name, field, replacement):
    manifest = migrate(ledger_input, tmp_path)
    rewrite_table(manifest, name, field, replacement)
    with pytest.raises(CurationError):
        storage.verify(manifest)
    with pytest.raises(CurationError):
        storage.lookup(manifest, ledger_input[2][0]["occurrence_id"])


def test_manifest_traversal_is_rejected(ledger_input, tmp_path):
    manifest = migrate(ledger_input, tmp_path)
    document = json.loads(manifest.read_bytes())
    document["tables"]["occurrences"]["partitions"][0]["path"] = "../outside.parquet"
    manifest.write_bytes(canonical_json(document) + b"\n")
    with pytest.raises(CurationError, match="traversal"):
        storage.verify(manifest)


def test_nonempty_native_payload_review_and_evidence_are_preserved(ledger_input, tmp_path):
    """Use real CLAW validation; deterministic review remains scientifically withheld."""
    ledger, _, occurrences = ledger_input
    status = coverage(ledger)
    payload = {
        "subject": "A:1", "predicate": "biolink:related_to", "object": "B:1",
        "context": {"strain": "fixture", "negated": True},
        "interpretation": {"normalization_contract": "test/v1", "normalizer_contract_sha256": "1" * 64,
                           "schema_sha256": "2" * 64, "prefix_map_sha256": "3" * 64},
        "evidence": ["fixture:source"], "provided_by": ["fixture:native"],
    }
    observation = {
        "observation_id": content_id("observation", payload), "payload": payload,
        "context_id": context_id(payload["context"]),
        "native_identity": {"identifier": "native:retained", "algorithm": "test/native-v1",
                            "normalizer_contract_sha256": "4" * 64, "schema_sha256": "5" * 64,
                            "prefix_map_sha256": "6" * 64},
    }
    claim_payload = {key: payload[key] for key in ("subject", "predicate", "object", "context", "interpretation")}
    claim_payload["epistemic_kind"] = "observational"
    claim = {"claim_id": content_id("claim", claim_payload), "payload": claim_payload,
             "context_id": context_id(payload["context"]), "observation_ids": [observation["observation_id"]]}
    review_id = "20261107T010000Z-storage-test"
    decision = unprocessed_decision(occurrences[0]["occurrence_id"])
    decision.update(review_state="reviewed", review_ids=[review_id],
                    observation_id=observation["observation_id"], claim_ids=[claim["claim_id"]])
    observations_by_id = {observation["observation_id"]: observation}
    targets = []
    for identifier, kind, checksum in (
        (decision["occurrence_id"], "decision", decision_digest(decision, observations_by_id)),
        (claim["claim_id"], "claim", claim_digest(claim, observations_by_id)),
    ):
        targets.append({"target_id": identifier, "path": "snapshot/manifest.json", "selector": identifier,
                        "label": "Synthetic fixture", "kind": "snapshot_row", "ownership_note": "Test only.",
                        "semantic_digest": {"algorithm": f"kg-microbe-curation-{kind}/v1", "sha256": checksum,
                                            "description": "Exact fixture scope."}})
    identifiers = [target["target_id"] for target in targets]
    review = {
        "schema_version": "1.0.0", "review_id": review_id, "kind": "batch",
        "repository": "Example/FixtureMech", "title": "Storage conformance fixture",
        "started_at": "2026-11-07T00:59:00Z", "finished_at": "2026-11-07T01:00:00Z",
        "reviewer": {"identity": "Synthetic fixture", "kind": "deterministic", "independence": "not_applicable",
                     "independence_basis": "Synthetic test."},
        "skill": "test-fixture", "completion": "completed", "verdict": "pass",
        "scientific_review": False, "summary": "Test only; no scientific approval.",
        "source": {"git_revision": "a" * 40, "state": "git_commit", "inputs": [
            {"path": "snapshot/manifest.json", "sha256": status["input_sha256"], "role": "snapshot"}]},
        "scope": {"description": "Exact test targets", "selection": "Explicit IDs", "coverage": "full",
                  "population_size": len(identifiers), "reviewed_target_ids": identifiers},
        "targets": targets,
        "checks": [{"check_id": "fixture", "name": "Scope", "status": "passed", "required": True,
                    "summary": "Fixture inspected", "target_ids": identifiers, "evidence_ids": ["fixture"]}],
        "evidence": [{"evidence_id": "fixture", "kind": "record_content", "reference": "fixture:source",
                      "accessed_at": "2026-11-07T00:59:30Z", "support": "supports", "summary": "Test only."}],
        "assessments": [{"assessment_id": "fixture", "area": "scope", "topic": "Exact fixture",
                         "outcome": "supported", "summary": "Test only.", "target_ids": identifiers,
                         "evidence_ids": ["fixture"]}],
        "findings": [], "actions": [], "limitations": [],
    }
    bundle = {"contract": CONTRACT, "input_sha256": status["input_sha256"],
              "occurrence_ids": [decision["occurrence_id"]], "decisions": [decision],
              "observations": [observation], "claims": [claim],
              "reviews": [{"review_id": review_id, "sha256": sha256_json(review), "document": review}]}
    apply_bundle(ledger, bundle, expected_revision=status["revision"])
    manifest = migrate(ledger_input, tmp_path)
    document = json.loads(manifest.read_bytes())
    for name in ("observations", "claims", "reviews", "evidence"):
        assert document["tables"][name]["rows"] == 1
    result = storage.lookup(manifest, decision["occurrence_id"])
    assert result["current_decision"]["disposition"] == "withheld"
    assert result["scientific_review"] is False
    assert result["history"][-1]["bundle"]["document"] == canonical_json(bundle).decode()
