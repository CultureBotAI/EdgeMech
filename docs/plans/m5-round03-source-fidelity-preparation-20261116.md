# Round03 source-fidelity preparation — 2026-11-16

This is a **coordinator-only** preparation note. It was written after inspecting
the failed round02 results and adjudication; it must not enter a blinded
reviewer package. The case-neutral section below may be separately extracted,
reviewed and pinned as common instructions. Do not expose the historical case
map, judgments, disagreement counts or feasibility prioritization to reviewers.

The [original protocol](../../artifacts/edge-calibration-20261115/protocol.json)
still controls all ten occurrences, six axes, denominators and thresholds.
This note supplies no new scientific ratings and changes no old artifact.

## Case-neutral common rubric for separate review and extraction

Source fidelity asks whether the original occurrence preserves the meaning of
the particular source assertion from which it is derived. It requires both an
exact source binding and a semantic comparison. These are distinct from whether
the biological proposition is independently true, whether a paper supports it,
and whether the graph uses an appropriate formal relation or node category.

For each occurrence, state the original predicate, endpoints and qualifiers;
identify the exact source version, record, field and applicable identity chain;
then explain the source-to-assertion translation. Preserve the source's level
of aggregation and reporting scope. A record describing a source report cannot
silently become an experimentally established biological property.

Use the existing categories as follows:

| Category | Required reasoning and evidence |
| --- | --- |
| `SUPPORTED` | The exact source instance and necessary identities are bound, the relevant field's meaning is established, and the occurrence preserves the asserted content, polarity, specificity and qualifiers at the stated source scope. Missing independent biological validation does not by itself defeat this source-level judgment. |
| `CONTRADICTED` | The exact binding and semantic witnesses demonstrate an unfaithful transformation: for example, reversed polarity, an identity/equivalence relation between independently incompatible source identities, substitution of a different kind of source assertion, or a known mapping that adds unsupported specificity. State precisely which source meaning changed and how the mapped field is known. This category concerns fidelity of the transformation; it does **not** require or establish biological falsity. |
| `NOT_ASSESSABLE` | A necessary source-instance, identity, field-selection, definition, unit, qualifier or transformation witness is missing or internally conflicting, so the asserted source meaning cannot be established. Give the exact missing witness. An unproven explanation of how the edge was generated is not evidence of a particular transformation defect. |
| `UNASSESSED` | The assessment has not been performed; it is not a completed unresolved judgment and cannot remain in a completed calibration matrix. |

Apply these distinctions consistently:

1. **Byte preservation is necessary but insufficient.** A matching row, hash,
   copied identifier or reproducible generated ID establishes preservation or
   a production rule. It does not establish semantic equivalence, biological
   validity or faithful transformation.
2. **Proven overreach differs from an unknown derivation.** If the selected
   source field and mapping are established, demonstrably adding a narrower
   concept can be unfaithful even when the narrower biological proposition
   might independently be true. If the generating field or mapping is unknown,
   a plausible overreach story must remain unproven. Merely failing to find a
   specific phenotype in a partial source view is not biological negation.
3. **Do not automatically copy a modeling verdict.** A formal domain/range or
   bearer problem can coexist with faithful preservation of a source's process
   assignment. It affects source fidelity only when evidence shows that it
   changes the represented source meaning. Conversely, a well-typed assertion
   can still reverse a source's polarity or conflate distinct source identities.
4. **Respect statistical and measurement scope.** A minimum, maximum, growth
   observation, optimum, range, bin membership, fractional weight and prevalence
   are different quantities. Preserve units and percentage basis when supplied;
   do not invent them. A known conversion must be supported by the source and
   producer rule. Missing context matters when it is necessary to interpret the
   original assertion, rather than as an automatic penalty for every source.
5. **Resolve the identity chain actually used by the assertion.** Conflicting
   fields do not authorize choosing whichever identity supports a desired
   conclusion. An unrelated bad crosswalk does not automatically invalidate an
   independently established chain used by the literal endpoint. Explain which
   fields participate, why, and which conflicting fields remain unresolved.
6. **Keep biological evidence separate.** A matching primary paper may support
   the organism's property, but cannot retroactively assign a mixed source row
   to that organism or repair a source transformation. A quarantined row proves
   a producer disposition, not the original trait's truth or falsity.
7. **Bind every necessary witness initially.** The source-instance record,
   exact identity authorities, field/term definitions and relevant producer
   rule must be explicit in the initial axis evidence IDs. Mentioning a source
   in rationale prose is not a replayable binding. Freeze the authored draft,
   evidence roles and matrix together; do not add support after sealing and
   call the earlier matrix unchanged.

Missing evidence remains an assessed limit. Agreement on unresolved categories
counts only toward the applicable agreement calculation, not the resolution
floor. Never choose a category to reach a threshold or to make a save succeed.

