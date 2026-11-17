"""Finalization preserves all gates, actual replay denominators and initial seals."""
from __future__ import annotations

import importlib.util
import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest
from test_calibration_adjudication_gates import setup_audit
from test_calibration_round import round_inputs as round_inputs_fixture

round_inputs = round_inputs_fixture
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts/adhoc"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("finalizer", SCRIPTS / "finalize_m5_calibration_20261116.py")
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


def replay_fixture(cases=None, axes=None):
    cases = cases or [f"case-{n}" for n in range(10)]
    axes = axes or {"claim", "literature"}
    expected = {(rid, cid) for rid in ("reviewer-a", "reviewer-b") for cid in cases}
    required = {(cid, "paper"): axes for cid in cases}
    pair_rows = [{"reviewer": rid, "case_id": cid, "status": "passed", "errors": [],
                  "review_id_sha256": rid + cid, "canonical_pair_replayed": True,
                  "authored_saved_document_equal": True, "adaptation_parity": {"status": "passed"},
                  "canonical_command": {"exit_code": 0}, "unknown_proof_denominator": False,
                  "verified_evidence": 1,
                  "proofs": [{"evidence_id_sha256": "proof", "status": "passed", "proof_count": 1}]}
                 for rid, cid in sorted(expected)]
    common = {"mode": "batch", "round_id": "test-round", "package_sha256": "package"}
    pairs = {**common, "rows": pair_rows, "context_errors": {},
             "contexts": {rid: {"status": "passed"} for rid in ("reviewer-a", "reviewer-b")},
             "summary": {"passed": True, "total": 20}}
    citations = {**common, "expected_total_final_citations": len(required),
                 "rows": [{"case_id": cid, "evidence_id": eid, "status": "passed",
                           "final_axes": sorted(axis_set), "kind": "jats", "scope": "exact",
                           "support": "supports", "proof_axes": sorted(axis_set)}
                           for (cid, eid), axis_set in required.items()]}
    return pairs, citations, expected, required


def integrity(data, exact=None):
    pairs, citations, expected, required = data
    return helper.technical_gate(pairs, citations, expected, required,
                                 package_sha256="package", round_id="test-round",
                                 exact_paper_cases=exact or {})


def test_all_twenty_actual_pairs_and_all_final_citations_count():
    result = integrity(replay_fixture(), {"case-0": {"supports"}})
    assert result["passed"]
    assert result["canonical_pairs"] == {
        "expected": 20, "retained": 20, "verified": 20, "complete_slot_inventory": True}
    assert result["initial_proofs"]["known_expected"] == 20
    assert result["final_citations"]["expected"] == 10


@pytest.mark.parametrize("damage", [
    lambda p, c: p["rows"].pop(),
    lambda p, c: p["rows"].append(deepcopy(p["rows"][0])),
    lambda p, c: p["rows"][0].update(unknown_proof_denominator=True),
    lambda p, c: p["rows"][0].update(authored_saved_document_equal=False),
    lambda p, c: p["rows"][0].update(proofs=[]),
    lambda p, c: p["rows"][0]["proofs"][0].update(proof_count=2),
    lambda p, c: p["rows"][0].update(review_id_sha256=p["rows"][1]["review_id_sha256"]),
    lambda p, c: p["rows"][0]["canonical_command"].update(exit_code=1),
    lambda p, c: p["contexts"]["reviewer-a"].update(status="failed"),
    lambda p, c: c["rows"].pop(),
    lambda p, c: c["rows"][0].update(final_axes=["claim"]),
    lambda p, c: c["rows"][0].update(kind="authority"),
    lambda p, c: c["rows"][0].update(kind="packet"),
    lambda p, c: c["rows"][0].update(status="failed"),
    lambda p, c: c.update(round_id="old-round"),
])
def test_forged_pass_summary_cannot_hide_missing_failed_or_nonpaper_rows(damage):
    data = replay_fixture()
    damage(data[0], data[1])
    assert not integrity(data)["passed"]


@pytest.mark.parametrize("field,value", [("scope", "partial"), ("scope", "context"),
                                         ("support", "refutes"), ("support", "context_only")])
def test_exact_paper_exercise_requires_actual_exact_directional_proof(field, value):
    data = replay_fixture()
    data[1]["rows"][0][field] = value
    assert not integrity(data, {"case-0": {"supports"}})["passed"]


