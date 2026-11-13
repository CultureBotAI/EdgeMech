"""Inspect, time, persist and verify individual recanary source decisions, PR76, 2026-11-13.

Inputs: retained per-edge source packets and human/agent authored judgments.
Outputs: private timing/decision files, private name/reference targeting bundle,
and short-quote public ledger. There is no automatic scientific verdict table.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from review_clock import begin_review, finish_review

CITATIONS = {
    "bacdive": "doi:10.1093/nar/gkab961",
    "bactotraits": "doi:10.1016/j.ecolind.2021.108047",
    "gold": "doi:10.1093/nar/gkac974",
    "gtdb": "doi:10.1093/nar/gkab776",
    "lpsn": "doi:10.1099/ijsem.0.004332",
    "lpsn_api": "doi:10.1099/ijsem.0.004332",
    "madin_etal": "doi:10.1038/s41597-020-0497-4",
    "mediadive": "doi:10.1093/nar/gkac803",
    "metatraits": "doi:10.1093/nar/gkaf1241",
    "metatraits_gtdb": "doi:10.1093/nar/gkaf1241",
    "microbedecoder": "doi:10.1093/nar/gkag515",
    "prego_habitat": "doi:10.3390/microorganisms10020293",
    "rhea_mappings": "doi:10.1093/nar/gkab1016",
}
PRIMARY_FILES = {
    "bacdive": ["bacdive_strains.json"],
    "bactotraits": ["BactoTraits_databaseV2_Jun2022.csv"],
    "gold": ["gold/GOLD_edges.tsv"],
    "gtdb": ["gtdb/"],
    "lpsn": ["lpsn_gss.csv", "lpsn/"],
    "lpsn_api": ["lpsn/"],
    "madin_etal": ["madin_etal.csv"],
    "mediadive": ["mediadive/"],
    "metatraits": ["ncbi_species_summary.jsonl.gz"],
    "metatraits_gtdb": ["gtdb_species_summary.jsonl.gz"],
    "microbedecoder": ["database.csv"],
    "prego_habitat": ["prego/"],
    "rhea_mappings": ["rhea", "rhea2"],
}


def private_packet(source_dir, ordinal):
    return Path(source_dir) / "packets" / f"{ordinal:02d}.json"


def display(packet):
    edge = packet["edge"]
    transform = edge["origin_transform"].split("/")[0]
    print(
        json.dumps(
            {
                "edge": {
                    k: edge.get(k)
                    for k in [
                        "canary_ordinal",
                        "occurrence_id",
                        "origin_transform",
                        "subject",
                        "subject_label",
                        "predicate",
                        "object",
                        "object_label",
                        "disposition",
                    ]
                },
                "object_definition": (edge.get("original_object_node") or {}).get("description"),
                "dataset_provenance_reference": CITATIONS[transform],
            },
            ensure_ascii=False,
        )
    )
    shown = 0
    for index, record in enumerate(packet["records"]):
        path = record["source_relative_path"]
        if not any(path.startswith(prefix) for prefix in PRIMARY_FILES[transform]):
            continue
        value = json.loads(record["text"])
        if isinstance(value, dict) and "summaries" in value:
            target = (edge.get("object_label") or "").lower()
            terms = {
                25: ["nitrate"],
                26: ["xylan"],
                27: ["fumarate"],
                28: ["tartrate"],
                29: ["plastic"],
                30: ["galactar"],
                43: ["nitrogen fixation"],
                44: ["psychro", "temperature"],
            }.get(edge["canary_ordinal"], [target])
            value = {
                "tax_name": value["tax_name"],
                "summaries": [
                    s
                    for s in value["summaries"]
                    if any(term in s["name"].lower() for term in terms)
                ],
            }
        elif path == "bacdive_strains.json":
            value = {
                k: value.get(k)
                for k in [
                    "General",
                    "External links",
                    "Name and taxonomic classification",
                    "Isolation, sampling and environmental information",
                    "Culture and growth conditions",
                ]
            }
        elif path.startswith("gtdb/"):
            value = {
                k: v
                for k, v in value.items()
                if k
                in [
                    "accession",
                    "gtdb_taxonomy",
                    "ncbi_taxid",
                    "ncbi_species_taxid",
                    "ncbi_taxonomy",
                    "ncbi_organism_name",
                ]
            }
        elif path == "database.csv":
            value = {k: v for k, v in value.items() if v not in ["NA", ""] and "sequence" not in k}
        elif path.startswith("prego/"):
            value = {"fields": value["fields"][:8]}
        elif isinstance(value, list) and path == "mediadive/media_strains.json":
            bid = re.search(r"bacdive_(\d+)", edge["subject"])
            if bid:
                value = [r for r in value if str(r.get("bacdive_id")) == bid.group(1)]
            else:
                target = edge.get("subject_label") or ""
                value = [r for r in value if r.get("species", "").startswith(target)]
        print(
            json.dumps(
                {
                    "record_index": index,
                    "source_relative_path": path,
                    "locator": record["locator"],
                    "binding": record.get("binding"),
                    "text_sha256": record["text_sha256"],
                    "data": value,
                },
                ensure_ascii=False,
            )
        )
        shown += 1
    print(json.dumps({"primary_records_shown": shown, "all_records": len(packet["records"])}))


def evidence_for(packet, item):
    index = item["record_index"]
    if not isinstance(index, int) or index < 0 or index >= len(packet["records"]):
        raise ValueError("Invalid record index")
    record = packet["records"][index]
    text = record["text"]
    if hashlib.sha256(text.encode()).hexdigest() != record["text_sha256"]:
        raise ValueError("Retained source text hash mismatch")
    quote = item["quote"]
    if not quote.strip() or quote not in text:
        raise ValueError("Quote must occur literally in retained source text")
    if len(quote.split()) > 40:
        raise ValueError("Use a short source excerpt")
    reference = item.get("reference") or CITATIONS[packet["edge"]["origin_transform"].split("/")[0]]
    if not re.fullmatch(r"(?:doi:10\.\d{4,9}/\S+|PMID:\d+)", reference):
        raise ValueError("Evidence needs a DOI or PMID")
    relative = record["source_relative_path"]
    if Path(relative).is_absolute() or ".." in Path(relative).parts or "\\" in relative:
        raise ValueError("Invalid public relative source path")
    return {
        "record_index": index,
        "quote": quote,
        "start": text.index(quote),
        "end": text.index(quote) + len(quote),
        "text_sha256": record["text_sha256"],
        "source_relative_path": relative,
        "locator": record["locator"],
        "retrieval_url": record["retrieval_url"],
        "extractor": record["extractor"],
        "evidence_level": "source_record",
        "reference": reference,
        "reference_role": "source database or record provenance; not scientific literature proof",
    }


def finish(source_dir, review_root, ordinal, verdict, rationale, evidence):
    if verdict not in {"SUPPORTED", "CONTRADICTED", "NOT_FOUND", "NOT_ASSESSABLE"}:
        raise ValueError("Invalid source verdict")
    packet = json.loads(private_packet(source_dir, ordinal).read_text())
    proof = [evidence_for(packet, item) for item in evidence]
    if verdict in {"SUPPORTED", "CONTRADICTED"} and not proof:
        raise ValueError("Directional verdict requires a verified quote")
    if not rationale.strip():
        raise ValueError("Rationale required")
    edge = packet["edge"]
    decision = {
        "canary_ordinal": ordinal,
        "occurrence_id": edge["occurrence_id"],
        "origin_transform": edge["origin_transform"],
        "claim_target": "original rule-labeled edge",
        "verdict": verdict,
        "rationale": rationale,
        "evidence": proof,
        "adjudicating_model": "GPT-6 (runtime model not more specifically exposed)",
        "source_records_examined": len(packet["records"]),
    }
    receipt = finish_review(review_root, "source", str(ordinal), decision)
    print(
        json.dumps(
            {"ordinal": ordinal, "verdict": verdict, "elapsed_seconds": receipt["elapsed_seconds"]}
        )
    )


def targeting(source_dir, output):
    packets = sorted((Path(source_dir) / "packets").glob("*.json"))
    result = []
    for path in packets:
        packet = json.loads(path.read_text())
        edge = packet["edge"]
        refs, strains = [], set()
        seen = set()
        for index, record in enumerate(packet["records"]):
            rec = json.loads(record["text"])
            if not isinstance(rec, dict):
                continue
            candidates = []
            if record["source_relative_path"].startswith("lpsn/"):
                strains.update(rec.get("type_strain_names", []))
                if rec.get("publication_doi"):
                    candidates.append(
                        (
                            "publication_doi",
                            rec["publication_doi"],
                            "species_description",
                            rec.get("publication_text", ""),
                        )
                    )
                for emendation in rec.get("emendations", []):
                    if emendation.get("publication_doi"):
                        candidates.append(
                            (
                                "publication_doi",
                                emendation["publication_doi"],
                                "species_description",
                                emendation.get("publication_text", ""),
                            )
                        )
            if record["source_relative_path"] == "bacdive_strains.json":
                classification = rec.get("Name and taxonomic classification", {})
                strain = classification.get("strain designation")
                if isinstance(strain, str):
                    strains.add(strain)
                external = rec.get("External links", {})
                external = external if isinstance(external, list) else [external]
                for value in external:
                    if value.get("culture collection no."):
                        strains.add(str(value["culture collection no."]))
                references = rec.get("Reference", [])
                references = references if isinstance(references, list) else [references]
                for ref in references:
                    val = ref.get("doi/url", "")
                    val = val.removeprefix("https://doi.org/").removeprefix("http://dx.doi.org/")
                    if (
                        val.startswith("10.")
                        and not val.startswith(("10.13145/", "10.83108/", "10.60712/"))
                        and "doi:" + val not in CITATIONS.values()
                    ):
                        candidates.append(
                            (
                                "doi/url",
                                ref["doi/url"],
                                "strain_reference",
                                ref.get("title", ""),
                            )
                        )
            if record["source_relative_path"] == "database.csv":
                for field in ["Bergey_Article_link", "Literature_Citation"]:
                    val = rec.get(field, "")
                    match = re.search(r"10\.\d{4,9}/[^\s;]+", val)
                    if match:
                        candidates.append((field, match.group(0), "row_primary", val))
            for field, val, role, title in candidates:
                doi = val.removeprefix("https://doi.org/").removeprefix("http://dx.doi.org/")
                if doi in seen:
                    continue
                seen.add(doi)
                quote = (
                    json.dumps(field, ensure_ascii=False)
                    + ": "
                    + json.dumps(val, ensure_ascii=False)
                )
                if quote not in record["text"]:
                    quote = val
                if quote not in record["text"]:
                    raise ValueError("Targeting citation is not in retained source")
                refs.append(
                    {
                        "reference": "doi:" + doi,
                        "role": role,
                        "title": title,
                        "identity_verified": True,
                        "identity_verification_scope": "association to raw source record only; retrieved paper identity remains unverified",
                        "identity_basis": {
                            "quote": quote,
                            "text_sha256": record["text_sha256"],
                            "source_relative_path": record["source_relative_path"],
                            "url": record["retrieval_url"],
                            "record_index": index,
                            "source_binding": record.get("binding"),
                        },
                    }
                )
        result.append(
            {
                "canary_ordinal": edge["canary_ordinal"],
                "occurrence_id": edge["occurrence_id"],
                "resolved_names": packet.get("resolved_names", []),
                "strain_designations": sorted(strains),
                "primary_references": refs,
            }
        )
    Path(output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(
        json.dumps(
            {"edges": len(result), "references": sum(len(r["primary_references"]) for r in result)}
        )
    )


def verify_claim_manifest(artifact_root):
    """Reject changed public claims before replaying private source decisions (#79)."""
    artifact_root = Path(artifact_root)
    metadata = json.loads((artifact_root / "sampling-metadata.json").read_text())
    raw = (artifact_root / "canary.jsonl").read_bytes()
    key = "artifacts/edge-recanary-20261113/canary.jsonl"
    if hashlib.sha256(raw).hexdigest() != metadata["hashes"][key]:
        raise ValueError("Public canary does not match its pinned sampling hash")
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    if len(rows) != 50 or {r["canary_ordinal"] for r in rows} != set(range(1, 51)):
        raise ValueError("Expected fifty unique public canary ordinals")
    if len({r["occurrence_id"] for r in rows}) != 50:
        raise ValueError("Expected fifty unique public canary occurrences")
    return {row["canary_ordinal"]: row for row in rows}


def verify_source_claim(packet_edge, public_edge):
    """Bind preserved original claim semantics across private/public sanitization."""
    for field in [
        "canary_ordinal",
        "occurrence_id",
        "origin_transform",
        "transform_row_number",
        "subject",
        "predicate",
        "object",
        "subject_label",
        "predicate_label",
        "object_label",
        "disposition",
    ]:
        if packet_edge.get(field) != public_edge.get(field):
            raise ValueError(f"Source packet differs from public claim field: {field}")


def export(source_dir, review_root, output, artifact_root=None):
    if artifact_root is None:
        artifact_root = Path(__file__).resolve().parents[3] / "artifacts/edge-recanary-20261113"
    public_claims = verify_claim_manifest(artifact_root)
    root = Path(review_root)
    rows = []
    for ordinal in range(1, 51):
        decision_path = root / "decisions" / "source" / f"{ordinal}.json"
        timer = json.loads((root / "timing" / "source" / f"{ordinal}.json").read_text())
        raw = decision_path.read_bytes()
        if (
            hashlib.sha256(raw).hexdigest() != timer["decision_sha256"]
            or timer["status"] != "finished"
        ):
            raise ValueError("Decision is not bound to finished timing receipt")
        packet_path = private_packet(source_dir, ordinal)
        if hashlib.sha256(packet_path.read_bytes()).hexdigest() != timer["packet_sha256"]:
            raise ValueError("Packet changed after adjudication")
        packet = json.loads(packet_path.read_text())
        verify_source_claim(packet["edge"], public_claims[ordinal])
        decision = json.loads(raw)
        if (
            decision["occurrence_id"] != packet["edge"]["occurrence_id"]
            or decision["canary_ordinal"] != ordinal
            or decision["origin_transform"] != packet["edge"]["origin_transform"]
        ):
            raise ValueError("Occurrence identity mismatch")
        for proof in decision["evidence"]:
            if evidence_for(packet, proof) != proof:
                raise ValueError("Evidence metadata mismatch")
        decision["adjudication_timing"] = {
            key: timer[key]
            for key in [
                "started_at",
                "stopped_at",
                "elapsed_seconds",
                "packet_sha256",
                "decision_sha256",
            ]
        }
        rows.append(decision)
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
    print(
        json.dumps(
            {
                "verified_rows": len(rows),
                "adjudication_seconds": sum(
                    row["adjudication_timing"]["elapsed_seconds"] for row in rows
                ),
            }
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["begin", "finish", "targeting", "export"])
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--review-root", type=Path)
    parser.add_argument("--ordinal", type=int)
    parser.add_argument("--verdict")
    parser.add_argument("--rationale")
    parser.add_argument("--evidence-json", default="[]")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--artifact-root", type=Path)
    args = parser.parse_args()
    if args.action == "begin":
        display(
            begin_review(
                args.review_root,
                "source",
                str(args.ordinal),
                private_packet(args.source_dir, args.ordinal),
            )["packet"]
        )
    elif args.action == "finish":
        finish(
            args.source_dir,
            args.review_root,
            args.ordinal,
            args.verdict,
            args.rationale,
            json.loads(args.evidence_json),
        )
    elif args.action == "targeting":
        targeting(args.source_dir, args.output)
    else:
        export(args.source_dir, args.review_root, args.output, args.artifact_root)


if __name__ == "__main__":
    main()
