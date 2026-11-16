"""Replayed, private occurrence packets with exact measurement context (issue #105).

Inputs are retained occurrence/source JSON bytes; output is a bounded presentation
of those bytes. No graph correction, scientific verdict or native admission is inferred.
"""

from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from pathlib import Path

from kg_microbe_curation.identity import CurationError, sha256_json

from .storage.parquet import safe_path

PROFILE = "edgemech-occurrence-packet/v1"
CLAIM_FIELDS = (
    "occurrence_id", "subject", "predicate", "object", "origin_transform",
    "transform_row_number", "relation", "subject_label", "object_label",
    "subject_category", "object_category",
)
CONCENTRATION = "BacDive_Salt_concentration"
UNIT = "BacDive_Salt_concentration_unit"


def _require(condition, message):
    if not condition:
        raise CurationError(message)


def _read_input(descriptor, root):
    _require(isinstance(descriptor, dict) and set(descriptor) == {"path", "sha256"},
             "Packet input requires exactly path and sha256")
    path = descriptor["path"]
    _require(isinstance(path, str) and bool(path), "Packet input path is missing")
    relative = Path(path)
    _require(not relative.is_absolute() and ".." not in relative.parts,
             "Packet inputs must be repository-relative")
    raw = safe_path(Path(root) / relative).read_bytes()
    _require(hashlib.sha256(raw).hexdigest() == descriptor["sha256"],
             "Packet input bytes differ from their pin")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        try:
            return [json.loads(line) for line in raw.splitlines() if line.strip()]
        except json.JSONDecodeError as error:
            raise CurationError("Packet input must be JSON or JSONL") from error


def _occurrence_from(value, occurrence_id):
    if isinstance(value, dict) and "edge" in value:
        candidates = [value["edge"]]
    elif isinstance(value, dict) and "occurrence_id" in value:
        candidates = [value]
    elif isinstance(value, list):
        candidates = value
    else:
        raise CurationError("Occurrence input has an unsupported shape")
    matches = [row for row in candidates
               if isinstance(row, dict) and row.get("occurrence_id") == occurrence_id]
    _require(len(matches) == 1, "Occurrence input must contain one exact selected occurrence")
    return matches[0]


def _source_from(value, occurrence_id):
    if isinstance(value, dict) and "edge" not in value:
        value = value.get(occurrence_id)
    _require(isinstance(value, dict) and isinstance(value.get("edge"), dict),
             "Source input must contain the selected source packet")
    _require(value["edge"].get("occurrence_id") == occurrence_id,
             "Source packet belongs to another occurrence")
    return value


def _is_subset(selected, retained):
    """Allow a pinned public projection to omit private fields, never replace them."""
    if isinstance(selected, dict):
        return isinstance(retained, dict) and all(
            key in retained and _is_subset(value, retained[key])
            for key, value in selected.items()
        )
    if isinstance(selected, list):
        return isinstance(retained, list) and len(selected) == len(retained) and all(
            _is_subset(a, b) for a, b in zip(selected, retained, strict=True)
        )
    return type(selected) is type(retained) and selected == retained


def _records(source):
    records = source.get("records")
    _require(isinstance(records, list), "Source packet requires retained records")
    result = []
    for index, wrapper in enumerate(records):
        _require(isinstance(wrapper, dict) and isinstance(wrapper.get("text"), str),
                 "Retained source record is malformed")
        _require(hashlib.sha256(wrapper["text"].encode()).hexdigest()
                 == wrapper.get("text_sha256"), "Retained source text hash mismatch")
        _require(isinstance(wrapper.get("source_relative_path"), str)
                 and bool(wrapper.get("locator")), "Retained source record lacks a selector")
        try:
            record = json.loads(wrapper["text"])
        except json.JSONDecodeError as error:
            raise CurationError("Retained source text must be JSON") from error
        result.append((index, wrapper, record))
    return result


def _proof(index, wrapper):
    return {"record_index": index, "source_relative_path": wrapper["source_relative_path"],
            "locator": wrapper["locator"], "text_sha256": wrapper["text_sha256"]}


