"""One fresh14 source witness using actual owner code; no scientific assessment.

check: freeze and inspect exact inputs, then test owner imports without a source run.
replay: repeat checks, run one literal CSV record through LPSNTransform.run.
verify: independently reread an attempt's artifacts without executing owner code.

The retained finalized TSV is explicitly NOT assumed to be the sampled TSV.
No constructor, finalizer, provider, full dataset transform or owner mutation runs.
"""
from __future__ import annotations

import argparse
import ast
import builtins
import contextlib
import csv
import hashlib
import importlib
import json
import os
import stat
import subprocess
import sys
import traceback
from pathlib import Path
from types import CodeType
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
OWNER = Path("/Users/marcin/Documents/VIMSS/ontology/KG-Hub/KG-Microbe/kg-microbe")
ORIGINAL = Path("/Users/marcin/agent-work/EdgeMech/m5-calibration-round03-20261116")
PACKET_DIR = Path(".temp/edge-calibration-20261115/fresh-14")
PACKAGE = Path(".temp/m5-round03-worker-20261116/round03-package")
BASE = "bcfa6bf5bfaa5fca23063fd1483d9fcbcb58a977"
CURRENT = "d6baf5b90003a2032747559d94c00f86a7a4c615"
LATER = "2d94ed094167d94402f21400a9ad7dc4f7f20438"
PRODUCER = "kg_microbe/transform_utils/lpsn/lpsn.py"
CODE = (PRODUCER, "kg_microbe/transform_utils/transform.py",
        "kg_microbe/transform_utils/constants.py", "kg_microbe/utils/tsv_io.py",
        "kg_microbe/utils/atomic_io.py", "kg_microbe/utils/source_finalization.py",
        "kg_microbe/utils/producer_audits.py")
RAW = "data/raw/lpsn_gss.csv"
EDGES = "data/transformed/lpsn/edges.tsv"
FINALIZATION = "data/transformed/lpsn/source_finalization.json"
FINGERPRINT = "data/transformed/lpsn/source_fingerprint.json"
API = "data/raw/lpsn/api_cache/781160.json"
OCCURRENCE = "urn:kg-microbe:occurrence:v1:78725eeeea961ce059a55092aebc34b522b1b4ffc2ea844207ce7049a039cc80"
ASSERTION = {"subject": "lpsn:781160", "predicate": "biolink:close_match",
             "object": "kgmicrobe.strain:JCM-14905", "relation": "skos:closeMatch"}
QUALIFIERS = {"primary_knowledge_source": "infores:lpsn",
              "knowledge_level": "knowledge_assertion", "agent_type": "manual_agent"}
