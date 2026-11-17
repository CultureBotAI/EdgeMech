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
from edgemech.literature_cache import LiteratureCache, abstract_text, full_text, verify_quote
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


def install_abstract(case, *, pmid="456", doi="10.1234/fixture", pmcid=None,
                     quote="The exact strain was non-motile.", markup=None):
    """Replace the fixture paper proof with primary-metadata-bound abstract text."""
    root, review, sidecar = case
    record = {"id": pmid, "source": "MED", "pmid": pmid, "pmcid": pmcid,
              "doi": doi, "title": "Fixture study", "abstractText": markup or quote}
    response = {"version": "fixture", "hitCount": 1, "resultList": {"result": [record]}}
    abstract_pin = write(root, "abstract.json", response)
    review["source"]["inputs"].append({**abstract_pin, "role": "Synthetic primary abstract"})
    document = LiteratureCache._document({"response_sha256": abstract_pin["sha256"]}, "abstract",
                                         abstract_text(record["abstractText"]))
    span = verify_quote(document, quote)
    proof = sidecar["proofs"][0]
    proof.pop("pmcid", None)
    reference = "https://doi.org/" + doi if doi else "https://pubmed.ncbi.nlm.nih.gov/" + pmid + "/"
    proof.update(kind="europepmc_abstract", input=abstract_pin, pmid=pmid, doi=doi,
                 inspected_extent="abstract", reference=reference,
                 **{k: span[k] for k in ("text_sha256", "start", "end", "extractor")})
    if pmcid:
        proof["pmcid"] = pmcid
    if not doi:
        proof["missing_doi_reason"] = "Selected primary record has no DOI"
    review["evidence"][0].update(reference=reference, quote=quote,
                               locator=f"abstract; chars {span['start']}:{span['end']}",
                               snapshot_sha256=abstract_pin["sha256"])
    repin_sidecar(case)
    return response


@pytest.fixture
def abstract_case(case):
    install_abstract(case)
    return case


@pytest.fixture
def supported_partial_case(abstract_case):
    """Synthetic #152 transport case; the source statement is explicitly scoped."""
    case = abstract_case
    review = case[1]
    review.update(completion="partial", verdict="needs_curation")
    review["checks"][0].update(status="unavailable", summary="Required historical authority unavailable")
    category(review, "claim", "SUPPORTED_AS_STATED")
    category(review, "literature", "SUPPORTS")
    review["evidence"][0]["support"] = "supports"
    case[2]["proofs"][0].update(scope="exact", support="supports",
                                scope_rationale="Exact synthetic scoped statement")
    repin_sidecar(case)
    return case


@pytest.fixture
def report_case(case):
    """Original fixture is a source report before any assessment is authored.

    This fixture exercises transport, not a semantic eligibility oracle: real
    original propositions still require independent scope inspection.
    """
    root, review, sidecar = case
    source = json.loads((root / "source.json").read_text())
    edge = source["edge"]
    edge.update(predicate="biolink:has_attribute", relation="biolink:has_attribute",
                object="fixture:reported-status", object_label="Fixture reported status",
                object_category="biolink:Attribute",
                original_object_node={
                    "id": "fixture:reported-status", "name": "Fixture reported status",
                    "description": "The fixture source reports status as observed; this node denotes "
                                   "the reported field value, not a biological property.",
                })
    record = json.dumps({"source_id": "fixture-source-v1", "subject": edge["subject"],
                         "field": "status", "value": "observed"})
    source["records"] = [{"source_relative_path": "fixture-source.json", "locator": "record 1",
                          "text": record, "text_sha256": hashlib.sha256(record.encode()).hexdigest()}]
    source_pin = write(root, "source.json", source)
    packet = build_packet(edge, source, occurrence_input=source_pin, source_input=source_pin, root=root)
    packet_pin = write(root, "packet.json", packet)
    for updated in (source_pin, packet_pin):
        next(p for p in review["source"]["inputs"] if p["path"] == updated["path"]).update(updated)
    sidecar["proofs"][1]["input"] = packet_pin
    review["evidence"][1]["snapshot_sha256"] = packet_pin["sha256"]
    claim = category(review, "claim", "SUPPORTED_AS_STATED")
    scope = "The identified fixture source reports status as observed for the original subject."
    next(d for d in claim["dimensions"] if d["name"] == "assertion_scope")["value"] = scope
    claim.update(assertion_basis="source_report", report_witnesses={
        "scope": scope, "source_instance_evidence_ids": ["source"],
        "identity_evidence_ids": ["meaning"], "definition_evidence_ids": ["meaning"],
    })
    sidecar["proofs"][1]["axes"].append("claim")
    claim["evidence_ids"].append("source")
    add_authority(case, "claim", "supports", "meaning")
    original = json.loads((root / "packet.json").read_text())["original_assertion"]
    sidecar["proofs"][-1]["original_entities"] = {
        name: original[name] for name in ("subject", "predicate", "object")
    }
    repin_sidecar(case)
    return case


