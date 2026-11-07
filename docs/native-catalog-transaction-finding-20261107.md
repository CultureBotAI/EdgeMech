# Release temporary Arrow views between native catalogue batches

The retained `scripts/adhoc/probe_native_catalog_lifetime_20261107.py` confirms
that registering/unregistering Arrow tables inside the catalogue-wide DuckDB
transaction retains their allocations until COMMIT. On 16 real pinned MIM
assertions in four batches, allocated Arrow bytes after unregister and garbage
collection rose 38,608 → 77,728 → 116,720 → 155,520, then fell to zero at COMMIT.
The same inputs without an outer transaction returned to zero after every batch.
Both modes produced identical 16 native, 96 evidence and 32 ancestry rows.

Receipt: `workspace/validation-20261107/native-catalog-arrow-lifetime.json`,
SHA256 `8f50ac7a0207be81c02759e856fdda19037f13a7931cdaf946768ff9044923aa`.
Probe helper SHA256: `436005a73912fca2c2dfb2b4816794cb2c91ecd11769a85b4f9ed5ec082c67ae`.
Observed census source SHA256: `4c478dfbb8ff85034085c9f0853e758ae6b79c7aa8fdfc2d90611e9db492a7d1`.
This proves the lifetime mechanism for that unit, not attribution of all RSS
observed during the interrupted combined canary.

Use one transaction per bounded insertion batch in the private temporary
catalogue, including native, evidence and ancestry inserts. Commit releases
that batch's Arrow view; errors must roll back that batch. Preserve all previous
input validation and complete final replay. Committing this private scratch
database does not publish an export: manifest-last publication remains gated on
verification of the entire inventory and all persisted census rows.

Add a regression that observes Arrow allocations before each production batch
and a failed-batch rollback test. Keep serial/parallel byte-equivalence and
tamper tests passing. Repeat a small actual production canary, then the combined
inventory canary, before the full census.
