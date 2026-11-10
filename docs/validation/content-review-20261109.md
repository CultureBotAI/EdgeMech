# Content-review preparation results — 2026-11-09

These are deterministic accounting and retrieval results, not scientific approvals.

- Full population: **17,637,435 occurrences**, 882 shards, 31 sources.
- Persisted Parquet: **1,442,895,472 bytes** (1.344 GiB). This excludes the node catalogue, source inputs, future documents and review histories.
- Preparation elapsed time: **637.463 seconds** on this host; not an M5 worker-pool benchmark.
- Missing-node occurrences: **0**; present endpoints with incomplete labels/categories: **238,422**.
- Occurrences with at least one nonempty inline evidence field: **4,619,930**. Fields include database-record URLs and unverified citations, not just literature.
- The plan's 4,635,128 inline-evidence total overcounted by **15,198** because its evidence fields overlap.
- Scientific reviews and approvals created: **0**. All content states remain `unassessed`.
- Validation: **220 tests passed**, Ruff passed, pinned CLAW contract check passed (16 files), and GitHub CI passed for the implementation. Independent read-back verified all 882 output shard hashes, sizes and counts.

Node metadata gaps are tracked in [issue #36](https://github.com/CultureBotAI/EdgeMech/issues/36). Counts above are affected occurrences, not distinct nodes; they do not establish scientific falsity.

## Input and output identity

- Census manifest: `a2b8353349816fd067ab3a7112fd1c2f5ee9c02971591ea52f31e9b981cbdd2e`.
- Reconstructed complete source edge SHA-256: `e6a846112ff8c769a8daa8a3c509c3390bd7b5e341c7998ce9188ebece9d4c9a`.
- Pinned node SHA-256: `0e5aa4e0c510e1ad3476d4298f21189a61f20b73b385d6c1ba60bbb36dd8b3a5`.
- Full preparation manifest: `01a89d9db03cdd37b3e7d3483a16e8a3748fe1c60e1b356bf11d6f7790099a3c`.
- Final canary manifest: `8b1988da14676d402a6ec04128ef7f757f699c7ad0de73646f1cb59912ecc547`.

The full scan used implementation commit `ef0b94e`. The subsequent #34 fix made manifest publication atomic and removed a redundant Arrow copy. A fresh 20,000-row canary passed after that fix; comparison after sorting by row number confirmed identical values in every column. Physical row ordering and Parquet bytes differ, so artifact hashes are not interchangeable.

## Canaries and prior decisions

Final canary: 20,000 persisted occurrences, 1,603,776 Parquet bytes, 6.466 seconds. Exact input/output occurrence parity was checked in both directions. It does not test full-population aggregation scale, provider rate limiting or scientific review quality.

The hash-bound prior wave bundles contain **593 distinct individual decisions**, with zero overlap between waves: 116, 120 and 357. All are withheld; no nonempty `quote` fields were found. The legacy ledger's population-wide reviewed label is cohort coverage, not evidence of 17.6M individual scientific reviews. See issue #35.

Anonymous Europe PMC canary for DOI `10.4056/sigs.1804360`: `abstract_available`, exact identifier matched, 11,374 response bytes persisted; SHA-256 `6cb133273a982a429fae505f581f659a3e40c0e9fdcaa4267344eb0340aaa763`. This DOI came from a prior-wave rationale, not an inferred citation for every edge. No quotation or entailment was approved. The initial sandboxed attempt failed DNS resolution and produced no completion marker; the network-enabled run used the same launcher and a new output path.

## Exact source profile

Distinct counts are exact across the complete population, not summed per partition.

| Source | Occurrences | Distinct SPO | Inline evidence | Missing nodes | Incomplete metadata |
|---|---:|---:|---:|---:|---:|
| infores:bacdive | 4,518,786 | 4,484,360 | 4,366,709 | 0 | 54,676 |
| infores:metatraits | 4,365,897 | 4,345,466 | 0 | 0 | 0 |
| infores:gtdb-metatraits | 3,417,267 | 3,244,068 | 0 | 0 | 25 |
| infores:gtdb | 1,471,034 | 1,470,525 | 0 | 0 | 0 |
| infores:ncbitaxon | 925,267 | 925,267 | 0 | 0 | 0 |
| infores:gold | 705,750 | 705,750 | 0 | 0 | 2 |
| infores:microbedecoder | 441,228 | 435,625 | 0 | 0 | 18,374 |
| infores:chebi | 417,520 | 417,073 | 0 | 0 | 0 |
| infores:lpsn | 290,999 | 290,999 | 0 | 0 | 124,064 |
| infores:prego | 237,745 | 221,500 | 237,745 | 0 | 40,980 |
| infores:rhea | 196,437 | 196,436 | 0 | 0 | 192 |
| infores:madin_etal | 182,406 | 182,406 | 0 | 0 | 21 |
| infores:bactotraits | 87,856 | 87,856 | 0 | 0 | 0 |
| infores:uberon | 74,852 | 74,429 | 0 | 0 | 21 |
| infores:go | 74,033 | 74,033 | 0 | 0 | 0 |
| infores:mediadive | 57,286 | 57,205 | 0 | 0 | 3 |
| infores:foodon | 55,372 | 55,370 | 0 | 0 | 11 |
| infores:faprotax | 53,171 | 53,047 | 0 | 0 | 0 |
| infores:pato | 18,910 | 18,833 | 0 | 0 | 6 |
| infores:bergey-manual | 15,013 | 14,931 | 15,013 | 0 | 0 |
| infores:ec | 12,021 | 12,005 | 0 | 0 | 19 |
| infores:envo | 10,825 | 10,822 | 0 | 0 | 0 |
| infores:upa | 2,746 | 2,746 | 0 | 0 | 9 |
| infores:metpo | 1,872 | 1,872 | 0 | 0 | 0 |
| infores:vpi-anaerobe-manual | 1,276 | 1,269 | 0 | 0 | 0 |
| infores:assay-metadata | 563 | 563 | 0 | 0 | 19 |
| infores:mesh | 477 | 477 | 0 | 0 | 0 |
| infores:microbedecoder-literature | 463 | 463 | 463 | 0 | 0 |
| infores:ncit | 250 | 250 | 0 | 0 | 0 |
| infores:micro | 88 | 88 | 0 | 0 | 0 |
| infores:po | 25 | 25 | 0 | 0 | 0 |

## Reproduce and continue

Retained launchers are under `scripts/adhoc/`: `prepare_content_inventory_20261109.py`, `inspect_content_inventory_20261109.py`, `audit_prior_review_coverage_20261109.py`, `probe_literature_20261109.py`, `sample_inventory_citations_20261109.py`, and this report generator. Bulk artifacts remain in ignored `workspace/`.

Next stages are the source-specific evidence catalogue, provider-governed retrieval, quote verification, scientific adjudication and validated publication described in [the corrected plan](../plans/content-review-20261109.md). The single-request probe is not a bulk retrieval scheduler. No M5 sessions were provisioned or terminated.