def test_conflicting_exact_paper_exercise_requires_both_directions():
    data = replay_fixture()
    assert not integrity(data, {"case-0": {"supports", "refutes"}})["passed"]
    data[1]["rows"].append({**data[1]["rows"][0], "evidence_id": "paper2", "support": "refutes"})
    data[1]["expected_total_final_citations"] += 1
    data[3]["case-0", "paper2"] = {"claim", "literature"}
    assert integrity(data, {"case-0": {"supports", "refutes"}})["passed"]


@pytest.mark.parametrize("scope,support,axis,passed", [
    ("exact", "refutes", "object_node", True), ("context", "refutes", "object_node", False),
    ("exact", "supports", "object_node", False), ("exact", "refutes", "relation", False),
])
def test_exact_authority_exercise_requires_refuting_correct_axis(scope, support, axis, passed):
    data = replay_fixture()
    data[1]["rows"].append({"case_id": "case-0", "evidence_id": "authority", "kind": "authority",
                           "status": "passed", "scope": scope, "support": support,
                           "final_axes": [axis], "proof_axes": [axis]})
    data[1]["expected_total_final_citations"] += 1
    data[3]["case-0", "authority"] = {axis}
    result = helper.technical_gate(*data, package_sha256="package", round_id="test-round",
                                   exact_authority_cases={"case-0": {"object_node"}})
    assert result["passed"] is passed


def supplement(documents):
    entries = []
    for rid, cases in ((documents["reviewer_a"]["reviewer"]["id"], documents["reviewer_a"]["cases"]),
                       (documents["reviewer_b"]["reviewer"]["id"], documents["reviewer_b"]["cases"]),
                       ("adjudicated", documents["audit"]["final_cases"])):
        for case in cases:
            for item in case["assessments"]:
                if item["axis"] in {"literature", "source_fidelity"} and item["category"] in {
                        "SUPPORTS", "REFUTES", "CONFLICTING", "SUPPORTED", "CONTRADICTED"}:
                    entries.append({"reviewer_id": rid, "case_id": case["case_id"], "axis": item["axis"],
                                    "category": item["category"], "status": "supported",
                                    "rationale": "Synthetic independent audit", "evidence_ids": ["paper"]})
    documents["audit"]["supplemental_semantic_audit"] = entries
    return entries


def setup_documents(data, monkeypatch, *, resolved=True):
    _, root, *_ = data
    _, audit, evaluate, _ = setup_audit(data, monkeypatch, resolved=resolved)
    audit["evidence_integrity"]["status"] = "passed"
    documents = {"audit": audit, **{key: json.loads((root / path).read_bytes()) for key, path in
                 (("reviewer_a", "a.json"), ("reviewer_b", "b.json"), ("manifest", "manifest.json"))}}
    supplement(documents)
    return documents, evaluate


@pytest.mark.parametrize("resolved", [False, True])
def test_real_accounting_gates_survive_finalization_unchanged(round_inputs, monkeypatch, resolved):
    documents, evaluate = setup_documents(round_inputs, monkeypatch, resolved=resolved)
    evaluated = evaluate()
    result = helper.finalize_accounting(evaluated, integrity(replay_fixture()),
                                        {"reviewer-a": {}, "reviewer-b": {}}, helper.supplemental_audit(documents))
    assert result["remaining_90_authorized_by_result"] is resolved
    assert not result["expansion_authorized"]
    assert result["initial_gates"] == evaluated["initial_gates"]
    assert {k: v for k, v in result["final_gates"].items() if k != "evidence_replay"} == {
        k: v for k, v in evaluated["final_gates"].items() if k != "evidence_replay"}
    assert result["initial_critical_label_classes"] == evaluated["initial_critical_label_classes"]


@pytest.mark.parametrize("field", ["critical_label_audit", "supplemental_semantic_audit"])
def test_any_unsupported_resolved_label_blocks_despite_perfect_replay(round_inputs, monkeypatch, field):
    documents, evaluate = setup_documents(round_inputs, monkeypatch)
    documents["audit"][field][0]["status"] = "unsupported"
    result = helper.finalize_accounting(evaluate(), integrity(replay_fixture()),
                                        {"reviewer-a": {}, "reviewer-b": {}}, helper.supplemental_audit(documents))
    assert not result["remaining_90_authorized_by_result"]


