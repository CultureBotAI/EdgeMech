"""Inspect strain parsing failures for PR94, 2026-11-14.

Input: one retained source packet; output: invalid alias and its source locator.
Read-only, offline diagnosis; does not change source evidence or targeting.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'edge_recanary_20261113'))
from organism_targeting import strain_aliases  # noqa: E402

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('packet', type=Path)
args = parser.parse_args()
for wrapper in json.loads(args.packet.read_text())['records']:
    record = json.loads(wrapper['text'])
    if not isinstance(record, dict):
        continue
    values = record.get('type_strain_names', [])[:]
    classification = record.get('Name and taxonomic classification', {})
    if classification.get('strain designation'):
        values.append(classification['strain designation'])
    external = record.get('External links', {})
    for link in external if isinstance(external, list) else [external]:
        if link.get('culture collection no.'):
            values.append(link['culture collection no.'])
    for value in values:
        try:
            strain_aliases([value])
        except ValueError as error:
            print(json.dumps({'source': wrapper['source_relative_path'],
                              'locator': wrapper['locator'], 'value': value,
                              'error': str(error)}))
