"""Initial seals reject authored/proof drift before it becomes historical evidence."""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest
from test_calibration_round import round_inputs  # noqa: F401

from edgemech.occurrence_review import CATEGORIES, DETAILS

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/adhoc"))
SPEC = importlib.util.spec_from_file_location(
    "initial_seal", ROOT / "scripts/adhoc/seal_m5_round03_initial_20261116.py")
SEAL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SEAL)


@pytest.fixture
def authored_round(round_inputs, monkeypatch):  # noqa: F811
    rounds, root, _, _, package, put = round_inputs
    monkeypatch.setattr(SEAL, "rounds", rounds)
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    (root / ".gitignore").write_text(".temp/\n")
    shutil.copyfile(ROOT / SEAL.HELPER, root / SEAL.HELPER)
    package = deepcopy(package)
    package["round_id"] = "m5-calibration-20261116-round03"
    package["files"].append({"path": SEAL.HELPER, "role": "proof_adapter"})
    for case in package["cases"]:
        case["evidence_ids"].append(case["case_id"] + "-source")
        next(p for p in package["files"] if p["path"] == case["packet_path"])["evidence_ids"] = [
            case["case_id"] + "-source"]
    put("package-2.json", package)
    rounds.freeze(root, "package-2.json", "manifest-2.json")
    manifest = rounds.read(root, "manifest-2.json")
    identity = {"id": "reviewer-a", "model": "actual-test-model", "session_id": "actual-test-session",
                "historical_exposure": "Synthetic fixture; no scientific judgments"}
    config = {"reviewer": identity, "canonical_identity": "reviewer-a", "cases": []}
    for case in manifest["cases"]:
        cid, oid, packet_path = case["case_id"], case["occurrence_id"], case["packet_path"]
        packet = rounds.read(root, packet_path)
        proof_path, review_path = f"cases/{cid}/proofs.json", f"cases/{cid}/review.json"
        source_pin = SEAL.pin(root, packet_path)
        proof = {"evidence_id": "source", "kind": "packet", "input": source_pin,
                 "scope": "exact", "scope_rationale": "Exact synthetic packet",
                 "support": "supports", "axes": ["source_fidelity"],
                 "inspected_extent": "Complete synthetic packet", "reference": packet_path,
                 "manifest_evidence_id": cid + "-source"}
        put(proof_path, {"profile": "edgemech-occurrence-review/v1", "occurrence_id": oid,
                         "reviewer": identity, "proofs": [proof]})
        labels = {"claim": "INSUFFICIENT_EVIDENCE", "literature": "UNAVAILABLE",
                  "relation": "UNRESOLVED", "subject_node": "UNRESOLVED",
                  "object_node": "UNRESOLVED", "source_fidelity": "SUPPORTED"}
        assessments = []
        for axis, category in labels.items():
            ids = ["source"] if axis == "source_fidelity" else []
            dims = {"axis": axis, "category": category, "scope": "Original synthetic occurrence",
                    **{key: "Explicit synthetic limit" for key in DETAILS[axis]}}
            assessments.append({"assessment_id": axis, "area": "evidence", "topic": axis,
                                "outcome": CATEGORIES[axis][category], "summary": "Authored fixture",
                                "target_ids": [oid], "evidence_ids": ids,
                                "dimensions": [{"name": key, "value": value, "definition": key,
                                                "evidence_ids": ids} for key, value in dims.items()]})
        source_inputs = {p["path"]: p for p in packet["inputs"].values()}
        source_inputs.update({packet_path: source_pin, proof_path: SEAL.pin(root, proof_path)})
        review = {"schema_version": "1.0.0", "review_id": "20000101T000000Z-" + cid,
                  "kind": "record", "repository": "CultureBotAI/EdgeMech", "title": "Fixture",
                  "started_at": "2000-01-01T00:00:00Z", "finished_at": "2000-01-01T00:00:00Z",
                  "reviewer": {"identity": "reviewer-a", "model": identity["model"], "kind": "agent",
                               "independence": "independent", "independence_basis": "Fixture only"},
                  "skill": "edgemech-occurrence-review/v1", "completion": "partial",
                  "verdict": "needs_curation", "scientific_review": True, "summary": "Fixture",
                  "source": {"git_revision": "a" * 40, "state": "working_tree", "inputs": [
                      {**p, "role": "fixture"} for p in source_inputs.values()]},
                  "scope": {"description": "Fixture", "selection": "Fixture", "coverage": "full",
                            "population_size": 1, "reviewed_target_ids": [oid]},
                  "targets": [{"target_id": oid, "path": packet_path, "selector": "occurrence_id=" + oid,
                               "label": "Fixture", "kind": "snapshot_row", "ownership_note": "Fixture"}],
                  "checks": [{"check_id": "fixture", "name": "Fixture", "status": "unavailable",
                              "required": True, "target_ids": [oid], "summary": "Explicit fixture limit"}],
                  "evidence": [{"evidence_id": "source", "kind": "record_content", "reference": packet_path,
                                "locator": "original occurrence", "accessed_at": "2000-01-01T00:00:00Z",
                                "support": "supports", "summary": "Fixture", "snapshot_sha256": source_pin["sha256"]}],
                  "assessments": assessments, "findings": [], "actions": [], "limitations": ["Fixture"]}
        put(review_path, review)
        config["cases"].append({"case_id": cid, "review": review_path, "proofs": proof_path})
    put("authored.json", config)
    return root, config, put


