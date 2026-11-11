"""Canonical scientific decisions require explicit scoped assessments and bound quotes."""
import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest
from kg_microbe_curation.identity import CurationError

import edgemech.literature_adjudication as module
from edgemech.literature_cache import EXTRACTOR
from edgemech.storage.parquet import file_hash


@pytest.fixture
def case(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for name in ('cohort', 'retrieval'):
        Path(name).mkdir()
        Path(name, 'manifest.json').write_text('{}')
    ids = ['urn:kg-microbe:occurrence:v1:' + char * 64 for char in ('1', '2')]
    row = {'occurrence_id': ids[0], 'row_number': 1, 'row_sha256': 'b' * 64,
           'labels': {'subject_label': 'Organism A', 'object_label': 'Trait B'},
           'fields': {'predicate': 'biolink:capable_of'},
           'references': {'doi:10.1234/example': []}, 'warnings': []}
    other = {**row, 'occurrence_id': ids[1], 'row_number': 2}
    manifest = {'source': {'manifest_sha256': 'c' * 64, 'edge_member': 'edges.tsv'},
                'occurrences_sha256': 'd' * 64}
    text = 'Organism A has trait B in condition C.'
    doc = {'kind': 'abstract', 'text': text, 'text_sha256': hashlib.sha256(text.encode()).hexdigest(),
           'extractor': EXTRACTOR, 'response': {'response_sha256': 'e' * 64, 'url': 'https://example.test'}}
    monkeypatch.setattr(module, 'load_cohort', lambda p: (manifest, [row, other], {}))
    monkeypatch.setattr(module, 'load_retrieval', lambda p, c: (
        {'cohort_sha256': file_hash(Path('cohort/manifest.json'))},
        {'doi:10.1234/example': {'documents': [doc]}}))
    notes = {'cohort_sha256': file_hash(Path('cohort/manifest.json')),
             'retrieval_sha256': file_hash(Path('retrieval/manifest.json')),
             'review_id': 'fixture', 'title': 'Synthetic explicit scientific assessment',
             'started_at': '2000-01-01T00:00:00Z',
             'reviewer': {'identity': 'Fixture agent', 'kind': 'agent', 'independence': 'self_review',
                          'independence_basis': 'Synthetic fixture, not scientific evidence.'},
             'assessments': [{'occurrence_id': ids[0], 'outcome': 'supported',
                              'rationale': 'Explicit bounded fixture judgment.',
                              'dimensions': {key: 'Explicit fixture scope.' for key in module.DIMENSIONS},
                              'quotes': [{'reference': 'doi:10.1234/example', 'kind': 'abstract',
                                          'quote': text, 'support': 'supports', 'summary': 'Fixture text.'}]}]}
    return notes


def run(notes):
    Path('notes.json').write_text(json.dumps(notes))
    return module.adjudicate(Path('cohort'), Path('retrieval'), Path('cache'),
                             Path('notes.json'), Path('output'), 'a' * 40)


def test_explicit_assessment_does_not_propagate_or_admit(case):
    result = run(case)
    assert result['scientific_assessments'] == result['verified_quotes'] == 1
    assert result['deferred_occurrences'] == 1
    assert result['kg_admissions'] == 0
    bundle = json.loads(Path('output/bundle.json').read_text())
    assert [d['review_state'] for d in bundle['decisions']] == ['reviewed', 'deferred']
    assert all(d['disposition'] == 'withheld' for d in bundle['decisions'])
    assert bundle['claims'] == bundle['observations'] == []


def test_interpretation_policy_is_pinned_in_canonical_review(case):
    Path('policy.md').write_text('Family-level evidence does not prove exact charge state.')
    pin = {'path': 'policy.md', 'sha256': file_hash(Path('policy.md'))}
    case['interpretation_inputs'] = [pin]
    run(case)
    bundle = json.loads(Path('output/bundle.json').read_text())
    inputs = bundle['reviews'][0]['document']['source']['inputs']
    assert any(item['sha256'] == pin['sha256'] and
               item['role'] == 'review interpretation input' for item in inputs)


@pytest.mark.parametrize('damage', ['changed', 'duplicate', 'during_review'])
def test_interpretation_policy_cannot_drift(case, monkeypatch, damage):
    Path('policy.md').write_text('Only partial source support.')
    pin = {'path': 'policy.md', 'sha256': file_hash(Path('policy.md'))}
    case['interpretation_inputs'] = [pin]
    if damage == 'changed':
        Path('policy.md').write_text('Changed policy.')
    elif damage == 'duplicate':
        case['interpretation_inputs'].append(pin)
    else:
        verify = module.verify_quote

        def mutate(*args, **kwargs):
            Path('policy.md').write_text('Changed during quote verification.')
            return verify(*args, **kwargs)

        monkeypatch.setattr(module, 'verify_quote', mutate)
    with pytest.raises(CurationError, match='Interpretation input'):
        run(case)
    assert not Path('output/manifest.json').exists()


@pytest.mark.parametrize('damage', ['pin', 'quote', 'reference', 'dimensions', 'duplicate'])
def test_reject_unbound_or_incomplete_assessments(case, damage):
    if damage == 'pin':
        case['retrieval_sha256'] = '0' * 64
    elif damage == 'quote':
        case['assessments'][0]['quotes'][0]['quote'] = 'Fabricated quotation.'
    elif damage == 'reference':
        case['assessments'][0]['quotes'][0]['reference'] = 'doi:10.1234/wrong'
    elif damage == 'dimensions':
        del case['assessments'][0]['dimensions']['context']
    else:
        case['assessments'].append(dict(case['assessments'][0]))
    with pytest.raises(CurationError):
        run(case)
    assert not Path('output/manifest.json').exists()


def test_unknown_is_a_scientific_outcome_without_invented_quote(case):
    case['assessments'][0].update(outcome='unknown', quotes=[])
    result = run(case)
    assert result['outcomes']['unknown'] == 1
    assert result['verified_quotes'] == 0
    bundle = json.loads(Path('output/bundle.json').read_text())
    assert bundle['reviews'][0]['document']['verdict'] == 'needs_curation'


@pytest.mark.parametrize('support', ['context_only', 'refutes', 'partial', 'unknown'])
def test_mixed_batch_requires_positive_evidence_per_supported_assessment(case, support):
    unknown = deepcopy(case['assessments'][0])
    unknown.update(occurrence_id='urn:kg-microbe:occurrence:v1:' + '2' * 64,
                   outcome='unknown', quotes=[])
    case['assessments'].append(unknown)
    case['assessments'][0]['quotes'][0]['support'] = support
    with pytest.raises(CurationError, match='Each supported assessment'):
        run(case)
    assert not Path('output/manifest.json').exists()


@pytest.mark.parametrize('support,conflict', [
    ('refutes', 'unresolved'), ('partial', 'none_reported'), ('context_only', 'none_reported'),
])
def test_concern_reports_refuting_evidence_as_unresolved_conflict(case, support, conflict):
    case['assessments'][0]['outcome'] = 'concern'
    case['assessments'][0]['quotes'][0]['support'] = support
    run(case)
    bundle = json.loads(Path('output/bundle.json').read_text())
    assert bundle['decisions'][0]['conflict_state'] == conflict
    assert bundle['decisions'][0]['disposition'] == 'withheld'
    assert bundle['reviews'][0]['document']['verdict'] == 'needs_curation'


def capture_notes(case):
    from edgemech.source_capture import FORMAT, KIND, REPRESENTATION
    Path('tool-response.txt').write_text('L7@P1: Organism A has trait B in condition C.\n')
    manifest = {'format': FORMAT, 'captures': [{
        'capture_id': 'primary', 'reference': 'doi:10.1234/example', 'title': 'Fixture study',
        'url': 'https://example.test/primary.pdf', 'representation': REPRESENTATION,
        'identity_review': {'verified': True, 'reviewer': 'Fixture agent', 'doi': '10.1234/example',
                            'title': 'Fixture study', 'basis': 'Explicit synthetic identity check.'},
        'snapshot': {'path': 'tool-response.txt', 'sha256': file_hash(Path('tool-response.txt'))},
    }]}
    Path('captures.json').write_text(json.dumps(manifest))
    case['source_capture_manifest'] = {'path': 'captures.json',
                                        'sha256': file_hash(Path('captures.json'))}
    case['assessments'][0]['quotes'][0].update(capture_id='primary', kind=KIND)
    return case


def test_tool_capture_is_honest_and_bound_in_canonical_review(case):
    result = run(capture_notes(case))
    assert result['verified_quotes'] == 1
    bundle = json.loads(Path('output/bundle.json').read_text())
    review = bundle['reviews'][0]['document']
    assert any('OCR' in text and 'not independently reproduced' in text for text in review['limitations'])
    inputs = {item['path']: item['sha256'] for item in review['source']['inputs']}
    assert inputs['tool-response.txt'] == file_hash(Path('tool-response.txt'))
    assert inputs['captures.json'] == file_hash(Path('captures.json'))
    evidence = review['evidence'][0]
    assert evidence['snapshot_sha256'] == inputs['tool-response.txt']
    assert 'tool-extracted primary text; L7@P1' in evidence['locator']
    assert evidence['reference'] == 'https://example.test/primary.pdf'


def test_tool_capture_cannot_add_a_source_not_cited_by_the_occurrence(case):
    capture_notes(case)
    case['assessments'][0]['quotes'][0]['reference'] = 'doi:10.1234/other'
    with pytest.raises(CurationError, match='citation of this occurrence'):
        run(case)
    assert not Path('output/manifest.json').exists()
