"""Adversarial checks for two frozen owner replays, not scientific rules."""

import copy
import importlib.util
import json
import os
import socket
import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

SPEC = importlib.util.spec_from_file_location(
    "first43_replay", Path(__file__).parents[1] /
    "scripts/adhoc/replay_metatraits_discrete_20261119.py")
replay = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(replay)


def source_record(case_name="first43"):
    case = replay.retained_case(case_name)
    return {"tax_name": case["taxon"], "summaries": [copy.deepcopy(case["summary"])]}


@pytest.mark.parametrize("mutation", ["taxon", "polarity", "percentage", "count", "databases",
                                     "duplicate", "missing", "discrete"])
@pytest.mark.parametrize("case_name", ["first43", "first28"])
def test_changed_source_or_multiplicity_rejected(mutation, case_name):
    record = source_record(case_name)
    if mutation == "taxon":
        record["tax_name"] = "another organism"
    elif mutation == "duplicate":
        record["summaries"] *= 2
    elif mutation == "missing":
        record["summaries"] = []
    else:
        opposite = "true" if case_name == "first43" else "false"
        key, value = {"polarity": ("majority_label", f"{opposite}: (100%)"),
                      "percentage": ("percentages", {opposite: 100.0}),
                      "count": ("num_observations", 11),
                      "databases": ("unique_databases", 1),
                      "discrete": ("is_discrete", False)}[mutation]
        record["summaries"][0][key] = value
    with pytest.raises(ValueError):
        replay.selected_summary(record, case_name)


@pytest.mark.parametrize("case_name", ["first43", "first28"])
def test_source_selector_retains_actual_ordinal_and_typed_summary(case_name):
    record = source_record(case_name)
    original = copy.deepcopy(record["summaries"][0])
    record["summaries"].insert(0, {"name": "unrelated", "majority_label": "true"})
    index, selected = replay.selected_summary(record, case_name)
    assert index == 1 and selected == original
    assert selected["percentages"] == replay.CASES[case_name]["summary"]["percentages"]


def test_only_frozen_cases_admitted_and_first43_remains_default():
    assert set(replay.CASES) == {"first43", "first28"}
    assert replay.selected_summary(source_record()) == replay.selected_summary(
        source_record(), "first43")
    with pytest.raises(ValueError, match="Only first43 and first28"):
        replay.selected_summary(source_record(), "first99")
    with pytest.raises(ValueError, match="Wrong source taxon"):
        replay.selected_summary(source_record("first28"))


def test_runtime_code_check_rejects_same_named_stub_and_alias_path(tmp_path):
    path = tmp_path / "owner.py"
    source = "def owner(value):\n    return value\n"
    namespace = {}
    exec(compile(source, str(path), "exec", dont_inherit=True), namespace)
    replay.verify_callable(namespace["owner"], path, source)
    with pytest.raises(ValueError, match="Runtime code differs"):
        replay.verify_callable(namespace["owner"], path, source.replace("return value", "return 0"))
    with pytest.raises(ValueError, match="source path mismatch"):
        replay.verify_callable(namespace["owner"], tmp_path / "alias.py", source)


def test_headers_read_only_constructor_expressions_without_executing_constructor(tmp_path):
    base = tmp_path / "kg_microbe/transform_utils/transform.py"
    producer = tmp_path / replay.PRODUCER
    producer.parent.mkdir(parents=True)
    base.write_text("class Transform:\n"
                    "    def __init__(self):\n"
                    "        raise RuntimeError('constructor must not run')\n"
                    "        self.node_header = [ID]\n"
                    "        self.edge_header = [SUBJECT]\n")
    producer.write_text("class MetaTraitsTransform:\n"
                        "    def __init__(self):\n"
                        "        self.edge_header = self.edge_header + ['has_percentage']\n"
                        "    def _init_from_shared_data(self, data):\n"
                        "        self.edge_header = data['edge_header']\n"
                        "        self.node_header = data['node_header']\n")
    assert replay.headers_from_owner(tmp_path, SimpleNamespace(ID="id", SUBJECT="subject")) == {
        "node_header": ["id"], "edge_header": ["subject", "has_percentage"]}


