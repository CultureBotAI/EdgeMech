"""Bounded candidate packets preserve inherited assertions without granting approval."""

from __future__ import annotations

from copy import deepcopy
from importlib.resources import files
from typing import Any

from kg_microbe_curation.contract import unprocessed_decision, validate_bundle
from kg_microbe_curation.identity import (
    CONTRACT,
    CurationError,
    content_id,
    context_id,
    sha256_json,
)
from kg_microbe_curation.native import validate_native_assertion

POLICY = {
    "name": "edgemech-inherited-candidate-packet/v1",
    "meaning": "Exact envelope transport; no biological normalization or approval",
    "decision": "deferred/withheld",
    "claims": "none; candidate membership does not assert a KG claim",
}


def inherited_bundle(
    input_sha256: str,
    membership: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    """Bind caller-selected occurrence IDs to complete native candidate envelopes.

    Callers must derive membership from verified input rows. This function checks
    the bounded canonical contract, not source authenticity or match eligibility.
    The observation is a fingerprint of a candidate packet, never an invented
    native assay/experiment identity. A withheld native mapping remains scoped to
    its own payload; it is not turned into a ban on all edges with that endpoint.
    """
    import hashlib

    schema = files("kg_microbe_curation").joinpath("schema/native_assertion.json").read_bytes()
    interpretation = {
        "normalization_contract": POLICY["name"],
        "normalizer_contract_sha256": sha256_json(POLICY),
        "schema_sha256": hashlib.sha256(schema).hexdigest(),
        "prefix_map_sha256": sha256_json({}),
    }
    bundle: dict[str, Any] = {
        "contract": CONTRACT,
        "input_sha256": input_sha256,
        "occurrence_ids": list(membership),
        "decisions": [], "observations": [], "claims": [], "reviews": [],
    }
    observations = {}
    for occurrence, candidates in membership.items():
        if not candidates:
            raise CurationError("Inherited packets require at least one native candidate")
        ids = []
        for candidate in candidates:
            validate_native_assertion(candidate)
            ids.append(candidate["assertion_id"])
        if len(set(ids)) != len(ids):
            raise CurationError("Duplicate native candidate in occurrence membership")
        payload = {
            "context": {"scope": "native_review_candidates", "candidate_assertion_ids": ids},
            "interpretation": interpretation,
            "native_assertions": deepcopy(candidates),
            "independent_scientific_review": False,
        }
        observation = {
            "observation_id": content_id("observation", payload),
            "context_id": context_id(payload["context"]),
            "payload": payload,
        }
        observations[observation["observation_id"]] = observation
        decision = unprocessed_decision(occurrence)
        decision.update(
            review_state="deferred", observation_id=observation["observation_id"],
            rationale="Inherited native candidate envelopes retained. Exact occurrence-level "
            "scientific review has not been performed; no KG claim is approved.",
        )
        bundle["decisions"].append(decision)
    bundle["observations"] = list(observations.values())
    validate_bundle(bundle, expected_input_sha256=input_sha256,
                    expected_occurrence_ids=membership)
    return bundle
