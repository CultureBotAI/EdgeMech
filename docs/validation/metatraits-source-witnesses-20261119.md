# Bounded MetaTraits source witnesses — 2026-11-19

Coordinator evidence for issues [#71](https://github.com/CultureBotAI/EdgeMech/issues/71),
[#72](https://github.com/CultureBotAI/EdgeMech/issues/72) and
[#205](https://github.com/CultureBotAI/EdgeMech/issues/205). This report is not
blinded reviewer navigation or a new categorical scientific assessment.

## First43: original negative aggregate and positive predicate

Original occurrence:
`urn:kg-microbe:occurrence:v1:2cad956c7d5d6ace49ddb7e887de8eab4a7c1b78410942732e2a44bbd1a00559`.
It connects `NCBITaxon:1540872` to `METPO:1005039` through
`biolink:capable_of` / `RO:0002215`, original MetaTraits data row 820840.

The frozen packet and exact raw source line 10486 agree on the selected summary
at `/summaries/124`: nitrogen fixation, negative 100%, ten observations from two
databases. The actual pinned mapping loader and owner `_process_single_file`
Tier 1 branch reproduce a positive capability predicate with `has_percentage=0.0`.
The separate fallback polarity routine does not run. The zero qualifier is
preserved evidence and must remain part of any future semantic comparison.

The helper executes complete compiled owner methods against one unchanged
selected summary, with a pinned source projection and guarded I/O. It does not
recreate the mapping rule. One edge, two nodes and an empty indeterminate stream
were retained. Owner output has eight row cells under ten headers; absent
`value`/`unit` cells normalize to empty. The original finalized TSV additionally
has an empty `publications` column. All semantic field values match under this
explicit normalization; the raw TSV forms differ and both are retained.

The [execution record](content-review-execution-20261119.md) contains artifact
hashes and exact environment/commit identities. Independent read-only inspection
verified 31 retained artifact hashes, 17 current owner code/input pins, byte-identical
historical packet/source/occurrence copies, and the producer at both claimed
Git baselines. The successful source receipt SHA256 is
`5144dfe483f0b56ac7f7710961ee5dd9d6caae721f1dc5570c87844390005f24`.

The taxon cache is seeded from the frozen subject and label; taxonomy resolution
was not independently replayed. Constructor, full-data transform and finalization
were not executed. Current retained template bytes and their declared release
do not establish which inputs an unknown historical dirty build consumed.
The negative source aggregate does not independently refute the biological
ability. This witness closes a bounded mapping/emission dependency; independent
source semantics, original identity and the complete assertion including its
qualifier still need scientific adjudication. Existing round 03 labels stay intact.

## First28: conditional GTDB source-to-emission witness

The bounded first28 replay and independent readback completed on M5. This
establishes mapping and emission given the frozen subject; original taxon
selection and source-field meaning remain unresolved. No biological category
conclusion, new six-axis assessment or increased review coverage is claimed.

Original occurrence:
`urn:kg-microbe:occurrence:v1:177815c9e4c39684189e2004e17840e6f0c42a2824750aad5d7f95bd7c0e5f3e`.
It connects `NCBITaxon:113559` to `METPO:1000870` through
`biolink:has_phenotype` / `RO:0002200`, original
`metatraits_gtdb/edges.tsv` data row 96074 (physical line 96075).

The original source is **GTDB** `data/raw/gtdb_species_summary.jsonl.gz`,
not first43's NCBI source file. The frozen packet and raw line 1498 agree on
taxon `Actinoplanes campanulatus` and the zero-based selector `/summaries/58`:
`sporulation`, discrete, positive 100%, three observations from two databases.
The source archive SHA256 is
`cb2fa59208200105a9473b792c94a45ae41abc24583a37eeaec4c5e4c3d84a63`;
the retained original line SHA256 is
`9b86a8dcb8611265b9cbe758a96f1a9202ae985c8d58aa2d6a17ba81405e3f42`.

The helper selects the actual `MetaTraitsGTDBTransform` subclass because the
original source and occurrence are GTDB-specific. It executes the actual
`load_metpo_mappings("metatraits synonym")`, mapping construction and inherited
`_process_single_file` Tier 1 emission. The trace also records the GTDB
`_search_ncbitaxon_by_label` and `_pick_ncbi_id` methods. The GTDB subclass
SHA256 is `4d15aaba4b793a6e0c63fbe51f035168c765d061f7ae8752ad8e861924d30ca7`,
matching both inspected owner Git baselines
`bcfa6bf5bfaa5fca23063fd1483d9fcbcb58a977` and
`d6baf5b90003a2032747559d94c00f86a7a4c615`.

The replay seeds `Actinoplanes campanulatus` to the frozen
`NCBITaxon:113559` with a synthetic singleton weight of one. That weight is not
recovered genome evidence. The real selection method runs, but this seed does
not exercise the original candidate set, counts, preferred species or tie
resolution. It therefore does not establish why the original build selected
that NCBI subject, or independently establish source-cell biological identity.
The generic source field `sporulation` still lacks its original definition;
the selected target's endospore definition does not supply one or prove spore
type. Current templates declare METPO `2026-06-12`, but their retained bytes
do not establish the unknown historical dirty build's inputs. Constructor,
full-dataset transformation, finalization, deduplication and independent
taxonomy resolution were not replayed.

One edge, two nodes and an empty indeterminate stream were retained. All named
edge fields match the original, including `has_percentage=100.0`,
`primary_knowledge_source=infores:gtdb-metatraits`,
`knowledge_level=observation` and `agent_type=automated_agent`. As with first43,
the raw owner row has eight cells under ten headers; absent `value` and `unit`
cells normalize to empty, and the original additionally has empty
`publications`. This is field equality under explicit normalization, not TSV
byte equality. The frozen subject and mapped trait are emitted as nodes;
empty node descriptions/enrichment do not establish appropriate node categories.
The emitted edge SHA256 is
`7032a93ce936f3f30aad3917b49daa9dc5acb2caa9ef03d19f7873fba1e56e1e`.

## First28 execution and audit boundary

M5 checkout:
`/Users/marcin/agent-work/EdgeMech/content-review-workers-20261119/metatraits-followup`.
Source outputs are under
`.temp/helper-workers-20261119/first28/implementation/` in that checkout.
After extending the helper, a new `first43-recanary01` replay and persisted
readback completed before `first28-followup01` started. Independent read-only
inspection verified all 33 retained artifact pins and 17 owner code/input pins
for the new first43 run, and all 34 artifact pins and 18 owner code/input pins
for first28. These are new source receipts, distinct from the original first43
receipt and helper described above and from the native worker launch receipts.

| Artifact | SHA256 |
| --- | --- |
| Extended `scripts/adhoc/replay_metatraits_discrete_20261119.py` | `9c9e285a95a3be067c3602dabe5943c5386143a5670b7cdee0be151792c08795` |
| `tests/test_metatraits_discrete_replay_20261119.py` | `58cc7fd775a4c00bdd3b21a3aa97077673a2365c8a0f9b0110f1a999a4a5a251` |
| `first43-recanary01/receipt.json` | `f89bf0d358af6400685cbf117cf00faf19e43df837b6ae318a786a2033ecfa6b` |
| `first43-recanary01/independent-readback.json` | `d0413ff2f44a688888dae28e4e18f999340c140ff6c976a707bbc16b7f48855f` |
| `first28-followup01/receipt.json` | `5ddb7ab9dc4ea8d6b69686c87edd2272225872368bf0edefb1e5362fcd953e5a` |
| `first28-followup01/independent-readback.json` | `b51d267a31b49892c866841ef394fdfd9dc49d2b0cbb4aaa32e2f8ba1af239e8` |

Both replays used the preserved owner interpreter
`/Users/marcin/agent-work/EdgeMech/pr1871-cleanup-20261119/preserved-worktree-artifacts/payload/.venv310/bin/python`,
Python 3.10.11. Their before/after runtime inventories match at SHA256
`5af90d0be1a4dc3810db4e835198b9fb89591431eb826f4b09d72297f26d8dfe`:
51,735 inventoried files, with 15 credential-named package paths explicitly
excluded without reading them. This bounds runtime drift checks; it is not a
complete historical or transitive runtime attestation. No owner runtime repair
or installation occurred. An initial plan rejected credential-named inventory
paths; its failure is preserved, and the exclusion fix was tested before the
successful plans and fresh canary.

Validation passed: 39 focused tests, Ruff and all 1,431 suite tests. The M5
worker ended cleanly at `ad6f9ab12c7216a295a423de014f76e779541ae1`; the source
commit was collected locally as `9ee7afb`. Native completion and report copies
are retained under `.temp/m5-source-witnesses-20261119/first28/` locally.
`completion.json` SHA256 is
`512014ed202d0cc1294ff56c5cb211dfd9ed83fd5dff135baeb82b2ca1e9fb14`;
`REPORT.md` SHA256 is
`7fbec0ff053dfef9deaeed38a88e6ee564906540aad03a01ab354e9bd4a90a48`.
The native completion and its coordinator check establish helper completion,
not scientific acceptance. The full private report retains additional pins,
command paths, original source/packet bindings and attempt history.

Read-only adversarial review discovered
[#221](https://github.com/CultureBotAI/EdgeMech/issues/221) **after the successful
replays**: failure handling can itself fail while re-reading an unavailable
runtime or owner path, before persisting `failure.json`. The successful receipts
remain valid within the limits above. The original finished clone and receipts
remain preserved; repair acceptance is recorded separately below.

## Failure-record repairs and fresh M5 re-canaries

Commit `131669b0fed293201238c432bb36ba2b6ecf8df0` repairs #221 and the
Python 3.10 compatibility finding
[#222](https://github.com/CultureBotAI/EdgeMech/issues/222). Unavailable runtime,
owner and helper diagnostics are recorded separately, with unknown after-state
rather than a false unchanged flag. If failure storage itself is unavailable,
the original exception propagates with a separate stderr diagnostic. Focused
tests passed **54/54**, and separate read-only review passed. Source selection
and emission were unchanged.

A fresh M5 clone, `content-review-workers-20261119/metatraits-repair-221`, was
provisioned at that exact commit. The stdlib negative smoke check then ran under
the actual retained Python **3.10.11**, where exception notes are unavailable.
All four persisted scenarios passed: removed synthetic runtime, removed synthetic
owner input, existing failure-file collision and injected permission denial.
Independent inspection confirmed preserved original errors, private artifacts,
unknown after-state and unchanged existing failure bytes. This checks synthetic
error paths; it does not inspect or modify the real owner environment.

The committed `recanary_metatraits_20261119.sh` driver then used the same clean
environment and owner interpreter for both real source cases. Both free plans
passed. First43 replay, separate readback and direct row inspection passed before
first28 was launched. First28 replay and separate readback also passed. Each
emitted edge file is byte-identical to its preceding retained owner output;
comparison to the finalized original still uses the stated empty-column
normalization. The fresh clone's tracked files remained clean at `131669b`.

Separate read-only inspection rehashed all **67 artifacts** across the two
replays and all **22 distinct owner code/input files** represented by their
17/18 per-case pins. Both free plans preceded first43; first43's persisted
readback preceded first28's helper snapshot. All eight before/after runtime
inventories match the earlier `5af90d0b...` inventory. Original worker commits
and receipts remain unchanged. No source or scientific interpretation changed.

| New artifact | SHA256 |
| --- | --- |
| Repaired source helper | `827079a6623b3f4837c75a8435544a6412c3db6f2b2e7a479745b1de249bc562` |
| Committed common driver | `21e9098b1f0a295d52d35b8f804f2794c718a934d4b82cd1176312231c8c3deb` |
| Python 3.10 smoke result | `a8c3a74b547d0f735d50b025e75ec5123c2d032cb9feee360959ee87360b8c88` |
| New first43 source receipt | `802fee59bf98446d1664d8d29f986b242cfcdf5f9461e0476ad9167ae3fc5e37` |
| New first43 readback | `e284270a96e3085a6311b22826c37e6bd4e7dd9931363b36ae31fb0277318b6b` |
| New first28 source receipt | `ff79d28fe1f524620d5cc8ffdf19b52a955ee78c589a7210fda6bf71c5a3fa32` |
| New first28 readback | `fd3fdd59288af7847693b73142f77f01a0c6dee3a4369dfceb2648457a298300` |

The smoke result is in `.temp/failure-runtime-smoke-222-m5-20261119-v1/`;
source receipts/readbacks are in
`.temp/source-recanary-221-20261119/{first43,first28}-canary01/`; stdout/stderr
are retained separately under `.temp/repair221-checks/`, all in the fresh clone.
The coordinator invoked these bounded offline checks through the committed
driver; they are not an additional native scientific-review session. The source
and identity limitations above remain unchanged.