## Coordinator diagnosis of the failed round

The [round02 result](../validation/m5-calibration-round02-results-20261116.md)
records six source-fidelity disagreements and four agreements. Three
disagreements were resolved separately; three remained unresolved, leaving
source-fidelity resolution at 7/10 against the fixed minimum 8/10. The
independent audit checked unsupported resolved claim/model labels; that audit
does not prove source-fidelity agreement or supply its missing witnesses.

The disagreement pattern shows different questions being answered: copying a
source field, preserving that field's meaning, proving a specific producer
error, or deciding whether one of several conflicting identities supplied the
trait. The common rubric must distinguish those questions before new scoring.
Do not turn this diagnosis into expected case labels in reviewer instructions.

| Historical case | Preparation issue and necessary additional witness |
| --- | --- |
| first-01 | A recorded test outcome, its general assay procedure, and the observation target required by the original predicate are different objects. Retain the exact test record, historical relation constraints and manufacturer procedure meaning together. |
| first-28 | Distinguish the directly bound generic source field from the narrower mapped endpoint. A proven specificity-changing transformation is a source-fidelity issue without biological refutation. |
| first-32 | Both identifiers being present in one record does not establish their semantic equivalence. Bind the independent identities and the original relation explicitly. |
| **first-30** | Round02 did not bind the actual quantitative field and derivation of the halophily assertion. The bounded local trace below supplies a promising new witness, subject to actual owner-function replay and independent interpretation. |
| **fresh-04** | Row10677 combines Paludifilum/BacDive132033 with DSM102218/CSURP2414; the independent identities do not agree. The meaning of the fractional `NaR_3_to_8=0.25` datum is also unresolved. Need a source-owner or original-data trail assigning the datum to a particular culture, plus the bin/weight definition. An independent organism paper alone does not decide either issue. |
| **fresh-05** | Row8521 combines Rubritalea/BacDive17851 with DSM19353/JCM14586, which resolve to another organism. Need provenance identifying which source entity supplied the phenotype cell. Independent type-strain nonmotility and the later quarantine do not repair that missing association. |

The bold cases were the three final source-fidelity gaps. This is a historical
gap map, not a new adjudication. Retain all original matrices and outcomes.

## Bounded first-30 source/producer trace

Read-only inspection on M5 found a concrete source-field chain absent from the
round02 scientific package. The observed canonical KG checkout was clean for
the two inspected producer files at commit
`d6baf5b90003a2032747559d94c00f86a7a4c615`.

The frozen occurrence is
`urn:kg-microbe:occurrence:v1:b912410040f3b6027290e16710d457e3e45753a38d8a5adda78f0a8ea423eb9b`:
`GTDB:s__SYIM01_sp009921765` to `METPO:1000625`, with original
`metatraits_gtdb/edges.tsv` data-row ordinal 2984816. The retained edge carries
value `1.8`, unit `%NaCl(w/v)` and `has_percentage=100.0`.

In the retained `data/raw/gtdb_species_summary.jsonl.gz`, JSONL line 54895 names
the exact GTDB species. Its source summaries report salinity minimum 0.0,
salinity growth 0.0, and salinity maximum 1.8, each as a median in percent NaCl
w/v from 27 observations and one database. These are source statistics, not a
new independent biological measurement or a proof of any universal optimum.

The inspected owner implementation is
`kg_microbe/transform_utils/metatraits/metatraits.py`:

- Lines 2650–2655 select the named salinity summaries into separate `sal_min`,
  `sal_max` and `sal_growth` fields.
- `_classify_salinity_phenotypes`, lines 1712–1749, selects the slightly
  halophilic label when the maximum is at least 1 and below 3, then carries
  `sal_max` into the output value and `%NaCl(w/v)` into the unit.
- Lines 2766–2790 emit the resulting phenotype through `has_phenotype`.
- `MetaTraitsGTDBTransform` inherits this implementation from
  `MetaTraitsTransform`; its own file declares that superclass and loads the
  same METPO label lookup. The frozen target definition is optimum-based, so
  this maximum-based classification is a concrete semantic question to assess.

The retained `data/transformed/metatraits_gtdb/edges.tsv` at physical line
2984817 (one header plus data-row ordinal) contains the exact subject,
predicate, object, value and unit above. Its byte hash matches the retained
`source_finalization.json` member hash. This is stronger evidence than matching
only a current trait label or an unbound numeric value.

