"""Bind explicit agent/human assessments and literal quotes to canonical CLAW reviews.

No keyword classifier creates scientific decisions. Unannotated occurrences remain
deferred. Supported source interpretations are still withheld from KG admission:
this stage does not synthesize native observations or normalized scientific claims.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

from kg_microbe_curation.contract import decision_digest, unprocessed_decision, validate_bundle
from kg_microbe_curation.identity import CONTRACT, CurationError, sha256_json

from .content_inventory import _write_json
from .evidence_campaign import load_cohort
from .literature_cache import LiteratureCache, load_retrieval, verify_quote
from .pins import check_contracts
from .source_capture import LIMITATION as CAPTURE_LIMITATION
from .source_capture import capture_quote, load_source_captures
from .storage.parquet import file_hash, safe_path

DIMENSIONS = {"taxon", "predicate", "object", "context", "evidence_scope"}
OUTCOMES = {"supported", "concern", "unknown", "not_applicable"}


def adjudicate(cohort: Path, retrieval: Path, cache: Path, annotations: Path,
               output: Path, git_revision: str):
    check_contracts()
    manifest, rows, queue = load_cohort(cohort)
    annotation_bytes = safe_path(annotations).read_bytes()
    annotation_sha = sha256(annotation_bytes).hexdigest()
    notes = json.loads(annotation_bytes)
    if notes["cohort_sha256"] != file_hash(cohort / "manifest.json"):
        raise CurationError("Assessment cohort pin mismatch")
    if notes["retrieval_sha256"] != file_hash(retrieval / "manifest.json"):
        raise CurationError("Assessment retrieval pin mismatch")
    with LiteratureCache(cache) as client:
        receipt, documents = load_retrieval(retrieval, client)
    if receipt["cohort_sha256"] != notes["cohort_sha256"]:
        raise CurationError("Retrieval belongs to another cohort")
    captures, capture_inputs = {}, []
    if "source_capture_manifest" in notes:
        captures, capture_inputs = load_source_captures(notes["source_capture_manifest"])
    interpretation_inputs = []
    seen_paths = set()
    for item in notes.get("interpretation_inputs", []):
        path = safe_path(Path(item["path"]))
        if str(path) in seen_paths or file_hash(path) != item["sha256"]:
            raise CurationError("Interpretation input is duplicate or its pin differs")
        seen_paths.add(str(path))
        try:
            relative = str(path.relative_to(Path.cwd().resolve()))
        except ValueError as error:
            raise CurationError("Interpretation input must be inside the repository") from error
        interpretation_inputs.append({"path": relative, "sha256": item["sha256"],
                                      "role": "review interpretation input"})
    used_captures = False
    selected = {row["occurrence_id"]: row for row in rows}
    annotations_by_id = {}
    for note in notes["assessments"]:
        key = note["occurrence_id"]
        if key not in selected or key in annotations_by_id:
            raise CurationError("Unknown or duplicate assessment occurrence")
        if note["outcome"] not in OUTCOMES or not note["rationale"].strip():
            raise CurationError("Assessment requires an explicit outcome and rationale")
        if set(note["dimensions"]) != DIMENSIONS:
            raise CurationError("Assessment requires taxon, predicate, object, context and scope")
        if not all(isinstance(value, str) and value.strip() for value in note["dimensions"].values()):
            raise CurationError("Assessment dimensions require explanations")
        if note["outcome"] in {"supported", "concern"} and not note.get("quotes"):
            raise CurationError("Supported/concern assessments require verified primary-source quotes")
        if note["outcome"] == "supported" and not any(
            quote["support"] == "supports" for quote in note.get("quotes", [])
        ):
            raise CurationError("Each supported assessment requires a supporting primary-source quote")
        annotations_by_id[key] = note
    if not annotations_by_id:
        raise CurationError("No scientific assessments supplied")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    review_id = now.replace("-", "").replace(":", "") + "-" + notes["review_id"]
    decisions, evidence, checks, assessments, targets, proofs = [], [], [], [], [], []
    for row in rows:
        key = row["occurrence_id"]
        decision = unprocessed_decision(key)
        decision.update(review_state="deferred", rationale="Not individually scientifically assessed "
                        "in this bounded campaign; retrieval availability is not claim support.")
        note = annotations_by_id.get(key)
        if note:
            ordinal = len(assessments) + 1
            evidence_ids = []
            for quote_index, selection in enumerate(note.get("quotes", [])):
                reference = selection["reference"]
                if reference not in row["references"] or row["warnings"]:
                    raise CurationError("Quote source is not an unambiguous citation of this occurrence")
                if "capture_id" in selection:
                    doc, proof, locator = capture_quote(captures, selection)
                    used_captures = True
                else:
                    entry = documents.get(reference)
                    if entry is None:
                        raise CurationError("Quoted document was not retrieved")
                    candidates = [doc for doc in entry["documents"] if doc["kind"] == selection["kind"]]
                    if len(candidates) != 1:
                        raise CurationError("Quote document kind is missing or ambiguous")
                    doc = candidates[0]
                    proof = verify_quote(doc, selection["quote"])
                    locator = (f"{proof['kind']} chars {proof['start']}:{proof['end']}; "
                               f"text_sha256={proof['text_sha256']}; {proof['extractor']}")
                evidence_id = f"paper-{ordinal}-{quote_index}"
                evidence_ids.append(evidence_id)
                proofs.append({"occurrence_id": key, "reference": reference, **proof})
                evidence.append({"evidence_id": evidence_id, "kind": "primary_source",
                                 "reference": doc["response"]["url"],
                                 "locator": locator,
                                 "accessed_at": now, "support": selection["support"],
                                 "summary": selection["summary"], "quote": proof["quote"],
                                 "snapshot_sha256": proof["response_sha256"]})
            record_id = f"record-{ordinal}"
            evidence_ids.append(record_id)
            evidence.append({"evidence_id": record_id, "kind": "record_content",
                             "reference": str(cohort / "occurrences.json"),
                             "locator": f"row_number={row['row_number']}; occurrence_id={key}",
                             "accessed_at": now, "support": "context_only",
                             "summary": "Exact original source row and preserved citation binding.",
                             "snapshot_sha256": row["row_sha256"]})
            conflict = "unresolved" if any(
                quote["support"] == "refutes" for quote in note.get("quotes", [])
            ) else "none_reported"
            decision.update(review_state="reviewed", conflict_state=conflict,
                            review_ids=[review_id], rationale=note["rationale"] +
                            " Disposition remains withheld pending native scoped-claim admission.")
            targets.append({"target_id": key, "path": str(cohort / "occurrences.json"),
                            "selector": f"row_number={row['row_number']}",
                            "label": f"{row['labels']['subject_label']} {row['fields']['predicate']} "
                                     f"{row['labels']['object_label']}", "kind": "snapshot_row",
                            "ownership_note": "Pinned KG-Microbe source occurrence; native owner "
                                              "admission and normalized observation remain unresolved.",
                            "semantic_digest": {"algorithm": "kg-microbe-curation-decision/v1",
                                                "sha256": decision_digest(decision, {}),
                                                "description": "Exact occurrence decision, no inferred observation."}})
            checks.append({"check_id": f"integrity-{ordinal}", "name": "Input and quote binding",
                           "status": "passed", "required": True, "target_ids": [key],
                           "summary": "Original occurrence identity and supplied quote spans verified; "
                                      "integrity does not determine the scientific outcome.",
                           "evidence_ids": evidence_ids})
            assessments.append({"assessment_id": f"science-{ordinal}", "area": "evidence",
                                "topic": "Occurrence-level scientific support", "outcome": note["outcome"],
                                "summary": note["rationale"], "target_ids": [key],
                                "evidence_ids": evidence_ids,
                                "dimensions": [{"name": name, "value": value,
                                                "definition": "Explicit reviewer assessment of " + name,
                                                "evidence_ids": evidence_ids}
                                               for name, value in sorted(note["dimensions"].items())]})
        decisions.append(decision)
    source_sha = manifest["source"]["manifest_sha256"]
    review = {
        "schema_version": "1.0.0", "review_id": review_id, "kind": "batch",
        "repository": "CultureBotAI/EdgeMech", "title": notes["title"],
        "started_at": notes["started_at"], "finished_at": now,
        "reviewer": notes["reviewer"], "skill": "edgemech-literature-adjudication/v1",
        "completion": "completed", "verdict": ("pass_with_limitations" if all(
            item["outcome"] == "supported" for item in assessments) else "needs_curation"),
        "scientific_review": True,
        "summary": "Explicit bounded scientific assessments with quote spans verified against retained evidence. "
                   "Unannotated occurrences remain deferred; no KG admission is granted.",
        "source": {"git_revision": git_revision, "state": "working_tree",
                   "inputs": [{"path": str(cohort / "manifest.json"), "sha256": notes["cohort_sha256"],
                               "role": "exact reviewed cohort"},
                              {"path": str(cohort / "source-manifest.json"),
                               "sha256": source_sha, "role": "canonical occurrence source"},
                              {"path": str(cohort / "occurrences.json"),
                               "sha256": manifest["occurrences_sha256"], "role": "exact source rows"},
                              {"path": str(retrieval / "manifest.json"),
                               "sha256": notes["retrieval_sha256"], "role": "retrieved evidence"},
                              {"path": str(annotations), "sha256": annotation_sha,
                               "role": "explicit reviewer judgments"}] + capture_inputs + interpretation_inputs},
        "scope": {"description": "Individually annotated source occurrences only",
                  "selection": "Bounded literature pilot; no propagation to shared-citation neighbors",
                  "coverage": "full" if len(assessments) == len(rows) else "partial",
                  "population_size": len(rows), "reviewed_target_ids": list(annotations_by_id)},
        "targets": targets, "checks": checks, "evidence": evidence, "assessments": assessments,
        "findings": [], "actions": [],
        "limitations": ["One agent assessment, not independent reviewer agreement.",
                        "Text availability and exact quotes do not establish scientific support.",
                        "No native observations or normalized claims were synthesized."] + (
                            [CAPTURE_LIMITATION] if used_captures else [])}
    bundle = {"contract": CONTRACT, "input_sha256": source_sha, "occurrence_ids": list(selected),
              "decisions": decisions, "observations": [], "claims": [],
              "reviews": [{"review_id": review_id, "sha256": sha256_json(review), "document": review}]}
    validate_bundle(bundle, expected_input_sha256=source_sha, expected_occurrence_ids=selected)
    if file_hash(annotations) != annotation_sha:
        raise CurationError("Reviewer annotations changed during adjudication")
    if any(file_hash(Path(item["path"])) != item["sha256"] for item in interpretation_inputs):
        raise CurationError("Interpretation input changed during adjudication")
    output = safe_path(output, exists=False)
    output.mkdir()
    _write_json(output / "bundle.json", bundle)
    _write_json(output / "quote-proofs.json", proofs)
    persisted = json.loads((output / "bundle.json").read_bytes())
    validate_bundle(persisted, expected_input_sha256=source_sha, expected_occurrence_ids=selected)
    receipt = {"occurrences": len(rows), "scientific_assessments": len(assessments),
               "deferred_occurrences": len(rows) - len(assessments), "verified_quotes": len(proofs),
               "outcomes": {outcome: sum(item["outcome"] == outcome for item in assessments)
                            for outcome in sorted(OUTCOMES)}, "kg_admissions": 0,
               "bundle_sha256": file_hash(output / "bundle.json"),
               "quote_proofs_sha256": file_hash(output / "quote-proofs.json")}
    _write_json(output / "manifest.json", receipt)
    return receipt
