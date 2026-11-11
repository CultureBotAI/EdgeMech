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
commit `f3c1568effad372dea6451292a9eb03c01174c36` after the three review fixes.
The earlier artifacts are retained; the final artifacts below supersede them.

| Artifact | SHA-256 |
|---|---|
| `workspace/chemical-scope-full-v2-notes-20261110.json` | `b2dbfcfc4ffe9140a9769f6542516cc50b567b2d5879d140e3d4578cc53c0816` |
| `workspace/chemical-scope-full-v3-20261110/bundle.json` | `1fecdea5b3c118d687096a3c3584fed95f5463ffd49d19501e2d8f543a700ccd` |
| `workspace/chemical-scope-full-v3-20261110/quote-proofs.json` | `919c7f5191945af69f24c7df5922b174f83e6eb06442c047e7424d445fac9199` |
| `workspace/chemical-scope-full-v3-20261110/manifest.json` | `8c2b1ac9b98f72f4f951306b6cac2572376fbf4793a8a280f92c40f43edfefa9` |
| `workspace/review-coverage-chemical-scope-v3-20261110.json` | `10ca5595dece2b4840849b7e37ec7185faaedf0e9e5ae434021e5d3be681d26a` |

Reproduction uses `scripts/adhoc/build_chemical_scope_review_20261110.py`, then
the existing adjudication and coverage launchers. The prior annotation SHA is
`6a3e8bd5f2c9ff5ffb61a88c61614b0d7211c3e118c7e44632f8914fe41f46a1`.
The reviewed cohort, retrieval and source-capture pins are inherited from PR #58.
Large artifacts and original tool responses remain in ignored workspace.

Read-only adversarial review found #60 (revision bytes hashed after parsing)
and #61 (source-value validation used the derived label). The follow-up review
confirmed those fixes and found #62, the same parsed-byte race in downstream
adjudication. All three were filed before fixing. Revision and annotation pins
now hash the exact parsed bytes, and exact source values
and encoding are checked separately. Mutation and identity-drift regressions
pass. Final local validation: **343 tests passed in 51.69 seconds**, the CI-scoped
Ruff check passed, and all 16 pinned CLAW contract files verified. A fresh
one-row canary preceded the final ten-assessment replay and coverage verification.

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

Upstream review findings #1837/#1838 subsequently added strict API record identity
and production input/freshness binding. A new canary and full production-path
`run/_fetch` replay consumed the same 35,425 cached records, with zero live fetches
or errors, and preserved the 36,512-label result. Its receipt SHA is
`0bc40292a3b19f176c64771209240fb167147c5f8251261d0f875a1ec7588219`.
The required record audit now binds API cache bytes, selected paths and GSS
selection. The replay recorded 665 absent API cache paths; existing cached web
fallback names are outside this API-specific guarantee. Canned cache misses are
not remote API evidence. The updated LPSN identity/admission suite has 88 passing
focused tests; full upstream validation is reported on PR #1836.

Upstream [PR1836](https://github.com/Knowledge-Graph-Hub/kg-microbe/pull/1836)
implements the citation repair and [issue1835](https://github.com/Knowledge-Graph-Hub/kg-microbe/issues/1835)
PREGO BTO label hydration from the existing declared ontology input. A one-ID
canary followed by the full 367-ID component replay supplied **367/367** labels
from the retained 2021-10-26 BTO authority, with explicit input/audit binding.
Its receipt SHA is `bc017d337a46f6e645913954c353689e9a8a9f2f4156eed4fc865e39e2f7d5e1`.
IMG and INSDC records still require owner-supplied names absent from these
retained inputs. Partial and obsolete EC identifiers have separate upstream
semantic issues. #36 remains a release and source-metadata follow-up: no pinned
graph bytes have been rewritten and no new release has been published.
