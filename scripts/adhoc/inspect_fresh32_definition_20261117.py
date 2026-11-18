#!/usr/bin/env python3
"""Inspect exact fresh32 mixed-description spans for issue210, 2026-11-17.

Input: immutable original packet. Output: exclusive private JSON span inventory;
no source quotations or scientific labels. This is not an omission authorization.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

PACKET_SHA256 = "14b21623a1726591121ea2882d9168e081f832e22143a58cad438163551326f7"


def inspect(packet_path: Path, output: Path, *, project: bool = False) -> dict:
    if output.exists() or output.is_symlink():
        raise ValueError("Inspection output already exists")
    raw = packet_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PACKET_SHA256:
        raise ValueError("Original fresh32 packet changed")
    packet = json.loads(raw)
    description = packet["endpoints"]["object"]["record"]["description"].encode()
    markers = [
        (b"Reviewed source-local process meaning for ", 0, len(b"Reviewed ")),
        (b"Reviewed vocabulary: ", 0, len(b"Reviewed ")),
        (b"The reviewed vocabulary version", len(b"The "), len(b"reviewed ")),
    ]
    spans = []
    for marker, prefix, length in markers:
        if description.count(marker) != 1:
            raise ValueError("Original review-status marker is missing or ambiguous")
        start = description.index(marker) + prefix
        spans.append({"source_byte_start": start, "source_byte_end": start + length,
                      "sha256": hashlib.sha256(description[start:start + length]).hexdigest()})
    result = {"schema": "edgemech-fresh32-description-inspection/v1",
              "packet_sha256": PACKET_SHA256,
              "source_pointer": "/endpoints/object/record/description",
              "source_field_sha256": hashlib.sha256(description).hexdigest(),
              "source_bytes": len(description), "candidate_omissions": spans,
              "offset_encoding": "UTF-8 bytes; zero-based half-open",
              "scope": "inspection_only_no_scientific_rating_or_omission_authorization"}
    if project:
        import prepare_m5_future_views_20261117 as future

        view = future.projection(packet)
        actual = view["endpoints"]["object"]["record"]["description"].encode()
        cursor = 0
        retained = []
        for span in spans:
            retained.append(description[cursor:span["source_byte_start"]])
            cursor = span["source_byte_end"]
        retained.append(description[cursor:])
        if actual != b"".join(retained):
            raise ValueError("Projection changed bytes beyond independently inspected spans")
        for key in set(future.original.FIELDS) - {"endpoints"}:
            if view[key] != packet[key]:
                raise ValueError(f"Projection changed retained field: {key}")
        for side in packet["endpoints"]:
            original_endpoint = dict(packet["endpoints"][side])
            expected_record = dict(original_endpoint["record"])
            if side == "object":
                expected_record["description"] = actual.decode()
            original_endpoint["record"] = expected_record
            if original_endpoint != view["endpoints"][side]:
                raise ValueError("Projection changed endpoint beyond inspected description spans")
        projected_path = output.with_suffix(".view.json")
        output.parent.mkdir(parents=True, exist_ok=True)
        with projected_path.open("x") as stream:
            os.fchmod(stream.fileno(), 0o600)
            json.dump(view, stream, indent=2, sort_keys=True)
            stream.write("\n")
        if json.loads(projected_path.read_bytes()) != view:
            raise ValueError("Projection failed persisted readback")
        result["projection"] = {
            "path": str(projected_path),
            "sha256": hashlib.sha256(projected_path.read_bytes()).hexdigest(),
            "helper_sha256": hashlib.sha256(Path(future.__file__).read_bytes()).hexdigest(),
            "projected_description_sha256": hashlib.sha256(actual).hexdigest(),
            "source_bytes": len(description), "retained_bytes": len(actual),
            "omitted_bytes": len(description) - len(actual),
            "blinding": view["blinding"],
            "outside_span_changes": 0,
            "scientific_ratings": 0,
        }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as stream:
        os.fchmod(stream.fileno(), 0o600)
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write("\n")
    if json.loads(output.read_bytes()) != result:
        raise ValueError("Inspection report failed persisted readback")
    return {"output": str(output), "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            "source_field_sha256": result["source_field_sha256"], "candidate_spans": spans}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--project", action="store_true")
    args = parser.parse_args()
    print(json.dumps(inspect(args.packet, args.output, project=args.project), sort_keys=True))


if __name__ == "__main__":
    main()
