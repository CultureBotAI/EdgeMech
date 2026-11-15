"""Timed scientific packet reading and durable decisions for PR76, 2026-11-13.

Inputs: frozen cohort and private retrieval packets; output: immutable review
snapshots, separately authored decisions, wall-clock receipts. No verdict is inferred.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from review_clock import begin_review, finish_review

ROOT = Path(__file__).resolve().parents[3]


def select(args):
    rows = [json.loads(s) for s in (ROOT / 'artifacts/edge-recanary-20261113/canary.jsonl').read_text().splitlines()]
    row = next(r for r in rows if r['canary_ordinal'] == args.edge)
    identity = str(args.edge) + ('-primary' if args.stage == 'primary' else '')
    snapshot = args.root / 'snapshots/scientific' / (identity + '.json')
    return row, identity, snapshot


def display(packet, *, needle=None):
    counts = {'primary': 0, 'fallback': 0}
    for item in packet['primary']:
        stage = item['retrieval_stage']
        index = counts[stage]
        counts[stage] += 1
        result = item['result']
        print(json.dumps({'stage': stage, 'paper': index, 'reference': item['reference'],
                          'title': result.get('title'), 'status': result.get('status'),
                          'ladder_attempts': result.get('ladder_attempts', [])}))
        for doc_index, doc in enumerate(result['documents']):
            text = doc['text']
            print(json.dumps({'document': doc_index, 'kind': doc['kind'], 'characters': len(text)}))
            if needle:
                matches = list(re.finditer(needle, text, re.IGNORECASE))
                for match in matches[:18]:
                    print(json.dumps({'offset': match.start(), 'excerpt': text[max(0, match.start()-250):match.end()+650]}))
                print(json.dumps({'matches': len(matches)}))
            elif doc['kind'] == 'abstract':
                print(text)
    print(json.dumps({'fallback_searches': [{'query': s['query'], 'hits': s.get('hit_count'),
                                              'status': s['response']['status']} for s in packet.get('fallback', [])]}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['begin', 'excerpts', 'finish'])
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--retrieval', required=True, type=Path)
    parser.add_argument('--edge', required=True, type=int)
    parser.add_argument('--stage', choices=['primary', 'final'], default='final')
    parser.add_argument('--needle')
    parser.add_argument('--decision-json')
    args = parser.parse_args()
    row, identity, snapshot = select(args)
    if args.action == 'begin':
        path = args.retrieval / 'packets' / (hashlib.sha256(row['occurrence_id'].encode()).hexdigest() + '.json')
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        with snapshot.open('xb') as handle:
            handle.write(path.read_bytes())
        result = begin_review(args.root, 'scientific', identity, snapshot)
        print(json.dumps({k: row.get(k) for k in ['canary_ordinal', 'occurrence_id', 'origin_transform',
                                                  'subject', 'predicate', 'object', 'subject_label',
                                                  'predicate_label', 'object_label']}))
        display(result['packet'], needle=args.needle)
    elif args.action == 'excerpts':
        display(json.loads(snapshot.read_text()), needle=args.needle)
    else:
        if not args.decision_json:
            parser.error('--decision-json required for finish')
        decision = json.loads(args.decision_json)
        decision.update(canary_ordinal=args.edge, occurrence_id=row['occurrence_id'],
                        adjudicating_model='GPT-6 in Codex; runtime variant not exposed')
        print(json.dumps(finish_review(args.root, 'scientific', identity, decision)))


if __name__ == '__main__':
    main()
