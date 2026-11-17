"""Canary readback must fail closed if canonical persistence changes authored scope."""
import copy
import importlib.util
from pathlib import Path

import pytest

PATH = Path(__file__).parents[1] / "scripts/adhoc/run_round02_acceptance_canary_20261116.py"
SPEC = importlib.util.spec_from_file_location("round02_acceptance", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


@pytest.mark.parametrize("field", ["assessments", "targets", "completion", "verdict", "review_id"])
def test_readback_rejects_authored_value_changes(field):
    authored = {"assessments": [{"scope": "exact named strain"}], "targets": ["original"],
                "completion": "partial", "verdict": "needs_curation", "review_id": "canary"}
    persisted = copy.deepcopy(authored)
    persisted[field] = "changed"
    with pytest.raises(ValueError, match="Persisted"):
        MODULE.check_parity(authored, persisted, {}, {})


def test_readback_rejects_other_occurrence_with_same_categories():
    review = {"assessments": [], "targets": [], "completion": "partial",
              "verdict": "needs_curation", "review_id": "canary"}
    receipt = {"occurrence_id": "replacement", "assessments": MODULE.AXES, "kg_admissions": 0}
    with pytest.raises(ValueError, match="Original occurrence"):
        MODULE.check_parity(review, review, receipt, {"occurrence_id": MODULE.base.OCCURRENCE})


@pytest.mark.parametrize("path", ["reviews/output", "../escape", ".temp/../escape", "/tmp/canary"])
def test_destination_rejects_nonprivate_or_escaping_paths(path):
    with pytest.raises(ValueError, match="Stage must"):
        MODULE.stage_path(path)
