#!/usr/bin/env python3
"""Prepare round03 literal bounded evidence, never scientific ratings (2026-11-16).

Issues #175, #180, #181, #183: read hash-pinned round02 raw inputs and round03
owner replay; retain private full originals and produce source-only navigation,
exact UTF-8 byte-span receipts and current-runtime packet projections. Canary
one PREGO and one mixed-literal producer derivative before future assembly.
The view-repair candidate has distinct paths and does not replace round03.
Outputs are private/exclusive. This does
not freeze a package, launch reviewers, execute evidence code or assign labels.
"""
from __future__ import annotations

import argparse
import ast
import io
import json
import tokenize
from pathlib import Path

import calibration_round_20261116 as rounds
import prepare_m5_reviewer_views_20261116 as original_views
import prepare_m5_round02_views_20261116 as views
import run_m5_review_worker_20261116 as worker

ROOT = rounds.ROOT
OLD = Path("/Users/marcin/agent-work/EdgeMech/m5-calibration-round02-20261116")
OLD_MANIFEST = ".temp/m5-round02-worker-20261116/round02-final/round-02-manifest.json"
OLD_SHA = "09fa2916bc298cd4a76c9baec27470cb0b7b47f44f9570775609b438ebe81445"
RUN = Path(".temp/m5-round03-worker-20261116")
FUTURE = RUN / "future-view-repair-01"
PACKAGE = FUTURE / "package"
PRIVATE = FUTURE / "private-originals"
CANARY = FUTURE / "prego-canary"
PRODUCER_CANARY = FUTURE / "source028-canary"
PACKAGE_ID = "m5-calibration-20261116-round03-view-repair01"
REPLAY = Path(".temp/first30-owner-replay-20261116/run-03")
REPLAY_SHA = "b79a181d650c6030c6df16507093cc66852e20b456bd491500756e1b86f8a4f1"
HELPER = "scripts/adhoc/assemble_m5_round03_20261116.py"
PREGO_SHA = "a36dc745ec1a2470c4f237e753736c28ef7ccd6d40976c6619411bd5d9e71935"
DOWNLOAD_SHA = "209669d1de7e2dfea17712a755217fd201241d2e32f763366ff0570270610153"
PROCESS_SHA = "85bb1d23ecb938bd31d1deefd479042ce3b12f35dce8ade511ddc8e499537790"
PRODUCER_NAME = "microbedecoder.py"
PRODUCER_SHA = "8aa801621cae6df7605a38b04a4f1eaf8da57aa2239db770f0ad3c5ab741d63b"
PRODUCER_VERSION = "d6baf5b90003a2032747559d94c00f86a7a4c615"
# Content-reviewed UTF-8 byte interval. Full source remains private. The interval
# includes a string-token boundary, but no current substantive definition.
PRODUCER_OMISSION = (7570, 7659)
EXPOSURE = (
    "Original source identifiers, substantive definitions, generated values and source selection "
    "remain visible. Executable strings receive content review: current definitions, conditions "
    "and counterevidence are retained, while separately identified historical evaluation is "
    "omitted with exact receipts. Code status alone does not make narration inseparable. "
    "Views are literal source fragments, not executable replacement code or scientific verdicts. "
    "Private complete originals remain available for mechanical provenance checks."
)


def retained():
    raw = rounds.safe(OLD, OLD_MANIFEST).read_bytes()
    rounds.require(rounds.digest(raw) == OLD_SHA, "Old manifest changed")
    return json.loads(raw)


def source(pin):
    raw = rounds.safe(OLD, pin["path"]).read_bytes()
    rounds.require(rounds.digest(raw) == pin["sha256"], "Old source changed")
    return raw


def persist(path, raw):
    target = rounds.safe(ROOT, str(path), exists=False)
    original_views.private_parents(target.parent)
    if target.exists():
        rounds.require(target.read_bytes() == raw, "Existing input differs")
    else:
        rounds.write(ROOT, str(path), raw=raw)
    return str(path)


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def complements(size, removed):
    merged = []
    for start, end in sorted(removed):
        rounds.require(0 <= start < end <= size, "Invalid omitted span")
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(end, merged[-1][1])
        else:
            merged.append([start, end])
    spans, cursor = [], 0
    for start, end in merged:
        if cursor < start:
            spans.append((cursor, start))
        cursor = end
    if cursor < size:
        spans.append((cursor, size))
    return spans


