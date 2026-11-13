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
                if ordinal == 34 and identities:
                    resolved = identities['NCBITaxon:1935118']
                    row['resolved_names'] = [resolved['label'], 'Candidatus Bathyarchaeota archaeon JdFR-10']
                    row['name_resolution'] = resolved
                    row['general_queries'] = ['("Hecatella orcuttiae" OR "JdFR-10") AND (marine OR ocean OR sediment)',
                                              '"JdFR-10"']
                if ordinal == 36 and identities:
                    row['claim_term_resolution'] = identities['BTO:0000648']
                    row['general_queries'] = ['"Oribacterium" AND (intestine OR intestinal OR gut OR feces OR faeces)', '"Oribacterium"']
                if ordinal == 1:
                    row['general_queries'] = ['("CCUG 36646" OR "CCUG36646")', '"Macrococcus" AND (abdomen OR abdominal)']
                if ordinal == 7:
                    row['general_queries'] = ['"GG12-C01-17"', '"Sulfolobus acidocaldarius" AND "GG12"']
                if ordinal == 35:
                    row['general_queries'] = ['"Pelagibacter" AND ("02_H12" OR "02 H12")', '"Pelagibacter" AND "JGI" AND (marine OR ocean)']
                if ordinal == 50:
                    row['general_queries'] = ['TITLE:"Roseburia intestinalis sp. nov."', '("Roseburia intestinalis" OR "L1-82" OR "DSM 14610") AND (ocean OR marine)']
                if ordinal == 43:
                    row['general_queries'] = ['"JdFR-68" AND (nitrogen OR nif OR diazotrophy)', '"JdFR-68"']
                if ordinal not in {1, 7, 34, 35, 36, 43, 50} and row['strain_designations']:
                    strains = [s.strip() for value in row['strain_designations'] for s in re.split(r'[;,]', value) if s.strip()]
                    row['general_queries'][1:] = ['(' + ' OR '.join('"' + s.replace('"', '') + '"' for s in strains[:4]) + ')']
                if row['applicability'] != 'APPLICABLE' or not row['general_queries']:
                    raise ValueError('Cannot request fallback for an excluded or untargeted edge')
                row['fallback_reason'] = reason
                selected.append(row['occurrence_id'])
        save(args.output / 'fallback-ids.json', selected)
        save(args.output / 'fallback-plan.json', plan)
        print(json.dumps({'fallback_edges': len(selected)}))


if __name__ == '__main__':
    main()
