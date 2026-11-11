"""Build issue #41/#55 chemical-scope notes, 2026-11-10.

Inputs: pinned prior annotations, exact cohort and explicit finite policy revisions.
Output: new immutable annotations; --canary selects the first revised occurrence.
"""
import argparse
import json
from pathlib import Path

from edgemech.chemical_scope_review import build_annotations

parser = argparse.ArgumentParser(description=__doc__)
for name in ("parent", "revisions", "cohort", "output"):
    parser.add_argument("--" + name, type=Path, required=True)
parser.add_argument("--parent-sha", required=True)
parser.add_argument("--canary", action="store_true")
print(json.dumps(build_annotations(**vars(parser.parse_args())), indent=2))
