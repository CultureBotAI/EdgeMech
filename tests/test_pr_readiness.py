"""A missing authoritative workflow must not produce green readiness (#17)."""

import hashlib
import json
import runpy
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

AUDIT = runpy.run_path(str(Path(__file__).parents[1] / "scripts/adhoc/check_pr_readiness_20261107.py"))


def test_missing_authoritative_workflow_is_not_ready(monkeypatch):
    head = "a" * 40
    data = {
        "url": "https://github.com/CultureBotAI/culturebotai-claw/pull/962",
        "number": 962, "headRefOid": head, "state": "OPEN", "isDraft": False,
        "mergeStateStatus": "CLEAN",
        "statusCheckRollup": [{"__typename": "CheckRun", "name": "pytest",
                               "status": "COMPLETED", "conclusion": "SUCCESS"}],
    }
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: SimpleNamespace(stdout=json.dumps(data)))
    expected = {"CultureBotAI/culturebotai-claw#962": ["pytest", "fleet-audit"]}
    record = AUDIT["inspect"]("CultureBotAI/culturebotai-claw#962=" + head, expected)
    assert record["ready"] is False
    assert record["expected_checks"] == ["fleet-audit", "pytest"]
    assert record["failures"] == ["Reported check inventory differs from reviewed expected checks"]
    data["statusCheckRollup"].append({"__typename": "CheckRun", "name": "fleet-audit",
                                    "status": "COMPLETED", "conclusion": "SUCCESS"})
    assert AUDIT["inspect"]("CultureBotAI/culturebotai-claw#962=" + head, expected)["ready"] is True


def test_inventory_cannot_be_silently_weakened(tmp_path):
    path = tmp_path / "inventory.json"
    original = json.dumps({"format": "edgemech-pr-check-inventory/v1", "checks": {
        "CultureBotAI/culturebotai-claw#962": ["pytest", "fleet-audit"],
    }}).encode()
    path.write_bytes(original)
    digest = hashlib.sha256(original).hexdigest()
    assert AUDIT["load_expected"](path, digest)["CultureBotAI/culturebotai-claw#962"] == ["pytest", "fleet-audit"]
    path.write_bytes(original.replace(b', "fleet-audit"', b''))
    with pytest.raises(ValueError, match="differs from pinned digest"):
        AUDIT["load_expected"](path, digest)
