"""Build deterministic helper-3 edge sample (2026-11-12).

Inputs: retained/omitted population CSV and immutable remote Parquets.
Outputs: quota CSV, saved SQL, 10k JSONL manifest, 50-edge canary and metadata.
Serves the helper-3 stratified edge-review draft PR. No evidence retrieval.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import shlex
import shutil
import subprocess
import time
from collections import Counter, defaultdict
from pathlib import Path

FILES = {
    "review": "non_ontology_transform_edge_reviews_all_16.37M.parquet",
    "doi": "doi-enrichment-tier0-tier1/curated_non_ontology_edges_tier0_tier1_doi.parquet",
    "omitted": "post-merge-curated/omitted_edges_audit_log.parquet",
    "nodes": "node_catalog.parquet",
}
HOST = None
DUCKDB = "duckdb"
SEED = "20261112-helper3-edge-sample-v1"
ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "artifacts/edge-sample-review-20261112"
PRIVATE_FULL = None


def public_canary(rows):
    """Remove inherited prose; exact original rows remain in private evidence."""
    excluded = {"review_rationale", "reviewer_worker", "snippet", "description",
                "source_citation", "prego_evidence"}

    def clean(value):
        if isinstance(value, dict):
            return {key: clean(item) for key, item in value.items() if key not in excluded}
        if isinstance(value, list):
            return [clean(item) for item in value]
        return value

    return [clean(row) for row in rows]


def public_metadata(metadata):
    """Publish identity hashes and relative inputs; machine receipt stays private."""
    metadata = json.loads(json.dumps(metadata))
    metadata.pop("input_file_size_mtime_before_and_after", None)
    metadata["input_files"] = FILES
    metadata["input_identity_limitation"] = (
        "Input sizes, mtimes and full execution receipt are retained privately; "
        "full input SHA-256 was not computed. Public schemas and relative filenames are retained.")
    if "private_full_manifest" in metadata:
        metadata["private_full_manifest"]["path"] = "sample/manifest.jsonl"
    metadata["source_representation"] = (
        "Original and curated triples remain distinct. Committed canary removes inherited "
        "narratives, long descriptions and source prose; full source rows and original canary "
        "are retained privately and hash-bound. Catalog label alternatives remain explicit.")
    metadata["committed_manifest"] = (
        "Compact identity/claim/stratum derivative. Full 10k source records retained privately; "
        "the committed 50-edge canary is a sanitized derivative of the private original.")
    return metadata


def sanitize_existing():
    """Preserve run provenance privately and publish portable sampling artifacts."""
    private = PRIVATE_FULL.parent / "private-provenance"
    private.mkdir(parents=True, exist_ok=True)
    paths = [Path(__file__).with_name(name) for name in ("sample.sql", "populations.sql")]
    paths += [OUT / "sampling-metadata.json", OUT / "canary.jsonl"]
    for path in paths:
        destination = private / path.name
        if not destination.exists():
            shutil.copy2(path, destination)
    metadata = json.loads((private / "sampling-metadata.json").read_text())
    original = private / "canary.jsonl"
    original_hash = hashlib.sha256(original.read_bytes()).hexdigest()
    if original_hash != metadata["hashes"][str((OUT / "canary.jsonl").relative_to(ROOT))]:
        raise ValueError("Private original canary and execution receipt disagree")
    rows = [json.loads(line) for line in original.read_text().splitlines()]
    write_jsonl(OUT / "canary.jsonl", public_canary(rows))
    with (OUT / "allocation.csv").open() as handle:
        quotas = list(csv.DictReader(handle))
    sql_path = Path(__file__).with_name("sample.sql")
    sql_path.write_text(query(quotas))
    Path(__file__).with_name("populations.sql").write_text(population_query())
    metadata = public_metadata(metadata)
    metadata["private_original_canary"] = {
        "path": "sample/private-provenance/canary.jsonl", "sha256": original_hash,
        "bytes": original.stat().st_size}
    metadata["private_execution_receipt_sha256"] = hashlib.sha256(
        (private / "sampling-metadata.json").read_bytes()).hexdigest()
    metadata["private_executed_sql_sha256"] = hashlib.sha256(
        (private / "sample.sql").read_bytes()).hexdigest()
    for path in paths[:2] + [OUT / "canary.jsonl", OUT / "allocation.csv"]:
        metadata["hashes"][str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    (OUT / "sampling-metadata.json").write_text(json.dumps(metadata, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"public_canary_sha256": metadata["hashes"][str((OUT / "canary.jsonl").relative_to(ROOT))],
                      "private_original_canary_sha256": original_hash, "rows": len(rows)}))


def normalize_allocation():
    """Issue #74: preserve the original CSV, normalize CRLF, and refresh its hash."""
    path = OUT / "allocation.csv"
    metadata_path = OUT / "sampling-metadata.json"
    metadata = json.loads(metadata_path.read_text())
    key = str(path.relative_to(ROOT))
    original = path.read_bytes()
    if hashlib.sha256(original).hexdigest() != metadata["hashes"][key]:
        raise ValueError("Allocation and recorded hash disagree before normalization")
    private = PRIVATE_FULL.parent / "private-provenance"
    private.mkdir(parents=True, exist_ok=True)
    backup = private / "allocation-before-lf.csv"
    if not backup.exists():
        backup.write_bytes(original)
    normalized = original.replace(b"\r\n", b"\n")
    path.write_bytes(normalized)
    metadata["hashes"][key] = hashlib.sha256(normalized).hexdigest()
    metadata_path.write_text(json.dumps(metadata, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"allocation_sha256": metadata["hashes"][key],
                      "normalized_crlf": original.count(b"\r\n")}))