def test_report_fixture_original_proposition_is_already_a_source_report(report_case):
    root, review, sidecar = report_case
    packet = json.loads((root / "packet.json").read_text())
    original = packet["original_assertion"]
    assert original["predicate"] == original["relation"] == "biolink:has_attribute"
    assert original["object"] == "fixture:reported-status"
    assert "reported field value, not a biological property" in packet["endpoints"]["object"]["record"]["description"]
    assert json.loads(packet["source_records"][0]["text"]) == {
        "source_id": "fixture-source-v1", "subject": original["subject"],
        "field": "status", "value": "observed",
    }
    assert sidecar["proofs"][-1]["original_entities"] == {
        name: original[name] for name in ("subject", "predicate", "object")
    }
    before = (root / "packet.json").read_bytes()
    assert validate(report_case)["claim_assertion_basis"] == "source_report"
    assert (root / "packet.json").read_bytes() == before
    assert review["evidence"][1]["snapshot_sha256"] == pin(root, "packet.json")["sha256"]


def test_report_save_readback_preserves_scope_witnesses_and_partial_model(report_case):
    root, review, _ = report_case
    review.update(completion="partial", verdict="needs_curation")
    review["checks"][0]["status"] = "unavailable"
    category(review, "relation", "INCORRECT")
    add_authority(report_case, "relation", "refutes", "model")
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "remote", "add", "origin",
                    "https://github.com/CultureBotAI/EdgeMech.git"], check=True)
    subprocess.run(["git", "-C", str(root), "-c", "user.name=Fixture", "-c",
                    "user.email=fixture@example.invalid", "commit", "--allow-empty", "-qm", "Fixture"], check=True)
    review["source"]["git_revision"] = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    result = module.save_occurrence_review(root, review, "packet.json", "proofs.json")
    saved = read_review(root, result["review"])
    assert saved["assessments"] == review["assessments"]
    assert saved["completion"] == "partial" and saved["verdict"] == "needs_curation"
    assert result["claim_assertion_basis"] == "source_report"
    assert result["assessments"]["relation"] == "INCORRECT"
    assert result["assessments"]["literature"] == "PARTIAL"
    assert result["kg_admissions"] == 0
    rendered = (root / result["review"]).with_suffix(".md").read_text()
    assert "does not establish independent biological truth" in rendered
    assert result["claim_assertion_scope"] in rendered
    assert "Original source instance" in rendered and "meaning" in rendered
    saved.update(completion="completed")
    with pytest.raises(ReviewError, match="unavailable required"):
        module.validate_occurrence_review(root, saved, "packet.json", "proofs.json")
    saved["checks"][0]["status"] = "passed"
    saved["verdict"] = "pass"
    with pytest.raises(ReviewError, match="unknown or concerning"):
        module.validate_occurrence_review(root, saved, "packet.json", "proofs.json")


@pytest.mark.parametrize("damage, message", [
    ("missing_entities", "exact original entity"),
    ("wrong_identifier", "exact original entity"),
    ("incomplete_identity", "omit original"),
    ("incomplete_definition", "omit original"),
    ("partial_authority", "exact supporting identity"),
    ("partial_instance", "exact source-instance"),
    ("scope_change", "scope must equal"),
    ("missing_version", "authority version"),
])
def test_report_requires_exact_original_identity_and_meaning(report_case, damage, message):
    _, review, sidecar = report_case
    authority = sidecar["proofs"][-1]
    claim = category(review, "claim", "SUPPORTED_AS_STATED")
    if damage == "missing_entities":
        authority.pop("original_entities")
    elif damage == "wrong_identifier":
        authority["original_entities"]["subject"] = "NCBITaxon:999"
    elif damage == "incomplete_identity":
        authority["original_entities"].pop("object")
    elif damage == "incomplete_definition":
        authority["original_entities"].pop("predicate")
    elif damage == "partial_authority":
        authority["scope"] = "partial"
    elif damage == "partial_instance":
        sidecar["proofs"][1]["scope"] = "partial"
    elif damage == "scope_change":
        claim["report_witnesses"]["scope"] = "An independent biological statement"
    else:
        authority.pop("version")
    repin_sidecar(report_case)
    with pytest.raises(ReviewError, match=message):
        validate(report_case)


