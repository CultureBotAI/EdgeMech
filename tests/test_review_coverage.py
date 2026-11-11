"""Issue #35: cohort counts never manufacture individual scientific coverage."""
import base64
import hashlib
import io
import json
from pathlib import Path

import pytest
from kg_microbe_curation.identity import CurationError, occurrence_id, sha256_json

from edgemech.evidence_campaign import references
from edgemech.literature_adjudication import DIMENSIONS, adjudicate
from edgemech.literature_cache import LiteratureCache
from edgemech.review_coverage import build_coverage
from edgemech.source_capture import FORMAT, KIND, LIMITATION, REPRESENTATION
from edgemech.storage.parquet import file_hash


def write(path, value):
    Path(path).write_text(json.dumps(value))
    return file_hash(Path(path))


@pytest.fixture
def coverage_case(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for directory in ('cohort', 'retrieval'):
        Path(directory).mkdir()
    source_sha = write('cohort/source-manifest.json', {'synthetic': True})
    source = {'manifest_sha256': source_sha, 'edge_member': 'edges.tsv',
              'edge_member_sha256': 'b' * 64,
              'header': ['subject', 'predicate', 'object', 'publications']}
    rows = []
    for number in (1, 2, 3):
        raw = f'Taxon:{number}\tbiolink:produces\tTrait:B\t10.1234/example\n'.encode()
        digest = hashlib.sha256(raw).hexdigest()
        key = occurrence_id(manifest_sha256=source_sha, member='edges.tsv',
                            member_sha256='b' * 64, row_number=number, row_sha256=digest)
        fields = dict(zip(source['header'], raw.decode().strip().split('\t'), strict=True))
        refs, warnings = references(fields)
        rows.append({'row_number': number, 'occurrence_id': key, 'row_sha256': digest,
                     'source_row_base64': base64.b64encode(raw).decode(), 'fields': fields,
                     'labels': {'subject_label': f'Taxon {number}', 'object_label': 'Trait B'},
                     'references': refs, 'warnings': warnings})
    census_sha = write('census.json', {'source': {'manifest_sha256': source_sha,
                       'source_rows': 100, 'selected_rows': 100, 'complete_export': True}})
    cohort_sha = write('cohort/manifest.json', {
        'source': source, 'census_sha256': census_sha, 'population': 3, 'selected': 3,
        'occurrences_sha256': write('cohort/occurrences.json', rows),
        'queue_sha256': write('cohort/queue.json', {'doi:10.1234/example':
                                                  [row['occurrence_id'] for row in rows]})})
    raw = json.dumps({'hitCount': 1, 'resultList': {'result': [{
        'doi': '10.1234/example', 'abstractText': 'Taxon produces trait in condition C.'}]}}).encode()

    class Response(io.BytesIO):
        status = 200

    with LiteratureCache(Path('cache'), opener=lambda *a, **kw: Response(raw)) as cache:
        document = cache.document('doi:10.1234/example')
    retrieval_sha = write('retrieval/manifest.json', {
        'cohort_sha256': cohort_sha, 'documents_sha256': write('retrieval/documents.json', [document])})
    notes = {'cohort_sha256': cohort_sha, 'retrieval_sha256': retrieval_sha,
             'review_id': 'coverage-fixture', 'title': 'Synthetic coverage fixture',
             'started_at': '2000-01-01T00:00:00Z',
             'reviewer': {'identity': 'Fixture', 'kind': 'agent', 'independence': 'self_review',
                          'independence_basis': 'Synthetic test data.'},
             'assessments': [{
                 'occurrence_id': row['occurrence_id'], 'outcome': outcome,
                 'rationale': 'Explicit bounded fixture judgment.',
                 'dimensions': {name: 'Fixture scope.' for name in DIMENSIONS},
                 'quotes': [{'reference': 'doi:10.1234/example', 'kind': 'abstract',
                             'quote': 'Taxon produces trait', 'summary': 'Fixture evidence.',
                             'support': 'supports' if outcome == 'supported' else 'context_only'}],
             } for row, outcome in zip(rows, ('supported', 'unknown'))]}
    write('notes.json', notes)
    adjudicate(Path('cohort'), Path('retrieval'), Path('cache'), Path('notes.json'),
               Path('adjudication'), 'a' * 40)
    prior_ids = [rows[0]['occurrence_id'], 'urn:kg-microbe:occurrence:v1:' + 'e' * 64]
    decisions = [{'occurrence_id': key, 'disposition': 'withheld'} for key in prior_ids]
    wave_sha = write('wave.json', {'input_sha256': source_sha, 'occurrence_ids': prior_ids,
                                  'decisions': decisions})
    cohort_table_sha = write('cohorts.json', [{
        'cohort_key': 'test cohort', 'population_occurrences': 100,
        'individually_reviewed_occurrences': 2, 'cohort_bound_occurrences': 98,
        'disposition': 'withheld'}])
    ledger_sha = write('ledger.json', {
        'contract': 'edgemech-full-snapshot-review-ledger/v1',
        'kg_source_manifest_sha256': source_sha, 'census_manifest_path': 'census.json',
        'census_manifest_sha256': census_sha, 'total_snapshot_occurrences': 100,
        'total_snapshot_cohorts': 1, 'coverage_summary': {'reviewed_occurrences': 100},
        'artifacts': {'individual_decision_index_593_path': 'index.json',
                      'individual_decision_index_593_sha256': write('index.json', decisions),
                      'cohort_decision_table_368_path': 'cohorts.json',
                      'cohort_decision_table_368_sha256': cohort_table_sha},
        'waves': {'one': {'bundle_path': 'wave.json', 'bundle_sha256': wave_sha}}})
    return {'ledger': Path('ledger.json'), 'ledger_sha': ledger_sha, 'cohort': Path('cohort'),
            'cohort_sha': cohort_sha, 'retrieval': Path('retrieval'), 'retrieval_sha': retrieval_sha,
            'cache': Path('cache'), 'adjudication': Path('adjudication'),
            'adjudication_sha': file_hash(Path('adjudication/manifest.json')), 'output': Path('view.json')}


def repin_manifest(case, filename):
    manifest = json.loads(Path('adjudication/manifest.json').read_text())
    manifest[{'bundle.json': 'bundle_sha256', 'quote-proofs.json': 'quote_proofs_sha256'}[filename]] = file_hash(Path('adjudication') / filename)
    case['adjudication_sha'] = write('adjudication/manifest.json', manifest)


def test_exact_union_and_explicit_scientific_coverage(coverage_case):
    result = build_coverage(**coverage_case)
    assert result['legacy_disposition_coverage']['population_disposition_coverage'] == 100
    assert result['legacy_disposition_coverage']['individual_prior_decision_ids'] == 2
    assert result['current_scientific_coverage']['scientific_assessments'] == 2
    assert result['current_scientific_coverage']['verified_quotes'] == 2
    assert result['current_scientific_coverage']['deferred_occurrences'] == 1
    assert result['distinct_individual_decision_or_assessment_ids'] == 3
    assert result['overlap_prior_and_current_ids'] == 1
    assert result['population_without_verified_current_scientific_assessment'] == 98
    assert json.loads(Path('view.json').read_text()) == result
    assert file_hash(Path('ledger.json')) == coverage_case['ledger_sha']
    with pytest.raises(FileExistsError):
        build_coverage(**coverage_case)


@pytest.mark.parametrize('path', ['ledger.json', 'wave.json', 'index.json', 'cohorts.json',
                                  'adjudication/bundle.json', 'adjudication/quote-proofs.json'])
def test_unpinned_artifact_changes_never_publish(coverage_case, path):
    Path(path).write_text('{}')
    with pytest.raises(CurationError, match='hash mismatch'):
        build_coverage(**coverage_case)
    assert not Path('view.json').exists()


@pytest.mark.parametrize('damage', ['omitted', 'extra', 'wrong_occurrence', 'wrong_offset'])
def test_proofs_must_cover_exact_scientific_evidence(coverage_case, damage):
    proofs = json.loads(Path('adjudication/quote-proofs.json').read_text())
    if damage == 'omitted':
        proofs.pop()
    elif damage == 'extra':
        proofs.append(dict(proofs[0]))
    elif damage == 'wrong_occurrence':
        proofs[0]['occurrence_id'] = proofs[1]['occurrence_id']
    else:
        proofs[0]['start'] += 1
    write('adjudication/quote-proofs.json', proofs)
    repin_manifest(coverage_case, 'quote-proofs.json')
    with pytest.raises(CurationError, match='[Pp]roof'):
        build_coverage(**coverage_case)
    assert not Path('view.json').exists()


def test_legacy_index_union_mismatch_rejected(coverage_case):
    index = json.loads(Path('index.json').read_text())
    index.pop()
    ledger = json.loads(Path('ledger.json').read_text())
    ledger['artifacts']['individual_decision_index_593_sha256'] = write('index.json', index)
    coverage_case['ledger_sha'] = write('ledger.json', ledger)
    with pytest.raises(CurationError, match='ID union'):
        build_coverage(**coverage_case)


def test_changed_reviewer_notes_rejected(coverage_case):
    Path('notes.json').write_text('{}')
    with pytest.raises(CurationError, match='source input changed'):
        build_coverage(**coverage_case)


@pytest.fixture
def capture_coverage(coverage_case):
    Path('capture.txt').write_text('Tool response, not original PDF bytes.\n'
                                   'L10@P2: Taxon produces trait in condition C.\n')
    captures = {'format': FORMAT, 'captures': [{
        'capture_id': 'primary-fixture', 'reference': 'doi:10.1234/example',
        'title': 'Synthetic study', 'url': 'https://example.test/study.pdf',
        'representation': REPRESENTATION,
        'identity_review': {'verified': True, 'doi': '10.1234/example',
                            'title': 'Synthetic study', 'reviewer': 'Fixture reviewer',
                            'basis': 'Explicit fixture manual identity confirmation.'},
        'snapshot': {'path': 'capture.txt', 'sha256': file_hash(Path('capture.txt'))},
    }]}
    capture_sha = write('captures.json', captures)
    notes = json.loads(Path('notes.json').read_text())
    notes['source_capture_manifest'] = {'path': 'captures.json', 'sha256': capture_sha}
    notes['assessments'][0]['quotes'][0].update(kind=KIND, capture_id='primary-fixture')
    write('notes.json', notes)
    adjudicate(Path('cohort'), Path('retrieval'), Path('cache'), Path('notes.json'),
               Path('adjudication-captured'), 'a' * 40)
    coverage_case.update(adjudication=Path('adjudication-captured'),
                          adjudication_sha=file_hash(Path('adjudication-captured/manifest.json')))
    return coverage_case


def repin_captured_bundle(case, bundle):
    for envelope in bundle['reviews']:
        envelope['sha256'] = sha256_json(envelope['document'])
    root = case['adjudication']
    receipt = json.loads((root / 'manifest.json').read_text())
    receipt['bundle_sha256'] = write(root / 'bundle.json', bundle)
    case['adjudication_sha'] = write(root / 'manifest.json', receipt)


def test_capture_and_conventional_quotes_replay_with_representation_limits(capture_coverage):
    result = build_coverage(**capture_coverage)
    scientific = result['current_scientific_coverage']
    assert scientific['verified_quotes'] == 2
    assert scientific['quote_representations'] == {KIND: 1, 'abstract': 1}
    assert scientific['evidence_representation_limitations'] == [LIMITATION]
    assert LIMITATION in result['limitations']
    assert scientific['scientific_assessments'] == 2


@pytest.mark.parametrize('damage', ['source_lines', 'representation', 'extractor'])
def test_capture_proof_all_fields_are_reconstructed(capture_coverage, damage):
    root = capture_coverage['adjudication']
    proofs = json.loads((root / 'quote-proofs.json').read_text())
    if damage == 'source_lines':
        proofs[0][damage][0]['page'] = 99
    else:
        proofs[0][damage] = 'wrong'
    receipt = json.loads((root / 'manifest.json').read_text())
    receipt['quote_proofs_sha256'] = write(root / 'quote-proofs.json', proofs)
    capture_coverage['adjudication_sha'] = write(root / 'manifest.json', receipt)
    with pytest.raises(CurationError, match='Quote proof differs'):
        build_coverage(**capture_coverage)
    assert not Path('view.json').exists()


@pytest.mark.parametrize('damage', ['snapshot_input', 'manifest_role', 'locator'])
def test_capture_requires_reviewed_manifest_snapshot_and_locator(capture_coverage, damage):
    root = capture_coverage['adjudication']
    bundle = json.loads((root / 'bundle.json').read_text())
    review = bundle['reviews'][0]['document']
    if damage == 'snapshot_input':
        review['source']['inputs'] = [item for item in review['source']['inputs']
                                      if item['path'] != 'capture.txt']
    elif damage == 'manifest_role':
        for item in review['source']['inputs']:
            if item['path'] == 'captures.json':
                item['role'] = 'unrelated input'
    else:
        review['evidence'][0]['locator'] = 'Incorrect capture location'
    repin_captured_bundle(capture_coverage, bundle)
    with pytest.raises(CurationError, match='capture|proofs'):
        build_coverage(**capture_coverage)
    assert not Path('view.json').exists()


@pytest.mark.parametrize('path', ['capture.txt', 'captures.json'])
def test_capture_inputs_remain_hash_bound(capture_coverage, path):
    Path(path).write_text('changed')
    with pytest.raises(CurationError, match='source input changed'):
        build_coverage(**capture_coverage)


@pytest.mark.parametrize('fixture_name', ['coverage_case', 'capture_coverage'])
def test_rehashed_evidence_url_must_match_reconstructed_source(request, fixture_name):
    case = request.getfixturevalue(fixture_name)
    root = case['adjudication']
    bundle = json.loads((root / 'bundle.json').read_text())
    bundle['reviews'][0]['document']['evidence'][0]['reference'] = 'https://example.test/wrong-paper'
    repin_captured_bundle(case, bundle)
    with pytest.raises(CurationError, match='Quote proofs do not exactly cover scientific evidence'):
        build_coverage(**case)
    assert not Path('view.json').exists()
