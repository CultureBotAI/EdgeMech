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
