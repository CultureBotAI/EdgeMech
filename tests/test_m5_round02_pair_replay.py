"""Failure-preserving accounting for immutable round02 canonical replay."""
import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts/adhoc"))
SPEC = importlib.util.spec_from_file_location(
    "round02_pair_replay", ROOT / "scripts/adhoc/replay_m5_round02_pairs_20261116.py")
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


def config(tmp_path):
    cohort = json.loads((ROOT / m.rounds.COHORT).read_text())
    reviewers = {rid: {"root": str(tmp_path / rid), "matrix": "initial.json",
                       "canonical_identity": rid} for rid in ("reviewer-a", "reviewer-b")}
    return {"reviewers": reviewers, "package_sha256": "frozen-package",
            "entries": [{"reviewer": rid, "case_id": c["case_id"], "input": None,
                         "proofs": None, "review": None}
                        for rid in reviewers for c in cohort["cases"]]}


def test_missing_pairs_remain_in_fixed_twenty_denominator(tmp_path):
    settings = config(tmp_path)
    _, entries = m.expected_entries(settings)
    assert len(entries) == 20 and all(e["review"] is None for e in entries)
    settings["entries"].pop()
    with pytest.raises(ValueError, match="Exactly twenty"):
        m.expected_entries(settings)


def test_failed_contexts_preserve_every_expected_entry_and_unknown_proofs(tmp_path, monkeypatch):
    settings = config(tmp_path)
    monkeypatch.setattr(m, "check_canary", lambda *args, **kwargs: {})
    def failed(*args):
        raise ValueError("retained matrix unavailable")
    monkeypatch.setattr(m, "context", failed)
    result = m.run(settings, tmp_path / ".temp" / "batch", "batch", canary=tmp_path)
    assert result["summary"]["entries_retained"] == 20
    assert result["summary"]["entries_with_unknown_proof_denominator"] == 20
    assert result["summary"]["all_parity_and_integrity_passed_pairs"] == 0
    assert not result["summary"]["technical_integrity_complete"]
    assert len(result["rows"]) == 20


def test_batch_refuses_missing_canary_before_creating_output(tmp_path):
    output = tmp_path / ".temp" / "batch"
    with pytest.raises(ValueError, match="persisted canary"):
        m.run(config(tmp_path), output, "batch")
    assert not output.exists()


def assessments():
    matrix = {"assessments": []}
    canonical = {"assessments": []}
    for axis, categories in m.rounds.CATEGORIES.items():
        category = next(iter(categories))
        details = {name: "exact authored value" for name in m.rounds.DETAILS[axis]}
        matrix["assessments"].append({"axis": axis, "category": category,
                                      "scope": "original scoped assertion", "evidence_ids": [],
                                      "dimensions": details})
        canonical["assessments"].append({"evidence_ids": [], "dimensions": [
            {"name": k, "value": v} for k, v in
            {"axis": axis, "category": category, "scope": "original scoped assertion", **details}.items()]})
    return matrix, canonical


@pytest.mark.parametrize("field", ["category", "scope", "assertion_scope"])
def test_matrix_to_canonical_meaning_changes_are_preserved_as_failures(field):
    matrix, canonical = assessments()
    authored = copy.deepcopy(canonical)
    target = next(d for d in canonical["assessments"][0]["dimensions"] if d["name"] == field)
    target["value"] = "changed"
    errors = m.assessment_parity(authored, canonical, matrix, {"proofs": []})
    assert "authored_saved_document" in errors
    assert any(e.startswith("matrix_claim_") for e in errors)


def test_missing_proofs_do_not_disappear_when_sidecar_is_unavailable(tmp_path):
    review = {"evidence": [{"evidence_id": "cited-a"}, {"evidence_id": "cited-b"}]}
    rows, pins, unknown = m.proof_inventory(tmp_path, review, None, None, False)
    assert len(rows) == 2 and {r["status"] for r in rows} == {"missing_proof"}
    assert unknown and not pins


