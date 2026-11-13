"""2026-11-13: primary-first retrieval for the fresh 50-edge recanary.

Inputs: explicit applicability/name/reference plan and frozen canary manifest.
Outputs: private raw responses, evidence packets, and real HTTP-attempt telemetry.
This helper assigns no scientific verdict and never searches an inapplicable edge.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src'))
from edgemech.literature_cache import (  # noqa: E402
    BASE,
    LiteratureCache,
    abstract_text,
    full_text,
    retry_delay,
)
from edgemech.literature_probe import identifier, matching_record  # noqa: E402

_SPEC = importlib.util.spec_from_file_location('recanary_fulltext_access', ROOT / 'scripts/fulltext_access.py')
FA = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = FA
_SPEC.loader.exec_module(FA)
MAX_BYTES = 16 * 1024**2
ROLES = {'species_description', 'strain_reference', 'row_primary'}
KEYS = {'SPRINGER_API_KEY', 'WILEY_TDM_TOKEN', 'WILEY_TDM_CLIENT_TOKEN',
        'ELSEVIER_API_KEY', 'ELS_API_KEY'}
SENSITIVE_HEADERS = {'authorization', 'x-els-apikey', 'wiley-tdm-client-token'}
DATASET_REGISTRY = ROOT / 'artifacts/edge-sample-review-20261112/source-publication-identities.json'
WRONG_INHERITED_DOIS = {'10.1093/nar/' + suffix for suffix in
                        ('gkad994', 'gkad1005', 'gkac886', 'gkac887', 'gkab894', 'gkac1003')}
WRONG_INHERITED_PMIDS = {'37933840', '34634807', '36350631', '36350650', '36243969'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write('\n')
        handle.flush()
        os.fsync(handle.fileno())


def canonical_reference(value):
    normalized = 'PMID:' + value[5:] if value.startswith('pmid:') else value
    kind, body = identifier(normalized)
    return kind + ':' + body


def excluded_reference(value):
    sources = json.loads(DATASET_REGISTRY.read_text())['sources']
    excluded = {'doi:' + row['doi'].lower() for row in sources}
    excluded.update('pmid:' + str(row['pmid']) for row in sources if row.get('pmid'))
    excluded.update('doi:' + doi for doi in WRONG_INHERITED_DOIS)
    excluded.update('pmid:' + pmid for pmid in WRONG_INHERITED_PMIDS)
    return value in excluded or value.startswith(('doi:10.13145/', 'doi:10.83108/'))


def check_reference(ref):
    value = canonical_reference(ref['reference'])
    if ref.get('role') not in ROLES or ref.get('identity_verified') is not True:
        raise ValueError('Primary references require an explicit verified primary-paper role')
    if not str(ref.get('identity_basis', '')).strip():
        raise ValueError('Primary reference lacks source identity provenance')
    if excluded_reference(value):
        raise ValueError('A source-record or dataset DOI cannot be biological primary evidence')
    return value


def load_inputs(manifest, plan):
    manifest_bytes = manifest.read_bytes()
    rows = [json.loads(line) for line in manifest_bytes.decode().splitlines()]
    plans = json.loads(plan.read_text())
    ids = {row['occurrence_id'] for row in rows}
    if not 0 < len(rows) == len(ids) <= 50:
        raise ValueError('Expected one to fifty unique canary occurrences')
    if len(plans) != len(rows) or {row['occurrence_id'] for row in plans} != ids:
        raise ValueError('Plan must contain every selected occurrence exactly once')
    for row in plans:
        if row.get('applicability') not in {'APPLICABLE', 'NOT_APPLICABLE'}:
            raise ValueError('Applicability must be decided before retrieval')
        if not str(row.get('applicability_rule', '')).strip():
            raise ValueError('Applicability needs a written rule')
        refs = row.get('primary_references', [])
        if len(refs) > 3 or len(row.get('general_queries', [])) > 2:
            raise ValueError('Bounded plan allows at most three primary references and two queries')
        for ref in refs:
            check_reference(ref)
        if row['applicability'] == 'NOT_APPLICABLE' and (refs or row.get('general_queries')):
            raise ValueError('NOT_APPLICABLE edges cannot have retrieval requests')
    return rows, plans, sha(manifest_bytes)


def safe_url(url):
    """Telemetry never retains credentials, query values, fragments or local paths."""
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme == 'file':
        return 'file:[private-local-source]'
    if parsed.username or parsed.password or not parsed.hostname:
        raise ValueError('Refusing URL credentials or missing hostname')
    query = urllib.parse.urlencode([(key, '[redacted]') for key, _ in
                                   urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)])
    return urllib.parse.urlunsplit((parsed.scheme, parsed.hostname, parsed.path, query, ''))


def service(url):
    host = urllib.parse.urlsplit(url).hostname or ''
    for fragment, name in [('ebi.ac.uk', 'europe_pmc'), ('openalex.org', 'openalex'),
                           ('crossref.org', 'crossref'), ('springernature.com', 'springer'),
                           ('api.wiley.com', 'wiley'), ('api.elsevier.com', 'elsevier'),
                           ('osti.gov', 'osti'), ('ncbi.nlm.nih.gov', 'ncbi')]:
        if host == fragment or host.endswith('.' + fragment):
            return name
    return 'download:' + host


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Response(io.BytesIO):
    def __init__(self, raw, status, headers, url):
        super().__init__(raw)
        self.status, self.headers, self.url = status, headers, url

    def geturl(self):
        return self.url


class BudgetExceeded(ValueError):
    pass


class Transport:
    """One process + LiteratureCache lock: each actual HTTP hop logged and spaced >=1s."""
    def __init__(self, root, *, opener=None, clock=time.time, sleeper=time.sleep):
        self.root = root
        self.opener = opener or urllib.request.build_opener(NoRedirect()).open
        self.clock, self.sleep = clock, sleeper
        self.next_at = 0.0
        self.events = []
        self.edge = None
        self.stage = None
        self.budget = None

    def __call__(self, request, timeout=25):
        if isinstance(request, str):
            request = urllib.request.Request(request)
        for _ in range(6):
            url = request.full_url
            parsed = urllib.parse.urlsplit(url)
            if parsed.scheme not in {'https', 'http'}:
                raise ValueError('Only HTTP(S) is allowed in network transport')
            if re.search(r'[^\s/]+@[^\s/]+', urllib.parse.unquote(url)):
                raise ValueError('Refusing personal-address disclosure in request URL')
            endpoint = safe_url(url)
            if self.budget is not None:
                if self.budget <= 0:
                    raise BudgetExceeded('Reference full-text request budget exhausted')
                self.budget -= 1
            delay = max(0, self.next_at - self.clock())
            if delay > 60:
                raise BudgetExceeded('Provider backoff extends beyond this bounded attempt')
            self.sleep(delay)
            started = self.clock()
            self.next_at = started + 1.0
            event = {'occurrence_id': self.edge, 'stage': self.stage, 'service': service(url),
                     'url': endpoint, 'started_at_epoch': started}
            try:
                with self.opener(request, timeout=timeout) as response:
                    raw = response.read(MAX_BYTES + 1)
                    if len(raw) > MAX_BYTES:
                        raise ValueError('Response exceeds sixteen MiB')
                    event['status'] = str(response.status)
                    event['response_sha256'] = sha(raw)
                    target = self.root / (sha(raw) + '.response')
                    if not target.exists():
                        with target.open('xb') as handle:
                            handle.write(raw)
                            handle.flush()
                            os.fsync(handle.fileno())
                    elif sha(target.read_bytes()) != sha(raw):
                        raise ValueError('Raw response hash collision')
                    event['bytes'] = len(raw)
                    return Response(raw, response.status, response.headers, endpoint)
            except urllib.error.HTTPError as error:
                event['status'] = str(error.code)
                wait = retry_delay(error.headers.get('Retry-After'), self.clock())
                if wait is not None:
                    self.next_at = max(self.next_at, self.clock() + wait)
                location = error.headers.get('Location')
                if error.code in {301, 302, 303, 307, 308} and location:
                    redirected = urllib.parse.urljoin(url, location)
                    headers = dict(request.header_items())
                    if urllib.parse.urlsplit(redirected).hostname != parsed.hostname:
                        headers = {key: value for key, value in headers.items()
                                   if key.lower() not in SENSITIVE_HEADERS}
                    request = urllib.request.Request(redirected, headers=headers)
                    continue
                raise
            except Exception as error:
                event['status'] = type(error).__name__
                raise
            finally:
                event['elapsed_seconds'] = self.clock() - started
                self.events.append(event)
                with (self.root.parent / 'http-attempts.jsonl').open('a') as handle:
                    handle.write(json.dumps(event) + '\n')
                    handle.flush()
                    os.fsync(handle.fileno())
        raise ValueError('Redirect limit exceeded')

    def fetch(self, url, headers=None):
        request = urllib.request.Request(url, headers={
            'User-Agent': 'EdgeMech-targeted-recanary/1',
            'Accept': 'application/json,application/xml,application/pdf,text/xml', **(headers or {})})
        with self(request) as response:
            raw = response.read()
            return raw, {'status': 'retrieved', 'url': safe_url(url),
                         'response_sha256': sha(raw), 'response_path': sha(raw) + '.response',
                         'content_type': response.headers.get('Content-Type', '')}

    def json(self, url, headers=None, timeout=15):
        raw, _ = self.fetch(url, headers)
        return json.loads(raw)


def load_credentials(path=None):
    """Read only named TDM keys; never execute env-file content or serialize values."""
    result = {key: os.environ[key] for key in KEYS if os.environ.get(key)}
    if path is not None and path.is_file():
        for line in path.read_text().splitlines():
            match = re.fullmatch(r'\s*(?:export\s+)?([A-Z_]+)\s*=\s*(.*?)\s*', line)
            if match and match[1] in KEYS:
                value = match[2]
                if value[:1] in {'"', "'"}:
                    if value[-1:] != value[:1]:
                        raise ValueError('Malformed TDM configuration')
                    value = value[1:-1]
                if value and not value.startswith('#'):
                    result[match[1]] = value
    return result


def xml_text(root):
    blocks = {'p', 'sec', 'section', 'title', 'article-title', 'body', 'abstract',
              'table', 'tr', 'td', 'th', 'caption', 'list-item', 'para'}
    def parts(node):
        block = node.tag.rsplit('}', 1)[-1] in blocks
        if block:
            yield '\n'
        if node.text:
            yield node.text
        for child in node:
            yield from parts(child)
            if child.tail:
                yield child.tail
        if block:
            yield '\n'
    return ''.join(parts(root)).strip()


def decode_document(raw, path, metadata):
    """Strong publication binding; retrieval success alone never establishes identity."""
    doi = (metadata.get('doi') or '').lower()
    pmid = str(metadata.get('pmid') or '')
    if raw.startswith(b'%PDF-'):
        executable = shutil.which('pdftotext')
        if not executable:
            raise ValueError('PDF text extractor unavailable')
        result = subprocess.run([executable, '-layout', str(path), '-'],
                                capture_output=True, check=True, timeout=30)
        text = result.stdout.decode(errors='replace')
        front = text.split('\f', 1)[0][:8000].lower()
        front = re.split(r'(?m)^\s*(?:references|bibliography|literature cited)\b', front, maxsplit=1)[0]
        doi_headers = re.findall(
            r'(?:https?://(?:dx\.)?doi\.org/|\bdoi\s*[:=]?\s*)'
            r'(10\.\d{4,9}/[^\s<>]+)', front)
        doi_match = doi and any(urllib.parse.unquote(value).rstrip('.,;') == doi for value in doi_headers)
        pmid_match = pmid and re.search(r'\bpmid\s*[:=]?\s*' + re.escape(pmid) + r'\b', front)
        title = re.sub(r'\W+', '', abstract_text(metadata.get('title') or '')).lower()
        title_match = len(title) >= 12 and title in re.sub(r'\W+', '', front)
        if not ((doi_match or pmid_match) and title_match):
            raise ValueError('PDF first-page publication identity is unverified')
        proof = 'Exact DOI/PMID header and matching title on first extracted page before references'
        extractor = 'edge-recanary-pdf-layout/v1'
    else:
        root = ET.fromstring(raw)
        articles = [node for node in root.iter() if node.tag.rsplit('}', 1)[-1] == 'article']
        candidates = articles or [root]
        selected = None
        for candidate in candidates:
            fronts = [node for node in candidate.iter() if node.tag.rsplit('}', 1)[-1] in {'front', 'coredata'}]
            ids = []
            for front in fronts:
                for node in front.iter():
                    name = node.tag.rsplit('}', 1)[-1]
                    if name in {'doi', 'pmid'} or (name == 'article-id' and node.get('pub-id-type') in {'doi', 'pmid'}):
                        ids.append((node.get('pub-id-type', name), (node.text or '').strip().lower()))
            if (doi and ('doi', doi) in ids) or (pmid and ('pmid', pmid) in ids):
                selected = candidate
                break
        if selected is None:
            raise ValueError('XML front-matter publication identity is unverified')
        if not any(node.tag.rsplit('}', 1)[-1].lower() in {'body', 'originaltext', 'full-text'} for node in selected.iter()):
            raise ValueError('Publisher XML supplies metadata but no article body')
        text = xml_text(selected)
        proof, extractor = 'DOI/PMID in XML front matter', 'edge-recanary-publisher-xml/v1'
    if len(text.strip()) < 100:
        raise ValueError('Insufficient full text')
    return {'kind': 'publisher_fulltext', 'extractor': extractor, 'text': text,
            'text_sha256': sha(text.encode()), 'identity_verified': True,
            'identity_basis': proof, 'doi': metadata.get('doi'), 'pmid': metadata.get('pmid')}


def publisher_candidate(doi, credentials):
    if doi.startswith(('10.1007/', '10.1038/', '10.1186/')) and credentials.get('SPRINGER_API_KEY'):
        url = 'https://api.springernature.com/openaccess/jats?' + urllib.parse.urlencode({
            'q': 'doi:' + doi, 'api_key': credentials['SPRINGER_API_KEY']})
        return 'springer_tdm', url, {}
    wiley = credentials.get('WILEY_TDM_TOKEN') or credentials.get('WILEY_TDM_CLIENT_TOKEN')
    if doi.startswith(('10.1002/', '10.1111/')) and wiley:
        return 'wiley_tdm', 'https://api.wiley.com/onlinelibrary/tdm/v1/articles/' + urllib.parse.quote(doi, safe=''), {'Wiley-TDM-Client-Token': wiley}
    elsevier = credentials.get('ELSEVIER_API_KEY') or credentials.get('ELS_API_KEY')
    if doi.startswith('10.1016/') and elsevier:
        return 'elsevier_tdm', 'https://api.elsevier.com/content/article/doi/' + urllib.parse.quote(doi, safe='') + '?httpAccept=text/xml', {'X-ELS-APIKey': elsevier}
    return None


def fulltext_ladder(metadata, client, transport, credentials, max_calls):
    """Reuse individual legal rungs, avoiding the unbounded availability orchestrator."""
    attempts = []
    doi = metadata.get('doi')
    if not doi:
        return [], [{'rung': 'ladder', 'status': 'no_doi_for_targeted_ladder'}]
    previous = FA._http_get_json
    discovery_failures = []

    def monitored_discovery(*args, **kwargs):
        try:
            return transport.json(*args, **kwargs)
        except Exception as error:
            discovery_failures.append('http_' + str(error.code) if isinstance(error, urllib.error.HTTPError)
                                      else type(error).__name__)
            raise

    FA._http_get_json = monitored_discovery
    transport.budget = max_calls
    try:
        candidates = []
        local = FA.try_zotero_local(doi=doi, pmid=metadata.get('pmid'))
        if local:
            candidates.append(('zotero_local', local[0], {}))
        else:
            attempts.append({'rung': 'zotero_local', 'status': 'not_found'})
        # Lazily evaluate rungs: provider discovery stops after usable full text.
        for rung in ['local', 'openalex', 'publisher', 'crossref']:
            before_failures = len(discovery_failures)
            if rung == 'openalex':
                found = FA.try_openalex_oa(doi)
                candidates = [('openalex_oa', found[0], {})] if found else []
            elif rung == 'publisher':
                found = publisher_candidate(doi, credentials)
                candidates = [found] if found else []
            elif rung == 'crossref':
                message = FA.crossref_meta(doi)
                if message and str(message.get('DOI', '')).lower() == doi.lower():
                    found = FA.try_crossref_tdm(doi, message)
                    candidates = [('crossref_tdm', found[0], {})] if found else []
                else:
                    candidates = []
            if not candidates:
                if rung != 'local':
                    failures = discovery_failures[before_failures:]
                    attempts.append({'rung': rung, 'status': failures[-1] if failures else 'not_found_or_unconfigured',
                                     'discovery_failures': failures})
                continue
            for name, url, headers in candidates:
                try:
                    if url.startswith('file://'):
                        local_path = Path(urllib.parse.unquote(urllib.parse.urlsplit(url).path))
                        raw = local_path.read_bytes()
                        response = {'url': safe_url(url), 'response_sha256': sha(raw),
                                    'response_path': sha(raw) + '.response', 'status': 'retrieved'}
                        target = client.root / response['response_path']
                        if not target.exists():
                            target.write_bytes(raw)
                    else:
                        raw, response = transport.fetch(url, headers)
                        target = client.root / response['response_path']
                    document = decode_document(raw, target, metadata)
                    document['response'] = response
                    document['retrieval_rung'] = name
                    attempts.append({'rung': name, 'status': 'verified_fulltext', 'url': safe_url(url)})
                    return [document], attempts
                except Exception as error:
                    attempts.append({'rung': name, 'status': type(error).__name__, 'url': safe_url(url)})
            candidates = []
    except Exception as error:
        attempts.append({'rung': 'ladder', 'status': type(error).__name__})
    finally:
        FA._http_get_json = previous
        transport.budget = None
    return [], attempts


def retrieve_reference(reference, client, transport, credentials, max_ladder_calls):
    result = client.document(reference)
    if excluded_reference(reference) or (result.get('doi') and excluded_reference('doi:' + result['doi'].lower())):
        result.update(status='excluded_dataset_or_wrong_inherited_reference', documents=[])
        return result
    if result.get('status') == 'ambiguous_or_missing_identifier' and reference.startswith('doi:'):
        doi = reference[4:]
        url = 'https://api.crossref.org/works/' + urllib.parse.quote(doi, safe='')
        try:
            raw, response = transport.fetch(url)
            record = json.loads(raw)['message']
            if str(record.get('DOI', '')).lower() == doi:
                result.update(doi=doi, title=(record.get('title') or [''])[0],
                              identity_metadata_response=response, status='crossref_identity_verified')
        except Exception as error:
            result['identity_lookup_failure'] = type(error).__name__
    if result.get('doi') and not any(d['kind'] == 'oa_fulltext' for d in result['documents']):
        documents, attempts = fulltext_ladder(result, client, transport, credentials, max_ladder_calls)
        result['documents'].extend(documents)
        result['ladder_attempts'] = attempts
    return result


def replay_document(result, document, client):
    """Offline replay returns verified text and identifiers from retained raw bytes."""
    reference = canonical_reference(result['reference'])
    if excluded_reference(reference):
        raise ValueError('Dataset/source-record identifier cannot support a biological claim')
    kind, value = reference.split(':', 1)
    metadata = None
    if result.get('metadata', {}).get('status') == 'retrieved':
        metadata = matching_record(json.loads(client.raw(result['metadata'])), kind, value)
    if metadata is None and result.get('identity_metadata_response'):
        record = json.loads(client.raw(result['identity_metadata_response']))['message']
        if kind != 'doi' or str(record.get('DOI', '')).lower() != value:
            raise ValueError('CrossRef publication identity mismatch')
        metadata = {'doi': value, 'title': (record.get('title') or [''])[0]}
    if metadata is None:
        raise ValueError('Publication identity cannot be replayed')
    if metadata.get('doi') and excluded_reference('doi:' + metadata['doi'].lower()):
        raise ValueError('Resolved dataset identifier cannot support a biological claim')
    for key in ('doi', 'pmid', 'pmcid'):
        if (str(metadata.get(key) or '').lower() != str(result.get(key) or '').lower()):
            raise ValueError('Packet publication identity differs from raw metadata')
    raw = client.raw(document['response'])
    if document['kind'] == 'abstract':
        if document['response']['response_sha256'] != result['metadata']['response_sha256']:
            raise ValueError('Abstract response differs from bound search response')
        rebuilt = client._document(document['response'], 'abstract', abstract_text(metadata['abstractText']))
    elif document['kind'] == 'oa_fulltext':
        rebuilt = client._document(document['response'], 'oa_fulltext', full_text(raw, metadata['pmcid']))
    elif document['kind'] == 'publisher_fulltext':
        rebuilt = decode_document(raw, client.root / document['response']['response_path'], metadata)
        rebuilt['response'] = document['response']
    else:
        raise ValueError('Unsupported evidence kind')
    if rebuilt['text_sha256'] != document['text_sha256'] or rebuilt['extractor'] != document['extractor']:
        raise ValueError('Replayed text or extractor differs from packet')
    return {**rebuilt, 'doi': metadata.get('doi'), 'pmid': metadata.get('pmid'),
            'pmcid': metadata.get('pmcid'), 'title': metadata.get('title')}


def run(manifest, plan, output, *, stage='primary', edge_ids=None, dry_run=False,
        tdm_env=None, max_ladder_calls=4, opener=None, clock=time.time, sleeper=time.sleep):
    rows, plans, manifest_hash = load_inputs(manifest, plan)
    if stage not in {'primary', 'fallback'} or not 0 <= max_ladder_calls <= 8:
        raise ValueError('Invalid stage or full-text call budget')
    selected = set(edge_ids or [row['occurrence_id'] for row in rows])
    if not selected or not selected <= {row['occurrence_id'] for row in rows}:
        raise ValueError('Selected IDs must be a nonempty subset of the manifest')
    if stage == 'fallback' and edge_ids is None:
        raise ValueError('Fallback requires an explicit selected occurrence list')
    plans = [row for row in plans if row['occurrence_id'] in selected]
    for row in plans:
        if stage == 'fallback' and row['applicability'] == 'APPLICABLE' and not row.get('fallback_reason', '').strip():
            raise ValueError('Fallback requires an authored insufficiency reason')
    if dry_run:
        print(json.dumps({'stage': stage, 'selected_edges': len(plans),
                          'applicable_edges': sum(r['applicability'] == 'APPLICABLE' for r in plans),
                          'primary_references': sum(len(r.get('primary_references', [])) for r in plans),
                          'max_ladder_calls_per_reference': max_ladder_calls, 'concurrency': 1}))
        return
    # Raw text must be outside tracked directories; retain the existing staging guard.
    FA._validate_staging_destination(output / 'sentinel.response')
    output.mkdir(parents=True, exist_ok=True)
    (output / 'cache').mkdir(exist_ok=True)
    transport = Transport(output / 'cache', opener=opener, clock=clock, sleeper=sleeper)
    transport.stage = stage
    credentials = load_credentials(tdm_env)
    t0 = time.monotonic()
    by_id = {row['occurrence_id']: row for row in rows}
    reference_results = {}
    with LiteratureCache(output / 'cache', opener=transport, clock=clock, sleeper=sleeper) as client:
        for plan_row in plans:
            oid = plan_row['occurrence_id']
            packet_path = output / 'packets' / (sha(oid.encode()) + '.json')
            claim_hash = sha(json.dumps(by_id[oid], sort_keys=True).encode())
            if stage == 'fallback':
                packet = json.loads(packet_path.read_text())
                if packet['claim_sha256'] != claim_hash or packet['manifest_sha256'] != manifest_hash:
                    raise ValueError('Fallback primary packet differs from frozen manifest')
                if packet['applicability'] != plan_row['applicability']:
                    raise ValueError('Fallback cannot change applicability')
            else:
                packet = {'occurrence_id': oid, 'claim_sha256': claim_hash,
                          'manifest_sha256': manifest_hash, 'applicability': plan_row['applicability'],
                          'primary': [], 'fallback': [], 'stages': []}
            transport.edge = oid
            before, started = len(transport.events), time.monotonic()
            if plan_row['applicability'] == 'APPLICABLE':
                refs = [check_reference(ref) for ref in plan_row.get('primary_references', [])]
                if stage == 'fallback':
                    refs = []
                    previous_references = {item['reference'] for item in packet['primary']}
                    for query in plan_row.get('general_queries', []):
                        url = BASE + 'search?' + urllib.parse.urlencode({
                            'query': query, 'resultType': 'core', 'format': 'json', 'pageSize': '3'})
                        response = client.request('recanary-general:' + query, url)
                        search = {'query': query, 'response': response, 'references': []}
                        if response['status'] == 'retrieved':
                            result = json.loads(client.raw(response))
                            search['hit_count'] = result.get('hitCount')
                            for record in result.get('resultList', {}).get('result', [])[:3]:
                                ref = 'doi:' + record['doi'].lower() if record.get('doi') else (
                                    'pmid:' + str(record['pmid']) if record.get('pmid') else None)
                                if ref and not excluded_reference(ref):
                                    search['references'].append(ref)
                                    if ref not in refs and ref not in previous_references:
                                        refs.append(ref)
                        packet['fallback'].append(search)
                for ref in refs:
                    if ref not in reference_results:
                        reference_results[ref] = retrieve_reference(ref, client, transport, credentials, max_ladder_calls)
                    packet['primary'].append({'reference': ref, 'retrieval_stage': stage,
                                              'result': reference_results[ref]})
            else:
                packet['retrieval_status'] = 'NOT_APPLICABLE'
            events = transport.events[before:]
            packet['stages'].append({'stage': stage, 'wall_seconds': time.monotonic() - started,
                                     'api_attempts': len(events),
                                     'api_attempts_by_service': dict(Counter(e['service'] for e in events)),
                                     'failure_counts': dict(Counter(e['status'] for e in events if e['status'] != '200')),
                                     'targeting_plan': plan_row})
            save(packet_path, packet)
            print(json.dumps({'edge': oid, 'stage': stage, 'calls': len(events),
                              'seconds': packet['stages'][-1]['wall_seconds']}), flush=True)
    receipt = {'stage': stage, 'selected_edges': len(plans), 'manifest_sha256': manifest_hash,
               'plan_sha256': sha(plan.read_bytes()), 'wall_seconds': time.monotonic() - t0,
               'api_attempts': len(transport.events),
               'api_attempts_by_service': dict(Counter(e['service'] for e in transport.events)),
               'status_counts': dict(Counter(e['status'] for e in transport.events))}
    save(output / (stage + '-receipt.json'), receipt)
    print(json.dumps(receipt), flush=True)
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ['manifest', 'plan', 'output']:
        parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--stage', choices=['primary', 'fallback'], default='primary')
    parser.add_argument('--edge-ids', type=Path)
    parser.add_argument('--tdm-env', '--env-file', dest='tdm_env', type=Path)
    parser.add_argument('--max-ladder-calls', type=int, default=4)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    run(args.manifest, args.plan, args.output, stage=args.stage,
        edge_ids=json.loads(args.edge_ids.read_text()) if args.edge_ids else None,
        dry_run=args.dry_run, tdm_env=args.tdm_env, max_ladder_calls=args.max_ladder_calls)
