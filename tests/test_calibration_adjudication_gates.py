"""Every emitted resolved judgment is audited, including agreements and final labels."""

from __future__ import annotations

import importlib.util
import json
from copy import deepcopy
from pathlib import Path

import pytest
from test_calibration_round import round_inputs as round_inputs_fixture
from test_calibration_round import seal_pair

round_inputs = round_inputs_fixture

HELPER = Path(__file__).resolve().parents[1] / "scripts/adhoc/calibration_adjudication_gates_20261116.py"


def setup_audit(data, monkeypatch, *, resolved=False, mutate=None):
    rounds, root, _, _, _, put = data
    spec = importlib.util.spec_from_file_location("adjudication_gates", HELPER)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    monkeypatch.setattr(m, "rounds", rounds)
    comparison = seal_pair(data, mutate, resolved)
    put("comparison.json", comparison)
    a = json.loads((root / "a.json").read_text())
    b = json.loads((root / "b.json").read_text())
    final = deepcopy(a["cases"])

    def critical(matrix, rid):
        return [{"reviewer_id": rid, "case_id": case["case_id"],
                 "axis": item["axis"], "category": item["category"],
                 "status": "supported", "rationale": "synthetic evidence audit",
                 "evidence_ids": ["paper"]}
                for case in matrix for item in case["assessments"]
                if m.critical_class(item["axis"], item["category"])]
    audit = {
        "round_id": "test-round", "package_sha256": comparison["package_sha256"],
        "adjudicator": {"id": "separate-adjudicator", "model": "fixture-model",
                        "session_id": "session-adjudicator"},
        "final_cases": final,
        "critical_label_audit": critical(a["cases"], "a") + critical(b["cases"], "b"),
        "final_critical_label_audit": critical(final, "adjudicated"),
        "evidence_integrity": {"status": "unavailable", "rationale": "no canonical receipts in fixture",
                               "receipt_paths": []},
        "nontrivial": {"exact_paper_claim_cases": [final[0]["case_id"]] if resolved else [],
                       "exact_authority_incorrect_cases": [final[0]["case_id"]] if resolved else [],
                       "rationale": "synthetic declared exercise, not independently replayed evidence"},
        "disagreement_dispositions": [{"case_id": d["case_id"], "axis": d["axis"],
                                       "status": "resolved", "rationale": "synthetic disposition"}
                                      for d in comparison["disagreements"]],
    }
    put("audit.json", audit)

    def evaluate():
        put("audit.json", audit)
        return m.evaluate(root, "manifest.json", "a.json", "b.json", "comparison.json", "audit.json")
    return m, audit, evaluate, put


def test_unresolved_agreement_cannot_meet_resolution_floor(round_inputs, monkeypatch):
    _, audit, evaluate, _ = setup_audit(round_inputs, monkeypatch)
    # A supplied alternate threshold must never change the preregistered protocol.
    audit["thresholds"] = {"resolved_claims": {"minimum": 0},
                           "resolved_modeling_per_axis": {"minimum": 0}}
    result = evaluate()
    assert result["initial_gates"]["initial_exact_category_agreement"]["numerator"] == 60
    assert result["final_gates"]["final_authored_axes"]["numerator"] == 60
    assert result["final_gates"]["resolved_claims"] == {
        "numerator": 0, "denominator": 10, "minimum": 2, "passed": False}
    assert all(g["numerator"] == 0 and g["minimum"] == 5 and not g["passed"]
               for g in result["final_gates"]["resolved_modeling_per_axis"].values())
    assert result["final_gates"]["resolved_source_fidelity"]["minimum"] == 8
    assert result["literature"]["experimental_denominator"] == 7
    assert all(c["status"] == "untested_label_class" for c in result["initial_critical_label_classes"].values())
    assert result["status"] == "failed_gate"
    assert result["scientific_calibration_passed"] is False


def test_report_scope_cannot_satisfy_independent_paper_directional_gate(round_inputs, monkeypatch):
    _, audit, evaluate, _ = setup_audit(round_inputs, monkeypatch, resolved=True)
    claim = next(a for a in audit["final_cases"][0]["assessments"] if a["axis"] == "claim")
    claim["assertion_basis"] = "source_report"
    claim["report_witnesses"] = {
        "scope": claim["dimensions"]["assertion_scope"],
        "source_instance_evidence_ids": ["paper"],
        "identity_evidence_ids": ["paper"], "definition_evidence_ids": ["paper"],
    }
    with pytest.raises(ValueError, match="Invalid nontrivial exercise cases"):
        evaluate()
    audit["nontrivial"]["exact_paper_claim_cases"] = []
    result = evaluate()
    assert not result["final_gates"]["exact_paper_backed_directional_claims"]["passed"]
    assert result["literature"]["experimental_denominator"] == 7
    assert result["final_gates"]["resolved_source_fidelity"]["minimum"] == 8


@pytest.mark.parametrize("field", ["critical_label_audit", "final_critical_label_audit"])
def test_omitted_critical_audit_rejected_even_when_reviewers_agree(round_inputs, monkeypatch, field):
    _, audit, evaluate, _ = setup_audit(round_inputs, monkeypatch, resolved=True)
    audit[field].pop()
    with pytest.raises(ValueError, match="Every emitted resolved"):
        evaluate()


