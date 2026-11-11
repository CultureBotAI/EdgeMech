"""Apply finite, explicit chemical-scope judgments without changing source assertions."""
from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

from kg_microbe_curation.identity import CurationError

from .content_inventory import _write_json
from .evidence_campaign import load_cohort
from .storage.parquet import file_hash, safe_path


def build_annotations(parent: Path, parent_sha: str, revisions: Path, cohort: Path,
                      output: Path, canary: bool = False):
    """Bind a reviewed finite policy to exact occurrence IDs and retained quotations."""
    parent = safe_path(parent)
    revisions = safe_path(revisions)
    if file_hash(parent) != parent_sha:
        raise CurationError("Chemical review parent pin mismatch")
    notes = json.loads(parent.read_bytes())
    config = json.loads(revisions.read_bytes())
    if config["format"] != "edgemech-chemical-scope-review/v1":
        raise CurationError("Unsupported chemical review format")
    policy = config["policy"]
    if policy.get("identity_authorized") is not False:
        raise CurationError("Chemical policy must withhold identity authorization")
    policy_path = safe_path(Path(policy["path"]))
    if file_hash(policy_path) != policy["sha256"]:
        raise CurationError("Chemical scope policy pin mismatch")
    if file_hash(cohort / "manifest.json") != notes["cohort_sha256"]:
        raise CurationError("Chemical review cohort pin mismatch")
    _, rows, _ = load_cohort(cohort)
    by_id = {row["occurrence_id"]: row for row in rows}
    assessments = {item["occurrence_id"]: item for item in notes["assessments"]}
    if len(assessments) != len(notes["assessments"]):
        raise CurationError("Duplicate parent assessment")
    updates = config["revisions"]
    if not updates or len({item["occurrence_id"] for item in updates}) != len(updates):
        raise CurationError("Chemical review requires unique explicit revisions")
    for update in updates:
        key = update["occurrence_id"]
        if key not in by_id or key not in assessments:
            raise CurationError("Unknown chemical revision occurrence")
        row = by_id[key]
        if (row["row_number"] != update["row_number"] or
                row["row_sha256"] != update["row_sha256"] or
                row["fields"]["subject"] != update["subject"] or
                row["fields"]["predicate"] != "biolink:produces" or
                update["predicate"] != "biolink:produces" or
                row["fields"]["object"] != update["mapped_object"] or
                row["fields"]["source_column"] != update["source_column"] or
                row["fields"]["source_record"] != update["source_record"] or
                row["labels"]["object_label"] != update["source_value"]):
            raise CurationError("Chemical revision differs from exact source assertion")
        if (update["outcome"] != "concern" or update["support"] != "partial" or
                update["family_production"] != "supported" or
                update["exact_chemical_scope"] != "not_established" or
                update.get("identity_authorized") is not False):
            raise CurationError("Chemical scope concern cannot approve exact identity")
        for field in ("rationale", "predicate_reason", "object_reason", "context", "evidence_scope"):
            if not isinstance(update.get(field), str) or not update[field].strip():
                raise CurationError(f"Chemical revision requires explicit {field}")
        note = assessments[key]
        if len(note["quotes"]) != 1:
            raise CurationError("Chemical revision requires one original citation binding")
        note.update(outcome="concern", rationale=update["rationale"])
        note["dimensions"].update(predicate=update["predicate_reason"], object=update["object_reason"],
                                  context=update["context"], evidence_scope=update["evidence_scope"])
        quote = note["quotes"][0]
        if quote["reference"] != update["reference"] or update["reference"] not in row["references"]:
            raise CurationError("Chemical revision differs from original citation binding")
        quote.update(support="partial", summary=update["rationale"])
        if "capture_id" in update:
            quote.update(capture_id=update["capture_id"], kind="tool_extracted_primary_text",
                         quote=update["quote"])
    result = deepcopy(notes)
    result.update(review_id="chemical-scope-issue41", title="Finite chemical-scope adjudication",
                  started_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    result["interpretation_inputs"] = [
        {"path": str(parent.relative_to(Path.cwd().resolve())), "sha256": parent_sha},
        {"path": str(revisions.relative_to(Path.cwd().resolve())), "sha256": file_hash(revisions)},
        {"path": str(policy_path.relative_to(Path.cwd().resolve())), "sha256": policy["sha256"]},
    ]
    if canary:
        result["assessments"] = [deepcopy(assessments[updates[0]["occurrence_id"]])]
    for item in result["interpretation_inputs"]:
        if file_hash(Path(item["path"])) != item["sha256"]:
            raise CurationError("Chemical review input changed during preparation")
    _write_json(safe_path(output, exists=False), result)
    if json.loads(output.read_bytes()) != result:
        raise CurationError("Chemical review notes readback differs")
    return {"assessments": len(result["assessments"]), "output_sha256": file_hash(output)}