SOURCE_ROW = 29573
EDGE_ROW = 116674
RECORD_SHA = "c7024f0fe3d29afec99cc98973bf2fb6f4314fc343ae741ee2ac33c3dadd432c"
MANIFEST_SHA = "3928396bf4c089620ec0209fdcb986c14f36969259ed01ab563c6807037ee298"
PACKET_PINS = {
    "packet.json": "c1c4a61470174802cfdbc08f31fd0e83b273270906111f5a4ef587ae973bd012",
    "source.json": "71e4b06bdf0f854037fc988999121e4494fddafdedae701031efb607c391f49d",
    "occurrence.json": "85f749adc4796dc82250f071109ed50fd00065c213dfeb65d412ef17f930a55c",
}
OWNER_PINS = {
    PRODUCER: "853aeac589d6f7b735cc5996e28c3623c03c7088517fd3167e76f7c2299e2da0",
    RAW: "31cb2ac2d4eaf965a92a02ad28a39cfece141f703b17815b4223ac091ea603f3",
    EDGES: "c5e39f276cc32b260bb11f35afbc14a40fa85b0d217e047a1b7bc2ac5f496c03",
}
LIMITS = [
    "Mechanical source/field/emission witness only; no scientific category or approval.",
    "Unknown historical dirty state remains unknown; clean-base replay is not original execution.",
    "Original transform row number is packet metadata; retained finalized TSV row 116674 differs.",
    "The original literal transformed row and all of its qualifiers are not recovered by this replay.",
    "One full source record is replayed, including its sibling deposits, but only fresh14 is compared.",
    "NCBI/GTDB lookups use explicitly empty indexes; parent rows are outside the bounded input.",
    "No constructor, graph finalization, merged output, ontology admission or independent taxonomy is replayed.",
    "Source type designation, mapping semantics and species/strain identity are distinct dependencies.",
    "E005/E006 were retrieved 2026-11-16 without declared releases; E001 is Biolink 4.4.0, while retained finalization declares schema 4.4.2.",
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def pin(path):
    require(path.is_file() and not path.is_symlink(), f"Not a regular input: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return {"sha256": digest.hexdigest(), "bytes": path.stat().st_size}


def private_dir(path):
    require(not path.exists() and not path.is_symlink(), "Attempt must be fresh")
    missing = []
    ancestor = path
    while not ancestor.exists():
        require(not ancestor.is_symlink(), "Symlink directory prohibited")
        missing.append(ancestor)
        ancestor = ancestor.parent
    require(not any(p.is_symlink() for p in (ancestor, *ancestor.parents)),
            "Symlink ancestor prohibited")
    for item in reversed(missing):
        item.mkdir(mode=0o700)
        item.chmod(0o700)


def save(path, raw):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        os.fchmod(stream.fileno(), 0o600)
        stream.write(raw)
    require(pin(path) == {"sha256": sha(raw), "bytes": len(raw)}, "Write readback mismatch")


def save_json(path, value):
    save(path, (json.dumps(value, indent=2, sort_keys=True) + "\n").encode())


def git_bytes(owner, revision, path):
    return subprocess.check_output(["git", "-C", str(owner), "show", f"{revision}:{path}"])


def literal_record(path, ordinal):
    """Stream CSV records, preserving original header and multiline record bytes."""
    with path.open(encoding="utf-8", newline="") as stream:
        lines = []

        def tracked():
            for line in stream:
                lines.append(line)
                yield line

        reader = csv.DictReader(tracked(), strict=True)
        require(reader.fieldnames is not None, "Missing CSV header")
        header = "".join(lines)
        lines.clear()
        start = reader.line_num + 1
        for number, row in enumerate(reader, 1):
            require(None not in row and None not in row.values(), "Malformed CSV width")
            if number == ordinal:
                return row, header.encode(), "".join(lines).encode(), [start, reader.line_num]
            lines.clear()
            start = reader.line_num + 1
    raise ValueError("Missing CSV record")


def packet_records(packet, occurrence, source):
    for item in (packet["original_assertion"], occurrence, source["edge"]):
        expected = {**ASSERTION, "occurrence_id": OCCURRENCE,
                    "origin_transform": "lpsn/edges.tsv", "transform_row_number": EDGE_ROW}
        require(all(item.get(k) == v for k, v in expected.items()), "Wrong original occurrence")
    require(packet["occurrence_id"] == OCCURRENCE, "Wrong packet identity")
    require(all(occurrence.get(k) == v for k, v in QUALIFIERS.items()), "Changed qualifiers")
    selected = [r for r in packet["source_records"] if r["source_relative_path"] == "lpsn_gss.csv"]
    require(len(selected) == 1, "Ambiguous source selector")
    selected = selected[0]
    require(selected["locator"] == f"CSV data row {SOURCE_ROW}", "Changed source ordinal")
    require(selected["text_sha256"] == RECORD_SHA == sha(selected["text"].encode()),
            "Changed source record")
    require(selected in source["records"], "Packet/source record disagreement")
    return selected


def inspect_edges(path):
    """Record all matching retained occurrences, never substitute their ordinal."""
    matches = []
    at_original_ordinal = None
    with path.open(newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        for number, row in enumerate(reader, 1):
            require(None not in row and None not in row.values(), "Malformed retained TSV")
            if number == EDGE_ROW:
                at_original_ordinal = row
            if all(row.get(k) == v for k, v in ASSERTION.items()):
                matches.append({"data_row": number, "row": row})
    require(at_original_ordinal is not None, "Missing retained ordinal")
    return {"original_packet_ordinal": EDGE_ROW, "retained_at_original_ordinal": at_original_ordinal,
            "retained_ordinal_matches_original_assertion": all(
                at_original_ordinal.get(k) == v for k, v in ASSERTION.items()),
            "retained_matches": matches, "retained_match_count": len(matches)}


def inspect_inputs(owner, original, output):
    manifest_path = original / PACKAGE / "manifest.json"
    require(pin(manifest_path)["sha256"] == MANIFEST_SHA, "Wrong round03 manifest")
    manifest = json.loads(manifest_path.read_text())
    bindings = {item["path"]: item for item in manifest["files"]}
    save(output / "round03-manifest.json", manifest_path.read_bytes())
    packets = {}
    for name, expected in PACKET_PINS.items():
        path = original / PACKET_DIR / name
        require(pin(path)["sha256"] == expected == bindings[str(PACKET_DIR / name)]["sha256"],
                f"Frozen packet mismatch: {name}")
        save(output / ("frozen-" + name), path.read_bytes())
        packets[name] = json.loads(path.read_text())
    selected = packet_records(packets["packet.json"], packets["occurrence.json"],
                              packets["source.json"])
    evidence = {}
    for number in (1, 5, 6, 7):
        identifier = f"r03-evidence-{number:03}"
        for folder, suffix in (("evidence", ".txt"), ("receipts", ".json")):
            relative = PACKAGE / folder / (identifier + suffix)
            binding = bindings[str(relative)]
            require(pin(original / relative)["sha256"] == binding["sha256"],
                    f"Manifest evidence mismatch: {relative}")
            save(output / (identifier + suffix), (original / relative).read_bytes())
            evidence[str(relative)] = binding
    receipt = json.loads((output / "r03-evidence-007.json").read_text())
    later_source = original / receipt["original_path"]
    require(pin(later_source)["sha256"] == receipt["source_sha256"], "E007 original mismatch")
    require(later_source.read_bytes() == git_bytes(owner, LATER, PRODUCER), "E007 Git mismatch")
    save(output / "later-E007-owner-source.txt", later_source.read_bytes())
    row, header, literal, physical = literal_record(owner / RAW, SOURCE_ROW)
    require(row == json.loads(selected["text"]), "Retained raw row differs from frozen source")
    require(row["record_no"] == "781160" and row["sp_epithet"] == "nassauensis"
            and row["subsp_epithet"] == "", "Wrong source scope")
    save(output / "original-source-record.csv", header + literal)
    save_json(output / "selected-source.json", row)
    pins = {path: pin(owner / path) for path in (*CODE, RAW, EDGES, FINALIZATION, FINGERPRINT, API)}
    for path, expected in OWNER_PINS.items():
        require(pins[path]["sha256"] == expected, f"Retained owner pin mismatch: {path}")
    history = {}
    for path in CODE:
        history[path] = {revision: sha(git_bytes(owner, revision, path))
                         for revision in (BASE, CURRENT)}
        require(history[path][BASE] == history[path][CURRENT] == pins[path]["sha256"],
                f"Owner code differs from sampled clean base: {path}")
        save(output / path.replace("/", "__"), (owner / path).read_bytes())
    for path in (FINALIZATION, FINGERPRINT, API):
        save(output / path.replace("/", "__"), (owner / path).read_bytes())
    finalization = json.loads((owner / FINALIZATION).read_text())
    require(finalization["members"]["edges.tsv"] == pins[EDGES], "Finalized edges pin mismatch")
    require(finalization["consumed_inputs"]["lpsn_gss_native"]["sha256"] == pins[RAW]["sha256"],
            "Finalized raw input mismatch")
    api = json.loads((owner / API).read_text())
    frozen_api = [r for r in packets["packet.json"]["source_records"]
                  if r["source_relative_path"] == "lpsn/api_cache/781160.json"]
    require(len(frozen_api) == 1 and api == json.loads(frozen_api[0]["text"]),
            "Retained API cache differs from packet")
    edge_inspection = inspect_edges(owner / EDGES)
    save_json(output / "retained-transformed-linkage.json", edge_inspection)
    selector = original / "scripts/adhoc/edge_sample_review_20261112/source_fidelity.py"
    save(output / "original-packet-selector-source.txt", selector.read_bytes())
    return {"occurrence_id": OCCURRENCE, "assertion": ASSERTION, "qualifiers": QUALIFIERS,
            "source_row": SOURCE_ROW, "source_physical_lines": physical,
            "source_literal_sha256": sha(literal), "source_canonical_sha256": RECORD_SHA,
            "source_field": "nomenclatural_type", "source_value": row["nomenclatural_type"],
            "owner_pins": pins, "clean_history": history, "manifest_sha256": MANIFEST_SHA,
            "packet_pins": PACKET_PINS, "authority_bindings": evidence,
            "later_E007_original_sha256": receipt["source_sha256"],
            "retained_transformed_linkage": edge_inspection,
            "selector_sha256": pin(selector)["sha256"],
            "api_declared_version": api["lpsn_version"], "api_category": api["category"],
            "finalization_schema": json.loads((owner / FINGERPRINT).read_text())["schema"],
            "runtime": {"executable": sys.executable, "version": sys.version}, "limits": LIMITS}


@contextlib.contextmanager
def private_owner_io(output):
    """Enforce local exclusive I/O during imports and replay, including dependencies."""
    active = True
    reads = set()
    original_open = builtins.open

    def audit(event, args):
        if not active:
            return
        if event in ("socket.connect", "socket.getaddrinfo", "socket.bind", "subprocess.Popen",
                     "os.system", "os.remove", "os.rename", "os.rmdir", "os.symlink", "os.link"):
            raise ValueError(f"Owner operation prohibited: {event}")
        if event == "open" and not isinstance(args[0], int):
            path = Path(args[0]).resolve()
            require(not any(part.lower() in (".aws", ".ssh", ".netrc", ".env", "credentials")
                            for part in path.parts), "Credential access prohibited")
            flags = args[2]
            if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
                require(path.is_relative_to(output) and flags & os.O_EXCL,
                        "Owner writes must be exclusive and private")
            else:
                reads.add(str(path))
        if event in ("os.mkdir", "os.chmod") and not isinstance(args[0], int):
            require(Path(args[0]).resolve().is_relative_to(output), "Owner mutation outside output")

    def exclusive_open(file, mode="r", *args, **kwargs):
        # os.fdopen wraps a descriptor whose path/creation flags were already
        # checked by the audit hook; there is no new pathname operation here.
        if isinstance(file, int):
            return original_open(file, mode, *args, **kwargs)
        if any(char in mode for char in "wax+"):
            require(mode in ("w", "wb", "wt", "x", "xb", "xt", "x+b"), "Unsafe write mode")
            require(Path(file).resolve().is_relative_to(output), "Write outside output")
            stream = original_open(file, mode.replace("w", "x"), *args, **kwargs)
            os.fchmod(stream.fileno(), 0o600)
            return stream
        return original_open(file, mode, *args, **kwargs)

    def path_open(path, mode="r", buffering=-1, encoding=None, errors=None, newline=None):
        return exclusive_open(path, mode, buffering=buffering, encoding=encoding,
                              errors=errors, newline=newline)

    sys.addaudithook(audit)
    old_umask = os.umask(0o077)
    try:
        with (patch("builtins.open", exclusive_open), patch("io.open", exclusive_open),
              patch("pathlib.Path.open", path_open)):
            yield reads
    finally:
        active = False
        os.umask(old_umask)


def code_tree(code):
    yield code
    for value in code.co_consts:
        if isinstance(value, CodeType):
            yield from code_tree(value)


def owner_headers(owner, constants):
    tree = ast.parse((owner / CODE[1]).read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Transform")
    init = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "__init__")
    headers = {}
    for node in init.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if isinstance(target, ast.Attribute) and target.attr in ("node_header", "edge_header"):
            require(isinstance(node.value, ast.List) and
                    all(isinstance(n, ast.Name) for n in node.value.elts), "Unknown header expression")
            headers[target.attr] = [getattr(constants, n.id) for n in node.value.elts]
    require(set(headers) == {"node_header", "edge_header"}, "Missing owner headers")
    return headers


def import_owner(owner):
    require(not any(n == "kg_microbe" or n.startswith("kg_microbe.") for n in sys.modules),
            "Owner import requires fresh process")
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(owner))
    module = importlib.import_module("kg_microbe.transform_utils.lpsn.lpsn")
    constants = importlib.import_module("kg_microbe.transform_utils.constants")
    # Exercise the imports actually needed by the parser/audit path during free checks.
    importlib.import_module("kg_microbe.utils.source_finalization")
    importlib.import_module("kg_microbe.utils.producer_audits")
    require(Path(module.__file__).resolve() == owner / PRODUCER, "Wrong owner module")
    compiled = set(code_tree(compile((owner / PRODUCER).read_text(), str(owner / PRODUCER),
                                    "exec", dont_inherit=True)))
    for name in ("run", "_parse_csv", "_extract_strain_deposits", "_make_close_match_edge"):
        require(getattr(module.LPSNTransform, name).__code__ in compiled, "Owner bytecode mismatch")
    require(constants.CLOSE_MATCH_PREDICATE == ASSERTION["predicate"] and
            constants.CLOSE_MATCH_RELATION == ASSERTION["relation"], "Mapping constant mismatch")
    return module, owner_headers(owner, constants)


class EmptyIndex:
    """Explicitly excludes independent NCBI and GTDB crosswalks from this unit."""

    def curies_by_label(self, label):
        return []

    def curies_by_rank_name(self, rank, name):
        return []


def execute_unit(owner, output, module, headers):
    obj = module.LPSNTransform.__new__(module.LPSNTransform)
    obj.begin_consumed_inputs()
    obj.source_name = "lpsn"
    obj.output_dir = output / "owner-output"
    private_dir(obj.output_dir)
    obj.output_node_file = obj.output_dir / "nodes.tsv"
    obj.output_edge_file = obj.output_dir / "edges.tsv"
    obj.knowledge_source = "infores:lpsn"
    obj.ncbi_impl = obj.gtdb_index = EmptyIndex()
    obj._ncbi_stats = {"matched": 0, "unmatched": 0, "ambiguous": 0}
    obj._gtdb_stats = dict(obj._ncbi_stats)
    for name, value in headers.items():
        setattr(obj, name, value)
    compiled = set(code_tree(compile((owner / PRODUCER).read_text(), str(owner / PRODUCER),
                                    "exec", dont_inherit=True)))
    events = []

    def trace(frame, event, arg):
        if frame.f_code.co_filename != str(owner / PRODUCER):
            return None
        require(frame.f_code in compiled, "Executed owner code differs from pinned source")
        require(frame.f_code.co_name not in ("__init__", "_load_ncbi_adapter", "_load_gtdb_index"),
                "Unbounded owner path")
        if event in ("call", "return"):
            item = {"event": event, "function": frame.f_code.co_name,
                    "line": frame.f_lineno}
            if frame.f_code.co_name == "_make_close_match_edge":
                item["arguments"] = {k: frame.f_locals[k]
                                     for k in ("record_no", "strain_curie", "inferred")}
            if event == "return" and frame.f_code.co_name in (
                    "_extract_strain_deposits", "_make_close_match_edge"):
                item["result"] = arg
            events.append(item)
        if event == "line" and frame.f_code.co_name == "run":
            events.append({"event": "line", "function": "run", "line": frame.f_lineno})
        return trace

    @contextlib.contextmanager
    def retained_write(path, mode="w", **kwargs):
        # Only replace transactional I/O; actual parser, branches, row builders,
        # serializer and consumed-input/audit checks remain the owner's code.
        require(mode == "w", "Unexpected atomic write mode")
        with open(path, "x", **kwargs) as stream:
            yield stream

    def retained_temporary(*, mode, dir):
        # The owner's snapshot algorithm still copies, hashes and rereads the
        # bytes. Only temporary-file lifecycle changes: exclusive and retained.
        require(mode == "w+b" and Path(dir) == obj.output_dir, "Unexpected snapshot request")
        return open(Path(dir) / ("consumed-" + os.urandom(12).hex() + ".csv"), "x+b")

    previous_trace = sys.gettrace()
    try:
        with (patch.object(module, "atomic_write", retained_write),
              patch("tempfile.NamedTemporaryFile", retained_temporary)):
            sys.settrace(trace)
            obj.run(data_file=output / "original-source-record.csv", show_status=False)
    finally:
        sys.settrace(previous_trace)
        save_json(output / "owner-trace.json", events)
    require(set(obj._native_gss_records) == {"781160"}, "More than one source unit parsed")
    save_json(output / "owner-native-records.json", obj._native_gss_records)
    save_json(output / "owner-consumption.json", {"inputs": obj.consumed_input_snapshots,
                                                "audit": obj.producer_audit_snapshots})


def compare_outputs(output):
    with (output / "owner-output/edges.tsv").open(newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        rows = list(reader)
        columns = reader.fieldnames
    require(rows and all(None not in r and None not in r.values() for r in rows), "Bad emitted TSV")
    matches = [row for row in rows if all(row.get(k) == v for k, v in ASSERTION.items())]
    require(len(matches) == 1, "Selected emitted occurrence missing or duplicated")
    selected = matches[0]
    require(all(selected.get(k) == v for k, v in QUALIFIERS.items()), "Changed emitted qualifiers")
    trace = json.loads((output / "owner-trace.json").read_text())
    emissions = [event for event in trace if event["event"] == "return" and
                 event["function"] == "_make_close_match_edge" and
                 event["arguments"]["strain_curie"] == ASSERTION["object"]]
    require(len(emissions) == 1 and emissions[0]["arguments"] ==
            {"record_no": "781160", "strain_curie": ASSERTION["object"], "inferred": False},
            "Selected emitting branch missing or ambiguous")
    require(dict(zip(columns, emissions[0]["result"])) == selected, "Trace/output disagreement")
    native = json.loads((output / "owner-native-records.json").read_text())
    require(set(native) == {"781160"} and native["781160"]["row"] ==
            json.loads((output / "selected-source.json").read_text()), "Native source mismatch")
    retained = json.loads((output / "retained-transformed-linkage.json").read_text())
    comparisons = []
    for item in retained["retained_matches"]:
        other = item["row"]
        differences = {k: [selected.get(k, ""), other.get(k, "")]
                       for k in set(selected) | set(other)
                       if selected.get(k, "") != other.get(k, "")}
        comparisons.append({"retained_data_row": item["data_row"], "differences": differences,
                            "retained_columns_absent_from_emission": sorted(set(other) - set(selected))})
    return {"selected_emission": selected, "emitted_columns": columns, "emitted_rows": rows,
            "source_units": 1, "selected_occurrences": len(matches),
            "selected_branch": emissions[0], "retained_comparisons": comparisons,
            "original_packet_known_fields_match": True,
            "original_literal_transformed_row_recovered": False, "limits": LIMITS}


def verify_attempt(output):
    receipt = json.loads((output / "receipt.json").read_text())
    for relative, expected in receipt["artifacts"].items():
        require(pin(output / relative) == expected, f"Artifact mismatch: {relative}")
    for path in (output, *output.rglob("*")):
        require(not path.is_symlink(), "Symlink artifact")
        mode = stat.S_IMODE(path.stat().st_mode)
        require(mode == (0o700 if path.is_dir() else 0o600), f"Nonprivate artifact: {path}")
    if receipt["mode"] == "replay":
        require(compare_outputs(output) == receipt["comparison"], "Independent comparison differs")
    return {"verified": True, "mode": receipt["mode"], "receipt": pin(output / "receipt.json"),
            "artifacts": len(receipt["artifacts"]), "scientific_assessment": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("check", "replay", "verify"))
    parser.add_argument("--attempt", type=Path, required=True)
    args = parser.parse_args()
    output = args.attempt.absolute()
    allowed = ROOT / ".temp/content-review-20261119"
    require(output.parent == allowed and output.name.startswith("fresh14-"), "Invalid attempt path")
    if args.mode == "verify":
        print(json.dumps(verify_attempt(output), indent=2))
        return
    private_dir(output)
    save(output / "helper-source.txt", Path(__file__).read_bytes())
    save_json(output / "invocation.json", {"argv": sys.argv, "executable": sys.executable,
                                          "cwd": str(Path.cwd()), "mode": args.mode})
    try:
        preflight = inspect_inputs(OWNER, ORIGINAL, output)
        save_json(output / "preflight.json", preflight)
        private_dir(output / "runtime-cache")
        os.environ["PYSTOW_HOME"] = str(output / "runtime-cache")
        with (private_owner_io(output) as reads,
              (output / "owner.log").open("x") as log,
              contextlib.redirect_stdout(log), contextlib.redirect_stderr(log)):
            module, headers = import_owner(OWNER)
            save_json(output / "owner-import.json", {"module": str(module.__file__),
                                                     "headers": headers, "compatible": True})
            if args.mode == "replay":
                execute_unit(OWNER, output, module, headers)
        save_json(output / "owner-read-paths.json", sorted(reads))
        # Rehash every inspected owner file; no repair or mutation is permitted.
        require({p: pin(OWNER / p) for p in preflight["owner_pins"]} == preflight["owner_pins"],
                "Owner input changed during attempt")
        comparison = compare_outputs(output) if args.mode == "replay" else None
        artifacts = {str(p.relative_to(output)): pin(p) for p in sorted(output.rglob("*"))
                     if p.is_file()}
        save_json(output / "receipt.json", {"mode": args.mode, "artifacts": artifacts,
                                            "comparison": comparison, "limits": LIMITS})
        print(json.dumps(verify_attempt(output), indent=2))
    except BaseException as exc:
        save_json(output / "failure.json", {"error_type": type(exc).__name__, "error": str(exc),
                                            "traceback": traceback.format_exc(), "limits": LIMITS})
        raise


if __name__ == "__main__":
    main()
