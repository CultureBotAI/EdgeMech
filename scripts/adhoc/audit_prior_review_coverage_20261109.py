"""Audit prior decision coverage without modifying reviews (2026-11-09).

Input: full-snapshot review-ledger manifest and its hash-bound wave bundles/index.
Output: JSON accounting for the 17M content-plan PR. Verifies artifact hashes and
exact decision-ID union, not independent scientific correctness or canonical
bundle validity. Cohort population counts never create individual decisions.
"""
import argparse
import json
from collections import Counter
from pathlib import Path

from edgemech.storage.parquet import file_hash


def checked(path, expected):
    path = Path(path)
    if file_hash(path) != expected:
        raise ValueError(f"Hash mismatch: {path}")
    return json.loads(path.read_bytes())


def quote_fields(value):
    if isinstance(value, dict):
        return sum(bool(item) for key, item in value.items() if key == "quote") + sum(
            quote_fields(item) for item in value.values()
        )
    if isinstance(value, list):
        return sum(quote_fields(item) for item in value)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_bytes())
    artifacts = manifest["artifacts"]
    index = checked(artifacts["individual_decision_index_593_path"],
                    artifacts["individual_decision_index_593_sha256"])
    index_ids = {item["occurrence_id"] for item in index}
    if len(index_ids) != len(index):
        raise ValueError("Repeated IDs in individual decision index")
    waves, union = {}, set()
    for name, wave in manifest["waves"].items():
        bundle = checked(wave["bundle_path"], wave["bundle_sha256"])
        decisions = bundle["decisions"]
        ids = {item["occurrence_id"] for item in decisions}
        waves[name] = {
            "decision_rows": len(decisions), "distinct_occurrences": len(ids),
            "overlap_with_prior_waves": len(union & ids),
            "dispositions": dict(Counter(item["disposition"] for item in decisions)),
            "nonempty_quote_fields": quote_fields(bundle),
            "bundle_sha256": wave["bundle_sha256"],
        }
        union |= ids
    if union != index_ids:
        raise ValueError("Wave decision-ID union does not match the individual index")
    print(json.dumps({
        "ledger_manifest_sha256": file_hash(args.manifest),
        "census_manifest_sha256": manifest["census_manifest_sha256"],
        "distinct_individual_decision_ids": len(union), "waves": waves,
        "legacy_declared_reviewed_occurrences": manifest["coverage_summary"]["reviewed_occurrences"],
        "unassessed_for_new_content_campaign": manifest["total_snapshot_occurrences"],
        "limitation": "Prior withheld decisions are not verified content or quote support.",
    }, indent=2))
