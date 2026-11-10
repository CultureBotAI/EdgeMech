"""Prepare/retrieve a pinned literature cohort (2026-11-09), follow-up to PR #33.
Inputs: pinned inventory/census or cohort; outputs: new campaign artifacts/cache.
Default bounds are one occurrence or one request; --all is explicit after canary.
"""
import argparse
import json
from pathlib import Path

from edgemech.evidence_campaign import prepare_cohort
from edgemech.literature_adjudication import adjudicate
from edgemech.literature_cache import retrieve_cohort

parser = argparse.ArgumentParser(description=__doc__)
commands = parser.add_subparsers(dest="command", required=True)
prepare = commands.add_parser("prepare")
prepare.add_argument("--inventory", type=Path, required=True)
prepare.add_argument("--sha256", required=True)
prepare.add_argument("--census", type=Path, required=True)
prepare.add_argument("--source", required=True)
prepare.add_argument("--output", type=Path, required=True)
prepare.add_argument("--all", action="store_true")
retrieve = commands.add_parser("retrieve")
retrieve.add_argument("--cohort", type=Path, required=True)
retrieve.add_argument("--cache", type=Path, required=True)
retrieve.add_argument("--output", type=Path, required=True)
retrieve.add_argument("--all", action="store_true")
review = commands.add_parser("adjudicate")
for name in ("cohort", "retrieval", "cache", "annotations", "output"):
    review.add_argument(f"--{name}", type=Path, required=True)
review.add_argument("--git-revision", required=True)
args = parser.parse_args()
if args.command == "prepare":
    print(json.dumps(prepare_cohort(args.inventory, args.sha256, args.census, args.source,
                                   args.output, None if args.all else 1), indent=2))
elif args.command == "retrieve":
    print(json.dumps(retrieve_cohort(args.cohort, args.cache, args.output,
                                    None if args.all else 1), indent=2))
elif args.command == "adjudicate":
    print(json.dumps(adjudicate(args.cohort, args.retrieval, args.cache, args.annotations,
                               args.output, args.git_revision), indent=2))
