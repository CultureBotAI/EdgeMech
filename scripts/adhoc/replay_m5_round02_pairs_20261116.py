#!/usr/bin/env python3
"""Inventory/replay the fixed twenty round02 canonical pairs without authoring ratings.

Config: package_sha256, manifest, runtime_git_revision, reviewers keyed a/b with
root, matrix and canonical_identity; entries has reviewer/case_id/input/proofs/
review for every original case (null paths retain missing outputs). Python is
optional per reviewer and defaults to its root/.venv/bin/python.
Run canary for one saved fresh-47, inspect check-canary, then batch with the same
config and canary directory. All outputs are exclusive private metadata/receipts;
input reviews, matrices, proofs and sources are read-only. No scientific pass.
For failed rounds, input-canary/input-batch replay authored drafts through the
production validate command. This separate path never satisfies canonical gates.

Evidence adaptation is mechanical: an exact proof input path+SHA must name a
frozen manifest file. Its declared source IDs are intersected with the initial
axis's evidence IDs. A valid explicit manifest_evidence_id or matching canonical
ID selects that identity; otherwise exactly one candidate is required. Multiple
quotation proofs may map to one source. Ambiguous or unmapped links fail parity,
without invalidating a separately successful production pair replay.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import calibration_round_20261116 as rounds
from kg_microbe_reviews import load_document

SCHEMA = "edgemech-round02-canonical-replay/v1"
ROOT = Path(__file__).absolute().parents[2]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def write(path, value=None, raw=None):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    data = encoded(value) if raw is None else raw
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    require(path.read_bytes() == data, "Persisted replay artifact differs")
    return {"path": str(path.absolute()), "sha256": sha(data)}


def pin(root, relative):
    path = rounds.safe(root, relative)
    raw = path.read_bytes()
    return raw, {"root": str(root), "path": relative, "sha256": sha(raw), "bytes": len(raw)}


def command(root, argv, out):
    """Fixed argv only; raw command output remains private, metadata contains hashes."""
    result = subprocess.run(argv, cwd=root, capture_output=True, check=False,
                            env={**os.environ, "PYTHONPATH": str(root / "src"),
                                 "PYTHONDONTWRITEBYTECODE": "1"})
    stdout = write(out / "stdout.log", raw=result.stdout)
    stderr = write(out / "stderr.log", raw=result.stderr)
    receipt = {"argv": argv, "cwd": str(root), "exit_code": result.returncode,
               "stdout": stdout, "stderr": stderr}
    receipt_pin = write(out / "command.json", receipt)
    return {**receipt, "receipt": receipt_pin}, result.stdout


def expected_entries(config):
    _, cohort = rounds.baseline(ROOT)
    cases = {c["case_id"]: c for c in cohort["cases"]}
    require(set(config["reviewers"]) == {"reviewer-a", "reviewer-b"}, "Two expected reviewers required")
    entries = config["entries"]
    keys = [(e["reviewer"], e["case_id"]) for e in entries]
    expected = {(r, c) for r in config["reviewers"] for c in cases}
    require(len(keys) == 20 and len(set(keys)) == 20 and set(keys) == expected,
            "Exactly twenty original reviewer/case entries required, including missing/failed outputs")
    require(all(set(e) >= {"reviewer", "case_id", "input", "proofs", "review"} for e in entries),
            "Each expected entry must declare input/proofs/review, using null for missing paths")
    roots = [str(Path(r["root"]).resolve()) for r in config["reviewers"].values()]
    require(len(set(roots)) == 2, "Reviewers must retain separate original clone roots")
    require(len({r.get("canonical_identity") for r in config["reviewers"].values()}) == 2,
            "Expected canonical reviewer identities must be distinct")
    return cases, sorted(entries, key=lambda e: (e["reviewer"], e["case_id"]))


def duplicates(config, entries):
    """Do not remove duplicates from the twenty-unit denominator; flag each collision."""
    by_path = {}
    for e in entries:
        if e["review"]:
            root = Path(config["reviewers"][e["reviewer"]]["root"]).resolve()
            path = (root / e["review"]).resolve()
            by_path.setdefault(str(path), []).append((e["reviewer"], e["case_id"]))
    return {key for keys in by_path.values() if len(keys) > 1 for key in keys}


def verify_frozen_inputs(root, manifest):
    """Replay coordinator-side hashes before executing any code from the clone."""
    paths = [item["path"] for item in manifest["files"]]
    require(len(paths) == len(set(paths)), "Repeated frozen input path")
    for item in manifest["files"]:
        _, actual = pin(root, item["path"])
        require(actual["sha256"] == item["sha256"], "Frozen clone input changed before execution")
    return len(paths)


def context(config, rid, out):
    settings = config["reviewers"][rid]
    root = Path(settings["root"]).absolute()
    require(root.resolve() == root and root.is_dir(), "Original clone root must be canonical")
    python = settings.get("python", str(root / ".venv/bin/python"))
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root).decode().strip()
    require(revision == config["runtime_git_revision"], "Original clone runtime revision differs")
    raw, manifest_pin = pin(root, config["manifest"])
    require(manifest_pin["sha256"] == config["package_sha256"], "Scientific package hash differs")
    manifest = json.loads(raw)
    frozen_input_count = verify_frozen_inputs(root, manifest)
    check, _ = command(root, [python, "-B", "scripts/adhoc/calibration_round_20261116.py", "verify",
                             "--manifest", config["manifest"]], out / "manifest-check")
    require(check["exit_code"] == 0, "Original clone manifest replay failed")
    for item in manifest["files"]:
        if item.get("role") == "proof_adapter":
            require(sha((ROOT / item["path"]).read_bytes()) == item["sha256"],
                    "Coordinator proof adapter differs from frozen runtime")
    helper = "scripts/adhoc/calibration_round_20261116.py"
    helper_pin = next(p for p in manifest["files"] if p["path"] == helper)
    require(sha((ROOT / helper).read_bytes()) == helper_pin["sha256"],
            "Coordinator matrix validator differs from frozen clone validator")
    matrix, labels = rounds.sealed_matrix(root, config["manifest"], settings["matrix"])
    require(matrix["reviewer"]["id"] == rid, "Sealed reviewer identity differs")
    require(matrix["round_id"] == "m5-calibration-20261116-round02", "Wrong scientific round")
    require(settings.get("canonical_identity"), "Expected canonical reviewer identity missing")
    matrix_raw, matrix_pin = pin(root, settings["matrix"])
    receipt_raw, receipt_pin = pin(root, settings["matrix"] + ".receipt.json")
    receipt = json.loads(receipt_raw)
    meta = {"reviewer": rid, "manifest": manifest_pin, "matrix": matrix_pin,
            "matrix_receipt": receipt_pin, "original_seal_time": receipt["saved_at"],
            "runtime_git_revision": revision, "matrix_sha256": sha(matrix_raw),
            "frozen_inputs_verified_before_clone_execution": frozen_input_count,
            "manifest_command": check, "status": "passed"}
    write(out / "context.json", meta)
    return {"root": root, "python": python, "matrix": matrix, "labels": labels,
            "manifest": manifest, "meta": meta, "settings": settings}


def evidence_mapping(evidence_ids, sidecar, manifest, initial_ids):
    files = {(p["path"], p["sha256"]): set(p.get("evidence_ids", []))
             for p in manifest.get("files", [])}
    proofs = {}
    for proof in sidecar.get("proofs", []):
        proofs.setdefault(proof.get("evidence_id"), []).append(proof)
    mapped, failures = set(), []
    for eid in evidence_ids:
        candidates = proofs.get(eid, [])
        if len(candidates) != 1:
            failures.append("missing_or_duplicate_proof")
            continue
        proof = candidates[0]
        raw_pin = proof.get("input", {})
        source_ids = files.get((raw_pin.get("path"), raw_pin.get("sha256")), set())
        choices = source_ids & set(initial_ids)
        explicit = proof.get("manifest_evidence_id")
        if explicit is not None:
            if explicit not in choices:
                failures.append("explicit_source_id_unbound")
                continue
            mapped.add(explicit)
        elif eid in choices:
            mapped.add(eid)
        elif len(choices) == 1:
            mapped.update(choices)
        else:
            failures.append("ambiguous_source_ids" if choices else "unmapped_source_input")
    return mapped, failures


def assessment_parity(authored, saved, matrix_case, sidecar, manifest=None):
    errors = []
    if authored != saved:
        errors.append("authored_saved_document")
    for field in ("assessments", "targets", "completion", "verdict", "review_id", "reviewer",
                  "evidence", "checks", "findings", "actions"):
        if authored.get(field) != saved.get(field):
            errors.append("authored_saved_" + field)
    matrix_axes = {a["axis"]: a for a in matrix_case["assessments"]}
    seen = set()
    for assessment in saved.get("assessments", []):
        dimensions = {d["name"]: d["value"] for d in assessment.get("dimensions", [])}
        axis = dimensions.get("axis")
        if axis not in matrix_axes or axis in seen:
            errors.append("canonical_axis_missing_unknown_or_duplicate")
            continue
        seen.add(axis)
        initial = matrix_axes[axis]
        for name in ("category", "scope"):
            if dimensions.get(name) != initial[name]:
                errors.append("matrix_" + axis + "_" + name)
        for name, value in initial["dimensions"].items():
            if dimensions.get(name) != value:
                label = name if name in rounds.DETAILS[axis] else "extra_" + sha(name.encode())
                errors.append("matrix_" + axis + "_dimension_" + label)
        mapped, mapping_errors = evidence_mapping(assessment.get("evidence_ids", []), sidecar,
                                                  manifest or {}, initial["evidence_ids"])
        errors.extend("matrix_" + axis + "_evidence_" + error for error in mapping_errors)
        if mapped != set(initial["evidence_ids"]):
            errors.append("matrix_" + axis + "_evidence_bindings")
    if seen != set(rounds.CATEGORIES):
        errors.append("canonical_six_axes_incomplete")
    return errors


def rationale_diagnostics(saved, matrix_case):
    """Text differences are evidence for adjudication, never automatic semantic verdicts."""
    canonical = {}
    for item in saved.get("assessments", []):
        dims = {d["name"]: d["value"] for d in item.get("dimensions", [])}
        canonical[dims.get("axis")] = item.get("summary")
    result = []
    for initial in matrix_case["assessments"]:
        axis = initial["axis"]
        rationale, summary_text = initial.get("rationale"), canonical.get(axis)
        available = isinstance(rationale, str) and isinstance(summary_text, str)
        result.append({"axis": axis,
                       "matrix_rationale_sha256": sha(rationale.encode()) if isinstance(rationale, str) else None,
                       "canonical_summary_sha256": sha(summary_text.encode()) if isinstance(summary_text, str) else None,
                       "literal_text_equal": rationale == summary_text if available else None,
                       "semantic_equivalence": "not_assessed_by_replay"})
    return result


def proof_inventory(root, authored, saved, sidecar, canonical_passed):
    """Union every known cited/provided proof; absent sidecars never shrink coverage."""
    evidence_ids = {e["evidence_id"] for review in (authored, saved) if review
                    for e in review.get("evidence", [])}
    by_id = {}
    for proof in (sidecar or {}).get("proofs", []):
        by_id.setdefault(proof.get("evidence_id"), []).append(proof)
    ids = evidence_ids | set(by_id)
    rows, input_pins = [], []
    for eid in sorted(ids, key=str):
        entries = by_id.get(eid, [])
        row = {"evidence_id_sha256": sha(str(eid).encode()), "cited": eid in evidence_ids,
               "proof_count": len(entries), "proof_sha256": sha(encoded(entries)),
               "status": "missing_proof" if not entries else "duplicate_proof" if len(entries) > 1
               else "pending_canonical_check"}
        if len(entries) == 1:
            try:
                raw, raw_pin = pin(root, entries[0]["input"]["path"])
                input_pins.append(raw_pin)
                row["raw_input"] = raw_pin
                row["status"] = ("raw_hash_mismatch" if sha(raw) != entries[0]["input"]["sha256"] else
                                 "passed" if canonical_passed else "canonical_check_failed_or_unavailable")
            except (OSError, ValueError, KeyError, TypeError):
                row["status"] = "raw_input_missing_or_invalid"
        rows.append(row)
    return rows, input_pins, (authored is None and saved is None) or sidecar is None



def isolated_proofs(root, authored, sidecar, packet_path, out):
    """Replay every original proof independently; never validate a modified review.

    The production evidence replay function receives a labeled, in-memory
    one-proof projection solely to prevent an earlier failure hiding later
    evidence. Whole-document validation, aggregate budgets and canonical saves
    remain separate. No projection is persisted as a review or used for scoring.
    """
    sys.path.insert(0, str(ROOT / "src"))
    from edgemech.occurrence_packet import validate_packet
    from edgemech.occurrence_review import _replay_evidence
    from edgemech.pins import check_contracts

    check_contracts()
    packet = load_document(pin(root, packet_path)[0])
    validate_packet(packet, root=root)
    inputs = {item["path"]: item["sha256"] for item in authored["source"]["inputs"]}
    evidence, proofs = {}, {}
    for item in authored["evidence"]:
        evidence.setdefault(item["evidence_id"], []).append(item)
    for item in sidecar["proofs"]:
        proofs.setdefault(item["evidence_id"], []).append(item)
    results = {}
    for eid in sorted(evidence.keys() | proofs.keys()):
        row = {"evidence_id_sha256": sha(eid.encode()), "status": "failed",
               "evidence_entries": len(evidence.get(eid, [])), "proof_entries": len(proofs.get(eid, []))}
        try:
            require(row["evidence_entries"] == row["proof_entries"] == 1,
                    "Every isolated proof needs exactly one original evidence item and proof")
            projected_review = {**authored, "evidence": evidence[eid]}
            projected_sidecar = {**sidecar, "proofs": proofs[eid]}
            replay = _replay_evidence(root, projected_review, packet_path, packet, projected_sidecar, inputs)
            require(set(replay) == {eid}, "Isolated replay omitted its expected proof")
            row["status"] = "passed"
        except Exception as error:
            private = write(out / (sha(eid.encode()) + "-error.json"), {
                "error_type": type(error).__name__, "message": str(error)})
            row["failure"] = private
        results[row["evidence_id_sha256"]] = row
    receipt = {"scope": "Isolated production evidence replay only; original whole-input validation and canonical persistence remain separate",
               "rows": list(results.values()), "expected": len(results),
               "passed": sum(r["status"] == "passed" for r in results.values())}
    return results, write(out / "receipt.json", receipt)


def unit(config, spec, ctx, original, out, path_duplicate=False, input_mode=False):
    root = ctx["root"]
    result = {"reviewer": spec["reviewer"], "case_id": spec["case_id"],
              "occurrence_id": original["occurrence_id"], "status": "failed", "errors": [],
              "canonical_pair_replayed": False, "proofs": [], "input_pins": [],
              "unknown_proof_denominator": True,
              "unit_scope": "Local pair checks; cross-pair review-ID uniqueness is checked in final receipt"}
    if path_duplicate:
        result["errors"].append("duplicate_canonical_path")
    documents = {}
    for field in ("input", "proofs", "review"):
        relative = spec[field]
        if relative is None:
            result["errors"].append("missing_" + field + "_path")
            documents[field] = None
            continue
        try:
            raw, entry_pin = pin(root, relative)
            result["input_pins"].append(entry_pin)
            documents[field] = load_document(raw) if field in {"input", "review"} else json.loads(raw)
        except (OSError, ValueError, KeyError, TypeError):
            documents[field] = None
            result["errors"].append("missing_or_invalid_" + field)
    authored, sidecar, saved = (documents[k] for k in ("input", "proofs", "review"))
    packet_path = next(c["packet_path"] for c in ctx["manifest"]["cases"] if c["case_id"] == spec["case_id"])
    _, packet_pin = pin(root, packet_path)
    result["input_pins"].append(packet_pin)
    if saved is not None:
        result["review_id_sha256"] = sha(str(saved.get("review_id")).encode())
        expected = ctx["matrix"]["reviewer"]
        if (saved.get("reviewer", {}).get("identity") != ctx["settings"]["canonical_identity"] or
                saved.get("reviewer", {}).get("model") != expected["model"]):
            result["errors"].append("canonical_reviewer_identity_or_model")
        if sidecar and "identity" in sidecar and any(
            sidecar["identity"].get(k) != expected[k] for k in ("id", "model", "session_id")
        ):
            result["errors"].append("proof_reviewer_session_identity")
        markdown = str(Path(spec["review"]).with_name("review.md"))
        try:
            raw, markdown_pin = pin(root, markdown)
            require(bool(raw), "Empty canonical Markdown")
            result["input_pins"].append(markdown_pin)
        except (OSError, ValueError):
            result["errors"].append("missing_or_empty_markdown")
    if not input_mode and sidecar is not None and spec["review"] and spec["proofs"]:
        check, stdout = command(root, [ctx["python"], "-B", "-m", "edgemech.occurrence_review", "check",
                                       "--review", spec["review"], "--packet", packet_path,
                                       "--proofs", spec["proofs"]], out / "canonical-check")
        result["canonical_command"] = check
        if check["exit_code"] == 0:
            checked = json.loads(stdout)
            result["canonical_pair_replayed"] = checked["occurrence_id"] == original["occurrence_id"]
            result["verified_evidence"] = checked["verified_evidence"]
            result["verified_quotes"] = checked["verified_quotes"]
        if not result["canonical_pair_replayed"]:
            result["errors"].append("canonical_production_check_failed")
    if authored is not None and saved is not None and sidecar is not None:
        matrix_case = next(c for c in ctx["matrix"]["cases"] if c["case_id"] == spec["case_id"])
        parity_errors = assessment_parity(authored, saved, matrix_case, sidecar, ctx["manifest"])
        result["adaptation_parity"] = {"status": "failed" if parity_errors else "passed",
                                       "errors": parity_errors,
                                       "scope": "Exact canonical input/save and matrix category/scope/details/source-ID binding; matrix rationale paraphrase needs adjudication"}
        result["rationale_diagnostics"] = rationale_diagnostics(saved, matrix_case)
        result["authored_saved_document_equal"] = authored == saved
        result["errors"].extend(parity_errors)
    else:
        result["errors"].append("authored_saved_matrix_parity_unavailable")
        result["adaptation_parity"] = {"status": "unavailable"}
    input_passed = False
    if input_mode and authored is not None and sidecar is not None:
        result["review_id_sha256"] = sha(str(authored.get("review_id")).encode())
        expected = ctx["matrix"]["reviewer"]
        if (authored.get("reviewer", {}).get("identity") != ctx["settings"]["canonical_identity"] or
                authored.get("reviewer", {}).get("model") != expected["model"]):
            result["errors"].append("authored_reviewer_identity_or_model")
        check, stdout = command(root, [ctx["python"], "-B", "-m", "edgemech.occurrence_review", "validate",
                                       "--review", spec["input"], "--packet", packet_path,
                                       "--proofs", spec["proofs"]], out / "input-validation")
        result["input_validation_command"] = check
        if check["exit_code"] == 0:
            checked = json.loads(stdout)
            input_passed = checked["occurrence_id"] == original["occurrence_id"]
            result["verified_evidence"] = checked["verified_evidence"]
            result["verified_quotes"] = checked["verified_quotes"]
        result["input_validation_passed"] = input_passed
        if not input_passed:
            result["errors"].append("authored_input_production_validation_failed")
        matrix_case = next(c for c in ctx["matrix"]["cases"] if c["case_id"] == spec["case_id"])
        errors = assessment_parity(authored, authored, matrix_case, sidecar, ctx["manifest"])
        result["draft_matrix_adaptation"] = {"status": "failed" if errors else "passed", "errors": errors,
                                             "scope": "Authored draft only; no saved-byte parity asserted"}
        result["rationale_diagnostics"] = rationale_diagnostics(authored, matrix_case)
        result["errors"].extend(errors)
    proofs, raw_pins, unknown = proof_inventory(root, authored, saved, sidecar,
                                              input_passed if input_mode else result["canonical_pair_replayed"])
    if input_mode and authored is not None and sidecar is not None:
        try:
            isolated, receipt = isolated_proofs(root, authored, sidecar, packet_path, out / "isolated-proofs")
            result["isolated_proof_receipt"] = receipt
            for row in proofs:
                isolated_row = isolated[row["evidence_id_sha256"]]
                row["whole_input_validation_passed"] = input_passed
                row["isolated_proof_replay"] = isolated_row
                if isolated_row["status"] == "passed" and row["status"] in {
                        "passed", "canonical_check_failed_or_unavailable"}:
                    row["status"] = "passed_isolated_proof"
                else:
                    row["status"] = "failed_isolated_proof"
        except Exception as error:
            result["isolated_proof_failure"] = write(out / "isolated-proof-prerequisite-error.json", {
                "error_type": type(error).__name__, "message": str(error)})
            for row in proofs:
                row["status"] = "isolated_proof_prerequisite_failed"

    result["proofs"], result["unknown_proof_denominator"] = proofs, unknown
    result["input_pins"].extend(raw_pins)
    if unknown or any(p["status"] not in {"passed", "passed_isolated_proof"} for p in proofs):
        result["errors"].append("proof_integrity_incomplete")
    if not result["errors"] and result["canonical_pair_replayed"]:
        result["status"] = "passed"
    write(out / "unit.json", result)
    return result


def summary(rows, mode):
    ids = {}
    for row in rows:
        if row.get("review_id_sha256"):
            ids.setdefault(row["review_id_sha256"], []).append(row)
    for group in ids.values():
        if len(group) > 1:
            for row in group:
                row["errors"].append("duplicate_review_id")
                row["status"] = "failed"
    proof_rows = [p for r in rows for p in r["proofs"]]
    return {"expected_pairs": 20 if mode in {"batch", "input-batch"} else 1, "entries_retained": len(rows),
            "canonical_pairs_replayed": sum(r["canonical_pair_replayed"] for r in rows),
            "all_parity_and_integrity_passed_pairs": sum(r["status"] == "passed" for r in rows),
            "known_expected_proof_items": len(proof_rows),
            "provided_proof_declarations": sum(p["proof_count"] for p in proof_rows),
            "passed_proof_items": sum(p["status"] in {"passed", "passed_isolated_proof"} for p in proof_rows),
            "authored_inputs_production_validated": sum(r.get("input_validation_passed", False) for r in rows),
            "canonical_persistence_gate_passed": len(rows) == 20 and all(r["canonical_pair_replayed"] for r in rows),
            "entries_with_unknown_proof_denominator": sum(r["unknown_proof_denominator"] for r in rows),
            "entries_with_nonidentical_matrix_rationale": sum(
                any(d["literal_text_equal"] is not True for d in r.get("rationale_diagnostics", []))
                for r in rows),
            "technical_integrity_complete": len(rows) == (20 if mode in {"batch", "input-batch"} else 1)
            and all(r["status"] == "passed" for r in rows),
            "scientific_calibration_pass": False}


def check_canary(directory, config, input_mode=False):
    receipt = json.loads((directory / "receipt.json").read_text())
    require(receipt["mode"] == ("input-canary" if input_mode else "canary") and receipt["helper_sha256"] == sha(Path(__file__).read_bytes())
            and receipt["config_sha256"] == sha(encoded(config)), "Canary runtime/configuration changed")
    require(len(receipt["rows"]) == 1 and receipt["rows"][0]["case_id"] == "fresh-47",
            "Canary must retain exactly one fresh-47 unit")
    if input_mode:
        require(receipt["rows"][0].get("input_validation_passed") and
                not receipt["rows"][0]["unknown_proof_denominator"] and
                all(p["status"] == "passed_isolated_proof" for p in receipt["rows"][0]["proofs"]),
                "Input canary did not replay all authored evidence")
    else:
        require(receipt["summary"]["technical_integrity_complete"], "Canary did not verify one fresh-47 pair")
    require(not directory.is_symlink() and not any(p.is_symlink() for p in directory.rglob("*")),
            "Canary artifact path became a symlink")
    expected_artifacts = {item["path"] for item in receipt["artifact_pins"]}
    actual_artifacts = {str(path.absolute()) for path in directory.rglob("*") if path.is_file()
                        and path != directory / "receipt.json"}
    require(actual_artifacts == expected_artifacts, "Canary persisted artifact inventory changed")
    for artifact in receipt["artifact_pins"]:
        require(sha(Path(artifact["path"]).read_bytes()) == artifact["sha256"],
                "Canary persisted command/unit artifact changed")
    check = receipt["rows"][0].get("input_validation_command" if input_mode else "canonical_command")
    require(check and check["exit_code"] == 0, "Canary lacks successful production check")
    checked = json.loads(Path(check["stdout"]["path"]).read_bytes())
    require(checked["occurrence_id"] == receipt["rows"][0]["occurrence_id"],
            "Canary production receipt occurrence differs")
    for item in receipt["rows"][0]["input_pins"]:
        _, current = pin(Path(item["root"]), item["path"])
        require(current == item, "Canary original input changed")
    for context_meta in receipt["contexts"].values():
        for key in ("manifest", "matrix", "matrix_receipt"):
            item = context_meta[key]
            _, current = pin(Path(item["root"]), item["path"])
            require(current == item, "Canary seal or manifest changed")
    return receipt


def run(config, output, mode, reviewer="reviewer-a", canary=None):
    cases, entries = expected_entries(config)
    require(not output.exists() and ".temp" in output.absolute().parts, "Use a new private output directory")
    require(not any(p.is_symlink() for p in (output, *output.absolute().parents)),
            "Output path must not traverse a symlink")
    input_mode = mode in {"input-canary", "input-batch"}
    if mode in {"batch", "input-batch"}:
        require(canary is not None, "Batch requires the inspected persisted canary")
        check_canary(canary, config, input_mode=input_mode)
    else:
        entries = [e for e in entries if e["case_id"] == "fresh-47" and e["reviewer"] == reviewer]
        require(len(entries) == 1, "Exactly one fresh-47 canary required")
    output.mkdir(mode=0o700, parents=True)
    contexts, context_errors, rows = {}, {}, []
    for rid in sorted({e["reviewer"] for e in entries}):
        try:
            contexts[rid] = context(config, rid, output / rid / "context")
        except Exception as error:
            private = write(output / rid / "context-error.json", {
                "error_type": type(error).__name__, "message": str(error)})
            context_errors[rid] = private
    duplicate_paths = duplicates(config, entries)
    for spec in entries:
        out = output / spec["reviewer"] / spec["case_id"]
        try:
            require(spec["reviewer"] in contexts, "Original manifest/matrix prerequisite failed")
            row = unit(config, spec, contexts[spec["reviewer"]], cases[spec["case_id"]], out,
                       (spec["reviewer"], spec["case_id"]) in duplicate_paths, input_mode=input_mode)
        except Exception as error:
            private = write(out / "error.json", {"error_type": type(error).__name__, "message": str(error)})
            row = {"reviewer": spec["reviewer"], "case_id": spec["case_id"], "status": "failed",
                   "occurrence_id": cases[spec["case_id"]]["occurrence_id"],
                   "canonical_pair_replayed": False, "errors": ["unit_or_prerequisite_failed"],
                   "private_failure_receipt": private, "proofs": [], "input_pins": [],
                   "unknown_proof_denominator": True}
        rows.append(row)
    totals = summary(rows, mode)
    if len(contexts) == 2 and len({c["matrix"]["reviewer"]["session_id"] for c in contexts.values()}) != 2:
        totals["technical_integrity_complete"] = False
        totals["reviewer_session_error"] = "two_labels_share_session"
    for row in rows:
        for item in row["input_pins"]:
            try:
                _, current = pin(Path(item["root"]), item["path"])
                require(current == item, "Read-only input changed during replay")
            except (OSError, ValueError):
                row["errors"].append("input_changed_during_replay")
                row["status"] = "failed"
                totals["technical_integrity_complete"] = False
    totals["all_parity_and_integrity_passed_pairs"] = sum(r["status"] == "passed" for r in rows)
    artifacts = [{"path": str(path.absolute()), "sha256": sha(path.read_bytes())}
                 for path in sorted(output.rglob("*")) if path.is_file()]
    receipt = {"schema": SCHEMA, "mode": mode, "helper_sha256": sha(Path(__file__).read_bytes()),
               "artifact_pins": artifacts,
               "config_sha256": sha(encoded(config)), "package_sha256": config["package_sha256"],
               "contexts": {rid: ctx["meta"] for rid, ctx in contexts.items()},
               "context_errors": context_errors, "rows": rows, "summary": totals,
               "scope": "Technical pair/proof/parity replay only; no new ratings or semantic approval."}
    write(output / "receipt.json", receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("canary", "check-canary", "batch", "input-canary", "check-input-canary", "input-batch"))
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--canary", type=Path)
    parser.add_argument("--reviewer", choices=("reviewer-a", "reviewer-b"), default="reviewer-a")
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    if args.mode in {"check-canary", "check-input-canary"}:
        result = check_canary(args.canary, config, input_mode=args.mode == "check-input-canary")
    else:
        require(args.output is not None, "Output directory required")
        result = run(config, args.output, args.mode, args.reviewer, args.canary)
    print(json.dumps(result["summary"], sort_keys=True))
    return 0 if result["summary"]["technical_integrity_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
