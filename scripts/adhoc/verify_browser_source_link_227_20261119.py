"""Verify one advertised raw manifest over HTTP; build/site in, receipt out; #227, 2026-11-19."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("receipt destination must be new")
    data = json.loads((args.site / "sample.json").read_bytes())
    source = next(item for item in data["provenance"]
                  if item["path"] == "artifacts/edge-sample-review-20261112/manifest.jsonl")
    url = source["download_url"]
    expected_url = ("https://raw.githubusercontent.com/CultureBotAI/EdgeMech/"
                    f'{data["source_commit"]}/{source["path"]}')
    if url != expected_url or "#" in url:
        raise ValueError("source link is not the exact pinned raw manifest")
    request = Request(url, headers={"User-Agent": "EdgeMech-public-source-verification/1"})
    with urlopen(request, timeout=60) as response:
        status, final_url = response.status, response.url
        content_type = response.headers.get("Content-Type", "")
        raw = response.read(source["bytes"] + 1)
    if status != 200 or final_url != url or "html" in content_type.lower():
        raise ValueError("advertised link did not serve the raw artifact")
    actual_sha = hashlib.sha256(raw).hexdigest()
    if len(raw) != source["bytes"] or actual_sha != source["sha256"]:
        raise ValueError("HTTP artifact bytes differ from the pinned browser source")
    rows = [json.loads(line) for line in raw.splitlines()]
    if len(rows) != data["counts"]["public_sample"]:
        raise ValueError("downloaded manifest cardinality differs")
    for record in data["records"]:
        original = rows[record["source_line"] - 1]
        if any(record[key] != original[key] for key in (
                "occurrence_id", "subject", "predicate", "object")):
            raise ValueError("visible source line does not resolve to the advertised original claim")
    args.output.mkdir(parents=True)
    (args.output / "manifest.jsonl").write_bytes(raw)
    if (args.output / "manifest.jsonl").read_bytes() != raw:
        raise ValueError("download was not persisted intact")
    receipt = {"issue": 227, "date": "2026-11-19", "source_commit": data["source_commit"],
               "url": url, "final_url": final_url, "http_status": status,
               "content_type": content_type, "bytes": len(raw), "sha256": actual_sha,
               "source_rows": len(rows), "verified_public_record_lines": len(data["records"]),
               "persisted_artifact": "manifest.jsonl", "original_tuples_preserved": True}
    (args.output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
