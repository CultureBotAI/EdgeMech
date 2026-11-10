"""Render measured 17M preparation results for the implementation PR, 2026-11-09.

Inputs: full/canary manifests, prior-wave audit and literature probe manifest.
Output: tracked Markdown report. Run after independent shard read-back checks.
"""
import argparse
import json
from pathlib import Path

from edgemech.storage.parquet import file_hash

parser = argparse.ArgumentParser(description=__doc__)
for name in ("full", "canary", "prior", "literature", "output"):
    parser.add_argument(f"--{name}", type=Path, required=True)
args = parser.parse_args()
full, canary, prior, literature = [json.loads(path.read_bytes()) for path in (
    args.full, args.canary, args.prior, args.literature
)]
if not full["complete_population"] or full["rows"] != 17637435:
    raise ValueError("Expected a complete pinned population")
profile = full["profile"]
size = sum(part["bytes"] for part in full["partitions"])
missing = sum(item["missing_node_occurrences"] for item in profile)
incomplete = sum(item["incomplete_node_occurrences"] for item in profile)
evidence = sum(item["inline_evidence_occurrences"] for item in profile)
lines = [
    "# Content-review preparation results — 2026-11-09", "",
    "These are deterministic accounting and retrieval results, not scientific approvals.", "",
    f"- Full population: **{full['rows']:,} occurrences**, {len(full['partitions'])} shards, "
    f"{len(profile)} sources.",
    f"- Persisted Parquet: **{size:,} bytes** ({size / 1024**3:.3f} GiB). "
    "This excludes the node catalogue, source inputs, future documents and review histories.",
    f"- Preparation elapsed time: **{full['elapsed_seconds']:,.3f} seconds** on this host; "
    "not an M5 worker-pool benchmark.",
    f"- Missing-node occurrences: **{missing:,}**; present endpoints with incomplete "
    f"labels/categories: **{incomplete:,}**.",
    f"- Occurrences with at least one nonempty inline evidence field: **{evidence:,}**. "
    "Fields include database-record URLs and unverified citations, not just literature.",
    "- Scientific reviews and approvals created: **0**. All content states remain `unassessed`.",
    "", "## Input and output identity", "",
    f"- Census manifest: `{full['census_manifest_sha256']}`.",
    f"- Reconstructed complete source edge SHA-256: `{full['selected_source_sha256']}`.",
    f"- Pinned node SHA-256: `{full['nodes_sha256']}`.",
    f"- Full preparation manifest: `{file_hash(args.full)}`.",
    f"- Final canary manifest: `{file_hash(args.canary)}`.",
    "", "The full scan used implementation commit `ef0b94e`. The subsequent #34 fix "
    "made manifest publication atomic and removed a redundant Arrow copy. A fresh "
    "20,000-row canary passed after that fix; comparison after sorting by row number "
    "confirmed identical values in every column. Physical row ordering and Parquet "
    "bytes differ, so artifact hashes are not interchangeable.",
    "", "## Canaries and prior decisions", "",
    f"Final canary: {canary['rows']:,} persisted occurrences, "
    f"{sum(p['bytes'] for p in canary['partitions']):,} Parquet bytes, "
    f"{canary['elapsed_seconds']:.3f} seconds. Exact input/output occurrence parity "
    "was checked in both directions. It does not test full-population aggregation "
    "scale, provider rate limiting or scientific review quality.",
    "", f"The hash-bound prior wave bundles contain **{prior['distinct_individual_decision_ids']} "
    "distinct individual decisions**, with zero overlap between waves: 116, 120 and "
    "357. All are withheld; no nonempty `quote` fields were found. The legacy "
    "ledger's population-wide reviewed label is cohort coverage, not evidence of "
    "17.6M individual scientific reviews. See issue #35.",
    "", f"Anonymous Europe PMC canary for DOI `{literature['identifier']}`: "
    f"`{literature['status']}`, exact identifier matched, "
    f"{literature['response_bytes']:,} response bytes persisted; SHA-256 "
    f"`{literature['response_sha256']}`. This DOI came from a prior-wave rationale, "
    "not an inferred citation for every edge. No quotation or entailment was approved. "
    "The initial sandboxed attempt failed DNS resolution and produced no completion "
    "marker; the network-enabled run used the same launcher and a new output path.",
    "", "## Exact source profile", "",
    "Distinct counts are exact across the complete population, not summed per partition.", "",
    "| Source | Occurrences | Distinct SPO | Inline evidence | Missing nodes | Incomplete metadata |",
    "|---|---:|---:|---:|---:|---:|",
]
for row in profile:
    lines.append(f"| {row['primary_knowledge_source']} | {row['occurrences']:,} | "
                 f"{row['distinct_spo']:,} | {row['inline_evidence_occurrences']:,} | "
                 f"{row['missing_node_occurrences']:,} | {row['incomplete_node_occurrences']:,} |")
lines += ["", "## Reproduce and continue", "",
          "Retained launchers are under `scripts/adhoc/`: `prepare_content_inventory_20261109.py`, "
          "`inspect_content_inventory_20261109.py`, `audit_prior_review_coverage_20261109.py`, "
          "`probe_literature_20261109.py`, `sample_inventory_citations_20261109.py`, and this "
          "report generator. Bulk artifacts remain in ignored `workspace/`.", "",
          "Next stages are the source-specific evidence catalogue, provider-governed retrieval, "
          "quote verification, scientific adjudication and validated publication described in "
          "[the corrected plan](../plans/content-review-20261109.md). The single-request probe "
          "is not a bulk retrieval scheduler. No M5 sessions were provisioned or terminated.", ""]
args.output.write_text("\n".join(lines))
