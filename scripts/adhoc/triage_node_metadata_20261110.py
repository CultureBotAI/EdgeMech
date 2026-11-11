"""Issue36 pinned node-gap triage, 2026-11-10. Input inventory; output new workspace artifact.
Default one partition canary; --all only after persisted canary verification.
"""
import argparse
import json
from pathlib import Path

from edgemech.node_metadata_triage import triage

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--manifest', type=Path, required=True)
parser.add_argument('--sha256', required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--all', action='store_true')
args = parser.parse_args()
print(json.dumps(triage(args.manifest, args.sha256, args.output, all_partitions=args.all), indent=2))
