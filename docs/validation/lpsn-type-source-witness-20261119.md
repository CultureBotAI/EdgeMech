# Bounded LPSN type-field witness — 2026-11-19

Coordinator evidence for the [content-review implementation](content-review-execution-20261119.md)
and the original type-field linkage dependency. **This report is not blinded
reviewer navigation or a new categorical scientific assessment.** A bounded
clean-base replay succeeded; original historical execution remains incompletely
bound. No graph correction, release verification or calibration pass is claimed.

## Exact occurrence and recovered source path

Original occurrence:
`urn:kg-microbe:occurrence:v1:78725eeeea961ce059a55092aebc34b522b1b4ffc2ea844207ce7049a039cc80`.
Its assertion is `lpsn:781160 biolink:close_match kgmicrobe.strain:JCM-14905`,
relation `skos:closeMatch`, original `lpsn/edges.tsv` data-row ordinal **116674**.
The frozen qualifiers are `primary_knowledge_source=infores:lpsn`,
`knowledge_level=knowledge_assertion` and `agent_type=manual_agent`.

The literal `lpsn_gss.csv` data row **29573**, physical line **29574**, parses
identically to the frozen source record for *Stackebrandtia nassauensis*, record
781160. Its `nomenclatural_type` lists DSM 44728, JCM 14905, LLR-40K-21,
NBRC 102104 and NRRL B-16338. The complete source row was retained. The retained
API cache also matches the frozen record; it declares version 1, species scope,
and includes JCM 14905 among its type-strain names. Selected-record equality
does not recover a historical full-export hash.

The helper executes the actual owner `LPSNTransform.run()` against this one CSV
record. The species/subspecies branch calls `_extract_strain_deposits`, then
`_make_close_match_edge(record_no='781160', strain_curie='kgmicrobe.strain:JCM-14905',
inferred=False)`. Pinned owner constants select the predicate and relation;
no copied mapping rule supplies the result. The trace checks executed producer
code objects against compiled source bytes.

One source unit produced four deposit edges and five nodes, including exactly
one target JCM occurrence. Its seven emitted assertion/qualifier fields match
the original packet's known fields. Sibling outputs are retained, not additional
reviewed cases. NCBI/GTDB indexes were explicitly empty; parent records,
constructors, finalization and independent taxonomic joins were excluded. Only
transactional file handling was adapted to exclusive private output creation.

## Historical and semantic limits

The retained finalized TSV contains the matching assertion at **row 131469**.
At the original ordinal **116674**, it instead contains the different assertion
`lpsn:797610 biolink:close_match kgmicrobe.strain:LMG-29233`. Both were retained;
neither ordinal was rewritten. Row 131469 matches the replay's seven fields and
adds an empty `publications` column. This is a field comparison, not raw TSV byte
identity or recovery of the original literal transformed row/full qualifier set.

The producer and six support files match sampled clean base
`bcfa6bf5bfaa5fca23063fd1483d9fcbcb58a977` and inspected revision
`d6baf5b90003a2032747559d94c00f86a7a4c615`. Unknown historical dirty changes and
the source/build binding for original ordinal 116674 remain unresolved.
The original packet selector binds a relevant source record by identity/name;
it does not supply a historical field-to-emission trace.

Round03 E007 is separately retained later producer evidence at
`2d94ed094167d94402f21400a9ad7dc4f7f20438`. Its type-deposit branch uses a different
builder, direction and subclass representation. It was inspected, not executed
as a substitute or endorsed as a correction. E005/E006 are source captures
retrieved on 2026-11-16 without declared releases. E001 is Biolink 4.4.0, while
the retained finalization declares schema 4.4.2. These version scopes remain
distinct. A source type designation, relation semantics and species/deposit
identity still require separate assessments; the shared graph category does
not establish their equivalence.

## Retained execution and independent checks

M5 clone: `/Users/marcin/agent-work/EdgeMech/content-review-workers-20261119/lpsn-fresh14`.
Source attempt: `.temp/content-review-20261119/fresh14-canary01/`.
Native report: `.temp/helper-workers-20261119/fresh14/REPORT.md`.
Ending worker commit: `40068d21b40d63051eb7a8863912e18b343c5877`; only the new
source helper and focused tests were committed. The owner execution used the
preserved Python 3.10.11 environment; EdgeMech tests used isolated Python 3.14.7.
The nested owner's executable/version are recorded observations, not a new
independent reconstruction of its entire installed environment.

Separate read-only inspection verified all **40 artifact hashes**, all **12
current owner code/input pins**, frozen packet/source/occurrence copies, and
sampled versus later producer Git bytes. The ignore-independent attempt
inventory contains 41 files including the receipt. Files are 0600 and directories
0700. The completed report and committed helper/tests retain the inspected hashes.

| Artifact | SHA256 |
| --- | --- |
| Source receipt | `4abd9e189ae49c91c49a750507d7c402027170afc7127342269e7061f876151f` |
| Literal source record with header | `e8767a1a7001dcc1a88d254dc33f5ebc8d658d6b678bf99f6de9a02a8f03d1f6` |
| Raw emitted edge TSV | `234520c49a3a4a2e76cef8f4d0da8f1f5d4ef280f5f12dda7174e97d997458ee` |
| Helper `replay_lpsn_type_link_20261119.py` | `c8b2c4f85856816547a8c200207fc0407f7f56243a412150851c83173b61db55` |
| Native report | `cef13f728a315d78d8815120ad99e6f7085aee7bc4b5db9f24dc3f703bfbeb9a` |
| Full-suite log | `776fa46ae93ea40eb623e0c3d9c3824f23513c91b8c4a9c31b67dfd735b8a46e` |

The first free check failed on Python 3.10 descriptor handling before source
execution; its failure and partial outputs remain preserved. After repair,
fresh check02 passed before the single real canary. No helper/test changes
followed that canary. Retained logs independently confirm **21 focused tests**,
Ruff and **1,436 complete-suite tests** passed, the latter in 195.60 seconds.
These checks apply to this worker's candidate, not every subsequent PR integration.

No literature/provider request was needed. This evidence does not establish
M5 library access, biological truth, relation/category correctness, original
historical execution, or a final graph release. Recovering the original TSV and
adequate build/input/code provenance remains a separate dependency.