def test_raw_source_copy_under_another_path_cannot_supply_report_authority(report_case):
    root, review, sidecar = report_case
    authority, evidence = sidecar["proofs"][-1], review["evidence"][-1]
    raw = (root / "source.json").read_bytes()
    (root / "meaning.txt").write_bytes(raw)
    source_pin = pin(root, "meaning.txt")
    next(p for p in review["source"]["inputs"] if p["path"] == "meaning.txt").update(source_pin)
    quote = "NCBITaxon:2"
    span = verify_quote(LiteratureCache._document(
        {"response_sha256": source_pin["sha256"]}, "authority_text", raw.decode()), quote)
    authority.update(input=source_pin, **{k: span[k] for k in ("text_sha256", "start", "end", "extractor")})
    evidence.update(snapshot_sha256=source_pin["sha256"], quote=quote,
                    locator=f"chars {span['start']}:{span['end']}")
    repin_sidecar(report_case)
    with pytest.raises(ReviewError, match="independent authority, not copied source bytes"):
        validate(report_case)


@pytest.mark.parametrize("declared_entities", [True, False])
def test_report_cannot_omit_linked_counterauthority_from_witness_roles(report_case, declared_entities):
    """#189: every applicable authority must enter the identity/definition evaluation."""
    add_authority(report_case, "claim", "refutes", "counter-meaning")
    if declared_entities:
        report_case[2]["proofs"][-1]["original_entities"] = dict(
            report_case[2]["proofs"][-2]["original_entities"])
    repin_sidecar(report_case)
    with pytest.raises(ReviewError, match="Every claim authority must have an explicit report witness role"):
        validate(report_case)


def test_report_counterauthority_cannot_resolve_by_adding_its_witness_role(report_case):
    add_authority(report_case, "claim", "refutes", "counter-meaning")
    report_case[2]["proofs"][-1]["original_entities"] = dict(
        report_case[2]["proofs"][-2]["original_entities"])
    claim = category(report_case[1], "claim", "SUPPORTED_AS_STATED")
    claim["report_witnesses"]["definition_evidence_ids"].append("counter-meaning")
    repin_sidecar(report_case)
    with pytest.raises(ReviewError, match="supporting identity and definition authorities"):
        validate(report_case)


def test_report_truth_stays_separate_from_refuting_biological_paper(report_case):
    review, sidecar = report_case[1:]
    sidecar["proofs"][0].update(scope="exact", support="refutes")
    review["evidence"][0]["support"] = "refutes"
    category(review, "literature", "REFUTES")
    repin_sidecar(report_case)
    result = validate(report_case)
    assert result["claim_assertion_basis"] == "source_report"
    assert result["assessments"]["claim"] == "SUPPORTED_AS_STATED"
    assert result["assessments"]["literature"] == "REFUTES"
    assert result["kg_admissions"] == 0


@pytest.mark.parametrize("axis", ["literature", "relation", "subject_node", "object_node", "source_fidelity"])
def test_report_fields_cannot_leak_to_other_axes(report_case, axis):
    review = report_case[1]
    assessment = next(a for a in review["assessments"] if a["assessment_id"] == axis)
    assessment["assertion_basis"] = "independent"
    with pytest.raises(ReviewError, match="only to the claim axis"):
        validate(report_case)


def test_report_packet_cannot_be_bound_to_literature(report_case):
    report_case[2]["proofs"][1]["axes"].append("literature")
    repin_sidecar(report_case)
    with pytest.raises(ReviewError, match="Copied source content"):
        validate(report_case)


def test_report_packet_cannot_silently_become_independent_evidence(report_case):
    claim = category(report_case[1], "claim", "SUPPORTED_AS_STATED")
    claim.pop("assertion_basis")
    claim.pop("report_witnesses")
    with pytest.raises(ReviewError, match="Copied source content"):
        validate(report_case)


