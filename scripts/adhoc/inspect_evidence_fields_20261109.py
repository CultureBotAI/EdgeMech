"""Inspect source-specific citation encodings for the retrieval PR, 2026-11-09.
Input: pinned preparation manifest. Output: bounded samples on stdout; no writes.
"""
import json
from pathlib import Path

import duckdb

root = Path('workspace/content-inventory-full-20261109')
manifest = json.loads((root / 'manifest.json').read_bytes())
with duckdb.connect(config={'memory_limit': '256MB', 'threads': '2'}) as db:
    db.read_parquet([str(root / p['path']) for p in manifest['partitions']]).create_view('rows')
    for source in ('infores:microbedecoder-literature', 'infores:bergey-manual',
                   'infores:prego', 'infores:bacdive'):
        rows = db.execute('SELECT DISTINCT publications,source_citation,source_citation_base64,'
                          'prego_evidence FROM rows WHERE primary_knowledge_source=? '
                          "AND (publications<>'' OR prego_evidence<>'' OR source_citation<>'') "
                          'LIMIT 3', [source]).fetchall()
        print(json.dumps({'source': source, 'samples': rows}, ensure_ascii=False))
