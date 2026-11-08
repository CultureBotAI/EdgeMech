# Bound and parallelize native catalogue validation

The census validates every exported native assertion serially, then issues a
lookup and separate inserts for each assertion, evidence binding and ancestry
binding. Public persisted verification repeats this complete catalogue build.
The combined native inventory is expected to exceed 327,000 rows; even a bounded
KG occurrence canary must validate that entire inventory.

On 2026-11-07, the retained `scripts/adhoc/benchmark_native_catalog_20261107.py`
measured the first 1,000 rows (8,206,453 bytes) of the pinned MIM export:

- Manifest SHA-256: `7b5c493d9301022b5972c304f69dd6f5e9ddad12881bac79ed48a90cb603e9c9`.
- Assertions SHA-256: `58748c350d4770aca02b0a82cf983afe64c8d10658b84a8dc3a0adb605a9888d`.
- JSON decoding and canonical validation: 6.015 seconds.
- Encoding and evidence/ancestry digest construction: 0.383 seconds.
- Serial SQL: 7.586 seconds for 10,000 statements.
- The exact 16-file canonical contract closure verified before measurement.

These measurements describe this prefix and local load, not the other native
corpora or the full census. They identify both validation and SQL round trips
as costs worth addressing. Use at most four spawn workers with bounded queued
batches and ordered consumption, and bounded Arrow batch insertion preserving
deduplication and evidence accounting. Keep full independent validation in the
public verifier, exact input pins and byte accounting, and final publication
checks. Test serial/parallel equivalence, invalid worker input and failure paths,
then repeat the real production launcher with `--workers 4` as a canary before
the full census. This supports CLAW #767 without changing review authority.