| Inspected artifact, relative to canonical KG checkout | SHA-256 |
| --- | --- |
| `data/raw/gtdb_species_summary.jsonl.gz` | `cb2fa59208200105a9473b792c94a45ae41abc24583a37eeaec4c5e4c3d84a63` |
| `kg_microbe/transform_utils/metatraits/metatraits.py` | `85d6687fa6ac1af3a11203a7f01b9bf3d387c06a23010ab651a89a4fad06cc3e` |
| `kg_microbe/transform_utils/metatraits_gtdb/metatraits_gtdb.py` | `4d15aaba4b793a6e0c63fbe51f035168c765d061f7ae8752ad8e861924d30ca7` |
| `data/transformed/metatraits_gtdb/edges.tsv` | `4a99138ab98ac453be014f636f4e2f31eb7d0565e652f60f28c76cfacb26c9ab` |
| `data/transformed/metatraits_gtdb/source_fingerprint.json` | `7538fd0f2739f1f40146b834ac355c4c848cae114ac8b1f0c06a6a50dd65c6d9` |
| `data/transformed/metatraits_gtdb/source_finalization.json` | `9b4f5d374f1cdcd38f05e54474563723a3d1828cfc0ca6dc29946c8d3fa8cece` |

The full parent producer file at sampled-release base
`bcfa6bf5bfaa5fca23063fd1483d9fcbcb58a977` has the same `85d6687f…` byte hash;
`git diff --exit-code` between that base and `d6baf5b` for the file was empty.
The classification comment entered history at commit
`070fb82a4594ebbbcf5855d4e4603c37dafa0c14` (2026-04-06). This comparison does
**not** recover an unknown dirty working-tree diff from a build described as
`bcfa6bf5b-dirty`, nor prove the complete sampled build's code/input chain.
The raw-file hash, exact record/edge match and matching finalization member
are direct retained witnesses; the complete historical build remains a limit.

Before using this material in fresh scoring, save a small repository helper
that reads the exact pinned source record and invokes the actual owner
classification function in an isolated pinned KG runtime. Do not reimplement
the threshold logic in the helper. Run exactly that one case, check regenerated
node/edge/value/unit bytes, preserve its receipt, and obtain separate semantic
inspection against the original endpoint definition. Pin all necessary
source-instance, definition, code and replay witnesses in the new package.
The current read-only trace is not that live production replay or a new rating.

## Feasibility gate before fresh reviewer fan-out

If the seven previously resolved cases remain resolved, at least one of the
three historical gaps must acquire a defensible resolved assessment to meet
8/10. The first-30 trace is the best bounded local lead found here. Its actual
owner-function replay and independent semantic interpretation should precede
fresh scoring. Confirm that the new evidence resolves the missing field-chain
question without inventing biological truth or historical build provenance.

If that replay or interpretation remains inconclusive, and neither mixed
BactoTraits row gains a genuine identity-to-datum witness, the available
evidence still supports at most the prior 7/10 resolution. Report that evidence
blocker; do not spend another reviewer round merely to retest an unattainable
floor. A corrected clone origin, a successful save, a source-report schema
extension, an ontology repair or better agreement on unknowns cannot supply
those missing source witnesses. No guaranteed future labels or pass are implied.

Inspection included ignored files within the explicit M5 source, transform,
mapping, private calibration and adjudication directories. No source bytes,
historical ratings, graph outputs or owner files were changed. No fresh
external retrieval, owner contact, reviewer launch, merge or publication was
performed by this audit.

## Executed bounded owner-method replay

On 2026-11-16 the saved helper
`scripts/adhoc/replay_first30_salinity_20261116.py` executed one selected record
on M5 using
`/Users/marcin/agent-work/EdgeMech/m5-kg-bactotraits-release-20261116/.venv310/bin/python`
(Python 3.10.11). The owner checkout was the canonical path above at
`d6baf5b90003a2032747559d94c00f86a7a4c615`. The helper imports the canonical
`MetaTraitsGTDBTransform`, verifies its inherited methods against compiled code
from the pinned parent file, bypasses the dataset-loading constructor, and
calls the actual `_load_metpo_lookups`, `_parse_quantitative_value` and
`_classify_salinity_phenotypes`. It contains no replacement classification
thresholds. Bytecode writes are disabled.

The invocation used the unchanged round02 `first-30` packet as its input and
wrote only a new private directory in the round03 worktree. `run-01` succeeded;
after adding the issue number to the helper header, the same one-record replay
was repeated as `run-02` to bind the final helper bytes. Both outputs remain.
The final invocation, from the M5 round03 worktree, was:

```sh
/Users/marcin/agent-work/EdgeMech/m5-kg-bactotraits-release-20261116/.venv310/bin/python -B scripts/adhoc/replay_first30_salinity_20261116.py --kg /Users/marcin/Documents/VIMSS/ontology/KG-Hub/KG-Microbe/kg-microbe --original /Users/marcin/agent-work/EdgeMech/m5-calibration-round02-20261116/.temp/edge-calibration-20261115/first-30 --output .temp/first30-owner-replay-20261116/run-02
```

