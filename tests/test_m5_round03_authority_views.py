"""Round03 evidence views preserve exact spans and do not republish evaluation prose."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts" / "adhoc"
sys.path.insert(0, str(SCRIPTS))


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


audit = load("audit_m5_authority_views_20261116")
assembly = load("assemble_m5_round03_20261116")


def test_utf8_match_offsets_and_full_inventory(tmp_path):
    raw = "neutral α\nevaluation β\n".encode()
    (tmp_path / "input.txt").write_bytes(raw)
    manifest = {"files": [{"path": "input.txt", "role": "authority", "sha256": audit.sha(raw)}]}
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    result = audit.inventory(tmp_path, "manifest.json")
    match = result["files"][0]["inspection_leads"][0]
    assert raw[match["byte_start"]:match["byte_end"]] == "evaluation β\n".encode()
    (tmp_path / "input.txt").write_bytes(raw + b"changed")
    with pytest.raises(ValueError, match="Retained input changed"):
        audit.inventory(tmp_path, "manifest.json")


def test_inventory_rejects_symlink_input(tmp_path):
    (tmp_path / "original").write_text("x")
    (tmp_path / "input").symlink_to(tmp_path / "original")
    with pytest.raises(ValueError, match="Symlink"):
        audit.checked(tmp_path, "input")


def test_literal_python_spans_keep_semantics_remove_separable_prose():
    raw = ('"""Historical evaluation α."""\n# Old verdict β\n'
           'VALUE = "α original value"\n'
           'def compute(x):\n    """Old review rationale."""\n    return x + VALUE\n').encode()
    view, receipt = assembly.bounded(raw, "owner.py")
    assert b"Historical" not in view and b"Old" not in view
    assert 'VALUE = "α original value"'.encode() in view
    assert b"return x + VALUE" in view
    for span in receipt["spans"]:
        assert (raw[span["source_byte_start"]:span["source_byte_end"]]
                == view[span["view_byte_start"]:span["view_byte_end"]])


def test_redacted_description_not_reintroduced_by_producer_property(monkeypatch):
    raw = ("class Example:\n    @property\n    def description(self):\n"
           '        return "Old historical judgment"\n'
           "    def identifier(self):\n        return 5\n").encode()
    monkeypatch.setattr(assembly, "PROCESS_SHA", assembly.rounds.digest(raw))
    view, _ = assembly.bounded(raw, "process-scopes.py")
    assert b"historical judgment" not in view
    assert b"description" not in view
    assert b"return 5" in view


def test_config_commentary_is_removed_without_modifying_values(monkeypatch):
    raw = b"# historical evaluation\nsource:\n  version: 2\n  # old verdict\n  url: x\n"
    monkeypatch.setattr(assembly, "DOWNLOAD_SHA", assembly.rounds.digest(raw))
    view, _ = assembly.bounded(raw, "download.yaml")
    assert b"historical" not in view and b"verdict" not in view
    assert b"version: 2" in view and b"url: x" in view


def test_convention_anchor_selects_sentence_without_line_number_dependency(monkeypatch):
    raw = b'old assessment\n\n"Taxon fixture" means an example. Excluding old result.\n'
    monkeypatch.setattr(assembly, "PREGO_SHA", assembly.rounds.digest(raw))
    view, receipt = assembly.bounded(raw, "source.txt")
    assert view == b'"Taxon fixture" means an example.'
    span = receipt["spans"][0]
    assert raw[span["source_byte_start"]:span["source_byte_end"]] == view


def test_canary_is_exclusive_and_rejects_saved_view_drift(tmp_path, monkeypatch):
    raw = b"original source\n"
    pin = {"path": "source.txt", "sha256": assembly.rounds.digest(raw), "version": "v1"}
    monkeypatch.setattr(assembly, "ROOT", tmp_path)
    monkeypatch.setattr(assembly.original_views, "ROOT", tmp_path)
    monkeypatch.setattr(assembly, "PREGO_SHA", pin["sha256"])
    monkeypatch.setattr(assembly, "prego_pin", lambda: pin)
    monkeypatch.setattr(assembly, "source", lambda _: raw)
    monkeypatch.setattr(assembly, "bounded", lambda r, p: (r, {"source_sha256": assembly.rounds.digest(r)}))
    assembly.canary()
    with pytest.raises(ValueError, match="exists"):
        assembly.canary()
    (tmp_path / assembly.CANARY / "view.txt").chmod(0o600)
    (tmp_path / assembly.CANARY / "view.txt").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="changed"):
        assembly.check_canary()
    assert (tmp_path / assembly.CANARY).stat().st_mode & 0o777 == 0o700


@pytest.mark.parametrize("damage", ["original", "span", "unbound_tail"])
def test_derivative_verifier_checks_original_and_complete_span_coverage(tmp_path, monkeypatch, damage):
    monkeypatch.setattr(assembly, "ROOT", tmp_path)
    package = tmp_path / assembly.PACKAGE
    package.mkdir(parents=True)
    raw = b"first source line\nsecond source line\n"
    view, receipt = assembly.bounded(raw, "source.txt")
    original_path, view_path, receipt_path = "original.txt", "view.txt", "receipt.json"
    receipt["original_path"] = original_path
    guide = {"inputs": [{"path": view_path, "receipt": receipt_path,
                         "source_sha256": assembly.rounds.digest(raw),
                         "view_sha256": assembly.rounds.digest(view)}]}
    config = {"files": [{"path": p} for p in (original_path, view_path, receipt_path)]}
    (tmp_path / original_path).write_bytes(raw)
    (tmp_path / view_path).write_bytes(view)
    (tmp_path / receipt_path).write_text(json.dumps(receipt))
    (package / "freeze-config.json").write_text(json.dumps(config))
    (package / "evidence-guide.json").write_text(json.dumps(guide))
    assert assembly.verify_views()["bounded_views_verified"] == 1
    if damage == "original":
        (tmp_path / original_path).write_bytes(raw + b"change")
    elif damage == "span":
        receipt["spans"][0]["source_byte_end"] += 1
    else:
        view += b"unbound evaluation"
        (tmp_path / view_path).write_bytes(view)
        receipt["view_sha256"] = assembly.rounds.digest(view)
        guide["inputs"][0]["view_sha256"] = assembly.rounds.digest(view)
    (tmp_path / receipt_path).write_text(json.dumps(receipt))
    (package / "evidence-guide.json").write_text(json.dumps(guide))
    with pytest.raises(ValueError):
        assembly.verify_views()
