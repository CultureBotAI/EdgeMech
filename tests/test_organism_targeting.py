"""Regression coverage for organism scope and numeric strain queries, #88/#91."""

import hashlib
import importlib
import json
from pathlib import Path

import pytest

HELPERS = Path(__file__).resolve().parents[1] / 'scripts/adhoc/edge_recanary_20261113'


@pytest.fixture
def targeting(monkeypatch):
    monkeypatch.syspath_prepend(str(HELPERS))
    return importlib.import_module('organism_targeting')


def source(path, record):
    if path.startswith('lpsn/api_cache/'):
        record = {'id': int(Path(path).stem), **record}
    text = json.dumps(record, sort_keys=True, indent=2)
    return {'source_relative_path': path, 'locator': Path(path).stem,
            'retrieval_url': 'https://example.test/source', 'text': text,
            'text_sha256': hashlib.sha256(text.encode()).hexdigest()}


def halotolerans_packet():
    return {'edge': {'occurrence_id': 'fixture:47', 'canary_ordinal': 47,
                     'subject': 'lpsn:783091', 'subject_label': 'Weissella halotolerans',
                     'object': 'METPO:1000600', 'object_label': 'salt'},
            # Reproduce old contaminated output: this field must not be trusted.
            'resolved_names': ['Weissella halotolerans', 'Weissella viridescens',
                               'Lactobacillus viridescens'],
            'records': [
                source('lpsn/api_cache/783091.json', {
                    'full_name': 'Weissella halotolerans', 'basonym_id': 123,
                    'type_strain_names': ['DSM 20190'],
                    'publication_doi': '10.1016/s0723-2020(83)80056-3'}),
                source('lpsn/api_cache/123.json', {
                    'full_name': 'Lactobacillus viridescens subsp. halotolerans',
                    'lpsn_correct_name_id': 783091, 'type_strain_names': ['DSM 20190']}),
                source('lpsn/api_cache/777409.json', {
                    'full_name': 'Lactobacillus viridescens',
                    'lpsn_correct_name_id': 783100,
                    'type_strain_names': ['ATCC 12706'],
                    'publication_doi': '10.1128/jb.73.6.758-759.1957'}),
                source('lpsn/api_cache/783100.json', {
                    'full_name': 'Weissella viridescens', 'basonym_id': 777409,
                    'type_strain_names': ['ATCC 12706', 'BCRC 11650']})]}


def test_subspecies_and_strain_names_never_seed_parent_species(targeting):
    assert targeting.normalized_names('Lactobacillus viridescens subsp. halotolerans') == {
        'Lactobacillus viridescens subsp. halotolerans'}
    assert targeting.normalized_names('GTDB:s__Fixture_species strain 123') == {
        'Fixture species strain 123'}
    assert targeting.normalized_names('Candidatus Fixture species') == {'Candidatus Fixture species'}


def test_public_projection_only_omits_private_annotations(targeting):
    private = {'subject': 'lpsn:1', 'subject_label': 'Fixture bacterium',
               'omitted_source_record': {'value': '0-10'}, 'snippet': 'Old cached text',
               'review_rationale': 'Old inherited review', 'reviewer_worker': 'old-worker',
               'original_subject_node': {'id': 'lpsn:1', 'description': 'Cached description'}}
    public = {'subject': 'lpsn:1', 'subject_label': 'Fixture bacterium',
              'omitted_source_record': {'value': '0-10'}, 'original_subject_node': {'id': 'lpsn:1'}}
    assert targeting.claim_identity(private) == targeting.claim_identity(public)
    public['omitted_source_record']['value'] = '1-10'
    assert targeting.claim_identity(private) != targeting.claim_identity(public)


def test_halotolerans_binds_basonym_but_withholds_broader_species(targeting, tmp_path):
    packet = halotolerans_packet()
    proofs, names = targeting.verified_sources(packet)
    assert set(proofs) == {0, 1}
    assert proofs[1]['parent_record_index'] == 0
    assert set(names) == {'Weissella halotolerans',
                          'Lactobacillus viridescens subsp. halotolerans'}
    directory = tmp_path / 'packets'
    directory.mkdir()
    (directory / '47.json').write_text(json.dumps(packet))
    output = tmp_path / 'targeting.json'
    importlib.import_module('source_adjudicate').targeting(tmp_path, output)
    [row] = json.loads(output.read_text())
    assert row['strain_designations'] == ['DSM 20190']
    assert row['candidate_strain_designations'] == ['ATCC 12706', 'BCRC 11650']
    assert [r['reference'] for r in row['primary_references']] == [
        'doi:10.1016/s0723-2020(83)80056-3']
    [excluded] = row['candidate_primary_references']
    assert excluded['reference'] == 'doi:10.1128/jb.73.6.758-759.1957'
    assert not excluded['identity_verified']
    assert excluded['source_association_verified']


