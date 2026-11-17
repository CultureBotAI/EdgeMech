#!/usr/bin/env python3
"""Capture bounded original relation authorities; never classify a cohort case.

Run --unit biolink-4.4.0, inspect --check biolink-4.4.0, then other units.
Git snapshots are exact committed bytes. Local snapshots retain original bytes.
All output is private and exclusive. Sampled producer binding is not inferred.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / '.temp/m5-round02-worker-20261116/relation-authorities/snapshots'
METPO = Path('/Users/marcin/agent-work/EdgeMech/m5-round02-owner-work-20261116/metpo-motility')
KG = Path('/Users/marcin/Documents/VIMSS/ontology/KG-Hub/KG-Microbe/kg-microbe')
OLD = Path('/Users/marcin/Documents/VIMSS/ontology/Mechs/EdgeMech/.temp/edge-calibration-authorities-20261115')
CURRENT = '62e388af7ea004b2e1fd0cd2b05db0174dcaea2e'
UNITS = {
    'biolink-4.4.0': (None, str(OLD / 'biolink/biolink-model.yaml'), '4.4.0'),
    'biolink-4.4.2': (None, str(KG / 'data/raw/biolink-model.yaml'), '4.4.2'),
    'metpo-release-2026-06-12': (None, str(OLD / 'metpo/metpo.owl'), '2026-06-12'),
    'metpo-properties-historical': (str(METPO), 'src/templates/metpo-properties.tsv', '5ad46a8d51a8f43b15a58ce23cfdd7ced575f2fb^'),
    'metpo-classes-historical': (str(METPO), 'src/templates/metpo_sheet.tsv', '5ad46a8d51a8f43b15a58ce23cfdd7ced575f2fb^'),
    'metpo-classes-maintained': (str(METPO), 'src/templates/metpo_sheet.tsv', CURRENT),
    'metpo-properties-maintained': (str(METPO), 'src/templates/metpo-properties.tsv', CURRENT),
    'kg-prego-convention': (str(KG), 'docs/PREGO_SCORE_VALIDATION.md', 'd6baf5b90003a2032747559d94c00f86a7a4c615'),
    'kg-download-config': (str(KG), 'download.yaml', 'd6baf5b90003a2032747559d94c00f86a7a4c615'),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def source(unit):
    repo, path, version = UNITS[unit]
    if repo:
        revision = subprocess.check_output(['git', '-C', repo, 'rev-parse', version]).decode().strip()
        raw = subprocess.check_output(['git', '-C', repo, 'show', f'{revision}:{path}'])
    else:
        revision, raw = version, Path(path).read_bytes()
    return raw, {'repository': repo, 'source_path': path, 'version': version, 'resolved_revision': revision}


def check(unit, output=OUTPUT):
    directory = output / unit
    receipt = json.loads((directory / 'receipt.json').read_text())
    raw, origin = source(unit)
    if (directory / 'source.txt').read_bytes() != raw or receipt['sha256'] != sha(raw):
        raise ValueError('Source or retained bytes changed')
    if receipt['origin'] != origin or receipt['helper_sha256'] != sha(Path(__file__).read_bytes()):
        raise ValueError('Origin or helper changed')
    return receipt


def capture(unit, output=OUTPUT):
    if unit != 'biolink-4.4.0':
        check('biolink-4.4.0', output)
    raw, origin = source(unit)
    directory = output / unit
    directory.mkdir(mode=0o700, parents=True, exist_ok=False)
    with (directory / 'source.txt').open('xb') as stream:
        stream.write(raw)
    receipt = {'unit': unit, 'origin': origin, 'sha256': sha(raw), 'bytes': len(raw),
               'helper_sha256': sha(Path(__file__).read_bytes()),
               'captured_at': datetime.now(timezone.utc).isoformat(),
               'scope': 'authority bytes only; sampled production version and semantic fitness not inferred'}
    with (directory / 'receipt.json').open('x') as stream:
        json.dump(receipt, stream, indent=2)
        stream.write('\n')
    return check(unit, output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--unit', choices=UNITS)
    group.add_argument('--check', choices=UNITS)
    group.add_argument('--plan', action='store_true')
    args = parser.parse_args()
    result = UNITS if args.plan else capture(args.unit) if args.unit else check(args.check)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
