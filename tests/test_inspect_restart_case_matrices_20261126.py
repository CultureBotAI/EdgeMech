"""Case matrices preserve rows/bindings and never manufacture review membership."""

import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "case_observer", ROOT / "scripts/adhoc/inspect_restart_case_matrices_20261126.py")
helper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper)
A = "urn:kg-microbe:occurrence:v1:" + "a" * 64
B = "urn:kg-microbe:occurrence:v1:" + "b" * 64


def raw_json(value):
    return json.dumps(value).encode()


def fixture(tmp_path, raws):
    entries = []
    for index, raw in enumerate(raws):
        path = tmp_path / f"source-{index}.json"
        path.write_bytes(raw)
        entries.append({"path": str(path), "sha256": helper.common.sha(raw)})
    locators = tmp_path / "locators.json"
    locators.write_bytes(raw_json(entries))
    manifest = tmp_path / "manifest.json"
    manifest.write_bytes(raw_json({"version": 1, "locator_artifacts": [
        {"path": str(locators), "sha256": helper.common.sha(locators.read_bytes())}]}))
    return manifest, helper.common.sha(manifest.read_bytes()), entries


def case(identifier=A, assessments=None):
    return {"case_id": "fixture-case", "occurrence_id": identifier,
            "assessments": [{"axis": "claim", "category": "UNRESOLVED"}]
            if assessments is None else assessments}


def test_duplicates_partial_axes_and_unbound_cases_are_retained(tmp_path):
    raw = raw_json({"round_id": "fixture-round", "cases": [case(), case(), case(B, []),
                    case("local-only")], "private_prose": "never copy this rationale",
                    "scientific_review_coverage": 99})
    manifest, pin, _ = fixture(tmp_path, [raw, raw])
    result = helper.inspect(manifest, pin)
    assert result["locator_records"] == 2 and result["distinct_read_hashes"] == 1
    assert result["case_rows_across_variants_not_population"] == 4
    assert result["assessment_rows_across_variants_not_population"] == 3
    assert result["canonical_case_ids_declared"] == [A, B]
    assert result["case_ids_with_assessment_rows_declared"] == [A]
    assert result["scientific_review_coverage"] == 0
    assert result["queue_A_count"] is result["queue_B_count"] is None
    assert not result["full_target_frozen"] and not result["baseline_cutoff_frozen"]
    assert "never copy" not in json.dumps(result)
    assert str(tmp_path) not in json.dumps(result)


@pytest.mark.parametrize("field,value", [
    ("case_id", {"private": "nested prose"}),
    ("occurrence_id", {"private": "nested prose"}),
    ("occurrence_id", "x" * 4097),
    ("occurrence_id", A + "\n"),
    ("assessments", {"private": "nested prose"}),
    ("assessments", [{"axis": {"private": "nested prose"}, "category": "SUPPORTED"}]),
    ("assessments", [{"axis": "claim", "category": {"private": "nested prose"}}]),
    ("assessments", [False]),
])
def test_bad_case_does_not_copy_nested_values_or_discard_other_cases(tmp_path, field, value):
    bad = case()
    bad[field] = value
    manifest, pin, _ = fixture(tmp_path, [raw_json({"cases": [bad, case(B)]})])
    result = helper.inspect(manifest, pin)
    assert result["unresolved_case_rows"] == 1
    assert result["case_ids_with_assessment_rows_declared"] == [B]
    assert len(result["documents"][0]["cases"]) == 2
    assert not result["all_selected_inputs_observed_without_shape_or_pin_error"]
    assert "nested prose" not in json.dumps(result)


@pytest.mark.parametrize("value", [None, {}, True, "not an array"])
def test_present_invalid_cases_are_not_treated_as_absent_or_empty(tmp_path, value):
    manifest, pin, _ = fixture(tmp_path, [raw_json({"cases": value})])
    result = helper.inspect(manifest, pin)
    assert result["document_status_counts"] == {"unresolved_document_shape": 1}
    assert not result["all_selected_inputs_observed_without_shape_or_pin_error"]


