"""Citation extraction, caching, throttling and strict quote-integrity regressions."""
import base64
import hashlib
import io
import json
import urllib.error

import pytest
from kg_microbe_curation.identity import CurationError

from edgemech.evidence_campaign import references
from edgemech.literature_cache import (
    EXTRACTOR,
    LiteratureCache,
    abstract_text,
    full_text,
    retry_delay,
    verify_quote,
)


class Response(io.BytesIO):
    status = 200


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


def test_citation_context_and_base64():
    citation = 'Paper (doi:10.1234/abc(DEF)). PMID:123'
    refs, warnings = references({'source_citation': citation,
                                'source_citation_base64': base64.b64encode(citation.encode()).decode(),
                                'publications': 'https://bacdive.dsmz.de/strain/123'})
    assert set(refs) == {'doi:10.1234/abc(def)', 'pmid:123'}
    assert not warnings
    assert references({'source_citation_base64': 'bad!'})[1] == ['invalid_citation_base64']
    assert references({'prego_evidence': '23 of 51 samples'})[0] == {}
    assert references({'prego_evidence_url': 'https://pubmed.ncbi.nlm.nih.gov/123/'})[0]
    assert references({'source_citation_base64': base64.b64encode(b'other').decode()})[1]


def test_exact_quote_preserves_inline_chemistry_and_rejects_paraphrase():
    text = abstract_text('<p>H<sub>2</sub> &amp; CO<sub>2</sub> support growth.</p>')
    assert text == 'H2 & CO2 support growth.'
    doc = {'text': text, 'text_sha256': hashlib.sha256(text.encode()).hexdigest(),
           'response': {'response_sha256': 'a' * 64}, 'extractor': EXTRACTOR, 'kind': 'abstract'}
    proof = verify_quote(doc, 'CO2 support growth.')
    assert text[proof['start']:proof['end']] == proof['quote']
    assert 'supported' not in proof  # Integrity is not scientific entailment.
    with pytest.raises(CurationError, match='verbatim'):
        verify_quote(doc, 'CO2 causes growth.')
    with pytest.raises(CurationError, match='nonempty'):
        verify_quote(doc, ' ')
    doc['text'] = 'tampered'
    with pytest.raises(CurationError, match='hash'):
        verify_quote(doc, 'tampered')


def test_fulltext_requires_exact_pmc_identity():
    raw = b'<article><front><article-meta><article-id pub-id-type="pmc">123</article-id></article-meta></front><body><p>Observation.</p></body></article>'
    assert full_text(raw, 'PMC123') == 'Observation.'
    with pytest.raises(CurationError, match='identity'):
        full_text(raw, 'PMC999')


def test_response_cache_is_durable_and_tamper_evident(tmp_path):
    calls = []
    clock = Clock()

    def opener(request, timeout):
        assert '@' not in str(request.headers)
        calls.append(request.full_url)
        return Response(b'{}')

    root = tmp_path / 'cache'
    with LiteratureCache(root, opener=opener, clock=clock, sleeper=clock.sleep) as cache:
        first = cache.request('one', 'https://example.test/one')
        second = cache.request('one', 'https://example.test/one')
        assert not first['cache_hit'] and second['cache_hit']
        assert len(calls) == 1
    with LiteratureCache(root, opener=opener, clock=clock, sleeper=clock.sleep) as cache:
        assert cache.request('one', 'https://example.test/one')['cache_hit']
        (root / first['response_path']).write_bytes(b'bad')
        with pytest.raises(CurationError, match='integrity'):
            cache.request('one', 'https://example.test/one')


def test_long_retry_after_is_persisted_and_stops_sends(tmp_path):
    clock = Clock()
    calls = []

    def opener(request, timeout):
        calls.append(request.full_url)
        raise urllib.error.HTTPError(request.full_url, 429, 'slow', {'Retry-After': '120'}, None)

    root = tmp_path / 'cache'
    with LiteratureCache(root, opener=opener, clock=clock, sleeper=clock.sleep) as cache:
        assert cache.request('one', 'https://example.test/one')['status'] == 'retry_later'
    with LiteratureCache(root, opener=opener, clock=clock, sleeper=clock.sleep) as cache:
        assert cache.request('two', 'https://example.test/two')['status'] == 'retry_later'
    assert len(calls) == 1
    assert clock.now == 1000


def test_404_is_negative_cached(tmp_path):
    calls = []

    def opener(request, timeout):
        calls.append(1)
        raise urllib.error.HTTPError(request.full_url, 404, 'absent', {}, None)

    with LiteratureCache(tmp_path / 'cache', opener=opener) as cache:
        assert cache.request('one', 'https://example.test/one')['status'] == 'http_404'
        assert cache.request('one', 'https://example.test/one')['cache_hit']
    assert len(calls) == 1


