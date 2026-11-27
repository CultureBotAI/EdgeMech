"""Fixture content checks preserve copies, failed checks and qualification holds."""

import importlib.util
import json
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "fixture_content", ROOT / "scripts/adhoc/inspect_restart_fixture_content_20261126.py")
helper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper)


@pytest.fixture
def inputs(tmp_path):
    review = {"review_id": "20000101T000000Z-fresh-47-readiness-reviewer-a",
              "title": "Fixture", "summary": "Fixture",
              "reviewer": {"independence_basis": "Fixture only"},
              "scope": {"description": "Fixture", "selection": "Fixture"},
              "limitations": ["Fixture"], "assessments": [{"summary": "Authored fixture"}],
              "unrelated_private_prose": "SECRET_PROSE_OR_OPERATIONAL_PATH"}
    raw = json.dumps(review).encode()
    source, copy = tmp_path / "source.yaml", tmp_path / "copy.yaml"
    source.write_bytes(raw)
    copy.write_bytes(raw)
    documents = [{"sha256": helper.digest(raw), "review_id": review["review_id"]}]
    locators = [{"path": str(path), "sha256": helper.digest(raw)} for path in (source, copy)]
    return tmp_path, documents, locators


def execute(inputs, *, seconds=60):
    root, documents, locators = inputs
    dp, lp = root / "documents.json", root / "locators.json"
    dp.write_text(json.dumps(documents))
    lp.write_text(json.dumps(locators))
    return helper.inspect(dp, helper.digest(dp.read_bytes()), lp, helper.digest(lp.read_bytes()), seconds)


def test_reads_each_copy_once_keeps_digest_only_content_and_no_qualification(inputs):
    root, _, _ = inputs
    before = {path.name: path.read_bytes() for path in root.iterdir()}
    result = execute(inputs)
    assert result["selected_variants"] == 1
    assert result["selected_locator_counts"]["readiness_a"] == 2
    assert all(result["observations"][0]["checks"].values())
    encoded = json.dumps(result)
    assert "SECRET_PROSE" not in encoded and str(root) not in encoded
    assert result["baseline_membership_qualified"] is False
    assert result["historical_execution_binding_verified"] is False
    assert result["scientific_review_coverage"] == 0
    assert result["queue_A_count"] is None and result["queue_B_count"] is None
    assert all((root / name).read_bytes() == raw for name, raw in before.items())


def test_nonfixture_content_is_reported_as_failed_checks_not_silently_removed(inputs):
    root, documents, locators = inputs
    for locator in locators:
        path = Path(locator["path"])
        value = json.loads(path.read_bytes())
        value["title"] = "Actual review with the same identifier"
        value["summary"] = {"nested": "DO_NOT_PUBLISH"}
        path.write_text(json.dumps(value))
        locator["sha256"] = helper.digest(path.read_bytes())
    documents[0]["sha256"] = locators[0]["sha256"]
    result = execute(inputs)
    checks = result["observations"][0]["checks"]
    assert checks["fixture_title"] is False and checks["fixture_summary"] is False
    assert "DO_NOT_PUBLISH" not in json.dumps(result)


def test_changed_second_copy_fails_even_when_first_variant_was_parsed(inputs):
    Path(inputs[2][1]["path"]).write_text("changed")
    with pytest.raises(ValueError, match="locator changed"):
        execute(inputs)


@pytest.mark.parametrize("kind", ["fifo", "symlink", "directory"])
def test_nonregular_selected_input_is_refused_without_blocking(inputs, kind):
    path = Path(inputs[2][0]["path"])
    path.unlink()
    if kind == "fifo":
        os.mkfifo(path)
    elif kind == "symlink":
        path.symlink_to(inputs[2][1]["path"])
    else:
        path.mkdir()
    with pytest.raises((ValueError, OSError)):
        execute(inputs)


@pytest.mark.parametrize("damage", ["duplicate_variant", "nested_ID", "unknown_locator", "missing_locator"])
def test_bad_identity_accounting_is_not_silent_omission(inputs, damage):
    _, documents, locators = inputs
    if damage == "duplicate_variant":
        documents.append(dict(documents[0]))
    elif damage == "nested_ID":
        documents[0]["review_id"] = {"secret": "DO_NOT_PUBLISH"}
    elif damage == "unknown_locator":
        locators[0]["sha256"] = "f" * 64
    else:
        locators.clear()
    with pytest.raises(ValueError):
        execute(inputs)


def test_duplicate_metadata_keys_and_stale_pins_are_rejected(tmp_path):
    path = tmp_path / "metadata.json"
    path.write_bytes(b'[{"sha256":"one","sha256":"two"}]')
    with pytest.raises(ValueError):
        helper.pinned(path, helper.digest(path.read_bytes()))
    path.write_bytes(b"[]")
    with pytest.raises(ValueError, match="changed"):
        helper.pinned(path, "0" * 64)


@pytest.mark.parametrize("seconds", [0, 61, True, 1.5])
def test_budget_validation(inputs, seconds):
    with pytest.raises(ValueError, match="budget"):
        execute(inputs, seconds=seconds)


def test_elapsed_and_byte_budgets_fail_without_qualification(inputs, monkeypatch):
    ticks = iter([0, 0, 61])
    monkeypatch.setattr(helper.time, "monotonic", lambda: next(ticks))
    with pytest.raises(TimeoutError):
        execute(inputs)
    monkeypatch.setattr(helper.time, "monotonic", lambda: 0)
    monkeypatch.setattr(helper, "MAX_TOTAL_BYTES", 1)
    with pytest.raises(ValueError, match="total read"):
        execute(inputs)


def test_stub_requires_exact_content_and_fixture_family_requires_explicit_content():
    stub = {"review_id": "original-review", "targets": [{"target_id": "original-occurrence"}]}
    assert helper.content_checks(stub, "canonical_stub")["exact_stub_without_assessments"] is True
    assert helper.content_checks({**stub, "assessments": [{}]}, "canonical_stub")[
        "exact_stub_without_assessments"] is False
    review = {"reviewer": {}, "scope": {}, "assessments": [{}], "limitations": []}
    assert not any(helper.content_checks(review, "occurrence_fixture").values())


def test_no_selected_documents_cannot_pass(inputs):
    inputs[1][0]["review_id"] = "unrelated"
    with pytest.raises(ValueError, match="no selected"):
        execute(inputs)
