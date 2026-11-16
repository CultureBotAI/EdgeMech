#!/usr/bin/env python3
"""Prepare one history-free reviewer view from a replayed original packet.

Preserves the complete original assertion, both nodes, source wrappers and
measurement context. Historical authored ratings in original_occurrence stay
in pinned private inputs but are not shown in this allowlisted projection.
Run fresh-47 first and check its persisted receipt before the other cases.
The v2 output location preserves the original preparation and requires a new canary.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from edgemech.occurrence_packet import validate_packet  # noqa: E402
from edgemech.storage.parquet import safe_path  # noqa: E402

BASE = ROOT / ".temp/m5-worker-run-20261116/package/cases-v2"
CONFIG_INPUTS = (
    "scripts/adhoc/prepare_m5_reviewer_views_20261116.py",
    "artifacts/edge-calibration-20261115/cohort.json",
    "src/edgemech/occurrence_packet.py",
    "src/edgemech/storage/parquet.py",
    "src/edgemech/contract-pins.json",
    "docs/record-review-profile.md",
    "uv.lock",
)
FIELDS = ("occurrence_id", "original_assertion", "endpoints", "measurement_context",
          "source_records")


def checked(path, *, exists=True):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    path = safe_path(path, exists=exists)
    if not path.is_relative_to(ROOT.absolute()):
        raise ValueError("Artifact path escapes task worktree")
    if exists and not path.is_file():
        raise ValueError("Artifact is not a regular file")
    return path


def sha(path):
    return hashlib.sha256(checked(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(checked(path).read_bytes())


def configuration():
    return {path: sha(ROOT / path) for path in CONFIG_INPUTS}


def private_parents(path):
    path = checked(path, exists=False)
    missing = []
    parent = path
    while not parent.exists():
        missing.append(parent)
        parent = parent.parent
    for directory in reversed(missing):
        safe_path(directory, exists=False).mkdir(mode=0o700)


def write_new(path, data):
    path = checked(path, exists=False)
    encoded = (json.dumps(data, indent=2, sort_keys=True) + "\n").encode()
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())
    if path.read_bytes() != encoded:
        raise ValueError("Persisted view differs")


def load_case(case):
    cohort_path = ROOT / "artifacts/edge-calibration-20261115/cohort.json"
    cohort = read(cohort_path)
    selected = [item for item in cohort["cases"] if item["case_id"] == case]
    if len(selected) != 1:
        raise ValueError("Unknown cohort case")
    packet_path = ROOT / ".temp/edge-calibration-20261115" / case / "packet.json"
    packet = read(packet_path)
    validation = validate_packet(packet, root=ROOT)
    if packet["original_assertion"] != selected[0]["original_assertion"]:
        raise ValueError("Original scope differs")
    return packet_path, packet, validation


def check(case, output_root=None):
    base = checked(BASE if output_root is None else output_root, exists=False)
    packet_path, packet, validation = load_case(case)
    receipt = read(base / case / "receipt.json")
    if receipt["case_id"] != case or receipt["configuration"] != configuration():
        raise ValueError("Canary configuration changed")
    if (receipt["packet_path"] != str(packet_path.relative_to(ROOT))
            or receipt["packet_sha256"] != sha(packet_path)):
        raise ValueError("Canary packet bytes changed")
    view_path = base / case / "view.json"
    if (receipt["view_sha256"] != sha(view_path)
            or read(view_path) != {key: packet[key] for key in FIELDS}
            or receipt["validation"] != validation):
        raise ValueError("Canary replay differs")
    return receipt


def prepare(case, output_root=None):
    base = checked(BASE if output_root is None else output_root, exists=False)
    pin = configuration()
    if case != "fresh-47":
        check("fresh-47", base)
    packet_path, packet, validation = load_case(case)
    view = {key: packet[key] for key in FIELDS}
    out = checked(base / case, exists=False)
    private_parents(base)
    out.mkdir(mode=0o700, exist_ok=False)
    write_new(out / "view.json", view)
    reread = read(out / "view.json")
    if reread != view or set(reread) != set(FIELDS):
        raise ValueError("View content differs")
    receipt = {"case_id": case, "configuration": pin,
               "packet_path": str(packet_path.relative_to(ROOT)),
               "packet_sha256": sha(packet_path), "view_sha256": sha(out / "view.json"),
               "validation": validation,
               "history_exposure": "Historical authored judgments excluded by field allowlist; "
               "original node labels and source bytes retained. Full original packet remains pinned.",
               "scientific_ratings": 0}
    write_new(out / "receipt.json", receipt)
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    operation = parser.add_mutually_exclusive_group(required=True)
    operation.add_argument("--case")
    operation.add_argument("--check")
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args()
    result = prepare(args.case, args.output_root) if args.case else check(args.check, args.output_root)
    print(json.dumps(result, sort_keys=True))
