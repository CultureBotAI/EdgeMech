"""Private retained bytes remain pinned, bounded and distinct from qualification."""

import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "retained_text", ROOT / "scripts/adhoc/capture_restart_retained_text_20261126.py")
helper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper)


def fixture(tmp_path, raws, mode="json"):
    paths, records = [], []
    for index, raw in enumerate(raws):
        path = tmp_path / f"source-{index}.data"
        path.write_bytes(raw)
        paths.append(path)
        records.append(f"{helper.common.sha(raw)}  {path}\n")
    inventory = tmp_path / "inventory.txt"
    inventory.write_text("".join(records))
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"version": 1, "format": mode, "inventory": {
        "path": str(inventory), "sha256": helper.common.sha(inventory.read_bytes()),
        "encoding": "sha256-lines"}}))
    return manifest, helper.common.sha(manifest.read_bytes()), paths


def test_private_json_preserves_nested_values_and_copy_multiplicity(tmp_path):
    raw = b'{"cases":[{"occurrence_id":"unqualified","rationale":"private"}],"scientific_review_coverage":99}'
    manifest, pin, _ = fixture(tmp_path, [raw, raw])
    result = helper.capture(manifest, pin)
    assert result["locator_records"] == 2 and result["distinct_read_hashes"] == 1
    assert result["documents"][0]["document"] == json.loads(raw)
    assert result["documents"][0]["text"].encode() == raw
    assert [row["position"] for row in result["locators"]] == [0, 1]
    assert result["scientific_review_coverage"] == 0
    assert result["queue_A_count"] is result["queue_B_count"] is None
    assert not result["full_target_frozen"] and not result["baseline_cutoff_frozen"]
    assert result["all_selected_inputs_observed_without_read_pin_or_decode_error"]


def test_markdown_preserves_exact_line_endings_and_unicode(tmp_path):
    raw = "# Retained α\r\n\r\n- no normalization\n".encode()
    manifest, pin, _ = fixture(tmp_path, [raw], "text")
    result = helper.capture(manifest, pin)
    assert result["documents"][0]["text"].encode() == raw
    assert result["document_status_counts"] == {"utf8_text_observed": 1}


@pytest.mark.parametrize("raw", [b'{"x":1,"x":2}', b'{"x":', b'\xff', b'{"x":NaN}',
                                 b'{"x":1e999}'])
def test_invalid_json_or_encoding_retains_exact_bytes_without_success(tmp_path, raw):
    manifest, pin, _ = fixture(tmp_path, [raw])
    result = helper.capture(manifest, pin)
    assert not result["all_selected_inputs_observed_without_read_pin_or_decode_error"]
    assert result["document_status_counts"] == {"unresolved_decode_or_json": 1}
    assert bytes.fromhex(result["documents"][0]["raw_hex"]) == raw


@pytest.mark.parametrize("raw", [b"null", b"[]", b"12", b'"scalar"'])
def test_valid_json_shapes_remain_values_without_assessment_claim(tmp_path, raw):
    manifest, pin, _ = fixture(tmp_path, [raw])
    result = helper.capture(manifest, pin)
    assert result["documents"][0]["document"] == json.loads(raw)
    assert result["scientific_review_coverage"] == 0


@pytest.mark.parametrize("kind", ["symlink", "fifo", "directory", "changed"])
def test_replaced_source_cannot_block_or_supply_unpinned_content(tmp_path, kind):
    manifest, pin, paths = fixture(tmp_path, [b"{}"])
    paths[0].unlink()
    if kind == "symlink":
        paths[0].symlink_to(manifest)
    elif kind == "fifo":
        os.mkfifo(paths[0])
    elif kind == "directory":
        paths[0].mkdir()
    else:
        paths[0].write_bytes(b'{"changed":true}')
    result = helper.capture(manifest, pin)
    assert result["documents"] == []
    assert result["locators"][0]["status"] == "unresolved_read_or_pin"
    assert not result["all_selected_inputs_observed_without_read_pin_or_decode_error"]


def test_changed_inventory_refuses_before_any_source_read(tmp_path, monkeypatch):
    manifest, pin, paths = fixture(tmp_path, [b"{}"])
    (tmp_path / "inventory.txt").write_text("changed")
    calls = []
    original = helper.common.read_pinned

    def record(path, *args):
        calls.append(path)
        return original(path, *args)

    monkeypatch.setattr(helper.common, "read_pinned", record)
    with pytest.raises(ValueError, match="hash mismatch"):
        helper.capture(manifest, pin)
    assert str(paths[0]) not in calls


@pytest.mark.parametrize("mutation", ["extra", "boolean_version", "nested_format", "duplicate"])
def test_strict_manifest_refuses_ambiguous_inputs(tmp_path, mutation):
    manifest, _, _ = fixture(tmp_path, [b"{}"])
    value = json.loads(manifest.read_bytes())
    if mutation == "duplicate":
        raw = b'{"version":1,"version":1,"format":"text","inventory":{}}'
    else:
        if mutation == "extra":
            value["extra"] = True
        elif mutation == "boolean_version":
            value["version"] = True
        else:
            value["format"] = {"private": "prose"}
        raw = json.dumps(value).encode()
    manifest.write_bytes(raw)
    with pytest.raises(ValueError):
        helper.capture(manifest, helper.common.sha(raw))


def test_selection_and_byte_limits_do_not_truncate_into_success(tmp_path, monkeypatch):
    manifest, pin, _ = fixture(tmp_path, [b"{}", b"[]"])
    monkeypatch.setattr(helper, "MAX_INPUTS", 1)
    with pytest.raises(ValueError, match="selection count"):
        helper.capture(manifest, pin)
    monkeypatch.setattr(helper, "MAX_INPUTS", 512)
    monkeypatch.setattr(helper, "MAX_SOURCE", 1)
    result = helper.capture(manifest, pin)
    assert result["documents"] == []
    assert not result["all_selected_inputs_observed_without_read_pin_or_decode_error"]
    monkeypatch.setattr(helper.common, "MAX_TOTAL", 1)
    with pytest.raises(ValueError, match="aggregate bound"):
        helper.capture(manifest, pin)


def test_main_refuses_support_pin_then_persists_error_report_exclusively(tmp_path, monkeypatch, capsys):
    manifest, pin, _ = fixture(tmp_path, [b'{"x":'])
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
    retained = output.read_bytes()
    assert receipt["output_sha256"] == helper.common.sha(retained)
    assert output.stat().st_mode & 0o777 == 0o600
    with pytest.raises(FileExistsError):
        helper.main()
    assert output.read_bytes() == retained


def test_valid_main_releases_private_content_only_to_result(tmp_path, monkeypatch, capsys):
    manifest, pin, _ = fixture(tmp_path, [b'{"private":"do not print body"}'])
    output = tmp_path / "result.json"
    monkeypatch.setattr(sys, "argv", [str(SPEC.origin), "--manifest", str(manifest),
                        "--manifest-sha256", pin, "--helper-sha256",
                        helper.common.sha(Path(SPEC.origin).read_bytes()), "--support-sha256",
                        helper.common.sha(helper.SUPPORT.read_bytes()), "--output", str(output)])
    monkeypatch.setattr(helper, "check_contracts", lambda: None)
    assert helper.main() == 0
    assert "do not print body" not in capsys.readouterr().out
    assert b"do not print body" in output.read_bytes()
