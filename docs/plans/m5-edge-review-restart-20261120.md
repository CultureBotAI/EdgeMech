# M5 CLAW assignment: resume the EdgeMech review campaign

User authorization received 2026-11-19 Pacific time (2026-11-20 UTC): have M5
CLAW restart EdgeMech edge review and continue to completion, starting with
unreviewed edges and then re-reviewing previously reviewed edges using newly
available LBNL Library services. This is an execution assignment, not a request
for another status-only inventory. It does not authorize merging new PRs.

## Ownership and durable execution

M5 CLAW owns coordination. Resolve EdgeMech through the current fleet manifest
and verified repository identity. Preserve other active CLAW assignments,
including MIM. Delegate an isolated EdgeMech coordinator and helper workers if
the fleet coordinator is occupied; keep one dispatcher and one catalogue writer.
Use existing supported `codex-work` or `agy-work` launch paths and record actual
session/model/runtime identities. Do not interrupt unrelated jobs or old reviews.

The currently inspected canonical CLAW manifest disables EdgeMech's generic
`record_review`, `deep_research`, `coordination_hooks` and `source_queue`
capabilities. This is a named assignment to coordinate the maintained **native
EdgeMech** review workflow, not a claim that generic fleet review hooks are
enabled. Resolve and respect that distinction; do not flip admission flags or
invoke a disabled generic runner to bypass it. Any required shared capability
change needs its own reviewed implementation and validation.

Maintain a durable campaign request, queue, progress ledger and resumable
checkpoints beneath EdgeMech's ignored `.temp/` or `~/agent-work/EdgeMech/`.
Retain completed and failed attempts. Continue bounded queued units without
requiring the user to repeatedly say "continue". Repair reversible operational
failures, and continue independent units when a source-specific evidence gap is
recorded. A global prerequisite failure must be reported precisely; never bypass
it or count a scheduled job as a completed review.

Write an acknowledgement and progress record at
`~/agent-work/EdgeMech/restart-20261120/ACK.md` and `progress.json`. Include the
assigned session, owned checkout/branch/commit, next concrete action, actual
worker state, queue counts and artifact paths. Later updates should preserve
prior checkpoint snapshots. Record the same request in the CLAW supervisor's
normal task registry so it survives a session handoff.

## Revised queue order

The user's new order supersedes the November19 plan's retained-100-first
**production scheduling order**. It does not waive evidence checks, alter old
calibration thresholds, or authorize fabricated passing labels.
In particular, the old **W7-before-W8 cohort-order prerequisite is replaced**
for this new campaign: remaining-90 reassessment is not required before the
unreviewed production queue. W5/W6 calibration and exact-runtime readiness,
independent verification of a real correction against regenerated candidate
bytes, and source-family/resource gates remain required before expansion.
This resolves review finding #223; old plan/results retain their historical scope.

1. Reconcile exact occurrence IDs from the frozen census against **all** retained
   review ledgers, native review bundles and earlier canary/wave outputs, including
   ignored archives. Verify the campaign population rather than trusting a
   "100% reviewed" cohort footer. The existing census reference is 17,637,435
   occurrences; the 10,000 sample and its retained 100 are subsets, not substitutes
   for complete population accounting. Before dispatch, freeze the exact full
   target manifest, count/hash, baseline review cutoff and the prior-assessment
   ID ledger with explicit membership criteria. Queue A and Queue B must be
   disjoint and exhaustive: **A intersect B is empty; A union B equals the frozen
   target**. Newly completed A occurrences stay in A and never enter B. Report
   unavailable/excluded/ineligible IDs separately with reasons; do not silently
   remove them from the denominator or shrink the full-census objective. Record
   any census/version difference before counting work. This resolves #224.
2. Queue A contains occurrences without a prior individual edge assessment.
   Run one genuinely unreviewed occurrence end to end through the intended
   launcher, library/evidence path and canonical persistence path, then inspect
   its nonempty saved artifacts and readback before any batch. If readiness is
   incomplete, treat it explicitly as an excluded preparation canary. Do not
   promote that result into calibrated production coverage.
3. Satisfy the unchanged scientific calibration, runtime/evidence checks and
   candidate-correction/resource gates before expanding Queue A, with only the
   old W7-before-W8 scheduling prerequisite replaced as stated above. Any
   mandatory calibration work on old fixed challenge
   cases is a separately labeled validation prerequisite, not the second-pass
   production queue. Do not silently change the registered cohort or floors to
   satisfy the new scheduling order. Resolve the concrete prerequisites in #220
   and record how they are met before dispatching a scientific batch.
