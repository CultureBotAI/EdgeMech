#!/usr/bin/env python3
"""Verify one strict M5 BactoTraits merge after all canonical producers complete.

2026-11-16 provenance: this is the ordinary KG merge CLI, selecting only the
canonical bactotraits source and one process. No finalization/freshness bypass
or low-level merge is used. All three actual source receipts and their complete
persisted trees are required. The canonical configuration retains its semantics;
source filenames become absolute and output-only filenames move to this unit's
exclusive directory, including stats (EdgeMech #160). Historical outputs remain
read-only. Plan before run; neither a plan nor this bounded candidate is a
full-snapshot release, publication, or scientific graph-wide validation.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import importlib.metadata
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path

import yaml

SOURCES = ("ontologies", "bacdive", "bactotraits")
SOURCE_SHA = "18316d7a0b6c2bef6fcb96a7659c2e3f3734c14786f383c2a93fefe2ae226a4b"
ROW_SHA = "345fd2d00ee93334d975085716692dd4d4c530d5529f04c5b07af0766d5a512a"
SPO = ("NCBITaxon:1123071", "biolink:has_phenotype", "METPO:1000703")
AUDIT = "bactotraits_identity_quarantine.tsv"
THREADS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS",
           "NUMEXPR_MAX_THREADS", "VECLIB_MAXIMUM_THREADS", "RAYON_NUM_THREADS", "BLIS_NUM_THREADS")


def require(condition, message):
    """Refuse incomplete or changed evidence explicitly, including under python -O."""
    if not condition:
        raise ValueError(message)


def safe(path):
    """Require a literal path without parent traversal or symlinked components."""
    path = Path(path).absolute()
    require(".." not in path.parts, "Parent traversal is not permitted")
    require(not any(item.is_symlink() for item in (path, *path.parents)), f"Symlinked path: {path}")
    return path


def identity(path):
    """Stream exact bytes and reject changes during hashing."""
    path = safe(path)
    require(path.is_file(), f"Required file missing: {path}")
    before = path.stat()
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    after = path.stat()
    fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
    require(all(getattr(before, key) == getattr(after, key) for key in fields), f"File changed while reading: {path}")
    return {"bytes": before.st_size, "sha256": digest.hexdigest()}


def snapshot(directory):
    """Inventory a named producer tree, including nested ignored files and rejecting links."""
    directory = safe(directory)
    require(directory.is_dir(), f"Required producer directory missing: {directory}")
    result = {}
    for path in sorted(directory.rglob("*")):
        require(not path.is_symlink(), f"Symlink in producer tree: {path}")
        if path.is_file():
            result[str(path.relative_to(directory))] = identity(path)
    return result


def read_json(path):
    """Read bounded receipts without accepting duplicate JSON keys."""
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    return json.loads(safe(path).read_text(), object_pairs_hook=pairs)


def write_new(path, value):
    """Preserve every earlier receipt using exclusive creation."""
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def bind(pins, path, expected=None):
    """Bind an input once and reject contradictory prior byte identities."""
    path = safe(path)
    observed = identity(path)
    if expected is not None:
        require(observed == expected, f"Receipt-bound file changed: {path}")
    require(str(path) not in pins or pins[str(path)] == observed, f"Conflicting input identity: {path}")
    pins[str(path)] = observed
    return observed


def verify_chain(kg_root, receipt_paths):
    """Require real whole-source completion and an unchanged recursive upstream chain."""
    receipts, pins = {}, {}
    for source in SOURCES:
        path = safe(receipt_paths[source])
        bind(pins, path)
        receipt = read_json(path)
        require(receipt.get("profile") == "m5-canonical-release-source-unit/v1", "Unsupported source receipt")
        require(receipt.get("returncode") == 0, f"{source}: producer did not complete")
        plan = receipt["plan"]
        require(plan.get("source") == source, f"{source}: wrong producer receipt")
        directory = kg_root / "data/transformed" / source
        require(plan.get("canonical_source_directory") == str(directory), f"{source}: noncanonical output")
        require(receipt.get("upstream_unchanged") is True and receipt.get("ancillary_preexisting_unchanged") is True,
                f"{source}: preservation checks are incomplete")
        recorded = receipt["canonical_source_artifacts"]
        require(snapshot(directory) == recorded, f"{source}: persisted source tree changed")
        for member in ("source_finalization.json", "source_fingerprint.json"):
            require(member in recorded, f"{source}: whole-source completion missing")
        finalization = read_json(directory / "source_finalization.json")
        marker = read_json(directory / "source_fingerprint.json")
        require(finalization == receipt.get("finalization_record") and finalization.get("source") == source,
                f"{source}: finalization receipt mismatch")
        require(marker == receipt.get("producer_fingerprint") and marker.get("version") == 3,
                f"{source}: producer fingerprint mismatch")
        for section in ("members", "audit_members"):
            require(bool(finalization.get(section)), f"{source}: missing finalization {section}")
            for name, expected in finalization[section].items():
                require(Path(name).name == name and name in recorded, "Invalid finalization member")
                require(recorded[name] == expected, f"{source}: finalization member differs: {name}")
        if source == "ontologies":
            require("ncbitaxon_nodes.tsv" in finalization["members"]
                    and "chebi_nodes.tsv" in finalization["members"], "Scoped ontology output cannot qualify")
        unit_ref = receipt["unit_receipt"]
        bind(pins, Path(unit_ref["path"]), {key: unit_ref[key] for key in ("bytes", "sha256")})
        unit = read_json(Path(unit_ref["path"]))
        require(unit.get("returncode") == 0 and unit.get("source") == source, "Underlying CLI unit incomplete")
        require(unit.get("git_revision") == plan.get("git_revision"), "Producer revision mismatch")
        for name, expected in plan["implementation_and_policy_inputs"].items():
            bind(pins, kg_root / name, expected)
        for original in plan["originals"]:
            bind(pins, Path(original["source"]), {key: original[key] for key in ("bytes", "sha256")})
        for upstream in SOURCES[:SOURCES.index(source)]:
            require(plan["upstream_before"].get(upstream) == receipts[upstream]["canonical_source_artifacts"],
                    f"{source}: upstream {upstream} is not the completed receipt")
        receipts[source] = receipt
    latest = read_json(Path(receipts["bactotraits"]["unit_receipt"]["path"]))
    for name, expected in latest["task_raw_after"].items():
        require(Path(name).name == name, "Invalid raw snapshot member")
        bind(pins, kg_root / "data/raw" / name, expected)
    for directory, files in receipts["bactotraits"]["ancillary_after"].items():
        for name, expected in files.items():
            bind(pins, kg_root / directory / name, expected)
    return receipts, pins


def relocated_configuration(canonical, kg_root, output):
    """Change only explicit path placement; preserve source options and graph semantics."""
    require(isinstance(canonical, dict), "Invalid canonical merge configuration")
    require(canonical.get("configuration", {}).get("allow_unfinalized_sources", False) is False,
            "Unfinalized source opt-out is forbidden")
    result = copy.deepcopy(canonical)
    deltas = []

    def replace(container, key, value, path):
        previous = container[key]
        container[key] = value
        deltas.append({"path": path, "before": previous, "after": value})

    replace(result["configuration"], "output_directory", str(output), ["configuration", "output_directory"])
    sources = result["merged_graph"]["source"]
    require("bactotraits" in sources, "Canonical BactoTraits source missing")
    for name, source in sources.items():
        inputs = source["input"]
        filenames = inputs["filename"]
        require(isinstance(filenames, list) and all(isinstance(value, str) for value in filenames),
                "Canonical source filenames must be a list")
        resolved = []
        for filename in filenames:
            path = Path(filename)
            require(not path.is_absolute() and ".." not in path.parts, "Noncanonical source path")
            resolved.append(str(safe(kg_root / path)))
        replace(inputs, "filename", resolved, ["merged_graph", "source", name, "input", "filename"])
    groups = [(["merged_graph", "operations"], result["merged_graph"].get("operations", []))]
    groups += [(["merged_graph", "source", name, "operations"], source.get("operations", []))
               for name, source in sources.items()]
    targets = set()
    for prefix, operations in groups:
        for index, operation in enumerate(operations):
            args = operation.get("args", {})
            if "filename" not in args:
                continue
            require(operation.get("name") == "kgx.graph_operations.summarize_graph.generate_graph_stats",
                    "Unreviewed output-producing merge operation")
            filename = Path(args["filename"])
            require(filename.name == str(filename), "Noncanonical operation output filename")
            target = str(output / filename.name)
            require(target not in targets, "Operation output paths collide")
            targets.add(target)
            replace(args, "filename", target, [*prefix, index, "args", "filename"])
    # Reversing every declared path-only delta must reconstruct the canonical object.
    recovered = copy.deepcopy(result)
    for delta in reversed(deltas):
        node = recovered
        for key in delta["path"][:-1]:
            node = node[key]
        node[delta["path"][-1]] = delta["before"]
    require(recovered == canonical, "Merge semantics changed beyond recorded path placement")
    return result, deltas


def literal_rows(path, delimiter="\t", encoding="utf-8", skip=0, quoting=csv.QUOTE_MINIMAL):
    """Stream well-formed literal records and preserve their data-row ordinal."""
    with path.open(encoding=encoding, newline="") as stream:
        reader = csv.reader(stream, delimiter=delimiter, quoting=quoting)
        for _ in range(skip):
            next(reader)
        header = next(reader)
        require(len(header) == len(set(header)), f"Duplicate table headers: {path}")
        for ordinal, values in enumerate(reader, 1):
            require(len(values) == len(header), f"Malformed row {ordinal}: {path}")
            yield ordinal, dict(zip(header, values))


def verify_quarantine(kg_root):
    """Replay the complete quarantined row, fresh joins and finalized source edge stream."""
    raw = kg_root / "data/raw/BactoTraits_databaseV2_Jun2022.csv"
    require(identity(raw)["sha256"] == SOURCE_SHA, "BactoTraits raw source changed")
    selected = [(ordinal, row) for ordinal, row in literal_rows(raw, ";", "ISO-8859-1", 2)
                if row.get("Bacdive_ID") == "17851"]
    require(len(selected) == 1 and selected[0][0] == 8521, "Reviewed raw occurrence is not unique row8521")
    row = selected[0][1]
    row_sha = hashlib.sha256(json.dumps(row, ensure_ascii=False, indent=2, sort_keys=True).encode()).hexdigest()
    require(row_sha == ROW_SHA, "Complete reviewed source row changed")
    audit = kg_root / "data/transformed/bactotraits" / AUDIT
    audits = list(literal_rows(audit))
    require(len(audits) == 1, "Expected exactly one complete quarantine audit occurrence")
    record = audits[0][1]
    expected = {"source_data_row": "8521", "reviewed_source_data_row": "8521", "bacdive_id": "17851",
                "ncbitaxon_id": SPO[0], "source_sha256": SOURCE_SHA, "reviewed_source_sha256": SOURCE_SHA,
                "row_sha256": ROW_SHA, "disposition": "quarantine_mixed_strain_row"}
    require(all(record.get(key) == value for key, value in expected.items()), "Quarantine audit identity mismatch")
    require(json.loads(record["raw_row_json"]) == row, "Quarantine audit omits or changes original row fields")
    policy = kg_root / "mappings/canonical/bactotraits_identity_quarantine.json"
    require(record.get("policy_sha256") == identity(policy)["sha256"], "Quarantine policy identity mismatch")
    decisions = read_json(policy).get("decisions", [])
    require(len(decisions) == 1 and decisions[0].get("bacdive_id") == "17851",
            "Policy must retain only the independently reviewed row")
    decision = decisions[0]
    for field in ("rule_id", "full_name", "culture_collection_codes", "rationale"):
        require(record.get(field) == decision.get(field), f"Quarantine audit policy field mismatch: {field}")
    require(record.get("full_name") == row.get("Full_name")
            and record.get("culture_collection_codes") == row.get("culture collection codes"),
            "Quarantine audit identity columns differ from complete original row")
    require(record.get("evidence_urls") == "|".join(decision.get("evidence_urls", [])),
            "Quarantine audit evidence URLs differ from policy")
    require(bool(record.get("rule_id")) and bool(record.get("evidence_urls")) and bool(record.get("rationale")),
            "Quarantine audit lacks decision evidence")
    joins = {}
    for source, filename, key in (("bacdive", "bacdive.tsv", "bacdive_id"),
                                  ("bactotraits", "bactotraits_mapping.tsv", "Bacdive_ID"),
                                  ("bactotraits", "bactotraits.tsv", "Bacdive_ID")):
        path = kg_root / "kg_microbe/transform_utils" / source / "tmp" / filename
        rows = [{"source_data_row": ordinal, "row": values} for ordinal, values in literal_rows(path)
                if values.get(key) in ("17851", "bacdive:17851") or values.get("ncbitaxon_id") == SPO[0]]
        target = [item for item in rows if item["row"].get(key) in ("17851", "bacdive:17851")]
        if filename == "bactotraits.tsv":
            require(not target, "Quarantined source row leaked into retained BactoTraits intermediate")
        else:
            require(len(target) == 1 and target[0]["row"].get("ncbitaxon_id") == SPO[0],
                    "Fresh source lookup does not preserve the reviewed exact identity")
        joins[f"{source}/{filename}"] = {"identity": identity(path), "matching_occurrences": rows}
    with (kg_root / "data/transformed/bactotraits/edges.tsv").open("rb") as stream:
        edges = inspect_tsv(stream, edges=True)
    require(edges["target_spo_occurrences"] == 0,
            "Target SPO remains in BactoTraits-only source output; independent lineage review is required")
    return {"audit": {"path": str(audit), **identity(audit), "rows": 1, "record": record},
            "source_row_sha256": row_sha, "fresh_joins": joins, "source_edges": edges}


def inspect_tsv(stream, *, edges=False):
    """Hash literal persisted TSV bytes and count targeted provenance while streaming."""
    digest, size, lines, tail = hashlib.sha256(), 0, 0, b""

    def decoded():
        nonlocal size, lines, tail
        for line in stream:
            digest.update(line)
            size += len(line)
            lines += line.count(b"\n")
            tail = line[-1:]
            yield line.decode("utf-8")

    reader = csv.reader(decoded(), delimiter="\t", quoting=csv.QUOTE_NONE)
    header = next(reader, None)
    require(header and len(header) == len(set(header)), "Missing or duplicate persisted TSV header")
    needed = ("subject", "predicate", "object", "primary_knowledge_source") if edges else ()
    require(set(needed).issubset(header), "Persisted edge provenance columns missing")
    count, target_count, bactotraits_count, examples = 0, 0, 0, []
    for count, values in enumerate(reader, 1):
        require(len(values) == len(header), "Malformed persisted TSV row")
        if edges:
            row = dict(zip(header, values))
            if tuple(row[key] for key in ("subject", "predicate", "object")) == SPO:
                target_count += 1
                if "infores:bactotraits" in row["primary_knowledge_source"].split("|"):
                    bactotraits_count += 1
                if len(examples) < 10:
                    examples.append({"source_data_row": count, "row": row})
    result = {"bytes": size, "sha256": digest.hexdigest(), "rows": count}
    require(count == max(0, lines + int(bool(tail) and tail != b"\n") - 1), "Physical/parsed TSV row counts differ")
    if edges:
        result.update(target_spo_occurrences=target_count, bactotraits_target_occurrences=bactotraits_count,
                      target_examples=examples)
    return result


def inspect_archive(path, config_sha, revision, python_version):
    """Verify the actual compressed graph members and embedded strict-merge provenance."""
    archive_identity = identity(path)
    seen, members, manifest = set(), {}, None
    with tarfile.open(path, "r|gz") as archive:
        for member in archive:
            require(member.isfile() and Path(member.name).name == member.name and member.name not in seen,
                    "Unsafe or duplicate graph archive member")
            seen.add(member.name)
            stream = archive.extractfile(member)
            if member.name == "manifest.json":
                require(member.size <= 1024 * 1024, "Unexpectedly large graph manifest")
                manifest = json.loads(stream.read())
            else:
                require(member.name in {"merged-kg_nodes.tsv", "merged-kg_edges.tsv", "merged-kg_reference_resolution.tsv"},
                        "Unexpected graph archive member")
                members[member.name] = inspect_tsv(stream, edges=member.name == "merged-kg_edges.tsv")
    require(manifest is not None and manifest.get("manifest_version") == 1, "Graph manifest missing or unsupported")
    expected_names = {"merged-kg_nodes.tsv", "merged-kg_edges.tsv", "merged-kg_reference_resolution.tsv"}
    require(set(members) == set(manifest.get("members", {})) == expected_names, "Graph manifest member set differs")
    for name, observed in members.items():
        require({key: observed[key] for key in ("bytes", "sha256", "rows")} == manifest["members"][name],
                f"Persisted graph member differs from manifest: {name}")
    provenance = manifest.get("provenance", {})
    require(provenance.get("source_finalization") == {"required": True, "diagnostic_opt_out": False},
            "Archive lacks strict finalization provenance")
    require(provenance.get("merge_config", {}).get("sha256") == config_sha, "Archive config identity mismatch")
    require(provenance.get("commit") == revision, "Archive producer revision is dirty or changed")
    require(provenance.get("python") == python_version, "Archive interpreter changed")
    require(members["merged-kg_edges.tsv"]["target_spo_occurrences"] == 0,
            "Target SPO remains in BactoTraits-only merge; independent lineage review is required")
    require(identity(path) == archive_identity, "Graph archive changed during inspection")
    return {"archive": {"path": str(path), **archive_identity}, "members": members, "manifest": manifest}


def runtime():
    """Bind the actual supported interpreter and complete installed distribution versions."""
    require((3, 10) <= sys.version_info[:2] <= (3, 12), "Run merge helper with pinned KG Python3.10-3.12")
    executable = Path(sys.executable).absolute()
    return {"python": sys.version, "executable": str(executable), "resolved": str(executable.resolve()),
            "binary": identity(executable.resolve()),
            "packages": {re.sub(r"[-_.]+", "-", dist.metadata["Name"].lower()): dist.version
                         for dist in importlib.metadata.distributions()}}


def prepare(args):
    """Build an immutable read-only plan requiring all completed upstream receipts."""
    kg_root, output_root, output = safe(args.kg_root), safe(args.output_root), safe(args.output)
    require(output.parent == output_root and output_root.is_dir(), "Candidate must be directly beneath worker output root")
    require(not output.exists(), "Candidate output already exists; preserve it")
    receipts, pins = verify_chain(kg_root, {source: getattr(args, source + "_receipt") for source in SOURCES})
    revision = subprocess.check_output(["git", "-C", str(kg_root), "rev-parse", "HEAD"], text=True).strip()
    short_revision = subprocess.check_output(["git", "-C", str(kg_root), "rev-parse", "--short", "HEAD"], text=True).strip()
    status = subprocess.check_output(["git", "-C", str(kg_root), "status", "--porcelain", "--untracked-files=no"], text=True)
    require(not status, "KG tracked candidate is not clean")
    require(all(receipt["plan"]["git_revision"] == revision for receipt in receipts.values()), "Source producer commits differ")
    actual_runtime = runtime()
    for name in ("inventory.json", "install-receipt.json", "installed-version-verification.json"):
        bind(pins, output_root / "environment" / name)
    installed = read_json(output_root / "environment/inventory.json")
    expected_packages = {re.sub(r"[-_.]+", "-", item["name"].lower()): item["version"]
                         for item in installed["packages"]}
    require(not installed["missing"] and actual_runtime["packages"] == expected_packages,
            "Actual merge packages differ from pinned offline installation")
    prior = receipts["bactotraits"]["plan"]
    require(actual_runtime["python"] == prior["python"]
            and actual_runtime["executable"] == prior["interpreter"]["executable"], "Merge interpreter differs from producer")
    canonical_path = kg_root / "merge.yaml"
    bind(pins, canonical_path)
    bind(pins, Path(__file__).resolve())
    configuration, deltas = relocated_configuration(yaml.safe_load(canonical_path.read_text()), kg_root, output)
    config_text = yaml.safe_dump(configuration, sort_keys=False)
    quarantine = verify_quarantine(kg_root)
    require(AUDIT in receipts["bactotraits"]["finalization_record"]["audit_members"],
            "Quarantine audit is not bound by finalization")
    lineage_path = safe(args.lineage_receipt)
    bind(pins, lineage_path)
    lineage = read_json(lineage_path)
    require(lineage.get("profile") == "m5-bactotraits-retained-lineage/v1", "Wrong historical lineage receipt")
    historical_madin = lineage["historical_source_graph_occurrences"]["madin_etal"]
    require(historical_madin["matched_occurrences"] == 1
            and historical_madin["matches"][0]["row"]["primary_knowledge_source"] == "infores:madin_etal",
            "Independent historical Madin provenance missing")
    for item in (historical_madin["input"], lineage["independent_madin_raw_occurrences"]["input"]):
        bind(pins, Path(item["path"]), {key: item[key] for key in ("bytes", "sha256")})
    environment = dict(prior["environment"])
    old_stage = prior["stage"]
    environment = {key: value.replace(old_stage, str(output)) for key, value in environment.items()}
    for key in THREADS:
        environment[key] = "1"
    environment["PYTHONPATH"] = str(kg_root)
    environment["VIRTUAL_ENV"] = str(Path(actual_runtime["executable"]).parent.parent)
    protected = {}
    for delta in deltas:
        if delta["path"][-1] == "filename" and "operations" in delta["path"]:
            path = kg_root / delta["before"]
            protected[str(path)] = identity(path) if path.exists() else None
            if path.exists():
                bind(pins, path)
    binding = {"kg_root": str(kg_root), "output_root": str(output_root), "output": str(output),
               "git_revision": revision, "short_revision": short_revision, "runtime": actual_runtime,
               "configuration": configuration, "configuration_text": config_text, "path_only_deltas": deltas,
               "input_pins": pins, "source_trees": {source: receipt["canonical_source_artifacts"] for source, receipt in receipts.items()},
               "quarantine": quarantine, "historical_independent_madin": historical_madin,
               "historical_independent_madin_raw": lineage["independent_madin_raw_occurrences"],
               "environment": environment, "protected_original_outputs": protected,
               "command": [actual_runtime["executable"], "-B", "-m", "kg_microbe.run", "merge", "-y",
                           str(output / "merge.yaml"), "-p", "1", "-s", "bactotraits"], "processes": 1}
    return {"profile": "m5-strict-bactotraits-merge-plan/v1", "action": "plan", "writes": 0,
            "binding": binding, "binding_sha256": hashlib.sha256(json.dumps(binding, sort_keys=True).encode()).hexdigest(),
            "free_disk_bytes": shutil.disk_usage(output_root).free}


def verify_after(binding):
    """Reject any input, producer tree, runtime or protected-output change after the CLI."""
    for name, expected in binding["input_pins"].items():
        require(identity(Path(name)) == expected, f"Merge input changed during execution: {name}")
    for source, expected in binding["source_trees"].items():
        require(snapshot(Path(binding["kg_root"]) / "data/transformed" / source) == expected, "Producer output changed during merge")
    require(runtime() == binding["runtime"], "Merge runtime changed")
    for name, expected in binding["protected_original_outputs"].items():
        path = Path(name)
        require((identity(path) if path.exists() else None) == expected, "Tracked or existing statistics were overwritten")


def run(plan, plan_file):
    """Execute the actual strict CLI once and verify persisted archive bytes before success."""
    approved_plan = read_json(plan_file)
    require(approved_plan.get("profile") == plan["profile"]
            and approved_plan.get("binding_sha256") == plan["binding_sha256"]
            and approved_plan.get("binding") == plan["binding"], "Inputs or plan changed since --plan")
    binding = plan["binding"]
    output = Path(binding["output"])
    require(not output.exists(), "Candidate output appeared after planning")
    os.umask(0o077)
    output.mkdir(mode=0o700)
    (output / "tmp").mkdir(mode=0o700)
    write_new(output / "plan.json", plan)
    config = output / "merge.yaml"
    with config.open("x") as stream:
        stream.write(binding["configuration_text"])
    environment = {key: value for key, value in os.environ.items()
                   if key not in ("CONDA_DEFAULT_ENV", "CONDA_PREFIX") and not key.startswith("TOX")}
    environment.update(binding["environment"])
    result = {"profile": "m5-strict-bactotraits-merge/v1", "started_at": datetime.now(timezone.utc).isoformat(),
              "plan_sha256": identity(plan_file)["sha256"], "binding_sha256": plan["binding_sha256"],
              "candidate_merged_graph_verified": False, "full_snapshot_release_verified": False,
              "published_release_verified": False, "scientific_trait_truth_resolved": False,
              "graph_wide_validation_claimed": False}
    try:
        with (output / "stdout.log").open("x") as stdout, (output / "stderr.log").open("x") as stderr:
            child = subprocess.Popen(binding["command"], cwd=binding["kg_root"], env=environment, stdout=stdout, stderr=stderr)
            write_new(output / "process.json", {"pid": child.pid, "parent_pid": os.getpid(), "command": binding["command"]})
            result["returncode"] = child.wait()
        verify_after(binding)
        require(result["returncode"] == 0, "Strict KG merge CLI did not complete; preserve logs")
        result["persisted_graph"] = inspect_archive(output / "merged-kg.tar.gz", identity(config)["sha256"],
                                                   binding["short_revision"], binding["runtime"]["python"].split()[0])
        result["quarantine_after"] = verify_quarantine(Path(binding["kg_root"]))
        require(result["quarantine_after"] == binding["quarantine"], "Quarantine/lineage changed during merge")
        result.update(status="complete", candidate_merged_graph_verified=True, inputs_and_upstreams_unchanged=True)
    except Exception as error:
        result.update(status="failed", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        result["completed_at"] = datetime.now(timezone.utc).isoformat()
        result["output_artifacts"] = {str(path.relative_to(output)): identity(path)
                                      for path in sorted(output.rglob("*")) if path.is_file()}
        write_new(output / "receipt.json", result)
    print(json.dumps({"receipt": str(output / "receipt.json"), "status": result["status"],
                      "candidate_merged_graph_verified": result["candidate_merged_graph_verified"]}))


def main():
    """Keep planning and actual merge invocation distinct and explicit."""
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", action="store_true")
    mode.add_argument("--run", action="store_true")
    for name in ("kg-root", "output-root", "output", "ontologies-receipt", "bacdive-receipt", "bactotraits-receipt", "lineage-receipt"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--plan-file", type=Path)
    args = parser.parse_args()
    if args.run and args.plan_file is None:
        parser.error("--run requires the newly recorded --plan-file")
    csv.field_size_limit(16 * 1024 * 1024)
    plan = prepare(args)
    if args.plan:
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        run(plan, args.plan_file)


if __name__ == "__main__":
    main()
