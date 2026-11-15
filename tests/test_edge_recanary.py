"""2026-11-13: offline recanary retrieval bounds, identities, privacy and telemetry."""
import hashlib
import importlib.util
import io
import json
import subprocess
import urllib.error
from pathlib import Path

import pytest

from edgemech.literature_cache import LiteratureCache

SCRIPT = (Path(__file__).resolve().parents[1] / 'scripts/adhoc'
          / 'edge_recanary_20261113/retrieve_targeted.py')


@pytest.fixture
def runner(monkeypatch):
    spec = importlib.util.spec_from_file_location('recanary_retrieve_test', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module.FA, 'try_zotero_local', lambda **kwargs: None)
    return module


class Clock:
    def __init__(self):
        self.value = 1000.0

    def now(self):
        return self.value

    def sleep(self, duration):
        self.value += duration


class Response(io.BytesIO):
    status = 200
    headers = {'Content-Type': 'application/json'}


def setup_inputs(tmp_path, count=1, applicable=True):
    rows = [{'occurrence_id': f'urn:fixture:{i:064x}', 'subject': 'NCBITaxon:1',
             'predicate': 'biolink:has_phenotype', 'object': 'METPO:1000698'}
            for i in range(count)]
    plans = [{'occurrence_id': row['occurrence_id'],
              'applicability': 'APPLICABLE' if applicable else 'NOT_APPLICABLE',
              'applicability_rule': 'fixture-rule',
              'primary_references': [{'reference': 'doi:10.1234/fixture',
                                      'role': 'species_description',
                                      'identity_verified': True,
                                      'identity_basis': 'Synthetic exact source-record citation'}]
              if applicable else [],
              'general_queries': ['"Fixture bacterium"'] if applicable else []}
             for row in rows]
    manifest, plan = tmp_path / 'manifest.jsonl', tmp_path / 'plan.json'
    manifest.write_text(''.join(json.dumps(row) + '\n' for row in rows))
    plan.write_text(json.dumps(plans))
    return manifest, plan, tmp_path / 'output'


def core_payload(doi='10.1234/fixture'):
    return json.dumps({'hitCount': 1, 'resultList': {'result': [{
        'source': 'MED', 'id': '123', 'pmid': '123', 'doi': doi,
        'title': 'Synthetic species description', 'isOpenAccess': 'N',
        'abstractText': 'Fixture bacterium has the measured trait.'}]}}).encode()


@pytest.mark.parametrize('damage', ['oversize', 'duplicate', 'dataset', 'record_doi',
                                    'wrong_inherited_doi', 'unverified', 'inapplicable_queries'])
def test_invalid_plan_fails_before_network(runner, tmp_path, damage):
    manifest, plan_path, output = setup_inputs(tmp_path, 51 if damage == 'oversize' else 1)
    plan = json.loads(plan_path.read_text())
    if damage == 'duplicate':
        manifest.write_text(manifest.read_text() * 2)
        plan *= 2
    elif damage in {'dataset', 'record_doi', 'wrong_inherited_doi'}:
        plan[0]['primary_references'][0]['reference'] = {
            'dataset': 'pmid:41296543', 'record_doi': 'doi:10.83108/rn.123',
            'wrong_inherited_doi': 'doi:10.1093/nar/gkad994'}[damage]
    elif damage == 'unverified':
        plan[0]['primary_references'][0]['identity_verified'] = False
    elif damage == 'inapplicable_queries':
        plan[0]['applicability'] = 'NOT_APPLICABLE'
    plan_path.write_text(json.dumps(plan))
    with pytest.raises(ValueError):
        runner.run(manifest, plan_path, output, dry_run=True)
    assert not output.exists()


def test_dry_run_is_network_and_output_free(runner, tmp_path, capsys):
    manifest, plan, output = setup_inputs(tmp_path, 50)
    runner.run(manifest, plan, output, dry_run=True,
               opener=lambda *args, **kwargs: pytest.fail('dry run attempted retrieval'))
    result = json.loads(capsys.readouterr().out)
    assert result['selected_edges'] == 50
    assert result['concurrency'] == 1
    assert not output.exists()


