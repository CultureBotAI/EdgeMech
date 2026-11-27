# Bounded candidate occurrence membership — issues #224 and #228

Status: source and synthetic tests prepared for independent review. No actual
candidate scan has run. This unit does not freeze A/B or qualify an assessment.

The retained ledger reconciliation names1287 unique candidate occurrence IDs.
They include IDs from distinct source versions and a known fixture; they are
observations requiring disposition, not the final reviewed population. The new
helper matches exact IDs against pinned census partitions and recomputes each
matched occurrence from its source manifest/member pins, row position and raw-row
hash using pinned CLAW identity code. Equal subject/predicate/object values and
identical raw rows at different positions cannot collapse into one occurrence.

Inputs are the existing census manifest at SHA256
a2b8353349816fd067ab3a7112fd1c2f5ee9c02971591ea52f31e9b981cbdd2e and the retained
candidate-ledger document at SHA256
32522e9a12210217a15cbf17e6ef1be75234140480d010701a5abf7229cd56be. The explicit
`--candidate-field candidate_union_ids` selects the already saved list. No new
identity extraction or historical metadata audit is needed. Private bindings
and actual invocation receipts belong in the campaign evidence, outside Git.

After independent source review, the first permitted observation is a single
partition using the same guarded read/match path, a60-second cooperative budget
and an exclusive private attempt directory. Inspect the persisted plan, progress
and result before any larger unit. If that read path passes, a separately
recorded complete declared-partition scan may use at most1800 cooperative seconds
with one process and PyArrow threading disabled. A failed or expired attempt is
retained; it is never overwritten or treated as completion. If a native read
stalls beyond the cooperative budget, preserve the attempt and stop its owned
process rather than introducing another simultaneous reader.

Outputs contain matched IDs and source positions/hashes, explicit IDs not seen
within the scanned partitions, and per-partition durable progress. A prefix
result cannot assert complete membership. Every result keeps scientific
coverage0, A/Bnull, full-target-frozenfalse, baseline-membership-qualifiedfalse
and full-census-native/source-replay-verifiedfalse. Missing IDs need explicit
source-version/fixture/other disposition; they are not silently discarded.

Reuse the existing retained census audit for its overlapping metadata and
terminal evidence. The original full verifier remains FAILED outer exit1 with
separately unobserved child exit. This helper does not run that verifier, replay
native classification or restore sources. It reads partitions only for the new
candidate membership question. The bounded timing-wrapper plan and final census
validation disposition are separate gates.

Further prerequisites remain: exhaustive discovery/archive handling, declared
review/source version validation, fixture and automated-archive dispositions,
an independently verified cutoff and exact disjoint/exhaustive A/B accounting.
All W5/W6, issue220, correction, resource and actual scientific-runtime gates
remain unchanged. No provider call, canonical save or scientific dispatch is
part of this unit.
