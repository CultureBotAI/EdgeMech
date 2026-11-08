#!/usr/bin/env python3
"""Persist real native-to-canonical packet conformance for CLAW #767, 2026-11-07.

Inputs: explicit pinned native export of at most ten rows, new output directory.
Outputs: labeled native-row transport fixture, canonical bundle and receipt.
Fixture occurrences are NOT KG release occurrences or eligible-overlap results.
"""

import argparse
import hashlib
import json
import os
from collections import Counter
from pathlib import Path

from kg_microbe_curation.contract import validate_bundle
from kg_microbe_curation.identity import canonical_json, occurrence_id, sha256_json
from kg_microbe_curation.native import validate_native_assertion

from edgemech.packets import inherited_bundle
from edgemech.pins import check_contracts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-export", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    pins = check_contracts()
    raw_manifest = (args.native_export / "manifest.json").read_bytes()
    if hashlib.sha256(raw_manifest).hexdigest() != args.manifest_sha256:
        raise ValueError("Native manifest differs from explicit pin")
    manifest = json.loads(raw_manifest)
    if not 1 <= manifest["rows"] <= 10 or manifest["assertions_bytes"] > 1024 * 1024:
        raise ValueError("This transport canary requires one to ten bounded native rows")
    raw = (args.native_export / "assertions.jsonl").read_bytes()
    if (len(raw), hashlib.sha256(raw).hexdigest()) != (
        manifest["assertions_bytes"], manifest["assertions_sha256"],
    ):
        raise ValueError("Native payload differs from manifest")
    rows = raw.splitlines(keepends=True)
    assertions = [json.loads(row) for row in rows]
    for assertion in assertions:
        validate_native_assertion(assertion)
    statuses = dict(Counter(a["native_review"]["status"] for a in assertions))
    if len(rows) != manifest["rows"] or statuses != manifest["native_status_counts"]:
        raise ValueError("Native counters do not reconcile")
    fixture = {
        "format": "edgemech-native-packet-conformance/v1",
        "occurrence_domain": "native_export_transport_fixture",
        "kg_release_occurrences": False,
        "native_manifest_sha256": args.manifest_sha256,
        "member": "assertions.jsonl", "member_sha256": manifest["assertions_sha256"],
        "rows": len(rows),
    }
    input_sha = sha256_json(fixture)
    membership = {
        occurrence_id(
            manifest_sha256=input_sha, member="assertions.jsonl",
            member_sha256=manifest["assertions_sha256"], row_number=position,
            row_sha256=hashlib.sha256(row).hexdigest(),
        ): [assertion]
        for position, (row, assertion) in enumerate(zip(rows, assertions, strict=True), 1)
    }
    bundle = inherited_bundle(input_sha, membership)
    if any(d["review_state"] != "deferred" or d["disposition"] != "withheld"
           for d in bundle["decisions"]) or bundle["claims"] or bundle["reviews"]:
        raise ValueError("Native transport unexpectedly grants scientific approval")
    recovered = [a for observation in bundle["observations"]
                 for a in observation["payload"]["native_assertions"]]
    if recovered != assertions:
        raise ValueError("Canonical packet did not preserve every native envelope")
    args.output.mkdir(parents=True, exist_ok=False)
    for name, value in (("fixture.json", fixture), ("bundle.json", bundle)):
        with (args.output / name).open("xb") as stream:
            stream.write(canonical_json(value) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
    persisted = json.loads((args.output / "bundle.json").read_bytes())
    validate_bundle(persisted, expected_input_sha256=input_sha,
                    expected_occurrence_ids=membership)
    if persisted != bundle:
        raise ValueError("Persisted canonical bundle differs from validated packet")
    receipt = {
        **fixture, "contract_pins": pins, "fixture_input_sha256": input_sha,
        "bundle_sha256": hashlib.sha256((args.output / "bundle.json").read_bytes()).hexdigest(),
        "native_status_counts": statuses, "canonical_decisions": len(bundle["decisions"]),
        "canonical_observations": len(bundle["observations"]),
        "canonical_disposition": "deferred/withheld", "scientific_approvals_created": 0,
        "verified": True,
    }
    with (args.output / "receipt.json").open("xb") as stream:
        stream.write(canonical_json(receipt) + b"\n")
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
