#!/usr/bin/env python3
"""Prove the public allowlist distinction with isolated fresh-process mutations.

Purpose: issue238 privacy negative control; issue228 source/result provenance.
Inputs: current tracked projection, its dependencies and synthetic privacy tests.
Outputs: exclusive synthetic copies, raw pytest logs/JUnit, hashes and a result
under durable .temp/fulltext staging. UTC date: 2026-11-26.
This is a new offline test producer, not a historical execution or live canary.
Only copied sources are mutated. Independent source/publication review is pending.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from preparation_receipt_20261126 import ROOT, checked_path, directory, read_regular

STAGING = ROOT / ".temp/fulltext/preparation-repairs-236-238"
PROJECTION = "scripts/adhoc/preparation_public_projection_20261126.py"
TEST = "tests/test_preparation_public_projection_20261126.py"
INPUTS = (PROJECTION, TEST, "scripts/adhoc/preparation_receipt_20261126.py",
          "scripts/adhoc/preparation_readback_20261126.py")
MUTATIONS = {
    "root_passthrough": (b"    return output\n", b"    output.update(data)\n    return output\n"),
    "nested_snapshot_passthrough": (
        b'    return {"sha256": digest(value["sha256"]), "bytes": integer(value["bytes"])}\n',
        b"    return dict(value)\n"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, raw):
    path = checked_path(path, "file", base=STAGING, absent=True)
    with directory(path.parent, create=True) as parent:
        fd = os.open(path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                     0o600, dir_fd=parent)
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
    if read_regular(path) != raw:
        raise ValueError("Mutation evidence readback mismatch")
    return {"path": str(path.relative_to(ROOT)), "bytes": len(raw), "sha256": sha(raw)}


def mutate(raw, name):
    old, new = MUTATIONS[name]
    if raw.count(old) != 1:
        raise ValueError("Mutation anchor must match exactly once")
    return raw.replace(old, new)


def execute(output):
    output = checked_path(output, "directory", base=STAGING, absent=True)
    originals = {name: read_regular(ROOT / name) for name in INPUTS}
    # Check every anchor before creating any execution/output directory.
    for name in MUTATIONS:
        mutate(originals[PROJECTION], name)
    with directory(output.parent, create=True) as parent:
        os.mkdir(output.name, 0o700, dir_fd=parent)
    runs = []
    for name in ("positive", *MUTATIONS):
        case = output / name
        checkout = case / "synthetic-checkout"
        source_pins = []
        for relative, raw in originals.items():
            if relative == PROJECTION and name != "positive":
                raw = mutate(raw, name)
            source_pins.append(save(checkout / relative, raw))
        env = {"PATH": os.defpath, "PYTHONPYCACHEPREFIX": str(case / "pycache"),
               "TMPDIR": str(case / "tmp"), "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}
        with directory(case / "tmp", create=True):
            pass
        command = [sys.executable, "-m", "pytest", "-q", "--tb=short", TEST,
                   "--basetemp=" + str(case / "fixtures"),
                   "--junitxml=" + str(case / "junit.xml"),
                   "-o", "cache_dir=" + str(case / "pytest-cache")]
        save(case / "command.json", (json.dumps(command, indent=2) + "\n").encode())
        result = subprocess.run(command, cwd=checkout, env=env, capture_output=True,
                                timeout=120, check=False)
        stdout = save(case / "stdout", result.stdout)
        stderr = save(case / "stderr", result.stderr)
        save(case / "exit-code", f"{result.returncode}\n".encode())
        xml = read_regular(case / "junit.xml")
        cases = ET.fromstring(xml).findall(".//testcase")
        failed = [node.attrib["name"] for node in cases if node.find("failure") is not None]
        errors = [node.attrib["name"] for node in cases if node.find("error") is not None]
        skipped = [node.attrib["name"] for node in cases if node.find("skipped") is not None]
        required = {f"test_allowlist_omits_all_operational_and_unknown_bindings[{kind}]"
                    for kind in (("commands", "library", "canonical", "summary")
                                 if name == "root_passthrough"
                                 else ("commands", "library", "canonical"))}
        required.add("test_command_projection_exact_allowlist")
        # Pytest's assertion rewriting can omit the literal 'AssertionError'.
        # Require the actual failed privacy assertion, not a generic exception.
        assertions = all(("assert MARKER not in text" if node.attrib["name"].startswith(
            "test_allowlist_omits_") else "assert set(result") in (node.find("failure").text or "")
                         for node in cases if node.attrib["name"] in required
                         and node.find("failure") is not None)
        meaningful = (len(cases) == 20 and not errors and not skipped and
                      ((name == "positive" and result.returncode == 0 and not failed)
                       or (name != "positive" and result.returncode == 1
                           and required.issubset(failed) and assertions)))
        runs.append({"name": name, "exit_code": result.returncode, "tests": len(cases),
                     "failures": failed, "errors": errors, "skipped": skipped,
                     "meaningful": meaningful, "sources": source_pins,
                     "stdout": stdout, "stderr": stderr, "junit_sha256": sha(xml)})
    unchanged = all(read_regular(ROOT / name) == raw for name, raw in originals.items())
    result = {"classification": "SYNTHETIC_OFFLINE_PRIVACY_MUTATION_NOT_CANARY",
              "producer_sha256": sha(read_regular(Path(__file__))),
              "original_source_sha256": {name: sha(raw) for name, raw in originals.items()},
              "original_sources_unchanged": unchanged, "runs": runs,
              "passed": unchanged and all(run["meaningful"] for run in runs),
              "new_provider_requests": 0, "new_canonical_saves": 0,
              "scientific_review_coverage": 0, "A_count": None, "B_count": None}
    save(output / "result.json", (json.dumps(result, indent=2) + "\n").encode())
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    result = execute(args.output)
    print(json.dumps({"passed": result["passed"], "runs": [
        {"name": run["name"], "exit_code": run["exit_code"],
         "failures": len(run["failures"]), "meaningful": run["meaningful"]}
        for run in result["runs"]]}))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
