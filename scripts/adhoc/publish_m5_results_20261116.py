#!/usr/bin/env python3
"""Publish bounded failed-round audit copies and register a separate next round.

Original ratings, canonical pairs, source bytes and proof sidecars stay unchanged.
This helper publishes no canonical review body and grants no gate passage.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).absolute().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "m5_publication_rounds", ROOT / "scripts/adhoc/calibration_round_20261116.py")
rounds = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rounds)
PRIVATE = ROOT / ".temp/m5-worker-run-20261116"
PUBLIC = ROOT / "artifacts/m5-calibration-20261116"
EXPECTED_PACKAGE = "14175634b794a90124bb66a458af3c30f23ca40e10731c4ba89226134a89f4ab"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def pin(path):
    relative = str(path.relative_to(ROOT))
    return {"path": relative, "sha256": digest(rounds.safe(ROOT, relative).read_bytes())}


def raw(path):
    return rounds.safe(ROOT, str(path.relative_to(ROOT))).read_bytes()


def publish(path, data):
    relative = str(path.relative_to(ROOT))
    target = rounds.safe(ROOT, relative, exists=False)
    if target.exists():
        if target.read_bytes() != data:
            raise ValueError(f"Refusing changed publication: {path.name}")
        return
    rounds.write(ROOT, relative, raw=data)


def main():
    manifest = PRIVATE / "package/round-01-manifest.json"
    if digest(raw(manifest)) != EXPECTED_PACKAGE:
        raise ValueError("Wrong round01 package")
    gate_path = PRIVATE / "adjudication/gates-reviewed.json"
    gates = json.loads(raw(gate_path))
    audit = PRIVATE / "adjudication/audit.json"
    if gates["status"] != "failed_gate" or gates["scientific_calibration_passed"]:
        raise ValueError("This publication helper only preserves the failed round")
    audit_pin = next(item for item in gates["input_pins"]
                     if item["path"].endswith("/adjudication/audit.json"))
    if audit_pin != pin(audit):
        raise ValueError("Final gate result does not bind the final audit")
    publications = []
    for source, name in [
        (audit, "round-01-adjudication-audit.json"),
        (gate_path, "round-01-gates.json"),
        (PRIVATE / "adjudication/report.md", "round-01-adjudication.md"),
    ]:
        target = PUBLIC / name
        publish(target, raw(source))
        publications.append({"source": pin(source), "public_copy": pin(target)})
    rubric = ROOT / "docs/plans/m5-calibration-round02-20261116.md"
    registration = {
        "schema": "edgemech-calibration-round-registration/v1",
        "round_id": "m5-calibration-20261116-round02",
        "status": "registered_preparation_only_no_package_or_reviewers",
        "superseded_round_preserved": "m5-calibration-20261116-round01",
        "prior_round_package_sha256": EXPECTED_PACKAGE,
        "protocol": pin(ROOT / "artifacts/edge-calibration-20261115/protocol.json"),
        "cohort": pin(ROOT / "artifacts/edge-calibration-20261115/cohort.json"),
        "rubric_repair": pin(rubric),
        "case_count": 10, "axes_per_case": 6, "experimental_literature_denominator": 7,
        "threshold_changes": [], "case_replacements": [],
        "package_sha256": None, "reviewers": [], "launched": False,
        "prerequisites": [
            "Resolve or explicitly bound sampled source/producer/ontology version binding",
            "Pin predicate meanings, inherited node constraints and exact local vocabulary definitions",
            "Resolve shared claim/model canonical acceptance policy (#152) prospectively",
            "Remove separable inherited judgment prose; disclose inseparable exposure (#156)",
            "Verify aggregate publication quote budget across both sessions (#157)",
            "Fresh empty round staging and single-unit production preparation/save/check canaries",
            "New immutable package followed by two fresh sessions and separate adjudication",
        ],
        "remaining_90_authorized_by_result": False, "expansion_authorized": False,
        "finding_issues": [f"https://github.com/CultureBotAI/EdgeMech/issues/{n}"
                           for n in [144, 145, 148, 149, 152, 153, 154, 155, 156, 157, 158, 159]],
    }
    target = PUBLIC / "round-02-registration.json"
    publish(target, (json.dumps(registration, indent=2, sort_keys=True) + "\n").encode())
    publications.append({"round02_registration": pin(target)})
    receipt = {"helper": pin(Path(__file__)), "publications": publications,
               "canonical_pairs": "18 original partial pairs retained privately at original replay paths",
               "scope": "Exact bounded audit copies and prospective rubric registration; no raw bodies"}
    publish(PRIVATE / "publication-receipt.json",
            (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode())
    print(json.dumps({"published": len(publications), "round01_status": gates["status"],
                      "round02_launched": False}))


if __name__ == "__main__":
    main()
