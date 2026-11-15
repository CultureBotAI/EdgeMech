"""2026-11-13: select a fresh 50-edge recanary for PR76 without evidence retrieval.

Inputs: pinned private 10k manifest and first public canary. Outputs: private full
and public sanitized canaries, brief claims and sampling provenance. No network.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "artifacts/edge-recanary-20261113"
FIRST = ROOT / "artifacts/edge-sample-review-20261112"
SEED = "20261113-helper3-fresh-recanary-v1"


def load_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def select_rows(rows, excluded):
    """Rank within original strata, then interleave for the same 39+11 spread."""
    groups = defaultdict(list)
    for original in rows:
        if original["occurrence_id"] in excluded:
            continue
        row = dict(original)
        row["recanary_hash"] = hashlib.sha256(
            (SEED + "\n" + row["occurrence_id"]).encode()).hexdigest()
        key = (row["origin_transform"], row["content_accuracy_verdict"], row["disposition"])
        groups[key].append(row)
    eligible = []
    for group in groups.values():
        group.sort(key=lambda r: (r["recanary_hash"], r["occurrence_id"]))
        for rank, row in enumerate(group, 1):
            row["recanary_stratum_rank"] = rank
        eligible.extend(group)
    selected = []
    for transform in sorted({r["origin_transform"] for r in eligible}):
        group = [r for r in eligible if r["origin_transform"] == transform
                 and r["disposition"] == "retained"]
        group.sort(key=lambda r: (r["recanary_stratum_rank"],
                                 r["content_accuracy_verdict"], r["recanary_hash"]))
        if len(group) < 3:
            raise ValueError("Insufficient fresh retained rows")
        selected.extend(group[:3])
    reasons = sorted({r["disposition"] for r in eligible if r["disposition"] != "retained"})
    for index, reason in enumerate(reasons):
        group = [r for r in eligible if r["disposition"] == reason]
        group.sort(key=lambda r: (r["recanary_stratum_rank"], r["origin_transform"],
                                 r["content_accuracy_verdict"], r["recanary_hash"]))
        selected.extend(group[:3 if index == 0 else 2])
    if len(selected) != 50 or len({r["occurrence_id"] for r in selected}) != 50:
        raise ValueError("Expected exactly 50 fresh unique occurrences")
    if len({r["origin_transform"] for r in selected}) != 13 or len(reasons) != 5:
        raise ValueError("Expected all 13 transforms and 5 omission reasons")
    for ordinal, row in enumerate(selected, 1):
        row["canary_ordinal"] = ordinal
    return selected


def write_rows(path, rows):
    path.write_text("".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n"
                            for row in rows))


def verify(data):
    """Replay selection without writes; input order must not affect the cohort."""
    manifest = data / "sample/manifest.jsonl"
    metadata = json.loads((OUT / "sampling-metadata.json").read_text())
    if sha(manifest) != metadata["parent_manifest_sha256"]:
        raise ValueError("Parent manifest changed")
    if sha(FIRST / "canary.jsonl") != metadata["excluded_canary_sha256"]:
        raise ValueError("Excluded first canary changed")
    rows = load_rows(manifest)
    excluded = {row["occurrence_id"] for row in load_rows(FIRST / "canary.jsonl")}
    selected = select_rows(rows, excluded)
    if selected != select_rows(list(reversed(rows)), excluded):
        raise ValueError("Fresh selection depends on input ordering")
    private = data / "phase2/sample/canary.jsonl"
    if selected != load_rows(private) or sha(private) != metadata["private_original_canary"]["sha256"]:
        raise ValueError("Persisted private cohort differs from deterministic replay")
    for relative, expected in metadata["hashes"].items():
        if sha(ROOT / relative) != expected:
            raise ValueError("Public sample artifact changed")
    parents = {row["occurrence_id"]: row for row in rows}
    for row in selected:
        for key in ("subject", "predicate", "object", "sampling_weight", "stratum_population",
                    "stratum_quota", "hash_rank", "sample_hash"):
            if row[key] != parents[row["occurrence_id"]][key]:
                raise ValueError("Sampling changed an original claim or parent weight/rank")
    print(json.dumps({"verified_rows": len(selected), "input_order_independent": True,
                      "first_canary_overlap": len({r["occurrence_id"] for r in selected} & excluded)}))


def build(data):
    manifest = data / "sample/manifest.jsonl"
    prior = FIRST / "canary.jsonl"
    first_metadata = json.loads((FIRST / "sampling-metadata.json").read_text())
    if sha(manifest) != first_metadata["private_full_manifest"]["sha256"]:
        raise ValueError("Private full manifest hash mismatch")
    if sha(prior) != first_metadata["hashes"][str(prior.relative_to(ROOT))]:
        raise ValueError("First canary hash mismatch")
    rows = load_rows(manifest)
    excluded = {r["occurrence_id"] for r in load_rows(prior)}
    if len(rows) != 10000 or len({r["occurrence_id"] for r in rows}) != 10000 or len(excluded) != 50:
        raise ValueError("Unexpected manifest or first-canary cardinality")
    if not excluded <= {r["occurrence_id"] for r in rows}:
        raise ValueError("First canary is not a subset of the manifest")
    selected = select_rows(rows, excluded)
    module_path = ROOT / "scripts/adhoc/edge_sample_review_20261112/build_sample.py"
    spec = importlib.util.spec_from_file_location("first_sampling", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    public = module.public_canary(selected)
    private_path = data / "phase2/sample/canary.jsonl"
    public_path = OUT / "canary.jsonl"
    brief_path = OUT / "claims.jsonl"
    metadata_path = OUT / "sampling-metadata.json"
    for path in (private_path, public_path, brief_path, metadata_path):
        if path.exists():
            raise FileExistsError(f"Refusing to replace existing recanary: {path.name}")
    private_path.parent.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    write_rows(private_path, selected)
    write_rows(public_path, public)
    keys = ("canary_ordinal", "occurrence_id", "origin_transform", "disposition",
            "subject", "subject_label", "predicate", "predicate_label", "object", "object_label",
            "content_accuracy_verdict", "stratum_population", "stratum_quota", "sampling_weight",
            "recanary_hash", "recanary_stratum_rank")
    write_rows(brief_path, [{key: r.get(key) for key in keys} for r in selected])
    metadata = {
        "seed": SEED, "selected_at": datetime.now(timezone.utc).isoformat(),
        "sample_size": 50, "retained": 39, "omitted": 11,
        "parent_manifest_sha256": sha(manifest), "excluded_canary_sha256": sha(prior),
        "excluded_occurrences": 50, "overlap_with_first_canary": 0,
        "method": "SHA256(seed + newline + occurrence_id) within original strata; interleave rank then rule verdict for 3 retained per transform; 3 for first lexical omission reason and 2 for each remaining reason, interleaving transform/verdict strata.",
        "weight_interpretation": "Original 10k-manifest N_h/n_h weights preserved unchanged. Both canaries use deliberate coverage quotas; these are not recanary inverse inclusion weights or a population accuracy estimator.",
        "canary_transforms": dict(sorted(Counter(r["origin_transform"] for r in selected).items())),
        "canary_dispositions": dict(sorted(Counter(r["disposition"] for r in selected).items())),
        "private_original_canary": {"path": "sample/canary.jsonl", "sha256": sha(private_path),
                                    "bytes": private_path.stat().st_size},
        "private_path_base": "phase2 private data directory",
        "hashes": {str(path.relative_to(ROOT)): sha(path) for path in (public_path, brief_path)},
        "scientific_retrieval_performed": False,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"selected": 50, "overlap": 0, "public": str(public_path.relative_to(ROOT)),
                      "private_relative": "phase2/sample/canary.jsonl"}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", required=True, type=Path,
                        help="Parent private data directory containing sample/manifest.jsonl")
    parser.add_argument("--verify", action="store_true", help="Replay deterministic selection and hashes without writing")
    args = parser.parse_args()
    (verify if args.verify else build)(args.data_dir)
