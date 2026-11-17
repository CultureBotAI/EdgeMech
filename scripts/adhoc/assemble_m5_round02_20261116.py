#!/usr/bin/env python3
"""Assemble explicit raw evidence for round02; never import historical ratings."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import calibration_round_20261116 as rounds

ROOT = rounds.ROOT
OLD = Path("/Users/marcin/agent-work/EdgeMech/m5-calibration-20261116")
RUN = Path(".temp/m5-round02-worker-20261116")
PACKAGE = RUN / "round02-final"
VIEWS = RUN / "package/views"
OLD_MANIFEST = Path(".temp/m5-worker-run-20261116/package/round-01-manifest.json")
OLD_HASH = "14175634b794a90124bb66a458af3c30f23ca40e10731c4ba89226134a89f4ab"
EXCLUDED_IDS = {"maintained-maintained-biolink-revalidation", "fresh04-identity-context"}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def retained_manifest():
    raw = (OLD / OLD_MANIFEST).read_bytes()
    rounds.require(digest(raw) == OLD_HASH, "Historical evidence manifest changed")
    return json.loads(raw)


def selected_inputs(manifest, case_ids):
    ids = {eid for case in manifest["cases"] if case["case_id"] in case_ids
           for eid in case["evidence_ids"]}
    return [item for item in manifest["files"]
            if item["role"] in {"authority", "evidence"}
            and set(item.get("evidence_ids", [])) & ids
            and not set(item.get("evidence_ids", [])) & EXCLUDED_IDS]


def private_references(value):
    """Close literal private navigation links without granting them evidence roles."""
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"path", "result_path", "private_receipt"} and isinstance(item, str):
                if item.startswith(".temp/"):
                    yield item
            else:
                yield from private_references(item)
    elif isinstance(value, list):
        for item in value:
            yield from private_references(item)


def copy_pin(item, destination):
    source = rounds.safe(OLD, item["path"])
    raw = source.read_bytes()
    rounds.require(digest(raw) == item["sha256"], "Retained evidence bytes changed")
    path = str(destination / (digest(raw) + source.suffix))
    target = rounds.safe(ROOT, path, exists=False)
    if target.exists():
        rounds.require(target.read_bytes() == raw, "Content-addressed evidence differs")
    else:
        rounds.write(ROOT, path, raw=raw)
    return {**item, "path": path, "original_path": item["path"],
            "retained_manifest_sha256": OLD_HASH}


def canary():
    dest = PACKAGE / "retained-canary"
    rounds.require(not (ROOT / dest).exists(), "Canary output already exists")
    pins = [copy_pin(p, dest) for p in selected_inputs(retained_manifest(), {"fresh-47"})]
    receipt = {"case_id": "fresh-47", "helper_sha256": digest(Path(__file__).read_bytes()),
               "inputs": pins, "scientific_ratings": 0}
    rounds.write(ROOT, str(PACKAGE / "retained-canary-receipt.json"), receipt)
    return receipt


def verify_canary():
    receipt = rounds.read(ROOT, str(PACKAGE / "retained-canary-receipt.json"))
    rounds.require(receipt["helper_sha256"] == digest(Path(__file__).read_bytes()),
                   "Assembly helper changed after canary")
    expected = selected_inputs(retained_manifest(), {"fresh-47"})
    rounds.require(len(expected) == len(receipt["inputs"]), "Canary coverage changed")
    for pin, source in zip(receipt["inputs"], expected, strict=True):
        rounds.require(pin["original_path"] == source["path"]
                       and pin["sha256"] == source["sha256"]
                       and digest(rounds.safe(ROOT, pin["path"]).read_bytes()) == pin["sha256"],
                       "Canary copy changed")
    return receipt


def assemble():
    verify_canary()
    old = retained_manifest()
    cohort = rounds.read(ROOT, rounds.COHORT)
    files = {}
    cases = {}

    def add(item, selected):
        item = dict(item)
        item.pop("case_ids", None)
        path = item["path"]
        raw = rounds.safe(ROOT, path).read_bytes()
        if item.get("sha256"):
            rounds.require(item["sha256"] == digest(raw), "Supplied evidence hash changed")
        if path in files:
            rounds.require(files[path] == item, "Conflicting file declaration")
        files[path] = item
        for cid in selected:
            for eid in item.get("evidence_ids", []):
                if eid not in cases[cid]["evidence_ids"]:
                    cases[cid]["evidence_ids"].append(eid)

    retained_id_map = {eid: f"r02-retained-{i:03d}" for i, eid in enumerate(sorted({
        eid for item in selected_inputs(old, {c["case_id"] for c in cohort["cases"]})
        for eid in item["evidence_ids"]}), 1)}
    for c in cohort["cases"]:
        cid = c["case_id"]
        packet = f".temp/edge-calibration-20261115/{cid}/packet.json"
        cases[cid] = {"case_id": cid, "packet_path": packet, "evidence_ids": [],
                      "reviewer_view_path": str(VIEWS / cid / "view.json")}
        add({"path": packet, "role": "packet", "evidence_ids": ["packet-" + cid],
             "visibility": "mechanical_replay_only"}, [cid])
        for name in ("occurrence.json", "source.json", "receipt.json"):
            add({"path": f".temp/edge-calibration-20261115/{cid}/{name}",
                 "role": "original_input", "visibility": "mechanical_replay_only"}, [])
        for name in ("view.json", "receipt.json"):
            add({"path": str(VIEWS / cid / name), "role": "reviewer_view"}, [])
    for item in selected_inputs(old, set(cases)):
        pin = copy_pin(item, PACKAGE / "retained")
        selected = [c["case_id"] for c in old["cases"]
                    if set(c["evidence_ids"]) & set(item["evidence_ids"])]
        pin["evidence_ids"] = [retained_id_map[eid] for eid in item["evidence_ids"]]
        # Historical path names can themselves contain prior interpretation.
        pin.pop("original_path")
        add(pin, selected)
    for folder in ("local-authorities", "relation-authorities"):
        for pin in rounds.read(ROOT, str(RUN / folder / "package-inputs.json")):
            add(pin, pin["case_ids"])
    for path in [RUN / "local-authorities/FACT_INDEX.json",
                 RUN / "relation-authorities/neutral-index.json",
                 RUN / "literature/search-scope.json"]:
        add({"path": str(path), "role": "instructions"}, [])
        for reference in sorted(set(private_references(rounds.read(ROOT, str(path))))):
            if reference not in files:
                add({"path": reference, "role": "navigation_receipt",
                     "scope": "Source/provenance navigation only; no independent evidence ID"}, [])
    rounds.write(ROOT, str(RUN / (PACKAGE.name + "-evidence-id-map-private.json")), retained_id_map)
    # Literal provider text from a fresh primary catalog response, without coordinator prose.
    provider = rounds.read(ROOT, str(RUN / "literature/tavily-lpsn775534.json"))
    response = provider["result"]["structuredContent"]["results"][0]
    path = str(PACKAGE / "lpsn775534-current.txt")
    rounds.write(ROOT, path, raw=response["raw_content"].encode())
    add({"path": path, "role": "authority", "version": "LPSN retrieved 2026-11-17",
         "evidence_ids": ["r02-lpsn775534"]}, ["fresh-32"])
    for path in sorted(rounds.RUNTIME_PATHS | {
            "scripts/adhoc/prepare_m5_reviewer_views_20261116.py",
            "scripts/adhoc/prepare_m5_round02_views_20261116.py",
            "scripts/adhoc/assemble_m5_round02_20261116.py",
            "scripts/adhoc/run_m5_review_worker_20261116.py"}):
        add({"path": path, "role": "proof_adapter"}, [])
    profile = RUN / "package/profile-for-reviewers.md"
    rounds.write(ROOT, str(PACKAGE / "profile-for-reviewers.md"),
                 raw=rounds.safe(ROOT, str(profile)).read_bytes())
    for path in [str(PACKAGE / "profile-for-reviewers.md"),
                 "scripts/adhoc/m5_review_20261116/round02-blinded-review.md",
                 "docs/record-reviews.md"]:
        add({"path": path, "role": "instructions"}, [])
    guide = {
        "round_id": "m5-calibration-20261116-round02", "ratings": None,
        "cases": [{"case_id": cid, "inputs": [
            {key: pin[key] for key in ("path", "role", "version", "evidence_ids") if key in pin}
            for pin in files.values() if set(pin.get("evidence_ids", [])) & set(c["evidence_ids"])
            and pin["role"] != "packet"]} for cid, c in cases.items()],
        "search_limits": "Retained round01 raw evidence copied after SHA-256 verification. "
            "New primary authorities and bounded literature searches are separately pinned. "
            "The 1997 Desulfobacter paper DOI was located but DOI/ADS extraction failed; "
            "Valency's five semantic fallback results concerned other taxa. "
            "No authenticated general fulltext, paid research or email request was used. "
            "Missing original paper is not refutation. Historical source identities remain unchanged.",
        "source_version_limits": "Producer commits, source hashes, ontology versions and candidate "
            "corrections are distinct. Read exact evidence versions; do not infer a sampled generating "
            "commit from a matching token hash or from a current convention.",
        "blinding": "Original packets and cohort are retained for mechanical replay. Read only "
            "versioned reviewer views and listed raw authorities/evidence; coordinator leads and "
            "reports, historical ratings and operational canary judgments are excluded.",
    }
    path = str(PACKAGE / "evidence-guide.json")
    rounds.write(ROOT, path, guide)
    add({"path": path, "role": "instructions"}, [])
    config = {"round_id": guide["round_id"], "files": list(files.values()),
              "cases": list(cases.values())}
    rounds.write(ROOT, str(PACKAGE / "freeze-config.json"), config)
    return {"cases": len(cases), "files": len(files), "scientific_ratings": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("canary", "check-canary", "assemble"))
    args = parser.parse_args()
    result = {"canary": canary, "check-canary": verify_canary, "assemble": assemble}[args.operation]()
    print(json.dumps(result, sort_keys=True))
