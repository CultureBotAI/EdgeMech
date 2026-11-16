#!/usr/bin/env python3
"""Assemble explicit M5 evidence inputs, without authoring any axis ratings.

Consumes current source packets, separately checked v2 views, raw evidence and
researcher inventories. Produces a private neutral guide and freeze config.
The round helper subsequently pins/replays this package. Never reads old ratings.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from edgemech.storage.parquet import safe_path  # noqa: E402

RUN = Path(".temp/m5-worker-run-20261116")
PACKAGE = RUN / "package"
EVIDENCE = RUN / "evidence"


def checked(path, *, exists=True):
    relative = Path(path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Expected a repository-relative evidence path")
    target = safe_path(ROOT / relative, exists=exists)
    if not target.is_relative_to(ROOT):
        raise ValueError("Evidence path escapes worktree")
    return target


def load(path):
    return json.loads(checked(path).read_bytes())


def write_bytes(path, raw):
    target = checked(path, exists=False)
    target.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    checked(path, exists=False)
    fd = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    if checked(path).read_bytes() != raw:
        raise ValueError("Persisted package derivative differs")


def write(path, value):
    write_bytes(path, (json.dumps(value, indent=2, sort_keys=True) + "\n").encode())


def main():
    os.umask(0o077)
    cohort = load("artifacts/edge-calibration-20261115/cohort.json")
    literature = load(EVIDENCE / "literature/reviewer-safe-evidence-inventory.json")
    fresh14 = load(EVIDENCE / "fresh14/evidence-map.json")
    files = {}
    cases = {c["case_id"]: {"case_id": c["case_id"], "evidence_ids": []}
             for c in cohort["cases"]}

    def add(path, role, eid=None, version=None, expected=None, selected=None):
        path = str(path)
        raw = checked(path).read_bytes()
        if expected and hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError("Evidence hash changed: " + path)
        item = files.setdefault(path, {"path": path, "role": role, "evidence_ids": []})
        if version:
            item["version"] = version
        if eid:
            if eid not in item["evidence_ids"]:
                item["evidence_ids"].append(eid)
            for cid in selected if selected is not None else cases:
                if eid not in cases[cid]["evidence_ids"]:
                    cases[cid]["evidence_ids"].append(eid)

    for path in ["src/edgemech/occurrence_packet.py", "src/edgemech/occurrence_review.py",
                 "src/edgemech/literature_cache.py", "src/edgemech/contract-pins.json",
                 "src/edgemech/storage/parquet.py", "src/edgemech/pins.py",
                 "schema/record_review.yaml", "scripts/record_review.py", "uv.lock",
                 "scripts/adhoc/prepare_m5_reviewer_views_20261116.py",
                 "scripts/adhoc/assemble_m5_package_20261116.py"]:
        add(path, "proof_adapter")
    add("scripts/adhoc/m5_review_20261116/blinded-review.md", "instructions")
    add("docs/record-reviews.md", "instructions")
    for cid, case in cases.items():
        prefix = Path(".temp/edge-calibration-20261115") / cid
        case["packet_path"] = str(prefix / "packet.json")
        case["reviewer_view_path"] = str(PACKAGE / "cases-v2" / cid / "view.json")
        for name in ["packet.json", "occurrence.json", "source.json", "receipt.json"]:
            add(prefix / name, "packet" if name == "packet.json" else "private_input",
                "packet-" + cid if name == "packet.json" else None, selected=[cid])
        add(case["reviewer_view_path"], "reviewer_view")
        add(PACKAGE / "cases-v2" / cid / "receipt.json", "receipt")
    common = EVIDENCE / "fresh14"
    for name, version, eid in [
        ("biolink-model-4.4.0.yaml", "4.4.0", "biolink440"),
        ("biolink-model-4.4.2.yaml", "4.4.2", "biolink442"),
        ("metpo.owl", "2026-06-12", "metpo20260612"),
        ("skos.txt", "W3C Recommendation2009-08-18", "skos2009"),
        ("glossary.txt", "LPSN snapshot2026-11-16", "lpsn-glossary")]:
        add(common / name, "authority", eid, version)
    for name in ["new-authority-copy-receipts.json", "local-schema-replay.json"]:
        add(common / name, "receipt")
    for candidate in fresh14["candidates"]:
        add(common / candidate["path"], "authority", candidate["evidence_candidate_id"],
            candidate["authority_version"], candidate["sha256"], ["fresh-14"])
    for name in ["maintained-biolink-revalidation.md", "maintained-lpsn.py",
                 "maintained-download.yaml"]:
        add(common / name, "authority", "maintained-" + Path(name).stem,
            "KG-Microbe2d94ed094167d94402f21400a9ad7dc4f7f20438")
    for candidate in load(EVIDENCE / "literature/literature-proof-candidates.json"):
        pin = candidate["raw_input"]
        add(pin["path"], "evidence", candidate["evidence_id"], expected=pin["sha256"],
            selected=[candidate["case_id"]])
        add(candidate["text_path"], "derivative", expected=candidate["text_sha256"])
    tax_cases = {"113559": "first-28", "1281099": "first-32", "1123071": "fresh-05",
                 "1642702": "fresh-04", "1540872": "first-43"}
    taxonomy = load(EVIDENCE / "literature/ncbi-authority-inventory.json")
    for item in taxonomy:
        add(item["raw_path"], "authority", "ncbi-" + item["taxid"],
            "NCBI record UpdateDate=" + item["version"] + "; retrieved=" + item["retrieved"],
            item["raw_sha256"], [tax_cases[item["taxid"]]])
        add(item["text_path"], "derivative", expected=item["text_sha256"])
        add(Path(item["raw_path"]).parent / "receipt.json", "receipt")
    for name in ["dsm19353", "dsm18772", "jcm14586", "bacdive17851"]:
        add(EVIDENCE / "literature/fresh05-authorities" / (name + ".txt"), "authority",
            "fresh05-" + name, "retained primary catalog snapshot2026-11-15", selected=["fresh-05"])
    add(EVIDENCE / "literature/fresh05-authority-receipts.json", "receipt")
    # Preserve provider-returned text exactly; no rephrased text masquerades as source.
    structural = load(EVIDENCE / "structural/tavily-extract.json")
    for item in structural["result"]["results"]:
        cid = "first-01" if "bacdive" in item["url"] else "first-32"
        path = PACKAGE / "structural-v2" / (cid + "-authority.txt")
        write_bytes(path, item["raw_content"].encode())
        add(path, "authority", cid + "-catalog", "provider snapshot2026-11-16", selected=[cid])
    add(EVIDENCE / "structural/tavily-extract.json", "receipt")
    add(EVIDENCE / "literature/fresh04-dsm102218-extract.json", "authority",
        "fresh04-dsm102218", "DSMZ provider snapshot2026-11-16", selected=["fresh-04"])
    add(EVIDENCE / "literature/fresh04-identity-conflict.json", "evidence", "fresh04-identity-context",
        selected=["fresh-04"])
    guide = {
        "round_id": "m5-calibration-20261116-round01", "ratings": None,
        "evidence_candidates_are_not_ratings": True,
        "literature_cases": literature["cases"], "fresh14": fresh14,
        "taxonomy_authorities": taxonomy,
        "structural_cases": {
            "first-01": {"catalog": "first-01-catalog", "scope": "Original assay link only; "
                "source CIT+ does not convert original procedure link into a citrate-metabolism claim. "
                "Retain original METPO2000511 and category/definition/version checks independently."},
            "first-32": {"catalogs": ["first-32-catalog", "ncbi-1281099"], "scope":
                "Original LPSN46511 close_match NCBI1281099; assess both identifiers without replacement. "
                "Current catalogs independently identify each endpoint; source row remains unchanged."}},
        "source_binding": "packet-CASE IDs bind exact replayed original source packets. "
            "Source fidelity does not establish independent scientific support.",
        "shared_authorities": ["biolink440", "biolink442", "metpo20260612", "skos2009", "lpsn-glossary"],
        "sampled_version_limit": "Local producer4.4.2 fingerprint is not a complete hash chain to sampled "
            "inputs. Staged4.4.0 is distinct. Assess semantic applicability and version uncertainty explicitly.",
        "retained_search_bounds": literature["retained_search_bounds"],
        "limits": "Only listed inputs may inform this round. Missing exact literature or authorities stay "
            "unresolved. Every candidate quote must be replayed and its entailment independently judged. "
            "Selected snippets are alternatives; their union is not automatically within the quotation budget."}
    write(PACKAGE / "evidence-guide-v2.json", guide)
    add(PACKAGE / "evidence-guide-v2.json", "instructions")
    write(PACKAGE / "freeze-config-v2.json", {"round_id": guide["round_id"],
          "files": list(files.values()), "cases": list(cases.values())})
    print(json.dumps({"cases": len(cases), "inputs": len(files), "ratings": 0,
                      "config": str(PACKAGE / "freeze-config-v2.json")}))


if __name__ == "__main__":
    main()
