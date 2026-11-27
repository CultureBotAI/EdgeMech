"""Inspect pinned fixture-family content without excluding baseline records.

Purpose: bounded read-only content observations after the accepted native audit.
Inputs: private document/locator audit JSON and their exact SHA256 pins; explicit
60-second-or-shorter cooperative budget. Reuse the audit's selection and hashes.
Outputs: stdout JSON containing only fixed check names, hashes and counts. The
caller retains actual invocation/results privately; no source text/path is copied.
Date: 2026-11-26 UTC. Issues #224/#228. This is a new parameterized inspection,
not a historical fixture producer, canonical replay or membership qualification.
No provider, subprocess, census scan, source mutation or filesystem output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from pathlib import Path

from kg_microbe_reviews import load_document

from edgemech.census import _json, _read_handle

MAX_BYTES = 16 * 1024 * 1024
MAX_TOTAL_BYTES = 64 * 1024 * 1024
MAX_ITEMS = 10_000
SHA = re.compile(r"[0-9a-f]{64}")
FAMILIES = {
    "20000101T000000Z-fixture": "occurrence_fixture",
    "20000101T000000Z-fresh-47-readiness-reviewer-a": "readiness_a",
    "20000101T000000Z-fresh-47-readiness-reviewer-b": "readiness_b",
    "original-review": "canonical_stub",
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    with _read_handle(path) as handle:
        raw = handle.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("input exceeds bound")
    return raw


def pinned(path, expected):
    if not isinstance(expected, str) or not SHA.fullmatch(expected):
        raise ValueError("invalid digest")
    raw = read(path)
    if digest(raw) != expected:
        raise ValueError("input changed")
    rows = _json(raw)
    if (not isinstance(rows, list) or len(rows) > MAX_ITEMS
            or any(not isinstance(row, dict) for row in rows)):
        raise ValueError("expected bounded mapping list")
    return rows, len(raw)


def content_checks(review, family):
    if not isinstance(review, dict):
        raise ValueError("review is not a mapping")
    if family == "canonical_stub":
        return {"exact_stub_without_assessments": review == {
            "review_id": "original-review", "targets": [{"target_id": "original-occurrence"}],
        }}
    reviewer, scope = review.get("reviewer"), review.get("scope")
    assessments, limitations = review.get("assessments"), review.get("limitations")
    if (not isinstance(reviewer, dict) or not isinstance(scope, dict)
            or not isinstance(assessments, list) or not assessments
            or any(not isinstance(item, dict) for item in assessments)
            or not isinstance(limitations, list)):
        raise ValueError("invalid inspected content shape")
    if family == "occurrence_fixture":
        return {
            "fixture_title": review.get("title") == "Synthetic scoped occurrence review",
            "fixture_summary": review.get("summary") == "Unresolved fixture remains unresolved",
            "fixture_reviewer": reviewer.get("identity") == "Fixture",
            "fixture_independence_basis": reviewer.get("independence_basis")
            == "Synthetic test; not scientific evidence",
            "fixture_scope": scope.get("selection") == "Synthetic one-unit case",
            "fixture_limitation": "Synthetic fixture" in limitations,
        }
    return {
        "fixture_title": review.get("title") == "Fixture",
        "fixture_summary": review.get("summary") == "Fixture",
        "fixture_independence_basis": reviewer.get("independence_basis") == "Fixture only",
        "fixture_scope": scope.get("description") == "Fixture"
        and scope.get("selection") == "Fixture",
        "fixture_limitation": "Fixture" in limitations,
        "fixture_assessment_summaries": all(item.get("summary") == "Authored fixture"
                                            for item in assessments),
    }


def inspect(documents_path, documents_sha, locators_path, locators_sha, seconds=60):
    if type(seconds) is not int or not 1 <= seconds <= 60:
        raise ValueError("budget must be an integer from 1 to 60")
    deadline = time.monotonic() + seconds

    def check_time():
        if time.monotonic() >= deadline:
            raise TimeoutError("cooperative inspection budget expired")

    check_time()
    documents, total_bytes = pinned(documents_path, documents_sha)
    locators, size = pinned(locators_path, locators_sha)
    total_bytes += size
    selected, known = {}, set()
    for document in documents:
        sha, review_id = document.get("sha256"), document.get("review_id")
        if (not isinstance(sha, str) or not SHA.fullmatch(sha) or sha in known
                or not isinstance(review_id, str) or not 1 <= len(review_id) <= 160
                or any(ord(c) < 32 or ord(c) == 127 for c in review_id)):
            raise ValueError("invalid or duplicate document identity")
        known.add(sha)
        if review_id in FAMILIES:
            selected[sha] = review_id
    if not selected:
        raise ValueError("no selected fixture-family observations")
    observed, counts = {}, {family: 0 for family in FAMILIES.values()}
    for locator in locators:
        check_time()
        sha = locator.get("sha256")
        if not isinstance(sha, str) or sha not in known:
            raise ValueError("locator lacks a declared byte variant")
        if sha not in selected:
            continue
        name = locator.get("path")
        if (not isinstance(name, str) or not name or len(name) > 4096
                or not Path(name).is_absolute() or ".." in Path(name).parts):
            raise ValueError("invalid private locator")
        raw = read(Path(name))
        total_bytes += len(raw)
        if total_bytes > MAX_TOTAL_BYTES:
            raise ValueError("total read budget exceeded")
        if digest(raw) != sha:
            raise ValueError("selected locator changed")
        family = FAMILIES[selected[sha]]
        counts[family] += 1
        if sha not in observed:
            review = load_document(raw)
            if not isinstance(review, dict) or review.get("review_id") != selected[sha]:
                raise ValueError("declared review identity differs")
            observed[sha] = {"sha256": sha, "family": family,
                             "checks": content_checks(review, family)}
        check_time()
    if set(observed) != set(selected):
        raise ValueError("selected variant lacks a readable locator")
    return {
        "status": "BOUNDED_FIXTURE_CONTENT_OBSERVATIONS",
        "documents_sha256": documents_sha, "locators_sha256": locators_sha,
        "declared_variants": len(documents), "selected_variants": len(selected),
        "selected_locator_counts": counts, "bytes_read": total_bytes,
        "observations": [observed[sha] for sha in sorted(observed)],
        "baseline_membership_qualified": False, "scientific_review_coverage": 0,
        "queue_A_count": None, "queue_B_count": None, "full_target_frozen": False,
        "historical_execution_binding_verified": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--documents", type=Path, required=True)
    parser.add_argument("--documents-sha256", required=True)
    parser.add_argument("--locators", type=Path, required=True)
    parser.add_argument("--locators-sha256", required=True)
    parser.add_argument("--seconds", type=int, default=60)
    args = parser.parse_args()
    try:
        result = inspect(args.documents, args.documents_sha256, args.locators,
                         args.locators_sha256, args.seconds)
    except (ValueError, OSError, TimeoutError) as error:
        print(json.dumps({"status": "FAILED_NO_QUALIFICATION", "error_type": type(error).__name__}))
        return 1
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
