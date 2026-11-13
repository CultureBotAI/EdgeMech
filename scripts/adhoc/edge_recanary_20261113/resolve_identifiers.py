"""Resolve four missing claim identifiers for recanary PR76, 2026-11-13.

Inputs: official taxonomy/ontology identifiers. Outputs: private raw responses,
selected labels/definitions and actual per-service request timings. No papers or
additional graph occurrences are searched. Requests are anonymous and serialized.
"""
import argparse
import hashlib
import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


def resolve(output):
    output.mkdir(parents=True, exist_ok=True)
    requests = [('NCBITaxon:1935118', 'ncbi',
                 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=taxonomy&id=1935118&retmode=xml')]
    for term, ontology in [('BTO:0000648', 'bto'), ('METPO:1000471', 'metpo'), ('METPO:1000444', 'metpo')]:
        requests.append((term, 'ols', 'https://www.ebi.ac.uk/ols4/api/ontologies/' + ontology +
                         '/terms?' + urllib.parse.urlencode({'obo_id': term})))
    results = []
    for term, service, url in requests:
        started = time.monotonic()
        result = {'identifier': term, 'service': service, 'url': url}
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'EdgeMech-recanary/1'})
            with urllib.request.urlopen(req, timeout=25) as response:
                raw = response.read()
                digest = hashlib.sha256(raw).hexdigest()
                (output / (digest + '.response')).write_bytes(raw)
                result.update(status=response.status, response_sha256=digest)
            if service == 'ncbi':
                taxon = ET.fromstring(raw).find('Taxon')
                if taxon is not None and taxon.findtext('TaxId') == term.split(':')[1]:
                    result['label'] = taxon.findtext('ScientificName')
            else:
                terms = json.loads(raw).get('_embedded', {}).get('terms', [])
                exact = [item for item in terms if item.get('obo_id') == term]
                if len(exact) == 1:
                    result.update(label=exact[0]['label'], definition=exact[0].get('description', []))
        except Exception as error:
            result['status'] = getattr(error, 'code', type(error).__name__)
        result['seconds'] = time.monotonic() - started
        results.append(result)
        (output / 'identifier-resolution.json').write_text(json.dumps(results, indent=2) + '\n')
        print(json.dumps(result), flush=True)
        time.sleep(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    resolve(parser.parse_args().output)
