"""Derived coverage accounting; cohort disposition is not individual scientific review.

This local presentation view does not change CLAW contracts or legacy decisions.
It reads bounded manifests/bundles and the selected cohort, never the full census.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from kg_microbe_curation.contract import validate_bundle
from kg_microbe_curation.identity import CurationError

from .content_inventory import _write_json
from .evidence_campaign import load_cohort
from .literature_cache import LiteratureCache, load_retrieval, verify_quote
from .source_capture import LIMITATION as CAPTURE_LIMITATION
from .source_capture import capture_quote, load_source_captures
from .storage.parquet import file_hash, safe_path

FORMAT = "edgemech-derived-review-coverage/v1"
MAX_JSON_BYTES = 64 * 1024**2
OCCURRENCE = re.compile(r"urn:kg-microbe:occurrence:v1:[0-9a-f]{64}")


def _checked(path: Path, expected: str):
    path = safe_path(path)
    if path.stat().st_size > MAX_JSON_BYTES:
        raise CurationError("Coverage JSON exceeds bounded input size")
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise CurationError(f"Coverage input hash mismatch: {path}")
    return json.loads(data)


def _ids(values, label):
    values = list(values)
    if any(not isinstance(value, str) or not OCCURRENCE.fullmatch(value) for value in values):
        raise CurationError(f"Invalid occurrence ID in {label}")
    if len(values) != len(set(values)):
        raise CurationError(f"Duplicate occurrence ID in {label}")
    return set(values)


def _count(value, label):
    if type(value) is not int or value < 0:
        raise CurationError(f"Invalid count: {label}")
    return value


def _quote_fields(value):
    if isinstance(value, dict):
        return sum(bool(item) for key, item in value.items() if key == "quote") + sum(
            _quote_fields(item) for item in value.values())
    if isinstance(value, list):
        return sum(_quote_fields(item) for item in value)
    return 0


def _legacy(ledger, expected):
    manifest = _checked(ledger, expected)
    if manifest["contract"] != "edgemech-full-snapshot-review-ledger/v1":
        raise CurationError("Unsupported legacy coverage ledger")
    source_sha = manifest["kg_source_manifest_sha256"]
    census = _checked(Path(manifest["census_manifest_path"]), manifest["census_manifest_sha256"])
    population = _count(manifest["total_snapshot_occurrences"], "population")
    if (census["source"]["manifest_sha256"] != source_sha
            or census["source"]["source_rows"] != population
            or census["source"]["selected_rows"] != population
            or census["source"]["complete_export"] is not True):
        raise CurationError("Legacy ledger does not bind the complete census population")
    artifacts = manifest["artifacts"]
    index = _checked(Path(artifacts["individual_decision_index_593_path"]),
                     artifacts["individual_decision_index_593_sha256"])
    index_ids = _ids((item["occurrence_id"] for item in index), "legacy index")
    waves, union = {}, set()
    for name, entry in sorted(manifest["waves"].items()):
        bundle = _checked(Path(entry["bundle_path"]), entry["bundle_sha256"])
        if bundle["input_sha256"] != source_sha:
            raise CurationError("Legacy wave belongs to another source population")
        ids = _ids((item["occurrence_id"] for item in bundle["decisions"]), "wave decisions")
        if ids != _ids(bundle["occurrence_ids"], "wave occurrences"):
            raise CurationError("Legacy wave decision coverage mismatch")
        waves[name] = {
            "bundle_sha256": entry["bundle_sha256"], "individual_decision_ids": len(ids),
            "overlap_with_earlier_waves": len(union & ids),
            "dispositions": dict(Counter(item["disposition"] for item in bundle["decisions"])),
            "nonempty_quote_fields_not_verified": _quote_fields(bundle),
        }
        union |= ids
    if union != index_ids:
        raise CurationError("Legacy wave ID union differs from individual decision index")
    cohorts = _checked(Path(artifacts["cohort_decision_table_368_path"]),
                       artifacts["cohort_decision_table_368_sha256"])
    if (len(cohorts) != manifest["total_snapshot_cohorts"]
            or len({row["cohort_key"] for row in cohorts}) != len(cohorts)):
        raise CurationError("Legacy cohort identity/count mismatch")
    totals = {key: sum(_count(row[key], key) for row in cohorts) for key in (
        "population_occurrences", "individually_reviewed_occurrences", "cohort_bound_occurrences")}
    if any(row["population_occurrences"] != row["individually_reviewed_occurrences"]
           + row["cohort_bound_occurrences"] for row in cohorts):
        raise CurationError("Legacy cohort disposition accounting mismatch")
    if totals["population_occurrences"] != population or totals["individually_reviewed_occurrences"] != len(union):
        raise CurationError("Legacy cohort totals do not reconcile")
    disposition_counts = Counter()
    for row in cohorts:
        disposition_counts[row["disposition"]] += row["population_occurrences"]
    return manifest, union, {
        "population_disposition_coverage": population,
        "cohort_bound_only_occurrences": totals["cohort_bound_occurrences"],
        "individual_prior_decision_ids": len(union),
        "legacy_claimed_reviewed_occurrences": manifest["coverage_summary"]["reviewed_occurrences"],
        "dispositions": dict(disposition_counts), "waves": waves,
        "individual_index_sha256": artifacts["individual_decision_index_593_sha256"],
        "cohort_table_sha256": artifacts["cohort_decision_table_368_sha256"],
        "scientific_review_coverage": "not_established_by_legacy_dispositions",
    }


def _current(cohort, cohort_sha, retrieval, retrieval_sha, cache, adjudication, adjudication_sha):
    _checked(cohort / "manifest.json", cohort_sha)
    source, rows, _ = load_cohort(cohort)
    _checked(retrieval / "manifest.json", retrieval_sha)
    with LiteratureCache(cache) as client:
        receipt, documents = load_retrieval(retrieval, client)
    if receipt["cohort_sha256"] != cohort_sha:
        raise CurationError("Coverage retrieval belongs to another cohort")
    manifest = _checked(adjudication / "manifest.json", adjudication_sha)
    bundle = _checked(adjudication / "bundle.json", manifest["bundle_sha256"])
    proofs = _checked(adjudication / "quote-proofs.json", manifest["quote_proofs_sha256"])
    rows_by_id = {row["occurrence_id"]: row for row in rows}
    validate_bundle(bundle, expected_input_sha256=source["source"]["manifest_sha256"],
                    expected_occurrence_ids=rows_by_id)
    reviewed = {item["occurrence_id"] for item in bundle["decisions"] if item["review_state"] == "reviewed"}
    assessed, outcomes, expected_proofs = set(), Counter(), Counter()
    captures, captures_by_target = {}, {}
    required_inputs = {str((cohort / "manifest.json").absolute()): cohort_sha,
                       str((retrieval / "manifest.json").absolute()): retrieval_sha,
                       str((cohort / "occurrences.json").absolute()): source["occurrences_sha256"]}
    for envelope in bundle["reviews"]:
        review = envelope["document"]
        if review["scientific_review"] is not True or review["completion"] != "completed":
            raise CurationError("Coverage requires completed explicit scientific reviews")
        inputs = {str(safe_path(Path(item["path"]))): item["sha256"] for item in review["source"]["inputs"]}
        if any(inputs.get(path) != digest for path, digest in required_inputs.items()):
            raise CurationError("Scientific review does not bind the selected inputs")
        for path, digest in inputs.items():
            if file_hash(Path(path)) != digest:
                raise CurationError("Scientific review source input changed")
        review_captures = {}
        for item in review["source"]["inputs"]:
            if item.get("role") == "manually identified tool-extracted primary evidence manifest":
                loaded, capture_inputs = load_source_captures(item)
                if any(inputs.get(str(safe_path(Path(entry["path"])))) != entry["sha256"]
                       for entry in capture_inputs):
                    raise CurationError("Source capture snapshot is not bound by scientific review inputs")
                for capture_id, capture in loaded.items():
                    if capture_id in captures and captures[capture_id] != capture:
                        raise CurationError("Conflicting source capture IDs across scientific reviews")
                    captures[capture_id] = review_captures[capture_id] = capture
        evidence = {item["evidence_id"]: item for item in review["evidence"]}
        for assessment in review["assessments"]:
            for key in assessment["target_ids"]:
                if key in assessed or key not in rows_by_id:
                    raise CurationError("Coverage requires one explicit assessment per selected occurrence")
                assessed.add(key)
                captures_by_target[key] = set(review_captures)
                outcomes[assessment["outcome"]] += 1
                for evidence_id in assessment["evidence_ids"]:
                    item = evidence[evidence_id]
                    if item.get("quote"):
                        if item["kind"] != "primary_source":
                            raise CurationError("Scientific quote coverage requires primary-source evidence")
                        expected_proofs[(key, item["quote"], item["snapshot_sha256"], item["locator"])] += 1
    if assessed != reviewed:
        raise CurationError("Explicit scientific assessment IDs differ from reviewed decision IDs")
    actual_proofs, quoted_ids, representations = Counter(), set(), Counter()
    used_captures = False
    for proof in proofs:
        key = proof["occurrence_id"]
        if key not in assessed or proof["reference"] not in rows_by_id[key]["references"] or rows_by_id[key]["warnings"]:
            raise CurationError("Quote proof is not bound to an assessed occurrence citation")
        if "capture_id" in proof:
            if proof["capture_id"] not in captures_by_target[key]:
                raise CurationError("Quote proof capture is not bound by this target's scientific review")
            _, rebuilt, locator = capture_quote(captures, proof)
            used_captures = True
        else:
            entry = documents.get(proof["reference"], {})
            candidates = [doc for doc in entry.get("documents", [])
                          if doc["kind"] == proof["kind"] and doc["extractor"] == proof["extractor"]]
            if len(candidates) != 1:
                raise CurationError("Missing or ambiguous proof document")
            rebuilt = verify_quote(candidates[0], proof["quote"])
            locator = (f"{proof['kind']} chars {proof['start']}:{proof['end']}; "
                       f"text_sha256={proof['text_sha256']}; {proof['extractor']}")
        if proof != {"occurrence_id": key, "reference": proof["reference"], **rebuilt}:
            raise CurationError("Quote proof differs from source response")
        actual_proofs[(key, proof["quote"], proof["response_sha256"], locator)] += 1
        quoted_ids.add(key)
        representations[proof["kind"]] += 1
    if actual_proofs != expected_proofs:
        raise CurationError("Quote proofs do not exactly cover scientific evidence per occurrence")
    counts = {"occurrences": len(rows), "scientific_assessments": len(assessed),
              "deferred_occurrences": len(rows) - len(assessed), "verified_quotes": len(proofs)}
    if any(manifest[key] != value for key, value in counts.items()):
        raise CurationError("Adjudication manifest counts differ from canonical artifacts")
    if any(manifest["outcomes"].get(key, 0) != outcomes.get(key, 0)
           for key in set(manifest["outcomes"]) | set(outcomes)):
        raise CurationError("Adjudication outcome counts differ from assessments")
    if any(item["disposition"] != "withheld" for item in bundle["decisions"]) or bundle["claims"]:
        raise CurationError("Coverage view is scoped to withheld scientific pilot decisions")
    return source, assessed, {
        **counts, "outcomes": dict(outcomes), "occurrences_with_verified_quotes": len(quoted_ids),
        "quote_representations": dict(representations),
        "evidence_representation_limitations": [CAPTURE_LIMITATION] if used_captures else [],
        "kg_admissions": 0, "bundle_sha256": manifest["bundle_sha256"],
        "quote_proofs_sha256": manifest["quote_proofs_sha256"],
    }


def build_coverage(ledger: Path, ledger_sha: str, cohort: Path, cohort_sha: str,
                   retrieval: Path, retrieval_sha: str, cache: Path, adjudication: Path,
                   adjudication_sha: str, output: Path):
    """Publish a new immutable view; never rewrite or promote legacy artifacts."""
    legacy, prior_ids, prior = _legacy(ledger, ledger_sha)
    source, assessed, current = _current(cohort, cohort_sha, retrieval, retrieval_sha, cache,
                                         adjudication, adjudication_sha)
    if (source["source"]["manifest_sha256"] != legacy["kg_source_manifest_sha256"]
            or source["census_sha256"] != legacy["census_manifest_sha256"]):
        raise CurationError("Legacy and scientific coverage refer to different source populations")
    total = legacy["total_snapshot_occurrences"]
    union = prior_ids | assessed
    if len(union) > total:
        raise CurationError("Individual ID union exceeds population")
    view = {"artifact_type": FORMAT, "source_manifest_sha256": legacy["kg_source_manifest_sha256"],
            "census_manifest_sha256": legacy["census_manifest_sha256"], "population_occurrences": total,
            "legacy_disposition_coverage": prior, "current_scientific_coverage": current,
            "distinct_individual_decision_or_assessment_ids": len(union),
            "overlap_prior_and_current_ids": len(prior_ids & assessed),
            "population_without_verified_current_scientific_assessment": total - len(assessed),
            "current_assessed_occurrence_ids": sorted(assessed),
            "individual_decision_or_assessment_ids": sorted(union),
            "inputs": {"ledger_manifest_sha256": ledger_sha, "cohort_manifest_sha256": cohort_sha,
                       "retrieval_manifest_sha256": retrieval_sha,
                       "adjudication_manifest_sha256": adjudication_sha},
            "limitations": [
                "Cohort disposition counts are not individual scientific review coverage.",
                "Prior individual decisions are hash/ID verified, not scientifically revalidated.",
                "Current scientific assessments are explicit agent judgments, not independent agreement.",
                "Verified quotations establish source fidelity, not biological correctness or KG admission.",
                "This bounded view does not scan the full census or replay prior native contracts.",
                "Unincluded campaigns are not counted; legacy artifacts remain unchanged.",
            ] + current["evidence_representation_limitations"]}
    _write_json(safe_path(output, exists=False), view)
    if _checked(output, file_hash(output)) != view:
        raise CurationError("Persisted coverage view differs")
    return view
