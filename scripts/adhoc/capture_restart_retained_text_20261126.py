#!/usr/bin/env python3
"""Capture a bounded selection of pinned retained text for private reconciliation.

Purpose: inspect remaining manifest/review content without filename exclusions.
Inputs: pinned private manifest, pinned GNU hash inventory, exact source pins,
and explicit JSON or UTF-8 text mode. Output: one exclusive private report with
complete decoded selected content; never publish that report or treat it as review.
Date: 2026-11-26. Issue #228. New parameterized source, not a historical producer.
Reuses the discovery helper's safe reads, cooperative bounds and durable publisher.
No provider, source restore, census, canonical save or mutable checkpoint operation.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from collections import Counter
from pathlib import Path

from edgemech.census import _json
from edgemech.pins import check_contracts

SUPPORT = Path(__file__).with_name("account_restart_discovery_20261126.py")
SPEC = importlib.util.spec_from_file_location("restart_text_support", SUPPORT)
common = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(common)
MAX_INPUTS = 512
MAX_SOURCE = 16 * 1024 * 1024


def capture(manifest_path, expected, *, seconds=60):
    budget = common.Budget(seconds)
    manifest = _json(common.read_pinned(str(manifest_path), expected, budget, 1024 * 1024))
    common.require(isinstance(manifest, dict)
                   and set(manifest) == {"version", "inventory", "format"},
                   "invalid manifest fields")
    common.require(type(manifest["version"]) is int and manifest["version"] == 1,
                   "invalid manifest version")
    mode = manifest["format"]
    common.require(isinstance(mode, str) and mode in {"json", "text"}, "invalid format")
    inventory = manifest["inventory"]
    common.require(isinstance(inventory, dict)
                   and set(inventory) == {"path", "sha256", "encoding"},
                   "invalid inventory fields")
    raw = common.read_pinned(inventory["path"], inventory["sha256"], budget)
    entries = list(common.inventory_rows(raw, inventory["encoding"], budget))
    common.require(0 < len(entries) <= MAX_INPUTS, "selection count exceeds bound")
    documents, locators = {}, []
    for position, (digest, _, name) in enumerate(entries):
        budget.check()
        locator = {"position": position, "expected_sha256": digest}
        try:
            source = common.read_pinned(name, digest, budget, MAX_SOURCE)
            locator.update(status="raw_pin_matches", bytes=len(source))
        except (ValueError, OSError) as error:
            locator.update(status="unresolved_read_or_pin", error_type=type(error).__name__)
            locators.append(locator)
            continue
        locators.append(locator)
        if digest in documents:
            continue
        document = {"sha256": digest, "bytes": len(source), "format": mode}
        try:
            text = source.decode("utf-8")
            document["text"] = text
            if mode == "json":
                value = _json(source)
                json.dumps(value, allow_nan=False)
                document.update(status="strict_json_observed", document=value)
            else:
                document.update(status="utf8_text_observed", text=text)
        except (ValueError, TypeError, UnicodeError, RecursionError) as error:
            # Retain malformed UTF-8/JSON bytes without replacing their source.
            # Hex is private evidence, never a sanitized public projection.
            document.update(status="unresolved_decode_or_json", error_type=type(error).__name__,
                            raw_hex=source.hex())
        documents[digest] = document
        budget.check()
    statuses = Counter(item["status"] for item in documents.values())
    complete = (all(item["status"] == "raw_pin_matches" for item in locators)
                and all(item["status"] in {"strict_json_observed", "utf8_text_observed"}
                        for item in documents.values()))
    return {
        "kind": "private-retained-text-observations/v1",
        "manifest_sha256": expected, "inventory_sha256": inventory["sha256"],
        "format": mode, "locator_records": len(locators),
        "distinct_read_hashes": len(documents), "document_status_counts": dict(statuses),
        "all_selected_inputs_observed_without_read_pin_or_decode_error": complete,
        "documents": [documents[key] for key in sorted(documents)], "locators": locators,
        "limitations": [
            "Raw selected content remains private and unverified; no commands in it are executed.",
            "Strict JSON or UTF-8 decoding is not schema validation or scientific approval.",
            "No baseline timing, occurrence membership or fixture disposition is inferred.",
            "Copies and variants are retained observations, not population or review counts.",
        ],
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
    # Pin executable inputs before reading the private selection.
    preflight = common.Budget(args.max_seconds)
    common.read_pinned(str(Path(__file__).absolute()), args.helper_sha256, preflight)
    common.read_pinned(str(SUPPORT.absolute()), args.support_sha256, preflight)
    check_contracts()
    report = capture(args.manifest, args.manifest_sha256, seconds=args.max_seconds)
    report.update(producer_sha256=args.helper_sha256, support_sha256=args.support_sha256)
    digest = common.publish(args.output, report)
    complete = report["all_selected_inputs_observed_without_read_pin_or_decode_error"]
    print(json.dumps({"output_sha256": digest,
                      "all_selected_inputs_observed_without_read_pin_or_decode_error": complete,
                      "scientific_review_coverage": 0}, sort_keys=True))
    return 0 if complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
