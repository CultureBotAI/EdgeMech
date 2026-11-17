#!/usr/bin/env python3
"""Prepare replayable round02 views while removing separable historical prose."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

import prepare_m5_reviewer_views_20261116 as original

ROOT = original.ROOT
BASE = ROOT / ".temp/m5-round02-worker-20261116/package/views"
VERSION = "edgemech-blinded-view/v3"
HELPER = "scripts/adhoc/prepare_m5_round02_views_20261116.py"
REDACTED_NODE = (
    "kgmicrobe.pathway:microbedecoder_faprotax_type_of_metabolism_"
    "48701f8146aa9f1120798eee257448f7d5f71e73e4216acf3d14c101a9fc0fd8"
)


def projection(packet):
    view = copy.deepcopy({key: packet[key] for key in original.FIELDS})
    redactions = []
    for side, endpoint in view["endpoints"].items():
        if endpoint["id"] == REDACTED_NODE:
            description = endpoint["record"].pop("description")
            if not description.startswith("Reviewed source-local process meaning for "):
                raise ValueError("Historical description changed; inspect the blinding rule")
            redactions.append({
                "pointer": f"/endpoints/{side}/record/description",
                "sha256": hashlib.sha256(description.encode()).hexdigest(),
                "reason": "Separable historical review prose excluded; original retained privately",
            })
    view["blinding"] = {
        "version": VERSION, "redactions": redactions,
        "original_record_hashes": "Bind original endpoint records before redaction",
        "exposure": "Original identifiers, labels, source rows and source-authored definitions retained; "
                    "their historical selection and producer wording cannot be blinded.",
    }
    return view


def configuration():
    return {**original.configuration(), HELPER: original.sha(ROOT / HELPER)}


def check(case, base=BASE):
    packet_path, packet, validation = original.load_case(case)
    receipt = original.read(base / case / "receipt.json")
    view_path = base / case / "view.json"
    if (receipt["configuration"] != configuration()
            or receipt["case_id"] != case
            or receipt["packet_path"] != str(packet_path.relative_to(ROOT))
            or receipt["packet_sha256"] != original.sha(packet_path)
            or receipt["view_sha256"] != original.sha(view_path)
            or receipt["validation"] != validation
            or original.read(view_path) != projection(packet)):
        raise ValueError("Round02 view or bound configuration changed")
    return receipt


def prepare(case, base=BASE):
    base = original.checked(base, exists=False)
    if case != "fresh-47":
        check("fresh-47", base)
    packet_path, packet, validation = original.load_case(case)
    view = projection(packet)
    original.private_parents(base)
    folder = base / case
    folder.mkdir(mode=0o700)
    original.write_new(folder / "view.json", view)
    original.write_new(folder / "receipt.json", {
        "case_id": case, "configuration": configuration(),
        "packet_path": str(packet_path.relative_to(ROOT)),
        "packet_sha256": original.sha(packet_path),
        "view_sha256": original.sha(folder / "view.json"),
        "validation": validation, "scientific_ratings": 0,
        "blinding": view["blinding"],
    })
    return check(case, base)


def blinded_profile(raw):
    start = raw.index("The abstract-adapter launcher is\n")
    end = raw.index("Preparation receipts from PR #128", start)
    return raw[:start] + raw[end:]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--case")
    mode.add_argument("--check")
    parser.add_argument("--output-root", type=Path, default=BASE)
    args = parser.parse_args()
    result = prepare(args.case, args.output_root) if args.case else check(args.check, args.output_root)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
