"""Reject substituted experiment receipts in validation prose (EdgeMech #6)."""

import hashlib
import json
import runpy
from copy import deepcopy
from pathlib import Path

import pytest

REPORT = runpy.run_path(str(Path(__file__).parents[1] / "scripts/adhoc/summarize_validation_20261107.py"))


@pytest.fixture
def receipt(tmp_path):
    source = {"source_manifest_sha256": REPORT["SNAPSHOT_SHA256"],
              "sqlite_sha256": REPORT["SQLITE_SHA256"]}
    tables = {name: {"logical_sha256": "a" * 64, "rows": 1} for name in REPORT["AUTHORITATIVE"]}
    manifest = {"source": source, "counters": REPORT["EXPECTED_COUNTERS"], "tables": tables}
    raw = json.dumps(manifest).encode()
    path = tmp_path / "manifest.json"
    path.write_bytes(raw)
    proof = {"contract": "edgemech-source-table-reconciliation/v1", "verified": True,
             "source_tables": deepcopy(tables), "persisted_tables": deepcopy(tables)}
    record = {
        "manifest": str(path), "manifest_sha256": hashlib.sha256(raw).hexdigest(),
        "contract": "edgemech-storage-canary/v1",
        "source_sqlite_sha256": REPORT["SQLITE_SHA256"], "source_sqlite_bytes": 806912,
        "source_sqlite": str(tmp_path / "source.sqlite"),
        "scientific_approvals_created": 0,
        "verification": {"verified": True, "rows": 1000, "table_rows": {"bundles": 1, "history": 1}},
        "status": {"source": source, "counters": dict(REPORT["EXPECTED_COUNTERS"])},
        "source_table_reconciliation": proof,
    }
    migration = {"manifest_sha256": record["manifest_sha256"],
                 "verification": record["verification"], "source_table_reconciliation": proof,
                 "input_hashes_before": {record["source_sqlite"]: REPORT["SQLITE_SHA256"]},
                 "input_hashes_after": {record["source_sqlite"]: REPORT["SQLITE_SHA256"]}}
    encoded = json.dumps(migration).encode()
    path.with_name("migration-receipt.json").write_bytes(encoded)
    record["migration_receipt_sha256"] = hashlib.sha256(encoded).hexdigest()
    return record


def test_expected_receipt_is_accepted(receipt):
    REPORT["check_storage"](receipt)


def test_different_valid_ledger_is_rejected(receipt):
    receipt["source_sqlite_sha256"] = "a" * 64
    with pytest.raises(ValueError, match="pinned"):
        REPORT["check_storage"](receipt)


def test_different_decisions_are_rejected(receipt):
    receipt["status"]["counters"]["review_state"] = {"unprocessed": 1000}
    with pytest.raises(ValueError, match="pinned"):
        REPORT["check_storage"](receipt)


def test_modified_persisted_manifest_is_rejected(receipt):
    Path(receipt["manifest"]).write_text("{}")
    with pytest.raises(ValueError, match="Persisted manifest differs"):
        REPORT["check_storage"](receipt)


def test_missing_source_output_proof_is_rejected(receipt):
    del receipt["source_table_reconciliation"]
    with pytest.raises(ValueError, match="Missing source-to-output"):
        REPORT["check_storage"](receipt)


@pytest.mark.parametrize("side", ["source_tables", "persisted_tables"])
@pytest.mark.parametrize("change", ["hash", "count", "missing_table"])
def test_changed_source_output_proof_is_rejected(receipt, side, change):
    table = receipt["source_table_reconciliation"][side]
    if change == "hash":
        table["metadata"]["logical_sha256"] = "b" * 64
    elif change == "count":
        table["metadata"]["rows"] += 1
    else:
        del table["metadata"]
    with pytest.raises(ValueError, match="Reconciliation proof"):
        REPORT["check_storage"](receipt)


@pytest.mark.parametrize("change", ["missing_hash", "bytes", "rehashed_binding"])
def test_missing_or_substituted_migration_receipt_is_rejected(receipt, change):
    path = Path(receipt["manifest"]).with_name("migration-receipt.json")
    if change == "missing_hash":
        del receipt["migration_receipt_sha256"]
    elif change == "bytes":
        path.write_text("{}")
    else:
        document = json.loads(path.read_bytes())
        document["manifest_sha256"] = "f" * 64
        raw = json.dumps(document).encode()
        path.write_bytes(raw)
        receipt["migration_receipt_sha256"] = hashlib.sha256(raw).hexdigest()
    with pytest.raises(ValueError, match="[Mm]igration receipt"):
        REPORT["check_storage"](receipt)


def test_rehashed_different_source_manifest_cannot_use_original_outer_pin(receipt):
    path = Path(receipt["manifest"])
    manifest = json.loads(path.read_bytes())
    manifest["source"]["sqlite_sha256"] = "b" * 64
    raw = json.dumps(manifest).encode()
    path.write_bytes(raw)
    receipt["manifest_sha256"] = hashlib.sha256(raw).hexdigest()
    receipt["status"]["source"] = manifest["source"]
    migration_path = path.with_name("migration-receipt.json")
    migration = json.loads(migration_path.read_bytes())
    migration["manifest_sha256"] = receipt["manifest_sha256"]
    raw = json.dumps(migration).encode()
    migration_path.write_bytes(raw)
    receipt["migration_receipt_sha256"] = hashlib.sha256(raw).hexdigest()
    with pytest.raises(ValueError, match="pinned"):
        REPORT["check_storage"](receipt)


@pytest.mark.parametrize("change", ["absent", "changed_after", "different_ledger", "missing_ledger"])
def test_rehashed_migration_input_substitution_is_rejected(receipt, change):
    path = Path(receipt["manifest"]).with_name("migration-receipt.json")
    migration = json.loads(path.read_bytes())
    ledger = receipt["source_sqlite"]
    if change == "absent":
        del migration["input_hashes_before"]
    elif change == "changed_after":
        migration["input_hashes_after"][ledger] = "b" * 64
    elif change == "different_ledger":
        migration["input_hashes_before"][ledger] = "b" * 64
        migration["input_hashes_after"][ledger] = "b" * 64
    else:
        migration["input_hashes_before"] = {"/other/source.sqlite": REPORT["SQLITE_SHA256"]}
        migration["input_hashes_after"] = migration["input_hashes_before"]
    raw = json.dumps(migration).encode()
    path.write_bytes(raw)
    receipt["migration_receipt_sha256"] = hashlib.sha256(raw).hexdigest()
    with pytest.raises(ValueError, match="Migration input hashes"):
        REPORT["check_storage"](receipt)
