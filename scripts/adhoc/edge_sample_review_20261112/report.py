"""2026-11-12 helper3: generate canary report and public operation record.
Inputs:50 source/scientific verdicts, allocation, private receipts and validation.
Outputs: public summary/combined ledger and the requested private canary report.
"""
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ART = ROOT / 'artifacts/edge-sample-review-20261112'
VERDICTS = ['SUPPORTED', 'CONTRADICTED', 'NOT_FOUND', 'NOT_ASSESSABLE']


def load_lines(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def cell(value):
    return str(value).replace('|', '/').replace('\n', ' ')


def resolve_original_canary(data, metadata):
    reference = metadata["private_original_canary"]
    relative = Path(reference["path"])
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Original canary path must be relative to private data")
    path = data / relative
    if not path.resolve().is_relative_to(data.resolve()):
        raise ValueError("Original canary escapes private data")
    if hashlib.sha256(path.read_bytes()).hexdigest() != reference["sha256"]:
        raise ValueError("Original canary hash differs from sampling metadata")
    return path


def generate(data, report, pr):
    cohort = load_lines(ART / 'canary.jsonl')
    science = {r['occurrence_id']: r for r in load_lines(ART / 'scientific-ledger.jsonl')}
    source = {r['occurrence_id']: r for r in json.loads((ART / 'source-adjudications.json').read_text())}
    if len(cohort) != 50 or set(source) != set(science) or set(source) != {r['occurrence_id'] for r in cohort}:
        raise ValueError('Require exactly 50 matched two-axis canary rows')
    original_path = resolve_original_canary(data, json.loads((ART / "sampling-metadata.json").read_text()))
    originals = {r['occurrence_id']: r for r in load_lines(original_path)}
    for row in cohort:
        if any(row[k] != originals[row['occurrence_id']][k] for k in ('subject', 'predicate', 'object', 'origin_transform', 'canary_ordinal')):
            raise ValueError('Sanitization changed a claim')
    first = json.loads((data / 'first-retrieval-receipt.json').read_text())
    retrieval = json.loads((data / 'literature/retrieval-receipt.json').read_text())
    extraction = json.loads((data / 'source/extraction-50.json').read_text())
    allocations = list(csv.DictReader((ART / 'allocation.csv').open()))
    validation_path = data / 'validation.json'
    validation = json.loads(validation_path.read_text()) if validation_path.exists() else {'status': 'pending final checks'}
    totals = {axis: Counter(r['verdict'] for r in rows.values()) for axis, rows in [('source', source), ('science', science)]}
    total_seconds = retrieval['wall_seconds'] + first['wall_seconds']
    api_calls = sum(retrieval['all_attempt_status_counts'].values())
    lines = ['# 50-edge canary report — 2026-11-12', '',
             '**STOP: only the 50-edge canary was adjudicated. The remaining9,950 edges were not retrieved or reviewed. No graph data were changed and no merge was performed.**', '',
             f'Draft PR: {pr}', '',
             '## Result and interpretation', '',
             f'Source fidelity: {dict(totals["source"])}. Scientific support: {dict(totals["science"])}.', '',
             'These are descriptive canary results, not per-source population accuracy estimates. NOT_FOUND means no adequate evidence in the recorded bounded search; NOT_ASSESSABLE includes non-biological identity/scaffolding edges and source/provenance gaps. Neither is counted as false. A database record can faithfully contain an association while independent science remains unresolved. Original rule-labelled triples are the review target; curated rewrites are retained separately.', '',
             '## Sample design', '',
             'Seed: `20261112-helper3-edge-sample-v1`. Deterministic MD5 ranking of occurrence identity plus seed within 29 strata. A same-hash prefix prefilter bounds remote memory; exact quotas are checked. Occurrence identity and multiplicity are preserved. The 10,000 manifest has8,500 retained edges balanced over 13 transforms then rule verdicts, plus 1,500 omitted edges (300 per omission reason, divided across transforms). Each retained transform has653–654 samples, exceeding385. Stratum weights are N_h/n_h. These allocations do not by themselves guarantee +/-5% weighted confidence intervals after nonresponse and organism clustering.', '',
             'The canary selects39 retained occurrences (three per transform with verdict diversity) and 11 omitted occurrences covering all five reasons. Its deliberate diversity prevents treating it as a simple random sample. The full manifest and allocation table are committed; only small samples were transferred. Remote sampling used2 threads,4GB memory and a1GB spill cap. Source extraction streamed large raw inputs read-only without remote output files.', '',
             'Input sizes, modification times and schemas were recorded privately; full multi-gigabyte input hashes were not computed. Manifest and evidence artifacts have SHA256 pins. Public sanitization preserves all 50 claim triples and identities; original manifest bytes remain privately pinned for retrieval replay.', '',
             '| Transform | Rule verdict | Disposition | Population | Sample | Weight N/n |',
             '|---|---|---|---:|---:|---:|']
    for a in allocations:
        lines.append('| ' + ' | '.join([a['origin_transform'], a['content_accuracy_verdict'], a['disposition'], a['population'], a['sample_quota'], f"{float(a['sampling_weight']):.3f}"]) + ' |')
    lines += ['', '## Counts by transform and verdict', '',
              'S=SUPPORTED; C=CONTRADICTED; F=NOT_FOUND; A=NOT_ASSESSABLE.', '',
              '| Transform | n | Source S/C/F/A | Scientific S/C/F/A |', '|---|---:|---|---|']
    for transform in sorted({r['origin_transform'] for r in cohort}):
        selected = [r for r in cohort if r['origin_transform'] == transform]
        counts = []
        for judgments in (source, science):
            c = Counter(judgments[r['occurrence_id']]['verdict'] for r in selected)
            counts.append('/'.join(str(c[v]) for v in VERDICTS))
        lines.append(f'| {transform} | {len(selected)} | {counts[0]} | {counts[1]} |')
    lines += ['', '## All 50 canary judgments and measured retrieval time', '',
              'Seconds and calls below measure literature retrieval only. Edge4 includes its initial live canary run (the second invocation hit the cache). Per-edge agent reasoning and source-parser wall times were not instrumented; presenting these numbers as end-to-end review time would be misleading. Complete per-edge rationales and proof hashes are in the committed ledgers.', '',
              '| # | Transform | Claim | Source | Science | Retrieval s | EPMC calls |', '|---:|---|---|---|---|---:|---:|']
    combined = []
    for row in cohort:
        oid = row['occurrence_id']
        sci = science[oid]
        seconds = sci['retrieval_seconds'] + (first['wall_seconds'] if row['canary_ordinal'] == 4 else 0)
        calls = sci['api_attempts'] + (first['new_api_attempts'] if row['canary_ordinal'] == 4 else 0)
        claim = f"{row['subject_label'] or row['subject']} — {row['predicate']} — {row['object_label'] or row['object']}"
        lines.append(f"| {row['canary_ordinal']} | {row['origin_transform']} | {cell(claim)} | {source[oid]['verdict']} | {sci['verdict']} | {seconds:.2f} | {calls} |")
        combined.append({'canary_ordinal': row['canary_ordinal'], 'occurrence_id': oid, 'origin_transform': row['origin_transform'],
                         'disposition': row['disposition'], 'subject': row['subject'], 'predicate': row['predicate'], 'object': row['object'],
                         'source_fidelity': source[oid], 'scientific_support': sci,
                         'retrieval_seconds_including_initial_canary': seconds, 'epmc_calls_including_initial_canary': calls})
    lines += ['', '## Five worked examples with verified quotations', '',
              'Quotes below are short excerpts; whitespace is collapsed only for display. Ledgers preserve the literal quotes, exact source/text hashes, URLs, evidence levels and publication identifiers. Database publication DOIs identify source provenance and are not biological proof.', '']
    examples = [(31, science), (36, science)]
    for ordinal in (43, 17, 32, 24, 1, 44, 47):
        row = next(r for r in cohort if r['canary_ordinal'] == ordinal)
        if source[row['occurrence_id']].get('evidence'):
            examples.append((ordinal, source))
        if len(examples) == 5:
            break
    if len(examples) != 5:
        raise ValueError('Need five worked quoted examples')
    for ordinal, axis in examples:
        row = next(r for r in cohort if r['canary_ordinal'] == ordinal)
        judgment = axis[row['occurrence_id']]
        lines += [f"### Edge{ordinal}: {'scientific support' if axis is science else 'source fidelity'} — {judgment['verdict']}", '', judgment['rationale'], '']
        for evidence in judgment['evidence'][:2]:
            quote = ' '.join(evidence['quote'].split())
            doi = evidence.get('doi') or evidence.get('publication_doi') or evidence.get('reference')
            pmid = evidence.get('pmid')
            lines += [f'> {quote}', '',
                      f"DOI/PMID: {doi or pmid or evidence.get('publication', 'see ledger')}. URL: {evidence.get('url') or evidence.get('retrieval_url', 'see ledger')}. Text SHA256: `{evidence.get('text_sha256', 'see ledger')}`.", '']
    lines += ['## Protocol, persisted side effects, and telemetry', '',
              'Every judgment is authored by GPT-6 in Codex (runtime variant not exposed). Source fidelity checks the upstream record, identifier, predicate, direction and qualifier. Scientific support uses an explicit query plan, up to five core records per query and up to two OA full texts per query. Exact strains and chemical forms are not replaced by generic species or chemical-class evidence. Taxonomy links, recipe composition, observation-without-outcome and unspecified Other metadata are explicitly outside the biological-trait axis.', '',
              'Europe PMC requests were anonymous, serialized through the existing LiteratureCache, with one-second provider spacing, bounded retries and durable content-addressed responses. One real edge completed first: four200 responses, a nonempty packet and matching SHA256 files were checked before completing the 50. All 50 packets and 50 scientific ledger rows persisted; all five scientific quote proofs replayed against raw bytes and matched exact text. Source quotes are independently rechecked against retained raw-source snapshots. No quote-free directional verdicts are allowed.', '',
              f'Literature retrieval: {total_seconds:.2f}s across 50 edges ({total_seconds/50:.2f}s/edge); {api_calls} API requests ({api_calls/50:.2f}/edge). All 103 returned200; no API throttling, retry exhaustion or parse failure was observed. The 50-edge invocation took{retrieval["wall_seconds"]:.2f}s, plus{first["wall_seconds"]:.2f}s for the first edge.', '',
              f'Source extraction: {extraction["elapsed_seconds"]:.2f}s for 50 selected edges and{extraction["records"]} candidate source records ({extraction["elapsed_seconds"]/50:.2f}s/edge amortized, not an individual-edge measurement). Initial dry/live source-parser fixes handled identifier-prefix matching, argument-size limits, legacy text encoding and misleading compressed-file extensions. No large remote output files were written.', '',
              'Supplemental identity checks:8 web-tool calls containing10 search queries and 7 page opens, shared across the canary; two publisher opens failed and primary database/PubMed records provided the needed identities. Europe PMC 103; NCBI E-utilities0; OpenAlex API0; CrossRef API0; Valency0; publisher TDM API0. Browser-backend transport counts are not exposed. One auxiliary14-edge adjudicator recorded a178-second partial interval including waits; complete agent time and per-edge reasoning time are unavailable.', '',
              '## Remaining9,950: projection and fan-out proposal (not launched)', '',
              f'Linear extrapolation of observed retrieval alone: {9950*total_seconds/50/3600:.1f} hours and approximately{round(9950*api_calls/50):,} Europe PMC requests. A naive repeated source-scan extrapolation is{9950*extraction["elapsed_seconds"]/50/3600:.1f} hours; grouping all sample selectors into one scan per source should reduce it substantially. Neither estimate includes deeper retrieval needed to resolve the many NOT_FOUND cases.', '',
              'Model time/cost was not metered, so a dollar total cannot honestly be inferred. Direct public API fees incurred were$0 and remain$0 at the same services; Codex/subagent usage depends on the account/model rates and actual tokens. A planning allowance of 0.5–2 minutes of adjudication per edge is 83–332 serial agent-hours, or28–111 hours across three adjudicators, excluding retrieval and reconciliation. This is an explicit budgeting assumption, not a measured rate.', '',
              'Do not fan out the current evidence-search protocol unchanged: recent generic hits and inaccessible original-description full texts leave low resolution. First repair citation identity tables and improve synonym/type-strain and cited-primary-paper targeting, then canary the changed path. If authorized later, use one local retrieval coordinator and one durable cache, then three Codex adjudicators reading disjoint cached50-edge batches grouped by taxon. Preserve all original sample weights and validate ledger coverage centrally. Keep source scans read-only on the storage host and all review/cache output local; a remote32-worker pool would add provider contention without solving evidence gaps. No remote worker sessions were started.', '',
              '## Review findings, checks, and public-repository handling', '',
              'Code integrity findings64–67 were filed and fixed before finalization: unconditional50-edge bound, full-ID packet filenames, raw-metadata citation identity checks and manifest-byte binding. Follow-up 68 records an internally inconsistent MicrobeDecoder taxon crosswalk; 69 records unrelated inherited dataset DOIs. Follow-ups 70–73 cover salinity-tolerance overreach, zero-percent positive edges, generic sporulation versus endospores, and original taxon-to-publication predicates. Issue 74 records the fixed CSV line-ending check; 75 retains the obsolete observation-predicate finding. Independent PR review findings 77–79 added guards for alternate raw-root privacy, metadata-driven report paths and source-claim hash binding; all were fixed and regression-tested. The public source transport was parameterized after the live run; that exact revised transport was not live re-canaried and requires a fresh single-record transport canary before any future expansion. No underlying graph fix is included.', '',
              f'Validation receipt: `{json.dumps(validation, sort_keys=True)}`.', '',
              'Before commit, the staged diff was scanned for personal home paths, machine hostnames, email addresses and key-like strings. Public helpers take data locations/hosts as arguments or environment variables. Private command lines, receipts, raw source records and full retrieved text remain outside Git. Public artifacts contain graph identifiers, short quotes, provenance URLs and hashes. Original/private and sanitized/public canary hashes are both recorded; replay uses the original, and identity/triple equivalence is checked. No merge is authorized.', '']
    body = '\n'.join(lines)
    public = ROOT / 'records/edge-sample-canary-2026-11-12.md'
    public.parent.mkdir(exist_ok=True)
    public.write_text(body)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(body + '\n## Private handoff locations\n\n' + f'- Worktree: `{ROOT}`\n- Private evidence: `{data}`\n- Original canary: `{original_path}`\n- Private report: `{report}`\n')
    (ART / 'canary-ledger.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in combined))
    print(json.dumps({'ledger_rows': len(combined), 'private_report_bytes': report.stat().st_size,
                      'public_report_sha256': hashlib.sha256(public.read_bytes()).hexdigest()}))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--data-dir', required=True, type=Path)
    p.add_argument('--report', required=True, type=Path)
    p.add_argument('--pr-url', default='pending draft PR creation')
    args = p.parse_args()
    generate(args.data_dir, args.report, args.pr_url)