The actual parser returned minimum `0.0`, growth `0.0` and maximum `1.8` from
three distinct source fields. The actual classifier was called with the
minimum and maximum, as at the pinned producer call site. It returned
`METPO:1000625`, `biolink:PhenotypicQuality`, `slightly halophilic`,
`biolink:has_phenotype`, value `1.8` and unit `%NaCl(w/v)`. These predicate,
object, value and unit strings agree with the retained edge. Every retained
edge column was also compared with the frozen occurrence's source row. The
full retained edge-file checksum and byte count agree with its finalization
member. Both parent and child producer files have the same inspected hashes
at `bcfa6bf5bfaa5fca23063fd1483d9fcbcb58a977` and
`d6baf5b90003a2032747559d94c00f86a7a4c615`.

The actual owner lookup read pinned `data/raw/metpo.json`, SHA-256
`fbef7ad9b436b28c59d142876eac3d98ffcf1777edab33a67e35fabd841d391a`.
The selected class ID, label and definition match the frozen endpoint. Its
definition concerns optimal growth; the consumed field is explicitly the
maximum. Independent semantic assessment must decide how that distinction
affects source fidelity. The replay assigns no scientific categories.

The final private result is
`/Users/marcin/agent-work/EdgeMech/m5-calibration-round03-20261116/.temp/first30-owner-replay-20261116/run-02/replay.json`
(8,969 bytes), SHA-256
`1f3ee584897966ffc1075f926f4cad7d28dcc68e6084fd10eb9ee3406ea39d61`.
The bound helper SHA-256 is
`6fcacd2ae12fc128829c0ec9cc2ff270a2db9e72925e48c5cfda9eb265fb4d47`.
The result records all raw, packet, ontology, code and edge pins, and contains
checksummed copies of the exact selected raw JSONL record, edge header/row,
ontology target node, finalization member and both owner producer files. The
copied raw line has SHA-256
`31bda54f2e42a4fa6396f89d62186539768425bccef29298c2d61231b06d991d`;
its parsed JSON equals the retained canonical-text record whose existing hash
is `e837c6090d7b2e748fd8f3ce2cb24bee9acf482c244183b303fe409e5bf44614`.
The different byte hashes reflect the recorded serialization formats.
The nonempty result, helper pin and resulting values were read back after
execution. All pinned owner/source inputs were rehashed before persistence.

`tests/test_first30_salinity_replay.py` passed all 15 focused tests. They cover
source identity, duplicate/missing fields, discrete/quantitative disagreement,
changed units or values, immutable byte pins, occurrence ordinals, changed
retained edges, a same-name substituted method with the original path/module,
a wrong imported path, and a definition change hidden behind the same label.

This is a successful bounded method replay, not a complete transform or
graph-build reproduction. Taxonomy resolution, the constructor, writer path
and underlying experiments were not rerun. It does not establish the unknown
`bcfa6bf5b-dirty` build state or prove that the maximum establishes the
organism's optimum. The earlier feasibility gate now has a concrete replay
witness; a separate semantic review is still required before freezing the
fresh evidence package. The prior failures and ratings remain unchanged.

## Review correction: standalone output privacy (#188)

Independent review found that the original helper depended on its parent
directory and the launcher's umask for privacy. Inspection on M5 confirmed
`.temp` was already `0700`, while the replay parent and `run-01`/`run-02`
directories were `0755` and their files `0644`. Those replay directories were
restricted to `0700` and all fourteen existing files to `0600`; SHA-256 checks
before and after the permission-only correction matched for every file.
Their contents and earlier receipt pins remain unchanged.

The helper now explicitly creates each missing output directory with mode
`0700` and each exclusive output file with mode `0600`. It leaves preexisting
ancestor permissions alone and refuses to overwrite existing output files or
reuse a run directory. The new regression test executes these persistence
functions with umask `000` and checks actual filesystem modes, bytes, hash,
unchanged ancestor permissions and overwrite rejection. All 16 focused tests
and Ruff checks passed. Scientific replay logic is unchanged.

The latest executed helper SHA-256 is
`fbfc48ee36f2debd9eb8a50e3afa77f35b3f1a3920f8d0c5ac3744a953093ab8`.
It completed the same one-record M5 invocation under umask `000`, changing
only the new output destination to
`.temp/first30-owner-replay-20261116/run-03`. Its `replay.json` is 8,969 bytes
with SHA-256
`b79a181d650c6030c6df16507093cc66852e20b456bd491500756e1b86f8a4f1`.
This is the current receipt for the helper after the review fix; `run-01` and
`run-02` remain historical evidence.

Readback verified `.temp`, the replay parent and `run-03` at `0700`, and all
seven `run-03` files at `0600`. The six copied scientific/code witnesses have
the same byte hashes as earlier runs. The actual owner-method output is
unchanged: maximum `1.8`, `METPO:1000625`, value `1.8`, unit `%NaCl(w/v)`.
No verdict or historical-build claim is added by this privacy correction.
