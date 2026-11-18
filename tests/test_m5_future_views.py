"""The future disclosure is specific; frozen v3 projections remain replayable."""
import copy
import hashlib
import sys
from pathlib import Path

import pytest
from test_m5_round02_views import packet

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts/adhoc"))
import prepare_m5_future_views_20261117 as future  # noqa: E402
import prepare_m5_round02_views_20261116 as prior  # noqa: E402


@pytest.fixture
def mixed_packet(monkeypatch):
    source = packet()
    # Synthetic mixed meaning/status text; actual original bytes stay private.
    source["endpoints"]["object"]["record"]["description"] = (
        "Reviewed source-local process meaning for original_field: Synthetic α definition. "
        "This does not establish a neighboring process or organism-level confirmation. "
        "Reviewed vocabulary: version-1; source locator: exact-row. "
        "The reviewed vocabulary version does not establish the generating version of the saved CSV."
    )
    raw = source["endpoints"]["object"]["record"]["description"].encode()
    monkeypatch.setattr(future, "MIXED_DESCRIPTION_SHA256", hashlib.sha256(raw).hexdigest())
    return source


def test_future_projection_preserves_mixed_semantics_and_bounds_only_status_tokens(mixed_packet):
    source = mixed_packet
    source["source_records"].append({"text": "Counterevidence and substantive definition remain."})
    before = copy.deepcopy(source)
    view = future.projection(source)
    old = prior.projection(source)
    assert source == before
    without_restored_description = copy.deepcopy(view)
    without_restored_description["endpoints"]["object"]["record"].pop("description")
    assert {k: v for k, v in without_restored_description.items() if k != "blinding"} == {
        k: v for k, v in old.items() if k != "blinding"}
    assert view["blinding"]["version"] == "edgemech-blinded-view/v4"
    assert old["blinding"]["version"] == "edgemech-blinded-view/v3"
    assert "cannot be blinded" in old["blinding"]["exposure"]
    assert "cannot be blinded" not in view["blinding"]["exposure"]
    raw = source["endpoints"]["object"]["record"]["description"].encode()
    omissions = view["blinding"]["bounded_omissions"]
    assert len(omissions) == 3
    for omission in omissions:
        part = raw[omission["source_byte_start"]:omission["source_byte_end"]]
        assert part in {b"Reviewed ", b"reviewed "}
        assert omission["sha256"] == hashlib.sha256(part).hexdigest()
        assert omission["source_field_sha256"] == hashlib.sha256(raw).hexdigest()
    spans = view["blinding"]["retained_semantic_spans"]
    reconstructed = b"".join(raw[span["source_byte_start"]:span["source_byte_end"]]
                             for span in spans).decode()
    assert reconstructed == view["endpoints"]["object"]["record"]["description"]
    assert reconstructed == raw.decode().replace("Reviewed ", "").replace("reviewed ", "")
    assert "Synthetic α definition" in reconstructed
    assert "does not establish a neighboring process" in reconstructed
    assert "vocabulary version does not establish the generating version" in reconstructed
    assert "version-1; source locator: exact-row" in reconstructed
    assert sum(item["source_byte_end"] - item["source_byte_start"]
               for item in [*omissions, *spans]) == len(raw)
    assert {x["pointer"] for x in view["blinding"]["retained_field_bindings"]} == {
        "/" + key for key in future.original.FIELDS}
    assert view["source_records"] == source["source_records"]


def test_future_projection_does_not_infer_additional_omissions_from_evaluative_words(mixed_packet):
    source = mixed_packet
    source["source_records"] = [{"text": "Reviewed biological definition is contrary evidence."}]
    source["endpoints"]["object"]["record"]["name"] = "supported substantive process label"
    view = future.projection(source)
    assert view["source_records"] == source["source_records"]
    assert view["endpoints"]["object"]["record"]["name"].startswith("supported")
    assert len(view["blinding"]["bounded_omissions"]) == 3


def test_changed_mixed_definition_requires_new_content_inspection(mixed_packet):
    mixed_packet["endpoints"]["object"]["record"]["description"] += " Changed substantive meaning."
    with pytest.raises(ValueError, match="Mixed original description changed"):
        future.projection(mixed_packet)