def test_strain_claim_excludes_other_strain_with_same_species(targeting):
    packet = {'edge': {'occurrence_id': 'fixture:strain', 'subject': 'kgmicrobe.strain:bacdive_1',
                       'object': 'METPO:1', 'canary_ordinal': 22}, 'records': []}
    for bid, strain in [(1, 'DSM 1'), (2, 'DSM 2')]:
        packet['records'].append(source('bacdive_strains.json', {
            'General': {'BacDive-ID': bid, 'NCBI tax id': [{'NCBI tax id': 10}]},
            'Name and taxonomic classification': {'species': 'Fixture bacterium',
                                                  'strain designation': strain},
            'External links': {'culture collection no.': strain}}))
    packet['records'].append(source('lpsn/api_cache/9.json', {
        'full_name': 'Fixture bacterium', 'type_strain_names': ['DSM 2'],
        'publication_doi': '10.1234/type-strain-description'}))
    proofs, names = targeting.verified_sources(packet)
    assert set(proofs) == {0}
    assert set(names) == {'Fixture bacterium'}
    result = importlib.import_module('source_adjudicate').packet_targeting(packet)
    assert result['strain_designations'] == ['DSM 1']
    assert result['candidate_strain_designations'] == ['DSM 2']
    assert result['candidate_primary_references'][0]['reference'] == 'doi:10.1234/type-strain-description'


def test_type_strain_is_admitted_only_with_matching_culture_identifier(targeting):
    packet = {'edge': {'occurrence_id': 'fixture:type', 'subject': 'kgmicrobe.strain:bacdive_1',
                       'object': 'METPO:1'}, 'records': [
        source('bacdive_strains.json', {
            'General': {'BacDive-ID': 1},
            'Name and taxonomic classification': {'species': 'Fixture bacterium'},
            'External links': {'culture collection no.': 'DSM 1'}}),
        source('lpsn/api_cache/9.json', {'full_name': 'Fixture bacterium',
                                       'type_strain_names': ['DSM 1', 'ATCC 111']})]}
    assert set(targeting.verified_sources(packet)[0]) == {0, 1}


@pytest.mark.parametrize('damage', ['missing', 'wrong', 'locator'])
def test_lpsn_id_is_bound_inside_retained_bytes(targeting, damage):
    packet = halotolerans_packet()
    wrapper = packet['records'][0]
    record = json.loads(wrapper['text'])
    if damage == 'missing':
        record.pop('id')
    elif damage == 'wrong':
        record['id'] = 777409
    else:
        wrapper['locator'] = '777409'
    wrapper['text'] = json.dumps(record)
    wrapper['text_sha256'] = hashlib.sha256(wrapper['text'].encode()).hexdigest()
    with pytest.raises(ValueError, match='LPSN record ID'):
        targeting.verified_sources(packet)


@pytest.mark.parametrize(('name', 'strains', 'expected'), [
    ('Eikenella corrodens', ['195-83; 207-76,26-73', '333/54-55', '195-83'],
     '("Eikenella corrodens") AND ("195-83" OR "207-76" OR "26-73" OR "333/54-55")'),
    ('Serratia marcescens', ['296;5751;37; ATCC 13880', 'atcc 13880'],
     '("Serratia marcescens") AND ("296" OR "5751" OR "37" OR "ATCC 13880")'),
])
def test_numeric_aliases_are_deduplicated_and_organism_anchored(targeting, name, strains, expected):
    assert targeting.strain_query([name], strains) == expected


def test_no_unanchored_query_or_raw_query_injection(targeting):
    with pytest.raises(ValueError, match='organism-name anchor'):
        targeting.strain_query([], ['296', 'ATCC 13880'])
    with pytest.raises(ValueError, match='Unsafe strain'):
        targeting.strain_query(['Serratia marcescens'], ['296" OR TITLE:clinical'])
    for name in ['296', 'Serratia marcescens\\', 'Serratia\nmarcescens']:
        with pytest.raises(ValueError, match='Invalid organism'):
            targeting.strain_query([name], ['296'])


def test_source_binding_checks_raw_text_hash(targeting):
    packet = halotolerans_packet()
    packet['records'][0]['text'] += ' '
    with pytest.raises(ValueError, match='hash mismatch'):
        targeting.verified_sources(packet)


def test_fallback_selector_anchors_saved_numeric_alias_lists(targeting, tmp_path, monkeypatch):
    selector = importlib.import_module('select_retrieval')
    decisions = tmp_path / 'reviews/decisions/scientific'
    decisions.mkdir(parents=True)
    rows = []
    for ordinal, name, strains in [(22, 'Eikenella corrodens', ['195-83;207-76;26-73;333/54-55']),
                                   (24, 'Serratia marcescens', ['296;5751;37;ATCC 13880'])]:
        row = {'canary_ordinal': ordinal, 'occurrence_id': f'fixture:{ordinal}',
               'applicability': 'APPLICABLE', 'targeting_identity_policy': targeting.POLICY,
               'resolved_names': [name], 'strain_designations': strains,
               'claim_search_terms': '(growth)', 'general_queries': []}
        rows.append(row)
        (decisions / f'{ordinal}-primary.json').write_text(json.dumps({
            'occurrence_id': row['occurrence_id'], 'fallback_reason': 'Primary evidence incomplete'}))
    plan = tmp_path / 'plan.json'
    plan.write_text(json.dumps(rows))
    monkeypatch.setattr('sys.argv', ['select_retrieval', '--plan', str(plan), '--output',
                                    str(tmp_path / 'selection'), '--reviews', str(tmp_path / 'reviews')])
    selector.main()
    selected = json.loads((tmp_path / 'selection/fallback-plan.json').read_text())
    for row in selected:
        assert all(query.startswith(targeting.name_query(row['resolved_names']) + ' AND ')
                   for query in row['general_queries'])
        assert row['general_queries'][1] == targeting.strain_query(
            row['resolved_names'], row['strain_designations'])
