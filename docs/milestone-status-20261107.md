# EdgeMech milestone review — 2026-11-07

This work implements the next #766/#767 stages of the
[2026-11-03 plan](https://github.com/Knowledge-Graph-Hub/kg-microbe/blob/5b785fafba6eeb52adf3ff5dae349ca1e284dbe1/docs/plans/edge-curation-implementation-20261103.md).
The plans remain an architecture baseline, not a claim that later browser,
scientific review-worker, production queue or publication milestones have shipped.
Every PR below remains unmerged; merges require explicit human approval.

| Repository / PR | Deliverable | Dependency or remaining scope |
| --- | --- | --- |
| [CLAW #962](https://github.com/CultureBotAI/culturebotai-claw/pull/962) | Shared artifact/native assertion contracts and reviewed semantics | Final adversarial review complete at `6031604c`; all five CI checks passed; ready for human merge decision. |
| [CLAW #987](https://github.com/CultureBotAI/culturebotai-claw/pull/987) | Minimal canonical contract distribution for native consumers | Depends on #962; final review and all six CI checks passed at `326bdff8`; MIM dependency adoption remains open. |
| [EdgeMech #2](https://github.com/CultureBotAI/EdgeMech/pull/2) | Repository scaffold, routing, lossless SQLite migration, external Parquet/DuckDB, native packets and complete census | Full census and source/output parity verified. Runtime contract pin `1b5391d083ba85ac94e5279c3cba25ac4fde243c`; all 16 imported files checked. See the PR's final exact-head CI/readiness audit. |
| [CLAW #953](https://github.com/CultureBotAI/culturebotai-claw/pull/953) | Explicit post-cutoff infrastructure admission, preserving historical DUF release bytes | [#960](https://github.com/CultureBotAI/culturebotai-claw/issues/960) implemented; current-main integration and public sync repairs reviewed under [CLAW #997](https://github.com/CultureBotAI/culturebotai-claw/issues/997) and [CLAW #1004](https://github.com/CultureBotAI/culturebotai-claw/issues/1004). A fresh consumer dry/apply canary passed. See the PR's final exact-head CI/readiness audit. |
| [MIM #1147](https://github.com/CultureBotAI/MediaIngredientMech/pull/1147) | Pinned ingredient decision export | Final review and all 17 CI checks passed at `8ec80235`; [#1144](https://github.com/CultureBotAI/MediaIngredientMech/issues/1144) advanced by CLAW #987. |
| [Trait #2082](https://github.com/CultureBotAI/TraitMech/pull/2082) | Owner-bound canonical examples and exact-observation evidence inventory | Final review and all nine CI checks passed at `39bc45b6`; ready for human merge decision. [#2083](https://github.com/CultureBotAI/TraitMech/issues/2083) remains open for exact observations and their reviews. |
| [Habitat #2313](https://github.com/CultureBotAI/HabitatMech/pull/2313) | Native decisions plus BacDive, PREGO and Madin source associations | Final review and all five CI checks passed at `73eed5f6`; ready for human merge decision. [#2311](https://github.com/CultureBotAI/HabitatMech/issues/2311) retains scientific review and projection work. |
| [Taxon #229](https://github.com/CultureBotAI/TaxonMech/pull/229) | Native mappings plus separate strain-to-assembly, genome-record and related-record links | Final exact-head review and all three CI checks passed at `9495d593`; all full exports verified; ready for human merge decision. [#226](https://github.com/CultureBotAI/TaxonMech/issues/226) retains exact reviews, nomenclature and excluded nested evidence. |
| [Site #541](https://github.com/CultureBotAI/CultureBotAI.github.io/pull/541) | Infrastructure membership without an invented scientific corpus | Final review and CI passed at `1642cf7c`; semantic check matches admission candidate; ready for human merge decision after CLAW admission. No site deployment performed. |

## Preserved scientific boundaries

The four baseline native export surfaces contain 327,941 assertions. MIM has
2,999 mapping decisions (1,747 supported and 1,252 withheld). Habitat has 1,831
native decisions (424 supported and 1,407 unassessed). Trait contributes 784
unassessed canonical examples from 1,130 owners; Taxon contributes 322,327
unassessed mapping rows. Their exact input manifests and source commits are
recorded in the [validation evidence](validation/20261107.md).

The baseline combined canary completed: all 327,941 native assertions and 1,000
selected KG rows were independently verified and persisted. All selected KG rows
were unmatched; it created zero approvals. This bounded result preceded the
[completed full census](validation/full-native-overlap-20261107.md): all
17,637,435 KG occurrences and all ten complete exports, containing 1,082,786
distinct native assertions and 6,594,391,632 native JSONL bytes. Its launcher,
interpreter, shell, environment and four-worker mode matched the expanded
representative canary. Independent native and exact KG/Parquet replay finished
before atomic publication. The final receipt and nonempty files were read back
and verified.

The full result contains 332,588 incompatible-scope occurrences, 116 whose
exact native candidates remain unassessed (unavailable reviewed evidence),
and 17,304,731 unmatched occurrences; ambiguous
mapping and exact eligibility are both zero. There are 332,704 endpoint-candidate
occurrences, including 116 exact subject–predicate–object candidates. The KG
header lacks complete native assertion/scope bindings, so zero exact eligibility
does not establish zero biological overlap. No scientific approvals were created.

The 882 Parquet files total 1,449,552,054 bytes. Elapsed time including verification
was 4,777.631 seconds; peak parent RSS was 1,484,701,696 bytes, excluding workers.
The manifest SHA-256 is
`a2b8353349816fd067ab3a7112fd1c2f5ee9c02971591ea52f31e9b981cbdd2e`;
the run receipt is
`a834c68c214cf7f8d2770aa25b9d4f48d241526465bc44965c4fc12f05611fe2`.
The six added Habitat/Taxon surfaces have passed real native export and canonical
packet canaries. The [expanded bounded join](validation/expanded-conformance-20261107.md)
also passed: 12 native assertions from all ten surfaces and 1,000 KG rows, all
unmatched, zero approvals, with independent persisted replay. This bounded
conformance proof does not establish full-population coverage.

Supported native status is inherited within the exported native scope. It does
not approve a KG occurrence, create a claim or count as an independent scientific
review. Transport packets retain the original native payload, locators, evidence,
review status and limitations; canonical decisions remain deferred/withheld.
Unknown distinct observation, claim and experiment counts remain unknown.

The [expanded input inventory](validation/native-expanded-inputs-20261107.md)
pins all six new complete exports. Habitat adds 13,266 unassessed source
associations: 3,081 BacDive, 8,807 PREGO and 1,378 Madin rows. It preserves
source counts, score/rank channels and selected-subset boundaries. These rows
do not establish growth, habitat preference or causality, and no reviewed KG
predicate projection is invented. Exact association reviews and projection
remain in Habitat #2311.

Taxon adds 741,579 unassessed typed links: 159,283 assembly, 126,576 genome-record
and 455,720 related-record links. Versioned accessions, original fields and
GOLD organism/project/analysis chains stay distinct; a linked assembly or
record does not establish strain identity or taxonomic equivalence. Unmatched
owner records remain explicitly unavailable. Mapping-specific reviews,
nomenclature, excluded nested ATB/StrainInfo evidence and reviewed KG
projections remain in Taxon #226. Neither expanded adapter promotes transport
validation to scientific review.

The census uses the historical 20260929 KG-Microbe snapshot, with recorded
producer `1408e7099-dirty`; it does not rename that input as a current production
release. Full-population transport accounting and endpoint candidates do not
measure all biological overlap across the Mechs' scientific corpora.

## Review and gate disposition

The local reader contract (`edgemech-reader/v1`) now defines pinned exact detail,
bounded ID search, query-bound pagination and verified artifact streaming. It
does not deploy a browser or authorize publication. Its 12 focused tests and
independent review passed. The isolated final storage repair passed the complete
183-test EdgeMech suite, lint and the canonical contract pin check. Its wheel and
source archive built, and the extracted archive collected all 183 tests.
That exact repair commit, `872492f6e959758dd3cbe79daf3035403a70e112`, was integrated
after the full census finished. Census code, its launcher, Parquet helpers,
schemas, packets and contract pins have no diff from the frozen execution.
Two additional readiness regressions passed separately. The final PR CI runs
the complete suite once; the exact-head result is retained with the PR handoff.
The [integrated package check](validation/final-package-20261107.md) rebuilt
both artifacts, verified their changed files and collected all 185 tests from
the extracted source archive.

The read-only final readiness helper uses a separately hash-pinned
[expected-check inventory](validation/pr-readiness-expected-checks-20261107.json).
Independent [workflow-policy review](reviews/pr-readiness-policy-review-20261107.md)
confirmed every applicable PR job against the frozen workflow trees and changed
paths; the inventory is not inferred from the response under test.
It verifies the reviewed head, open/non-draft/clean state, every expected check
and successful completion; a missing workflow cannot pass merely because the
reported subset is green. EdgeMech #17 records that review finding and its two
passing regressions. The one-PR live canary saved and verified all five checks
for CLAW #962 at `6031604c`; its retained
[receipt](validation/pr-readiness-canary-20261107.json) hashes to
`d699d8294c0fd90773bc15c8ab44a37c70a1824c94c09a410a808d88ca68b4d8`.
Use the final nine-PR audit retained with the PR handoff for exact-head CI
readiness; it does not supply merge permission. CLAW #990 records the corrected stale
admission-status sentence in the #962 PR body, without a source change.

The final storage acceptance review filed EdgeMech #14 and #15 before repairs.
Production migration now compares independent SQLite and persisted Parquet
complete-field hashes and row counts for all five authoritative tables before
publication. The evidence report also verifies the pinned source digest and
unchanged migration input-hash maps. Independent read-only review, four mutation
controls, a real 1,000-row canary and two subsequent layout measurements passed.
The [source-parity proof](validation/storage-source-parity-provenance-20261107.md)
retains the exact implementation hashes, mutations and real receipts.
These shared-host measurements establish integrity and local layout costs;
they do not select a production layout or establish a performance improvement.
EdgeMech #18 corrects the README admission status. #19 expands Ruff to all test
modules while preserving one full pytest invocation and the existing PR trigger.

Independent adversarial passes found and filed durability, publication race,
runtime pin closure, reporting provenance, source packaging, native persistence,
catalogue scaling and Arrow transaction-lifetime defects. In-scope repairs are
included in their owning PRs, with negative controls and real persisted canaries.
The [catalogue evidence](validation/native-catalog-20261107.md) retains the
interrupted run and measured defect rather than presenting it as a successful run.

CLAW #960 now has a separate immutable infrastructure admission declaration.
The historical DUF release declaration, historical cohort applicability and
governed payload bytes remain unchanged. Admission activates only through its
protected first-parent introduction; candidate tests and the local canary do
not activate it. Only the exact empty EdgeMech bootstrap may be reported as
pending installation, and that state verifies zero installed payloads.

The real consumer canary at policy commit `ce87c61d813fb26e78d0d2e4475967424074cc2c`
used the clean EdgeMech feature head `ea2503df9ffdbf9cb6b6ae82b3c0ba32d272f3d2`.
Dry-run and apply-mode no-op both verified all 19 working and committed artifacts
plus the exact data pin, with zero planned/applied changes. Persisted receipts
were independently rehashed: dry `c946ac224216c78d6c4ddd7c19f27929e705c7ed4d93d2395e0c0c260634d4a5`,
apply `8707cf3e10034604af02908477fbc9bd11f8adcf279bb60ea6aa48a1d96e6e74`.
Final scoped review confirmed that all 19 governed files and the pin still match
that clean EdgeMech canary head. The later readiness helper, reports and #19
test-lint change are outside the governed set; the historical no-op proof is
not relabeled as a new clean-head canary.
Before the subsequent main integration, candidate CI passed at `85a69ee2164a3c9e70e0ffd8a9c33038ab84d716`:
7,898 tests passed, 446 skipped, 87.77% coverage; the safety-module coverage gate
passed at 77%, and CI mypy passed across 103 source files. All five checks are
green at that historical head. Review findings #982, #984, #986 and #988 cover
bootstrap completeness, receipt-path aliases, actual source-object binding and
explicit rejection of invalid fetch refs; each was filed and repaired before
the canary. Earlier cohort assumptions were repaired under #963.
The first final CI run also found workflow coupling to a fleet-specific policy
filename (#989). Its reviewed repair uses only the generic protected selector,
preserves the existing manifest-derived workflow assertion, and leaves the
verified policy/helper bytes unchanged. The repaired head `85a69ee2` passes the
authoritative fleet audit: 185 candidate tests, plus 45 completeness tests with
one skipped, and the protected historical fourteen-consumer audit.

The final readiness audit then detected a real conflict with newly advanced
CLAW main `081e9c8f44c5ce28849e162b7fecac1b3ba17ad7`. The review finding was
filed as [CLAW #997](https://github.com/CultureBotAI/culturebotai-claw/issues/997)
before integration. Upstream now permits checksum-valid current payload revisions;
the repair separates those revisions from an exact packaged admitted-manifest
snapshot. The snapshot remains bound to the unchanged `7e672227` source and
admission declaration. Current authority, layout, applicability and checksums
still validate; the historical fourteen-consumer cohort and its target bytes
remain fixed. The integration passed 124 focused tests, an independent review,
and three targeted mutation controls.

The required real dry-run canary then caught a public-sync mismatch before any
write or receipt: the ordinary synchronizer still required the historical pin
to match today's installed payloads. [CLAW #1004](https://github.com/CultureBotAI/culturebotai-claw/issues/1004)
records that finding and its repair. Only the exact admitted Edge identity and
declared source pin may select the separately authenticated old data. One
verified byte bundle flows through planning, transaction writes, post-verification
and rollback; the generic canonical verifier remains strict. Nine new public-path
tests, 51 existing governance/transaction/sparse tests, an installed-wheel
public-plan check, two targeted mutation controls and three read-only reviews
passed. [CLAW #1006](https://github.com/CultureBotAI/culturebotai-claw/issues/1006)
records the mutation harness's import-origin rejection and its correction;
the rejected run is not counted as a successful mutation proof.

The corrected real canaries used policy commit
`a099f2559e334bdec9941b1d25fb3f714d36add0` and the clean EdgeMech feature head
`375a86e9d0ae56533d73b54654867d55c29026e4`, with the same non-login Bash,
interpreter, launcher, environment and output parent for dry-run and apply mode.
Both persisted receipts verify 19 working and committed artifacts plus the exact
data pin, with zero planned/applied changes and protected admission inactive.
Their independently rehashed receipts are dry
`67e712957d5db6df26bcab37fdf628c454d8b8fa5eb530dd8261fde45009c851` and apply
`811436513d01591f8631f640aafcc2829b2e4b01421ae839366e7547e0b2a77c`.
These receipts supersede the earlier canary for the integrated policy without
relabelling its historical proof. The subsequent EdgeMech documentation update
changes no governed files, runtime, census inputs or outputs. Final CI and the
nine-PR readiness result are retained with the PR handoff; no merge is implied.

Two unrelated local findings remain filed: CLAW #965 concerns a stale local
ProteinTraitsMech checkout selected by fallback configuration; #966 concerns a
skill reference checker treating Git object-store metadata as a missing source
path. This work neither mutates that checkout nor weakens those checks. They
are separate from the repaired EdgeMech admission gate.

The minimal distribution in CLAW #987 advances MIM #1144 without upgrading its
native LinkML runtime. A six-package environment verified the real three-row
MIM export; a separate installed reviews environment passed 148 canonical tests
and checked all 13 imported Python module origins. The 11 packaging regressions
and all six CI checks pass, including 7,806 tests with 418 skipped in full CI.
Review finding #985 was repaired and checked by two failing mutation controls.
No registry publication or MIM dependency adoption has occurred.

MIM #1147's full CI reports 4,708 passed and 547 skipped; its separate mandatory
native tier passes 92 tests. Trait #2082's full CI reports 4,901 passed and 26
skipped; its separate native adapter/inventory tier passes 34 tests.
Habitat #2313's full QC reports 1,235 passed and 27 skipped, plus four structured
review-contract tests; its mandatory native integration tier passes 28 tests.
Taxon #229's final QC reports 1,132 passed, 34 skipped and five deselected,
plus four structured-review tests; all native quality gates passed. Its mandatory
native integration tier passes 35 tests. The authoritative QC job finished in
45m55s at unchanged head `9495d5939df1135f0c71e28c9d5194a12d2e0f9c`;
no native commit or rerun was made just to record completion.
Trait #2083 now has a complete pinned inventory: 784 canonical examples,
769 graph objects and 113 review documents, with no exact canonical-example
review selectors. The schema defines `observation_count` and `datasets`, but
none of the 1,130 pinned records carries `observation_count` or populated dataset
references. Existing notes and citations are preserved; exact assay/review
bindings are not invented. EdgeMech #16 records the correction from schema-level
absence to this measured instance-level result.
