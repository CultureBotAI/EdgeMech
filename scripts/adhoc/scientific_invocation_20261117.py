#!/usr/bin/env python3
"""Bind future reviewer prompts to a verified package, clone and fresh session.

Issue #203, 2026-11-17. Inputs: a package-pinned structured instruction plan and
same-clone production receipt. Outputs: exclusive invocation JSON and generated
prompt. Preparing or checking this contract does not authorize scientific work,
assign ratings, certify evidence sufficiency, or relax the unchanged thresholds.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

import calibration_round_20261116 as rounds

PLAN_SCHEMA = "edgemech-scientific-instructions/v1"
ADJUDICATION_PLAN_SCHEMA = "edgemech-scientific-instructions/v2"
ADJUDICATION_SCHEMA = "edgemech-initial-results-binding/v1"
TEMPLATE_SCHEMA = "edgemech-scientific-instruction-template/v1"
SCHEMA = "edgemech-scientific-invocation/v1"
PURPOSE = "scientific_calibration_candidate"
HELPER = "scripts/adhoc/scientific_invocation_20261117.py"
PHASES = {"blinded_initial_review", "evidence_adjudication"}
SESSION_KEYS = {"reviewer_id", "workdir", "session_root", "output_root"}
PLACEHOLDERS = {"manifest_path", "round_id", "workdir", "session_root", "output_root", "reviewer_id"}
# Invocation paths belong in typed placeholders, never in copied prose. Treat
# ambiguous slash expressions conservatively: templates can spell out “save and
# check” while source evidence retains its exact scientific text unchanged.
LITERAL_PATH = re.compile(r"[/\\]|\b(?:manifest|initial-seal|reviewer-result)\.json\b|"
                          r"\b(?:FINAL_REPORT|final)\.md\b")
INITIAL_ROLES = {"initial_manifest", "initial_matrix", "initial_receipt", "initial_seal",
                 "initial_comparison", "initial_authored_review", "initial_proof_sidecar",
                 "initial_invocation", "initial_worker_metadata", "initial_worker_identity",
                 "initial_worker_events", "initial_native_session", "initial_config",
                 "initial_prompt", "initial_readiness"}


def original_runtime(original, original_files):
    """Validate the complete recorded runtime, without substituting this clone's environment."""
    import run_m5_review_worker_20261116 as worker

    runtime = original["runtime"]
    rounds.require(isinstance(runtime, dict) and set(runtime) == set(worker.RUNTIME_KEYS),
                   "Initial runtime lacks the complete maintained launcher bindings")
    rounds.require(all(isinstance(value, str) and value.strip() for value in runtime.values()),
                   "Initial runtime has an empty or invalid binding")
    rounds.require(all(re.fullmatch(r"[0-9a-f]{64}", value)
                       for key, value in runtime.items() if key.endswith("_sha256")),
                   "Initial runtime has an invalid hash")
    launcher = "scripts/adhoc/run_m5_review_worker_20261116.py"
    rounds.require(launcher in original_files
                   and "scripts/adhoc/prepare_calibration_20261115.py" in original_files
                   and runtime["helper_sha256"] == original_files[launcher]["sha256"]
                   and runtime["lock_sha256"] == original_files["uv.lock"]["sha256"],
                   "Initial launcher or lock hash differs from original frozen runtime")
    clone = Path(original["session"]["workdir"])
    prefix, executable = Path(runtime["python_prefix"]), Path(runtime["python_executable"])
    rounds.require(prefix.is_absolute() and prefix.is_relative_to(clone) and prefix != clone
                   and executable.is_absolute() and executable.parent == prefix / "bin"
                   and Path(runtime["codex_path"]).is_absolute()
                   and runtime["repository_identity"] == worker.REPOSITORY
                   and runtime["repository_origin"].removesuffix(".git")
                   == "https://github.com/CultureBotAI/EdgeMech",
                   "Initial runtime does not bind the original isolated EdgeMech clone")
    return runtime


