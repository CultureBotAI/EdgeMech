"""Bounded first43/first28 owner replay; mechanical evidence, never a scientific verdict.

Plan checks are read-only apart from exclusive private artifacts. Replay uses the
actual owner loader and emission method, without the dataset-loading constructor.
Only these two frozen occurrences are admitted. No provider requests are used.
"""
from __future__ import annotations

import argparse
import ast
import builtins
import contextlib
import csv
import gzip
import hashlib
import importlib
import importlib.util
import io
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from types import CodeType
from unittest.mock import patch

BASE = "bcfa6bf5bfaa5fca23063fd1483d9fcbcb58a977"
REV = "d6baf5b90003a2032747559d94c00f86a7a4c615"
PRODUCER = "kg_microbe/transform_utils/metatraits/metatraits.py"
LOADER = "kg_microbe/utils/mapping_file_utils.py"
RAW = "data/raw/ncbi_species_summary.jsonl.gz"
ONTOLOGY = "data/raw/metpo.json"
EDGES = "data/transformed/metatraits/edges.tsv"
FINALIZATION = "data/transformed/metatraits/source_finalization.json"
CODE = (PRODUCER, LOADER, "kg_microbe/transform_utils/metatraits/io.py",
        "kg_microbe/utils/metpo_predicates.py", "kg_microbe/utils/tsv_io.py",
        "kg_microbe/utils/graph_canonicalization.py", "kg_microbe/transform_utils/constants.py",
        "kg_microbe/transform_utils/transform.py")
INPUTS = (RAW, ONTOLOGY, "data/raw/metpo_sheet.tsv", "data/raw/metpo-properties.tsv",
          "mappings/canonical/metpo_alias_mappings.tsv",
          "kg_microbe/transform_utils/custom_curies.yaml", EDGES, FINALIZATION,
          "data/transformed/metatraits/source_fingerprint.json")