def test_unreferenced_and_duplicate_proofs_remain_in_accounting(tmp_path):
    proof = {"evidence_id": "extra", "input": {"path": "missing", "sha256": "none"}}
    rows, _, unknown = m.proof_inventory(tmp_path, {"evidence": []}, None,
                                        {"proofs": [proof, proof]}, False)
    assert len(rows) == 1 and rows[0]["proof_count"] == 2
    assert rows[0]["status"] == "duplicate_proof" and not unknown


def test_duplicate_review_ids_fail_both_entries_without_removing_rows():
    rows = [{"review_id_sha256": "same", "errors": [], "status": "passed",
             "canonical_pair_replayed": True, "proofs": [], "unknown_proof_denominator": False}
            for _ in range(2)]
    result = m.summary(rows, "batch")
    assert len(rows) == 2 and all(r["status"] == "failed" for r in rows)
    assert all("duplicate_review_id" in r["errors"] for r in rows)
    assert not result["technical_integrity_complete"]


def test_duplicate_canonical_paths_are_flagged_for_each_affected_case(tmp_path):
    settings = config(tmp_path)
    for e in settings["entries"][:2]:
        e["review"] = "same/review.yaml"
    found = m.duplicates(settings, settings["entries"])
    assert found == {(e["reviewer"], e["case_id"]) for e in settings["entries"][:2]}


def test_changed_canary_config_cannot_authorize_batch(tmp_path):
    (tmp_path / "receipt.json").write_text(json.dumps({
        "mode": "canary", "helper_sha256": m.sha(Path(m.__file__).read_bytes()),
        "config_sha256": "older-config"}))
    with pytest.raises(ValueError, match="configuration changed"):
        m.check_canary(tmp_path, config(tmp_path))


def test_multiple_quotation_proofs_map_to_one_frozen_source_without_extra_fields():
    manifest = {"files": [{"path": "raw/paper.json", "sha256": "paperhash",
                           "evidence_ids": ["frozen-paper"]}]}
    sidecar = {"proofs": [{"evidence_id": eid,
                           "input": {"path": "raw/paper.json", "sha256": "paperhash"}}
                          for eid in ("strain-snippet", "observation-snippet")]}
    mapped, errors = m.evidence_mapping(["strain-snippet", "observation-snippet"], sidecar,
                                        manifest, ["frozen-paper"])
    assert mapped == {"frozen-paper"} and not errors


@pytest.mark.parametrize("condition,expected", [
    ("multiple", "ambiguous_source_ids"), ("wrong_hash", "unmapped_source_input"),
    ("different_path", "unmapped_source_input"), ("false_explicit", "explicit_source_id_unbound"),
])
def test_evidence_mapping_never_guesses_an_ambiguous_or_unbound_source(condition, expected):
    ids = ["one", "two"] if condition == "multiple" else ["one"]
    manifest = {"files": [{"path": "raw/paper.json", "sha256": "hash", "evidence_ids": ids}]}
    proof = {"evidence_id": "new-quote", "input": {"path": "raw/paper.json", "sha256": "hash"}}
    if condition == "wrong_hash":
        proof["input"]["sha256"] = "changed"
    elif condition == "different_path":
        proof["input"]["path"] = "unfrozen-copy.json"
    elif condition == "false_explicit":
        proof["manifest_evidence_id"] = "unrelated"
    mapped, errors = m.evidence_mapping(["new-quote"], {"proofs": [proof]}, manifest, ids)
    assert not mapped and errors == [expected]


def test_changed_clone_validator_is_rejected_before_any_clone_code_executes(tmp_path, monkeypatch):
    helper = tmp_path / "validator.py"
    helper.write_text("modified executable code")
    manifest = {"files": [{"path": "validator.py", "sha256": m.sha(b"frozen original code")}]}
    raw = m.encoded(manifest)
    (tmp_path / "manifest.json").write_bytes(raw)
    settings = {"reviewers": {"reviewer-a": {"root": str(tmp_path)}},
                "manifest": "manifest.json", "package_sha256": m.sha(raw),
                "runtime_git_revision": "same-git-head"}
    monkeypatch.setattr(m.subprocess, "check_output", lambda *args, **kwargs: b"same-git-head\n")
    executed = []
    monkeypatch.setattr(m, "command", lambda *args: executed.append(args))
    with pytest.raises(ValueError, match="before execution"):
        m.context(settings, "reviewer-a", tmp_path / "out")
    assert not executed


