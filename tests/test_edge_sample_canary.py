"""Offline bounds and durable retrieval checks for the helper-3 canary (2026-11-12)."""
import csv
import hashlib
import importlib.util
import io
import json
import sqlite3
import subprocess
import sys
import urllib.error
from collections import Counter
from pathlib import Path

import pytest

from edgemech.literature_cache import LiteratureCache

SCRIPT = (Path(__file__).resolve().parents[1] / 'scripts' / 'adhoc'
          / 'edge_sample_review_20261112' / 'retrieve.py')


@pytest.fixture
def runner():
    spec = importlib.util.spec_from_file_location('edge_sample_retrieve', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def occurrence(number):
    return f'urn:kg-microbe:occurrence:v1:{number:064x}'


def inputs(tmp_path, count=2):
    rows = [{'occurrence_id': occurrence(i)} for i in range(count)]
    plan = [{'occurrence_id': row['occurrence_id'], 'queries': ['"Fixture bacterium"']}
            for row in rows]
    manifest = tmp_path / 'manifest.jsonl'
    plan_path = tmp_path / 'plan.json'
    manifest.write_text(''.join(json.dumps(row) + '\n' for row in rows))
    plan_path.write_text(json.dumps(plan))
    return manifest, plan_path, tmp_path / 'output'


@pytest.mark.parametrize('damage', ['oversize', 'duplicate_edge', 'duplicate_plan',
                                    'missing_plan', 'unexpected_plan'])
def test_invalid_batches_fail_before_output_or_provider(runner, tmp_path, monkeypatch, damage):
    manifest, plan_path, output = inputs(tmp_path, 51 if damage == 'oversize' else 2)
    if damage == 'duplicate_edge':
        row = manifest.read_text().splitlines()[0]
        manifest.write_text(row + '\n' + row + '\n')
    else:
        plan = json.loads(plan_path.read_text())
        if damage == 'duplicate_plan':
            plan[1] = plan[0]
        elif damage == 'missing_plan':
            plan.pop()
        elif damage == 'unexpected_plan':
            plan[1]['occurrence_id'] = occurrence(500)
        plan_path.write_text(json.dumps(plan))

    def forbidden(*args, **kwargs):
        pytest.fail('Invalid input reached the provider cache')

    monkeypatch.setattr(runner, 'LiteratureCache', forbidden)
    with pytest.raises(ValueError):
        runner.retrieve(manifest, plan_path, output)
    assert not output.exists()


def test_fifty_edge_dry_run_has_no_output_or_provider(runner, tmp_path, monkeypatch, capsys):
    manifest, plan_path, output = inputs(tmp_path, 50)

    def forbidden(*args, **kwargs):
        pytest.fail('Dry run reached the provider cache')

    monkeypatch.setattr(runner, 'LiteratureCache', forbidden)
    runner.retrieve(manifest, plan_path, output, dry_run=True)
    receipt = json.loads(capsys.readouterr().out)
    assert receipt['edges'] == 50
    assert receipt['distinct_queries'] == 1
    assert receipt['concurrent_requests'] == 1
    assert not output.exists()


class Response(io.BytesIO):
    status = 200


class Clock:
    def __init__(self):
        self.value = 1000.0

    def now(self):
        return self.value

    def sleep(self, duration):
        self.value += duration


def test_shared_query_persists_real_cache_packets_and_attempts(runner, tmp_path, monkeypatch):
    manifest, plan_path, output = inputs(tmp_path)
    payload = {'hitCount': 1, 'resultList': {'result': [{
        'source': 'MED', 'id': '1234', 'pmid': '1234', 'doi': '10.1234/fixture',
        'title': 'Synthetic fixture', 'abstractText': 'Fixture <i>bacterium</i> uses glucose.',
        'isOpenAccess': 'N'}]}}
    raw = json.dumps(payload).encode()
    calls = []
    clock = Clock()

    def opener(request, timeout):
        calls.append((request.full_url, request.headers, timeout))
        return Response(raw)

    monkeypatch.setattr(runner, 'LiteratureCache', lambda root: LiteratureCache(
        root, opener=opener, clock=clock.now, sleeper=clock.sleep, interval=1))
    runner.retrieve(manifest, plan_path, output)

    packets = [json.loads(path.read_text()) for path in sorted((output / 'packets').glob('*.json'))]
    packets.sort(key=lambda packet: packet["occurrence_id"])
    assert len(packets) == 2
    assert [p['api_attempts'] for p in packets] == [1, 0]
    assert [p['searches'][0]['response']['cache_hit'] for p in packets] == [False, True]
    assert len(calls) == 1
    assert all('mailto' not in url and '@' not in str(headers) for url, headers, _ in calls)
    document = packets[0]['documents'][0]['documents'][0]
    assert document['text'] == 'Fixture bacterium uses glucose.'
    assert document['text_sha256'] == hashlib.sha256(document['text'].encode()).hexdigest()
    digest = hashlib.sha256(raw).hexdigest()
    assert document['response']['response_sha256'] == digest
    assert (output / 'cache' / f'{digest}.response').read_bytes() == raw
    receipt = json.loads((output / 'retrieval-receipt.json').read_text())
    assert receipt['edges_persisted'] == 2
    assert receipt['new_api_attempts'] == 1
    assert receipt['all_attempt_status_counts'] == {'200': 1}
    assert receipt['manifest_sha256'] == hashlib.sha256(manifest.read_bytes()).hexdigest()
    assert receipt['plan_sha256'] == hashlib.sha256(plan_path.read_bytes()).hexdigest()
    with sqlite3.connect(output / 'cache' / 'cache.sqlite') as db:
        assert db.execute('SELECT COUNT(*) FROM attempts').fetchone()[0] == 1


def test_provider_failure_is_persisted_without_documents(runner, tmp_path, monkeypatch):
    manifest, plan_path, output = inputs(tmp_path, 1)
    clock = Clock()
    calls = []

    def opener(request, timeout):
        calls.append(request.full_url)
        raise urllib.error.URLError('Synthetic offline failure')

    monkeypatch.setattr(runner, 'LiteratureCache', lambda root: LiteratureCache(
        root, opener=opener, clock=clock.now, sleeper=clock.sleep, interval=1))
    runner.retrieve(manifest, plan_path, output)
    packet = json.loads(next((output / 'packets').glob('*.json')).read_text())
    assert packet['documents'] == []
    assert packet['searches'][0]['response']['status'] == 'retry_exhausted'
    assert packet['api_attempts'] == len(calls) == 3
    receipt = json.loads((output / 'retrieval-receipt.json').read_text())
    assert receipt['new_api_attempts'] == 3
    assert receipt['all_attempt_status_counts'] == {'URLError': 3}


def test_optimized_python_still_rejects_oversize_batch(tmp_path):
    manifest, plan_path, output = inputs(tmp_path, 51)
    # Provider construction is replaced in the subprocess: a regression must
    # fail this test without performing any live request.
    code = '''
import runpy
import sys
from pathlib import Path
namespace = runpy.run_path(sys.argv[1])
def forbidden(*args, **kwargs):
    raise SystemExit(42)
namespace["retrieve"].__globals__["LiteratureCache"] = forbidden
try:
    namespace["retrieve"](Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]))
except ValueError:
    raise SystemExit(0)
raise SystemExit(43)
'''
    result = subprocess.run(
        [sys.executable, '-O', '-B', '-c', code, str(SCRIPT), str(manifest),
         str(plan_path), str(output)], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert not output.exists()


def test_distinct_ids_with_shared_suffix_persist_distinct_packets(runner, tmp_path, monkeypatch):
    manifest, plan_path, output = inputs(tmp_path)
    ids = ['urn:first:shared', 'urn:second:shared']
    manifest.write_text(''.join(json.dumps({'occurrence_id': ident}) + '\n' for ident in ids))
    plan_path.write_text(json.dumps([{'occurrence_id': ident, 'queries': []} for ident in ids]))
    clock = Clock()

    def forbidden(*args, **kwargs):
        pytest.fail('An empty query plan reached the network')

    monkeypatch.setattr(runner, 'LiteratureCache', lambda root: LiteratureCache(
        root, opener=forbidden, clock=clock.now, sleeper=clock.sleep))
    runner.retrieve(manifest, plan_path, output)
    assert {path.name for path in (output / 'packets').glob('*.json')} == {
        hashlib.sha256(ident.encode()).hexdigest() + '.json' for ident in ids}
    assert {json.loads(path.read_text())['occurrence_id']
            for path in (output / 'packets').glob('*.json')} == set(ids)


@pytest.fixture
def finalizer():
    script = SCRIPT.with_name('finalize_scientific.py')
    spec = importlib.util.spec_from_file_location('edge_sample_finalize', script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def evidence_case(runner, tmp_path, monkeypatch):
    manifest, plan_path, retrieval = inputs(tmp_path, 1)
    raw = json.dumps({'hitCount': 1, 'resultList': {'result': [{
        'source': 'MED', 'id': '1234', 'pmid': '1234', 'doi': '10.1234/fixture',
        'title': 'Synthetic fixture', 'abstractText': 'Fixture bacterium uses glucose.',
        'isOpenAccess': 'N'}]}}).encode()
    clock = Clock()
    monkeypatch.setattr(runner, 'LiteratureCache', lambda root: LiteratureCache(
        root, opener=lambda request, timeout: Response(raw), clock=clock.now,
        sleeper=clock.sleep))
    runner.retrieve(manifest, plan_path, retrieval)
    decisions = tmp_path / 'decisions.json'
    decisions.write_text(json.dumps([{
        'occurrence_id': occurrence(0), 'verdict': 'SUPPORTED',
        'rationale': 'The synthetic abstract states this exact fixture assertion.',
        'citations': [{'paper': 0, 'document': 0, 'quote': 'Fixture bacterium uses glucose.'}]}]))
    return manifest, decisions, retrieval, tmp_path / 'ledger.jsonl'


def test_finalizer_replays_quote_and_publication_identity(finalizer, evidence_case):
    finalizer.finalize(*evidence_case)
    ledger = json.loads(evidence_case[-1].read_text())
    assert ledger['verdict'] == 'SUPPORTED'
    assert ledger['evidence'][0]['quote'] == 'Fixture bacterium uses glucose.'
    assert ledger['evidence'][0]['pmid'] == '1234'
    assert ledger['evidence'][0]['doi'] == '10.1234/fixture'
    assert len(ledger['evidence'][0]['response_sha256']) == 64
    assert ledger['evidence'][0]['start'] == 0
    assert ledger['adjudicating_model']


def test_finalizer_rejects_definitive_verdict_without_quote(finalizer, evidence_case):
    manifest, decisions, retrieval, output = evidence_case
    rows = json.loads(decisions.read_text())
    rows[0]['citations'] = []
    decisions.write_text(json.dumps(rows))
    with pytest.raises(ValueError, match='verified evidence'):
        finalizer.finalize(manifest, decisions, retrieval, output)
    assert not output.exists()


def test_finalizer_rejects_internally_consistent_fabricated_text(finalizer, evidence_case):
    manifest, decisions, retrieval, output = evidence_case
    packet_path = next((retrieval / 'packets').glob('*.json'))
    packet = json.loads(packet_path.read_text())
    document = packet['documents'][0]['documents'][0]
    document['text'] = 'Fixture bacterium does not use glucose.'
    document['text_sha256'] = hashlib.sha256(document['text'].encode()).hexdigest()
    packet_path.write_text(json.dumps(packet))
    rows = json.loads(decisions.read_text())
    rows[0]['citations'][0]['quote'] = document['text']
    decisions.write_text(json.dumps(rows))
    with pytest.raises(ValueError, match='Text hash mismatch on replay'):
        finalizer.finalize(manifest, decisions, retrieval, output)
    assert not output.exists()


@pytest.mark.parametrize('damage', ['missing_search', 'failed_search', 'failed_fulltext'])
def test_not_found_requires_complete_searches(finalizer, evidence_case, damage):
    manifest, decisions, retrieval, output = evidence_case
    rows = json.loads(decisions.read_text())
    rows[0].update(verdict='NOT_FOUND', citations=[])
    decisions.write_text(json.dumps(rows))
    packet_path = next((retrieval / 'packets').glob('*.json'))
    packet = json.loads(packet_path.read_text())
    if damage == 'missing_search':
        packet['searches'] = []
    elif damage == 'failed_search':
        packet['searches'][0]['response']['status'] = 'retry_exhausted'
    else:
        packet['documents'][0]['fulltext_response'] = {'status': 'http_403'}
    packet_path.write_text(json.dumps(packet))
    with pytest.raises(ValueError, match='completed searches|Incomplete fulltext'):
        finalizer.finalize(manifest, decisions, retrieval, output)
    assert not output.exists()


@pytest.fixture
def sampler():
    script = SCRIPT.with_name('build_sample.py')
    spec = importlib.util.spec_from_file_location('edge_sample_builder', script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def stratum(row):
    return tuple(row[key] for key in ('origin_transform', 'content_accuracy_verdict', 'disposition'))


def test_allocation_is_deterministic_and_respects_sample_design(sampler, tmp_path, monkeypatch):
    artifact_root = sampler.OUT
    (tmp_path / 'populations.csv').write_bytes((artifact_root / 'populations.csv').read_bytes())
    monkeypatch.setattr(sampler, 'OUT', tmp_path)
    first = sampler.allocation()
    first_bytes = (tmp_path / 'allocation.csv').read_bytes()
    second = sampler.allocation()
    assert first == second
    assert first_bytes == (tmp_path / 'allocation.csv').read_bytes()
    assert first_bytes == (artifact_root / 'allocation.csv').read_bytes()
    assert sum(row['sample_quota'] for row in first) == 10000
    retained = [row for row in first if row['disposition'] == 'retained']
    omitted = [row for row in first if row['disposition'] != 'retained']
    assert sum(row['sample_quota'] for row in retained) == 8500
    assert sum(row['sample_quota'] for row in omitted) == 1500
    transform_totals = Counter()
    reason_totals = Counter()
    for row in retained:
        transform_totals[row['origin_transform']] += row['sample_quota']
    for row in omitted:
        reason_totals[row['disposition']] += row['sample_quota']
    assert len(transform_totals) == 13
    assert min(transform_totals.values()) >= 385
    assert len(reason_totals) == 5
    assert set(reason_totals.values()) == {300}
    assert all(0 < row['sample_quota'] <= row['population'] for row in first)
    assert sampler.apportion(8, {'b': 10, 'a': 1, 'c': 10}) == {
        'a': 1, 'b': 4, 'c': 3}
    assert sampler.apportion(8, {'c': 10, 'a': 1, 'b': 10}) == {
        'a': 1, 'b': 4, 'c': 3}


def test_saved_manifest_matches_every_quota_weight_and_seed(sampler):
    rows = [json.loads(line) for line in (sampler.OUT / 'manifest.jsonl').read_text().splitlines()]
    with (sampler.OUT / 'allocation.csv').open() as handle:
        quotas = {stratum(row): row for row in csv.DictReader(handle)}
    assert len(rows) == len({row['occurrence_id'] for row in rows}) == 10000
    counts = Counter(stratum(row) for row in rows)
    assert counts == {key: int(row['sample_quota']) for key, row in quotas.items()}
    assert sum(row['disposition'] == 'retained' for row in rows) == 8500
    for row in rows:
        quota = quotas[stratum(row)]
        assert row['stratum_quota'] == int(quota['sample_quota'])
        assert row['stratum_population'] == int(quota['population'])
        assert row['sampling_weight'] == pytest.approx(
            row['stratum_population'] / row['stratum_quota'])
        assert row['sample_hash'] == hashlib.md5(
            (sampler.SEED + ':' + row['occurrence_id']).encode()).hexdigest()
    metadata = json.loads((sampler.OUT / 'sampling-metadata.json').read_text())
    for relative_path, expected in metadata['hashes'].items():
        assert hashlib.sha256((sampler.ROOT / relative_path).read_bytes()).hexdigest() == expected


def test_saved_canary_replays_deterministically_with_all_coverage(sampler):
    rows = [json.loads(line) for line in (sampler.OUT / 'manifest.jsonl').read_text().splitlines()]
    saved = [json.loads(line) for line in (sampler.OUT / 'canary.jsonl').read_text().splitlines()]
    reconstructed = sampler.canary(rows)
    assert [row['occurrence_id'] for row in reconstructed] == [row['occurrence_id'] for row in saved]
    assert [row['canary_ordinal'] for row in saved] == list(range(1, 51))
    assert len(saved) == len({row['occurrence_id'] for row in saved}) == 50
    assert len({row['origin_transform'] for row in saved}) == 13
    omitted = [row for row in saved if row['disposition'] != 'retained']
    retained = [row for row in saved if row['disposition'] == 'retained']
    assert len(omitted) == 11
    assert len(retained) == 39
    assert len({row['disposition'] for row in omitted}) == 5
    assert set(Counter(row['origin_transform'] for row in retained).values()) == {3}
    for row in saved:
        assert (row['curated_source_record'] is not None) == (row['disposition'] == 'retained')
        assert (row['omitted_source_record'] is not None) == (row['disposition'] != 'retained')


def test_finalizer_rejects_changed_claim_with_same_occurrence_id(finalizer, evidence_case):
    manifest, decisions, retrieval, output = evidence_case
    row = json.loads(manifest.read_text())
    row['subject'] = 'NCBITaxon:999999999'
    manifest.write_text(json.dumps(row) + '\n')
    with pytest.raises(ValueError):
        finalizer.finalize(manifest, decisions, retrieval, output)
    assert not output.exists()


@pytest.fixture
def oa_evidence_case(runner, tmp_path, monkeypatch):
    manifest, plan_path, retrieval = inputs(tmp_path, 1)
    core = json.dumps({'hitCount': 1, 'resultList': {'result': [{
        'source': 'MED', 'id': '1234', 'pmid': '1234', 'pmcid': 'PMC12345',
        'doi': '10.1234/fixture', 'title': 'Synthetic fixture',
        'abstractText': 'Fixture bacterium uses glucose.', 'isOpenAccess': 'Y'}]}}).encode()
    xml = b'''<article><front><article-meta>
<article-id pub-id-type="pmc">12345</article-id>
<article-id pub-id-type="pmid">1234</article-id>
<article-id pub-id-type="doi">10.1234/fixture</article-id>
<title-group><article-title>Synthetic fixture</article-title></title-group>
</article-meta></front><body><sec><p>Fixture bacterium uses glucose.</p></sec></body></article>'''
    clock = Clock()

    def opener(request, timeout):
        return Response(xml if request.full_url.endswith('/fullTextXML') else core)

    monkeypatch.setattr(runner, 'LiteratureCache', lambda root: LiteratureCache(
        root, opener=opener, clock=clock.now, sleeper=clock.sleep))
    runner.retrieve(manifest, plan_path, retrieval)
    decisions = tmp_path / 'decisions.json'
    decisions.write_text(json.dumps([{
        'occurrence_id': occurrence(0), 'verdict': 'SUPPORTED',
        'rationale': 'The synthetic full text states this exact fixture assertion.',
        'citations': [{'paper': 0, 'document': 1, 'quote': 'Fixture bacterium uses glucose.'}]}]))
    return manifest, decisions, retrieval, tmp_path / 'ledger.jsonl'


def test_finalizer_accepts_oa_quote_with_bound_identity(finalizer, oa_evidence_case):
    finalizer.finalize(*oa_evidence_case)
    ledger = json.loads(oa_evidence_case[-1].read_text())
    assert ledger['evidence'][0]['kind'] == 'oa_fulltext'
    assert ledger['evidence'][0]['doi'] == '10.1234/fixture'
    assert ledger['evidence'][0]['pmid'] == '1234'


@pytest.mark.parametrize('field,bogus', [
    ('doi', '10.9999/invented'), ('pmid', '999999'), ('pmcid', 'PMC99999'),
    ('source', 'Invented source'), ('id', '999999')])
def test_finalizer_rejects_oa_identity_not_bound_to_raw_search(
        finalizer, oa_evidence_case, field, bogus):
    manifest, decisions, retrieval, output = oa_evidence_case
    packet_path = next((retrieval / 'packets').glob('*.json'))
    packet = json.loads(packet_path.read_text())
    packet['documents'][0][field] = bogus
    packet_path.write_text(json.dumps(packet))
    with pytest.raises(ValueError):
        finalizer.finalize(manifest, decisions, retrieval, output)
    assert not output.exists()


@pytest.fixture
def reporter():
    spec = importlib.util.spec_from_file_location('edge_sample_report', SCRIPT.with_name('report.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('relative', ['sample/canary.jsonl',
                                      'sample/private-provenance/canary.jsonl'])
def test_report_resolves_both_recorded_private_canary_layouts(reporter, tmp_path, relative):
    path = tmp_path / relative
    path.parent.mkdir(parents=True)
    path.write_text('{"fixture": true}\n')
    metadata = {'private_original_canary': {
        'path': relative, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}}
    assert reporter.resolve_original_canary(tmp_path, metadata) == path.resolve()


def test_report_rejects_changed_private_canary(reporter, tmp_path):
    path = tmp_path / 'canary.jsonl'
    path.write_text('{"fixture": true}\n')
    metadata = {'private_original_canary': {
        'path': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}}
    path.write_text('{"fixture": false}\n')
    with pytest.raises(ValueError):
        reporter.resolve_original_canary(tmp_path, metadata)


@pytest.mark.parametrize('escape', ['absolute', 'parent', 'symlink'])
def test_report_rejects_private_canary_path_escape(reporter, tmp_path, escape):
    data = tmp_path / 'data'
    data.mkdir()
    outside = tmp_path / 'outside.jsonl'
    outside.write_text('{"fixture": true}\n')
    if escape == 'absolute':
        relative = str(outside)
    elif escape == 'parent':
        relative = '../outside.jsonl'
    else:
        (data / 'linked.jsonl').symlink_to(outside)
        relative = 'linked.jsonl'
    metadata = {'private_original_canary': {
        'path': relative, 'sha256': hashlib.sha256(outside.read_bytes()).hexdigest()}}
    with pytest.raises(ValueError):
        reporter.resolve_original_canary(data, metadata)


@pytest.fixture
def source_runner():
    spec = importlib.util.spec_from_file_location(
        'edge_sample_source', SCRIPT.with_name('source_fidelity.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_source_paths_stay_relative_under_alternate_raw_root(source_runner, tmp_path):
    raw_root = tmp_path / 'alternate-cache'
    raw_root.mkdir()
    source = raw_root / 'table.csv'
    source.write_text('taxon,trait\nfixture,positive\n')
    relative = source_runner.capture_source_relative_path(source, raw_root)
    assert relative == 'table.csv'
    legacy_record = {'source_path': str(source)}
    assert source_runner.source_relative_path(legacy_record, raw_root) == relative
    captured_record = {**legacy_record, 'source_relative_path': relative}
    assert source_runner.source_relative_path(captured_record) == relative
    assert str(tmp_path) not in relative


def test_source_paths_reject_unknown_absolute_root(source_runner, tmp_path):
    root = tmp_path / 'approved'
    root.mkdir()
    source = tmp_path / 'elsewhere' / 'table.csv'
    source.parent.mkdir()
    source.write_text('fixture\n')
    with pytest.raises(ValueError):
        source_runner.source_relative_path({'source_path': str(source)}, root)
    with pytest.raises(ValueError):
        source_runner.capture_source_relative_path(source, root)


@pytest.mark.parametrize('damage', ['absolute', 'parent'])
def test_source_paths_reject_unsafe_captured_relative_path(source_runner, tmp_path, damage):
    relative = str(tmp_path / 'table.csv') if damage == 'absolute' else '../table.csv'
    with pytest.raises(ValueError):
        source_runner.source_relative_path({'source_relative_path': relative})


def test_source_claims_bind_frozen_manifest_bytes(source_runner, tmp_path):
    path = tmp_path / 'canary.jsonl'
    rows = [{'occurrence_id': occurrence(index), 'canary_ordinal': index + 1,
             'subject': 'NCBITaxon:1', 'predicate': 'biolink:has_phenotype',
             'object': 'METPO:1000698', 'origin_transform': 'fixture/edges.tsv'}
            for index in range(50)]
    path.write_text(''.join(json.dumps(row) + '\n' for row in rows))
    metadata = {'hashes': {'artifacts/edge-sample-review-20261112/canary.jsonl':
                           hashlib.sha256(path.read_bytes()).hexdigest()}}
    (tmp_path / 'sampling-metadata.json').write_text(json.dumps(metadata))
    assert source_runner.verify_claim_manifest(tmp_path) == rows
    rows[0]['predicate'] = 'biolink:capable_of'
    path.write_text(''.join(json.dumps(row) + '\n' for row in rows))
    with pytest.raises(ValueError):
        source_runner.verify_claim_manifest(tmp_path)
