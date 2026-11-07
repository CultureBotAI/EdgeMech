# Expanded native transport conformance, 2026-11-07

Six new native surfaces passed canonical packet transport, followed by a bounded
join of all ten representative export surfaces against the pinned KG-Microbe
snapshot. This advances the adapter conformance work in CLAW #767. The complete
expanded native inventory and all 17,637,435 KG rows have not yet been joined.

## Native packet checks

The unchanged retained launcher
[`run_native_packet_canary_20261107.py`](../../scripts/adhoc/run_native_packet_canary_20261107.py)
checked the manifest pin, payload hash, exact native envelope validation and
status counts, then passed the envelopes through `inherited_bundle`. It wrote a
fixture and canonical bundle, read the bundle back, and checked its exact
membership and content before writing a receipt. The first real BacDive packet
was verified on disk before the remaining representative packets ran through the
same launcher and environment.

Each new packet contains one unassessed native assertion, one canonical transport
observation and one deferred/withheld decision. Each contains zero claims and
zero canonical reviews and creates zero scientific approvals. The observation
fingerprints a candidate packet; it is not a newly asserted biological assay.
The fixture explicitly declares `native_export_transport_fixture` and
`kg_release_occurrences: false`. These checks do not claim that an eligible KG
match was found.

| Native surface | Persisted bundle bytes | Bundle SHA256 | Exact receipt |
| --- | ---: | --- | --- |
| Habitat BacDive association | 7,496 | `afa9314965d5e55d88e5a60ffa8d9f3e410c58fe682f91c0a7bbc6ee3311560e` | [BacDive](expanded-conformance-20261107/packet-bacdive.json) |
| Habitat PREGO association | 7,625 | `121f8543d908eb11fafc0619a683b609f3a397bcb1911e87234cd8c8902e44bd` | [PREGO](expanded-conformance-20261107/packet-prego.json) |
| Habitat Madin association | 7,324 | `c2e1f093777ed90ce4a5327c9cfde64e1a2d0f795d1ee59877406b566d69ef9a` | [Madin](expanded-conformance-20261107/packet-madin.json) |
| Taxon assembly link | 8,323 | `f1b7ce46aaa29c2d4d2a4c9baee0d33f33200a007aba3f40ccfa554c14be5d13` | [Assembly](expanded-conformance-20261107/packet-assemblies.json) |
| Taxon genome-record link | 8,818 | `2c1daf7250e27b8b2654eecd75c20afeafe146880ced7d76cbbd8fb66b7893ae` | [Genome record](expanded-conformance-20261107/packet-genomes.json) |
| Taxon related-record link | 8,527 | `2c440c86ddb63b662ed2c6cf072003e2ada93e0b5346be26fac2bd02f7653e62` | [Related record](expanded-conformance-20261107/packet-related.json) |

All six bundles and receipts were independently rehashed after their launcher
completed. The original artifacts remain outside Git under
`workspace/validation-20261107/native-packet-expanded-{bacdive,prego,madin,assemblies,genomes,related}/`.
The small receipts retained here are byte-identical copies. The native source
manifest and assertion-stream hashes are recorded separately in every receipt.

Habitat predicates remain unprojected `habitatmech:characteristic_taxa`
associations. Taxon predicates retain the native `genome_assemblies`,
`genome_records` and `related_records` slots, exact accession versions, source
qualifiers and owner-binding limitations. The full native envelopes survive the
canonical conversion unchanged; neither association transport nor shared
endpoints grant organism, strain or genome identity.

## Representative bounded join

The unchanged production
[`run_census_20261107.py`](../../scripts/adhoc/run_census_20261107.py) ran with
`--workers 4 --limit 1000`. Its input was the three-row MIM canary, one example
each from the existing Trait, Habitat and Taxon canaries, and one row from each
of the six new surfaces above: 12 native assertions across ten pinned exports.
The [retained manifest](expanded-conformance-20261107/census-manifest.json) records
all ten input manifest hashes and their immutable source commits.

The driver verified all selected native rows, source member hashes and persisted
native replay, then independently read the stored Parquet classification counts.
The published result contains 1,000 KG occurrences, all unmatched, with zero
eligible matches and zero approvals. Endpoint and subject-predicate-object
candidate occurrence counts are also zero for this bounded prefix. Its single
Parquet partition is nonempty at 85,908 bytes and has SHA256
`ed2ae15a0ef626fac334ea5e570cbcaf8dcdc9a6e710989f9561f40a35833ae3`.

The 12 native assertions have 72 evidence references and 33 distinct evidence
bindings; six ancestry references resolve to four distinct ancestry bindings.
These are provenance accounting units. Native biological observations, claims
and independent experiments remain uncounted (`null`).

The [run receipt](expanded-conformance-20261107/census-run.json) reports 133.619
seconds including verification and peak parent-process RSS of 219,316,224 bytes;
worker memory is excluded. It verified all 16 shared contract files at CLAW
`1b5391d083ba85ac94e5279c3cba25ac4fde243c`.

| Provenance | SHA256 |
| --- | --- |
| Original KG snapshot manifest | `f585e55a616d3771f382c91c78713cb8d74812c7ba177576090ccd5f9e6654b2` |
| Expanded representative census manifest | `a7bfc32251c1b7890ce6ed8a873c66cf02e87a0e7d1fa05a8c3532b1d2ac5e24` |
| Expanded representative run receipt | `15125b3610b55cf00bdfaa3e91ae544c9e50f9901990fbb7cfd88931f8338769` |
| Census implementation | `2b90886fb21d1f42d3d718d936e1a09e37c935b1b23d5ff6cf4b266abfa73793` |
| Census launcher | `8d390030ae9c5f3ac909cc5ae5aa78d4c9b95ba6ce765810e772b2fc9debf9d4` |
| Native packet launcher | `9c663e96e5d83d64dc3cc9372cbf07b9dbcd077857775687985805424aaf1d90` |

The original bounded artifact remains under
`workspace/validation-20261107/expanded-representative-conformance/`, with its
adjacent `.run.json` receipt. The manifest and receipt above were independently
rehashed after publication. Bulk native payloads and Parquet remain outside Git.

The KG snapshot header lacks explicit native assertion and scope bindings.
Zero eligibility therefore does not establish zero biological overlap. This
check covers representative exporter surfaces and an initial 1,000-row KG
prefix; it does not replace the complete census after the final exports freeze.
