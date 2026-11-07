"""Reject substituted experiment receipts in validation prose (EdgeMech #6)."""

import hashlib
import json
import runpy
from pathlib import Path

import pytest

REPORT = runpy.run_path(str(Path(__file__).parents[1] / "scripts/adhoc/summarize_validation_20261107.py"))


@pytest.fixture
def receipt(tmp_path):
    source = {"source_manifest_sha256": REPORT["SNAPSHOT_SHA256"]}
    manifest = {"source": source, "counters": REPORT["EXPECTED_COUNTERS"]}
    raw = json.dumps(manifest).encode()
    path = tmp_path / "manifest.json"
    path.write_bytes(raw)
    return {
        "manifest": str(path), "manifest_sha256": hashlib.sha256(raw).hexdigest(),
        "contract": "edgemech-storage-canary/v1",
        "source_sqlite_sha256": REPORT["SQLITE_SHA256"], "source_sqlite_bytes": 806912,
        "scientific_approvals_created": 0,
        "verification": {"verified": True, "rows": 1000, "table_rows": {"bundles": 1, "history": 1}},
        "status": {"source": source, "counters": dict(REPORT["EXPECTED_COUNTERS"])},
    }


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
