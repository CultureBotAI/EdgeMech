"""Capture instants must cross the pinned review timestamp boundary unchanged (#133)."""

from __future__ import annotations

import importlib.util
from datetime import datetime
from pathlib import Path

import pytest
import yaml
from kg_microbe_reviews import ReviewError, validate_review

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "scripts/adhoc/review_bactotraits_identity_130_20261115.py"


@pytest.fixture
def helper(monkeypatch):
    monkeypatch.syspath_prepend(str(HELPER.parent))
    spec = importlib.util.spec_from_file_location("identity_review_130", HELPER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(("captured", "expected"), [
    ("2026-11-16T07:31:54.779207+00:00", "2026-11-16T07:31:54.779207Z"),
    ("2026-11-15T23:31:54.779207-08:00", "2026-11-16T07:31:54.779207Z"),
    ("2026-11-16T13:01:54.1+05:30", "2026-11-16T07:31:54.100000Z"),
    ("2026-11-16T07:31:54+00:00", "2026-11-16T07:31:54Z"),
    ("2026-11-16T07:31:54.779207Z", "2026-11-16T07:31:54.779207Z"),
])
def test_133_normalization_preserves_instant_and_microseconds(helper, captured, expected):
    normalized = helper.canonical_utc_timestamp(captured)
    assert normalized == expected
    assert datetime.fromisoformat(normalized) == datetime.fromisoformat(captured)


@pytest.mark.parametrize("captured", [
    "2026-11-16T07:31:54.779207", "2026-11-16", "not-a-timestamp", None,
    "2026-11-16T07:31:54.7792071+00:00",
])
def test_133_naive_invalid_or_unrepresentable_instants_are_rejected(helper, captured):
    with pytest.raises(ValueError):
        helper.canonical_utc_timestamp(captured)


def test_133_actual_capture_timestamp_is_accepted_by_pinned_review_contract_after_normalization(helper):
    path = ROOT / "reviews/structured/20261116T052355Z-fresh05-abstract-adapter/review.yaml"
    review = yaml.safe_load(path.read_text())
    review.update(started_at="2026-11-16T07:00:00Z", finished_at="2026-11-16T08:00:00Z",
                  review_id="20261116T080000Z-timestamp-contract-regression")
    captured = "2026-11-16T07:31:54.779207+00:00"
    review["evidence"][0]["accessed_at"] = captured
    with pytest.raises(ReviewError, match=r"evidence\.0\.accessed_at"):
        validate_review(review)
    review["evidence"][0]["accessed_at"] = helper.canonical_utc_timestamp(captured)
    validate_review(review)
    assert review["evidence"][0]["accessed_at"] == "2026-11-16T07:31:54.779207Z"
