"""Pinned tool text proves literal spans, not publisher/PDF byte authenticity."""
import json
from pathlib import Path

import pytest
from kg_microbe_curation.identity import CurationError

from edgemech.source_capture import (
    FORMAT,
    KIND,
    REPRESENTATION,
    capture_quote,
    extract_lines,
    load_source_captures,
)
from edgemech.storage.parquet import file_hash


@pytest.fixture
def capture_case(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path('response.txt').write_text(
        'Tool metadata: original PDF not retained.\nL10@P2: Organism A ferments glucose.\n'
        'L11@P2: It produces product B.\nL20@P3: Another section.\n')
    entry = {'capture_id': 'fixture', 'reference': 'doi:10.1234/example',
             'title': 'Synthetic primary study', 'url': 'https://example.test/study.pdf',
             'representation': REPRESENTATION,
             'identity_review': {'verified': True, 'reviewer': 'Fixture reviewer',
                                 'doi': '10.1234/example', 'title': 'Synthetic primary study',
                                 'basis': 'Synthetic explicit manual identity approval.'},
             'snapshot': {'path': 'response.txt', 'sha256': file_hash(Path('response.txt'))}}
    manifest = {'format': FORMAT, 'captures': [entry]}
    return manifest


def load(manifest):
    Path('captures.json').write_text(json.dumps(manifest))
    return load_source_captures({'path': 'captures.json', 'sha256': file_hash(Path('captures.json'))})


def selection(**updates):
    return {'capture_id': 'fixture', 'reference': 'doi:10.1234/example', 'kind': KIND,
            'quote': 'Organism A ferments glucose.', **updates}


def test_verified_capture_preserves_coordinates_and_raw_response_pin(capture_case):
    captures, inputs = load(capture_case)
    doc, proof, locator = capture_quote(captures, selection())
    assert doc['representation'] == REPRESENTATION
    assert doc['text'].startswith('Organism A ferments glucose.\nIt produces')
    assert proof['response_sha256'] == file_hash(Path('response.txt'))
    assert proof['source_lines'] == [{'line': 10, 'page': 2}]
    assert 'L10@P2' in locator
    assert {item['path'] for item in inputs} == {'captures.json', 'response.txt'}


def test_source_capture_manifest_and_snapshot_tampering_rejected(capture_case):
    load(capture_case)
    pin = {'path': 'captures.json', 'sha256': file_hash(Path('captures.json'))}
    Path('captures.json').write_text('{}')
    with pytest.raises(CurationError, match='hash mismatch'):
        load_source_captures(pin)
    Path('response.txt').write_text('L10@P2: Altered quote.')
    with pytest.raises(CurationError, match='hash mismatch'):
        load(capture_case)


@pytest.mark.parametrize('update,match', [
    ({'capture_id': 'absent'}, 'Unknown source capture'),
    ({'reference': 'doi:10.1234/other'}, 'reference or representation mismatch'),
    ({'kind': 'oa_fulltext'}, 'reference or representation mismatch'),
    ({'quote': 'Organism A can ferment glucose.'}, 'not verbatim'),
    ({'quote': 'It produces product B.\nAnother section.'}, 'omitted source lines'),
])
def test_capture_quote_rejects_unbound_or_invented_spans(capture_case, update, match):
    captures, _ = load(capture_case)
    with pytest.raises(CurationError, match=match):
        capture_quote(captures, selection(**update))


@pytest.mark.parametrize('field,value', [('verified', False), ('doi', '10.1234/wrong'),
                                       ('title', 'Other title'), ('basis', ''), ('reviewer', '')])
def test_manual_identity_approval_must_be_explicit(capture_case, field, value):
    capture_case['captures'][0]['identity_review'][field] = value
    with pytest.raises(CurationError, match='manual DOI/title identity review'):
        load(capture_case)


def test_marked_lines_reject_combined_documents_and_ignore_unmarked_metadata():
    with pytest.raises(CurationError, match='unique and increasing'):
        extract_lines(b'L1: first\nSecond document\nL1: second')
    with pytest.raises(CurationError, match='no marked primary text'):
        extract_lines(b'Unmarked tool summary, not a primary-source quote.')


def test_page_range_marker_is_preserved_without_guessing_a_single_page():
    text, spans = extract_lines(b'L72@P0-1: One source line spans a page boundary.')
    assert text == 'One source line spans a page boundary.'
    assert spans[0]['page'] == '0-1'
