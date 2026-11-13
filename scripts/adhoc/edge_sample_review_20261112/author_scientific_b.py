"""2026-11-12 helper3: persist root's14 individually read scientific decisions.
Input canary packet evidence; output authored decisions and merged50 decisions.
"""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[3]
out = root / 'artifacts/edge-sample-review-20261112'
rows = {r['canary_ordinal']: r for r in map(json.loads, (out / 'canary.jsonl').read_text().splitlines())}
# These are explicit authored judgments, not classifications computed from source labels.
DECISIONS = {
31: ('SUPPORTED', 'Table6 lists acetate among Spirochaeta stenostrepta fermentation products (third species column). The same article reclassifies the species as Treponema stenostrepta. LPSN791062 source record marks spelling corrected to T.stenostreptum and binds DSM2028/ATCC25083 plus this DOI; this is the same taxon, not transfer from S.caldaria.', [
    (0, 1, 'acetate, ethanol, CO2, H2, (lactate)'),
    (0, 1, 'Spirochaeta stenostrepta [63]')]),
33: ('NOT_FOUND', 'Both exact Eucapsis microscopica queries completed with zero hits. No publication evidence for the reported photosynthetic-cyanobacteria trait was retrieved; lack of hits is not biological contradiction.', []),
34: ('NOT_FOUND', 'The exact RIFOXYD1_FULL_47_9 query yielded zero hits. The single broad Amesbacteria/loam paper concerns Hg soil remediation; its abstract and retained full text do not identify this MAG in loam. No taxon-to-habitat binding was established.', []),
35: ('NOT_FOUND', 'Exact RIFCSPHIGHO2_02_FULL_41_13 search returned no hits. Broader results describe Magasanikbacteria groups in soil or groundwater, but retained text does not bind this exact MAG to soil. Order/group-level findings were not transferred to the named assembly.', []),
36: ('SUPPORTED', 'A primary I.scapularis experiment reports survival in leaf litter and mulch. These are organic substrates; this supports the broad organic-material habitat assertion through that explicit mapping, not the original PREGO score or a microbial classification of this tick.', [
    (5, 0, 'Tick viability assays without acaricide indicated tick survival above 80% at week four in Phenocosms with leaf litter and mulch')]),
37: ('NOT_FOUND', 'Two cited primary abstracts establish bilirubin mono/diglucuronidation, but neither distinguishes the required C12 beta-D-glucuronoside dianion/regioisomer. Generic bilirubin glucuronide evidence does not verify this exact chemical participant.', []),
38: ('NOT_FOUND', 'Cited abstracts identify ammonia-dependent NAD synthetase activity but do not state the complete deamido-NAD/ATP to AMP/diphosphate reaction or bind EC6.3.1.5 to RHEA21188. Partial enzyme agreement does not validate the exact reaction mapping.', []),
39: ('NOT_FOUND', 'The cited abstract reports oxidation of dinitrotoluene isomers with nitrite release, but not the specific 3,4-dinitrotoluene product 4-methyl-6-nitrocatechol, cofactor stoichiometry or Rhea directional mapping. Exact reaction evidence remains unverified.', []),
43: ('NOT_FOUND', 'Targeted HOT-871/nitrogen-fixation query had zero hits. Broader papers mention HOT-871 abundance or compare a repeat protein, not nitrogen fixation in that organism. Neither absence of a trait statement nor results for another Gracilibacterium imply contradiction.', []),
44: ('NOT_FOUND', 'Targeted nitrification query had zero hits. The exact species-description abstract discusses morphology/taxonomy; other returned studies concern secondary metabolites and straw degradation. Retained full texts contain no matching nitrification assertion for S.fagopyri.', []),
47: ('SUPPORTED', 'The comparative Azoarcus/Aromatoleum study explicitly includes Ar.toluvorans in Aromatoleum Group2 and describes the non-plant-associated group as facultative or obligate anaerobes. This supports anaerobic capability, not obligate anaerobiosis; the edge reports the generic source value anaerobe.', [
    (1, 0, 'all are facultative or obligate anaerobes.'),
    (1, 0, 'Ar. toluolicum, and Ar. toluvorans.')]),
48: ('NOT_FOUND', 'Exact taxon/alkaline-phosphatase search returned zero hits. Broader results and retained full texts concern lasso peptide biosynthesis, P450 enzymes and other taxa; no taxon-specific alkaline-phosphatase activity result was retrieved.', []),
49: ('NOT_FOUND', 'The soil-comparison paper does not document DSM5219 in agricultural soil. Other results use M.mahii as a reference or describe different strains/sites. A hypersaline or hydraulic-fracturing habitat does not exclude agricultural soil, so no contradiction is assigned.', []),
50: ('NOT_FOUND', 'No targeted anthropogenic-material hit. Retrieved exact-strain literature places ATCC51271 in the human gingival crevice and provides taxonomic comparisons, not the required anthropogenic environmental-material habitat. A different documented habitat is not proof of absence from this one.', []),
}
decisions = [{'occurrence_id': rows[n]['occurrence_id'], 'canary_ordinal': n,
              'verdict': v, 'rationale': rationale,
              'citations': [{'paper': p, 'document': d, 'quote': q} for p, d, q in citations]}
             for n, (v, rationale, citations) in DECISIONS.items()]
(out / 'scientific-decisions-b.json').write_text(json.dumps(decisions, indent=2) + '\n')
a = json.loads((out / 'scientific-decisions-a.json').read_text())
combined = a['decisions'] + decisions + json.loads((out / 'scientific-decisions-scope.json').read_text())
ordinals = {r["occurrence_id"]: n for n, r in rows.items()}
for decision in combined:
    decision["canary_ordinal"] = ordinals[decision["occurrence_id"]]
combined.sort(key=lambda d: d["canary_ordinal"])
if [d['canary_ordinal'] for d in combined] != list(range(1, 51)):
    raise ValueError('Need exactly canary ordinals1 through50')
(out / 'scientific-decisions.json').write_text(json.dumps(combined, indent=2) + '\n')
print('Saved50 authored scientific judgments;3SUPPORTED,25NOT_FOUND,22NOT_ASSESSABLE')
