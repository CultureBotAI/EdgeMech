#!/usr/bin/env python3
"""2026-11-15: Inspect one edge47 paper and retain private provenance.

Inputs: reviewed module for read-only Zotero search, local PDF/JATS, or PMC URL.
Outputs: private receipts, article text, and figure assets under .temp/fulltext.
Serves the edge47 salt-evidence review; anonymous retrieval, no publication.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

PAPERS = [
    ("10.1016/s0723-2020(83)80056-3", "23194599",
     "Lactobacillus halotolerans sp.nov., nom.rev. and Lactobacillus minor sp.nov., nom.rev."),
    ("10.1111/j.1365-2672.1993.tb01600.x", "8294308",
     "Taxonomic studies on some leuconostoc-like organisms from fermented sausages: description of a new genus Weissella for the Leuconostoc paramesenteroides group of species."),
]

PUBLIC_HOSTS = {"pmc.ncbi.nlm.nih.gov", "cdn.ncbi.nlm.nih.gov"}


def allowed_url(value):
    parsed = urlsplit(value)
    return (parsed.scheme == "https" and parsed.hostname in PUBLIC_HOSTS
            and not parsed.username and not parsed.password and parsed.port in (None, 443)
            and not parsed.query and not parsed.fragment)


class PublicRedirects(HTTPRedirectHandler):
    max_redirections = 3

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not allowed_url(newurl):
            raise ValueError("redirect outside public PMC host allowlist refused")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--safe-fulltext-module", type=Path)
    parser.add_argument("--paper", type=Path)
    parser.add_argument("--xml", type=Path)
    parser.add_argument("--url", help="Anonymous PMC article figure page or figure asset")
    parser.add_argument("--artifact-name", default="figure-page.html")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if ".temp" not in output.parts:
        parser.error("private .temp output required")
    output.mkdir(parents=True, exist_ok=True)
    if args.url:
        if not allowed_url(args.url):
            parser.error("public HTTPS PMC page or asset without credentials/query required")
        if Path(args.artifact_name).name != args.artifact_name:
            parser.error("artifact-name must be a basename")
        request = Request(args.url, headers={"User-Agent": "EdgeMech-evidence-check/1.0"})
        with build_opener(PublicRedirects()).open(request, timeout=30) as response:
            raw = response.read(20 * 1024 * 1024 + 1)
            if len(raw) > 20 * 1024 * 1024:
                parser.error("artifact exceeds 20MiB")
            content_type = response.headers.get("Content-Type")
        artifact = output / args.artifact_name
        artifact.write_bytes(raw)
        receipt = {"url": args.url, "artifact": str(artifact), "bytes": len(raw),
                   "sha256": hashlib.sha256(raw).hexdigest(), "content_type": content_type}
        target = output / (args.artifact_name + ".receipt.json")
    elif args.safe_fulltext_module:
        spec = importlib.util.spec_from_file_location("edge47_safe_fulltext", args.safe_fulltext_module)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        receipt = {"method": "readonly_zotero_exact_doi_pmid_title", "papers": []}
        for doi, pmid, title in PAPERS:
            hit = module.try_zotero_local(doi=doi, pmid=pmid, title=title)
            receipt["papers"].append({"doi": doi, "pmid": pmid, "found": bool(hit),
                                       "local_result": hit})
        target = output / "local-search.json"
    elif args.xml:
        xml = args.xml.resolve()
        raw = xml.read_bytes()
        root = ET.fromstring(raw)
        meta = root.find("./front/article-meta")
        body = root.find("./body")
        if meta is None or body is None:
            parser.error("primary JATS article metadata/body required")
        ids = {node.get("pub-id-type"): "".join(node.itertext()) for node in meta.findall("article-id")}
        sections = [{"id": section.get("id"),
                     "title": "".join(section.find("title").itertext()) if section.find("title") is not None else "",
                     "text": " ".join(section.itertext())} for section in body.iter("sec")]
        figure_nodes = list(body.iter("fig")) + root.findall("./floats-group/fig")
        table_nodes = list(body.iter("table-wrap")) + root.findall("./floats-group/table-wrap")
        figures = [{"id": node.get("id"), "label": node.findtext("label"),
                    "caption": " ".join(node.find("caption").itertext()) if node.find("caption") is not None else "",
                    "graphics": [graphic.attrib for graphic in node.iter("graphic")]} for node in figure_nodes]
        tables = [{"id": node.get("id"), "label": node.findtext("label"),
                   "rows": [[" ".join(cell.itertext()) for cell in row] for row in node.iter("tr")]} for node in table_nodes]
        extracted = {"ids": ids, "title": " ".join(meta.find("title-group").itertext()),
                     "sections": sections, "figures": figures, "tables": tables}
        text_path = output / "paper-sections.json"
        text = (json.dumps(extracted, indent=2, ensure_ascii=False) + "\n").encode()
        text_path.write_bytes(text)
        receipt = {"xml_path": str(xml), "xml_bytes": len(raw),
                   "xml_sha256": hashlib.sha256(raw).hexdigest(), "primary_identifiers": ids,
                   "extracted_path": str(text_path), "extracted_bytes": len(text),
                   "extracted_sha256": hashlib.sha256(text).hexdigest(),
                   "section_count": len(sections), "figure_count": len(figures), "table_count": len(tables)}
        target = output / "xml-extraction-receipt.json"
    elif args.paper:
        pdf = args.paper.resolve()
        raw = pdf.read_bytes()
        if not raw.startswith(b"%PDF-"):
            parser.error("PDF signature required")
        text_path = output / "paper-layout.txt"
        info_path = output / "paper-info.txt"
        subprocess.run(["pdftotext", "-layout", str(pdf), str(text_path)], check=True)
        info = subprocess.run(["pdfinfo", str(pdf)], check=True, capture_output=True)
        info_path.write_bytes(info.stdout)
        text = text_path.read_bytes()
        receipt = {"pdf_path": str(pdf), "pdf_bytes": len(raw),
                   "pdf_sha256": hashlib.sha256(raw).hexdigest(),
                   "text_path": str(text_path), "text_bytes": len(text),
                   "text_sha256": hashlib.sha256(text).hexdigest(),
                   "text_pages": text.count(b"\x0c"), "pdfinfo_path": str(info_path)}
        target = output / "extraction-receipt.json"
    else:
        parser.error("supply local search module, PDF, or XML")
    payload = (json.dumps(receipt, indent=2) + "\n").encode()
    target.write_bytes(payload)
    if target.read_bytes() != payload:
        raise RuntimeError("receipt persistence mismatch")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
