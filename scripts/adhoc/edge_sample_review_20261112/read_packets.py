"""2026-11-12 helper3: inspect persisted canary evidence without changing it."""
import argparse
import hashlib
import json
import os
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('ordinals', nargs='*', type=int)
p.add_argument('--full', action='store_true')
a = p.parse_args()
root = Path(__file__).resolve().parents[3]
data = Path(os.environ["EDGEMECH_DATA_DIR"]) / "literature"
rows = [json.loads(s) for s in (root / 'artifacts/edge-sample-review-20261112/canary.jsonl').read_text().splitlines()]
for row in rows:
    if a.ordinals and row['canary_ordinal'] not in a.ordinals:
        continue
    path = data / 'packets' / (hashlib.sha256(row['occurrence_id'].encode()).hexdigest() + '.json')
    if not path.exists():
        continue
    packet = json.loads(path.read_text())
    print('\nEDGE', row['canary_ordinal'], row['subject_label'], row['predicate'], row['object_label'])
    print('SEARCHES', [(s['query'], s.get('hit_count'), s['response']['status']) for s in packet['searches']])
    for i, paper in enumerate(packet['documents']):
        print('PAPER', i, paper['doi'], paper['pmid'], paper['title'])
        for j, doc in enumerate(paper['documents']):
            print('DOC', j, doc['kind'], 'CHARS', len(doc['text']))
            if doc['kind'] == 'abstract' or a.full:
                print(doc['text'])
