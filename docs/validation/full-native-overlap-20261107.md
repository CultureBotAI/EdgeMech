# Full native overlap census, 2026-11-07

The complete pinned KG-Microbe population of **17,637,435 edge occurrences**
has been joined against **1,082,786 native assertions across ten exports**.
The production driver completed independent replay of the persisted native
envelopes and every stored KG row before publishing the immutable artifact.
The results below are verified final counts, replacing the provisional counts
observed during the run. This completes the expanded census execution for
CLAW #767.

## Verified results

| Classification | KG occurrences |
| --- | ---: |
| `ambiguous_mapping` | 0 |
| `exact_eligible` | 0 |
| `incompatible_scope` | 332,588 |
| `unavailable_evidence_export` | 116 |
| `unmatched` | 17,304,731 |
| Total | 17,637,435 |

There are **332,704 occurrences with an exact subject/object endpoint candidate**
and **116 with an exact subject/predicate/object candidate**. The latter 116
have only unassessed native candidates and are classified as
`unavailable_evidence_export`; this category records unavailable reviewed
evidence, not missing transport files. The remaining endpoint candidates have
different native predicates and are classified as `incompatible_scope`.
Endpoint coincidence does not establish equivalent scientific meaning or
organism, strain or genome identity.

The source header lacks the explicit `native_assertion` and `native_scope`
bindings required for inherited-review eligibility. Zero eligible occurrences
therefore does **not** establish zero biological overlap. The census covers the
declared exporter surfaces at their pinned commits; it does not assert that all
scientific evidence in the specialist repositories has been exported. It
creates **zero independent scientific reviews and zero KG approvals**.

## Persisted artifact and verification

The published artifact is
`workspace/validation-20261107/full-native-overlap-expanded/`, with adjacent
`full-native-overlap-expanded.run.json` and
`full-native-overlap-expanded.launch.json` records. Bulk data remains outside Git.
The small [manifest](full-native-overlap-20261107/census-manifest.json),
[run receipt](full-native-overlap-20261107/census-run.json) and
[launch record](full-native-overlap-20261107/launch.json) retained here are
byte-identical copies, checked with `cmp` and independently rehashed after
publication.

The artifact contains **882 nonempty Parquet partitions totaling 1,449,552,054
bytes**, ten native JSONL streams totaling **6,594,391,632 bytes**, and the source
and native manifest copies. An ignore-independent post-run file inventory found
904 regular files, including all 882 partitions and ten JSONL streams, with no
zero-byte files. No second full replay was run after the production driver.

The driver verified original source member hashes and row counts, reconstructed
the native catalogue from the copied envelopes, reconciled its complete native
accounting, and replayed occurrence identities, exact source-row bytes,
classifications and candidate bindings from every Parquet partition. It checked
partition hashes, schemas, row ordering and source reconstruction, then verified
the persisted classification totals through DuckDB. Publication occurred only
after those checks and file/directory synchronization completed. The adjacent
run receipt also records the driver's independent persisted-counter check.

Elapsed time including verification was **4,777.631127875065 seconds** (about
79.6 minutes). Peak parent-process RSS was **1,484,701,696 bytes**; this excludes
the four validation workers and is not a whole-process-tree memory measurement.
The source row limit was `null`, `complete_export` is `true`, and selected rows
equal all 17,637,435 source rows.

## Native accounting

| Accounting unit | Count |
| --- | ---: |
| Exported native assertion rows | 1,082,786 |
| Distinct native assertion IDs | 1,082,786 |
| Duplicate assertion rows | 0 |
| Evidence references | 7,339,857 |
| Distinct evidence bindings | 3,219 |
| Shared evidence references | 7,336,638 |
| Ancestry references | 5,998 |
| Distinct ancestry bindings | 2,612 |
| Shared ancestry references | 3,386 |

Distinct biological observations, native claims and independent experiments
remain explicitly uncounted (`null`). These reference and binding counters are
provenance accounting units; repeated references do not create independent
experiments or additional reviews.

## Frozen native inputs

