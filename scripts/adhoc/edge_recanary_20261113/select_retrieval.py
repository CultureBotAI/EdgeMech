"""Select bounded stage IDs from saved plans and actual judgments for PR76, 2026-11-13.

Inputs: frozen targeting plan; optional completed primary review decisions.
Outputs: first-unit/remainder IDs or explicitly justified fallback plan and IDs.
"""
import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from organism_targeting import POLICY, name_query, strain_query


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def load_identifier_resolutions(directory):
    """Issue #85: derive labels/definitions from exact identifiers in raw bytes."""
    identities = {}
    for item in json.loads((directory / 'identifier-resolution.json').read_text()):
        digest = item['response_sha256']
        if not re.fullmatch(r'[0-9a-f]{64}', digest):
            raise ValueError('Invalid identifier response digest')
        raw = (directory / (digest + '.response')).read_bytes()
        if hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError('Identifier response hash mismatch')
        identifier = item['identifier']
        if identifier == 'NCBITaxon:1935118':
            taxon = ET.fromstring(raw).find('Taxon')
            if taxon is None or '1935118' not in [node.text for node in taxon.findall('AkaTaxIds/TaxId')]:
                raise ValueError('Merged taxonomy identifier is not bound')
            item = {**item, 'label': taxon.findtext('ScientificName'),
                    'current_taxid': taxon.findtext('TaxId'), 'binding': 'AkaTaxIds/TaxId'}
        else:
            terms = json.loads(raw).get('_embedded', {}).get('terms', [])
            exact = [term for term in terms if term.get('obo_id') == identifier]
            if len(exact) != 1 or not str(exact[0].get('label', '')).strip():
                raise ValueError('Ontology identifier is not uniquely bound to raw response')
            item = {**item, 'label': exact[0]['label'],
                    'definition': exact[0].get('description', []), 'binding': 'obo_id'}
        if identifier in identities:
            raise ValueError('Duplicate identifier resolution')
        identities[identifier] = item
    return identities


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--reviews', type=Path)
    parser.add_argument('--identifiers', type=Path)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    if not 0 < len(plan) <= 50:
        raise ValueError('Only the bounded canary may be selected')
    if args.reviews is None:
        first = next(row for row in plan if row['applicability'] == 'APPLICABLE' and row['primary_references'])
        save(args.output / 'primary-first-ids.json', [first['occurrence_id']])
        save(args.output / 'primary-remaining-ids.json', [r['occurrence_id'] for r in plan if r != first])
        print(json.dumps({'first_ordinal': first['canary_ordinal'], 'remaining': len(plan)-1}))
    else:
        selected = []
        identities = load_identifier_resolutions(args.identifiers) if args.identifiers else {}
        for row in plan:
            if (args.reviews / 'decisions/scientific' / (str(row['canary_ordinal']) + '.json')).exists():
                continue
            path = args.reviews / 'decisions/scientific' / (str(row['canary_ordinal']) + '-primary.json')
            if not path.exists():
                continue
            decision = json.loads(path.read_text())
            if decision['occurrence_id'] != row['occurrence_id']:
                raise ValueError('Decision identity mismatch')
            reason = decision.get('fallback_reason', '').strip()
            if reason:
                ordinal = row['canary_ordinal']
                if row.get('targeting_identity_policy') != POLICY:
                    raise ValueError('Legacy targeting plans are replay-only; rebuild exact organism bindings')
                if ordinal == 34 and identities:
                    resolved = identities['NCBITaxon:1935118']
                    # Retain the resolution for inspection. New aliases must go
                    # through source-packet binding before entering a query.
                    row['name_resolution_candidate'] = resolved
                if ordinal == 36 and identities:
                    row['claim_term_resolution'] = identities['BTO:0000648']
                anchor = name_query(row['resolved_names'])
                row['general_queries'] = [anchor + ' AND ' + row['claim_search_terms']]
                if row['strain_designations']:
                    row['general_queries'].append(strain_query(row['resolved_names'], row['strain_designations']))
                else:
                    row['general_queries'].append(anchor)
                if row['applicability'] != 'APPLICABLE' or not row['general_queries']:
                    raise ValueError('Cannot request fallback for an excluded or untargeted edge')
                row['fallback_reason'] = reason
                selected.append(row['occurrence_id'])
        save(args.output / 'fallback-ids.json', selected)
        save(args.output / 'fallback-plan.json', plan)
        print(json.dumps({'fallback_edges': len(selected)}))


if __name__ == '__main__':
    main()
