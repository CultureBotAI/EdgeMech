"""Read-only cache status for the evidence campaign PR (2026-11-09).
Input: cache directory. Output: request/status/byte counters; no network traffic.
"""
import argparse
import json
import sqlite3
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('cache', type=Path)
args = parser.parse_args()
with sqlite3.connect((args.cache / 'cache.sqlite').resolve().as_uri() + '?mode=ro', uri=True) as db:
    attempts = db.execute('SELECT status,count(*) FROM attempts GROUP BY status').fetchall()
    entries = db.execute('SELECT key,record FROM cache ORDER BY key').fetchall()
print(json.dumps({'attempts': dict(attempts), 'cached_keys': len(entries),
                  'response_bytes': sum(p.stat().st_size for p in args.cache.glob('*.response')),
                  'states': {key: json.loads(value)['status'] for key, value in entries}}, indent=2))