def original_readiness(root, files, original, original_files, metadata):
    """Replay retained original readiness lineage without reusing its environment authority.

    Absolute paths are interpreted under the recorded original clone. Only their
    pinned byte-identical retained copies are read here. No old subprocess command,
    credential, binary or interpreter is executed in the later adjudicator clone.
    """
    import run_m5_review_worker_20261116 as worker

    from edgemech.occurrence_review import validate_occurrence_review

    runtime = original_runtime(original, original_files)
    clone = Path(original["session"]["workdir"])

    def retained(value, *, hidden=True):
        rounds.require(isinstance(value, dict) and set(value) == {"path", "sha256"}
                       and isinstance(value["path"], str) and value["path"] in files,
                       "Original readiness dependency is not package-pinned")
        path = value["path"]
        rounds.require(str(Path(path)) == path and value == pin(root, path)
                       and files[path]["sha256"] == value["sha256"]
                       and rounds.safe(root, path).stat().st_size > 0,
                       "Original readiness dependency changed")
        rounds.require(not hidden or files[path].get("visibility") != "reviewer",
                       "Original readiness mechanics cannot be scientific navigation")
        return rounds.safe(root, path)

    def relative_saved(path, *, beneath=None):
        rounds.require(isinstance(path, str) and Path(path).is_absolute()
                       and str(Path(path)) == path and Path(path).is_relative_to(clone),
                       "Original readiness path belongs to another clone")
        if beneath is not None:
            rounds.require(Path(path).is_relative_to(beneath),
                           "Original readiness artifact escapes its recorded output")
        relative = str(Path(path).relative_to(clone))
        rounds.safe(root, relative)
        return relative

    receipt_pin = original["production_receipt"]
    receipt_file = retained(receipt_pin)
    rounds.require(Path(receipt_pin["path"]).parts[0] == ".temp"
                   and files[receipt_pin["path"]]["role"] == "initial_readiness",
                   "Original readiness receipt must be a private typed input")
    receipt = rounds.read(root, receipt_pin["path"])
    output = clone / Path(receipt_pin["path"]).parent
    output_relative = Path(receipt_pin["path"]).parent
    rounds.require(receipt.get("schema") == worker.SCHEMA and receipt.get("status") == "passed"
                   and receipt.get("scope") == worker.PRODUCTION_SCOPE
                   and all(receipt.get(key) == value for key, value in runtime.items()),
                   "Original readiness receipt does not match the complete initial runtime")
    state_pin = {"path": str(output_relative / "metadata.json"),
                 "sha256": receipt.get("metadata_sha256")}
    retained(state_pin)
    state = rounds.read(root, state_pin["path"])
    rounds.require(state.get("schema") == worker.SCHEMA and state.get("role") == "canary"
                   and state.get("status") == "passed" and state.get("exit_code") == 0
                   and state.get("workdir") == str(clone) and state.get("output_root") == str(output)
                   and state.get("ending_git_head") == runtime["git_head"]
                   and all(state.get(key) == value for key, value in runtime.items()),
                   "Original readiness metadata is incomplete or belongs to another clone/runtime")
    rounds.require(timestamp(state["started_at"], "canary started_at")
                   <= timestamp(state["finished_at"], "canary finished_at")
                   <= timestamp(metadata["started_at"], "initial started_at"),
                   "Original readiness must complete before the initial worker starts")
    result_pin = {"path": str(output_relative / "canary-result.json"),
                  "sha256": receipt.get("result_sha256")}
    retained(result_pin)
    result = rounds.read(root, result_pin["path"])
    checks = result.get("checks", [])
    names = [item.get("name") for item in checks if isinstance(item, dict)]
    rounds.require(result == receipt.get("result") and result.get("status") == "passed"
                   and isinstance(checks, list) and len(names) == len(checks)
                   and all(item.get("passed") is True for item in checks)
                   and all(isinstance(name, str) for name in names)
                   and len(set(names)) == len(names) and worker.CHECKS <= set(names),
                   "Original readiness result/checks are incomplete")
    artifacts = result.get("artifacts", [])
    rounds.require(isinstance(artifacts, list) and artifacts, "Missing original readiness artifacts")
    seen = set()
    for item in artifacts:
        path = relative_saved(item.get("path"), beneath=output)
        rounds.require(path not in seen and path != result_pin["path"],
                       "Repeated or self-referential original readiness artifact")
        seen.add(path)
        retained({"path": path, "sha256": item.get("sha256")})
    bootstrap = receipt.get("independent_replay", {})
    rounds.require(bootstrap == state.get("independent_replay"),
                   "Original bootstrap receipt and metadata differ")
    for name in ("packet.json", "receipt.json"):
        actual = str(worker.FRESH47 / name)
        copied = str(output_relative / name)
        sha = bootstrap.get("artifacts", {}).get(name)
        retained({"path": actual, "sha256": sha}, hidden=False)
        retained({"path": copied, "sha256": sha})
        doc = rounds.read(root, copied)
        cohort = rounds.read(root, rounds.COHORT)
        target = next(c for c in cohort["cases"] if c["case_id"] == "fresh-47")
        rounds.require(doc.get("occurrence_id") == target["occurrence_id"]
                       and (name != "receipt.json" or doc.get("case_id") == "fresh-47"),
                       "Original readiness used another bootstrap occurrence")
    production = receipt.get("production")
    rounds.require(isinstance(production, dict) and production == state.get("production"),
                   "Original production readiness lineage is missing or inconsistent")
    spec = production.get("spec", {})
    rounds.require(spec.get("workdir") == str(clone)
                   and spec.get("package") == original["manifest"]
                   and state.get("production_plan") == spec,
                   "Original production readiness names another clone or package")
    for item in [spec["package"], *spec["inputs"].values(), *spec["source_inputs"]]:
        retained(item, hidden=False)
    for item in spec["execution_files"]:
        rounds.require(item["path"] in original_files
                       and original_files[item["path"]]["sha256"] == item["sha256"],
                       "Original production execution file was not frozen")
    current_spec = worker.production_spec(root, *(spec["inputs"][name]["path"]
                                                for name in ("review", "packet", "proofs")),
                                          spec["package"]["path"])
    rounds.require(current_spec == {**spec, "workdir": str(root)},
                   "Retained original production inputs or execution inventory changed")
    for item in production["outputs"].values():
        retained(item)
    rounds.require(worker.inspect_production_pair(root, spec) == production["outputs"],
                   "Retained original canonical save/readback pair changed")
    authored = worker.load_document(retained(spec["inputs"]["review"], hidden=False).read_bytes())
    canonical_check = validate_occurrence_review(root, authored, spec["inputs"]["packet"]["path"],
                                                 spec["inputs"]["proofs"]["path"])
    prompt_path = relative_saved(state.get("prompt_path"))
    retained({"path": prompt_path, "sha256": receipt.get("prompt_sha256")})
    rounds.require(state.get("prompt_sha256") == receipt.get("prompt_sha256")
                   and state.get("executed_prompt_sha256") == receipt.get("executed_prompt_sha256"),
                   "Original readiness prompt bindings differ")
    validators = [*bootstrap.get("validators", []), *production.get("validators", [])]
    expected_names = {"runtime_contracts", "fresh47_packet_replay", "production-package",
                      "production-save", "production-check"}
    rounds.require(len(validators) == len(expected_names)
                   and {v.get("name") for v in validators} == expected_names,
                   "Original readiness is missing independent validator records")
    executable = runtime["python_executable"]
    commands = {
        "runtime_contracts": [executable, "-B", "-m", "edgemech", "check-contracts"],
        "fresh47_packet_replay": [executable, "-B", str(clone / "scripts/adhoc/prepare_calibration_20261115.py"),
                                   "--check", "fresh-47"],
        "production-package": [executable, "-B", str(clone / "scripts/adhoc/calibration_round_20261116.py"),
                               "--root", str(clone), "verify", "--manifest", spec["package"]["path"]],
    }
    for action in ("save", "check"):
        commands["production-" + action] = [
            executable, "-B", "-m", "edgemech.occurrence_review", action, "--root", str(clone),
            "--review", spec["review"] if action == "check" else spec["inputs"]["review"]["path"],
            "--packet", spec["inputs"]["packet"]["path"], "--proofs", spec["inputs"]["proofs"]["path"]]
    expected_results = {
        "production-package": rounds.verify(root, spec["package"]["path"]),
        "production-check": canonical_check,
        "production-save": {**canonical_check, "review": spec["review"],
                            "review_sha256": production["outputs"]["review"]["sha256"]},
    }
    for validation in validators:
        rounds.require(validation.get("exit_code") == 0
                       and validation.get("command") == commands[validation["name"]],
                       "Original readiness validator failed or differs from maintained command")
        for stream in ("stdout", "stderr"):
            path = str(output_relative / f"validator-{validation['name']}.{stream}")
            value = {"path": path, "sha256": validation.get(stream + "_sha256")}
            # Successful validators routinely have empty stderr; it must still be pinned.
            rounds.require(path in files and files[path]["sha256"] == value["sha256"]
                           and files[path].get("visibility") != "reviewer"
                           and value == pin(root, path), "Original validator output changed or missing")
            if stream == "stdout" and validation["name"] in expected_results:
                rounds.require(rounds.read(root, path) == expected_results[validation["name"]],
                               "Original production validator output differs from retained replay")
    for field in ("canary", "ending_replay"):
        replay = metadata.get(field, {})
        rounds.require(replay.get("path") == str(clone / receipt_pin["path"])
                       and replay.get("sha256") == pin(root, str(receipt_file.relative_to(root)))["sha256"]
                       and replay.get("current_replay", {}).get("artifacts") == bootstrap["artifacts"]
                       and replay.get("production_replay", {}).get("spec") == spec
                       and replay.get("production_replay", {}).get("outputs") == production["outputs"],
                       "Initial worker did not replay its bound original readiness at entry and exit")


