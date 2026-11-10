"""One anonymous, durable Europe PMC retrieval probe; no entailment judgments.

This is a single-request canary, not a bulk scheduler. Bulk deployment still
requires a shared provider limiter, retry policy and a versioned document cache.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from kg_microbe_curation.identity import CurationError

from .content_inventory import _write_json
from .storage.parquet import file_hash, safe_path

MAX_RESPONSE_BYTES = 4 * 1024 * 1024


def identifier(value: str):
    """Restrict requests to explicit DOI/PMID identifiers, never arbitrary queries."""
    if value.startswith("PMID:") and re.fullmatch(r"[1-9][0-9]*", value[5:]):
        return "pmid", value[5:]
    cleaned = re.sub(r"^(?:doi:|https://(?:dx\.)?doi\.org/)", "", value, flags=re.I)
    if re.fullmatch(r"10\.[0-9]{4,9}/[^\s\"\\@]+", cleaned):
        return "doi", cleaned.lower()
    raise CurationError("Expected an explicit DOI or PMID identifier")


def matching_record(data, kind, value):
    """A first search hit is insufficient: require exactly one identifier match."""
    results = data.get("resultList", {}).get("result", [])
    matches = []
    for result in results:
        if kind == "doi" and str(result.get("doi", "")).lower() == value:
            matches.append(result)
        elif kind == "pmid" and result.get("source") == "MED" and str(result.get("id")) == value:
            matches.append(result)
    # Refuse truncated searches as well as missing/ambiguous exact matches.
    if data.get("hitCount", 0) > len(results) or len(matches) != 1:
        return None
    return matches[0]


def probe(identifier_value: str, output: Path):
    kind, value = identifier(identifier_value)
    query = f'DOI:"{value}"' if kind == "doi" else f"EXT_ID:{value} AND SRC:MED"
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urllib.parse.urlencode({
        "query": query, "resultType": "core", "format": "json", "pageSize": "10",
    })
    output = safe_path(output, exists=False)
    output.mkdir()
    request = urllib.request.Request(url, headers={
        "User-Agent": "EdgeMech-literature-canary/1", "Accept": "application/json",
    })
    # Fail visibly on network/HTTP errors; an incomplete directory is not a cache hit.
    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read(MAX_RESPONSE_BYTES + 1)
        status = response.status
    if status != 200 or not raw or len(raw) > MAX_RESPONSE_BYTES:
        raise CurationError("Unexpected or oversized literature response")
    path = output / "response.json"
    with path.open("xb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    digest = hashlib.sha256(raw).hexdigest()
    if file_hash(path) != digest:
        raise CurationError("Literature response persistence mismatch")
    data = json.loads(path.read_bytes())
    result = matching_record(data, kind, value)
    abstract = result.get("abstractText") if result else None
    receipt = {
        "artifact_type": "literature-retrieval-probe/v1", "identifier_kind": kind,
        "identifier": value, "request_url": url,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "response_sha256": digest, "response_bytes": len(raw),
        "status": "ambiguous_or_missing_identifier" if result is None else (
            "abstract_available" if abstract else "abstract_unavailable"
        ),
        "matched_identifier": value if result else None,
        "abstract_field": "resultList.result[].abstractText" if abstract else None,
        "quote_verified": False, "claim_support": "unassessed",
        "scientific_approvals": 0,
        "limitations": ["Retrieved abstract may contain XML markup.",
                        "Availability and identifier equality do not establish edge support.",
                        "One request does not test rate limiting, retries or bulk throughput."],
    }
    _write_json(output / "manifest.json", receipt)
    return receipt
