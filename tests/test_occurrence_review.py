"""Exercise profile scope/evidence failures through real packet and CLAW validation."""
from __future__ import annotations

import hashlib
import json
import subprocess
from copy import deepcopy

import pytest
from kg_microbe_curation.identity import CurationError
from kg_microbe_reviews import ReviewError, read_review

from edgemech import occurrence_review as module
from edgemech.literature_cache import LiteratureCache, full_text, verify_quote
from edgemech.occurrence_packet import build_packet


def pin(root, path):
    return {"path": path, "sha256": hashlib.sha256((root / path).read_bytes()).hexdigest()}


def write(root, path, value):
    (root / path).write_text(json.dumps(value))
    return pin(root, path)


def category(review, axis, value):
    assessment = next(a for a in review["assessments"]
                      if next(d["value"] for d in a["dimensions"] if d["name"] == "axis") == axis)
    next(d for d in assessment["dimensions"] if d["name"] == "category")["value"] = value
    assessment["outcome"] = module.CATEGORIES[axis][value]
    return assessment


@pytest.fixture
def case(tmp_path):
    oid = "urn:kg-microbe:occurrence:v1:" + "1" * 64
    edge = {"occurrence_id": oid, "subject": "NCBITaxon:2", "predicate": "biolink:capable_of",
            "object": "GO:0008150", "origin_transform": "fixture/edges.tsv",
            "transform_row_number": 1, "relation": "RO:0002215",
            "subject_label": "Bacteria", "object_label": "biological_process",
            "subject_category": "biolink:OrganismTaxon", "object_category": "biolink:BiologicalProcess",
            "original_subject_node": {"id": "NCBITaxon:2", "name": "Bacteria"},
            "original_object_node": {"id": "GO:0008150", "name": "biological_process"}}
    source = {"edge": edge, "records": []}
    source_pin = write(tmp_path, "source.json", source)
    packet = build_packet(edge, source, occurrence_input=source_pin, source_input=source_pin,
                          root=tmp_path)
    packet_pin = write(tmp_path, "packet.json", packet)
    xml = ('<article><front><article-meta><article-id pub-id-type="doi">10.1234/fixture</article-id>'
           '<article-id pub-id-type="pmc">123</article-id><title-group><article-title>Fixture study'
           '</article-title></title-group></article-meta></front><body><sec><p>'
           'Another strain grew in defined conditions.</p></sec></body></article>')
    (tmp_path / "paper.xml").write_text(xml)
    paper_pin = pin(tmp_path, "paper.xml")
    quote = "Another strain grew in defined conditions."
    document = LiteratureCache._document({"response_sha256": paper_pin["sha256"]}, "oa_fulltext",
                                         full_text(xml.encode(), "PMC123"))
    span = verify_quote(document, quote)
    proof = {"evidence_id": "paper", "kind": "jats", "input": paper_pin,
             "scope": "partial", "scope_rationale": "Different strain; does not establish exact claim.",
             "inspected_extent": "Entire fixture body", "support": "partial",
             "axes": ["claim", "literature"], "title": "Fixture study", "doi": "10.1234/fixture",
             "pmcid": "PMC123", "reference": "https://doi.org/10.1234/fixture",
             **{k: span[k] for k in ("text_sha256", "start", "end", "extractor")}}
    source_proof = {"evidence_id": "source", "kind": "packet", "input": packet_pin,
                    "scope": "exact", "scope_rationale": "Exact original row", "support": "supports",
                    "axes": ["source_fidelity"], "inspected_extent": "Whole fixture packet",
                    "reference": "packet.json"}
    sidecar = {"profile": module.PROFILE, "occurrence_id": oid, "proofs": [proof, source_proof]}
    sidecar_pin = write(tmp_path, "proofs.json", sidecar)
    labels = {"claim": "INSUFFICIENT_EVIDENCE", "literature": "PARTIAL", "relation": "UNRESOLVED",
              "subject_node": "UNRESOLVED", "object_node": "UNRESOLVED", "source_fidelity": "SUPPORTED"}
    assessments = []
    for axis, label in labels.items():
        eids = ["paper"] if axis in {"claim", "literature"} else (
            ["source"] if axis == "source_fidelity" else [])
        dims = {"axis": axis, "category": label, "scope": "Original assertion in fixture context",
                **{k: "Explicitly unresolved fixture check" for k in module.DETAILS[axis]}}
        assessments.append({"assessment_id": axis, "area": "evidence", "topic": axis,
                            "outcome": module.CATEGORIES[axis][label], "summary": "Authored fixture judgment",
                            "target_ids": [oid], "evidence_ids": eids,
                            "dimensions": [{"name": k, "value": v, "definition": k,
                                            "evidence_ids": eids} for k, v in dims.items()]})
    review = {"schema_version": "1.0.0", "review_id": "20000101T000000Z-fixture", "kind": "record",
              "repository": "CultureBotAI/EdgeMech", "title": "Synthetic scoped occurrence review",
              "started_at": "2000-01-01T00:00:00Z", "finished_at": "2000-01-01T00:00:00Z",
              "reviewer": {"identity": "Fixture", "kind": "agent", "independence": "self_review",
                           "independence_basis": "Synthetic test; not scientific evidence"},
              "skill": module.PROFILE, "completion": "completed", "verdict": "needs_curation",
              "scientific_review": True, "summary": "Unresolved fixture remains unresolved",
              "source": {"git_revision": "a" * 40, "state": "working_tree", "inputs": [
                  {**p, "role": "fixture input"} for p in (source_pin, packet_pin, paper_pin, sidecar_pin)]},
              "scope": {"description": "One fixture", "selection": "Synthetic one-unit case",
                        "coverage": "full", "population_size": 1, "reviewed_target_ids": [oid]},
              "targets": [{"target_id": oid, "path": "packet.json", "selector": "occurrence_id=" + oid,
                           "label": "Fixture occurrence", "kind": "snapshot_row",
                           "ownership_note": "Synthetic fixture has no maintained biological owner"}],
              "checks": [{"check_id": "fixture", "name": "Synthetic test inputs",
                          "status": "passed", "required": True, "target_ids": [oid],
                          "summary": "Test fixture construction; no scientific certification"}], "evidence": [
                  {"evidence_id": "paper", "kind": "primary_source", "reference": proof["reference"],
                   "locator": f"body; chars {span['start']}:{span['end']}", "accessed_at": "2000-01-01T00:00:00Z",
                   "support": "partial", "summary": "Different-strain fixture", "quote": quote,
                   "snapshot_sha256": paper_pin["sha256"]},
                  {"evidence_id": "source", "kind": "record_content", "reference": "packet.json",
                   "locator": "original occurrence", "accessed_at": "2000-01-01T00:00:00Z",
                   "support": "supports", "summary": "Exact source fixture", "snapshot_sha256": packet_pin["sha256"]}],
              "assessments": assessments, "findings": [], "actions": [], "limitations": ["Synthetic fixture"]}
    return tmp_path, review, sidecar