@pytest.mark.parametrize("axis", ["relation", "subject_node", "object_node"])
@pytest.mark.parametrize("model_category", ["INCORRECT", "UNRESOLVED", "UNASSESSED"])
def test_152_supported_claim_saves_without_rewriting_model_judgments(
    supported_partial_case, axis, model_category,
):
    case = supported_partial_case
    root, review, _ = case
    for model_axis in ("relation", "subject_node", "object_node"):
        value = model_category if model_axis == axis else "CORRECT"
        category(review, model_axis, value)
        if value in {"CORRECT", "INCORRECT"}:
            add_authority(case, model_axis, "supports" if value == "CORRECT" else "refutes", model_axis)

    def git(*args):
        return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.PIPE).decode().strip()

    git("init", "-q")
    git("remote", "add", "origin", "https://github.com/CultureBotAI/EdgeMech.git")
    git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
        "commit", "--allow-empty", "-qm", "Fixture base")
    review["source"]["git_revision"] = git("rev-parse", "HEAD")
    result = module.save_occurrence_review(root, review, "packet.json", "proofs.json")
    persisted = read_review(root, result["review"])
    replay = module.validate_occurrence_review(root, persisted, "packet.json", "proofs.json")
    assert persisted["assessments"] == review["assessments"]
    assert persisted["completion"] == "partial"
    assert persisted["verdict"] == "needs_curation"
    assert replay["assessments"]["claim"] == "SUPPORTED_AS_STATED"
    assert replay["assessments"][axis] == model_category
    assert replay["kg_admissions"] == 0
    assert (root / result["review"]).stat().st_size > 0
    assert (root / result["review"]).with_suffix(".md").stat().st_size > 0

    # Even after required checks become available, this unresolved/defective
    # axis alone prevents an unqualified pass; all other axes are supported.
    persisted.update(completion="completed", verdict="pass")
    persisted["checks"][0].update(status="passed")
    with pytest.raises(ReviewError, match="unknown or concerning"):
        module.validate_occurrence_review(root, persisted, "packet.json", "proofs.json")


def test_152_supported_claim_does_not_waive_exact_evidence(supported_partial_case):
    case = supported_partial_case
    case[2]["proofs"][0]["scope"] = "partial"
    repin_sidecar(case)
    with pytest.raises(ReviewError, match="exact-scope"):
        validate(case)


def test_152_supported_claim_does_not_prove_incorrect_model(supported_partial_case):
    case = supported_partial_case
    category(case[1], "relation", "INCORRECT")
    with pytest.raises(ReviewError, match="Resolved modeling judgment requires versioned authority"):
        validate(case)


def test_152_supported_claim_does_not_complete_unavailable_checks(supported_partial_case):
    case = supported_partial_case
    case[1]["completion"] = "completed"
    with pytest.raises(ReviewError, match="unavailable required checks cannot be a completed review"):
        validate(case)


def test_152_supported_claim_does_not_complete_unassessed_model(supported_partial_case):
    case = supported_partial_case
    case[1]["completion"] = "completed"
    case[1]["checks"][0]["status"] = "passed"
    category(case[1], "relation", "UNASSESSED")
    with pytest.raises(ReviewError, match="Completed reviews cannot contain unassessed axes"):
        validate(case)


def test_127_abstract_replays_literal_markup_derivative_without_promoting_scope(case):
    quote = "The exact strain was non-motile."
    install_abstract(case, markup="<p>The exact strain was <i>non-motile</i>.</p>", quote=quote)
    result = validate(case)
    assert result["verified_quotes"] == 1
    assert result["assessments"]["claim"] == "INSUFFICIENT_EVIDENCE"
    assert result["assessments"]["literature"] == "PARTIAL"
    assert result["kg_admissions"] == 0
    assert result["native_capability_enabled"] is False


@pytest.mark.parametrize(("claim", "literature", "role"), [
    ("SUPPORTED_AS_STATED", "SUPPORTS", "supports"),
    ("CONTRADICTED_AS_STATED", "REFUTES", "refutes"),
])
def test_127_exact_abstract_role_is_required_for_directional_judgment(abstract_case, claim, literature, role):
    case = abstract_case
    category(case[1], "claim", claim)
    category(case[1], "literature", literature)
    with pytest.raises(ReviewError, match="exact-scope"):
        validate(case)
    case[2]["proofs"][0].update(scope="exact", support=role)
    case[1]["evidence"][0]["support"] = role
    repin_sidecar(case)
    assert validate(case)["assessments"]["claim"] == claim


