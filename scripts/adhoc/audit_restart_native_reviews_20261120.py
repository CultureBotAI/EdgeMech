"""Inventory retained native review bytes without qualifying baseline membership.

Date: 2026-11-20 UTC; repaired 2026-11-26. Issues: #228 (provenance), #224
(full baseline), #234 (timestamp precision), #235 (structural projection).
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
MAX_ITEMS = 10_000
OCCURRENCE = re.compile(r"urn:kg-microbe:occurrence:v1:[0-9a-f]{64}")
REVIEW_FIELDS = {
    "review_id": 160, "kind": 160, "repository": 256, "skill": 256,
    "completion": 160, "verdict": 160, "started_at": 64, "finished_at": 64,
}
TARGET_FIELDS = {"target_id": 4096, "kind": 160, "path": 4096, "selector": 4096}
INPUT_FIELDS = {"path": 4096, "sha256": 64, "role": 1024}
ASSESSMENT_FIELDS = {"assessment_id": 160, "area": 256, "outcome": 160}


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
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|\+00:00)", value
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
    if (not isinstance(value, list) or len(value) > MAX_ITEMS
            or any(not isinstance(item, dict) for item in value)):
        raise ValueError(f"{label} must be a list of mappings; no silent omission")
    return value


def text(value, limit):
    """Bound declared structural strings; never stringify a nested input value."""
    if value is None:
        return None  # Missing optional declarations stay unknown, not inferred.
    if (not isinstance(value, str) or not value.strip() or len(value) > limit
            or any(ord(char) < 32 or ord(char) == 127 for char in value)):
        raise ValueError("invalid structural string type, length or control character")
    return value


def project(mapping, fields):
    return {key: text(mapping.get(key), limit) for key, limit in fields.items()}


def observations(review, cutoff):
    if not isinstance(review, dict):
        raise ValueError("review must be a mapping")
    declared = project(review, REVIEW_FIELDS)
    scientific = review.get("scientific_review")
    if scientific is not None and type(scientific) is not bool:
        raise ValueError("scientific_review must be a boolean or absent")
    targets = [project(row, TARGET_FIELDS)
               for row in mappings(review.get("targets", []), "targets")]
    assessments = mappings(review.get("assessments", []), "assessments")
    target_ids = {row["target_id"] for row in targets if row["target_id"] is not None}
    occurrence_targets = {value for value in target_ids if OCCURRENCE.fullmatch(value)}
    assessment_rows, assessed_ids, orphan_ids = [], set(), set()
    for position, row in enumerate(assessments):
        ids = row.get("target_ids", [])
        if (not isinstance(ids, list) or len(ids) > MAX_ITEMS
                or any(not isinstance(value, str) for value in ids)):
            raise ValueError("assessment target_ids must be strings; no silent omission")
        ids = [text(value, TARGET_FIELDS["target_id"]) for value in ids]
        exact_ids = {value for value in ids if OCCURRENCE.fullmatch(value)}
        assessed_ids |= exact_ids & occurrence_targets
        orphan_ids |= exact_ids - occurrence_targets
        dimensions = mappings(row.get("dimensions", []), "assessment dimensions")
        axes = []
        for item in dimensions:
            name = text(item.get("name"), 160)
            if name in {"axis", "category"}:
                axes.append({"name": name, "value": text(item.get("value"), 256)})
        assessment_rows.append({
            "position": position, **project(row, ASSESSMENT_FIELDS),
            "target_ids": ids, "axis_and_category": axes,
        })
    source = review.get("source", {})
    reviewer = review.get("reviewer", {})
    if not isinstance(source, dict) or not isinstance(reviewer, dict):
        raise ValueError("source and reviewer must be mappings")
    revision = text(source.get("git_revision"), 64)
    inputs = [project(row, INPUT_FIELDS)
              for row in mappings(source.get("inputs", []), "source inputs")]
    markers = []
    if reviewer.get("identity") == "Fixture":
        markers.append("reviewer.identity equals Fixture")
    if review.get("review_id") == "20000101T000000Z-fixture":
        markers.append("known synthetic review_id declared in document")
    if inputs and all(row.get("role") == "fixture input" for row in inputs):
        markers.append("all source inputs explicitly declare fixture input role")
    return {
        **{key: value for key, value in declared.items()
           if key not in {"started_at", "finished_at"}},
        "scientific_review_declared": scientific,
        "started_at_declared": declared["started_at"],
        "finished_at_declared": declared["finished_at"],
        "timing": timing(review, cutoff), "synthetic_content_markers": markers,
        "source_git_revision_declared": revision,
        "source_inputs_unverified": inputs,
        "declared_targets": targets,
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
