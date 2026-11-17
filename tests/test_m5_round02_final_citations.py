"""Independent final-citation replay cannot conceal missing slots or shifted sources."""
import copy
import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest
from test_occurrence_review import add_authority, case, category, repin_sidecar  # noqa: F401

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


@pytest.mark.parametrize("corruption", [None, "missing", "duplicate", "axis", "repeated_axis", "repeated_evidence", "occurrence", "allowlist"])
def test_all_seventy_two_expected_final_citations_remain_bound(corruption):
    audit, report, manifest = complete_fixture()
    if corruption == "missing":
        report["rows"].pop()
    elif corruption == "duplicate":
        report["rows"][-1] = copy.deepcopy(report["rows"][0])
    elif corruption == "axis":
        report["rows"][0]["final_axes"].pop()
    elif corruption == "repeated_axis":
        report["rows"][0]["final_axes"].append(report["rows"][0]["final_axes"][0])
    elif corruption == "repeated_evidence":
        audit["final_cases"][0]["assessments"][0]["evidence_ids"].append("e0")
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


def test_new_round_denominator_comes_from_complete_authored_bindings():
    audit, report, manifest = complete_fixture()
    for axis in audit["final_cases"][0]["assessments"]:
        axis["evidence_ids"] = ["e0"]
    report["rows"] = [r for r in report["rows"] if r["case_id"] != "case-0" or r["evidence_id"] == "e0"]
    _, rows = m.expected_rows(audit, report, manifest)
    assert len(rows) == 65
    report["rows"].pop()
    with pytest.raises(ValueError, match="Every final citation"):
        m.expected_rows(audit, report, manifest)


@pytest.mark.parametrize("missing", [None, "config", "base", "audit", "report", "manifest"])
def test_new_round_must_be_explicit_and_equal_in_every_bound_document(missing):
    documents = {key: {"round_id": "m5-calibration-20261116-round03"}
                 for key in ("config", "base", "audit", "report", "manifest")}
    if missing is not None:
        documents[missing]["round_id"] = m.pairs.DEFAULT_ROUND
        with pytest.raises(ValueError, match="scientific round differs"):
            m.check_round(**documents)
    else:
        assert m.check_round(**documents) == "m5-calibration-20261116-round03"


@pytest.mark.parametrize("required", [
    ["existing_same_case_proof_replayed_again"], ["new_adjudicator_literal_anchor"],
    ["existing_same_case_proof_replayed_again", "new_adjudicator_literal_anchor"],
    ["new_adjudicator_paper_anchor"],
    ["existing_same_case_proof_replayed_again", "new_adjudicator_paper_anchor"],
])
def test_canaries_cover_only_the_paths_actually_used(required):
    rows = [{"proof_origin": origin} for origin in required]
    checked = [{"rows": [{"origin": origin}]} for origin in required]
    m.check_canary_origins(rows, checked)
    with pytest.raises(ValueError, match="every used"):
        m.check_canary_origins(rows, checked[:-1])


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
           "final_axes": ["relation"],
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
        assert result["kind"] == "authority"
        assert result["final_axes"] == ["relation"]
        assert not result["canonical_pair_verified"]
        assert "small literal snippet" not in json.dumps(result)