def test_rationale_paraphrase_is_visible_without_inventing_semantic_failure():
    matrix, canonical = assessments()
    for item in matrix["assessments"]:
        item["rationale"] = "original authored reasoning"
    for item in canonical["assessments"]:
        item["summary"] = "a differently worded canonical explanation"
    assert not m.assessment_parity(canonical, canonical, matrix, {"proofs": []})
    diagnostics = m.rationale_diagnostics(canonical, matrix)
    assert len(diagnostics) == 6 and all(d["literal_text_equal"] is False for d in diagnostics)
    assert all(d["semantic_equivalence"] == "not_assessed_by_replay" for d in diagnostics)
    assert all(d["matrix_rationale_sha256"] != d["canonical_summary_sha256"] for d in diagnostics)


def test_input_validation_preserves_missing_pair_and_never_becomes_canonical(tmp_path, monkeypatch):
    matrix_case, authored = assessments()
    matrix_case["case_id"] = "fresh-47"
    authored.update({"review_id": "authored-draft", "reviewer": {"identity": "reviewer-a", "model": "actual"},
                     "evidence": []})
    for name, value in (("input.json", authored), ("proofs.json", {"proofs": []}), ("packet.json", {})):
        (tmp_path / name).write_text(json.dumps(value))
    ctx = {"root": tmp_path, "python": "python", "settings": {"canonical_identity": "reviewer-a"},
           "matrix": {"reviewer": {"model": "actual"}, "cases": [matrix_case]},
           "manifest": {"cases": [{"case_id": "fresh-47", "packet_path": "packet.json"}], "files": []}}
    calls = []
    def successful(root, argv, out):
        calls.append(argv)
        return {"exit_code": 0}, json.dumps({"occurrence_id": "original", "verified_evidence": 0,
                                            "verified_quotes": 0}).encode()
    monkeypatch.setattr(m, "command", successful)
    monkeypatch.setattr(m, "isolated_proofs", lambda *args: ({}, {}))
    result = m.unit({}, {"reviewer": "reviewer-a", "case_id": "fresh-47", "input": "input.json",
                         "proofs": "proofs.json", "review": "missing/review.yaml"},
                    ctx, {"occurrence_id": "original"}, tmp_path / "out", input_mode=True)
    assert len(calls) == 1 and "validate" in calls[0] and "check" not in calls[0]
    assert result["input_validation_passed"]
    assert not result["canonical_pair_replayed"] and result["status"] == "failed"
    assert "missing_or_invalid_review" in result["errors"]
    assert result["adaptation_parity"]["status"] == "unavailable"
    assert result["draft_matrix_adaptation"]["status"] == "passed"
    totals = m.summary([result] * 20, "input-batch")
    assert totals["expected_pairs"] == 20 and totals["authored_inputs_production_validated"] == 20
    assert not totals["canonical_persistence_gate_passed"] and not totals["technical_integrity_complete"]


def test_input_batch_requires_its_own_input_canary(tmp_path):
    output = tmp_path / ".temp" / "batch"
    with pytest.raises(ValueError, match="persisted canary"):
        m.run(config(tmp_path), output, "input-batch")
    assert not output.exists()


def test_input_canary_cannot_unlock_canonical_batch(tmp_path):
    settings = config(tmp_path)
    (tmp_path / "receipt.json").write_text(json.dumps({
        "mode": "input-canary", "helper_sha256": m.sha(Path(m.__file__).read_bytes()),
        "config_sha256": m.sha(m.encoded(settings))}))
    with pytest.raises(ValueError, match="configuration changed"):
        m.check_canary(tmp_path, settings)


