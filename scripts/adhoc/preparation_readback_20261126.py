#!/usr/bin/env python3
"""Replay private library bytes or one canonical engineering review pair.

Purpose: excluded native preparation, issue228 provenance; no occurrence adapter.
Inputs: retained Valency response or exact canonical review.yaml path.
Outputs: append-only private identity/offset/hash or canonical-readback receipts.
UTC date: 2026-11-26; native worker units 2/3. Does not contact any provider.
Issues236/237 repaired after triage; issue228 executed original retained at SHA256
572e1c4680872eb9a860ecec5c1ecd48958076718081dc823e6d2ec9c50aade2.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

from preparation_receipt_20261126 import (
    BASE,
    ROOT,
    checked_path,
    directory,
    pin,
    read_regular,
    utc,
    write_new,
)


def strict_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result

    def invalid_constant(value):
        raise ValueError("Nonfinite JSON constant")

    return json.loads(raw, object_pairs_hook=unique, parse_constant=invalid_constant)


def validate_data(data):
    if not isinstance(data, dict) or data.get("found") is not True:
        raise ValueError("Expected successful paper object")
    if data.get("paper_id") != "17625207" or data.get("query_type") != "paper_by_id":
        raise ValueError("Wrong lookup identity")
    warnings = data.get("warnings")
    if not isinstance(warnings, list) or any(not isinstance(w, str) for w in warnings):
        raise ValueError("Malformed warnings")
    paper, meta = data.get("paper"), data.get("_meta")
    if not isinstance(paper, dict) or not isinstance(meta, dict):
        raise ValueError("Expected paper and metadata mappings")
    expected = {
        "id": "17625207", "base_id": "17625207", "doi": "10.1099/ijs.0.65010-0",
        "title": "Rubritalea squalenifaciens sp. nov., a squalene-producing marine bacterium "
                 "belonging to subdivision 1 of the phylum 'Verrucomicrobia'.",
        "source": "pubmed", "url": "https://pubmed.ncbi.nlm.nih.gov/17625207/",
        "journal_ref": "International journal of systematic and evolutionary microbiology. "
                       "2007;57(Pt 7):1630-1634",
    }
    if any(type(paper.get(k)) is not str or paper[k] != v for k, v in expected.items()):
        raise ValueError("Publication identity does not match retained fresh05 metadata")
    abstract = paper.get("abstract")
    if not isinstance(abstract, str) or not abstract.strip() or len(abstract.encode()) > 1024 * 1024:
        raise ValueError("Malformed or oversized abstract")
    for key in ("request_id", "tool", "server_version"):
        if not isinstance(meta.get(key), str) or not meta[key].strip() or len(meta[key]) > 512:
            raise ValueError("Malformed request metadata")
    if (meta["tool"] != "get_paper_by_id" or type(meta.get("duration_ms")) is not int
            or meta["duration_ms"] < 0):
        raise ValueError("Malformed provider metadata")
    return data


def validate_envelope(response):
    if not isinstance(response, dict) or response.get("isError", False) is not False:
        raise ValueError("MCP error or malformed envelope")
    content = response.get("content")
    if not isinstance(content, list) or len(content) != 1:
        raise ValueError("Expected one text content block")
    block = content[0]
    if (not isinstance(block, dict) or block.get("type") != "text"
            or not isinstance(block.get("text"), str)):
        raise ValueError("Malformed MCP text block")
    data = validate_data(strict_json(block["text"]))
    if "structuredContent" in response:
        structured = validate_data(response["structuredContent"])
        # Canonical encoding also distinguishes bool/int and float/int values.
        if json.dumps(structured, sort_keys=True) != json.dumps(data, sort_keys=True):
            raise ValueError("Structured and textual provider responses differ")
    return data


def library():
    path = BASE / "library/response-01.json"
    checked_path(BASE / "library/abstract-01.txt", "file", absent=True)
    request_pin = pin(BASE / "library/request-01.json")
    original = read_regular(path)
    data = validate_envelope(strict_json(original))
    paper = data["paper"]
    abstract = paper["abstract"]
    quote = "was a non-motile, rod-shaped"
    if abstract.count(quote) != 1:
        raise ValueError("Expected one exact bounded snippet")
    start = abstract.index(quote)
    end = start + len(quote)
    raw = abstract.encode("utf-8")
    bstart = len(abstract[:start].encode("utf-8"))
    bend = bstart + len(quote.encode("utf-8"))
    abstract_pin = write_new(BASE / "library/abstract-01.txt", raw)
    reread = read_regular(BASE / "library/abstract-01.txt")
    if reread[bstart:bend] != quote.encode() or read_regular(path) != original:
        raise ValueError("Saved bytes changed or literal replay failed")
    return {
        "timestamp_utc": utc(), "classification": "EXCLUDED_PREPARATION_CANARY",
        "scientific_review_coverage": 0, "occurrence": None,
        "provider": "valency", "provider_request_count": 1,
        "request_id": data["_meta"]["request_id"], "provider_metadata": data["_meta"],
        "request": request_pin, "response": pin(path),
        "response_representation": "JSON serialization of actual exposed MCP tool result; not HTTP wire bytes",
        "identity": {k: paper[k] for k in ("id", "doi", "title", "journal_ref", "url")},
        "identity_verified": True, "inspected_extent": "metadata and complete returned abstract",
        "body_read": False, "tables_read": False, "figures_read": False,
        "original_pdf_obtained": False, "fulltext_ready": False,
        "native_scientific_proof_admitted": False,
        "proof_limit": "Valency JSON is access evidence; pinned adapter accepts Europe PMC core JSON or JATS, not this representation.",
        "abstract": abstract_pin, "quote": quote, "quote_words": len(quote.split()),
        "quote_sha256": hashlib.sha256(quote.encode()).hexdigest(),
        "character_offsets_zero_based_end_exclusive": [start, end],
        "utf8_byte_offsets_zero_based_end_exclusive": [bstart, bend],
        "literal_replay": "passed", "fulltext_provider_sweep": False,
    }


def canonical(path):
    from kg_microbe_governance.artifacts.scripts import record_review

    from edgemech.pins import check_contracts

    path = checked_path(path, "file", base=ROOT, required=True)
    contracts = check_contracts()
    relative = str(path.relative_to(ROOT))
    markdown = path.with_name("review.md")
    before = [pin(path), pin(markdown)]
    review = record_review.read_review(ROOT, relative, ROOT / "schema/record_review.yaml")
    if review["scientific_review"] is not False or review["kind"] != "repository":
        raise ValueError("Expected non-scientific repository review")
    if {t["path"] for t in review["targets"]} != {
        "pyproject.toml", "docs/record-review-profile.md",
    }:
        raise ValueError("Unexpected target outside engineering canary scope")
    for item in review["source"]["inputs"]:
        if pin(ROOT / item["path"])["sha256"] != item["sha256"]:
            raise ValueError("Current input hash differs")
    after = [pin(path), pin(markdown)]
    if before != after or any(p["bytes"] == 0 for p in after):
        raise ValueError("Empty or changed saved canonical pair")
    return {"timestamp_utc": utc(), "classification": "EXCLUDED_PREPARATION_CANARY",
            "scientific_review_coverage": 0, "occurrence": None, "A_B_attempt": False,
            "contracts": contracts, "review_id": review["review_id"], "artifacts": after,
            "canonical_read_review": "passed", "input_hash_replay": "passed",
            "markdown_regeneration": "passed by canonical read_review",
            "source_provenance": record_review.source_provenance(ROOT, review)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("library", "canonical"))
    parser.add_argument("--review", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    output = checked_path(args.output, "file", absent=True)
    with directory(output.parent):
        pass
    if args.mode == "canonical" and args.review is None:
        parser.error("Canonical mode requires --review")
    result = library() if args.mode == "library" else canonical(args.review.absolute())
    receipt = write_new(output, (json.dumps(result, indent=2) + "\n").encode())
    print(json.dumps({"receipt": receipt, "result": result}))


if __name__ == "__main__":
    main()
