"""Cross-review publication budget and exact public-file coverage guards."""
import importlib.util
from pathlib import Path

import pytest

PATH = Path(__file__).parents[1] / "scripts/adhoc/gate_round02_publication_20261116.py"
SPEC = importlib.util.spec_from_file_location("round02_publication", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_cross_reviewer_alias_union_deduplicates_repeated_excerpt():
    groups = []
    MODULE.add_quote(groups, {"doi:10.1/a"}, "same  excerpt", {"reviewer": "a"})
    MODULE.add_quote(groups, {"pmid:42"}, "another excerpt", {"reviewer": "b"})
    MODULE.add_quote(groups, {"doi:10.1/a", "pmid:42", "pmcid:PMC7"},
                     "same excerpt", {"reviewer": "b"})
    inventory = MODULE.quote_inventory(groups)
    assert len(inventory) == 1
    assert inventory[0]["deduplicated_quote_words"] == 4
    assert sum(len(e["occurrences"]) for e in inventory[0]["excerpts"]) == 3


def test_individually_legal_quotes_fail_aggregate_publication_budget():
    groups = []
    MODULE.add_quote(groups, {"doi:10.1/a", "pmid:42"}, " ".join(["a"] * 20), {"case": 1})
    MODULE.add_quote(groups, {"pmid:42", "pmcid:PMC7"}, " ".join(["b"] * 10), {"case": 2})
    inventory = MODULE.quote_inventory(groups)
    assert inventory[0]["deduplicated_quote_words"] == 30
    assert not inventory[0]["within_budget"]


@pytest.mark.parametrize("attack", ["extra", "prose", "missing", "symlink"])
def test_candidate_gate_rejects_unaccounted_public_bytes(tmp_path, attack):
    expected = {"one.json": b'{"quotation_words":0}\n'}
    (tmp_path / "one.json").write_bytes(expected["one.json"])
    if attack == "extra":
        (tmp_path / "extra.md").write_text("unaccounted paper prose")
    elif attack == "prose":
        (tmp_path / "one.json").write_text('{"quote":"unaccounted excerpt"}')
    elif attack == "missing":
        (tmp_path / "one.json").unlink()
    else:
        (tmp_path / "link").symlink_to(tmp_path / "one.json")
    with pytest.raises(ValueError):
        MODULE.inspect_candidate(tmp_path, expected)


def test_partial_round_cannot_claim_two_reviewer_all_ten_coverage():
    with pytest.raises(ValueError, match="both reviewers and all ten"):
        MODULE.coverage({"mode": "round", "reviews": [{"reviewer": "reviewer-a", "case_id": "fresh-05"}]})


def test_canary_cannot_impersonate_scientific_reviewer():
    with pytest.raises(ValueError, match="one operational unit"):
        MODULE.coverage({"mode": "canary", "reviews": [{"reviewer": "reviewer-a", "case_id": "fresh-05"}]})


def test_twenty_labels_cannot_reuse_ten_canonical_pairs(tmp_path):
    import json
    cohort = json.loads((MODULE.ROOT / "artifacts/edge-calibration-20261115/cohort.json").read_text())
    specs = [{"root": str(tmp_path), "review": case["case_id"] + ".yaml",
              "reviewer": reviewer, "case_id": case["case_id"]}
             for reviewer in ("reviewer-a", "reviewer-b") for case in cohort["cases"]]
    with pytest.raises(ValueError, match="Repeated canonical root/review"):
        MODULE.coverage({"mode": "round", "reviews": specs})


@pytest.mark.parametrize("corruption", ["review_id", "identity", "model", "session", "categories"])
def test_canonical_reviews_are_bound_to_distinct_sealed_reviewer_outputs(tmp_path, corruption):
    reviewer = {"id": "reviewer-a", "model": "actual-model", "session_id": "actual-session"}
    axes = {axis: next(iter(values)) for axis, values in MODULE.CATEGORIES.items()}
    initial = {"occurrence_id": "original", "assessments": [
        {"axis": axis, "category": category} for axis, category in axes.items()]}
    bindings = {"reviewer-a": {"root": str(tmp_path), "reviewer": reviewer,
        "canonical_identity": "Actual reviewer A", "cases": {"fresh-05": initial}}}
    spec = {"root": str(tmp_path), "reviewer": "reviewer-a", "case_id": "fresh-05"}
    review = {"review_id": "unique", "reviewer": {"identity": "Actual reviewer A", "model": "actual-model"}}
    proofs = {"identity": dict(reviewer)}
    replay = {"occurrence_id": "original", "assessments": dict(axes)}
    seen = set()
    if corruption == "review_id":
        seen.add("unique")
    elif corruption in {"identity", "model"}:
        review["reviewer"][corruption] = "different"
    elif corruption == "session":
        proofs["identity"]["session_id"] = "other-session"
    else:
        replay["assessments"]["claim"] = "UNASSESSED"
    with pytest.raises(ValueError):
        MODULE.bind_review(spec, review, proofs, replay, bindings, seen)


def test_valid_bound_review_preserves_initial_categories_and_session(tmp_path):
    reviewer = {"id": "reviewer-a", "model": "actual-model", "session_id": "actual-session"}
    axes = {axis: next(iter(values)) for axis, values in MODULE.CATEGORIES.items()}
    case = {"occurrence_id": "original", "assessments": [
        {"axis": axis, "category": category} for axis, category in axes.items()]}
    bindings = {"reviewer-a": {"root": str(tmp_path), "reviewer": reviewer,
        "canonical_identity": "Actual reviewer A", "cases": {"fresh-05": case}}}
    seen = set()
    MODULE.bind_review({"root": str(tmp_path), "reviewer": "reviewer-a", "case_id": "fresh-05"},
                       {"review_id": "unique", "reviewer": {"identity": "Actual reviewer A", "model": "actual-model"}},
                       {"identity": reviewer}, {"occurrence_id": "original", "assessments": axes},
                       bindings, seen)
    assert seen == {"unique"}


@pytest.mark.parametrize("failure", ["changed_matrix", "repeated_session", "wrong_reviewer"])
def test_sealed_reviewer_binding_rejects_receipt_or_identity_mismatch(tmp_path, failure):
    import json
    config = {"mode": "round", "package_sha256": "package", "reviewers": {}}
    for rid in ("reviewer-a", "reviewer-b"):
        reviewer = {"id": rid, "model": "actual-model", "session_id": rid + "-session"}
        if rid == "reviewer-b" and failure == "repeated_session":
            reviewer["session_id"] = "reviewer-a-session"
        if rid == "reviewer-b" and failure == "wrong_reviewer":
            reviewer["id"] = "reviewer-a"
        matrix = {"round_id": "m5-calibration-20261116-round02", "package_sha256": "package",
                  "reviewer": reviewer, "cases": []}
        raw = MODULE.encoded(matrix)
        filename = rid + ".json"
        (tmp_path / filename).write_bytes(raw)
        (tmp_path / (filename + ".receipt.json")).write_text(json.dumps({
            "matrix_path": filename, "matrix_sha256": MODULE.digest(raw),
            "reviewer": reviewer, "package_sha256": "package"}))
        config["reviewers"][rid] = {"root": str(tmp_path), "matrix": filename,
                                    "canonical_identity": rid + " identity"}
    if failure == "changed_matrix":
        (tmp_path / "reviewer-b.json").write_bytes(raw + b"\n")
    with pytest.raises(ValueError):
        MODULE.reviewer_bindings(config)