def run_seal(data):
    return SEAL.seal(data[0], "manifest-2.json", "authored.json", ".temp/initial")


def test_complete_initial_seal_derives_all_axes_and_replays_without_persisting(authored_round):
    root, _, _ = authored_round
    result = run_seal(authored_round)
    assert result["status"] == "passed" and result["cases"] == 10 and result["authored_axes"] == 60
    assert result["canonical_persistence_checked"] is False and not (root / "reviews").exists()
    matrix = SEAL.rounds.read(root, ".temp/initial/matrix.json")
    source = matrix["cases"][0]["assessments"][-1]
    assert source["evidence_ids"] == [matrix["cases"][0]["case_id"] + "-source"]
    assert source["rationale"] == "Authored fixture"
    assert SEAL.check(root, ".temp/initial/initial-seal.json") == result
    with pytest.raises(ValueError, match="already exists"):
        run_seal(authored_round)


@pytest.mark.parametrize("damage", ["missing_case", "duplicate_case", "wrong_model", "wrong_session",
                                   "wrong_packet", "unmapped_source", "omitted_evidence", "unassessed"])
def test_incomplete_or_unbound_authored_set_never_seals(authored_round, damage):
    root, config, put = authored_round
    first = config["cases"][0]
    review = SEAL.rounds.read(root, first["review"])
    sidecar = SEAL.rounds.read(root, first["proofs"])
    if damage == "missing_case":
        config["cases"].pop()
    elif damage == "duplicate_case":
        config["cases"][-1] = dict(first)
    elif damage == "wrong_model":
        review["reviewer"]["model"] = "another-model"
    elif damage == "wrong_session":
        sidecar["reviewer"]["session_id"] = "another-session"
    elif damage == "wrong_packet":
        review["targets"][0]["path"] = "cases/another/packet.json"
    elif damage == "unmapped_source":
        sidecar["proofs"][0]["manifest_evidence_id"] = "paper"
    elif damage == "omitted_evidence":
        assessment = review["assessments"][-1]
        assessment["evidence_ids"] = []
        for dimension in assessment["dimensions"]:
            dimension["evidence_ids"] = []
    else:
        assessment = review["assessments"][0]
        next(d for d in assessment["dimensions"] if d["name"] == "category")["value"] = "UNASSESSED"
    put(first["proofs"], sidecar)
    next(p for p in review["source"]["inputs"] if p["path"] == first["proofs"]).update(
        SEAL.pin(root, first["proofs"]))
    put(first["review"], review)
    put("authored.json", config)
    with pytest.raises(ValueError):
        run_seal(authored_round)
    assert not (root / ".temp/initial").exists()


@pytest.mark.parametrize("target", ["draft", "proofs", "source", "matrix", "seal", "config"])
def test_postseal_augmentation_cannot_pass_as_unchanged_initial_evidence(authored_round, target):
    root, config, _ = authored_round
    run_seal(authored_round)
    paths = {"draft": config["cases"][0]["review"], "proofs": config["cases"][0]["proofs"],
             "source": "authority.txt", "matrix": ".temp/initial/matrix.json",
             "seal": ".temp/initial/initial-seal.json", "config": "authored.json"}
    path = root / paths[target]
    path.chmod(0o600)
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="changed"):
        SEAL.check(root, ".temp/initial/initial-seal.json")


@pytest.mark.parametrize("damage", ["public", "not_ignored", "identity"])
def test_private_destination_and_unambiguous_reviewer_required(authored_round, damage):
    root, config, put = authored_round
    output = ".temp/initial"
    if damage == "public":
        output = "artifacts/initial"
    elif damage == "not_ignored":
        (root / ".gitignore").write_text("")
    else:
        config["canonical_identity"] = "another-persona"
        put("authored.json", config)
    with pytest.raises(ValueError, match="private|Git-ignored|Canonical identity"):
        SEAL.seal(root, "manifest-2.json", "authored.json", output)
    assert not (root / output).exists()


