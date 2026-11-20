"""Inventory retained native review bytes without qualifying baseline membership.

Date: 2026-11-20 UTC. Issues: #228 (helper/result provenance), #224 (full baseline).
Purpose: inspect every explicit native-review locator, retaining copies, byte
variants, malformed inputs, partial assessments and synthetic-content markers.
Inputs: private newline-delimited absolute paths with a SHA256 pin, proposed UTC
cutoff. Hidden/ignored search scope is supplied separately, never inferred here.
Outputs: exclusive private result directory with per-locator readbacks, per-byte
document observations and aggregate summary. No review bodies/quotes are copied.
Provenance: uses pinned CLAW load_document and maintained census._read_handle.
This is read-only preparation, not canonical validation, source-input replay,
exhaustive archive search, scientific approval or a frozen A/B population.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from kg_microbe_reviews import load_document

from edgemech.census import _read_handle
from edgemech.pins import check_contracts

MAX_BYTES = 16 * 1024 * 1024
MAX_LOCATORS = 10_000
OCCURRENCE = re.compile(r"urn:kg-microbe:occurrence:v1:[0-9a-f]{64}")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_bounded(path):
    with _read_handle(path) as handle:
        data = handle.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("input exceeds 16 MiB; retained as unresolved")
    return data


def instant(value):
    if not isinstance(value, str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|\+00:00)", value
    ):
        raise ValueError("expected an explicit UTC timestamp")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def timing(review, cutoff):
    try:
        start, finish = instant(review.get("started_at")), instant(review.get("finished_at"))
    except (ValueError, TypeError):
        return "unknown_or_incomplete_declared_timing"
    if finish < start:
        return "invalid_declared_time_order"
    if start > cutoff:
        return "declared_after_cutoff"
    if finish > cutoff:
        return "declared_straddles_cutoff"
    return "declared_at_or_before_cutoff"


def mappings(value, label):
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise ValueError(f"{label} must be a list of mappings; no silent omission")
    return value


def observations(review, cutoff):
    targets = mappings(review.get("targets", []), "targets")
    assessments = mappings(review.get("assessments", []), "assessments")
    target_ids = {row.get("target_id") for row in targets if isinstance(row.get("target_id"), str)}
    occurrence_targets = {value for value in target_ids if OCCURRENCE.fullmatch(value)}
    assessment_rows, assessed_ids, orphan_ids = [], set(), set()
    for position, row in enumerate(assessments):
        ids = row.get("target_ids", [])
        if not isinstance(ids, list) or any(not isinstance(value, str) for value in ids):
            raise ValueError("assessment target_ids must be strings; no silent omission")
        exact_ids = {value for value in ids if OCCURRENCE.fullmatch(value)}
        assessed_ids |= exact_ids & occurrence_targets
        orphan_ids |= exact_ids - occurrence_targets
        dimensions = mappings(row.get("dimensions", []), "assessment dimensions")
        assessment_rows.append({
            "position": position, "assessment_id": row.get("assessment_id"),
            "area": row.get("area"), "outcome": row.get("outcome"), "target_ids": ids,
            "axis_and_category": [
                {"name": item.get("name"), "value": item.get("value")}
                for item in dimensions if item.get("name") in {"axis", "category"}
            ],
        })
    source = review.get("source", {})
    reviewer = review.get("reviewer", {})
    if not isinstance(source, dict) or not isinstance(reviewer, dict):
        raise ValueError("source and reviewer must be mappings")
    inputs = mappings(source.get("inputs", []), "source inputs")
    markers = []
    if reviewer.get("identity") == "Fixture":
        markers.append("reviewer.identity equals Fixture")
    if review.get("review_id") == "20000101T000000Z-fixture":
        markers.append("known synthetic review_id declared in document")
    if inputs and all(row.get("role") == "fixture input" for row in inputs):
        markers.append("all source inputs explicitly declare fixture input role")
    return {
        "review_id": review.get("review_id"), "kind": review.get("kind"),
        "repository": review.get("repository"), "skill": review.get("skill"),
        "completion": review.get("completion"), "verdict": review.get("verdict"),
        "scientific_review_declared": review.get("scientific_review"),
        "started_at_declared": review.get("started_at"),
        "finished_at_declared": review.get("finished_at"),
        "timing": timing(review, cutoff), "synthetic_content_markers": markers,
        "source_git_revision_declared": source.get("git_revision"),
        "source_inputs_unverified": [
            {key: item.get(key) for key in ("path", "sha256", "role")} for item in inputs
        ],
        "declared_targets": [
            {key: item.get(key) for key in ("target_id", "kind", "path", "selector")}
            for item in targets
        ],
        "assessment_rows": assessment_rows,
        "declared_assessed_occurrence_ids": sorted(assessed_ids),
        "orphan_assessment_occurrence_ids": sorted(orphan_ids),
        "declared_occurrence_targets_without_assessments": sorted(occurrence_targets - assessed_ids),
        "membership_disposition": "UNRESOLVED_NOT_QUALIFIED_BY_THIS_INVENTORY",
    }


def audit(paths, cutoff):
    locators, documents = [], {}
    for position, path in enumerate(paths):
        entry = {"position": position, "path": str(path)}
        locators.append(entry)
        try:
            raw = read_bounded(path)
            sha = digest(raw)
            entry.update(sha256=sha, bytes=len(raw))
            if sha not in documents:
                document = {"sha256": sha}
                documents[sha] = document
                try:
                    document.update(observations(load_document(raw), cutoff))
                    document["status"] = "parsed_observations_only"
                except Exception as error:
                    document.update(status="unresolved_parse_or_shape", error_type=type(error).__name__)
            entry["status"] = documents[sha]["status"]
        except Exception as error:
            entry.update(status="unresolved_read", error_type=type(error).__name__)
    status_counts = Counter(row["status"] for row in locators)
    parsed = [row for row in documents.values() if row["status"] == "parsed_observations_only"]
    return locators, sorted(documents.values(), key=lambda row: row["sha256"]), {
        "locator_count": len(locators), "byte_variant_count": len(documents),
        "locator_status_counts": dict(status_counts),
        "distinct_declared_review_ids": len({row.get("review_id") for row in parsed
                                             if isinstance(row.get("review_id"), str)}),
        "variant_timing_counts": dict(Counter(row["timing"] for row in parsed)),
        "variants_with_synthetic_content_markers": sum(bool(row["synthetic_content_markers"])
                                                      for row in parsed),
        "variants_with_orphan_assessment_ids": sum(bool(row["orphan_assessment_occurrence_ids"])
                                                  for row in parsed),
        "all_locators_read_and_parsed": all(row["status"] == "parsed_observations_only"
                                            for row in locators),
        "scientific_review_coverage": 0, "full_target_frozen": False,
        "queue_A_count": None, "queue_B_count": None,
    }


def write_json(path, value):
    data = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    with path.open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    if read_bounded(path) != data:
        raise ValueError("persisted output differs from authored bytes")
    return digest(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paths", type=Path, required=True)
    parser.add_argument("--paths-sha256", required=True)
    parser.add_argument("--cutoff", required=True)
    parser.add_argument("--results", type=Path, required=True)
    args = parser.parse_args()
    cutoff = instant(args.cutoff)
    raw = read_bounded(args.paths)
    if digest(raw) != args.paths_sha256:
        raise ValueError("locator inventory hash mismatch")
    paths = [Path(line) for line in raw.decode("utf-8").splitlines()]
    if not paths or len(paths) > MAX_LOCATORS or any(not path.is_absolute() for path in paths):
        raise ValueError("require 1..10000 explicit absolute locators")
    check_contracts()
    args.results.mkdir(mode=0o700)
    locators, documents, summary = audit(paths, cutoff)
    summary.update({
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "helper_sha256": digest(read_bounded(Path(__file__))),
        "paths_sha256": digest(raw), "proposed_cutoff_utc": args.cutoff,
        "locators_sha256": write_json(args.results / "locators.json", locators),
        "documents_sha256": write_json(args.results / "documents.json", documents),
        "status": "BOUNDED_NATIVE_OBSERVATIONS_BASELINE_RECONCILIATION_STILL_OPEN",
        "limitations": [
            "Locator search scope is external; this is not an exhaustive archive search",
            "Declared timing, source inputs and exact census membership need independent replay",
            "Markers are retained observations, never automatic fixture exclusion",
            "Partial/engineering/rejected observations remain; no scientific approval inferred",
            "No canonical schema validation or source/evidence correctness asserted",
        ],
    })
    write_json(args.results / "summary.json", summary)
    descriptor = os.open(args.results, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["all_locators_read_and_parsed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
