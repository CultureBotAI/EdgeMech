#!/usr/bin/env python3
"""Publish bounded M5 execution accounting without raw evidence or event logs.

Inputs are retained reviewer results, launcher metadata, sealed matrices and the
coordinator's independent canonical replay receipt. This performs fresh hash,
identity, category and completion checks; it never changes authored judgments.
Run --plan before the one exclusive --run publication. Existing outputs are never
overwritten. No process is launched and no credentials or environment values are read.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).absolute().parents[2]
PRIVATE = ".temp/m5-worker-run-20261116"
PUBLIC = "artifacts/m5-calibration-20261116"
SPEC = importlib.util.spec_from_file_location(
    "m5_execution_rounds", ROOT / "scripts/adhoc/calibration_round_20261116.py")
rounds = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rounds)
require = rounds.require
EXPECTED_ERROR = ("kg_microbe_governance.artifacts.scripts.record_review.ReviewError: "
                  "Supported-as-stated cannot conceal incorrect/unassessed original modeling")


def pin(root, path, expected=None):
    raw = rounds.safe(root, path).read_bytes()
    sha = rounds.digest(raw)
    require(expected is None or expected == sha, f"Input hash changed: {path}")
    return {"path": path, "sha256": sha}


def read(root, path):
    return rounds.read(root, path)


def projected_categories(review):
    result = {}
    for assessment in review["assessments"]:
        dims = {d["name"]: d["value"] for d in assessment["dimensions"]}
        require(dims["axis"] not in result, "Repeated canonical axis")
        result[dims["axis"]] = dims["category"]
    require(result.keys() == rounds.CATEGORIES.keys(), "Incomplete canonical axes")
    return result


def safe_launch(root, worker):
    path = f"{PRIVATE}/{worker}/metadata.json"
    metadata = read(root, path)
    require(metadata["status"] in {"completed", "passed"} and metadata["exit_code"] == 0,
            "A worker is not successfully finished")
    command = metadata["command"]
    expected = ["exec", "--approve-for-me", "--json", "--color", "never", "-C",
                str(root), "-o", str(root / PRIVATE / worker / "final.md"), "-"]
    require(Path(command[0]).name == "codex" and command[1:] == expected,
            "Unexpected launcher parameters; do not publish arbitrary command arguments")
    fields = ("role", "status", "exit_code", "started_at", "finished_at", "git_head",
              "ending_git_head", "launcher_pid", "worker_pid", "codex_sha256",
              "helper_sha256", "python_sha256", "lock_sha256", "distributions_sha256",
              "environment_sha256", "prompt_sha256", "executed_prompt_sha256")
    return {"worker": worker, "metadata": pin(root, path),
            **{key: metadata[key] for key in fields},
            "launch_model_setting": metadata["model"],
            "command_settings": {"program": "codex", "operation": "exec",
                                 "automatic_approval_review": True, "json_events": True,
                                 "color": "never", "prompt_via_stdin": True,
                                 "workdir": ".", "output": f"{PRIVATE}/{worker}/final.md"}}


def canonical_row(root, rid, row, replay, labels):
    cid = row["case_id"]
    if rid == "reviewer-a":
        authored = row["private_review_input"]
        proofs = row["private_proof_sidecar"]
        save_path = row["save_command"]["receipt"]["path"]
    else:
        authored = {"path": row["review_input"], "sha256": row["review_input_sha256"]}
        proofs = {"path": row["proof_sidecar"], "sha256": row["proof_sidecar_sha256"]}
        save_path = row["save"]["receipt_path"]
    authored = pin(root, **{"path": authored["path"], "expected": authored["sha256"]})
    proofs = pin(root, proofs["path"], proofs["sha256"])
    review = read(root, authored["path"])
    require(projected_categories(review) == labels[cid], "Authored categories changed after seal")
    require(review["completion"] == "partial", "Unexpected authored completion")
    save = read(root, save_path)
    result = {"reviewer_id": rid, "case_id": cid, "review_id": row["review_id"],
              "authored_input": authored, "proof_sidecar": proofs,
              "save_command_receipt": pin(root, save_path), "save_exit_status": save["exit_status"],
              "authored_categories_match_sealed_matrix": True,
              "authored_completion": review["completion"],
              "save_finished_at": save.get("finished_at", save.get("at"))}
    if cid == "fresh-05":
        error = save["stderr"].strip().splitlines()[-1]
        require(save["exit_status"] == 1 and error == EXPECTED_ERROR,
                "Unexpected fresh-05 save outcome")
        require(replay["status"] == "unavailable", "Failed save unexpectedly has replay")
        # Path enumeration includes ignored files, unlike Git-aware searches.
        matches = list((root / "reviews/structured").rglob(row["review_id"]))
        require(not matches, "Failed fresh-05 unexpectedly has a persisted canonical directory")
        result.update(persisted=False, canonical_replay="unavailable", exact_error=error,
                      missing_pair_search="Path.rglob under reviews/structured includes ignored files")
        return result
    require(save["exit_status"] == 0 and replay["status"] == "passed"
            and replay["exit_status"] == 0, "Expected canonical save/replay did not pass")
    require(replay["completion"] == "partial" and replay["categories_match_sealed_matrix"] is True,
            "Canonical replay did not preserve the partial matrix")
    current = [pin(root, item["path"], item["sha256"]) for item in replay["current_file_pins"]]
    yaml_path, md_path = row["canonical_yaml"], row["canonical_markdown"]
    expected_yaml = row.get("yaml_sha256", row.get("canonical_yaml_sha256"))
    expected_md = row.get("markdown_sha256", row.get("canonical_markdown_sha256"))
    yaml_pin, md_pin = pin(root, yaml_path, expected_yaml), pin(root, md_path, expected_md)
    saved = yaml.safe_load(rounds.safe(root, yaml_path).read_bytes())
    require(saved["review_id"] == row["review_id"] and saved["completion"] == "partial",
            "Persisted review identity/completion differs")
    require(projected_categories(saved) == labels[cid] == replay["persisted_categories"],
            "Persisted categories differ from original matrix")
    require(yaml_pin in current and md_pin in current and proofs in current,
            "Independent replay does not bind persisted pair and proof sidecar")
    result.update(persisted=True, completion=saved["completion"],
                  canonical_pair=[yaml_pin, md_pin], canonical_replay="passed",
                  canonical_publication_status="retained_privately_uncommitted_not_public",
                  independent_replay_file_pins=current,
                  persisted_categories_match_sealed_matrix=True,
                  required_unavailable_checks=sum(c.get("required") is True
                                                  and c["status"] == "unavailable"
                                                  for c in saved["checks"]))
    return result


def build(root):
    manifest_path = f"{PRIVATE}/package/round-01-manifest.json"
    comparison_path = f"{PRIVATE}/initial-comparison.json"
    replay_path = f"{PRIVATE}/adjudication/canonical-replay.json"
    identity_path = f"{PRIVATE}/actual-runtime-identities.json"
    manifest = read(root, manifest_path)
    comparison = rounds.compare(root, manifest_path, f"{PRIVATE}/reviewer-a/initial-matrix.json",
                                f"{PRIVATE}/reviewer-b/initial-matrix.json")
    require(comparison == read(root, comparison_path), "Initial comparison changed")
    require(rounds.safe(root, comparison_path).read_bytes()
            == rounds.safe(root, f"{PUBLIC}/round-01-initial-comparison.json").read_bytes(),
            "Public/private comparison bytes differ")
    identities = read(root, identity_path)
    require({i["worker"] for i in identities} == {"reviewer-a", "reviewer-b", "runtime-canary-03"},
            "Unexpected runtime identity inventory")
    require(len(identities) == 3, "Repeated runtime identity")
    require(all(i["matching_session_logs"] == 1 and len(i["models"]) == 1 for i in identities)
            and len({i["thread_id"] for i in identities}) == 3,
            "Ambiguous or repeated worker runtime identity")
    identity_map = {i["worker"]: i for i in identities}
    replay = read(root, replay_path)
    replay_map = {(r["reviewer_id"], r["case_id"]): r for r in replay["checks"]}
    expected_cases = {c["case_id"] for c in manifest["cases"]}
    require(len(replay["checks"]) == 20 and set(replay_map) ==
            {(rid, cid) for rid in ("reviewer-a", "reviewer-b") for cid in expected_cases},
            "Independent canonical replay coverage is incomplete")
    results, rows, receipt_copies = [], [], []
    for rid in ("reviewer-a", "reviewer-b"):
        result_path = f"{PRIVATE}/{rid}/reviewer-result.json"
        report = read(root, result_path)
        matrix_path = f"{PRIVATE}/{rid}/initial-matrix.json"
        matrix, labels = rounds.sealed_matrix(root, manifest_path, matrix_path)
        matrix_pin = pin(root, matrix_path, report["matrix_sha256"])
        public_matrix = f"{PUBLIC}/{rid}-initial.json"
        require(rounds.safe(root, matrix_path).read_bytes() == rounds.safe(root, public_matrix).read_bytes(),
                "Public initial matrix differs from privately sealed bytes")
        seal_path = matrix_path + ".receipt.json"
        receipt_copies.append((seal_path, f"{PUBLIC}/{rid}-initial.json.receipt.json"))
        identity = identity_map[rid]
        require(identity["matching_session_logs"] == 1 and len(identity["models"]) == 1,
                "Runtime identity is ambiguous")
        require(identity["thread_id"] == matrix["reviewer"]["session_id"]
                and identity["models"][0]["model"] == matrix["reviewer"]["model"],
                "Runtime and reviewer identity differ")
        canonical = report.get("canonical_reviews", report.get("canonical_results"))
        require(len(canonical) == 10 and {r["case_id"] for r in canonical} == expected_cases,
                "Reviewer canonical-attempt accounting differs from cohort")
        case_rows = [canonical_row(root, rid, row, replay_map[rid, row["case_id"]], labels)
                     for row in canonical]
        rows.extend(case_rows)
        inspection_path = (report["fresh_47_production_canary"]["inspection"]["path"]
                           if rid == "reviewer-a" else report["fresh47_canary_inspection"])
        inspection = read(root, inspection_path)
        canary = next(row for row in case_rows if row["case_id"] == "fresh-47")
        require({p["sha256"] for p in canary["canonical_pair"]}
                == {inspection["yaml_sha256"], inspection["markdown_sha256"]},
                "Canary inspection does not bind the persisted pair")
        canary_time = datetime.fromisoformat(canary["save_finished_at"].replace("Z", "+00:00"))
        require(all(canary_time < datetime.fromisoformat(row["save_finished_at"].replace("Z", "+00:00"))
                    for row in case_rows if row["case_id"] != "fresh-47"),
                "Fresh-47 was not the first canonical save attempt")
        results.append({"reviewer": matrix["reviewer"], "runtime_thread_id": identity["thread_id"],
                        "actual_model": identity["models"][0]["model"],
                        "runtime_identity_matching_logs": identity["matching_session_logs"],
                        "launcher": safe_launch(root, rid), "reviewer_result": pin(root, result_path),
                        "private_initial_matrix": matrix_pin, "public_initial_matrix": pin(root, public_matrix),
                        "public_private_initial_matrix_bytes_identical": True,
                        "initial_matrix_seal_receipt": pin(root, seal_path),
                        "fresh47_canary": {"inspection_receipt": pin(root, inspection_path),
                                           "inspection_attestation": inspection["inspected"],
                                           "save_precedes_other_case_attempts": True,
                                           "scope": "single production canonical save and persisted-pair replay; partial review, not scientific calibration"}})
    persisted = [row for row in rows if row["persisted"]]
    require(len(persisted) == 18 and all(row["completion"] == "partial" for row in persisted),
            "Unexpected persisted canonical coverage")
    require((replay["passed"], replay["failed"], replay["unavailable"], replay["denominator"])
            == (18, 0, 2, 20), "Canonical replay summary differs from its rows")
    runtime_canary = safe_launch(root, "runtime-canary-03")
    runtime_canary["actual_identity"] = {"thread_id": identity_map["runtime-canary-03"]["thread_id"],
                                        "model": identity_map["runtime-canary-03"]["models"][0]["model"]}
    report = {"schema": "edgemech-m5-calibration-execution/v1", "round_id": manifest["round_id"],
              "package_sha256": comparison["package_sha256"],
              "accounting_helper": pin(root, "scripts/adhoc/summarize_m5_execution_20261116.py"),
              "source_receipts": [pin(root, p) for p in (manifest_path, identity_path, comparison_path, replay_path)],
              "reviewers": results, "runtime_launcher_canary": runtime_canary,
              "all_listed_worker_jobs_completed": True, "running_jobs": [],
              "canonical_attempts": rows,
              "canonical_accounting": {"expected": 20, "persisted": 18, "save_failed": 2,
                                       "independent_replay_passed": 18, "persisted_replay_denominator": 18,
                                       "all_expected_replay_denominator": 20, "unavailable": 2,
                                       "partial_reviews": 18, "completed_scientific_reviews": 0},
              "canonical_publication": {
                  "status": "all_18_pairs_retained_privately_uncommitted",
                  "public_canonical_pairs": 0,
                  "reason": "Combined authority quotations exceed the per-authority-version short-quote budget; original bytes remain unchanged. This artifact contains hashes and statuses, not the quoted reviews.",
              },
              "private_provenance": {
                  "original_reviewer_helpers": [
                      pin(root, "scripts/adhoc/m5_reviewer_a_20261116.py",
                          read(root, f"{PRIVATE}/reviewer-a/reviewer-result.json")["helper"]["sha256"]),
                      pin(root, "scripts/adhoc/reviewer_b_calibration_20261116.py"),
                  ],
                  "publication_status": "Original authoring helpers remain at their exact paths, privately retained and uncommitted because they contain quotation literals.",
                  "reproduction": "The published accounting helper reads sealed matrices and immutable authored/proof inputs; it never executes original authoring helpers, authors ratings or changes judgments.",
              },
              "initial_agreement": comparison["initial_gates"],
              "same_model_reviewers": comparison["same_model"], "scientific_calibration_passed": False,
              "limitations": ["Both reviewers used the same model; this is operational agreement, not independent expert validation.",
                              "Historical exposure is preserved verbatim in each sealed reviewer identity.",
                              "Partial canonical save and technical replay do not establish scientific support or calibration passage.",
                              "Both fresh-05 save failures retain their exact initial judgments and authored/proof bytes.",
                              "All listed worker processes completed; this report starts no continuing job.",
                              "This summary rechecks hashes, identities and category preservation; canonical profile execution is evidenced by the separately retained replay receipt."]}
    return report, receipt_copies


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", action="store_true")
    mode.add_argument("--run", action="store_true")
    args = parser.parse_args()
    report, copies = build(ROOT)
    output = f"{PUBLIC}/round-01-execution.json"
    targets = [output, *(dst for _, dst in copies)]
    require(all(not rounds.safe(ROOT, path, exists=False).exists() for path in targets),
            "Publication output already exists; preserve it")
    if args.run:
        for src, dst in copies:
            rounds.write(ROOT, dst, raw=rounds.safe(ROOT, src).read_bytes())
            require(rounds.safe(ROOT, dst).read_bytes() == rounds.safe(ROOT, src).read_bytes(),
                    "Published receipt copy differs")
        rounds.write(ROOT, output, report)
    print(json.dumps({"status": "published" if args.run else "plan_only", "output": output,
                      "receipt_copies": [dst for _, dst in copies],
                      "canonical_accounting": report["canonical_accounting"],
                      "scientific_calibration_passed": False}, sort_keys=True))


if __name__ == "__main__":
    main()
