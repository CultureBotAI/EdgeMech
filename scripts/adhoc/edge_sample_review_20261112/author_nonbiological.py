"""2026-11-12 helper3: save individually authored scientific scope decisions.
Input canary; output decisions for22 edges that make no biological trait assertion.
"""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[3]
out = root / 'artifacts/edge-sample-review-20261112'
REASONS = {
1: 'An API20E citrate observation link has no positive/negative assay result. The edge does not assert citrate utilization; the existence of that observation is a source-fidelity question.',
2: 'BacDive record versus CIP culture-collection accession is an identity mapping, not a biological trait assertion. Assess the original close_match separately from the curated same_as.',
3: 'DSM51066 subclass_of Corallococcus coralloides is a strain-to-taxon classification, without a trait, habitat, substrate or reaction assertion.',
7: 'GOLD organism AMBR158 related_to Streptococcus salivarius is an organism-to-taxonomy link without a specific biological trait.',
8: 'GOLD RUG12445 related_to uncultured Lachnospiraceae bacterium is an organism-to-taxonomy link without a specific biological trait.',
9: 'GOLD Neisseria N177_16 related_to the corresponding NCBI taxon is an identifier relationship, not a biological trait assertion.',
10: 'Assembly GCA_016931655.1 in_taxon GTDB JAFGEJ01 is a classification assertion; biological support of a phenotype cannot be tested from this edge.',
11: 'GTDB Kaistella salipaludis close_match NCBI Chryseobacterium salipaludis is a taxonomic name crosswalk requiring source identity review.',
12: 'Assembly GCF_030540985.1 in_taxon Pseudomonas aeruginosa is a classification assertion, not evidence of a phenotype or habitat.',
13: 'Paracoccus tegillarcae subclass_of Paracoccus asserts taxonomic placement only; source fidelity is assessed independently.',
14: 'LPSN Aliivibrio sifiae close_match its NCBI taxon is a source-identifier crosswalk, without a biological trait claim.',
15: 'Zhihengliuella halotolerans subclass_of Zhihengliuella is taxonomic placement, without a trait or reaction claim.',
16: 'Methanogenium tationis subclass_of Methanogenium is taxonomic placement, without a biological trait assertion.',
17: 'The original taxon close_match DOI edge is a publication-identifier relationship, not a biological claim. Its predicate/direction defect and curated mentions rewrite belong to source fidelity.',
18: 'Rhizobium herbae subclass_of Rhizobium is taxonomic placement; the scientific trait axis is not applicable.',
23: 'Main solution234 has_part vitaminB12 is a medium recipe composition statement. It does not assert that a taxon grows in or requires that ingredient; source recipe fidelity is assessed separately.',
32: 'The Methanomethylophilus alvi to NCBI1281099 close_match is an identity crosswalk, not a biological trait. The incompatible endpoint labels require independent source-fidelity investigation, not an inferred phenotype verdict.',
40: 'Bergey Type_of_metabolism=Other for Alloyangia pacifica has no specified metabolic phenotype that literature can support or contradict.',
41: 'Bergey Type_of_metabolism=Other for Trinickia caryophylli does not define a falsifiable metabolic trait.',
42: 'Bergey Type_of_metabolism=Other for Rickettsiella chironomi is unspecified source metadata, not an assessable biological claim.',
45: 'IMG2772190913 in_taxon Leeuwenhoekiella aestuarii is a genome-to-taxon link. Missing graph node metadata does not itself establish biological falsehood.',
46: 'IMG2770939627 in_taxon Marinomonas pollencensis is a genome-to-taxon link. Its omission for missing node metadata is a source/integrity question, not a biological trait judgment.',
}
rows = [json.loads(s) for s in (out / 'canary.jsonl').read_text().splitlines()]
decisions = [{'occurrence_id': r['occurrence_id'], 'canary_ordinal': r['canary_ordinal'],
              'verdict': 'NOT_ASSESSABLE', 'rationale': REASONS[r['canary_ordinal']], 'citations': []}
             for r in rows if r['canary_ordinal'] in REASONS]
(out / 'scientific-decisions-scope.json').write_text(json.dumps(decisions, indent=2) + '\n')