def test_gtdb_configuration_comes_from_selected_owner_without_constructor(tmp_path):
    base = tmp_path / "kg_microbe/transform_utils/transform.py"
    producer = tmp_path / replay.GTDB_PRODUCER
    producer.parent.mkdir(parents=True)
    base.write_text("class Transform:\n"
                    "    def __init__(self):\n"
                    "        self.node_header = [ID]\n"
                    "        self.edge_header = [SUBJECT]\n")
    producer.write_text("class MetaTraitsGTDBTransform:\n"
                        "    def __init__(self):\n"
                        "        raise RuntimeError('must not run')\n"
                        "        self.edge_header = self.edge_header + ['has_percentage']\n"
                        "        self.knowledge_source = 'infores:gtdb-metatraits'\n")
    assert replay.owner_knowledge_source(tmp_path, "first28") == "infores:gtdb-metatraits"
    assert replay.headers_from_owner(
        tmp_path, SimpleNamespace(ID="id", SUBJECT="subject"), "first28") == {
            "node_header": ["id"], "edge_header": ["subject", "has_percentage"]}
    producer.write_text(producer.read_text().replace("gtdb-metatraits", "metatraits"))
    with pytest.raises(ValueError, match="knowledge source changed"):
        replay.owner_knowledge_source(tmp_path, "first28")


def test_private_files_exclusive_even_under_permissive_umask(tmp_path):
    tmp_path.chmod(0o755)
    directory = tmp_path / "new-parent" / "attempt"
    prior = os.umask(0)
    try:
        replay.create_private_dir(directory)
        path = directory / "artifact"
        witness = replay.save_private(path, b"retained\n")
    finally:
        os.umask(prior)
    assert stat.S_IMODE(tmp_path.stat().st_mode) == 0o755
    assert stat.S_IMODE(directory.parent.stat().st_mode) == 0o700
    assert stat.S_IMODE(directory.stat().st_mode) == 0o700
    assert witness["mode"] == "0o600"
    assert witness["sha256"] == replay.sha(path.read_bytes())
    with pytest.raises(FileExistsError):
        replay.save_private(path, b"overwrite")
    with pytest.raises(ValueError, match="fresh directory"):
        replay.create_private_dir(directory)
    assert path.read_bytes() == b"retained\n"


def test_owner_io_keeps_writes_private_exclusive_and_bounded(tmp_path):
    output = tmp_path / "private"
    replay.create_private_dir(output)
    with replay.private_owner_io(output):
        path = output / "owner.tsv"
        with path.open("w") as stream:
            stream.write("unchanged serialization\n")
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
        with pytest.raises(FileExistsError):
            path.open("w")
        with pytest.raises(ValueError, match="outside output"):
            (tmp_path / "escape").open("w")
        with pytest.raises(ValueError, match="exclusive"):
            os.open(path, os.O_WRONLY | os.O_TRUNC)
        with pytest.raises(ValueError, match="Credential access"):
            (tmp_path / ".netrc").open()
        with pytest.raises(ValueError, match="prohibited"):
            socket.getaddrinfo("example.invalid", 443)
    assert path.read_text() == "unchanged serialization\n"


@pytest.mark.parametrize("field,value", [("predicate", "biolink:has_phenotype"),
                                         ("has_percentage", "100.0"),
                                         ("unit", "percent"), ("negated", "true"),
                                         ("subject", "NCBITaxon:other")])
def test_all_edge_qualifiers_compared_not_only_triple(field, value):
    frozen = {"subject": replay.SUBJECT, "predicate": "biolink:capable_of",
              "object": replay.OBJECT, "has_percentage": "0.0", "unit": ""}
    emitted = {**frozen, field: value}
    with pytest.raises(ValueError, match="differs from frozen original"):
        replay.compare_edge(emitted, frozen)


