"""Grouped upstream extraction and name/citation packets for recanary PR76, 2026-11-13.

Inputs: bounded fresh canary and configured read-only upstream root. Each source is
scanned once per invocation. Outputs: private source snapshots, packets and timing
receipts. No scientific search or automatic verdicts; one transport canary first.
"""

from __future__ import annotations

import argparse
import base64
import csv
import gzip
import hashlib
import json
import re
import subprocess
import time
from collections import defaultdict
from pathlib import Path


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def text_open(path):
    with path.open("rb") as stream:
        compressed = stream.read(2) == b"\x1f\x8b"
    return gzip.open(path, "rt") if compressed else path.open()


def array_records(path):
    decoder, buffer = json.JSONDecoder(), ""
    with path.open() as stream:
        while True:
            buffer = buffer.lstrip(" \r\n\t,[")
            if buffer.startswith("]"):
                return
            try:
                value, consumed = decoder.raw_decode(buffer)
            except json.JSONDecodeError:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    raise ValueError("Incomplete upstream JSON array")
                buffer += chunk
            else:
                yield value
                buffer = buffer[consumed:]


def normalized_names(name):
    if not name:
        return set()
    name = name.removeprefix("GTDB:").removeprefix("s__").replace("_", " ").strip()
    result = {name, name.removeprefix("Candidatus ")}
    words = name.removeprefix("Candidatus ").split()
    if len(words) >= 2 and words[1] not in {"sp.", "bacterium", "strain", "as"}:
        result.add(" ".join(words[:2]))
    return result


