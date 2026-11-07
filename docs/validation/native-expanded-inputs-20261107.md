# Verified expanded native inputs, 2026-11-07

Six complete native exports are frozen for the expanded KG-Microbe overlap
census: 13,266 HabitatMech selected source associations and 741,579 TaxonMech
typed strain links. They supplement the existing four native exports; the
earlier Habitat decision and Taxon GTDB mapping artifacts remain unchanged.
All six additions contain **unassessed** assertions, zero independent
scientific reviews and zero approved KG occurrences.

The complete JSONL files remain outside Git in their native worktrees. Small
byte-identical manifest copies are retained beside this document. Each hash
below was independently recomputed from the persisted output after its producer
completed exact byte, ordered membership and status reconciliation.

## Frozen producers and contracts

| Producer | Reviewed PR head | Native source commit |
| --- | --- | --- |
| [HabitatMech #2313](https://github.com/CultureBotAI/HabitatMech/pull/2313) | `73eed5f64fe550b6d6b7c640d53384c72e13abff` | `3b232e8a50ac434e4c1131edc43fb39ba0af10e3` |
| [TaxonMech #229](https://github.com/CultureBotAI/TaxonMech/pull/229) | `9495d5939df1135f0c71e28c9d5194a12d2e0f9c` | `ab35a0d0a0a2b47d250145db0c15b414fccbfdb8` |

Both use the immutable CLAW native-assertion contract at
`1b5391d083ba85ac94e5279c3cba25ac4fde243c`, prerequisite
[CLAW #962](https://github.com/CultureBotAI/culturebotai-claw/pull/962).

| File | SHA-256 |
| --- | --- |
| Habitat `src/habitatmech/edge_observations.py` | `c5ac597214f5502bc8aa94edb443f7a13fae3648ff6c5ea03500ba9c14ad6032` |
| Habitat `tests/test_edge_observations.py` | `951ab9298d3b0607197e733f8442248174af82e109a54bf9d4bddbf4d3277488` |
| Taxon `src/taxonmech/edge_links.py` | `c422f95a82d2c39b0935fdb35d216f45a88093909174e599fbadcb5d9932aa2d` |
| Taxon `tests/test_edge_links.py` | `e21c02ba5395d2cd95253860f9240c9d4d155bc66406e83ae8bede8b7cc67344` |

Independent read-only reviews checked both implementations and then the exact
PR heads, source hashes, docs and canary receipts; no new blocking finding was
identified. Native code remained unchanged throughout all six full exports.
The final worktrees were clean. These PRs remain unmerged; review completion
does not authorize a merge.

## Full export manifests

`HABITAT` denotes
`/Users/marcin/Documents/VIMSS/ontology/Mechs/HabitatMech-edgemech-adapter-20261107/build/edge-curation-20261107/observations-v1`.
`TAXON` denotes
`/Users/marcin/Documents/VIMSS/ontology/Mechs/TaxonMech-edgemech-adapter-20261107/build/edge-curation-20261107/links-v1`.
Each directory contains `manifest.json` and `assertions.jsonl`.

| Persisted directory | Rows | JSONL bytes | Manifest SHA-256 |
| --- | ---: | ---: | --- |
| `HABITAT/bacdive-full` | 3,081 | 18,250,331 | `56ec544212a597670bbaa10e876dce0abd8771172319afb3686affc55e02cd81` |
| `HABITAT/prego-full` | 8,807 | 52,830,916 | `2955d0c6b5e2d7435c419303d86a9d2208cebd00bf4cc4c7551c1d135479af14` |
| `HABITAT/madin-full` | 1,378 | 7,883,998 | `dadf1f1f6a0a6eaf2ff6150d833c83d4c1bfb70bb70ed9504ed5604937ef91a3` |
| `TAXON/assemblies-full` | 159,283 | 1,114,645,457 | `ea0a7a6ff94ccac499bc0a9604d3031918fd8a14bacc39193c982ed4f97e14d8` |
| `TAXON/genomes-full` | 126,576 | 871,511,827 | `30c4bb2e8b6d6bfd578bc3f32e5f30acadab13d081445c9efbbf5cfebf97a2fa` |
| `TAXON/related-full` | 455,720 | 3,213,453,029 | `51bcc70ee72ee7721e44c7454e88a52fd877fa9ac17da17823ec8c89c8e25627` |

| Retained manifest | Assertions SHA-256 |
| --- | --- |
| [Habitat BacDive](native-expanded-inputs-20261107/habitat-bacdive-full.manifest.json) | `ce6818181deb7338c985706c5c93f81b6510ac95125c4364914cc84e3dfd3ba1` |
| [Habitat PREGO](native-expanded-inputs-20261107/habitat-prego-full.manifest.json) | `84e603a585f8c7bf36b380cd47360ea55144bdd7b8c70a49252b9037b970965a` |
| [Habitat Madin](native-expanded-inputs-20261107/habitat-madin-full.manifest.json) | `4613ce2182fc61b632a3f965fc86d3a694a2925f319948a594a2dd0b21cc8f4f` |
| [Taxon assemblies](native-expanded-inputs-20261107/taxon-assemblies-full.manifest.json) | `c5b08c188721f403ccd7bc9a8a49aadb92aa674cd3e4040105c393b046ef817f` |
| [Taxon genome records](native-expanded-inputs-20261107/taxon-genomes-full.manifest.json) | `d598e805ad39d80ea68640eab1a06fa8f5e66d75e9c2990235eb7cf90e571ff7` |
| [Taxon related records](native-expanded-inputs-20261107/taxon-related-full.manifest.json) | `874253031ca6790647e917caaded7fe619f6856fb74ea96cb5302eb95fedbe3e` |

The copied manifests retain ordered assertion/source-position membership
digests, complete native source-file hashes, native source counts, four-worker
mode, status counters and explicit excluded surfaces. They are producer input
receipts, not the full KG census result or scientific approval records.

## Real canaries preceded each full export

Every surface first passed a free complete-input preflight, then one real source
row (`--positions 1`) through its production module and durable publisher.
Persisted nonempty files, hashes, row counters and unassessed scope were checked
before the corresponding `--all` run. Independent review also inspected all six
canaries on disk. All used the same nonlogin Bash shell, Python environment,
source pin, output parent and `--workers 4` mode as their full exports.

| Canary directory | Rows / JSONL bytes | Manifest SHA-256 |
| --- | --- | --- |
| `HABITAT/bacdive-canary` | 1 / 5,869 | `155742a8f807502c20bfad000fbb4190d0435b0b05fc3363af73c03dab1ee846` |
| `HABITAT/prego-canary` | 1 / 5,998 | `d3f2e4eedf9bada324283120fcb3cb6ffd1878eded4ccbbbfeb2e8138f19e302` |
| `HABITAT/madin-canary` | 1 / 5,697 | `0da75e6cf1a4102f1df4f33640eac6bc4dfb1ffc8d3c7a80d5271d3737697c5f` |
| `TAXON/assemblies-canary` | 1 / 6,696 | `b669e8cce1708487a05c3a40092a6b1df7652fa2fd4523ea78ba73c1cbf90503` |
| `TAXON/genomes-canary` | 1 / 7,191 | `f859f3500ca5631a98f0548dc94899c9bd41551e55deef847e8a446065c09356` |
| `TAXON/related-canary` | 1 / 6,900 | `3cb531b5a45a10f66c6b6dd68fa38e26981faba6a4fa605c26b49b391fd0938d` |

The retained producer launchers are `python -m habitatmech.edge_observations`
and `python -m taxonmech.edge_links`. Exact commands and canary payload hashes
are in the native PRs' committed guides:
`docs/edge-source-associations-20261107.md` and
`docs/edge-typed-links-20261107.md`. The interpreter was the adjacent CLAW
implementation worktree's `.venv/bin/python`, with each native `src` plus the
detached `culturebotai-claw-edgemech-contract-1b5391d/src` on `PYTHONPATH`.
No provider calls or credentials were used.

Every generated envelope validates with the pinned shared contract. Work is
bounded to four workers and 256 submitted rows, retaining source order.
Persisted binary hashes and ordered membership must equal the validated stream
before publication. The reviewed publisher exclusively creates a destination,
flushes payload and directory entries, and publishes the manifest last.

## Preserved scientific limits

Habitat exports transport the native `habitatmech:characteristic_taxa` slot
with explicit unprojected source-association scope. They retain complete owner
and association rows. BacDive strain counts remain distinct from taxon candidate
pools; PREGO rank, score, direct flags and channels retain source meaning; Madin
has no invented rank or score. Selected inventories can omit upstream candidates.
Grounding review does not review each association. Characteristicness, growth,
habitat preference, negative observations and causality are not inferred.

Taxon predicates remain `taxonmech:genome_assemblies`,
`taxonmech:genome_records` and `taxonmech:related_records`. Supplied accession
versions, typed database IDs and GOLD organism/project/analysis chains stay
distinct. Exact lexical owner bindings preserve full rows and hashes without
normalization or new joins. Source taxonomy does not establish strain identity
or overwrite classification. Genome records may describe plasmid or draft scope.

The 147 assembly, 74 genome-record and 445 related-record matched-owner gaps
remain explicit; no subject-owner gaps were observed. Nested AllTheBacteria and
StrainInfo evidence, nomenclature, strain/deposit equivalence and reviewed KG
projections remain outside these flat profiles. External primary-source files
named in the native manifests were not fetched or reverified.

[Habitat #2311](https://github.com/CultureBotAI/HabitatMech/issues/2311) and
[Taxon #226](https://github.com/CultureBotAI/TaxonMech/issues/226) are advanced
by this source transport and remain open for exact assertion evidence/review
and the excluded scientific scopes. Endpoint overlap alone cannot approve any
current KG occurrence. Zero eligible reviewed overlap must not be interpreted
as absence of biological overlap.

## Native validation evidence

The final mandatory integration jobs passed without skipped feature tests:

- Habitat head `73eed5f64fe550b6d6b7c640d53384c72e13abff`: 28 passed in 1.86 s,
  [job 128546587893](https://github.com/CultureBotAI/HabitatMech/actions/runs/42420140646/job/128546587893).
- Taxon head `9495d5939df1135f0c71e28c9d5194a12d2e0f9c`: 35 passed in 2.79 s,
  [job 128549111840](https://github.com/CultureBotAI/TaxonMech/actions/runs/42420973396/job/128549111840).

Both native full repository quality gates were still running when these input
receipts were frozen. No extra native commit or full rerun was made just to
record final export hashes. Final CI readiness and the complete KG census result
are recorded separately once those checks finish.
