#!/usr/bin/env python3
"""Record coordinator phase state in both required durable locations."""
import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / ".temp/m5-round02-worker-20261116"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase")
    parser.add_argument("--next", required=True)
    parser.add_argument("--completed", action="append", default=[])
    parser.add_argument("--blocker", action="append", default=[])
    args = parser.parse_args()
    path = RUN / "progress.json"
    state = json.loads(path.read_text()) if path.exists() else {
        "completed": [], "round01": "failed; immutable d197474",
        "service_use": [], "package_sha256": None,
        "canonical_save": "pending current-runtime canary",
        "gates": {"round02": "not scored", "remaining90": "closed", "expansion9900": "closed"},
        "running": {"coordinator_launcher_pid": 47151, "coordinator_worker_pid": 47214,
                    "fresh_reviewers": [], "preparation_agents": [
                        "/root/acceptance_boundary", "/root/local_authorities", "/root/relation_ontology"]}}
    state.update(updated_at=datetime.now(timezone.utc).isoformat(), phase=args.phase,
                 next_task=args.next, blockers=args.blocker)
    state["completed"].extend(item for item in args.completed if item not in state["completed"])
    raw = json.dumps(state, indent=2, sort_keys=True) + "\n"
    prose = "# M5 round02 progress\n\n" + raw
    for target, content in [(path, raw), (RUN / "PROGRESS.md", prose),
                            (ROOT / ".temp/m5-round02-progress.json", raw),
                            (ROOT / ".temp/M5_ROUND02_PROGRESS.md", prose)]:
        temporary = target.with_suffix(target.suffix + ".new")
        temporary.write_text(content)
        os.chmod(temporary, 0o600)
        temporary.replace(target)
    print(json.dumps({"phase": args.phase, "path": str(path)}))


if __name__ == "__main__":
    main()
