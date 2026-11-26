#!/usr/bin/env python3
"""Replay private library bytes or one canonical engineering review pair.

Purpose: excluded native preparation, issue228 provenance; no occurrence adapter.
Inputs: retained Valency response or exact canonical review.yaml path.
Outputs: append-only private identity/offset/hash or canonical-readback receipts.
UTC date: 2026-11-26; native worker units 2/3. Does not contact any provider.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

from preparation_receipt_20261126 import BASE, ROOT, pin, utc, write_new


def library():
    path = BASE / "library/response-01.json"
    original = path.read_bytes()
    response = json.loads(original)
    texts = [json.loads(c["text"]) for c in response["content"] if c["type"] == "text"]
    if len(texts) != 1:
        raise ValueError("Expected one retained provider text response")
    data = texts[0]
    if response.get("structuredContent") and response["structuredContent"] != data:
        raise ValueError("Structured and textual provider responses differ")
    paper = data["paper"]
    if not (data["found"] and paper["id"] == "17625207"
            and paper["doi"] == "10.1099/ijs.0.65010-0"
            and paper["title"] == "Rubritalea squalenifaciens sp. nov., a squalene-producing "
            "marine bacterium belonging to subdivision 1 of the phylum 'Verrucomicrobia'."
            and paper["source"] == "pubmed"
            and "2007;57(Pt 7):1630-1634" in paper["journal_ref"]):
        raise ValueError("Publication identity does not match retained fresh05 metadata")
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
    reread = (BASE / "library/abstract-01.txt").read_bytes()
    if reread[bstart:bend] != quote.encode() or path.read_bytes() != original:
        raise ValueError("Saved bytes changed or literal replay failed")
    return {
        "timestamp_utc": utc(), "classification": "EXCLUDED_PREPARATION_CANARY",
        "scientific_review_coverage": 0, "occurrence": None,
        "provider": "valency", "provider_request_count": 1,
        "request_id": data["_meta"]["request_id"], "provider_metadata": data["_meta"],
        "request": pin(BASE / "library/request-01.json"), "response": pin(path),
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
    output = args.output.absolute()
    output.relative_to(BASE)
    if any(p.is_symlink() for p in (output, *output.parents)):
        raise ValueError("Symlink output")
    result = library() if args.mode == "library" else canonical(args.review.absolute())
    receipt = write_new(output, (json.dumps(result, indent=2) + "\n").encode())
    print(json.dumps({"receipt": receipt, "result": result}))


if __name__ == "__main__":
    main()
