"""2026-11-15, PR76 issues111–113/115: bounded retrieval and retained provenance.

Only synthetic credentials and mocked provider responses are used. Tests exercise
the real transport/run paths and inspect persisted packets, receipts and logs.
"""
import json
import urllib.error
import urllib.parse

import pytest
from test_edge_recanary import Clock, Response, core_payload, setup_inputs
from test_edge_recanary import runner as runner


@pytest.mark.parametrize('url,headers', [
    ('http://api.wiley.com/article', {'Wiley-TDM-Client-Token': 'fixture-token'}),
    ('https://api.wiley.com:8443/article', {'Wiley-TDM-Client-Token': 'fixture-token'}),
    ('https://api.wiley.com:0/article', {'Wiley-TDM-Client-Token': 'fixture-token'}),
    ('https://api.wiley.com.example.test/article', {'Wiley-TDM-Client-Token': 'fixture-token'}),
    ('https://api.wiley.com@other.example.test/article', {'Wiley-TDM-Client-Token': 'fixture-token'}),
    ('https://other.example.test@api.wiley.com/article', {'Wiley-TDM-Client-Token': 'fixture-token'}),
    ('https://api.wiley.com/article', {'X-ELS-APIKey': 'fixture-elsevier'}),
    ('https://other.example.test/article', {'Authorization': 'Bearer fixture-token'}),
    ('http://api.springernature.com/article?api_key=fixture-key', {}),
    ('https://api.springernature.com:8443/article?API%5FKEY=fixture-key', {}),
    ('https://api.springernature.com.example.test/article?apiKey=fixture-key', {}),
    ('https://user@api.springernature.com/article?api_key=fixture-key', {}),
])
def test_credentials_reject_unsafe_initial_origins_before_io(runner, tmp_path, url, headers):
    transport = runner.Transport(tmp_path / 'not-created',
                                 opener=lambda *args, **kwargs: pytest.fail('unsafe request'))
    with pytest.raises(ValueError):
        transport.fetch(url, headers)
    assert transport.events == []
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('destination', [
    'http://api.wiley.com/article',
    'https://api.wiley.com:8443/article',
    'https://download.example.test/article',
])
def test_origin_change_is_anonymous_including_query_credentials(runner, tmp_path, destination):
    root = tmp_path / 'cache'
    root.mkdir()
    requests, clock = [], Clock()
    target = destination + '?API%5FKEY=fixture-key&apiKey=fixture-key&access-token=fixture-token&part=1'

    def opener(request, timeout):
        requests.append(request)
        if len(requests) == 1:
            raise urllib.error.HTTPError(request.full_url, 302, 'fixture redirect',
                                         {'Location': target}, None)
        return Response(b'fixture article')

    transport = runner.Transport(root, opener=opener, clock=clock.now, sleeper=clock.sleep)
    raw, _ = transport.fetch('https://api.wiley.com/article?api_key=fixture-key',
                             {'Wiley-TDM-Client-Token': 'fixture-token'})
    assert raw == b'fixture article'
    assert len(requests) == 2
    assert not any(key.lower() in runner.SENSITIVE_HEADERS for key, _ in requests[1].header_items())
    assert urllib.parse.parse_qsl(urllib.parse.urlsplit(requests[1].full_url).query) == [('part', '1')]
    assert 'fixture-key' not in requests[1].full_url
    assert 'fixture-token' not in requests[1].full_url
    log = (tmp_path / 'http-attempts.jsonl').read_text()
    assert 'fixture-key' not in log and 'fixture-token' not in log


@pytest.mark.parametrize('destination', [
    'https://api.springernature.com/article?API%5FKEY=fixture-key',
    'https://api.springernature.com:443/article?apiKey=fixture-key',
])
def test_same_effective_origin_preserves_authentication(runner, tmp_path, destination):
    root = tmp_path / 'cache'
    root.mkdir()
    requests, clock = [], Clock()

    def opener(request, timeout):
        requests.append(request)
        if len(requests) == 1:
            raise urllib.error.HTTPError(request.full_url, 302, 'fixture redirect',
                                         {'Location': destination}, None)
        return Response(b'fixture article')

    transport = runner.Transport(root, opener=opener, clock=clock.now, sleeper=clock.sleep)
    transport.fetch('https://api.springernature.com/article?api_key=fixture-key',
                    {'Authorization': 'Bearer fixture-token'})
    assert len(requests) == 2
    assert requests[1].get_header('Authorization') == 'Bearer fixture-token'
    assert 'fixture-key' in requests[1].full_url