@pytest.mark.parametrize("damage", [
    "wrong_pmid", "leading_zero_pmid", "numeric_pmid", "wrong_doi", "numeric_doi",
    "wrong_title", "numeric_title", "wrong_pmcid", "fabricated_pmcid", "wrong_url",
    "full_text_extent", "full_text_locator", "quote", "span", "extractor", "raw_hash",
    "claim_axis_only", "literature_axis_only", "authority_kind",
])
def test_127_abstract_proof_and_evidence_cannot_misrepresent_primary_text(abstract_case, damage):
    case = abstract_case
    proof, evidence = case[2]["proofs"][0], case[1]["evidence"][0]
    if damage == "wrong_pmid":
        proof["pmid"] = "789"
    elif damage == "leading_zero_pmid":
        proof["pmid"] = "0456"
    elif damage == "numeric_pmid":
        proof["pmid"] = 456
    elif damage == "wrong_doi":
        proof["doi"] = "10.1234/other"
    elif damage == "numeric_doi":
        proof["doi"] = 123
    elif damage == "wrong_title":
        proof["title"] = "A different study"
    elif damage == "numeric_title":
        proof["title"] = 123
    elif damage == "wrong_pmcid":
        proof["pmcid"] = 123
    elif damage == "fabricated_pmcid":
        proof["pmcid"] = "PMC123"
    elif damage == "wrong_url":
        proof["reference"] = evidence["reference"] = "https://doi.org/10.1234/other"
    elif damage == "full_text_extent":
        proof["inspected_extent"] = "full_text"
    elif damage == "full_text_locator":
        evidence["locator"] = evidence["locator"].replace("abstract;", "full text;")
    elif damage == "quote":
        evidence["quote"] = "An invented observation."
    elif damage == "span":
        proof["end"] += 1
    elif damage == "extractor":
        proof["extractor"] = "edgemech-literal-text/v1"
    elif damage == "raw_hash":
        evidence["snapshot_sha256"] = "0" * 64
    elif damage == "claim_axis_only":
        proof["axes"] = ["claim"]
    elif damage == "literature_axis_only":
        proof["axes"] = ["literature"]
    else:
        evidence["kind"] = "authority"
    repin_sidecar(case)
    with pytest.raises((ReviewError, CurationError)):
        validate(case)


@pytest.mark.parametrize("damage", [
    "wrong_id", "wrong_source", "numeric_pmid", "empty_title", "duplicate_pmid",
    "duplicate_doi", "duplicate_pmcid", "absent_abstract", "empty_abstract", "markup_only",
    "abstract_list", "numeric_doi", "numeric_pmcid", "malformed_results", "boolean_hits",
    "truncated_results", "missing_hits", "oversized_results",
])
def test_127_malformed_or_ambiguous_primary_records_fail_even_with_repinned_input(abstract_case, damage):
    root, review, sidecar = case = abstract_case
    response = json.loads((root / "abstract.json").read_text())
    record = response["resultList"]["result"][0]
    if damage == "wrong_id":
        record["id"] = "789"
    elif damage == "wrong_source":
        record["source"] = "PMC"
    elif damage == "numeric_pmid":
        record["pmid"] = 456
    elif damage == "empty_title":
        record["title"] = " "
    elif damage in {"duplicate_pmid", "duplicate_doi", "duplicate_pmcid"}:
        other = deepcopy(record)
        other["title"] = "Conflicting duplicate; do not select by title"
        if damage != "duplicate_pmid":
            other["id"] = other["pmid"] = "789"
        if damage == "duplicate_pmcid":
            record["pmcid"] = other["pmcid"] = "PMC123"
            other["doi"] = "10.1234/other"
        response["resultList"]["result"].append(other)
        response["hitCount"] = 2
    elif damage == "absent_abstract":
        del record["abstractText"]
    elif damage == "empty_abstract":
        record["abstractText"] = " "
    elif damage == "markup_only":
        record["abstractText"] = "<p></p>"
    elif damage == "abstract_list":
        record["abstractText"] = ["Not literal primary text"]
    elif damage == "numeric_doi":
        record["doi"] = 123
    elif damage == "numeric_pmcid":
        record["pmcid"] = 123
    elif damage == "malformed_results":
        response["resultList"]["result"] = {"result": record}
    elif damage == "boolean_hits":
        response["hitCount"] = True
    elif damage == "truncated_results":
        response["hitCount"] = 2
    elif damage == "missing_hits":
        del response["hitCount"]
    else:
        response["resultList"]["result"] *= 1001
        response["hitCount"] = 1001
    updated = write(root, "abstract.json", response)
    next(i for i in review["source"]["inputs"] if i["path"] == "abstract.json").update(updated)
    sidecar["proofs"][0]["input"] = updated
    review["evidence"][0]["snapshot_sha256"] = updated["sha256"]
    repin_sidecar(case)
    with pytest.raises(ReviewError):
        validate(case)


