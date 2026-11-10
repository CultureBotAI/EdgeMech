"""Verify retained campaign artifacts after PR38 issues42-49 fixes (2026-11-10).

Inputs: cohort, retrieval, provider cache, adjudication directories.
Output: new JSON validation receipt; no network requests or scientific judgments.
"""
import argparse
import json
from pathlib import Path

from kg_microbe_curation.contract import validate_bundle
from kg_microbe_curation.identity import CurationError

from edgemech.content_inventory import _write_json
from edgemech.evidence_campaign import load_cohort
from edgemech.literature_cache import LiteratureCache, load_retrieval, verify_quote
from edgemech.storage.parquet import file_hash


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('cohort', 'retrieval', 'cache', 'adjudication', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    cohort, rows, queue = load_cohort(args.cohort)
    with LiteratureCache(args.cache) as cache:
        retrieval, documents = load_retrieval(args.retrieval, cache)
        attempts = dict(cache.db.execute('SELECT status,count(*) FROM attempts GROUP BY status').fetchall())
    if retrieval['cohort_sha256'] != file_hash(args.cohort / 'manifest.json'):
        raise CurationError('Retrieval cohort binding mismatch')
    if set(documents) != set(queue):
        raise CurationError('Validation requires complete cohort retrieval coverage')
    receipt = json.loads((args.adjudication / 'manifest.json').read_bytes())
    for name, key in (('bundle.json', 'bundle_sha256'), ('quote-proofs.json', 'quote_proofs_sha256')):
        if file_hash(args.adjudication / name) != receipt[key]:
            raise CurationError('Adjudication artifact hash mismatch')
    bundle = json.loads((args.adjudication / 'bundle.json').read_bytes())
    validate_bundle(bundle, expected_input_sha256=cohort['source']['manifest_sha256'],
                    expected_occurrence_ids=[row['occurrence_id'] for row in rows])
    proofs = json.loads((args.adjudication / 'quote-proofs.json').read_bytes())
    for proof in proofs:
        candidates = [doc for doc in documents[proof['reference']]['documents']
                      if doc['kind'] == proof['kind'] and doc['extractor'] == proof['extractor']]
        if len(candidates) != 1:
            raise CurationError('Missing or ambiguous quote derivative')
        rebuilt = verify_quote(candidates[0], proof['quote'])
        if any(proof[key] != value for key, value in rebuilt.items()):
            raise CurationError('Quote proof differs from retained response')
    result = {'cohort_sha256': file_hash(args.cohort / 'manifest.json'),
              'retrieval_sha256': file_hash(args.retrieval / 'manifest.json'),
              'adjudication': receipt, 'verified_proofs': len(proofs),
              'cache_attempts': attempts, 'retrieval': retrieval}
    _write_json(args.output, result)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