def timestamp(value, name):
    rounds.text(value, name)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("Invalid " + name) from error
    rounds.require(parsed.tzinfo is not None, "Timestamp needs a timezone: " + name)
    return parsed


def artifact(root, files, value, role=None, *, visible=None):
    """Require an exact typed pin inside this phase's immutable package."""
    rounds.require(isinstance(value, dict) and set(value) == {"path", "sha256"},
                   "Invalid adjudication artifact pin")
    path = value["path"]
    rounds.require(isinstance(path, str) and str(Path(path)) == path and path in files,
                   "Adjudication artifact is not package-pinned")
    item = files[path]
    rounds.require(value == pin(root, path) and item["sha256"] == value["sha256"],
                   "Adjudication artifact hash mismatch")
    if role is not None:
        rounds.require(item["role"] == role, "Adjudication artifact role mismatch")
        rounds.require(Path(path).parts[0] == ".temp",
                       "Initial adjudication artifacts must remain private beneath .temp")
    if visible is not None:
        rounds.require((item.get("visibility") == "reviewer") is visible,
                       "Adjudication artifact exposure mismatch")
    return rounds.read(root, path)


def observed_identity(root, files, entry, reviewer):
    """Replay only identity fields from the private, final native-session snapshot."""
    identity = artifact(root, files, entry["identity"], "initial_worker_identity", visible=False)
    rounds.require(re.fullmatch(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}",
                                reviewer["session_id"]), "Invalid original native session UUID")
    rounds.require(identity.get("schema") == "edgemech-worker-identity/v1"
                   and identity.get("model") == reviewer["model"]
                   and identity.get("session_id") == reviewer["session_id"]
                   and identity.get("events") == entry["events"]
                   and identity.get("native_session", {}).get("sha256")
                   == entry["native_session"]["sha256"], "Initial observed identity mismatch")
    threads, native_ids, models = set(), set(), set()
    for field, role in (("events", "initial_worker_events"),
                        ("native_session", "initial_native_session")):
        value = entry[field]
        rounds.require(isinstance(value, dict) and set(value) == {"path", "sha256"}
                       and isinstance(value["path"], str) and value["path"] in files
                       and str(Path(value["path"])) == value["path"]
                       and Path(value["path"]).parts[0] == ".temp", "Missing private session pin")
        item = files[value["path"]]
        rounds.require(item["role"] == role and item.get("visibility") != "reviewer"
                       and value == pin(root, value["path"])
                       and item["sha256"] == value["sha256"], "Private session pin mismatch")
        for line in rounds.safe(root, value["path"]).read_bytes().splitlines():
            event = json.loads(line, object_pairs_hook=rounds.unique_object)
            rounds.require(isinstance(event, dict), "Malformed initial session event")
            if field == "events" and event.get("type") == "thread.started":
                threads.add(event.get("thread_id"))
            if field == "native_session":
                payload = event.get("payload", {})
                if event.get("type") == "session_meta":
                    native_ids.add(payload.get("id"))
                if event.get("type") == "turn_context":
                    models.add(payload.get("model"))
    rounds.require(threads == native_ids == {reviewer["session_id"]}
                   and models == {reviewer["model"]}, "Initial native session/model mismatch")


