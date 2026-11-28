#!/usr/bin/env python3
"""Prepare allowlisted public digests/statuses, never publish operational bindings.

Purpose: issue238 privacy repair, issue228 preserved-result provenance.
Inputs: one preserved engineering JSON artifact and an explicit projection kind.
Outputs: a NEW proposal file in the private repair tree; no automatic publication.
UTC date: 2026-11-26. Original receipts and canonical pair remain immutable.
This projection is not a RecordReview schema, scientific proof or history erasure.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path

from preparation_readback_20261126 import strict_json
from preparation_receipt_20261126 import ROOT, checked_path, directory, read_regular

PROPOSAL = ROOT / ".temp/preparation-repairs-236-238-20261126/public-proposal"


def integer(value, *, minimum=0, maximum=1_000_000_000):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError("Invalid bounded integer")
    return value


def boolean(value):
    if type(value) is not bool:
        raise ValueError("Invalid boolean status")
    return value


def digest(value, length=64):
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{" + str(length) + "}", value) is None:
        raise ValueError("Invalid digest")
    return value


def status(value):
    if type(value) is not str or value not in {"passed", "failed"}:
        raise ValueError("Invalid status")
    return value


def mapping(value):
    if not isinstance(value, dict):
        raise ValueError("Expected object")
    return value


def snapshot(value):
    value = mapping(value)
    return {"sha256": digest(value["sha256"]), "bytes": integer(value["bytes"])}


def exit_status(value):
    if value is not None:
        integer(value, minimum=-255, maximum=255)
    return {"exit_code": value, "status": "unavailable" if value is None
            else "passed" if value == 0 else "failed"}


def record_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    allow_nan=False).encode()).hexdigest()


def command_projection(value):
    value = mapping(value)
    return {"record_sha256": record_digest(value), **exit_status(value["exit_code"]),
            "helper_sha256": digest(mapping(value["helper"])["sha256"]),
            "stdout": snapshot(value["stdout"]), "stderr": snapshot(value["stderr"])}


def project(raw, kind):
    data = mapping(strict_json(raw))
    integer(data["scientific_review_coverage"], maximum=0)
    # Construct every public field explicitly. No dict expansion of source data,
    # recursive passthrough, exception text, argv, labels, timestamps or path fields.
    output = {"format": "preparation-public-digest/v1", "kind": kind,
              "source_artifact_sha256": hashlib.sha256(raw).hexdigest(),
              "scientific_review_coverage": 0}
    if kind == "commands":
        commands = data["commands"]
        if not isinstance(commands, list) or len(commands) > 1000:
            raise ValueError("Invalid command list")
        output["commands"] = [command_projection(item) for item in commands]
        output["command_count"] = len(commands)
    elif kind == "library":
        if data["provider"] != "valency":
            raise ValueError("Unexpected provider")
        output["provider"] = "valency"
        output["provider_request_count"] = integer(data["provider_request_count"], maximum=1)
        for field in ("identity_verified", "body_read", "tables_read", "figures_read",
                      "fulltext_ready", "native_scientific_proof_admitted"):
            output[field] = boolean(data[field])
        output["literal_replay"] = status(data["literal_replay"])
        for field in ("request", "response", "abstract"):
            output[field] = snapshot(data[field])
        output["quote_sha256"] = digest(data["quote_sha256"])
        output["quote_words"] = integer(data["quote_words"], maximum=25)
    elif kind == "canonical":
        output["canonical_read_review"] = status(data["canonical_read_review"])
        output["input_hash_replay"] = status(data["input_hash_replay"])
        contracts = mapping(data["contracts"])
        output["contracts"] = {"verified": boolean(contracts["verified"]),
                               "files": integer(contracts["files"], maximum=16),
                               "claw_commit": digest(contracts["claw_commit"], 40)}
        artifacts = data["artifacts"]
        if not isinstance(artifacts, list) or len(artifacts) != 2:
            raise ValueError("Expected two artifact digests")
        projected = {}
        for item in artifacts:
            item = mapping(item)
            path = item["path"]
            if not isinstance(path, str):
                raise ValueError("Invalid artifact identifier")
            key = {"review.yaml": "review_yaml", "review.md": "review_markdown"}.get(
                Path(path).name)
            if key is None or key in projected:
                raise ValueError("Invalid or duplicated canonical artifact")
            projected[key] = snapshot(item)
        output["artifacts"] = projected
    elif kind == "summary":
        if (data["scientific_review_coverage"] != 0 or data["occurrence"] is not None
                or data["A_B_attempt"] is not False
                or any(data[k] is not None for k in ("A_count", "B_count", "baseline_cutoff"))):
            raise ValueError("Unexpected scientific scope")
        integer(data["scientific_review_coverage"], maximum=0)
        output.update({"status": "bounded_preparation_executed_with_limits", "occurrence": None,
                       "A_B_attempt": False, "A_count": None, "B_count": None,
                       "baseline_cutoff": None})
        validation = mapping(data["validation"])
        output["validation"] = {
            "contracts": integer(validation["contracts"], maximum=16),
            "focused_passed": integer(mapping(validation["focused"])["passed"]),
            "full_suite": {k: integer(mapping(validation["full_suite"])[k])
                           for k in ("passed", "failed", "errors")},
            "full_suite_outcome": exit_status(validation["full_suite"]["exit_code"]),
            "ruff": exit_status(validation["ruff_exit"]),
            "package_build": exit_status(validation["package_build_exit"]),
        }
        readiness = mapping(data["readiness"])
        output["readiness"] = {k: boolean(readiness[k]) for k in (
            "shared_canonical_engineering", "actual_worker_metadata_abstract_access",
            "fulltext", "native_occurrence_production", "calibration")}
        output["publication_review"] = "pending"
    else:
        raise ValueError("Unsupported projection kind")
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=("commands", "library", "canonical", "summary"))
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    output = checked_path(args.output, "file", base=PROPOSAL, absent=True)
    raw = read_regular(args.source)
    data = (json.dumps(project(raw, args.kind), indent=2) + "\n").encode()
    with directory(output.parent) as parent:
        fd = os.open(output.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                     0o600, dir_fd=parent)
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    if read_regular(output) != data:
        raise ValueError("Projection readback mismatch")
    print(json.dumps({"projection_sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}))


if __name__ == "__main__":
    main()
