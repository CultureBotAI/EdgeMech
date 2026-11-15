"""2026-11-12 helper3: author bounded canary queries; inputs manifest, output plan.
Manual query choices for this canary, recorded for reproducibility in the draft PR.
"""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'artifacts/edge-sample-review-20261112'
DATA = Path(os.environ["EDGEMECH_DATA_DIR"])
QUERIES = {
4: ['"Sphingomonas molluscorum" AND temperature', 'DOI:"10.1099/ijs.0.64441-0"'],
5: ['"Lewinella cohaerens" AND (salinity OR NaCl)', 'DOI:"10.1099/ijs.0.65254-0"'],
6: ['("Pseudaeromonas sharmana" OR "Aeromonas sharmana") AND pH', 'DOI:"10.1099/ijs.0.63972-0"'],
19: ['"Staphylococcus aureus" AND "W48906"', '"Staphylococcus aureus" AND "Gram-positive"'],
20: ['"Escherichia coli" AND "SS52"', '"Escherichia coli" AND "Gram-negative"'],
21: ['("Sinorhizobium meliloti" OR "Ensifer meliloti") AND "CIAM1775"', '"Sinorhizobium meliloti" AND (spore OR sporulation)'],
22: ['"Streptomyces" AND "sp001746295"', '"Streptomyces" AND "rolled oats"'],
24: ['"BacDive" AND "165511"', '"Clostridium septicum" AND "EG medium"'],
25: ['"Lactobacillus algidus" AND fumarate', 'EXT_ID:10843056 AND SRC:MED'],
26: ['"Alcanivorax borkumensis" AND nitrate', '"Alcanivorax borkumensis" AND (anaerobic OR "electron acceptor")'],
27: ['"Vibrio furnissii" AND manganese', '"Vibrio furnissii" AND oxidation'],
28: ['"Actinoplanes campanulatus" AND (spore OR sporulation)', 'EXT_ID:23114571 AND SRC:MED'],
29: ['"Actinophytocola xinjiangensis" AND (chemoheterotrophic OR heterotrophic)', '"Actinophytocola xinjiangensis"'],
30: ['"SYIM01" AND "sp009921765"', '"GCA_009921765"'],
31: ['"Treponema stenostreptum" AND acetate', 'EXT_ID:23961314 AND SRC:MED'],
33: ['"Eucapsis microscopica" AND photosynthesis', '"Eucapsis microscopica"'],
34: ['"RIFOXYD1_FULL_47_9"', '"Amesbacteria" AND loam'],
35: ['"RIFCSPHIGHO2_02_FULL_41_13"', '"Magasanikbacteria" AND soil'],
36: ['"Ixodes scapularis" AND "organic material"', '"Ixodes scapularis" AND "leaf litter"'],
37: ['DOI:"10.1042/bj3030233"', 'DOI:"10.1124/dmd.110.033829"'],
38: ['DOI:"10.1074/jbc.270.11.6181"', 'DOI:"10.1128/jb.176.11.3400-3402.1994"'],
39: ['DOI:"10.1128/aem.68.2.634-641.2002"'],
43: ['"HOT-871" AND "nitrogen fixation"', '"Gracilibacteria" AND "HOT-871"'],
44: ['"Streptomyces fagopyri" AND nitrification', '"Streptomyces fagopyri"'],
47: ['"Aromatoleum toluvorans" AND anaerobic', '"Azoarcus toluvorans" AND anaerobic'],
48: ['"Longimycelium tulufanense" AND "alkaline phosphatase"', '"Longimycelium tulufanense"'],
49: ['"Methanohalophilus mahii" AND "agricultural soil"', '"Methanohalophilus mahii" AND "DSM 5219"'],
50: ['"Catonella morbi" AND "anthropogenic"', '"Catonella morbi" AND "ATCC 51271"'],
}
rows = [json.loads(s) for s in (OUT / 'canary.jsonl').read_text().splitlines()]
plan = [{'occurrence_id': r['occurrence_id'], 'canary_ordinal': r['canary_ordinal'],
         'queries': QUERIES.get(r['canary_ordinal'], []),
         'scope': ('Biological claim/reaction: bounded exact taxon/strain, trait and citation search'
                   if r['canary_ordinal'] in QUERIES else
                   'No biological trait claim: source identity, classification, recipe, observation-only or unspecified Other; scientific axis not assessable')}
        for r in rows]
(OUT / 'query-plan.json').write_text(json.dumps(plan, indent=2) + '\n')
DATA.mkdir(exist_ok=True)
(DATA / 'first-edge.jsonl').write_text(json.dumps(rows[3]) + '\n')
(DATA / 'first-plan.json').write_text(json.dumps([plan[3]], indent=2) + '\n')
print(json.dumps({'planned_edges': len(plan), 'searched_edges': len(QUERIES), 'queries': sum(len(p['queries']) for p in plan)}))