def reviewed_literal_omissions(raw, path):
    """Apply one content-reviewed omission; never classify by keyword alone."""
    digest = rounds.digest(raw)
    if Path(path).name != PRODUCER_NAME and digest != PRODUCER_SHA:
        return []
    rounds.require(digest == PRODUCER_SHA, "Producer literal review requires exact source hash")
    start, end = PRODUCER_OMISSION
    rounds.require(0 <= start < end <= len(raw), "Invalid reviewed literal omission")
    return [{"source_byte_start": start, "source_byte_end": end,
             "sha256": rounds.digest(raw[start:end]),
             "source_version": PRODUCER_VERSION,
             "reason": "separable_historical_evaluation"}]


def python_spans(raw, *, exclude_description=False, extra_removed=()):
    """Remove prose tokens without executing or rewriting producer source code."""
    text = raw.decode("utf-8")
    lines = text.splitlines(keepends=True)
    starts, cursor = [], 0
    for line in lines:
        starts.append(cursor)
        cursor += len(line.encode())

    def token_position(position):
        row, column = position
        return starts[row - 1] + len(lines[row - 1][:column].encode())

    removed = list(extra_removed)
    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        if token.type == tokenize.COMMENT:
            removed.append((token_position(token.start), token_position(token.end)))
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                value = body[0].value
                if isinstance(value.value, str):
                    removed.append((starts[value.lineno - 1] + value.col_offset,
                                    starts[value.end_lineno - 1] + value.end_col_offset))
        if exclude_description and isinstance(node, ast.FunctionDef) and node.name == "description":
            first = min([node.lineno, *[d.lineno for d in node.decorator_list]])
            removed.append((starts[first - 1], starts[node.end_lineno - 1] + node.end_col_offset))
    return complements(len(raw), removed)


def bounded(raw, path):
    digest = rounds.digest(raw)
    policy = "whole_native_document"
    spans = [(0, len(raw))]
    omissions = []
    if digest == PREGO_SHA:
        rounds.require(raw.count(b'"Taxon') == 1, "Producer convention anchor is ambiguous")
        begin = raw.index(b'"Taxon')
        end = raw.index(b". Excluding", begin) + 1
        spans = [(begin, end)]
        policy = "producer_convention_sentence_only"
    elif Path(path).suffix == ".py" or digest == PRODUCER_SHA:
        omissions = reviewed_literal_omissions(raw, path)
        spans = python_spans(raw, exclude_description=digest == PROCESS_SHA,
                             extra_removed=[(item["source_byte_start"], item["source_byte_end"])
                                            for item in omissions])
        policy = "producer_code_without_comments_docstrings_or_redacted_description"
        if omissions:
            policy = "producer_code_with_reviewed_literal_omission"
    elif digest == DOWNLOAD_SHA:
        removed, cursor = [], 0
        for line in raw.splitlines(keepends=True):
            if line.lstrip().startswith(b"#"):
                removed.append((cursor, cursor + len(line)))
            cursor += len(line)
        spans = complements(len(raw), removed)
        policy = "download_configuration_without_commentary"
    output, bindings = bytearray(), []
    for start, end in spans:
        chunk = raw[start:end]
        if not chunk.strip():
            continue
        if output:
            output.extend(b"\n\n")
        view_start = len(output)
        output.extend(chunk)
        bindings.append({"source_byte_start": start, "source_byte_end": end,
                         "view_byte_start": view_start, "view_byte_end": len(output),
                         "sha256": rounds.digest(chunk)})
    rounds.require(output and bindings, "Empty authority view")
    return bytes(output), {"policy": policy, "spans": bindings,
                           "source_sha256": digest, "view_sha256": rounds.digest(output),
                           "offset_encoding": "UTF-8 bytes; zero-based half-open",
                           "span_separator": "two LF bytes, not source text",
                           "reviewed_content_omissions": omissions,
                           "inseparable_exposure": EXPOSURE}


def prego_pin():
    pins = [p for p in retained()["files"] if p["sha256"] == PREGO_SHA]
    rounds.require(len(pins) == 1, "PREGO input is not unique")
    return pins[0]


def canary():
    rounds.require(not (ROOT / CANARY).exists(), "Canary output exists")
    pin = prego_pin()
    raw = source(pin)
    view, receipt = bounded(raw, pin["path"])
    persist(CANARY / "source.txt", raw)
    persist(CANARY / "view.txt", view)
    receipt.update(version=pin["version"], helper_sha256=rounds.digest(Path(__file__).read_bytes()))
    persist(CANARY / "receipt.json", encoded(receipt))
    return check_canary()