def validate(case):
    return module.validate_occurrence_review(case[0], case[1], "packet.json", "proofs.json")


def repin_sidecar(case):
    root, review, sidecar = case
    p = write(root, "proofs.json", sidecar)
    next(i for i in review["source"]["inputs"] if i["path"] == p["path"]).update(p)


def link_proof(case, proof, evidence):
    case[2]["proofs"].append(proof)
    case[1]["evidence"].append(evidence)
    for assessment in case[1]["assessments"]:
        axis = next(d["value"] for d in assessment["dimensions"] if d["name"] == "axis")
        if axis in proof["axes"]:
            assessment["evidence_ids"] = [*assessment["evidence_ids"], proof["evidence_id"]]
            for dim in assessment["dimensions"]:
                dim["evidence_ids"] = list(assessment["evidence_ids"])
    repin_sidecar(case)


def add_authority(case, axis, role, eid):
    root, review, _ = case
    text = "Synthetic authority assertion about the exact model."
    path = eid + ".txt"
    (root / path).write_text(text)
    authority_pin = pin(root, path)
    review["source"]["inputs"].append({**authority_pin, "role": "Synthetic authority"})
    span = verify_quote(LiteratureCache._document(
        {"response_sha256": authority_pin["sha256"]}, "authority_text", text), text)
    proof = {"evidence_id": eid, "kind": "authority", "input": authority_pin,
             "scope": "exact", "scope_rationale": "Exact synthetic model", "support": role,
             "inspected_extent": "Whole fixture", "axes": [axis], "version": "v1",
             "reference": "https://example.invalid/" + eid,
             **{k: span[k] for k in ("text_sha256", "start", "end", "extractor")}}
    evidence = {"evidence_id": eid, "kind": "authority", "reference": proof["reference"],
                "locator": f"chars {span['start']}:{span['end']}", "accessed_at": "2000-01-01T00:00:00Z",
                "support": role, "summary": "Synthetic authority", "quote": text,
                "snapshot_sha256": authority_pin["sha256"]}
    link_proof(case, proof, evidence)