@pytest.mark.parametrize("field", ["critical_label_audit", "final_critical_label_audit"])
def test_unsupported_initial_or_final_label_is_critical(round_inputs, monkeypatch, field):
    _, audit, evaluate, _ = setup_audit(round_inputs, monkeypatch, resolved=True)
    audit[field][0].update(status="unsupported", evidence_ids=[], rationale="evidence does not entail claim")
    result = evaluate()
    gate = result["final_gates"]["critical_overclaims"]
    assert gate["initial_unsupported_labels"] + gate["final_unsupported_labels"] == 1
    assert gate["maximum"] == 0 and gate["passed"] is False
    assert result["initial_critical_label_classes"]["unsupported SUPPORTED_AS_STATED"]["emitted_labels"] == 20
    assert result["final_critical_label_classes"]["unsupported SUPPORTED_AS_STATED"]["emitted_labels"] == 10
    assert result["scientific_calibration_passed"] is False


def test_integrity_attestation_without_canonical_replay_never_passes(round_inputs, monkeypatch):
    _, audit, evaluate, put = setup_audit(round_inputs, monkeypatch, resolved=True)
    audit["evidence_integrity"]["status"] = "passed"
    result = evaluate()
    assert result["status"] == "pending_independent_evidence_integrity"
    assert result["final_gates"]["evidence_replay"]["passed"] is False
    put("arbitrary-receipt.json", {"status": "passed"})
    audit["evidence_integrity"]["receipt_paths"] = ["arbitrary-receipt.json"]
    result = evaluate()
    assert result["final_gates"]["evidence_replay"]["receipts"]
    assert result["scientific_calibration_passed"] is False


def test_unresolved_disagreement_over_resolved_model_blocks(round_inputs, monkeypatch):
    def mutate(matrix):
        relation = next(a for a in matrix["cases"][0]["assessments"] if a["axis"] == "relation")
        relation["category"] = "INCORRECT"
    _, audit, evaluate, _ = setup_audit(round_inputs, monkeypatch, resolved=True, mutate=mutate)
    audit["disagreement_dispositions"][0]["status"] = "unresolved"
    result = evaluate()
    assert len(result["disagreements"]) == 1
    assert result["disagreements"][0]["reviewer_a"] == "CORRECT"
    assert result["disagreements"][0]["reviewer_b"] == "INCORRECT"
    assert result["final_gates"]["disagreement_disposition"] == {
        "blocking_unresolved_disagreements": 1, "passed": False}
    audit["disagreement_dispositions"] = []
    with pytest.raises(ValueError, match="Every initial disagreement"):
        evaluate()


def test_altered_initial_comparison_rejected(round_inputs, monkeypatch):
    _, _, evaluate, put = setup_audit(round_inputs, monkeypatch)
    put("comparison.json", {"status": "passed"})
    with pytest.raises(ValueError, match="Initial comparison differs"):
        evaluate()


@pytest.mark.parametrize("axis", ["claim", "literature", "relation", "subject_node",
                                  "object_node", "source_fidelity"])
@pytest.mark.parametrize("defect", ["missing_scope", "empty_scope", "missing_dimensions",
                                    "missing_detail", "empty_detail"])
def test_final_assessment_requires_scope_and_every_axis_detail(round_inputs, monkeypatch, axis, defect):
    m, audit, evaluate, _ = setup_audit(round_inputs, monkeypatch)
    item = next(a for a in audit["final_cases"][0]["assessments"] if a["axis"] == axis)
    if defect == "missing_scope":
        item.pop("scope")
    elif defect == "empty_scope":
        item["scope"] = "  "
    elif defect == "missing_dimensions":
        item.pop("dimensions")
    else:
        detail = sorted(m.rounds.DETAILS[axis])[0]
        if defect == "missing_detail":
            item["dimensions"].pop(detail)
        else:
            item["dimensions"][detail] = "  "
    with pytest.raises(ValueError, match="Missing final"):
        evaluate()


@pytest.mark.parametrize("change", [
    lambda a: a["final_cases"].pop(),
    lambda a: a["final_cases"][0]["assessments"].pop(),
    lambda a: a["final_cases"][0]["assessments"][0].update(category="UNASSESSED"),
    lambda a: a["adjudicator"].update(session_id="session-a"),
    lambda a: a["critical_label_audit"].append(deepcopy(a["critical_label_audit"][0])),
    lambda a: a["critical_label_audit"][0].update(category="CONTRADICTED_AS_STATED"),
    lambda a: a["final_critical_label_audit"][0].update(reviewer_id="a"),
    lambda a: a["final_critical_label_audit"][0].update(evidence_ids=["unbound"]),
])
def test_incomplete_or_relabelled_audit_rejected(round_inputs, monkeypatch, change):
    _, audit, evaluate, _ = setup_audit(round_inputs, monkeypatch, resolved=True)
    change(audit)
    with pytest.raises(ValueError):
        evaluate()