def test_missing_empty_column_is_explicit_and_nonempty_column_is_rejected():
    result = replay.compare_edge({"object": replay.OBJECT},
                                 {"object": replay.OBJECT, "publications": ""})
    assert result["original_columns_absent_from_owner_header"] == ["publications"]
    with pytest.raises(ValueError):
        replay.compare_edge({"object": replay.OBJECT},
                            {"object": replay.OBJECT, "publications": "some citation"})


@pytest.mark.parametrize("case_name", ["first43", "first28"])
def test_changed_frozen_packet_rejected_even_if_internal_hash_recomputed(tmp_path, case_name):
    for name in replay.CASES[case_name]["packet_pins"]:
        (tmp_path / name).write_text(json.dumps({"text": "changed", "text_sha256":
                                               replay.sha(b"changed")}))
    with pytest.raises(ValueError, match="Frozen packet mismatch"):
        replay.inspect_inputs(tmp_path / "unused-owner", tmp_path, case_name)


def test_output_tsv_preserves_multiplicity_and_omitted_trailing_cells(tmp_path):
    path = tmp_path / "edges.tsv"
    path.write_bytes(b"subject\tpredicate\tvalue\nS\tP\nS\tP\n")
    header, raw, rows = replay.read_rows(path)
    assert header == ["subject", "predicate", "value"]
    assert raw == [["S", "P"], ["S", "P"]]
    assert rows == [{"subject": "S", "predicate": "P", "value": ""}] * 2


def readback_fixture(tmp_path, case_name="first43"):
    case = replay.retained_case(case_name)
    output = tmp_path / "attempt"
    replay.create_private_dir(output)
    replay.create_private_dir(output / "owner-output")
    record = source_record(case_name)
    replay.save_json(output / f"original-source-line-{case['raw_line']}.jsonl", record)
    replay.save_json(output / "bounded-input.jsonl", record)
    percentage = "0.0" if case_name == "first43" else "100.0"
    raw = ("subject\tpredicate\tobject\thas_percentage\n"
           f"{case['subject']}\t{case['predicate']}\t{case['object']}\t{percentage}\n").encode()
    edge_path = "owner-output/bounded-input_edges.tsv"
    replay.save_private(output / edge_path, raw)
    replay.save_private(output / f"original-edge-{case['edge_row']}.tsv", raw)
    header, raw_rows, rows = replay.read_rows(output / edge_path)
    receipt = {"status": "replayed", "case": case_name, "occurrence_id": case["occurrence"],
               "selected_summary_index_zero_based": 0, "original_edge": rows[0],
               "owner_mapping": {"edge_header": header}, "emitted_raw_rows": raw_rows,
               "comparison": replay.compare_edge(rows[0], rows[0]),
               "emitted_line_hashes": {edge_path: [replay.sha(line) for line in
                                                   raw.splitlines(keepends=True)]},
               "artifact_pins": {str(path.relative_to(output)): replay.pin(path)
                                 for path in output.rglob("*") if path.is_file()}}
    replay.save_json(output / "receipt.json", receipt)
    return output, receipt


@pytest.mark.parametrize("case_name", ["first43", "first28"])
def test_separate_readback_checks_each_row_and_hash(tmp_path, case_name):
    output, receipt = readback_fixture(tmp_path, case_name)
    assert replay.verify_artifacts(output, case_name)["emitted_edge_rows"] == 1
    path = output / "owner-output/bounded-input_edges.tsv"
    path.write_bytes(path.read_bytes().replace(b"0.0", b"1.0"))
    with pytest.raises(ValueError, match="Artifact changed"):
        replay.verify_artifacts(output, case_name)
    # Even re-pinning the changed artifact cannot hide disagreement with the receipt rows.
    receipt["artifact_pins"][str(path.relative_to(output))] = replay.pin(path)
    (output / "receipt.json").write_bytes(replay.json_bytes(receipt))
    with pytest.raises(ValueError, match="raw rows differ"):
        replay.verify_artifacts(output, case_name)


