# Exact native review and remaining typed evidence coverage

The initial native adapter exports the complete pinned `data/raw/gtdb_mappings.tsv` surface: 322,327 extracted mappings, all unassessed because this inventory lacks exact assertion-level approval proofs. Generated record status cannot supply those proofs.

## Completed source-transport advancement

[PR #229](https://github.com/CultureBotAI/TaxonMech/pull/229) now also exports and verifies all 741,579 links in three distinct committed flat inventories. Every row preserves its original native predicate/type, accession version, source chain and exact owner evidence; all added assertions remain unassessed.

| Surface | Verified rows | Manifest SHA-256 |
| --- | ---: | --- |
| Strain-to-NCBI assembly | 159,283 | `ea0a7a6ff94ccac499bc0a9604d3031918fd8a14bacc39193c982ed4f97e14d8` |
| Strain-to-genome record | 126,576 | `30c4bb2e8b6d6bfd578bc3f32e5f30acadab13d081445c9efbbf5cfebf97a2fa` |
| Strain-to-related record | 455,720 | `51bcc70ee72ee7721e44c7454e88a52fd877fa9ac17da17823ec8c89c8e25627` |

The source commit is `ab35a0d0a0a2b47d250145db0c15b414fccbfdb8`; reviewed code head is `9495d5939df1135f0c71e28c9d5194a12d2e0f9c`, exporter SHA-256 `c422f95a82d2c39b0935fdb35d216f45a88093909174e599fbadcb5d9932aa2d`. Each full output followed a verified one-row four-worker canary. Native source/owner hash, byte and row-count preflight passed; generated envelopes validate; persisted exact bytes, ordered assertion/source-position membership and status counters reconcile before publication. Independent rehashing and exact-head review passed. The PR retains final payload digests and sizes, and the committed guide retains the canary receipts.

## Remaining evidence and scientific scope

This issue remains open. Additional work must establish exact assertion review, primary evidence ancestry and reviewed KG projection policy before eligible reuse. No new scientific review or KG occurrence approval is created by the transport.

- Reconcile or explicitly assess the 147 assembly, 74 genome-record and 445 related-record references lacking an exact matched-owner row. Current assertions retain these gaps without new alias joins; all subject-owner rows are present.
- Add separate native adapters for the nested AllTheBacteria and StrainInfo evidence contracts, nomenclature and any supported strain/deposit identity assertions.
- Preserve supplied versions and source taxonomy while keeping strain/deposit identity, taxon classification and genome-record identity distinct. Retain GOLD organism/project/analysis chains; a shared sample, taxon or owner does not establish genome equivalence.
- Supply exact native review selectors and evidence-bound safe projections. Never promote record/cohort review to approval of every exported assertion, or turn absent exact reviewed overlap into a claim of no biological overlap.

All three CI checks passed on the final PR head. The [authoritative native QC](https://github.com/CultureBotAI/TaxonMech/actions/runs/42420973398/job/128549175715) reports 1,132 tests passed, 34 skipped and five deselected, plus four separate structured-review contract tests; all quality gates passed. Its required adapter tier passed all 35 tests, and vendored-sync passed. PR #229 is ready for review and remains unmerged. This source-transport advancement does not depend on claiming the remaining scientific work complete.