def adjudication_inputs(root, plan, manifest, files):
    """Replay the completed originals without refreezing or changing their identities.

    A separate phase manifest avoids a circular hash: initial matrices continue to
    name the original manifest; the adjudication manifest pins those original bytes.
    This is a launcher coherence contract, not a new scientific review schema.
    """
    import run_m5_review_worker_20261116 as worker
    import seal_m5_round03_initial_20261116 as seals

    value = plan.get("adjudication")
    rounds.require(isinstance(value, dict) and set(value) == {
        "schema", "initial_manifest", "runtime_git_head", "reviewers", "comparison"}
        and value["schema"] == ADJUDICATION_SCHEMA, "Missing typed adjudication inputs")
    commit = value["runtime_git_head"]
    rounds.require(isinstance(commit, str) and re.fullmatch(r"[0-9a-f]{40}", commit),
                   "Initial runtime must be an exact Git commit")
    initial = artifact(root, files, value["initial_manifest"], "initial_manifest", visible=False)
    original_path = value["initial_manifest"]["path"]
    rounds.require(original_path != plan["manifest_path"]
                   and initial.get("package_purpose") == PURPOSE
                   and initial["round_id"] == manifest["round_id"]
                   and initial["cases"] == manifest["cases"]
                   and initial["cohort_id"] == manifest["cohort_id"],
                   "Adjudication must retain the original round, cases and evidence bindings")
    rounds.verify(root, original_path)
    original_files = {item["path"]: item for item in initial["files"]}
    for path, item in original_files.items():
        rounds.require(path in files and all(files[path].get(key) == val for key, val in item.items()
                                            if key != "visibility"),
                       "Adjudication changed an original input or its role/version")
    entries = value["reviewers"]
    rounds.require(isinstance(entries, list) and len(entries) == 2,
                   "Adjudication requires exactly two original reviewers")
    ids, sessions, clones, matrix_paths, seal_paths = set(), set(), set(), [], set()
    visible_results, initial_navigation = set(), None
    for position, entry in enumerate(entries):
        rounds.require(isinstance(entry, dict) and set(entry) == {
            "position", "reviewer", "saved_at", "matrix", "receipt", "seal", "invocation",
            "metadata", "identity", "events", "native_session"}
            and entry["position"] == ("reviewer_a", "reviewer_b")[position],
            "Invalid or swapped initial reviewer positions")
        matrix = artifact(root, files, entry["matrix"], "initial_matrix", visible=True)
        receipt = artifact(root, files, entry["receipt"], "initial_receipt", visible=True)
        seal = artifact(root, files, entry["seal"], "initial_seal", visible=True)
        reviewer = entry["reviewer"]
        rounds.require(isinstance(reviewer, dict) and reviewer == matrix["reviewer"]
                       == receipt["reviewer"], "Original reviewer identity was swapped or changed")
        matrix_path = entry["matrix"]["path"]
        rounds.require(matrix_path not in matrix_paths and entry["seal"]["path"] not in seal_paths
                       and entry["receipt"]["path"] == matrix_path + ".receipt.json"
                       and receipt["matrix_path"] == matrix_path
                       and receipt["matrix_sha256"] == entry["matrix"]["sha256"]
                       and receipt.get("initial_seal") == entry["seal"]
                       and seal["manifest"] == original_path
                       and seal["matrix"] == entry["matrix"]
                       and seal.get("schema") == seals.SCHEMA
                       and seal.get("scope") == receipt.get("scope") == seals.SCOPE,
                       "Initial matrix, receipt and authored seal do not match")
        rounds.require(entry["saved_at"] == receipt["saved_at"] == seal["saved_at"],
                       "Original initial timestamps changed")
        saved_at = timestamp(entry["saved_at"], "initial saved_at")
        rounds.require(reviewer["id"] not in ids and reviewer["session_id"] not in sessions,
                       "Initial reviewers require distinct identities and native sessions")
        ids.add(reviewer["id"])
        sessions.add(reviewer["session_id"])
        matrix_paths.append(matrix_path)
        seal_paths.add(entry["seal"]["path"])
        for item in seal["inputs"]:
            rounds.require(item["path"] in files
                           and files[item["path"]]["sha256"] == item["sha256"],
                           "Initial seal dependency is outside the adjudication package")
        seals.check(root, entry["seal"]["path"])
        for check in seal["validations"]:
            for field, role in (("review", "initial_authored_review"),
                                ("proofs", "initial_proof_sidecar")):
                document = artifact(root, files, check[field], role, visible=True)
                visible_results.add(check[field]["path"])
                if field == "review":
                    rounds.require(document["source"]["git_revision"] == commit,
                                   "Initial authored review uses another runtime commit")
        original = artifact(root, files, entry["invocation"], "initial_invocation", visible=False)
        rounds.require(isinstance(original, dict) and set(original) == {
            "schema", "purpose", "round_id", "manifest", "instructions", "runtime",
            "production_receipt", "session", "prompt"} and original["schema"] == SCHEMA
            and original["purpose"] == PURPOSE and original["round_id"] == initial["round_id"]
            and original["manifest"] == value["initial_manifest"]
            and original["runtime"]["git_head"] == commit,
            "Initial launch manifest, identity or runtime differs")
        original_runtime(original, original_files)
        original_plan, _, original_bindings = checked_plan(
            root, original_path, original["instructions"]["path"])
        rounds.require(original_plan["phase"] == "blinded_initial_review"
                       and original["instructions"] == original_bindings["instructions"]
                       and original["session"] in original_plan["sessions"]
                       and original["session"]["reviewer_id"] == reviewer["id"],
                       "Initial invocation does not bind this blinded reviewer")
        navigation = set(original_plan["read_paths"]) - set(original_plan["instruction_paths"])
        rounds.require(initial_navigation is None or initial_navigation == navigation,
                       "Initial reviewers did not share one evidence navigation boundary")
        initial_navigation = navigation
        clone = original["session"]["workdir"]
        rounds.require(clone not in clones, "Initial reviewers reused a clone")
        clones.add(clone)
        prompt = original["prompt"]
        rounds.require(prompt["path"] in files and files[prompt["path"]]["sha256"] == prompt["sha256"]
                       and files[prompt["path"]].get("visibility") != "reviewer"
                       and rounds.safe(root, prompt["path"]).read_bytes() == generated_prompt(
                           original_plan, initial, original["session"], original_bindings,
                           instruction_templates(root, original_plan)),
                       "Initial generated prompt changed")
        metadata = artifact(root, files, entry["metadata"], "initial_worker_metadata", visible=False)
        expected_context = {"path": entry["invocation"]["path"],
                            "sha256": entry["invocation"]["sha256"],
                            "manifest": original["manifest"], "session": original["session"],
                            "scope": "invocation_coherence_not_scientific_approval"}
        rounds.require(metadata.get("schema") == worker.SCHEMA
                       and metadata.get("status") == "completed" and metadata.get("exit_code") == 0
                       and metadata.get("role") == "reviewer"
                       and metadata.get("scientific_invocation") == expected_context
                       and metadata.get("workdir") == clone
                       and metadata.get("output_root") == original["session"]["output_root"]
                       and metadata.get("ending_git_head") == commit
                       and all(metadata.get(key) == val for key, val in original["runtime"].items())
                       and metadata.get("prompt_sha256") == prompt["sha256"],
                       "Initial worker did not complete the bound invocation/runtime")
        rounds.require(timestamp(initial["created_at"], "initial package created_at")
                       <= timestamp(metadata["started_at"], "initial started_at") <= saved_at
                       <= timestamp(metadata["finished_at"], "initial finished_at")
                       <= timestamp(manifest["created_at"], "adjudication created_at"),
                       "Initial sealing/completion must precede the adjudication freeze")
        output = Path(original["session"]["output_root"]).relative_to(clone)
        rounds.require(entry["metadata"]["path"] == str(output / "metadata.json")
                       and entry["events"]["path"] == str(output / "events.jsonl"),
                       "Initial worker artifacts belong to another output root")
        original_readiness(root, files, original, original_files, metadata)
        observed_identity(root, files, entry, reviewer)
        visible_results.update(entry[field]["path"] for field in ("matrix", "receipt", "seal"))
    comparison = artifact(root, files, value["comparison"], "initial_comparison", visible=True)
    rounds.require(comparison == rounds.compare(root, original_path, *matrix_paths),
                   "Initial comparison differs from deterministic replay or reviewer order")
    visible_results.add(value["comparison"]["path"])
    rounds.require(set(plan["read_paths"]) == initial_navigation | visible_results
                   | set(plan["instruction_paths"]),
                   "Adjudication navigation must contain only original evidence and sealed results")
    rounds.require(all(session["reviewer_id"] not in ids and session["workdir"] not in clones
                       for session in plan["sessions"]),
                   "Adjudication requires a separate identity and clone from initial reviewers")
    return value