@pytest.mark.parametrize("kind", ["jats", "europepmc_abstract"])
@pytest.mark.parametrize("damage", [None, "title", "doi", "offset", "role", "quote", "extent"])
def test_new_final_paper_anchor_replays_primary_identity_and_exact_extent(tmp_path, monkeypatch, kind, damage):
    monkeypatch.setattr(m, "ROOT", tmp_path)
    metadata = {"title": "Synthetic paper", "doi": "10.1234/synthetic", "pmcid": "PMC123"}
    extent = "body" if kind == "jats" else "abstract"
    if kind == "jats":
        raw = (b'<article><front><article-meta><article-id pub-id-type="doi">10.1234/synthetic</article-id>'
               b'<article-id pub-id-type="pmc">123</article-id><title-group><article-title>Synthetic paper'
               b'</article-title></title-group></article-meta></front><body><sec><p>A literal paper excerpt.'
               b'</p></sec></body></article>')
    else:
        metadata["pmid"] = "456"
        raw = json.dumps({"hitCount": 1, "resultList": {"result": [{
            **metadata, "id": "456", "source": "MED", "abstractText": "A literal paper excerpt."}]}}).encode()
    path = tmp_path / "paper.data"
    path.write_bytes(raw)
    reference = "https://doi.org/10.1234/synthetic"
    proof = {**metadata, "reference": reference, "inspected_extent": extent}
    quote, aliases = m.literal(raw, kind, proof, "literal paper excerpt", None)
    proof.update({key: quote[key] for key in ("start", "end", "extractor", "text_sha256")})
    proof.update(scope="exact", support="supports", axes=["claim", "literature"])
    monkeypatch.setattr(m, "final_authored_proof", lambda *args: (
        proof, {"reference": reference, "quote": "literal paper excerpt"}, []))
    frozen = {"path": "paper.data", "sha256": m.pairs.sha(raw), "role": "evidence"}
    row = {"case_id": "case", "evidence_id": "paper", "kind": kind,
           "proof_origin": "new_adjudicator_paper_anchor", "paper_identity": metadata,
           "reference": reference, "inspected_extent": extent, "final_axes": ["claim", "literature"],
           "raw_input": {"path": str(path), "sha256": m.pairs.sha(raw)},
           "verified_quote": quote, "verified_identities": sorted(aliases),
           "locator": f"{extent}; chars {quote['start']}:{quote['end']}"}
    if damage in {"title", "doi"}:
        metadata[damage] = "changed"
    elif damage == "offset":
        row["verified_quote"]["start"] += 1
    elif damage == "role":
        frozen["role"] = "authority"
    elif damage == "quote":
        row["verified_quote"]["quote"] = "not present in paper"
    elif damage == "extent":
        row["inspected_extent"] = "body" if kind == "europepmc_abstract" else ""
    if damage:
        with pytest.raises(ValueError):
            m.replay_one(row, frozen, {}, {}, {})
    else:
        result = m.replay_one(row, frozen, {}, {}, {})
        assert result["status"] == "passed" and result["source_binding"]["kind"] == "new_final_paper_anchor"
        assert result["kind"] == kind
        assert result["source_binding"]["inspected_extent"] == extent
        assert result["semantic_support"] == "not_assessed" and not result["canonical_pair_verified"]
        assert result["scope"] == "exact" and result["support"] == "supports"


