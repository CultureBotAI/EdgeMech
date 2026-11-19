"""Hermetic witness-integrity tests; never duplicate the owner's mapping rule."""
from __future__ import annotations

import copy
import importlib.util
import json
import os
import socket
from pathlib import Path

import pytest

HELPER = Path(__file__).resolve().parents[1] / "scripts/adhoc/replay_lpsn_type_link_20261119.py"
spec = importlib.util.spec_from_file_location("lpsn_type_witness", HELPER)
witness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(witness)


def test_literal_record_preserves_multiline_and_crlf(tmp_path):
    path = tmp_path / "input.csv"
    path.write_bytes(b'a,b\r\nfirst,x\r\n"line1\r\nline2","JCM 14905; DSM 44728"\r\nlast,z\r\n')
    row, header, literal, physical = witness.literal_record(path, 2)
    assert row == {"a": "line1\r\nline2", "b": "JCM 14905; DSM 44728"}
    assert header == b"a,b\r\n"
    assert literal == b'"line1\r\nline2","JCM 14905; DSM 44728"\r\n'
    assert physical == [3, 4]


@pytest.mark.parametrize("body", [b"a,b\nx\n", b"a,b\nx,y,z\n", b"a,b\n"])
def test_bad_or_missing_csv_record_rejected(tmp_path, body):
    path = tmp_path / "input.csv"
    path.write_bytes(body)
    with pytest.raises(ValueError):
        witness.literal_record(path, 1)


def test_exclusive_private_creation_and_symlinks(tmp_path):
    output = tmp_path / "new" / "attempt"
    witness.private_dir(output)
    witness.save(output / "proof.json", b"{}\n")
    assert output.stat().st_mode & 0o777 == 0o700
    assert (output / "proof.json").stat().st_mode & 0o777 == 0o600
    with pytest.raises(FileExistsError):
        witness.save(output / "proof.json", b"replacement")
    with pytest.raises(ValueError, match="fresh"):
        witness.private_dir(output)
    link = tmp_path / "link"
    link.symlink_to(output, target_is_directory=True)
    with pytest.raises(ValueError, match="Symlink"):
        witness.private_dir(link / "child")
    assert (output / "proof.json").read_bytes() == b"{}\n"


def test_retained_match_never_becomes_original_ordinal(tmp_path, monkeypatch):
    monkeypatch.setattr(witness, "EDGE_ROW", 2)
    header = "\t".join(witness.ASSERTION) + "\n"
    matching = "\t".join(witness.ASSERTION.values()) + "\n"
    other = "lpsn:1\tbiolink:subclass_of\tlpsn:2\trdfs:subClassOf\n"
    path = tmp_path / "edges.tsv"
    path.write_text(header + matching + other + matching)
    result = witness.inspect_edges(path)
    assert result["retained_match_count"] == 2
    assert [item["data_row"] for item in result["retained_matches"]] == [1, 3]
    assert not result["retained_ordinal_matches_original_assertion"]
    assert result["retained_at_original_ordinal"]["subject"] == "lpsn:1"


@pytest.fixture
def packet_fixture(monkeypatch):
    text = json.dumps({"record_no": "781160", "nomenclatural_type": "JCM 14905"})
    monkeypatch.setattr(witness, "RECORD_SHA", witness.sha(text.encode()))
    record = {"text": text, "text_sha256": witness.RECORD_SHA,
              "source_relative_path": "lpsn_gss.csv", "locator": "CSV data row 29573"}
    occurrence = {**witness.ASSERTION, **witness.QUALIFIERS, "occurrence_id": witness.OCCURRENCE,
                  "origin_transform": "lpsn/edges.tsv", "transform_row_number": witness.EDGE_ROW}
    packet = {"occurrence_id": witness.OCCURRENCE, "original_assertion": dict(occurrence),
              "source_records": [record]}
    source = {"edge": dict(occurrence), "records": [copy.deepcopy(record)]}
    return packet, occurrence, source


@pytest.mark.parametrize("change", ["identity", "predicate", "qualifier", "ordinal", "duplicate",
                                    "text", "source_binding"])
def test_packet_binding_rejects_substitution(packet_fixture, change):
    packet, occurrence, source = packet_fixture
    assert witness.packet_records(packet, occurrence, source)
    if change == "identity":
        occurrence["object"] = "JCM:14905"
    elif change == "predicate":
        packet["original_assertion"]["predicate"] = "biolink:in_taxon"
    elif change == "qualifier":
        occurrence["agent_type"] = "automated_agent"
    elif change == "ordinal":
        packet["source_records"][0]["locator"] = "CSV data row 29574"
    elif change == "duplicate":
        packet["source_records"].append(copy.deepcopy(packet["source_records"][0]))
    elif change == "text":
        packet["source_records"][0]["text"] += " "
    else:
        source["records"] = []
    with pytest.raises(ValueError):
        witness.packet_records(packet, occurrence, source)


