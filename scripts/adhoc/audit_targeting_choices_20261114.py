"""Audit curated primary choices against replayed sources for PR94/#103, 2026-11-14.

Input: private rebuilt enrichment JSON. Output: missing choice/scope summary only.
Offline and read-only; does not silently remove choices or assign evidence verdicts.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'edge_recanary_20261113'))
from build_targeting import PRIMARY_CHOICES  # noqa: E402

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('enrichment', type=Path)
args = parser.parse_args()
for row in json.loads(args.enrichment.read_text()):
    ordinal = row['canary_ordinal']
    available = {ref['reference'].casefold() for ref in row['primary_references']}
    for choice in PRIMARY_CHOICES.get(ordinal, []):
        if 'doi:' + choice.casefold() in available:
            continue
        edge = row['source_packet']['edge']
        candidates = [ref for ref in row['candidate_primary_references']
                      if ref['reference'].casefold() == 'doi:' + choice.casefold()]
        print(json.dumps({'ordinal': ordinal, 'subject': edge['subject'],
                          'names': row['resolved_names'], 'missing_choice': choice,
                          'candidate_scopes': [ref['organism_scope'] for ref in candidates],
                          'candidate_record_indices': [ref['identity_basis']['record_index']
                                                       for ref in candidates]}))
