#!/usr/bin/env python3
"""Record synthetic timing-wrapper controls without repeating census verification.

Purpose: execute unit 2 of the independently reviewed census-terminal plan.
Inputs: explicit SHA256-pinned retained audit, exclusive private results path.
Outputs: fixed true/time-true stdout/stderr, observed statuses and private receipt.
UTC date: 2026-11-26. Issues: #228 provenance, #224 full-population accounting.
Provenance: new bounded producer; reuses existing retained metadata audit instead
of replaying its source/census reads. Original failed terminal and unknown child
exit are immutable facts. This helper cannot run a census, restore source, infer
scientific approval, freeze A/B, or modify application permissions.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from edgemech.census import _json, _read_handle

ROOT = Path(__file__).resolve().parents[2]
MAX_BYTES = 256 * 1024
COMMANDS = (
    ("direct_true", ("/usr/bin/true",)),
    ("timed_true", ("/usr/bin/time", "-l", "/usr/bin/true")),
)
WARNING = b"time: sysctl kern.clockrate: Operation not permitted"
OUTPUT_SPEC = importlib.util.spec_from_file_location(
    "restart_private_attempt", Path(__file__).with_name("restart_private_attempt_20261126.py"))
private_output = importlib.util.module_from_spec(OUTPUT_SPEC)
OUTPUT_SPEC.loader.exec_module(private_output)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    with _read_handle(path) as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("retained audit exceeds the bounded metadata limit")
    return raw


def audit_binding(path, expected):
    raw = read(path)
    if digest(raw) != expected:
        raise ValueError("retained audit pin mismatch")
    census = _json(raw)["census"]
    terminal = census["terminal"]["actual_retained_item"]
    if (type(census["actual_outer_exit_code"]) is not int
            or census["actual_outer_exit_code"] != 1
            or terminal["status"] != "failed" or type(terminal["exit_code"]) is not int
            or terminal["exit_code"] != 1 or census["terminal_success_claimed"] is not False
            or census["native_child_exit_status_separately_observed"] is not None
            or census["result_json_equals_manifest"] is not True):
        raise ValueError("audit does not retain the expected failed/unknown distinction")
    for key in ("independent_scientific_reviews", "kg_occurrences_approved"):
        if type(census[key]) is not int or census[key] != 0:
            raise ValueError("audit cannot qualify scientific approvals")
    return {
        "audit_sha256": digest(raw), "original_outer_exit_code": 1,
        "original_child_exit_code": None, "original_status": "FAILED",
        "complete_result_equals_pinned_manifest_in_reused_audit": True,
        "metadata_audit_replayed": False,
    }


def save(path, raw, *, output):
    return output.save(path.name, raw)


def probe(audit, expected, results):
    # Validate all non-mutating inputs first; supplied audit commands are never used.
    binding = audit_binding(audit, expected)
    with private_output.private_attempt(results, ROOT / ".temp") as output:
        return _probe(binding, results, output)


def _probe(binding, results, output):
    outcomes = []
    for name, argv in COMMANDS:
        error = None
        try:
            completed = subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True,
                                       timeout=15, check=False)
            code, stdout, stderr = completed.returncode, completed.stdout, completed.stderr
        except subprocess.TimeoutExpired as exc:
            code, stdout, stderr, error = None, exc.stdout or b"", exc.stderr or b"", "timeout"
        except OSError as exc:
            code, stdout, stderr, error = None, b"", b"", type(exc).__name__
        outcomes.append({
            "name": name, "argv": list(argv), "exit_code": code, "error": error,
            "stdout": save(results / f"{name}.stdout", stdout, output=output),
            "stderr": save(results / f"{name}.stderr", stderr, output=output),
            "timing_permission_warning": WARNING in stderr,
        })
    direct, timed = outcomes
    if direct["exit_code"] != 0 or timed["exit_code"] is None or timed["error"] is not None:
        disposition = "SYNTHETIC_CONTROL_FAILED_OR_TIMED_OUT"
    elif timed["exit_code"] == 1 and timed["timing_permission_warning"]:
        disposition = "TIMING_WRAPPER_WARNING_REPRODUCED_WITH_SYNTHETIC_TRUE"
    else:
        disposition = "CURRENT_WRAPPER_OUTCOME_DIFFERS_OR_IS_UNRESOLVED"
    report = {
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "helper_sha256": digest(read(Path(__file__))), **binding,
        "output_helper_sha256": digest(read(Path(private_output.__file__))),
        "outcomes": outcomes, "disposition": disposition,
        "original_child_exit_inferred": False,
        "original_full_replay_gate": "PENDING_INDEPENDENT_EVIDENCE_DISPOSITION",
        "full_census_reverified": False, "source_restored": False,
        "scientific_review_coverage": 0, "full_target_frozen": False,
        "queue_A_count": None, "queue_B_count": None,
    }
    receipt = save(results / "receipt.json",
                   (json.dumps(report, indent=2, allow_nan=False) + "\n").encode(), output=output)
    return {"receipt": receipt, "disposition": disposition, "original_outer_exit_code": 1,
            "original_child_exit_code": None, "full_census_reverified": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--audit-sha256", required=True)
    parser.add_argument("--results", type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    result = probe(args.audit, args.audit_sha256, args.results)
    print(json.dumps(result, sort_keys=True))
    return 1 if result["disposition"] == "SYNTHETIC_CONTROL_FAILED_OR_TIMED_OUT" else 0


if __name__ == "__main__":
    raise SystemExit(main())