def test_not_applicable_persists_packet_with_zero_calls(runner, tmp_path):
    manifest, plan, output = setup_inputs(tmp_path, applicable=False)
    receipt = runner.run(manifest, plan, output,
                         opener=lambda *args, **kwargs: pytest.fail('inapplicable retrieval'))
    assert receipt['api_attempts'] == 0
    packet = json.loads(next((output / 'packets').glob('*.json')).read_text())
    assert packet['retrieval_status'] == 'NOT_APPLICABLE'
    assert packet['primary'] == []


def test_primary_stage_only_fetches_exact_reference_and_replays_identity(runner, tmp_path):
    manifest, plan, output = setup_inputs(tmp_path)
    calls = []
    clock = Clock()

    def opener(request, timeout):
        calls.append(request.full_url)
        return Response(core_payload())

    receipt = runner.run(manifest, plan, output, opener=opener, clock=clock.now,
                         sleeper=clock.sleep, max_ladder_calls=0)
    assert len(calls) == receipt['api_attempts'] == 1
    assert receipt['api_attempts_by_service'] == {'europe_pmc': 1}
    assert 'DOI%3A' in calls[0]
    packet = json.loads(next((output / 'packets').glob('*.json')).read_text())
    assert packet['fallback'] == []
    result = packet['primary'][0]['result']
    document = result['documents'][0]
    with LiteratureCache(output / 'cache') as client:
        rebuilt = runner.replay_document(result, document, client)
        assert rebuilt['doi'] == '10.1234/fixture'
        assert rebuilt['pmid'] == '123'
        result['doi'] = '10.1234/invented'
        with pytest.raises(ValueError, match='identity'):
            runner.replay_document(result, document, client)
    events = [json.loads(line) for line in (output / 'http-attempts.jsonl').read_text().splitlines()]
    assert len(events) == 1 and events[0]['status'] == '200'
    assert '[redacted]' in runner.urllib.parse.unquote(events[0]['url'])


def test_fallback_requires_selection_and_authored_reason(runner, tmp_path):
    manifest, plan, output = setup_inputs(tmp_path)
    with pytest.raises(ValueError, match='explicit selected'):
        runner.run(manifest, plan, output, stage='fallback', dry_run=True)
    oid = json.loads(manifest.read_text())['occurrence_id']
    with pytest.raises(ValueError, match='insufficiency reason'):
        runner.run(manifest, plan, output, stage='fallback', edge_ids=[oid], dry_run=True)


def test_real_attempt_telemetry_counts_redirects_and_strips_credentials(runner, tmp_path):
    root = tmp_path / 'cache'
    root.mkdir()
    clock, requests = Clock(), []

    def opener(request, timeout):
        requests.append(request)
        if len(requests) == 1:
            raise urllib.error.HTTPError(request.full_url, 302, 'redirect',
                                         {'Location': 'https://download.example.test/article'}, None)
        return Response(b'payload')

    transport = runner.Transport(root, opener=opener, clock=clock.now, sleeper=clock.sleep)
    transport.edge, transport.stage = 'fixture', 'primary'
    raw, _ = transport.fetch('https://api.wiley.com/example?api_key=unit-test-key',
                             {'Wiley-TDM-Client-Token': 'synthetic-private-header'})
    assert raw == b'payload'
    assert [event['status'] for event in transport.events] == ['302', '200']
    assert transport.events[1]['started_at_epoch'] - transport.events[0]['started_at_epoch'] >= 1
    assert not any('token' in key.lower() for key, _ in requests[1].header_items())
    persisted = (tmp_path / 'http-attempts.jsonl').read_text()
    assert 'unit-test-key' not in persisted
    assert 'synthetic-private-header' not in persisted


def test_failure_is_counted_without_secret_exception_text(runner, tmp_path):
    root = tmp_path / 'cache'
    root.mkdir()
    clock = Clock()

    def opener(request, timeout):
        raise urllib.error.HTTPError(request.full_url, 403, 'unit-test-key', {}, None)

    transport = runner.Transport(root, opener=opener, clock=clock.now, sleeper=clock.sleep)
    with pytest.raises(urllib.error.HTTPError):
        transport.fetch('https://api.springernature.com/example?api_key=unit-test-key')
    log = (tmp_path / 'http-attempts.jsonl').read_text()
    assert 'unit-test-key' not in log
    assert transport.events[0]['service'] == 'springer'
    assert transport.events[0]['status'] == '403'


