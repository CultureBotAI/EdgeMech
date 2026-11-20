# Edge content review: current implementation plan

**Scheduling update, 2026-11-20 UTC:** the user requested M5 CLAW restart the
campaign with unreviewed occurrences first, then previously reviewed occurrences
using LBNL services. The [restart assignment](m5-edge-review-restart-20261120.md)
governs that new execution, replacing the W7-before-W8 cohort order and freezing
disjoint baseline queues while retaining the scientific calibration, evidence,
runtime, correction and resource gates. The November19 implementation record
below remains the engineering/evidence baseline.

Reconciled **2026-11-19** against main `f841b1d`, the reviewed prerequisite
candidate `27be00d` ([PR #211](https://github.com/CultureBotAI/EdgeMech/pull/211)),
and the completed calibration reports. This update addresses
[#213](https://github.com/CultureBotAI/EdgeMech/issues/213). The original November 9
design remains below as a dated baseline; its status and authorization statements
are historical. This section governs the next execution.

Implementation is in unmerged
[PR #214](https://github.com/CultureBotAI/EdgeMech/pull/214), stacked on #211.
The [execution record](../validation/content-review-execution-20261119.md) retains
three completed native M5 helpers, inspected source witnesses, typed adjudication
bindings, adversarial repairs and fresh source re-canaries at code revision
`131669b`. Engineering progress has not changed any scientific outcome or gate.

## Objective and assessment contract

Find and correct errors in exact edge occurrences and their endpoint nodes.
Account for all 17,637,435 frozen occurrences eventually; do not promise positive
literature support for every assertion. Start with the retained 100, including
the ten fixed calibration challenges. Repeated review adds assessment depth, not
new population coverage. Preserve every original assertion, source row and
multiplicity when proposing corrections.

Use the implemented [occurrence profile](../record-review-profile.md) over the
pinned CLAW contract. Every selected occurrence receives six **separate**
categorical assessments:

| Axis | Required question and evidence |
| --- | --- |
| Claim | Is the original statement supported as stated, contradicted, conflicting, insufficiently evidenced or not assessable? Preserve organism/strain, conditions, units, polarity, modality and original endpoint meanings. A source report is allowed only when that is the original proposition. |
| Literature | Does inspected text support, refute, conflict with or partly address the exact claim? Preserve explicit no-match, unavailable and not-applicable states. Verify DOI identity and short literal snippets with retained document hashes, offsets, extraction version and inspected extent. |
| Relation | Is this predicate, direction, specificity and qualifier set appropriate, beyond mere domain/range compatibility? Pin the applicable relation version. |
| Subject node | Independently assess identity, label, category, rank/type and definition against version-bound authority. A nonempty category or valid identifier is insufficient. |
| Object node | Apply the same checks independently, including quantitative bounds, units, endpoint conventions, statistic and process/assay meaning where relevant. |
| Source fidelity | Does the original edge preserve the source assertion's meaning? Use a directly bound semantic comparison where sufficient; recover the producer branch where selection, identity, polarity or mapping makes it necessary. Missing necessary provenance is not a contradiction. |

The profile defines the exact category vocabulary and shared-outcome mapping;
this plan does not create a second schema. `UNASSESSED` is unfinished work.
An assessed unresolved limit is a valid finding, but may still fail a calibration
resolution gate. Supported claims and incorrect modeling can coexist; persistence
must preserve that distinction. Transport validity, quote matches and reviewer
agreement are not scientific truth.

For each directional literature judgment, verify publication identity, organism
and strain, measured outcome, methods/conditions and entailment. Inspect the full
paper or relevant methods/table when an abstract cannot answer those questions.
Use alternate verified identifiers when no DOI exists and record why. Database
papers and inherited dataset DOIs do not establish each database assertion.
Keep supporting and contrary text; never manufacture a snippet or reinterpret a
biological claim as a report to obtain a passing label.

## Reconciled starting state

| Deliverable | State on 2026-11-19 |
| --- | --- |
| Inventory, retained100, complete packets, six-axis profile, abstract replay | Implemented on main through PRs #76/#94/#120/#128/#131. Earlier canary judgments are not a completed six-axis reassessment of all100. Remaining9,900 are unreviewed. |
| Operational calibration | Rounds01,02,03 completed and **failed**. Preserve their matrices, seals, rejected saves, evidence and reports. These are purposive challenges, not a gold standard or a population accuracy estimate. |
| Latest failed round | [Round03](../validation/m5-calibration-round03-results-20261116.md): initial54/60 overall, fidelity7/10 agreement and3/10 final resolution; unsupported initial judgments, unresolved disagreements and blinding failure. Mechanical20/20 canonical replay did not repair science. |
| Clone and save/readback repairs | [PR #211 live results](../validation/m5-prerequisites-live-20261117.md): two fresh M5 environments at `3057bb2`,380 bindings each, actual canonical save/readback passed after a preserved failed canary. These receipts apply only to those exact environments/packages/runtime. PR #211 and its calibration base stack remain unmerged. |
| Scientific invocation | Initial-review instruction/package/session binding implemented; full typed adjudication inputs tracked in [#209](https://github.com/CultureBotAI/EdgeMech/issues/209). Its existing fail-closed rejection is not adjudication readiness. |
| Evidence gaps | [Ten-case coordinator witness map](m5-source-fidelity-witness-map-20261117.md) names original selection, field-meaning, identity, bin, process-version and cell-lineage gaps. The map contains historical judgments and must not enter blinded reviewer navigation. |
| BactoTraits correction | Owner quarantine and EdgeMech evidence merged; bounded regenerated candidate verified. Full graph-release verification remains [#143](https://github.com/CultureBotAI/EdgeMech/issues/143). |
| Library use | Earlier public/CBORG service receipts are recorded in NEXT_TASKS. Failed licensed retrievals remain failures. PR #211 reused evidence without new literature retrieval; fresh05's round03 directional evidence was an abstract, not an inspected full paper. |

Current implementation disposition:

| Stage | November19 result / remaining work |
| --- | --- |
| W0 | Durable native launcher implemented, independently reviewed and exercised by three completed M5 helpers. |
| W1 | First43 and first28 conditional owner mapping/emission witnesses retained; repaired helper passed fresh first43/readback before first28/readback. Original field meanings, taxon selection and historical dirty-build limits remain explicit. |
| W2 | Typed initial-result/adjudication binding implemented and tested, including complete readiness lineage and aligned persistence instructions. Positive new scientific-session replay remains a W5/W6 prerequisite. |
| W3 | Fresh14 bounded type-field emission recovered. Original historical TSV linkage and the other cases' semantic/identity dependencies remain unresolved. |
| W4 | Matching fresh05 paper body extraction inspected; Valency metadata and failed retrieval outcomes retained. The new extraction is not yet a canonical paper proof and does not resolve mixed-row cell lineage. |
| W5–W8 | Pending/gated. Concrete next-package tasks are in #220 below; no new scientific round, retained-90 review or expansion has started. |

## Dependency-ordered implementation on M5

The user authorized implementation using M5 sessions and additional `codex-work`
or `agy-work` helpers on 2026-11-19. Work on a branch based on PR #211; do not
mutate old clones or frozen outputs. Merge still requires separate explicit
authorization. Resolve current sessions before launching: the old count of32
idle panes is not a current capacity measurement. The execution log and exact
receipts belong in [the November19 run record](../validation/content-review-execution-20261119.md).

| Stage | Concrete work, owner and dependency | Acceptance / stop condition |
| --- | --- | --- |
| W0: register execution | Coordinator reconciles branch/runtime, M5 sessions, wrapper, private output roots and current owner inputs. Implement a single-unit durable helper launcher, separate from scientific reviewers. | Plan mode is free; run exactly one helper end to end through the real wrapper/shell/output path. Verify nonempty report, events, exit status, hashes and runtime identity before another helper. Preserve failures; changed launch path requires a new canary. |
| W1: recover source witnesses | M5 source helper starts with **first43** MetaTraits mapping/polarity; only after its actual owner-code replay and persisted receipt pass, run first28 through the same helper. Pin original source row, loader, lookup/template, selected serial/worker branch and emitted qualifiers. | Actual owner implementation and exact mapping inputs, not a handwritten equivalent. Compare emitted bytes/meaning with the original occurrence. Separate sampled clean base/current replay from the unknown historical dirty build. No biological refutation inferred from a negative aggregate. |
| W2: bind adjudication | Contract helper implements #209 in parallel with W1. A separately frozen phase package binds the original package plus both reviewer identities, original matrices, receipts/seals and comparison. | Reject absent, swapped, stale, changed or premature inputs before launching. Replay original seals; preserve timestamps. Initial reviewer instructions remain blind. Meaningful negative tests and real retained-artifact replay precede scientific use. |
| W3: close remaining evidence dependencies | Coordinator prioritizes the witness map after W1: original type-field linkage; exact process-generation definition/version; LPSN subject authority; BactoTraits bin/weight meaning and culture/cell lineage; original GTDB identity. Assign bounded source-specific helper tasks. | For each dependency record established, conflicting or still missing, with original and current version scope. Do not treat producer-selected ID as proof of the culture supplying a phenotype. Do not silently replace missing historical inputs with a current snapshot. |
| W4: literature and correction work | Evidence helper replays retained citations before local provenance/Zotero and anonymous OA/appropriate LBNL channels. Start with one exact organism-matched paper needed by a calibration claim. Owner fixes proceed on separate branches with issue and regression records. | Retain service/request outcome, DOI/title identity, inspected extent, document/quote pins and scientific limits. One real retrieval unit before any batch; safe authenticated general-helper integration remains dependent on PR #102. Candidate verification and graph-release verification stay separate. |
| W5: scientific package readiness | After W1–W4 evidence dispositions and W2 contract review, freeze a **new** package with complete available bindings, neutral navigation and independently checked exposure omissions. Freeze both phase instruction assets/runtime before initial review; bind later sealed outputs in the adjudication phase without circular hashes. | Audit substantive definitions, counterevidence, original entity/version bindings and unresolved dependencies. Missing evidence must remain explicit. Demonstrate the planned evidence can exercise the unchanged gates; do not launch another round merely because every available file hashes. |
| W6: fresh reviewer execution | Provision new isolated clones at one exact committed runtime. Run actual same-clone save/readback in A; inspect before B. Use fresh scientific sessions that have not read historical judgments. Both initial reviewers get identical scientific evidence, with clone-specific execution paths. | Two immutable10-by-6 initial matrices and seals before mutual exposure; then separate adjudication through W2's bound inputs. Complete canonical save/readback, all proof replay and unchanged scoring. Record model/session identities and exposure limits. |
| W7: reassess retained100 | Only a passing W6 permits reviewing the remaining90 through the same production path. Start one new occurrence end to end, then bounded queues. Deduplicate evidence/node checks while retaining each edge binding. | All100 occurrence/endpoint accounting, six axes each, explicit unresolved counts, independent directional/model audit, issue/owner/correction linkage and persisted artifacts. |
| W8: measured expansion | Only after W7 and independently verified real correction against regenerated candidate bytes, select a bounded next cohort from9,900. Later full-population work requires source-family coverage and measured resources. | No automatic17M sweep. Measure wall time, peak memory/swap, bytes, provider throttling/failure rates and writer contention at1, then2, then4. Each new adapter/launcher/provider path has its own live canary. |

W0–W4 are evidence/engineering work, not additional scientific calibration
coverage. Helper workers exposed to old outcomes cannot become nominally blinded
reviewers. Each task has one exclusive output directory and an immutable input
identity; one coordinator owns dispatch and completion accounting. Use a bounded
queue, at most two new evidence helpers initially after the single-worker canary,
and one writer per catalogue. Do not interrupt unrelated M5 jobs or infer capacity
from core count. Native wrapper defaults may be used; record actual model and
reasoning settings without silently substituting a model.

### Concrete package handoff after witness recovery

The readiness audit is tracked in
[#220](https://github.com/CultureBotAI/EdgeMech/issues/220). Before W5/W6:

1. Record each recovered witness and its unresolved semantic or historical
   dependency. Independently assess whether the available evidence can exercise
   the unchanged gates without predicting reviewers' labels.
2. Build a separately identified **scientific** package. The November17 builder
   creates an engineering-prerequisite package; old round03 lacks the new
   invocation provenance. Neither is eligible for retrospective promotion.
3. Instantiate and review concrete neutral instruction templates and plans for
   both phases, including version-bound definitions and counterevidence. Register
   reviewer IDs `reviewer-a` and `reviewer-b`, distinct fresh clone paths and
   distinct repository-relative artifact namespaces, such as
   `.temp/ROUND/reviewer-a/` and `.temp/ROUND/reviewer-b/`. Distinct absolute
   clones alone do not prevent collisions when unchanged relative paths are
   collected into the adjudicator clone.
   Pin all authoring, proof, accounting and finalization helpers.
4. Generate authoring/citation/finalizer configurations against the original
   scientific manifest. After initial sessions finish, collect their final
   observed identities, native logs and complete readiness lineage, retaining
   the original relative file layout. Freeze their results in the separate
   adjudication launch manifest, then replay the typed #209 bindings.
5. Preserve the registered **20 initial canonical pairs**. Final adjudication
   produces separately sealed and proof-validated drafts/matrix; those drafts
   are not ten additional saved canonical pairs. The adjudicator's actual fresh
   environment still requires its own production save/readback canary. This
   prospective policy is aligned under
   [#219](https://github.com/CultureBotAI/EdgeMech/issues/219).

The new fresh05 public body-text extraction is inspected access evidence, not
yet an admitted canonical paper proof. The existing paper adapter accepts
verified Europe PMC abstracts or JATS. Obtain suitable original bytes or review
and canary a new extractor before using this extraction in scientific scoring;
do not disguise it as an authority document. The matching primary paper also
cannot repair mixed-row phenotype-cell lineage.

## Unchanged scientific gates

The [registered protocol](edge-calibration-20261115.md) and its machine-readable
protocol/cohort remain authoritative. Do not tune these thresholds after scoring:

- 10/10 packet and20/20 endpoint-role input coverage;60/60 final authored axes,
  no `UNASSESSED`, and explicit reasons for unresolved outcomes.
- Initial exact-category agreement at least54/60 overall,8/10 on **every** axis
  and9/10 for claim. Publish all six confusion tables before reconciliation.
- Zero independently adjudicated unsupported resolved claim/model judgments;
  audit both reviewers' initial labels and final labels, retaining all failures.
- Every input, quoted text, publication identity, authority version and immutable
  canonical review pair replays. A child process exiting0 is insufficient.
- Final source-fidelity resolution at least8/10; claim at least2/10; each modeling
  axis at least5/10. Agreement on unresolved labels cannot meet these floors.
- At least one exact-scope independently paper-backed directional claim and one
  exact-authority-backed incorrect-model judgment. Source-report support cannot
  substitute for the paper-backed exercise.
- Preserve both original ratings and evidence-based disagreement dispositions;
  unresolved disagreement over a resolved claim/model judgment blocks passage.
  Maintain prospectively seven applicable literature cases and report all ten.

A failed round is a durable result. Diagnose the specific failure, improve
evidence/procedure and register a new round only when the new inputs justify it.
Same-model agreement is operational evidence; it does not establish independent
expert agreement or calibrated population accuracy. No engineering receipt,
successful save, candidate correction or merged PR overrides these gates.

## Review, publication and handoff

Every material adversarial finding becomes an issue before repair. Review the
final diff read-only, address in-scope findings, run focused tests during work and
the full suite/contracts/lint/build on the final candidate. Open a PR against the
actual dependency branch and name unmerged owner/CLAW dependencies. No automatic
merge or cleanup of unmerged worktrees.

Public results contain bounded snippets, DOI/authority identifiers, hashes,
locators, status counts and limitations. Full articles and raw private packets
remain in ignored private storage. Helpers remain tracked in `scripts/adhoc/`.
Record actual library services used, including unavailable/failed outcomes;
using an LBNL skill alone is not service execution. Reconcile NEXT_TASKS and the
execution record with persisted results, not the workers' optimistic summaries.

## Historical November 9 design

Reviewed 2026-11-09 against EdgeMech main `47bcaec` and the pinned census.
Original (retained unchanged in ignored workspace):
`PLAN_17M_EDGE_CONTENT_AND_DOI_SNIPPET_REVIEW_20261109.md`, SHA-256
`57a56a66625363fd3cfce30cd7b815bddd2ca47b8ad9ac06133b9d623dcdc423`.
Review findings: [#31](https://github.com/CultureBotAI/EdgeMech/issues/31),
[#32](https://github.com/CultureBotAI/EdgeMech/issues/32).

## Assessment and corrections

The objective is useful; the proposed completion test is scientifically invalid.
Complete accounting is achievable. Complete positive support is not guaranteed.
A DOI identifies a work, a verbatim excerpt establishes what a text says, and an
edge-level judgment additionally needs organism/strain, predicate, object,
conditions, direction, modality, and provenance to match. A database paper cannot
substitute for experimental support for every assertion that database contains.

1. Preserve separate endpoint-presence, source-fidelity, retrieval, quote-match,
   entailment, and decision states. Allow `unassessed`, `unavailable`,
   `not_applicable`, `contradicted`, and `insufficient_evidence`. A null citation or
   quote with an explicit reason is a valid outcome. Never require invented text.
   Do not label all PREGO/FAPROTAX assertions inaccurate or all ontology edges
   accurate simply from their source. Non-exact mappings can be valid as written.
2. Presence means an ID is in the pinned node table. Missing labels/categories are
   separate quality failures. Predicate validity and domain/range require their
   own versioned checks. Hash-backed attribute IDs are not intrinsically invalid;
   assess their represented value and semantics. `Other` is not automatically false.
3. Exact source rows and occurrence multiplicity remain authoritative. The census
   stores binary `source_row` and canonical IDs, not top-level subject/evidence
   columns. Actual names are `partitions/rows-000000000001-000000020000.parquet`,
   not `part-00000.parquet`. The source TSVs are in the census's pinned snapshot,
   not the census output directory.
4. Approximate cardinality estimates can exceed true row counts; the original
   distinct counts are not trustworthy exact counts. Use exact SQL distinct tuple
   counts and an OR across evidence fields (not their sum). DOI counts must
   distinguish rows, identifiers, works, packets, and independent experiments.
   Counts grouped by `(source,predicate,object)` omit organism and conditions and
   cannot define equivalent scientific claims. The asserted 593 earlier reviews
   need an exact ID union and assessment of scope; cohort anchors are not coverage
   of their entire cohorts. The retained audit now confirms 593 distinct decision
   IDs (116 + 120 + 357), with zero inter-wave overlap, all withheld and no nonempty
   `quote` fields. Hashes match all three wave bundles and the combined ID index.
   This verifies decision accounting, not claim support; all 17,637,435 occurrences
   remain unassessed for the new content campaign. The legacy ledger's 100% reviewed
   label conflates cohort disposition with individual review; track its corrected
   view in [#35](https://github.com/CultureBotAI/EdgeMech/issues/35), preserving history.
5. Keep canonical identities and shared review schemas in pinned CLAW. This PR's
   local preparation inventory is an analysis product, not a replacement review
   contract. Compile/cache schemas once per process or worker image; run tests in
   CI/final validation, and validate contracts and content on ingestion/publication.
   Removing correctness gates entirely trades speed for silent corruption.
6. The 32-worker recommendation, I/O percentages, per-worker RSS, and 2.2 GiB
   output size have no reproducible supporting measurement here. An
   ignore-independent search of `scripts/` and `workspace/` found neither named
   profiling helper. Reported 14.6 GiB swap use does not establish safe spare RAM.
   This execution host has about 23 GiB free; the M5's reported 70 GiB is not a
   transferable budget. 17,637,435 allocations of 4096 bytes alone are about
   67.28 GiB (72.24 GB), before metadata. Measure actual columnar outputs instead.
7. Do not kill purported orphan processes without ownership and liveness evidence.
   Use a bounded queue with leases, immutable results, and idempotent task keys.
   Agent sessions, CPU cores, DuckDB threads, and provider requests are separate
   concurrency budgets. A single writer owns each DuckDB catalogue. Start at one
   process, then measure 2 and 4 before considering more; never assume 32 is best.

## Research and alternatives

- [Crossref access and limits](https://www.crossref.org/documentation/retrieve-metadata/rest-api/access-and-authentication/)
  currently documents public concurrency one and response-header rate limits.
  Use anonymous access, one shared provider queue, caching, retry/backoff and
  server-directed limits. Never add an email to obtain a higher pool.
- [Crossref retrieval guidance](https://www.crossref.org/documentation/retrieve-metadata/rest-api/tips-for-using-the-crossref-rest-api/)
  recommends caching and considering data dumps for very large workloads.
  Compare a deduplicated DOI queue against a local metadata snapshot after exact
  citation counts are known. A whole Crossref dump is not justified for a small
  set of works or this machine's disk budget.
- [Crossref full-text guidance](https://www.crossref.org/documentation/retrieve-metadata/rest-api/text-and-data-mining-for-researchers/)
  distinguishes metadata and links from the actual full text. Abstracts may be
  missing; metadata availability never establishes claim support or full-text rights.
- [Europe PMC service reference](https://europepmc.org/docs/EBI_Europe_PMC_Web_Service_Reference.pdf)
  distinguishes abstracts from the open-access full-text subset. Preserve the
  response, identifiers, retrieval URL/time, text extraction version and content
  hash; verify exact identifier matches, not the first search hit. Record access
  failures explicitly. Reuse the repository's `scripts/fulltext_access.py` access
  ladder where suitable, but add durable caching, exact-match verification and
  scheduler limits before bulk use; its current first-hit helper alone is insufficient.
- [DuckDB aggregation documentation](https://duckdb.org/docs/stable/sql/functions/aggregates.html)
  distinguishes exact distinct aggregation from approximate estimates. Use
  columnar staging, bounded memory/spill, exact reconciliation, and source hashes.

## Implementation sequence and acceptance criteria

### A. Deterministic preparation (implemented in this branch)

`src/edgemech/content_inventory.py` and the retained launcher
`scripts/adhoc/prepare_content_inventory_20261109.py`:

- Require the census SHA-256; verify the copied source manifest and node member.
- Check partition bounds, selected bytes, exact raw-row digests, canonical
  occurrence IDs, ordering, row counts, and persisted ID parity in both directions.
- Reject duplicate/empty node IDs so joins cannot multiply occurrences. Preserve
  original evidence columns verbatim as candidates, including base64 payloads.
- Write one Zstd Parquet preparation shard per selected input partition, with
  endpoint states and `content_status=unassessed`. Do not create scientific reviews.
- Compute exact source profiles across persisted shards. On a complete population,
  reconstruct and verify the original edge-file SHA-256, including header bytes.
- Refuse existing output directories; publish the manifest last after checks.
  Flush shards and publish a fully flushed manifest with an atomic, non-replacing
  link. Injected publication failures expose no completion marker ([#34](https://github.com/CultureBotAI/EdgeMech/issues/34)).
  A failure leaves an unpublished directory for diagnosis; retry at a new path.
- Default to one whole partition; full execution uses the same command with `--all`.
  Check a 10 GiB free-space reserve, 512 MB DuckDB memory and 4 GB spill cap.
  These are operating limits, not guarantees for total Python/Arrow RSS or final size.

Partial preparation verifies selected bytes only and does not replay native review
history. The established `verify-census` command remains the native-contract audit.
Preparation output is explicitly not a public scientific approval artifact.
Some `publications` cells contain only BacDive strain URLs. An inline-evidence
count includes those raw references; it is not a count of literature-supported rows.

### B. Evidence catalogue and source-specific fidelity adapters

Deduplicate retrieval by normalized publication identifier, but preserve every raw
citation and occurrence binding. Keep a many-to-many occurrence/evidence table;
store documents once and quotations by stable document hash plus text offsets.
Claim keys must include taxon/strain, normalized relation, object, units,
conditions, polarity/modality, source record, and normalization version. Unknown
context prevents unsafe grouping. Never propagate one reviewed cohort anchor to
all occurrences. Decode base64 only with the source's documented encoding and
retain the original bytes and decoder version.

Reconcile previous-wave IDs against the frozen census and keep prior decisions
with their actual scope. Harvest native exports with pinned repository commits,
locators, payload/evidence hashes, and review status; citation coincidence is only
a candidate binding. Develop source-fidelity adapters separately for taxonomy,
ontology relations, aggregated traits, measured observations, mappings and mined
claims. Validate a single representative case of each before scaling that adapter.

### C. Retrieval and quote verification

The initial one-request probe is implemented in `edgemech.literature_probe` and
`scripts/adhoc/probe_literature_20261109.py`. It accepts only DOI/PMID identifiers,
uses anonymous Europe PMC access, bounds the response size and timeout, checks
exact identifier equality and ambiguity, retains response bytes and hashes, and
publishes retrieval status without asserting quote validity or claim support.
The DOI `10.4056/sigs.1804360` from a prior-wave rationale returned an abstract in
the live canary; the persisted response was verified. This is not a bulk scheduler.

Run one actual anonymous DOI/PMID request with the future production launcher,
verify nonempty durable response and exact identifier equality, then test missing
abstracts, wrong identifiers, ambiguous results, rate limits and retry exhaustion.
Use a process-shared provider limiter; obey Retry-After, bounded exponential
backoff with jitter, bounded payloads/timeouts, and negative-cache expiry. Keep
abstract/full-text/metadata distinctions and access/license restrictions explicit.
Do not execute an unbounded paid retrieval or LLM sweep from a CPU-only estimate.

Verify quote substrings against a versioned text extraction of retained source
bytes. Store raw and normalized forms, offsets, retrieval hash and locator.
A verbatim match is an integrity test, not an entailment verdict. Distinguish
assertion-specific evidence, source-background evidence, and definition evidence.

### D. Scientific adjudication and measured expansion

Use canonical CLAW/native contracts for decisions, after any needed shared schema
extension is reviewed upstream. Record direct support, contradiction, missing
context and not-applicable cases independently of transport validity. Calibrate
reviewers on a stratified gold set including negative controls and source-specific
failure cases. Audit agreement and false-support rate before propagating any
explicitly scoped decision. Route unresolved cases to the native owner.

One partition is a transport/performance canary, not a scientifically representative
sample. Add canaries across all source families and evidence failure modes. Measure
peak parent/child RSS, swap pressure, API throttling, persisted bytes, wall time and
failure rate. Use those measurements to set process and provider concurrency.
Prefer dynamic cost-aware tasks over 27/28 fixed partitions per worker. Separate
network retrieval from local joins and scientific review.

### E. Publication and sync

Verify exact occurrence parity, one accounting state per occurrence, immutable
hashes and full manifest coverage. Report unresolved counts alongside positive
judgments; never use nonempty DOI/snippet as a completion criterion. Validate
shared review contracts at the publication boundary and run the full test suite.
Sync by content hashes to a new destination, then independently verify it before
publishing its manifest. Preserve source, evidence and prior decision identities.
No merge, remote worker-pool expansion, or scientific approval is implied by this PR.
