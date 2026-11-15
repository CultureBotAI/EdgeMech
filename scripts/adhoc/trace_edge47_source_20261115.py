#!/usr/bin/env python3
"""2026-11-15: Trace edge47 salt units without changing graph or review status.

Inputs: frozen source-packet JSON, read-only KG-Microbe raw/transformed root;
optional one anonymous authoritative web page. Outputs: private .temp snapshots
and hash-verified source trace for the edge47 scientific follow-up PR.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/adhoc/edge_recanary_20261113"))
from source_extract import array_records  # noqa: E402

OCCURRENCE = (
    "urn:kg-microbe:occurrence:v1:"
    "358f925d6342994dbe5598a3d3d2cdfafe3ad30028b7305c3cf21242cf3a9b57"
)
PUBLIC_PAGES = {
    "bacdive": "https://bacdive.dsmz.de/strain/6845",
    "fields": "https://api.bacdive.dsmz.de/strain_fields_information",
    "cip": "https://catalogue-crbip.pasteur.fr/fiche_catalogue.xhtml?crbip=CIP+103005",
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def file_digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            result.update(chunk)
    return result.hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)


def persist(path, payload):
    if path.exists() and path.read_bytes() != payload:
        raise ValueError("refusing to replace different retained evidence")
    path.write_bytes(payload)
    if path.read_bytes() != payload:
        raise ValueError("persisted evidence differs")


def trace(packet_path, raw_root, output):
    packets = json.loads(packet_path.read_text())
    packet = packets[OCCURRENCE]
    selected = {}
    for record in packet["records"]:
        if record["source_relative_path"] == "database.csv":
            key = "microbedecoder"
        elif record["source_relative_path"] == "bacdive_strains.json" and record["locator"] == "6845":
            key = "bacdive"
        else:
            continue
        if key in selected or digest(record["text"].encode()) != record["text_sha256"]:
            raise ValueError("ambiguous source record or frozen source hash mismatch")
        selected[key] = record
        persist(output / ("frozen-" + key + ".json"), record["text"].encode())
    if set(selected) != {"microbedecoder", "bacdive"}:
        raise ValueError("missing exact upstream source record")

    csv_record = json.loads(selected["microbedecoder"]["text"])
    bacdive = json.loads(selected["bacdive"]["text"])
    with (raw_root / "database.csv").open(encoding="latin1", newline="") as stream:
        row = next(row for number, row in enumerate(csv.DictReader(stream), 1) if number == 20904)
    if canonical(row) != selected["microbedecoder"]["text"]:
        raise ValueError("current raw CSV row differs from frozen source row")
    raw_bacdive = next(row for row in array_records(raw_root / "bacdive_strains.json")
                       if row.get("General", {}).get("BacDive-ID") == 6845)
    if canonical(raw_bacdive) != selected["bacdive"]["text"]:
        raise ValueError("current raw BacDive record differs from frozen source record")

    relevant = ("Genus", "Species", "Strain", "LPSN_ID", "BacDive_ID",
                "BacDive_Salt_concentration", "BacDive_Salt_concentration_unit")
    fields = {key: csv_record.get(key) for key in relevant}
    expected_csv = {"LPSN_ID": "783091", "BacDive_ID": "6845",
                    "BacDive_Salt_concentration": "0-10",
                    "BacDive_Salt_concentration_unit": "%"}
    if any(fields[key] != value for key, value in expected_csv.items()):
        raise ValueError("source measurement or organism differs from this bounded review")
    halophily = bacdive.get("Physiology and metabolism", {}).get("halophily")
    if isinstance(halophily, dict):
        halophily = [halophily]
    if not isinstance(halophily, list) or not halophily:
        raise ValueError("missing halophily observation")
    expected_observation = {"@ref": 119830, "concentration": "0-10 %",
                            "growth": "positive", "salt": "NaCl", "tested relation": "growth"}
    if halophily != [expected_observation]:
        raise ValueError("halophily observation differs from this bounded review")
    reference_ids = {str(item.get("@ref")) for item in halophily}
    references = bacdive.get("references", [])
    if isinstance(references, dict):
        references = [references]
    matched_refs = [item for item in references
                    if str(item.get("@id", item.get("id", ""))) in reference_ids]

    transformed = raw_root.parent / "transformed/microbedecoder/edges.tsv"
    paired = []
    with transformed.open() as stream:
        for number, row in enumerate(csv.DictReader(stream, delimiter="\t"), 2):
            if row.get("subject") == "lpsn:783091" and row.get("source_column") in (
                    "BacDive_Salt_concentration", "BacDive_Salt_concentration_unit"):
                paired.append({"tsv_line": number, **row})
    csv_sha = file_digest(raw_root / "database.csv")
    expected_record = "sha256:" + csv_sha + "#record=20904"
    if len(paired) != 2 or any(row.get("source_record") != expected_record for row in paired):
        raise ValueError("current transformed sibling rows do not share the exact CSV source record")
    summary = {
        "occurrence_id": OCCURRENCE,
        "source_packet_sha256": file_digest(packet_path),
        "frozen_edge": packet["edge"],
        "microbedecoder": {
            "locator": "CSV data row 20904",
            "source_file_sha256": csv_sha,
            "selected_record_sha256": selected["microbedecoder"]["text_sha256"],
            "frozen_matches_current_raw": True,
            "fields": fields,
        },
        "bacdive": {
            "locator": "6845",
            "selected_record_sha256": selected["bacdive"]["text_sha256"],
            "frozen_matches_current_raw": True,
            "general": bacdive.get("General"),
            "taxonomy": bacdive.get("Name and taxonomic classification"),
            "halophily": halophily,
            "matching_references": matched_refs,
            "all_reference_records": references,
            "culture_growth_conditions_separate_from_halophily": bacdive.get("Culture and growth conditions"),
        },
        "current_transformed_sibling_rows": paired,
        "current_transformed_sha256": file_digest(transformed),
        "current_transformed_is_not_claimed_identical_to_frozen_release": True,
        "interpretation": {
            "reported_value": "0-10", "reported_unit": "%", "tested_salt": "NaCl",
            "test_result": "positive", "tested_relation": "growth",
            "percent_basis": "not specified; do not infer w/v, w/w, or convert to g/L",
            "assay_medium_temperature_duration": "not linked to this halophily observation",
            "scope": "BacDive6845 type strain; not a species-wide universal",
            "not_established": ["optimum", "upper tolerance threshold", "growth at every real-valued point"],
        },
    }
    persist(output / "source-trace.json", (json.dumps(summary, indent=2) + "\n").encode())
    print(json.dumps({"trace_written": True, "frozen_raw_records_verified": 2,
                      "source_record": expected_record, "halophily": halophily,
                      "paired_transformed_rows": len(paired)}, indent=2))


def fetch_page(name, output):
    url = PUBLIC_PAGES[name]
    request = urllib.request.Request(url, headers={"User-Agent": "EdgeMech-source-review/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = response.read(4 * 1024 * 1024 + 1)
        status = response.status
        final_url = response.url
    if not payload or len(payload) > 4 * 1024 * 1024:
        raise ValueError("empty or oversized public page")
    persist(output / (name + ".html"), payload)
    receipt = {"requested_url": url, "final_url": final_url, "status": status,
               "bytes": len(payload), "sha256": digest(payload),
               "retrieved_at": datetime.now(timezone.utc).isoformat()}
    receipt_path = output / (name + "-retrieval.json")
    if receipt_path.exists():
        raise ValueError("retrieval receipt already exists")
    persist(receipt_path, (json.dumps(receipt, indent=2) + "\n").encode())
    print(json.dumps(receipt, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-packet", type=Path)
    parser.add_argument("--raw-root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fetch-page", choices=PUBLIC_PAGES)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / ".temp"):
        parser.error("output must be under this checkout's private .temp")
    if subprocess.run(["git", "-C", str(ROOT), "check-ignore", "-q", str(output)]).returncode:
        parser.error("output is not gitignored")
    output.mkdir(parents=True, exist_ok=True)
    if args.fetch_page:
        fetch_page(args.fetch_page, output)
    else:
        if not args.source_packet or not args.raw_root:
            parser.error("source trace requires --source-packet and --raw-root")
        trace(args.source_packet, args.raw_root, output)


if __name__ == "__main__":
    main()
