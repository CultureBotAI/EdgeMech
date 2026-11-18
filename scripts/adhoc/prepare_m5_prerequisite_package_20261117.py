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
import stat
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import author_m5_review_data_20261116 as author
import calibration_round_20261116 as rounds
import prepare_calibration_20261115 as bootstrap
import prepare_m5_future_views_20261117 as views
import run_m5_review_worker_20261116 as worker

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "edgemech-prerequisite-package/v1"
FIXED = {rounds.PROTOCOL, rounds.COHORT, "docs/record-review-profile.md",
         "scripts/adhoc/calibration_round_20261116.py"}
REFRESH_ROLES = {"proof_adapter", "profile", "round_helper", "instructions"}
BOOTSTRAP_ROOT = bootstrap.PRIVATE / bootstrap.CANARY
BOOTSTRAP_RECEIPT = str(BOOTSTRAP_ROOT / "receipt.json")
BOOTSTRAP_NAMES = {"occurrence.json", "source.json", "packet.json"}


def checked_document(root, path, expected):
    raw = rounds.safe(root, path).read_bytes()
    rounds.require(rounds.digest(raw) == expected, f"Source hash changed: {path}")
    return json.loads(raw, object_pairs_hook=rounds.unique_object)


def complete_bootstrap_manifest(root, source_root, manifest, receipt_sha):
    """Bind exact retained preparation; never regenerate or re-date its receipt (#212)."""
    receipt = checked_document(source_root, BOOTSTRAP_RECEIPT, receipt_sha)
    cases = [case for case in manifest["cases"] if case["case_id"] == bootstrap.CANARY]
    rounds.require(len(cases) == 1 and receipt.get("case_id") == bootstrap.CANARY
                   and receipt.get("occurrence_id") == cases[0]["occurrence_id"]
                   and receipt.get("cohort_id") == bootstrap.COHORT_ID
                   and receipt.get("profile") == "edgemech-calibration-preparation/v1",
                   "Bootstrap receipt identity differs")
    rounds.require(receipt.get("configuration") == bootstrap.configuration(root),
                   "Retained bootstrap configuration differs; new preparation required")
    rounds.require(receipt.get("scientific_status") == "unassessed"
                   and receipt.get("kg_admissions") == 0
                   and receipt.get("native_capability_enabled") is False
                   and receipt.get("canary_receipt") is None, "Invalid bootstrap capability")
    rounds.require(set(receipt["artifacts"]) == BOOTSTRAP_NAMES,
                   "Bootstrap artifact inventory differs")
    complete = copy.deepcopy(manifest)
    pins = {item["path"]: item for item in complete["files"]}
    rounds.require(len(pins) == len(complete["files"]), "Repeated source manifest path")
    for name, pin in receipt["artifacts"].items():
        path = str(BOOTSTRAP_ROOT / name)
        rounds.require(pin.get("path") == path and path in pins
                       and pin.get("sha256") == pins[path]["sha256"],
                       "Bootstrap artifact differs from retained manifest")
        rounds.require(rounds.digest(rounds.safe(source_root, path).read_bytes()) == pin["sha256"],
                       "Retained bootstrap artifact changed")
        pins[path]["required_mode"] = "0600"
    if BOOTSTRAP_RECEIPT in pins:
        rounds.require(pins[BOOTSTRAP_RECEIPT]["sha256"] == receipt_sha,
                       "Bootstrap receipt differs from retained manifest")
        pins[BOOTSTRAP_RECEIPT]["required_mode"] = "0600"
    else:
        complete["files"].append({"path": BOOTSTRAP_RECEIPT, "sha256": receipt_sha,
                                  "role": "bootstrap_receipt", "visibility": "coordinator_only",
                                  "required_mode": "0600"})
    public_path, public_sha = bootstrap.PUBLIC["fresh"]
    rounds.require(rounds.digest(rounds.safe(source_root, public_path).read_bytes()) == public_sha
                   and rounds.digest(rounds.safe(root, public_path).read_bytes()) == public_sha,
                   "Bootstrap public occurrence projection changed")
    if public_path in pins:
        rounds.require(pins[public_path]["sha256"] == public_sha,
                       "Bootstrap public projection differs from retained manifest")
    else:
        complete["files"].append({"path": public_path, "sha256": public_sha,
                                  "role": "bootstrap_public_projection",
                                  "visibility": "coordinator_only"})
    return complete


