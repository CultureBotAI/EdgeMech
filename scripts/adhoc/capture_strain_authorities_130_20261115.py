#!/usr/bin/env python3
"""2026-11-15: capture one public strain authority for EdgeMech issue #130.

Inputs: one allowlisted public catalog URL selected by name; no credentials.
Outputs: exclusive private raw HTML, derivative text and hash/provenance receipt.
Run one authority end to end and inspect its artifacts before further captures.
Raw catalog bodies must remain gitignored. This does not adjudicate graph claims.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
URLS = {
    "dsm19353": "https://www.dsmz.de/collection/catalogue/details/culture/DSM-19353",
    "jcm14586": "https://www.jcm.riken.jp/cgi-bin/jcm/jcm_number?JCM=14586",
    "dsm18772": "https://www.dsmz.de/collection/catalogue/details/culture/DSM-18772",
    "bacdive17851": "https://bacdive.dsmz.de/strain/17851",
}
LIMIT = 4 * 1024 * 1024


class Text(HTMLParser):
    """Deterministic catalog text derivative, retaining content order."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.skip += 1
        if tag in {"p", "div", "br", "tr", "td", "li", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.skip = max(0, self.skip - 1)
        if tag in {"p", "div", "tr", "td", "li", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write_new(path, raw):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    if path.read_bytes() != raw:
        raise ValueError("Persisted artifact differs")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", choices=URLS)
    parser.add_argument("--plan", action="store_true")
    args = parser.parse_args()
    destination = ROOT / ".temp" / "identity130" / "authorities"
    for parent in (ROOT / ".temp", destination.parent, destination):
        if parent.is_symlink() or not parent.is_dir():
            raise ValueError("Prepare real private staging directories first")
        if stat.S_IMODE(parent.stat().st_mode) != 0o700:
            raise ValueError("Staging directories must be mode 0700")
    relative = destination.relative_to(ROOT) / (args.name + ".html")
    subprocess.run(["git", "check-ignore", "--no-index", "--quiet", str(relative)],
                   cwd=ROOT, check=True)
    paths = {kind: destination / (args.name + suffix) for kind, suffix in
             (("raw", ".html"), ("text", ".txt"), ("receipt", ".json"))}
    if any(path.exists() or path.is_symlink() for path in paths.values()):
        raise ValueError("Authority artifacts already exist; preserve prior capture")
    if args.plan:
        print(json.dumps({"url": URLS[args.name], "writes": 0, "provider_calls": 0,
                          "destination": str(destination.relative_to(ROOT))}))
        return 0
    fetched_at = datetime.now(timezone.utc).isoformat()
    request = urllib.request.Request(URLS[args.name], headers={"User-Agent": "EdgeMech/0.1"})
    with urllib.request.urlopen(request, timeout=60) as response:
        raw = response.read(LIMIT + 1)
        content_type = response.headers.get("Content-Type", "")
        charset = response.headers.get_content_charset() or "utf-8"
        status, final_url = response.status, response.url
    if status != 200 or not raw or len(raw) > LIMIT or "html" not in content_type.lower():
        raise ValueError("Expected one nonempty bounded HTML authority response")
    extractor = Text()
    extractor.feed(raw.decode(charset, errors="strict"))
    text = "\n".join(" ".join(line.split()) for line in "".join(extractor.parts).splitlines()
                     if line.strip()) + "\n"
    text_raw = text.encode("utf-8")
    if not text.strip():
        raise ValueError("Authority response has no readable text")
    receipt = {"name": args.name, "requested_url": URLS[args.name], "final_url": final_url,
               "fetched_at": fetched_at, "status": status, "content_type": content_type,
               "charset": charset, "raw_bytes": len(raw), "raw_sha256": sha(raw),
               "text_bytes": len(text_raw), "text_sha256": sha(text_raw),
               "extractor": "catalog-html-text/v1", "authenticated": False,
               "channel": "anonymous_primary_catalog", "http_calls": 1,
               "scope": "One public catalog page; identity still requires authored assessment",
               "raw_path": str(paths["raw"].relative_to(ROOT)),
               "text_path": str(paths["text"].relative_to(ROOT)),
               "script_sha256": sha(Path(__file__).read_bytes())}
    write_new(paths["raw"], raw)
    write_new(paths["text"], text_raw)
    write_new(paths["receipt"], (json.dumps(receipt, indent=2) + "\n").encode())
    if json.loads(paths["receipt"].read_text()) != receipt:
        raise ValueError("Persisted receipt differs")
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