def test_private_owner_io_denies_overwrite_external_write_network_and_credentials(tmp_path):
    output = tmp_path / "private"
    witness.private_dir(output)
    witness.save(output / "existing", b"prior")
    with witness.private_owner_io(output):
        witness.save(output / "descriptor-write", b"exclusive\n")
        with (output / "new").open("w") as stream:
            stream.write("retained")
        with pytest.raises(FileExistsError):
            (output / "existing").open("w")
        with pytest.raises(ValueError, match="outside output"):
            (tmp_path / "external").open("w")
        with pytest.raises(ValueError, match="exclusive"):
            os.open(output / "existing", os.O_RDWR)
        with pytest.raises(ValueError, match="Credential"):
            (tmp_path / ".env").open()
        with pytest.raises(ValueError, match="prohibited"):
            socket.getaddrinfo("localhost", 443)
        with pytest.raises(ValueError, match="prohibited"):
            (output / "existing").unlink()
    assert (output / "existing").read_bytes() == b"prior"
    assert (output / "new").stat().st_mode & 0o777 == 0o600


def test_verify_detects_tamper_and_permissions(tmp_path):
    output = tmp_path / "attempt"
    witness.private_dir(output)
    artifact = output / "evidence.json"
    witness.save(artifact, b"{}\n")
    witness.save_json(output / "receipt.json", {"mode": "check", "artifacts": {
        "evidence.json": witness.pin(artifact)}})
    assert witness.verify_attempt(output)["verified"]
    artifact.chmod(0o644)
    with pytest.raises(ValueError, match="Nonprivate"):
        witness.verify_attempt(output)
    artifact.chmod(0o600)
    artifact.write_bytes(b"altered")
    with pytest.raises(ValueError, match="Artifact mismatch"):
        witness.verify_attempt(output)


@pytest.fixture
def replay_artifacts(tmp_path):
    output = tmp_path
    (output / "owner-output").mkdir()
    selected = {**witness.ASSERTION, **witness.QUALIFIERS}
    (output / "owner-output/edges.tsv").write_text(
        "\t".join(selected) + "\n" + "\t".join(selected.values()) + "\n")
    event = {"event": "return", "function": "_make_close_match_edge", "line": 999,
             "arguments": {"record_no": "781160", "strain_curie": witness.ASSERTION["object"],
                           "inferred": False}, "result": list(selected.values())}
    witness.save_json(output / "owner-trace.json", [event])
    witness.save_json(output / "selected-source.json", {"record_no": "781160"})
    witness.save_json(output / "owner-native-records.json", {"781160": {"row": {"record_no": "781160"}}})
    witness.save_json(output / "retained-transformed-linkage.json", {"retained_matches": [
        {"data_row": 200000, "row": {**selected, "publications": ""}}]})
    return output


def test_compare_preserves_qualifiers_and_absent_columns(replay_artifacts):
    result = witness.compare_outputs(replay_artifacts)
    assert not result["original_literal_transformed_row_recovered"]
    assert result["retained_comparisons"] == [{"retained_data_row": 200000, "differences": {},
                                               "retained_columns_absent_from_emission": ["publications"]}]
    assert result["selected_emission"]["agent_type"] == "manual_agent"


@pytest.mark.parametrize("change", ["duplicate", "qualifier", "branch", "trace", "source"])
def test_compare_rejects_ambiguous_or_changed_witness(replay_artifacts, change):
    output = replay_artifacts
    edges = output / "owner-output/edges.tsv"
    trace_path = output / "owner-trace.json"
    if change == "duplicate":
        edges.write_text(edges.read_text() + edges.read_text().splitlines()[1] + "\n")
    elif change == "qualifier":
        edges.write_text(edges.read_text().replace("manual_agent", "automated_agent"))
    elif change in ("branch", "trace"):
        events = json.loads(trace_path.read_text())
        if change == "branch":
            events[0]["arguments"]["inferred"] = True
        else:
            events[0]["result"][0] = "lpsn:OTHER"
        trace_path.write_text(json.dumps(events))
    else:
        (output / "owner-native-records.json").write_text('{"different": {}}')
    with pytest.raises(ValueError):
        witness.compare_outputs(output)
