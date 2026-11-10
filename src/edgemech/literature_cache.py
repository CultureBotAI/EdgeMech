"""Anonymous, serialized retrieval with durable cache, bounded retries and quote proofs."""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import random
import re
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path

from kg_microbe_curation.identity import CurationError

from .content_inventory import _space, _write_json
from .evidence_campaign import load_cohort
from .literature_probe import identifier, matching_record
from .storage.parquet import file_hash, safe_path

LEGACY_EXTRACTOR = "edgemech-literal-text/v1"
EXTRACTOR = "edgemech-literal-text/v2"
BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest/"
MAX_BYTES = 8 * 1024**2


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

    def handle_starttag(self, tag, attrs):
        if tag in {"p", "h1", "h2", "h3", "h4", "br", "div", "li"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"p", "h1", "h2", "h3", "h4", "div", "li"}:
            self.parts.append("\n")


def abstract_text(markup):
    parser = TextExtractor()
    parser.feed(markup)
    return "".join(parser.parts).strip()


def _full_text_sections(raw, pmcid):
    root = ET.fromstring(raw)
    ids = [element.text for element in root.findall("./front/article-meta/article-id")
           if element.get("pub-id-type") in {"pmc", "pmcid"}]
    if not any(str(value).removeprefix("PMC") == pmcid.removeprefix("PMC") for value in ids):
        raise CurationError("Full-text identity mismatch")
    sections = root.findall("./front/article-meta/title-group/article-title")
    sections += root.findall("./front/article-meta/abstract") + root.findall("./body")
    return sections


def _legacy_full_text(raw, pmcid):
    """Replay v1 artifacts for audit only; v1 OA text cannot support new quote proofs."""
    return "\n\n".join("".join(section.itertext())
                       for section in _full_text_sections(raw, pmcid)).strip()


def full_text(raw, pmcid):
    # JATS block boundaries must not manufacture word adjacency. Inline elements
    # retain adjacency, including H<sub>2</sub>. Offsets refer to this derivative.
    blocks = {"abstract", "article-title", "body", "sec", "title", "p", "break",
              "table-wrap", "table", "thead", "tbody", "tfoot", "tr", "td", "th",
              "caption", "fig", "list", "list-item", "def-list", "def-item", "def",
              "disp-formula", "boxed-text", "fn-group", "fn", "statement", "speech",
              "verse-line", "ref-list", "app-group", "app", "ack"}

    def parts(element):
        block = element.tag.rsplit("}", 1)[-1] in blocks
        if block:
            yield "\n"
        if element.text:
            yield element.text
        for child in element:
            yield from parts(child)
            if child.tail:
                yield child.tail
        if block:
            yield "\n"

    return "\n\n".join("".join(parts(section)).strip()
                       for section in _full_text_sections(raw, pmcid)).strip()


def retry_delay(value, now):
    if value is None:
        return None
    try:
        return max(0, float(value))
    except ValueError:
        try:
            return max(0, parsedate_to_datetime(value).timestamp() - now)
        except (ValueError, TypeError, OverflowError):
            return None