def compact(rows):
    keys = ("occurrence_id", "row_number", "partition_id", "origin_transform",
            "transform_row_number", "subject", "subject_label", "predicate", "predicate_label",
            "object", "object_label", "presence_verdict", "content_accuracy_verdict",
            "disposition", "stratum_population", "stratum_quota", "sampling_weight",
            "hash_rank", "sample_hash")
    output = []
    for row in rows:
        item = {key: row[key] for key in keys}
        curated = row["curated_source_record"]
        if curated and (any(curated[key] != row[key] for key in ("subject", "predicate", "object"))
                        or curated["curation_action"] != "kept_unchanged"):
            item["curated_change"] = {key: curated[key] for key in (
                "subject", "predicate", "object", "curation_action")}
        output.append(item)
    return output


def private_pin():
    return {"path": str(PRIVATE_FULL), "sha256": hashlib.sha256(PRIVATE_FULL.read_bytes()).hexdigest(),
            "bytes": PRIVATE_FULL.stat().st_size}


def input_schemas(files):
    sql = " UNION ALL ".join(
        f"SELECT {quoted(name)} AS input_file, * FROM "
        f"(DESCRIBE SELECT * FROM read_parquet({quoted(path)}))"
        for name, path in files.items()) + ";"
    return json.loads(remote(shlex.quote(DUCKDB) + " -json", input_text=sql))


def compact_existing(files):
    """Move verified full manifest privately, then publish a compact derivative."""
    manifest = OUT / "manifest.jsonl"
    metadata_path = OUT / "sampling-metadata.json"
    metadata = json.loads(metadata_path.read_text())
    expected = metadata["hashes"][str(manifest.relative_to(ROOT))]
    if hashlib.sha256(manifest.read_bytes()).hexdigest() != expected:
        raise ValueError("Existing full manifest hash differs from sampling receipt")
    rows = [json.loads(line) for line in manifest.read_text().splitlines()]
    if len(rows) != 10000:
        raise ValueError("Existing full manifest cardinality differs")
    if PRIVATE_FULL.exists():
        raise FileExistsError(PRIVATE_FULL)
    metadata["input_schemas"] = input_schemas(files)
    PRIVATE_FULL.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(manifest), str(PRIVATE_FULL))
    if private_pin()["sha256"] != expected:
        raise ValueError("Moved full manifest hash differs")
    write_jsonl(manifest, compact(rows))
    metadata["hashes"][str(manifest.relative_to(ROOT))] = hashlib.sha256(manifest.read_bytes()).hexdigest()
    metadata["private_full_manifest"] = private_pin()
    metadata["committed_manifest"] = "Compact identity/claim/stratum derivative; full 10k source records retained at private_full_manifest. Full canary unchanged."
    (PRIVATE_FULL.parent / "sampling-metadata.json").write_text(json.dumps(metadata, sort_keys=True, indent=2) + "\n")
    metadata_path.write_text(json.dumps(public_metadata(metadata), sort_keys=True, indent=2) + "\n")
    print(json.dumps({"private_full_manifest": private_pin(), "compact_bytes": manifest.stat().st_size}))