@pytest.mark.parametrize("case_name", ["first43", "first28"])
def test_separate_readback_rejects_multiple_emitted_occurrences(tmp_path, case_name):
    output, receipt = readback_fixture(tmp_path, case_name)
    path = output / "owner-output/bounded-input_edges.tsv"
    path.write_bytes(path.read_bytes() + path.read_bytes().splitlines(keepends=True)[1])
    receipt["artifact_pins"][str(path.relative_to(output))] = replay.pin(path)
    (output / "receipt.json").write_bytes(replay.json_bytes(receipt))
    with pytest.raises(ValueError, match="exactly one emitted"):
        replay.verify_artifacts(output, case_name)


def test_readback_rejects_cross_case_receipt_even_with_selected_occurrence_id(tmp_path):
    output, receipt = readback_fixture(tmp_path, "first28")
    with pytest.raises(ValueError, match="selected case receipt"):
        replay.verify_artifacts(output)
    receipt["occurrence_id"] = replay.OCCURRENCE
    (output / "receipt.json").write_bytes(replay.json_bytes(receipt))
    with pytest.raises(ValueError, match="selected case receipt"):
        replay.verify_artifacts(output)


def test_runtime_inventory_skips_credential_paths_and_detects_code_changes(tmp_path, monkeypatch):
    monkeypatch.setattr(replay.sys, "prefix", str(tmp_path))
    code = tmp_path / "library.py"
    code.write_text("original code")
    excluded = tmp_path / "credentials"
    excluded.mkdir()
    (excluded / "do-not-read").touch()
    original_pin = replay.pin

    def guarded_pin(path):
        assert excluded not in path.parents
        return original_pin(path)

    monkeypatch.setattr(replay, "pin", guarded_pin)
    before = replay.runtime_identity()
    assert before["excluded_paths_not_read"] == ["credentials/do-not-read"]
    assert before == replay.runtime_identity()
    code.write_text("changed code")
    assert before != replay.runtime_identity()


def failure_run_fixture(tmp_path, monkeypatch, case_name="first43"):
    """Real private writes/pins and small runtime inventory; no owner emission."""
    case = replay.retained_case(case_name)
    kg, original, output = (tmp_path / name for name in ("owner", "original", "attempt"))
    for name in case["code"] + tuple(case["input_pins"]):
        path = kg / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"Synthetic input: {name}\n")
    original.mkdir()
    for name in case["packet_pins"]:
        (original / name).write_text("Synthetic original packet\n")
    executable = tmp_path / "runtime" / "bin" / "python"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"synthetic executable inventory member\n")
    helper = tmp_path / "helper.py"
    helper.write_text("# Synthetic retained helper source\n")
    monkeypatch.setattr(replay.sys, "prefix", str(executable.parent.parent))
    monkeypatch.setattr(replay.sys, "executable", str(executable))
    monkeypatch.setattr(replay, "__file__", str(helper))
    monkeypatch.setenv("PYSTOW_HOME", str(tmp_path / "unused-cache"))
    inspection = {"packet_pins": {name: replay.pin(original / name)
                                  for name in case["packet_pins"]}}
    monkeypatch.setattr(replay, "inspect_inputs", lambda *_: inspection)
    monkeypatch.setattr(replay, "prepare_owner", lambda *_: (SimpleNamespace(), {}))
    return SimpleNamespace(kg=kg, original=original, output=output, executable=executable,
                           helper=helper, owner_file=kg / case["code"][0], inspection=inspection)


