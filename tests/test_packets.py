"""Candidate packet transport cannot upgrade inherited review into KG approval."""

from copy import deepcopy

import pytest
from kg_microbe_curation.contract import validate_bundle
from kg_microbe_curation.identity import CurationError, sha256_json
from kg_microbe_curation.native import NATIVE_CONTRACT, native_assertion_id

from edgemech.packets import inherited_bundle


def native(status="withheld"):
    locator = {"repository": "Example/Mech", "commit": "a" * 40,
               "path": "native.json", "selector": {"position": 1}}
    payload = {"native": "complete original row", "target": None}
    review = {"disposition": status, "reason": "Scope remains native"}
    assertion = {
        "contract": NATIVE_CONTRACT,
        "native_locator": {**locator, "source_sha256": "b" * 64,
                           "payload_sha256": sha256_json(payload)},
        "payload": {"subject": "Native:1", "predicate": "skos:exactMatch", "object": None,
                    "native_payload": payload,
                    "context": {"scope": "mapping_only", "withheld_is_global_ban": False},
                    "interpretation": {"normalization_contract": "test-exact/v1",
                                       "normalizer_contract_sha256": "c" * 64,
                                       "schema_sha256": "d" * 64, "prefix_map_sha256": "e" * 64}},
        "evidence": [{"evidence_id": "native", "locator": locator,
                      "sha256": "b" * 64, "ancestry": []}],
        "native_review": {"status": status, "locator": locator, "sha256": "b" * 64,
                          "payload": review, "payload_sha256": sha256_json(review),
                          "rationale": "Inherited native withhold"},
        "assurance": "native_withheld_decision",
        "limitations": ["No KG occurrence review"], "independent_scientific_review": False,
    }
    assertion["assertion_id"] = native_assertion_id(assertion)
    return assertion


def test_complete_native_payload_scope_and_withhold_survive_packet():
    assertion = native()
    original = deepcopy(assertion)
    occurrences = ["urn:kg-microbe:occurrence:v1:" + value * 64 for value in ("1", "2")]
    bundle = inherited_bundle("3" * 64, {item: [assertion] for item in occurrences})
    validate_bundle(bundle, expected_occurrence_ids=occurrences)
    assert bundle["occurrence_ids"] == occurrences
    assert len(bundle["observations"]) == 1
    assert bundle["observations"][0]["payload"]["native_assertions"] == [original]
    assert assertion == original
    assert bundle["claims"] == bundle["reviews"] == []
    assert all(d["disposition"] == "withheld" and d["review_state"] == "deferred"
               and d["review_ids"] == [] for d in bundle["decisions"])


def test_empty_duplicate_and_tampered_candidates_fail_closed():
    occurrence = "urn:kg-microbe:occurrence:v1:" + "1" * 64
    assertion = native()
    with pytest.raises(CurationError, match="at least one"):
        inherited_bundle("2" * 64, {occurrence: []})
    with pytest.raises(CurationError, match="Duplicate"):
        inherited_bundle("2" * 64, {occurrence: [assertion, assertion]})
    assertion["payload"]["context"]["scope"] = "all KG edges"
    with pytest.raises(CurationError, match="identity mismatch"):
        inherited_bundle("2" * 64, {occurrence: [assertion]})
