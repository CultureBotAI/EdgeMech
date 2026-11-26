#!/usr/bin/env python3
"""One anonymous Europe PMC request with immutable private response/receipt.

This helper fetches evidence bytes only. It does not infer entailment, produce a
review, or follow publisher links. Run and inspect one request before a batch.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--pmid")
    group.add_argument("--pmcid")
    group.add_argument("--ncbi-taxid")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.pmid and not args.pmid.isdigit():
        parser.error("PMID must be decimal digits")
    if args.pmcid and not (args.pmcid.startswith("PMC") and args.pmcid[3:].isdigit()):
        parser.error("PMCID must be PMC followed by decimal digits")
    if args.ncbi_taxid and not args.ncbi_taxid.isdigit():
        parser.error("NCBI TaxID must be decimal digits")
    if args.output.exists():
        parser.error("output must not already exist")
    args.output.mkdir(parents=True, mode=0o700)
    os.chmod(args.output, 0o700)
    base = "https://www.ebi.ac.uk/europepmc/webservices/rest/"
    url = (
        base + "search?" + urlencode({"query": f"EXT_ID:{args.pmid} AND SRC:MED",
                                    "resultType": "core", "format": "json", "pageSize": 10})
        if args.pmid else (
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?" + urlencode(
                {"db": "taxonomy", "id": args.ncbi_taxid, "retmode": "xml"})
            if args.ncbi_taxid else base + args.pmcid + "/fullTextXML")
    )
    receipt = {
        "request": {"method": "GET", "url": url, "headers": {"User-Agent": "EdgeMech-evidence/1"}},
        "started_at": datetime.now(timezone.utc).isoformat(),
        "authenticated": False,
        "scientific_assessment": "none",
    }
    try:
        with urlopen(Request(url, headers={"User-Agent": "EdgeMech-evidence/1"}), timeout=45) as response:
            raw = response.read(20_000_001)
            if len(raw) > 20_000_000:
                raise ValueError("response exceeded 20 MB bounded request")
            receipt.update(http_status=response.status, final_url=response.url)
        name = "response.json" if args.pmid else "response.xml"
        destination = args.output / name
        with destination.open("xb") as handle:
            handle.write(raw)
        os.chmod(destination, 0o600)
        receipt.update(response=name, sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
        if args.pmid:
            hits = json.loads(raw)["resultList"]["result"]
            exact = [x for x in hits if x.get("id") == args.pmid and x.get("source") == "MED"]
            if len(exact) != 1:
                raise ValueError("expected exactly one primary PMID match")
            receipt["identity"] = {k: exact[0].get(k) for k in ("id", "source", "doi", "pmcid", "title")}
        receipt["status"] = "persisted"
    except Exception as error:
        receipt.update(status="failed", error_type=type(error).__name__, error=str(error))
        raise
    finally:
        receipt["finished_at"] = datetime.now(timezone.utc).isoformat()
        with (args.output / "receipt.json").open("x") as handle:
            json.dump(receipt, handle, indent=2)
            handle.write("\n")
        os.chmod(args.output / "receipt.json", 0o600)
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