def instruction_templates(root, plan):
    templates = []
    for path in plan["instruction_paths"]:
        try:
            template = rounds.read(root, path)
        except (ValueError, TypeError) as error:
            raise ValueError("Scientific instructions require structured templates, not legacy prose") \
                from error
        rounds.require(isinstance(template, dict) and set(template) == {"schema", "text"}
                       and template["schema"] == TEMPLATE_SCHEMA
                       and isinstance(template["text"], str) and template["text"].strip(),
                       "Scientific instructions require structured templates")
        body = template["text"]
        names = re.findall(r"\{\{([a-z_]+)\}\}", body)
        rounds.require(set(names) <= PLACEHOLDERS, "Unknown instruction placeholder")
        literal = re.sub(r"\{\{[a-z_]+\}\}", "", body)
        rounds.require("{{" not in literal and "}}" not in literal
                       and not LITERAL_PATH.search(literal),
                       "Instruction templates must use bound placeholders for paths")
        templates.append(template)
    return templates


def absolute(path):
    rounds.require(isinstance(path, str), "Missing absolute path")
    value = Path(path)
    rounds.require(value.is_absolute() and str(value) == str(value.resolve()),
                   "Path must be absolute, canonical and free of symlinks")
    rounds.require(not any(part.is_symlink() for part in (value, *value.parents)), "Symlink path")
    return value


def pin(root, path):
    return {"path": path, "sha256": rounds.digest(rounds.safe(root, path).read_bytes())}


