# EdgeMech validation evidence — 2026-11-07

Generated from persisted receipts by `scripts/adhoc/summarize_validation_20261107.py`.
Bulk stores and full receipts remain in ignored `workspace/validation-20261107/`.

## SQLite migration

Each measurement migrates the same verified 1,000-row ledger in a separate process.
Migration time includes complete replay and verification; reconciliation is a second full audit.
Peak memory is process RSS, including Python, Arrow and DuckDB. These small-input measurements
do not establish a production layout, graph-wide performance or review quality.

| Buckets | Row group | Files | Parquet bytes | Migration s | Reconcile s | Lookup ms | Peak MiB |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 16 | 8192 | 46 | 228250 | 2.303 | 0.544 | 154.587 | 240.14 |
| 2 | 1024 | 11 | 143021 | 2.600 | 0.766 | 186.732 | 235.80 |
| 64 | 8192 | 146 | 485112 | 3.181 | 1.002 | 158.752 | 240.73 |

Input SQLite: `85d0f98093a595308f9246cc9c517dbaf5ef26086d65650f0cff025609498ade` (806912 bytes).
All authoritative fields, occurrence IDs, raw rows, memberships, current decisions
and historical canonical bundles are compared through replay. Independent source
and persisted complete-field logical hashes and row counts match for all five
authoritative tables before publication; the hash-bound migration receipt retains both sides.
The canary preserves
999 unprocessed plus one deferred decision, all withheld, with one historical bundle.
It creates zero scientific approvals.

- `storage-source-parity-canary` receipt SHA-256: `d0bbffb055fb9b900feca137519e7fcf380378960dbce36176e69024962e4c2a`;
  artifact manifest: `10ec71920b7ea2c6077a12cf89435b7c1c3833e8c686a10df11086e6daaa2ab4`;
  migration receipt: `34b3ad5bd69babbdf32bc955d66c6bae089d93f263efd0b093962741c6a5211e`.
- `storage-source-parity-benchmark-2` receipt SHA-256: `bb09d1f4ba3e028cd1bf20b5845849ae907d7801c095ab7ffb428438ac6aa0af`;
  artifact manifest: `0f107ed4c6b296f08022d4f1fe63460a798fbad7aa7f2ec7aed77e272ffc13fe`;
  migration receipt: `a71d376ce3b9f6434d4dde89ccbacecff920eab952c60ba822c11566319f6954`.
- `storage-source-parity-benchmark-64` receipt SHA-256: `5e854fd15e1cab57719fcdd5f492aa93aa9ea0192c3d3da5c4e67bb3b0d02e39`;
  artifact manifest: `ffce85311f68cb2f2959450e0182fa4157787a9c1684123a036c4508a0621c08`;
  migration receipt: `910989cd4852255320d06472ff43796a7f6aeace9fe36de629e16c4cb0203bfe`.

## Native overlap census

The source is the historical 20260929 KG-Microbe snapshot, not a newly published release.
Its manifest SHA-256 is `f585e55a616d3771f382c91c78713cb8d74812c7ba177576090ccd5f9e6654b2`
and its recorded producer is `1408e7099-dirty`. Exact inherited-scope eligibility is
separate from scientific approval. Matching endpoints alone cannot approve a KG claim.

No census receipt was supplied to this report.
