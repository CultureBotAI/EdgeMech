"""Extract and verify source records for the helper-3 fifty-edge canary, 2026-11-12.

Inputs: canary.jsonl and read-only remote kg-microbe upstream files.
Outputs: private exact source-record snapshots and adjudication quote checks.
Serves: feat/stratified-edge-sample-review-20261112. No scientific verdict inference.
"""

from __future__ import annotations

import argparse
import base64
import csv
import gzip
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

RAW = Path(os.environ.get("EDGEMECH_RAW_ROOT", "data/raw"))
HOST = os.environ.get("EDGEMECH_REMOTE_HOST", "")
DATA = Path(os.environ.get("EDGEMECH_SOURCE_DATA", "workspace/edge-sample-review/source"))
ARTIFACT = Path("artifacts/edge-sample-review-20261112")


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def open_text(path):
    with path.open("rb") as handle:
        magic = handle.read(2)
    return gzip.open(path, "rt") if magic == b"\x1f\x8b" else path.open()


def json_array(path):
    """Stream the BacDive top-level array without retaining the 748 MiB corpus."""
    decoder = json.JSONDecoder()
    with path.open() as handle:
        buffer = ""
        eof = False
        while True:
            buffer = buffer.lstrip(" \n\r\t,[")
            if buffer.startswith("]"):
                return
            try:
                record, consumed = decoder.raw_decode(buffer)
            except json.JSONDecodeError:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    if eof or not buffer.strip():
                        return
                    eof = True
                    raise ValueError("Incomplete JSON array")
                buffer += chunk
            else:
                yield record
                buffer = buffer[consumed:]


