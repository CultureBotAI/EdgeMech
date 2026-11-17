"""Historical conclusions and altered evidence must not enter the fresh package."""
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/adhoc"))
SPEC = importlib.util.spec_from_file_location(
    "round02_assembly", ROOT / "scripts/adhoc/assemble_m5_round02_20261116.py")
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


def test_explicit_roles_and_ids_exclude_conclusions_and_other_cases():
    manifest = {"cases": [{"case_id": "fresh-47", "evidence_ids": ["a", "b", "fresh04-identity-context"]}],
                "files": [{"path": "raw", "role": "evidence", "evidence_ids": ["a"]},
                          {"path": "judgments", "role": "instructions", "evidence_ids": ["b"]},
                          {"path": "context", "role": "evidence", "evidence_ids": ["fresh04-identity-context"]},
                          {"path": "other", "role": "authority", "evidence_ids": ["c"]}]}
    assert [x["path"] for x in m.selected_inputs(manifest, {"fresh-47"})] == ["raw"]


def test_native_source_and_service_navigation_links_are_covered():
    value = {"records": [{"path": ".temp/native.txt"}],
             "service": {"result_path": ".temp/service.json"},
             "search": [{"private_receipt": ".temp/search.json"}],
             "external_root": "/retained/read-only/root"}
    assert set(m.private_references(value)) == {
        ".temp/native.txt", ".temp/service.json", ".temp/search.json"}


def test_changed_original_rejected_before_new_copy(tmp_path, monkeypatch):
    old, new = tmp_path / "old", tmp_path / "new"
    old.mkdir()
    new.mkdir()
    (old / "raw.txt").write_bytes(b"changed")
    monkeypatch.setattr(m, "OLD", old)
    monkeypatch.setattr(m, "ROOT", new)
    with pytest.raises(ValueError, match="evidence bytes changed"):
        m.copy_pin({"path": "raw.txt", "sha256": m.digest(b"original")}, Path("private"))
    assert list(new.iterdir()) == []


def test_copy_preserves_bytes_and_refuses_destination_change(tmp_path, monkeypatch):
    old, new = tmp_path / "old", tmp_path / "new"
    old.mkdir()
    new.mkdir()
    (old / "raw.txt").write_bytes(b"original")
    monkeypatch.setattr(m, "OLD", old)
    monkeypatch.setattr(m, "ROOT", new)
    pin = {"path": "raw.txt", "sha256": m.digest(b"original")}
    result = m.copy_pin(pin, Path("private"))
    target = new / result["path"]
    assert target.read_bytes() == b"original"
    target.chmod(0o600)
    target.write_bytes(b"changed")
    with pytest.raises(ValueError, match="evidence differs"):
        m.copy_pin(pin, Path("private"))