def quoted(value):
    return "'" + str(value).replace("'", "''") + "'"


def apportion(total, capacities):
    """Equal quotas with deterministic remainder and capacity redistribution."""
    result = dict.fromkeys(sorted(capacities), 0)
    while total:
        available = [key for key in result if result[key] < capacities[key]]
        if not available:
            raise ValueError("Insufficient population for requested sample")
        share = max(1, total // len(available))
        for key in available:
            amount = min(share, capacities[key] - result[key], total)
            result[key] += amount
            total -= amount
    return result


def allocation():
    with (OUT / "populations.csv").open() as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["population"] = int(row["population"])
    selected = {}
    for retained, total in ((True, 8500), (False, 1500)):
        eligible = [r for r in rows if (r["disposition"] == "retained") == retained]
        group_field = "origin_transform" if retained else "disposition"
        grouped = defaultdict(list)
        for row in eligible:
            grouped[row[group_field]].append(row)
        quotas = apportion(total, {k: sum(r["population"] for r in group) for k, group in grouped.items()})
        for key, group in grouped.items():
            capacities = {(r["origin_transform"], r["content_accuracy_verdict"], r["disposition"]): r["population"] for r in group}
            selected.update(apportion(quotas[key], capacities))
    for row in rows:
        key = (row["origin_transform"], row["content_accuracy_verdict"], row["disposition"])
        row["sample_quota"] = selected[key]
        row["inclusion_probability"] = row["sample_quota"] / row["population"]
        row["sampling_weight"] = row["population"] / row["sample_quota"]
        row["hash_prefix_threshold"] = math.ceil(2**32 * min(1, (3 * row["sample_quota"] + 100) / row["population"]))
    with (OUT / "allocation.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return rows


def population_query(files=None):
    files = FILES if files is None else files
    return f"""-- Population strata, helper-3 sample, 2026-11-12.
-- Paths are relative to the input root; build_sample.py accepts --input-root.
SET threads=2;
SET memory_limit='4GB';
SET max_temp_directory_size='1GB';
SELECT r.origin_transform,r.content_accuracy_verdict,
 coalesce(o.omission_reason,'retained') AS disposition,count(*) AS population
FROM read_parquet({quoted(files['review'])}) r
LEFT JOIN read_parquet({quoted(files['omitted'])}) o USING(occurrence_id)
GROUP BY ALL ORDER BY ALL;
"""


def query(rows, files=None):
    files = FILES if files is None else files
    values = ",\n".join("(" + ",".join(quoted(r[key]) for key in (
        "origin_transform", "content_accuracy_verdict", "disposition")) + "," + ",".join(str(r[key]) for key in (
        "population", "sample_quota", "hash_prefix_threshold")) + ")" for r in rows)
    return f"""-- Helper-3 deterministic sample, 2026-11-12. Generated by build_sample.py.
-- Hash-prefix prefilter uses the SAME md5 order as ranking; exact quotas are checked.
-- No remote output files. Memory/temporary spill bounded explicitly.
-- Portable template: paths are relative to the input root.
SET threads=2;
SET memory_limit='4GB';
SET max_temp_directory_size='1GB';
CREATE TEMP TABLE quotas(origin_transform VARCHAR, content_accuracy_verdict VARCHAR,
 disposition VARCHAR, population BIGINT, quota BIGINT, threshold BIGINT);
INSERT INTO quotas VALUES {values};
CREATE TEMP TABLE hash_candidates AS
SELECT r.occurrence_id, q.*, md5({quoted(SEED)} || ':' || r.occurrence_id) AS sample_hash
FROM read_parquet({quoted(files['review'])}) r
JOIN quotas q USING(origin_transform, content_accuracy_verdict)
WHERE ('0x' || substr(md5({quoted(SEED)} || ':' || r.occurrence_id),1,8))::BIGINT < q.threshold;
CREATE TEMP TABLE selected AS
SELECT h.*, row_number() OVER (
 PARTITION BY h.origin_transform,h.content_accuracy_verdict,h.disposition
 ORDER BY h.sample_hash,h.occurrence_id) AS hash_rank
FROM hash_candidates h
LEFT JOIN read_parquet({quoted(files['omitted'])}) o USING(occurrence_id)
WHERE coalesce(o.omission_reason,'retained') = h.disposition
QUALIFY hash_rank <= h.quota;
CREATE TEMP TABLE sampled_review AS
SELECT r.* FROM read_parquet({quoted(files['review'])}) r
SEMI JOIN selected s USING(occurrence_id);
CREATE TEMP TABLE sampled_curated AS
SELECT c.* FROM read_parquet({quoted(files['doi'])}) c
SEMI JOIN selected s USING(occurrence_id);
CREATE TEMP TABLE sampled_omitted AS
SELECT o.* FROM read_parquet({quoted(files['omitted'])}) o
SEMI JOIN selected s USING(occurrence_id);
CREATE TEMP TABLE sampled_node_ids AS
SELECT subject AS id FROM sampled_review UNION SELECT object FROM sampled_review
UNION SELECT subject FROM sampled_curated UNION SELECT object FROM sampled_curated;
CREATE TEMP TABLE sampled_nodes AS
SELECT n.id, min(n.name) AS name, list(DISTINCT n.name ORDER BY n.name) AS labels,
 min(n.description) AS description, count(*) AS catalog_rows
FROM read_parquet({quoted(files['nodes'])}) n SEMI JOIN sampled_node_ids i USING(id)
GROUP BY n.id;
SELECT r.*, s.disposition, s.population AS stratum_population, s.quota AS stratum_quota,
 s.population::DOUBLE/s.quota AS sampling_weight, s.sample_hash, s.hash_rank,
 CASE WHEN c.occurrence_id IS NULL THEN NULL ELSE c END AS curated_source_record,
 CASE WHEN o.occurrence_id IS NULL THEN NULL ELSE o END AS omitted_source_record,
 ns AS original_subject_node, no AS original_object_node,
 cs AS curated_subject_node, co AS curated_object_node
FROM sampled_review r JOIN selected s USING(occurrence_id)
LEFT JOIN sampled_curated c USING(occurrence_id)
LEFT JOIN sampled_omitted o USING(occurrence_id)
LEFT JOIN sampled_nodes ns ON ns.id = r.subject
LEFT JOIN sampled_nodes no ON no.id = r.object
LEFT JOIN sampled_nodes cs ON cs.id = c.subject
LEFT JOIN sampled_nodes co ON co.id = c.object
ORDER BY r.origin_transform,s.disposition,r.content_accuracy_verdict,s.hash_rank;
"""


def remote(command, *, input_text=None):
    if not HOST:
        raise ValueError("Remote host must be supplied explicitly")
    result = subprocess.run(["ssh", HOST, command], input=input_text, text=True,
                            capture_output=True, check=True)
    if result.stderr.strip():
        print(result.stderr.strip())
    return result.stdout


def write_jsonl(path, rows):
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def canary(rows):
    chosen = []
    for transform in sorted({r["origin_transform"] for r in rows}):
        group = [r for r in rows if r["origin_transform"] == transform and r["disposition"] == "retained"]
        # Rank-first interleaving ensures available rule-verdict strata are represented.
        group.sort(key=lambda r: (r["hash_rank"], r["content_accuracy_verdict"], r["sample_hash"]))
        chosen.extend(group[:3])
    reasons = sorted({r["disposition"] for r in rows if r["disposition"] != "retained"})
    for index, reason in enumerate(reasons):
        group = sorted((r for r in rows if r["disposition"] == reason), key=lambda r: (
            r["hash_rank"], r["origin_transform"], r["sample_hash"]))
        chosen.extend(group[:3 if index == 0 else 2])
    if len(chosen) != 50 or len({r["occurrence_id"] for r in chosen}) != 50:
        raise ValueError("Canary must contain exactly 50 distinct occurrence IDs")
    if len({r["origin_transform"] for r in chosen}) != 13:
        raise ValueError("Canary transform coverage incomplete")
    if len({r["disposition"] for r in chosen if r["disposition"] != "retained"}) != 5:
        raise ValueError("Canary omission coverage incomplete")
    for index, row in enumerate(chosen, 1):
        row["canary_ordinal"] = index
    return chosen


def main():
    global HOST, DUCKDB, PRIVATE_FULL
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Run bounded read-only remote sampling")
    parser.add_argument("--compact-existing", action="store_true", help="Move verified full sample privately; read input schemas only")
    parser.add_argument("--sanitize-existing", action="store_true", help="Publish portable derivatives of the saved run without resampling")
    parser.add_argument("--normalize-allocation", action="store_true", help="Normalize allocation CSV line endings and refresh its hash without resampling")
    parser.add_argument("--remote-host", default=os.environ.get("EDGEMECH_REMOTE_HOST"))
    parser.add_argument("--input-root", type=Path)
    parser.add_argument("--private-data-dir", type=Path)
    parser.add_argument("--remote-duckdb", default="duckdb")
    args = parser.parse_args()
    if sum((args.execute, args.compact_existing, args.sanitize_existing, args.normalize_allocation)) > 1:
        parser.error("Choose one execution or migration mode")
    if args.execute or args.compact_existing or args.sanitize_existing or args.normalize_allocation:
        if args.private_data_dir is None:
            parser.error("--private-data-dir is required for execution or migration")
        PRIVATE_FULL = args.private_data_dir.resolve() / "sample/manifest.jsonl"
    if args.execute or args.compact_existing:
        if not args.remote_host or args.input_root is None:
            parser.error("--remote-host and --input-root are required for remote execution")
    HOST, DUCKDB = args.remote_host, args.remote_duckdb
    files = {name: str(args.input_root / value) for name, value in FILES.items()} if args.input_root else FILES
    if args.normalize_allocation:
        normalize_allocation()
        return
    if args.sanitize_existing:
        sanitize_existing()
        return
    if args.compact_existing:
        if args.execute:
            parser.error("--compact-existing and --execute are mutually exclusive")
        compact_existing(files)
        return
    for filename in ("manifest.jsonl", "canary.jsonl", "sampling-metadata.json"):
        if (OUT / filename).exists():
            raise FileExistsError(f"Refusing to overwrite completed sample: {filename}")
    quotas = allocation()
    sql_path = Path(__file__).with_name("sample.sql")
    sql = query(quotas)
    sql_path.write_text(sql)
    print(json.dumps({"planned_edges": sum(r["sample_quota"] for r in quotas),
                      "strata": len(quotas), "sql": str(sql_path)}))
    if not args.execute:
        return
    stat_command = "stat -f '%N|%z|%m' " + " ".join(shlex.quote(value) for value in files.values())
    before = remote(stat_command)
    schemas = input_schemas(files)
    version = remote(shlex.quote(DUCKDB) + " --version").strip()
    actual_sql = query(quotas, files)
    PRIVATE_FULL.parent.mkdir(parents=True, exist_ok=True)
    (PRIVATE_FULL.parent / "sample.executed.sql").write_text(actual_sql)
    start = time.monotonic()
    raw = remote(shlex.quote(DUCKDB) + " -json", input_text=actual_sql)
    elapsed = time.monotonic() - start
    after = remote(stat_command)
    if before != after:
        raise ValueError("Input metadata changed during sampling")
    rows = json.loads(raw)
    if len(rows) != 10000 or len({r["occurrence_id"] for r in rows}) != 10000:
        raise ValueError("Sample cardinality or occurrence multiplicity failure")
    counts = Counter((r["origin_transform"], r["content_accuracy_verdict"], r["disposition"]) for r in rows)
    for quota in quotas:
        key = (quota["origin_transform"], quota["content_accuracy_verdict"], quota["disposition"])
        if counts[key] != quota["sample_quota"]:
            raise ValueError(f"Insufficient prefixed candidates for {key}; increase threshold, regenerate before reviewing")
    for row in rows:
        if (row["curated_source_record"] is not None) != (row["disposition"] == "retained"):
            raise ValueError("Retained/omitted join mismatch")
        if (row["omitted_source_record"] is not None) != (row["disposition"] != "retained"):
            raise ValueError("Omission audit join mismatch")
    if PRIVATE_FULL.exists():
        raise FileExistsError(PRIVATE_FULL)
    PRIVATE_FULL.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(PRIVATE_FULL, rows)
    write_jsonl(OUT / "manifest.jsonl", compact(rows))
    selected_canary = canary(rows)
    write_jsonl(PRIVATE_FULL.parent / "canary.jsonl", selected_canary)
    write_jsonl(OUT / "canary.jsonl", public_canary(selected_canary))
    metadata = {
        "seed": SEED, "sample_size": len(rows), "canary_size": len(selected_canary),
        "private_full_manifest": private_pin(),
        "input_schemas": schemas,
        "committed_manifest": "Compact identity/claim/stratum derivative; full 10k source records retained at private_full_manifest. Full canary retained.",
        "retained_sample": 8500, "omitted_sample": 1500, "remote_sampling_seconds": elapsed,
        "duckdb_version": version, "input_file_size_mtime_before_and_after": before.splitlines(),
        "input_identity_limitation": "File paths, sizes, mtimes and unchanged metadata are recorded; full input SHA-256 not computed.",
        "method": "Top seeded MD5 occurrence hashes within transform x rule-verdict x disposition; conservative same-hash prefix filtering retains exact top quota, verified for every stratum.",
        "allocation": "8500 equally across 13 retained transforms then verdicts; 1500 equally across five omission reasons then transform/verdict strata, capacity constrained.",
        "canary_selection": "39 retained: first three rank-interleaved rows per transform; 11 omitted: first 3 for first lexical omission reason, 2 for each remaining reason; not a precision-estimation sample.",
        "inference": "Full manifest has inverse inclusion weights N_h/n_h. Canary is purposive coverage within sample and must not be used to estimate population accuracy or confidence intervals.",
        "precision": "At least 653 retained edges per transform. Approximate +/-5% 95% binomial precision at n=385 presumes independent simple random sampling; stratified weights, clustering, assessment missingness and reviewer error require separate treatment.",
        "source_representation": "Top-level triple/labels are original rule-review values. curated_source_record and omitted_source_record preserve separate input rows. Node labels are explicit catalog candidates; min(name) is display-only when labels disagree.",
        "hashes": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in (
            OUT / "populations.csv", OUT / "allocation.csv", sql_path, OUT / "manifest.jsonl", OUT / "canary.jsonl")},
        "transforms": dict(sorted(Counter(r["origin_transform"] for r in rows).items())),
        "canary_transforms": dict(sorted(Counter(r["origin_transform"] for r in selected_canary).items())),
        "canary_dispositions": dict(sorted(Counter(r["disposition"] for r in selected_canary).items())),
    }
    private_canary = PRIVATE_FULL.parent / "canary.jsonl"
    metadata["private_original_canary"] = {"path": "sample/canary.jsonl",
        "sha256": hashlib.sha256(private_canary.read_bytes()).hexdigest(), "bytes": private_canary.stat().st_size}
    (PRIVATE_FULL.parent / "sampling-metadata.json").write_text(json.dumps(metadata, sort_keys=True, indent=2) + "\n")
    public = public_metadata(metadata)
    public["private_executed_sql_sha256"] = hashlib.sha256(actual_sql.encode()).hexdigest()
    public["private_execution_receipt_sha256"] = hashlib.sha256(
        (PRIVATE_FULL.parent / "sampling-metadata.json").read_bytes()).hexdigest()
    (OUT / "sampling-metadata.json").write_text(json.dumps(public, sort_keys=True, indent=2) + "\n")
    print(json.dumps(public, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