def checked_plan(root, manifest_path, plan_path):
    """Replay originals with the existing verifier; add only invocation coherence."""
    replay = rounds.verify(root, manifest_path)
    manifest = rounds.read(root, manifest_path)
    rounds.require(manifest.get("package_purpose") == PURPOSE,
                   "Engineering-only or undeclared package cannot authorize scientific invocation")
    files = {item["path"]: item for item in manifest["files"]}
    rounds.require(plan_path in files and files[plan_path]["role"] == "scientific_instructions",
                   "Scientific instruction plan must be pinned with its explicit role")
    rounds.require(HELPER in files, "Invocation helper must be pinned")
    plan = rounds.read(root, plan_path)
    rounds.require(isinstance(plan, dict) and plan.get("phase") in PHASES,
                   "Unsupported scientific phase")
    adjudication = plan["phase"] == "evidence_adjudication"
    fields = {"schema", "purpose", "round_id", "manifest_path", "phase",
              "instruction_paths", "read_paths", "sessions"}
    rounds.require(set(plan) == fields | ({"adjudication"} if adjudication else set()),
                   "Unexpected or missing scientific instruction fields")
    rounds.require(plan["schema"] == (ADJUDICATION_PLAN_SCHEMA if adjudication else PLAN_SCHEMA)
                   and plan["purpose"] == PURPOSE,
                   "Invalid scientific instruction purpose or schema")
    rounds.require(plan["round_id"] == manifest["round_id"]
                   and plan["manifest_path"] == manifest_path,
                   "Instruction/package manifest ID or path mismatch")
    for name in ("read_paths", "instruction_paths"):
        values = plan[name]
        rounds.require(isinstance(values, list) and values
                       and all(isinstance(value, str) for value in values)
                       and len(values) == len(set(values)), "Invalid " + name)
    allowed = set(plan["read_paths"])
    if not adjudication:
        rounds.require(not any(item["role"] in INITIAL_ROLES for item in files.values()),
                       "Blinded initial package cannot include initial reviewer results")
    rounds.require(allowed == ({path for path, item in files.items()
                                if item.get("visibility") == "reviewer"} | {rounds.PROTOCOL}),
                   "Allowed navigation must exactly match package reviewer visibility")
    rounds.require(set(plan["instruction_paths"]) == {
        path for path in allowed if files[path]["role"] == "instructions"},
        "Instruction paths differ from reviewer-facing instruction pins")
    instruction_templates(root, plan)
    rounds.require(rounds.PROTOCOL in allowed, "Original protocol must remain reviewer-facing")
    for case in manifest["cases"]:
        rounds.require(case.get("reviewer_view_path") in allowed
                       and case["packet_path"] not in allowed,
                       "Case views must be visible; original packets are mechanical inputs")
        for eid in case["evidence_ids"]:
            matches = [item for item in files.values() if eid in item.get("evidence_ids", [])]
            rounds.require(len(matches) == 1, "Evidence binding is missing or ambiguous")
            item = matches[0]
            rounds.require(item["path"] in allowed or item["path"] == case["packet_path"],
                           "Case evidence is outside declared navigation")
    sessions = plan["sessions"]
    rounds.require(isinstance(sessions, list) and sessions, "Missing planned sessions")
    ids, roots, clones = set(), [], set()
    for session in sessions:
        rounds.require(isinstance(session, dict) and set(session) == SESSION_KEYS,
                       "Invalid planned session fields")
        rid = session["reviewer_id"]
        rounds.require(isinstance(rid, str) and re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", rid)
                       and rid not in ids, "Invalid or repeated reviewer ID")
        ids.add(rid)
        clone = absolute(session["workdir"])
        fresh = absolute(session["session_root"])
        output = absolute(session["output_root"])
        rounds.require(fresh != clone and fresh.is_relative_to(clone)
                       and output.parent == fresh, "Session/output roots must be inside their clone")
        rounds.require(clone not in clones, "Independent sessions require distinct reviewer clones")
        rounds.require(all(not fresh.is_relative_to(other) and not other.is_relative_to(fresh)
                           for other in roots), "Session roots overlap")
        clones.add(clone)
        roots.append(fresh)
    if adjudication:
        adjudication_inputs(root, plan, manifest, files)
    return plan, manifest, {"manifest": {"path": manifest_path,
                                          "sha256": replay["manifest_sha256"]},
                            "instructions": pin(root, plan_path)}