def add_direct_authority(data, source_path="authority.txt", version="fixture-1"):
    """Author valid synthetic canonical data directly, bypassing convenience helpers."""
    from edgemech.literature_cache import LiteratureCache, verify_quote

    root, config, put = data
    entry = config["cases"][0]
    manifest = SEAL.rounds.read(root, "manifest-2.json")
    case = next(c for c in manifest["cases"] if c["case_id"] == entry["case_id"])
    if source_path == "case_packet":
        source_path = case["packet_path"]
    frozen = next(p for p in manifest["files"] if p["path"] == source_path)
    raw = (root / source_path).read_bytes()
    text = raw.decode()
    span = verify_quote(LiteratureCache._document(
        {"response_sha256": frozen["sha256"]}, "authority_text", text), text[:20])
    review = SEAL.rounds.read(root, entry["review"])
    sidecar = SEAL.rounds.read(root, entry["proofs"])
    proof = {"evidence_id": "direct-authority", "kind": "authority",
             "input": {"path": source_path, "sha256": frozen["sha256"]},
             "manifest_evidence_id": frozen["evidence_ids"][0], "version": version,
             "scope": "context", "scope_rationale": "Synthetic unresolved context",
             "support": "context_only", "axes": ["relation"],
             "reference": source_path, "inspected_extent": "Synthetic source fragment",
             **{key: span[key] for key in ("start", "end", "extractor", "text_sha256")}}
    sidecar["proofs"].append(proof)
    put(entry["proofs"], sidecar)
    review["evidence"].append({
        "evidence_id": proof["evidence_id"], "kind": "authority", "reference": source_path,
        "locator": f"synthetic fragment; chars {span['start']}:{span['end']}",
        "accessed_at": "2000-01-01T00:00:00Z", "support": "context_only",
        "summary": "Synthetic context", "snapshot_sha256": frozen["sha256"], "quote": span["quote"]})
    relation = next(a for a in review["assessments"] if a["assessment_id"] == "relation")
    relation["evidence_ids"] = [proof["evidence_id"]]
    for dimension in relation["dimensions"]:
        dimension["evidence_ids"] = [proof["evidence_id"]]
    inputs = {p["path"]: p for p in review["source"]["inputs"]}
    inputs[source_path] = {**proof["input"], "role": "synthetic source"}
    inputs[entry["proofs"]] = {**SEAL.pin(root, entry["proofs"]), "role": "synthetic proofs"}
    review["source"]["inputs"] = list(inputs.values())
    put(entry["review"], review)
    return entry, case, review, sidecar, manifest


@pytest.mark.parametrize("source,version,message", [
    ("authority.txt", "unreviewed-version", "version differs"),
    ("evidence.txt", "fixture-1", "authority role"),
    ("case_packet", "fixture-1", "authority role"),
])
def test_direct_authored_role_version_bypass_never_seals(authored_round, source, version, message):
    entry, case, review, _, _ = add_direct_authority(authored_round, source, version)
    # The base occurrence profile has no manifest parameter. Demonstrate that
    # these otherwise valid direct inputs reach the missing package boundary.
    checked = SEAL.validate_occurrence_review(authored_round[0], review,
                                              case["packet_path"], entry["proofs"])
    assert checked["verified_evidence"] == 2
    with pytest.raises(ValueError, match=message):
        run_seal(authored_round)
    assert not (authored_round[0] / ".temp/initial").exists()


def test_exact_direct_authority_can_seal_without_convenience_authoring_helper(authored_round):
    add_direct_authority(authored_round)
    assert run_seal(authored_round)["status"] == "passed"


@pytest.mark.parametrize("damage", ["unreferenced_version", "case_id", "duplicate_frozen_match",
                                   "input_hash", "wrong_packet", "packet_role", "paper_role"])
def test_every_proof_has_frozen_case_role_and_version_even_without_axis_projection(authored_round, damage):
    _, case, _, sidecar, manifest = add_direct_authority(authored_round)
    # This function consumes the entire sidecar, not any assessment's evidence
    # subset, so a proof omitted from a future projection cannot avoid checks.
    if damage == "unreferenced_version":
        sidecar["proofs"][-1]["version"] = "other"
    elif damage == "case_id":
        case["evidence_ids"] = [eid for eid in case["evidence_ids"] if eid != "authority"]
    elif damage == "duplicate_frozen_match":
        manifest["files"].append(deepcopy(next(p for p in manifest["files"] if p["path"] == "authority.txt")))
    elif damage == "input_hash":
        sidecar["proofs"][-1]["input"]["sha256"] = "0" * 64
    elif damage == "wrong_packet":
        case["packet_path"] = "another-case/packet.json"
    elif damage == "packet_role":
        next(p for p in manifest["files"] if p["path"] == case["packet_path"])["role"] = "evidence"
    else:
        sidecar["proofs"][-1]["kind"] = "jats"
    with pytest.raises(ValueError):
        SEAL.validate_frozen_proofs(sidecar, manifest, case)
