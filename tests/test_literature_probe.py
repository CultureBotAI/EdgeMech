"""Identifier equality and ambiguity gates for the one-request retrieval probe."""
import pytest
from kg_microbe_curation.identity import CurationError

from edgemech.literature_probe import identifier, matching_record


@pytest.mark.parametrize("value", ["PMID:0", "PMID:1 OR title:test", "doi:foo", "10.1234/a@b.org"])
def test_reject_nonidentifiers(value):
    with pytest.raises(CurationError):
        identifier(value)


def test_identifier_normalization():
    assert identifier("https://doi.org/10.1234/ABC") == ("doi", "10.1234/abc")
    assert identifier("PMID:123") == ("pmid", "123")


def test_wrong_hit_ambiguous_and_truncated_results():
    record = {"doi": "10.1234/ABC", "id": "123", "source": "MED"}
    data = {"hitCount": 1, "resultList": {"result": [record]}}
    assert matching_record(data, "doi", "10.1234/abc") == record
    assert matching_record(data, "doi", "10.1234/wrong") is None
    assert matching_record(data, "pmid", "123") == record
    record["source"] = "PMC"
    assert matching_record(data, "pmid", "123") is None
    data["hitCount"] = 2
    assert matching_record(data, "doi", "10.1234/abc") is None
    data["resultList"]["result"].append(dict(record))
    assert matching_record(data, "doi", "10.1234/abc") is None
