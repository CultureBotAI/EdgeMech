#!/usr/bin/env python3
"""Mirror authored round03 progress; 2026-11-16, #190/#192.

Inputs: a complete coordinator-authored JSON state under the supplied run root.
Outputs: progress.json and PROGRESS.md plus required repository .temp mirrors.
This helper records state only; it does not calculate scientific results.
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / ".temp/m5-round03-worker-20261116"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True)
    args = parser.parse_args()
    source = args.state.resolve()
    if not source.is_relative_to(RUN.resolve()):
        raise ValueError("Authored state must be within the round03 output root")
    state = json.loads(source.read_text())
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    raw = json.dumps(state, indent=2, sort_keys=True) + "\n"
    prose = "# M5 round03 progress\n\n```json\n" + raw + "```\n"
    for target, content in (
        (RUN / "progress.json", raw), (RUN / "PROGRESS.md", prose),
        (ROOT / ".temp/m5-round03-progress.json", raw),
        (ROOT / ".temp/M5_ROUND03_PROGRESS.md", prose),
    ):
        temporary = target.with_suffix(target.suffix + ".new")
        temporary.write_text(content)
        os.chmod(temporary, 0o600)
        temporary.replace(target)
    print(json.dumps({"phase": state["phase"], "path": str(RUN / "progress.json")}))


if __name__ == "__main__":
    main()