def test_partial_evidence_keeps_claim_and_modeling_unresolved(case):
    receipt = validate(case)
    assert receipt["assessments"]["claim"] == "INSUFFICIENT_EVIDENCE"
    assert receipt["verified_quotes"] == 1
    assert receipt["kg_admissions"] == 0
    assert receipt["native_capability_enabled"] is False


@pytest.mark.parametrize("label", ["SUPPORTED_AS_STATED", "CONTRADICTED_AS_STATED", "CONFLICTING_EVIDENCE"])
def test_partial_quote_cannot_prove_exact_claim(case, label):
    category(case[1], "claim", label)
    with pytest.raises(ReviewError, match="exact-scope"):
        validate(case)


@pytest.mark.parametrize(("claim", "literature", "role"), [
    ("SUPPORTED_AS_STATED", "SUPPORTS", "supports"),
    ("CONTRADICTED_AS_STATED", "REFUTES", "refutes"),
])
def test_exact_authored_scope_requires_corresponding_replayed_role(case, claim, literature, role):
    category(case[1], "claim", claim)
    category(case[1], "literature", literature)
    case[1]["evidence"][0]["support"] = role
    case[2]["proofs"][0].update(scope="exact", support=role)
    repin_sidecar(case)
    assert validate(case)["assessments"]["claim"] == claim


def test_121_paper_applicability_cannot_be_removed_to_hide_opposition(case):
    case[2]["proofs"][0]["axes"] = ["literature"]
    repin_sidecar(case)
    with pytest.raises(ReviewError, match="both axes"):
        validate(case)


def test_121_evidence_absence_cannot_drop_an_applicable_paper(case):
    assessment = category(case[1], "literature", "NO_MATCH")
    assessment["evidence_ids"] = []
    for dimension in assessment["dimensions"]:
        dimension["evidence_ids"] = []
    with pytest.raises(ReviewError, match="omits applicable evidence"):
        validate(case)


def test_121_exact_refuting_paper_cannot_be_omitted_from_supported_claim(case):
    category(case[1], "claim", "SUPPORTED_AS_STATED")
    category(case[1], "literature", "CONFLICTING")
    case[1]["evidence"][0]["support"] = "supports"
    case[2]["proofs"][0].update(scope="exact", support="supports")
    proof, evidence = deepcopy(case[2]["proofs"][0]), deepcopy(case[1]["evidence"][0])
    proof.update(evidence_id="opposition", support="refutes")
    evidence.update(evidence_id="opposition", support="refutes")
    link_proof(case, proof, evidence)
    claim = category(case[1], "claim", "SUPPORTED_AS_STATED")
    claim["evidence_ids"] = ["paper"]
    for dim in claim["dimensions"]:
        dim["evidence_ids"] = ["paper"]
    with pytest.raises(ReviewError, match="omits applicable evidence"):
        validate(case)
    claim["evidence_ids"] = ["paper", "opposition"]
    with pytest.raises(ReviewError, match="requires conflict"):
        validate(case)
    category(case[1], "claim", "CONFLICTING_EVIDENCE")
    assert validate(case)["assessments"]["claim"] == "CONFLICTING_EVIDENCE"


