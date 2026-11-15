"""Offline retained-canary compatibility audit for PR94/#99, 2026-11-14.

Inputs: private first/fresh canaries and source snapshots under --data-root.
Output: --output JSON containing counts, hashes and failure IDs only. No network,
scientific verdict, or modification of any retained evidence. Canary --limit 1.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent / 'edge_recanary_20261113'))
from organism_targeting import claim_identity  # noqa: E402
from source_adjudicate import packet_targeting  # noqa: E402


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def audit(data_root, limit):
    first_sources = json.loads((data_root / 'source/source-records-50.json').read_text())
    cohorts = [
        ('first', ROOT / 'artifacts/edge-sample-review-20261112/canary.jsonl',
         data_root / 'sample/private-provenance/canary.jsonl'),
        ('fresh', ROOT / 'artifacts/edge-recanary-20261113/canary.jsonl',
         data_root / 'phase2/sample/canary.jsonl')]
    result = []
    for cohort, public_path, private_path in cohorts:
        public = {row['occurrence_id']: row for row in rows(public_path)}
        private = {row['occurrence_id']: row for row in rows(private_path)}
        if len(public) != 50 or set(public) != set(private):
            raise ValueError('Retained cohort identity mismatch')
        for oid, row in public.items():
            if len(result) >= limit:
                break
            item = {'cohort': cohort, 'ordinal': row['canary_ordinal'], 'occurrence_id': oid,
                    'projection_matches': claim_identity(private[oid]) == row}
            if cohort == 'fresh':
                packet = json.loads((data_root / 'phase2/source/packets'
                                     / f"{row['canary_ordinal']:02d}.json").read_text())
                item['packet_projection_matches'] = claim_identity(packet['edge']) == row
                source_records = packet['records']
                try:
                    targeting = packet_targeting(packet)
                    item['targeting_rebuilt'] = True
                    item['bound_names'] = len(targeting['resolved_names'])
                    item['bound_strains'] = len(targeting['strain_designations'])
                except (KeyError, TypeError, ValueError) as error:
                    item['targeting_rebuilt'] = False
                    item['targeting_error'] = str(error)
            else:
                source_records = first_sources[oid]
            item['source_record_count'] = len(source_records)
            item['source_hashes_match'] = all(
                hashlib.sha256(record['text'].encode()).hexdigest() == record['text_sha256']
                for record in source_records)
            result.append(item)
    return {'rows_checked': len(result),
            'projection_mismatches': sum(not row['projection_matches'] for row in result),
            'packet_projection_mismatches': sum(not row.get('packet_projection_matches', True)
                                               for row in result),
            'source_hash_failures': sum(not row['source_hashes_match'] for row in result),
            'targeting_failures': sum(row.get('targeting_rebuilt') is False for row in result),
            'rows': result}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--limit', type=int, default=100)
    args = parser.parse_args()
    if not 1 <= args.limit <= 100 or args.output.exists():
        parser.error('limit 1..100 and a new output path required')
    result = audit(args.data_root, args.limit)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    if json.loads(args.output.read_text()) != result:
        raise ValueError('Persisted audit differs from result')
    print(json.dumps({key: value for key, value in result.items() if key != 'rows'}))