def _measurement(edge, records):
    unresolved = {
        "status": "unresolved", "reason": "No measurement-context adapter for this source field",
        "percent_basis": None, "assay_conditions": None,
        "unknowns": ["Measurement context has not been resolved for this source field"],
    }
    if edge["origin_transform"] != "microbedecoder/edges.tsv":
        return unresolved
    source_row = edge.get("omitted_source_record") or edge.get("curated_source_record")
    if not isinstance(source_row, dict) or source_row.get("source_column") not in {
        CONCENTRATION, UNIT,
    }:
        return unresolved
    for field in ("occurrence_id", "subject", "predicate", "object", "origin_transform"):
        _require(source_row.get(field) == edge[field],
                 "Retained measurement assertion differs from the original occurrence")
    selected = [(i, w, r) for i, w, r in records
                if w["source_relative_path"] == "database.csv"
                and isinstance(r, dict) and edge["subject"] == "lpsn:" + str(r.get("LPSN_ID"))]
    _require(len(selected) == 1, "Measurement requires one exact MicrobeDecoder LPSN record")
    csv_index, csv_wrapper, csv_record = selected[0]
    _require(re.fullmatch(r"CSV data row [1-9][0-9]*", str(csv_wrapper["locator"])) is not None,
             "Measurement CSV row selector is invalid")
    concentration, unit = csv_record.get(CONCENTRATION), csv_record.get(UNIT)
    _require(all(isinstance(v, str) and v.strip() and v != "NA"
                 for v in (concentration, unit)), "Measurement concentration or unit is missing")
    _require(source_row.get("value") == csv_record[source_row["source_column"]],
             "Measurement value differs from the exact original source field")
    bid = str(csv_record.get("BacDive_ID", ""))
    _require(re.fullmatch(r"[1-9][0-9]*", bid) is not None,
             "Measurement lacks an exact BacDive identifier")
    selected = [(i, w, r) for i, w, r in records
                if w["source_relative_path"] == "bacdive_strains.json"
                and isinstance(r, dict)
                and str(r.get("General", {}).get("BacDive-ID")) == bid]
    _require(len(selected) == 1, "Measurement requires one exact BacDive strain record")
    bac_index, bac_wrapper, bacdive = selected[0]
    _require(str(bac_wrapper["locator"]) == bid, "BacDive locator differs from its exact strain ID")
    observations = bacdive.get("Physiology and metabolism", {}).get("halophily", [])
    observations = [observations] if isinstance(observations, dict) else observations
    _require(isinstance(observations, list) and all(isinstance(v, dict) for v in observations),
             "Halophily observations are malformed")
    # Exact source strings only: do not normalize %, infer a percent basis or convert units.
    matches = [o for o in observations if o.get("concentration") == concentration + " " + unit]
    _require(len(matches) == 1, "Measurement requires one exact concentration/unit observation")
    observation = matches[0]
    _require(all(isinstance(observation.get(field), str) and observation[field].strip()
                 for field in ("salt", "tested relation", "growth")),
             "Measurement observation lacks substance, tested relation or growth result")
    ref = str(observation.get("@ref", ""))
    _require(ref not in {"", "None"}, "Measurement observation lacks a reference")
    references = bacdive.get("Reference", [])
    references = [references] if isinstance(references, dict) else references
    _require(isinstance(references, list) and all(isinstance(v, dict) for v in references),
             "BacDive Reference records are malformed")
    matches = [item for item in references if str(item.get("@id", "")) == ref]
    _require(len(matches) == 1, "Measurement requires one exact BacDive Reference record")
    classification = bacdive.get("Name and taxonomic classification", {})
    external = bacdive.get("External links", {})
    external = external if isinstance(external, list) else [external]
    collections = [item["culture collection no."] for item in external
                   if isinstance(item, dict) and item.get("culture collection no.")]
    return {
        "status": "source_bound", "adapter": "microbedecoder-bacdive-salt/v1",
        "substance": observation["salt"], "literal_concentration": concentration,
        "recorded_unit": unit, "tested_relation": observation["tested relation"],
        "growth_result": observation["growth"], "original_observation": observation,
        "percent_basis": None, "assay_conditions": None,
        "unknowns": ["Percentage basis is not specified by this observation",
                     "Assay medium, temperature and duration are not linked to this observation",
                     "An optimum, upper tolerance threshold and every point in the range are not established"],
        "organism_scope": {"assertion_subject": edge["subject"], "bacdive_id": bid,
                           "strain_designation": classification.get("strain designation"),
                           "culture_collection_numbers": collections,
                           "scope": "exact source strain; no species-wide generalization"},
        "reference": matches[0], "reference_id": ref,
        "source_bindings": [_proof(csv_index, csv_wrapper), _proof(bac_index, bac_wrapper)],
        "join_basis": "Exact LPSN endpoint, CSV BacDive_ID, BacDive-ID, literal measurement and @ref",
    }


def _assemble(occurrence, source_packet, occurrence_input, source_input):
    edge = source_packet["edge"]
    _require(all(field in occurrence and field in edge for field in CLAIM_FIELDS),
             "Occurrence is missing required original claim fields")
    _require(_is_subset(occurrence, edge), "Occurrence differs from its retained source assertion")
    records = _records(source_packet)
    endpoints = {}
    for side in ("subject", "object"):
        node = edge.get("original_" + side + "_node")
        _require(isinstance(node, dict) and node.get("id") == edge[side],
                 f"Original {side} node does not bind the endpoint")
        endpoints[side] = {
            "id": edge[side], "category": edge[side + "_category"],
            "label": edge[side + "_label"], "record": node,
            "record_sha256": sha256_json(node),
            "authority_status": "unassessed",
            "authority_note": "Retained catalog snapshot; current identifier/category validity is unassessed",
        }
    result = {
        "profile": PROFILE, "occurrence_id": edge["occurrence_id"],
        "inputs": {"occurrence": occurrence_input, "source": source_input},
        "original_assertion": {field: edge[field] for field in CLAIM_FIELDS},
        "original_occurrence": edge, "endpoints": endpoints,
        "source_records": source_packet["records"],
        "measurement_context": _measurement(edge, records),
        "scientific_status": "unassessed", "native_admission": False,
    }
    return deepcopy(result)


def build_packet(occurrence, source_packet, *, occurrence_input, source_input, root: Path):
    """Construct a private presentation and replay both pinned input files immediately."""
    packet = _assemble(occurrence, source_packet, occurrence_input, source_input)
    validate_packet(packet, root=root)
    return packet


def validate_packet(packet, *, root: Path):
    """Rebuild from retained bytes; self-declared field hashes alone are insufficient."""
    try:
        occurrence_id = packet["occurrence_id"]
        descriptors = packet["inputs"]
        _require(set(descriptors) == {"occurrence", "source"}, "Packet inputs differ")
        occurrence = _occurrence_from(_read_input(descriptors["occurrence"], root), occurrence_id)
        source = _source_from(_read_input(descriptors["source"], root), occurrence_id)
        expected = _assemble(occurrence, source, descriptors["occurrence"], descriptors["source"])
        _require(packet == expected, "Packet presentation differs from replayed retained inputs")
    except (KeyError, TypeError, AttributeError) as error:
        raise CurationError("Occurrence packet is malformed") from error
    return {"occurrence_id": occurrence_id, "inputs_verified": 2,
            "endpoint_records_verified": 2,
            "measurement_status": packet["measurement_context"]["status"]}