def check_canary():
    receipt = rounds.read(ROOT, str(CANARY / "receipt.json"))
    pin = prego_pin()
    view, expected = bounded(source(pin), pin["path"])
    expected.update(version=pin["version"], helper_sha256=rounds.digest(Path(__file__).read_bytes()))
    rounds.require(receipt == expected, "Bounded canary configuration changed")
    rounds.require((ROOT / CANARY / "view.txt").read_bytes() == view
                   and rounds.digest((ROOT / CANARY / "source.txt").read_bytes()) == PREGO_SHA,
                   "Persisted bounded canary changed")
    return {"receipt": str(CANARY / "receipt.json"), "view_sha256": rounds.digest(view),
            "scientific_ratings": 0}


def runtime_paths(root):
    """Use the launcher's complete maintained execution scan, including ignored files."""
    fixed = {rounds.PROTOCOL, rounds.COHORT, "docs/record-review-profile.md",
             "scripts/adhoc/calibration_round_20261116.py"}
    execution = {item["path"] for item in worker.execution_inventory(root)}
    return (rounds.RUNTIME_PATHS | execution) - fixed


def assemble():
    check_canary()
    check_producer_canary()
    rounds.require(not (ROOT / PACKAGE).exists(), "Package output exists")
    old = retained()
    _, cohort = rounds.baseline(ROOT)
    files, cases, id_map, guide = {}, {}, {}, []

    def add(path, role, **extra):
        pin = {"path": str(path), "role": role, **extra}
        if str(path) in files:
            rounds.require(files[str(path)] == pin, "Conflicting package declaration")
        files[str(path)] = pin

    for case in cohort["cases"]:
        cid = case["case_id"]
        original_path = f".temp/edge-calibration-20261115/{cid}"
        for name in ("packet.json", "source.json", "occurrence.json"):
            rel = f"{original_path}/{name}"
            old_pin = next(p for p in old["files"] if p["path"] == rel)
            persist(Path(rel), source(old_pin))
            add(rel, "packet" if name == "packet.json" else "original_input",
                visibility="mechanical_replay_only",
                **({"evidence_ids": [f"packet-{cid}"]} if name == "packet.json" else {}))
        cases[cid] = {"case_id": cid, "packet_path": f"{original_path}/packet.json",
                      "reviewer_view_path": str(PACKAGE / "cases" / cid / "view.json"),
                      "evidence_ids": [f"packet-{cid}"]}

    # The existing current-runtime preparation is not replaced. New view receipts
    # are separate artifacts bound to current configuration and original bytes.
    for cid in ["fresh-47", *[c for c in cases if c != "fresh-47"]]:
        views.prepare(cid, ROOT / PACKAGE / "cases")
        add(PACKAGE / "cases" / cid / "view.json", "reviewer_view")
        add(PACKAGE / "cases" / cid / "receipt.json", "view_receipt",
            visibility="mechanical_replay_only")

    for number, pin in enumerate((p for p in old["files"]
                                   if p["role"] in {"authority", "evidence"}), 1):
        raw = source(pin)
        eid = f"r03-evidence-{number:03d}"
        for prior_id in pin["evidence_ids"]:
            id_map[prior_id] = eid
        full_path = PRIVATE / (pin["sha256"] + Path(pin["path"]).suffix)
        persist(full_path, raw)
        add(full_path, "private_original", visibility="mechanical_replay_only")
        view, receipt = bounded(raw, pin["path"]) if pin["role"] == "authority" else (
            raw, {"policy": "whole_primary_response", "source_sha256": rounds.digest(raw),
                  "view_sha256": rounds.digest(raw), "spans": [{"source_byte_start": 0,
                  "source_byte_end": len(raw), "view_byte_start": 0,
                  "view_byte_end": len(raw), "sha256": rounds.digest(raw)}],
                  "offset_encoding": "UTF-8 bytes; zero-based half-open"})
        path = PACKAGE / "evidence" / (eid + (".txt" if pin["role"] == "authority"
                                                     else Path(pin["path"]).suffix))
        persist(path, view)
        receipt.update(version=pin.get("version"), original_path=str(full_path),
                       evidence_id=eid, helper_sha256=rounds.digest(Path(__file__).read_bytes()))
        receipt_path = PACKAGE / "receipts" / (eid + ".json")
        persist(receipt_path, encoded(receipt))
        add(path, pin["role"], evidence_ids=[eid],
            **({"version": pin["version"]} if "version" in pin else {}))
        add(receipt_path, "bounded_view_receipt", visibility="mechanical_replay_only")
        guide.append({"evidence_id": eid, "path": str(path), "role": pin["role"],
                      "version": pin.get("version"), "source_sha256": pin["sha256"],
                      "view_sha256": rounds.digest(view), "policy": receipt["policy"],
                      "source_name": Path(pin["path"]).name,
                      "receipt": str(receipt_path),
                      "scope": "Producer convention stated in KG-Microbe PREGO documentation; "
                      "not an ontology definition or an exception automatically applicable to "
                      "other transforms." if pin["sha256"] == PREGO_SHA else
                      "Source-native text or operative code at the stated version."})

    for old_case in old["cases"]:
        for old_id in old_case["evidence_ids"]:
            if old_id in id_map and id_map[old_id] not in cases[old_case["case_id"]]["evidence_ids"]:
                cases[old_case["case_id"]]["evidence_ids"].append(id_map[old_id])

    replay_raw = (ROOT / REPLAY / "replay.json").read_bytes()
    rounds.require(rounds.digest(replay_raw) == REPLAY_SHA, "Owner replay changed")
    replay = json.loads(replay_raw)
    persist(PRIVATE / "owner-replay.json", replay_raw)
    add(PRIVATE / "owner-replay.json", "private_original", visibility="mechanical_replay_only")
    for number, (name, pin) in enumerate(sorted(replay["artifact_pins"].items()), 1):
        raw = (ROOT / REPLAY / name).read_bytes()
        rounds.require(rounds.digest(raw) == pin["sha256"], "Replay witness changed")
        eid = f"r03-owner-{number:03d}"
        full_path = PRIVATE / (pin["sha256"] + Path(name).suffix)
        persist(full_path, raw)
        add(full_path, "private_original", visibility="mechanical_replay_only")
        view, receipt = bounded(raw, name)
        path = PACKAGE / "evidence" / (eid + ".txt")
        persist(path, view)
        version = ("KG-Microbe d6baf5b90003a2032747559d94c00f86a7a4c615; "
                   "bounded owner-method replay 2026-11-16; historical dirty build not established")
        receipt.update(version=version, original_path=str(full_path), evidence_id=eid,
                       replay_sha256=REPLAY_SHA)
        rp = PACKAGE / "receipts" / (eid + ".json")
        persist(rp, encoded(receipt))
        citable = name in {"owner-metatraits.py", "owner-metatraits-gtdb.py",
                           "metpo-target-node.json"}
        role = "authority" if citable else "source_witness"
        add(path, role, version=version, **({"evidence_ids": [eid]} if citable else {}))
        add(rp, "bounded_view_receipt", visibility="mechanical_replay_only")
        if citable:
            cases["first-30"]["evidence_ids"].append(eid)
        guide.append({"evidence_id": eid if citable else None, "path": str(path), "role": role,
                      "version": version, "source_name": name,
                      "source_sha256": pin["sha256"], "view_sha256": rounds.digest(view),
                      "policy": receipt["policy"], "receipt": str(rp),
                      "scope": "Code/ontology witness" if citable else
                      "Source-binding context; cite original packet, not as independent authority"})

    replay_fields = ("actual_method_output", "parsed_values", "summaries", "producer_history",
                     "source_tax_name", "raw_line", "transform_data_row", "transform_physical_line",
                     "ontology_mapping", "limits", "runtime", "occurrence_id", "helper_sha256")
    replay_view = {key: replay[key] for key in replay_fields}
    replay_view["source_receipt_sha256"] = REPLAY_SHA
    replay_view["input_pins"] = {
        key: {field: pin[field] for field in ("sha256", "bytes")}
        for key, pin in replay["input_pins"].items()
    }
    replay_view["artifact_pins"] = {
        key: {field: pin[field] for field in ("sha256", "bytes")}
        for key, pin in replay["artifact_pins"].items()
    }
    replay_view["packet_pins"] = {
        key: {field: pin[field] for field in ("sha256", "bytes")}
        for key, pin in replay["packet_pins"].items()
    }
    replay_view["evidence_scope"] = (
        "Technical method-replay witness for source_fidelity; not independent identity, "
        "definition, paper, experimental or biological evidence. Constructor, taxonomy resolver, "
        "writer and historical dirty build were not executed."
    )
    path = PACKAGE / "owner-method-result.json"
    persist(path, encoded(replay_view))
    replay_id = "r03-owner-method-result"
    replay_version = "receipt " + REPLAY_SHA + "; helper " + replay["helper_sha256"]
    add(path, "authority", version=replay_version, evidence_ids=[replay_id])
    cases["first-30"]["evidence_ids"].append(replay_id)
    replay_receipt = PACKAGE / "receipts" / "owner-method-result.json"
    persist(replay_receipt, encoded({
        "policy": "allowlisted_json_projection", "source_sha256": REPLAY_SHA,
        "view_sha256": rounds.digest(encoded(replay_view)),
        "original_path": str(PRIVATE / "owner-replay.json"), "version": replay_version,
        "fields": list(replay_fields), "pin_groups": ["input_pins", "artifact_pins", "packet_pins"],
        "evidence_scope": replay_view["evidence_scope"],
    }))
    add(replay_receipt, "bounded_view_receipt", visibility="mechanical_replay_only")
    guide.append({"evidence_id": replay_id, "path": str(path), "role": "authority",
                  "version": replay_version, "source_name": "owner-method-replay.json",
                  "source_sha256": REPLAY_SHA, "view_sha256": rounds.digest(encoded(replay_view)),
                  "policy": "allowlisted_json_projection", "receipt": str(replay_receipt),
                  "scope": replay_view["evidence_scope"]})

    profile = views.blinded_profile((ROOT / "docs/record-review-profile.md").read_text())
    persist(PACKAGE / "profile-for-reviewers.md", profile.encode())
    add(PACKAGE / "profile-for-reviewers.md", "instructions")
    for path in ("scripts/adhoc/m5_review_20261116/round03-blinded-review.md",
                 "scripts/adhoc/m5_review_20261116/round03-neutral-rubric.md",
                 "scripts/adhoc/m5_review_20261116/round03-authoring.md",
                 "docs/record-reviews.md"):
        rounds.safe(ROOT, path)
        add(path, "instructions")
    runtime = runtime_paths(ROOT)
    for path in sorted(runtime):
        rounds.safe(ROOT, path)
        add(path, "proof_adapter")
    navigation = {"round_id": PACKAGE_ID, "inputs": guide,
                  "cases": list(cases.values()), "inseparable_exposure": EXPOSURE,
                  "navigation_policy": "Read only case view paths and evidence paths here. "
                  "Receipt/original paths are mechanical replay inputs. Do not follow source links, "
                  "read repository history, old reports or other private directories.",
                  "owner_method_result": str(PACKAGE / "owner-method-result.json"),
                  "source_version_limits": "Current authority/producer versions do not establish "
                  "the complete sampled dirty build. A source report is not a biological result.",
                  "scientific_ratings": 0}
    persist(PACKAGE / "evidence-guide.json", encoded(navigation))
    add(PACKAGE / "evidence-guide.json", "instructions")
    config = {"round_id": navigation["round_id"], "files": list(files.values()),
              "cases": list(cases.values())}
    persist(PACKAGE / "freeze-config.json", encoded(config))
    persist(PRIVATE / "historical-evidence-id-map.json", encoded(id_map))
    return {"config": str(PACKAGE / "freeze-config.json"), "cases": len(cases),
            "files": len(files), "scientific_ratings": 0, "frozen": False}