def test_retry_exhaustion_and_shared_lock(tmp_path):
    clock = Clock()
    calls = []

    def opener(request, timeout):
        calls.append(1)
        raise urllib.error.URLError('temporary')

    with LiteratureCache(tmp_path / 'cache', opener=opener, clock=clock, sleeper=clock.sleep) as cache:
        with pytest.raises(CurationError, match='busy'):
            with LiteratureCache(tmp_path / 'cache'):
                pass
        assert cache.request('one', 'https://example.test/one')['status'] == 'retry_exhausted'
    assert len(calls) == 3
    assert clock.now >= 1006


def test_document_rejects_wrong_identifier(tmp_path):
    raw = json.dumps({'hitCount': 1, 'resultList': {'result': [
        {'doi': '10.1234/wrong', 'abstractText': 'Looks plausible.'}
    ]}}).encode()
    with LiteratureCache(tmp_path / 'cache', opener=lambda *a, **kw: Response(raw)) as cache:
        result = cache.document('doi:10.1234/right')
        assert result['status'] == 'ambiguous_or_missing_identifier'
        assert result['documents'] == []


def test_negative_identifier_hits_do_not_extend_expiry(tmp_path):
    clock = Clock()
    raw = json.dumps({'hitCount': 0, 'resultList': {'result': []}}).encode()
    with LiteratureCache(tmp_path / 'cache', opener=lambda *a, **kw: Response(raw),
                         clock=clock, sleeper=clock.sleep) as cache:
        cache.document('doi:10.1234/absent')
        deadline = cache.db.execute('SELECT expires FROM cache').fetchone()[0]
        clock.sleep(100)
        cache.document('doi:10.1234/absent')
        assert cache.db.execute('SELECT expires FROM cache').fetchone()[0] == deadline


def test_copied_source_manifest_is_verified(tmp_path):
    from edgemech.evidence_campaign import load_cohort
    for name, value in [('occurrences', []), ('queue', {})]:
        (tmp_path / f'{name}.json').write_text(json.dumps(value))
    manifest = {name + '_sha256': hashlib.sha256((tmp_path / f'{name}.json').read_bytes()).hexdigest()
                for name in ('occurrences', 'queue')}
    manifest['source'] = {'manifest_sha256': hashlib.sha256(b'original').hexdigest()}
    (tmp_path / 'manifest.json').write_text(json.dumps(manifest))
    (tmp_path / 'source-manifest.json').write_bytes(b'tampered')
    with pytest.raises(CurationError, match='Copied source manifest'):
        load_cohort(tmp_path)


def test_retry_deferred_identifier_is_not_completed(tmp_path, monkeypatch):
    import edgemech.literature_cache as module
    cohort = tmp_path / 'cohort'
    cohort.mkdir()
    (cohort / 'manifest.json').write_text('{}')
    monkeypatch.setattr(module, 'load_cohort', lambda path: (
        {'queue_identifiers': 2}, [], {'doi:10.1234/a': [], 'doi:10.1234/b': []}))
    monkeypatch.setattr(module.LiteratureCache, 'document', lambda self, key: {
        'metadata': {'status': 'retry_later', 'cache_hit': False}, 'documents': []})
    result = module.retrieve_cohort(cohort, tmp_path / 'cache', tmp_path / 'out', limit=None)
    assert result['attempted_identifiers'] == 1
    assert result['completed_identifiers'] == 0
    assert result['deferred_identifiers'] == 2


def test_retry_after_http_date():
    assert retry_delay('Thu, 01 Jan 1970 00:20:00 GMT', 1000) == 200
    assert retry_delay('invalid', 1000) is None


def test_documented_microbedecoder_display_policy_keeps_original_bytes():
    original = b'Pr\xe9vot\tDOI:10.1234/abc\\note\n'
    display = original.decode('utf-8', errors='replace').replace('\\', '\\\\').replace('\t', '\\t').replace('\n', '\\n')
    fields = {'primary_knowledge_source': 'infores:microbedecoder-literature',
              'value_encoding': 'backslash', 'source_citation': display,
              'source_citation_base64': base64.b64encode(original).decode()}
    assert references(fields)[1] == []
    fields['source_citation'] = display + 'changed'
    assert references(fields)[1] == ['citation_base64_plaintext_mismatch']


def test_rehashing_fabricated_text_cannot_pass_source_reextraction(tmp_path):
    from edgemech.content_inventory import _write_json
    from edgemech.literature_cache import load_retrieval
    from edgemech.storage.parquet import file_hash

    raw = json.dumps({'hitCount': 1, 'resultList': {'result': [
        {'doi': '10.1234/example', 'abstractText': 'Actual source text.'}
    ]}}).encode()
    with LiteratureCache(tmp_path / 'cache', opener=lambda *a, **kw: Response(raw)) as cache:
        record = cache.document('doi:10.1234/example')
        record['documents'][0]['text'] = 'Fabricated source text.'
        record['documents'][0]['text_sha256'] = hashlib.sha256(b'Fabricated source text.').hexdigest()
        output = tmp_path / 'output'
        output.mkdir()
        _write_json(output / 'documents.json', [record])
        _write_json(output / 'manifest.json', {'documents_sha256': file_hash(output / 'documents.json')})
        with pytest.raises(CurationError, match='extraction'):
            load_retrieval(output, cache)
