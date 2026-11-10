"""Bind explicit hand-authored scientific judgments to exact cohort IDs, 2026-11-09.
Inputs: cohort/retrieval plus conf/literature_assessments/20261109-pilot-judgments.json.
Output: expanded review notes under workspace for the literature PR. No inference
or propagation: every selected row and outcome is explicitly authored in the input.
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
for key in ('cohort', 'retrieval', 'judgments', 'output'):
    parser.add_argument(f'--{key}', type=Path, required=True)
args = parser.parse_args()
notes = json.loads(args.judgments.read_bytes())
if notes['cohort_sha256'] != file_hash(args.cohort / 'manifest.json'):
    raise CurationError('Pilot judgment cohort pin mismatch')
if notes['retrieval_sha256'] != file_hash(args.retrieval / 'manifest.json'):
    raise CurationError('Pilot judgment retrieval pin mismatch')
_, rows, _ = load_cohort(args.cohort)
by_number = {row['row_number']: row for row in rows}
assessments = []
for judgment in notes['judgments']:
    row = by_number[judgment['row_number']]
    paper = notes['papers'][judgment['paper']]
    if row['fields']['predicate'] != judgment['predicate']:
        raise CurationError('Pilot judgment predicate differs from selected occurrence')
    if row['labels']['object_label'] != judgment['object']:
        raise CurationError('Pilot judgment object differs from selected occurrence')
    if paper['reference'] not in row['references']:
        raise CurationError('Pilot judgment reference is not cited by selected occurrence')
    supported = judgment['outcome'] == 'supported'
    assessments.append({
        'occurrence_id': row['occurrence_id'], 'outcome': judgment['outcome'],
        'rationale': judgment['rationale'],
        'dimensions': {'taxon': paper['taxon'], 'context': paper['context'],
                       'predicate': judgment['predicate_reason'], 'object': judgment['object_reason'],
                       'evidence_scope': 'Primary-source abstract; explicit bounded interpretation. '
                                         'No native claim admission or automatic generalization.'},
        'quotes': [{'reference': paper['reference'], 'kind': 'abstract', 'quote': paper['quote'],
                    'support': 'supports' if supported else 'context_only',
                    'summary': judgment['rationale']}],
    })
_write_json(args.output, {
    'cohort_sha256': notes['cohort_sha256'], 'retrieval_sha256': notes['retrieval_sha256'],
    'review_id': 'microbedecoder-ten-occurrence-pilot',
    'title': 'Ten bounded source-level scientific assessments from three species descriptions',
    'started_at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
    'reviewer': {'identity': 'Codex', 'kind': 'agent', 'independence': 'self_review',
                 'independence_basis': 'The same agent implemented this workflow and authored the '
                                       'explicit judgments; this is not independent reviewer agreement.'},
    'assessments': assessments,
})
