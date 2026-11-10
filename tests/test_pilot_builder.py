"""Issue #48: optimized Python must retain every pilot judgment binding guard."""
import base64
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest
from kg_microbe_curation.identity import occurrence_id

from edgemech.evidence_campaign import references
from edgemech.storage.parquet import file_hash

BUILDER = (Path(__file__).resolve().parents[1] / 'scripts' / 'adhoc' /
           'build_literature_pilot_assessments_20261109.py')


@pytest.fixture
def pilot(tmp_path):
    cohort, retrieval = tmp_path / 'cohort', tmp_path / 'retrieval'
    cohort.mkdir()
    retrieval.mkdir()
    (cohort / 'source-manifest.json').write_text('{"synthetic": true}')
    source = {'manifest_sha256': file_hash(cohort / 'source-manifest.json'),
              'edge_member': 'edges.tsv', 'edge_member_sha256': 'b' * 64,
              'header': ['predicate', 'publications']}
    raw = b'biolink:produces\t10.1234/example\n'
    row_sha = hashlib.sha256(raw).hexdigest()
    key = occurrence_id(manifest_sha256=source['manifest_sha256'], member=source['edge_member'],
                        member_sha256=source['edge_member_sha256'], row_number=1, row_sha256=row_sha)
    fields = {'predicate': 'biolink:produces', 'publications': '10.1234/example'}
    refs, warnings = references(fields)
    row = {'row_number': 1, 'occurrence_id': key, 'row_sha256': row_sha,
           'source_row_base64': base64.b64encode(raw).decode(), 'fields': fields,
           'labels': {'object_label': 'Trait B'}, 'references': refs, 'warnings': warnings}
    (cohort / 'occurrences.json').write_text(json.dumps([row]))
    (cohort / 'queue.json').write_text(json.dumps({'doi:10.1234/example': [key]}))
    manifest = {'source': source, 'population': 1, 'selected': 1, 'queue_identifiers': 1,
                'occurrences_sha256': file_hash(cohort / 'occurrences.json'),
                'queue_sha256': file_hash(cohort / 'queue.json')}
    (cohort / 'manifest.json').write_text(json.dumps(manifest))
    (retrieval / 'manifest.json').write_text('{"synthetic": true}')
    notes = {'cohort_sha256': file_hash(cohort / 'manifest.json'),
             'retrieval_sha256': file_hash(retrieval / 'manifest.json'),
             'papers': {'one': {'reference': 'doi:10.1234/example', 'quote': 'Fixture quote.',
                                'taxon': 'Fixture taxon.', 'context': 'Fixture context.'}},
             'judgments': [{'row_number': 1, 'paper': 'one', 'predicate': 'biolink:produces',
                            'object': 'Trait B', 'outcome': 'supported', 'rationale': 'Fixture.',
                            'predicate_reason': 'Fixture.', 'object_reason': 'Fixture.'}]}
    return tmp_path, notes, key


def invoke(pilot):
    root, notes, _ = pilot
    (root / 'judgments.json').write_text(json.dumps(notes))
    return subprocess.run([
        sys.executable, '-O', str(BUILDER), '--cohort', 'cohort', '--retrieval', 'retrieval',
        '--judgments', 'judgments.json', '--output', 'notes.json',
    ], cwd=root, capture_output=True, text=True, timeout=30)


def test_optimized_builder_preserves_valid_occurrence_binding(pilot):
    result = invoke(pilot)
    assert result.returncode == 0, result.stderr
    root, _, key = pilot
    assert json.loads((root / 'notes.json').read_text())['assessments'][0]['occurrence_id'] == key


@pytest.mark.parametrize('damage,message', [
    ('cohort_sha256', 'cohort pin mismatch'), ('retrieval_sha256', 'retrieval pin mismatch'),
    ('predicate', 'predicate differs'), ('object', 'object differs'),
    ('reference', 'reference is not cited'),
])
def test_optimized_builder_rejects_mismatched_judgments(pilot, damage, message):
    root, notes, _ = pilot
    if damage.endswith('sha256'):
        notes[damage] = '0' * 64
    elif damage == 'reference':
        notes['papers']['one']['reference'] = 'doi:10.1234/other'
    else:
        notes['judgments'][0][damage] = 'Wrong value'
    result = invoke(pilot)
    assert result.returncode != 0
    assert message in result.stderr
    assert not (root / 'notes.json').exists()