@pytest.mark.parametrize("damage", [
    lambda entries: entries.pop(),
    lambda entries: entries.append(deepcopy(entries[0])),
    lambda entries: entries[0].update(evidence_ids=["unbound"]),
    lambda entries: entries[0].update(category="UNAVAILABLE"),
])
def test_supplemental_resolved_audit_must_be_complete_and_bound(round_inputs, monkeypatch, damage):
    documents, _ = setup_documents(round_inputs, monkeypatch)
    damage(documents["audit"]["supplemental_semantic_audit"])
    with pytest.raises(ValueError):
        helper.supplemental_audit(documents)


def test_transport_save_time_is_distinct_from_complete_original_seal(tmp_path, monkeypatch):
    root = tmp_path.resolve()
    monkeypatch.setattr(helper, "ROOT", root)
    config, documents = {"initial_seals": {}}, {"reviewer_config": {"manifest": "manifest.json", "reviewers": {}}}
    monkeypatch.setattr(helper.initial, "check", lambda *args: {
        "status": "passed", "cases": 10, "authored_axes": 60})
    for rid, key in (("reviewer-a", "reviewer_a"), ("reviewer-b", "reviewer_b")):
        clone = root / rid
        clone.mkdir()
        matrix = json.dumps({"reviewer": {"id": rid}}).encode()
        receipt = {"matrix_sha256": helper.rounds.digest(matrix), "package_sha256": "package",
                   "reviewer": {"id": rid}, "saved_at": "original-time"}
        (clone / "matrix.json").write_bytes(matrix)
        (clone / "matrix.json.receipt.json").write_text(json.dumps(receipt))
        (root / (rid + ".json")).write_bytes(matrix)
        (root / (rid + ".json.receipt.json")).write_text(json.dumps({**receipt, "saved_at": "transport-time"}))
        seal = json.dumps({"manifest": "manifest.json", "matrix": {"path": "matrix.json"}, "canonical_identity": rid}).encode()
        (clone / "seal.json").write_bytes(seal)
        config["initial_seals"][rid] = {"root": str(clone), "seal": {"path": "seal.json", "sha256": helper.rounds.digest(seal)}}
        config[key] = {"path": rid + ".json"}
        documents["reviewer_config"]["reviewers"][rid] = {"root": str(clone), "matrix": "matrix.json", "canonical_identity": rid}
    checked = helper.original_seals(config, documents)
    assert checked["reviewer-a"]["original_saved_at"] == "original-time"
    assert checked["reviewer-a"]["transport_saved_at"] == "transport-time"
    (root / "reviewer-a.json").write_bytes((root / "reviewer-a.json").read_bytes() + b" ")
    with pytest.raises(ValueError, match="Transport matrix differs"):
        helper.original_seals(config, documents)


def test_pin_failure_preserves_full_unattempted_denominator_and_exclusive_output(tmp_path, monkeypatch):
    root = tmp_path.resolve()
    monkeypatch.setattr(helper, "ROOT", root)
    _, cohort = helper.rounds.baseline(Path(__file__).resolve().parents[1])
    monkeypatch.setattr(helper.rounds, "baseline", lambda _: ({}, cohort))
    (root / "manifest.json").write_text("{}")
    (root / "config.json").write_text(json.dumps({"manifest": {"path": "manifest.json", "sha256": "wrong"}}))
    result = helper.run("config.json", ".temp/result")
    assert result["status"] == "failed_prerequisite_or_replay"
    assert len(result["canonical_pairs"]["slots"]) == 20
    assert all(row["status"] == "unattempted" and row["unknown_proof_denominator"]
               for row in result["canonical_pairs"]["slots"])
    assert (root / ".temp/result/failure.json").exists()
    with pytest.raises(ValueError, match="already exists"):
        helper.run("config.json", ".temp/result")


def test_later_failure_retains_completed_pair_slots(tmp_path):
    pairs, _, expected, _ = replay_fixture()
    output = tmp_path.resolve()
    (output / "canonical-pairs").mkdir()
    (output / "canonical-pairs/receipt.json").write_text(json.dumps(pairs))
    result = helper.failure_slots(output, expected)
    assert result["expected"] == result["retained_rows"] == 20
    assert all(row["status"] == "passed" for row in result["slots"])