def test_redirect_userinfo_is_rejected_before_second_request(runner, tmp_path):
    root = tmp_path / 'cache'
    root.mkdir()
    requests, clock = [], Clock()

    def opener(request, timeout):
        requests.append(request)
        raise urllib.error.HTTPError(request.full_url, 302, 'fixture redirect',
                                     {'Location': 'https://user@api.wiley.com/article'}, None)

    transport = runner.Transport(root, opener=opener, clock=clock.now, sleeper=clock.sleep)
    with pytest.raises(ValueError, match='userinfo'):
        transport.fetch('https://api.wiley.com/article', {'Wiley-TDM-Client-Token': 'fixture-token'})
    assert len(requests) == 1


def test_anonymous_binary_redirect_keeps_noncredential_query(runner, tmp_path):
    root = tmp_path / 'cache'
    root.mkdir()
    requests, clock = [], Clock()

    def opener(request, timeout):
        requests.append(request)
        if len(requests) == 1:
            raise urllib.error.HTTPError(request.full_url, 302, 'fixture redirect',
                                         {'Location': 'https://download.example.test/article?download=1'}, None)
        return Response(b'fixture article')

    transport = runner.Transport(root, opener=opener, clock=clock.now, sleeper=clock.sleep)
    transport.fetch('https://api.wiley.com/article', {'Wiley-TDM-Client-Token': 'fixture-token'})
    assert requests[1].full_url == 'https://download.example.test/article?download=1'
    assert not any(key.lower() in runner.SENSITIVE_HEADERS for key, _ in requests[1].header_items())


@pytest.mark.parametrize('stage', ['primary', 'fallback'])
@pytest.mark.parametrize('dry_run', [False, True])
def test_empty_selection_fails_before_output_or_requests(runner, tmp_path, stage, dry_run):
    manifest, plan, output = setup_inputs(tmp_path, count=2)
    with pytest.raises(ValueError, match='nonempty subset'):
        runner.run(manifest, plan, output, stage=stage, edge_ids=[], dry_run=dry_run,
                   opener=lambda *args, **kwargs: pytest.fail('empty selection requested data'))
    assert not output.exists()


def snapshot(root):
    return {path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob('*') if path.is_file()}


def test_primary_rerun_preserves_primary_and_fallback_bytes(runner, tmp_path):
    manifest, plan, output = setup_inputs(tmp_path)
    oid = json.loads(manifest.read_text())['occurrence_id']
    clock, calls = Clock(), []

    def opener(request, timeout):
        calls.append(request.full_url)
        return Response(core_payload())

    runner.run(manifest, plan, output, opener=opener, clock=clock.now,
               sleeper=clock.sleep, max_ladder_calls=0)
    plans = json.loads(plan.read_text())
    plans[0]['fallback_reason'] = 'Synthetic primary assessment needs additional evidence'
    plan.write_text(json.dumps(plans))
    runner.run(manifest, plan, output, stage='fallback', edge_ids=[oid],
               opener=opener, clock=clock.now, sleeper=clock.sleep, max_ladder_calls=0)
    retained = snapshot(output)
    call_count = len(calls)
    packet = json.loads(next((output / 'packets').glob('*.json')).read_text())
    assert [stage['stage'] for stage in packet['stages']] == ['primary', 'fallback']
    assert packet['fallback']
    assert len(list((output / 'receipts').glob('*.json'))) == 2
    with pytest.raises(FileExistsError, match='Primary packet already exists'):
        runner.run(manifest, plan, output, opener=opener, clock=clock.now,
                   sleeper=clock.sleep, max_ladder_calls=0)
    assert len(calls) == call_count
    assert snapshot(output) == retained


def test_later_primary_collision_prevents_all_batch_side_effects(runner, tmp_path):
    manifest, plan, output = setup_inputs(tmp_path, count=2, applicable=False)
    rows = [json.loads(line) for line in manifest.read_text().splitlines()]
    runner.run(manifest, plan, output, edge_ids=[rows[1]['occurrence_id']])
    retained = snapshot(output)
    with pytest.raises(FileExistsError, match='Primary packet already exists'):
        runner.run(manifest, plan, output,
                   opener=lambda *args, **kwargs: pytest.fail('colliding batch requested data'))
    assert snapshot(output) == retained


def test_disjoint_primary_runs_keep_receipts_and_legacy_bytes(runner, tmp_path):
    manifest, plan, output = setup_inputs(tmp_path, count=2, applicable=False)
    rows = [json.loads(line) for line in manifest.read_text().splitlines()]
    output.mkdir()
    legacy = output / 'primary-receipt.json'
    legacy.write_bytes(b'{"historical_receipt": true}\n')
    first = runner.run(manifest, plan, output, edge_ids=[rows[0]['occurrence_id']])
    first_bytes = (output / first['receipt_path']).read_bytes()
    second = runner.run(manifest, plan, output, edge_ids=[rows[1]['occurrence_id']])
    assert first['run_id'] != second['run_id']
    assert (output / first['receipt_path']).read_bytes() == first_bytes
    assert legacy.read_bytes() == b'{"historical_receipt": true}\n'
    assert len(list((output / 'receipts').glob('*.json'))) == 2
    for receipt, row in [(first, rows[0]), (second, rows[1])]:
        persisted = json.loads((output / receipt['receipt_path']).read_text())
        assert persisted == receipt
        assert persisted['selected_occurrence_ids'] == [row['occurrence_id']]
        packet = json.loads((output / 'packets' / (runner.sha(row['occurrence_id'].encode()) + '.json')).read_text())
        assert packet['stages'][0]['run_id'] == receipt['run_id']