def plan(root, source_root, manifest_path, manifest_sha, spec_path, spec_sha, output,
         *, bootstrap_receipt_sha256=None):
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
    if bootstrap_receipt_sha256 is not None:
        manifest = complete_bootstrap_manifest(root, source_root, manifest,
                                               bootstrap_receipt_sha256)
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
                            "sha256": pin["sha256"],
                            **({"required_mode": pin["required_mode"]}
                               if "required_mode" in pin else {})})
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
    if "bootstrap" in ledger:
        directory = rounds.safe(root, ledger["bootstrap"]["case_directory"], exists=False)
        rounds.require(directory.is_dir() and stat.S_IMODE(directory.stat().st_mode)
                       == int(ledger["bootstrap"]["directory_mode"], 8),
                       "Bootstrap directory mode changed")
    for item in [*ledger["actions"], *ledger["prerequisite_documents"]]:
        if item.get("action") == "omit_historical_instructions":
            continue
        rounds.require(rounds.digest(rounds.safe(root, item["path"]).read_bytes()) == item["sha256"],
                       f"Planned input changed during staging: {item['path']}")
        if "required_mode" in item:
            rounds.require(stat.S_IMODE((root / item["path"]).stat().st_mode)
                           == int(item["required_mode"], 8), "Bootstrap file mode changed")


def copy_retained(root, source, pin):
    raw = rounds.safe(source, pin["path"]).read_bytes()
    rounds.require(rounds.digest(raw) == pin["sha256"], "Source changed after plan")
    rounds.write(root, pin["path"], raw=raw)
    if "required_mode" in pin:
        path = rounds.safe(root, pin["path"])
        path.chmod(int(pin["required_mode"], 8))
        rounds.require(path.read_bytes() == raw, "Bootstrap bytes changed during mode setup")


def check_bootstrap(root):
    """The same free maintained checker used by the actual durable worker launcher."""
    directory = root / BOOTSTRAP_ROOT
    rounds.require(stat.S_IMODE(directory.stat().st_mode) == 0o700,
                   "Bootstrap directory must remain mode 0700")
    command = [sys.executable, "-B", str(root / "scripts/adhoc/prepare_calibration_20261115.py"),
               "--check", bootstrap.CANARY]
    record, receipt = worker.production_validator("bootstrap-preparation-check", command,
                                                   root, worker.child_environment(root))
    rounds.require(receipt == rounds.read(root, BOOTSTRAP_RECEIPT),
                   "Bootstrap checker returned another receipt")
    return record


def prepare(args):
    root, source = args.root.resolve(), args.source_root.resolve()
    metadata_preflight(root, args)
    rounds.text(args.bootstrap_receipt_sha256, "bootstrap receipt SHA256")
    manifest, spec, tracked, actions = plan(root, source, args.source_manifest,
        args.source_sha256, args.operational_spec, args.spec_sha256, args.output,
        bootstrap_receipt_sha256=args.bootstrap_receipt_sha256)
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
              "bootstrap": {"receipt_path": BOOTSTRAP_RECEIPT,
                            "receipt_sha256": args.bootstrap_receipt_sha256,
                            "case_directory": str(BOOTSTRAP_ROOT), "directory_mode": "0700",
                            "artifact_mode": "0600", "archive_root": str(bootstrap.ARCHIVE),
                            "private_upstream_inputs": rounds.read(
                                source, BOOTSTRAP_RECEIPT)["private_upstream_inputs"]},
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
            copy_retained(root, source, pin)
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
    bootstrap_check = check_bootstrap(root)
    frozen = rounds.freeze(root, config_path, target_manifest)
    verified = rounds.verify(root, target_manifest)
    verify_transition(root, ledger)
    authored = author.assemble(root, target_manifest, spec_path, str(prefix / "operational"))
    verify_transition(root, ledger)
    result = {"schema": SCHEMA, "status": "prepared", "manifest": frozen,
              "verification": verified, "operational": authored,
              "bootstrap_check": bootstrap_check,
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
    parser.add_argument("--bootstrap-receipt-sha256", required=True,
                        help="Exact original fresh-47 preparation receipt SHA256")
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
