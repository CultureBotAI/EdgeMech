#!/usr/bin/env python3
"""Assemble authored review data without inventing judgments; 2026-11-16, #180/#181/#192.

Inputs: frozen manifest, one case ID, authored canonical metadata, six compact
assessments and explicit proof specifications. Outputs: exclusive private
review/proof JSON and validation receipt. Computes only pins, literal offsets,
schema representation and canonical outcomes. No retrieval or canonical save.
"""
from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).parent))

import calibration_round_20261116 as rounds  # noqa: E402

from edgemech.literature_cache import LiteratureCache, verify_quote  # noqa: E402
from edgemech.occurrence_review import (  # noqa: E402
    CATEGORIES,
    DETAILS,
    PROFILE,
    _europepmc_abstract,
    _jats,
    validate_occurrence_review,
)


def input_pin(root, path):
    return {"path": path, "sha256": rounds.digest(rounds.safe(root, path).read_bytes())}


def make_evidence(root, manifest, case, specs, accessed_at):
    files = {eid: pin for pin in manifest["files"] for eid in pin.get("evidence_ids", [])}
    proofs, evidence, seen = [], [], set()
    for authored in specs:
        item = copy.deepcopy(authored)
        eid = rounds.text(item["evidence_id"], "evidence ID")
        rounds.require(eid not in seen, "Duplicate authored evidence ID")
        seen.add(eid)
        mid = item["manifest_evidence_id"]
        rounds.require(mid in case["evidence_ids"] and mid in files, "Evidence outside case")
        pin = files[mid]
        raw_pin = input_pin(root, pin["path"])
        rounds.require(raw_pin["sha256"] == pin["sha256"], "Manifest evidence changed")
        rounds.require("input" not in item, "Input is derived from frozen manifest")
        summary = rounds.text(item.pop("summary"), "evidence summary")
        locator = rounds.text(item.pop("locator"), "authored locator")
        quote = item.pop("quote", None)
        item["input"] = raw_pin
        kind = item["kind"]
        if kind == "packet":
            rounds.require(pin["path"] == case["packet_path"], "Packet proof must use original packet")
            rounds.require(quote is None, "Packet proof cannot contain a quote")
            canonical_kind = "record_content"
        else:
            raw = rounds.safe(root, pin["path"]).read_bytes()
            if kind == "authority":
                rounds.require(pin["role"] == "authority", "Authority proof requires authority input")
                rounds.require(item.get("version") == pin["version"], "Authority version differs")
                text, extractor_kind, canonical_kind = raw.decode(), "authority_text", "authority"
            elif kind == "europepmc_abstract":
                rounds.require(pin["role"] == "evidence", "Paper proof requires frozen evidence input")
                text, _ = _europepmc_abstract(raw, item)
                extractor_kind, canonical_kind = "abstract", "primary_source"
                rounds.require(locator.startswith("abstract;"), "Abstract locator must disclose extent")
            elif kind == "jats":
                rounds.require(pin["role"] == "evidence", "Paper proof requires frozen evidence input")
                text, _ = _jats(raw, item)
                extractor_kind, canonical_kind = "oa_fulltext", "primary_source"
            else:
                raise ValueError("Unsupported proof representation")
            span = verify_quote(LiteratureCache._document(
                {"response_sha256": raw_pin["sha256"]}, extractor_kind, text), quote)
            for key in ("text_sha256", "start", "end", "extractor"):
                rounds.require(key not in item, "Quote offsets are computed from literal text")
                item[key] = span[key]
            locator += f"; chars {span['start']}:{span['end']}"
            quote = span["quote"]
        ev = {"evidence_id": eid, "kind": canonical_kind, "reference": item["reference"],
              "locator": locator, "accessed_at": accessed_at, "support": item["support"],
              "summary": summary, "snapshot_sha256": raw_pin["sha256"]}
        if quote is not None:
            ev["quote"] = quote
        proofs.append(item)
        evidence.append(ev)
    return proofs, evidence


