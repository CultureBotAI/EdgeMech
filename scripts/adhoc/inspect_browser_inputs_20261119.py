"""Inspect committed browser inputs; stdout only; Edge Pages plan, 2026-11-19."""

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PATHS = (
    "artifacts/edge-sample-review-20261112/manifest.jsonl",
    "artifacts/edge-sample-review-20261112/canary-ledger.jsonl",
    "artifacts/edge-recanary-20261113/canary.jsonl",
    "artifacts/edge-recanary-20261113/source-adjudications.json",
    "artifacts/edge-recanary-20261113/scientific-ledger.jsonl",
)
for name in PATHS:
    raw = (ROOT / name).read_text()
    rows = [json.loads(line) for line in raw.splitlines()] if name.endswith("jsonl") else json.loads(raw)
    print(json.dumps({"path": name, "bytes": len(raw.encode()), "rows": len(rows),
                      "keys": sorted(set().union(*(row.keys() for row in rows))),
                      "verdicts": dict(Counter(row.get("verdict") for row in rows)),
                      "applicability": dict(Counter(row.get("scientific_applicability")
                                                    for row in rows))}, sort_keys=True))
