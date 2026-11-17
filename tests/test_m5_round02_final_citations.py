"""Independent final-citation replay cannot conceal missing slots or shifted sources."""
import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts/adhoc"))
SPEC = importlib.util.spec_from_file_location("final_citations", ROOT / "scripts/adhoc/replay_m5_round02_final_citations_20261116.py")
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


def complete_fixture():
    audit, manifest, report = {"final_cases": []}, {"cases": []}, {"rows": []}
    for index in range(10):
        cid = "case-" + str(index)
        ids = ["e" + str(n) for n in range(8 if index < 2 else 7)]
        assessments = [{"axis": axis, "evidence_ids": ids} for axis in m.pairs.rounds.CATEGORIES]
        audit["final_cases"].append({"case_id": cid, "occurrence_id": cid, "assessments": assessments})
        manifest["cases"].append({"case_id": cid, "occurrence_id": cid, "evidence_ids": ids})
        report["rows"].extend({"case_id": cid, "evidence_id": eid, "final_axes": list(m.pairs.rounds.CATEGORIES)} for eid in ids)
    return audit, report, manifest


@pytest.mark.parametrize("corruption", [None, "missing", "duplicate", "axis", "occurrence", "allowlist"])
def test_all_seventy_two_expected_final_citations_remain_bound(corruption):
    audit, report, manifest = complete_fixture()
    if corruption == "missing":
        report["rows"].pop()
    elif corruption == "duplicate":
        report["rows"][-1] = copy.deepcopy(report["rows"][0])
    elif corruption == "axis":
        report["rows"][0]["final_axes"].pop()
    elif corruption == "occurrence":
        audit["final_cases"][0]["occurrence_id"] = "other"
    elif corruption == "allowlist":
        manifest["cases"][0]["evidence_ids"].pop()
    if corruption:
        with pytest.raises(ValueError):
            m.expected_rows(audit, report, manifest)
    else:
        cases, rows = m.expected_rows(audit, report, manifest)
        assert len(cases) == 10 and len(rows) == 72


@pytest.mark.parametrize("corruption", [None, "version", "identity", "offset", "source", "role"])
def test_external_anchor_replays_exact_literal_and_frozen_identity(tmp_path, monkeypatch, corruption):
    monkeypatch.setattr(m, "ROOT", tmp_path)
    raw = b"Synthetic source with a small literal snippet for replay."
    path = tmp_path / "authority.txt"
    path.write_bytes(raw)
    proof = {"version": "test-v1", "reference": "authority.txt"}
    quote, identities = m.literal(raw, "authority", proof, "small literal snippet", "test-v1")
    frozen = {"path": "authority.txt", "sha256": m.pairs.sha(raw), "role": "authority", "version": "test-v1"}
    row = {"case_id": "case", "evidence_id": "source", "kind": "authority",
           "proof_origin": "new_adjudicator_literal_anchor", "authority_version": "test-v1",
           "reference": "authority.txt", "inspected_extent": "synthetic source",
           "raw_input": {"path": str(path), "sha256": m.pairs.sha(raw)},
           "verified_quote": quote, "verified_identities": sorted(identities),
           "locator": f"chars {quote['start']}:{quote['end']}"}
    if corruption == "version":
        row["authority_version"] = "different"
    elif corruption == "identity":
        row["verified_identities"] = ["unrelated-source"]
    elif corruption == "offset":
        row["verified_quote"]["end"] += 1
    elif corruption == "source":
        path.write_bytes(raw + b" changed")
    elif corruption == "role":
        frozen["role"] = "packet"
    if corruption:
        with pytest.raises(ValueError):
            m.replay_one(row, frozen, {}, {}, {})
    else:
        result = m.replay_one(row, frozen, {}, {}, {})
        assert result["status"] == "passed" and result["semantic_support"] == "not_assessed"
        assert not result["canonical_pair_verified"]
        assert "small literal snippet" not in json.dumps(result)


def test_batch_requires_canaries_for_both_data_paths_before_output(tmp_path):
    with pytest.raises(ValueError, match="existing-proof and new-anchor"):
        m.run({}, tmp_path / ".temp" / "out", "batch")
    assert not (tmp_path / ".temp" / "out").exists()


def test_canary_rejects_changed_private_source_and_nested_receipt(tmp_path):
    config = {"test": "configuration"}
    output = tmp_path / "canary"
    output.mkdir()
    nested = output / "nested" / "receipt.json"
    nested.parent.mkdir()
    nested.write_text("{}")
    source = tmp_path / "private.json"
    source.write_text("{}")
    receipt = {"mode": "canary", "helper_sha256": m.pairs.sha(Path(m.__file__).read_bytes()),
               "config_sha256": m.pairs.sha(m.pairs.encoded(config)), "passed": True,
               "rows": [{"case_id": "one"}],
               "artifact_pins": [{"path": str(nested), "sha256": m.pairs.sha(nested.read_bytes())}],
               "input_pins": [{"path": str(source), "sha256": m.pairs.sha(source.read_bytes())}]}
    (output / "receipt.json").write_bytes(m.pairs.encoded(receipt))
    assert m.check_canary(output, config) == receipt
    nested.write_text('{"changed":true}')
    with pytest.raises(ValueError, match="private data changed"):
        m.check_canary(output, config)
    nested.write_text("{}")
    source.write_text('{"changed":true}')
    with pytest.raises(ValueError, match="private data changed"):
        m.check_canary(output, config)


