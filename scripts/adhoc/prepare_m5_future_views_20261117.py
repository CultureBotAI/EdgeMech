#!/usr/bin/env python3
"""Prepare v4 future case views; inputs are original packets, outputs exclusive views.

Issues #203/#210, 2026-11-17. Preserve historical v3 replay. The future view removes
only inspected review-status spans from the exact mixed description; definitions,
limitations and provenance remain. This is not a scientific assessment.
"""
from __future__ import annotations

import argparse
import hashlib
import json

import prepare_m5_reviewer_views_20261116 as original
import prepare_m5_round02_views_20261116 as prior

ROOT = original.ROOT
VERSION = "edgemech-blinded-view/v4"
HELPER = "scripts/adhoc/prepare_m5_future_views_20261117.py"
MIXED_DESCRIPTION_SHA256 = "5d1f1915951a1ebfed7d6cbe745bb5fa316f89054dea753b0c73871db2b3c5e8"


def bounded_description(raw, pointer):
    """Remove only three independently inspected status tokens from exact bytes."""
    source_hash = hashlib.sha256(raw).hexdigest()
    if source_hash != MIXED_DESCRIPTION_SHA256:
        raise ValueError("Mixed original description changed; inspect the semantic spans")
    markers = (
        (b"Reviewed source-local process meaning for ", 0, len(b"Reviewed ")),
        (b"Reviewed vocabulary: ", 0, len(b"Reviewed ")),
        (b"The reviewed vocabulary version", len(b"The "), len(b"reviewed ")),
    )
    omissions, retained, pieces = [], [], []
    cursor = 0
    for marker, prefix, length in markers:
        if raw.count(marker) != 1:
            raise ValueError("Review-status span missing or ambiguous")
        start = raw.index(marker) + prefix
        end = start + length
        if start < cursor:
            raise ValueError("Review-status spans are out of order")
        if cursor < start:
            retained.append({"pointer": pointer, "source_byte_start": cursor,
                             "source_byte_end": start,
                             "sha256": hashlib.sha256(raw[cursor:start]).hexdigest()})
            pieces.append(raw[cursor:start])
        omissions.append({"pointer": pointer, "source_field_sha256": source_hash,
                          "source_byte_start": start, "source_byte_end": end,
                          "sha256": hashlib.sha256(raw[start:end]).hexdigest(),
                          "offset_encoding": "UTF-8 bytes; zero-based half-open",
                          "scope": "review-status token only",
                          "reason": "Separable historical review status; semantic text retained"})
        cursor = end
    if cursor < len(raw):
        retained.append({"pointer": pointer, "source_byte_start": cursor,
                         "source_byte_end": len(raw),
                         "sha256": hashlib.sha256(raw[cursor:]).hexdigest()})
        pieces.append(raw[cursor:])
    return b"".join(pieces).decode(), omissions, retained


def projection(packet):
    view = prior.projection(packet)
    omissions, retained_semantics = [], []
    for item in view["blinding"]["redactions"]:
        _, _, side, _, field = item["pointer"].split("/")
        raw = packet["endpoints"][side]["record"][field].encode()
        text, spans, retained = bounded_description(raw, item["pointer"])
        view["endpoints"][side]["record"][field] = text
        omissions.extend(spans)
        retained_semantics.extend(retained)
    # Record the specific fields actually retained; no assertion that all producer
    # wording is inseparable or that a code string is necessarily substantive.
    exposed = [{"pointer": "/" + key, "sha256": hashlib.sha256(
        json.dumps(view[key], sort_keys=True, ensure_ascii=False).encode()).hexdigest()}
        for key in sorted(original.FIELDS)]
    view["blinding"] = {
        "version": VERSION, "bounded_omissions": omissions,
        "retained_semantic_spans": retained_semantics,
        "retained_field_bindings": exposed,
        "binding_encoding": "JSON sorted keys, ensure_ascii=false, default separators; UTF-8",
        "original_record_hashes": "Bind complete original endpoint records before omission",
        "exposure": (
            "The bound occurrence identity, assertion, endpoint fields, measurement context and "
            "source rows remain visible, including their original selection and any wording in "
            "those retained fields. The listed omissions remove only inspected review-status "
            "tokens from an exact mixed description. Its substantive definition, scope limits, "
            "source/version provenance and warning about the unknown generating version remain "
            "verbatim in the retained spans. Preserved wording is not independently validated "
            "meaning or a scientific verdict. Other definitions and counterevidence remain. "
            "This projection does not classify external producer prose or executable strings: "
            "their content-reviewed omissions require separate package-pinned span receipts. "
            "Code status alone does not make evaluation prose inseparable."
        ),
    }
    return view


def configuration():
    return {**prior.configuration(), HELPER: original.sha(ROOT / HELPER)}


def check(case, base):
    packet_path, packet, validation = original.load_case(case)
    receipt = original.read(base / case / "receipt.json")
    view_path = base / case / "view.json"
    expected = {"case_id": case, "configuration": configuration(),
                "packet_path": str(packet_path.relative_to(ROOT)),
                "packet_sha256": original.sha(packet_path),
                "view_sha256": original.sha(view_path), "validation": validation,
                "scientific_ratings": 0, "blinding": projection(packet)["blinding"]}
    if receipt != expected or original.read(view_path) != projection(packet):
        raise ValueError("Future view or bound configuration changed")
    return receipt


def prepare(case, base):
    base = original.checked(base, exists=False)
    if case != "fresh-47":
        check("fresh-47", base)
    packet_path, packet, validation = original.load_case(case)
    view = projection(packet)
    original.private_parents(base)
    folder = base / case
    folder.mkdir(mode=0o700)
    original.write_new(folder / "view.json", view)
    original.write_new(folder / "receipt.json", {
        "case_id": case, "configuration": configuration(),
        "packet_path": str(packet_path.relative_to(ROOT)),
        "packet_sha256": original.sha(packet_path),
        "view_sha256": original.sha(folder / "view.json"),
        "validation": validation, "scientific_ratings": 0, "blinding": view["blinding"],
    })
    return check(case, base)


def main():
    from pathlib import Path

    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--case")
    mode.add_argument("--check")
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    result = prepare(args.case, args.output_root) if args.case else check(args.check, args.output_root)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
