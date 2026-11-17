"""Arbitrary source publication needs exact file coverage and identified review."""
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts/adhoc"))
SPEC = importlib.util.spec_from_file_location(
    "public_source_gate", ROOT / "scripts/adhoc/gate_round02_public_sources_20261116.py")
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


def test_python_escaped_literals_are_counted_as_their_rendered_quote():
    raw = b'QUOTE = "two words\\n" "three more words"\n'
    assert "two words three more words" in m.literals(Path("example.py"), raw)


def test_unreviewed_prose_attestation_is_not_inferred(tmp_path):
    with pytest.raises(ValueError, match="attestation"):
        m.gate({"root": str(tmp_path), "review_attestation": {"reviewer": "agent"}})


def test_missing_new_file_invalidates_earlier_review(tmp_path, monkeypatch):
    monkeypatch.setattr(m, "proposed_sources", lambda root, baseline: {"new.md"})
    with pytest.raises(ValueError, match="inventory differs"):
        m.gate({"root": str(tmp_path), "baseline": "HEAD", "files": [],
                "review_attestation": {"reviewer": "agent", "all_files_inspected": True,
                                       "no_unaccounted_external_quotations": True}})
