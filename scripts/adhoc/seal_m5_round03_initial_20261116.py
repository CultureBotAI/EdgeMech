#!/usr/bin/env python3
"""Validate and seal complete authored initial reviews before comparison.

Purpose/date/issues: 2026-11-16, EdgeMech #180/#181. Inputs are a frozen round
manifest and a config with reviewer, canonical_identity, and ten case_id/review/
proofs entries. Outputs are an immutable derived matrix, its normal round receipt,
and a seal of every authored draft, proof and input. No ratings are invented;
canonical persistence and semantic sufficiency remain separate later checks.
All paths except --root are repository-relative. Quote-bearing inputs stay private.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import calibration_round_20261116 as rounds
from kg_microbe_reviews import load_document
from replay_m5_round02_pairs_20261116 import assessment_parity, evidence_mapping

from edgemech.occurrence_review import validate_occurrence_review

HELPER = "scripts/adhoc/seal_m5_round03_initial_20261116.py"
SCHEMA = "edgemech-round03-initial-seal/v1"
SCOPE = "initial_authored_draft_and_literal_proof_validation_not_semantic_approval_or_persistence"
IDENTITY_KEYS = ("id", "model", "session_id")


def pin(root, path):
    raw = rounds.safe(root, path).read_bytes()
    return {"path": path, "sha256": rounds.digest(raw)}


def verify_pins(root, pins):
    for item in pins:
        rounds.require(pin(root, item["path"]) == item, f"Sealed input changed: {item['path']}")


def mapped_ids(ids, sidecar, manifest, allowed):
    mapped, failures = evidence_mapping(ids, sidecar, manifest, allowed)
    rounds.require(not failures, "Initial proof mapping failed: " + ", ".join(failures))
    return sorted(mapped)


def project_case(authored, sidecar, manifest, case):
    axes = []
    for assessment in authored["assessments"]:
        dimensions = {d["name"]: d["value"] for d in assessment["dimensions"]}
        axis = dimensions["axis"]
        projected = {
            "axis": axis, "category": dimensions["category"], "scope": dimensions["scope"],
            "rationale": assessment["summary"],
            "dimensions": {name: value for name, value in dimensions.items()
                           if name not in {"axis", "category", "scope"}},
            "evidence_ids": mapped_ids(assessment["evidence_ids"], sidecar, manifest,
                                       case["evidence_ids"]),
        }
        if "assertion_basis" in assessment:
            projected["assertion_basis"] = assessment["assertion_basis"]
        if "report_witnesses" in assessment:
            report = assessment["report_witnesses"]
            projected["report_witnesses"] = {"scope": report["scope"], **{
                group: mapped_ids(report[group], sidecar, manifest, case["evidence_ids"])
                for group in ("source_instance_evidence_ids", "identity_evidence_ids",
                              "definition_evidence_ids")}}
        axes.append(projected)
    result = {"case_id": case["case_id"], "occurrence_id": case["occurrence_id"],
              "assessments": axes}
    rounds.require(not assessment_parity(authored, authored, result, sidecar, manifest),
                   "Derived matrix differs from complete authored assessment")
    return result


def validate(root, manifest_path, config_path):
    rounds.verify(root, manifest_path)
    manifest = rounds.read(root, manifest_path)
    frozen = {item["path"]: item["sha256"] for item in manifest["files"]}
    rounds.require(HELPER in frozen and frozen[HELPER] == pin(root, HELPER)["sha256"],
                   "Initial sealing helper must be in the frozen runtime")
    config = rounds.read(root, config_path)
    reviewer = config["reviewer"]
    for key in (*IDENTITY_KEYS, "historical_exposure"):
        rounds.text(reviewer.get(key), "actual reviewer " + key)
    rounds.require(reviewer["model"] not in {"unknown", "configured_default"},
                   "Actual reviewer model required")
    canonical_identity = rounds.text(config.get("canonical_identity"), "canonical reviewer identity")
    rounds.require(canonical_identity == reviewer["id"], "Canonical identity must equal reviewer ID")
    cases = {c["case_id"]: c for c in manifest["cases"]}
    entries = config["cases"]
    rounds.require(isinstance(entries, list) and len(entries) == 10 and len(cases) == 10,
                   "Exactly ten complete authored cases required")
    ids = [entry["case_id"] for entry in entries]
    rounds.require(len(set(ids)) == 10 and set(ids) == cases.keys(),
                   "Initial authored cases differ from frozen cohort")
    for field in ("review", "proofs"):
        rounds.require(len({entry[field] for entry in entries}) == 10,
                       f"Repeated initial {field} path")
    pins = {}

    def add_pin(path, expected=None):
        current = pin(root, path)
        rounds.require(expected is None or current["sha256"] == expected,
                       "Initial authored input hash mismatch")
        rounds.require(path not in pins or pins[path] == current, "Input changed during validation")
        pins[path] = current

    add_pin(manifest_path)
    add_pin(config_path)
    for item in manifest["files"]:
        add_pin(item["path"], item["sha256"])
    matrix = {"round_id": manifest["round_id"], "package_sha256": pins[manifest_path]["sha256"],
              "reviewer": reviewer, "cases": []}
    validations, review_ids = [], set()
    for entry in sorted(entries, key=lambda item: item["case_id"]):
        case = cases[entry["case_id"]]
        add_pin(entry["review"])
        add_pin(entry["proofs"])
        authored = load_document(rounds.safe(root, entry["review"]).read_bytes())
        sidecar = rounds.read(root, entry["proofs"])
        actual = authored["reviewer"]
        rounds.require(actual.get("identity") == canonical_identity and
                       actual.get("model") == reviewer["model"] and actual.get("kind") == "agent",
                       "Canonical reviewer identity/model differs from actual session")
        rounds.require(all(sidecar.get("reviewer", {}).get(key) == reviewer[key]
                           for key in IDENTITY_KEYS), "Proof reviewer session differs")
        rounds.require(authored["review_id"] not in review_ids, "Repeated canonical review identity")
        review_ids.add(authored["review_id"])
        for item in authored["source"]["inputs"]:
            add_pin(item["path"], item["sha256"])
        checked = validate_occurrence_review(root, authored, case["packet_path"], entry["proofs"])
        rounds.require(checked["occurrence_id"] == case["occurrence_id"],
                       "Authored review targets another occurrence")
        matrix["cases"].append(project_case(authored, sidecar, manifest, case))
        validations.append({"case_id": case["case_id"], "review": pins[entry["review"]],
                            "proofs": pins[entry["proofs"]], "packet": pins[case["packet_path"]],
                            "review_id": authored["review_id"], "validation": checked})
    rounds.validate_matrix(root, manifest_path, matrix)
    verify_pins(root, pins.values())
    return {"matrix": matrix, "inputs": sorted(pins.values(), key=lambda item: item["path"]),
            "validations": validations, "canonical_identity": canonical_identity}


def seal(root, manifest_path, config_path, output):
    rounds.require(Path(output).parts and Path(output).parts[0] == ".temp",
                   "Initial quote-bearing seal must remain private under .temp")
    ignored = subprocess.run(["git", "check-ignore", "-q", "--no-index", "--", output],
                             cwd=root, capture_output=True, check=False)
    rounds.require(ignored.returncode == 0, "Initial seal destination must be Git-ignored")
    result = validate(root, manifest_path, config_path)
    directory = rounds.safe(root, output, exists=False)
    rounds.require(not directory.exists(), "Initial seal output already exists")
    # The final receipt is the completion marker. Interrupted partial outputs stay
    # preserved and cannot be accepted by check or the normal matrix reader.
    directory.mkdir(parents=True, mode=0o700)
    matrix_path = str(Path(output) / "matrix.json")
    seal_path = str(Path(output) / "initial-seal.json")
    verify_pins(root, result["inputs"])
    matrix_sha = rounds.write(root, matrix_path, result["matrix"])
    saved_at = datetime.now(timezone.utc).isoformat()
    document = {"schema": SCHEMA, "scope": SCOPE, "saved_at": saved_at,
                "manifest": manifest_path, "config": config_path,
                "matrix": {"path": matrix_path, "sha256": matrix_sha},
                **{key: value for key, value in result.items() if key != "matrix"}}
    seal_sha = rounds.write(root, seal_path, document)
    verify_pins(root, result["inputs"])
    rounds.write(root, matrix_path + ".receipt.json", {
        "schema": rounds.SCHEMA, "matrix_path": matrix_path, "matrix_sha256": matrix_sha,
        "package_sha256": result["matrix"]["package_sha256"], "saved_at": saved_at,
        "reviewer": result["matrix"]["reviewer"], "scope": SCOPE,
        "initial_seal": {"path": seal_path, "sha256": seal_sha}})
    return check(root, seal_path)


def check(root, seal_path):
    document = rounds.read(root, seal_path)
    rounds.require(document.get("schema") == SCHEMA, "Wrong initial seal schema")
    verify_pins(root, document["inputs"])
    matrix_path = document["matrix"]["path"]
    rounds.require(pin(root, matrix_path) == document["matrix"], "Initial matrix changed")
    receipt = rounds.read(root, matrix_path + ".receipt.json")
    rounds.require(receipt.get("initial_seal") == pin(root, seal_path), "Initial seal changed")
    matrix, _ = rounds.sealed_matrix(root, document["manifest"], matrix_path)
    current = validate(root, document["manifest"], document["config"])
    rounds.require(current["matrix"] == matrix and all(current[key] == document[key]
                   for key in ("inputs", "validations", "canonical_identity")),
                   "Initial authored values or proof identities changed")
    return {"status": "passed", "scope": SCOPE, "seal": pin(root, seal_path),
            "matrix": document["matrix"], "cases": len(matrix["cases"]),
            "authored_axes": sum(len(case["assessments"]) for case in matrix["cases"]),
            "pinned_inputs": len(document["inputs"]), "canonical_persistence_checked": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "seal"):
        sub = commands.add_parser(name)
        sub.add_argument("--manifest", required=True)
        sub.add_argument("--config", required=True)
        if name == "seal":
            sub.add_argument("--output", required=True)
    commands.add_parser("check").add_argument("--seal", required=True)
    args = parser.parse_args()
    root = args.root.absolute()
    if args.command == "check":
        result = check(root, args.seal)
    elif args.command == "seal":
        result = seal(root, args.manifest, args.config, args.output)
    else:
        checked = validate(root, args.manifest, args.config)
        result = {"status": "passed", "scope": SCOPE, "cases": len(checked["validations"]),
                  "pinned_inputs": len(checked["inputs"]), "canonical_persistence_checked": False}
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