@pytest.mark.parametrize("case_name", ["first43", "first28"])
@pytest.mark.parametrize("unavailable, diagnostic", [
    ("executable", "runtime_identity_after"),
    ("owner_file", "owner_identity_after"),
    ("helper", "helper_sha256"),
])
def test_failure_survives_unavailable_after_diagnostic(tmp_path, monkeypatch, case_name,
                                                     unavailable, diagnostic):
    fixture = failure_run_fixture(tmp_path, monkeypatch, case_name)
    original_error = ValueError("Original source inspection failure")

    def fail_inspection(*_):
        getattr(fixture, unavailable).unlink()
        raise original_error

    monkeypatch.setattr(replay, "inspect_inputs", fail_inspection)
    with pytest.raises(ValueError, match="Original source inspection failure") as caught:
        replay.run("plan", fixture.kg, fixture.original, fixture.output, case_name)
    assert caught.value is original_error
    path = fixture.output / "failure.json"
    raw = path.read_bytes()
    failure = json.loads(raw)
    assert raw and stat.S_IMODE(path.stat().st_mode) == 0o600
    assert failure["error_type"] == "ValueError" and failure["error"] == str(original_error)
    assert failure[diagnostic] is None
    assert failure["diagnostic_errors"] == {diagnostic: {
        "error_type": "FileNotFoundError",
        "error": failure["diagnostic_errors"][diagnostic]["error"]}}
    assert str(getattr(fixture, unavailable)) in failure["diagnostic_errors"][diagnostic]["error"]
    assert failure["runtime_identity_before"] == json.loads(
        (fixture.output / "runtime-before.json").read_bytes())
    assert failure["owner_identity_before"]
    assert failure["runtime_identity_unchanged"] is (None if unavailable == "executable" else True)
    assert failure["owner_identity_unchanged"] is (None if unavailable == "owner_file" else True)
    assert not (fixture.output / "receipt.json").exists()
    with pytest.raises(ValueError, match="fresh directory"):
        replay.run("plan", fixture.kg, fixture.original, fixture.output, case_name)
    assert path.read_bytes() == raw


def test_runtime_after_failure_is_persisted_when_diagnostic_retry_also_fails(tmp_path, monkeypatch):
    fixture = failure_run_fixture(tmp_path, monkeypatch)
    runtime_errors = []
    original_runtime_identity = replay.runtime_identity

    def inspect_then_remove_runtime(*_):
        fixture.executable.unlink()
        return fixture.inspection

    def observe_runtime():
        try:
            return original_runtime_identity()
        except FileNotFoundError as error:
            runtime_errors.append(error)
            raise

    monkeypatch.setattr(replay, "inspect_inputs", inspect_then_remove_runtime)
    monkeypatch.setattr(replay, "runtime_identity", observe_runtime)
    with pytest.raises(FileNotFoundError) as caught:
        replay.run("plan", fixture.kg, fixture.original, fixture.output)
    assert len(runtime_errors) == 2 and caught.value is runtime_errors[0]
    failure = json.loads((fixture.output / "failure.json").read_bytes())
    assert failure["error_type"] == "FileNotFoundError"
    assert failure["error"] == str(runtime_errors[0])
    assert failure["runtime_identity_before"]["executable_pin"]
    assert failure["runtime_identity_after"] is None
    assert failure["runtime_identity_unchanged"] is None
    assert failure["diagnostic_errors"]["runtime_identity_after"] == {
        "error_type": "FileNotFoundError", "error": str(runtime_errors[1])}


@pytest.mark.parametrize("unavailable", ["executable", "owner_file"])
def test_incomplete_initial_snapshot_is_unknown_not_unchanged(tmp_path, monkeypatch, unavailable):
    fixture = failure_run_fixture(tmp_path, monkeypatch)
    getattr(fixture, unavailable).unlink()
    with pytest.raises(FileNotFoundError):
        replay.run("plan", fixture.kg, fixture.original, fixture.output)
    failure = json.loads((fixture.output / "failure.json").read_bytes())
    assert failure["owner_identity_before"] is None
    assert failure["owner_identity_unchanged"] is None
    if unavailable == "executable":
        assert failure["runtime_identity_before"] is None
        assert failure["runtime_identity_unchanged"] is None
    diagnostic = "runtime_identity_after" if unavailable == "executable" else "owner_identity_after"
    assert failure[diagnostic] is None
    assert failure["diagnostic_errors"][diagnostic]["error_type"] == "FileNotFoundError"


