#!/usr/bin/env python3
"""Finalize unchanged M5 calibration gates after actual complete replay (2026-11-16).

Issues #180/#181/#183/#192. Inputs: hash-pinned manifest, original matrix mirrors,
comparison, independent audit/accounting, reviewer/citation configs, original
initial seals and inspected canary receipts. Recomputes accounting, checks both
original seals, then invokes maintained twenty-pair and final-citation batches.
Outputs: exclusive private replay/final receipts, including failures. No labels,
threshold changes, new evidence, publication or graph admission are generated.

Config keys: manifest, reviewer_a, reviewer_b, comparison, audit, accounting,
reviewer_config, citation_config, final_authored are {path,sha256} relative to
this repository. final_authored is the separate adjudication-stage ten-case
draft/proof config using the initial validator's reviewer/canonical_identity/cases
shape; validation does not add saves or augment the original initial seals.
initial_seals maps reviewer-a/b to {root,seal:{path,sha256}}. pair_canary is
{directory,receipt_sha256}; citation_canaries is a list with that same shape.
The caller must inspect these canaries before invoking this coordinator helper.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import calibration_adjudication_gates_20261116 as accounting
import calibration_round_20261116 as rounds
import replay_m5_round02_final_citations_20261116 as citations
import replay_m5_round02_pairs_20261116 as pairs
import seal_m5_round03_initial_20261116 as initial

ROOT = Path(__file__).absolute().parents[2]
SCHEMA = "edgemech-calibration-finalization/v1"
PIN_KEYS = ("manifest", "reviewer_a", "reviewer_b", "comparison", "audit", "accounting",
            "reviewer_config", "citation_config", "final_authored")


def read_pin(root, pin):
    rounds.require(set(pin) == {"path", "sha256"}, "Expected exact path/hash input pin")
    raw = rounds.safe(root, pin["path"]).read_bytes()
    rounds.require(rounds.digest(raw) == pin["sha256"], "Finalization input changed: " + pin["path"])
    return json.loads(raw, object_pairs_hook=rounds.unique_object)


def canary_directory(pin):
    directory = Path(pin["directory"]).absolute()
    rounds.require(directory.resolve() == directory and directory.is_dir(), "Invalid canary directory")
    receipt = directory / "receipt.json"
    rounds.require(not receipt.is_symlink() and rounds.digest(receipt.read_bytes())
                   == pin["receipt_sha256"], "Inspected canary receipt changed")
    return directory


def gate_leaves(value):
    rounds.require(isinstance(value, dict) and value, "Missing unchanged gates")
    if "passed" in value:
        rounds.require(isinstance(value["passed"], bool), "Gate status must be boolean")
        return [value["passed"]]
    result = []
    for nested in value.values():
        result.extend(gate_leaves(nested))
    return result


def expected_citations(audit, manifest):
    """Derive every distinct final witness and its exact axis applicability."""
    cases = {case["case_id"]: case for case in manifest["cases"]}
    expected, seen = {}, set()
    for case in audit["final_cases"]:
        cid = case["case_id"]
        rounds.require(cid in cases and cid not in seen, "Final cases missing/repeated")
        seen.add(cid)
        axes = [a["axis"] for a in case["assessments"]]
        rounds.require(len(axes) == 6 and set(axes) == set(rounds.CATEGORIES), "Final axes incomplete")
        for assessment in case["assessments"]:
            ids = assessment["evidence_ids"]
            rounds.require(len(ids) == len(set(ids)) and set(ids) <= set(cases[cid]["evidence_ids"]),
                           "Final evidence identity missing/repeated/unbound")
            for eid in ids:
                expected.setdefault((cid, eid), set()).add(assessment["axis"])
    rounds.require(seen == cases.keys() and len(seen) == 10, "All ten final cases required")
    return expected


def supplemental_audit(documents):
    """Audit additional resolved axes without changing preregistered classes."""
    targets = {"source_fidelity": {"SUPPORTED", "CONTRADICTED"},
               "literature": {"SUPPORTS", "REFUTES", "CONFLICTING"}}
    audit, expected = documents["audit"], {}
    for rid, cases in ((documents["reviewer_a"]["reviewer"]["id"], documents["reviewer_a"]["cases"]),
                       (documents["reviewer_b"]["reviewer"]["id"], documents["reviewer_b"]["cases"]),
                       ("adjudicated", audit["final_cases"])):
        for case in cases:
            for item in case["assessments"]:
                if item["category"] in targets.get(item["axis"], set()):
                    expected[rid, case["case_id"], item["axis"]] = item["category"]
    allowed = {case["case_id"]: case["evidence_ids"] for case in documents["manifest"]["cases"]}
    entries, seen = audit["supplemental_semantic_audit"], set()
    for entry in entries:
        key = entry["reviewer_id"], entry["case_id"], entry["axis"]
        rounds.require(key in expected and key not in seen, "Unexpected/repeated supplemental audit")
        rounds.require(entry["category"] == expected[key], "Supplemental audit changed an authored label")
        rounds.require(entry["status"] in {"supported", "unsupported"}, "Invalid supplemental audit status")
        rounds.text(entry.get("rationale"), "supplemental audit rationale")
        accounting.evidence_ids(entry["evidence_ids"], allowed[key[1]],
                                required=entry["status"] == "supported")
        seen.add(key)
    rounds.require(seen == expected.keys(), "Every resolved fidelity/directional literature label needs supplemental audit")
    unsupported = sum(entry["status"] == "unsupported" for entry in entries)
    return {"passed": unsupported == 0, "expected": len(expected), "audited": len(entries),
            "unsupported": unsupported, "entries": entries,
            "scope": "Explicit user requirement, separate from unchanged original critical classes and thresholds."}


def exact_paper_requirements(audit):
    directional = {"SUPPORTED_AS_STATED": {"supports"}, "CONTRADICTED_AS_STATED": {"refutes"},
                   "CONFLICTING_EVIDENCE": {"supports", "refutes"},
                   "SUPPORTS": {"supports"}, "REFUTES": {"refutes"},
                   "CONFLICTING": {"supports", "refutes"}}
    final = {case["case_id"]: {a["axis"]: a for a in case["assessments"]}
             for case in audit["final_cases"]}
    requirements = {}
    for cid in audit["nontrivial"]["exact_paper_claim_cases"]:
        axes = final[cid]
        rounds.require(axes["claim"].get("assertion_basis", "independent") == "independent",
                       "Report support cannot satisfy exact-paper claim exercise")
        requirements[cid] = directional[axes["claim"]["category"]] | directional[axes["literature"]["category"]]
    return requirements


def exact_authority_requirements(audit):
    final = {case["case_id"]: case for case in audit["final_cases"]}
    return {cid: {a["axis"] for a in final[cid]["assessments"]
                  if a["axis"] in rounds.MODEL_AXES and a["category"] == "INCORRECT"}
            for cid in audit["nontrivial"]["exact_authority_incorrect_cases"]}


def final_authored(config, documents):
    """Apply the complete production profile to distinct adjudicated drafts."""
    validated = initial.validate(ROOT, config["manifest"]["path"], config["final_authored"]["path"])
    actual = validated["matrix"]
    author = documents["audit"]["adjudicator"]
    rounds.require(all(actual["reviewer"][key] == author[key] for key in ("id", "model", "session_id")),
                   "Final authored reviewer differs from independent adjudicator")

    def by_case(cases):
        return {case["case_id"]: {**{key: value for key, value in case.items() if key != "assessments"},
                                  "assessments": {a["axis"]: a for a in case["assessments"]}}
                for case in cases}

    rounds.require(by_case(actual["cases"]) == by_case(documents["audit"]["final_cases"]),
                   "Final audit differs from complete adjudicated authored assessments/proof bindings")
    return {"status": "passed", "stage": "distinct_adjudication", "cases": len(actual["cases"]),
            "authored_axes": sum(len(c["assessments"]) for c in actual["cases"]),
            "canonical_persistence_checked": False, "initial_seals_augmented": False,
            "inputs": validated["inputs"], "validations": validated["validations"]}


def bind_final_citation_drafts(documents, validated):
    """A new directional anchor must use this exact final adjudication draft."""
    report = json.loads(citations.read_bound(documents["citation_config"]["citation_report"]),
                        object_pairs_hook=rounds.unique_object)
    entries = {entry["case_id"]: entry for entry in documents["final_authored"]["cases"]}
    inputs = {pin["path"]: pin["sha256"] for pin in validated["inputs"]}
    cases = {case["case_id"]: case for case in documents["manifest"]["cases"]}
    for row in report["rows"]:
        if {"final_root", "final_input", "final_sidecar", "final_proof_id"} & row.keys():
            rounds.require(Path(row["final_root"]).absolute() == ROOT,
                           "Final citation uses a different adjudication root")
            entry = entries[row["case_id"]]
            for field, authored_key in (("final_input", "review"), ("final_sidecar", "proofs")):
                relative = entry[authored_key]
                rounds.require(row[field] == {"path": str(ROOT / relative), "sha256": inputs[relative]},
                               "Final citation uses a different authored final draft/proof set")
            sidecar = rounds.read(ROOT, entry["proofs"])
            mapped = initial.mapped_ids([row["final_proof_id"]], sidecar, documents["manifest"],
                                         cases[row["case_id"]]["evidence_ids"])
            rounds.require(mapped == [row["evidence_id"]], "Final citation selected another proof identity")


def original_seals(config, documents):
    """Validate complete original authored sets, then bind exact transport mirrors."""
    base = documents["reviewer_config"]
    rounds.require(set(config["initial_seals"]) == {"reviewer-a", "reviewer-b"},
                   "Both original initial seals required")
    results = {}
    for rid, mirror_key in (("reviewer-a", "reviewer_a"), ("reviewer-b", "reviewer_b")):
        declared = config["initial_seals"][rid]
        settings = base["reviewers"][rid]
        root = Path(declared["root"]).absolute()
        rounds.require(root.resolve() == root and str(root) == settings["root"],
                       "Original seal root differs from reviewer clone")
        seal = read_pin(root, declared["seal"])
        rounds.require(seal["manifest"] == base["manifest"]
                       and seal["matrix"]["path"] == settings["matrix"]
                       and seal["canonical_identity"] == settings["canonical_identity"],
                       "Initial seal differs from canonical reviewer configuration")
        checked = initial.check(root, declared["seal"]["path"])
        rounds.require(checked["status"] == "passed" and checked["cases"] == 10
                       and checked["authored_axes"] == 60, "Complete initial seal replay failed")
        original_raw = rounds.safe(root, settings["matrix"]).read_bytes()
        mirrored_raw = rounds.safe(ROOT, config[mirror_key]["path"]).read_bytes()
        rounds.require(original_raw == mirrored_raw, "Transport matrix differs from original initial matrix")
        original_receipt = rounds.safe(root, settings["matrix"] + ".receipt.json").read_bytes()
        mirror_receipt = rounds.safe(ROOT, config[mirror_key]["path"] + ".receipt.json").read_bytes()
        # A transport save honestly has its own path/time. The original complete
        # seal remains authoritative for scientific authorship and initial time.
        left, right = json.loads(original_receipt), json.loads(mirror_receipt)
        for field in ("matrix_sha256", "package_sha256", "reviewer"):
            rounds.require(left[field] == right[field], "Transport receipt changed original seal identity")
        matrix = json.loads(original_raw)
        rounds.require(matrix["reviewer"]["id"] == rid, "Original initial reviewer identity differs")
        results[rid] = {"root": str(root), "check": checked,
                        "matrix_sha256": rounds.digest(original_raw),
                        "original_matrix_receipt_sha256": rounds.digest(original_receipt),
                        "mirror_matrix_receipt_sha256": rounds.digest(mirror_receipt),
                        "original_saved_at": left["saved_at"],
                        "transport_saved_at": right["saved_at"]}
    return results


def technical_gate(pair_receipt, citation_receipt, expected_pairs, required_citations,
                   *, package_sha256, round_id, exact_paper_cases=None, exact_authority_cases=None):
    """Count actual returned units; receipt totals cannot replace missing rows."""
    problems = []
    if (pair_receipt.get("mode") != "batch" or citation_receipt.get("mode") != "batch"
            or any(receipt.get("package_sha256") != package_sha256
                   or receipt.get("round_id") != round_id for receipt in (pair_receipt, citation_receipt))):
        problems.append("batch_round_or_package_mismatch")
    rows = pair_receipt.get("rows", [])
    keys = [(row.get("reviewer"), row.get("case_id")) for row in rows]
    complete_pairs = len(keys) == len(set(keys)) == len(expected_pairs) == 20 and set(keys) == expected_pairs
    if not complete_pairs:
        problems.append("twenty_original_pair_slots_not_complete")
    review_ids = [row.get("review_id_sha256") for row in rows]
    if len(set(review_ids)) != 20 or not all(review_ids):
        problems.append("canonical_review_identities_missing_or_repeated")
    successful, proof_total, proof_passed, unknown = 0, 0, 0, 0
    for row in rows:
        proofs = row.get("proofs", [])
        proof_total += len(proofs)
        unknown += row.get("unknown_proof_denominator") is not False
        proof_keys = [proof.get("evidence_id_sha256") for proof in proofs]
        unique_proofs = len(proof_keys) == len(set(proof_keys)) and all(proof_keys)
        good_proofs = [proof for proof in proofs if proof.get("status") == "passed"
                       and proof.get("proof_count") == 1]
        proof_passed += len(good_proofs)
        successful += bool(row.get("status") == "passed" and row.get("canonical_pair_replayed") is True
                           and row.get("authored_saved_document_equal") is True
                           and row.get("adaptation_parity", {}).get("status") == "passed"
                           and row.get("canonical_command", {}).get("exit_code") == 0
                           and not row.get("errors") and row.get("unknown_proof_denominator") is False
                           and unique_proofs and len(good_proofs) == len(proofs)
                           and row.get("verified_evidence") == len(proofs))
    if successful != 20 or unknown or proof_passed != proof_total or proof_total == 0:
        problems.append("canonical_parity_or_initial_proof_replay_incomplete")
    contexts = pair_receipt.get("contexts", {})
    if (set(contexts) != {"reviewer-a", "reviewer-b"} or pair_receipt.get("context_errors")
            or any(c.get("status") != "passed" for c in contexts.values())):
        problems.append("reviewer_context_replay_incomplete")
    citation_rows = citation_receipt.get("rows", [])
    citation_keys = [(row.get("case_id"), row.get("evidence_id")) for row in citation_rows]
    complete_citations = (bool(required_citations) and len(citation_keys) == len(set(citation_keys))
                          == len(required_citations) and set(citation_keys) == required_citations.keys())
    if not complete_citations:
        problems.append("final_citation_slots_missing_repeated_or_untested")
    citation_passed = sum(row.get("status") == "passed"
                          and set(row.get("final_axes", [])) == required_citations.get(key)
                          and len(row.get("final_axes", [])) == len(set(row.get("final_axes", [])))
                          for row, key in zip(citation_rows, citation_keys, strict=True))
    if (citation_passed != len(required_citations)
            or citation_receipt.get("expected_total_final_citations") != len(required_citations)):
        problems.append("final_literal_identity_or_axis_replay_incomplete")
    paper_kinds = {"jats", "europepmc_abstract"}
    if any("literature" in row.get("final_axes", []) and row.get("kind") not in paper_kinds
           for row in citation_rows):
        problems.append("final_literature_uses_nonpaper_evidence")
    exact_paper_cases = exact_paper_cases or {}
    paper_support = {}
    for row in citation_rows:
        if (row.get("status") == "passed" and row.get("kind") in paper_kinds
                and row.get("scope") == "exact"
                and row.get("support") in {"supports", "refutes"}
                and {"claim", "literature"} <= set(row.get("proof_axes", []))
                and {"claim", "literature"} <= set(row.get("final_axes", []))):
            paper_support.setdefault(row["case_id"], set()).add(row.get("support"))
    if any(not needed <= paper_support.get(cid, set()) for cid, needed in exact_paper_cases.items()):
        problems.append("declared_exact_paper_claim_lacks_exact_directional_paper_witness")
    exact_authority_cases = exact_authority_cases or {}
    authority_axes = {}
    for row in citation_rows:
        if (row.get("status") == "passed" and row.get("kind") == "authority"
                and row.get("scope") == "exact" and row.get("support") == "refutes"):
            axes = set(row.get("final_axes", [])) & set(row.get("proof_axes", [])) & set(rounds.MODEL_AXES)
            authority_axes.setdefault(row["case_id"], set()).update(axes)
    if any(not needed & authority_axes.get(cid, set()) for cid, needed in exact_authority_cases.items()):
        problems.append("declared_exact_authority_incorrect_lacks_exact_refuting_model_witness")
    return {"passed": not problems, "problems": problems,
            "canonical_pairs": {"expected": 20, "retained": len(rows), "verified": successful,
                                "complete_slot_inventory": complete_pairs},
            "initial_proofs": {"known_expected": proof_total, "passed": proof_passed,
                               "entries_with_unknown_denominator": unknown},
            "final_citations": {"expected": len(required_citations), "retained": len(citation_rows),
                                "passed": citation_passed, "complete_slot_inventory": complete_citations},
            "exact_paper_exercises": {"required": {cid: sorted(values) for cid, values in exact_paper_cases.items()},
                                      "verified_support": {cid: sorted(values) for cid, values in paper_support.items()}},
            "exact_authority_exercises": {"eligible_final_incorrect_axes": {
                cid: sorted(values) for cid, values in exact_authority_cases.items()},
                "exact_refuting_authority_axes": {cid: sorted(values) for cid, values in authority_axes.items()}}}


def finalize_accounting(evaluated, integrity, seals, supplemental):
    result = copy.deepcopy(evaluated)
    original_evidence_gate = result["final_gates"]["evidence_replay"]
    adjudicator_passed = original_evidence_gate["authored_status"] == "passed"
    seals_passed = set(seals) == {"reviewer-a", "reviewer-b"}
    evidence_passed = integrity["passed"] and adjudicator_passed and seals_passed
    result["final_gates"]["evidence_replay"] = {
        **original_evidence_gate, "passed": evidence_passed,
        "status": "passed" if evidence_passed else "failed",
        "reason": "Actual complete canonical, literal and identity replay plus original initial "
                  "seals; semantic sufficiency remains the separate identified adjudicator's judgment.",
        "independent_adjudicator_integrity_passed": adjudicator_passed,
        "complete_initial_seals_verified": seals_passed, "actual_replay": integrity,
    }
    passed = (all(gate_leaves(result["initial_gates"])) and all(gate_leaves(result["final_gates"]))
              and supplemental["passed"])
    result["supplemental_semantic_audit"] = supplemental
    result.update(schema=SCHEMA, status="passed_operational_calibration" if passed else "failed_gate",
                  scientific_calibration_passed=passed, remaining_90_authorized_by_result=passed,
                  expansion_authorized=False,
                  interpretation="Original operational calibration gates only. Agreement, replay and "
                  "persistence do not establish independent expert validation or graph admission.")
    return result


def new_output(relative):
    path = Path(relative)
    rounds.require(not path.is_absolute() and path.parts and path.parts[0] == ".temp"
                   and ".." not in path.parts, "New repository-relative private output required")
    output = rounds.safe(ROOT, str(path), exists=False)
    rounds.require(not output.exists(), "Finalization output already exists")
    missing, parent = [], output
    while not parent.exists():
        missing.append(parent)
        parent = parent.parent
    for directory in reversed(missing):
        directory.mkdir(mode=0o700)
    return output


def verify_config_bindings(config, documents):
    base = documents["reviewer_config"]
    manifest = documents["manifest"]
    rounds.require(base.get("round_id") == manifest["round_id"]
                   and base["manifest"] == config["manifest"]["path"]
                   and base["package_sha256"] == config["manifest"]["sha256"],
                   "Reviewer replay config differs from exact round package")
    frozen = {item["path"]: item for item in manifest["files"]}
    for module in (accounting, rounds, citations, pairs, initial):
        path = Path(module.__file__).absolute()
        relative = str(path.relative_to(ROOT))
        role = "round_helper" if module is rounds else "proof_adapter"
        rounds.require(relative in frozen and frozen[relative]["role"] == role
                       and frozen[relative]["sha256"] == rounds.digest(path.read_bytes()),
                       "Finalizer dependency is not the frozen runtime: " + relative)
    own = str(Path(__file__).absolute().relative_to(ROOT))
    rounds.require(own in frozen and frozen[own]["role"] == "proof_adapter"
                   and frozen[own]["sha256"] == rounds.digest(Path(__file__).read_bytes()),
                   "Finalizer is not frozen with this package")
    cited_config = documents["citation_config"]
    for field, key in (("reviewer_config", "reviewer_config"), ("final_audit", "audit")):
        raw = citations.read_bound(cited_config[field], ROOT / config[key]["path"])
        rounds.require(rounds.digest(raw) == config[key]["sha256"], "Final citation config uses another audit/config")
    cases, entries = pairs.expected_entries(base)
    rounds.require(set(cases) == {case["case_id"] for case in manifest["cases"]}, "Original cohort differs")
    return {(entry["reviewer"], entry["case_id"]) for entry in entries}


def failure_slots(output, expected):
    """Keep attempted/failed/unattempted slots even when a later prerequisite fails."""
    receipt_path = output / "canonical-pairs" / "receipt.json"
    rows = []
    receipt_error = None
    if receipt_path.exists():
        try:
            rows = json.loads(receipt_path.read_bytes(), object_pairs_hook=rounds.unique_object)["rows"]
        except Exception as error:
            receipt_error = str(error)
    slots = []
    for rid, cid in sorted(expected):
        found = [row for row in rows if row.get("reviewer") == rid and row.get("case_id") == cid]
        slots.append({"reviewer": rid, "case_id": cid,
                      "status": found[0].get("status", "invalid") if len(found) == 1
                      else "unattempted" if not found else "invalid_repeated_slot",
                      "retained_rows": len(found),
                      "unknown_proof_denominator": not found or any(
                          row.get("unknown_proof_denominator") is not False for row in found)})
    return {"expected": 20, "slots": slots, "retained_rows": len(rows),
            "receipt_read_error": receipt_error,
            "scope": "Observed execution only; prerequisite failure prevents a final pass."}


def run(config_path, output_relative):
    config_raw = rounds.safe(ROOT, config_path).read_bytes()
    config = json.loads(config_raw, object_pairs_hook=rounds.unique_object)
    output = new_output(output_relative)
    pairs.write(output / "config.json", raw=config_raw)
    _, cohort = rounds.baseline(ROOT)
    expected = {(rid, case["case_id"]) for rid in ("reviewer-a", "reviewer-b") for case in cohort["cases"]}
    final, evaluated = None, None
    try:
        documents = {key: read_pin(ROOT, config[key]) for key in PIN_KEYS}
        expected = verify_config_bindings(config, documents)
        required_citations = expected_citations(documents["audit"], documents["manifest"])
        evaluated = accounting.evaluate(ROOT, *[config[key]["path"] for key in
                                              ("manifest", "reviewer_a", "reviewer_b", "comparison", "audit")])
        rounds.require(evaluated == documents["accounting"], "Authored accounting differs from unchanged reevaluation")
        supplemental = supplemental_audit(documents)
        paper_requirements = exact_paper_requirements(documents["audit"])
        authority_requirements = exact_authority_requirements(documents["audit"])
        final_drafts = final_authored(config, documents)
        pairs.write(output / "final-authored-validation.json", final_drafts)
        bind_final_citation_drafts(documents, final_drafts)
        seals = original_seals(config, documents)
        pairs.write(output / "initial-seals.json", seals)
        pair_canary = canary_directory(config["pair_canary"])
        citation_canaries = [canary_directory(pin) for pin in config["citation_canaries"]]
        pair_receipt = pairs.run(documents["reviewer_config"], output / "canonical-pairs", "batch",
                                 canary=pair_canary)
        citation_receipt = citations.run(documents["citation_config"], output / "final-citations", "batch",
                                         canaries=citation_canaries)
        # Recheck seals and all authored top-level pins after actual execution.
        rounds.require(original_seals(config, documents) == seals, "Original seals changed during finalization")
        for key in PIN_KEYS:
            read_pin(ROOT, config[key])
        initial.verify_pins(ROOT, final_drafts["inputs"])
        rounds.require(rounds.safe(ROOT, config_path).read_bytes() == config_raw, "Finalizer config changed")
        integrity = technical_gate(pair_receipt, citation_receipt, expected, required_citations,
                                   package_sha256=config["manifest"]["sha256"],
                                   round_id=documents["manifest"]["round_id"],
                                   exact_paper_cases=paper_requirements,
                                   exact_authority_cases=authority_requirements)
        final = finalize_accounting(evaluated, integrity, seals, supplemental)
        final["initial_seal_checks"] = seals
        final["final_authored_validation"] = {"path": str(output / "final-authored-validation.json"),
                                               "sha256": rounds.digest((output / "final-authored-validation.json").read_bytes())}
        final["replay_receipts"] = {name: {"path": str(output / folder / "receipt.json"),
                                         "sha256": rounds.digest((output / folder / "receipt.json").read_bytes())}
                                    for name, folder in (("pairs", "canonical-pairs"),
                                                         ("citations", "final-citations"))}
    except Exception as error:
        failure = {"error_type": type(error).__name__, "message": str(error)}
        pairs.write(output / "failure.json", failure)
        final = {**(copy.deepcopy(evaluated) if evaluated is not None else {}),
                 "schema": SCHEMA, "status": "failed_prerequisite_or_replay",
                 "scientific_calibration_passed": False, "remaining_90_authorized_by_result": False,
                 "expansion_authorized": False, "failure": failure,
                 "canonical_pairs": failure_slots(output, expected),
                 "expected_pairs": 20, "replay_outputs_retained_under": str(output),
                 "scope": "No prerequisite failure reduces the twenty-slot denominator. "
                          "Any completed child receipts remain preserved; absent slots are unattempted."}
        if evaluated is not None:
            final["final_gates"]["evidence_replay"].update(
                passed=False, status="failed", reason="Finalization prerequisite or replay failed; see failure receipt.")
    final["finalizer"] = {"helper_sha256": rounds.digest(Path(__file__).read_bytes()),
                          "config_sha256": rounds.digest(config_raw), "source_config": config_path,
                          "published": False, "graph_admissions": 0}
    pairs.write(output / "finalization.json", final)
    return final


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = run(args.config, args.output)
    print(json.dumps({"status": result["status"],
                      "remaining_90_authorized_by_result": result["remaining_90_authorized_by_result"],
                      "expansion_authorized": False, "output": args.output}, sort_keys=True))
    return 0 if result["scientific_calibration_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
