# M5 BactoTraits graph-release verification — 2026-11-16

The new M5 pair verifies the exact-row correction through the actual producer,
and a separate fresh candidate verifies that its complete quarantine audit and
zero graph rows survive production source finalization. Strict merge refuses
the incomplete upstream chain. No corrected merged graph or published release
is established by this evidence.

| Check | Actual result |
| --- | --- |
| Fresh baseline, `ef27b97a0b450767da54235c6105b5250c178adc` | 21 edges, 22 nodes |
| Fresh corrected candidate, `2d94ed094167d94402f21400a9ad7dc4f7f20438` | 0 edges, 0 nodes, 1 complete quarantine audit |
| Separate fresh candidate through `finalize(fresh_run=True)` | 0 edges, 0 nodes, identical quarantine audit |
| Strict `load_and_merge(processes=1)` | Refused missing current BacDive whole-source finalization; no merged output |
| Current raw reviewed-input preflight | Passed against original M5 raw root |
| Current published corrected release | Unavailable; dependency tracked in [#143](https://github.com/CultureBotAI/EdgeMech/issues/143) |

The producer merge is [KG-Microbe PR #1867](https://github.com/Knowledge-Graph-Hub/kg-microbe/pull/1867),
reviewed head `a86c63e778ebf8a646abb9d4d9e0718dfd49f5a0`. The earlier
[identity investigation](bactotraits-identity-20261115.md) is a historical
pre-finalization record. Its old receipts and every nested cache file remain
unchanged; none was used in place of the new baseline.

## Current publication and preserved graph

The live GitHub API inspection found 14 releases, with latest tag
[2025-03-07](https://github.com/Knowledge-Graph-Hub/kg-microbe/releases/tag/2025-03-07),
published `2025-03-07T23:03:41Z`. No November 16 corrected release was present.
The retained canonical M5 `merged-kg.tar.gz` has SHA256
`3d529dd0024843f9278ecfbfc8703413061ef9c4c7474805ecec03aa8cfdfd4c`.
Its embedded historical manifest records generation `2026-10-18T11:56:34+00:00`,
producer `bcfa6bf5b-dirty`, Python 3.10.11, 17,927,641 edges and 3,440,986 nodes.
Those counts are manifest claims, not a new graph-wide validation.

[Upstream #887](https://github.com/Knowledge-Graph-Hub/kg-microbe/issues/887)
remains open and the current release workflow retains its retired artifact URL.
A new URL probe failed DNS; this execution did not reproduce the issue's
historical HTTP404. Publication requires a fresh complete dependency chain,
canonical merge and lineage verification, a working artifact publication source,
separate human approval, and verification of the published asset bytes.

The second GitHub inspection at `2026-11-16T21:20:12Z` again found 14 releases,
with newest asset modification on August 26. The canonical configuration has
24 source keys from 15 producers. After the planned ontologies/BacDive/BactoTraits
chain, 12 additional whole-source completions remain: gold, gtdb, lpsn, lpsn_api,
madin_etal, mediadive, metatraits, metatraits_gtdb, microbedecoder,
ontologies_stubs, prego (habitat only), and rhea_mappings. Independent review
confirmed their completion records were absent using exact paths including
ignored files. This establishes an unmet full-release dependency; it does not
by itself establish that rebuilding them is infeasible. The global ontology
raw-input preflight does not certify those sources' input availability or
freshness.

Independent review found that the first archive stat observation rounded its
nanosecond timestamp by 24 ns through JavaScript Number serialization. The original
observation is preserved. A new Python-written observation records exact
`st_mtime_ns=1792324632633850376` and confirms the unchanged archive SHA256.
[#147](https://github.com/CultureBotAI/EdgeMech/issues/147) tracks this corrected
metadata recording; it is not evidence of archive mutation.

## New execution and provenance

Both new replay runs used the unchanged
`scripts/adhoc/replay_bactotraits_identity_130_20261115.py`, SHA256
`060d7e4dbb6189051f989a4a9efbf55336408e4224ecba5a4975e710538ea90e`,
with `--plan` before each `--run` and a new `--baseline-receipt`. They used one
unit at a time, exclusive output stages, identical shared inputs and the same
absolute `.venv310/bin/python` executable. Python is 3.10.11, built on M5 on
October 10 with Clang 21.0.0; old Python version strings were not rewritten.

The original CSV SHA256 is
`18316d7a0b6c2bef6fcb96a7659c2e3f3734c14786f383c2a93fefe2ae226a4b`.
The complete decoded row 8521/BacDive17851 SHA256 is
`345fd2d00ee93334d975085716692dd4d4c530d5529f04c5b07af0766d5a512a`.
The receipts bind the original and staged CSV, actual BacDive lookup, METPO
tables, local alias and prefix mappings, producer Python source files and policy.
NCBITaxon DB metadata and actual queried statements are bound; the DB and OWL
release agree at `2026-07-12`. This is not a whole-database hash.

The first Poetry install failed DNS. The isolated Python 3.10 environment was
then installed offline from all 346 applicable main/dev lock packages using
`--no-index --no-deps --require-hashes`. Installed versions and `pip check` pass.
335 wheels match lock hashes directly; 11 cached built wheels have separate
wheel hashes and co-located source archives matching the lock. The latter is
source/archive association, not a reproducible-build attestation. Lock SHA256:
`a9e8336e172faef6449ed79a2dde8df7932a5cfb9ba368e7a93a7c7ab83d7f6f`.

| Receipt | SHA256 |
| --- | --- |
| New baseline | `8d2a780d27670106456450fb4c8d1063424570b7bf9277387c8abcb09a389eb0` |
| New pre-finalization candidate | `03446ab15dbe56bf277d25c810b5b0a612a73fe5850d73447d112ab74e611477` |
| New finalized candidate | `0c832333ac93018e95e81d2ba53e9e587b58c4838840859ba823f8f7fd441996` |

The separate finalization helper runs the actual producer and finalizer on the
same live object; it does not reopen old outputs and claim a fresh run. It pins
shared policy files before/after use, the schema trio, finalization code,
configuration, preceding receipts and resulting files. The complete quarantine
audit remains SHA256
`28d62147d49735406a35c721db345497c7e044f69f6d723caa0367f996158918`.
Finalized empty edge TSV SHA256 is
`1a1f91d2da59ddf2aad7f854f52b7e2b23aaba455918bdd7382980bf6e25079f`;
the finalizer adds canonical columns without adding assertions.

All three new stages were copied byte-for-byte beneath the required invocation
output root `.temp/m5-worker-run-20261116/results-r1/`; original paths in receipts
remain unchanged. The [compact result](m5-bactotraits-release-20261116.json)
records every receipt-bound output hash. Complete receipts, plans, stdout/stderr,
publication responses, environment inventory and historical preservation checks
remain private under that invocation root.

## Lineage and scope

The full original CSV has 19,456 data records and exactly one matching BacDive
17851/conflicting-accession occurrence. The lookup has 36,596 records, with one
mapping to NCBITaxon:1123071. The producer rebuilds its mapping and quarantines
the complete reviewed row before its pruned copy and graph writes. The retained
October copies were inspected read-only; stale completion records cannot admit
them through the strict current merge path.

The equivalent historical Madin assertion has independent source provenance:
raw row 50,223, DSM18772, `motility=no`, `data_source=gold`, `ref_id=13521`;
the transformed edge has `infores:madin_etal`. It is not evidence of leakage
from this BactoTraits row. The BacDive lookup separately records motility=no,
although the inspected historical BacDive edge file has no matching assertion.
Neither independent source was newly scientifically reassessed here.

The lineage helper streamed eight explicit input paths, including ignored data,
and hashed them before/after. Its source search used `rg --no-ignore --hidden`.
This is not absence evidence across arbitrary copies or uninspected graphs.
No neighboring row was quarantined, no replacement organism was inferred, and
the correction does not establish trait falsity or graph-wide validity.

## Actual canonical dependency chain

The ordinary CLI whole-ontology unit completed on committed KG candidate
`b631cacf5bca2f5f993e85bacb96578919cc7d92`, whose production implementation is
unchanged from the corrected merged code. It wrote 1,355,041 nodes and 1,729,253
edges across 14 graph pairs. Independent review counted those rows and verified
97 persisted artifacts and 526 named input, implementation and authority paths.
The actual whole-source finalization and producer fingerprint both completed;
the earlier scoped RO canary was not substituted for whole-source completion.
The complete chain receipt SHA256 is
`c5defa64ee549fbc4ef6978ca4cc1fbe441ee319d465eb1188a836cc6534119e`.

The next BacDive unit uses the same canonical output placement, launcher,
Python environment and single-worker/thread limits. Its plan pins six original
inputs totaling 14.875 GB, including the actual 14.074 GB NCBITaxon DB, with
188.416 GB free before staging. BacDive and full BactoTraits completion, followed
by the ordinary strict BactoTraits-only merge, remain pending in this checkpoint.
No completion marker is synthesized and no freshness check is disabled.

The strict merge helper preserves canonical semantics and records explicit
path-only configuration changes: absolute source paths and exclusive output
paths, including statistics. This prevents the canonical cwd-relative stats
filename from overwriting a task-checkout artifact
([#160](https://github.com/CultureBotAI/EdgeMech/issues/160)). It requires all three
complete source receipts and verifies the complete quarantined row, retained
intermediate joins and streamed merged outputs. Its 24 focused tests also pass
independently. A BactoTraits-only candidate cannot establish full-snapshot
publication.

## Independent review and checks

Read-only adversarial review independently recomputed all new stage artifact
hashes, checked complete audit JSON against the original row, compared actual
runtime versions, and verified all 37 historical files. It found no defect in
the bounded producer/finalizer/admission evidence. Two evidence bookkeeping
findings were filed and fixed: [#146](https://github.com/CultureBotAI/EdgeMech/issues/146)
for concurrent progress updates and [#147](https://github.com/CultureBotAI/EdgeMech/issues/147)
for stat precision. A second read-only review verified both fixes.

The finalization helper's six focused tests and production-launcher four focused
tests passed. EdgeMech's final full suite passed 777 tests after the progress
boundary fixes. Required EdgeMech lint and offline wheel/source package builds
also passed. Independent review reran the 23 helper-boundary checks and verified
the actual retained five-case retry receipt against its persisted log bytes.

The first KG standard gate passed its cheap stages and 9,999 tests but failed
four scratch-context assertions and one output-root teardown guard. A versioned
environment moves scratch outside Git into durable `~/agent-work`; all five
affected checks pass without changing assertions or guards
([#161](https://github.com/CultureBotAI/EdgeMech/issues/161)). A second gate exposed
pre-existing fixture dependence on newly produced canonical taxonomy data
([KG #1873](https://github.com/Knowledge-Graph-Hub/kg-microbe/issues/1873)). A
pristine verification checkout at exactly the same committed candidate passes
that real test canary; the unchanged standard full gate there remains pending.
The populated-checkout failure and every earlier log remain preserved.

Read-only review found two new helper boundary cases: exact temporary-root paths
were accepted, and imported terminal receipts did not require consistent exit
status and log hashes. Both are fixed with 23 focused tests
([#162](https://github.com/CultureBotAI/EdgeMech/issues/162)); actual prior test
receipts remain valid. The earlier executed helper bytes are retained by hash.
The existing Java toolchain recorder can mistake `_JAVA_OPTIONS` text for the
version ([KG #1872](https://github.com/Knowledge-Graph-Hub/kg-microbe/issues/1872));
actual Java version and binary/library hashes were captured separately without
rewriting the old record or claiming this provenance-only field gates admission.
