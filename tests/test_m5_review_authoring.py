"""Exercise compact authored data through frozen inputs and real profile validation."""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest
from kg_microbe_reviews import ReviewError
from test_occurrence_review import case as case
from test_occurrence_review import install_abstract
from test_occurrence_review import report_case as report_case

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "scripts/adhoc/author_m5_review_data_20261116.py"


@pytest.fixture
def authoring():
    spec = importlib.util.spec_from_file_location("m5_review_authoring_test", HELPER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepare(module, case, monkeypatch):
    """Use the real freeze/verify, replacing only the preregistered test cohort pins."""
    root, review, sidecar = case
    root = root.resolve()
    rounds = module.rounds

    def put(path, value):
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(value))

    packet = json.loads((root / "packet.json").read_text())
    cid = "synthetic-case"
    original = {
        "case_id": cid, "occurrence_id": packet["occurrence_id"],
        "original_assertion": packet["original_assertion"],
        "endpoints": {side: {"private_record_sha256": packet["endpoints"][side]["record_sha256"]}
                      for side in ("subject", "object")},
    }
    put(rounds.PROTOCOL, {"cohort_id": "synthetic-authoring"})
    put(rounds.COHORT, {"cases": [original]})
    monkeypatch.setattr(rounds, "PINS", {
        path: rounds.digest((root / path).read_bytes())
        for path in (rounds.PROTOCOL, rounds.COHORT)
    })
    files = []
    for path in sorted(rounds.RUNTIME_PATHS | {
        "docs/record-review-profile.md", "scripts/adhoc/calibration_round_20261116.py",
    }):
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / path, root / path)
        if path in rounds.RUNTIME_PATHS:
            files.append({"path": path, "role": "proof_adapter"})
    (root / "instructions.md").write_text("Synthetic test instructions, no scientific rating.\n")
    (root / "unused-authority.txt").write_text("Synthetic unused authority.\n")
    files.extend([
        {"path": "instructions.md", "role": "instructions"},
        {"path": "unused-authority.txt", "role": "authority", "version": "unused-v1"},
        {"path": "source.json", "role": "source"},
    ])
    for proof in sidecar["proofs"]:
        item = {"path": proof["input"]["path"], "role": (
            "authority" if proof["kind"] == "authority" else "evidence"),
            "evidence_ids": [proof["evidence_id"]]}
        if proof["kind"] == "authority":
            item["version"] = proof["version"]
        files.append(item)
    put("config.json", {"round_id": "synthetic-authoring", "files": files,
                        "cases": [{"case_id": cid, "packet_path": "packet.json",
                                   "evidence_ids": [p["evidence_id"] for p in sidecar["proofs"]]}]})
    rounds.freeze(root, "config.json", "manifest.json")
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    (root / ".gitignore").write_text(".temp/\n")
    subprocess.run(["git", "-C", str(root), "remote", "add", "origin",
                    "https://github.com/CultureBotAI/EdgeMech.git"], check=True)
    subprocess.run(["git", "-C", str(root), "-c", "user.name=Fixture", "-c",
                    "user.email=fixture@example.invalid", "commit", "--allow-empty", "-qm", "Fixture"],
                   check=True)
    reserved = {"source", "targets", "assessments", "evidence", "kind", "repository", "skill"}
    metadata = {key: deepcopy(value) for key, value in review.items() if key not in reserved}
    metadata["reviewer"]["model"] = "synthetic-model"
    authored = {
        "case_id": cid, "review": metadata, "accessed_at": "2000-01-01T00:00:00Z",
        "reviewer_identity": {"id": metadata["reviewer"]["identity"], "model": "synthetic-model",
                              "session_id": "synthetic-session", "historical_exposure": "Test only"},
        "ownership_note": "Synthetic fixture; no maintained scientific owner",
        "proofs": [], "assessments": [],
    }
    canonical_evidence = {e["evidence_id"]: e for e in review["evidence"]}
    for proof in sidecar["proofs"]:
        item = {key: deepcopy(value) for key, value in proof.items()
                if key not in {"input", "text_sha256", "start", "end", "extractor"}}
        ev = canonical_evidence[proof["evidence_id"]]
        item.update(manifest_evidence_id=proof["evidence_id"], summary=ev["summary"],
                    locator=ev["locator"].split("; chars", 1)[0])
        if "quote" in ev:
            item["quote"] = ev["quote"]
        authored["proofs"].append(item)
    for assessment in review["assessments"]:
        dims = {d["name"]: d["value"] for d in assessment["dimensions"]}
        compact = {"axis": dims.pop("axis"), "category": dims.pop("category"),
                   "scope": dims.pop("scope"), "rationale": assessment["summary"],
                   "evidence_ids": deepcopy(assessment["evidence_ids"]), "dimensions": dims}
        for key in ("assertion_basis", "report_witnesses"):
            if key in assessment:
                compact[key] = deepcopy(assessment[key])
        authored["assessments"].append(compact)
    put(".temp/spec.json", authored)
    return root, authored, put


