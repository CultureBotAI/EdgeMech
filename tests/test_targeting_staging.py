"""2026-11-15, #114: raw targeting writers must preflight private output paths."""

import hashlib
import importlib
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

HELPERS = Path(__file__).resolve().parents[1] / 'scripts/adhoc/edge_recanary_20261113'


@pytest.fixture
def pipeline(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(HELPERS))
    source = importlib.import_module('source_adjudicate')
    builder = importlib.import_module('build_targeting')
    selector = importlib.import_module('select_retrieval')
    repo = tmp_path / 'publication-repo'
    repo.mkdir()
    subprocess.run(['git', 'init', '-q', str(repo)], check=True)
    (repo / '.gitignore').write_text('.temp/\n')
    (repo / '.temp').mkdir()
    row = next(row for row in builder.lines(builder.ART / 'canary.jsonl')
               if row['canary_ordinal'] == 22)
    row['snippet'] = 'Synthetic private source annotation; must remain in the sidecar.'
    record = {
        'General': {'BacDive-ID': 161115},
        'Name and taxonomic classification': {'species': 'Eikenella corrodens'},
        'External links': {'culture collection no.': 'JCM 10962'},
        'private_fixture_marker': 'Unprojected source bytes',
    }
    text = json.dumps(record, sort_keys=True)
    packet = {'edge': row, 'records': [{
        'source_relative_path': 'bacdive_strains.json', 'locator': '161115',
        'source_path': '/private/synthetic-machine/raw/bacdive_strains.json',
        'retrieval_url': 'https://example.invalid/strain/161115',
        'text': text, 'text_sha256': hashlib.sha256(text.encode()).hexdigest(),
    }]}
    sources = tmp_path / 'source-packets'
    (sources / 'packets').mkdir(parents=True)
    (sources / 'packets/22.json').write_text(json.dumps(packet))
    enrichment = tmp_path / 'seed-enrichment.json'
    source.targeting(sources, enrichment, ordinal=22)
    plan = tmp_path / 'seed-plan.json'
    builder.build(enrichment, plan, ordinal=22)
    reviews = tmp_path / 'reviews'
    decisions = reviews / 'decisions/scientific'
    decisions.mkdir(parents=True)
    (decisions / '22-primary.json').write_text(json.dumps({
        'occurrence_id': row['occurrence_id'],
        'fallback_reason': 'Synthetic primary evidence requires a fallback.',
    }))
    return SimpleNamespace(repo=repo, source=source, builder=builder, selector=selector,
                           sources=sources, enrichment=enrichment, plan=plan,
                           reviews=reviews, packet=packet)


def invoke(pipeline, writer, destination, monkeypatch):
    if writer == 'enrichment':
        pipeline.source.targeting(pipeline.sources, destination, ordinal=22)
    elif writer == 'primary':
        pipeline.builder.build(pipeline.enrichment, destination, ordinal=22)
    else:
        monkeypatch.setattr('sys.argv', ['select_retrieval', '--plan', str(pipeline.plan),
                            '--output', str(destination), '--reviews', str(pipeline.reviews)])
        pipeline.selector.main()


def output_paths(writer, destination):
    if writer == 'enrichment':
        return [destination], destination
    if writer == 'primary':
        sources = destination.with_suffix('.sources.json')
        return [destination, destination.with_suffix('.manifest.jsonl'), sources,
                destination.with_name(destination.stem + '-receipt.json')], sources
    sources = destination / 'fallback-plan.sources.json'
    return [destination / 'fallback-ids.json', destination / 'fallback-plan.json', sources], sources


@pytest.mark.parametrize('writer', ['enrichment', 'primary', 'fallback'])
@pytest.mark.parametrize('unsafe', ['public', 'tracked', 'file_symlink', 'parent_symlink',
                                   'parent_escape', 'visible_staging'])
def test_writers_reject_unsafe_paths_before_any_output(
        pipeline, tmp_path, monkeypatch, writer, unsafe):
    parent = pipeline.repo / ('.temp' if unsafe != 'public' else 'artifacts') / 'candidate'
    if unsafe == 'parent_escape':
        parent = pipeline.repo / '.temp' / '..' / 'artifacts' / 'candidate'
    if unsafe == 'visible_staging':
        (pipeline.repo / '.gitignore').write_text('')
    if unsafe == 'parent_symlink':
        external = tmp_path / 'external'
        external.mkdir()
        parent.symlink_to(external, target_is_directory=True)
    else:
        parent.mkdir(parents=True)
    destination = parent / ('selection' if writer == 'fallback' else 'output.json')
    outputs, raw_destination = output_paths(writer, destination)
    raw_destination.parent.mkdir(parents=True, exist_ok=True)
    if unsafe == 'tracked':
        raw_destination.write_text('Synthetic tracked file')
        subprocess.run(['git', '-C', str(pipeline.repo), 'add', '-f', '--',
                        str(raw_destination.relative_to(pipeline.repo))], check=True)
        # Existing-file refusal alone cannot detect an absent but tracked path.
        raw_destination.unlink()
    if unsafe == 'file_symlink':
        raw_destination.symlink_to(tmp_path / 'escaped-source.json')

    with pytest.raises(ValueError, match='Private targeting output'):
        invoke(pipeline, writer, destination, monkeypatch)

    assert all(not path.exists() for path in outputs)
    assert not (tmp_path / 'escaped-source.json').exists()
    if unsafe == 'file_symlink':
        assert raw_destination.is_symlink()


def test_ignored_enrichment_primary_and_fallback_keep_complete_source_sidecars(
        pipeline, monkeypatch):
    private = pipeline.repo / '.temp'
    enrichment = private / 'enrichment.json'
    pipeline.source.targeting(pipeline.sources, enrichment, ordinal=22)
    [enriched] = json.loads(enrichment.read_text())
    assert enriched['source_packet'] == pipeline.packet

    plan = private / 'plan.json'
    pipeline.builder.build(enrichment, plan, ordinal=22)
    sidecar = plan.with_suffix('.sources.json')
    expected = {pipeline.packet['edge']['occurrence_id']: pipeline.packet}
    assert json.loads(sidecar.read_text()) == expected

    monkeypatch.setattr('sys.argv', ['select_retrieval', '--plan', str(plan),
                        '--output', str(private / 'fallback'),
                        '--reviews', str(pipeline.reviews)])
    pipeline.selector.main()
    fallback = private / 'fallback/fallback-plan.json'
    assert fallback.with_suffix('.sources.json').read_bytes() == sidecar.read_bytes()
    importlib.import_module('retrieve_targeted').load_inputs(
        plan.with_suffix('.manifest.jsonl'), fallback)
