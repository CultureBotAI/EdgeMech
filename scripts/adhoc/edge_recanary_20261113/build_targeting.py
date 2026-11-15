"""Build primary-first targets for recanary PR76, 2026-11-13.

Inputs: frozen public cohort/applicability and private grouped-source enrichment.
Outputs: public bounded targeting plan with raw-source association proofs. No
inherited graph DOI is accepted as a primary reference, even if its syntax is valid.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from organism_targeting import POLICY, claim_identity, name_query, strain_query
from source_adjudicate import packet_targeting

ROOT = Path(__file__).resolve().parents[3]
ART = ROOT / 'artifacts/edge-recanary-20261113'
# Terms only specify the claim to search; they do not assign scientific outcomes.
TERMS = {
    1: '(abdomen OR abdominal OR isolation)',
    4: '(NaCl OR salinity OR salt)',
    5: '(motility OR motile OR flagella)',
    6: '(temperature OR growth OR optimum)',
    7: '("GG12-C01-17" OR "hot spring" OR temperature)',
    19: '(succinate OR succinic OR "carbon source")',
    20: '(14628 OR morphology OR pleomorphic OR rod)',
    21: '(aerobic OR anaerobic OR oxygen)',
    22: '("EG medium" OR "Eggerth" OR "Gagnon")',
    24: '("nutrient agar" OR "medium 1" OR DSMZ)',
    25: '(nitrate OR reduction OR respiration)',
    26: '(xylan OR hydrolysis OR "23A/997/2015")',
    27: '(fumarate OR respiration OR "electron acceptor")',
    28: '(tartrate OR tartaric OR growth)',
    29: '(plastic OR polymer OR degradation)',
    30: '(galactarate OR mucate OR mucic)',
    31: '(lactate OR "lactic acid" OR fermentation)',
    32: '(sulfite OR sulphite OR respiration)',
    33: '(oxygenic OR photoautotrophy OR photosynthesis)',
    34: '(marine OR ocean OR seawater)',
    35: '("02_H12" OR marine OR ocean)',
    36: '(habitat OR isolation OR intestinal)',
    43: '("JdFR-68" OR "nitrogen fixation" OR diazotrophy)',
    44: '(temperature OR psychrophilic OR growth)',
    47: '(salt OR NaCl OR salinity)',
    48: '(oxidase OR phenotype)',
    49: '(grassland OR isolation OR soil)',
    50: '("L1-82" OR ocean OR isolation)',
}

# Curator-selected original descriptions and relevant source-row references.
# Selection happened from upstream titles before any literature request. Generic
# databases, trait-mining studies and prediction models are excluded here.
PRIMARY_CHOICES = {
    4: ['10.1099/ijsem.0.001523'],
    5: ['10.1099/ijs.0.65010-0'],
    6: ['10.1099/ijsem.0.001496'],
    19: ['10.1099/ijs.0.65213-0'],
    # Species-only references cannot establish the exact 14628 strain (#104).
    20: [],
    21: ['10.2323/jgam.25.215', '10.1099/ijs.0.02091-0', '10.1099/ijs.0.64316-0'],
    # The species type description is not bound to this non-type strain (#103).
    22: [],
    25: ['10.1093/infdis/106.2.162', '10.1099/00221287-51-3-387', '10.1099/ijsem.0.005511'],
    27: ['10.3390/microorganisms10071363'],
    28: ['10.1099/ijsem.0.003189'],
    29: ['10.1007/s10482-022-01756-2'],
    31: ['10.1016/s0723-2020(84)80007-7', '10.1002/9781118960608.gbm00569'],
    32: ['10.1016/s0723-2020(97)80004-5', '10.1002/9781118960608.gbm01011.pub2'],
    36: ['10.1099/ijs.0.63060-0', '10.1099/ijs.0.060988-0'],
    44: ['10.1099/ijs.0.64774-0'],
    47: ['10.1016/s0723-2020(83)80056-3', '10.1111/j.1365-2672.1993.tb01600.x'],
    48: ['10.1099/00207713-44-1-143', '10.1099/00207713-47-3-808', '10.1099/00207713-46-4-939'],
    49: ['10.1099/00207713-49-4-1761'],
    # The species description is not bound to the exact L1-82 strain (#104).
    50: [],
}


def lines(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def dedupe(values):
    return list(dict.fromkeys(str(v).strip() for v in values if str(v).strip()))


def build(enrichment, destination, ordinal=None):
    cohort = lines(ART / 'canary.jsonl')
    if ordinal is not None:
        cohort = [row for row in cohort if row['canary_ordinal'] == ordinal]
        if len(cohort) != 1:
            raise ValueError('Select one frozen canary ordinal')
    manifest = destination.with_suffix('.manifest.jsonl')
    sources = destination.with_suffix('.sources.json')
    receipt_path = destination.with_name(destination.stem + '-receipt.json')
    if any(path.exists() for path in (destination, manifest, sources, receipt_path)):
        raise ValueError('Refusing to overwrite a targeting plan or its provenance')
    applicability = {r['occurrence_id']: r for r in lines(ART / 'applicability.jsonl')}
    targeting = {r['occurrence_id']: r for r in json.loads(enrichment.read_text())}
    if set(targeting) != {r['occurrence_id'] for r in cohort}:
        raise ValueError('Source enrichment must cover the exact selected cohort')
    plan = []
    for row in cohort:
        oid, ordinal = row['occurrence_id'], row['canary_ordinal']
        scope, target = applicability[oid], targeting[oid]
        applicable = scope['scientific_applicability'] == 'APPLICABLE'
        packet = target.get('source_packet')
        if not packet or claim_identity(packet['edge']) != claim_identity(row):
            raise ValueError('Source packet must bind the exact selected manifest row')
        if target != {**packet_targeting(packet), 'source_packet': packet}:
            raise ValueError('Source enrichment differs from replayed organism bindings')
        if target.get('targeting_identity_policy') != POLICY:
            raise ValueError('Rebuild source enrichment with exact organism bindings before retrieval')
        names = dedupe(target.get('resolved_names', []))
        strains = dedupe(target.get('strain_designations', []))
        refs, seen = [], set()
        # Only references recovered from the matching upstream record enter here.
        for ref in target.get('primary_references', []):
            key = ref['reference'].lower()
            if key in seen:
                continue
            if (ref.get('identity_verified') is not True or not ref.get('identity_basis')
                    or ref.get('organism_identity_verified') is not True
                    or not ref.get('organism_binding')):
                raise ValueError('Unverified source association')
            refs.append(ref)
            seen.add(key)
        available_count = len(refs)
        choices = ['doi:' + value for value in PRIMARY_CHOICES.get(ordinal, [])]
        available = {r['reference'].lower(): r for r in refs}
        if applicable and any(ref not in available for ref in choices):
            raise ValueError(f'Chosen source reference absent for edge {ordinal}')
        refs = [available[ref] for ref in choices]
        queries = []
        if applicable:
            if ordinal not in TERMS:
                raise ValueError('Applicable claim needs a reviewed search concept')
            if names:
                anchor = name_query(names)
                queries.append(anchor + ' AND ' + TERMS[ordinal])
                # Second query broadens within resolved names, not to a genus or
                # unrelated strain: the claim must retain its taxonomic scope.
                queries.append(strain_query(names, strains) if strains else anchor)
        plan.append({
            'canary_ordinal': ordinal, 'occurrence_id': oid,
            'applicability': scope['scientific_applicability'],
            'applicability_rule': scope['applicability_rule'],
            'resolved_names': names, 'strain_designations': strains,
            'targeting_identity_policy': POLICY,
            'source_packet_sha256': target['source_packet_sha256'],
            'name_bindings': target['name_bindings'],
            'strain_bindings': target['strain_bindings'],
            'claim_search_terms': TERMS.get(ordinal),
            'primary_references': refs[:3] if applicable else [],
            'primary_references_available': available_count if applicable else 0,
            'general_queries': queries if applicable else [],
            'fallback_reason': '',
            'targeting_policy': 'Exact organism/source bindings required; candidate aliases/references withheld. Retrieved article identifiers and claim support require separate checks.',
        })
    destination.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n')
    manifest.write_text(''.join(json.dumps(row, sort_keys=True) + '\n' for row in cohort))
    sources.write_text(json.dumps({oid: target['source_packet'] for oid, target in targeting.items()},
                                  sort_keys=True) + '\n')
    receipt = {'rows': len(plan), 'applicable': sum(p['applicability'] == 'APPLICABLE' for p in plan),
               'plan_sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
               'source_enrichment_sha256': hashlib.sha256(enrichment.read_bytes()).hexdigest(),
               'selected_manifest_sha256': hashlib.sha256(manifest.read_bytes()).hexdigest(),
               'source_packets_sha256': hashlib.sha256(sources.read_bytes()).hexdigest(),
               'cohort_sha256': hashlib.sha256((ART / 'canary.jsonl').read_bytes()).hexdigest()}
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--enrichment', required=True, type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--ordinal', type=int)
    args = parser.parse_args()
    build(args.enrichment, args.output, args.ordinal)
