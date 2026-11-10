# Scientific follow-ups: evidence, coverage and metadata

This pass addresses #41 and #35 and completes the distinct-node triage for #36.
It preserves original occurrences, historical reviews and evidence snapshots.
The earlier preparation requests #31 and #32 were reconciled against merged PRs
#33/#38 and closed; those closures do not imply completion of scientific review.

## Six scientific uncertainties revisited

| Source row | Revised outcome | Evidence and remaining boundary |
|---|---|---|
| 7728825, Basfia fermentation | Supported | Original species description explicitly reports glucose fermentation, printed p48 |
| 7726743, Actinobacillus fermentation | Supported | Original paper explicitly characterizes type strain130Z as fermentative, printed p210 |
| 7726749, combined CSL/glucose/fumarate consumption | Concern | Original p208 separates initial enrichment from isolated-colony product screening without fumarate; the mixture does not establish consumption of each component |
| 7728857, Basfia succinate production | Unknown exact chemical scope | Succinic-acid production is supported; source-cell succinate maps to general anion CHEBI:26806 |
| 7726784, Actinobacillus succinate production | Unknown exact chemical scope | Same acid/anion boundary; no source-value replacement or assumed dianion |
| 7726785, Actinobacillus acetate production | Unknown exact chemical scope | Original p210 now establishes acetic-acid co-production; exact acetate interpretation requires the same normalization policy |

Primary papers: [Kuhnert et al., Basfia species description](https://doi.org/10.1099/ijs.0.011809-0)
and [Guettler et al., Actinobacillus species description](https://doi.org/10.1099/00207713-49-1-207).
The source-capture manifest records public author-uploaded copies, checked
identities, URLs and retained hashes. The Actinobacillus enrichment formulation
and screening stage must remain separate; this concern does not demonstrate that
fumarate cannot be consumed in another experiment. Correction route: #56.

The chemical audit corrected the earlier uncertainty description: both source
cells already say succinate, and their object is [CHEBI:26806](https://www.ebi.ac.uk/chebi/CHEBI:26806),
the anion class, rather than specifically the dianion CHEBI:30031. Neutral
[succinic acid, CHEBI:15741](https://www.ebi.ac.uk/chebi/CHEBI:15741), is distinct.
The local producer uses exact-name chemical mapping; its unified SSSOM has
separate exact mappings for succinic acid and succinate. This is a
paper-to-source-table scope question, not a demonstrated literal-mapping defect.
Isolation-agar pH is not production-assay pH. Acidic analytical conditions likewise
do not determine culture speciation. An explicit native claim normalization policy
is required before exact chemical approval (#55); the same standard applies to acetate.

The ten-assessment pilot now has **6 supported, 1 concern and 3 unknown** outcomes,
with ten literal quotation proofs and **zero KG admissions**. The other 453
cohort occurrences remain deferred. These are revised agent judgments on the same
ten IDs, not ten additional reviews or independent scientific agreement.

## Evidence representation and validation

Six quotations use retained Europe PMC abstracts. Four use hashed browsing-tool
extracts of original author-uploaded paper PDFs. Direct local download attempts
returned HTTP403; the retained tool text is not represented as downloaded PDF
bytes or visually checked page images. OCR was not independently reproduced.
The versioned adapter extracts only marked source lines, preserves newlines and
coordinates, rejects omitted-line crossings, and requires an explicit manual
DOI/title identity review. It cannot introduce a citation absent from the original
occurrence. Canonical reviews retain these limitations and all source-input hashes.

A one-occurrence Actinobacillus canary persisted and validated before the complete
ten-assessment revision. The corrected coverage builder independently reconstructed
all ten proofs and their canonical per-occurrence evidence bindings. Local final
validation: **318 tests passed in 41.38 seconds**, repository-wide Ruff passed,
and all 16 pinned CLAW contract files verified. Review findings #50–#54 were filed
before correction and have regression coverage. Final review also found and fixed
#57: proof/evidence parity now verifies the reconstructed source URL. The real
coverage rerun with that check is byte-identical to the result below. No further
blocking findings remained in the read-only source-capture review.

| Retained artifact | SHA-256 |
|---|---|
| `workspace/scientific-followup-full-20261110/bundle.json` | `50628c6da9855a07ea28b23ace22102086743c6507aa744ddbba02780423ed77` |
| `workspace/scientific-followup-full-20261110/quote-proofs.json` | `f95eb3be8917ac6e0c07a146cc4d382064079154f27622ef63cf4451c211693f` |
| `workspace/review-coverage-scientific-followup-20261110.json` | `ab2723dfb26ceaf8eea9009aa60d874eb66f4570e6e0997d20690e2d1cb2dc5b` |
| `workspace/node-metadata-full-v2-20261110/manifest.json` | `afa061b0361610c5e30882306c95389646b059b8611e2309f3c233b537a5c1e6` |

Reviewable judgments and capture pins live in `conf/literature_assessments/20261110-*.json`.
Reproduction launchers are `scripts/adhoc/build_scientific_followup_20261110.py`,
`run_evidence_campaign_20261109.py`, `build_review_coverage_20261110.py` and
`triage_node_metadata_20261110.py`. Bulk source captures and results stay in ignored
workspace; a clone alone cannot reproduce those source-bound artifacts without them.

## Corrected coverage view (#35)

The immutable derived view verifies pinned legacy ledger/census/index/cohort/wave
artifacts and current canonical assessments. Its exact ID union is **600**:
593 prior individual decisions plus ten current assessments minus three overlaps.
The legacy population-wide disposition count remains 17,637,435 withheld rows;
it establishes neither quote verification nor individual scientific support.
Only **10** population occurrences have the explicitly verified current scientific
assessments included in this view; 17,637,425 do not. Original historical artifacts
remain unchanged. The current review is not seeded from the legacy reviewed=100% label.

## Distinct-node triage and upstream routing (#36)

The pinned scan reconciles all **238,422 affected occurrences** to **79,573 distinct
incomplete nodes** and 239,797 endpoint roles. Every observed gap is a missing label;
no category gap or absent endpoint was found in this inventory. Role, namespace
and source counts overlap and must not be added as distinct occurrence counts.

| Namespace | Distinct nodes missing labels | Repair route |
|---|---:|---|
| INSDC | 22,772 | KG-Microbe accession-node construction; resolve against pinned accession metadata |
| doi | 19,230 | Publication-node titles, with exact DOI matching and retained provenance |
| IMG | 18,374 | Source genome/IMG metadata and MicrobeDecoder node assembly |
| PMID | 17,303 | Publication-node titles, with exact PMID matching |
| NCBITaxon | 1,313 | Pinned taxonomy names and obsolete/merged-ID handling |
| BTO | 367 | Pinned ontology node loading and identifier reconciliation |
| EC | 141 | Enzyme-class node loading; distinguish partial EC identifiers |
| Other namespaces | 73 | Source-specific ontology/accession triage from the retained node table |

Prioritize by affected occurrences as well as node count: BacDive's 54,676 affected
occurrences involve only ten distinct incomplete nodes; PREGO's 40,980 involve
1,679. These source counts do not establish which upstream transform caused the gap.
`nodes.parquet` retains exact IDs, missing-field flags, roles, source memberships
and affected occurrence counts for repair selection. No labels are invented and no
pinned release is rewritten. Upstream fixes and normal release regeneration remain
open under #36. A fresh one-partition canary preceded the durable full rerun; output
read-back and post-scan input hashes were verified before publication.
