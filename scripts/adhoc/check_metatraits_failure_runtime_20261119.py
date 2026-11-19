"""Stdlib smoke check for MetaTraits failure persistence; issues #221/#222, 2026-11-19.

Input: --output, a new private directory beneath this checkout's .temp directory.
Output: retained synthetic attempts, failure diagnostics and a reread result.json.
Uses synthetic runtime/owner files and mocked inspection, without network calls,
credential inspection, real owner imports, owner data changes or scientific review.
Run with the actual owner Python to check compatibility as well as error handling.
"""
from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
HELPER = Path(__file__).with_name("replay_metatraits_discrete_20261119.py")
SPEC = importlib.util.spec_from_file_location("metatraits_failure_smoke_replay", HELPER)
replay = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(replay)
SCENARIOS = ("removed_runtime", "removed_owner", "existing_failure", "denied_failure")


def private_file(path, raw):
    if not path.parent.exists():
        replay.create_private_dir(path.parent)
    replay.save_private(path, raw)


def check_case(output, scenario):
    directory = output / scenario
    replay.create_private_dir(directory)
    kg, original, attempt = (directory / name for name in ("owner", "original", "attempt"))
    case = replay.retained_case("first43")
    for name in case["code"] + tuple(case["input_pins"]):
        private_file(kg / name, ("Synthetic owner inventory: " + name + "\n").encode())
    for name in case["packet_pins"]:
        private_file(original / name, b"Synthetic original packet\n")
    executable = directory / "synthetic-runtime" / "python"
    helper = directory / "synthetic-helper.py"
    private_file(executable, b"Synthetic executable inventory member\n")
    private_file(helper, b"# Synthetic helper source\n")
    owner_file = kg / case["code"][0]
    original_error = ValueError("Synthetic primary inspection failure: " + scenario)
    prior_failure = b'{"reserved": "existing failure; never overwrite"}\n'
    stderr = io.StringIO()
    actual_save_json = replay.save_json
    actual_runtime_identity = replay.runtime_identity
    runtime_observations = []

    def inspect(*_):
        if scenario == "removed_runtime":
            executable.unlink()
        elif scenario == "removed_owner":
            owner_file.unlink()
        elif scenario == "existing_failure":
            replay.save_private(attempt / "failure.json", prior_failure)
        raise original_error

    def save_json(path, value):
        if scenario == "denied_failure" and path == attempt / "failure.json":
            raise PermissionError("Synthetic failure-path permission denial")
        return actual_save_json(path, value)

    def runtime_identity():
        try:
            result = actual_runtime_identity()
        except Exception as error:
            runtime_observations.append({"error_type": type(error).__name__, "error": str(error)})
            raise
        runtime_observations.append({"status": "inspected-synthetic-runtime"})
        return result

    caught = None
    with (patch.object(replay.sys, "prefix", str(executable.parent)),
          patch.object(replay.sys, "executable", str(executable)),
          patch.object(replay, "__file__", str(helper)),
          patch.object(replay, "inspect_inputs", inspect),
          patch.object(replay, "runtime_identity", runtime_identity),
          patch.object(replay, "save_json", save_json),
          contextlib.redirect_stderr(stderr)):
        try:
            replay.run("plan", kg, original, attempt)
        except Exception as error:
            caught = error
    replay.require(caught is original_error, "Primary exception object was replaced or swallowed")
    replay.require(runtime_observations[0] == {"status": "inspected-synthetic-runtime"},
                   "Initial synthetic runtime inspection did not succeed")
    replay.require(not (attempt / "receipt.json").exists(), "Failure was reported as success")
    failure_path = attempt / "failure.json"
    result = {"scenario": scenario, "status": "passed", "original_exception_preserved": True,
              "error_type": type(caught).__name__, "error": str(caught),
              "runtime_observations": runtime_observations,
              "permission_denial_injected": scenario == "denied_failure"}
    if scenario in ("removed_runtime", "removed_owner"):
        failure = json.loads(failure_path.read_bytes())
        replay.require(failure["error_type"] == "ValueError" and
                       failure["error"] == str(original_error), "Wrong primary failure persisted")
        identity = "runtime" if scenario == "removed_runtime" else "owner"
        replay.require(failure[f"{identity}_identity_before"] is not None,
                       "Initial complete snapshot missing")
        replay.require(failure[f"{identity}_identity_after"] is None and
                       failure[f"{identity}_identity_unchanged"] is None,
                       "Unavailable after-state reported as known or unchanged")
        replay.require(failure["diagnostic_errors"][f"{identity}_identity_after"]["error_type"] ==
                       "FileNotFoundError", "Missing after-state error diagnostic")
        result["failure_record_pin"] = replay.pin(failure_path)
        replay.require(result["failure_record_pin"]["bytes"] > 0 and
                       result["failure_record_pin"]["mode"] == "0o600",
                       "Failure record is empty or not private")
    else:
        expected_error = "FileExistsError" if scenario == "existing_failure" else "PermissionError"
        replay.require("Failure record could not be persisted: " + expected_error in stderr.getvalue(),
                       "Failure persistence diagnostic missing from stderr")
        if scenario == "existing_failure":
            replay.require(failure_path.read_bytes() == prior_failure, "Existing failure overwritten")
            result["preserved_existing_failure_pin"] = replay.pin(failure_path)
        else:
            replay.require(not failure_path.exists(), "Injected permission denial wrote a failure")
            result["failure_record_unavailable"] = True
    result["stderr_pin"] = replay.save_private(directory / "stderr.log", stderr.getvalue().encode())
    replay.save_json(directory / "check.json", result)
    return result


def check(output):
    output = output.resolve()
    replay.require(output.is_relative_to(ROOT / ".temp"), "Smoke output must be beneath checkout .temp")
    replay.create_private_dir(output)
    runtime = {"executable": sys.executable, "version": sys.version,
               "exception_notes_supported": callable(getattr(ValueError(), "add_note", None))}
    result = {"schema": "edgemech.metatraits-failure-runtime-smoke/v1", "status": "passed",
              "runtime": runtime, "invocation": sys.argv,
              "helper_pin": replay.pin(HELPER), "smoke_helper_pin": replay.pin(Path(__file__)),
              "limits": ["Synthetic failure-path checks only; no owner emission or scientific review.",
                         "Permission denial is injected; existing failure-path collision is real.",
                         "Runtime inventories cover only synthetic files, not the active environment."]}
    old_cache = os.environ.get("PYSTOW_HOME")
    try:
        result["checks"] = [check_case(output, scenario) for scenario in SCENARIOS]
    except Exception as error:
        replay.save_json(output / "smoke-failure.json", {
            "error_type": type(error).__name__, "error": str(error), "runtime": runtime})
        raise
    finally:
        if old_cache is None:
            os.environ.pop("PYSTOW_HOME", None)
        else:
            os.environ["PYSTOW_HOME"] = old_cache
    pin = replay.save_json(output / "result.json", result)
    replay.require(json.loads((output / "result.json").read_bytes()) == result,
                   "Persisted smoke result differs")
    return {"status": "passed", "output": str(output), "result_pin": pin,
            "checks": len(result["checks"]), "runtime": runtime}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(check(args.output), sort_keys=True))


if __name__ == "__main__":
    main()