def test_failed_proof_does_not_hide_later_proof_replay(tmp_path, monkeypatch):
    sys.path.insert(0, str(ROOT / "src"))
    from edgemech import occurrence_packet, occurrence_review, pins
    (tmp_path / "packet.json").write_text("{}")
    monkeypatch.setattr(pins, "check_contracts", lambda: None)
    monkeypatch.setattr(occurrence_packet, "validate_packet", lambda *args, **kwargs: None)
    calls = []
    def replay(root, review, packet_path, packet, sidecar, inputs):
        eid = sidecar["proofs"][0]["evidence_id"]
        calls.append(eid)
        assert len(review["evidence"]) == len(sidecar["proofs"]) == 1
        if eid == "first-invalid":
            raise ValueError("Original packet proof cannot support claim")
        return {eid: sidecar["proofs"][0]}
    monkeypatch.setattr(occurrence_review, "_replay_evidence", replay)
    review = {"source": {"inputs": []}, "evidence": [{"evidence_id": e} for e in ["first-invalid", "later-valid"]]}
    sidecar = {"proofs": [{"evidence_id": e} for e in ["first-invalid", "later-valid"]]}
    original = copy.deepcopy((review, sidecar))
    rows, receipt = m.isolated_proofs(tmp_path, review, sidecar, "packet.json", tmp_path / "out")
    assert calls == ["first-invalid", "later-valid"]
    assert rows[m.sha(b"first-invalid")]["status"] == "failed"
    assert rows[m.sha(b"later-valid")]["status"] == "passed"
    assert (review, sidecar) == original
    assert json.loads(Path(receipt["path"]).read_text())["passed"] == 1


def test_isolated_replay_retains_missing_and_duplicate_declarations(tmp_path, monkeypatch):
    sys.path.insert(0, str(ROOT / "src"))
    from edgemech import occurrence_packet, occurrence_review, pins
    (tmp_path / "packet.json").write_text("{}")
    monkeypatch.setattr(pins, "check_contracts", lambda: None)
    monkeypatch.setattr(occurrence_packet, "validate_packet", lambda *args, **kwargs: None)
    calls = []
    monkeypatch.setattr(occurrence_review, "_replay_evidence", lambda *args: calls.append(args))
    review = {"source": {"inputs": []}, "evidence": [{"evidence_id": e} for e in ["missing", "duplicate", "duplicate"]]}
    sidecar = {"proofs": [{"evidence_id": e} for e in ["duplicate", "extra"]]}
    rows, receipt = m.isolated_proofs(tmp_path, review, sidecar, "packet.json", tmp_path / "out")
    assert len(rows) == 3 and not calls
    assert all(r["status"] == "failed" for r in rows.values())
    assert rows[m.sha(b"duplicate")]["evidence_entries"] == 2
    assert rows[m.sha(b"missing")]["proof_entries"] == 0
    assert rows[m.sha(b"extra")]["evidence_entries"] == 0
    assert json.loads(Path(receipt["path"]).read_text())["passed"] == 0


def test_canary_inventory_keeps_nested_receipts(tmp_path):
    settings = {"test": "configuration"}
    nested = tmp_path / "isolated-proofs" / "receipt.json"
    nested.parent.mkdir()
    nested.write_text('{"expected":1,"passed":1}\n')
    stdout = tmp_path / "stdout.log"
    stdout.write_text('{"occurrence_id":"original"}\n')
    receipt = {"mode": "input-canary", "helper_sha256": m.sha(Path(m.__file__).read_bytes()),
               "config_sha256": m.sha(m.encoded(settings)), "contexts": {},
               "artifact_pins": [{"path": str(p), "sha256": m.sha(p.read_bytes())} for p in (nested, stdout)],
               "rows": [{"case_id": "fresh-47", "occurrence_id": "original", "input_pins": [],
                         "input_validation_passed": True, "unknown_proof_denominator": False,
                         "proofs": [{"status": "passed_isolated_proof"}],
                         "input_validation_command": {"exit_code": 0, "stdout": {"path": str(stdout)}}}]}
    (tmp_path / "receipt.json").write_bytes(m.encoded(receipt))
    assert m.check_canary(tmp_path, settings, input_mode=True) == receipt
    nested.write_text('{"changed":true}\n')
    with pytest.raises(ValueError, match="artifact changed"):
        m.check_canary(tmp_path, settings, input_mode=True)
