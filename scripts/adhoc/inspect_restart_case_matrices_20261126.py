#!/usr/bin/env python3
"""Observe retained case-matrix bindings without assigning baseline membership.

Purpose: account for cases/assessments nested outside native-review top-level fields.
Inputs: pinned private manifest of pinned audit locator artifacts and raw file pins.
Output: one exclusive private metadata report; locator paths and rationale/evidence
fields omitted. Declared scalar identifiers/categories remain unverified inputs.
Date: 2026-11-26. Issue #228. New parameterized source, not a historical producer.
Uses pinned CLAW loading and the discovery helper's bounded reads and publisher.
No provider, census, canonical review or mutable campaign-state operation.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
from collections import Counter
from pathlib import Path

from kg_microbe_reviews import load_document

from edgemech.census import _json
from edgemech.pins import check_contracts

SUPPORT = Path(__file__).with_name("account_restart_discovery_20261126.py")
SPEC = importlib.util.spec_from_file_location("restart_discovery_support", SUPPORT)
common = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(common)
OCCURRENCE = re.compile(r"urn:kg-microbe:occurrence:v1:[0-9a-f]{64}\Z")
MAX_ITEMS = 10_000
MAX_SOURCE = 16 * 1024 * 1024


def scalar(value, limit=256):
    if value is None:
        return None
    common.require(isinstance(value, str) and 0 < len(value) <= limit
                   and all(ord(char) >= 32 and ord(char) != 127 for char in value),
                   "unsupported scalar shape")
    return value


def sequence(value):
    common.require(isinstance(value, list) and len(value) <= MAX_ITEMS,
                   "unsupported sequence shape")
    return value


def case_observation(case, position, budget):
    budget.check(rows=1)
    common.require(isinstance(case, dict), "case must be an object")
    case_id = scalar(case.get("case_id"), 160)
    identifier = scalar(case.get("occurrence_id"), 4096)
    canonical = identifier if identifier and OCCURRENCE.fullmatch(identifier) else None
    assessments = sequence(case.get("assessments", []))
    rows = []
    for index, item in enumerate(assessments):
        budget.check(rows=1)
        common.require(isinstance(item, dict), "assessment must be an object")
        rows.append({"position": index, "axis": scalar(item.get("axis"), 160),
                     "category": scalar(item.get("category"), 256)})
    return {"position": position, "status": "observed_only", "case_id": case_id,
            "occurrence_id_declared": identifier, "canonical_occurrence_id": canonical,
            "assessment_rows": rows,
            "has_declared_occurrence_and_assessment_rows": bool(canonical and rows)}


def document_observation(value, budget):
    common.require(isinstance(value, dict), "document must be an object")
    if "cases" not in value:
        return {"status": "no_direct_cases_key", "cases": []}
    cases = sequence(value["cases"])
    result = {"status": "case_container_observations_only",
              "round_id_declared": scalar(value.get("round_id"), 160),
              "package_sha256_declared": scalar(value.get("package_sha256"), 64),
              "cases": []}
    for position, case in enumerate(cases):
        try:
            row = case_observation(case, position, budget)
        except (ValueError, TypeError) as error:
            row = {"position": position, "status": "unresolved_case_shape",
                   "error_type": type(error).__name__}
        result["cases"].append(row)
    return result


def inspect(manifest_path, expected, *, seconds=60):
    budget = common.Budget(seconds)
    manifest = _json(common.read_pinned(str(manifest_path), expected, budget, 1024 * 1024))
    common.require(isinstance(manifest, dict) and set(manifest) == {"version", "locator_artifacts"}
                   and type(manifest["version"]) is int and manifest["version"] == 1,
                   "invalid manifest")
    artifacts = manifest["locator_artifacts"]
    common.require(isinstance(artifacts, list) and 0 < len(artifacts) <= 128,
                   "invalid locator artifact count")
    locators, documents, inputs = [], {}, []
    for artifact_index, item in enumerate(artifacts):
        common.require(isinstance(item, dict) and set(item) == {"path", "sha256"},
                       "invalid locator artifact fields")
        raw = common.read_pinned(item["path"], item["sha256"], budget)
        entries = sequence(_json(raw))
        inputs.append({"artifact_index": artifact_index, "sha256": item["sha256"],
                       "locator_records": len(entries)})
        for position, entry in enumerate(entries):
            budget.check(rows=1)
            common.require(len(locators) < MAX_ITEMS and isinstance(entry, dict)
                           and "path" in entry and "sha256" in entry,
                           "invalid locator or total locator bound")
            pin = common.token(entry["sha256"], common.DIGEST, "raw file digest")
            record = {"artifact_index": artifact_index, "position": position, "sha256": pin}
            locators.append(record)
            try:
                source = common.read_pinned(entry["path"], pin, budget, MAX_SOURCE)
                record["bytes"] = len(source)
                if pin not in documents:
                    document = {"sha256": pin}
                    documents[pin] = document
                    try:
                        document.update(document_observation(load_document(source), budget))
                    except (ValueError, TypeError) as error:
                        document.update(status="unresolved_document_shape",
                                        error_type=type(error).__name__, cases=[])
                record["status"] = "raw_pin_matches"
            except (OSError, ValueError, TypeError) as error:
                record.update(status="unresolved_read_or_pin", error_type=type(error).__name__)
    ordered = sorted(documents.values(), key=lambda row: row["sha256"])
    rows = [row for document in ordered for row in document.get("cases", [])]
    canonical_ids = sorted({row["canonical_occurrence_id"] for row in rows
                            if row.get("canonical_occurrence_id")})
    bound_ids = sorted({row["canonical_occurrence_id"] for row in rows
                        if row.get("has_declared_occurrence_and_assessment_rows")})
    unresolved = (any(row["status"] != "raw_pin_matches" for row in locators)
                  or any(row["status"].startswith("unresolved") for row in ordered + rows))
    budget.check()
    return {
        "kind": "retained-case-matrix-observations/v1", "manifest_sha256": expected,
        "inputs": inputs, "locators": locators, "documents": ordered,
        "locator_records": len(locators), "distinct_read_hashes": len(ordered),
        "document_status_counts": dict(Counter(row["status"] for row in ordered)),
        "case_rows_across_variants_not_population": len(rows),
        "unresolved_case_rows": sum(row["status"].startswith("unresolved") for row in rows),
        "assessment_rows_across_variants_not_population":
            sum(len(row.get("assessment_rows", [])) for row in rows),
        "canonical_case_ids_declared": canonical_ids,
        "case_ids_with_assessment_rows_declared": bound_ids,
        "all_selected_inputs_observed_without_shape_or_pin_error": not unresolved,
        "limitations": ["Direct cases/assessments only; other containers remain outside this predicate.",
                        "Declared IDs, axes and categories are observations, not validated judgments.",
                        "No timing, source replay, scientific approval or baseline membership inferred.",
                        "Counters preserve byte-variant rows; they are not unique occurrence coverage."],
        "scientific_review_coverage": 0, "queue_A_count": None, "queue_B_count": None,
        "full_target_frozen": False, "baseline_cutoff_frozen": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--helper-sha256", required=True)
    parser.add_argument("--support-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-seconds", type=float, default=60)
    args = parser.parse_args()
    common.read_pinned(str(Path(__file__).absolute()), args.helper_sha256, common.Budget(), 1024 * 1024)
    common.read_pinned(str(SUPPORT.absolute()), args.support_sha256, common.Budget(), 1024 * 1024)
    check_contracts()
    result = inspect(args.manifest, args.manifest_sha256, seconds=args.max_seconds)
    result.update(producer_sha256=args.helper_sha256, support_sha256=args.support_sha256)
    digest = common.publish(args.output, result)
    print(json.dumps({"output_sha256": digest, "scientific_review_coverage": 0,
                      "all_selected_inputs_observed_without_shape_or_pin_error":
                          result["all_selected_inputs_observed_without_shape_or_pin_error"]}, sort_keys=True))
    return 0 if result["all_selected_inputs_observed_without_shape_or_pin_error"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