@pytest.mark.parametrize("damage", [None, "session", "model", "identity", "changed_proof", "unbound_scope", "substituted_predicate", "substituted_endpoint"])
@pytest.mark.parametrize("kind", ["jats", "authority"])
def test_final_anchor_requires_actual_adjudicator_and_valid_distinct_profile(case, monkeypatch, damage, kind):  # noqa: F811
    root, review, sidecar = case
    if kind == "authority":
        add_authority(case, "relation", "refutes", "model")
        category(review, "relation", "INCORRECT")
        sidecar["proofs"][-1]["reference"] = "model.txt"
        review["evidence"][-1]["reference"] = "model.txt"
    coordinator = root.parent / (root.name + "-coordinator")
    shutil.copytree(root, coordinator)
    monkeypatch.setattr(m, "ROOT", coordinator)
    packet_hash = m.pairs.sha((coordinator / "packet.json").read_bytes())
    author = {"id": "adjudicator", "model": "actual-model", "session_id": "actual-final-session"}
    review["reviewer"].update(identity=author["id"], model=author["model"])
    sidecar["reviewer"] = dict(author)
    if damage == "session":
        sidecar["reviewer"]["session_id"] = "initial-session"
    elif damage == "model":
        review["reviewer"]["model"] = "another-model"
    elif damage == "identity":
        review["reviewer"]["identity"] = "initial-reviewer"
    elif damage == "unbound_scope":
        sidecar["proofs"][0]["scope"] = "invented"
    elif damage in {"substituted_predicate", "substituted_endpoint"}:
        from edgemech.occurrence_packet import build_packet
        source = json.loads((root / "source.json").read_bytes())
        edge = source["edge"]
        if damage == "substituted_predicate":
            edge["predicate"] = "biolink:related_to"
        else:
            edge["object"] = "GO:0009987"
            edge["original_object_node"]["id"] = edge["object"]
        (root / "source.json").write_text(json.dumps(source))
        source_pin = {"path": "source.json", "sha256": m.pairs.sha((root / "source.json").read_bytes())}
        changed = build_packet(edge, source, occurrence_input=source_pin, source_input=source_pin, root=root)
        (root / "packet.json").write_text(json.dumps(changed))
        for path in ("source.json", "packet.json"):
            next(p for p in review["source"]["inputs"] if p["path"] == path)["sha256"] = m.pairs.sha((root / path).read_bytes())
        packet_pin = next(p for p in review["source"]["inputs"] if p["path"] == "packet.json")
        sidecar["proofs"][1]["input"]["sha256"] = packet_pin["sha256"]
        review["evidence"][1]["snapshot_sha256"] = packet_pin["sha256"]
    repin_sidecar(case)
    (root / "final-review.json").write_text(json.dumps(review))
    index = 0 if kind == "jats" else -1
    proof, item = sidecar["proofs"][index], review["evidence"][index]
    raw = (root / proof["input"]["path"]).read_bytes()
    quote, aliases = m.literal(raw, kind, proof, item["quote"], proof.get("version"))
    def pin(path):
        return {"path": str(path), "sha256": m.pairs.sha(path.read_bytes())}
    row = {"case_id": "case", "evidence_id": "final-witness", "kind": kind, "final_root": str(root),
           "proof_origin": "new_adjudicator_paper_anchor" if kind == "jats" else "new_adjudicator_literal_anchor",
           "final_proof_id": proof["evidence_id"],
           "final_input": pin(root / "final-review.json"), "final_sidecar": pin(root / "proofs.json"),
           "raw_input": pin(coordinator / proof["input"]["path"]), "reference": proof["reference"],
           "inspected_extent": proof["inspected_extent"], "final_axes": proof["axes"],
           "verified_quote": quote, "verified_identities": sorted(aliases), "locator": item["locator"]}
    if kind == "jats":
        row["paper_identity"] = {key: proof[key] for key in ("title", "doi", "pmcid")}
    else:
        row["authority_version"] = proof["version"]
    if damage == "changed_proof":
        (root / "proofs.json").write_text("{}")
    frozen = {**proof["input"], "role": "evidence" if kind == "jats" else "authority",
              **({"version": proof["version"]} if kind == "authority" else {})}
    packet = {"packet_path": "packet.json", "occurrence_id": sidecar["occurrence_id"],
              "frozen_packet_sha256": packet_hash}
    if damage in {"substituted_predicate", "substituted_endpoint"}:
        from edgemech.occurrence_review import validate_occurrence_review
        assert validate_occurrence_review(root, review, "packet.json", "proofs.json")["occurrence_id"] == packet["occurrence_id"]
    if damage:
        with pytest.raises(ValueError):
            m.replay_one(row, frozen, packet, {}, {}, author)
    else:
        result = m.replay_one(row, frozen, packet, {}, {}, author)
        assert result["scope"] == ("partial" if kind == "jats" else "exact")
        assert result["support"] == ("partial" if kind == "jats" else "refutes")
        assert result["proof_axes"] == proof["axes"]
        assert result["status"] == "passed"  # Literal identity; cannot meet exact directional gate.


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
    case = {"evidence_ids": ["original-id", "final-id"]}  # noqa: F811
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
