#!/usr/bin/env python3
"""Freeze an engineering-only M5 prerequisite bundle (#203/#205/#206; 2026-11-17).

Inputs: exact retained manifest and conservative operational fixture, plus this
committed clone's runtime. Outputs: private immutable copied evidence, v4 views,
runtime transition ledger, manifest and production authoring inputs. Never rates
science, changes an old package, retrieves papers or authorizes reviewer launch.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

import author_m5_review_data_20261116 as author
import calibration_round_20261116 as rounds
import prepare_m5_future_views_20261117 as views
import run_m5_review_worker_20261116 as worker

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "edgemech-prerequisite-package/v1"
FIXED = {rounds.PROTOCOL, rounds.COHORT, "docs/record-review-profile.md",
         "scripts/adhoc/calibration_round_20261116.py"}
REFRESH_ROLES = {"proof_adapter", "profile", "round_helper", "instructions"}


def checked_document(root, path, expected):
    raw = rounds.safe(root, path).read_bytes()
    rounds.require(rounds.digest(raw) == expected, f"Source hash changed: {path}")
    return json.loads(raw, object_pairs_hook=rounds.unique_object)


def plan(root, source_root, manifest_path, manifest_sha, spec_path, spec_sha, output):
    rounds.require(root.resolve() != source_root.resolve(), "Use a fresh destination clone")
    rounds.require(Path(output).parts and Path(output).parts[0] == ".temp"
                   and len(Path(output).parts) > 1, "Output must be a private .temp directory")
    rounds.require(not rounds.safe(root, output, exists=False).exists(), "Output already exists")
    ignored = subprocess.run(["git", "check-ignore", "--quiet", "--no-index", output], cwd=root)
    rounds.require(ignored.returncode == 0, "Output must be gitignored")
    rounds.require(not subprocess.check_output(
        ["git", "-C", str(root), "status", "--porcelain", "--untracked-files=no"],
        text=True).strip(), "Commit runtime before staging")
    origin = subprocess.check_output(
        ["git", "-C", str(root), "remote", "get-url", "origin"], text=True).strip()
    rounds.require(origin == "https://github.com/CultureBotAI/EdgeMech.git", "Noncanonical origin")
    manifest = checked_document(source_root, manifest_path, manifest_sha)
    spec = checked_document(source_root, spec_path, spec_sha)
    rounds.require(spec["review"].get("scientific_review") is False
                   and spec["review"]["verdict"] == "not_assessed", "Scientific fixture forbidden")
    unknown = {"NOT_ASSESSABLE", "UNAVAILABLE", "UNRESOLVED"}
    rounds.require(len(spec["assessments"]) == 6
                   and all(a["category"] in unknown for a in spec["assessments"]),
                   "Operational fixture must remain unresolved on every axis")
    tracked = set(subprocess.check_output(
        ["git", "-C", str(root), "ls-files"], text=True).splitlines())
    actions = []
    for pin in manifest["files"]:
        path = pin["path"]
        if pin["role"] == "instructions":
            actions.append({"path": path, "action": "omit_historical_instructions",
                            "previous_sha256": pin["sha256"]})
            continue
        if path in tracked:
            raw = rounds.safe(root, path).read_bytes()
            current = rounds.digest(raw)
            rounds.require(current == pin["sha256"] or pin["role"] in REFRESH_ROLES,
                           f"Non-runtime tracked evidence changed: {path}")
            actions.append({"path": path, "action": "bind_current_runtime",
                            "previous_sha256": pin["sha256"], "sha256": current})
        else:
            raw = rounds.safe(source_root, path).read_bytes()
            rounds.require(rounds.digest(raw) == pin["sha256"], f"Retained evidence changed: {path}")
            target = rounds.safe(root, path, exists=False)
            rounds.require(not target.exists(), f"Evidence destination already exists: {path}")
            actions.append({"path": path, "action": "copy_exact_retained_input",
                            "sha256": pin["sha256"]})
    return manifest, spec, tracked, actions


def metadata_preflight(root, args):
    rounds.text(args.package_id, "package ID")
    rounds.require(re.fullmatch(r"[0-9]{8}T[0-9]{6}Z-[a-z0-9][a-z0-9-]*", args.review_id),
                   "Review ID needs a UTC timestamp and safe suffix")
    timestamp = datetime.strptime(args.timestamp, "%Y-%m-%dT%H:%M:%SZ")
    rounds.require(timestamp.strftime("%Y%m%dT%H%M%SZ") == args.review_id.split("-", 1)[0],
                   "Review ID and timestamp differ")
    target = rounds.safe(root, f"reviews/structured/{args.review_id}/review.yaml", exists=False)
    rounds.require(not target.parent.exists(), "Canonical review destination already exists")
    for path in args.prerequisite_document:
        rounds.safe(root, path)


def verify_transition(root, ledger):
    current_head = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    rounds.require(current_head == ledger["runtime_commit"], "Runtime commit changed during staging")
    rounds.require(not subprocess.check_output(
        ["git", "-C", str(root), "status", "--porcelain", "--untracked-files=no"],
        text=True).strip(), "Tracked runtime changed during staging")
    rounds.require(worker.execution_inventory(root) == ledger["execution_inventory"],
                   "Execution inventory changed during staging")
    for item in [*ledger["actions"], *ledger["prerequisite_documents"]]:
        if item.get("action") == "omit_historical_instructions":
            continue
        rounds.require(rounds.digest(rounds.safe(root, item["path"]).read_bytes()) == item["sha256"],
                       f"Planned input changed during staging: {item['path']}")


def prepare(args):
    root, source = args.root.resolve(), args.source_root.resolve()
    metadata_preflight(root, args)
    manifest, spec, tracked, actions = plan(root, source, args.source_manifest,
        args.source_sha256, args.operational_spec, args.spec_sha256, args.output)
    ledger = {"schema": SCHEMA, "package_purpose": "engineering_prerequisites",
              "scientific_authorization": False, "source_manifest": {
                  "path": args.source_manifest, "sha256": args.source_sha256},
              "source_fixture": {"path": args.operational_spec, "sha256": args.spec_sha256},
              "runtime_commit": subprocess.check_output(
                  ["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip(),
              "execution_inventory": worker.execution_inventory(root),
              "prerequisite_documents": [{"path": path, "sha256": rounds.digest(
                  rounds.safe(root, path).read_bytes())} for path in args.prerequisite_document],
              "actions": actions,
              "scope": "Complete retained byte bindings; unresolved scientific witnesses remain missing."}
    if args.plan:
        return {"status": "plan_only", "files": len(actions), "cases": len(manifest["cases"]),
                "runtime_commit": ledger["runtime_commit"], "scientific_authorization": False}
    prefix = Path(args.output)
    files = {}
    for pin, action in zip(manifest["files"], actions, strict=True):
        if action["action"] == "omit_historical_instructions":
            continue
        if action["action"] == "copy_exact_retained_input":
            # Check again immediately before persistence; never accept a changed source.
            raw = rounds.safe(source, pin["path"]).read_bytes()
            rounds.require(rounds.digest(raw) == pin["sha256"], "Source changed after plan")
            rounds.write(root, pin["path"], raw=raw)
        if pin["path"] not in FIXED:
            files[pin["path"]] = {k: v for k, v in pin.items() if k != "sha256"}
    # Freeze every maintained execution input, including newly added helpers.
    for execution_pin in worker.execution_inventory(root):
        path = execution_pin["path"]
        if path not in FIXED:
            files.setdefault(path, {"path": path, "role": "proof_adapter"})
    for path in ("uv.lock", "pyproject.toml"):
        files.setdefault(path, {"path": path, "role": "proof_adapter"})
    instruction = "scripts/adhoc/m5_review_20261116/replay-canary.md"
    files[instruction] = {"path": instruction, "role": "instructions"}
    for path in args.prerequisite_document:
        rounds.safe(root, path)
        files[path] = {"path": path, "role": "coordinator_prerequisite_document",
                       "visibility": "coordinator_only"}
    cases = copy.deepcopy(manifest["cases"])
    for case in cases:
        path = str(prefix / "views" / case["case_id"] / "view.json")
        rounds.write(root, path, views.projection(rounds.read(root, case["packet_path"])))
        case["reviewer_view_path"] = path
        files[path] = {"path": path, "role": "reviewer_view"}
    ledger_path = str(prefix / "binding-transition.json")
    rounds.write(root, ledger_path, ledger)
    files[ledger_path] = {"path": ledger_path, "role": "provenance_receipt"}
    review = spec["review"]
    review.update(review_id=args.review_id, title="Prerequisite canonical transport canary")
    spec["reviewer_identity"].update(id="prerequisite-operational-fixture", model="configured_default",
                                      session_id="operational-fixture-no-scientific-session")
    review["reviewer"].update(identity="prerequisite-operational-fixture", model="configured_default")
    spec["accessed_at"] = review["started_at"] = review["finished_at"] = args.timestamp
    spec_path = str(prefix / "operational-spec.json")
    rounds.write(root, spec_path, spec)
    files[spec_path] = {"path": spec_path, "role": "operational_fixture",
                        "visibility": "coordinator_only"}
    config_path, target_manifest = str(prefix / "freeze-config.json"), str(prefix / "manifest.json")
    config = {"round_id": args.package_id, "package_purpose": "engineering_prerequisites",
              "files": list(files.values()), "cases": cases}
    rounds.write(root, config_path, config)
    verify_transition(root, ledger)
    frozen = rounds.freeze(root, config_path, target_manifest)
    verified = rounds.verify(root, target_manifest)
    verify_transition(root, ledger)
    authored = author.assemble(root, target_manifest, spec_path, str(prefix / "operational"))
    verify_transition(root, ledger)
    result = {"schema": SCHEMA, "status": "prepared", "manifest": frozen,
              "verification": verified, "operational": authored,
              "scientific_authorization": False}
    rounds.write(root, str(prefix / "preparation-receipt.json"), result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--source-manifest", required=True)
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--operational-spec", required=True)
    parser.add_argument("--spec-sha256", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--package-id", required=True)
    parser.add_argument("--review-id", required=True)
    parser.add_argument("--timestamp", required=True)
    parser.add_argument("--prerequisite-document", action="append", default=[])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", action="store_true")
    mode.add_argument("--run", action="store_true")
    print(json.dumps(prepare(parser.parse_args()), indent=2))


if __name__ == "__main__":
    main()
