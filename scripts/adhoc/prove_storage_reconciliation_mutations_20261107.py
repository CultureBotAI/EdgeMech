#!/usr/bin/env python3
"""Prove EdgeMech #14 / CLAW #951 regressions detect removed checks, 2026-11-07.

Inputs: current storage/report sources and tests. Outputs: isolated mutant files,
fresh-process pytest logs and hash-bound receipt in a new workspace directory.
Production files and existing outputs are never changed.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STORAGE = ROOT / "src/edgemech/storage/__init__.py"
REPORT = ROOT / "scripts/adhoc/summarize_validation_20261107.py"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.absolute()
    if ".." in output.parts or not output.is_relative_to(ROOT / "workspace"):
        raise ValueError("Use a new literal workspace directory")
    output.mkdir(parents=False, exist_ok=False)
    originals = {path: path.read_bytes() for path in (STORAGE, REPORT)}
    cases = []
    old = "        if expected[name] != actual[name]:"
    source = originals[STORAGE].decode()
    if source.count(old) != 1:
        raise ValueError("Storage guard is no longer exact")
    mutant = output / "storage_without_source_comparison.py"
    mutant.write_text(source.replace(old, "        if False:"))
    text = (ROOT / "tests/test_storage.py").read_text()
    loader = (
        "import importlib.util as _u\nimport sys as _s\nimport edgemech as _e\n"
        f"_spec = _u.spec_from_file_location('edgemech.storage', {str(mutant)!r}, "
        f"submodule_search_locations=[{str(STORAGE.parent)!r}])\n"
        "_module = _u.module_from_spec(_spec)\n_s.modules[_spec.name] = _module\n"
        "_spec.loader.exec_module(_module)\n_e.storage = _module\n"
        "from edgemech import storage"
    )
    test = output / "test_storage_mutant.py"
    test.write_text(text.replace("from edgemech import storage", loader, 1))
    cases.append(("source_output", test, "test_internally_valid_writer_header_change_cannot_publish"))

    source = originals[REPORT].decode()
    input_begin = source.index("    if (not isinstance(before, dict)")
    input_end = source.index('        raise ValueError("Migration input hashes', input_begin)
    report_cases = [
        ("report_proof", "    check_source_reconciliation(record, manifest)\n", "",
         "test_missing_source_output_proof_is_rejected"),
        ("manifest_input", '        or manifest.get("source", {}).get("sqlite_sha256") != SQLITE_SHA256\n',
         "", "test_rehashed_different_source_manifest_cannot_use_original_outer_pin"),
        ("migration_inputs", source[input_begin:input_end], "    if False:\n",
         "test_rehashed_migration_input_substitution_is_rejected[different_ledger]"),
    ]
    for name, old, new, node in report_cases:
        if source.count(old) != 1:
            raise ValueError(f"Report guard is no longer exact: {name}")
        mutant = output / (name + "_without_guard.py")
        mutant.write_text(source.replace(old, new))
        text = (ROOT / "tests/test_validation_report.py").read_text()
        loader = 'REPORT = runpy.run_path(str(Path(__file__).parents[1] / "scripts/adhoc/summarize_validation_20261107.py"))'
        if loader not in text:
            raise ValueError("Report test loader changed")
        test = output / ("test_" + name + "_mutant.py")
        test.write_text(text.replace(loader, f"REPORT = runpy.run_path({str(mutant)!r})"))
        cases.append((name, test, node))

    results = []
    for name, test, node in cases:
        environment = {**os.environ, "PYTHONPATH": str(ROOT / "src"),
                       "PYTHONPYCACHEPREFIX": str(output / (name + "-bytecode"))}
        result = subprocess.run([sys.executable, "-m", "pytest", "-q", f"{test}::{node}"],
                                cwd=ROOT, env=environment, capture_output=True, text=True,
                                timeout=180)
        log = result.stdout + result.stderr
        (output / (name + ".log")).write_text(log)
        if result.returncode != 1 or "DID NOT RAISE" not in log:
            raise ValueError(f"Mutation did not fail at its intended regression: {name}")
        results.append({"guard": name, "regression_failed_as_expected": True, "exit_code": 1})
    if any(path.read_bytes() != raw for path, raw in originals.items()):
        raise ValueError("Production sources changed during mutation proof")
    receipt = {"format": "edgemech-source-reconciliation-mutation/v1", "mutations": results,
               "production_sources_unchanged": True,
               "source_sha256": {str(path.relative_to(ROOT)): hashlib.sha256(raw).hexdigest()
                                 for path, raw in originals.items()}}
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
