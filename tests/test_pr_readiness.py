"""A missing authoritative workflow or stale base must not produce green readiness (#17, #22)."""

import hashlib
import json
import runpy
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

AUDIT = runpy.run_path(
    str(Path(__file__).parents[1] / "scripts/adhoc/check_pr_readiness_20261107.py")
)


def test_missing_authoritative_workflow_is_not_ready(monkeypatch):
    head = "a" * 40
    data = {
        "url": "https://github.com/CultureBotAI/culturebotai-claw/pull/962",
        "number": 962,
        "headRefOid": head,
        "state": "OPEN",
        "isDraft": False,
        "mergeStateStatus": "CLEAN",
        "statusCheckRollup": [
            {
                "__typename": "CheckRun",
                "name": "pytest",
                "status": "COMPLETED",
                "conclusion": "SUCCESS",
            }
        ],
    }
    monkeypatch.setattr(
        subprocess, "run", lambda *args, **kwargs: SimpleNamespace(stdout=json.dumps(data))
    )
    expected = {"CultureBotAI/culturebotai-claw#962": ["pytest", "fleet-audit"]}
    record = AUDIT["inspect"]("CultureBotAI/culturebotai-claw#962=" + head, expected)
    assert record["ready"] is False
    assert record["expected_checks"] == ["fleet-audit", "pytest"]
    assert record["failures"] == ["Reported check inventory differs from reviewed expected checks"]
    data["statusCheckRollup"].append(
        {
            "__typename": "CheckRun",
            "name": "fleet-audit",
            "status": "COMPLETED",
            "conclusion": "SUCCESS",
        }
    )
    assert AUDIT["inspect"]("CultureBotAI/culturebotai-claw#962=" + head, expected)["ready"] is True


def test_current_base_provenance_and_stale_base_detection(monkeypatch):
    head = "a" * 40
    stale_base = "b" * 40
    current_default = "c" * 40
    merge_oid = "d" * 40
    data = {
        "url": "https://github.com/CultureBotAI/culturebotai-claw/pull/962",
        "number": 962,
        "headRefOid": head,
        "baseRefName": "main",
        "baseRefOid": stale_base,
        "defaultBranchOid": current_default,
        "potentialMergeCommit": {
            "oid": merge_oid,
            "parents": {"nodes": [{"oid": stale_base}, {"oid": head}]},
        },
        "state": "OPEN",
        "isDraft": False,
        "mergeStateStatus": "CLEAN",
        "statusCheckRollup": [
            {
                "__typename": "CheckRun",
                "name": "pytest",
                "status": "COMPLETED",
                "conclusion": "SUCCESS",
            },
            {
                "__typename": "CheckRun",
                "name": "fleet-audit",
                "status": "COMPLETED",
                "conclusion": "SUCCESS",
            },
        ],
    }
    monkeypatch.setattr(
        subprocess, "run", lambda *args, **kwargs: SimpleNamespace(stdout=json.dumps(data))
    )
    expected = {"CultureBotAI/culturebotai-claw#962": ["pytest", "fleet-audit"]}
    record = AUDIT["inspect"]("CultureBotAI/culturebotai-claw#962=" + head, expected)
    assert record["base_ref_oid"] == stale_base
    assert record["default_branch_oid"] == current_default
    assert record["potential_merge_commit_oid"] == merge_oid
    assert record["potential_merge_parents"] == [stale_base, head]
    assert record["base_oid_matches_default_branch"] is False
    assert record["ready"] is False
    assert "PR baseRefOid differs from target default branch OID" in record["failures"]
    assert (
        "potentialMergeCommit parents do not include current default branch OID"
        in record["failures"]
    )

    data["baseRefOid"] = current_default
    data["potentialMergeCommit"]["parents"]["nodes"][0]["oid"] = current_default
    fresh = AUDIT["inspect"]("CultureBotAI/culturebotai-claw#962=" + head, expected)
    assert fresh["base_oid_matches_default_branch"] is True
    assert fresh["potential_merge_parents"] == [current_default, head]
    assert fresh["ready"] is True
    assert fresh["failures"] == []


def test_inventory_cannot_be_silently_weakened(tmp_path):
    path = tmp_path / "inventory.json"
    original = json.dumps(
        {
            "format": "edgemech-pr-check-inventory/v1",
            "checks": {
                "CultureBotAI/culturebotai-claw#962": ["pytest", "fleet-audit"],
            },
        }
    ).encode()
    path.write_bytes(original)
    digest = hashlib.sha256(original).hexdigest()
    assert AUDIT["load_expected"](path, digest)["CultureBotAI/culturebotai-claw#962"] == [
        "pytest",
        "fleet-audit",
    ]
    path.write_bytes(original.replace(b', "fleet-audit"', b""))
    with pytest.raises(ValueError, match="differs from pinned digest"):
        AUDIT["load_expected"](path, digest)