def generated_prompt(plan, manifest, session, bindings, templates):
    """There is no user-supplied launch prose or hardcoded historical round path."""
    rounds.require(plan["phase"] in PHASES, "Unsupported scientific phase")
    context = {"round_id": plan["round_id"], "phase": plan["phase"], **bindings,
               "session": session, "allowed_read_paths": plan["read_paths"],
               "instruction_paths": plan["instruction_paths"],
               "cases": [{key: case[key] for key in
                          ("case_id", "occurrence_id", "reviewer_view_path", "evidence_ids")}
                         for case in manifest["cases"]]}
    adjudication = plan["phase"] == "evidence_adjudication"
    if adjudication:
        rounds.require(plan.get("schema") == ADJUDICATION_PLAN_SCHEMA
                       and isinstance(plan.get("adjudication"), dict),
                       "Missing typed adjudication inputs")
        # Do not expose prompts, native logs or other initial-session mechanics.
        inputs = plan["adjudication"]
        context["initial_results"] = {
            "initial_manifest": inputs["initial_manifest"],
            "runtime_git_head": inputs["runtime_git_head"],
            "reviewers": [{key: entry[key] for key in
                           ("position", "reviewer", "saved_at", "matrix", "receipt", "seal")}
                          for entry in inputs["reviewers"]],
            "comparison": inputs["comparison"],
        }
    replacements = {"manifest_path": bindings["manifest"]["path"],
                    "round_id": plan["round_id"], **session}
    rendered = []
    for template in templates:
        body = template["text"]
        for key, value in replacements.items():
            body = body.replace("{{" + key + "}}", value)
        rendered.append(body)
    phase = (
        "Independently assess all cases on all six axes under the original protocol. Do not "
        "delegate ratings or read another session. Author complete canonical drafts and proof "
        "sidecars before sealing. Validate exactly one fresh-47 draft and inspect persisted "
        "artifacts before the remaining cases. Use seal_m5_round03_initial_20261116.py "
        "validate/seal/check, with this bound manifest and this session's output root. Preserve "
        "rejected attempts; never change scientific judgments to pass transport. After sealing, "
        "save/check the canonical reviews with python -B -m edgemech.occurrence_review, first "
        "fresh-47 and then the remaining cases only after inspecting actual YAML/Markdown. "
        "All expected slots, failures and unattempted blockers remain in the denominator."
    )
    if adjudication:
        phase = (
            "You are the separate evidence adjudicator; the initial results are intentionally "
            "visible only in this phase. Read both bound original matrices, their authored "
            "drafts and proof sidecars, seals and the replayed comparison. Independently audit "
            "the evidence for every resolved claim and model label, including agreements, "
            "and record a reasoned disposition for every initial disagreement. Preserve both "
            "original identities, timestamps, ratings and failures. Do not edit or reseal "
            "initial results, average labels, invent consensus or reinterpret an initial "
            "failure as a pass. Author separate final assessments with exact evidence "
            "bindings under the supplied output root. Use only package-pinned adjudication "
            "helpers and phase templates; missing final-output tooling is a blocker. "
            "For final scientific authoring, proof checks and scoring, use "
            "initial_results.initial_manifest so every initial matrix and evidence binding "
            "retains its original package identity. The phase manifest is the launch/input "
            "envelope, not a replacement scientific package or rewritten initial matrix. "
            "Validate exactly one final fresh-47 draft and proof sidecar, inspect the persisted "
            "draft, proofs and validation receipt, then author the remaining nine. All ten "
            "final drafts use the shared canonical review schema and the full occurrence "
            "profile. Author final-authored-config.json and all sixty final assessments in "
            "the separate audit; validate the complete set without making another initial "
            "seal. The frozen finalizer must require exact draft/proof parity with the final "
            "audit and bind every final input in its immutable validation and accounting "
            "receipts. Final canonical persistence is not attempted: no ten additional "
            "final canonical saves are required. The canonical-pair denominator remains "
            "the original twenty initial pairs. This draft-only final stage does not waive "
            "the separate passing same-clone production save/readback canary required "
            "before this adjudicator invocation. "
            "Report every unchanged gate, unsupported label, unresolved disagreement, "
            "failed or unattempted canonical slot and evidence replay result. No result "
            "of this invocation alone authorizes retained-cohort review or expansion."
        )
    text = (
        "You are a fresh scientific " + ("adjudicator" if adjudication else "reviewer")
        + ". This generated invocation binds the exact package "
        "and session below; operational readiness is not scientific approval.\n\n"
        + json.dumps(context, indent=2, sort_keys=True) + "\n\n"
        "Run calibration_round_20261116.py verify --manifest using exactly the manifest.path "
        "above. The package-pinned instruction templates are rendered below; use these bound "
        "renderings rather than supplying your own substitutions. The allowed_read_paths list is the "
        "complete scientific navigation boundary. Other package files are mechanical replay "
        "inputs only: do not print their hidden contents. Do not follow source links, retrieve "
        "new evidence, inspect Git history, issues, coordinator notes, operational judgments, "
        "or unlisted directories. Record unavoidable exposure and deviations.\n\n"
        + "\n\n".join(rendered) + "\n\n"
        + phase + "\n\n"
        "Keep claim, literature, source-fidelity, relation, subject-node and object-node "
        "assessments distinct, using the pinned shared schemas and instruction assets. "
        "Original occurrence, predicate, endpoints and source version stay fixed. Source-report "
        "support does not establish biological truth or independent literature support. "
        "Missing access is not refutation. Existing thresholds and scope remain unchanged.\n\n"
        "Determine actual model/session from this output root's events.jsonl using "
        "identify_m5_worker_20261116.py. Use the supplied reviewer_id consistently; "
        "configured_default is not an actual model. Same-model agreement is operational only. "
        "Use short literal quotations; the 25-word limit per source is shared across the whole "
        "package's reviewers and cases. Do not omit counterevidence to meet that limit.\n\n"
        "Use only frozen maintained execution helpers and production CLIs. Do not create new "
        "execution code, edit inputs/runtime/environment, waive a gate or alter an initial seal. "
        "Author JSON/Markdown data only under the supplied output root, apart from canonical "
        "review saves inside this clone. Helper gaps go to the coordinator. Record commands, "
        "exit statuses, exact paths/hashes, exposure, blockers and all expected slots in "
        "reviewer-result.json. Save a complete durable FINAL_REPORT.md in the output root. "
        "The launcher owns final.md; your final message must be self-contained. No commits, "
        "issues, messages, merges, publication, graph admission or expansion.\n"
    )
    return text.encode()


def session_marker(contract_path, value):
    return {"schema": SCHEMA, "invocation": contract_path,
            "invocation_sha256": rounds.digest(json.dumps(value, sort_keys=True).encode()),
            "session": value["session"]}