@pytest.mark.parametrize("axis", ["relation", "subject_node", "object_node"])
@pytest.mark.parametrize("verdict", ["CORRECT", "INCORRECT"])
def test_122_opposing_model_authorities_require_unresolved(case, axis, verdict):
    add_authority(case, axis, "supports", "authority-support")
    add_authority(case, axis, "refutes", "authority-opposition")
    category(case[1], axis, verdict)
    with pytest.raises(ReviewError, match="require UNRESOLVED"):
        validate(case)
    category(case[1], axis, "UNRESOLVED")
    assert validate(case)["assessments"][axis] == "UNRESOLVED"


def test_122_opposing_source_proofs_cannot_resolve_one_way(case):
    proof, evidence = deepcopy(case[2]["proofs"][1]), deepcopy(case[1]["evidence"][1])
    proof.update(evidence_id="source-opposition", support="refutes")
    evidence.update(evidence_id="source-opposition", support="refutes")
    link_proof(case, proof, evidence)
    with pytest.raises(ReviewError, match="requires NOT_ASSESSABLE"):
        validate(case)
    category(case[1], "source_fidelity", "NOT_ASSESSABLE")
    assert validate(case)["assessments"]["source_fidelity"] == "NOT_ASSESSABLE"


@pytest.mark.parametrize(("label", "role"), [("SUPPORTED", "supports"), ("CONTRADICTED", "refutes")])
@pytest.mark.parametrize("scope", ["partial", "context"])
@pytest.mark.parametrize("opposition", [False, True])
def test_125_partial_source_evidence_cannot_resolve_full_source_verdict(case, label, role, scope, opposition):
    category(case[1], "source_fidelity", label)
    case[2]["proofs"][1].update(support=role, scope=scope)
    case[1]["evidence"][1]["support"] = role
    if opposition:
        opposite = "refutes" if role == "supports" else "supports"
        proof, evidence = deepcopy(case[2]["proofs"][1]), deepcopy(case[1]["evidence"][1])
        proof.update(evidence_id="source-opposition", support=opposite, scope="exact")
        evidence.update(evidence_id="source-opposition", support=opposite)
        link_proof(case, proof, evidence)
    repin_sidecar(case)
    with pytest.raises(ReviewError, match="exact-scope packet evidence"):
        validate(case)
    category(case[1], "source_fidelity", "NOT_ASSESSABLE")
    assert validate(case)["assessments"]["source_fidelity"] == "NOT_ASSESSABLE"