def run(module, root, authored, put, output=".temp/authored"):
    put(".temp/spec.json", authored)
    return module.assemble(root, "manifest.json", ".temp/spec.json", output)


def test_real_profile_preserves_all_authored_values(authoring, case, monkeypatch):
    root, authored, put = prepare(authoring, case, monkeypatch)
    original = deepcopy(authored)
    receipt = run(authoring, root, authored, put)
    review = json.loads((root / receipt["review"]["path"]).read_text())
    proofs = json.loads((root / receipt["proofs"]["path"]).read_text())
    assert authored == original
    assert receipt["status"] == "validated_draft_only"
    assert receipt["canonical_persistence"] == "not_attempted"
    assert receipt["scientific_approval"] is False
    assert proofs["reviewer"] == original["reviewer_identity"]
    for key, value in original["review"].items():
        assert review[key] == value
    for compact, canonical in zip(original["assessments"], review["assessments"], strict=True):
        dims = {d["name"]: d["value"] for d in canonical["dimensions"]}
        assert dims == {"axis": compact["axis"], "category": compact["category"],
                        "scope": compact["scope"], **compact["dimensions"]}
        assert canonical["summary"] == compact["rationale"]
        assert canonical["evidence_ids"] == compact["evidence_ids"]
    assert review["findings"] == original["review"]["findings"]
    assert not (root / "reviews").exists()


def test_packet_cannot_supply_literature_and_failed_attempt_is_retained(authoring, case, monkeypatch):
    root, authored, put = prepare(authoring, case, monkeypatch)
    authored["proofs"][1]["axes"].append("literature")
    authored["assessments"][1]["evidence_ids"].append("source")
    with pytest.raises(ReviewError):
        run(authoring, root, authored, put)
    assert (root / ".temp/authored/proofs.json").exists()
    assert (root / ".temp/authored/review.json").exists()
    assert not (root / ".temp/authored/draft-receipt.json").exists()


def test_ambiguous_primary_paper_is_rejected(authoring, case, monkeypatch):
    response = install_abstract(case)
    response["resultList"]["result"].append(deepcopy(response["resultList"]["result"][0]))
    response["hitCount"] = 2
    (case[0] / "abstract.json").write_text(json.dumps(response))
    root, authored, put = prepare(authoring, case, monkeypatch)
    with pytest.raises(ReviewError, match="one exact primary MED PMID result"):
        run(authoring, root, authored, put)


def test_report_groups_and_original_entities_survive_assembly(authoring, report_case, monkeypatch):
    root, authored, put = prepare(authoring, report_case, monkeypatch)
    receipt = run(authoring, root, authored, put)
    review = json.loads((root / receipt["review"]["path"]).read_text())
    sidecar = json.loads((root / receipt["proofs"]["path"]).read_text())
    assert review["assessments"][0]["assertion_basis"] == "source_report"
    assert review["assessments"][0]["report_witnesses"] == authored["assessments"][0]["report_witnesses"]
    assert sidecar["proofs"][-1]["original_entities"] == authored["proofs"][-1]["original_entities"]
    authored["assessments"][0]["report_witnesses"]["identity_evidence_ids"] = []
    with pytest.raises(ReviewError):
        run(authoring, root, authored, put, ".temp/missing-identity")


def test_successful_authored_outputs_cannot_be_overwritten(authoring, case, monkeypatch):
    root, authored, put = prepare(authoring, case, monkeypatch)
    run(authoring, root, authored, put)
    before = {p.name: p.read_bytes() for p in (root / ".temp/authored").iterdir()}
    authored["review"]["summary"] = "Different attempted summary"
    with pytest.raises(ValueError, match="new private"):
        run(authoring, root, authored, put)
    assert {p.name: p.read_bytes() for p in (root / ".temp/authored").iterdir()} == before