def test_native_document_and_empty_case_container_remain_distinct(tmp_path):
    manifest, pin, _ = fixture(tmp_path, [raw_json({"review_id": "native"}), raw_json({"cases": []})])
    result = helper.inspect(manifest, pin)
    assert result["document_status_counts"] == {
        "no_direct_cases_key": 1, "case_container_observations_only": 1}
    assert result["case_ids_with_assessment_rows_declared"] == []


@pytest.mark.parametrize("raw", [b'{"cases":[],"cases":[{}]}', b'{"cases": ['])
def test_duplicate_keys_and_malformed_json_remain_unresolved(tmp_path, raw):
    manifest, pin, _ = fixture(tmp_path, [raw])
    result = helper.inspect(manifest, pin)
    assert result["document_status_counts"] == {"unresolved_document_shape": 1}
    assert not result["all_selected_inputs_observed_without_shape_or_pin_error"]


def test_changed_raw_hash_never_produces_case_binding(tmp_path):
    manifest, pin, entries = fixture(tmp_path, [raw_json({"cases": [case()]})])
    Path(entries[0]["path"]).write_bytes(raw_json({"cases": [case(B)]}))
    result = helper.inspect(manifest, pin)
    assert result["locators"][0]["status"] == "unresolved_read_or_pin"
    assert result["documents"] == []
    assert not result["all_selected_inputs_observed_without_shape_or_pin_error"]


@pytest.mark.parametrize("kind", ["symlink", "fifo", "directory"])
def test_replaced_nonregular_source_refused_without_blocking(tmp_path, kind):
    manifest, pin, entries = fixture(tmp_path, [raw_json({"cases": [case()]})])
    source = Path(entries[0]["path"])
    source.unlink()
    if kind == "symlink":
        source.symlink_to(manifest)
    elif kind == "fifo":
        os.mkfifo(source)
    else:
        source.mkdir()
    result = helper.inspect(manifest, pin)
    assert result["locators"][0]["status"] == "unresolved_read_or_pin"


def test_artifact_hash_mismatch_refuses_before_source_reads(tmp_path, monkeypatch):
    manifest, pin, _ = fixture(tmp_path, [raw_json({"cases": [case()]})])
    (tmp_path / "locators.json").write_bytes(b"[]")
    calls = []
    original = helper.common.read_pinned

    def record(path, *args):
        calls.append(path)
        return original(path, *args)

    monkeypatch.setattr(helper.common, "read_pinned", record)
    with pytest.raises(ValueError, match="hash mismatch"):
        helper.inspect(manifest, pin)
    assert len(calls) == 2


def test_aggregate_and_case_bounds_refuse_instead_of_truncating(tmp_path, monkeypatch):
    manifest, pin, _ = fixture(tmp_path, [raw_json({"cases": [case(), case(B)]})])
    monkeypatch.setattr(helper, "MAX_ITEMS", 1)
    result = helper.inspect(manifest, pin)
    assert result["document_status_counts"] == {"unresolved_document_shape": 1}
    assert result["canonical_case_ids_declared"] == []
    monkeypatch.setattr(helper.common, "MAX_TOTAL", 1)
    with pytest.raises(ValueError, match="aggregate bound"):
        helper.inspect(manifest, pin)


def test_main_pins_support_and_preserves_unresolved_report(tmp_path, monkeypatch, capsys):
    manifest, pin, _ = fixture(tmp_path, [raw_json({"cases": None})])
    output = tmp_path / "result.json"
    argv = [str(SPEC.origin), "--manifest", str(manifest), "--manifest-sha256", pin,
            "--helper-sha256", helper.common.sha(Path(SPEC.origin).read_bytes()),
            "--support-sha256", "0" * 64, "--output", str(output)]
    monkeypatch.setattr(sys, "argv", argv)
    monkeypatch.setattr(helper, "check_contracts", lambda: None)
    with pytest.raises(ValueError, match="hash mismatch"):
        helper.main()
    assert not output.exists()
    argv[8] = helper.common.sha(helper.SUPPORT.read_bytes())
    assert helper.main() == 1
    receipt = json.loads(capsys.readouterr().out)
    before = output.read_bytes()
    assert receipt["output_sha256"] == helper.common.sha(before)
    assert json.loads(before)["scientific_review_coverage"] == 0
    with pytest.raises(FileExistsError):
        helper.main()
    assert output.read_bytes() == before
