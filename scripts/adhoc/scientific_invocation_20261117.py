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
from pathlib import Path

import calibration_round_20261116 as rounds

PLAN_SCHEMA = "edgemech-scientific-instructions/v1"
TEMPLATE_SCHEMA = "edgemech-scientific-instruction-template/v1"
SCHEMA = "edgemech-scientific-invocation/v1"
PURPOSE = "scientific_calibration_candidate"
HELPER = "scripts/adhoc/scientific_invocation_20261117.py"
PHASES = {"blinded_initial_review"}
SESSION_KEYS = {"reviewer_id", "workdir", "session_root", "output_root"}
PLACEHOLDERS = {"manifest_path", "round_id", "workdir", "session_root", "output_root", "reviewer_id"}
# Invocation paths belong in typed placeholders, never in copied prose. Treat
# ambiguous slash expressions conservatively: templates can spell out “save and
# check” while source evidence retains its exact scientific text unchanged.
LITERAL_PATH = re.compile(r"[/\\]|\b(?:manifest|initial-seal|reviewer-result)\.json\b|"
                          r"\b(?:FINAL_REPORT|final)\.md\b")


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
    rounds.require(set(plan) == {"schema", "purpose", "round_id", "manifest_path", "phase",
                                "instruction_paths", "read_paths", "sessions"},
                   "Unexpected or missing scientific instruction fields")
    rounds.require(plan["schema"] == PLAN_SCHEMA and plan["purpose"] == PURPOSE,
                   "Invalid scientific instruction purpose or schema")
    rounds.require(plan["round_id"] == manifest["round_id"]
                   and plan["manifest_path"] == manifest_path,
                   "Instruction/package manifest ID or path mismatch")
    rounds.require(plan["phase"] in PHASES,
                   "Unsupported scientific phase; only blinded initial review is implemented")
    for name in ("read_paths", "instruction_paths"):
        values = plan[name]
        rounds.require(isinstance(values, list) and values
                       and all(isinstance(value, str) for value in values)
                       and len(values) == len(set(values)), "Invalid " + name)
    allowed = set(plan["read_paths"])
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
    text = (
        "You are a fresh scientific reviewer. This generated invocation binds the exact package "
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