def test_fulltext_budget_counts_actual_requests(runner, tmp_path):
    root = tmp_path / 'cache'
    root.mkdir()
    clock = Clock()
    transport = runner.Transport(root, opener=lambda request, timeout: Response(b'fixture'),
                                 clock=clock.now, sleeper=clock.sleep)
    transport.budget = 1
    transport.fetch('https://example.test/one')
    with pytest.raises(runner.BudgetExceeded):
        transport.fetch('https://example.test/two')
    assert len(transport.events) == 1


def xml_document(doi='10.1234/fixture'):
    return (f'<article><front><article-meta><article-id pub-id-type="doi">{doi}'
            '</article-id><title-group><article-title>Fixture species</article-title>'
            '</title-group></article-meta></front><body><p>'
            + 'Fixture bacterium has the measured trait. ' * 6
            + '</p></body></article>').encode()


def test_xml_fulltext_requires_front_matter_identity_and_body(runner, tmp_path):
    metadata = {'doi': '10.1234/fixture', 'title': 'Fixture species'}
    document = runner.decode_document(xml_document(), tmp_path / 'unused.xml', metadata)
    assert document['identity_verified']
    assert document['text_sha256'] == hashlib.sha256(document['text'].encode()).hexdigest()
    with pytest.raises(ValueError, match='identity'):
        runner.decode_document(xml_document('10.1234/wrong'), tmp_path / 'unused.xml', metadata)
    with pytest.raises(ValueError, match='body'):
        runner.decode_document(xml_document().split(b'<body>')[0] + b'</article>',
                               tmp_path / 'unused.xml', metadata)


def test_pdf_title_alone_cannot_substitute_for_doi_binding(runner, tmp_path, monkeypatch):
    monkeypatch.setattr(runner.shutil, 'which', lambda name: 'fixture-pdftotext')
    metadata = {'doi': '10.1234/fixture', 'title': 'Synthetic description of a fixture species'}
    monkeypatch.setattr(runner.subprocess, 'run', lambda *args, **kwargs: subprocess.CompletedProcess(
        args[0], 0, stdout=(metadata['title'] + '\n' + 'Other text. ' * 40).encode()))
    with pytest.raises(ValueError, match='identity'):
        runner.decode_document(b'%PDF-fixture', tmp_path / 'fixture.pdf', metadata)
    monkeypatch.setattr(runner.subprocess, 'run', lambda *args, **kwargs: subprocess.CompletedProcess(
        args[0], 0, stdout=(metadata['title'] + '\ndoi: ' + metadata['doi'] + '\n' + 'Other text. ' * 40).encode()))
    assert runner.decode_document(b'%PDF-fixture', tmp_path / 'fixture.pdf', metadata)['identity_verified']


def test_replay_rejects_dataset_resolved_from_unknown_pmid(runner, tmp_path):
    manifest, plan_path, output = setup_inputs(tmp_path)
    plan = json.loads(plan_path.read_text())
    plan[0]['primary_references'][0]['reference'] = 'pmid:123'
    plan_path.write_text(json.dumps(plan))
    clock = Clock()
    runner.run(manifest, plan_path, output,
               opener=lambda request, timeout: Response(core_payload('10.1093/nar/gkad994')),
               clock=clock.now, sleeper=clock.sleep, max_ladder_calls=0)
    packet = json.loads(next((output / 'packets').glob('*.json')).read_text())
    result = packet['primary'][0]['result']
    assert result['status'] == 'excluded_dataset_or_wrong_inherited_reference'
    assert result['documents'] == []