def test_real_freeze_round_helper_role_is_accepted_and_dependency_drift_fails(round_inputs, monkeypatch):
    rounds, root, _, cohort, freeze_config, put = round_inputs
    monkeypatch.setattr(helper, "ROOT", root)
    monkeypatch.setattr(helper, "rounds", rounds)
    for module in (helper, helper.accounting, rounds, helper.citations, helper.pairs, helper.initial):
        source = Path(module.__file__)
        relative = "scripts/adhoc/" + source.name
        target = root / relative
        target.write_bytes(source.read_bytes())
        monkeypatch.setattr(module, "__file__", str(target))
        if module is not rounds:
            freeze_config["files"].append({"path": relative, "role": "proof_adapter"})
    put("runtime-config.json", freeze_config)
    rounds.freeze(root, "runtime-config.json", "runtime-manifest.json")
    package = rounds.digest((root / "runtime-manifest.json").read_bytes())
    base = {"round_id": "test-round", "manifest": "runtime-manifest.json", "package_sha256": package,
            "reviewers": {rid: {"root": str(root / rid), "canonical_identity": rid}
                          for rid in ("reviewer-a", "reviewer-b")},
            "entries": [{"reviewer": rid, "case_id": case["case_id"], "input": None, "proofs": None,
                         "review": None} for rid in ("reviewer-a", "reviewer-b") for case in cohort["cases"]]}
    put("replay.json", base)
    put("audit-minimal.json", {})
    config = {key: {"path": path, "sha256": rounds.digest((root / path).read_bytes())}
              for key, path in (("manifest", "runtime-manifest.json"), ("reviewer_config", "replay.json"),
                                ("audit", "audit-minimal.json"))}
    cited = {key: {"path": str(root / config[pin]["path"]), "sha256": config[pin]["sha256"]}
             for key, pin in (("reviewer_config", "reviewer_config"), ("final_audit", "audit"))}
    documents = {"reviewer_config": base, "citation_config": cited,
                 "manifest": json.loads((root / "runtime-manifest.json").read_bytes())}
    assert len(helper.verify_config_bindings(config, documents)) == 20
    Path(helper.initial.__file__).write_bytes(Path(helper.initial.__file__).read_bytes() + b"\nchanged")
    with pytest.raises(ValueError, match="not the frozen runtime"):
        helper.verify_config_bindings(config, documents)


@pytest.mark.parametrize("damage", ["root", "input", "proofs", "proof_identity", "none"])
def test_new_anchor_binds_the_same_final_draft_and_proof_set(tmp_path, monkeypatch, damage):
    root = tmp_path.resolve()
    monkeypatch.setattr(helper, "ROOT", root)
    (root / "sidecar.json").write_text("{}")
    row = {"case_id": "case", "evidence_id": "evidence", "final_root": str(root),
           "final_input": {"path": str(root / "final.json"), "sha256": "final-hash"},
           "final_sidecar": {"path": str(root / "sidecar.json"), "sha256": "proofs-hash"},
           "final_proof_id": "proof"}
    if damage == "root":
        row["final_root"] = str(root / "different")
    elif damage in {"input", "proofs"}:
        row["final_input" if damage == "input" else "final_sidecar"]["path"] += ".alternative"
    mapped = ["other"] if damage == "proof_identity" else ["evidence"]
    monkeypatch.setattr(helper.initial, "mapped_ids", lambda *args: mapped)
    raw = json.dumps({"rows": [row]}).encode()
    (root / "report.json").write_bytes(raw)
    documents = {"citation_config": {"citation_report": {"path": str(root / "report.json"),
                   "sha256": helper.rounds.digest(raw)}},
                 "final_authored": {"cases": [{"case_id": "case", "review": "final.json", "proofs": "sidecar.json"}]},
                 "manifest": {"cases": [{"case_id": "case", "evidence_ids": ["evidence"]}]}}
    validated = {"inputs": [{"path": "final.json", "sha256": "final-hash"},
                             {"path": "sidecar.json", "sha256": "proofs-hash"}]}
    if damage == "none":
        helper.bind_final_citation_drafts(documents, validated)
    else:
        with pytest.raises(ValueError):
            helper.bind_final_citation_drafts(documents, validated)