class LiteratureCache:
    """One shared directory is one provider queue; flock prevents concurrent senders."""
    def __init__(self, root: Path, *, opener=urllib.request.urlopen, clock=time.time,
                 sleeper=time.sleep, interval=1.0):
        self.root = safe_path(root, exists=False)
        self.root.mkdir(exist_ok=True)
        self.opener, self.clock, self.sleep, self.interval = opener, clock, sleeper, interval
        self.lock = None
        self.db = None

    def __enter__(self):
        self.lock = safe_path(self.root / "provider.lock", exists=False).open("a+")
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            self.lock.close()
            raise CurationError("Provider cache is busy; reuse the same queue after it finishes") from error
        self.db = sqlite3.connect(safe_path(self.root / "cache.sqlite", exists=False))
        self.db.execute("CREATE TABLE IF NOT EXISTS cache(key TEXT PRIMARY KEY, "
                        "expires REAL NOT NULL, record TEXT NOT NULL)")
        self.db.execute("CREATE TABLE IF NOT EXISTS provider(id INTEGER PRIMARY KEY, next_at REAL)")
        self.db.execute("INSERT OR IGNORE INTO provider VALUES(1,0)")
        self.db.execute("CREATE TABLE IF NOT EXISTS attempts(key TEXT,url TEXT,time REAL,status TEXT)")
        self.db.commit()
        return self

    def __exit__(self, *args):
        self.db.close()
        fcntl.flock(self.lock, fcntl.LOCK_UN)
        self.lock.close()

    def _cached(self, key):
        row = self.db.execute("SELECT expires,record FROM cache WHERE key=?", (key,)).fetchone()
        if row and row[0] > self.clock():
            record = json.loads(row[1])
            if record.get("response_sha256"):
                self.raw(record)
            return {**record, "cache_hit": True}
        return None

    def raw(self, record):
        digest = record.get("response_sha256")
        if (not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest)
                or record.get("response_path") != f"{digest}.response"):
            raise CurationError("Cached response requires a canonical content-addressed basename")
        path = safe_path(self.root / record["response_path"])
        if file_hash(path) != digest:
            raise CurationError("Cached response integrity mismatch")
        return path.read_bytes()

    def _store(self, key, record, ttl):
        self.db.execute("INSERT OR REPLACE INTO cache VALUES(?,?,?)",
                        (key, self.clock() + ttl, json.dumps(record, sort_keys=True)))
        self.db.commit()
        return {**record, "cache_hit": False}

    def request(self, key, url):
        cached = self._cached(key)
        if cached:
            return cached
        record = {"key": key, "url": url, "retrieved_at": datetime.now(timezone.utc).isoformat()}
        for attempt in range(3):
            _space(self.root, 2 * 1024**3)
            next_at = self.db.execute("SELECT next_at FROM provider WHERE id=1").fetchone()[0]
            delay = max(0, next_at - self.clock())
            if delay > 15:
                return self._store(key, {**record, "status": "retry_later", "retry_at": next_at}, delay)
            self.sleep(delay)
            self.db.execute("UPDATE provider SET next_at=? WHERE id=1", (self.clock() + self.interval,))
            self.db.commit()
            try:
                request = urllib.request.Request(url, headers={
                    "User-Agent": "EdgeMech-evidence-campaign/1", "Accept": "application/json, application/xml",
                })
                with self.opener(request, timeout=25) as response:
                    raw = response.read(MAX_BYTES + 1)
                    if response.status != 200 or not raw or len(raw) > MAX_BYTES:
                        raise CurationError("Empty, oversized or non-200 response")
                digest = hashlib.sha256(raw).hexdigest()
                path = self.root / f"{digest}.response"
                if path.exists():
                    if file_hash(path) != digest:
                        raise CurationError("Content-addressed response collision")
                else:
                    with path.open("xb") as handle:
                        handle.write(raw)
                        handle.flush()
                        os.fsync(handle.fileno())
                self.db.execute("INSERT INTO attempts VALUES(?,?,?,?)", (key, url, self.clock(), "200"))
                return self._store(key, {**record, "status": "retrieved", "response_sha256": digest,
                                        "response_path": path.name, "response_bytes": len(raw)}, 30 * 86400)
            except urllib.error.HTTPError as error:
                self.db.execute("INSERT INTO attempts VALUES(?,?,?,?)",
                                (key, url, self.clock(), str(error.code)))
                retry = error.code in {429, 500, 502, 503, 504}
                wait = retry_delay(error.headers.get("Retry-After"), self.clock())
                wait = wait if wait is not None else 2 ** (attempt + 1) + random.uniform(0, 0.25)
                if retry:
                    self.db.execute("UPDATE provider SET next_at=max(next_at,?) WHERE id=1",
                                    (self.clock() + wait,))
                self.db.commit()
                if not retry:
                    return self._store(key, {**record, "status": f"http_{error.code}"}, 86400)
            except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
                self.db.execute("INSERT INTO attempts VALUES(?,?,?,?)",
                                (key, url, self.clock(), type(error).__name__))
                self.db.execute("UPDATE provider SET next_at=max(next_at,?) WHERE id=1",
                                (self.clock() + 2 ** (attempt + 1),))
                self.db.commit()
        return self._store(key, {**record, "status": "retry_exhausted"}, 300)

    def document(self, reference):
        kind, value = reference.split(":", 1)
        identifier(("PMID:" if kind == "pmid" else "doi:") + value)
        query = f'DOI:"{value}"' if kind == "doi" else f"EXT_ID:{value} AND SRC:MED"
        url = BASE + "search?" + urllib.parse.urlencode({
            "query": query, "resultType": "core", "format": "json", "pageSize": "10",
        })
        metadata = self.request(f"core:{reference}", url)
        result = {"reference": reference, "metadata": metadata, "status": metadata["status"],
                  "documents": []}
        if metadata["status"] != "retrieved":
            return result
        try:
            record = matching_record(json.loads(self.raw(metadata)), kind, value)
        except (ValueError, TypeError, AttributeError):
            result["status"] = "invalid_metadata"
            return result
        if record is None:
            self.db.execute("UPDATE cache SET expires=min(expires,?) WHERE key=?",
                            (self.clock() + 86400, f"core:{reference}"))
            self.db.commit()
            result["status"] = "ambiguous_or_missing_identifier"
            return result
        result.update(title=record.get("title"), doi=record.get("doi"), pmid=record.get("pmid"),
                      pmcid=record.get("pmcid"), status="no_abstract")
        if isinstance(record.get("abstractText"), str) and record["abstractText"].strip():
            result["documents"].append(self._document(metadata, "abstract", abstract_text(record["abstractText"])))
            result["status"] = "text_available"
        pmcid = record.get("pmcid", "")
        if (record.get("isOpenAccess") == "Y" and isinstance(pmcid, str)
                and re.fullmatch(r"PMC[1-9][0-9]*", pmcid)):
            full = self.request(f"full:{pmcid}", BASE + pmcid + "/fullTextXML")
            result["fulltext_retrieval"] = full
            if full["status"] == "retrieved":
                try:
                    text = full_text(self.raw(full), pmcid)
                except (ET.ParseError, CurationError):
                    result["fulltext_status"] = "invalid_xml_or_identity"
                else:
                    if text:
                        result["documents"].append(self._document(full, "oa_fulltext", text))
                        result["status"] = "text_available"
        return result

    @staticmethod
    def _document(response, kind, text):
        return {"kind": kind, "response": response, "extractor": EXTRACTOR,
                "text": text, "text_sha256": hashlib.sha256(text.encode()).hexdigest()}


