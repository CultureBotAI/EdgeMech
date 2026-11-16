#!/usr/bin/env python3
"""2026-11-16: preserve real M5 production units at the canonical KG output base.

The reviewed KG unit launcher supplies named input staging, pinned code/config,
private caches, one actual CLI source and raw side-effect inventory. This wrapper
changes only output placement to the task checkout's initially absent canonical
source directory, so BacDive's fixed upstream paths select the actual new output.
It captures every file in that source tree and checks pre-existing upstream trees
remain unchanged. No completion markers are invented, copied or relabeled.
Separate source units share the output base but own disjoint source directories.
Original M5 inputs and the earlier RO canary stages are read-only.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

SHARED_LAUNCHER = "scripts/adhoc/run_bactotraits_production_unit_20261116.py"
UPSTREAM = {"ontologies": (), "bacdive": ("ontologies",), "bactotraits": ("ontologies", "bacdive")}
GO_RECEIPT_SHA256 = "dd96bdb5d482e75458b545a658ddd4d1117e53e61f38d84b5f27cabc17d90001"
JAVA_PROOFS = {
    "java-runtime-supplement-r3.json": "b697bb006e0754712d28cd0a3bf47628b3f11cd24506ebeab51058d98a175ac1",
    "java-runtime-implementation-r3.json": "ec76081f31d0e639082cb3eb359f82f2c138fd31e8538f2c7282b4dfd14a1451",
}
ANCILLARY = (
    "kg_microbe/transform_utils/ontologies/xrefs",
    "kg_microbe/transform_utils/ontologies/trees",
    "kg_microbe/transform_utils/bacdive/tmp",
    "kg_microbe/transform_utils/bactotraits/tmp",
)


def load_launcher(root):
    """Import the separately reviewed helper without invoking a producer or changing KG code."""
    path = root / SHARED_LAUNCHER
    spec = importlib.util.spec_from_file_location("m5_kg_production_unit", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def inventory(directory, launcher):
    """Stream every member of one explicit owned subtree, including ignored and hidden files."""
    if not directory.exists():
        return {}
    return {
        str(path.relative_to(directory)): launcher.identity(launcher.safe_path(path))
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


def java_provenance(environment, launcher):
    """Preserve the full JVM version output, including any banner before the actual version."""
    command = shutil.which("java", path=environment.get("PATH"))
    launcher.require(command is not None, "Java is unavailable")
    result = subprocess.run(  # noqa: S603 -- PATH-selected Java with fixed read-only version arguments.
        [command, "-version"],
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    selected_home = environment.get("JAVA_HOME")
    if not selected_home and Path("/usr/libexec/java_home").is_file():
        home_result = subprocess.run(  # noqa: S603 -- fixed macOS JDK locator, read-only.
            ["/usr/libexec/java_home"],
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if home_result.returncode == 0:
            selected_home = home_result.stdout.strip()
    resolved = Path(command).resolve()
    actual = Path(selected_home) / "bin/java" if selected_home else resolved
    return {
        "command": [command, "-version"],
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "path": command,
        "resolved_path": str(resolved),
        "launcher_identity": launcher.identity(resolved),
        "selected_java_home": selected_home,
        "selected_jdk_java_path": str(actual.resolve()) if actual.is_file() else None,
        "selected_jdk_java_identity": launcher.identity(actual) if actual.is_file() else None,
    }


def bind_prior_authorities(plan, args, launcher):
    """Require the actually rebuilt GO cache and inspected JDK, not just whichever bytes now exist."""
    pins = plan["implementation_and_policy_inputs"]
    receipt_path = (
        args.kg_root / "data/validation-bactotraits-130/production-ro-canary-r3/receipt.json"
    )
    receipt_identity = launcher.identity(receipt_path)
    launcher.require(
        receipt_identity["sha256"] == GO_RECEIPT_SHA256, "Reviewed RO/GO receipt changed"
    )
    pins[str(receipt_path)] = receipt_identity
    receipt = json.loads(receipt_path.read_text())
    go = {}
    for name in ("go.db", "go.db.toolchain.json"):
        path = args.kg_root / "data/raw" / name
        expected = receipt["task_raw_after"][name]
        launcher.require(launcher.identity(path) == expected, f"Fresh r3 GO cache changed: {name}")
        pins[str(path)] = expected
        go[name] = {"path": str(path), **expected}
    plan["retained_go_cache"] = {
        "receipt": {"path": str(receipt_path), **receipt_identity},
        "members": go,
    }
    proofs = {}
    for name, expected_sha in JAVA_PROOFS.items():
        path = args.output_root / name
        observed = launcher.identity(path)
        launcher.require(observed["sha256"] == expected_sha, "Reviewed Java supplement changed")
        pins[str(path)] = observed
        proofs[name] = {"path": str(path), **observed}
    implementation = json.loads(
        (args.output_root / "java-runtime-implementation-r3.json").read_text()
    )
    for role in ("actual_runtime_launcher", "actual_runtime_vm"):
        native = implementation[role]
        path = Path(native["path"])
        expected = {key: native[key] for key in ("bytes", "sha256")}
        launcher.require(
            str(path.resolve()) == native["resolved"] and launcher.identity(path) == expected,
            "Inspected Java implementation changed",
        )
        pins[str(path)] = expected
    actual_java = implementation["actual_runtime_launcher"]["resolved"]
    launcher.require(
        plan["java"]["selected_jdk_java_path"] == actual_java, "Different Java runtime selected"
    )
    # Freeze the actual JDK proved by -XshowSettings in the supplement, avoiding
    # any later macOS /Library/Java/Home selector change during the long unit.
    plan["environment"]["JAVA_HOME"] = str(Path(actual_java).parent.parent)
    plan["java_supplements"] = proofs


def prepare(args, launcher):
    """Pin this wrapper and canonical placement without opening any output for writing."""
    launcher.require(
        args.kg_root.resolve() == launcher.ROOT, "Selected KG checkout differs from helper root"
    )
    plan = launcher.prepare(args)
    for name in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "NUMEXPR_MAX_THREADS",
        "VECLIB_MAXIMUM_THREADS",
        "RAYON_NUM_THREADS",
        "BLIS_NUM_THREADS",
    ):
        plan["environment"][name] = "1"
    for name in ("ROBOT_JAVA_ARGS", "_JAVA_OPTIONS"):
        plan["environment"][name] += " -XX:ActiveProcessorCount=1"
    output = launcher.safe_path(args.kg_root / "data/transformed")
    source = launcher.safe_path(output / args.source)
    launcher.require(
        not source.exists(), f"Canonical source output already exists: {source}; preserve it"
    )
    prior = {}
    for name in UPSTREAM[args.source]:
        directory = output / name
        for member in ("source_finalization.json", "source_fingerprint.json"):
            launcher.require(
                (directory / member).is_file(),
                f"Completed upstream evidence missing: {directory / member}",
            )
        prior[name] = inventory(directory, launcher)
    plan["command"][plan["command"].index("-o") + 1] = str(output)
    plan["canonical_output_base"] = str(output)
    plan["canonical_source_directory"] = str(source)
    plan["upstream_before"] = prior
    plan["ancillary_before"] = {
        name: inventory(launcher.safe_path(args.kg_root / name), launcher) for name in ANCILLARY
    }
    fresh_ancillary = {
        "bacdive": (
            "bacdive.tsv",
            "bacdive_physiology_metabolism.tsv",
            "bacdive_name_tax_classification.tsv",
        ),
        "bactotraits": ("bactotraits_mapping.tsv", "bactotraits.tsv"),
    }
    for name in fresh_ancillary.get(args.source, ()):
        path = args.kg_root / "kg_microbe/transform_utils" / args.source / "tmp" / name
        launcher.require(not path.exists(), f"Existing ancillary output must be preserved: {path}")
    legacy = args.kg_root / "kg_microbe/transform_utils/bacdive/metabolite_mapping.json"
    plan["implementation_and_policy_inputs"][str(legacy)] = launcher.identity(legacy)
    if args.source == "bactotraits":
        launcher.require(
            args.bacdive_receipt is not None, "BactoTraits requires the fresh BacDive unit receipt"
        )
        previous = json.loads(args.bacdive_receipt.read_text())
        launcher.require(
            previous["returncode"] == 0 and previous["plan"]["source"] == "bacdive",
            "BacDive unit did not complete",
        )
        expected = previous["ancillary_after"]["kg_microbe/transform_utils/bacdive/tmp"][
            "bacdive.tsv"
        ]
        lookup = args.kg_root / "kg_microbe/transform_utils/bacdive/tmp/bacdive.tsv"
        launcher.require(
            launcher.identity(lookup) == expected,
            "Fresh BacDive lookup differs from its actual unit",
        )
        plan["implementation_and_policy_inputs"][str(lookup)] = expected
        plan["implementation_and_policy_inputs"][str(args.bacdive_receipt)] = launcher.identity(
            args.bacdive_receipt
        )
        plan["fresh_bacdive_lookup"] = {
            "path": str(lookup),
            **expected,
            "receipt": str(args.bacdive_receipt),
        }
    wrapper = Path(__file__).resolve()
    plan["implementation_and_policy_inputs"][str(wrapper)] = launcher.identity(wrapper)
    plan["wrapper"] = {"path": str(wrapper), **launcher.identity(wrapper)}
    output_root = launcher.safe_path(args.output_root)
    launcher.require(output_root.is_dir(), "Worker output root must already exist")
    record = output_root / f"chain-{args.unit}.json"
    launcher.require(not record.exists(), "Chain receipt already exists; preserve it")
    plan["chain_receipt"] = str(record)
    plan["java"] = java_provenance({**os.environ, **plan["environment"]}, launcher)
    bind_prior_authorities(plan, args, launcher)
    plan["java_provenance_issue"] = "https://github.com/Knowledge-Graph-Hub/kg-microbe/issues/1872"
    return plan


def verify_members(directory, record, launcher):
    """Independently compare persisted finalizer member hashes, without inventing a success marker."""
    for section in ("members", "audit_members"):
        launcher.require(
            isinstance(record.get(section), dict) and bool(record[section]), f"Missing {section}"
        )
        for name, expected in record[section].items():
            launcher.require(Path(name).name == name, "Escaping finalizer member name")
            launcher.require(
                launcher.identity(directory / name) == expected, f"Finalizer member changed: {name}"
            )


def run(plan, launcher):
    """Run one canonical source, preserve its complete output tree and check upstream nonmutation."""
    source = Path(plan["canonical_source_directory"])
    launcher.require(not source.exists(), "Canonical output appeared after planning")
    code = launcher.run(plan)
    outputs = inventory(source, launcher)
    ancillary = {name: inventory(launcher.ROOT / name, launcher) for name in ANCILLARY}
    for directory, members in plan["ancillary_before"].items():
        launcher.require(
            all(ancillary[directory].get(name) == expected for name, expected in members.items()),
            f"Pre-existing ancillary input changed: {directory}",
        )
    upstream_after = {
        name: inventory(Path(plan["canonical_output_base"]) / name, launcher)
        for name in plan["upstream_before"]
    }
    launcher.require(
        upstream_after == plan["upstream_before"], "Previously completed upstream output changed"
    )
    finalized = None
    marker = None
    if code == 0:
        record_path = source / "source_finalization.json"
        marker_path = source / "source_fingerprint.json"
        launcher.require(
            record_path.is_file() and marker_path.is_file(),
            "CLI success lacks actual completion evidence",
        )
        finalized = json.loads(record_path.read_text())
        marker = json.loads(marker_path.read_text())
        verify_members(source, finalized, launcher)
    receipt = {
        "profile": "m5-canonical-release-source-unit/v1",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "returncode": code,
        "plan": plan,
        "canonical_source_artifacts": outputs,
        "ancillary_after": ancillary,
        "ancillary_preexisting_unchanged": True,
        "upstream_unchanged": True,
        "finalization_record": finalized,
        "producer_fingerprint": marker,
        "unit_receipt": {
            "path": str(Path(plan["stage"]) / "receipt.json"),
            **launcher.identity(Path(plan["stage"]) / "receipt.json"),
        },
        "merged_graph_verified": False,
        "published_release_verified": False,
        "scope": "One real source through the canonical CLI output base; independent review precedes the next unit.",
    }
    launcher.write_new(Path(plan["chain_receipt"]), receipt)
    print(
        json.dumps(
            {
                "chain_receipt": plan["chain_receipt"],
                "returncode": code,
                "source": str(source),
                "artifact_count": len(outputs),
            }
        )
    )
    return code


def main():
    """Require a read-only plan or one explicit canonical-layout producer unit."""
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--plan", action="store_true")
    action.add_argument("--run", action="store_true")
    parser.add_argument("--kg-root", type=Path, required=True)
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--source", choices=tuple(UPSTREAM), required=True)
    parser.add_argument("--unit", required=True)
    parser.add_argument("--raw-input", action="append", required=True)
    parser.add_argument("--bacdive-receipt", type=Path)
    args = parser.parse_args()
    launcher = load_launcher(args.kg_root)
    plan = prepare(args, launcher)
    if args.plan:
        print(json.dumps({"action": "plan", "writes": 0, **plan}, sort_keys=True, indent=2))
    else:
        raise SystemExit(run(plan, launcher))


if __name__ == "__main__":
    main()