@pytest.mark.parametrize("identity", ["same", "doi_only", "pmcid_only", "distinct"])
def test_124_quotation_budget_joins_publication_aliases_across_raw_bytes(case, identity):
    root, review, sidecar = case
    extra_quote = " ".join("word" + str(i) for i in range(20))
    raw = (root / "paper.xml").read_text().replace("</sec>", f"<p>{extra_quote}</p></sec>")
    doi, pmcid = "10.1234/fixture", "PMC123"
    if identity in {"doi_only", "distinct"}:
        raw = raw.replace('pub-id-type="pmc">123', 'pub-id-type="pmc">124')
        pmcid = "PMC124"
    if identity == "distinct":
        raw = raw.replace("10.1234/fixture", "10.1234/other")
        doi = "10.1234/other"
    elif identity == "pmcid_only":
        raw = raw.replace('<article-id pub-id-type="doi">10.1234/fixture</article-id>', '')
        doi = ""
    (root / "paper2.xml").write_text(raw)
    new_pin = pin(root, "paper2.xml")
    review["source"]["inputs"].append({**new_pin, "role": "Second retained representation"})
    span = verify_quote(LiteratureCache._document({"response_sha256": new_pin["sha256"]},
                                                 "oa_fulltext", full_text(raw.encode(), pmcid)), extra_quote)
    proof, evidence = deepcopy(sidecar["proofs"][0]), deepcopy(review["evidence"][0])
    url = ("https://doi.org/" + doi if doi else "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC123/")
    proof.update(evidence_id="paper2", input=new_pin, doi=doi, pmcid=pmcid, reference=url,
                 missing_doi_reason="No DOI in this retained representation",
                 **{k: span[k] for k in ("text_sha256", "start", "end", "extractor")})
    evidence.update(evidence_id="paper2", reference=url, quote=extra_quote,
                    locator=f"chars {span['start']}:{span['end']}", snapshot_sha256=new_pin["sha256"])
    link_proof(case, proof, evidence)
    if identity == "distinct":
        assert validate(case)["verified_quotes"] == 2
    else:
        with pytest.raises(ReviewError, match="25-word excerpt per source"):
            validate(case)


def test_missing_doi_requires_explicit_reason_and_verified_alternate(case):
    root, review, sidecar = case
    raw = (root / "paper.xml").read_text().replace(
        '<article-id pub-id-type="doi">10.1234/fixture</article-id>', '')
    (root / "paper.xml").write_text(raw)
    new_pin = pin(root, "paper.xml")
    next(i for i in review["source"]["inputs"] if i["path"] == "paper.xml").update(new_pin)
    url = "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC123/"
    review["evidence"][0].update(reference=url, snapshot_sha256=new_pin["sha256"])
    sidecar["proofs"][0].update(input=new_pin, doi="", reference=url)
    repin_sidecar(case)
    with pytest.raises(ReviewError, match="missing DOI reason"):
        validate(case)
    sidecar["proofs"][0]["missing_doi_reason"] = "No DOI in primary article metadata"
    repin_sidecar(case)
    assert validate(case)["verified_quotes"] == 1


def test_resolved_node_model_needs_versioned_authority_not_only_packet(case):
    category(case[1], "subject_node", "CORRECT")["evidence_ids"] = ["source"]
    case[2]["proofs"][1]["axes"].append("subject_node")
    repin_sidecar(case)
    with pytest.raises(ReviewError, match="versioned authority"):
        validate(case)


def test_versioned_authority_replays_and_applies_to_only_bound_axis(case):
    root, review, sidecar = case
    text = "Fixture identifier has a taxon category."
    (root / "authority.txt").write_text(text)
    authority_pin = pin(root, "authority.txt")
    review["source"]["inputs"].append({**authority_pin, "role": "Synthetic authority"})
    doc = LiteratureCache._document({"response_sha256": authority_pin["sha256"]}, "authority_text", text)
    span = verify_quote(doc, text)
    proof = {"evidence_id": "authority", "kind": "authority", "input": authority_pin,
             "scope": "exact", "scope_rationale": "Exact synthetic endpoint identifier",
             "inspected_extent": "Whole fixture authority", "support": "supports",
             "axes": ["subject_node"], "reference": "https://example.invalid/authority/v1", "version": "v1",
             **{k: span[k] for k in ("text_sha256", "start", "end", "extractor")}}
    sidecar["proofs"].append(proof)
    review["evidence"].append({"evidence_id": "authority", "kind": "authority", "reference": proof["reference"],
                               "locator": f"chars {span['start']}:{span['end']}",
                               "accessed_at": "2000-01-01T00:00:00Z", "support": "supports",
                               "summary": "Synthetic endpoint authority", "quote": text,
                               "snapshot_sha256": authority_pin["sha256"]})
    assessment = category(review, "subject_node", "CORRECT")
    assessment["evidence_ids"] = ["authority"]
    for dimension in assessment["dimensions"]:
        dimension["evidence_ids"] = ["authority"]
    repin_sidecar(case)
    assert validate(case)["assessments"]["subject_node"] == "CORRECT"
    proof["version"] = ""
    repin_sidecar(case)
    with pytest.raises(ReviewError, match="authority version"):
        validate(case)