The retained census manifest records each native source commit and assertion
stream SHA256 as well as the export manifest hashes below. The launch record
preserves the exact original input directories. The six expanded surfaces and
their source limitations are described in
[the expanded-input guide](native-expanded-inputs-20261107.md).

| Export surface | Rows | Native manifest SHA256 |
| --- | ---: | --- |
| MediaIngredientMech native decisions | 2,999 | `3b8166c8a30d95c5c56387c9bd80a1a7c482058a2d9d781e31b3c1496d176741` |
| TraitMech canonical examples | 784 | `7a1e5b5d9ff30e3b1db947c7facea76f43d967b48594ea72c7777e8fba1e545a` |
| HabitatMech existing record assertions | 1,831 | `484e037facef2e3f4edff792c5acfd52ac932a46b4af321f8526aca40e17d4c4` |
| TaxonMech GTDB mappings | 322,327 | `c12ca30e4adec18849311946fbbb27ee3045c1b3a2b845ef178f2db0ed6960a5` |
| HabitatMech BacDive associations | 3,081 | `56ec544212a597670bbaa10e876dce0abd8771172319afb3686affc55e02cd81` |
| HabitatMech PREGO associations | 8,807 | `2955d0c6b5e2d7435c419303d86a9d2208cebd00bf4cc4c7551c1d135479af14` |
| HabitatMech Madin associations | 1,378 | `dadf1f1f6a0a6eaf2ff6150d833c83d4c1bfb70bb70ed9504ed5604937ef91a3` |
| TaxonMech assembly links | 159,283 | `ea0a7a6ff94ccac499bc0a9604d3031918fd8a14bacc39193c982ed4f97e14d8` |
| TaxonMech genome-record links | 126,576 | `30c4bb2e8b6d6bfd578bc3f32e5f30acadab13d081445c9efbbf5cfebf97a2fa` |
| TaxonMech related-record links | 455,720 | `51bcc70ee72ee7721e44c7454e88a52fd877fa9ac17da17823ec8c89c8e25627` |

## Runtime and source provenance

The successful [representative canary](expanded-conformance-20261107.md) used
the same production launcher, `.venv/bin/python`, EdgeMech working directory,
default Bash login shell and `--workers 4` mode. The full run replaced its ten
representative inputs with the frozen complete exports and omitted `--limit`.
The census implementation and launcher remained unchanged throughout this run.
All 16 canonical runtime files matched CLAW commit
`1b5391d083ba85ac94e5279c3cba25ac4fde243c`.

| Provenance item | SHA256 |
| --- | --- |
| KG snapshot manifest | `f585e55a616d3771f382c91c78713cb8d74812c7ba177576090ccd5f9e6654b2` |
| KG edge member `merged-kg_edges.tsv` | `e6a846112ff8c769a8daa8a3c509c3390bd7b5e341c7998ce9188ebece9d4c9a` |
| KG producer provenance binding | `e16875d8302a81645593fc573eabdf4cb47284cd8bc62d8e71f6ff7eecc8e42f` |
| Published full census manifest | `a2b8353349816fd067ab3a7112fd1c2f5ee9c02971591ea52f31e9b981cbdd2e` |
| Published run receipt | `a834c68c214cf7f8d2770aa25b9d4f48d241526465bc44965c4fc12f05611fe2` |
| Exact launch record | `a4adf90d4099c38dd97fd2c058319bc9f4f13dfca62721c28d8d2987647ae237` |
| Census implementation | `2b90886fb21d1f42d3d718d936e1a09e37c935b1b23d5ff6cf4b266abfa73793` |
| Census launcher | `8d390030ae9c5f3ac909cc5ae5aa78d4c9b95ba6ce765810e772b2fc9debf9d4` |
| Preceding representative canary manifest | `a7bfc32251c1b7890ce6ed8a873c66cf02e87a0e7d1fa05a8c3532b1d2ac5e24` |

The source is the historical pinned intermediate snapshot under
`kg-microbe/data/merged/20260929`. Its legacy producer provenance is retained;
successful census validation does not certify that producer as clean or approve
a new KG-Microbe release. Specialist scientific-scope follow-ups remain separate
from transport conformance.
