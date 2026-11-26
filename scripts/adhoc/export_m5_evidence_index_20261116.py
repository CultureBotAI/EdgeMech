#!/usr/bin/env python3
"""Export bounded public metadata from the verified private round01 guide.

No article bodies, raw catalog rows, historical ratings or new judgments leave
private staging. This index is a derivative, not a second evidence authority.
"""
import argparse
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).absolute().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "m5_index_rounds", ROOT / "scripts/adhoc/calibration_round_20261116.py")
rounds = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rounds)
MANIFEST = ROOT / ".temp/m5-worker-run-20261116/package/round-01-manifest.json"
GUIDE = ".temp/m5-worker-run-20261116/package/evidence-guide-v2.json"
OUTPUT = ROOT / "artifacts/m5-calibration-20261116/round-01-evidence-index.json"


def payload():
    manifest_path = str(MANIFEST.relative_to(ROOT))
    manifest_raw = rounds.safe(ROOT, manifest_path).read_bytes()
    manifest = json.loads(manifest_raw)
    guide_raw = rounds.safe(ROOT, GUIDE).read_bytes()
    pin = [x for x in manifest["files"] if x["path"] == GUIDE]
    if len(pin) != 1 or rounds.digest(guide_raw) != pin[0]["sha256"]:
        raise ValueError("Guide is not the frozen input")
    guide = json.loads(guide_raw)
    papers = []
    cases = []
    for case in guide["literature_cases"]:
        cases.append({key: case[key] for key in ["case_id", "occurrence_id", "search_scope",
                                                "unresolved_evidence_gap"]})
        for candidate in case["literature_candidates"]:
            papers.append({"case_id": case["case_id"], "evidence_id": candidate["evidence_id"],
                           "primary_identity": candidate["identity"],
                           "raw_sha256": candidate["raw_input"]["sha256"],
                           "text_sha256": candidate["text_sha256"],
                           "scope_rationale": candidate["scope_rationale"],
                           "limitations": candidate["limitations"]})
    result = {"round_id": manifest["round_id"],
              "package_sha256": rounds.digest(manifest_raw),
              "scope": "bounded metadata and evidence limits; no new axis ratings",
              "publications": papers, "literature_case_limits": cases,
              "current_taxonomy": [{key: item[key] for key in
                                    ["taxid", "raw_sha256", "retrieved", "version", "limits"]}
                                   for item in guide["taxonomy_authorities"]],
              "sampled_version_limit": guide["sampled_version_limit"],
              "structural_cases": guide["structural_cases"],
              "fresh14_scope": {key: guide["fresh14"][key] for key in
                                ["case_id", "occurrence_id", "sampled_ontology_version_status",
                                 "maintained_producer_commit", "modeling_convention_status"]}}
    return (json.dumps(result, indent=2, sort_keys=True) + "\n").encode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    raw = payload()
    relative = str(OUTPUT.relative_to(ROOT))
    if args.check:
        if rounds.safe(ROOT, relative).read_bytes() != raw:
            raise ValueError("Public index differs from frozen guide projection")
    else:
        rounds.write(ROOT, relative, raw=raw)
    print(OUTPUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