def verify_quote(document, quote):
    """Exact contiguous match only, with character offsets into the pinned text derivative."""
    if document["extractor"] not in {EXTRACTOR, LEGACY_EXTRACTOR}:
        raise CurationError("Unknown text extractor")
    if document["kind"] == "oa_fulltext" and document["extractor"] == LEGACY_EXTRACTOR:
        raise CurationError("Legacy OA text is audit-only; regenerate retrieval from retained cache")
    text = document["text"]
    if hashlib.sha256(text.encode()).hexdigest() != document["text_sha256"]:
        raise CurationError("Text derivative hash mismatch")
    if not isinstance(quote, str) or not quote.strip():
        raise CurationError("Quote must be nonempty")
    start = text.find(quote)
    if start < 0:
        raise CurationError("Quote is not verbatim in the retrieved text")
    return {"quote": quote, "start": start, "end": start + len(quote),
            "text_sha256": document["text_sha256"],
            "response_sha256": document["response"]["response_sha256"],
            "extractor": document["extractor"], "kind": document["kind"]}


def _deferred(result):
    return any(result.get(stage, {}).get("status") in {"retry_later", "retry_exhausted"}
               for stage in ("metadata", "fulltext_retrieval"))


def retrieve_cohort(cohort: Path, cache: Path, output: Path, limit=1):
    manifest, rows, queue = load_cohort(cohort)
    keys = sorted(queue)[:limit] if limit is not None else sorted(queue)
    output = safe_path(output, exists=False)
    output.mkdir()
    results = []
    with LiteratureCache(cache) as client:
        for key in keys:
            result = client.document(key)
            results.append(result)
            if _deferred(result):
                break
    _write_json(output / "documents.json", results)
    completed = sum(not _deferred(result) for result in results)
    receipt = {"cohort_sha256": file_hash(cohort / "manifest.json"),
               "documents_sha256": file_hash(output / "documents.json"),
               "selected_identifiers": len(keys), "attempted_identifiers": len(results),
               "completed_identifiers": completed,
               "deferred_identifiers": len(keys) - completed,
               "text_available": sum(bool(r["documents"]) for r in results),
               "metadata_cache_hits": sum(r["metadata"]["cache_hit"] for r in results),
               "queue_identifiers": manifest["queue_identifiers"], "scientific_approvals": 0}
    _write_json(output / "manifest.json", receipt)
    return receipt


def load_retrieval(path: Path, cache: LiteratureCache):
    """Rebuild text from retained bytes; a caller-supplied text/hash pair is insufficient."""
    path = safe_path(path)
    manifest = json.loads(safe_path(path / "manifest.json").read_bytes())
    data_path = safe_path(path / "documents.json")
    if file_hash(data_path) != manifest["documents_sha256"]:
        raise CurationError("Retrieval artifact hash mismatch")
    documents = json.loads(data_path.read_bytes())
    for entry in documents:
        kind, value = entry["reference"].split(":", 1)
        if entry["metadata"]["status"] != "retrieved":
            if entry["documents"]:
                raise CurationError("Failed retrieval cannot have text")
            continue
        raw_metadata = cache.raw(entry["metadata"])
        try:
            record = matching_record(json.loads(raw_metadata), kind, value)
        except (ValueError, TypeError, AttributeError) as error:
            if entry.get("status") != "invalid_metadata" or entry["documents"]:
                raise CurationError("Invalid metadata cannot provide publication text") from error
            continue
        if entry.get("status") == "invalid_metadata":
            raise CurationError("Invalid-metadata status disagrees with retained response")
        if record is None and entry["documents"]:
            raise CurationError("Unbound publication text")
        for doc in entry["documents"]:
            if doc["extractor"] not in {EXTRACTOR, LEGACY_EXTRACTOR}:
                raise CurationError("Unknown text extractor")
            raw = cache.raw(doc["response"])
            if doc["kind"] == "abstract":
                if doc["response"]["response_sha256"] != entry["metadata"]["response_sha256"]:
                    raise CurationError("Abstract response binding mismatch")
                text = abstract_text(record["abstractText"])
            elif doc["kind"] == "oa_fulltext" and record.get("isOpenAccess") == "Y":
                extract = _legacy_full_text if doc["extractor"] == LEGACY_EXTRACTOR else full_text
                text = extract(raw, record["pmcid"])
            else:
                raise CurationError("Unknown or unauthorized document kind")
            if text != doc["text"] or hashlib.sha256(text.encode()).hexdigest() != doc["text_sha256"]:
                raise CurationError("Text differs from pinned response extraction")
    if len({entry['reference'] for entry in documents}) != len(documents):
        raise CurationError("Duplicate retrieved reference")
    return manifest, {entry["reference"]: entry for entry in documents}
