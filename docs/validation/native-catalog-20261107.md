# Native catalogue measurements and canary repairs

The retained `scripts/adhoc/benchmark_native_catalog_20261107.py` measured the
same first 1,000 native MIM rows (8,206,453 bytes) using the former per-row SQL
algorithm and the initial bounded production path. These historical measurements
address EdgeMech #8; they predate the large-inventory repairs in #10 and #11.

| Path | Measured time |
| --- | ---: |
| Serial decoding and canonical validation | 4.603 s |
| Serial encoding and evidence bindings | 0.324 s |
| Serial SQL, 10,000 statements | 5.261 s |
| Four-worker production catalogue, including worker startup/shutdown | 5.640 s |
| Bulk SQL within that production measurement, 16 batches | 1.100 s |

The serial stages total about 10.19 seconds. This single prefix comparison
shows roughly 1.8-fold improvement under the measured local load; it does not
predict full-corpus throughput. That implementation queued at most four
ordered batches, each bounded to 64 rows and 512 KiB except a single larger
legal native envelope. Database writes remain in the parent process.
Public verification independently validates all native data again.

The production receipt records parent peak RSS of 315,277,312 bytes and OS child
RSS accounting separately. Neither is a measured simultaneous pool-memory peak.
The final tests compare serial/four-worker artifact bytes and exercise duplicate
accounting, bounded queues, worker failure and tampered persisted payloads.

Both historical comparison receipts bind these exact bytes:

- Native manifest: `7b5c493d9301022b5972c304f69dd6f5e9ddad12881bac79ed48a90cb603e9c9`.
- Native JSONL: `58748c350d4770aca02b0a82cf983afe64c8d10658b84a8dc3a0adb605a9888d`.
- Benchmark helper: `a7ffff9de3f50f03f7eb00b0fae94cfd5ab4a2448f8cd681158592e37e469223`.
- Census implementation: `d18f23a8a6c9cc6f49ad60e0b401f15656f970d3e5df04889d751c4fb110d4b0`.

Receipts under `workspace/edge-curation-20261107/`:

- `native-catalog-reviewed-baseline-1000.json`: `2f2c076fd5c31329e8142d3b38031892e950e29e575f1d39521368559ef0ceef`.
- `native-catalog-reviewed-workers4-v2-1000.json`: `ff4a3ce7100e28c627b3d2ec0f943af843477bcc06462dcbbd9bf1f702976e65`.

Earlier exploratory receipts remain preserved. This comparison uses the
committed helper bytes and verifies all 16 shared contract pins.

The real four-adapter canary subsequently exposed repeated SQL lookup overhead
and Arrow allocations retained by the catalogue-wide transaction. That run was
interrupted without publishing a manifest. Its evidence remains in
`workspace/validation-20261107/combined-bounded-conformance-interrupted-20261107.json`.
The failure and repairs are recorded in `docs/native-large-catalog-finding-20261107.md`
and `docs/native-catalog-transaction-finding-20261107.md`.

The repaired path uses at most four ordered batches, each bounded to 512 rows
or 4 MiB, with a single larger legal envelope traveling alone. Each insertion
batch commits native rows and their evidence/ancestry bindings atomically in the
private catalogue. The complete input and persisted census replay still gate
external manifest publication. A retained real-data probe demonstrated Arrow
allocations accumulating across four batches under the old outer transaction
and returning to zero after each batch without it. Production regressions check
allocation release, complete rollback and retry.

The final code hash is
`2b90886fb21d1f42d3d718d936e1a09e37c935b1b23d5ff6cf4b266abfa73793`.
Actual canary/full-population measurements are reported in
[`20261107.md`](20261107.md); the prefix speedup above is not used to estimate them.
