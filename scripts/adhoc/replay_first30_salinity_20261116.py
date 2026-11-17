"""Replay one pinned first-30 owner method for issue #70 round03 preflight, 2026-11-16.

Inputs: read-only canonical KG checkout and retained first-30 packet. Output:
new private evidence directory. This is a method replay, not a graph rebuild or
a scientific rating. No network calls, constructor, or producer writes are used.
Issue #188: new output directories/files are explicitly private under any umask.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import importlib
import io
import json
import os
import subprocess
import sys
from pathlib import Path
from types import CodeType

BASE = "bcfa6bf5bfaa5fca23063fd1483d9fcbcb58a977"
REV = "d6baf5b90003a2032747559d94c00f86a7a4c615"
PRODUCER = "kg_microbe/transform_utils/metatraits/metatraits.py"
CHILD = "kg_microbe/transform_utils/metatraits_gtdb/metatraits_gtdb.py"
RAW = "data/raw/gtdb_species_summary.jsonl.gz"
ONTOLOGY = "data/raw/metpo.json"
EDGES = "data/transformed/metatraits_gtdb/edges.tsv"
FINALIZATION = "data/transformed/metatraits_gtdb/source_finalization.json"
PINS = {
    PRODUCER: "85d6687fa6ac1af3a11203a7f01b9bf3d387c06a23010ab651a89a4fad06cc3e",
    CHILD: "4d15aaba4b793a6e0c63fbe51f035168c765d061f7ae8752ad8e861924d30ca7",
    RAW: "cb2fa59208200105a9473b792c94a45ae41abc24583a37eeaec4c5e4c3d84a63",
    ONTOLOGY: "fbef7ad9b436b28c59d142876eac3d98ffcf1777edab33a67e35fabd841d391a",
    EDGES: "4a99138ab98ac453be014f636f4e2f31eb7d0565e652f60f28c76cfacb26c9ab",
    FINALIZATION: "9b4f5d374f1cdcd38f05e54474563723a3d1828cfc0ca6dc29946c8d3fa8cece",
    "data/transformed/metatraits_gtdb/source_fingerprint.json":
        "7538fd0f2739f1f40146b834ac355c4c848cae114ac8b1f0c06a6a50dd65c6d9",
}
PACKET_PINS = {
    "packet.json": "68ae9cbdb5c02a160c3497977ce191924e9aed8c89321f3da7924770df3ffc82",
    "source.json": "a63d6966a081eacd6b9149ae03c41964aa5f64a4e781abcd88e66a3e654af493",
    "occurrence.json": "a75775ad5e3ebcbf20481a158cb3d81762ff40f95de914fdf5d41a740d4dd4aa",
}
RECORD_SHA = "e837c6090d7b2e748fd8f3ce2cb24bee9acf482c244183b303fe409e5bf44614"
OCCURRENCE = "urn:kg-microbe:occurrence:v1:b912410040f3b6027290e16710d457e3e45753a38d8a5adda78f0a8ea423eb9b"
TAXON = "SYIM01 sp009921765"
SUBJECT = "GTDB:s__SYIM01_sp009921765"
OBJECT = "METPO:1000625"
RAW_LINE = 54895
EDGE_ROW = 2984816
MODULE = "kg_microbe.transform_utils.metatraits.metatraits"
FIELDS = {"salinity minimum": "Median: 0.0 % NaCl (w/v)",
          "salinity growth": "Median: 0.0 % NaCl (w/v)",
          "salinity maximum": "Median: 1.8 % NaCl (w/v)"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def check_file(path, expected):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    require(digest.hexdigest() == expected, f"Pinned file mismatch: {path}")
    return {"path": str(path), "sha256": expected, "bytes": path.stat().st_size}


def create_private_output_dir(path):
    """Create only missing directories, privately; never reuse an output path."""
    require(not path.exists(), "Output must be a fresh directory")
    missing = []
    ancestor = path
    while not ancestor.exists():
        missing.append(ancestor)
        ancestor = ancestor.parent
    require(ancestor.is_dir(), "Output ancestor is not a directory")
    for directory in reversed(missing):
        directory.mkdir(mode=0o700)
        directory.chmod(0o700)


def save_private(path, raw):
    """Create a private file exclusively, then verify its persisted bytes."""
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        os.fchmod(stream.fileno(), 0o600)
        stream.write(raw)
    return check_file(path, sha(raw))


def selected_summaries(record):
    require(record.get("tax_name") == TAXON, "Source taxon identity mismatch")
    selected = [s for s in record["summaries"] if s.get("name") in FIELDS]
    require(len(selected) == len(FIELDS), "Missing or duplicate salinity summary")
    for name, label in FIELDS.items():
        expected = {"name": name, "is_discrete": False, "num_observations": 27,
                    "unique_databases": 1, "majority_label": label, "percentages": {}}
        require(selected.count(expected) == 1, f"Source field, unit or value mismatch: {name}")
    return {s["name"]: s for s in selected}


def verify_record(raw_line, wrapper):
    require(wrapper["text_sha256"] == RECORD_SHA == sha(wrapper["text"].encode()),
            "Retained source record pin mismatch")
    require(wrapper["extractor"] == "source-record-json-canonical/v1", "Unexpected extractor")
    require(wrapper["locator"] == f"JSONL line {RAW_LINE}: {TAXON}", "Source locator mismatch")
    record = json.loads(raw_line)
    require(record == json.loads(wrapper["text"]), "Raw source differs from retained record")
    return record, selected_summaries(record)


def verify_occurrence(packet, source, occurrence, row):
    expected = {"subject": SUBJECT, "predicate": "biolink:has_phenotype", "object": OBJECT,
                "relation": "RO:0002200", "origin_transform": "metatraits_gtdb/edges.tsv",
                "occurrence_id": OCCURRENCE, "transform_row_number": EDGE_ROW}
    for record in (packet["original_assertion"], source["edge"], occurrence):
        require(all(record.get(k) == v for k, v in expected.items()), "Frozen occurrence mismatch")
    require(packet["occurrence_id"] == OCCURRENCE, "Packet occurrence mismatch")
    retained = source["edge"]["curated_source_record"]
    for key, value in row.items():
        require(retained.get(key) == value, f"Retained edge field mismatch: {key}")
    require(row.get("subject") == SUBJECT and row.get("object") == OBJECT, "Edge identity mismatch")
    require(row.get("value") == "1.8" and row.get("unit") == "%NaCl(w/v)", "Edge measurement mismatch")
    require(packet["endpoints"]["subject"]["label"] == TAXON, "Endpoint label mismatch")


def nested_code(code, name):
    found = [c for c in code.co_consts if isinstance(c, CodeType) and c.co_name == name]
    require(len(found) == 1, f"Expected exactly one compiled owner definition: {name}")
    return found[0]


def verify_method(method, path, owner_source):
    """Reject imported aliases/stubs even when their name or module is copied."""
    require(method.__module__ == MODULE, "Method is not from the canonical owner module")
    require(Path(method.__code__.co_filename).resolve() == path.resolve(), "Method source path mismatch")
    compiled = compile(owner_source, str(path), "exec", dont_inherit=True)
    expected = nested_code(nested_code(compiled, "MetaTraitsTransform"), method.__name__)
    require(method.__code__ == expected, "Runtime method differs from pinned owner implementation")
    return {"method": method.__name__, "module": method.__module__,
            "path": str(path), "first_line": method.__code__.co_firstlineno}


def owner_replay(kg, summaries):
    # Import the actual canonical class, but avoid its dataset-loading constructor.
    require(not any(k == "kg_microbe" or k.startswith("kg_microbe.") for k in sys.modules),
            "KG module already imported; use a fresh replay process")
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(kg))
    os.environ["KG_MICROBE_METPO_JSON"] = str(kg / ONTOLOGY)
    module = importlib.import_module(MODULE)
    child = importlib.import_module("kg_microbe.transform_utils.metatraits_gtdb.metatraits_gtdb")
    require(Path(module.__file__).resolve() == kg / PRODUCER, "Wrong canonical producer import")
    require(Path(child.__file__).resolve() == kg / CHILD, "Wrong canonical child import")
    cls = child.MetaTraitsGTDBTransform
    owner_source = (kg / PRODUCER).read_text()
    methods = ("_load_metpo_lookups", "_parse_quantitative_value", "_classify_salinity_phenotypes")
    witnesses = []
    for name in methods:
        method = getattr(cls, name)
        require(method is getattr(module.MetaTraitsTransform, name), "Child overrides expected owner method")
        witnesses.append(verify_method(method, kg / PRODUCER, owner_source))
    require(module._metpo_json_path(kg / "data/raw").resolve() == kg / ONTOLOGY,
            "Owner loader would read a different ontology")
    obj = cls.__new__(cls)
    obj.input_base_dir = kg / "data/raw"
    obj.metpo_label_to_class = {}
    obj.metpo_synonym_to_class = {}
    obj.metpo_pattern_to_predicate = {}
    obj._load_metpo_lookups()
    values = {name: obj._parse_quantitative_value(row["majority_label"])
              for name, row in summaries.items()}
    # Same two arguments as the pinned producer call site; no thresholds here.
    result = obj._classify_salinity_phenotypes(values["salinity minimum"], values["salinity maximum"])
    require(len(result) == 1, "Owner did not produce exactly one phenotype")
    return result[0], values, witnesses, obj.metpo_label_to_class


def verify_ontology(ontology, packet, generated, mapping):
    nodes = [n for n in ontology["graphs"][0]["nodes"]
             if n.get("id") == "https://w3id.org/metpo/1000625"]
    require(len(nodes) == 1, "Ambiguous or missing ontology target")
    node = nodes[0]
    endpoint = packet["endpoints"]["object"]
    require(node["type"] == "CLASS" and node["lbl"] == endpoint["label"] == generated["name"],
            "Ontology class/label mismatch")
    require(node["meta"]["definition"]["val"] == endpoint["record"]["description"],
            "Ontology definition differs from frozen target")
    require(mapping[node["lbl"].lower()]["curie"] == generated["curie"] == endpoint["id"] == OBJECT,
            "Owner ontology mapping mismatch")
    return node


def run(kg, original, output):
    kg, original, output = kg.resolve(), original.resolve(), output.resolve()
    require(not output.exists(), "Output must be a fresh directory")
    require(not output.is_relative_to(kg) and not output.is_relative_to(original),
            "Output must be outside owner and retained evidence directories")
    pins = {p: check_file(kg / p, h) for p, h in PINS.items()}
    packet_pins = {p: check_file(original / p, h) for p, h in PACKET_PINS.items()}
    history = {}
    for revision in (BASE, REV):
        history[revision] = {}
        for path in (PRODUCER, CHILD):
            raw = subprocess.check_output(["git", "-C", str(kg), "show", f"{revision}:{path}"])
            require(sha(raw) == PINS[path], "Historical producer differs from inspected code")
            history[revision][path] = sha(raw)
    packet = json.loads((original / "packet.json").read_text())
    source = json.loads((original / "source.json").read_text())
    occurrence = json.loads((original / "occurrence.json").read_text())
    require(len(source["records"]) == 1, "Expected one retained source record")
    with gzip.open(kg / RAW, "rb") as stream:
        for number, raw_line in enumerate(stream, 1):
            if number == RAW_LINE:
                break
        else:
            raise ValueError("Selected raw source line missing")
    record, summaries = verify_record(raw_line, source["records"][0])
    with (kg / EDGES).open(newline="") as stream:
        header = stream.readline()
        for number, edge_line in enumerate(stream, 1):
            if number == EDGE_ROW:
                break
        else:
            raise ValueError("Selected retained edge missing")
    row = next(csv.DictReader(io.StringIO(header + edge_line), delimiter="\t", quoting=csv.QUOTE_NONE))
    verify_occurrence(packet, source, occurrence, row)
    finalization = json.loads((kg / FINALIZATION).read_text())
    member = finalization["members"]["edges.tsv"]
    require(member == {"bytes": pins[EDGES]["bytes"], "sha256": pins[EDGES]["sha256"]},
            "Finalization does not bind the inspected retained edge file")
    generated, values, methods, mapping = owner_replay(kg, summaries)
    for key, row_key in (("curie", "object"), ("predicate", "predicate"), ("value", "value"), ("unit", "unit")):
        require(str(generated[key]) == row[row_key], f"Owner result differs from stored edge: {key}")
    ontology_node = verify_ontology(json.loads((kg / ONTOLOGY).read_text()), packet, generated, mapping)
    # Verify all read-only inputs again before persisting successful evidence.
    for path, expected in PINS.items():
        check_file(kg / path, expected)
    create_private_output_dir(output)
    artifact_pins = {}

    def save(name, raw):
        path = output / name
        artifact_pins[name] = save_private(path, raw)

    def save_json(name, value):
        save(name, (json.dumps(value, indent=2, sort_keys=True) + "\n").encode())

    save("source-record-54895.json", raw_line)
    save("retained-edge-2984816.tsv", (header + edge_line).encode())
    save_json("metpo-target-node.json", ontology_node)
    save_json("source-finalization-member.json", member)
    save("owner-metatraits.py", (kg / PRODUCER).read_bytes())
    save("owner-metatraits-gtdb.py", (kg / CHILD).read_bytes())
    result = {"schema": "edgemech.first30-owner-method-replay/v1", "case": "first-30",
              "occurrence_id": OCCURRENCE, "input_pins": pins, "packet_pins": packet_pins,
              "producer_history": history, "runtime": {"python": sys.version, "executable": sys.executable},
              "helper_sha256": sha(Path(__file__).read_bytes()), "methods": methods,
              "raw_line": RAW_LINE, "transform_data_row": EDGE_ROW, "transform_physical_line": EDGE_ROW + 1,
              "retained_source_record_sha256": RECORD_SHA, "source_tax_name": record["tax_name"],
              "summaries": summaries, "parsed_values": values, "actual_method_output": generated,
              "ontology_mapping": mapping[ontology_node["lbl"].lower()], "artifact_pins": dict(artifact_pins),
              "limits": ["Only lookup, numeric parser and salinity classifier methods executed; constructor, taxonomy resolution, writers and full transform/build not executed.",
                         "Current raw/source/edge/finalization and two clean Git baselines agree on the bounded witnesses; original bcfa6bf5b-dirty build provenance is not proved.",
                         "The retained source taxon name matches the frozen endpoint label; independent taxonomic identity and underlying experimental observations are not established.",
                         "No biological, literature, source-fidelity, relation or node verdict is assigned. Independent semantic assessment is required before any fresh scoring package."]}
    save_json("replay.json", result)
    return artifact_pins["replay.json"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kg", type=Path, required=True)
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.kg, args.original, args.output), sort_keys=True))


if __name__ == "__main__":
    main()