@pytest.mark.parametrize('stage', ['primary', 'fallback'])
@pytest.mark.parametrize('child', ['packets', 'receipts', 'cache', 'http-attempts.jsonl', 'packet'])
def test_run_rejects_nested_output_symlinks_before_mutation(runner, tmp_path, stage, child):
    manifest, plan, output = setup_inputs(tmp_path)
    plans = json.loads(plan.read_text())
    plans[0]['fallback_reason'] = 'Synthetic primary assessment needs additional evidence'
    plan.write_text(json.dumps(plans))
    oid = plans[0]['occurrence_id']
    outside = tmp_path / 'outside'
    outside.mkdir()
    retained = outside / 'retained.json'
    retained.write_text('{"retained": true}\n')
    output.mkdir()
    if child == 'packet':
        (output / 'packets').mkdir()
        (output / 'packets' / (runner.sha(oid.encode()) + '.json')).symlink_to(retained)
    else:
        (output / child).symlink_to(retained if child == 'http-attempts.jsonl' else outside)
    before = snapshot(tmp_path)
    with pytest.raises(NotADirectoryError, match='[Ss]ymlink'):
        runner.run(manifest, plan, output, stage=stage, edge_ids=[oid],
                   opener=lambda *args, **kwargs: pytest.fail('unsafe staging requested data'))
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize('child', ['cache', 'http-attempts.jsonl'])
def test_direct_transport_rejects_known_symlinks_before_request(runner, tmp_path, child):
    outside = tmp_path / 'outside'
    outside.mkdir()
    retained = outside / 'retained.json'
    retained.write_bytes(b'fixture retained bytes')
    root = tmp_path / 'cache'
    if child == 'cache':
        root.symlink_to(outside)
    else:
        root.mkdir()
        (tmp_path / child).symlink_to(retained)
    before = snapshot(tmp_path)
    transport = runner.Transport(root, opener=lambda *args, **kwargs: pytest.fail('unsafe request'))
    with pytest.raises(NotADirectoryError, match='[Ss]ymlink'):
        transport.fetch('https://example.test/article')
    assert transport.events == []
    assert snapshot(tmp_path) == before


def test_transport_checks_hashed_response_path_before_read_or_write(runner, tmp_path):
    root = tmp_path / 'cache'
    root.mkdir()
    raw = b'fixture response'
    retained = tmp_path / 'retained.json'
    retained.write_bytes(raw)
    (root / (runner.sha(raw) + '.response')).symlink_to(retained)
    clock = Clock()
    transport = runner.Transport(root, opener=lambda *args, **kwargs: Response(raw),
                                 clock=clock.now, sleeper=clock.sleep)
    with pytest.raises(NotADirectoryError, match='[Ss]ymlink'):
        transport.fetch('https://example.test/article')
    assert retained.read_bytes() == raw
    assert transport.events[0]['status'] == 'NotADirectoryError'


@pytest.mark.parametrize('child', ['packets', 'receipts'])
def test_run_rechecks_packet_and_receipt_paths_at_write_time(runner, tmp_path, child):
    manifest, plan, output = setup_inputs(tmp_path)
    outside = tmp_path / 'outside'
    outside.mkdir()
    clock, calls = Clock(), []

    def opener(request, timeout):
        calls.append(request.full_url)
        (output / child).symlink_to(outside)
        return Response(core_payload())

    with pytest.raises(NotADirectoryError, match='[Ss]ymlink'):
        runner.run(manifest, plan, output, opener=opener, clock=clock.now,
                   sleeper=clock.sleep, max_ladder_calls=0)
    assert len(calls) == 1
    assert list(outside.iterdir()) == []


def test_transport_rechecks_telemetry_path_at_write_time(runner, tmp_path):
    root = tmp_path / 'cache'
    root.mkdir()
    retained = tmp_path / 'retained.json'
    retained.write_bytes(b'fixture retained bytes')
    clock = Clock()

    def opener(request, timeout):
        (tmp_path / 'http-attempts.jsonl').symlink_to(retained)
        return Response(b'fixture response')

    transport = runner.Transport(root, opener=opener, clock=clock.now, sleeper=clock.sleep)
    with pytest.raises(NotADirectoryError, match='[Ss]ymlink'):
        transport.fetch('https://example.test/article')
    assert retained.read_bytes() == b'fixture retained bytes'
