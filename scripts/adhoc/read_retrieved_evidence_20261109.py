"""Verify and inspect cached texts before manual adjudication, 2026-11-09.
Inputs: retrieval directory/cache. Output: selected document text on stdout.
Serves the literature-campaign PR; does not assign scientific judgments.
"""
import argparse
from pathlib import Path

from edgemech.literature_cache import LiteratureCache, load_retrieval

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('retrieval', type=Path)
parser.add_argument('cache', type=Path)
parser.add_argument('--reference')
args = parser.parse_args()
with LiteratureCache(args.cache) as cache:
    manifest, documents = load_retrieval(args.retrieval, cache)
    for key, entry in documents.items():
        if args.reference and args.reference != key:
            continue
        print(key, entry['status'], entry.get('title'))
        for doc in entry['documents']:
            print(doc['kind'], doc['text'][:16000])
