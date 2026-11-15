"""Bind search candidates to exact source organisms; EdgeMech #88/#91, 2026-11-14.

Inputs: retained source packets or verified targeting names/strain designations.
Outputs: source-indexed identity proofs and bounded, organism-anchored queries.
No network, scientific verdicts, or changes to the frozen November 13 artifacts.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from source_extract import normalized_names

POLICY = "exact-organism-source-bindings/v2"


def strain_aliases(values):
    """Split source lists, remove duplicates, and refuse query syntax as data."""
    aliases = []
    for value in values:
        if not isinstance(value, str):
            raise ValueError("Strain designations must be strings")
        for part in re.split(r"[;,]", value):
            alias = " ".join(part.split())
            if not alias:
                continue
            if not re.fullmatch(r"[\w ./'()+-]+", alias) or '"' in alias:
                raise ValueError("Unsafe strain designation")
            if alias.casefold() not in {v.casefold() for v in aliases}:
                aliases.append(alias)
    return aliases


def name_query(names):
    names = list(dict.fromkeys(names))
    if not names:
        raise ValueError("A verified organism-name anchor is required")
    if any(not isinstance(n, str) or not n.strip()
           or not re.fullmatch(r"[\w ./\[\]'()+-]+", n)
           or not any(character.isalpha() for character in n) for n in names):
        raise ValueError("Invalid organism-name anchor")
    return "(" + " OR ".join('"' + name + '"' for name in names[:6]) + ")"


def strain_query(names, strains):
    """Every strain fallback, numeric or named, retains the organism anchor."""
    anchor = name_query(names)
    aliases = strain_aliases(strains)[:4]
    if not aliases:
        raise ValueError("No strain aliases available")
    return anchor + " AND (" + " OR ".join('"' + alias + '"' for alias in aliases) + ")"


def verified_sources(packet):
    """Rebuild organism bindings from raw record identities, not old resolved_names.

    An exact source match can add names; a retained candidate cannot. LPSN
    basonym/correct-name IDs are followed only from an already bound record.
    Strain claims require their exact BacDive/culture ID before species-level
    references are considered. These proofs establish targeting scope only.
    """
    edge = packet["edge"]
    endpoints = [edge[side] for side in ("subject", "object")]
    strain_claim = any(v.startswith("kgmicrobe.strain:") for v in endpoints)
    bids = {match for value in endpoints for match in re.findall(r"bacdive_(\d+)", value)}
    cultures = {v.split(":", 1)[1].replace("-", " ").casefold()
                for v in endpoints if v.startswith("kgmicrobe.strain:") and "bacdive_" not in v}
    taxids = {v.split(":", 1)[1] for v in endpoints if v.startswith("NCBITaxon:")}
    lpsn_ids = {v.split(":", 1)[1]: None for v in endpoints if v.startswith("lpsn:")}
    names, proofs = {}, {}
    if not strain_claim:
        for side in ("subject", "object"):
            if edge[side].startswith(("NCBITaxon:", "lpsn:", "GTDB:")):
                for name in normalized_names(edge.get(side + "_label")):
                    names[name] = {"claim_endpoint": edge[side], "field": side + "_label"}
    records = []
    for wrapper in packet["records"]:
        if hashlib.sha256(wrapper["text"].encode()).hexdigest() != wrapper["text_sha256"]:
            raise ValueError("Retained source text hash mismatch")
        records.append(json.loads(wrapper["text"]))

    changed = True
    while changed:
        changed = False
        for index, (wrapper, record) in enumerate(zip(packet["records"], records, strict=True)):
            if index in proofs or not isinstance(record, dict):
                continue
            source = wrapper["source_relative_path"]
            matched, parent, related = None, None, set()
            if source == "bacdive_strains.json":
                general = record.get("General", {})
                classification = record.get("Name and taxonomic classification", {})
                bid = str(general.get("BacDive-ID", ""))
                external = record.get("External links", {})
                external = external if isinstance(external, list) else [external]
                collections = strain_aliases([str(v.get("culture collection no.", ""))
                                             for v in external if isinstance(v, dict)])
                exact = bid in bids or bool(cultures & {v.replace("-", " ").casefold()
                                                      for v in collections})
                taxa = general.get("NCBI tax id", [])
                taxa = taxa if isinstance(taxa, list) else [taxa]
                tids = {str(v.get("NCBI tax id", "")) for v in taxa if isinstance(v, dict)}
                related = normalized_names(classification.get("species"))
                if exact:
                    matched = "exact strain/culture identifier"
                elif not strain_claim and (taxids & tids or set(names) & related):
                    matched = "exact taxon identifier or full taxon name; strain is a search candidate"
                if matched:
                    lpsn = classification.get("LPSN", {})
                    if isinstance(lpsn, dict):
                        related |= normalized_names(lpsn.get("species"))
                        for synonym in lpsn.get("synonyms", []):
                            if isinstance(synonym, dict):
                                related |= normalized_names(synonym.get("synonym"))
            elif source.startswith("lpsn/api_cache/"):
                lid = Path(source).stem
                related = normalized_names(record.get("full_name"))
                if lid in lpsn_ids:
                    parent = lpsn_ids[lid]
                    matched = "exact LPSN endpoint" if parent is None else "explicit LPSN basonym/correct-name ID"
                elif set(names) & related:
                    matched = "exact full organism name"
                if matched:
                    for field in ("basonym_id", "lpsn_correct_name_id"):
                        if record.get(field):
                            lpsn_ids.setdefault(str(record[field]), index)
            elif source == "database.csv":
                lid = "lpsn:" + str(record.get("LPSN_ID", ""))
                if lid in endpoints:
                    matched = "exact MicrobeDecoder LPSN endpoint"
                    related = normalized_names(record.get("org_name"))
            if matched:
                proof = {"occurrence_id": edge["occurrence_id"], "record_index": index,
                         "source_relative_path": source, "locator": wrapper["locator"],
                         "text_sha256": wrapper["text_sha256"], "basis": matched,
                         "parent_record_index": parent}
                proofs[index] = proof
                for name in related:
                    names.setdefault(name, proof)
                changed = True
    return proofs, names
