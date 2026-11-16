#!/usr/bin/env python3
"""Freeze and prepare the ten-case EdgeMech calibration, 2026-11-15.

Inputs: retained public canaries, private source archives, and preregistered protocol.
Outputs: public cohort bindings and private per-case packet/replay receipts. Serves the
post-PR120 calibration preparation; no scoring, retrieval, graph edits or admission.
Run --freeze once, then --plan, then --prepare fresh-47 and --check fresh-47 before
preparing other cases individually. All writes are exclusive; originals stay intact.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).absolute().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from kg_microbe_curation.identity import sha256_json  # noqa: E402

from edgemech.occurrence_packet import (  # noqa: E402
    CLAIM_FIELDS,
    build_packet,
    validate_packet,
)
from edgemech.pins import check_contracts  # noqa: E402
from edgemech.storage.parquet import safe_path  # noqa: E402

COHORT_ID = "edge-calibration-20261115"
CANARY = "fresh-47"
BASE = Path("artifacts") / COHORT_ID
COHORT = BASE / "cohort.json"
PROTOCOL = BASE / "protocol.json"
PRIVATE = Path(".temp") / COHORT_ID
ARCHIVE = Path("/Users/marcin/agent-work/EdgeMech/edge-sample-review-20261112-data")
RAW_ROOT = Path("/Users/marcin/Documents/VIMSS/ontology/KG-Hub/KG-Microbe/"
                "kg-microbe/data/raw")
PUBLIC = {
    "first": ("artifacts/edge-sample-review-20261112/canary.jsonl",
              "e4addcfec2703cf8ef2cf879d5d1c244f5eefbd0cde0096b5e7f7170e06c8641"),
    "fresh": ("artifacts/edge-recanary-20261113/canary.jsonl",
              "76b4556e9bb62cde92eaed764710f8bbe4a420b016602be1945cb9ed3d53d703"),
}
FIRST_INPUTS = {
    "sample/private-provenance/canary.jsonl":
        "757e9c7f48ba621369c5065167b5fcb2892dcdd5f0a57fe3950d7edacb896ba9",
    "source/source-records-50.json":
        "20967c6ddd2a11778dd062064f2a8b202d02fd6f8f98fc153e5091fa69f128d3",
}
SELECTION = (
    ("first", 1, "API-kit observation and retained predicate identity"),
    ("first", 28, "Generic sporulation versus a specific spore phenotype"),
    ("first", 30, "Salinity maximum, tolerance and preference distinctions"),
    ("first", 32, "Discordant organism identifier crosswalk"),
    ("first", 43, "Zero-positive capability and original omission context"),
    ("fresh", 4, "Quantitative range-bin definition and units"),
    ("fresh", 5, "Historical evidence-positive control candidate; not a gold label"),
    ("fresh", 14, "Species identity versus a nomenclatural type-strain accession"),
    ("fresh", 32, "Second historical evidence-positive control candidate; not a gold label"),
    ("fresh", 47, "Retained partial paper evidence and strain-specific measurement context"),
)
CODE_PATHS = (
    "scripts/adhoc/prepare_calibration_20261115.py",
    "src/edgemech/occurrence_packet.py",
    "src/edgemech/occurrence_review.py",
    "src/edgemech/contract-pins.json",
    "docs/record-review-profile.md",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    path = safe_path(path)
    require(path.is_file(), f"Not a regular file: {path}")
    return path.read_bytes()


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def pin(root, relative):
    return {"path": str(relative), "sha256": digest(read(root / relative))}


def pinned_read(root, relative, expected):
    raw = read(root / relative)
    require(digest(raw) == expected, f"Retained input changed: {relative}")
    return raw


def select(raw, ordinal):
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    matches = [row for row in rows if row.get("canary_ordinal") == ordinal]
    require(len(matches) == 1, f"Expected one exact ordinal: {ordinal}")
    return matches[0]


def subset(public, private):
    if isinstance(public, dict):
        return isinstance(private, dict) and all(
            key in private and subset(value, private[key]) for key, value in public.items())
    if isinstance(public, list):
        return isinstance(private, list) and len(public) == len(private) and all(
            subset(a, b) for a, b in zip(public, private, strict=True))
    return type(public) is type(private) and public == private


def selected_case(root, archive, cohort, ordinal, rationale):
    public_path, expected = PUBLIC[cohort]
    public_raw = pinned_read(root, public_path, expected)
    occurrence = select(public_raw, ordinal)
    oid = occurrence["occurrence_id"]
    if cohort == "first":
        edge_path, records_path = FIRST_INPUTS
        edge_raw = pinned_read(archive, edge_path, FIRST_INPUTS[edge_path])
        records_raw = pinned_read(archive, records_path, FIRST_INPUTS[records_path])
        edge = select(edge_raw, ordinal)
        records = deepcopy(json.loads(records_raw)[oid])
        for wrapper in records:
            original = Path(wrapper["source_path"])
            require(".." not in original.parts, "Historical source path has traversal")
            relative = str(original.relative_to(RAW_ROOT))
            require("source_relative_path" not in wrapper,
                    "Historical source unexpectedly already has derived relative path")
            wrapper["source_relative_path"] = relative
        source = {"edge": edge, "records": records}
        upstream = [pin(archive, path) for path in FIRST_INPUTS]
        derivation = {"kind": "selected-private-edge-and-source-map",
                      "edge_selector": f"canary_ordinal={ordinal}", "records_selector": oid,
                      "source_relative_path_rule": "source_path relative to historical_raw_root",
                      "historical_raw_root": str(RAW_ROOT),
                      "retained_fields": "all original wrapper fields and exact text unchanged"}
    else:
        path = f"phase2/source/packets/{ordinal:02d}.json"
        raw = read(archive / path)
        source = json.loads(raw)
        edge = source["edge"]
        upstream = [{"path": path, "sha256": digest(raw)}]
        derivation = {"kind": "retained-complete-source-packet", "selector": oid}
    require(edge["occurrence_id"] == oid, "Private occurrence differs from public selection")
    require(subset(occurrence, edge), "Public occurrence differs from retained private edge")
    for field in CLAIM_FIELDS:
        require(field in occurrence, f"Missing original assertion field: {field}")
    endpoints = {}
    for side in ("subject", "object"):
        key = "original_" + side + "_node"
        require(edge[key]["id"] == occurrence[side], "Retained endpoint identity differs")
        endpoints[side] = {"id": occurrence[side], "label": occurrence[side + "_label"],
                           "category": occurrence[side + "_category"],
                           "public_record_sha256": sha256_json(occurrence[key]),
                           "private_record_sha256": sha256_json(edge[key])}
    records = source["records"]
    require(records, "Selected source records are empty")
    for wrapper in records:
        require(digest(wrapper["text"].encode()) == wrapper["text_sha256"],
                "Retained source text hash differs")
    manifest = {
        "case_id": f"{cohort}-{ordinal:02d}", "cohort": cohort, "ordinal": ordinal,
        "occurrence_id": oid, "public_input": {"path": public_path, "sha256": expected},
        "public_selector": f"canary_ordinal={ordinal};occurrence_id={oid}",
        "original_assertion": {field: occurrence[field] for field in CLAIM_FIELDS},
        "endpoints": endpoints, "private_upstream_inputs": upstream,
        "private_derivation": derivation, "historical_selection_rationale": rationale,
        "source_record_bindings": [
            {key: wrapper[key] for key in ("source_relative_path", "locator", "text_sha256")}
            for wrapper in records],
    }
    return manifest, occurrence, source


def cohort_document(root, archive):
    cases = [selected_case(root, archive, *choice)[0] for choice in SELECTION]
    require(len({case["occurrence_id"] for case in cases}) == len(cases),
            "Calibration occurrences are not distinct")
    return {"profile": "edgemech-calibration-cohort/v1", "cohort_id": COHORT_ID,
            "canary_case_id": CANARY, "selection": "purposive retained-case preparation",
            "population": {"retained_occurrences": 100, "new_review_coverage": 0,
                           "unreviewed_sample_occurrences": 9900},
            "historical_labels_are_gold": False, "scientific_status": "unassessed",
            "cases": cases}


def write_new(path, raw):
    safe_path(path, exists=False)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    require(read(path) == raw, f"Persisted bytes differ: {path}")


def configuration(root):
    protocol = json.loads(read(root / PROTOCOL))
    require(protocol.get("profile") == "edgemech-calibration-protocol/v1"
            and protocol.get("cohort_id") == COHORT_ID
            and protocol.get("canary_case_id") == CANARY, "Protocol identity differs")
    for cohort in PUBLIC:
        require(protocol.get("selection", {}).get(cohort)
                == [ordinal for name, ordinal, _ in SELECTION if name == cohort],
                "Protocol selection differs from frozen case policy")
    return {"protocol": pin(root, PROTOCOL), "cohort": pin(root, COHORT),
            "code_inputs": [pin(root, path) for path in CODE_PATHS]}


def frozen_case(root, archive, case_id):
    frozen = json.loads(read(root / COHORT))
    require(frozen.get("profile") == "edgemech-calibration-cohort/v1"
            and frozen.get("cohort_id") == COHORT_ID
            and frozen.get("canary_case_id") == CANARY, "Frozen cohort identity differs")
    expected_ids = [f"{cohort}-{ordinal:02d}" for cohort, ordinal, _ in SELECTION]
    require([row["case_id"] for row in frozen["cases"]] == expected_ids,
            "Frozen selection differs from preregistered cases")
    require(case_id in expected_ids, "Case is outside the frozen calibration")
    index = expected_ids.index(case_id)
    selected = selected_case(root, archive, *SELECTION[index])
    require(frozen["cases"][index] == selected[0], "Frozen case or retained inputs changed")
    return selected


def ignored_private(root):
    safe_path(root / PRIVATE, exists=False)
    result = subprocess.run(["git", "check-ignore", "--no-index", "-q", str(PRIVATE / "probe")],
                            cwd=root, check=False)
    require(result.returncode == 0, "Private staging is not gitignored")
    tracked = subprocess.run(["git", "ls-files", "--", str(PRIVATE)], cwd=root,
                             capture_output=True, check=True)
    require(not tracked.stdout, "Private staging contains tracked files")


def private_directory(path, *, new=False):
    safe_path(path, exists=False)
    if new:
        path.mkdir(mode=0o700)
    elif not path.exists():
        path.mkdir(mode=0o700)
    require(path.is_dir() and stat.S_IMODE(path.stat().st_mode) == 0o700,
            f"Private directory must have mode 0700: {path}")


def check_case(root, archive, case_id):
    check_contracts()
    ignored_private(root)
    manifest, occurrence, source = frozen_case(root, archive, case_id)
    config = configuration(root)
    directory = root / PRIVATE / case_id
    safe_path(directory)
    require(stat.S_IMODE(directory.stat().st_mode) == 0o700, "Private case permissions differ")
    receipt = json.loads(read(directory / "receipt.json"))
    require(receipt.get("profile") == "edgemech-calibration-preparation/v1"
            and receipt.get("case_id") == case_id
            and receipt.get("occurrence_id") == manifest["occurrence_id"]
            and receipt.get("cohort_id") == COHORT_ID, "Receipt identity differs")
    require(receipt["configuration"] == config, "Canary/configuration changed; new run required")
    require(receipt["private_upstream_inputs"] == manifest["private_upstream_inputs"]
            and receipt["private_derivation"] == manifest["private_derivation"],
            "Receipt upstream derivation changed")
    expected_names = {"occurrence.json", "source.json", "packet.json"}
    require(set(receipt["artifacts"]) == expected_names, "Receipt artifact inventory differs")
    for name in expected_names:
        require(receipt["artifacts"][name] == pin(root, PRIVATE / case_id / name),
                f"Prepared artifact changed: {name}")
        require(stat.S_IMODE((directory / name).stat().st_mode) == 0o600,
                "Private artifact permissions differ")
    require(read(directory / "occurrence.json") == encoded(occurrence),
            "Prepared occurrence differs from frozen projection")
    require(read(directory / "source.json") == encoded(source),
            "Prepared source differs from retained derivation")
    packet = json.loads(read(directory / "packet.json"))
    expected_packet = build_packet(
        occurrence, source,
        occurrence_input=pin(root, PRIVATE / case_id / "occurrence.json"),
        source_input=pin(root, PRIVATE / case_id / "source.json"), root=root)
    require(packet == expected_packet, "Packet differs from frozen case-local inputs")
    result = validate_packet(packet, root=root)
    require(receipt["validation"] == result, "Receipt validation differs")
    require(receipt.get("scientific_status") == "unassessed"
            and receipt.get("kg_admissions") == 0
            and receipt.get("native_capability_enabled") is False, "Preparation claimed promotion")
    if case_id == CANARY:
        require(receipt.get("canary_receipt") is None, "Canary receipt cannot depend on another")
    else:
        check_case(root, archive, CANARY)
        require(receipt.get("canary_receipt") == pin(root, PRIVATE / CANARY / "receipt.json"),
                "Verified canary receipt changed")
    return receipt


def prepare(root, archive, case_id):
    ignored_private(root)
    manifest, occurrence, source = frozen_case(root, archive, case_id)
    config = configuration(root)
    canary_pin = None
    if case_id != CANARY:
        check_case(root, archive, CANARY)
        canary_pin = pin(root, PRIVATE / CANARY / "receipt.json")
    check_contracts()
    if not (root / ".temp").exists():
        private_directory(root / ".temp")
    private_directory(root / PRIVATE)
    directory = root / PRIVATE / case_id
    private_directory(directory, new=True)
    write_new(directory / "occurrence.json", encoded(occurrence))
    write_new(directory / "source.json", encoded(source))
    packet = build_packet(occurrence, source,
                          occurrence_input=pin(root, PRIVATE / case_id / "occurrence.json"),
                          source_input=pin(root, PRIVATE / case_id / "source.json"), root=root)
    write_new(directory / "packet.json", encoded(packet))
    result = validate_packet(json.loads(read(directory / "packet.json")), root=root)
    require(configuration(root) == config, "Configuration changed during preparation")
    require(frozen_case(root, archive, case_id)[0] == manifest,
            "Retained input changed during preparation")
    receipt = {"profile": "edgemech-calibration-preparation/v1", "cohort_id": COHORT_ID,
               "case_id": case_id, "occurrence_id": manifest["occurrence_id"],
               "prepared_at": datetime.now(timezone.utc).isoformat(),
               "configuration": config, "private_upstream_inputs": manifest["private_upstream_inputs"],
               "private_derivation": manifest["private_derivation"], "canary_receipt": canary_pin,
               "artifacts": {name: pin(root, PRIVATE / case_id / name)
                             for name in ("occurrence.json", "source.json", "packet.json")},
               "validation": result, "scientific_status": "unassessed", "kg_admissions": 0,
               "native_capability_enabled": False}
    write_new(directory / "receipt.json", encoded(receipt))
    return check_case(root, archive, case_id)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--freeze", action="store_true")
    group.add_argument("--plan", action="store_true")
    group.add_argument("--prepare", metavar="CASE")
    group.add_argument("--check", metavar="CASE")
    parser.add_argument("--archive-root", type=Path, default=ARCHIVE)
    args = parser.parse_args()
    root, archive = safe_path(ROOT), safe_path(args.archive_root)
    if args.freeze:
        document = cohort_document(root, archive)
        safe_path(root / BASE, exists=False).mkdir(parents=True, exist_ok=True)
        write_new(root / COHORT, encoded(document))
        output = {"cohort": pin(root, COHORT), "cases": len(document["cases"]),
                  "scientific_status": "unassessed"}
    elif args.plan:
        ignored_private(root)
        config = configuration(root)
        cases = [f"{cohort}-{ordinal:02d}" for cohort, ordinal, _ in SELECTION]
        for case_id in cases:
            frozen_case(root, archive, case_id)
        output = {"configuration": config, "case_ids": cases, "first_live_case": CANARY,
                  "network_calls": 0, "scientific_assessments": 0,
                  "writes": 0, "kg_admissions": 0}
    elif args.prepare:
        output = prepare(root, archive, args.prepare)
    else:
        output = check_case(root, archive, args.check)
    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()
