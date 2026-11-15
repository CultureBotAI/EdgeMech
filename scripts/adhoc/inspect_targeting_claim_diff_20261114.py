"""Inspect retained/private versus public canary fields for PR94/#96, 2026-11-14.

Inputs: --packet retained source packet, --manifest public canary JSONL.
Output: differing field paths only; no raw evidence text or mutations.
"""

import argparse
import json

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--packet', required=True)
parser.add_argument('--manifest', required=True)
args = parser.parse_args()
with open(args.packet) as stream:
    private = json.load(stream)['edge']
with open(args.manifest) as stream:
    public = next(row for line in stream if (row := json.loads(line))['occurrence_id']
                  == private['occurrence_id'])


def differences(left, right, path='edge'):
    if isinstance(left, dict) and isinstance(right, dict):
        for key in sorted(set(left) | set(right)):
            if key not in left or key not in right:
                print(path + '.' + key + ': key absent on one side')
            else:
                differences(left[key], right[key], path + '.' + key)
    elif left != right:
        print(path + ': values differ')


differences(private, public)
