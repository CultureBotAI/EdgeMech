"""Issues #52/#53: follow-up notes bind every revision and preserve per-row evidence scope."""
import json
import subprocess
import sys
from pathlib import Path

import pytest
from test_pilot_builder import pilot as pilot

BUILDER = (Path(__file__).resolve().parents[1] / 'scripts' / 'adhoc' /
           'build_scientific_followup_20261110.py')


def revision(number=1):
    return {'row_number': number, 'outcome': 'supported', 'capture_id': 'fixture-source',
            'quote': 'Direct full-text process.', 'support': 'supports',
            'rationale': 'Direct full-text process evidence.',
            'predicate_reason': 'Explicit process wording.', 'object_reason': 'Exact process label.',
            'context': 'Full-text methods describe isolate-specific culture conditions.',
            'evidence_scope': 'Primary full-text tool capture; exact literal phrase with OCR limitations.'}


def invoke(pilot, updates, *, canary=False):
    root, notes, _ = pilot
    (root / 'parent.json').write_text(json.dumps(notes))
    (root / 'captures.json').write_text('{"synthetic": true}')
    (root / 'revisions.json').write_text(json.dumps({
        'parent_judgments': 'parent.json', 'capture_manifest': 'captures.json', 'revisions': updates}))
    return subprocess.run([
        sys.executable, '-O', str(BUILDER), '--revisions', 'revisions.json',
        '--cohort', 'cohort', '--retrieval', 'retrieval', '--output', 'notes.json',
        *(['--canary'] if canary else []),
    ], cwd=root, capture_output=True, text=True, timeout=30)


def test_revised_row_uses_explicit_fulltext_context_and_scope(pilot):
    update = revision()
    result = invoke(pilot, [update])
    assert result.returncode == 0, result.stderr
    assessment = json.loads((pilot[0] / 'notes.json').read_text())['assessments'][0]
    assert assessment['dimensions']['context'] == update['context']
    assert assessment['dimensions']['evidence_scope'] == update['evidence_scope']
    assert assessment['quotes'][0]['capture_id'] == 'fixture-source'


def test_unchanged_row_retains_abstract_context_without_claiming_new_audit(pilot):
    result = invoke(pilot, [])
    assert result.returncode == 0, result.stderr
    assessment = json.loads((pilot[0] / 'notes.json').read_text())['assessments'][0]
    assert assessment['dimensions']['context'] == pilot[1]['papers']['one']['context']
    assert 'abstract assessment retained' in assessment['dimensions']['evidence_scope']
    assert 'No new full-text or chemical-mapping assessment' in assessment['dimensions']['evidence_scope']
    assert assessment['quotes'][0]['kind'] == 'abstract'


@pytest.mark.parametrize('canary', [False, True])
def test_unknown_revision_rejected_before_any_output_even_for_canary(pilot, canary):
    result = invoke(pilot, [revision(999)], canary=canary)
    assert result.returncode != 0
    assert 'Unknown follow-up revision rows: [999]' in result.stderr
    assert not (pilot[0] / 'notes.json').exists()


@pytest.mark.parametrize('field', ['context', 'evidence_scope'])
def test_revision_cannot_fall_back_to_stale_context_or_generic_scope(pilot, field):
    update = revision()
    del update[field]
    result = invoke(pilot, [update])
    assert result.returncode != 0
    assert f'Follow-up revision requires explicit {field}' in result.stderr
    assert not (pilot[0] / 'notes.json').exists()
