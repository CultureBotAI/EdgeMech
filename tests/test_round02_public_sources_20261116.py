"""Arbitrary source publication needs exact file coverage and identified review."""
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts/adhoc"))
SPEC = importlib.util.spec_from_file_location(
    "public_source_gate", ROOT / "scripts/adhoc/gate_round02_public_sources_20261116.py")
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


def test_python_escaped_literals_are_counted_as_their_rendered_quote():
    raw = b'QUOTE = "two words\\n" "three more words"\n'
    assert "two words three more words" in m.literals(Path("example.py"), raw)


def test_unreviewed_prose_attestation_is_not_inferred(tmp_path):
    with pytest.raises(ValueError, match="attestation"):
        m.gate({"root": str(tmp_path), "review_attestation": {"reviewer": "agent"}})


def test_missing_new_file_invalidates_earlier_review(tmp_path, monkeypatch):
    monkeypatch.setattr(m, "proposed_sources", lambda root, baseline: {"new.md"})
    with pytest.raises(ValueError, match="inventory differs"):
        m.gate({"root": str(tmp_path), "baseline": "HEAD", "files": [],
                "review_attestation": {"reviewer": "agent", "all_files_inspected": True,
                                       "no_unaccounted_external_quotations": True}})


@pytest.mark.parametrize("extra_words,passed", [(0, True), (20, False)])
def test_identical_excerpt_keeps_each_publication_budget(tmp_path, monkeypatch, extra_words, passed):
    shared = " ".join(f"shared{i}" for i in range(10))
    extra = " ".join(f"unique{i}" for i in range(extra_words))
    raw = (shared + "\n" + extra).encode()
    (tmp_path / "proposal.md").write_bytes(raw)
    quotes = [{"quote": shared, "aliases": {"doi:10.1234/a"},
               "sha256": m.publication.text_hash(shared)},
              {"quote": shared, "aliases": {"doi:10.1234/b"},
               "sha256": m.publication.text_hash(shared)}]
    if extra_words:
        quotes.append({"quote": extra, "aliases": {"doi:10.1234/a"},
                       "sha256": m.publication.text_hash(extra)})
    monkeypatch.setattr(m, "catalog", lambda specs: quotes)
    monkeypatch.setattr(m, "proposed_sources", lambda root, baseline: {"proposal.md"})
    result = m.gate({
        "root": str(tmp_path), "baseline": "HEAD", "quote_catalog_reviews": [],
        "files": [{"path": "proposal.md", "sha256": m.publication.digest(raw),
                   "classification": "catalog_literals",
                   "quote_sha256s": sorted({q["sha256"] for q in quotes})}],
        "review_attestation": {"reviewer": "fixture", "all_files_inspected": True,
                               "no_unaccounted_external_quotations": True},
    })
    budgets = {tuple(source["source_identities"]): source["deduplicated_quote_words"]
               for source in result["sources"]}
    assert budgets == {("doi:10.1234/a",): 10 + extra_words, ("doi:10.1234/b",): 10}
    assert result["passed"] is passed
