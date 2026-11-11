# Chemical scope decisions and upstream metadata repairs

The three remaining #41 chemical assessments now have explicit `concern`
decisions under the [finite policy](../chemical-scope-policy.md). Positive
product evidence is retained with `partial` support: the cited measurements
do not establish the graph object's exact anionic scope. No biological
refutation, replacement chemical, identity approval or KG admission is inferred.
This completes these review decisions, not native normalized-claim construction.

The same ten-occurrence pilot now contains **6 supported and 4 concern**
assessments, with no unknown outcome. The fourth concern is the earlier
mixed-medium assertion tracked in #56. All ten literal quotation proofs were
reconstructed in the coverage pass: four retained abstracts and six original
paper tool-text captures. Extraction limitations remain unchanged. The other
453 cohort occurrences remain deferred; this is not a new ten-occurrence cohort.

The builder checks exact occurrence and row identities, subject, predicate,
chemical object, source column/record, source value and original citation.
It rejects identity authorization or exact-support promotion. The canonical
review pins the prior annotations, three decision records and policy document;
coverage independently rehashes those inputs. Earlier artifacts are unchanged.

A one-occurrence Basfia canary persisted a canonical bundle and a verified
three-line source quotation before the full revision. The initial invocation
rejected a short Git revision before creating output; the corrected invocation
used the full commit identifier. Full artifacts were generated from implementation
commit `3455b56751b91383c165932ff310a41c0cf59ae6`.

| Artifact | SHA-256 |
|---|---|
| `workspace/chemical-scope-full-notes-20261110.json` | `e8bf046636b2b10ccc1a9a2fe6f118557db7465182ad1a02d35cc7080f6ec58b` |
| `workspace/chemical-scope-full-20261110/bundle.json` | `d1455966083393f21f52d5706944cf22c1b01ebbdb7ca863e6f7a5c5b8ecf08f` |
| `workspace/chemical-scope-full-20261110/quote-proofs.json` | `919c7f5191945af69f24c7df5922b174f83e6eb06442c047e7424d445fac9199` |
| `workspace/chemical-scope-full-20261110/manifest.json` | `763f0869f9192fca705bfac81ed3785398f6cd86afa2e7b23d34a5a2e932195e` |
| `workspace/review-coverage-chemical-scope-20261110.json` | `f3c97271f4fc2f367b7831618acda00b47b681d6e1e558a4776ec4c199c5127d` |

Reproduction uses `scripts/adhoc/build_chemical_scope_review_20261110.py`, then
the existing adjudication and coverage launchers. The prior annotation SHA is
`6a3e8bd5f2c9ff5ffb61a88c61614b0d7211c3e118c7e44632f8914fe41f46a1`.
The reviewed cohort, retrieval and source-capture pins are inherited from PR #58.
Large artifacts and original tool responses remain in ignored workspace.

For #36, current upstream KG-Microbe already repairs blank-name merge precedence
and has explicit native-backed ENVO dispositions. A bounded eight-EC public
merge replay recovered the existing ontology names in a persisted archive;
this verifies the current fix rather than changing the historical release.

New upstream [issue1834](https://github.com/Knowledge-Graph-Hub/kg-microbe/issues/1834)
preserves unique source-owned LPSN bibliographic citations as display labels,
with source-field provenance. An offline one-record canary preceded a replay
of 35,425 retained API records through the production emitters. This supplied
labels for **36,512** previously unnamed IDs: 19,209 DOI and 17,303 PMID nodes.
Twenty-one DOI IDs had conflicting citation strings and remain unresolved.
These are verbatim citation labels, not independently verified article titles.
The source-cache audit does not establish full transform selection or merged
release coverage. Its receipt SHA is
`86e9bb438bc8fa87348ba2fbf5e3bdbc58b1b933fab22f5d56eb35ba50cef918`.

Upstream [issue1835](https://github.com/Knowledge-Graph-Hub/kg-microbe/issues/1835)
tracks PREGO BTO label hydration from the existing declared ontology input.
IMG and INSDC records still require owner-supplied names absent from these
retained inputs. Partial and obsolete EC identifiers have separate upstream
semantic issues. #36 remains a release and source-metadata follow-up: no pinned
graph bytes have been rewritten and no new release has been published.
