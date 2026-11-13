"""Helper 3, 2026-11-12: bounded anonymous retrieval for the edge canary draft PR.
Inputs: <=50 manifest rows and an explicit query plan. Outputs: durable cache,
per-edge retrieval packets and telemetry outside Git. Never assigns a verdict.
"""
import argparse
import hashlib
import json
import os
import sys
import time
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'src'))
from edgemech.literature_cache import BASE, LiteratureCache, abstract_text, full_text


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w') as handle:
        json.dump(obj, handle, indent=2, ensure_ascii=False)
        handle.write('\n')
        handle.flush()
        os.fsync(handle.fileno())


def retrieve(manifest, plan, output, dry_run=False):
    rows = [json.loads(line) for line in manifest.read_text().splitlines()]
    plans = json.loads(plan.read_text())
    ids = {row['occurrence_id'] for row in rows}
    if not 0 < len(ids) == len(rows) <= 50:
        raise ValueError("Hard per-batch bound: 1 to 50 unique edges")
    if {p["occurrence_id"] for p in plans} != ids or len(plans) != len(rows):
        raise ValueError("Plan must contain each manifest occurrence exactly once")
    if dry_run:
        print(json.dumps({'edges': len(rows), 'distinct_queries': len({q for p in plans for q in p['queries']}),
                          'max_fulltext_per_query': 2, 'concurrent_requests': 1}))
        return
    output.mkdir(parents=True, exist_ok=True)
    start = time.time()
    with LiteratureCache(output / 'cache') as cache:
        initial = cache.db.execute('SELECT COUNT(*) FROM attempts').fetchone()[0]
        for number, plan_row in enumerate(plans, 1):
            t0 = time.time()
            before = cache.db.execute('SELECT COUNT(*) FROM attempts').fetchone()[0]
            packet = {'occurrence_id': plan_row['occurrence_id'], 'plan': plan_row,
                      'searches': [], 'documents': []}
            seen = set()
            for query in plan_row['queries']:
                url = BASE + 'search?' + urllib.parse.urlencode({
                    'query': query, 'resultType': 'core', 'format': 'json', 'pageSize': '5'})
                response = cache.request('canary-query:' + query, url)
                search = {'query': query, 'response': response}
                packet['searches'].append(search)
                if response['status'] != 'retrieved':
                    continue
                payload = json.loads(cache.raw(response))
                search['hit_count'] = payload.get('hitCount')
                full_count = 0
                for record in payload.get('resultList', {}).get('result', []):
                    identity = (record.get('source'), record.get('id'))
                    if identity in seen:
                        continue
                    seen.add(identity)
                    item = {k: record.get(k) for k in ('title', 'doi', 'pmid', 'pmcid', 'id', 'source')}
                    item['documents'] = []
                    if record.get('abstractText'):
                        item['documents'].append(cache._document(response, 'abstract', abstract_text(record['abstractText'])))
                    if record.get('isOpenAccess') == 'Y' and record.get('pmcid') and full_count < 2:
                        full_count += 1
                        pmcid = record['pmcid']
                        full = cache.request('full:' + pmcid, BASE + pmcid + '/fullTextXML')
                        item['fulltext_response'] = full
                        if full['status'] == 'retrieved':
                            try:
                                text = full_text(cache.raw(full), pmcid)
                                item['documents'].append(cache._document(full, 'oa_fulltext', text))
                            except Exception as error:
                                item['fulltext_parse_failure'] = type(error).__name__
                    packet['documents'].append(item)
            packet['retrieval_seconds'] = time.time() - t0
            packet['api_attempts'] = cache.db.execute('SELECT COUNT(*) FROM attempts').fetchone()[0] - before
            write(output / 'packets' / (hashlib.sha256(plan_row["occurrence_id"].encode()).hexdigest() + '.json'), packet)
            print(json.dumps({'edge': number, 'documents': len(packet['documents']),
                              'seconds': round(packet['retrieval_seconds'], 2), 'attempts': packet['api_attempts']}), flush=True)
        statuses = dict(cache.db.execute('SELECT status,COUNT(*) FROM attempts GROUP BY status').fetchall())
        receipt = {'edges_persisted': len(plans), 'wall_seconds': time.time() - start,
                   'new_api_attempts': cache.db.execute('SELECT COUNT(*) FROM attempts').fetchone()[0] - initial,
                   'all_attempt_status_counts': statuses, 'service': 'Europe PMC',
                   'manifest_sha256': hashlib.sha256(manifest.read_bytes()).hexdigest(),
                   'plan_sha256': hashlib.sha256(plan.read_bytes()).hexdigest()}
        write(output / 'retrieval-receipt.json', receipt)
        print(json.dumps(receipt), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    retrieve(args.manifest, args.plan, args.output, args.dry_run)
