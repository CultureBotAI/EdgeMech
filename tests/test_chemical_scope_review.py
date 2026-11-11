"""Chemical-scope revisions must not change identity or manufacture exact support."""
import json
from copy import deepcopy
from pathlib import Path

import pytest
from kg_microbe_curation.identity import CurationError

import edgemech.chemical_scope_review as module
from edgemech.storage.parquet import file_hash


@pytest.fixture
def review(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path('cohort').mkdir()
    Path('cohort/manifest.json').write_text('{}')
    Path('policy.md').write_text('Finite chemical concern; no exact identity approval.')
    row = {'occurrence_id': 'one', 'row_number': 1, 'row_sha256': 'a' * 64,
           'references': {'doi:10.1234/original': []},
           'fields': {'predicate': 'biolink:produces', 'object': 'CHEBI:26806',
                      'subject': 'taxon:one', 'source_column': 'products', 'source_record': 'record1',
                      'value': 'succinate', 'value_encoding': 'backslash'},
           'labels': {'object_label': 'succinate'}}
    monkeypatch.setattr(module, 'load_cohort', lambda path: ({}, [row], {}))
    note = {'occurrence_id': 'one', 'outcome': 'unknown', 'dimensions': {'taxon': 'Original strain'},
            'quotes': [{'reference': 'doi:10.1234/original', 'kind': 'abstract',
                        'quote': 'Succinic acid was produced.', 'support': 'context_only'}]}
    parent = {'cohort_sha256': file_hash(Path('cohort/manifest.json')),
              'assessments': [note, {**deepcopy(note), 'occurrence_id': 'unchanged'}]}
    Path('parent.json').write_text(json.dumps(parent))
    update = {'occurrence_id': 'one', 'row_number': 1, 'mapped_object': 'CHEBI:26806',
              'row_sha256': 'a' * 64, 'subject': 'taxon:one', 'predicate': 'biolink:produces',
              'source_column': 'products', 'source_record': 'record1',
              'reference': 'doi:10.1234/original', 'identity_authorized': False,
              'source_value': 'succinate', 'value_encoding': 'backslash',
              'outcome': 'concern', 'support': 'partial',
              'family_production': 'supported', 'exact_chemical_scope': 'not_established',
              **{key: 'Explicit reviewer scope.' for key in
                 ('rationale', 'predicate_reason', 'object_reason', 'context', 'evidence_scope')}}
    config = {'format': 'edgemech-chemical-scope-review/v1',
              'policy': {'path': 'policy.md', 'sha256': file_hash(Path('policy.md')),
                         'identity_authorized': False},
              'revisions': [update]}
    return parent, config


def run(config, canary=False):
    Path('revisions.json').write_text(json.dumps(config))
    return module.build_annotations(Path('parent.json'), file_hash(Path('parent.json')),
                                    Path('revisions.json'), Path('cohort'), Path('notes.json'), canary)


@pytest.mark.parametrize('canary', [False, True])
def test_finite_revision_preserves_source_citation_and_other_assessments(review, canary):
    parent, config = review
    run(config, canary)
    result = json.loads(Path('notes.json').read_text())
    assert result['assessments'][0]['outcome'] == 'concern'
    quote = result['assessments'][0]['quotes'][0]
    assert quote['reference'] == 'doi:10.1234/original'
    assert quote['quote'] == 'Succinic acid was produced.'
    assert quote['support'] == 'partial'
    assert len(result['interpretation_inputs']) == 3
    if canary:
        assert len(result['assessments']) == 1
    else:
        assert result['assessments'][1] == parent['assessments'][1]
    assert json.loads(Path('parent.json').read_text()) == parent


@pytest.mark.parametrize('field,value', [
    ('mapped_object', 'CHEBI:30031'), ('occurrence_id', 'unknown'), ('row_number', 2),
    ('source_value', 'succinic acid'), ('outcome', 'supported'), ('support', 'supports'),
    ('exact_chemical_scope', 'established'), ('context', ''),
    ('identity_authorized', True), ('row_sha256', 'b' * 64), ('subject', 'taxon:other'),
    ('source_column', 'supplied_medium'), ('source_record', 'record2'),
    ('reference', 'doi:10.1234/supplemental'),
])
def test_rejects_identity_drift_and_exact_approval_even_in_canary(review, field, value):
    config = review[1]
    config['revisions'][0][field] = value
    with pytest.raises(CurationError):
        run(config, canary=True)
    assert not Path('notes.json').exists()


def test_policy_edit_requires_new_pin(review):
    Path('policy.md').write_text('Different interpretation.')
    with pytest.raises(CurationError, match='policy pin'):
        run(review[1])
    assert not Path('notes.json').exists()


def test_revisions_changed_after_parse_cannot_be_pinned_as_consumed(review, monkeypatch):
    load = module.load_cohort

    def mutate(path):
        Path('revisions.json').write_text('{"different": "revision bytes"}')
        return load(path)

    monkeypatch.setattr(module, 'load_cohort', mutate)
    with pytest.raises(CurationError, match='input changed'):
        run(review[1])
    assert not Path('notes.json').exists()


@pytest.mark.parametrize('field,value', [('value', 'succinic acid'), ('value_encoding', 'plain')])
def test_raw_source_value_is_checked_independently_of_derived_label(review, monkeypatch, field, value):
    load = module.load_cohort

    def altered_source(path):
        manifest, rows, queue = load(path)
        rows[0]['fields'][field] = value
        assert rows[0]['labels']['object_label'] == 'succinate'
        return manifest, rows, queue

    monkeypatch.setattr(module, 'load_cohort', altered_source)
    with pytest.raises(CurationError, match='exact source assertion'):
        run(review[1])
    assert not Path('notes.json').exists()
