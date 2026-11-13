"""2026-11-12 helper 3: replay short-quote decisions against cached retrieval bytes.

Inputs: canary manifest, authored decisions, private retrieval cache. Output: scientific
ledger with exact quote proofs. Serves the edge-sample canary draft PR; fixes #66/#67.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'src'))
from edgemech.literature_cache import LiteratureCache, abstract_text, full_text, verify_quote

MODEL = 'GPT-6 (Codex runtime; variant not exposed)'
VERDICTS = {'SUPPORTED', 'CONTRADICTED', 'NOT_FOUND', 'NOT_ASSESSABLE'}
CITATION_IDENTITY = ('source', 'id', 'doi', 'pmid', 'pmcid')


def bound_metadata(item, packet, cache):
    """Bind either abstract or OA citation identity to original search bytes."""
    matches = []
    for search in packet['searches']:
        response = search['response']
        if response['status'] != 'retrieved':
            continue
        records = json.loads(cache.raw(response))['resultList']['result']
        matches.extend(record for record in records
                       if record.get('source') == item.get('source')
                       and record.get('id') == item.get('id'))
    if not matches:
        raise ValueError('Publication identity absent from retrieved search metadata')
    if any(record.get(key) != item.get(key)
           for record in matches for key in CITATION_IDENTITY):
        raise ValueError('Citation identity mismatch against retrieved search metadata')
    return matches[0]


def finalize(manifest, decisions, retrieval, output):
    manifest_bytes = manifest.read_bytes()
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    receipt = json.loads((retrieval / 'retrieval-receipt.json').read_text())
    if receipt.get('manifest_sha256') != manifest_sha256:
        raise ValueError('Manifest hash differs from retrieval receipt')
    rows = [json.loads(line) for line in manifest_bytes.decode().splitlines()]
    decisions = json.loads(decisions.read_text())
    if not 0 < len(rows) == len(decisions) <= 50:
        raise ValueError('Expected one decision per edge, maximum 50')
    if {r['occurrence_id'] for r in rows} != {d['occurrence_id'] for d in decisions}:
        raise ValueError('Decisions differ from manifest')
    if len({d['occurrence_id'] for d in decisions}) != len(decisions):
        raise ValueError('Duplicate decision')
    results = []
    with LiteratureCache(retrieval / 'cache') as cache:
        for decision in decisions:
            occurrence_id = decision['occurrence_id']
            packet_path = retrieval / 'packets' / (
                hashlib.sha256(occurrence_id.encode()).hexdigest() + '.json')
            packet = json.loads(packet_path.read_text())
            if packet['occurrence_id'] != occurrence_id:
                raise ValueError('Packet identity mismatch')
            if decision['verdict'] not in VERDICTS or not decision['rationale'].strip():
                raise ValueError('Missing verdict/rationale')
            result = {
                **decision, 'adjudicating_model': MODEL, 'evidence': [],
                'manifest_sha256': manifest_sha256,
                'retrieval_seconds': packet['retrieval_seconds'],
                'api_attempts': packet['api_attempts'],
                'queries': [s['query'] for s in packet['searches']],
            }
            if decision['verdict'] == 'NOT_FOUND':
                if not packet['searches'] or any(
                    s['response']['status'] != 'retrieved' for s in packet['searches']
                ):
                    raise ValueError('NOT_FOUND requires completed searches')
                if any(item.get('fulltext_response', {}).get('status', 'retrieved') != 'retrieved'
                       or item.get('fulltext_parse_failure') for item in packet['documents']):
                    raise ValueError('Incomplete fulltext retrieval is NOT_ASSESSABLE')
            if decision['verdict'] in {'SUPPORTED', 'CONTRADICTED'} and not decision.get('citations'):
                raise ValueError('Directional verdict requires verified evidence')
            for citation in decision.get('citations', []):
                item = packet['documents'][citation['paper']]
                metadata = bound_metadata(item, packet, cache)
                doc = item['documents'][citation['document']]
                raw = cache.raw(doc['response'])
                if doc['kind'] == 'abstract':
                    matches = [r for r in json.loads(raw)['resultList']['result']
                               if r.get('source') == item['source'] and r.get('id') == item['id']]
                    if len(matches) != 1:
                        raise ValueError('Ambiguous publication identity')
                    source = matches[0]
                    if any(source.get(key) != metadata.get(key) for key in CITATION_IDENTITY):
                        raise ValueError('Citation identity mismatch')
                    text = abstract_text(source['abstractText'])
                elif doc['kind'] == 'oa_fulltext':
                    text = full_text(raw, metadata['pmcid'])
                else:
                    raise ValueError('Unexpected evidence level')
                rebuilt = cache._document(doc['response'], doc['kind'], text)
                if rebuilt['text_sha256'] != doc['text_sha256']:
                    raise ValueError('Text hash mismatch on replay')
                if not metadata.get('doi') and not metadata.get('pmid'):
                    raise ValueError('Scientific evidence requires DOI/PMID')
                proof = verify_quote(rebuilt, citation['quote'])
                result['evidence'].append({
                    **proof, 'doi': metadata.get('doi'), 'pmid': metadata.get('pmid'),
                    'pmcid': metadata.get('pmcid'), 'url': doc['response']['url'],
                    'title': metadata['title'],
                })
            results.append(result)
    output.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in results))
    print(json.dumps({
        'ledger_rows': len(results),
        'quotes_verified': sum(len(r['evidence']) for r in results),
        'ledger_bytes': output.stat().st_size,
    }))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for name in ('manifest', 'decisions', 'retrieval', 'output'):
        p.add_argument('--' + name, required=True, type=Path)
    a = p.parse_args()
    finalize(a.manifest, a.decisions, a.retrieval, a.output)
