This adds native TaxonMech exports for EdgeMech while preserving exact source rows, typed predicates and evidence scope. The original GTDB export retains all 322,327 source mappings without inventing assertion-level review. Three additional complete exports now retain 741,579 typed strain links, all unassessed.

| Surface | Rows | JSONL bytes | Manifest SHA-256 |
| --- | ---: | ---: | --- |
| `taxonmech:genome_assemblies` | 159,283 | 1,114,645,457 | `ea0a7a6ff94ccac499bc0a9604d3031918fd8a14bacc39193c982ed4f97e14d8` |
| `taxonmech:genome_records` | 126,576 | 871,511,827 | `30c4bb2e8b6d6bfd578bc3f32e5f30acadab13d081445c9efbbf5cfebf97a2fa` |
| `taxonmech:related_records` | 455,720 | 3,213,453,029 | `51bcc70ee72ee7721e44c7454e88a52fd877fa9ac17da17823ec8c89c8e25627` |

Assertions SHA-256 values respectively:

- Assemblies: `c5b08c188721f403ccd7bc9a8a49aadb92aa674cd3e4040105c393b046ef817f`.
- Genome records: `d598e805ad39d80ea68640eab1a06fa8f5e66d75e9c2990235eb7cf90e571ff7`.
- Related records: `874253031ca6790647e917caaded7fe619f6856fb74ea96cb5302eb95fedbe3e`.

The immutable native source is `ab35a0d0a0a2b47d250145db0c15b414fccbfdb8`. Exporter SHA-256 remains `c422f95a82d2c39b0935fdb35d216f45a88093909174e599fbadcb5d9932aa2d` at reviewed PR head `9495d5939df1135f0c71e28c9d5194a12d2e0f9c`. Source and owner inventories reconcile to their native manifest hashes, bytes and counts. Accession versions, dotted identifiers, source taxonomy and GOLD organism/project/analysis chains remain distinct. Missing matched-owner bindings remain explicit: 147 assembly, 74 genome-record and 445 related-record rows. No subject-owner gaps were observed.

No alias join, strain/deposit equivalence, taxonomy reassignment or genome equivalence is inferred. Nested AllTheBacteria/StrainInfo overlays and nomenclature require separate scoped adapters; external primary-source files were not fetched or reverified. Every new assertion reports zero independent scientific reviews and zero KG approvals.

Depends on shared-contract [CLAW #962](https://github.com/CultureBotAI/culturebotai-claw/pull/962), pinned at `1b5391d083ba85ac94e5279c3cba25ac4fde243c`. [#226](https://github.com/CultureBotAI/TaxonMech/issues/226) is advanced through complete typed source transport and remains open for exact native reviews, excluded evidence surfaces and reviewed KG projections. Existing output directories remain immutable.

Validation: all three CI checks passed on the final head. The [authoritative quality gate](https://github.com/CultureBotAI/TaxonMech/actions/runs/42420973398/job/128549175715) reports 1,132 tests passed, 34 skipped and five deselected, plus four separate structured-review contract tests; every TaxonMech quality gate passed. The mandatory native-contract tier passed all 35 tests, and vendored-sync passed. Ruff passed locally. Independent read-only implementation and exact-head reviews found no new blocking issue. A real four-worker canary per surface preceded each full export through the same launcher/environment; persisted bytes, ordered membership and counters reconciled before durable manifest-last publication, then independent hashes and counts were checked. The [committed typed-link guide](https://github.com/CultureBotAI/TaxonMech/blob/9495d5939df1135f0c71e28c9d5194a12d2e0f9c/docs/edge-typed-links-20261107.md) retains canary provenance; its pending-full note describes the earlier code-freeze stage. The final full receipts above were completed afterward without changing producer code.

Fixes #227 and #228. These independent review findings required persisted-byte/membership verification and bounded parallel validation; mutation, serial/spawn identity, bounded-order and worker-failure tests cover the repairs. Merging remains subject to explicit human approval; no merge is authorized or performed.