def verify_views():
    """Replay every bounded derivative against its retained full original."""
    config = rounds.read(ROOT, str(PACKAGE / "freeze-config.json"))
    guide = rounds.read(ROOT, str(PACKAGE / "evidence-guide.json"))
    paths = {p["path"] for p in config["files"]}
    for item in guide["inputs"]:
        rounds.require(item["path"] in paths and item["receipt"] in paths, "Unpinned view")
        receipt = rounds.read(ROOT, item["receipt"])
        rounds.require(receipt["original_path"] in paths, "Unpinned private original")
        raw = rounds.safe(ROOT, receipt["original_path"]).read_bytes()
        view = rounds.safe(ROOT, item["path"]).read_bytes()
        rounds.require(rounds.digest(raw) == receipt["source_sha256"] == item["source_sha256"],
                       "Source bytes changed")
        rounds.require(rounds.digest(view) == receipt["view_sha256"] == item["view_sha256"],
                       "View bytes changed")
        if rounds.digest(raw) == PRODUCER_SHA or item.get("source_name") == PRODUCER_NAME:
            expected_view, expected_receipt = bounded(raw, item["source_name"])
            rounds.require(receipt.get("version") == item.get("version") == PRODUCER_VERSION,
                           "Producer version changed")
            rounds.require(view == expected_view and all(
                receipt.get(key) == expected_receipt[key]
                for key in ("policy", "spans", "reviewed_content_omissions",
                            "source_sha256", "view_sha256", "offset_encoding", "span_separator")),
                "Reviewed producer omission changed")
        if receipt["policy"] == "allowlisted_json_projection":
            source_value, view_value = json.loads(raw), json.loads(view)
            expected = {key: source_value[key] for key in receipt["fields"]}
            for group in receipt["pin_groups"]:
                expected[group] = {key: {field: pin[field] for field in ("sha256", "bytes")}
                                   for key, pin in source_value[group].items()}
            expected["source_receipt_sha256"] = receipt["source_sha256"]
            expected["evidence_scope"] = receipt["evidence_scope"]
            rounds.require(expected == view_value, "Owner replay projection changed")
            continue
        cursor = 0
        for span in receipt["spans"]:
            start, end = span["source_byte_start"], span["source_byte_end"]
            first, last = span["view_byte_start"], span["view_byte_end"]
            rounds.require(0 <= start < end <= len(raw), "Invalid source span")
            rounds.require(0 <= first < last <= len(view), "Invalid view span")
            expected_gap = b"" if cursor == 0 else b"\n\n"
            rounds.require(view[cursor:first] == expected_gap, "Unbound derivative text")
            rounds.require(raw[start:end] == view[first:last]
                           and rounds.digest(raw[start:end]) == span["sha256"], "Span differs")
            cursor = last
        rounds.require(cursor == len(view), "Unbound derivative tail")
    return {"bounded_views_verified": len(guide["inputs"]), "scientific_ratings": 0,
            "scope": "Exact derivative replay; semantic blinding requires independent inspection"}


