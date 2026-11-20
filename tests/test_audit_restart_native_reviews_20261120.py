"""Baseline inventory must preserve uncertainty and never manufacture membership."""

import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "native_inventory", ROOT / "scripts/adhoc/audit_restart_native_reviews_20261120.py"
)
helper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper)
ID = "urn:kg-microbe:occurrence:v1:" + "a" * 64
OTHER = "urn:kg-microbe:occurrence:v1:" + "b" * 64
CUTOFF = helper.instant("2026-11-20T05:26:45Z")


@pytest.fixture
def review():
    return {
        "review_id": "retained-partial", "started_at": "2026-11-19T00:00:00Z",
        "finished_at": "2026-11-19T00:01:00Z", "completion": "partial",
        "scientific_review": False, "reviewer": {"identity": "historical author"},
        "source": {"inputs": [{"path": "packet.json", "sha256": "c" * 64, "role": "target"}]},
        "targets": [{"target_id": ID, "kind": "snapshot_row"}],
        "assessments": [{"assessment_id": "partial", "outcome": "unknown", "target_ids": [ID]}],
        "evidence": [{"summary": "Mention only: " + OTHER}],
    }


def save(path, review):
    path.write_text(json.dumps(review))
    return path


def test_copies_and_changed_bytes_with_same_review_id_all_survive(tmp_path, review):
    paths = [save(tmp_path / name, review) for name in ("first", "copy")]
    revised = copy.deepcopy(review)
    revised["assessments"][0]["outcome"] = "concern"
    paths.append(save(tmp_path / "changed", revised))
    locators, documents, summary = helper.audit(paths, CUTOFF)
    assert len(locators) == 3 and len(documents) == 2
    assert locators[0]["sha256"] == locators[1]["sha256"] != locators[2]["sha256"]
    assert summary["distinct_declared_review_ids"] == 1
    assert {row["assessment_rows"][0]["outcome"] for row in documents} == {"unknown", "concern"}


def test_partial_engineering_and_unknown_outcome_are_observed_without_membership(review):
    result = helper.observations(review, CUTOFF)
    assert result["completion"] == "partial" and result["scientific_review_declared"] is False
    assert result["declared_assessed_occurrence_ids"] == [ID]
    assert result["membership_disposition"].startswith("UNRESOLVED")
    assert OTHER not in result["declared_assessed_occurrence_ids"]


def test_orphan_targets_and_population_mentions_never_become_bound_assessments(review):
    review["scope"] = {"reviewed_target_ids": [OTHER], "population_size": 17_637_435}
    review["targets"].append({"target_id": OTHER})
    orphan = "urn:kg-microbe:occurrence:v1:" + "d" * 64
    review["assessments"].append({"target_ids": [orphan]})
    result = helper.observations(review, CUTOFF)
    assert result["declared_assessed_occurrence_ids"] == [ID]
    assert result["orphan_assessment_occurrence_ids"] == [orphan]
    assert result["declared_occurrence_targets_without_assessments"] == [OTHER]


def test_fixture_content_is_flagged_even_in_nonfixture_filename_and_not_auto_excluded(review):
    review["reviewer"]["identity"] = "Fixture"
    review["review_id"] = "20000101T000000Z-fixture"
    review["source"]["inputs"][0]["role"] = "fixture input"
    result = helper.observations(review, CUTOFF)
    assert len(result["synthetic_content_markers"]) == 3
    assert result["declared_assessed_occurrence_ids"] == [ID]
    assert result["membership_disposition"].startswith("UNRESOLVED")


@pytest.mark.parametrize(("start", "finish", "expected"), [
    ("2026-11-19T00:00:00Z", "2026-11-20T05:26:45Z", "declared_at_or_before_cutoff"),
    ("2026-11-20T06:00:00Z", "2026-11-20T06:01:00Z", "declared_after_cutoff"),
    ("2026-11-19T00:00:00Z", "2026-11-20T06:00:00Z", "declared_straddles_cutoff"),
    ("2026-11-19T00:00:00Z", None, "unknown_or_incomplete_declared_timing"),
    ("2026-11-19T00:00:00Z", "2026-11-18T00:00:00Z", "invalid_declared_time_order"),
    ("2026-11-19T00:00:00Z", "2026-11-19T00:01:00", "unknown_or_incomplete_declared_timing"),
])
def test_cutoff_never_guesses_from_filename_or_missing_timezone(review, start, finish, expected):
    review.update(started_at=start, finished_at=finish)
    assert helper.observations(review, CUTOFF)["timing"] == expected


def test_missing_and_duplicate_key_inputs_are_retained_as_errors(tmp_path):
    duplicate = tmp_path / "duplicate.yaml"
    duplicate.write_text("review_id: first\nreview_id: replaced\n")
    locators, documents, summary = helper.audit([tmp_path / "missing", duplicate], CUTOFF)
    assert [row["status"] for row in locators] == ["unresolved_read", "unresolved_parse_or_shape"]
    assert len(documents) == 1 and not summary["all_locators_read_and_parsed"]
    assert summary["queue_A_count"] is None and summary["queue_B_count"] is None


def test_symlink_is_not_followed(tmp_path, review):
    path = save(tmp_path / "review", review)
    link = tmp_path / "link"
    link.symlink_to(path)
    locators, documents, summary = helper.audit([link], CUTOFF)
    assert locators[0]["status"] == "unresolved_read"
    assert documents == [] and not summary["all_locators_read_and_parsed"]


def test_malformed_assessment_shape_is_not_silently_discarded(tmp_path, review):
    review["assessments"] = {"lost": "assessment"}
    locators, _, summary = helper.audit([save(tmp_path / "review", review)], CUTOFF)
    assert locators[0]["status"] == "unresolved_parse_or_shape"
    assert not summary["all_locators_read_and_parsed"]


def test_main_retains_error_readback_and_never_overwrites_results(tmp_path, monkeypatch):
    paths = tmp_path / "paths.txt"
    paths.write_text(str(tmp_path / "absent") + "\n")
    result = tmp_path / "results"
    monkeypatch.setattr(helper, "check_contracts", lambda: None)
    monkeypatch.setattr(sys, "argv", [
        "audit", "--paths", str(paths), "--paths-sha256", hashlib.sha256(paths.read_bytes()).hexdigest(),
        "--cutoff", "2026-11-20T05:26:45Z", "--results", str(result),
    ])
    assert helper.main() == 1
    before = (result / "summary.json").read_bytes()
    assert json.loads(before)["locator_status_counts"] == {"unresolved_read": 1}
    with pytest.raises(FileExistsError):
        helper.main()
    assert (result / "summary.json").read_bytes() == before


def test_bad_inventory_pin_fails_before_output_creation(tmp_path, monkeypatch):
    paths = tmp_path / "paths.txt"
    paths.write_text(str(tmp_path / "absent") + "\n")
    result = tmp_path / "results"
    monkeypatch.setattr(sys, "argv", ["audit", "--paths", str(paths), "--paths-sha256", "f" * 64,
                                     "--cutoff", "2026-11-20T05:26:45Z", "--results", str(result)])
    with pytest.raises(ValueError, match="hash mismatch"):
        helper.main()
    assert not result.exists()