def test_127_duplicate_json_keys_and_oversized_raw_response_are_rejected(abstract_case):
    root, _, sidecar = abstract_case
    raw = (root / "abstract.json").read_bytes()
    duplicate = raw.replace(b'"pmid": "456"', b'"pmid": "789", "pmid": "456"')
    with pytest.raises(ReviewError):
        module._europepmc_abstract(duplicate, sidecar["proofs"][0])
    with pytest.raises(ReviewError, match="bounded input size"):
        module._europepmc_abstract(b" " * (module.MAX_BYTES + 1), sidecar["proofs"][0])


def test_127_missing_doi_uses_verified_pmid_and_explicit_reason(case):
    install_abstract(case, doi="")
    assert validate(case)["verified_quotes"] == 1
    del case[2]["proofs"][0]["missing_doi_reason"]
    repin_sidecar(case)
    with pytest.raises(ReviewError, match="missing DOI reason"):
        validate(case)
    case[2]["proofs"][0]["missing_doi_reason"] = "Absent in retained primary record"
    case[2]["proofs"][0]["reference"] = "https://pubmed.ncbi.nlm.nih.gov/789/"
    case[1]["evidence"][0]["reference"] = "https://pubmed.ncbi.nlm.nih.gov/789/"
    repin_sidecar(case)
    with pytest.raises(ReviewError, match="bound PMID URL"):
        validate(case)


@pytest.mark.parametrize("alias", ["doi", "pmid", "pmcid", "pmcid_omitted", "distinct"])
def test_127_abstract_and_jats_share_publication_quote_budget_through_verified_aliases(case, alias):
    root, review, sidecar = case
    jats_proof, jats_evidence = deepcopy(sidecar["proofs"][0]), deepcopy(review["evidence"][0])
    # The JATS's verified PMID is included even when old proofs did not declare it.
    raw = (root / "paper.xml").read_text().replace(
        "<title-group>", '<article-id pub-id-type="pmid">456</article-id><title-group>')
    (root / "paper.xml").write_text(raw)
    new_pin = pin(root, "paper.xml")
    next(i for i in review["source"]["inputs"] if i["path"] == "paper.xml").update(new_pin)
    jats_proof["input"] = new_pin
    jats_evidence["snapshot_sha256"] = new_pin["sha256"]
    quote = " ".join("word" + str(i) for i in range(20))
    install_abstract(case, pmid="456" if alias == "pmid" else "789",
                     doi="10.1234/fixture" if alias == "doi" else "",
                     pmcid="PMC123" if alias.startswith("pmcid") else None, quote=quote)
    if alias == "pmcid_omitted":
        # Omitting the declared alias cannot hide the verified raw metadata.
        del sidecar["proofs"][0]["pmcid"]
    jats_proof["evidence_id"] = jats_evidence["evidence_id"] = "full-paper"
    link_proof(case, jats_proof, jats_evidence)
    if alias == "distinct":
        assert validate(case)["verified_quotes"] == 2
    else:
        with pytest.raises(ReviewError, match="25-word excerpt per source"):
            validate(case)


def test_127_abstract_save_readback_replays_retained_input(abstract_case):
    root, review, _ = abstract_case
    def git(*args):
        return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.PIPE).decode().strip()
    git("init", "-q")
    git("remote", "add", "origin", "https://github.com/CultureBotAI/EdgeMech.git")
    git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
        "commit", "--allow-empty", "-qm", "Fixture base")
    review["source"]["git_revision"] = git("rev-parse", "HEAD")
    result = module.save_occurrence_review(root, review, "packet.json", "proofs.json")
    persisted = read_review(root, result["review"])
    assert result["verified_quotes"] == 1
    assert persisted["evidence"][0]["locator"].startswith("abstract;")
    assert (root / result["review"]).stat().st_size > 0
    with pytest.raises(ReviewError, match="immutable"):
        module.save_occurrence_review(root, review, "packet.json", "proofs.json")
    (root / "abstract.json").write_text("changed retained response")
    with pytest.raises(ReviewError, match="changed"):
        module.validate_occurrence_review(root, persisted, "packet.json", "proofs.json")


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