def producer_pin():
    pins = [p for p in retained()["files"] if p["sha256"] == PRODUCER_SHA]
    rounds.require(len(pins) == 1, "Producer input is not unique")
    pin = pins[0]
    rounds.require(pin.get("role") == "authority" and pin.get("version") == PRODUCER_VERSION
                   and Path(pin["path"]).name == PRODUCER_NAME, "Producer identity/version changed")
    return pin


def producer_canary():
    """Canary the actual affected input through the same bounded assembly path."""
    rounds.require(not (ROOT / PRODUCER_CANARY).exists(), "Producer canary output exists")
    pin = producer_pin()
    raw = source(pin)
    view, receipt = bounded(raw, pin["path"])
    persist(PRODUCER_CANARY / "source.py", raw)
    persist(PRODUCER_CANARY / "view.txt", view)
    receipt.update(version=pin["version"], source_path=pin["path"],
                   package_id=PACKAGE_ID, helper_sha256=rounds.digest(Path(__file__).read_bytes()))
    persist(PRODUCER_CANARY / "receipt.json", encoded(receipt))
    return check_producer_canary()


def check_producer_canary():
    receipt = rounds.read(ROOT, str(PRODUCER_CANARY / "receipt.json"))
    pin = producer_pin()
    raw = source(pin)
    view, expected = bounded(raw, pin["path"])
    expected.update(version=pin["version"], source_path=pin["path"],
                    package_id=PACKAGE_ID, helper_sha256=rounds.digest(Path(__file__).read_bytes()))
    rounds.require(receipt == expected, "Producer canary configuration changed")
    rounds.require((ROOT / PRODUCER_CANARY / "source.py").read_bytes() == raw
                   and (ROOT / PRODUCER_CANARY / "view.txt").read_bytes() == view,
                   "Persisted producer canary changed")
    return {"receipt": str(PRODUCER_CANARY / "receipt.json"), "source_sha256": PRODUCER_SHA,
            "view_sha256": rounds.digest(view), "version": PRODUCER_VERSION,
            "helper_sha256": expected["helper_sha256"], "package_id": PACKAGE_ID,
            "scientific_ratings": 0,
            "scope": "Literal derivative replay; independent content/navigation review required"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("canary", "check-canary", "producer-canary",
                                             "check-producer-canary", "assemble", "verify-views"))
    args = parser.parse_args()
    print(json.dumps({"canary": canary, "check-canary": check_canary,
                      "producer-canary": producer_canary,
                      "check-producer-canary": check_producer_canary,
                      "assemble": assemble, "verify-views": verify_views}[args.operation](),
                     sort_keys=True))


if __name__ == "__main__":
    main()
