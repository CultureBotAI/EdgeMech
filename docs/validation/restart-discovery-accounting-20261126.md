# Retained discovery reference accounting

Date: 2026-11-26. Provenance: issue #228. Engineering review/publication pending.

`scripts/adhoc/account_restart_discovery_20261126.py` compares finite, pinned
hash inventories with pinned evidence scopes. It preserves inventory record
multiplicity, reports shared hashes and conflicting locator bindings, and keeps
scope-only hashes. It never opens a source locator listed inside an inventory.
Scope labels and kinds are supplied assertions: a matching hash is a reference,
not proof that an artifact was fully inspected or scientifically qualified.

The new parameterized source was tracked before use. It did not produce the
earlier inline discovery queries or recovery checkpoints. Exact executed bytes,
private invocation bindings, all test attempts and the original inputs remain
retained privately. Public provenance contains hashes and bounded results only.

## Boundaries

Inputs are an explicitly pinned private manifest and at most128 inventories and
128 scope artifacts. Supported inventory formats are SHA256 line and NUL streams;
scopes additionally accept strict JSON arrays, objects and JSONL with direct
scalar digest fields. Duplicate JSON keys and malformed records fail closed.
GNU escaped line locators preserve byte identity. Paths never enter the report.

Limits are1 MiB for the manifest,64 MiB per other input,256 MiB aggregate input,
500,000 records and64 MiB output. The default60-second deadline is cooperative.
Reads use the maintained nonblocking/no-follow regular-file reader and pins.
Publication walks every parent through directory descriptors without following
symlinks, creates a new file exclusively, flushes file and directory, and reads
back exact bytes. Failed attempts remain; the same name cannot be overwritten.

An offline self-review found an intermediate-parent replacement race in the
initial publisher. The finding was filed before repair. A fresh pytest process
against preserved pre-fix bytes failed the new replacement-at-open regression
with `DID NOT RAISE`; final descriptor traversal passes that regression.

## Final validation

- Full suite: **1669 passed in181.75s**, exit0.
- Focused suite: **32 passed in0.45s**, exit0.
- Contracts:16 verified; CI-scope Ruff and offline sdist/wheel builds passed.
- Source SHA256: `d99752cd5690b9fec34ef09ac7246d9c68301d836b1341fab0d17e8240964f7f`.
- Tests SHA256: `3bab3c6cfac6d3df659bd00927d0e2ed3c167629d9b6bed163e8af6dfb0ed68e`.

An earlier full run had35 failures,1625 passes and7 errors because its repository
basetemp was outside the existing `.temp/fulltext/` staging boundary. The next
focused invocation also lacked its basetemp parent (14 passes,18 setup errors).
Both attempts remain retained. The final suite uses a fresh, existing parent
under `.temp/fulltext/`; no staging guard was weakened. A wrong module-entry
contract command and a sandbox-denied global build-cache attempt were likewise
retained, followed by successful corrected invocations using owned storage.
The source/tests above were unchanged throughout final validation and actual use.

## Actual bounded result

One metadata-only run completed with exit0 and exact persisted readback:

| Measure | Count |
| --- | ---: |
| Saved inventory records, preserving copies |134910|
| Distinct inventoried byte hashes |20509|
| Hashes referenced by the17 selected scopes |3252|
| Hashes absent from those selected scopes |17257|
| Scope-only hashes, retained separately |13|
| Conflicting locator/hash bindings in these inventories |0|

The two inventories have18670 and1840 hashes with one shared hash. The selected
scopes reference1416 and1837 respectively. Absence from the selected scopes is
an accounting gap, not a claim that a file was never read. The13 scope-only
hashes come from the separately authored SQLite narrative reference list, which
reuses a retained readback without reopening any database.

Historical parse failures and the original census outer exit1 remain unchanged;
the census child exit remains unobserved. This run neither repeats census
verification nor establishes A/B membership. Scientific coverage remains0,
A/B counts are null and target/cutoff are unfrozen. Independent source/result
review and publication readback remain pending. Worker privacy/canonical
publication treatment, calibration and all scientific gates remain separate.

Result and validation pins are in
`scripts/adhoc/provenance/restart-discovery-accounting-20261126/summary.json`.