OCCURRENCE = "urn:kg-microbe:occurrence:v1:2cad956c7d5d6ace49ddb7e887de8eab4a7c1b78410942732e2a44bbd1a00559"
SUBJECT = "NCBITaxon:1540872"
OBJECT = "METPO:1005039"
TAXON = "Candidatus Gracilibacteria bacterium HOT-871"
TRAIT = "nitrogen fixation"
RAW_LINE = 10486
EDGE_ROW = 820840
RECORD_SHA = "899d048ab49589171e5a2718d5b308f793544eddf0a88d9463c9f2f8160ba83e"
MODULE = "kg_microbe.transform_utils.metatraits.metatraits"
PACKET_PINS = {
    "packet.json": "70decffa3ed755ad913171964494b4edfcf84b2341a34a76a925837f1565befc",
    "occurrence.json": "693719992316abf9c8b64915f7ce67e45bf1ac45b8d2cdb167eef4c9f29acbeb",
    "source.json": "387def480444da8fb12044aa3a61ce4289e28376d263d45da5238771d510de40",
}
INPUT_PINS = {
    RAW: "1881360fb0ae1f28bdbd7d307ed0f7815044b0aa8ad0d769e0ee68f64d431ce7",
    ONTOLOGY: "fbef7ad9b436b28c59d142876eac3d98ffcf1777edab33a67e35fabd841d391a",
    EDGES: "2fa49eeb5b71abaf1f8732ddf320debdfe5924947e8a73e294b4ccd1931ad666",
    FINALIZATION: "34b15913947b912eb99207d13c80c7e836168ba54423a52a2bfaa286b690d2ea",
    "data/transformed/metatraits/source_fingerprint.json":
        "8a0773a90751681f52033f2ee237925fbf445ae0a53274638b383d843a8ad74b",
    "data/raw/metpo_sheet.tsv": "ec9700569bf5e83d39fe4c29f525c06d3c396adfad2ce0bf33072b8b1a1b1409",
    "data/raw/metpo-properties.tsv": "8ef8929f3f8d3ed61ba41f062548a3d4d2e058932c522b7ddb3a01d1e06cef63",
    "mappings/canonical/metpo_alias_mappings.tsv":
        "15c4aa67644fd0aac233dbc909cda0b8bbfcbc50bb998fc8bf3e06a7b19ace06",
    "kg_microbe/transform_utils/custom_curies.yaml":
        "5b201563b8042eb51a6984f56354be2b3420deae0d029ce707c961ec6eeab784",
}
GTDB_PRODUCER = "kg_microbe/transform_utils/metatraits_gtdb/metatraits_gtdb.py"
CASES = {
    "first43": {
        "occurrence": OCCURRENCE, "subject": SUBJECT, "object": OBJECT,
        "taxon": TAXON, "trait": TRAIT, "raw_line": RAW_LINE, "edge_row": EDGE_ROW,
        "record_sha": RECORD_SHA, "packet_pins": PACKET_PINS,
        "raw": RAW, "edges": EDGES, "finalization": FINALIZATION,
        "input_pins": INPUT_PINS, "code": CODE,
        "producer": PRODUCER, "module": MODULE, "class": "MetaTraitsTransform",
        "origin": "metatraits/edges.tsv", "predicate": "biolink:capable_of",
        "relation": "RO:0002215", "knowledge_source": "infores:metatraits",
        "summary_index": 124,
        "summary": {"name": TRAIT, "is_discrete": True, "majority_label": "false: (100%)",
                    "num_observations": 10, "unique_databases": 2,
                    "percentages": {"false": 100.0}},
    },
    "first28": {
        "occurrence": "urn:kg-microbe:occurrence:v1:177815c9e4c39684189e2004e17840e6f0c42a2824750aad5d7f95bd7c0e5f3e",
        "subject": "NCBITaxon:113559", "object": "METPO:1000870",
        "taxon": "Actinoplanes campanulatus", "trait": "sporulation",
        "raw_line": 1498, "edge_row": 96074, "summary_index": 58,
        "record_sha": "0bf0d3cf44cf54982b9f88ea25666a02d5bec3fc86209911e79c9761ba46a896",
        "packet_pins": {
            "packet.json": "eb5e38bf636fed915f15ee9bd2ce9f1d4d010eb8c1e8d815a17e1de265bcd527",
            "source.json": "a11495091472648e39d2b4a7b1190676cbefbf5a95791784910617c90c38522d",
            "occurrence.json": "0f48424854ed44e039e0ebe0a53768bcd78a63a583c732d0295f176c4e57f186",
        },
        "raw": "data/raw/gtdb_species_summary.jsonl.gz",
        "edges": "data/transformed/metatraits_gtdb/edges.tsv",
        "finalization": "data/transformed/metatraits_gtdb/source_finalization.json",
        "input_pins": {
            **{path: digest for path, digest in INPUT_PINS.items()
               if path != RAW and not path.startswith("data/transformed/metatraits/")},
            "data/raw/gtdb_species_summary.jsonl.gz":
                "cb2fa59208200105a9473b792c94a45ae41abc24583a37eeaec4c5e4c3d84a63",
            "data/transformed/metatraits_gtdb/edges.tsv":
                "4a99138ab98ac453be014f636f4e2f31eb7d0565e652f60f28c76cfacb26c9ab",
            "data/transformed/metatraits_gtdb/source_finalization.json":
                "9b4f5d374f1cdcd38f05e54474563723a3d1828cfc0ca6dc29946c8d3fa8cece",
            "data/transformed/metatraits_gtdb/source_fingerprint.json":
                "7538fd0f2739f1f40146b834ac355c4c848cae114ac8b1f0c06a6a50dd65c6d9",
        },
        "code": CODE + (GTDB_PRODUCER,), "producer": GTDB_PRODUCER,
        "module": "kg_microbe.transform_utils.metatraits_gtdb.metatraits_gtdb",
        "class": "MetaTraitsGTDBTransform", "origin": "metatraits_gtdb/edges.tsv",
        "predicate": "biolink:has_phenotype", "relation": "RO:0002200",
        "knowledge_source": "infores:gtdb-metatraits",
        "summary": {"name": "sporulation", "is_discrete": True,
                    "majority_label": "true: (100%)", "num_observations": 3,
                    "unique_databases": 2, "percentages": {"true": 100.0}},
    },
}
LIMITS = [
    "Mechanical source/lookup/emission evidence only; no scientific labels or new coverage.",
    "Unknown historical dirty state remains unknown; agreement with two clean bases is not a historical execution trace.",
    "Current retained templates are hash-bound at declared METPO version 2026-06-12; their presence at the sampled dirty execution is not independently proved.",
    "Exactly one unchanged summary is projected from the full original source record; other summaries are retained but not replayed.",
    "Taxon cache is seeded from the frozen subject/label; independent taxonomy resolution and source-cell biological identity are not tested.",
    "Chemical node enrichment is disabled; it does not supply the emitted edge. Constructor, finalizer, deduplication and full transform are not run.",
    "A negative source aggregate is not independent biological refutation, and replaying source choice does not prove biological truth.",
    "The original source field definition is unresolved. Generic sporulation does not establish biological spore type; the selected target definition is not a source-field definition.",
    "For first28 the actual GTDB subclass inherits the emission method; its GTDB-to-NCBI lookup is seeded solely from the frozen subject, with a synthetic singleton weight of one, not recovered genome-count evidence.",
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def pin(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    info = path.stat()
    return {"sha256": digest.hexdigest(), "bytes": info.st_size,
            "mtime_ns": info.st_mtime_ns, "mode": oct(stat.S_IMODE(info.st_mode))}


def create_private_dir(path):
    require(not path.exists() and not path.is_symlink(), "Output must be a fresh directory")
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
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        os.fchmod(stream.fileno(), 0o600)
        stream.write(raw)
    result = pin(path)
    require(result["sha256"] == sha(raw), "Persisted output differs")
    return result


def save_json(path, value):
    return save_private(path, (json.dumps(value, indent=2, sort_keys=True) + "\n").encode())


def git_bytes(kg, revision, path):
    return subprocess.check_output(["git", "-C", str(kg), "show", f"{revision}:{path}"])


def retained_case(name):
    require(name in CASES, "Only first43 and first28 are admitted")
    return CASES[name]


def selected_summary(record, case_name="first43"):
    case = retained_case(case_name)
    require(record.get("tax_name") == case["taxon"], "Wrong source taxon")
    found = [(i, item) for i, item in enumerate(record["summaries"])
             if item.get("name") == case["trait"]]
    require(len(found) == 1, "Missing or duplicate selected summary")
    index, summary = found[0]
    require(summary == case["summary"], "Changed source summary")
    return index, summary


def read_selected_line(path, number):
    with path.open("rb") as stream:
        compressed = stream.read(2) == b"\x1f\x8b"
    opener = gzip.open if compressed else open
    with opener(path, "rb") as stream:
        for index, raw in enumerate(stream, 1):
            if index == number:
                return raw
    raise ValueError("Missing source line")


def inspect_inputs(kg, original, case_name="first43"):
    case = retained_case(case_name)
    packet_pins = {p: pin(original / p) for p in ("packet.json", "source.json", "occurrence.json")}
    for path, expected in case["packet_pins"].items():
        require(packet_pins[path]["sha256"] == expected, f"Frozen packet mismatch: {path}")
    packet = json.loads((original / "packet.json").read_text())
    source = json.loads((original / "source.json").read_text())
    occurrence = json.loads((original / "occurrence.json").read_text())
    expected = {"occurrence_id": case["occurrence"], "subject": case["subject"],
                "object": case["object"], "predicate": case["predicate"],
                "relation": case["relation"], "origin_transform": case["origin"],
                "transform_row_number": case["edge_row"]}
    for record in (packet["original_assertion"], occurrence, source["edge"]):
        require(all(record.get(k) == v for k, v in expected.items()), "Frozen occurrence mismatch")
    require(packet["occurrence_id"] == case["occurrence"], "Packet identity mismatch")
    require(len(source["records"]) == 1, "Expected exactly one retained source record")
    wrapper = source["records"][0]
    require(wrapper["text_sha256"] == case["record_sha"] == sha(wrapper["text"].encode()),
            "Retained source record pin mismatch")
    require(wrapper["locator"] == f"JSONL line {case['raw_line']}: {case['taxon']}",
            "Wrong source locator")
    require(Path(wrapper["source_path"]).resolve() == kg / case["raw"], "Wrong source path")
    require(wrapper["extractor"] == "source-record-json-canonical/v1", "Wrong extractor")
    raw = read_selected_line(kg / case["raw"], case["raw_line"])
    record = json.loads(raw)
    require(record == json.loads(wrapper["text"]), "Owner source differs from frozen source")
    index, summary = selected_summary(record, case_name)
    require(index == case["summary_index"], "Wrong frozen summary ordinal")
    with (kg / case["edges"]).open("rb") as stream:
        header = stream.readline()
        for number, row in enumerate(stream, 1):
            if number == case["edge_row"]:
                break
        else:
            raise ValueError("Missing original transformed row")
    parsed = next(csv.DictReader(io.StringIO((header + row).decode()), delimiter="\t"))
    # first28 was retained, so its packet has no omitted_source_record. The
    # original row comes directly from the hash-pinned original transform;
    # curated extras and inherited assessments are never comparison authority.
    frozen = source["edge"]["omitted_source_record"]
    if frozen is not None:
        require(all(parsed[key] == frozen[key] for key in parsed if key in frozen),
                "Original edge differs from omitted source record")
    for key in ("subject", "predicate", "object", "relation"):
        require(parsed[key] == expected[key], f"Original edge mismatch: {key}")
    require(parsed["primary_knowledge_source"] == case["knowledge_source"],
            "Original knowledge source mismatch")
    require(parsed["knowledge_level"] == occurrence["knowledge_level"], "Knowledge level mismatch")
    require(parsed["agent_type"] == occurrence["agent_type"], "Agent type mismatch")
    pins = {p: pin(kg / p) for p in case["code"] + tuple(case["input_pins"])}
    for path, expected_hash in case["input_pins"].items():
        require(pins[path]["sha256"] == expected_hash, f"Pinned input mismatch: {path}")
    history = {revision: {p: sha(git_bytes(kg, revision, p)) for p in case["code"]}
               for revision in (BASE, REV)}
    for path in case["code"]:
        require(pins[path]["sha256"] == history[BASE][path] == history[REV][path],
                f"Owner code differs from clean baselines: {path}")
    finalization = json.loads((kg / case["finalization"]).read_text())
    require(finalization["members"]["edges.tsv"] ==
            {key: pins[case["edges"]][key] for key in ("sha256", "bytes")},
            "Retained edge finalization mismatch")
    return {"packet_pins": packet_pins, "owner_pins": pins, "history": history,
            "case": case_name, "occurrence_id": case["occurrence"],
            "original_assertion": packet["original_assertion"],
            "selected_summary_index_zero_based": index, "summary": summary,
            "raw_line_sha256": sha(raw), "retained_canonical_source_sha256": case["record_sha"],
            "original_edge": parsed, "original_edge_raw_sha256": sha(header + row),
            "source_line": case["raw_line"], "transform_data_row": case["edge_row"],
            "transform_physical_line": case["edge_row"] + 1,
            "source_selector": f"/summaries/{index}", "summary_sha256": sha(json_bytes(summary)),
            "finalization_edge_member": finalization["members"]["edges.tsv"],
            "runtime": {"executable": sys.executable, "version": sys.version,
                        "available_modules": {name: importlib.util.find_spec(name) is not None
                                              for name in ("pandas", "oaklib", "yaml", "tqdm")}}}


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def code_tree(code):
    yield code
    for value in code.co_consts:
        if isinstance(value, CodeType):
            yield from code_tree(value)


def verify_callable(function, path, source):
    require(Path(function.__code__.co_filename).resolve() == path.resolve(),
            "Runtime owner source path mismatch")
    require(function.__code__ in set(code_tree(compile(source, str(path), "exec",
                                                     dont_inherit=True))),
            "Runtime code differs from pinned owner")


def headers_from_owner(kg, constants, case_name="first43"):
    """Evaluate only the actual header expressions, never either constructor."""
    case = retained_case(case_name)
    headers = {}
    base_tree = ast.parse((kg / "kg_microbe/transform_utils/transform.py").read_text())
    producer_tree = ast.parse((kg / case["producer"]).read_text())
    for tree, class_name in ((base_tree, "Transform"), (producer_tree, case["class"])):
        classes = [node for node in tree.body if isinstance(node, ast.ClassDef)
                   and node.name == class_name]
        require(len(classes) == 1, "Ambiguous owner class")
        constructors = [node for node in classes[0].body if isinstance(node, ast.FunctionDef)
                        and node.name == "__init__"]
        require(len(constructors) == 1, "Ambiguous owner constructor")
        assignments = [node for node in ast.walk(constructors[0]) if isinstance(node, ast.Assign)
                       and len(node.targets) == 1 and isinstance(node.targets[0], ast.Attribute)
                       and node.targets[0].attr in ("node_header", "edge_header")]
        require(len(assignments) == (2 if tree is base_tree else 1), "Ambiguous owner headers")
        for node in assignments:
            value = node.value
            name = node.targets[0].attr
            if isinstance(value, ast.BinOp) and isinstance(value.op, ast.Add):
                require(isinstance(value.left, ast.Attribute) and value.left.attr == name,
                        "Unexpected header extension")
                value = value.right
                prefix = headers[name]
            else:
                prefix = []
            require(isinstance(value, ast.List), "Unexpected header expression")
            require(all(isinstance(item, (ast.Name, ast.Constant)) for item in value.elts),
                    "Unexpected header item")
            headers[name] = prefix + [getattr(constants, item.id) if isinstance(item, ast.Name)
                                      else item.value for item in value.elts]
    return headers


def owner_knowledge_source(kg, case_name):
    """Read the actual constructor's literal configuration without executing it."""
    case = retained_case(case_name)
    tree = ast.parse((kg / case["producer"]).read_text())
    values = [assignment.value for node in tree.body
              if isinstance(node, ast.ClassDef) and node.name == case["class"]
              for method in node.body
              if isinstance(method, ast.FunctionDef) and method.name == "__init__"
              for assignment in ast.walk(method) if isinstance(assignment, ast.Assign)
              for target in assignment.targets
              if isinstance(target, ast.Attribute) and target.attr == "knowledge_source"]
    require(len(values) == 1 and isinstance(values[0], ast.Constant),
            "Ambiguous owner knowledge source")
    require(values[0].value == case["knowledge_source"], "Owner knowledge source changed")
    return values[0].value


@contextlib.contextmanager
def private_owner_io(output):
    """Only adapt I/O: exclusive private creation, no network/processes/credential reads.

    Owner loader, mapping, polarity, row construction and TSV serialization remain
    unchanged. The audit hook is active only during this context.
    """
    active = True
    read_paths = set()
    original_open = builtins.open

    def audit(event, args):
        if not active:
            return
        if event in ("socket.connect", "socket.getaddrinfo", "subprocess.Popen", "os.system"):
            raise ValueError(f"Owner operation prohibited: {event}")
        if event == "open" and not isinstance(args[0], int):
            path = Path(args[0]).resolve()
            require(not any(part in (".aws", ".ssh", ".netrc", ".env", "credentials")
                            for part in path.parts), "Credential access prohibited")
            flags = args[2]
            if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
                require(path.is_relative_to(output) and flags & os.O_EXCL,
                        "Owner writes must be exclusive and inside private output")
            else:
                read_paths.add(str(path))
        if event in ("os.remove", "os.rename", "os.rmdir"):
            raise ValueError(f"Owner destructive operation prohibited: {event}")
        if event == "os.mkdir":
            require(Path(args[0]).resolve().is_relative_to(output), "Owner mkdir outside output")

    def exclusive_open(file, mode="r", *args, **kwargs):
        if any(character in mode for character in "wax+"):
            require(mode in ("w", "wb", "wt", "x", "xb", "xt"), "Unsafe owner write mode")
            require(Path(file).resolve().is_relative_to(output), "Owner write outside output")
            mode = mode.replace("w", "x")
            stream = original_open(file, mode, *args, **kwargs)
            os.fchmod(stream.fileno(), 0o600)
            return stream
        return original_open(file, mode, *args, **kwargs)

    def path_open(path, mode="r", buffering=-1, encoding=None, errors=None, newline=None):
        # Python 3.10's Path accessor retains its original io.open reference.
        return exclusive_open(path, mode, buffering=buffering, encoding=encoding,
                              errors=errors, newline=newline)

    sys.addaudithook(audit)
    old_umask = os.umask(0o077)
    try:
        with (patch("builtins.open", exclusive_open), patch("io.open", exclusive_open),
              patch("pathlib.Path.open", path_open)):
            yield read_paths
    finally:
        active = False
        os.umask(old_umask)


def prepare_owner(kg, case_name="first43"):
    case = retained_case(case_name)
    require(not any(name == "kg_microbe" or name.startswith("kg_microbe.")
                    for name in sys.modules), "Use a fresh process for the canonical owner import")
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(kg))
    os.environ["KG_MICROBE_METPO_JSON"] = str(kg / ONTOLOGY)
    os.environ["KG_MICROBE_METPO_TEMPLATE_DIR"] = str(kg / "data/raw")
    module = importlib.import_module(MODULE)
    selected_module = importlib.import_module(case["module"])
    loader = importlib.import_module("kg_microbe.utils.mapping_file_utils")
    constants = importlib.import_module("kg_microbe.transform_utils.constants")
    require(Path(module.__file__).resolve() == kg / PRODUCER, "Wrong owner module")
    require(Path(selected_module.__file__).resolve() == kg / case["producer"],
            "Wrong selected owner module")
    require(Path(loader.__file__).resolve() == kg / LOADER, "Wrong loader module")
    verify_callable(loader.load_metpo_mappings, kg / LOADER, (kg / LOADER).read_text())
    cls = getattr(selected_module, case["class"])
    for method in ("_build_trait_mapping", "_load_metpo_lookups", "_process_single_file"):
        verify_callable(getattr(cls, method), kg / PRODUCER, (kg / PRODUCER).read_text())
    verify_callable(cls._search_ncbitaxon_by_label, kg / case["producer"],
                    (kg / case["producer"]).read_text())
    require(module.CUSTOM_CURIES_YAML_FILE.resolve() ==
            kg / "kg_microbe/transform_utils/custom_curies.yaml", "Wrong custom mapping file")
    require(loader.LOCAL_METPO_ALIAS_OVERRIDES_PATH.resolve() ==
            kg / "mappings/canonical/metpo_alias_mappings.tsv", "Wrong alias mapping file")
    obj = cls.__new__(cls)
    obj.input_base_dir = kg / "data/raw"
    require(module._metpo_json_path(obj.input_base_dir).resolve() == kg / ONTOLOGY,
            "Wrong ontology path")
    obj.metpo_mappings = loader.load_metpo_mappings("metatraits synonym")
    obj.trait_mapping = {}
    obj._build_trait_mapping()
    obj.metpo_label_to_class = {}
    obj.metpo_synonym_to_class = {}
    obj.metpo_pattern_to_predicate = {}
    obj._load_metpo_lookups()
    require(case["trait"] in obj.trait_mapping, "Owner did not load the selected trait")
    require(obj.trait_mapping[case["trait"]]["curie"] == case["object"],
            "Owner selected a different object")
    # Explicitly conditioned on the original subject: no independent identity claim.
    obj.ncbitaxon_name_to_id = {case["taxon"].lower(): case["subject"]}
    condition = {"ncbitaxon_name_to_id": obj.ncbitaxon_name_to_id}
    if case_name == "first28":
        obj.ncbitaxon_name_to_id = {}
        obj.gtdb_to_ncbi = {case["taxon"]: {case["subject"]: 1}}
        obj.gtdb_preferred_ncbi = {}
        condition = {"gtdb_to_ncbi": obj.gtdb_to_ncbi,
                     "gtdb_preferred_ncbi": obj.gtdb_preferred_ncbi,
                     "singleton_weight_is_synthetic_not_genome_evidence": True}
    obj.chemical_loader = None
    obj.knowledge_source = owner_knowledge_source(kg, case_name)
    for name, value in headers_from_owner(kg, constants, case_name).items():
        setattr(obj, name, value)
    return obj, {"loader_entry": obj.metpo_mappings[case["trait"]],
                 "selected_lookup_entry": obj.trait_mapping[case["trait"]],
                 "owner_class": case["module"] + "." + case["class"],
                 "knowledge_source_from_owner_constructor": obj.knowledge_source,
                 "metpo_declared_version": constants.METPO_VERSION,
                 "template_urls": [constants.METPO_CLASSES_ROBOT_TEMPLATE_URL,
                                   constants.METPO_PROPERTIES_ROBOT_TEMPLATE_URL],
                 "edge_header": obj.edge_header, "node_header": obj.node_header,
                 "taxon_cache_condition": condition}


def read_rows(path):
    with path.open(newline="") as stream:
        rows = list(csv.reader(stream, delimiter="\t"))
    require(bool(rows), "Empty TSV output")
    header = rows[0]
    require(len(header) == len(set(header)), "Duplicate output columns")
    require(all(len(row) <= len(header) for row in rows[1:]), "Unexpected extra output fields")
    return header, rows[1:], [dict(zip(header, row + [""] * (len(header) - len(row))))
                             for row in rows[1:]]


def compare_edge(emitted, frozen):
    differences = {key: {"emitted": emitted.get(key, ""), "frozen": frozen.get(key, "")}
                   for key in set(emitted) | set(frozen)
                   if emitted.get(key, "") != frozen.get(key, "")}
    require(not differences, f"Emitted edge differs from frozen original: {differences}")
    return {"all_field_values_match_with_absent_fields_empty": True,
            "original_columns_absent_from_owner_header": sorted(set(frozen) - set(emitted)),
            "emitted": emitted, "frozen_original": frozen}


def emission_trace(kg, case_name="first43"):
    case = retained_case(case_name)
    compiled = {str(kg / path): set(code_tree(compile((kg / path).read_text(), str(kg / path),
                                                   "exec", dont_inherit=True)))
                for path in case["code"]}
    calls, lines, rows = [], {}, []

    def trace(frame, event, arg):
        path = frame.f_code.co_filename
        if path not in compiled:
            return None
        name = frame.f_code.co_name
        if event == "call":
            require(frame.f_code in compiled[path], "Executed owner code differs from pin")
            require(name not in ("_apply_majority_label_to_predicate", "_reviewed_manual_mapping",
                                 "_get_ncbitaxon_impl", "_search_ncbitaxon_label"),
                    f"Unexpected fallback outside bounded Tier1 replay: {name}")
            calls.append({"path": str(Path(path).relative_to(kg)), "function": name,
                          "first_line": frame.f_code.co_firstlineno})
            if name == "write_row":
                rows.append(list(frame.f_locals["row"]))
        if event == "line":
            lines.setdefault(str(Path(path).relative_to(kg)), set()).add(frame.f_lineno)
        return trace

    return trace, calls, lines, rows


def persist_inputs(kg, original, output, inspection, case_name="first43"):
    case = retained_case(case_name)
    for name in case["packet_pins"]:
        save_private(output / ("frozen-" + name), (original / name).read_bytes())
    raw = read_selected_line(kg / case["raw"], case["raw_line"])
    save_private(output / f"original-source-line-{case['raw_line']}.jsonl", raw)
    record = json.loads(raw)
    index, summary = selected_summary(record, case_name)
    require(index == inspection["selected_summary_index_zero_based"], "Source selector changed")
    projected = {**record, "summaries": [summary]}
    save_private(output / "bounded-input.jsonl",
                 (json.dumps(projected, separators=(",", ":")) + "\n").encode())
    save_json(output / "selected-summary.json", summary)
    # Preserve the complete, exact small inputs and implementation files privately.
    for path in case["code"] + tuple(case["input_pins"]):
        if path in (case["raw"], case["edges"]):
            continue
        save_private(output / path.replace("/", "__"), (kg / path).read_bytes())
    with (kg / case["edges"]).open("rb") as stream:
        header = stream.readline()
        for number, row in enumerate(stream, 1):
            if number == case["edge_row"]:
                break
    save_private(output / f"original-edge-{case['edge_row']}.tsv", header + row)
    ontology = json.loads((kg / ONTOLOGY).read_text())
    nodes = [node for node in ontology["graphs"][0]["nodes"]
             if node.get("id") == "https://w3id.org/metpo/" + case["object"].split(":")[1]]
    require(len(nodes) == 1, "Missing or duplicate ontology target")
    packet = json.loads((original / "packet.json").read_text())
    endpoint = packet["endpoints"]["object"]
    require(nodes[0]["lbl"] == endpoint["label"] and
            nodes[0]["meta"]["definition"]["val"] == endpoint["record"]["description"],
            "Ontology differs from frozen target definition")
    save_json(output / "ontology-target.json", nodes[0])


def verify_artifacts(directory, case_name="first43"):
    """Separate process readback: hashes, every emitted row, selector and comparison."""
    case = retained_case(case_name)
    receipt = json.loads((directory / "receipt.json").read_text())
    require(receipt["status"] == "replayed" and receipt["occurrence_id"] == case["occurrence"]
            and receipt.get("case", "first43") == case_name, "Not a successful selected case receipt")
    for name, expected in receipt["artifact_pins"].items():
        path = directory / name
        require(path.resolve().is_relative_to(directory.resolve()), "Artifact escapes directory")
        actual = pin(path)
        require(actual == expected and actual["mode"] == "0o600", f"Artifact changed: {name}")
    for path in (directory, directory / "owner-output"):
        require(stat.S_IMODE(path.stat().st_mode) == 0o700, "Output directory is not private")
    record = json.loads((directory / f"original-source-line-{case['raw_line']}.jsonl").read_bytes())
    index, summary = selected_summary(record, case_name)
    projected = json.loads((directory / "bounded-input.jsonl").read_bytes())
    require(projected == {**record, "summaries": [summary]}, "Bounded source projection changed")
    require(index == receipt["selected_summary_index_zero_based"], "Selector changed")
    header, raw_rows, rows = read_rows(directory / "owner-output/bounded-input_edges.tsv")
    require(len(rows) == 1, "Expected exactly one emitted edge occurrence")
    require(header == receipt["owner_mapping"]["edge_header"], "Emitted header changed")
    require(raw_rows == receipt["emitted_raw_rows"], "Emitted raw rows differ from receipt")
    frozen = read_rows(directory / f"original-edge-{case['edge_row']}.tsv")[2]
    require(len(frozen) == 1 and frozen[0] == receipt["original_edge"], "Frozen edge changed")
    comparison = compare_edge(rows[0], frozen[0])
    require(comparison == receipt["comparison"], "Comparison differs from receipt")
    for name, expected in receipt["emitted_line_hashes"].items():
        actual = [sha(line) for line in (directory / name).read_bytes().splitlines(keepends=True)]
        require(actual == expected, f"Emitted line hashes differ: {name}")
    return {"case": case_name, "occurrence_id": case["occurrence"],
            "receipt_sha256": pin(directory / "receipt.json")["sha256"],
            "artifact_count": len(receipt["artifact_pins"]), "emitted_edge_rows": len(rows),
            "all_artifact_hashes_and_emitted_rows_reread": True, "comparison": comparison}


def runtime_identity():
    """Bind the retained virtualenv before/after use without loading credentials."""
    prefix = Path(sys.prefix)
    require(sys.prefix != sys.base_prefix, "Use the retained virtualenv")
    paths = sorted(path for path in prefix.rglob("*") if path.is_file())
    excluded = {path for path in paths
                if any(part in (".aws", ".ssh", ".netrc", ".env", "credentials")
                       for part in path.relative_to(prefix).parts)}
    # Some installed libraries have credential-named package directories. Do not
    # open any of those paths, even for hashing; explicitly bound this inventory.
    return {"prefix": str(prefix), "executable": sys.executable, "version": sys.version,
            "resolved_executable": str(Path(sys.executable).resolve()),
            "executable_pin": pin(Path(sys.executable)),
            "excluded_paths_not_read": sorted(str(path.relative_to(prefix)) for path in excluded),
            "files": {str(path.relative_to(prefix)): {**pin(path),
                      "symlink_target": os.readlink(path) if path.is_symlink() else None}
                      for path in paths if path not in excluded}}


def run(mode, kg, original, output, case_name="first43"):
    case = retained_case(case_name)
    require(not output.resolve().is_relative_to(kg) and
            not output.resolve().is_relative_to(original), "Output inside read-only evidence")
    create_private_dir(output)
    before = {}
    runtime_before = None
    log = io.StringIO()
    try:
        save_private(output / "helper-source.txt", Path(__file__).read_bytes())
        runtime_before = runtime_identity()
        save_json(output / "runtime-before.json", runtime_before)
        before = {path: pin(kg / path) for path in case["code"] + tuple(case["input_pins"])}
        inspection = inspect_inputs(kg, original, case_name)
        save_json(output / "preflight.json", inspection)
        create_private_dir(output / "runtime-cache")
        # Pystow initializes a README during the oaklib import. Keep that incidental
        # library cache private; never let imports initialize the user's home cache.
        os.environ["PYSTOW_HOME"] = str(output / "runtime-cache")
        mapping = None
        with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            with private_owner_io(output) as reads:
                obj, mapping = prepare_owner(kg, case_name)
        save_private(output / "loader.log", log.getvalue().encode())
        save_json(output / "owner-mapping.json", mapping)
        if mode == "plan":
            result = {**inspection, "status": "checked-no-emission", "owner_mapping": mapping,
                      "owner_read_paths": sorted(reads), "limits": LIMITS}
        else:
            persist_inputs(kg, original, output, inspection, case_name)
            create_private_dir(output / "owner-output")
            trace, calls, lines, trace_rows = emission_trace(kg, case_name)
            require(sys.gettrace() is None, "Unexpected existing runtime tracer")
            with private_owner_io(output) as emission_reads:
                sys.settrace(trace)
                try:
                    returned = obj._process_single_file(output / "bounded-input.jsonl",
                                                        output / "owner-output", show_status=False)
                finally:
                    sys.settrace(None)
            header, raw_rows, rows = read_rows(returned["edges_file"])
            require(len(rows) == 1, "Expected exactly one emitted edge occurrence")
            comparison = compare_edge(rows[0], inspection["original_edge"])
            require(header == obj.edge_header, "Unexpected edge header")
            for key in ("unmapped_traits", "measurement_traits", "unresolved_taxa"):
                require(returned[key] == [], f"Unexpected diagnostic output: {key}")
            require(returned["indeterminate_traits_file"].read_bytes() == b"",
                    "Unexpected indeterminate trait output")
            result = {**inspection, "status": "replayed", "owner_mapping": mapping,
                      "execution_path": MODULE + ".MetaTraitsTransform._process_single_file/Tier1",
                      "executed_calls": calls,
                      "executed_lines": {key: sorted(value) for key, value in lines.items()},
                      "writer_calls_raw_rows": trace_rows, "emitted_raw_rows": raw_rows,
                      "comparison": comparison,
                      "owner_return": {key: str(value) if isinstance(value, Path) else value
                                       for key, value in returned.items()},
                      "owner_read_paths": sorted(reads | emission_reads), "limits": LIMITS,
                      "emitted_line_hashes": {
                          str(path.relative_to(output)): [sha(line) for line in
                                                         path.read_bytes().splitlines(keepends=True)]
                          for path in sorted((output / "owner-output").iterdir())}}
        after = {path: pin(kg / path) for path in before}
        require(before == after, "Read-only owner identity changed during run")
        runtime_after = runtime_identity()
        save_json(output / "runtime-after.json", runtime_after)
        require(runtime_before == runtime_after, "Retained runtime changed during run")
        require(inspection["packet_pins"] == {name: pin(original / name)
                                             for name in case["packet_pins"]},
                "Original packet changed during run")
        result.update(owner_identity_before=before, owner_identity_after=after,
                      runtime_identity_unchanged=True, original_packet_identity_unchanged=True,
                      owner_checkout=str(kg), original_packet_directory=str(original),
                      helper_sha256=sha(Path(__file__).read_bytes()), mode=mode,
                      invocation=sys.argv, schema="edgemech.metatraits-retained-owner-replay/v2")
        result["artifact_pins"] = {str(path.relative_to(output)): pin(path)
                                   for path in sorted(output.rglob("*")) if path.is_file()}
        receipt = save_json(output / "receipt.json", result)
        return {"output": str(output), "receipt": receipt, "status": result["status"]}
    except Exception as error:
        # Failures are durable, including partial owner output; never reuse this attempt.
        save_json(output / "failure.json", {
            "error_type": type(error).__name__, "error": str(error), "invocation": sys.argv,
            "case": case_name,
            "runtime_identity_unchanged": (runtime_identity() == runtime_before
                                           if runtime_before is not None else None),
            "helper_sha256": sha(Path(__file__).read_bytes()), "owner_identity_before": before,
            "owner_identity_after": {path: pin(kg / path) for path in before},
            "captured_log": log.getvalue(), "limits": LIMITS})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "replay", "verify"))
    parser.add_argument("--case", choices=tuple(CASES), default="first43")
    parser.add_argument("--kg", type=Path, required=True)
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.absolute()
    if args.mode == "verify":
        result = verify_artifacts(output, args.case)
        save_json(output / "independent-readback.json", result)
    else:
        result = run(args.mode, args.kg.resolve(), args.original.resolve(), output, args.case)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