def load_helper(name):
    spec = importlib.util.spec_from_file_location('recanary_test_' + name,
                                                  SCRIPT.with_name(name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('case', ['doi_prefix', 'other_title', 'reference_section', 'second_page'])
def test_pdf_binding_rejects_other_paper_identifiers(runner, tmp_path, monkeypatch, case):
    metadata = {'doi': '10.1234/fixture', 'title': 'Synthetic description of a fixture species'}
    text = metadata['title'] + '\ndoi: ' + metadata['doi'] + '\n' + 'Content text. ' * 40
    if case == 'doi_prefix':
        text = text.replace(metadata['doi'], metadata['doi'] + '-other-paper')
    elif case == 'other_title':
        text = text.replace(metadata['title'], 'An entirely different article title')
    elif case == 'reference_section':
        text = 'A different article\nReferences\n' + text
    else:
        text = 'A different first page\f' + text
    monkeypatch.setattr(runner.shutil, 'which', lambda name: 'fixture-pdftotext')
    monkeypatch.setattr(runner.subprocess, 'run', lambda *args, **kwargs: subprocess.CompletedProcess(
        args[0], 0, stdout=text.encode()))
    with pytest.raises(ValueError, match='identity'):
        runner.decode_document(b'%PDF-fixture', tmp_path / 'fixture.pdf', metadata)


@pytest.mark.parametrize('failure', ['http', 'budget'])
def test_swallowed_ladder_failures_cannot_pass_not_found(runner, tmp_path, failure):
    manifest, plan, output = setup_inputs(tmp_path)
    clock = Clock()

    def opener(request, timeout):
        if 'europepmc' in request.full_url:
            return Response(core_payload())
        raise urllib.error.HTTPError(request.full_url, 403, 'fixture denial', {}, None)

    receipt = runner.run(manifest, plan, output, opener=opener, clock=clock.now,
                         sleeper=clock.sleep, max_ladder_calls=0 if failure == 'budget' else 4)
    packet = json.loads(next((output / 'packets').glob('*.json')).read_text())
    attempts = packet['primary'][0]['result']['ladder_attempts']
    expected = 'BudgetExceeded' if failure == 'budget' else 'http_403'
    assert any(attempt['status'] == expected for attempt in attempts)
    finalizer = load_helper('finalize_scientific')
    with pytest.raises(ValueError, match='full-text ladder'):
        finalizer.validate_not_found(packet)
    assert receipt['api_attempts'] == (1 if failure == 'budget' else 3)


def test_finished_timer_is_accepted_by_scientific_finalizer(tmp_path):
    clock = load_helper('review_clock')
    finalizer = load_helper('finalize_scientific')
    packet_path = tmp_path / 'packet.json'
    packet_path.write_text('{"fixture": true}')
    root = tmp_path / 'reviews'
    begun = clock.begin_review(root, 'scientific', '1', packet_path)
    receipt = clock.finish_review(root, 'scientific', '1', {
        'canary_ordinal': 1, 'occurrence_id': 'urn:fixture:1',
        'verdict': 'NOT_ASSESSABLE', 'rationale': 'Synthetic fixture.'})
    assert receipt['stopped_monotonic_ns'] >= begun['timer']['started_monotonic_ns']
    assert receipt['elapsed_seconds'] == pytest.approx(
        (receipt['stopped_monotonic_ns'] - receipt['started_monotonic_ns']) / 1e9)
    decisions = finalizer.timed_decisions(root)
    assert decisions['urn:fixture:1']['final'][1]['elapsed_seconds'] == receipt['elapsed_seconds']


def test_packet_verifier_replays_bytes_and_rejects_claim_metadata_text_tampering(runner, tmp_path, monkeypatch):
    import sys
    monkeypatch.syspath_prepend(str(SCRIPT.parent))
    sys.modules.pop('verify_packets', None)
    import verify_packets
    manifest, plan, output = setup_inputs(tmp_path)
    row = json.loads(manifest.read_text())
    row['canary_ordinal'] = 1
    manifest.write_text(json.dumps(row) + '\n')
    clock = Clock()
    runner.run(manifest, plan, output, opener=lambda *a, **k: Response(core_payload()),
               clock=clock.now, sleeper=clock.sleep, max_ladder_calls=0)
    before = {p.relative_to(output): p.read_bytes() for p in output.rglob('*') if p.is_file()}
    result = verify_packets.verify(manifest, output, [1])
    assert result['packets'] == result['documents'] == result['raw_responses'] == 1
    assert before == {p.relative_to(output): p.read_bytes() for p in output.rglob('*') if p.is_file()}
    path = next((output / 'packets').glob('*.json'))
    original = path.read_bytes()
    for damage in ('claim', 'metadata', 'text'):
        packet = json.loads(original)
        if damage == 'claim':
            packet['claim_sha256'] = '0' * 64
        elif damage == 'metadata':
            packet['primary'][0]['result']['doi'] = '10.1234/wrong'
        else:
            packet['primary'][0]['result']['documents'][0]['text'] += ' altered'
        path.write_text(json.dumps(packet))
        with pytest.raises(ValueError):
            verify_packets.verify(manifest, output, [1])
    path.write_bytes(original)
    response = next((output / 'cache').glob('*.response'))
    response.write_bytes(b'tampered')
    with pytest.raises(Exception, match='integrity'):
        verify_packets.verify(manifest, output, [1])


def test_relative_input_paths_and_single_unit_match_full_finalization(tmp_path, monkeypatch):
    finalizer = load_helper('finalize_scientific')
    clock = load_helper('review_clock')
    monkeypatch.setattr(finalizer, 'ROOT', tmp_path)
    monkeypatch.chdir(tmp_path)
    rows = [{'canary_ordinal': i, 'occurrence_id': f'urn:fixture:{i}',
             'origin_transform': 'fixture', 'predicate': 'biolink:has_phenotype',
             'object': 'METPO:1000698'} for i in range(1, 51)]
    applicability = [{**row, 'scientific_applicability': 'APPLICABLE' if row['canary_ordinal'] == 1 else 'NOT_APPLICABLE',
                      'applicability_rule': 'fixture', 'applicability_reason': 'Synthetic fixture.'}
                     for row in rows]
    manifest = tmp_path / 'manifest.jsonl'
    manifest.write_text(''.join(json.dumps(row) + '\n' for row in rows))
    applied = tmp_path / 'applicability.jsonl'
    applied.write_text(''.join(json.dumps(row) + '\n' for row in applicability))
    sampling = tmp_path / 'sampling.json'
    sampling.write_text(json.dumps({'private_original_canary': {'sha256': finalizer.sha(manifest.read_bytes())}}))
    pins = tmp_path / 'pins.json'
    pins.write_text(json.dumps({'hashes': {'applicability.jsonl': finalizer.sha(applied.read_bytes())}}))
    args = [Path(p.name) for p in (manifest, applied, sampling, pins)]
    assert finalizer.validate_inputs(*args) == finalizer.validate_inputs(manifest, applied, sampling, pins)
    retrieval, reviews = tmp_path / 'retrieval', tmp_path / 'reviews'
    packets = retrieval / 'packets'
    packets.mkdir(parents=True)
    packet = {'occurrence_id': rows[0]['occurrence_id'],
              'manifest_sha256': finalizer.sha(manifest.read_bytes()),
              'claim_sha256': finalizer.sha(json.dumps(rows[0], sort_keys=True).encode()),
              'applicability': 'APPLICABLE', 'primary': [], 'fallback': [], 'stages': []}
    packet_path = packets / (finalizer.sha(rows[0]['occurrence_id'].encode()) + '.json')
    packet_path.write_text(json.dumps(packet))
    for name, decision in [('1-primary', {'fallback_reason': ''}),
                           ('1', {'verdict': 'NOT_ASSESSABLE', 'rationale': 'Synthetic incomplete evidence.'})]:
        clock.begin_review(reviews, 'scientific', name, packet_path)
        clock.finish_review(reviews, 'scientific', name,
                            {**decision, 'canary_ordinal': 1, 'occurrence_id': rows[0]['occurrence_id']})
    full, single = tmp_path / 'full.jsonl', tmp_path / 'single.jsonl'
    common = (Path(manifest.name), Path(applied.name), retrieval, reviews)
    kwargs = {'sampling_metadata': Path(sampling.name), 'applicability_metadata': Path(pins.name)}
    finalizer.finalize(*common, full, **kwargs)
    finalizer.finalize(*common, single, edge=1, **kwargs)
    assert len(full.read_text().splitlines()) == 50
    assert json.loads(full.read_text().splitlines()[0]) == json.loads(single.read_text())
    assert len(json.loads(single.read_text())['adjudication_timing']['segments']) == 2
    with pytest.raises(ValueError, match='one frozen canary ordinal'):
        finalizer.finalize(*common, single, edge=51, **kwargs)


def test_ontology_resolution_replays_raw_label_and_rejects_wrong_identifier(tmp_path):
    selector = load_helper('select_retrieval')
    term = {'obo_id': 'BTO:0000648', 'label': 'intestine', 'description': ['Synthetic definition.']}
    raw = json.dumps({'_embedded': {'terms': [term]}}).encode()
    digest = hashlib.sha256(raw).hexdigest()
    (tmp_path / (digest + '.response')).write_bytes(raw)
    summary = [{'identifier': 'BTO:0000648', 'response_sha256': digest,
                'label': 'changed label', 'definition': ['changed definition']}]
    summary_path = tmp_path / 'identifier-resolution.json'
    summary_path.write_text(json.dumps(summary))
    result = selector.load_identifier_resolutions(tmp_path)['BTO:0000648']
    assert result['label'] == 'intestine'
    assert result['definition'] == ['Synthetic definition.']
    assert result['binding'] == 'obo_id'
    summary[0]['identifier'] = 'BTO:9999999'
    summary_path.write_text(json.dumps(summary))
    with pytest.raises(ValueError, match='uniquely bound'):
        selector.load_identifier_resolutions(tmp_path)


def test_source_replay_rejects_changed_public_manifest_and_claim(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(SCRIPT.parent))
    source = load_helper('source_adjudicate')
    rows = [{'canary_ordinal': i, 'occurrence_id': f'urn:fixture:{i}',
             'subject': 'NCBITaxon:1', 'predicate': 'biolink:has_phenotype',
             'object': 'METPO:1000698', 'object_label': 'fixture trait'} for i in range(1, 51)]
    path = tmp_path / 'canary.jsonl'
    path.write_text(''.join(json.dumps(row) + '\n' for row in rows))
    (tmp_path / 'sampling-metadata.json').write_text(json.dumps({'hashes': {
        'artifacts/edge-recanary-20261113/canary.jsonl': hashlib.sha256(path.read_bytes()).hexdigest()}}))
    assert source.verify_claim_manifest(tmp_path)[1] == rows[0]
    source.verify_source_claim(rows[0], rows[0])
    for field in ('object', 'object_label', 'subject', 'predicate'):
        with pytest.raises(ValueError, match=field):
            source.verify_source_claim(rows[0], {**rows[0], field: 'altered'})
    path.write_text(path.read_text().replace('fixture trait', 'changed trait', 1))
    with pytest.raises(ValueError, match='pinned sampling hash'):
        source.verify_claim_manifest(tmp_path)


@pytest.mark.parametrize('damage', ['ledger_applicability', 'ledger_rule', 'classifier', 'sidecar'])
def test_report_denominator_rejects_changed_frozen_applicability(tmp_path, monkeypatch, damage):
    import shutil
    report = load_helper('report')
    original_root, original_art = report.ROOT, report.ART
    metadata = json.loads((original_art / 'applicability-metadata.json').read_text())
    for relative in metadata['hashes']:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(original_root / relative, target)
    artifact = tmp_path / original_art.relative_to(original_root)
    shutil.copyfile(original_art / 'applicability-metadata.json', artifact / 'applicability-metadata.json')
    monkeypatch.setattr(report, 'ROOT', tmp_path)
    monkeypatch.setattr(report, 'ART', artifact)
    fresh = report.lines(artifact / 'canary.jsonl')
    science = report.lines(artifact / 'applicability.jsonl')
    assert len(report.validate_applicability(fresh, science)) == 50
    if damage == 'ledger_applicability':
        science[0]['scientific_applicability'] = (
            'APPLICABLE' if science[0]['scientific_applicability'] == 'NOT_APPLICABLE' else 'NOT_APPLICABLE')
    elif damage == 'ledger_rule':
        science[0]['applicability_rule'] = 'altered-rule'
    else:
        path = (tmp_path / 'scripts/adhoc/edge_recanary_20261113/applicability.py'
                if damage == 'classifier' else artifact / 'applicability.jsonl')
        path.write_text(path.read_text() + '\n')
    with pytest.raises(ValueError, match='frozen'):
        report.validate_applicability(fresh, science)


@pytest.fixture
def supplemental_packets(runner, tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(SCRIPT.parent))
    verifier = load_helper('verify_packets')
    manifest, plan, output = setup_inputs(tmp_path)
    row = json.loads(manifest.read_text())
    row.update(canary_ordinal=1, subject='NCBITaxon:1935118', object='BTO:0000648')
    manifest.write_text(json.dumps(row) + '\n')
    clock = Clock()
    runner.run(manifest, plan, output, opener=lambda *a, **k: Response(core_payload()),
               clock=clock.now, sleeper=clock.sleep, max_ladder_calls=0)
    identifiers = tmp_path / 'identifiers'
    identifiers.mkdir()
    payloads = {
        'NCBITaxon:1935118': b'<TaxaSet><Taxon><TaxId>999</TaxId><ScientificName>Fixture organism</ScientificName><AkaTaxIds><TaxId>1935118</TaxId></AkaTaxIds></Taxon></TaxaSet>',
        'BTO:0000648': json.dumps({'_embedded': {'terms': [{
            'obo_id': 'BTO:0000648', 'label': 'intestine', 'description': ['Fixture definition.']}]}}).encode(),
    }
    summary = []
    for identifier, raw in payloads.items():
        digest = hashlib.sha256(raw).hexdigest()
        (identifiers / (digest + '.response')).write_bytes(raw)
        summary.append({'identifier': identifier, 'response_sha256': digest})
    (identifiers / 'identifier-resolution.json').write_text(json.dumps(summary))
    resolutions = verifier.load_identifier_resolutions(identifiers)
    packet_path = next((output / 'packets').glob('*.json'))
    packet = json.loads(packet_path.read_text())
    packet['stages'][0]['targeting_plan'].update(
        name_resolution=resolutions['NCBITaxon:1935118'],
        claim_term_resolution=resolutions['BTO:0000648'])
    packet_path.write_text(json.dumps(packet))
    return verifier, manifest, output, identifiers, packet_path


def test_packet_verifier_replays_separate_identifier_store(supplemental_packets):
    verifier, manifest, output, identifiers, packet_path = supplemental_packets
    with pytest.raises(ValueError, match='explicit identifier store'):
        verifier.verify(manifest, output)
    result = verifier.verify(manifest, output, identifiers=identifiers)
    assert result['packets'] == result['documents'] == result['raw_responses'] == 1
    assert result['identifier_responses'] == 2
    # Habitat/host occurrences can put the organism in the object position.
    row = json.loads(manifest.read_text())
    row['subject'], row['object'] = row['object'], row['subject']
    manifest.write_text(json.dumps(row) + '\n')
    packet = json.loads(packet_path.read_text())
    packet['manifest_sha256'] = hashlib.sha256(manifest.read_bytes()).hexdigest()
    packet['claim_sha256'] = hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest()
    packet_path.write_text(json.dumps(packet))
    assert verifier.verify(manifest, output, identifiers=identifiers)['identifier_responses'] == 2


@pytest.mark.parametrize('damage', ['label', 'hash', 'raw_bytes', 'supplemental_path',
                                    'literature_path', 'identifier_digest'])
def test_packet_verifier_rejects_corrupt_identifier_or_literature_records(supplemental_packets, damage):
    from kg_microbe_curation.identity import CurationError
    verifier, manifest, output, identifiers, packet_path = supplemental_packets
    packet = json.loads(packet_path.read_text())
    supplement = packet['stages'][0]['targeting_plan']['claim_term_resolution']
    if damage == 'label':
        supplement['label'] = 'unrelated term'
    elif damage == 'hash':
        supplement['response_sha256'] = '0' * 64
    elif damage == 'raw_bytes':
        (identifiers / (supplement['response_sha256'] + '.response')).write_bytes(b'tampered')
    elif damage == 'supplemental_path':
        supplement['response_path'] = '../other.response'
    elif damage == 'literature_path':
        packet['primary'][0]['result']['metadata']['response_path'] = '../other.response'
    elif damage == 'identifier_digest':
        summary_path = identifiers / 'identifier-resolution.json'
        summary = json.loads(summary_path.read_text())
        summary[1]['response_sha256'] = '../outside'
        summary_path.write_text(json.dumps(summary))
    packet_path.write_text(json.dumps(packet))
    with pytest.raises((ValueError, CurationError)):
        verifier.verify(manifest, output, identifiers=identifiers)
