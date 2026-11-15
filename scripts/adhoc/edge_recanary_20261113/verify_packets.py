"""2026-11-13, PR76: replay one or more persisted canary packets without requests.

Inputs: original frozen manifest and private retrieval directory. Output: JSON
counts on stdout; any raw-byte, claim, metadata or derivative mismatch fails.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from retrieve_targeted import (
    LiteratureCache,
    canonical_reference,
    matching_record,
    replay_document,
    sha,
)
from select_retrieval import load_identifier_resolutions


class ReadOnlyCache:
    """Use only pure byte-reading/extraction methods; never open the cache DB."""
    raw = LiteratureCache.raw
    _document = staticmethod(LiteratureCache._document)

    def __init__(self, root):
        self.root = root


def verify(manifest, retrieval, edges=None, identifiers=None):
    raw_manifest = manifest.read_bytes()
    rows = [json.loads(line) for line in raw_manifest.decode().splitlines()]
    if not 0 < len(rows) <= 50 or len({r['occurrence_id'] for r in rows}) != len(rows):
        raise ValueError('Manifest must contain one to fifty unique occurrences')
    if edges is not None:
        selected = set(edges)
        if not selected or not selected <= {r['canary_ordinal'] for r in rows}:
            raise ValueError('Selected ordinals are outside the frozen manifest')
        rows = [r for r in rows if r['canary_ordinal'] in selected]
    client = ReadOnlyCache(retrieval / 'cache')
    digests = set()
    identifier_digests = set()
    resolutions = None
    counts = {'packets': 0, 'papers': 0, 'documents': 0, 'raw_responses': 0,
              'identifier_responses': 0, 'telemetry_attempts': 0,
              'manifest_sha256': sha(raw_manifest)}

    def check_identifier(value, claim):
        nonlocal resolutions
        if identifiers is None:
            raise ValueError('Supplemental provenance requires an explicit identifier store')
        if 'response_path' in value:
            raise ValueError('Supplemental identifier record cannot supply a literature response path')
        if resolutions is None:
            resolutions = load_identifier_resolutions(Path(identifiers))
        identifier = value.get('identifier')
        if identifier not in {claim.get('subject'), claim.get('object')} or identifier not in resolutions:
            raise ValueError('Supplemental identifier does not match the frozen claim')
        rebuilt = resolutions[identifier]
        for key in ('identifier', 'response_sha256', 'label', 'definition', 'current_taxid', 'binding'):
            if value.get(key) != rebuilt.get(key):
                raise ValueError('Supplemental identifier metadata differs from raw replay')
        identifier_digests.add(rebuilt['response_sha256'])

    def check_raw(value, claim, trail=()):
        if isinstance(value, dict):
            if (len(trail) == 4 and trail[0] == 'stages' and isinstance(trail[1], int)
                    and trail[2] == 'targeting_plan'
                    and trail[3] in {'name_resolution', 'claim_term_resolution'}):
                check_identifier(value, claim)
                return
            if 'response_path' in value or 'response_sha256' in value:
                client.raw(value)
                digests.add(value['response_sha256'])
            for key, child in value.items():
                check_raw(child, claim, (*trail, key))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                check_raw(child, claim, (*trail, index))

    for row in rows:
        oid = row['occurrence_id']
        packet = json.loads((retrieval / 'packets' / (sha(oid.encode()) + '.json')).read_text())
        if (packet['occurrence_id'] != oid or packet['manifest_sha256'] != sha(raw_manifest)
                or packet['claim_sha256'] != sha(json.dumps(row, sort_keys=True).encode())):
            raise ValueError('Packet differs from frozen claim or manifest')
        check_raw(packet, row)
        for item in packet['primary']:
            result = item['result']
            if canonical_reference(item['reference']) != canonical_reference(result['reference']):
                raise ValueError('Paper wrapper and retrieved reference differ')
            kind, value = canonical_reference(result['reference']).split(':', 1)
            metadata = None
            if result.get('metadata', {}).get('status') == 'retrieved':
                metadata = matching_record(json.loads(client.raw(result['metadata'])), kind, value)
            if metadata is None and result.get('identity_metadata_response'):
                crossref = json.loads(client.raw(result['identity_metadata_response']))['message']
                if kind != 'doi' or str(crossref.get('DOI', '')).lower() != value:
                    raise ValueError('CrossRef metadata identity mismatch')
                metadata = {'doi': value, 'title': (crossref.get('title') or [''])[0]}
            if metadata is None and (result['documents'] or any(result.get(k) for k in ('doi', 'pmid', 'pmcid', 'title'))):
                raise ValueError('Unbound publication identity or documents')
            if metadata is not None:
                for key in ('doi', 'pmid', 'pmcid', 'title'):
                    if str(metadata.get(key) or '').lower() != str(result.get(key) or '').lower():
                        raise ValueError('Packet metadata differs from retained response')
            for document in result['documents']:
                rebuilt = replay_document(result, document, client)
                if rebuilt['text'] != document['text']:
                    raise ValueError('Packet text differs from raw document replay')
                counts['documents'] += 1
            counts['papers'] += 1
        counts['packets'] += 1
    selected_ids = {r['occurrence_id'] for r in rows}
    log = retrieval / 'http-attempts.jsonl'
    if log.exists():
        for line in log.read_text().splitlines():
            event = json.loads(line)
            if event['occurrence_id'] not in selected_ids:
                continue
            counts['telemetry_attempts'] += 1
            if event.get('response_sha256'):
                digest = event['response_sha256']
                record = {'response_path': digest + '.response', 'response_sha256': digest}
                raw = client.raw(record)
                if len(raw) != event['bytes']:
                    raise ValueError('Telemetry byte count differs from raw response')
                digests.add(digest)
    counts['raw_responses'] = len(digests)
    counts['identifier_responses'] = len(identifier_digests)
    return counts


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--retrieval', required=True, type=Path)
    parser.add_argument('--identifiers', type=Path,
                        help='Separate directory containing identifier-resolution.json and its raw responses')
    parser.add_argument('--edge', type=int, action='append')
    args = parser.parse_args()
    print(json.dumps(verify(args.manifest, args.retrieval, args.edge, args.identifiers), sort_keys=True))
