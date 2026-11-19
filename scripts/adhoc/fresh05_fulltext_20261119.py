#!/usr/bin/env python3
"""Find exact fresh05 local attachments or retain one anonymous public response.

Inputs: local Zotero SQLite or an explicitly selected legal public HTTPS URL.
Outputs: private, exclusive evidence and readback receipts beneath .temp.
Serves content-review W4 / #213, 2026-11-19; never changes scientific ratings.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

DOI = "10.1099/ijs.0.65010-0"
PMID = "17625207"
MAX_BYTES = 20 * 1024 * 1024
ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / ".temp/content-review-20261119/literature/fresh05-access"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def save(path, data):
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    assert path.read_bytes() == data
    return {"path": str(path.relative_to(ROOT)), "sha256": digest(data), "bytes": len(data)}


def local(zotero):
    db = zotero / "zotero.sqlite"
    with sqlite3.connect(db.as_uri() + "?mode=ro", uri=True) as conn:
        conn.execute("PRAGMA query_only=ON")
        matches = conn.execute(
            "SELECT DISTINCT d.itemID FROM itemData d "
            "JOIN itemDataValues v ON v.valueID=d.valueID "
            "WHERE lower(v.value) LIKE ? OR v.value LIKE ? OR lower(v.value) LIKE ?",
            ("%" + DOI + "%", "%" + PMID + "%", "%rubritalea squalenifaciens%"),
        ).fetchall()
        result = []
        for (item_id,) in matches:
            fields = conn.execute(
                "SELECT f.fieldName,v.value FROM itemData d "
                "JOIN itemDataValues v ON v.valueID=d.valueID "
                "JOIN fields f ON f.fieldID=d.fieldID WHERE d.itemID=? "
                "AND f.fieldName IN ('title','DOI','url','extra','publicationTitle')",
                (item_id,),
            ).fetchall()
            attachments = []
            for key, path in conn.execute(
                "SELECT i.key,a.path FROM itemAttachments a "
                "JOIN items i ON i.itemID=a.itemID WHERE a.parentItemID=?", (item_id,),
            ):
                if path and path.startswith("storage:"):
                    full = zotero / "storage" / key / path.removeprefix("storage:")
                    attachments.append({"path": str(full), "exists": full.is_file(),
                                        "sha256": digest(full.read_bytes()) if full.is_file() else None})
            result.append({"item_id": item_id, "fields": dict(fields), "attachments": attachments})
    return {"database": str(db), "database_sha256": digest(db.read_bytes()),
            "query_scope": "read-only Zotero itemData values: DOI, PMID or exact species phrase; attachment metadata for matching items",
            "matches": result}


def fetch(url):
    if urlparse(url).scheme != "https" or urlparse(url).username or urlparse(url).password:
        raise ValueError("Only anonymous HTTPS is allowed")
    request = Request(url, headers={"User-Agent": "EdgeMech-evidence-check/20261119",
                                    "Accept": "application/json,text/html,application/pdf,*/*"})
    try:
        response = urlopen(request, timeout=45)
    except HTTPError as exc:
        response = exc
    with response:
        body = response.read(MAX_BYTES + 1)
        if len(body) > MAX_BYTES:
            raise ValueError("Response exceeds evidence limit")
        meta = {"requested_url": url, "final_url": response.geturl(),
                "status": response.code, "content_type": response.headers.get("Content-Type"),
                "content_length_header": response.headers.get("Content-Length"),
                "anonymous": True, "credentials_used": False}
    return body, meta


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("local", "fetch"))
    parser.add_argument("--unit", required=True)
    parser.add_argument("--zotero", type=Path, default=Path("/Users/marcin/Zotero"))
    parser.add_argument("--url")
    args = parser.parse_args()
    if not args.unit.replace("-", "").isalnum():
        raise ValueError("Invalid unit")
    os.umask(0o077)
    output = BASE / args.unit
    if any(path.is_symlink() for path in (output, *output.parents)):
        raise ValueError("Symlink evidence destination")
    output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    output.mkdir(mode=0o700)
    receipt = {"doi": DOI, "pmid": PMID, "action": args.action,
               "time_utc": datetime.now(timezone.utc).isoformat(),
               "script_sha256": digest(Path(__file__).read_bytes()),
               "scientific_assessment": False}
    if args.action == "local":
        result = local(args.zotero)
        receipt["match_count"] = len(result["matches"])
        receipt["artifact"] = save(output / "local.json", json.dumps(result, indent=2).encode())
    else:
        body, meta = fetch(args.url)
        receipt.update(meta)
        receipt["artifact"] = save(output / "response", body)
    receipt_pin = save(output / "receipt.json", json.dumps(receipt, indent=2).encode())
    print(json.dumps({"receipt": receipt_pin, "match_count": receipt.get("match_count"),
                      "status": receipt.get("status"), "artifact": receipt["artifact"]}, indent=2))


if __name__ == "__main__":
    main()
