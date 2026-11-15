"""2026-11-12: show literal evidence contexts to support manual canary review."""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('ordinal', type=int)
p.add_argument('pattern')
p.add_argument('--width', type=int, default=500)
a = p.parse_args()
root = Path(__file__).resolve().parents[3]
rows = [json.loads(s) for s in (root / 'artifacts/edge-sample-review-20261112/canary.jsonl').read_text().splitlines()]
row = next(r for r in rows if r['canary_ordinal'] == a.ordinal)
path = Path(os.environ["EDGEMECH_DATA_DIR"]) / "literature" / "packets" / (hashlib.sha256(row['occurrence_id'].encode()).hexdigest() + '.json')
packet = json.loads(path.read_text())
for i, paper in enumerate(packet['documents']):
    for j, doc in enumerate(paper['documents']):
        for match in re.finditer(a.pattern, doc['text'], re.I):
            print('PAPER', i, 'DOC', j, paper['doi'], doc['kind'], 'OFFSET', match.start())
            print(doc['text'][max(0, match.start()-a.width):match.end()+a.width])
