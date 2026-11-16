#!/usr/bin/env python3
"""2026-11-16: summarize completed M5 native producers without bulk contracts.

Reads the three immutable canonical source receipts and checks their selected
files against the saved hashes. The compact report is a projection, not a new
producer/finalization receipt. NCBITaxon version queries use SQLite mode=ro and
the exact ontology-node version predicate used by KG ontology_utils. No build,
merge, network request, freshness override, or old-receipt edit is performed.
The complete BactoTraits audit is copied byte-for-byte to a fresh output path.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import re
import sqlite3
import sys
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

SOURCES = ("ontologies", "bacdive", "bactotraits")
# Exact receipts observed after the separate native executions and their reviews.
CHAIN_SHA256 = {
    "ontologies": "c5defa64ee549fbc4ef6978ca4cc1fbe441ee319d465eb1188a836cc6534119e",
    "bacdive": "6742881bc5743bdf8ed12023638634ad628f482377ad8f0ad0799936585103bd",
    "bactotraits": "36968cb32f7c10ec883160503e369bf1ad19ecfa3b8203395e327f24db93a445",
}
LAUNCHER = "scripts/adhoc/run_bactotraits_production_unit_20261116.py"
AUDIT = "bactotraits_identity_quarantine.tsv"
CAPS = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "NUMEXPR_MAX_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "RAYON_NUM_THREADS",
    "BLIS_NUM_THREADS",
)


def require(condition, message):
    """Refuse a compact success summary if its source evidence has drifted."""
    if not condition:
        raise ValueError(message)


def identity(path):
    """Stream exact bytes; never load a database into memory."""
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            size += len(block)
            digest.update(block)
    return {"bytes": size, "sha256": digest.hexdigest()}


def checked(path, expected):
    """Return a saved identity only after checking the actual file."""
    require(identity(path) == expected, f"Evidence changed: {path}")
    return dict(expected)


def read_record(path):
    """Read one already-completed evidence record without printing its payload."""
    with path.open() as stream:
        return json.load(stream)


def collect(args):
    """Build a bounded projection of recorded execution and current selected members."""
    summary_path = args.output_root / "canonical-production-summary.json"
    audit_copy = args.output_root / "full-bactotraits-audit" / AUDIT
    require(args.output_root.is_dir(), "Worker output root must already exist")
    require(
        not summary_path.exists() and not audit_copy.parent.exists(), "Preserve existing results"
    )
    result = {
        "profile": "m5-canonical-production-summary/v1",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "summary_helper": {"path": Path(__file__).name, **identity(Path(__file__))},
        "scope": "Three actual source producers; no merge or published-release success is asserted.",
        "merged_graph_verified": False,
        "published_release_verified": False,
        "sources": {},
    }
    original_inputs = {}
    runtime = None
    for source in SOURCES:
        unit_name = f"canonical-{source}-r1"
        chain_path = args.output_root / f"chain-{unit_name}.json"
        chain_identity = identity(chain_path)
        require(chain_identity["sha256"] == CHAIN_SHA256[source], "Reviewed chain receipt changed")
        chain = read_record(chain_path)
        plan = chain["plan"]
        source_dir = args.kg_root / "data/transformed" / source
        unit_path = args.kg_root / "data/validation-bactotraits-130" / unit_name / "receipt.json"
        require(chain["returncode"] == 0 and plan["source"] == source, "Producer did not complete")
        require(plan["canonical_source_directory"] == str(source_dir), "Unexpected source path")
        require(chain["unit_receipt"]["path"] == str(unit_path), "Unexpected unit receipt path")
        expected_unit = {key: chain["unit_receipt"][key] for key in ("bytes", "sha256")}
        checked(unit_path, expected_unit)
        unit = read_record(unit_path)
        require(unit["returncode"] == 0, "Native CLI did not complete")
        require(not unit["task_raw_changed_files"], "A pre-existing raw input changed")
        require(
            chain["upstream_unchanged"] and chain["ancillary_preexisting_unchanged"], "Input drift"
        )
        require(plan["processes"] == 1, "Unexpected source concurrency")
        require(all(plan["environment"][name] == "1" for name in CAPS), "Native cap drift")
        recorded_runtime = {
            "producer_commit": plan["git_revision"],
            "python": plan["python"],
            "packages": plan["packages"],
            "poetry_lock": checked(
                args.kg_root / "poetry.lock",
                plan["implementation_and_policy_inputs"]["poetry.lock"],
            ),
            "kg_launcher": {
                "path": LAUNCHER,
                **checked(
                    args.kg_root / LAUNCHER, plan["implementation_and_policy_inputs"][LAUNCHER]
                ),
            },
            "canonical_wrapper": {
                "path": "scripts/adhoc/" + Path(plan["wrapper"]["path"]).name,
                **checked(
                    Path(plan["wrapper"]["path"]),
                    {key: plan["wrapper"][key] for key in ("bytes", "sha256")},
                ),
            },
            "source_processes": 1,
            "native_thread_caps": {name: plan["environment"][name] for name in CAPS},
            "authority_guards": {
                name: plan["environment"][name]
                for name in (
                    "KG_SEMSQL_BUILD",
                    "KG_GO_VERSION_CHECK",
                    "KG_NCBITAXON_VERSION_CHECK",
                    "KG_CHEBI_VERSION_CHECK",
                )
            },
        }
        java_proofs = {
            name: checked(Path(item["path"]), {key: item[key] for key in ("bytes", "sha256")})
            for name, item in plan["java_supplements"].items()
        }
        java_native = read_record(args.output_root / "java-runtime-implementation-r3.json")
        java_implementation = {}
        for role in ("actual_runtime_launcher", "actual_runtime_vm"):
            item = java_native[role]
            java_implementation[role] = {
                "file": Path(item["path"]).name,
                **checked(Path(item["path"]), {key: item[key] for key in ("bytes", "sha256")}),
            }
        recorded_runtime["java"] = {
            "version_output": "\n".join(
                line
                for line in plan["java"]["stderr"].splitlines()
                if not line.startswith("Picked up _JAVA_OPTIONS:")
            ),
            "implementation": java_implementation,
            "supplement_files": java_proofs,
            "original_go_record_java_metadata_issue": plan["java_provenance_issue"],
        }
        require(
            plan["python"] == sys.version, "Summary interpreter differs from recorded execution"
        )
        require(
            plan["interpreter"]["executable"] == sys.executable, "Different interpreter selected"
        )
        if runtime is None:
            runtime = recorded_runtime
        require(runtime == recorded_runtime, "Source runtime or implementation differs")
        selected = {
            "source_finalization.json": chain["canonical_source_artifacts"][
                "source_finalization.json"
            ],
            "source_fingerprint.json": chain["canonical_source_artifacts"][
                "source_fingerprint.json"
            ],
            **chain["finalization_record"]["members"],
            **chain["finalization_record"]["audit_members"],
        }
        for name, expected in selected.items():
            require(Path(name).name == name, "Unexpected nested finalizer member")
            checked(source_dir / name, expected)
        result["sources"][source] = {
            "producer_commit": plan["git_revision"],
            "started_at": unit["started_at"],
            "completed_at": unit["completed_at"],
            "counts": chain["finalization_record"]["summaries"]["rows"],
            "chain_receipt": {"path": chain_path.name, **chain_identity},
            "inner_receipt": {"path": str(unit_path.relative_to(args.kg_root)), **expected_unit},
            "source_directory": str(source_dir.relative_to(args.kg_root)),
            "finalizer_graph_and_audit_members": selected,
            "finalizer_code_fingerprint": chain["finalization_record"]["finalizer_code"],
            "configuration_digest": hashlib.sha256(
                json.dumps(plan["environment"], sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest(),
            "configuration_digest_format": "sha256 of compact sorted-key environment JSON",
            "original_inputs_unchanged_at_execution_end": True,
            "existing_raw_inputs_unchanged": True,
            "upstream_unchanged": chain["upstream_unchanged"],
            "preexisting_ancillary_unchanged": chain["ancillary_preexisting_unchanged"],
        }
        original_inputs.update({Path(item["source"]).name: item for item in plan["originals"]})
        if source == "bactotraits":
            fresh_lookup = plan["fresh_bacdive_lookup"]
    result["runtime"] = runtime
    result["runtime"]["interpreter_binary_observed_during_summary"] = {
        "name": Path(sys.executable).resolve().name,
        **identity(Path(sys.executable).resolve()),
    }
    inputs = {}
    for role, name in (
        ("original_full_csv", "BactoTraits_databaseV2_Jun2022.csv"),
        ("retained_ncbitaxon_db", "ncbitaxon.db"),
        ("retained_ncbitaxon_owl_gzip", "ncbitaxon.owl.gz"),
    ):
        recorded = original_inputs[name]
        expected = {key: recorded[key] for key in ("bytes", "sha256")}
        inputs[role] = {
            "path": "data/raw/" + name,
            **checked(args.kg_root / "data/raw" / name, expected),
            "original_retained_identity_matches_staged": True,
        }
    lookup_path = args.kg_root / "kg_microbe/transform_utils/bacdive/tmp/bacdive.tsv"
    inputs["fresh_bacdive_lookup"] = {
        "path": str(lookup_path.relative_to(args.kg_root)),
        **checked(lookup_path, {key: fresh_lookup[key] for key in ("bytes", "sha256")}),
        "source_receipt": Path(fresh_lookup["receipt"]).name,
    }
    go_cache = plan["retained_go_cache"]
    go_members = {}
    for name, item in go_cache["members"].items():
        path = args.kg_root / "data/raw" / name
        require(item["path"] == str(path), "Unexpected GO cache location")
        go_members[name] = {
            "path": str(path.relative_to(args.kg_root)),
            **checked(path, {key: item[key] for key in ("bytes", "sha256")}),
        }
    go_receipt = go_cache["receipt"]
    go_receipt_path = Path(go_receipt["path"])
    inputs["current_go_cache"] = {
        "members": go_members,
        "fresh_build_receipt": {
            "path": str(go_receipt_path.relative_to(args.kg_root)),
            **checked(go_receipt_path, {key: go_receipt[key] for key in ("bytes", "sha256")}),
        },
        "java_history_note": "Original toolchain record is preserved; separately pinned supplements identify the actual JVM.",
    }
    db = args.kg_root / "data/raw/ncbitaxon.db"
    with closing(sqlite3.connect(db.as_uri() + "?mode=ro", uri=True)) as connection:
        version = connection.execute(
            "SELECT value FROM statements WHERE predicate = 'owl:versionInfo' "
            "AND subject LIKE '%ncbitaxon%' AND value IS NOT NULL LIMIT 1"
        ).fetchone()
    require(version is not None, "Missing NCBITaxon version stamp")
    db_version = re.search(r"\d{4}-\d{2}-\d{2}", str(version[0]))
    with gzip.open(args.kg_root / "data/raw/ncbitaxon.owl.gz", "rt", errors="replace") as stream:
        head = stream.read(2_000_000)
    owl_version = re.search(r"versionIRI[^>]{0,160}?(\d{4}-\d{2}-\d{2})", head)
    require(
        db_version and owl_version and db_version[0] == owl_version[1], "Authority version drift"
    )
    inputs["retained_ncbitaxon_db"].update(
        {
            "authority_version": db_version[0],
            "matching_owl_gzip_version": owl_version[1],
            "toolchain_record_present": db.with_name(db.name + ".toolchain.json").exists(),
            "build_history": "Retained database has no historical toolchain record; no original builder is inferred.",
        }
    )
    result["inputs"] = inputs
    source_audit = args.kg_root / "data/transformed/bactotraits" / AUDIT
    with source_audit.open(newline="") as stream:
        audits = list(csv.DictReader(stream, delimiter="\t"))
    require(len(audits) == 1, "Unexpected quarantine audit count")
    row = audits[0]
    require(row["source_data_row"] == row["reviewed_source_data_row"] == "8521", "Wrong row")
    require(row["bacdive_id"] == "17851", "Wrong BacDive identity")
    result["quarantine_audit"] = {
        key: row[key]
        for key in (
            "rule_id",
            "source_data_row",
            "reviewed_source_data_row",
            "bacdive_id",
            "ncbitaxon_id",
            "disposition",
            "row_sha256",
            "source_sha256",
            "reviewed_source_sha256",
            "policy_sha256",
        )
    }
    result["quarantine_audit"].update(
        {
            "row_count": 1,
            "complete_raw_row_field_count": len(json.loads(row["raw_row_json"])),
            "original_path": str(source_audit.relative_to(args.kg_root)),
            "exact_copy_path": str(audit_copy.relative_to(args.output_root)),
            **identity(source_audit),
        }
    )
    return result, summary_path, source_audit, audit_copy


def main():
    """Keep the plan read-only and both new output paths exclusive."""
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--plan", action="store_true")
    action.add_argument("--run", action="store_true")
    parser.add_argument("--kg-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    result, summary_path, source_audit, audit_copy = collect(args)
    if args.plan:
        print(
            json.dumps(
                {
                    "action": "plan",
                    "writes": 0,
                    "planned_outputs": [
                        summary_path.name,
                        str(audit_copy.relative_to(args.output_root)),
                    ],
                    **result,
                },
                indent=2,
            )
        )
        return
    audit_copy.parent.mkdir(mode=0o700)
    with audit_copy.open("xb") as stream:
        stream.write(source_audit.read_bytes())
    require(identity(audit_copy) == identity(source_audit), "Audit copy changed")
    with summary_path.open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"summary": summary_path.name, **identity(summary_path)}))


if __name__ == "__main__":
    main()
