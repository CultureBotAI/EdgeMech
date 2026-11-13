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
    20: ['10.1099/0096266x-5-2-67', '10.1007/s10482-018-1047-3'],
    21: ['10.2323/jgam.25.215', '10.1099/ijs.0.02091-0', '10.1099/ijs.0.64316-0'],
    22: ['10.1099/00207713-22-2-73'],
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
    50: ['10.1099/ijs.0.02143-0', '10.1099/ijs.0.64098-0'],
}


def lines(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def dedupe(values):
    return list(dict.fromkeys(str(v).strip() for v in values if str(v).strip()))


def build(enrichment, destination):
    cohort = lines(ART / 'canary.jsonl')
    applicability = {r['occurrence_id']: r for r in lines(ART / 'applicability.jsonl')}
    targeting = {r['occurrence_id']: r for r in json.loads(enrichment.read_text())}
    if set(targeting) != {r['occurrence_id'] for r in cohort}:
        raise ValueError('Source enrichment must cover the exact fresh fifty')
    plan = []
    for row in cohort:
        oid, ordinal = row['occurrence_id'], row['canary_ordinal']
        scope, target = applicability[oid], targeting[oid]
        applicable = scope['scientific_applicability'] == 'APPLICABLE'
        names = dedupe(target.get('resolved_names', []))
        if ordinal == 7 and not names:
            names = [row['subject_label']]
        if ordinal == 47:
            names = [n for n in names if n not in {'Lactobacillus viridescens', 'Weissella viridescens'}]
        strains = dedupe(target.get('strain_designations', []))
        refs, seen = [], set()
        # Only references recovered from the matching upstream record enter here.
        for ref in target.get('primary_references', []):
            key = ref['reference'].lower()
            if key in seen:
                continue
            if ref.get('identity_verified') is not True or not ref.get('identity_basis'):
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
                quoted = ['"' + n.replace('"', '') + '"' for n in names[:6]]
                queries.append('(' + ' OR '.join(quoted) + ') AND ' + TERMS[ordinal])
                # Second query broadens within resolved names, not to a genus or
                # unrelated strain: the claim must retain its taxonomic scope.
                queries.append('(' + ' OR '.join(quoted[:3]) + ')')
            elif strains:
                quoted = ['"' + s.replace('"', '') + '"' for s in strains[:4]]
                queries.append('(' + ' OR '.join(quoted) + ') AND ' + TERMS[ordinal])
        plan.append({
            'canary_ordinal': ordinal, 'occurrence_id': oid,
            'applicability': scope['scientific_applicability'],
            'applicability_rule': scope['applicability_rule'],
            'resolved_names': names, 'strain_designations': strains,
            'primary_references': refs[:3] if applicable else [],
            'primary_references_available': available_count if applicable else 0,
            'general_queries': queries if applicable else [],
            'fallback_reason': '',
            'targeting_policy': 'Raw source association only; inherited graph DOI fields excluded. Retrieved article identifiers independently checked.',
        })
    destination.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n')
    receipt = {'rows': len(plan), 'applicable': sum(p['applicability'] == 'APPLICABLE' for p in plan),
               'plan_sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
               'source_enrichment_sha256': hashlib.sha256(enrichment.read_bytes()).hexdigest(),
               'cohort_sha256': hashlib.sha256((ART / 'canary.jsonl').read_bytes()).hexdigest()}
    destination.with_name(destination.stem + '-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--enrichment', required=True, type=Path)
    parser.add_argument('--output', type=Path, default=ART / 'targeting-plan.json')
    args = parser.parse_args()
    build(args.enrichment, args.output)
