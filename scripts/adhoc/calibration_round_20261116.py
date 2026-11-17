#!/usr/bin/env python3
"""Freeze evidence inputs and initial matrices; count the preregistered calibration.

This helper never authors assessments or grants a scientific calibration pass.
Hash/packet replay and initial agreement precede independent evidence adjudication,
canonical review persistence and proof replay. Those gates remain explicitly pending.
All input/output paths are repository relative; outputs are exclusive and read-only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).absolute().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from edgemech.occurrence_packet import validate_packet  # noqa: E402
from edgemech.occurrence_review import CATEGORIES, DETAILS  # noqa: E402

PROTOCOL = "artifacts/edge-calibration-20261115/protocol.json"
COHORT = "artifacts/edge-calibration-20261115/cohort.json"
PINS = {
    PROTOCOL: "d24b9e1e9833d70407bf06a04ae6c0ff92f5564149a3b51e6402e5416e866517",
    COHORT: "1dc756b0ba628756baf544cacf36f0a1ab2e4c68eed6724ee281205f22d606ee",
}
SCHEMA = "edgemech-calibration-round/v1"
RUNTIME_PATHS = {
    "src/edgemech/occurrence_packet.py", "src/edgemech/occurrence_review.py",
    "src/edgemech/literature_cache.py", "src/edgemech/contract-pins.json",
    "src/edgemech/storage/parquet.py", "src/edgemech/pins.py", "uv.lock",
    "schema/record_review.yaml",
}
MODEL_AXES = ("relation", "subject_node", "object_node")
VIEW_FIELDS = {"occurrence_id", "original_assertion", "endpoints", "measurement_context",
               "source_records"}
RESOLVED = {
    "claim": {"SUPPORTED_AS_STATED", "CONTRADICTED_AS_STATED", "CONFLICTING_EVIDENCE"},
    "source_fidelity": {"SUPPORTED", "CONTRADICTED"},
    **{axis: {"CORRECT", "INCORRECT"} for axis in MODEL_AXES},
}


def require(value, message):
    if not value:
        raise ValueError(message)


def text(value, name):
    require(isinstance(value, str) and bool(value.strip()), f"Missing {name}")
    return value


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def safe(root, relative, *, exists=True):
    text(relative, "repository-relative path")
    path = Path(relative)
    require(not path.is_absolute() and ".." not in path.parts, "Unsafe relative path")
    target = root / path
    require(not any(p.is_symlink() for p in (target, *target.parents)), "Symlink path")
    require(target.resolve().is_relative_to(root.resolve()), "Path escapes root")
    if exists:
        require(target.is_file(), f"Missing input: {relative}")
    return target


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def read(root, path):
    return json.loads(safe(root, path).read_bytes(), object_pairs_hook=unique_object)


def write(root, path, value=None, *, raw=None):
    target = safe(root, path, exists=False)
    target.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    payload = raw if raw is not None else (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
    descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    target.chmod(0o400)
    return digest(payload)


def baseline(root):
    for path, sha in PINS.items():
        require(digest(safe(root, path).read_bytes()) == sha, "Preregistered baseline changed")
    return read(root, PROTOCOL), read(root, COHORT)


def packet_scope(packet, original):
    require(packet["original_assertion"] == original["original_assertion"],
            "Packet original assertion differs from cohort")
    for side in ("subject", "object"):
        require(packet["endpoints"][side]["record_sha256"]
                == original["endpoints"][side]["private_record_sha256"],
                "Packet endpoint differs from cohort")


def reviewer_view(root, case, packet, paths):
    if "reviewer_view_path" not in case:
        return
    require(case["reviewer_view_path"] in paths, "Unpinned reviewer view")
    view = read(root, case["reviewer_view_path"])
    if "blinding" in view:
        from prepare_m5_round02_views_20261116 import HELPER, VERSION, projection
        require(HELPER in paths and
                "scripts/adhoc/prepare_m5_reviewer_views_20261116.py" in paths,
                "Unpinned blinding adapters")
        require(view["blinding"].get("version") == VERSION and view == projection(packet),
                "Reviewer view differs from the versioned blinded projection")
        return
    require(view == {key: packet[key] for key in VIEW_FIELDS},
            "Reviewer view must be the exact allowlisted packet projection")


def freeze(root, config_path, output):
    protocol, cohort = baseline(root)
    config = read(root, config_path)
    text(config.get("round_id"), "round_id")
    declared = config["files"]
    require(isinstance(declared, list), "Files must be a list")
    fixed = [{"path": path, "role": role} for path, role in (
        (PROTOCOL, "protocol"), (COHORT, "cohort"),
        ("docs/record-review-profile.md", "profile"),
        ("scripts/adhoc/calibration_round_20261116.py", "round_helper"))]
    files, paths, evidence = [], set(), set()
    for item in [*fixed, *declared]:
        path, role = item["path"], text(item.get("role"), "file role")
        require(path not in paths, f"Repeated input: {path}")
        paths.add(path)
        if role == "authority":
            text(item.get("version"), "authority version")
        ids = item.get("evidence_ids", [])
        require(isinstance(ids, list), "evidence_ids must be a list")
        for eid in ids:
            text(eid, "evidence ID")
            require(eid not in evidence, "Evidence ID binds more than one input")
            evidence.add(eid)
        files.append({**item, "sha256": digest(safe(root, path).read_bytes())})
    require({"instructions", "proof_adapter", "authority", "evidence"}
            <= {item["role"] for item in files}, "Incomplete common evidence package")
    require(RUNTIME_PATHS <= paths,
            "Missing required adapter/runtime pins: " + ", ".join(sorted(RUNTIME_PATHS - paths)))
    originals = {case["case_id"]: case for case in cohort["cases"]}
    cases, seen = [], set()
    for case in config["cases"]:
        case_id = case["case_id"]
        require(case_id in originals and case_id not in seen, "Unknown/repeated case")
        seen.add(case_id)
        packet_path = case["packet_path"]
        require(packet_path in paths, "Unpinned case packet")
        packet = read(root, packet_path)
        require(packet["occurrence_id"] == originals[case_id]["occurrence_id"],
                "Packet is not the original occurrence")
        packet_scope(packet, originals[case_id])
        reviewer_view(root, case, packet, paths)
        for pin in packet["inputs"].values():
            require(pin["path"] in paths, "Unpinned packet input")
            require(digest(safe(root, pin["path"]).read_bytes()) == pin["sha256"],
                    "Packet input changed")
        ids = case["evidence_ids"]
        require(isinstance(ids, list) and len(ids) == len(set(ids)) and set(ids) <= evidence,
                "Invalid case evidence IDs")
        original = originals[case_id]
        cases.append({"case_id": case_id, "occurrence_id": original["occurrence_id"],
                      "original_assertion": original["original_assertion"],
                      "endpoints": original["endpoints"], "packet_path": packet_path,
                      "evidence_ids": ids})
        if "reviewer_view_path" in case:
            cases[-1]["reviewer_view_path"] = case["reviewer_view_path"]
    require(seen == originals.keys(), "Every original case is required")
    manifest = {"schema": SCHEMA, "round_id": config["round_id"],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "cohort_id": protocol["cohort_id"], "files": files, "cases": cases,
                "scientific_status": "unassessed", "thresholds_changed": False,
                "scope": "input_freeze_not_evidence_entailment_or_calibration_pass"}
    return {"manifest_sha256": write(root, output, manifest), "path": output}


def verify(root, manifest_path, case_id=None):
    _, cohort = baseline(root)
    manifest = read(root, manifest_path)
    require(manifest.get("schema") == SCHEMA, "Invalid round manifest")
    originals = {c["case_id"]: c for c in cohort["cases"]}
    require(len(manifest["cases"]) == len(originals), "Missing/repeated manifest case")
    require({c["case_id"] for c in manifest["cases"]} == originals.keys(), "Cohort changed")
    paths = [item["path"] for item in manifest["files"]]
    require(len(paths) == len(set(paths)) and set(PINS) <= set(paths), "Invalid input pins")
    require(RUNTIME_PATHS <= set(paths),
            "Missing required adapter/runtime pins: "
            + ", ".join(sorted(RUNTIME_PATHS - set(paths))))
    for pin in manifest["files"]:
        require(digest(safe(root, pin["path"]).read_bytes()) == pin["sha256"],
                f"Pinned input changed: {pin['path']}")
    if case_id is not None:
        require(case_id in originals, "Unknown canary case")
    results = []
    for case in manifest["cases"]:
        original = originals[case["case_id"]]
        for key in ("occurrence_id", "original_assertion", "endpoints"):
            require(case[key] == original[key], f"Original {key} changed")
        require(case["packet_path"] in paths, "Unpinned packet")
        if case_id is not None and case["case_id"] != case_id:
            continue
        packet = read(root, case["packet_path"])
        require(packet["occurrence_id"] == case["occurrence_id"], "Wrong packet occurrence")
        packet_scope(packet, original)
        reviewer_view(root, case, packet, paths)
        require(all(pin["path"] in paths for pin in packet["inputs"].values()),
                "Unpinned packet input")
        results.append({"case_id": case["case_id"], **validate_packet(packet, root=root)})
    return {"manifest_sha256": digest(safe(root, manifest_path).read_bytes()),
            "input_hashes_verified": len(paths), "packet_replay": results,
            "scope": "input_and_packet_replay_only_not_proof_replay_or_entailment"}


def validate_assertion_basis(assessment):
    """Keep original report scope and every witness role explicit before sealing."""
    axis, category = assessment["axis"], assessment["category"]
    basis = assessment.get("assertion_basis", "independent")
    require(basis in {"independent", "source_report"}, "Invalid assertion basis")
    require(axis == "claim" or not {"assertion_basis", "report_witnesses"} & assessment.keys(),
            "Assertion fields belong only to the claim axis")
    witnesses = assessment.get("report_witnesses")
    if basis == "source_report":
        require(isinstance(witnesses, dict)
                and witnesses.get("scope") == assessment["dimensions"]["assertion_scope"],
                "Source-report scope must bind the original authored assertion")
        for group in ("source_instance_evidence_ids", "identity_evidence_ids", "definition_evidence_ids"):
            group_ids = witnesses.get(group)
            require(isinstance(group_ids, list)
                    and all(isinstance(eid, str) for eid in group_ids)
                    and len(group_ids) == len(set(group_ids))
                    and set(group_ids) <= set(assessment["evidence_ids"]),
                    "Report witnesses must belong to their axis evidence set")
            if category in RESOLVED["claim"]:
                require(group_ids, "Resolved report lacks required witness group")
    else:
        require(witnesses is None, "Report witnesses require source_report assertion basis")


def validate_matrix(root, manifest_path, matrix):
    manifest = read(root, manifest_path)
    require(matrix["round_id"] == manifest["round_id"], "Wrong matrix round")
    require(matrix["package_sha256"] == digest(safe(root, manifest_path).read_bytes()),
            "Matrix used another package")
    reviewer = matrix["reviewer"]
    for name in ("id", "model", "session_id", "historical_exposure"):
        text(reviewer.get(name), "reviewer " + name)
    require(reviewer["model"] not in {"unknown", "configured_default"}, "Actual model required")
    cases = {case["case_id"]: case for case in manifest["cases"]}
    seen, categories = set(), {}
    for case in matrix["cases"]:
        cid = case["case_id"]
        require(cid in cases and cid not in seen, "Unknown/repeated matrix case")
        seen.add(cid)
        require(case["occurrence_id"] == cases[cid]["occurrence_id"], "Wrong occurrence scope")
        axes = {}
        for assessment in case["assessments"]:
            axis, category = assessment["axis"], assessment["category"]
            require(axis in CATEGORIES and axis not in axes, "Unknown/repeated matrix axis")
            require(category in CATEGORIES[axis] and category != "UNASSESSED", "Invalid category")
            for name in ("scope", "rationale"):
                text(assessment.get(name), name)
            dimensions = assessment["dimensions"]
            require(isinstance(dimensions, dict) and DETAILS[axis] <= dimensions.keys(),
                    f"Missing {axis} dimensions")
            for name in DETAILS[axis]:
                text(dimensions[name], name)
            ids = assessment["evidence_ids"]
            require(isinstance(ids, list) and len(ids) == len(set(ids))
                    and set(ids) <= set(cases[cid]["evidence_ids"]), "Unbound evidence ID")
            validate_assertion_basis(assessment)
            if category in RESOLVED.get(axis, set()) or category in {"SUPPORTS", "REFUTES", "CONFLICTING", "PARTIAL"}:
                require(ids, "Resolved/partial assessment lacks evidence")
            axes[axis] = category
        require(axes.keys() == CATEGORIES.keys(), "All six axes required")
        categories[cid] = axes
    require(seen == cases.keys(), "All ten cases required")
    return categories


def save_matrix(root, manifest_path, matrix_path, output):
    verify(root, manifest_path)
    matrix = read(root, matrix_path)
    validate_matrix(root, manifest_path, matrix)
    receipt_path = output + ".receipt.json"
    require(not safe(root, receipt_path, exists=False).exists(), "Receipt already exists")
    sha = write(root, output, raw=safe(root, matrix_path).read_bytes())
    receipt = {"schema": SCHEMA, "matrix_path": output, "matrix_sha256": sha,
               "package_sha256": matrix["package_sha256"],
               "saved_at": datetime.now(timezone.utc).isoformat(),
               "reviewer": matrix["reviewer"], "scope": "immutable_initial_matrix_not_canonical_review"}
    write(root, receipt_path, receipt)
    return receipt


def sealed_matrix(root, manifest_path, path):
    receipt = read(root, path + ".receipt.json")
    require(receipt["matrix_path"] == path
            and receipt["matrix_sha256"] == digest(safe(root, path).read_bytes()),
            "Initial matrix changed after saving")
    matrix = read(root, path)
    require(receipt["package_sha256"] == matrix["package_sha256"]
            and receipt["reviewer"] == matrix["reviewer"], "Matrix receipt differs")
    return matrix, validate_matrix(root, manifest_path, matrix)


def compare(root, manifest_path, reviewer_a, reviewer_b):
    replay = verify(root, manifest_path)
    protocol, _ = baseline(root)
    left, a = sealed_matrix(root, manifest_path, reviewer_a)
    right, b = sealed_matrix(root, manifest_path, reviewer_b)
    require(left["reviewer"]["id"] != right["reviewer"]["id"], "Repeated reviewer")
    require(left["reviewer"]["session_id"] != right["reviewer"]["session_id"], "Repeated session")
    thresholds = protocol["thresholds"]
    tables, disagreements, per_axis = {}, [], {}
    for axis in protocol["axes"]:
        cells = Counter((a[cid][axis], b[cid][axis]) for cid in a)
        tables[axis] = [{"reviewer_a": x, "reviewer_b": y, "count": n}
                        for (x, y), n in sorted(cells.items())]
        per_axis[axis] = sum(a[cid][axis] == b[cid][axis] for cid in a)
        disagreements.extend({"case_id": cid, "axis": axis, "reviewer_a": a[cid][axis],
                              "reviewer_b": b[cid][axis], "disposition": "pending_adjudication"}
                             for cid in a if a[cid][axis] != b[cid][axis])
    def gate(value, rule):
        return {"numerator": value, "denominator": rule["denominator"],
                "minimum": rule["minimum"], "passed": value >= rule["minimum"]}
    initial = {
        "packets_replayed": gate(len(replay["packet_replay"]), thresholds["packets_replayed"]),
        "endpoint_roles_retained": gate(sum(r["endpoint_records_verified"] for r in replay["packet_replay"]), thresholds["endpoint_roles_retained"]),
        "initial_exact_category_agreement": gate(sum(per_axis.values()), thresholds["initial_exact_category_agreement"]),
        "initial_per_axis_agreement": {axis: gate(n, thresholds["initial_per_axis_agreement"])
                                       for axis, n in per_axis.items()},
        "initial_claim_agreement": gate(per_axis["claim"], thresholds["initial_claim_agreement"]),
    }
    resolutions, literature = {}, {}
    applicable = protocol["experimental_literature"]["applicable_case_ids"]
    for matrix, labels in ((left, a), (right, b)):
        rid = matrix["reviewer"]["id"]
        resolutions[rid] = {axis: {"numerator": sum(row[axis] in values for row in labels.values()),
                                  "denominator": 10} for axis, values in RESOLVED.items()}
        literature[rid] = {"all_ten": {cid: row["literature"] for cid, row in labels.items()},
                           "experimental_denominator": 7,
                           "exact_directional": sum(labels[cid]["literature"] in
                                                    {"SUPPORTS", "REFUTES", "CONFLICTING"}
                                                    for cid in applicable)}
    critical = {}
    for category in sorted(RESOLVED["claim"]):
        critical["unsupported " + category] = {"emitted_labels": sum(row["claim"] == category for labels in (a, b) for row in labels.values()), "unsupported_labels": None, "status": "pending_independent_audit"}
    for category in ("CORRECT", "INCORRECT"):
        critical["unsupported " + category + " model judgment"] = {"emitted_labels": sum(row[axis] == category for labels in (a, b) for row in labels.values() for axis in MODEL_AXES), "unsupported_labels": None, "status": "pending_independent_audit"}
    for item in critical.values():
        if item["emitted_labels"] == 0:
            item["status"] = "untested_label_class"
    passed = all(item["passed"] for key, item in initial.items() if key != "initial_per_axis_agreement") and all(item["passed"] for item in initial["initial_per_axis_agreement"].values())
    pending = {key: {"status": "pending_independent_adjudication_and_canonical_replay",
                     "preregistered_requirement": thresholds[key]}
               for key in ("final_authored_axes", "evidence_replay", "resolved_claims",
                           "resolved_source_fidelity", "resolved_modeling_per_axis",
                           "exact_paper_backed_directional_claims",
                           "exact_authority_backed_incorrect_model_judgments")}
    return {"schema": SCHEMA, "round_id": left["round_id"],
            "package_sha256": left["package_sha256"],
            "matrices": [{"path": path, "sha256": digest(safe(root, path).read_bytes())}
                         for path in (reviewer_a, reviewer_b)],
            "reviewers": [left["reviewer"], right["reviewer"]],
            "same_model": left["reviewer"]["model"] == right["reviewer"]["model"],
            "interpretation": "Operational agreement only; no independent expert validation inferred.",
            "initial_confusion_tables": tables, "initial_gates": initial,
            "initial_resolution_counts_not_final_gates": resolutions,
            "literature_counts": literature, "critical_errors": critical,
            "disagreements": disagreements, "remaining_gates": pending,
            "disagreement_gate": {"status": "pending_adjudication"},
            "scientific_calibration_passed": False,
            "status": "pending_adjudication" if passed else "failed_initial_gate",
            "remaining_90_authorized_by_result": False, "expansion_authorized": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    sub = parser.add_subparsers(dest="command", required=True)
    frozen = sub.add_parser("freeze")
    frozen.add_argument("--config", required=True)
    frozen.add_argument("--output", required=True)
    check = sub.add_parser("verify")
    check.add_argument("--manifest", required=True)
    check.add_argument("--case")
    check.add_argument("--output")
    save = sub.add_parser("save-matrix")
    save.add_argument("--manifest", required=True)
    save.add_argument("--matrix", required=True)
    save.add_argument("--output", required=True)
    comparison = sub.add_parser("compare")
    comparison.add_argument("--manifest", required=True)
    comparison.add_argument("--reviewer-a", required=True)
    comparison.add_argument("--reviewer-b", required=True)
    comparison.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        if args.command == "freeze":
            result = freeze(args.root, args.config, args.output)
        elif args.command == "verify":
            result = verify(args.root, args.manifest, args.case)
            if args.output:
                write(args.root, args.output, result)
        elif args.command == "save-matrix":
            result = save_matrix(args.root, args.manifest, args.matrix, args.output)
        else:
            result = compare(args.root, args.manifest, args.reviewer_a, args.reviewer_b)
            write(args.root, args.output, result)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(f"Calibration accounting failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
