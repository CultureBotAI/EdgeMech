"""Issue41: apply explicit six-row follow-up judgments, 2026-11-10.
Inputs: original pilot judgments, revisions, pinned cohort/retrieval and source captures.
Outputs: expanded notes in a new workspace file, without changing source assertions.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from kg_microbe_curation.identity import CurationError

from edgemech.content_inventory import _write_json
from edgemech.evidence_campaign import load_cohort
from edgemech.storage.parquet import file_hash

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--revisions', type=Path, required=True)
parser.add_argument('--cohort', type=Path, required=True)
parser.add_argument('--retrieval', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--canary', action='store_true')
args = parser.parse_args()
revisions = json.loads(args.revisions.read_bytes())
parent = json.loads(Path(revisions['parent_judgments']).read_bytes())
if (file_hash(args.cohort / 'manifest.json') != parent['cohort_sha256'] or
        file_hash(args.retrieval / 'manifest.json') != parent['retrieval_sha256']):
    raise CurationError('Follow-up input pin mismatch')
_, rows, _ = load_cohort(args.cohort)
by_number = {row['row_number']: row for row in rows}
updates = {revision['row_number']: revision for revision in revisions['revisions']}
if len(updates) != len(revisions['revisions']):
    raise CurationError('Duplicate follow-up revision')
parent_numbers = {judgment['row_number'] for judgment in parent['judgments']}
unknown_numbers = set(updates) - parent_numbers
if unknown_numbers:
    raise CurationError(f'Unknown follow-up revision rows: {sorted(unknown_numbers)}')
for update in updates.values():
    for field in ('context', 'evidence_scope'):
        if not isinstance(update.get(field), str) or not update[field].strip():
            raise CurationError(f'Follow-up revision requires explicit {field}')
assessments = []
for original in parent['judgments']:
    number = original['row_number']
    if args.canary and number != 7726743:
        continue
    row = by_number[number]
    if (row['fields']['predicate'] != original['predicate'] or
            row['labels']['object_label'] != original['object']):
        raise CurationError('Judgment does not match original occurrence')
    note = {**original, **updates.get(number, {})}
    paper = parent['papers'][original['paper']]
    if paper['reference'] not in row['references']:
        raise CurationError('Paper not cited by original occurrence')
    selection = {'reference': paper['reference'], 'kind': 'abstract',
                 'quote': paper['quote'], 'support': 'supports' if note['outcome'] == 'supported' else 'context_only',
                 'summary': note['rationale']}
    if 'capture_id' in note:
        selection.update(capture_id=note['capture_id'], kind='tool_extracted_primary_text',
                         quote=note['quote'], support=note['support'])
    assessments.append({'occurrence_id': row['occurrence_id'], 'outcome': note['outcome'],
                        'rationale': note['rationale'], 'quotes': [selection],
                        'dimensions': {'taxon': paper['taxon'], 'context': note.get('context', paper['context']),
                                       'predicate': note['predicate_reason'], 'object': note['object_reason'],
                                       'evidence_scope': note.get('evidence_scope',
                                           'Primary-source abstract assessment retained from the original pilot. '
                                           'No new full-text or chemical-mapping assessment for this occurrence. '
                                           'No native claim admission or scope propagation.')}})
_write_json(args.output, {'cohort_sha256': parent['cohort_sha256'],
                         'retrieval_sha256': parent['retrieval_sha256'],
                         'source_capture_manifest': {'path': revisions['capture_manifest'],
                                                     'sha256': file_hash(Path(revisions['capture_manifest']))},
                         'review_id': 'scientific-followup-issue41',
                         'title': 'Issue41 original-source and chemical-scope follow-up',
                         'started_at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                         'reviewer': {'identity': 'Codex', 'kind': 'agent', 'independence': 'self_review',
                                      'independence_basis': 'Agent research and implementation, not independent human agreement.'},
                         'assessments': assessments})
