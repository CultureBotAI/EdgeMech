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


def mixed_producer(monkeypatch):
    # Synthetic data only: no retained source text is embedded in a test/helper.
    raw = ('NOTE = (\n    "Current α definition; historical verdict v1; "\n'
           '    "counterevidence: exact identity remains unavailable."\n)\n'
           'def emit():\n    return NOTE\n').encode()
    omitted = b"historical verdict v1; "
    begin = raw.index(omitted)
    monkeypatch.setattr(assembly, "PRODUCER_SHA", assembly.rounds.digest(raw))
    monkeypatch.setattr(assembly, "PRODUCER_OMISSION", (begin, begin + len(omitted)))
    pin = {"path": "microbedecoder.py", "sha256": assembly.rounds.digest(raw),
           "role": "authority", "version": assembly.PRODUCER_VERSION}
    return raw, pin


def test_mixed_literal_removes_only_reviewed_history_preserves_counterevidence(monkeypatch):
    raw, pin = mixed_producer(monkeypatch)
    view, receipt = assembly.bounded(raw, pin["path"])
    assert b"historical verdict" not in view
    assert "Current α definition; ".encode() in view
    assert b"counterevidence: exact identity remains unavailable." in view
    assert b"return NOTE" in view
    assert receipt["policy"] == "producer_code_with_reviewed_literal_omission"
    omission, = receipt["reviewed_content_omissions"]
    start, end = omission["source_byte_start"], omission["source_byte_end"]
    assert raw[start:end] == b"historical verdict v1; "
    assert omission["sha256"] == assembly.rounds.digest(raw[start:end])
    assert omission["source_version"] == assembly.PRODUCER_VERSION
    for span in receipt["spans"]:
        first, last = span["source_byte_start"], span["source_byte_end"]
        assert not (first < end and start < last)
        assert raw[first:last] == view[span["view_byte_start"]:span["view_byte_end"]]
        assert assembly.rounds.digest(raw[first:last]) == span["sha256"]


def test_historical_keyword_is_not_a_blanket_string_deletion_rule():
    raw = (b'STATE = "withdrawn is a current status value; retain contrary evidence"\n'
           b'RULE = "historical data are permitted only under the current condition"\n')
    view, receipt = assembly.bounded(raw, "unrelated-producer.py")
    assert view == raw
    assert receipt["reviewed_content_omissions"] == []


def test_known_producer_changed_bytes_require_new_content_review(monkeypatch):
    raw, pin = mixed_producer(monkeypatch)
    with pytest.raises(ValueError, match="exact source hash"):
        assembly.bounded(raw + b"# different version\n", pin["path"])


@pytest.mark.parametrize("changed", ["version", "role", "path"])
def test_producer_pin_requires_exact_version_identity(monkeypatch, changed):
    _, pin = mixed_producer(monkeypatch)
    damaged = {**pin, changed: "unreviewed"}
    monkeypatch.setattr(assembly, "retained", lambda: {"files": [damaged]})
    with pytest.raises(ValueError, match="identity/version"):
        assembly.producer_pin()


@pytest.mark.parametrize("damage", ["source", "view", "helper_binding", "omission"])
def test_producer_canary_is_new_persisted_and_binding_sensitive(tmp_path, monkeypatch, damage):
    raw, pin = mixed_producer(monkeypatch)
    monkeypatch.setattr(assembly, "ROOT", tmp_path)
    monkeypatch.setattr(assembly.original_views, "ROOT", tmp_path)
    monkeypatch.setattr(assembly, "retained", lambda: {"files": [pin]})
    monkeypatch.setattr(assembly, "source", lambda _: raw)
    old = tmp_path / assembly.RUN / "authority-view-canary"
    old.mkdir(parents=True)
    (old / "view.txt").write_bytes(b"preserved old canary")
    result = assembly.producer_canary()
    assert result["scientific_ratings"] == 0
    target = tmp_path / assembly.PRODUCER_CANARY
    saved = json.loads((target / "receipt.json").read_text())
    assert (target / "source.py").read_bytes() == raw
    assert b"historical verdict" not in (target / "view.txt").read_bytes()
    assert saved["reviewed_content_omissions"]
    assert (old / "view.txt").read_bytes() == b"preserved old canary"
    with pytest.raises(ValueError, match="exists"):
        assembly.producer_canary()
    if damage in {"source", "view"}:
        name = "source.py" if damage == "source" else "view.txt"
        (target / name).chmod(0o600)
        (target / name).write_bytes(b"changed")
    else:
        if damage == "helper_binding":
            saved["helper_sha256"] = "0" * 64
        else:
            saved["reviewed_content_omissions"] = []
        (target / "receipt.json").chmod(0o600)
        (target / "receipt.json").write_text(json.dumps(saved))
    with pytest.raises(ValueError, match="changed"):
        assembly.check_producer_canary()


@pytest.mark.parametrize("damage", ["omission", "version", "retained_history"])
def test_package_verifier_replays_reviewed_literal_policy(tmp_path, monkeypatch, damage):
    raw, pin = mixed_producer(monkeypatch)
    monkeypatch.setattr(assembly, "ROOT", tmp_path)
    package = tmp_path / assembly.PACKAGE
    package.mkdir(parents=True)
    view, receipt = assembly.bounded(raw, pin["path"])
    receipt.update(original_path="source.py", version=pin["version"])
    item = {"path": "view.txt", "receipt": "receipt.json", "source_name": pin["path"],
            "version": pin["version"], "source_sha256": assembly.rounds.digest(raw),
            "view_sha256": assembly.rounds.digest(view)}
    (tmp_path / "source.py").write_bytes(raw)
    (tmp_path / "view.txt").write_bytes(view)
    (tmp_path / "receipt.json").write_text(json.dumps(receipt))
    (package / "freeze-config.json").write_text(json.dumps(
        {"files": [{"path": p} for p in ("source.py", "view.txt", "receipt.json")]}))
    (package / "evidence-guide.json").write_text(json.dumps({"inputs": [item]}))
    assert assembly.verify_views()["bounded_views_verified"] == 1
    if damage == "omission":
        receipt["reviewed_content_omissions"] = []
    elif damage == "version":
        receipt["version"] = item["version"] = "wrong-version"
    else:
        # Rehashing an unredacted derivative does not make the known policy pass.
        (tmp_path / "view.txt").write_bytes(raw)
        receipt["view_sha256"] = item["view_sha256"] = assembly.rounds.digest(raw)
    (tmp_path / "receipt.json").write_text(json.dumps(receipt))
    (package / "evidence-guide.json").write_text(json.dumps({"inputs": [item]}))
    with pytest.raises(ValueError, match="changed"):
        assembly.verify_views()