def make_assessments(authored, oid):
    output, seen = [], set()
    for item in authored:
        axis, category = item["axis"], item["category"]
        rounds.require(axis in CATEGORIES and axis not in seen, "Duplicate or unknown axis")
        seen.add(axis)
        rounds.require(category in CATEGORIES[axis] and category != "UNASSESSED", "Incomplete category")
        rounds.require(DETAILS[axis] <= item["dimensions"].keys(), "Missing authored dimensions")
        rounds.require(not {"axis", "category", "scope"} & item["dimensions"].keys(),
                       "Reserved dimension override")
        ids = item["evidence_ids"]
        dims = {"axis": axis, "category": category, "scope": item["scope"], **item["dimensions"]}
        assessment = {
            "assessment_id": axis, "area": "evidence", "topic": axis,
            "outcome": CATEGORIES[axis][category], "summary": item["rationale"],
            "target_ids": [oid], "evidence_ids": ids,
            "dimensions": [{"name": key, "value": value, "definition": key,
                            "evidence_ids": ids} for key, value in dims.items()],
        }
        for key in ("assertion_basis", "report_witnesses"):
            if key in item:
                assessment[key] = copy.deepcopy(item[key])
        output.append(assessment)
    rounds.require(seen == CATEGORIES.keys(), "All six authored axes required")
    return output


def assemble(root, manifest_path, spec_path, output):
    rounds.verify(root, manifest_path)
    initial_spec_pin = input_pin(root, spec_path)
    manifest, authored = rounds.read(root, manifest_path), rounds.read(root, spec_path)
    matches = [c for c in manifest["cases"] if c["case_id"] == authored["case_id"]]
    rounds.require(len(matches) == 1, "Unknown or repeated case")
    case = matches[0]
    destination = rounds.safe(root, output, exists=False)
    rounds.require(Path(output).parts[0] == ".temp" and not destination.exists(),
                   "Output must be a new private .temp directory")
    check = subprocess.run(["git", "check-ignore", "--quiet", "--no-index", output], cwd=root)
    rounds.require(check.returncode == 0, "Output is not gitignored")
    metadata = copy.deepcopy(authored["review"])
    identity = authored["reviewer_identity"]
    for key in ("id", "model", "session_id", "historical_exposure"):
        rounds.text(identity.get(key), "reviewer " + key)
    rounds.require(metadata["reviewer"]["identity"] == identity["id"]
                   and metadata["reviewer"].get("model") == identity["model"]
                   and metadata["reviewer"].get("kind") == "agent",
                   "Canonical reviewer identity/model differs from session identity")
    reserved = {"source", "targets", "assessments", "evidence", "kind", "repository", "skill"}
    rounds.require(not reserved & metadata.keys(), "Canonical mechanical fields are derived")
    packet_path = case["packet_path"]
    packet = rounds.read(root, packet_path)
    proofs, evidence = make_evidence(root, manifest, case, authored["proofs"], authored["accessed_at"])
    assessments = make_assessments(authored["assessments"], case["occurrence_id"])
    sidecar = {"profile": PROFILE, "occurrence_id": case["occurrence_id"], "proofs": proofs,
               "reviewer": identity}
    proof_path, review_path = output + "/proofs.json", output + "/review.json"
    # Preserve authored attempts even if the production validator rejects them.
    rounds.write(root, proof_path, sidecar)
    paths = {manifest_path, spec_path, packet_path, proof_path,
             *(p["path"] for p in packet["inputs"].values()),
             *(p["input"]["path"] for p in proofs)}
    review = {**metadata, "kind": "record", "repository": "CultureBotAI/EdgeMech", "skill": PROFILE,
              "source": {"git_revision": subprocess.check_output(
                  ["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
                  "state": "working_tree", "inputs": [
                      {**input_pin(root, path), "role": "authored review input"} for path in sorted(paths)]},
              "targets": [{"target_id": case["occurrence_id"], "path": packet_path,
                           "selector": "occurrence_id=" + case["occurrence_id"],
                           "label": case["case_id"], "kind": "snapshot_row",
                           "ownership_note": authored["ownership_note"]}],
              "assessments": assessments, "evidence": evidence}
    rounds.write(root, review_path, review)
    result = validate_occurrence_review(root, review, packet_path, proof_path)
    rounds.verify(root, manifest_path)
    rounds.require(input_pin(root, spec_path) == initial_spec_pin, "Authored spec changed during assembly")
    receipt = {"status": "validated_draft_only", "case_id": case["case_id"],
               "authored_spec": input_pin(root, spec_path), "review": input_pin(root, review_path),
               "proofs": input_pin(root, proof_path), "validation": result,
               "canonical_persistence": "not_attempted", "scientific_approval": False}
    rounds.write(root, output + "/draft-receipt.json", receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(json.dumps(assemble(args.root, args.manifest, args.spec, args.output), sort_keys=True))


if __name__ == "__main__":
    main()
