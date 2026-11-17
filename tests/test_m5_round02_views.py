"""Blinding removes historical prose without losing original source identity."""
import copy
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/adhoc"))
SPEC = importlib.util.spec_from_file_location(
    "round02_views", ROOT / "scripts/adhoc/prepare_m5_round02_views_20261116.py")
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


def packet():
    return {"occurrence_id": "exact-original", "original_assertion": {"predicate": "original"},
            "endpoints": {"object": {"id": m.REDACTED_NODE, "record_sha256": "original-hash",
                "record": {"description": "Reviewed source-local process meaning for private prose",
                           "id": m.REDACTED_NODE, "name": "sulfite_respiration"}}},
            "measurement_context": {}, "source_records": [{"text": "literal original source"}],
            "original_occurrence": {"review_rationale": "historic label"}}


def test_exact_source_and_original_hash_preserved_without_historic_prose():
    source = packet()
    before = copy.deepcopy(source)
    view = m.projection(source)
    assert source == before
    assert "description" not in view["endpoints"]["object"]["record"]
    assert view["endpoints"]["object"]["record_sha256"] == "original-hash"
    assert view["source_records"] == source["source_records"]
    assert view["original_assertion"] == source["original_assertion"]
    assert "private prose" not in str(view) and "historic label" not in str(view)
    assert len(view["blinding"]["redactions"]) == 1


def test_unrecognized_replacement_requires_inspection():
    source = packet()
    source["endpoints"]["object"]["record"]["description"] = "different definition"
    with pytest.raises(ValueError, match="description changed"):
        m.projection(source)


def test_profile_derivative_retains_policy_but_removes_old_case_canary():
    raw = (ROOT / "docs/record-review-profile.md").read_text()
    derivative = m.blinded_profile(raw)
    assert "Its partial\nself-review" not in derivative
    assert "source contains conflicting strain" not in derivative
    assert "Positive or refuting claim" in derivative
    assert "Preparation receipts from PR #128" in derivative
