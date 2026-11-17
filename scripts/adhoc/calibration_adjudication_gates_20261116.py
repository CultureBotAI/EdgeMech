#!/usr/bin/env python3
"""Count remaining calibration gates from a separately authored evidence audit.

Never authors judgments, changes the initial matrices or grants a scientific pass.
Authored audit statements and receipt existence do not prove quote/authority
entailment or canonical persistence; evidence-integrity verification stays pending.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).absolute().parents[2]
ROUND_HELPER = ROOT / "scripts/adhoc/calibration_round_20261116.py"
SPEC = importlib.util.spec_from_file_location("calibration_round_accounting", ROUND_HELPER)
rounds = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rounds)
require, text = rounds.require, rounds.text


def evidence_ids(value, allowed, *, required=False):
    require(isinstance(value, list) and all(isinstance(eid, str) for eid in value),
            "Evidence IDs must be a list of strings")
    require(len(value) == len(set(value)) and set(value) <= set(allowed),
            "Unbound/repeated evidence ID")
    if required:
        require(value, "Supported/resolved judgment requires evidence IDs")


def final_labels(audit, cases):
    labels = {}
    for case in audit["final_cases"]:
        cid = case["case_id"]
        require(cid in cases and cid not in labels, "Unknown/repeated final case")
        axes = {}
        for assessment in case["assessments"]:
            axis, category = assessment["axis"], assessment["category"]
            require(axis in rounds.CATEGORIES and axis not in axes, "Unknown/repeated final axis")
            require(category in rounds.CATEGORIES[axis] and category != "UNASSESSED",
                    "Invalid final category")
            text(assessment.get("scope"), "final scope")
            text(assessment.get("rationale"), "final rationale")
            dimensions = assessment.get("dimensions")
            require(isinstance(dimensions, dict) and rounds.DETAILS[axis] <= dimensions.keys(),
                    f"Missing final {axis} dimensions")
            for name in rounds.DETAILS[axis]:
                text(dimensions[name], "final " + name)
            evidence_ids(assessment["evidence_ids"], cases[cid]["evidence_ids"],
                         required=category in rounds.RESOLVED.get(axis, set())
                         or category in {"SUPPORTS", "REFUTES", "CONFLICTING", "PARTIAL"})
            rounds.validate_assertion_basis(assessment)
            axes[axis] = category
        require(axes.keys() == rounds.CATEGORIES.keys(), "All six final axes required")
        labels[cid] = axes
    require(labels.keys() == cases.keys(), "All ten final cases required")
    return labels


def critical_class(axis, category):
    if axis == "claim" and category in rounds.RESOLVED["claim"]:
        return "unsupported " + category
    if axis in rounds.MODEL_AXES and category in {"CORRECT", "INCORRECT"}:
        return "unsupported " + category + " model judgment"
    return None


def expected_critical(reviewer_labels):
    expected = {}
    for rid, labels in reviewer_labels:
        for cid, axes in labels.items():
            for axis, category in axes.items():
                if critical_class(axis, category):
                    expected[rid, cid, axis] = category
    return expected


def audit_critical(entries, expected, cases):
    counts = {"unsupported " + cat: {"emitted_labels": 0, "unsupported_labels": 0}
              for cat in rounds.RESOLVED["claim"]}
    counts.update({"unsupported " + cat + " model judgment":
                   {"emitted_labels": 0, "unsupported_labels": 0}
                   for cat in ("CORRECT", "INCORRECT")})
    seen = set()
    for entry in entries:
        key = entry["reviewer_id"], entry["case_id"], entry["axis"]
        require(key in expected and key not in seen, "Unexpected/repeated critical label audit")
        require(entry["category"] == expected[key], "Critical audit changed initial/final label")
        require(entry["status"] in {"supported", "unsupported"}, "Invalid critical audit status")
        text(entry.get("rationale"), "critical audit rationale")
        evidence_ids(entry["evidence_ids"], cases[key[1]]["evidence_ids"],
                     required=entry["status"] == "supported")
        seen.add(key)
        item = counts[critical_class(key[2], entry["category"])]
        item["emitted_labels"] += 1
        item["unsupported_labels"] += entry["status"] == "unsupported"
    require(seen == expected.keys(), "Every emitted resolved claim/model label needs critical audit")
    for item in counts.values():
        item["status"] = "audited" if item["emitted_labels"] else "untested_label_class"
    return counts


def dispositions(entries, disagreements):
    expected = {(item["case_id"], item["axis"]): item for item in disagreements}
    seen, preserved = set(), []
    blocking = 0
    for entry in entries:
        key = entry["case_id"], entry["axis"]
        require(key in expected and key not in seen, "Unexpected/repeated disagreement disposition")
        require(entry["status"] in {"resolved", "unresolved"}, "Invalid disagreement status")
        text(entry.get("rationale"), "disagreement rationale")
        seen.add(key)
        original = expected[key]
        resolved_label = any(critical_class(key[1], original[r]) for r in ("reviewer_a", "reviewer_b"))
        blocked = entry["status"] == "unresolved" and resolved_label
        blocking += blocked
        preserved.append({**original, "adjudication": entry, "blocks_passage": bool(blocked)})
    require(seen == expected.keys(), "Every initial disagreement must be preserved")
    return preserved, blocking


def gate(numerator, rule):
    return {"numerator": numerator, "denominator": rule.get("denominator"),
            "minimum": rule["minimum"], "passed": numerator >= rule["minimum"]}


def evaluate(root, manifest_path, reviewer_a, reviewer_b, comparison_path, audit_path):
    # This rereads the pinned manifest/runtime and replays the original packets.
    comparison = rounds.compare(root, manifest_path, reviewer_a, reviewer_b)
    require(rounds.read(root, comparison_path) == comparison,
            "Initial comparison differs from sealed matrices and original protocol")
    manifest = rounds.read(root, manifest_path)
    cases = {case["case_id"]: case for case in manifest["cases"]}
    left, a = rounds.sealed_matrix(root, manifest_path, reviewer_a)
    right, b = rounds.sealed_matrix(root, manifest_path, reviewer_b)
    protocol, _ = rounds.baseline(root)
    thresholds = protocol["thresholds"]
    audit = rounds.read(root, audit_path)
    require(audit["round_id"] == manifest["round_id"], "Wrong adjudication round")
    require(audit["package_sha256"] == comparison["package_sha256"], "Wrong adjudication package")
    author = audit["adjudicator"]
    for name in ("id", "model", "session_id"):
        text(author.get(name), "adjudicator " + name)
    require(author["model"] not in {"unknown", "configured_default"}, "Actual adjudicator model required")
    require(all(author["session_id"] != r["reviewer"]["session_id"]
                and author["id"] != r["reviewer"]["id"] for r in (left, right)),
            "Adjudication must use a separate session from initial reviewers")
    final = final_labels(audit, cases)
    initial_critical = audit_critical(
        audit["critical_label_audit"],
        expected_critical([(left["reviewer"]["id"], a), (right["reviewer"]["id"], b)]), cases)
    final_critical = audit_critical(audit["final_critical_label_audit"],
                                    expected_critical([("adjudicated", final)]), cases)
    preserved, blocking = dispositions(audit["disagreement_dispositions"], comparison["disagreements"])
    initial_errors = sum(item["unsupported_labels"] for item in initial_critical.values())
    final_errors = sum(item["unsupported_labels"] for item in final_critical.values())
    final_gates = {
        "final_authored_axes": gate(sum(len(axes) for axes in final.values()), thresholds["final_authored_axes"]),
        "resolved_claims": gate(sum(row["claim"] in rounds.RESOLVED["claim"] for row in final.values()), thresholds["resolved_claims"]),
        "resolved_source_fidelity": gate(sum(row["source_fidelity"] in rounds.RESOLVED["source_fidelity"] for row in final.values()), thresholds["resolved_source_fidelity"]),
        "resolved_modeling_per_axis": {axis: gate(sum(row[axis] in rounds.RESOLVED[axis] for row in final.values()), thresholds["resolved_modeling_per_axis"]) for axis in rounds.MODEL_AXES},
        "critical_overclaims": {"initial_unsupported_labels": initial_errors,
                                "final_unsupported_labels": final_errors,
                                "maximum": thresholds["critical_overclaims"]["maximum"],
                                "passed": initial_errors + final_errors <= thresholds["critical_overclaims"]["maximum"]},
        "disagreement_disposition": {"blocking_unresolved_disagreements": blocking,
                                     "passed": blocking == 0},
    }
    final_gates["final_authored_axes"]["unassessed"] = 0
    nontrivial = audit["nontrivial"]
    text(nontrivial.get("rationale"), "nontrivial exercise rationale")
    independent_claims = {
        case["case_id"] for case in audit["final_cases"]
        for assessment in case["assessments"]
        if assessment["axis"] == "claim"
        and assessment.get("assertion_basis", "independent") == "independent"
    }
    for field, gate_name, eligible in (
        ("exact_paper_claim_cases", "exact_paper_backed_directional_claims",
         {cid for cid, row in final.items()
          if row["claim"] in rounds.RESOLVED["claim"] and cid in independent_claims
          and row["literature"] in {"SUPPORTS", "REFUTES", "CONFLICTING"}}),
        ("exact_authority_incorrect_cases", "exact_authority_backed_incorrect_model_judgments",
         {cid for cid, row in final.items() if any(row[axis] == "INCORRECT" for axis in rounds.MODEL_AXES)}),
    ):
        values = nontrivial[field]
        require(isinstance(values, list) and all(isinstance(cid, str) for cid in values)
                and len(values) == len(set(values)) and set(values) <= eligible,
                "Invalid nontrivial exercise cases")
        final_gates[gate_name] = {**gate(len(values), thresholds[gate_name]),
                                  "case_ids": values, "scope": "authored evidence audit; independent replay required"}
    integrity = audit["evidence_integrity"]
    require(integrity["status"] in {"passed", "failed", "unavailable"}, "Invalid evidence integrity status")
    text(integrity.get("rationale"), "evidence integrity rationale")
    receipt_paths = integrity["receipt_paths"]
    require(isinstance(receipt_paths, list) and all(isinstance(path, str) for path in receipt_paths)
            and len(receipt_paths) == len(set(receipt_paths)), "Invalid integrity receipts")
    receipts = []
    for path in receipt_paths:
        raw = rounds.safe(root, path).read_bytes()
        require(raw, "Empty integrity receipt")
        receipts.append({"path": path, "sha256": rounds.digest(raw)})
    final_gates["evidence_replay"] = {
        "authored_status": integrity["status"], "receipts": receipts,
        "required_fraction": thresholds["evidence_replay"]["required_fraction"],
        "passed": False,
        "status": "failed" if integrity["status"] == "failed" else "pending_independent_canonical_and_evidence_replay",
        "reason": "Receipt existence and audit assertions are not semantic, quote, authority or immutable canonical-pair replay.",
    }
    applicable = protocol["experimental_literature"]["applicable_case_ids"]
    not_applicable = protocol["experimental_literature"]["not_applicable_case_ids"]
    deviations = [{"case_id": cid, "category": row["literature"]}
                  for cid, row in final.items()
                  if (cid in applicable and row["literature"] == "NOT_APPLICABLE")
                  or (cid in not_applicable and row["literature"] != "NOT_APPLICABLE")]
    numeric_gates = [value for key, value in final_gates.items()
                     if key not in {"resolved_modeling_per_axis", "evidence_replay"}]
    numeric_gates.extend(final_gates["resolved_modeling_per_axis"].values())
    failed = comparison["status"] == "failed_initial_gate" or any(not item["passed"] for item in numeric_gates) or integrity["status"] == "failed"
    return {"schema": "edgemech-calibration-adjudication-gates/v1",
            "round_id": audit["round_id"], "package_sha256": audit["package_sha256"],
            "adjudicator": author,
            "input_pins": [{"path": path, "sha256": rounds.digest(rounds.safe(root, path).read_bytes())}
                           for path in (manifest_path, reviewer_a, reviewer_b, comparison_path, audit_path)],
            "accounting_helper_sha256": rounds.digest(Path(__file__).read_bytes()),
            "initial_gates": comparison["initial_gates"], "final_gates": final_gates,
            "initial_critical_label_classes": initial_critical,
            "final_critical_label_classes": final_critical,
            "disagreements": preserved, "final_categories": final,
            "literature": {"all_ten": {cid: row["literature"] for cid, row in final.items()},
                           "experimental_denominator": protocol["experimental_literature"]["denominator"],
                           "exact_directional": sum(final[cid]["literature"] in {"SUPPORTS", "REFUTES", "CONFLICTING"} for cid in applicable),
                           "applicability_deviations": deviations},
            "status": "failed_gate" if failed else "pending_independent_evidence_integrity",
            "scientific_calibration_passed": False,
            "remaining_90_authorized_by_result": False, "expansion_authorized": False,
            "interpretation": "Operational calibration accounting; no expert independence or scientific correctness follows from agreement or saved output."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    for name in ("manifest", "reviewer-a", "reviewer-b", "comparison", "audit", "output"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    try:
        report = evaluate(args.root, args.manifest, args.reviewer_a, args.reviewer_b,
                          args.comparison, args.audit)
        rounds.write(args.root, args.output, report)
        print(json.dumps(report, sort_keys=True))
        return 0
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(f"Adjudication accounting failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