@pytest.mark.parametrize("changed, identity", [
    ("executable", "runtime"), ("owner_file", "owner"),
])
def test_available_changed_after_state_is_recorded_as_changed(tmp_path, monkeypatch, changed,
                                                            identity):
    fixture = failure_run_fixture(tmp_path, monkeypatch)

    def inspect_then_change(*_):
        getattr(fixture, changed).write_bytes(b"changed inventory member\n")
        return fixture.inspection

    monkeypatch.setattr(replay, "inspect_inputs", inspect_then_change)
    with pytest.raises(ValueError, match="changed during run"):
        replay.run("plan", fixture.kg, fixture.original, fixture.output)
    failure = json.loads((fixture.output / "failure.json").read_bytes())
    assert failure[f"{identity}_identity_unchanged"] is False
    assert failure[f"{identity}_identity_before"] != failure[f"{identity}_identity_after"]
    assert failure["diagnostic_errors"] == {}


def test_failure_record_write_error_preserves_original_exception_and_existing_bytes(
        tmp_path, monkeypatch, capsys):
    fixture = failure_run_fixture(tmp_path, monkeypatch)
    original_error = ValueError("Original failure with unavailable failure record path")
    existing = b"Already present; never overwrite\n"

    def fail_inspection(*_):
        replay.save_private(fixture.output / "failure.json", existing)
        raise original_error

    monkeypatch.setattr(replay, "inspect_inputs", fail_inspection)
    with pytest.raises(ValueError) as caught:
        replay.run("plan", fixture.kg, fixture.original, fixture.output)
    assert caught.value is original_error
    assert (fixture.output / "failure.json").read_bytes() == existing
    assert "Failure record could not be persisted: FileExistsError" in original_error.__notes__[0]
    assert "Failure record could not be persisted: FileExistsError" in capsys.readouterr().err


@pytest.mark.parametrize("stderr_available", [True, False])
def test_legacy_exception_survives_unwritable_failure_record_without_add_note(
        tmp_path, monkeypatch, capsys, stderr_available):
    class LegacyFailure(ValueError):
        add_note = None

    fixture = failure_run_fixture(tmp_path, monkeypatch)
    original_error = LegacyFailure("Original error on Python without callable add_note")
    original_save_json = replay.save_json

    def fail_inspection(*_):
        raise original_error

    def deny_failure_record(path, value):
        if path.name == "failure.json":
            raise PermissionError("Synthetic failure record permission denial")
        return original_save_json(path, value)

    class UnavailableStderr:
        def write(self, _):
            raise OSError("Synthetic stderr unavailable")

    monkeypatch.setattr(replay, "inspect_inputs", fail_inspection)
    monkeypatch.setattr(replay, "save_json", deny_failure_record)
    if not stderr_available:
        monkeypatch.setattr(replay.sys, "stderr", UnavailableStderr())
    with pytest.raises(LegacyFailure) as caught:
        replay.run("plan", fixture.kg, fixture.original, fixture.output)
    assert caught.value is original_error
    assert not (fixture.output / "failure.json").exists()
    if stderr_available:
        assert "Failure record could not be persisted: PermissionError" in capsys.readouterr().err


def test_standalone_runtime_smoke_preserves_attempts_and_reread_result(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location(
        "metatraits_failure_smoke_test", Path(__file__).parents[1] /
        "scripts/adhoc/check_metatraits_failure_runtime_20261119.py")
    smoke = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(smoke)
    monkeypatch.setattr(smoke, "ROOT", tmp_path)
    output = tmp_path / ".temp" / "failure-smoke"
    result = smoke.check(output)
    assert result["status"] == "passed" and result["checks"] == 4
    raw = (output / "result.json").read_bytes()
    assert result["result_pin"] == replay.pin(output / "result.json")
    assert {check["scenario"] for check in json.loads(raw)["checks"]} == set(smoke.SCENARIOS)
    assert (output / "removed_runtime/attempt/failure.json").is_file()
    assert (output / "removed_owner/attempt/failure.json").is_file()
    assert not (output / "denied_failure/attempt/failure.json").exists()
    with pytest.raises(ValueError, match="fresh directory"):
        smoke.check(output)
    assert (output / "result.json").read_bytes() == raw
    with pytest.raises(ValueError, match="beneath checkout .temp"):
        smoke.check(tmp_path / "outside-output")
    assert not (tmp_path / "outside-output").exists()
