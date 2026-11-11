"""Bounded, manually identified primary text captured from a browsing tool.

Hashes authenticate the retained tool response, not downloaded publisher/PDF bytes.
The extractor preserves marked line boundaries; it does not reproduce or certify OCR.
This local evidence adapter does not introduce a scientific-review contract.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

from kg_microbe_curation.artifact import validate_relative_path
from kg_microbe_curation.identity import CurationError

from .literature_probe import identifier
from .storage.parquet import safe_path

FORMAT = "edgemech-source-capture/v1"
EXTRACTOR = "edgemech-marked-tool-lines/v1"
KIND = "tool_extracted_primary_text"
REPRESENTATION = "tool-extracted primary text"
LIMITATION = (
    "Some evidence is tool-extracted primary text with explicit manual DOI/title identity review. "
    "Retained hashes bind browsing-tool responses, not original publisher/PDF bytes; "
    "OCR and the tool's extraction were not independently reproduced."
)
LINE = re.compile(r"^L(?P<line>[0-9]+)(?:@P(?P<page>[0-9]+(?:-[0-9]+)?))?: ?(?P<text>.*)$")


def _pinned_bytes(path: str, expected: str, bound: int) -> bytes:
    validate_relative_path(path)
    file = safe_path(Path(path))
    if not file.is_file() or file.stat().st_size > bound:
        raise CurationError("Source capture must be a bounded regular file")
    with file.open("rb") as handle:
        raw = handle.read(bound + 1)
    if len(raw) > bound or hashlib.sha256(raw).hexdigest() != expected:
        raise CurationError("Source capture hash mismatch or size exceeded")
    return raw


def extract_lines(raw: bytes):
    """Select only marked source lines, keeping newlines and source coordinates."""
    try:
        source = raw.decode("utf-8")
    except UnicodeError as exc:
        raise CurationError("Source capture must be UTF-8 tool text") from exc
    parts, spans = [], []
    offset = 0
    for line in source.splitlines():
        match = LINE.fullmatch(line)
        if match is None:
            continue
        number = int(match["line"])
        if spans and number <= spans[-1]["line"]:
            raise CurationError("Source capture line markers must be unique and increasing")
        text = match["text"]
        parts.append(text)
        page = match["page"]
        page = int(page) if page and "-" not in page else page
        spans.append({"line": number, "page": page,
                      "start": offset, "end": offset + len(text)})
        offset += len(text) + 1
    if not spans or not any(parts):
        raise CurationError("Source capture has no marked primary text")
    return "\n".join(parts), spans


def load_source_captures(pin: dict):
    """Verify evidence pins and explicit manual identity approval, without inferring it."""
    raw = _pinned_bytes(pin["path"], pin["sha256"], 1024**2)
    manifest = json.loads(raw)
    entries = manifest.get("captures")
    if manifest.get("format") != FORMAT or not isinstance(entries, list) or not 1 <= len(entries) <= 100:
        raise CurationError("Invalid or unbounded source-capture manifest")
    inputs = [{"path": pin["path"], "sha256": pin["sha256"],
               "role": "manually identified tool-extracted primary evidence manifest"}]
    captures = {}
    for entry in entries:
        capture_id = entry.get("capture_id")
        if not isinstance(capture_id, str) or not capture_id.strip() or capture_id in captures:
            raise CurationError("Missing or duplicate source capture ID")
        reference = entry.get("reference", "")
        kind, doi = identifier(reference)
        identity = entry.get("identity_review", {})
        if (kind != "doi" or reference != f"doi:{doi}" or identity.get("verified") is not True
                or identity.get("doi") != doi or not isinstance(entry.get("title"), str)
                or not entry["title"].strip() or identity.get("title") != entry["title"]
                or not all(isinstance(identity.get(field), str) and identity[field].strip()
                           for field in ("reviewer", "basis"))):
            raise CurationError("Source capture requires explicit matching manual DOI/title identity review")
        url = entry.get("url", "")
        parsed = urlsplit(url)
        if (parsed.scheme not in {"https", "http"} or not parsed.hostname or parsed.username
                or parsed.password or entry.get("representation") != REPRESENTATION):
            raise CurationError("Invalid source capture URL or representation")
        snapshot = entry["snapshot"]
        source = _pinned_bytes(snapshot["path"], snapshot["sha256"], 16 * 1024**2)
        text, spans = extract_lines(source)
        captures[capture_id] = {
            "capture_id": capture_id, "reference": reference, "title": entry["title"],
            "identity_review": identity, "representation": REPRESENTATION,
            "kind": KIND, "extractor": EXTRACTOR, "text": text,
            "text_sha256": hashlib.sha256(text.encode()).hexdigest(), "lines": spans,
            "response": {"url": url, "response_sha256": snapshot["sha256"]},
        }
        item = {"path": snapshot["path"], "sha256": snapshot["sha256"],
                "role": "retained browsing-tool response; original document bytes not captured"}
        if item not in inputs:
            inputs.append(item)
    return captures, inputs


def capture_quote(captures: dict, selection: dict):
    capture = captures.get(selection["capture_id"])
    if capture is None:
        raise CurationError("Unknown source capture")
    if selection["reference"] != capture["reference"] or selection["kind"] != KIND:
        raise CurationError("Source capture reference or representation mismatch")
    text, quote = capture["text"], selection["quote"]
    if capture["extractor"] != EXTRACTOR or hashlib.sha256(text.encode()).hexdigest() != capture["text_sha256"]:
        raise CurationError("Source capture derivative integrity mismatch")
    if not isinstance(quote, str) or not quote.strip():
        raise CurationError("Quote must be nonempty")
    start = text.find(quote)
    if start < 0:
        raise CurationError("Quote is not verbatim in the captured primary text")
    proof = {"quote": quote, "start": start, "end": start + len(quote),
             "text_sha256": capture["text_sha256"], "kind": KIND, "extractor": EXTRACTOR,
             "response_sha256": capture["response"]["response_sha256"]}
    touched = [line for line in capture["lines"]
               if line["start"] < proof["end"] and line["end"] >= proof["start"]]
    if not touched or any(right["line"] != left["line"] + 1
                          for left, right in zip(touched, touched[1:])):
        raise CurationError("Quote crosses omitted source lines")
    proof.update(capture_id=capture["capture_id"], representation=REPRESENTATION,
                 source_lines=[{"line": line["line"], "page": line["page"]} for line in touched])
    coordinates = ", ".join(f"L{line['line']}" + (
        f"@P{line['page']}" if line["page"] is not None else "") for line in touched)
    locator = (f"{REPRESENTATION}; {coordinates}; chars {proof['start']}:{proof['end']}; "
               f"text_sha256={proof['text_sha256']}; {EXTRACTOR}")
    return capture, proof, locator