4. Once Queue A has complete, independently checked occurrence accounting,
   process the frozen Queue B: all occurrences individually reviewed by the
   recorded baseline cutoff, including
   earlier partial or unresolved reviews. Obtain new evidence through the actual
   LBNL-enabled environment, preserve previous ratings, and write new versioned
   assessments with explicit changes and evidence provenance. Do not overwrite
   old reviews or count re-review as new population coverage.

Use bounded, checkpointed cohorts. Start at one worker and increase to two only
after its actual canary passes; measure memory, storage, provider limits and
writer contention before considering more. Deduplicate paper/node evidence while
retaining each occurrence's binding. A full-population queue is not permission
for an uncontrolled 17-million-request provider sweep.

## Six required assessments and evidence

Every completed occurrence needs separate categorical assessments for:

- The exact claim, including organism/strain, conditions, units, polarity and
  qualifiers; source reports are allowed only for original report propositions.
- Literature support or refutation, with verified publication identity and DOI
  where available, short literal snippets, document hashes/locators and inspected
  extent. Preserve unavailable, insufficient and not-applicable outcomes.
- Relation choice, direction and specificity against the applicable version.
- Subject identity, label, category, rank/type and version-bound definition.
- Object identity, label, category and version-bound definition, including
  quantitative boundaries, units and process/assay meaning where relevant.
- Source fidelity, separate from biological truth and ontology correctness.

Use the maintained EdgeMech profile and pinned CLAW schemas, not an improvised
parallel schema. `UNASSESSED` is unfinished. Assessed uncertainty is a result,
not evidence of falsehood. Existing calibration resolution floors still apply.
File material defects, propose corrections in maintained owner inputs, and
verify regenerated candidate bytes. Candidate and full graph-release verification
remain distinct; #143 still tracks BactoTraits release verification.

## LBNL access must be exercised in the worker

Apply the installed `lbnl-mech-record-review` and
`lbnl-literature-and-db-access` skills. Search local provenance and retained
Zotero/OA evidence before provider requests; route by claim content and publisher.
Use already configured M5 CBORG Valency/Tavily/Context7 and appropriate licensed
TDM/database access. A configured tool or metadata response is not full-text
access: verify one relevant live retrieval, readable required content, identity,
private persistence and literal evidence replay inside the **actual** worker.

Keep provider request/outcome records and distinguish metadata, abstract,
extracted body, publisher full text, tables and figures actually inspected.
Do not count an HTTP challenge page as a paper. If one licensed route fails,
record it and try the appropriate available legal alternatives; do not repeatedly
retry an identical failed route or claim all library access is unavailable.

Use existing credentials without printing or committing them. Additional secret
transfers and new paid deep-research sweeps are not authorized by this handoff.
No personal email disclosure, external human messaging or notification mentions.
Full article bodies stay private; only permitted bounded excerpts and provenance
belong in public records.

## Known state to verify and reuse

- Canonical main was `f841b1d`; reviewed candidate PR #214 is at
  `64a1c65b1be698842a73921ec9e4304e3339a91d`, based on unmerged PR #211.
  The final candidate passed 1,468 tests, 16 contracts, Ruff and package builds.
  Re-check current GitHub state and adopt an isolated exact runtime without
  treating an unmerged candidate as deployment or assuming merge permission.
- Read `docs/plans/content-review-20261109.md`, its W5 checklist, #220 and the
  November19 execution/adversarial records. Typed adjudication, complete original
  readiness lineage, phase/original manifest distinctions and the registered
  20-initial-pair persistence policy are already implemented. Reuse them.
- M5 source helpers completed first43, first28 and fresh14. Their reports and
  private evidence are in `~/agent-work/EdgeMech/content-review-workers-20261119/`.
  The repaired source helper passed fresh canaries in `metatraits-repair-221`
  at `131669b0fed293201238c432bb36ba2b6ecf8df0`. Preserve these environments.
- Prior calibration rounds failed. Remaining dependencies include original
  field meanings, GTDB/LPSN identities, mixed-row phenotype-cell lineage, bin
  weights and process-generation versions. The fresh05 public body extraction
  is not yet admitted by the current abstract/JATS proof adapter. Library access
  can improve evidence; it does not by itself repair those dependencies.

## Completion and reporting

Report attempted, successfully persisted, fully assessed, unresolved, failed,
blocked and re-reviewed counts separately for both queues, with exact ID
accounting and no double counting. Each checkpoint must identify actual running
jobs, recent verified outputs, remaining work and any precise blocker.

Campaign completion requires every occurrence in the frozen full target manifest
accounted for across both
queues, all six assessments and endpoint roles present, canonical save/readback
and evidence checks passed, independently audited decisions and correction/issue
linkage, and a final coverage/limitations report. Do not declare completion from
process exit, cohort labels, queue exhaustion with failed saves, or a merged
engineering PR. Continue the authorized work until that condition or a concrete
external prerequisite prevents further independent progress.
