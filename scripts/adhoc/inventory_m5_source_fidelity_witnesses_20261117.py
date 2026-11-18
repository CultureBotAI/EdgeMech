#!/usr/bin/env python3
"""Inventory immutable round03 source-fidelity bindings for issue205, 2026-11-17.

Inputs: exact original manifest and completed adjudication audit. Output: a
coordinator-only JSON inventory; no evidence text, new categories or readiness
claim is generated. Historical categories remain historical. No network calls.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

MANIFEST_SHA256 = "3928396bf4c089620ec0209fdcb986c14f36969259ed01ab563c6807037ee298"
AUDIT_SHA256 = "ff949f12e4e88c332736085798fa2b4454b107a5ed32203cc6ed4ecf7024cefe"


def read_pinned(path: Path, expected: str) -> dict:
    data = path.read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected:
        raise ValueError(f"Original input hash mismatch: {path}: {actual}")
    return json.loads(data)


def inventory(manifest: dict, audit: dict) -> dict:
    if audit["package_sha256"] != MANIFEST_SHA256:
        raise ValueError("Audit references a different original package")
    if manifest["round_id"] != audit["round_id"]:
        raise ValueError("Audit and package round identities differ")
    cases = {case["case_id"]: case for case in manifest["cases"]}
    finals = {case["case_id"]: case for case in audit["final_cases"]}
    if len(cases) != 10 or len(finals) != 10 or cases.keys() != finals.keys():
        raise ValueError("Expected the same ten original and adjudicated cases")
    pins: dict[str, list[dict]] = {}
    for pin in manifest["files"]:
        for evidence_id in pin.get("evidence_ids", []):
            pins.setdefault(evidence_id, []).append(pin)
    records = []
    for case_id, case in cases.items():
        final = finals[case_id]
        if final["occurrence_id"] != case["occurrence_id"]:
            raise ValueError(f"Changed occurrence identity: {case_id}")
        assessments = [a for a in final["assessments"] if a["axis"] == "source_fidelity"]
        if len(assessments) != 1:
            raise ValueError(f"Expected exactly one source-fidelity assessment: {case_id}")
        assessment = assessments[0]
        evidence = []
        for evidence_id in assessment["evidence_ids"]:
            if evidence_id not in case["evidence_ids"] or evidence_id not in pins:
                raise ValueError(f"Unbound historical evidence: {case_id}/{evidence_id}")
            evidence.append({"evidence_id": evidence_id, "original_pins": pins[evidence_id]})
        records.append({
            "case_id": case_id,
            "occurrence_id": case["occurrence_id"],
            "original_assertion": case["original_assertion"],
            "historical_final_source_fidelity": assessment["category"],
            "historical_scope": assessment["scope"],
            "historical_evidence_bindings": evidence,
        })
    return {
        "purpose": "coordinator_only_historical_binding_inventory",
        "issue": "https://github.com/CultureBotAI/EdgeMech/issues/205",
        "round_id": manifest["round_id"],
        "manifest_sha256": MANIFEST_SHA256,
        "audit_sha256": AUDIT_SHA256,
        "limitations": [
            "No new scientific assessment or evidence sufficiency decision.",
            "Original pin membership is checked; underlying source bytes are not replayed.",
            "Contains historical outcomes: never include in blinded reviewer navigation.",
            "A complete binding inventory does not authorize another round or expansion.",
        ],
        "cases": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = inventory(read_pinned(args.manifest, MANIFEST_SHA256), read_pinned(args.audit, AUDIT_SHA256))
    if args.output.exists():
        raise ValueError(f"Refusing to overwrite an existing inventory: {args.output}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.output.chmod(0o600)
    print(json.dumps({"output": str(args.output), "cases": len(result["cases"]),
                      "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest()}))


if __name__ == "__main__":
    main()
