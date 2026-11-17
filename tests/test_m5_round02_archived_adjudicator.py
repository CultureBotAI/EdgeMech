"""Retrospective bounded checks of the exact historical driver, not batch approval."""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts/adhoc"))
SPEC = importlib.util.spec_from_file_location(
    "archival_canary", ROOT / "scripts/adhoc/canary_m5_round02_archived_adjudicator_20261116.py")
wrapper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(wrapper)


def test_archive_preserves_executed_bytes_and_exclusive_receipts(tmp_path):
    module = wrapper.load_archive()
    assert module.sha(wrapper.ARCHIVE.read_bytes()) == wrapper.EXECUTED_SHA256
    path = tmp_path / "receipt.json"
    module.write(path, {"original": True})
    raw = path.read_bytes()
    with pytest.raises(FileExistsError):
        module.write(path, {"overwritten": True})
    assert path.read_bytes() == raw
    missing = module.artifact(tmp_path / "missing.json", expected="required-hash")
    assert missing["exists"] is False and missing["hash_matches"] is False
    mismatch = module.artifact(path, expected="incorrect-hash")
    assert mismatch["exists"] is True and mismatch["hash_matches"] is False


def test_archived_command_guard_rejects_save_before_execution(tmp_path, monkeypatch):
    module = wrapper.load_archive()
    calls = []
    monkeypatch.setattr(module.subprocess, "run", lambda *args, **kwargs: calls.append(args))
    with pytest.raises(AssertionError):
        module.run(tmp_path, tmp_path, "attempt", ["python", "-m", "edgemech.occurrence_review", "save"])
    assert calls == []


def test_archived_inspection_keeps_missing_matrix_citation_and_missing_pair(tmp_path, monkeypatch):
    module = wrapper.load_archive()
    packet = {"occurrence_id": "original", "original_assertion": {"subject": "s"},
              "endpoints": {role: {"record_sha256": role + "-hash"} for role in ("subject", "object")}}
    (tmp_path / "packet.json").write_text(json.dumps(packet))
    (tmp_path / "view.json").write_text("{}")
    (tmp_path / "extra.json").write_text("{}")
    packet_sha = module.sha((tmp_path / "packet.json").read_bytes())
    sidecar = {"occurrence_id": "original", "proofs": [{
        "evidence_id": "packet-proof", "kind": "packet", "axes": ["source_fidelity"],
        "scope": "exact", "support": "supports", "scope_rationale": "Original input", "inspected_extent": "packet",
        "input": {"path": "packet.json", "sha256": packet_sha}, "reference": "packet.json"}]}
    (tmp_path / "proofs.json").write_text(json.dumps(sidecar))
    dims = {"axis": "source_fidelity", "category": "SUPPORTED", "scope": "original", "source_binding": "exact input"}
    review = {"review_id": "unique", "source": {"inputs": [{"path": "packet.json", "sha256": packet_sha}]},
              "targets": [{"target_id": "original", "path": "packet.json", "selector": "occurrence_id=original"}],
              "assessments": [{"summary": "Original reasoning", "evidence_ids": ["packet-proof"],
                               "dimensions": [{"name": k, "value": v} for k, v in dims.items()]}],
              "evidence": [{"evidence_id": "packet-proof", "snapshot_sha256": packet_sha, "locator": "original row"}],
              "checks": [], "verdict": "blocked", "completion": "partial"}
    (tmp_path / "input.json").write_text(json.dumps(review))
    case = {"case_id": "fresh-47", "occurrence_id": "original", "packet_path": "packet.json",
            "reviewer_view_path": "view.json", "original_assertion": packet["original_assertion"],
            "endpoints": {role: {"private_record_sha256": role + "-hash"} for role in ("subject", "object")},
            "evidence_ids": ["packet-proof", "required-extra"]}
    original = {"occurrence_id": "original", "assessments": [{"axis": "source_fidelity", "category": "SUPPORTED",
                "scope": "original", "rationale": "Original reasoning", "dimensions": {"source_binding": "exact input"},
                "evidence_ids": ["packet-proof", "required-extra"]}]}
    indexed = {"occurrence_id": "original", "input_path": "input.json", "proof_path": "proofs.json",
               "pair_paths": {"yaml": "missing/review.yaml", "markdown": "missing/review.md"}}
    pins = {"packet.json": {"path": "packet.json", "sha256": packet_sha, "role": "packet"},
            "extra.json": {"path": "extra.json", "sha256": module.sha(b"{}"), "role": "authority"}}
    evidence = {"packet-proof": pins["packet.json"], "required-extra": pins["extra.json"]}
    monkeypatch.setattr(module, "validate_packet", lambda *args, **kwargs: {"packet": "checked"})
    monkeypatch.setattr(module.production, "validate_review", lambda *args: None)
    monkeypatch.setattr(module.production, "_replay_evidence", lambda *args: {"packet-proof": {}})
    commands = []
    def command(root, out, label, argv):
        commands.append(label)
        return {"exit_status": 0 if label == "validate" else 1}
    monkeypatch.setattr(module, "run", command)
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir() if p.is_file()}
    result = module.inspect_case(tmp_path, tmp_path / "out", "reviewer-b", case, original, indexed, pins, evidence)
    report = json.loads(Path(result["path"]).read_bytes())
    assert commands == ["validate", "check"]
    assert report["canonical_pair_status"] == "failed_missing_pair"
    assert report["proof_coverage"]["canonical_evidence_proof_union"] == 1
    assert report["proof_coverage"]["expected"] == 2
    assert report["proof_coverage"]["missing_initial_citation_proofs"] == 1
    missing = report["proof_coverage"]["rows"][-1]
    assert missing["production_binding_status"] == "unavailable" and not missing["proof_present"]
    assert report["matrix_to_authored_canonical_comparison"][0]["removed_evidence_ids"] == ["required-extra"]
    assert all((tmp_path / name).read_bytes() == raw for name, raw in before.items())


def test_canary_rejects_wrong_private_source_before_executing_archive(tmp_path, monkeypatch):
    original = tmp_path / "original.py"
    original.write_text("different historical bytes")
    monkeypatch.setattr(wrapper.replay, "expected_entries", lambda config: None)
    called = []
    monkeypatch.setattr(wrapper.replay, "context", lambda *args: called.append(args))
    with pytest.raises(ValueError, match="exact executed"):
        wrapper.canary({}, original, tmp_path / ".temp" / "out", "reviewer-b")
    assert not called