def check_phase_runtime(plan, runtime):
    if plan["phase"] == "evidence_adjudication":
        rounds.require(runtime.get("git_head") == plan["adjudication"]["runtime_git_head"],
                       "Adjudicator Git head differs from the frozen initial runtime")


def validate(root, contract_path, *, manifest_path, runtime, receipt_path, output, prompt,
             fresh=True):
    value = rounds.read(root, contract_path)
    rounds.require(set(value) == {"schema", "purpose", "round_id", "manifest", "instructions",
                                 "runtime", "production_receipt", "session", "prompt"}
                   and value["schema"] == SCHEMA and value["purpose"] == PURPOSE,
                   "Invalid scientific invocation contract")
    rounds.require(value["manifest"]["path"] == manifest_path,
                   "Supplied package differs from scientific invocation")
    plan, manifest, bindings = checked_plan(root, manifest_path, value["instructions"]["path"])
    rounds.require(value["round_id"] == manifest["round_id"]
                   and all(value[key] == binding for key, binding in bindings.items()),
                   "Invocation package/instruction hash or ID mismatch")
    rounds.require(value["runtime"] == runtime, "Scientific invocation runtime changed")
    check_phase_runtime(plan, runtime)
    receipt_path = Path(receipt_path).absolute()
    rounds.require(receipt_path.is_relative_to(root), "Receipt belongs to another clone")
    rounds.require(value["production_receipt"] == pin(root, str(receipt_path.relative_to(root))),
                   "Scientific invocation production receipt changed")
    session = value["session"]
    rounds.require(session in plan["sessions"] and session["workdir"] == str(root),
                   "Invocation session differs from package plan or clone")
    session_root = absolute(session["session_root"])
    rounds.require(session["output_root"] == str(output), "Invocation output root differs")
    if fresh:
        rounds.require(not session_root.exists(), "Scientific session root already exists")
    else:
        marker = session_root / "invocation.json"
        rounds.require(marker.is_file() and not marker.is_symlink()
                       and json.loads(marker.read_bytes()) == session_marker(contract_path, value),
                       "Scientific session reservation changed")
    expected = generated_prompt(plan, manifest, session, bindings, instruction_templates(root, plan))
    rounds.require(value["prompt"] == pin(root, str(Path(prompt).relative_to(root)))
                   and Path(prompt).read_bytes() == expected,
                   "Scientific prompt differs from verified structured instructions")
    return {"path": contract_path, "sha256": pin(root, contract_path)["sha256"],
            "manifest": value["manifest"], "session": session,
            "scope": "invocation_coherence_not_scientific_approval"}


def reserve(root, contract_path):
    value = rounds.read(root, contract_path)
    target = absolute(value["session"]["session_root"])
    target.mkdir(mode=0o700, parents=True, exist_ok=False)
    rounds.write(root, str((target / "invocation.json").relative_to(root)),
                 session_marker(contract_path, value))


def prepare(root, manifest_path, plan_path, reviewer_id, receipt_path, output):
    import run_m5_review_worker_20261116 as worker

    plan, manifest, bindings = checked_plan(root, manifest_path, plan_path)
    matches = [item for item in plan["sessions"] if item["reviewer_id"] == reviewer_id]
    rounds.require(len(matches) == 1 and matches[0]["workdir"] == str(root),
                   "No planned session for reviewer in this clone")
    session = matches[0]
    rounds.require(not absolute(session["session_root"]).exists(),
                   "Scientific session root already exists")
    receipt = rounds.read(root, receipt_path)
    environment = worker.child_environment(root)
    runtime = {"git_head": subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip(),
        "helper_sha256": worker.digest(worker.HELPER),
        "codex_path": receipt["codex_path"], "codex_sha256": worker.digest(receipt["codex_path"]),
        **worker.runtime_bindings(root, environment), **worker.repository_bindings(root)}
    check_phase_runtime(plan, runtime)
    worker.verify_receipt(root / receipt_path, runtime, root, environment,
                          reviewer_package=manifest_path)
    prompt_path = output + ".prompt.md"
    for path in (output, prompt_path):
        rounds.require(not rounds.safe(root, path, exists=False).exists(), "Invocation output exists")
        rounds.require(not (root / path).is_relative_to(absolute(session["session_root"])),
                       "Instruction artifacts must be outside the reserved fresh session")
    value = {"schema": SCHEMA, "purpose": PURPOSE, "round_id": manifest["round_id"],
             **bindings, "runtime": runtime, "production_receipt": pin(root, receipt_path),
             "session": session}
    prompt = generated_prompt(plan, manifest, session, bindings, instruction_templates(root, plan))
    value["prompt"] = {"path": prompt_path, "sha256": rounds.digest(prompt)}
    rounds.write(root, prompt_path, raw=prompt)
    rounds.write(root, output, value)
    return validate(root, output, manifest_path=manifest_path, runtime=runtime,
                    receipt_path=root / receipt_path, output=Path(session["output_root"]),
                    prompt=root / prompt_path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=rounds.ROOT)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--instruction-plan", required=True)
    parser.add_argument("--reviewer-id", required=True)
    parser.add_argument("--production-receipt", required=True)
    parser.add_argument("--output", required=True, help="Exclusive repository-relative invocation JSON")
    args = parser.parse_args()
    print(json.dumps(prepare(args.root.resolve(), args.manifest, args.instruction_plan,
                             args.reviewer_id, args.production_receipt, args.output), sort_keys=True))


if __name__ == "__main__":
    main()