@pytest.mark.parametrize("damage", ["identity", "category", "evidence", "report", "none"])
def test_final_profile_projection_cannot_differ_from_adjudicated_audit(round_inputs, monkeypatch, damage):
    documents, _ = setup_documents(round_inputs, monkeypatch)
    audit = documents["audit"]
    actual = {"reviewer": deepcopy(audit["adjudicator"]), "cases": deepcopy(audit["final_cases"])}
    if damage == "identity":
        actual["reviewer"]["session_id"] = "other-session"
    elif damage == "category":
        actual["cases"][0]["assessments"][0]["category"] = "INSUFFICIENT_EVIDENCE"
    elif damage == "evidence":
        actual["cases"][0]["assessments"][0]["evidence_ids"] = ["authority"]
    elif damage == "report":
        actual["cases"][0]["assessments"][0]["report_witnesses"] = {"scope": "invented"}
    invoked = []

    def validate(root, manifest, final_config):
        invoked.append((manifest, final_config))
        return {"matrix": actual, "inputs": [], "validations": []}

    monkeypatch.setattr(helper.initial, "validate", validate)
    config = {"manifest": {"path": "manifest.json"}, "final_authored": {"path": "final-drafts.json"}}
    if damage == "none":
        result = helper.final_authored(config, documents)
        assert result["authored_axes"] == 60 and not result["initial_seals_augmented"]
    else:
        with pytest.raises(ValueError):
            helper.final_authored(config, documents)
    assert invoked == [("manifest.json", "final-drafts.json")]


def test_actual_orchestration_recomputes_and_calls_both_batches(round_inputs, monkeypatch):
    rounds, root, _, cohort, _, put = round_inputs
    documents, evaluate = setup_documents(round_inputs, monkeypatch)
    object_axis = next(a for a in documents["audit"]["final_cases"][0]["assessments"] if a["axis"] == "object_node")
    object_axis["evidence_ids"].append("authority")
    evaluated = evaluate()
    monkeypatch.setattr(helper, "ROOT", root)
    monkeypatch.setattr(helper, "rounds", rounds)
    calls = []
    cases = [c["case_id"] for c in cohort["cases"]]
    pair_receipt, citation_receipt, expected, _ = replay_fixture(cases, set(rounds.CATEGORIES))
    cid = documents["audit"]["final_cases"][0]["case_id"]
    citation_receipt["rows"].append({"case_id": cid, "evidence_id": "authority", "status": "passed",
                                     "kind": "authority", "scope": "exact", "support": "refutes",
                                     "proof_axes": ["object_node"], "final_axes": ["object_node"]})
    citation_receipt["expected_total_final_citations"] += 1
    package = rounds.digest((root / "manifest.json").read_bytes())
    pair_receipt["package_sha256"] = citation_receipt["package_sha256"] = package
    documents.update(accounting=evaluated, reviewer_config={}, citation_config={}, final_authored={},
                     comparison=json.loads((root / "comparison.json").read_bytes()))
    config = {}
    for key, value in documents.items():
        path = key + "-input.json"
        put(path, value)
        config[key] = {"path": path, "sha256": rounds.digest((root / path).read_bytes())}
    # Preserve original frozen manifest hash for the execution boundary fixture.
    config["manifest"] = {"path": "manifest.json", "sha256": package}
    for name in ("pair-canary", "citation-canary"):
        put(name + "/receipt.json", {"status": "passed"})
    config["pair_canary"] = {"directory": str(root / "pair-canary"),
                             "receipt_sha256": rounds.digest((root / "pair-canary/receipt.json").read_bytes())}
    config["citation_canaries"] = [{"directory": str(root / "citation-canary"),
                                    "receipt_sha256": rounds.digest((root / "citation-canary/receipt.json").read_bytes())}]
    put("final-config.json", config)
    monkeypatch.setattr(helper, "verify_config_bindings", lambda *_: expected)
    monkeypatch.setattr(helper, "original_seals", lambda *_: {"reviewer-a": {}, "reviewer-b": {}})
    monkeypatch.setattr(helper, "final_authored", lambda *_: {"status": "passed", "inputs": []})
    monkeypatch.setattr(helper, "bind_final_citation_drafts", lambda *_: None)

    def reevaluate(*args):
        calls.append("reevaluate")
        return evaluated

    monkeypatch.setattr(helper.accounting, "evaluate", reevaluate)

    def batch(name, receipt):
        def invoke(config, output, mode, **kwargs):
            assert mode == "batch" and kwargs
            calls.append(name)
            output.mkdir()
            helper.pairs.write(output / "receipt.json", receipt)
            return receipt
        return invoke

    monkeypatch.setattr(helper.pairs, "run", batch("canonical", pair_receipt))
    monkeypatch.setattr(helper.citations, "run", batch("citations", citation_receipt))
    result = helper.run("final-config.json", ".temp/finalized")
    assert calls == ["reevaluate", "canonical", "citations"]
    assert result["remaining_90_authorized_by_result"] and not result["expansion_authorized"]
    assert result["final_gates"]["evidence_replay"]["actual_replay"]["canonical_pairs"]["verified"] == 20
