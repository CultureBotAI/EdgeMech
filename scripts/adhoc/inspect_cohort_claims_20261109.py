"""Print exact cohort claims/citation anomalies for manual review, 2026-11-09.
Input: cohort directory. Output: bounded JSON lines; no scientific decisions.
"""
import argparse
import base64
import json
from pathlib import Path

from edgemech.evidence_campaign import load_cohort

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('cohort', type=Path)
parser.add_argument('--warnings', action='store_true')
parser.add_argument('--reference')
args = parser.parse_args()
manifest, rows, queue = load_cohort(args.cohort)
for row in rows:
    if args.warnings and not row['warnings']:
        continue
    if args.reference and args.reference not in row['references']:
        continue
    summary = {'row': row['row_number'], 'id': row['occurrence_id'],
               'subject': row['labels']['subject_label'], 'predicate': row['fields']['predicate'],
               'object': row['labels']['object_label'], 'value': row['fields']['value'],
               'source_column': row['fields']['source_column'], 'references': list(row['references'])}
    if args.warnings:
        summary.update(warnings=row['warnings'], plain=row['fields']['source_citation'],
                       decoded=base64.b64decode(row['fields']['source_citation_base64']).decode())
    print(json.dumps(summary, ensure_ascii=False))