@pytest.mark.parametrize("corruption", [None, "duplicate", "input_path", "reference"])
def test_existing_original_proof_is_bound_to_same_case_file_and_source(tmp_path, monkeypatch, corruption):
    monkeypatch.setattr(m, "ROOT", tmp_path)
    original_root = tmp_path / "reviewer"
    original_root.mkdir()
    raw = b"Synthetic original authority with a bounded excerpt."
    for root in (tmp_path, original_root):
        (root / "source.txt").write_bytes(raw)
    proof = {"evidence_id": "proof", "kind": "authority", "version": "v1", "reference": "source.txt",
             "input": {"path": "source.txt", "sha256": m.pairs.sha(raw)}, "inspected_extent": "synthetic source"}
    quote, identities = m.literal(raw, "authority", proof, "bounded excerpt", "v1")
    proof.update({k: quote[k] for k in ("start", "end", "extractor", "text_sha256")})
    review = {"source": {"inputs": [proof["input"]]}, "evidence": [{"evidence_id": "proof", "quote": "bounded excerpt",
              "snapshot_sha256": m.pairs.sha(raw), "reference": "source.txt", "locator": f"chars {quote['start']}:{quote['end']}"}]}
    sidecar = {"occurrence_id": "original", "proofs": [proof]}
    if corruption == "duplicate":
        sidecar["proofs"].append(copy.deepcopy(proof))
    elif corruption == "reference":
        review["evidence"][0]["reference"] = "other-source"
    for name, value in (("input.json", review), ("proofs.json", sidecar)):
        (original_root / name).write_text(json.dumps(value))
    def pin(path):
        return {"path": str(path), "sha256": m.pairs.sha(path.read_bytes())}
    row = {"case_id": "case", "evidence_id": "source", "kind": "authority",
           "proof_origin": "existing_same_case_proof_replayed_again", "prior_proof": {"reviewer_id": "reviewer-a", "proof_id": "proof"},
           "original_input": pin(original_root / "input.json"), "original_sidecar": pin(original_root / "proofs.json"),
           "original_raw_input": pin(original_root / "source.txt"), "raw_input": pin(tmp_path / "source.txt"),
           "reference": "source.txt", "inspected_extent": "synthetic source", "verified_identities": sorted(identities),
           "verified_quote": quote, "locator": f"chars {quote['start']}:{quote['end']}"}
    entries = {("reviewer-a", "case"): {"input": "input.json", "proofs": "proofs.json"}}
    if corruption == "input_path":
        entries["reviewer-a", "case"]["input"] = "different.json"
    frozen = {"path": "source.txt", "sha256": m.pairs.sha(raw), "version": "v1", "evidence_ids": ["source"]}
    arguments = (row, frozen, {"occurrence_id": "original", "evidence_ids": ["source"]},
                 {"reviewer-a": {"root": original_root, "manifest": {"files": [frozen]}}}, entries)
    if corruption:
        with pytest.raises(ValueError):
            m.replay_one(*arguments)
    else:
        result = m.replay_one(*arguments)
        assert result["status"] == "passed" and not result["canonical_pair_verified"]


@pytest.mark.parametrize("corruption", [None, "hash_only", "version", "identity", "duplicate_metadata", "case_id", "not_frozen", "missing_id_no_case", "missing_id_ambiguous", "missing_id_unique"])
def test_source_alias_requires_both_frozen_pins_and_embedded_primary_identity(corruption):
    raw = b'id: https://example.invalid/schema\nname: Synthetic-Schema\nversion: "v1"\n'
    if corruption == "hash_only":
        raw = b"Equal bytes without primary schema metadata"
    elif corruption == "identity":
        raw = b'name: Synthetic-Schema\nversion: "v1"\n'
    elif corruption == "duplicate_metadata":
        raw += b'id: https://example.invalid/another\n'
    digest = m.pairs.sha(raw)
    original = {"path": "retained.yaml", "sha256": digest, "role": "authority", "version": "v1", "evidence_ids": ["original-id"]}
    final = {"path": "snapshot.txt", "sha256": digest, "role": "authority", "version": "v1", "evidence_ids": ["final-id"]}
    proof = {"input": {"path": "retained.yaml", "sha256": digest}, "version": "v1", "manifest_evidence_id": "original-id"}
    case = {"evidence_ids": ["original-id", "final-id"]}
    manifest = {"files": [original, final]}
    if corruption in {"missing_id_no_case", "missing_id_ambiguous", "missing_id_unique"}:
        proof.pop("manifest_evidence_id")
        if corruption == "missing_id_no_case":
            case["evidence_ids"] = ["final-id"]
        elif corruption == "missing_id_ambiguous":
            original["evidence_ids"].append("another-original")
            case["evidence_ids"].append("another-original")
    if corruption == "version":
        original["version"] = "v0"
    elif corruption == "case_id":
        case["evidence_ids"] = ["final-id"]
    elif corruption == "not_frozen":
        manifest["files"] = [final]
    if corruption and corruption != "missing_id_unique":
        with pytest.raises(ValueError):
            m.source_binding(proof, final, case, manifest, raw, "final-id")
    else:
        result = m.source_binding(proof, final, case, manifest, raw, "final-id")
        assert result["kind"] == "verified_frozen_schema_alias"
        assert result["original_manifest_id"] == "original-id" and result["final_manifest_id"] == "final-id"
        assert result["source_reference_preserved"]
