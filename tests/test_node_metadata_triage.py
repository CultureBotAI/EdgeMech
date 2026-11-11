"""Issue36: node/role counts must not inflate affected occurrence coverage."""
import json

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from kg_microbe_curation.identity import CurationError

from edgemech.node_metadata_triage import triage
from edgemech.storage.parquet import file_hash


def fixture(tmp_path):
    row = {'occurrence_id': 'one', 'primary_knowledge_source': 'infores:fixture',
           'subject': 'X:1', 'subject_label': '', 'subject_category': 'biolink:Thing',
           'subject_present_in_nodes': True, 'object': 'X:1', 'object_label': '',
           'object_category': 'biolink:Thing', 'object_present_in_nodes': True}
    path = tmp_path / 'part.parquet'
    pq.write_table(pa.Table.from_pylist([row, {**row, 'occurrence_id': 'two'}]), path)
    manifest = {'partitions': [{'path': path.name, 'bytes': path.stat().st_size,
                                'sha256': file_hash(path)}], 'nodes_sha256': 'a' * 64,
                'profile': [{'incomplete_node_occurrences': 2}]}
    source = tmp_path / 'manifest.json'
    source.write_text(json.dumps(manifest))
    return source


def test_self_loop_counts_nodes_occurrences_and_roles_separately(tmp_path):
    source = fixture(tmp_path)
    output = tmp_path / 'out'
    result = triage(source, file_hash(source), output, all_partitions=True)
    assert result['affected_occurrences'] == 2
    assert result['distinct_incomplete_nodes'] == 1
    assert result['incomplete_endpoint_roles'] == 4
    assert pq.read_table(output / 'nodes.parquet').to_pylist()[0]['affected_occurrences'] == 2
    assert json.loads((output / 'manifest.json').read_text()) == result


def test_rejects_pin_before_publication(tmp_path):
    source = fixture(tmp_path)
    with pytest.raises(CurationError, match='pin'):
        triage(source, '0' * 64, tmp_path / 'out')
    assert not (tmp_path / 'out').exists()


def test_checks_declared_population_count(tmp_path):
    source = fixture(tmp_path)
    manifest = json.loads(source.read_text())
    manifest['profile'][0]['incomplete_node_occurrences'] = 3
    source.write_text(json.dumps(manifest))
    with pytest.raises(CurationError, match='totals'):
        triage(source, file_hash(source), tmp_path / 'out', all_partitions=True)
    assert not (tmp_path / 'out' / 'manifest.json').exists()


def test_node_flush_failure_never_publishes(tmp_path, monkeypatch):
    import edgemech.node_metadata_triage as module
    source = fixture(tmp_path)
    output = tmp_path / 'out'

    def failed_flush(descriptor):
        raise OSError('Injected node flush failure')

    monkeypatch.setattr(module.os, 'fsync', failed_flush)
    with pytest.raises(OSError, match='node flush'):
        triage(source, file_hash(source), output)
    assert (output / 'nodes.parquet').exists()
    assert not (output / 'manifest.json').exists()


def test_persisted_node_corruption_never_publishes(tmp_path, monkeypatch):
    source = fixture(tmp_path)
    original_write = pq.write_table

    def corrupt_write(table, destination, **kwargs):
        original_write(table.slice(0, 0), destination, **kwargs)

    monkeypatch.setattr(pq, 'write_table', corrupt_write)
    with pytest.raises(CurationError, match='Persisted node artifact differs'):
        triage(source, file_hash(source), tmp_path / 'out')
    assert not (tmp_path / 'out' / 'manifest.json').exists()


@pytest.mark.parametrize('damage', ['manifest', 'partition'])
def test_changed_input_after_initial_scan_never_publishes(tmp_path, monkeypatch, damage):
    source = fixture(tmp_path)
    original_write = pq.write_table

    def mutate_input(table, destination, **kwargs):
        original_write(table, destination, **kwargs)
        if damage == 'manifest':
            manifest = json.loads(source.read_text())
            manifest['nodes_sha256'] = 'b' * 64
            source.write_text(json.dumps(manifest))
        else:
            path = tmp_path / 'part.parquet'
            changed = pq.read_table(path).to_pylist()
            changed[0]['primary_knowledge_source'] = 'infores:changed'
            original_write(pa.Table.from_pylist(changed), path)

    monkeypatch.setattr(pq, 'write_table', mutate_input)
    with pytest.raises(CurationError, match='changed during triage|integrity mismatch'):
        triage(source, file_hash(source), tmp_path / 'out')
    assert not (tmp_path / 'out' / 'manifest.json').exists()
