#!/usr/bin/env python3
"""Read exact-head CI readiness for EdgeMech milestones #766/#767; 2026-11-07.

Inputs: PR head pins, a hash-pinned expected-check inventory, GitHub read access.
Output: a new JSON audit receipt; no PR, issue, branch or review is mutated.
This records readiness at the checked time, never permission to merge.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

PIN = re.compile(r"(?P<repo>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)#(?P<number>[1-9][0-9]*)=(?P<head>[0-9a-f]{40})")
FIELDS = "number,url,headRefOid,isDraft,state,mergeStateStatus,statusCheckRollup"


def load_expected(path: Path, digest: str) -> dict:
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError("Expected-check inventory differs from pinned digest")
    data = json.loads(raw)
    if data.get("format") != "edgemech-pr-check-inventory/v1" or not isinstance(data.get("checks"), dict):
        raise ValueError("Invalid expected-check inventory")
    for identity, checks in data["checks"].items():
        if (not isinstance(identity, str) or PIN.fullmatch(identity + "=" + "0" * 40) is None
                or not isinstance(checks, list) or not checks
                or any(not isinstance(name, str) or not name for name in checks)
                or len(set(checks)) != len(checks)):
            raise ValueError("Expected checks must be explicit, nonempty and unique for each PR")
    return data["checks"]


def inspect(pin: str, expected: dict) -> dict:
    match = PIN.fullmatch(pin)
    if match is None:
        raise ValueError(f"Invalid PR pin: {pin}")
    repo, number, head = match.group("repo", "number", "head")
    required_checks = expected[f"{repo}#{number}"]
    checked = datetime.now(UTC).isoformat()
    result = subprocess.run(
        ["gh", "pr", "view", number, "--repo", repo, "--json", FIELDS],
        check=True, capture_output=True, text=True, timeout=60,
    )
    data = json.loads(result.stdout)
    failures = []
    expected_url = f"https://github.com/{repo}/pull/{number}"
    for valid, reason in (
        (data["url"] == expected_url and data["number"] == int(number), "PR identity differs"),
        (data["headRefOid"] == head, "head differs from reviewed pin"),
        (data["state"] == "OPEN", "PR is not open"),
        (data["isDraft"] is False, "PR is draft"),
        (data["mergeStateStatus"] == "CLEAN", "merge state is not clean"),
        (bool(data["statusCheckRollup"]), "no CI checks are reported"),
    ):
        if not valid:
            failures.append(reason)
    checks, observed_names = [], []
    for check in data["statusCheckRollup"]:
        if check.get("__typename") == "CheckRun":
            observed_names.append(check.get("name"))
            passed = check.get("status") == "COMPLETED" and check.get("conclusion") == "SUCCESS"
            checks.append({key: check.get(key) for key in
                           ("name", "status", "conclusion", "detailsUrl", "completedAt")})
        elif check.get("__typename") == "StatusContext":
            observed_names.append(check.get("context"))
            passed = check.get("state") == "SUCCESS"
            checks.append({key: check.get(key) for key in ("context", "state", "targetUrl")})
        else:
            passed = False
            checks.append({"unrecognized_check_type": check.get("__typename")})
        if not passed:
            failures.append(f"Check not successful: {check.get('name', check.get('context', 'unknown'))}")
    if set(observed_names) != set(required_checks) or len(observed_names) != len(required_checks):
        failures.append("Reported check inventory differs from reviewed expected checks")
    return {
        "url": data["url"], "expected_head": head, "observed_head": data["headRefOid"],
        "checked_at": checked, "state": data["state"], "is_draft": data["isDraft"],
        "merge_state": data["mergeStateStatus"], "checks": checks,
        "expected_checks": sorted(required_checks),
        "ready": not failures, "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pr", action="append", required=True)
    parser.add_argument("--expected-checks", type=Path, required=True)
    parser.add_argument("--expected-checks-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if any(PIN.fullmatch(pin) is None for pin in args.pr):
        parser.error("Every --pr must be REPOSITORY#NUMBER=40_HEX_HEAD")
    if len(set(args.pr)) != len(args.pr):
        parser.error("Duplicate PR pins are not allowed")
    if args.output.exists():
        parser.error("Output already exists; choose a new receipt path")
    expected = load_expected(args.expected_checks, args.expected_checks_sha256)
    if any(pin.split("=", 1)[0] not in expected for pin in args.pr):
        parser.error("Every requested PR requires a pinned expected-check inventory")
    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(lambda pin: inspect(pin, expected), args.pr))
    receipt = {
        "format": "edgemech-pr-readiness-audit/v1",
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "expected_checks_sha256": args.expected_checks_sha256,
        "completed_at": datetime.now(UTC).isoformat(),
        "merge_permission": False,
        "all_ready": all(record["ready"] for record in records),
        "prs": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as handle:
        json.dump(receipt, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    print(json.dumps({"receipt": str(args.output), "all_ready": receipt["all_ready"],
                      "prs": len(records)}, sort_keys=True))
    return 0 if receipt["all_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
