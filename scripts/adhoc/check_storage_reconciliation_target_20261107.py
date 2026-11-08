#!/usr/bin/env python3
"""Verify the isolated EdgeMech target for CLAW #951, 2026-11-07.

Input: this checkout and CLAW repository validation imports. Output: exact target
identity/branch. Root holds the EdgeMech edit lease; this helper acquires no lease
and performs no mutation or provider request.
"""

import json
from pathlib import Path

from plugins.repository_settings import RepositoryTarget

root = Path(__file__).resolve().parents[2]
target = RepositoryTarget("edgemech", root, "CultureBotAI/EdgeMech")
repository = target.open()
expected = "fix/storage-source-reconciliation-951-20261107"
if repository.active_branch.name != expected:
    raise ValueError("Unexpected storage reconciliation branch")
print(json.dumps({"root": str(root), "branch": expected,
                  "head": repository.head.commit.hexsha,
                  "origin": repository.remotes.origin.url}, sort_keys=True))