def test_evidence_not_allowed_for_case_is_rejected(authoring, case, monkeypatch):
    root, authored, put = prepare(authoring, case, monkeypatch)
    manifest = json.loads((root / "manifest.json").read_text())
    manifest["cases"][0]["evidence_ids"].remove("paper")
    (root / "manifest.json").chmod(0o600)
    put("manifest.json", manifest)
    with pytest.raises(ValueError, match="Evidence outside case"):
        run(authoring, root, authored, put)


def test_authority_version_must_match_frozen_manifest(authoring, report_case, monkeypatch):
    root, authored, put = prepare(authoring, report_case, monkeypatch)
    authored["proofs"][-1]["version"] = "v2"
    with pytest.raises(ValueError, match="Authority version differs"):
        run(authoring, root, authored, put)


def test_duplicate_axis_cannot_be_assembled(authoring, case, monkeypatch):
    root, authored, put = prepare(authoring, case, monkeypatch)
    authored["assessments"].append(deepcopy(authored["assessments"][0]))
    with pytest.raises(ValueError, match="Duplicate or unknown axis"):
        run(authoring, root, authored, put)


def test_session_identity_cannot_diverge_from_canonical_reviewer(authoring, case, monkeypatch):
    root, authored, put = prepare(authoring, case, monkeypatch)
    authored["reviewer_identity"]["model"] = "different-model"
    with pytest.raises(ValueError, match="identity/model differs"):
        run(authoring, root, authored, put)


def test_pinned_input_changes_fail_before_any_output(authoring, case, monkeypatch):
    root, authored, put = prepare(authoring, case, monkeypatch)
    (root / "paper.xml").write_text("Changed after freeze")
    with pytest.raises(ValueError, match="Pinned input changed"):
        run(authoring, root, authored, put)
    assert not (root / ".temp/authored").exists()


def test_multiple_quote_aliases_keep_complete_canonical_axis_proofs(authoring, case, monkeypatch):
    root, authored, put = prepare(authoring, case, monkeypatch)
    second = deepcopy(authored["proofs"][0])
    second.update(evidence_id="paper-second-span", quote="grew in defined conditions.")
    authored["proofs"].append(second)
    for axis in authored["assessments"][:2]:
        axis["evidence_ids"].append("paper-second-span")
    receipt = run(authoring, root, authored, put)
    saved = json.loads((root / receipt["review"]["path"]).read_text())
    sidecar = json.loads((root / receipt["proofs"]["path"]).read_text())
    assert saved["assessments"][0]["evidence_ids"] == ["paper", "paper-second-span"]
    assert [p["evidence_id"] for p in sidecar["proofs"]] == ["paper", "source", "paper-second-span"]
    spec = importlib.util.spec_from_file_location(
        "m5_initial_seal_projection_test", ROOT / "scripts/adhoc/seal_m5_round03_initial_20261116.py")
    seal = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(seal)
    manifest = json.loads((root / "manifest.json").read_text())
    projected = seal.project_case(saved, sidecar, manifest, manifest["cases"][0])
    assert projected["assessments"][0]["evidence_ids"] == ["paper"]
    # Matrix sources may deduplicate, but omitting a distinct applicable proof
    # from the canonical axis cannot pass the production validator.
    authored["assessments"][0]["evidence_ids"].remove("paper-second-span")
    with pytest.raises(ReviewError):
        run(authoring, root, authored, put, ".temp/missing-proof")


def test_spec_changed_during_validation_has_no_success_receipt(authoring, case, monkeypatch):
    root, authored, put = prepare(authoring, case, monkeypatch)
    real_validate = authoring.validate_occurrence_review

    def mutate_spec(*args):
        result = real_validate(*args)
        changed = deepcopy(authored)
        changed["review"]["summary"] = "Concurrent edit after authored input was read"
        put(".temp/spec.json", changed)
        return result

    monkeypatch.setattr(authoring, "validate_occurrence_review", mutate_spec)
    with pytest.raises(ValueError, match="Authored spec changed during assembly"):
        run(authoring, root, authored, put)
    assert not (root / ".temp/authored/draft-receipt.json").exists()