def extract(rows, raw_root):
    root = Path(raw_root).resolve()
    records = {r["occurrence_id"]: [] for r in rows}
    names, taxids, bids, cultures = {}, {}, {}, {}
    source_times, reads = {}, defaultdict(int)
    for row in rows:
        key = row["occurrence_id"]
        names[key], taxids[key], bids[key], cultures[key] = set(), set(), set(), set()
        for side in ["subject", "object"]:
            value = row[side]
            label = row.get(side + "_label") or ""
            if value.startswith(("NCBITaxon:", "lpsn:", "GTDB:")):
                names[key].update(normalized_names(label))
            taxids[key].update(re.findall(r"NCBITaxon:(\d+)", value + " " + label))
            bids[key].update(re.findall(r"bacdive_(\d+)", value))
            if value.startswith("kgmicrobe.strain:") and "bacdive_" not in value:
                cultures[key].add(value.split(":", 1)[1].replace("-", " ").lower())

    def add(row, path, record, url, locator, binding="exact source selector"):
        relative = path.resolve().relative_to(root).as_posix()
        if Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise ValueError("Unsafe source-relative identity")
        text = json.dumps(record, ensure_ascii=False, sort_keys=True, indent=2)
        value = {
            "source_relative_path": relative,
            "source_path": str(path),
            "source_file_size": path.stat().st_size,
            "source_file_mtime_ns": path.stat().st_mtime_ns,
            "locator": locator,
            "retrieval_url": url,
            "binding": binding,
            "text": text,
            "text_sha256": sha(text.encode()),
            "evidence_level": "source_record",
            "extractor": "source-record-json-canonical/v1",
        }
        records[row["occurrence_id"]].append(value)

    def select(transform):
        return [r for r in rows if r["origin_transform"].split("/")[0] == transform]

    def begin(path):
        relative = path.relative_to(root).as_posix()
        reads[relative] += 1
        if reads[relative] != 1:
            raise ValueError("Upstream source would be scanned more than once")
        return time.monotonic()

    def end(path, started):
        source_times[path.relative_to(root).as_posix()] = time.monotonic() - started

    # Small primary tables first; BactoTraits binds BacDive IDs for the one large scan.
    for transform, filename in [
        ("bactotraits", "BactoTraits_databaseV2_Jun2022.csv"),
        ("madin_etal", "madin_etal.csv"),
        ("microbedecoder", "database.csv"),
    ]:
        wanted = select(transform)
        if not wanted:
            continue
        path = root / filename
        started = begin(path)
        with path.open(encoding="latin1", newline="") as stream:
            if transform == "bactotraits":
                next(stream)
                next(stream)
            for ordinal, rec in enumerate(
                csv.DictReader(stream, delimiter=";" if transform == "bactotraits" else ","), 1
            ):
                recnames = set()
                for label in [
                    rec.get("Full_name"),
                    rec.get("org_name"),
                    rec.get("species"),
                    " ".join([rec.get("Genus", ""), rec.get("Species", "")]),
                ]:
                    recnames.update(normalized_names(label))
                for row in wanted:
                    key = row["occurrence_id"]
                    matched = False
                    if transform == "bactotraits":
                        matched = bool(names[key] & recnames)
                    elif transform == "madin_etal":
                        matched = bool(taxids[key] & {rec.get("tax_id"), rec.get("species_tax_id")})
                    elif transform == "microbedecoder":
                        matched = any(
                            v == "lpsn:" + rec.get("LPSN_ID", "")
                            for v in [row["subject"], row["object"]]
                        )
                    if matched:
                        url = {
                            "bactotraits": "https://ordar.otelo.univ-lorraine.fr/files/ORDAR-53/BactoTraits_databaseV2_Jun2022.csv",
                            "madin_etal": "https://github.com/bacteria-archaea-traits/bacteria-archaea-traits/blob/master/output/condensed_traits_NCBI.csv",
                            "microbedecoder": "https://github.com/thackmann/MicrobeDecoder/raw/main/Shiny/MicrobeDecoder/data/database/database.zip",
                        }[transform]
                        add(row, path, rec, url, f"CSV data row {ordinal}")
                        bid = rec.get("Bacdive_ID") or rec.get("BacDive_ID")
                        if bid and bid != "NA":
                            bids[key].update(re.findall(r"\d+", bid))
                        names[key].update(recnames)
        end(path, started)

    # Exact requested strains plus at most eight taxon-level candidates per edge.
    path = root / "bacdive_strains.json"
    started = begin(path)
    candidate_counts = defaultdict(int)
    for rec in array_records(path):
        general = rec.get("General", {})
        bid = str(general.get("BacDive-ID", ""))
        taxa = general.get("NCBI tax id", [])
        taxa = taxa if isinstance(taxa, list) else [taxa]
        tids = {str(v.get("NCBI tax id", "")) for v in taxa if isinstance(v, dict)}
        classification = rec.get("Name and taxonomic classification", {})
        recnames = normalized_names(classification.get("species"))
        links = rec.get("External links", {})
        linked = links if isinstance(links, list) else [links]
        cc = set()
        for item in linked:
            cc.update(
                str(item.get("culture collection no.", "")).lower().replace("-", " ").split(", ")
            )
        for row in rows:
            key = row["occurrence_id"]
            exact = bid in bids[key] or bool(cultures[key] & cc)
            taxon = bool(taxids[key] & tids) or bool(names[key] & recnames)
            if exact or (taxon and candidate_counts[key] < 8):
                add(
                    row,
                    path,
                    rec,
                    "https://bacdive.dsmz.de/strain/" + bid,
                    bid,
                    "exact strain/culture ID"
                    if exact
                    else "taxon-level candidate; cap eight; not strain equivalence",
                )
                candidate_counts[key] += not exact
                names[key].update(recnames)
                lpsn = classification.get("LPSN", {})
                if isinstance(lpsn, dict):
                    names[key].update(normalized_names(lpsn.get("species")))
                    for synonym in lpsn.get("synonyms", []):
                        if isinstance(synonym, dict):
                            names[key].update(normalized_names(synonym.get("synonym")))
    end(path, started)

    # One GSS scan selects API name records for every applicable taxon. Linked
    # basonyms/synonyms/type strains are read once per unique API file, not per edge.
    lpsn_ids = {
        r["occurrence_id"]: {
            v.split(":", 1)[1] for v in [r["subject"], r["object"]] if v.startswith("lpsn:")
        }
        for r in rows
    }
    path = root / "lpsn_gss.csv"
    started = begin(path)
    with path.open(encoding="latin1", newline="") as stream:
        for ordinal, rec in enumerate(csv.DictReader(stream), 1):
            label = " ".join(
                [rec.get("genus_name", ""), rec.get("sp_epithet", ""), rec.get("subsp_epithet", "")]
            ).strip()
            for row in rows:
                key = row["occurrence_id"]
                if rec.get("record_no") in lpsn_ids[key] or (label and label in names[key]):
                    lpsn_ids[key].add(rec["record_no"])
                    names[key].update(normalized_names(label))
                    add(row, path, rec, rec["address"], f"CSV data row {ordinal}")
    end(path, started)
    api_cache = {}
    for row in rows:
        key = row["occurrence_id"]
        pending = [(lid, 0) for lid in sorted(lpsn_ids[key])]
        visited = set()
        while pending:
            lid, depth = pending.pop(0)
            if lid in visited:
                continue
            visited.add(lid)
            path = root / "lpsn" / "api_cache" / (str(lid) + ".json")
            if not path.is_file():
                continue
            if lid not in api_cache:
                started = begin(path)
                api_cache[lid] = json.loads(path.read_text())
                end(path, started)
            rec = api_cache[lid]
            add(
                row,
                path,
                rec,
                rec.get("lpsn_address") or "https://lpsn.dsmz.de/taxon/" + lid,
                lid,
                "exact/name-resolved LPSN record; linked names flagged by ID",
            )
            names[key].update(normalized_names(rec.get("full_name")))
            if depth < 2:
                for field in ["basonym_id", "lpsn_correct_name_id"]:
                    if rec.get(field):
                        pending.append((str(rec[field]), depth + 1))

    for transform, filename in [
        ("metatraits", "ncbi_species_summary.jsonl.gz"),
        ("metatraits_gtdb", "gtdb_species_summary.jsonl.gz"),
    ]:
        wanted = select(transform)
        if not wanted:
            continue
        path = root / filename
        started = begin(path)
        by_name = defaultdict(list)
        for row in wanted:
            for name in names[row["occurrence_id"]]:
                by_name[name].append(row)
        with text_open(path) as stream:
            for ordinal, line in enumerate(stream, 1):
                rec = json.loads(line)
                for row in by_name.get(rec.get("tax_name"), []):
                    add(
                        row,
                        path,
                        rec,
                        "https://metatraits.embl.de/",
                        f"JSONL line {ordinal}: {rec['tax_name']}",
                    )
        end(path, started)

    wanted = select("gold")
    if wanted:
        path = root / "gold" / "GOLD_edges.tsv"
        started = begin(path)
        pairs = {(r["subject"], r["object"]): r for r in wanted}
        with path.open() as stream:
            for ordinal, rec in enumerate(csv.DictReader(stream, delimiter="\t"), 1):
                row = pairs.get((rec["subject"], rec["object"]))
                if row:
                    add(
                        row,
                        path,
                        rec,
                        "https://gold.jgi.doe.gov/organism?id=" + row["subject"].split(":")[-1],
                        f"TSV data row {ordinal}",
                    )
        end(path, started)

    wanted = select("gtdb")
    if wanted:
        for filename in ["ar53_metadata.tsv.gz", "bac120_metadata.tsv.gz"]:
            path = root / "gtdb" / filename
            started = begin(path)
            found = set()
            with text_open(path) as stream:
                for ordinal, rec in enumerate(csv.DictReader(stream, delimiter="\t"), 1):
                    taxa = {
                        v.split("__", 1)[0] + "__" + v.split("__", 1)[1].replace(" ", "_")
                        for v in rec.get("gtdb_taxonomy", "").split(";")
                        if "__" in v
                    }
                    for row in wanted:
                        key = row["occurrence_id"]
                        if key in found:
                            continue
                        gtdb = {
                            v.split(":", 1)[1]
                            for v in [row["subject"], row["object"]]
                            if v.startswith("GTDB:")
                        }
                        if gtdb and gtdb <= taxa:
                            add(
                                row,
                                path,
                                rec,
                                "https://gtdb.ecogenomic.org/genome?gid="
                                + rec.get("accession", ""),
                                f"TSV data row {ordinal}",
                            )
                            found.add(key)
            end(path, started)

    wanted = select("mediadive")
    if wanted:
        for filename, prefix in [
            ("media_detailed.json", "mediadive.medium:"),
            ("media_strains.json", "mediadive.medium:"),
            ("solutions.json", "mediadive.solution:"),
        ]:
            path = root / "mediadive" / filename
            started = begin(path)
            data = json.loads(path.read_text())
            for row in wanted:
                for value in [row["subject"], row["object"]]:
                    if value.startswith(prefix) and value.split(":", 1)[1] in data:
                        key = value.split(":", 1)[1]
                        add(
                            row,
                            path,
                            data[key],
                            "https://mediadive.dsmz.de/"
                            + ("solution/" if prefix.endswith("solution:") else "medium/")
                            + key,
                            key,
                        )
            end(path, started)

    wanted = select("prego_habitat")
    if wanted:
        pairs = {
            frozenset(
                [
                    next(
                        v.split(":", 1)[1]
                        for v in [r["subject"], r["object"]]
                        if v.startswith("NCBITaxon:")
                    ),
                    next(v for v in [r["subject"], r["object"]] if not v.startswith("NCBITaxon:")),
                ]
            ): r
            for r in wanted
        }
        for directory in [
            "environmental_samples_extracted",
            "annotated_genomes_isolates_extracted",
        ]:
            path = root / "prego" / directory / "database_pairs.tsv"
            started = begin(path)
            with path.open() as stream:
                for ordinal, line in enumerate(stream, 1):
                    fields = line.rstrip("\n").split("\t")
                    row = pairs.get(frozenset([fields[1], fields[3]]))
                    if row:
                        add(
                            row,
                            path,
                            {"raw_tsv": line.rstrip("\n"), "fields": fields},
                            "https://prego.hcmr.gr/",
                            f"TSV line {ordinal}",
                        )
            end(path, started)

    wanted = select("rhea_mappings")
    if wanted:
        for filename in ["rhea2ec.tsv", "rhea2go.tsv", "rhea/rhea-directions.tsv"]:
            path = root / filename
            started = begin(path)
            with path.open() as stream:
                for ordinal, rec in enumerate(csv.DictReader(stream, delimiter="\t"), 1):
                    vals = set(rec.values())
                    for row in wanted:
                        endpoints = [
                            row["subject"].split(":", 1)[1],
                            row["object"].split(":", 1)[1],
                        ]
                        if all(v in vals or "GO:" + v in vals for v in endpoints):
                            add(
                                row,
                                path,
                                rec,
                                "https://www.rhea-db.org/rhea/" + endpoints[0],
                                f"TSV data row {ordinal}",
                            )
            end(path, started)
    return {
        "records": records,
        "source_scan_seconds": source_times,
        "source_scan_counts": dict(reads),
        "taxon_candidate_counts": dict(candidate_counts),
        "resolved_names": {k: sorted(v) for k, v in names.items()},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--remote")
    parser.add_argument("--host")
    parser.add_argument("--raw-root", type=Path)
    parser.add_argument("--canary", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()
    if args.remote:
        payload = json.loads(base64.b64decode(args.remote))
        print(json.dumps(extract(payload["rows"], payload["raw_root"]), ensure_ascii=False))
        return
    if not all([args.host, args.raw_root, args.canary, args.output]) or not 1 <= args.limit <= 50:
        parser.error("host/raw-root/canary/output and limit1..50 required")
    all_rows = [json.loads(line) for line in args.canary.read_text().splitlines()]
    if len(all_rows) != 50:
        raise ValueError("Expected exactly the fresh fifty-edge canary")
    rows = all_rows[: args.limit]
    selectors = [
        {
            k: r.get(k)
            for k in [
                "occurrence_id",
                "origin_transform",
                "subject",
                "object",
                "subject_label",
                "object_label",
            ]
        }
        for r in rows
    ]
    payload = base64.b64encode(
        json.dumps({"rows": selectors, "raw_root": str(args.raw_root)}).encode()
    ).decode()
    started = time.monotonic()
    result = subprocess.run(
        ["ssh", args.host, "python3", "-", "--remote", payload],
        input=Path(__file__).read_text(),
        text=True,
        capture_output=True,
    )
    if result.returncode:
        raise RuntimeError(result.stderr)
    data = json.loads(result.stdout)
    args.output.mkdir(parents=True, exist_ok=True)
    path = args.output / f"source-records-{len(rows)}.json"
    if path.exists():
        raise ValueError("Refusing to overwrite an existing extraction")
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    elapsed = time.monotonic() - started
    receipt = {
        "edges": len(rows),
        "elapsed_seconds": elapsed,
        "records": sum(map(len, data["records"].values())),
        "snapshot_sha256": sha(path.read_bytes()),
        "canary_sha256": sha(args.canary.read_bytes()),
        "source_scan_counts": data["source_scan_counts"],
        "source_scan_seconds": data["source_scan_seconds"],
    }
    (args.output / f"extraction-{len(rows)}.json").write_text(json.dumps(receipt, indent=2) + "\n")
    packets = args.output / "packets"
    packets.mkdir(exist_ok=True)
    for row in rows:
        packet = {
            "edge": row,
            "records": data["records"][row["occurrence_id"]],
            "resolved_names": data["resolved_names"][row["occurrence_id"]],
        }
        (packets / f"{row['canary_ordinal']:02d}.json").write_text(
            json.dumps(packet, ensure_ascii=False, indent=2) + "\n"
        )
    print(
        json.dumps(
            {
                "edges": len(rows),
                "records": receipt["records"],
                "elapsed_seconds": elapsed,
                "snapshot_bytes": path.stat().st_size,
            }
        )
    )


if __name__ == "__main__":
    main()