@pytest.mark.parametrize("damage", ["missing_axis", "duplicate_axis", "unassessed", "missing_details",
                                    "wrong_mapping", "source_as_claim", "unbound_dimension"])
def test_reject_incomplete_or_conflated_axes(case, damage):
    review = case[1]
    if damage == "missing_axis":
        review["assessments"].pop()
    elif damage == "duplicate_axis":
        extra = deepcopy(review["assessments"][0])
        extra["assessment_id"] = "duplicate"
        review["assessments"].append(extra)
    elif damage == "unassessed":
        category(review, "object_node", "UNASSESSED")
    elif damage == "missing_details":
        review["assessments"][2]["dimensions"] = review["assessments"][2]["dimensions"][:3]
    elif damage == "wrong_mapping":
        review["assessments"][0]["outcome"] = "supported"
    elif damage == "source_as_claim":
        case[2]["proofs"][1]["axes"].append("claim")
        repin_sidecar(case)
    else:
        review["assessments"][0]["dimensions"][0]["evidence_ids"] = ["source"]
    with pytest.raises(ReviewError):
        validate(case)


@pytest.mark.parametrize("damage", ["doi", "title", "quote", "span", "hash", "axis", "occurrence",
                                    "raw", "endpoint", "missing_proof", "source_pin"])
def test_replay_rejects_tampered_evidence_and_bindings(case, damage):
    root, review, sidecar = case
    if damage in {"doi", "title"}:
        sidecar["proofs"][0][damage] = "wrong"
    elif damage == "quote":
        review["evidence"][0]["quote"] = "Invented evidence"
    elif damage == "span":
        sidecar["proofs"][0]["start"] += 1
    elif damage == "hash":
        review["evidence"][0]["snapshot_sha256"] = "0" * 64
    elif damage == "axis":
        sidecar["proofs"][0]["axes"] = ["subject_node"]
    elif damage == "occurrence":
        sidecar["occurrence_id"] = "wrong"
    elif damage == "raw":
        (root / "paper.xml").write_text("corrupt")
    elif damage == "endpoint":
        p = json.loads((root / "packet.json").read_text())
        p["endpoints"]["object"]["category"] = "biolink:ChemicalEntity"
        updated = write(root, "packet.json", p)
        next(i for i in review["source"]["inputs"] if i["path"] == "packet.json").update(updated)
    elif damage == "source_pin":
        review["source"]["inputs"] = [i for i in review["source"]["inputs"] if i["path"] != "source.json"]
    else:
        sidecar["proofs"].pop()
    repin_sidecar(case)
    with pytest.raises((ReviewError, CurationError)):
        validate(case)


def test_save_readback_preserves_six_axes_and_replays_private_bytes(case):
    root, review, _ = case
    def git(*args):
        return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.PIPE).decode().strip()
    git("init", "-q")
    git("remote", "add", "origin", "https://github.com/CultureBotAI/EdgeMech.git")
    git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
        "commit", "--allow-empty", "-qm", "Fixture base")
    review["source"]["git_revision"] = git("rev-parse", "HEAD")
    result = module.save_occurrence_review(root, review, "packet.json", "proofs.json")
    persisted = read_review(root, result["review"])
    assert len(persisted["assessments"]) == 6
    assert (root / result["review"]).stat().st_size > 0
    with pytest.raises(ReviewError, match="immutable"):
        module.save_occurrence_review(root, review, "packet.json", "proofs.json")
    (root / "paper.xml").write_text("changed retained source")
    with pytest.raises(ReviewError, match="changed"):
        module.validate_occurrence_review(root, persisted, "packet.json", "proofs.json")