def upstream(rows):
    results = {r["occurrence_id"]: [] for r in rows}

    def add(row, path, record, url, locator=None):
        text = json.dumps(record, ensure_ascii=False, sort_keys=True, indent=2)
        results[row["occurrence_id"]].append(
            {
                "source_path": str(path),
                "source_relative_path": capture_source_relative_path(path),
                "source_file_size": path.stat().st_size,
                "source_file_mtime_ns": path.stat().st_mtime_ns,
                "locator": locator,
                "retrieval_url": url,
                "text": text,
                "text_sha256": digest(text),
                "evidence_level": "source_record",
                "extractor": "source-record-json-canonical/v1",
            }
        )

    def subset(name):
        return [r for r in rows if r["origin_transform"].split("/")[0] == name]

    # BacDive records carry explicit stable strain IDs and record-level DOIs.
    wanted = subset("bacdive") + subset("mediadive")
    if wanted:
        for rec in json_array(RAW / "bacdive_strains.json"):
            bid = str(rec.get("General", {}).get("BacDive-ID", ""))
            for row in wanted:
                if (
                    ("kgmicrobe.strain:bacdive_" + bid) in [row["subject"], row["object"]]
                    or ("bacdive:" + bid) in [row["subject"], row["object"]]
                    or row["subject"]
                    == "kgmicrobe.strain:DSM-" + str(rec.get("General", {}).get("DSM-Number", ""))
                ):
                    add(
                        row,
                        RAW / "bacdive_strains.json",
                        rec,
                        "https://bacdive.dsmz.de/strain/" + bid,
                        bid,
                    )
    # Source tables: exact IDs and explicit names, preserving all candidate records.
    for transform, filename in [
        ("bactotraits", "BactoTraits_databaseV2_Jun2022.csv"),
        ("madin_etal", "madin_etal.csv"),
        ("microbedecoder", "database.csv"),
        ("lpsn", "lpsn_gss.csv"),
    ]:
        wanted = subset(transform)
        if not wanted:
            continue
        path = RAW / filename
        with path.open(encoding="latin1", newline="") as handle:
            if transform == "bactotraits":
                next(handle)
                next(handle)
            reader = csv.DictReader(handle, delimiter=";" if transform == "bactotraits" else ",")
            for ordinal, rec in enumerate(reader, 1):
                for row in wanted:
                    subject = row["subject"]
                    obj = row["object"]
                    slabel = row.get("subject_label") or ""
                    keys = set()
                    if transform == "madin_etal":
                        keys = {
                            "NCBITaxon:" + rec.get("tax_id", ""),
                            "NCBITaxon:" + rec.get("species_tax_id", ""),
                        }
                    elif transform == "bactotraits":
                        keys = {"kgmicrobe.strain:bacdive_" + rec.get("Bacdive_ID", "")}
                    elif transform == "microbedecoder":
                        keys = {
                            "lpsn:" + rec.get("LPSN_ID", ""),
                            "IMG:" + rec.get("IMG_Genome_ID", ""),
                        }
                    elif transform == "lpsn":
                        keys = {"lpsn:" + rec.get("record_no", "")}
                    name_match = bool(
                        slabel
                        and slabel
                        in {
                            rec.get("Full_name"),
                            rec.get("org_name"),
                            rec.get("species"),
                            " ".join(
                                [rec.get("genus_name", ""), rec.get("sp_epithet", "")]
                            ).strip(),
                        }
                    )
                    if subject in keys or obj in keys or name_match:
                        url = (
                            rec.get("address")
                            or rec.get("LPSN_Page_link")
                            or {
                                "madin_etal": "https://doi.org/10.1038/s41597-020-0497-4",
                                "bactotraits": "https://doi.org/10.1016/j.ecolind.2021.108047",
                                "microbedecoder": "https://microbedecoder.cn/",
                            }[transform]
                        )
                        add(row, path, rec, url, f"CSV data row {ordinal}")
    # LPSN API records; explicit source ID selection, not species-name inference.
    wanted = subset("lpsn_api")
    for row in wanted:
        ids = [
            value.split(":", 1)[1]
            for value in [row["subject"], row["object"]]
            if value.startswith("lpsn:")
        ]
        for lid in ids:
            for cache in ["api_cache", "web_cache"]:
                path = RAW / "lpsn" / cache / (lid + ".json")
                if path.is_file():
                    add(
                        row,
                        path,
                        json.loads(path.read_text()),
                        "https://lpsn.dsmz.de/taxon/" + lid,
                        lid,
                    )
    # Aggregate trait rows remain aggregate evidence, never experimental evidence.
    for transform, filename in [
        ("metatraits", "ncbi_species_summary.jsonl.gz"),
        ("metatraits_gtdb", "gtdb_species_summary.jsonl.gz"),
    ]:
        wanted = subset(transform)
        if not wanted:
            continue
        path = RAW / filename
        with open_text(path) as handle:
            for ordinal, line in enumerate(handle, 1):
                rec = json.loads(line)
                name = rec.get("tax_name", "")
                for row in wanted:
                    if name in {
                        row.get("subject_label"),
                        row.get("object_label"),
                        row["subject"].removeprefix("GTDB:").removeprefix("s__"),
                    }:
                        add(
                            row,
                            path,
                            rec,
                            "https://metatraits.embl.de/",
                            f"JSONL line {ordinal}: {name}",
                        )
    # GOLD native source table is itself the upstream export, not downstream transform.
    wanted = subset("gold")
    if wanted:
        path = RAW / "gold" / "GOLD_edges.tsv"
        with path.open() as handle:
            for ordinal, rec in enumerate(csv.DictReader(handle, delimiter="\t"), 1):
                for row in wanted:
                    if rec["subject"] == row["subject"] and rec["object"] == row["object"]:
                        add(
                            row,
                            path,
                            rec,
                            "https://gold.jgi.doe.gov/organism?id=" + row["subject"].split(":")[-1],
                            f"TSV data row {ordinal}",
                        )
    # GTDB explicit genome taxonomy and metadata records.
    wanted = subset("gtdb")
    if wanted:
        for filename in ["ar53_metadata.tsv.gz", "bac120_metadata.tsv.gz"]:
            path = RAW / "gtdb" / filename
            with open_text(path) as handle:
                for ordinal, rec in enumerate(csv.DictReader(handle, delimiter="\t"), 1):
                    accession = rec.get("accession", "")
                    taxonomy = rec.get("gtdb_taxonomy", "")
                    for row in wanted:
                        values = [row["subject"], row["object"]]
                        accession_match = any(
                            accession
                            and (
                                value.endswith(accession)
                                or value.endswith(accession.removeprefix("RS_").removeprefix("GB_"))
                            )
                            for value in values
                        )
                        taxon_match = all(
                            value.split(":", 1)[-1] in taxonomy.split(";") for value in values
                        )
                        if accession_match or (taxon_match and not results[row["occurrence_id"]]):
                            add(
                                row,
                                path,
                                rec,
                                "https://gtdb.ecogenomic.org/genome?gid=" + accession,
                                f"TSV data row {ordinal}",
                            )
    # MediaDive JSON records, keyed medium or solution IDs.
    wanted = subset("mediadive")
    if wanted:
        for filename in [
            "media_detailed.json",
            "media_strains.json",
            "solutions.json",
            "compounds.json",
        ]:
            path = RAW / "mediadive" / filename
            data = json.loads(path.read_text())
            if not isinstance(data, dict):
                continue
            for row in wanted:
                ids = [
                    v.split(":", 1)[-1]
                    for v in [row["subject"], row["object"]]
                    if v.startswith(("mediadive.", "mediadive:"))
                ]
                for key in ids:
                    if key in data:
                        add(row, path, data[key], "https://mediadive.dsmz.de/medium/" + key, key)
    # PREGO literal environmental association records include score and provenance.
    wanted = subset("prego_habitat")
    if wanted:
        for directory in [
            "environmental_samples_extracted",
            "annotated_genomes_isolates_extracted",
        ]:
            path = RAW / "prego" / directory / "database_pairs.tsv"
            with path.open() as handle:
                for ordinal, line in enumerate(handle, 1):
                    fields = line.rstrip("\n").split("\t")
                    for row in wanted:
                        values = [row["subject"], row["object"]]
                        tid = next(
                            (v.split(":", 1)[1] for v in values if v.startswith("NCBITaxon:")), None
                        )
                        habitat = next((v for v in values if not v.startswith("NCBITaxon:")), None)
                        if tid and tid in fields[:4] and habitat in fields[:4]:
                            add(
                                row,
                                path,
                                {"raw_tsv": line.rstrip("\n"), "fields": fields},
                                "https://prego.hcmr.gr/",
                                f"TSV line {ordinal}",
                            )
    # Rhea mappings from upstream reference files; direction retained.
    wanted = subset("rhea_mappings")
    if wanted:
        for filename in ["rhea2ec.tsv", "rhea2go.tsv", "rhea/rhea-directions.tsv"]:
            path = RAW / filename
            with path.open() as handle:
                for ordinal, rec in enumerate(csv.DictReader(handle, delimiter="\t"), 1):
                    vals = set(rec.values())
                    for row in wanted:
                        endpoints = [
                            row["subject"].split(":", 1)[-1],
                            row["object"].split(":", 1)[-1],
                        ]
                        if all(v in vals or ("GO:" + v) in vals for v in endpoints):
                            add(
                                row,
                                path,
                                rec,
                                "https://www.rhea-db.org/rhea/"
                                + next(
                                    (
                                        v.split(":")[-1]
                                        for v in [row["subject"], row["object"]]
                                        if v.startswith("RHEA:")
                                    ),
                                    "",
                                ),
                                f"TSV data row {ordinal}",
                            )
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--remote")
    parser.add_argument("--extract", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()
    if args.remote:
        global RAW
        payload = json.loads(base64.b64decode(args.remote))
        RAW = Path(payload["raw_root"])
        print(json.dumps(upstream(payload["rows"]), ensure_ascii=False))
        return
    if args.extract:
        if not HOST:
            raise ValueError("Set EDGEMECH_REMOTE_HOST and EDGEMECH_RAW_ROOT explicitly")
        rows = [json.loads(line) for line in (ARTIFACT / "canary.jsonl").read_text().splitlines()][
            : args.limit
        ]
        if not 1 <= len(rows) <= 50:
            raise ValueError("Only the authorized canary is permitted")
        rows = [
            {
                key: row.get(key)
                for key in [
                    "occurrence_id",
                    "origin_transform",
                    "subject",
                    "object",
                    "subject_label",
                    "object_label",
                ]
            }
            for row in rows
        ]
        payload = base64.b64encode(
            json.dumps({"raw_root": str(RAW), "rows": rows}).encode()
        ).decode()
        start = time.monotonic()
        result = subprocess.run(
            ["ssh", HOST, "python3", "-", "--remote", payload],
            input=Path(__file__).read_text(),
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode:
            raise RuntimeError(result.stderr)

        data = json.loads(result.stdout)
        DATA.mkdir(parents=True, exist_ok=True)
        (DATA / f"source-records-{len(rows)}.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        )
        (DATA / f"extraction-{len(rows)}.json").write_text(
            json.dumps(
                {
                    "elapsed_seconds": time.monotonic() - start,
                    "edges": len(rows),
                    "records": sum(map(len, data.values())),
                    "stderr": result.stderr,
                },
                indent=2,
            )
            + "\n"
        )
        print(json.dumps({key: len(value) for key, value in data.items()}))
    if args.verify:
        canary_rows = verify_claim_manifest(ARTIFACT)
        data = json.loads((DATA / "source-records-50.json").read_text())
        rows = json.loads((ARTIFACT / "source-adjudications.json").read_text())
        if len(rows) != 50 or len({r["occurrence_id"] for r in rows}) != 50:
            raise ValueError("Expected exactly 50 distinct verdicts")
        proofs = 0
        expected = {r["canary_ordinal"]: r["occurrence_id"] for r in canary_rows}
        for row in rows:
            if expected[row["canary_ordinal"]] != row["occurrence_id"]:
                raise ValueError("Canary occurrence identity mismatch")
            if row["verdict"] not in {"SUPPORTED", "CONTRADICTED", "NOT_FOUND", "NOT_ASSESSABLE"}:
                raise ValueError("Unknown verdict")
            for evidence in row.get("evidence", []):
                if evidence["record_index"] != MANUAL[row["canary_ordinal"]][2]:
                    raise ValueError("Source record index mismatch")
                rec = data[row["occurrence_id"]][evidence["record_index"]]
                if digest(rec["text"]) != rec["text_sha256"]:
                    raise ValueError("Snapshot hash mismatch")
                if evidence["text_sha256"] != rec["text_sha256"]:
                    raise ValueError("Evidence text hash does not bind the source snapshot")
                relative = source_relative_path(rec)
                if (
                    evidence["source_relative_path"] != relative
                    or evidence["locator"] != rec["locator"]
                ):
                    raise ValueError("Evidence source identity mismatch")
                if evidence["retrieval_url"] != public_evidence_url(rec):
                    raise ValueError("Evidence origin URL mismatch")
                if evidence["reference"] != MANUAL[row["canary_ordinal"]][4]:
                    raise ValueError("Evidence reference mismatch")
                if row["verdict"] in {"SUPPORTED", "CONTRADICTED"} and not evidence["reference"]:
                    raise ValueError("Directional verdict requires a DOI or PMID")
                if evidence["doi"] != evidence["reference"].removeprefix("doi:"):
                    raise ValueError("DOI mismatch")
                if rec["text"][evidence["start"] : evidence["end"]] != evidence["quote"]:
                    raise ValueError("Quote offset mismatch")
                if evidence["quote"] not in rec["text"]:
                    raise ValueError("Quote not exact")
                proofs += 1
            if row["verdict"] in {"SUPPORTED", "CONTRADICTED"} and not row.get("evidence"):
                raise ValueError("Conclusive verdict without quote")
        print(json.dumps({"verified_rows": len(rows), "verified_quotes": proofs}))


def inspect_records():
    rows = [json.loads(line) for line in (ARTIFACT / "canary.jsonl").read_text().splitlines()]
    data = json.loads((DATA / "source-records-50.json").read_text())
    selected = {int(value) for value in sys.argv[-1].split(",")}
    for row in rows:
        if row["canary_ordinal"] not in selected:
            continue
        print("\nEDGE", row["canary_ordinal"], row["subject"], row["predicate"], row["object"])
        for index, record in enumerate(data[row["occurrence_id"]]):
            print("SOURCE", index, record["locator"], record["source_path"])
            rec = json.loads(record["text"])
            if (
                row["canary_ordinal"] in {1, 2, 3, 24}
                and isinstance(rec, dict)
                and "General" in rec
            ):
                rec = {
                    key: rec.get(key)
                    for key in ["General", "External links", "Culture and growth conditions"]
                }
            elif row["origin_transform"].startswith("prego"):
                rec = {"fields": rec["fields"][:8]}
            elif row["origin_transform"].startswith("mediadive") and isinstance(rec, list):
                rec = (
                    [item for item in rec if item.get("bacdive_id") == 165511]
                    if row["canary_ordinal"] == 24
                    else {
                        "records": len(rec),
                        "note": "Inspect bound exact organism before promotion",
                    }
                )
            elif "summaries" in rec:
                terms = {
                    25: "fumarate",
                    26: "nitrate",
                    27: "manganese",
                    28: "spor",
                    29: "heterotroph",
                    30: "sal",
                    43: "nitrogen fixation",
                    44: "nitrification",
                }
                rec = {
                    "tax_name": rec["tax_name"],
                    "summaries": [
                        s for s in rec["summaries"] if terms[row["canary_ordinal"]] in s["name"]
                    ],
                }
            elif row["origin_transform"].startswith("microbedecoder"):
                rec = {
                    key: value
                    for key, value in rec.items()
                    if value not in ["", "NA"] and "sequence" not in key
                }
            elif row["origin_transform"].startswith("gtdb/"):
                rec = {
                    key: value
                    for key, value in rec.items()
                    if key.startswith(("ncbi_", "gtdb_", "accession"))
                }
            print(json.dumps(rec, ensure_ascii=False, indent=2)[:18000])


# These are individually authored adjudications, not transform-wide rules.
# Each tuple is verdict, rationale, source index, short literal quote, citation.
# Citations identify source databases/records; they are not biological article proofs.
MANUAL = {
    1: (
        "NOT_ASSESSABLE",
        "The exact strain record contains API 20E CIT positive. The original predicate METPO:2000511 is obsolete and has no declared successor; procedure provenance is verified, but full predicate correctness is unresolved.",
        0,
        '"CIT": "+"',
        "doi:10.13145/bacdive171442.20241212.9.2",
    ),
    2: (
        "SUPPORTED",
        "BacDive 139636 explicitly identifies culture CIP 53.119. The original close_match direction and strain identifiers agree; the stronger curated same_as assertion is not adjudicated here.",
        0,
        '"culture collection no.": "CIP 53.119"',
        "doi:10.13145/bacdive139636.20241212.9.2",
    ),
    3: (
        "SUPPORTED",
        "BacDive 8680 binds DSM 51066 to NCBI species 184914. The strain-to-species direction agrees under the graph convention that strains are taxonomic classes.",
        0,
        '"NCBI tax id": 184914',
        "doi:10.13145/bacdive8680.20241212.9.2",
    ),
    4: (
        "NOT_ASSESSABLE",
        "The BactoTraits CSV has no direct NCBI-ID field. Exact-name selection did not resolve the Sphingomonas molluscorum source strain; a BacDive-to-NCBI crosswalk is needed before assigning its 22–27 C optimum bin.",
        None,
        None,
        None,
    ),
    5: (
        "NOT_ASSESSABLE",
        "The BactoTraits CSV has no direct NCBI-ID field. Exact-name selection did not bind Lewinella cohaerens DSM 23179 to a source strain row, so the 1–3 percent NaCl range bin cannot yet be source-verified.",
        None,
        None,
        None,
    ),
    6: (
        "NOT_ASSESSABLE",
        "The source selection did not resolve the Pseudaeromonas sharmana name to a BactoTraits strain and historical-name crosswalk. The 1–2 pH-unit delta mapping alone does not verify this edge.",
        None,
        None,
        None,
    ),
    7: (
        "SUPPORTED",
        "The native GOLD export explicitly links Go0591365 to NCBITaxon1304 using in_taxon. The original related_to edge is a valid but less informative generalization with the same direction and identifiers.",
        0,
        '"id": "gold:Go0591365-in_taxon-NCBITaxon:1304"',
        "doi:10.1093/nar/gkac974",
    ),
    8: (
        "SUPPORTED",
        "The native GOLD export binds Go0688105 to NCBITaxon297314 using in_taxon. Original related_to retains the relationship but loses its taxonomic specificity; the uncultured label is not independent species validation.",
        0,
        '"id": "gold:Go0688105-in_taxon-NCBITaxon:297314"',
        "doi:10.1093/nar/gkac974",
    ),
    9: (
        "SUPPORTED",
        "GOLD explicitly assigns organism Go0545989 to NCBITaxon2056175. Original related_to preserves endpoints and direction as a broader relation.",
        0,
        '"id": "gold:Go0545989-in_taxon-NCBITaxon:2056175"',
        "doi:10.1093/nar/gkac974",
    ),
    10: (
        "SUPPORTED",
        "GTDB metadata accession GB_GCA_016931655.1 places the genome in species JAFGEJ01 sp016931655. Removal of the GB prefix and space-to-underscore encoding preserve the identifiers and membership direction.",
        0,
        "s__JAFGEJ01 sp016931655",
        "doi:10.1093/nar/gkab776",
    ),
    11: (
        "NOT_ASSESSABLE",
        "This edge is a GTDB-species to NCBI-taxonomy crosswalk. The genome-accession selector did not retrieve the required Kaistella/Chryseobacterium crosswalk; a label match alone would not verify close_match.",
        None,
        None,
        None,
    ),
    12: (
        "SUPPORTED",
        "GTDB metadata accession RS_GCF_030540985.1 gives species Pseudomonas aeruginosa. The original assembly in_taxon edge preserves the exact RefSeq assembly and GTDB species.",
        0,
        "s__Pseudomonas aeruginosa",
        "doi:10.1093/nar/gkab776",
    ),
    13: (
        "SUPPORTED",
        "LPSN GSS record5318 is Paracoccus tegillarcae and explicitly names genus Paracoccus; separate GSS record516256 is that genus. The child-to-genus direction and both name-record IDs agree.",
        0,
        '"genus_name": "Paracoccus"',
        "doi:10.1099/ijsem.0.004332",
    ),
    14: (
        "NOT_ASSESSABLE",
        "LPSN record789102 identifies Aliivibrio sifiae and its type strains, but the GSS source has no NCBI566293 cross-reference. The NCBI endpoint needs an independent identifier binding.",
        0,
        '"sp_epithet": "sifiae"',
        "doi:10.1099/ijsem.0.004332",
    ),
    15: (
        "SUPPORTED",
        "LPSN GSS record786247 names genus Zhihengliuella and the separately retrieved genus record517557 confirms that ID. Species-to-genus subclass direction agrees.",
        0,
        '"genus_name": "Zhihengliuella"',
        "doi:10.1099/ijsem.0.004332",
    ),
    16: (
        "SUPPORTED",
        "LPSN API record777891 explicitly sets parent517071. It is a synonym, but the original name-record hierarchy is faithfully represented rather than silently promoted to current accepted nomenclature.",
        0,
        '"lpsn_parent_id": 517071',
        "doi:10.83108/rn.777891",
    ),
    17: (
        "CONTRADICTED",
        "The source identifies this DOI as the publication describing Hoeflea halophila, not a taxonomic concept equivalent to the organism. Original taxon close_match publication has the wrong predicate/domain; curated mentions is a separate claim.",
        0,
        '"publication_doi": "10.1007/s10482-013-9876-6"',
        "doi:10.83108/rn.791057",
    ),
    18: (
        "SUPPORTED",
        "The Rhizobium herbae name record explicitly has parent517106 (Rhizobium). The source also marks the name a synonym; that status does not invalidate its recorded name hierarchy.",
        0,
        '"lpsn_parent_id": 517106',
        "doi:10.83108/rn.789390",
    ),
    19: (
        "SUPPORTED",
        "Madin data row160570 (PATRIC provenance) has exact tax_id1410799 and name W48906 with gram_stain positive. Another row with the same taxon leaves the trait unavailable; unavailable is not negative evidence.",
        1,
        '"gram_stain": "positive"',
        "doi:10.1038/s41597-020-0497-4",
    ),
    20: (
        "SUPPORTED",
        "Madin rows151076 and151077 assign gram_stain negative to tax_id1330457; other exact-ID rows bind that taxon to O157:H7 SS52. The edge correctly represents the explicit strain-level source field.",
        2,
        '"gram_stain": "negative"',
        "doi:10.1038/s41597-020-0497-4",
    ),
    21: (
        "SUPPORTED",
        "Madin row47799 explicitly binds CIAM1775 and tax_id1041152 and states sporulation no. This supports source fidelity of the negative sporulation phenotype, without establishing independent experimental support.",
        0,
        '"sporulation": "no"',
        "doi:10.1038/s41597-020-0497-4",
    ),
    22: (
        "NOT_ASSESSABLE",
        "MediaDive84 has many growth-positive Streptomyces strain records but no NCBI1931 field. The particular BacDive/GTDB strain-to-species bridge behind this edge was not recovered; recipe existence and genus membership are insufficient.",
        0,
        '"name": "ROLLED OATS MINERAL MEDIUM"',
        "doi:10.1093/nar/gkac803",
    ),
    23: (
        "NOT_ASSESSABLE",
        "A MediaDive solution record was retrieved, but the source compound-ID18 to CHEBI176843 mapping has not been independently bound. Vitamin B12 as a name alone does not prove chemical identifier correctness.",
        None,
        None,
        None,
    ),
    24: (
        "SUPPORTED",
        "MediaDive J14 lists BacDive165511/JCM7297 with growth1; the separate BacDive record identifies Clostridium septicum. This verifies the exact strain-medium pair rather than extrapolating from species-wide growth.",
        2,
        '"bacdive_id": 165511,\n    "ccno": "JCM 7297",\n    "domain": "B",\n    "growth": 1',
        "doi:10.1093/nar/gkac803",
    ),
    25: (
        "NOT_ASSESSABLE",
        "Exact Lactobacillus algidus selection did not bind a MetaTraits raw taxon row. Historical synonyms and the original summary lineage need resolving before judging the negative fumarate-reduction predicate.",
        None,
        None,
        None,
    ),
    26: (
        "NOT_ASSESSABLE",
        "The exact Alcanivorax borkumensis aggregate contains nitrate reduction true98.39%/false1.61%, while electron-acceptor, denitrification and ammonification summaries are false100%. The edge lacks the original summary-name lineage needed to distinguish a valid minority assertion from a predicate-mapping error.",
        0,
        '"name": "reduction: nitrate"',
        "doi:10.1093/nar/gkaf1241",
    ),
    27: (
        "SUPPORTED",
        "The exact Vibrio furnissii aggregate reports oxidation:manganese false100% across11observations. The negative predicate preserves that source polarity. Element name Manganese matches the concept label; no oxidation-state-specific claim is made.",
        0,
        '"majority_label": "false: (100%)",\n      "name": "oxidation: manganese"',
        "doi:10.1093/nar/gkaf1241",
    ),
    28: (
        "NOT_ASSESSABLE",
        "The exact source says generic sporulation true100%, but METPO1000870 specifically defines dormant stress-resistant endospores. The source does not distinguish endospores from Actinoplanes sporangial spores, so the narrower ontology mapping is unverified.",
        0,
        '"majority_label": "true: (100%)",\n      "name": "sporulation"',
        "doi:10.1093/nar/gkaf1241",
    ),
    29: (
        "SUPPORTED",
        "Actinophytocola xinjiangensis has growth:chemoheterotrophy true100% in the GTDB-keyed aggregate. The phenotype agrees with that explicit source term; this remains one aggregate observation rather than a new strain experiment.",
        0,
        '"majority_label": "true: (100%)",\n      "name": "growth: chemoheterotrophy"',
        "doi:10.1093/nar/gkaf1241",
    ),
    30: (
        "CONTRADICTED",
        "The source reports salinity maximum1.8% and growth/minimum0%. The edge turns an upper tolerance limit into a phenotype requiring0.3–0.8M NaCl for optimal growth. Maximum tolerated salinity cannot be reinterpreted as an optimal requirement.",
        0,
        '"majority_label": "Median: 1.8 % NaCl (w/v)",\n      "name": "salinity maximum"',
        "doi:10.1093/nar/gkaf1241",
    ),
    31: (
        "SUPPORTED",
        "The MicrobeDecoder row for LPSN791062 lists acetate among Bergey_Major_end_products and has matching type strains DSM2028/ATCC25083. Produces acetate preserves the source assertion; its Bergey article DOI is explicitly present in that row.",
        0,
        '"Bergey_Major_end_products": "ethanol;acetate;CO2;H2"',
        "doi:10.1002/9781118960608.gbm01248",
    ),
    32: (
        "CONTRADICTED",
        "The transform copies NCBI1281099 from its source, but the same source row identifies the LPSN organism as archaeal Methanomethylophilus alvi and the NCBI organism as Escherichia coli. This is an internally inconsistent crosswalk, so close_match fails identifier correctness despite faithful copying.",
        0,
        '"NCBI_Species": "Escherichia coli",\n  "NCBI_Taxonomy_ID": "1281099"',
        "doi:10.1093/nar/gkag515",
    ),
    33: (
        "SUPPORTED",
        "The Eucapsis microscopica source row includes the literal FAPROTAX token photosynthetic_cyanobacteria. Original has_attribute only reports that source value, so it is faithful; the later curated photosynthesis mapping is not evaluated here.",
        0,
        "photosynthetic_cyanobacteria",
        "doi:10.1093/nar/gkag515",
    ),
    34: (
        "SUPPORTED",
        "PREGO has the exact taxon1797267/environmentENVO00002258 pair, source annotation Loam, and score4. Habitat-to-taxon direction is the inverse of the listed pair but preserves location_of semantics. This is fidelity to a mined annotation, not independent ecology evidence.",
        0,
        '"Loam",\n    "4"',
        "doi:10.3390/microorganisms10020293",
    ),
    35: (
        "SUPPORTED",
        "The exact PREGO taxon1798676/soilENVO00001998 association has an explicit JGI IMG score3 row matching the sampled occurrence. A second score4 row is kept separate; no duplicate-collapse inference is made.",
        0,
        '"Metagenome-Assembled Genome",\n    "3"',
        "doi:10.3390/microorganisms10020293",
    ),
    36: (
        "SUPPORTED",
        "The source includes ENVO01000155/taxon6945 in MG-RAST amplicon data,40 of1541samples,score4, matching the sampled statistical association. Ixodes is a tick; source fidelity does not make this a microbial biological assertion.",
        2,
        '"40 of 1541 samples",\n    "4"',
        "doi:10.3390/microorganisms10020293",
    ),
    37: (
        "NOT_ASSESSABLE",
        "The bounded extractor checks Rhea mapping/direction files but does not resolve RDF reaction-side participant nodes. RHEA75099 to CHEBI229705 therefore lacks a retrieved participant record; a reaction label containing bilirubin is insufficient.",
        None,
        None,
        None,
    ),
    38: (
        "SUPPORTED",
        "The authoritative Rhea-to-EC mapping explicitly assigns undirected/master21188 to EC6.3.1.5. Original close_match represents a curated reaction-to-enzyme-class mapping without asserting taxon capability.",
        0,
        '"ID": "6.3.1.5",\n  "MASTER_ID": "21188",\n  "RHEA_ID": "21188"',
        "doi:10.1093/nar/gkab1016",
    ),
    39: (
        "SUPPORTED",
        "Rhea directions explicitly give master57792 and left-to-right57793. The original directionalReaction edge preserves both identifiers and direction.",
        0,
        '"RHEA_ID_LR": "57793",\n  "RHEA_ID_MASTER": "57792"',
        "doi:10.1093/nar/gkab1016",
    ),
    40: (
        "SUPPORTED",
        "The Alloyangia pacifica row literally records Bergey_Type_of_metabolism Other. Original has_attribute faithfully preserves that uninformative source string; source fidelity does not oppose omitting it for usefulness.",
        0,
        '"Bergey_Type_of_metabolism": "Other"',
        "doi:10.1002/9781118960608.gbm01671",
    ),
    41: (
        "SUPPORTED",
        "The Trinickia caryophylli row literally records Bergey_Type_of_metabolism Other. Original reported-value attribute is faithful even though the value provides no actionable metabolic mechanism.",
        0,
        '"Bergey_Type_of_metabolism": "Other"',
        "doi:10.1002/9781118960608.gbm02068",
    ),
    42: (
        "SUPPORTED",
        "The Rickettsiella chironomi row records metabolism Other and states no culture has been isolated. The original has_attribute reports the literal source field, not an experimentally established trait.",
        0,
        '"Bergey_Type_of_metabolism": "Other"',
        "doi:10.1002/9781118960608.gbm01177",
    ),
    43: (
        "CONTRADICTED",
        "For the exact HOT-871 taxon the nitrogen-fixation summary is false100% over10observations. An unqualified positive capable_of assertion reverses this source polarity; this supports the rationale for omitting the positive edge.",
        0,
        '"majority_label": "false: (100%)",\n      "name": "nitrogen fixation"',
        "doi:10.1093/nar/gkaf1241",
    ),
    44: (
        "CONTRADICTED",
        "The exact Streptomyces fagopyri summary states nitrification false100%. Original positive capable_of conflicts with that source polarity; it does not establish organism-wide biological impossibility.",
        0,
        '"majority_label": "false: (100%)",\n      "name": "nitrification"',
        "doi:10.1093/nar/gkaf1241",
    ),
    45: (
        "SUPPORTED",
        "The source row for LPSN5861 lists IMG2772190913 in its genome-ID field. The original genome-to-name in_taxon edge faithfully copies this membership; its missing node is an independent graph-integrity reason for omission.",
        0,
        '"IMG_Genome_ID": "2882585947,2772190913"',
        "doi:10.1093/nar/gkag515",
    ),
    46: (
        "SUPPORTED",
        "The source row for LPSN788336 explicitly gives IMG2770939627. Genome-to-name membership and direction are faithful to this source even though the graph node is absent and other crosswalk columns require separate validation.",
        0,
        '"IMG_Genome_ID": "2770939627"',
        "doi:10.1093/nar/gkag515",
    ),
    47: (
        "SUPPORTED",
        "The Aromatoleum toluvorans row includes anaerobe in the semicolon-separated BacDive_Oxygen_tolerance field. Original reported-value has_attribute is faithful. It does not mean obligate anaerobe, since aerobe appears in the same field.",
        0,
        '"BacDive_Oxygen_tolerance": "aerobe;anaerobe"',
        "doi:10.1093/nar/gkag515",
    ),
    48: (
        "SUPPORTED",
        "The Longimycelium tulufanense row includes alkaline phosphatase in BacDive_Enzyme_activity. This verifies the original literal reported-value attribute only; the ultimate BacDive-to-LPSN alignment remains a separate biological-provenance concern.",
        0,
        "alkaline phosphatase",
        "doi:10.1093/nar/gkag515",
    ),
    49: (
        "SUPPORTED",
        "PREGO contains the exact agricultural-soil/taxon547558 direction with80 of137samples and score2.11372486057172. The statistical source association is copied faithfully; the score below3 remains an independently valid omission criterion.",
        1,
        '"80 of 137 samples",\n    "2.11372486057172"',
        "doi:10.3390/microorganisms10020293",
    ),
    50: (
        "SUPPORTED",
        "PREGO contains the exact anthropogenic-material/taxon592026 direction with35 of60samples and score1.51164782671173. The original association is source-faithful while failing the retention score threshold.",
        1,
        '"35 of 60 samples",\n    "1.51164782671173"',
        "doi:10.3390/microorganisms10020293",
    ),
}


def author():
    records = json.loads((DATA / "source-records-50.json").read_text())
    rows = verify_claim_manifest(ARTIFACT)
    output = []
    for row in rows:
        ordinal = row["canary_ordinal"]
        verdict, rationale, index, quote, citation = MANUAL[ordinal]
        evidence = []
        if index is not None:
            record = records[row["occurrence_id"]][index]
            if quote not in record["text"]:
                raise ValueError(f"Edge {ordinal} quote is not exact: {quote!r}")
            public_source = source_relative_path(record)
            url = record["retrieval_url"]
            if "database.csv" == public_source:
                url = "https://github.com/thackmann/MicrobeDecoder/raw/main/Shiny/MicrobeDecoder/data/database/database.zip"
            elif public_source.startswith(("ncbi_", "gtdb_species")):
                url = "https://metatraits.embl.de/"
            elif public_source == "madin_etal.csv":
                url = "https://github.com/bacteria-archaea-traits/bacteria-archaea-traits/blob/master/output/condensed_traits_NCBI.csv"
            evidence.append(
                {
                    "record_index": index,
                    "quote": quote,
                    "text_sha256": record["text_sha256"],
                    "start": record["text"].index(quote),
                    "end": record["text"].index(quote) + len(quote),
                    "extractor": record["extractor"],
                    "evidence_level": "source_record",
                    "retrieval_url": url,
                    "retrieval_mode": "retained upstream snapshot; public origin URL",
                    "source_relative_path": public_source,
                    "locator": record["locator"],
                    "reference": citation,
                    "doi": citation.removeprefix("doi:"),
                    "reference_role": "source record or database provenance; not a biological-paper proof",
                }
            )
        output.append(
            {
                "canary_ordinal": ordinal,
                "occurrence_id": row["occurrence_id"],
                "origin_transform": row["origin_transform"],
                "claim_target": "original rule-labeled edge",
                "verdict": verdict,
                "rationale": rationale,
                "evidence": evidence,
                "adjudicating_model": "GPT-6 (runtime model not more specifically exposed)",
                "source_records_examined": len(records[row["occurrence_id"]]),
                "source_protocol": "exact ID/name selection in upstream snapshots; conditional mapping review; no inherited verdicts",
            }
        )
    (ARTIFACT / "source-adjudications.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n"
    )
    from collections import Counter

    print(json.dumps(dict(Counter(row["verdict"] for row in output))))


def public_evidence_url(record):
    """Public origin for a private retained source record; never expose its host/path."""
    relative = source_relative_path(record)
    if relative == "database.csv":
        return "https://github.com/thackmann/MicrobeDecoder/raw/main/Shiny/MicrobeDecoder/data/database/database.zip"
    if relative.startswith(("ncbi_", "gtdb_species")):
        return "https://metatraits.embl.de/"
    if relative == "madin_etal.csv":
        return "https://github.com/bacteria-archaea-traits/bacteria-archaea-traits/blob/master/output/condensed_traits_NCBI.csv"
    return record["retrieval_url"]


def _validated_public_relative(value):
    """Reject absolute, escaping or noncanonical paths before public serialization."""
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("Source relative path must be a nonempty POSIX path")
    path = Path(value)
    if not path.parts or path.is_absolute() or ".." in path.parts or ":" in path.parts[0]:
        raise ValueError("Source path must remain relative to the configured raw root")
    if path.as_posix() != value or value == ".":
        raise ValueError("Source relative path must be canonical")
    return value


def capture_source_relative_path(path, raw_root=None):
    """Bind a newly captured source file to its configured root without leaking it."""
    root = RAW if raw_root is None else Path(raw_root)
    try:
        relative = Path(path).resolve().relative_to(root.resolve()).as_posix()
    except ValueError as error:
        raise ValueError("Source file is outside the configured raw root") from error
    return _validated_public_relative(relative)


def source_relative_path(record, raw_root=None):
    """Read capture-time relative identity or safely adapt pre-relative snapshots."""
    if "source_relative_path" in record:
        return _validated_public_relative(record["source_relative_path"])
    original = record.get("source_path")
    if not isinstance(original, str) or not original:
        raise ValueError("Source snapshot lacks its path identity")
    # Historical private snapshots predate explicit relative-path capture. Only the
    # known legacy marker is stripped; an unrecognized absolute path never escapes.
    if "/data/raw/" in original:
        return _validated_public_relative(original.split("/data/raw/", 1)[1])
    return capture_source_relative_path(original, raw_root)


def verify_claim_manifest(artifact_root=ARTIFACT):
    """Reject any changed canary claim before replaying its existing source verdict."""
    root = Path(artifact_root)
    metadata = json.loads((root / "sampling-metadata.json").read_text())
    key = (ARTIFACT / "canary.jsonl").as_posix()
    expected_hash = metadata.get("hashes", {}).get(key)
    if not isinstance(expected_hash, str) or len(expected_hash) != 64:
        raise ValueError("Sampling metadata lacks the pinned canary hash")
    raw = (root / "canary.jsonl").read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_hash:
        raise ValueError("Canary claims do not match the pinned sampling metadata")
    return [json.loads(line) for line in raw.decode("utf-8").splitlines()]


if __name__ == "__main__":
    if "--inspect" in sys.argv:
        inspect_records()
    elif "--author" in sys.argv:
        author()
    else:
        main()
